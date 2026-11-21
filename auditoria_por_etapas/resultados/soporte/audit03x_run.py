"""03-X characterization, fresh marked SQLite only. Never loads operator .env.
Usage: browser | phone. Internal modes validate the inherited isolated marker.
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

SUPPORT = Path(__file__).resolve().parent
sys.path.insert(0, str(SUPPORT))
import audit03k_run as base
ROOT, APP, RESULTS = base.ROOT, base.APP, base.RESULTS
write = base.write
EAN, UPC = '0012345678905', '012345678905'

def inventory():
    return {'scope':'03-X / AUD03X-CODIGO-EAN-UPC01', 'physical':'NO EJECUTADO en browser',
        'requirements':['PROD01/CA02 búsqueda', 'PROD02/CA03 unicidad', 'PROD03/CA01 captura',
                        'PROD03/CA02 aviso', 'PROD04/CA03 edición', 'RN29 permisos'],
        'routes':['/productos/', '/productos/nuevo/', '/productos/codigos/comprobar/',
                  '/productos/<uuid>/editar/', '/ventas/'],
        'field':{'barcode':'obligatorio, texto hasta64, ASCII letras/dígitos/espacios/guiones; NFKC/sin espacios/casefold; ceros preservados',
                 'capture':'campo temporal y Usar código expreso', 'q/query':'búsqueda parcial'},
        'outputs':['Sin duplicados en esta consulta.', 'El código de barras ya está registrado',
                   'Ya existe un producto con este código de barras.', '403', 'lista coincidente'],
        'classification':'caracterización del alcance vigente; equivalencia EAN/UPC PROPUESTA/PENDIENTE',
        'planned':['alta de ambas cadenas', 'duplicados literales y con espacios', 'edición colisionante',
                   'búsqueda ADMIN/ALMACENERO/VENDEDOR', 'peticiones denegadas y ausencia de cambios',
                   'consulta vendedor antes/después de lotes ficticios', 'servicio y DB']}

def stock():
    from catalog.models import Product
    from identity.models import Account
    from inventory.services import confirm_initial_load, LotInput
    from django.utils import timezone as tz
    products = list(Product.objects.order_by('barcode'))
    assert {p.barcode for p in products} == {EAN, UPC}
    assert all(not p.lots.exists() for p in products)
    for p in products:
        confirm_initial_load(actor=Account.objects.get(email='warehouse@audit03.invalid'), product=p,
            lots=[LotInput('X-' + p.barcode, 7 if p.barcode == EAN else 11,
                           Decimal('1.00'), tz.localdate()+timedelta(days=60))])

def service_checks():
    from catalog.models import Product, Category
    from catalog.services import register_canned_product
    from identity.models import Account
    from django.core.exceptions import ValidationError, PermissionDenied
    from django.db import transaction, IntegrityError
    before = json.dumps(base.snapshot(), default=str, sort_keys=True)
    cases=[]
    def check(id, ok):
        cases.append({'id':id,'ok':ok})
        assert ok, id
    check('normalized-distinct', Product.normalize_barcode(EAN)!=Product.normalize_barcode(UPC))
    check('leading-zeros', Product.normalize_barcode(EAN)==EAN and Product.normalize_barcode(UPC)==UPC)
    for role in ['admin','warehouse','seller']:
        for code in [EAN, UPC, '00 12345678905', ' 012345678905 ']:
            try:
                register_canned_product(actor=Account.objects.get(email=role+'@audit03.invalid'),
                    name='AUD03 X rechazo servicio', barcode=code, category=Category.objects.get(name='Higiene'),
                    unit='UND', sale_price=Decimal('3.00'), minimum_stock=10)
            except (ValidationError, PermissionDenied) as error:
                check(role+'-reject-'+code, isinstance(error, ValidationError if role=='admin' else PermissionDenied))
            else:
                check(role+'-reject-'+code,False)
    # Verify the actual unique constraint independently of model validation.
    try:
        with transaction.atomic():
            Product.objects.create(name='AUD03 X constraint', barcode=EAN, category=Category.objects.get(name='Higiene'),sale_price=Decimal('3.00'))
    except IntegrityError:
        check('database-unique',True)
    else:
        check('database-unique',False)
    check('service-rejections-unchanged',json.dumps(base.snapshot(),default=str,sort_keys=True)==before)
    return cases

def main():
    action=sys.argv[1]
    if action in ['serve','snapshot','stock','service-checks']:
        base.setup()
        if action=='snapshot': print(json.dumps(base.snapshot(),ensure_ascii=False,default=str))
        elif action=='stock': stock()
        elif action=='service-checks': print(json.dumps(service_checks()))
        else:
            from django.core.management import execute_from_command_line
            execute_from_command_line(['manage.py','runserver','127.0.0.1:'+os.environ['AUDIT03_PORT'],'--noreload','--insecure'])
        return
    assert action in ['browser','phone']
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+secrets.token_hex(4)
    run=RESULTS/'datos'/('etapa03k-X-'+stamp)
    out=RESULTS/'evidencias'/('03-X-'+action+'-'+stamp)
    protected=[*APP.glob('*.sqlite3'),*(RESULTS/'datos').rglob('*.sqlite3'),ROOT/'PLANIFICACION_SCRUM_R1PMV.xlsx']
    state=lambda p:base.digest(p) if p.exists() else None
    hashes={str(p.relative_to(ROOT)):state(p) for p in protected}
    run.mkdir();out.mkdir()
    write(run/'marker.json',{'run':run.name,'created_utc':stamp})
    (run/'.django-key').write_text(secrets.token_urlsafe(48),encoding='utf-8')
    os.environ.update(AUDIT03_RUN_DIR=str(run),AUDIT03_OUT=str(out),AUDIT03_PYTHON=sys.executable)
    base.setup();base.common.prepare(run);base.fixtures()
    write(out/'inventory-before.json',inventory())
    if action=='phone':
        from catalog.models import Product, Category
        Product.objects.create(name='AUD03 X EAN físico',barcode=EAN,category=Category.objects.get(name='Higiene'),sale_price=Decimal('3.00'))
    write(out/'orm-initial.json',base.snapshot())
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    os.environ['AUDIT03_PORT']=str(port)
    result={'action':action,'run':run.name,'started_utc':stamp,'evidence':str(out.relative_to(ROOT))}
    server=subprocess.Popen([sys.executable,__file__,'serve'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(100):
            with socket.socket() as sock:
                if sock.connect_ex(('127.0.0.1',port))==0:break
            if server.poll() is not None:raise RuntimeError('Server failed')
            time.sleep(.1)
        child=subprocess.run(['node',str(SUPPORT/('audit03x_'+action+'.cjs'))],capture_output=True,text=True,encoding='utf-8')
        result.update(browser_exit=child.returncode,browser_output=child.stdout,browser_error=child.stderr)
    finally:
        write(out/'orm-final.json',base.snapshot())
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
        result['finished_utc']=datetime.now(timezone.utc).isoformat()
        write(out/'result.json',result)
        print(json.dumps({k:v for k,v in result.items() if k!='protected_unchanged'},ensure_ascii=False))
    if result.get('browser_exit',1) or not result['port_closed'] or not all(result['protected_unchanged'].values()):raise SystemExit(1)

if __name__=='__main__':main()
