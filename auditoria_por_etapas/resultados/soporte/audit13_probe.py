"""Repeatable HTTP/service probes on a newly marked audit13 fixture database only."""
from __future__ import annotations
import hashlib, json, os, re, sys, uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from audit13_run import setup, write, ROOT, RESULTS

setup()
from django.apps import apps
from django.db import connection, transaction
from django.test import Client
from django.test.utils import setup_test_environment, CaptureQueriesContext
from django.utils import timezone as tz
from django.core.exceptions import PermissionDenied
from identity.models import Account, Role
from identity.views import _dashboard_summary
from inventory.models import Lot, StockWriteOff
from inventory.services import write_off_stock
from catalog.models import Product
from sales.models import Sale, SaleLine, SaleDraft
from sales.services import add_product_to_draft, checkout_sale
from cash.models import CashShift
from cash.services import close_cash_shift

setup_test_environment()
run = Path(os.environ['AUDIT13_RUN_DIR'])
fixture = json.loads((run/'fixture.json').read_text(encoding='utf-8'))
# A probe includes confirmed service writes. Never reuse a previously consumed
# fixture, including runs created before this marker was added.
expected_sales = 0 if fixture.get('empty') else len(fixture['sales'])
if Sale.objects.count() != expected_sales or StockWriteOff.objects.exists():
    raise SystemExit('Prepare a new audit13 fixture; this database was already consumed.')
with (run/'probe-started.json').open('x', encoding='utf-8') as marker:
    json.dump({'started_utc': datetime.now(timezone.utc).isoformat()}, marker)
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
out = RESULTS/'evidencias'/('13-servidor-'+stamp)
out.mkdir(exist_ok=False)
results = []

def record(case, expected, observed, status=None, **extra):
    status = status or ('CUMPLE' if expected == observed else 'INCUMPLE')
    results.append({'id':case,'expected':expected,'observed':observed,'status':status,**extra})

def business():
    rows = {}
    for app in ['catalog','inventory','cash','sales']:
        for model in apps.get_app_config(app).get_models():
            rows[model._meta.label] = sorted([json.dumps(x,sort_keys=True,default=str) for x in model.objects.values()])
    return hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()

def normalized(summary):
    return {k:format(v,'.2f') if isinstance(v,Decimal) else v for k,v in summary.items()}

users={key:Account.objects.get(pk=pk) for key,pk in fixture['accounts'].items()}
clients={}
for key,user in users.items():
    client=Client(raise_request_exception=False); client.force_login(user); clients[key]=client
admin, wh, seller = clients['admin'],clients['warehouse'],clients['seller']
before=business()
base = admin.get('/inicio/')
summary=normalized(base.context['summary'])
if fixture.get('empty'):
    record('13-S-EMPTY',dict(sales_count=0,sales_total='0.00',discount_total='0.00',open_shifts=0,low_stock=0,expiring=0,expired=0),summary)
    for key,cl in clients.items():
        res=cl.get('/inicio/')
        record('13-S-EMPTY-'+key,200,res.status_code)
    for route in ['/inventario/stock/','/productos/vencimientos/','/ventas/historial/']:
        res=admin.get(route)
        record('13-S-EMPTY-DEST-'+route,200,res.status_code)
else:
    record('13-S-01-SUMMARY',fixture['expected_summary'],summary)
    captured={}
    for key,code,nq in [('admin',Role.Code.ADMIN,4),('warehouse',Role.Code.WAREHOUSE,2),('seller',Role.Code.SELLER,0)]:
        with CaptureQueriesContext(connection) as queries: partial=_dashboard_summary(code,tz.localdate())
        captured[key]=[q['sql'] for q in queries]
        record('13-S-02-QUERY-COUNT-'+key,nq,len(queries),note='Observed implementation budget for this build only')
        expected_keys = sorted(summary) if key=='admin' else ['expired','expiring','low_stock'] if key=='warehouse' else []
        record('13-S-02-KEYS-'+key,expected_keys,sorted(partial or {}))
        if key!='admin':
            record('13-S-02-NO-FINANCIAL-QUERIES-'+key, False,any('sales_sale' in s or 'cash_cashshift' in s for s in captured[key]))
    write(out/'summary-queries.json',captured)
    today=tz.localdate()
    write(out/'source-rows.json',{
      'sales':list(Sale.objects.order_by('confirmed_at').values('correlative','confirmed_at','total_amount','discount_amount','cash_received','change_given','seller_id','cash_shift_id')),
      'products':[{'name':p.name,'active':p.is_active,'category_active':p.category.is_active,'minimum':p.minimum_stock,'physical':p.physical_stock,'sellable':p.sellable_stock} for p in Product.objects.select_related('category').prefetch_related('lots')],
      'lots':list(Lot.objects.order_by('expiration_date').values('number','expiration_date','available_quantity','product__is_active','product__category__is_active')),
      'shifts':list(CashShift.objects.values('status','opened_at','seller_id'))})
    for key,cl in clients.items():
        res=cl.get('/inicio/'); html=res.content.decode()
        record('13-S-03-ROLE-'+key,{'status':200,'financial':key=='admin','inventory':key in ('admin','warehouse')}, {'status':res.status_code,'financial':'Ventas de hoy' in html,'inventory':'Productos con stock bajo' in html})
        record('13-S-03-DATE-'+key,key in ('admin','warehouse'),today.strftime('%d/%m/%Y')+' · Lima' in html)
        record('13-S-04-CACHE-'+key,True,all(x in res.headers.get('Cache-Control','') for x in ['no-cache','no-store','private']))
    for query in ['', '?fecha=1900-01-01&fecha_desde=bad&dias=0&vendedor=unknown','?fecha=&dias=','?dias=abc','?dias=1&dias=3650']:
        record('13-S-05-IGNORED-PARAMS-'+str(len(results)),summary,normalized(admin.get('/inicio/'+query).context['summary']))
    overview=admin.get('/inventario/stock/')
    record('13-S-06-OVERVIEW',{'low':3,'upcoming':6,'expired':5},{'low':len(overview.context['low_stock']),'upcoming':len(overview.context['expiring_lots']),'expired':len(overview.context['expired_lots'])})
    exp=admin.get('/productos/vencimientos/')
    record('13-S-07-EXPIRATIONS',{'days':30,'upcoming':6,'expired':5,'rows':11},{'days':exp.context['days'],'upcoming':exp.context['upcoming_count'],'expired':exp.context['expired_count'],'rows':len(exp.context['lots'])})
    hist=admin.get('/ventas/historial/')
    histday=admin.get('/ventas/historial/',{'fecha':str(today)})
    record('13-S-08-HISTORY-ALL',{'count':5,'total':'243.39'},{'count':len(hist.context['sales']),'total':str(sum((s.total_amount for s in hist.context['sales']),Decimal('0.00')))})
    record('13-S-09-HISTORY-DAY',{'count':3,'total':'60.06','discount':'5.06'},{'count':len(histday.context['sales']),'total':str(sum((s.total_amount for s in histday.context['sales']),Decimal('0.00'))),'discount':str(sum((s.discount_amount for s in histday.context['sales']),Decimal('0.00')))})
    for key,cl in [('seller',seller),('seller2',clients['seller2'])]:
        own=cl.get('/ventas/historial/',{'vendedor':users['seller2' if key=='seller' else 'seller'].pk,'fecha':str(today)})
        record('13-S-09-OWN-HISTORY-'+key,{'count':2 if key=='seller' else 1,'owners':[str(users[key].pk)]},{'count':len(own.context['sales']),'owners':sorted(set(str(s.seller_id) for s in own.context['sales']))})
    with patch('django.utils.timezone.localdate',return_value=today+timedelta(days=1)):
        n=normalized(admin.get('/inicio/').context['summary'])
    record('13-S-10-DATE-ROLLOVER',{'sales_count':1,'sales_total':'92.22'},{k:n[k] for k in ['sales_count','sales_total']},note='Clock patched to next Lima day; no browser midnight claim')
    with transaction.atomic():
        Product.objects.all().update(sale_price=Decimal('999.99'))
        SaleLine.objects.all().update(amount=Decimal('0.01'))
        n=normalized(admin.get('/inicio/').context['summary'])
        record('13-S-11-SNAPSHOTS',summary,n,note='Fixture transaction rolled back; total read from Sale snapshots, not product price/SaleLine')
        transaction.set_rollback(True)

# Direct methods and role-denied destinations; session rows are deliberately excluded from business hash.
for key,cl in clients.items():
    record('13-S-12-POST-'+key,405,cl.post('/inicio/',{'sales_total':'999','role':'ADMIN'}).status_code)
    record('13-S-12-HEAD-'+key,405,cl.head('/inicio/').status_code)
for key,route in [('warehouse','/ventas/historial/'),('seller','/inventario/stock/'),('seller','/productos/vencimientos/'),('seller','/productos/nuevo/'),('warehouse','/empleados/'),('admin','/ventas/')]:
    for method in ['get','post']:
        record('13-S-13-DENY-'+key+method+route,403,getattr(clients[key],method)(route,{}).status_code)
anon=Client()
res=anon.get('/inicio/')
record('13-S-14-ANON',{'status':302,'location':'/?next=/inicio/'},{'status':res.status_code,'location':res.headers.get('Location')})
record('13-S-15-NO-MUTATION',before,business())

# Input boundaries of the dashboard's expiration destination. Record defect before any fix.
for label,value,days,msg in [('default',None,30,False),('empty','',30,False),('min','1',1,False),('max','3650',3650,False),('zero','0',30,True),('negative','-1',30,True),('above','3651',30,True),('decimal','1.5',30,True),('plus','+1',30,True),('unicode','١',30,True),('repeat',['1','3650'],3650,False),('five-significant-digits','10000',30,True),('leadingzeros',' 00001 ',1,False),('negativezeros','-00001',30,True)]:
    res=admin.get('/productos/vencimientos/',{} if value is None else {'dias':value})
    expected={'status':200,'days':days,'message':msg}
    observed={'status':res.status_code,'days':res.context['days'] if res.status_code==200 else None,'message':('por defecto.' in res.content.decode()) if res.status_code==200 else None}
    record('13-S-16-DAYS-'+label,expected,observed,request_length=0 if value is None else len(value),note='No raw giant query logged in evidence')

if not fixture.get('empty'):
    # Serialized cross-role service flow. Separate from fixture snapshots.
    product=Product.objects.get(pk=fixture['products']['venta-integracion'])
    draft=add_product_to_draft(actor=users['seller'],product_id=product.pk,quantity=2)
    record('13-S-17-DRAFT-IGNORED',summary,normalized(admin.get('/inicio/').context['summary']))
    sale=checkout_sale(actor=users['seller'],draft_id=draft.pk,cash_received=Decimal('10.00'),idempotency_key=uuid.uuid4())
    after_sale=normalized(admin.get('/inicio/').context['summary'])
    record('13-S-18-SELLER-TO-ADMIN',{'sales_count':4,'sales_total':'67.16','discount_total':'5.06','low_stock':4}, {k:after_sale[k] for k in ['sales_count','sales_total','discount_total','low_stock']},sale=str(sale.pk),received=str(sale.cash_received),change=str(sale.change_given))
    record('13-S-19-SELLER-TO-WAREHOUSE',4,wh.get('/inicio/').context['summary']['low_stock'])
    lot=Lot.objects.get(product=product)
    record('13-S-20-FEFO-BALANCE',1,lot.available_quantity)
    before_denied=business()
    try: write_off_stock(actor=users['seller'],lot=lot,quantity=1,reason='DAÑO')
    except PermissionDenied: denied=True
    else: denied=False
    record('13-S-21-SERVICE-DENIAL',{'denied':True,'unchanged':True},{'denied':denied,'unchanged':before_denied==business()})
    write_off_stock(actor=users['warehouse'],lot=lot,quantity=1,reason='DAÑO',notes='Audit13 isolated integration')
    record('13-S-22-WAREHOUSE-TO-ADMIN',5,admin.get('/inicio/').context['summary']['expiring'])
    close=close_cash_shift(actor=users['seller'],counted_amount=Decimal('159.37'))
    record('13-S-23-CLOSE-TO-ADMIN',0,admin.get('/inicio/').context['summary']['open_shifts'],expected_cash=str(close.expected_amount),difference=str(close.difference))
    record('13-S-24-CLOSE-PRESERVES-TODAY',4,admin.get('/inicio/').context['summary']['sales_count'])

report={'run':run.name,'database':str(run/'audit.sqlite3'),'engine':connection.vendor,'at_utc':datetime.now(timezone.utc).isoformat(),'date_lima':str(tz.localdate()),'fixture':fixture,'results':results,'counts':{status:sum(r['status']==status for r in results) for status in ['CUMPLE','INCUMPLE']},'limitations':['HTTP client is not visual browser','SQLite does not verify PostgreSQL locks or snapshot concurrency','This run mutates only its new marked isolated DB; do not rerun against a populated probe DB','Fixtures have synthetic historical snapshots; service integration is separately identified']}
write(out/'results.json',report)
print(json.dumps({'evidence':str(out),'counts':report['counts']},ensure_ascii=False))
raise SystemExit(1 if report['counts']['INCUMPLE'] else 0)
