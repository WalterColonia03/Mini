"""Stage03-B runner: fresh marked databases, read-only catalogue observations.
Usage: baseline | tests [labels] | browser. Internal modes require marked run.
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
    os.environ['DJANGO_SETTINGS_MODULE']='audit03b_settings'
    import django;django.setup()
def snapshot():
    from catalog.models import Product
    from inventory.models import Lot
    result=common.snapshot()
    result['stock']=[{'id':str(p.pk),'barcode':p.barcode,'physical':p.physical_stock,'current':p.sellable_stock,'minimum':p.minimum_stock,'sellable':p.is_sellable} for p in Product.objects.order_by('pk')]
    result['lots_dates']=list(Lot.objects.order_by('pk').values('id','expiration_date'))
    return result
def fixtures():
    from django.utils import timezone as dtz
    from catalog.models import Category,Product
    from identity.models import Account
    from inventory.models import InitialInventoryLoad,Lot
    from cash.models import CashRegister
    from cash.services import open_cash_shift
    if Product.objects.exists():raise RuntimeError('Fixture must start with an empty product catalogue')
    today=dtz.localdate()
    category=Category.objects.create(name='AUD03B Conservas')
    inactive=Category.objects.create(name='AUD03B Categoría inactiva',is_active=False)
    warehouse=Account.objects.get(email='warehouse@audit03.invalid')
    rows=[]
    specs=[('ZERO','AUD03B Cero',[],10,True,category),('LOW','AUD03B Bajo',[(9,1)],10,True,category),
           ('EQUAL','AUD03B Igual',[(5,1),(5,2)],10,True,category),('HIGH','AUD03B Alto',[(11,1)],10,True,category),
           ('MIX','AUD03B Mezcla',[(4,1),(5,2),(50,-1),(3,0),(0,3)],10,True,category),
           ('MINZERO','AUD03B Mínimo cero',[],0,True,category),('MINTHREE','AUD03B Mínimo tres',[(4,1)],3,True,category),
           ('OFF','AUD03B Producto inactivo',[(9,1)],10,False,category),('CATOFF','AUD03B Categoría suspendida',[(11,1)],10,True,inactive),
           ('ACCENT','AUD03B Atún clásico',[(2,1)],1,True,category),('XSS','AUD03B <script>texto</script>',[],10,True,category)]
    for code,name,lots,minimum,active,cat in specs:
        p=Product.objects.create(category=cat,name=name,barcode='AUD03B-'+code,sale_price=Decimal('8.50'),minimum_stock=minimum,is_active=active)
        if lots:
            load=InitialInventoryLoad.objects.create(product=p,responsible=warehouse)
            for i,(qty,offset) in enumerate(lots):
                Lot.objects.create(product=p,initial_load=load,number=f'{code}-{i}',initial_quantity=max(qty,1),available_quantity=qty,unit_cost=Decimal('5.00'),expiration_date=today+timedelta(days=offset))
        rows.append({'id':str(p.pk),'name':name,'code':p.barcode,'price':'8,50','current':sum(q for q,o in lots if o>0),'physical':sum(q for q,o in lots),'minimum':minimum,'active':active,'category':cat.name,'category_active':cat.is_active})
    CashRegister.objects.create(code='CAJA-01')
    open_cash_shift(actor=Account.objects.get(email='seller@audit03.invalid'),opening_amount=Decimal('50.00'))
    return {'business_date':str(today),'products':rows,'snapshot':snapshot()}
def baseline():
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=RESULTS/'evidencias'/('03-B-inventario-'+stamp);out.mkdir()
    old=json.loads((RESULTS/'evidencias/03-inventario-20261110T000729019055Z/inventory.json').read_text(encoding='utf-8'))
    files=[ROOT/p for p in old['source_hashes']]
    files.extend([APP/'catalog/migrations/0003_normalize_category_spaces.py',APP/'catalog/test_audit03_categories.py'])
    protected=[*APP.glob('*.sqlite3'),*(RESULTS/'datos').rglob('*.sqlite3'),ROOT/'PLANIFICACION_SCRUM_R1PMV.xlsx']
    for rel in ['catalog/views.py','catalog/forms.py','catalog/templates/catalog/product_list.html']:
        dest=out/'before'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((APP/rel).read_bytes())
    report={'started_utc':stamp,'scope':'HU-PROD-01/CA01..03; catalogue read/search and role boundaries',
      'criteria':[c for c in old['criteria'] if c['id'].startswith('HU-PROD-01/')],
      'initial_status':'NO EJECUTADO in depth; E03-OBS-01 static candidate',
      'source_hashes':{str(p.relative_to(ROOT).as_posix()):digest(p) for p in files},
      'protected_hashes':{str(p.relative_to(ROOT).as_posix()):digest(p) for p in protected},
      'git_status':subprocess.check_output(['git','-C',str(APP),'status','--short'],text=True)}
    write(out/'baseline.json',report);print(str(out.relative_to(ROOT)));return
def main():
    action=sys.argv[1]
    if action=='baseline':return baseline()
    if action in ['serve','snapshot','fixtures']:
        setup()
        if action=='snapshot':print(json.dumps(snapshot(),ensure_ascii=False,default=str))
        elif action=='fixtures':print(json.dumps(fixtures(),ensure_ascii=False,default=str))
        else:
            from django.core.management import execute_from_command_line
            execute_from_command_line(['manage.py','runserver','127.0.0.1:'+os.environ['AUDIT03_PORT'],'--noreload','--insecure'])
        return
    if action not in ['tests','browser']:raise SystemExit('Expected baseline/tests/browser')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run=RESULTS/'datos'/('etapa03b-'+stamp);out=RESULTS/'evidencias'/('03-B-'+action+'-'+stamp)
    protected=[*APP.glob('*.sqlite3'),*(RESULTS/'datos').rglob('*.sqlite3'),ROOT/'PLANIFICACION_SCRUM_R1PMV.xlsx']
    hashes={str(p.relative_to(ROOT)):digest(p) for p in protected}
    run.mkdir();out.mkdir();write(run/'marker.json',{'run':run.name,'created_utc':stamp})
    (run/'.django-key').write_text(secrets.token_urlsafe(48),encoding='utf-8')
    os.environ.update(AUDIT03_RUN_DIR=str(run),AUDIT03_OUT=str(out),AUDIT03_PYTHON=sys.executable)
    setup();result={'action':action,'run':run.name,'evidence':str(out.relative_to(ROOT)),'started_utc':stamp}
    if action=='tests':
        logging.disable(logging.CRITICAL)
        from django.core.management import call_command
        from django.test.runner import DiscoverRunner
        labels=sys.argv[2:] or ['catalog.test_audit03_catalogue']
        log=io.StringIO()
        with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
            call_command('check');call_command('makemigrations',check=True,dry_run=True,verbosity=1)
            runner=DiscoverRunner(verbosity=2,interactive=False);result['labels']=labels;result['methods']=runner.build_suite(labels).countTestCases();result['failures']=runner.run_tests(labels)
        safe=re.sub(r'(name="csrfmiddlewaretoken" value=")[^"]+',r'\1[REDACTED]',log.getvalue())
        (out/'tests.txt').write_text(safe,encoding='utf-8')
    else:
        common.prepare(run)
        with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
        os.environ['AUDIT03_PORT']=str(port)
        server=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'serve'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            for _ in range(100):
                with socket.socket() as sock:
                    if sock.connect_ex(('127.0.0.1',port))==0:break
                if server.poll() is not None:raise RuntimeError('Isolated server failed to start')
                time.sleep(.1)
            browser=subprocess.run(['node',str(SUPPORT/'audit03b_browser.cjs')],capture_output=True,text=True,encoding='utf-8')
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
    result['protected_unchanged']={str(p.relative_to(ROOT)):digest(p)==hashes[str(p.relative_to(ROOT))] for p in protected}
    result['finished_utc']=datetime.now(timezone.utc).isoformat();write(out/'result.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
    if result.get('failures',0) or result.get('browser_exit',0) or result.get('port_closed',True) is not True or not all(result['protected_unchanged'].values()):raise SystemExit(1)
if __name__=='__main__':main()
