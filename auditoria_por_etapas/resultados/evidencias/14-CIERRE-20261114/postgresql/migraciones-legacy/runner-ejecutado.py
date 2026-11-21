"""Real MigrationExecutor on isolated SQLite schema: rejected legacy rows remain unchanged."""
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import secrets
import sys
import traceback
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'r1-pmv/manage.py').exists())
OUT=Path(sys.argv[1]).resolve();OUT.mkdir(parents=True,exist_ok=False)
(OUT/'runner-ejecutado.py').write_bytes(Path(__file__).read_bytes())
sha=lambda b:hashlib.sha256(b).hexdigest()
save=lambda p,d:p.write_text(json.dumps(d,ensure_ascii=False,indent=2,default=str)+'\n',encoding='utf-8')
spec=importlib.util.spec_from_file_location('base14',HERE.parents[1]/'14-D-20261113/navegador/recorrido.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
report=dict(started_utc=datetime.now(timezone.utc).isoformat(),engine='SQLite :memory:',pasada=1,scope='Diagnóstico previo real cash0004/sales0007 con datos ficticios; no base operativa',
    before=base.build(),plan08=sha((ROOT/'08_Historias_de_Usuario.md').read_bytes()),cases=[])
os.environ.update(APP_ENV='test',DJANGO_DEBUG='false',DJANGO_SETTINGS_MODULE='config.settings',DJANGO_SECRET_KEY=secrets.token_urlsafe(48),DJANGO_ALLOWED_HOSTS='testserver')
sys.path.insert(0,str(ROOT/'r1-pmv'))
from config import env
env.load_dotenv=lambda path=None:None
from django.conf import settings
settings.DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}
import django
django.setup()
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.recorder import MigrationRecorder

def row(model,pk):return model.objects.filter(pk=pk).values().get()
def reject(target,rows):
    before={name:row(model,pk) for name,(model,pk) in rows.items()}
    try:MigrationExecutor(connection).migrate([target])
    except RuntimeError as e:message=str(e)
    else:raise AssertionError('Migration should reject invalid legacy data')
    after={name:row(model,pk) for name,(model,pk) in rows.items()}
    assert before==after
    assert not MigrationRecorder.Migration.objects.filter(app=target[0],name=target[1]).exists()
    report['cases'].append(dict(id=target[0]+'-invalid-rejected',ok=True,message=message,all_original_values_unchanged=True,migration_not_marked_applied=True,rows=before))
    save(OUT/'results-partial.json',report)
def accept(target,rows):
    before={name:row(model,pk) for name,(model,pk) in rows.items()}
    MigrationExecutor(connection).migrate([target])
    after={name:row(model,pk) for name,(model,pk) in rows.items()}
    assert before==after and MigrationRecorder.Migration.objects.filter(app=target[0],name=target[1]).exists()
    report['cases'].append(dict(id=target[0]+'-valid-applied',ok=True,all_original_values_unchanged=True,migration_marked_applied=True,rows=before))
    save(OUT/'results-partial.json',report)
try:
    executor=MigrationExecutor(connection)
    targets=[t for t in executor.loader.graph.leaf_nodes() if t[0] not in ('cash','sales')]+[('cash','0003_cashshiftclose'),('sales','0006_sale_lot_traceability')]
    executor.migrate(targets)
    apps=executor.loader.project_state(targets).apps
    Role=apps.get_model('identity','Role');Account=apps.get_model('identity','Account')
    Category=apps.get_model('catalog','Category');Product=apps.get_model('catalog','Product')
    Register=apps.get_model('cash','CashRegister');Shift=apps.get_model('cash','CashShift');Close=apps.get_model('cash','CashShiftClose')
    Draft=apps.get_model('sales','SaleDraft');Line=apps.get_model('sales','SaleDraftLine');Sale=apps.get_model('sales','Sale')
    role=Role.objects.create(code='VENDEDOR',name='Vendedor')
    seller=Account.objects.create(email='legacy@audit14.invalid',password='!',display_name='Legacy ficticio',role=role)
    register=Register.objects.create(code='CAJA-01',is_active=True)
    shift=Shift.objects.create(cash_register=register,seller=seller,opening_amount=Decimal('100'),status='CLOSED')
    closure=Close.objects.create(cash_shift=shift,closed_by=seller,counted_amount=Decimal('-1'),expected_amount=Decimal('100'),difference=Decimal('0'))
    cash_rows={'cash_close':(Close,closure.pk),'cash_shift':(Shift,shift.pk)}
    reject(('cash','0004_integration_money_limits'),cash_rows)
    # Controlled fixture correction only; diagnostic itself must not edit any value.
    Close.objects.filter(pk=closure.pk).update(counted_amount=Decimal('100'),difference=Decimal('0'))
    accept(('cash','0004_integration_money_limits'),cash_rows)
    category=Category.objects.create(name='Legado14',name_normalized='LEGADO14')
    product=Product.objects.create(category=category,name='Producto legado14',search_name='producto legado14',barcode='INT-LEGADO14',barcode_normalized='INT-LEGADO14',sale_price=Decimal('10'))
    draft=Draft.objects.create(cash_shift=shift,seller=seller,status='ACTIVE')
    line=Line.objects.create(draft=draft,product=product,quantity=1000000,unit_price=Decimal('10'))
    sale=Sale.objects.create(cash_shift=shift,seller=seller,total_amount=Decimal('-1'),base_amount=Decimal('0'),igv_amount=Decimal('0'),discount_amount=Decimal('0'),cash_received=Decimal('0'),change_given=Decimal('0'),correlative='V-00000001',idempotency_key=uuid.uuid4())
    sales_rows={'sale':(Sale,sale.pk),'draft_line':(Line,line.pk),'draft':(Draft,draft.pk)}
    reject(('sales','0007_integration_money_limits'),sales_rows)
    Line.objects.filter(pk=line.pk).update(quantity=999999)
    Sale.objects.filter(pk=sale.pk).update(total_amount=Decimal('10000000.00'),base_amount=Decimal('10000000.00'),cash_received=Decimal('10000000.00'))
    accept(('sales','0007_integration_money_limits'),sales_rows)
    report['valid_legacy_sale_above_new_operation_limit_preserved']='10000000.00'
    report['ok']=True
except Exception as e:
    report.update(ok=False,error=type(e).__name__,detail=str(e),traceback=traceback.format_exc())
finally:
    connection.close()
    report.update(after=base.build(),finished_utc=datetime.now(timezone.utc).isoformat())
    report['source_stable']=report['before']==report['after']
    report['ok']=report.get('ok',False) and report['source_stable']
    save(OUT/'results.json',report)
    print(json.dumps({k:report[k] for k in ('ok','source_stable')})+' cases='+str(len(report['cases'])))
sys.exit(0 if report['ok'] else 1)
