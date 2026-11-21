from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal, ROUND_HALF_UP
from unittest.mock import patch

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cash.models import CashRegister, CashShift
from cash.services import close_cash_shift
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot
from inventory.services import LotInput, confirm_initial_load, register_stock_entry
from sales.models import Sale, SaleCounter, SaleDraft, SaleDraftLine, SaleLine
from sales.services import IGV_FACTOR, MONEY, add_product_to_draft, checkout_sale, discard_active_draft


class CheckoutAndDiscountAudit11Tests(TestCase):
    password = "Test-only-Passw0rd!"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

        cls.admin = Account.objects.create_user(
            "a11-admin@test.invalid", cls.password, display_name="Admin 11", role=cls.admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "a11-wh@test.invalid", cls.password, display_name="Almacen 11", role=cls.warehouse_role
        )
        cls.seller = Account.objects.create_user(
            "a11-seller@test.invalid", cls.password, display_name="Vendedor 11", role=cls.seller_role
        )
        cls.other_seller = Account.objects.create_user(
            "a11-seller2@test.invalid", cls.password, display_name="Vendedor Dos 11", role=cls.seller_role
        )
        cls.inactive_seller = Account.objects.create_user(
            "a11-inactive@test.invalid",
            cls.password,
            display_name="Vendedor Inactivo 11",
            role=cls.seller_role,
            is_active=False,
        )

        cls.register = CashRegister.objects.create(code="CAJA-01")
        cls.cat_active = Category.objects.create(name="Abarrotes Audit 11", is_active=True)
        cls.cat_inactive = Category.objects.create(name="Suspendida Audit 11", is_active=False)

        cls.product_tax = Product.objects.create(
            category=cls.cat_active,
            name="Conserva Centavos 11",
            barcode="775119900001",
            sale_price=Decimal("3.55"),
            minimum_stock=2,
        )
        confirm_initial_load(
            actor=cls.warehouse,
            product=cls.product_tax,
            lots=[LotInput("TAX-LOT-1", 50, Decimal("1.5000"), timezone.localdate() + timedelta(days=30))],
        )

        cls.product_second = Product.objects.create(
            category=cls.cat_active,
            name="Arroz Bolsa Audit 11",
            barcode="775119900002",
            sale_price=Decimal("4.20"),
            minimum_stock=2,
        )
        confirm_initial_load(
            actor=cls.warehouse,
            product=cls.product_second,
            lots=[LotInput("SEC-LOT-1", 20, Decimal("2.1000"), timezone.localdate() + timedelta(days=30))],
        )

    def _open_shift(self, seller=None, opening=Decimal("100.00")) -> CashShift:
        return CashShift.objects.create(
            cash_register=self.register,
            seller=seller or self.seller,
            opening_amount=opening,
        )

    def _checkout_get_payload(self, *, cash_received: str, discount_amount: str = "", key=None) -> tuple:
        get_resp = self.client.get(reverse("sales-checkout"))
        self.assertEqual(get_resp.status_code, 200)
        initial = get_resp.context["form"].initial
        payload = {
            "cash_received": cash_received,
            "discount_amount": discount_amount,
            "idempotency_key": str(key or initial["idempotency_key"]),
            "expected_subtotal": str(initial["expected_subtotal"]),
            "draft_signature": initial["draft_signature"],
        }
        return get_resp, payload

    def test_new_checkout_rejects_discount_and_keeps_entire_draft(self) -> None:
        self._open_shift()
        self.client.force_login(self.seller)
        draft = add_product_to_draft(actor=self.seller, product_id=self.product_tax.pk, quantity=3)
        tables = (Sale, SaleCounter, SaleLine, SaleDraft, SaleDraftLine, Lot, CashShift)

        def snapshot():
            return [list(model.objects.order_by("pk").values()) for model in tables]

        before = snapshot()
        for invalid in ("0.01", "10.64", "10.65", "11.00", "-0.01", "abc", "0e0", ["1", "0"]):
            with self.subTest(discount=invalid):
                review, payload = self._checkout_get_payload(cash_received="20.00", discount_amount=invalid)
                self.assertNotContains(review, 'name="discount_amount"')
                response = self.client.post(reverse("sales-checkout"), payload)
                self.assertContains(response, "Los descuentos no están habilitados para nuevas ventas")
                self.assertEqual(snapshot(), before)

        with self.assertRaisesMessage(ValidationError, "Los descuentos no están habilitados para nuevas ventas"):
            checkout_sale(actor=self.seller, draft_id=draft.pk, cash_received=Decimal("15.00"),
                          discount_amount=Decimal("1.00"), idempotency_key=uuid.uuid4())
        self.assertEqual(snapshot(), before)
        _, payload = self._checkout_get_payload(cash_received="15.00", discount_amount="0.00")
        response = self.client.post(reverse("sales-checkout"), payload)
        sale = Sale.objects.get()
        self.assertRedirects(response, reverse("sales-receipt", args=(sale.pk,)))
        self.assertEqual((sale.discount_amount, sale.total_amount, sale.base_amount, sale.igv_amount, sale.change_given),
                         tuple(map(Decimal, ("0.00", "10.65", "9.03", "1.62", "4.35"))))

    def test_form_and_service_reject_non_ascii_scientific_overprecision_and_non_finite(self) -> None:
        self._open_shift()
        self.client.force_login(self.seller)
        draft = add_product_to_draft(actor=self.seller, product_id=self.product_tax.pk, quantity=2)

        # Form/HTTP layer checks (Arabic-Indic digits, scientific notation, >2 decimals, leading +)
        invalid_form_cases = [
            ("١٠.٠٠", ""),
            ("10.00", "١.٠٠"),
            ("1e2", ""),
            ("10.00", "1e0"),
            ("+10.00", ""),
            ("10.00", "+1.00"),
            ("10.005", ""),
            ("10.00", "1.005"),
            ("abc", ""),
        ]
        for cash_raw, disc_raw in invalid_form_cases:
            with self.subTest(cash_raw=cash_raw, disc_raw=disc_raw):
                _, payload = self._checkout_get_payload(cash_received=cash_raw, discount_amount=disc_raw)
                resp = self.client.post(reverse("sales-checkout"), payload)
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(Sale.objects.count(), 0)

        # Service layer checks (direct calls bypassing forms)
        bad_service_amounts = [
            Decimal("10.005"),
            Decimal("NaN"),
            Decimal("Infinity"),
            Decimal("-1.00"),
            True,
            False,
            10.5,
            "10.00",
        ]
        for bad_val in bad_service_amounts:
            with self.subTest(bad_cash=bad_val):
                with self.assertRaises(ValidationError):
                    checkout_sale(
                        actor=self.seller,
                        draft_id=draft.pk,
                        cash_received=bad_val,  # type: ignore[arg-type]
                        idempotency_key=uuid.uuid4(),
                    )
            with self.subTest(bad_disc=bad_val):
                with self.assertRaises(ValidationError):
                    checkout_sale(
                        actor=self.seller,
                        draft_id=draft.pk,
                        cash_received=Decimal("10.00"),
                        discount_amount=bad_val,  # type: ignore[arg-type]
                        idempotency_key=uuid.uuid4(),
                    )
        with self.assertRaises(ValidationError):
            checkout_sale(
                actor=self.seller,
                draft_id=draft.pk,
                cash_received=Decimal("10.00"),
                idempotency_key="not-a-uuid",  # type: ignore[arg-type]
            )
        self.assertEqual(Sale.objects.count(), 0)

    def test_round_half_up_igv_precision_across_centavo_spectrum(self) -> None:
        self._open_shift()
        today = timezone.localdate()
        # Check net totals in [0.57..0.63] and [8.40..8.50] and exact HALF_UP ties (e.g. 0.59, 10.00)
        for cent in ("0.58", "0.59", "0.60", "1.18", "3.55", "10.00"):
            with self.subTest(cent=cent):
                p = Product.objects.create(
                    category=self.cat_active,
                    name=f"P-{cent}",
                    barcode=f"7751188{cent.replace('.', '')}",
                    sale_price=Decimal(cent),
                )
                confirm_initial_load(
                    actor=self.warehouse,
                    product=p,
                    lots=[LotInput(f"L-{cent}", 2, Decimal("0.2000"), today + timedelta(days=10))],
                )
                d = add_product_to_draft(actor=self.seller, product_id=p.pk, quantity=1)
                sale = checkout_sale(
                    actor=self.seller,
                    draft_id=d.pk,
                    cash_received=Decimal(cent),
                    idempotency_key=uuid.uuid4(),
                )
                exp_base = (Decimal(cent) / IGV_FACTOR).quantize(MONEY, rounding=ROUND_HALF_UP)
                self.assertEqual(sale.base_amount, exp_base)
                self.assertEqual(sale.igv_amount, Decimal(cent) - exp_base)
                self.assertEqual(sale.base_amount + sale.igv_amount, sale.total_amount)

    def test_fefo_three_level_order_today_exclusion_and_historical_snapshots(self) -> None:
        self._open_shift()
        today = timezone.localdate()
        prod = Product.objects.create(
            category=self.cat_active,
            name="Leche FEFO Completa 11",
            barcode="775117700001",
            sale_price=Decimal("4.50"),
        )
        t1 = timezone.now() - timedelta(hours=4)
        t2 = timezone.now() - timedelta(hours=2)
        t3 = timezone.now() - timedelta(hours=1)
        with patch("django.utils.timezone.now", return_value=t1):
            confirm_initial_load(
                actor=self.warehouse,
                product=prod,
                lots=[
                    LotInput("LOT-EXP-PAST", 5, Decimal("1.0000"), today + timedelta(days=1)),
                    LotInput("LOT-EXP-TODAY", 4, Decimal("1.5000"), today + timedelta(days=1)),
                    LotInput("LOT-TIE-1", 2, Decimal("2.0000"), today + timedelta(days=5)),
                ],
            )
        Lot.objects.filter(product=prod, number_normalized="LOT-EXP-PAST").update(
            expiration_date=today - timedelta(days=1)
        )
        Lot.objects.filter(product=prod, number_normalized="LOT-EXP-TODAY").update(expiration_date=today)

        with patch("django.utils.timezone.now", return_value=t2):
            register_stock_entry(
                actor=self.warehouse,
                product=prod,
                lots=[LotInput("LOT-TIE-2", 3, Decimal("3.0000"), today + timedelta(days=5))],
            )
        with patch("django.utils.timezone.now", return_value=t3):
            register_stock_entry(
                actor=self.warehouse,
                product=prod,
                lots=[LotInput("LOT-FAR", 10, Decimal("4.0000"), today + timedelta(days=30))],
            )

        # Average cost across created lots stays tracked accurately; sell 6 units -> LOT-TIE-1 (2), LOT-TIE-2 (3), LOT-FAR (1)
        draft = add_product_to_draft(actor=self.seller, product_id=prod.pk, quantity=6)
        prod.refresh_from_db()
        expected_avg_cost = prod.average_cost
        sale = checkout_sale(
            actor=self.seller,
            draft_id=draft.pk,
            cash_received=Decimal("30.00"),
            idempotency_key=uuid.uuid4(),
        )
        self.assertEqual(sale.total_amount, Decimal("27.00"))
        self.assertEqual(sale.change_given, Decimal("3.00"))

        lots = {lot.number_normalized: lot.available_quantity for lot in Lot.objects.filter(product=prod)}
        self.assertEqual(lots["LOT-EXP-PAST"], 5)
        self.assertEqual(lots["LOT-EXP-TODAY"], 4)
        self.assertEqual(lots["LOT-TIE-1"], 0)
        self.assertEqual(lots["LOT-TIE-2"], 0)
        self.assertEqual(lots["LOT-FAR"], 9)

        line = SaleLine.objects.get(sale=sale)
        self.assertEqual(line.unit_cost, expected_avg_cost)
        self.assertEqual(line.product_snapshot_name, "Leche FEFO Completa 11")
        self.assertEqual(line.product_snapshot_barcode, "775117700001")

        # Mutate live catalog & verify receipt keeps historical snapshots
        prod.name = "Leche Nombre Editado 11"
        prod.sale_price = Decimal("9.99")
        prod.save(update_fields=["name", "sale_price"])
        self.client.force_login(self.seller)
        receipt = self.client.get(reverse("sales-receipt", args=(sale.pk,)))
        self.assertContains(receipt, "Leche FEFO Completa 11")
        self.assertNotContains(receipt, "Leche Nombre Editado 11")

    def test_idempotency_rejects_divergent_amounts_and_allows_retry_after_failed_attempt(self) -> None:
        self._open_shift()
        draft = add_product_to_draft(actor=self.seller, product_id=self.product_tax.pk, quantity=2)  # 7.10
        key = uuid.uuid4()

        # First attempt fails due to insufficient cash -> key can still be used for valid retry
        with self.assertRaises(ValidationError):
            checkout_sale(
                actor=self.seller,
                draft_id=draft.pk,
                cash_received=Decimal("5.00"),
                idempotency_key=key,
            )
        self.assertEqual(Sale.objects.count(), 0)

        sale = checkout_sale(
            actor=self.seller,
            draft_id=draft.pk,
            cash_received=Decimal("10.00"),
            discount_amount=Decimal("0.00"),
            idempotency_key=key,
        )
        # Identical replay returns exact existing sale
        same = checkout_sale(
            actor=self.seller,
            draft_id=draft.pk,
            cash_received=Decimal("10.00"),
            discount_amount=Decimal("0.00"),
            idempotency_key=key,
        )
        self.assertEqual(same.pk, sale.pk)
        self.assertEqual(Sale.objects.count(), 1)

        # Divergent replay with same key & same draft_id MUST fail (cash or discount differs)
        with self.assertRaises(ValidationError):
            checkout_sale(
                actor=self.seller,
                draft_id=draft.pk,
                cash_received=Decimal("20.00"),
                discount_amount=Decimal("0.00"),
                idempotency_key=key,
            )
        with self.assertRaises(ValidationError):
            checkout_sale(
                actor=self.seller,
                draft_id=draft.pk,
                cash_received=Decimal("10.00"),
                discount_amount=Decimal("1.00"),
                idempotency_key=key,
            )
        self.assertEqual(Sale.objects.count(), 1)

    def test_vanished_draft_on_checkout_post_redirects_cleanly_without_broken_page(self) -> None:
        self._open_shift()
        self.client.force_login(self.seller)
        add_product_to_draft(actor=self.seller, product_id=self.product_tax.pk, quantity=1)
        _, payload = self._checkout_get_payload(cash_received="5.00")

        # Simulate draft discarded in another tab between view GET/check and service execution
        def vanish(**kwargs):
            discard_active_draft(actor=self.seller)
            return checkout_sale(**kwargs)

        with patch("sales.views.checkout_sale", side_effect=vanish):
            resp = self.client.post(reverse("sales-checkout"), payload, follow=True)
        self.assertRedirects(resp, reverse("sales-draft"))
        self.assertContains(resp, "El borrador de venta no está disponible")
        self.assertEqual(Sale.objects.count(), 0)

    def test_mid_checkout_error_rolls_back_counter_sale_lines_lots_and_keeps_draft_active(self) -> None:
        self._open_shift()
        draft = add_product_to_draft(actor=self.seller, product_id=self.product_tax.pk, quantity=2)
        add_product_to_draft(actor=self.seller, product_id=self.product_second.pk, quantity=2)

        counter, _ = SaleCounter.objects.get_or_create(id=1, defaults={"next_value": 1})
        before_counter = counter.next_value
        before_lots = list(Lot.objects.order_by("pk").values_list("pk", "available_quantity"))

        # Inject error on the second Lot.save() inside checkout_sale's atomic block (CT-ROLLBACK-02)
        real_save = Lot.save
        calls = {"count": 0}

        def fail_on_second_lot(lot_self, *args, **kwargs):
            calls["count"] += 1
            if calls["count"] == 2:
                raise RuntimeError("Fallo simulado a mitad de cobro")
            return real_save(lot_self, *args, **kwargs)

        with patch.object(Lot, "save", fail_on_second_lot):
            with self.assertRaises(RuntimeError):
                checkout_sale(
                    actor=self.seller,
                    draft_id=draft.pk,
                    cash_received=Decimal("20.00"),
                    idempotency_key=uuid.uuid4(),
                )

        self.assertEqual(Sale.objects.count(), 0)
        self.assertEqual(SaleLine.objects.count(), 0)
        counter.refresh_from_db()
        self.assertEqual(counter.next_value, before_counter)
        self.assertEqual(list(Lot.objects.order_by("pk").values_list("pk", "available_quantity")), before_lots)
        draft.refresh_from_db()
        self.assertEqual(draft.status, SaleDraft.Status.ACTIVE)

    def test_intervening_category_deactivation_stock_drop_and_seller_deactivation(self) -> None:
        self._open_shift()
        draft = add_product_to_draft(actor=self.seller, product_id=self.product_tax.pk, quantity=3)

        # Deactivate category before checkout -> blocks with ValidationError
        self.cat_active.is_active = False
        self.cat_active.save(update_fields=["is_active"])
        with self.assertRaises(ValidationError):
            checkout_sale(
                actor=self.seller,
                draft_id=draft.pk,
                cash_received=Decimal("20.00"),
                idempotency_key=uuid.uuid4(),
            )
        self.cat_active.is_active = True
        self.cat_active.save(update_fields=["is_active"])

        # Reduce sellable stock below draft quantity -> blocks without touching lots
        Lot.objects.filter(number="TAX-LOT-1").update(available_quantity=2)
        with self.assertRaises(ValidationError):
            checkout_sale(
                actor=self.seller,
                draft_id=draft.pk,
                cash_received=Decimal("20.00"),
                idempotency_key=uuid.uuid4(),
            )
        self.assertEqual(Lot.objects.get(number="TAX-LOT-1").available_quantity, 2)
        Lot.objects.filter(number="TAX-LOT-1").update(available_quantity=50)

        # Deactivate seller -> raises PermissionDenied in checkout_sale AND blocks HTTP
        self.seller.is_active = False
        self.seller.save(update_fields=["is_active"])
        with self.assertRaises(PermissionDenied):
            checkout_sale(
                actor=self.seller,
                draft_id=draft.pk,
                cash_received=Decimal("20.00"),
                idempotency_key=uuid.uuid4(),
            )
        self.assertEqual(Sale.objects.count(), 0)

    def test_never_cache_headers_and_cross_role_authorization(self) -> None:
        self._open_shift()
        draft = add_product_to_draft(actor=self.seller, product_id=self.product_tax.pk, quantity=2)
        sale = checkout_sale(
            actor=self.seller,
            draft_id=draft.pk,
            cash_received=Decimal("10.00"),
            idempotency_key=uuid.uuid4(),
        )
        draft2 = add_product_to_draft(actor=self.seller, product_id=self.product_tax.pk, quantity=1)

        self.client.force_login(self.seller)
        for url in (
            reverse("sales-checkout"),
            reverse("sales-receipt", args=(sale.pk,)),
            reverse("sales-shift-history"),
            reverse("sales-history"),
        ):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200, url)
            cc = resp.headers.get("Cache-Control", "")
            for directive in ("no-cache", "no-store", "must-revalidate", "max-age=0"):
                self.assertIn(directive, cc, f"Missing {directive} on {url}: {cc}")

        # Warehouse cannot view receipt, checkout, or histories
        self.client.force_login(self.warehouse)
        for url in (
            reverse("sales-checkout"),
            reverse("sales-receipt", args=(sale.pk,)),
            reverse("sales-shift-history"),
            reverse("sales-history"),
        ):
            self.assertEqual(self.client.get(url).status_code, 403, url)

        # Other seller gets 404 on someone else's receipt
        self.client.force_login(self.other_seller)
        self.assertEqual(self.client.get(reverse("sales-receipt", args=(sale.pk,))).status_code, 404)

        # Admin gets 200 on receipt and full history, 403 on checkout and seller shift history
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("sales-receipt", args=(sale.pk,))).status_code, 200)
        self.assertEqual(self.client.get(reverse("sales-history")).status_code, 200)
        self.assertEqual(self.client.get(reverse("sales-checkout")).status_code, 403)
        self.assertEqual(self.client.get(reverse("sales-shift-history")).status_code, 403)

        # Cleanup second active draft
        discard_active_draft(actor=self.seller)
        self.assertEqual(draft2.lines.count(), 0)

    def test_cash_close_admin_dashboard_and_stock_integration_for_full_price_sales(self) -> None:
        shift = self._open_shift(opening=Decimal("100.00"))
        # First sale 2 × 3.55.
        d1 = add_product_to_draft(actor=self.seller, product_id=self.product_tax.pk, quantity=2)
        s1 = checkout_sale(
            actor=self.seller,
            draft_id=d1.pk,
            cash_received=Decimal("20.00"),
            idempotency_key=uuid.uuid4(),
        )
        # Second sale, exact cash.
        d2 = add_product_to_draft(actor=self.seller, product_id=self.product_second.pk, quantity=1)
        s2 = checkout_sale(
            actor=self.seller,
            draft_id=d2.pk,
            cash_received=Decimal("4.20"),
            idempotency_key=uuid.uuid4(),
        )
        self.assertEqual(s1.total_amount + s2.total_amount, Decimal("11.30"))

        # Opening plus both full-price sales.
        close = close_cash_shift(actor=self.seller, counted_amount=Decimal("111.30"))
        self.assertEqual(close.expected_amount, Decimal("111.30"))
        self.assertEqual(close.difference, Decimal("0.00"))

        # Admin dashboard and history reflect exact net sales & discounts
        self.client.force_login(self.admin)
        dash = self.client.get(reverse("dashboard"))
        self.assertContains(dash, "11,30")
        hist = self.client.get(reverse("sales-history"))
        self.assertContains(hist, s1.correlative)
        self.assertContains(hist, s2.correlative)
        self.assertEqual(hist.context["total_descuentos"], Decimal("0.00"))

        # Warehouse stock overview and product Kardex reflect decremented stock cleanly
        self.client.force_login(self.warehouse)
        stock = self.client.get(reverse("stock-overview"))
        self.assertEqual(stock.status_code, 200)
        self.assertContains(stock, self.product_tax.name)
        mov = self.client.get(reverse("product-movements", args=(self.product_tax.pk,)))
        self.assertEqual(mov.status_code, 200)
        self.assertContains(mov, s1.correlative)
        self.assertEqual(Lot.objects.get(number="TAX-LOT-1").available_quantity, 48)
        self.assertEqual(Lot.objects.get(number="SEC-LOT-1").available_quantity, 19)
        self.assertEqual(shift.sales.count(), 2)
