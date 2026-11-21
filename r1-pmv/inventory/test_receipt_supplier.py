from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot, Supplier
from inventory.services import LotInput, confirm_initial_load, register_stock_entry


class ReceiptSupplierTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.worker = Account.objects.create_user("supplier-receipt@test.invalid", None,
                                                role=role, display_name="Receptor de prueba")
        cls.category = Category.objects.create(name="Higiene")

    def prepare(self, operation):
        product = Product.objects.create(name=operation.__name__, barcode=operation.__name__.replace("_", "-"),
                                         category=self.category, sale_price=Decimal("5.00"))
        self.future = timezone.localdate() + timedelta(days=30)
        if operation is register_stock_entry:
            confirm_initial_load(actor=self.worker, product=product,
                                 lots=[LotInput("BASE", 3, Decimal("1.00"), self.future)])
        return product

    def receipt(self, operation, product, supplier):
        return operation(actor=self.worker, product=product, supplier=supplier,
                         lots=[LotInput("NEW", 2, Decimal("2.00"), self.future)])

    def state(self):
        return (list(InitialInventoryLoad.objects.values()), list(Lot.objects.values()),
                list(Product.objects.order_by("pk").values()))

    def test_stale_active_supplier_is_rejected_atomically(self):
        for operation in [confirm_initial_load, register_stock_entry]:
            with self.subTest(operation=operation.__name__):
                product = self.prepare(operation)
                supplier = Supplier.objects.create(name=operation.__name__, ruc=str(Supplier.objects.count()).zfill(11))
                Supplier.objects.filter(pk=supplier.pk).update(is_active=False)
                before = self.state()
                with self.assertRaisesMessage(ValidationError, "El proveedor seleccionado está inactivo."):
                    self.receipt(operation, product, supplier)
                self.assertEqual(self.state(), before)

    def test_reactivated_supplier_uses_current_database_state(self):
        for operation in [confirm_initial_load, register_stock_entry]:
            with self.subTest(operation=operation.__name__):
                product = self.prepare(operation)
                supplier = Supplier.objects.create(name=operation.__name__, ruc=str(Supplier.objects.count()).zfill(11),
                                                   is_active=False)
                Supplier.objects.filter(pk=supplier.pk).update(is_active=True)
                self.receipt(operation, product, supplier)
                self.assertEqual(Lot.objects.get(product=product, number="NEW").supplier_id, supplier.pk)

    def test_removed_supplier_is_rejected_without_writes(self):
        for operation in [confirm_initial_load, register_stock_entry]:
            with self.subTest(operation=operation.__name__):
                product = self.prepare(operation)
                supplier = Supplier.objects.create(name=operation.__name__, ruc=str(Supplier.objects.count()).zfill(11))
                Supplier.objects.filter(pk=supplier.pk).delete()
                before = self.state()
                with self.assertRaisesMessage(ValidationError, "El proveedor seleccionado ya no existe."):
                    self.receipt(operation, product, supplier)
                self.assertEqual(self.state(), before)
