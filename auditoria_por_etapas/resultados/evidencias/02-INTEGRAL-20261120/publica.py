"""Chrome against the disposable academic deployment. All accounts and stock are fixtures."""
import json, os, sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit
stage = Path(os.environ["MMSTAGE"])
sys.path.insert(0, str(stage/"package"))
sys.path.insert(0, os.environ["MM_PLAYWRIGHT"])
from config.env import load_dotenv
load_dotenv(stage/".db.env")
base="https://minimarket-academico-auditoria02.vercel.app"
assert urlsplit(os.environ["DATABASE_URL"]).hostname.endswith("prisma.io")
os.environ.update(APP_ENV="demo", DJANGO_SECRET_KEY=(stage/"django.key").read_text(), PGSSLMODE="require",
                  DJANGO_SETTINGS_MODULE="config.settings", DJANGO_ALLOW_ASYNC_UNSAFE="true")
import django
django.setup()
from identity.models import Account
from cash.models import CashShift
from catalog.models import Category, Product
from inventory.services import confirm_initial_load, LotInput
from sales.models import SaleDraft
from django.utils import timezone
from playwright.sync_api import sync_playwright
creds=json.loads((stage/"fixtures.json").read_text())
seller=Account.objects.get(email=creds["VENDEDOR"][0])
warehouse=Account.objects.get(email=creds["ALMACENERO"][0])
assert seller.email.endswith("@prueba.invalid") and warehouse.email.endswith("@prueba.invalid")
if not Product.objects.filter(barcode="77500201").exists():
    cat=Category.objects.create(name="Abarrotes de ensayo")
    product=Product.objects.create(category=cat,name="Leche de ensayo",barcode="77500201",sale_price=Decimal("4.50"))
    confirm_initial_load(actor=warehouse,product=product,lots=[LotInput("L02",25,Decimal("3"),timezone.localdate()+timedelta(days=45))])
def check(label, value):
    print(label, bool(value), flush=True)
    assert value, label
with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path=r"C:\Program Files\Google\Chrome\Application\chrome.exe",headless=True)
    def login(role):
        p=browser.new_context(locale="es-PE").new_page()
        p.goto(base)
        email,password=creds[role]
        p.locator('[name=email]').fill(email)
        p.locator('[name=password]').fill(password)
        p.get_by_role("button",name="Iniciar sesión").click()
        p.wait_for_url("**/inicio/")
        return p
    a=login("ADMIN"); w=login("ALMACENERO"); s=login("VENDEDOR"); s2=login("VENDEDOR")
    check("cookies HTTPS / HttpOnly", all(c["secure"] and c["httpOnly"] for c in s.context.cookies() if c["name"]=="sessionid") and any(c["name"]=="sessionid" for c in s.context.cookies()))
    def row():
        a.goto(base+"/empleados/")
        return a.locator("tr").filter(has_text=seller.email)
    def role(label):
        row().get_by_text("Editar").click()
        a.locator("select[name=role]").select_option(label=label)
        a.get_by_role("button",name="Guardar cambios").click()
    def state(action):
        row().get_by_text(action,exact=True).click()
        a.locator("main form button[type=submit]").click()
    check("personal restringido", all(p.goto(base+"/empleados/").status==403 for p in (w,s)))
    check("caja previa", all(p.goto(base+"/caja/abrir/").status==200 for p in (s,s2)))
    role("Almacenero")
    check("rol revocado en las dos sesiones", all(p.goto(base+"/caja/abrir/").status==403 for p in (s,s2)))
    state("Desactivar")
    for p in (s,s2): p.goto(base+"/inicio/")
    check("desactivación en ambas sesiones", all("/?next=" in p.url for p in (s,s2)))
    state("Reactivar")
    for p in (s,s2): p.goto(base+"/inicio/")
    check("reactivación conserva revocación", all("/?next=" in p.url for p in (s,s2)))
    role("Vendedor"); s=login("VENDEDOR")
    s.goto(base+"/salir/")
    check("sin turno", "actualmente no tienes un turno" in s.inner_text("main"))
    s.goto(base+"/caja/abrir/"); s.locator('[name=opening_amount]').fill("50")
    s.get_by_role("button",name="Abrir turno").click()
    s.wait_for_url("**/caja/turnos/*/abierto/**")
    shift=CashShift.objects.get(seller=seller,status="OPEN")
    role("Almacenero"); seller.refresh_from_db()
    check("rol conservado con turno", seller.role.code=="VENDEDOR" and "turno de caja abierto" in a.inner_text("main"))
    state("Desactivar"); seller.refresh_from_db()
    check("desactivación rechazada con turno",seller.is_active and CashShift.objects.filter(pk=shift.pk,status="OPEN",seller=seller).exists())
    s.goto(base+"/salir/")
    check("turno sin borrador","seguirá ligado" in s.inner_text("main"))
    s.goto(base+"/ventas/?query=Leche"); s.locator('form:has(input[name=product_id]) button[type=submit]').click()
    draft=SaleDraft.objects.get(seller=seller,status=SaleDraft.Status.ACTIVE)
    s.goto(base+"/salir/"); check("advertencia borrador","La venta en preparación se descartará" in s.inner_text("main"))
    s.get_by_text("Cancelar",exact=True).click(); draft.refresh_from_db()
    check("cancelar conserva borrador",draft.status==SaleDraft.Status.ACTIVE)
    s.goto(base+"/salir/"); s.get_by_role("button",name="Cerrar sesión").click(); draft.refresh_from_db()
    check("confirmar descarta y mantiene turno", draft.status==SaleDraft.Status.DISCARDED and CashShift.objects.filter(pk=shift.pk,seller=seller,status="OPEN").exists())
    s.goto(base+"/inicio/"); check("salida invalida sesión", "/?next=" in s.url)
    browser.close()
