"""Reproduce diferencias actuales en datos nuevos, sin modificar el producto."""
from pathlib import Path
import contextlib,hashlib,io,json,os,secrets,sys,traceback,uuid
from datetime import datetime,timedelta,timezone
from decimal import Decimal
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3];APP=ROOT/'r1-pmv'
RUN=HERE/('contrastes-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(3))
RUN.mkdir(exist_ok=False);(RUN/'tmp').mkdir()
sys.dont_write_bytecode=True
os.environ.update(TEMP=str(RUN/'tmp'),TMP=str(RUN/'tmp'),PYTHONDONTWRITEBYTECODE='1')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected=[p for p in APP.rglob('*') if p.is_file() and '.venv' not in p.parts and '__pycache__' not in p.parts and '.git' not in p.parts and p.suffix in ('.py','.html','.css','.js','.sqlite3','.yaml','.yml','.toml')]
before={p.relative_to(ROOT).as_posix():sha(p) for p in protected}
(RUN/'protected-before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
def own(p):
    if isinstance(p,int):return True
    try:return Path(p).resolve().is_relative_to(RUN)
    except (TypeError,ValueError):return False
def guard(event,args):
    if event=='open':
        p,mode,flags=args
        if not isinstance(p,int) and Path(p).resolve()==APP/'.env':raise PermissionError('No operator environment read')
        writing=(isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        if writing and not own(p):raise PermissionError('Write outside owned run')
    if event=='sqlite3.connect' and not own(args[0]):raise PermissionError('Database outside owned run')
sys.addaudithook(guard)
report={'run':RUN.relative_to(ROOT).as_posix(),'started_utc':datetime.now(timezone.utc).isoformat(),'engine':'SQLite','scope':'Servicios/ORM de datos ficticios; no navegador, no concurrencia'}
try:
    sys.path.insert(0,str(APP))
    os.environ.update(APP_ENV='test',DATABASE_URL='sqlite',DJANGO_DEBUG='false',DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost,testserver',DJANGO_SECRET_KEY=secrets.token_urlsafe(48),DJANGO_SETTINGS_MODULE='config.settings')
    from config import env
    loader=env.load_dotenv;env.load_dotenv=lambda path=None:None
    try:
        from django.conf import settings
        settings.INSTALLED_APPS
    finally:env.load_dotenv=loader
    settings.DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':RUN/'data.sqlite3'}}
    import django
    django.setup()
    from django.core.management import call_command
    from django.core.exceptions import ValidationError
    from django.db import connection
    from django.utils import timezone as tz
    from unittest.mock import patch
    from identity.models import Account,Role
    from catalog.models import Category,Product
    from inventory.models import Lot,StockWriteOff,InitialInventoryLoad
    from inventory.services import LotInput,confirm_initial_load,register_stock_entry,write_off_stock,register_physical_adjustment
    from cash.models import CashRegister
    from cash.services import open_cash_shift
    from sales.models import Sale,SaleLine
    from sales.services import add_product_to_draft,checkout_sale
    log=io.StringIO()
    with contextlib.redirect_stdout(log):call_command('migrate',interactive=False,verbosity=0)
    roles={c:Role.objects.create(code=c,name=c) for c in ['ADMIN','ALMACENERO','VENDEDOR']}
    actors={c:Account.objects.create_user(f'{c.lower()}@contraste.invalid',secrets.token_urlsafe(24)+'Aa1!',display_name='Persona ficticia '+c,role=r) for c,r in roles.items()}
    category=Category.objects.create(name='Categoria ficticia contraste')
    product=Product.objects.create(category=category,name='Producto ficticio contraste',barcode='INTERNO-CONTRASTE',sale_price=Decimal('10'))
    t0=tz.localdate(); t2=t0+timedelta(days=2)
    load=confirm_initial_load(actor=actors['ALMACENERO'],product=product,lots=[LotInput('A',10,Decimal('2'),t0+timedelta(days=1)),LotInput('B',10,Decimal('4'),t0+timedelta(days=30))])
    CashRegister.objects.create(code='CAJA-01')
    shift=open_cash_shift(actor=actors['VENDEDOR'],opening_amount=Decimal('100'))
    draft=add_product_to_draft(actor=actors['VENDEDOR'],product_id=product.pk,quantity=2)
    sale=checkout_sale(actor=actors['VENDEDOR'],draft_id=draft.pk,cash_received=Decimal('20'),idempotency_key=uuid.uuid4())
    def snap():
        product.refresh_from_db()
        lots=list(Lot.objects.filter(product=product).order_by('number').values('number','available_quantity','initial_quantity','unit_cost','expiration_date'))
        return {'physical':sum(x['available_quantity'] for x in lots),'sellable_on_t2':sum(x['available_quantity'] for x in lots if x['expiration_date']>t2),'average':str(product.average_cost),'lots':lots,'sales_count':Sale.objects.count(),'writeoffs':StockWriteOff.objects.count()}
    report['after_sale']=snap()
    line=SaleLine.objects.get(sale=sale)
    report['sale_cost_snapshot']=str(line.unit_cost)
    with patch('django.utils.timezone.localdate',return_value=t2):
        report['after_expiration_without_mutation']=snap()
        receipt=register_stock_entry(actor=actors['ALMACENERO'],product=product,lots=[LotInput('C',10,Decimal('6'),t0+timedelta(days=40))],business_date=t2)
        report['after_receipt']=snap()
        report['receipt_reuses_initial_load']=receipt.pk==load.pk
        before_retry=snap()
        try:
            register_stock_entry(actor=actors['ALMACENERO'],product=product,lots=[LotInput('C',10,Decimal('6'),t0+timedelta(days=40))],business_date=t2)
            report['repeat_result']='accepted'
        except ValidationError as exc:report['repeat_result']={'error':exc.messages}
        report['repeat_rejection_without_mutation']=snap()==before_retry
        lot=Lot.objects.get(product=product,number='A')
        before_theft=snap()
        try:
            write_off_stock(actor=actors['ALMACENERO'],lot=lot,quantity=1,reason=StockWriteOff.Reason.THEFT,notes='Conteo ficticio; falta una unidad')
            report['expired_theft']='accepted'
        except ValidationError as exc:report['expired_theft']={'error':exc.messages}
        report['expired_theft_rejection_without_mutation']=snap()==before_theft
        writeoff=write_off_stock(actor=actors['ADMIN'],lot=lot,quantity=1,reason=StockWriteOff.Reason.EXPIRATION)
        report['admin_writeoff_allowed']=writeoff.responsible_id==actors['ADMIN'].pk
        report['after_writeoff_one_expired']=snap()
        line.refresh_from_db();report['sale_cost_after_changes']=str(line.unit_cost)
    report['new_policy_expected_receipt_cost']=str(((Decimal('18')*Decimal('3')+Decimal('10')*Decimal('6'))/Decimal('28')).quantize(Decimal('0.0001')))
    report['sale_model_fields']=[f.name for f in Sale._meta.fields]
    report['allocation_tables']=[t for t in connection.introspection.table_names() if 'allocation' in t]
    report['sale_line_fields']=[f.name for f in SaleLine._meta.fields]
    report['draft_quantity_constraints']=[c.name for c in __import__('sales.models',fromlist=['SaleDraftLine']).SaleDraftLine._meta.constraints]
    assert report['after_sale']['average']=='3.0000'
    assert report['after_receipt']['average']=='4.5000'
    assert report['after_writeoff_one_expired']['average']=='5.0000'
    assert report['sale_cost_after_changes']=='3.0000'
    assert report['receipt_reuses_initial_load'] and report['repeat_rejection_without_mutation']
    assert report['expired_theft_rejection_without_mutation'] and report['admin_writeoff_allowed']
    assert report['allocation_tables']==[]
    report['reproduced']=True
    connection.close()
except BaseException as exc:
    report['fatal']={'type':type(exc).__name__,'message':str(exc)}
    (RUN/'fatal.log').write_text(traceback.format_exc(),encoding='utf-8')
finally:
    after={k:sha(ROOT/k) for k in before}
    report['changed_protected']=[k for k in before if before[k]!=after[k]]
    report['operator_db_sha256']=after.get('r1-pmv/r1_pmv.sqlite3')
    report['finished_utc']=datetime.now(timezone.utc).isoformat()
    (RUN/'protected-after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
    (RUN/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
    print(json.dumps({'run':report['run'],'reproduced':report.get('reproduced',False),'fatal':report.get('fatal'),'changed_protected':report['changed_protected']},ensure_ascii=True))
raise SystemExit(0 if report.get('reproduced') and not report['changed_protected'] else 1)
