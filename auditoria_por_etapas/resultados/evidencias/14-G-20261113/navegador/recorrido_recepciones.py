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
original_witness = base.witness
PRODUCT = "Recepción 14G"
FINAL = False


def witness(db):
    result = original_witness(db)
    with closing(sqlite3.connect(db.as_uri()+"?mode=ro",uri=True)) as con:
        con.row_factory=sqlite3.Row
        result["recepciones"]=[dict(r) for r in con.execute("SELECT correlative,product_snapshot_name,responsible_snapshot_name,supplier_snapshot_name,average_cost_after FROM inventory_stockreceipt ORDER BY correlative")]
        result["lineas_recepcion"]=[dict(r) for r in con.execute("SELECT r.correlative,l.number,l.quantity,l.unit_cost,l.expiration_date FROM inventory_stockreceiptline l JOIN inventory_stockreceipt r ON r.id=l.receipt_id ORDER BY r.correlative,l.number")]
        result["asignaciones"]=[dict(r) for r in con.execute("SELECT a.lot_snapshot_number,a.quantity,r.correlative FROM sales_salelotallocation a LEFT JOIN inventory_stockreceiptline l ON l.lot_id=a.lot_id LEFT JOIN inventory_stockreceipt r ON r.id=l.receipt_id ORDER BY r.correlative")]
    return result


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
        comparison = {
            "clave_en_formulario":key_present,"primera_ruta":first_path,
            "primero_fisico":sum(l["available_quantity"] for l in first["lotes"]),
            "primer_promedio":first["productos"][0]["average_cost"],
            "segundo_fisico":sum(l["available_quantity"] for l in second["lotes"]),
            "segundo_promedio":second["productos"][0]["average_cost"],
            "reintento_misma_constancia":first_path==replay_path,
            "reintento_igual_sin_mutacion":first["sha256"]==replay_after["sha256"],
            "clave_divergente_sin_mutacion":after["sha256"]==second["sha256"],
            "constancia_preserva_proveedor":"Proveedor original 14G" in w.locator("main").inner_text(),
            "constancia_preserva_responsable":"Almacén 14G" in w.locator("main").inner_text()}
        base.save(self.out/"comparaciones.json", comparison)
        if not FINAL:
            return
        assert all(comparison[k] for k in ("clave_en_formulario","reintento_misma_constancia",
            "reintento_igual_sin_mutacion","clave_divergente_sin_mutacion",
            "constancia_preserva_proveedor","constancia_preserva_responsable"))
        assert (comparison["primero_fisico"],comparison["primer_promedio"],comparison["segundo_fisico"],comparison["segundo_promedio"]) == (20,4.5,25,5.2)
        w.reload()
        snap("10-recarga-constancia", "ALMACENERO", w, same=renamed)
        a.reload()
        base.link(a,first_path)
        snap("11-constancia-admin", "ADMIN", a,lambda s,t:"R-00000001" in t and "Proveedor original 14G" in t,same=renamed,photo=True)
        self.denied("12-vendedor-constancia-403","VENDEDOR",v,first_path)
        base.link(w,"/inventario/entrada/")
        base.selector(w,"product").select_option(value=product_value)
        for name,value in {"number":"INVALIDO","quantity":"0","unit_cost":"6","expiration_date":expiration}.items():
            base.fill(w,"lots-0-"+name,value)
        preserved_key=base.selector(w,"idempotency_key").input_value()
        base.button(w,"Confirmar entrada")
        snap("13-cantidad-invalida","ALMACENERO",w,lambda s,t:"mayor o igual a 1" in t,same=renamed,photo=True)
        assert base.selector(w,"idempotency_key").input_value()==preserved_key
        base.fill(w,"lots-0-quantity","1")
        base.fill(w,"lots-0-expiration_date",base.datetime.now(base.ZoneInfo("America/Lima")).date().isoformat())
        base.button(w,"Confirmar entrada")
        snap("14-vencimiento-rechazado","ALMACENERO",w,lambda s,t:"posterior a hoy" in t,same=renamed)
        base.fill(w,"lots-0-number","C")
        base.fill(w,"lots-0-expiration_date",(base.datetime.fromisoformat(expiration).date()+timedelta(days=1)).isoformat())
        base.button(w,"Confirmar entrada")
        snap("15-fecha-contradictoria","ALMACENERO",w,lambda s,t:"otro vencimiento" in t,same=renamed,photo=True)
        base.link(v,"/caja/abrir/")
        base.fill(v,"opening_amount","100")
        base.button(v,"Abrir turno")
        snap("16-apertura","VENDEDOR",v,lambda s,t:s["turnos"][0]["opening_amount"]==100)
        base.link(v,"/ventas/")
        base.fill(v,"query","INT-14G")
        base.button(v,"Buscar")
        base.fill(v,"quantity","22")
        base.button(v,"Agregar")
        base.link(v,"/ventas/cobrar/")
        base.fill(v,"cash_received","220")
        base.button(v,"Confirmar cobro")
        sale=snap("17-venta-multirecepcion","VENDEDOR",v,lambda s,t:s["ventas"][0]["total_amount"]==220 and sum(l["available_quantity"] for l in s["lotes"])==3,photo=True)
        assert [(r["correlative"],r["quantity"]) for r in sale["asignaciones"]]==[(None,10),("R-00000001",10),("R-00000002",2)]
        base.link(w,"/inventario/bajas/nueva/")
        snap("18-seleccion-origen-merma","ALMACENERO",w,lambda s,t:"R-00000002" in t,photo=True)
        w.get_by_role("row").filter(has_text="R-00000002").get_by_role("link",name="Dar de baja").click()
        base.fill(w,"quantity","1")
        base.selector(w,"reason").select_option("ROBO")
        base.fill(w,"notes","Faltante ficticio en recepción 14G")
        base.button(w,"Confirmar baja")
        after_loss=snap("19-merma-origen-correcto","ALMACENERO",w,lambda s,t:sum(l["available_quantity"] for l in s["lotes"])==2,photo=True)
        base.link(a,"/inventario/stock/")
        a.get_by_role("link",name="Ver movimientos").click()
        snap("20-movimientos-tras-venta-merma","ADMIN",a,lambda s,t:all(x in t for x in ("R-00000001","R-00000002","V-00000001","+10","+5","-22","-1")),same=after_loss,photo=True)
        base.link(a,"/ventas/historial/")
        snap("21-ventas-admin","ADMIN",a,lambda s,t:"V-00000001" in t,same=after_loss)
        base.link(v,"/caja/cerrar/")
        base.fill(v,"counted_amount","320")
        base.button(v,"Cerrar turno")
        closed=snap("22-cierre","VENDEDOR",v,lambda s,t:"Exacto" in t and s["cierres"][0]["expected_amount"]==320 and s["cierres"][0]["difference"]==0,photo=True)
        base.link(w,first_path) if w.locator(f'a[href="{first_path}"]').count() else w.goto(self.base+first_path)
        snap("23-cantidad-original-preservada","ALMACENERO",w,lambda s,t:"10 UND" in t and "4,50" in t,same=closed,photo=True)


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("salida",type=Path)
    parser.add_argument("--final",action="store_true")
    args=parser.parse_args()
    FINAL=args.final
    base.prepare=prepare
    base.Journey=Journey
    if FINAL:
        base.witness=witness
    try:
        base.main(args.salida)
    finally:
        meta_path=args.salida/"ejecucion.json"
        if meta_path.exists():
            meta=json.loads(meta_path.read_text(encoding="utf-8"))
            meta.update(sublote="14-G",runner14g_sha256=base.sha(Path(__file__).read_bytes()))
            base.save(meta_path,meta)
