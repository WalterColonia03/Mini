"""Stage 15 (15-B) WSGI, HTTP Headers, Error 500, Deploy Config, Seed/Reset & CSP Probe.

Runs entirely against disposable temporary SQLite databases and ephemeral secrets in TEMP.
Never reads any operational .env, never modifies r1-pmv/ or r1_pmv.sqlite3.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import traceback
import urllib.error
import urllib.request
import uuid
from wsgiref.simple_server import WSGIRequestHandler, make_server

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "r1-pmv/manage.py").exists())
HERE.mkdir(parents=True, exist_ok=True)
STAMP = datetime.now(dt_timezone.utc).isoformat()
TMPDIR = (Path(tempfile.gettempdir()) / ("audit15b-srv-" + secrets.token_hex(8))).resolve()
TMPDIR.mkdir(exist_ok=False)
DB_LOCAL = TMPDIR / "db_local.sqlite3"
DB_SEED = TMPDIR / "db_seed.sqlite3"


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
    }


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class _QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):  # noqa: A002
        pass


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def http_get(url: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, str], bytes]:
    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with opener.open(req, timeout=10) as resp:
            return resp.status, {k.lower(): v for k, v in resp.headers.items()}, resp.read()
    except urllib.error.HTTPError as err:
        return err.code, {k.lower(): v for k, v in err.headers.items()}, err.read()


report: dict = {
    "started_utc": STAMP,
    "etapa": "ETAPA-15",
    "sublote": "15-B-SERVIDOR",
    "pasada": 1,
    "cursor_entrada": "15-SEGURIDAD-CORRECCIONES-PENDIENTES",
    "plan08_sha256": digest((ROOT / "08_Historias_de_Usuario.md").read_bytes()),
    "head": subprocess.check_output(["git", "-C", str(ROOT / "r1-pmv"), "rev-parse", "HEAD"], text=True).strip(),
    "before_build": compute_build(),
    "cases": [],
}

SECRET = secrets.token_urlsafe(48)


def run_case(case_id: str, fn) -> None:
    t0 = time.monotonic()
    try:
        details = fn() or {}
        report["cases"].append(
            {"id": case_id, "ok": True, "seconds": round(time.monotonic() - t0, 3), **details}
        )
    except Exception as exc:
        report["cases"].append(
            {
                "id": case_id,
                "ok": False,
                "seconds": round(time.monotonic() - t0, 3),
                "error": type(exc).__name__,
                "detail": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
    print(f"[{case_id}] ok={report['cases'][-1]['ok']}", flush=True)


try:
    sys.path.insert(0, str(ROOT / "r1-pmv"))
    os.environ.update(
        {
            "APP_ENV": "local",
            "DJANGO_DEBUG": "false",
            "DJANGO_SECRET_KEY": SECRET,
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DJANGO_ALLOWED_HOSTS": "127.0.0.1,localhost,testserver",
        }
    )
    from config import env as config_env

    config_env.load_dotenv = lambda path=None: None
    from django.conf import global_settings, settings

    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(DB_LOCAL),
        }
    }
    import django

    django.setup()
    from django.core.management import CommandError, call_command
    from django.db import connections
    from django.test import Client
    from django.test.utils import override_settings

    with io.StringIO() as buf:
        call_command("migrate", interactive=False, verbosity=0, stdout=buf, stderr=buf)

    # Case 1: WSGI raw server with DEBUG=False serves HTML 200 but 404 on /static/* and emits expected security headers
    def case_s15b_01_wsgi_static_and_headers() -> dict:
        from config.wsgi import application

        port = free_port()
        httpd = make_server("127.0.0.1", port, application, handler_class=_QuietHandler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            st_login, hdr_login, body_login = http_get(f"http://127.0.0.1:{port}/")
            st_css, hdr_css, _ = http_get(f"http://127.0.0.1:{port}/static/identity/app.css")
            st_js, _, _ = http_get(f"http://127.0.0.1:{port}/static/identity/navigation.js")
            st_fav, _, _ = http_get(f"http://127.0.0.1:{port}/favicon.ico")
            html = body_login.decode("utf-8", errors="replace")
            assert st_login == 200
            assert "/static/identity/app.css" in html
            assert "/static/identity/navigation.js" in html
            assert st_css == 404 and st_js == 404
            security_headers = {
                "x-content-type-options": hdr_login.get("x-content-type-options"),
                "referrer-policy": hdr_login.get("referrer-policy"),
                "x-frame-options": hdr_login.get("x-frame-options"),
                "cross-origin-opener-policy": hdr_login.get("cross-origin-opener-policy"),
                "cache-control": hdr_login.get("cache-control"),
                "content-security-policy": hdr_login.get("content-security-policy"),
                "permissions-policy": hdr_login.get("permissions-policy"),
                "strict-transport-security": hdr_login.get("strict-transport-security"),
                "x-request-id-present": bool(hdr_login.get("x-request-id")),
            }
            assert security_headers["x-content-type-options"] == "nosniff"
            assert security_headers["referrer-policy"] == "same-origin"
            assert security_headers["x-frame-options"] == "DENY"
            assert security_headers["content-security-policy"] is None
            assert security_headers["permissions-policy"] is None
            assert security_headers["strict-transport-security"] is None
            return {
                "login_status": st_login,
                "static_app_css_status_under_wsgi_debug_false": st_css,
                "static_navigation_js_status_under_wsgi_debug_false": st_js,
                "favicon_status": st_fav,
                "security_headers": security_headers,
            }
        finally:
            httpd.shutdown()
            httpd.server_close()
            connections.close_all()

    run_case("S15B-01-wsgi-debug-false-estaticos-y-headers", case_s15b_01_wsgi_static_and_headers)

    # Case 2: APP_ENV=production/demo SecurityMiddleware behavior in isolated subprocess WSGI
    def case_s15b_02_production_https_and_hsts() -> dict:
        py = str(ROOT / "r1-pmv/.venv/Scripts/python.exe")
        db_prod = TMPDIR / "db_prod.sqlite3"
        shutil.copy2(DB_LOCAL, db_prod)
        probe_code = """
import json, os, secrets
from pathlib import Path
from django.test import Client
from django.core.management import call_command

os.environ.update({
    "APP_ENV": "production",
    "DJANGO_DEBUG": "false",
    "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
    "DJANGO_ALLOWED_HOSTS": "testserver,127.0.0.1,localhost",
    "DJANGO_SETTINGS_MODULE": "config.settings",
})
import config.env as ce
ce.load_dotenv = lambda path=None: None
from django.conf import settings
settings.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.environ["PROBE_DB"]}}
import django
django.setup()
from identity.models import Account, Role
r = Role.objects.get_or_create(code="ADMIN", defaults={"name": "ADMIN"})[0]
pw = secrets.token_urlsafe(12) + "Aa1"
u = Account.objects.create_user(email="prodprobe@audit15b.invalid", password=pw, display_name="ProdProbe", role=r)

cl = Client(enforce_csrf_checks=True)
resp_plain_http = cl.get("/")
resp_https_login = cl.get("/", HTTP_X_FORWARDED_PROTO="https")
csrf_tok = resp_https_login.cookies[settings.CSRF_COOKIE_NAME].value
resp_post = cl.post(
    "/",
    {"email": u.email, "password": pw, "csrfmiddlewaretoken": csrf_tok},
    HTTP_X_FORWARDED_PROTO="https",
)
csrf_m = resp_https_login.cookies[settings.CSRF_COOKIE_NAME]
sess_m = cl.cookies[settings.SESSION_COOKIE_NAME]
print(json.dumps({
    "plain_http_status": resp_plain_http.status_code,
    "plain_http_location": resp_plain_http.headers.get("Location"),
    "https_get_status": resp_https_login.status_code,
    "hsts": resp_https_login.headers.get("Strict-Transport-Security"),
    "post_login_status": resp_post.status_code,
    "csrf_cookie_secure": bool(csrf_m["secure"]),
    "csrf_cookie_httponly": bool(csrf_m["httponly"]),
    "csrf_cookie_samesite": csrf_m["samesite"],
    "session_cookie_secure": bool(sess_m["secure"]),
    "session_cookie_httponly": bool(sess_m["httponly"]),
    "session_cookie_samesite": sess_m["samesite"],
    "session_cookie_age": settings.SESSION_COOKIE_AGE,
    "session_expire_at_browser_close": settings.SESSION_EXPIRE_AT_BROWSER_CLOSE,
}))
"""
        env = os.environ.copy()
        env["PROBE_DB"] = str(db_prod)
        env["PYTHONPATH"] = str(ROOT / "r1-pmv")
        res = subprocess.run([py, "-c", probe_code], env=env, capture_output=True, text=True, check=True, timeout=60)
        data = json.loads(res.stdout.strip().splitlines()[-1])
        assert data["plain_http_status"] == 301
        assert data["plain_http_location"].startswith("https://")
        assert data["https_get_status"] == 200
        assert data["hsts"] == "max-age=31536000; includeSubDomains; preload"
        assert data["post_login_status"] == 302
        assert data["csrf_cookie_secure"] is True and data["session_cookie_secure"] is True
        return data

    run_case("S15B-02-app-env-production-https-hsts-cookies", case_s15b_02_production_https_and_hsts)

    # Case 3: 500.html lacks request_id, RequestIdMiddleware response header on 500, and dead SENSITIVE_POST_PARAMETERS
    def case_s15b_03_error_500_y_redaccion() -> dict:
        from django.http import HttpResponse
        from django.urls import path
        import config.urls as root_urls

        has_core_setting = hasattr(global_settings, "SENSITIVE_POST_PARAMETERS")
        assert has_core_setting is False

        canary_pw = "Canary500Pass!"
        canary_sess = "CanarySessXYZ"

        def explode_view(request):
            raise RuntimeError(f"boom password={canary_pw} sessionid={canary_sess}")

        boom_slug = "audit15b-boom-" + secrets.token_hex(4)
        extra_route = path(boom_slug + "/", explode_view)
        orig_patterns = list(root_urls.urlpatterns)
        buf = io.StringIO()
        handler = logging.StreamHandler(buf)
        from app_platform.logging import RedactSensitiveDataFilter

        handler.addFilter(RedactSensitiveDataFilter())
        req_logger = logging.getLogger("django.request")
        req_logger.addHandler(handler)
        try:
            root_urls.urlpatterns = [*orig_patterns, extra_route]
            from django.urls import clear_url_caches

            clear_url_caches()
            cl = Client(raise_request_exception=False)
            resp = cl.get(f"/{boom_slug}/", HTTP_X_REQUEST_ID="audit15b-req-500")
            body = resp.content.decode("utf-8", errors="replace")
            log_text = buf.getvalue()
            assert resp.status_code == 500
            assert canary_pw not in body and canary_sess not in body
            assert canary_pw not in log_text and canary_sess not in log_text
            assert "[REDACTED]" in log_text
            assert "audit15b-req-500" not in body  # confirms 500.html does NOT display request_id
            assert resp.headers.get("X-Request-ID") == "audit15b-req-500"
            return {
                "global_settings_has_SENSITIVE_POST_PARAMETERS": has_core_setting,
                "status_code": resp.status_code,
                "x_request_id_header_on_500": resp.headers.get("X-Request-ID"),
                "request_id_visible_in_500_html": "audit15b-req-500" in body,
                "canary_leaked_in_html": False,
                "canary_leaked_in_log": False,
                "redacted_marker_in_log": True,
            }
        finally:
            root_urls.urlpatterns = orig_patterns
            from django.urls import clear_url_caches

            clear_url_caches()
            req_logger.removeHandler(handler)

    run_case("S15B-03-error-500-request-id-y-redaccion", case_s15b_03_error_500_y_redaccion)

    # Case 4: seed_pmv + reset_demo_db isolated subprocess check (no real .env or sqlite touched)
    def case_s15b_04_seed_and_reset_demo_db() -> dict:
        py = str(ROOT / "r1-pmv/.venv/Scripts/python.exe")
        probe_seed = """
import json, os, secrets
from datetime import timedelta
from decimal import Decimal
from django.core.management import CommandError, call_command
from django.db.models.deletion import ProtectedError
from django.utils import timezone as tz

os.environ.update({
    "APP_ENV": "local",
    "DJANGO_DEBUG": "false",
    "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
    "DJANGO_ALLOWED_HOSTS": "testserver,127.0.0.1,localhost",
    "DJANGO_SETTINGS_MODULE": "config.settings",
})
for k in ("SEED_ADMIN_PASSWORD", "SEED_WAREHOUSE_PASSWORD", "SEED_SELLER_PASSWORD"):
    os.environ.pop(k, None)
import config.env as ce
ce.load_dotenv = lambda path=None: None
from django.conf import settings
settings.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.environ["PROBE_DB"]}}
import django
django.setup()

call_command("migrate", interactive=False, verbosity=0)

missing_env_error = None
try:
    call_command("seed_pmv", verbosity=0)
except CommandError as exc:
    missing_env_error = str(exc)

pw_a = secrets.token_urlsafe(10) + "Aa1!"
pw_w = secrets.token_urlsafe(10) + "Ww1!"
pw_s = secrets.token_urlsafe(10) + "Ss1!"
os.environ["SEED_ADMIN_PASSWORD"] = pw_a
os.environ["SEED_WAREHOUSE_PASSWORD"] = pw_w
os.environ["SEED_SELLER_PASSWORD"] = pw_s

call_command("seed_pmv", verbosity=0)
call_command("seed_pmv", verbosity=0)  # idempotency second call

from identity.models import Account, LoginAttempt, IdentityAuditEvent
from catalog.models import Category, Product
from inventory.models import Supplier, StockWriteOff, PhysicalAdjustment, StockReceipt
from inventory.services import LotInput, confirm_initial_load, create_supplier, register_stock_entry, write_off_stock, register_physical_adjustment
from cash.models import CashRegister, CashShift, CashShiftClose
from cash.services import open_cash_shift, close_cash_shift
from sales.models import Sale
from sales.services import add_product_to_draft, checkout_sale

admin_u = Account.objects.get(email="admin@pmv.invalid")
wh_u = Account.objects.get(email="almacen@pmv.invalid")
sell_u = Account.objects.get(email="caja@pmv.invalid")
inact_u = Account.objects.get(email="inactiva.demo@pmv.invalid")
inact_uses_admin_pw = inact_u.check_password(pw_a)
legacy_cat_exists = Category.objects.filter(name="Productos enlatados").exists()
cat = Category.objects.get(name="Productos enlatados")
sup = create_supplier(actor=admin_u, name="ProvDemo15B", ruc="20123456789")
prod = Product.objects.create(category=cat, name="DemoProd15B", barcode="7759990001112", sale_price=Decimal("5.00"))
fut = tz.localdate() + timedelta(days=60)
load = confirm_initial_load(actor=wh_u, product=prod, lots=[LotInput("L-DEMO-1", 10, Decimal("2.0000"), fut)], supplier=sup)
lot = load.lots.get()
register_stock_entry(actor=wh_u, product=prod, lots=[LotInput("L-DEMO-2", 5, Decimal("2.2000"), fut + timedelta(days=5))], supplier=sup)
write_off_stock(actor=wh_u, lot=lot, quantity=1, reason=StockWriteOff.Reason.DAMAGE, notes="Rotura demo")
register_physical_adjustment(actor=admin_u, lot=lot, delta=-1, reason="Ajuste demo")
sh = open_cash_shift(actor=sell_u, opening_amount=Decimal("20.00"))
import uuid
dr = add_product_to_draft(actor=sell_u, product_id=prod.pk, quantity=1)
checkout_sale(actor=sell_u, draft_id=dr.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4())
close_cash_shift(actor=sell_u, counted_amount=Decimal("25.00"))

demo_env_blocked = None
with os.popen("") if False else open(os.devnull):
    settings.APP_ENV = "demo"
    try:
        call_command("reset_demo_db", "--yes", verbosity=0)
    except CommandError as exc:
        demo_env_blocked = str(exc)
    finally:
        settings.APP_ENV = "local"

reset_error = None
try:
    call_command("reset_demo_db", "--yes", verbosity=0)
except Exception as exc:
    reset_error = f"{type(exc).__name__}: {exc}"

print(json.dumps({
    "missing_env_error": missing_env_error,
    "inactiva_uses_admin_password": inact_uses_admin_pw,
    "legacy_cat_exists": legacy_cat_exists,
    "demo_env_blocked": demo_env_blocked,
    "reset_demo_db_local_error": reset_error,
    "surviving_sales": Sale.objects.count(),
    "surviving_writeoffs": StockWriteOff.objects.count(),
    "surviving_adjustments": PhysicalAdjustment.objects.count(),
    "surviving_receipts": StockReceipt.objects.count(),
    "surviving_suppliers": Supplier.objects.count(),
    "surviving_shifts": CashShift.objects.count(),
    "surviving_closes": CashShiftClose.objects.count(),
}))
"""
        env = os.environ.copy()
        env["PROBE_DB"] = str(DB_SEED)
        env["PYTHONPATH"] = str(ROOT / "r1-pmv")
        res = subprocess.run([py, "-c", probe_seed], env=env, capture_output=True, text=True, check=True, timeout=90)
        data = json.loads(res.stdout.strip().splitlines()[-1])
        assert data["missing_env_error"] is not None
        assert data["inactiva_uses_admin_password"] is True
        assert data["legacy_cat_exists"] is True
        assert data["demo_env_blocked"] is not None
        assert data["reset_demo_db_local_error"] is not None
        assert data["surviving_sales"] == 1
        return data

    run_case("S15B-04-seed-pmv-y-reset-demo-db-omisiones", case_s15b_04_seed_and_reset_demo_db)

    # Case 5: Static config & CSP readiness inventory on source files
    def case_s15b_05_config_deploy_y_csp_scan() -> dict:
        req_txt = (ROOT / "r1-pmv/requirements.txt").read_text(encoding="utf-8")
        dockerfile = (ROOT / "r1-pmv/Dockerfile").read_text(encoding="utf-8")
        compose = (ROOT / "r1-pmv/compose.yaml").read_text(encoding="utf-8")
        env_ex = (ROOT / "r1-pmv/.env.example").read_text(encoding="utf-8")
        gitignore = (ROOT / "r1-pmv/.gitignore").read_text(encoding="utf-8")
        seg_doc = (ROOT / "r1-pmv/docs/seguridad.md").read_text(encoding="utf-8")
        template_files = sorted(
            [*(ROOT / "r1-pmv/templates").glob("*.html"), *(ROOT / "r1-pmv").glob("*/templates/*/*.html")]
        )
        inline_scripts = []
        inline_handlers = []
        inline_styles = []
        for tf in template_files:
            rel = tf.relative_to(ROOT / "r1-pmv").as_posix()
            for lineno, line in enumerate(tf.read_text(encoding="utf-8").splitlines(), start=1):
                if re.search(r"<script(?![^>]*\bsrc=)", line, re.I):
                    inline_scripts.append(f"{rel}:{lineno}")
                if re.search(r"\bon(?:click|load|submit|change)\s*=", line, re.I):
                    inline_handlers.append(f"{rel}:{lineno}")
                if re.search(r"\bstyle\s*=", line, re.I):
                    inline_styles.append(f"{rel}:{lineno}")

        return {
            "requirements_has_whitenoise": "whitenoise" in req_txt.lower(),
            "dockerfile_runs_collectstatic": "collectstatic" in dockerfile.lower(),
            "dockerfile_cmd_uses_gunicorn": "gunicorn" in dockerfile,
            "compose_overrides_with_runserver": "runserver" in compose,
            "compose_uses_insecure_flag": "--insecure" in compose,
            "compose_has_tls_proxy": "nginx" in compose.lower() or "caddy" in compose.lower() or "traefik" in compose.lower(),
            "env_example_debug_false": "DJANGO_DEBUG=false" in env_ex,
            "gitignore_ignores_env": ".env" in gitignore.splitlines(),
            "docs_seguridad_stale_12_11": "12/11/2026" in seg_doc and "Requisitos pendientes" in seg_doc,
            "template_inline_scripts": inline_scripts,
            "template_inline_handlers": inline_handlers,
            "template_inline_style_count": len(inline_styles),
        }

    run_case("S15B-05-deploy-compose-y-inventario-csp", case_s15b_05_config_deploy_y_csp_scan)

except Exception as exc:
    report["fatal"] = {"type": type(exc).__name__, "detail": str(exc), "traceback": traceback.format_exc()}
finally:
    if "connections" in globals():
        connections.close_all()
    shutil.rmtree(TMPDIR, ignore_errors=True)
    report["tmpdir_deleted"] = not TMPDIR.exists()
    report["after_build"] = compute_build()
    report["source_stable"] = report["before_build"] == report["after_build"]
    report["passed"] = sum(1 for c in report["cases"] if c["ok"])
    report["total"] = len(report["cases"])
    report["ok"] = (
        not report.get("fatal")
        and report["passed"] == report["total"]
        and report["source_stable"]
        and report.get("tmpdir_deleted", False)
    )
    report["finished_utc"] = datetime.now(dt_timezone.utc).isoformat()
    (HERE / "resultados-servidor15b.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {k: report[k] for k in ("ok", "passed", "total", "source_stable", "tmpdir_deleted")},
            ensure_ascii=False,
        )
    )
sys.exit(0 if report["ok"] else 1)
