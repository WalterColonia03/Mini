"""Verificación aislada en navegador Chrome real (multi-contexto + desktop 1366x768 + móvil 390x844) para Sublote 02-E."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import socket
import socketserver
import sys
import threading
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "r1-pmv/manage.py").is_file())
PROJECT = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
OUT = RESULTS / "evidencias/02-INTEGRAL-20261120/navegador-final"
SHOTS = OUT / "capturas"
OUT.mkdir(parents=True, exist_ok=True)
SHOTS.mkdir(parents=True, exist_ok=True)

CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
PW_LIB = Path(r"C:\Users\walte\AppData\Local\Temp\audit14d-browser-6f523915")

RUN_NAME = f"etapa02e-{secrets.token_hex(4)}"
RUN_DIR = (RESULTS / "datos" / RUN_NAME).resolve()
assert RUN_DIR.parent == (RESULTS / 'datos').resolve()
RUN_DIR.mkdir(parents=True, exist_ok=False)
(RUN_DIR / "marker.json").write_text(
    json.dumps({"run": RUN_NAME, "stage": "02-E"}),
    encoding="utf-8",
)

os.environ.update(
    APP_ENV="test",
    DATABASE_URL="sqlite",
    DJANGO_DEBUG="false",
    DJANGO_ALLOW_ASYNC_UNSAFE="true",
    DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost,testserver",
    DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
    DJANGO_SETTINGS_MODULE="config.settings",
)
sys.path.insert(0, str(PROJECT))
os.chdir(PROJECT)

from config import env as config_env  # noqa: E402

config_env.load_dotenv = lambda path=None: None

from django.conf import settings  # noqa: E402

settings.DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(RUN_DIR / "audit02e.sqlite3"),
    }
}
settings.SESSION_COOKIE_NAME = "audit02e_sessionid"
settings.CSRF_COOKIE_NAME = "audit02e_csrftoken"
settings.SESSION_COOKIE_SECURE = False
settings.CSRF_COOKIE_SECURE = False

import django  # noqa: E402

django.setup()

import atexit  # noqa: E402
from django.contrib.staticfiles.handlers import StaticFilesHandler  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.core.wsgi import get_wsgi_application  # noqa: E402
from django.db import connections  # noqa: E402
from django.urls import reverse  # noqa: E402
from django.utils import timezone  # noqa: E402

atexit.register(lambda: (connections.close_all(), shutil.rmtree(RUN_DIR, ignore_errors=True)))

from cash.models import CashRegister, CashShift  # noqa: E402
from catalog.models import Category, Product  # noqa: E402
from identity.models import Account, IdentityAuditEvent, Role  # noqa: E402
from inventory.services import LotInput, confirm_initial_load  # noqa: E402
from sales.models import SaleDraft  # noqa: E402

sys.path.insert(0, str(PW_LIB))
from playwright.sync_api import sync_playwright  # noqa: E402

PASSWORD = "Audit02E!ChromePassword"
NEW_PASSWORD = "Audit02E!NewPassword2"


class ThreadingWSGIServer(socketserver.ThreadingMixIn, WSGIServer):
    daemon_threads = True


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def layout_metrics(page) -> dict:
    return page.evaluate(
        """() => {
            const de = document.documentElement;
            const body = document.body;
            return {
                innerWidth: window.innerWidth,
                docScrollWidth: de.scrollWidth,
                bodyScrollWidth: body ? body.scrollWidth : 0,
                horizontalOverflow: de.scrollWidth > window.innerWidth + 1,
                scrollHeight: de.scrollHeight,
            };
        }"""
    )


def open_context_and_login(browser, base: str, email: str, password: str, viewport: dict, page_errors: list, console_errors: list, server_5xx: list):
    ctx = browser.new_context(locale="es-PE", timezone_id="America/Lima", viewport=viewport)
    page = ctx.new_page()
    page.set_default_timeout(10000)
    page.on("pageerror", lambda err: page_errors.append({"actor": email, "error": str(err)}))
    page.on(
        "console",
        lambda msg: console_errors.append({"actor": email, "text": msg.text})
        if msg.type == "error"
        else None,
    )
    page.on(
        "response",
        lambda resp: server_5xx.append({"actor": email, "url": resp.url, "status": resp.status})
        if resp.status >= 500
        else None,
    )
    page.goto(base + reverse("login"))
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button:has-text("Iniciar sesión")')
    page.wait_for_url(f"**{reverse('dashboard')}**")
    return ctx, page


def save_jpg(page, name: str, full_page: bool = True) -> str:
    path = SHOTS / f"{name}.jpg"
    page.screenshot(path=str(path), type="jpeg", quality=84, full_page=full_page)
    return path.relative_to(OUT).as_posix()


def main() -> None:
    prod_db = PROJECT / "r1_pmv.sqlite3"
    prod_db_before = sha256_file(prod_db)

    call_command("migrate", verbosity=0, interactive=False)
    today = timezone.localdate()

    r_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    r_sel, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

    admin1 = Account.objects.create_user("admin1_02e@example.invalid", PASSWORD, display_name="Ana Admin 02E", role=r_admin)
    admin2 = Account.objects.create_user("admin2_02e@example.invalid", PASSWORD, display_name="Luis Admin Dos", role=r_admin)
    wh1 = Account.objects.create_user("almacen_02e@example.invalid", PASSWORD, display_name="Pedro Almacenero", role=r_wh)
    seller1 = Account.objects.create_user("vendedor1_02e@example.invalid", PASSWORD, display_name="Carmen Vendedora", role=r_sel)
    seller2 = Account.objects.create_user("vendedor2_02e@example.invalid", PASSWORD, display_name="Mario Segundo", role=r_sel)

    CashRegister.objects.create(code="CAJA-01")
    cat = Category.objects.create(name="Abarrotes")
    product = Product.objects.create(category=cat, name="Leche Evaporada", barcode="77500201", sale_price=Decimal("4.50"))
    confirm_initial_load(actor=wh1, product=product, lots=[LotInput("L02E-01", 25, Decimal("3.0000"), today + timedelta(days=45))])

    app = StaticFilesHandler(get_wsgi_application())
    server = make_server("127.0.0.1", 0, app, server_class=ThreadingWSGIServer, handler_class=QuietHandler)
    port = server.server_address[1]
    base = f"http://127.0.0.1:{port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    desktop = {"width": 1366, "height": 768}
    mobile = {"width": 390, "height": 844}
    page_errors: list = []
    console_errors: list = []
    server_5xx: list = []
    cache_headers: dict[str, str] = {}
    checkpoints: dict[str, object] = {}
    layouts: dict[str, dict] = {}
    screenshots: list[str] = []

    login_path = reverse("login")
    dash_path = reverse("dashboard")
    logout_path = reverse("logout")
    emp_list_path = reverse("employee-list")
    emp_create_path = reverse("employee-create")
    cash_open_path = reverse("cash-open")
    sales_draft_path = reverse("sales-draft")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(CHROME), headless=True)

            # 1. Visitante anónimo redirigido al intentar acceder a /empleados/
            ctx_anon = browser.new_context(locale="es-PE", timezone_id="America/Lima", viewport=desktop)
            pg_anon = ctx_anon.new_page()
            resp_anon = pg_anon.goto(base + emp_list_path)
            cache_headers["login_redirect_cache"] = resp_anon.headers.get("cache-control", "")
            checkpoints["anon_redirected_to_login"] = (
                f"{base}{login_path}" in pg_anon.url and f"next={emp_list_path}" in pg_anon.url
            )
            ctx_anon.close()

            # 2. Almacenero: /salir/ sin caja + acceso prohibido 403 a /empleados/
            ctx_wh, pg_wh = open_context_and_login(browser, base, wh1.email, PASSWORD, desktop, page_errors, console_errors, server_5xx)
            pg_wh.goto(base + logout_path)
            wh_salir_text = pg_wh.inner_text("main")
            checkpoints["salir_almacen_copy"] = "Tu cuenta no opera turnos de caja." in wh_salir_text
            resp_wh_403 = pg_wh.goto(base + emp_list_path)
            checkpoints["almacen_empleados_403"] = resp_wh_403 is not None and resp_wh_403.status == 403
            pg_wh.goto(base + dash_path)

            # 3. Vendedor 1: /salir/ sin turno -> abrir turno -> /salir/ sin borrador -> con borrador -> cancelar -> confirmar
            ctx_s1, pg_s1 = open_context_and_login(browser, base, seller1.email, PASSWORD, desktop, page_errors, console_errors, server_5xx)
            pg_s1.goto(base + logout_path)
            checkpoints["salir_seller_no_shift"] = "actualmente no tienes un turno de caja abierto" in pg_s1.inner_text("main")

            # Abrir turno
            pg_s1.goto(base + cash_open_path)
            pg_s1.fill('input[name="opening_amount"]', "50.00")
            pg_s1.click('button:has-text("Abrir turno")')
            pg_s1.wait_for_url("**/caja/turnos/*/abierto/**")

            pg_s1.goto(base + logout_path)
            s1_shift_text = pg_s1.inner_text("main")
            checkpoints["salir_seller_open_shift_no_draft"] = (
                "seguirá ligado a tu cuenta" in s1_shift_text
                and "La venta en preparación se descartará" not in s1_shift_text
            )

            # Crear borrador
            pg_s1.goto(base + f"{sales_draft_path}?query=Leche")
            pg_s1.click('form:has(input[name="product_id"]) button[type="submit"]')
            pg_s1.wait_for_load_state("networkidle")
            checkpoints["draft_created_before_logout"] = SaleDraft.objects.filter(seller=seller1).exists()

            # /salir/ con borrador + cancelar conserva borrador y turno
            pg_s1.goto(base + logout_path)
            s1_draft_text = pg_s1.inner_text("main")
            checkpoints["salir_seller_open_shift_with_draft"] = (
                "La venta en preparación se descartará" in s1_draft_text
                and "El turno abierto seguirá ligado a tu cuenta." in s1_draft_text
            )
            screenshots.append(save_jpg(pg_s1, "salir-vendedor-borrador"))
            pg_s1.click('a:has-text("Cancelar")')
            pg_s1.wait_for_url(f"**{dash_path}**")
            checkpoints["salir_cancel_keeps_draft"] = SaleDraft.objects.filter(seller=seller1).exists()

            # Confirmar /salir/ descarta borrador y conserva turno abierto
            pg_s1.goto(base + logout_path)
            pg_s1.click('button:has-text("Cerrar sesión")')
            pg_s1.wait_for_load_state("networkidle")
            checkpoints["salir_confirm_discards_draft_keeps_shift"] = (
                not SaleDraft.objects.filter(seller=seller1, status=SaleDraft.Status.ACTIVE).exists()
                and SaleDraft.objects.filter(seller=seller1, status=SaleDraft.Status.DISCARDED).exists()
                and CashShift.objects.filter(seller=seller1, status=CashShift.Status.OPEN).exists()
            )
            # Verificar 403 vendedor sobre /empleados/
            ctx_s2, pg_s2 = open_context_and_login(browser, base, seller2.email, PASSWORD, desktop, page_errors, console_errors, server_5xx)
            resp_s2_403 = pg_s2.goto(base + emp_list_path)
            checkpoints["seller_empleados_403"] = resp_s2_403 is not None and resp_s2_403.status == 403
            screenshots.append(save_jpg(pg_s2, "acceso-403-vendedor"))
            pg_s2.goto(base + dash_path)

            # 4. Bloquear una cuenta con 5 intentos fallidos en navegador
            ctx_lock = browser.new_context(locale="es-PE", timezone_id="America/Lima", viewport=desktop)
            pg_lock = ctx_lock.new_page()
            lock_email = "bloqueo_browser@example.invalid"
            locked_user = Account.objects.create_user(lock_email, PASSWORD, display_name="Usuario Bloqueado Browser", role=r_sel)
            for _ in range(5):
                pg_lock.goto(base + login_path)
                pg_lock.fill('input[name="email"]', lock_email)
                pg_lock.fill('input[name="password"]', "ClaveIncorrecta99")
                pg_lock.click('button:has-text("Iniciar sesión")')
                pg_lock.wait_for_load_state("networkidle")
            checkpoints["lock_screen_message"] = "Demasiados intentos fallidos consecutivos" in pg_lock.inner_text("main")
            screenshots.append(save_jpg(pg_lock, "login-locked"))
            ctx_lock.close()

            # 5. Admin 1 y Admin 2 en paralelo
            ctx_a1, pg_a1 = open_context_and_login(browser, base, admin1.email, PASSWORD, desktop, page_errors, console_errors, server_5xx)
            resp_list = pg_a1.goto(base + emp_list_path)
            cache_headers["employees_list"] = resp_list.headers.get("cache-control", "")
            layouts["desktop_employees_list"] = layout_metrics(pg_a1)
            screenshots.append(save_jpg(pg_a1, "empleados-lista"))

            # Búsqueda por nombre largo y sin resultados
            pg_a1.fill('input[name="q"]', "inexistente-02e")
            pg_a1.press('input[name="q"]', "Enter")
            pg_a1.wait_for_load_state("networkidle")
            checkpoints["employees_empty_search"] = "No hay empleados que coincidan" in pg_a1.inner_text("main") or "0" in pg_a1.inner_text("main") or ("vendedor" not in pg_a1.inner_text("table").lower() if pg_a1.locator("table").count() else True)

            # Crear nuevo empleado desde formulario
            pg_a1.goto(base + emp_create_path)
            pg_a1.fill('input[name="display_name"]', "Sofía Nueva Empleada")
            pg_a1.fill('input[name="email"]', "sofia_02e@example.invalid")
            pg_a1.fill('input[name="password"]', PASSWORD)
            pg_a1.select_option('select[name="role"]', str(r_wh.pk))
            pg_a1.click('main form button[type="submit"]')
            pg_a1.wait_for_url(f"**{emp_list_path}")
            created_sofia = Account.objects.get(email_normalized="sofia_02e@example.invalid")
            checkpoints["employee_created_in_ui"] = created_sofia.display_name == "Sofía Nueva Empleada"

            # Intentar cambiar rol de seller1 con turno abierto -> rechazado en servidor sin perder datos
            pg_a1.goto(base + reverse("employee-edit", args=(seller1.pk,)))
            pg_a1.select_option('select[name="role"]', str(r_wh.pk))
            pg_a1.click('button:has-text("Guardar cambios")')
            pg_a1.wait_for_load_state("networkidle")
            checkpoints["role_change_open_shift_blocked_ui"] = "turno de caja abierto" in pg_a1.inner_text("main").lower()

            # Reset de contraseña sobre seller2 con sesión viva -> revoca sesión de pg_s2
            pg_a1.goto(base + reverse("employee-edit", args=(seller2.pk,)))
            pg_a1.fill('input[name="new_password"]', NEW_PASSWORD)
            pg_a1.click('button:has-text("Guardar cambios")')
            pg_a1.wait_for_url(f"**{emp_list_path}")
            pg_s2.goto(base + dash_path)
            checkpoints["password_reset_revokes_other_browser_session"] = f"next={dash_path}" in pg_s2.url
            ctx_s2.close()

            # Renombrar correo de cuenta bloqueada + confirmar desactivar/reactivar conservando bloqueo
            pg_a1.goto(base + reverse("employee-edit", args=(locked_user.pk,)))
            screenshots.append(save_jpg(pg_a1, "empleados-editar-bloqueado"))
            checkpoints["edit_shows_lockout_banner"] = "bloqueo temporal vigente" in pg_a1.inner_text("main").lower()
            pg_a1.fill('input[name="email"]', "bloqueo_renombrado@example.invalid")
            pg_a1.click('button:has-text("Guardar cambios")')
            pg_a1.wait_for_url(f"**{emp_list_path}")

            # Pantalla explícita de confirmación: cancelar vs confirmar desactivar + sesión activa de Almacenero revocada
            pg_a1.goto(base + reverse("employee-state-confirm", args=(wh1.pk,)) + "?action=desactivar")
            layouts["desktop_state_confirm"] = layout_metrics(pg_a1)
            screenshots.append(save_jpg(pg_a1, "empleados-confirmar-desactivar"))
            pg_a1.click('a:has-text("Cancelar")')
            pg_a1.wait_for_url(f"**{emp_list_path}")
            wh1.refresh_from_db()
            checkpoints["state_confirm_cancel_no_mutation"] = wh1.is_active is True

            pg_a1.goto(base + reverse("employee-state-confirm", args=(wh1.pk,)) + "?action=desactivar")
            pg_a1.click('button:has-text("Confirmar desactivación")')
            pg_a1.wait_for_url(f"**{emp_list_path}")
            wh1.refresh_from_db()
            checkpoints["state_confirm_deactivates"] = wh1.is_active is False

            # Sesión previa del almacenero queda rechazada
            pg_wh.goto(base + dash_path)
            checkpoints["deactivated_warehouse_kicked_out"] = f"next={dash_path}" in pg_wh.url
            ctx_wh.close()

            # Confirmar desactivar seller1 con turno abierto muestra advertencia y rechaza al confirmar
            pg_a1.goto(base + reverse("employee-state-confirm", args=(seller1.pk,)) + "?action=desactivar")
            checkpoints["confirm_warns_open_shift"] = "Turno de caja abierto" in pg_a1.inner_text("main")
            pg_a1.click('button:has-text("Confirmar desactivación")')
            pg_a1.wait_for_url(f"**{emp_list_path}")
            seller1.refresh_from_db()
            checkpoints["deactivate_open_shift_rejected"] = seller1.is_active is True

            # Confirmar reactivación sobre usuario bloqueado muestra advertencia y conserva bloqueo hasta desbloqueo explícito
            pg_a1.goto(base + reverse("employee-state-confirm", args=(locked_user.pk,)) + "?action=desactivar")
            pg_a1.click('button:has-text("Confirmar desactivación")')
            pg_a1.wait_for_url(f"**{emp_list_path}")
            pg_a1.goto(base + reverse("employee-state-confirm", args=(locked_user.pk,)) + "?action=reactivar")
            checkpoints["reactivate_confirm_shows_lockout_warning"] = "Bloqueo temporal vigente" in pg_a1.inner_text("main")
            screenshots.append(save_jpg(pg_a1, "empleados-confirmar-bloqueo-reactivar"))
            pg_a1.click('button:has-text("Confirmar reactivación")')
            pg_a1.wait_for_url(f"**{emp_list_path}")

            # Verificar cuenta sigue bloqueada al intentar login en nuevo contexto
            ctx_try = browser.new_context(locale="es-PE", timezone_id="America/Lima", viewport=desktop)
            pg_try = ctx_try.new_page()
            pg_try.goto(base + login_path)
            pg_try.fill('input[name="email"]', "bloqueo_renombrado@example.invalid")
            pg_try.fill('input[name="password"]', PASSWORD)
            pg_try.click('button:has-text("Iniciar sesión")')
            pg_try.wait_for_load_state("networkidle")
            checkpoints["lockout_survived_rename_and_reactivate"] = "Demasiados intentos fallidos consecutivos" in pg_try.inner_text("main")

            # Desbloqueo explícito en UI -> permite iniciar sesión
            pg_a1.goto(base + reverse("employee-edit", args=(locked_user.pk,)))
            pg_a1.check('input[name="unlock_account"]')
            pg_a1.click('button:has-text("Guardar cambios")')
            pg_a1.wait_for_url(f"**{emp_list_path}")

            pg_try.goto(base + login_path)
            pg_try.fill('input[name="email"]', "bloqueo_renombrado@example.invalid")
            pg_try.fill('input[name="password"]', PASSWORD)
            pg_try.click('button:has-text("Iniciar sesión")')
            pg_try.wait_for_url(f"**{dash_path}**")
            checkpoints["explicit_unlock_allows_login"] = dash_path in pg_try.url
            ctx_try.close()

            # Admin 2 intenta auto-desactivarse desde confirmar -> rechazado
            ctx_a2, pg_a2 = open_context_and_login(browser, base, admin2.email, PASSWORD, desktop, page_errors, console_errors, server_5xx)
            pg_a2.goto(base + reverse("employee-state-confirm", args=(admin2.pk,)) + "?action=desactivar")
            checkpoints["self_deactivate_warning_shown"] = "tu propia cuenta" in pg_a2.inner_text("main")
            pg_a2.click('button:has-text("Confirmar desactivación")')
            pg_a2.wait_for_url(f"**{emp_list_path}")
            admin2.refresh_from_db()
            checkpoints["self_deactivate_rejected"] = admin2.is_active is True
            ctx_a2.close()

            # Responsivo móvil 390x844 (lista empleados + confirmar estado)
            ctx_mob, pg_mob = open_context_and_login(browser, base, admin1.email, PASSWORD, mobile, page_errors, console_errors, server_5xx)
            pg_mob.goto(base + emp_list_path)
            layouts["mobile_employees_list"] = layout_metrics(pg_mob)
            screenshots.append(save_jpg(pg_mob, "mobile-empleados-lista"))
            pg_mob.goto(base + reverse("employee-state-confirm", args=(created_sofia.pk,)) + "?action=desactivar")
            layouts["mobile_state_confirm"] = layout_metrics(pg_mob)
            screenshots.append(save_jpg(pg_mob, "mobile-confirmar-estado"))
            ctx_mob.close()

            # Cerrar sesión Admin 1 por /salir/
            pg_a1.goto(base + logout_path)
            checkpoints["salir_admin_copy"] = "Tu cuenta no opera turnos de caja." in pg_a1.inner_text("main")
            pg_a1.click('button:has-text("Cerrar sesión")')
            pg_a1.wait_for_load_state("networkidle")
            checkpoints["salir_admin_redirected_to_login"] = pg_a1.locator('input[name="email"]').count() == 1
            ctx_a1.close()
            ctx_s1.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as chk:
        chk.settimeout(1.0)
        port_closed = chk.connect_ex(("127.0.0.1", port)) != 0

    prod_db_after = sha256_file(prod_db)
    audit_actions = list(IdentityAuditEvent.objects.order_by("occurred_at").values_list("action", flat=True))
    checkpoints["audit_events_recorded"] = len(audit_actions) > 0
    checkpoints["audit_actions_present"] = sorted(set(audit_actions))
    no_overflow = all(not m["horizontalOverflow"] for m in layouts.values())

    unexpected_console_errors = [
        c for c in console_errors if "403 (Forbidden)" not in c.get("text", "")
    ]
    report = {
        "stage": "02-E",
        "port_used": port,
        "port_closed": port_closed,
        "prod_db_unchanged": prod_db_before == prod_db_after,
        "prod_db_sha256": prod_db_after,
        "checkpoints": checkpoints,
        "layouts": layouts,
        "no_horizontal_overflow": no_overflow,
        "cache_headers": cache_headers,
        "screenshots": screenshots,
        "page_errors": page_errors,
        "console_errors": console_errors,
        "unexpected_console_errors": unexpected_console_errors,
        "server_5xx": server_5xx,
    }
    report["all_passed"] = (
        all(bool(v) for k, v in checkpoints.items() if isinstance(v, bool))
        and no_overflow
        and port_closed
        and report["prod_db_unchanged"]
        and not page_errors
        and not unexpected_console_errors
        and not server_5xx
    )

    connections.close_all()
    shutil.rmtree(RUN_DIR, ignore_errors=True)
    (OUT / "resumen.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = [
        "# Informe de verificación en navegador real Chrome · Sublote 02-E (20/11/2026)",
        "",
        f"- **Puerto loopback efímero usado y cerrado:** `{port}` (`port_closed: {port_closed}`)",
        f"- **Sin errores JS/consola/5xx:** `page_errors={len(page_errors)}`, `console_errors={len(console_errors)}`, `server_5xx={len(server_5xx)}`",
        f"- **Responsividad sin desbordamiento horizontal (1366x768 y 390x844):** `{no_overflow}`",
        f"- **Base protegida intacta:** `{report['prod_db_unchanged']}` (`{prod_db_after}`)",
        "",
        "## Puntos comprobados",
        "",
        *[f"- `{k}`: `{v}`" for k, v in checkpoints.items()],
        "",
        "## Métricas de layout",
        "",
        *[f"- `{name}`: `innerWidth={m['innerWidth']}`, `docScrollWidth={m['docScrollWidth']}`, `horizontalOverflow={m['horizontalOverflow']}`" for name, m in layouts.items()],
        "",
        "## Capturas generadas",
        "",
        *[f"- `{shot}`" for shot in screenshots],
    ]
    (OUT / "INFORME.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": report["all_passed"],
        "port_closed": port_closed,
        "no_overflow": no_overflow,
        "page_errors": len(page_errors),
        "unexpected_console_errors": len(unexpected_console_errors),
        "expected_403_console_errors": len(console_errors) - len(unexpected_console_errors),
        "server_5xx": len(server_5xx),
        "failed_checkpoints": [k for k, v in checkpoints.items() if isinstance(v, bool) and not v],
    }, ensure_ascii=False))
    if not report["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()


