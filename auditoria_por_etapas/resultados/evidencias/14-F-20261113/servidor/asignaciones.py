"""Ejecuta variantes14F en una SQLite nueva persistente junto al JSON solicitado."""
import argparse
import hashlib
import json
import logging
import re
import runpy
import sqlite3
import sys
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

folder = Path(__file__).resolve().parent
root = next(parent for parent in folder.parents if (parent / "r1-pmv/manage.py").exists())
base = runpy.run_path(str(root / "auditoria_por_etapas/resultados/evidencias/14-D-20261113/servidor/variantes.py"))
from django.apps import apps
from django.core.management import call_command
from django.db import connection
from django.utils import timezone
from cash.models import CashRegister, CashShift, CashShiftClose
from catalog.models import Category, Product
from identity.models import Account
from inventory.models import Lot
from sales.models import Sale, SaleLine

post, auth, digest, snapshot, HiddenInputs = [base[key] for key in
    ("post", "auth", "digest", "snapshot", "HiddenInputs")]
cases = []


def sanitize_database(path):
    # Esta función opera exclusivamente sobre la SQLite ficticia recién creada por el runner.
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA secure_delete = ON")
        db.execute("DELETE FROM django_session")
        db.execute("DELETE FROM identity_loginattempt")
        db.execute("UPDATE identity_account SET password = '!'")
        db.commit()
        db.execute("VACUUM")
        assert db.execute("SELECT COUNT(*) FROM django_session").fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM identity_account WHERE password <> '!'").fetchone()[0] == 0


def record(identifier, case, expected, observed, extra=None):
    cases.append({"id": identifier, "caso": case, "esperado": expected, "observado": observed,
                  "resultado": "CUMPLE" if expected == observed else "INCUMPLE", **(extra or {})})


def receipt(client, sale):
    response = client.get(f"/ventas/constancia/{sale.pk}/")
    assert response.status_code == 200
    return response.content.decode().split('id="constancia-interna">', 1)[1].split("</section>", 1)[0]


def receipt_names(content):
    return {key: re.search(rf"<dt>{label}</dt><dd>([^<]*)</dd>", content).group(1)
            for key, label in (("vendedor", "Vendedor"), ("caja", "Caja"))}


def allocation_values(line):
    try:
        model = apps.get_model("sales", "SaleLotAllocation")
    except LookupError:
        return []
    return list(model.objects.filter(line=line).order_by("lot_snapshot_number").values_list(
        "lot_snapshot_number", "quantity"))


def create_product(admin, warehouse, category, name, lots):
    assert post(admin, "/productos/nuevo/", {
        "name": name, "barcode": f"INT-{name}", "barcode_type": "INTERNAL", "category": category.pk,
        "unit": "UND", "sale_price": "10.00", "controls_expiration": "on", "minimum_stock": 1,
    }).status_code == 302
    product = Product.objects.get(name=name)
    payload = {"product": product.pk, "lots-TOTAL_FORMS": len(lots), "lots-INITIAL_FORMS": 0,
               "lots-MIN_NUM_FORMS": 1, "lots-MAX_NUM_FORMS": 10}
    for index, (number, quantity) in enumerate(lots):
        for field, value in {"number": number, "quantity": quantity, "unit_cost": "3.0000",
            "expiration_date": (timezone.localdate() + timedelta(days=30 + index)).isoformat()}.items():
            payload[f"lots-{index}-{field}"] = value
    assert post(warehouse, "/inventario/carga-inicial/", payload).status_code == 302
    return product


def review(seller, product, quantity, cash):
    assert post(seller, "/ventas/", {"product_id": product.pk, "quantity": quantity}).status_code == 302
    data = HiddenInputs(seller.get("/ventas/cobrar/")).data
    return {**data, "cash_received": cash}


def run():
    call_command("migrate", verbosity=0, interactive=False)
    admin, wh, seller = [auth(code) for code in ("ADMIN", "ALMACENERO", "VENDEDOR")]
    account = Account.objects.get(role__code="VENDEDOR")
    Account.objects.filter(pk=account.pk).update(display_name="Vendedor original ficticio")
    register, _ = CashRegister.objects.get_or_create(code="CAJA-01")
    assert post(admin, "/productos/categorias/nueva/", {"name": "Asignaciones14F"}).status_code == 302
    category = Category.objects.get(name="Asignaciones14F")
    assert post(seller, "/caja/abrir/", {"opening_amount": "100.00"}).status_code == 302
    p1 = create_product(admin, wh, category, "Caso-parcial", [("A", 3), ("B", 7)])
    payload = review(seller, p1, 4, "40.00")
    response = post(seller, "/ventas/cobrar/", payload)
    assert response.status_code == 302
    sale1 = Sale.objects.get(idempotency_key=payload["idempotency_key"])
    line1 = sale1.lines.get()
    record("F01", "FEFO A3 B7 vender4 conserva saldo A0 B6", [("A", 0), ("B", 6)],
           list(p1.lots.order_by("number").values_list("number", "available_quantity")))
    record("F02", "Asignaciones durables venta4", [("A", 3), ("B", 1)], allocation_values(line1))
    original_receipt = receipt(admin, sale1)
    original_names = receipt_names(original_receipt)
    Account.objects.filter(pk=account.pk).update(display_name="Vendedor actualizado ficticio")
    CashRegister.objects.filter(pk=register.pk).update(code="CAJA-RENOMBRADA")
    record("F03", "Constancia conserva identidad original al cambiar maestros", original_names,
           receipt_names(receipt(admin, sale1)))
    record("F04", "Venta persiste snapshots vendedor y caja",
           {"vendedor": "Vendedor original ficticio", "caja": "CAJA-01"},
           {"vendedor": getattr(sale1, "seller_snapshot_name", None),
            "caja": getattr(sale1, "cash_register_snapshot_code", None)})
    before = snapshot()
    repeated = post(seller, "/ventas/cobrar/", payload)
    record("F05", "Reenvío recupera misma venta sin modificar datos", True,
           repeated.status_code == 302 and str(sale1.pk) in repeated.url and before == snapshot())

    p2 = create_product(admin, wh, category, "Caso-agotado", [("A", 3), ("B", 2)])
    payload2 = review(seller, p2, 5, "50.00")
    before = snapshot()
    denied = post(wh, "/ventas/cobrar/", payload2)
    record("F06", "ALMACENERO no cobra", True, denied.status_code == 403 and before == snapshot())
    assert post(seller, "/ventas/cobrar/", payload2).status_code == 302
    sale2 = Sale.objects.get(idempotency_key=payload2["idempotency_key"])
    p2.refresh_from_db()
    record("F07", "Contrato A3 B2 vender5 tiene asignaciones3/2",
           [("A", 3), ("B", 2)], allocation_values(sale2.lines.get()))
    record("F08", "Agotar mantiene costo histórico3 y reinicia vigente0",
           {"fisico": 0, "promedio": "0.0000", "snapshot": "3.0000"},
           {"fisico": p2.physical_stock, "promedio": str(p2.average_cost),
            "snapshot": str(sale2.lines.get().unit_cost)})
    # Tres líneas agregadas A,B,C, con UUID de venta deliberadamente desordenado3,1,2.
    for label in ("Orden-A", "Orden-B", "Orden-C"):
        item = create_product(admin, wh, category, label, [("UNICO", 1)])
        assert post(seller, "/ventas/", {"product_id": item.pk, "quantity": 1}).status_code == 302
    order_payload = {**HiddenInputs(seller.get("/ventas/cobrar/")).data, "cash_received": "30.00"}
    identifiers = iter(uuid.UUID(int=number) for number in (3, 1, 2))
    with patch.object(SaleLine._meta.get_field("id"), "default", lambda: next(identifiers)):
        # Django cached_property también conserva el callable usado para defaults.
        with patch.object(SaleLine._meta.get_field("id"), "_get_default", lambda: next(identifiers)):
            assert post(seller, "/ventas/cobrar/", order_payload).status_code == 302
    ordered_sale = Sale.objects.get(idempotency_key=order_payload["idempotency_key"])
    order_html = receipt(admin, ordered_sale)
    html_order = re.findall(r"<td>(Orden-[ABC])</td>", order_html)
    record("F09", "Constancia mantiene orden agregado independiente deUUID",
           ["Orden-A", "Orden-B", "Orden-C"], html_order)
    record("F10", "Posición de línea persistida", [1, 2, 3],
           [getattr(line, "position", None) for line in ordered_sale.lines.all()])
    # Fixture heredada explícita, sin asignaciones ni snapshots nuevos.
    legacy = Sale.objects.create(cash_shift=CashShift.objects.get(status="OPEN"), seller=account,
        total_amount=Decimal("10"), base_amount=Decimal("8.47"), igv_amount=Decimal("1.53"),
        cash_received=Decimal("10"), change_given=Decimal("0"), correlative="V-99999999",
        idempotency_key=uuid.uuid4())
    old_line = SaleLine.objects.create(sale=legacy, product=p1, product_snapshot_name="Legado ficticio",
        product_snapshot_barcode=p1.barcode, quantity=1, unit_price=Decimal("10"), amount=Decimal("10"))
    before = snapshot()
    legacy_html = receipt(admin, legacy)
    record("F11", "Constancia avisa dato histórico no disponible", True,
           bool(re.search(r"no disponible|no capturad|no registrad|desconocid", legacy_html, re.I)))
    record("F12", "Consultar legado conservaNULL y asignaciones vacías", True,
           old_line.unit_cost is None and allocation_values(old_line) == [] and before == snapshot())
    return {"fecha_lima": str(timezone.localdate()), "base": connection.settings_dict["NAME"],
            "herramienta": "Django Client con CSRF y login HTTP, SQLite archivo nueva",
            "casos": cases}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("salida", type=Path)
    output = parser.parse_args().salida.resolve()
    database = output.with_suffix(".sqlite3")
    if output.exists() or database.exists():
        raise SystemExit("Use nombres nuevos de JSON/base para preservar evidencia.")
    connection.close()
    connection.settings_dict["NAME"] = str(database)
    logging.disable(logging.CRITICAL)
    result = run()
    result["fuentes_sha256"] = {name: hashlib.sha256((root / "r1-pmv" / name).read_bytes()).hexdigest()
        for name in ("sales/models.py", "sales/services.py", "sales/views.py",
                     "sales/templates/sales/sales_receipt.html")}
    result["08_sha256"] = hashlib.sha256((root / "08_Historias_de_Usuario.md").read_bytes()).hexdigest()
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    connection.close()
    sanitize_database(database)
    failed = [case["id"] for case in cases if case["resultado"] == "INCUMPLE"]
    print(f"{len(cases) - len(failed)}/{len(cases)}. Fallos: {failed}")
    sys.exit(bool(failed))
