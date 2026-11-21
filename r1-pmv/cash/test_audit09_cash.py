from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot
from sales.models import SaleDraft
from sales.services import (
    add_product_to_draft,
    checkout_sale,
    discard_active_draft,
    remove_draft_line,
)

from .models import CashRegister, CashShift, CashShiftClose
from .services import close_cash_shift, open_cash_shift


class Audit09CashRegressionTests(TestCase):
    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

        cls.admin = Account.objects.create_user(
            "admin.a09@test.invalid", cls.password, display_name="Admin A09", role=cls.admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "wh.a09@test.invalid", cls.password, display_name="Almacén A09", role=cls.warehouse_role
        )
        cls.seller1 = Account.objects.create_user(
            "seller1.a09@test.invalid", cls.password, display_name="Vendedor Uno A09", role=cls.seller_role
        )
        cls.seller2 = Account.objects.create_user(
            "seller2.a09@test.invalid", cls.password, display_name="Vendedor Dos Largo A09", role=cls.seller_role
        )

        cls.cash_register = CashRegister.objects.create(code="CAJA-01")
        category = Category.objects.create(name="Bebidas A09")
        cls.product = Product.objects.create(
            category=category,
            name="Gaseosa A09 500ml",
            barcode="775999000001",
            sale_price=Decimal("5.50"),
        )
        load = InitialInventoryLoad.objects.create(product=cls.product, responsible=cls.warehouse)
        Lot.objects.create(
            product=cls.product,
            initial_load=load,
            number="LOTE-A09-1",
            initial_quantity=50,
            available_quantity=50,
            unit_cost=Decimal("3.0000"),
            expiration_date=timezone.localdate() + timedelta(days=90),
        )

    def _assert_no_store(self, response) -> None:
        cache_control = response.headers.get("Cache-Control", "")
        self.assertIn("no-store", cache_control.lower())

    def test_anonymous_redirects_on_all_cash_urls(self) -> None:
        fake_id = uuid.uuid4()
        urls = [
            reverse("cash-open"),
            reverse("cash-close"),
            reverse("cash-shift-opened", args=(fake_id,)),
            reverse("cash-shift-closed", args=(fake_id,)),
            reverse("cash-shift-history"),
        ]
        for url in urls:
            with self.subTest(url=url):
                resp = self.client.get(url)
                self.assertRedirects(resp, f"{reverse('login')}?next={url}", fetch_redirect_response=False)

        for post_url in (reverse("cash-open"), reverse("cash-close")):
            resp = self.client.post(post_url, {"opening_amount": "10.00"})
            self.assertRedirects(resp, f"{reverse('login')}?next={post_url}", fetch_redirect_response=False)

    def test_role_matrix_permissions_and_http_methods(self) -> None:
        shift = open_cash_shift(actor=self.seller1, opening_amount=Decimal("40.00"))
        close = close_cash_shift(actor=self.seller1, counted_amount=Decimal("40.00"))

        self.client.force_login(self.warehouse)
        for url in (
            reverse("cash-open"),
            reverse("cash-close"),
            reverse("cash-shift-opened", args=(shift.pk,)),
            reverse("cash-shift-closed", args=(shift.pk,)),
            reverse("cash-shift-history"),
        ):
            self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(reverse("cash-open"), {"opening_amount": "10.00"}).status_code, 403)
        self.assertEqual(self.client.post(reverse("cash-close"), {"counted_amount": "10.00"}).status_code, 403)

        self.client.force_login(self.admin)
        for denied_url in (
            reverse("cash-open"),
            reverse("cash-close"),
            reverse("cash-shift-opened", args=(shift.pk,)),
        ):
            self.assertEqual(self.client.get(denied_url).status_code, 403)
        self.assertEqual(self.client.post(reverse("cash-open"), {"opening_amount": "10.00"}).status_code, 403)
        self.assertEqual(self.client.post(reverse("cash-close"), {"counted_amount": "10.00"}).status_code, 403)

        r_hist = self.client.get(reverse("cash-shift-history"))
        self.assertEqual(r_hist.status_code, 200)
        self._assert_no_store(r_hist)
        r_closed = self.client.get(reverse("cash-shift-closed", args=(close.cash_shift_id,)))
        self.assertEqual(r_closed.status_code, 200)
        self._assert_no_store(r_closed)

        self.client.force_login(self.seller1)
        self.assertEqual(self.client.put(reverse("cash-open")).status_code, 405)
        self.assertEqual(self.client.delete(reverse("cash-close")).status_code, 405)
        self.assertEqual(self.client.post(reverse("cash-shift-opened", args=(shift.pk,))).status_code, 405)
        self.assertEqual(self.client.post(reverse("cash-shift-closed", args=(shift.pk,))).status_code, 405)
        self.assertEqual(self.client.post(reverse("cash-shift-history")).status_code, 405)

    def test_fix09_01_04_05_open_empty_post_boundaries_ascii_and_cache_headers(self) -> None:
        self.client.force_login(self.seller1)

        r_get = self.client.get(reverse("cash-open"))
        self.assertEqual(r_get.status_code, 200)
        self._assert_no_store(r_get)

        r_empty = self.client.post(reverse("cash-open"), {})
        self.assertEqual(r_empty.status_code, 200)
        self.assertTrue(r_empty.context["form"].is_bound)
        self.assertTrue(r_empty.context["form"].errors)
        self.assertFalse(CashShift.objects.exists())

        for invalid in ("١٠", "١٠.٥٠", "1e-3", "1e5", "10000000.00", "NaN", "Infinity", "10,50", "-0.01", "1.005"):
            with self.subTest(invalid=invalid):
                resp = self.client.post(reverse("cash-open"), {"opening_amount": invalid})
                self.assertEqual(resp.status_code, 200)
                self.assertTrue(resp.context["form"].errors)
                self.assertFalse(CashShift.objects.exists())

        r_neg_zero = self.client.post(reverse("cash-open"), {"opening_amount": "-0.00"})
        shift = CashShift.objects.get()
        self.assertRedirects(r_neg_zero, reverse("cash-shift-opened", args=(shift.pk,)))
        self.assertEqual(shift.opening_amount, Decimal("0.00"))
        self.assertFalse(shift.opening_amount.is_signed())

        r_opened = self.client.get(reverse("cash-shift-opened", args=(shift.pk,)))
        self.assertEqual(r_opened.status_code, 200)
        self._assert_no_store(r_opened)
        self.assertContains(r_opened, "CAJA-01 está abierta")
        self.assertContains(r_opened, reverse("sales-draft"))

        close_cash_shift(actor=self.seller1, counted_amount=Decimal("9999999.99"))
        shift2 = open_cash_shift(actor=self.seller2, opening_amount=Decimal("9999999.99"))
        self.assertEqual(shift2.opening_amount, Decimal("9999999.99"))

    def test_fix09_03_service_validation_boundaries_and_stale_actor_checks(self) -> None:
        self.assertRaises(PermissionDenied, open_cash_shift, actor=None, opening_amount=Decimal("10.00"))
        self.assertRaises(PermissionDenied, open_cash_shift, actor=self.admin, opening_amount=Decimal("10.00"))
        self.assertRaises(PermissionDenied, close_cash_shift, actor=None, counted_amount=Decimal("10.00"))
        self.assertRaises(PermissionDenied, close_cash_shift, actor=self.warehouse, counted_amount=Decimal("10.00"))

        stale_inactive = Account.objects.get(pk=self.seller1.pk)
        Account.objects.filter(pk=self.seller1.pk).update(is_active=False)
        try:
            with self.assertRaises(PermissionDenied):
                open_cash_shift(actor=stale_inactive, opening_amount=Decimal("10.00"))
        finally:
            Account.objects.filter(pk=self.seller1.pk).update(is_active=True)

        shift = open_cash_shift(actor=self.seller1, opening_amount=Decimal("50"))
        self.assertEqual(shift.opening_amount, Decimal("50.00"))

        stale_demoted = Account.objects.get(pk=self.seller1.pk)
        Account.objects.filter(pk=self.seller1.pk).update(role=self.warehouse_role)
        try:
            with self.assertRaises(PermissionDenied):
                close_cash_shift(actor=stale_demoted, counted_amount=Decimal("50.00"))
        finally:
            Account.objects.filter(pk=self.seller1.pk).update(role=self.seller_role)

        Account.objects.filter(pk=self.seller1.pk).update(is_active=False)
        try:
            with self.assertRaises(PermissionDenied):
                close_cash_shift(actor=stale_inactive, counted_amount=Decimal("50.00"))
        finally:
            Account.objects.filter(pk=self.seller1.pk).update(is_active=True)

        for bad_val in (
            Decimal("-0.01"),
            Decimal("1.005"),
            Decimal("1e-3"),
            Decimal("1000000000000.00"),
            Decimal("NaN"),
            Decimal("Infinity"),
            Decimal("-Infinity"),
            True,
            False,
            10,
            10.5,
            "10.00",
            None,
        ):
            with self.subTest(bad_val=repr(bad_val)):
                with self.assertRaises(ValidationError):
                    close_cash_shift(actor=self.seller1, counted_amount=bad_val)

        close = close_cash_shift(actor=self.seller1, counted_amount=Decimal("-0.00"))
        self.assertEqual(close.counted_amount, Decimal("0.00"))
        self.assertFalse(close.counted_amount.is_signed())
        self.assertEqual(close.difference, Decimal("-50.00"))

        self.cash_register.is_active = False
        self.cash_register.save(update_fields=["is_active"])
        try:
            with self.assertRaises(ValidationError):
                open_cash_shift(actor=self.seller1, opening_amount=Decimal("10.00"))
        finally:
            self.cash_register.is_active = True
            self.cash_register.save(update_fields=["is_active"])

    def test_fix09_01_02_close_empty_post_no_open_shift_and_retry_show_visible_errors(self) -> None:
        self.client.force_login(self.seller1)

        r_no_shift = self.client.post(reverse("cash-close"), {"counted_amount": "50.00"})
        self.assertEqual(r_no_shift.status_code, 200)
        self._assert_no_store(r_no_shift)
        self.assertContains(r_no_shift, "No tienes un turno de caja abierto para cerrar.")
        self.assertContains(r_no_shift, "alert alert-error")
        self.assertContains(r_no_shift, "No tienes un turno abierto")

        open_cash_shift(actor=self.seller1, opening_amount=Decimal("50.00"))

        r_empty = self.client.post(reverse("cash-close"), {})
        self.assertEqual(r_empty.status_code, 200)
        self.assertTrue(r_empty.context["form"].is_bound)
        self.assertTrue(r_empty.context["form"].errors)
        self.assertEqual(CashShiftClose.objects.count(), 0)

        for invalid in ("١٠", "1e-3", "1e5", "1000000000000.00", "NaN", "10,50", "-0.01", "1.005"):
            with self.subTest(invalid=invalid):
                resp = self.client.post(reverse("cash-close"), {"counted_amount": invalid})
                self.assertEqual(resp.status_code, 200)
                self.assertTrue(resp.context["form"].errors)
                self.assertEqual(CashShiftClose.objects.count(), 0)

        r1 = self.client.post(reverse("cash-close"), {"counted_amount": "50.00"})
        self.assertEqual(r1.status_code, 302)
        self.assertEqual(CashShiftClose.objects.count(), 1)

        r_retry = self.client.post(reverse("cash-close"), {"counted_amount": "50.00"})
        self.assertEqual(r_retry.status_code, 200)
        self.assertContains(r_retry, "No tienes un turno de caja abierto para cerrar.")
        self.assertContains(r_retry, "alert alert-error")
        self.assertEqual(CashShiftClose.objects.count(), 1)

    def test_fix09_01_draft_with_and_without_lines_vs_cash_close(self) -> None:
        shift = open_cash_shift(actor=self.seller1, opening_amount=Decimal("100.00"))
        self.client.force_login(self.seller1)

        self.assertEqual(self.client.get(reverse("cash-shift-closed", args=(shift.pk,))).status_code, 404)

        empty_draft = SaleDraft.objects.create(cash_shift=shift, seller=self.seller1)
        r_empty_draft = self.client.get(reverse("cash-close"))
        self.assertEqual(r_empty_draft.status_code, 200)
        self.assertFalse(r_empty_draft.context["has_active_draft"])
        self.assertNotContains(r_empty_draft, "Tienes una venta en preparación activa")
        empty_draft.delete()

        draft = add_product_to_draft(actor=self.seller1, product_id=self.product.pk, quantity=2)
        r_warn = self.client.get(reverse("cash-close"))
        self.assertTrue(r_warn.context["has_active_draft"])
        self.assertContains(r_warn, "Tienes una venta en preparación activa")
        self.assertContains(r_warn, reverse("sales-draft"))

        r_blocked = self.client.post(reverse("cash-close"), {"counted_amount": "100.00"})
        self.assertEqual(r_blocked.status_code, 200)
        self.assertContains(r_blocked, "Hay una venta en preparación con productos")
        self.assertContains(r_blocked, "Ir a la venta en preparación para cobrarla o descartarla")
        self.assertEqual(CashShiftClose.objects.count(), 0)

        line = draft.lines.get()
        remove_draft_line(actor=self.seller1, line_id=line.pk)
        r_after_remove = self.client.get(reverse("cash-close"))
        self.assertFalse(r_after_remove.context["has_active_draft"])

        add_product_to_draft(actor=self.seller1, product_id=self.product.pk, quantity=2)
        self.assertTrue(discard_active_draft(actor=self.seller1))
        self.assertFalse(self.client.get(reverse("cash-close")).context["has_active_draft"])

        draft2 = add_product_to_draft(actor=self.seller1, product_id=self.product.pk, quantity=2)
        sale = checkout_sale(
            actor=self.seller1,
            draft_id=draft2.pk,
            cash_received=Decimal("20.00"),
            idempotency_key=uuid.uuid4(),
        )
        self.assertEqual(sale.total_amount, Decimal("11.00"))
        self.assertEqual(sale.change_given, Decimal("9.00"))

        r_shortage = self.client.post(reverse("cash-close"), {"counted_amount": "105.00"})
        self.assertRedirects(r_shortage, reverse("cash-shift-closed", args=(shift.pk,)))

        close = CashShiftClose.objects.get(cash_shift=shift)
        self.assertEqual(close.expected_amount, Decimal("111.00"))
        self.assertEqual(close.counted_amount, Decimal("105.00"))
        self.assertEqual(close.difference, Decimal("-6.00"))

        r_acta = self.client.get(reverse("cash-shift-closed", args=(shift.pk,)))
        self.assertEqual(r_acta.status_code, 200)
        self._assert_no_store(r_acta)
        self.assertContains(r_acta, "success-panel")
        self.assertContains(r_acta, "mt-3")
        self.assertContains(r_acta, "status-error")
        self.assertContains(r_acta, "Faltante")
        self.assertContains(r_acta, "-6,00")

        r_opened_closed = self.client.get(reverse("cash-shift-opened", args=(shift.pk,)))
        self.assertEqual(r_opened_closed.status_code, 200)
        self.assertNotContains(r_opened_closed, "CAJA-01 está abierta")
        self.assertNotContains(r_opened_closed, "Ir a preparar venta")
        self.assertContains(r_opened_closed, "Cerrado")
        self.assertContains(r_opened_closed, reverse("cash-shift-closed", args=(shift.pk,)))

        self.client.force_login(self.seller2)
        self.assertEqual(self.client.get(reverse("cash-shift-closed", args=(shift.pk,))).status_code, 404)

    def test_shift_history_isolation_styles_and_constant_query_count(self) -> None:
        s1_a = open_cash_shift(actor=self.seller1, opening_amount=Decimal("100.00"))
        close_cash_shift(actor=self.seller1, counted_amount=Decimal("95.00"))

        s2_a = open_cash_shift(actor=self.seller2, opening_amount=Decimal("80.00"))
        close_cash_shift(actor=self.seller2, counted_amount=Decimal("85.00"))

        s1_b = open_cash_shift(actor=self.seller1, opening_amount=Decimal("50.00"))

        self.client.force_login(self.seller1)
        r_seller = self.client.get(reverse("cash-shift-history"))
        self.assertEqual(r_seller.status_code, 200)
        self._assert_no_store(r_seller)
        self.assertContains(r_seller, "cash-history-table")
        self.assertContains(r_seller, reverse("dashboard"))
        self.assertContains(r_seller, "Faltante")
        self.assertContains(r_seller, "Abierto")
        self.assertNotContains(r_seller, self.seller2.display_name)
        self.assertEqual(list(r_seller.context["shifts"]), [s1_b, s1_a])

        self.client.force_login(self.admin)
        with self.assertNumQueries(4):
            # session + account + role + 1 JOIN query for CashShift/CashRegister/Account/CashShiftClose
            r_admin = self.client.get(reverse("cash-shift-history"))
        self.assertEqual(r_admin.status_code, 200)
        self.assertContains(r_admin, self.seller1.display_name)
        self.assertContains(r_admin, self.seller2.display_name)
        self.assertContains(r_admin, "Sobrante")
        self.assertEqual(list(r_admin.context["shifts"]), [s1_b, s2_a, s1_a])

        r_dash = self.client.get(reverse("dashboard"))
        self.assertEqual(r_dash.context["summary"]["open_shifts"], 1)

        close_cash_shift(actor=self.seller1, counted_amount=Decimal("50.00"))
        r_dash_after = self.client.get(reverse("dashboard"))
        self.assertEqual(r_dash_after.context["summary"]["open_shifts"], 0)

        for idx in range(5):
            open_cash_shift(actor=self.seller2, opening_amount=Decimal("20.00") + idx)
            close_cash_shift(actor=self.seller2, counted_amount=Decimal("20.00") + idx)
        with self.assertNumQueries(4):
            self.client.get(reverse("cash-shift-history"))

    def test_logout_discards_draft_and_preserves_open_shift(self) -> None:
        shift = open_cash_shift(actor=self.seller1, opening_amount=Decimal("75.00"))
        add_product_to_draft(actor=self.seller1, product_id=self.product.pk, quantity=1)
        self.client.force_login(self.seller1)

        r_logout_get = self.client.get(reverse("logout"))
        self.assertEqual(r_logout_get.status_code, 200)
        self.assertTrue(r_logout_get.context["has_active_draft"])

        r_logout_post = self.client.post(reverse("logout"))
        self.assertRedirects(r_logout_post, reverse("login"))

        shift.refresh_from_db()
        self.assertEqual(shift.status, CashShift.Status.OPEN)
        self.assertFalse(SaleDraft.objects.filter(seller=self.seller1, status=SaleDraft.Status.ACTIVE).exists())

        self.client.force_login(self.seller2)
        r_other = self.client.get(reverse("cash-open"))
        self.assertContains(r_other, self.seller1.display_name)
        r_other_post = self.client.post(reverse("cash-open"), {"opening_amount": "15.00"})
        self.assertContains(r_other_post, "Ya existe un turno abierto")

        self.client.force_login(self.seller1)
        r_relogin = self.client.get(reverse("cash-open"))
        self.assertContains(r_relogin, "Ya abriste CAJA-01")
        close_cash_shift(actor=self.seller1, counted_amount=Decimal("75.00"))

        self.client.force_login(self.seller2)
        r_now_open = self.client.post(reverse("cash-open"), {"opening_amount": "15.00"})
        self.assertEqual(r_now_open.status_code, 302)
