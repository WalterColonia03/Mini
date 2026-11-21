"""HUECO-09: datos de demostracion (muestra de enlatados por unidad)."""
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot

# nombre, codigo, precio, minimo, lotes[(numero, cantidad, costo, dias_a_vencer)]
DEMO = [
    ("Atun en lata 170g", "7750001000011", "6.50", 10, [("A1", 60, "4.20", 300)]),
    ("Duraznos en almibar 820g", "7750001000028", "12.90", 10, [("B1", 4, "8.50", 200)]),
    ("Frejoles en lata 400g", "7750001000035", "5.20", 8, [("C1", 25, "3.10", 12)]),
    ("Leche evaporada 400g", "7750001000042", "4.80", 15, [("D1", 40, "3.20", 150), ("D2", 30, "3.25", 400)]),
]


class Command(BaseCommand):
    help = "Carga productos y lotes de demostracion (idempotente)."

    @transaction.atomic
    def handle(self, *args, **options):
        cat = Category.objects.filter(name_normalized="productos enlatados").first()
        if cat is None:
            self.stderr.write("No existe la categoria 'Productos enlatados'; abortando.")
            return
        warehouse = Account.objects.filter(role__code=Role.Code.WAREHOUSE).first()
        if warehouse is None:
            self.stderr.write("No hay un almacenero para registrar la carga.")
            return
        today = timezone.localdate()
        created = 0
        for name, code, price, minimum, lots in DEMO:
            existing = Product.objects.filter(barcode=code).first()
            if existing is not None:
                if existing.average_cost == Decimal("0.0000"):
                    total_qty = sum(qty for _, qty, _, _ in lots)
                    weighted = sum(Decimal(cost) * qty for _, qty, cost, _ in lots)
                    if total_qty > 0:
                        existing.average_cost = (weighted / total_qty).quantize(
                            Decimal("0.0001"), rounding=ROUND_HALF_UP
                        )
                        existing.save(update_fields=["average_cost", "updated_at"])
                continue
            total_qty = sum(qty for _, qty, _, _ in lots)
            weighted = sum(Decimal(cost) * qty for _, qty, cost, _ in lots)
            avg_cost = (
                (weighted / total_qty).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
                if total_qty > 0
                else Decimal("0.0000")
            )
            product = Product(
                category=cat,
                name=name,
                barcode=code,
                sale_price=Decimal(price),
                minimum_stock=minimum,
                average_cost=avg_cost,
            )
            product.full_clean()
            product.save()
            load = InitialInventoryLoad.objects.create(product=product, responsible=warehouse)
            for number, qty, cost, days in lots:
                Lot.objects.create(
                    product=product,
                    initial_load=load,
                    responsible=warehouse,
                    number=number,
                    initial_quantity=qty,
                    available_quantity=qty,
                    unit_cost=Decimal(cost),
                    expiration_date=today + timedelta(days=days),
                )
            created += 1
        Lot.objects.filter(responsible__isnull=True).update(responsible=warehouse)
        self.stdout.write(f"Productos demo creados: {created}")