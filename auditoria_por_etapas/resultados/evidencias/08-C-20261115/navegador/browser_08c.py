import hashlib
import json
import os
import sys
import tempfile
import threading
import time
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from wsgiref.simple_server import make_server

ROOT = Path(__file__).resolve().parents[5]
R1 = ROOT / "r1-pmv"
sys.path.insert(0, str(R1))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

tmp_dir = Path(tempfile.mkdtemp(prefix="audit08c_browser_"))

import django
django.setup()

from django.conf import settings
settings.DATABASES["default"] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": str(tmp_dir / "browser08c.sqlite3"),
    "ATOMIC_REQUESTS": False,
    "AUTOCOMMIT": True,
    "CONN_MAX_AGE": 0,
    "OPTIONS": {"timeout": 20},
    "TIME_ZONE": None,
    "USER": "",
    "PASSWORD": "",
    "HOST": "",
    "PORT": "",
    "TEST": {"CHARSET": None, "COLLATION": None, "MIRROR": None, "NAME": None},
}
settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
settings.DEBUG = True

from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from django.utils import timezone

call_command("migrate", verbosity=0)

from catalog.models import Category, Product
from cash.models import CashRegister, CashShift
from identity.models import Account, Role
from inventory.models import PhysicalAdjustment, StockWriteOff, Supplier
from inventory.services import LotInput, confirm_initial_load, register_physical_adjustment, register_stock_entry, write_off_stock
from sales.models import SaleDraft
from sales.services import add_product_to_draft, checkout_sale

from playwright.sync_api import sync_playwright

r_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
r_sel, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

Account.objects.create_user(email="admin08c@local.test", password="Password123!", display_name="Admin 08C", role=r_admin, is_active=True)
u_wh = Account.objects.create_user(email="alma08c@local.test", password="Password123!", display_name="Almacenero 08C", role=r_wh, is_active=True)
u_sel = Account.objects.create_user(email="vend08c@local.test", password="Password123!", display_name="Vendedor 08C", role=r_sel, is_active=True)

cat = Category.objects.create(name="Bebidas 08C")
cat_inact = Category.objects.create(name="Inactiva 08C", is_active=True)
prod_act = Product.objects.create(name="Agua Mineral 08C", barcode="7750000000811", category=cat, unit=Product.Unit.UNIT, sale_price=Decimal("3.00"), minimum_stock=5, is_active=True)
prod_q0 = Product.objects.create(name="Producto Vacio 08C", barcode="7750000000812", category=cat, unit=Product.Unit.UNIT, sale_price=Decimal("6.00"), minimum_stock=2, is_active=True)
prod_inact = Product.objects.create(name="Producto Desactivado 08C", barcode="7750000000813", category=cat_inact, unit=Product.Unit.UNIT, sale_price=Decimal("4.50"), minimum_stock=1, is_active=True)
sup = Supplier.objects.create(name="Distribuidora 08C SAC", ruc="20600000811", phone="999000811")

today = timezone.localdate()
load = confirm_initial_load(actor=u_wh, product=prod_act, lots=[LotInput(number="L-B08C-1", quantity=100, unit_cost=Decimal("1.5000"), expiration_date=today + timedelta(days=90))], supplier=sup)
lot_act = load.lines.first().lot
register_stock_entry(actor=u_wh, product=prod_act, lots=[LotInput(number="L-B08C-2", quantity=50, unit_cost=Decimal("1.6000"), expiration_date=today + timedelta(days=120))], supplier=sup)
confirm_initial_load(actor=u_wh, product=prod_inact, lots=[LotInput(number="L-INACT-08C", quantity=10, unit_cost=Decimal("2.0000"), expiration_date=today + timedelta(days=45))], supplier=sup)
prod_inact.is_active = False
prod_inact.save(update_fields=["is_active"])
cat_inact.is_active = False
cat_inact.save(update_fields=["is_active"])

confirm_initial_load(actor=u_wh, product=prod_q0, lots=[LotInput(number="L-EMPTY-1", quantity=2, unit_cost=Decimal("2.0000"), expiration_date=today + timedelta(days=30))], supplier=sup)
write_off_stock(actor=u_wh, lot=prod_q0.lots.first(), quantity=2, reason=StockWriteOff.Reason.THEFT, notes="Vaciar para ajuste Q=0")

reg = CashRegister.objects.create(name="CAJA-B08C")
shift = CashShift.objects.create(cash_register=reg, seller=u_sel, opening_amount=Decimal("50.00"), status=CashShift.Status.OPEN)
for i in range(25):
    d = add_product_to_draft(actor=u_sel, product_id=prod_act.pk, quantity=1)
    checkout_sale(actor=u_sel, draft_id=d.pk, cash_received=Decimal("3.00"), idempotency_key=uuid.uuid4())

u_admin = Account.objects.get(email="admin08c@local.test")
adj_seed = register_physical_adjustment(actor=u_admin, lot=lot_act, delta=2, reason="Conteo semilla 08C", idempotency_key=uuid.uuid4())
wo_seed = write_off_stock(actor=u_wh, lot=lot_act, quantity=1, reason=StockWriteOff.Reason.THEFT, notes="Merma semilla 08C", idempotency_key=uuid.uuid4())

wsgi_app = StaticFilesHandler(get_wsgi_application())
server = make_server("127.0.0.1", 0, wsgi_app)
port = server.server_port
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
base_url = f"http://127.0.0.1:{port}"
OUT_DIR = Path(__file__).parent


def login_as(page, email):
    page.goto(f"{base_url}/", wait_until="networkidle")
    page.fill('input[name="username"], input[name="email"]', email)
    page.fill('input[name="password"]', "Password123!")
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")


def inspect_a11y_and_layout(page):
    return page.evaluate("""() => {
        const vw = window.innerWidth;
        const docSw = document.documentElement.scrollWidth;
        const bodySw = document.body.scrollWidth;
        const skipLink = document.querySelector('a.skip-link');
        const h1 = document.querySelector('h1');
        const h2 = document.querySelector('h2');
        const ths = Array.from(document.querySelectorAll('table th')).map(th => ({
            text: th.textContent.trim(),
            scope: th.getAttribute('scope'),
            empty: th.textContent.trim().length === 0,
        }));
        const captions = Array.from(document.querySelectorAll('table')).map(t => Boolean(t.querySelector('caption')));
        const controls = Array.from(document.querySelectorAll('input:not([type="hidden"]), select, textarea')).map(el => {
            const id = el.id;
            const lbl = id ? document.querySelector(`label[for="${CSS.escape(id)}"]`) : null;
            return {name: el.name, id, hasLabel: Boolean(lbl), labelText: lbl ? lbl.textContent.trim() : null};
        });
        const tableWraps = Array.from(document.querySelectorAll('.table-wrap, .table-responsive')).map(w => {
            const r = w.getBoundingClientRect();
            const tbl = w.querySelector('table');
            const tblW = tbl ? tbl.getBoundingClientRect().width : 0;
            return {
                className: w.className,
                clientWidth: w.clientWidth,
                scrollWidth: w.scrollWidth,
                tableWidth: Math.round(tblW),
                horizontallyClipped: w.scrollWidth > w.clientWidth + 1,
                tabindex: w.getAttribute('tabindex'),
                role: w.getAttribute('role'),
                ariaLabel: w.getAttribute('aria-label'),
            };
        });
        const sidebarNav = document.querySelector('.sidebar-nav');
        const navRect = sidebarNav ? sidebarNav.getBoundingClientRect() : null;
        const navOverflow = sidebarNav ? (sidebarNav.scrollWidth > vw + 1) : false;
        const clippedButtons = Array.from(document.querySelectorAll('a.button, button, a.btn')).filter(el => {
            const r = el.getBoundingClientRect();
            return r.width > 0 && (r.right > vw + 1 || r.left < -1);
        }).map(el => ({text: el.textContent.trim(), right: Math.round(el.getBoundingClientRect().right), vw}));
        const summaryItems = Array.from(document.querySelectorAll('.summary-list > div')).map(div => {
            const dt = div.querySelector('dt');
            const dd = div.querySelector('dd');
            if (!dt || !dd) return null;
            const dr = dt.getBoundingClientRect();
            const ddr = dd.getBoundingClientRect();
            return {
                dt: dt.textContent.trim(),
                ddTopGeDtBottom: ddr.top >= dr.bottom - 2,
                ddRight: Math.round(ddr.right),
                overlapsVw: ddr.right > vw + 1,
            };
        }).filter(Boolean);
        return {
            viewportWidth: vw,
            docScrollWidth: docSw,
            bodyScrollWidth: bodySw,
            horizontalPageOverflow: docSw > vw + 1,
            hasSkipLink: Boolean(skipLink),
            topbarH1: h1 ? h1.textContent.trim() : null,
            contentH2: h2 ? h2.textContent.trim() : null,
            tableCount: captions.length,
            tablesWithCaption: captions.filter(Boolean).length,
            emptyThCount: ths.filter(x => x.empty).length,
            thsWithoutScope: ths.filter(x => !x.scope).length,
            unlabeledControls: controls.filter(c => !c.hasLabel),
            tableWraps,
            sidebarNavScrollWidth: sidebarNav ? sidebarNav.scrollWidth : null,
            sidebarNavOverflow: navOverflow,
            clippedButtons,
            summaryOverflowItems: summaryItems.filter(x => x.overlapsVw),
            summaryItemsCount: summaryItems.length,
        };
    }""")


def main():
    results = {
        "meta": {
            "stage": "08-C",
            "app_css_sha256": hashlib.sha256((R1 / "identity/static/identity/app.css").read_bytes()).hexdigest(),
        },
        "desktop_1366_a11y_and_flows": {},
        "mobile_390_post_appcss_audit": {},
        "errors": {"console": [], "pageerror": [], "http_5xx": []},
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        # 1. Desktop 1366x900: Almacenero keyboard + double-submit + a11y + focus
        ctx = browser.new_context(viewport={"width": 1366, "height": 900})
        page = ctx.new_page()
        page.on("console", lambda m: results["errors"]["console"].append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: results["errors"]["pageerror"].append(str(e)))
        page.on("response", lambda r: results["errors"]["http_5xx"].append(f"{r.status} {r.url}") if r.status >= 500 else None)

        login_as(page, "alma08c@local.test")

        # Keyboard Tab test on writeoff selector + selected lot form error focus
        page.goto(f"{base_url}/inventario/bajas/nueva/", wait_until="networkidle")
        results["desktop_1366_a11y_and_flows"]["writeoff_selector"] = inspect_a11y_and_layout(page)
        page.keyboard.press("Tab")
        first_focus = page.evaluate("() => document.activeElement ? document.activeElement.className + ':' + document.activeElement.textContent.trim() : null")
        results["desktop_1366_a11y_and_flows"]["first_tab_target"] = first_focus

        # Navigate to selected lot and submit invalid empty form -> check focus & error alert
        page.goto(f"{base_url}/inventario/bajas/nueva/?lote={lot_act.pk}", wait_until="networkidle")
        page.fill('input[name="quantity"]', "")
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        results["desktop_1366_a11y_and_flows"]["writeoff_error_state"] = {
            "has_writeoff_errors_box": page.locator("#writeoff-errors").count() > 0,
            "active_element_tag": page.evaluate("() => document.activeElement ? document.activeElement.tagName + '#' + (document.activeElement.id || '') : null"),
            "a11y": inspect_a11y_and_layout(page),
        }

        # Valid writeoff + back-button/resubmit idempotency test in real browser
        wo_count_before = StockWriteOff.objects.count()
        page.fill('input[name="quantity"]', "2")
        page.select_option('select[name="reason"]', "ROBO")
        page.fill('textarea[name="notes"]', "Prueba doble envio navegador 08C")
        idem_val = page.input_value('input[name="idempotency_key"]')
        page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")
        receipt_url = page.url
        results["desktop_1366_a11y_and_flows"]["writeoff_receipt"] = inspect_a11y_and_layout(page)

        # Go back and re-submit same cached form (same idempotency_key) -> should replay without creating a 2nd StockWriteOff
        page.go_back(wait_until="domcontentloaded")
        if page.locator('button[type="submit"]').count() > 0:
            idem_after_back = page.input_value('input[name="idempotency_key"]')
            page.click('button[type="submit"]')
            page.wait_for_load_state("networkidle")
            replay_flash = page.locator(".flash-stack").inner_text() if page.locator(".flash-stack").count() > 0 else ""
            replay_url = page.url
        else:
            idem_after_back = None
            replay_flash = ""
            replay_url = page.url
        wo_count_after = StockWriteOff.objects.count()
        results["desktop_1366_a11y_and_flows"]["browser_back_resubmit_idempotency"] = {
            "same_idempotency_key_on_back": idem_val == idem_after_back,
            "wo_count_delta": wo_count_after - wo_count_before,
            "same_receipt_url": receipt_url == replay_url,
            "replay_flash": replay_flash.strip(),
        }
        ctx.close()

        # 2. Desktop 1366x900: Admin adjustment error focus + Kardex keyboard table wrap
        ctx_adm = browser.new_context(viewport={"width": 1366, "height": 900})
        page_adm = ctx_adm.new_page()
        login_as(page_adm, "admin08c@local.test")
        page_adm.goto(f"{base_url}/inventario/ajustes/nuevo/?lote={lot_act.pk}", wait_until="networkidle")
        page_adm.fill('input[name="delta"]', "0")
        page_adm.fill('textarea[name="reason"]', " ")
        page_adm.click('button[type="submit"]')
        page_adm.wait_for_load_state("networkidle")
        results["desktop_1366_a11y_and_flows"]["adjustment_error_focus"] = {
            "has_adjustment_errors_box": page_adm.locator("#adjustment-errors").count() > 0,
            "active_element": page_adm.evaluate("() => document.activeElement ? document.activeElement.tagName + '#' + (document.activeElement.id || '') : null"),
            "a11y": inspect_a11y_and_layout(page_adm),
        }
        page_adm.goto(f"{base_url}/inventario/ajustes/{adj_seed.pk}/", wait_until="networkidle")
        results["desktop_1366_a11y_and_flows"]["adjustment_detail"] = inspect_a11y_and_layout(page_adm)
        page_adm.goto(f"{base_url}/inventario/productos/{prod_act.pk}/movimientos/", wait_until="networkidle")
        results["desktop_1366_a11y_and_flows"]["product_movements"] = inspect_a11y_and_layout(page_adm)
        ctx_adm.close()

        # 3. Mobile 390x844 audit AFTER app.css edits
        ctx_mob = browser.new_context(viewport={"width": 390, "height": 844})
        pm = ctx_mob.new_page()
        login_as(pm, "admin08c@local.test")
        mob_views = [
            ("01-movil-390-bajas-selector.png", f"{base_url}/inventario/bajas/nueva/"),
            ("02-movil-390-constancia-merma.png", f"{base_url}/inventario/bajas/{wo_seed.pk}/"),
            ("03-movil-390-ajustes-selector.png", f"{base_url}/inventario/ajustes/nuevo/"),
            ("04-movil-390-detalle-ajuste.png", f"{base_url}/inventario/ajustes/{adj_seed.pk}/"),
            ("05-movil-390-kardex.png", f"{base_url}/inventario/productos/{prod_act.pk}/movimientos/"),
        ]
        for fname, url in mob_views:
            pm.goto(url, wait_until="networkidle")
            pm.screenshot(path=str(OUT_DIR / fname), full_page=True)
            results["mobile_390_post_appcss_audit"][fname] = inspect_a11y_and_layout(pm)
        ctx_mob.close()
        browser.close()

    server.shutdown()
    (OUT_DIR / "browser_08c_resultado.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "wo_back_delta": results["desktop_1366_a11y_and_flows"]["browser_back_resubmit_idempotency"]["wo_count_delta"],
        "adj_focus": results["desktop_1366_a11y_and_flows"]["adjustment_error_focus"]["active_element"],
        "wo_errors_box": results["desktop_1366_a11y_and_flows"]["writeoff_error_state"]["has_writeoff_errors_box"],
        "mobile_kardex_overflow": results["mobile_390_post_appcss_audit"]["05-movil-390-kardex.png"]["horizontalPageOverflow"],
        "mobile_kardex_sidebar_overflow": results["mobile_390_post_appcss_audit"]["05-movil-390-kardex.png"]["sidebarNavOverflow"],
        "mobile_kardex_table_clipped": [w["horizontallyClipped"] for w in results["mobile_390_post_appcss_audit"]["05-movil-390-kardex.png"]["tableWraps"]],
        "http_5xx": len(results["errors"]["http_5xx"]),
        "pageerror": len(results["errors"]["pageerror"]),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
