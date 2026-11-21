from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from identity.models import Account, Role
from .models import Category, Product
from .services import register_canned_product, update_product


class MinimumStockServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.admin = Account.objects.create_user("limits@audit.invalid", None, role=role, display_name="Prueba")
        cls.category = Category.objects.create(name="Límites")

    def test_registration_does_not_truncate_fractions_or_accept_booleans(self):
        for value in [0.5, Decimal("1.5"), True, float("inf"), Decimal("NaN")]:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError) as error:
                    register_canned_product(actor=self.admin, name="Mínimo", barcode="MIN-1",
                        category=self.category, unit="UND", sale_price=Decimal("8.50"), minimum_stock=value)
                self.assertIn("minimum_stock", error.exception.message_dict)
                self.assertFalse(Product.objects.exists())

    def test_edit_rejects_invalid_minimum_without_saving_other_fields(self):
        product = Product.objects.create(category=self.category, name="Original", barcode="MIN-EDIT",
                                         sale_price=Decimal("8.50"), minimum_stock=10)
        before = list(Product.objects.values())
        for value in [0.5, Decimal("1.5"), True, float("inf"), Decimal("NaN")]:
            with self.subTest(value=value):
                with self.assertRaises(ValidationError) as error:
                    update_product(actor=self.admin, product=product, name="Cambio rechazado", barcode="MIN-NEW",
                                   sale_price=Decimal("9.20"), minimum_stock=value, category=self.category)
                self.assertIn("minimum_stock", error.exception.message_dict)
                self.assertEqual(list(Product.objects.values()), before)

