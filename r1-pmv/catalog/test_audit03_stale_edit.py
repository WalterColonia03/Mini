from decimal import Decimal

from django.core import signing
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse

from identity.models import Account, Role
from .models import Category, Product
from .services import product_edit_snapshot, update_product


class StaleProductEditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.first = Account.objects.create_user("first@stale.invalid", "Password-123", role=role, display_name="Primero")
        cls.second = Account.objects.create_user("second@stale.invalid", "Password-123", role=role, display_name="Segundo")
        cls.category = Category.objects.create(name="Conservas")
        cls.other_category = Category.objects.create(name="Higiene")

    def setUp(self):
        self.product = Product.objects.create(
            category=self.category, name="Producto prueba", barcode="K7-A",
            sale_price=Decimal("8.50"), minimum_stock=10,
        )
        self.url = reverse("product-edit", args=[self.product.pk])
        self.first_client, self.second_client = Client(), Client()
        self.first_client.force_login(self.first)
        self.second_client.force_login(self.second)

    def payload(self, client):
        form = client.get(self.url).context["form"]
        return {
            "name": self.product.name, "barcode": self.product.barcode,
            "category": str(self.product.category_id), "sale_price": "8.50", "minimum_stock": "10",
            "edit_snapshot": form.initial["edit_snapshot"],
        }

    def test_stale_form_cannot_revert_commercial_changes(self):
        for field, value in [
            ("name", "Producto nuevo"), ("barcode", "K7-NEW"),
            ("sale_price", "9.20"), ("minimum_stock", "17"),
            ("category", str(self.other_category.pk)),
        ]:
            with self.subTest(field=field):
                self.product.refresh_from_db()
                original = product_edit_snapshot(self.product)
                first = self.payload(self.first_client)
                second = self.payload(self.second_client)
                first[field] = value
                self.assertEqual(self.first_client.post(self.url, first).status_code, 302)
                self.product.refresh_from_db()
                expected = product_edit_snapshot(self.product)
                self.assertNotEqual(original, expected)
                response = self.second_client.post(self.url, second)
                self.assertContains(response, "El producto cambió desde que abrió esta pantalla.")
                self.assertContains(response, "Revisar ficha actual")
                self.product.refresh_from_db()
                self.assertEqual(product_edit_snapshot(self.product), expected)
                # Restore a consistent original state before the next independent case.
                Product.objects.filter(pk=self.product.pk).update(
                    name=original["name"], barcode=original["barcode"],
                    barcode_normalized=Product.normalize_barcode(original["barcode"]),
                    search_name=Product.normalize_search_name(original["name"]),
                    category_id=original["category_id"], sale_price=original["sale_price"],
                    minimum_stock=original["minimum_stock"], is_active=original["is_active"],
                )

    def test_missing_tampered_and_other_product_snapshots_cannot_save(self):
        payload = self.payload(self.first_client)
        other = Product.objects.create(category=self.category, name="Otro producto", barcode="K7-B", sale_price=Decimal("2.00"))
        for token in ["", payload["edit_snapshot"] + "x", signing.dumps(product_edit_snapshot(other), salt="catalog.product-edit")]:
            with self.subTest(token=token):
                response = self.first_client.post(self.url, {**payload, "name": "Modificado", "edit_snapshot": token})
                self.assertContains(response, "El producto cambió desde que abrió esta pantalla.")
                self.product.refresh_from_db()
                self.assertEqual(self.product.name, "Producto prueba")

    def test_status_change_rejects_stale_snapshot(self):
        snapshot = product_edit_snapshot(self.product)
        Product.objects.filter(pk=self.product.pk).update(is_active=False)
        with self.assertRaises(ValidationError):
            update_product(actor=self.first, product=self.product, name="Modificado", barcode="K7-A",
                           sale_price=Decimal("8.50"), minimum_stock=10, expected_snapshot=snapshot)
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Producto prueba")

    def test_authorization_still_precedes_form_processing(self):
        warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        warehouse = Account.objects.create_user("warehouse@stale.invalid", None, role=warehouse_role, display_name="Almacén")
        self.second_client.force_login(warehouse)
        response = self.second_client.post(self.url, self.payload(self.first_client))
        self.assertEqual(response.status_code, 403)

    def test_service_rejects_malformed_snapshots_without_writing(self):
        valid = product_edit_snapshot(self.product)
        other = Product.objects.create(category=self.category, name="Otro K7", barcode="K7-OTHER", sale_price=Decimal("2.00"))
        variants = {
            "missing": {k: v for k, v in valid.items() if k != "is_active"},
            "extra": {**valid, "version": 1},
            "minimum_text": {**valid, "minimum_stock": "10"},
            "active_text": {**valid, "is_active": "true"},
            "price_text": {**valid, "sale_price": "precio"},
            "price_nan": {**valid, "sale_price": "NaN"},
            "category_text": {**valid, "category_id": "no-uuid"},
            "other_product": product_edit_snapshot(other),
            "not_dict": ["id"],
        }
        for label, snapshot in variants.items():
            with self.subTest(label=label):
                with self.assertRaises(ValidationError) as error:
                    update_product(actor=self.first, product=self.product, name="Modificado", barcode="K7-A",
                                   sale_price=Decimal("9.99"), minimum_stock=11, expected_snapshot=snapshot)
                self.assertEqual(error.exception.code, "stale_product")
                self.product.refresh_from_db()
                self.assertEqual(product_edit_snapshot(self.product), valid)

    def test_version_check_is_the_first_product_statement(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        snapshot = product_edit_snapshot(self.product)
        with CaptureQueriesContext(connection) as queries:
            update_product(actor=self.first, product=self.product, name="Producto prueba", barcode="K7-A",
                           sale_price=Decimal("9.20"), minimum_stock=10, expected_snapshot=snapshot)
        touching = [q["sql"].lstrip() for q in queries.captured_queries if "catalog_product" in q["sql"]]
        # SQLite has no row lock for SELECT FOR UPDATE: compare and lock in the first write.
        self.assertTrue(touching[0].startswith('UPDATE "catalog_product"'), touching[0])
        self.product.refresh_from_db()
        self.assertEqual(self.product.sale_price, Decimal("9.20"))

    def test_rejected_field_keeps_opened_version_for_correction(self):
        Product.objects.create(category=self.category, name="Ocupado K7", barcode="K7-TAKEN", sale_price=Decimal("2.00"))
        payload = self.payload(self.first_client)
        response = self.first_client.post(self.url, {**payload, "barcode": "K7-TAKEN"})
        self.assertContains(response, "Ya existe un producto con este código de barras.")
        self.assertContains(response, payload["edit_snapshot"])
        self.assertNotContains(response, "Revisar ficha actual")
        response = self.first_client.post(self.url, {**payload, "barcode": "K7-FIXED"})
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.barcode, "K7-FIXED")
        # The same opened version cannot be replayed after its own successful save.
        response = self.first_client.post(self.url, {**payload, "barcode": "K7-A"})
        self.assertContains(response, "El producto cambió desde que abrió esta pantalla.")
        self.product.refresh_from_db()
        self.assertEqual(self.product.barcode, "K7-FIXED")

    def test_repeated_identical_submission_is_not_reported_as_conflict(self):
        payload = {**self.payload(self.first_client), "sale_price": "9.20"}
        self.assertEqual(self.first_client.post(self.url, payload).status_code, 302)
        saved = Product.objects.values("updated_at", "sale_price").get(pk=self.product.pk)
        # Double click or reload re-sends the same values with the opened version.
        response = self.first_client.post(self.url, payload)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.values("updated_at", "sale_price").get(pk=self.product.pk), saved)
