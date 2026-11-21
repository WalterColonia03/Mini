"""Check configured cookie names and secure request behavior, never real TLS."""
from __future__ import annotations

import json
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / "r1-pmv"), str(Path(__file__).resolve().parent)]
os.environ["DJANGO_SETTINGS_MODULE"] = "audit01h_settings"
os.environ["AUDIT01H_ENV"] = "production"

from django.conf import settings

# Override before Django initializes its connections; this process owns only
# an in-memory database and never reads the workspace's operational DB.
settings.DATABASES["default"]["NAME"] = ":memory:"
import django

django.setup()
from django.core.management import call_command
from django.db import connection
from django.test import Client
from identity.models import Account, Role

assert connection.settings_dict["NAME"] == ":memory:"
call_command("migrate", interactive=False, verbosity=0)
role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador ficticio")
account = Account.objects.create_user(
    "tls-cookie-01h@ejemplo.invalid", secrets.token_urlsafe(32),
    display_name="Auditoría ficticia", role=role,
)
password = secrets.token_urlsafe(32)
account.set_password(password)
account.save(update_fields=["password"])
client = Client(enforce_csrf_checks=True)
insecure_status = Client().get("/", secure=False).status_code
start = client.get("/", secure=True)
csrf = start.cookies[settings.CSRF_COOKIE_NAME]
response = client.post(
    "/", {"email": account.email, "password": password, "csrfmiddlewaretoken": csrf.value},
    secure=True, HTTP_REFERER="https://testserver/",
)
session = response.cookies[settings.SESSION_COOKIE_NAME]
dashboard = client.get("/inicio/", secure=True)
result = {
    "environment": settings.APP_ENV,
    "database": ":memory:",
    "tool": "Django Client; secure=True with same-origin Referer, no TLS or real proxy",
    "plain_http_redirect_status": insecure_status,
    "https_simulated_get_status": start.status_code,
    "https_simulated_login_status": response.status_code,
    "login_location": response.headers.get("Location"),
    "https_simulated_dashboard_status": dashboard.status_code,
    "csrf_secure": bool(csrf["secure"]),
    "csrf_httponly": bool(csrf["httponly"]),
    "csrf_samesite": csrf["samesite"],
    "session_secure": bool(session["secure"]),
    "session_httponly": bool(session["httponly"]),
    "session_samesite": session["samesite"],
    "custom_cookie_names_used": settings.CSRF_COOKIE_NAME.startswith("audit01h_") and settings.SESSION_COOKIE_NAME.startswith("audit01h_"),
}
assert insecure_status == 301 and response.status_code == 302 and dashboard.status_code == 200
assert result["csrf_secure"] and result["session_secure"] and result["session_httponly"]
out = ROOT / "auditoria_por_etapas/resultados/evidencias/01-H-20261115/tls-cookies-simulados.json"
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
