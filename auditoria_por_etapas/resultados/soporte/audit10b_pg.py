"""Ephemeral isolated PostgreSQL 18.4 audit runner for Stage 10-B (9 concurrency/DB/PG cases)."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone as dt_tz
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parents[0]
ROOT = RESULTS.parents[1]
PMV = ROOT / "r1-pmv"
PG_BIN = Path("C:/Program Files/PostgreSQL/18/bin")
EV_DIR = RESULTS / "evidencias" / "10-B-20261114"
OPERATIONAL_DB = PMV / "r1_pmv.sqlite3"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_ephemeral_pg(pg_dir: Path, port: int) -> None:
    pgdata = pg_dir / "data"
    logfile = pg_dir / "pg.log"
    init_log = pg_dir / "initdb.log"
    with init_log.open("wb") as f_init:
        r_init = subprocess.run(
            [
                str(PG_BIN / "initdb.exe"),
                "-D",
                str(pgdata),
                "-U",
                "postgres",
                "-A",
                "trust",
                "-E",
                "UTF8",
                "--locale=C",
            ],
            stdout=f_init,
            stderr=subprocess.STDOUT,
        )
    if r_init.returncode != 0:
        raise RuntimeError("initdb failed: " + init_log.read_text(encoding="cp1252", errors="replace"))

    ctl_log = pg_dir / "pg_ctl_start.log"
    with ctl_log.open("wb") as f_ctl:
        r_start = subprocess.run(
            [
                str(PG_BIN / "pg_ctl.exe"),
                "-D",
                str(pgdata),
                "-l",
                str(logfile),
                "-o",
                f"-p {port} -h 127.0.0.1",
                "-w",
                "start",
            ],
            stdout=f_ctl,
            stderr=subprocess.STDOUT,
            timeout=30,
        )
    if r_start.returncode != 0:
        raise RuntimeError(
            "pg_ctl start failed: "
            + ctl_log.read_text(encoding="cp1252", errors="replace")
            + "\n"
            + (logfile.read_text(encoding="cp1252", errors="replace") if logfile.exists() else "")
        )

    cdb_log = pg_dir / "createdb.log"
    with cdb_log.open("wb") as f_cdb:
        r_createdb = subprocess.run(
            [
                str(PG_BIN / "createdb.exe"),
                "-h",
                "127.0.0.1",
                "-p",
                str(port),
                "-U",
                "postgres",
                "audit10b_pg",
            ],
            stdout=f_cdb,
            stderr=subprocess.STDOUT,
            timeout=20,
        )
    if r_createdb.returncode != 0:
        raise RuntimeError("createdb failed: " + cdb_log.read_text(encoding="cp1252", errors="replace"))


def stop_ephemeral_pg(pg_dir: Path) -> None:
    pgdata = pg_dir / "data"
    if (pgdata / "postmaster.pid").exists():
        subprocess.run(
            [str(PG_BIN / "pg_ctl.exe"), "-D", str(pgdata), "stop", "-m", "immediate", "-w"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=15,
        )


def run_worker_suite() -> dict:
    sys.path.insert(0, str(PMV))
    sys.path.insert(0, str(HERE))
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit10b_pg_settings"
    import django
    django.setup()

    import psycopg
    from django.core.exceptions import PermissionDenied, ValidationError
    from django.core.management import call_command
    from django.db import IntegrityError, connection, connections, transaction
    from django.test.utils import CaptureQueriesContext
    from django.utils import timezone

    from cash.models import CashRegister, CashShift
    from cash.services import close_cash_shift, open_cash_shift
    from catalog.models import Category, Product
    from catalog.services import (
        create_category,
        product_edit_snapshot,
        register_canned_product,
        toggle_category_status,
        update_product,
    )
    from identity.models import Account, Role
    from inventory.models import Lot
    from inventory.services import LotInput, confirm_initial_load, create_supplier
    from sales.models import Sale, SaleDraft, SaleDraftLine
    from sales.services import (
        add_product_to_draft,
        checkout_sale,
        discard_active_draft,
        draft_signature,
        update_draft_line,
    )
    from sales.views import _search_products

    call_command("migrate", verbosity=0, interactive=False)
    ver_row = connection.cursor()
    ver_row.execute("SELECT version(), current_database();")
    pg_version, pg_db = ver_row.fetchone()

    r_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    r_sell, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})
    pw = f"Pg10b!{secrets.token_hex(8)}"
    admin = Account.objects.create_user(email="admin.pg@demo.invalid", display_name="Admin PG", role=r_admin, password=pw)
    wh = Account.objects.create_user(email="wh.pg@demo.invalid", display_name="Almacenero PG", role=r_wh, password=pw)
    seller = Account.objects.create_user(email="seller.pg@demo.invalid", display_name="Vendedor PG", role=r_sell, password=pw)
    CashRegister.objects.create(code="CAJA-01", is_active=True)

    cat = create_category(actor=admin, name="Productos enlatados")
    sup = create_supplier(actor=admin, name="Proveedor PG SAC", ruc="20123456786", phone="999111222")
    today = timezone.localdate()

    cases = []

    def add_case(cid: str, ok: bool, detail: dict):
        cases.append({"id": cid, "ok": bool(ok), **detail})

    # PG01: Lima midnight expiration boundary (04:59:58 UTC = 23:59:58 Lima today vs 05:00:01 UTC = 00:00:01 Lima on exp_day)
    exp_day = today + timedelta(days=1)
    p1 = register_canned_product(
        actor=admin, name="Conserva Medianoche", barcode="7751001000010", category=cat, unit="UND",
        sale_price=Decimal("5.00"), minimum_stock=2, barcode_type=Product.BarcodeType.GTIN,
    )
    with patch("django.utils.timezone.now", return_value=datetime(today.year, today.month, today.day, 12, 0, tzinfo=dt_tz.utc)):
        confirm_initial_load(
            actor=wh, product=p1, supplier=sup, business_date=today,
            lots=[LotInput(number="L-MID", quantity=5, unit_cost=Decimal("2.50"), expiration_date=exp_day)],
        )
    shift = open_cash_shift(actor=seller, opening_amount=Decimal("100.00"))
    t_2359_lima = datetime(today.year, today.month, today.day, 23, 59, 58, tzinfo=timezone.get_current_timezone()).astimezone(dt_tz.utc)
    t_0001_lima = t_2359_lima + timedelta(seconds=3)
    with patch("django.utils.timezone.now", return_value=t_2359_lima):
        d1 = add_product_to_draft(actor=seller, product_id=p1.pk, quantity=1)
        before_mid_ok = d1.lines.count() == 1
    discard_active_draft(actor=seller)
    after_mid_err = ""
    with patch("django.utils.timezone.now", return_value=t_0001_lima):
        try:
            add_product_to_draft(actor=seller, product_id=p1.pk, quantity=1)
        except ValidationError as exc:
            after_mid_err = " ".join(exc.messages)
    add_case(
        "PG01_lima_midnight_expiration_boundary",
        before_mid_ok and ("no tiene existencias vendibles disponibles" in after_mid_err.lower()),
        {
            "before_mid_ok": before_mid_ok,
            "after_mid_err": after_mid_err,
        },
    )

    # PG02: --locale=C Unicode / diacritics / & / spaces / NUL char safety
    p_uni = register_canned_product(
        actor=admin, name="Café & Té Especial 100g", barcode="775-UNI-10B", category=cat, unit="UND",
        sale_price=Decimal("4.50"), minimum_stock=1, barcode_type=Product.BarcodeType.INTERNAL,
    )
    confirm_initial_load(
        actor=wh, product=p_uni, supplier=sup, business_date=today,
        lots=[LotInput(number="L-UNI", quantity=6, unit_cost=Decimal("2.00"), expiration_date=today + timedelta(days=30))],
    )
    q_uni = list(_search_products("  café & té  ").values_list("name", flat=True))
    nul_status = None
    nul_err = None
    try:
        from django.test import Client
        cli = Client(HTTP_HOST="127.0.0.1")
        cli.post("/", {"email": seller.email, "password": pw})
        r_nul = cli.get("/ventas/", {"query": "abc\x00def"})
        nul_status = r_nul.status_code
    except Exception as exc:
        nul_err = f"{type(exc).__name__}: {exc}"
    add_case("PG02_locale_c_unicode_and_nul_safety", "Café & Té Especial 100g" in q_uni and nul_status in (200, 400), {
        "found": q_uni, "nul_http_status": nul_status, "nul_err": nul_err,
    })

    # PG03: Two concurrent threads racing add(4) + add(4) on stock=6 via Barrier(2)
    barrier3 = threading.Barrier(2)
    res3 = []

    def worker_add(qty):
        try:
            connections.close_all()
            barrier3.wait(timeout=5)
            d = add_product_to_draft(actor=seller, product_id=p_uni.pk, quantity=qty)
            ln = d.lines.get(product=p_uni)
            res3.append(("OK", ln.quantity))
        except Exception as exc:
            res3.append(("ERR", str(exc)))
        finally:
            connections.close_all()

    t1 = threading.Thread(target=worker_add, args=(4,))
    t2 = threading.Thread(target=worker_add, args=(4,))
    t1.start(); t2.start(); t1.join(); t2.join()
    ok3_count = sum(1 for k, _ in res3 if k == "OK")
    err3_count = sum(1 for k, _ in res3 if k == "ERR")
    final_line_qty = SaleDraftLine.objects.filter(draft__status="ACTIVE", product=p_uni).values_list("quantity", flat=True).first()
    discard_active_draft(actor=seller)
    add_case("PG03_concurrent_add_stock_ceiling", ok3_count == 1 and err3_count == 1 and final_line_qty == 4, {
        "results": res3, "final_line_qty": final_line_qty,
    })

    # PG04: Concurrent add vs close_cash_shift AND update vs discard
    d4 = add_product_to_draft(actor=seller, product_id=p_uni.pk, quantity=1)
    l4 = d4.lines.get(product=p_uni)
    barrier4 = threading.Barrier(2)
    res4 = []

    def w_upd():
        try:
            connections.close_all()
            barrier4.wait(timeout=5)
            update_draft_line(actor=seller, line_id=l4.pk, quantity=2)
            res4.append(("UPD_OK", None))
        except Exception as exc:
            res4.append(("UPD_ERR", str(exc)))
        finally:
            connections.close_all()

    def w_disc():
        try:
            connections.close_all()
            barrier4.wait(timeout=5)
            discard_active_draft(actor=seller)
            res4.append(("DISC_OK", None))
        except Exception as exc:
            res4.append(("DISC_ERR", str(exc)))
        finally:
            connections.close_all()

    tu = threading.Thread(target=w_upd); td = threading.Thread(target=w_disc)
    tu.start(); td.start(); tu.join(); td.join()
    discard_active_draft(actor=seller)
    active_after_disc = SaleDraft.objects.filter(status="ACTIVE").count()

    # Race add vs close_cash_shift
    barrier4b = threading.Barrier(2)
    res4b = []

    def w_add4b():
        try:
            connections.close_all()
            barrier4b.wait(timeout=5)
            add_product_to_draft(actor=seller, product_id=p_uni.pk, quantity=1)
            res4b.append("ADD_OK")
        except Exception as exc:
            res4b.append("ADD_ERR:" + str(exc))
        finally:
            connections.close_all()

    def w_cls4b():
        try:
            connections.close_all()
            barrier4b.wait(timeout=5)
            close_cash_shift(actor=seller, counted_amount=Decimal("100.00"))
            res4b.append("CLOSE_OK")
        except Exception as exc:
            res4b.append("CLOSE_ERR:" + str(exc))
        finally:
            connections.close_all()

    ta = threading.Thread(target=w_add4b); tc = threading.Thread(target=w_cls4b)
    ta.start(); tc.start(); ta.join(); tc.join()
    shift.refresh_from_db()
    invariant4b = not (shift.status == CashShift.Status.CLOSED and SaleDraft.objects.filter(cash_shift=shift, status="ACTIVE").exists())
    if shift.status == CashShift.Status.OPEN:
        discard_active_draft(actor=seller)
    else:
        shift = open_cash_shift(actor=seller, opening_amount=Decimal("100.00"))
    add_case("PG04_concurrent_update_discard_and_add_close_invariant", active_after_disc == 0 and invariant4b, {
        "upd_vs_disc": res4, "add_vs_close": res4b, "invariant_ok": invariant4b,
    })

    # PG05: Real PG lock contention on Account (pg_blocking_pids > 0) + mid-wait revocation => PermissionDenied
    locked_ready = threading.Event()
    waiter_started = threading.Event()
    blocking_observed = []
    other_activity = []
    revoked_res = []

    def locker_conn():
        conn_info = f"host=127.0.0.1 port={os.environ['AUDIT10B_PG_PORT']} user=postgres dbname=audit10b_pg"
        with psycopg.connect(conn_info, autocommit=False) as c:
            with c.cursor() as cur:
                cur.execute("SELECT id FROM identity_account WHERE id = %s FOR UPDATE", (str(seller.pk),))
                locked_ready.set()
                waiter_started.wait(timeout=5)
                # Poll pg_blocking_pids until waiter hits FOR UPDATE lock on identity_account (max 4s)
                # Clear PG stats snapshot each iteration because stats_fetch_consistency='cache' freezes pg_stat_activity inside a transaction.
                for _ in range(80):
                    cur.execute("SELECT pg_stat_clear_snapshot()")
                    cur.execute(
                        "SELECT pid, wait_event_type, wait_event, pg_blocking_pids(pid) "
                        "FROM pg_stat_activity "
                        "WHERE datname='audit10b_pg' AND pid <> pg_backend_pid() AND cardinality(pg_blocking_pids(pid)) > 0"
                    )
                    rows = cur.fetchall()
                    if rows:
                        blocking_observed.append([[r[0], r[1], r[2], list(r[3])] for r in rows])
                        break
                    time.sleep(0.05)
                cur.execute(
                    "SELECT pid, state, wait_event_type, wait_event FROM pg_stat_activity "
                    "WHERE datname='audit10b_pg' AND pid <> pg_backend_pid()"
                )
                other_activity.extend([[r[0], r[1], r[2], r[3]] for r in cur.fetchall()])
                cur.execute("UPDATE identity_account SET is_active = false WHERE id = %s", (str(seller.pk),))
            c.commit()

    def blocked_seller_op():
        try:
            connections.close_all()
            locked_ready.wait(timeout=5)
            waiter_started.set()
            add_product_to_draft(actor=seller, product_id=p_uni.pk, quantity=1)
            revoked_res.append("UNEXPECTED_OK")
        except PermissionDenied as exc:
            revoked_res.append("PermissionDenied:" + str(exc))
        except Exception as exc:
            revoked_res.append(type(exc).__name__ + ":" + str(exc))
        finally:
            connections.close_all()

    tl = threading.Thread(target=locker_conn); tw = threading.Thread(target=blocked_seller_op)
    tl.start(); tw.start(); tl.join(); tw.join()
    Account.objects.filter(pk=seller.pk).update(is_active=True)
    seller.refresh_from_db()
    add_case(
        "PG05_account_lock_pg_blocking_pids_and_revocation",
        len(blocking_observed) > 0 and any(x.startswith("PermissionDenied:") for x in revoked_res) and SaleDraft.objects.filter(status="ACTIVE").count() == 0,
        {
            "pg_blocking_pids_observed": blocking_observed,
            "other_activity_snapshot": other_activity,
            "waiter_outcome": revoked_res,
        },
    )

    # PG06: Concurrent category toggle vs add_product_to_draft (zero deadlock, consistent result)
    cat_b = create_category(actor=admin, name="Enlatados B")
    p_b = register_canned_product(
        actor=admin, name="Jurel 425g", barcode="7751001000096", category=cat_b, unit="UND",
        sale_price=Decimal("7.00"), minimum_stock=1, barcode_type=Product.BarcodeType.GTIN,
    )
    confirm_initial_load(
        actor=wh, product=p_b, supplier=sup, business_date=today,
        lots=[LotInput(number="L-JUR", quantity=5, unit_cost=Decimal("3.00"), expiration_date=today + timedelta(days=30))],
    )
    b6 = threading.Barrier(2)
    r6 = []

    def w_cat():
        try:
            connections.close_all()
            b6.wait(timeout=5)
            toggle_category_status(actor=admin, category=cat_b, is_active=False)
            r6.append("CAT_DISABLED")
        except Exception as exc:
            r6.append("CAT_ERR:" + str(exc))
        finally:
            connections.close_all()

    def w_add_b():
        try:
            connections.close_all()
            b6.wait(timeout=5)
            add_product_to_draft(actor=seller, product_id=p_b.pk, quantity=1)
            r6.append("ADD_OK")
        except Exception as exc:
            r6.append("ADD_ERR:" + str(exc))
        finally:
            connections.close_all()

    tc6 = threading.Thread(target=w_cat); ta6 = threading.Thread(target=w_add_b)
    tc6.start(); ta6.start(); tc6.join(); ta6.join()
    cat_b.refresh_from_db()
    add_case("PG06_concurrent_category_toggle_vs_draft_no_deadlock", (not cat_b.is_active) and all("DEADLOCK" not in s.upper() for s in r6), {
        "outcomes": r6, "cat_active_after": cat_b.is_active,
    })
    discard_active_draft(actor=seller)

    # PG07: N+1 query invariance (1 vs 20 products) + EXPLAIN (FORMAT JSON) on PG 18.4
    with CaptureQueriesContext(connection) as ctx1:
        list(_search_products("Conserva").values_list("id", flat=True))
    q_count_before = len(ctx1)
    for idx in range(20):
        px = register_canned_product(
            actor=admin, name=f"Conserva Lote {idx:02d}", barcode=f"775999000{idx:04d}", category=cat, unit="UND",
            sale_price=Decimal("3.50"), minimum_stock=1, barcode_type=Product.BarcodeType.INTERNAL,
        )
        confirm_initial_load(
            actor=wh, product=px, supplier=sup, business_date=today,
            lots=[LotInput(number=f"LX-{idx:02d}", quantity=5, unit_cost=Decimal("1.50"), expiration_date=today + timedelta(days=10))],
        )
    qs = _search_products("Conserva")
    with CaptureQueriesContext(connection) as ctx2:
        found20 = list(qs)
    q_count_after = len(ctx2)
    sql, params = qs.query.sql_with_params()
    with connection.cursor() as cur:
        cur.execute("EXPLAIN (FORMAT JSON) " + sql, params)
        explain_plan = cur.fetchone()[0]
    add_case("PG07_query_invariance_and_pg_explain", q_count_before == q_count_after == 1 and len(found20) >= 20, {
        "queries_before": q_count_before, "queries_after_plus20": q_count_after,
        "found_count": len(found20), "top_node_type": explain_plan[0]["Plan"]["Node Type"],
    })

    # PG08: DEC-11-TOPE-EFECTIVO-FORM/C-03 PG CheckConstraints on sales_saledraftline
    d8 = SaleDraft.objects.create(cash_shift=shift, seller=seller, status=SaleDraft.Status.ACTIVE)
    pg_constraints = {}
    sql_ins = (
        "INSERT INTO sales_saledraftline "
        "(id, draft_id, product_id, quantity, unit_price, created_at, updated_at) "
        "VALUES (%s, %s, %s, %s, %s, NOW(), NOW())"
    )
    expected_cname = {
        "qty_zero": "sale_draft_line_quantity_gt_zero",
        "qty_1000000": "sale_draft_line_quantity_max",
        "price_zero": "sale_draft_line_unit_price_gt_zero",
    }
    for key, args in [
        ("qty_zero", (str(uuid.uuid4()), str(d8.pk), str(p_uni.pk), 0, Decimal("4.50"))),
        ("qty_1000000", (str(uuid.uuid4()), str(d8.pk), str(p_uni.pk), 1000000, Decimal("4.50"))),
        ("price_zero", (str(uuid.uuid4()), str(d8.pk), str(p_uni.pk), 1, Decimal("0.00"))),
    ]:
        try:
            with transaction.atomic():
                with connection.cursor() as cur:
                    cur.execute(sql_ins, args)
            pg_constraints[key] = "NO_ERROR"
        except IntegrityError as exc:
            pg_constraints[key] = str(exc).splitlines()[0]
    discard_active_draft(actor=seller)
    add_case(
        "PG08_dec11_c03_pg_check_constraints",
        all(expected_cname[k] in pg_constraints[k] for k in expected_cname),
        {"constraints": pg_constraints},
    )

    # PG09: DEC-12-ORDEN-LINEAS-RECIBO/C-04 Concurrent PG checkout with stale signature vs Admin price edit
    d9 = add_product_to_draft(actor=seller, product_id=p_uni.pk, quantity=2)
    sig9 = draft_signature(d9.pk, d9.lines.all())
    snap9 = product_edit_snapshot(p_uni)
    b9 = threading.Barrier(2)
    r9 = []

    def w_admin_price():
        try:
            connections.close_all()
            b9.wait(timeout=5)
            p_fresh = Product.objects.get(pk=p_uni.pk)
            update_product(
                actor=admin, product=p_fresh, name=p_fresh.name, barcode=p_fresh.barcode,
                sale_price=Decimal("8.00"), minimum_stock=p_fresh.minimum_stock,
                category=p_fresh.category, expected_snapshot=snap9, barcode_type=p_fresh.barcode_type,
            )
            r9.append("PRICE_8_00")
        except Exception as exc:
            r9.append("PRICE_ERR:" + str(exc))
        finally:
            connections.close_all()

    def w_checkout_stale():
        try:
            connections.close_all()
            # Ensure admin commits price first OR serialize deterministically to observe stale check on PG!
            b9.wait(timeout=5)
            time.sleep(0.05)
            checkout_sale(
                actor=seller, draft_id=d9.pk, cash_received=Decimal("20.00"),
                idempotency_key=uuid.uuid4(), expected_subtotal=Decimal("9.00"), expected_signature=sig9,
            )
            r9.append("CHECKOUT_OLD_OK")
        except ValidationError as exc:
            r9.append("CHECKOUT_REJECTED:" + " ".join(exc.messages))
        except Exception as exc:
            r9.append("CHECKOUT_ERR:" + str(exc))
        finally:
            connections.close_all()

    tp9 = threading.Thread(target=w_admin_price); tc9 = threading.Thread(target=w_checkout_stale)
    tp9.start(); tc9.start(); tp9.join(); tc9.join()
    sales_after_p9 = Sale.objects.count()
    discard_active_draft(actor=seller)
    close_cash_shift(actor=seller, counted_amount=Decimal("100.00"))
    add_case("PG09_dec12_c04_concurrent_price_vs_checkout_pg", sales_after_p9 == 0 and any(x.startswith("CHECKOUT_REJECTED:") for x in r9), {
        "outcomes": r9, "sales_created": sales_after_p9,
    })

    return {
        "pg_version": pg_version,
        "pg_db": pg_db,
        "total": len(cases),
        "passed": sum(1 for c in cases if c["ok"]),
        "failed": sum(1 for c in cases if not c["ok"]),
        "cases": cases,
    }


def main():
    if os.environ.get("AUDIT10B_PG_WORKER") == "1":
        res = run_worker_suite()
        print(json.dumps(res, ensure_ascii=False))
        raise SystemExit(0 if res["failed"] == 0 else 1)

    EV_DIR.mkdir(parents=True, exist_ok=True)
    db_before = file_sha256(OPERATIONAL_DB) if OPERATIONAL_DB.exists() else None
    stamp = datetime.now(dt_tz.utc).strftime("%Y%m%dT%H%M%SZ")
    pg_dir = RESULTS / "datos" / f"etapa10b-pg-{stamp}-{secrets.token_hex(4)}"
    pg_dir.mkdir(parents=True, exist_ok=False)
    port = free_port()
    try:
        start_ephemeral_pg(pg_dir, port)
        env = os.environ.copy()
        env.update(
            {
                "AUDIT10B_PG_WORKER": "1",
                "AUDIT10B_PG_PORT": str(port),
                "AUDIT10B_PG_DB": "audit10b_pg",
                "AUDIT10B_PG_SECRET": "pg10b-" + secrets.token_hex(32),
                "PYTHONPATH": str(HERE) + os.pathsep + str(PMV),
                "PYTHONUTF8": "1",
            }
        )
        r = subprocess.run(
            [str(PMV / ".venv" / "Scripts" / "python.exe"), str(Path(__file__).resolve())],
            env=env,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        db_after = file_sha256(OPERATIONAL_DB) if OPERATIONAL_DB.exists() else None
        out = {
            "timestamp_utc": datetime.now(dt_tz.utc).isoformat(),
            "exit_code": r.returncode,
            "operational_db_sha256_before": db_before,
            "operational_db_sha256_after": db_after,
            "operational_db_untouched": db_before == db_after,
            "stderr": (r.stderr or "").strip(),
        }
        try:
            out["worker"] = json.loads((r.stdout or "").strip().splitlines()[-1])
        except Exception:
            out["raw_stdout"] = r.stdout
        (EV_DIR / "pg-results.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if (r.returncode == 0 and db_before == db_after) else 1
    finally:
        stop_ephemeral_pg(pg_dir)
        shutil.rmtree(pg_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
