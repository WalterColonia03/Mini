"""Real-browser (Chrome Playwright) Stage 08 audit journey on isolated WSGI + temporary SQLite DB."""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import secrets
import sqlite3
import sys
import tempfile
import threading
import uuid
from contextlib import closing
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit
from wsgiref.simple_server import WSGIRequestHandler, make_server

ROOT = Path(__file__).resolve().parents[5]
R1_PMV = ROOT / "r1-pmv"
OUT = Path(__file__).resolve().parent

ACTORS = {
    "ADMIN": ("Administración 08B", "Administrador"),
    "ALMACENERO": ("Almacén 08B", "Almacenero"),
    "VENDEDOR": ("Venta 08B", "Vendedor"),
}


class QuietHandler(WSGIRequestHandler):
    def log_message(self, *args):
        pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def witness(db: Path) -> dict:
    with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)) as con:
        tables = [
            r[0]
            for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            if r[0].startswith(("catalog_", "inventory_", "sales_", "cash_"))
        ]
        per_table = {}
        counts = {}
        for t in tables:
            rows = list(con.execute(f'SELECT * FROM "{t}" ORDER BY 1'))
            counts[t] = len(rows)
            per_table[t] = sha(json.dumps(rows, ensure_ascii=True, default=str).encode())
        return {
            "sha256": sha(json.dumps(per_table, sort_keys=True).encode()),
            "counts": counts,
            "per_table": per_table,
        }


def layout_probe(page) -> dict:
    return page.evaluate(
        """() => {
            const doc = document.documentElement;
            const clipped = [...document.querySelectorAll('.alert, [role="alert"], .badge, nav a, h1, h2, h3')].map(el => {
                const r = el.getBoundingClientRect();
                return {
                    tag: el.tagName,
                    cls: el.className,
                    text: (el.innerText || '').trim().slice(0, 60),
                    w: Math.round(r.width),
                    h: Math.round(r.height),
                    clipsX: el.scrollWidth > el.clientWidth + 2,
                };
            }).filter(x => x.w > 0 && x.h > 0 && x.clipsX);
            const activeMenu = [...document.querySelectorAll('.nav-link.is-active, .sidebar a.active, a[aria-current="page"]')]
                .map(el => ({ href: el.getAttribute('href'), text: (el.innerText || '').trim() }));
            return {
                viewport: { w: window.innerWidth, h: window.innerHeight },
                scrollWidth: doc.scrollWidth,
                clientWidth: doc.clientWidth,
                horizontalOverflow: doc.scrollWidth > doc.clientWidth,
                clippedCount: clipped.length,
                clippedSample: clipped.slice(0, 8),
                activeMenu,
                topbarTitle: (document.querySelector('.app-topbar h1')?.innerText || '').trim(),
                pageHeading: (document.querySelector('.page-heading h2')?.innerText || '').trim(),
            };
        }"""
    )


def prepare_db(db_path: Path, password: str) -> dict:
    sys.path.insert(0, str(R1_PMV))
    os.environ.update(
        APP_ENV="test",
        DJANGO_DEBUG="false",
        DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
        DJANGO_SETTINGS_MODULE="config.settings",
        DJANGO_ALLOWED_HOSTS="127.0.0.1,localhost",
    )
    from config import env as config_env

    config_env.load_dotenv = lambda path=None: None
    from django.conf import settings

    settings.DATABASES = {
        "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": str(db_path)}
    }
    import django

    django.setup()
    from django.core.management import call_command
    from django.db import connection
    from django.utils import timezone as tz
    from cash.models import CashRegister
    from cash.services import open_cash_shift
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.models import Lot
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        register_physical_adjustment,
        register_stock_entry,
        write_off_stock,
    )
    from sales.services import add_product_to_draft, checkout_sale

    call_command("migrate", verbosity=0, interactive=False)
    accounts = {}
    for code, (dname, rname) in ACTORS.items():
        role, _ = Role.objects.get_or_create(code=code, defaults={"name": rname})
        accounts[code] = Account.objects.create_user(
            email=f"{code.lower()}@example.invalid",
            password=password,
            display_name=dname,
            role=role,
        )

    today = tz.localdate()
    cat_active = Category.objects.create(name="Abarrotes Audit08B", is_active=True)
    cat_inactive = Category.objects.create(name="Descontinuados Audit08B", is_active=True)

    prod_active = Product.objects.create(
        category=cat_active,
        name="Aceite Vegetal <Safe> 1L",
        barcode="7750800010011",
        sale_price=Decimal("9.50"),
        minimum_stock=4,
        is_active=True,
    )
    prod_zero = Product.objects.create(
        category=cat_active,
        name="Arroz Extra 5Kg",
        barcode="7750800010022",
        sale_price=Decimal("22.00"),
        minimum_stock=2,
        is_active=True,
    )
    prod_pag = Product.objects.create(
        category=cat_active,
        name="Galleta Soda Paginada",
        barcode="7750800010033",
        sale_price=Decimal("1.50"),
        minimum_stock=5,
        is_active=True,
    )
    prod_inactive_cat = Product.objects.create(
        category=cat_inactive,
        name="Fideo Categoria Desactivada",
        barcode="7750800010044",
        sale_price=Decimal("4.00"),
        minimum_stock=1,
        is_active=True,
    )

    # 1) Active product: load 10 @ S/ 5.00 + receipt 5 @ S/ 8.00 => 15 u, avg S/ 6.0000
    confirm_initial_load(
        actor=accounts["ALMACENERO"],
        product=prod_active,
        lots=[
            LotInput("L-ACT-VENC", 3, Decimal("5.0000"), today + timedelta(days=1)),
            LotInput("L-ACT-VIG", 7, Decimal("5.0000"), today + timedelta(days=30)),
        ],
    )
    lot_exp = Lot.objects.get(product=prod_active, number="L-ACT-VENC")
    Lot.objects.filter(pk=lot_exp.pk).update(expiration_date=today - timedelta(days=1))

    lot_vig = Lot.objects.get(product=prod_active, number="L-ACT-VIG")
    register_stock_entry(
        actor=accounts["ALMACENERO"],
        product=prod_active,
        lots=[LotInput("L-ACT-REC", 5, Decimal("8.0000"), today + timedelta(days=60))],
        idempotency_key=uuid.uuid4(),
    )
    lot_rec = Lot.objects.get(product=prod_active, number="L-ACT-REC")

    # 2) Zero-stock product: load 2 @ S/ 14.00, sell all 2 so Q = 0 & avg = 0
    confirm_initial_load(
        actor=accounts["ALMACENERO"],
        product=prod_zero,
        lots=[LotInput("L-ZERO-1", 2, Decimal("14.0000"), today + timedelta(days=25))],
    )
    CashRegister.objects.create(code="CAJA-01")
    open_cash_shift(
        actor=accounts["VENDEDOR"],
        opening_amount=Decimal("100.00"),
    )
    draft_zero = add_product_to_draft(actor=accounts["VENDEDOR"], product_id=prod_zero.pk, quantity=2)
    checkout_sale(
        actor=accounts["VENDEDOR"],
        draft_id=draft_zero.pk,
        cash_received=Decimal("50.00"),
        idempotency_key=uuid.uuid4(),
    )
    lot_zero = Lot.objects.get(product=prod_zero, number="L-ZERO-1")

    # 2b) Perform a multi-lot FEFO sale on prod_active (9 units = 7 from L-ACT-VIG + 2 from L-ACT-REC, never L-ACT-VENC!)
    # Wait: leave that sale for after loading prod_active or do an 8-unit sale now -> leaves 3 on L-ACT-VENC, 0 on L-ACT-VIG, 4 on L-ACT-REC
    draft_active = add_product_to_draft(actor=accounts["VENDEDOR"], product_id=prod_active.pk, quantity=8)
    checkout_sale(
        actor=accounts["VENDEDOR"],
        draft_id=draft_active.pk,
        cash_received=Decimal("80.00"),
        idempotency_key=uuid.uuid4(),
    )

    # 3) Paginated product: 1 load + 27 operations = 28 movement rows (>25 page size)
    confirm_initial_load(
        actor=accounts["ALMACENERO"],
        product=prod_pag,
        lots=[LotInput("L-PAG-01", 60, Decimal("0.8000"), today + timedelta(days=90))],
    )
    lot_pag = Lot.objects.get(product=prod_pag, number="L-PAG-01")
    for idx in range(27):
        if idx % 2 == 0:
            write_off_stock(
                actor=accounts["ALMACENERO"],
                lot=lot_pag,
                quantity=1,
                reason="DAÑO",
                notes=f"Empaque aplastado #{idx + 1}",
                idempotency_key=uuid.uuid4(),
            )
        else:
            register_physical_adjustment(
                actor=accounts["ADMIN"],
                lot=lot_pag,
                delta=1,
                reason=f"Conteo ajuste #{idx + 1}",
                idempotency_key=uuid.uuid4(),
            )

    # 4) Inactive category + inactive product with initial load already confirmed
    confirm_initial_load(
        actor=accounts["ALMACENERO"],
        product=prod_inactive_cat,
        lots=[LotInput("L-INACT-1", 4, Decimal("2.5000"), today + timedelta(days=40))],
    )
    lot_inact = Lot.objects.get(product=prod_inactive_cat, number="L-INACT-1")
    Product.objects.filter(pk=prod_inactive_cat.pk).update(is_active=False)
    Category.objects.filter(pk=cat_inactive.pk).update(is_active=False)

    # 5) Perform a multi-lot sale on prod_active later? Done in browser or checked before closing
    connection.close()
    return {
        "prod_active": {"id": str(prod_active.pk), "name": prod_active.name},
        "lot_exp": {"id": str(lot_exp.pk), "number": lot_exp.number},
        "lot_vig": {"id": str(lot_vig.pk), "number": lot_vig.number},
        "lot_rec": {"id": str(lot_rec.pk), "number": lot_rec.number},
        "prod_zero": {"id": str(prod_zero.pk), "name": prod_zero.name},
        "lot_zero": {"id": str(lot_zero.pk), "number": lot_zero.number},
        "prod_pag": {"id": str(prod_pag.pk), "name": prod_pag.name},
        "prod_inactive_cat": {"id": str(prod_inactive_cat.pk), "name": prod_inactive_cat.name},
        "lot_inact": {"id": str(lot_inact.pk), "number": lot_inact.number},
        "today": today.isoformat(),
    }


def login(browser, base_url: str, role_code: str, password: str, console_errors: list, server_errors: list):
    ctx = browser.new_context(locale="es-PE", timezone_id="America/Lima", viewport={"width": 1366, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(8000)
    page.on("pageerror", lambda err: console_errors.append(f"[{role_code}] pageerror: {err}"))
    page.on("console", lambda msg: console_errors.append(f"[{role_code}] console.{msg.type}: {msg.text}") if msg.type == "error" else None)
    page.on("response", lambda r: server_errors.append({"role": role_code, "url": r.url, "status": r.status}) if r.status >= 500 else None)
    page.goto(base_url + "/")
    page.locator('[name="email"]').fill(f"{role_code.lower()}@example.invalid")
    page.locator('[name="password"]').fill(password)
    page.get_by_role("button", name="Iniciar sesión", exact=True).click()
    page.wait_for_url("**/inicio/")
    return ctx, page


def main() -> None:
    from playwright.sync_api import sync_playwright

    steps = []
    console_errors: list[str] = []
    server_errors: list[dict] = []

    tmpdir = tempfile.mkdtemp(prefix="audit08b_browser_")
    try:
        db_path = Path(tmpdir).resolve() / "browser08b.sqlite3"
        password = secrets.token_urlsafe(24)
        fix = prepare_db(db_path, password)

        from django.contrib.staticfiles.handlers import StaticFilesHandler
        from django.core.wsgi import get_wsgi_application
        from django.db import connections

        server = make_server("127.0.0.1", 0, StaticFilesHandler(get_wsgi_application()), handler_class=QuietHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_port}"

        def record(step_id: str, role: str, page, ok_cond: bool, extra: dict | None = None, shot: bool = True, same_before: dict | None = None):
            page.wait_for_load_state("load")
            w_now = witness(db_path)
            if same_before is not None:
                assert w_now["sha256"] == same_before["sha256"], f"Unexpected DB mutation on {step_id}"
            assert ok_cond, f"Check failed on {step_id}"
            lp = layout_probe(page)
            assert not lp["horizontalOverflow"], f"Horizontal overflow on {step_id}: {lp}"
            if shot:
                page.screenshot(path=str(OUT / f"{step_id}.png"), full_page=True)
            steps.append(
                {
                    "id": step_id,
                    "role": role,
                    "path": urlsplit(page.url).path + (("?" + urlsplit(page.url).query) if urlsplit(page.url).query else ""),
                    "layout": lp,
                    "non_mutation_verified": same_before is not None,
                    "witness_sha256": w_now["sha256"],
                    "extra": extra or {},
                }
            )
            return w_now

        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True, channel="chrome")
                try:
                    ctx_a, p_a = login(browser, base_url, "ADMIN", password, console_errors, server_errors)
                    ctx_w, p_w = login(browser, base_url, "ALMACENERO", password, console_errors, server_errors)
                    ctx_v, p_v = login(browser, base_url, "VENDEDOR", password, console_errors, server_errors)

                    w0 = witness(db_path)

                    # 1. ALMACENERO: open /inventario/bajas/nueva/ -> verify expired & active lots visible (L-ACT-VIG depleted by 8-u sale)
                    p_w.goto(base_url + "/inventario/bajas/nueva/")
                    txt = p_w.locator("body").inner_text()
                    record(
                        "01-merma-selector-almacenero",
                        "ALMACENERO",
                        p_w,
                        "L-ACT-VENC" in txt and "L-ACT-REC" in txt and "L-ACT-VIG" not in txt,
                        same_before=w0,
                    )

                    # 2. ALMACENERO: try DAMAGE on expired lot -> rejected without mutation
                    p_w.goto(base_url + f"/inventario/bajas/nueva/?lote={fix['lot_exp']['id']}")
                    p_w.locator('[name="quantity"]').fill("1")
                    p_w.locator('[name="reason"]').select_option("DAÑO")
                    p_w.locator('[name="notes"]').fill("Botella golpeada despues de vencer")
                    p_w.get_by_role("button", name="Confirmar baja", exact=True).click()
                    txt_err = p_w.locator("body").inner_text()
                    record("02-merma-dano-lote-vencido-rechazo", "ALMACENERO", p_w, "Vencimiento por caducidad o Robo o faltante" in txt_err, same_before=w0)

                    # 3. ALMACENERO: register THEFT write-off on expired lot (RN-05/C-01) -> B-* receipt + print media check
                    p_w.locator('[name="reason"]').select_option("ROBO")
                    p_w.locator('[name="notes"]').fill("Faltante <script>alert(1)</script> en estante vencido")
                    idem_wo = p_w.locator('[name="idempotency_key"]').input_value()
                    p_w.get_by_role("button", name="Confirmar baja", exact=True).click()
                    p_w.wait_for_url("**/inventario/bajas/*/")
                    receipt_url = urlsplit(p_w.url).path
                    rtxt = p_w.locator("body").inner_text()
                    wo_correlativo = "B-00000015"
                    w1 = record(
                        "03-constancia-merma-robo-vencido",
                        "ALMACENERO",
                        p_w,
                        "Constancia interna de merma. No es un comprobante de pago." in rtxt
                        and wo_correlativo in rtxt
                        and "Carga inicial " in rtxt
                        and "Faltante <script>alert(1)</script> en estante vencido" in rtxt
                        and "6.0000" in rtxt.replace(",", "."),
                        extra={"correlativo": wo_correlativo},
                    )

                    # Print CSS emulation check
                    p_w.emulate_media(media="print")
                    p_w.screenshot(path=str(OUT / "03b-constancia-merma-print.png"), full_page=True)
                    p_w.emulate_media(media="screen")

                    # Replay idempotency check via POST using same idempotency_key
                    p_w.goto(base_url + f"/inventario/bajas/nueva/?lote={fix['lot_exp']['id']}")
                    csrf_token = p_w.locator('[name="csrfmiddlewaretoken"]').first.input_value()
                    replay_resp = p_w.request.post(
                        base_url + "/inventario/bajas/nueva/",
                        form={
                            "csrfmiddlewaretoken": csrf_token,
                            "lot_id": fix["lot_exp"]["id"],
                            "idempotency_key": idem_wo,
                            "quantity": "1",
                            "reason": "ROBO",
                            "notes": "Faltante <script>alert(1)</script> en estante vencido",
                        },
                    )
                    assert replay_resp.status == 200 and receipt_url in replay_resp.url
                    w_replay = witness(db_path)
                    assert w_replay["sha256"] == w1["sha256"], "Replay mutated DB!"

                    # 4. Cross-role: VENDEDOR denied (403) on merma form, merma receipt, adjustment form, adjustment detail
                    for step_id, path in [
                        ("04a-vendedor-403-merma-form", "/inventario/bajas/nueva/"),
                        ("04b-vendedor-403-constancia", receipt_url),
                        ("04c-vendedor-403-ajuste-form", "/inventario/ajustes/nuevo/"),
                    ]:
                        resp = p_v.goto(base_url + path)
                        assert resp.status == 403
                        record(step_id, "VENDEDOR", p_v, "No tienes permiso" in p_v.locator("body").inner_text() or "Acceso denegado" in p_v.locator("body").inner_text(), shot=(step_id == "04b-vendedor-403-constancia"), same_before=w1)

                    # ALMACENERO denied (403) on /inventario/ajustes/nuevo/
                    resp_alm_adj = p_w.goto(base_url + "/inventario/ajustes/nuevo/")
                    assert resp_alm_adj.status == 403
                    record("05-almacenero-403-ajuste-nuevo", "ALMACENERO", p_w, "No tienes permiso" in p_w.locator("body").inner_text() or "Acceso denegado" in p_w.locator("body").inner_text(), same_before=w1)

                    # ADMIN allowed on receipt created by ALMACENERO
                    resp_adm_rec = p_a.goto(base_url + receipt_url)
                    assert resp_adm_rec.status == 200
                    record("06-admin-lee-constancia-almacenero", "ADMIN", p_a, "Constancia interna de merma. No es un comprobante de pago." in p_a.locator("body").inner_text(), shot=False, same_before=w1)

                    # 5. ADMIN: Adjustment selector -> confirm inactive product + 0 u. lot are visible (note lack of Inactivo badge)
                    p_a.goto(base_url + "/inventario/ajustes/nuevo/")
                    adj_sel_txt = p_a.locator("body").inner_text()
                    record(
                        "07-ajuste-selector-admin",
                        "ADMIN",
                        p_a,
                        "L-INACT-1" in adj_sel_txt and "L-ZERO-1" in adj_sel_txt,
                        extra={"badge_inactivo_present": "Inactivo" in adj_sel_txt},
                        same_before=w1,
                    )

                    # 6. ADMIN: Existing lot negative adjustment on inactive product/category
                    p_a.goto(base_url + f"/inventario/ajustes/nuevo/?lote={fix['lot_inact']['id']}")
                    p_a.locator('[name="delta"]').fill("-2")
                    p_a.locator('[name="reason"]').fill("Retiro fisico de producto desactivado")
                    p_a.get_by_role("button", name="Confirmar ajuste", exact=True).click()
                    p_a.wait_for_url("**/inventario/ajustes/*/")
                    adj_inact_url = urlsplit(p_a.url).path
                    w2 = record("08-ajuste-negativo-inactivo", "ADMIN", p_a, "-2" in p_a.locator("body").inner_text() and "Fideo Categoria Desactivada" in p_a.locator("body").inner_text())

                    # ALMACENERO CAN read adjustment detail & VENDEDOR gets 403 on adjustment detail
                    assert p_w.goto(base_url + adj_inact_url).status == 200
                    record("09-almacenero-lee-ajuste", "ALMACENERO", p_w, "Detalle del ajuste físico" in p_w.locator("body").inner_text(), shot=False, same_before=w2)
                    assert p_v.goto(base_url + adj_inact_url).status == 403

                    # 7. ADMIN: Q=0 product new lot requires unit_cost + cost_source; test rejection first, then valid
                    p_a.goto(base_url + f"/inventario/ajustes/nuevo/?producto={fix['prod_zero']['id']}")
                    p_a.locator('[name="number"]').fill("L-ZERO-RECUP")
                    exp_ok = (datetime.strptime(fix["today"], "%Y-%m-%d").date() + timedelta(days=45)).isoformat()
                    p_a.locator('[name="expiration_date"]').fill(exp_ok)
                    p_a.locator('[name="delta"]').fill("4")
                    p_a.locator('[name="reason"]').fill("Hallazgo en conteo anual Q=0")
                    p_a.get_by_role("button", name="Confirmar ajuste", exact=True).click()
                    record("10-ajuste-q0-sin-costo-rechazo", "ADMIN", p_a, "stock físico en cero" in p_a.locator("body").inner_text(), same_before=w2)

                    p_a.locator('[name="unit_cost"]').fill("11.2500")
                    p_a.locator('[name="cost_source"]').fill("Factura proveedor F001-00912")
                    p_a.get_by_role("button", name="Confirmar ajuste", exact=True).click()
                    p_a.wait_for_url("**/inventario/ajustes/*/")
                    adj_zero_url = urlsplit(p_a.url).path
                    w3 = record(
                        "11-ajuste-q0-lote-nuevo-ok",
                        "ADMIN",
                        p_a,
                        "11.2500" in p_a.locator("body").inner_text().replace(",", ".")
                        and "Factura proveedor F001-00912" in p_a.locator("body").inner_text()
                        and "AJUSTE" in p_a.locator("body").inner_text(),
                    )

                    # 8. Check prod_active movements as ADMIN, ALMACENERO (200 with costs) & VENDEDOR (403 denied!)
                    p_a.goto(base_url + f"/inventario/productos/{fix['prod_active']['id']}/movimientos/")
                    mov_a_txt = p_a.locator("body").inner_text()
                    record(
                        "12-kardex-admin-prod-activo",
                        "ADMIN",
                        p_a,
                        "Costo unitario de salida:" in mov_a_txt
                        and wo_correlativo in mov_a_txt
                        and "6.0000" in mov_a_txt.replace(",", ".")
                        and "L-ACT-VIG" in mov_a_txt
                        and "L-ACT-REC" in mov_a_txt,
                        same_before=w3,
                    )

                    r_mov_v = p_v.goto(base_url + f"/inventario/productos/{fix['prod_active']['id']}/movimientos/")
                    assert r_mov_v.status == 403
                    record("13-kardex-vendedor-403-denegado", "VENDEDOR", p_v, "No tienes permiso" in p_v.locator("body").inner_text() or "Acceso denegado" in p_v.locator("body").inner_text(), same_before=w3)

                    # Also verify ALMACENERO can read prod_active movements with 4-decimal costs
                    r_mov_w = p_w.goto(base_url + f"/inventario/productos/{fix['prod_active']['id']}/movimientos/")
                    assert r_mov_w.status == 200
                    record(
                        "13b-kardex-almacenero-200",
                        "ALMACENERO",
                        p_w,
                        "Costo unitario de salida:" in p_w.locator("body").inner_text()
                        and "6.0000" in p_w.locator("body").inner_text().replace(",", "."),
                        shot=False,
                        same_before=w3,
                    )

                    # 9. Pagination + type filter on prod_pag (28 rows -> page 1 = 25, page 2 = 3)
                    p_a.goto(base_url + f"/inventario/productos/{fix['prod_pag']['id']}/movimientos/")
                    rows_p1 = p_a.locator("table.movements-table tbody tr").count()
                    record("14-kardex-paginacion-p1", "ADMIN", p_a, rows_p1 == 25 and "Página 1 de 2" in p_a.locator("body").inner_text(), shot=False, same_before=w3)

                    p_a.goto(base_url + f"/inventario/productos/{fix['prod_pag']['id']}/movimientos/?page=1&tipo=merma")
                    rows_wo = p_a.locator("table.movements-table tbody tr").count()
                    # Total mermas = 14 (indices 0,2,...,26 => 14 writeoffs on page 1)
                    record("15-kardex-filtro-tipo-merma", "ADMIN", p_a, rows_wo == 14 and "Saldo de apertura (UND)" in p_a.locator("body").inner_text(), shot=False, same_before=w3)

                    p_a.goto(base_url + f"/inventario/productos/{fix['prod_pag']['id']}/movimientos/?page=2&tipo=merma")
                    record("15b-kardex-pagina-fuera-rango", "ADMIN", p_a, "no existe para estos filtros" in p_a.locator("body").inner_text().lower(), shot=False, same_before=w3)

                    p_a.goto(base_url + f"/inventario/productos/{fix['prod_pag']['id']}/movimientos/?page=2")
                    rows_p2 = p_a.locator("table.movements-table tbody tr").count()
                    record("16-kardex-paginacion-p2", "ADMIN", p_a, rows_p2 == 3 and "Página 2 de 2" in p_a.locator("body").inner_text(), same_before=w3)

                    # 10. Future routes return 404 without mutation
                    for label, future_path in [("writeoffs", "/inventario/bajas/"), ("adjustments", "/inventario/ajustes/")]:
                        r404 = p_a.goto(base_url + future_path)
                        assert r404.status == 404, f"Expected 404 on {future_path}, got {r404.status}"
                    record("17-rutas-futuras-404", "ADMIN", p_a, True, shot=False, same_before=w3)

                    # 11. Mobile 390x844 spot check on key Stage 08 screens
                    p_a.set_viewport_size({"width": 390, "height": 844})
                    p_a.goto(base_url + receipt_url)
                    record("18-movil-390-constancia-merma", "ADMIN", p_a, True, same_before=w3)
                    p_a.goto(base_url + adj_zero_url)
                    record("19-movil-390-detalle-ajuste", "ADMIN", p_a, True, same_before=w3)
                    p_a.goto(base_url + f"/inventario/productos/{fix['prod_active']['id']}/movimientos/")
                    record("20-movil-390-kardex", "ADMIN", p_a, True, same_before=w3)

                    ctx_a.close()
                    ctx_w.close()
                    ctx_v.close()
                finally:
                    browser.close()
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
            connections.close_all()
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)

    save_json(
        OUT / "browser_etapa08_resultado.json",
        {
            "executed_utc": datetime.now(timezone.utc).isoformat(),
            "playwright": importlib.metadata.version("playwright"),
            "django": importlib.metadata.version("django"),
            "console_errors": console_errors,
            "server_5xx_errors": server_errors,
            "steps_count": len(steps),
            "steps": steps,
        },
    )
    print(f"Browser Stage 08 audit complete: {len(steps)} steps, console_errors={len(console_errors)}, server_5xx={len(server_errors)}")


if __name__ == "__main__":
    main()
