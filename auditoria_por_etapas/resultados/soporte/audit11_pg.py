"""Stage 11 real PostgreSQL 18.4 concurrency, lock wait (pg_blocking_pids), rollback, and Lima timezone suite.
Runs completely isolated in a temporary PG cluster and temporary SQLite audit marker dir.
Never loads operator .env and never modifies existing SQLite databases.
"""
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

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
SUPPORT = Path(__file__).resolve().parent
PG_BIN = Path("C:/Program Files/PostgreSQL/18/bin")


def digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def protected_snapshot() -> dict[str, str | None]:
    paths = [
        APP / "r1_pmv.sqlite3",
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]
    return {str(p.relative_to(ROOT)): digest(p) for p in paths}


def main() -> int:
    start_hashes = protected_snapshot()
    stamp = datetime.now(dt_timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)
    run_dir = RESULTS / "datos" / f"etapa11-pg-{stamp}"
    out_dir = RESULTS / "evidencias" / f"11-pg-{stamp}"
    run_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    (run_dir / "marker.json").write_text(json.dumps({"run": run_dir.name, "created_utc": stamp}), encoding="utf-8")
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")

    os.environ.update(
        AUDIT11_RUN_DIR=str(run_dir),
        AUDIT11_OUT=str(out_dir),
        AUDIT11_DEFAULT_COOKIES="1",
        DJANGO_SETTINGS_MODULE="audit11_settings",
    )
    sys.path.insert(0, str(APP))
    sys.path.insert(0, str(SUPPORT))

    import django
    django.setup()

    from django.conf import settings
    from django.core.exceptions import PermissionDenied, ValidationError
    from django.core.management import call_command
    from django.db import close_old_connections, connection, connections, transaction
    from django.utils import timezone as tz

    cluster = (Path(tempfile.gettempdir()) / ("audit11-pg-" + secrets.token_hex(8))).resolve()
    cluster.mkdir(exist_ok=False)
    dbdir = cluster / "data"
    pw_pg = secrets.token_urlsafe(32)
    pwfile = cluster / "pw"
    pwfile.write_text(pw_pg, encoding="utf-8")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        pg_port = s.getsockname()[1]

    report: dict = {
        "stamp_utc": stamp,
        "evidence": str((out_dir / "pg_report.json").relative_to(ROOT)),
        "pg_port": pg_port,
        "checks": [],
        "scenarios": {},
    }

    pg_started = False
    try:
        subprocess.run(
            [
                str(PG_BIN / "initdb.exe"),
                "-D", str(dbdir),
                "-U", "audit11",
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

        import psycopg
        from psycopg import sql

        dbname = "audit11_" + secrets.token_hex(4)
        with psycopg.connect(
            host="127.0.0.1", port=pg_port, user="audit11", password=pw_pg, dbname="postgres", autocommit=True
        ) as conn:
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
            pg_version = conn.execute("SELECT version()").fetchone()[0]

        connections.close_all()
        settings.DATABASES["default"] = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": dbname,
            "USER": "audit11",
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
        report["checks"].append("pg_migrate_clean")

        from cash.models import CashRegister, CashShift, CashShiftClose
        from cash.services import close_cash_shift
        from catalog.models import Category, Product
        from identity.models import Account, Role
        from inventory.models import Lot, StockWriteOff
        from inventory.services import LotInput, confirm_initial_load, write_off_stock
        from sales.models import Sale, SaleCounter, SaleDraft, SaleLine
        from sales.services import add_product_to_draft, checkout_sale, sellable_stock_for_product

        def inspect_blocking_pids(holder_backend_pid: int) -> list[dict]:
            with psycopg.connect(
                host="127.0.0.1", port=pg_port, user="audit11", password=pw_pg, dbname=dbname, autocommit=True
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

        # Seed roles and baseline users/products
        r_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
        r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
        r_sel, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

        admin = Account.objects.create_user("pg-admin@test.invalid", "PgPass123!A", display_name="PG Admin", role=r_admin)
        wh = Account.objects.create_user("pg-wh@test.invalid", "PgPass123!A", display_name="PG WH", role=r_wh)
        seller = Account.objects.create_user("pg-seller@test.invalid", "PgPass123!A", display_name="PG Seller", role=r_sel)
        seller_off = Account.objects.create_user("pg-seller-off@test.invalid", "PgPass123!A", display_name="PG Seller Off", role=r_sel)
        reg = CashRegister.objects.create(code="CAJA-01")
        cat = Category.objects.create(name="PG Audit Cat 11")
        today = tz.localdate()

        # ── Scenario 1 (CT-CONC-03): Competing checkout vs write_off_stock on last 2 units ──
        prod_conc = Product.objects.create(category=cat, name="PG Stock Conc", barcode="PG-CONC-01", sale_price=Decimal("5.00"))
        confirm_initial_load(
            actor=wh,
            product=prod_conc,
            lots=[LotInput("PG-LOT-C1", 2, Decimal("2.0000"), today + timedelta(days=20))],
        )
        lot_conc = Lot.objects.get(product=prod_conc)
        shift1 = CashShift.objects.create(cash_register=reg, seller=seller, opening_amount=Decimal("50.00"))
        draft_c = add_product_to_draft(actor=seller, product_id=prod_conc.pk, quantity=2)

        evt_hold = threading.Event()
        evt_go = threading.Event()
        holder_pid_1: list[int] = []
        orig_wo_save = Lot.save

        def hold_during_writeoff():
            close_old_connections()
            try:
                held = {"done": False}

                def slow_save(lot_self, *args, **kwargs):
                    if not held["done"] and lot_self.pk == lot_conc.pk:
                        held["done"] = True
                        with connection.cursor() as c:
                            c.execute("SELECT pg_backend_pid()")
                            holder_pid_1.append(c.fetchone()[0])
                        evt_hold.set()
                        evt_go.wait(8)
                    return orig_wo_save(lot_self, *args, **kwargs)

                with patch.object(Lot, "save", slow_save):
                    wo = write_off_stock(
                        actor=wh,
                        lot=lot_conc,
                        quantity=1,
                        reason=StockWriteOff.Reason.DAMAGE,
                        notes="Contencion real PostgreSQL",
                    )
                    return {"ok": True, "writeoff": str(wo.correlativo)}
            except Exception as exc:
                return {"ok": False, "type": type(exc).__name__, "error": str(exc)}
            finally:
                close_old_connections()

        def try_checkout_competing():
            close_old_connections()
            try:
                evt_hold.wait(8)
                s = checkout_sale(
                    actor=seller,
                    draft_id=draft_c.pk,
                    cash_received=Decimal("10.00"),
                    idempotency_key=uuid.uuid4(),
                )
                return {"ok": True, "sale": s.correlative}
            except Exception as exc:
                return {"ok": False, "type": type(exc).__name__, "error": str(exc)}
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            f_wo = pool.submit(hold_during_writeoff)
            f_co = pool.submit(try_checkout_competing)
            blocked_c3 = []
            for _ in range(40):
                if holder_pid_1:
                    blocked_c3 = inspect_blocking_pids(holder_pid_1[0])
                    if blocked_c3:
                        break
                time.sleep(0.05)
            evt_go.set()
            res_wo = f_wo.result(timeout=15)
            res_co = f_co.result(timeout=15)

        lot_conc.refresh_from_db()
        report["scenarios"]["CT_CONC_03_stock_contention"] = {
            "writeoff": res_wo,
            "checkout": res_co,
            "lot_after": lot_conc.available_quantity,
            "pg_blocking_pids": blocked_c3,
        }
        assert res_wo["ok"] is True and res_co["ok"] is False and res_co["type"] == "ValidationError"
        assert lot_conc.available_quantity == 1
        assert len(blocked_c3) >= 1, f"Expected real pg_blocking_pids in CT-CONC-03, got {blocked_c3}"
        report["checks"].append("CT_CONC_03_stock_contention")

        # Cleanup draft_c after failed contention checkout
        from sales.services import discard_active_draft
        discard_active_draft(actor=seller)

        # ── Scenario 2 (CT-CONC-04a & CT-CONC-04b): Concurrent Idempotency (identical vs divergent) ──
        prod_i = Product.objects.create(category=cat, name="PG Idem Prod", barcode="PG-IDEM-01", sale_price=Decimal("10.00"))
        confirm_initial_load(
            actor=wh,
            product=prod_i,
            lots=[LotInput("PG-LOT-I1", 10, Decimal("3.0000"), today + timedelta(days=20))],
        )

        # 4a: identical payload race
        draft_i1 = add_product_to_draft(actor=seller, product_id=prod_i.pk, quantity=1)
        key_i1 = uuid.uuid4()
        evt_hold.clear()
        evt_go.clear()
        pid_i1: list[int] = []
        orig_sale_create = Sale.objects.create

        def idem_worker_a(draft_obj, key_obj):
            close_old_connections()
            try:
                def slow_sale_create(**kw):
                    with connection.cursor() as c:
                        c.execute("SELECT pg_backend_pid()")
                        pid_i1.append(c.fetchone()[0])
                    evt_hold.set()
                    evt_go.wait(8)
                    return orig_sale_create(**kw)

                with patch.object(Sale.objects, "create", side_effect=slow_sale_create):
                    s = checkout_sale(
                        actor=seller,
                        draft_id=draft_obj.pk,
                        cash_received=Decimal("20.00"),
                        discount_amount=Decimal("2.00"),
                        idempotency_key=key_obj,
                    )
                    return {"ok": True, "sale_id": str(s.pk), "correlative": s.correlative}
            except Exception as exc:
                return {"ok": False, "type": type(exc).__name__, "error": str(exc)}
            finally:
                close_old_connections()

        def idem_worker_b(draft_obj, key_obj, cash_val, disc_val):
            close_old_connections()
            try:
                evt_hold.wait(8)
                s = checkout_sale(
                    actor=seller,
                    draft_id=draft_obj.pk,
                    cash_received=cash_val,
                    discount_amount=disc_val,
                    idempotency_key=key_obj,
                )
                return {"ok": True, "sale_id": str(s.pk), "correlative": s.correlative}
            except Exception as exc:
                return {"ok": False, "type": type(exc).__name__, "error": str(exc)}
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            fa = pool.submit(idem_worker_a, draft_i1, key_i1)
            fb = pool.submit(idem_worker_b, draft_i1, key_i1, Decimal("20.00"), Decimal("2.00"))
            blocked_i1 = []
            for _ in range(40):
                if pid_i1:
                    blocked_i1 = inspect_blocking_pids(pid_i1[0])
                    if blocked_i1:
                        break
                time.sleep(0.05)
            evt_go.set()
            r4a_a = fa.result(timeout=15)
            r4a_b = fb.result(timeout=15)

        report["scenarios"]["CT_CONC_04a_idempotent_same_payload"] = {
            "worker_a": r4a_a,
            "worker_b": r4a_b,
            "pg_blocking_pids": blocked_i1,
        }
        assert r4a_a["ok"] and r4a_b["ok"] and r4a_a["sale_id"] == r4a_b["sale_id"]
        assert Sale.objects.filter(idempotency_key=key_i1).count() == 1
        assert Lot.objects.get(product=prod_i).available_quantity == 9
        assert len(blocked_i1) >= 1, f"Expected real pg_blocking_pids in CT-CONC-04a, got {blocked_i1}"
        report["checks"].append("CT_CONC_04a_idempotent_same_payload")

        # 4b: divergent payload race (MUST commit winner and raise ValidationError for loser)
        draft_i2 = add_product_to_draft(actor=seller, product_id=prod_i.pk, quantity=1)
        key_i2 = uuid.uuid4()
        evt_hold.clear()
        evt_go.clear()
        pid_i1.clear()
        with ThreadPoolExecutor(max_workers=2) as pool:
            fa = pool.submit(idem_worker_a, draft_i2, key_i2)
            fb = pool.submit(idem_worker_b, draft_i2, key_i2, Decimal("50.00"), Decimal("0.00"))
            blocked_i2 = []
            for _ in range(40):
                if pid_i1:
                    blocked_i2 = inspect_blocking_pids(pid_i1[0])
                    if blocked_i2:
                        break
                time.sleep(0.05)
            evt_go.set()
            r4b_a = fa.result(timeout=15)
            r4b_b = fb.result(timeout=15)

        report["scenarios"]["CT_CONC_04b_idempotent_divergent_payload"] = {
            "worker_a": r4b_a,
            "worker_b": r4b_b,
            "pg_blocking_pids": blocked_i2,
        }
        assert r4b_a["ok"] is True and r4b_b["ok"] is False and r4b_b["type"] == "ValidationError"
        assert Sale.objects.filter(idempotency_key=key_i2).count() == 1
        assert Lot.objects.get(product=prod_i).available_quantity == 8
        report["checks"].append("CT_CONC_04b_idempotent_divergent_payload")

        # ── Scenario 3 (CT-CONC-05): Concurrent checkout_sale vs close_cash_shift ──
        # Sales so far on shift1: two sales of 8.00 net each => total_amount sum = 16.00; next sale adds 8.00 => 24.00 + 50 opening = 74.00
        draft_c5 = add_product_to_draft(actor=seller, product_id=prod_i.pk, quantity=1)
        evt_hold.clear()
        evt_go.clear()
        pid_c5: list[int] = []

        def hold_checkout_then_commit():
            close_old_connections()
            try:
                def slow_sale_create(**kw):
                    with connection.cursor() as c:
                        c.execute("SELECT pg_backend_pid()")
                        pid_c5.append(c.fetchone()[0])
                    evt_hold.set()
                    evt_go.wait(8)
                    return orig_sale_create(**kw)

                with patch.object(Sale.objects, "create", side_effect=slow_sale_create):
                    s = checkout_sale(
                        actor=seller,
                        draft_id=draft_c5.pk,
                        cash_received=Decimal("10.00"),
                        discount_amount=Decimal("2.00"),
                        idempotency_key=uuid.uuid4(),
                    )
                    return {"ok": True, "sale_id": str(s.pk), "total": str(s.total_amount)}
            finally:
                close_old_connections()

        def close_shift_competing():
            close_old_connections()
            try:
                evt_hold.wait(8)
                cl = close_cash_shift(actor=seller, counted_amount=Decimal("74.00"))
                return {"ok": True, "expected": str(cl.expected_amount), "diff": str(cl.difference)}
            except Exception as exc:
                return {"ok": False, "type": type(exc).__name__, "error": str(exc)}
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            fc_co = pool.submit(hold_checkout_then_commit)
            fc_cl = pool.submit(close_shift_competing)
            blocked_c5 = []
            for _ in range(40):
                if pid_c5:
                    blocked_c5 = inspect_blocking_pids(pid_c5[0])
                    if blocked_c5:
                        break
                time.sleep(0.05)
            evt_go.set()
            r5_co = fc_co.result(timeout=15)
            r5_cl = fc_cl.result(timeout=15)

        report["scenarios"]["CT_CONC_05_checkout_vs_cash_close"] = {
            "checkout": r5_co,
            "close": r5_cl,
            "pg_blocking_pids": blocked_c5,
        }
        assert r5_co["ok"] and r5_cl["ok"] and r5_cl["expected"] == "74.00" and r5_cl["diff"] == "0.00"
        assert len(blocked_c5) >= 1, f"Expected real pg_blocking_pids in CT-CONC-05, got {blocked_c5}"
        report["checks"].append("CT_CONC_05_checkout_vs_cash_close")

        # ── Scenario 4: Account lock serialization (checkout_sale vs Account deactivation lock) ──
        shift_off = CashShift.objects.create(cash_register=reg, seller=seller_off, opening_amount=Decimal("30.00"))
        draft_off = add_product_to_draft(actor=seller_off, product_id=prod_i.pk, quantity=1)
        evt_acc_locked = threading.Event()
        evt_acc_commit = threading.Event()
        pid_acc: list[int] = []

        def lock_and_deactivate_seller():
            close_old_connections()
            try:
                with transaction.atomic():
                    Role.objects.select_for_update().get(code=Role.Code.ADMIN)
                    acc = Account.objects.select_for_update().get(pk=seller_off.pk)
                    with connection.cursor() as c:
                        c.execute("SELECT pg_backend_pid()")
                        pid_acc.append(c.fetchone()[0])
                    acc.is_active = False
                    acc.save(update_fields=["is_active"])
                    evt_acc_locked.set()
                    evt_acc_commit.wait(8)
                return {"ok": True}
            finally:
                close_old_connections()

        def try_checkout_during_deactivation():
            close_old_connections()
            try:
                evt_acc_locked.wait(8)
                checkout_sale(
                    actor=seller_off,
                    draft_id=draft_off.pk,
                    cash_received=Decimal("10.00"),
                    idempotency_key=uuid.uuid4(),
                )
                return {"ok": True}
            except PermissionDenied as exc:
                return {"ok": False, "type": "PermissionDenied", "error": str(exc)}
            except Exception as exc:
                return {"ok": False, "type": type(exc).__name__, "error": str(exc)}
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            fa_lock = pool.submit(lock_and_deactivate_seller)
            fa_co = pool.submit(try_checkout_during_deactivation)
            blocked_acc = []
            for _ in range(40):
                if pid_acc:
                    blocked_acc = inspect_blocking_pids(pid_acc[0])
                    if blocked_acc:
                        break
                time.sleep(0.05)
            evt_acc_commit.set()
            r_acc_admin = fa_lock.result(timeout=15)
            r_acc_co = fa_co.result(timeout=15)

        report["scenarios"]["account_lock_checkout_vs_deactivation"] = {
            "admin": r_acc_admin,
            "checkout": r_acc_co,
            "pg_blocking_pids": blocked_acc,
        }
        assert r_acc_admin["ok"] and not r_acc_co["ok"] and r_acc_co["type"] == "PermissionDenied"
        assert Lot.objects.get(product=prod_i).available_quantity == 7
        assert len(blocked_acc) >= 1, f"Expected real pg_blocking_pids on Account lock, got {blocked_acc}"
        report["checks"].append("account_lock_checkout_vs_deactivation")

        # Cleanup seller_off draft/shift so reg is free
        draft_off.status = SaleDraft.Status.DISCARDED
        draft_off.discarded_at = tz.now()
        draft_off.save(update_fields=["status", "discarded_at"])
        shift_off.status = CashShift.Status.CLOSED
        shift_off.save(update_fields=["status"])

        # ── Scenario 5 (CT-ROLLBACK-02): Induced mid-checkout exception rolls back PG transaction completely ──
        shift_rb = CashShift.objects.create(cash_register=reg, seller=seller, opening_amount=Decimal("20.00"))
        draft_rb = add_product_to_draft(actor=seller, product_id=prod_conc.pk, quantity=1)
        add_product_to_draft(actor=seller, product_id=prod_i.pk, quantity=2)

        before_sales_count = Sale.objects.count()
        before_lines_count = SaleLine.objects.count()
        counter_rb = SaleCounter.objects.get(id=1)
        before_counter_val = counter_rb.next_value
        before_conc_qty = Lot.objects.get(product=prod_conc).available_quantity
        before_i_qty = Lot.objects.get(product=prod_i).available_quantity

        lot_calls = {"n": 0}
        real_lot_save = Lot.save

        def fail_second_lot(lot_self, *args, **kwargs):
            lot_calls["n"] += 1
            if lot_calls["n"] == 2:
                raise RuntimeError("CT-ROLLBACK-02 Postgres mid-checkout failure")
            return real_lot_save(lot_self, *args, **kwargs)

        try:
            with patch.object(Lot, "save", fail_second_lot):
                checkout_sale(
                    actor=seller,
                    draft_id=draft_rb.pk,
                    cash_received=Decimal("30.00"),
                    idempotency_key=uuid.uuid4(),
                )
            raise AssertionError("Expected RuntimeError was not raised")
        except RuntimeError:
            pass

        counter_rb.refresh_from_db()
        draft_rb.refresh_from_db()
        assert Sale.objects.count() == before_sales_count
        assert SaleLine.objects.count() == before_lines_count
        assert counter_rb.next_value == before_counter_val
        assert Lot.objects.get(product=prod_conc).available_quantity == before_conc_qty
        assert Lot.objects.get(product=prod_i).available_quantity == before_i_qty
        assert draft_rb.status == SaleDraft.Status.ACTIVE
        report["scenarios"]["CT_ROLLBACK_02_pg"] = {
            "sales_unchanged": True,
            "counter_unchanged": counter_rb.next_value,
            "lots_intact": [before_conc_qty, before_i_qty],
            "draft_still_active": True,
        }
        report["checks"].append("CT_ROLLBACK_02_pg")
        discard_active_draft(actor=seller)

        # ── Scenario 6: UTC <-> America/Lima midnight boundary (04:59:59Z vs 05:00:00Z) ──
        exp_date = date(2026, 11, 12)
        prod_tz = Product.objects.create(category=cat, name="PG TZ Midnight", barcode="PG-TZ-01", sale_price=Decimal("6.00"))
        confirm_initial_load(
            actor=wh,
            product=prod_tz,
            lots=[LotInput("PG-TZ-EXP12", 5, Decimal("2.0000"), date(2026, 11, 30))],
        )
        Lot.objects.filter(product=prod_tz).update(expiration_date=exp_date)
        prod_tz_safe = Product.objects.create(category=cat, name="PG TZ Safe", barcode="PG-TZ-02", sale_price=Decimal("7.00"))
        confirm_initial_load(
            actor=wh,
            product=prod_tz_safe,
            lots=[LotInput("PG-TZ-SAFE", 5, Decimal("2.5000"), date(2026, 11, 30))],
        )

        utc_before = datetime(2026, 11, 12, 4, 59, 59, tzinfo=dt_timezone.utc)   # 2026-11-11 23:59:59 Lima
        utc_after = datetime(2026, 11, 12, 5, 0, 0, tzinfo=dt_timezone.utc)     # 2026-11-12 00:00:00 Lima

        with patch("django.utils.timezone.now", return_value=utc_before):
            assert tz.localdate() == date(2026, 11, 11)
            assert sellable_stock_for_product(prod_tz) == 5
            d_before = add_product_to_draft(actor=seller, product_id=prod_tz.pk, quantity=1)
            s_before = checkout_sale(
                actor=seller,
                draft_id=d_before.pk,
                cash_received=Decimal("6.00"),
                idempotency_key=uuid.uuid4(),
            )
            Sale.objects.filter(pk=s_before.pk).update(confirmed_at=utc_before)

        # At 05:00:00Z (Lima 2026-11-12 00:00:00), PG-TZ-EXP12 expires TODAY in Lima -> NOT sellable!
        with patch("django.utils.timezone.now", return_value=utc_after):
            assert tz.localdate() == date(2026, 11, 12)
            assert sellable_stock_for_product(prod_tz) == 0
            d_after_bad = SaleDraft.objects.create(cash_shift=shift_rb, seller=seller)
            from sales.models import SaleDraftLine
            SaleDraftLine.objects.create(draft=d_after_bad, product=prod_tz, quantity=1, unit_price=Decimal("6.00"))
            try:
                checkout_sale(
                    actor=seller,
                    draft_id=d_after_bad.pk,
                    cash_received=Decimal("6.00"),
                    idempotency_key=uuid.uuid4(),
                )
                raise AssertionError("Lot expiring 2026-11-12 must be rejected at 05:00:00Z Lima midnight")
            except ValidationError:
                pass
            discard_active_draft(actor=seller)

            # Safe lot sale at 05:00:00Z belongs to Lima 2026-11-12 business date
            d_after_ok = add_product_to_draft(actor=seller, product_id=prod_tz_safe.pk, quantity=1)
            s_after = checkout_sale(
                actor=seller,
                draft_id=d_after_ok.pk,
                cash_received=Decimal("7.00"),
                idempotency_key=uuid.uuid4(),
            )
            Sale.objects.filter(pk=s_after.pk).update(confirmed_at=utc_after)

        count_nov11 = Sale.objects.filter(pk__in=[s_before.pk, s_after.pk], confirmed_at__date=date(2026, 11, 11)).count()
        count_nov12 = Sale.objects.filter(pk__in=[s_before.pk, s_after.pk], confirmed_at__date=date(2026, 11, 12)).count()
        assert count_nov11 == 1 and count_nov12 == 1
        report["scenarios"]["lima_midnight_utc_boundary"] = {
            "sellable_at_04_59_59Z": 5,
            "sellable_at_05_00_00Z": 0,
            "nov11_lima_sales": count_nov11,
            "nov12_lima_sales": count_nov12,
        }
        report["checks"].append("lima_midnight_utc_boundary")

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
        report["protected_unchanged"] = {
            k: (digest(ROOT / k) if (ROOT / k).exists() else None) == v for k, v in start_hashes.items()
        }
        (out_dir / "pg_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    print(json.dumps({
        "evidence": report["evidence"],
        "pg_version": report.get("pg_version"),
        "transaction_isolation": report.get("transaction_isolation"),
        "checks": report["checks"],
        "port_closed": report["port_closed"],
        "protected_unchanged": all(report["protected_unchanged"].values()),
    }, ensure_ascii=False, indent=2))
    return 0 if (len(report["checks"]) == 8 and report["port_closed"] and all(report["protected_unchanged"].values())) else 1


if __name__ == "__main__":
    raise SystemExit(main())
