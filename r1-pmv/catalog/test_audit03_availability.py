from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot
from inventory.services import LotInput, confirm_initial_load, register_stock_entry
from .models import Category, Product
from .services import toggle_category_status, toggle_product_availability


class ProductAvailabilityAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.admin = Account.objects.create_user("admin@estado.invalid", None, role=admin_role, display_name="Admin")
        cls.warehouse = Account.objects.create_user("almacen@estado.invalid", None, role=warehouse_role, display_name="Almacén")
        cls.category = Category.objects.create(name="Productos enlatados")

    def setUp(self):
        self.client.force_login(self.admin)
        self.product = Product.objects.create(category=self.category, name="Conserva estado", barcode="EST-1",
                                              sale_price=Decimal("8.50"))
        self.url = reverse("product-toggle", args=[self.product.pk])

    def test_named_disable_and_enable_requests_are_repeatable(self):
        for target in ["false", "true"]:
            self.client.post(self.url, {"is_active": target, "version": self.product.updated_at.isoformat()})
            self.product.refresh_from_db()
            expected = self.product.updated_at
            self.client.post(self.url, {"is_active": target, "version": self.product.updated_at.isoformat()})
            self.product.refresh_from_db()
            self.assertEqual(self.product.is_active, target == "true")
            self.assertEqual(self.product.updated_at, expected)

    def test_inactive_label_matches_criterion(self):
        self.client.post(self.url, {"is_active": "false", "version": self.product.updated_at.isoformat()})
        response = self.client.get(reverse("product-list"))
        self.assertContains(response, ">Inactivo<", html=False)

    def test_activation_message_describes_state_with_zero_stock(self):
        self.client.post(self.url, {"is_active": "false", "version": self.product.updated_at.isoformat()})
        self.product.refresh_from_db()
        response = self.client.post(self.url, {"is_active": "true", "version": self.product.updated_at.isoformat()}, follow=True)
        self.assertContains(response, "ahora está activo.")
        self.product.refresh_from_db()
        self.assertFalse(self.product.is_sellable)

    def test_stale_or_missing_version_cannot_reactivate(self):
        version = self.product.updated_at.isoformat()
        self.client.post(self.url, {"is_active": "false", "version": version})
        for payload in ({"is_active": "true"}, {"is_active": "true", "version": version}):
            response = self.client.post(self.url, payload, follow=True)
            self.assertContains(response, "Revise la disponibilidad actual")
            self.product.refresh_from_db()
            self.assertFalse(self.product.is_active)

    def test_bad_state_input_does_not_change_product(self):
        before = list(Product.objects.values())
        for value in ["", "yes", "2"]:
            with self.subTest(value=value):
                response = self.client.post(self.url, {"is_active": value}, follow=True)
                self.assertContains(response, "Seleccione un estado válido para el producto.")
                self.assertEqual(list(Product.objects.values()), before)

    def test_legacy_toggle_reads_current_state_even_with_stale_instance(self):
        stale = Product.objects.get(pk=self.product.pk)
        toggle_product_availability(actor=self.admin, product=self.product)
        toggle_product_availability(actor=self.admin, product=stale)
        self.product.refresh_from_db()
        self.assertTrue(self.product.is_active)

    def test_category_buttons_converge_on_the_requested_state(self):
        url = reverse("category-toggle", args=[self.category.pk])
        for target in ["false", "true"]:
            self.category.refresh_from_db()
            payload = {"is_active": target, "state_version": self.category.state_version, "confirm": "yes"}
            for attempt in range(2):
                response = self.client.post(url, payload)
                self.assertEqual(response.status_code, 302 if attempt == 0 else 409)
                self.category.refresh_from_db()
                self.assertEqual(self.category.is_active, target == "true")
        self.product.refresh_from_db()
        self.assertTrue(self.product.is_active)

    def test_legacy_category_toggle_rechecks_the_current_state(self):
        stale = Category.objects.get(pk=self.category.pk)
        toggle_category_status(actor=self.admin, category=self.category)
        toggle_category_status(actor=self.admin, category=stale)
        self.category.refresh_from_db()
        self.assertTrue(self.category.is_active)

    def test_inactive_product_blocks_both_inventory_services_without_writes(self):
        lots = [LotInput("ESTADO-1", 20, Decimal("5.00"), timezone.localdate() + timedelta(days=30))]
        confirm_initial_load(actor=self.warehouse, product=self.product, lots=lots)
        empty = Product.objects.create(category=self.category, name="Vacío", barcode="EST-2", sale_price=Decimal("3.00"))
        self.product.refresh_from_db()
        self.client.post(self.url, {"is_active": "false", "version": self.product.updated_at.isoformat()})
        self.client.post(reverse("product-toggle", args=[empty.pk]), {"is_active": "false", "version": empty.updated_at.isoformat()})
        # Pass the previously loaded objects, whose in-memory state is still active.
        before = {m._meta.label:list(m.objects.order_by("pk").values()) for m in [Product, Lot, InitialInventoryLoad]}
        for operation, article in [(confirm_initial_load, empty), (register_stock_entry, self.product)]:
            with self.assertRaises(ValidationError):
                operation(actor=self.warehouse, product=article, lots=lots)
        self.assertEqual(before, {m._meta.label:list(m.objects.order_by("pk").values()) for m in [Product, Lot, InitialInventoryLoad]})

