"""Reproducible isolated setup, baseline and existing test revalidation."""
import os
import sys
import json
import hashlib
import subprocess
import secrets
import io
import re
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'r1-pmv'
OUT = ROOT / 'auditoria_por_etapas/resultados/evidencias/01-E-20261114'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO))
os.environ['DJANGO_SETTINGS_MODULE'] = 'audit01e_settings'

def dump(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')

def baseline(name):
    files = {}
    for p in sorted(REPO.rglob('*')):
        rel = p.relative_to(REPO)
        if any(part in {'.git', '.venv', '__pycache__', 'evidencias', 'db', 'staticfiles'} for part in rel.parts):
            continue
        if p.is_file() and p.suffix in {'.py', '.html', '.css', '.js', '.txt', '.yaml'}:
            files[rel.as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    docs = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.md')}
    data = {'time_lima': datetime.now(ZoneInfo('America/Lima')).isoformat(),
        'head': subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip(),
        'dirty_status': subprocess.check_output(['git','-C',str(REPO),'status','--short'],text=True),
        'build_sha256': hashlib.sha256(json.dumps(files,sort_keys=True).encode()).hexdigest(),
        'source_files': files, 'documents': docs,
        'protected_database_sha256': {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (REPO/'r1_pmv.sqlite3',REPO/'db/db.sqlite3') if p.exists()}}
    dump(name, data)
    print(json.dumps({k:data[k] for k in ('time_lima','head','build_sha256')}))

if sys.argv[1] == 'baseline':
    baseline(sys.argv[2]); raise SystemExit

import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from identity.models import Account, Role, LoginAttempt
assert Path(settings.DATABASES['default']['NAME']).resolve() == (ROOT/'auditoria_por_etapas/resultados/datos/01-E-20261114/audit.sqlite3').resolve()

if sys.argv[1] == 'setup':
    if Account.objects.exists() if Path(settings.DATABASES['default']['NAME']).exists() else False:
        raise SystemExit('Refusing to reseed existing data')
    call_command('migrate', verbosity=0)
    credentials = {}
    for code, label in Role.Code.choices:
        role, _ = Role.objects.get_or_create(code=code, defaults={'name':label})
        password = secrets.token_urlsafe(24)
        account = Account.objects.create_user(f'{code.lower()}@audit01e.invalid',password,
            display_name=f'AUD01E {label}',role=role)
        credentials[code] = {'email':account.email,'password':password}
    inactive = Account.objects.create_user('inactiva@audit01e.invalid',secrets.token_urlsafe(24),
        display_name='AUD01E Inactiva',role=role,is_active=False)
    (settings.DATA/'.credentials.json').write_text(json.dumps(credentials),encoding='utf-8')
    dump('setup.json',{'database':str(settings.DATABASES['default']['NAME']),
        'accounts':4,'roles':list(credentials),'inactive':1,'operator_env_read':False,
        'django':django.get_version(),'python':sys.version.split()[0]})
    print('New isolated database migrated; 4 fictional accounts ready. No credentials printed.')
elif sys.argv[1] == 'tests':
    settings.SESSION_COOKIE_NAME = 'sessionid'
    settings.CSRF_COOKIE_NAME = 'csrftoken'
    labels = ['identity.test_auth_audit01','identity.tests.AuthenticationAndAuthorizationTests',
        'identity.tests.EmployeeEditDeactivateTests.test_login_lock_expires_after_fifteen_minutes',
        'identity.tests.EmployeeEditDeactivateTests.test_unknown_identifier_has_the_same_lock_response',
        'identity.tests.EmployeeEditDeactivateTests.test_success_resets_counter_without_deleting_throttle_row',
        'audit01e_probes']
    if len(sys.argv) > 2 and sys.argv[2] == 'identity':
        labels = ['identity', 'audit01e_probes']
    stream = io.StringIO()
    code = 0
    with redirect_stdout(stream), redirect_stderr(stream):
        try: call_command('test',*labels,verbosity=2,interactive=False)
        except SystemExit as exc: code = int(exc.code or 0)
    log = stream.getvalue().replace(settings.SECRET_KEY,'[REDACTED]')
    log = re.sub(r'(?i)((?:password|csrfmiddlewaretoken|sessionid|csrftoken)\s*[:=]\s*)[^\s,;}]+',r'\1[REDACTED]',log)
    stem = 'identity-regression' if len(sys.argv)>2 else 'tests'
    (OUT/(stem+'.txt')).write_text(log,encoding='utf-8')
    dump(stem+'.json',{'labels':labels,'exit_code':code,'database':'SQLite :memory:',
        'tool':'Django Client/ORM, not browser; no PostgreSQL concurrency',
        'summary':re.findall(r'Ran \d+ tests in [^\n]+',log)})
    print(json.dumps({'exit_code':code,'summary':re.findall(r'Ran \d+ tests in [^\n]+',log)}))
    raise SystemExit(code)
elif sys.argv[1] == 'extra-fixtures':
    path = settings.DATA/'.credentials.json'
    credentials = json.loads(path.read_text(encoding='utf-8'))
    if 'INACTIVA' in credentials:
        raise SystemExit('Additional fixtures already prepared')
    password = secrets.token_urlsafe(24)
    inactive = Account.objects.get(email='inactiva@audit01e.invalid')
    inactive.set_password(password)
    inactive.save(update_fields=['password'])
    credentials['INACTIVA'] = {'email':inactive.email,'password':password}
    password = secrets.token_urlsafe(24)
    email = 'a'*(254-len('@example.invalid'))+'@example.invalid'
    account = Account.objects.create_user(email,password,display_name='AUD01E Correo254',role=Role.objects.get(code='VENDEDOR'))
    credentials['LIMITE'] = {'email':email,'password':password}
    path.write_text(json.dumps(credentials),encoding='utf-8')
    dump('extra-fixtures.json',{'inactive_password_prepared':True,'additional_account':'Correo254',
        'purpose':'correct inactive password and real254 account in browser','operational_accounts_changed':False})
    print('Isolated additional fixtures ready; no credentials printed')
elif sys.argv[1] == 'state':
    from django.apps import apps
    from django.contrib.sessions.models import Session
    from django.utils.crypto import salted_hmac
    business = {}
    for model in apps.get_models():
        if model._meta.app_label in {'catalog','inventory','cash','sales'}:
            rows = list(model.objects.order_by('pk').values())
            business[model._meta.label] = {'count':len(rows),
                'sha256':hashlib.sha256(json.dumps(rows,default=str,sort_keys=True).encode()).hexdigest()}
    accounts = []
    for a in Account.objects.order_by('email'):
        attempt = LoginAttempt.objects.filter(identifier=salted_hmac('identity.login.throttle',a.email_normalized,algorithm='sha256').hexdigest()).first()
        accounts.append({'role':a.role.code,'active':a.is_active,'last_login':str(a.last_login),
            'attempt': None if not attempt else {'failures':attempt.failures,'locked_until':str(attempt.locked_until)}})
    dump(sys.argv[2],{'accounts':accounts,'sessions':Session.objects.count(),
        'attempt_rows':LoginAttempt.objects.count(),'business':business})
    print('Sanitized ORM state recorded')
elif sys.argv[1] == 'clock':
    from datetime import timedelta
    from django.utils import timezone
    from django.utils.crypto import salted_hmac
    identifier = salted_hmac('identity.login.throttle','almacenero@audit01e.invalid',algorithm='sha256').hexdigest()
    attempt = LoginAttempt.objects.get(identifier=identifier)
    old = str(attempt.locked_until)
    attempt.locked_until = timezone.now()+timedelta(seconds=int(sys.argv[2]))
    attempt.save(update_fields=['locked_until'])
    dump('clock-'+sys.argv[2]+'.json',{'fixture':'ALMACENERO isolated01E','old':old,
        'new':str(attempt.locked_until),'purpose':'controlled UI remaining time/expiration, not 15min real wait'})
    print('Only isolated fixture deadline adjusted; count unchanged')
