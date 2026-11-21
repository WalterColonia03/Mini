"""Stage 01-E: isolated database, no operator .env or database access."""
import os
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'auditoria_por_etapas/resultados/datos/01-E-20261114'
DATA.mkdir(parents=True, exist_ok=True)
key = DATA / '.django-key'
if not key.exists():
    key.write_text(secrets.token_urlsafe(48), encoding='utf-8')
os.environ.update(APP_ENV='test', DATABASE_URL='sqlite', DJANGO_DEBUG='false',
                  DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost,testserver',
                  DJANGO_SECRET_KEY=key.read_text(encoding='utf-8'))
from config import env
loader = env.load_dotenv
env.load_dotenv = lambda *args, **kwargs: None
try:
    from config.settings import *
finally:
    env.load_dotenv = loader
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3',
    'NAME': str(DATA / 'audit.sqlite3'), 'TEST': {'NAME': ':memory:'}}}
SESSION_COOKIE_NAME = 'audit01e_sessionid'
CSRF_COOKIE_NAME = 'audit01e_csrftoken'
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
