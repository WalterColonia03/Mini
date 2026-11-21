"""Supplementary read-only checks on the audit13 empty fixture."""
import json
import logging
import os
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from unittest.mock import patch
from audit13_run import setup, RESULTS, write

setup()
from django.db import DatabaseError
from django.test import Client
from identity.models import Account
from inventory.models import Lot
from sales.models import Sale
from catalog.models import Product
from cash.models import CashShift

run = Path(os.environ['AUDIT13_RUN_DIR'])
fixture = json.loads((run/'fixture.json').read_text(encoding='utf-8'))
assert fixture.get('empty'), 'Use a marked EMPTY fixture only.'
logging.getLogger('django.request').disabled = True
client = Client(raise_request_exception=False)
client.force_login(Account.objects.get(pk=fixture['accounts']['admin']))
results = []
def verify(ident, expected, actual):
    results.append(dict(id=ident, expected=expected, observed=actual,
                        status='CUMPLE' if actual == expected else 'INCUMPLE'))

for route, texts in [
    ('/inventario/stock/', ['Sin alertas de stock bajo ni de vencimiento.',
                           'No hay productos registrados en el catálogo todavía.']),
    ('/productos/vencimientos/', ['No hay lotes con unidades disponibles que estén vencidos o venzan en los próximos 30 días.']),
    ('/ventas/historial/', ['No se encontraron ventas con los filtros aplicados.']),
]:
    response = client.get(route)
    verify('13-E-'+route, dict(status=200, messages=[True for _ in texts]),
           dict(status=response.status_code, messages=[t in unescape(response.content.decode()) for t in texts]))
response = client.get('/inicio/')
verify('13-E-ZERO-SUMMARY', 2, response.content.decode().count('S/ 0,00'))
verify('13-E-REFRESH-TEXT', True,
       'Actualiza la página para volver a consultar.' in response.content.decode())
verify('13-E-NO-FUTURE-REPORTS', False, 'Yape' in response.content.decode())
with patch('identity.views._dashboard_summary', side_effect=DatabaseError('audit fixture')):
    failed = client.get('/inicio/')
verify('13-E-FAILURE-NOT-ZERO', dict(status=500, has_zero=False),
       dict(status=failed.status_code, has_zero='S/ 0,00' in failed.content.decode()))
verify('13-E-BUSINESS-EMPTY', [0,0,0,0],
       [m.objects.count() for m in [Sale, Product, Lot, CashShift]])
out = RESULTS/'evidencias/13-A-20261113'/(
    'empty-messages-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json'
)
write(out, dict(run=run.name, at_utc=datetime.now(timezone.utc).isoformat(),
                layer='Django Client, not browser', results=results,
                passed=sum(x['status']=='CUMPLE' for x in results), total=len(results)))
print(json.dumps({'path':str(out), 'passed':sum(x['status']=='CUMPLE' for x in results), 'total':len(results)}))
raise SystemExit(0 if all(x['status']=='CUMPLE' for x in results) else 1)
