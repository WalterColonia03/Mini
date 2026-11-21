"""Exclusive isolated PostgreSQL 18.4 settings for Stage 10-B audit; never touches .env."""
import os

os.environ.update(
    APP_ENV="test",
    DATABASE_URL="sqlite",
    DJANGO_DEBUG="false",
    DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost,testserver",
    DJANGO_SECRET_KEY=os.environ["AUDIT10B_PG_SECRET"],
)

from config import env as config_env  # noqa: E402

_orig_loader = config_env.load_dotenv
config_env.load_dotenv = lambda path=None: None
try:
    from config.settings import *  # noqa: F403, E402
finally:
    config_env.load_dotenv = _orig_loader

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["AUDIT10B_PG_DB"],
        "USER": "postgres",
        "PASSWORD": "",
        "HOST": "127.0.0.1",
        "PORT": os.environ["AUDIT10B_PG_PORT"],
        "CONN_MAX_AGE": 0,
    }
}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
SESSION_COOKIE_NAME = "audit10b_pg_sessionid"
CSRF_COOKIE_NAME = "audit10b_pg_csrftoken"
