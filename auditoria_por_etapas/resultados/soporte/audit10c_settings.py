"""Exclusive isolated settings for Stage 10-C (SQLite scale, PG 18.4 scale, and isolated r1_pmv clone migration check).

Never loads operator .env and strictly rejects pointing at r1-pmv/r1_pmv.sqlite3.
"""
import json
import os
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[1]
ROOT = RESULTS.parents[1]
OPERATIONAL_DB = (ROOT / "r1-pmv" / "r1_pmv.sqlite3").resolve()

RUN_DIR = Path(os.environ["AUDIT10C_RUN_DIR"]).resolve()
if RUN_DIR.parent != (RESULTS / "datos").resolve() or not RUN_DIR.name.startswith("etapa10c-"):
    raise RuntimeError(f"Invalid audit10c directory: {RUN_DIR}")
marker = json.loads((RUN_DIR / "marker.json").read_text(encoding="utf-8"))
if marker.get("run") != RUN_DIR.name or marker.get("stage") != "10-C":
    raise RuntimeError("Audit10c marker mismatch")

os.environ.update(
    APP_ENV="test",
    DATABASE_URL="sqlite",
    DJANGO_DEBUG="false",
    DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost,testserver",
    DJANGO_SECRET_KEY=(RUN_DIR / ".django-key").read_text(encoding="utf-8").strip(),
)

from config import env as config_env  # noqa: E402

_orig_loader = config_env.load_dotenv
config_env.load_dotenv = lambda path=None: None
try:
    from config.settings import *  # noqa: F403, E402
finally:
    config_env.load_dotenv = _orig_loader

MODE = os.environ.get("AUDIT10C_MODE", "sqlite")
if MODE == "pg":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["AUDIT10C_PG_DB"],
            "USER": "postgres",
            "PASSWORD": "",
            "HOST": "127.0.0.1",
            "PORT": os.environ["AUDIT10C_PG_PORT"],
            "CONN_MAX_AGE": 0,
        }
    }
elif MODE == "clone":
    clone_path = (RUN_DIR / "r1_pmv_clone.sqlite3").resolve()
    if clone_path == OPERATIONAL_DB or clone_path.parent != RUN_DIR:
        raise RuntimeError(f"Refusing unsafe clone path: {clone_path}")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": clone_path,
            "OPTIONS": {"timeout": 20},
        }
    }
elif MODE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": RUN_DIR / "scale.sqlite3",
            "OPTIONS": {"timeout": 20},
        }
    }
else:
    raise RuntimeError(f"Unknown AUDIT10C_MODE: {MODE}")

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
SESSION_COOKIE_NAME = "audit10c_sessionid"
CSRF_COOKIE_NAME = "audit10c_csrftoken"
