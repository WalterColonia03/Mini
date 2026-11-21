"""Read only: record the isolated account's real lock deadline, without secrets."""
import argparse
import json
from datetime import timedelta
from audit01k import setup_django, CRED_FILE, OUT

setup_django()
from django.utils import timezone
from django.utils.crypto import salted_hmac
from identity.models import Account, LoginAttempt

p = argparse.ArgumentParser()
p.add_argument('--label', choices=['antes', 'despues'], required=True)
args = p.parse_args()
creds = json.loads(CRED_FILE.read_text(encoding='utf-8'))
identifier = salted_hmac('identity.login.throttle', Account.normalize_email(creds['admin']['email']), algorithm='sha256').hexdigest()
a = LoginAttempt.objects.get(pk=identifier)
now = timezone.now()
result = dict(observado_utc=now.isoformat(), failures=a.failures, locked_until=a.locked_until.isoformat() if a.locked_until else None)
if a.locked_until:
    result['quinto_fallo_inferido_de_plazo_15_min'] = (a.locked_until-timedelta(minutes=15)).isoformat()
    result['segundos_restantes'] = (a.locked_until-now).total_seconds()
destination = OUT / f'expiracion-real-{args.label}.json'
assert not destination.exists()
destination.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result))
