"""Product state concurrency checks in a NEW owned PostgreSQL cluster, then stop.
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
CLUSTER=(Path(tempfile.gettempdir())/('audit03e-pg-'+secrets.token_hex(12))).resolve()
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
    assert CLUSTER.parent==Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith('audit03e-pg-')
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
    from catalog.services import toggle_product_availability
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):call_command('migrate',interactive=False,verbosity=0)
    with connection.cursor() as cur:
        cur.execute("SELECT current_database(),current_setting('data_directory'),current_setting('transaction_isolation')")
        db,folder,iso=cur.fetchone();assert db==DBNAME and Path(folder).resolve()==DBDIR
    report.update(database=db,isolation=iso)
    role=Role.objects.create(code='ADMIN',name='AUD03 ADMIN')
    actor=Account.objects.create_user('admin@audit03.invalid',None,display_name='AUD03',role=role)
    from decimal import Decimal
    settings.ALLOWED_HOSTS = ['testserver', '127.0.0.1']
    from django.test import Client
    from django.urls import reverse

    category = Category.objects.create(name='Conservas')
    product = Product.objects.create(category=category, name='Prueba concurrente', barcode='PG-E', sale_price=Decimal('8.50'))

    def race(case, target, starting, expected, category_case=False):
        article = category if category_case else product
        model = Category if category_case else Product
        route = 'category-toggle' if category_case else 'product-toggle'
        table = '"catalog_category"' if category_case else '"catalog_product"'
        model.objects.filter(pk=article.pk).update(is_active=starting)
        barrier = threading.Barrier(2, timeout=10)
        def work(number):
            close_old_connections()
            lock_reached = False
            def coordinate(execute, query, params, many, context):
                nonlocal lock_reached
                if not lock_reached and table in query and 'FOR UPDATE' in query:
                    lock_reached = True
                    barrier.wait()
                return execute(query, params, many, context)
            try:
                client = Client()
                client.force_login(Account.objects.get(pk=actor.pk))
                payload = {} if target is None else {'is_active': target}
                with connection.execute_wrapper(coordinate):
                    response = client.post(reverse(route, args=[article.pk]), payload)
                return {'status': response.status_code, 'lock_reached': lock_reached}
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses=list(pool.map(work, range(2)))
        article.refresh_from_db()
        report['cases'].append({'id':case,'ok':all(x=={'status':302,'lock_reached':True} for x in statuses) and article.is_active==expected,
                                'statuses':statuses,'final_active':article.is_active})

    # These requests express the same button action and must converge.
    race('PG-E01-disable-twice', 'false', True, False)
    race('PG-E02-enable-twice', 'true', False, True)
    race('PG-E05-category-disable-twice', 'false', True, False, category_case=True)
    race('PG-E06-category-enable-twice', 'true', False, True, category_case=True)
    # Old callers without an explicit target retain their toggle operation.
    first = Product.objects.get(pk=product.pk)
    second = Product.objects.get(pk=product.pk)
    toggle_product_availability(actor=actor, product=first)
    toggle_product_availability(actor=actor, product=second)
    product.refresh_from_db()
    report['cases'].append({'id':'PG-E03-stale-legacy-toggle','ok':product.is_active})
    report['cases'].append({'id':'PG-E04-other-fields','ok':product.sale_price==Decimal('8.50')
        and product.category_id==category.pk and product.name=='Prueba concurrente' and product.physical_stock==0})
except Exception as exc:
    report['error']={'type':type(exc).__name__,'message':str(exc).replace(PW,'[REDACTED]')[:800]}
finally:
    if configured:connections.close_all()
    if started:own();pg('pg_ctl','-D',DBDIR,'-m','fast','-w','stop')
    with socket.socket() as s:report['port_closed']=s.connect_ex(('127.0.0.1',PORT))!=0
    report['protected_unchanged']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))] for p in protected}
    report['finished_utc']=datetime.now(timezone.utc).isoformat()
    out=RESULTS/'evidencias'/('03-E-postgresql-'+STAMP+'.json');out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'evidence':str(out.relative_to(ROOT)),'cases':report['cases'],'error':report.get('error'),'port_closed':report['port_closed'],'protected_unchanged':all(report['protected_unchanged'].values())},ensure_ascii=False))
if report.get('error') or not all(x['ok'] for x in report['cases']) or not report['port_closed'] or not all(report['protected_unchanged'].values()):raise SystemExit(1)
