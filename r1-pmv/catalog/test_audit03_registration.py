from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from identity.models import Account, Role
from .models import Category, Product
from .services import register_canned_product


class RegistrationBoundaryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.admin = Account.objects.create_user("registro@audit.invalid", None, role=role, display_name="Registro")
        cls.category = Category.objects.create(name="Productos enlatados")

    def setUp(self):
        self.client.force_login(self.admin)
        self.data = dict(name="Atún de prueba", barcode="At-01", barcode_type="INTERNAL", category=str(self.category.pk),
                         unit="UND", sale_price="8.50", minimum_stock="")

    def test_empty_post_is_bound_with_six_required_fields(self):
        response = self.client.post(reverse("product-entry"), {})
        self.assertEqual(set(response.context["form"].errors), {"name", "barcode", "barcode_type", "category", "unit", "sale_price"})
        self.assertFalse(Product.objects.exists())

    def test_unicode_duplicate_names_rejected_with_a_single_message(self):
        self.client.post(reverse("product-entry"), self.data)
        for name in ["ATÚN DE PRUEBA", "  Atu\u0301n  de prueba "]:
            with self.subTest(name=name):
                response = self.client.post(reverse("product-entry"), {**self.data, "name": name, "barcode": "At-02"})
                self.assertFormError(response.context["form"], "name", ["Ya existe un producto registrado con este nombre."])
        self.assertEqual(Product.objects.count(), 1)

    def test_code_conflict_only_shows_the_relevant_field_error(self):
        self.client.post(reverse("product-entry"), self.data)
        response = self.client.post(reverse("product-entry"), {**self.data, "name": "Otro", "barcode": " a T- 01 "})
        self.assertFormError(response.context["form"], "barcode", ["Ya existe un producto con este código de barras."])
        self.assertEqual(Product.objects.count(), 1)

    def test_stale_or_removed_category_is_rejected_by_service(self):
        for remove in [False, True]:
            with self.subTest(remove=remove):
                cat = Category.objects.create(name=f"Temporal {remove}")
                rows = Category.objects.filter(pk=cat.pk)
                if remove:
                    rows.delete()
                else:
                    rows.update(is_active=False)
                with self.assertRaises(ValidationError) as caught:
                    register_canned_product(actor=self.admin, category=cat, name="Prueba", barcode="AT-01",
                                            unit="UND", sale_price=Decimal("8.50"), minimum_stock=None)
                self.assertEqual(caught.exception.message_dict["category"], ["Seleccione una categoría activa."])
        self.assertFalse(Product.objects.exists())

    def test_model_full_clean_rejects_whitespace_fields(self):
        product = Product(category=self.category, name="  ", barcode="   ", sale_price=Decimal("1.00"))
        with self.assertRaises(ValidationError) as caught:
            product.full_clean()
        self.assertTrue({"name", "barcode"}.issubset(caught.exception.message_dict))

    def test_optional_minimum_can_be_omitted_and_zero_is_preserved(self):
        self.data.pop("minimum_stock")
        for code, values, expected in [("T1", {}, 10), ("T2", {"minimum_stock": "0"}, 0)]:
            with self.subTest(code=code):
                response = self.client.post(reverse("product-entry"), {**self.data, **values, "barcode": code, "name": code})
                self.assertEqual(response.status_code, 302)
                self.assertEqual(Product.objects.get(barcode=code).minimum_stock, expected)

