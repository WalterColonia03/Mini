"""Stage 11B isolated PostgreSQL 18.4 concurrency, pg_blocking_pids, post-write rollback, DB constraints & Lima tz suite."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

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


def main() -> int:
    prod_db = PROJECT / "r1_pmv.sqlite3"
    prod_db_before = sha_bytes(prod_db.read_bytes())
    build_before = build_snapshot()

    os.environ.update(
        APP_ENV="test",
        DATABASE_URL="sqlite",
        DJANGO_DEBUG="false",
        DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost,testserver",
        DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
        DJANGO_SETTINGS_MODULE="config.settings",
    )
    sys.path.insert(0, str(PROJECT))
    os.chdir(PROJECT)

    from config import env as config_env  # noqa: E402

    config_env.load_dotenv = lambda path=None: None

    from django.conf import settings  # noqa: E402

    settings.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

    import django  # noqa: E402

    django.setup()

    from django.core.exceptions import PermissionDenied, ValidationError  # noqa: E402
    from django.core.management import call_command  # noqa: E402
    from django.db import IntegrityError, close_old_connections, connection, connections, transaction  # noqa: E402
    from django.utils import timezone as tz  # noqa: E402

    cluster = (Path(tempfile.gettempdir()) / ("audit11b-pg-" + secrets.token_hex(8))).resolve()
    cluster.mkdir(exist_ok=False)
    (cluster / "AUDIT11B_OWNED").write_text("owned_by_audit11b_pg", encoding="utf-8")
    dbdir = cluster / "data"
    pw_pg = secrets.token_urlsafe(32)
    pwfile = cluster / "pw"
    pwfile.write_text(pw_pg, encoding="utf-8")

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        pg_port = s.getsockname()[1]

    report: dict = {
        "executed_utc": datetime.now(dt_timezone.utc).isoformat(),
        "pg_port": pg_port,
        "build_before": build_before,
        "checks": [],
        "scenarios": {},
    }
    pg_started = False

    try:
        subprocess.run(
            [
                str(PG_BIN / "initdb.exe"),
                "-D", str(dbdir),
                "-U", "audit11b",
                "--pwfile", str(pwfile),
                "--auth-host=scram-sha-256",
                "--auth-local=scram-sha-256",
                "--encoding=UTF8",
                "--locale=C",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        pwfile.unlink()
        subprocess.run(
            [
                str(PG_BIN / "pg_ctl.exe"),
                "-D", str(dbdir),
                "-l", str(cluster / "pg.log"),
                "-o", f"-h 127.0.0.1 -p {pg_port} -c log_statement=none -c log_min_error_statement=panic",
                "-w", "start",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        pg_started = True

        import psycopg  # noqa: E402
        from psycopg import sql  # noqa: E402

        dbname = "audit11b_" + secrets.token_hex(4)
        with psycopg.connect(
            host="127.0.0.1", port=pg_port, user="audit11b", password=pw_pg, dbname="postgres", autocommit=True
        ) as conn:
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
            pg_version = conn.execute("SELECT version()").fetchone()[0]

        connections.close_all()
        settings.DATABASES["default"] = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": dbname,
            "USER": "audit11b",
            "PASSWORD": pw_pg,
            "HOST": "127.0.0.1",
            "PORT": pg_port,
            "CONN_MAX_AGE": 0,
            "CONN_HEALTH_CHECKS": False,
            "ATOMIC_REQUESTS": False,
            "AUTOCOMMIT": True,
            "TIME_ZONE": "America/Lima",
            "OPTIONS": {"options": "-c statement_timeout=15000 -c lock_timeout=10000"},
        }
        del connections["default"]

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            call_command("migrate", interactive=False, verbosity=0)

        with connection.cursor() as cur:
            cur.execute("SHOW transaction_isolation")
            iso_level = cur.fetchone()[0]
        report["pg_version"] = pg_version
        report["transaction_isolation"] = iso_level
        report["checks"].append("01_pg_migrate_clean")

        from cash.models import CashRegister, CashShift, CashShiftClose  # noqa: E402
        from cash.services import close_cash_shift, open_cash_shift  # noqa: E402
        from catalog.models import Category, Product  # noqa: E402
        from identity.models import Account, Role  # noqa: E402
        from inventory.models import Lot, StockWriteOff  # noqa: E402
        from inventory.services import LotInput, confirm_initial_load, write_off_stock  # noqa: E402
        from sales.models import Sale, SaleCounter, SaleDraft, SaleDraftLine, SaleLine, SaleLotAllocation  # noqa: E402
        from sales.services import add_product_to_draft, checkout_sale, discard_active_draft, sellable_stock_for_product  # noqa: E402

        def inspect_blocking_pids(holder_backend_pid: int) -> list[dict]:
            with psycopg.connect(
                host="127.0.0.1", port=pg_port, user="audit11b", password=pw_pg, dbname=dbname, autocommit=True
            ) as obs:
                rows = obs.execute(
                    """
                    SELECT pid, wait_event_type, wait_event, pg_blocking_pids(pid) AS blockers, left(query, 120)
                    FROM pg_stat_activity
                    WHERE datname = %s AND state = 'active' AND %s = ANY(pg_blocking_pids(pid))
                    """,
                    (dbname, holder_backend_pid),
                ).fetchall()
                return [
                    {"pid": r[0], "wait_type": r[1], "wait_event": r[2], "blockers": r[3], "query": r[4]}
                    for r in rows
                ]

        r_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
        r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
        r_sel, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

        admin = Account.objects.create_user("pg11b-admin@test.invalid", "Pg11B!Pass123", display_name="PG Admin 11B", role=r_admin)
        wh = Account.objects.create_user("pg11b-wh@test.invalid", "Pg11B!Pass123", display_name="PG WH 11B", role=r_wh)
        seller = Account.objects.create_user("pg11b-sel@test.invalid", "Pg11B!Pass123", display_name="PG Seller 11B", role=r_sel)
        seller_off = Account.objects.create_user("pg11b-seloff@test.invalid", "Pg11B!Pass123", display_name="PG Seller Off 11B", role=r_sel)
        reg = CashRegister.objects.create(code="CAJA-01")
        cat = Category.objects.create(name="PG Cat 11B")
        today = tz.localdate()

        # ── 02. CT-CONC-03: checkout vs write_off_stock on last 2 units ──────────
        prod_conc = Product.objects.create(category=cat, name="PG Stock Conc 11B", barcode="PG11B-CONC", sale_price=Decimal("5.00"))
        confirm_initial_load(actor=wh, product=prod_conc, lots=[LotInput("PG-LOT-C1", 2, Decimal("2.0000"), today + timedelta(days=20))])
        lot_conc = Lot.objects.get(product=prod_conc)
        shift1 = open_cash_shift(actor=seller, opening_amount=Decimal("50.00"))
        draft_c = add_product_to_draft(actor=seller, product_id=prod_conc.pk, quantity=2)

        evt_hold = threading.Event()
        evt_go = threading.Event()
        holder_pid: list[int] = []
        orig_lot_save = Lot.save

        def hold_wo():
            close_old_connections()
            try:
                held = {"done": False}
                def slow_save(self_lot, *a, **kw):
                    if not held["done"] and self_lot.pk == lot_conc.pk:
                        held["done"] = True
                        with connection.cursor() as c:
                            c.execute("SELECT pg_backend_pid()")
                            holder_pid.append(c.fetchone()[0])
                        evt_hold.set()
                        evt_go.wait(8)
                    return orig_lot_save(self_lot, *a, **kw)
                with patch.object(Lot, "save", slow_save):
                    wo = write_off_stock(actor=wh, lot=lot_conc, quantity=1, reason=StockWriteOff.Reason.DAMAGE, notes="Race PG 11B")
                    return {"ok": True, "correlative": wo.correlativo}
            except Exception as exc:
                return {"ok": False, "type": type(exc).__name__, "error": str(exc)}
            finally:
                close_old_connections()

        def compete_co():
            close_old_connections()
            try:
                evt_hold.wait(8)
                s = checkout_sale(actor=seller, draft_id=draft_c.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4())
                return {"ok": True, "sale": s.correlative}
            except Exception as exc:
                return {"ok": False, "type": type(exc).__name__, "error": str(exc)}
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(hold_wo)
            f2 = pool.submit(compete_co)
            blocked_02 = []
            for _ in range(50):
                if holder_pid:
                    blocked_02 = inspect_blocking_pids(holder_pid[0])
                    if blocked_02:
                        break
                time.sleep(0.05)
            evt_go.set()
            r1 = f1.result(timeout=15)
            r2 = f2.result(timeout=15)

        lot_conc.refresh_from_db()
        assert r1["ok"] and not r2["ok"] and r2["type"] == "ValidationError"
        assert lot_conc.available_quantity == 1 and Sale.objects.count() == 0 and len(blocked_02) >= 1
        report["scenarios"]["02_CT_CONC_03_stock_contention"] = {"writeoff": r1, "checkout": r2, "lot_after": lot_conc.available_quantity, "pg_blocking_pids": blocked_02}
        report["checks"].append("02_CT_CONC_03_stock_contention")
        discard_active_draft(actor=seller)

        # ── 03. CT-CONC-04a: identical concurrent idempotency_key + allocations ─
        prod_i = Product.objects.create(category=cat, name="PG Idem Prod 11B", barcode="PG11B-IDEM", sale_price=Decimal("10.00"))
        confirm_initial_load(actor=wh, product=prod_i, lots=[LotInput("PG-LOT-I1", 10, Decimal("3.0000"), today + timedelta(days=20))])
        d_i1 = add_product_to_draft(actor=seller, product_id=prod_i.pk, quantity=2)
        k_i1 = uuid.uuid4()
        evt_hold.clear(); evt_go.clear()
        pid_03: list[int] = []
        orig_sale_create = Sale.objects.create

        def idem_worker(draft_id, key_obj, cash_val, delay_hold=False):
            close_old_connections()
            try:
                if delay_hold:
                    def slow_create(**kw):
                        with connection.cursor() as c:
                            c.execute("SELECT pg_backend_pid()")
                            pid_03.append(c.fetchone()[0])
                        evt_hold.set()
                        evt_go.wait(8)
                        return orig_sale_create(**kw)
                    with patch.object(Sale.objects, "create", side_effect=slow_create):
                        s = checkout_sale(actor=seller, draft_id=draft_id, cash_received=cash_val, idempotency_key=key_obj)
                else:
                    evt_hold.wait(8)
                    s = checkout_sale(actor=seller, draft_id=draft_id, cash_received=cash_val, idempotency_key=key_obj)
                return {"ok": True, "sale_id": str(s.pk), "correlative": s.correlative}
            except Exception as exc:
                return {"ok": False, "type": type(exc).__name__, "error": str(exc)}
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            f_a = pool.submit(idem_worker, d_i1.pk, k_i1, Decimal("25.00"), True)
            f_b = pool.submit(idem_worker, d_i1.pk, k_i1, Decimal("25.00"), False)
            blocked_03 = []
            for _ in range(50):
                if pid_03:
                    blocked_03 = inspect_blocking_pids(pid_03[0])
                    if blocked_03:
                        break
                time.sleep(0.05)
            evt_go.set()
            ra = f_a.result(timeout=15)
            rb = f_b.result(timeout=15)

        assert ra["ok"] and rb["ok"] and ra["sale_id"] == rb["sale_id"] and Sale.objects.count() == 1
        assert SaleLotAllocation.objects.filter(line__sale_id=ra["sale_id"]).count() == 1
        assert SaleLotAllocation.objects.get(line__sale_id=ra["sale_id"]).quantity == 2
        assert Lot.objects.get(product=prod_i).available_quantity == 8 and len(blocked_03) >= 1
        report["scenarios"]["03_CT_CONC_04a_idempotent_same"] = {"a": ra, "b": rb, "lot_after": 8, "pg_blocking_pids": blocked_03}
        report["checks"].append("03_CT_CONC_04a_idempotent_same")

        # ── 04. CT-CONC-04b: divergent concurrent idempotency_key ──────────────
        d_i2 = add_product_to_draft(actor=seller, product_id=prod_i.pk, quantity=1)
        k_i2 = uuid.uuid4()
        evt_hold.clear(); evt_go.clear(); pid_03.clear()

        with ThreadPoolExecutor(max_workers=2) as pool:
            fa2 = pool.submit(idem_worker, d_i2.pk, k_i2, Decimal("10.00"), True)
            fb2 = pool.submit(idem_worker, d_i2.pk, k_i2, Decimal("20.00"), False)
            blocked_04 = []
            for _ in range(50):
                if pid_03:
                    blocked_04 = inspect_blocking_pids(pid_03[0])
                    if blocked_04:
                        break
                time.sleep(0.05)
            evt_go.set()
            r4a = fa2.result(timeout=15)
            r4b = fb2.result(timeout=15)

        assert r4a["ok"] and not r4b["ok"] and r4b["type"] == "ValidationError"
        assert Sale.objects.count() == 2 and Lot.objects.get(product=prod_i).available_quantity == 7 and len(blocked_04) >= 1
        report["scenarios"]["04_CT_CONC_04b_idempotent_divergent"] = {"winner": r4a, "loser": r4b, "pg_blocking_pids": blocked_04}
        report["checks"].append("04_CT_CONC_04b_idempotent_divergent")

        # ── 05. CT-CONC-05: checkout vs close_cash_shift serialized on CashShift ─
        d_c5 = add_product_to_draft(actor=seller, product_id=prod_i.pk, quantity=1)
        evt_hold.clear(); evt_go.clear(); pid_05: list[int] = []

        def co_before_close():
            close_old_connections()
            try:
                def slow_sc(**kw):
                    with connection.cursor() as c:
                        c.execute("SELECT pg_backend_pid()")
                        pid_05.append(c.fetchone()[0])
                    evt_hold.set()
                    evt_go.wait(8)
                    return orig_sale_create(**kw)
                with patch.object(Sale.objects, "create", side_effect=slow_sc):
                    s = checkout_sale(actor=seller, draft_id=d_c5.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4())
                return {"ok": True, "correlative": s.correlative, "total": str(s.total_amount)}
            except Exception as exc:
                return {"ok": False, "type": type(exc).__name__, "error": str(exc)}
            finally:
                close_old_connections()

        def close_shift_race():
            close_old_connections()
            try:
                evt_hold.wait(8)
                cl = close_cash_shift(actor=seller, counted_amount=Decimal("90.00"))
                return {"ok": True, "expected": str(cl.expected_amount), "diff": str(cl.difference)}
            except Exception as exc:
                return {"ok": False, "type": type(exc).__name__, "error": str(exc)}
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            f5a = pool.submit(co_before_close)
            f5b = pool.submit(close_shift_race)
            blocked_05 = []
            for _ in range(50):
                if pid_05:
                    blocked_05 = inspect_blocking_pids(pid_05[0])
                    if blocked_05:
                        break
                time.sleep(0.05)
            evt_go.set()
            r5a = f5a.result(timeout=15)
            r5b = f5b.result(timeout=15)

        assert r5a["ok"] and r5b["ok"] and r5b["expected"] == "90.00" and r5b["diff"] == "0.00" and len(blocked_05) >= 1
        report["scenarios"]["05_CT_CONC_05_checkout_vs_close"] = {"checkout": r5a, "close": r5b, "pg_blocking_pids": blocked_05}
        report["checks"].append("05_CT_CONC_05_checkout_vs_close")

        # ── 06. Account deactivation lock race ────────────────────────────────
        shift_off = open_cash_shift(actor=seller_off, opening_amount=Decimal("20.00"))
        d_off = add_product_to_draft(actor=seller_off, product_id=prod_i.pk, quantity=1)
        evt_acc_hold = threading.Event(); evt_acc_go = threading.Event(); pid_06: list[int] = []

        def deactivate_seller_lock():
            close_old_connections()
            try:
                with transaction.atomic():
                    acc = Account.objects.select_for_update().get(pk=seller_off.pk)
                    with connection.cursor() as c:
                        c.execute("SELECT pg_backend_pid()")
                        pid_06.append(c.fetchone()[0])
                    acc.is_active = False
                    acc.save(update_fields=["is_active"])
                    evt_acc_hold.set()
                    evt_acc_go.wait(8)
                return {"ok": True}
            finally:
                close_old_connections()

        def try_co_off():
            close_old_connections()
            try:
                evt_acc_hold.wait(8)
                checkout_sale(actor=seller_off, draft_id=d_off.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4())
                return {"ok": True}
            except PermissionDenied as exc:
                return {"ok": False, "type": "PermissionDenied", "error": str(exc)}
            except Exception as exc:
                return {"ok": False, "type": type(exc).__name__, "error": str(exc)}
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            f6a = pool.submit(deactivate_seller_lock)
            f6b = pool.submit(try_co_off)
            blocked_06 = []
            for _ in range(50):
                if pid_06:
                    blocked_06 = inspect_blocking_pids(pid_06[0])
                    if blocked_06:
                        break
                time.sleep(0.05)
            evt_acc_go.set()
            r6a = f6a.result(timeout=15)
            r6b = f6b.result(timeout=15)

        assert r6a["ok"] and not r6b["ok"] and r6b["type"] == "PermissionDenied" and len(blocked_06) >= 1
        report["scenarios"]["06_account_lock_deactivation"] = {"admin": r6a, "checkout": r6b, "pg_blocking_pids": blocked_06}
        report["checks"].append("06_account_lock_deactivation")
        d_off.status = SaleDraft.Status.DISCARDED; d_off.discarded_at = tz.now(); d_off.save(update_fields=["status", "discarded_at"])
        shift_off.status = CashShift.Status.CLOSED; shift_off.save(update_fields=["status"])

        # ── 07. Concurrent Product price edit & Category deactivation during checkout ─
        shift_live = open_cash_shift(actor=seller, opening_amount=Decimal("20.00"))
        prod_live = Product.objects.create(category=cat, name="PG Live Edit", barcode="PG11B-LIVE", sale_price=Decimal("8.00"))
        confirm_initial_load(actor=wh, product=prod_live, lots=[LotInput("PG-LIVE-1", 5, Decimal("3.0000"), today + timedelta(days=20))])
        d_live = add_product_to_draft(actor=seller, product_id=prod_live.pk, quantity=1)
        evt_p_hold = threading.Event(); evt_p_go = threading.Event(); pid_07: list[int] = []

        def hold_prod_price():
            close_old_connections()
            try:
                with transaction.atomic():
                    p = Product.objects.select_for_update().get(pk=prod_live.pk)
                    with connection.cursor() as c:
                        c.execute("SELECT pg_backend_pid()")
                        pid_07.append(c.fetchone()[0])
                    p.sale_price = Decimal("9.50")
                    p.save(update_fields=["sale_price"])
                    evt_p_hold.set()
                    evt_p_go.wait(8)
                return {"ok": True, "new_price": "9.50"}
            finally:
                close_old_connections()

        def try_co_live():
            close_old_connections()
            try:
                evt_p_hold.wait(8)
                checkout_sale(actor=seller, draft_id=d_live.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4())
                return {"ok": True}
            except ValidationError as exc:
                return {"ok": False, "type": "ValidationError", "error": exc.messages[0]}
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            f7a = pool.submit(hold_prod_price)
            f7b = pool.submit(try_co_live)
            blocked_07 = []
            for _ in range(50):
                if pid_07:
                    blocked_07 = inspect_blocking_pids(pid_07[0])
                    if blocked_07:
                        break
                time.sleep(0.05)
            evt_p_go.set()
            r7a = f7a.result(timeout=15)
            r7b = f7b.result(timeout=15)

        assert r7a["ok"] and not r7b["ok"] and r7b["type"] == "ValidationError" and len(blocked_07) >= 1
        # Category deactivation inside checkout
        cat_off = Category.objects.create(name="PG Cat Off 11B")
        prod_cat_off = Product.objects.create(category=cat_off, name="PG Cat Off Prod", barcode="PG11B-COFF", sale_price=Decimal("4.00"))
        confirm_initial_load(actor=wh, product=prod_cat_off, lots=[LotInput("PG-COFF-1", 4, Decimal("1.5000"), today + timedelta(days=20))])
        discard_active_draft(actor=seller)
        d_coff = add_product_to_draft(actor=seller, product_id=prod_cat_off.pk, quantity=1)
        cat_off.is_active = False; cat_off.save(update_fields=["is_active"])
        try:
            checkout_sale(actor=seller, draft_id=d_coff.pk, cash_received=Decimal("5.00"), idempotency_key=uuid.uuid4())
            raise AssertionError("Deactivated category must be rejected")
        except ValidationError as exc:
            cat_off_err = exc.messages[0]
        discard_active_draft(actor=seller)
        report["scenarios"]["07_live_price_and_category_race"] = {
            "price_edit": r7a, "checkout": r7b, "pg_blocking_pids": blocked_07, "category_off_msg": cat_off_err
        }
        report["checks"].append("07_live_price_and_category_race")

        # ── 08. CT-ROLLBACK-02: post-write allocation & lot save rollback + retry ─
        d_rb = add_product_to_draft(actor=seller, product_id=prod_conc.pk, quantity=1)
        add_product_to_draft(actor=seller, product_id=prod_i.pk, quantity=1)
        before_s = Sale.objects.count(); before_sl = SaleLine.objects.count()
        before_alloc = SaleLotAllocation.objects.count(); before_cnt = SaleCounter.objects.get(id=1).next_value
        before_l_conc = Lot.objects.get(product=prod_conc).available_quantity
        before_l_i = Lot.objects.get(product=prod_i).available_quantity
        key_rb = uuid.uuid4()
        with patch("sales.services.reset_average_cost_if_empty", side_effect=RuntimeError("PG post-write fail after allocation+lot")):
            try:
                checkout_sale(actor=seller, draft_id=d_rb.pk, cash_received=Decimal("20.00"), idempotency_key=key_rb)
                raise AssertionError("Must fail")
            except RuntimeError:
                pass

        d_rb.refresh_from_db()
        assert (Sale.objects.count(), SaleLine.objects.count(), SaleLotAllocation.objects.count()) == (before_s, before_sl, before_alloc)
        assert SaleCounter.objects.get(id=1).next_value == before_cnt
        assert Lot.objects.get(product=prod_conc).available_quantity == before_l_conc
        assert Lot.objects.get(product=prod_i).available_quantity == before_l_i
        assert d_rb.status == SaleDraft.Status.ACTIVE

        s_retry = checkout_sale(actor=seller, draft_id=d_rb.pk, cash_received=Decimal("20.00"), idempotency_key=key_rb)
        assert SaleLotAllocation.objects.filter(line__sale=s_retry).count() == 2
        report["scenarios"]["08_CT_ROLLBACK_02_pg_and_retry"] = {
            "rolled_back_all_tables": True,
            "counter_preserved_during_rollback": before_cnt,
            "retry_same_key_sale": s_retry.correlative,
            "retry_allocations": 2,
        }
        report["checks"].append("08_CT_ROLLBACK_02_pg_and_retry")

        # ── 09. Direct PG SQL/ORM constraints + MAX_CASH_ACCUMULATED ─────────────
        pg_constraints = {}
        for cname, fn in [
            ("draft_qty_gt_999999", lambda: SaleDraftLine.objects.create(draft=SaleDraft.objects.create(cash_shift=shift_live, seller=seller), product=prod_i, quantity=1000000, unit_price=Decimal("1.00"))),
            ("alloc_qty_zero", lambda: SaleLotAllocation.objects.create(line=s_retry.lines.first(), lot=lot_conc, quantity=0, lot_snapshot_number="X", lot_snapshot_expiration_date=today, lot_snapshot_received_at=tz.now())),
            ("sale_neg_total", lambda: Sale.objects.create(cash_shift=shift_live, seller=seller, total_amount=Decimal("-1.00"), base_amount=Decimal("0.00"), igv_amount=Decimal("0.00"), discount_amount=Decimal("0.00"), cash_received=Decimal("0.00"), change_given=Decimal("0.00"), correlative="V-99999998", idempotency_key=uuid.uuid4())),
            ("dup_correlative", lambda: Sale.objects.create(cash_shift=shift_live, seller=seller, total_amount=Decimal("1.00"), base_amount=Decimal("0.85"), igv_amount=Decimal("0.15"), discount_amount=Decimal("0.00"), cash_received=Decimal("1.00"), change_given=Decimal("0.00"), correlative=s_retry.correlative, idempotency_key=uuid.uuid4())),
            ("close_diff_mismatch", lambda: CashShiftClose.objects.create(cash_shift=shift1, closed_by=seller, expected_amount=Decimal("90.00"), counted_amount=Decimal("85.00"), difference=Decimal("0.00"))),
        ]:
            try:
                with transaction.atomic():
                    fn()
                pg_constraints[cname] = False
            except IntegrityError:
                pg_constraints[cname] = True

        # Accumulated shift cap test in PG (MAX_CASH_ACCUMULATED = 999999999999.99)
        discard_active_draft(actor=seller)
        prod_cap = Product.objects.create(category=cat, name="PG Cap Prod", barcode="PG11B-CAP", sale_price=Decimal("100.00"))
        confirm_initial_load(actor=wh, product=prod_cap, lots=[LotInput("PG-CAP-1", 5, Decimal("10.0000"), today + timedelta(days=20))])
        d_cap = add_product_to_draft(actor=seller, product_id=prod_cap.pk, quantity=1)
        Sale.objects.create(
            cash_shift=shift_live, seller=seller, seller_snapshot_name=seller.display_name, cash_register_snapshot_code=reg.code,
            total_amount=Decimal("999999999990.00"), base_amount=Decimal("847457627110.17"), igv_amount=Decimal("152542372879.83"),
            discount_amount=Decimal("0.00"), cash_received=Decimal("999999999990.00"), change_given=Decimal("0.00"),
            correlative="V-00009999", idempotency_key=uuid.uuid4(),
        )
        cap_blocked = False
        try:
            checkout_sale(actor=seller, draft_id=d_cap.pk, cash_received=Decimal("100.00"), idempotency_key=uuid.uuid4())
        except ValidationError as exc:
            cap_blocked = "excedería la capacidad acumulada" in exc.messages[0]
        discard_active_draft(actor=seller)
        assert all(pg_constraints.values()) and cap_blocked
        report["scenarios"]["09_pg_constraints_and_accumulated_cap"] = {"constraints": pg_constraints, "accumulated_cap_blocked": cap_blocked}
        report["checks"].append("09_pg_constraints_and_accumulated_cap")

        # ── 10. Lima midnight boundary (04:59:59Z vs 05:00:00Z) ─────────────────
        exp_d = date(2026, 11, 12)
        prod_tz = Product.objects.create(category=cat, name="PG TZ Midnight 11B", barcode="PG11B-TZ1", sale_price=Decimal("6.00"))
        confirm_initial_load(actor=wh, product=prod_tz, lots=[LotInput("PG-TZ-EXP", 3, Decimal("2.0000"), date(2026, 11, 30))])
        Lot.objects.filter(product=prod_tz).update(expiration_date=exp_d)
        reg_tz = CashRegister.objects.create(code="CAJA-TZ")
        shift_tz = CashShift.objects.create(cash_register=reg_tz, seller=seller_off, opening_amount=Decimal("10.00"))
        seller_off.is_active = True; seller_off.save(update_fields=["is_active"])

        utc_b = datetime(2026, 11, 12, 4, 59, 59, tzinfo=dt_timezone.utc)
        utc_a = datetime(2026, 11, 12, 5, 0, 0, tzinfo=dt_timezone.utc)
        with patch("django.utils.timezone.now", return_value=utc_b):
            assert tz.localdate() == date(2026, 11, 11) and sellable_stock_for_product(prod_tz) == 3
            d_tz = add_product_to_draft(actor=seller_off, product_id=prod_tz.pk, quantity=1)
            s_tz_b = checkout_sale(actor=seller_off, draft_id=d_tz.pk, cash_received=Decimal("6.00"), idempotency_key=uuid.uuid4())
            Sale.objects.filter(pk=s_tz_b.pk).update(confirmed_at=utc_b)
        with patch("django.utils.timezone.now", return_value=utc_a):
            assert tz.localdate() == date(2026, 11, 12) and sellable_stock_for_product(prod_tz) == 0
            d_tz_exp = SaleDraft.objects.create(cash_shift=shift_tz, seller=seller_off)
            SaleDraftLine.objects.create(draft=d_tz_exp, product=prod_tz, quantity=1, unit_price=Decimal("6.00"))
            tz_rejected = False
            try:
                checkout_sale(actor=seller_off, draft_id=d_tz_exp.pk, cash_received=Decimal("6.00"), idempotency_key=uuid.uuid4())
            except ValidationError:
                tz_rejected = True
            assert tz_rejected
        report["scenarios"]["10_lima_midnight_utc_boundary"] = {"sellable_045959Z": 3, "sellable_050000Z": 0, "midnight_rejected": True}
        report["checks"].append("10_lima_midnight_utc_boundary")

    finally:
        connections.close_all()
        if pg_started:
            subprocess.run(
                [str(PG_BIN / "pg_ctl.exe"), "-D", str(dbdir), "-m", "fast", "-w", "stop"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        shutil.rmtree(cluster, ignore_errors=True)
        with socket.socket() as s:
            report["port_closed"] = s.connect_ex(("127.0.0.1", pg_port)) != 0
        report["build_after"] = build_snapshot()
        report["sources_stable"] = build_before == report["build_after"]
        report["prod_db_unchanged"] = sha_bytes(prod_db.read_bytes()) == prod_db_before
        report["prod_db_sha256"] = prod_db_before
        (OUT / "pg_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")

    print(json.dumps({
        "ok": len(report["checks"]) == 10 and report["port_closed"] and report["prod_db_unchanged"],
        "checks_count": len(report["checks"]),
        "pg_version": report.get("pg_version"),
        "port_closed": report["port_closed"],
        "prod_db_unchanged": report["prod_db_unchanged"],
        "sources_stable": report["sources_stable"],
    }, ensure_ascii=False))
    return 0 if (len(report["checks"]) == 10 and report["port_closed"] and report["prod_db_unchanged"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
