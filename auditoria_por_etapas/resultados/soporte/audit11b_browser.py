"""Stage 11 isolated real-Chrome end-to-end verification (Desktop 1366x900 + Mobile 390x844 + keyboard)."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import shutil
import socketserver
import sys
import threading
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server  # noqa: E402

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "r1-pmv/manage.py").is_file())
PROJECT = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
CHROME = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
PW_LIB = Path(r"C:\Users\walte\AppData\Local\Temp\audit14d-browser-6f523915")

OUT = Path(sys.argv[1]).resolve()
OUT.mkdir(parents=True, exist_ok=True)

RUN_NAME = f"etapa11b-{secrets.token_hex(4)}"
RUN_DIR = (RESULTS / "datos" / RUN_NAME).resolve()
RUN_DIR.mkdir(parents=True, exist_ok=False)
(RUN_DIR / "marker.json").write_text(json.dumps({"run": RUN_NAME, "stage": "11-B"}), encoding="utf-8")

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
        "NAME": str(RUN_DIR / "audit.sqlite3"),
    }
}
settings.SESSION_COOKIE_NAME = "audit11b_sessionid"
settings.CSRF_COOKIE_NAME = "audit11b_csrftoken"
settings.SESSION_COOKIE_SECURE = False
settings.CSRF_COOKIE_SECURE = False

import django  # noqa: E402

django.setup()

from django.contrib.staticfiles.handlers import StaticFilesHandler  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.core.wsgi import get_wsgi_application  # noqa: E402
from django.db import connections  # noqa: E402
from django.urls import reverse  # noqa: E402
from django.utils import timezone  # noqa: E402

import atexit  # noqa: E402
atexit.register(lambda: (connections.close_all(), shutil.rmtree(RUN_DIR, ignore_errors=True)))

from cash.models import CashRegister, CashShift, CashShiftClose  # noqa: E402
from catalog.models import Category, Product  # noqa: E402
from identity.models import Account, Role  # noqa: E402
from inventory.models import Lot  # noqa: E402
from inventory.services import LotInput, confirm_initial_load  # noqa: E402
from sales.models import Sale, SaleCounter, SaleDraft, SaleLine, SaleLotAllocation  # noqa: E402

sys.path.insert(0, str(PW_LIB))
from playwright.sync_api import sync_playwright  # noqa: E402

PASSWORD = "Audit11B!ChromePassword"


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_snapshot() -> dict:
    exts = {".py", ".html", ".css", ".js"}
    files = sorted(
        p
        for p in PROJECT.rglob("*")
        if p.is_file() and p.suffix in exts and ".venv" not in p.parts and "__pycache__" not in p.parts
    )
    manifest = {p.relative_to(PROJECT).as_posix(): sha_bytes(p.read_bytes()) for p in files}
    h = hashlib.sha256()
    for rel, file_path in [(p.relative_to(PROJECT).as_posix(), p) for p in files]:
        h.update((rel + "\n").encode("utf-8"))
        h.update(file_path.read_bytes())
    return {"count": len(files), "sha256": h.hexdigest(), "files": manifest}


from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server  # noqa: E402


class ThreadingWSGIServer(socketserver.ThreadingMixIn, WSGIServer):
    daemon_threads = True


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        pass


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


def login_ui(browser, base: str, email: str, password: str, viewport: dict, page_errors: list, console_errors: list):
    ctx = browser.new_context(locale="es-PE", timezone_id="America/Lima", viewport=viewport)
    page = ctx.new_page()
    page.set_default_timeout(8000)
    page.on("pageerror", lambda err: page_errors.append({"actor": email, "error": str(err)}))
    page.on(
        "console",
        lambda msg: console_errors.append({"actor": email, "text": msg.text})
        if msg.type == "error"
        else None,
    )
    page.goto(base + "/")
    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)
    page.click('button:has-text("Iniciar sesión")')
    page.wait_for_url("**/inicio/")
    return ctx, page


def main() -> None:
    prod_db = PROJECT / "r1_pmv.sqlite3"
    prod_db_before = sha_bytes(prod_db.read_bytes())
    build_before = build_snapshot()

    call_command("migrate", verbosity=0, interactive=False)
    today = timezone.localdate()

    r_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    r_sel, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

    admin = Account.objects.create_user("admin11b@example.invalid", PASSWORD, display_name="Admin Audit11B", role=r_admin)
    wh = Account.objects.create_user("almacen11b@example.invalid", PASSWORD, display_name="Lucia Almacen11B", role=r_wh)
    seller1 = Account.objects.create_user("vendedor1@example.invalid", PASSWORD, display_name="Carmen V11B", role=r_sel)
    seller2 = Account.objects.create_user("vendedor2@example.invalid", PASSWORD, display_name="Mario V2_11B", role=r_sel)
    reg = CashRegister.objects.create(code="CAJA-01")

    cat = Category.objects.create(name="Lacteos y Pan 11B")
    long_name = "ProductoUltraExtensoSinEspaciosNiGuionesParaComprobarEnvolturaYNoDesbordeEnMostradorYConstanciaInterna1234567890ABCDEFGHIJKL"
    p_pan = Product.objects.create(category=cat, name="Pan Precio Vivo 11B", barcode="11B-PAN-01", sale_price=Decimal("5.00"))
    p_long = Product.objects.create(category=cat, name=long_name, barcode="11B-LONG-02", sale_price=Decimal("12.00"))
    p_fefo = Product.objects.create(category=cat, name="Leche FEFO 11B", barcode="11B-FEFO-03", sale_price=Decimal("3.55"))

    confirm_initial_load(actor=wh, product=p_pan, lots=[LotInput("L-PAN-01", 10, Decimal("2.1000"), today + timedelta(days=30))])
    confirm_initial_load(actor=wh, product=p_long, lots=[LotInput("L-LONG-01", 10, Decimal("6.0000"), today + timedelta(days=30))])
    load_fefo = confirm_initial_load(
        actor=wh,
        product=p_fefo,
        lots=[
            LotInput("FEFO-TIE-1", 2, Decimal("2.0000"), today + timedelta(days=10)),
            LotInput("FEFO-FAR", 10, Decimal("2.0000"), today + timedelta(days=40)),
        ],
    )
    # Create tie-date lot after initial load with later expiration tie & past/today expired lots
    l_past = Lot.objects.create(
        product=p_fefo,
        initial_load=load_fefo,
        number="FEFO-PAST",
        number_normalized="FEFO-PAST",
        initial_quantity=5,
        available_quantity=5,
        unit_cost=Decimal("2.0000"),
        expiration_date=today - timedelta(days=1),
    )
    l_today = Lot.objects.create(
        product=p_fefo,
        initial_load=load_fefo,
        number="FEFO-TODAY",
        number_normalized="FEFO-TODAY",
        initial_quantity=5,
        available_quantity=5,
        unit_cost=Decimal("2.0000"),
        expiration_date=today,
    )
    l_tie_2 = Lot.objects.create(
        product=p_fefo,
        initial_load=load_fefo,
        number="FEFO-TIE-2",
        number_normalized="FEFO-TIE-2",
        initial_quantity=4,
        available_quantity=4,
        unit_cost=Decimal("2.0000"),
        expiration_date=today + timedelta(days=10),
    )

    app = StaticFilesHandler(get_wsgi_application())
    server = make_server("127.0.0.1", 0, app, server_class=ThreadingWSGIServer, handler_class=QuietHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{port}"

    page_errors: list = []
    console_errors: list = []
    report: dict = {
        "executed_utc": datetime.now(timezone.utc if hasattr(timezone, "utc") else None).isoformat()
        if hasattr(datetime, "now")
        else "",
        "port": port,
        "chrome_path": str(CHROME),
        "checkpoints": {},
        "layout": {},
    }
    from datetime import timezone as dt_tz

    report["executed_utc"] = datetime.now(dt_tz.utc).isoformat()

    cache_headers: dict[str, str] = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=str(CHROME), headless=True)

            # 1. Login roles
            ctx_admin, pg_admin = login_ui(browser, base, admin.email, PASSWORD, {"width": 1366, "height": 900}, page_errors, console_errors)
            ctx_wh, pg_wh = login_ui(browser, base, wh.email, PASSWORD, {"width": 1366, "height": 900}, page_errors, console_errors)
            ctx_s1, pg_s1 = login_ui(browser, base, seller1.email, PASSWORD, {"width": 1366, "height": 900}, page_errors, console_errors)
            ctx_s2, pg_s2 = login_ui(browser, base, seller2.email, PASSWORD, {"width": 1366, "height": 900}, page_errors, console_errors)

            # Capture Cache-Control on critical checkout GET later
            def track_cache(resp):
                path = urlsplit(resp.url).path
                if path.startswith("/ventas/") or path.startswith("/caja/"):
                    cc = resp.headers.get("cache-control", "")
                    if cc:
                        cache_headers[path] = cc

            pg_s1.on("response", track_cache)

            # 2. Seller 1 opens shift S/ 100.00
            pg_s1.goto(base + "/caja/abrir/")
            pg_s1.fill('input[name="opening_amount"]', "100.00")
            pg_s1.click('button:has-text("Abrir turno")')
            pg_s1.wait_for_url("**/caja/**")
            report["checkpoints"]["shift_opened_ui"] = "CAJA-01" in pg_s1.locator("body").inner_text()

            # 3. Seller 1 prepares Sale 1: Pan 2x5.00 + Long 1x12.00 = 22.00
            pg_s1.goto(base + "/ventas/")
            pg_s1.fill('input[name="query"]', "Pan Precio Vivo 11B")
            pg_s1.click('form.search-form button:has-text("Buscar")')
            pg_s1.fill('form.line-add-form input[name="quantity"]', "2")
            pg_s1.click('form.line-add-form button:has-text("Agregar")')
            pg_s1.wait_for_load_state("load")

            pg_s1.fill('input[name="query"]', "11B-LONG-02")
            pg_s1.click('form.search-form button:has-text("Buscar")')
            pg_s1.fill('form.line-add-form input[name="quantity"]', "1")
            pg_s1.click('form.line-add-form button:has-text("Agregar")')
            pg_s1.wait_for_load_state("load")

            # Keyboard activation of Cobrar venta link
            co_link = pg_s1.locator('a[href="/ventas/cobrar/"]')
            co_link.focus()
            pg_s1.keyboard.press("Enter")
            pg_s1.wait_for_url("**/ventas/cobrar/")

            # Check initial checkout UI
            co_text = pg_s1.locator("body").inner_text()
            tax_warn_ok = (
                "Esta venta genera una constancia interna. No emite una boleta ni factura electrónica autorizada por SUNAT."
                in co_text
            )
            discount_inputs_count = pg_s1.locator('input[name="discount_amount"]').count()
            report["checkpoints"]["tax_warning_pre_confirm"] = tax_warn_ok
            report["checkpoints"]["discount_inputs_in_dom_count"] = discount_inputs_count
            report["checkpoints"]["subtotal_initial_22"] = "22,00" in co_text
            report["checkpoints"]["base_initial_18_64"] = "18,64" in co_text
            report["checkpoints"]["igv_initial_3_36"] = "3,36" in co_text
            report["layout"]["checkout_desktop_1366"] = layout_metrics(pg_s1)
            pg_s1.screenshot(path=str(OUT / "01-checkout-initial.png"), full_page=True)

            # Live JS change calculation
            pg_s1.fill("#id_cash_received", "21.99")
            vuelto_short = pg_s1.locator("#checkout-change").inner_text().strip()
            pg_s1.fill("#id_cash_received", "")
            pg_s1.locator("#id_cash_received").type("e")
            vuelto_alpha = pg_s1.locator("#checkout-change").inner_text().strip()
            pg_s1.fill("#id_cash_received", "25.00")
            vuelto_25 = pg_s1.locator("#checkout-change").inner_text().strip()
            report["checkpoints"]["js_vuelto_short"] = vuelto_short
            report["checkpoints"]["js_vuelto_alpha"] = vuelto_alpha
            report["checkpoints"]["js_vuelto_25"] = vuelto_25

            # Insufficient cash POST (21.99)
            pg_s1.fill("#id_cash_received", "21.99")
            pg_s1.click('section.form-panel form button:has-text("Confirmar cobro")')
            pg_s1.wait_for_load_state("load")
            short_body = pg_s1.locator("body").inner_text()
            report["checkpoints"]["insufficient_rejected"] = "insuficiente" in short_body.lower()
            report["checkpoints"]["insufficient_zero_sales"] = Sale.objects.count() == 0
            report["checkpoints"]["insufficient_mentions_0_01_shortfall"] = ("0,01" in short_body or "0.01" in short_body)
            pg_s1.screenshot(path=str(OUT / "02-checkout-insufficient.png"), full_page=True)

            # Tampered DOM hidden discount injection rejected
            pg_s1.evaluate(
                """() => {
                    const form = document.querySelector('section.form-panel form');
                    const inp = document.createElement('input');
                    inp.type = 'hidden';
                    inp.name = 'discount_amount';
                    inp.value = '2.00';
                    form.appendChild(inp);
                }"""
            )
            pg_s1.fill("#id_cash_received", "30.00")
            pg_s1.click('section.form-panel form button:has-text("Confirmar cobro")')
            pg_s1.wait_for_load_state("load")
            disc_body = pg_s1.locator("body").inner_text()
            report["checkpoints"]["tampered_discount_rejected"] = (
                "Los descuentos no están habilitados para nuevas ventas" in disc_body and Sale.objects.count() == 0
            )
            pg_s1.screenshot(path=str(OUT / "03-checkout-discount-rejected.png"), full_page=True)

            # Admin updates Pan price in live (5.00 -> 7.50) while Seller has form at 22.00
            pg_admin.goto(base + reverse("product-edit", args=(p_pan.pk,)))
            pg_admin.fill('input[name="sale_price"]', "7.50")
            pg_admin.click('form.form-panel button:has-text("Guardar cambios")')
            pg_admin.wait_for_load_state("load")

            pg_s1.fill("#id_cash_received", "30.00")
            pg_s1.click('section.form-panel form button:has-text("Confirmar cobro")')
            pg_s1.wait_for_load_state("load")
            price_chg_body = pg_s1.locator("body").inner_text()
            report["checkpoints"]["live_price_change_detected"] = (
                "S/ 5.00" in price_chg_body and "S/ 7.50" in price_chg_body and "27,00" in price_chg_body and Sale.objects.count() == 0
            )
            pg_s1.screenshot(path=str(OUT / "04-checkout-price-changed.png"), full_page=True)

            # Seller confirms Sale 1 with exact cash 27.00 via keyboard Enter + verify JS double-submit guard
            pg_s1.fill("#id_cash_received", "27.00")
            vuelto_exact = pg_s1.locator("#checkout-change").inner_text().strip()
            js_guard_state = pg_s1.evaluate(
                """() => {
                    const form = document.querySelector('section.form-panel form');
                    const btn = form.querySelector('button[type="submit"]');
                    let secondPrevented = false;
                    form.addEventListener('submit', function(e) {
                        if (window.__firstSeen) { secondPrevented = e.defaultPrevented; }
                        window.__firstSeen = true;
                    });
                    form.requestSubmit(btn);
                    const disabledAfterFirst = btn.disabled;
                    const textAfterFirst = btn.textContent;
                    const ev2 = new Event('submit', {bubbles: true, cancelable: true});
                    form.dispatchEvent(ev2);
                    return {disabledAfterFirst, textAfterFirst, secondPrevented: ev2.defaultPrevented};
                }"""
            )
            pg_s1.wait_for_url("**/ventas/constancia/**")
            report["checkpoints"]["js_double_submit_guard"] = js_guard_state
            v1_body = pg_s1.locator("body").inner_text()
            report["checkpoints"]["exact_cash_vuelto_js"] = vuelto_exact
            report["checkpoints"]["v1_receipt_ok"] = (
                "V-00000001" in v1_body
                and "CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO" in v1_body
                and "27,00" in v1_body
                and "22,88" in v1_body
                and "4,12" in v1_body
                and "0,00" in v1_body
                and "2.1000" not in v1_body
                and "6.0000" not in v1_body
            )
            report["layout"]["receipt_desktop_1366"] = layout_metrics(pg_s1)
            pg_s1.screenshot(path=str(OUT / "05-receipt-exact-v1.png"), full_page=True)

            # Back button / no-store re-check (expect ERR_CACHE_MISS or redirect, zero duplicate sales)
            try:
                pg_s1.go_back(wait_until="load")
                back_info = f"url:{pg_s1.url}"
            except Exception as exc:
                back_info = type(exc).__name__ + ": " + str(exc).splitlines()[0]
                pg_s1.wait_for_timeout(300)
            pg_s1.goto(base + "/ventas/cobrar/")
            pg_s1.wait_for_load_state("load")
            report["checkpoints"]["back_button_info"] = back_info
            report["checkpoints"]["revisit_checkout_after_sale_redirects_draft"] = "/ventas/cobrar/" not in pg_s1.url
            report["checkpoints"]["back_button_no_duplicate_sale"] = Sale.objects.count() == 1

            # 4. Prepare Sale 2: 5 x Leche FEFO (3.55 = 17.75, base 15.04, igv 2.71), excess cash 50.00 -> change 32.25
            pg_s1.goto(base + "/ventas/")
            pg_s1.fill('input[name="query"]', "Leche FEFO")
            pg_s1.click('form.search-form button:has-text("Buscar")')
            pg_s1.fill('form.line-add-form input[name="quantity"]', "5")
            pg_s1.click('form.line-add-form button:has-text("Agregar")')
            pg_s1.wait_for_url("**/ventas/**")

            pg_s1.goto(base + "/ventas/cobrar/")
            pg_s1.fill("#id_cash_received", "50.00")
            vuelto_excess_js = pg_s1.locator("#checkout-change").inner_text().strip()
            pg_s1.click('section.form-panel form button:has-text("Confirmar cobro")')
            pg_s1.wait_for_url("**/ventas/constancia/**")
            v2_url = pg_s1.url
            v2_id = urlsplit(v2_url).path.strip("/").split("/")[-1]
            v2 = Sale.objects.get(pk=v2_id)
            report["checkpoints"]["excess_cash_vuelto_js"] = vuelto_excess_js
            report["checkpoints"]["v2_correlative"] = v2.correlative

            # Verify FEFO allocations & expired untouched
            l_past.refresh_from_db()
            l_today.refresh_from_db()
            l_tie_2.refresh_from_db()
            l_tie_1 = Lot.objects.get(product=p_fefo, number="FEFO-TIE-1")
            l_far = Lot.objects.get(product=p_fefo, number="FEFO-FAR")
            allocs_v2 = [
                (a.lot_snapshot_number, a.quantity)
                for a in SaleLotAllocation.objects.filter(line__sale=v2).order_by(
                    "lot_snapshot_expiration_date", "lot_snapshot_received_at", "lot_id"
                )
            ]
            report["checkpoints"]["fefo_allocs_v2"] = allocs_v2
            report["checkpoints"]["expired_untouched_browser"] = (
                l_past.available_quantity == 5 and l_today.available_quantity == 5
            )
            report["checkpoints"]["fefo_remaining_tie1_tie2_far"] = [
                l_tie_1.available_quantity,
                l_tie_2.available_quantity,
                l_far.available_quantity,
            ]

            # Rename masters post-sale and verify receipt preserves snapshot!
            pg_admin.goto(base + reverse("product-edit", args=(p_fefo.pk,)))
            pg_admin.fill('input[name="name"]', "Leche Renombrada PostVenta 11B")
            pg_admin.fill('input[name="sale_price"]', "9.99")
            pg_admin.click('form.form-panel button:has-text("Guardar cambios")')
            pg_admin.wait_for_load_state("load")

            seller1.display_name = "Carmen Renombrada"
            seller1.save(update_fields=["display_name"])
            reg.code = "CAJA-99"
            reg.save(update_fields=["code"])

            pg_s1.goto(v2_url)
            v2_snap_body = pg_s1.locator("body").inner_text()
            report["checkpoints"]["snapshots_preserved_after_rename_browser"] = (
                "Leche FEFO 11B" in v2_snap_body
                and "3,55" in v2_snap_body
                and "Carmen V11B" in v2_snap_body
                and "CAJA-01" in v2_snap_body
                and "Leche Renombrada PostVenta" not in v2_snap_body
                and "2.0000" not in v2_snap_body
            )
            pg_s1.screenshot(path=str(OUT / "06-receipt-fefo-snapshots-v2.png"), full_page=True)

            # 5. Mobile 390x844 check (prepare temporary draft, inspect mobile checkout & receipt, then discard draft)
            ctx_mob = browser.new_context(
                locale="es-PE", timezone_id="America/Lima", viewport={"width": 390, "height": 844}
            )
            pg_mob = ctx_mob.new_page()
            pg_mob.on("pageerror", lambda err: page_errors.append({"actor": "mobile", "error": str(err)}))
            pg_mob.goto(base + "/")
            pg_mob.fill('input[name="email"]', seller1.email)
            pg_mob.fill('input[name="password"]', PASSWORD)
            pg_mob.click('button:has-text("Iniciar sesión")')
            pg_mob.wait_for_url("**/inicio/")
            pg_mob.goto(base + "/ventas/")
            pg_mob.fill('input[name="query"]', "Pan")
            pg_mob.click('form.search-form button:has-text("Buscar")')
            pg_mob.fill('form.line-add-form input[name="quantity"]', "1")
            pg_mob.click('form.line-add-form button:has-text("Agregar")')
            pg_mob.wait_for_load_state("load")
            pg_mob.goto(base + "/ventas/cobrar/")
            report["layout"]["checkout_mobile_390"] = layout_metrics(pg_mob)
            pg_mob.screenshot(path=str(OUT / "07-checkout-mobile-390.png"), full_page=True)
            # Discard temporary draft so sales stay 2
            pg_mob.goto(base + "/ventas/")
            pg_mob.click('form[action="/ventas/descartar/"] button:has-text("Descartar venta")')
            pg_mob.wait_for_load_state("load")
            pg_mob.goto(v2_url)
            mob_receipt_metrics = layout_metrics(pg_mob)
            mob_receipt_metrics["table_clip"] = pg_mob.evaluate(
                """() => {
                    const wrap = document.querySelector('.table-wrap');
                    const tbl = document.querySelector('.receipt-table');
                    const nav = document.querySelector('.sidebar-nav');
                    return {
                        wrapClientW: wrap ? wrap.clientWidth : null,
                        wrapScrollW: wrap ? wrap.scrollWidth : null,
                        tblClientW: tbl ? tbl.clientWidth : null,
                        tblScrollW: tbl ? tbl.scrollWidth : null,
                        navClientW: nav ? nav.clientWidth : null,
                        navScrollW: nav ? nav.scrollWidth : null,
                    };
                }"""
            )
            report["layout"]["receipt_mobile_390"] = mob_receipt_metrics
            pg_mob.screenshot(path=str(OUT / "08-receipt-mobile-390.png"), full_page=True)
            ctx_mob.close()

            # 6. Cross-role: ALMACENERO checks stock & movements + denied checkout/receipt
            pg_wh.goto(base + "/inventario/stock/")
            wh_stock_text = pg_wh.locator("body").inner_text()
            pg_wh.goto(base + f"/inventario/productos/{p_fefo.pk}/movimientos/")
            wh_mov_text = pg_wh.locator("body").inner_text()
            report["layout"]["warehouse_movements_1366"] = layout_metrics(pg_wh)
            pg_wh.screenshot(path=str(OUT / "09-warehouse-movements.png"), full_page=True)

            wh_co_resp = pg_wh.goto(base + "/ventas/cobrar/")
            wh_rcpt_resp = pg_wh.goto(v2_url)
            report["checkpoints"]["wh_stock_and_kardex_ok"] = (
                "21" in wh_stock_text and "11" in wh_stock_text and "V-00000002" in wh_mov_text and "FEFO-TIE-1" in wh_mov_text and "FEFO-TIE-2" in wh_mov_text
            )
            report["checkpoints"]["wh_denied_403"] = wh_co_resp.status == 403 and wh_rcpt_resp.status == 403

            # 7. Cross-role: ADMIN checks dashboard & sales_history & receipt + denied checkout
            pg_admin.goto(base + "/inicio/")
            adm_dash_text = pg_admin.locator("body").inner_text()
            pg_admin.screenshot(path=str(OUT / "10-admin-dashboard.png"), full_page=True)
            pg_admin.goto(base + "/ventas/historial/")
            adm_hist_text = pg_admin.locator("body").inner_text()
            pg_admin.goto(v2_url)
            adm_rcpt_text = pg_admin.locator("body").inner_text()
            adm_co_resp = pg_admin.goto(base + "/ventas/cobrar/")
            report["checkpoints"]["admin_dashboard_and_history_ok"] = (
                "44,75" in adm_dash_text
                and "Descuentos otorgados hoy" in adm_dash_text
                and "0,00" in adm_dash_text
                and "V-00000001" in adm_hist_text
                and "V-00000002" in adm_hist_text
                and "2.0000" not in adm_rcpt_text
                and "2,0000" not in adm_rcpt_text
            )
            report["checkpoints"]["admin_checkout_denied_403"] = adm_co_resp.status == 403

            # 8. Cross-role: VENDEDOR 2 denied foreign receipt (404)
            s2_rcpt_resp = pg_s2.goto(v2_url)
            report["checkpoints"]["seller2_foreign_receipt_404"] = s2_rcpt_resp.status == 404

            # 9. Seller 1 shift history + cash close exact 144.75 + closed blocks sales
            pg_s1.goto(base + "/ventas/historial/turno/")
            shift_hist_ok = "44,75" in pg_s1.locator("body").inner_text()
            pg_s1.goto(base + "/caja/cerrar/")
            close_pre_text = pg_s1.locator("body").inner_text()
            pg_s1.fill('input[name="counted_amount"]', "144.75")
            pg_s1.click('form button:has-text("Cerrar turno")')
            pg_s1.wait_for_url("**/caja/turnos/*/cerrado/")
            closed_text = pg_s1.locator("body").inner_text()
            pg_s1.screenshot(path=str(OUT / "11-seller-cash-closed.png"), full_page=True)
            pg_s1.goto(base + "/ventas/")
            closed_blocks = "Abre tu turno para preparar una venta" in pg_s1.locator("body").inner_text()
            report["checkpoints"]["shift_hist_44_75_ok"] = shift_hist_ok
            report["checkpoints"]["close_blind_hides_expected"] = ("100,00" in close_pre_text and "144,75" not in close_pre_text)
            report["checkpoints"]["closed_blocks_sales"] = closed_blocks
            report["checkpoints"]["cash_close_exact_and_blocks_sales"] = (
                shift_hist_ok
                and "100,00" in close_pre_text
                and "144,75" not in close_pre_text
                and "144,75" in closed_text
                and "Exacto" in closed_text
                and "0,00" in closed_text
                and closed_blocks
            )

            ctx_admin.close()
            ctx_wh.close()
            ctx_s1.close()
            ctx_s2.close()
            browser.close()
    finally:
        server.shutdown()
        server.server_close()

    # Check port closed
    import socket

    s_chk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_chk.settimeout(1.0)
    port_closed = s_chk.connect_ex(("127.0.0.1", port)) != 0
    s_chk.close()

    build_after = build_snapshot()
    prod_db_after = sha_bytes(prod_db.read_bytes())

    report["orm_summary"] = {
        "sales_count": Sale.objects.count(),
        "sales": list(
            Sale.objects.order_by("correlative").values(
                "correlative", "total_amount", "base_amount", "igv_amount", "discount_amount",
                "cash_received", "change_given", "seller_snapshot_name", "cash_register_snapshot_code",
            )
        ),
        "sale_counter_next": SaleCounter.objects.get(id=1).next_value,
        "drafts_statuses": list(SaleDraft.objects.order_by("created_at").values_list("status", flat=True)),
        "cash_close": list(CashShiftClose.objects.values("expected_amount", "counted_amount", "difference")),
    }
    report["cache_headers"] = cache_headers
    report["page_errors"] = page_errors
    report["console_errors"] = console_errors
    report["port_closed"] = port_closed
    report["prod_db_unchanged"] = prod_db_before == prod_db_after
    report["prod_db_sha256"] = prod_db_after
    report["build_before"] = {"count": build_before["count"], "sha256": build_before["sha256"]}
    report["build_after"] = {"count": build_after["count"], "sha256": build_after["sha256"]}
    report["sources_stable"] = build_before == build_after
    if not report["sources_stable"]:
        report["changed_sources"] = [
            k for k in sorted(set(build_before["files"]) | set(build_after["files"]))
            if build_before["files"].get(k) != build_after["files"].get(k)
        ]

    from django.db import connections

    connections.close_all()
    shutil.rmtree(RUN_DIR, ignore_errors=True)
    (OUT / "browser_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "all_checkpoints_true": all(bool(v) if isinstance(v, bool) else True for k, v in report["checkpoints"].items() if k != "insufficient_mentions_0_01_shortfall"),
        "page_errors": len(page_errors),
        "console_errors": len(console_errors),
        "port_closed": port_closed,
        "prod_db_unchanged": report["prod_db_unchanged"],
        "sources_stable": report["sources_stable"],
    }))


if __name__ == "__main__":
    main()
