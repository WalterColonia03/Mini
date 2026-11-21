from decimal import Decimal
from uuid import uuid4

from django.test import TestCase
from django.urls import reverse

from identity.models import Account, Role
from .models import Category, Product


class BarcodeCheckTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.actors = {}
        for code in [Role.Code.ADMIN, Role.Code.WAREHOUSE, Role.Code.SELLER]:
            role = Role.objects.create(code=code, name=code)
            cls.actors[code] = Account.objects.create_user(
                f"{code.lower()}@barcode-check.invalid", None, role=role, display_name=code)
        cls.category = Category.objects.create(name="Higiene")
        cls.existing = Product.objects.create(category=cls.category, name="Jabón de prueba",
            barcode="00AB-12", sale_price=Decimal("3.00"), is_active=False)
        cls.other = Product.objects.create(category=cls.category, name="Otro producto",
            barcode="OTHER", sale_price=Decimal("4.00"))

    def setUp(self):
        self.url = reverse("product-barcode-check")
        self.client.force_login(self.actors[Role.Code.ADMIN])
        self.before = list(Product.objects.order_by("pk").values())

    def assert_no_cache(self, response):
        self.assertIn("no-store", response["Cache-Control"])
        self.assertIn("no-cache", response["Cache-Control"])
        self.assertIn("max-age=0", response["Cache-Control"])

    def tearDown(self):
        self.assertEqual(list(Product.objects.order_by("pk").values()), self.before)

    def test_new_code_returns_only_duplicate_false_without_writing(self):
        response = self.client.get(self.url, {"barcode": "0012345678905"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"duplicate": False})
        self.assert_no_cache(response)

    def test_normalized_duplicate_includes_inactive_product_and_category(self):
        Category.objects.filter(pk=self.category.pk).update(is_active=False)
        for code in ["00AB-12", "  00 aB -12  ", "00\tAb-12"]:
            with self.subTest(code=code):
                response = self.client.get(self.url, {"barcode": code})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"duplicate": True})
                self.assert_no_cache(response)

    def test_edit_excludes_only_existing_current_product(self):
        response = self.client.get(self.url, {"barcode": "00ab-12", "product_id": self.existing.pk})
        self.assertEqual(response.json(), {"duplicate": False})
        response = self.client.get(self.url, {"barcode": "00ab-12", "product_id": self.other.pk})
        self.assertEqual(response.json(), {"duplicate": True})

    def test_invalid_or_unknown_current_product_rejected(self):
        for value, expected in [("", 400), ("not-a-uuid", 400), (str(uuid4()), 404)]:
            with self.subTest(value=value):
                response = self.client.get(self.url, {"barcode": "00AB-12", "product_id": value})
                self.assertEqual(response.status_code, expected)
                self.assertEqual(set(response.json()), {"error"})
                self.assert_no_cache(response)

    def test_missing_empty_invalid_and_oversized_barcode_rejected(self):
        for data in [{}, {"barcode": ""}, {"barcode": "   "}, {"barcode": "<script>"},
                     {"barcode": "A" * 65}, {"barcode": "AB_12"}]:
            with self.subTest(data=data):
                response = self.client.get(self.url, data)
                self.assertEqual(response.status_code, 400)
                self.assertEqual(set(response.json()), {"error"})
                self.assert_no_cache(response)

    def test_length_boundary_accepted(self):
        response = self.client.get(self.url, {"barcode": "A" * 64})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"duplicate": False})

    def test_anonymous_redirect_and_worker_denials_without_lookup_disclosure(self):
        self.client.logout()
        response = self.client.get(self.url, {"barcode": "00AB-12"})
        self.assertEqual(response.status_code, 302)
        self.assert_no_cache(response)
        for code in [Role.Code.WAREHOUSE, Role.Code.SELLER]:
            with self.subTest(role=code):
                self.client.force_login(self.actors[code])
                response = self.client.get(self.url, {"barcode": "00AB-12"})
                self.assertEqual(response.status_code, 403)
                self.assertEqual(set(response.json()), {"error"})
                self.assert_no_cache(response)

    def test_post_is_not_a_write_api(self):
        response = self.client.post(self.url, {"barcode": "00AB-12"})
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response["Allow"], "GET")
        self.assert_no_cache(response)
