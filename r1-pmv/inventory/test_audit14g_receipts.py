"""DOC-03AI-01: receipt identity, immutable input history and transactional effects."""
import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot, StockReceipt, StockReceiptCounter, StockReceiptLine, Supplier
from inventory.services import LotInput, confirm_initial_load, register_stock_entry, register_physical_adjustment
from sales.models import SaleLine
from sales.services import add_product_to_draft, checkout_sale
from cash.models import CashRegister, CashShift


class ReceiptIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin, cls.worker, cls.seller = [Account.objects.create_user(
            email=code.lower()+"@receipt14g.invalid", password=None, display_name=code+" original",
            role=Role.objects.create(code=code, name=code)) for code in ("ADMIN", "ALMACENERO", "VENDEDOR")]
        cls.other = Account.objects.create_user(email="other@receipt14g.invalid", password=None,
            display_name="Otro almacenero", role=cls.worker.role)
        cls.product = Product.objects.create(category=Category.objects.create(name="Familia14G"),
            name="Producto original14G", barcode="INT-14G", sale_price=Decimal("10"))
        cls.supplier = Supplier.objects.create(name="Proveedor original14G", ruc="20000000014")
        cls.future = timezone.localdate()+timedelta(days=60)
        confirm_initial_load(actor=cls.worker, product=cls.product, supplier=cls.supplier,
            lots=[LotInput("INI",10,Decimal("3"),cls.future)])

    def setUp(self):
        self.client.force_login(self.worker)

    def snapshot(self):
        with connection.cursor() as cursor:
            tables=sorted(t for t in connection.introspection.table_names()
                          if t.startswith(("catalog_","inventory_","sales_","cash_")))
            result={}
            for table in tables:
                cursor.execute('SELECT * FROM "'+table+'" ORDER BY 1')
                result[table]=cursor.fetchall()
            return result

    def payload(self, key=None, number="C", quantity=10, cost="6", supplier=True):
        return {"product":str(self.product.pk),"supplier":str(self.supplier.pk) if supplier else "",
            "idempotency_key":str(key or uuid.uuid4()),"lots-TOTAL_FORMS":"1","lots-INITIAL_FORMS":"0",
            "lots-MIN_NUM_FORMS":"1","lots-MAX_NUM_FORMS":"1000","lots-0-number":number,
            "lots-0-quantity":str(quantity),"lots-0-unit_cost":cost,"lots-0-expiration_date":self.future.isoformat()}

    def confirm(self, payload):
        response=self.client.post(reverse("stock-entry"),payload)
        self.assertEqual(response.status_code,302,response.content[:200])
        receipt=StockReceipt.objects.get(idempotency_key=payload["idempotency_key"])
        self.assertEqual(response.url,reverse("stock-receipt",args=(receipt.pk,)))
        return receipt

    def test_two_receipts_same_lot_replay_and_divergent_content(self):
        payload=self.payload()
        first=self.confirm(payload)
        self.product.refresh_from_db()
        self.assertEqual((self.product.physical_stock,self.product.average_cost),(20,Decimal("4.5000")))
        before=self.snapshot()
        self.assertEqual(self.confirm({**payload,"lots-0-number":" c ","lots-0-unit_cost":"6.0000"}).pk,first.pk)
        self.assertEqual(self.snapshot(),before)
        for altered in ({"lots-0-quantity":"11"},{"lots-0-number":"D"},{"supplier":""}):
            self.assertContains(self.client.post(reverse("stock-entry"),{**payload,**altered}),"otro contenido o responsable")
            self.assertEqual(self.snapshot(),before)
        second=self.confirm(self.payload(quantity=5,cost="8",supplier=False))
        self.assertEqual([first.correlative,second.correlative],["R-00000001","R-00000002"])
        self.product.refresh_from_db()
        self.assertEqual((self.product.physical_stock,self.product.average_cost),(25,Decimal("5.2000")))
        self.assertEqual(list(StockReceiptLine.objects.order_by("receipt__correlative").values_list("quantity",flat=True)),[10,5])
        self.assertEqual(Lot.objects.filter(number_normalized="C").count(),2)
        selector=self.client.get(reverse("stock-writeoff"))
        self.assertContains(selector,"R-00000001")
        self.assertContains(selector,"R-00000002")
        self.client.force_login(self.admin)
        selector=self.client.get(reverse("physical-adjustment"))
        self.assertContains(selector,"R-00000001")
        self.assertContains(selector,"R-00000002")

    def test_order_independent_signature_and_distinct_actor_rejected(self):
        key=uuid.uuid4()
        lots=[LotInput("B",2,Decimal("6"),self.future),LotInput("A",3,Decimal("8"),self.future)]
        receipt=register_stock_entry(actor=self.worker,product=self.product,lots=lots,idempotency_key=key)
        before=self.snapshot()
        replay=register_stock_entry(actor=self.worker,product=self.product,lots=list(reversed(lots)),idempotency_key=key)
        self.assertEqual(replay.pk,receipt.pk)
        with self.assertRaisesMessage(ValidationError,"otro contenido o responsable"):
            register_stock_entry(actor=self.other,product=self.product,lots=lots,idempotency_key=key)
        self.assertEqual(self.snapshot(),before)

    def test_commercial_spaces_are_canonical_without_rewriting_legacy(self):
        payload=self.payload(number=" ab  12 ")
        receipt=self.confirm(payload)
        self.assertEqual(receipt.lines.get().number,"AB 12")
        before=self.snapshot()
        self.assertEqual(self.confirm({**payload,"lots-0-number":"AB 12"}).pk,receipt.pk)
        self.assertEqual(self.snapshot(),before)
        duplicate=self.payload(number="AB 12")
        duplicate.update({"lots-TOTAL_FORMS":"2","lots-1-number":"ab  12","lots-1-quantity":"1",
            "lots-1-unit_cost":"3","lots-1-expiration_date":self.future.isoformat()})
        self.assertContains(self.client.post(reverse("stock-entry"),duplicate),"está repetido")
        self.assertEqual(self.snapshot(),before)
        self.confirm(self.payload(number="AB12"))
        # Old spelling is compared canonically, but is never rewritten by a receipt.
        initial=self.product.lots.get(is_initial=True)
        Lot.objects.filter(pk=initial.pk).update(number="old  code",number_normalized="OLD  CODE")
        before=self.snapshot()
        payload=self.payload(number="OLD CODE")
        payload["lots-0-expiration_date"]=(self.future+timedelta(days=1)).isoformat()
        self.assertContains(self.client.post(reverse("stock-entry"),payload),"otro vencimiento")
        self.assertEqual(self.snapshot(),before)
        self.assertEqual(Lot.objects.get(pk=initial.pk).number_normalized,"OLD  CODE")

    def test_expired_or_inactive_confirmed_payload_replays_but_new_entry_rejects(self):
        payload=self.payload()
        receipt=self.confirm(payload)
        Product.objects.filter(pk=self.product.pk).update(is_active=False)
        Category.objects.filter(pk=self.product.category_id).update(is_active=False)
        Supplier.objects.filter(pk=self.supplier.pk).update(is_active=False)
        before=self.snapshot()
        with patch("django.utils.timezone.localdate",return_value=self.future+timedelta(days=1)):
            self.assertEqual(self.confirm(payload).pk,receipt.pk)
            response=self.client.post(reverse("stock-entry"),{**payload,"idempotency_key":str(uuid.uuid4())})
            self.assertEqual(response.status_code,200)
        self.assertEqual(self.snapshot(),before)
        Account.objects.filter(pk=self.worker.pk).update(is_active=False)
        with self.assertRaises(PermissionDenied):
            register_stock_entry(actor=self.worker,product=self.product,idempotency_key=payload["idempotency_key"],
                supplier=self.supplier,lots=[LotInput("C",10,Decimal("6"),self.future)])
        self.assertEqual(self.snapshot(),before)

    def test_invalid_inputs_keep_key_and_no_partial_state_then_correct(self):
        payload=self.payload()
        before=self.snapshot()
        variants=[{"lots-0-quantity":"0"},{"lots-0-unit_cost":"1.00001"},
            {"lots-0-expiration_date":timezone.localdate().isoformat()},{"idempotency_key":"invalid"},
            {"idempotency_key":""},{"lots-TOTAL_FORMS":"2","lots-1-number":" c ",
             "lots-1-quantity":"1","lots-1-unit_cost":"1","lots-1-expiration_date":self.future.isoformat()}]
        for changes in variants:
            response=self.client.post(reverse("stock-entry"),{**payload,**changes})
            self.assertEqual(response.status_code,200)
            self.assertEqual(self.snapshot(),before)
            if "idempotency_key" not in changes:
                self.assertContains(response,payload["idempotency_key"])
        receipt=self.confirm(payload)
        self.assertEqual(receipt.correlative,"R-00000001")
        before=self.snapshot()
        bad={**self.payload(quantity=5,cost="8"),"lots-0-expiration_date":(self.future+timedelta(days=1)).isoformat()}
        self.assertContains(self.client.post(reverse("stock-entry"),bad),"otro vencimiento")
        self.assertEqual(self.snapshot(),before)

    def test_snapshots_and_original_quantity_survive_master_changes_and_adjustment(self):
        receipt=self.confirm(self.payload())
        line=receipt.lines.get()
        register_physical_adjustment(actor=self.admin,lot=line.lot,delta=4,reason="Conteo de prueba")
        Product.objects.filter(pk=self.product.pk).update(name="Renombrado",barcode="OTRO")
        Supplier.objects.filter(pk=self.supplier.pk).update(name="Nuevo proveedor",ruc="20000000015")
        Account.objects.filter(pk=self.worker.pk).update(display_name="Otro nombre")
        Lot.objects.filter(pk=line.lot_id).update(number="Editado",number_normalized="EDITADO",unit_cost=Decimal("9"))
        before=self.snapshot()
        response=self.client.get(reverse("stock-receipt",args=(receipt.pk,)))
        for text in ("Producto original14G","INT-14G","Proveedor original14G","ALMACENERO original","10 UND","6,0000"):
            self.assertContains(response,text)
        self.assertEqual(line.quantity,10)
        self.assertEqual(Lot.objects.get(pk=line.lot_id).initial_quantity,14)
        movement=self.client.get(reverse("product-movements",args=(self.product.pk,)))
        self.assertContains(movement,"Recepción R-00000001")
        self.assertContains(movement,"+10")
        self.assertContains(movement,"Proveedor original14G")
        self.assertEqual(self.snapshot(),before)

    def test_permissions_on_post_and_receipt_and_counter_exhaustion(self):
        receipt=self.confirm(self.payload())
        before=self.snapshot()
        for actor in (self.admin,self.seller):
            self.client.force_login(actor)
            self.assertEqual(self.client.post(reverse("stock-entry"),self.payload()).status_code,403)
            expected=200 if actor==self.admin else 403
            self.assertEqual(self.client.get(reverse("stock-receipt",args=(receipt.pk,))).status_code,expected)
            self.assertEqual(self.snapshot(),before)
        self.client.force_login(self.worker)
        StockReceiptCounter.objects.update(last_number=99999999)
        before=self.snapshot()
        self.assertContains(self.client.post(reverse("stock-entry"),self.payload(number="MAX")),"Se agotó la capacidad")
        self.assertEqual(self.snapshot(),before)

    def test_failure_after_each_write_rolls_back_every_business_table(self):
        StockReceiptCounter.objects.create(key="global",last_number=0)
        payload=self.payload()
        before=self.snapshot()
        for target,method in ((StockReceiptCounter,"save"),(StockReceipt,"save"),
            (Lot.objects,"bulk_create"),(StockReceiptLine.objects,"bulk_create"),(Product,"save")):
            with self.subTest(target=str(target),method=method):
                original=getattr(target,method)
                writes=[]
                def write_then_fail(*args,**kwargs):
                    original(*args,**kwargs)
                    writes.append(self.snapshot()!=before)
                    raise RuntimeError("Fallo postwrite14G")
                with patch.object(target,method,autospec=True,side_effect=write_then_fail):
                    with self.assertRaisesMessage(RuntimeError,"postwrite14G"):
                        self.client.post(reverse("stock-entry"),payload)
                self.assertEqual(writes,[True])
                self.assertEqual(self.snapshot(),before)
        self.assertEqual(self.confirm(payload).correlative,"R-00000001")

    def test_sale_fefo_keeps_two_receipt_origins_and_average_snapshot(self):
        one=self.confirm(self.payload())
        two=self.confirm(self.payload(quantity=5,cost="8"))
        CashShift.objects.create(cash_register=CashRegister.objects.create(code="CAJA14G"),seller=self.seller,
            opening_amount=Decimal("100"))
        self.client.force_login(self.seller)
        self.assertEqual(self.client.post(reverse("sales-draft"),{"product_id":self.product.pk,"quantity":22}).status_code,302)
        review=self.client.get(reverse("sales-checkout"))
        response=self.client.post(reverse("sales-checkout"),{**review.context["form"].initial,"cash_received":"220"})
        self.assertEqual(response.status_code,302)
        line=SaleLine.objects.get()
        self.assertEqual(line.unit_cost,Decimal("5.2000"))
        assigned={a.lot_id:a.quantity for a in line.lot_allocations.all()}
        self.assertEqual(assigned[one.lines.get().lot_id],10)
        self.assertEqual(assigned[two.lines.get().lot_id],2)
        self.product.refresh_from_db()
        self.assertEqual((self.product.physical_stock,self.product.average_cost),(3,Decimal("5.2000")))


class ReceiptMigrationTests(TransactionTestCase):
    def test_old_rows_remain_identical_without_receipt_backfill(self):
        executor=MigrationExecutor(connection)
        latest=executor.loader.graph.leaf_nodes()
        old_target=("inventory","0007_output_unit_cost")
        try:
            executor.migrate([old_target])
            apps=executor.loader.project_state([target for target in latest if target[0] != "inventory"]+[old_target]).apps
            role=apps.get_model("identity","Role").objects.create(code="ALMACENERO",name="Almacenero")
            actor=apps.get_model("identity","Account").objects.create(email="legacy14g@invalid.test",password="!",role=role,display_name="Legado")
            category=apps.get_model("catalog","Category").objects.create(name="Legado",name_normalized="LEGADO")
            product=apps.get_model("catalog","Product").objects.create(category=category,name="Legado",search_name="legado",
                barcode="LEGACY",barcode_normalized="LEGACY",sale_price=Decimal("10"),average_cost=Decimal("3"))
            load=apps.get_model("inventory","InitialInventoryLoad").objects.create(product=product,responsible=actor)
            model=apps.get_model("inventory","Lot")
            for initial in (True,False):
                model.objects.create(product=product,initial_load=load,number=str(initial),number_normalized=str(initial),
                    is_initial=initial,initial_quantity=10,available_quantity=8,unit_cost=Decimal("3"),
                    expiration_date=timezone.localdate()+timedelta(days=30))
            old=list(model.objects.order_by("pk").values())
            MigrationExecutor(connection).migrate(latest)
            migrated = list(Lot.objects.order_by("pk").values())
            for row in migrated:
                self.assertIsNone(row.pop("adjustment_origin_id"))
            self.assertEqual(migrated,old)
            self.assertEqual(StockReceipt.objects.count(),0)
            self.assertEqual(StockReceiptLine.objects.count(),0)
        finally:
            MigrationExecutor(connection).migrate(latest)
