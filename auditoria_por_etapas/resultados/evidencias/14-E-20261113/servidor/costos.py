"""F-COSTO por HTTP, con SQLite en memoria y huellas de negocio antes/después."""
import argparse
import hashlib
import json
import logging
import runpy
import sys
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

folder = Path(__file__).resolve().parent
root = next(parent for parent in folder.parents if (parent / "r1-pmv/manage.py").exists())
helper = root / "auditoria_por_etapas/resultados/evidencias/14-D-20261113/servidor/variantes.py"
base = runpy.run_path(str(helper))
from django.core.management import call_command
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from catalog.models import Category, Product
from cash.models import CashRegister
from identity.models import Account
from inventory.models import Lot, StockWriteOff, PhysicalAdjustment
from sales.models import Sale, SaleLine

post, auth, digest, snapshot, HiddenInputs = [base[key] for key in
    ("post", "auth", "digest", "snapshot", "HiddenInputs")]
records = []


def state(product):
    product.refresh_from_db()
    physical = product.lots.aggregate(q=Sum("available_quantity"))["q"] or 0
    sellable = product.lots.filter(expiration_date__gt=timezone.localdate()).aggregate(
        q=Sum("available_quantity"))["q"] or 0
    return {"fisico": physical, "vendible": sellable, "promedio": str(product.average_cost)}


def record(code, operation, expected, actual, extra=None):
    records.append({"id": code, "caso": operation, "esperado": expected, "observado": actual,
                    "resultado": "CUMPLE" if actual == expected else "INCUMPLE", **(extra or {})})


def verify_state(code, operation, product, physical, sellable, cost):
    record(code, operation, {"fisico": physical, "vendible": sellable, "promedio": cost}, state(product))


def lots_payload(product, lots):
    payload = {"product": product.pk, "lots-TOTAL_FORMS": len(lots), "lots-INITIAL_FORMS": 0,
               "lots-MIN_NUM_FORMS": 1, "lots-MAX_NUM_FORMS": 10}
    for index, (number, quantity, cost, date) in enumerate(lots):
        for field, value in {"number": number, "quantity": quantity,
                             "unit_cost": cost, "expiration_date": date.isoformat()}.items():
            payload[f"lots-{index}-{field}"] = value
    return payload


def writeoff(lot, quantity, reason="ROBO"):
    return {"lot_id": lot.pk, "quantity": quantity, "reason": reason, "notes": "Conteo ficticio confirmado",
            "idempotency_key": str(uuid.uuid4())}


def adjust(lot, delta):
    return {"lot_id": lot.pk, "delta": delta, "reason": "Conteo físico ficticio",
            "idempotency_key": str(uuid.uuid4())}


def reject(code, client, url, payload, statuses):
    before = snapshot()
    response = post(client, url, payload)
    after = snapshot()
    record(code, f"Rechazo sin mutación {url}", {"status_valido": True, "datos_iguales": True},
           {"status_valido": response.status_code in statuses, "datos_iguales": before == after},
           {"HTTP": response.status_code, "huella_antes": digest(before), "huella_despues": digest(after)})


def rollback_probe(code, client, url, payload, target, original):
    before = snapshot()
    wrote = []
    def fail_after(*args, **kwargs):
        result = original(*args, **kwargs)
        wrote.append(snapshot() != before)
        raise RuntimeError("Fallo sintético posterior a escritura 14-E")
    try:
        with patch(target, autospec=True, side_effect=fail_after):
            post(client, url, payload)
    except RuntimeError as error:
        assert str(error) == "Fallo sintético posterior a escritura 14-E"
    after = snapshot()
    record(code, f"Rollback postwrite {url}", {"escribio": True, "restauro": True},
           {"escribio": bool(wrote and all(wrote)), "restauro": before == after},
           {"huella_antes": digest(before), "huella_despues": digest(after)})


def run():
    call_command("migrate", verbosity=0, interactive=False)
    admin, wh, seller = [auth(code) for code in ("ADMIN", "ALMACENERO", "VENDEDOR")]
    CashRegister.objects.get_or_create(code="CAJA-01")
    assert post(admin, "/productos/categorias/nueva/", {"name": "F-COSTO"}).status_code == 302
    category = Category.objects.get(name="F-COSTO")
    assert post(admin, "/productos/nuevo/", {"name": "Costo ficticio", "barcode": "INT-F-COSTO",
        "barcode_type": "INTERNAL", "category": category.pk, "unit": "UND", "sale_price": "10.00",
        "controls_expiration": "on", "minimum_stock": "1"}).status_code == 302
    product = Product.objects.get(name="Costo ficticio")
    today = timezone.localdate()
    business_date = today + timedelta(days=1)
    initial = lots_payload(product, [("EXP", 8, "3.0000", business_date),
                                    ("VIG", 10, "3.0000", today + timedelta(days=30))])
    assert post(wh, "/inventario/carga-inicial/", initial).status_code == 302
    verify_state("E01", "Carga inicial 18 a3", product, 18, 18, "3.0000")
    with patch("django.utils.timezone.localdate", return_value=business_date):
        verify_state("E02", "Expirar8 conserva físico y promedio", product, 18, 10, "3.0000")
        receipt = lots_payload(product, [("REC", 10, "6.0000", today + timedelta(days=60))])
        reject("E03", admin, "/inventario/entrada/", receipt, {403})
        rollback_probe("E04", wh, "/inventario/entrada/", receipt,
                       "inventory.models.Lot.objects.bulk_create", Lot.objects.bulk_create)
        assert post(wh, "/inventario/entrada/", receipt).status_code == 302
        verify_state("E05", "Recepción usa Q físico18 y C3", product, 28, 20, "4.0714")
        vig, expired = product.lots.get(number="VIG"), product.lots.get(number="EXP")
        reject("E06", wh, "/inventario/ajustes/nuevo/", adjust(vig, 2), {403})
        reject("E07", seller, "/inventario/bajas/nueva/", writeoff(vig, 1), {403})
        reject("E08", wh, "/inventario/bajas/nueva/", writeoff(vig, 999), {200})
        assert post(seller, "/caja/abrir/", {"opening_amount": "10.00"}).status_code == 302
        assert post(seller, "/ventas/", {"product_id": product.pk, "quantity": 1}).status_code == 302
        checkout = HiddenInputs(seller.get("/ventas/cobrar/")).data
        checkout["cash_received"] = "10.00"
        rollback_probe("E09", seller, "/ventas/cobrar/", checkout, "inventory.models.Lot.save", Lot.save)
        assert post(seller, "/ventas/cobrar/", checkout).status_code == 302
        sale_line = SaleLine.objects.get()
        verify_state("E10", "Venta1 conserva promedio", product, 27, 19, "4.0714")
        record("E11", "Costo histórico de venta", "4.0714", str(sale_line.unit_cost))
        rollback_probe("E12", wh, "/inventario/bajas/nueva/", writeoff(vig, 1),
                       "inventory.models.Lot.save", Lot.save)
        assert post(wh, "/inventario/bajas/nueva/", writeoff(vig, 1)).status_code == 302
        write_off = StockWriteOff.objects.get()
        verify_state("E13", "Baja1 conserva promedio", product, 26, 18, "4.0714")
        record("E14", "Costo histórico de baja", "4.0714", str(getattr(write_off, "unit_cost", None)))
        rollback_probe("E15", admin, "/inventario/ajustes/nuevo/", adjust(vig, 2),
                       "inventory.models.Lot.save", Lot.save)
        assert post(admin, "/inventario/ajustes/nuevo/", adjust(vig, 2)).status_code == 302
        adjustment = PhysicalAdjustment.objects.get()
        verify_state("E16", "Ajuste+2 con físico conserva promedio", product, 28, 20, "4.0714")
        record("E17", "Costo histórico de ajuste", "4.0714", str(getattr(adjustment, "unit_cost", None)))
        prior = {model._meta.label: list(model.objects.order_by("pk").values()) for model in
                 (Sale, SaleLine, StockWriteOff, PhysicalAdjustment)}
        assert post(wh, "/inventario/bajas/nueva/", writeoff(expired, 8, "VENCIMIENTO")).status_code == 302
        verify_state("E18", "Agotar vencidos conserva promedio con físico restante", product, 20, 20, "4.0714")
        assert post(seller, "/ventas/", {"product_id": product.pk, "quantity": 20}).status_code == 302
        checkout = HiddenInputs(seller.get("/ventas/cobrar/")).data
        checkout["cash_received"] = "200.00"
        assert post(seller, "/ventas/cobrar/", checkout).status_code == 302
        verify_state("E19", "Agotar físico por venta lleva promedio a cero", product, 0, 0, "0.0000")
        preserved = all(
            model.objects.filter(pk=entry["id"]).values().get() == entry
            for model in (Sale, SaleLine, StockWriteOff, PhysicalAdjustment)
            for entry in prior[model._meta.label]
        )
        record("E20", "Snapshots previos conservados tras agotamiento", True, preserved)
        # Savepoint evita que el comportamiento previo defectuoso contamine la siguiente rama.
        with transaction.atomic():
            reject("E21", admin, "/inventario/ajustes/nuevo/", adjust(vig, 2), {200})
            transaction.set_rollback(True)
        # Comprobación independiente de cero alcanzado por baja y por ajuste negativo.
        for index, endpoint in enumerate(("/inventario/bajas/nueva/", "/inventario/ajustes/nuevo/"), start=22):
            with transaction.atomic():
                assert post(wh, "/inventario/entrada/",
                            lots_payload(product, [(f"END-{index}", 2, "7.0000", today + timedelta(days=90))])).status_code == 302
                last_lot = product.lots.get(number=f"END-{index}")
                client = wh if index == 22 else admin
                payload = writeoff(last_lot, 2) if index == 22 else adjust(last_lot, -2)
                assert post(client, endpoint, payload).status_code == 302
                verify_state(f"E{index}", "Agotamiento por baja/ajuste lleva promedio a cero",
                             product, 0, 0, "0.0000")
                transaction.set_rollback(True)
    return {"fecha_lima_real": str(today), "fecha_simulada": str(business_date), "base": ":memory:",
            "CSRF": True, "runner": "Django Client WSGI y ORM", "casos": records}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("salida", type=Path)
    output = parser.parse_args().salida
    if output.exists():
        raise SystemExit("Use un archivo nuevo para preservar evidencia.")
    logging.disable(logging.CRITICAL)
    result = run()
    sources = ["inventory/services.py", "inventory/models.py", "sales/services.py", "sales/models.py"]
    result["fuentes_sha256"] = {name: hashlib.sha256((root / "r1-pmv" / name).read_bytes()).hexdigest()
                                for name in sources}
    result["08_sha256"] = hashlib.sha256((root / "08_Historias_de_Usuario.md").read_bytes()).hexdigest()
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    failed = [item["id"] for item in records if item["resultado"] == "INCUMPLE"]
    print(f"{len(records) - len(failed)}/{len(records)}. Fallos: {failed}")
    sys.exit(bool(failed))
