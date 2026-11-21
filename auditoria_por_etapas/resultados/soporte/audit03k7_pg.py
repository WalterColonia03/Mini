"""Optimistic product edits with verified PostgreSQL row-lock contention in a NEW owned PostgreSQL cluster, then stop.
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
CLUSTER=(Path(tempfile.gettempdir())/('audit03k7-pg-'+secrets.token_hex(12))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK=CLUSTER/'AUDIT03_OWNED';MARK.write_text(STAMP,encoding='utf-8')
DBDIR=CLUSTER/'data';PW=secrets.token_urlsafe(40)
PWFILE=CLUSTER/'password';PWFILE.write_text(PW,encoding='utf-8')
DBNAME='audit03_'+secrets.token_hex(5)
with socket.socket() as s:s.bind(('127.0.0.1',0));PORT=s.getsockname()[1]
protected=[*(ROOT/'r1-pmv').glob('*.sqlite3'),*(RESULTS/'datos').rglob('*.sqlite3'),ROOT/'PLANIFICACION_SCRUM_R1PMV.xlsx']
def state(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
hashes={str(p.relative_to(ROOT)):state(p) for p in protected}
report={'started_utc':STAMP,'cluster':str(CLUSTER),'port':PORT,'cases':[],'protected_absent_at_start':[k for k,v in hashes.items() if v is None]}
def own():
    assert CLUSTER.parent==Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith('audit03k7-pg-')
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

    from catalog.services import update_product, product_edit_snapshot
    from decimal import Decimal
    from queue import Queue
    import time

    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
        call_command('migrate',interactive=False,verbosity=0)
    with connection.cursor() as cur:
        cur.execute("SELECT current_database(),current_setting('data_directory'),current_setting('transaction_isolation')")
        db,folder,iso=cur.fetchone()
        assert db==DBNAME and Path(folder).resolve()==DBDIR
    report.update(database=db,isolation=iso)
    role=Role.objects.create(code='ADMIN',name='AUD03 ADMIN')
    actors=[Account.objects.create_user(f'admin{i}@audit03.invalid',None,display_name=f'AUD03 {i}',role=role) for i in (1,2)]
    category=Category.objects.create(name='Prueba de concurrencia K7')

    def scenario(case_id, name, barcode, winner_changes, loser_changes):
        product=Product.objects.create(category=category,name=name,barcode=barcode,sale_price=Decimal('8.50'),minimum_stock=10)
        stale=product_edit_snapshot(Product.objects.get(pk=product.pk))
        original={'name':name,'barcode':barcode,'sale_price':Decimal('8.50'),'minimum_stock':10}
        start=threading.Barrier(2,timeout=10)
        locked=threading.Event()
        release=threading.Event()
        loser_pid=Queue(maxsize=1)

        def work(index, changes):
            close_old_connections()
            try:
                actor=Account.objects.get(pk=actors[index].pk)
                current=Product.objects.get(pk=product.pk)
                assert product_edit_snapshot(current)==stale
                with connection.cursor() as cursor:
                    cursor.execute('SELECT pg_backend_pid()')
                    pid=cursor.fetchone()[0]
                start.wait()
                with transaction.atomic():
                    if index==0:
                        Product.objects.select_for_update().get(pk=product.pk)
                        locked.set()
                        if not release.wait(15):
                            raise RuntimeError('Observer did not release winner lock')
                    else:
                        if not locked.wait(10):
                            raise RuntimeError('Winner failed to acquire lock')
                        loser_pid.put(pid)
                    payload={**original,**changes}
                    update_product(actor=actor,product=current,category=category,
                                   expected_snapshot=stale,**payload)
                return {'status':'saved'}
            except ValidationError as exc:
                return {'status':'rejected','stale':exc.code=='stale_product'}
            finally:
                connections.close_all()

        observed_wait=False
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                first=pool.submit(work,0,winner_changes)
                second=pool.submit(work,1,loser_changes)
                try:
                    pid=loser_pid.get(timeout=12)
                    end=time.monotonic()+8
                    with psycopg.connect(**conf,dbname=DBNAME,autocommit=True) as observer:
                        while time.monotonic()<end:
                            state=observer.execute(
                                "SELECT wait_event_type FROM pg_stat_activity WHERE pid=%s",(pid,)
                            ).fetchone()
                            if state and state[0]=='Lock':
                                observed_wait=True
                                break
                            time.sleep(.05)
                finally:
                    release.set()
                outcomes=[first.result(timeout=20),second.result(timeout=20)]
        finally:
            release.set()
        current=Product.objects.get(pk=product.pk)
        actual={'name':current.name,'barcode':current.barcode,
                'sale_price':current.sale_price,'minimum_stock':current.minimum_stock}
        expected={**original,**winner_changes}
        report['cases'].append({
            'id':case_id,
            'ok':observed_wait and outcomes==[{'status':'saved'},{'status':'rejected','stale':True}] and actual==expected,
            'outcomes':outcomes,'row_lock_wait_observed':observed_wait,
            'final_matches_winner_only':actual==expected,
        })

    scenario('PG-K7-01-price-vs-minimum','Producto K7 precio','K7-A',
             {'sale_price':Decimal('9.20')},{'minimum_stock':17})
    scenario('PG-K7-02-code-vs-name','Producto K7 codigo','K7-B',
             {'barcode':'K7-CORREGIDO'},{'name':'Producto K7 nombre'})
except Exception as exc:
    report['error']={'type':type(exc).__name__,'message':str(exc).replace(PW,'[REDACTED]')[:800]}
finally:
    if configured:connections.close_all()
    if started:own();pg('pg_ctl','-D',DBDIR,'-m','fast','-w','stop')
    with socket.socket() as s:report['port_closed']=s.connect_ex(('127.0.0.1',PORT))!=0
    report['protected_unchanged']={str(p.relative_to(ROOT)):state(p)==hashes[str(p.relative_to(ROOT))] for p in protected}
    report['finished_utc']=datetime.now(timezone.utc).isoformat()
    out=RESULTS/'evidencias'/('03-K7-postgresql-'+STAMP+'.json')
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'evidence':str(out.relative_to(ROOT)),'cases':report['cases'],'error':report.get('error'),'port_closed':report['port_closed'],'protected_unchanged':all(report['protected_unchanged'].values())},ensure_ascii=False))
if report.get('error') or len(report['cases'])!=2 or not all(x['ok'] for x in report['cases']) or not report['port_closed'] or not all(report['protected_unchanged'].values()):raise SystemExit(1)
