"""Stage14-J: documented count origins, persistent replay and historical read model."""
import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, IntegrityError, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Product
from identity.models import Account
from inventory.models import InitialInventoryLoad, Lot, PhysicalAdjustment, StockReceipt, StockWriteOff
from inventory.services import register_physical_adjustment, write_off_stock, LotInput, register_stock_entry
from inventory import test_audit14g_receipts as receipt_tests


class AdjustmentIntegrationTests(TestCase):
    setUpTestData = classmethod(receipt_tests.ReceiptIntegrationTests.setUpTestData.__func__)
    snapshot = receipt_tests.ReceiptIntegrationTests.snapshot

    def setUp(self):
        self.lot=Lot.objects.get(product=self.product,number='INI')
        self.client.force_login(self.admin)
        self.key=uuid.uuid4()

    def adjust(self,**changes):
        args=dict(actor=self.admin,lot=self.lot,delta=2,reason='Conteo ficticio',idempotency_key=self.key)
        args.update(changes)
        return register_physical_adjustment(**args)

    def new_lot(self,**changes):
        args=dict(actor=self.admin,product=self.product,number='D',expiration_date=self.future,delta=2,
                  reason='Hallazgo con etiqueta fiable',idempotency_key=self.key)
        args.update(changes)
        return register_physical_adjustment(**args)

    def payload(self,**changes):
        args=dict(lot_id=str(self.lot.pk),delta='2',reason='Conteo ficticio',idempotency_key=str(self.key))
        args.update(changes)
        return args

    def test_existing_sequence_original_quantity_and_history_survive_changes(self):
        original=list(self.product.initial_load.lines.values())
        plus=self.adjust();minus=self.adjust(delta=-3,idempotency_key=uuid.uuid4())
        self.lot.refresh_from_db();self.product.refresh_from_db()
        self.assertEqual((self.lot.available_quantity,self.product.physical_stock,self.product.average_cost),(9,9,Decimal('3')))
        self.assertEqual((plus.unit_cost,minus.unit_cost),(Decimal('3'),Decimal('3')))
        self.assertEqual(original,list(self.product.initial_load.lines.values()))
        records=list(PhysicalAdjustment.objects.values())
        Product.objects.filter(pk=self.product.pk).update(name='Producto actual',barcode='ACTUAL')
        Account.objects.filter(pk=self.admin.pk).update(display_name='Autor actual')
        Lot.objects.filter(pk=self.lot.pk).update(number='NUEVO',number_normalized='NUEVO')
        self.assertEqual(records,list(PhysicalAdjustment.objects.values()))
        before=self.snapshot()
        for actor in (self.admin,self.worker):
            self.client.force_login(actor)
            response=self.client.get(reverse('physical-adjustment-detail',args=(plus.pk,)))
            body=response.content.decode().split('data-testid="adjustment-detail"')[1]
            self.assertIn(plus.product_snapshot_name,body);self.assertIn(plus.responsible_snapshot_name,body)
            self.assertNotIn('Autor actual',body);self.assertNotIn('Producto actual',body)
            result=self.client.get(reverse('product-movements',args=(self.product.pk,)))
            self.assertContains(result,'Ajuste físico — Lote INI');self.assertContains(result,'Ver ajuste',count=2)
            self.assertEqual(result.context['closing_balance'],9)
        self.assertEqual(self.snapshot(),before)

    def test_replay_across_sessions_divergence_and_revocation(self):
        url=reverse('physical-adjustment');payload=self.payload()
        first=self.client.post(url,payload);self.assertEqual(first.status_code,302)
        before=self.snapshot();other=Client();other.force_login(self.admin)
        self.assertEqual(other.post(url,payload).url,first.url)
        self.assertEqual(self.snapshot(),before)
        for changes in ({'delta':'3'},{'reason':'Otra causa'}):
            response=other.post(url,{**payload,**changes});self.assertEqual(response.status_code,200)
            self.assertContains(response,'otra solicitud');self.assertEqual(self.snapshot(),before)
        Product.objects.filter(pk=self.product.pk).update(is_active=False)
        before=self.snapshot();self.assertEqual(self.adjust().pk,PhysicalAdjustment.objects.get().pk)
        self.assertEqual(self.snapshot(),before)
        Account.objects.filter(pk=self.admin.pk).update(is_active=False)
        before=self.snapshot()
        with self.assertRaises(PermissionDenied):self.adjust()
        self.assertEqual(self.snapshot(),before)

    def test_new_lot_has_adjustment_origin_single_ledger_entry_and_is_sellable(self):
        result=self.new_lot();lot=result.lot
        self.assertEqual(lot.adjustment_origin_id,result.pk)
        self.assertEqual((lot.available_quantity,lot.unit_cost),(2,Decimal('3')))
        self.assertFalse(lot.is_initial);self.assertEqual(result.origin_snapshot,'AJUSTE '+str(result.pk))
        self.assertEqual(StockReceipt.objects.count(),0)
        self.assertEqual(InitialInventoryLoad.objects.count(),1)
        self.product.refresh_from_db();self.assertEqual(self.product.sellable_stock,12)
        response=self.client.get(reverse('product-movements',args=(self.product.pk,)))
        self.assertEqual(response.context['closing_balance'],12)
        self.assertEqual(len(response.context['page_obj']),2)
        before=self.snapshot();self.assertEqual(self.new_lot().pk,result.pk);self.assertEqual(self.snapshot(),before)
        with self.assertRaises(ValidationError):self.new_lot(idempotency_key=uuid.uuid4())
        self.assertEqual(self.snapshot(),before)
        # Existing-lot subsequent adjustment doesn't add another origin.
        self.adjust(lot=lot,delta=-1,idempotency_key=uuid.uuid4())
        writeoff=write_off_stock(actor=self.worker,lot=lot,quantity=1,reason='ROBO',notes='Faltante real ficticio')
        self.assertEqual(writeoff.origin_snapshot,'AJUSTE '+str(result.pk))

    def test_zero_stock_requires_documented_cost_and_preserves_previous_outputs(self):
        original=self.adjust(delta=-10)
        self.product.refresh_from_db();self.assertEqual(self.product.average_cost,0)
        before=self.snapshot()
        for changes in ({},{'unit_cost':Decimal('2.5')},{'cost_source':'Factura ficticia'}):
            with self.assertRaises(ValidationError):self.adjust(idempotency_key=uuid.uuid4(),**changes)
            self.assertEqual(self.snapshot(),before)
        result=self.adjust(idempotency_key=uuid.uuid4(),unit_cost=Decimal('2.5000'),cost_source='Documento ficticio 001')
        self.product.refresh_from_db();self.assertEqual((self.product.physical_stock,self.product.average_cost),(2,Decimal('2.5')))
        self.assertEqual(result.cost_source,'Documento ficticio 001');original.refresh_from_db();self.assertEqual(original.unit_cost,3)
        self.assertEqual(list(self.product.initial_load.lines.values_list('quantity',flat=True)),[10])

    def test_new_expired_inactive_lot_is_physical_only_and_zero_cost_is_supported(self):
        self.adjust(delta=-10)
        Product.objects.filter(pk=self.product.pk).update(is_active=False)
        result=self.new_lot(idempotency_key=uuid.uuid4(),expiration_date=timezone.localdate(),unit_cost=Decimal('2.5'),cost_source='Etiqueta y comprobante ficticio')
        self.product.refresh_from_db();self.assertEqual((self.product.physical_stock,self.product.sellable_stock),(2,0))
        self.assertEqual(result.lot.expiration_date,timezone.localdate())
        self.assertEqual(result.unit_cost,Decimal('2.5'))
        response=self.client.get(reverse('product-movements',args=(self.product.pk,)))
        self.assertEqual(response.context['closing_balance'],2)

    def test_invalid_existing_new_and_http_requests_do_not_consume_key(self):
        before=self.snapshot()
        for changes in ({'delta':0},{'delta':True},{'delta':1000000},{'delta':-11},{'reason':''},{'reason':'x'*301},
                        {'reason':'a\x00b'},{'unit_cost':Decimal('4')},{'unit_cost':Decimal('NaN')},{'cost_source':'x'*301},
                        {'unit_cost':Decimal('3.00001')},{'idempotency_key':'bad'},{'expiration_date':self.future}):
            with self.subTest(changes=changes),self.assertRaises(ValidationError):self.adjust(**changes)
            self.assertEqual(self.snapshot(),before)
        for changes in ({'number':' '},{'number':'x'*65},{'number':'a\x00b'},{'number':' ini '},{'delta':-1},
                        {'expiration_date':None},{'expiration_date':Lot.latest_expiration_date(timezone.localdate())+timedelta(days=1)}):
            with self.subTest(changes=changes),self.assertRaises(ValidationError):self.new_lot(**changes)
            self.assertEqual(self.snapshot(),before)
        url=reverse('physical-adjustment')
        for changes in ({'idempotency_key':''},{'idempotency_key':'bad'},{'delta':'1.5'},{'delta':'１２'},{'reason':' '},
                        {'delta':'0'},{'unit_cost':'2.12345'}):
            response=self.client.post(url,self.payload(**changes))
            self.assertEqual(response.status_code,200);self.assertTrue(response.context['form'].errors)
            self.assertContains(response,'id="adjustment-errors"');self.assertEqual(self.snapshot(),before)
        result=self.client.post(url,self.payload());self.assertEqual(result.status_code,302)

    def test_http_new_lot_roles_methods_and_unknown_id(self):
        url=reverse('physical-adjustment');payload=dict(product_id=str(self.product.pk),number='D',expiration_date=self.future.isoformat(),delta='2',reason='Conteo',idempotency_key=str(self.key))
        for actor in (self.worker,self.seller):
            self.client.force_login(actor);before=self.snapshot()
            self.assertEqual(self.client.post(url,payload).status_code,403);self.assertEqual(self.snapshot(),before)
        self.client.force_login(self.admin)
        first=self.client.post(url,payload);self.assertEqual(first.status_code,302)
        before=self.snapshot()
        for actor,code in ((self.admin,200),(self.worker,200),(self.seller,403)):
            self.client.force_login(actor);self.assertEqual(self.client.get(first.url).status_code,code)
        self.client.force_login(self.admin);self.assertEqual(self.client.post(first.url,{}).status_code,405)
        self.assertEqual(self.client.get(reverse('physical-adjustment-detail',args=(uuid.uuid4(),))).status_code,404)
        self.assertEqual(self.snapshot(),before)

    def test_product_without_initial_load_rejects_both_modes(self):
        p=Product.objects.create(name='Sin carga',barcode='SIN-CARGA',category=self.product.category,sale_price=10)
        before=self.snapshot()
        with self.assertRaisesMessage(ValidationError,'carga inicial'):self.new_lot(product=p)
        self.assertEqual(self.snapshot(),before)

    def test_postwrite_rollback_after_new_lot_record_stock_and_cost(self):
        import inventory.services as services
        original_create=PhysicalAdjustment.objects.create; original_save=Lot.save; original_reset=services.reset_average_cost_if_empty
        def fail_record(**kwargs): original_create(**kwargs);raise RuntimeError('after adjustment')
        def fail_stock(instance,*args,**kwargs):
            original_save(instance,*args,**kwargs)
            if not instance._state.adding and kwargs.get('update_fields'):raise RuntimeError('after stock/origin')
        def fail_cost(product):original_reset(product);raise RuntimeError('after cost')
        for target,name,fn in ((PhysicalAdjustment.objects,'create',fail_record),(Lot,'save',fail_stock),(services,'reset_average_cost_if_empty',fail_cost)):
            for new in (False,True):
                before=self.snapshot()
                with patch.object(target,name,fn),self.assertRaises(RuntimeError):
                    self.new_lot() if new else self.adjust()
                self.assertEqual(self.snapshot(),before)
        self.assertIsNotNone(self.new_lot().pk)

    def test_legacy_and_escaped_snapshot_output(self):
        old=PhysicalAdjustment.objects.create(lot=self.lot,delta=1,reason='Motivo antiguo',responsible=self.admin)
        response=self.client.get(reverse('physical-adjustment-detail',args=(old.pk,)))
        self.assertContains(response,'Registro anterior o incompleto')
        body=response.content.decode().split('data-testid="adjustment-detail"')[1]
        self.assertNotIn(self.admin.display_name,body);self.assertNotIn(self.product.name,body)
        result=self.adjust(reason='<script>motivo</script>')
        response=self.client.get(reverse('physical-adjustment-detail',args=(result.pk,)))
        self.assertContains(response,'&lt;script&gt;motivo&lt;/script&gt;');self.assertNotContains(response,'<script>motivo</script>')
