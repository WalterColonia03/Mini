"""13-B-04: fresh, owned PostgreSQL cluster; never accepts an external DSN."""
from __future__ import annotations
import contextlib, hashlib, io, json, os, secrets, socket, statistics, subprocess, sys, tempfile, threading, time, traceback, uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / 'auditoria_por_etapas/resultados'
BIN = Path('C:/Program Files/PostgreSQL/18/bin')
STAMP = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
CLUSTER = Path(tempfile.gettempdir()) / ('audit13-pg-' + secrets.token_hex(12))
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / 'AUDIT13_OWNED'
MARK.write_text(STAMP, encoding='utf-8')
DBDIR = CLUSTER / 'data'
PW = secrets.token_urlsafe(40)
PWFILE = CLUSTER / 'password'
PWFILE.write_text(PW, encoding='utf-8')
DBNAME = 'audit13_' + secrets.token_hex(5)
with socket.socket() as sock:
    sock.bind(('127.0.0.1', 0)); PORT = sock.getsockname()[1]
OUT = RESULTS/'evidencias'/('13-B-PG-'+STAMP)
OUT.mkdir(exist_ok=False)
report = {'pass':'primera','sublote':'13-B-04','at_utc':datetime.now(timezone.utc).isoformat(),
          'cluster':str(CLUSTER),'database':DBNAME,'port':PORT,'cases':[],
          'plan08_sha256':hashlib.sha256((ROOT/'08_Historias_de_Usuario.md').read_bytes()).hexdigest(),
          'identity_views_sha256':hashlib.sha256((ROOT/'r1-pmv/identity/views.py').read_bytes()).hexdigest()}
def write(path, data): path.write_text(json.dumps(data,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
def own():
    assert CLUSTER.resolve().parent == Path(tempfile.gettempdir()).resolve()
    assert CLUSTER.name.startswith('audit13-pg-') and MARK.read_text(encoding='utf-8') == STAMP
def pg(name,*args):
    own()
    with tempfile.TemporaryFile(mode='w+',encoding='utf-8',errors='replace') as f:
        r=subprocess.run([str(BIN/(name+'.exe')),*map(str,args)],stdout=f,stderr=f,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
        f.seek(0); diagnostic=f.read().replace(PW,'[REDACTED]')
    if r.returncode: raise RuntimeError(name+': '+diagnostic[-1000:])
def norm(value):
    return {k:format(v,'.2f') if isinstance(v,Decimal) else v for k,v in value.items()} if value else value
def case(name, expected, observed, **extra):
    report['cases'].append(dict(id=name,expected=expected,observed=observed,ok=expected==observed,**extra))
started=False
try:
    pg('initdb','-D',DBDIR,'-U','audit13','--pwfile',PWFILE,'--auth-host=scram-sha-256','--auth-local=scram-sha-256','--encoding=UTF8','--locale=C')
    PWFILE.unlink()
    pg('pg_ctl','-D',DBDIR,'-l',CLUSTER/'postgres.log','-o',f'-h 127.0.0.1 -p {PORT} -c log_statement=none -c log_min_error_statement=panic','-w','start')
    started=True
    import psycopg
    from psycopg import sql
    conf=dict(host='127.0.0.1',port=PORT,user='audit13',password=PW)
    with psycopg.connect(**conf,dbname='postgres',autocommit=True) as c:
        assert Path(c.execute('SHOW data_directory').fetchone()[0]).resolve()==DBDIR.resolve()
        report['postgres_version']=c.execute('SELECT version()').fetchone()[0]
        c.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(DBNAME)))
    sys.path.insert(0,str(ROOT/'r1-pmv'))
    os.environ.update(APP_ENV='test',DJANGO_DEBUG='false',DJANGO_SECRET_KEY=secrets.token_urlsafe(48),DJANGO_SETTINGS_MODULE='config.settings',DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1,testserver')
    from config import env
    loader=env.load_dotenv; env.load_dotenv=lambda path=None:None
    from django.conf import settings
    settings.DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':DBNAME,'USER':'audit13','PASSWORD':PW,'HOST':'127.0.0.1','PORT':PORT,'CONN_MAX_AGE':0,'OPTIONS':{'options':'-c statement_timeout=60000 -c lock_timeout=10000'}}}
    env.load_dotenv=loader
    import django
    django.setup()
    from django.db import connection, connections, transaction
    from django.test import Client
    from django.test.utils import CaptureQueriesContext, setup_test_environment
    from django.utils import timezone as tz
    from identity.models import Account, Role
    from identity.views import _dashboard_summary
    from catalog.models import Category, Product
    from inventory.models import InitialInventoryLoad, Lot
    from sales.models import Sale
    from audit13_run import fixtures
    run=RESULTS/'datos'/('etapa13-pg-'+STAMP)
    run.mkdir(exist_ok=False); write(run/'marker.json',{'run':run.name,'isolated':True,'engine':'postgresql','database':DBNAME})
    (Path(tempfile.gettempdir())/'minimarket-audit13'/run.name).mkdir(parents=True,exist_ok=False)
    with contextlib.redirect_stdout(io.StringIO()): fixtures(run)
    fixture=json.loads((run/'fixture.json').read_text(encoding='utf-8'))
    today=tz.localdate(); report['date_lima']=str(today)
    with connection.cursor() as c:
        c.execute("SELECT current_database(), current_setting('data_directory'), current_setting('transaction_isolation'), pg_backend_pid()")
        db,folder,isolation,reader_pid=c.fetchone()
    assert db==DBNAME and Path(folder).resolve()==DBDIR.resolve()
    report.update(isolation=isolation,reader_pid=reader_pid,fixture=fixture)
    case('PG-01-admin-seven',fixture['expected_summary'],norm(_dashboard_summary(Role.Code.ADMIN,today)))
    case('PG-02-warehouse-three',dict(low_stock=3,expiring=6,expired=5),norm(_dashboard_summary(Role.Code.WAREHOUSE,today)))
    case('PG-03-seller-none',None,_dashboard_summary(Role.Code.SELLER,today))
    case('PG-04-next-Lima-day',{'sales_count':1,'sales_total':'92.22'}, {k:v for k,v in norm(_dashboard_summary(Role.Code.ADMIN,today+timedelta(days=1))).items() if k in ('sales_count','sales_total')})
    setup_test_environment()
    admin=Client(); admin.force_login(Account.objects.get(pk=fixture['accounts']['admin']))
    for route, expected in [('/inventario/stock/',(3,6,5)),('/productos/vencimientos/',(30,6,5,11)),('/ventas/historial/?fecha='+str(today),(3,'60.06'))]:
        response=admin.get(route); ctx=response.context
        observed=(len(ctx['low_stock']),len(ctx['expiring_lots']),len(ctx['expired_lots'])) if 'stock' in route else (ctx['days'],ctx['upcoming_count'],ctx['expired_count'],len(ctx['lots'])) if 'vencimientos' in route else (len(ctx['sales']),str(sum((s.total_amount for s in ctx['sales']),Decimal('0.00'))))
        case('PG-05-linked-'+route,expected,observed)
    for field in ['fecha','fecha_desde','fecha_hasta']:
        for value in ['2026-02-30','20260101','9'*5000]:
            response=admin.get('/ventas/historial/',{field:value})
            case('PG-D11-'+field+'-'+str(len(value)),(200,0),(response.status_code,len(response.context['sales'])))
    # Real empty tables in a rolled-back transaction; historical fixtures survive.
    from sales.models import SaleLine
    from cash.models import CashShift
    with transaction.atomic():
        SaleLine.objects.all().delete(); Sale.objects.all().delete()
        Lot.objects.all().delete(); InitialInventoryLoad.objects.all().delete()
        Product.objects.all().delete(); CashShift.objects.all().delete()
        empty=dict(sales_count=0,sales_total='0.00',discount_total='0.00',open_shifts=0,low_stock=0,expiring=0,expired=0)
        case('PG-empty-summary',empty,norm(_dashboard_summary(Role.Code.ADMIN,today)))
        for route,literal in [('/inventario/stock/','No hay productos registrados'),('/productos/vencimientos/','No hay lotes con unidades disponibles'),('/ventas/historial/','No se encontraron ventas')]:
            response=admin.get(route)
            case('PG-empty-'+route,(200,True),(response.status_code,literal in response.content.decode()))
        transaction.set_rollback(True)
    lotid=fixture['lots']['A13-venta-integracion-0']; saleid=fixture['sales'][1]['id']
    with psycopg.connect(**conf,dbname=DBNAME,autocommit=True) as writer:
        writer_pid=writer.execute('SELECT pg_backend_pid()').fetchone()[0]
        assert writer_pid!=reader_pid
        report['writer_pid']=writer_pid
        for round in range(5):
            with writer.transaction():
                writer.execute('UPDATE inventory_lot SET available_quantity=3 WHERE id=%s',(lotid,))
                writer.execute('UPDATE sales_sale SET total_amount=10.01 WHERE id=%s',(saleid,))
            fired=[]
            def interleave(execute, query, params, many, context):
                result=execute(query,params,many,context)
                if query.lstrip().upper().startswith('SELECT') and not fired:
                    with writer.transaction():
                        writer.execute('UPDATE inventory_lot SET available_quantity=0 WHERE id=%s',(lotid,))
                        writer.execute('UPDATE sales_sale SET total_amount=17.11 WHERE id=%s',(saleid,))
                    fired.append(True)
                return result
            with connection.execute_wrapper(interleave): observed=norm(_dashboard_summary(Role.Code.ADMIN,today))
            after=norm(_dashboard_summary(Role.Code.ADMIN,today))
            consistent=observed==fixture['expected_summary'] or observed==after
            case('PG-06-concurrent-snapshot-'+str(round),True,consistent,observed_summary=observed,before=fixture['expected_summary'],after=after,independent_pids=[reader_pid,writer_pid],writer_committed_between_first_query_and_read_completion=bool(fired))
        with writer.transaction():
            writer.execute('UPDATE inventory_lot SET available_quantity=3 WHERE id=%s',(lotid,))
            writer.execute('UPDATE sales_sale SET total_amount=10.01 WHERE id=%s',(saleid,))
    if 'pre' not in sys.argv:
        ready=threading.Event(); stop=threading.Event()
        def continuously_write():
            writes=0
            with psycopg.connect(**conf,dbname=DBNAME,autocommit=True) as concurrent:
                pid=concurrent.execute('SELECT pg_backend_pid()').fetchone()[0]
                while not stop.is_set():
                    changed=writes%2==0
                    with concurrent.transaction():
                        concurrent.execute('UPDATE inventory_lot SET available_quantity=%s WHERE id=%s',(0 if changed else 3,lotid))
                        concurrent.execute('UPDATE sales_sale SET total_amount=%s WHERE id=%s',(Decimal('17.11') if changed else Decimal('10.01'),saleid))
                    writes+=1; ready.set(); time.sleep(.002)
            return {'pid':pid,'commits':writes}
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(continuously_write)
            assert ready.wait(10)
            observed=[]
            try:
                for _ in range(25): observed.append(norm(_dashboard_summary(Role.Code.ADMIN,today)))
            finally: stop.set()
            writer_stats=future.result(timeout=10)
        before=fixture['expected_summary']; after=dict(before,expiring=5,low_stock=4,sales_total='67.16')
        case('PG-06b-overlapping-reader-writer',True,all(x in (before,after) for x in observed),summaries=observed,reader_pid=reader_pid,writer=writer_stats)
        with psycopg.connect(**conf,dbname=DBNAME) as writer:
            writer.execute('UPDATE inventory_lot SET available_quantity=3 WHERE id=%s',(lotid,))
            writer.execute('UPDATE sales_sale SET total_amount=10.01 WHERE id=%s',(saleid,))
        from sales.services import add_product_to_draft, checkout_sale
        seller=Account.objects.get(pk=fixture['accounts']['seller'])
        draft=add_product_to_draft(actor=seller,product_id=fixture['products']['venta-integracion'],quantity=2)
        case('PG-09-draft-no-effect',{'summary':fixture['expected_summary'],'stock':3},
             {'summary':norm(_dashboard_summary(Role.Code.ADMIN,today)),'stock':Lot.objects.get(pk=lotid).available_quantity})
        key=uuid.uuid4()
        sale=checkout_sale(actor=seller,draft_id=draft.pk,cash_received=Decimal('10.00'),idempotency_key=key)
        expected_after=dict(fixture['expected_summary'],sales_count=4,sales_total='67.16',low_stock=4)
        case('PG-10-checkout',{'summary':expected_after,'stock':1,'total':'7.10','received':'10.00','change':'2.90'},
             {'summary':norm(_dashboard_summary(Role.Code.ADMIN,today)),'stock':Lot.objects.get(pk=lotid).available_quantity,
              'total':str(sale.total_amount),'received':str(sale.cash_received),'change':str(sale.change_given)})
        repeated=checkout_sale(actor=seller,draft_id=draft.pk,cash_received=Decimal('10.00'),idempotency_key=key)
        case('PG-11-idempotency-refresh',{'same_sale':True,'summary':expected_after,'sales_all_dates':6,'stock':1},
             {'same_sale':repeated.pk==sale.pk,'summary':norm(admin.get('/inicio/').context['summary']),'sales_all_dates':Sale.objects.count(),'stock':Lot.objects.get(pk=lotid).available_quantity})
        case('PG-12-warehouse-after',dict(low_stock=4,expiring=6,expired=5),norm(_dashboard_summary(Role.Code.WAREHOUSE,today)))
        # Declared synthetic scale; not operational volume and not a load/SLA test.
        category=Category.objects.create(name='Audit13 volume')
        prods=[Product(name=f'Volume {i}',search_name=f'volume {i}',barcode=f'VOL13-{i}',barcode_normalized=f'VOL13-{i}',category=category,minimum_stock=5,sale_price=Decimal('3.55')) for i in range(2000)]
        Product.objects.bulk_create(prods,batch_size=500)
        loads=[InitialInventoryLoad(product=p,responsible_id=fixture['accounts']['warehouse']) for p in prods]
        InitialInventoryLoad.objects.bulk_create(loads,batch_size=500)
        lots=[Lot(product=p,initial_load=load,responsible_id=fixture['accounts']['warehouse'],number=f'VOL-{i}',number_normalized=f'VOL-{i}',initial_quantity=3,available_quantity=i%4,unit_cost=Decimal('1.2345'),expiration_date=today+timedelta(days=i-2)) for p,load in zip(prods,loads) for i in range(10)]
        Lot.objects.bulk_create(lots,batch_size=500)
        # 30,000 historical synthetic snapshots, current day: exact .01 accumulation.
        sales=[Sale(cash_shift_id=fixture['open_shift'],seller_id=fixture['accounts']['seller'],total_amount=Decimal('0.01'),base_amount=Decimal('0.01'),igv_amount=0,discount_amount=0,cash_received=Decimal('0.01'),change_given=0,correlative=f'V-{i+100000:08d}',idempotency_key=uuid.uuid4()) for i in range(30000)]
        Sale.objects.bulk_create(sales,batch_size=1000)
        with connection.cursor() as c: c.execute('ANALYZE')
        counts=dict(products=Product.objects.count(),lots=Lot.objects.count(),sales=Sale.objects.count())
        report['volume']={'synthetic_added':{'products':2000,'lots':20000,'sales':30000},'total_rows':counts,'roles':{},'cache':'no app cache; warmed local DB; sequential observations'}
        case('PG-07-decimal-volume',{'sales_count':30004,'sales_total':'367.16','discount_total':'5.06'}, {k:v for k,v in norm(_dashboard_summary(Role.Code.ADMIN,today)).items() if k in ('sales_count','sales_total','discount_total')})
        for role in Role.Code.values:
            times=[]
            for _ in range(21):
                start=time.perf_counter(); _dashboard_summary(role,today); times.append((time.perf_counter()-start)*1000)
            with CaptureQueriesContext(connection) as capture: _dashboard_summary(role,today)
            queries=[q['sql'] for q in capture]
            case('PG-13-query-count-'+role,0 if role==Role.Code.SELLER else 1,len(queries))
            if role!=Role.Code.ADMIN:
                case('PG-14-no-finance-'+role,False,any('sales_sale' in q or 'cash_cashshift' in q for q in queries))
            report['volume']['roles'][role]={'query_count':len(queries),'samples_ms':times,'median_ms':statistics.median(times),'sample_p95_ms':sorted(times)[19],'max_ms':max(times)}
            write(OUT/(role+'-queries.json'),queries)
            plans=[]
            for query in queries:
                with connection.cursor() as c:
                    c.execute('EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) '+query); plans.append(c.fetchone()[0])
            write(OUT/(role+'-plans.json'),plans)
    if 'pre' not in sys.argv:
        from django.test.utils import teardown_test_environment
        from django.test.runner import DiscoverRunner
        teardown_test_environment()
        log=io.StringIO()
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            failures=DiscoverRunner(verbosity=2,interactive=False).run_tests(['identity.test_audit13_summary','sales.test_audit13_history_boundaries'])
        (OUT/'regression-postgresql.txt').write_text(log.getvalue(),encoding='utf-8')
        case('PG-08-regression',0,failures,modules=['identity.test_audit13_summary','sales.test_audit13_history_boundaries'])
    report['limitations']=['PostgreSQL18.4 Windows differs from intended PostgreSQL17; no production or PG17 certification','Synthetic local volume, 21 sequential timings per role, no operational SLA or p95 guarantee','Concurrent atomic writes are deliberate fixture updates, not a full checkout load test','No cache/index added on these measurements alone','Browser is covered separately by parent task']
except Exception as error:
    report['error']=str(error).replace(PW,'[REDACTED]'); report['traceback']=traceback.format_exc().replace(PW,'[REDACTED]')
finally:
    if 'connections' in globals(): connections.close_all()
    if started: pg('pg_ctl','-D',DBDIR,'-m','fast','-w','stop')
    with socket.socket() as sock: report['port_closed']=sock.connect_ex(('127.0.0.1',PORT))!=0
    report['finished_utc']=datetime.now(timezone.utc).isoformat()
    write(OUT/'results.json',report)
    print(json.dumps({'evidence':str(OUT),'cases':len(report['cases']),'failed':sum(not x['ok'] for x in report['cases']),'error':report.get('error'),'port_closed':report['port_closed']}))
raise SystemExit(1 if report.get('error') or any(not x['ok'] for x in report['cases']) else 0)
