"""Accepted product policy checks and simultaneous product submissions in a NEW owned PostgreSQL cluster, then stop.
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
CLUSTER=(Path(tempfile.gettempdir())/('audit03i-pg-'+secrets.token_hex(12))).resolve()
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
    assert CLUSTER.parent==Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith('audit03i-pg-')
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
    from catalog.services import register_canned_product, update_product
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):call_command('migrate',interactive=False,verbosity=0)
    with connection.cursor() as cur:
        cur.execute("SELECT current_database(),current_setting('data_directory'),current_setting('transaction_isolation')")
        db,folder,iso=cur.fetchone();assert db==DBNAME and Path(folder).resolve()==DBDIR
    report.update(database=db,isolation=iso)
    role=Role.objects.create(code='ADMIN',name='AUD03 ADMIN')
    actor=Account.objects.create_user('admin@audit03.invalid',None,display_name='AUD03',role=role)
    from decimal import Decimal


    from django.db import IntegrityError
    from django.db.migrations.executor import MigrationExecutor
    from django.db.migrations.recorder import MigrationRecorder
    canned=Category.objects.create(name='Primera')
    other=Category.objects.create(name='Segunda')
    def snap():
        return list(Product.objects.order_by('pk').values())
    executor=MigrationExecutor(connection)
    executor.migrate([('catalog','0004_product_search_name')])
    state=executor.loader.project_state([('catalog','0004_product_search_name')]).apps
    Legacy=state.get_model('catalog','Product')
    first=Legacy.objects.create(category_id=canned.pk,name='  Atún   heredado ',search_name='  atún   heredado ',
        barcode='LEG-1',barcode_normalized='leg-1',sale_price=Decimal('8.50'),minimum_stock=10)
    second=Legacy.objects.create(category_id=other.pk,name='ATÚN HEREDADO',search_name='atún heredado',
        barcode='LEG-2',barcode_normalized='leg-2',sale_price=Decimal('8.50'),minimum_stock=10)
    target=[('catalog','0005_product_name_and_minimum_policy')]
    def fails_migration(case, expected):
        before=snap()
        try:
            MigrationExecutor(connection).migrate(target)
            message=''
        except RuntimeError as error:
            message=str(error)
        applied=MigrationRecorder(connection).migration_qs.filter(app='catalog',name=target[0][1]).exists()
        report['cases'].append({'id':case,'ok':expected in message and before==snap() and not applied,
                                'rejected_before_writes':before==snap() and not applied})
    fails_migration('PG-I01-migration-name-collision','Product name collision')
    Legacy.objects.filter(pk=second.pk).update(name='Otra herencia',minimum_stock=1000000)
    fails_migration('PG-I02-migration-minimum','minimum outside')
    Legacy.objects.filter(pk=second.pk).update(minimum_stock=999999)
    before=snap()
    MigrationExecutor(connection).migrate(target)
    final=snap()
    def commercial(rows):return [{k:v for k,v in row.items() if k!='search_name'} for row in rows]
    report['cases'].append({'id':'PG-I03-migration-success','ok':commercial(before)==commercial(final)
        and all(p['search_name']==Product.normalize_search_name(p['name']) for p in final)})

    def register(name, barcode, category, minimum=10):
        return register_canned_product(actor=actor,name=name,barcode=barcode,category=category,unit='UND',
                                       sale_price=Decimal('8.50'),minimum_stock=minimum)
    def race(case, articles, edit=False):
        barrier=threading.Barrier(2,timeout=10)
        before=snap()
        def work(article):
            close_old_connections()
            reached=False
            def coordinate(execute,query,params,many,context):
                nonlocal reached
                prefix='UPDATE "catalog_product"' if edit else 'INSERT INTO "catalog_product"'
                if not reached and query.startswith(prefix):
                    reached=True;barrier.wait()
                return execute(query,params,many,context)
            try:
                name,code,cat_id,pk=article
                cat=Category.objects.get(pk=cat_id)
                with connection.execute_wrapper(coordinate):
                    if edit:
                        p=update_product(actor=actor,product=Product.objects.get(pk=pk),category=cat,name=name,
                                         barcode=code,sale_price=Decimal('9.20'),minimum_stock=999999)
                    else:p=register(name,code,cat)
                return {'status':'saved','id':str(p.pk),'barrier':reached}
            except ValidationError as error:
                return {'status':'rejected','id':str(pk) if pk else None,'fields':error.message_dict,'barrier':reached}
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:outcomes=list(pool.map(work,articles))
        after=snap()
        winners=[o for o in outcomes if o['status']=='saved'];losers=[o for o in outcomes if o['status']=='rejected']
        ok=len(winners)==len(losers)==1 and all(o['barrier'] for o in outcomes)
        ok=ok and losers[0].get('fields',{}).get('name')==['Ya existe un producto registrado con este nombre.']
        ok=ok and len(after)==len(before)+(0 if edit else 1)
        if edit and losers:
            loser=losers[0]['id']
            ok=ok and next(p for p in before if str(p['id'])==loser)==next(p for p in after if str(p['id'])==loser)
        report['cases'].append({'id':case,'ok':ok,'outcomes':outcomes,'new_rows':len(after)-len(before)})
    race('PG-I04-concurrent-create-name',[
        ('Nombre  simultáneo','RACE-1',canned.pk,None),(' NOMBRE SIMULTÁNEO ','RACE-2',other.pk,None)])
    a=register('Editable A','EDIT-A',canned);b=register('Editable B','EDIT-B',other)
    race('PG-I05-concurrent-edit-name',[
        ('Renombrado común','NEW-A',canned.pk,a.pk),(' RENOMBRADO   COMÚN ','NEW-B',other.pk,b.pk)],edit=True)

    inactive=register('Reservado inactivo','OFF',canned)
    Product.objects.filter(pk=inactive.pk).update(is_active=False)
    before=snap()
    try:register('RESERVADO  INACTIVO','OFF-2',other);errors={}
    except ValidationError as error:errors=error.message_dict
    report['cases'].append({'id':'PG-I06-inactive-reserves-name','ok':bool(errors.get('name')) and snap()==before})

    before=snap();outcomes=[]
    try:register('Sobre máximo','OVER',canned,1000000);outcomes.append(False)
    except ValidationError as error:outcomes.append(bool(error.message_dict.get('minimum_stock')))
    try:
        update_product(actor=actor,product=inactive,category=canned,name='Cambio rechazado',barcode='OVER-EDIT',
                       sale_price=Decimal('9.20'),minimum_stock=1000000)
        outcomes.append(False)
    except ValidationError as error:outcomes.append(bool(error.message_dict.get('minimum_stock')))
    try:
        with transaction.atomic():Product.objects.filter(pk=inactive.pk).update(minimum_stock=1000000)
        outcomes.append(False)
    except IntegrityError:outcomes.append(True)
    report['cases'].append({'id':'PG-I07-maximum-all-layers','ok':all(outcomes) and len(outcomes)==3 and before==snap()})

    # A linked historical sale is retained when a permitted name edit succeeds.
    import uuid
    from cash.models import CashRegister,CashShift
    from sales.models import Sale,SaleLine
    seller_role=Role.objects.create(code='VENDEDOR',name='Vendedor')
    seller=Account.objects.create_user('seller@audit03.invalid',None,role=seller_role,display_name='AUD03')
    shift=CashShift.objects.create(cash_register=CashRegister.objects.create(code='AUD-I'),seller=seller,opening_amount=Decimal('20'))
    original=Product.objects.get(pk=first.pk)
    sale=Sale.objects.create(cash_shift=shift,seller=seller,total_amount=Decimal('8.50'),base_amount=Decimal('7.20'),
        igv_amount=Decimal('1.30'),cash_received=Decimal('10'),change_given=Decimal('1.50'),correlative='V-AUD-I',idempotency_key=uuid.uuid4())
    line=SaleLine.objects.create(sale=sale,product=original,product_snapshot_name=original.name,
        product_snapshot_barcode=original.barcode,quantity=1,unit_price=Decimal('8.50'),amount=Decimal('8.50'))
    history=list(SaleLine.objects.values())
    update_product(actor=actor,product=original,category=canned,name='Atún heredado marca 170g',barcode=original.barcode,
                   sale_price=Decimal('8.50'),minimum_stock=10)
    report['cases'].append({'id':'PG-I08-name-edit-history','ok':history==list(SaleLine.objects.values()) and
        Product.objects.get(pk=original.pk).search_name=='atún heredado marca 170g'})
except Exception as exc:
    report['error']={'type':type(exc).__name__,'message':str(exc).replace(PW,'[REDACTED]')[:800]}
finally:
    if configured:connections.close_all()
    if started:own();pg('pg_ctl','-D',DBDIR,'-m','fast','-w','stop')
    with socket.socket() as s:report['port_closed']=s.connect_ex(('127.0.0.1',PORT))!=0
    report['protected_unchanged']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()==hashes[str(p.relative_to(ROOT))] for p in protected}
    report['finished_utc']=datetime.now(timezone.utc).isoformat()
    out=RESULTS/'evidencias'/('03-I-postgresql-'+STAMP+'.json');out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'evidence':str(out.relative_to(ROOT)),'cases':report['cases'],'error':report.get('error'),'port_closed':report['port_closed'],'protected_unchanged':all(report['protected_unchanged'].values())},ensure_ascii=False))
if report.get('error') or not all(x['ok'] for x in report['cases']) or not report['port_closed'] or not all(report['protected_unchanged'].values()):raise SystemExit(1)
