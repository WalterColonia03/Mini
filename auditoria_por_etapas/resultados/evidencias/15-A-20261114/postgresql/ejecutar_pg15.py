"""Stage 15 (15-A) Isolated Ephemeral PostgreSQL 18.4 Concurrency, Process-Kill Rollback, WAL Recovery & Backup/Restore Suite.

Creates an exclusively owned temporary PostgreSQL 18.4 cluster in TEMP, never touches any operational database or .env,
and stops/cleans the cluster on exit.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import contextlib
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from unittest.mock import patch
import uuid

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "r1-pmv/manage.py").exists())
HERE.mkdir(parents=True, exist_ok=True)
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
PYTHON = ROOT / "r1-pmv/.venv/Scripts/python.exe"
STAMP = datetime.now(dt_timezone.utc).isoformat()

CLUSTER = (Path(tempfile.gettempdir()) / ("audit15-pg-" + secrets.token_hex(10))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT15_OWNED"
MARK.write_text(STAMP, encoding="utf-8")
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(40)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit15_" + secrets.token_hex(5)
DBNAME_RESTORED = DBNAME + "_restored"

with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_build() -> dict:
    names = (
        subprocess.check_output(
            ["git", "-C", str(ROOT / "r1-pmv"), "ls-files", "-co", "--exclude-standard", "-z"]
        )
        .decode()
        .split("\0")
    )
    files = {
        n: digest((ROOT / "r1-pmv" / n).read_bytes())
        for n in sorted(set(names))
        if n
        and not n.startswith("evidencias/")
        and Path(n).suffix in {".py", ".html", ".css", ".js", ".svg", ".ps1", ".sh"}
    }
    return {
        "count": len(files),
        "sha256": digest(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()),
        "files": files,
    }


def own() -> None:
    assert CLUSTER.parent == Path(tempfile.gettempdir()).resolve()
    assert CLUSTER.name.startswith("audit15-pg-")
    assert MARK.read_text(encoding="utf-8") == STAMP


def pg(name: str, *args, env_extra: dict | None = None) -> str:
    own()
    run_env = os.environ.copy()
    if env_extra:
        run_env.update(env_extra)
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as f:
        r = subprocess.run(
            [str(BIN / (name + ".exe")), *map(str, args)],
            stdout=f,
            stderr=f,
            env=run_env,
            timeout=90,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        f.seek(0)
        text = f.read().replace(PW, "[REDACTED]")
    if r.returncode:
        raise RuntimeError(f"{name} failed ({r.returncode}): {text[-1200:]}")
    return text


report: dict = {
    "started_utc": STAMP,
    "etapa": "ETAPA-15",
    "sublote": "15-A-PG",
    "pasada": 1,
    "cursor_entrada": "15-SEGURIDAD-BASELINE-01",
    "cluster": str(CLUSTER),
    "database": DBNAME,
    "database_restored": DBNAME_RESTORED,
    "port": PORT,
    "plan08_sha256": digest((ROOT / "08_Historias_de_Usuario.md").read_bytes()),
    "head": subprocess.check_output(["git", "-C", str(ROOT / "r1-pmv"), "rev-parse", "HEAD"], text=True).strip(),
    "before_build": {k: v for k, v in compute_build().items() if k != "files"},
    "cases": [],
}


def save_report(filename: str = "resultados-pg15.json") -> None:
    (HERE / filename).write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )


def run_case(case_id: str, fn) -> None:
    t0 = time.monotonic()
    try:
        details = fn() or {}
        report["cases"].append(
            {"id": case_id, "ok": True, "seconds": round(time.monotonic() - t0, 3), **details}
        )
    except Exception as exc:
        report["cases"].append(
            {
                "id": case_id,
                "ok": False,
                "seconds": round(time.monotonic() - t0, 3),
                "error": type(exc).__name__,
                "detail": str(exc).replace(PW, "[REDACTED]"),
                "traceback": traceback.format_exc().replace(PW, "[REDACTED]"),
            }
        )
    save_report("resultados-pg15-partial.json")
    print(f"[{case_id}] ok={report['cases'][-1]['ok']}", flush=True)


started = False
try:
    # 0. Contrast current build/plan08 against 14-CIERRE 19 PostgreSQL cases
    def case_inherit_14_cierre() -> dict:
        pg14_dir = ROOT / "auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/postgresql/final"
        pg14_data = json.loads((pg14_dir / "results.json").read_text(encoding="utf-8"))
        pg14_compat = json.loads((pg14_dir / "compatibilidad-build.json").read_text(encoding="utf-8"))
        cur_build = compute_build()
        assert pg14_data["ok"] is True and pg14_data["passed"] == 19 and pg14_data["total"] == 19
        pg14_build_sha = pg14_data["before"]["sha256"]
        pg14_plan08_sha = pg14_compat["08_copy_sha256"]
        build_matches = pg14_build_sha == cur_build["sha256"]
        plan08_matches = pg14_plan08_sha == report["plan08_sha256"]
        return {
            "inherited_from": "14-CIERRE-20261114/postgresql/final/results.json",
            "inherited_status": "COMPATIBLE" if (build_matches and plan08_matches) else "HISTORICA_NO_REUTILIZABLE_POR_CAMBIO_DE_BUILD",
            "pg14_build_sha256": pg14_build_sha,
            "current_build_sha256": cur_build["sha256"],
            "pg14_plan08_sha256": pg14_plan08_sha,
            "current_plan08_sha256": report["plan08_sha256"],
            "build_matches": build_matches,
            "plan08_matches": plan08_matches,
            "inherited_cases_count": pg14_data["total"],
            "inherited_cases_passed": pg14_data["passed"],
            "inherited_case_ids": [c["id"] for c in pg14_data["cases"]],
        }

    run_case("PG15-00-contraste-herencia-14-CIERRE", case_inherit_14_cierre)

    # Initialize and start ephemeral PostgreSQL 18.4 cluster
    pg(
        "initdb",
        "-D",
        DBDIR,
        "-U",
        "audit15",
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

    pg_conf = {"host": "127.0.0.1", "port": PORT, "user": "audit15", "password": PW}
    with psycopg.connect(**pg_conf, dbname="postgres", autocommit=True) as conn:
        assert Path(conn.execute("SHOW data_directory").fetchone()[0]).resolve() == DBDIR
        report["postgres_version"] = conn.execute("SELECT version()").fetchone()[0]
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DBNAME)))

    sys.path.insert(0, str(ROOT / "r1-pmv"))
    os.environ.update(
        {
            "APP_ENV": "test",
            "DJANGO_DEBUG": "false",
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DJANGO_ALLOWED_HOSTS": "testserver,127.0.0.1,localhost",
        }
    )
    from config import env as config_env

    config_env.load_dotenv = lambda path=None: None
    from django.conf import settings

    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": DBNAME,
            "USER": "audit15",
            "PASSWORD": PW,
            "HOST": "127.0.0.1",
            "PORT": PORT,
            "CONN_MAX_AGE": 0,
            "OPTIONS": {"options": "-c statement_timeout=30000 -c lock_timeout=15000"},
        }
    }
    import django

    django.setup()
    from django.core.exceptions import PermissionDenied, ValidationError
    from django.core.management import call_command
    from django.db import IntegrityError, close_old_connections, connection, connections, transaction
    from django.test import Client
    from django.test.utils import setup_test_environment
    from django.urls import reverse
    from django.utils import timezone as tz
    from django.utils.crypto import salted_hmac

    from cash.models import CashRegister, CashShift, CashShiftClose
    from cash.services import close_cash_shift, open_cash_shift
    from catalog.models import Category, Product
    from catalog.services import create_category, register_canned_product, update_product
    from identity.models import Account, LoginAttempt, Role
    from identity.services import (
        create_employee,
        deactivate_employee,
        reactivate_employee,
        update_employee,
    )
    from inventory.models import (
        InitialInventoryLoad,
        Lot,
        PhysicalAdjustment,
        StockReceipt,
        StockWriteOff,
    )
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        register_physical_adjustment,
        register_stock_entry,
        write_off_stock,
    )
    from sales.models import Sale, SaleCounter, SaleDraft, SaleDraftLine, SaleLine, SaleLotAllocation
    from sales.services import add_product_to_draft, checkout_sale, discard_active_draft

    with (HERE / "migrations.txt").open("w", encoding="utf-8") as mlog, contextlib.redirect_stdout(
        mlog
    ), contextlib.redirect_stderr(mlog):
        call_command("migrate", interactive=False, verbosity=1)

    with connection.cursor() as cur:
        cur.execute(
            "SELECT current_database(), current_setting('data_directory'), current_setting('transaction_isolation')"
        )
        cur_db, cur_dir, cur_iso = cur.fetchone()
    assert cur_db == DBNAME and Path(cur_dir).resolve() == DBDIR
    report.update({"isolation": cur_iso, "migrated": True, "django": django.get_version()})
    setup_test_environment()

    PW_USER = "Audit15!Pass9"
    roles = {
        code: Role.objects.update_or_create(code=code, defaults={"name": code})[0]
        for code in ("ADMIN", "ALMACENERO", "VENDEDOR")
    }

    def make_actor(code: str, label: str, password: str = PW_USER) -> Account:
        return Account.objects.create_user(
            email=f"{label.lower()}@audit15.invalid",
            password=password,
            display_name=label,
            role=roles[code],
        )

    admin1 = make_actor("ADMIN", "Admin1PG15")
    admin2 = make_actor("ADMIN", "Admin2PG15")
    warehouse1 = make_actor("ALMACENERO", "Almacen1PG15")
    warehouse2 = make_actor("ALMACENERO", "Almacen2PG15")
    seller1 = make_actor("VENDEDOR", "Seller1PG15")
    seller2 = make_actor("VENDEDOR", "Seller2PG15")

    cat_main = create_category(actor=admin1, name="CategoriaPG15")
    reg1 = CashRegister.objects.get_or_create(code="CAJA-01")[0]
    reg2 = CashRegister.objects.get_or_create(code="CAJA-02")[0]
    future = tz.localdate() + timedelta(days=90)

    def make_product(label: str, qty: int = 10, cost: str = "3.0000", price: str = "10.00"):
        p = Product.objects.create(
            category=cat_main,
            name=label,
            barcode="PG15-" + label[:18],
            sale_price=Decimal(price),
        )
        load = confirm_initial_load(
            actor=warehouse1,
            product=p,
            lots=[LotInput("LOT-A", qty, Decimal(cost), future)],
        )
        return p, load.lots.get()

    def snapshot_tables(conn_obj=None) -> dict[str, str]:
        c_obj = conn_obj or connection
        with c_obj.cursor() as cur:
            tables = sorted(
                t
                for t in c_obj.introspection.table_names()
                if t.startswith(("identity_", "catalog_", "inventory_", "cash_", "sales_"))
                and t != "identity_loginattempt"
            )
            digests = {}
            for t in tables:
                cur.execute(f'SELECT * FROM "{t}" ORDER BY 1')
                digests[t] = digest(json.dumps(cur.fetchall(), default=str, sort_keys=True).encode())
            return digests

    def race_two(ops, lock_table: str):
        gate = threading.Barrier(2, timeout=15)
        locked = threading.Event()
        attempted = threading.Event()
        pids = {}
        waits = []

        def worker(i: int):
            close_old_connections()
            with connection.cursor() as cur:
                cur.execute("SELECT pg_backend_pid()")
                pids[i] = cur.fetchone()[0]
            first_hit = [False]

            def intercept(execute, query, params, many, context):
                match = ("FOR UPDATE" in query or "FOR NO KEY UPDATE" in query) and f'FROM "{lock_table}"' in query
                if i == 1 and match:
                    attempted.set()
                res = execute(query, params, many, context)
                if i == 0 and match and not first_hit[0]:
                    first_hit[0] = True
                    locked.set()
                    if not attempted.wait(12):
                        raise RuntimeError(f"Worker 1 did not reach FOR UPDATE on {lock_table}")
                    deadline = time.monotonic() + 12
                    while time.monotonic() < deadline:
                        with connection.cursor() as cur:
                            cur.execute("SELECT pg_blocking_pids(%s)", [pids[1]])
                            blockers = cur.fetchone()[0]
                        if pids[0] in blockers:
                            waits.append({"blocked": pids[1], "blocker": pids[0], "table": lock_table})
                            break
                        time.sleep(0.02)
                    if not waits:
                        raise RuntimeError(f"No PG lock wait observed on {lock_table}")
                return res

            try:
                gate.wait()
                if i == 1 and not locked.wait(12):
                    raise RuntimeError("Worker 0 did not acquire lock")
                with connection.execute_wrapper(intercept):
                    out = ops[i]()
                return {"result": "success", "value": str(getattr(out, "pk", out))}
            except Exception as exc:
                return {"result": type(exc).__name__, "detail": str(exc)}
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futs = [pool.submit(worker, i) for i in range(2)]
            results = [f.result(timeout=40) for f in futs]
        assert len(set(pids.values())) == 2 and waits, {"pids": pids, "waits": waits, "results": results}
        return {"pids": pids, "lock_waits": waits, "results": results}

    # PG15-01: Login concurrency (5th failure vs valid password on identity_loginattempt)
    def case_pg15_01_login() -> dict:
        user_login = make_actor("VENDEDOR", "LoginRacePG15")
        ident = salted_hmac("identity.login.throttle", user_login.email_normalized, algorithm="sha256").hexdigest()
        LoginAttempt.objects.create(identifier=ident, failures=4)

        def attempt_post(pw: str):
            cl = Client(enforce_csrf_checks=True)
            cl.get(reverse("login"))
            tok = cl.cookies[settings.CSRF_COOKIE_NAME].value
            resp = cl.post(
                reverse("login"),
                {"email": user_login.email, "password": pw, "csrfmiddlewaretoken": tok},
            )
            body = resp.content.decode("utf-8")
            return "bloqueo15" if "15 minuto(s)" in body else ("ok302" if resp.status_code == 302 else "credenciales")

        r = race_two(
            [lambda: attempt_post("WrongPass!99"), lambda: attempt_post(PW_USER)],
            "identity_loginattempt",
        )
        row = LoginAttempt.objects.get(identifier=ident)
        assert row.failures == 5 and row.locked_until is not None
        assert [x["value"] for x in r["results"]] == ["bloqueo15", "bloqueo15"]
        return {**r, "failures": row.failures, "locked_until": row.locked_until.isoformat()}

    run_case("PG15-01-login-5to-fallo-vs-clave-correcta", case_pg15_01_login)

    # PG15-02: Mutual deactivation of last two active ADMINs
    def case_pg15_02_last_admin() -> dict:
        # Ensure only admin1 and admin2 are active ADMINs
        Account.objects.filter(role=roles["ADMIN"]).exclude(pk__in=[admin1.pk, admin2.pk]).update(is_active=False)
        Account.objects.filter(pk__in=[admin1.pk, admin2.pk]).update(is_active=True)
        r = race_two(
            [
                lambda: deactivate_employee(actor=Account.objects.get(pk=admin1.pk), account=Account.objects.get(pk=admin2.pk)),
                lambda: deactivate_employee(actor=Account.objects.get(pk=admin2.pk), account=Account.objects.get(pk=admin1.pk)),
            ],
            "identity_role",
        )
        active_admins = Account.objects.filter(role=roles["ADMIN"], is_active=True).count()
        assert active_admins == 1
        assert [x["result"] for x in r["results"]] == ["success", "ValidationError"]
        # Restore both admins active
        Account.objects.filter(pk__in=[admin1.pk, admin2.pk]).update(is_active=True)
        return {**r, "active_admins_after_race": active_admins}

    run_case("PG15-02-ultimo-admin-desactivacion-mutua", case_pg15_02_last_admin)

    # PG15-03: Duplicate normalized employee email race
    def case_pg15_03_duplicate_email() -> dict:
        r = race_two(
            [
                lambda: create_employee(
                    actor=admin1,
                    display_name="Dup Uno",
                    email="  Dup.Email@audit15.invalid ",
                    role=roles["VENDEDOR"],
                    password=PW_USER,
                ),
                lambda: create_employee(
                    actor=admin2,
                    display_name="Dup Dos",
                    email="dup.email@AUDIT15.INVALID",
                    role=roles["VENDEDOR"],
                    password=PW_USER,
                ),
            ],
            "identity_role",
        )
        count = Account.objects.filter(email_normalized="dup.email@audit15.invalid").count()
        assert count == 1
        assert [x["result"] for x in r["results"]] == ["success", "ValidationError"]
        return {**r, "persisted_accounts": count}

    run_case("PG15-03-empleado-correo-duplicado-normalizado", case_pg15_03_duplicate_email)

    # PG15-04: Deactivate seller vs open_cash_shift & checkout_sale vs deactivate_employee
    def case_pg15_04_deactivate_vs_sales_and_cash() -> dict:
        CashShift.objects.filter(status="OPEN").update(status="CLOSED")
        s_temp = make_actor("VENDEDOR", "SellerDeactPG15")
        # Subcase A: deactivate_employee first vs open_cash_shift second
        r_a = race_two(
            [
                lambda: deactivate_employee(actor=admin1, account=Account.objects.get(pk=s_temp.pk)),
                lambda: open_cash_shift(actor=Account.objects.get(pk=s_temp.pk), opening_amount=Decimal("20.00")),
            ],
            "identity_account",
        )
        s_temp.refresh_from_db()
        assert not s_temp.is_active
        assert CashShift.objects.filter(seller=s_temp, status="OPEN").count() == 0
        assert [x["result"] for x in r_a["results"]] == ["success", "PermissionDenied"]

        # Subcase B: reactivate s_temp, open shift, prepare draft; checkout_sale first vs deactivate_employee second
        reactivate_employee(actor=admin1, account=s_temp)
        sh = open_cash_shift(actor=s_temp, opening_amount=Decimal("25.00"))
        p, _ = make_product("ProdDeactCheckout", qty=5)
        dr = add_product_to_draft(actor=s_temp, product_id=p.pk, quantity=2)
        r_b = race_two(
            [
                lambda: checkout_sale(
                    actor=s_temp,
                    draft_id=dr.pk,
                    cash_received=Decimal("20.00"),
                    idempotency_key=uuid.uuid4(),
                ),
                lambda: deactivate_employee(actor=admin1, account=Account.objects.get(pk=s_temp.pk)),
            ],
            "identity_account",
        )
        s_temp.refresh_from_db()
        assert s_temp.is_active is True
        assert Sale.objects.filter(cash_shift=sh).count() == 1
        assert [x["result"] for x in r_b["results"]] == ["success", "ValidationError"]
        close_cash_shift(actor=s_temp, counted_amount=Decimal("45.00"))
        return {"deactivate_vs_open": r_a, "checkout_vs_deactivate_with_open_shift": r_b}

    run_case("PG15-04-desactivar-vendedor-vs-turno-y-cobro", case_pg15_04_deactivate_vs_sales_and_cash)

    # PG15-05: Role change vs add_product_to_draft / open_cash_shift
    def case_pg15_05_role_change_races() -> dict:
        CashShift.objects.filter(status="OPEN").update(status="CLOSED")
        s_role = make_actor("VENDEDOR", "SellerRolePG15")
        p, _ = make_product("ProdRoleRace", qty=5)
        # Subcase A: role change VENDEDOR->ALMACENERO first vs open_cash_shift second
        r_a = race_two(
            [
                lambda: update_employee(
                    actor=admin1,
                    account=Account.objects.get(pk=s_role.pk),
                    display_name=s_role.display_name,
                    email=s_role.email,
                    role=roles["ALMACENERO"],
                ),
                lambda: open_cash_shift(actor=Account.objects.get(pk=s_role.pk), opening_amount=Decimal("15.00")),
            ],
            "identity_account",
        )
        assert [x["result"] for x in r_a["results"]] == ["success", "PermissionDenied"]

        # Restore VENDEDOR, open shift, race add_product_to_draft first vs role change second
        update_employee(
            actor=admin1,
            account=s_role,
            display_name=s_role.display_name,
            email=s_role.email,
            role=roles["VENDEDOR"],
        )
        open_cash_shift(actor=s_role, opening_amount=Decimal("15.00"))
        r_b = race_two(
            [
                lambda: add_product_to_draft(actor=s_role, product_id=p.pk, quantity=1),
                lambda: update_employee(
                    actor=admin1,
                    account=Account.objects.get(pk=s_role.pk),
                    display_name=s_role.display_name,
                    email=s_role.email,
                    role=roles["ALMACENERO"],
                ),
            ],
            "identity_account",
        )
        assert [x["result"] for x in r_b["results"]] == ["success", "ValidationError"]
        discard_active_draft(actor=s_role)
        close_cash_shift(actor=s_role, counted_amount=Decimal("15.00"))
        return {"role_change_vs_open": r_a, "add_draft_vs_role_change_with_open_shift": r_b}

    run_case("PG15-05-cambio-rol-vs-caja-y-borrador", case_pg15_05_role_change_races)

    # PG15-06: Logout (discard_active_draft) vs checkout_sale
    def case_pg15_06_logout_vs_checkout() -> dict:
        CashShift.objects.filter(status="OPEN").update(status="CLOSED")
        sh = open_cash_shift(actor=seller1, opening_amount=Decimal("30.00"))
        p, lot = make_product("ProdLogoutRace", qty=10)
        # Subcase A: discard_active_draft (logout) wins lock first -> checkout_sale fails with ValidationError
        dr1 = add_product_to_draft(actor=seller1, product_id=p.pk, quantity=3)
        r_discard_first = race_two(
            [
                lambda: discard_active_draft(actor=seller1),
                lambda: checkout_sale(
                    actor=seller1,
                    draft_id=dr1.pk,
                    cash_received=Decimal("30.00"),
                    idempotency_key=uuid.uuid4(),
                ),
            ],
            "identity_account",
        )
        lot.refresh_from_db()
        assert [x["result"] for x in r_discard_first["results"]] == ["success", "ValidationError"]
        assert lot.available_quantity == 10 and Sale.objects.filter(cash_shift=sh).count() == 0

        # Subcase B: checkout_sale wins lock first -> sale commits, discard_active_draft returns False cleanly
        dr2 = add_product_to_draft(actor=seller1, product_id=p.pk, quantity=3)
        r_checkout_first = race_two(
            [
                lambda: checkout_sale(
                    actor=seller1,
                    draft_id=dr2.pk,
                    cash_received=Decimal("30.00"),
                    idempotency_key=uuid.uuid4(),
                ),
                lambda: discard_active_draft(actor=seller1),
            ],
            "identity_account",
        )
        lot.refresh_from_db()
        assert [x["result"] for x in r_checkout_first["results"]] == ["success", "success"]
        assert r_checkout_first["results"][1]["value"] == "False"
        assert lot.available_quantity == 7 and Sale.objects.filter(cash_shift=sh).count() == 1
        close_cash_shift(actor=seller1, counted_amount=Decimal("60.00"))
        return {"discard_first": r_discard_first, "checkout_first": r_checkout_first}

    run_case("PG15-06-logout-descarte-vs-checkout-venta", case_pg15_06_logout_vs_checkout)

    # PG15-07 & PG15-08: Concurrent open_cash_shift on CAJA-01 and concurrent close_cash_shift on same shift
    def case_pg15_07_08_cash_open_and_close_races() -> dict:
        CashShift.objects.filter(status="OPEN").update(status="CLOSED")
        r_open = race_two(
            [
                lambda: open_cash_shift(actor=seller1, opening_amount=Decimal("20.00")),
                lambda: open_cash_shift(actor=seller2, opening_amount=Decimal("25.00")),
            ],
            "cash_cashregister",
        )
        assert [x["result"] for x in r_open["results"]] == ["success", "ValidationError"]
        assert CashShift.objects.filter(cash_register=reg1, status="OPEN").count() == 1

        r_close = race_two(
            [
                lambda: close_cash_shift(actor=seller1, counted_amount=Decimal("20.00")),
                lambda: close_cash_shift(actor=seller1, counted_amount=Decimal("20.00")),
            ],
            "identity_account",
        )
        assert [x["result"] for x in r_close["results"]] == ["success", "ValidationError"]
        assert CashShift.objects.filter(cash_register=reg1, status="OPEN").count() == 0
        return {"concurrent_open_register": r_open, "concurrent_close_shift": r_close}

    run_case("PG15-07-08-apertura-y-cierre-caja-concurrentes", case_pg15_07_08_cash_open_and_close_races)

    # PG15-09: Concurrent FEFO multi-lot sales & SaleCounter serialization + RN-14 reset at physical zero
    def case_pg15_09_fefo_multilot_and_counter() -> dict:
        CashShift.objects.filter(status="OPEN").update(status="CLOSED")
        sh1 = CashShift.objects.create(cash_register=reg1, seller=seller1, opening_amount=Decimal("50.00"))
        sh2 = CashShift.objects.create(cash_register=reg2, seller=seller2, opening_amount=Decimal("50.00"))
        p = Product.objects.create(
            category=cat_main,
            name="ProdFEFOCero",
            barcode="PG15-FEFO-001",
            sale_price=Decimal("10.00"),
        )
        load = confirm_initial_load(
            actor=warehouse1,
            product=p,
            lots=[
                LotInput("FEFO-1", 3, Decimal("4.0000"), tz.localdate() + timedelta(days=15)),
                LotInput("FEFO-2", 5, Decimal("6.0000"), tz.localdate() + timedelta(days=45)),
            ],
        )
        dr1 = add_product_to_draft(actor=seller1, product_id=p.pk, quantity=4)
        dr2 = add_product_to_draft(actor=seller2, product_id=p.pk, quantity=4)

        r = race_two(
            [
                lambda: checkout_sale(
                    actor=seller1, draft_id=dr1.pk, cash_received=Decimal("40.00"), idempotency_key=uuid.uuid4()
                ),
                lambda: checkout_sale(
                    actor=seller2, draft_id=dr2.pk, cash_received=Decimal("40.00"), idempotency_key=uuid.uuid4()
                ),
            ],
            "catalog_product",
        )
        assert [x["result"] for x in r["results"]] == ["success", "success"]
        s1 = Sale.objects.get(pk=r["results"][0]["value"])
        s2 = Sale.objects.get(pk=r["results"][1]["value"])
        p.refresh_from_db()
        lots_after = list(Lot.objects.filter(product=p).order_by("expiration_date").values("number", "available_quantity"))
        assert all(item["available_quantity"] == 0 for item in lots_after)
        assert p.average_cost == Decimal("0.0000")
        alloc_s1 = list(
            SaleLotAllocation.objects.filter(line__sale=s1)
            .order_by("lot_snapshot_expiration_date")
            .values("lot_snapshot_number", "quantity")
        )
        alloc_s2 = list(
            SaleLotAllocation.objects.filter(line__sale=s2)
            .order_by("lot_snapshot_expiration_date")
            .values("lot_snapshot_number", "quantity")
        )
        assert alloc_s1 == [{"lot_snapshot_number": "FEFO-1", "quantity": 3}, {"lot_snapshot_number": "FEFO-2", "quantity": 1}]
        assert alloc_s2 == [{"lot_snapshot_number": "FEFO-2", "quantity": 4}]
        assert int(s2.correlative[2:]) == int(s1.correlative[2:]) + 1
        CashShift.objects.filter(pk__in=[sh1.pk, sh2.pk]).update(status="CLOSED")
        return {
            **r,
            "correlatives": [s1.correlative, s2.correlative],
            "allocations_sale1": alloc_s1,
            "allocations_sale2": alloc_s2,
            "lots_after": lots_after,
            "product_average_cost_after_zero": str(p.average_cost),
        }

    run_case("PG15-09-dos-ventas-fefo-multilote-y-salecounter", case_pg15_09_fefo_multilot_and_counter)

    # PG15-10: checkout_sale vs update_product (price change race)
    def case_pg15_10_checkout_vs_price_update() -> dict:
        CashShift.objects.filter(status="OPEN").update(status="CLOSED")
        sh = open_cash_shift(actor=seller1, opening_amount=Decimal("50.00"))
        p, _ = make_product("ProdPrecioRace", qty=10, price="10.00")
        dr = add_product_to_draft(actor=seller1, product_id=p.pk, quantity=1)
        # Subcase A: update_product wins lock on catalog_product -> checkout_sale detects price change under lock and raises ValidationError
        r_price_first = race_two(
            [
                lambda: update_product(
                    actor=admin1,
                    product=p,
                    name=p.name,
                    barcode=p.barcode,
                    category=cat_main,
                    sale_price=Decimal("12.50"),
                    minimum_stock=p.minimum_stock,
                ),
                lambda: checkout_sale(
                    actor=seller1, draft_id=dr.pk, cash_received=Decimal("20.00"), idempotency_key=uuid.uuid4()
                ),
            ],
            "catalog_product",
        )
        assert [x["result"] for x in r_price_first["results"]] == ["success", "ValidationError"]
        assert Sale.objects.filter(cash_shift=sh).count() == 0

        # Refresh draft line price to 12.50, then Subcase B: checkout_sale wins lock first -> sale commits at 12.50, update_product sets 15.00 after
        add_product_to_draft(actor=seller1, product_id=p.pk, quantity=1)  # refreshes unit_price to 12.50
        p.refresh_from_db()
        r_sale_first = race_two(
            [
                lambda: checkout_sale(
                    actor=seller1, draft_id=dr.pk, cash_received=Decimal("30.00"), idempotency_key=uuid.uuid4()
                ),
                lambda: update_product(
                    actor=admin1,
                    product=p,
                    name=p.name,
                    barcode=p.barcode,
                    category=cat_main,
                    sale_price=Decimal("15.00"),
                    minimum_stock=p.minimum_stock,
                ),
            ],
            "catalog_product",
        )
        assert [x["result"] for x in r_sale_first["results"]] == ["success", "success"]
        sale_committed = Sale.objects.get(pk=r_sale_first["results"][0]["value"])
        p.refresh_from_db()
        assert sale_committed.lines.get().unit_price == Decimal("12.50")
        assert p.sale_price == Decimal("15.00")
        close_cash_shift(actor=seller1, counted_amount=Decimal("75.00"))
        return {"price_update_first": r_price_first, "checkout_first": r_sale_first}

    run_case("PG15-10-checkout-venta-vs-cambio-precio", case_pg15_10_checkout_vs_price_update)

    # PG15-11: Concurrent confirm_initial_load on same product
    def case_pg15_11_initial_load_race() -> dict:
        p = Product.objects.create(
            category=cat_main,
            name="ProdCargaInicialRace",
            barcode="PG15-IIL-001",
            sale_price=Decimal("8.00"),
        )
        lots = [LotInput("INIT-RACE-1", 5, Decimal("3.0000"), future)]
        r = race_two(
            [
                lambda: confirm_initial_load(actor=warehouse1, product=p, lots=lots),
                lambda: confirm_initial_load(actor=warehouse2, product=p, lots=lots),
            ],
            "catalog_product",
        )
        assert [x["result"] for x in r["results"]] == ["success", "ValidationError"]
        assert InitialInventoryLoad.objects.filter(product=p).count() == 1
        assert Lot.objects.filter(product=p).count() == 1
        return {**r, "initial_loads": 1, "lots": 1}

    run_case("PG15-11-carga-inicial-simultanea", case_pg15_11_initial_load_race)

    # PG15-12: CT-ROLLBACK-01-POST-ESCRITURA/C-01 — Real OS process kill AFTER uncommitted SQL writes in PostgreSQL + idempotent retry
    def case_pg15_12_process_kill_postwrite() -> dict:
        CashShift.objects.filter(status="OPEN").update(status="CLOSED")
        sh = open_cash_shift(actor=seller1, opening_amount=Decimal("40.00"))
        p, lot = make_product("ProdKillPostWrite", qty=10, price="10.00")
        dr = add_product_to_draft(actor=seller1, product_id=p.pk, quantity=3)
        idem_key = uuid.uuid4()
        before = snapshot_tables()

        ready_file = CLUSTER / "child_postwrite_ready.json"
        if ready_file.exists():
            ready_file.unlink()

        child_code = f"""
import json, os, secrets, sys, time, uuid
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, {str(ROOT / 'r1-pmv')!r})
os.environ.update(
    APP_ENV='test',
    DJANGO_DEBUG='false',
    DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
    DJANGO_SETTINGS_MODULE='config.settings',
    DJANGO_ALLOWED_HOSTS='testserver,127.0.0.1',
)
from config import env
env.load_dotenv = lambda path=None: None
from django.conf import settings
settings.DATABASES = {{
    'default': {{
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': {DBNAME!r},
        'USER': 'audit15',
        'PASSWORD': {PW!r},
        'HOST': '127.0.0.1',
        'PORT': {PORT},
        'CONN_MAX_AGE': 0,
    }}
}}
import django
django.setup()
from django.db import connection
from identity.models import Account
from sales.services import checkout_sale

seller = Account.objects.get(pk={str(seller1.pk)!r})
with connection.cursor() as cur:
    cur.execute('SELECT pg_backend_pid()')
    backend_pid = cur.fetchone()[0]

def pause_after_lot_write(execute, query, params, many, context):
    res = execute(query, params, many, context)
    if query.lstrip().upper().startswith('UPDATE "INVENTORY_LOT"'):
        Path({str(ready_file)!r}).write_text(json.dumps({{'backend_pid': backend_pid, 'query': query}}), encoding='utf-8')
        time.sleep(60)
    return res

with connection.execute_wrapper(pause_after_lot_write):
    checkout_sale(
        actor=seller,
        draft_id=uuid.UUID({str(dr.pk)!r}),
        cash_received=Decimal('30.00'),
        idempotency_key=uuid.UUID({str(idem_key)!r}),
    )
"""
        proc = subprocess.Popen(
            [str(PYTHON), "-B", "-c", child_code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        deadline = time.monotonic() + 20
        child_info = None
        while time.monotonic() < deadline:
            if ready_file.exists():
                child_info = json.loads(ready_file.read_text(encoding="utf-8"))
                break
            if proc.poll() is not None:
                raise RuntimeError(f"Child exited early: {proc.stderr.read().decode('utf-8', 'replace')}")
            time.sleep(0.05)
        assert child_info is not None, "Child did not reach post-write barrier"
        child_backend_pid = child_info["backend_pid"]

        # Verify in pg_stat_activity that child_backend_pid is 'idle in transaction' holding uncommitted writes
        with connection.cursor() as cur:
            cur.execute(
                "SELECT state, query FROM pg_stat_activity WHERE pid = %s",
                [child_backend_pid],
            )
            row = cur.fetchone()
        assert row is not None and row[0] == "idle in transaction", f"Unexpected backend state: {row}"

        # Abruptly kill child OS process!
        proc.terminate()
        proc.wait(timeout=10)

        # Wait until PostgreSQL cleans up the terminated backend PID
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            with connection.cursor() as cur:
                cur.execute("SELECT count(*) FROM pg_stat_activity WHERE pid = %s", [child_backend_pid])
                if cur.fetchone()[0] == 0:
                    break
            time.sleep(0.05)

        after_kill = snapshot_tables()
        assert after_kill == before, "Uncommitted post-write state was not 100% rolled back after process kill"

        # Now execute idempotent retry with the exact same idempotency_key!
        sale_retry = checkout_sale(
            actor=seller1,
            draft_id=dr.pk,
            cash_received=Decimal("30.00"),
            idempotency_key=idem_key,
        )
        lot.refresh_from_db()
        assert Sale.objects.filter(idempotency_key=idem_key).count() == 1
        assert lot.available_quantity == 7
        close_cash_shift(actor=seller1, counted_amount=Decimal("70.00"))
        return {
            "child_os_pid": proc.pid,
            "child_pg_backend_pid": child_backend_pid,
            "observed_pg_state_before_kill": row[0],
            "all_business_tables_identical_after_kill": True,
            "tables_verified": len(before),
            "retry_with_same_idempotency_key_succeeded": True,
            "retry_sale_correlative": sale_retry.correlative,
            "lot_stock_after_retry": lot.available_quantity,
        }

    run_case("PG15-12-muerte-real-proceso-postwrite-y-reintento", case_pg15_12_process_kill_postwrite)

    # PG15-13: CT-ROLLBACK-01-POST-ESCRITURA/C-02 — Abrupt PostgreSQL motor stop (-m immediate) during uncommitted post-write transaction + WAL recovery + retry
    def case_pg15_13_motor_crash_wal_recovery() -> dict:
        p, lot = make_product("ProdCrashWAL", qty=10, cost="4.0000")
        idem_key = uuid.uuid4()
        before = snapshot_tables()
        ready_event = threading.Event()
        worker_err = []

        def writer_in_flight():
            close_old_connections()
            def pause_after_product_update(execute, query, params, many, context):
                res = execute(query, params, many, context)
                if query.lstrip().upper().startswith('UPDATE "CATALOG_PRODUCT"'):
                    ready_event.set()
                    time.sleep(60)
                return res

            try:
                with connection.execute_wrapper(pause_after_product_update):
                    register_stock_entry(
                        actor=warehouse1,
                        product=p,
                        lots=[LotInput("WAL-LOT-1", 5, Decimal("7.0000"), future)],
                        idempotency_key=idem_key,
                    )
            except Exception as exc:
                worker_err.append(type(exc).__name__)
            finally:
                connections.close_all()

        t = threading.Thread(target=writer_in_flight, daemon=True)
        t.start()
        assert ready_event.wait(15), "Worker did not reach post-write point before crash"

        # Stop PostgreSQL abruptly with -m immediate (simulating power loss / engine crash without clean shutdown)
        connections.close_all()
        pg("pg_ctl", "-D", DBDIR, "-m", "immediate", "-w", "stop")
        # Restart PostgreSQL (triggers WAL crash recovery)
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
        t.join(timeout=10)
        close_old_connections()

        after_recovery = snapshot_tables()
        assert after_recovery == before, "WAL recovery did not roll back uncommitted receipt/lot/product writes"

        # Now retry the exact same stock entry with the same idempotency_key
        receipt = register_stock_entry(
            actor=warehouse1,
            product=p,
            lots=[LotInput("WAL-LOT-1", 5, Decimal("7.0000"), future)],
            idempotency_key=idem_key,
        )
        p.refresh_from_db()
        assert StockReceipt.objects.filter(idempotency_key=idem_key).count() == 1
        assert p.physical_stock == 15 and p.average_cost == Decimal("5.0000")
        return {
            "crash_mode": "pg_ctl stop -m immediate + pg_ctl start (WAL crash recovery)",
            "worker_exception_on_crash": worker_err,
            "all_business_tables_identical_after_wal_recovery": True,
            "tables_verified": len(before),
            "retry_receipt_correlative": receipt.correlative,
            "stock_after_retry": p.physical_stock,
            "average_cost_after_retry": str(p.average_cost),
        }

    run_case("PG15-13-caida-abrupta-motor-pg-wal-recovery-y-reintento", case_pg15_13_motor_crash_wal_recovery)

    # PG15-14: S1-OPS-DB-02 — Runtime DB Role Privileges (migrator_user vs app_user)
    def case_pg15_14_runtime_roles() -> dict:
        app_pw = secrets.token_urlsafe(24)
        mig_pw = secrets.token_urlsafe(24)
        with psycopg.connect(**pg_conf, dbname=DBNAME, autocommit=True) as super_conn:
            super_conn.execute(
                sql.SQL("CREATE ROLE migrator_user WITH LOGIN PASSWORD {}").format(sql.Literal(mig_pw))
            )
            super_conn.execute(
                sql.SQL("CREATE ROLE app_user WITH LOGIN PASSWORD {}").format(sql.Literal(app_pw))
            )
            super_conn.execute(
                sql.SQL("GRANT CONNECT, TEMPORARY ON DATABASE {} TO migrator_user, app_user").format(
                    sql.Identifier(DBNAME)
                )
            )
            super_conn.execute("GRANT USAGE, CREATE ON SCHEMA public TO migrator_user")
            super_conn.execute("GRANT USAGE ON SCHEMA public TO app_user")
            super_conn.execute(
                "ALTER DEFAULT PRIVILEGES FOR ROLE migrator_user IN SCHEMA public "
                "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user"
            )

        # 1) Test if app_user can SELECT when tables were created by superuser (audit15) instead of migrator_user
        app_conf = {"host": "127.0.0.1", "port": PORT, "user": "app_user", "password": app_pw, "dbname": DBNAME}
        select_without_explicit_grant_failed = False
        with psycopg.connect(**app_conf, autocommit=True) as app_conn:
            try:
                app_conn.execute('SELECT count(*) FROM "catalog_category"')
            except psycopg.errors.InsufficientPrivilege:
                select_without_explicit_grant_failed = True

        # 2) Grant DML on existing tables to app_user, then verify DML succeeds and DDL is blocked!
        with psycopg.connect(**pg_conf, dbname=DBNAME, autocommit=True) as super_conn:
            super_conn.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user")
            super_conn.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user")

        ddl_blocked = {}
        with psycopg.connect(**app_conf, autocommit=True) as app_conn:
            cat_count = app_conn.execute('SELECT count(*) FROM "catalog_category"').fetchone()[0]
            assert cat_count >= 1
            for ddl_label, ddl_sql in [
                ("create_table", "CREATE TABLE public.rogue_table (id int)"),
                ("drop_table", 'DROP TABLE "catalog_category"'),
                ("alter_table", 'ALTER TABLE "catalog_category" ADD COLUMN rogue_col int'),
            ]:
                try:
                    app_conn.execute(ddl_sql)
                except psycopg.errors.InsufficientPrivilege:
                    ddl_blocked[ddl_label] = True
                else:
                    raise AssertionError(f"app_user was allowed to execute {ddl_label}")

        return {
            "init_sh_default_privileges_require_migrator_owner_finding": select_without_explicit_grant_failed,
            "app_user_dml_select_works_after_grant": True,
            "app_user_ddl_blocked": ddl_blocked,
        }

    run_case("PG15-14-privilegios-roles-bd-app-user-vs-ddl", case_pg15_14_runtime_roles)

    # PG15-15: S1-OPS-DB-01 — Backup (pg_dump custom) + Manifest SHA-256 + Restore (pg_restore) + Smoke Check
    def case_pg15_15_backup_and_restore() -> dict:
        close_old_connections()
        connections.close_all()
        source_digests = snapshot_tables()
        with connection.cursor() as cur:
            source_counts = {}
            for t in sorted(source_digests.keys()):
                cur.execute(f'SELECT count(*) FROM "{t}"')
                source_counts[t] = cur.fetchone()[0]
        connections.close_all()

        backup_dir = HERE / "backup_restore_artifacts"
        backup_dir.mkdir(exist_ok=True)
        dump_file = backup_dir / "minimarket_pg15.dump"
        manifest_file = backup_dir / "manifest.json"
        if dump_file.exists():
            dump_file.unlink()

        pg(
            "pg_dump",
            "-h",
            "127.0.0.1",
            "-p",
            PORT,
            "-U",
            "audit15",
            "--format=custom",
            "--no-owner",
            "--no-privileges",
            "--file",
            dump_file,
            DBNAME,
            env_extra={"PGPASSWORD": PW},
        )
        dump_bytes = dump_file.read_bytes()
        dump_sha256 = digest(dump_bytes)
        manifest = {
            "backup_file": dump_file.name,
            "sha256": dump_sha256,
            "size_bytes": len(dump_bytes),
            "created_utc": datetime.now(dt_timezone.utc).isoformat(),
            "postgres_version": report.get("postgres_version"),
            "table_counts": source_counts,
        }
        manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        # Verify manifest hash before restore
        assert digest(dump_file.read_bytes()) == json.loads(manifest_file.read_text(encoding="utf-8"))["sha256"]

        # Create clean target database and run pg_restore
        with psycopg.connect(**pg_conf, dbname="postgres", autocommit=True) as conn:
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DBNAME_RESTORED)))

        pg(
            "pg_restore",
            "-h",
            "127.0.0.1",
            "-p",
            PORT,
            "-U",
            "audit15",
            "--no-owner",
            "--no-privileges",
            "--exit-on-error",
            "-d",
            DBNAME_RESTORED,
            dump_file,
            env_extra={"PGPASSWORD": PW},
        )

        # Switch Django default connection to DBNAME_RESTORED and verify 100% table digests, counts, and HTTP smoke queries
        connections.close_all()
        settings.DATABASES["default"]["NAME"] = DBNAME_RESTORED
        close_old_connections()
        with connection.cursor() as cur:
            cur.execute("SELECT current_database()")
            assert cur.fetchone()[0] == DBNAME_RESTORED
            restored_counts = {}
            for t in sorted(source_digests.keys()):
                cur.execute(f'SELECT count(*) FROM "{t}"')
                restored_counts[t] = cur.fetchone()[0]
        restored_digests = snapshot_tables()
        assert restored_counts == source_counts, "Row counts differ after pg_restore"
        assert restored_digests == source_digests, "Table SHA-256 digests differ after pg_restore"

        # Functional HTTP smoke check on restored DB
        cl = Client()
        cl.force_login(admin1)
        for smoke_url in (
            reverse("dashboard"),
            reverse("employee-list"),
            reverse("product-list"),
            reverse("stock-overview"),
            reverse("cash-shift-history"),
            reverse("sales-history"),
        ):
            r_smoke = cl.get(smoke_url)
            assert r_smoke.status_code == 200, f"Smoke GET {smoke_url} failed on restored DB: {r_smoke.status_code}"

        # Remove binary dump file after verification so we don't leave binary blobs in repo, keep manifest.json
        dump_file.unlink()
        return {
            "dump_sha256": dump_sha256,
            "dump_size_bytes": len(dump_bytes),
            "manifest_file": "backup_restore_artifacts/manifest.json",
            "tables_restored_and_verified": len(source_digests),
            "counts_identical": True,
            "digests_identical": True,
            "http_smoke_checks_passed": 6,
        }

    run_case("PG15-15-backup-pg-dump-manifiesto-y-pg-restore", case_pg15_15_backup_and_restore)

except Exception as exc:
    report["fatal"] = {
        "type": type(exc).__name__,
        "detail": str(exc).replace(PW, "[REDACTED]"),
        "traceback": traceback.format_exc().replace(PW, "[REDACTED]"),
    }
finally:
    if started:
        try:
            if "connections" in globals():
                connections.close_all()
            pg("pg_ctl", "-D", DBDIR, "-m", "fast", "-w", "stop")
            with socket.socket() as s:
                s.settimeout(1)
                report["port_closed"] = s.connect_ex(("127.0.0.1", PORT)) != 0
            report["cluster_stopped"] = True
        except Exception as exc:
            report["stop_error"] = str(exc).replace(PW, "[REDACTED]")
    if PWFILE.exists():
        PWFILE.unlink()
    own()
    shutil.rmtree(CLUSTER, ignore_errors=True)
    report["cluster_deleted"] = not CLUSTER.exists()
    report["after_build"] = {k: v for k, v in compute_build().items() if k != "files"}
    report["source_stable"] = report["before_build"] == report["after_build"]
    report["passed"] = sum(1 for c in report["cases"] if c["ok"])
    report["total"] = len(report["cases"])
    report["ok"] = (
        not report.get("fatal")
        and report["passed"] == report["total"]
        and report["source_stable"]
        and report.get("cluster_stopped", False)
        and report.get("cluster_deleted", False)
    )
    report["finished_utc"] = datetime.now(dt_timezone.utc).isoformat()
    save_report("resultados-pg15.json")
    partial_file = HERE / "resultados-pg15-partial.json"
    if partial_file.exists():
        partial_file.unlink()
    print(
        json.dumps(
            {
                k: report[k]
                for k in ("ok", "passed", "total", "source_stable", "cluster_stopped", "cluster_deleted")
            },
            ensure_ascii=False,
        )
    )
sys.exit(0 if report["ok"] else 1)
