"""HU-INV-04 / DEC-08: balances from known inputs, filtering and stable pages."""
import uuid
from datetime import datetime, time, timedelta
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.db import connection
from django.db.models import Prefetch
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, InitialLoadLine, Lot, PhysicalAdjustment, Supplier
from inventory.services import LotInput, confirm_initial_load, register_stock_entry, register_physical_adjustment, write_off_stock
from cash.models import CashRegister, CashShift
from sales.models import SaleLotAllocation, SaleLine
from sales.services import add_product_to_draft, checkout_sale


def business_state():
    with connection.cursor() as cursor:
        rows = {}
        for table in sorted(connection.introspection.table_names()):
            if table.startswith(("catalog_", "inventory_", "cash_", "sales_")):
                cursor.execute('SELECT * FROM "'+table+'" ORDER BY 1')
                rows[table] = cursor.fetchall()
        return rows


class LedgerTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin, cls.worker, cls.seller = [Account.objects.create_user(email=code.lower()+"@ledger14h2.invalid",
            password=None, display_name=code+" original", role=Role.objects.create(code=code,name=code))
            for code in ("ADMIN","ALMACENERO","VENDEDOR")]
        cls.category=Category.objects.create(name="Familia14H2")
        cls.product=Product.objects.create(name="Kardex14H2",barcode="INT-14H2",category=cls.category,sale_price=Decimal("10"))
        cls.supplier=Supplier.objects.create(name="Proveedor14H2",ruc="20000000014")
        cls.future=timezone.localdate()+timedelta(days=30)
        cls.day=timezone.localdate()-timedelta(days=1)

    def setUp(self):
        self.client.force_login(self.admin)
        self.url=reverse("product-movements",args=(self.product.pk,))

    def at(self,hour):
        return patch("django.utils.timezone.now",return_value=datetime.combine(self.day,time(hour),tzinfo=ZoneInfo("America/Lima")))

    def period(self,start,end,kind=""):
        return dict(desde=self.day.isoformat()+"T"+start,hasta=self.day.isoformat()+"T"+end,tipo=kind)

    def prepare(self,cursor=False):
        with self.at(9):
            load=confirm_initial_load(actor=self.worker,product=self.product,supplier=self.supplier,
                lots=[LotInput("INICIAL",10 if cursor else 20,Decimal("3"),self.future)])
            CashShift.objects.create(cash_register=CashRegister.objects.create(code="CAJA14H2"),seller=self.seller,opening_amount=100)
        with self.at(10):
            receipt=register_stock_entry(actor=self.worker,product=self.product,supplier=self.supplier,
                lots=[LotInput("C",10,Decimal("6"),self.future+timedelta(days=30))])
        if cursor:
            with self.at(11):
                receipt=register_stock_entry(actor=self.worker,product=self.product,supplier=self.supplier,
                    lots=[LotInput("C",5,Decimal("8"),self.future+timedelta(days=30))])
        with self.at(12 if cursor else 11):
            draft=add_product_to_draft(actor=self.seller,product_id=self.product.pk,quantity=22 if cursor else 5)
            checkout_sale(actor=self.seller,draft_id=draft.pk,cash_received=Decimal("220"),idempotency_key=uuid.uuid4())
        with self.at(13 if cursor else 12):
            write_off_stock(actor=self.worker,lot=receipt.lines.get().lot if cursor else load.lines.get().lot,
                quantity=1 if cursor else 2,reason="ROBO",notes="Conteo ficticio")
        if not cursor:
            with self.at(13):
                register_physical_adjustment(actor=self.admin,lot=load.lines.get().lot,delta=1,reason="Recuento positivo")
        return load,receipt

    def test_written_case_real_balances_and_outgoing_filter(self):
        self.prepare()
        before=business_state()
        all_rows=self.client.get(self.url)
        self.assertEqual([e["balance"] for e in all_rows.context["events"]],[20,30,25,23,24])
        result=self.client.get(self.url,self.period("10:00","13:00","salidas"))
        self.assertEqual([e["delta"] for e in result.context["events"]],[-5,-2])
        self.assertEqual([e["balance"] for e in result.context["events"]],[25,23])
        self.assertEqual((result.context["opening_balance"],result.context["closing_balance"],result.context["filtered_delta"]),(20,24,-7))
        self.assertEqual(business_state(),before)

    def test_three_origins_sale22_period_open20_close2(self):
        self.prepare(cursor=True)
        result=self.client.get(self.url)
        self.assertEqual([e["balance"] for e in result.context["events"]],[10,20,25,3,2])
        sales=self.client.get(self.url,self.period("10:01","13:00","venta"))
        self.assertEqual((sales.context["opening_balance"],sales.context["closing_balance"],sales.context["filtered_delta"]),(20,2,-22))
        row=sales.context["events"][0]
        self.assertEqual(row["balance"],3)
        self.assertTrue(row["allocation_complete"])
        self.assertEqual(sorted(a.quantity for a in row["allocations"]),[2,10,10])
        self.assertContains(sales,"R-00000001");self.assertContains(sales,"R-00000002")

    def test_same_instant_pages25_preserve_period_and_full_totals(self):
        with self.at(8):
            load=confirm_initial_load(actor=self.worker,product=self.product,lots=[LotInput("PAG",50,Decimal("2"),self.future)])
        for i in range(26):
            with self.at(9):
                register_physical_adjustment(actor=self.admin,lot=load.lots.get(),delta=1,reason=f"Recuento {i}")
        query=self.period("09:00","09:00","ajuste")
        before=business_state()
        one=self.client.get(self.url,query);two=self.client.get(self.url,{**query,"page":"2"})
        ids1=[e["orden_id"] for e in one.context["events"]];ids2=[e["orden_id"] for e in two.context["events"]]
        self.assertEqual((len(ids1),len(ids2)),(25,1))
        self.assertEqual(ids1+ids2,sorted(ids1+ids2));self.assertFalse(set(ids1)&set(ids2))
        self.assertEqual([e["balance"] for e in one.context["events"]+two.context["events"]],list(range(51,77)))
        for response in (one,two):
            self.assertEqual((response.context["filtered_count"],response.context["filtered_delta"],response.context["opening_balance"],response.context["closing_balance"]),(26,26,50,76))
        self.assertIn("tipo=ajuste",one.context["next_url"]);self.assertIn("desde=",two.context["previous_url"])
        self.assertEqual(business_state(),before)

    def test_invalid_dates_types_pages_and_repeated_keys_never_mutate_or_render_results(self):
        self.prepare()
        before=business_state()
        queries=[{"desde":"2026-01-01T09:00"},{"desde":"2026-02-30T09:00","hasta":"2026-03-01T09:00"},
            self.period("13:00","09:00"),{"desde":"0000-01-01T00:00","hasta":"0001-01-01T00:00"},
            {"desde":"2026-01-01T09:00:01","hasta":"2026-01-01T10:00"},{"tipo":"otra"},
            {"page":"0"},{"page":"-1"},{"page":"1.5"},{"page":"١"},{"page":"9"*10000},{"page":"999"},
            {"tipo":["venta","merma"]},{"page":["1","2"]},{"desde":["",""]}]
        for query in queries:
            with self.subTest(query=str(query)[:100]):
                result=self.client.get(self.url,query)
                self.assertEqual(result.status_code,200)
                self.assertFalse(result.context["query_valid"])
                self.assertEqual(result.context["events"],[])
                self.assertContains(result,"No se realizó la consulta")
                self.assertNotContains(result,'data-testid="closing-balance"')
                self.assertEqual(business_state(),before)

    def test_empty_period_year_boundaries_and_minute_end(self):
        self.prepare()
        for query,opening in ((dict(desde="0001-01-01T00:00",hasta="0001-01-01T23:59"),0),
                             (dict(desde="9999-12-31T23:59",hasta="9999-12-31T23:59"),24)):
            result=self.client.get(self.url,query)
            self.assertTrue(result.context["query_valid"])
            self.assertEqual((result.context["opening_balance"],result.context["closing_balance"],result.context["filtered_delta"]),(opening,opening,0))
        adjustment=PhysicalAdjustment.objects.get()
        PhysicalAdjustment.objects.filter(pk=adjustment.pk).update(created_at=adjustment.created_at+timedelta(seconds=59,microseconds=999999))
        result=self.client.get(self.url,self.period("13:00","13:00"))
        self.assertEqual((len(result.context["events"]),result.context["opening_balance"],result.context["closing_balance"]),(1,23,24))

    def test_legacy_input_does_not_invent_opening_from_current_stock(self):
        load=InitialInventoryLoad.objects.create(product=self.product,responsible=self.worker)
        Lot.objects.create(product=self.product,initial_load=load,number="LEGADO",initial_quantity=10,available_quantity=5,
            unit_cost=Decimal("3"),expiration_date=self.future)
        result=self.client.get(self.url)
        self.assertIsNone(result.context["opening_balance"]);self.assertIsNone(result.context["closing_balance"])
        self.assertIsNone(result.context["filtered_delta"])
        self.assertContains(result,"Sin fotografía de entrada")
        self.assertIsNone(result.context["events"][0]["balance"])

    def test_incomplete_allocation_and_ambiguous_product_are_explicit(self):
        self.prepare()
        allocation=SaleLotAllocation.objects.get()
        SaleLotAllocation.objects.filter(pk=allocation.pk).update(quantity=allocation.quantity-1)
        result=self.client.get(self.url,{"tipo":"venta"})
        self.assertIsNone(result.context["closing_balance"])
        self.assertContains(result,"Asignación incompleta")
        self.assertEqual(result.context["filtered_delta"],-5)
        SaleLotAllocation.objects.filter(pk=allocation.pk).update(quantity=allocation.quantity)
        SaleLine.objects.update(product=None)
        result=self.client.get(self.url,{"tipo":"venta"})
        self.assertContains(result,"identidad del producto no confirmada")
        self.assertIsNone(result.context["filtered_delta"]);self.assertIsNone(result.context["closing_balance"])

    def test_compensating_discrepancy_between_lots_is_detected(self):
        load,receipt=self.prepare()
        Lot.objects.filter(pk=load.lines.get().lot_id).update(available_quantity=15)
        Lot.objects.filter(pk=receipt.lines.get().lot_id).update(available_quantity=9)
        self.assertEqual(self.product.physical_stock,24)
        result=self.client.get(self.url)
        self.assertEqual(result.context["filtered_delta"],24)
        self.assertIsNone(result.context["closing_balance"])
        self.assertContains(result,"Las cantidades por lote no concilian")

    def test_inconsistent_origin_link_never_passes_by_coincidental_total(self):
        load,_=self.prepare()
        other=Product.objects.create(category=self.category,name="Otro",barcode="OTRO",sale_price=Decimal("1"))
        header=InitialInventoryLoad.objects.create(product=other,responsible=self.worker)
        InitialLoadLine.objects.filter(load=load).update(load=header)
        result=self.client.get(self.url)
        self.assertIsNone(result.context["closing_balance"])
        self.assertContains(result,"relación de origen inconsistente")

    def test_negative_sequence_is_not_presented_as_trustworthy(self):
        self.prepare()
        adjustment=PhysicalAdjustment.objects.get()
        PhysicalAdjustment.objects.filter(pk=adjustment.pk).update(delta=-1,
            created_at=datetime.combine(self.day,time(8),tzinfo=ZoneInfo("America/Lima")))
        result=self.client.get(self.url)
        self.assertIsNone(result.context["closing_balance"])
        self.assertContains(result,"secuencia registrada produce una cantidad negativa")

    def test_new_lot_seen_between_reads_degrades_to_unknown_without_crashing(self):
        self.prepare()
        from inventory.ledger import build_ledger
        observed=Product.objects.prefetch_related(Prefetch("lots",queryset=Lot.objects.select_related(
            "responsible","supplier","initial_line__load","receipt_line__receipt"))).get(pk=self.product.pk)
        receipt=register_stock_entry(actor=self.worker,product=self.product,lots=[LotInput("NUEVO",3,Decimal("4"),self.future)])
        write_off_stock(actor=self.worker,lot=receipt.lines.get().lot,quantity=1,reason="ROBO",notes="Faltante ficticio")
        before=business_state()
        rows,issues=build_ledger(observed)
        self.assertIn("El inventario cambió durante la consulta. Vuelva a consultar.",issues)
        self.assertTrue(all(row["balance"] is None for row in rows))
        self.assertEqual(business_state(),before)

    def test_roles_methods_inactive_product_and_empty_product(self):
        empty=self.client.get(self.url)
        self.assertEqual((empty.context["opening_balance"],empty.context["closing_balance"],empty.context["filtered_count"]),(0,0,0))
        self.prepare()
        Product.objects.filter(pk=self.product.pk).update(is_active=False)
        before=business_state()
        for actor in (self.admin,self.worker,self.seller):
            self.client.force_login(actor)
            result=self.client.get(self.url)
            self.assertEqual(result.status_code,403 if actor==self.seller else 200)
            self.assertEqual(self.client.post(self.url,{}).status_code,403 if actor==self.seller else 405)
            if actor!=self.seller:
                self.assertEqual(result.context["closing_balance"],24)
                self.assertIn("no-store",result.headers["Cache-Control"])
            self.assertEqual(business_state(),before)
        self.client.logout()
        self.assertEqual(self.client.get(self.url).status_code,302)
