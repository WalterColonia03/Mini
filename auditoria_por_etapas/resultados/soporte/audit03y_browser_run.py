"""03-Y explicit identity browser audit, NEW marked SQLite, no operator .env.
Usage: browser. Internal modes require inherited owned marker through audit03k_settings.
"""
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4

SUPPORT = Path(__file__).resolve().parent
sys.path.insert(0, str(SUPPORT))
import audit03k_run as base
ROOT, APP, RESULTS = base.ROOT, base.APP, base.RESULTS
write = base.write
EAN, UPC, PADDED = '0012345678905', '012345678905', '00012345678905'


def snapshot():
    from catalog.models import Product, ProductBarcodeKey
    result = base.snapshot()
    if any(stage in os.environ.get('AUDIT03_RUN_DIR', '') for stage in ['-AH-', '-AG-', '-AI-', '-AJ-']):
        from inventory.models import StockWriteOff, PhysicalAdjustment
        result['writeoffs'] = list(StockWriteOff.objects.order_by('pk').values())
        result['adjustments'] = list(PhysicalAdjustment.objects.order_by('pk').values())
    if any(stage in os.environ.get('AUDIT03_RUN_DIR', '') for stage in ['-AH-', '-AG-', '-AI-', '-AJ-']):
        from sales.models import SaleLine
        result['sales.SaleLine'] = list(SaleLine.objects.order_by('pk').values())
    result['identity'] = list(Product.objects.order_by('pk').values('id','barcode_type'))
    result['catalog.ProductBarcodeKey'] = list(ProductBarcodeKey.objects.order_by('reading_key').values('product_id','reading_key'))
    if any(stage in os.environ.get('AUDIT03_RUN_DIR', '') for stage in ['-AB-', '-AC-', '-AD-', '-AE-', '-AF-', '-AG-', '-AH-', '-AI-', '-AJ-']):
        from inventory.models import Lot, InitialInventoryLoad
        result['receipt_lots'] = list(Lot.objects.order_by('pk').values())
        result['receipt_loads'] = list(InitialInventoryLoad.objects.order_by('pk').values())
    return result


def stock_and_history():
    from catalog.models import Product
    from identity.models import Account
    from inventory.services import confirm_initial_load, LotInput
    from sales.services import add_product_to_draft, checkout_sale
    from django.utils import timezone as tz
    product = Product.objects.get(barcode=EAN)
    assert product.barcode_type == 'GTIN' and not product.lots.exists()
    confirm_initial_load(actor=Account.objects.get(email='warehouse@audit03.invalid'), product=product,
        lots=[LotInput('Y-GTIN',7,Decimal('1.00'),tz.localdate()+timedelta(days=60))])
    seller = Account.objects.get(email='seller@audit03.invalid')
    draft = add_product_to_draft(actor=seller,product_id=product.pk,quantity=1)
    sale = checkout_sale(actor=seller,draft_id=draft.pk,cash_received=Decimal('5.00'),idempotency_key=uuid4())
    print(json.dumps({'product_id':str(product.pk),'sale_id':str(sale.pk)}))


def inventory():
    return {'scope':'03-Y explicit GTIN/internal identity selected by user',
        'requirements':['PROD01/CA02','PROD02/CA03','PROD03/CA01-02','PROD04/CA03','RN29','DEC-03X-IDENTIDAD'],
        'routes':['/productos/','/productos/nuevo/','/productos/codigos/comprobar/','/productos/<uuid>/editar/','/ventas/'],
        'fields':['barcode','barcode_type','edit_snapshot','query','q'],
        'outputs':['duplicate warning','explicit type','invalid GTIN warning','same product in searches','unchanged historic barcode'],
        'planned':['GTIN creation with leading zeros','UPC/EAN/padded equivalence','cross-type collision rejection',
                   'invalid GTIN checksum','numeric internal creation','own GTIN edit and history','role denials'],
        'not_executed':['phone','original database migration','inventory reception audit','PostgreSQL concurrency']}


def main():
    action = sys.argv[1]
    if action in ['serve','snapshot','stock-history','ah-advance','aj-expire','aj-actor']:
        base.setup()
        if '-AH-' in os.environ.get('AUDIT03_RUN_DIR', ''):
            from audit03ah_clock import install
            install()
        if action in ['aj-expire','aj-actor']:
            from audit03aj_session import inspect_or_expire
            print(json.dumps(inspect_or_expire(action=='aj-expire')))
            return
        if action == 'ah-advance':
            from audit03ah_clock import advance
            advance()
            return
        if action=='snapshot': print(json.dumps(snapshot(),ensure_ascii=False,default=str))
        elif action=='stock-history': stock_and_history()
        else:
            from django.core.management import execute_from_command_line
            execute_from_command_line(['manage.py','runserver','127.0.0.1:'+os.environ['AUDIT03_PORT'],'--noreload','--insecure'])
        return
    assert action in ('browser','phone','z-before','z-after','z-phone','aa-box','ab-receipt','ac-supplier','ad-fefo','ae-initial','af-recovery','ag-before','ag-after','ah-cost','ai-recovery','aj-session')
    stage = {'aj-session':'AJ','ai-recovery':'AI','ah-cost':'AH','ag-before':'AG','ag-after':'AG','aa-box':'AA', 'ab-receipt':'AB', 'ac-supplier':'AC', 'ad-fefo':'AD', 'ae-initial':'AE', 'af-recovery':'AF'}.get(action, 'Z' if action.startswith('z-') else 'Y')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+secrets.token_hex(4)
    run = RESULTS/'datos'/('etapa03k-'+stage+'-'+stamp)
    out = RESULTS/'evidencias'/('03-'+stage+'-'+action+'-'+stamp)
    protected = [*APP.glob('*.sqlite3'),*(RESULTS/'datos').rglob('*.sqlite3'),ROOT/'PLANIFICACION_SCRUM_R1PMV.xlsx']
    state=lambda p:base.digest(p) if p.exists() else None
    hashes={str(p.relative_to(ROOT)):state(p) for p in protected}
    run.mkdir();out.mkdir()
    write(run/'marker.json',{'run':run.name,'created_utc':stamp})
    (run/'.django-key').write_text(secrets.token_urlsafe(48),encoding='utf-8')
    os.environ.update(AUDIT03_RUN_DIR=str(run),AUDIT03_OUT=str(out),AUDIT03_PYTHON=sys.executable)
    result={'action':action,'run':run.name,'started_utc':stamp,'evidence':str(out.relative_to(ROOT))}
    server=None
    try:
        base.setup();base.common.prepare(run);base.fixtures()
        if stage == 'AJ':
            from audit03ab_receipt import prepare, inventory as receipt_inventory
            prepare()
            spec=receipt_inventory()
            spec.update(scope='03-AJ expired session and account revocation', cases=['expire stored session', 'old form redirects without writes', 'login does not replay POST', 'role revoked', 'account deactivated and reactivated'])
            write(out/'inventory-before.json',spec)
        elif stage == 'AI':
            from audit03ab_receipt import prepare, inventory as receipt_inventory
            prepare()
            spec = receipt_inventory()
            spec.update(scope='03-AI response loss in subsequent receipt', cases=['abort before POST delivery', 'replay uncommitted POST', 'commit then abort response', 'exact and modified duplicate replay', 'recover via menus across roles'], not_executed=['server or motor crash', 'concurrency', 'valuation policy'])
            write(out/'inventory-before.json',spec)
        elif stage == 'AH':
            from audit03ab_receipt import prepare
            from audit03ah_clock import inventory
            prepare()
            write(out/'inventory-before.json',inventory())
        elif stage == 'AG':
            from audit03ab_receipt import prepare, inventory as receipt_inventory
            write(out/'inventory-before.json', receipt_inventory())
            prepare()
        elif stage == 'AF':
            from audit03ab_receipt import prepare
            write(out/'inventory-before.json', {
                'criteria':['INV01a/CA01-04','08:873 receipt access','PROP-03-RET-T05'],
                'routes':['/inventario/carga-inicial/','/inventario/stock/',
                          '/inventario/cargas/<uuid>/','/inventario/carga-inicial/<uuid>/creada/'],
                'fields':['product','supplier','lot number/quantity/cost/expiration'],
                'roles':['warehouse submits and recovers','admin reads receipt','seller denied receipt'],
                'cases':['abort POST before delivery','commit POST then abort browser response',
                         'replay exact payload after response loss','recover through stock menu',
                         'HALF_UP four-decimal tie','two-decimal display tie','receipt alias permissions']})
            prepare()
        elif stage == 'AE':
            from audit03ab_receipt import prepare
            write(out/'inventory-before.json', {
                'criteria':['INV01a/CA01-03','PROD05 boundary','CAT01 boundary','PROP-03-RET-T06'],
                'routes':['/inventario/carga-inicial/','/productos/','/productos/categorias/','/ventas/'],
                'fields':['product','supplier','lot number/quantity/cost/expiration','is_active','category state version'],
                'roles':['warehouse fills old receipt','admin deactivates and reactivates','seller queries stock'],
                'cases':['initial receipt rejected after product deactivation','initial receipt rejected after category deactivation',
                         'old POST rejected without inventory changes','reactivation permits receipt','neighbour preserved']})
            prepare()
        elif stage == 'AD':
            from audit03ad_fefo import prepare
            write(out/'inventory-before.json', {
                'criteria':['INV-01a/CA05','RN-19','VEN01c FEFO boundary'],
                'routes':['/ventas/','/ventas/cobrar/','/inventario/stock/'],
                'roles':['seller: prepare and confirm sales','warehouse: observe stock'],
                'cases':['expiration priority','receipt timestamp tiebreak','UUID tiebreak',
                         'expired excluded','repeat checkout preserves lots','historical receipt times preserved']})
            write(out/'fixture.json', prepare())
        elif stage == 'AC':
            from audit03ab_receipt import prepare
            write(out/'inventory-before.json', {
                'criteria':['INV-01a/CA02-03','INV-01b/CA01','PROV04 boundary','PROP-03-RET-T04/T06'],
                'routes':['/inventario/carga-inicial/','/inventario/entrada/','/inventario/proveedores/'],
                'fields':['supplier: optional active selection','product','lots: number,quantity,unit_cost,expiration_date'],
                'roles':['warehouse fills and submits','admin deactivates/reactivates supplier','seller cannot toggle supplier'],
                'cases':['old form after deactivation','rejection without commerce writes','reactivate and resubmit','optional supplier']
            })
            prepare()
            from inventory.models import Lot
            from django.utils import timezone as django_time
            fixture = json.loads((out/'fixture.json').read_text(encoding='utf-8'))
            ceiling = Lot.latest_expiration_date(django_time.localdate())
            fixture.update(ceiling=ceiling.isoformat(), over_ceiling=(ceiling+timedelta(days=1)).isoformat())
            write(out/'fixture.json', fixture)
        elif stage == 'AB':
            from audit03ab_receipt import prepare, inventory as receipt_inventory
            write(out/'inventory-before.json', receipt_inventory())
            prepare()
        elif stage == 'AA':
            from audit03z_fixtures import prepare_package_sample
            write(out/'inventory-before.json',{'criteria':['PROP-03-RET-T01 (identity only)','PROD01/CA02'],
                'roles':['ADMIN: validate code','ALMACENERO: catalogue','VENDEDOR: sale lookup'],
                'specimen':{'unit':'4006381333931','outer':'14006381333938','units_per_carton_in_fixture':12},
                'checks':['three unit records','alternating searches','unknown outer code','stock and transaction snapshots']})
            prepare_package_sample()
        elif stage == 'Z':
            from audit03z_fixtures import inventory as inventory_z, prepare_legacy
            write(out/'inventory-before.json',inventory_z())
            prepare_legacy()
        elif action == 'phone':
            from catalog.models import Product, Category
            Product.objects.create(name='GTIN físico Y',category=Category.objects.get(name='Higiene'),barcode=EAN,barcode_type='GTIN',sale_price=Decimal('3.00'))
        if stage == 'Y':
            write(out/'inventory-before.json',dict(inventory(),mode=action))
        write(out/'orm-initial.json',snapshot())
        with socket.socket() as sock:
            sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        os.environ['AUDIT03_PORT']=str(port)
        server=subprocess.Popen([sys.executable,__file__,'serve'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        for _ in range(100):
            with socket.socket() as sock:
                if sock.connect_ex(('127.0.0.1',port))==0:break
            if server.poll() is not None:raise RuntimeError('Server failed')
            time.sleep(.1)
        script = {'phone':'audit03y_phone.cjs', 'browser':'audit03y_browser.cjs', 'z-phone':'audit03z_phone.cjs',
                  'ab-receipt':'audit03ab_browser.cjs', 'ac-supplier':'audit03ac_browser.cjs',
                  'ad-fefo':'audit03ad_browser.cjs', 'ae-initial':'audit03ae_browser.cjs',
                  'aj-session':'audit03aj_browser.cjs','ai-recovery':'audit03ai_browser.cjs','ah-cost':'audit03ah_browser.cjs','ag-before':'audit03ag_browser.cjs','ag-after':'audit03ag_browser.cjs',
                  'af-recovery':'audit03af_browser.cjs'}.get(action, 'audit03z_browser.cjs')
        child=subprocess.run(['node',str(SUPPORT/script),action],capture_output=True,text=True,encoding='utf-8')
        result.update(browser_exit=child.returncode,browser_output=child.stdout,browser_error=child.stderr)
        write(out/'orm-final.json',snapshot())
    except Exception as error:
        result['error_type']=type(error).__name__
        raise
    finally:
        if server:
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
        result['original_sha256']=state(APP/'r1_pmv.sqlite3')
        result['finished_utc']=datetime.now(timezone.utc).isoformat();write(out/'result.json',result)
        print(json.dumps({k:v for k,v in result.items() if k!='protected_unchanged'},ensure_ascii=False))
    if result.get('browser_exit',1) or not result.get('port_closed') or not all(result['protected_unchanged'].values()):raise SystemExit(1)

if __name__=='__main__':main()
