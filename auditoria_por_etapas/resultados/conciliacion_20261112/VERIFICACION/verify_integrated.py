"""Read-only product verification; all writes limited to a newly owned evidence run."""
from __future__ import annotations
import contextlib
import hashlib
import io
import json
import os
import secrets
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
APP = ROOT / 'r1-pmv'
RUN = HERE / ('integrated-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + secrets.token_hex(3))
RUN.mkdir(exist_ok=False)
(RUN / 'tmp').mkdir()
sys.dont_write_bytecode = True
os.environ.update(PYTHONDONTWRITEBYTECODE='1', TEMP=str(RUN/'tmp'), TMP=str(RUN/'tmp'))

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

protected = sorted(set(APP.glob('*.sqlite3')) | set((ROOT/'auditoria_por_etapas/resultados/datos').rglob('*.sqlite3')) | set(ROOT.glob('*.md')) | set(APP.glob('*.md')) | {p for p in APP.rglob('*') if p.is_file() and p.suffix in ('.py','.html','.css','.js','.yaml','.yml','.toml') and '.venv' not in p.parts and '__pycache__' not in p.parts})
book = ROOT/'PLANIFICACION_SCRUM_R1PMV.xlsx'
if book.exists(): protected.append(book)
before = {str(p.relative_to(ROOT)): digest(p) for p in protected}
(RUN/'protected-before.json').write_text(json.dumps(before,indent=2),encoding='utf-8')
started = time.monotonic()
report = {'started_utc':datetime.now(timezone.utc).isoformat(), 'run':str(RUN.relative_to(ROOT)), 'protected_count':len(before), 'xlsx_present':book.exists(), 'checks':[], 'guard_denials':[], 'code_changed':False}

def allowed(path):
    if isinstance(path, int): return True
    try: return Path(path).resolve().is_relative_to(RUN)
    except (TypeError,ValueError): return False

def guard(event,args):
    if event == 'open':
        path,mode,flags = args
        if not isinstance(path,int) and Path(path).resolve() == APP/'.env':
            report['guard_denials'].append('operator_env_read')
            raise PermissionError('Operator .env is outside verification boundary')
        writing = (isinstance(mode,str) and any(x in mode for x in 'wax+')) or (isinstance(flags,int) and flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        if writing and not allowed(path): raise PermissionError('Write outside owned verification run')
    elif event == 'sqlite3.connect':
        db = args[0]
        if str(db) != ':memory:' and not (str(db).startswith('file:memory') or allowed(db)):
            raise PermissionError('Database outside owned verification run')
    elif event in ('os.remove','os.rmdir','os.mkdir','os.chmod','os.utime'):
        if not allowed(args[0]): raise PermissionError('Filesystem mutation outside owned verification run')
    elif event in ('os.rename','os.replace'):
        if not all(allowed(p) for p in args[:2]): raise PermissionError('Rename outside owned verification run')

sys.addaudithook(guard)
try:
    # Negative check proves the hook rejects reading, without exposing any bytes.
    try:
        with (APP/'.env').open('rb'): pass
    except PermissionError:
        report['operator_env_guard_verified'] = True
    import sqlite3
    try:
        sqlite3.connect(str(APP/'r1_pmv.sqlite3'))
    except PermissionError:
        report['operator_db_guard_verified'] = True
    sys.path.insert(0,str(APP))
    os.environ.update(APP_ENV='test', DATABASE_URL='sqlite', DJANGO_DEBUG='false', DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost,testserver', DJANGO_SECRET_KEY=secrets.token_urlsafe(48), DJANGO_SETTINGS_MODULE='config.settings')
    from config import env
    original_loader = env.load_dotenv
    env.load_dotenv = lambda path=None: report.setdefault('suppressed_dotenv_calls',[]).append(str(path))
    try:
        from django.conf import settings
        settings.INSTALLED_APPS
    finally:
        env.load_dotenv = original_loader
    settings.DATABASES = {'default':{'ENGINE':'django.db.backends.sqlite3','NAME':str(RUN/'unused.sqlite3'),'TEST':{'NAME':str(RUN/'test.sqlite3')}}}
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    import django
    django.setup()
    report['python_version'] = sys.version
    report['django_version'] = django.get_version()
    os.chdir(APP)
    from django.core.management import call_command
    from config.test_runner import ProjectTestRunner
    from django.test.runner import RemoteTestResult
    for command,options in [('check',{}),('makemigrations',{'check':True,'dry_run':True,'interactive':False})]:
        stream=io.StringIO()
        outcome={'command':command,'options':options}
        try:
            with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
                call_command(command,verbosity=1,**options)
            outcome['status']='PASS'
        except BaseException as exc:
            outcome.update(status='FAIL',exception=type(exc).__name__)
            traceback.print_exc(file=stream)
        (RUN/(command+'.log')).write_text(stream.getvalue(),encoding='utf-8')
        report['checks'].append(outcome)
    import unittest
    class EvidenceRunner(ProjectTestRunner):
        def run_suite(self,suite,**kwargs):
            report['discovered_test_count']=suite.countTestCases()
            result=super().run_suite(suite,**kwargs)
            report['suite']={'tests_run':result.testsRun,'failures':[str(t) for t,_ in result.failures], 'errors':[str(t) for t,_ in result.errors], 'skipped':[(str(t),reason) for t,reason in result.skipped], 'successful':result.wasSuccessful()}
            return result
    stream=io.StringIO()
    runner=EvidenceRunner(verbosity=2,interactive=False,keepdb=True,parallel=1)
    with contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
        failures=runner.run_tests([])
    output=stream.getvalue()
    (RUN/'suite.log').write_text(output,encoding='utf-8')
    report['suite_exit']=failures
    report['database_engine']=settings.DATABASES['default']['ENGINE']
    report['test_database']=str(RUN/'test.sqlite3')
    report['default_cookie_names']={'session':settings.SESSION_COOKIE_NAME,'csrf':settings.CSRF_COOKIE_NAME}
except BaseException as exc:
    report['fatal']={'type':type(exc).__name__,'message':str(exc)}
    (RUN/'fatal.log').write_text(traceback.format_exc(),encoding='utf-8')
finally:
    after={str(p.relative_to(ROOT)):digest(p) if p.exists() else None for p in protected}
    (RUN/'protected-after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
    report['changed_protected']=[p for p in before if before[p]!=after[p]]
    report['operator_db_sha256']=after.get(str(Path('r1-pmv')/'r1_pmv.sqlite3'))
    report['duration_seconds']=round(time.monotonic()-started,3)
    report['finished_utc']=datetime.now(timezone.utc).isoformat()
    (RUN/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('suppressed_dotenv_calls',)},ensure_ascii=False))
