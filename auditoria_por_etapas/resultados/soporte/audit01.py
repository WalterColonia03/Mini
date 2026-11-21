"""Stage 01 isolated fixtures and evidence. Never use the operator database."""
from __future__ import annotations
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / 'r1-pmv'
sys.path.insert(0, str(APP))
os.environ['DJANGO_SETTINGS_MODULE'] = 'audit01_settings'
import django
django.setup()
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.utils import timezone
from django.utils.crypto import salted_hmac
from identity.models import Account, Role, LoginAttempt

DATA = ROOT / 'auditoria_por_etapas/resultados/datos/etapa01-20261109'
EVIDENCE = ROOT / 'auditoria_por_etapas/resultados/evidencias'
assert Path(connection.settings_dict['NAME']).resolve() == (DATA / 'audit.sqlite3').resolve()
BASE = 'http://127.0.0.1:8766'

def baseline():
    paths = [APP / 'r1_pmv.sqlite3', DATA.parent / 'etapa00-20261105/audit.sqlite3']
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def output(name, value):
    value = {'date_lima': datetime.now(ZoneInfo('America/Lima')).isoformat(), **value}
    path = EVIDENCE / name
    if path.exists():
        path = EVIDENCE / 'repeticiones' / (datetime.now().strftime('%Y%m%d-%H%M%S-%f-') + name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding='utf-8')
    print(json.dumps({'evidence': str(path.relative_to(ROOT)), **value}, ensure_ascii=False, default=str))

def identifier(email):
    return salted_hmac('identity.login.throttle', Account.normalize_email(email), algorithm='sha256').hexdigest()

def proof(base=BASE):
    import urllib.request
    challenge = secrets.token_hex(32)
    expected = hmac.new(settings.SECRET_KEY.encode(), challenge.encode(), hashlib.sha256).hexdigest()
    with urllib.request.urlopen(urllib.request.Request(base + '/', headers={'X-Audit01-Challenge': challenge}), timeout=10) as response:
        assert hmac.compare_digest(response.headers.get('X-Audit01-Proof', ''), expected), 'Wrong audit instance'

def inspect():
    from django.contrib.sessions.models import Session
    from catalog.models import Product
    from inventory.models import Lot
    from cash.models import CashShift
    from sales.models import Sale
    prepared = json.loads((DATA / 'prepared.json').read_text())
    output('01-persistencia.json', {
        'database': str(DATA / 'audit.sqlite3'), 'protected_databases_unchanged': baseline() == prepared['baseline'],
        'hashes': baseline(), 'accounts': list(Account.objects.values('email','role__code','is_active','is_staff','last_login')),
        'attempt_rows': LoginAttempt.objects.count(), 'attempt_failures': list(LoginAttempt.objects.values_list('failures', flat=True)),
        'sessions': Session.objects.count(), 'products': Product.objects.count(), 'lots': Lot.objects.count(),
        'shifts': CashShift.objects.count(), 'sales': Sale.objects.count()})

command = sys.argv[1] if len(sys.argv) > 1 else 'inspect'
if command == 'prepare':
    if (DATA / 'audit.sqlite3').exists() or (DATA / 'prepared.json').exists():
        raise SystemExit('Existing stage01 database: refusing to seed or reset.')
    before = baseline()
    call_command('migrate', interactive=False, verbosity=0)
    credentials = {}
    for key, rolecode, active, staff in [
        ('admin', Role.Code.ADMIN, True, False), ('almacen', Role.Code.WAREHOUSE, True, False),
        ('vendedor', Role.Code.SELLER, True, False), ('inactivo', Role.Code.SELLER, False, False),
        ('staff', Role.Code.ADMIN, True, True)]:
        role, _ = Role.objects.get_or_create(code=rolecode, defaults={'name': rolecode.label})
        password = secrets.token_urlsafe(24)
        email = key + '.audit01@example.invalid'
        Account.objects.create_user(email, password, display_name='AUD01 ' + key, role=role, is_active=active, is_staff=staff)
        credentials[key] = {'email': email, 'password': password}
    (DATA / '.credentials.json').write_text(json.dumps(credentials), encoding='utf-8')
    (DATA / 'prepared.json').write_text(json.dumps({'baseline': before, 'database': str(DATA / 'audit.sqlite3')}), encoding='utf-8')
    output('01-preparacion.json', {'baseline': before, 'protected_databases_unchanged': before == baseline(), 'accounts':5, 'database':str(DATA / 'audit.sqlite3'), 'secrets_logged':False})
elif command == 'serve':
    if not (DATA / 'prepared.json').exists():
        raise SystemExit('Prepare the isolated database first.')
    call_command('runserver', '127.0.0.1:8766', use_reloader=False, insecure_serving=True)
elif command == 'check':
    call_command('check')
    call_command('makemigrations', check=True, dry_run=True)
elif command == 'proof':
    proof()
    proof('http://localhost:8766')
    print('Both loopback hosts authenticated as stage01 isolated instance. No credentials transmitted.')
elif command == 'inspect':
    inspect()
elif command == 'ui-clock':
    # Controlled boundary setup only; never changes application time or real data.
    key = sys.argv[2]
    seconds = int(sys.argv[3])
    assert key in {'admin', 'almacen', 'vendedor', 'inactivo'}
    email = key + '.audit01@example.invalid'
    row = LoginAttempt.objects.get(pk=identifier(email))
    before = {'failures': row.failures, 'locked_until': row.locked_until}
    assert row.locked_until is not None, 'Only an existing UI lock may be moved'
    row.locked_until = timezone.now() + timedelta(seconds=seconds)
    row.save(update_fields=['locked_until','updated_at'])
    output('01-ui-clock-' + key + '-' + str(seconds) + '.json', {'fixture':email, 'before':before,
        'after':{'failures': row.failures, 'locked_until':row.locked_until}, 'purpose':'Controlled remaining-time/expiry fixture; not 15 minutes of wall-clock waiting'})
else:
    raise SystemExit('Unknown command')
