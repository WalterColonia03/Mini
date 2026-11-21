"""Regressions for the commercial login perimeter and lockout."""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import salted_hmac

from cash.models import CashRegister, CashShift
from catalog.models import Category, Product

from .models import Account, LoginAttempt, Role
from .services import authenticate_active_account


class CommercialLoginPerimeterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.role_admin = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.role_warehouse = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.role_seller = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
        cls.password = "Synthetic01iPassword!"
        cls.staff = Account.objects.create_user(
            "staff01i@example.invalid", cls.password, display_name="Staff ficticio",
            role=cls.role_admin, is_staff=True,
        )
        cls.superuser = Account.objects.create_user(
            "super01i@example.invalid", cls.password, display_name="Superusuario ficticio",
            role=cls.role_seller, is_staff=True, is_superuser=True,
        )
        cls.warehouse = Account.objects.create_user(
            "warehouse01i@example.invalid", cls.password, display_name="Almacenero ficticio",
            role=cls.role_warehouse,
        )

    def _identifier(self, email):
        return salted_hmac("identity.login.throttle", Account.normalize_email(email), algorithm="sha256").hexdigest()

    def _lock(self, email):
        return LoginAttempt.objects.create(
            identifier=self._identifier(email), failures=5,
            locked_until=timezone.now() + timedelta(minutes=15),
        )

    def test_commercial_application_has_no_django_admin_endpoints(self):
        client = Client()
        for path in ("/admin", "/admin/", "/admin/login/", "/admin/identity/account/"):
            with self.subTest(path=path):
                self.assertEqual(client.get(path).status_code, 404)
                self.assertEqual(client.post(path, {"username": self.staff.email, "password": self.password}).status_code, 404)
        self.assertNotIn("_auth_user_id", client.session)
        self.assertEqual(LoginAttempt.objects.count(), 0)

    def test_locked_staff_and_superuser_cannot_bypass_login_via_admin(self):
        for account in (self.staff, self.superuser):
            with self.subTest(superuser=account.is_superuser):
                attempt = self._lock(account.email)
                client = Client()
                response = client.post("/admin/login/?next=/admin/", {
                    "username": account.email, "password": self.password, "next": "/admin/",
                })
                self.assertEqual(response.status_code, 404)
                self.assertNotIn("_auth_user_id", client.session)
                self.assertEqual(client.get(reverse("dashboard")).status_code, 302)
                attempt.refresh_from_db()
                self.assertEqual(attempt.failures, 5)
                self.assertIsNotNone(attempt.locked_until)

    def test_authenticated_staff_has_no_admin_portal_or_role_escalation(self):
        for account in (self.staff, self.superuser):
            with self.subTest(superuser=account.is_superuser):
                client = Client()
                self.assertEqual(client.post(reverse("login"), {
                    "email": account.email, "password": self.password,
                }).status_code, 302)
                self.assertEqual(client.get("/admin/").status_code, 404)
                self.assertEqual(client.get("/admin/identity/account/").status_code, 404)
                expected = 403 if account.role_id == self.role_seller.pk else 200
                self.assertEqual(client.get(reverse("employee-list")).status_code, expected)

    def test_denied_cross_role_requests_preserve_populated_business_data(self):
        category = Category.objects.create(name="Categoría ficticia 01I")
        Product.objects.create(
            category=category, name="Producto ficticio 01I", barcode="AUD-01I",
            sale_price=Decimal("4.20"), minimum_stock=2,
        )
        register = CashRegister.objects.create(code="CAJA-01I")
        CashShift.objects.create(cash_register=register, seller=self.superuser, opening_amount=Decimal("25.00"))

        def snapshot():
            return {
                "accounts": list(Account.objects.order_by("id").values("id", "display_name", "role_id", "is_active")),
                "categories": list(Category.objects.order_by("id").values("id", "name", "is_active")),
                "products": list(Product.objects.order_by("id").values("id", "name", "sale_price", "is_active")),
                "shifts": list(CashShift.objects.order_by("id").values("id", "seller_id", "opening_amount", "status")),
            }

        for account in (self.warehouse, self.superuser, self.staff):
            with self.subTest(role=account.role.code):
                client = Client(enforce_csrf_checks=True)
                client.get(reverse("login"))
                token = client.cookies[settings.CSRF_COOKIE_NAME].value
                response = client.post(reverse("login"), {
                    "email": account.email, "password": self.password, "csrfmiddlewaretoken": token,
                })
                self.assertEqual(response.status_code, 302)
                token = client.cookies[settings.CSRF_COOKIE_NAME].value
                before = snapshot()
                if account.role.code != Role.Code.ADMIN:
                    denied = client.get(reverse("employee-list"))
                    self.assertEqual(denied.status_code, 403)
                    self.assertNotContains(denied, self.staff.display_name, status_code=403)
                    denied = client.post(reverse("employee-edit", args=[self.staff.pk]), {
                        "display_name": "Alteración ficticia", "csrfmiddlewaretoken": token,
                    })
                    self.assertEqual(denied.status_code, 403)
                    denied = client.post(reverse("product-entry"), {
                        "name": "Alta indebida", "csrfmiddlewaretoken": token,
                    })
                    self.assertEqual(denied.status_code, 403)
                else:
                    denied = client.post(reverse("cash-open"), {
                        "opening_amount": "999.00", "csrfmiddlewaretoken": token,
                    })
                    self.assertEqual(denied.status_code, 403)
                self.assertEqual(snapshot(), before)

    def test_known_identifier_already_locked_does_not_hash_password(self):
        attempt = self._lock(self.staff.email)
        original = (attempt.failures, attempt.locked_until, attempt.updated_at)
        with patch("identity.services.check_password", side_effect=AssertionError("Unexpected hash for locked known identity")):
            result = authenticate_active_account(self.staff.email, self.password)
        attempt.refresh_from_db()
        self.assertFalse(result.authenticated)
        self.assertEqual(result.locked_minutes, 15)
        self.assertEqual((attempt.failures, attempt.locked_until, attempt.updated_at), original)

    def test_unknown_identifier_already_locked_does_not_hash_password(self):
        email = "missing01i@example.invalid"
        attempt = self._lock(email)
        original = (attempt.failures, attempt.locked_until, attempt.updated_at)
        with patch.object(Account, "set_password", autospec=True, side_effect=AssertionError("Unexpected hash for locked unknown identity")):
            result = authenticate_active_account(email, self.password)
        attempt.refresh_from_db()
        self.assertFalse(result.authenticated)
        self.assertEqual(result.locked_minutes, 15)
        self.assertEqual((attempt.failures, attempt.locked_until, attempt.updated_at), original)

    def test_fifth_failure_gets_full_fifteen_minutes_after_password_check(self):
        attempt = LoginAttempt.objects.create(identifier=self._identifier(self.staff.email), failures=4)
        initial = timezone.now()
        clock = [initial]

        def password_check(_password, _encoded):
            clock[0] += timedelta(seconds=3)
            return False

        with patch("identity.services.timezone.now", side_effect=lambda: clock[0]), patch(
            "identity.services.check_password", side_effect=password_check
        ):
            result = authenticate_active_account(self.staff.email, "wrong")
        attempt.refresh_from_db()
        self.assertFalse(result.authenticated)
        self.assertEqual(result.locked_minutes, 15)
        self.assertEqual(attempt.failures, 5)
        self.assertEqual(attempt.locked_until, initial + timedelta(seconds=3, minutes=15))

    def test_expired_lock_still_checks_password_and_resets_on_success(self):
        attempt = self._lock(self.staff.email)
        expiration = attempt.locked_until
        with patch("identity.services.timezone.now", return_value=expiration):
            result = authenticate_active_account(self.staff.email, self.password)
        attempt.refresh_from_db()
        self.assertTrue(result.authenticated)
        self.assertEqual(attempt.failures, 0)
        self.assertIsNone(attempt.locked_until)

    def test_failed_attempt_logs_sanitized_diagnostic_when_audit_insert_fails(self):
        client = Client()
        fake_secret = "audit01i-fake-secret-value"
        with self.assertLogs("identity.audit", level="WARNING") as logs:
            with patch("identity.audit.record_transactional_event", side_effect=OSError("password=" + fake_secret)):
                response = client.post(reverse("login"), {
                    "email": self.staff.email, "password": "wrong",
                }, HTTP_X_REQUEST_ID="audit01i-failed-insert")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Correo o contraseña incorrectos")
        self.assertNotIn("_auth_user_id", client.session)
        self.assertEqual(LoginAttempt.objects.get(pk=self._identifier(self.staff.email)).failures, 1)
        output = "\n".join(logs.output)
        self.assertIn("audit_persist_error", output)
        self.assertIn("OSError", output)
        self.assertIn("audit01i-failed-insert", output)
        self.assertNotIn(fake_secret, output)

    def test_locked_attempt_logs_sanitized_diagnostic_when_audit_insert_fails(self):
        attempt = self._lock(self.staff.email)
        expires = attempt.locked_until
        client = Client()
        fake_secret = "audit01i-other-fake-secret"
        with self.assertLogs("identity.audit", level="WARNING") as logs:
            with patch("identity.audit.record_transactional_event", side_effect=OSError("password=" + fake_secret)):
                response = client.post(reverse("login"), {
                    "email": self.staff.email, "password": self.password,
                }, HTTP_X_REQUEST_ID="audit01i-locked-insert")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "15 minuto(s)")
        self.assertNotIn("_auth_user_id", client.session)
        attempt.refresh_from_db()
        self.assertEqual((attempt.failures, attempt.locked_until), (5, expires))
        output = "\n".join(logs.output)
        self.assertIn("audit_persist_error", output)
        self.assertIn("audit01i-locked-insert", output)
        self.assertNotIn(fake_secret, output)

    def test_failed_attempt_remains_denied_when_both_audit_sinks_fail(self):
        client = Client()
        with patch("identity.audit.record_transactional_event", side_effect=OSError), patch(
            "identity.audit._emit_external_event", side_effect=OSError
        ):
            response = client.post(reverse("login"), {
                "email": self.staff.email, "password": "wrong",
            })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Correo o contraseña incorrectos")
        self.assertNotIn("_auth_user_id", client.session)
        self.assertEqual(LoginAttempt.objects.get(pk=self._identifier(self.staff.email)).failures, 1)
