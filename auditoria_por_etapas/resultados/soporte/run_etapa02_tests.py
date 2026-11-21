"""Ejecuta la suite automatizada de la Etapa 02 y genera el diff reproducible de identity."""

from __future__ import annotations

import difflib
import io
import os
import sys
from pathlib import Path


SOPORTE_DIR = Path(__file__).resolve().parent
RESULTADOS_DIR = SOPORTE_DIR.parent
REPO_ROOT = RESULTADOS_DIR.parent.parent
APP_ROOT = REPO_ROOT / "r1-pmv"
EVIDENCIAS_DIR = RESULTADOS_DIR / "evidencias"
BASELINE_DIR = RESULTADOS_DIR / "datos" / "etapa02-20261109" / "baseline-identity"

if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))
if str(SOPORTE_DIR) not in sys.path:
    sys.path.insert(0, str(SOPORTE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "audit02_settings")


def build_diff() -> str:
    tracked = [
        "models.py",
        "forms.py",
        "services.py",
        "views.py",
        "templates/identity/employee_list.html",
    ]
    chunks: list[str] = []
    for rel in tracked:
        old_path = BASELINE_DIR / rel
        new_path = APP_ROOT / "identity" / rel
        old_lines = old_path.read_text(encoding="utf-8").splitlines(keepends=True)
        new_lines = new_path.read_text(encoding="utf-8").splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/r1-pmv/identity/{rel}",
            tofile=f"b/r1-pmv/identity/{rel}",
        )
        chunks.append("".join(diff))
    return "\n".join(c for c in chunks if c)


def main() -> int:
    import django

    django.setup()
    from django.conf import settings
    from django.core.management import call_command
    from django.test.runner import DiscoverRunner

    settings.SESSION_COOKIE_NAME = "sessionid"
    settings.CSRF_COOKIE_NAME = "csrftoken"

    EVIDENCIAS_DIR.mkdir(parents=True, exist_ok=True)
    diff_text = build_diff()
    (EVIDENCIAS_DIR / "02-identity-cambios.diff").write_text(diff_text, encoding="utf-8")

    buf = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = buf
    try:
        call_command("check")
        call_command("makemigrations", "--check", "--dry-run")
        runner = DiscoverRunner(verbosity=2, interactive=False)
        failures = runner.run_tests(
            [
                "identity.test_etapa02_audit",
                "identity.tests",
                "identity.test_auth_audit01",
                "sales.tests.SalePreparationTests.test_logout_discards_active_draft_but_keeps_shift_and_stock",
                "sales.tests.SalePreparationTests.test_canceling_logout_keeps_the_session_and_draft",
            ]
        )
    finally:
        sys.stdout, sys.stderr = old_out, old_err

    output = f"EXIT_FAILURES={failures}\n" + buf.getvalue()
    (EVIDENCIAS_DIR / "02-tests-etapa02.txt").write_text(output, encoding="utf-8")
    print(output)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
