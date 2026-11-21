"""CP-HU-AUTH-01-003: role gates with existing business data, local demo."""
from datetime import timedelta
from decimal import Decimal
import uuid

from django.apps import apps
from django.conf import settings
from django.contrib.auth import SESSION_KEY
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from cash.forms import CashOpeningForm
from cash.models import CashRegister, CashShift
from catalog.forms import ProductRegistrationForm
from catalog.models import Category, Product
from inventory.models import InitialInventoryLoad, Lot
from sales.forms import CheckoutForm
from sales.models import Sale, SaleCounter, SaleDraft, SaleDraftLine, SaleLine, SaleLotAllocation

from .models import Account, Role


class AcademicRoleGateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.password = "FicticiaLocal01K!"
        cls.accounts = {}
        for code, label in Role.Code.choices:
            role = Role.objects.create(code=code, name=label)
            cls.accounts[code] = Account.objects.create_user(
                f"{code.lower()}.01k@pruebas.invalid", cls.password,
                role=role, display_name=f"Persona ficticia {label}",
            )
        cls.category = Category.objects.create(name="Categoría protegida 01K")
        cls.product = Product.objects.create(
            name="Producto protegido 01K", barcode="AUD01K-PROTEGIDO",
            barcode_type=Product.BarcodeType.INTERNAL, category=cls.category,
            sale_price=Decimal("10.00"), average_cost=Decimal("2.0000"),
        )
        cls.load = InitialInventoryLoad.objects.create(
            product=cls.product, responsible=cls.accounts[Role.Code.WAREHOUSE],
        )
        cls.lot = Lot.objects.create(
            product=cls.product, initial_load=cls.load, number="LOTE-PROTEGIDO-01K",
            initial_quantity=10, available_quantity=9, unit_cost=Decimal("2.0000"),
            expiration_date=timezone.localdate()+timedelta(days=100),
        )
        cls.register = CashRegister.objects.create(code="CAJA-PROTEGIDA-01K")
        cls.shift = CashShift.objects.create(
            cash_register=cls.register, seller=cls.accounts[Role.Code.SELLER],
            opening_amount=Decimal("100.00"),
        )
        cls.draft = SaleDraft.objects.create(
            cash_shift=cls.shift, seller=cls.accounts[Role.Code.SELLER],
        )
        cls.draft_line = SaleDraftLine.objects.create(
            draft=cls.draft, product=cls.product, quantity=1, unit_price=Decimal("10.00"),
        )
        cls.sale = Sale.objects.create(
            cash_shift=cls.shift, seller=cls.accounts[Role.Code.SELLER],
            seller_snapshot_name="Vendedor de constancia protegido 01K",
            cash_register_snapshot_code=cls.register.code,
            total_amount=Decimal("10.00"), base_amount=Decimal("8.47"),
            igv_amount=Decimal("1.53"), cash_received=Decimal("20.00"),
            change_given=Decimal("10.00"), correlative="V-00000117",
            idempotency_key=uuid.uuid4(),
        )
        cls.sale_line = SaleLine.objects.create(
            sale=cls.sale, position=1, product=cls.product,
            product_snapshot_name=cls.product.name,
            product_snapshot_barcode=cls.product.barcode,
            quantity=1, unit_price=Decimal("10.00"), amount=Decimal("10.00"),
            unit_cost=Decimal("2.0000"),
        )
        SaleLotAllocation.objects.create(
            line=cls.sale_line, lot=cls.lot, quantity=1,
            lot_snapshot_number=cls.lot.number,
            lot_snapshot_expiration_date=cls.lot.expiration_date,
            lot_snapshot_received_at=cls.lot.received_at,
        )
        SaleCounter.objects.create(id=1, next_value=118)

    def _client(self, role=None):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("login"))
        if role is not None:
            response = client.post(reverse("login"), {
                "email": self.accounts[role].email,
                "password": self.password,
                "csrfmiddlewaretoken": client.cookies[settings.CSRF_COOKIE_NAME].value,
            })
            self.assertEqual(response.status_code, 302)
            self.assertEqual(client.session[SESSION_KEY], str(self.accounts[role].pk))
        return client

    def _snapshot(self):
        business = {
            model._meta.label: list(model.objects.order_by(model._meta.pk.name).values())
            for model in apps.get_models()
            if model._meta.app_label in {"cash", "catalog", "inventory", "sales"}
        }
        business["identity.Account"] = list(Account.objects.order_by("pk").values())
        return business

    def _denied_pair(self, client, route, payload, *, visitor=False):
        before = self._snapshot()
        for method in ("get", "post"):
            with self.subTest(route=route, method=method, visitor=visitor):
                if method == "get":
                    response = client.get(route)
                else:
                    response = client.post(route, {
                        **payload,
                        "csrfmiddlewaretoken": client.cookies[settings.CSRF_COOKIE_NAME].value,
                    })
                if visitor:
                    self.assertEqual(response.status_code, 302)
                    self.assertTrue(response.headers["Location"].startswith("/?next="))
                    self.assertNotIn(SESSION_KEY, client.session)
                else:
                    self.assertEqual(response.status_code, 403)
                    self.assertContains(response, "No tienes permiso para esta operación", status_code=403)
                    self.assertContains(response, "Tu cuenta no tiene autorización para realizar esta operación.", status_code=403)
                for marker in (
                    self.category.name, self.product.name, self.product.barcode,
                    self.lot.number, self.register.code, self.sale.correlative,
                    self.sale.seller_snapshot_name,
                ):
                    self.assertNotIn(marker, response.content.decode())
                self.assertEqual(before, self._snapshot())

    def test_cp003_seller_cannot_create_product_with_valid_payload_and_csrf(self):
        payload = {
            "name": "Producto nuevo ficticio 01K", "barcode_type": "INTERNAL",
            "barcode": "NUEVO-01K", "category": str(self.category.pk),
            "unit": "UND", "sale_price": "3.00", "minimum_stock": "2",
        }
        form = ProductRegistrationForm(payload)
        self.assertTrue(form.is_valid(), form.errors.as_json())
        self._denied_pair(self._client(Role.Code.SELLER), reverse("product-entry"), payload)

    def test_cp003_warehouse_cannot_checkout_with_valid_payload_and_csrf(self):
        payload = {"cash_received": "20.00", "idempotency_key": str(uuid.uuid4())}
        form = CheckoutForm(payload)
        self.assertTrue(form.is_valid(), form.errors.as_json())
        self._denied_pair(self._client(Role.Code.WAREHOUSE), reverse("sales-checkout"), payload)

    def test_cp003_admin_cannot_open_cash_with_valid_payload_and_csrf(self):
        payload = {"opening_amount": "100.00"}
        form = CashOpeningForm(payload)
        self.assertTrue(form.is_valid(), form.errors.as_json())
        self._denied_pair(self._client(Role.Code.ADMIN), reverse("cash-open"), payload)

    def test_cp003_visitor_cannot_read_or_post_sales_history_with_valid_csrf(self):
        self._denied_pair(self._client(), reverse("sales-history"), {}, visitor=True)

    def test_other_published_role_gates_preserve_populated_business_tables(self):
        # This is authorization coverage; it does not approve the destination workflows.
        routes = {
            Role.Code.ADMIN: [
                ("sales-draft", ()), ("sales-checkout", ()), ("cash-close", ()),
                ("inventory-load", ()), ("stock-entry", ()),
            ],
            Role.Code.WAREHOUSE: [
                ("employee-list", ()), ("employee-create", ()),
                ("employee-edit", (self.accounts[Role.Code.ADMIN].pk,)),
                ("product-entry", ()), ("product-edit", (self.product.pk,)),
                ("category-create", ()), ("supplier-create", ()),
                ("cash-open", ()), ("cash-close", ()), ("sales-draft", ()),
                ("sales-history", ()), ("physical-adjustment", ()),
            ],
            Role.Code.SELLER: [
                ("employee-list", ()), ("employee-create", ()),
                ("employee-edit", (self.accounts[Role.Code.ADMIN].pk,)),
                ("product-edit", (self.product.pk,)), ("category-create", ()),
                ("supplier-list", ()), ("supplier-create", ()),
                ("inventory-load", ()), ("stock-entry", ()),
                ("stock-writeoff", ()), ("physical-adjustment", ()),
                ("stock-overview", ()), ("product-expirations", ()),
                ("product-movements", (self.product.pk,)),
            ],
        }
        for role, targets in routes.items():
            client = self._client(role)
            for name, args in targets:
                with self.subTest(role=role, route=name):
                    self._denied_pair(client, reverse(name, args=args), {})
