"""Stage 01 regression cases. Django Client/ORM, not browser evidence."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone as dt_timezone
import secrets
import sys
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.models import Session
from django.test import Client, RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils.crypto import salted_hmac
from django.views.debug import ExceptionReporter, SafeExceptionReporterFilter

from .models import Account, LoginAttempt, Role
from .services import INVALID_CREDENTIALS_MESSAGE, authenticate_active_account
from .views import login_view


class LoginAudit01Tests(TestCase):
    """Credentials, persistent lockout, boundaries and server-side navigation."""

    @classmethod
    def setUpTestData(cls):
        cls.password = secrets.token_urlsafe(24)
        cls.wrong_password = secrets.token_urlsafe(24)
        cls.accounts = {}
        for code, label in Role.Code.choices:
            role = Role.objects.create(code=code, name=label)
            cls.accounts[code] = Account.objects.create_user(
                f"{code.lower()}.audit01@example.invalid", cls.password,
                display_name=f"AUD01 {label}", role=role,
            )
        cls.admin = cls.accounts[Role.Code.ADMIN]
        cls.inactive = Account.objects.create_user(
            "inactive.audit01@example.invalid", cls.password,
            display_name="AUD01 Inactive", role=cls.admin.role, is_active=False,
        )
        cls.base_time = datetime(2026, 11, 9, 17, 0, tzinfo=dt_timezone.utc)

    def post(self, email=None, password=None, client=None, **extra):
        return (client or self.client).post(reverse("login"), {
            "email": self.admin.email if email is None else email,
            "password": self.password if password is None else password,
            **extra,
        })

    def attempt(self, email=None):
        identifier = salted_hmac(
            "identity.login.throttle", Account.normalize_email(email or self.admin.email),
            algorithm="sha256",
        ).hexdigest()
        return LoginAttempt.objects.get(identifier=identifier)

    def lock(self, email=None, client=None):
        with patch("identity.services.timezone.now", return_value=self.base_time):
            for _ in range(5):
                self.post(email=email, password=self.wrong_password, client=client)
        return self.attempt(email)

    def test_empty_post_is_bound_and_reports_both_required_fields(self):
        # An altered request may contain no form keys; validation must still run.
        response = self.client.post(reverse("login"), {})
        self.assertTrue(response.context["form"].is_bound)
        self.assertEqual(set(response.context["form"].errors), {"email", "password"})
        self.assertEqual(LoginAttempt.objects.count(), 0)

    def test_get_and_failed_post_are_not_cacheable(self):
        for response in (self.client.get(reverse("login")), self.post(password=self.wrong_password)):
            with self.subTest(status=response.status_code):
                self.assertIn("no-store", response.headers.get("Cache-Control", ""))
                self.assertIn("private", response.headers.get("Cache-Control", ""))

    @override_settings(DEBUG=False)
    def test_exception_filter_redacts_submitted_credentials(self):
        request = RequestFactory().post(reverse("login"), {
            "email": self.admin.email, "password": self.password,
            "csrfmiddlewaretoken": secrets.token_urlsafe(32),
        })
        request.user = AnonymousUser()
        with patch("identity.views.authenticate_active_account", side_effect=RuntimeError("AUD01 induced failure")):
            try:
                login_view(request)
            except RuntimeError:
                reporter = ExceptionReporter(request, *sys.exc_info())
                # Never print the generated report or submitted values.
                self.assertFalse(self.password in reporter.get_traceback_text(), "Credential leaked into exception report")
            else:
                self.fail("The induced exception path did not execute")
        cleansed = SafeExceptionReporterFilter().get_post_parameters(request)
        self.assertFalse(cleansed.get("password") == self.password, "POST credential was not redacted")

    @override_settings(DEBUG=False)
    def test_service_exception_filter_redacts_credential_locals(self):
        request = RequestFactory().get(reverse("login"))
        with patch.object(LoginAttempt.objects, "get_or_create", side_effect=RuntimeError("AUD01 induced failure")):
            try:
                authenticate_active_account(self.admin.email, self.password)
            except RuntimeError:
                reporter = ExceptionReporter(request, *sys.exc_info())
                frames = reporter.get_traceback_data()["frames"]
                service_frames = [frame for frame in frames if frame["function"] == "authenticate_active_account"]
                self.assertEqual(len(service_frames), 1)
                filtered = dict(service_frames[0]["vars"])
                self.assertFalse(self.password in str(filtered), "Credential leaked from service locals")
            else:
                self.fail("The induced exception path did not execute")

    def test_all_three_roles_accept_normalized_email_and_persist_identity(self):
        for role, account in self.accounts.items():
            client = Client()
            response = self.post(email=f"  {account.email.upper()}  ", client=client)
            with self.subTest(role=role):
                self.assertRedirects(response, reverse("dashboard"))
                self.assertEqual(client.session["_auth_user_id"], str(account.pk))
                self.assertEqual(client.session["role_code"], role)
                stored = Session.objects.get(session_key=client.session.session_key).get_decoded()
                self.assertEqual(stored["_auth_user_id"], str(account.pk))
                self.assertFalse(self.password in str(stored), "Session contains submitted password")
                self.assertEqual(self.attempt(account.email).failures, 0)

    def test_wrong_unknown_inactive_share_exact_message_and_no_identity(self):
        cases = (
            (self.admin.email, self.wrong_password),
            ("unknown.audit01@example.invalid", self.password),
            (self.inactive.email, self.password),
        )
        before = list(Account.objects.values())
        for email, password in cases:
            client = Client()
            response = self.post(email=email, password=password, client=client)
            self.assertEqual(list(response.context["form"].non_field_errors()), [INVALID_CREDENTIALS_MESSAGE])
            self.assertNotIn("_auth_user_id", client.session)
        self.assertEqual(before, list(Account.objects.values()))

    def test_fifth_failure_locks_for_exactly_fifteen_minutes(self):
        with patch("identity.services.timezone.now", return_value=self.base_time):
            for index in range(1, 6):
                response = self.post(password=self.wrong_password)
                attempt = self.attempt()
                self.assertEqual(attempt.failures, index)
                if index < 5:
                    self.assertIsNone(attempt.locked_until)
                    self.assertEqual(list(response.context["form"].non_field_errors()), [INVALID_CREDENTIALS_MESSAGE])
                else:
                    self.assertEqual(attempt.locked_until, self.base_time + timedelta(minutes=15))
                    self.assertContains(response, "15 minuto(s)")
                self.assertNotIn("_auth_user_id", self.client.session)

    def test_inactive_and_unknown_share_fifth_failure_response(self):
        for email in (self.inactive.email, "unknown.audit01@example.invalid"):
            client = Client()
            with patch("identity.services.timezone.now", return_value=self.base_time):
                for index in range(5):
                    response = self.post(email=email, client=client)
                    self.assertNotIn("_auth_user_id", client.session)
                    self.assertContains(response, "15 minuto(s)" if index == 4 else INVALID_CREDENTIALS_MESSAGE)
            self.assertEqual(self.attempt(email).locked_until, self.base_time + timedelta(minutes=15))

    def test_locked_state_shared_across_sessions_and_normalized_variants(self):
        attempt = self.lock()
        original = (attempt.failures, attempt.locked_until, attempt.updated_at)
        other = Client()
        with patch("identity.services.timezone.now", return_value=self.base_time + timedelta(seconds=30)):
            for password in (self.password, self.wrong_password):
                response = self.post(email=f" {self.admin.email.upper()} ", password=password, client=other)
                self.assertContains(response, "15 minuto(s)")
                self.assertNotIn("_auth_user_id", other.session)
        attempt.refresh_from_db()
        self.assertEqual((attempt.failures, attempt.locked_until, attempt.updated_at), original)
        self.assertEqual(LoginAttempt.objects.count(), 1)

    def test_minutes_round_up_at_each_relevant_boundary(self):
        self.lock()
        for seconds, minutes in ((0, 15), (59, 15), (60, 14), (839, 2), (840, 1), (899, 1)):
            with self.subTest(seconds=seconds), patch("identity.services.timezone.now", return_value=self.base_time + timedelta(seconds=seconds)):
                response = self.post()
                self.assertContains(response, f"{minutes} minuto(s)")
                self.assertNotIn("_auth_user_id", self.client.session)

    def test_exact_expiration_permits_login_and_resets_stable_row(self):
        attempt = self.lock()
        with patch("identity.services.timezone.now", return_value=self.base_time + timedelta(minutes=15)):
            response = self.post()
        self.assertRedirects(response, reverse("dashboard"))
        attempt.refresh_from_db()
        self.assertEqual(attempt.failures, 0)
        self.assertIsNone(attempt.locked_until)
        self.assertEqual(LoginAttempt.objects.count(), 1)

    def test_wrong_password_after_expiration_starts_new_series(self):
        attempt = self.lock()
        with patch("identity.services.timezone.now", return_value=self.base_time + timedelta(minutes=15)):
            response = self.post(password=self.wrong_password)
        self.assertContains(response, INVALID_CREDENTIALS_MESSAGE)
        attempt.refresh_from_db()
        self.assertEqual(attempt.failures, 1)
        self.assertIsNone(attempt.locked_until)

    def test_success_before_fifth_failure_resets_consecutive_count(self):
        for _ in range(4):
            self.post(password=self.wrong_password)
        self.assertRedirects(self.post(), reverse("dashboard"))
        self.assertEqual(self.attempt().failures, 0)
        self.post(password=self.wrong_password, client=Client())
        self.assertEqual(self.attempt().failures, 1)
        self.assertIsNone(self.attempt().locked_until)

    def test_one_identifier_lock_does_not_lock_another_role(self):
        self.lock()
        for role in (Role.Code.WAREHOUSE, Role.Code.SELLER):
            client = Client()
            self.assertRedirects(self.post(email=self.accounts[role].email, client=client), reverse("dashboard"))
            self.assertEqual(client.session["role_code"], role)
        self.assertEqual(self.attempt().failures, 5)

    def test_lock_does_not_revoke_an_already_authenticated_session(self):
        authenticated = Client()
        self.assertRedirects(self.post(client=authenticated), reverse("dashboard"))
        self.lock(client=Client())
        self.assertEqual(authenticated.get(reverse("dashboard")).status_code, 200)
        self.assertEqual(authenticated.session["_auth_user_id"], str(self.admin.pk))

    def test_password_whitespace_is_preserved(self):
        spaced = "  " + self.password + "  "
        self.admin.set_password(spaced)
        self.admin.save(update_fields=["password"])
        self.assertContains(self.post(), INVALID_CREDENTIALS_MESSAGE)
        self.assertRedirects(self.post(password=spaced), reverse("dashboard"))

    def test_invalid_fields_do_not_increment_lock_counter(self):
        cases = (("", self.password), ("not-an-email", self.password), (self.admin.email, ""),
                 ("bad\x00@example.invalid", self.password), (self.admin.email, "bad\x00value"))
        for email, password in cases:
            response = self.post(email=email, password=password)
            self.assertTrue(response.context["form"].errors)
            self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(LoginAttempt.objects.count(), 0)

    def test_email_length_boundaries_254_255_319_320_321(self):
        # Django's EmailValidator permits 320, while the Account model permits 254.
        # Unknown valid identifiers still receive the uniform credentials message.
        for size in (254, 255, 319, 320, 321):
            email = "a" * (size - len("@example.invalid")) + "@example.invalid"
            response = self.post(email=email)
            if size <= 320:
                self.assertEqual(list(response.context["form"].non_field_errors()), [INVALID_CREDENTIALS_MESSAGE])
            else:
                self.assertIn("email", response.context["form"].errors)
        self.assertEqual(LoginAttempt.objects.count(), 4)

    def test_password_is_not_repopulated_and_next_is_html_escaped(self):
        marker = '<script data-audit="untrusted">alert(1)</script>'
        response = self.post(password=self.wrong_password, next=marker)
        html = response.content.decode()
        self.assertFalse(self.wrong_password in html, "Rejected password was rendered")
        self.assertNotIn(marker, html)
        self.assertIn("&lt;script", html)

    def test_csrf_absent_invalid_and_cross_origin_do_not_touch_attempts(self):
        for token, origin in ((None, None), ("invalid", None), ("cookie", "https://outside.example.invalid")):
            client = Client(enforce_csrf_checks=True)
            client.get(reverse("login"))
            data = {"email": self.admin.email, "password": self.password}
            if token:
                data["csrfmiddlewaretoken"] = client.cookies[settings.CSRF_COOKIE_NAME].value if token == "cookie" else token
            response = client.post(reverse("login"), data, **({"HTTP_ORIGIN": origin} if origin else {}))
            self.assertEqual(response.status_code, 403)
            self.assertNotIn("_auth_user_id", client.session)
        self.assertEqual(LoginAttempt.objects.count(), 0)

    def test_valid_csrf_rotates_csrf_and_session_and_sets_cookie_flags(self):
        client = Client(enforce_csrf_checks=True)
        client.get(reverse("login"))
        old_csrf = client.cookies[settings.CSRF_COOKIE_NAME].value
        session = client.session
        session["anonymous_marker"] = "AUD01"
        session.save()
        old_session = session.session_key
        response = self.post(client=client, csrfmiddlewaretoken=old_csrf)
        self.assertRedirects(response, reverse("dashboard"))
        self.assertNotEqual(client.session.session_key, old_session)
        self.assertFalse(Session.objects.filter(session_key=old_session).exists())
        self.assertNotEqual(client.cookies[settings.CSRF_COOKIE_NAME].value, old_csrf)
        cookie = client.cookies[settings.SESSION_COOKIE_NAME]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")

    def test_external_scheme_relative_and_javascript_next_fall_back(self):
        for target in ("https://outside.example.invalid/", "//outside.example.invalid/", "javascript:alert(1)", "///outside.example.invalid", "http:///outside.example.invalid"):
            with self.subTest(target=target):
                self.assertRedirects(self.post(client=Client(), next=target), reverse("dashboard"))

    def test_https_login_rejects_http_downgrade_next(self):
        response = self.client.post(reverse("login"), {
            "email": self.admin.email, "password": self.password, "next": "http://testserver/inicio/",
        }, secure=True)
        self.assertRedirects(response, reverse("dashboard"))

    def test_internal_next_is_followed_but_does_not_bypass_role_authorization(self):
        seller = self.accounts[Role.Code.SELLER]
        before = list(Account.objects.values())
        response = self.post(email=seller.email, next=reverse("employee-list"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("employee-list"))
        denied = self.client.get(response.headers["Location"])
        self.assertEqual(denied.status_code, 403)
        self.assertNotContains(denied, self.inactive.email, status_code=403)
        for old, new in zip(before, list(Account.objects.values())):
            old.pop("last_login")
            new.pop("last_login")
            self.assertEqual(old, new)

    def test_get_credentials_are_ignored_and_put_is_rejected(self):
        response = self.client.get(reverse("login"), {"email": self.admin.email, "password": self.password})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.put(reverse("login"), {}).status_code, 405)
        self.assertEqual(LoginAttempt.objects.count(), 0)

    def test_login_attempts_store_only_hmac_and_counter_state(self):
        self.post(password=self.wrong_password)
        stored = LoginAttempt.objects.values().get()
        self.assertEqual(set(stored), {"identifier", "failures", "locked_until", "updated_at"})
        self.assertEqual(len(stored["identifier"]), 64)
        self.assertNotIn(self.admin.email, str(stored))
        self.assertFalse(self.password in str(stored) or self.wrong_password in str(stored))

    def test_contradictory_post_and_get_next_and_nonexistent_local_target(self):
        # POST next takes priority over contradictory GET query next.
        client = Client()
        response = client.post(
            f"{reverse('login')}?next={reverse('cash-open')}",
            {"email": self.admin.email, "password": self.password, "next": reverse("employee-list")},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("employee-list"))

        # Empty POST next falls back to GET query next due to `or` evaluation.
        client = Client()
        response = client.post(
            f"{reverse('login')}?next={reverse('employee-list')}",
            {"email": self.admin.email, "password": self.password, "next": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("employee-list"))

        # Disallowed external POST next overrides valid GET next and falls back to dashboard.
        client = Client()
        response = client.post(
            f"{reverse('login')}?next={reverse('employee-list')}",
            {"email": self.admin.email, "password": self.password, "next": "https://outside.example.invalid/"},
        )
        self.assertRedirects(response, reverse("dashboard"))

        # Same-host absolute URL and root login URL as next.
        client = Client()
        response = client.post(
            reverse("login"),
            {"email": self.admin.email, "password": self.password, "next": "http://testserver/empleados/"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "http://testserver/empleados/")

        client = Client()
        response = client.post(
            reverse("login"),
            {"email": self.admin.email, "password": self.password, "next": reverse("login")},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], reverse("login"))
        self.assertRedirects(client.get(reverse("login")), reverse("dashboard"))

        # Non-existent local destination redirects to the local path, which then returns 404 safely.
        client = Client()
        missing_path = "/ruta-inexistente-aud01/"
        response = client.post(
            reverse("login"),
            {"email": self.admin.email, "password": self.password, "next": missing_path},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], missing_path)
        not_found = client.get(missing_path)
        self.assertEqual(not_found.status_code, 404)
        self.assertFalse(self.password in not_found.content.decode())
        self.assertEqual(client.get(reverse("dashboard")).status_code, 200)

    def test_already_authenticated_get_and_post_redirect_to_dashboard_ignoring_next(self):
        self.client.force_login(self.admin)
        get_resp = self.client.get(f"{reverse('login')}?next={reverse('employee-list')}")
        self.assertRedirects(get_resp, reverse("dashboard"))
        post_resp = self.client.post(
            f"{reverse('login')}?next={reverse('employee-list')}",
            {"email": self.admin.email, "password": self.wrong_password, "next": reverse("employee-list")},
        )
        self.assertRedirects(post_resp, reverse("dashboard"))
        self.assertEqual(LoginAttempt.objects.count(), 0)

    def test_unicode_casefold_and_idn_email_normalization_boundaries(self):
        # Non-ASCII local parts (RFC 6531 / EAI) are rejected by Django's EmailValidator before service/LoginAttempt.
        for non_ascii_local in ("josé.audit01@example.invalid", "straße@example.invalid"):
            resp = self.post(email=non_ascii_local, password=self.password, client=Client())
            self.assertIn("email", resp.context["form"].errors)
        self.assertEqual(LoginAttempt.objects.count(), 0)

        # Unicode whitespace (e.g. NBSP \u00a0, tabs) around valid email is stripped and authenticates the account.
        client_ws = Client()
        self.assertRedirects(
            self.post(email=f"\u00a0\t{self.admin.email.upper()}\u00a0", client=client_ws),
            reverse("dashboard"),
        )
        self.assertEqual(client_ws.session["_auth_user_id"], str(self.admin.pk))

        # IDN domain with accented characters and German ß: accepted by EmailValidator; casefold() normalizes domain.
        idn_account = Account.objects.create_user(
            "usuario@münchen.invalid", self.password,
            display_name="AUD01 IDN", role=self.admin.role,
        )
        client_idn = Client()
        self.assertRedirects(self.post(email="  USUARIO@MÜNCHEN.INVALID  ", client=client_idn), reverse("dashboard"))
        self.assertEqual(client_idn.session["_auth_user_id"], str(idn_account.pk))

        eszett_domain = Account.objects.create_user(
            "usuario@straße.invalid", self.password,
            display_name="AUD01 Eszett Domain", role=self.admin.role,
        )
        self.assertEqual(eszett_domain.email_normalized, "usuario@strasse.invalid")
        client_eszett = Client()
        self.assertRedirects(self.post(email="USUARIO@STRASSE.INVALID", client=client_eszett), reverse("dashboard"))
        self.assertEqual(client_eszett.session["_auth_user_id"], str(eszett_domain.pk))

        # IDN Unicode domain vs punycode domain: both pass EmailValidator, but normalize_email does not apply IDNA.
        idn_unicode = "otro@münchen.invalid"
        idn_punycode = "otro@xn--mnchen-3ya.invalid"
        for variant in (idn_unicode, idn_punycode):
            resp = self.post(email=variant, password=self.wrong_password, client=Client())
            self.assertEqual(list(resp.context["form"].non_field_errors()), [INVALID_CREDENTIALS_MESSAGE])
        self.assertNotEqual(Account.normalize_email(idn_unicode), Account.normalize_email(idn_punycode))
        self.assertEqual(self.attempt(idn_unicode).failures, 1)
        self.assertEqual(self.attempt(idn_punycode).failures, 1)

    def test_whitespace_only_email_vs_whitespace_only_password_and_long_password_no_truncation(self):
        # Whitespace-only email is stripped by EmailField and rejected as required without touching LoginAttempt.
        resp_email_ws = self.post(email="     ", password=self.password)
        self.assertIn("email", resp_email_ws.context["form"].errors)
        self.assertEqual(LoginAttempt.objects.count(), 0)

        # Whitespace-only password is kept (strip=False), reaches service, and counts as 1 failed attempt.
        resp_pwd_ws = self.post(email=self.admin.email, password="     ")
        self.assertEqual(list(resp_pwd_ws.context["form"].non_field_errors()), [INVALID_CREDENTIALS_MESSAGE])
        self.assertEqual(self.attempt(self.admin.email).failures, 1)

        # Long password (>72 bytes) is not truncated by LoginForm or Argon2.
        long_prefix = "A" * 90 + "1b!"
        long_pwd_1 = long_prefix + "X99"
        long_pwd_2 = long_prefix + "Y99"
        self.admin.set_password(long_pwd_1)
        self.admin.save(update_fields=["password"])
        self.assertContains(self.post(password=long_pwd_2), INVALID_CREDENTIALS_MESSAGE)
        self.assertRedirects(self.post(password=long_pwd_1), reverse("dashboard"))

    def test_second_complete_lockout_cycle_after_expiration(self):
        self.lock()
        second_base = self.base_time + timedelta(minutes=15)
        with patch("identity.services.timezone.now", return_value=second_base):
            for index in range(1, 6):
                response = self.post(password=self.wrong_password)
                attempt = self.attempt()
                self.assertEqual(attempt.failures, index)
                if index < 5:
                    self.assertIsNone(attempt.locked_until)
                    self.assertEqual(list(response.context["form"].non_field_errors()), [INVALID_CREDENTIALS_MESSAGE])
                else:
                    self.assertEqual(attempt.locked_until, second_base + timedelta(minutes=15))
                    self.assertContains(response, "15 minuto(s)")

    def test_identity_routes_authorization_and_method_boundaries(self):
        target = self.accounts[Role.Code.SELLER]
        edit_url = reverse("employee-edit", args=[target.pk])
        deact_url = reverse("employee-deactivate", args=[target.pk])
        protected = (
            ("GET", reverse("dashboard")),
            ("GET", reverse("logout")),
            ("POST", reverse("logout")),
            ("GET", reverse("employee-list")),
            ("GET", reverse("employee-create")),
            ("POST", reverse("employee-create")),
            ("GET", edit_url),
            ("POST", edit_url),
            ("POST", deact_url),
        )
        before = list(Account.objects.order_by("pk").values("pk", "email", "display_name", "role_id", "is_active"))
        for method, path in protected:
            anon = Client()
            resp = anon.get(path) if method == "GET" else anon.post(path, {})
            self.assertEqual(resp.status_code, 302)
            self.assertEqual(resp.headers["Location"], f"{reverse('login')}?next={path}")

        for role in (Role.Code.WAREHOUSE, Role.Code.SELLER):
            client = Client()
            client.force_login(self.accounts[role])
            for method, path in (
                ("GET", reverse("employee-list")),
                ("GET", reverse("employee-create")),
                ("POST", reverse("employee-create")),
                ("GET", edit_url),
                ("POST", edit_url),
                ("GET", deact_url),
                ("POST", deact_url),
            ):
                resp = client.get(path) if method == "GET" else client.post(path, {"display_name": "MUTATED"})
                self.assertEqual(resp.status_code, 403)
                self.assertNotContains(resp, self.inactive.email, status_code=403)

        after = list(Account.objects.order_by("pk").values("pk", "email", "display_name", "role_id", "is_active"))
        self.assertEqual(before, after)

        # Method restrictions on identity routes for authorized actor.
        admin_client = Client()
        admin_client.force_login(self.admin)
        self.assertEqual(admin_client.post(reverse("dashboard"), {}).status_code, 405)
        self.assertEqual(admin_client.put(reverse("logout"), {}).status_code, 405)
        self.assertEqual(admin_client.post(reverse("employee-list"), {}).status_code, 405)
        self.assertEqual(admin_client.get(deact_url).status_code, 405)
        self.assertEqual(Client().delete(reverse("login")).status_code, 405)

    def test_admin_login_surface_rejects_nonstaff_rejects_unnormalized_email_and_shares_session(self):
        staff = Account.objects.create_user(
            "staff.audit01@example.invalid", self.password,
            display_name="AUD01 Staff", role=self.admin.role, is_staff=True,
        )
        # Non-staff commercial roles and inactive account cannot authenticate on /admin/login/.
        for account in (*self.accounts.values(), self.inactive):
            client = Client()
            resp = client.post("/admin/login/?next=/admin/", {
                "username": account.email, "password": self.password, "next": "/admin/",
            })
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("_auth_user_id", client.session)
        self.assertEqual(LoginAttempt.objects.count(), 0)

        # ModelBackend does not normalize uppercase/whitespace email on /admin/login/.
        client_upper = Client()
        resp_upper = client_upper.post("/admin/login/?next=/admin/", {
            "username": f"  {staff.email.upper()}  ", "password": self.password, "next": "/admin/",
        })
        self.assertEqual(resp_upper.status_code, 200)
        self.assertNotIn("_auth_user_id", client_upper.session)

        # Lock staff on public login `/`, then log in via `/admin/login/`; session also accesses `/inicio/`.
        self.lock(email=staff.email, client=Client())
        admin_client = Client()
        resp_ok = admin_client.post("/admin/login/?next=/admin/", {
            "username": staff.email, "password": self.password, "next": "/admin/",
        })
        self.assertEqual(resp_ok.status_code, 302)
        self.assertEqual(resp_ok.headers["Location"], "/admin/")
        self.assertRedirects(admin_client.get(reverse("login")), reverse("dashboard"))
        self.assertEqual(admin_client.get(reverse("dashboard")).status_code, 200)

    def test_logging_redact_filter_redacts_message_keys_and_documents_exc_info_boundary(self):
        import logging
        from app_platform.logging import RedactSensitiveDataFilter

        filt = RedactSensitiveDataFilter()
        record = logging.LogRecord(
            name="audit01", level=logging.ERROR, pathname=__file__, lineno=1,
            msg="login password=%s csrfmiddlewaretoken=%s sessionid=%s Authorization: Bearer %s",
            args=(self.password, "tok123", "sess123", "jwt123"), exc_info=None,
        )
        self.assertTrue(filt.filter(record))
        formatted = logging.Formatter().format(record)
        self.assertFalse(self.password in formatted)
        self.assertNotIn("tok123", formatted)
        self.assertNotIn("sess123", formatted)
        self.assertNotIn("jwt123", formatted)
        self.assertIn("[REDACTED]", formatted)

    def test_unusable_password_follows_uniform_five_failure_lockout(self):
        self.admin.set_unusable_password()
        self.admin.save(update_fields=["password"])
        self.assertFalse(self.admin.has_usable_password())

        with patch("identity.services.timezone.now", return_value=self.base_time):
            for index in range(1, 6):
                response = self.post()
                self.assertEqual(response.status_code, 200)
                expected = (
                    INVALID_CREDENTIALS_MESSAGE if index < 5 else
                    "Demasiados intentos fallidos consecutivos. Inténtelo nuevamente en 15 minuto(s)."
                )
                self.assertEqual(list(response.context["form"].non_field_errors()), [expected])
                self.assertNotIn("_auth_user_id", self.client.session)
                self.assertEqual(self.attempt().failures, index)

        self.admin.refresh_from_db()
        self.assertFalse(self.admin.has_usable_password())
        self.assertIsNone(self.admin.last_login)
        self.assertEqual(self.attempt().locked_until, self.base_time + timedelta(minutes=15))
        self.assertEqual(LoginAttempt.objects.count(), 1)

    def test_legacy_pbkdf2_account_accepts_normalized_login_after_failure(self):
        from django.contrib.auth.hashers import identify_hasher, make_password

        self.admin.password = make_password(self.password, hasher="pbkdf2_sha256")
        self.admin.save(update_fields=["password"])
        self.assertEqual(identify_hasher(self.admin.password).algorithm, "pbkdf2_sha256")

        failed = self.post(password=self.wrong_password)
        self.assertEqual(list(failed.context["form"].non_field_errors()), [INVALID_CREDENTIALS_MESSAGE])
        self.assertNotIn("_auth_user_id", self.client.session)
        attempt = self.attempt()
        self.assertEqual(attempt.failures, 1)
        self.assertIsNone(attempt.locked_until)
        self.admin.refresh_from_db()
        self.assertIsNone(self.admin.last_login)

        accepted = self.post(email=f"  {self.admin.email.upper()}  ")
        self.assertRedirects(accepted, reverse("dashboard"))
        self.admin.refresh_from_db()
        self.assertIsNotNone(self.admin.last_login)
        persisted_session = Session.objects.get(session_key=self.client.session.session_key).get_decoded()
        self.assertEqual(persisted_session["_auth_user_id"], str(self.admin.pk))
        self.assertEqual(persisted_session["role_code"], Role.Code.ADMIN)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
        attempt.refresh_from_db()
        self.assertEqual(attempt.failures, 0)
        self.assertIsNone(attempt.locked_until)
        self.assertEqual(LoginAttempt.objects.count(), 1)


