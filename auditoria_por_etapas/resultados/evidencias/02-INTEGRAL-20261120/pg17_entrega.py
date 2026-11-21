"""Verificación aislada en PostgreSQL 18.4 (concurrencia, bloqueos y atomicidad) para Sublote 02-E."""
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
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "r1-pmv/manage.py").is_file())
PROJECT = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
OUT = RESULTS / "evidencias/02-INTEGRAL-20261120/postgresql17-entrega"
OUT.mkdir(parents=True, exist_ok=True)
BIN = Path(os.environ["AUDIT_PG17_BIN"])

STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
CLUSTER = (Path(tempfile.gettempdir()) / f"audit02e-pg-{secrets.token_hex(8)}").resolve()
assert CLUSTER.parent == Path(tempfile.gettempdir()).resolve()
CLUSTER.mkdir(exist_ok=False)
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(36)
PWFILE = CLUSTER / "pw.txt"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = f"audit02e_{secrets.token_hex(5)}"

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]


def pg(cmd: str, *args) -> None:
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as capture:
        proc = subprocess.run(
            [str(BIN / f"{cmd}.exe"), *map(str, args)],
            stdout=capture,
            stderr=capture,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        capture.seek(0)
        msg = capture.read().replace(PW, "[REDACTED]")
    if proc.returncode != 0:
        raise RuntimeError(f"{cmd} failed: {msg[-800:]}")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    prod_db = PROJECT / "r1_pmv.sqlite3"
    db_before = sha256_file(prod_db)
    evidence: dict = {
        "stage": "02-E",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "port": PORT,
        "cases": [],
    }
    started = False
    configured = False
    try:
        pg(
            "initdb",
            "-D",
            DBDIR,
            "-U",
            "audit02e",
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

        with psycopg.connect(
            host="127.0.0.1",
            port=PORT,
            user="audit02e",
            password=PW,
            dbname="postgres",
            autocommit=True,
        ) as conn:
            evidence["postgres_version"] = conn.execute("SELECT version()").fetchone()[0]
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DBNAME)))

        sys.path.insert(0, str(PROJECT))
        os.environ.update(
            APP_ENV="test",
            DJANGO_DEBUG="false",
            DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
            DJANGO_SETTINGS_MODULE="config.settings",
        )
        from config import env as config_env

        config_env.load_dotenv = lambda path=None: None
        from django.conf import settings

        settings.DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": DBNAME,
                "USER": "audit02e",
                "PASSWORD": PW,
                "HOST": "127.0.0.1",
                "PORT": PORT,
                "CONN_MAX_AGE": 60,
                "OPTIONS": {"options": "-c statement_timeout=20000 -c lock_timeout=12000"},
            }
        }
        import django

        django.setup()
        configured = True

        from django.core.management import call_command
        from django.db import close_old_connections, connection, connections
        from django.test import Client
        from django.urls import reverse
        from django.utils import timezone as dj_tz

        from cash.models import CashRegister, CashShift
        from cash.services import close_cash_shift, open_cash_shift
        from catalog.models import Category, Product
        from identity.models import Account, IdentityAuditEvent, LoginAttempt, Role
        from identity.services import (
            _active_lockout_until,
            authenticate_active_account,
            create_employee,
            deactivate_employee,
            reactivate_employee,
            update_employee,
        )
        from inventory.services import LotInput, confirm_initial_load
        from sales.models import SaleDraft

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            call_command("migrate", interactive=False, verbosity=0)

        with connection.cursor() as cur:
            cur.execute("SELECT current_database(), current_setting('transaction_isolation')")
            db_name, iso = cur.fetchone()
            evidence.update(db=db_name, isolation=iso, migrations="PASS")

        roles = {
            code: Role.objects.get_or_create(code=code, defaults={"name": code})[0]
            for code in [Role.Code.ADMIN, Role.Code.SELLER, Role.Code.WAREHOUSE]
        }
        pw_user = "PgAudit02E!99"
        admin1 = Account.objects.create_user("pg_admin1@test.invalid", pw_user, display_name="PG Admin 1", role=roles[Role.Code.ADMIN])
        admin2 = Account.objects.create_user("pg_admin2@test.invalid", pw_user, display_name="PG Admin 2", role=roles[Role.Code.ADMIN])
        wh1 = Account.objects.create_user("pg_wh@test.invalid", pw_user, display_name="PG Almacenero", role=roles[Role.Code.WAREHOUSE])
        seller1 = Account.objects.create_user("pg_s1@test.invalid", pw_user, display_name="PG Vendedor 1", role=roles[Role.Code.SELLER])
        CashRegister.objects.create(code="CAJA-01")

        def run_blocking_race(name: str, lock_table: str, ops: list):
            barrier = threading.Barrier(2, timeout=10)
            first_locked = threading.Event()
            second_entered = threading.Event()
            pids: dict[int, int] = {}
            blockers: list[bool] = []

            def worker(idx: int):
                close_old_connections()
                with connection.cursor() as cur:
                    cur.execute("SELECT pg_backend_pid()")
                    pids[idx] = cur.fetchone()[0]

                def wrapper(execute, query, params, many, context):
                    is_lock = ("FOR UPDATE" in query or "FOR NO KEY UPDATE" in query) and f'FROM "{lock_table}"' in query
                    if is_lock and idx == 1:
                        second_entered.set()
                    result = execute(query, params, many, context)
                    if is_lock and idx == 0 and not first_locked.is_set():
                        first_locked.set()
                        if not second_entered.wait(10):
                            raise RuntimeError("Second worker did not attempt row lock")
                        deadline = time.monotonic() + 10
                        while time.monotonic() < deadline:
                            with connection.cursor() as c2:
                                c2.execute("SELECT pg_blocking_pids(%s)", [pids[1]])
                                if pids[0] in c2.fetchone()[0]:
                                    blockers.append(True)
                                    break
                            time.sleep(0.02)
                        if not blockers:
                            raise RuntimeError("PostgreSQL blocking PID was not observed")
                    return result

                try:
                    barrier.wait()
                    if idx == 1 and not first_locked.wait(10):
                        raise RuntimeError("First worker did not acquire lock")
                    with connection.execute_wrapper(wrapper):
                        ops[idx]()
                    return {"op": idx, "result": "success"}
                except Exception as exc:
                    return {"op": idx, "result": type(exc).__name__}
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=2) as pool:
                futs = [pool.submit(worker, i) for i in range(2)]
                res = [f.result(timeout=30) for f in futs]
            return {
                "name": name,
                "connections": len(set(pids.values())),
                "postgres_blocking_observed": bool(blockers),
                "results": res,
            }

        # 1. Carrera último administrador
        c1 = run_blocking_race(
            "last_admin_race",
            "identity_role",
            [
                lambda: deactivate_employee(actor=Account.objects.get(pk=admin1.pk), account=Account.objects.get(pk=admin2.pk)),
                lambda: deactivate_employee(actor=Account.objects.get(pk=admin2.pk), account=Account.objects.get(pk=admin1.pk)),
            ],
        )
        active_admins = Account.objects.filter(role=roles[Role.Code.ADMIN], is_active=True).count()
        c1["active_admins"] = active_admins
        c1["passed"] = c1["postgres_blocking_observed"] and active_admins >= 1 and sorted(r["result"] for r in c1["results"]) == ["ValidationError", "success"]
        evidence["cases"].append(c1)
        Account.objects.filter(pk__in=[admin1.pk, admin2.pk]).update(is_active=True)

        # 2. Correo duplicado normalizado concurrente
        c2 = run_blocking_race(
            "duplicate_email_race",
            "identity_role",
            [
                lambda: create_employee(actor=Account.objects.get(pk=admin1.pk), display_name="Dup PG 1", email="DupSame@Test.Invalid", password=pw_user, role=roles[Role.Code.SELLER]),
                lambda: create_employee(actor=Account.objects.get(pk=admin2.pk), display_name="Dup PG 2", email="  dupsame@test.invalid ", password=pw_user, role=roles[Role.Code.SELLER]),
            ],
        )
        norm_cnt = Account.objects.filter(email_normalized="dupsame@test.invalid").count()
        c2["normalized_count"] = norm_cnt
        c2["passed"] = c2["postgres_blocking_observed"] and norm_cnt == 1 and sorted(r["result"] for r in c2["results"]) == ["ValidationError", "success"]
        evidence["cases"].append(c2)

        # 3. Apertura de turno vs cambio de rol concurrente
        c3 = run_blocking_race(
            "open_shift_vs_role_change",
            "identity_account",
            [
                lambda: open_cash_shift(actor=Account.objects.get(pk=seller1.pk), opening_amount=Decimal("25.00")),
                lambda: update_employee(actor=Account.objects.get(pk=admin1.pk), account=Account.objects.get(pk=seller1.pk), display_name="PG Vendedor 1", email=seller1.email, role=roles[Role.Code.WAREHOUSE]),
            ],
        )
        seller1.refresh_from_db()
        open_shifts = CashShift.objects.filter(seller=seller1, status=CashShift.Status.OPEN).count()
        c3.update(role=seller1.role.code, open_shifts=open_shifts)
        c3["passed"] = c3["postgres_blocking_observed"] and seller1.role.code == Role.Code.SELLER and open_shifts == 1 and [r["result"] for r in c3["results"]] == ["success", "ValidationError"]
        evidence["cases"].append(c3)
        close_cash_shift(actor=Account.objects.get(pk=seller1.pk), counted_amount=Decimal("25.00"))

        # 4. Carrera de bloqueo por intentos fallidos vs cambio de correo / reactivación
        locked_acc = create_employee(actor=admin1, display_name="PG Bloqueado", email="pg_lock_old@test.invalid", password=pw_user, role=roles[Role.Code.SELLER])
        for _ in range(5):
            authenticate_active_account("pg_lock_old@test.invalid", "WrongPass99")
        deactivate_employee(actor=admin1, account=locked_acc)
        reactivate_employee(actor=admin1, account=locked_acc)
        update_employee(actor=admin1, account=locked_acc, display_name="PG Bloqueado", email="pg_lock_new@test.invalid", role=roles[Role.Code.SELLER])
        lock_survives_old_new = (
            _active_lockout_until("pg_lock_new@test.invalid") is not None
            and not authenticate_active_account("pg_lock_new@test.invalid", pw_user).authenticated
        )
        c4 = {"name": "lockout_preservation_pg", "lock_survives_reactivate_and_rename": lock_survives_old_new, "passed": lock_survives_old_new}
        evidence["cases"].append(c4)

        # 5. Atomicidad de /salir/ (descarte + LOGOUT_SUCCESS) con rollback en PostgreSQL
        today = dj_tz.localdate()
        cat = Category.objects.create(name="PG Bebidas")
        prod = Product.objects.create(category=cat, name="Agua PG", barcode="77599901", sale_price=Decimal("2.50"))
        confirm_initial_load(actor=wh1, product=prod, lots=[LotInput("PG-L1", 10, Decimal("1.0000"), today + timedelta(days=30))])
        open_cash_shift(actor=seller1, opening_amount=Decimal("10.00"))
        client = Client()
        client.force_login(seller1)
        client.post(reverse("sales-draft"), {"product_id": str(prod.pk), "quantity": "2"})
        before_logout_ev = IdentityAuditEvent.objects.filter(action="LOGOUT_SUCCESS").count()
        with patch("identity.views.logout", side_effect=RuntimeError("pg_logout_abort")):
            try:
                client.post(reverse("logout"))
            except RuntimeError:
                pass
        draft_kept = SaleDraft.objects.filter(seller=seller1, status=SaleDraft.Status.ACTIVE).exists()
        ev_after_rollback = IdentityAuditEvent.objects.filter(action="LOGOUT_SUCCESS").count()
        res_ok = client.post(reverse("logout"))
        draft_gone = (
            not SaleDraft.objects.filter(seller=seller1, status=SaleDraft.Status.ACTIVE).exists()
            and SaleDraft.objects.filter(seller=seller1, status=SaleDraft.Status.DISCARDED).exists()
        )
        ev_after_commit = IdentityAuditEvent.objects.filter(action="LOGOUT_SUCCESS").count()
        c5 = {
            "name": "logout_atomic_pg",
            "draft_kept_on_rollback": draft_kept,
            "audit_unchanged_on_rollback": ev_after_rollback == before_logout_ev,
            "commit_status": res_ok.status_code,
            "draft_deleted_on_commit": draft_gone,
            "audit_created_on_commit": ev_after_commit == before_logout_ev + 1,
            "passed": draft_kept and ev_after_rollback == before_logout_ev and res_ok.status_code == 302 and draft_gone and ev_after_commit == before_logout_ev + 1,
        }
        evidence["cases"].append(c5)
        from django.contrib.sessions.models import Session
        for action in ("role", "deactivate", "password"):
            for admin_first in (True, False):
                target = Account.objects.create_user(
                    f"race-{action}-{admin_first}@example.invalid", pw_user,
                    display_name="Empleado de ensayo", role=roles[Role.Code.SELLER],
                )
                client = Client()
                statuses = []
                def sign_in():
                    response = client.post(reverse("login"), {"email": target.email, "password": pw_user})
                    statuses.append(response.status_code)
                def change():
                    if action == "deactivate":
                        deactivate_employee(actor=admin1, account=target)
                    else:
                        update_employee(actor=admin1, account=target, display_name=target.display_name,
                                        email=target.email, role=roles[Role.Code.WAREHOUSE] if action=="role" else target.role,
                                        new_password=pw_user+"2" if action=="password" else "")
                race = run_blocking_race(f"{action}-admin-first-{admin_first}", "identity_account",
                                         [change, sign_in] if admin_first else [sign_in, change])
                sessions = [r.get_decoded() for r in Session.objects.all()]
                active = [r for r in sessions if r.get("_auth_user_id")==str(target.pk)]
                expected_status = 200 if admin_first and action != "role" else 302
                roles_after = [r.get("role_code") for r in active]
                race.update(login_status=statuses, session_roles=roles_after)
                race["passed"] = (race["postgres_blocking_observed"] and
                                  all(r["result"]=="success" for r in race["results"]) and
                                  statuses==[expected_status] and roles_after==(["ALMACENERO"] if action=="role" else []))
                evidence["cases"].append(race)
        evidence["audit_events_total"] = IdentityAuditEvent.objects.count()
        evidence["status"] = "COMPLETE" if all(c["passed"] for c in evidence["cases"]) else "FAILED"
    except Exception as exc:
        evidence.update(status="INCOMPLETE", error_type=type(exc).__name__, error=str(exc).replace(PW, "[REDACTED]")[-1200:])
    finally:
        if configured:
            connections.close_all()
        try:
            if started:
                pg("pg_ctl", "-D", DBDIR, "-m", "fast", "-w", "stop")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                evidence["port_closed"] = s.connect_ex(("127.0.0.1", PORT)) != 0
        except Exception as exc:
            evidence["stop_error"] = type(exc).__name__
        shutil.rmtree(CLUSTER, ignore_errors=True)

    db_after = sha256_file(prod_db)
    evidence["prod_db_unchanged"] = db_before == db_after
    evidence["prod_db_sha256"] = db_after
    evidence["finished_utc"] = datetime.now(timezone.utc).isoformat()
    (OUT / "resumen.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# Informe de verificación en PostgreSQL 17 · Sublote 02-E (20/11/2026)",
        "",
        f"- **Motor:** `{evidence.get('postgres_version', 'N/A')}`",
        f"- **Puerto usado y cerrado:** `{PORT}` (`port_closed: {evidence.get('port_closed')}`)",
        f"- **Base protegida intacta:** `{evidence['prod_db_unchanged']}` (`{db_after}`)",
        f"- **Estado general:** `{evidence['status']}`",
        "",
        "## Casos ejecutados",
        "",
        *[f"- `{c['name']}` -> `passed={c.get('passed')}` ({c})" for c in evidence["cases"]],
    ]
    (OUT / "INFORME.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"ok": evidence["status"] == "COMPLETE" and evidence.get("port_closed"), "port_closed": evidence.get("port_closed")}, ensure_ascii=False))
    if not (evidence["status"] == "COMPLETE" and evidence.get("port_closed") and evidence["prod_db_unchanged"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()




