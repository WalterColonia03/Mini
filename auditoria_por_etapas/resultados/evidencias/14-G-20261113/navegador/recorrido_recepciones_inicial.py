"""Recepción desde UI y contraste con SQLite ficticia. Cada salida debe ser nueva."""
import argparse
import importlib.util
import json
import sqlite3
import uuid
from contextlib import closing
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("audit14d", HERE.parents[1] / "14-D-20261113/navegador/recorrido.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.ACTORS = {"ADMIN": "Administración 14G", "ALMACENERO": "Almacén 14G", "VENDEDOR": "Venta 14G"}
original_prepare = base.prepare
PRODUCT = "Recepción 14G"


def prepare(db, password):
    original_prepare(db, password)
    from django.db import connection
    from django.utils import timezone
    from catalog.models import Category, Product
    from identity.models import Account
    from inventory.models import Supplier
    from inventory.services import confirm_initial_load, LotInput
    category = Category.objects.create(name="Familia 14G")
    product = Product.objects.create(name=PRODUCT, category=category, barcode="INT-14G",
        barcode_normalized="INT-14G", barcode_type="INTERNAL", search_name="recepcion 14g",
        unit="UND", controls_expiration=True, sale_price=Decimal("10"))
    supplier = Supplier.objects.create(name="Proveedor original 14G", ruc="20000000014")
    actor = Account.objects.get(email="almacenero@example.invalid")
    confirm_initial_load(actor=actor, product=product, supplier=supplier,
        lots=[LotInput("INICIAL", 10, Decimal("3"), timezone.localdate()+timedelta(days=30))])
    connection.close()


class Journey(base.Journey):
    def run(self, browser, password):
        a = self.connect(browser, "ADMIN", password)
        w = self.connect(browser, "ALMACENERO", password)
        v = self.connect(browser, "VENDEDOR", password)
        snap = self.observe
        base.link(w, "/inventario/entrada/")
        snap("01-formulario", "ALMACENERO", w, photo=True)
        product_value = w.locator('select[name="product"] option').filter(has_text=PRODUCT).get_attribute("value")
        base.selector(w, "product").select_option(value=product_value)
        supplier_option = w.locator('select[name="supplier"] option').filter(has_text="Proveedor original 14G")
        base.selector(w, "supplier").select_option(value=supplier_option.get_attribute("value"))
        expiration = (base.datetime.now(base.ZoneInfo("America/Lima")).date()+timedelta(days=60)).isoformat()
        for name, value in {"number":" C ","quantity":"10","unit_cost":"6.0000","expiration_date":expiration}.items():
            base.fill(w, "lots-0-"+name, value)
        payload = w.locator("form[data-testid='stock-entry-form']").evaluate("f=>Object.fromEntries(new FormData(f))")
        payload.setdefault("idempotency_key", str(uuid.uuid4()))
        key_present = w.locator('[name="idempotency_key"]').count() == 1
        before = base.witness(self.db)
        base.button(w, "Confirmar entrada")
        first = snap("02-primera-recepcion", "ALMACENERO", w, photo=True)
        first_path = base.urlsplit(w.url).path
        reply = w.request.post(self.base+"/inventario/entrada/", form=payload)
        replay_path = base.urlsplit(reply.url).path
        replay_after = base.witness(self.db)
        base.save(self.out/"03-reintento.json", {"rol":"ALMACENERO","metodo":"POST","http":reply.status,
            "ruta":base.urlsplit(reply.url).path,"misma_ruta":base.urlsplit(reply.url).path==first_path,
            "sin_mutacion":first["sha256"]==replay_after["sha256"],"avisa_lote_existente":"ya existe" in reply.text()})
        self.steps.append("03-reintento")
        base.link(w, "/inventario/entrada/")
        base.selector(w, "product").select_option(value=product_value)
        for name, value in {"number":"C","quantity":"5","unit_cost":"8","expiration_date":expiration}.items():
            base.fill(w, "lots-0-"+name, value)
        base.button(w, "Confirmar entrada")
        second = snap("04-segunda-recepcion-mismo-lote", "ALMACENERO", w, photo=True)
        base.link(a, "/inventario/stock/")
        a.get_by_role("link", name="Ver movimientos").click()
        snap("05-movimientos-admin", "ADMIN", a, same=second, photo=True)
        self.denied("06-vendedor-entrada-403", "VENDEDOR", v, "/inventario/entrada/")
        self.denied("07-admin-entrada-403", "ADMIN", a, "/inventario/entrada/")
        # Same UUID with altered content must never be treated as another receipt.
        divergent = {**payload,"lots-0-number":"D","lots-0-quantity":"11"}
        reply = w.request.post(self.base+"/inventario/entrada/", form=divergent)
        after = base.witness(self.db)
        base.save(self.out/"08-clave-con-contenido-distinto.json", {"rol":"ALMACENERO","metodo":"POST",
            "http":reply.status,"sin_mutacion":after["sha256"]==second["sha256"],
            "ruta":base.urlsplit(reply.url).path,"testigo_antes":second,"testigo_despues":after})
        self.steps.append("08-clave-con-contenido-distinto")
        # Historical control is a technical fixture mutation, not UI coverage of edits.
        with closing(sqlite3.connect(self.db)) as con:
            con.execute("UPDATE inventory_supplier SET name='Proveedor renombrado 14G'")
            con.execute("UPDATE identity_account SET display_name='Almacén renombrado 14G' WHERE email='almacenero@example.invalid'")
            con.commit()
        w.goto(self.base+first_path)
        renamed = snap("09-constancia-tras-renombrar", "ALMACENERO", w, photo=True)
        base.save(self.out/"comparaciones.json", {
            "clave_en_formulario":key_present,"primera_ruta":first_path,
            "primero_fisico":sum(l["available_quantity"] for l in first["lotes"]),
            "primer_promedio":first["productos"][0]["average_cost"],
            "segundo_fisico":sum(l["available_quantity"] for l in second["lotes"]),
            "segundo_promedio":second["productos"][0]["average_cost"],
            "reintento_misma_constancia":first_path==replay_path,
            "reintento_igual_sin_mutacion":first["sha256"]==replay_after["sha256"],
            "clave_divergente_sin_mutacion":after["sha256"]==second["sha256"],
            "constancia_preserva_proveedor":"Proveedor original 14G" in w.locator("main").inner_text(),
            "constancia_preserva_responsable":"Almacén 14G" in w.locator("main").inner_text()})


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("salida",type=Path)
    base.prepare=prepare
    base.Journey=Journey
    base.main(parser.parse_args().salida)
