"""Logout failure must roll back a discarded draft and leave the session usable."""
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import logout as actual_logout
from django.contrib.sessions.models import Session
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cash.models import CashRegister, CashShift
from cash.services import open_cash_shift
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot
from sales.models import SaleDraft
from sales.services import add_product_to_draft


class LogoutAtomicAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        seller_role, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})
        warehouse_role, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
        cls.seller = Account.objects.create_user("atomic-seller@example.invalid", "SampleFixture8!", display_name="Vendedor Test", role=seller_role)
        warehouse = Account.objects.create_user("atomic-warehouse@example.invalid", "SampleFixture8!", display_name="Almacen Test", role=warehouse_role)
        CashRegister.objects.create(code="CAJA-01")
        category = Category.objects.create(name="Auditoria atomicidad")
        cls.product = Product.objects.create(category=category, name="Producto ficticio", barcode="775000000248", sale_price=Decimal("4.00"))
        load = InitialInventoryLoad.objects.create(product=cls.product, responsible=warehouse)
        cls.lot = Lot.objects.create(product=cls.product, initial_load=load, number="ATOMIC-02", initial_quantity=10,
                                     available_quantity=10, unit_cost=Decimal("2.00"), expiration_date=timezone.localdate()+timedelta(days=30))

    def test_failure_after_discard_rolls_back_draft_and_keeps_session(self):
        shift = open_cash_shift(actor=self.seller, opening_amount=Decimal("25.00"))
        draft = add_product_to_draft(actor=self.seller, product_id=self.product.pk, quantity=2)
        self.client.force_login(self.seller)
        session_key = self.client.session.session_key
        def fail_after_logout(request):
            actual_logout(request)
            raise RuntimeError("simulated logout failure")

        with patch("identity.views.logout", side_effect=fail_after_logout):
            with self.assertRaises(RuntimeError):
                self.client.post(reverse("logout"))
        draft.refresh_from_db()
        shift.refresh_from_db()
        self.lot.refresh_from_db()
        self.assertEqual(draft.status, SaleDraft.Status.ACTIVE)
        self.assertEqual(draft.lines.count(), 1)
        self.assertEqual(draft.lines.get().quantity, 2)
        self.assertEqual(shift.status, CashShift.Status.OPEN)
        self.assertEqual(self.lot.available_quantity, 10)
        self.assertTrue(Session.objects.filter(session_key=session_key).exists())
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

    def test_confirmed_logout_discards_and_revokes_session(self):
        shift = open_cash_shift(actor=self.seller, opening_amount=Decimal("25.00"))
        draft = add_product_to_draft(actor=self.seller, product_id=self.product.pk, quantity=2)
        self.client.force_login(self.seller)
        session_key = self.client.session.session_key
        self.assertEqual(self.client.post(reverse("logout")).status_code, 302)
        draft.refresh_from_db()
        shift.refresh_from_db()
        self.lot.refresh_from_db()
        self.assertEqual(draft.status, SaleDraft.Status.DISCARDED)
        self.assertEqual(draft.lines.count(), 0)
        self.assertEqual(shift.status, CashShift.Status.OPEN)
        self.assertEqual(self.lot.available_quantity, 10)
        self.assertFalse(Session.objects.filter(session_key=session_key).exists())
