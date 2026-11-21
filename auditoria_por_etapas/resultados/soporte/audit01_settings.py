"""Exclusive local audit configuration; never opens the operator database."""
import os
from pathlib import Path

AUDIT_ROOT = Path(__file__).resolve().parents[1]
AUDIT_DATA = (AUDIT_ROOT / "datos" / "etapa01-20261109").resolve()
AUDIT_DATA.mkdir(parents=True, exist_ok=True)
os.environ["APP_ENV"] = "test"
os.environ["DATABASE_URL"] = "sqlite"
os.environ["DJANGO_DEBUG"] = "false"
os.environ["DJANGO_ALLOWED_HOSTS"] = "127.0.0.1,localhost,testserver"
key_file = AUDIT_DATA / ".django-key"
if not key_file.exists():
    import secrets
    key_file.write_text(secrets.token_urlsafe(48), encoding="utf-8")
os.environ["DJANGO_SECRET_KEY"] = key_file.read_text(encoding="utf-8")

# Do not consume the operator's .env, even for unrelated configuration.
from config import env as config_env
previous_loader = config_env.load_dotenv
config_env.load_dotenv = lambda path=None: None
try:
    from config.settings import *  # noqa: F403
finally:
    config_env.load_dotenv = previous_loader

DATABASES = {"default": {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": str(AUDIT_DATA / "audit.sqlite3"),
    "TEST": {"NAME": str(AUDIT_DATA / "test-audit.sqlite3")},
}}
SESSION_COOKIE_NAME = "audit01_sessionid"
CSRF_COOKIE_NAME = "audit01_csrftoken"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

class AuditIdentityMiddleware:
    """Prove the responding server has the isolated audit key; disclose no key."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import hashlib
        import hmac
        response = self.get_response(request)
        challenge = request.headers.get("X-Audit01-Challenge", "")
        if len(challenge) == 64 and all(c in "0123456789abcdef" for c in challenge):
            response["X-Audit01-Proof"] = hmac.new(
                SECRET_KEY.encode("utf-8"), challenge.encode("ascii"), hashlib.sha256
            ).hexdigest()
        return response

MIDDLEWARE = ["audit01_settings.AuditIdentityMiddleware", *MIDDLEWARE]
