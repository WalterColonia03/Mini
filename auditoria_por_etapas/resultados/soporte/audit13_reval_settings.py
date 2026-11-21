"""Isolated Stage 13 revalidation settings; never loads .env or touches operational SQLites."""
import hashlib
import hmac
import json
import os
from pathlib import Path

from django.db import DatabaseError

RESULTS = Path(__file__).resolve().parents[1]
RUN_DIR = Path(os.environ["AUDIT13_REVAL_RUN_DIR"]).resolve()
if RUN_DIR.parent != (RESULTS / "datos").resolve() or not RUN_DIR.name.startswith("etapa13-reval-"):
    raise RuntimeError(f"Invalid audit13 revalidation directory: {RUN_DIR}")
if json.loads((RUN_DIR / "marker.json").read_text(encoding="utf-8"))["run"] != RUN_DIR.name:
    raise RuntimeError("Audit13 revalidation marker mismatch")

os.environ.update(
    APP_ENV="test",
    DATABASE_URL="sqlite",
    DJANGO_DEBUG="false",
    DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost,testserver",
    DJANGO_SECRET_KEY=(RUN_DIR / ".django-key").read_text(encoding="utf-8"),
)

from config import env as config_env

_loader = config_env.load_dotenv
config_env.load_dotenv = lambda path=None: None
try:
    from config.settings import *  # noqa: F403
finally:
    config_env.load_dotenv = _loader

if os.environ.get("AUDIT13_REVAL_PG_DB"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["AUDIT13_REVAL_PG_DB"],
            "USER": os.environ["AUDIT13_REVAL_PG_USER"],
            "PASSWORD": os.environ["AUDIT13_REVAL_PG_PASSWORD"],
            "HOST": os.environ.get("AUDIT13_REVAL_PG_HOST", "127.0.0.1"),
            "PORT": os.environ["AUDIT13_REVAL_PG_PORT"],
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": RUN_DIR / "audit.sqlite3",
        }
    }

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
SESSION_COOKIE_NAME = "audit13_reval_sessionid"
CSRF_COOKIE_NAME = "audit13_reval_csrftoken"


class Audit13RevalMiddleware:
    """Adds signed request proof headers and an isolated single-shot 500 fault trigger."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        nonce = request.headers.get("X-Audit13-Challenge", "")
        if len(nonce) == 64 and all(c in "0123456789abcdef" for c in nonce):
            response["X-Audit13-Proof"] = hmac.new(
                SECRET_KEY.encode(), nonce.encode(), hashlib.sha256  # noqa: F405
            ).hexdigest()
            response["X-Audit13-Run"] = RUN_DIR.name
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        flag = RUN_DIR / "force_500_once.flag"
        if request.path == "/inicio/" and flag.exists():
            from identity import views as identity_views

            flag.unlink(missing_ok=True)
            original = identity_views._dashboard_summary

            def _raise_once(*args, **kwargs):
                identity_views._dashboard_summary = original
                raise DatabaseError("audit13_reval simulated diagnostic token SECRET-999")

            identity_views._dashboard_summary = _raise_once
        return None


MIDDLEWARE = ["audit13_reval_settings.Audit13RevalMiddleware", *MIDDLEWARE]  # noqa: F405
