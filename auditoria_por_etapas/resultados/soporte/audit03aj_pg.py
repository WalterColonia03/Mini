"""Stage 03-AJ / 06-E PostgreSQL 18.4 row-lock concurrency races on an owned temporary cluster.

Exercises real blocking between inventory receipts (register_stock_entry / confirm_initial_load)
and administrator revocations (update_employee role change / deactivate_employee) on identity_account.
Stops the cluster cleanly in finally, leaves protected DBs and XLSX untouched.
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
CLUSTER = (Path(tempfile.gettempdir()) / ("audit03aj-pg-" + secrets.token_hex(12))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT03AJ_OWNED"
MARK.write_text(STAMP, encoding="utf-8")
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(40)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit03aj_" + secrets.token_hex(5)
with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]

protected = [*(ROOT / "r1-pmv").glob("*.sqlite3"), *(RESULTS / "datos").rglob("*.sqlite3"), ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx"]


def state(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


hashes = {str(p.relative_to(ROOT)): state(p) for p in protected}
evidence = {
    "started_utc": datetime.now(timezone.utc).isoformat(),
    "cluster": str(CLUSTER),
    "port": PORT,
    "cases": [],
    "protected_absent_at_start": [k for k, v in hashes.items() if v is None],
}


def own():
    assert CLUSTER.parent == Path(tempfile.gettempdir()).resolve()
    assert CLUSTER.name.startswith("audit03aj-pg-") and MARK.read_text(encoding="utf-8") == STAMP


def pg(name, *args):
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as capture:
        result = subprocess.run(
            [str(BIN / (name + ".exe")), *map(str, args)],
            stdout=capture,
            stderr=capture,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        capture.seek(0)
        diagnostic = capture.read().replace(PW, "[REDACTED]")
    if result.returncode:
        raise RuntimeError(name + " failed: " + diagnostic[-1000:])


started = False
configured = False
try:
    own()
    pg(
        "initdb",
        "-D",
        DBDIR,
        "-U",
        "audit03aj",
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

    conf = {"host": "127.0.0.1", "port": PORT, "user": "audit03aj", "password": PW}
    with psycopg.connect(**conf, dbname="postgres", autocommit=True) as conn:
        assert Path(conn.execute("SHOW data_directory").fetchone()[0]).resolve() == DBDIR
        evidence["postgres_version"] = conn.execute("SELECT version()").fetchone()[0]
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DBNAME)))

    sys.path.insert(0, str(ROOT / "r1-pmv"))
    os.environ.update(
        APP_ENV="test",
        DJANGO_DEBUG="false",
        DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
        DJANGO_SETTINGS_MODULE="config.settings",
    )
    from config import env

    old_loader = env.load_dotenv
    env.load_dotenv = lambda path=None: None
    from django.conf import settings

    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": DBNAME,
            "USER": "audit03aj",
            "PASSWORD": PW,
            "HOST": "127.0.0.1",
            "PORT": PORT,
            "CONN_MAX_AGE": 60,
            "OPTIONS": {"options": "-c statement_timeout=20000 -c lock_timeout=12000"},
        }
    }
    env.load_dotenv = old_loader
    import django

    django.setup()
    configured = True

    from django.core.management import call_command
    from django.db import close_old_connections, connection, connections
    from django.utils import timezone as tz

    from catalog.models import Category, Product
    from identity.models import Account, Role
    from identity.services import deactivate_employee, reactivate_employee, update_employee
    from inventory.models import InitialInventoryLoad, Lot
    from inventory.services import LotInput, confirm_initial_load, register_stock_entry

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    with connection.cursor() as cur:
        cur.execute("SELECT current_database(), current_setting('data_directory'), current_setting('transaction_isolation')")
        db, folder, iso = cur.fetchone()
        assert db == DBNAME and Path(folder).resolve() == DBDIR
    evidence.update(db=DBNAME, isolation=iso, migrations="PASS")

    roles = {code: Role.objects.create(code=code, name=code) for code in ["ADMIN", "VENDEDOR", "ALMACENERO"]}
    admin = Account.objects.create_user("admin@audit03aj.invalid", "SafeAudit3!x", display_name="Admin AJ", role=roles["ADMIN"])
    cat = Category.objects.create(name="Conservas AJ PG")
    prod_entry = Product.objects.create(category=cat, name="Producto Entrada PG", barcode="775000910001", sale_price=Decimal("9.00"))
    prod_init_a = Product.objects.create(category=cat, name="Producto Carga A PG", barcode="775000910002", sale_price=Decimal("8.00"))
    prod_init_b = Product.objects.create(category=cat, name="Producto Carga B PG", barcode="775000910003", sale_price=Decimal("8.50"))
    future = tz.localdate() + timedelta(days=90)

    # Seed base initial load on prod_entry.
    wh_seed = Account.objects.create_user("wh-seed@audit03aj.invalid", "SafeAudit3!x", display_name="Seed WH", role=roles["ALMACENERO"])
    confirm_initial_load(actor=wh_seed, product=prod_entry, lots=[LotInput("PG-BASE", 10, Decimal("2.0000"), future)])

    def race_account_lock(name, operations):
        barrier = threading.Barrier(2, timeout=10)
        pids = {}
        first_locked = threading.Event()
        second_entered = threading.Event()
        observed_blockers = []

        def work(index):
            close_old_connections()
            with connection.cursor() as cur:
                cur.execute("SELECT pg_backend_pid()")
                pids[index] = cur.fetchone()[0]
            def coordinate(execute, query, params, many, context):
                is_lock = "FOR UPDATE" in query and 'FROM "identity_account"' in query
                if is_lock and index == 1:
                    second_entered.set()
                value = execute(query, params, many, context)
                if is_lock and index == 0 and not first_locked.is_set():
                    first_locked.set()
                    if not second_entered.wait(10):
                        raise RuntimeError("second worker did not attempt identity_account row lock")
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        with connection.cursor() as cur:
                            cur.execute("SELECT pg_blocking_pids(%s)", [pids[1]])
                            if pids[0] in cur.fetchone()[0]:
                                observed_blockers.append(True)
                                break
                        time.sleep(0.02)
                    if not observed_blockers:
                        raise RuntimeError("PostgreSQL identity_account lock wait was not observed")
                return value

            try:
                barrier.wait()
                if index == 1 and not first_locked.wait(10):
                    raise RuntimeError("first worker did not acquire identity_account row lock")
                with connection.execute_wrapper(coordinate):
                    operations[index]()
                return {"operation": index, "result": "success"}
            except Exception as exc:
                return {"operation": index, "result": type(exc).__name__}
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            f = [pool.submit(work, i) for i in range(2)]
            results = [x.result(timeout=30) for x in f]

        case = {
            "name": name,
            "connections": len(set(pids.values())),
            "postgres_blocking_observed": bool(observed_blockers),
            "results": results,
        }
        evidence["cases"].append(case)
        return case

    # Case 1: entry locks Account first, update_employee (role -> VENDEDOR) waits and succeeds after commit.
    wh1 = Account.objects.create_user("wh1@audit03aj.invalid", "SafeAudit3!x", display_name="WH1", role=roles["ALMACENERO"])
    c1 = race_account_lock(
        "entry_vs_role",
        [
            lambda: register_stock_entry(
                actor=Account.objects.select_related("role").get(pk=wh1.pk),
                product=prod_entry,
                lots=[LotInput("PG-C1", 2, Decimal("5.0000"), future)],
            ),
            lambda: update_employee(
                actor=Account.objects.select_related("role").get(pk=admin.pk),
                account=Account.objects.select_related("role").get(pk=wh1.pk),
                display_name="WH1",
                email="wh1@audit03aj.invalid",
                role=roles["VENDEDOR"],
            ),
        ],
    )
    wh1.refresh_from_db()
    prod_entry.refresh_from_db()
    c1.update(role=wh1.role.code, lots=Lot.objects.filter(product=prod_entry).count(), average_cost=str(prod_entry.average_cost))
    assert c1["postgres_blocking_observed"] and c1["connections"] == 2
    assert [r["result"] for r in c1["results"]] == ["success", "success"]
    assert c1["role"] == "VENDEDOR" and c1["lots"] == 2 and c1["average_cost"] == "2.5000"

    # Case 2: update_employee (role -> VENDEDOR) locks Account first, register_stock_entry blocks and raises PermissionDenied.
    wh2 = Account.objects.create_user("wh2@audit03aj.invalid", "SafeAudit3!x", display_name="WH2", role=roles["ALMACENERO"])
    wh2_stale_actor = Account.objects.select_related("role").get(pk=wh2.pk)
    c2 = race_account_lock(
        "role_vs_entry",
        [
            lambda: update_employee(
                actor=Account.objects.select_related("role").get(pk=admin.pk),
                account=Account.objects.select_related("role").get(pk=wh2.pk),
                display_name="WH2",
                email="wh2@audit03aj.invalid",
                role=roles["VENDEDOR"],
            ),
            lambda: register_stock_entry(
                actor=wh2_stale_actor,
                product=prod_entry,
                lots=[LotInput("PG-C2", 5, Decimal("9.0000"), future)],
            ),
        ],
    )
    wh2.refresh_from_db()
    prod_entry.refresh_from_db()
    c2.update(role=wh2.role.code, lots=Lot.objects.filter(product=prod_entry).count(), average_cost=str(prod_entry.average_cost))
    assert c2["postgres_blocking_observed"] and c2["connections"] == 2
    assert [r["result"] for r in c2["results"]] == ["success", "PermissionDenied"]
    assert c2["role"] == "VENDEDOR" and c2["lots"] == 2 and c2["average_cost"] == "2.5000"

    # Case 3: entry locks Account first, deactivate_employee waits and deactivates cleanly after commit.
    wh3 = Account.objects.create_user("wh3@audit03aj.invalid", "SafeAudit3!x", display_name="WH3", role=roles["ALMACENERO"])
    c3 = race_account_lock(
        "entry_vs_deactivate",
        [
            lambda: register_stock_entry(
                actor=Account.objects.select_related("role").get(pk=wh3.pk),
                product=prod_entry,
                lots=[LotInput("PG-C3", 1, Decimal("8.0000"), future)],
            ),
            lambda: deactivate_employee(
                actor=Account.objects.select_related("role").get(pk=admin.pk),
                account=Account.objects.select_related("role").get(pk=wh3.pk),
            ),
        ],
    )
    wh3.refresh_from_db()
    prod_entry.refresh_from_db()
    c3.update(active=wh3.is_active, lots=Lot.objects.filter(product=prod_entry).count(), average_cost=str(prod_entry.average_cost))
    assert c3["postgres_blocking_observed"] and c3["connections"] == 2
    assert [r["result"] for r in c3["results"]] == ["success", "success"]
    assert c3["active"] is False and c3["lots"] == 3 and c3["average_cost"] == "2.9231"

    # Case 4: deactivate_employee locks Account first, register_stock_entry blocks and raises PermissionDenied.
    wh4 = Account.objects.create_user("wh4@audit03aj.invalid", "SafeAudit3!x", display_name="WH4", role=roles["ALMACENERO"])
    wh4_stale_actor = Account.objects.select_related("role").get(pk=wh4.pk)
    c4 = race_account_lock(
        "deactivate_vs_entry",
        [
            lambda: deactivate_employee(
                actor=Account.objects.select_related("role").get(pk=admin.pk),
                account=Account.objects.select_related("role").get(pk=wh4.pk),
            ),
            lambda: register_stock_entry(
                actor=wh4_stale_actor,
                product=prod_entry,
                lots=[LotInput("PG-C4", 5, Decimal("9.0000"), future)],
            ),
        ],
    )
    wh4.refresh_from_db()
    prod_entry.refresh_from_db()
    c4.update(active=wh4.is_active, lots=Lot.objects.filter(product=prod_entry).count(), average_cost=str(prod_entry.average_cost))
    assert c4["postgres_blocking_observed"] and c4["connections"] == 2
    assert [r["result"] for r in c4["results"]] == ["success", "PermissionDenied"]
    assert c4["active"] is False and c4["lots"] == 3 and c4["average_cost"] == "2.9231"

    # Case 5: deactivate_employee locks Account first, confirm_initial_load blocks and raises PermissionDenied.
    wh5 = Account.objects.create_user("wh5@audit03aj.invalid", "SafeAudit3!x", display_name="WH5", role=roles["ALMACENERO"])
    wh5_stale_actor = Account.objects.select_related("role").get(pk=wh5.pk)
    c5 = race_account_lock(
        "deactivate_vs_initial_load",
        [
            lambda: deactivate_employee(
                actor=Account.objects.select_related("role").get(pk=admin.pk),
                account=Account.objects.select_related("role").get(pk=wh5.pk),
            ),
            lambda: confirm_initial_load(
                actor=wh5_stale_actor,
                product=prod_init_a,
                lots=[LotInput("PG-IA", 4, Decimal("3.0000"), future)],
            ),
        ],
    )
    wh5.refresh_from_db()
    c5.update(active=wh5.is_active, initial_loads=InitialInventoryLoad.objects.filter(product=prod_init_a).count())
    assert c5["postgres_blocking_observed"] and c5["connections"] == 2
    assert [r["result"] for r in c5["results"]] == ["success", "PermissionDenied"]
    assert c5["active"] is False and c5["initial_loads"] == 0

    # Case 6: reactivated wh5 confirms initial_load first while role -> ADMIN waits on identity_account.
    reactivate_employee(actor=Account.objects.select_related("role").get(pk=admin.pk), account=Account.objects.select_related("role").get(pk=wh5.pk))
    c6 = race_account_lock(
        "initial_load_vs_role",
        [
            lambda: confirm_initial_load(
                actor=Account.objects.select_related("role").get(pk=wh5.pk),
                product=prod_init_b,
                lots=[LotInput("PG-IB", 4, Decimal("3.0000"), future)],
            ),
            lambda: update_employee(
                actor=Account.objects.select_related("role").get(pk=admin.pk),
                account=Account.objects.select_related("role").get(pk=wh5.pk),
                display_name="WH5",
                email="wh5@audit03aj.invalid",
                role=roles["ADMIN"],
            ),
        ],
    )
    wh5.refresh_from_db()
    c6.update(role=wh5.role.code, initial_loads=InitialInventoryLoad.objects.filter(product=prod_init_b).count())
    assert c6["postgres_blocking_observed"] and c6["connections"] == 2
    assert [r["result"] for r in c6["results"]] == ["success", "success"]
    assert c6["role"] == "ADMIN" and c6["initial_loads"] == 1

    evidence["status"] = "COMPLETE"
except Exception as exc:
    evidence.update(status="INCOMPLETE", error_type=type(exc).__name__, error=str(exc).replace(PW, "[REDACTED]")[-1200:])
finally:
    if configured:
        connections.close_all()
    try:
        own()
        if started:
            assert Path((DBDIR / "postmaster.pid").read_text(encoding="utf-8").splitlines()[1]).resolve() == DBDIR
            pg("pg_ctl", "-D", DBDIR, "-m", "fast", "-w", "stop")
        with socket.socket() as s:
            evidence["port_closed"] = s.connect_ex(("127.0.0.1", PORT)) != 0
        evidence["cluster_retained"] = CLUSTER.exists()
    except Exception as exc:
        evidence["stop_error"] = type(exc).__name__
    evidence["protected_unchanged"] = {str(p.relative_to(ROOT)): state(p) == hashes[str(p.relative_to(ROOT))] for p in protected}
    evidence["finished_utc"] = datetime.now(timezone.utc).isoformat()
    out = RESULTS / "evidencias" / ("03-AJ-postgresql-" + STAMP + ".json")
    out.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "evidence": str(out.relative_to(ROOT)),
                "status": evidence["status"],
                "cases": evidence["cases"],
                "port_closed": evidence.get("port_closed"),
                "protected_unchanged": all(evidence["protected_unchanged"].values()),
            },
            ensure_ascii=False,
        )
    )
sys.exit(
    0
    if evidence["status"] == "COMPLETE"
    and evidence.get("port_closed")
    and all(evidence["protected_unchanged"].values())
    else 1
)

