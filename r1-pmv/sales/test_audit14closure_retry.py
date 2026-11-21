"""Stage 14: the new operation limit must not prevent historical recovery."""
import uuid
from decimal import Decimal

from django.db import connection
from django.test import TestCase
from django.urls import reverse

from cash.models import CashRegister
from cash.services import close_cash_shift, open_cash_shift
from identity.models import Account, Role
from .models import Sale, SaleDraft


class HistoricalLargeDiscountRetryTests(TestCase):
    def test_http_retry_preserves_large_historical_discount_after_shift_close(self):
        role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
        seller = Account.objects.create_user(
            "retry14@audit.invalid", None, role=role, display_name="Reintento 14"
        )
        CashRegister.objects.create(code="CAJA-01")
        shift = open_cash_shift(actor=seller, opening_amount=Decimal("0.00"))
        draft = SaleDraft.objects.create(cash_shift=shift, seller=seller, status=SaleDraft.Status.DISCARDED)
        # Historical fixture: this is not a newly authorized discounted checkout.
        sale = Sale.objects.create(
            cash_shift=shift, seller=seller, draft=draft, total_amount=Decimal("10000000.00"),
            base_amount=Decimal("10000000.00"), igv_amount=Decimal("0.00"),
            discount_amount=Decimal("10000000.00"), cash_received=Decimal("10000000.00"),
            change_given=Decimal("0.00"), correlative="HIST-14", idempotency_key=uuid.uuid4(),
        )
        close_cash_shift(actor=seller, counted_amount=Decimal("10000000.00"))
        self.client.force_login(seller)

        def snapshot():
            with connection.cursor() as cursor:
                result = {}
                for table in sorted(t for t in connection.introspection.table_names()
                                    if t.startswith(("catalog_", "inventory_", "sales_", "cash_"))):
                    cursor.execute('SELECT * FROM "' + table + '" ORDER BY 1')
                    result[table] = cursor.fetchall()
            return result

        before = snapshot()
        payload = {
            "cash_received": "10000000.00", "discount_amount": "10000000.00",
            "idempotency_key": str(sale.idempotency_key), "expected_subtotal": "20000000.00",
            "draft_signature": f"{draft.pk}|historical-fixture",
        }
        for _ in range(2):
            response = self.client.post(reverse("sales-checkout"), payload)
            self.assertRedirects(response, reverse("sales-receipt", args=[sale.pk]), fetch_redirect_response=False)
            self.assertEqual(snapshot(), before)
        payload["discount_amount"] = "10000000.01"
        response = self.client.post(reverse("sales-checkout"), payload)
        self.assertRedirects(response, reverse("sales-draft"), fetch_redirect_response=False)
        self.assertEqual(snapshot(), before)
