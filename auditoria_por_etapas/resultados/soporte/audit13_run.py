"""Isolated fixtures and runner for stage13. All writes confined to a new marked audit DB."""
from __future__ import annotations
import json, os, secrets, sys, uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import gettempdir

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / 'r1-pmv'
RESULTS = ROOT / 'auditoria_por_etapas/resultados'
SUPPORT = Path(__file__).resolve().parent

def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding='utf-8')

def setup():
    sys.path[:0] = [str(APP), str(SUPPORT)]
    os.environ['DJANGO_SETTINGS_MODULE'] = 'audit13_settings'
    import django
    django.setup()

def fixtures(run, empty=False):
    from django.core.management import call_command
    from django.utils import timezone as tz
    from identity.models import Account, Role
    from catalog.models import Category, Product
    from inventory.models import InitialInventoryLoad, Lot
    from cash.models import CashRegister, CashShift
    from sales.models import Sale, SaleLine
    call_command('migrate', interactive=False, verbosity=0)
    accounts, creds = {}, {}
    for name, code, display in [('admin','ADMIN','Administrador'), ('warehouse','ALMACENERO','Almacenero'), ('seller','VENDEDOR','Vendedor'), ('seller2','VENDEDOR','Vendedor')]:
        role, _ = Role.objects.get_or_create(code=code, defaults={'name': display})
        pw = secrets.token_urlsafe(24) + 'A1!'
        email = name + '@audit13.invalid'
        accounts[name] = Account.objects.create_user(email, pw, role=role, display_name='Audit13 '+display+' '+name)
        creds[name] = {'email': email, 'password': pw}
    private_file = Path(gettempdir()) / 'minimarket-audit13' / run.name / '.credentials.json'
    write(private_file, creds)
    if empty:
        write(run/'fixture.json', {'run':run.name, 'empty':True, 'accounts':{k:str(v.pk) for k,v in accounts.items()}, 'date_lima':str(tz.localdate())})
        print(json.dumps({'run':str(run),'empty':True,'credentials_private':str(private_file)},ensure_ascii=False))
        return
    today = tz.localdate()
    cat = Category.objects.create(name='Audit13 activos')
    cat_off = Category.objects.create(name='Audit13 categoría inactiva', is_active=False)
    products, lots = {}, {}
    spec = [
        ('sin-lotes', 0, True, cat, []),
        ('igual-minimo', 5, True, cat, [(30,5)]),
        ('sobre-minimo', 5, True, cat, [(31,6)]),
        ('solo-vencido', 1, True, cat, [(0,7),(-1,2)]),
        ('mixto', 3, True, cat, [(1,2),(30,2),(31,9),(0,4),(10,0)]),
        ('producto-inactivo', 99, False, cat, [(1,8),(0,3)]),
        ('categoria-inactiva', 99, True, cat_off, [(30,4),(-1,6)]),
        ('venta-integracion', 1, True, cat, [(2,3)]),
    ]
    for n, minimum, active, category, lotdefs in spec:
        p = Product.objects.create(name='Audit13 '+n, barcode='AUDIT13-'+n, category=category, minimum_stock=minimum, is_active=active, sale_price=Decimal('3.55'))
        products[n] = p
        if not lotdefs: continue
        load = InitialInventoryLoad.objects.create(product=p, responsible=accounts['warehouse'])
        for i, (days, qty) in enumerate(lotdefs):
            lot = Lot.objects.create(product=p, initial_load=load, responsible=accounts['warehouse'], number=f'A13-{n}-{i}', initial_quantity=max(qty,1), available_quantity=qty, unit_cost=Decimal('1.2345'), expiration_date=today+timedelta(days=days))
            lots[lot.number] = lot
    register, _ = CashRegister.objects.get_or_create(code='CAJA-01')
    shift_old = CashShift.objects.create(cash_register=register, seller=accounts['seller2'], opening_amount=Decimal('20.00'), status='CLOSED')
    shift = CashShift.objects.create(cash_register=register, seller=accounts['seller'], opening_amount=Decimal('10.00'))
    CashShift.objects.filter(pk=shift.pk).update(opened_at=tz.now()-timedelta(days=1))
    start = tz.make_aware(datetime.combine(today, datetime.min.time()), tz.get_current_timezone())
    sale_specs = [
        ('prev-boundary',start-timedelta(microseconds=1),'91.11','1.11',shift_old,accounts['seller2']),
        ('start-boundary',start,'10.01','0.01',shift_old,accounts['seller2']),
        ('today-other',start+timedelta(hours=10),'20.02','2.02',shift,accounts['seller']),
        ('end-boundary',start+timedelta(days=1)-timedelta(microseconds=1),'30.03','3.03',shift,accounts['seller']),
        ('next-boundary',start+timedelta(days=1),'92.22','2.22',shift,accounts['seller']),
    ]
    sales=[]
    for i,(name,at,total,disc,sh,seller) in enumerate(sale_specs,1):
        s = Sale.objects.create(cash_shift=sh,seller=seller,total_amount=Decimal(total),base_amount=Decimal(total),igv_amount=0,discount_amount=Decimal(disc),cash_received=Decimal(total)+10,change_given=10,correlative=f'V-{90000000+i:08d}',idempotency_key=uuid.uuid4())
        Sale.objects.filter(pk=s.pk).update(confirmed_at=at)
        SaleLine.objects.create(sale=s,product=products['venta-integracion'],product_snapshot_name='Audit13 histórico',product_snapshot_barcode='AUDIT13-HIST',quantity=1,unit_price=Decimal(total)+Decimal(disc),amount=Decimal(total)+Decimal(disc),unit_cost=Decimal('1.2345'))
        sales.append({'name':name,'id':str(s.pk),'at_lima':str(at),'total':total,'discount':disc,'seller':seller.email,'shift':str(sh.pk)})
    fixture={'run':run.name,'date_lima':str(today),'timezone':'America/Lima','accounts':{k:str(v.pk) for k,v in accounts.items()},'products':{k:str(v.pk) for k,v in products.items()},'lots':{k:str(v.pk) for k,v in lots.items()},'sales':sales,'open_shift':str(shift.pk),'closed_shift':str(shift_old.pk),'expected_summary':{'sales_count':3,'sales_total':'60.06','discount_total':'5.06','open_shifts':1,'low_stock':3,'expiring':6,'expired':5},'fixture_note':'Sales/expired lots inserted as synthetic historical snapshots via ORM; not proof of historical checkout or validation. Integration probe separately uses services.'}
    write(run/'fixture.json', fixture)
    print(json.dumps({'run':str(run),'fixture':str(run/'fixture.json'),'credentials_private':str(private_file)},ensure_ascii=False))

if __name__ == '__main__':
    command = sys.argv[1]
    if command == 'new':
        run = RESULTS/'datos'/('etapa13-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+secrets.token_hex(4))
        run.mkdir(parents=True,exist_ok=False)
        write(run/'marker.json',{'run':run.name,'isolated':True})
        private_dir = Path(gettempdir()) / 'minimarket-audit13' / run.name
        private_dir.mkdir(parents=True,exist_ok=False)
        (private_dir/'.django-key').write_text(secrets.token_urlsafe(48),encoding='utf-8')
        os.environ['AUDIT13_RUN_DIR']=str(run)
        setup(); fixtures(run, empty='empty' in sys.argv[2:])
    elif command == 'server':
        setup()
        from django.core.management import call_command
        call_command('runserver','127.0.0.1:'+sys.argv[2],use_reloader=False,insecure=True)
    else:
        raise SystemExit('Use new or server PORT; AUDIT13_RUN_DIR required for server')
