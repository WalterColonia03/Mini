from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from cash.models import CashRegister, CashShift
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.services import LotInput, confirm_initial_load, register_stock_entry
from sales.models import Sale, SaleLine
from sales.services import add_product_to_draft, checkout_sale


class HistoricalCostTests(TestCase):
    def setUp(self):
        seller_role = Role.objects.create(code='VENDEDOR', name='Seller')
        warehouse_role = Role.objects.create(code='ALMACENERO', name='Warehouse')
        self.seller = Account.objects.create_user('seller@cost.invalid', None, display_name="Vendedor ficticio", role=seller_role)
        self.worker = Account.objects.create_user('worker@cost.invalid', None, display_name="Almacen ficticio", role=warehouse_role)
        CashShift.objects.create(cash_register=CashRegister.objects.create(code='COST'),
                                 seller=self.seller, opening_amount=Decimal('50'))
        self.product = Product.objects.create(category=Category.objects.create(name='Cost'),
                                             name='Cost', barcode='COST', sale_price=Decimal('9'))
        self.future = timezone.localdate() + timedelta(days=30)
        confirm_initial_load(actor=self.worker, product=self.product,
                             lots=[LotInput('A', 10, Decimal('2'), self.future),
                                   LotInput('B', 10, Decimal('4'), self.future + timedelta(days=1))])

    def sell(self, quantity=2):
        draft = add_product_to_draft(actor=self.seller, product_id=self.product.pk, quantity=quantity)
        key = uuid4()
        sale = checkout_sale(actor=self.seller, draft_id=draft.pk,
                             cash_received=Decimal('200'), idempotency_key=key)
        return sale, draft, key

    def replenish(self):
        register_stock_entry(actor=self.worker, product=self.product,
                             lots=[LotInput('C', 10, Decimal('6'), self.future)])

    def test_replenishment_preserves_cost_and_retry(self):
        sale, draft, key = self.sell()
        old = SaleLine.objects.filter(sale=sale).values().get()
        self.assertEqual(old['unit_cost'], Decimal('3.0000'))
        self.replenish()
        self.product.refresh_from_db()
        self.assertEqual(self.product.average_cost, Decimal('4.0714'))
        retry = checkout_sale(actor=self.seller, draft_id=draft.pk,
                              cash_received=Decimal('200'), idempotency_key=key)
        self.assertEqual(retry.pk, sale.pk)
        self.assertEqual(SaleLine.objects.filter(sale=sale).values().get(), old)
        next_sale, _, _ = self.sell()
        self.assertEqual(next_sale.lines.get().unit_cost, Decimal('4.0714'))

    def test_unknown_legacy_cost_stays_null(self):
        sale, _, _ = self.sell()
        SaleLine.objects.filter(sale=sale).update(unit_cost=None)
        self.replenish()
        self.assertIsNone(sale.lines.get().unit_cost)

    def test_zero_stock_uses_incoming_cost(self):
        sale, _, _ = self.sell(20)
        self.replenish()
        self.product.refresh_from_db()
        self.assertEqual(self.product.average_cost, Decimal('6.0000'))
        self.assertEqual(sale.lines.get().unit_cost, Decimal('3.0000'))

    def test_rejected_entry_preserves_cost_and_lots(self):
        sale, _, _ = self.sell()
        before = list(self.product.lots.order_by('pk').values())
        with self.assertRaises(ValidationError):
            register_stock_entry(actor=self.worker, product=self.product,
                                 lots=[LotInput('A', 1, Decimal('100'), self.future)])
        self.product.refresh_from_db()
        self.assertEqual(self.product.average_cost, Decimal('3.0000'))
        self.assertEqual(list(self.product.lots.order_by('pk').values()), before)
        self.assertEqual(sale.lines.get().unit_cost, Decimal('3.0000'))
        self.assertEqual(Sale.objects.count(), 1)

