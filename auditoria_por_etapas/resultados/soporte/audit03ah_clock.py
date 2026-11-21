"""Business-date simulation for AH's marked disposable database only.
No production setting, OS clock, stored expiration, or timestamp is changed.
"""
import json
import os
from datetime import date
from pathlib import Path


def install():
    from django.utils import timezone
    from django.conf import settings
    run = Path(os.environ['AUDIT03_RUN_DIR']).resolve()
    assert '-AH-' in run.name and json.loads((run/'marker.json').read_text())['run'] == run.name
    assert Path(settings.DATABASES['default']['NAME']).resolve() == run/'audit.sqlite3'
    original = timezone.localdate
    def business_date(value=None, timezone=None):
        clock = run/'business-date.txt'
        if value is None and clock.exists():
            return date.fromisoformat(clock.read_text().strip())
        return original(value, timezone)
    timezone.localdate = business_date


def advance():
    run = Path(os.environ['AUDIT03_RUN_DIR'])
    fixture = json.loads((Path(os.environ['AUDIT03_OUT'])/'fixture.json').read_text(encoding='utf-8'))
    (run/'business-date.txt').write_text(fixture['future'],encoding='utf-8')
    print(json.dumps({'business_date':fixture['future'],'scope':'isolated timezone.localdate only'}))


def inventory():
    from inventory.forms import StockWriteOffForm, PhysicalAdjustmentForm
    return {
        'criteria':['INV01b/CA01-02','RN14','RN28','INV02/CA01-03 boundary','INV03/CA02-03 boundary'],
        'routes':['/inventario/carga-inicial/','/inventario/entrada/','/inventario/stock/',
                  '/inventario/bajas/nueva/','/inventario/ajustes/nuevo/','/ventas/','/ventas/cobrar/'],
        'roles':['warehouse receives and writes off','admin adjusts','seller sells and is denied inventory writes'],
        'forms':{cls.__name__:{name:{'label':str(f.label),'required':f.required,
                      'type':type(f).__name__,'initial':str(f.initial),'minimum':str(getattr(f,'min_value',None)),
                      'maximum':str(getattr(f,'max_value',None)),'max_length':getattr(f,'max_length',None)}
                      for name,f in cls.base_fields.items()} for cls in [StockWriteOffForm,PhysicalAdjustmentForm]},
        'cases':['two costs and FEFO sale','advance business date to first expiration',
                 'receipt excludes expired quantity but uses old average','partial expired writeoff reprices live stock',
                 'positive and negative physical adjustment','historical sale unchanged','role denials and rejected reason'],
        'not_approved':['valuation policy','full writeoff/adjustment HUs','sanitary recall','concurrency','deployment']}
