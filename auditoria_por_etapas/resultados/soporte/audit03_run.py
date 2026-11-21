"""Fresh Stage03-A run. No reset/flush, no business .env, no production writes.
Commands: tests (memory), browser (exclusive SQLite), snapshot/serve (marked run).
"""
import contextlib
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import secrets
import re
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal

SUPPORT=Path(__file__).resolve().parent
RESULTS=SUPPORT.parent
ROOT=RESULTS.parent.parent
APP=ROOT/'r1-pmv'
sys.path[:0]=[str(APP),str(SUPPORT)]
def write(p,x): p.write_text(json.dumps(x,indent=2,ensure_ascii=False,default=str),encoding='utf-8')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def setup():
    os.environ['DJANGO_SETTINGS_MODULE']='audit03_settings'
    import django
    django.setup()
def snapshot():
    from catalog.models import Category,Product
    from inventory.models import Lot,InitialInventoryLoad
    from cash.models import CashShift
    from sales.models import Sale,SaleLine,SaleDraft,SaleDraftLine
    return {model._meta.label:list(model.objects.order_by('pk').values(*fields)) for model,fields in [
        (Category,['id','name','name_normalized','is_active']),
        (Product,['id','name','barcode','category_id','sale_price','minimum_stock','unit','controls_expiration','is_active']),
        (Lot,['id','product_id','available_quantity','initial_quantity']),
        (InitialInventoryLoad,['id','product_id']),
        (CashShift,['id','status','opening_amount']),
        (Sale,['id','total_amount','cash_received','change_given']),
        (SaleLine,['id','product_id','product_snapshot_name','product_snapshot_barcode','unit_price','quantity']),
        (SaleDraft,['id','status']), (SaleDraftLine,['id','draft_id','product_id','quantity','unit_price'])]}
def prepare(run):
    from django.core.management import call_command
    from identity.models import Role,Account
    call_command('migrate',verbosity=0,interactive=False)
    creds={}
    for alias,code in [('admin','ADMIN'),('warehouse','ALMACENERO'),('seller','VENDEDOR')]:
        role,_=Role.objects.get_or_create(code=code,defaults={'name':code})
        pwd='Aa1!'+secrets.token_urlsafe(18)
        a=Account.objects.create_user(alias+'@audit03.invalid',pwd,display_name='AUD03 '+code,role=role)
        creds[alias]={'email':a.email,'password':pwd}
    write(run/'.credentials.json',creds)
def effects_fixture(category_id):
    from catalog.models import Category,Product
    from identity.models import Account
    from inventory.services import confirm_initial_load,LotInput
    from cash.models import CashRegister
    from cash.services import open_cash_shift
    from sales.services import add_product_to_draft,checkout_sale
    import uuid
    c=Category.objects.get(pk=category_id)
    warehouse=Account.objects.get(email='warehouse@audit03.invalid')
    seller=Account.objects.get(email='seller@audit03.invalid')
    p=Product.objects.create(category=c,name='AUD03 Bebida de prueba',barcode='AUD03-BEBIDA',sale_price=Decimal('8.50'))
    empty=Product.objects.create(category=c,name='AUD03 Sin carga',barcode='AUD03-EMPTY',sale_price=Decimal('4.00'))
    confirm_initial_load(actor=warehouse,product=p,lots=[LotInput(number='AUD03-LOTE',quantity=20,unit_cost=Decimal('5.00'),expiration_date=datetime.now(timezone.utc).date()+timedelta(days=30))])
    CashRegister.objects.create(code='CAJA-01')
    open_cash_shift(actor=seller,opening_amount=Decimal('50.00'))
    draft=add_product_to_draft(actor=seller,product_id=p.pk,quantity=1)
    sale=checkout_sale(actor=seller,draft_id=draft.pk,cash_received=Decimal('10.00'),idempotency_key=uuid.uuid4())
    add_product_to_draft(actor=seller,product_id=p.pk,quantity=2)
    return {'product_id':str(p.pk),'empty_product_id':str(empty.pk),'sale_id':str(sale.pk),'category_id':str(c.pk),'snapshot':snapshot()}
def main():
    action=sys.argv[1]
    if action in ['snapshot','serve','effects']:
        setup()
        if action=='snapshot': print(json.dumps(snapshot(),default=str,ensure_ascii=False))
        elif action=='effects': print(json.dumps(effects_fixture(sys.argv[2]),default=str,ensure_ascii=False))
        else:
            from django.core.management import execute_from_command_line
            execute_from_command_line(['manage.py','runserver','127.0.0.1:'+os.environ['AUDIT03_PORT'],'--noreload','--insecure'])
        return
    if action not in ['tests','browser']: raise SystemExit('Expected tests/browser')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run=RESULTS/'datos'/('etapa03a-'+stamp)
    out=RESULTS/'evidencias'/('03-A-'+action+'-'+stamp)
    protected=[*APP.glob('*.sqlite3'),*(RESULTS/'datos').rglob('*.sqlite3'),ROOT/'PLANIFICACION_SCRUM_R1PMV.xlsx']
    before={str(p.relative_to(ROOT)):digest(p) for p in protected}
    run.mkdir();out.mkdir()
    write(run/'marker.json',{'run':run.name,'created_utc':stamp})
    (run/'.django-key').write_text(secrets.token_urlsafe(48),encoding='utf-8')
    os.environ.update(AUDIT03_RUN_DIR=str(run),AUDIT03_OUT=str(out),AUDIT03_PYTHON=sys.executable)
    setup()
    result={'action':action,'run':run.name,'evidence':str(out.relative_to(ROOT)),'started_utc':stamp}
    if action=='tests':
        logging.disable(logging.CRITICAL)
        from django.core.management import call_command
        from django.test.runner import DiscoverRunner
        labels=sys.argv[2:] or ['catalog.test_audit03_categories','catalog.tests.CategoryTests','catalog.tests.CategoryListTests','catalog.tests.CategoryCreateTests']
        log=io.StringIO()
        with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
            call_command('check');call_command('makemigrations',check=True,dry_run=True,verbosity=1)
            runner=DiscoverRunner(verbosity=2,interactive=False)
            suite=runner.build_suite(labels);result['methods']=suite.countTestCases();result['labels']=labels
            result['failures']=runner.run_tests(labels)
        safe_log=re.sub(r'(name="csrfmiddlewaretoken" value=")[^"]+',r'\1[REDACTED]',log.getvalue())
        (out/'tests.txt').write_text(safe_log,encoding='utf-8')
    else:
        prepare(run)
        with socket.socket() as s:
            s.bind(('127.0.0.1',0));port=s.getsockname()[1]
        os.environ['AUDIT03_PORT']=str(port)
        server=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'serve'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            for _ in range(100):
                with socket.socket() as s:
                    if s.connect_ex(('127.0.0.1',port))==0: break
                if server.poll() is not None: raise RuntimeError('Isolated server failed to start')
                time.sleep(.1)
            p=subprocess.run(['node',str(SUPPORT/'audit03_browser.cjs')],capture_output=True,text=True,encoding='utf-8')
            result.update(browser_exit=p.returncode,browser_output=p.stdout,browser_error=p.stderr)
            write(out/'orm-final.json',snapshot())
        finally:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired: server.kill();server.wait(timeout=5)
            result['port_closed']=False
            for _ in range(50):
                with socket.socket() as s:
                    if s.connect_ex(('127.0.0.1',port))!=0: result['port_closed']=True;break
                time.sleep(.1)
    result['protected_unchanged']={str(p.relative_to(ROOT)):digest(p)==before[str(p.relative_to(ROOT))] for p in protected}
    result['finished_utc']=datetime.now(timezone.utc).isoformat()
    write(out/'result.json',result)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result.get('failures',0) or result.get('browser_exit',0) or not all(result['protected_unchanged'].values()) or result.get('port_closed',True) is not True: raise SystemExit(1)
if __name__=='__main__':main()
