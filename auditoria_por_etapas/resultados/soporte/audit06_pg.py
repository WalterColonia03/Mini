"""Stage 06 real PostgreSQL 18.4 concurrency, locking, rollback, savepoint, and DB-trigger tests.
Runs in an ephemeral owned cluster (AUDIT06_OWNED) and never alters existing SQLite DBs.
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
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "auditoria_por_etapas/resultados"
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
CLUSTER = (Path(tempfile.gettempdir()) / ("audit06-pg-" + secrets.token_hex(12))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT06_OWNED"
MARK.write_text(STAMP, encoding="utf-8")
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(40)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit06_" + secrets.token_hex(5)
with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]

protected = [
    *(ROOT / "r1-pmv").glob("*.sqlite3"),
    *(RESULTS / "datos").rglob("*.sqlite3"),
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
    assert CLUSTER.parent == Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith("audit06-pg-")
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


started = False
configured = False
try:
    own()
    pg(
        "initdb",
        "-D",
        DBDIR,
        "-U",
        "audit06",
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
    from psycopg import sql

    conf = {"host": "127.0.0.1", "port": PORT, "user": "audit06", "password": PW}
    with psycopg.connect(**conf, dbname="postgres", autocommit=True) as conn:
        assert Path(conn.execute("SHOW data_directory").fetchone()[0]).resolve() == DBDIR
        report["version"] = conn.execute("SELECT version()").fetchone()[0]
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DBNAME)))

    sys.path.insert(0, str(ROOT / "r1-pmv"))
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
            "USER": "audit06",
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
    from django.db import IntegrityError, close_old_connections, connection, connections, transaction
    from django.test import Client
    from django.utils import timezone as tz
    from cash.models import CashRegister, CashShift
    from catalog.models import Category, Product
    from catalog.services import toggle_category_status, toggle_product_availability
    from identity.models import Account, Role
    from inventory.models import Lot
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        create_supplier,
        register_stock_entry,
        toggle_supplier_status,
    )
    from sales.models import SaleLine
    from sales.services import add_product_to_draft, checkout_sale

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

    pw_user = "PgAudit06#Pass123"
    admin = Account.objects.create_user("admin.pg06@test.invalid", pw_user, display_name="Admin PG06", role=admin_role)
    wh1 = Account.objects.create_user("wh1.pg06@test.invalid", pw_user, display_name="Almacen1 PG06", role=wh_role)
    wh2 = Account.objects.create_user("wh2.pg06@test.invalid", pw_user, display_name="Almacen2 PG06", role=wh_role)
    seller = Account.objects.create_user("seller.pg06@test.invalid", pw_user, display_name="Seller PG06", role=seller_role)
    reg = CashRegister.objects.create(code="CAJA-PG06")
    CashShift.objects.create(cash_register=reg, seller=seller, opening_amount=Decimal("100.00"))

    today = tz.localdate()
    future = today + timedelta(days=45)
    future2 = today + timedelta(days=90)
    cat_a = Category.objects.create(name="PG06 Cat A")

    # ── Case 1: Same-lot concurrent register_stock_entry + barrier race ──
    p_same = Product.objects.create(category=cat_a, name="PG Same Lot", barcode="775060000101", sale_price=Decimal("8.00"))
    confirm_initial_load(actor=wh1, product=p_same, lots=[LotInput("PG-BASE-1", 4, Decimal("2.0000"), future)])

    r1, rel1 = threading.Event(), threading.Event()

    def hold_same():
        close_old_connections()
        try:
            with transaction.atomic():
                register_stock_entry(actor=wh1, product=p_same, lots=[LotInput("PG-SAME-1", 4, Decimal("4.0000"), future)])
                r1.set()
                rel1.wait(timeout=8)
                return {"status": "committed"}
        finally:
            close_old_connections()

    def wait_same():
        close_old_connections()
        try:
            r1.wait(timeout=8)
            try:
                register_stock_entry(actor=wh2, product=p_same, lots=[LotInput("pg-same-1", 4, Decimal("6.0000"), future2)])
                return {"status": "unexpected_commit"}
            except ValidationError as exc:
                return {"status": "rejected", "messages": exc.messages}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        fh, fw = pool.submit(hold_same), pool.submit(wait_same)
        lock1 = observe_waiter(obs, "catalog_product")
        rel1.set()
        fh.result()
        wait_res1 = fw.result()

    # Barrier simultaneous race for same lot on fresh loaded product
    p_race = Product.objects.create(category=cat_a, name="PG Race Entry", barcode="775060000102", sale_price=Decimal("8.00"))
    confirm_initial_load(actor=wh1, product=p_race, lots=[LotInput("PG-INI-R", 4, Decimal("2.0000"), future)])
    bar1 = threading.Barrier(2, timeout=8)

    def race_same(actor_obj):
        close_old_connections()
        try:
            bar1.wait()
            register_stock_entry(actor=actor_obj, product=p_race, lots=[LotInput("PG-RACE-SAME", 4, Decimal("4.0000"), future)])
            return {"status": "committed"}
        except ValidationError as exc:
            return {"status": "rejected", "messages": exc.messages}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        fa, fb = pool.submit(race_same, wh1), pool.submit(race_same, wh2)
        race_res1 = [fa.result(), fb.result()]

    p_same.refresh_from_db()
    p_race.refresh_from_db()
    c1_ok = (
        lock1 is not None
        and wait_res1["status"] == "rejected"
        and any("ya existe para este producto" in m for m in wait_res1["messages"])
        and Lot.objects.filter(product=p_same).count() == 2
        and p_same.average_cost == Decimal("3.0000")
        and sorted(x["status"] for x in race_res1) == ["committed", "rejected"]
        and Lot.objects.filter(product=p_race).count() == 2
        and p_race.average_cost == Decimal("3.0000")
    )
    report["cases"].append(
        {"id": "pg_same_lot_race_and_lock", "ok": c1_ok, "checks": {"lock": lock1, "waiter": wait_res1, "barrier": race_res1}}
    )

    # ── Case 2: Concurrent DISTINCT lots serialize cleanly with zero lost update ──
    p_dist = Product.objects.create(category=cat_a, name="PG Distinct Lots", barcode="775060000201", sale_price=Decimal("10.00"))
    confirm_initial_load(actor=wh1, product=p_dist, lots=[LotInput("DIST-0", 10, Decimal("2.0000"), future)])
    r2, rel2 = threading.Event(), threading.Event()

    def hold_dist():
        close_old_connections()
        try:
            with transaction.atomic():
                register_stock_entry(actor=wh1, product=p_dist, lots=[LotInput("DIST-1", 10, Decimal("4.0000"), future)])
                r2.set()
                rel2.wait(timeout=8)
                return {"status": "committed"}
        finally:
            close_old_connections()

    def wait_dist():
        close_old_connections()
        try:
            r2.wait(timeout=8)
            register_stock_entry(actor=wh2, product=p_dist, lots=[LotInput("DIST-2", 20, Decimal("6.0000"), future2)])
            return {"status": "committed"}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        fh, fw = pool.submit(hold_dist), pool.submit(wait_dist)
        lock2 = observe_waiter(obs, "catalog_product")
        rel2.set()
        res_h2, res_w2 = fh.result(), fw.result()

    p_dist.refresh_from_db()
    c2_ok = (
        lock2 is not None
        and res_h2["status"] == "committed"
        and res_w2["status"] == "committed"
        and p_dist.physical_stock == 40
        and Lot.objects.filter(product=p_dist).count() == 3
        and p_dist.average_cost == Decimal("4.5000")
    )
    report["cases"].append(
        {"id": "pg_distinct_lots_serialized_no_lost_update", "ok": c2_ok, "checks": {"lock": lock2, "average_cost": str(p_dist.average_cost), "lots": Lot.objects.filter(product=p_dist).count()}}
    )

    # ── Case 3: Bidirectional register_stock_entry vs checkout_sale (zero deadlock, exact cost/FEFO) ──
    # Order A: entry_first -> checkout_sale waits -> captures updated average_cost 4.0000
    p_ea = Product.objects.create(category=cat_a, name="PG Entry Sale A", barcode="775060000301", sale_price=Decimal("10.00"))
    confirm_initial_load(actor=wh1, product=p_ea, lots=[LotInput("EA-0", 10, Decimal("2.0000"), future)])
    draft_ea = add_product_to_draft(actor=seller, product_id=p_ea.pk, quantity=2)

    r3a, rel3a = threading.Event(), threading.Event()
    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        def h3a():
            close_old_connections()
            try:
                with transaction.atomic():
                    register_stock_entry(actor=wh1, product=p_ea, lots=[LotInput("EA-1", 10, Decimal("6.0000"), future2)])
                    r3a.set()
                    rel3a.wait(timeout=8)
                return {"status": "committed"}
            finally:
                close_old_connections()

        def w3a():
            close_old_connections()
            try:
                r3a.wait(timeout=8)
                sale = checkout_sale(actor=seller, draft_id=draft_ea.pk, cash_received=Decimal("30.00"), idempotency_key=uuid.uuid4())
                return {"unit_cost": str(SaleLine.objects.get(sale=sale).unit_cost)}
            finally:
                close_old_connections()

        fh, fw = pool.submit(h3a), pool.submit(w3a)
        lock3a = observe_waiter(obs, "catalog_product")
        rel3a.set()
        fh.result()
        res3a = fw.result()

    # Order B: sale_first (sells 6 of 10 @ 2.0000, leaving 4) -> entry waits -> computes moving avg on 4 remaining + 4 @ 6.0000 == 4.0000 (if it had read stale 10, avg would be 3.1429!)
    p_eb = Product.objects.create(category=cat_a, name="PG Sale Entry B", barcode="775060000302", sale_price=Decimal("10.00"))
    confirm_initial_load(actor=wh1, product=p_eb, lots=[LotInput("EB-0", 10, Decimal("2.0000"), future)])
    draft_eb = add_product_to_draft(actor=seller, product_id=p_eb.pk, quantity=6)

    r3b, rel3b = threading.Event(), threading.Event()
    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        def h3b():
            close_old_connections()
            try:
                with transaction.atomic():
                    sale = checkout_sale(actor=seller, draft_id=draft_eb.pk, cash_received=Decimal("100.00"), idempotency_key=uuid.uuid4())
                    r3b.set()
                    rel3b.wait(timeout=8)
                    return {"unit_cost": str(SaleLine.objects.get(sale=sale).unit_cost)}
            finally:
                close_old_connections()

        def w3b():
            close_old_connections()
            try:
                r3b.wait(timeout=8)
                register_stock_entry(actor=wh1, product=p_eb, lots=[LotInput("EB-1", 4, Decimal("6.0000"), future2)])
                return {"status": "committed"}
            finally:
                close_old_connections()

        fh, fw = pool.submit(h3b), pool.submit(w3b)
        lock3b = observe_waiter(obs, "catalog_product")
        rel3b.set()
        res3b_sale = fh.result()
        res3b_entry = fw.result()

    p_eb.refresh_from_db()
    c3_ok = (
        lock3a is not None
        and res3a["unit_cost"] == "4.0000"
        and lock3b is not None
        and res3b_sale["unit_cost"] == "2.0000"
        and res3b_entry["status"] == "committed"
        and p_eb.average_cost == Decimal("4.0000")
        and p_eb.sellable_stock == 8
    )
    report["cases"].append(
        {"id": "pg_bidirectional_stock_entry_vs_checkout_sale", "ok": c3_ok, "checks": {"order_a": {"lock": lock3a, "res": res3a}, "order_b": {"lock": lock3b, "sale": res3b_sale, "final_avg": str(p_eb.average_cost)}}}
    )

    # ── Case 4: Bidirectional Category Suspension & Product Deactivation vs register_stock_entry ──
    cat_s1 = Category.objects.create(name="PG06 Cat Susp1")
    cat_s2 = Category.objects.create(name="PG06 Cat Susp2")
    p_cs1 = Product.objects.create(category=cat_s1, name="PG CS1", barcode="775060000401", sale_price=Decimal("4.00"))
    p_cs2 = Product.objects.create(category=cat_s2, name="PG CS2", barcode="775060000402", sale_price=Decimal("4.00"))
    confirm_initial_load(actor=wh1, product=p_cs1, lots=[LotInput("CS1-0", 3, Decimal("2.00"), future)])
    confirm_initial_load(actor=wh1, product=p_cs2, lots=[LotInput("CS2-0", 3, Decimal("2.00"), future)])

    r4a, rel4a = threading.Event(), threading.Event()
    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        def h4a():
            close_old_connections()
            try:
                with transaction.atomic():
                    toggle_category_status(actor=admin, category=cat_s1, is_active=False)
                    r4a.set()
                    rel4a.wait(timeout=8)
            finally:
                close_old_connections()

        def w4a():
            close_old_connections()
            try:
                r4a.wait(timeout=8)
                try:
                    register_stock_entry(actor=wh1, product=p_cs1, lots=[LotInput("CS1-1", 3, Decimal("4.00"), future)])
                    return {"status": "unexpected_commit"}
                except ValidationError as exc:
                    return {"status": "rejected", "messages": exc.messages}
            finally:
                close_old_connections()

        fa, fb = pool.submit(h4a), pool.submit(w4a)
        lock4a = observe_waiter(obs, "catalog_category")
        rel4a.set()
        fa.result()
        res4a = fb.result()

    p_pd = Product.objects.create(category=cat_a, name="PG PD1", barcode="775060000403", sale_price=Decimal("4.00"))
    confirm_initial_load(actor=wh1, product=p_pd, lots=[LotInput("PD-0", 3, Decimal("2.00"), future)])
    r4b, rel4b = threading.Event(), threading.Event()
    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        def h4b():
            close_old_connections()
            try:
                with transaction.atomic():
                    toggle_product_availability(actor=admin, product=p_pd, is_active=False)
                    r4b.set()
                    rel4b.wait(timeout=8)
            finally:
                close_old_connections()

        def w4b():
            close_old_connections()
            try:
                r4b.wait(timeout=8)
                try:
                    register_stock_entry(actor=wh1, product=p_pd, lots=[LotInput("PD-1", 3, Decimal("4.00"), future)])
                    return {"status": "unexpected_commit"}
                except ValidationError as exc:
                    return {"status": "rejected", "messages": exc.messages}
            finally:
                close_old_connections()

        fa, fb = pool.submit(h4b), pool.submit(w4b)
        lock4b = observe_waiter(obs, "catalog_product")
        rel4b.set()
        fa.result()
        res4b = fb.result()

    r4c, rel4c = threading.Event(), threading.Event()
    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        def h4c():
            close_old_connections()
            try:
                with transaction.atomic():
                    register_stock_entry(actor=wh1, product=p_cs2, lots=[LotInput("CS2-1", 3, Decimal("4.00"), future)])
                    r4c.set()
                    rel4c.wait(timeout=8)
            finally:
                close_old_connections()

        def w4c():
            close_old_connections()
            try:
                r4c.wait(timeout=8)
                cat = toggle_category_status(actor=admin, category=cat_s2, is_active=False)
                return {"is_active": cat.is_active}
            finally:
                close_old_connections()

        fa, fb = pool.submit(h4c), pool.submit(w4c)
        lock4c = observe_waiter(obs, "catalog_category")
        rel4c.set()
        fa.result()
        res4c = fb.result()

    c4_ok = (
        lock4a is not None
        and res4a["status"] == "rejected"
        and Lot.objects.filter(product=p_cs1).count() == 1
        and lock4b is not None
        and res4b["status"] == "rejected"
        and Lot.objects.filter(product=p_pd).count() == 1
        and lock4c is not None
        and not res4c["is_active"]
        and Lot.objects.filter(product=p_cs2).count() == 2
    )
    report["cases"].append(
        {"id": "pg_bidirectional_category_and_product_deactivation", "ok": c4_ok, "checks": {"cat_susp": res4a, "prod_deact": res4b, "entry_before_cat_susp": res4c}}
    )

    # ── Case 5: Concurrent Supplier Deactivation + ALMACENERO Revocation ──
    sup_race = create_supplier(actor=admin, name="PG06 Sup Race SAC", ruc="20606000091")
    p_sup = Product.objects.create(category=cat_a, name="PG Sup06", barcode="775060000501", sale_price=Decimal("4.50"))
    confirm_initial_load(actor=wh1, product=p_sup, lots=[LotInput("SUP-0", 4, Decimal("2.00"), future)])

    r5s, rel5s = threading.Event(), threading.Event()
    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        def h5s():
            close_old_connections()
            try:
                with transaction.atomic():
                    toggle_supplier_status(actor=admin, supplier=sup_race, is_active=False)
                    r5s.set()
                    rel5s.wait(timeout=8)
            finally:
                close_old_connections()

        def w5s():
            close_old_connections()
            try:
                r5s.wait(timeout=8)
                try:
                    register_stock_entry(actor=wh1, product=p_sup, supplier=sup_race, lots=[LotInput("SUP-1", 4, Decimal("4.00"), future)])
                    return {"status": "unexpected_commit"}
                except ValidationError as exc:
                    return {"status": "rejected", "messages": exc.messages}
            finally:
                close_old_connections()

        fa, fb = pool.submit(h5s), pool.submit(w5s)
        lock5s = observe_waiter(obs, "inventory_supplier")
        rel5s.set()
        fa.result()
        res5s = fb.result()

    wh_victim = Account.objects.create_user("wh.victim06@test.invalid", pw_user, display_name="Victim WH06", role=wh_role)
    r5a, rel5a = threading.Event(), threading.Event()
    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        def h5a():
            close_old_connections()
            try:
                with transaction.atomic():
                    Account.objects.select_for_update().filter(pk=wh_victim.pk).update(role=seller_role, is_active=False)
                    r5a.set()
                    rel5a.wait(timeout=8)
            finally:
                close_old_connections()

        def w5a():
            close_old_connections()
            try:
                r5a.wait(timeout=8)
                try:
                    register_stock_entry(actor=wh_victim, product=p_sup, lots=[LotInput("ACT-1", 4, Decimal("4.00"), future)])
                    return {"status": "unexpected_commit"}
                except PermissionDenied as exc:
                    return {"status": "denied", "message": str(exc)}
            finally:
                close_old_connections()

        fa, fb = pool.submit(h5a), pool.submit(w5a)
        lock5a = observe_waiter(obs, "identity_account")
        rel5a.set()
        fa.result()
        res5a = fb.result()

    c5_ok = (
        lock5s is not None
        and res5s["status"] == "rejected"
        and lock5a is not None
        and res5a["status"] == "denied"
        and Lot.objects.filter(product=p_sup).count() == 1
    )
    report["cases"].append(
        {"id": "pg_supplier_deactivation_and_warehouse_revocation", "ok": c5_ok, "checks": {"supplier": {"lock": lock5s, "res": res5s}, "actor": {"lock": lock5a, "res": res5a}}}
    )

    # ── Case 6: FIX06-02 savepoint IntegrityError + CT-ROLLBACK-01 + NUL ValidationError + Trigger 23514 on is_initial=False ──
    p_rb = Product.objects.create(category=cat_a, name="PG Rollback06", barcode="775060000601", sale_price=Decimal("6.00"))
    confirm_initial_load(actor=wh1, product=p_rb, lots=[LotInput("RB-INI", 4, Decimal("2.0000"), future)])

    with patch.object(Lot.objects, "bulk_create", side_effect=IntegrityError("colisión pg")):
        sp_caught = None
        try:
            with transaction.atomic():
                register_stock_entry(actor=wh1, product=p_rb, lots=[LotInput("RB-SP", 4, Decimal("5.0000"), future)])
        except ValidationError as exc:
            sp_caught = exc.messages

    orig_bulk = Lot.objects.bulk_create
    created_in_tx = {"called": False}

    def boom_after_insert(*args, **kwargs):
        res = orig_bulk(*args, **kwargs)
        created_in_tx["called"] = True
        raise RuntimeError("Simulated PG crash after Lot.bulk_create")

    rb_caught = False
    Lot.objects.bulk_create = boom_after_insert
    try:
        register_stock_entry(actor=wh1, product=p_rb, lots=[LotInput("RB-BOOM", 4, Decimal("8.0000"), future)])
    except RuntimeError:
        rb_caught = True
    finally:
        Lot.objects.bulk_create = orig_bulk

    nul_caught = None
    try:
        register_stock_entry(actor=wh1, product=p_rb, lots=[LotInput("L\x00PG06", 2, Decimal("3.00"), future)])
    except ValidationError as exc:
        nul_caught = exc.messages

    # Verify DB trigger 0006 protects received_at on subsequent lot (is_initial=False)
    sub_lot = Lot.objects.filter(product=p_same, is_initial=False).first()
    trigger_sqlstate = None
    try:
        with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute("UPDATE inventory_lot SET received_at = received_at - interval '1 day' WHERE id = %s", [str(sub_lot.pk)])
    except IntegrityError as exc:
        cause = getattr(exc, "__cause__", exc)
        trigger_sqlstate = getattr(cause, "sqlstate", None)

    p_rb.refresh_from_db()
    c6_ok = (
        sp_caught is not None
        and any("conflicto" in m for m in sp_caught)
        and created_in_tx["called"]
        and rb_caught
        and Lot.objects.filter(product=p_rb).count() == 1
        and p_rb.average_cost == Decimal("2.0000")
        and nul_caught is not None
        and sub_lot is not None
        and trigger_sqlstate == "23514"
    )
    report["cases"].append(
        {
            "id": "pg_fix06_02_savepoint_rollback_nul_and_trigger_23514",
            "ok": c6_ok,
            "checks": {
                "savepoint_caught": sp_caught,
                "rollback_called": created_in_tx["called"],
                "rollback_caught": rb_caught,
                "nul_guard": nul_caught,
                "trigger_sqlstate_on_subsequent_lot": trigger_sqlstate,
            },
        }
    )

    # ── Case 7: Threaded WSGI HTTP Double-Submit on /inventario/entrada/ + FIX06-01 empty POST ──
    p_http = Product.objects.create(category=cat_a, name="PG HTTP Entry", barcode="775060000701", sale_price=Decimal("8.00"))
    confirm_initial_load(actor=wh1, product=p_http, lots=[LotInput("HTTP-INI", 5, Decimal("2.0000"), future)])

    c_wh1, c_wh2 = Client(enforce_csrf_checks=True), Client(enforce_csrf_checks=True)
    c_wh1.force_login(wh1)
    c_wh2.force_login(wh2)
    tok1 = c_wh1.get("/inventario/entrada/").cookies["csrftoken"].value
    tok2 = c_wh2.get("/inventario/entrada/").cookies["csrftoken"].value

    empty_pg_resp = c_wh1.post("/inventario/entrada/", data={}, HTTP_X_CSRFTOKEN=tok1)
    empty_pg_body = empty_pg_resp.content.decode("utf-8", errors="replace")
    empty_pg_ok = (
        empty_pg_resp.status_code == 200
        and 'role="alert"' in empty_pg_body
        and "Seleccione un producto." in empty_pg_body
    )

    barrier_http = threading.Barrier(2, timeout=8)
    base_post = {
        "product": str(p_http.pk),
        "supplier": "",
        "lots-TOTAL_FORMS": "4",
        "lots-INITIAL_FORMS": "0",
        "lots-MIN_NUM_FORMS": "1",
        "lots-MAX_NUM_FORMS": "1000",
        "lots-0-number": "PG-HTTP-SUB",
        "lots-0-quantity": "5",
        "lots-0-unit_cost": "4.0000",
        "lots-0-expiration_date": future.isoformat(),
    }

    def http_submit(client_obj: Client, tok: str):
        close_old_connections()
        try:
            barrier_http.wait()
            resp = client_obj.post("/inventario/entrada/", {**base_post, "csrfmiddlewaretoken": tok})
            body = resp.content.decode() if resp.status_code == 200 else ""
            return {
                "status": resp.status_code,
                "location": resp.get("Location"),
                "has_dup_msg": "ya existe para este producto" in body,
                "has_alert": 'role="alert"' in body,
            }
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        fh1 = pool.submit(http_submit, c_wh1, tok1)
        fh2 = pool.submit(http_submit, c_wh2, tok2)
        http_results = [fh1.result(), fh2.result()]

    p_http.refresh_from_db()
    c7_ok = (
        empty_pg_ok
        and sorted(r["status"] for r in http_results) == [200, 302]
        and any(r["status"] == 200 and r["has_dup_msg"] for r in http_results)
        and Lot.objects.filter(product=p_http).count() == 2
        and p_http.average_cost == Decimal("3.0000")
    )
    report["cases"].append(
        {
            "id": "pg_http_double_submit_and_fix06_01_empty_post",
            "ok": c7_ok,
            "checks": {
                "empty_pg_ok": empty_pg_ok,
                "http_results": http_results,
                "final_lots": Lot.objects.filter(product=p_http).count(),
                "final_avg": str(p_http.average_cost),
            },
        }
    )

except Exception as exc:
    report["error"] = {"type": type(exc).__name__, "message": str(exc).replace(PW, "[REDACTED]")[:800]}
finally:
    if configured:
        connections.close_all()
    if started:
        own()
        pg("pg_ctl", "-D", DBDIR, "-m", "fast", "-w", "stop")
    with socket.socket() as s:
        report["port_closed"] = s.connect_ex(("127.0.0.1", PORT)) != 0
    report["protected_unchanged"] = {str(p.relative_to(ROOT)): state_hash(p) == hashes[str(p.relative_to(ROOT))] for p in protected}
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    out = RESULTS / "evidencias" / ("06-postgresql-" + STAMP + ".json")
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

