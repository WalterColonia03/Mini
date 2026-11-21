"""Stage 05 real PostgreSQL 18.4 concurrency, locking, rollback, and DB-trigger tests.
Runs in an ephemeral owned cluster (AUDIT05_OWNED) and never alters existing SQLite DBs.
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
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "auditoria_por_etapas/resultados"
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
CLUSTER = (Path(tempfile.gettempdir()) / ("audit05-pg-" + secrets.token_hex(12))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT05_OWNED"
MARK.write_text(STAMP, encoding="utf-8")
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(40)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit05_" + secrets.token_hex(5)
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
    assert CLUSTER.parent == Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith("audit05-pg-")
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
        "audit05",
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

    conf = {"host": "127.0.0.1", "port": PORT, "user": "audit05", "password": PW}
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
            "USER": "audit05",
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
    from catalog.models import Category, Product
    from catalog.services import toggle_category_status, toggle_product_availability, update_product
    from identity.models import Account, Role
    from inventory.models import InitialInventoryLoad, InitialLoadLine, Lot
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        create_supplier,
        toggle_supplier_status,
    )

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

    pw_user = "PgAudit05#Pass123"
    admin = Account.objects.create_user("admin.pg05@test.invalid", pw_user, display_name="Admin PG05", role=admin_role)
    wh1 = Account.objects.create_user("wh1.pg05@test.invalid", pw_user, display_name="Almacen1 PG05", role=wh_role)
    wh2 = Account.objects.create_user("wh2.pg05@test.invalid", pw_user, display_name="Almacen2 PG05", role=wh_role)

    today = tz.localdate()
    future = today + timedelta(days=45)
    future2 = today + timedelta(days=90)
    cat_a = Category.objects.create(name="PG05 Cat A")
    cat_b = Category.objects.create(name="PG05 Cat B")

    # ── Case 1 (CT-CONC-01): Simultaneous confirm_initial_load + held row-lock observation ──
    p_lock = Product.objects.create(category=cat_a, name="PG Lock Prod", barcode="775050000101", sale_price=Decimal("5.00"))
    ready1 = threading.Event()
    release1 = threading.Event()

    def lock_confirm_holder():
        close_old_connections()
        try:
            with transaction.atomic():
                load = confirm_initial_load(
                    actor=wh1,
                    product=p_lock,
                    lots=[LotInput("PG-LOCK-1", 4, Decimal("2.5000"), future)],
                )
                ready1.set()
                release1.wait(timeout=8)
                return str(load.pk)
        finally:
            close_old_connections()

    def lock_confirm_waiter():
        close_old_connections()
        try:
            ready1.wait(timeout=8)
            try:
                confirm_initial_load(
                    actor=wh2,
                    product=p_lock,
                    lots=[LotInput("PG-LOCK-2", 6, Decimal("3.0000"), future2)],
                )
                return {"status": "unexpected_commit"}
            except ValidationError as exc:
                return {"status": "rejected", "messages": exc.messages}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        fh = pool.submit(lock_confirm_holder)
        fw = pool.submit(lock_confirm_waiter)
        wait_obs1 = observe_waiter(obs, "catalog_product")
        release1.set()
        fh.result()
        wait_res1 = fw.result()

    # Simultaneous barrier race on a fresh product
    p_race = Product.objects.create(category=cat_a, name="PG Race Prod", barcode="775050000102", sale_price=Decimal("6.00"))
    barrier1 = threading.Barrier(2, timeout=8)

    def race_worker(idx: int, actor: Account):
        close_old_connections()
        try:
            barrier1.wait()
            load = confirm_initial_load(
                actor=actor,
                product=p_race,
                lots=[LotInput(f"PG-RACE-{idx}", 5, Decimal("2.2500"), future)],
            )
            return {"status": "committed", "load_id": str(load.pk)}
        except ValidationError as exc:
            return {"status": "rejected", "messages": exc.messages}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_a = pool.submit(race_worker, 1, wh1)
        f_b = pool.submit(race_worker, 2, wh2)
        race_res = [f_a.result(), f_b.result()]

    p_lock.refresh_from_db()
    p_race.refresh_from_db()
    c1_ok = (
        wait_obs1 is not None
        and wait_res1["status"] == "rejected"
        and any("ya tiene una carga inicial" in m for m in wait_res1["messages"])
        and InitialInventoryLoad.objects.filter(product=p_lock).count() == 1
        and InitialLoadLine.objects.filter(load__product=p_lock).count() == 1
        and Lot.objects.filter(product=p_lock).count() == 1
        and p_lock.average_cost == Decimal("2.5000")
        and sorted(x["status"] for x in race_res) == ["committed", "rejected"]
        and InitialInventoryLoad.objects.filter(product=p_race).count() == 1
        and InitialLoadLine.objects.filter(load__product=p_race).count() == 1
        and Lot.objects.filter(product=p_race).count() == 1
    )
    report["cases"].append(
        {"id": "pg_ct_conc_01_duplicate_initial_load", "ok": c1_ok, "checks": {"lock": wait_obs1, "waiter": wait_res1, "barrier": race_res}}
    )

    # ── Case 2: confirm_initial_load vs update_product (category reclassification) both orders, zero deadlock ──
    p_reclass_a = Product.objects.create(category=cat_a, name="PG Reclass A", barcode="775050000201", sale_price=Decimal("4.00"))
    p_reclass_b = Product.objects.create(category=cat_a, name="PG Reclass B", barcode="775050000202", sale_price=Decimal("4.00"))

    reclass_results = {}
    for label, first_op, prod_obj in [("confirm_first", "confirm", p_reclass_a), ("reclass_first", "reclass", p_reclass_b)]:
        ev_ready = threading.Event()
        ev_rel = threading.Event()

        def holder2(op=first_op, p=prod_obj, r=ev_ready, rel=ev_rel):
            close_old_connections()
            try:
                with transaction.atomic():
                    if op == "confirm":
                        confirm_initial_load(actor=wh1, product=p, lots=[LotInput("PG-REC-1", 4, Decimal("2.00"), future)])
                    else:
                        update_product(
                            actor=admin,
                            product=p,
                            name=p.name,
                            barcode=p.barcode,
                            sale_price=p.sale_price,
                            minimum_stock=p.minimum_stock,
                            category=cat_b,
                        )
                    r.set()
                    rel.wait(timeout=8)
                return {"status": "committed"}
            finally:
                close_old_connections()

        def waiter2(op=first_op, p=prod_obj, r=ev_ready):
            close_old_connections()
            try:
                r.wait(timeout=8)
                if op == "confirm":
                    updated = update_product(
                        actor=admin,
                        product=p,
                        name=p.name,
                        barcode=p.barcode,
                        sale_price=p.sale_price,
                        minimum_stock=p.minimum_stock,
                        category=cat_b,
                    )
                    return {"status": "committed", "cat_id": str(updated.category_id)}
                load = confirm_initial_load(actor=wh1, product=p, lots=[LotInput("PG-REC-2", 4, Decimal("2.00"), future)])
                return {"status": "committed", "load_id": str(load.pk)}
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
            f_h = pool.submit(holder2)
            f_w = pool.submit(waiter2)
            lock2 = observe_waiter(obs, "catalog_product")
            ev_rel.set()
            res_h = f_h.result()
            res_w = f_w.result()
        prod_obj.refresh_from_db()
        reclass_results[label] = {
            "lock": lock2,
            "holder": res_h,
            "waiter": res_w,
            "final_cat_id": str(prod_obj.category_id),
            "loads": InitialInventoryLoad.objects.filter(product=prod_obj).count(),
        }

    c2_ok = (
        all(v["lock"] is not None and v["final_cat_id"] == str(cat_b.pk) and v["loads"] == 1 for v in reclass_results.values())
    )
    report["cases"].append({"id": "pg_product_before_category_no_deadlock_with_reclassify", "ok": c2_ok, "checks": reclass_results})

    # ── Case 3: Bidirectional Category Suspension vs confirm_initial_load ──
    cat_suspend_first = Category.objects.create(name="PG05 Suspend First")
    cat_confirm_first = Category.objects.create(name="PG05 Confirm First")
    p_cat_race1 = Product.objects.create(category=cat_suspend_first, name="PG CatRace1", barcode="775050000301", sale_price=Decimal("3.00"))
    p_cat_race2 = Product.objects.create(category=cat_confirm_first, name="PG CatRace2", barcode="775050000302", sale_price=Decimal("3.00"))

    cat_results = {}
    # Order A: Category suspension holds lock -> confirm_initial_load waits -> rejects cleanly without writes
    r3a, rel3a = threading.Event(), threading.Event()

    def hold_cat_suspend():
        close_old_connections()
        try:
            with transaction.atomic():
                toggle_category_status(actor=admin, category=cat_suspend_first, is_active=False)
                r3a.set()
                rel3a.wait(timeout=8)
        finally:
            close_old_connections()

    def wait_load_after_cat():
        close_old_connections()
        try:
            r3a.wait(timeout=8)
            try:
                confirm_initial_load(actor=wh1, product=p_cat_race1, lots=[LotInput("PG-C1", 3, Decimal("1.50"), future)])
                return {"status": "unexpected_commit"}
            except ValidationError as exc:
                return {"status": "rejected", "messages": exc.messages}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        fa = pool.submit(hold_cat_suspend)
        fb = pool.submit(wait_load_after_cat)
        lock3a = observe_waiter(obs, "catalog_category")
        rel3a.set()
        fa.result()
        res3a = fb.result()
    cat_results["suspend_first"] = {"lock": lock3a, "confirm": res3a, "loads": InitialInventoryLoad.objects.filter(product=p_cat_race1).count()}

    # Order B: Confirm holds lock on p_cat_race2/cat_confirm_first -> toggle waits -> confirm succeeds once, toggle disables
    r3b, rel3b = threading.Event(), threading.Event()

    def hold_confirm_before_cat():
        close_old_connections()
        try:
            with transaction.atomic():
                load = confirm_initial_load(actor=wh1, product=p_cat_race2, lots=[LotInput("PG-C2", 3, Decimal("1.50"), future)])
                r3b.set()
                rel3b.wait(timeout=8)
                return str(load.pk)
        finally:
            close_old_connections()

    def wait_cat_suspend():
        close_old_connections()
        try:
            r3b.wait(timeout=8)
            cat = toggle_category_status(actor=admin, category=cat_confirm_first, is_active=False)
            return {"is_active": cat.is_active}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        fa = pool.submit(hold_confirm_before_cat)
        fb = pool.submit(wait_cat_suspend)
        lock3b = observe_waiter(obs, "catalog_category")
        rel3b.set()
        fa.result()
        res3b = fb.result()
    cat_results["confirm_first"] = {"lock": lock3b, "toggle": res3b, "loads": InitialInventoryLoad.objects.filter(product=p_cat_race2).count()}

    c3_ok = (
        cat_results["suspend_first"]["lock"] is not None
        and cat_results["suspend_first"]["confirm"]["status"] == "rejected"
        and cat_results["suspend_first"]["loads"] == 0
        and Lot.objects.filter(product=p_cat_race1).count() == 0
        and cat_results["confirm_first"]["lock"] is not None
        and not cat_results["confirm_first"]["toggle"]["is_active"]
        and cat_results["confirm_first"]["loads"] == 1
    )
    report["cases"].append({"id": "pg_bidirectional_category_suspension_vs_initial_load", "ok": c3_ok, "checks": cat_results})

    # ── Case 4: Bidirectional Product Deactivation vs confirm_initial_load ──
    p_deact_first = Product.objects.create(category=cat_a, name="PG Deact1", barcode="775050000401", sale_price=Decimal("4.00"))
    p_deact_second = Product.objects.create(category=cat_a, name="PG Deact2", barcode="775050000402", sale_price=Decimal("4.00"))

    r4a, rel4a = threading.Event(), threading.Event()
    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        def h4a():
            close_old_connections()
            try:
                with transaction.atomic():
                    toggle_product_availability(actor=admin, product=p_deact_first, is_active=False)
                    r4a.set()
                    rel4a.wait(timeout=8)
            finally:
                close_old_connections()

        def w4a():
            close_old_connections()
            try:
                r4a.wait(timeout=8)
                try:
                    confirm_initial_load(actor=wh1, product=p_deact_first, lots=[LotInput("PG-D1", 3, Decimal("2.00"), future)])
                    return {"status": "unexpected_commit"}
                except ValidationError as exc:
                    return {"status": "rejected", "messages": exc.messages}
            finally:
                close_old_connections()

        fa, fb = pool.submit(h4a), pool.submit(w4a)
        lock4a = observe_waiter(obs, "catalog_product")
        rel4a.set()
        fa.result()
        res4a = fb.result()

    r4b, rel4b = threading.Event(), threading.Event()
    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        def h4b():
            close_old_connections()
            try:
                with transaction.atomic():
                    confirm_initial_load(actor=wh1, product=p_deact_second, lots=[LotInput("PG-D2", 3, Decimal("2.00"), future)])
                    r4b.set()
                    rel4b.wait(timeout=8)
            finally:
                close_old_connections()

        def w4b():
            close_old_connections()
            try:
                r4b.wait(timeout=8)
                prod = toggle_product_availability(actor=admin, product=p_deact_second, is_active=False)
                return {"is_active": prod.is_active}
            finally:
                close_old_connections()

        fa, fb = pool.submit(h4b), pool.submit(w4b)
        lock4b = observe_waiter(obs, "catalog_product")
        rel4b.set()
        fa.result()
        res4b = fb.result()

    c4_ok = (
        lock4a is not None
        and res4a["status"] == "rejected"
        and InitialInventoryLoad.objects.filter(product=p_deact_first).count() == 0
        and Lot.objects.filter(product=p_deact_first).count() == 0
        and lock4b is not None
        and not res4b["is_active"]
        and InitialInventoryLoad.objects.filter(product=p_deact_second).count() == 1
    )
    report["cases"].append(
        {
            "id": "pg_bidirectional_product_deactivation_vs_initial_load",
            "ok": c4_ok,
            "checks": {"deact_first": {"lock": lock4a, "res": res4a}, "confirm_first": {"lock": lock4b, "res": res4b}},
        }
    )

    # ── Case 5: Concurrent Supplier Deactivation + ALMACENERO Revocation ──
    sup_race = create_supplier(actor=admin, name="PG05 Sup Race SAC", ruc="20505000091")
    p_sup_race = Product.objects.create(category=cat_a, name="PG SupRace", barcode="775050000501", sale_price=Decimal("4.50"))
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
                    confirm_initial_load(actor=wh1, product=p_sup_race, supplier=sup_race, lots=[LotInput("PG-SUP1", 4, Decimal("2.00"), future)])
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

    wh_victim = Account.objects.create_user("wh.victim05@test.invalid", pw_user, display_name="Victim WH05", role=wh_role)
    p_actor_race = Product.objects.create(category=cat_a, name="PG ActorRace", barcode="775050000502", sale_price=Decimal("4.50"))
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
                    confirm_initial_load(actor=wh_victim, product=p_actor_race, lots=[LotInput("PG-ACT1", 4, Decimal("2.00"), future)])
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
        and InitialInventoryLoad.objects.filter(product=p_sup_race).count() == 0
        and lock5a is not None
        and res5a["status"] == "denied"
        and InitialInventoryLoad.objects.filter(product=p_actor_race).count() == 0
    )
    report["cases"].append(
        {
            "id": "pg_supplier_deactivation_and_warehouse_revocation",
            "ok": c5_ok,
            "checks": {"supplier": {"lock": lock5s, "res": res5s}, "actor": {"lock": lock5a, "res": res5a}},
        }
    )

    # ── Case 6 (CT-ROLLBACK-01 + PostgreSQL \x00 NUL-byte ValidationError + 0006 Trigger ERRCODE 23514) ──
    p_rb = Product.objects.create(category=cat_a, name="PG Rollback", barcode="775050000601", sale_price=Decimal("4.00"), average_cost=Decimal("0.0000"))
    orig_bulk_create = Lot.objects.bulk_create
    created_inside_tx = {"called": False}

    def failing_bulk_create(*args, **kwargs):
        res = orig_bulk_create(*args, **kwargs)
        created_inside_tx["called"] = True
        raise RuntimeError("Simulated PostgreSQL failure after Lot.bulk_create")

    Lot.objects.bulk_create = failing_bulk_create
    rb_caught = False
    try:
        confirm_initial_load(actor=wh1, product=p_rb, lots=[LotInput("PG-RB-1", 4, Decimal("2.00"), future)])
    except RuntimeError:
        rb_caught = True
    finally:
        Lot.objects.bulk_create = orig_bulk_create

    nul_caught = None
    try:
        confirm_initial_load(actor=wh1, product=p_rb, lots=[LotInput("L\x00PG", 4, Decimal("2.00"), future)])
    except ValidationError as exc:
        nul_caught = {"type": type(exc).__name__, "messages": exc.messages}

    # Check PostgreSQL DB trigger 0006 prevents UPDATE of received_at (SQLSTATE 23514)
    sample_lot = Lot.objects.filter(product=p_lock).first()
    trigger_sqlstate = None
    try:
        with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute("UPDATE inventory_lot SET received_at = received_at - interval '1 day' WHERE id = %s", [str(sample_lot.pk)])
    except IntegrityError as exc:
        cause = getattr(exc, "__cause__", exc)
        trigger_sqlstate = getattr(cause, "sqlstate", None)

    p_rb.refresh_from_db()
    c6_ok = (
        created_inside_tx["called"]
        and rb_caught
        and InitialInventoryLoad.objects.filter(product=p_rb).count() == 0
        and InitialLoadLine.objects.filter(load__product=p_rb).count() == 0
        and Lot.objects.filter(product=p_rb).count() == 0
        and p_rb.average_cost == Decimal("0.0000")
        and nul_caught is not None
        and nul_caught["type"] == "ValidationError"
        and trigger_sqlstate == "23514"
    )
    report["cases"].append(
        {
            "id": "pg_ct_rollback_01_nul_guard_and_trigger_immutability",
            "ok": c6_ok,
            "checks": {
                "rollback_called": created_inside_tx["called"],
                "rollback_caught": rb_caught,
                "rb_loads": InitialInventoryLoad.objects.filter(product=p_rb).count(),
                "nul_guard": nul_caught,
                "trigger_sqlstate": trigger_sqlstate,
            },
        }
    )

    # ── Case 7: Threaded HTTP WSGI Double-Submit on PostgreSQL + Empty POST ──
    p_http = Product.objects.create(category=cat_a, name="PG HTTP Race", barcode="775050000701", sale_price=Decimal("8.00"))
    c_wh1, c_wh2 = Client(), Client()
    c_wh1.force_login(wh1)
    c_wh2.force_login(wh2)

    empty_resp = c_wh1.post("/inventario/carga-inicial/", {})
    empty_ok = empty_resp.status_code == 200 and 'role="alert"' in empty_resp.content.decode()

    barrier_http = threading.Barrier(2, timeout=8)
    http_post_data = {
        "product": str(p_http.pk),
        "supplier": "",
        "lots-TOTAL_FORMS": "4",
        "lots-INITIAL_FORMS": "0",
        "lots-MIN_NUM_FORMS": "1",
        "lots-MAX_NUM_FORMS": "1000",
        "lots-0-number": "PG-HTTP-1",
        "lots-0-quantity": "10",
        "lots-0-unit_cost": "3.5000",
        "lots-0-expiration_date": future.isoformat(),
    }

    def http_submit(client_obj: Client):
        close_old_connections()
        try:
            barrier_http.wait()
            resp = client_obj.post("/inventario/carga-inicial/", http_post_data)
            body = resp.content.decode() if resp.status_code == 200 else ""
            has_msg = (
                "Este producto ya tiene una carga inicial confirmada." in body
                or "Este producto ya tiene una carga inicial registrada o no está disponible." in body
            )
            return {
                "status": resp.status_code,
                "location": resp.get("Location"),
                "has_already_msg": has_msg,
                "has_confirmada_msg": "Este producto ya tiene una carga inicial confirmada." in body,
                "has_registrada_msg": "Este producto ya tiene una carga inicial registrada o no está disponible." in body,
                "has_alert": 'role="alert"' in body,
            }
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_h1 = pool.submit(http_submit, c_wh1)
        f_h2 = pool.submit(http_submit, c_wh2)
        http_results = [f_h1.result(), f_h2.result()]

    c7_ok = (
        empty_ok
        and sorted(r["status"] for r in http_results) == [200, 302]
        and any(r["status"] == 200 and r["has_already_msg"] for r in http_results)
        and InitialInventoryLoad.objects.filter(product=p_http).count() == 1
        and InitialLoadLine.objects.filter(load__product=p_http).count() == 1
        and Lot.objects.filter(product=p_http).count() == 1
    )
    report["cases"].append(
        {
            "id": "pg_http_concurrent_double_submit_and_empty_post",
            "ok": c7_ok,
            "checks": {
                "empty_ok": empty_ok,
                "http_results": http_results,
                "final_loads": InitialInventoryLoad.objects.filter(product=p_http).count(),
                "final_lines": InitialLoadLine.objects.filter(load__product=p_http).count(),
                "final_lots": Lot.objects.filter(product=p_http).count(),
            },
        }
    )

    # ── Case 8: DEC-05-LOTE-ESPACIOS + InitialLoadLine Snapshot Preservation on PG ──
    sup_dec05 = create_supplier(actor=admin, name="Proveedor Original PG05", ruc="20100070970")
    p_dec05_dup = Product.objects.create(category=cat_a, name="PG DEC05 Dup", barcode="775050000801", sale_price=Decimal("7.00"))
    dec05_dup_rejected = False
    try:
        confirm_initial_load(
            actor=wh1,
            product=p_dec05_dup,
            supplier=sup_dec05,
            lots=[
                LotInput("  ab  12 ", 4, Decimal("2.0000"), future),
                LotInput("AB 12", 5, Decimal("3.0000"), future2),
            ],
        )
    except ValidationError:
        dec05_dup_rejected = True

    p_dec05 = Product.objects.create(category=cat_a, name="Producto Snap PG05", barcode="775050000802", sale_price=Decimal("7.00"))
    load_dec05 = confirm_initial_load(
        actor=wh1,
        product=p_dec05,
        supplier=sup_dec05,
        lots=[
            LotInput("  ab  12 ", 4, Decimal("2.0000"), future),
            LotInput("AB12", 6, Decimal("3.0000"), future2),
        ],
    )
    p_dec05.refresh_from_db()
    dup_sqlstate = None
    try:
        with transaction.atomic():
            with connection.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO inventory_lot (
                        id, product_id, supplier_id, initial_load_id, responsible_id,
                        number, number_normalized, unit_cost, initial_quantity, available_quantity,
                        expiration_date, is_initial, received_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, 'AB 12', 'AB 12', 1.0000, 1, 1, %s, true, now()
                    )
                    """,
                    [
                        "00000000-0000-0000-0000-000000000809",
                        str(p_dec05.pk),
                        str(sup_dec05.pk),
                        str(load_dec05.pk),
                        str(wh1.pk),
                        future,
                    ],
                )
    except IntegrityError as exc:
        dup_sqlstate = getattr(getattr(exc, "__cause__", exc), "sqlstate", None)

    Product.objects.filter(pk=p_dec05.pk).update(name="Producto Renombrado PG05", barcode="775050000899")
    type(sup_dec05).objects.filter(pk=sup_dec05.pk).update(name="Proveedor Renombrado PG05")
    Account.objects.filter(pk=wh1.pk).update(display_name="Responsable Renombrado PG05")
    load_dec05.refresh_from_db()
    lines_dec05 = list(InitialLoadLine.objects.filter(load=load_dec05).order_by("number").values_list("number", "quantity", "unit_cost"))

    c8_ok = (
        dec05_dup_rejected
        and InitialInventoryLoad.objects.filter(product=p_dec05_dup).count() == 0
        and InitialLoadLine.objects.filter(load__product=p_dec05_dup).count() == 0
        and p_dec05.average_cost == Decimal("2.6000")
        and p_dec05.physical_stock == 10
        and dup_sqlstate == "23505"
        and load_dec05.product_snapshot_name == "Producto Snap PG05"
        and load_dec05.product_snapshot_barcode == "775050000802"
        and load_dec05.supplier_snapshot_name == "Proveedor Original PG05"
        and load_dec05.responsible_snapshot_name == "Almacen1 PG05"
        and load_dec05.average_cost_snapshot == Decimal("2.6000")
        and lines_dec05 == [("AB 12", 4, Decimal("2.0000")), ("AB12", 6, Decimal("3.0000"))]
    )
    report["cases"].append(
        {
            "id": "pg_dec_05_lot_spacing_and_initial_load_line_snapshot",
            "ok": c8_ok,
            "checks": {
                "dup_rejected": dec05_dup_rejected,
                "dup_sqlstate": dup_sqlstate,
                "lines": [(n, q, str(c)) for n, q, c in lines_dec05],
                "snapshots": [
                    load_dec05.product_snapshot_name,
                    load_dec05.supplier_snapshot_name,
                    load_dec05.responsible_snapshot_name,
                    str(load_dec05.average_cost_snapshot),
                ],
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
    out = RESULTS / "evidencias" / ("05-postgresql-" + STAMP + ".json")
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
    or len(report["cases"]) != 8
    or not all(x["ok"] for x in report["cases"])
    or not report["port_closed"]
    or not all(report["protected_unchanged"].values())
):
    raise SystemExit(1)
