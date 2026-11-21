"""01-K: PostgreSQL efímero, concurrencia de ingreso y perímetro de admin."""
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
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
OUT = ROOT / "auditoria_por_etapas/resultados/evidencias/01-K-20261115"
OUT.mkdir(parents=True, exist_ok=True)
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUTPUT = OUT / f"postgresql-01k-{STAMP}.json"

evidence = {
    "caso": "E01-PG-01-revalidacion-01K",
    "inicio_utc": datetime.now(timezone.utc).isoformat(),
    "herramienta": "PostgreSQL 18.4 nativo efímero / Django Client CSRF / conexiones por hilo",
    "escenarios": [],
    "limpieza": {},
}

cluster = (Path(tempfile.gettempdir()) / ("audit01k-pg-" + secrets.token_hex(12))).resolve()
cluster.mkdir()
marker = cluster / "AUDIT01K_OWNED"
marker.write_text(STAMP, encoding="utf-8")
dbdir = cluster / "data"
password = secrets.token_urlsafe(40)
pwfile = cluster / "password"
pwfile.write_text(password, encoding="utf-8")

with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]

database = "audit01k_" + secrets.token_hex(5)
pg_user = "audit01k"
started = False
configured = False
phase = "initdb"
password_good = secrets.token_urlsafe(32)
password_wrong = secrets.token_urlsafe(32)


def pg(command, *args):
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as capture:
        result = subprocess.run(
            [str(BIN / (command + ".exe")), *map(str, args)],
            stdout=capture,
            stderr=capture,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        capture.seek(0)
        diagnostic = capture.read()
    if result.returncode:
        evidence["comando_fallido"] = {
            "nombre": command,
            "codigo": result.returncode,
            "diagnostico": diagnostic.replace(password, "[SECRETO]").strip(),
        }
        raise RuntimeError(f"Falló {command}; código {result.returncode}")
    return diagnostic


def own_cluster():
    assert cluster.parent == Path(tempfile.gettempdir()).resolve()
    assert cluster.name.startswith("audit01k-pg-")
    assert marker.read_text(encoding="utf-8") == STAMP


try:
    own_cluster()
    pg(
        "initdb",
        "-D", dbdir,
        "-U", pg_user,
        "--pwfile", pwfile,
        "--auth-host=scram-sha-256",
        "--auth-local=scram-sha-256",
        "--encoding=UTF8",
        "--locale=C",
    )
    pwfile.unlink()
    phase = "arranque"
    pg(
        "pg_ctl",
        "-D", dbdir,
        "-l", cluster / "postgres.log",
        "-o", f"-h 127.0.0.1 -p {port} -c log_statement=none -c log_min_error_statement=panic",
        "-w", "start",
    )
    started = True

    import psycopg
    from psycopg import sql

    pg_config = {"host": "127.0.0.1", "port": port, "user": pg_user, "password": password}
    phase = "base"
    with psycopg.connect(**pg_config, dbname="postgres", autocommit=True) as conn:
        evidence["servidor"] = conn.execute("SELECT version()").fetchone()[0]
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))

    sys.path.insert(0, str(ROOT / "r1-pmv"))
    os.environ.update({
        "APP_ENV": "test",
        "DJANGO_DEBUG": "false",
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
        "DJANGO_SETTINGS_MODULE": "config.settings",
    })
    from config import env

    original_loader = env.load_dotenv
    env.load_dotenv = lambda path=None: None
    try:
        from django.conf import settings
        settings.DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": database,
                "USER": pg_user,
                "PASSWORD": password,
                "HOST": "127.0.0.1",
                "PORT": port,
                "CONN_MAX_AGE": 60,
                "OPTIONS": {"options": "-c statement_timeout=20000 -c lock_timeout=15000"},
            }
        }
    finally:
        env.load_dotenv = original_loader

    import django
    django.setup()
    configured = True

    from django.core.management import call_command
    from django.db import close_old_connections, connection, connections
    from django.test import Client
    from django.utils import timezone as django_timezone
    from django.utils.crypto import salted_hmac
    from identity.models import Account, LoginAttempt, Role

    phase = "migraciones"
    with connection.cursor() as cur:
        cur.execute("SELECT current_database(), current_setting('data_directory'), current_setting('transaction_isolation')")
        actual_db, actual_dir, isolation = cur.fetchone()
        assert actual_db == database and Path(actual_dir).resolve() == dbdir
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)
        call_command("check", verbosity=0)
    evidence.update({
        "base_efimera": database,
        "puerto_loopback": port,
        "isolation": isolation,
        "django": django.get_version(),
        "migraciones": "PASS",
        "check": "PASS",
    })

    seller_role, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor prueba PG"})

    def state(identifier):
        row = LoginAttempt.objects.get(pk=identifier)
        return {
            "filas": LoginAttempt.objects.filter(pk=identifier).count(),
            "fallos": row.failures,
            "locked_until": row.locked_until.isoformat() if row.locked_until else None,
        }

    def scenario(name, passwords, initial, first_insert=False, ordered=False):
        email = name + "@example.invalid"
        account = Account.objects.create_user(email, password_good, display_name="Fixture PG 01K", role=seller_role)
        identifier = salted_hmac("identity.login.throttle", email, algorithm="sha256").hexdigest()
        if initial is not None:
            LoginAttempt.objects.create(identifier=identifier, failures=initial)
        barrier = threading.Barrier(len(passwords), timeout=15)
        insert_barrier = threading.Barrier(len(passwords), timeout=15)
        first_has_row = threading.Event()
        second_entered = threading.Event()
        pids = {}
        insert_waiters = []
        observed_blocking = []

        def worker(index, raw_password):
            close_old_connections()
            client = Client(enforce_csrf_checks=True)
            get_response = client.get("/")
            token = get_response.cookies[settings.CSRF_COOKIE_NAME].value
            with connection.cursor() as cur:
                cur.execute("SELECT pg_backend_pid()")
                pids[index] = cur.fetchone()[0]
                if first_insert:
                    def trace_insert(execute, sql_text, params, many, context):
                        if "INSERT INTO" in sql_text and "identity_loginattempt" in sql_text:
                            insert_waiters.append(index)
                            insert_barrier.wait()
                        return execute(sql_text, params, many, context)
                elif ordered:
                    def trace_insert(execute, sql_text, params, many, context):
                        if "SELECT" in sql_text and "FOR UPDATE" in sql_text and "identity_loginattempt" in sql_text:
                            if index == 0:
                                result = execute(sql_text, params, many, context)
                                first_has_row.set()
                                second_entered.wait(timeout=5)
                                time.sleep(0.25)
                                return result
                            second_entered.set()
                        return execute(sql_text, params, many, context)
                else:
                    def trace_insert(execute, sql_text, params, many, context):
                        return execute(sql_text, params, many, context)

                barrier.wait()
                if ordered and index > 0:
                    assert first_has_row.wait(timeout=5)
                with connection.execute_wrapper(trace_insert):
                    response = client.post("/", {"email": email, "password": raw_password, "csrfmiddlewaretoken": token})
            text = response.content.decode("utf-8", errors="replace")
            msg = "bloqueo15" if "Demasiados intentos fallidos consecutivos." in text and "15 minuto(s)" in text else ("credenciales" if "Correo o contraseña incorrectos" in text else "")
            result = {
                "hilo": index,
                "http": response.status_code,
                "destino": response.headers.get("Location"),
                "sesion_fixture": client.session.get("_auth_user_id") == str(account.pk),
                "mensaje": msg,
            }
            connections.close_all()
            return result

        stop_monitor = threading.Event()

        def monitor_wait():
            if not ordered:
                return
            with psycopg.connect(**pg_config, dbname=database, autocommit=True) as obs:
                while not stop_monitor.is_set() and len(pids) < 2:
                    time.sleep(0.02)
                while not stop_monitor.is_set():
                    rows = obs.execute(
                        "SELECT pid, wait_event_type, wait_event, pg_blocking_pids(pid) FROM pg_stat_activity WHERE pid = ANY(%s)",
                        ([pids[0], pids[1]],),
                    ).fetchall()
                    for pid, wtype, wevent, blockers in rows:
                        if blockers:
                            observed_blocking.append({"pid": pid, "wait_event_type": wtype, "wait_event": wevent, "blocking_pids": blockers})
                            return
                    time.sleep(0.02)

        with ThreadPoolExecutor(max_workers=len(passwords) + 1) as pool:
            mon = pool.submit(monitor_wait)
            futures = [pool.submit(worker, idx, pw) for idx, pw in enumerate(passwords)]
            results = [f.result(timeout=30) for f in futures]
            stop_monitor.set()
            mon.result(timeout=5)
        current = state(identifier)
        item = {
            "escenario": name,
            "fin_utc": datetime.now(timezone.utc).isoformat(),
            "barrera_insert": len(insert_waiters),
            "espera_fila_observada_pg": bool(observed_blocking),
            "respuestas": results,
            "persistencia": current,
        }
        evidence["escenarios"].append(item)
        return item

    phase = "primera creación simultánea"
    item = scenario("primera-fila", [password_wrong] * 2, None, first_insert=True)
    assert item["barrera_insert"] == 2 and item["persistencia"]["fallos"] == 2 and item["persistencia"]["locked_until"] is None
    assert all(r["http"] == 200 and not r["sesion_fixture"] and r["mensaje"] == "credenciales" for r in item["respuestas"])
    item["resultado"] = "PASS"

    phase = "cinco fallos simultáneos"
    item = scenario("cinco-fallos", [password_wrong] * 5, 0)
    assert item["persistencia"]["fallos"] == 5
    locked = datetime.fromisoformat(item["persistencia"]["locked_until"])
    assert 899 < (locked - datetime.fromisoformat(item["fin_utc"])).total_seconds() <= 900
    assert sorted(r["mensaje"] for r in item["respuestas"]) == ["bloqueo15"] + ["credenciales"] * 4
    item["resultado"] = "PASS"

    phase = "éxito primero y fallo en espera"
    item = scenario("exito-antes-fallo", [password_good, password_wrong], 4, ordered=True)
    assert item["espera_fila_observada_pg"] and item["persistencia"]["fallos"] == 1 and item["persistencia"]["locked_until"] is None
    assert item["respuestas"][0]["http"] == 302 and item["respuestas"][0]["sesion_fixture"] and item["respuestas"][0]["destino"] == "/inicio/"
    assert item["respuestas"][1]["http"] == 200 and item["respuestas"][1]["mensaje"] == "credenciales"
    item["resultado"] = "PASS"

    phase = "quinto fallo primero y clave correcta en espera"
    item = scenario("fallo-antes-exito", [password_wrong, password_good], 4, ordered=True)
    assert item["espera_fila_observada_pg"] and item["persistencia"]["fallos"] == 5
    assert all(r["http"] == 200 and not r["sesion_fixture"] and r["mensaje"] == "bloqueo15" for r in item["respuestas"])
    item["resultado"] = "PASS"

    phase = "admin-denegado-concurrente-con-bloqueo"
    su_email = "su.concurrente.01h@example.invalid"
    su_acc = Account.objects.create_user(su_email, password_good, display_name="SU PG 01K", role=seller_role, is_staff=True, is_superuser=True)
    su_ident = salted_hmac("identity.login.throttle", su_email, algorithm="sha256").hexdigest()
    LoginAttempt.objects.create(identifier=su_ident, failures=5, locked_until=django_timezone.now() + timedelta(minutes=15))
    barrier_su = threading.Barrier(2, timeout=15)

    def su_worker(route):
        close_old_connections()
        c = Client(enforce_csrf_checks=True)
        c.get("/")
        tok = c.cookies[settings.CSRF_COOKIE_NAME].value
        barrier_su.wait()
        try:
            if route == "/":
                r = c.post("/", {"email": su_email, "password": password_good, "csrfmiddlewaretoken": tok})
            else:
                r = c.post("/admin/login/?next=/admin/", {"username": su_email, "password": password_good, "next": "/admin/", "csrfmiddlewaretoken": tok})
            return {"ruta": route, "http": r.status_code, "sesion_fixture": c.session.get("_auth_user_id") == str(su_acc.pk), "dash": c.get("/inicio/").status_code}
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        su_results = [f.result(timeout=30) for f in (pool.submit(su_worker, "/"), pool.submit(su_worker, "/admin/login/?next=/admin/"))]
    su_state = state(su_ident)
    assert su_results[0]["http"] == 200 and not su_results[0]["sesion_fixture"] and su_results[0]["dash"] == 302
    assert su_results[1]["http"] == 404 and not su_results[1]["sesion_fixture"] and su_results[1]["dash"] == 302
    assert su_state["fallos"] == 5 and su_state["locked_until"] is not None
    evidence["escenarios"].append({"escenario": "admin-denegado-concurrente", "respuestas": su_results, "persistencia": su_state, "resultado": "PASS"})

    evidence["resultado"] = "PASS, cinco escenarios"
    evidence["fuentes_sha256"] = {
        name: hashlib.sha256((ROOT / "r1-pmv" / name).read_bytes()).hexdigest()
        for name in ["identity/services.py", "identity/views.py", "identity/forms.py", "identity/models.py"]
    }
except Exception as error:
    evidence["resultado"] = "INCOMPLETO"
    evidence["fase"] = phase
    evidence["error_tipo"] = type(error).__name__
    if isinstance(error, AssertionError):
        evidence["assertion"] = str(error)
finally:
    if configured:
        connections.close_all()
    try:
        own_cluster()
        if (dbdir / "postmaster.pid").exists():
            assert Path((dbdir / "postmaster.pid").read_text(encoding="utf-8").splitlines()[1]).resolve() == dbdir
            pg("pg_ctl", "-D", dbdir, "-m", "fast", "-w", "stop")
            with socket.socket() as sock:
                sock.settimeout(1)
                assert sock.connect_ex(("127.0.0.1", port)) != 0
            evidence["limpieza"]["puerto_cerrado"] = True
        own_cluster()
        shutil.rmtree(cluster)
        evidence["limpieza"]["carpeta_propia_eliminada"] = not cluster.exists()
    except Exception as error:
        evidence["limpieza"]["error_tipo"] = type(error).__name__
        evidence["limpieza"]["carpeta_pendiente"] = str(cluster)
    evidence["fin_utc"] = datetime.now(timezone.utc).isoformat()
    OUTPUT.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "postgresql-01k-latest.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"resultado": evidence.get("resultado"), "evidencia": str(OUTPUT.relative_to(ROOT)), "limpieza": evidence["limpieza"]}, ensure_ascii=False))

sys.exit(0 if evidence.get("resultado", "").startswith("PASS") and evidence["limpieza"].get("carpeta_propia_eliminada") else 1)
