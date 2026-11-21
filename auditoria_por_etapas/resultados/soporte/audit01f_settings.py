"""Stage 01-F: isolated SQLite database, no operator .env or production database access."""
from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "auditoria_por_etapas/resultados/datos/01-F-20261114"
DATA.mkdir(parents=True, exist_ok=True)
KEY_PATH = DATA / ".django-key"
if not KEY_PATH.exists():
    KEY_PATH.write_text(secrets.token_urlsafe(48), encoding="utf-8")

os.environ.update(
    APP_ENV="test",
    DATABASE_URL="sqlite",
    DJANGO_DEBUG="false",
    DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost,testserver",
    DJANGO_SECRET_KEY=KEY_PATH.read_text(encoding="utf-8").strip(),
)

from config import env  # noqa: E402

_original_loader = env.load_dotenv
env.load_dotenv = lambda *args, **kwargs: None
try:
    from config.settings import *  # noqa: E402, F403
finally:
    env.load_dotenv = _original_loader

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(DATA / "audit.sqlite3"),
        "TEST": {"NAME": ":memory:"},
    }
}
if "test" not in sys.argv:
    SESSION_COOKIE_NAME = "audit01f_sessionid"
    CSRF_COOKIE_NAME = "audit01f_csrftoken"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
