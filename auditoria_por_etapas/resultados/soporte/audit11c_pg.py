"""Stage 11C PostgreSQL 18.4 deep verification: OS SIGKILL, pg_ctl -m immediate, NFR-05 / PT-CHECKOUT-01 (2k/10k), and lock compatibility."""
from __future__ import annotations

import hashlib
import http.cookiejar
import json
import os
import re
import secrets
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "r1-pmv/manage.py").is_file())
PROJECT = ROOT / "r1-pmv"
PG_BIN = Path(r"C:\Program Files\PostgreSQL\18\bin")

OUT = Path(sys.argv[1]).resolve()
OUT.mkdir(parents=True, exist_ok=True)


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_snapshot() -> dict:
    exts = {".py", ".html", ".css", ".js"}
    files = sorted(
        p
        for p in PROJECT.rglob("*")
        if p.is_file() and p.suffix in exts and ".venv" not in p.parts and "__pycache__" not in p.parts
    )
    h = hashlib.sha256()
    for p in files:
        h.update((p.relative_to(PROJECT).as_posix() + "\n").encode("utf-8"))
        h.update(p.read_bytes())
    return {"count": len(files), "sha256": h.hexdigest()}


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


WORKER_CODE = r"""
import json, os, sys, time
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

sys.path.insert(0, os.environ["AUDIT11C_PROJECT"])
os.chdir(os.environ["AUDIT11C_PROJECT"])

from config import env as config_env
config_env.load_dotenv = lambda path=None: None

import django
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
settings.DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["AUDIT11C_PG_DB"],
        "USER": os.environ["AUDIT11C_PG_USER"],
        "PASSWORD": os.environ["AUDIT11C_PG_PASS"],
        "HOST": "127.0.0.1",
        "PORT": int(os.environ["AUDIT11C_PG_PORT"]),
        "CONN_MAX_AGE": 0,
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "TIME_ZONE": "America/Lima",
        "OPTIONS": {"options": "-c statement_timeout=30000 -c lock_timeout=15000"},
    }
}
settings.SESSION_COOKIE_SECURE = False
settings.CSRF_COOKIE_SECURE = False
django.setup()

from django.db import connections  # noqa: E402
assert connections["default"].vendor == "postgresql"

barrier_file = Path(os.environ["AUDIT11C_BARRIER_FILE"]) if os.environ.get("AUDIT11C_BARRIER_FILE") else None
hold_seconds = float(os.environ.get("AUDIT11C_HOLD_SECONDS", "25"))

if barrier_file is not None:
    from sales.models import SaleDraft
    orig_save = SaleDraft.save

    def halted_draft_save(self, *args, **kwargs):
        res = orig_save(self, *args, **kwargs)
        if self.status == SaleDraft.Status.DISCARDED:
            from django.db import connection
            with connection.cursor() as cur:
                cur.execute("SELECT pg_backend_pid(), txid_current_if_assigned()::text")
                pid, xid = cur.fetchone()
            barrier_file.write_text(json.dumps({"backend_pid": pid, "xid": xid}), encoding="utf-8")
            time.sleep(hold_seconds)
        return res

    SaleDraft.save = halted_draft_save

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.wsgi import get_wsgi_application

app = StaticFilesHandler(get_wsgi_application())

class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass

class ThreadedWSGI(WSGIServer):
    daemon_threads = True

server = make_server("127.0.0.1", int(os.environ["AUDIT11C_HTTP_PORT"]), app, server_class=ThreadedWSGI, handler_class=QuietHandler)
Path(os.environ["AUDIT11C_READY_FILE"]).write_text("ready", encoding="utf-8")
server.serve_forever()
"""


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def http_session():
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoRedirect())


def extract_csrf_and_hidden(html: str) -> dict[str, str]:
    tokens = {}
    for m in re.finditer(r'<input\b([^>]+)>', html, re.IGNORECASE):
        attrs = m.group(1)
        name_m = re.search(r'name=["\']([^"\']+)["\']', attrs)
        val_m = re.search(r'value=["\']([^"\']*)["\']', attrs)
        if name_m and val_m:
            tokens[name_m.group(1)] = val_m.group(1)
    return tokens


def pg_locks_snapshot(conn, backend_pid: int) -> dict:
    cur = conn.execute(
        """
        SELECT a.pid, a.state, a.backend_xid::text,
               COALESCE(c.relname, l.locktype) AS target, l.mode, l.granted
        FROM pg_locks l
        JOIN pg_stat_activity a ON a.pid = l.pid
        LEFT JOIN pg_class c ON c.oid = l.relation
        WHERE l.pid = %s AND l.locktype IN ('relation', 'transactionid')
        ORDER BY target, l.mode
        """,
        (backend_pid,),
    )
    rows = cur.fetchall()
    return {
        "backend_pid": backend_pid,
        "states": sorted({r[1] for r in rows}),
        "backend_xids": sorted({r[2] for r in rows if r[2]}),
        "relation_locks": [
            {"table": r[3], "mode": r[4], "granted": r[5]}
            for r in rows
            if r[3] != "transactionid" and r[3].startswith(("sales_", "inventory_", "cash_", "catalog_", "identity_"))
        ],
    }


def start_worker(
    *,
    worker_script: Path,
    pg_port: int,
    dbname: str,
    pw_pg: str,
    secret_key: str,
    barrier_file: Path | None,
    ready_file: Path,
) -> tuple[subprocess.Popen, int]:
    http_port = free_port()
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "test",
            "DATABASE_URL": "sqlite",
            "DJANGO_DEBUG": "false",
            "DJANGO_ALLOWED_HOSTS": "127.0.0.1,localhost,testserver",
            "DJANGO_SECRET_KEY": secret_key,
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "AUDIT11C_PROJECT": str(PROJECT),
            "AUDIT11C_PG_DB": dbname,
            "AUDIT11C_PG_USER": "audit11c",
            "AUDIT11C_PG_PASS": pw_pg,
            "AUDIT11C_PG_PORT": str(pg_port),
            "AUDIT11C_HTTP_PORT": str(http_port),
            "AUDIT11C_READY_FILE": str(ready_file),
            "AUDIT11C_HOLD_SECONDS": "25",
        }
    )
    if barrier_file is not None:
        env["AUDIT11C_BARRIER_FILE"] = str(barrier_file)
    else:
        env.pop("AUDIT11C_BARRIER_FILE", None)

    proc = subprocess.Popen(
        [str(PROJECT / ".venv/Scripts/python.exe"), str(worker_script)],
        cwd=PROJECT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    deadline = time.time() + 20.0
    while not ready_file.exists():
        if proc.poll() is not None:
            out, err = proc.communicate(timeout=2)
            raise RuntimeError(f"Worker exited prematurely rc={proc.returncode}: {err.decode('utf-8', 'replace')}")
        if time.time() > deadline:
            proc.kill()
            raise TimeoutError("Timed out waiting for HTTP worker ready")
        time.sleep(0.05)
    return proc, http_port


def pg_ctl(dbdir: Path, pg_log: Path, pg_port: int, action: str, mode: str | None = None) -> None:
    cmd = [str(PG_BIN / "pg_ctl.exe"), "-D", str(dbdir)]
    if action == "start":
        cmd += ["-l", str(pg_log), "-o", f"-h 127.0.0.1 -p {pg_port} -c log_statement=none -c log_min_error_statement=panic", "-w", "start"]
    elif action == "stop":
        cmd += ["-m", mode or "fast", "-w", "stop"]
    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )


def main() -> int:
    prod_db = PROJECT / "r1_pmv.sqlite3"
    prod_db_before = sha_bytes(prod_db.read_bytes())
    build_before = build_snapshot()
    secret_key = secrets.token_urlsafe(48)

    os.environ.update(
        APP_ENV="test",
        DATABASE_URL="sqlite",
        DJANGO_DEBUG="false",
        DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost,testserver",
        DJANGO_SECRET_KEY=secret_key,
        DJANGO_SETTINGS_MODULE="config.settings",
    )
    sys.path.insert(0, str(PROJECT))
    os.chdir(PROJECT)

    cluster = (Path(tempfile.gettempdir()) / ("audit11c-pg-" + secrets.token_hex(8))).resolve()
    cluster.mkdir(exist_ok=False)
    (cluster / "AUDIT11C_OWNED").write_text("owned_by_audit11c_pg", encoding="utf-8")
    dbdir = cluster / "data"
    pg_log = cluster / "pg.log"
    pw_pg = secrets.token_urlsafe(32)
    pwfile = cluster / "pw"
    pwfile.write_text(pw_pg, encoding="utf-8")
    worker_script = cluster / "http_worker.py"
    worker_script.write_text(WORKER_CODE, encoding="utf-8")
    pg_port = free_port()
    pg_started = False
    connections = None

    report: dict = {
        "executed_utc": datetime.now(dt_timezone.utc).isoformat(),
        "pg_port": pg_port,
        "build_before": build_before,
        "scenarios": {},
    }

    try:
        subprocess.run(
            [
                str(PG_BIN / "initdb.exe"),
                "-D", str(dbdir), "-U", "audit11c", "--pwfile", str(pwfile),
                "--auth-host=scram-sha-256", "--auth-local=scram-sha-256",
                "--encoding=UTF8", "--locale=C",
            ],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW,
        )
        pwfile.unlink()
        pg_ctl(dbdir, pg_log, pg_port, "start")
        pg_started = True

        import psycopg  # noqa: E402
        from psycopg import sql  # noqa: E402

        dbname = "audit11c_" + secrets.token_hex(4)
        with psycopg.connect(host="127.0.0.1", port=pg_port, user="audit11c", password=pw_pg, dbname="postgres", autocommit=True) as conn:
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
            report["pg_version"] = conn.execute("SELECT version()").fetchone()[0]

        from config import env as config_env  # noqa: E402
        config_env.load_dotenv = lambda path=None: None

        from django.conf import settings  # noqa: E402
        settings.DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": dbname,
                "USER": "audit11c",
                "PASSWORD": pw_pg,
                "HOST": "127.0.0.1",
                "PORT": pg_port,
                "CONN_MAX_AGE": 0,
                "CONN_HEALTH_CHECKS": False,
                "ATOMIC_REQUESTS": False,
                "AUTOCOMMIT": True,
                "TIME_ZONE": "America/Lima",
                "OPTIONS": {"options": "-c statement_timeout=30000 -c lock_timeout=15000"},
            }
        }
        settings.SESSION_COOKIE_SECURE = False
        settings.CSRF_COOKIE_SECURE = False

        import django  # noqa: E402
        django.setup()

        from django.core.management import call_command  # noqa: E402
        from django.db import close_old_connections, connections  # noqa: E402
        from django.test import Client  # noqa: E402
        from django.test.utils import CaptureQueriesContext  # noqa: E402
        from django.utils import timezone as tz  # noqa: E402

        assert connections["default"].vendor == "postgresql"

        call_command("migrate", verbosity=0)

        from cash.models import CashRegister, CashShift  # noqa: E402
        from cash.services import open_cash_shift  # noqa: E402
        from catalog.models import Category, Product  # noqa: E402
        from identity.models import Account, Role  # noqa: E402
        from inventory.models import Lot, Supplier  # noqa: E402
        from inventory.services import LotInput, confirm_initial_load  # noqa: E402
        from sales.models import Sale, SaleCounter, SaleDraft, SaleLine, SaleLotAllocation  # noqa: E402
        from sales.services import add_product_to_draft  # noqa: E402

        roles = {r.code: r for r in Role.objects.all()}
        admin = Account.objects.create_user(
            email="admin11c@example.com", display_name="Admin 11C", password=secrets.token_urlsafe(20), role=roles[Role.Code.ADMIN]
        )
        warehouse = Account.objects.create_user(
            email="alm11c@example.com", display_name="Almacen 11C", password=secrets.token_urlsafe(20), role=roles[Role.Code.WAREHOUSE]
        )
        seller_pw = secrets.token_urlsafe(20)
        seller = Account.objects.create_user(
            email="vend11c@example.com", display_name="Vendedor 11C", password=seller_pw, role=roles[Role.Code.SELLER]
        )
        reg1, _ = CashRegister.objects.get_or_create(code="CAJA-11C-1", defaults={"is_active": True})
        cat = Category.objects.create(name="Lacteos 11C")
        sup = Supplier.objects.create(name="Prov 11C", ruc="20456789012")
        prod = Product.objects.create(category=cat, name="Leche 11C", barcode="7751111111111", sale_price=Decimal("10.00"))
        confirm_initial_load(
            actor=warehouse,
            product=prod,
            lots=[LotInput(number="L-11C-1", quantity=10, unit_cost=Decimal("4.0000"), expiration_date=date.today() + timedelta(days=30), supplier=sup)],
        )
        shift = open_cash_shift(actor=seller, register=reg1, opening_amount=Decimal("100.00"))
        draft = add_product_to_draft(actor=seller, product_id=prod.pk, quantity=3)

        def http_login(base_url: str):
            op = http_session()
            r_login_get = op.open(base_url + "/")
            login_html = r_login_get.read().decode("utf-8")
            csrf_login = extract_csrf_and_hidden(login_html)["csrfmiddlewaretoken"]
            login_data = urllib.parse.urlencode(
                {"csrfmiddlewaretoken": csrf_login, "email": seller.email, "password": seller_pw}
            ).encode()
            try:
                r_login_post = op.open(urllib.request.Request(base_url + "/", data=login_data, method="POST"))
                login_status = r_login_post.status
            except urllib.request.HTTPError as e:
                login_status = e.code
            assert login_status in (200, 302), f"Unexpected login status {login_status}"
            return op

        def http_login_and_get_checkout(base_url: str):
            op = http_login(base_url)
            r_chk_get = op.open(base_url + "/ventas/cobrar/")
            chk_html = r_chk_get.read().decode("utf-8")
            fields = extract_csrf_and_hidden(chk_html)
            fields["cash_received"] = "50.00"
            return op, fields

        def fire_checkout_post(op, base_url: str, fields: dict[str, str]):
            body = urllib.parse.urlencode(fields).encode()
            req = urllib.request.Request(base_url + "/ventas/cobrar/", data=body, method="POST")
            try:
                resp = op.open(req, timeout=20)
                return resp.status, resp.headers.get("Location", "")
            except urllib.request.HTTPError as e:
                return e.code, e.headers.get("Location", "")
            except Exception as exc:
                return f"ERR:{type(exc).__name__}:{exc}", ""

        # ── 01. CT-ROLLBACK-01/C-01: real HTTP OS SIGKILL post-write pre-commit ───────
        ready1 = cluster / "ready1"
        barrier1 = cluster / "barrier1.json"
        w1, port1 = start_worker(
            worker_script=worker_script, pg_port=pg_port, dbname=dbname, pw_pg=pw_pg,
            secret_key=secret_key, barrier_file=barrier1, ready_file=ready1,
        )
        locks_obs = {}
        try:
            op1, fields1 = http_login_and_get_checkout(f"http://127.0.0.1:{port1}")
            saved_idem_key = fields1["idempotency_key"]
            saved_sig = fields1["draft_signature"]
            saved_sub = fields1["expected_subtotal"]
            post_res: list = []

            t = threading.Thread(target=lambda: post_res.append(fire_checkout_post(op1, f"http://127.0.0.1:{port1}", fields1)), daemon=True)
            t.start()
            t_wait = time.time() + 15.0
            while not barrier1.exists():
                if time.time() > t_wait:
                    raise TimeoutError("Did not reach post-write barrier1")
                time.sleep(0.05)
            binfo1 = json.loads(barrier1.read_text(encoding="utf-8"))
            with psycopg.connect(host="127.0.0.1", port=pg_port, user="audit11c", password=pw_pg, dbname=dbname) as inspect_conn:
                locks_obs = pg_locks_snapshot(inspect_conn, binfo1["backend_pid"])
            w1.kill()
            w1.wait(timeout=5)
            t.join(timeout=5)
        finally:
            if w1.poll() is None:
                w1.kill()

        close_old_connections()
        lot_after_kill = Lot.objects.get(product=prod, number="L-11C-1")
        draft_after_kill = SaleDraft.objects.get(pk=draft.pk)
        counter_after_kill = SaleCounter.objects.first()

        # Retry with clean worker using exact same idempotency_key
        ready2 = cluster / "ready2"
        w2, port2 = start_worker(
            worker_script=worker_script, pg_port=pg_port, dbname=dbname, pw_pg=pw_pg,
            secret_key=secret_key, barrier_file=None, ready_file=ready2,
        )
        try:
            op2, fields2 = http_login_and_get_checkout(f"http://127.0.0.1:{port2}")
            fields2["idempotency_key"] = saved_idem_key
            fields2["expected_subtotal"] = saved_sub
            fields2["draft_signature"] = saved_sig
            retry1_status, retry1_loc = fire_checkout_post(op2, f"http://127.0.0.1:{port2}", fields2)
        finally:
            w2.kill()
            w2.wait(timeout=5)

        close_old_connections()
        sale1 = Sale.objects.get()
        lot_after_retry1 = Lot.objects.get(product=prod, number="L-11C-1")
        c01_ok = (
            bool(locks_obs.get("backend_xids"))
            and {"sales_salecounter", "sales_sale", "sales_saleline", "sales_salelotallocation", "inventory_lot", "sales_saledraft"}.issubset(
                {x["table"] for x in locks_obs.get("relation_locks", []) if x["mode"] == "RowExclusiveLock" and x["granted"]}
            )
            and lot_after_kill.available_quantity == 10
            and draft_after_kill.status == SaleDraft.Status.ACTIVE
            and counter_after_kill is None
            and retry1_status == 302
            and sale1.correlative == "V-00000001"
            and lot_after_retry1.available_quantity == 7
        )
        report["scenarios"]["01_CT_ROLLBACK_01_C01_os_kill_checkout"] = {
            "ok": c01_ok,
            "locks_held_before_kill": locks_obs,
            "killed_http_outcome": post_res,
            "post_kill_state": {
                "lot_available": lot_after_kill.available_quantity,
                "draft_status": draft_after_kill.status,
                "counter_exists": counter_after_kill is not None,
            },
            "retry_outcome": {"status": retry1_status, "location": retry1_loc, "correlative": sale1.correlative, "lot_available": lot_after_retry1.available_quantity},
        }

        # ── 02. CT-ROLLBACK-01/C-02: pg_ctl -m immediate pre-commit & post-commit ─
        draft2 = add_product_to_draft(actor=seller, product_id=prod.pk, quantity=2)
        ready3 = cluster / "ready3"
        barrier3 = cluster / "barrier3.json"
        w3, port3 = start_worker(
            worker_script=worker_script, pg_port=pg_port, dbname=dbname, pw_pg=pw_pg,
            secret_key=secret_key, barrier_file=barrier3, ready_file=ready3,
        )
        try:
            op3, fields3 = http_login_and_get_checkout(f"http://127.0.0.1:{port3}")
            saved_key2 = fields3["idempotency_key"]
            saved_sig2 = fields3["draft_signature"]
            saved_sub2 = fields3["expected_subtotal"]
            post_res3: list = []
            t3 = threading.Thread(target=lambda: post_res3.append(fire_checkout_post(op3, f"http://127.0.0.1:{port3}", fields3)), daemon=True)
            t3.start()
            t_wait = time.time() + 15.0
            while not barrier3.exists():
                if time.time() > t_wait:
                    raise TimeoutError("Did not reach post-write barrier3")
                time.sleep(0.05)
            binfo3 = json.loads(barrier3.read_text(encoding="utf-8"))
            with psycopg.connect(host="127.0.0.1", port=pg_port, user="audit11c", password=pw_pg, dbname=dbname) as inspect_conn:
                locks_obs3 = pg_locks_snapshot(inspect_conn, binfo3["backend_pid"])
            connections.close_all()
            pg_ctl(dbdir, pg_log, pg_port, "stop", mode="immediate")
            pg_started = False
            w3.kill()
            w3.wait(timeout=5)
            t3.join(timeout=5)
        finally:
            if w3.poll() is None:
                w3.kill()

        pg_ctl(dbdir, pg_log, pg_port, "start")
        pg_started = True
        connections.close_all()
        close_old_connections()

        sales_count_mid = Sale.objects.count()
        lot_after_immed = Lot.objects.get(product=prod, number="L-11C-1").available_quantity
        counter_after_immed = SaleCounter.objects.get(id=1).next_value

        # Now cleanly execute via HTTP -> confirm V-00000002 -> immediate crash POST-commit -> retry
        ready4 = cluster / "ready4"
        w4, port4 = start_worker(
            worker_script=worker_script, pg_port=pg_port, dbname=dbname, pw_pg=pw_pg,
            secret_key=secret_key, barrier_file=None, ready_file=ready4,
        )
        try:
            op4, fields4 = http_login_and_get_checkout(f"http://127.0.0.1:{port4}")
            fields4["idempotency_key"] = saved_key2
            fields4["expected_subtotal"] = saved_sub2
            fields4["draft_signature"] = saved_sig2
            ok2_status, ok2_loc = fire_checkout_post(op4, f"http://127.0.0.1:{port4}", fields4)
        finally:
            w4.kill()
            w4.wait(timeout=5)

        connections.close_all()
        pg_ctl(dbdir, pg_log, pg_port, "stop", mode="immediate")
        pg_ctl(dbdir, pg_log, pg_port, "start")
        connections.close_all()
        close_old_connections()

        ready5 = cluster / "ready5"
        w5, port5 = start_worker(
            worker_script=worker_script, pg_port=pg_port, dbname=dbname, pw_pg=pw_pg,
            secret_key=secret_key, barrier_file=None, ready_file=ready5,
        )
        try:
            op5 = http_login(f"http://127.0.0.1:{port5}")
            r_close = op5.open(f"http://127.0.0.1:{port5}/caja/cerrar/")
            csrf_token5 = extract_csrf_and_hidden(r_close.read().decode("utf-8"))["csrfmiddlewaretoken"]
            replay_fields = {
                "csrfmiddlewaretoken": csrf_token5,
                "cash_received": "50.00",
                "idempotency_key": saved_key2,
                "expected_subtotal": saved_sub2,
                "draft_signature": saved_sig2,
            }
            replay_status, replay_loc = fire_checkout_post(op5, f"http://127.0.0.1:{port5}", replay_fields)
        finally:
            w5.kill()
            w5.wait(timeout=5)

        close_old_connections()
        sales_final = list(Sale.objects.order_by("correlative").values_list("correlative", "id"))
        lot_after_c02 = Lot.objects.get(product=prod, number="L-11C-1").available_quantity
        c02_ok = (
            bool(locks_obs3.get("backend_xids"))
            and sales_count_mid == 1
            and lot_after_immed == 7
            and counter_after_immed == 2
            and ok2_status == 302
            and replay_status == 302
            and ok2_loc == replay_loc
            and [r[0] for r in sales_final] == ["V-00000001", "V-00000002"]
            and lot_after_c02 == 5
        )
        report["scenarios"]["02_CT_ROLLBACK_01_C02_pg_immediate_crash"] = {
            "ok": c02_ok,
            "locks_before_precommit_crash": locks_obs3,
            "precommit_crash_state": {
                "sales_count": sales_count_mid,
                "lot_available": lot_after_immed,
                "counter_next": counter_after_immed,
            },
            "post_commit_crash_replay": {
                "first_commit": [ok2_status, ok2_loc],
                "post_recovery_replay": [replay_status, replay_loc],
                "same_receipt_location": ok2_loc == replay_loc,
                "correlatives": [r[0] for r in sales_final],
                "lot_available_after": lot_after_c02,
            },
        }

        # ── 03. NFR-05 & PT-CHECKOUT-01: 2,000 products / 10,000 lots benchmark ───────
        cats = [Category(name=f"Cat Bench {i}") for i in range(10)]
        Category.objects.bulk_create(cats)
        cats = list(Category.objects.filter(name__startswith="Cat Bench ").order_by("name"))
        prods_to_create = [
            Product(
                category=cats[i % 10],
                name=f"Prod Bench {i:04d}",
                barcode=f"7759{i:09d}",
                sale_price=Decimal("4.50"),
                average_cost=Decimal("2.1000"),
                minimum_stock=5,
                is_active=True,
            )
            for i in range(2000)
        ]
        Product.objects.bulk_create(prods_to_create, batch_size=500)
        bench_prods = list(Product.objects.filter(name__startswith="Prod Bench ").order_by("name"))
        today_lima = tz.localdate()
        lots_to_create = []
        for idx, bp in enumerate(bench_prods):
            lots_to_create.append(
                Lot(product=bp, number=f"EXP-{idx}", quantity_received=10, available_quantity=10, unit_cost=Decimal("2.0000"), expiration_date=today_lima - timedelta(days=1), supplier=sup)
            )
            for k in range(1, 5):
                lots_to_create.append(
                    Lot(product=bp, number=f"OK-{idx}-{k}", quantity_received=200, available_quantity=200, unit_cost=Decimal("2.1000"), expiration_date=today_lima + timedelta(days=10 * k), supplier=sup)
                )
        Lot.objects.bulk_create(lots_to_create, batch_size=2000)

        with psycopg.connect(host="127.0.0.1", port=pg_port, user="audit11c", password=pw_pg, dbname=dbname, autocommit=True) as conn:
            conn.execute("ANALYZE")

        # Measure queries and 30 sequential checkouts (HTTP Client -> checkout view -> PG 18.4)
        client = Client()
        client.force_login(seller)
        seq_latencies_ms: list[float] = []
        get_queries_1line = 0
        post_queries_1line = 0
        post_queries_5line = 0

        for i in range(30):
            add_product_to_draft(actor=seller, product_id=bench_prods[i].pk, quantity=2)
            with CaptureQueriesContext(connections["default"]) as ctx_get:
                g = client.get("/ventas/cobrar/")
            assert g.status_code == 200
            if i == 0:
                get_queries_1line = len(ctx_get)
            form_obj = g.context["form"]
            payload = {
                "cash_received": "10.00",
                "idempotency_key": str(form_obj.initial["idempotency_key"]),
                "expected_subtotal": str(form_obj.initial["expected_subtotal"]),
                "draft_signature": str(form_obj.initial["draft_signature"]),
            }
            t0 = time.perf_counter()
            with CaptureQueriesContext(connections["default"]) as ctx_post:
                p_resp = client.post("/ventas/cobrar/", data=payload)
            dt_ms = (time.perf_counter() - t0) * 1000.0
            assert p_resp.status_code == 302, f"Seq checkout {i} failed: {p_resp.status_code}"
            seq_latencies_ms.append(dt_ms)
            if i == 0:
                post_queries_1line = len(ctx_post)

        # 5-line cart query measurement
        for j in range(5):
            add_product_to_draft(actor=seller, product_id=bench_prods[100 + j].pk, quantity=1)
        g5 = client.get("/ventas/cobrar/")
        f5 = g5.context["form"]
        t0 = time.perf_counter()
        with CaptureQueriesContext(connections["default"]) as ctx_post5:
            p5 = client.post("/ventas/cobrar/", data={
                "cash_received": "50.00",
                "idempotency_key": str(f5.initial["idempotency_key"]),
                "expected_subtotal": str(f5.initial["expected_subtotal"]),
                "draft_signature": str(f5.initial["draft_signature"]),
            })
        dt5_ms = (time.perf_counter() - t0) * 1000.0
        assert p5.status_code == 302
        post_queries_5line = len(ctx_post5)

        # 4 concurrent sellers checking out simultaneously (4 batches x 4 workers = 16 checkouts)
        conc_sellers = []
        conc_regs = []
        for s_idx in range(4):
            u = Account.objects.create_user(
                email=f"conc{s_idx}@example.com", display_name=f"Conc {s_idx}", password=secrets.token_urlsafe(20), role=roles[Role.Code.SELLER]
            )
            r = CashRegister.objects.create(code=f"CAJA-BENCH-{s_idx}", is_active=True)
            open_cash_shift(actor=u, register=r, opening_amount=Decimal("50.00"))
            conc_sellers.append(u)
            conc_regs.append(r)

        conc_latencies_ms: list[float] = []
        conc_errors: list[str] = []
        barrier_conc = threading.Barrier(4)

        def run_conc_worker(w_idx: int, batch_round: int):
            close_old_connections()
            u = conc_sellers[w_idx]
            add_product_to_draft(actor=u, product_id=bench_prods[200 + w_idx * 10 + batch_round].pk, quantity=2)
            c = Client()
            c.force_login(u)
            gr = c.get("/ventas/cobrar/")
            fo = gr.context["form"]
            pay = {
                "cash_received": "20.00",
                "idempotency_key": str(fo.initial["idempotency_key"]),
                "expected_subtotal": str(fo.initial["expected_subtotal"]),
                "draft_signature": str(fo.initial["draft_signature"]),
            }
            barrier_conc.wait(timeout=10)
            st = time.perf_counter()
            pr = c.post("/ventas/cobrar/", data=pay)
            elapsed = (time.perf_counter() - st) * 1000.0
            close_old_connections()
            return pr.status_code, elapsed

        for br in range(4):
            barrier_conc = threading.Barrier(4)
            with ThreadPoolExecutor(max_workers=4) as pool:
                futs = [pool.submit(run_conc_worker, wi, br) for wi in range(4)]
                for fut in futs:
                    st_code, el_ms = fut.result(timeout=20)
                    conc_latencies_ms.append(el_ms)
                    if st_code != 302:
                        conc_errors.append(str(st_code))

        def pct(vals: list[float], p: float) -> float:
            s = sorted(vals)
            idx = min(len(s) - 1, max(0, int(round((len(s) - 1) * p))))
            return round(s[idx], 2)

        seq_p95 = pct(seq_latencies_ms, 0.95)
        conc_p95 = pct(conc_latencies_ms, 0.95)
        bench_ok = len(conc_errors) == 0 and seq_p95 <= 3000.0 and conc_p95 <= 3000.0
        report["scenarios"]["03_NFR05_PT_CHECKOUT_01_volume_pg18"] = {
            "ok": bench_ok,
            "dataset": {
                "products_total": Product.objects.count(),
                "lots_total": Lot.objects.count(),
            },
            "queries": {
                "get_checkout_1line": get_queries_1line,
                "post_checkout_1line": post_queries_1line,
                "post_checkout_5line": post_queries_5line,
                "post_5line_latency_ms": round(dt5_ms, 2),
            },
            "sequential_n30": {
                "min_ms": round(min(seq_latencies_ms), 2),
                "p50_ms": round(statistics.median(seq_latencies_ms), 2),
                "p95_ms": seq_p95,
                "max_ms": round(max(seq_latencies_ms), 2),
                "within_NFR05_3000ms": seq_p95 <= 3000.0,
                "within_legacy_PT_CHECKOUT_500ms": seq_p95 <= 500.0,
            },
            "concurrent_4x4_n16": {
                "errors": conc_errors,
                "min_ms": round(min(conc_latencies_ms), 2),
                "p50_ms": round(statistics.median(conc_latencies_ms), 2),
                "p95_ms": conc_p95,
                "max_ms": round(max(conc_latencies_ms), 2),
                "within_NFR05_3000ms": conc_p95 <= 3000.0,
                "within_legacy_PT_CHECKOUT_500ms": conc_p95 <= 500.0,
            },
        }

        # ── 04. Lock compatibility: checkout vs entry, write-off, product update ─
        from django.db import OperationalError  # noqa: E402
        from inventory.services import StockReceiptLineInput, create_write_off, register_stock_entry  # noqa: E402
        from catalog.services import update_product  # noqa: E402
        from sales.services import checkout_sale  # noqa: E402

        shared_prod = bench_prods[500]
        deadlocks = 0
        lock_outcomes = []
        for round_i in range(4):
            close_old_connections()
            u_w = conc_sellers[0]
            shared_prod.refresh_from_db()
            SaleDraft.objects.filter(seller=u_w, status=SaleDraft.Status.ACTIVE).update(status=SaleDraft.Status.DISCARDED)
            draft_w = add_product_to_draft(actor=u_w, product_id=shared_prod.pk, quantity=1)
            k_w = uuid.uuid4()
            b_lock = threading.Barrier(3)

            def task_chk():
                close_old_connections()
                b_lock.wait(timeout=10)
                try:
                    s = checkout_sale(actor=u_w, draft_id=draft_w.pk, cash_received=Decimal("10.00"), idempotency_key=k_w)
                    return ("chk_ok", s.correlative)
                except Exception as exc:
                    return ("chk_err", type(exc).__name__, str(exc))
                finally:
                    close_old_connections()

            def task_entry():
                close_old_connections()
                b_lock.wait(timeout=10)
                try:
                    register_stock_entry(
                        actor=warehouse,
                        supplier=sup,
                        reference=f"REF-LC-{round_i}",
                        idempotency_key=uuid.uuid4(),
                        lines=[StockReceiptLineInput(product=shared_prod, lot_number=f"L-LC-{round_i}", quantity=5, unit_cost=Decimal("2.2000"), expiration_date=today_lima + timedelta(days=60))],
                    )
                    return ("entry_ok",)
                except Exception as exc:
                    return ("entry_err", type(exc).__name__, str(exc))
                finally:
                    close_old_connections()

            def task_prod_edit():
                close_old_connections()
                b_lock.wait(timeout=10)
                try:
                    update_product(
                        actor=admin,
                        product=shared_prod,
                        category=shared_prod.category,
                        name=shared_prod.name,
                        barcode=shared_prod.barcode,
                        sale_price=Decimal("4.55") if round_i % 2 == 0 else Decimal("4.50"),
                        minimum_stock=5,
                    )
                    return ("prod_ok",)
                except Exception as exc:
                    return ("prod_err", type(exc).__name__, str(exc))
                finally:
                    close_old_connections()

            with ThreadPoolExecutor(max_workers=3) as pool:
                r1, r2, r3 = [f.result(timeout=20) for f in (pool.submit(task_chk), pool.submit(task_entry), pool.submit(task_prod_edit))]
            for item in (r1, r2, r3):
                if len(item) >= 3 and "deadlock" in item[2].lower():
                    deadlocks += 1
            lock_outcomes.append([r1, r2, r3])
            shared_prod.refresh_from_db()

        with psycopg.connect(host="127.0.0.1", port=pg_port, user="audit11c", password=pw_pg, dbname=dbname) as conn:
            conn.execute("SELECT pg_stat_force_next_flush()")
            time.sleep(0.15)
            conn.execute("SELECT pg_stat_clear_snapshot()")
            deadlocks_pg = conn.execute("SELECT deadlocks FROM pg_stat_database WHERE datname = %s", (dbname,)).fetchone()[0]

        report["scenarios"]["04_LOCK_COMPATIBILITY_pg18"] = {
            "ok": deadlocks == 0 and deadlocks_pg == 0,
            "python_deadlocks": deadlocks,
            "pg_stat_database_deadlocks": deadlocks_pg,
            "rounds": lock_outcomes,
        }

    finally:
        if connections is not None:
            connections.close_all()
        if pg_started:
            subprocess.run(
                [str(PG_BIN / "pg_ctl.exe"), "-D", str(dbdir), "-m", "immediate", "-w", "stop"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW,
            )
        if cluster.exists() and (cluster / "AUDIT11C_OWNED").is_file():
            shutil.rmtree(cluster, ignore_errors=True)

    with socket.socket() as s:
        port_closed = s.connect_ex(("127.0.0.1", pg_port)) != 0

    build_after = build_snapshot()
    prod_db_after = sha_bytes(prod_db.read_bytes())
    report["finished_utc"] = datetime.now(dt_timezone.utc).isoformat()
    report["port_closed"] = port_closed
    report["build_after"] = build_after
    report["sources_stable"] = build_before == build_after
    report["prod_db_unchanged"] = prod_db_before == prod_db_after
    report["all_scenarios_ok"] = all(v.get("ok") for v in report["scenarios"].values())

    out_path = OUT / "pg11c_report.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"out": str(out_path), "all_scenarios_ok": report["all_scenarios_ok"], "port_closed": port_closed, "sources_stable": report["sources_stable"], "prod_db_unchanged": report["prod_db_unchanged"]}, ensure_ascii=False))
    return 0 if (report["all_scenarios_ok"] and port_closed and report["sources_stable"] and report["prod_db_unchanged"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
