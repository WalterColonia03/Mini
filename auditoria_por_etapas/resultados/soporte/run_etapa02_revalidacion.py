"""Revalidate existing Stage 02 tests using SQLite memory, without resetting files.

Run with r1-pmv/.venv/Scripts/python.exe from any directory. Evidence uses a fresh
UTC filename on every run. No persistent database or .env is opened by Django.
"""
from __future__ import annotations

import ast
import contextlib
import hashlib
import io
import json
import os
import secrets
import sys
import time
import types
import unittest
from datetime import datetime, timezone
from pathlib import Path


SUPPORT = Path(__file__).resolve().parent
RESULTS = SUPPORT.parent
ROOT = RESULTS.parent.parent
APP = ROOT / "r1-pmv"
sys.path.insert(0, str(APP))

LABELS = [
    "identity.test_etapa02_audit",
    "identity.tests",
    "identity.test_auth_audit01",
    "sales.tests.SalePreparationTests.test_logout_discards_active_draft_but_keeps_shift_and_stock",
    "sales.tests.SalePreparationTests.test_canceling_logout_keeps_the_session_and_draft",
]
EXECUTION_NAME = "02-A-revalidacion-servidor"


def digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def protected_hashes() -> dict[str, str | None]:
    paths = [APP / "r1_pmv.sqlite3"]
    paths.extend(sorted((RESULTS / "datos").glob("etapa0[012]-202611*/audit.sqlite3")))
    return {str(path.relative_to(ROOT).as_posix()): digest(path) for path in paths}


def redactions() -> set[str]:
    """Collect synthetic password literals without printing them or real secrets."""
    values: set[str] = set()
    for path in [APP / "identity" / "tests.py", APP / "identity" / "test_etapa02_audit.py",
                 APP / "identity" / "test_auth_audit01.py", APP / "sales" / "tests.py"]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                names = [target.id for target in node.targets if isinstance(target, ast.Name)]
                if any("password" in name.lower() for name in names):
                    values.add(node.value.value)
            if isinstance(node, ast.Dict):
                for key, value in zip(node.keys, node.values):
                    if isinstance(key, ast.Constant) and isinstance(key.value, str) and "password" in key.value.lower():
                        if isinstance(value, ast.Constant) and isinstance(value.value, str):
                            values.add(value.value)
    return {value for value in values if len(value) >= 4}


def main() -> int:
    started = datetime.now(timezone.utc)
    # Windows clocks may have coarser resolution than microseconds; concurrent
    # runners must never overwrite one another's evidence.
    stamp = started.strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(6)
    output_base = RESULTS / "evidencias" / f"02-revalidacion-{stamp}"
    before = protected_hashes()
    report = {
        "stage": "ETAPA-02", "execution": EXECUTION_NAME,
        "started_utc": started.isoformat(), "timezone_for_user_dates": "America/Lima",
        "engine": "django.db.backends.sqlite3", "database": ":memory:",
        "dotenv_loaded": False, "labels": LABELS, "checks": [], "methods": [],
        "limitations": [
            "Django TestCase/client/service tests; not browser evidence.",
            "Sequential SQLite does not demonstrate PostgreSQL row locks or concurrent last-admin safety.",
            "Method titles/docstrings are not proof of every criterion they mention.",
            "No recovery code, single-session or remote logout implementation is certified by this run.",
        ],
    }
    stream = io.StringIO()
    failures = 1
    timer = time.monotonic()
    with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
        # Prevent the usual settings import from reading operator .env values.
        import config.env
        config.env.load_dotenv = lambda path=None: None
        os.environ["APP_ENV"] = "test"
        os.environ["DJANGO_SECRET_KEY"] = "ephemeral-stage02-revalidation-memory-only"
        os.environ["DJANGO_DEBUG"] = "false"
        os.environ["DJANGO_ALLOWED_HOSTS"] = "localhost,127.0.0.1,testserver"
        os.environ["DATABASE_URL"] = "sqlite"
        import config.settings as base_settings
        isolated = types.ModuleType("audit02_revalidation_memory_settings")
        for name in dir(base_settings):
            if name.isupper():
                setattr(isolated, name, getattr(base_settings, name))
        isolated.DATABASES = {"default": {
            "ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:",
            "TEST": {"NAME": ":memory:"},
        }}
        sys.modules[isolated.__name__] = isolated
        os.environ["DJANGO_SETTINGS_MODULE"] = isolated.__name__

        import django
        django.setup()
        from django.conf import settings
        from django.core.management import call_command
        from django.test.runner import DiscoverRunner

        if settings.DATABASES["default"]["NAME"] != ":memory:":
            raise RuntimeError("Persistent database configuration rejected.")
        report["django_version"] = django.get_version()
        report["python_version"] = sys.version.split()[0]

        class Result(unittest.TextTestResult):
            def addSuccess(self, test):
                super().addSuccess(test)
                report["methods"].append({"id": test.id(), "status": "PASS"})

            def addFailure(self, test, err):
                super().addFailure(test, err)
                report["methods"].append({"id": test.id(), "status": "FAIL"})

            def addError(self, test, err):
                super().addError(test, err)
                report["methods"].append({"id": test.id(), "status": "ERROR"})

            def addSkip(self, test, reason):
                super().addSkip(test, reason)
                report["methods"].append({"id": test.id(), "status": "SKIP", "reason": reason})

        class Runner(DiscoverRunner):
            def get_test_runner_kwargs(self):
                kwargs = super().get_test_runner_kwargs()
                kwargs["resultclass"] = Result
                return kwargs

        try:
            for command, options in [
                ("check", {}),
                ("makemigrations", {"check": True, "dry_run": True}),
            ]:
                call_command(command, **options)
                report["checks"].append({"command": command, "options": options, "status": "PASS"})
            runner = Runner(verbosity=2, interactive=False, stream=stream)
            failures = runner.run_tests(LABELS)
        except (Exception, SystemExit) as exc:
            report["execution_error"] = type(exc).__name__
            print(f"Runner error type: {type(exc).__name__}")
    report["elapsed_seconds"] = round(time.monotonic() - timer, 3)
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    report["failure_count"] = failures
    report["method_count"] = len(report["methods"])
    report["protected_before"] = before
    report["protected_after"] = protected_hashes()
    report["protected_unchanged"] = report["protected_after"] == before
    sources = [APP / "identity" / "test_etapa02_audit.py", APP / "identity" / "tests.py",
               APP / "identity" / "test_auth_audit01.py", APP / "sales" / "tests.py",
               APP / "identity" / "services.py", APP / "identity" / "models.py",
               APP / "identity" / "forms.py", APP / "identity" / "views.py"]
    report["source_sha256_after"] = {str(p.relative_to(ROOT).as_posix()): digest(p) for p in sources}
    log = stream.getvalue()
    for secret in sorted(redactions(), key=len, reverse=True):
        log = log.replace(secret, "<REDACTED_TEST_SECRET>")
    output_base.with_suffix(".txt").write_text(log, encoding="utf-8")
    output_base.with_suffix(".json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"report": str(output_base.with_suffix(".json")), "log": str(output_base.with_suffix(".txt")),
                      "method_count": report["method_count"], "failure_count": failures,
                      "checks": report["checks"], "protected_unchanged": report["protected_unchanged"]}, indent=2))
    return 0 if not failures and report["protected_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
