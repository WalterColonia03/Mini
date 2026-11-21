"""Stage 05-J real HTTP with CSRF and concurrent initial load on PostgreSQL.
Runs in an ephemeral owned cluster (AUDIT05J_OWNED) and never alters existing SQLite DBs.
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
CLUSTER = (Path(tempfile.gettempdir()) / ("audit05j-pg-" + secrets.token_hex(12))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT05J_OWNED"
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
source_paths = [p for p in (ROOT / "r1-pmv").rglob("*")
                if p.is_file() and p.suffix in {".py", ".html", ".css", ".js"}
                and not any(part in {".venv", ".git", "__pycache__"} for part in p.parts)]
source_paths.append(Path(__file__))
source_hashes = {str(p.relative_to(ROOT)): state_hash(p) for p in source_paths}
report = {
    "started_utc": STAMP,
    "cluster": str(CLUSTER),
    "port": PORT,
    "cases": [],
    "protected_absent_at_start": [k for k, v in hashes.items() if v is None],
}


def own() -> None:
    assert CLUSTER.parent == Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith("audit05j-pg-")
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


def start_pg() -> None:
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


http_server = None
http_thread = None
http_process = None
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
    start_pg()
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

    import http.cookiejar
    import re
    import urllib.request
    import urllib.parse
    import urllib.error
    from socketserver import ThreadingMixIn
    from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server
    from django.core.wsgi import get_wsgi_application

    class ThreadedServer(ThreadingMixIn, WSGIServer):
        daemon_threads = True

    class QuietHandler(WSGIRequestHandler):
        def log_message(self, *args):
            pass

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args):
            return None

    def client():
        jar = http.cookiejar.CookieJar()
        return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar), NoRedirect()), jar

    def request(opener, route, data=None):
        encoded = urllib.parse.urlencode(data).encode() if data is not None else None
        req = urllib.request.Request(base + route, data=encoded)
        try:
            response = opener.open(req, timeout=25)
        except urllib.error.HTTPError as exc:
            response = exc
        with response:
            return response.status, response.headers.get('Location'), response.read().decode('utf8')

    def token(body):
        return re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', body).group(1)

    def check(name, actual, expected):
        report['cases'].append({'id':name,'ok':actual == expected,'actual':actual,'expected':expected})
        if actual != expected:
            raise AssertionError(name)

    def snapshot(product):
        product.refresh_from_db()
        return {'loads': InitialInventoryLoad.objects.filter(product=product).count(),
                'lines': InitialLoadLine.objects.filter(load__product=product).count(),
                'lots': list(Lot.objects.filter(product=product).order_by('number_normalized').values(
                    'number_normalized','available_quantity','unit_cost','responsible_id','initial_load_id')),
                'stock':product.physical_stock,'cost':str(product.average_cost)}

    settings.CSRF_COOKIE_SECURE = False
    settings.SESSION_COOKIE_SECURE = False
    settings.SECURE_SSL_REDIRECT = False
    settings.SESSION_COOKIE_NAME = 'audit05j_session'
    settings.CSRF_COOKIE_NAME = 'audit05j_csrf'
    role = Role.objects.create(code=Role.Code.WAREHOUSE, name='Almacenero')
    password = secrets.token_urlsafe(24)
    actors = [Account.objects.create_user(f'wh{i}@audit05j.invalid', password,
              display_name=f'Almacen HTTP {i}', role=role) for i in range(2)]
    category = Category.objects.create(name='Categoria HTTP05J')
    product = Product.objects.create(category=category, name='Carga simultanea HTTP05J',
                barcode='775050900001', sale_price=Decimal('9.00'))
    with socket.socket() as port_socket:
        port_socket.bind(('127.0.0.1', 0))
        http_port = port_socket.getsockname()[1]
    child_code = '''
import json, sys
from socketserver import ThreadingMixIn
from wsgiref.simple_server import WSGIServer, WSGIRequestHandler, make_server
config = json.loads(sys.stdin.readline())
from config import env
env.load_dotenv = lambda path=None: None
from django.conf import settings
for key, value in config['settings'].items():
    setattr(settings, key, value)
import django
django.setup()
trap = config.get('trap')
if trap:
    from django.db import connection as trap_conn
    from catalog.models import Product as TrapProduct
    orig_save = TrapProduct.save
    def trapped_save(self, *args, **kwargs):
        res = orig_save(self, *args, **kwargs)
        if str(self.pk) == trap['product_id'] and 'average_cost' in (kwargs.get('update_fields') or ()):
            with trap_conn.cursor() as cur:
                cur.execute('SELECT id FROM catalog_category WHERE id = %s FOR UPDATE', [trap['category_id']])
        return res
    TrapProduct.save = trapped_save
from django.core.wsgi import get_wsgi_application
class Server(ThreadingMixIn, WSGIServer):
    allow_reuse_address = False
    daemon_threads = True
class Quiet(WSGIRequestHandler):
    def log_message(self, *args): pass
make_server('127.0.0.1', config['port'], get_wsgi_application(), server_class=Server, handler_class=Quiet).serve_forever()
'''
    def stop_http(proc):
        if proc is None:
            return True
        if proc.poll() is None:
            proc.kill()
        proc.wait(timeout=5)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with socket.socket() as probe:
                if probe.connect_ex(('127.0.0.1', http_port)) != 0:
                    return True
            time.sleep(.05)
        with socket.socket() as probe:
            return probe.connect_ex(('127.0.0.1', http_port)) != 0

    def start_http(trap=None):
        process = subprocess.Popen([sys.executable, '-c', child_code], cwd=ROOT/'r1-pmv',
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        config = {'port': http_port, 'trap': trap, 'settings': {key: getattr(settings, key) for key in (
            'DATABASES', 'SECRET_KEY', 'ALLOWED_HOSTS', 'CSRF_COOKIE_SECURE',
            'SESSION_COOKIE_SECURE', 'SECURE_SSL_REDIRECT', 'SESSION_COOKIE_NAME', 'CSRF_COOKIE_NAME')}}
        process.stdin.write(json.dumps(config)+'\n')
        process.stdin.close()
        deadline = time.monotonic()+15
        while time.monotonic()<deadline:
            with socket.socket() as probe:
                if probe.connect_ex(('127.0.0.1', http_port)) == 0:
                    return process
            if process.poll() is not None:
                raise RuntimeError('Owned HTTP child exited during startup')
            time.sleep(.05)
        process.kill()
        process.wait(timeout=5)
        raise TimeoutError('Owned HTTP child startup')

    http_process = start_http()
    base = f'http://127.0.0.1:{http_port}'
    report['http_port'] = http_port
    clients = []
    csrf_tokens = []
    for actor in actors:
        opener, jar = client()
        status, _, body = request(opener,'/')
        check(f'login_get_{len(clients)}',status,200)
        status, location, _ = request(opener,'/',{'email':actor.email,'password':password,'csrfmiddlewaretoken':token(body)})
        check(f'login_post_{len(clients)}',(status,location),(302,'/inicio/'))
        status, _, body = request(opener,'/inventario/carga-inicial/')
        check(f'load_form_{len(clients)}',status,200)
        clients.append(opener)
        csrf_tokens.append(token(body))
    before = snapshot(product)
    future = (tz.localdate()+timedelta(days=45)).isoformat()
    payload = {'product':str(product.pk),'supplier':'','lots-TOTAL_FORMS':'2','lots-INITIAL_FORMS':'0',
        'lots-MIN_NUM_FORMS':'1','lots-MAX_NUM_FORMS':'1000',
        'lots-0-number':'HTTP-J1','lots-0-quantity':'3','lots-0-unit_cost':'1.2500','lots-0-expiration_date':future,
        'lots-1-number':'HTTP-J2','lots-1-quantity':'7','lots-1-unit_cost':'2.7500','lots-1-expiration_date':future}
    status, _, _ = request(clients[0],'/inventario/carga-inicial/',payload)
    check('missing_csrf_403',status,403)
    check('missing_csrf_no_mutation',snapshot(product),before)
    invalid = dict(payload, csrfmiddlewaretoken=csrf_tokens[0])
    invalid['lots-1-quantity']='0'
    status, _, body = request(clients[0],'/inventario/carga-inicial/',invalid)
    check('invalid_second_lot_200',status,200)
    check('invalid_second_lot_error','mayor o igual a 1' in body,True)
    check('invalid_second_lot_atomic',snapshot(product),before)

    if '--interrupt' in sys.argv or '--post-write-interrupt' in sys.argv:
        def post_form(target_payload):
            try:
                return request(clients[0], '/inventario/carga-inicial/',
                    dict(target_payload, csrfmiddlewaretoken=csrf_tokens[0]))
            except (OSError, __import__('http.client', fromlist=['HTTPException']).HTTPException) as exc:
                return (type(exc).__name__, None, '')

        if '--interrupt' in sys.argv:
            with psycopg.connect(**conf, dbname=DBNAME) as holder, psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as observer:
                holder.execute('SELECT id FROM catalog_product WHERE id=%s FOR UPDATE', [product.pk])
                with ThreadPoolExecutor(max_workers=1) as pool:
                    pending = pool.submit(lambda: post_form(payload)[0])
                    deadline = time.monotonic()+8
                    waits = []
                    while time.monotonic()<deadline:
                        waits = observer.execute("SELECT pid, pg_blocking_pids(pid) FROM pg_stat_activity WHERE datname=%s AND wait_event_type='Lock' AND query ILIKE '%%catalog_product%%'", [DBNAME]).fetchall()
                        if waits:
                            break
                        time.sleep(.025)
                    check('interruption_observed_waiter', bool(waits), True)
                    report['interruption'] = {'http_pid': http_process.pid, 'waiters': waits, 'holder_pid': holder.info.backend_pid}
                    stop_http(http_process)
                    report['interruption']['response'] = pending.result(timeout=5)
                    holder.commit()
            check('interruption_no_mutation', snapshot(product), before)
            http_process = start_http()
            status, location, _ = request(clients[0], '/inventario/carga-inicial/', dict(payload, csrfmiddlewaretoken=csrf_tokens[0]))
            check('recovery_same_session_csrf', status, 302)
            recovered = snapshot(product)
            check('recovery_one_load', recovered['loads'], 1)
            check('recovery_two_lines', recovered['lines'], 2)
            check('recovery_two_lots', len(recovered['lots']), 2)
            check('recovery_stock', recovered['stock'], 10)
            check('recovery_cost', recovered['cost'], '2.3000')
            check('recovery_receipt', request(clients[0], location)[0], 200)
            request(clients[0], '/inventario/carga-inicial/', dict(payload, csrfmiddlewaretoken=csrf_tokens[0]))
            check('recovery_replay_no_mutation', snapshot(product), recovered)
            report['interruption']['recovered'] = recovered
            product = Product.objects.create(category=category, name='Carga concurrente tras recuperacion', barcode='775050900002', sale_price=Decimal('9.00'))
            payload['product'] = str(product.pk)
            before = snapshot(product)

        # CT-ROLLBACK-01-POST-ESCRITURA / C-01 (HTTP worker killed AFTER ORM writes before COMMIT) & C-02 (PG -m immediate crash)
        trap_category = Category.objects.create(name='Trampa Barrera 05M')
        required_write_tables = {'inventory_initialinventoryload', 'inventory_lot', 'inventory_initialloadline', 'catalog_product'}

        def park_post_write(target_prod, target_payload):
            global http_process
            stop_http(http_process)
            http_process = start_http(trap={'product_id': str(target_prod.pk), 'category_id': str(trap_category.pk)})
            holder_conn = psycopg.connect(**conf, dbname=DBNAME)
            obs_conn = psycopg.connect(**conf, dbname=DBNAME, autocommit=True)
            holder_conn.execute('SELECT id FROM catalog_category WHERE id=%s FOR UPDATE', [trap_category.pk])
            holder_pid = holder_conn.info.backend_pid
            pool = ThreadPoolExecutor(max_workers=1)
            pending = pool.submit(lambda: post_form(target_payload)[0])
            deadline = time.monotonic() + 10
            wait_rows = []
            while time.monotonic() < deadline:
                wait_rows = obs_conn.execute("""
                    SELECT pid, pg_blocking_pids(pid), backend_xid::text, state, wait_event_type
                    FROM pg_stat_activity
                    WHERE datname=%s AND pid<>%s AND wait_event_type='Lock' AND query ILIKE '%%catalog_category%%'
                """, [DBNAME, holder_pid]).fetchall()
                if wait_rows:
                    break
                time.sleep(.025)
            locks = []
            visible_counts = None
            if wait_rows:
                waiter_pid = wait_rows[0][0]
                locks = obs_conn.execute("""
                    SELECT l.relation::regclass::text, l.mode, l.granted
                    FROM pg_locks l
                    WHERE l.pid=%s AND l.relation IS NOT NULL
                    ORDER BY 1, 2, 3
                """, [waiter_pid]).fetchall()
                visible_counts = {
                    'loads': obs_conn.execute("SELECT count(*) FROM inventory_initialinventoryload WHERE product_id=%s", [target_prod.pk]).fetchone()[0],
                    'lots': obs_conn.execute("SELECT count(*) FROM inventory_lot WHERE product_id=%s", [target_prod.pk]).fetchone()[0],
                    'lines': obs_conn.execute("SELECT count(*) FROM inventory_initialloadline l JOIN inventory_initialinventoryload i ON i.id=l.load_id WHERE i.product_id=%s", [target_prod.pk]).fetchone()[0],
                }
            return holder_conn, obs_conn, pool, pending, wait_rows, locks, visible_counts

        pw_product = Product.objects.create(category=category, name='Post-write HTTP Kill 05M', barcode='775050900003', sale_price=Decimal('9.00'))
        pw_before = snapshot(pw_product)
        pw_payload = dict(payload, product=str(pw_product.pk))
        holder_c1, obs_c1, pool_c1, pending_c1, wait_c1, locks_c1, vis_c1 = park_post_write(pw_product, pw_payload)
        killed_http_pid_c1 = http_process.pid
        try:
            waiter_pid_c1 = wait_c1[0][0] if wait_c1 else None
            backend_xid_c1 = wait_c1[0][2] if wait_c1 else None
            locked_tables_c1 = {rel for rel, mode, granted in locks_c1 if granted and mode == 'RowExclusiveLock'}
            check('c01_post_write_waiter_observed', bool(wait_c1) and backend_xid_c1 is not None, True)
            check('c01_post_write_row_exclusive_locks', required_write_tables.issubset(locked_tables_c1), True)
            check('c01_post_write_uncommitted_invisible', vis_c1, {'loads': 0, 'lots': 0, 'lines': 0})
            stop_http(http_process)
            resp_c1 = pending_c1.result(timeout=5)
            holder_c1.commit()
            exit_deadline = time.monotonic() + 5
            still_alive = 1
            while time.monotonic() < exit_deadline:
                still_alive = obs_c1.execute("SELECT count(*) FROM pg_stat_activity WHERE pid=%s", [waiter_pid_c1]).fetchone()[0]
                if still_alive == 0:
                    break
                time.sleep(.025)
            check('c01_pg_backend_exited_cleanly', still_alive, 0)
        finally:
            pool_c1.shutdown(wait=False)
            obs_c1.close()
            holder_c1.close()
        check('c01_post_write_kill_no_residue', snapshot(pw_product), pw_before)
        http_process = start_http()
        st_c1, loc_c1, _ = request(clients[0], '/inventario/carga-inicial/', dict(pw_payload, csrfmiddlewaretoken=csrf_tokens[0]))
        check('c01_recovery_same_session_csrf', st_c1, 302)
        pw_recovered = snapshot(pw_product)
        check('c01_recovery_one_load', pw_recovered['loads'], 1)
        check('c01_recovery_two_lines', pw_recovered['lines'], 2)
        check('c01_recovery_two_lots', len(pw_recovered['lots']), 2)
        check('c01_recovery_stock', pw_recovered['stock'], 10)
        check('c01_recovery_cost', pw_recovered['cost'], '2.3000')
        check('c01_recovery_receipt', request(clients[0], loc_c1)[0], 200)
        st_c1_replay, _, body_c1_replay = request(clients[0], '/inventario/carga-inicial/', dict(pw_payload, csrfmiddlewaretoken=csrf_tokens[0]))
        check('c01_recovery_replay_rejected', (st_c1_replay, 'ya tiene una carga inicial' in body_c1_replay), (200, True))
        check('c01_recovery_replay_no_mutation', snapshot(pw_product), pw_recovered)
        report['post_write_c01'] = {
            'killed_http_pid': killed_http_pid_c1,
            'wait_row': wait_c1,
            'locks': locks_c1,
            'uncommitted_visible': vis_c1,
            'interrupted_response': resp_c1,
            'recovered': pw_recovered,
        }

        # C-02: PG immediate crash right after writes inside transaction (before COMMIT)
        crash_product = Product.objects.create(category=category, name='Post-write PG Crash 05M', barcode='775050900004', sale_price=Decimal('9.00'))
        crash_before = snapshot(crash_product)
        crash_payload = dict(payload, product=str(crash_product.pk))
        holder_c2, obs_c2, pool_c2, pending_c2, wait_c2, locks_c2, vis_c2 = park_post_write(crash_product, crash_payload)
        try:
            backend_xid_c2 = wait_c2[0][2] if wait_c2 else None
            locked_tables_c2 = {rel for rel, mode, granted in locks_c2 if granted and mode == 'RowExclusiveLock'}
            check('c02_post_write_waiter_observed', bool(wait_c2) and backend_xid_c2 is not None, True)
            check('c02_post_write_row_exclusive_locks', required_write_tables.issubset(locked_tables_c2), True)
            check('c02_post_write_uncommitted_invisible', vis_c2, {'loads': 0, 'lots': 0, 'lines': 0})
            obs_c2.close()
            connections.close_all()
            own()
            started = False
            pg('pg_ctl', '-D', DBDIR, '-m', 'immediate', '-w', 'stop')
            resp_c2 = pending_c2.result(timeout=5)
        finally:
            pool_c2.shutdown(wait=False)
            with contextlib.suppress(Exception):
                obs_c2.close()
            stop_http(http_process)
            with contextlib.suppress(Exception):
                holder_c2.close()
        start_pg()
        started = True
        check('c02_pg_crash_no_residue', snapshot(crash_product), crash_before)
        check('c02_prior_commit_durable', snapshot(pw_product), pw_recovered)
        http_process = start_http()
        st_c2, loc_c2, _ = request(clients[0], '/inventario/carga-inicial/', dict(crash_payload, csrfmiddlewaretoken=csrf_tokens[0]))
        check('c02_recovery_same_session_csrf', st_c2, 302)
        crash_recovered = snapshot(crash_product)
        check('c02_recovery_one_load', crash_recovered['loads'], 1)
        check('c02_recovery_two_lines', crash_recovered['lines'], 2)
        check('c02_recovery_stock', crash_recovered['stock'], 10)
        check('c02_recovery_cost', crash_recovered['cost'], '2.3000')
        check('c02_recovery_receipt', request(clients[0], loc_c2)[0], 200)
        st_c2_replay, _, _ = request(clients[0], '/inventario/carga-inicial/', dict(crash_payload, csrfmiddlewaretoken=csrf_tokens[0]))
        check('c02_recovery_replay_rejected', st_c2_replay, 200)
        check('c02_recovery_replay_no_mutation', snapshot(crash_product), crash_recovered)
        report['post_write_c02'] = {
            'wait_row': wait_c2,
            'locks': locks_c2,
            'uncommitted_visible': vis_c2,
            'interrupted_response': resp_c2,
            'recovered': crash_recovered,
        }

    barrier = threading.Barrier(3,timeout=10)
    def submit(index):
        barrier.wait()
        started_at=time.monotonic()
        status, location, body=request(clients[index],'/inventario/carga-inicial/',dict(payload,csrfmiddlewaretoken=csrf_tokens[index]))
        return {'actor':str(actors[index].pk),'status':status,'location':location,
                'rejected_message':'ya tiene una carga inicial' in body,
                'started':started_at,'finished':time.monotonic()}

    # Hold the exact product row so both real requests must overlap at its lock.
    with psycopg.connect(**conf,dbname=DBNAME) as holder, psycopg.connect(**conf,dbname=DBNAME,autocommit=True) as observer:
        holder.execute('SELECT id FROM catalog_product WHERE id=%s FOR UPDATE',[product.pk])
        holder_pid=holder.info.backend_pid
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(submit,i) for i in range(2)]
            barrier.wait()
            waits=[]
            deadline=time.monotonic()+8
            while time.monotonic()<deadline:
                waits=observer.execute("""SELECT pid,pg_blocking_pids(pid),wait_event_type
                    FROM pg_stat_activity WHERE datname=%s AND wait_event_type='Lock'
                    AND query ILIKE '%%catalog_product%%' AND pid<>%s""",[DBNAME,holder_pid]).fetchall()
                if len(waits)>=2:
                    break
                time.sleep(.025)
            report['overlapping_requests']={'holder_pid':holder_pid,'waiters':waits,'product_id':str(product.pk)}
            holder.commit()
            responses=[f.result() for f in futures]
    check('two_requests_observed_waiting',len(waits)>=2,True)
    report['responses']=responses
    check('one_redirect_one_rejection',sorted(r['status'] for r in responses),[200,302])
    check('loser_explained',next(r for r in responses if r['status']==200)['rejected_message'],True)
    after=snapshot(product)
    report['before']=before
    report['after']=after
    check('one_load',after['loads'],1)
    check('two_lines',after['lines'],2)
    check('two_lots',len(after['lots']),2)
    check('stock_ten',after['stock'],10)
    check('weighted_cost',after['cost'],'2.3000')
    winner=next(r for r in responses if r['status']==302)
    check('all_lots_responsible_winner',all(str(l['responsible_id'])==winner['actor'] for l in after['lots']),True)
    for index in range(2):
        status, _, body = request(clients[index],'/inventario/carga-inicial/',dict(payload,csrfmiddlewaretoken=csrf_tokens[index]))
        check(f'replay_status_{index}',status,200)
        check(f'replay_message_{index}','ya tiene una carga inicial' in body,True)
        check(f'replay_snapshot_{index}',snapshot(product),after)
        status, _, body=request(clients[index],winner['location'])
        check(f'receipt_{index}',status,200)
        check(f'receipt_cost_{index}','S/ 2,30' in body,True)
except Exception as exc:
    report['error']={'type':type(exc).__name__,'message':str(exc).replace(PW,'[REDACTED]')[:300]}
finally:
    if http_process:
        report['http_closed'] = stop_http(http_process)
    if http_server:
        http_server.shutdown()
        http_server.server_close()
        http_thread.join(timeout=5)
        with socket.socket() as sock:
            report['http_closed']=sock.connect_ex(('127.0.0.1',http_port))!=0
    if configured:
        connections.close_all()
    if started:
        own()
        pg('pg_ctl','-D',DBDIR,'-m','fast','-w','stop')
    with socket.socket() as sock:
        report['pg_closed']=sock.connect_ex(('127.0.0.1',PORT))!=0
    report['protected_unchanged']={str(p.relative_to(ROOT)):state_hash(p)==hashes[str(p.relative_to(ROOT))] for p in protected}
    report['finished_utc']=datetime.now(timezone.utc).isoformat()
    report['source_manifest'] = {'before':source_hashes,
        'changed_during_run':[name for name, digest in source_hashes.items()
                              if state_hash(ROOT / name) != digest]}
    output=RESULTS/'evidencias'/('05-J-network-'+STAMP+'.json')
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding='utf8')
    print(json.dumps({'evidence':str(output.relative_to(ROOT)),'checks':len(report['cases']),
        'error':report.get('error'),'http_closed':report.get('http_closed'),'pg_closed':report.get('pg_closed'),
        'protected_unchanged':all(report['protected_unchanged'].values())},ensure_ascii=False))
if report.get('error') or not report.get('http_closed') or not report.get('pg_closed') or not all(report['protected_unchanged'].values()):
    raise SystemExit(1)
