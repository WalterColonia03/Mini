from __future__ import annotations

from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from identity.models import Account, Role

from .models import CashRegister, CashShift


class CashOpeningTests(TestCase):
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

    def test_seller_opens_zero_amount_shift_linked_to_session(self) -> None:
        self.client.force_login(self.seller)

        response = self.client.post(reverse("cash-open"), {"opening_amount": "0.00"})

        shift = CashShift.objects.get()
        self.assertRedirects(response, reverse("cash-shift-opened", args=(shift.pk,)))
        self.assertEqual(shift.seller, self.seller)
        self.assertEqual(shift.cash_register, self.cash_register)
        self.assertEqual(shift.opening_amount, Decimal("0.00"))
        self.assertEqual(shift.status, CashShift.Status.OPEN)
        self.assertTrue(timezone.is_aware(shift.opened_at))

    def test_invalid_amounts_do_not_create_shift(self) -> None:
        self.client.force_login(self.seller)
        for amount in ("", "-0.01", "1.001", "texto"):
            with self.subTest(amount=amount):
                response = self.client.post(reverse("cash-open"), {"opening_amount": amount})
                self.assertEqual(response.status_code, 200)
                self.assertFalse(CashShift.objects.exists())

    def test_other_roles_cannot_open_shift_by_direct_post(self) -> None:
        for account in (self.admin, self.warehouse):
            with self.subTest(role=account.role.code):
                self.client.force_login(account)
                response = self.client.post(reverse("cash-open"), {"opening_amount": "25.00"})
                self.assertEqual(response.status_code, 403)
                self.assertFalse(CashShift.objects.exists())

    def test_existing_global_open_shift_blocks_another_seller(self) -> None:
        CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("10.00"),
        )
        self.client.force_login(self.other_seller)

        response = self.client.post(reverse("cash-open"), {"opening_amount": "20.00"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe un turno abierto")
        self.assertEqual(CashShift.objects.count(), 1)

    def test_database_constraint_rejects_two_open_shifts_for_register(self) -> None:
        CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("10.00"),
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            CashShift.objects.create(
                cash_register=self.cash_register,
                seller=self.other_seller,
                opening_amount=Decimal("20.00"),
            )

    def test_seller_cannot_view_another_sellers_shift_detail(self) -> None:
        shift = CashShift.objects.create(
            cash_register=self.cash_register,
            seller=self.seller,
            opening_amount=Decimal("10.00"),
        )
        self.client.force_login(self.other_seller)
        response = self.client.get(reverse("cash-shift-opened", args=(shift.pk,)))
        self.assertEqual(response.status_code, 404)


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 2 — HU-CAJA-05
# ═══════════════════════════════════════════════════════════════════════════════

class CashShiftHistoryTests(TestCase):
    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        from decimal import Decimal
        admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador H")
        seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor H")
        cls.admin = Account.objects.create_user(
            "adminch@test.invalid", cls.password, display_name="Admin CH", role=admin_role
        )
        cls.seller = Account.objects.create_user(
            "sellerch@test.invalid", cls.password, display_name="Seller CH", role=seller_role
        )
        warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero H")
        cls.warehouse = Account.objects.create_user(
            "whch@test.invalid", cls.password, display_name="WH CH", role=warehouse_role
        )

    def test_seller_can_see_shift_history(self) -> None:
        self.client.force_login(self.seller)
        response = self.client.get(reverse("cash-shift-history"))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_see_shift_history(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("cash-shift-history"))
        self.assertEqual(response.status_code, 200)

    def test_warehouse_gets_403(self) -> None:
        self.client.force_login(self.warehouse)
        self.assertEqual(self.client.get(reverse("cash-shift-history")).status_code, 403)

    def test_shift_history_renders_shortage_surplus_and_exact_labels_and_amounts(self) -> None:
        """BUG-002: El historial de turnos muestra el monto y la etiqueta de la diferencia (Faltante/Sobrante/Exacto)."""
        from .models import CashShiftClose

        reg = CashRegister.objects.create(code="CAJA-HIST-DIFF")
        shift = CashShift.objects.create(
            cash_register=reg,
            seller=self.seller,
            opening_amount=Decimal("100.00"),
            status=CashShift.Status.CLOSED,
        )
        CashShiftClose.objects.create(
            cash_shift=shift,
            counted_amount=Decimal("95.00"),
            expected_amount=Decimal("100.00"),
            difference=Decimal("-5.00"),
            closed_by=self.seller,
        )
        self.client.force_login(self.admin)
        response = self.client.get(reverse("cash-shift-history"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "-5,00")
        self.assertContains(response, "Faltante")

    def test_cash_open_and_close_reject_scientific_notation_and_absurd_amounts(self) -> None:
        """BUG-009: Apertura y cierre de caja rechazan notación científica (1e5) y montos desmesurados."""
        reg = CashRegister.objects.create(code="CAJA-LIM-01")
        self.client.force_login(self.seller)
        for bad in ("1e5", "99999999999.99"):
            with self.subTest(opening=bad):
                r_open = self.client.post(reverse("cash-open"), {"opening_amount": bad})
                self.assertEqual(r_open.status_code, 200)
                self.assertFalse(CashShift.objects.filter(cash_register=reg).exists())

        shift = CashShift.objects.create(
            cash_register=reg, seller=self.seller, opening_amount=Decimal("50.00")
        )
        for bad in ("1e5", "1000000000000.00"):
            with self.subTest(counted=bad):
                r_close = self.client.post(reverse("cash-close"), {"counted_amount": bad})
                self.assertEqual(r_close.status_code, 200)
                shift.refresh_from_db()
                self.assertEqual(shift.status, CashShift.Status.OPEN)

    def test_bug023_and_bug031_cash_open_shows_owner_and_shift_opened_has_sales_draft_link(self) -> None:
        """BUG-023 y BUG-031: /caja/abrir/ informa quién ocupa la caja y /caja/turnos/<id>/abierto/ enlaza a preparar venta."""
        reg = CashRegister.objects.create(code="CAJA-BUG31")
        shift = CashShift.objects.create(
            cash_register=reg, seller=self.seller, opening_amount=Decimal("50.00")
        )
        self.client.force_login(self.seller)
        opened_resp = self.client.get(reverse("cash-shift-opened", args=(shift.pk,)))
        self.assertEqual(opened_resp.status_code, 200)
        self.assertContains(opened_resp, reverse("sales-draft"))

        seller2 = Account.objects.create_user(
            email="seller2.bug31@example.com",
            password="StrongPassword!123",
            display_name="Marcos Cajero",
            role=Role.objects.get(code=Role.Code.SELLER),
        )
        self.client.force_login(seller2)
        busy_resp = self.client.get(reverse("cash-open"))
        self.assertEqual(busy_resp.status_code, 200)
        self.assertContains(busy_resp, self.seller.display_name)
