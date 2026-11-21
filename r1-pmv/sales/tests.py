from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cash.models import CashRegister, CashShift
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot

from cash.models import CashShift, CashRegister  # noqa: F401 – used in test subclasses
from .models import SaleDraft, SaleDraftLine


class SalePreparationTests(TestCase):
    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
        cls.admin = Account.objects.create_user(
            "admin@test.invalid", cls.password, display_name="Admin", role=admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "warehouse@test.invalid", cls.password, display_name="Almacén", role=warehouse_role
        )
        cls.seller = Account.objects.create_user(
            "seller@test.invalid", cls.password, display_name="Vendedor uno", role=seller_role
        )
        cls.other_seller = Account.objects.create_user(
            "seller2@test.invalid", cls.password, display_name="Vendedor dos", role=seller_role
        )
        cls.cash_register = CashRegister.objects.create(code="CAJA-01")
        category = Category.objects.create(name="Productos enlatados")
        cls.product = Product.objects.create(
            category=category,
            name="Atún en lata",
            barcode="775000000001",
            sale_price=Decimal("118.00"),
        )
        load = InitialInventoryLoad.objects.create(product=cls.product, responsible=cls.warehouse)
        cls.sellable_lot = Lot.objects.create(
            product=cls.product,
            initial_load=load,
            number="VIGENTE-01",
            initial_quantity=3,
            available_quantity=3,
            unit_cost=Decimal("40.0000"),
            expiration_date=timezone.localdate() + timedelta(days=20),
        )
        cls.expired_lot = Lot.objects.create(
            product=cls.product,
            initial_load=load,
            number="VENCIDO-01",
            initial_quantity=8,
            available_quantity=8,
            unit_cost=Decimal("40.0000"),
            expiration_date=timezone.localdate(),
        )

    def open_shift(self, seller=None):
        return CashShift.objects.create(
            cash_register=self.cash_register,
            seller=seller or self.seller,
            opening_amount=Decimal("15.00"),
        )

    def add_line(self, quantity="1"):
        return self.client.post(
            reverse("sales-draft"),
            {"product_id": str(self.product.pk), "quantity": quantity},
        )

    def test_empty_preparation_needs_own_open_shift_and_creates_no_draft(self) -> None:
        self.client.force_login(self.seller)

        response = self.client.get(reverse("sales-draft"))

        self.assertContains(response, "Abre tu turno para preparar una venta")
        self.assertFalse(SaleDraft.objects.exists())

    def test_search_finds_active_sellable_product_by_name_or_barcode(self) -> None:
        self.open_shift()
        self.client.force_login(self.seller)

        by_name = self.client.get(reverse("sales-draft"), {"query": "atún"})
        by_code = self.client.get(reverse("sales-draft"), {"query": self.product.barcode})

        self.assertContains(by_name, self.product.name)
        self.assertContains(by_code, self.product.name)
        self.assertContains(by_name, "3")

    def test_first_line_creates_draft_and_does_not_move_stock_or_cash(self) -> None:
        shift = self.open_shift()
        self.client.force_login(self.seller)
        before_quantities = list(Lot.objects.values_list("id", "available_quantity"))

        response = self.add_line("2")

        draft = SaleDraft.objects.get()
        line = SaleDraftLine.objects.get()
        self.assertRedirects(response, f"{reverse('sales-draft')}?query=")
        self.assertEqual(draft.cash_shift, shift)
        self.assertEqual(draft.seller, self.seller)
        self.assertEqual(draft.status, SaleDraft.Status.ACTIVE)
        self.assertEqual(line.quantity, 2)
        self.assertEqual(line.unit_price, Decimal("118.00"))
        self.assertEqual(list(Lot.objects.values_list("id", "available_quantity")), before_quantities)
        shift.refresh_from_db()
        self.assertEqual(shift.opening_amount, Decimal("15.00"))

    def test_same_product_is_grouped_and_cannot_exceed_sellable_stock(self) -> None:
        self.open_shift()
        self.client.force_login(self.seller)
        self.add_line("1")
        self.add_line("1")

        rejected = self.add_line("2")

        self.assertContains(rejected, "supera las existencias vendibles")
        self.assertEqual(SaleDraftLine.objects.count(), 1)
        self.assertEqual(SaleDraftLine.objects.get().quantity, 2)

    def test_expired_or_today_lot_is_not_available_for_preparation(self) -> None:
        self.open_shift()
        self.client.force_login(self.seller)

        response = self.add_line("4")

        self.assertContains(response, "supera las existencias vendibles")
        self.assertFalse(SaleDraft.objects.exists())

    def test_update_and_remove_last_line_discards_draft_without_stock_change(self) -> None:
        self.open_shift()
        self.client.force_login(self.seller)
        self.add_line("1")
        line = SaleDraftLine.objects.get()
        before_quantities = list(Lot.objects.values_list("id", "available_quantity"))

        updated = self.client.post(reverse("sales-line-update", args=(line.pk,)), {"quantity": "3"})
        line.refresh_from_db()
        removed = self.client.post(reverse("sales-line-remove", args=(line.pk,)))

        draft = SaleDraft.objects.get()
        self.assertRedirects(updated, reverse("sales-draft"))
        self.assertEqual(line.quantity, 3)
        self.assertRedirects(removed, reverse("sales-draft"))
        self.assertEqual(draft.status, SaleDraft.Status.DISCARDED)
        self.assertIsNotNone(draft.discarded_at)
        self.assertFalse(SaleDraftLine.objects.exists())
        self.assertEqual(list(Lot.objects.values_list("id", "available_quantity")), before_quantities)

    def test_totals_show_price_base_igv_and_total_with_half_up_rule(self) -> None:
        self.open_shift()
        self.client.force_login(self.seller)
        self.add_line("2")

        response = self.client.get(reverse("sales-draft"))

        self.assertContains(response, "S/ 118,00 por unidad")
        self.assertContains(response, "S/ 200,00")
        self.assertContains(response, "S/ 36,00")
        self.assertContains(response, "S/ 236,00")
        self.assertContains(response, "no descuenta existencias ni mueve efectivo")

    def test_another_seller_cannot_use_the_open_shift_or_create_draft(self) -> None:
        self.open_shift(self.seller)
        self.client.force_login(self.other_seller)

        response = self.add_line("1")

        self.assertContains(response, "turno de caja abierto a tu nombre")
        self.assertFalse(SaleDraft.objects.exists())

    def test_only_seller_role_can_open_the_sales_preparation_route(self) -> None:
        for account in (self.admin, self.warehouse):
            with self.subTest(role=account.role.code):
                self.client.force_login(account)
                response = self.client.get(reverse("sales-draft"))
                self.assertEqual(response.status_code, 403)

    def test_logout_discards_active_draft_but_keeps_shift_and_stock(self) -> None:
        shift = self.open_shift()
        self.client.force_login(self.seller)
        self.add_line("1")
        before_quantities = list(Lot.objects.values_list("id", "available_quantity"))

        confirmation = self.client.get(reverse("logout"))
        response = self.client.post(reverse("logout"))

        draft = SaleDraft.objects.get()
        shift.refresh_from_db()
        self.assertContains(confirmation, "La venta en preparación se descartará")
        self.assertRedirects(response, reverse("login"))
        self.assertEqual(draft.status, SaleDraft.Status.DISCARDED)
        self.assertFalse(SaleDraftLine.objects.filter(draft=draft).exists())
        self.assertEqual(shift.status, CashShift.Status.OPEN)
        self.assertEqual(list(Lot.objects.values_list("id", "available_quantity")), before_quantities)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_canceling_logout_keeps_the_session_and_draft(self) -> None:
        self.open_shift()
        self.client.force_login(self.seller)
        self.add_line("1")

        confirmation = self.client.get(reverse("logout"))
        cancel = self.client.get(reverse("dashboard"))

        self.assertContains(confirmation, "La venta en preparación se descartará")
        self.assertEqual(cancel.status_code, 200)
        self.assertTrue(SaleDraft.objects.filter(status=SaleDraft.Status.ACTIVE).exists())
        self.assertIn("_auth_user_id", self.client.session)


# ─────────────────────────────────────────────────────────────────────────────
# HU-VEN-01c · Cobrar en efectivo y descontar existencias
# ─────────────────────────────────────────────────────────────────────────────

class CheckoutTests(TestCase):
    """CA1-6 de HU-VEN-01c: cobro FEFO, idempotencia y correlativo."""

    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
        cls.admin = Account.objects.create_user(
            "co_admin@test.invalid", cls.password, display_name="Admin", role=admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "co_warehouse@test.invalid", cls.password, display_name="Almacén", role=warehouse_role
        )
        cls.seller = Account.objects.create_user(
            "co_seller@test.invalid", cls.password, display_name="Vendedor cobro", role=seller_role
        )
        cls.cash_register = CashRegister.objects.create(code="CAJA-CO-01")
        category = Category.objects.create(name="Enlatados cobro")
        cls.product = Product.objects.create(
            category=category,
            name="Atún cobro",
            barcode="775000000099",
            sale_price=Decimal("118.00"),
        )

    def _open_shift(self):
        return CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("50.00"),
        )

    def _make_lot(self, number, quantity, days_ahead=20):
        load = InitialInventoryLoad.objects.get_or_create(
            product=self.product,
            defaults={"responsible": self.warehouse},
        )[0]
        return Lot.objects.create(
            product=self.product,
            initial_load=load,
            number=number,
            initial_quantity=quantity,
            available_quantity=quantity,
            unit_cost=Decimal("40.0000"),
            expiration_date=timezone.localdate() + timedelta(days=days_ahead),
        )

    def _prepare_sale(self, quantity=1):
        """Helper: add a line to draft via the view and return the draft."""
        self.client.post(
            reverse("sales-draft"),
            {"product_id": str(self.product.pk), "quantity": str(quantity)},
        )
        return SaleDraft.objects.filter(seller=self.seller, status=SaleDraft.Status.ACTIVE).first()

    def _post_checkout(self, cash_received, idem_key=None):
        import uuid as _uuid
        if idem_key is None:
            idem_key = _uuid.uuid4()
        page = self.client.get(reverse("sales-checkout"))
        initial = page.context["form"].initial if page.status_code == 200 else {}
        return self.client.post(
            reverse("sales-checkout"),
            {
                "expected_subtotal": str(initial.get("expected_subtotal", "")),
                "draft_signature": initial.get("draft_signature", ""),
                "cash_received": str(cash_received),
                "idempotency_key": str(idem_key),
            },
        ), idem_key

    # ── CA1: Pago exacto completa venta, descuenta lotes FEFO y registra snapshots ──

    def test_exact_payment_creates_sale_and_deducts_lot_stock(self) -> None:
        from .models import Sale, SaleLine
        self._open_shift()
        self.client.force_login(self.seller)
        lot = self._make_lot("LOTE-CA1", 3)
        self._prepare_sale(quantity=2)

        response, _ = self._post_checkout(Decimal("236.00"))  # 2 × 118.00

        sale = Sale.objects.get(seller=self.seller)
        lot.refresh_from_db()
        self.assertRedirects(response, reverse("sales-receipt", args=(sale.pk,)))
        self.assertEqual(sale.total_amount, Decimal("236.00"))
        self.assertEqual(sale.change_given, Decimal("0.00"))
        self.assertRegex(sale.correlative, r"V-\d{8}")
        lines = SaleLine.objects.filter(sale=sale)
        self.assertEqual(lines.count(), 1)
        self.assertEqual(lines.first().product_snapshot_name, "Atún cobro")
        self.assertEqual(lot.available_quantity, 1)  # 3 - 2

    # ── CA2: Pago insuficiente no crea venta ni modifica lotes ──

    def test_insufficient_cash_rejected_no_sale_no_stock_change(self) -> None:
        from .models import Sale
        self._open_shift()
        self.client.force_login(self.seller)
        lot = self._make_lot("LOTE-CA2", 2)
        self._prepare_sale(quantity=1)
        before_qty = lot.available_quantity

        response, _ = self._post_checkout(Decimal("100.00"))  # less than 118.00

        self.assertEqual(Sale.objects.count(), 0)
        lot.refresh_from_db()
        self.assertEqual(lot.available_quantity, before_qty)
        self.assertContains(response, "insuficiente")

    # ── CA3: Efectivo mayor al total → calcula vuelto correcto ──

    def test_overpayment_records_correct_change(self) -> None:
        from .models import Sale
        self._open_shift()
        self.client.force_login(self.seller)
        self._make_lot("LOTE-CA3", 5)
        self._prepare_sale(quantity=1)

        self._post_checkout(Decimal("200.00"))  # 200 - 118 = 82 vuelto

        sale = Sale.objects.get(seller=self.seller)
        self.assertEqual(sale.cash_received, Decimal("200.00"))
        self.assertEqual(sale.change_given, Decimal("82.00"))

    # ── CA4: Reintento con la misma idempotency_key devuelve la misma venta ──

    def test_duplicate_idempotency_key_returns_same_sale(self) -> None:
        import uuid as _uuid
        from .models import Sale
        self._open_shift()
        self.client.force_login(self.seller)
        self._make_lot("LOTE-CA4", 5)
        self._prepare_sale(quantity=1)
        idem = _uuid.uuid4()

        self._post_checkout(Decimal("118.00"), idem_key=idem)
        # Second attempt with the same key (draft is now DISCARDED, re-prepare)
        self._make_lot("LOTE-CA4B", 5)
        self._prepare_sale(quantity=1)
        self._post_checkout(Decimal("118.00"), idem_key=idem)

        # Only one Sale should exist for this key
        self.assertEqual(Sale.objects.filter(idempotency_key=idem).count(), 1)

    def test_idempotency_key_cannot_be_reused_for_another_draft(self) -> None:
        import uuid
        from django.core.exceptions import ValidationError
        from .services import checkout_sale

        self._open_shift()
        self.client.force_login(self.seller)
        lot = self._make_lot("LOTE-KEY", 5)
        first = self._prepare_sale()
        key = uuid.uuid4()
        sale = checkout_sale(actor=self.seller, draft_id=first.pk,
                             cash_received=Decimal("118.00"), idempotency_key=key)
        self.assertEqual(checkout_sale(actor=self.seller, draft_id=first.pk,
                                      cash_received=Decimal("118.00"), idempotency_key=key), sale)
        second = self._prepare_sale()
        with self.assertRaises(ValidationError):
            checkout_sale(actor=self.seller, draft_id=second.pk,
                          cash_received=Decimal("118.00"), idempotency_key=key)
        lot.refresh_from_db()
        self.assertEqual(lot.available_quantity, 4)
        second.refresh_from_db()
        self.assertEqual(second.status, SaleDraft.Status.ACTIVE)

    # ── CA5: Dos ventas distintas tienen correlativos únicos secuenciales ──

    def test_two_different_sales_get_unique_sequential_correlatives(self) -> None:
        import uuid as _uuid
        from .models import Sale
        self._open_shift()
        self.client.force_login(self.seller)
        self._make_lot("LOTE-CA5A", 5)
        self._prepare_sale(quantity=1)
        self._post_checkout(Decimal("118.00"), idem_key=_uuid.uuid4())

        # Close shift to open a new one (the unique constraint allows only one open shift)
        from cash.services import close_cash_shift
        close_cash_shift(actor=self.seller, counted_amount=Decimal("168.00"))
        self._open_shift()

        self._make_lot("LOTE-CA5B", 5)
        self._prepare_sale(quantity=1)
        self._post_checkout(Decimal("118.00"), idem_key=_uuid.uuid4())

        sales = list(Sale.objects.filter(seller=self.seller).order_by("confirmed_at"))
        self.assertEqual(len(sales), 2)
        self.assertNotEqual(sales[0].correlative, sales[1].correlative)
        # The second correlative number should be greater than the first
        n1 = int(sales[0].correlative.split("-")[1])
        n2 = int(sales[1].correlative.split("-")[1])
        self.assertGreater(n2, n1)

    # ── CA6: Rol no-SELLER recibe 403 ──

    def test_non_seller_roles_cannot_access_checkout(self) -> None:
        self._open_shift()
        self._make_lot("LOTE-CA6", 5)
        for account in (self.admin, self.warehouse):
            with self.subTest(role=account.role.code):
                self.client.force_login(account)
                response, _ = self._post_checkout(Decimal("118.00"))
                self.assertEqual(response.status_code, 403)


# ─────────────────────────────────────────────────────────────────────────────
# HU-VEN-02a · Generar una constancia interna de venta
# ─────────────────────────────────────────────────────────────────────────────

class ReceiptTests(TestCase):
    """CA1-4 de HU-VEN-02a: constancia histórica, inmutable, con leyenda."""

    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        from .models import Sale, SaleLine
        import uuid as _uuid
        seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
        admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.seller = Account.objects.create_user(
            "rec_seller@test.invalid", cls.password, display_name="Vendedor constancia", role=seller_role
        )
        cls.admin = Account.objects.create_user(
            "rec_admin@test.invalid", cls.password, display_name="Admin constancia", role=admin_role
        )
        cls.other_seller = Account.objects.create_user(
            "rec_other@test.invalid", cls.password, display_name="Otro vendedor", role=seller_role
        )
        cls.warehouse = Account.objects.create_user(
            "rec_wh@test.invalid", cls.password, display_name="Almacén constancia", role=warehouse_role
        )
        cash_register = CashRegister.objects.create(code="CAJA-REC-01")
        shift = CashShift.objects.create(
            cash_register=cash_register,
            seller=cls.seller,
            opening_amount=Decimal("0.00"),
        )
        category = Category.objects.create(name="Enlatados recibo")
        product = Product.objects.create(
            category=category,
            name="Leche condensada recibo",
            barcode="775000000011",
            sale_price=Decimal("50.00"),
        )
        idem = _uuid.uuid4()
        cls.sale = Sale.objects.create(
            cash_shift=shift,
            seller=cls.seller,
            seller_snapshot_name=cls.seller.display_name,
            cash_register_snapshot_code=cash_register.code,
            total_amount=Decimal("100.00"),
            base_amount=Decimal("84.75"),
            igv_amount=Decimal("15.25"),
            cash_received=Decimal("100.00"),
            change_given=Decimal("0.00"),
            correlative="V-00000001",
            idempotency_key=idem,
        )
        SaleLine.objects.create(
            sale=cls.sale,
            position=1,
            product_snapshot_name="Leche condensada recibo",
            product_snapshot_barcode="775000000011",
            quantity=2,
            unit_price=Decimal("50.00"),
            amount=Decimal("100.00"),
        )
        # mutate product to prove snapshots are historical
        product.name = "Nombre cambiado"
        product.save()

    # ── CA1: Muestra correlativo, fecha, vendedor, caja, líneas e importes ──

    def test_receipt_shows_all_required_fields(self) -> None:
        self.client.force_login(self.seller)
        response = self.client.get(reverse("sales-receipt", args=(self.sale.pk,)))

        self.assertContains(response, "V-00000001")
        self.assertContains(response, self.seller.display_name)
        self.assertContains(response, "CAJA-REC-01")
        self.assertContains(response, "100,00")
        self.assertContains(response, "84,75")
        self.assertContains(response, "15,25")

    # ── CA2: Los datos son inmutables (snapshots, no recalculados) ──

    def test_receipt_uses_snapshots_not_live_product_data(self) -> None:
        self.client.force_login(self.seller)
        response = self.client.get(reverse("sales-receipt", args=(self.sale.pk,)))

        # Shows the snapshot name, not the mutated live name
        self.assertContains(response, "Leche condensada recibo")
        self.assertNotContains(response, "Nombre cambiado")

    # ── CA3: Contiene la leyenda obligatoria (no validez tributaria) ──

    def test_receipt_contains_mandatory_legal_notice(self) -> None:
        self.client.force_login(self.seller)
        response = self.client.get(reverse("sales-receipt", args=(self.sale.pk,)))

        self.assertContains(response, "constancia interna")
        self.assertContains(response, "validez tributaria")

    # ── CA4: Solo el vendedor dueño puede acceder; otro recibe 404 ──

    def test_other_seller_gets_404_for_different_sale(self) -> None:
        self.client.force_login(self.other_seller)
        response = self.client.get(reverse("sales-receipt", args=(self.sale.pk,)))
        self.assertEqual(response.status_code, 404)


# ─────────────────────────────────────────────────────────────────────────────
# HU-CAJA-02 · Cerrar y cuadrar la caja
# ─────────────────────────────────────────────────────────────────────────────

class CashCloseTests(TestCase):
    """CA1-5 de HU-CAJA-02: cierre con exacto, sobrante, faltante, bloqueo y doble cierre."""

    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
        admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.admin = Account.objects.create_user(
            "cl_admin@test.invalid", cls.password, display_name="Admin cierre", role=admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "cl_wh@test.invalid", cls.password, display_name="Almacén cierre", role=warehouse_role
        )
        cls.seller = Account.objects.create_user(
            "cl_seller@test.invalid", cls.password, display_name="Vendedor cierre", role=seller_role
        )
        cls.cash_register = CashRegister.objects.create(code="CAJA-CL-01")

    def _open_shift(self, opening=Decimal("100.00")):
        return CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=opening,
        )

    def _post_close(self, counted):
        return self.client.post(reverse("cash-close"), {"counted_amount": str(counted)})

    # ── CA1: Exacto → diferencia = 0 ──

    def test_close_exact_amount_records_zero_difference(self) -> None:
        from cash.models import CashShiftClose
        shift = self._open_shift(opening=Decimal("100.00"))
        self.client.force_login(self.seller)

        response = self._post_close(Decimal("100.00"))

        close = CashShiftClose.objects.get(cash_shift=shift)
        self.assertRedirects(response, reverse("cash-shift-closed", args=(shift.pk,)))
        self.assertEqual(close.difference, Decimal("0.00"))
        self.assertEqual(close.expected_amount, Decimal("100.00"))
        self.assertEqual(close.counted_amount, Decimal("100.00"))
        shift.refresh_from_db()
        self.assertEqual(shift.status, CashShift.Status.CLOSED)

    # ── CA2: Sobrante → diferencia > 0 ──

    def test_close_surplus_records_positive_difference(self) -> None:
        from cash.models import CashShiftClose
        shift = self._open_shift(opening=Decimal("50.00"))
        self.client.force_login(self.seller)

        self._post_close(Decimal("80.00"))

        close = CashShiftClose.objects.get(cash_shift=shift)
        self.assertEqual(close.difference, Decimal("30.00"))

    # ── CA3: Faltante → diferencia < 0 ──

    def test_close_shortage_records_negative_difference(self) -> None:
        from cash.models import CashShiftClose
        shift = self._open_shift(opening=Decimal("100.00"))
        self.client.force_login(self.seller)

        self._post_close(Decimal("70.00"))

        close = CashShiftClose.objects.get(cash_shift=shift)
        self.assertEqual(close.difference, Decimal("-30.00"))

    # ── CA4: Borrador con líneas bloquea el cierre ──

    def test_close_blocked_when_active_draft_has_lines(self) -> None:
        from cash.models import CashShiftClose
        import uuid as _uuid
        shift = self._open_shift()
        # Create category, product, lot and draft with a line
        category = Category.objects.create(name="Enlatados cierre")
        product = Product.objects.create(
            category=category, name="Producto cierre", barcode="775000000055",
            sale_price=Decimal("10.00"),
        )
        load = InitialInventoryLoad.objects.create(product=product, responsible=self.warehouse)
        Lot.objects.create(
            product=product, initial_load=load, number="LOTE-BLK",
            initial_quantity=5, available_quantity=5,
            unit_cost=Decimal("5.0000"),
            expiration_date=timezone.localdate() + timedelta(days=10),
        )
        draft = SaleDraft.objects.create(cash_shift=shift, seller=self.seller)
        SaleDraftLine.objects.create(draft=draft, product=product, quantity=1, unit_price=Decimal("10.00"))
        self.client.force_login(self.seller)

        response = self._post_close(Decimal("100.00"))

        self.assertFalse(CashShiftClose.objects.exists())
        self.assertContains(response, "venta en preparación")
        shift.refresh_from_db()
        self.assertEqual(shift.status, CashShift.Status.OPEN)

    # ── CA5: Doble cierre → el segundo no duplica ni altera el acta ──

    def test_double_close_does_not_create_duplicate(self) -> None:
        from cash.models import CashShiftClose
        shift = self._open_shift()
        self.client.force_login(self.seller)

        self._post_close(Decimal("100.00"))
        # Shift is now CLOSED; second attempt should fail gracefully
        response = self._post_close(Decimal("100.00"))

        self.assertEqual(CashShiftClose.objects.filter(cash_shift=shift).count(), 1)
        # The view should stay on the form with an error (no turno abierto)
        self.assertContains(response, "No tienes un turno")

    # ── Extra: Roles no-SELLER reciben 403 ──

    def test_non_seller_roles_cannot_close_shift(self) -> None:
        self._open_shift()
        for account in (self.admin, self.warehouse):
            with self.subTest(role=account.role.code):
                self.client.force_login(account)
                response = self._post_close(Decimal("100.00"))
                self.assertEqual(response.status_code, 403)

    # ── Acta de cierre es visible y correcta ──

    def test_closed_shift_detail_shows_correct_amounts(self) -> None:
        shift = self._open_shift(opening=Decimal("200.00"))
        self.client.force_login(self.seller)
        self._post_close(Decimal("210.00"))  # 10 sobrante

        response = self.client.get(reverse("cash-shift-closed", args=(shift.pk,)))

        self.assertContains(response, "200,00")  # expected (opening + 0 sales)
        self.assertContains(response, "210,00")  # counted
        self.assertContains(response, "10,00")   # difference


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 2 — HU-VEN-05a y HU-VEN-05b
# ═══════════════════════════════════════════════════════════════════════════════

class _SaleHistoryBase(TestCase):
    """Base con infraestructura mínima para tests de historial de ventas."""
    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
        cls.admin = Account.objects.create_user(
            "adminh@test.invalid", cls.password, display_name="Admin H", role=admin_role
        )
        cls.seller = Account.objects.create_user(
            "sellerh@test.invalid", cls.password, display_name="Seller H", role=seller_role
        )
        cls.other_seller = Account.objects.create_user(
            "sellerh2@test.invalid", cls.password, display_name="Seller H2", role=seller_role
        )
        cls.cash_register = CashRegister.objects.create(code="CAJA-H1")


# ── HU-VEN-05a · Historial de ventas del turno actual ────────────────────────

class SalesShiftHistoryTests(_SaleHistoryBase):
    def test_seller_with_no_shift_gets_200_with_empty_message(self) -> None:
        self.client.force_login(self.seller)
        response = self.client.get(reverse("sales-shift-history"))
        self.assertEqual(response.status_code, 200)

    def test_seller_with_open_shift_sees_page(self) -> None:
        shift = CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("0.00"),
        )
        self.client.force_login(self.seller)
        response = self.client.get(reverse("sales-shift-history"))
        self.assertEqual(response.status_code, 200)
        # Limpiar shift abierto
        shift.delete()

    def test_non_seller_gets_403(self) -> None:
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("sales-shift-history")).status_code, 403)


# ── HU-VEN-05b · Historial completo de ventas ────────────────────────────────

class SalesHistoryTests(_SaleHistoryBase):
    def test_admin_can_access_sales_history(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("sales-history"))
        self.assertEqual(response.status_code, 200)

    def test_seller_can_access_sales_history(self) -> None:
        self.client.force_login(self.seller)
        response = self.client.get(reverse("sales-history"))
        self.assertEqual(response.status_code, 200)

    def test_filter_by_fecha_returns_200(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("sales-history"), {"fecha": "2026-01-01"})
        self.assertEqual(response.status_code, 200)

    def test_filter_by_correlativo_and_invalid_fecha_do_not_crash(self) -> None:
        self.client.force_login(self.admin)
        r1 = self.client.get(reverse("sales-history"), {"correlativo": "V-00000001"})
        self.assertEqual(r1.status_code, 200)
        r2 = self.client.get(reverse("sales-history"), {"fecha": "fecha-invalida"})
        self.assertEqual(r2.status_code, 200)
        self.assertContains(r2, "La fecha ingresada no es válida")

    def test_discard_draft_endpoint_clears_active_draft(self) -> None:
        from catalog.models import Category, Product
        from sales.models import SaleDraft, SaleDraftLine

        cat = Category.objects.create(name="Productos enlatados")
        prod = Product.objects.create(
            category=cat, name="Atún Test Discard", barcode="77599901", sale_price=Decimal("5.00")
        )
        shift = CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("50.00"),
        )
        draft = SaleDraft.objects.create(cash_shift=shift, seller=self.seller)
        SaleDraftLine.objects.create(draft=draft, product=prod, quantity=1, unit_price=Decimal("5.00"))
        self.client.force_login(self.seller)
        resp = self.client.post(reverse("sales-draft-discard"))
        self.assertRedirects(resp, reverse("sales-draft"))
        draft.refresh_from_db()
        self.assertEqual(draft.status, SaleDraft.Status.DISCARDED)

    def test_sales_history_and_shift_history_display_discount_column_and_totals(self) -> None:
        """BUG-015: El historial de ventas y del turno muestran la columna Descuento (S/) y totales."""
        import uuid as _uuid
        from sales.models import Sale

        shift = CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("50.00"),
        )
        Sale.objects.create(
            cash_shift=shift,
            seller=self.seller,
            total_amount=Decimal("18.00"),
            discount_amount=Decimal("2.00"),
            base_amount=Decimal("15.25"),
            igv_amount=Decimal("2.75"),
            cash_received=Decimal("20.00"),
            change_given=Decimal("2.00"),
            correlative="V-00088801",
            idempotency_key=_uuid.uuid4(),
        )
        self.client.force_login(self.admin)
        hist_resp = self.client.get(reverse("sales-history"))
        self.assertContains(hist_resp, "Descuento (S/)")
        self.assertContains(hist_resp, "Total vendido (filtrado):")

        self.client.force_login(self.seller)
        shift_resp = self.client.get(reverse("sales-shift-history"))
        self.assertContains(shift_resp, "Descuento (S/)")
        self.assertContains(shift_resp, "Descuentos: S/ 2,00")

    def test_sales_receipt_hides_nueva_venta_for_admin_and_shows_back_to_history(self) -> None:
        """BUG-008 y BUG-023: En la constancia de venta, Admin no ve 'Nueva venta' (que daba 403) y ve 'Volver al historial'."""
        import uuid as _uuid
        from sales.models import Sale

        shift = CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("50.00"),
        )
        sale = Sale.objects.create(
            cash_shift=shift,
            seller=self.seller,
            total_amount=Decimal("10.00"),
            base_amount=Decimal("8.47"),
            igv_amount=Decimal("1.53"),
            cash_received=Decimal("10.00"),
            change_given=Decimal("0.00"),
            correlative="V-00088802",
            idempotency_key=_uuid.uuid4(),
        )
        self.client.force_login(self.admin)
        admin_resp = self.client.get(reverse("sales-receipt", args=(sale.pk,)))
        self.assertEqual(admin_resp.status_code, 200)
        self.assertContains(admin_resp, reverse("sales-history"))
        self.assertNotContains(admin_resp, "Nueva venta")

    def test_price_change_during_checkout_warns_seller_and_updates_draft_line_price(self) -> None:
        """BUG-006: Si el Admin cambia el precio mientras la vendedora está en /ventas/cobrar/, se alerta y actualiza el precio."""
        import uuid as _uuid
        from datetime import timedelta
        from catalog.models import Category, Product
        from inventory.models import InitialInventoryLoad, Lot
        from sales.models import Sale, SaleDraftLine

        cat = Category.objects.create(name="Cat Colision Precio")
        prod = Product.objects.create(
            category=cat, name="Producto Colision", barcode="77577701", sale_price=Decimal("10.00")
        )
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.admin)
        Lot.objects.create(
            product=prod,
            initial_load=load,
            number="L-COL-1",
            initial_quantity=10,
            available_quantity=10,
            unit_cost=Decimal("5.0000"),
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("50.00"),
        )
        self.client.force_login(self.seller)
        self.client.post(reverse("sales-draft"), {"product_id": str(prod.pk), "quantity": "1"})

        initial_review = self.client.get(reverse("sales-checkout")).context["form"].initial
        # Admin cambia el precio a S/ 15.00 antes del cobro
        prod.sale_price = Decimal("15.00")
        prod.save(update_fields=["sale_price"])

        resp = self.client.post(
            reverse("sales-checkout"),
            {
                "expected_subtotal": str(initial_review["expected_subtotal"]),
                "draft_signature": initial_review["draft_signature"],
                "cash_received": "20.00",
                "idempotency_key": str(_uuid.uuid4()),
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "cambió de S/ 10.00 a S/ 15.00")
        self.assertEqual(Sale.objects.count(), 0)
        line = SaleDraftLine.objects.get(product=prod)
        self.assertEqual(line.unit_price, Decimal("15.00"))

    def test_multitab_draft_modification_warns_seller_on_checkout(self) -> None:
        """BUG-007: Si el borrador se modifica en otra pestaña antes de confirmar cobro, se advierte el nuevo subtotal."""
        import uuid as _uuid
        from datetime import timedelta
        from catalog.models import Category, Product
        from inventory.models import InitialInventoryLoad, Lot
        from sales.models import Sale

        cat = Category.objects.create(name="Cat Multitab")
        prod = Product.objects.create(
            category=cat, name="Producto Multitab", barcode="77577702", sale_price=Decimal("10.00")
        )
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.admin)
        Lot.objects.create(
            product=prod,
            initial_load=load,
            number="L-MT-1",
            initial_quantity=10,
            available_quantity=10,
            unit_cost=Decimal("5.0000"),
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("50.00"),
        )
        self.client.force_login(self.seller)
        self.client.post(reverse("sales-draft"), {"product_id": str(prod.pk), "quantity": "2"})

        initial_review = self.client.get(reverse("sales-checkout")).context["form"].initial
        # La pestaña 1 tenía expected_subtotal=30.00 pero el carrito ahora suma 20.00
        resp = self.client.post(
            reverse("sales-checkout"),
            {
                "cash_received": "30.00",
                "expected_subtotal": "30.00",
                "draft_signature": initial_review["draft_signature"],
                "idempotency_key": str(_uuid.uuid4()),
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "El resumen de la venta en preparación cambió")
        self.assertEqual(Sale.objects.count(), 0)

    def test_bug025_checkout_detects_same_subtotal_product_swap_via_draft_signature(self) -> None:
        """BUG-025: Si se sustituye un producto por otro del mismo precio en otra pestaña, el cobro lo detecta."""
        import uuid as _uuid
        from catalog.models import Category
        from inventory.models import InitialInventoryLoad, Lot
        from sales.models import Sale
        from sales.services import remove_draft_line

        cat, _ = Category.objects.get_or_create(
            name_normalized="productos enlatados", defaults={"name": "Productos enlatados"}
        )
        prod_a = Product.objects.create(
            category=cat,
            name="Atun A 10 soles",
            barcode="775000250001",
            sale_price=Decimal("10.00"),
        )
        prod_b = Product.objects.create(
            category=cat,
            name="Caballa B 10 soles",
            barcode="775000250002",
            sale_price=Decimal("10.00"),
        )
        for p, code in ((prod_a, "LA-25"), (prod_b, "LB-25")):
            load = InitialInventoryLoad.objects.create(product=p, responsible=self.admin)
            Lot.objects.create(
                product=p,
                initial_load=load,
                number=code,
                initial_quantity=10,
                available_quantity=10,
                unit_cost=Decimal("5.0000"),
                expiration_date=timezone.localdate() + timedelta(days=60),
            )
        CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("50.00"),
        )
        self.client.force_login(self.seller)
        self.client.post(reverse("sales-draft"), {"product_id": str(prod_a.pk), "quantity": "1"})

        get_resp = self.client.get(reverse("sales-checkout"))
        self.assertEqual(get_resp.status_code, 200)
        initial_sig = get_resp.context["form"].initial["draft_signature"]
        initial_subtotal = get_resp.context["form"].initial["expected_subtotal"]

        # En otra pestaña se reemplaza prod_a por prod_b manteniendo el subtotal 10.00
        draft = get_resp.context["draft"]
        remove_draft_line(actor=self.seller, line_id=draft.lines.first().pk)
        self.client.post(reverse("sales-draft"), {"product_id": str(prod_b.pk), "quantity": "1"})

        post_resp = self.client.post(
            reverse("sales-checkout"),
            {
                "cash_received": "10.00",
                "discount_amount": "",
                "idempotency_key": str(_uuid.uuid4()),
                "expected_subtotal": str(initial_subtotal),
                "draft_signature": initial_sig,
            },
        )
        self.assertEqual(post_resp.status_code, 200)
        self.assertContains(post_resp, "El resumen de la venta en preparación cambió")
        self.assertEqual(Sale.objects.count(), 0)

    def test_bug006_draft_warns_seller_when_catalog_price_changes_during_preparation(self) -> None:
        """BUG-006: Al actualizar cantidad en el borrador tras cambio de precio del catálogo, se avisa al vendedor."""
        from catalog.models import Category
        from inventory.models import InitialInventoryLoad, Lot

        cat, _ = Category.objects.get_or_create(
            name_normalized="productos enlatados", defaults={"name": "Productos enlatados"}
        )
        prod = Product.objects.create(
            category=cat,
            name="Conserva Cambio Precio",
            barcode="775000060001",
            sale_price=Decimal("5.50"),
        )
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.admin)
        Lot.objects.create(
            product=prod,
            initial_load=load,
            number="L-06",
            initial_quantity=10,
            available_quantity=10,
            unit_cost=Decimal("3.0000"),
            expiration_date=timezone.localdate() + timedelta(days=60),
        )
        CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("50.00"),
        )
        self.client.force_login(self.seller)
        self.client.post(reverse("sales-draft"), {"product_id": str(prod.pk), "quantity": "1"})
        line = prod.sale_draft_lines.first()

        prod.sale_price = Decimal("9.50")
        prod.save(update_fields=["sale_price", "updated_at"])

        resp = self.client.post(
            reverse("sales-line-update", args=(line.pk,)),
            {"quantity": "2"},
            follow=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "se actualizó de S/ 5.50 a S/ 9.50")

    def test_new_checkout_keeps_full_total_on_validation_error(self) -> None:
        """A rejected discount must never be previewed as an accepted total."""
        import uuid as _uuid
        from catalog.models import Category
        from inventory.models import InitialInventoryLoad, Lot

        cat, _ = Category.objects.get_or_create(
            name_normalized="productos enlatados", defaults={"name": "Productos enlatados"}
        )
        prod = Product.objects.create(
            category=cat,
            name="Conserva Descuento 29",
            barcode="775000290001",
            sale_price=Decimal("5.50"),
        )
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.admin)
        Lot.objects.create(
            product=prod,
            initial_load=load,
            number="L-29",
            initial_quantity=10,
            available_quantity=10,
            unit_cost=Decimal("3.0000"),
            expiration_date=timezone.localdate() + timedelta(days=60),
        )
        CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("50.00"),
        )
        self.client.force_login(self.seller)
        self.client.post(reverse("sales-draft"), {"product_id": str(prod.pk), "quantity": "2"})

        resp = self.client.post(
            reverse("sales-checkout"),
            {
                "cash_received": "5.00",
                "discount_amount": "3.00",
                "idempotency_key": str(_uuid.uuid4()),
            },
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context["totals"].total, Decimal("11.00"))
        self.assertEqual(resp.context["subtotal"], Decimal("11.00"))
        self.assertContains(resp, "recalc();")

    def test_bug033_and_bug037_inactive_category_or_product_blocks_search_draft_line_update_and_checkout(self) -> None:
        """BUG-033 y BUG-037: Desactivar categoría o producto bloquea búsqueda, actualización de cantidad en borrador y cobro."""
        import uuid as _uuid
        from catalog.models import Category
        from inventory.models import InitialInventoryLoad, Lot
        from sales.models import Sale

        cat = Category.objects.create(name="Cat Ventas 33", is_active=True)
        prod = Product.objects.create(
            category=cat,
            name="Conserva Bloqueo 33",
            barcode="775000339991",
            sale_price=Decimal("6.00"),
        )
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.admin)
        Lot.objects.create(
            product=prod,
            initial_load=load,
            number="L-33-V",
            initial_quantity=10,
            available_quantity=10,
            unit_cost=Decimal("3.0000"),
            expiration_date=timezone.localdate() + timedelta(days=60),
        )
        CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("50.00"),
        )
        self.client.force_login(self.seller)
        self.client.post(reverse("sales-draft"), {"product_id": str(prod.pk), "quantity": "1"})
        line = prod.sale_draft_lines.first()

        # Desactivar producto impide aumentar cantidad en el borrador (BUG-037)
        prod.is_active = False
        prod.save(update_fields=["is_active"])
        upd_resp = self.client.post(
            reverse("sales-line-update", args=(line.pk,)),
            {"quantity": "5"},
            follow=True,
        )
        self.assertContains(upd_resp, "no está disponible para la venta")
        line.refresh_from_db()
        self.assertEqual(line.quantity, 1)

        # Reactivar producto pero desactivar categoría bloquea búsqueda, incremento y cobro (BUG-033)
        prod.is_active = True
        prod.save(update_fields=["is_active"])
        cat.is_active = False
        cat.save(update_fields=["is_active"])

        search_resp = self.client.get(reverse("sales-draft"), {"query": "Conserva Bloqueo 33"})
        self.assertEqual(list(search_resp.context["products"]), [])

        initial_review = self.client.get(reverse("sales-checkout")).context["form"].initial
        checkout_resp = self.client.post(
            reverse("sales-checkout"),
            {
                "expected_subtotal": str(initial_review["expected_subtotal"]),
                "draft_signature": initial_review["draft_signature"],
                "cash_received": "10.00",
                "idempotency_key": str(_uuid.uuid4()),
            },
        )
        self.assertEqual(checkout_resp.status_code, 200)
        self.assertContains(checkout_resp, "ya no está disponible para la venta")
        self.assertEqual(Sale.objects.count(), 0)

    def test_bug035_and_bug036_draft_signature_includes_draft_id_and_checkout_renders_hidden_field_errors(self) -> None:
        """BUG-035 y BUG-036: La firma del borrador incluye draft.pk para impedir cobro cruzado entre borradores y muestra errores de campos ocultos."""
        import uuid as _uuid
        from catalog.models import Category
        from inventory.models import InitialInventoryLoad, Lot
        from sales.models import Sale

        cat, _ = Category.objects.get_or_create(
            name_normalized="productos enlatados", defaults={"name": "Productos enlatados"}
        )
        prod = Product.objects.create(
            category=cat,
            name="Conserva Firma 35",
            barcode="775000350001",
            sale_price=Decimal("8.00"),
        )
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.admin)
        Lot.objects.create(
            product=prod,
            initial_load=load,
            number="L-35",
            initial_quantity=20,
            available_quantity=20,
            unit_cost=Decimal("4.0000"),
            expiration_date=timezone.localdate() + timedelta(days=90),
        )
        CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("50.00"),
        )
        self.client.force_login(self.seller)

        # Borrador 1 (Cliente 1)
        self.client.post(reverse("sales-draft"), {"product_id": str(prod.pk), "quantity": "1"})
        tab1_get = self.client.get(reverse("sales-checkout"))
        stale_sig = tab1_get.context["form"].initial["draft_signature"]
        stale_subtotal = tab1_get.context["form"].initial["expected_subtotal"]

        # Se descarta Borrador 1 y se crea Borrador 2 (Cliente 2) con el mismo producto y cantidad
        self.client.post(reverse("sales-draft-discard"))
        self.client.post(reverse("sales-draft"), {"product_id": str(prod.pk), "quantity": "1"})

        # La pestaña antigua intenta cobrar con la firma de Borrador 1 -> debe bloquearse
        cross_resp = self.client.post(
            reverse("sales-checkout"),
            {
                "cash_received": "10.00",
                "expected_subtotal": str(stale_subtotal),
                "draft_signature": stale_sig,
                "idempotency_key": str(_uuid.uuid4()),
            },
        )
        self.assertEqual(cross_resp.status_code, 200)
        self.assertContains(cross_resp, "El resumen de la venta en preparación cambió")
        self.assertEqual(Sale.objects.count(), 0)

        # Enviar un idempotency_key corrupto muestra error visible en .alert-error (BUG-036)
        corrupt_resp = self.client.post(
            reverse("sales-checkout"),
            {
                "cash_received": "10.00",
                "idempotency_key": "corrupt-uuid",
            },
        )
        self.assertEqual(corrupt_resp.status_code, 200)
        self.assertContains(corrupt_resp, "alert-error")
