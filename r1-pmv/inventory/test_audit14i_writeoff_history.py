"""14-I: replay survives sessions and write-off history survives master changes."""
import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import Lot, StockWriteOff
from inventory.services import LotInput, confirm_initial_load, register_stock_entry, write_off_stock
from inventory import test_audit14g_receipts as receipt_tests


class WriteoffHistoryTests(TestCase):
    setUpTestData = classmethod(receipt_tests.ReceiptIntegrationTests.setUpTestData.__func__)
    snapshot = receipt_tests.ReceiptIntegrationTests.snapshot

    def setUp(self):
        self.lot=Lot.objects.get(product=self.product,number='INI')
        self.client.force_login(self.worker)
        self.key=uuid.uuid4()

    def payload(self,**overrides):
        return dict(lot_id=str(self.lot.pk),quantity='2',reason='DAÑO',notes='Frasco roto ficticio',idempotency_key=str(self.key),**overrides)

    def create(self,**overrides):
        args=dict(actor=self.worker,lot=self.lot,quantity=2,reason='DAÑO',notes='Frasco roto ficticio',idempotency_key=self.key)
        args.update(overrides)
        return write_off_stock(**args)

    def test_snapshot_and_ledger_survive_master_changes(self):
        wo=self.create(); before=list(StockWriteOff.objects.values())
        Product.objects.filter(pk=self.product.pk).update(name='Nombre actual',barcode='INT-ACTUAL',is_active=False)
        Account.objects.filter(pk=self.worker.pk).update(display_name='Empleado actual')
        Lot.objects.filter(pk=self.lot.pk).update(number='NUEVO',number_normalized='NUEVO',expiration_date=self.future+timedelta(days=1))
        self.assertEqual(list(StockWriteOff.objects.values()),before)
        self.assertEqual(wo.unit_cost,Decimal('3'))
        self.assertEqual(wo.lot_snapshot_number,'INI')
        self.assertTrue(wo.origin_snapshot.startswith('Carga inicial '))
        self.lot.refresh_from_db();self.product.refresh_from_db()
        self.assertEqual(self.lot.available_quantity,8);self.assertEqual(self.product.average_cost,Decimal('3'))
        state=self.snapshot()
        for actor in (self.worker,self.admin):
            self.client.force_login(actor)
            result=self.client.get(reverse('stock-writeoff-receipt',args=(wo.pk,)))
            for value in (wo.product_snapshot_name,wo.responsible_snapshot_name,'INI','2 UND','S/ 3,0000','No es un comprobante de pago.'):
                self.assertContains(result,value)
            receipt_html=result.content.decode().split('data-testid="writeoff-receipt"',1)[1]
            self.assertNotIn('Empleado actual',receipt_html)
            moves=self.client.get(reverse('product-movements',args=(self.product.pk,)))
            self.assertContains(moves,'Lote INI');self.assertContains(moves,'Ver constancia de merma')
        self.assertEqual(self.snapshot(),state)

    def test_replay_across_sessions_and_after_state_date_changes(self):
        url=reverse('stock-writeoff');payload=self.payload()
        result=self.client.post(url,payload);self.assertEqual(result.status_code,302)
        wo=StockWriteOff.objects.get();before=self.snapshot()
        other_session=Client();other_session.force_login(self.worker)
        replay=other_session.post(url,{**payload,'notes':'  Frasco roto ficticio  '})
        self.assertEqual(replay.url,result.url);self.assertEqual(self.snapshot(),before)
        Product.objects.filter(pk=self.product.pk).update(is_active=False)
        Category.objects.filter(pk=self.product.category_id).update(is_active=False)
        before=self.snapshot()
        with patch('django.utils.timezone.localdate',return_value=self.future+timedelta(days=2)):
            self.assertEqual(self.create().pk,wo.pk)
        self.assertEqual(self.snapshot(),before)
        for actor,changes in ((self.other,{}),(self.worker,{'quantity':1})):
            with self.assertRaises(ValidationError):self.create(actor=actor,**changes)
            self.assertEqual(self.snapshot(),before)

    def test_invalid_http_keys_and_fields_do_not_mutate_or_consume_key(self):
        baseline=self.snapshot();payload=self.payload();url=reverse('stock-writeoff')
        for changes in ({'idempotency_key':''},{'idempotency_key':'bad'},{'quantity':'0'},{'quantity':'11'},
                        {'quantity':'1.5'},{'quantity':'1000000'},{'quantity':'１２'},{'reason':'OTRO'},
                        {'notes':' '},{'notes':'a\x00b'},{'reason':'VENCIMIENTO'}):
            with self.subTest(changes=changes):
                reply=self.client.post(url,{**payload,**changes})
                self.assertEqual(reply.status_code,200);self.assertTrue(reply.context['form'].errors)
                self.assertEqual(self.snapshot(),baseline)
        reply=self.client.post(url,payload)
        self.assertEqual(reply.status_code,302);self.assertEqual(StockWriteOff.objects.count(),1)

    def test_service_types_expiry_and_inactive_product_policy(self):
        before=self.snapshot()
        for changes in ({'quantity':True},{'quantity':0},{'quantity':Decimal('1')},{'quantity':11},
                        {'idempotency_key':'bad'},{'reason':'OTRO'},{'notes':None},{'notes':'a\x00b'}):
            with self.subTest(changes=changes),self.assertRaises(ValidationError):self.create(**changes)
            self.assertEqual(self.snapshot(),before)
        Product.objects.filter(pk=self.product.pk).update(is_active=False)
        with patch('django.utils.timezone.localdate',return_value=self.future):
            before=self.snapshot()
            with self.assertRaises(ValidationError):self.create(reason='DAÑO')
            with self.assertRaises(ValidationError):self.create(reason='ROBO',notes='')
            self.assertEqual(self.snapshot(),before)
            theft=self.create(reason='ROBO');expired=self.create(reason='VENCIMIENTO',notes='',idempotency_key=uuid.uuid4())
            self.assertEqual(theft.reason,'ROBO');self.assertEqual(expired.reason,'VENCIMIENTO')
        self.lot.refresh_from_db();self.assertEqual(self.lot.available_quantity,6)

    def test_same_commercial_lot_has_unambiguous_receipt_origin(self):
        r1=register_stock_entry(actor=self.worker,product=self.product,lots=[LotInput('C',10,Decimal('6'),self.future)])
        r2=register_stock_entry(actor=self.worker,product=self.product,lots=[LotInput('C',5,Decimal('8'),self.future)])
        wo=self.create(lot=r2.lines.get().lot)
        self.assertEqual(wo.origin_snapshot,'Recepción '+r2.correlative)
        self.assertEqual(r1.lines.get().lot.available_quantity,10)
        self.assertEqual(r2.lines.get().lot.available_quantity,3)
        self.assertEqual(wo.unit_cost,Decimal('5.2'))

    def test_legacy_is_not_invented(self):
        wo=StockWriteOff.objects.create(lot=self.lot,quantity=1,reason='ROBO',notes='Dato conservado',responsible=self.worker,correlativo='B-00000099')
        before=self.snapshot();result=self.client.get(reverse('stock-writeoff-receipt',args=(wo.pk,)))
        self.assertContains(result,'Registro anterior o incompleto')
        self.assertContains(result,'Dato conservado');self.assertContains(result,'No disponible')
        receipt_html=result.content.decode().split('data-testid="writeoff-receipt"',1)[1]
        self.assertNotIn(self.product.name,receipt_html);self.assertNotIn(self.worker.display_name,receipt_html)
        self.assertEqual(self.snapshot(),before)

    def test_postwrite_failures_rollback_every_business_table_and_retry(self):
        import inventory.services as services
        original_create=StockWriteOff.objects.create
        original_save=Lot.save
        original_reset=services.reset_average_cost_if_empty
        def fail_create(**kwargs): original_create(**kwargs); raise RuntimeError('after row')
        def fail_save(instance,*args,**kwargs): original_save(instance,*args,**kwargs); raise RuntimeError('after stock')
        def fail_reset(product): original_reset(product); raise RuntimeError('after cost')
        for target,replacement in ((StockWriteOff.objects,'create'),(Lot,'save'),(services,'reset_average_cost_if_empty')):
            callback={'create':fail_create,'save':fail_save,'reset_average_cost_if_empty':fail_reset}[replacement]
            before=self.snapshot()
            with patch.object(target,replacement,callback),self.assertRaises(RuntimeError):self.create(quantity=10)
            self.assertEqual(self.snapshot(),before)
        wo=self.create(quantity=10);self.assertEqual(wo.unit_cost,Decimal('3'))
        self.product.refresh_from_db();self.assertEqual(self.product.average_cost,Decimal('0'))

    def test_receipt_roles_methods_unknown_and_revoked_replay(self):
        wo=self.create();url=reverse('stock-writeoff-receipt',args=(wo.pk,));before=self.snapshot()
        for actor,code in ((self.admin,200),(self.worker,200),(self.seller,403)):
            self.client.force_login(actor);self.assertEqual(self.client.get(url).status_code,code)
        self.client.force_login(self.worker)
        self.assertEqual(self.client.post(url,{}).status_code,405)
        self.assertEqual(self.client.get(reverse('stock-writeoff-receipt',args=(uuid.uuid4(),))).status_code,404)
        self.assertEqual(self.snapshot(),before)
        Account.objects.filter(pk=self.worker.pk).update(is_active=False)
        before=self.snapshot()
        with self.assertRaises(PermissionDenied):self.create()
        self.assertEqual(self.snapshot(),before)

    def test_receipt_escapes_notes_and_conserves_full_detail(self):
        notes='<script>alert(1)</script>\n'+'Detalle ficticio '*200
        wo=self.create(notes=notes)
        response=self.client.get(reverse('stock-writeoff-receipt',args=(wo.pk,)))
        self.assertContains(response,'&lt;script&gt;alert(1)&lt;/script&gt;')
        self.assertNotContains(response,'<script>alert(1)</script>')
        self.assertEqual(StockWriteOff.objects.get().notes,notes.strip())

    def test_same_key_after_stock_exhausted_returns_same_result(self):
        wo=self.create(quantity=10);before=self.snapshot()
        self.assertEqual(self.create(quantity=10).pk,wo.pk)
        self.assertEqual(self.snapshot(),before)
