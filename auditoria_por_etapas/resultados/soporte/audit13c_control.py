"""Explicit, reversible controls for marked isolated browser fixtures only."""
import json, os, sys
from datetime import datetime, timezone
from pathlib import Path
from audit13_run import setup, RESULTS

setup()  # validates parent/marker and ignores the operator .env
from django.conf import settings
from identity.models import Account, Role

run = settings.RUN_DIR
fixture = json.loads((run/'fixture.json').read_text(encoding='utf-8'))
action, value = sys.argv[1:3]
if action == 'fault':
    assert value in ['off','/inicio/','/inventario/stock/','/productos/vencimientos/','/ventas/historial/']
    (run/'browser-failure.json').write_text(json.dumps({'path':None if value=='off' else value}),encoding='utf-8')
elif action == 'account':
    assert fixture.get('empty'), 'Account variants are restricted to the empty fixture'
    account = Account.objects.get(pk=fixture['accounts']['admin'])
    if value == 'inactive': Account.objects.filter(pk=account.pk).update(is_active=False)
    elif value == 'invalid-role':
        role,_=Role.objects.get_or_create(code='AUDIT13_INVALID',defaults={'name':'Rol ficticio inválido'})
        Account.objects.filter(pk=account.pk).update(role=role)
    elif value == 'restore':
        Account.objects.filter(pk=account.pk).update(is_active=True,role=Role.objects.get(code='ADMIN'))
    else: raise ValueError('Unknown account variant')
else: raise ValueError('Unknown control')
event=dict(at_utc=datetime.now(timezone.utc).isoformat(),fixture=run.name,action=action,value=value)
with (RESULTS/'evidencias/13-B-final-20261113/controls.jsonl').open('a',encoding='utf-8') as f:
    f.write(json.dumps(event)+'\n')
print(json.dumps(event))
