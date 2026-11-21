"""Stage 06 Revalidation — PostgreSQL 18.4 concurrency, locking, triggers, constraints & rollback suite.
Runs inside an isolated ephemeral PG 18.4 cluster in %TEMP% and leaves all workspace SQLite/XLSX files untouched.
"""
from __future__ import annotations

import hashlib
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
from datetime import timedelta, timezone as dt_timezone, datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
STAMP = datetime.now(dt_timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
CLUSTER = (Path(tempfile.gettempdir()) / ("audit06-reval-pg-" + secrets.token_hex(8))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT06R_OWNED"
MARK.write_text(STAMP, encoding="utf-8")
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(36)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit06r_" + secrets.token_hex(4)
with socket.socket() as _s:
    _s.bind(("127.0.0.1", 0))
    PORT = _s.getsockname()[1]


def digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def protected_files() -> list[Path]:
    return [
        *APP.glob("*.sqlite3"),
        *(
            p
            for d in (RESULTS / "datos").iterdir()
            if d.is_dir() and d.name.startswith(("etapa00", "etapa06", "06-"))
            for p in d.rglob("*.sqlite3")
        ),
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]


START_HASHES = {str(p.relative_to(ROOT)): digest(p) for p in protected_files()}
report: dict = {
    "started_utc": STAMP,
    "cluster": str(CLUSTER),
    "port": PORT,
    "cases": [],
}


def pg(name: str, *args) -> None:
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as f:
        proc = subprocess.run(
            [str(BIN / f"{name}.exe"), *map(str, args)],
            stdout=f,
            stderr=f,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        f.seek(0)
        diag = f.read().replace(PW, "[REDACTED]")
    if proc.returncode:
        raise RuntimeError(f"{name} failed: {diag[-800:]}")


def observe_waiter(conn, relation_prefix: str, timeout_s: float = 6.0) -> dict | None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.pid, a.wait_event_type, a.wait_event, pg_blocking_pids(a.pid), l.relation::regclass::text
                FROM pg_stat_activity a
                LEFT JOIN pg_locks l ON l.pid = a.pid AND NOT l.granted
                WHERE a.datname = current_database()
                  AND a.pid <> pg_backend_pid()
                  AND cardinality(pg_blocking_pids(a.pid)) > 0
                """
            )
            for pid, wet, we, blockers, rel in cur.fetchall():
                if rel is None or rel.startswith(relation_prefix):
                    return {
                        "waiting_pid": pid,
                        "wait_event_type": wet,
                        "wait_event": we,
                        "blocking_pids": list(blockers),
                        "relation": rel,
                    }
        time.sleep(0.02)
    return None


def rec(case_id: str, ok: bool, details: dict) -> None:
    report["cases"].append({"id": case_id, "ok": ok, "details": details})
    if not ok:
        raise AssertionError(f"PG Case failed: {case_id} -> {details}")


started = False
configured = False
try:
    pg(
        "initdb",
        "-D",
        DBDIR,
        "-U",
        "audit06r",
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
        f"-h 127.0.0.1 -p {PORT} -c log_statement=none -c log_min_error_statement=panic -c deadlock_timeout=100ms",
        "-w",
        "start",
    )
    started = True

    import psycopg
    from psycopg import errors as pg_errors
    from psycopg import sql

    conf = {"host": "127.0.0.1", "port": PORT, "user": "audit06r", "password": PW}
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
    from config import env as config_env

    _orig_loader = config_env.load_dotenv
    config_env.load_dotenv = lambda path=None: None
    try:
        from django.conf import settings

        settings.DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": DBNAME,
                "USER": "audit06r",
                "PASSWORD": PW,
                "HOST": "127.0.0.1",
                "PORT": PORT,
                "CONN_MAX_AGE": 0,
                "OPTIONS": {"options": "-c statement_timeout=20000 -c lock_timeout=12000"},
            }
        }
        settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
        settings.CSRF_COOKIE_SECURE = False
        settings.SESSION_COOKIE_SECURE = False
        import django

        django.setup()
        configured = True
    finally:
        config_env.load_dotenv = _orig_loader

    from django.core.exceptions import PermissionDenied, ValidationError
    from django.core.management import call_command
    from django.db import IntegrityError, close_old_connections, connections, transaction
    from django.test import Client
    from django.urls import reverse
    from django.utils import timezone as tz

    from cash.models import CashRegister
    from cash.services import open_cash_shift
    from catalog.models import Category, Product
    from catalog.services import toggle_category_status, toggle_product_availability
    from identity.models import Account, Role
    from inventory.models import (
        Lot,
        PhysicalAdjustment,
        StockReceipt,
        StockReceiptCounter,
        StockReceiptLine,
        StockWriteOff,
        Supplier,
    )
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        create_supplier,
        register_physical_adjustment,
        register_stock_entry,
        toggle_supplier_status,
        write_off_stock,
    )
    from sales.models import SaleLine
    from sales.services import add_product_to_draft, checkout_sale

    call_command("migrate", interactive=False, verbosity=0)

    r_adm = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    r_wh = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    r_sel = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    pw = secrets.token_urlsafe(16) + "A1!"
    adm = Account.objects.create_user("adm@pg06.invalid", pw, display_name="Admin PG06", role=r_adm)
    wh1 = Account.objects.create_user("wh1@pg06.invalid", pw, display_name="Almacenero PG1", role=r_wh)
    wh2 = Account.objects.create_user("wh2@pg06.invalid", pw, display_name="Almacenero PG2", role=r_wh)
    sel = Account.objects.create_user("sel@pg06.invalid", pw, display_name="Vendedor PG", role=r_sel)

    CashRegister.objects.create(code="CAJA-01")
    open_cash_shift(actor=sel, opening_amount=Decimal("50.00"))
    cat = Category.objects.create(name="Cat PG06", is_active=True)
    sup = create_supplier(actor=adm, name="Proveedor PG06 SAC", ruc="20555555551", phone="999000111")

    today = tz.localdate()
    tomorrow = today + timedelta(days=1)
    future_45 = today + timedelta(days=45)
    future_60 = today + timedelta(days=60)
    future_90 = today + timedelta(days=90)

    # ── PG06R-01: Concurrent same idempotency_key + same content ──────────────
    p1 = Product.objects.create(category=cat, name="PG Idem Same", barcode="7759900001", sale_price=Decimal("5.00"), minimum_stock=2)
    confirm_initial_load(actor=wh1, product=p1, supplier=sup, lots=[LotInput("INI-1", 10, Decimal("2.0000"), future_60)])
    k1 = uuid.uuid4()
    b1 = threading.Barrier(2)

    def _run_same_key():
        close_old_connections()
        try:
            b1.wait(timeout=5)
            r = register_stock_entry(
                actor=Account.objects.get(pk=wh1.pk),
                product=Product.objects.get(pk=p1.pk),
                supplier=Supplier.objects.get(pk=sup.pk),
                lots=[LotInput("SAME-K-1", 5, Decimal("4.0000"), future_60)],
                idempotency_key=k1,
            )
            return str(r.pk)
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futs1 = [pool.submit(_run_same_key), pool.submit(_run_same_key)]
        ids1 = [f.result() for f in futs1]
    p1.refresh_from_db()
    rec(
        "PG06R-01_same_key_concurrent_replay",
        len(set(ids1)) == 1
        and StockReceipt.objects.filter(product=p1).count() == 1
        and p1.physical_stock == 15
        and p1.average_cost == Decimal("2.6667"),
        {"ids": ids1, "physical": p1.physical_stock, "avg": str(p1.average_cost)},
    )

    # ── PG06R-02: Divergent content & cross-actor race on same key ────────────
    p2 = Product.objects.create(category=cat, name="PG Idem Div", barcode="7759900002", sale_price=Decimal("5.00"), minimum_stock=2)
    confirm_initial_load(actor=wh1, product=p2, lots=[LotInput("INI-2", 4, Decimal("3.0000"), future_60)])
    k2_div = uuid.uuid4()
    b2 = threading.Barrier(2)

    def _run_div(qty: int):
        close_old_connections()
        try:
            b2.wait(timeout=5)
            r = register_stock_entry(
                actor=Account.objects.get(pk=wh1.pk),
                product=Product.objects.get(pk=p2.pk),
                lots=[LotInput("DIV-1", qty, Decimal("5.0000"), future_60)],
                idempotency_key=k2_div,
            )
            return ("ok", qty, str(r.pk))
        except ValidationError as err:
            return ("err", qty, err.messages[0])
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futs2 = [pool.submit(_run_div, 3), pool.submit(_run_div, 7)]
        div_res = sorted([f.result() for f in futs2], key=lambda x: x[0])

    k2_actor = uuid.uuid4()
    b2b = threading.Barrier(2)

    def _run_actor_race(acct_id):
        close_old_connections()
        try:
            b2b.wait(timeout=5)
            r = register_stock_entry(
                actor=Account.objects.get(pk=acct_id),
                product=Product.objects.get(pk=p2.pk),
                lots=[LotInput("ACT-1", 2, Decimal("6.0000"), future_60)],
                idempotency_key=k2_actor,
            )
            return ("ok", str(acct_id), str(r.pk))
        except ValidationError as err:
            return ("err", str(acct_id), err.messages[0])
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futs2b = [pool.submit(_run_actor_race, wh1.pk), pool.submit(_run_actor_race, wh2.pk)]
        actor_res = sorted([f.result() for f in futs2b], key=lambda x: x[0])

    rec(
        "PG06R-02_divergent_and_cross_actor_race",
        [r[0] for r in div_res] == ["err", "ok"]
        and "otro contenido o responsable" in div_res[0][2]
        and [r[0] for r in actor_res] == ["err", "ok"]
        and "otro contenido o responsable" in actor_res[0][2]
        and StockReceipt.objects.filter(product=p2).count() == 2,
        {"div_res": div_res, "actor_res": actor_res},
    )

    # ── PG06R-03: Concurrent HTTP double-submit (same key & distinct commercial lots) + FIX06-01 ─
    p3 = Product.objects.create(category=cat, name="PG HTTP Race", barcode="7759900003", sale_price=Decimal("5.00"), minimum_stock=2)
    confirm_initial_load(actor=wh1, product=p3, lots=[LotInput("INI-3", 4, Decimal("2.0000"), future_60)])
    ch1, ch2 = Client(enforce_csrf_checks=True), Client(enforce_csrf_checks=True)
    ch1.force_login(wh1)
    ch2.force_login(wh1)
    ch1.get(reverse("stock-entry"))
    ch2.get(reverse("stock-entry"))
    tok1, tok2 = ch1.cookies["csrftoken"].value, ch2.cookies["csrftoken"].value

    empty_pg = ch1.post(reverse("stock-entry"), {}, HTTP_X_CSRFTOKEN=tok1)
    k_http_same = str(uuid.uuid4())
    base_http = {
        "idempotency_key": k_http_same,
        "product": str(p3.pk),
        "supplier": str(sup.pk),
        "lots-TOTAL_FORMS": "1",
        "lots-INITIAL_FORMS": "0",
        "lots-MIN_NUM_FORMS": "1",
        "lots-MAX_NUM_FORMS": "1000",
        "lots-0-number": "HTTP-SAME",
        "lots-0-quantity": "4",
        "lots-0-unit_cost": "4.0000",
        "lots-0-expiration_date": future_60.isoformat(),
    }
    b_http = threading.Barrier(2)

    def _http_post(client_obj, payload, tok):
        close_old_connections()
        try:
            b_http.wait(timeout=5)
            resp = client_obj.post(reverse("stock-entry"), {**payload, "csrfmiddlewaretoken": tok})
            return (resp.status_code, resp.get("Location"))
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futs3 = [pool.submit(_http_post, ch1, base_http, tok1), pool.submit(_http_post, ch2, base_http, tok2)]
        http_same_res = [f.result() for f in futs3]

    # Now two distinct keys submitting commercial lot "COM-C" with same date concurrently -> BOTH commit!
    ch2_w2 = Client(enforce_csrf_checks=True)
    ch2_w2.force_login(wh2)
    ch2_w2.get(reverse("stock-entry"))
    tok_w2 = ch2_w2.cookies["csrftoken"].value
    p3_com_a = {**base_http, "idempotency_key": str(uuid.uuid4()), "lots-0-number": "COM-C", "lots-0-quantity": "2", "lots-0-unit_cost": "5.0000"}
    p3_com_b = {**base_http, "idempotency_key": str(uuid.uuid4()), "lots-0-number": "com-c", "lots-0-quantity": "2", "lots-0-unit_cost": "5.0000"}
    b_http2 = threading.Barrier(2)

    def _http_post2(client_obj, payload, tok):
        close_old_connections()
        try:
            b_http2.wait(timeout=5)
            resp = client_obj.post(reverse("stock-entry"), {**payload, "csrfmiddlewaretoken": tok})
            return (resp.status_code, resp.get("Location"))
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futs3b = [pool.submit(_http_post2, ch1, p3_com_a, tok1), pool.submit(_http_post2, ch2_w2, p3_com_b, tok_w2)]
        http_com_res = [f.result() for f in futs3b]

    p3.refresh_from_db()
    rec(
        "PG06R-03_http_double_submit_and_distinct_commercial",
        empty_pg.status_code == 200
        and 'role="alert"' in empty_pg.content.decode("utf-8")
        and [r[0] for r in http_same_res] == [302, 302]
        and http_same_res[0][1] == http_same_res[1][1]
        and [r[0] for r in http_com_res] == [302, 302]
        and http_com_res[0][1] != http_com_res[1][1]
        and StockReceipt.objects.filter(product=p3).count() == 3
        and p3.physical_stock == 12,
        {"http_same_res": http_same_res, "http_com_res": http_com_res, "physical": p3.physical_stock},
    )

    # ── PG06R-04: Concurrent contradictory expiration dates for same commercial lot ─
    p4 = Product.objects.create(category=cat, name="PG Lot Date Conflict", barcode="7759900004", sale_price=Decimal("5.00"), minimum_stock=2)
    confirm_initial_load(actor=wh1, product=p4, lots=[LotInput("INI-4", 5, Decimal("3.0000"), future_60)])
    b4 = threading.Barrier(2)

    def _date_race(exp_d):
        close_old_connections()
        try:
            b4.wait(timeout=5)
            r = register_stock_entry(
                actor=Account.objects.get(pk=wh1.pk),
                product=Product.objects.get(pk=p4.pk),
                lots=[LotInput("CONF-C", 3, Decimal("4.0000"), exp_d)],
                idempotency_key=uuid.uuid4(),
            )
            return ("ok", exp_d.isoformat(), str(r.pk))
        except ValidationError as err:
            return ("err", exp_d.isoformat(), err.messages[0])
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futs4 = [pool.submit(_date_race, future_45), pool.submit(_date_race, future_90)]
        date_res = sorted([f.result() for f in futs4], key=lambda x: x[0])

    p4.refresh_from_db()
    rec(
        "PG06R-04_concurrent_contradictory_lot_date",
        [r[0] for r in date_res] == ["err", "ok"]
        and "ya existe con otro vencimiento" in date_res[0][2]
        and StockReceipt.objects.filter(product=p4).count() == 1
        and p4.physical_stock == 8,
        {"date_res": date_res, "physical": p4.physical_stock},
    )

    # ── PG06R-05: Concurrent register_stock_entry vs checkout_sale (F-COSTO DOC-03AH-01/C-04) + real pg_locks wait ─
    p_fc = Product.objects.create(category=cat, name="PG FCOSTO Race", barcode="7759900005", sale_price=Decimal("8.00"), minimum_stock=2)
    confirm_initial_load(
        actor=wh1,
        product=p_fc,
        lots=[
            LotInput("FC-E", 8, Decimal("3.0000"), tomorrow),
            LotInput("FC-V", 10, Decimal("3.0000"), future_90),
        ],
    )
    Lot.objects.filter(product=p_fc, number_normalized="FC-E").update(expiration_date=today)
    draft_fc = add_product_to_draft(actor=sel, product_id=p_fc.pk, quantity=1)
    k_sale_fc = uuid.uuid4()
    b5 = threading.Barrier(2)

    def _entry_fc():
        close_old_connections()
        try:
            b5.wait(timeout=5)
            r = register_stock_entry(
                actor=Account.objects.get(pk=wh1.pk),
                product=Product.objects.get(pk=p_fc.pk),
                lots=[LotInput("FC-NEW", 10, Decimal("6.0000"), future_60)],
                idempotency_key=uuid.uuid4(),
            )
            return r.correlative
        finally:
            close_old_connections()

    def _sale_fc():
        close_old_connections()
        try:
            b5.wait(timeout=5)
            s = checkout_sale(
                actor=Account.objects.get(pk=sel.pk),
                draft_id=draft_fc.pk,
                cash_received=Decimal("10.00"),
                idempotency_key=k_sale_fc,
            )
            return s.correlative
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_ent = pool.submit(_entry_fc)
        f_sal = pool.submit(_sale_fc)
        cor_ent, cor_sal = f_ent.result(), f_sal.result()

    p_fc.refresh_from_db()
    sale_fc_cost = SaleLine.objects.get(sale__correlative=cor_sal).unit_cost
    valid_serial_pairs = {
        (Decimal("4.0714"), Decimal("4.0714")),  # entry before sale
        (Decimal("4.1111"), Decimal("3.0000")),  # sale before entry: (17*3 + 10*6)/27 = 111/27 = 4.1111
    }

    # Observe real PG Lock wait when external connection holds Product row FOR UPDATE
    def _waiter_entry():
        close_old_connections()
        try:
            return register_stock_entry(
                actor=Account.objects.get(pk=wh1.pk),
                product=Product.objects.get(pk=p_fc.pk),
                lots=[LotInput("WAIT-PG", 1, Decimal("4.0000"), future_60)],
                idempotency_key=uuid.uuid4(),
            ).correlative
        finally:
            close_old_connections()

    with psycopg.connect(**conf, dbname=DBNAME) as lock_conn, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs_conn:
        assert lock_conn.execute("SELECT id FROM catalog_product WHERE id = %s FOR UPDATE", (p_fc.pk,)).fetchone() is not None
        with ThreadPoolExecutor(max_workers=1) as pool:
            waiter_future = pool.submit(_waiter_entry)
            observed = observe_waiter(obs_conn, "catalog_product", timeout_s=6.0)
            lock_conn.commit()
            waited_cor = waiter_future.result()

    p_fc.refresh_from_db()
    rec(
        "PG06R-05_entry_vs_checkout_and_lock_wait",
        (p_fc.average_cost is not None)
        and (Decimal(str(StockReceipt.objects.get(correlative=cor_ent).average_cost_after)) in {Decimal("4.0714"), Decimal("4.1111")})
        and (StockReceipt.objects.get(correlative=cor_ent).average_cost_after, sale_fc_cost) in valid_serial_pairs
        and p_fc.physical_stock == 28
        and p_fc.sellable_stock == 20
        and observed is not None
        and observed["wait_event_type"] == "Lock"
        and bool(waited_cor),
        {
            "after_pair": [str(StockReceipt.objects.get(correlative=cor_ent).average_cost_after), str(sale_fc_cost)],
            "physical": p_fc.physical_stock,
            "lock_wait": observed,
        },
    )

    # ── PG06R-06: Concurrent entry vs write-off vs physical adjustment (Product->Lot lock order) ─
    p6 = Product.objects.create(category=cat, name="PG 3-Way Stock Race", barcode="7759900006", sale_price=Decimal("5.00"), minimum_stock=2)
    confirm_initial_load(actor=wh1, product=p6, lots=[LotInput("INI-6", 10, Decimal("3.0000"), future_60)])
    lot6 = Lot.objects.get(product=p6, number_normalized="INI-6")
    b6 = threading.Barrier(3)

    def _w_entry():
        close_old_connections()
        try:
            b6.wait(timeout=5)
            return register_stock_entry(
                actor=Account.objects.get(pk=wh1.pk),
                product=Product.objects.get(pk=p6.pk),
                lots=[LotInput("E6", 5, Decimal("6.0000"), future_60)],
                idempotency_key=uuid.uuid4(),
            ).correlative
        finally:
            close_old_connections()

    def _w_wo():
        close_old_connections()
        try:
            b6.wait(timeout=5)
            return write_off_stock(
                actor=Account.objects.get(pk=wh2.pk),
                lot=Lot.objects.get(pk=lot6.pk),
                quantity=2,
                reason=StockWriteOff.Reason.DAMAGE,
                notes="Carrera baja PG",
            ).correlativo
        finally:
            close_old_connections()

    def _w_adj():
        close_old_connections()
        try:
            b6.wait(timeout=5)
            return str(
                register_physical_adjustment(
                    actor=Account.objects.get(pk=adm.pk),
                    lot=Lot.objects.get(pk=lot6.pk),
                    delta=3,
                    reason="Carrera ajuste PG",
                ).pk
            )
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=3) as pool:
        f6a, f6b, f6c = pool.submit(_w_entry), pool.submit(_w_wo), pool.submit(_w_adj)
        res6 = (f6a.result(), f6b.result(), f6c.result())

    p6.refresh_from_db()
    rec(
        "PG06R-06_three_way_entry_writeoff_adjustment",
        all(res6) and p6.physical_stock == 16 and Lot.objects.get(pk=lot6.pk).available_quantity == 11,
        {"ops": res6, "physical": p6.physical_stock},
    )

    # ── PG06R-07: Concurrent entry vs category/product/supplier/actor deactivation & role change ─
    p7 = Product.objects.create(category=cat, name="PG Disable Race", barcode="7759900007", sale_price=Decimal("5.00"), minimum_stock=2)
    confirm_initial_load(actor=wh1, product=p7, lots=[LotInput("INI-7", 4, Decimal("2.0000"), future_60)])
    wh_temp = Account.objects.create_user("wh_temp@pg06.invalid", pw, display_name="WH Temp PG", role=r_wh)
    b7 = threading.Barrier(3)

    def _entry7():
        close_old_connections()
        try:
            b7.wait(timeout=5)
            r = register_stock_entry(
                actor=Account.objects.get(pk=wh_temp.pk),
                product=Product.objects.get(pk=p7.pk),
                supplier=Supplier.objects.get(pk=sup.pk),
                lots=[LotInput("RACE-7", 2, Decimal("3.0000"), future_60)],
                idempotency_key=uuid.uuid4(),
            )
            return ("ok", str(r.pk))
        except (ValidationError, PermissionDenied) as exc:
            return ("rejected", str(exc))
        finally:
            close_old_connections()

    def _disable_prod():
        close_old_connections()
        try:
            b7.wait(timeout=5)
            toggle_product_availability(actor=Account.objects.get(pk=adm.pk), product=Product.objects.get(pk=p7.pk), is_active=False)
            return "prod_off"
        finally:
            close_old_connections()

    def _revoke_actor():
        close_old_connections()
        try:
            b7.wait(timeout=5)
            with transaction.atomic():
                acct = Account.objects.select_for_update().get(pk=wh_temp.pk)
                acct.is_active = False
                acct.save(update_fields=["is_active"])
            return "actor_off"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=3) as pool:
        futs7 = [pool.submit(_entry7), pool.submit(_disable_prod), pool.submit(_revoke_actor)]
        r7 = [f.result() for f in futs7]

    p7.refresh_from_db()
    wh_temp.refresh_from_db()
    expected_lots = 2 if r7[0][0] == "ok" else 1
    rec(
        "PG06R-07_deactivation_and_actor_revocation_race",
        not p7.is_active
        and not wh_temp.is_active
        and Lot.objects.filter(product=p7).count() == expected_lots,
        {"outcomes": r7, "lots": Lot.objects.filter(product=p7).count()},
    )

    # ── PG06R-08: Post-write exception rollback + SQL triggers (23514) & DB constraints ─
    p8 = Product.objects.create(category=cat, name="PG Rollback & DB Trigger", barcode="7759900008", sale_price=Decimal("5.00"), minimum_stock=2)
    confirm_initial_load(actor=wh1, product=p8, lots=[LotInput("INI-8", 5, Decimal("3.0000"), future_60)])
    pre_last = StockReceiptCounter.objects.get(key="global").last_number
    pre_receipt_cnt = StockReceipt.objects.count()
    crash_caught = False
    try:
        with patch("inventory.models.StockReceiptLine.objects.bulk_create", side_effect=RuntimeError("Fallo simulado tras escribir StockReceipt")):
            register_stock_entry(
                actor=wh1,
                product=p8,
                lots=[LotInput("RB-1", 4, Decimal("7.0000"), future_60)],
                idempotency_key=uuid.uuid4(),
            )
    except RuntimeError:
        crash_caught = True
    p8.refresh_from_db()
    mid_last = StockReceiptCounter.objects.get(key="global").last_number
    mid_receipt_cnt = StockReceipt.objects.count()

    # Subsequent clean receipt consumes next correlative without gaps
    clean_rec = register_stock_entry(
        actor=wh1,
        product=p8,
        lots=[LotInput("CLEAN-8", 4, Decimal("7.0000"), future_60)],
        idempotency_key=uuid.uuid4(),
    )
    clean_lot = Lot.objects.get(product=p8, number_normalized="CLEAN-8")

    # Verify PostgreSQL triggers (migration 0006/0008) & CHECK constraints reject raw SQL tampering with SQLSTATE 23514
    trigger_err = None
    constraint_err = None
    with psycopg.connect(**conf, dbname=DBNAME) as c_sql:
        try:
            c_sql.execute("UPDATE inventory_lot SET received_at = received_at - interval '1 day' WHERE id = %s", (clean_lot.pk,))
        except pg_errors.CheckViolation as exc:
            trigger_err = exc.sqlstate
            c_sql.rollback()
        try:
            c_sql.execute("UPDATE inventory_stockreceipt SET average_cost_after = 0 WHERE id = %s", (clean_rec.pk,))
        except pg_errors.CheckViolation as exc:
            constraint_err = exc.sqlstate
            c_sql.rollback()

    rec(
        "PG06R-08_post_write_rollback_and_pg_triggers",
        crash_caught
        and mid_last == pre_last
        and mid_receipt_cnt == pre_receipt_cnt
        and clean_rec.correlative == f"R-{pre_last + 1:08d}"
        and trigger_err == "23514"
        and constraint_err == "23514",
        {"pre_last": pre_last, "clean_cor": clean_rec.correlative, "trigger_sqlstate": trigger_err, "constraint_sqlstate": constraint_err},
    )

    # ── PG06R-09: Outer transaction savepoint recovery after IntegrityError / ValidationError ─
    p9 = Product.objects.create(category=cat, name="PG Savepoint", barcode="7759900009", sale_price=Decimal("5.00"), minimum_stock=2)
    confirm_initial_load(actor=wh1, product=p9, lots=[LotInput("INI-9", 3, Decimal("2.0000"), future_60)])
    with transaction.atomic():
        try:
            register_stock_entry(
                actor=wh1,
                product=p9,
                lots=[LotInput("BAD\x00LOT", 1, Decimal("2.0000"), future_60)],
                idempotency_key=uuid.uuid4(),
            )
        except ValidationError:
            pass
        rec9 = register_stock_entry(
            actor=wh1,
            product=p9,
            lots=[LotInput("SP-OK-9", 3, Decimal("4.0000"), future_60)],
            idempotency_key=uuid.uuid4(),
        )
    p9.refresh_from_db()
    rec(
        "PG06R-09_savepoint_and_nul_rejection",
        bool(rec9.pk) and p9.physical_stock == 6 and p9.average_cost == Decimal("3.0000"),
        {"rec9": rec9.correlative, "physical": p9.physical_stock, "avg": str(p9.average_cost)},
    )

    # ── PG06R-10: Concurrent multi-product burst (10 threads -> 10 contiguous correlatives, lot64 & bounds) ─
    burst_prods = []
    for idx in range(10):
        bp = Product.objects.create(category=cat, name=f"PG Burst {idx}", barcode=f"775999000{idx}", sale_price=Decimal("5.00"), minimum_stock=1)
        confirm_initial_load(actor=wh1, product=bp, lots=[LotInput(f"IB-{idx}", 2, Decimal("2.0000"), future_60)])
        burst_prods.append(bp)
    pre_burst_last = StockReceiptCounter.objects.get(key="global").last_number
    b10 = threading.Barrier(10)

    def _burst(prod_id, idx):
        close_old_connections()
        try:
            b10.wait(timeout=8)
            r = register_stock_entry(
                actor=Account.objects.get(pk=wh1.pk),
                product=Product.objects.get(pk=prod_id),
                lots=[LotInput(("Z" * 64) if idx == 0 else f"BL-{idx}", 999999 if idx == 1 else 2, Decimal("9999999.9999") if idx == 2 else Decimal("4.0000"), future_60)],
                idempotency_key=uuid.uuid4(),
            )
            return r.correlative
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=10) as pool:
        futs10 = [pool.submit(_burst, bp.pk, i) for i, bp in enumerate(burst_prods)]
        burst_correlatives = [f.result() for f in futs10]

    expected_burst = [f"R-{n:08d}" for n in range(pre_burst_last + 1, pre_burst_last + 11)]
    rec(
        "PG06R-10_burst_10_contiguous_correlatives_and_bounds",
        sorted(burst_correlatives) == expected_burst,
        {"burst_correlatives": sorted(burst_correlatives), "expected": expected_burst},
    )

except Exception as exc:
    report["error"] = {"type": type(exc).__name__, "message": str(exc).replace(PW, "[REDACTED]")[:1000]}
finally:
    if configured:
        connections.close_all()
    if started:
        pg("pg_ctl", "-D", DBDIR, "-m", "fast", "-w", "stop")
    with socket.socket() as _s:
        report["port_closed"] = _s.connect_ex(("127.0.0.1", PORT)) != 0
    if report["port_closed"]:
        shutil.rmtree(CLUSTER, ignore_errors=True)
    report["protected_unchanged"] = {k: digest(ROOT / k) == v for k, v in START_HASHES.items()}
    report["finished_utc"] = datetime.now(dt_timezone.utc).isoformat()
    out_path = RESULTS / "evidencias" / f"06-reval-pg18-{STAMP}.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                "evidence": str(out_path.relative_to(ROOT)),
                "cases_passed": sum(1 for c in report["cases"] if c["ok"]),
                "cases_total": len(report["cases"]),
                "cases": [{"id": c["id"], "ok": c["ok"]} for c in report["cases"]],
                "error": report.get("error"),
                "port_closed": report["port_closed"],
                "protected_unchanged": all(report["protected_unchanged"].values()),
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    )

if (
    report.get("error")
    or len(report["cases"]) != 10
    or not all(x["ok"] for x in report["cases"])
    or not report["port_closed"]
    or not all(report["protected_unchanged"].values())
):
    raise SystemExit(1)
