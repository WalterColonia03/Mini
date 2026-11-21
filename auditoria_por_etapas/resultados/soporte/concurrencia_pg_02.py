"""Stage 02 races on an exclusively created PostgreSQL cluster; no app .env.

The owned cluster is stopped and retained, not reset, flushed, or deleted.
By default runs post-fix verification. --reproduce requires pre-fix sources.
Run from project root with r1-pmv/.venv/Scripts/python.exe -B <this file>.
"""
from __future__ import annotations
import contextlib
import io
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from decimal import Decimal
VERIFY = '--reproduce' not in sys.argv

ROOT=Path(__file__).resolve().parents[3]
BIN=Path('C:/Program Files/PostgreSQL/18/bin')
STAMP=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
CLUSTER=(Path(tempfile.gettempdir())/('audit02c-pg-'+secrets.token_hex(12))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK=CLUSTER/'AUDIT02C_OWNED'
MARK.write_text(STAMP,encoding='utf-8')
DBDIR=CLUSTER/'data'
PW=secrets.token_urlsafe(40)
PWFILE=CLUSTER/'password'
PWFILE.write_text(PW,encoding='utf-8')
DBNAME='audit02c_'+secrets.token_hex(5)
with socket.socket() as s:
    s.bind(('127.0.0.1',0)); PORT=s.getsockname()[1]
evidence={'started_utc':datetime.now(timezone.utc).isoformat(),'cluster':str(CLUSTER),'port':PORT,'mode':'verify' if VERIFY else 'reproduce-before-fix','cases':[]}

def own():
    assert CLUSTER.parent==Path(tempfile.gettempdir()).resolve()
    assert CLUSTER.name.startswith('audit02c-pg-') and MARK.read_text(encoding='utf-8')==STAMP

def pg(name,*args):
    with tempfile.TemporaryFile(mode='w+',encoding='utf-8',errors='replace') as capture:
        result=subprocess.run([str(BIN/(name+'.exe')),*map(str,args)],stdout=capture,stderr=capture,
                              timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
        capture.seek(0); diagnostic=capture.read().replace(PW,'[REDACTED]')
    if result.returncode:
        raise RuntimeError(name+' failed: '+diagnostic[-1000:])

started=False
configured=False
try:
    own()
    pg('initdb','-D',DBDIR,'-U','audit02c','--pwfile',PWFILE,'--auth-host=scram-sha-256',
       '--auth-local=scram-sha-256','--encoding=UTF8','--locale=C')
    PWFILE.unlink()
    pg('pg_ctl','-D',DBDIR,'-l',CLUSTER/'postgres.log','-o',
       f'-h 127.0.0.1 -p {PORT} -c log_statement=none -c log_min_error_statement=panic','-w','start')
    started=True
    import psycopg
    from psycopg import sql
    conf={'host':'127.0.0.1','port':PORT,'user':'audit02c','password':PW}
    with psycopg.connect(**conf,dbname='postgres',autocommit=True) as conn:
        assert Path(conn.execute('SHOW data_directory').fetchone()[0]).resolve()==DBDIR
        evidence['postgres_version']=conn.execute('SELECT version()').fetchone()[0]
        conn.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(DBNAME)))
    sys.path.insert(0,str(ROOT/'r1-pmv'))
    os.environ.update(APP_ENV='test',DJANGO_DEBUG='false',DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
                      DJANGO_SETTINGS_MODULE='config.settings')
    from config import env
    old_loader=env.load_dotenv; env.load_dotenv=lambda path=None: None
    from django.conf import settings
    settings.DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':DBNAME,
      'USER':'audit02c','PASSWORD':PW,'HOST':'127.0.0.1','PORT':PORT,'CONN_MAX_AGE':60,
      'OPTIONS':{'options':'-c statement_timeout=20000 -c lock_timeout=12000'}}}
    env.load_dotenv=old_loader
    import django
    django.setup(); configured=True
    from django.db import connection,connections,close_old_connections
    from django.core.management import call_command
    from identity.models import Account,Role
    from identity.services import create_employee,deactivate_employee,update_employee
    from cash.models import CashRegister,CashShift
    from cash.services import open_cash_shift,close_cash_shift
    with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
        call_command('migrate',interactive=False,verbosity=0)
    with connection.cursor() as cur:
        cur.execute("SELECT current_database(),current_setting('data_directory'),current_setting('transaction_isolation')")
        db,folder,iso=cur.fetchone();assert db==DBNAME and Path(folder).resolve()==DBDIR
    evidence.update(db=DBNAME,isolation=iso,migrations='PASS')
    roles={code:Role.objects.create(code=code,name=code) for code in ['ADMIN','VENDEDOR','ALMACENERO']}
    admin1=Account.objects.create_user('admin1@audit02c.invalid','SafeAudit2!x',display_name='Admin1',role=roles['ADMIN'])
    admin2=Account.objects.create_user('admin2@audit02c.invalid','SafeAudit2!x',display_name='Admin2',role=roles['ADMIN'])
    seller=Account.objects.create_user('seller@audit02c.invalid','SafeAudit2!x',display_name='Seller',role=roles['VENDEDOR'])
    CashRegister.objects.create(code='CAJA-01')
    def race(name,operations,markers):
        barrier=threading.Barrier(2,timeout=10)
        seen=[];pids={}; first_locked=threading.Event(); second_entered=threading.Event(); observed_blockers=[]
        lock_table='identity_account' if name in ('open_vs_deactivate','deactivate_vs_open','role_vs_open','open_vs_role') else 'identity_role'
        def work(index):
            close_old_connections()
            with connection.cursor() as cur:
                cur.execute('SELECT pg_backend_pid()');pids[index]=cur.fetchone()[0]
            hit=False
            def coordinate(execute,query,params,many,context):
                nonlocal hit
                if not VERIFY and not hit and markers[index] in query:
                    hit=True;seen.append(index);barrier.wait()
                is_lock=VERIFY and 'FOR UPDATE' in query and f'FROM "{lock_table}"' in query
                if is_lock and index==1:
                    second_entered.set()
                value=execute(query,params,many,context)
                if is_lock and index==0 and not first_locked.is_set():
                    first_locked.set()
                    if not second_entered.wait(10):
                        raise RuntimeError('second worker did not attempt row lock')
                    deadline=time.monotonic()+10
                    while time.monotonic()<deadline:
                        with connection.cursor() as cur:
                            cur.execute('SELECT pg_blocking_pids(%s)',[pids[1]])
                            if pids[0] in cur.fetchone()[0]:
                                observed_blockers.append(True); break
                        time.sleep(.02)
                    if not observed_blockers:
                        raise RuntimeError('PostgreSQL lock wait was not observed')
                return value
            try:
                if VERIFY:
                    barrier.wait()
                    if index==1 and not first_locked.wait(10):
                        raise RuntimeError('first worker did not acquire row lock')
                with connection.execute_wrapper(coordinate):
                    operations[index]()
                return {'operation':index,'result':'success'}
            except Exception as exc:
                return {'operation':index,'result':type(exc).__name__}
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            f=[pool.submit(work,i) for i in range(2)]
            results=[x.result(timeout=30) for x in f]
        case={'name':name,'connections':len(set(pids.values())),'synchronized_before_write':sorted(seen),
              'postgres_blocking_observed':bool(observed_blockers),'results':results}
        evidence['cases'].append(case)
        return case
    # Two checks see the other ADMIN before either account is deactivated.
    case=race('last_admin',[
        lambda:deactivate_employee(actor=Account.objects.get(pk=admin1.pk),account=Account.objects.get(pk=admin2.pk)),
        lambda:deactivate_employee(actor=Account.objects.get(pk=admin2.pk),account=Account.objects.get(pk=admin1.pk))],
        ['UPDATE "identity_account"','UPDATE "identity_account"'])
    case['active_admins']=Account.objects.filter(role=roles['ADMIN'],is_active=True).count()
    # Restore test fixtures by explicit reactivation rather than reset/database cleanup.
    Account.objects.filter(pk__in=[admin1.pk,admin2.pk]).update(is_active=True)
    case=race('duplicate_email',[
        lambda:create_employee(actor=Account.objects.get(pk=admin1.pk),display_name='Duplicate1',email='same@audit02c.invalid',password='Valid2!x',role=roles['VENDEDOR']),
        lambda:create_employee(actor=Account.objects.get(pk=admin2.pk),display_name='Duplicate2',email='same@audit02c.invalid',password='Valid2!x',role=roles['VENDEDOR'])],
        ['INSERT INTO "identity_account"','INSERT INTO "identity_account"'])
    case['normalized_count']=Account.objects.filter(email_normalized='same@audit02c.invalid').count()
    case=race('open_vs_deactivate',[
        lambda:open_cash_shift(actor=Account.objects.get(pk=seller.pk),opening_amount=Decimal('5.00')),
        lambda:deactivate_employee(actor=Account.objects.get(pk=admin1.pk),account=Account.objects.get(pk=seller.pk))],
        ['INSERT INTO "cash_cashshift"','UPDATE "identity_account"'])
    seller.refresh_from_db()
    case['seller_active']=seller.is_active
    case['open_shifts']=CashShift.objects.filter(seller=seller,status='OPEN').count()
    if not VERIFY:
        a,b,c=evidence['cases']
        assert all(x['synchronized_before_write']==[0,1] for x in (a,b,c)), 'Pre-fix write barriers were not reached'
        assert a['active_admins']==0 and b['normalized_count']==1
        assert any(r['result']=='IntegrityError' for r in b['results'])
        assert c['seller_active'] is False and c['open_shifts']==1
    if VERIFY:
        a,b,c=evidence['cases'][:3]
        assert all(x['postgres_blocking_observed'] for x in (a,b,c))
        assert a['connections']==2 and a['active_admins']>=1 and sum(r['result']=='success' for r in a['results'])==1
        assert b['connections']==2 and b['normalized_count']==1 and sorted(r['result'] for r in b['results'])==['ValidationError','success']
        assert c['connections']==2 and not (c['seller_active'] is False and c['open_shifts']>0)
        assert sum(r['result']=='success' for r in c['results'])==1
        close_cash_shift(actor=Account.objects.get(pk=seller.pk),counted_amount=Decimal('5.00'))
        seller2=Account.objects.create_user('seller2@audit02c.invalid','SafeAudit2!x',display_name='Seller2',role=roles['VENDEDOR'])
        case=race('deactivate_vs_open',[
            lambda:deactivate_employee(actor=Account.objects.get(pk=admin1.pk),account=Account.objects.get(pk=seller2.pk)),
            lambda:open_cash_shift(actor=Account.objects.get(pk=seller2.pk),opening_amount=Decimal('5.00'))],
            ['UPDATE "identity_account"','INSERT INTO "cash_cashshift"'])
        seller2.refresh_from_db();case.update(seller_active=seller2.is_active,open_shifts=CashShift.objects.filter(seller=seller2,status='OPEN').count())
        assert case['postgres_blocking_observed'] and case['seller_active'] is False and case['open_shifts']==0
        assert [r['result'] for r in case['results']]==['success','PermissionDenied']
        seller3=Account.objects.create_user('seller3@audit02c.invalid','SafeAudit2!x',display_name='Seller3',role=roles['VENDEDOR'])
        case=race('role_vs_open',[
            lambda:update_employee(actor=Account.objects.get(pk=admin1.pk),account=Account.objects.get(pk=seller3.pk),display_name='Seller3',email='seller3@audit02c.invalid',role=roles['ALMACENERO']),
            lambda:open_cash_shift(actor=Account.objects.get(pk=seller3.pk),opening_amount=Decimal('5.00'))],
            ['UPDATE "identity_account"','INSERT INTO "cash_cashshift"'])
        seller3.refresh_from_db();case.update(role=seller3.role.code,open_shifts=CashShift.objects.filter(seller=seller3,status='OPEN').count())
        assert case['postgres_blocking_observed'] and case['role']=='ALMACENERO' and case['open_shifts']==0
        assert [r['result'] for r in case['results']]==['success','PermissionDenied']
        seller4=Account.objects.create_user('seller4@audit02c.invalid','SafeAudit2!x',display_name='Seller4',role=roles['VENDEDOR'])
        case=race('open_vs_role',[
            lambda:open_cash_shift(actor=Account.objects.get(pk=seller4.pk),opening_amount=Decimal('5.00')),
            lambda:update_employee(actor=Account.objects.get(pk=admin1.pk),account=Account.objects.get(pk=seller4.pk),display_name='Seller4',email='seller4@audit02c.invalid',role=roles['ALMACENERO'])],
            ['INSERT INTO "cash_cashshift"','UPDATE "identity_account"'])
        seller4.refresh_from_db();case.update(role=seller4.role.code,open_shifts=CashShift.objects.filter(seller=seller4,status='OPEN').count())
        assert case['postgres_blocking_observed'] and case['role']=='VENDEDOR' and case['open_shifts']==1
        assert [r['result'] for r in case['results']]==['success','ValidationError']
    evidence['status']='COMPLETE'
except Exception as exc:
    evidence.update(status='INCOMPLETE',error_type=type(exc).__name__,error=str(exc).replace(PW,'[REDACTED]')[-1200:])
finally:
    if configured: connections.close_all()
    try:
        own()
        if started:
            assert Path((DBDIR/'postmaster.pid').read_text(encoding='utf-8').splitlines()[1]).resolve()==DBDIR
            pg('pg_ctl','-D',DBDIR,'-m','fast','-w','stop')
        with socket.socket() as s:
            evidence['port_closed']=s.connect_ex(('127.0.0.1',PORT))!=0
        evidence['cluster_retained']=CLUSTER.exists()
    except Exception as exc:
        evidence['stop_error']=type(exc).__name__
    evidence['finished_utc']=datetime.now(timezone.utc).isoformat()
    out=ROOT/'auditoria_por_etapas/resultados/evidencias'/('02-C-pg-'+STAMP+'.json')
    out.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'evidence':str(out.relative_to(ROOT)),'status':evidence['status'],
                      'cases':evidence['cases'],'port_closed':evidence.get('port_closed')},ensure_ascii=False))
sys.exit(0 if evidence['status']=='COMPLETE' and evidence.get('port_closed') else 1)
