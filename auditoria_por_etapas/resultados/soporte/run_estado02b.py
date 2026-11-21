"""Run state-intent regression against in-memory SQLite without loading .env."""
import contextlib
import io
import json
import os
from pathlib import Path
import sys
import types
from datetime import datetime, timezone

RESULTS = Path(__file__).resolve().parents[1]
ROOT = RESULTS.parent.parent
sys.path.insert(0, str(ROOT / "r1-pmv"))
import config.env
config.env.load_dotenv = lambda path=None: None
os.environ.update(APP_ENV="test", DJANGO_SECRET_KEY="memory-only-audit-state", DJANGO_DEBUG="false", DATABASE_URL="sqlite")
import config.settings as base
settings = types.ModuleType("audit_state02b_settings")
for key in dir(base):
    if key.isupper():
        setattr(settings, key, getattr(base, key))
settings.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:", "TEST": {"NAME": ":memory:"}}}
sys.modules[settings.__name__] = settings
os.environ["DJANGO_SETTINGS_MODULE"] = settings.__name__
import django
django.setup()
from django.test.runner import DiscoverRunner
out = io.StringIO()
with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
    runner = DiscoverRunner(verbosity=2, interactive=False, stream=out)
    failures = runner.run_tests(["identity.test_etapa02_estado"])
timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
label = sys.argv[1] if len(sys.argv) > 1 else "run"
if label not in ("antes", "despues"):
    raise SystemExit("Invalid label")
path = RESULTS / "evidencias" / f"02b-estado-{label}-{timestamp}.json"
payload = {"time_utc": timestamp, "label": label, "database": ":memory:", "failures": failures, "output": out.getvalue()}
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"file": str(path), "failures": failures, "output": out.getvalue()}, ensure_ascii=False))
sys.exit(1 if failures else 0)
