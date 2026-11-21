"""Stage13-B read-only HTTP queries, plus rolled-back identity invalidation.

Only audit13_settings marked fixtures; no checkout, no operational database.
Evidence contains no credentials, cookies, session keys or raw giant payloads.
"""
import hashlib
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from html import unescape
from pathlib import Path
from unittest.mock import patch
from audit13_run import setup, RESULTS, ROOT, write

setup()
from django.apps import apps
from django.db import DatabaseError, connection, transaction
from django.test import Client
from django.test.utils import setup_test_environment
from django.utils import timezone as tz
from identity.models import Account, Role
from sales.models import Sale

setup_test_environment()
logging.getLogger('django.request').disabled = True
run = Path(os.environ['AUDIT13_RUN_DIR'])
fixture = json.loads((run/'fixture.json').read_text(encoding='utf-8'))
assert Sale.objects.count() == (0 if fixture.get('empty') else len(fixture['sales'])), 'New unconsumed fixture required'
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
out = RESULTS/'evidencias'/('13-B-servidor-'+stamp)
out.mkdir(exist_ok=False)
results = []

def record(case, expected, actual, **extra):
    results.append(dict(id=case, expected=expected, observed=actual,
        status='CUMPLE' if expected == actual else 'INCUMPLE', **extra))

def business():
    rows={}
    for app in ['catalog','inventory','cash','sales']:
        for model in apps.get_app_config(app).get_models():
            rows[model._meta.label]=sorted(json.dumps(r,sort_keys=True,default=str) for r in model.objects.values())
    return hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()

users={key:Account.objects.get(pk=pk) for key,pk in fixture['accounts'].items()}
clients={}
for key,user in users.items():
    client=Client(raise_request_exception=False); client.force_login(user); clients[key]=client
admin=clients['admin']
before=business()
summary=admin.get('/inicio/').context['summary']
expected_summary=(dict(sales_count=0,sales_total='0.00',discount_total='0.00',open_shifts=0,low_stock=0,expiring=0,expired=0)
    if fixture.get('empty') else fixture['expected_summary'])
record('FINAL-admin-values',expected_summary,{k:format(v,'.2f') if isinstance(v,Decimal) else v for k,v in summary.items()})
record('FINAL-warehouse-values',{k:expected_summary[k] for k in ['low_stock','expiring','expired']},clients['warehouse'].get('/inicio/').context['summary'])
record('FINAL-lima-date',fixture['date_lima'],str(admin.get('/inicio/').context['summary_date']))

# Seven literal D11 error classes, impossible calendar values and representable upper limits.
cases=[
 ('nul',{'correlativo':'V-\x00'},'Los filtros contienen caracteres no válidos.'),
 ('date-format',{'fecha':'bad'},'La fecha ingresada no es válida.'),
 ('date-impossible',{'fecha':'2026-02-30'},'La fecha ingresada no es válida.'),
 ('date-overflow',{'fecha':'9999-12-31'},'La fecha ingresada no es válida.'),
 ('date-noniso',{'fecha':'20260101'},'La fecha ingresada no es válida.'),
 ('from-format',{'fecha_desde':'bad'},'La fecha inicial ingresada no es válida.'),
 ('from-impossible',{'fecha_desde':'2026-02-30'},'La fecha inicial ingresada no es válida.'),
 ('to-format',{'fecha_hasta':'bad'},'La fecha final ingresada no es válida.'),
 ('to-impossible',{'fecha_hasta':'2026-02-30'},'La fecha final ingresada no es válida.'),
 ('to-overflow',{'fecha_hasta':'9999-12-31'},'La fecha final ingresada no es válida.'),
 ('range',{'fecha_desde':'2026-01-02','fecha_hasta':'2026-01-01'},'La fecha inicial no puede ser posterior a la fecha final.'),
 ('seller',{'vendedor':'bad'},'El vendedor seleccionado no es válido.'),
 ('shift',{'turno':'bad'},'El turno seleccionado no es válido.'),
 ('date-long',{'fecha':'9'*5000},'La fecha ingresada no es válida.'),
]
for label,params,message in cases:
    res=admin.get('/ventas/historial/',params); html=unescape(res.content.decode())
    record('D11-'+label,dict(status=200,message=True,rows=0),dict(status=res.status_code,message=message in html,rows=len(res.context['sales']) if res.status_code==200 else None),param_lengths={k:len(v) for k,v in params.items()})

for label,params,count in [
 ('today',{'fecha':str(tz.localdate())},0 if fixture.get('empty') else 3),
 ('today-range',{'fecha_desde':str(tz.localdate()),'fecha_hasta':str(tz.localdate())},0 if fixture.get('empty') else 3),
 ('empty',{},0 if fixture.get('empty') else 5),
 ('long-correlative',{'correlativo':'x'*5000},0),
 ('unknown-seller',{'vendedor':'00000000-0000-0000-0000-000000000000'},0),
 ('unknown-shift',{'turno':'00000000-0000-0000-0000-000000000000'},0),
 ('first-day',{'fecha':'0001-01-01'},0),
 ('last-supported-day',{'fecha':'9999-12-30'},0),
]:
    res=admin.get('/ventas/historial/',params)
    record('D10-'+label,dict(status=200,rows=count),dict(status=res.status_code,rows=len(res.context['sales']) if res.status_code==200 else None))

for label,value,days,msg in [
 ('default',None,30,False),('empty','',30,False),('min','1',1,False),('max','3650',3650,False),
 ('zero','0',30,True),('negative','-1',30,True),('above','3651',30,True),('decimal','1.5',30,True),
 ('plus','+1',30,True),('unicode','١',30,True),('repeat',['1','3650'],3650,False),
 ('leadingzeros',' 00001 ',1,False),('negativezeros','-00001',30,True),('giant','9'*5000,30,True),
 ('giant-zeros','0'*5000+'1',1,False),('spaces','  ',30,False),('null','\x00',30,True)]:
    res=admin.get('/productos/vencimientos/',{} if value is None else {'dias':value})
    record('D06-'+label,dict(status=200,days=days,message=msg),dict(status=res.status_code,days=res.context['days'] if res.status_code==200 else None,message='por defecto.' in unescape(res.content.decode())),request_length=len(value or ''))
    if res.status_code==200:
        upcoming=0 if fixture.get('empty') else (2 if days==1 else 8 if days==3650 else 6)
        expired=0 if fixture.get('empty') else 5
        record('D07-'+label,dict(expired=expired,upcoming=upcoming,rows=expired+upcoming),dict(expired=res.context['expired_count'],upcoming=res.context['upcoming_count'],rows=len(res.context['lots'])))

for role,route in [('seller','/inventario/stock/'),('seller','/productos/vencimientos/'),('seller','/productos/'),('warehouse','/ventas/historial/'),('warehouse','/caja/turnos/'),('warehouse','/empleados/')]:
    for method in ['get','post']:
        res=getattr(clients[role],method)(route,{})
        html=unescape(res.content.decode())
        record('DENY-'+role+'-'+method+route,dict(status=403,no_data=True),dict(status=res.status_code,no_data=all(x not in html for x in ['Audit13 venta-integracion','V-90000001','S/ 60,06'])))

for label,mutate in [('inactive',lambda u: Account.objects.filter(pk=u.pk).update(is_active=False)),('invalid-role',lambda u: Role.objects.filter(pk=u.role_id).update(code='INVALID'))]:
    with transaction.atomic():
        actor=users['admin']; invalid=Client(raise_request_exception=False); invalid.force_login(actor); mutate(actor)
        res=invalid.get('/inicio/'); html=unescape(res.content.decode())
        record('ACCOUNT-'+label,dict(status=302 if label=='inactive' else 403,no_summary=True),dict(status=res.status_code,no_summary='Ventas de hoy' not in html and 'S/ 60,06' not in html))
        if label=='inactive': record('ACCOUNT-revoked-session',False,'_auth_user_id' in invalid.session)
        transaction.set_rollback(True)
res=Client().get('/inicio/')
record('ACCOUNT-anonymous',302,res.status_code)

for role,cl in clients.items():
    res=cl.get('/inicio/'); summary=res.context['summary'] or {}
    record('ROLE-'+role,7 if role=='admin' else 3 if role=='warehouse' else 0,len(summary))
    for method in ['post','head']: record('METHOD-'+role+'-'+method,405,getattr(cl,method)('/inicio/').status_code)

for target,route in [('identity.views._dashboard_summary','/inicio/'),('inventory.views.render','/inventario/stock/'),('catalog.views.render','/productos/vencimientos/'),('sales.views.render','/ventas/historial/')]:
    with patch(target,side_effect=DatabaseError('synthetic test failure')):
        res=admin.get(route)
    html=unescape(res.content.decode())
    record('FAILURE-'+route,dict(status=500,no_zero=True,no_detail=True,action=True),dict(status=res.status_code,no_zero='S/ 0,00' not in html,no_detail='synthetic test failure' not in html,action='actualiza la página' in html))
    record('RECOVERY-'+route,200,admin.get(route).status_code)

if fixture.get('empty'):
    res=admin.get('/inicio/')
    record('EMPTY-summary',dict(sales_count=0,sales_total=Decimal('0'),discount_total=Decimal('0'),open_shifts=0,low_stock=0,expiring=0,expired=0),res.context['summary'])
    for route,texts in [('/inventario/stock/',['Sin alertas de stock bajo ni de vencimiento.','No hay productos registrados en el catálogo todavía.']),('/productos/vencimientos/',['No hay lotes con unidades disponibles que estén vencidos o venzan en los próximos 30 días.']),('/ventas/historial/',['No se encontraron ventas con los filtros aplicados.'])]:
        res=admin.get(route); html=unescape(res.content.decode())
        record('EMPTY-'+route,[True]*len(texts),[t in html for t in texts])
else:
    res=admin.get('/inventario/stock/'); html=unescape(res.content.decode())
    record('H13-07-threshold',True,'Stock vigente en el mínimo o por debajo' in html)
    record('H13-07-equality',True,any(p.name=='Audit13 igual-minimo' for p in res.context['low_stock']))
    record('H13-07-receipt',True,'mercadería recibida' in unescape(clients['warehouse'].get('/inicio/').content.decode()))
    record('H13-06-link-context',True,'Historial de ventas (todas las fechas)' in unescape(admin.get('/inicio/').content.decode()))
record('NO-BUSINESS-MUTATION',before,business())
paths=['identity/views.py','identity/templates/identity/dashboard.html','inventory/templates/inventory/stock_overview.html','sales/views.py','templates/500.html']
report=dict(pasada=1,sublote='13-B-03',at_utc=datetime.now(timezone.utc).isoformat(),date_lima=str(tz.localdate()),run=run.name,empty=bool(fixture.get('empty')),engine=connection.vendor,layer='Django Client; not browser',sha256_08=hashlib.sha256((ROOT/'08_Historias_de_Usuario.md').read_bytes()).hexdigest(),sha256_files={p:hashlib.sha256((ROOT/'r1-pmv'/p).read_bytes()).hexdigest() for p in paths if (ROOT/'r1-pmv'/p).exists()},results=results,passed=sum(x['status']=='CUMPLE' for x in results),total=len(results))
write(out/'results.json',report)
print(json.dumps(dict(evidence=str(out),passed=report['passed'],total=report['total'],failed=[x['id'] for x in results if x['status']!='CUMPLE']),ensure_ascii=False))
raise SystemExit(0 if report['passed']==report['total'] else 1)
