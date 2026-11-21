"""Stage 03-AJ / 06-E: session expiry, revocation, cache headers and lock-safe actor verification."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Category, Product
from identity.models import Account, Role
from identity.services import deactivate_employee, reactivate_employee, update_employee
from inventory.models import InitialInventoryLoad, Lot
from inventory.services import LotInput, confirm_initial_load, register_stock_entry


class ReceiptSessionAndRevocationTests(TestCase):
    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
        cls.admin = Account.objects.create_user(
            "admin-aj@test.invalid", cls.password, display_name="Admin AJ", role=cls.admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "wh-aj@test.invalid", cls.password, display_name="Almacenero AJ", role=cls.warehouse_role
        )
        cls.seller = Account.objects.create_user(
            "seller-aj@test.invalid", cls.password, display_name="Vendedor AJ", role=cls.seller_role
        )
        cls.category = Category.objects.create(name="Conservas AJ")
        cls.product_loaded = Product.objects.create(
            category=cls.category,
            name="Atún AJ reposición",
            barcode="775000900001",
            sale_price=Decimal("7.50"),
        )
        cls.product_unloaded = Product.objects.create(
            category=cls.category,
            name="Sardina AJ carga inicial",
            barcode="775000900002",
            sale_price=Decimal("6.20"),
        )
        cls.load = confirm_initial_load(
            actor=cls.warehouse,
            product=cls.product_loaded,
            lots=[LotInput("AJ-INIT", 10, Decimal("2.0000"), timezone.localdate() + timedelta(days=60))],
        )

    def _entry_payload(self, product, number="AJ-NEW"):
        future = (timezone.localdate() + timedelta(days=90)).isoformat()
        return {
            "product": str(product.pk),
            "supplier": "",
            "lots-TOTAL_FORMS": "1",
            "lots-INITIAL_FORMS": "0",
            "lots-MIN_NUM_FORMS": "1",
            "lots-MAX_NUM_FORMS": "1000",
            "lots-0-number": number,
            "lots-0-quantity": "2",
            "lots-0-unit_cost": "5.0000",
            "lots-0-expiration_date": future,
        }

    def test_service_rejects_anonymous_inactive_and_stale_actor_instances(self) -> None:
        future = timezone.localdate() + timedelta(days=90)
        sample_lot = [LotInput("AJ-STALE", 3, Decimal("4.0000"), future)]
        inactive_wh = Account.objects.create_user(
            "wh-inact-aj@test.invalid",
            self.password,
            display_name="Inactivo AJ",
            role=self.warehouse_role,
            is_active=False,
        )

        # Capture in-memory snapshots before mutating the DB row.
        stale_role_wh = Account.objects.select_related("role").get(pk=self.warehouse.pk)
        update_employee(
            actor=self.admin,
            account=Account.objects.get(pk=self.warehouse.pk),
            display_name=self.warehouse.display_name,
            email=self.warehouse.email,
            role=self.seller_role,
        )

        try:
            for operation, target in (
                (confirm_initial_load, self.product_unloaded),
                (register_stock_entry, self.product_loaded),
            ):
                for label, bad_actor in (
                    ("anonymous", AnonymousUser()),
                    ("inactive", inactive_wh),
                    ("stale_role", stale_role_wh),
                ):
                    with self.subTest(op=operation.__name__, case=label):
                        before_lots = list(Lot.objects.order_by("pk").values())
                        before_loads = list(InitialInventoryLoad.objects.order_by("pk").values())
                        with self.assertRaises(PermissionDenied):
                            operation(actor=bad_actor, product=target, lots=sample_lot)
                        self.assertEqual(list(Lot.objects.order_by("pk").values()), before_lots)
                        self.assertEqual(list(InitialInventoryLoad.objects.order_by("pk").values()), before_loads)
        finally:
            update_employee(
                actor=self.admin,
                account=Account.objects.get(pk=self.warehouse.pk),
                display_name=self.warehouse.display_name,
                email=self.warehouse.email,
                role=self.warehouse_role,
            )

        stale_active_wh = Account.objects.select_related("role").get(pk=self.warehouse.pk)
        deactivate_employee(actor=self.admin, account=Account.objects.get(pk=self.warehouse.pk))
        try:
            for operation, target in (
                (confirm_initial_load, self.product_unloaded),
                (register_stock_entry, self.product_loaded),
            ):
                before_lots = list(Lot.objects.order_by("pk").values())
                before_loads = list(InitialInventoryLoad.objects.order_by("pk").values())
                with self.subTest(op=operation.__name__, case="stale_deactivated"):
                    with self.assertRaises(PermissionDenied):
                        operation(actor=stale_active_wh, product=target, lots=sample_lot)
                    self.assertEqual(list(Lot.objects.order_by("pk").values()), before_lots)
                    self.assertEqual(list(InitialInventoryLoad.objects.order_by("pk").values()), before_loads)
        finally:
            reactivate_employee(actor=self.admin, account=Account.objects.get(pk=self.warehouse.pk))

    def test_surviving_inactive_session_is_logged_out_before_view_or_service(self) -> None:
        inactive_wh = Account.objects.create_user(
            "wh-surviving@test.invalid",
            self.password,
            display_name="Sobreviviente Inactivo",
            role=self.warehouse_role,
            is_active=False,
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(inactive_wh)

        for route_name, args in (
            ("stock-entry", ()),
            ("inventory-load", ()),
            ("inventory-load-created", (self.load.pk,)),
        ):
            with self.subTest(route=route_name):
                get_resp = client.get(reverse(route_name, args=args))
                self.assertRedirects(
                    get_resp,
                    f"{reverse('login')}?next={reverse(route_name, args=args)}",
                    fetch_redirect_response=False,
                )
                self.assertNotIn("_auth_user_id", client.session)

        # Repeat with a valid CSRF token and a surviving session for an inactive user on POST.
        client.force_login(self.warehouse)
        form_get = client.get(reverse("stock-entry"))
        csrf = form_get.cookies["csrftoken"].value
        Account.objects.filter(pk=self.warehouse.pk).update(is_active=False)
        try:
            before_lots = Lot.objects.count()
            post_resp = client.post(
                reverse("stock-entry"),
                {**self._entry_payload(self.product_loaded), "csrfmiddlewaretoken": csrf},
            )
            self.assertRedirects(
                post_resp,
                f"{reverse('login')}?next={reverse('stock-entry')}",
                fetch_redirect_response=False,
            )
            self.assertNotIn("_auth_user_id", client.session)
            self.assertEqual(Lot.objects.count(), before_lots)
        finally:
            Account.objects.filter(pk=self.warehouse.pk).update(is_active=True)

        # Dashboard and root login also flush an inactive surviving session cleanly.
        dash_client = Client()
        dash_client.force_login(inactive_wh)
        dash_resp = dash_client.get(reverse("dashboard"))
        self.assertRedirects(
            dash_resp, f"{reverse('login')}?next={reverse('dashboard')}",
            fetch_redirect_response=False,
        )
        self.assertNotIn("_auth_user_id", dash_client.session)

        dash_client.force_login(inactive_wh)
        root_resp = dash_client.get(reverse("login"))
        self.assertEqual(root_resp.status_code, 200)
        self.assertNotIn("_auth_user_id", dash_client.session)

    def test_receipt_routes_emit_no_store_and_detail_panel_layout_classes(self) -> None:
        self.client.force_login(self.warehouse)
        for route_name, args in (
            ("inventory-load", ()),
            ("stock-entry", ()),
            ("inventory-load-created", (self.load.pk,)),
        ):
            resp = self.client.get(reverse(route_name, args=args))
            self.assertEqual(resp.status_code, 200)
            cc = resp.headers.get("Cache-Control", "")
            self.assertIn("no-store", cc)
            self.assertIn("no-cache", cc)
            if route_name == "inventory-load-created":
                self.assertContains(resp, 'class="panel form-panel load-detail-panel"')

    def test_redirected_login_with_non_warehouse_role_denies_without_writes(self) -> None:
        next_path = reverse("stock-entry")
        client = Client(enforce_csrf_checks=True)
        get_login = client.get(f"{reverse('login')}?next={next_path}")
        csrf = get_login.cookies["csrftoken"].value

        login_resp = client.post(
            f"{reverse('login')}?next={next_path}",
            {
                "email": self.admin.email,
                "password": self.password,
                "next": next_path,
                "csrfmiddlewaretoken": csrf,
            },
        )
        self.assertEqual(login_resp.status_code, 302)
        self.assertEqual(login_resp["Location"], next_path)
        denied = client.get(next_path)
        self.assertEqual(denied.status_code, 403)
        self.assertContains(denied, "No tienes permiso", status_code=403)

        before_lots = Lot.objects.count()
        post_csrf = client.cookies["csrftoken"].value
        denied_post = client.post(
            next_path,
            {**self._entry_payload(self.product_loaded), "csrfmiddlewaretoken": post_csrf},
        )
        self.assertEqual(denied_post.status_code, 403)
        self.assertEqual(Lot.objects.count(), before_lots)

