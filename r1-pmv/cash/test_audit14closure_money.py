"""Integration boundary: per-sale limits differ from cumulative cash closure."""
import uuid
from datetime import timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import connection, IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.services import confirm_initial_load, LotInput
from cash.models import CashRegister, CashShift, CashShiftClose
from cash.services import open_cash_shift, close_cash_shift
from cash.forms import CashCloseForm, CashOpeningForm
from sales.models import Sale, SaleDraftLine
from sales.services import add_product_to_draft, checkout_sale, discard_active_draft


class IntegrationMoneyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.worker,cls.seller=[Account.objects.create_user(email=code+'@money.invalid',password=None,
            display_name=code+' prueba',role=Role.objects.create(code=code,name=code)) for code in ('ALMACENERO','VENDEDOR')]
        CashRegister.objects.create(code='CAJA-01')
        cls.product=Product.objects.create(name='Producto límite14',barcode='INT-MONEY',category=Category.objects.create(name='Límites14'),sale_price=Decimal('5000000'))
        confirm_initial_load(actor=cls.worker,product=cls.product,lots=[LotInput('A',10,Decimal('3'),timezone.localdate()+timedelta(days=30))])

    def snapshot(self):
        with connection.cursor() as c:
            out={}
            for table in sorted(t for t in connection.introspection.table_names() if t.startswith(('cash_','sales_','inventory_','catalog_'))):
                c.execute('SELECT * FROM "'+table+'" ORDER BY 1');out[table]=c.fetchall()
        return out

    def sell(self,quantity=1,cash='5000000'):
        draft=add_product_to_draft(actor=self.seller,product_id=self.product.pk,quantity=quantity)
        return checkout_sale(actor=self.seller,draft_id=draft.pk,cash_received=Decimal(cash),idempotency_key=uuid.uuid4())

    def test_accumulated_two_sales_can_close_over_single_operation_limit(self):
        open_cash_shift(actor=self.seller,opening_amount=Decimal('0'))
        self.sell();self.sell()
        self.client.force_login(self.seller)
        reply=self.client.post(reverse('cash-close'),{'counted_amount':'10000000.00'})
        self.assertEqual(reply.status_code,302)
        close=CashShiftClose.objects.get()
        self.assertEqual(close.expected_amount,Decimal('10000000'))
        self.assertEqual(close.difference,Decimal('0'))
        state=self.snapshot();self.client.get(reply.url);self.assertEqual(self.snapshot(),state)

    def test_new_sale_and_cash_cannot_exceed_operation_limit(self):
        open_cash_shift(actor=self.seller,opening_amount=Decimal('0'))
        draft=add_product_to_draft(actor=self.seller,product_id=self.product.pk,quantity=2)
        before=self.snapshot()
        with self.assertRaises(ValidationError):
            checkout_sale(actor=self.seller,draft_id=draft.pk,cash_received=Decimal('10000000'),idempotency_key=uuid.uuid4())
        self.assertEqual(self.snapshot(),before)

    def test_accumulated_capacity_is_checked_before_any_sale_write(self):
        shift=open_cash_shift(actor=self.seller,opening_amount=Decimal('0'))
        old=Sale.objects.create(cash_shift=shift,seller=self.seller,total_amount=Decimal('999999999999.98'),
            base_amount=Decimal('999999999999.98'),igv_amount=0,discount_amount=0,cash_received=Decimal('999999999999.98'),
            change_given=0,correlative='LEGACY-MAX',idempotency_key=uuid.uuid4())
        Product.objects.filter(pk=self.product.pk).update(sale_price=Decimal('0.02'))
        draft=add_product_to_draft(actor=self.seller,product_id=self.product.pk,quantity=1)
        before=self.snapshot()
        with self.assertRaisesMessage(ValidationError,'capacidad'):
            checkout_sale(actor=self.seller,draft_id=draft.pk,cash_received=Decimal('0.02'),idempotency_key=uuid.uuid4())
        self.assertEqual(self.snapshot(),before)
        discard_active_draft(actor=self.seller)
        close=close_cash_shift(actor=self.seller,counted_amount=Decimal('999999999999.99'))
        self.assertEqual(close.difference,Decimal('0.01'))

    def test_form_limits_and_invalid_shapes(self):
        for form_class,field,maximum in ((CashOpeningForm,'opening_amount','9999999.99'),(CashCloseForm,'counted_amount','999999999999.99')):
            for value in ('0','0.01',maximum):
                self.assertTrue(form_class({field:value}).is_valid(),(field,value))
            for value in ('','-1','++1','+1','1e2','١٢','1.001',str(Decimal(maximum)+Decimal('0.01'))):
                self.assertFalse(form_class({field:value}).is_valid(),(field,value))

    def test_direct_database_constraints_and_negative_difference(self):
        shift=open_cash_shift(actor=self.seller,opening_amount=Decimal('10'))
        draft=add_product_to_draft(actor=self.seller,product_id=self.product.pk,quantity=1)
        line=draft.lines.get()
        for quantity in (0,1000000):
            with self.assertRaises(IntegrityError),transaction.atomic():SaleDraftLine.objects.filter(pk=line.pk).update(quantity=quantity)
        SaleDraftLine.objects.filter(pk=line.pk).update(quantity=999999)
        for values in ({'counted_amount':-1,'expected_amount':0,'difference':-1},
                       {'counted_amount':10,'expected_amount':15,'difference':0},
                       {'counted_amount':Decimal('1000000000000'),'expected_amount':0,'difference':Decimal('1000000000000')}):
            with self.assertRaises(IntegrityError),transaction.atomic():CashShiftClose.objects.create(cash_shift=shift,closed_by=self.seller,**values)
        record=CashShiftClose.objects.create(cash_shift=shift,closed_by=self.seller,counted_amount=10,expected_amount=15,difference=-5)
        self.assertEqual(record.difference,-5)

    def test_large_historical_sale_can_be_retrieved_without_new_policy_rewriting(self):
        shift=open_cash_shift(actor=self.seller,opening_amount=Decimal('0'))
        draft=add_product_to_draft(actor=self.seller,product_id=self.product.pk,quantity=1)
        key=uuid.uuid4()
        sale=Sale.objects.create(cash_shift=shift,seller=self.seller,draft=draft,total_amount=10000000,
            base_amount=10000000,igv_amount=0,cash_received=10000000,change_given=0,correlative='LEGACY-14',idempotency_key=key)
        before=self.snapshot()
        recovered=checkout_sale(actor=self.seller,draft_id=draft.pk,cash_received=Decimal('10000000'),idempotency_key=key)
        self.assertEqual(recovered.pk,sale.pk);self.assertEqual(self.snapshot(),before)
