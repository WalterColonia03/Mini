"""Verify catalogue reads, Unicode search and a legacy product migration in a fresh owned PostgreSQL cluster.
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
CLUSTER=(Path(tempfile.gettempdir())/('audit03b-pg-'+secrets.token_hex(12))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK=CLUSTER/'AUDIT03B_OWNED';MARK.write_text(STAMP,encoding='utf-8')
DBDIR=CLUSTER/'data';PW=secrets.token_urlsafe(40)
PWFILE=CLUSTER/'password';PWFILE.write_text(PW,encoding='utf-8')
DBNAME='audit03_'+secrets.token_hex(5)
with socket.socket() as s:s.bind(('127.0.0.1',0));PORT=s.getsockname()[1]
protected=[*(ROOT/'r1-pmv').glob('*.sqlite3'),*(RESULTS/'datos').rglob('*.sqlite3'),ROOT/'PLANIFICACION_SCRUM_R1PMV.xlsx']
hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
report={'started_utc':STAMP,'cluster':str(CLUSTER),'port':PORT,'cases':[]}
def own():
    assert CLUSTER.parent==Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith('audit03b-pg-')
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
    from catalog.models import Category
    from catalog.services import create_category
    from django.db.migrations.executor import MigrationExecutor
    executor = MigrationExecutor(connection)
    old_target = [('catalog', '0003_normalize_category_spaces')]
    executor.migrate(old_target)
    historical = executor.loader.project_state(old_target).apps
    old_category = historical.get_model('catalog', 'Category').objects.create(
        name='Legado', name_normalized='legado'
    )
    old_product = historical.get_model('catalog', 'Product').objects.create(
        name='Piña anterior', barcode='ANTERIOR', barcode_normalized='anterior',
        category=old_category, sale_price='2.50'
    )
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):call_command('migrate',interactive=False,verbosity=0)
    with connection.cursor() as cur:
        cur.execute("SELECT current_database(),current_setting('data_directory'),current_setting('transaction_isolation')")
        db,folder,iso=cur.fetchone();assert db==DBNAME and Path(folder).resolve()==DBDIR
    report.update(database=db,isolation=iso)
    role=Role.objects.create(code='ADMIN',name='AUD03 ADMIN')
    actor=Account.objects.create_user('admin@audit03.invalid',None,display_name='AUD03',role=role)
    import logging
    logging.disable(logging.CRITICAL)
    from datetime import timedelta
    from decimal import Decimal
    from django.test import Client
    from django.utils import timezone as dtz
    from catalog.models import Product
    from inventory.models import InitialInventoryLoad,Lot
    from catalog.test_audit03_catalogue import CatalogueTable
    category=Category.objects.create(name='AUD03B PG')
    product=Product.objects.create(category=category,name='AUD03B Atún clásico',barcode='AUD03B-ACCENT',sale_price=Decimal('8.50'))
    load=InitialInventoryLoad.objects.create(product=product,responsible=actor)
    today=dtz.localdate()
    for index,(qty,offset) in enumerate([(4,1),(5,2),(50,-1),(3,0)]):
        Lot.objects.create(product=product,initial_load=load,number=f'PG-{index}',initial_quantity=qty,available_quantity=qty,unit_cost=Decimal('1.00'),expiration_date=today+timedelta(days=offset))
    client=Client(raise_request_exception=False);client.force_login(actor)
    before=list(Lot.objects.order_by('pk').values('id','available_quantity'))
    response=client.get('/productos/',{'q':'AUD03B-ACCENT'})
    table=CatalogueTable(response.content.decode())
    report['cases'].append({'id':'PG03B-stock-dates','ok':response.status_code==200 and table.rows[0].get('Existencias vigentes (UND)')=='9 Stock bajo','status':response.status_code,'rows':table.rows})
    null=client.get('/productos/',{'q':'\x00'})
    report['cases'].append({'id':'PG03B-null-query','ok':null.status_code==200 and 'La búsqueda contiene un carácter no válido.' in null.content.decode() and not CatalogueTable(null.content.decode()).rows,'status':null.status_code})
    exact=client.get('/productos/',{'q':'Atún'})
    upper=client.get('/productos/',{'q':'ATÚN'})
    with connection.cursor() as cur:
        cur.execute("SELECT datctype, UPPER('Atún'), UPPER('ATÚN') FROM pg_database WHERE datname = current_database()")
        locale,lowered,uppered=cur.fetchone()
    matches = CatalogueTable(upper.content.decode()).rows
    report['cases'].append({'id':'PG03B-unicode','ok':[row['Código de barras'] for row in matches]==['AUD03B-ACCENT'] and len(CatalogueTable(exact.content.decode()).rows)==1,'locale':locale,'upper_functions':[lowered,uppered]})
    legacy = client.get('/productos/', {'q':'PIÑA ANTERIOR'})
    legacy_rows = CatalogueTable(legacy.content.decode()).rows
    existing = Product.objects.get(pk=old_product.pk)
    report['cases'].append({'id':'PG03B-migration','ok':[row['Nombre'] for row in legacy_rows]==['Piña anterior'] and existing.category_id==old_category.pk and existing.barcode=='ANTERIOR' and existing.sale_price==Decimal('2.50')})
    report['cases'].append({'id':'PG03B-read-only','ok':before==list(Lot.objects.order_by('pk').values('id','available_quantity'))})
except Exception as exc:
    report['error']={'type':type(exc).__name__,'message':str(exc).replace(PW,'[REDACTED]')[:800]}
finally:
    if configured:connections.close_all()
    if started:own();pg('pg_ctl','-D',DBDIR,'-m','fast','-w','stop')
    with socket.socket() as s:report['port_closed']=s.connect_ex(('127.0.0.1',PORT))!=0
    report['protected_unchanged']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))] for p in protected}
    report['finished_utc']=datetime.now(timezone.utc).isoformat()
    out=RESULTS/'evidencias'/('03-B-postgresql-'+STAMP+'.json');out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'evidence':str(out.relative_to(ROOT)),'cases':report['cases'],'error':report.get('error'),'port_closed':report['port_closed'],'protected_unchanged':all(report['protected_unchanged'].values())},ensure_ascii=False))
if report.get('error') or not all(x['ok'] for x in report['cases']) or not report['port_closed'] or not all(report['protected_unchanged'].values()):raise SystemExit(1)
