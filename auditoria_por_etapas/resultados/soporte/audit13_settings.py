"""Audit13 isolated settings; operator .env is never loaded."""
import json
import os
from tempfile import gettempdir
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[1]
RUN_DIR = Path(os.environ['AUDIT13_RUN_DIR']).resolve()
if RUN_DIR.parent != (RESULTS / 'datos').resolve() or not RUN_DIR.name.startswith('etapa13-'):
    raise RuntimeError('Invalid audit13 directory')
if json.loads((RUN_DIR / 'marker.json').read_text(encoding='utf-8'))['run'] != RUN_DIR.name:
    raise RuntimeError('Audit13 marker mismatch')
PRIVATE_DIR = Path(gettempdir()) / 'minimarket-audit13' / RUN_DIR.name
os.environ.update(APP_ENV='test', DATABASE_URL='sqlite', DJANGO_DEBUG='false',
                  DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost,testserver',
                  DJANGO_SECRET_KEY=(PRIVATE_DIR / '.django-key').read_text(encoding='utf-8'))
from config import env as config_env
_loader = config_env.load_dotenv
config_env.load_dotenv = lambda path=None: None
try:
    from config.settings import *
finally:
    config_env.load_dotenv = _loader
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': RUN_DIR / 'audit.sqlite3'}}
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
SESSION_COOKIE_NAME = 'audit13_sessionid'
CSRF_COOKIE_NAME = 'audit13_csrftoken'
if os.environ.get('AUDIT13_DEFAULT_COOKIES') == '1':
    SESSION_COOKIE_NAME = 'sessionid'
    CSRF_COOKIE_NAME = 'csrftoken'
