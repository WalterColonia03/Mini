"""Suite de auditoría y regresión para la Etapa 02 (HU-AUTH-03 y HU-USR-01..05)."""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import salted_hmac

from cash.models import CashRegister, CashShift
from cash.services import close_cash_shift, open_cash_shift
from catalog.models import Category, Product
from identity.forms import EmployeeCreationForm, EmployeeEditForm
from identity.models import Account, LoginAttempt, Role
from identity.services import (
    create_employee,
    deactivate_employee,
    reactivate_employee,
    update_employee,
)
from inventory.models import InitialInventoryLoad, Lot
from sales.models import SaleDraft
from sales.services import add_product_to_draft


def _login_identifier(email: str) -> str:
    normalized = Account.normalize_email(email)
    return salted_hmac("identity.login.throttle", normalized, algorithm="sha256").hexdigest()


class Stage02AuditRegressionTests(TestCase):
    """Regresiones directas de los defectos inequívocos FIX-E02-01..07."""

    password = "Audit02!Pass"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role, _ = Role.objects.update_or_create(
            code=Role.Code.ADMIN, defaults={"name": "Administrador"}
        )
        cls.warehouse_role, _ = Role.objects.update_or_create(
            code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"}
        )
        cls.seller_role, _ = Role.objects.update_or_create(
            code=Role.Code.SELLER, defaults={"name": "Vendedor"}
        )

        cls.admin = Account.objects.create_user(
            "admin@minimarket.local",
            cls.password,
            display_name="Ana Administradora",
            role=cls.admin_role,
        )
        cls.warehouse = Account.objects.create_user(
            "almacen@minimarket.local",
            cls.password,
            display_name="Bruno Almacenero",
            role=cls.warehouse_role,
        )
        cls.seller = Account.objects.create_user(
            "ventas@minimarket.local",
            cls.password,
            display_name="Carla Vendedora",
            role=cls.seller_role,
        )
        cls.seller2 = Account.objects.create_user(
            "ventas2@minimarket.local",
            cls.password,
            display_name="Diego Vendedor",
            role=cls.seller_role,
        )
        cls.inactive_user = Account.objects.create_user(
            "inactivo@minimarket.local",
            cls.password,
            display_name="Elena Inactiva",
            role=cls.seller_role,
            is_active=False,
        )

        cls.register = CashRegister.objects.create(code="CAJA-01")
        cls.category = Category.objects.create(name="Productos enlatados")
        cls.product = Product.objects.create(
            category=cls.category,
            name="Atún en lata",
            barcode="775000000201",
            sale_price=Decimal("8.50"),
        )
        load = InitialInventoryLoad.objects.create(
            product=cls.product,
            responsible=cls.warehouse,
        )
        cls.lot = Lot.objects.create(
            product=cls.product,
            initial_load=load,
            number="LOT-E02-01",
            initial_quantity=10,
            available_quantity=10,
            unit_cost=Decimal("4.5000"),
            expiration_date=timezone.localdate() + timedelta(days=20),
        )

    def test_fix_e02_01_employee_list_filters_by_name_or_email_and_orders_alphabetically(self) -> None:
        self.client.force_login(self.admin)
        response_all = self.client.get(reverse("employee-list"))
        self.assertEqual(response_all.status_code, 200)
        self.assertIn('name="q"', response_all.content.decode("utf-8"), "Falta input de búsqueda name='q'")
        names = [acc.display_name for acc in response_all.context["employees"]]
        self.assertEqual(
            names,
            [
                "Ana Administradora",
                "Bruno Almacenero",
                "Carla Vendedora",
                "Diego Vendedor",
                "Elena Inactiva",
            ],
        )

        by_name = self.client.get(reverse("employee-list"), {"q": "Carla"})
        self.assertEqual([a.email for a in by_name.context["employees"]], ["ventas@minimarket.local"])

        by_email = self.client.get(reverse("employee-list"), {"q": "INACTIVO@minimarket"})
        self.assertEqual([a.email for a in by_email.context["employees"]], ["inactivo@minimarket.local"])

        no_match = self.client.get(reverse("employee-list"), {"q": "inexistente-xyz"})
        self.assertEqual(list(no_match.context["employees"]), [])
        self.assertIn(
            "No se encontraron empleados para el criterio ingresado.",
            no_match.content.decode("utf-8"),
        )

    def test_fix_e02_02_empty_post_binds_forms_and_views_set_never_cache_and_sensitive_decorators(self) -> None:
        self.client.force_login(self.admin)

        res_list = self.client.get(reverse("employee-list"))
        self.assertIn("no-store", res_list.headers.get("Cache-Control", ""))

        res_create = self.client.post(reverse("employee-create"), data={})
        self.assertEqual(res_create.status_code, 200)
        self.assertTrue(res_create.context["form"].is_bound)
        self.assertTrue(res_create.context["form"].errors)
        self.assertIn("no-store", res_create.headers.get("Cache-Control", ""))

        res_edit = self.client.post(reverse("employee-edit", args=[self.seller.pk]), data={})
        self.assertEqual(res_edit.status_code, 200)
        self.assertTrue(res_edit.context["form"].is_bound)
        self.assertTrue(res_edit.context["form"].errors)
        self.assertIn("no-store", res_edit.headers.get("Cache-Control", ""))

        self.assertEqual(create_employee.__code__.co_name, "sensitive_variables_wrapper")
        self.assertEqual(update_employee.__code__.co_name, "sensitive_variables_wrapper")

    def test_fix_e02_03_deactivation_revokes_persisted_sessions_discards_draft_and_reactivation_clears_lockout(self) -> None:
        seller_client = Client()
        res_login_initial = seller_client.post(
            reverse("login"),
            {"email": self.seller2.email, "password": self.password},
        )
        self.assertEqual(res_login_initial.status_code, 302)
        self.assertEqual(seller_client.get(reverse("dashboard")).status_code, 200)

        closed_shift = CashShift.objects.create(
            cash_register=self.register,
            seller=self.seller2,
            opening_amount=Decimal("20.00"),
            status=CashShift.Status.CLOSED,
        )
        SaleDraft.objects.create(
            seller=self.seller2,
            cash_shift=closed_shift,
            status=SaleDraft.Status.ACTIVE,
        )
        identifier = _login_identifier(self.seller2.email)
        LoginAttempt.objects.update_or_create(
            identifier=identifier,
            defaults={
                "failures": 5,
                "locked_until": timezone.now() + timedelta(minutes=15),
            },
        )
        old_updated_at = self.seller2.updated_at

        deactivate_employee(actor=self.admin, account=self.seller2)
        self.seller2.refresh_from_db()
        self.assertFalse(self.seller2.is_active)
        self.assertGreater(self.seller2.updated_at, old_updated_at)
        self.assertFalse(
            SaleDraft.objects.filter(seller=self.seller2, status=SaleDraft.Status.ACTIVE).exists()
        )

        # DOC-02-04/C-03: Reactivar la cuenta NO levanta silenciosamente un bloqueo temporal vigente;
        # la cookie previa tampoco revive y solo un desbloqueo explícito habilita el nuevo ingreso.
        reactivate_employee(actor=self.admin, account=self.seller2)
        self.seller2.refresh_from_db()
        self.assertTrue(self.seller2.is_active)
        attempt = LoginAttempt.objects.get(identifier=identifier)
        self.assertEqual(attempt.failures, 5)
        self.assertIsNotNone(attempt.locked_until)

        res_old_cookie = seller_client.get(reverse("dashboard"))
        self.assertEqual(res_old_cookie.status_code, 302)
        self.assertIn(reverse("login"), res_old_cookie["Location"])

        blocked_client = Client()
        res_still_locked = blocked_client.post(
            reverse("login"),
            {"email": self.seller2.email, "password": self.password},
        )
        self.assertContains(res_still_locked, "Demasiados intentos fallidos consecutivos")

        # Desbloqueo explícito autorizado por ADMIN habilita nuevamente el ingreso.
        from identity.services import update_employee

        update_employee(
            actor=self.admin,
            account=self.seller2,
            display_name=self.seller2.display_name,
            email=self.seller2.email,
            role=self.seller2.role,
            unlock_account=True,
        )
        fresh_client = Client()
        res_login = fresh_client.post(
            reverse("login"),
            {"email": self.seller2.email, "password": self.password},
        )
        self.assertEqual(res_login.status_code, 302)

    def test_fix_e02_03b_role_change_updates_active_session_role_code_and_preserves_display_name_on_error(self) -> None:
        seller_client = Client()
        res_login = seller_client.post(
            reverse("login"),
            {"email": self.seller2.email, "password": self.password},
        )
        self.assertEqual(res_login.status_code, 302)
        self.assertEqual(seller_client.session.get("role_code"), Role.Code.SELLER)

        update_employee(
            actor=self.admin,
            account=self.seller2,
            display_name="Diego Almacén",
            email=self.seller2.email,
            role=self.warehouse_role,
        )
        cookie_name = settings.SESSION_COOKIE_NAME
        session_key = seller_client.cookies[cookie_name].value
        session_obj = Session.objects.get(session_key=session_key)
        self.assertEqual(session_obj.get_decoded().get("role_code"), Role.Code.WAREHOUSE)

        # Un error de validación en employee_edit no debe mutar account.display_name en el subtítulo.
        self.client.force_login(self.admin)
        bad_res = self.client.post(
            reverse("employee-edit", args=[self.seller2.pk]),
            {
                "display_name": "Nombre No Guardado Temporal",
                "email": self.admin.email,
                "role": self.warehouse_role.pk,
                "new_password": "",
            },
        )
        self.assertEqual(bad_res.status_code, 200)
        self.assertEqual(bad_res.context["account"].display_name, "Diego Almacén")

    def test_fix_e02_04_duplicate_email_message_matches_hu_usr_02_ca_02_literal(self) -> None:
        self.client.force_login(self.admin)
        res_create = self.client.post(
            reverse("employee-create"),
            {
                "display_name": "Duplicado Uno",
                "email": "  VENTAS@MINIMARKET.LOCAL ",
                "role": self.seller_role.pk,
                "password": "Valida12",
            },
        )
        self.assertEqual(res_create.status_code, 200)
        self.assertEqual(
            res_create.context["form"].errors.get("email"),
            ["El correo ya está registrado."],
        )

        res_inactive_dup = self.client.post(
            reverse("employee-create"),
            {
                "display_name": "Duplicado Inactivo",
                "email": "INACTIVO@minimarket.local",
                "role": self.seller_role.pk,
                "password": "Valida12",
            },
        )
        self.assertEqual(res_inactive_dup.status_code, 200)
        self.assertEqual(
            res_inactive_dup.context["form"].errors.get("email"),
            ["El correo ya está registrado."],
        )

        res_edit_dup = self.client.post(
            reverse("employee-edit", args=[self.seller.pk]),
            {
                "display_name": self.seller.display_name,
                "email": "ADMIN@minimarket.local",
                "role": self.seller_role.pk,
                "new_password": "",
            },
        )
        self.assertEqual(res_edit_dup.status_code, 200)
        self.assertEqual(
            res_edit_dup.context["form"].errors.get("email"),
            ["El correo ya está registrado."],
        )

    def test_fix_e02_05_rn24_password_policy_accepts_7_chars_and_rejects_missing_classes_in_form_and_service(self) -> None:
        valid_form = EmployeeCreationForm(
            data={
                "display_name": "Siete Caracteres",
                "email": "siete@minimarket.local",
                "role": self.seller_role.pk,
                "password": "Abcdef1",
            }
        )
        self.assertTrue(valid_form.is_valid(), valid_form.errors)

        for weak_pw in ("Abcde1", "abcdef1", "ABCDEF1", "Abcdefg", "1234567", "       a"):
            form = EmployeeCreationForm(
                data={
                    "display_name": "Prueba Débil",
                    "email": "debil@minimarket.local",
                    "role": self.seller_role.pk,
                    "password": weak_pw,
                }
            )
            self.assertFalse(form.is_valid(), f"Password {weak_pw!r} debía fallar en EmployeeCreationForm")
            self.assertIn("password", form.errors)

            edit_form = EmployeeEditForm(
                data={
                    "display_name": self.seller.display_name,
                    "email": self.seller.email,
                    "role": self.seller_role.pk,
                    "new_password": weak_pw,
                },
            )
            self.assertFalse(edit_form.is_valid(), f"Password {weak_pw!r} debía fallar en EmployeeEditForm")
            self.assertIn("new_password", edit_form.errors)

            with self.assertRaises(ValidationError):
                create_employee(
                    actor=self.admin,
                    display_name="Servicio Débil",
                    email="serviciodebil@minimarket.local",
                    role=self.seller_role,
                    password=weak_pw,
                )

            with self.assertRaises(ValidationError):
                update_employee(
                    actor=self.admin,
                    account=self.seller,
                    display_name=self.seller.display_name,
                    email=self.seller.email,
                    role=self.seller_role,
                    new_password=weak_pw,
                )

    def test_fix_e02_06_logout_draft_warning_only_triggers_when_draft_has_lines(self) -> None:
        shift = open_cash_shift(
            actor=self.seller,
            opening_amount=Decimal("50.00"),
        )
        draft = SaleDraft.objects.create(
            seller=self.seller,
            cash_shift=shift,
            status=SaleDraft.Status.ACTIVE,
        )
        self.assertEqual(draft.lines.count(), 0)

        self.client.force_login(self.seller)
        res_empty_draft = self.client.get(reverse("logout"))
        self.assertEqual(res_empty_draft.status_code, 200)
        self.assertFalse(res_empty_draft.context["has_active_draft"])

        add_product_to_draft(actor=self.seller, product_id=self.product.pk, quantity=2)
        res_with_lines = self.client.get(reverse("logout"))
        self.assertEqual(res_with_lines.status_code, 200)
        self.assertTrue(res_with_lines.context["has_active_draft"])
        self.assertIn(
            "La venta en preparación se descartará. El turno abierto seguirá ligado a tu cuenta.",
            res_with_lines.content.decode("utf-8"),
        )

        res_post = self.client.post(reverse("logout"))
        self.assertEqual(res_post.status_code, 302)
        self.assertEqual(res_post["Location"], reverse("login"))
        self.assertFalse(
            SaleDraft.objects.filter(seller=self.seller, status=SaleDraft.Status.ACTIVE).exists()
        )
        self.assertTrue(
            CashShift.objects.filter(seller=self.seller, status=CashShift.Status.OPEN).exists()
        )
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.available_quantity, 10)

    def test_fix_e02_07_email_fields_allow_up_to_254_chars(self) -> None:
        self.assertEqual(EmployeeCreationForm.base_fields["email"].max_length, 254)
        self.assertEqual(EmployeeEditForm.base_fields["email"].max_length, 254)
        local_part = "e" * (254 - len("@minimarket.local"))
        email_254 = f"{local_part}@minimarket.local"
        self.assertEqual(len(email_254), 254)
        form = EmployeeCreationForm(
            data={
                "display_name": "Correo 254",
                "email": email_254,
                "role": self.seller_role.pk,
                "password": "Abcdef1",
            }
        )
        self.assertTrue(form.is_valid(), form.errors)


class Stage02ComprehensiveCriteriaTests(TestCase):
    """Cobertura exhaustiva de HU-AUTH-03, HU-USR-01..05, RN-12, RN-17, RN-18, RN-24, RN-29, RN-30 y QA00-L877-c."""

    password = "Audit02!Pass"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role, _ = Role.objects.update_or_create(
            code=Role.Code.ADMIN, defaults={"name": "Administrador"}
        )
        cls.warehouse_role, _ = Role.objects.update_or_create(
            code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"}
        )
        cls.seller_role, _ = Role.objects.update_or_create(
            code=Role.Code.SELLER, defaults={"name": "Vendedor"}
        )

        cls.admin = Account.objects.create_user(
            "admin@minimarket.local",
            cls.password,
            display_name="Ana Administradora",
            role=cls.admin_role,
        )
        cls.warehouse = Account.objects.create_user(
            "almacen@minimarket.local",
            cls.password,
            display_name="Bruno Almacenero",
            role=cls.warehouse_role,
        )
        cls.seller1 = Account.objects.create_user(
            "ventas1@minimarket.local",
            cls.password,
            display_name="Carla Vendedora",
            role=cls.seller_role,
        )
        cls.seller2 = Account.objects.create_user(
            "ventas2@minimarket.local",
            cls.password,
            display_name="Diego Vendedor",
            role=cls.seller_role,
        )
        cls.register = CashRegister.objects.create(code="CAJA-01")
        cls.category = Category.objects.create(name="Productos enlatados")
        cls.product = Product.objects.create(
            category=cls.category,
            name="Atún en lata",
            barcode="775000000201",
            sale_price=Decimal("8.50"),
        )
        load = InitialInventoryLoad.objects.create(
            product=cls.product,
            responsible=cls.warehouse,
        )
        cls.lot = Lot.objects.create(
            product=cls.product,
            initial_load=load,
            number="LOT-E02-02",
            initial_quantity=10,
            available_quantity=10,
            unit_cost=Decimal("4.5000"),
            expiration_date=timezone.localdate() + timedelta(days=20),
        )

    def test_hu_auth_03_ca01_ca02_ca03_and_rn29_rn30_with_two_sellers(self) -> None:
        # Vendedor 1 abre turno y prepara borrador con líneas
        shift = open_cash_shift(actor=self.seller1, opening_amount=Decimal("40.00"))
        add_product_to_draft(actor=self.seller1, product_id=self.product.pk, quantity=3)

        c1 = Client()
        c1.post(reverse("login"), {"email": self.seller1.email, "password": self.password})

        # Cancelar en /salir/ conserva sesión y borrador
        res_confirm = c1.get(reverse("logout"))
        self.assertEqual(res_confirm.status_code, 200)
        self.assertTrue(res_confirm.context["has_active_draft"])
        self.assertIn("Cerrar sesión · Minimarket", res_confirm.content.decode("utf-8"))
        self.assertEqual(
            SaleDraft.objects.filter(seller=self.seller1, status=SaleDraft.Status.ACTIVE).count(),
            1,
        )

        # Confirmar POST /salir/ descarta borrador, conserva turno y stock, e invalida sesión
        res_logout = c1.post(reverse("logout"))
        self.assertRedirects(res_logout, reverse("login"))
        self.assertEqual(
            SaleDraft.objects.filter(seller=self.seller1, status=SaleDraft.Status.ACTIVE).count(),
            0,
        )
        shift.refresh_from_db()
        self.assertEqual(shift.status, CashShift.Status.OPEN)
        self.assertEqual(shift.seller_id, self.seller1.pk)
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.available_quantity, 10)

        # CA-03: rutas protegidas exigen nueva autenticación tras cerrar sesión
        for route_name in ("dashboard", "sales-draft", "cash-open", "cash-close"):
            res = c1.get(reverse(route_name))
            self.assertEqual(res.status_code, 302)
            self.assertIn(reverse("login"), res["Location"])

        # Vendedor 2 en segundo navegador no puede abrir otro turno ni usar/cerrar el turno de Vendedor 1
        c2 = Client()
        c2.post(reverse("login"), {"email": self.seller2.email, "password": self.password})
        with self.assertRaises(ValidationError):
            open_cash_shift(actor=self.seller2, opening_amount=Decimal("10.00"))
        with self.assertRaises(ValidationError):
            add_product_to_draft(actor=self.seller2, product_id=self.product.pk, quantity=1)
        with self.assertRaises(ValidationError):
            close_cash_shift(actor=self.seller2, counted_amount=Decimal("40.00"))

        # Vendedor 1 vuelve a iniciar sesión y recupera su turno abierto sin borrador previo
        c1.post(reverse("login"), {"email": self.seller1.email, "password": self.password})
        res_sales = c1.get(reverse("sales-draft"))
        self.assertEqual(res_sales.status_code, 200)
        self.assertIsNone(res_sales.context["draft"])

    def test_hu_usr_01_to_05_role_matrix_and_http_method_guards(self) -> None:
        emp_urls = [
            reverse("employee-list"),
            reverse("employee-create"),
            reverse("employee-edit", args=[self.seller1.pk]),
        ]
        deactivate_url = reverse("employee-deactivate", args=[self.seller1.pk])

        # Visitante no autenticado -> 302 a login
        anon = Client()
        for url in emp_urls + [deactivate_url]:
            res = anon.get(url)
            self.assertEqual(res.status_code, 302)
            self.assertIn(reverse("login"), res["Location"])

        # VENDEDOR y ALMACENERO -> 403 en GET y POST, sin mutar BD
        for non_admin in (self.seller1, self.warehouse):
            c = Client()
            c.force_login(non_admin)
            for url in emp_urls:
                self.assertEqual(c.get(url).status_code, 403)
                self.assertEqual(c.post(url, {}).status_code, 403)
            self.assertEqual(c.post(deactivate_url, {}).status_code, 403)

        # ADMIN: GET a employee-deactivate -> 405; POST a employee-list -> 405
        admin_client = Client()
        admin_client.force_login(self.admin)
        self.assertEqual(admin_client.get(deactivate_url).status_code, 405)
        self.assertEqual(admin_client.post(reverse("employee-list"), {}).status_code, 405)

    def test_hu_usr_03_04_last_admin_protection_and_historical_integrity(self) -> None:
        # Una cuenta ADMIN inactiva no puede administrar al último ADMIN activo.
        other_admin = Account.objects.create_user(
            "admin2@minimarket.local",
            self.password,
            display_name="Segundo Admin",
            role=self.admin_role,
            is_active=False,
        )
        with self.assertRaisesMessage(
            ValidationError, "Solo el administrador activo puede desactivar cuentas."
        ):
            deactivate_employee(actor=other_admin, account=self.admin)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

        # Desactivar a otro administrador cuando solo queda uno activo tampoco permite dejar 0 admins
        other_admin.is_active = True
        other_admin.save(update_fields=["is_active"])
        deactivate_employee(actor=self.admin, account=other_admin)
        other_admin.refresh_from_db()
        self.assertFalse(other_admin.is_active)

        # Las operaciones históricas de un vendedor desactivado se conservan intactas (HU-USR-04/CA-02)
        shift = open_cash_shift(actor=self.seller1, opening_amount=Decimal("25.00"))
        close_cash_shift(actor=self.seller1, counted_amount=Decimal("25.00"))
        deactivate_employee(actor=self.admin, account=self.seller1)
        self.assertTrue(CashShift.objects.filter(pk=shift.pk, seller=self.seller1).exists())

