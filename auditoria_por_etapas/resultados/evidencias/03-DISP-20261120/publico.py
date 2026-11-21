"""Chrome y observaciones ORM sobre el despliegue académico aislado de 02."""
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

here = Path(__file__).resolve().parent
stage = Path(os.environ["MMSTAGE"])
package = stage / "package"
manifest = json.loads((here.parent / "02-INTEGRAL-20261120/paquete-entrega.json").read_text())
assert all(hashlib.sha256((package / name).read_bytes()).hexdigest() == digest
           for name, digest in manifest.items()), "El paquete de preparación difiere"
sys.path[:0] = [str(package), os.environ["MM_PLAYWRIGHT"]]
from config.env import load_dotenv
from urllib.parse import urlsplit

load_dotenv(stage / ".db.env")
assert urlsplit(os.environ["DATABASE_URL"]).hostname.endswith(".prisma.io")
os.environ.update(APP_ENV="demo", DJANGO_SECRET_KEY=(stage / "django.key").read_text(),
                  PGSSLMODE="require", DJANGO_SETTINGS_MODULE="config.settings",
                  DJANGO_ALLOW_ASYNC_UNSAFE="true")
import django
django.setup()
from cash.models import CashShift
from catalog.models import Category
from catalog.services import register_canned_product
from django.db import connection, transaction
from django.db.models import Sum
from django.utils.timezone import localdate
from identity.models import Account
from inventory.models import Lot
from inventory.services import confirm_initial_load, LotInput
from playwright.sync_api import sync_playwright
from sales.models import Sale, SaleDraft, SaleDraftLine, SaleLine

base = "https://minimarket-academico-auditoria02.vercel.app"
credentials = json.loads((stage / "fixtures.json").read_text())
run = uuid4().hex[:10].upper()
name, barcode = "Leche ensayo " + run, "PRECIO-" + run
report = {"inicio_utc": datetime.now(timezone.utc).isoformat(), "url": base, "fixture": barcode,
          "controles": [], "estados": {}}
root = next(p for p in here.parents if (p / "08_Historias_de_Usuario.md").exists())
report["08_sha256"] = hashlib.sha256((root / "08_Historias_de_Usuario.md").read_bytes()).hexdigest()
output = here / ("publico-" + run + ".json")


def save():
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf8")


def check(label, actual, expected):
    ok = actual == expected
    report["controles"].append(dict(caso=label, observado=actual, esperado=expected, cumple=ok))
    save()
    assert ok, label


def snapshot(label):
    product.refresh_from_db()
    rows = list(SaleLine.objects.filter(product=product).order_by("sale__correlative")
                .values_list("quantity", "unit_price", "amount"))
    active = SaleDraftLine.objects.filter(draft__cash_shift=shift, draft__status="ACTIVE", product=product)
    state = {"precio": str(product.sale_price), "lote": Lot.objects.get(product=product).available_quantity,
             "lineas_venta": [[q, str(p), str(a)] for q, p, a in rows],
             "carrito": [str(x) for x in active.values_list("unit_price", flat=True)],
             "ventas_turno": shift.sales.count(), "efectivo_esperado": str(shift.opening_amount +
                (shift.sales.aggregate(total=Sum("total_amount"))["total"] or Decimal("0")))}
    report["estados"][label] = state
    save()
    return state


def scenario(browser):
    def login(role):
        p = browser.new_context(locale="es-PE").new_page()
        p.goto(base)
        assert urlsplit(p.url).netloc == urlsplit(base).netloc
        p.locator("[name=email]").fill(credentials[role][0])
        p.locator("[name=password]").fill(credentials[role][1])
        p.get_by_role("button", name="Iniciar sesión").click()
        p.wait_for_url("**/inicio/")
        return p

    admin, wh, seller = [login(role) for role in ("ADMIN", "ALMACENERO", "VENDEDOR")]
    def catalog_row(page):
        return page.locator("tbody tr").filter(has_text=barcode)

    def offer(quantity=None):
        seller.locator("[name=query]").fill(barcode)
        seller.get_by_role("button", name="Buscar").click()
        row = seller.locator(".sales-search-panel tr").filter(has_text=name)
        if quantity is not None:
            row.locator("[name=quantity]").fill(str(quantity))
            row.get_by_role("button", name="Agregar").click()
        else:
            return row.locator("td").nth(3).inner_text()

    def pay(cash):
        seller.locator("[name=cash_received]").fill(cash)
        seller.get_by_role("button", name="Confirmar cobro").click()

    def receipt(unit, amount):
        row = seller.locator("#constancia-interna tbody tr").filter(has_text=name)
        return [cell.strip().replace(",", ".") for cell in row.locator("td").all_inner_texts()][-2:] == [
            "S/ " + unit, "S/ " + amount]

    kind = sys.argv[1]
    assert kind in ("producto", "categoria")
    report["variante"] = kind
    seller.locator('nav a[href="/ventas/"]').first.click()
    offer(2)
    seller.get_by_role("link", name="Cobrar venta").click()
    pay("20.00")
    check("venta previa", receipt("10.00", "20.00"), True)
    historic = seller.url
    seller.goto(base + "/ventas/")
    offer(1)
    before = snapshot("antes")
    def toggle(active):
        if kind == "producto":
            admin.goto(base + "/productos/")
            catalog_row(admin).get_by_role("button", name="Habilitar" if active else "Deshabilitar", exact=True).click()
        else:
            admin.goto(base + "/productos/categorias/")
            admin.locator("tbody tr").filter(has_text=category.name).get_by_role("button", name="Activar" if active else "Desactivar", exact=True).click()
            admin.get_by_role("button", name="Confirmar activación" if active else "Confirmar desactivación").click()
    toggle(False)
    for role, page in [("admin", admin), ("almacén", wh)]:
        page.goto(base + "/productos/")
        page.reload()
        check(role + " estado", catalog_row(page).locator("td").nth(6).inner_text(), "Inactivo" if kind == "producto" else "Categoría desactivada")
    seller.reload()
    seller.locator("[name=query]").fill(barcode)
    seller.get_by_role("button", name="Buscar").click()
    check("sin oferta", seller.locator(".sales-search-panel tr").filter(has_text=name).count(), 0)
    seller.get_by_role("link", name="Cobrar venta").click()
    pay("10.00")
    check("rechazo al cobrar", "no está disponible" in seller.inner_text("main") or "desactivada" in seller.inner_text("main"), True)
    from inventory.services import register_stock_entry
    from django.core.exceptions import ValidationError
    try:
        register_stock_entry(actor=warehouse, product=product, lots=[LotInput("NO-"+run,1,Decimal("3"),localdate()+timedelta(days=30))])
    except ValidationError as error:
        check("entrada rechazada por disponibilidad", any("disponible" in m or "desactivada" in m or "inactiv" in m for m in error.messages), True)
    else:
        raise AssertionError("entrada permitida")
    check("rechazos sin mutación", snapshot("rechazada"), before)
    seller.goto(historic)
    check("histórico accesible durante suspensión", receipt("10.00", "20.00"), True)
    toggle(True)
    seller.goto(base + "/ventas/")
    check("oferta reactivada", offer(), "S/ 10,00")
    seller.get_by_role("link", name="Cobrar venta").click()
    pay("10.00")
    check("venta recuperada", receipt("10.00", "10.00"), True)
    check("stock final", snapshot("final")["lote"], 5)


try:
    with connection.cursor() as cur:
        cur.execute("SHOW server_version")
        report["postgresql"] = cur.fetchone()[0]
    assert all(credentials[r][0].endswith("@prueba.invalid") for r in ("ADMIN","ALMACENERO","VENDEDOR"))
    admin_user, warehouse, seller_user = [Account.objects.get(email=credentials[r][0], role__code=r, is_active=True)
                                          for r in ("ADMIN","ALMACENERO","VENDEDOR")]
    shift = CashShift.objects.get(status="OPEN", seller=seller_user)
    check("sin borrador previo en turno ficticio", SaleDraft.objects.filter(cash_shift=shift, status="ACTIVE").exists(), False)
    with transaction.atomic():
        category = Category.objects.create(name="Lácteos ensayo " + run)
        product = register_canned_product(actor=admin_user, name=name, barcode=barcode, barcode_type="INTERNAL",
                                          category=category, unit="UND", sale_price=Decimal("10.00"), minimum_stock=2)
        confirm_initial_load(actor=warehouse, product=product, lots=[
            LotInput("L-" + run, 8, Decimal("3"), localdate() + timedelta(days=30))])
    snapshot("inicio")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe", headless=True)
        report["chrome"] = browser.version
        scenario(browser)
        browser.close()
    report["resultado"] = "Disponibilidad ejecutada"
except Exception as error:
    report["fallo"] = type(error).__name__
    import traceback
    report["ubicacion"] = [[Path(f.filename).name, f.lineno, f.name] for f in traceback.extract_tb(error.__traceback__) if f.filename == __file__]
    print("Fallo", report["fallo"], report["ubicacion"], flush=True)
    raise SystemExit(1)
finally:
    report["fin_utc"] = datetime.now(timezone.utc).isoformat()
    save()
    print(output.name, flush=True)

