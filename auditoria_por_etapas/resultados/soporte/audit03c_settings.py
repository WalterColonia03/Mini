"""Exclusive, marked audit database; deliberately never loads the operator .env."""
import hashlib
import hmac
import json
import os
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[1]
RUN_DIR = Path(os.environ['AUDIT03_RUN_DIR']).resolve()
if RUN_DIR.parent != (RESULTS/'datos').resolve() or not RUN_DIR.name.startswith('etapa03c-'):
    raise RuntimeError('Invalid audit03c directory')
if json.loads((RUN_DIR/'marker.json').read_text(encoding='utf-8'))['run'] != RUN_DIR.name:
    raise RuntimeError('Audit marker mismatch')
os.environ.update(APP_ENV='test', DATABASE_URL='sqlite', DJANGO_DEBUG='false',
    DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost,testserver',
    DJANGO_SECRET_KEY=(RUN_DIR/'.django-key').read_text(encoding='utf-8'))
from config import env as config_env
loader = config_env.load_dotenv
config_env.load_dotenv = lambda path=None: None
try:
    from config.settings import *
finally:
    config_env.load_dotenv = loader
DATABASES={'default':{'ENGINE':'django.db.backends.sqlite3','NAME':RUN_DIR/'audit.sqlite3'}}
EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'
SESSION_COOKIE_NAME='audit03c_sessionid'
CSRF_COOKIE_NAME='audit03c_csrftoken'

class ProofMiddleware:
    def __init__(self,get_response): self.get_response=get_response
    def __call__(self,request):
        response=self.get_response(request)
        nonce=request.headers.get('X-Audit03-Challenge','')
        if len(nonce)==64 and all(c in '0123456789abcdef' for c in nonce):
            response['X-Audit03-Proof']=hmac.new(SECRET_KEY.encode(),nonce.encode(),hashlib.sha256).hexdigest()
            response['X-Audit03-Run']=RUN_DIR.name
        return response
MIDDLEWARE=['audit03c_settings.ProofMiddleware',*MIDDLEWARE]
