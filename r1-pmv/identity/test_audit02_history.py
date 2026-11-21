"""Employee deactivation preserves a real fictional sale and inventory load."""
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cash.models import CashRegister, CashShift, CashShiftClose
from cash.services import close_cash_shift, open_cash_shift
from catalog.models import Category, Product
from identity.models import Account, Role
from identity.services import deactivate_employee
from inventory.models import InitialInventoryLoad, Lot
from sales.models import Sale, SaleLine
from sales.services import add_product_to_draft, checkout_sale


class EmployeeHistoryAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        admin_role, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
        seller_role, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})
        warehouse_role, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
        cls.admin = Account.objects.create_user("history-admin@example.invalid", "FixtureHistory8!", display_name="Admin Historia", role=admin_role)
        cls.seller = Account.objects.create_user("history-seller@example.invalid", "FixtureHistory8!", display_name="Vendedor Historia", role=seller_role)
        cls.warehouse = Account.objects.create_user("history-wh@example.invalid", "FixtureHistory8!", display_name="Almacen Historia", role=warehouse_role)
        CashRegister.objects.create(code="CAJA-01")
        category = Category.objects.create(name="Historia ficticia")
        cls.product = Product.objects.create(category=category, name="Producto Historia", barcode="775000000249", sale_price=Decimal("4.00"))
        cls.load = InitialInventoryLoad.objects.create(product=cls.product, responsible=cls.warehouse)
        cls.lot = Lot.objects.create(product=cls.product, initial_load=cls.load, responsible=cls.warehouse, number="HISTORIA02", initial_quantity=10,
                                     available_quantity=10, unit_cost=Decimal("2.00"), expiration_date=timezone.localdate()+timedelta(days=30))

    def test_deactivation_preserves_sale_shift_close_stock_load_and_admin_view(self):
        shift = open_cash_shift(actor=self.seller, opening_amount=Decimal("25.00"))
        draft = add_product_to_draft(actor=self.seller, product_id=self.product.pk, quantity=2)
        sale = checkout_sale(actor=self.seller, draft_id=draft.pk, cash_received=Decimal("8.00"), idempotency_key=uuid4())
        close = close_cash_shift(actor=self.seller, counted_amount=Decimal("33.00"))
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.available_quantity, 8)
        deactivate_employee(actor=self.admin, account=self.seller)
        deactivate_employee(actor=self.admin, account=self.warehouse)
        self.seller.refresh_from_db()
        self.warehouse.refresh_from_db()
        self.lot.refresh_from_db()
        self.assertFalse(self.seller.is_active)
        self.assertFalse(self.warehouse.is_active)
        self.assertTrue(Sale.objects.filter(pk=sale.pk, seller=self.seller, cash_shift=shift).exists())
        self.assertEqual(SaleLine.objects.filter(sale=sale).count(), 1)
        self.assertTrue(CashShift.objects.filter(pk=shift.pk, seller=self.seller, status="CLOSED").exists())
        self.assertTrue(CashShiftClose.objects.filter(pk=close.pk, cash_shift=shift, closed_by=self.seller).exists())
        self.assertTrue(InitialInventoryLoad.objects.filter(pk=self.load.pk, responsible=self.warehouse).exists())
        self.assertEqual(self.lot.responsible_id, self.warehouse.pk)
        self.assertEqual(self.lot.available_quantity, 8)
        self.client.force_login(self.admin)
        response = self.client.get(reverse("sales-history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, sale.correlative)
        listing = self.client.get(reverse("employee-list"))
        self.assertContains(listing, self.seller.email)
        self.assertContains(listing, self.warehouse.email)
        self.assertGreaterEqual(listing.content.decode("utf-8").count("Inactivo"), 2)
