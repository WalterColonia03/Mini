"""Stage03-K runner: fresh marked databases, product registration and role observations.
Usage: tests [labels] | browser | physical | keyboard. Internal modes require marked run.
No reset, no operator .env, no reuse of retained databases.
"""
import contextlib
from datetime import datetime,timezone,timedelta
from decimal import Decimal
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import re
import secrets
import socket
import subprocess
import sys
import time

SUPPORT=Path(__file__).resolve().parent
RESULTS=SUPPORT.parent;ROOT=RESULTS.parent.parent;APP=ROOT/'r1-pmv'
sys.path[:0]=[str(APP),str(SUPPORT)]
import audit03_run as common
write=common.write;digest=common.digest
def setup():
    os.environ['DJANGO_SETTINGS_MODULE']='audit03k_settings'
    import django;django.setup()
def snapshot():
    from catalog.models import Product
    data = common.snapshot()
    data['commerce'] = list(Product.objects.order_by('pk').values('id', 'barcode_normalized', 'search_name', 'average_cost'))
    return data


def fixtures():
    from cash.models import CashRegister
    from cash.services import open_cash_shift
    from catalog.models import Category
    from identity.models import Account
    for name, active in [('Productos enlatados', True), ('Higiene', True), ('Suspendida', False)]:
        Category.objects.create(name=name, is_active=active)
    CashRegister.objects.create(code='CAJA-01')
    seller = Account.objects.get(email='seller@audit03.invalid')
    open_cash_shift(actor=seller, opening_amount=Decimal('50.00'))


def availability_fixture():
    from django.utils import timezone as local_time
    from catalog.models import Category, Product
    from catalog.services import toggle_product_availability
    from identity.models import Account
    from inventory.models import InitialInventoryLoad, Lot

    today = local_time.localdate()
    admin = Account.objects.get(email='admin@audit03.invalid')
    warehouse = Account.objects.get(email='warehouse@audit03.invalid')
    active = Category.objects.create(name='Alimentos')
    suspended = Category.objects.create(name='Suspendida', is_active=False)
    fx = common.effects_fixture(active.pk)
    available = Product.objects.get(pk=fx['product_id'])
    empty = Product.objects.get(pk=fx['empty_product_id'])
    cases = []

    def include(product, stock, badge, offered):
        toggle_product_availability(actor=admin, product=product, is_active=False)
        cases.append(dict(id=str(product.pk), code=product.barcode, stock=stock,
                          badge=badge, offered=offered, price=str(product.sale_price)))

    def lot(product, number, day, quantity):
        load, _ = InitialInventoryLoad.objects.get_or_create(product=product, defaults={'responsible': warehouse})
        Lot.objects.create(product=product, initial_load=load, number=number, initial_quantity=quantity,
                           available_quantity=quantity, unit_cost=Decimal('1.00'), expiration_date=day)

    # Historical lots are seeded directly so yesterday/today can be exercised locally.
    lot(available, 'VENCE-HOY', today, 5)
    lot(available, 'VENCIDO', today - timedelta(days=1), 8)
    include(available, 19, 'Disponible', True)
    include(empty, 0, 'Sin stock vigente', False)
    for name, cat, days, qty, stock, badge in [
        ('Vence hoy', active, 0, 3, 0, 'Sin stock vigente'),
        ('Solo vencido', active, -1, 4, 0, 'Sin stock vigente'),
        ('Categoría suspendida', suspended, 1, 7, 7, 'Categoría desactivada'),
    ]:
        product = Product.objects.create(category=cat, name=name, barcode='K03-'+str(qty), sale_price=Decimal('6.20'))
        lot(product, 'LOTE-'+str(qty), today+timedelta(days=days), qty)
        include(product, stock, badge, False)
    write(Path(os.environ['AUDIT03_OUT'])/'fixture.json', {
        'date_lima':today, 'sale_id':fx['sale_id'], 'cases':cases,
        'lots':list(Lot.objects.order_by('pk').values('number','product_id','available_quantity','expiration_date')),
    })


def keyboard_fixture():
    from catalog.models import Category
    from identity.models import Account, Role
    run = Path(os.environ['AUDIT03_RUN_DIR'])
    category = Category.objects.create(name='Higiene')
    fixture = common.effects_fixture(category.pk)
    credentials = json.loads((run/'.credentials.json').read_text(encoding='utf-8'))
    password = 'Aa1!' + secrets.token_urlsafe(18)
    admin2 = Account.objects.create_user('admin2@audit03.invalid', password,
        display_name='AUD03 segundo ADMIN', role=Role.objects.get(code='ADMIN'))
    credentials['admin2'] = {'email':admin2.email, 'password':password}
    write(run/'.credentials.json', credentials)
    fixture.pop('snapshot')
    write(Path(os.environ['AUDIT03_OUT'])/'fixture.json', fixture)


def main():
    action=sys.argv[1]
    if action in ['serve','snapshot']:
        setup()
        if action=='snapshot':print(json.dumps(snapshot(),ensure_ascii=False,default=str))
        else:
            from django.core.management import execute_from_command_line
            execute_from_command_line(['manage.py','runserver','127.0.0.1:'+os.environ['AUDIT03_PORT'],'--noreload','--insecure'])
        return
    if action not in ['tests','browser','physical','keyboard','sqlite-race','capture','phone','frontier','frontier-product','reclassify','barcode-check','phone-check']:raise SystemExit('Unknown audit action')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+secrets.token_hex(4)
    run=RESULTS/'datos'/('etapa03k-'+stamp);out=RESULTS/'evidencias'/('03-R-altered-'+action+'-'+stamp)
    protected=[*APP.glob('*.sqlite3'),*(RESULTS/'datos').rglob('*.sqlite3'),ROOT/'PLANIFICACION_SCRUM_R1PMV.xlsx']
    # A protected file that is already absent is reported, never recreated or restored.
    def state(p):return digest(p) if p.exists() else None
    hashes={str(p.relative_to(ROOT)):state(p) for p in protected}
    run.mkdir();out.mkdir();write(run/'marker.json',{'run':run.name,'created_utc':stamp})
    (run/'.django-key').write_text(secrets.token_urlsafe(48),encoding='utf-8')
    os.environ.update(AUDIT03_RUN_DIR=str(run),AUDIT03_OUT=str(out),AUDIT03_PYTHON=sys.executable)
    setup();result={'action':action,'run':run.name,'evidence':str(out.relative_to(ROOT)),'started_utc':stamp}
    if action=='tests':
        logging.disable(logging.CRITICAL)
        from django.core.management import call_command
        from django.test.runner import DiscoverRunner
        labels=sys.argv[2:] or ['catalog']
        log=io.StringIO()
        with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
            call_command('check');call_command('makemigrations',check=True,dry_run=True,verbosity=1)
            runner=DiscoverRunner(verbosity=2,interactive=False);result['labels']=labels;result['methods']=runner.build_suite(labels).countTestCases();result['failures']=runner.run_tests(labels)
        safe=re.sub(r'(name="csrfmiddlewaretoken" value=")[^"]+',r'\1[REDACTED]',log.getvalue())
        (out/'tests.txt').write_text(safe,encoding='utf-8')
    elif action=='sqlite-race':
        common.prepare(run)
        from audit03k7_races import product_races
        result['cases']=product_races()
        result['failures']=sum(not case['ok'] for case in result['cases'])
    else:
        common.prepare(run)
        if action == 'physical':
            fixtures()
        elif action in ('keyboard', 'capture', 'phone', 'frontier', 'frontier-product', 'reclassify', 'barcode-check', 'phone-check'):
            keyboard_fixture()
            if action == 'phone-check':
                from catalog.models import Product
                fx = json.loads((out/'fixture.json').read_text(encoding='utf-8'))
                p = Product.objects.get(pk=fx['product_id'])
                p.barcode = '00CAT03K-A'
                p.is_active = False
                p.save()
            if action == 'reclassify':
                from catalog.models import Category, Product
                from identity.models import Account
                from inventory.services import register_stock_entry, LotInput
                from django.utils import timezone as local_time
                fx = json.loads((out/'fixture.json').read_text(encoding='utf-8'))
                fx['category_b_id'] = str(Category.objects.create(name='Alimentos').pk)
                register_stock_entry(actor=Account.objects.get(email='warehouse@audit03.invalid'),
                    product=Product.objects.get(pk=fx['product_id']),
                    lots=[LotInput('N-COMPLEMENTO',1,Decimal('5.00'),local_time.localdate()+timedelta(days=60))])
                q = Product.objects.get(pk=fx['empty_product_id'])
                q.category_id = fx['category_b_id']
                q.save()
                from inventory.services import confirm_initial_load
                confirm_initial_load(actor=Account.objects.get(email='warehouse@audit03.invalid'), product=q,
                    lots=[LotInput('Q-LOTE', 6, Decimal('2.00'), local_time.localdate()+timedelta(days=60))])
                from sales.services import add_product_to_draft
                add_product_to_draft(actor=Account.objects.get(email='seller@audit03.invalid'), product_id=q.pk, quantity=1)
                write(out/'fixture.json',fx)
            if action == 'frontier-product':
                from catalog.models import Product
                from identity.models import Account
                from inventory.services import confirm_initial_load, LotInput
                from django.utils import timezone as local_time
                fx = json.loads((out/'fixture.json').read_text(encoding='utf-8'))
                confirm_initial_load(actor=Account.objects.get(email='warehouse@audit03.invalid'),
                    product=Product.objects.get(pk=fx['empty_product_id']),
                    lots=[LotInput('M-CONTROL',5,Decimal('1.00'),local_time.localdate()+timedelta(days=90))])
                from sales.services import discard_active_draft, add_product_to_draft, checkout_sale
                import uuid
                seller = Account.objects.get(email='seller@audit03.invalid')
                discard_active_draft(actor=seller)
                control_draft = add_product_to_draft(actor=seller,product_id=fx['empty_product_id'],quantity=1)
                control_sale = checkout_sale(actor=seller,draft_id=control_draft.pk,
                    cash_received=Decimal('4.00'),idempotency_key=uuid.uuid4())
                add_product_to_draft(actor=seller,product_id=fx['product_id'],quantity=2)
                fx['neighbor_sale_id'] = str(control_sale.pk)
                write(out/'fixture.json',fx)
        else:
            availability_fixture()
        write(out/'orm-initial.json', snapshot())
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        os.environ['AUDIT03_PORT']=str(port)
        server=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'serve'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            for _ in range(100):
                with socket.socket() as sock:
                    if sock.connect_ex(('127.0.0.1',port))==0:break
                if server.poll() is not None:raise RuntimeError('Isolated server failed to start')
                time.sleep(.1)
            scripts = {'physical':'audit03k_physical.cjs', 'keyboard':'audit03k7_keyboard.cjs', 'browser':'audit03k_browser.cjs', 'capture':'audit03k8_capture.cjs', 'phone':'audit03k9_phone.cjs'}
            scripts['frontier'] = 'audit03l_browser.cjs'
            scripts['frontier-product'] = 'audit03m_browser.cjs'
            scripts['reclassify'] = 'audit03r_altered.cjs'
            scripts['barcode-check'] = 'audit03o_barcode.cjs'
            scripts['phone-check'] = 'audit03p_phone.cjs'
            browser=subprocess.run(['node',str(SUPPORT/scripts[action])],capture_output=True,text=True,encoding='utf-8')
            result.update(browser_exit=browser.returncode,browser_output=browser.stdout,browser_error=browser.stderr)
            write(out/'orm-final.json',snapshot())
        finally:
            server.terminate()
            try:server.wait(timeout=5)
            except subprocess.TimeoutExpired:server.kill();server.wait(timeout=5)
            result['port_closed']=False
            for _ in range(50):
                with socket.socket() as sock:
                    if sock.connect_ex(('127.0.0.1',port))!=0:result['port_closed']=True;break
                time.sleep(.1)
    result['protected_unchanged']={str(p.relative_to(ROOT)):state(p)==hashes[str(p.relative_to(ROOT))] for p in protected}
    result['protected_absent_at_start']=[k for k,v in hashes.items() if v is None]
    result['finished_utc']=datetime.now(timezone.utc).isoformat();write(out/'result.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
    if result.get('failures',0) or result.get('browser_exit',0) or result.get('port_closed',True) is not True or not all(result['protected_unchanged'].values()):raise SystemExit(1)
if __name__=='__main__':main()
