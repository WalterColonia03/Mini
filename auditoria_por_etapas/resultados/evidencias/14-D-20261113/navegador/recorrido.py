"""Primera pasada 14-D. Desde la raíz: python ruta/recorrido.py DIRECTORIO_NUEVO.

Usar Python del proyecto con playwright instalado, y Chrome estable (o E14_CHROME).
El servidor de prueba escucha en loopback; SQLite, secretos y cuentas son de un solo uso.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import tempfile
import threading
from contextlib import closing
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlsplit
from wsgiref.simple_server import WSGIRequestHandler, make_server
from zoneinfo import ZoneInfo


ROOT = next(p for p in Path(__file__).resolve().parents if (p / "r1-pmv/manage.py").is_file())
PROJECT = ROOT / "r1-pmv"
CAT, PRODUCT, BAR, SUP = "Familia 14D", "Harina 14D", "INT-14D-HARINA", "Proveedor 14D"
EARLY, LATE = "14D-PRIMERO", "14D-SEGUNDO"
ACTORS = {"ADMIN": "Administración 14D", "ALMACENERO": "Almacén 14D", "VENDEDOR": "Venta 14D"}
ROLE_NAMES = {"ADMIN": "Administrador", "ALMACENERO": "Almacenero", "VENDEDOR": "Vendedor"}


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build():
    extensions = {".py", ".html", ".css", ".js"}
    files = sorted(p for directory in ("identity", "catalog", "inventory", "cash", "sales", "config", "templates", "app_platform")
                   for p in (PROJECT/directory).rglob("*") if p.is_file() and p.suffix in extensions)
    manifest = {p.relative_to(PROJECT).as_posix(): sha(p.read_bytes()) for p in files}
    return {"sha256": sha(json.dumps(manifest, sort_keys=True).encode()), "archivos": manifest,
            "head": subprocess.check_output(["git", "-C", str(PROJECT), "rev-parse", "HEAD"], text=True).strip()}


def prepare(db, password):
    sys.path.insert(0, str(PROJECT))
    os.environ.update(APP_ENV="test", DJANGO_DEBUG="false", DJANGO_SETTINGS_MODULE="config.settings",
                      DJANGO_SECRET_KEY=secrets.token_urlsafe(48), DJANGO_ALLOWED_HOSTS="127.0.0.1")
    from django.conf import settings
    settings.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": str(db)}}
    import django
    django.setup()
    from django.core.management import call_command
    from django.db import connection
    from identity.models import Account, Role
    from cash.models import CashRegister
    assert Path(connection.settings_dict["NAME"]).resolve() == db and not db.exists()
    call_command("migrate", verbosity=0, interactive=False)
    for code, name in ACTORS.items():
        role, _ = Role.objects.get_or_create(code=code, defaults={"name": ROLE_NAMES[code]})
        Account.objects.create_user(email=code.lower() + "@example.invalid", password=password,
                                    display_name=name, role=role)
    CashRegister.objects.get_or_create(code="CAJA-01", defaults={"is_active": True})
    connection.close()


def witness(db):
    """Inspect every catalogue, inventory, sales and cash table, plus non-secret role/account state."""
    with closing(sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)) as con:
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                  if r[0].startswith(("catalog_", "inventory_", "sales_", "cash_"))]
        digest, counts = {}, {}
        for table in tables:
            rows = list(con.execute(f'SELECT * FROM "{table}" ORDER BY 1'))
            counts[table] = len(rows)
            digest[table] = sha(json.dumps(rows, ensure_ascii=True).encode())
        accounts = list(con.execute("SELECT r.code,a.is_active FROM identity_account a "
                                    "JOIN identity_role r ON r.id=a.role_id ORDER BY r.code"))
        digest["identity_role_membership_active"] = sha(json.dumps(accounts).encode())
        def rows(sql):
            con.row_factory = sqlite3.Row
            return [dict(row) for row in con.execute(sql)]
        return {
            "sha256": sha(json.dumps(digest, sort_keys=True).encode()), "por_tabla": digest, "filas": counts,
            "cuentas_rol_activas": accounts,
            "categorias": rows("SELECT name,is_active,state_version FROM catalog_category ORDER BY name"),
            "productos": rows("SELECT name,barcode,sale_price,minimum_stock,average_cost,is_active FROM catalog_product"),
            "proveedores": rows("SELECT name,ruc,is_active FROM inventory_supplier"),
            "lotes": rows("SELECT l.number,l.initial_quantity,l.available_quantity,l.unit_cost,l.expiration_date,"
                          "p.name AS producto,s.name AS proveedor,a.display_name AS autor_carga FROM inventory_lot l "
                          "JOIN catalog_product p ON p.id=l.product_id LEFT JOIN inventory_supplier s ON s.id=l.supplier_id "
                          "LEFT JOIN inventory_initialinventoryload i ON i.id=l.initial_load_id "
                          "LEFT JOIN identity_account a ON a.id=i.responsible_id ORDER BY l.number"),
            "borrador": rows("SELECT d.status,l.quantity,l.unit_price FROM sales_saledraft d "
                             "LEFT JOIN sales_saledraftline l ON d.id=l.draft_id"),
            "ventas": rows("SELECT s.correlative,s.total_amount,s.base_amount,s.igv_amount,s.discount_amount,"
                           "s.cash_received,s.change_given,a.display_name AS vendedor, t.opening_amount "
                           "FROM sales_sale s JOIN identity_account a ON a.id=s.seller_id "
                           "JOIN cash_cashshift t ON t.id=s.cash_shift_id"),
            "lineas": rows("SELECT product_snapshot_name,product_snapshot_barcode,quantity,unit_price,amount,unit_cost "
                           "FROM sales_saleline"),
            "bajas": rows("SELECT w.correlativo,l.number,w.quantity,w.reason,w.notes,a.display_name AS responsable "
                          "FROM inventory_stockwriteoff w JOIN inventory_lot l ON l.id=w.lot_id "
                          "JOIN identity_account a ON a.id=w.responsible_id"),
            "turnos": rows("SELECT t.status,t.opening_amount,a.display_name AS vendedor FROM cash_cashshift t "
                           "JOIN identity_account a ON a.id=t.seller_id"),
            "cierres": rows("SELECT c.counted_amount,c.expected_amount,c.difference,a.display_name AS autor "
                            "FROM cash_cashshiftclose c JOIN identity_account a ON a.id=c.closed_by_id"),
        }


class QuietLog(WSGIRequestHandler):
    def log_message(self, *args):
        pass


class Journey:
    def __init__(self, db, out, base):
        self.db, self.out, self.base = db, out, base
        self.steps, self.http, self.roles = [], [], {}

    def observe(self, key, actor, page, condition=None, same=None, photo=False):
        page.wait_for_load_state("load")
        state = witness(self.db)
        content = page.locator("body").inner_text()
        if condition is not None and not condition(state, content):
            raise AssertionError(f"Testigo funcional discordante en {key}")
        if same is not None:
            assert state["sha256"] == same["sha256"], f"Mutación inesperada en {key}"
        fields = page.locator("form input:not([type=hidden]):not([type=password]), form select, form textarea").evaluate_all(
            """es => es.filter(e=>e.offsetWidth||e.offsetHeight).map(e=>({
                campo:e.name, etiqueta:[...(e.labels||[])].map(l=>l.innerText.trim()).join(' '),
                tipo:e.type, valor:e.tagName==='SELECT' ? e.selectedOptions[0]?.text : e.value,
                opciones:e.tagName==='SELECT' ? [...e.options].map(o=>o.text) : undefined,
                obligatorio:e.required, min:e.getAttribute('min'), max:e.getAttribute('max'),
                paso:e.getAttribute('step'), longitud:e.getAttribute('maxlength')}))""")
        data = {"id": key, "rol": actor, "utc": datetime.now(timezone.utc).isoformat(),
                "ruta": urlsplit(page.url).path, "texto_visible": content, "controles": fields,
                "testigo": state, "sin_mutacion_verificada": same is not None}
        save(self.out / (key + ".json"), data)
        if photo:
            page.screenshot(path=self.out / (key + ".jpg"), type="jpeg", quality=68, full_page=True)
        self.steps.append(key)
        return state

    def connect(self, browser, actor, password):
        ctx = browser.new_context(locale="es-PE", timezone_id="America/Lima", viewport={"width": 1280, "height": 900})
        page = ctx.new_page()
        page.set_default_timeout(6000)
        page.on("response", lambda r: self.http.append({"rol": actor, "metodo": r.request.method,
                "ruta": urlsplit(r.url).path, "http": r.status}) if r.request.resource_type == "document" else None)
        page.goto(self.base)
        fill(page, "email", actor.lower() + "@example.invalid")
        fill(page, "password", password)
        button(page, "Iniciar sesión")
        page.wait_for_url("**/inicio/")
        self.roles[actor] = page
        return page

    def denied(self, key, actor, page, path):
        before = witness(self.db)
        reply = page.goto(self.base + path)
        assert reply.status == 403
        self.observe(key, actor, page, same=before, photo=True)
        page.go_back()

    def direct_denied(self, key, actor, page, path, payload):
        before = witness(self.db)
        token = page.locator('[name="csrfmiddlewaretoken"]').first.input_value()
        response = page.request.post(self.base + path, form={**payload, "csrfmiddlewaretoken": token})
        assert response.status == 403
        assert "No tiene permiso" in response.text() or "Acceso denegado" in response.text()
        after = witness(self.db)
        assert before["sha256"] == after["sha256"]
        save(self.out/(key+".json"), {"id":key, "rol":actor, "ruta":path, "metodo":"POST",
             "canal":"Solicitud HTTP directa autenticada con sesión del navegador y CSRF válido",
             "http":response.status, "testigo_antes":before, "testigo_despues":after,
             "sin_mutacion_verificada":True, "utc":datetime.now(timezone.utc).isoformat()})
        self.steps.append(key)

    def run(self, browser, password):
        A, W, V = ACTORS
        a = self.connect(browser, A, password)
        w = self.connect(browser, W, password)
        v = self.connect(browser, V, password)
        snap = self.observe
        for key, actor, page in [("01-admin", A, a), ("02-almacen", W, w), ("03-venta", V, v)]:
            snap(key, actor, page)
        self.denied("04-admin-apertura-403", A, a, "/caja/abrir/")
        link(a, "/productos/categorias/")
        link(a, "/productos/categorias/nueva/")
        snap("05-alta-categoria", A, a)
        self.direct_denied("05b-admin-carga-POST403", A, a, "/inventario/carga-inicial/", {})
        fill(a, "name", CAT)
        button(a, "Guardar")
        snap("06-categoria-guardada", A, a, lambda s,t: CAT in t and s["categorias"][0]["name"] == CAT)
        link(a, "/productos/nuevo/")
        snap("07-alta-producto", A, a)
        fill(a, "name", PRODUCT)
        selector(a, "barcode_type").select_option("INTERNAL")
        fill(a, "barcode", BAR)
        selector(a, "category").select_option(label=CAT)
        fill(a, "sale_price", "3.55")
        fill(a, "minimum_stock", "5")
        button(a, "Registrar producto")
        snap("08-producto-guardado", A, a, lambda s,t: PRODUCT in t and s["productos"][0]["barcode"] == BAR and not s["lotes"])
        link(a, "/inventario/proveedores/")
        link(a, "/inventario/proveedores/nuevo/")
        snap("09-alta-proveedor", A, a)
        fill(a, "name", SUP)
        fill(a, "ruc", "20000000014")
        button(a, "Guardar")
        snap("10-proveedor-guardado", A, a, lambda s,t: SUP in t and s["proveedores"][0]["ruc"] == "20000000014")
        self.denied("11-almacen-historial-403", W, w, "/ventas/historial/")
        link(w, "/inventario/carga-inicial/")
        snap("12-carga-selecciones", W, w)
        self.direct_denied("12b-almacen-apertura-POST403", W, w, "/caja/abrir/", {"opening_amount":"100.00"})
        for name, match in [("product", PRODUCT), ("supplier", SUP)]:
            field = selector(w, name)
            label = next(o for o in field.locator("option").all_text_contents() if match in o)
            field.select_option(label=label)
        today = datetime.now(ZoneInfo("America/Lima")).date()
        for i, (lot, qty, offset) in enumerate([(EARLY, 3, 0), (LATE, 7, 30)]):
            for name, val in [("number", lot), ("quantity", str(qty)), ("unit_cost", "2.0000"),
                              ("expiration_date", (today + timedelta(days=offset)).isoformat())]:
                fill(w, f"lots-{i}-{name}", val)
        before = witness(self.db)
        button(w, "Confirmar existencias")
        snap("13-carga-vencida-rechazada", W, w, lambda s,t: "posterior a hoy en Lima" in t, same=before, photo=True)
        fill(w, "lots-0-expiration_date", (today + timedelta(days=7)).isoformat())
        button(w, "Confirmar existencias")
        snap("14-existencias-confirmadas", W, w, lambda s,t: "Carga inicial confirmada" in t
             and available(s) == [3,7] and all(l["proveedor"] == SUP and l["autor_carga"] == ACTORS[W] for l in s["lotes"]), photo=True)
        self.denied("15-vendedor-stock-403", V, v, "/inventario/stock/")
        link(v, "/caja/abrir/")
        snap("16-apertura", V, v)
        fill(v, "opening_amount", "100.00")
        button(v, "Abrir turno")
        snap("17-turno-abierto", V, v, lambda s,t: s["turnos"][0]["status"] == "OPEN" and "CAJA-01" in t)
        link(v, "/ventas/")
        fill(v, "query", BAR)
        button(v, "Buscar")
        snap("18-busqueda", V, v, lambda s,t: PRODUCT in t and "10" in v.locator("table tbody tr").first.inner_text())
        fill(v, "quantity", "4")
        button(v, "Agregar")
        snap("19-borrador", V, v, lambda s,t: "4 und." in t and s["borrador"][0]["quantity"] == 4 and available(s) == [3,7] and not s["ventas"])
        link(v, "/ventas/cobrar/")
        snap("20-cobro-en-revision", V, v)
        assert v.locator('[name="discount_amount"]').count() == 0
        self.direct_denied("20b-vendedor-categoria-POST403", V, v, "/productos/categorias/nueva/", {"name":"Rechazada14D"})
        link(a, "/productos/categorias/")
        button(a, "Desactivar")
        snap("21-confirmar-desactivacion", A, a)
        button(a, "Confirmar desactivación")
        before = snap("22-categoria-inactiva", A, a, lambda s,t: "Inactiva" in t and s["categorias"][0]["is_active"] == 0)
        fill(v, "cash_received", "20.00")
        button(v, "Confirmar cobro")
        snap("23-borrador-inhabilitado", V, v, lambda s,t: "disponible para la venta" in t, same=before, photo=True)
        button(a, "Activar")
        button(a, "Confirmar activación")
        before = snap("24-categoria-reactivada", A, a, lambda s,t: "Activa" in t and s["categorias"][0]["is_active"] == 1)
        link(v, "/ventas/")
        link(v, "/ventas/cobrar/")
        fill(v, "cash_received", "14.19")
        button(v, "Confirmar cobro")
        snap("25-efectivo-insuficiente", V, v, lambda s,t: "insuficiente" in t.casefold(), same=before)
        fill(v, "cash_received", "20.00")
        assert v.locator("#checkout-change").inner_text().replace(".", ",") == "S/ 5,80"
        snap("26-cobro-previo", V, v, lambda s,t: "5,80" in t or "5.80" in t, photo=True)
        button(v, "Confirmar cobro")
        def sale_ok(s,t):
            return ("CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO" in t and "V-00000001" in t
                    and available(s) == [0,6] and len(s["ventas"]) == 1 and s["lineas"][0]["quantity"] == 4
                    and tuple(s["ventas"][0][k] for k in ("total_amount", "cash_received", "change_given")) == (14.2,20,5.8))
        before = snap("27-constancia", V, v, sale_ok, photo=True)
        v.reload()
        snap("28-constancia-releida", V, v, sale_ok, same=before)
        link(w, "/inventario/stock/")
        snap("29-stock-tras-venta", W, w, lambda s,t: PRODUCT in t and w.locator("tbody tr").first.locator("td").all_inner_texts()[2:4] == ["6","6"], photo=True)
        link(w, "/inventario/bajas/nueva/")
        w.get_by_role("row").filter(has_text=LATE).get_by_role("link").click()
        snap("30-merma-formulario", W, w)
        fill(w, "quantity", "1")
        selector(w, "reason").select_option("VENCIMIENTO")
        button(w, "Confirmar baja")
        snap("30b-merma-causa-incompatible", W, w, lambda s,t: "aún no ha vencido" in t, same=before, photo=True)
        fill(w, "quantity", "7")
        selector(w, "reason").select_option("DAÑO")
        fill(w, "notes", "Envase roto en estante de prueba 14D")
        button(w, "Confirmar baja")
        snap("31-merma-excesiva", W, w, lambda s,t: "supera las existencias" in t, same=before)
        fill(w, "quantity", "1")
        button(w, "Confirmar baja")
        after = snap("32-merma-confirmada", W, w, lambda s,t: len(s["bajas"]) == 1 and s["bajas"][0]["correlativo"] in t and available(s) == [0,5], photo=True)
        link(a, "/inventario/stock/")
        snap("33-stock-admin", A, a, lambda s,t: a.locator("tbody tr").first.locator("td").all_inner_texts()[2:4] == ["5","5"], same=after)
        a.get_by_role("link",name="Ver movimientos").click()
        snap("34-movimientos", A, a, lambda s,t: all(x in t for x in [PRODUCT, EARLY, LATE, "V-00000001", s["bajas"][0]["correlativo"], "+3","+7","-4","-1"]), same=after, photo=True)
        link(a, "/ventas/historial/")
        snap("35-ventas-admin", A, a, lambda s,t: "V-00000001" in t and ACTORS[V] in t and "5,80" in t.replace(".",","), same=after, photo=True)
        a.get_by_role("link",name="V-00000001").click()
        snap("36-constancia-admin", A, a, lambda s,t: BAR in t and "V-00000001" in t, same=after)
        link(v, "/caja/cerrar/")
        snap("37-cierre-formulario", V, v)
        fill(v, "counted_amount", "114.20")
        button(v, "Cerrar turno")
        def closed(s,t):
            return "Exacto" in t and len(s["cierres"]) == 1 and s["turnos"][0]["status"] == "CLOSED" and s["cierres"][0]["expected_amount"] == 114.2 and s["cierres"][0]["difference"] == 0
        end = snap("38-cierre", V, v, closed, photo=True)
        v.reload()
        snap("39-acta-releida", V, v, closed, same=end)
        link(v, "/ventas/")
        snap("40-venta-sin-turno", V, v, lambda s,t: "Requiere turno abierto" in t, same=end)


def available(state):
    return [lot["available_quantity"] for lot in state["lotes"]]


def selector(page, name):
    return page.locator(f'[name="{name}"]').first


def fill(page, name, value):
    selector(page, name).fill(value)


def button(page, caption):
    page.get_by_role("button", name=caption, exact=True).click()


def link(page, path):
    page.locator(f'a[href="{path}"]:visible').first.click()


def main(out):
    from playwright.sync_api import sync_playwright
    out.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix="etapa14d-") as tmp:
        db = Path(tmp).resolve() / "prueba.sqlite3"
        password = secrets.token_urlsafe(24)
        prepare(db, password)
        from django.contrib.staticfiles.handlers import StaticFilesHandler
        from django.core.wsgi import get_wsgi_application
        from django.db import connections
        server = make_server("127.0.0.1", 0, StaticFilesHandler(get_wsgi_application()), handler_class=QuietLog)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        j = Journey(db, out, f"http://127.0.0.1:{server.server_port}")
        meta = {"sqlite": sqlite3.sqlite_version, "django": importlib.metadata.version("Django"),
                "playwright": importlib.metadata.version("playwright"), "base_temporal": Path(tmp).name,
                "plan08_inicio": sha((ROOT/"08_Historias_de_Usuario.md").read_bytes()),
                "inicio_utc": datetime.now(timezone.utc).isoformat(), "estado": "incompleto"}
        first_build = build()
        save(out/"build-inicio.json", first_build)
        meta["build_inicio"] = first_build["sha256"]
        try:
            with sync_playwright() as pw:
                launch = {"executable_path": os.environ["E14_CHROME"]} if os.getenv("E14_CHROME") else {"channel":"chrome"}
                browser = pw.chromium.launch(headless=True, **launch)
                meta["chrome"] = browser.version
                try:
                    j.run(browser, password)
                    meta["estado"] = "recorrido_completo"
                finally:
                    browser.close()
        finally:
            server.shutdown()
            worker.join()
            server.server_close()
            connections.close_all()
            meta.update(pasos=j.steps, fin_utc=datetime.now(timezone.utc).isoformat())
            final_build = build()
            save(out/"build-final.json", final_build)
            meta.update(build_final=final_build["sha256"], build_estable=first_build == final_build,
                        runner_sha256=sha(Path(__file__).read_bytes()))
            save(out/"http.json", j.http)
            save(out/"ejecucion.json", meta)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("salida", type=Path, help="Directorio nuevo para evidencia; nunca sobrescribe otra pasada.")
    main(parser.parse_args().salida)
