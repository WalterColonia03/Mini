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

    for page in (admin, wh):
        page.locator('nav a[href="/productos/"]').first.click()
        check("encabezado precio " + ("ADMIN" if page == admin else "ALMACENERO"),
              page.locator(".catalog-products th").nth(3).inner_text(), "Precio (S/)")
        check("v1 catálogo y categoría " + ("ADMIN" if page == admin else "ALMACENERO"),
              catalog_row(page).locator("td").all_inner_texts()[1:4],
              [category.name, barcode, "10,00"])
    check("almacén sin acción de edición", catalog_row(wh).get_by_text("Editar").count(), 0)
    for role, page in [("ALMACENERO", wh), ("VENDEDOR", seller)]:
        for path in ["/productos/categorias/", f"/productos/{product.pk}/editar/"]:
            check(role + " GET " + path, page.request.get(base + path).status, 403)
    check("VENDEDOR GET catálogo", seller.request.get(base + "/productos/").status, 403)
    check("ADMIN categorías", admin.request.get(base + "/productos/categorias/").status, 200)
    categories = admin.context.new_page()
    categories.goto(base + "/productos/categorias/")
    categories.reload()
    check("categoría activa tras recarga ADMIN",
          categories.locator("tbody tr").filter(has_text=category.name).locator("td").nth(1).inner_text(), "Activa")
    categories.close()
    seller.locator('nav a[href="/ventas/"]').first.click()
    offer(2)
    seller.get_by_role("link", name="Cobrar venta").click()
    pay("20.00")
    check("constancia v1", receipt("10.00", "20.00"), True)
    old_url = seller.url
    old_sale = Sale.objects.get(pk=old_url.rstrip("/").split("/")[-1])
    seller.goto(base + "/ventas/")
    offer(1)
    before = snapshot("borrador_antes")
    catalog_row(admin).get_by_role("link", name="Editar").click()
    check("etiqueta precio con IGV", admin.locator('label[for=id_sale_price]').inner_text(), "Precio final con IGV (S/)")
    admin.locator("[name=sale_price]").fill("11.50")
    check("acción explícita", admin.locator("main button[type=submit]").inner_text(), "Guardar cambios")
    admin.get_by_role("button", name="Guardar cambios").click()
    check("aviso de edición", admin.get_by_text(f"Producto «{name}» actualizado.", exact=True).count(), 1)
    for role, page in [("ADMIN", admin), ("ALMACENERO", wh)]:
        page.reload()
        check("v2 catálogo tras recarga " + role, catalog_row(page).locator("td").all_inner_texts()[1:4],
              [category.name, barcode, "11,50"])
    seller.reload()
    check("v1 en carrito tras recarga", seller.get_by_text("S/ 10,00 por unidad", exact=True).count(), 1)
    check("v2 en nueva búsqueda del vendedor", offer(), "S/ 11,50")
    check("GET conserva línea antigua", snapshot("recarga")["carrito"], ["10.00"])
    seller.get_by_role("link", name="Cobrar venta").click()
    pay("20.00")
    message = f"El precio de «{name}» cambió de S/ 10.00 a S/ 11.50. Verifica el nuevo total antes de confirmar el cobro."
    check("resumen exige revisión", seller.get_by_text(message, exact=True).count(), 1)
    stopped = snapshot("revision")
    check("revisión conserva stock, ventas y caja", [stopped[k] for k in ("lote","ventas_turno","efectivo_esperado")],
          [before[k] for k in ("lote","ventas_turno","efectivo_esperado")])
    check("línea revisada", stopped["carrito"], ["11.50"])
    pay("11.50")
    check("constancia v2", receipt("11.50", "11.50"), True)
    sale = Sale.objects.get(pk=seller.url.rstrip("/").split("/")[-1])
    check("base, IGV y total", [str(x) for x in (sale.base_amount, sale.igv_amount, sale.total_amount)],
          ["9.75", "1.75", "11.50"])
    after = snapshot("confirmada")
    check("ambas líneas históricas", after["lineas_venta"], [[2, "10.00", "20.00"], [1, "11.50", "11.50"]])
    check("un descuento de stock y un ingreso", [after["lote"], after["ventas_turno"], Decimal(after["efectivo_esperado"]) == Decimal(before["efectivo_esperado"])+Decimal("11.50")],
          [before["lote"]-1, before["ventas_turno"]+1, True])
    seller.goto(base + "/ventas/historial/turno/")
    for obj, total in [(old_sale, "20.00"), (sale, "11.50")]:
        row = seller.locator("tbody tr").filter(has_text=obj.correlative)
        check("total histórico " + obj.correlative, row.locator("td").nth(4).inner_text().replace(",", "."), total)
    seller.get_by_role("link", name=old_sale.correlative).click()
    seller.reload()
    check("constancia anterior recuperada desde historial", receipt("10.00", "20.00"), True)


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
    report["resultado"] = "P1 y P2 ejecutados"
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
