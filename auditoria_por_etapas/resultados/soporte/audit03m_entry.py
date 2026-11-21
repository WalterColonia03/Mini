"""Individual product suspension vs a subsequent stock entry, inside audit03m_pg's private cluster."""
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from audit03l_concurrency import contest
from cash.models import CashShift
from catalog.models import Category, Product
from catalog.services import toggle_product_availability
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot, PhysicalAdjustment, StockWriteOff, Supplier
from inventory.services import LotInput, confirm_initial_load, register_stock_entry
from sales.models import Sale, SaleCounter, SaleDraft, SaleDraftLine, SaleLine


UNAVAILABLE = "El producto no está disponible para registrar entradas."


def surrounding_state():
    """Comparable state only; no accounts, keys or emails are included in reports."""
    fields = {
        SaleCounter: ("pk", "next_value"),
        Sale: ("pk", "cash_shift_id", "draft_id", "total_amount", "cash_received"),
        SaleLine: ("pk", "product_id", "quantity", "product_snapshot_barcode", "unit_price"),
        SaleDraft: ("pk", "status"),
        SaleDraftLine: ("pk", "draft_id", "product_id", "quantity", "unit_price"),
        CashShift: ("pk", "status", "opening_amount"),
        StockWriteOff: ("pk", "lot_id", "quantity"),
        PhysicalAdjustment: ("pk", "lot_id", "delta"),
    }
    return {model.__name__: list(model.objects.order_by("pk").values_list(*columns))
            for model, columns in fields.items()}


def state(product):
    product = Product.objects.select_related("category").get(pk=product.pk)
    lots = [
        {"id": str(lot.pk), "number": lot.number_normalized, "initial": lot.is_initial,
         "quantity": lot.initial_quantity, "available": lot.available_quantity,
         "cost": str(lot.unit_cost), "expires": lot.expiration_date.isoformat(),
         "supplier": str(lot.supplier_id), "warehouse": str(lot.responsible_id),
         "load": str(lot.initial_load_id)}
        for lot in Lot.objects.filter(product=product).order_by("number_normalized")
    ]
    return {
        "category_id": str(product.category_id), "active_category": product.category.is_active,
        "category_version": product.category.state_version, "active_product": product.is_active,
        "stock": sum(row["available"] for row in lots), "average_cost": str(product.average_cost),
        "loads": [str(pk) for pk in InitialInventoryLoad.objects.filter(product=product).values_list("pk", flat=True)],
        "lots": lots,
    }


def run_entry_cases():
    admin_role, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    warehouse_role, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    admin, original_worker, receiving_worker = [
        Account.objects.create_user(f"m-entry-{name}@audit03.invalid", None, role=role,
                                    display_name=f"AUD03 M {name}")
        for name, role in [("admin", admin_role), ("inicial", warehouse_role), ("entrada", warehouse_role)]
    ]
    original_supplier = Supplier.objects.create(name="AUD03 M origen", ruc="20903000001")
    receiving_supplier = Supplier.objects.create(name="AUD03 M entrada", ruc="20903000002")
    day = timezone.localdate()
    initial_expiry = day + timedelta(days=90)
    entry_expiry = day + timedelta(days=30)
    cases = []
    for first in ("suspension", "entrada"):
        category = Category.objects.create(name=f"AUD03 M grupo entrada {first}")
        product = Product.objects.create(name=f"AUD03 M conserva {first}", category=category,
                                         barcode=f"M-ENT-{first}", sale_price=Decimal("8.50"))
        load = confirm_initial_load(
            actor=original_worker, product=product, supplier=original_supplier, business_date=day,
            lots=[LotInput("L-BASE", 20, Decimal("2.5000"), initial_expiry)])
        neighbor = Product.objects.create(name=f"Control entrada {first}",category=category,barcode=f"M-CONTROL-{first}",sale_price=Decimal("3.00"))
        confirm_initial_load(actor=original_worker,product=neighbor,lots=[LotInput("CONTROL",4,Decimal("1.00"),initial_expiry)])
        neighbor_before = state(neighbor)
        before = state(product)
        surrounding_before = surrounding_state()

        def suspend():
            updated = toggle_product_availability(actor=Account.objects.get(pk=admin.pk),
                product=Product.objects.get(pk=product.pk), is_active=False)
            return {"active": updated.is_active}

        def receive(number="M-ENTRADA"):
            receipt = register_stock_entry(actor=Account.objects.get(pk=receiving_worker.pk),
                product=Product.objects.get(pk=product.pk), supplier=Supplier.objects.get(pk=receiving_supplier.pk),
                business_date=day, lots=[LotInput(number, 5, Decimal("4.0000"), entry_expiry)])
            return {"load": str(receipt.pk)}

        entry_first = first == "entrada"
        race = contest(receive, suspend) if entry_first else contest(suspend, receive)
        after = state(product)
        surrounding_after = surrounding_state()
        try:
            receive("L-INTENTO-POSTERIOR")
            followup = {"status": "committed"}
        except ValidationError as exc:
            followup = {"status": "rejected", "messages": exc.messages}
        after_followup = state(product)
        old_rows = [row for row in after["lots"] if row["initial"]]
        new_rows = [row for row in after["lots"] if not row["initial"]]
        expected_new = {
            "number": "M-ENTRADA", "initial": False, "quantity": 5, "available": 5,
            "cost": "4.0000", "expires": entry_expiry.isoformat(),
            "supplier": str(receiving_supplier.pk), "warehouse": str(receiving_worker.pk),
            "load": str(load.pk),
        }
        checks = {
            "conflict_observed": race["lock_observed"] and race["blocker_matches_winner"]
                                 and race["distinct_connections"],
            "first_committed": race["winner"]["status"] == "committed",
            "second_expected": (race["contender"]["status"] == "committed" if entry_first else
                                race["contender"] == {"status": "rejected", "messages": [UNAVAILABLE]}),
            "one_suspension": before["active_category"] and after["active_category"]
                              and after["category_version"] == before["category_version"]
                              and after["category_id"] == before["category_id"] and not after["active_product"],
            "neighbor_preserved": neighbor_before == state(neighbor) and Product.objects.get(pk=neighbor.pk).is_sellable,
            "initial_lot_and_load_preserved": len(old_rows) == 1 and old_rows == before["lots"]
                                              and after["loads"] == before["loads"] == [str(load.pk)],
            "stock_and_cost": before["stock"] == 20 and before["average_cost"] == "2.5000"
                              and after["stock"] == (25 if entry_first else 20)
                              and after["average_cost"] == ("2.8000" if entry_first else "2.5000"),
            "entry_attribution": ([{k: v for k, v in row.items() if k != "id"} for row in new_rows]
                                  == ([expected_new] if entry_first else [])),
            "next_entry_rejected": followup == {"status": "rejected", "messages": [UNAVAILABLE]},
            "next_entry_unchanged": after_followup == after,
            "other_operations_unchanged": surrounding_before == surrounding_after == surrounding_state(),
        }
        cases.append({"id": f"PG-M-entrada-primero-{first}", "ok": all(checks.values()), "checks": checks,
                      "neighbor_before":neighbor_before,"neighbor_after":state(neighbor),
                      "date_lima": day.isoformat(), "race": race, "before": before, "after": after,
                      "followup_different_lot": followup, "after_followup": after_followup,
                      "other_rows_compared": {name: len(rows) for name, rows in surrounding_before.items()}})
    return cases
