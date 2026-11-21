"""Stage 05 audit tests: HU-INV-01a initial inventory load, catalog links, and lot queries."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from cash.models import CashRegister, CashShift
from catalog.models import Category, Product
from catalog.services import toggle_category_status, toggle_product_availability
from identity.models import Account, Role
from identity.services import deactivate_employee, update_employee
from sales.services import add_product_to_draft, checkout_sale

from .forms import InitialLoadProductForm, LotInputForm, LotInputFormSet
from .models import InitialInventoryLoad, Lot, Supplier
from .services import LotInput, confirm_initial_load


class Stage05InitialLoadAuditTests(TestCase):
    password = "Test-only-Passw0rd5!"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

        cls.admin = Account.objects.create_user(
            "admin.audit05@test.invalid", cls.password, display_name="Admin Audit05", role=cls.admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "wh.audit05@test.invalid", cls.password, display_name="Lucía Almacén", role=cls.warehouse_role
        )
        cls.warehouse2 = Account.objects.create_user(
            "wh2.audit05@test.invalid", cls.password, display_name="Pedro Almacén", role=cls.warehouse_role
        )
        cls.seller = Account.objects.create_user(
            "seller.audit05@test.invalid", cls.password, display_name="Carlos Vendedor", role=cls.seller_role
        )

        cls.cat_canned = Category.objects.create(name="Conservas Audit05")
        cls.cat_drinks = Category.objects.create(name="Bebidas Audit05")
        cls.cat_inactive = Category.objects.create(name="Categoría Inactiva Audit05", is_active=False)

        cls.prod_drinks = Product.objects.create(
            category=cls.cat_drinks,
            name="Néctar Durazno 1L",
            barcode="775050010001",
            sale_price=Decimal("6.50"),
            minimum_stock=10,
        )
        cls.prod_canned = Product.objects.create(
            category=cls.cat_canned,
            name="Sardinas en Salsa 425g",
            barcode="775050010002",
            sale_price=Decimal("7.20"),
            minimum_stock=10,
        )
        cls.prod_inactive = Product.objects.create(
            category=cls.cat_canned,
            name="Producto Inactivo Audit05",
            barcode="775050010003",
            sale_price=Decimal("4.00"),
            is_active=False,
        )
        cls.prod_cat_inactive = Product.objects.create(
            category=cls.cat_inactive,
            name="Producto Cat Inactiva",
            barcode="775050010004",
            sale_price=Decimal("4.50"),
        )
        cls.supplier_active = Supplier.objects.create(
            name="Distribuidora Audit05 SAC", ruc="20505010001", phone="01-4445555"
        )
        cls.supplier_inactive = Supplier.objects.create(
            name="Proveedor Inactivo Audit05", ruc="20505010002", is_active=False
        )
        cls.register = CashRegister.objects.create(code="CAJA-A05")

    def _lot_payload(self, product, lots_rows, supplier_id=""):
        data = {
            "product": str(product.pk) if product is not None else "",
            "supplier": str(supplier_id) if supplier_id is not None else "",
            "lots-TOTAL_FORMS": str(len(lots_rows)),
            "lots-INITIAL_FORMS": "0",
            "lots-MIN_NUM_FORMS": "1",
            "lots-MAX_NUM_FORMS": "1000",
        }
        for i, row in enumerate(lots_rows):
            data[f"lots-{i}-number"] = row.get("number", "")
            data[f"lots-{i}-quantity"] = row.get("quantity", "")
            data[f"lots-{i}-unit_cost"] = row.get("unit_cost", "")
            data[f"lots-{i}-expiration_date"] = row.get("expiration_date", "")
        return data

    # ── Elegibilidad y enlace con catalog (DOC03-01, CA-01) ───────────────────

    def test_eligible_products_queryset_includes_any_active_category_und_and_excludes_ineligible(self) -> None:
        qs = list(InitialLoadProductForm().fields["product"].queryset)
        self.assertIn(self.prod_drinks, qs)
        self.assertIn(self.prod_canned, qs)
        self.assertNotIn(self.prod_inactive, qs)
        self.assertNotIn(self.prod_cat_inactive, qs)

        sup_qs = list(InitialLoadProductForm().fields["supplier"].queryset)
        self.assertIn(self.supplier_active, sup_qs)
        self.assertNotIn(self.supplier_inactive, sup_qs)

        # Una vez confirmada la carga inicial, desaparece del selector elegible
        tomorrow = timezone.localdate() + timedelta(days=1)
        confirm_initial_load(
            actor=self.warehouse,
            product=self.prod_canned,
            lots=[LotInput("ELIG-1", 1, Decimal("2.0000"), tomorrow)],
        )
        qs_after = list(InitialLoadProductForm().fields["product"].queryset)
        self.assertNotIn(self.prod_canned, qs_after)

    def test_ineligible_products_rejected_via_http_and_service_without_residue(self) -> None:
        future = (timezone.localdate() + timedelta(days=10)).isoformat()
        future_date = timezone.localdate() + timedelta(days=10)
        self.client.force_login(self.warehouse)

        for bad_prod in (self.prod_inactive, self.prod_cat_inactive):
            with self.subTest(prod=bad_prod.name):
                resp = self.client.post(
                    reverse("inventory-load"),
                    self._lot_payload(
                        bad_prod,
                        [{"number": "BAD-1", "quantity": "2", "unit_cost": "1.00", "expiration_date": future}],
                    ),
                )
                self.assertEqual(resp.status_code, 200)
                self.assertContains(resp, "ya tiene una carga inicial registrada o no está disponible")
                with self.assertRaisesMessage(ValidationError, "no está disponible para la carga inicial"):
                    confirm_initial_load(
                        actor=self.warehouse,
                        product=bad_prod,
                        lots=[LotInput("BAD-1", 2, Decimal("1.00"), future_date)],
                    )

        # Producto None o inexistente/sin guardar -> ValidationError controlado, nunca DoesNotExist/AttributeError
        with self.assertRaisesMessage(ValidationError, "no es válido"):
            confirm_initial_load(
                actor=self.warehouse,
                product=None,
                lots=[LotInput("NONE-1", 1, Decimal("1.00"), future_date)],
            )
        unsaved = Product(category=self.cat_drinks, name="No guardado", barcode="UNSAVED", sale_price=Decimal("2.00"))
        with self.assertRaisesMessage(ValidationError, "ya no existe"):
            confirm_initial_load(
                actor=self.warehouse,
                product=unsaved,
                lots=[LotInput("UNS-1", 1, Decimal("1.00"), future_date)],
            )
        missing = Product(
            pk=uuid.uuid4(), category=self.cat_drinks, name="Ausente", barcode="MISS", sale_price=Decimal("2.00")
        )
        with self.assertRaisesMessage(ValidationError, "ya no existe"):
            confirm_initial_load(
                actor=self.warehouse,
                product=missing,
                lots=[LotInput("MIS-1", 1, Decimal("1.00"), future_date)],
            )
        self.assertFalse(InitialInventoryLoad.objects.exists())
        self.assertFalse(Lot.objects.exists())

    # ── FIX05-01 / FIX05-02 / Formularios y fronteras (CA-02, CA-03, RN-03) ───

    def test_empty_post_with_header_csrf_and_tampered_management_forms_do_not_crash_or_bind_empty(self) -> None:
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.warehouse)
        csrf_client.get(reverse("inventory-load"))
        tok = csrf_client.cookies["csrftoken"].value

        # Empty POST {} with X-CSRFToken header MUST trigger validation errors (FIX05)
        r_empty = csrf_client.post(reverse("inventory-load"), data={}, HTTP_X_CSRFTOKEN=tok)
        self.assertEqual(r_empty.status_code, 200)
        self.assertContains(r_empty, "Seleccione un producto.")
        self.assertContains(r_empty, "1 formulario como mínimo")

        # All blank lot rows
        r_blank = csrf_client.post(
            reverse("inventory-load"),
            {**self._lot_payload(self.prod_drinks, [{}, {}]), "csrfmiddlewaretoken": tok},
        )
        self.assertEqual(r_blank.status_code, 200)
        self.assertContains(r_blank, "1 formulario como mínimo")

        # Tampered management forms
        for payload in (
            {"product": str(self.prod_drinks.pk), "csrfmiddlewaretoken": tok},
            {
                "product": str(self.prod_drinks.pk),
                "lots-TOTAL_FORMS": "-1",
                "lots-INITIAL_FORMS": "0",
                "lots-MIN_NUM_FORMS": "1",
                "lots-MAX_NUM_FORMS": "1000",
                "csrfmiddlewaretoken": tok,
            },
            {
                "product": str(self.prod_drinks.pk),
                "lots-TOTAL_FORMS": "abc",
                "lots-INITIAL_FORMS": "0",
                "lots-MIN_NUM_FORMS": "1",
                "lots-MAX_NUM_FORMS": "1000",
                "csrfmiddlewaretoken": tok,
            },
            {
                "product": str(self.prod_drinks.pk),
                "lots-TOTAL_FORMS": "5000",
                "lots-INITIAL_FORMS": "0",
                "lots-MIN_NUM_FORMS": "1",
                "lots-MAX_NUM_FORMS": "1000",
                "csrfmiddlewaretoken": tok,
            },
        ):
            r = csrf_client.post(reverse("inventory-load"), payload)
            self.assertEqual(r.status_code, 200)
        self.assertFalse(InitialInventoryLoad.objects.exists())

    def test_lot_form_rejects_today_and_past_expiration_arabic_digits_and_does_not_mask_later_errors(self) -> None:
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)

        # Past & today expiration rejected directly on LotInputForm (FIX05-01)
        for bad_date in (today - timedelta(days=1), today, Lot.latest_expiration_date(today) + timedelta(days=1)):
            form = LotInputForm(
                data={"number": "L-EXP", "quantity": "2", "unit_cost": "1.50", "expiration_date": bad_date.isoformat()}
            )
            self.assertFalse(form.is_valid())
            self.assertIn("expiration_date", form.errors)

        # Non-ASCII digits rejected cleanly (FIX05-02)
        arabic = LotInputForm(
            data={"number": "L-AR", "quantity": "٥", "unit_cost": "٢.٥٠", "expiration_date": tomorrow.isoformat()}
        )
        self.assertFalse(arabic.is_valid())
        self.assertIn("quantity", arabic.errors)
        self.assertIn("unit_cost", arabic.errors)

        # Comma decimal & scientific notation rejected cleanly
        comma = LotInputForm(
            data={"number": "L-C", "quantity": "2", "unit_cost": "1,50", "expiration_date": tomorrow.isoformat()}
        )
        self.assertFalse(comma.is_valid())
        self.assertIn("unit_cost", comma.errors)
        sci = LotInputForm(
            data={"number": "L-S", "quantity": "2", "unit_cost": "1e2", "expiration_date": tomorrow.isoformat()}
        )
        self.assertFalse(sci.is_valid())
        self.assertIn("unit_cost", sci.errors)

        # Non-masking multi-lot submit: lot 1 qty=0 + lot 2 today expiration + lot 3 duplicate number of lot 1!
        self.client.force_login(self.warehouse)
        resp = self.client.post(
            reverse("inventory-load"),
            self._lot_payload(
                self.prod_drinks,
                [
                    {"number": "dup-01", "quantity": "0", "unit_cost": "1.50", "expiration_date": tomorrow.isoformat()},
                    {"number": "OK-02", "quantity": "5", "unit_cost": "1.50", "expiration_date": today.isoformat()},
                    {"number": " DUP-01 ", "quantity": "3", "unit_cost": "2.00", "expiration_date": tomorrow.isoformat()},
                ],
            ),
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "posterior a hoy en Lima")
        self.assertContains(resp, "está repetido")
        lot_formset = resp.context["lot_formset"]
        self.assertIn("quantity", lot_formset.forms[0].errors)
        self.assertIn("expiration_date", lot_formset.forms[1].errors)
        self.assertIn("number", lot_formset.forms[2].errors)
        self.assertFalse(InitialInventoryLoad.objects.exists())

    def test_nul_bytes_and_invalid_lot_types_are_rejected_without_db_crash(self) -> None:
        future = timezone.localdate() + timedelta(days=20)
        bad_lots = [
            ("nul_number", LotInput("LOT\x00NUL", 1, Decimal("1.00"), future)),
            ("blank_number", LotInput("   ", 1, Decimal("1.00"), future)),
            ("len_65", LotInput("X" * 65, 1, Decimal("1.00"), future)),
            ("qty_0", LotInput("Q0", 0, Decimal("1.00"), future)),
            ("qty_1000000", LotInput("QMAX", 1000000, Decimal("1.00"), future)),
            ("cost_0", LotInput("C0", 1, Decimal("0.0000"), future)),
            ("cost_5_decimals", LotInput("C5D", 1, Decimal("1.12345"), future)),
            ("cost_gt_max", LotInput("CMAX", 1, Decimal("10000000.0000"), future)),
            ("datetime_exp", LotInput("DTEXP", 1, Decimal("1.00"), datetime(2030, 1, 1, 12, 0))),
            ("float_cost", LotInput("FLT", 1, 1.5, future)),
        ]
        for label, bad in bad_lots:
            with self.subTest(case=label):
                with self.assertRaises(ValidationError):
                    confirm_initial_load(
                        actor=self.warehouse,
                        product=self.prod_drinks,
                        lots=[LotInput("VALID-FIRST", 2, Decimal("1.00"), future), bad],
                    )
        # Lot.clean() also rejects NUL byte cleanly
        with self.assertRaisesMessage(ValidationError, "carácter no válido"):
            Lot(number="BAD\x00LOT", expiration_date=future).clean()

        self.assertFalse(InitialInventoryLoad.objects.exists())
        self.assertFalse(Lot.objects.exists())
        self.prod_drinks.refresh_from_db()
        self.assertEqual(self.prod_drinks.average_cost, Decimal("0.0000"))

    def test_atomic_rollback_on_mid_transaction_database_failure_ct_rollback_01(self) -> None:
        future = timezone.localdate() + timedelta(days=30)
        with patch.object(Lot.objects, "bulk_create", side_effect=RuntimeError("Fallo simulado de disco")):
            with self.assertRaises(RuntimeError):
                confirm_initial_load(
                    actor=self.warehouse,
                    product=self.prod_drinks,
                    lots=[
                        LotInput("RB-1", 5, Decimal("2.0000"), future),
                        LotInput("RB-2", 5, Decimal("4.0000"), future + timedelta(days=5)),
                    ],
                )
        self.assertFalse(InitialInventoryLoad.objects.exists())
        self.assertFalse(Lot.objects.exists())
        self.prod_drinks.refresh_from_db()
        self.assertEqual(self.prod_drinks.average_cost, Decimal("0.0000"))

    # ── Costo promedio, limites máximos, sparse rows y constancia (CA-04, CA-05)

    def test_sparse_rows_weighted_cost_half_up_boundaries_and_constancia(self) -> None:
        tomorrow = timezone.localdate() + timedelta(days=1)
        max_exp = Lot.latest_expiration_date(timezone.localdate())

        self.client.force_login(self.warehouse)
        # Lote 1 y Lote 3 llenos; Lote 2 y Lote 4 en blanco
        # Costo promedio ponderado: (1 * 1.2344 + 1 * 1.2345) / 2 = 1.23445 -> 1.2345 (S/ 1,23)
        resp = self.client.post(
            reverse("inventory-load"),
            self._lot_payload(
                self.prod_drinks,
                [
                    {"number": " sp-1 ", "quantity": "1", "unit_cost": "1.2344", "expiration_date": tomorrow.isoformat()},
                    {},
                    {"number": "S" * 64, "quantity": "1", "unit_cost": "1.2345", "expiration_date": max_exp.isoformat()},
                    {},
                ],
                supplier_id=self.supplier_active.pk,
            ),
        )
        load = InitialInventoryLoad.objects.get(product=self.prod_drinks)
        self.assertRedirects(resp, reverse("inventory-load-created", args=(load.pk,)))

        self.prod_drinks.refresh_from_db()
        self.assertEqual(self.prod_drinks.physical_stock, 2)
        self.assertEqual(self.prod_drinks.sellable_stock, 2)
        self.assertEqual(self.prod_drinks.average_cost, Decimal("1.2345"))
        self.assertTrue(self.prod_drinks.is_sellable)

        lots = list(load.lots.order_by("expiration_date"))
        self.assertEqual([l.number_normalized for l in lots], ["SP-1", "S" * 64])
        self.assertTrue(all(l.is_initial and l.responsible == self.warehouse for l in lots))
        self.assertTrue(all(l.supplier == self.supplier_active for l in lots))

        # Constancia canonical + alias HTML y clases FIX05-05 (.load-col-lot / .load-col-wrap)
        for route_name in ("inventory-load-created", "inventory-load-created-alias"):
            r = self.client.get(reverse(route_name, args=(load.pk,)))
            self.assertEqual(r.status_code, 200)
            # 14-H1: promedio visible a2; costo original de cada lote a4.
            self.assertContains(r, "<dd>S/ 1,23</dd>", html=True)
            self.assertContains(r, "S/ 1,2345")
            self.assertContains(r, 'class="load-col-lot"')
            self.assertContains(r, "Proveedor al confirmar")
            self.assertContains(r, self.warehouse.display_name)
            self.assertContains(r, self.supplier_active.name)

        # Producto ya no aceptado en segundo POST directo
        second = self.client.post(
            reverse("inventory-load"),
            self._lot_payload(
                self.prod_drinks,
                [{"number": "SP-3", "quantity": "1", "unit_cost": "9.00", "expiration_date": tomorrow.isoformat()}],
            ),
        )
        self.assertEqual(second.status_code, 200)
        self.assertContains(second, "ya tiene una carga inicial registrada")
        self.assertEqual(InitialInventoryLoad.objects.filter(product=self.prod_drinks).count(), 1)
        self.assertEqual(Lot.objects.filter(product=self.prod_drinks).count(), 2)

        # HALF_UP .0050 -> visual S/ 1,01 en segundo producto + limites máximos servicio
        confirm_initial_load(
            actor=self.warehouse2,
            product=self.prod_canned,
            lots=[LotInput("MAX-QTY", 999999, Decimal("1.0050"), tomorrow)],
        )
        self.prod_canned.refresh_from_db()
        self.assertEqual(self.prod_canned.average_cost, Decimal("1.0050"))
        load2 = InitialInventoryLoad.objects.get(product=self.prod_canned)
        r2 = self.client.get(reverse("inventory-load-created", args=(load2.pk,)))
        self.assertContains(r2, "S/ 1,01")
        self.assertContains(r2, "Sin proveedor asignado")

    # ── Roles, @never_cache, consultas de lotes y RN-06 (CA-01, CA-05, RN-06, RN-29)

    def test_role_matrix_cache_headers_and_rn06_consistency_across_queries(self) -> None:
        future_30 = timezone.localdate() + timedelta(days=15)
        load = confirm_initial_load(
            actor=self.warehouse,
            product=self.prod_canned,
            supplier=self.supplier_active,
            lots=[LotInput("EQ-10", 10, Decimal("3.5000"), future_30)],
        )

        # Anónimo redirige a login en todas las vistas de etapa 05
        anon = Client()
        for url in (
            reverse("inventory-load"),
            reverse("inventory-load-created", args=(load.pk,)),
            reverse("inventory-load-created-alias", args=(load.pk,)),
            reverse("stock-overview"),
            reverse("product-movements", args=(self.prod_canned.pk,)),
            reverse("product-list"),
            reverse("product-expirations"),
        ):
            r = anon.get(url)
            self.assertEqual(r.status_code, 302)
            self.assertEqual(r["Location"], f"/?next={url}")

        # VENDEDOR obtiene 403 en todas las rutas de carga, consultas de lotes y catálogo
        self.client.force_login(self.seller)
        for url in (
            reverse("inventory-load"),
            reverse("inventory-load-created", args=(load.pk,)),
            reverse("inventory-load-created-alias", args=(load.pk,)),
            reverse("stock-overview"),
            reverse("product-movements", args=(self.prod_canned.pk,)),
            reverse("product-list"),
            reverse("product-expirations"),
        ):
            self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(
            self.client.post(
                reverse("inventory-load"),
                self._lot_payload(
                    self.prod_drinks,
                    [{"number": "V1", "quantity": "1", "unit_cost": "1.00", "expiration_date": future_30.isoformat()}],
                ),
            ).status_code,
            403,
        )

        # ADMIN: 403 en inventory-load GET/POST; 200 en constancia y consultas de lotes/catálogo; sin "Cargar otro producto"
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("inventory-load")).status_code, 403)
        self.assertEqual(
            self.client.post(
                reverse("inventory-load"),
                self._lot_payload(
                    self.prod_drinks,
                    [{"number": "A1", "quantity": "1", "unit_cost": "1.00", "expiration_date": future_30.isoformat()}],
                ),
            ).status_code,
            403,
        )
        admin_cert = self.client.get(reverse("inventory-load-created", args=(load.pk,)))
        self.assertEqual(admin_cert.status_code, 200)
        self.assertNotContains(admin_cert, "Cargar otro producto")
        self.assertNotContains(admin_cert, "Registrar entrada posterior")

        # Cache-Control no-store en TODAS las rutas de etapa 05 (FIX05-03) y RN-06 consistencia stock == minimum == 10 (FIX05-04)
        for actor in (self.warehouse, self.admin):
            self.client.force_login(actor)
            for url in (
                reverse("inventory-load-created", args=(load.pk,)),
                reverse("inventory-load-created-alias", args=(load.pk,)),
                reverse("stock-overview"),
                reverse("product-movements", args=(self.prod_canned.pk,)),
                reverse("product-list"),
                reverse("product-expirations"),
            ):
                r = self.client.get(url)
                self.assertEqual(r.status_code, 200)
                self.assertIn("no-store", r.headers.get("Cache-Control", ""))
                self.assertIn("no-cache", r.headers.get("Cache-Control", ""))

            so = self.client.get(reverse("stock-overview"))
            self.assertIn(self.prod_canned, so.context["low_stock"])
            self.assertContains(so, "Stock bajo")
            pl = self.client.get(reverse("product-list"))
            self.assertContains(pl, "Stock bajo")

        # Random non-existent UUID -> 404 controlado
        self.assertEqual(self.client.get(reverse("inventory-load-created", args=(uuid.uuid4(),))).status_code, 404)
        self.assertEqual(self.client.get(reverse("product-movements", args=(uuid.uuid4(),))).status_code, 404)

        # Actor revocado o rol cambiado rechazado en servicio
        stale_wh = Account.objects.select_related("role").get(pk=self.warehouse2.pk)
        deactivate_employee(actor=self.admin, account=Account.objects.get(pk=self.warehouse2.pk))
        with self.assertRaises(PermissionDenied):
            confirm_initial_load(
                actor=stale_wh,
                product=self.prod_drinks,
                lots=[LotInput("REV-1", 1, Decimal("1.00"), future_30)],
            )
        with self.assertRaises(PermissionDenied):
            confirm_initial_load(
                actor=AnonymousUser(),
                product=self.prod_drinks,
                lots=[LotInput("ANON-1", 1, Decimal("1.00"), future_30)],
            )
        Account.objects.filter(pk=self.warehouse2.pk).update(is_active=True)

        # Modificar role snapshot
        update_employee(
            actor=self.admin,
            account=Account.objects.get(pk=self.warehouse2.pk),
            display_name=self.warehouse2.display_name,
            email=self.warehouse2.email,
            role=self.seller_role,
        )
        with self.assertRaises(PermissionDenied):
            confirm_initial_load(
                actor=stale_wh,
                product=self.prod_drinks,
                lots=[LotInput("ROLE-1", 1, Decimal("1.00"), future_30)],
            )

    # ── Efecto posterior en ventas y FEFO (CA-05, RN-03, RN-19) ───────────────

    def test_downstream_sellability_lima_clock_and_fefo_tie_breakers(self) -> None:
        today = timezone.localdate()
        # Producto con lote A vence en +10d y 2 lotes empatados en +20d con distinto instante de ingreso
        t1 = datetime(2026, 11, 11, 10, 0, tzinfo=dt_timezone.utc)
        t2 = datetime(2026, 11, 11, 11, 0, tzinfo=dt_timezone.utc)

        with patch("django.utils.timezone.now", return_value=t1):
            confirm_initial_load(
                actor=self.warehouse,
                product=self.prod_drinks,
                lots=[
                    LotInput("Z-PRONTO", 2, Decimal("2.00"), today + timedelta(days=10)),
                    LotInput("B-EMPATE-T1", 2, Decimal("3.00"), today + timedelta(days=20)),
                ],
            )
        # Crear tercer lote mismo producto vencimiento igual al 2do lote con received_at t2 (> t1)
        load = InitialInventoryLoad.objects.get(product=self.prod_drinks)
        with patch("django.utils.timezone.now", return_value=t2):
            Lot.objects.create(
                product=self.prod_drinks,
                initial_load=load,
                responsible=self.warehouse,
                number="A-EMPATE-T2",
                number_normalized="A-EMPATE-T2",
                initial_quantity=2,
                available_quantity=2,
                unit_cost=Decimal("4.00"),
                expiration_date=today + timedelta(days=20),
            )

        CashShift.objects.create(cash_register=self.register, seller=self.seller, opening_amount=Decimal("50.00"))
        draft = add_product_to_draft(actor=self.seller, product_id=self.prod_drinks.pk, quantity=3)
        sale = checkout_sale(
            actor=self.seller,
            draft_id=draft.pk,
            cash_received=Decimal("30.00"),
            idempotency_key=uuid.uuid4(),
        )
        self.assertEqual(sale.total_amount, Decimal("19.50"))

        # Debe consumir primero Z-PRONTO (2 unid., menor vencimiento), luego B-EMPATE-T1 (1 unid., menor received_at), sin tocar A-EMPATE-T2
        lot_first = Lot.objects.get(product=self.prod_drinks, number_normalized="Z-PRONTO")
        lot_second = Lot.objects.get(product=self.prod_drinks, number_normalized="B-EMPATE-T1")
        lot_third = Lot.objects.get(product=self.prod_drinks, number_normalized="A-EMPATE-T2")
        self.assertEqual(lot_first.available_quantity, 0)
        self.assertEqual(lot_second.available_quantity, 1)
        self.assertEqual(lot_third.available_quantity, 2)

        # Producto con lote que vence hoy (en Lima) deja de ser vendible en /ventas/ y figura en vencimientos/stock
        confirm_initial_load(
            actor=self.warehouse,
            product=self.prod_canned,
            lots=[LotInput("EXP-HOY", 5, Decimal("2.00"), today + timedelta(days=1))],
        )
        Lot.objects.filter(product=self.prod_canned).update(expiration_date=today)
        self.prod_canned.refresh_from_db()
        self.assertEqual(self.prod_canned.physical_stock, 5)
        self.assertEqual(self.prod_canned.sellable_stock, 0)
        self.assertFalse(self.prod_canned.is_sellable)
        with self.assertRaises(ValidationError):
            add_product_to_draft(actor=self.seller, product_id=self.prod_canned.pk, quantity=1)
