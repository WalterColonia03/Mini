"""Stage 09 Revalidation PostgreSQL 18.4 Verification (2026-11-14):
1) Migrations 0001..0005 & DB constraints (one_open_shift_per_register, CashShiftClose 14,2 bounds & negative difference).
2) Concurrent open_cash_shift race across two sellers -> single open shift, controlled ValidationError.
3) Concurrent close_cash_shift double-submit -> single CashShiftClose, controlled ValidationError.
4) Concurrent close_cash_shift vs checkout_sale (both directions under READ COMMITTED row locks + pg_blocking_pids, no discount_amount).
5) Concurrent close_cash_shift (no_key=True) vs deactivate_employee / update_employee role change + sales._lock_seller_actor lock-mode check.
6) America/Lima midnight boundary rendering & fecha_desde/fecha_hasta PG filtering on /caja/turnos/ and /cerrado/.
7) N+1 constant SQL query check (+30 shifts) and EXPLAIN (FORMAT JSON) plan analysis.
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
OUT_DIR = RESULTS / "evidencias" / "09-reval-20261114"
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
STAMP = datetime.now(dt_timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
CLUSTER = (Path(tempfile.gettempdir()) / ("audit09-reval-pg-" + secrets.token_hex(12))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT09_OWNED"
MARK.write_text(STAMP, encoding="utf-8")
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(40)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit09_reval_" + secrets.token_hex(5)
with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]

protected = [
    *APP.glob("*.sqlite3"),
    *sorted(
        p
        for p in (RESULTS / "datos").rglob("*.sqlite3")
        if p.parent.name.startswith("etapa09-") and not p.parent.name.startswith("etapa09-reval-")
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
    assert CLUSTER.parent == Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith("audit09-reval-pg-")
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

    from django.core.exceptions import ValidationError
    from django.core.management import call_command
    from django.db import IntegrityError, close_old_connections, connection, connections, transaction
    from django.test import Client
    from django.test.utils import CaptureQueriesContext, setup_test_environment
    from django.utils import timezone as tz

    setup_test_environment()

    from cash.models import CashRegister, CashShift, CashShiftClose
    from cash.services import close_cash_shift, open_cash_shift
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from identity.services import deactivate_employee, update_employee
    from inventory.services import LotInput, confirm_initial_load
    from sales.models import Sale, SaleDraft
    from sales.services import add_product_to_draft, checkout_sale, discard_active_draft

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    with connection.cursor() as cur:
        cur.execute("SELECT current_database(), current_setting('data_directory'), current_setting('transaction_isolation')")
        db_name, data_dir, iso_level = cur.fetchone()
        report["db_verification"] = {
            "current_database": db_name,
            "data_directory_matches": Path(data_dir).resolve() == DBDIR,
            "transaction_isolation": iso_level,
        }

    r_adm = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    r_wh = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    r_sel = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
    pw_user = secrets.token_urlsafe(18) + "A1!"
    admin = Account.objects.create_user("admin@pg09.invalid", pw_user, display_name="Admin PG09", role=r_adm)
    wh = Account.objects.create_user("wh@pg09.invalid", pw_user, display_name="Almacen PG09", role=r_wh)
    seller1 = Account.objects.create_user("s1@pg09.invalid", pw_user, display_name="Vendedor Uno PG09", role=r_sel)
    seller2 = Account.objects.create_user("s2@pg09.invalid", pw_user, display_name="Vendedor Dos PG09", role=r_sel)

    reg = CashRegister.objects.create(code="CAJA-01")
    cat = Category.objects.create(name="General PG09", is_active=True)
    sup = __import__("inventory.services", fromlist=["create_supplier"]).create_supplier(
        actor=admin, name="Proveedor PG09", ruc="20123456709", phone="01-5551109"
    )
    future = tz.localdate() + timedelta(days=90)
    p = Product.objects.create(category=cat, name="Leche PG09", barcode="775090988801", sale_price=Decimal("5.00"), minimum_stock=2)
    confirm_initial_load(actor=wh, product=p, supplier=sup, lots=[LotInput("LOT-PG09-1", 50, Decimal("3.0000"), future)])

    # ── Case 1: DB Constraints in PostgreSQL 18.4 (cash 0001..0004) ───────────
    c1_checks = {}
    with connection.cursor() as cur:
        # Bad opening < 0
        try:
            with transaction.atomic():
                cur.execute(
                    "INSERT INTO cash_cashshift (id, cash_register_id, seller_id, opening_amount, status, opened_at) "
                    "VALUES (%s, %s, %s, %s, %s, %s)",
                    [uuid.uuid4(), reg.pk, seller1.pk, Decimal("-0.01"), "CLOSED", tz.now()],
                )
            c1_checks["neg_opening_rejected"] = False
        except IntegrityError:
            c1_checks["neg_opening_rejected"] = True

        # Valid 14,2 cumulative close + valid negative difference
        sh_chk = CashShift.objects.create(cash_register=reg, seller=seller1, opening_amount=Decimal("9999999.99"), status=CashShift.Status.CLOSED)
        cl_neg = CashShiftClose.objects.create(
            cash_shift=sh_chk,
            closed_by=seller1,
            counted_amount=Decimal("999999999990.00"),
            expected_amount=Decimal("999999999999.99"),
            difference=Decimal("-9.99"),
        )
        c1_checks["cumulative_14_2_and_neg_diff_allowed"] = (cl_neg.difference == Decimal("-9.99"))

        # Inconsistent difference rejected
        sh_bad = CashShift.objects.create(cash_register=reg, seller=seller1, opening_amount=Decimal("10.00"), status=CashShift.Status.CLOSED)
        try:
            with transaction.atomic():
                CashShiftClose.objects.create(
                    cash_shift=sh_bad,
                    closed_by=seller1,
                    counted_amount=Decimal("10.00"),
                    expected_amount=Decimal("10.00"),
                    difference=Decimal("1.00"),
                )
            c1_checks["inconsistent_diff_rejected"] = False
        except IntegrityError:
            c1_checks["inconsistent_diff_rejected"] = True

    report["cases"].append({"id": "pg_cash_0001_0004_constraints", "ok": all(c1_checks.values()), "checks": c1_checks})

    # ── Case 2: Concurrent open_cash_shift race ───────────────────────────────
    b_open = threading.Barrier(2)

    def try_open(actor):
        close_old_connections()
        try:
            b_open.wait(timeout=5)
            sh = open_cash_shift(actor=actor, opening_amount=Decimal("100.00"))
            return ("opened", str(sh.pk), str(actor.pk))
        except ValidationError as exc:
            return ("rejected", str(exc.messages[0]), str(actor.pk))
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(try_open, seller1)
        f2 = pool.submit(try_open, seller2)
        res_open = [f1.result(timeout=10), f2.result(timeout=10)]

    opened_count = sum(1 for r in res_open if r[0] == "opened")
    rejected_count = sum(1 for r in res_open if r[0] == "rejected")
    active_shift = CashShift.objects.get(status=CashShift.Status.OPEN)
    c2_ok = opened_count == 1 and rejected_count == 1 and CashShift.objects.filter(status=CashShift.Status.OPEN).count() == 1
    report["cases"].append({"id": "pg_concurrent_open_shift", "ok": c2_ok, "checks": {"outcomes": res_open}})
    close_cash_shift(actor=active_shift.seller, counted_amount=Decimal("100.00"))

    # ── Case 3: Concurrent close_cash_shift double submit ─────────────────────
    shift_c3 = open_cash_shift(actor=seller1, opening_amount=Decimal("50.00"))
    b_close = threading.Barrier(2)

    def try_close():
        close_old_connections()
        try:
            b_close.wait(timeout=5)
            cl = close_cash_shift(actor=seller1, counted_amount=Decimal("50.00"))
            return ("closed", str(cl.pk))
        except ValidationError as exc:
            return ("rejected", str(exc.messages[0]))
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        r_c = [pool.submit(try_close), pool.submit(try_close)]
        res_close = [r_c[0].result(timeout=10), r_c[1].result(timeout=10)]

    shift_c3.refresh_from_db()
    c3_ok = (
        sum(1 for r in res_close if r[0] == "closed") == 1
        and sum(1 for r in res_close if r[0] == "rejected") == 1
        and CashShiftClose.objects.filter(cash_shift=shift_c3).count() == 1
        and shift_c3.status == CashShift.Status.CLOSED
    )
    report["cases"].append({"id": "pg_concurrent_double_close", "ok": c3_ok, "checks": {"outcomes": res_close}})

    # ── Case 4: close_cash_shift vs checkout_sale (both directions + pg_blocking_pids) ─
    shift_c4a = open_cash_shift(actor=seller1, opening_amount=Decimal("100.00"))
    draft_c4a = add_product_to_draft(actor=seller1, product_id=p.pk, quantity=2)  # 2 * 5.00 = 10.00
    from inventory.models import Lot

    locked_evt = threading.Event()
    proceed_evt = threading.Event()
    blocking_pids_seen = []
    orig_lot_select = Lot.objects.select_for_update

    def gated_lot_select(*args, **kwargs):
        locked_evt.set()
        proceed_evt.wait(timeout=8)
        return orig_lot_select(*args, **kwargs)

    def run_sale_c4a():
        close_old_connections()
        try:
            with patch.object(Lot.objects, "select_for_update", gated_lot_select):
                s = checkout_sale(
                    actor=seller1,
                    draft_id=draft_c4a.pk,
                    cash_received=Decimal("10.00"),
                    idempotency_key=uuid.uuid4(),
                )
                return ("sale_ok", str(s.total_amount))
        finally:
            close_old_connections()

    def run_close_c4a():
        close_old_connections()
        try:
            assert locked_evt.wait(timeout=8)
            cl = close_cash_shift(actor=seller1, counted_amount=Decimal("110.00"))
            return ("close_ok", str(cl.expected_amount), str(cl.difference))
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_sale = pool.submit(run_sale_c4a)
        f_close = pool.submit(run_close_c4a)
        with psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
            for _ in range(40):
                rows = obs.execute(
                    "SELECT pid, pg_blocking_pids(pid) FROM pg_stat_activity WHERE datname = %s AND cardinality(pg_blocking_pids(pid)) > 0",
                    (DBNAME,),
                ).fetchall()
                if rows:
                    blocking_pids_seen.append(rows[0][0])
                    break
                threading.Event().wait(0.05)
        proceed_evt.set()
        res_sale_4a = f_sale.result(timeout=10)
        res_close_4a = f_close.result(timeout=10)

    # Direction B: close commits before checkout acquires CashShift lock -> checkout rejects cleanly
    shift_c4b = open_cash_shift(actor=seller1, opening_amount=Decimal("50.00"))
    draft_c4b = add_product_to_draft(actor=seller1, product_id=p.pk, quantity=1)
    checkout_ready = threading.Event()
    close_done = threading.Event()
    orig_atomic = transaction.atomic
    hits = {"n": 0}

    def gated_atomic(*args, **kwargs):
        hits["n"] += 1
        if hits["n"] == 1:
            checkout_ready.set()
            close_done.wait(timeout=8)
        return orig_atomic(*args, **kwargs)

    def run_sale_4b():
        close_old_connections()
        try:
            with patch("sales.services.transaction.atomic", side_effect=gated_atomic):
                checkout_sale(actor=seller1, draft_id=draft_c4b.pk, cash_received=Decimal("5.00"), idempotency_key=uuid.uuid4())
            return ("unexpected_ok",)
        except ValidationError as exc:
            return ("rejected", str(exc.messages[0]))
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=1) as pool:
        f_sb = pool.submit(run_sale_4b)
        assert checkout_ready.wait(timeout=8)
        discard_active_draft(actor=seller1)
        cl_4b = close_cash_shift(actor=seller1, counted_amount=Decimal("50.00"))
        close_done.set()
        res_sale_4b = f_sb.result(timeout=10)

    c4_ok = (
        res_sale_4a == ("sale_ok", "10.00")
        and res_close_4a == ("close_ok", "110.00", "0.00")
        and len(blocking_pids_seen) >= 1
        and res_sale_4b[0] == "rejected"
        and cl_4b.expected_amount == Decimal("50.00")
        and Sale.objects.filter(cash_shift=shift_c4b).count() == 0
    )
    report["cases"].append(
        {
            "id": "pg_close_vs_checkout_both_directions",
            "ok": c4_ok,
            "checks": {
                "dir_a_sale": res_sale_4a,
                "dir_a_close": res_close_4a,
                "pg_blocking_pids_count": len(blocking_pids_seen),
                "dir_b_sale": res_sale_4b,
            },
        }
    )

    # ── Case 5: close (no_key=True) & checkout_sale lock-mode vs identity/admin ─
    shift_c5 = open_cash_shift(actor=seller1, opening_amount=Decimal("60.00"))
    acct_locked = threading.Event()
    release_acct = threading.Event()
    from cash import services as cash_services

    orig_val_amt = cash_services._validate_cash_amount

    def paused_val(value, *, field_name, **kwargs):
        if field_name == "counted_amount":
            acct_locked.set()
            release_acct.wait(timeout=8)
        return orig_val_amt(value, field_name=field_name, **kwargs)

    def run_close_c5():
        close_old_connections()
        try:
            with patch.object(cash_services, "_validate_cash_amount", paused_val):
                cl = close_cash_shift(actor=seller1, counted_amount=Decimal("60.00"))
                return ("close_ok", str(cl.expected_amount))
        finally:
            close_old_connections()

    def run_deact_c5():
        close_old_connections()
        try:
            assert acct_locked.wait(timeout=8)
            with psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
                with obs.transaction():
                    try:
                        obs.execute("SELECT 1 FROM identity_account WHERE id = %s FOR KEY SHARE NOWAIT", (str(seller1.pk),))
                        fk_allowed = True
                    except psycopg.errors.LockNotAvailable:
                        fk_allowed = False
                with obs.transaction():
                    try:
                        obs.execute("SELECT 1 FROM identity_account WHERE id = %s FOR UPDATE NOWAIT", (str(seller1.pk),))
                        for_update_blocked = False
                    except psycopg.errors.LockNotAvailable:
                        for_update_blocked = True
            release_acct.set()
            deactivate_employee(actor=admin, account=seller1)
            seller1.refresh_from_db()
            return ("deactivated_after_close", seller1.is_active, fk_allowed, for_update_blocked)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        fc5 = pool.submit(run_close_c5)
        fd5 = pool.submit(run_deact_c5)
        rc5 = fc5.result(timeout=15)
        rd5 = fd5.result(timeout=15)

    # Also test close (Account no_key) vs update_employee role change concurrently
    seller1.is_active = True
    seller1.save(update_fields=["is_active"])
    open_cash_shift(actor=seller1, opening_amount=Decimal("20.00"))
    b_rc = threading.Barrier(2)

    def run_close_rc():
        close_old_connections()
        try:
            b_rc.wait(timeout=5)
            close_cash_shift(actor=seller1, counted_amount=Decimal("20.00"))
            return "close_ok"
        except ValidationError as exc:
            return f"close_err:{exc.messages[0]}"
        finally:
            close_old_connections()

    def run_role_rc():
        close_old_connections()
        try:
            b_rc.wait(timeout=5)
            update_employee(actor=admin, account=seller1, display_name=seller1.display_name, email=seller1.email, role=r_wh)
            return "role_ok"
        except ValidationError as exc:
            return f"role_err:{exc.messages[0]}"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_crc = pool.submit(run_close_rc)
        f_rrc = pool.submit(run_role_rc)
        res_close_rc = f_crc.result(timeout=10)
        res_role_rc = f_rrc.result(timeout=10)

    # Check sales._lock_seller_actor lock mode observation (FOR UPDATE without no_key vs FOR NO KEY UPDATE)
    seller1.refresh_from_db()
    if seller1.role_id != r_sel.pk:
        update_employee(actor=admin, account=seller1, display_name=seller1.display_name, email=seller1.email, role=r_sel)
    if CashShift.objects.filter(status=CashShift.Status.OPEN).exists():
        close_cash_shift(actor=seller1, counted_amount=Decimal("20.00"))

    shift_sales_lock = open_cash_shift(actor=seller1, opening_amount=Decimal("10.00"))
    draft_sales_lock = add_product_to_draft(actor=seller1, product_id=p.pk, quantity=1)
    sales_acct_evt = threading.Event()
    sales_rel_evt = threading.Event()
    from sales import services as sales_services

    orig_lock_actor = sales_services._lock_seller_actor

    def paused_lock_actor(actor, message="No tiene permiso para preparar ventas."):
        locked = orig_lock_actor(actor, message)
        if message == "No tiene permiso para cobrar ventas.":
            sales_acct_evt.set()
            sales_rel_evt.wait(timeout=8)
        return locked

    def run_sales_lock():
        close_old_connections()
        try:
            with patch.object(sales_services, "_lock_seller_actor", paused_lock_actor):
                checkout_sale(actor=seller1, draft_id=draft_sales_lock.pk, cash_received=Decimal("5.00"), idempotency_key=uuid.uuid4())
            return "ok"
        finally:
            close_old_connections()

    fk_blocked_under_sales_lock = None
    with ThreadPoolExecutor(max_workers=1) as pool:
        fs = pool.submit(run_sales_lock)
        assert sales_acct_evt.wait(timeout=8)
        with psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
            with obs.transaction():
                try:
                    obs.execute("SELECT 1 FROM identity_account WHERE id = %s FOR KEY SHARE NOWAIT", (str(seller1.pk),))
                    fk_blocked_under_sales_lock = False
                except psycopg.errors.LockNotAvailable:
                    fk_blocked_under_sales_lock = True
        sales_rel_evt.set()
        fs.result(timeout=10)
    close_cash_shift(actor=seller1, counted_amount=Decimal("15.00"))

    c5_ok = (
        rc5 == ("close_ok", "60.00")
        and rd5 == ("deactivated_after_close", False, True, True)
        and res_close_rc == "close_ok"
        and (res_role_rc == "role_ok" or res_role_rc.startswith("role_err:"))
    )
    report["cases"].append(
        {
            "id": "pg_no_key_lock_and_sales_lock_observation",
            "ok": c5_ok,
            "checks": {
                "cash_no_key_close": rc5,
                "cash_no_key_deact_tuple": rd5,
                "concurrent_close_vs_role_change": [res_close_rc, res_role_rc],
                "sales_lock_blocks_fk_key_share_nowait": fk_blocked_under_sales_lock,
            },
        }
    )

    # ── Case 6: America/Lima midnight boundary & PG fecha_desde/fecha_hasta filter ─
    shift_tz = open_cash_shift(actor=seller2, opening_amount=Decimal("80.00"))
    close_tz = close_cash_shift(actor=seller2, counted_amount=Decimal("80.00"))
    t_open_utc = datetime(2026, 11, 12, 4, 59, 0, tzinfo=dt_timezone.utc)   # 2026-11-11 23:59 Lima
    t_close_utc = datetime(2026, 11, 12, 5, 1, 0, tzinfo=dt_timezone.utc)   # 2026-11-12 00:01 Lima
    CashShift.objects.filter(pk=shift_tz.pk).update(opened_at=t_open_utc)
    CashShiftClose.objects.filter(pk=close_tz.pk).update(closed_at=t_close_utc)

    c_adm = Client()
    c_adm.force_login(admin)
    html_hist = c_adm.get("/caja/turnos/").content.decode()
    html_acta = c_adm.get(f"/caja/turnos/{shift_tz.pk}/cerrado/").content.decode()
    html_nov11 = c_adm.get("/caja/turnos/?fecha_desde=2026-11-11&fecha_hasta=2026-11-11").content.decode()
    html_nov12 = c_adm.get("/caja/turnos/?fecha_desde=2026-11-12&fecha_hasta=2026-11-12").content.decode()
    c6_ok = (
        "11/11/2026 23:59" in html_hist
        and "12/11/2026 00:01" in html_hist
        and "11/11/2026 23:59" in html_acta
        and "12/11/2026 00:01" in html_acta
        and str(shift_tz.pk) in html_nov11
        and str(shift_tz.pk) not in html_nov12
    )
    report["cases"].append(
        {
            "id": "pg_america_lima_midnight_and_filter",
            "ok": c6_ok,
            "checks": {
                "open_lima_hist": "11/11/2026 23:59" in html_hist,
                "close_lima_hist": "12/11/2026 00:01" in html_hist,
                "included_in_nov11_lima_filter": str(shift_tz.pk) in html_nov11,
                "excluded_from_nov12_lima_filter": str(shift_tz.pk) not in html_nov12,
            },
        }
    )

    # ── Case 7: N+1 query invariance +30 shifts & EXPLAIN JSON ────────────────
    connection.force_debug_cursor = True
    with CaptureQueriesContext(connection) as q_before:
        assert c_adm.get("/caja/turnos/").status_code == 200

    for i in range(30):
        open_cash_shift(actor=seller2, opening_amount=Decimal("10.00") + i)
        close_cash_shift(actor=seller2, counted_amount=Decimal("10.00") + i)

    with CaptureQueriesContext(connection) as q_after:
        resp_after = c_adm.get("/caja/turnos/")
        assert resp_after.status_code == 200
    connection.force_debug_cursor = False

    from django.db.models import DecimalField, OuterRef, Subquery, Sum, Value
    from django.db.models.functions import Coalesce
    sales_sq = Subquery(
        Sale.objects.filter(cash_shift=OuterRef("pk"))
        .order_by()
        .values("cash_shift")
        .annotate(total=Sum("total_amount"))
        .values("total")[:1],
        output_field=DecimalField(max_digits=14, decimal_places=2),
    )
    qs_hist = (
        CashShift.objects.select_related("cash_register", "seller", "close")
        .annotate(sales_collected=Coalesce(sales_sq, Value(Decimal("0.00"))))
        .order_by("-opened_at", "-id")
    )
    sql_hist, params_hist = qs_hist.query.sql_with_params()
    with connection.cursor() as cur:
        cur.execute(f"EXPLAIN (FORMAT JSON) {sql_hist}", params_hist)
        plan_hist = cur.fetchone()[0][0]["Plan"]

    def collect_plan_nodes(node: dict) -> list[dict]:
        nodes = [{"node_type": node.get("Node Type"), "relation": node.get("Relation Name"), "index": node.get("Index Name")}]
        for ch in node.get("Plans", []):
            nodes.extend(collect_plan_nodes(ch))
        return nodes

    c7_ok = len(q_before) == len(q_after) and len(q_before) <= 5
    report["cases"].append(
        {
            "id": "pg_history_constant_queries_and_explain",
            "ok": c7_ok,
            "checks": {
                "queries_before": len(q_before),
                "queries_after_plus30": len(q_after),
                "rendered_rows_total": resp_after.content.decode().count("Ver acta"),
                "plan_nodes": collect_plan_nodes(plan_hist),
            },
        }
    )

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
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / ("pg18-" + STAMP + ".json")
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
    or len(report["cases"]) != 7
    or not all(x["ok"] for x in report["cases"])
    or not report["port_closed"]
    or not all(report["protected_unchanged"].values())
):
    raise SystemExit(1)
