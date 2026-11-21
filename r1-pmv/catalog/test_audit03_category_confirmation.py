from datetime import timedelta
from decimal import Decimal
import uuid

from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from cash.models import CashRegister, CashShift
from cash.services import open_cash_shift
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot
from inventory.services import LotInput, confirm_initial_load
from sales.models import Sale, SaleLine, SaleDraft, SaleDraftLine
from sales.services import add_product_to_draft, checkout_sale
from .models import Category, Product
from .services import toggle_category_status


class CategoryConfirmationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.actors = {}
        for alias, code in [("admin", "ADMIN"), ("admin2", "ADMIN"), ("warehouse", "ALMACENERO"), ("seller", "VENDEDOR")]:
            role, _ = Role.objects.get_or_create(code=code, defaults={"name": code})
            cls.actors[alias] = Account.objects.create_user(alias + "@confirm.invalid", None, role=role, display_name=alias)
        cls.category = Category.objects.create(name="Grupo de prueba")
        cls.product = Product.objects.create(category=cls.category, name="Producto con lotes", barcode="CONF-1", sale_price=Decimal("8.50"))
        confirm_initial_load(actor=cls.actors["warehouse"], product=cls.product,
                             lots=[LotInput("CONF-LOT", 20, Decimal("5"), timezone.localdate() + timedelta(days=30))])
        CashRegister.objects.create(code="CAJA-01")
        open_cash_shift(actor=cls.actors["seller"], opening_amount=Decimal("50"))
        draft = add_product_to_draft(actor=cls.actors["seller"], product_id=cls.product.pk, quantity=1)
        checkout_sale(actor=cls.actors["seller"], draft_id=draft.pk, cash_received=Decimal("10"), idempotency_key=uuid.uuid4())
        add_product_to_draft(actor=cls.actors["seller"], product_id=cls.product.pk, quantity=2)

    def setUp(self):
        self.client.force_login(self.actors["admin"])
        self.confirm = reverse("category-state-confirm", args=[self.category.pk])
        self.commit = reverse("category-toggle", args=[self.category.pk])

    def business(self):
        return {m._meta.label: list(m.objects.order_by("pk").values()) for m in
                [Product, Lot, InitialInventoryLoad, Sale, SaleLine, SaleDraft, SaleDraftLine, CashShift]}

    def payload(self, target="false", version=None):
        self.category.refresh_from_db()
        return {"is_active": target, "state_version": str(self.category.state_version if version is None else version), "confirm": "yes"}

    def test_confirmation_get_explains_real_impact_without_writes_and_cancel_is_readonly(self):
        before = self.business()
        response = self.client.get(self.confirm, {"is_active": "false", "state_version": "0"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual((response.context["product_count"], response.context["draft_count"], response.context["physical_units"]), (1, 1, 19))
        self.assertContains(response, "Confirmar desactivación")
        self.assertContains(response, "Las ventas confirmadas conservarán sus datos")
        self.assertIn("no-store", response.headers["Cache-Control"])
        self.client.get(reverse("category-list"))  # Cancel destination.
        self.category.refresh_from_db()
        self.assertTrue(self.category.is_active)
        self.assertEqual(self.category.state_version, 0)
        self.assertEqual(self.business(), before)

    def test_commit_changes_only_category_state_and_version(self):
        before = self.business()
        response = self.client.post(self.commit, self.payload())
        self.assertRedirects(response, reverse("category-list"))
        self.category.refresh_from_db()
        self.assertEqual((self.category.is_active, self.category.state_version), (False, 1))
        self.assertEqual(self.business(), before)
        activation = self.client.get(self.confirm)
        self.assertContains(activation, "Confirmar activación")
        self.assertContains(activation, "Los productos deshabilitados individualmente seguirán deshabilitados")

    def test_replayed_confirmation_is_rejected_without_another_change(self):
        payload = self.payload()
        self.client.post(self.commit, payload)
        before = self.business()
        response = self.client.post(self.commit, payload)
        self.assertContains(response, "La categoría cambió", status_code=409)
        self.assertNotContains(response, 'name="confirm"', status_code=409)
        self.category.refresh_from_db()
        self.assertEqual((self.category.is_active, self.category.state_version), (False, 1))
        self.assertEqual(self.business(), before)

    def test_old_screen_rejected_after_two_changes_even_when_boolean_matches_again(self):
        stale = self.payload()
        toggle_category_status(actor=self.actors["admin2"], category=self.category, is_active=False, expected_version=0)
        toggle_category_status(actor=self.actors["admin2"], category=self.category, is_active=True, expected_version=1)
        before = self.business()
        self.assertEqual(self.client.post(self.commit, stale).status_code, 409)
        self.assertEqual(self.client.get(self.confirm, stale).status_code, 409)
        self.category.refresh_from_db()
        self.assertEqual((self.category.is_active, self.category.state_version), (True, 2))
        self.assertEqual(self.business(), before)

    def test_missing_confirmation_version_and_invalid_inputs_never_mutate(self):
        good = self.payload()
        variants = [{}, {"is_active": "false"}, {**good, "confirm": "no"}, {**good, "is_active": "2"}]
        variants += [{**good, "state_version": v} for v in ["", "-1", "0.5", "NaN", "1e3", "９", "9223372036854775808"]]
        before = self.business()
        for data in variants:
            with self.subTest(data=data):
                self.assertEqual(self.client.post(self.commit, data).status_code, 400)
        self.category.refresh_from_db()
        self.assertEqual((self.category.is_active, self.category.state_version), (True, 0))
        self.assertEqual(self.business(), before)

    def test_service_checks_version_and_does_not_advance_on_noop(self):
        toggle_category_status(actor=self.actors["admin"], category=self.category, is_active=True, expected_version=0)
        self.assertEqual(self.category.state_version, 0)
        for invalid in [-1, True, "0"]:
            with self.subTest(version=invalid), self.assertRaises(ValidationError):
                toggle_category_status(actor=self.actors["admin"], category=self.category, is_active=False, expected_version=invalid)
        toggle_category_status(actor=self.actors["admin2"], category=self.category, is_active=False, expected_version=0)
        with self.assertRaises(ValidationError) as error:
            toggle_category_status(actor=self.actors["admin"], category=self.category, is_active=True, expected_version=0)
        self.assertEqual(error.exception.code, "stale_category")

    def test_roles_methods_csrf_and_missing_uuid(self):
        before = self.business()
        for alias in ["warehouse", "seller", None]:
            client = Client()
            if alias:
                client.force_login(self.actors[alias])
            self.assertEqual(client.get(self.confirm).status_code, 403 if alias else 302)
            self.assertEqual(client.post(self.commit, self.payload()).status_code, 403 if alias else 302)
        self.assertEqual(self.client.post(self.confirm, self.payload()).status_code, 405)
        self.assertEqual(self.client.get(self.commit).status_code, 405)
        self.assertEqual(self.client.get(reverse("category-state-confirm", args=[uuid.uuid4()])).status_code, 404)
        csrf = Client(enforce_csrf_checks=True)
        csrf.force_login(self.actors["admin"])
        self.assertEqual(csrf.post(self.commit, self.payload()).status_code, 403)
        self.assertEqual(self.business(), before)
