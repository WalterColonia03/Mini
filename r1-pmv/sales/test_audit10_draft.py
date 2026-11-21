"""Stage 10 audit regressions: sale draft preparation, stock bounds, search hygiene,
strict ASCII quantities, two-tab/staleness warnings, actor locks, and explicit HU-VEN-01a/04 checks.
"""
from __future__ import annotations

import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from cash.models import CashRegister, CashShift
from cash.services import close_cash_shift, open_cash_shift
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot
from sales.models import SaleDraft, SaleDraftLine
from sales.services import (
    add_product_to_draft,
    discard_active_draft,
    draft_totals,
    remove_draft_line,
    sellable_stock_for_product,
    update_draft_line,
)


class Stage10SaleDraftAuditTests(TestCase):
    password = "Audit10-Strong!Pass"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
        cls.wh_role, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
        cls.sel_role, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

        cls.admin = Account.objects.create_user(
            "admin.a10@test.invalid", cls.password, display_name="Admin A10", role=cls.admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "wh.a10@test.invalid", cls.password, display_name="Almacén A10", role=cls.wh_role
        )
        cls.seller = Account.objects.create_user(
            "seller.a10@test.invalid", cls.password, display_name="Vendedor A10", role=cls.sel_role
        )
        cls.other_seller = Account.objects.create_user(
            "seller2.a10@test.invalid", cls.password, display_name="Vendedor2 A10", role=cls.sel_role
        )
        cls.cash_register = CashRegister.objects.create(code="CAJA-01")
        cls.cat_active = Category.objects.create(name="Conservas y Granos A10")
        cls.cat_inactive = Category.objects.create(name="Suspendida A10", is_active=False)

        today = timezone.localdate()

        # Multi-GTIN + mixed expired/today/vigente lots -> sellable = 6 (4 + 2), physical = 19 (5 expired + 8 today + 6 vigente)
        cls.prod_gtin = Product.objects.create(
            category=cls.cat_active,
            name="Atún en Lata GTIN A10",
            barcode="0775000000014",
            barcode_type=Product.BarcodeType.GTIN,
            sale_price=Decimal("5.90"),
            minimum_stock=2,
        )
        load_gtin = InitialInventoryLoad.objects.create(product=cls.prod_gtin, responsible=cls.warehouse)
        Lot.objects.create(
            product=cls.prod_gtin, initial_load=load_gtin, number="EXP-PAST",
            initial_quantity=5, available_quantity=5, unit_cost=Decimal("2.00"),
            expiration_date=today - timedelta(days=1),
        )
        Lot.objects.create(
            product=cls.prod_gtin, initial_load=load_gtin, number="EXP-TODAY",
            initial_quantity=8, available_quantity=8, unit_cost=Decimal("2.00"),
            expiration_date=today,
        )
        Lot.objects.create(
            product=cls.prod_gtin, initial_load=load_gtin, number="VIG-01",
            initial_quantity=4, available_quantity=4, unit_cost=Decimal("2.00"),
            expiration_date=today + timedelta(days=5),
        )
        Lot.objects.create(
            product=cls.prod_gtin, initial_load=load_gtin, number="VIG-02",
            initial_quantity=2, available_quantity=2, unit_cost=Decimal("2.00"),
            expiration_date=today + timedelta(days=30),
        )

        # Product with & in name and leading zero internal code
        cls.prod_amp = Product.objects.create(
            category=cls.cat_active,
            name="Café & Pan A10",
            barcode="00A10-INT",
            barcode_type=Product.BarcodeType.INTERNAL,
            sale_price=Decimal("10.00"),
            minimum_stock=1,
        )
        load_amp = InitialInventoryLoad.objects.create(product=cls.prod_amp, responsible=cls.warehouse)
        Lot.objects.create(
            product=cls.prod_amp, initial_load=load_amp, number="AMP-01",
            initial_quantity=5, available_quantity=5, unit_cost=Decimal("4.00"),
            expiration_date=today + timedelta(days=15),
        )

    def test_anonymous_redirects_and_non_seller_forbidden_on_all_draft_routes(self) -> None:
        line_id = uuid.uuid4()
        routes = [
            ("GET", reverse("sales-draft")),
            ("POST", reverse("sales-draft")),
            ("POST", reverse("sales-line-update", args=(line_id,))),
            ("POST", reverse("sales-line-remove", args=(line_id,))),
            ("POST", reverse("sales-draft-discard")),
        ]
        for method, url in routes:
            resp = getattr(self.client, method.lower())(url)
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp["Location"], f"/?next={url}")

        for actor in (self.admin, self.warehouse):
            self.client.force_login(actor)
            for method, url in routes:
                with self.subTest(role=actor.role.code, method=method, url=url):
                    resp = getattr(self.client, method.lower())(url, {"quantity": "1"})
                    self.assertEqual(resp.status_code, 403)

    def test_search_normalizes_accents_spaces_and_multi_gtin_without_inflating_stock(self) -> None:
        open_cash_shift(actor=self.seller, opening_amount=Decimal("20.00"))
        self.client.force_login(self.seller)

        # Casefold + accents + multi spaces + UPC12/EAN13/GTIN14 keys all return exact sellable_quantity=6
        for q in ("ATÚN   EN   LATA", "0775000000014", "775000000014", "00775000000014"):
            with self.subTest(query=q):
                resp = self.client.get(reverse("sales-draft"), {"query": q})
                self.assertEqual(resp.status_code, 200)
                products = list(resp.context["products"])
                self.assertEqual(len(products), 1)
                self.assertEqual(products[0].pk, self.prod_gtin.pk)
                self.assertEqual(products[0].sellable_quantity, 6)
                self.assertEqual(sellable_stock_for_product(self.prod_gtin), 6)

        # Leading zeroes internal code works verbatim; stripped fails
        self.assertEqual(len(self.client.get(reverse("sales-draft"), {"query": "00A10-INT"}).context["products"]), 1)
        self.assertEqual(len(self.client.get(reverse("sales-draft"), {"query": "A10-INT"}).context["products"]), 0)

    def test_search_errors_and_redirect_encoding_and_empty_or_no_shift_post(self) -> None:
        self.client.force_login(self.seller)

        # POST without open shift renders visible .alert-error with message
        r_no_shift = self.client.post(
            reverse("sales-draft"),
            {"product_id": str(self.prod_gtin.pk), "quantity": "1"},
        )
        self.assertEqual(r_no_shift.status_code, 200)
        self.assertContains(r_no_shift, "alert-error")
        self.assertContains(r_no_shift, "Necesitas un turno de caja abierto a tu nombre para preparar una venta.")
        self.assertFalse(SaleDraft.objects.exists())

        open_cash_shift(actor=self.seller, opening_amount=Decimal("20.00"))

        # Empty POST {} binds form and renders required errors
        r_empty = self.client.post(reverse("sales-draft"), {})
        self.assertEqual(r_empty.status_code, 200)
        self.assertTrue(r_empty.context["add_form"].is_bound)
        self.assertContains(r_empty, "alert-error")

        # NUL byte & >160 chars query render search_form error without 500
        for bad_q in ("atun\x00", "X" * 161):
            r_bad = self.client.get(reverse("sales-draft"), {"query": bad_q})
            self.assertEqual(r_bad.status_code, 200)
            self.assertContains(r_bad, "alert-error")
            self.assertEqual(list(r_bad.context["products"]), [])

        # Special chars `&` in query are preserved in redirect via urlencode
        r_amp = self.client.post(
            f"{reverse('sales-draft')}?query=Caf%C3%A9%20%26%20Pan",
            {"product_id": str(self.prod_amp.pk), "quantity": "1"},
        )
        self.assertRedirects(r_amp, f"{reverse('sales-draft')}?query=Caf%C3%A9+%26+Pan")

    def test_strict_ascii_integer_and_bounds_on_add_and_update_forms_and_services(self) -> None:
        open_cash_shift(actor=self.seller, opening_amount=Decimal("20.00"))
        self.client.force_login(self.seller)

        # Reject non-ASCII digits, leading '+', decimals, scientific notation, zero, negatives, >999999
        for bad_qty in ("٥", "+2", "1.5", "1e2", "0", "-1", "1000000"):
            with self.subTest(add_qty=bad_qty):
                resp = self.client.post(
                    reverse("sales-draft"),
                    {"product_id": str(self.prod_gtin.pk), "quantity": bad_qty},
                )
                self.assertEqual(resp.status_code, 200)
                self.assertContains(resp, "alert-error")
                self.assertFalse(SaleDraft.objects.exists())

        # Service-level validation rejects bool, float, <=0, >999999
        for svc_qty in (True, False, 1.5, 0, -3, 1000000):
            with self.subTest(service_qty=svc_qty):
                with self.assertRaises(ValidationError):
                    add_product_to_draft(actor=self.seller, product_id=self.prod_gtin.pk, quantity=svc_qty)

        # Add valid line, then verify UpdateDraftLineForm rejects invalid quantities without mutating line
        draft = add_product_to_draft(actor=self.seller, product_id=self.prod_gtin.pk, quantity=2)
        line = draft.lines.get()
        for bad_qty in ("٥", "+3", "2.5", "0", "-2", "1000000"):
            with self.subTest(update_qty=bad_qty):
                resp = self.client.post(
                    reverse("sales-line-update", args=(line.pk,)),
                    {"quantity": bad_qty},
                    follow=True,
                )
                self.assertEqual(resp.status_code, 200)
                self.assertContains(resp, "alert-error")
                line.refresh_from_db()
                self.assertEqual(line.quantity, 2)

        with self.assertRaises(ValidationError):
            update_draft_line(actor=self.seller, line_id=line.pk, quantity=1000000)

    def test_manual_discard_and_close_shift_lock_behavior(self) -> None:
        shift = open_cash_shift(actor=self.seller, opening_amount=Decimal("50.00"))
        self.client.force_login(self.seller)
        add_product_to_draft(actor=self.seller, product_id=self.prod_gtin.pk, quantity=3)
        add_product_to_draft(actor=self.seller, product_id=self.prod_amp.pk, quantity=2)
        before_lots = list(Lot.objects.order_by("id").values_list("id", "available_quantity"))

        # RN-30: open draft with lines blocks cash shift close
        with self.assertRaises(ValidationError):
            close_cash_shift(actor=self.seller, counted_amount=Decimal("50.00"))

        # Manual discard deletes lines, discards draft, leaves stock/cash intact, unblocks close
        resp = self.client.post(reverse("sales-draft-discard"), follow=True)
        self.assertContains(resp, "La venta en preparación fue descartada.")
        draft = SaleDraft.objects.get()
        self.assertEqual(draft.status, SaleDraft.Status.DISCARDED)
        self.assertIsNotNone(draft.discarded_at)
        self.assertFalse(SaleDraftLine.objects.exists())
        self.assertEqual(list(Lot.objects.order_by("id").values_list("id", "available_quantity")), before_lots)

        close = close_cash_shift(actor=self.seller, counted_amount=Decimal("50.00"))
        shift.refresh_from_db()
        self.assertEqual(shift.status, CashShift.Status.CLOSED)
        self.assertEqual(close.expected_amount, Decimal("50.00"))

    def test_inactive_seller_denied_on_draft_services_and_atomic_draft_totals(self) -> None:
        shift = open_cash_shift(actor=self.seller, opening_amount=Decimal("30.00"))
        add_product_to_draft(actor=self.seller, product_id=self.prod_gtin.pk, quantity=2)
        draft = SaleDraft.objects.get(cash_shift=shift, status=SaleDraft.Status.ACTIVE)
        totals = draft_totals(draft)
        self.assertEqual(totals.total, Decimal("11.80"))
        self.assertEqual(totals.base, Decimal("10.00"))
        self.assertEqual(totals.igv, Decimal("1.80"))

        # Deactivating seller row denies all draft service operations cleanly
        self.seller.is_active = False
        self.seller.save(update_fields=["is_active"])
        line = draft.lines.get()
        for fn in (
            lambda: add_product_to_draft(actor=self.seller, product_id=self.prod_amp.pk, quantity=1),
            lambda: update_draft_line(actor=self.seller, line_id=line.pk, quantity=1),
            lambda: remove_draft_line(actor=self.seller, line_id=line.pk),
            lambda: discard_active_draft(actor=self.seller),
        ):
            with self.assertRaises(PermissionDenied):
                fn()

    def test_explicit_absence_of_hu_ven_01a_inactivity_screen_lock_and_hu_ven_04_gaps(self) -> None:
        """Evidence check: verify code reality honestly (no 5-min screen lock; /ventas/ hides lookup without shift)."""
        self.client.force_login(self.seller)

        # HU-VEN-04: without open shift, lookup form is not rendered and 'Producto no encontrado' does not exist
        no_shift_html = self.client.get(reverse("sales-draft"), {"query": self.prod_gtin.barcode}).content.decode()
        self.assertNotIn('name="query"', no_shift_html)
        self.assertNotIn("Producto no encontrado", no_shift_html)

        open_cash_shift(actor=self.seller, opening_amount=Decimal("20.00"))
        add_product_to_draft(actor=self.seller, product_id=self.prod_gtin.pk, quantity=1)

        # HU-VEN-01a / RN-22: after > 5 minutes of inactivity, /ventas/ still responds 200 without screen lock
        self.assertEqual(settings.SESSION_COOKIE_AGE, 1209600)
        with patch("django.utils.timezone.now", return_value=timezone.now() + timedelta(minutes=10)):
            resp = self.client.get(reverse("sales-draft"))
            self.assertEqual(resp.status_code, 200)
            html = resp.content.decode()
            self.assertIn("Venta en preparación", html)
            self.assertNotIn("reingresar mi contraseña", html.lower())

        missing_html = self.client.get(reverse("sales-draft"), {"query": "9999999999999"}).content.decode()
        self.assertIn("No se encontraron productos con existencias vendibles.", missing_html)
        self.assertNotIn("Producto no encontrado", missing_html)
