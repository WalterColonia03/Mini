"""Business registration checks and simultaneous product submissions in a NEW owned PostgreSQL cluster, then stop.
No production settings, no reuse or deletion of existing clusters/databases.
"""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parents[3]
RESULTS=ROOT/'auditoria_por_etapas/resultados'
BIN=Path('C:/Program Files/PostgreSQL/18/bin')
STAMP=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
CLUSTER=(Path(tempfile.gettempdir())/('audit03c-pg-'+secrets.token_hex(12))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK=CLUSTER/'AUDIT03_OWNED';MARK.write_text(STAMP,encoding='utf-8')
DBDIR=CLUSTER/'data';PW=secrets.token_urlsafe(40)
PWFILE=CLUSTER/'password';PWFILE.write_text(PW,encoding='utf-8')
DBNAME='audit03_'+secrets.token_hex(5)
with socket.socket() as s:s.bind(('127.0.0.1',0));PORT=s.getsockname()[1]
protected=[*(ROOT/'r1-pmv').glob('*.sqlite3'),*(RESULTS/'datos').rglob('*.sqlite3'),ROOT/'PLANIFICACION_SCRUM_R1PMV.xlsx']
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
report={'started_utc':STAMP,'cluster':str(CLUSTER),'port':PORT,'cases':[]}
def own():
    assert CLUSTER.parent==Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith('audit03c-pg-')
    assert MARK.read_text(encoding='utf-8')==STAMP
def pg(name,*args):
    with tempfile.TemporaryFile(mode='w+',encoding='utf-8',errors='replace') as f:
        result=subprocess.run([str(BIN/(name+'.exe')),*map(str,args)],stdout=f,stderr=f,timeout=50,creationflags=subprocess.CREATE_NO_WINDOW)
        f.seek(0);diagnostic=f.read().replace(PW,'[REDACTED]')
    if result.returncode: raise RuntimeError(name+' failed: '+diagnostic[-800:])
started=False;configured=False
try:
    own();pg('initdb','-D',DBDIR,'-U','audit03','--pwfile',PWFILE,'--auth-host=scram-sha-256','--auth-local=scram-sha-256','--encoding=UTF8','--locale=C')
    PWFILE.unlink()
    pg('pg_ctl','-D',DBDIR,'-l',CLUSTER/'postgres.log','-o',f'-h 127.0.0.1 -p {PORT} -c log_statement=none -c log_min_error_statement=panic','-w','start');started=True
    import psycopg
    from psycopg import sql
    conf={'host':'127.0.0.1','port':PORT,'user':'audit03','password':PW}
    with psycopg.connect(**conf,dbname='postgres',autocommit=True) as conn:
        assert Path(conn.execute('SHOW data_directory').fetchone()[0]).resolve()==DBDIR
        report['version']=conn.execute('SELECT version()').fetchone()[0]
        conn.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(DBNAME)))
    sys.path.insert(0,str(ROOT/'r1-pmv'))
    os.environ.update(APP_ENV='test',DJANGO_DEBUG='false',DJANGO_SECRET_KEY=secrets.token_urlsafe(48),DJANGO_SETTINGS_MODULE='config.settings')
    from config import env
    loader=env.load_dotenv;env.load_dotenv=lambda path=None:None
    from django.conf import settings
    settings.DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':DBNAME,'USER':'audit03','PASSWORD':PW,'HOST':'127.0.0.1','PORT':PORT,'CONN_MAX_AGE':0,'OPTIONS':{'options':'-c statement_timeout=20000 -c lock_timeout=12000'}}}
    env.load_dotenv=loader
    import django;django.setup();configured=True
    from django.db import connection,connections,close_old_connections,transaction
    from django.core.management import call_command
    from django.core.exceptions import ValidationError
    from identity.models import Account,Role
    from catalog.models import Category, Product
    from catalog.services import register_canned_product
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):call_command('migrate',interactive=False,verbosity=0)
    with connection.cursor() as cur:
        cur.execute("SELECT current_database(),current_setting('data_directory'),current_setting('transaction_isolation')")
        db,folder,iso=cur.fetchone();assert db==DBNAME and Path(folder).resolve()==DBDIR
    report.update(database=db,isolation=iso)
    role=Role.objects.create(code='ADMIN',name='AUD03 ADMIN')
    actor=Account.objects.create_user('admin@audit03.invalid',None,display_name='AUD03',role=role)
    from decimal import Decimal

    canned = Category.objects.create(name='Productos enlatados')
    other = Category.objects.create(name='Otra activa')

    def register(name, barcode, category):
        return register_canned_product(
            actor=actor, name=name, barcode=barcode, category=category,
            unit='UND', sale_price=Decimal('8.50'), minimum_stock=None,
        )

    def race(case, articles, expected_created, synchronize_insert):
        barrier = threading.Barrier(2, timeout=10)
        def work(article):
            close_old_connections()
            reached = False
            def coordinate(execute, query, params, many, context):
                nonlocal reached
                if synchronize_insert and not reached and query.startswith('INSERT INTO "catalog_product"'):
                    reached = True
                    barrier.wait()
                return execute(query, params, many, context)
            try:
                name, barcode, category_id = article
                category = Category.objects.get(pk=category_id)
                if not synchronize_insert:
                    reached = True
                    barrier.wait()
                with connection.execute_wrapper(coordinate):
                    product = register(name, barcode, category)
                return {'status': 'created', 'code': product.barcode_normalized, 'barrier': reached}
            except ValidationError as exc:
                return {'status': 'rejected', 'fields': exc.message_dict, 'barrier': reached}
            finally:
                connections.close_all()
        before = Product.objects.count()
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(work, articles))
        delta = Product.objects.count() - before
        ok = delta == expected_created and all(o['barrier'] for o in outcomes)
        ok = ok and sum(o['status'] == 'created' for o in outcomes) == expected_created
        if expected_created == 1:
            ok = ok and any(o.get('fields', {}).get('barcode') == ['Ya existe un producto con este código de barras.'] for o in outcomes)
        report['cases'].append({'id': case, 'ok': ok, 'outcomes': outcomes, 'new_rows': delta})

    race('PG-C01-code-collision', [('A', 'Ac 010', canned.pk), ('B', ' a C010 ', other.pk)], 1, True)
    race('PG-C02-same-category-new-codes', [('C', 'C-1', canned.pk), ('D', 'C-2', canned.pk)], 2, False)
    products = list(Product.objects.all())
    report['cases'].append({'id': 'PG-C03-stored', 'ok': len(products) == 3 and all(
        p.minimum_stock == 10 and p.sale_price == Decimal('8.50') and p.controls_expiration
        and p.physical_stock == 0 and not p.is_sellable for p in products)})
    stale = Category.objects.create(name='Anteriormente activa')
    Category.objects.filter(pk=stale.pk).update(is_active=False)
    before = Product.objects.count()
    try:
        register('Registro tardío', 'STALE', stale)
        errors = {}
    except ValidationError as exc:
        errors = exc.message_dict
    report['cases'].append({'id': 'PG-C04-suspended-after-selection', 'ok': bool(errors.get('category')) and
        Product.objects.count()==before, 'new_rows': Product.objects.count()-before, 'errors': errors})

    # Wait until PostgreSQL itself reports that the registration is waiting
    # for the category update. Committing then makes the suspension visible.
    import queue
    import time
    category = Category.objects.create(name='Cambio en curso')
    pids = queue.Queue()
    def delayed_registration():
        close_old_connections()
        try:
            with connection.cursor() as cur:
                cur.execute('SELECT pg_backend_pid()')
                pids.put(cur.fetchone()[0])
            register('Alta durante suspensión', 'DURANTE', category)
            return {}
        except ValidationError as exc:
            return exc.message_dict
        finally:
            connections.close_all()
    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic(), connection.cursor() as cur:
            Category.objects.filter(pk=category.pk).update(is_active=False)
            pending = pool.submit(delayed_registration)
            worker_pid = pids.get(timeout=5)
            deadline = time.monotonic()+5
            blocked = False
            while time.monotonic() < deadline and not pending.done():
                cur.execute('SELECT pg_backend_pid() = ANY(pg_blocking_pids(%s))', [worker_pid])
                if cur.fetchone()[0]:
                    blocked = True
                    break
                time.sleep(.02)
        errors = pending.result(timeout=10)
    report['cases'].append({'id':'PG-C05-suspension-in-flight','ok':blocked and bool(errors.get('category')) and
        not Product.objects.filter(barcode='DURANTE').exists(),'blocking_observed':blocked,'errors':errors})

    from catalog.forms import ProductRegistrationForm
    # Two already validated forms, different barcodes. Measure the extra
    # name guard separately from the guaranteed unique barcode.
    forms = [ProductRegistrationForm(data={'category': str(canned.pk), 'name': 'Nombre compartido', 'barcode': code,
        'unit':'UND','minimum_stock':'','sale_price':'8.50'}) for code in ['NOM-1', 'NOM-2']]
    both_valid = all(form.is_valid() for form in forms)
    if both_valid:
        for form in forms:
            register_canned_product(actor=actor, **form.cleaned_data)
    report['observations'] = [{'id':'PG-C06-prevalidated-names','both_valid':both_valid,
        'stored':Product.objects.filter(search_name=Product.normalize_search_name('Nombre compartido')).count()}]
except Exception as exc:
    report['error']={'type':type(exc).__name__,'message':str(exc).replace(PW,'[REDACTED]')[:800]}
finally:
    if configured:connections.close_all()
    if started:own();pg('pg_ctl','-D',DBDIR,'-m','fast','-w','stop')
    with socket.socket() as s:report['port_closed']=s.connect_ex(('127.0.0.1',PORT))!=0
    report['protected_unchanged']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))] for p in protected}
    report['finished_utc']=datetime.now(timezone.utc).isoformat()
    out=RESULTS/'evidencias'/('03-C-postgresql-'+STAMP+'.json');out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'evidence':str(out.relative_to(ROOT)),'cases':report['cases'],'error':report.get('error'),'port_closed':report['port_closed'],'protected_unchanged':all(report['protected_unchanged'].values())},ensure_ascii=False))
if report.get('error') or not all(x['ok'] for x in report['cases']) or not report['port_closed'] or not all(report['protected_unchanged'].values()):raise SystemExit(1)
