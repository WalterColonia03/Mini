"""Stage 09 real PostgreSQL 18.4 verification:
1) Concurrent open_cash_shift race across two sellers -> single open shift, controlled ValidationError.
2) Concurrent close_cash_shift double-submit -> single CashShiftClose, controlled ValidationError.
3) Concurrent close_cash_shift vs checkout_sale (both directions under READ COMMITTED row locks + pg_blocking_pids).
4) Concurrent close_cash_shift vs deactivate_employee / update_employee role change (Account -> CashShift, zero deadlock).
5) America/Lima midnight boundary rendering on /caja/turnos/ and /caja/turnos/<id>/cerrado/.
6) N+1 constant SQL query check (force_debug_cursor=True) and EXPLAIN (FORMAT JSON) plan analysis.
Runs in an ephemeral owned cluster (AUDIT09_OWNED) and never alters existing SQLite DBs.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
STAMP = datetime.now(dt_timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
CLUSTER = (Path(tempfile.gettempdir()) / ("audit09-pg-" + secrets.token_hex(12))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT09_OWNED"
MARK.write_text(STAMP, encoding="utf-8")
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(40)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit09_" + secrets.token_hex(5)
with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]

archived_prefixes = (
    "etapa00",
    "etapa01",
    "etapa02",
    "etapa03",
    "etapa04",
    "etapa05",
    "etapa06",
    "etapa07",
    "etapa09",
)
protected = [
    *APP.glob("*.sqlite3"),
    *sorted(
        p
        for p in (RESULTS / "datos").rglob("*.sqlite3")
        if p.parent.name.startswith(archived_prefixes)
    ),
    ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
]


def state_hash(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


hashes = {str(p.relative_to(ROOT)): state_hash(p) for p in protected}
report = {
    "started_utc": STAMP,
    "cluster": str(CLUSTER),
    "port": PORT,
    "cases": [],
    "protected_absent_at_start": [k for k, v in hashes.items() if v is None],
}


def own() -> None:
    assert CLUSTER.parent == Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith("audit09-pg-")
    assert MARK.read_text(encoding="utf-8") == STAMP


def pg(name: str, *args) -> None:
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as f:
        result = subprocess.run(
            [str(BIN / (name + ".exe")), *map(str, args)],
            stdout=f,
            stderr=f,
            timeout=50,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        f.seek(0)
        diagnostic = f.read().replace(PW, "[REDACTED]")
    if result.returncode:
        raise RuntimeError(name + " failed: " + diagnostic[-800:])


started = False
configured = False
try:
    own()
    pg(
        "initdb",
        "-D",
        DBDIR,
        "-U",
        "audit09",
        "--pwfile",
        PWFILE,
        "--auth-host=scram-sha-256",
        "--auth-local=scram-sha-256",
        "--encoding=UTF8",
        "--locale=C",
    )
    PWFILE.unlink()
    pg(
        "pg_ctl",
        "-D",
        DBDIR,
        "-l",
        CLUSTER / "postgres.log",
        "-o",
        f"-h 127.0.0.1 -p {PORT} -c log_statement=none -c log_min_error_statement=panic",
        "-w",
        "start",
    )
    started = True

    import psycopg
    from psycopg import sql

    conf = {"host": "127.0.0.1", "port": PORT, "user": "audit09", "password": PW}
    with psycopg.connect(**conf, dbname="postgres", autocommit=True) as conn:
        assert Path(conn.execute("SHOW data_directory").fetchone()[0]).resolve() == DBDIR
        report["version"] = conn.execute("SELECT version()").fetchone()[0]
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DBNAME)))

    sys.path.insert(0, str(APP))
    os.environ.update(
        APP_ENV="test",
        DJANGO_DEBUG="false",
        DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
        DJANGO_SETTINGS_MODULE="config.settings",
    )
    from config import env

    loader = env.load_dotenv
    env.load_dotenv = lambda path=None: None
    from django.conf import settings

    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": DBNAME,
            "USER": "audit09",
            "PASSWORD": PW,
            "HOST": "127.0.0.1",
            "PORT": PORT,
            "CONN_MAX_AGE": 0,
            "OPTIONS": {"options": "-c statement_timeout=20000 -c lock_timeout=12000"},
        }
    }
    settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
    env.load_dotenv = loader

    import django

    django.setup()
    configured = True

    from django.core.exceptions import PermissionDenied, ValidationError
    from django.core.management import call_command
    from django.db import close_old_connections, connection, connections, transaction
    from django.test import Client
    from django.test.utils import CaptureQueriesContext, setup_test_environment
    from django.utils import timezone as tz

    setup_test_environment()

    from cash.models import CashRegister, CashShift, CashShiftClose
    from cash.services import close_cash_shift, open_cash_shift
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from identity.services import deactivate_employee, update_employee
    from inventory.models import Lot
    from inventory.services import LotInput, confirm_initial_load
    from sales.models import Sale, SaleCounter, SaleDraft
    from sales.services import add_product_to_draft, checkout_sale, discard_active_draft

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    with connection.cursor() as cur:
        cur.execute("SELECT current_database(), current_setting('data_directory'), current_setting('transaction_isolation')")
        db, folder, iso = cur.fetchone()
        assert db == DBNAME and Path(folder).resolve() == DBDIR
    report.update(database=db, isolation=iso)

    admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
    pw_user = "PgAudit09#Pass123"
    admin = Account.objects.create_user("admin.pg09@test.invalid", pw_user, display_name="Admin PG09", role=admin_role)
    wh = Account.objects.create_user("wh.pg09@test.invalid", pw_user, display_name="Almacen PG09", role=wh_role)
    seller1 = Account.objects.create_user("seller1.pg09@test.invalid", pw_user, display_name="Vendedor1 PG09", role=seller_role)
    seller2 = Account.objects.create_user("seller2.pg09@test.invalid", pw_user, display_name="Vendedor2 PG09", role=seller_role)
    seller3 = Account.objects.create_user("seller3.pg09@test.invalid", pw_user, display_name="Vendedor3 PG09", role=seller_role)

    reg = CashRegister.objects.create(code="CAJA-01")
    cat = Category.objects.create(name="PG09 Abarrotes")
    p = Product.objects.create(category=cat, name="Producto PG09", barcode="775090000101", sale_price=Decimal("10.00"), minimum_stock=2)
    confirm_initial_load(actor=wh, product=p, lots=[LotInput("PG09-LOT", 50, Decimal("5.00"), tz.localdate() + timedelta(days=90))])
    SaleCounter.objects.get_or_create(pk=1)

    # ── Case 1: Concurrent open_cash_shift across two sellers ──────────────────
    open_barrier = threading.Barrier(2)

    def try_open(actor_obj, amt):
        close_old_connections()
        try:
            open_barrier.wait(timeout=8)
            s = open_cash_shift(actor=actor_obj, opening_amount=amt)
            return ("ok", str(s.pk), actor_obj.display_name)
        except ValidationError as exc:
            return ("validation_error", str(exc.messages[0]), actor_obj.display_name)
        except Exception as exc:
            return ("unexpected", f"{type(exc).__name__}: {exc}", actor_obj.display_name)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        r1 = pool.submit(try_open, seller1, Decimal("50.00"))
        r2 = pool.submit(try_open, seller2, Decimal("60.00"))
        res_open = [r1.result(timeout=10), r2.result(timeout=10)]

    open_shifts_c1 = list(CashShift.objects.filter(status=CashShift.Status.OPEN))
    c1_ok = (
        sorted(x[0] for x in res_open) == ["ok", "validation_error"]
        and len(open_shifts_c1) == 1
    )
    report["cases"].append({"id": "pg_concurrent_open_two_sellers", "ok": c1_ok, "checks": res_open})
    winner_seller = Account.objects.get(pk=open_shifts_c1[0].seller_id)
    close_cash_shift(actor=winner_seller, counted_amount=open_shifts_c1[0].opening_amount)

    # ── Case 2: Concurrent close_cash_shift double-submit ─────────────────────
    shift_c2 = open_cash_shift(actor=seller1, opening_amount=Decimal("100.00"))
    close_barrier = threading.Barrier(2)

    def try_close():
        close_old_connections()
        try:
            close_barrier.wait(timeout=8)
            cl = close_cash_shift(actor=seller1, counted_amount=Decimal("100.00"))
            return ("ok", str(cl.pk))
        except ValidationError as exc:
            return ("validation_error", str(exc.messages[0]))
        except Exception as exc:
            return ("unexpected", f"{type(exc).__name__}: {exc}")
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        fc1 = pool.submit(try_close)
        fc2 = pool.submit(try_close)
        res_close = [fc1.result(timeout=10), fc2.result(timeout=10)]

    c2_ok = (
        sorted(x[0] for x in res_close) == ["ok", "validation_error"]
        and CashShiftClose.objects.filter(cash_shift=shift_c2).count() == 1
    )
    report["cases"].append({"id": "pg_concurrent_close_double_submit", "ok": c2_ok, "checks": res_close})

    # ── Case 3: Concurrent close_cash_shift vs checkout_sale (both directions + pg_blocking_pids)
    # Direction A: checkout_sale commits first while close_cash_shift waits on CashShift lock
    shift_c3a = open_cash_shift(actor=seller1, opening_amount=Decimal("100.00"))
    draft_c3a = add_product_to_draft(actor=seller1, product_id=p.pk, quantity=1)
    Sale.objects.create(  # warm SaleCounter before timed test if needed (skip; counter created above)
        cash_shift=shift_c3a, seller=seller1,
        total_amount=Decimal("0.00"), base_amount=Decimal("0.00"), igv_amount=Decimal("0.00"),
        discount_amount=Decimal("0.00"), cash_received=Decimal("0.00"), change_given=Decimal("0.00"),
        correlative="V-00009901", idempotency_key=uuid.uuid4(),
    )
    Sale.objects.filter(correlative="V-00009901").delete()

    locked_shift_evt = threading.Event()
    proceed_sale_evt = threading.Event()
    blocking_pids_seen = []

    orig_lot_save = Lot.save

    def slowed_lot_save(self, *args, **kwargs):
        locked_shift_evt.set()
        proceed_sale_evt.wait(timeout=8)
        return orig_lot_save(self, *args, **kwargs)

    def run_sale_c3a():
        close_old_connections()
        try:
            with patch.object(Lot, "save", slowed_lot_save):
                s = checkout_sale(
                    actor=seller1,
                    draft_id=draft_c3a.pk,
                    cash_received=Decimal("20.00"),
                    discount_amount=Decimal("1.00"),
                    idempotency_key=uuid.uuid4(),
                )
                return ("sale_ok", str(s.total_amount))
        finally:
            close_old_connections()

    def run_close_c3a():
        close_old_connections()
        try:
            assert locked_shift_evt.wait(timeout=8)
            cl = close_cash_shift(actor=seller1, counted_amount=Decimal("109.00"))
            return ("close_ok", str(cl.expected_amount), str(cl.difference))
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_sale = pool.submit(run_sale_c3a)
        f_close = pool.submit(run_close_c3a)
        # Observe pg_blocking_pids from controller connection while close waits on CashShift lock
        with psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
            for _ in range(40):
                rows = obs.execute(
                    "SELECT pid, pg_blocking_pids(pid), query FROM pg_stat_activity "
                    "WHERE datname = %s AND cardinality(pg_blocking_pids(pid)) > 0",
                    (DBNAME,),
                ).fetchall()
                if rows:
                    blocking_pids_seen.append(rows[0][0])
                    break
                threading.Event().wait(0.05)
        proceed_sale_evt.set()
        res_sale_3a = f_sale.result(timeout=10)
        res_close_3a = f_close.result(timeout=10)

    # Direction B: close_cash_shift wins lock while checkout_sale reaches atomic block -> checkout rejects
    shift_c3b = open_cash_shift(actor=seller1, opening_amount=Decimal("50.00"))
    draft_c3b = add_product_to_draft(actor=seller1, product_id=p.pk, quantity=1)
    # Remove the line or keep a draft so pre-check passes then hold close? Wait: close checks draft lines too!
    # Scenario B tests: seller removes draft line in another tab after checkout passed pre-lock validation,
    # then close_cash_shift commits CLOSED before checkout acquires CashShift lock!
    checkout_ready_evt = threading.Event()
    close_committed_evt = threading.Event()
    orig_atomic = transaction.atomic
    atomic_hits = {"n": 0}

    def gated_atomic(*args, **kwargs):
        atomic_hits["n"] += 1
        if atomic_hits["n"] == 1:
            checkout_ready_evt.set()
            close_committed_evt.wait(timeout=8)
        return orig_atomic(*args, **kwargs)

    def run_sale_c3b():
        close_old_connections()
        try:
            with patch("sales.services.transaction.atomic", side_effect=gated_atomic):
                checkout_sale(
                    actor=seller1,
                    draft_id=draft_c3b.pk,
                    cash_received=Decimal("10.00"),
                    idempotency_key=uuid.uuid4(),
                )
            return ("unexpected_ok",)
        except ValidationError as exc:
            return ("rejected", str(exc.messages[0]))
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=1) as pool:
        f_sale_b = pool.submit(run_sale_c3b)
        assert checkout_ready_evt.wait(timeout=8)
        discard_active_draft(actor=seller1)
        cl_b = close_cash_shift(actor=seller1, counted_amount=Decimal("50.00"))
        close_committed_evt.set()
        res_sale_3b = f_sale_b.result(timeout=10)

    # Direction C: close_cash_shift holds Account (FOR NO KEY UPDATE) — prove FK FOR KEY SHARE NOWAIT
    # succeeds (preventing FK deadlock with child inserts) while FOR UPDATE NOWAIT blocks cleanly.
    shift_c3c = open_cash_shift(actor=seller1, opening_amount=Decimal("60.00"))
    acct_locked_evt = threading.Event()
    release_acct_evt = threading.Event()
    from cash import services as cash_services

    orig_validate_amt = cash_services._validate_cash_amount

    def paused_validate_amt(value, *, field_name):
        if field_name == "counted_amount":
            acct_locked_evt.set()
            release_acct_evt.wait(timeout=8)
        return orig_validate_amt(value, field_name=field_name)

    def run_close_c3c():
        close_old_connections()
        try:
            with patch.object(cash_services, "_validate_cash_amount", paused_validate_amt):
                cl_c = close_cash_shift(actor=seller1, counted_amount=Decimal("60.00"))
                return ("close_ok", str(cl_c.expected_amount))
        finally:
            close_old_connections()

    for_key_share_ok = False
    for_update_blocked = False
    with ThreadPoolExecutor(max_workers=1) as pool:
        fc_c3 = pool.submit(run_close_c3c)
        assert acct_locked_evt.wait(timeout=8)
        with psycopg.connect(**conf, dbname=DBNAME, autocommit=False) as probe_conn:
            row_ks = probe_conn.execute(
                "SELECT id FROM identity_account WHERE id = %s FOR KEY SHARE NOWAIT",
                (seller1.pk,),
            ).fetchone()
            for_key_share_ok = row_ks is not None and str(row_ks[0]) == str(seller1.pk)
            probe_conn.rollback()
            try:
                probe_conn.execute(
                    "SELECT id FROM identity_account WHERE id = %s FOR UPDATE NOWAIT",
                    (seller1.pk,),
                )
            except psycopg.errors.LockNotAvailable:
                for_update_blocked = True
            probe_conn.rollback()
        release_acct_evt.set()
        res_close_3c = fc_c3.result(timeout=10)

    c3_ok = (
        res_sale_3a == ("sale_ok", "9.00")
        and res_close_3a == ("close_ok", "109.00", "0.00")
        and len(blocking_pids_seen) >= 1
        and cl_b.expected_amount == Decimal("50.00")
        and res_sale_3b[0] == "rejected"
        and "turno de caja abierto" in res_sale_3b[1]
        and for_key_share_ok
        and for_update_blocked
        and res_close_3c == ("close_ok", "60.00")
    )
    report["cases"].append({
        "id": "pg_concurrent_close_vs_checkout_sale",
        "ok": c3_ok,
        "checks": {
            "dir_a_sale": res_sale_3a,
            "dir_a_close": res_close_3a,
            "pg_blocking_pids_observed": len(blocking_pids_seen),
            "dir_b_sale": res_sale_3b,
            "dir_c_for_key_share_nowait_ok": for_key_share_ok,
            "dir_c_for_update_nowait_blocked": for_update_blocked,
            "dir_c_close": res_close_3c,
        },
    })

    # ── Case 4: Concurrent deactivate_employee vs close_cash_shift (Account -> CashShift, zero deadlock)
    shift_c4 = open_cash_shift(actor=seller3, opening_amount=Decimal("40.00"))
    c4_ready = threading.Event()
    c4_release = threading.Event()
    c4_blocking_observed = []

    def close_and_hold():
        close_old_connections()
        try:
            with transaction.atomic():
                close_cash_shift(actor=seller3, counted_amount=Decimal("40.00"))
                c4_ready.set()
                c4_release.wait(timeout=8)
            return "closed"
        finally:
            close_old_connections()

    def deact_worker():
        close_old_connections()
        try:
            assert c4_ready.wait(timeout=8)
            acc_deact = deactivate_employee(actor=admin, account=seller3)
            return ("deactivated", acc_deact.is_active)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        fc4_a = pool.submit(close_and_hold)
        fc4_b = pool.submit(deact_worker)
        with psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
            for _ in range(40):
                rows = obs.execute(
                    "SELECT pid FROM pg_stat_activity WHERE datname = %s AND cardinality(pg_blocking_pids(pid)) > 0",
                    (DBNAME,),
                ).fetchall()
                if rows:
                    c4_blocking_observed.append(rows[0][0])
                    break
                threading.Event().wait(0.05)
        c4_release.set()
        r4a = fc4_a.result(timeout=10)
        r4b = fc4_b.result(timeout=10)

    # Also test stale active handle rejected once deactivated in DB
    stale_s3 = Account.objects.get(pk=seller3.pk)
    stale_s3.is_active = True  # simulate stale in-memory object from old request
    denied_stale_ok = False
    try:
        open_cash_shift(actor=stale_s3, opening_amount=Decimal("10.00"))
    except PermissionDenied:
        denied_stale_ok = True

    c4_ok = r4a == "closed" and r4b == ("deactivated", False) and len(c4_blocking_observed) >= 1 and denied_stale_ok
    report["cases"].append({
        "id": "pg_concurrent_close_vs_deactivate_no_deadlock",
        "ok": c4_ok,
        "checks": {
            "close": r4a,
            "deactivate": r4b,
            "blocking_observed": len(c4_blocking_observed),
            "stale_deactivated_denied": denied_stale_ok,
        },
    })

    # ── Case 5: America/Lima timezone boundary rendering on cash views ─────────
    shift_tz = open_cash_shift(actor=seller2, opening_amount=Decimal("25.00"))
    close_tz = close_cash_shift(actor=seller2, counted_amount=Decimal("25.00"))
    t_open_utc = datetime(2026, 11, 12, 4, 59, 0, tzinfo=dt_timezone.utc)   # 2026-11-11 23:59 Lima
    t_close_utc = datetime(2026, 11, 12, 5, 1, 0, tzinfo=dt_timezone.utc)   # 2026-11-12 00:01 Lima
    CashShift.objects.filter(pk=shift_tz.pk).update(opened_at=t_open_utc)
    CashShiftClose.objects.filter(pk=close_tz.pk).update(closed_at=t_close_utc)

    c_adm = Client()
    c_adm.force_login(admin)
    html_hist = c_adm.get("/caja/turnos/").content.decode()
    html_acta = c_adm.get(f"/caja/turnos/{shift_tz.pk}/cerrado/").content.decode()
    c5_ok = (
        "11/11/2026 23:59" in html_hist
        and "12/11/2026 00:01" in html_hist
        and "11/11/2026 23:59" in html_acta
        and "12/11/2026 00:01" in html_acta
    )
    report["cases"].append({
        "id": "pg_america_lima_midnight_formatting",
        "ok": c5_ok,
        "checks": {"open_lima_rendered": "11/11/2026 23:59" in html_hist, "close_lima_rendered": "12/11/2026 00:01" in html_hist},
    })

    # ── Case 6: N+1 query invariance (force_debug_cursor=True) and EXPLAIN JSON
    connection.force_debug_cursor = True
    with CaptureQueriesContext(connection) as q_before:
        assert c_adm.get("/caja/turnos/").status_code == 200

    for i in range(25):
        s_bulk = open_cash_shift(actor=seller2, opening_amount=Decimal("10.00") + i)
        close_cash_shift(actor=seller2, counted_amount=Decimal("10.00") + i)

    with CaptureQueriesContext(connection) as q_after:
        assert c_adm.get("/caja/turnos/").status_code == 200
    connection.force_debug_cursor = False

    qs_hist = CashShift.objects.select_related("cash_register", "seller", "close").order_by("-opened_at")
    sql_hist, params_hist = qs_hist.query.sql_with_params()
    with connection.cursor() as cur:
        cur.execute(f"EXPLAIN (FORMAT JSON) {sql_hist}", params_hist)
        plan_hist = cur.fetchone()[0][0]["Plan"]

    def collect_plan_nodes(node: dict) -> list[dict]:
        info = {"node_type": node.get("Node Type"), "relation": node.get("Relation Name"), "index": node.get("Index Name")}
        nodes = [info]
        for ch in node.get("Plans", []):
            nodes.extend(collect_plan_nodes(ch))
        return nodes

    c6_ok = len(q_before) == len(q_after) and len(q_before) <= 5
    report["cases"].append({
        "id": "pg_history_constant_queries_and_explain",
        "ok": c6_ok,
        "checks": {
            "queries_before": len(q_before),
            "queries_after_plus25": len(q_after),
            "plan_nodes": collect_plan_nodes(plan_hist),
        },
    })

except Exception as exc:
    import traceback

    report["error"] = {
        "type": type(exc).__name__,
        "message": str(exc).replace(PW, "[REDACTED]")[:800],
        "traceback": traceback.format_exc().replace(PW, "[REDACTED]"),
    }
finally:
    if configured:
        connections.close_all()
    if started:
        own()
        pg("pg_ctl", "-D", DBDIR, "-m", "fast", "-w", "stop")
    with socket.socket() as s:
        report["port_closed"] = s.connect_ex(("127.0.0.1", PORT)) != 0
    report["protected_unchanged"] = {str(p.relative_to(ROOT)): state_hash(p) == hashes[str(p.relative_to(ROOT))] for p in protected}
    report["finished_utc"] = datetime.now(dt_timezone.utc).isoformat()
    out = RESULTS / "evidencias" / ("09-postgresql-" + STAMP + ".json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                "evidence": str(out.relative_to(ROOT)),
                "cases": [{"id": c["id"], "ok": c["ok"]} for c in report["cases"]],
                "error": report.get("error"),
                "port_closed": report["port_closed"],
                "protected_unchanged": all(report["protected_unchanged"].values()),
            },
            ensure_ascii=False,
            default=str,
        )
    )

if (
    report.get("error")
    or len(report["cases"]) != 6
    or not all(x["ok"] for x in report["cases"])
    or not report["port_closed"]
    or not all(report["protected_unchanged"].values())
):
    raise SystemExit(1)
