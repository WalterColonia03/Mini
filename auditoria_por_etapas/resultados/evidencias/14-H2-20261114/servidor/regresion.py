"""Suite completa sobre SQLite efímera, con manifiestos antes/después."""
import contextlib
import hashlib
import json
import logging
import os
from pathlib import Path
import runpy
import secrets
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) == 2 else HERE
OUT.mkdir(parents=True, exist_ok=True)
ROOT = next(p for p in HERE.parents if (p / "r1-pmv/manage.py").exists())
manifest = runpy.run_path(str(HERE.parent / "verificar.py"))["product"]
before = manifest()
start = datetime.now(timezone.utc).isoformat()
os.environ.update(APP_ENV="test", DJANGO_SETTINGS_MODULE="config.settings",
                  DJANGO_SECRET_KEY=secrets.token_urlsafe(50), DJANGO_DEBUG="false",
                  DJANGO_ALLOWED_HOSTS="testserver,localhost,127.0.0.1")
sys.path.insert(0, str(ROOT / "r1-pmv"))
os.chdir(ROOT / "r1-pmv")
from django.conf import settings
settings.DATABASES["default"] = {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
status = 0
with (OUT / "regresion-final.txt").open("x", encoding="utf-8") as log:
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        import django
        django.setup()
        logging.disable(logging.CRITICAL)
        from django.core.management import call_command
        try:
            call_command("test", interactive=False, verbosity=1)
            call_command("makemigrations", check=True, dry_run=True, verbosity=1)
        except SystemExit as exc:
            status = exc.code or 0
after = manifest()
changed = sorted(p for p in before.keys() | after.keys() if before.get(p) != after.get(p))
report = dict(inicio_utc=start, fin_utc=datetime.now(timezone.utc).isoformat(),
              base="SQLite :memory:, test runner", salida=status, archivos=len(after),
              cambios_durante_prueba=changed, fuentes=after,
              build=hashlib.sha256(json.dumps(after, sort_keys=True, separators=(",", ":")).encode()).hexdigest())
(OUT / "regresion-manifiesto.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in report.items() if k != "fuentes"}, indent=2))
sys.exit(status or bool(changed))
