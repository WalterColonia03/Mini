from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot
from inventory.services import LotInput, confirm_initial_load, register_stock_entry


class ReceiptBoundaryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.worker = Account.objects.create_user("receipt@test.invalid", "Test-only-Ab123!",
                                                role=role, display_name="Almacenero de prueba")
        cls.category = Category.objects.create(name="Higiene")

    def test_service_rejects_invalid_lot_without_partial_receipt(self):
        future = timezone.localdate() + timedelta(days=30)
        invalid = [
            ("fraction", LotInput("BAD", Decimal("1.5"), Decimal("2.00"), future)),
            ("boolean", LotInput("BAD", True, Decimal("2.00"), future)),
            ("quantity_over_limit", LotInput("BAD", 1000000, Decimal("2.00"), future)),
            ("number_over_limit", LotInput("L" * 65, 1, Decimal("2.00"), future)),
            ("cost_nan", LotInput("BAD", 1, Decimal("NaN"), future)),
            ("cost_infinite", LotInput("BAD", 1, Decimal("Infinity"), future)),
        ]
        for operation in [confirm_initial_load, register_stock_entry]:
            for label, bad_lot in invalid:
                with self.subTest(operation=operation.__name__, case=label):
                    product = Product.objects.create(
                        name=operation.__name__ + label, barcode=(operation.__name__ + label).replace("_", "-"),
                        category=self.category, sale_price=Decimal("5.00"))
                    if operation is register_stock_entry:
                        confirm_initial_load(actor=self.worker, product=product,
                                             lots=[LotInput("BASE", 2, Decimal("1.00"), future)])
                    product.refresh_from_db()
                    original_cost = product.average_cost
                    before = (list(Lot.objects.values()), list(InitialInventoryLoad.objects.values()))
                    with self.assertRaises(ValidationError):
                        operation(actor=self.worker, product=product,
                                  lots=[LotInput("VALID", 1, Decimal("1.00"), future), bad_lot])
                    self.assertEqual(before, (list(Lot.objects.values()), list(InitialInventoryLoad.objects.values())))
                    product.refresh_from_db()
                    self.assertEqual(product.average_cost, original_cost)

    def test_valid_boundary_values_are_preserved(self):
        future = timezone.localdate() + timedelta(days=1)
        product = Product.objects.create(name="Límites válidos", barcode="LIM-OK",
                                         category=self.category, sale_price=Decimal("5.00"))
        confirm_initial_load(actor=self.worker, product=product,
                             lots=[LotInput("A" * 64, 999999, Decimal("9999999.9999"), future)])
        register_stock_entry(actor=self.worker, product=product,
                             lots=[LotInput("B", 1, Decimal("0.0001"), future)])
        self.assertEqual(Lot.objects.get(number="A" * 64).available_quantity, 999999)
        self.assertEqual(Lot.objects.get(number="B").unit_cost, Decimal("0.0001"))
        product.refresh_from_db()
        self.assertEqual(product.average_cost, Decimal("9999989.9999"))
