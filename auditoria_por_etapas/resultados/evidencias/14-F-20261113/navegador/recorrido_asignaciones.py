"""14-F, asignaciones y fotografía histórica. Salida nueva; --final exige historia preservada."""
from __future__ import annotations
import argparse
import importlib.util
import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime,timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("audit14d_support",HERE.parents[1]/"14-D-20261113/navegador/recorrido.py")
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
fill,button,link,selector=base.fill,base.button,base.link,base.selector
base.ACTORS={"ADMIN":"Administración 14F","ALMACENERO":"Almacén 14F","VENDEDOR":"Venta original 14F"}
original_prepare,original_witness=base.prepare,base.witness
FIRST,SECOND="Zeta 14F","Alfa 14F"
FINAL=False


def prepare(db,password):
    original_prepare(db,password)
    from catalog.models import Category,Product
    from identity.models import Account
    from inventory.models import InitialInventoryLoad,Lot
    from cash.models import CashRegister,CashShift
    from sales.models import Sale,SaleLine
    from django.db import connection
    today=datetime.now(ZoneInfo("America/Lima")).date()
    cat=Category.objects.create(name="Familia14F")
    actor=Account.objects.get(email="almacenero@example.invalid")
    products={}
    for name,barcode,price,lots in [(FIRST,"INT-14F-ZETA","3.55",[("14F-A",3,7),("14F-B",7,30)]),
                                    (SECOND,"INT-14F-ALFA","2.00",[("14F-C",2,40)])]:
        product=Product.objects.create(name=name,category=cat,barcode=barcode,barcode_normalized=barcode,
            barcode_type="INTERNAL",search_name=Product.normalize_search_name(name),
            sale_price=Decimal(price),average_cost=Decimal("1.0000"),minimum_stock=1,unit="UND",controls_expiration=True)
        load=InitialInventoryLoad.objects.create(product=product,responsible=actor)
        for number,qty,days in lots:
            Lot.objects.create(product=product,initial_load=load,responsible=actor,
                number=number,number_normalized=number,initial_quantity=qty,available_quantity=qty,
                unit_cost=Decimal("1.0000"),expiration_date=today+timedelta(days=days))
        products[name]=product
    seller=Account.objects.get(email="vendedor@example.invalid")
    register=CashRegister.objects.get(code="CAJA-01")
    oldshift=CashShift.objects.create(cash_register=register,seller=seller,opening_amount=Decimal("0"),status="CLOSED")
    legacy=Sale.objects.create(cash_shift=oldshift,seller=seller,total_amount=Decimal("3.55"),
        base_amount=Decimal("3.01"),igv_amount=Decimal("0.54"),discount_amount=Decimal("0"),
        cash_received=Decimal("4"),change_given=Decimal("0.45"),correlative="V-00000000",idempotency_key=uuid.uuid4())
    SaleLine.objects.create(sale=legacy,product=products[FIRST],product_snapshot_name=FIRST,
        product_snapshot_barcode=products[FIRST].barcode,quantity=1,unit_price=Decimal("3.55"),amount=Decimal("3.55"),unit_cost=None)
    connection.close()


def witness(db):
    state=original_witness(db)
    with closing(sqlite3.connect(db.as_uri()+"?mode=ro",uri=True)) as con:
        con.row_factory=sqlite3.Row
        names=[r["name"] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'sales_%'")]
        state["estructura_ventas"]={}
        state["historia_ventas"]={}
        for table in names:
            fields=[r["name"] for r in con.execute(f"PRAGMA table_info({table})")]
            state["estructura_ventas"][table]=fields
            if table in {"sales_sale","sales_saleline"} or "allocation" in table:
                public=[f for f in fields if f not in {"idempotency_key","draft_signature"}]
                state["historia_ventas"][table]=[dict(r) for r in con.execute(f"SELECT {','.join(public)} FROM {table} ORDER BY id")]
    return state


class AllocationJourney(base.Journey):
    def record(self,key,role,page,photo=True):
        state=self.observe(key,role,page,photo=photo)
        return state

    def receipt_values(self,page):
        receipt=page.locator("#constancia-interna")
        values={}
        for name in ("Vendedor","Caja"):
            values[name]=receipt.locator("dt",has_text=name).locator("..").locator("dd").inner_text()
        values["productos"]=receipt.locator("tbody tr td:first-child").all_inner_texts()
        values["texto"]=receipt.inner_text()
        return values

    def run(self,browser,password):
        a=self.connect(browser,"ADMIN",password)
        w=self.connect(browser,"ALMACENERO",password)
        v=self.connect(browser,"VENDEDOR",password)
        link(w,"/inventario/stock/")
        initial=self.record("01-stock-inicial","ALMACENERO",w)
        base.save(self.out/"fixture.json",{"canal":"ORM controlado antes de UI","fecha_lima":datetime.now(ZoneInfo("America/Lima")).date().isoformat(),
            "dato":"Zeta A3/B7; Alfa C2; costo1; fechas hoy+7/+30/+40. Legado V00000000 sin costo/asignación/snapshots, turno cerrado.",
            "nota":"Saldos iniciales fijados; no se deriva consumo de la venta legacy ni se presenta como carga UI.",
            "testigo":initial})
        link(v,"/caja/abrir/")
        fill(v,"opening_amount","100")
        button(v,"Abrir turno")
        for barcode,qty in [("INT-14F-ZETA","4"),("INT-14F-ALFA","1")]:
            link(v,"/ventas/")
            fill(v,"query",barcode)
            button(v,"Buscar")
            fill(v,"quantity",qty)
            button(v,"Agregar")
        self.record("02-borrador-dos-lineas","VENDEDOR",v)
        link(v,"/ventas/cobrar/")
        self.record("03-revision-cobro","VENDEDOR",v)
        fill(v,"cash_received","20")
        button(v,"Confirmar cobro")
        sold=self.record("04-constancia-original","VENDEDOR",v)
        expected_quantities={l["number"]:l["available_quantity"] for l in sold["lotes"]}
        assert expected_quantities=={"14F-A":0,"14F-B":6,"14F-C":1}
        original=self.receipt_values(v)
        receipt_url=v.url
        if FINAL:
            assert original["productos"]==[FIRST,SECOND]
            assert original["Vendedor"] == "Venta original 14F" and original["Caja"] == "CAJA-01"
            history = sold["historia_ventas"]
            sale = next(s for s in history["sales_sale"] if s["correlative"]=="V-00000001")
            assert sale["seller_snapshot_name"] == original["Vendedor"]
            assert sale["cash_register_snapshot_code"] == original["Caja"]
            lines = sorted((r for r in history["sales_saleline"] if r["sale_id"]==sale["id"]),key=lambda r:r["position"])
            assert [(r["position"],r["product_snapshot_name"],r["quantity"]) for r in lines] == [(1,FIRST,4),(2,SECOND,1)]
            allocations = history["sales_salelotallocation"]
            for line, expected in zip(lines,[{"14F-A":3,"14F-B":1},{"14F-C":1}],strict=True):
                actual={r["lot_snapshot_number"]:r["quantity"] for r in allocations if r["line_id"]==line["id"]}
                assert actual == expected and sum(actual.values()) == line["quantity"]
            assert len(allocations) == 3
        link(w,"/inventario/stock/")
        self.record("05-stock-posterior","ALMACENERO",w)
        link(a,"/inventario/stock/")
        a.get_by_role("row").filter(has_text=FIRST).get_by_role("link",name="Ver movimientos").click()
        self.record("06-movimientos-original","ADMIN",a)
        movement_url=a.url
        if FINAL:
            current_row=a.get_by_role("row").filter(has_text="Venta V-00000001")
            assert "14F-A · 3 UND" in current_row.inner_text() and "14F-B · 1 UND" in current_row.inner_text()
            assert "Costo unitario de salida: S/ 1,0000" in current_row.inner_text()
            old_row=a.get_by_role("row").filter(has_text="Venta V-00000000")
            assert "No disponibles" in old_row.inner_text() and "Costo unitario de salida: No disponible" in old_row.inner_text()
            self.denied("06b-vendedor-movimientos-403","VENDEDOR",v,movement_url.replace(self.base,""))
            base.save(self.out/"movimientos-confrontados.json",{"nueva":current_row.inner_text(),"legado":old_row.inner_text()})
        with closing(sqlite3.connect(self.db)) as con:
            con.execute("UPDATE identity_account SET display_name=? WHERE email=?",("Venta renombrada 14F","vendedor@example.invalid"))
            con.execute("UPDATE cash_cashregister SET code=? WHERE code=?",("CAJA-RENOMBRADA-14F","CAJA-01"))
            con.execute("UPDATE catalog_product SET name=?,barcode=? WHERE name=?",("Producto renombrado 14F","INT-14F-RENOMBRADO",FIRST))
            con.commit()
        base.save(self.out/"control-maestros.json",{"canal":"Control técnico fixture SQLite local después de confirmar",
            "cambios":{"vendedor":["Venta original 14F","Venta renombrada 14F"],"caja":["CAJA-01","CAJA-RENOMBRADA-14F"],
                       "producto":[FIRST,"Producto renombrado 14F"],"barcode":["INT-14F-ZETA","INT-14F-RENOMBRADO"]},
            "alcance":"Sólo datos ficticios. No es prueba de UI para editar maestros."})
        v.goto(receipt_url)
        changed=self.record("07-constancia-reabierta","VENDEDOR",v)
        after=self.receipt_values(v)
        comparison={"original":original,"despues_cambio_maestros":after,
                    "misma_historia":original==after,"esperado_vendedor":"Venta original 14F","esperado_caja":"CAJA-01",
                    "orden_esperado":[FIRST,SECOND]}
        base.save(self.out/"comparacion-historia.json",comparison)
        if FINAL:
            assert comparison["misma_historia"]
            assert "Costo" not in after["texto"]
        a.reload()
        self.record("08-movimientos-tras-cambio","ADMIN",a)
        link(a,"/ventas/historial/")
        self.record("09-historial","ADMIN",a)
        a.get_by_role("link",name="V-00000000",exact=True).click()
        self.record("10-constancia-legacy","ADMIN",a)
        if FINAL:
            legacy=self.receipt_values(a)
            assert legacy["Vendedor"] == legacy["Caja"] == "No disponible (registro anterior)"
            assert "El orden original de los productos no está disponible en este registro." in legacy["texto"]
        link(v,"/caja/cerrar/")
        fill(v,"counted_amount","116.20")
        button(v,"Cerrar turno")
        self.record("11-cierre","VENDEDOR",v)
        final=witness(self.db)
        assert final["cierres"][0]["expected_amount"]==116.2
        base.save(self.out/"testigo-final.json",final)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("salida",type=Path)
    parser.add_argument("--final",action="store_true")
    args=parser.parse_args()
    FINAL=args.final
    base.prepare,base.witness,base.Journey=prepare,witness,AllocationJourney
    base.main(args.salida)
    metadata=json.loads((args.salida/"ejecucion.json").read_text(encoding="utf-8"))
    metadata.update(sublote="14-F",modo="FINAL" if FINAL else "BEFORE",runner14f_sha256=base.sha(Path(__file__).read_bytes()))
    base.save(args.salida/"ejecucion.json",metadata)
