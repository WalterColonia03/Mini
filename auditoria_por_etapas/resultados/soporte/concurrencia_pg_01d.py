"""E01-PG-01. Clúster PostgreSQL desechable y solicitudes Django reales.

Desde la raíz:
  ./r1-pmv/.venv/Scripts/python.exe -B ./auditoria_por_etapas/resultados/soporte/concurrencia_pg_01d.py
Necesita PostgreSQL 18 instalado y psycopg del proyecto. No usa Docker ni .env.
Cada ejecución migra sólo su base efímera, verifica su ruta y elimina su clúster.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[3]
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
EVIDENCE = ROOT / "auditoria_por_etapas/resultados/evidencias"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
output = EVIDENCE / f"01-D-postgresql-{STAMP}.json"
evidence = {
    "caso": "E01-PG-01", "inicio_utc": datetime.now(timezone.utc).isoformat(),
    "herramienta": "PostgreSQL nativo efímero / Django Client CSRF / conexiones por hilo",
    "docker": "Motor Docker Desktop no disponible; se usa binario local ya instalado.",
    "escenarios": [], "limpieza": {},
}
# Use normal inherited directory permissions for PostgreSQL's restricted child process.
# tempfile.mkdtemp uses mode 0700, which prevents initdb reading its own password on Windows.
cluster = (Path(tempfile.gettempdir()) / ("audit01-pg-" + secrets.token_hex(12))).resolve()
cluster.mkdir()
marker = cluster / "AUDIT01_OWNED"
marker.write_text(STAMP, encoding="utf-8")
dbdir = cluster / "data"
password = secrets.token_urlsafe(40)
pwfile = cluster / "password"
pwfile.write_text(password, encoding="utf-8")
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
database = "audit01_" + secrets.token_hex(5)
pg_user = "audit01"
started = False
configured = False
phase = "initdb"
password_good = secrets.token_urlsafe(32)
password_wrong = secrets.token_urlsafe(32)


def pg(command, *args):
    # A server started by pg_ctl may inherit pipe handles on Windows. A file keeps
    # subprocess.run from waiting for the entire server lifetime to reach EOF.
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as capture:
        result = subprocess.run(
            [str(BIN / (command + ".exe")), *map(str, args)],
            stdout=capture, stderr=capture, timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        capture.seek(0)
        diagnostic = capture.read()
    if result.returncode:
        evidence["comando_fallido"] = {"nombre": command, "codigo": result.returncode,
                                      "diagnostico": diagnostic.replace(password, "[SECRETO]").strip()}
        raise RuntimeError("Falló " + command + "; código " + str(result.returncode))
    return diagnostic


def own_cluster():
    assert cluster.parent == Path(tempfile.gettempdir()).resolve()
    assert cluster.name.startswith("audit01-pg-")
    assert marker.read_text(encoding="utf-8") == STAMP


try:
    own_cluster()
    pg("initdb", "-D", dbdir, "-U", pg_user, "--pwfile", pwfile,
       "--auth-host=scram-sha-256", "--auth-local=scram-sha-256",
       "--encoding=UTF8", "--locale=C")
    pwfile.unlink()
    phase = "arranque"
    pg("pg_ctl", "-D", dbdir, "-l", cluster / "postgres.log", "-o",
       f"-h 127.0.0.1 -p {port} -c log_statement=none -c log_min_error_statement=panic", "-w", "start")
    started = True
    import psycopg
    from psycopg import sql
    pg_config = {"host": "127.0.0.1", "port": port, "user": pg_user, "password": password}
    phase = "base"
    with psycopg.connect(**pg_config, dbname="postgres", autocommit=True) as conn:
        assert Path(conn.execute("SHOW data_directory").fetchone()[0]).resolve() == dbdir
        evidence["servidor"] = conn.execute("SELECT version()").fetchone()[0]
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    sys.path.insert(0, str(ROOT / "r1-pmv"))
    os.environ.update({"APP_ENV": "test", "DJANGO_DEBUG": "false",
                       "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
                       "DJANGO_SETTINGS_MODULE": "config.settings"})
    from config import env
    original_loader = env.load_dotenv
    env.load_dotenv = lambda path=None: None
    from django.conf import settings
    settings.DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql", "NAME": database,
        "USER": pg_user, "PASSWORD": password, "HOST": "127.0.0.1", "PORT": port,
        "CONN_MAX_AGE": 60, "OPTIONS": {"options": "-c statement_timeout=20000 -c lock_timeout=15000"},
    }}
    env.load_dotenv = original_loader
    import django
    django.setup()
    configured = True
    from django.db import connection, connections, close_old_connections
    from django.core.management import call_command
    from django.test import Client
    from django.utils import timezone as django_timezone
    from django.utils.crypto import salted_hmac
    from identity.models import Account, Role, LoginAttempt
    phase = "migraciones"
    with connection.cursor() as cur:
        cur.execute("SELECT current_database(), current_setting('data_directory'), current_setting('transaction_isolation')")
        actual_db, actual_dir, isolation = cur.fetchone()
        assert actual_db == database and Path(actual_dir).resolve() == dbdir
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)
        call_command("check", verbosity=0)
    evidence.update({"base_efimera": database, "puerto_loopback": port, "isolation": isolation,
                     "django": django.get_version(), "migraciones": "PASS", "check": "PASS"})
    role, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor prueba PG"})

    def state(identifier):
        row = LoginAttempt.objects.get(pk=identifier)
        return {"filas": LoginAttempt.objects.filter(pk=identifier).count(),
                "fallos": row.failures, "locked_until": row.locked_until.isoformat() if row.locked_until else None}

    def scenario(name, passwords, initial, first_insert=False, ordered=False):
        email = name + "@example.invalid"
        account = Account.objects.create_user(email, password_good, display_name="Fixture PG", role=role)
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

        def worker(index, submitted):
            close_old_connections()
            client = Client(enforce_csrf_checks=True)
            assert client.get("/").status_code == 200
            token = client.cookies[settings.CSRF_COOKIE_NAME].value
            with connection.cursor() as cur:
                cur.execute("SELECT pg_backend_pid()")
                pids[index] = cur.fetchone()[0]
            seen_insert = False
            def schedule(execute, query, params, many, context):
                nonlocal seen_insert
                if first_insert and not seen_insert and query.startswith('INSERT INTO "identity_loginattempt"'):
                    seen_insert = True
                    insert_waiters.append(index)
                    insert_barrier.wait()
                is_row_lock = 'FROM "identity_loginattempt"' in query and "FOR UPDATE" in query
                if ordered and is_row_lock and index == 1:
                    second_entered.set()
                value = execute(query, params, many, context)
                if ordered and is_row_lock and index == 0:
                    first_has_row.set()
                    assert second_entered.wait(10)
                    deadline = time.monotonic() + 10
                    while time.monotonic() < deadline:
                        with connection.cursor() as cur:
                            cur.execute("SELECT pg_blocking_pids(%s)", [pids[1]])
                            blockers = cur.fetchone()[0]
                        if pids[0] in blockers:
                            observed_blocking.append(True)
                            break
                        time.sleep(0.02)
                    assert observed_blocking, "No se observó la espera PostgreSQL"
                return value
            barrier.wait()
            if ordered and index == 1:
                assert first_has_row.wait(10)
            start = time.monotonic_ns()
            try:
                with connection.execute_wrapper(schedule):
                    response = client.post("/", {
                        "email": email, "password": submitted, "csrfmiddlewaretoken": token,
                    })
                body = response.content.decode()
                message = "bloqueo15" if "15 minuto(s)" in body else "credenciales" if "Correo o contraseña incorrectos" in body else None
                session = client.session
                return {"indice": index, "http": response.status_code, "mensaje": message,
                        "sesion_fixture": session.get("_auth_user_id") == str(account.pk),
                        "destino": response.get("Location"), "duracion_ms": round((time.monotonic_ns()-start)/1e6, 3)}
            finally:
                connections.close_all()
        before = django_timezone.now()
        with ThreadPoolExecutor(max_workers=len(passwords)) as pool:
            futures = [pool.submit(worker, i, pw) for i, pw in enumerate(passwords)]
            results = [future.result(timeout=30) for future in futures]
        after = django_timezone.now()
        current = state(identifier)
        assert len(set(pids.values())) == len(passwords), "Conexiones reutilizadas entre hilos"
        assert current["filas"] == 1
        item = {"escenario": name, "inicio_utc": before.isoformat(), "fin_utc": after.isoformat(),
                "conexiones_distintas": len(set(pids.values())), "inicial_fallos": initial,
                "barrera_insert": len(insert_waiters), "espera_fila_observada_pg": bool(observed_blocking),
                "respuestas": results, "persistencia": current}
        evidence["escenarios"].append(item)
        return item

    phase = "primera creación simultánea"
    item = scenario("primera-fila", [password_wrong]*2, None, first_insert=True)
    assert item["barrera_insert"] == 2 and item["persistencia"]["fallos"] == 2
    assert item["persistencia"]["locked_until"] is None
    assert all(r["http"] == 200 and not r["sesion_fixture"] and r["mensaje"] == "credenciales" for r in item["respuestas"])
    item["resultado"] = "PASS"
    phase = "cinco fallos simultáneos"
    item = scenario("cinco-fallos", [password_wrong]*5, 0)
    assert item["persistencia"]["fallos"] == 5
    locked = datetime.fromisoformat(item["persistencia"]["locked_until"])
    assert 899 < (locked-datetime.fromisoformat(item["fin_utc"])).total_seconds() <= 900
    assert sorted(r["mensaje"] for r in item["respuestas"]) == ["bloqueo15"]+["credenciales"]*4
    assert all(r["http"] == 200 and not r["sesion_fixture"] for r in item["respuestas"])
    item["resultado"] = "PASS"
    phase = "éxito primero y fallo en espera"
    item = scenario("exito-antes-fallo", [password_good, password_wrong], 4, ordered=True)
    assert item["espera_fila_observada_pg"]
    assert item["persistencia"]["fallos"] == 1 and item["persistencia"]["locked_until"] is None
    assert item["respuestas"][0]["http"] == 302 and item["respuestas"][0]["sesion_fixture"]
    assert item["respuestas"][0]["destino"] == "/inicio/"
    assert item["respuestas"][1]["http"] == 200 and item["respuestas"][1]["mensaje"] == "credenciales"
    item["resultado"] = "PASS"
    phase = "quinto fallo primero y clave correcta en espera"
    item = scenario("fallo-antes-exito", [password_wrong, password_good], 4, ordered=True)
    assert item["espera_fila_observada_pg"] and item["persistencia"]["fallos"] == 5
    assert all(r["http"] == 200 and not r["sesion_fixture"] and r["mensaje"] == "bloqueo15" for r in item["respuestas"])
    item["resultado"] = "PASS"
    evidence["resultado"] = "PASS, cuatro escenarios"
    evidence["fuentes_sha256"] = {name: hashlib.sha256((ROOT/"r1-pmv"/name).read_bytes()).hexdigest()
                                  for name in ["identity/services.py", "identity/views.py", "identity/models.py"]}
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
            assert Path((dbdir/"postmaster.pid").read_text(encoding="utf-8").splitlines()[1]).resolve() == dbdir
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
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"resultado": evidence.get("resultado"), "evidencia": str(output.relative_to(ROOT)),
                      "limpieza": evidence["limpieza"]}, ensure_ascii=False))
sys.exit(0 if evidence.get("resultado", "").startswith("PASS") and evidence["limpieza"].get("carpeta_propia_eliminada") else 1)
