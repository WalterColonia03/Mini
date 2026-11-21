from __future__ import annotations

from django.contrib.auth.hashers import identify_hasher
from django.test import Client, TestCase
from django.urls import reverse

from .models import Account, Role
from .services import INVALID_CREDENTIALS_MESSAGE


class AuthenticationAndAuthorizationTests(TestCase):
    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
        cls.admin = Account.objects.create_user(
            "admin@test.invalid", cls.password, display_name="Admin", role=cls.admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "warehouse@test.invalid", cls.password, display_name="Almacén", role=cls.warehouse_role
        )
        cls.seller = Account.objects.create_user(
            "seller@test.invalid", cls.password, display_name="Vendedor", role=cls.seller_role
        )
        cls.inactive = Account.objects.create_user(
            "inactive@test.invalid", cls.password, display_name="Inactiva", role=cls.admin_role, is_active=False
        )

    def login(self, email: str, password: str | None = None):
        return self.client.post(reverse("login"), {"email": email, "password": password or self.password})

    def test_unknown_existing_role_cannot_log_in_or_access_dashboard(self) -> None:
        old_role = Role.objects.create(code="ANTIGUO", name="Rol antiguo")
        old_account = Account.objects.create_user(
            "old@test.invalid", self.password, display_name="Cuenta antigua", role=old_role
        )
        response = self.login(old_account.email)
        self.assertContains(response, INVALID_CREDENTIALS_MESSAGE)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.client.force_login(old_account)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("employee-edit", args=[old_account.pk])).status_code, 404)

    def test_active_account_creates_server_session(self) -> None:
        response = self.login(" ADMIN@TEST.INVALID ")
        self.assertRedirects(response, reverse("dashboard"))
        self.assertEqual(str(self.client.session["_auth_user_id"]), str(self.admin.pk))
        self.assertEqual(self.client.session["role_code"], Role.Code.ADMIN)

    def test_login_rotates_an_existing_anonymous_session_key(self) -> None:
        session = self.client.session
        session["pre_auth_marker"] = "kept"
        session.save()
        previous_key = session.session_key

        response = self.login(self.admin.email)

        self.assertRedirects(response, reverse("dashboard"))
        self.assertNotEqual(self.client.session.session_key, previous_key)
        self.assertEqual(self.client.session["pre_auth_marker"], "kept")

    def test_password_uses_argon2_and_is_never_stored_in_plain_text(self) -> None:
        self.assertNotIn(self.password, self.admin.password)
        self.assertEqual(identify_hasher(self.admin.password).algorithm, "argon2")

    def test_login_post_requires_csrf_and_sets_protected_cookies(self) -> None:
        csrf_client = Client(enforce_csrf_checks=True)
        rejected = csrf_client.post(
            reverse("login"), {"email": self.admin.email, "password": self.password}
        )
        self.assertEqual(rejected.status_code, 403)
        self.assertNotIn("_auth_user_id", csrf_client.session)

        form_response = csrf_client.get(reverse("login"))
        csrf_cookie = form_response.cookies["csrftoken"]
        accepted = csrf_client.post(
            reverse("login"),
            {
                "email": self.admin.email,
                "password": self.password,
                "csrfmiddlewaretoken": csrf_cookie.value,
            },
        )

        self.assertRedirects(accepted, reverse("dashboard"))
        self.assertTrue(csrf_cookie["httponly"])
        self.assertEqual(csrf_cookie["samesite"], "Lax")
        self.assertTrue(accepted.cookies["sessionid"]["httponly"])
        self.assertEqual(accepted.cookies["sessionid"]["samesite"], "Lax")

    def test_login_does_not_show_internal_access_copy(self) -> None:
        response = self.client.get(reverse("login"))

        self.assertContains(response, 'data-testid="login-form"')
        for removed_copy in (
            "Ingreso y personal",
            "Ingresa con tu cuenta de trabajo",
            "Accede a las opciones de tu puesto",
            "Cuenta activa",
            "Un rol de trabajo",
            "Datos ficticios controlados",
        ):
            with self.subTest(removed_copy=removed_copy):
                self.assertNotContains(response, removed_copy)

    def test_invalid_email_is_rejected_before_authentication(self) -> None:
        response = self.login("not-an-email")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Introduzca una dirección de correo electrónico válida")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_unknown_email_wrong_password_and_inactive_account_share_message(self) -> None:
        cases = [
            ("unknown@test.invalid", self.password),
            (self.admin.email, "incorrecta"),
            (self.inactive.email, self.password),
        ]
        for email, password in cases:
            with self.subTest(email=email):
                response = self.login(email, password)
                self.assertContains(response, INVALID_CREDENTIALS_MESSAGE)
                self.assertNotIn("_auth_user_id", self.client.session)

    def test_dashboard_only_shows_authorized_navigation(self) -> None:
        self.client.force_login(self.seller)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Abrir turno")
        self.assertContains(response, "Preparar venta")
        self.assertNotContains(response, "Registrar producto")
        self.assertNotContains(response, "Carga inicial")

    def test_sidebar_limits_each_role_to_its_current_operation(self) -> None:
        cases = (
            (self.admin, "Registrar producto", "product-entry", ("Existencias iniciales", "Apertura de caja")),
            (self.warehouse, "Existencias iniciales", "inventory-load", ("Registrar producto", "Apertura de caja")),
            (self.seller, "Apertura de caja", "cash-open", ("Registrar producto", "Existencias iniciales")),
        )

        for account, operation_label, route_name, unavailable_labels in cases:
            with self.subTest(role=account.role.code):
                self.client.force_login(account)
                response = self.client.get(reverse("dashboard"))

                self.assertContains(response, operation_label)
                self.assertContains(response, f'href="{reverse(route_name)}"')
                if account.role.code == Role.Code.SELLER:
                    self.assertContains(response, f'href="{reverse("sales-draft")}"')
                else:
                    self.assertNotContains(response, f'href="{reverse("sales-draft")}"')
                for unavailable_label in unavailable_labels:
                    self.assertNotContains(response, unavailable_label)

    def test_dashboard_does_not_expose_planning_identifiers(self) -> None:
        self.client.force_login(self.admin)

        response = self.client.get(reverse("dashboard"))

        self.assertContains(response, "Operaciones autorizadas")
        for internal_label in ("HU-", "SCRUM", "Sprint", "corte"):
            with self.subTest(internal_label=internal_label):
                self.assertNotContains(response, internal_label)

    def test_sales_preparation_page_does_not_expose_planning_identifiers(self) -> None:
        self.client.force_login(self.seller)

        response = self.client.get(reverse("sales-draft"))

        self.assertContains(response, "Abre tu turno para preparar una venta")
        for internal_label in ("HU-", "SCRUM", "Sprint", "PostgreSQL", "segunda semana"):
            with self.subTest(internal_label=internal_label):
                self.assertNotContains(response, internal_label)

    def test_direct_operation_is_denied_without_mutating_data(self) -> None:
        self.client.force_login(self.warehouse)
        before = Account.objects.count()
        response = self.client.get(reverse("product-entry"))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Account.objects.count(), before)

    def test_anonymous_protected_route_redirects_to_the_public_login(self) -> None:
        response = self.client.get(reverse("product-entry"))

        self.assertRedirects(response, f"{reverse('login')}?next={reverse('product-entry')}")

    def test_role_matrix_is_enforced_on_direct_urls(self) -> None:
        routes = {
            Role.Code.ADMIN: "product-entry",
            Role.Code.WAREHOUSE: "inventory-load",
            Role.Code.SELLER: "cash-open",
        }
        users = {
            Role.Code.ADMIN: self.admin,
            Role.Code.WAREHOUSE: self.warehouse,
            Role.Code.SELLER: self.seller,
        }
        for allowed_role, route_name in routes.items():
            for current_role, account in users.items():
                with self.subTest(route=route_name, current_role=current_role):
                    self.client.force_login(account)
                    response = self.client.get(reverse(route_name))
                    self.assertEqual(response.status_code, 200 if current_role == allowed_role else 403)

        for current_role, account in users.items():
            with self.subTest(route="sales-draft", current_role=current_role):
                self.client.force_login(account)
                response = self.client.get(reverse("sales-draft"))
                self.assertEqual(response.status_code, 200 if current_role == Role.Code.SELLER else 403)

    def test_post_logout_invalidates_session_and_back_route_requires_login(self) -> None:
        self.client.force_login(self.seller)
        response = self.client.post(reverse("logout"))
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)
        response = self.client.get(reverse("sales-draft"))
        self.assertEqual(response.status_code, 302)


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 2 — HU-USR-01 y HU-USR-02
# ═══════════════════════════════════════════════════════════════════════════════

class EmployeeManagementTests(TestCase):
    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Admin Emp")
        cls.seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor Emp")
        cls.warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero Emp")
        cls.admin = Account.objects.create_user(
            "adminemp@test.invalid", cls.password, display_name="Admin", role=cls.admin_role
        )
        cls.seller = Account.objects.create_user(
            "selleremp@test.invalid", cls.password, display_name="Seller", role=cls.seller_role
        )

    def _create_payload(self, **overrides):
        data = {
            "display_name": "Juan Pérez",
            "email": "juan@test.invalid",
            "password": "SecureP4ss!",
            "role": str(self.seller_role.pk),
        }
        data.update(overrides)
        return data

    # ── HU-USR-01 ·  Lista de empleados ──

    def test_admin_can_see_employee_list(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("employee-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin")

    def test_non_admin_gets_403_on_employee_list(self) -> None:
        self.client.force_login(self.seller)
        self.assertEqual(self.client.get(reverse("employee-list")).status_code, 403)

    # ── HU-USR-02 · Crear empleado ──

    def test_admin_creates_employee_successfully(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(reverse("employee-create"), self._create_payload())
        self.assertRedirects(response, reverse("employee-list"))
        self.assertTrue(Account.objects.filter(email_normalized="juan@test.invalid").exists())

    def test_duplicate_email_is_rejected(self) -> None:
        self.client.force_login(self.admin)
        # Crear primero
        self.client.post(reverse("employee-create"), self._create_payload(email="dup@test.invalid"))
        # Intentar duplicado
        response = self.client.post(reverse("employee-create"), self._create_payload(email="dup@test.invalid"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Account.objects.filter(email_normalized="dup@test.invalid").count(), 1)

    def test_non_admin_post_is_forbidden(self) -> None:
        self.client.force_login(self.seller)
        response = self.client.post(reverse("employee-create"), self._create_payload())
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Account.objects.filter(email_normalized="juan@test.invalid").exists())


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 3 — HU-USR-03 y HU-USR-04 · Editar y desactivar empleados
# ═══════════════════════════════════════════════════════════════════════════════

class EmployeeEditDeactivateTests(TestCase):
    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Admin ED")
        cls.seller_role = Role.objects.create(code=Role.Code.SELLER, name="Seller ED")
        cls.warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="WH ED")
        cls.admin = Account.objects.create_user(
            "admined@test.invalid", cls.password, display_name="Admin ED", role=cls.admin_role
        )
        cls.seller = Account.objects.create_user(
            "sellered@test.invalid", cls.password, display_name="Seller ED", role=cls.seller_role
        )

    # ── HU-USR-03 · Editar ──

    def test_admin_can_access_employee_edit_form(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("employee-edit", args=(self.seller.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seller ED")

    def test_admin_can_edit_employee_name(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("employee-edit", args=(self.seller.pk,)),
            {
                "display_name": "Seller Editado",
                "email": self.seller.email,
                "role": str(self.seller_role.pk),
            },
        )
        self.assertRedirects(response, reverse("employee-list"))
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.display_name, "Seller Editado")

    def test_duplicate_email_is_rejected_on_edit(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("employee-edit", args=(self.seller.pk,)),
            {
                "display_name": "Seller ED",
                "email": self.admin.email,  # correo ya tomado
                "role": str(self.seller_role.pk),
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_non_admin_gets_403_on_edit(self) -> None:
        self.client.force_login(self.seller)
        self.assertEqual(
            self.client.get(reverse("employee-edit", args=(self.seller.pk,))).status_code, 403
        )

    # ── HU-USR-04 · Desactivar / Reactivar ──

    def test_admin_can_deactivate_employee(self) -> None:
        # Crear empleado temporal para desactivar sin afectar otros tests
        wh = Account.objects.create_user(
            "whtemp@test.invalid", self.password, display_name="WH Temp", role=self.warehouse_role
        )
        self.client.force_login(self.admin)
        response = self.client.post(reverse("employee-deactivate", args=(wh.pk,)), {"action": "desactivar"})
        self.assertRedirects(response, reverse("employee-list"))
        wh.refresh_from_db()
        self.assertFalse(wh.is_active)

    def test_admin_cannot_deactivate_self(self) -> None:
        self.client.force_login(self.admin)
        # Intento de desactivar su propia cuenta — debe fallar con mensaje de error
        response = self.client.post(reverse("employee-deactivate", args=(self.admin.pk,)), {"action": "desactivar"})
        self.assertRedirects(response, reverse("employee-list"))
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)  # sigue activo

    def test_admin_can_reactivate_inactive_employee(self) -> None:
        wh2 = Account.objects.create_user(
            "wh2temp@test.invalid", self.password, display_name="WH2 Temp",
            role=self.warehouse_role, is_active=False
        )
        self.client.force_login(self.admin)
        self.client.post(reverse("employee-deactivate", args=(wh2.pk,)), {"action": "reactivar"})
        wh2.refresh_from_db()
        self.assertTrue(wh2.is_active)

    def test_non_admin_gets_403_on_deactivate(self) -> None:
        self.client.force_login(self.seller)
        self.assertEqual(
            self.client.post(reverse("employee-deactivate", args=(self.admin.pk,))).status_code, 403
        )

    def test_admin_cannot_change_own_role(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("employee-edit", args=(self.admin.pk,)),
            {
                "display_name": self.admin.display_name,
                "email": self.admin.email,
                "role": str(self.seller_role.pk),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No puedes cambiar el rol de tu propia cuenta")
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.role, self.admin_role)

    def test_cannot_deactivate_seller_with_open_shift(self) -> None:
        from decimal import Decimal
        from cash.models import CashRegister, CashShift

        reg = CashRegister.objects.create(code="CAJA-EMP-TEST")
        shift = CashShift.objects.create(
            cash_register=reg, seller=self.seller, opening_amount=Decimal("20.00")
        )
        self.client.force_login(self.admin)
        response = self.client.post(reverse("employee-deactivate", args=(self.seller.pk,)), {"action": "desactivar"}, follow=True)
        self.assertContains(response, "No se puede desactivar a un vendedor con un turno de caja abierto")
        self.seller.refresh_from_db()
        self.assertTrue(self.seller.is_active)
        shift.delete()

    def test_five_failed_login_attempts_block_further_attempts(self) -> None:
        for _ in range(5):
            self.client.post(reverse("login"), {"email": self.admin.email, "password": "wrong-password"})
        blocked = self.client.post(reverse("login"), {"email": self.admin.email, "password": self.password})
        self.assertEqual(blocked.status_code, 200)
        self.assertContains(blocked, "Demasiados intentos fallidos consecutivos")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_honors_safe_next_parameter(self) -> None:
        target = reverse("employee-list")
        response = self.client.post(
            f"{reverse('login')}?next={target}",
            {"email": self.admin.email, "password": self.password, "next": target},
        )
        self.assertRedirects(response, target)

    def test_cannot_change_role_of_seller_with_open_shift(self) -> None:
        """BUG-001: No se puede cambiar el rol de un vendedor con turno de caja abierto."""
        from decimal import Decimal
        from cash.models import CashRegister, CashShift

        reg = CashRegister.objects.create(code="CAJA-ROLE-LOCK")
        shift = CashShift.objects.create(
            cash_register=reg, seller=self.seller, opening_amount=Decimal("25.00")
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("employee-edit", args=(self.seller.pk,)),
            {
                "display_name": self.seller.display_name,
                "email": self.seller.email,
                "role": str(self.warehouse_role.pk),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No se puede cambiar el rol de un empleado con un turno de caja abierto")
        self.seller.refresh_from_db()
        self.assertEqual(self.seller.role, self.seller_role)
        shift.delete()

    def test_dashboard_for_admin_and_warehouse_includes_expired_lots_and_single_h1(self) -> None:
        """BUG-016 y BUG-023: /inicio/ muestra lotes vencidos a Admin y Almacenero y un único <h1>."""
        wh = Account.objects.create_user(
            "wh_dash@test.invalid", self.password, display_name="WH Dash", role=self.warehouse_role
        )
        for user in (self.admin, wh):
            with self.subTest(role=user.role.code):
                self.client.force_login(user)
                response = self.client.get(reverse("dashboard"))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Lotes vencidos con stock")
                html = response.content.decode("utf-8")
                self.assertEqual(html.count("<h1"), 1)

    def test_logout_confirm_shows_minimarket_title_and_draft_warning_for_seller(self) -> None:
        """BUG-017 y BUG-020: /salir/ muestra marca Minimarket y advierte descarte de borrador."""
        self.client.force_login(self.seller)
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cerrar sesión · Minimarket")
        self.assertContains(response, "venta en preparación")

    def test_employee_list_does_not_render_broken_bootstrap_dismiss_button(self) -> None:
        """BUG-019: /empleados/ no renderiza botones huérfanos data-bs-dismiss."""
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("employee-edit", args=(self.seller.pk,)),
            {
                "display_name": "Seller Sin Boton Roto",
                "email": self.seller.email,
                "role": str(self.seller_role.pk),
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'data-bs-dismiss="alert"')

    def test_login_lock_expires_after_fifteen_minutes(self) -> None:
        """El bloqueo afecta al correo, incluso si se cambia de navegador."""
        from datetime import timedelta
        from django.utils import timezone
        from .models import LoginAttempt

        for _ in range(5):
            self.client.post(
                reverse("login"),
                {"email": self.admin.email, "password": "WrongPassword!999"},
            )
        attempt = LoginAttempt.objects.get()
        self.assertGreater(attempt.locked_until, timezone.now() + timedelta(minutes=14))
        new_client = Client()
        blocked = new_client.post(reverse("login"), {"email": self.admin.email.upper(), "password": self.password})
        self.assertContains(blocked, "Demasiados intentos fallidos consecutivos")
        self.assertNotIn("_auth_user_id", new_client.session)
        attempt.locked_until = timezone.now() - timedelta(seconds=10)
        attempt.save()

        response = self.client.post(
            reverse("login"),
            {"email": self.admin.email, "password": self.password},
        )
        self.assertRedirects(response, reverse("dashboard"))

    def test_unknown_identifier_has_the_same_lock_response(self) -> None:
        for email in (self.admin.email, "unknown@test.invalid"):
            client = Client()
            for _ in range(4):
                response = client.post(reverse("login"), {"email": email, "password": "WrongPassword!999"})
                self.assertContains(response, INVALID_CREDENTIALS_MESSAGE)
            response = client.post(reverse("login"), {"email": email, "password": "WrongPassword!999"})
            self.assertContains(response, "Demasiados intentos fallidos consecutivos")
            self.assertContains(response, "15 minuto(s)")

    def test_success_resets_counter_without_deleting_throttle_row(self) -> None:
        from .models import LoginAttempt

        self.client.post(reverse("login"), {"email": self.admin.email, "password": "incorrecta"})
        attempt = LoginAttempt.objects.get()
        response = self.client.post(reverse("login"), {"email": self.admin.email, "password": self.password})
        self.assertRedirects(response, reverse("dashboard"))
        attempt.refresh_from_db()
        self.assertEqual(attempt.failures, 0)
        self.assertIsNone(attempt.locked_until)

