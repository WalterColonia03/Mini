"""02-B: new marked SQLite DB, isolated settings, Chrome and ORM snapshots; never reset."""
import hashlib, json, os, secrets, socket, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
SUPPORT=Path(__file__).resolve().parent
RESULTS=SUPPORT.parent
ROOT=RESULTS.parent.parent
APP=ROOT/'r1-pmv'
sys.path[:0]=[str(APP),str(SUPPORT)]
import audit02a_run as helper

def state():
    from identity.models import Account
    from django.contrib.sessions.models import Session
    from cash.models import CashShift, CashShiftClose
    from sales.models import SaleDraft, Sale
    from inventory.models import Lot
    return {'accounts':[{'id':str(a.pk),'email':a.email,'name':a.display_name,'role':a.role.code,'active':a.is_active,
                         'sessions':sum(s.get_decoded().get('_auth_user_id')==str(a.pk) for s in Session.objects.all())}
                        for a in Account.objects.select_related('role').order_by('email')],
            'shifts':list(CashShift.objects.order_by('id').values('id','seller_id','status','opening_amount')),
            'closes':CashShiftClose.objects.count(),'drafts':list(SaleDraft.objects.order_by('id').values('id','seller_id','status')),
            'lots':list(Lot.objects.order_by('id').values('id','available_quantity')),'sales':Sale.objects.count()}

def main():
    if sys.argv[1]=='snapshot':
        helper.setup();print(json.dumps(state(),default=str,ensure_ascii=False));return
    if sys.argv[1]=='serve':
        helper.setup()
        from django.core.management import execute_from_command_line
        execute_from_command_line(['manage.py','runserver','127.0.0.1:'+os.environ['AUDIT02A_PORT'],'--noreload','--insecure']);return
    if sys.argv[1]!='run': raise SystemExit('Expected run/snapshot/serve')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run=RESULTS/'datos'/('etapa02a-b-'+stamp);evidence=RESULTS/'evidencias'/('02-B-'+stamp)
    protected=[APP/'r1_pmv.sqlite3',RESULTS/'datos/etapa00-20261105/audit.sqlite3',
               RESULTS/'datos/etapa01-20261109/audit.sqlite3',RESULTS/'datos/etapa02-20261109/audit.sqlite3',
               RESULTS/'datos/etapa02a-20261109T231223297870Z/audit.sqlite3',
               RESULTS/'datos/etapa02a-b-20261109T235102894578Z/audit.sqlite3']
    old={str(p.relative_to(ROOT)):helper.digest(p) for p in protected}
    run.mkdir(exist_ok=False);evidence.mkdir(exist_ok=False)
    helper.write(run/'marker.json',{'run':run.name,'created_utc':stamp})
    (run/'.django-key').write_text(secrets.token_urlsafe(48),encoding='utf8')
    os.environ.update(AUDIT02A_RUN_DIR=str(run),AUDIT02A_EVIDENCE=str(evidence),AUDIT02A_PYTHON=sys.executable)
    helper.setup();helper.prepare(run)
    from identity.models import Account, Role
    inactive=Account.objects.create_user('inactive@audit02a.invalid','Aa1!'+secrets.token_urlsafe(18),display_name='AUD02B Inactivo',role=Role.objects.get(code='VENDEDOR'),is_active=False)
    helper.write(evidence/'initial.json',state())
    source=[APP/'identity'/'views.py',APP/'identity'/'forms.py',APP/'identity'/'services.py',APP/'identity'/'models.py',
            APP/'identity'/'authorization.py',APP/'cash'/'services.py',APP/'sales'/'services.py',
            *(APP/'identity/templates/identity').glob('employee_*.html')]
    src={str(p.relative_to(ROOT)):helper.digest(p) for p in source}
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    os.environ['AUDIT02A_PORT']=str(port)
    server=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'serve'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    result={'run':run.name,'port':port,'evidence':str(evidence.relative_to(ROOT)),'source_sha256_before':src}
    try:
        for _ in range(100):
            with socket.socket() as s:
                if s.connect_ex(('127.0.0.1',port))==0:break
            if server.poll() is not None:raise RuntimeError('Audit server exited')
            time.sleep(.1)
        browser=subprocess.run(['node',str(SUPPORT/'audit02b_chrome.cjs')],capture_output=True,text=True,encoding='utf8')
        result.update(browser_exit=browser.returncode,browser_output=browser.stdout,browser_error=browser.stderr)
        helper.write(evidence/'orm-final.json',state())
    finally:
        server.terminate()
        try:server.wait(timeout=5)
        except subprocess.TimeoutExpired:server.kill();server.wait(timeout=5)
        result['port_closed']=False
        for _ in range(50):
            with socket.socket() as s:
                if s.connect_ex(('127.0.0.1',port))!=0:result['port_closed']=True;break
            time.sleep(.1)
        result['protected_unchanged']={str(p.relative_to(ROOT)):helper.digest(p)==old[str(p.relative_to(ROOT))] for p in protected}
        result['source_sha256_after']={str(p.relative_to(ROOT)):helper.digest(p) for p in source}
        result['database_sha256']=helper.digest(run/'audit.sqlite3')
        helper.write(evidence/'closure.json',result)
    print(json.dumps(result,indent=2,ensure_ascii=False))
    if result.get('browser_exit')!=0 or not result['port_closed'] or not all(result['protected_unchanged'].values()):raise SystemExit(1)
if __name__=='__main__':main()
