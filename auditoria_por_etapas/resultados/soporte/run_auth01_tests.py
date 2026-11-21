"""Run bounded stage-01 tests in SQLite memory, preserving sanitized evidence."""
from __future__ import annotations

from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
import hashlib
import importlib
import inspect
import io
import json
import os
from pathlib import Path
import re
import sys
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "r1-pmv"))
os.environ["DJANGO_SETTINGS_MODULE"] = "audit01_settings"
LABELS = (
    "identity.test_auth_audit01",
    "identity.tests.AuthenticationAndAuthorizationTests",
    "identity.tests.EmployeeEditDeactivateTests.test_login_lock_expires_after_fifteen_minutes",
    "identity.tests.EmployeeEditDeactivateTests.test_unknown_identifier_has_the_same_lock_response",
    "identity.tests.EmployeeEditDeactivateTests.test_success_resets_counter_without_deleting_throttle_row",
)
capture = io.StringIO()
exit_code = 0
started = datetime.now(ZoneInfo("America/Lima"))
with redirect_stdout(capture), redirect_stderr(capture):
    import django
    django.setup()
    from django.conf import settings
    from django.core.management import call_command
    database = Path(settings.DATABASES["default"]["NAME"]).resolve()
    expected = (ROOT / "auditoria_por_etapas/resultados/datos/etapa01-20261109/audit.sqlite3").resolve()
    if database != expected:
        raise SystemExit("Unexpected database configuration; refusing to run.")
    settings.DATABASES["default"]["TEST"]["NAME"] = ":memory:"
    settings.SESSION_COOKIE_NAME = "sessionid"
    settings.CSRF_COOKIE_NAME = "csrftoken"
    try:
        call_command("test", *LABELS, verbosity=2, interactive=False)
    except SystemExit as exc:
        exit_code = int(exc.code or 0)

# Failures must not make a generated fixture credential appear in evidence.
sanitized = capture.getvalue()
sensitive_values = {settings.SECRET_KEY}
for module_name in ("identity.test_auth_audit01", "identity.tests"):
    module = importlib.import_module(module_name)
    for _, cls in inspect.getmembers(module, inspect.isclass):
        for attribute in ("password", "wrong_password"):
            value = getattr(cls, attribute, None)
            if isinstance(value, str) and value:
                sensitive_values.add(value)
for value in sorted(sensitive_values, key=len, reverse=True):
    sanitized = sanitized.replace(value, "[REDACTED]")
sanitized = re.sub(r"(?i)((?:password|csrfmiddlewaretoken|sessionid|csrftoken)\s*[:=]\s*)[^\s,;}]+", r"\1[REDACTED]", sanitized)

evidence = ROOT / "auditoria_por_etapas/resultados/evidencias"
evidence.mkdir(parents=True, exist_ok=True)
stem = "01-auth-tests-" + started.strftime("%Y%m%d-%H%M%S-%f")
log_path = evidence / f"{stem}.txt"
with log_path.open("x", encoding="utf-8") as handle:
    handle.write(sanitized)
manifest = {
    "started_lima": started.isoformat(),
    "finished_lima": datetime.now(ZoneInfo("America/Lima")).isoformat(),
    "tool": "Django test runner / Client / ORM; no browser",
    "python": sys.version.split()[0], "django": django.get_version(),
    "settings": "audit01_settings", "test_database": "SQLite :memory:",
    "cookie_name_override_for_legacy_tests": ["sessionid", "csrftoken"],
    "labels": LABELS, "exit_code": exit_code,
    "log": log_path.name, "log_sha256": hashlib.sha256(log_path.read_bytes()).hexdigest(),
    "source_sha256": {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in (
            "r1-pmv/identity/views.py", "r1-pmv/identity/services.py",
            "r1-pmv/identity/test_auth_audit01.py", "r1-pmv/identity/tests.py",
        )
    },
}
with (evidence / f"{stem}.json").open("x", encoding="utf-8") as handle:
    json.dump(manifest, handle, ensure_ascii=False, indent=2)
summary = re.search(r"Ran \d+ tests in [^\n]+", sanitized)
print(summary.group(0) if summary else "No test summary found; inspect saved evidence.")
print("Result:", "PASS" if exit_code == 0 else "FAIL", "; exit:", exit_code)
print("Evidence:", log_path.relative_to(ROOT))
raise SystemExit(exit_code)
