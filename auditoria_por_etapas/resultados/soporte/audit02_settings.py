"""Settings aislados y reproducibles para la auditoría de la Etapa 02 (Sesión y personal).

Nunca toca `r1-pmv/r1_pmv.sqlite3`, `datos/etapa00-20261105/audit.sqlite3` ni `datos/etapa01-20261109/audit.sqlite3`.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


SOPORTE_DIR = Path(__file__).resolve().parent
RESULTADOS_DIR = SOPORTE_DIR.parent
ETAPAS_DIR = RESULTADOS_DIR.parent
REPO_ROOT = ETAPAS_DIR.parent
APP_ROOT = REPO_ROOT / "r1-pmv"

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
if str(SOPORTE_DIR) not in sys.path:
    sys.path.insert(0, str(SOPORTE_DIR))

from config.settings import *  # noqa: E402,F401,F403


AUDIT_STAGE = "ETAPA-02"
AUDIT_DB_DIR = RESULTADOS_DIR / "datos" / "etapa02-20261109"
AUDIT_DB_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DB_PATH = Path(os.environ.get("AUDIT02_DB_PATH", str(AUDIT_DB_DIR / "audit.sqlite3"))).resolve()

protected_db_paths = {
    (APP_ROOT / "r1_pmv.sqlite3").resolve(),
    (RESULTADOS_DIR / "datos" / "etapa00-20261105" / "audit.sqlite3").resolve(),
    (RESULTADOS_DIR / "datos" / "etapa01-20261109" / "audit.sqlite3").resolve(),
}
if AUDIT_DB_PATH in protected_db_paths:
    raise RuntimeError(f"Base protegida detectada: {AUDIT_DB_PATH}")

SECRET_KEY = "audit-etapa02-isolated-ephemeral-key-not-for-production"
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8767",
    "http://localhost:8767",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": AUDIT_DB_PATH,
    }
}

SESSION_COOKIE_NAME = "audit02_sessionid"
CSRF_COOKIE_NAME = "audit02_csrftoken"

MIDDLEWARE = [
    "audit02_settings.Audit02ProofHeaderMiddleware",
    *MIDDLEWARE,
]


class Audit02ProofHeaderMiddleware:
    """Expone una cabecera determinista para comprobar el proceso vivo."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        challenge = request.headers.get("X-Audit02-Challenge")
        if challenge:
            response["X-Audit02-Proof"] = f"{AUDIT_STAGE}:{challenge}:{AUDIT_DB_PATH.name}"
        response["X-Audit02-Stage"] = AUDIT_STAGE
        return response

