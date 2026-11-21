"""Exclusive, marked Stage 10-B audit settings; never loads operator .env or r1_pmv.sqlite3."""
import hashlib
import hmac
import json
import os
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[1]
RUN_DIR = Path(os.environ["AUDIT10B_RUN_DIR"]).resolve()
if RUN_DIR.parent != (RESULTS / "datos").resolve() or not RUN_DIR.name.startswith("etapa10b-"):
    raise RuntimeError(f"Invalid audit10b directory: {RUN_DIR}")
marker = json.loads((RUN_DIR / "marker.json").read_text(encoding="utf-8"))
if marker.get("run") != RUN_DIR.name or marker.get("stage") != "10-B":
    raise RuntimeError("Audit10b marker mismatch")

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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": RUN_DIR / "audit.sqlite3",
        "OPTIONS": {"timeout": 20},
    }
}
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
SESSION_COOKIE_NAME = "audit10b_sessionid"
CSRF_COOKIE_NAME = "audit10b_csrftoken"
if os.environ.get("AUDIT10B_DEFAULT_COOKIES") == "1":
    SESSION_COOKIE_NAME = "sessionid"
    CSRF_COOKIE_NAME = "csrftoken"


class ProofMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        nonce = request.headers.get("X-Audit10B-Challenge", "")
        if len(nonce) == 64 and all(c in "0123456789abcdef" for c in nonce):
            response["X-Audit10B-Proof"] = hmac.new(
                SECRET_KEY.encode(), nonce.encode(), hashlib.sha256  # noqa: F405
            ).hexdigest()
            response["X-Audit10B-Run"] = RUN_DIR.name
        return response


MIDDLEWARE = ["audit10b_settings.ProofMiddleware", *MIDDLEWARE]  # noqa: F405
