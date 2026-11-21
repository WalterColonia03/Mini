"""Stage 15 (15-A) Isolated Local Server & Headless Chrome Security Verification Runner.

Starts an ephemeral ThreadedWSGIServer backed by a disposable SQLite DB with fictional test accounts,
runs audit15_browser.cjs in headless Chrome, verifies source integrity, and cleans up all temporary files.
"""
from __future__ import annotations

import contextlib
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import traceback
import uuid
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "r1-pmv/manage.py").exists())
HERE.mkdir(parents=True, exist_ok=True)
STAMP = datetime.now(dt_timezone.utc).isoformat()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_build() -> dict:
    names = (
        subprocess.check_output(
            ["git", "-C", str(ROOT / "r1-pmv"), "ls-files", "-co", "--exclude-standard", "-z"]
        )
        .decode()
        .split("\0")
    )
    files = {
        n: digest((ROOT / "r1-pmv" / n).read_bytes())
        for n in sorted(set(names))
        if n
        and not n.startswith("evidencias/")
        and Path(n).suffix in {".py", ".html", ".css", ".js", ".svg", ".ps1", ".sh"}
    }
    return {
        "count": len(files),
        "sha256": digest(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()),
        "files": files,
    }


class QuietWSGIHandler(WSGIRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return


class ThreadedWSGIServer(socketserver.ThreadingMixIn, WSGIServer):
    daemon_threads = True
    allow_reuse_address = True


TMP_DIR = Path(tempfile.mkdtemp(prefix="audit15-nav-"))
DB_PATH = TMP_DIR / "nav15.sqlite3"
CREDS_PATH = TMP_DIR / ".credentials.json"
IDS_PATH = TMP_DIR / "fixture_ids.json"

summary: dict = {
    "started_utc": STAMP,
    "etapa": "ETAPA-15",
    "sublote": "15-A-NAVEGADOR",
    "pasada": 1,
    "cursor_entrada": "15-SEGURIDAD-BASELINE-01",
    "plan08_sha256": digest((ROOT / "08_Historias_de_Usuario.md").read_bytes()),
    "head": subprocess.check_output(["git", "-C", str(ROOT / "r1-pmv"), "rev-parse", "HEAD"], text=True).strip(),
    "before_build": {k: v for k, v in compute_build().items() if k != "files"},
    "ok": False,
}

server = None
try:
    sys.path.insert(0, str(ROOT / "r1-pmv"))
    os.environ.update(
        {
            "APP_ENV": "test",
            "DJANGO_DEBUG": "false",
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DJANGO_ALLOWED_HOSTS": "127.0.0.1,localhost,testserver",
        }
    )
    from config import env as config_env

    config_env.load_dotenv = lambda path=None: None
    from django.conf import settings

    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(DB_PATH),
            "CONN_MAX_AGE": 0,
            "OPTIONS": {"timeout": 20},
        }
    }

    import django

    django.setup()
    from django.contrib.staticfiles.handlers import StaticFilesHandler
    from django.core.management import call_command
    from django.core.wsgi import get_wsgi_application
    from django.db import connections
    from django.utils import timezone as tz

    from cash.models import CashRegister
    from cash.services import close_cash_shift, open_cash_shift
    from catalog.models import Product
    from catalog.services import create_category, register_canned_product
    from identity.models import Account, Role
    from inventory.services import LotInput, confirm_initial_load, create_supplier
    from sales.services import add_product_to_draft, checkout_sale

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    pw = secrets.token_urlsafe(12) + "Aa1!"
    roles = {
        code: Role.objects.update_or_create(code=code, defaults={"name": label})[0]
        for code, label in Role.Code.choices
    }
    admin1 = Account.objects.create_user(
        "admin1@audit15.invalid", pw, display_name="Ana Admin", role=roles[Role.Code.ADMIN]
    )
    warehouse1 = Account.objects.create_user(
        "almacen1@audit15.invalid", pw, display_name="Bruno Almacen", role=roles[Role.Code.WAREHOUSE]
    )
    seller1 = Account.objects.create_user(
        "vendedor1@audit15.invalid", pw, display_name="Carla Ventas", role=roles[Role.Code.SELLER]
    )
    seller2 = Account.objects.create_user(
        "vendedor2@audit15.invalid", pw, display_name="Diego Ventas", role=roles[Role.Code.SELLER]
    )
    lockprobe = Account.objects.create_user(
        "lockprobe@audit15.invalid", pw, display_name="Lucia Lock", role=roles[Role.Code.SELLER]
    )
    staffprobe = Account.objects.create_user(
        "staffprobe@audit15.invalid",
        pw,
        display_name="Soporte Staff",
        role=roles[Role.Code.ADMIN],
        is_staff=True,
        is_superuser=True,
    )
    inactive1 = Account.objects.create_user(
        "inactivo1@audit15.invalid",
        pw,
        display_name="Elena Inactiva",
        role=roles[Role.Code.SELLER],
        is_active=False,
    )

    CashRegister.objects.update_or_create(code="CAJA-01", defaults={"is_active": True})
    cat = create_category(actor=admin1, name="Lácteos Navegador15")
    prod = register_canned_product(
        actor=admin1,
        name="Leche Fresca Navegador15",
        barcode="7751500999001",
        category=cat,
        unit=Product.Unit.UNIT,
        sale_price=Decimal("7.50"),
        minimum_stock=3,
        barcode_type=Product.BarcodeType.INTERNAL,
    )
    sup = create_supplier(actor=admin1, name="Distribuidora Navegador15", ruc="20123456789", phone="015551234")
    confirm_initial_load(
        actor=warehouse1,
        product=prod,
        supplier=sup,
        lots=[LotInput("NAV15-L1", 25, Decimal("4.2000"), tz.localdate() + timedelta(days=90))],
    )

    # Seed one closed shift & sale owned by seller2 to verify cross-seller ownership isolation in Chrome
    sh2 = open_cash_shift(actor=seller2, opening_amount=Decimal("50.00"))
    dr2 = add_product_to_draft(actor=seller2, product_id=prod.pk, quantity=2)
    sale2 = checkout_sale(actor=seller2, draft_id=dr2.pk, cash_received=Decimal("20.00"), idempotency_key=uuid.uuid4())
    close_cash_shift(actor=seller2, counted_amount=Decimal("65.00"))

    creds = {
        "admin": {"email": admin1.email, "password": pw},
        "warehouse": {"email": warehouse1.email, "password": pw},
        "seller1": {"email": seller1.email, "password": pw},
        "seller2": {"email": seller2.email, "password": pw},
        "lockprobe": {"email": lockprobe.email, "password": pw},
        "staffprobe": {"email": staffprobe.email, "password": pw},
        "inactive": {"email": inactive1.email, "password": pw},
    }
    CREDS_PATH.write_text(json.dumps(creds), encoding="utf-8")
    IDS_PATH.write_text(
        json.dumps(
            {
                "category_id": str(cat.pk),
                "product_id": str(prod.pk),
                "product_barcode": prod.barcode,
                "seller2_id": str(seller2.pk),
                "seller2_name": seller2.display_name,
                "seller2_shift_id": str(sh2.pk),
                "seller2_sale_id": str(sale2.pk),
                "seller2_sale_correlative": sale2.correlative,
                "seller1_id": str(seller1.pk),
            }
        ),
        encoding="utf-8",
    )

    app = StaticFilesHandler(get_wsgi_application())
    server = ThreadedWSGIServer(("127.0.0.1", 0), QuietWSGIHandler)
    server.set_app(app)
    port = server.server_address[1]
    srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
    srv_thread.start()

    node_env = os.environ.copy()
    node_env.update(
        {
            "AUDIT15_PORT": str(port),
            "AUDIT15_CREDS": str(CREDS_PATH),
            "AUDIT15_IDS": str(IDS_PATH),
            "AUDIT15_OUT": str(HERE),
        }
    )
    proc = subprocess.run(
        ["node", str(HERE / "audit15_browser.cjs")],
        cwd=str(HERE),
        env=node_env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    browser_stdout = (proc.stdout or "").replace(pw, "[REDACTED]")
    browser_stderr = (proc.stderr or "").replace(pw, "[REDACTED]")
    summary["node_returncode"] = proc.returncode
    summary["node_stdout"] = browser_stdout.strip()
    if browser_stderr.strip():
        summary["node_stderr"] = browser_stderr.strip()

    browser_report_path = HERE / "browser-report.json"
    if browser_report_path.exists():
        summary["browser"] = json.loads(browser_report_path.read_text(encoding="utf-8"))

    connections.close_all()
    assert proc.returncode == 0, f"Browser script failed: {browser_stderr}"
    summary["after_build"] = {k: v for k, v in compute_build().items() if k != "files"}
    summary["source_stable"] = summary["before_build"] == summary["after_build"]
    summary["ok"] = bool(summary.get("browser", {}).get("ok")) and summary["source_stable"]
except Exception as exc:
    summary["fatal"] = {"type": type(exc).__name__, "detail": str(exc), "traceback": traceback.format_exc()}
finally:
    if server is not None:
        with contextlib.suppress(Exception):
            server.shutdown()
            server.server_close()
    if CREDS_PATH.exists():
        CREDS_PATH.unlink()
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    summary["temp_dir_deleted"] = not TMP_DIR.exists()
    if "port" in locals():
        with socket.socket() as s:
            s.settimeout(1)
            summary["port_closed"] = s.connect_ex(("127.0.0.1", port)) != 0
    summary["finished_utc"] = datetime.now(dt_timezone.utc).isoformat()
    (HERE / "resultados-navegador15.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "ok": summary["ok"],
                "passed": summary.get("browser", {}).get("passed", 0),
                "total": summary.get("browser", {}).get("total", 0),
                "source_stable": summary.get("source_stable", False),
                "temp_dir_deleted": summary["temp_dir_deleted"],
            },
            ensure_ascii=False,
        )
    )
sys.exit(0 if summary["ok"] else 1)
