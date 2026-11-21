from decimal import Decimal
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import patch

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from identity.models import Account, Role
from .forms import ProductRegistrationForm
from .models import Category, Product
from .services import register_canned_product, update_product


class ProductPolicyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.admin = Account.objects.create_user("policy@audit.invalid", None, role=role, display_name="Prueba")
        cls.category = Category.objects.create(name="Auditoría")

    def register(self, name="Producto", barcode="POL-1", minimum_stock=10):
        return register_canned_product(actor=self.admin, name=name, barcode=barcode, category=self.category,
                                       unit="UND", sale_price=Decimal("8.50"), minimum_stock=minimum_stock)

    def edit(self, product, **values):
        return update_product(actor=self.admin, product=product, category=self.category,
                              **{**dict(name=product.name, barcode=product.barcode, sale_price=product.sale_price,
                                        minimum_stock=product.minimum_stock), **values})

    def test_default_and_integer_boundaries_in_both_services(self):
        for index, value in enumerate([None, 0, 999999]):
            p = self.register(name=f"Producto {index}", barcode=f"POL-{index}", minimum_stock=value)
            self.assertEqual(p.minimum_stock, 10 if value is None else value)
            for minimum in [0, 999999]:
                self.edit(p, minimum_stock=minimum)
                p.refresh_from_db()
                self.assertEqual(p.minimum_stock, minimum)

    def test_above_maximum_rejected_in_services_and_database(self):
        with self.assertRaises(ValidationError) as error:
            self.register(minimum_stock=1000000)
        self.assertIn("minimum_stock", error.exception.message_dict)
        self.assertFalse(Product.objects.exists())
        p = self.register()
        before = list(Product.objects.values())
        with self.assertRaises(ValidationError) as error:
            self.edit(p, name="Cambio rechazado", barcode="NEW", minimum_stock=1000000)
        self.assertIn("minimum_stock", error.exception.message_dict)
        self.assertEqual(list(Product.objects.values()), before)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Product.objects.filter(pk=p.pk).update(minimum_stock=1000000)
        self.assertEqual(list(Product.objects.values()), before)

    def test_name_unique_including_inactive_case_spaces_and_unicode(self):
        p = self.register(name="Atún  marca  170 g")
        Product.objects.filter(pk=p.pk).update(is_active=False)
        for variant in [" ATÚN marca 170 g ", "Atu\u0301n\tmarca 170 g"]:
            with self.subTest(variant=variant), self.assertRaises(ValidationError) as error:
                self.register(name=variant, barcode="NEW")
            self.assertEqual(error.exception.message_dict, {"name": ["Ya existe un producto registrado con este nombre."]})
        self.assertEqual(Product.objects.count(), 1)
        self.register(name="Atún marca 400 g", barcode="OTHER")
        self.register(name="Atun marca 170 g", barcode="NOACCENT")
        self.assertEqual(Product.objects.count(), 3)

    def test_edit_name_collision_rolls_back_other_fields_and_self_is_allowed(self):
        p = self.register(name="Original")
        self.register(name="Ocupado", barcode="OTHER")
        before = list(Product.objects.order_by("pk").values())
        with self.assertRaises(ValidationError) as error:
            self.edit(p, name=" OCUPADO ", barcode="NEW", sale_price=Decimal("9.20"), minimum_stock=0)
        self.assertEqual(error.exception.message_dict, {"name": ["Ya existe un producto registrado con este nombre."]})
        self.assertEqual(list(Product.objects.order_by("pk").values()), before)
        p.refresh_from_db()
        self.edit(p, name=" ORIGINAL ")
        p.refresh_from_db()
        self.assertEqual(p.name, "ORIGINAL")

    def test_prevalidated_forms_cannot_bypass_name_uniqueness(self):
        forms = [ProductRegistrationForm(data=dict(name="Nombre nuevo", barcode_type="INTERNAL", barcode=code, category=str(self.category.pk),
                 unit="UND", sale_price="8.50", minimum_stock="10")) for code in ["PRE-1", "PRE-2"]]
        self.assertTrue(all(f.is_valid() for f in forms))
        register_canned_product(actor=self.admin, **forms[0].cleaned_data)
        with self.assertRaises(ValidationError) as error:
            register_canned_product(actor=self.admin, **forms[1].cleaned_data)
        self.assertIn("name", error.exception.message_dict)
        self.assertEqual(Product.objects.count(), 1)

    def test_database_unique_key_and_partial_save_stay_consistent(self):
        p = self.register()
        p.name = " Otra   marca "
        p.save(update_fields=["name"])
        p.refresh_from_db()
        self.assertEqual((p.name, p.search_name), ("Otra marca", "otra marca"))
        with self.assertRaises(IntegrityError), transaction.atomic():
            Product.objects.create(category=self.category, name="OTRA marca", barcode="NEW", sale_price=Decimal("1"))

    def test_unrelated_integrity_errors_are_not_reported_as_duplicates(self):
        p = self.register()
        with patch.object(Product, "save", side_effect=IntegrityError("unrelated")):
            with self.assertRaises(IntegrityError):
                self.register(name="Otro", barcode="NEW")
            with self.assertRaises(IntegrityError):
                self.edit(p)
        self.assertEqual(Product.objects.count(), 1)

    def test_migration_collision_preflight_changes_nothing(self):
        first = self.register(name="Primero")
        second = self.register(name="Segundo", barcode="SECOND")
        Product.objects.filter(pk=first.pk).update(name=" Mismo   nombre ")
        Product.objects.filter(pk=second.pk).update(name="MISMO nombre")
        before = list(Product.objects.order_by("pk").values())
        migrate = import_module("catalog.migrations.0005_product_name_and_minimum_policy").prepare_product_keys
        with self.assertRaisesMessage(RuntimeError, "Product name collision"):
            migrate(apps, SimpleNamespace(connection=SimpleNamespace(alias="default")))
        self.assertEqual(list(Product.objects.order_by("pk").values()), before)
