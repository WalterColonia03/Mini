from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cash.models import CashRegister, CashShift
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot
from sales.models import Sale, SaleDraft, SaleDraftLine


class CheckoutReviewRequiredTests(TestCase):
    def setUp(self):
        seller_role = Role.objects.create(code=Role.Code.SELLER, name='Vendedor')
        warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name='Almacenero')
        self.seller = Account.objects.create_user('review-seller@test.invalid', 'test-only-pass', display_name='Vendedor', role=seller_role)
        warehouse = Account.objects.create_user('review-warehouse@test.invalid', 'test-only-pass', display_name='Almacén', role=warehouse_role)
        register = CashRegister.objects.create(code='CAJA-REVIEW')
        CashShift.objects.create(cash_register=register, seller=self.seller, opening_amount=Decimal('50.00'))
        cat = Category.objects.create(name='Alimentos de prueba')
        self.product = Product.objects.create(category=cat, name='Producto prueba', barcode='REVIEW01', sale_price=Decimal('8.50'))
        load = InitialInventoryLoad.objects.create(product=self.product, responsible=warehouse)
        self.lot = Lot.objects.create(product=self.product, initial_load=load, number='REVIEW-1', initial_quantity=10, available_quantity=10,
                                      unit_cost=Decimal('2.0000'), expiration_date=timezone.localdate()+timedelta(days=60))
        self.client.force_login(self.seller)
        self.client.post(reverse('sales-draft'), {'product_id': str(self.product.pk), 'quantity':'2'})
        get = self.client.get(reverse('sales-checkout'))
        self.assertEqual(get.status_code, 200)
        self.data = {**get.context['form'].initial, 'cash_received':'50.00', 'discount_amount':''}
        self.line = SaleDraftLine.objects.get(product=self.product)
        self.client.post(reverse('sales-line-update', args=(self.line.pk,)), {'quantity':'3'})

    def test_omitted_review_fields_reject_and_allow_explicit_review(self):
        for omitted in (('expected_subtotal',), ('draft_signature',), ('expected_subtotal','draft_signature')):
            with self.subTest(omitted=omitted):
                payload = {k: v for k, v in self.data.items() if k not in omitted}
                response = self.client.post(reverse('sales-checkout'), payload)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'No se pudo verificar el resumen de la venta')
                self.assertEqual(Sale.objects.count(), 0)
                self.lot.refresh_from_db()
                self.assertEqual(self.lot.available_quantity, 10)
                self.line.refresh_from_db()
                self.assertEqual(self.line.quantity, 3)
                self.assertEqual(SaleDraft.objects.get(pk=self.line.draft_id).status, SaleDraft.Status.ACTIVE)
                self.assertEqual(response.context['form'].data['expected_subtotal'], '25.50')
                self.assertTrue(response.context['form'].data['draft_signature'])
        refreshed = response.context['form'].data.copy()
        confirmed = self.client.post(reverse('sales-checkout'), refreshed)
        self.assertEqual(confirmed.status_code, 302)
        sale = Sale.objects.get()
        self.assertEqual(sale.total_amount, Decimal('25.50'))
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.available_quantity, 7)

    def test_intact_obsolete_summary_is_rejected(self):
        response = self.client.post(reverse('sales-checkout'), self.data)
        self.assertContains(response, 'El resumen de la venta en preparación cambió')
        self.assertFalse(Sale.objects.exists())
