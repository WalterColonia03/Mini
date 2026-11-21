from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cash.models import CashRegister, CashShift
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot
from sales.models import Sale, SaleDraft, SaleDraftLine
from sales.services import add_product_to_draft, checkout_sale, remove_draft_line, update_draft_line


class CheckoutReviewedDraftAudit03STests(TestCase):
    def setUp(self):
        seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
        warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacén")
        self.seller = Account.objects.create_user("audit03s-seller@test.invalid", "test-password", display_name="Vendedor", role=seller_role)
        warehouse = Account.objects.create_user("audit03s-stock@test.invalid", "test-password", display_name="Almacén", role=warehouse_role)
        register = CashRegister.objects.create(code="AUD03S")
        CashShift.objects.create(cash_register=register, seller=self.seller, opening_amount=Decimal("50.00"))
        category = Category.objects.create(name="AUD03S Alimentos")
        self.products = []
        for suffix in ("A", "B"):
            product = Product.objects.create(category=category, name="AUD03S " + suffix, barcode="AUD03S-" + suffix, sale_price=Decimal("8.50"))
            load = InitialInventoryLoad.objects.create(product=product, responsible=warehouse)
            Lot.objects.create(product=product, initial_load=load, number="AUD03S-" + suffix, initial_quantity=10,
                               available_quantity=10, unit_cost=Decimal("2.0000"), expiration_date=timezone.localdate() + timedelta(days=60))
            self.products.append(product)
        self.draft = add_product_to_draft(actor=self.seller, product_id=self.products[0].pk, quantity=2)
        self.line = SaleDraftLine.objects.get(draft=self.draft)
        self.client.force_login(self.seller)
        response = self.client.get(reverse("sales-checkout"))
        self.payload = {**response.context["form"].initial, "cash_received": "50.00", "discount_amount": ""}

    def checkout_with_intervening_change(self, change):
        def interleave(**kwargs):
            change()
            return checkout_sale(**kwargs)
        with patch("sales.views.checkout_sale", side_effect=interleave):
            return self.client.post(reverse("sales-checkout"), self.payload)

    def assert_no_sale_or_stock_change(self, response):
        self.assertContains(response, "La venta en preparación cambió")
        self.assertFalse(Sale.objects.exists())
        self.assertEqual(list(Lot.objects.order_by("number").values_list("available_quantity", flat=True)), [10, 10])
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, SaleDraft.Status.ACTIVE)

    def test_changed_quantity_after_view_check_requires_review_and_retry(self):
        response = self.checkout_with_intervening_change(
            lambda: update_draft_line(actor=self.seller, line_id=self.line.pk, quantity=3))
        self.assert_no_sale_or_stock_change(response)
        self.assertEqual(response.context["form"].data["expected_subtotal"], "25.50")
        confirmed = self.client.post(reverse("sales-checkout"), response.context["form"].data)
        self.assertEqual(confirmed.status_code, 302)
        self.assertEqual(Sale.objects.get().total_amount, Decimal("25.50"))

    def test_same_total_replacement_after_view_check_requires_review(self):
        def replace():
            # Create the replacement before removing the old line so the draft
            # remains active and has the same UUID and total.
            add_product_to_draft(actor=self.seller, product_id=self.products[1].pk, quantity=2)
            remove_draft_line(actor=self.seller, line_id=self.line.pk)
        response = self.checkout_with_intervening_change(replace)
        self.assert_no_sale_or_stock_change(response)
        self.assertEqual(response.context["form"].data["expected_subtotal"], "17.00")
        self.assertEqual(SaleDraftLine.objects.get(draft=self.draft).product_id, self.products[1].pk)

    def test_price_refresh_does_not_overwrite_a_changed_draft(self):
        product = self.products[0]
        product.sale_price = Decimal("9.50")
        product.save(update_fields=["sale_price"])
        response = self.checkout_with_intervening_change(
            lambda: add_product_to_draft(actor=self.seller, product_id=self.products[1].pk, quantity=1))
        self.assert_no_sale_or_stock_change(response)
        self.line.refresh_from_db()
        self.assertEqual(self.line.unit_price, Decimal("8.50"))
        self.assertEqual(SaleDraftLine.objects.filter(draft=self.draft).count(), 2)

    def test_existing_idempotent_sale_returns_even_with_review_snapshot(self):
        first = checkout_sale(actor=self.seller, draft_id=self.draft.pk, cash_received=Decimal("50.00"),
                              idempotency_key=self.payload["idempotency_key"], expected_subtotal=self.payload["expected_subtotal"],
                              expected_signature=self.payload["draft_signature"])
        second = checkout_sale(actor=self.seller, draft_id=self.draft.pk, cash_received=Decimal("50.00"),
                               idempotency_key=self.payload["idempotency_key"], expected_subtotal=self.payload["expected_subtotal"],
                               expected_signature=self.payload["draft_signature"])
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Sale.objects.count(), 1)
