"""Stage03-D runner: fresh marked databases, product editing and cross-role observations.
Usage: tests [labels] | browser. Internal modes require marked run.
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
    os.environ['DJANGO_SETTINGS_MODULE']='audit03d_settings'
    import django;django.setup()
def snapshot():
    from catalog.models import Product
    data = common.snapshot()
    data['commerce'] = list(Product.objects.order_by('pk').values('id', 'barcode_normalized', 'search_name', 'average_cost'))
    return data


def fixtures():
    from catalog.models import Category, Product
    from cash.models import CashShift
    from sales.models import Sale, SaleLine
    canned = Category.objects.create(name='Productos enlatados')
    Category.objects.create(name='Alternativa activa')
    Category.objects.create(name='Suspendida', is_active=False)
    result = common.effects_fixture(canned.pk)
    Product.objects.create(category=canned, name='Atún ocupado', barcode='DUPLICADO', sale_price=Decimal('2.50'))
    write(Path(os.environ['AUDIT03_OUT'])/'fixture.json', result)


def main():
    action=sys.argv[1]
    if action in ['serve','snapshot']:
        setup()
        if action=='snapshot':print(json.dumps(snapshot(),ensure_ascii=False,default=str))
        else:
            from django.core.management import execute_from_command_line
            execute_from_command_line(['manage.py','runserver','127.0.0.1:'+os.environ['AUDIT03_PORT'],'--noreload','--insecure'])
        return
    if action not in ['tests','browser']:raise SystemExit('Expected tests/browser')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run=RESULTS/'datos'/('etapa03d-'+stamp);out=RESULTS/'evidencias'/('03-D-'+action+'-'+stamp)
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
        labels=sys.argv[2:] or ['catalog']
        log=io.StringIO()
        with contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
            call_command('check');call_command('makemigrations',check=True,dry_run=True,verbosity=1)
            runner=DiscoverRunner(verbosity=2,interactive=False);result['labels']=labels;result['methods']=runner.build_suite(labels).countTestCases();result['failures']=runner.run_tests(labels)
        safe=re.sub(r'(name="csrfmiddlewaretoken" value=")[^"]+',r'\1[REDACTED]',log.getvalue())
        (out/'tests.txt').write_text(safe,encoding='utf-8')
    else:
        common.prepare(run)
        fixtures()
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
            browser=subprocess.run(['node',str(SUPPORT/'audit03d_browser.cjs')],capture_output=True,text=True,encoding='utf-8')
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
