"""14 closure: independent PostgreSQL connections, owned ephemeral cluster, no external DSN."""
from __future__ import annotations
import contextlib
import hashlib
import importlib.util
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
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'r1-pmv/manage.py').exists())
OUT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE/('corrida-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S'))
OUT.mkdir(parents=True,exist_ok=False)
(OUT/'runner-ejecutado.py').write_bytes(Path(__file__).read_bytes())
(OUT/'08-ejecutado.md').write_bytes((ROOT/'08_Historias_de_Usuario.md').read_bytes())
BIN=Path('C:/Program Files/PostgreSQL/18/bin')
STAMP=datetime.now(timezone.utc).isoformat()
CLUSTER=(Path(tempfile.gettempdir())/('audit14close-pg-'+secrets.token_hex(10))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK=CLUSTER/'AUDIT14_OWNED';MARK.write_text(STAMP,encoding='utf-8')
DBDIR=CLUSTER/'data';PW=secrets.token_urlsafe(40);PWFILE=CLUSTER/'password';PWFILE.write_text(PW,encoding='utf-8')
DBNAME='audit14_'+secrets.token_hex(5)
with socket.socket() as s:s.bind(('127.0.0.1',0));PORT=s.getsockname()[1]

def digest(data):return hashlib.sha256(data).hexdigest()
def build():
    names=subprocess.check_output(['git','-C',str(ROOT/'r1-pmv'),'ls-files','-co','--exclude-standard','-z']).decode().split('\0')
    files={n:digest((ROOT/'r1-pmv'/n).read_bytes()) for n in sorted(set(names)) if n and not n.startswith('evidencias/') and Path(n).suffix in {'.py','.html','.css','.js','.svg','.ps1','.sh'}}
    return dict(files=files,sha256=digest(json.dumps(files,sort_keys=True,separators=(',',':')).encode()))
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
def own():
    assert CLUSTER.parent==Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith('audit14close-pg-')
    assert MARK.read_text(encoding='utf-8')==STAMP
def pg(name,*args):
    own()
    with tempfile.TemporaryFile(mode='w+',encoding='utf-8',errors='replace') as f:
        r=subprocess.run([str(BIN/(name+'.exe')),*map(str,args)],stdout=f,stderr=f,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
        f.seek(0);text=f.read().replace(PW,'[REDACTED]')
    if r.returncode:raise RuntimeError(name+': '+text[-1200:])
report=dict(started_utc=STAMP,pasada=1,sublote='14-cierre-PG',cases=[],cluster=str(CLUSTER),database=DBNAME,port=PORT,
    plan08=digest((ROOT/'08_Historias_de_Usuario.md').read_bytes()),before=build(),runner_sha256=digest(Path(__file__).read_bytes()),
    python=sys.version,head=subprocess.check_output(['git','-C',str(ROOT/'r1-pmv'),'rev-parse','HEAD'],text=True).strip())
def case(name,fn):
    start=time.monotonic()
    try:
        details=fn() or {};report['cases'].append(dict(id=name,ok=True,seconds=round(time.monotonic()-start,3),**details))
    except Exception as e:
        report['cases'].append(dict(id=name,ok=False,seconds=round(time.monotonic()-start,3),error=type(e).__name__,detail=str(e).replace(PW,'[REDACTED]'),traceback=traceback.format_exc().replace(PW,'[REDACTED]')))
    save(OUT/'results-partial.json',report)
    print(name,report['cases'][-1]['ok'],flush=True)
started=False
try:
    pg('initdb','-D',DBDIR,'-U','audit14','--pwfile',PWFILE,'--auth-host=scram-sha-256','--auth-local=scram-sha-256','--encoding=UTF8','--locale=C')
    PWFILE.unlink()
    pg('pg_ctl','-D',DBDIR,'-l',CLUSTER/'postgres.log','-o',f'-h 127.0.0.1 -p {PORT} -c log_statement=none -c log_min_error_statement=panic','-w','start');started=True
    import psycopg
    from psycopg import sql
    conf=dict(host='127.0.0.1',port=PORT,user='audit14',password=PW)
    with psycopg.connect(**conf,dbname='postgres',autocommit=True) as c:
        assert Path(c.execute('SHOW data_directory').fetchone()[0]).resolve()==DBDIR
        report['postgres_version']=c.execute('SELECT version()').fetchone()[0]
        c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(DBNAME)))
    sys.path.insert(0,str(ROOT/'r1-pmv'))
    os.environ.update(APP_ENV='test',DJANGO_DEBUG='false',DJANGO_SECRET_KEY=secrets.token_urlsafe(48),DJANGO_SETTINGS_MODULE='config.settings',DJANGO_ALLOWED_HOSTS='testserver,127.0.0.1')
    from config import env
    env.load_dotenv=lambda path=None:None
    from django.conf import settings
    settings.DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':DBNAME,'USER':'audit14','PASSWORD':PW,'HOST':'127.0.0.1','PORT':PORT,'CONN_MAX_AGE':0,'OPTIONS':{'options':'-c statement_timeout=30000 -c lock_timeout=15000'}}}
    import django
    django.setup()
    from django.core.management import call_command
    from django.db import connection,connections,transaction,close_old_connections,IntegrityError
    from django.core.exceptions import ValidationError
    from django.utils import timezone as tz
    from django.test import Client
    from django.test.utils import setup_test_environment
    from identity.models import Account,Role
    from catalog.models import Category,Product
    from inventory.models import Lot,StockWriteOff,StockReceipt,PhysicalAdjustment
    from inventory.services import confirm_initial_load,register_stock_entry,write_off_stock,register_physical_adjustment,LotInput
    from cash.models import CashRegister,CashShift,CashShiftClose
    from cash.services import close_cash_shift
    from sales.services import add_product_to_draft,checkout_sale,discard_active_draft
    from sales.models import Sale,SaleLine,SaleDraftLine
    with (OUT/'migrations.txt').open('x',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        call_command('migrate',interactive=False,verbosity=1)
    with connection.cursor() as c:
        c.execute("SELECT current_database(),current_setting('data_directory'),current_setting('transaction_isolation')")
        db,folder,isolation=c.fetchone()
    assert db==DBNAME and Path(folder).resolve()==DBDIR
    report.update(isolation=isolation,migrated=True,django=django.get_version())
    setup_test_environment()
    roles={code:Role.objects.create(code=code,name=code) for code in ('ADMIN','ALMACENERO','VENDEDOR')}
    def actor(code,label):return Account.objects.create_user(email=label+'@audit14.invalid',password=None,display_name=label,role=roles[code])
    admin=actor('ADMIN','AdminPG');admin2=actor('ADMIN','Admin2PG');warehouse=actor('ALMACENERO','AlmacenPG');warehouse2=actor('ALMACENERO','Almacen2PG');seller=actor('VENDEDOR','VentaPG')
    category=Category.objects.create(name='CategoriaPG14')
    register=CashRegister.objects.get_or_create(code='CAJA-01')[0]
    future=tz.localdate()+timedelta(days=90)
    def product(label,qty=10,cost='3'):
        p=Product.objects.create(category=category,name=label,barcode='INT-'+label,sale_price=Decimal('10'))
        load=confirm_initial_load(actor=warehouse,product=p,lots=[LotInput('A',qty,Decimal(cost),future)])
        return p,load.lots.get()
    def snapshot():
        with connection.cursor() as cur:
            tables=sorted(t for t in connection.introspection.table_names() if t.startswith(('catalog_','inventory_','sales_','cash_')))
            digests={}
            for t in tables:
                cur.execute('SELECT * FROM "'+t+'" ORDER BY 1')
                digests[t]=digest(json.dumps(cur.fetchall(),default=str,sort_keys=True).encode())
        return digests
    def race(ops,table='catalog_product'):
        gate=threading.Barrier(2,timeout=12);locked=threading.Event();attempted=threading.Event();pids={};waits=[]
        def work(i):
            close_old_connections()
            with connection.cursor() as c:c.execute('SELECT pg_backend_pid()');pids[i]=c.fetchone()[0]
            first_hit=[False]
            def intercept(execute,query,params,many,context):
                match='FOR UPDATE' in query and 'FROM "'+table+'"' in query
                if i==1 and match:attempted.set()
                result=execute(query,params,many,context)
                if i==0 and match and not first_hit[0]:
                    first_hit[0]=True;locked.set()
                    if not attempted.wait(12):raise RuntimeError('Second connection did not reach contested lock')
                    end=time.monotonic()+12
                    while time.monotonic()<end:
                        with connection.cursor() as c:
                            c.execute('SELECT pg_blocking_pids(%s)',[pids[1]])
                            observed=c.fetchone()[0]
                        if pids[0] in observed:waits.append(dict(blocked=pids[1],blocker=pids[0]));break
                        time.sleep(.02)
                    if not waits:raise RuntimeError('No real PG blocking observed')
                return result
            try:
                gate.wait()
                if i==1 and not locked.wait(12):raise RuntimeError('First lock not acquired')
                with connection.execute_wrapper(intercept):result=ops[i]()
                return dict(result='success',pk=str(getattr(result,'pk',result)))
            except Exception as e:return dict(result=type(e).__name__,detail=str(e))
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures=[pool.submit(work,i) for i in range(2)];results=[f.result(timeout=40) for f in futures]
        assert len(set(pids.values()))==2 and waits,dict(pids=pids,waits=waits,results=results)
        return dict(pids=pids,lock_waits=waits,results=results)
    def writeoff_replay():
        p,l=product('MermaReplay');key=uuid.uuid4()
        ops=[lambda:write_off_stock(actor=warehouse,lot=l,quantity=2,reason='DAÑO',notes='Frasco roto',idempotency_key=key)]*2
        r=race(ops,'identity_account');l.refresh_from_db()
        assert [o['result'] for o in r['results']]==['success','success'] and len({o['pk'] for o in r['results']})==1
        assert l.available_quantity==8 and StockWriteOff.objects.filter(lot=l).count()==1
        return dict(**r,stock=8,writeoffs=1)
    case('PG14-01-merma-UUID-concurrente',writeoff_replay)
    def writeoff_conflict():
        p,l=product('MermaDivergente');key=uuid.uuid4()
        r=race([lambda:write_off_stock(actor=warehouse,lot=l,quantity=2,reason='ROBO',notes='Faltante',idempotency_key=key),lambda:write_off_stock(actor=warehouse2,lot=l,quantity=2,reason='ROBO',notes='Faltante',idempotency_key=key)])
        assert [o['result'] for o in r['results']]==['success','ValidationError']
        l.refresh_from_db();assert l.available_quantity==8 and StockWriteOff.objects.filter(lot=l).count()==1
        return dict(**r,stock=8,writeoffs=1)
    case('PG14-02-merma-clave-otro-actor',writeoff_conflict)
    def receipt_replay():
        p,l=product('RecepcionReplay');key=uuid.uuid4();lots=[LotInput('C',5,Decimal('7'),future)]
        r=race([lambda:register_stock_entry(actor=warehouse,product=p,lots=lots,idempotency_key=key)]*2,'identity_account')
        assert [o['result'] for o in r['results']]==['success','success'] and len({o['pk'] for o in r['results']})==1
        p.refresh_from_db();assert p.physical_stock==15 and p.average_cost==Decimal('4.3333') and StockReceipt.objects.filter(product=p).count()==1
        return dict(**r,stock=15,average=str(p.average_cost),receipts=1)
    case('PG14-03-recepcion-UUID-concurrente',receipt_replay)
    def receipt_commercial():
        p,l=product('RecepcionComercial');lots=[LotInput('C',5,Decimal('7'),future)]
        r=race([lambda:register_stock_entry(actor=warehouse,product=p,lots=lots,idempotency_key=uuid.uuid4()),lambda:register_stock_entry(actor=warehouse2,product=p,lots=lots,idempotency_key=uuid.uuid4())],'inventory_stockreceiptcounter')
        assert [o['result'] for o in r['results']]==['success','success'] and len({o['pk'] for o in r['results']})==2
        p.refresh_from_db();assert p.physical_stock==20 and StockReceipt.objects.filter(product=p).count()==2
        return dict(**r,stock=20,commercial_C_lots=Lot.objects.filter(product=p,number_normalized='C').count())
    case('PG14-04-dos-entregas-reales-mismo-C',receipt_commercial)
    def stock_race(kind,first):
        p,l=product('Carrera'+kind+first,5)
        CashShift.objects.filter(status='OPEN').update(status='CLOSED')
        shift=CashShift.objects.create(cash_register=register,seller=seller,opening_amount=Decimal('100'))
        draft=add_product_to_draft(actor=seller,product_id=p.pk,quantity=4)
        sale=lambda:checkout_sale(actor=seller,draft_id=draft.pk,cash_received=Decimal('40'),idempotency_key=uuid.uuid4())
        other=(lambda:write_off_stock(actor=warehouse,lot=l,quantity=3,reason='ROBO',notes='Faltante')) if kind=='Merma' else (lambda:register_physical_adjustment(actor=admin,lot=l,delta=-3,reason='Conteo'))
        ops=[sale,other] if first=='Venta' else [other,sale]
        r=race(ops);assert [o['result'] for o in r['results']]==['success','ValidationError'],r
        l.refresh_from_db();assert l.available_quantity==(1 if first=='Venta' else 2)
        assert Sale.objects.filter(cash_shift=shift).count()==(1 if first=='Venta' else 0)
        return dict(**r,stock=l.available_quantity,sales=Sale.objects.filter(cash_shift=shift).count())
    for kind in ('Merma','Ajuste'):
        for first in ('Venta','Inventario'):case('PG14-05-'+kind+'-primero-'+first,lambda k=kind,f=first:stock_race(k,f))
    def two_negative_adjustments():
        p,l=product('DosAjustes',5)
        r=race([lambda:register_physical_adjustment(actor=admin,lot=l,delta=-4,reason='ConteoA'),lambda:register_physical_adjustment(actor=admin2,lot=l,delta=-4,reason='ConteoB')])
        assert [o['result'] for o in r['results']]==['success','ValidationError']
        l.refresh_from_db();assert l.available_quantity==1 and PhysicalAdjustment.objects.filter(lot=l).count()==1
        return dict(**r,stock=1,adjustments=1)
    case('PG14-06-dos-ajustes-sin-negativo',two_negative_adjustments)
    def rollback():
        p,l=product('RollbackPG',5)
        original=Lot.save
        def fail(instance,*args,**kwargs):original(instance,*args,**kwargs);raise RuntimeError('Injected after lot write')
        results=[]
        for label,op in [('merma',lambda:write_off_stock(actor=warehouse,lot=l,quantity=5,reason='ROBO',notes='Faltante',idempotency_key=uuid.uuid4())),('ajuste',lambda:register_physical_adjustment(actor=admin,lot=l,delta=-5,reason='Conteo'))]:
            before=snapshot()
            try:
                with patch.object(Lot,'save',fail):op()
            except RuntimeError:pass
            else:raise AssertionError('Failure not raised')
            assert snapshot()==before
            results.append(dict(operation=label,all_business_tables_identical=True))
        return dict(results=results,tables=len(before))
    case('PG14-07-rollback-postwrite',rollback)
    def concurrent_correlatives():
        count=8;fixtures=[product('Correlativo'+str(i),3) for i in range(count)]
        actors=[actor('ALMACENERO','Parallel'+str(i)) for i in range(count)]
        import inventory.services as services
        original=services._next_writeoff_correlativo;barrier=threading.Barrier(count,timeout=15);seen=threading.local();pids=[]
        def collide():
            value=original()
            if not getattr(seen,'hit',False):seen.hit=True;barrier.wait()
            return value
        def worker(i):
            close_old_connections()
            with connection.cursor() as c:c.execute('SELECT pg_backend_pid()');pids.append(c.fetchone()[0])
            try:return write_off_stock(actor=actors[i],lot=fixtures[i][1],quantity=1,reason='ROBO',notes='Faltante').correlativo
            finally:connections.close_all()
        with patch.object(services,'_next_writeoff_correlativo',collide),ThreadPoolExecutor(max_workers=count) as pool:
            values=list(pool.map(worker,range(count)))
        assert len(set(values))==count and len(set(pids))==count
        nums=sorted(int(v[2:]) for v in values);assert nums==list(range(nums[0],nums[0]+count))
        return dict(connections=len(set(pids)),correlatives=values,forced_first_attempt_collision=True)
    case('PG14-08-colision-correlativos-8conexiones',concurrent_correlatives)
    def ledger_concurrent():
        p,l=product('KardexConcurrente',10);client=Client();client.force_login(admin)
        state={'fired':False};pids=[]
        def writer():
            close_old_connections()
            try:
                with connection.cursor() as c:c.execute('SELECT pg_backend_pid()');pids.append(c.fetchone()[0])
                register_physical_adjustment(actor=admin2,lot=l,delta=-2,reason='IntercalacionPG')
            finally:connections.close_all()
        def intercept(execute,query,params,many,context):
            result=execute(query,params,many,context)
            if query.lstrip().upper().startswith('SELECT') and 'FROM "inventory_lot"' in query and not state['fired']:
                state['fired']=True
                with ThreadPoolExecutor(max_workers=1) as pool:pool.submit(writer).result(timeout=20)
            return result
        with connection.cursor() as c:c.execute('SELECT pg_backend_pid()');pids.append(c.fetchone()[0])
        with connection.execute_wrapper(intercept):response=client.get('/inventario/productos/'+str(p.pk)+'/movimientos/')
        assert response.status_code==200 and state['fired'] and len(set(pids))==2
        html=response.content.decode();authoritative=response.context['summary']['closing_balance'] if 'summary' in response.context else None
        # Read-committed multi-statement query must either show a consistent cut or explicitly report unavailable.
        has_unavailable='No disponible' in html
        fresh=client.get('/inventario/productos/'+str(p.pk)+'/movimientos/')
        assert fresh.status_code==200
        assert 'data-testid="closing-balance">8<' in fresh.content.decode()
        assert has_unavailable or 'data-testid="closing-balance">10<' in html or 'data-testid="closing-balance">8<' in html
        return dict(independent_pids=pids,interleaved_write_committed=True,inflight_shows_unavailable=has_unavailable,refresh_balance=8,observed_html_sha256=digest(response.content))
    case('PG14-09-kardex-escritura-entre-lecturas',ledger_concurrent)
    def adjustment_replay_new_origin():
        p,l=product('AjusteNuevoIdem',5);key=uuid.uuid4()
        args=dict(actor=admin,product=p,number='HALLAZGO',expiration_date=future,delta=2,reason='Recuento documentado',idempotency_key=key)
        r=race([lambda:register_physical_adjustment(**args)]*2,'identity_account')
        assert [o['result'] for o in r['results']]==['success','success'] and len({o['pk'] for o in r['results']})==1
        assert p.physical_stock==7 and Lot.objects.filter(product=p,number_normalized='HALLAZGO').count()==1
        new=Lot.objects.get(product=p,number_normalized='HALLAZGO')
        assert new.adjustment_origin_id is not None
        return dict(**r,physical_stock=7,new_origins=1)
    case('PG14-10-ajuste-nuevo-reenvio-UUID',adjustment_replay_new_origin)
    def adjustment_new_collision():
        p,l=product('AjusteNuevoColision',5)
        args=dict(product=p,number='HALLAZGO',expiration_date=future,delta=2,reason='Recuento documentado')
        r=race([lambda:register_physical_adjustment(actor=admin,idempotency_key=uuid.uuid4(),**args),lambda:register_physical_adjustment(actor=admin2,idempotency_key=uuid.uuid4(),**args)])
        assert [o['result'] for o in r['results']]==['success','ValidationError'],r
        assert p.physical_stock==7 and Lot.objects.filter(product=p,number_normalized='HALLAZGO').count()==1
        return dict(**r,physical_stock=7,new_origins=1)
    case('PG14-11-ajuste-nuevo-colision-comercial',adjustment_new_collision)
    def checks_and_limits():
        CashShift.objects.filter(status='OPEN').update(status='CLOSED')
        shift=CashShift.objects.create(cash_register=register,seller=seller,opening_amount=Decimal('100'))
        p,l=product('LimitesCajaPG',20)
        draft=add_product_to_draft(actor=seller,product_id=p.pk,quantity=1)
        draftline=SaleDraftLine.objects.get(draft=draft)
        results=[]
        def rejects(label,op):
            before=snapshot()
            try:
                with transaction.atomic():op()
            except IntegrityError as e:results.append(dict(id=label,rejected=True,type=type(e).__name__))
            else:raise AssertionError('Constraint accepted '+label)
            assert snapshot()==before
        rejects('draft_quantity_1000000',lambda:SaleDraftLine.objects.filter(pk=draftline.pk).update(quantity=1000000))
        sale=checkout_sale(actor=seller,draft_id=draft.pk,cash_received=Decimal('10'),idempotency_key=uuid.uuid4())
        rejects('sale_total_negative',lambda:Sale.objects.filter(pk=sale.pk).update(total_amount=Decimal('-.01')))
        rejects('sale_received_negative',lambda:Sale.objects.filter(pk=sale.pk).update(cash_received=Decimal('-.01')))
        closure=close_cash_shift(actor=seller,counted_amount=Decimal('110'))
        rejects('close_count_negative',lambda:CashShiftClose.objects.filter(pk=closure.pk).update(counted_amount=Decimal('-.01')))
        rejects('close_expected_negative',lambda:CashShiftClose.objects.filter(pk=closure.pk).update(expected_amount=Decimal('-.01')))
        rejects('close_difference_inconsistent',lambda:CashShiftClose.objects.filter(pk=closure.pk).update(difference=Decimal('.01')))
        return dict(checks=results,all_rejected_tables_unchanged=True)
    case('PG14-12-checks-montos-cantidad-cierre',checks_and_limits)
    def cash_accumulated_and_capacity():
        CashShift.objects.filter(status='OPEN').update(status='CLOSED')
        shift=CashShift.objects.create(cash_register=register,seller=seller,opening_amount=Decimal('0'))
        p,l=product('CapacidadAcumulada',20)
        draft=add_product_to_draft(actor=seller,product_id=p.pk,quantity=1)
        sale=checkout_sale(actor=seller,draft_id=draft.pk,cash_received=Decimal('10'),idempotency_key=uuid.uuid4())
        # Explicit historical fixture, not a new sale bypass: tests accumulated accounting capacity.
        Sale.objects.filter(pk=sale.pk).update(total_amount=Decimal('10000000.00'),base_amount=Decimal('10000000.00'),igv_amount=0,cash_received=Decimal('10000000.00'))
        closure=close_cash_shift(actor=seller,counted_amount=Decimal('10000000.00'))
        assert closure.expected_amount==Decimal('10000000.00') and closure.difference==0
        shift2=CashShift.objects.create(cash_register=register,seller=seller,opening_amount=Decimal('0'))
        d2=add_product_to_draft(actor=seller,product_id=p.pk,quantity=1)
        s2=checkout_sale(actor=seller,draft_id=d2.pk,cash_received=Decimal('10'),idempotency_key=uuid.uuid4())
        maximum=Decimal('999999999999.99')
        Sale.objects.filter(pk=s2.pk).update(total_amount=maximum,base_amount=maximum,igv_amount=0,cash_received=maximum)
        d3=add_product_to_draft(actor=seller,product_id=p.pk,quantity=1);before=snapshot()
        try:checkout_sale(actor=seller,draft_id=d3.pk,cash_received=Decimal('10'),idempotency_key=uuid.uuid4())
        except ValidationError as e:assert 'capacidad' in str(e)
        else:raise AssertionError('Accepted amount beyond accumulated capacity')
        assert snapshot()==before
        discard_active_draft(actor=seller)
        final=close_cash_shift(actor=seller,counted_amount=maximum)
        assert final.expected_amount==maximum and final.difference==0
        return dict(historical_fixture=True,above_operation_limit_closes='10000000.00',at_storage_limit_closes=str(maximum),next_sale_rejected_before_mutation=True)
    case('PG14-13-cierre-acumulado-y-capacidad-previa',cash_accumulated_and_capacity)
    def simultaneous_http(kind):
        p,l=product('HTTP'+kind,10);key=uuid.uuid4();clients=[Client(),Client()]
        who=warehouse if kind=='Merma' else admin
        for client in clients:client.force_login(who)
        payload=dict(lot_id=str(l.pk),idempotency_key=str(key))
        if kind=='Merma':
            path='/inventario/bajas/nueva/';payload.update(quantity='2',reason='ROBO',notes='Faltante HTTP')
        else:
            path='/inventario/ajustes/nuevo/';payload.update(delta='-2',reason='Conteo HTTP')
        replies={}
        def send(i):
            result=clients[i].post(path,payload)
            replies[i]=dict(status=result.status_code,location=result.headers.get('Location'))
            assert result.status_code==302,dict(status=result.status_code,errors=str(getattr(result,'context',None)))
            return result.headers['Location']
        r=race([lambda:send(0),lambda:send(1)],'identity_account')
        assert [x['result'] for x in r['results']]==['success','success'] and replies[0]==replies[1],dict(r=r,replies=replies)
        l.refresh_from_db();assert l.available_quantity==8
        model=StockWriteOff if kind=='Merma' else PhysicalAdjustment
        assert model.objects.filter(lot=l).count()==1
        return dict(**r,independent_sessions=True,responses=replies,stock=8,operations=1,csrf_note='Django Client concurrente sin validacionCSRF; Chrome previo comprueba middlewareCSRF por separado')
    for kind in ('Merma','Ajuste'):case('PG14-14-HTTP-dos-sesiones-'+kind,lambda k=kind:simultaneous_http(k))
    def receipt_rollback_postwrite():
        p,l=product('RecepcionRollback',10);key=uuid.uuid4();before=snapshot();original=Product.save
        def fail(instance,*args,**kwargs):original(instance,*args,**kwargs);raise RuntimeError('Injected after average cost write')
        args=dict(actor=warehouse,product=p,lots=[LotInput('C',5,Decimal('7'),future)],idempotency_key=key)
        try:
            with patch.object(Product,'save',fail):register_stock_entry(**args)
        except RuntimeError:pass
        else:raise AssertionError('No failure after write')
        assert snapshot()==before
        receipt=register_stock_entry(**args)
        assert StockReceipt.objects.filter(idempotency_key=key).count()==1 and p.physical_stock==15
        return dict(all_business_tables_unchanged_after_exception=True,tables=len(before),retry_receipt=str(receipt.pk),stock_after_retry=15)
    case('PG14-15-recepcion-rollback-y-reintento',receipt_rollback_postwrite)
except Exception as e:
    report['fatal']=dict(type=type(e).__name__,detail=str(e).replace(PW,'[REDACTED]'),traceback=traceback.format_exc().replace(PW,'[REDACTED]'))
finally:
    if started:
        try:
            if 'connections' in globals():connections.close_all()
            pg('pg_ctl','-D',DBDIR,'-m','fast','-w','stop');report['cluster_stopped']=True
        except Exception as e:report['stop_error']=str(e).replace(PW,'[REDACTED]')
    if PWFILE.exists():PWFILE.unlink()
    report.update(after=build(),finished_utc=datetime.now(timezone.utc).isoformat())
    report['source_stable']=report['before']==report['after']
    report['passed']=sum(c['ok'] for c in report['cases']);report['total']=len(report['cases'])
    report['ok']=not report.get('fatal') and report['passed']==report['total'] and report['source_stable'] and report.get('cluster_stopped',False)
    save(OUT/'results.json',report)
    print(json.dumps({k:report[k] for k in ('ok','passed','total','source_stable')},ensure_ascii=False))
sys.exit(0 if report['ok'] else 1)
