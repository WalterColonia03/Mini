"""14-H1: original load values and honest legacy output; no Kardex balance claim."""
import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, IntegrityError, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, InitialLoadLine, Lot, Supplier
from inventory.services import LotInput, confirm_initial_load, register_stock_entry, register_physical_adjustment, write_off_stock
from cash.models import CashRegister, CashShift
from sales.services import add_product_to_draft, checkout_sale


def snapshot():
    with connection.cursor() as cursor:
        result = {}
        for table in sorted(connection.introspection.table_names()):
            if table.startswith(("catalog_", "inventory_", "cash_", "sales_")):
                cursor.execute('SELECT * FROM "'+table+'" ORDER BY 1')
                result[table] = cursor.fetchall()
        return result


class InitialHistoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin, cls.worker, cls.seller = [Account.objects.create_user(
            email=code.lower()+"@history14h.invalid",password=None,display_name=code+" original",
            role=Role.objects.create(code=code,name=code)) for code in ("ADMIN","ALMACENERO","VENDEDOR")]
        cls.product = Product.objects.create(category=Category.objects.create(name="Familia14H"),
            name="Producto original",barcode="INT-14H",sale_price=Decimal("10"))
        cls.supplier = Supplier.objects.create(name="Proveedor original",ruc="20000000014")
        cls.future = timezone.localdate()+timedelta(days=60)

    def confirm(self, supplier=True):
        return confirm_initial_load(actor=self.worker,product=self.product,supplier=self.supplier if supplier else None,
            lots=[LotInput(" a  1 ",3,Decimal("2.1234"),self.future),LotInput("B",7,Decimal("4"),self.future+timedelta(days=1))])

    def test_originals_survive_master_renames_adjustment_receipt_sale_and_loss(self):
        load = self.confirm()
        original = list(InitialInventoryLoad.objects.values())
        lines = list(load.lines.values())
        self.assertEqual(load.average_cost_snapshot,Decimal("3.4370"))
        self.assertEqual([(l.number,l.quantity,l.unit_cost) for l in load.lines.all()],
                         [("A 1",3,Decimal("2.1234")),("B",7,Decimal("4"))])
        for line in load.lines.select_related("lot"):
            self.assertEqual(line.received_at,line.lot.received_at)
        Product.objects.filter(pk=self.product.pk).update(name="Producto actual",barcode="INT-ACTUAL")
        Supplier.objects.filter(pk=self.supplier.pk).update(name="Proveedor actual",ruc="20000000015",is_active=False)
        Account.objects.filter(pk=self.worker.pk).update(display_name="Autor actual")
        first = load.lines.get(number="A 1").lot
        register_physical_adjustment(actor=self.admin,lot=first,delta=2,reason="Recuento ficticio")
        register_stock_entry(actor=self.worker,product=self.product,lots=[LotInput("POST",5,Decimal("6"),self.future+timedelta(days=2))])
        CashShift.objects.create(cash_register=CashRegister.objects.create(code="14H"),seller=self.seller,opening_amount=100)
        draft = add_product_to_draft(actor=self.seller,product_id=self.product.pk,quantity=4)
        checkout_sale(actor=self.seller,draft_id=draft.pk,cash_received=Decimal("40"),idempotency_key=uuid.uuid4())
        first.refresh_from_db()
        self.assertEqual(first.available_quantity,1)
        write_off_stock(actor=self.worker,lot=first,quantity=1,reason="ROBO",notes="Faltante ficticio")
        self.assertEqual(list(InitialInventoryLoad.objects.values()),original)
        self.assertEqual(list(load.lines.values()),lines)
        self.client.force_login(self.admin)
        result = self.client.get(reverse("inventory-load-created",args=(load.pk,)))
        for text in ("Producto original","INT-14H","ALMACENERO original","Proveedor original","20000000014","S/ 2,1234","3 UND","S/ 3,44","Datos actuales"):
            self.assertContains(result,text)
        self.assertEqual(len(result.context["lines"]),2)
        moves = self.client.get(reverse("product-movements",args=(self.product.pk,)))
        self.assertContains(moves,"Carga inicial — Lote A 1 (Proveedor original)")
        self.assertContains(moves,"ALMACENERO original")
        self.assertContains(moves,"Ver carga inicial",count=2)

    def test_no_supplier_and_output_escaping_with_boundary_values(self):
        Product.objects.filter(pk=self.product.pk).update(name="<script>original</script>")
        load = confirm_initial_load(actor=self.worker,product=self.product,lots=[
            LotInput("X"*64,999999,Decimal("9999999.9999"),self.future)])
        self.assertEqual(load.supplier_snapshot_name,"")
        self.assertEqual(load.lines.get().quantity,999999)
        self.assertEqual(load.lines.get().unit_cost,Decimal("9999999.9999"))
        self.client.force_login(self.worker)
        response = self.client.get(reverse("inventory-load-created",args=(load.pk,)))
        self.assertContains(response,"Sin proveedor asignado")
        self.assertContains(response,"&lt;script&gt;original&lt;/script&gt;")
        self.assertNotContains(response,"<script>original</script>")

    def test_expiration_and_deactivation_do_not_rewrite_originals(self):
        load = self.confirm()
        Product.objects.filter(pk=self.product.pk).update(is_active=False)
        before = snapshot()
        self.client.force_login(self.worker)
        with patch("django.utils.timezone.localdate",return_value=self.future+timedelta(days=1)):
            response = self.client.get(reverse("inventory-load-created",args=(load.pk,)))
            self.assertContains(response,"Datos originales de la carga inicial")
            self.assertEqual(response.context["load"].product.sellable_stock,0)
            self.assertEqual(response.context["load"].product.physical_stock,10)
        self.assertEqual(snapshot(),before)

    def test_legacy_capacity_is_never_reported_as_original_quantity(self):
        load = InitialInventoryLoad.objects.create(product=self.product,responsible=self.worker)
        lot = Lot.objects.create(product=self.product,initial_load=load,number="LEGADO",initial_quantity=12,
            available_quantity=8,unit_cost=Decimal("3"),expiration_date=self.future)
        self.client.force_login(self.worker)
        before = snapshot()
        page = self.client.get(reverse("inventory-load-created",args=(load.pk,)))
        self.assertContains(page,"Cantidad original no disponible")
        self.assertFalse(page.context["has_snapshot"])
        self.assertIsNone(page.context["lots"][0].original_initial_quantity)
        self.assertContains(page,"8 UND")
        moves = self.client.get(reverse("product-movements",args=(self.product.pk,)))
        self.assertEqual(moves.context["events"][0]["cantidad"],"No disponible")
        self.assertEqual(snapshot(),before)

    def test_four_postwrite_failures_roll_back_all_business_tables(self):
        before = snapshot()
        for target, method in ((InitialInventoryLoad,"save"),(Lot.objects,"bulk_create"),
                               (InitialLoadLine.objects,"bulk_create"),(Product,"save")):
            with self.subTest(target=str(target)):
                original = getattr(target,method)
                writes = []
                def fail_after_write(*args,**kwargs):
                    original(*args,**kwargs)
                    writes.append(snapshot()!=before)
                    raise RuntimeError("Fallo postwrite14H")
                with patch.object(target,method,autospec=True,side_effect=fail_after_write):
                    with self.assertRaisesMessage(RuntimeError,"postwrite14H"):
                        self.confirm()
                self.assertEqual(writes,[True])
                self.assertEqual(snapshot(),before)
        self.assertEqual(self.confirm().lines.count(),2)

    def test_denied_invalid_and_stale_state_leave_no_partial_history(self):
        before = snapshot()
        for actor in (self.admin,self.seller):
            with self.assertRaises(PermissionDenied):
                confirm_initial_load(actor=actor,product=self.product,lots=[LotInput("A",1,Decimal("3"),self.future)])
            self.client.force_login(actor)
            self.assertEqual(self.client.post(reverse("inventory-load"),{}).status_code,403)
            self.assertEqual(snapshot(),before)
        with self.assertRaises(ValidationError):
            confirm_initial_load(actor=self.worker,product=self.product,lots=[LotInput("A",1,Decimal("3"),timezone.localdate())])
        self.assertEqual(snapshot(),before)
        Supplier.objects.filter(pk=self.supplier.pk).update(is_active=False)
        before = snapshot()
        with self.assertRaises(ValidationError):
            self.confirm()
        self.assertEqual(snapshot(),before)
        load = self.confirm(supplier=False)
        before = snapshot()
        with self.assertRaises(ValidationError):
            self.confirm(supplier=False)
        self.assertEqual(snapshot(),before)
        self.assertEqual(load.lines.count(),2)

    def test_read_permissions_alias_cache_and_get_nonmutation(self):
        load = self.confirm()
        before = snapshot()
        for actor in (self.admin,self.worker,self.seller):
            self.client.force_login(actor)
            for name in ("inventory-load-created","inventory-load-created-alias"):
                url=reverse(name,args=(load.pk,))
                page=self.client.get(url)
                self.assertEqual(page.status_code,403 if actor==self.seller else 200)
                self.assertEqual(self.client.post(url,{}).status_code,403 if actor==self.seller else 405)
                if actor!=self.seller:
                    self.assertIn("no-store",page.headers["Cache-Control"])
                self.assertEqual(snapshot(),before)
        self.client.logout()
        self.assertEqual(self.client.get(reverse("inventory-load-created",args=(load.pk,))).status_code,302)


class InitialHistoryMigrationTests(TransactionTestCase):
    def test_nullable_migration_preserves_old_rows_and_lot_instant_guard(self):
        executor=MigrationExecutor(connection)
        latest=executor.loader.graph.leaf_nodes()
        target=("inventory","0008_stock_receipts")
        try:
            executor.migrate([target])
            apps=executor.loader.project_state([t for t in latest if t[0]!="inventory"]+[target]).apps
            role=apps.get_model("identity","Role").objects.create(code="ALMACENERO",name="Almacenero")
            actor=apps.get_model("identity","Account").objects.create(email="legacy14h@invalid.test",password="!",role=role,display_name="Legado")
            cat=apps.get_model("catalog","Category").objects.create(name="Legado",name_normalized="LEGADO")
            product=apps.get_model("catalog","Product").objects.create(category=cat,name="Legado",search_name="legado",barcode="LEGACY",barcode_normalized="LEGACY",sale_price=Decimal("10"))
            header=apps.get_model("inventory","InitialInventoryLoad").objects.create(product=product,responsible=actor)
            apps.get_model("inventory","Lot").objects.create(product=product,initial_load=header,number="A",number_normalized="A",initial_quantity=10,available_quantity=8,unit_cost=Decimal("3"),expiration_date=timezone.localdate()+timedelta(days=30))
            old=snapshot()
            MigrationExecutor(connection).migrate(latest)
            after=snapshot()
            for table,rows in old.items():
                self.assertEqual([row[:len(rows[0])] for row in after[table]] if rows else after[table],rows)
            self.assertEqual(InitialLoadLine.objects.count(),0)
            current=InitialInventoryLoad.objects.get(pk=header.pk)
            self.assertIsNone(current.product_snapshot_name)
            self.assertIsNone(current.average_cost_snapshot)
            with self.assertRaises(IntegrityError), transaction.atomic():
                Lot.objects.update(received_at=timezone.now()+timedelta(days=1))
        finally:
            MigrationExecutor(connection).migrate(latest)
