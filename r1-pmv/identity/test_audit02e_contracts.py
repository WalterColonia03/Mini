"""Pruebas de contrato del sublote 02-E: confirmacion de estado, bloqueos, revocacion y auditoria tecnica."""
from __future__ import annotations

import io
import json
import logging
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.sessions.models import Session
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from app_platform.logging import RedactSensitiveDataFilter, redact_sensitive_text
from cash.models import CashRegister, CashShift
from catalog.models import Category, Product
from inventory.models import InitialInventoryLoad, Lot
from sales.models import SaleDraft

from .models import Account, IdentityAuditEvent, LoginAttempt, Role
from .services import (
    _active_lockout_until,
    _login_identifier,
    authenticate_active_account,
    create_employee,
    deactivate_employee,
    reactivate_employee,
    update_employee,
)


class Sublot02EContractsTests(TestCase):
    password = "Pass02e!Secure"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role, _ = Role.objects.get_or_create(
            code=Role.Code.ADMIN, defaults={"name": "Administrador"}
        )
        cls.seller_role, _ = Role.objects.get_or_create(
            code=Role.Code.SELLER, defaults={"name": "Vendedor"}
        )
        cls.warehouse_role, _ = Role.objects.get_or_create(
            code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"}
        )
        cls.admin = Account.objects.create_user(
            "admin02e@test.invalid",
            cls.password,
            display_name="Admin 02E",
            role=cls.admin_role,
        )
        cls.admin2 = Account.objects.create_user(
            "admin2_02e@test.invalid",
            cls.password,
            display_name="Admin Dos",
            role=cls.admin_role,
        )
        cls.seller = Account.objects.create_user(
            "seller02e@test.invalid",
            cls.password,
            display_name="Vendedor 02E",
            role=cls.seller_role,
        )
        cls.warehouse = Account.objects.create_user(
            "warehouse02e@test.invalid",
            cls.password,
            display_name="Almacenero 02E",
            role=cls.warehouse_role,
        )
        cls.cash_register = CashRegister.objects.create(code="CAJA-02E")
        category = Category.objects.create(name="Abarrotes 02E")
        cls.product = Product.objects.create(
            category=category,
            name="Arroz 02E",
            barcode="775000000201",
            sale_price=Decimal("12.50"),
        )
        load = InitialInventoryLoad.objects.create(product=cls.product, responsible=cls.warehouse)
        Lot.objects.create(
            product=cls.product,
            initial_load=load,
            number="LOTE-02E-01",
            initial_quantity=10,
            available_quantity=10,
            unit_cost=Decimal("8.0000"),
            expiration_date=timezone.localdate() + timedelta(days=30),
        )

    def _open_shift_for(self, seller: Account) -> CashShift:
        return CashShift.objects.create(
            cash_register=self.cash_register,
            seller=seller,
            opening_amount=Decimal("20.00"),
        )

    # ── H02E-01 · Salida por rol, turno y borrador + atomicidad rollback ──────

    def test_h02e01_logout_messages_by_role_shift_and_draft(self) -> None:
        self.client.force_login(self.admin)
        res_admin = self.client.get(reverse("logout"))
        self.assertContains(res_admin, "Tu cuenta no opera turnos de caja.")
        self.assertNotContains(res_admin, "venta en preparación")

        self.client.force_login(self.warehouse)
        res_wh = self.client.get(reverse("logout"))
        self.assertContains(res_wh, "Tu cuenta no opera turnos de caja.")
        self.assertNotContains(res_wh, "venta en preparación")

        self.client.force_login(self.seller)
        res_seller_no_shift = self.client.get(reverse("logout"))
        self.assertContains(res_seller_no_shift, "actualmente no tienes un turno de caja abierto")
        self.assertNotContains(res_seller_no_shift, "La venta en preparación se descartará")

        self._open_shift_for(self.seller)
        res_seller_shift = self.client.get(reverse("logout"))
        self.assertContains(res_seller_shift, "seguirá ligado a tu cuenta")
        self.assertNotContains(res_seller_shift, "actualmente no tienes un turno de caja abierto")
        self.assertNotContains(res_seller_shift, "La venta en preparación se descartará")

        post_draft = self.client.post(
            reverse("sales-draft"),
            {"product_id": str(self.product.pk), "quantity": "1"},
        )
        self.assertEqual(post_draft.status_code, 302)
        res_seller_draft = self.client.get(reverse("logout"))
        self.assertContains(res_seller_draft, "venta en preparación")
        self.assertContains(res_seller_draft, "El turno abierto seguirá ligado a tu cuenta.")

    def test_h02e01_logout_rollback_drops_draft_and_audit_when_logout_fails(self) -> None:
        self._open_shift_for(self.seller)
        self.client.force_login(self.seller)
        self.client.post(
            reverse("sales-draft"),
            {"product_id": str(self.product.pk), "quantity": "2"},
        )
        self.assertTrue(SaleDraft.objects.filter(seller=self.seller).exists())
        before_events = IdentityAuditEvent.objects.filter(action="LOGOUT_SUCCESS").count()

        def fail_logout(request):
            raise RuntimeError("simulated logout outage")

        with patch("identity.audit._emit_external_event") as mocked_emit:
            with patch("identity.views.logout", side_effect=fail_logout):
                with self.assertRaisesMessage(RuntimeError, "simulated logout outage"):
                    self.client.post(reverse("logout"))

        self.assertTrue(SaleDraft.objects.filter(seller=self.seller).exists())
        self.assertEqual(
            IdentityAuditEvent.objects.filter(action="LOGOUT_SUCCESS").count(),
            before_events,
        )
        mocked_emit.assert_not_called()

    # ── H02E-02 · Pantalla explícita de confirmación GET + POST /estado/ ───────

    def test_h02e02_state_confirm_get_cancel_confirm_idempotent_and_guards(self) -> None:
        target = create_employee(
            actor=self.admin,
            display_name="Confirmar Estado",
            email="confirmstate@test.invalid",
            password=self.password,
            role=self.warehouse_role,
        )
        self.client.force_login(self.admin)

        # GET /estado/ sigue prohibido (405) y /estado/confirmar/ muestra resumen y advertencias
        self.assertEqual(self.client.get(reverse("employee-deactivate", args=(target.pk,))).status_code, 405)
        self.assertEqual(
            self.client.get(reverse("employee-state-confirm", args=(target.pk,)), {"action": "invalida"}).status_code,
            400,
        )
        confirm_get = self.client.get(
            reverse("employee-state-confirm", args=(target.pk,)),
            {"action": "desactivar"},
        )
        self.assertEqual(confirm_get.status_code, 200)
        self.assertContains(confirm_get, target.display_name)
        self.assertContains(confirm_get, target.email)
        self.assertContains(confirm_get, "Desactivar cuenta")
        self.assertContains(confirm_get, reverse("employee-deactivate", args=(target.pk,)))
        self.assertContains(confirm_get, reverse("employee-list"))

        # Falta / invalida en POST /estado/ -> 400
        self.assertEqual(self.client.post(reverse("employee-deactivate", args=(target.pk,)), {}).status_code, 400)
        self.assertEqual(
            self.client.post(reverse("employee-deactivate", args=(target.pk,)), {"action": "otro"}).status_code,
            400,
        )

        # Confirmar desactivación y validar idempotencia
        res_post = self.client.post(
            reverse("employee-deactivate", args=(target.pk,)),
            {"action": "desactivar"},
        )
        self.assertRedirects(res_post, reverse("employee-list"))
        target.refresh_from_db()
        self.assertFalse(target.is_active)

        confirm_already = self.client.get(
            reverse("employee-state-confirm", args=(target.pk,)),
            {"action": "desactivar"},
        )
        self.assertContains(confirm_already, "ya tiene el estado solicitado")

        res_idem = self.client.post(
            reverse("employee-deactivate", args=(target.pk,)),
            {"action": "desactivar"},
        )
        self.assertRedirects(res_idem, reverse("employee-list"))
        target.refresh_from_db()
        self.assertFalse(target.is_active)

        # Confirmar reactivación con bloqueo vigente visible en pantalla
        identifier = _login_identifier(target.email_normalized)
        LoginAttempt.objects.update_or_create(
            identifier=identifier,
            defaults={"failures": 5, "locked_until": timezone.now() + timedelta(minutes=10)},
        )
        react_get = self.client.get(
            reverse("employee-state-confirm", args=(target.pk,)),
            {"action": "reactivar"},
        )
        self.assertContains(react_get, "Bloqueo temporal vigente")
        res_react = self.client.post(
            reverse("employee-deactivate", args=(target.pk,)),
            {"action": "reactivar"},
        )
        self.assertRedirects(res_react, reverse("employee-list"))
        target.refresh_from_db()
        self.assertTrue(target.is_active)
        self.assertIsNotNone(_active_lockout_until(target.email_normalized))

        # Auto-desactivación, último admin y turno abierto muestran advertencia en confirmar y rechazan en POST
        self_get = self.client.get(
            reverse("employee-state-confirm", args=(self.admin.pk,)),
            {"action": "desactivar"},
        )
        self.assertContains(self_get, "No puedes desactivar tu propia cuenta")
        self._open_shift_for(self.seller)
        shift_get = self.client.get(
            reverse("employee-state-confirm", args=(self.seller.pk,)),
            {"action": "desactivar"},
        )
        self.assertContains(shift_get, "Turno de caja abierto")
        for blocked in (shift_get, self_get):
            self.assertContains(blocked, "La cuenta seguirá activa y conservará sus sesiones.")
            self.assertNotContains(blocked, "se cerrarán de inmediato")
        self.assertContains(confirm_get, "se cerrarán de inmediato")
        res_shift_post = self.client.post(
            reverse("employee-deactivate", args=(self.seller.pk,)),
            {"action": "desactivar"},
        )
        self.assertRedirects(res_shift_post, reverse("employee-list"))
        self.seller.refresh_from_db()
        self.assertTrue(self.seller.is_active)

        # Roles no autorizados y anónimo
        for role_user in (self.seller, self.warehouse):
            self.client.force_login(role_user)
            self.assertEqual(
                self.client.get(reverse("employee-state-confirm", args=(target.pk,))).status_code,
                403,
            )
            self.assertEqual(
                self.client.post(
                    reverse("employee-deactivate", args=(target.pk,)),
                    {"action": "desactivar"},
                ).status_code,
                403,
            )
        self.client.logout()
        anon_res = self.client.get(reverse("employee-state-confirm", args=(target.pk,)))
        self.assertEqual(anon_res.status_code, 302)
        self.assertIn(reverse("login"), anon_res["Location"])

    # ── H02E-03 · Bloqueo conservado, revocación de sesión y límites ──────────

    def test_h02e03_lockout_preserved_across_email_rename_and_reactivate_until_explicit_unlock(self) -> None:
        target = create_employee(
            actor=self.admin,
            display_name="Bloqueo Persistente",
            email="lockold@test.invalid",
            password=self.password,
            role=self.seller_role,
        )
        for _ in range(5):
            authenticate_active_account(target.email, "WrongPass123")
        self.assertIsNotNone(_active_lockout_until(target.email_normalized))

        # Cambiar correo sin desbloqueo conserva el bloqueo sobre el nuevo correo
        update_employee(
            actor=self.admin,
            account=target,
            display_name="Bloqueo Persistente",
            email="locknew@test.invalid",
            role=self.seller_role,
        )
        self.assertIsNotNone(_active_lockout_until("locknew@test.invalid"))
        res_locked = authenticate_active_account("locknew@test.invalid", self.password)
        self.assertFalse(res_locked.authenticated)
        self.assertGreater(res_locked.locked_minutes, 0)

        # Desactivar y reactivar conserva bloqueo
        deactivate_employee(actor=self.admin, account=target)
        reactivate_employee(actor=self.admin, account=target)
        res_after_reactivate = authenticate_active_account("locknew@test.invalid", self.password)
        self.assertFalse(res_after_reactivate.authenticated)
        self.assertGreater(res_after_reactivate.locked_minutes, 0)

        # Desbloqueo explícito en editar sí lo levanta y queda auditado
        self.client.force_login(self.admin)
        edit_url = reverse("employee-edit", args=(target.pk,))
        self.assertContains(self.client.get(edit_url), "bloqueo temporal vigente")
        post_unlock = self.client.post(
            edit_url,
            {
                "display_name": "Bloqueo Persistente",
                "email": "locknew@test.invalid",
                "role": str(self.seller_role.pk),
                "new_password": "",
                "unlock_account": "on",
            },
        )
        self.assertRedirects(post_unlock, reverse("employee-list"))
        self.assertIsNone(_active_lockout_until("locknew@test.invalid"))
        self.assertTrue(
            IdentityAuditEvent.objects.filter(
                action="ACCOUNT_UNLOCKED", target_id=str(target.pk)
            ).exists()
        )
        res_ok = authenticate_active_account("locknew@test.invalid", self.password)
        self.assertTrue(res_ok.authenticated)

    def test_h02e03_password_reset_revokes_other_sessions_and_self_logs_out(self) -> None:
        other_client = self.client_class()
        admin_client = self.client_class()

        other_client.post(
            reverse("login"),
            {"email": self.seller.email, "password": self.password},
        )
        self.assertEqual(other_client.get(reverse("dashboard")).status_code, 200)

        admin_client.force_login(self.admin)
        new_pass = "ResetPass02e!"
        res_reset = admin_client.post(
            reverse("employee-edit", args=(self.seller.pk,)),
            {
                "display_name": self.seller.display_name,
                "email": self.seller.email,
                "role": str(self.seller_role.pk),
                "new_password": new_pass,
            },
        )
        self.assertRedirects(res_reset, reverse("employee-list"))
        self.assertTrue(
            IdentityAuditEvent.objects.filter(
                action="PASSWORD_RESET", target_id=str(self.seller.pk)
            ).exists()
        )
        # Sesión previa del vendedor ya no accede al panel
        revoked_dash = other_client.get(reverse("dashboard"))
        self.assertEqual(revoked_dash.status_code, 302)
        self.assertIn(reverse("login"), revoked_dash["Location"])

        # Auto-reset de contraseña cierra la propia sesión del administrador
        self_client = self.client_class()
        self_client.post(
            reverse("login"),
            {"email": self.admin2.email, "password": self.password},
        )
        self_res = self_client.post(
            reverse("employee-edit", args=(self.admin2.pk,)),
            {
                "display_name": self.admin2.display_name,
                "email": self.admin2.email,
                "role": str(self.admin_role.pk),
                "new_password": "Admin2Reset02e!",
            },
        )
        self.assertRedirects(self_res, reverse("login"))
        self.assertEqual(self_client.get(reverse("dashboard")).status_code, 302)

    def test_h02e03_boundary_lengths_and_nul_byte_rejection(self) -> None:
        self.client.force_login(self.admin)
        # Nombre de 120 chars válido; 121 chars rechazado
        name_120 = "N" * 120
        res_ok = self.client.post(
            reverse("employee-create"),
            {
                "display_name": name_120,
                "email": "borde120@test.invalid",
                "password": self.password,
                "role": str(self.seller_role.pk),
            },
        )
        self.assertRedirects(res_ok, reverse("employee-list"))

        res_121 = self.client.post(
            reverse("employee-create"),
            {
                "display_name": "N" * 121,
                "email": "borde121@test.invalid",
                "password": self.password,
                "role": str(self.seller_role.pk),
            },
        )
        self.assertEqual(res_121.status_code, 200)
        self.assertFalse(Account.objects.filter(email_normalized="borde121@test.invalid").exists())

        # Correo 254 chars válido y 255 rechazado (etiquetas DNS <= 63 chars)
        email_254 = f"{'a' * 61}@{'b' * 62}.{'c' * 62}.{'d' * 62}.com"
        self.assertEqual(len(email_254), 254)
        res_254 = self.client.post(
            reverse("employee-create"),
            {
                "display_name": "Correo Borde 254",
                "email": email_254,
                "password": self.password,
                "role": str(self.seller_role.pk),
            },
        )
        self.assertRedirects(res_254, reverse("employee-list"))

        email_255 = f"{'a' * 62}@{'b' * 62}.{'c' * 62}.{'d' * 62}.com"
        self.assertEqual(len(email_255), 255)
        res_255 = self.client.post(
            reverse("employee-create"),
            {
                "display_name": "Correo Borde 255",
                "email": email_255,
                "password": self.password,
                "role": str(self.seller_role.pk),
            },
        )
        self.assertEqual(res_255.status_code, 200)
        self.assertFalse(Account.objects.filter(email_normalized=email_255).exists())

        # Byte NUL rechazado sin 500
        res_nul = self.client.post(
            reverse("employee-create"),
            {
                "display_name": "Usuario\x00Nulo",
                "email": "nul\x00user@test.invalid",
                "password": self.password,
                "role": str(self.seller_role.pk),
            },
        )
        self.assertEqual(res_nul.status_code, 200)
        self.assertFalse(
            any(
                "\x00" in name or "\x00" in mail
                for name, mail in Account.objects.values_list("display_name", "email")
            )
        )

    # ── H02E-04 · Auditoría transaccional, correlación y redacción ─────────────

    def test_h02e04_audit_lifecycle_utc_request_id_and_zero_secrets_in_db(self) -> None:
        with self.captureOnCommitCallbacks(execute=True):
            req_id = "req-02e-lifecycle-42"
            res_create = self.client.post(
                reverse("employee-create"),
                {
                    "display_name": "Canario Vida",
                    "email": "vida02e@test.invalid",
                    "password": self.password,
                    "role": str(self.seller_role.pk),
                },
            )
            # Without admin login -> 302 ACCESS_DENIED
            self.assertEqual(res_create.status_code, 302)

        self.client.post(
            reverse("login"),
            {"email": self.admin.email, "password": self.password},
            HTTP_X_REQUEST_ID=req_id,
        )
        login_ev = IdentityAuditEvent.objects.filter(action="LOGIN_SUCCESS", request_id=req_id).first()
        self.assertIsNotNone(login_ev)
        self.assertEqual(login_ev.occurred_at.utcoffset().total_seconds(), 0)

        canary_secret = "Canario-Secreto-Prueba-02e!"
        emp_res = self.client.post(
            reverse("employee-create"),
            {
                "display_name": "Auditoría Completa",
                "email": "audita02e@test.invalid",
                "password": canary_secret,
                "role": str(self.seller_role.pk),
            },
            HTTP_X_REQUEST_ID="req-create-02e",
        )
        self.assertEqual(emp_res.status_code, 302)
        self.assertEqual(emp_res.headers.get("X-Request-ID"), "req-create-02e")

        target = Account.objects.get(email_normalized="audita02e@test.invalid")
        # Role change, edit, deactivate, reactivate
        self.client.post(
            reverse("employee-edit", args=(target.pk,)),
            {
                "display_name": "Auditoría Editada",
                "email": target.email,
                "role": str(self.warehouse_role.pk),
                "new_password": "",
            },
            HTTP_X_REQUEST_ID="req-role-02e",
        )
        self.client.post(
            reverse("employee-deactivate", args=(target.pk,)),
            {"action": "desactivar"},
            HTTP_X_REQUEST_ID="req-deact-02e",
        )
        self.client.post(
            reverse("employee-deactivate", args=(target.pk,)),
            {"action": "reactivar"},
            HTTP_X_REQUEST_ID="req-react-02e",
        )
        self.client.post(reverse("logout"), HTTP_X_REQUEST_ID="req-logout-02e")

        expected_actions = {
            "LOGIN_SUCCESS",
            "EMPLOYEE_CREATED",
            "ROLE_CHANGED",
            "EMPLOYEE_DEACTIVATED",
            "EMPLOYEE_REACTIVATED",
            "LOGOUT_SUCCESS",
        }
        recorded_actions = set(IdentityAuditEvent.objects.values_list("action", flat=True))
        self.assertTrue(expected_actions.issubset(recorded_actions))

        from .audit import sanitize_metadata

        deact_ev = IdentityAuditEvent.objects.get(action="EMPLOYEE_DEACTIVATED", target_id=str(target.pk))
        self.assertIs(deact_ev.metadata.get("sessions_revoked"), True)
        sanitized = sanitize_metadata(
            {"sessionid": "abc", "session_key": "xyz", "session": "sec", "sessions_revoked": True}
        )
        self.assertEqual(sanitized["sessionid"], "[REDACTED]")
        self.assertEqual(sanitized["session_key"], "[REDACTED]")
        self.assertEqual(sanitized["session"], "[REDACTED]")
        self.assertIs(sanitized["sessions_revoked"], True)

        for event in IdentityAuditEvent.objects.all():
            self.assertTrue(timezone.is_aware(event.occurred_at))
            self.assertTrue(bool(event.request_id))
            serialized = json.dumps(event.metadata, ensure_ascii=False)
            self.assertNotIn(canary_secret, serialized)
            self.assertNotIn(self.password, serialized)
            self.assertNotIn(canary_secret, event.actor_identifier)

    def test_h02e04_log_redaction_including_exc_info_and_resilient_logger_failure(self) -> None:
        canary = "CANARIO-SECRETO-PRUEBA"
        log_filter = RedactSensitiveDataFilter()
        self.assertNotIn(canary, redact_sensitive_text(f"new_password={canary} sessionid={canary}"))

        for logger_name in ("identity.audit", "django.request"):
            logger = logging.getLogger(logger_name)
            redact_filters = [
                flt
                for flt in [
                    *logger.filters,
                    *(f for h in logger.handlers for f in h.filters),
                ]
                if isinstance(flt, RedactSensitiveDataFilter)
            ]
            self.assertTrue(
                redact_filters,
                f"El logger {logger_name} debe tener RedactSensitiveDataFilter configurado en settings.LOGGING",
            )
            stream = io.StringIO()
            handler = logging.StreamHandler(stream)
            handler.setFormatter(logging.Formatter("%(levelname)s %(message)s %(exc_text)s"))
            handler.addFilter(redact_filters[0])
            logger.addHandler(handler)
            prev_level = logger.level
            logger.setLevel(logging.INFO)
            try:
                try:
                    raise ValueError(f"Error con clave={canary} y csrftoken={canary}")
                except ValueError:
                    logger.error(
                        "Fallo en solicitud password=%s new_password=%s sessionid=%s",
                        canary,
                        canary,
                        canary,
                        exc_info=True,
                    )
            finally:
                logger.removeHandler(handler)
                logger.setLevel(prev_level)
            output = stream.getvalue()
            self.assertIn("[REDACTED]", output)
            self.assertNotIn(canary, output)

        # Fallo del logger en rechazo no concede acceso ni genera 500, y escribe respaldo redactado
        self.client.force_login(self.seller)
        err_stream = io.StringIO()
        with patch("sys.stderr", err_stream):
            with patch(
                "identity.audit.audit_logger.log",
                side_effect=RuntimeError(f"sink error password={canary}"),
            ):
                denied = self.client.get(reverse("employee-list"), HTTP_X_REQUEST_ID="req-sink-fail")
        self.assertEqual(denied.status_code, 403)
        stderr_out = err_stream.getvalue()
        self.assertIn("identity_audit_log_failure", stderr_out)
        self.assertNotIn(canary, stderr_out)
