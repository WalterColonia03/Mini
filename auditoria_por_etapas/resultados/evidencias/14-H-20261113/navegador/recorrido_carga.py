"""14-H1: carga por UI, consulta histórica y contraste SQLite aislado."""
import argparse
import importlib.util
import json
import sqlite3
from contextlib import closing
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("audit14d", HERE.parents[1] / "14-D-20261113/navegador/recorrido.py")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
original_prepare = base.prepare
base.ACTORS = {"ADMIN":"Administración 14H", "ALMACENERO":"Almacén original 14H", "VENDEDOR":"Venta 14H"}
FINAL = False


def prepare(db, password):
    original_prepare(db, password)
    from django.db import connection
    from catalog.models import Category, Product
    from inventory.models import Supplier
    category = Category.objects.create(name="Familia 14H")
    Product.objects.create(name="Producto original 14H", category=category, barcode="INT-14H",
        sale_price=Decimal("10"), unit="UND", controls_expiration=True)
    Supplier.objects.create(name="Proveedor original 14H", ruc="20000000014")
    connection.close()


class Journey(base.Journey):
    def run(self, browser, password):
        w = self.connect(browser, "ALMACENERO", password)
        a = self.connect(browser, "ADMIN", password)
        v = self.connect(browser, "VENDEDOR", password)
        snap = self.observe
        base.link(w, "/inventario/carga-inicial/")
        snap("01-formulario", "ALMACENERO", w, photo=True)
        for name, match in (("product","Producto original 14H"),("supplier","Proveedor original 14H")):
            field = base.selector(w, name)
            field.select_option(label=next(o for o in field.locator("option").all_text_contents() if match in o))
        today = base.datetime.now(base.ZoneInfo("America/Lima")).date()
        for i, (number, qty, cost) in enumerate((("  a  1 ",3,"2.1234"),("B",7,"4"))):
            for name, val in dict(number=number,quantity=str(qty),unit_cost=cost,expiration_date=(today+timedelta(days=30+i)).isoformat()).items():
                base.fill(w, f"lots-{i}-{name}", val)
        payload = w.locator("form").filter(has=w.locator('[name="lots-0-number"]')).evaluate("f=>Object.fromEntries(new FormData(f))")
        base.button(w, "Confirmar existencias")
        confirmed = snap("02-carga-confirmada", "ALMACENERO", w, lambda s,t:"Carga inicial confirmada" in t and sum(l["available_quantity"] for l in s["lotes"])==10,photo=True)
        path = base.urlsplit(w.url).path
        # Rename fixture directly: this is a historical control, not UI edit coverage.
        with closing(sqlite3.connect(self.db)) as con:
            con.execute("UPDATE catalog_product SET name='Producto actual 14H',barcode='INT-ACTUAL-14H'")
            con.execute("UPDATE inventory_supplier SET name='Proveedor actual 14H',ruc='20000000015',is_active=0")
            con.execute("UPDATE identity_account SET display_name='Almacén actual 14H' WHERE email='almacenero@example.invalid'")
            con.commit()
        w.reload()
        renamed = snap("03-carga-tras-cambiar-maestros", "ALMACENERO", w,photo=True)
        body = w.locator("main").inner_text()
        checks = {"producto_original":"Producto original 14H" in body,
            "autor_original":"Almacén original 14H" in body,
            "proveedor_original":"Proveedor original 14H" in body,
            "costo_cuatro_decimales":"2,1234" in body or "2.1234" in body}
        base.save(self.out/"comparaciones.json",checks)
        if not FINAL:
            return
        assert all(checks.values()), checks
        a.goto(self.base+path)
        snap("04-admin-constancia", "ADMIN", a,lambda s,t:"Producto original 14H" in t,same=renamed,photo=True)
        self.denied("05-vendedor-constancia-403", "VENDEDOR", v, path)
        self.denied("06-admin-carga-403", "ADMIN", a, "/inventario/carga-inicial/")
        self.denied("07-vendedor-carga-403", "VENDEDOR", v, "/inventario/carga-inicial/")
        response = w.request.post(self.base+"/inventario/carga-inicial/", form=payload)
        assert response.status == 200 and base.witness(self.db)["sha256"] == renamed["sha256"]
        base.save(self.out/"08-reintento-rechazado.json",dict(http=response.status,sin_mutacion=True))
        self.steps.append("08-reintento-rechazado")
        base.link(a,"/inventario/ajustes/nuevo/")
        a.get_by_role("row").filter(has_text="A 1").get_by_role("link",name="Ajustar").click()
        base.fill(a,"delta","2")
        base.fill(a,"reason","Recuento ficticio 14H")
        base.button(a,"Confirmar ajuste")
        adjusted = snap("09-ajuste-positivo", "ADMIN", a,lambda s,t:sum(l["available_quantity"] for l in s["lotes"])==12,photo=True)
        w.goto(self.base+path)
        snap("10-original-y-disponible", "ALMACENERO", w,lambda s,t:"3 UND" in t and "5 UND" in t and "Producto original 14H" in t,same=adjusted,photo=True)
        base.link(w,"/inventario/stock/")
        w.get_by_role("link",name="Ver movimientos").click()
        snap("11-movimientos-con-origen", "ALMACENERO", w,lambda s,t:all(x in t for x in ("+3","+7","+2","Proveedor original 14H","Almacén original 14H")),same=adjusted,photo=True)
        w.get_by_role("link",name="Ver carga inicial").first.click()
        snap("12-enlace-carga", "ALMACENERO", w,lambda s,t:"Producto original 14H" in t,same=adjusted)
        w.set_viewport_size({"width":390,"height":844})
        snap("13-consulta-movil", "ALMACENERO", w,same=adjusted,photo=True)
        assert w.evaluate("document.documentElement.scrollWidth <= innerWidth")
        region=w.get_by_role("region",name="Lotes de la carga inicial, tabla desplazable")
        region.focus()
        region.press("End")
        region.evaluate("e=>e.scrollLeft=e.scrollWidth")
        assert region.evaluate("e=>e.scrollLeft>0")
        snap("13b-tabla-movil-desplazada", "ALMACENERO", w,same=adjusted,photo=True)
        # Old load deliberately lacks a snapshot; no backfill by inspection.
        with closing(sqlite3.connect(self.db)) as con:
            con.execute("DELETE FROM inventory_initialloadline")
            con.execute("UPDATE inventory_initialinventoryload SET product_snapshot_name=NULL,product_snapshot_barcode=NULL,unit_snapshot=NULL,responsible_snapshot_name=NULL,supplier_snapshot_name=NULL,supplier_snapshot_ruc=NULL,average_cost_snapshot=NULL")
            con.commit()
        w.set_viewport_size({"width":1280,"height":900})
        w.reload()
        legacy = snap("14-legado-explicito", "ALMACENERO", w,lambda s,t:"Cantidad original no disponible" in t and "Datos actuales" in t,photo=True)
        base.link(w,"/inventario/stock/")
        w.get_by_role("link",name="Ver movimientos").click()
        snap("15-legado-movimientos", "ALMACENERO", w,lambda s,t:"Origen histórico incompleto" in t,same=legacy,photo=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("salida",type=Path)
    parser.add_argument("--final",action="store_true")
    args=parser.parse_args()
    FINAL=args.final
    base.prepare=prepare
    base.Journey=Journey
    try:
        base.main(args.salida)
    finally:
        p=args.salida/"ejecucion.json"
        if p.exists():
            data=json.loads(p.read_text(encoding="utf-8"))
            data.update(sublote="14-H1",runner14h_sha256=base.sha(Path(__file__).read_bytes()))
            base.save(p,data)
