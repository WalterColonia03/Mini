"""Migrate/check/test only with in-memory database; immutable per-run evidence."""
import contextlib
import importlib.util
import json
import logging
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
OUT=Path(sys.argv[1]).resolve(); OUT.mkdir(parents=True,exist_ok=False)
labels=sys.argv[2:]
spec=importlib.util.spec_from_file_location('auditbase',HERE.parent/'14-D-20261113/navegador/recorrido.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
before=base.build();start=datetime.now(timezone.utc).isoformat()
os.environ.update(APP_ENV='test',DJANGO_SETTINGS_MODULE='config.settings',DJANGO_SECRET_KEY=secrets.token_urlsafe(48),DJANGO_DEBUG='false',DJANGO_ALLOWED_HOSTS='testserver,localhost,127.0.0.1')
sys.path.insert(0,str(ROOT/'r1-pmv'));os.chdir(ROOT/'r1-pmv')
from django.conf import settings
settings.DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':':memory:'}}
status=0
with (OUT/'resultado.txt').open('x',encoding='utf-8') as log, contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
    import django
    django.setup();logging.disable(logging.CRITICAL)
    from django.core.management import call_command
    try:
        if labels==['--migration-money']:
            call_command('makemigrations','cash','sales',name='integration_money_limits',verbosity=1)
        else:
            call_command('test',*labels,interactive=False,verbosity=1)
            call_command('makemigrations',check=True,dry_run=True,verbosity=1)
    except SystemExit as e:
        status=e.code or 0
after=base.build()
base.save(OUT/'manifiesto.json',dict(inicio_utc=start,fin_utc=datetime.now(timezone.utc).isoformat(),labels=labels,status=status,
    base='SQLite :memory:',plan08=base.sha((ROOT/'08_Historias_de_Usuario.md').read_bytes()),antes=before,despues=after,fuentes_estables=before==after))
print(json.dumps(dict(status=status,fuentes_estables=before==after,build=after['sha256'])))
sys.exit(status)
