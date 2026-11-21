from __future__ import annotations

import re
import uuid
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.forms import InitialLoadProductForm, StockEntryProductForm, SupplierForm
from inventory.models import InitialInventoryLoad, Lot, StockReceipt, Supplier
from inventory.services import (
    LotInput,
    confirm_initial_load,
    create_supplier,
    register_stock_entry,
    toggle_supplier_status,
)


class Stage04SupplierAuditTests(TestCase):
    password = "Test-only-Audit04!"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

        cls.admin = Account.objects.create_user(
            "admin.audit04@test.invalid",
            cls.password,
            display_name="Admin Stage04",
            role=cls.admin_role,
        )
        cls.warehouse = Account.objects.create_user(
            "warehouse.audit04@test.invalid",
            cls.password,
            display_name="Almacén Stage04",
            role=cls.wh_role,
        )
        cls.seller = Account.objects.create_user(
            "seller.audit04@test.invalid",
            cls.password,
            display_name="Vendedor Stage04",
            role=cls.seller_role,
        )
        cls.category = Category.objects.create(name="Abarrotes Audit04")

    # ── Validaciones de modelo y formulario (RUC, nombre, teléfono, SUNAT) ────

    def test_model_and_form_enforce_ascii_ruc_and_distinguish_sunat_disclaimer(self) -> None:
        form = SupplierForm()
        self.assertIn("solo valida formato", form.fields["ruc"].help_text)
        self.assertIn("SUNAT", form.fields["ruc"].help_text)

        valid_leading_zero = Supplier(
            name="  Distribuidora   Ceros   SAC ",
            ruc="00123456789",
            phone=" +51  (01) 444-5555 ",
        )
        valid_leading_zero.full_clean()
        self.assertEqual(valid_leading_zero.name, "Distribuidora Ceros SAC")
        self.assertEqual(valid_leading_zero.phone, "+51 (01) 444-5555")

        for bad_ruc, label in [
            ("2012345678", "10_digits"),
            ("201234567890", "12_digits"),
            ("2012345678A", "letters"),
            ("٢٠١٢٣٤٥٦٧٨٩", "arabic_indic_unicode_digits"),
            ("201234\x006789", "nul_byte"),
        ]:
            with self.subTest(bad_ruc=label):
                f = SupplierForm(data={"name": "Proveedor OK", "ruc": bad_ruc, "phone": ""})
                self.assertFalse(f.is_valid())
                self.assertIn("ruc", f.errors)
                before = list(Supplier.objects.values())
                with self.assertRaises(ValidationError):
                    Supplier(name="Proveedor OK", ruc=bad_ruc).full_clean()
                with self.assertRaises(ValidationError):
                    create_supplier(actor=self.admin, name="Proveedor OK", ruc=bad_ruc)
                self.assertEqual(list(Supplier.objects.values()), before)
                if label in {"10_digits", "12_digits", "letters", "arabic_indic_unicode_digits"}:
                    self.assertEqual(
                        f.errors["ruc"][0],
                        "El RUC debe contener exactamente 11 dígitos numéricos.",
                    )

    def test_model_form_and_service_reject_bad_names_and_phones(self) -> None:
        long_name = "A" * 161
        for payload, bad_field in [
            ({"name": "   ", "ruc": "20111222333", "phone": ""}, "name"),
            ({"name": "---", "ruc": "20111222333", "phone": ""}, "name"),
            ({"name": long_name, "ruc": "20111222333", "phone": ""}, "name"),
            ({"name": "Con\x00Nul", "ruc": "20111222333", "phone": ""}, "name"),
            ({"name": "Proveedor OK", "ruc": "20111222333", "phone": "((--))"}, "phone"),
            ({"name": "Proveedor OK", "ruc": "20111222333", "phone": "abc<script>"}, "phone"),
            ({"name": "Proveedor OK", "ruc": "20111222333", "phone": "9" * 21}, "phone"),
            ({"name": "Proveedor OK", "ruc": "20111222333", "phone": "999\x00111"}, "phone"),
        ]:
            with self.subTest(payload=payload):
                form = SupplierForm(data=payload)
                self.assertFalse(form.is_valid())
                self.assertIn(bad_field, form.errors)

                before = list(Supplier.objects.values())
                with self.assertRaises(ValidationError) as model_error:
                    Supplier(**payload).full_clean()
                self.assertIn(bad_field, model_error.exception.message_dict)

                with self.assertRaises(ValidationError) as cm:
                    create_supplier(
                        actor=self.admin,
                        name=payload["name"],
                        ruc=payload["ruc"],
                        phone=payload["phone"],
                    )
                self.assertIn(bad_field, cm.exception.message_dict)
                self.assertEqual(list(Supplier.objects.values()), before)

        max_name = "N" * 160
        max_phone = "1" * 20
        sup = create_supplier(actor=self.admin, name=f"  {max_name}  ", ruc=" 00998877665 ", phone=f" {max_phone} ")
        self.assertEqual(sup.name, max_name)
        self.assertEqual(sup.ruc, "00998877665")
        self.assertEqual(sup.phone, max_phone)
        self.assertTrue(sup.is_active)

    def test_duplicate_ruc_rejected_even_when_existing_supplier_is_inactive(self) -> None:
        existing = create_supplier(actor=self.admin, name="Proveedor Activo", ruc="20444555666")
        toggle_supplier_status(actor=self.admin, supplier=existing, is_active=False)
        existing.refresh_from_db()
        self.assertFalse(existing.is_active)

        form = SupplierForm(data={"name": "Homónimo Otro", "ruc": "20444555666", "phone": ""})
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors["ruc"], ["El RUC ya está registrado."])

        with self.assertRaises(ValidationError) as cm:
            create_supplier(actor=self.admin, name="Homónimo Otro", ruc="20444555666")
        self.assertEqual(cm.exception.message_dict["ruc"], ["El RUC ya está registrado."])

    # ── Seguridad de servicios (actor stale, anónimo, no-admin) ──────────────

    def test_services_block_anonymous_non_admin_and_stale_revoked_admin(self) -> None:
        from django.contrib.auth.models import AnonymousUser

        sup = create_supplier(actor=self.admin, name="Base Proveedor", ruc="20333444555")

        for bad_actor in [AnonymousUser(), self.warehouse, self.seller]:
            with self.subTest(actor=str(bad_actor)):
                with self.assertRaises(PermissionDenied):
                    create_supplier(actor=bad_actor, name="No Debe", ruc="20888777666")
                with self.assertRaises(PermissionDenied):
                    toggle_supplier_status(actor=bad_actor, supplier=sup, is_active=False)

        deactivated_admin = Account.objects.create_user(
            "deact.admin@test.invalid", self.password, display_name="Deact", role=self.admin_role
        )
        Account.objects.filter(pk=deactivated_admin.pk).update(is_active=False)
        with self.assertRaises(PermissionDenied):
            create_supplier(actor=deactivated_admin, name="Deact Try", ruc="20888777667")
        with self.assertRaises(PermissionDenied):
            toggle_supplier_status(actor=deactivated_admin, supplier=sup, is_active=False)

        demoted_admin = Account.objects.create_user(
            "demoted.admin@test.invalid", self.password, display_name="Demoted", role=self.admin_role
        )
        Account.objects.filter(pk=demoted_admin.pk).update(role=self.seller_role)
        with self.assertRaises(PermissionDenied):
            create_supplier(actor=demoted_admin, name="Demoted Try", ruc="20888777668")
        with self.assertRaises(PermissionDenied):
            toggle_supplier_status(actor=demoted_admin, supplier=sup, is_active=False)

        sup.refresh_from_db()
        self.assertTrue(sup.is_active)

    def test_toggle_service_handles_idempotency_stale_instance_and_missing_supplier(self) -> None:
        sup = create_supplier(actor=self.admin, name="Estado Control", ruc="20777888999")
        stale_copy = Supplier.objects.get(pk=sup.pk)

        toggle_supplier_status(actor=self.admin, supplier=sup, is_active=False)
        self.assertFalse(sup.is_active)
        self.assertTrue(getattr(sup, "_state_changed", False))

        # Idempotent second call with explicit target keeps False instead of inverting back to True
        toggle_supplier_status(actor=self.admin, supplier=stale_copy, is_active=False)
        stale_copy.refresh_from_db()
        self.assertFalse(stale_copy.is_active)

        # Legacy toggle without explicit is_active reads real DB state (False -> True), even from stale copy
        stale_copy.is_active = True  # stale in-memory flag pretending to still be True
        toggle_supplier_status(actor=self.admin, supplier=stale_copy)
        self.assertTrue(stale_copy.is_active)
        self.assertTrue(Supplier.objects.get(pk=sup.pk).is_active)

        with self.assertRaises(ValidationError):
            toggle_supplier_status(actor=self.admin, supplier=sup, is_active="false")  # type: ignore[arg-type]

        Supplier.objects.filter(pk=sup.pk).delete()
        with self.assertRaisesMessage(ValidationError, "ya no existe"):
            toggle_supplier_status(actor=self.admin, supplier=sup)

    # ── Rutas, roles, navegación, caché y HTML/UI ────────────────────────────

    def test_role_matrix_nav_headers_and_unimplemented_edit_routes(self) -> None:
        sup = create_supplier(actor=self.admin, name="Matriz Roles SAC", ruc="20102030405")
        toggle_url = reverse("supplier-toggle", args=(sup.pk,))

        # Anónimo redirige al login en todas las rutas
        for method, url in [
            ("get", reverse("supplier-list")),
            ("get", reverse("supplier-create")),
            ("post", reverse("supplier-create")),
            ("post", toggle_url),
        ]:
            resp = getattr(self.client, method)(url)
            self.assertEqual(resp.status_code, 302)
            self.assertIn("next=", resp["Location"])

        # VENDEDOR: sin enlace en barra lateral y 403 en todas las rutas
        self.client.force_login(self.seller)
        dash_seller = self.client.get(reverse("dashboard"))
        self.assertEqual(dash_seller.status_code, 200)
        self.assertNotContains(dash_seller, reverse("supplier-list"))
        self.assertEqual(self.client.get(reverse("supplier-list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("supplier-create")).status_code, 403)
        self.assertEqual(
            self.client.post(reverse("supplier-create"), {"name": "X", "ruc": "20102030409"}).status_code,
            403,
        )
        self.assertEqual(self.client.post(toggle_url, {"is_active": "false"}).status_code, 403)

        # ALMACENERO: ve menú y lista solo lectura; 403 en crear/estado
        self.client.force_login(self.warehouse)
        dash_wh = self.client.get(reverse("dashboard"))
        self.assertContains(dash_wh, reverse("supplier-list"))
        list_wh = self.client.get(reverse("supplier-list"))
        self.assertEqual(list_wh.status_code, 200)
        self.assertIn("no-store", list_wh["Cache-Control"])
        self.assertContains(list_wh, "Matriz Roles SAC")
        self.assertNotContains(list_wh, reverse("supplier-create"))
        self.assertNotContains(list_wh, toggle_url)
        self.assertEqual(self.client.get(reverse("supplier-create")).status_code, 403)
        self.assertEqual(self.client.post(toggle_url, {"is_active": "false"}).status_code, 403)

        # ADMIN: ve menú, botones, GET en toggle es 405, HU-PROV-03 editar sigue 404
        self.client.force_login(self.admin)
        dash_admin = self.client.get(reverse("dashboard"))
        self.assertContains(dash_admin, reverse("supplier-list"))
        list_admin = self.client.get(reverse("supplier-list"))
        self.assertEqual(list_admin.status_code, 200)
        self.assertContains(list_admin, reverse("supplier-create"))
        self.assertContains(list_admin, toggle_url)
        self.assertContains(list_admin, 'name="is_active" value="false"')
        self.assertEqual(self.client.get(toggle_url).status_code, 405)

        for candidate_edit in [
            f"/inventario/proveedores/{sup.pk}/editar/",
            f"/inventario/proveedores/{sup.pk}/",
            f"/proveedores/{sup.pk}/editar/",
        ]:
            self.assertEqual(self.client.get(candidate_edit).status_code, 404)

    def test_search_label_placement_whitespace_collapse_and_nul_guard(self) -> None:
        create_supplier(actor=self.admin, name="  Comercial   Andes   EIRL ", ruc="00456789012", phone="991-222")
        create_supplier(actor=self.admin, name="Bodega Norte", ruc="20654321987")

        self.client.force_login(self.admin)
        resp_all = self.client.get(reverse("supplier-list"))
        html_all = resp_all.content.decode()
        label_pos = html_all.index('<label for="supplier-search"')
        group_pos = html_all.index('<div class="input-group"')
        self.assertLess(label_pos, group_pos)

        resp_ruc = self.client.get(reverse("supplier-list"), {"q": "004567"})
        self.assertContains(resp_ruc, "Comercial Andes EIRL")
        self.assertNotContains(resp_ruc, "Bodega Norte")

        resp_spaced = self.client.get(reverse("supplier-list"), {"q": "  Comercial   Andes  "})
        self.assertContains(resp_spaced, "Comercial Andes EIRL")

        resp_nul = self.client.get(reverse("supplier-list"), {"q": "abc\x00def"})
        self.assertEqual(resp_nul.status_code, 200)
        self.assertContains(resp_nul, "La búsqueda contiene caracteres no válidos.")
        self.assertNotContains(resp_nul, "Bodega Norte")
        self.assertContains(resp_nul, 'aria-label="Limpiar búsqueda"')

    def test_create_view_empty_post_shows_errors_shifts_autofocus_and_handles_two_tab_toggle(self) -> None:
        self.client.force_login(self.admin)

        get_create = self.client.get(reverse("supplier-create"))
        self.assertIn("no-store", get_create["Cache-Control"])
        self.assertContains(get_create, "solo valida formato")

        empty_post = self.client.post(reverse("supplier-create"), {})
        self.assertEqual(empty_post.status_code, 200)
        self.assertContains(empty_post, 'role="alert"')
        self.assertContains(empty_post, "El nombre del proveedor es obligatorio.")
        self.assertContains(empty_post, "El RUC es obligatorio.")

        bad_ruc_post = self.client.post(
            reverse("supplier-create"),
            {"name": "Proveedor Foco", "ruc": "123", "phone": ""},
        )
        self.assertEqual(bad_ruc_post.status_code, 200)
        html_bad_ruc = bad_ruc_post.content.decode()
        self.assertIn("El RUC debe contener exactamente 11 dígitos numéricos.", html_bad_ruc)
        # El foco se mueve al campo con error (id_ruc) y se retira de id_name
        ruc_input = re.search(r'<input[^>]*id="id_ruc"[^>]*>', html_bad_ruc).group(0)
        name_input = re.search(r'<input[^>]*id="id_name"[^>]*>', html_bad_ruc).group(0)
        self.assertIn("autofocus", ruc_input)
        self.assertNotIn("autofocus", name_input)

        ok_post = self.client.post(
            reverse("supplier-create"),
            {"name": "  Logística   Sur  ", "ruc": "20555444332", "phone": ""},
            follow=True,
        )
        self.assertContains(ok_post, "Proveedor «Logística Sur» registrado.")
        sup = Supplier.objects.get(ruc="20555444332")
        self.assertTrue(sup.is_active)

        toggle_url = reverse("supplier-toggle", args=(sup.pk,))
        tab1 = self.client.post(toggle_url, {"is_active": "false"}, follow=True)
        self.assertContains(tab1, "Proveedor «Logística Sur» ahora está inactivo.")
        tab2_stale = self.client.post(toggle_url, {"is_active": "false"}, follow=True)
        self.assertContains(tab2_stale, "El proveedor «Logística Sur» ya se encontraba inactivo.")
        sup.refresh_from_db()
        self.assertFalse(sup.is_active)

        bad_target = self.client.post(toggle_url, {"is_active": "quizas"}, follow=True)
        self.assertContains(bad_target, "El estado solicitado para el proveedor no es válido.")
        sup.refresh_from_db()
        self.assertFalse(sup.is_active)

    # ── Relación proveedor ↔ recepciones, inactivos e historia en inventario ─

    def test_inactive_supplier_rejected_without_silent_none_and_history_preserved(self) -> None:
        sup = create_supplier(actor=self.admin, name="Proveedor Histórico SAC", ruc="20666777888")
        p_init = Product.objects.create(
            category=self.category, name="Aceite Vegetal", barcode="775040001001", sale_price=Decimal("9.50")
        )
        p_sub = Product.objects.create(
            category=self.category, name="Azúcar Rubia", barcode="775040001002", sale_price=Decimal("5.20")
        )
        future = (timezone.localdate() + timedelta(days=15)).isoformat()

        confirm_initial_load(
            actor=self.warehouse,
            product=p_sub,
            lots=[LotInput("BASE-01", 5, Decimal("3.0000"), timezone.localdate() + timedelta(days=10))],
        )

        # Desactivar proveedor antes de que el almacenero envíe carga inicial o entrada posterior
        toggle_supplier_status(actor=self.admin, supplier=sup, is_active=False)

        self.assertNotIn(sup, InitialLoadProductForm().fields["supplier"].queryset)
        self.assertNotIn(sup, StockEntryProductForm().fields["supplier"].queryset)

        self.client.force_login(self.warehouse)
        for route_name, prod, lot_code in [
            ("inventory-load", p_init, "L-INACT-INI"),
            ("stock-entry", p_sub, "L-INACT-ENT"),
        ]:
            url = reverse(route_name)
            payload = {
                "idempotency_key": str(uuid.uuid4()),
                "product": str(prod.pk),
                "supplier": str(sup.pk),
                "lots-TOTAL_FORMS": "1",
                "lots-INITIAL_FORMS": "0",
                "lots-MIN_NUM_FORMS": "1",
                "lots-MAX_NUM_FORMS": "1000",
                "lots-0-number": lot_code,
                "lots-0-quantity": "4",
                "lots-0-unit_cost": "3.5000",
                "lots-0-expiration_date": future,
            }
            resp = self.client.post(url, payload)
            self.assertEqual(resp.status_code, 200)
            self.assertContains(resp, "Proveedor Histórico SAC")
            self.assertContains(resp, "20666777888")
            self.assertContains(resp, f'value="__inactive__:{sup.pk}"')
            self.assertNotContains(resp, f'<option value="{sup.pk}"')

            # Un segundo envío sin cambiar la selección del proveedor debe seguir bloqueado
            second_resp = self.client.post(url, {**payload, "supplier": f"__inactive__:{sup.pk}"})
            self.assertEqual(second_resp.status_code, 200)
            self.assertContains(second_resp, "está inactivo")
            self.assertFalse(Lot.objects.filter(number_normalized=lot_code).exists())

        # Reactivar permite recepción y luego volver a desactivar conserva el histórico
        toggle_supplier_status(actor=self.admin, supplier=sup, is_active=True)
        resp_init_ok = self.client.post(
            reverse("inventory-load"),
            {
                "product": str(p_init.pk),
                "supplier": str(sup.pk),
                "lots-TOTAL_FORMS": "1",
                "lots-INITIAL_FORMS": "0",
                "lots-MIN_NUM_FORMS": "1",
                "lots-MAX_NUM_FORMS": "1000",
                "lots-0-number": "L-HIST-INI",
                "lots-0-quantity": "4",
                "lots-0-unit_cost": "4.0000",
                "lots-0-expiration_date": future,
            },
        )
        load_init = InitialInventoryLoad.objects.get(product=p_init)
        self.assertRedirects(resp_init_ok, reverse("inventory-load-created", args=(load_init.pk,)))

        resp_sub_ok = self.client.post(
            reverse("stock-entry"),
            {
                "idempotency_key": str(uuid.uuid4()),
                "product": str(p_sub.pk),
                "supplier": str(sup.pk),
                "lots-TOTAL_FORMS": "1",
                "lots-INITIAL_FORMS": "0",
                "lots-MIN_NUM_FORMS": "1",
                "lots-MAX_NUM_FORMS": "1000",
                "lots-0-number": "L-HIST-ENT",
                "lots-0-quantity": "6",
                "lots-0-unit_cost": "3.8000",
                "lots-0-expiration_date": future,
            },
        )
        load_sub = InitialInventoryLoad.objects.get(product=p_sub)
        receipt = StockReceipt.objects.get(product=p_sub)
        self.assertRedirects(resp_sub_ok, reverse("stock-receipt", args=(receipt.pk,)))

        # Desactivar nuevamente no altera las vistas históricas de carga, movimientos ni vencimientos
        toggle_supplier_status(actor=self.admin, supplier=sup, is_active=False)

        for actor in (self.warehouse, self.admin):
            self.client.force_login(actor)
            r_load = self.client.get(reverse("stock-receipt", args=(receipt.pk,)))
            self.assertEqual(r_load.status_code, 200)
            self.assertContains(r_load, "Proveedor Histórico SAC")

            r_mov = self.client.get(reverse("product-movements", args=(p_sub.pk,)))
            self.assertEqual(r_mov.status_code, 200)
            self.assertContains(r_mov, "(Proveedor Histórico SAC)")

            r_exp = self.client.get(reverse("product-expirations"))
            self.assertEqual(r_exp.status_code, 200)
            self.assertContains(r_exp, "Proveedor Histórico SAC")
