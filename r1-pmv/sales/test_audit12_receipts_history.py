from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from app_platform.history import INVALID_PAGE_MESSAGE

from cash.models import CashRegister, CashShift, CashShiftClose
from cash.services import close_cash_shift, open_cash_shift
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.services import LotInput, confirm_initial_load
from sales.models import Sale, SaleCounter, SaleDraft, SaleLine
from sales.services import add_product_to_draft, checkout_sale, discard_active_draft


class Stage12ReceiptsAndHistoriesTests(TestCase):
    password = "Test-only-Passw0rd!12"

    @classmethod
    def setUpTestData(cls) -> None:
        admin_role, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
        seller_role, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})
        wh_role, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})

        cls.admin = Account.objects.create_user(
            "admin12@test.invalid", cls.password, display_name="Admin Stage12", role=admin_role
        )
        cls.seller1 = Account.objects.create_user(
            "seller12_1@test.invalid", cls.password, display_name="Vendedora Uno 12", role=seller_role
        )
        cls.seller2 = Account.objects.create_user(
            "seller12_2@test.invalid", cls.password, display_name="Vendedor Dos 12", role=seller_role
        )
        cls.warehouse = Account.objects.create_user(
            "wh12@test.invalid", cls.password, display_name="Almacenero 12", role=wh_role
        )
        cls.register = CashRegister.objects.create(code="CAJA-01")

        cls.category = Category.objects.create(name="Abarrotes Stage12 Test", is_active=True)
        cls.p1 = Product.objects.create(
            category=cls.category,
            name="Leche Stage12 400g",
            barcode="775120010001",
            sale_price=Decimal("3.55"),
            minimum_stock=2,
        )
        confirm_initial_load(
            actor=cls.warehouse,
            product=cls.p1,
            lots=[
                LotInput(
                    "L12-P1",
                    40,
                    Decimal("2.1234"),
                    timezone.localdate() + timedelta(days=45),
                )
            ],
        )
        cls.p2 = Product.objects.create(
            category=cls.category,
            name="Arroz Stage12 1kg",
            barcode="775120010002",
            sale_price=Decimal("10.00"),
            minimum_stock=2,
        )
        confirm_initial_load(
            actor=cls.warehouse,
            product=cls.p2,
            lots=[
                LotInput(
                    "L12-P2",
                    30,
                    Decimal("6.5000"),
                    timezone.localdate() + timedelta(days=60),
                )
            ],
        )

    def _load_historical_discount(self, sale, discount):
        # Materialize pre-policy monetary snapshots in this isolated test fixture.
        original_total = sale.total_amount
        sale.discount_amount = Decimal(discount)
        sale.total_amount = original_total - sale.discount_amount
        sale.base_amount = (sale.total_amount / Decimal("1.18")).quantize(Decimal("0.01"), ROUND_HALF_UP)
        sale.igv_amount = sale.total_amount - sale.base_amount
        sale.change_given = sale.cash_received - sale.total_amount
        sale.save(update_fields=("discount_amount", "total_amount", "base_amount", "igv_amount", "change_given"))

    def _assert_no_store(self, response) -> None:
        cc = response.headers.get("Cache-Control", "")
        self.assertIn("no-store", cc)

    def test_checkout_retry_recovers_receipt_when_no_active_draft(self) -> None:
        open_cash_shift(actor=self.seller1, opening_amount=Decimal("100.00"))
        add_product_to_draft(actor=self.seller1, product_id=self.p2.pk, quantity=2)  # CP-DEC-11, total 20.

        self.client.force_login(self.seller1)
        review = self.client.get(reverse("sales-checkout"))
        self.assertEqual(review.status_code, 200)
        initial = review.context["form"].initial
        payload = {
            "cash_received": "20.00",
            "idempotency_key": str(initial["idempotency_key"]),
            "expected_subtotal": str(initial["expected_subtotal"]),
            "draft_signature": initial["draft_signature"],
        }

        first = self.client.post(reverse("sales-checkout"), payload)
        sale = Sale.objects.get(seller=self.seller1)
        self.assertRedirects(first, reverse("sales-receipt", args=(sale.pk,)))
        self.assertEqual(Sale.objects.count(), 1)
        self.assertEqual(SaleCounter.objects.get(pk=1).next_value, 2)
        self.p1.lots.get().refresh_from_db()
        self.assertEqual(self.p1.lots.get().available_quantity, 40)

        self._load_historical_discount(sale, "2.00")
        payload["discount_amount"] = "2.00"
        original = list(Sale.objects.values())
        recovered = checkout_sale(actor=self.seller1, draft_id=sale.draft_id, cash_received=sale.cash_received,
                                  discount_amount=sale.discount_amount, idempotency_key=sale.idempotency_key)
        self.assertEqual(recovered.pk, sale.pk)
        # Retry original historical POST after draft is gone -> must recover same receipt (not redirect to sales-draft!)
        retry = self.client.post(reverse("sales-checkout"), payload, follow=True)
        self.assertRedirects(retry, reverse("sales-receipt", args=(sale.pk,)))
        self.assertEqual(list(Sale.objects.values()), original)
        self.assertContains(retry, sale.correlative)
        self.assertContains(retry, "ya había sido confirmado")
        self.assertEqual(Sale.objects.count(), 1)
        self.assertEqual(SaleCounter.objects.get(pk=1).next_value, 2)
        lot1 = self.p1.lots.get()
        lot2 = self.p2.lots.get()
        self.assertEqual(lot1.available_quantity, 40)
        self.assertEqual(lot2.available_quantity, 28)
        self.assertEqual(sale.total_amount, Decimal("18.00"))
        self.assertEqual(sale.base_amount, Decimal("15.25"))
        self.assertEqual(sale.igv_amount, Decimal("2.75"))
        close_cash_shift(actor=self.seller1, counted_amount=Decimal("118.00"))
        after_close = list(CashShiftClose.objects.values())
        closed_retry = self.client.post(reverse("sales-checkout"), payload)
        self.assertRedirects(closed_retry, reverse("sales-receipt", args=(sale.pk,)))
        self.assertEqual(list(Sale.objects.values()), original)
        self.assertEqual(list(CashShiftClose.objects.values()), after_close)

    def test_checkout_retry_recovers_receipt_even_with_new_active_draft_without_touching_it(self) -> None:
        open_cash_shift(actor=self.seller1, opening_amount=Decimal("50.00"))
        add_product_to_draft(actor=self.seller1, product_id=self.p2.pk, quantity=1)

        self.client.force_login(self.seller1)
        initial = self.client.get(reverse("sales-checkout")).context["form"].initial
        payload_1 = {
            "cash_received": "10.00",
            "discount_amount": "",
            "idempotency_key": str(initial["idempotency_key"]),
            "expected_subtotal": str(initial["expected_subtotal"]),
            "draft_signature": initial["draft_signature"],
        }
        r1 = self.client.post(reverse("sales-checkout"), payload_1)
        sale1 = Sale.objects.get()
        self.assertRedirects(r1, reverse("sales-receipt", args=(sale1.pk,)))

        # Mutate live catalog name AFTER sale1 to prove signature prefix match still recovers safely
        self.p2.name = "Arroz Nombre Renombrado Post Venta"
        self.p2.save(update_fields=["name"])

        # Seller starts a fresh draft_2
        draft2 = add_product_to_draft(actor=self.seller1, product_id=self.p1.pk, quantity=3)

        # Delayed retry for draft_1 arrives while draft_2 is active
        retry = self.client.post(reverse("sales-checkout"), payload_1)
        self.assertRedirects(retry, reverse("sales-receipt", args=(sale1.pk,)))
        self.assertEqual(Sale.objects.count(), 1)
        draft2.refresh_from_db()
        self.assertEqual(draft2.status, SaleDraft.Status.ACTIVE)
        self.assertEqual(draft2.lines.count(), 1)

    def test_checkout_retry_tampered_amounts_rejected_and_new_draft_same_key_rejected(self) -> None:
        open_cash_shift(actor=self.seller1, opening_amount=Decimal("50.00"))
        add_product_to_draft(actor=self.seller1, product_id=self.p2.pk, quantity=1)

        self.client.force_login(self.seller1)
        initial1 = self.client.get(reverse("sales-checkout")).context["form"].initial
        payload1 = {
            "cash_received": "10.00",
            "discount_amount": "0.00",
            "idempotency_key": str(initial1["idempotency_key"]),
            "expected_subtotal": str(initial1["expected_subtotal"]),
            "draft_signature": initial1["draft_signature"],
        }
        self.client.post(reverse("sales-checkout"), payload1)
        self.assertEqual(Sale.objects.count(), 1)

        # Tampered cash with no draft -> redirects to draft with error
        tampered = dict(payload1, cash_received="50.00")
        r_tampered = self.client.post(reverse("sales-checkout"), tampered, follow=True)
        self.assertRedirects(r_tampered, reverse("sales-draft"))
        self.assertContains(r_tampered, "otros montos")
        self.assertEqual(Sale.objects.count(), 1)

        # Open draft_2 -> reuse draft_1 key with draft_2 signature -> must reject via service
        add_product_to_draft(actor=self.seller1, product_id=self.p2.pk, quantity=1)
        initial2 = self.client.get(reverse("sales-checkout")).context["form"].initial
        r_cross = self.client.post(
            reverse("sales-checkout"),
            {
                "cash_received": "10.00",
                "discount_amount": "",
                "idempotency_key": str(initial1["idempotency_key"]),
                "expected_subtotal": str(initial2["expected_subtotal"]),
                "draft_signature": initial2["draft_signature"],
            },
        )
        self.assertEqual(r_cross.status_code, 200)
        self.assertContains(r_cross, "ya corresponde a otra venta")
        self.assertEqual(Sale.objects.count(), 1)

        # Another seller cannot use seller1's idempotency_key or draft signature to recover seller1's receipt
        discard_active_draft(actor=self.seller1)
        close_cash_shift(actor=self.seller1, counted_amount=Decimal("60.00"))
        open_cash_shift(actor=self.seller2, opening_amount=Decimal("40.00"))
        add_product_to_draft(actor=self.seller2, product_id=self.p2.pk, quantity=1)
        self.client.force_login(self.seller2)
        r_foreign_retry = self.client.post(reverse("sales-checkout"), payload1)
        self.assertEqual(r_foreign_retry.status_code, 200)
        self.assertNotContains(r_foreign_retry, "Vendedora Uno 12")
        self.assertEqual(Sale.objects.count(), 1)

    def test_receipt_legal_notice_subtotal_payment_print_and_snapshot_isolation(self) -> None:
        shift = open_cash_shift(actor=self.seller1, opening_amount=Decimal("80.00"))
        add_product_to_draft(actor=self.seller1, product_id=self.p1.pk, quantity=2)  # 7.10
        add_product_to_draft(actor=self.seller1, product_id=self.p2.pk, quantity=1)  # 10.00 -> 17.10
        self.client.force_login(self.seller1)
        initial = self.client.get(reverse("sales-checkout")).context["form"].initial
        self.client.post(
            reverse("sales-checkout"),
            {
                "cash_received": "20.00",
                "idempotency_key": str(initial["idempotency_key"]),
                "expected_subtotal": str(initial["expected_subtotal"]),
                "draft_signature": initial["draft_signature"],
            },
        )
        sale = Sale.objects.get()
        self._load_historical_discount(sale, "2.10")
        self.assertRegex(sale.correlative, r"^V-\d{8}$")
        self.assertEqual(sale.total_amount, Decimal("15.00"))
        self.assertEqual(sale.discount_amount, Decimal("2.10"))

        # Mutate product metadata & average cost after sale
        self.p1.name = "PRODUCTO_MUTADO_NO_DEBE_VERSE"
        self.p1.barcode = "999999999999"
        self.p1.sale_price = Decimal("99.00")
        self.p1.average_cost = Decimal("55.5555")
        self.p1.save()

        # Shortcut on /ventas/
        draft_resp = self.client.get(reverse("sales-draft"))
        self.assertEqual(draft_resp.status_code, 200)
        self._assert_no_store(draft_resp)
        self.assertContains(draft_resp, f"Última constancia ({sale.correlative})")
        self.assertContains(draft_resp, reverse("sales-receipt", args=(sale.pk,)))

        # Receipt UI assertions
        rec = self.client.get(reverse("sales-receipt", args=(sale.pk,)))
        self.assertEqual(rec.status_code, 200)
        self._assert_no_store(rec)
        self.assertContains(rec, "CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO")
        self.assertContains(rec, "constancia interna")
        self.assertContains(rec, "validez tributaria")
        self.assertContains(rec, "comprobante de pago autorizado por SUNAT")
        self.assertContains(rec, "canal autorizado habitual")
        self.assertContains(rec, "Medio de pago")
        self.assertContains(rec, "Efectivo")
        self.assertContains(rec, "Subtotal")
        self.assertContains(rec, "17,10")
        self.assertContains(rec, "Descuento")
        self.assertContains(rec, "2,10")
        self.assertContains(rec, "15,00")
        self.assertContains(rec, "20,00")
        self.assertContains(rec, "5,00")
        self.assertContains(rec, "Leche Stage12 400g")
        self.assertContains(rec, "CAJA-01")
        self.assertContains(rec, reverse("sales-shift-history"))
        self.assertContains(rec, "@media print")
        # Never expose historical unit_cost or mutated product data
        self.assertNotContains(rec, "PRODUCTO_MUTADO_NO_DEBE_VERSE")
        self.assertNotContains(rec, "999999999999")
        self.assertNotContains(rec, "2,1234")
        self.assertNotContains(rec, "2.1234")
        self.assertNotContains(rec, "55,5555")
        self.assertNotContains(rec, "6,5000")

        # Close shift -> Admin sees 200 without Nueva venta/Ventas del turno; Seller2 404; WH 403; Anon 302
        close_cash_shift(actor=self.seller1, counted_amount=Decimal("95.00"))
        self.client.force_login(self.seller1)
        rec_after_close = self.client.get(reverse("sales-receipt", args=(sale.pk,)))
        self.assertEqual(rec_after_close.status_code, 200)
        self.assertNotContains(rec_after_close, "Ventas del turno</a>")

        self.client.force_login(self.admin)
        rec_admin = self.client.get(reverse("sales-receipt", args=(sale.pk,)))
        self.assertEqual(rec_admin.status_code, 200)
        self._assert_no_store(rec_admin)
        self.assertNotContains(rec_admin, "Nueva venta")
        self.assertContains(rec_admin, reverse("sales-history"))

        self.client.force_login(self.seller2)
        self.assertEqual(self.client.get(reverse("sales-receipt", args=(sale.pk,))).status_code, 404)
        self.assertEqual(self.client.get(reverse("sales-receipt", args=(uuid.uuid4(),))).status_code, 404)
        self.assertEqual(self.client.get("/ventas/constancia/no-es-uuid/").status_code, 404)

        self.client.force_login(self.warehouse)
        self.assertEqual(self.client.get(reverse("sales-receipt", args=(sale.pk,))).status_code, 403)
        self.assertEqual(self.client.post(reverse("sales-receipt", args=(sale.pk,))).status_code, 403)

        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(reverse("sales-receipt", args=(sale.pk,))).status_code, 405)

        self.client.logout()
        anon = self.client.get(reverse("sales-receipt", args=(sale.pk,)))
        self.assertEqual(anon.status_code, 302)
        self.assertIn(reverse("login"), anon.url)

    def test_histories_filters_nul_lima_dates_isolation_and_query_counts(self) -> None:
        s1_closed = open_cash_shift(actor=self.seller1, opening_amount=Decimal("100.00"))
        d1 = add_product_to_draft(actor=self.seller1, product_id=self.p2.pk, quantity=2)  # 20.00
        sale1 = checkout_sale(
            actor=self.seller1, draft_id=d1.pk, cash_received=Decimal("20.00"), idempotency_key=uuid.uuid4()
        )
        close_cash_shift(actor=self.seller1, counted_amount=Decimal("120.00"))

        s2_closed = open_cash_shift(actor=self.seller2, opening_amount=Decimal("50.00"))
        d2 = add_product_to_draft(actor=self.seller2, product_id=self.p2.pk, quantity=3)  # 30.00
        sale2 = checkout_sale(
            actor=self.seller2,
            draft_id=d2.pk,
            cash_received=Decimal("30.00"),
            idempotency_key=uuid.uuid4(),
        )
        self._load_historical_discount(sale2, "5.00")
        close_cash_shift(actor=self.seller2, counted_amount=Decimal("73.00"))

        s1_open = open_cash_shift(actor=self.seller1, opening_amount=Decimal("40.00"))
        d3 = add_product_to_draft(actor=self.seller1, product_id=self.p1.pk, quantity=2)  # 7.10
        sale3 = checkout_sale(
            actor=self.seller1, draft_id=d3.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4()
        )

        # Pin Lima timestamps: sale1 on 2026-11-10 23:59 Lima, sale2 & sale3 on 2026-11-11 00:00+ Lima
        lima = ZoneInfo("America/Lima")
        Sale.objects.filter(pk=sale1.pk).update(confirmed_at=datetime(2026, 11, 10, 23, 59, 59, tzinfo=lima))
        Sale.objects.filter(pk=sale2.pk).update(confirmed_at=datetime(2026, 11, 11, 0, 0, 0, tzinfo=lima))
        Sale.objects.filter(pk=sale3.pk).update(confirmed_at=datetime(2026, 11, 11, 14, 15, 0, tzinfo=lima))
        CashShift.objects.filter(pk=s1_closed.pk).update(opened_at=datetime(2026, 11, 10, 23, 50, 0, tzinfo=lima))
        CashShift.objects.filter(pk=s2_closed.pk).update(opened_at=datetime(2026, 11, 11, 0, 10, 0, tzinfo=lima))

        # Cash closed acta checks Total cobrado + role isolation
        self.client.force_login(self.seller1)
        acta1 = self.client.get(reverse("cash-shift-closed", args=(s1_closed.pk,)))
        self.assertEqual(acta1.status_code, 200)
        self._assert_no_store(acta1)
        self.assertContains(acta1, "Total cobrado")
        self.assertContains(acta1, "20,00")
        self.assertEqual(self.client.get(reverse("cash-shift-closed", args=(s2_closed.pk,))).status_code, 404)

        # Seller shift history only sees s1_open (sale3)
        sh_resp = self.client.get(reverse("sales-shift-history"))
        self.assertEqual(sh_resp.status_code, 200)
        self._assert_no_store(sh_resp)
        self.assertContains(sh_resp, sale3.correlative)
        self.assertNotContains(sh_resp, sale1.correlative)
        self.assertNotContains(sh_resp, sale2.correlative)
        self.assertContains(sh_resp, "Efectivo")

        # Seller sales history ignores ?vendedor and isolates ?turno
        s1_hist = self.client.get(reverse("sales-history"))
        self.assertEqual(s1_hist.status_code, 200)
        self._assert_no_store(s1_hist)
        self.assertNotContains(s1_hist, 'name="vendedor"')
        self.assertContains(s1_hist, sale3.correlative)
        self.assertContains(s1_hist, sale1.correlative)
        self.assertNotContains(s1_hist, sale2.correlative)
        self.assertNotContains(s1_hist, self.seller2.display_name)

        s1_bypass_vendedor = self.client.get(reverse("sales-history"), {"vendedor": str(self.seller2.pk)})
        self.assertNotContains(s1_bypass_vendedor, sale2.correlative)

        s1_foreign_turno = self.client.get(reverse("sales-history"), {"turno": str(s2_closed.pk)})
        self.assertEqual(s1_foreign_turno.context["total_vendido"], Decimal("0.00"))
        self.assertNotContains(s1_foreign_turno, sale2.correlative)

        # Cash shift history for Seller1: only own shifts, Total cobrado shown
        ch_seller = self.client.get(reverse("cash-shift-history"))
        self.assertEqual(ch_seller.status_code, 200)
        self._assert_no_store(ch_seller)
        self.assertNotContains(ch_seller, 'name="vendedor"')
        self.assertNotContains(ch_seller, self.seller2.display_name)
        self.assertContains(ch_seller, "20,00")

        # Admin filters + Lima date bounds + NUL guard + 4 queries on unfiltered cash history
        self.client.force_login(self.admin)
        r_date_10 = self.client.get(reverse("sales-history"), {"fecha": "2026-11-10"})
        self.assertEqual([s.pk for s in r_date_10.context["sales"]], [sale1.pk])

        r_date_11 = self.client.get(
            reverse("sales-history"), {"fecha_desde": "2026-11-11", "fecha_hasta": "2026-11-11"}
        )
        self.assertEqual([s.pk for s in r_date_11.context["sales"]], [sale3.pk, sale2.pk])
        self.assertEqual(r_date_11.context["total_vendido"], Decimal("32.10"))
        self.assertEqual(r_date_11.context["total_descuentos"], Decimal("5.00"))

        r_seller2 = self.client.get(reverse("sales-history"), {"vendedor": str(self.seller2.pk)})
        self.assertEqual([s.pk for s in r_seller2.context["sales"]], [sale2.pk])

        r_inverted = self.client.get(
            reverse("sales-history"), {"fecha_desde": "2026-11-12", "fecha_hasta": "2026-11-10"}
        )
        self.assertEqual(r_inverted.status_code, 200)
        self.assertContains(r_inverted, "no puede ser posterior")
        self.assertEqual(list(r_inverted.context["sales"]), [])

        # NUL bytes never 500
        for params in (
            {"correlativo": "V-\x00"},
            {"fecha": "\x00"},
            {"fecha_desde": "2026-11-10\x00"},
            {"vendedor": "\x00"},
            {"turno": "\x00"},
        ):
            r_nul = self.client.get(reverse("sales-history"), params)
            self.assertEqual(r_nul.status_code, 200)
            self.assertContains(r_nul, "caracteres no válidos")

        # Cash history unfiltered keeps exact 4 queries + Total cobrado + Admin filters work
        with self.assertNumQueries(4):
            r_ch_admin = self.client.get(reverse("cash-shift-history"))
        self.assertEqual(r_ch_admin.status_code, 200)
        self.assertContains(r_ch_admin, "Total cobrado")
        self.assertContains(r_ch_admin, "25,00")

        r_ch_range = self.client.get(
            reverse("cash-shift-history"),
            {"fecha_desde": "2026-11-11", "fecha_hasta": "2026-11-11", "vendedor": str(self.seller2.pk)},
        )
        self.assertEqual(r_ch_range.status_code, 200)
        self.assertEqual([s.pk for s in r_ch_range.context["shifts"]], [s2_closed.pk])
        self.assertContains(r_ch_range, "25,00")

        r_ch_nul = self.client.get(reverse("cash-shift-history"), {"fecha_desde": "2026-\x00"})
        self.assertEqual(r_ch_nul.status_code, 200)
        self.assertContains(r_ch_nul, "caracteres no válidos")

        # Query count invariance for sales_history when adding +10 sales
        with self.assertNumQueries(7):
            # session, account, role, totals agg, sellers, shifts, sales list -> fixed count across +10 sales
            self.client.get(reverse("sales-history"))
        before_qs = len(self.client.get(reverse("sales-history")).context["sales"])
        self.assertGreater(before_qs, 0)
        for i in range(10):
            d_extra = add_product_to_draft(actor=self.seller1, product_id=self.p1.pk, quantity=1)
            checkout_sale(
                actor=self.seller1, draft_id=d_extra.pk, cash_received=Decimal("5.00"), idempotency_key=uuid.uuid4()
            )
        with self.assertNumQueries(7):
            r_more = self.client.get(reverse("sales-history"))
        self.assertEqual(len(r_more.context["sales"]), before_qs + 10)

        # Denied warehouse & POST 405 checks
        self.client.force_login(self.warehouse)
        self.assertEqual(self.client.get(reverse("sales-history")).status_code, 403)
        self.assertEqual(self.client.get(reverse("sales-shift-history")).status_code, 403)
        self.assertEqual(self.client.get(reverse("cash-shift-history")).status_code, 403)
        self.assertEqual(self.client.get(reverse("cash-shift-closed", args=(s1_closed.pk,))).status_code, 403)

        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(reverse("sales-history")).status_code, 405)
        self.assertEqual(self.client.post(reverse("cash-shift-history")).status_code, 405)

    def test_tied_timestamps_and_26_item_pagination_disjoint_complete_and_safe(self) -> None:
        lima = ZoneInfo("America/Lima")
        tied_dt = datetime(2026, 11, 12, 10, 0, 0, tzinfo=lima)

        # Create 26 closed shifts with identical opened_at and closed_at timestamps -> tie-broken by -id
        shifts = []
        shift_pks = []
        for idx in range(26):
            sh = CashShift.objects.create(
                cash_register=self.register,
                seller=self.seller1 if idx % 2 == 0 else self.seller2,
                opening_amount=Decimal("10.00"),
                status=CashShift.Status.CLOSED,
            )
            CashShiftClose.objects.create(
                cash_shift=sh,
                closed_by=sh.seller,
                counted_amount=Decimal("20.00"),
                expected_amount=Decimal("20.00"),
                difference=Decimal("0.00"),
            )
            shifts.append(sh)
            shift_pks.append(sh.pk)
        CashShift.objects.filter(pk__in=shift_pks).update(opened_at=tied_dt)
        CashShiftClose.objects.filter(cash_shift_id__in=shift_pks).update(closed_at=tied_dt)

        expected_shift_order = sorted(shift_pks, reverse=True)
        self.assertEqual(list(CashShift.objects.filter(pk__in=shift_pks).values_list("pk", flat=True)), expected_shift_order)
        expected_close_order = sorted(
            CashShiftClose.objects.filter(cash_shift_id__in=shift_pks).values_list("pk", flat=True),
            reverse=True,
        )
        self.assertEqual(
            list(CashShiftClose.objects.filter(cash_shift_id__in=shift_pks).values_list("pk", flat=True)),
            expected_close_order,
        )
        d_tie_1 = SaleDraft.objects.create(cash_shift=shifts[0], seller=self.seller1, status=SaleDraft.Status.DISCARDED)
        d_tie_2 = SaleDraft.objects.create(cash_shift=shifts[1], seller=self.seller1, status=SaleDraft.Status.DISCARDED)
        SaleDraft.objects.filter(pk__in=[d_tie_1.pk, d_tie_2.pk]).update(created_at=tied_dt)
        self.assertEqual(
            list(SaleDraft.objects.filter(pk__in=[d_tie_1.pk, d_tie_2.pk]).values_list("pk", flat=True)),
            sorted([d_tie_1.pk, d_tie_2.pk], reverse=True),
        )

        # Create 26 confirmed sales with identical confirmed_at timestamps -> tie-broken by -correlative, -id
        sale_pks = []
        base_correlative = 120000
        for idx in range(26):
            owner_shift = shifts[idx]
            s = Sale.objects.create(
                cash_shift=owner_shift,
                seller=owner_shift.seller,
                correlative=f"V-{base_correlative + idx:08d}",
                idempotency_key=uuid.uuid4(),
                total_amount=Decimal("10.00"),
                base_amount=Decimal("8.47"),
                igv_amount=Decimal("1.53"),
                discount_amount=Decimal("0.00"),
                cash_received=Decimal("10.00"),
                change_given=Decimal("0.00"),
            )
            sale_pks.append(s.pk)
        Sale.objects.filter(pk__in=sale_pks).update(confirmed_at=tied_dt)

        expected_sale_order = list(
            Sale.objects.filter(pk__in=sale_pks).order_by("-confirmed_at", "-correlative", "-id").values_list("pk", flat=True)
        )
        self.assertEqual(list(Sale.objects.filter(pk__in=sale_pks).values_list("pk", flat=True)), expected_sale_order)

        self.assertEqual(CashShift._meta.ordering, ["-opened_at", "-id"])
        self.assertEqual(CashShiftClose._meta.ordering, ["-closed_at", "-id"])
        self.assertEqual(SaleDraft._meta.ordering, ["-created_at", "-id"])
        self.assertEqual(Sale._meta.ordering, ["-confirmed_at", "-correlative", "-id"])

        # Seller1 & Admin cash-shift-history pagination across 2 pages (25 per page)
        self.client.force_login(self.seller1)
        sh_s1 = self.client.get(reverse("cash-shift-history"), {"fecha_desde": "2026-11-12", "fecha_hasta": "2026-11-12"})
        self.assertEqual(sh_s1.status_code, 200)
        s1_shift_ids = [s.pk for s in sh_s1.context["shifts"]]
        self.assertEqual(s1_shift_ids, sorted([shifts[i].pk for i in range(0, 26, 2)], reverse=True))
        self.assertNotContains(sh_s1, self.seller2.display_name)

        self.client.force_login(self.admin)
        sh_p1 = self.client.get(reverse("cash-shift-history"), {"fecha_desde": "2026-11-12", "fecha_hasta": "2026-11-12"})
        sh_p2 = self.client.get(
            reverse("cash-shift-history"), {"fecha_desde": "2026-11-12", "fecha_hasta": "2026-11-12", "page": "2"}
        )
        self.assertEqual(sh_p1.status_code, 200)
        self.assertEqual(sh_p2.status_code, 200)
        p1_shift_ids = [s.pk for s in sh_p1.context["shifts"]]
        p2_shift_ids = [s.pk for s in sh_p2.context["shifts"]]
        self.assertEqual(len(p1_shift_ids), 25)
        self.assertEqual(len(p2_shift_ids), 1)
        self.assertEqual(set(p1_shift_ids).intersection(p2_shift_ids), set())
        self.assertEqual(p1_shift_ids + p2_shift_ids, expected_shift_order)
        self.assertContains(sh_p2, "fecha_desde=2026-11-12")
        self.assertContains(sh_p2, "fecha_hasta=2026-11-12")

        # Sales-history pagination across 2 pages + full filtered totals > page sum (26 * 10 = 260 > 250)
        sa_p1 = self.client.get(reverse("sales-history"), {"fecha": "2026-11-12"})
        sa_p2 = self.client.get(reverse("sales-history"), {"fecha": "2026-11-12", "page": "2"})
        self.assertEqual(sa_p1.status_code, 200)
        self.assertEqual(sa_p2.status_code, 200)
        p1_sale_ids = [s.pk for s in sa_p1.context["sales"]]
        p2_sale_ids = [s.pk for s in sa_p2.context["sales"]]
        self.assertEqual(len(p1_sale_ids), 25)
        self.assertEqual(len(p2_sale_ids), 1)
        self.assertEqual(set(p1_sale_ids).intersection(p2_sale_ids), set())
        self.assertEqual(p1_sale_ids + p2_sale_ids, expected_sale_order)
        self.assertEqual(sa_p1.context["total_vendido"], Decimal("260.00"))
        self.assertEqual(sa_p2.context["total_vendido"], Decimal("260.00"))
        self.assertContains(sa_p2, "fecha=2026-11-12")

        # Invalid pages, duplicate parameters, malformed/inverted/9999-12-31 dates on BOTH histories
        for bad_page in ("abc", "0", "-1", "\u0661", "999", "9" * 400):
            for url_name in ("sales-history", "cash-shift-history"):
                with self.subTest(url_name=url_name, bad_page=bad_page[:12]):
                    r_bad = self.client.get(reverse(url_name), {"page": bad_page})
                    self.assertEqual(r_bad.status_code, 200)
                    self.assertContains(r_bad, INVALID_PAGE_MESSAGE)

        for url_name in ("sales-history", "cash-shift-history"):
            r_dup = self.client.get(f"{reverse(url_name)}?page=1&page=2")
            self.assertEqual(r_dup.status_code, 200)
            self.assertContains(r_dup, "No repita el parámetro page.")

        for bad_date_params in (
            {"fecha_desde": "9999-12-31"},
            {"fecha_hasta": "9999-12-31"},
            {"fecha_desde": "2026-11-15", "fecha_hasta": "2026-11-10"},
            {"fecha_desde": "2026-02-30"},
            {"fecha_hasta": "no-es-fecha"},
        ):
            r_ch_bad = self.client.get(reverse("cash-shift-history"), bad_date_params)
            self.assertEqual(r_ch_bad.status_code, 200)
            self.assertEqual(list(r_ch_bad.context["shifts"]), [])

    def test_receipt_line_order_three_items_reversed_uuids_and_legacy_fallback(self) -> None:
        p3 = Product.objects.create(
            category=self.category,
            name="Azucar Blanca Stage12 1kg",
            barcode="775120010003",
            sale_price=Decimal("4.50"),
            minimum_stock=1,
        )
        confirm_initial_load(
            actor=self.warehouse,
            product=p3,
            lots=[LotInput("L12-P3", 20, Decimal("3.1000"), timezone.localdate() + timedelta(days=30))],
        )
        shift = open_cash_shift(actor=self.seller1, opening_amount=Decimal("20.00"))
        # Normal checkout of 3 items preserves insertion order 1, 2, 3
        add_product_to_draft(actor=self.seller1, product_id=p3.pk, quantity=1)
        add_product_to_draft(actor=self.seller1, product_id=self.p1.pk, quantity=1)
        draft = add_product_to_draft(actor=self.seller1, product_id=self.p2.pk, quantity=1)
        sale_real = checkout_sale(
            actor=self.seller1,
            draft_id=draft.pk,
            cash_received=Decimal("20.00"),
            idempotency_key=uuid.uuid4(),
        )
        self.assertEqual(
            list(sale_real.lines.values_list("position", "product_snapshot_name")),
            [
                (1, "Azucar Blanca Stage12 1kg"),
                (2, "Leche Stage12 400g"),
                (3, "Arroz Stage12 1kg"),
            ],
        )

        # Synthetic Sale with reversed UUIDs: pos=1 > pos=2 > pos=3 in UUID value
        sale_rev = Sale.objects.create(
            cash_shift=shift,
            seller=self.seller1,
            correlative="V-00129901",
            idempotency_key=uuid.uuid4(),
            total_amount=Decimal("18.05"),
            base_amount=Decimal("15.30"),
            igv_amount=Decimal("2.75"),
            discount_amount=Decimal("0.00"),
            cash_received=Decimal("20.00"),
            change_given=Decimal("1.95"),
        )
        SaleLine.objects.create(
            id=uuid.UUID("ffffffff-0000-0000-0000-000000000001"),
            sale=sale_rev,
            position=1,
            product=self.p1,
            product_snapshot_name="LINEA_A_UUID_ALTO",
            product_snapshot_barcode="7750001",
            quantity=1,
            unit_price=Decimal("3.55"),
            amount=Decimal("3.55"),
            unit_cost=Decimal("2.1234"),
        )
        SaleLine.objects.create(
            id=uuid.UUID("88888888-0000-0000-0000-000000000002"),
            sale=sale_rev,
            position=2,
            product=self.p2,
            product_snapshot_name="LINEA_B_UUID_MEDIO",
            product_snapshot_barcode="7750002",
            quantity=1,
            unit_price=Decimal("10.00"),
            amount=Decimal("10.00"),
            unit_cost=Decimal("6.5000"),
        )
        SaleLine.objects.create(
            id=uuid.UUID("11111111-0000-0000-0000-000000000003"),
            sale=sale_rev,
            position=3,
            product=p3,
            product_snapshot_name="LINEA_C_UUID_BAJO",
            product_snapshot_barcode="7750003",
            quantity=1,
            unit_price=Decimal("4.50"),
            amount=Decimal("4.50"),
            unit_cost=Decimal("3.1000"),
        )
        self.client.force_login(self.seller1)
        r_rev = self.client.get(reverse("sales-receipt", args=(sale_rev.pk,)))
        self.assertEqual(r_rev.status_code, 200)
        self.assertTrue(r_rev.context["sale"].has_original_line_order)
        self.assertNotContains(r_rev, "El orden original de los productos no está disponible en este registro.")
        self.assertEqual(
            [line.product_snapshot_name for line in r_rev.context["sale"].lines.all()],
            ["LINEA_A_UUID_ALTO", "LINEA_B_UUID_MEDIO", "LINEA_C_UUID_BAJO"],
        )
        html_rev = r_rev.content.decode("utf-8")
        self.assertLess(html_rev.index("LINEA_A_UUID_ALTO"), html_rev.index("LINEA_B_UUID_MEDIO"))
        self.assertLess(html_rev.index("LINEA_B_UUID_MEDIO"), html_rev.index("LINEA_C_UUID_BAJO"))

        # Legacy sale without position values -> has_original_line_order=False and notice shown
        sale_legacy = Sale.objects.create(
            cash_shift=shift,
            seller=self.seller1,
            correlative="V-00129902",
            idempotency_key=uuid.uuid4(),
            total_amount=Decimal("13.55"),
            base_amount=Decimal("11.48"),
            igv_amount=Decimal("2.07"),
            discount_amount=Decimal("0.00"),
            cash_received=Decimal("15.00"),
            change_given=Decimal("1.45"),
        )
        SaleLine.objects.create(
            id=uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001"),
            sale=sale_legacy,
            position=None,
            product=self.p1,
            product_snapshot_name="LEGACY_UUID_A",
            product_snapshot_barcode="7750011",
            quantity=1,
            unit_price=Decimal("3.55"),
            amount=Decimal("3.55"),
        )
        SaleLine.objects.create(
            id=uuid.UUID("bbbbbbbb-0000-0000-0000-000000000002"),
            sale=sale_legacy,
            position=None,
            product=self.p2,
            product_snapshot_name="LEGACY_UUID_B",
            product_snapshot_barcode="7750012",
            quantity=1,
            unit_price=Decimal("10.00"),
            amount=Decimal("10.00"),
        )
        r_leg = self.client.get(reverse("sales-receipt", args=(sale_legacy.pk,)))
        self.assertEqual(r_leg.status_code, 200)
        self.assertFalse(r_leg.context["sale"].has_original_line_order)
        self.assertContains(r_leg, "El orden original de los productos no está disponible en este registro.")
        self.assertEqual(
            [line.product_snapshot_name for line in r_leg.context["sale"].lines.all()],
            ["LEGACY_UUID_A", "LEGACY_UUID_B"],
        )

    def test_seller_menu_closed_acta_title_last_sale_disappears_and_deactivated_cookie(self) -> None:
        shift = open_cash_shift(actor=self.seller1, opening_amount=Decimal("50.00"))
        draft = add_product_to_draft(actor=self.seller1, product_id=self.p2.pk, quantity=1)
        sale = checkout_sale(
            actor=self.seller1,
            draft_id=draft.pk,
            cash_received=Decimal("10.00"),
            idempotency_key=uuid.uuid4(),
        )
        self.client.force_login(self.seller1)
        r_draft_open = self.client.get(reverse("sales-draft"))
        self.assertContains(r_draft_open, "Mi historial de ventas")
        self.assertContains(r_draft_open, "Mi historial de turnos")
        self.assertContains(r_draft_open, f"Última constancia ({sale.correlative})")

        close_cash_shift(actor=self.seller1, counted_amount=Decimal("60.00"))

        # After shift closes, /ventas/ no longer offers active-shift "Última constancia"
        r_draft_closed = self.client.get(reverse("sales-draft"))
        self.assertEqual(r_draft_closed.status_code, 200)
        self.assertNotContains(r_draft_closed, "Última constancia")

        # Acta de cierre heading & sidebar highlighting for VENDEDOR and ADMIN
        r_acta_seller = self.client.get(reverse("cash-shift-closed", args=(shift.pk,)))
        self.assertEqual(r_acta_seller.status_code, 200)
        self.assertContains(r_acta_seller, "<h1>Acta de cierre</h1>", html=True)
        self.assertContains(r_acta_seller, "no-print")
        self.assertContains(r_acta_seller, "window.print()")
        self.assertNotContains(
            r_acta_seller,
            f'<a class="nav-item is-active" href="{reverse("cash-close")}">',
        )
        self.assertContains(
            r_acta_seller,
            f'<a class="nav-item is-active" href="{reverse("cash-shift-history")}">',
        )

        # Active cookie must immediately fail on deactivation across all Stage 12 routes
        Account.objects.filter(pk=self.seller1.pk).update(is_active=False)
        for path in (
            reverse("sales-draft"),
            reverse("sales-checkout"),
            reverse("sales-receipt", args=(sale.pk,)),
            reverse("sales-shift-history"),
            reverse("sales-history"),
            reverse("cash-shift-history"),
            reverse("cash-shift-closed", args=(shift.pk,)),
            reverse("cash-shift-opened", args=(shift.pk,)),
        ):
            r_deactivated = self.client.get(path)
            self.assertEqual(r_deactivated.status_code, 302)
            self.assertIn(reverse("login"), r_deactivated.url)

        self.client.force_login(self.admin)
        r_acta_admin = self.client.get(reverse("cash-shift-closed", args=(shift.pk,)))
        self.assertEqual(r_acta_admin.status_code, 200)
        self.assertContains(r_acta_admin, "<h1>Acta de cierre</h1>", html=True)
        self.assertContains(
            r_acta_admin,
            f'<a class="nav-item is-active" href="{reverse("cash-shift-history")}">',
        )


class Stage12MigrationOrderingTests(TransactionTestCase):
    def test_stage12_migrations_round_trip_and_no_pending_migrations(self) -> None:
        executor = MigrationExecutor(connection)
        executor.migrate(
            [
                ("cash", "0004_integration_money_limits"),
                ("sales", "0007_integration_money_limits"),
            ]
        )
        executor.loader.build_graph()
        executor.migrate(
            [
                ("cash", "0005_alter_cashshift_options_alter_cashshiftclose_options"),
                ("sales", "0008_alter_sale_options_alter_saledraft_options"),
            ]
        )
        # Restore any remaining apps to latest migrated state and verify zero drift
        call_command("migrate", interactive=False, verbosity=0)
        call_command("makemigrations", check=True, dry_run=True, verbosity=0)
