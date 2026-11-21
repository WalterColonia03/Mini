"""Recorrido 14-E para F-COSTO; salida nueva, --final exige el contrato corregido."""
from __future__ import annotations

import argparse
import importlib.util
import sqlite3
from contextlib import closing
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
BASE_RUNNER = HERE.parents[1] / "14-D-20261113/navegador/recorrido.py"
spec = importlib.util.spec_from_file_location("audit14d_browser_support", BASE_RUNNER)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
fill, button, link, selector = base.fill, base.button, base.link, base.selector
base.ACTORS = {"ADMIN":"Administración 14E", "ALMACENERO":"Almacén 14E", "VENDEDOR":"Venta 14E"}
PRODUCT = "F-COSTO 14E"
BARCODE = "INT-F-COSTO-14E"
EXPIRED, CURRENT, INCOMING = "14E-A-VENCIDO", "14E-B-VIGENTE", "14E-C-ENTRADA"
original_prepare, original_witness = base.prepare, base.witness
FINAL = False


def prepare(db, password):
    original_prepare(db, password)
    from catalog.models import Category, Product
    from identity.models import Account
    from inventory.models import InitialInventoryLoad, Lot, Supplier
    from django.db import connection
    today = datetime.now(ZoneInfo("America/Lima")).date()
    cat = Category.objects.create(name="Familia 14E")
    product = Product.objects.create(name=PRODUCT, category=cat, barcode=BARCODE,
        barcode_normalized=BARCODE, barcode_type="INTERNAL", search_name=Product.normalize_search_name(PRODUCT),
        sale_price=Decimal("8.00"), average_cost=Decimal("3.0000"), minimum_stock=5, unit="UND", controls_expiration=True)
    supplier = Supplier.objects.create(name="Proveedor 14E", ruc="20000000015")
    actor = Account.objects.get(email="almacenero@example.invalid")
    load = InitialInventoryLoad.objects.create(product=product, responsible=actor)
    for number, qty, days in [(EXPIRED,8,-1),(CURRENT,10,7)]:
        Lot.objects.create(product=product, initial_load=load, supplier=supplier, responsible=actor,
            number=number, number_normalized=number, initial_quantity=qty, available_quantity=qty,
            unit_cost=Decimal("3.0000"), expiration_date=today+timedelta(days=days))
    connection.close()


def witness(db):
    state = original_witness(db)
    with closing(sqlite3.connect(db.as_uri()+"?mode=ro",uri=True)) as con:
        con.row_factory = sqlite3.Row
        for table, key in [("inventory_stockwriteoff","costos_baja"),("inventory_physicaladjustment","costos_ajuste")]:
            fields = [r["name"] for r in con.execute(f"PRAGMA table_info({table})")]
            wanted = [f for f in ("id","quantity","delta","unit_cost","cost_before","cost_after") if f in fields]
            state[key] = {"columnas":fields, "filas":[dict(r) for r in con.execute(f"SELECT {','.join(wanted)} FROM {table} ORDER BY id")]}
    return state


class CostJourney(base.Journey):
    def check(self, key, actor, page, qty, cost, photo=True, same=None):
        state = self.observe(key, actor, page, lambda s,t: sum(base.available(s)) == qty, same=same, photo=photo)
        actual = Decimal(str(state["productos"][0]["average_cost"]))
        record = {"paso":key, "fisico":qty, "promedio_esperado":cost, "promedio_observado":str(actual),
                  "resultado":"CUMPLE" if actual == Decimal(cost) else "INCUMPLE"}
        self.results.append(record)
        base.save(self.out/"comparaciones-costo.json", self.results)
        if FINAL:
            assert record["resultado"] == "CUMPLE", str(record)
            if key.endswith("-costo") or key == "03-recepcion-confirmada":
                shown = page.locator("dt",has_text="Costo promedio").locator("..").locator("dd").inner_text()
                expected = "S/ " + f"{Decimal(cost):.2f}".replace(".",",")
                assert shown == expected, {"esperado":expected,"observado":shown}
        return state

    def inventory(self, page, actor, key, qty, cost):
        link(page,"/inventario/stock/")
        self.check(key+"-stock",actor,page,qty,cost)
        page.get_by_role("link",name="Ver carga",exact=True).click()
        return self.check(key+"-costo",actor,page,qty,cost)

    def writeoff(self,page,key,lot,qty,reason,remaining,cost):
        link(page,"/inventario/bajas/nueva/")
        page.get_by_role("row").filter(has_text=lot).get_by_role("link").click()
        fill(page,"quantity",str(qty))
        selector(page,"reason").select_option(reason)
        if reason != "VENCIMIENTO":
            fill(page,"notes","Conteo y daño documentado para prueba ficticia F-COSTO14E")
        button(page,"Confirmar baja")
        return self.check(key,"ALMACENERO",page,remaining,cost)

    def run(self,browser,password):
        self.results = []
        a=self.connect(browser,"ADMIN",password)
        w=self.connect(browser,"ALMACENERO",password)
        v=self.connect(browser,"VENDEDOR",password)
        initial = self.inventory(a,"ADMIN","01-inicial",18,"3.0000")
        base.save(self.out/"fixture.json",{
            "creacion":"Fixture ORM controlada previa a acciones UI",
            "fecha_lima":datetime.now(ZoneInfo("America/Lima")).date().isoformat(),
            "datos":initial,"contrato":"DOC-03AH-01/C-01..02","lotes":"A vence ayer, B hoy+7; recepción C hoy+30",
            "aislamiento":"SQLite nueva, cuentas ficticias, sin copia de datos operativos"})
        link(w,"/inventario/entrada/")
        self.observe("02-recepcion-formulario","ALMACENERO",w)
        for name,match in [("product",PRODUCT),("supplier","Proveedor 14E")]:
            field=selector(w,name)
            label=next(x for x in field.locator("option").all_text_contents() if match in x)
            field.select_option(label=label)
        today=datetime.now(ZoneInfo("America/Lima")).date()
        for field,value in [("number",INCOMING),("quantity","10"),("unit_cost","6.0000"),
                            ("expiration_date",(today+timedelta(days=30)).isoformat())]:
            fill(w,"lots-0-"+field,value)
        if FINAL:
            before=witness(self.db)
            fill(w,"lots-0-unit_cost","0")
            button(w,"Confirmar entrada")
            self.observe("02b-costo-cero-rechazado","ALMACENERO",w,
                lambda s,t: "mayor" in t and "costo" in t.casefold(),same=before,photo=True)
            fill(w,"lots-0-unit_cost","6.0000")
        button(w,"Confirmar entrada")
        self.check("03-recepcion-confirmada","ALMACENERO",w,28,"4.0714")
        self.inventory(a,"ADMIN","04-admin-recepcion",28,"4.0714")
        link(v,"/caja/abrir/")
        fill(v,"opening_amount","100")
        button(v,"Abrir turno")
        link(v,"/ventas/")
        fill(v,"query",BARCODE)
        button(v,"Buscar")
        self.observe("05-busqueda-vigentes","VENDEDOR",v,
            lambda s,t: v.locator("tbody tr").first.locator("td").all_inner_texts()[2]=="20",photo=True)
        fill(v,"quantity","1")
        button(v,"Agregar")
        link(v,"/ventas/cobrar/")
        fill(v,"cash_received","10")
        button(v,"Confirmar cobro")
        self.check("06-venta-confirmada","VENDEDOR",v,27,"4.0714")
        assert "Costo promedio" not in v.locator("body").inner_text()
        assert "Costo unitario" not in v.locator("body").inner_text()
        self.inventory(a,"ADMIN","07-admin-postventa",27,"4.0714")
        self.writeoff(w,"08-merma-una",CURRENT,1,"DAÑO",26,"4.0714")
        self.inventory(a,"ADMIN","09-admin-postmerma",26,"4.0714")
        link(a,"/inventario/stock/")
        a.get_by_role("link",name="Ver movimientos").click()
        self.check("10-movimientos","ADMIN",a,26,"4.0714")
        link(a,"/ventas/historial/")
        self.check("11-historial","ADMIN",a,26,"4.0714")
        self.writeoff(w,"12-baja-vencido",EXPIRED,8,"VENCIMIENTO",18,"4.0714")
        self.writeoff(w,"13-baja-vigente",CURRENT,8,"DAÑO",10,"4.0714")
        last = self.writeoff(w,"14-agotamiento",INCOMING,10,"DAÑO",0,"0.0000")
        self.inventory(a,"ADMIN","15-admin-cero",0,"0.0000")
        link(v,"/caja/cerrar/")
        fill(v,"counted_amount","108.00")
        button(v,"Cerrar turno")
        self.observe("16-cierre","VENDEDOR",v,
            lambda s,t: s["cierres"][0]["expected_amount"]==108 and s["cierres"][0]["difference"]==0 and "Exacto" in t,photo=True)
        link(a,"/ventas/historial/")
        a.get_by_role("link",name="V-00000001").click()
        self.check("17-historico-tras-agotar","ADMIN",a,0,"0.0000")
        final=witness(self.db)
        sale_cost=Decimal(str(final["lineas"][0]["unit_cost"]))
        self.results.append({"paso":"snapshot-venta","costo_esperado":"4.0714","costo_observado":str(sale_cost),
            "resultado":"CUMPLE" if sale_cost==Decimal("4.0714") else "INCUMPLE"})
        if FINAL:
            assert sale_cost==Decimal("4.0714")
            assert len(final["costos_baja"]["filas"]) == 4
            assert "unit_cost" in final["costos_baja"]["columnas"]
            assert all(Decimal(str(r["unit_cost"]))==Decimal("4.0714")
                       for r in final["costos_baja"]["filas"])
        base.save(self.out/"comparaciones-costo.json",self.results)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("salida",type=Path)
    parser.add_argument("--final",action="store_true")
    args=parser.parse_args()
    FINAL=args.final
    base.prepare,base.witness,base.Journey=prepare,witness,CostJourney
    base.main(args.salida)
    metadata=__import__("json").loads((args.salida/"ejecucion.json").read_text(encoding="utf-8"))
    metadata.update(sublote="14-E",modo="FINAL" if FINAL else "BEFORE",runner14e_sha256=base.sha(Path(__file__).read_bytes()))
    base.save(args.salida/"ejecucion.json",metadata)
