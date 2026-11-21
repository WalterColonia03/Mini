"""Stage 14: catalog prices obey the same monetary boundary as checkout."""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from identity.models import Account, Role
from .models import Category, Product
from .services import product_edit_snapshot, register_canned_product, update_product


class IntegrationPriceBoundaryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.admin = Account.objects.create_user(
            "price14@audit.invalid", None, role=role, display_name="Precio 14"
        )
        cls.category = Category.objects.create(name="Precios 14")
        cls.product = Product.objects.create(
            category=cls.category, name="Producto original", barcode="PRICE-14",
            barcode_type=Product.BarcodeType.INTERNAL, sale_price=Decimal("5.00")
        )

    def snapshot(self):
        with connection.cursor() as cursor:
            result = {}
            for table in sorted(t for t in connection.introspection.table_names()
                                if t.startswith(("catalog_", "inventory_", "sales_", "cash_"))):
                cursor.execute('SELECT * FROM "' + table + '" ORDER BY 1')
                result[table] = cursor.fetchall()
        return result

    def test_create_and_edit_http_reject_noncanonical_prices_without_mutation(self):
        self.client.force_login(self.admin)
        edit_url = reverse("product-edit", args=[self.product.pk])
        edit_token = self.client.get(edit_url).context["form"].initial["edit_snapshot"]
        for url in (reverse("product-entry"), edit_url):
            for raw in ("", "0", "-1", "+1", "++1", "١٢", "1e2", "1.001", "10000000.00"):
                with self.subTest(url=url, price=raw):
                    before = self.snapshot()
                    response = self.client.post(url, {
                        "name": "Cambio rechazado", "barcode_type": "INTERNAL",
                        "barcode": "PRICE-NEW", "category": str(self.category.pk),
                        "unit": "UND", "sale_price": raw, "minimum_stock": "10",
                        "edit_snapshot": edit_token,
                    })
                    self.assertEqual(response.status_code, 200)
                    self.assertIn("sale_price", response.context["form"].errors)
                    self.assertEqual(self.snapshot(), before)

    def test_services_reject_non_decimal_or_invalid_prices_without_mutation(self):
        invalid = (None, True, 1.0, "+1", "١٢", "1e2", Decimal("NaN"),
                   Decimal("Infinity"), Decimal("0"), Decimal("-1"),
                   Decimal("1E2"), Decimal("1.001"), Decimal("10000000.00"))
        for value in invalid:
            for editing in (False, True):
                with self.subTest(price=value, editing=editing):
                    before = self.snapshot()
                    kwargs = dict(actor=self.admin, name="Cambio rechazado", barcode="PRICE-NEW",
                                  category=self.category, sale_price=value, minimum_stock=10)
                    with self.assertRaises(ValidationError) as error:
                        if editing:
                            update_product(product=self.product, **kwargs)
                        else:
                            register_canned_product(unit="UND", **kwargs)
                    self.assertIn("sale_price", error.exception.message_dict)
                    self.assertEqual(self.snapshot(), before)

    def test_service_accepts_price_boundaries_and_preserves_legacy_replay(self):
        for index, value in enumerate((Decimal("0.01"), Decimal("9999999.99"))):
            product = register_canned_product(
                actor=self.admin, name=f"Precio límite {index}", barcode=f"PRICE-LIMIT-{index}",
                category=self.category, unit="UND", sale_price=value, minimum_stock=10,
            )
            self.assertEqual(product.sale_price, value)
        Product.objects.filter(pk=self.product.pk).update(sale_price=Decimal("10000000.00"))
        self.product.refresh_from_db()
        stale = product_edit_snapshot(self.product)
        stale["name"] = "Nombre anterior"
        before = self.snapshot()
        recovered = update_product(
            actor=self.admin, product=self.product, name=self.product.name,
            barcode=self.product.barcode, category=self.category, sale_price=self.product.sale_price,
            minimum_stock=self.product.minimum_stock, expected_snapshot=stale,
        )
        self.assertEqual(recovered.pk, self.product.pk)
        self.assertEqual(self.snapshot(), before)
