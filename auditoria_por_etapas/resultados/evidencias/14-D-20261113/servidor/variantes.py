"""Ejecutar con Python de r1-pmv. Crea SQLite en memoria y emite un JSON inédito."""
import argparse
import hashlib
import html
import json
import logging
import os
import re
import secrets
import sqlite3
import sys
import uuid
from datetime import timedelta
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

folder = Path(__file__).resolve().parent
root = next(path for path in folder.parents if (path / "r1-pmv/manage.py").is_file())
app = root / "r1-pmv"
sys.path.insert(0, str(app))
os.environ.update(APP_ENV="test", DJANGO_SETTINGS_MODULE="config.settings", DJANGO_DEBUG="false",
                  DJANGO_SECRET_KEY=secrets.token_urlsafe(50), DJANGO_ALLOWED_HOSTS="testserver")
import django
from django.conf import settings

settings.DATABASES["default"] = {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
django.setup()
from django.apps import apps
from django.core.management import call_command
from django.db import connection
from django.test import Client
from django.utils import timezone
from cash.models import CashRegister, CashShiftClose
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import Lot, StockWriteOff
from sales.models import Sale, SaleDraftLine


class HiddenInputs(HTMLParser):
    def __init__(self, response):
        super().__init__()
        self.data = {}
        self.feed(response.content.decode())

    def handle_starttag(self, tag, attrs):
        item = dict(attrs)
        if tag == "input" and item.get("type") == "hidden" and item.get("name"):
            self.data[item["name"]] = item.get("value", "")


def digest(value):
    canonical = json.dumps(value, default=str, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def snapshot():
    # Todos los campos concretos, incluidos tiempos, claves y snapshots. Solo se exportan huellas.
    tables = {}
    for name in ("identity", "catalog", "inventory", "cash", "sales"):
        for model in apps.get_app_config(name).get_models(include_auto_created=True):
            rows = list(model.objects.order_by("pk").values())
            tables[model._meta.db_table] = (len(rows), digest(rows))
    return tables


def post(client, url, data, **kw):
    return client.post(url, data={**data, "csrfmiddlewaretoken": client.cookies["csrftoken"].value}, **kw)


def auth(code):
    role, _ = Role.objects.get_or_create(code=code, defaults={"name": code})
    password = secrets.token_urlsafe(25)
    account = Account.objects.create_user(email=f"{code.lower()}@example.invalid",
                                          role=role, display_name=code, password=password)
    c = Client(enforce_csrf_checks=True)
    c.get("/")
    response = post(c, "/", {"email": account.email, "password": password})
    assert response.status_code == 302 and response.url == "/inicio/"
    return c


def body(response):
    return " ".join(html.unescape(re.sub("<[^>]+>", " ", response.content.decode())).split())


def probe(code, actor, purpose, client, url, data, status, literal="", verify=None, allowed_tables=()):
    before = snapshot()
    response = post(client, url, data)
    after = snapshot()
    changed = sorted(key for key in before if before[key] != after[key])
    content = body(response)
    checks = {"HTTP": response.status_code == status,
              "texto": not literal or literal in content,
              "tablas_permitidas": set(changed) <= set(allowed_tables)}
    if verify:
        checks["efecto"] = verify()
    visible_errors = [html.unescape(re.sub("<[^>]+>", "", value)).strip() for value in
                      re.findall(r'<div class="text-danger small mt-1">(.+?)</div>', response.content.decode(), re.S)]
    records.append({"id": code, "rol": actor, "caso": purpose, "ruta": url, "HTTP_esperado": status,
                    "HTTP": response.status_code, "literal_buscado": literal or None,
                    "errores_de_campo": visible_errors, "huella_antes": digest(before), "huella_despues": digest(after),
                    "tablas_cambiadas": changed, "comprobaciones": checks,
                    "resultado": "CUMPLE" if all(checks.values()) else "INCUMPLE"})
    return response


def run():
    assert connection.vendor == "sqlite" and connection.settings_dict["NAME"] == ":memory:"
    call_command("migrate", verbosity=0, interactive=False)
    admin, wh, seller = [auth(code) for code in ("ADMIN", "ALMACENERO", "VENDEDOR")]
    CashRegister.objects.get_or_create(code="CAJA-01")
    assert post(admin, "/productos/categorias/nueva/", {"name": "Ficticia catorce"}).status_code == 302
    cat = Category.objects.get(name="Ficticia catorce")
    assert post(admin, "/productos/nuevo/", {"name": "Muestra catorce", "barcode": "INT-CATORCE",
                "barcode_type": "INTERNAL", "category": cat.pk, "unit": "UND", "sale_price": "5.00",
                "controls_expiration": "on", "minimum_stock": 1}).status_code == 302
    prod = Product.objects.get(name="Muestra catorce")
    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)
    load = {"product": prod.pk, "lots-TOTAL_FORMS": 1, "lots-INITIAL_FORMS": 0, "lots-MIN_NUM_FORMS": 1,
            "lots-MAX_NUM_FORMS": 10, "lots-0-number": "L-FICTICIO", "lots-0-quantity": 10,
            "lots-0-unit_cost": "2.0000", "lots-0-expiration_date": tomorrow.isoformat()}
    denied = "No tienes permiso para esta operación"
    probe("S01", "ADMIN", "carga inicial con producto válido", admin, "/inventario/carga-inicial/", load, 403, denied)
    assert post(wh, "/inventario/carga-inicial/", load).status_code == 302
    lot = Lot.objects.get(product=prod)
    add = {"product_id": prod.pk, "quantity": 2}
    state_url = f"/productos/{prod.pk}/disponibilidad/"
    cat_url = f"/productos/categorias/{cat.pk}/estado/"
    cause_url = "/inventario/bajas/nueva/"

    def writeoff(reason, notes="", quantity=1):
        return {"lot_id": lot.pk, "quantity": quantity, "reason": reason,
                "notes": notes, "idempotency_key": str(uuid.uuid4())}

    probe("S02", "ALMACENERO", "apertura de caja", wh, "/caja/abrir/", {"opening_amount": "10.00"}, 403, denied)
    probe("S03", "VENDEDOR", "baja real por daño", seller, cause_url, writeoff("DAÑO", "Empaque roto"), 403, denied)
    probe("S04", "VENDEDOR", "cambio de disponibilidad", seller, state_url, {"is_active": "false"}, 403, denied)
    assert post(seller, "/caja/abrir/", {"opening_amount": "10.00"}).status_code == 302
    assert post(seller, "/ventas/", add).status_code == 302
    checkout_url = "/ventas/cobrar/"
    checkout = HiddenInputs(seller.get(checkout_url)).data
    checkout["cash_received"] = "10.00"
    assert {"expected_subtotal", "draft_signature", "idempotency_key"} <= checkout.keys()
    probe("S05", "ALMACENERO", "cobro reservado al vendedor", wh, checkout_url, checkout, 403, denied)
    probe("S06", "VENDEDOR", "efectivo 9.99 para dos unidades por 10.00", seller, checkout_url,
          {**checkout, "cash_received": "9.99"}, 200, "es insuficiente para cubrir el total")
    probe("S07", "VENDEDOR", "cierre bloqueado por dos unidades en borrador", seller, "/caja/cerrar/",
          {"counted_amount": "10.00"}, 200, "Hay una venta en preparación con productos")
    assert post(admin, state_url, {"is_active": "false"}).status_code == 302
    prod.refresh_from_db()
    assert not prod.is_active
    probe("S08", "VENDEDOR", "cobrar revisión anterior tras POST de desactivación de producto",
          seller, checkout_url, checkout, 200, "ya no está disponible para la venta")
    assert post(admin, state_url, {"is_active": "true"}).status_code == 302
    pending = HiddenInputs(admin.get(cat_url + "confirmar/")).data
    assert pending["is_active"] == "false" and post(admin, cat_url, pending).status_code == 302
    cat.refresh_from_db()
    assert not cat.is_active
    probe("S09", "VENDEDOR", "cobrar revisión anterior tras confirmar desactivación de categoría",
          seller, checkout_url, checkout, 200, "ya no está disponible para la venta")
    probe("S10", "ADMIN", "reenviar confirmación antigua de categoría", admin, cat_url, pending,
          409, "La categoría cambió desde que abrió esta pantalla")
    pending = HiddenInputs(admin.get(cat_url + "confirmar/")).data
    assert pending["is_active"] == "true" and post(admin, cat_url, pending).status_code == 302
    probe("S11", "ALMACENERO", "merma de 11 para saldo 10", wh, cause_url,
          writeoff("DAÑO", "Empaque roto", 11), 200, "La cantidad supera las existencias")
    # CP-HU-INV-02-001 y RN-05. Fechas de Lima controladas sin editar el registro del lote.
    probe("S12", "ALMACENERO", "vencimiento prematuro, vence mañana", wh, cause_url,
          writeoff("VENCIMIENTO"), 200, "El lote aún no ha vencido")
    with patch("django.utils.timezone.localdate", return_value=tomorrow):
        probe("S13", "VENDEDOR", "venció hoy entre la revisión y el cobro", seller, checkout_url,
              checkout, 200, "Disponible: 0, solicitado: 2.")
        probe("S14", "ALMACENERO", "daño de lote vencido", wh, cause_url,
              writeoff("DAÑO", "Empaque roto"), 200, "El lote está vencido")
        probe("S15", "ALMACENERO", "robo de lote vencido sin explicar", wh, cause_url,
              writeoff("ROBO", " "), 200, "Detalle obligatorio")
        stock_before = Lot.objects.get(pk=lot.pk).available_quantity
        def theft_saved():
            return (Lot.objects.get(pk=lot.pk).available_quantity == stock_before - 1
                    and StockWriteOff.objects.filter(lot=lot, reason="ROBO", quantity=1,
                          responsible__role__code="ALMACENERO", notes="Faltante confirmado por conteo").count() == 1)
        probe("S16", "ALMACENERO", "robo explicado de una unidad de lote vencido", wh, cause_url,
              writeoff("ROBO", "Faltante confirmado por conteo"), 302, verify=theft_saved,
              allowed_tables=("inventory_lot", "inventory_stockwriteoff", "catalog_product"))
    # Vuelve el reloj al día original de la fixture; esta variante positiva discrimina un rechazo espurio.
    response = post(seller, checkout_url, checkout)
    sale = Sale.objects.get()
    assert response.status_code == 302 and str(sale.pk) in response.url and sale.total_amount == Decimal("10.00")
    probe("S17", "VENDEDOR", "reenvío idéntico al cobro confirmado", seller, checkout_url, checkout,
          302, verify=lambda: Sale.objects.count() == 1)
    assert post(seller, "/caja/cerrar/", {"counted_amount": "20.00"}).status_code == 302
    close = CashShiftClose.objects.get()
    assert close.expected_amount == Decimal("20.00") and close.difference == 0
    probe("S18", "VENDEDOR", "segundo cierre del mismo turno", seller, "/caja/cerrar/",
          {"counted_amount": "20.00"}, 200, "No tienes un turno de caja abierto para cerrar.")
    return {"fecha_lima": str(today), "vencimiento_controlado": str(tomorrow),
            "roles_login_HTTP": ["ADMIN", "ALMACENERO", "VENDEDOR"], "CSRF": True,
            "tablas": sorted(snapshot()), "tablas_excluidas": "sesiones técnicas Django, auth, admin, migrations",
            "control_positivo": {"cobros": Sale.objects.count(), "venta": sale.correlative,
                      "importe": str(sale.total_amount), "esperado_cierre": str(close.expected_amount),
                      "diferencia": str(close.difference), "saldo_lote": Lot.objects.get(pk=lot.pk).available_quantity},
            "variantes": records}


if __name__ == "__main__":
    args = argparse.ArgumentParser()
    args.add_argument("salida", type=Path)
    path = args.parse_args().salida
    if path.exists():
        raise SystemExit("Especifique un archivo nuevo para preservar la evidencia anterior.")
    logging.disable(logging.CRITICAL)
    records = []
    data = run()
    data.update(django=django.get_version(), python=sys.version.split()[0], sqlite=sqlite3.sqlite_version,
                base=":memory:", archivo_servicio_merma=digest((app / "inventory/services.py").read_text("utf-8")),
                herramienta="Django Client (WSGI en proceso), Django ORM; sin navegador")
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    failed = [item["id"] for item in records if item["resultado"] != "CUMPLE"]
    print(f"{len(records) - len(failed)}/{len(records)}. Fallos: {failed}.")
    sys.exit(bool(failed))
