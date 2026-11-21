"""Stage 04 real PostgreSQL 18.4 concurrency & row-lock tests in an ephemeral owned cluster.
Never touches production settings or existing databases/clusters.
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
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "auditoria_por_etapas/resultados"
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
CLUSTER = (Path(tempfile.gettempdir()) / ("audit04-pg-" + secrets.token_hex(12))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT04_OWNED"
MARK.write_text(STAMP, encoding="utf-8")
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(40)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit04_" + secrets.token_hex(5)
with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]

protected = [
    *(ROOT / "r1-pmv").glob("*.sqlite3"),
    *(RESULTS / "datos").rglob("*.sqlite3"),
    ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
]


def state(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


hashes = {str(p.relative_to(ROOT)): state(p) for p in protected}
report = {
    "started_utc": STAMP,
    "cluster": str(CLUSTER),
    "port": PORT,
    "cases": [],
    "protected_absent_at_start": [k for k, v in hashes.items() if v is None],
}


def own() -> None:
    assert CLUSTER.parent == Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith("audit04-pg-")
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


def observe_waiter(conn, relation_prefix: str, timeout_s: float = 5.0) -> dict | None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.pid, a.wait_event_type, a.wait_event, pg_blocking_pids(a.pid), l.relation::regclass::text,
                       a.query
                FROM pg_stat_activity a
                LEFT JOIN pg_locks l ON l.pid = a.pid AND NOT l.granted
                WHERE a.datname = current_database()
                  AND a.pid <> pg_backend_pid()
                  AND cardinality(pg_blocking_pids(a.pid)) > 0
                """
            )
            for pid, wet, we, blockers, rel, query in cur.fetchall():
                # A transactionid lock has no relation; identify the blocked SELECT,
                # rather than treating any unrelated blocked transaction as evidence.
                if f'"{relation_prefix}"' in query and "FOR UPDATE" in query.upper():
                    return {
                        "waiting_pid": pid,
                        "wait_event_type": wet,
                        "wait_event": we,
                        "blocking_pids": list(blockers),
                        "relation": rel,
                        "blocked_select_relation": relation_prefix,
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
        "audit04",
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

    conf = {"host": "127.0.0.1", "port": PORT, "user": "audit04", "password": PW}
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
            "USER": "audit04",
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
    from django.utils import timezone as tz
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.models import InitialInventoryLoad, Lot, Supplier
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        create_supplier,
        register_stock_entry,
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

    pw_user = "PgAudit04#Pass123"
    admin = Account.objects.create_user("admin.pg@test.invalid", pw_user, display_name="Admin PG", role=admin_role)
    admin2 = Account.objects.create_user("admin2.pg@test.invalid", pw_user, display_name="Admin PG 2", role=admin_role)
    wh = Account.objects.create_user("wh.pg@test.invalid", pw_user, display_name="Almacén PG", role=wh_role)
    cat = Category.objects.create(name="PG Audit04")

    # ── Case 1: Concurrent duplicate RUC create_supplier -> 1 ok, 1 controlled ValidationError ──
    barrier1 = threading.Barrier(2, timeout=8)
    before_insert = threading.Barrier(2, timeout=8)
    original_clean = Supplier.full_clean

    def synchronized_clean(instance, *args, **kwargs):
        original_clean(instance, *args, **kwargs)
        if instance.ruc == "20111222334":
            before_insert.wait()  # Both passed the exists check before either INSERT.

    def create_dup_worker(idx: int) -> dict:
        close_old_connections()
        try:
            barrier1.wait()
            sup = create_supplier(actor=admin if idx == 1 else admin2, name=f"Duplicado PG {idx}", ruc="20111222334")
            return {"status": "created", "id": str(sup.pk)}
        except ValidationError as exc:
            return {"status": "validation_error", "messages": exc.messages}
        finally:
            close_old_connections()

    with patch.object(Supplier, "full_clean", synchronized_clean), ThreadPoolExecutor(max_workers=2) as pool:
        r1 = list(pool.map(create_dup_worker, [1, 2]))
    statuses1 = sorted(x["status"] for x in r1)
    msg_err1 = next((x["messages"] for x in r1 if x["status"] == "validation_error"), [])
    c1_ok = (
        statuses1 == ["created", "validation_error"]
        and msg_err1 == ["El RUC ya está registrado."]
        and Supplier.objects.filter(ruc="20111222334").count() == 1
    )
    report["cases"].append({"id": "pg_concurrent_duplicate_ruc_create", "ok": c1_ok, "checks": r1})

    # ── Case 2: Concurrent toggle_supplier_status with explicit is_active=False + lock observation ──
    sup_toggle = create_supplier(actor=admin, name="Toggle PG SAC", ruc="20444555661")
    locked_ready = threading.Event()
    release_holder = threading.Event()

    def lock_holder():
        close_old_connections()
        try:
            with transaction.atomic():
                toggle_supplier_status(actor=admin, supplier=sup_toggle, is_active=False)
                locked_ready.set()
                release_holder.wait(timeout=8)
        finally:
            close_old_connections()

    def lock_waiter():
        close_old_connections()
        try:
            locked_ready.wait(timeout=8)
            updated = toggle_supplier_status(actor=admin2, supplier=sup_toggle, is_active=False)
            return {"is_active": updated.is_active, "changed": getattr(updated, "_state_changed", None)}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        f_hold = pool.submit(lock_holder)
        f_wait = pool.submit(lock_waiter)
        wait_obs = observe_waiter(obs, "inventory_supplier")
        release_holder.set()
        f_hold.result()
        wait_res = f_wait.result()
    sup_toggle.refresh_from_db()
    c2_ok = wait_obs is not None and not sup_toggle.is_active and wait_res == {"is_active": False, "changed": False}
    report["cases"].append(
        {"id": "pg_concurrent_toggle_idempotent_with_row_lock", "ok": c2_ok, "checks": {"lock": wait_obs, "waiter": wait_res}}
    )

    # ── Case 3: Concurrent deactivate vs confirm_initial_load AND register_stock_entry ──
    sup_race_init = create_supplier(actor=admin, name="Race Init SAC", ruc="20555666771")
    sup_race_ent = create_supplier(actor=admin, name="Race Entry SAC", ruc="20555666772")
    prod_race_init = Product.objects.create(
        category=cat, name="Arroz PG Init", barcode="775049990001", sale_price=Decimal("4.20")
    )
    prod_race_ent = Product.objects.create(
        category=cat, name="Fideo PG Entry", barcode="775049990002", sale_price=Decimal("3.80")
    )
    future = tz.localdate() + timedelta(days=30)
    confirm_initial_load(
        actor=wh,
        product=prod_race_ent,
        lots=[LotInput("PG-BASE", 3, Decimal("2.00"), future)],
    )

    race_results = {}
    for op_name, sup_obj, prod_obj, lot_code, use_entry in [
        ("initial_load", sup_race_init, prod_race_init, "PG-L1", False),
        ("stock_entry", sup_race_ent, prod_race_ent, "PG-L2", True),
    ]:
        ready3 = threading.Event()
        release3 = threading.Event()

        def deactivate_holder(s=sup_obj, ev_ready=ready3, ev_rel=release3):
            close_old_connections()
            try:
                with transaction.atomic():
                    toggle_supplier_status(actor=admin, supplier=s, is_active=False)
                    ev_ready.set()
                    ev_rel.wait(timeout=8)
            finally:
                close_old_connections()

        def receipt_waiter(s=sup_obj, p=prod_obj, lc=lot_code, entry_flag=use_entry, ev_ready=ready3):
            close_old_connections()
            try:
                ev_ready.wait(timeout=8)
                try:
                    if entry_flag:
                        register_stock_entry(
                            actor=wh, product=p, supplier=s, lots=[LotInput(lc, 5, Decimal("2.10"), future)]
                        )
                    else:
                        confirm_initial_load(
                            actor=wh, product=p, supplier=s, lots=[LotInput(lc, 5, Decimal("2.00"), future)]
                        )
                    return {"status": "committed"}
                except ValidationError as exc:
                    return {"status": "rejected", "messages": exc.messages}
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
            f_deact = pool.submit(deactivate_holder)
            f_rcpt = pool.submit(receipt_waiter)
            lock_sub = observe_waiter(obs, "inventory_supplier")
            release3.set()
            f_deact.result()
            rcpt_sub = f_rcpt.result()
        race_results[op_name] = {"lock": lock_sub, "receipt": rcpt_sub}

    c3_ok = (
        all(v["lock"] is not None and v["receipt"]["status"] == "rejected" for v in race_results.values())
        and all(any("está inactivo" in m for m in v["receipt"]["messages"]) for v in race_results.values())
        and Lot.objects.filter(product=prod_race_init).count() == 0
        and InitialInventoryLoad.objects.filter(product=prod_race_init).count() == 0
        and Lot.objects.filter(product=prod_race_ent).count() == 1
    )
    report["cases"].append(
        {"id": "pg_concurrent_supplier_deactivation_blocks_receipt", "ok": c3_ok, "checks": race_results}
    )

    # ── Case 4: Concurrent ADMIN demotion blocks create_supplier + PG HTTP ?q=%00 safe 200 ──
    admin_victim = Account.objects.create_user("victim.pg@test.invalid", pw_user, display_name="Victim PG", role=admin_role)
    ready4 = threading.Event()
    release4 = threading.Event()

    def demote_holder():
        close_old_connections()
        try:
            with transaction.atomic():
                Account.objects.select_for_update().filter(pk=admin_victim.pk).update(role=seller_role, is_active=False)
                ready4.set()
                release4.wait(timeout=8)
        finally:
            close_old_connections()

    def victim_create_waiter():
        close_old_connections()
        try:
            ready4.wait(timeout=8)
            try:
                create_supplier(actor=admin_victim, name="Post Revocación PG", ruc="20888999001")
                return {"status": "unexpected_commit"}
            except PermissionDenied as exc:
                return {"status": "denied", "message": str(exc)}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as obs:
        f_demote = pool.submit(demote_holder)
        f_create = pool.submit(victim_create_waiter)
        lock4 = observe_waiter(obs, "identity_account")
        release4.set()
        f_demote.result()
        create_res = f_create.result()

    client = Client()
    client.force_login(admin)
    nul_http = client.get("/inventario/proveedores/", {"q": "abc\x00def"})
    nul_ok = nul_http.status_code == 200 and "La búsqueda contiene caracteres no válidos." in nul_http.content.decode()

    c4_ok = (
        lock4 is not None
        and create_res["status"] == "denied"
        and not Supplier.objects.filter(ruc="20888999001").exists()
        and nul_ok
    )
    report["cases"].append(
        {
            "id": "pg_concurrent_admin_revocation_and_nul_search",
            "ok": c4_ok,
            "checks": {"lock": lock4, "create": create_res, "nul_http_status": nul_http.status_code, "nul_controlled": nul_ok},
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
    report["protected_unchanged"] = {str(p.relative_to(ROOT)): state(p) == hashes[str(p.relative_to(ROOT))] for p in protected}
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    out = RESULTS / "evidencias" / ("04-postgresql-" + STAMP + ".json")
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
    or len(report["cases"]) != 4
    or not all(x["ok"] for x in report["cases"])
    or not report["port_closed"]
    or not all(report["protected_unchanged"].values())
):
    raise SystemExit(1)
