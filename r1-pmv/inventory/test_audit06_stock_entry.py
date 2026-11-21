"""Stage 06 audit tests: HU-INV-01b stock_entry, moving average cost, FEFO/RN-28, roles, and FUTURO scope boundary."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, connection, transaction
from django.test import Client, TestCase
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.utils import timezone

from cash.models import CashRegister, CashShift
from catalog.models import Category, Product
from catalog.services import toggle_category_status, toggle_product_availability
from identity.models import Account, Role
from identity.services import deactivate_employee, update_employee
from sales.models import Sale, SaleLine
from sales.services import add_product_to_draft, checkout_sale

from .forms import LotInputForm, StockEntryProductForm
from .models import InitialInventoryLoad, Lot, StockReceipt, Supplier
from .services import LotInput, confirm_initial_load, register_stock_entry


class Stage06StockEntryAuditTests(TestCase):
    password = "Test-only-Passw0rd6!"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

        cls.admin = Account.objects.create_user(
            "admin.audit06@test.invalid", cls.password, display_name="Admin Audit06", role=cls.admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "wh.audit06@test.invalid", cls.password, display_name="Lucía Almacén06", role=cls.warehouse_role
        )
        cls.warehouse2 = Account.objects.create_user(
            "wh2.audit06@test.invalid", cls.password, display_name="Pedro Almacén06", role=cls.warehouse_role
        )
        cls.seller = Account.objects.create_user(
            "seller.audit06@test.invalid", cls.password, display_name="Carlos Vendedor06", role=cls.seller_role
        )

        cls.cat_active = Category.objects.create(name="Abarrotes Audit06")
        cls.cat_inactive = Category.objects.create(name="Categoría Suspendida Audit06", is_active=False)

        cls.prod_loaded = Product.objects.create(
            category=cls.cat_active,
            name="Aceite Vegetal 1L",
            barcode="775060010001",
            sale_price=Decimal("9.50"),
            minimum_stock=10,
        )
        cls.prod_exhausted = Product.objects.create(
            category=cls.cat_active,
            name="Arroz Extra 1kg",
            barcode="775060010002",
            sale_price=Decimal("4.80"),
            minimum_stock=5,
        )
        cls.prod_expired_only = Product.objects.create(
            category=cls.cat_active,
            name="Yogurt Vencido Audit06",
            barcode="775060010003",
            sale_price=Decimal("6.00"),
            minimum_stock=5,
        )
        cls.prod_no_load = Product.objects.create(
            category=cls.cat_active,
            name="Producto Sin Carga Audit06",
            barcode="775060010004",
            sale_price=Decimal("5.00"),
        )
        cls.prod_inactive_loaded = Product.objects.create(
            category=cls.cat_active,
            name="Producto Inactivo Con Carga",
            barcode="775060010005",
            sale_price=Decimal("5.20"),
        )
        cls.prod_catoff_loaded = Product.objects.create(
            category=cls.cat_active,
            name="Producto Cat Off Con Carga",
            barcode="775060010006",
            sale_price=Decimal("5.40"),
        )

        cls.supplier_active = Supplier.objects.create(
            name="Distribuidora Alfa Audit06 SAC", ruc="20606010001", phone="01-5550101"
        )
        cls.supplier_long = Supplier.objects.create(
            name=(
                "Corporacion Logistica Integral de Abastecimiento Alimentario del Pacifico Sur "
                "Sociedad Anonima Cerrada Distribuida en Almacenes de Lima Metropolitana y Callao SAC"
            )[:160],
            ruc="20606010002",
            phone="01-5550102",
        )
        cls.supplier_inactive = Supplier.objects.create(
            name="Proveedor Inactivo Audit06", ruc="20606010003", is_active=False
        )
        cls.register = CashRegister.objects.create(code="CAJA-A06")

    def _lot_payload(self, product, lots_rows, supplier_id=""):
        data = {
            "idempotency_key": str(uuid.uuid4()),
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

    # ── Elegibilidad y sentinels de proveedor ────────────────────────────────

    def test_eligible_products_and_suppliers_queryset_and_sentinels(self) -> None:
        today = timezone.localdate()
        future = today + timedelta(days=30)

        confirm_initial_load(
            actor=self.warehouse,
            product=self.prod_loaded,
            supplier=self.supplier_active,
            lots=[LotInput("INI-1", 4, Decimal("2.0000"), future)],
        )
        confirm_initial_load(
            actor=self.warehouse,
            product=self.prod_exhausted,
            lots=[LotInput("EXH-1", 2, Decimal("3.0000"), future)],
        )
        Lot.objects.filter(product=self.prod_exhausted).update(available_quantity=0)
        confirm_initial_load(
            actor=self.warehouse,
            product=self.prod_expired_only,
            lots=[LotInput("EXP-1", 3, Decimal("4.0000"), today + timedelta(days=1))],
        )
        Lot.objects.filter(product=self.prod_expired_only).update(expiration_date=today)

        confirm_initial_load(
            actor=self.warehouse,
            product=self.prod_inactive_loaded,
            lots=[LotInput("INO-1", 2, Decimal("2.0000"), future)],
        )
        self.prod_inactive_loaded.is_active = False
        self.prod_inactive_loaded.save(update_fields=["is_active"])

        confirm_initial_load(
            actor=self.warehouse,
            product=self.prod_catoff_loaded,
            lots=[LotInput("CTO-1", 2, Decimal("2.0000"), future)],
        )
        self.prod_catoff_loaded.category = self.cat_inactive
        self.prod_catoff_loaded.save(update_fields=["category"])

        form = StockEntryProductForm()
        prod_qs = set(form.fields["product"].queryset.values_list("pk", flat=True))
        self.assertIn(self.prod_loaded.pk, prod_qs)
        self.assertIn(self.prod_exhausted.pk, prod_qs)
        self.assertIn(self.prod_expired_only.pk, prod_qs)
        self.assertNotIn(self.prod_no_load.pk, prod_qs)
        self.assertNotIn(self.prod_inactive_loaded.pk, prod_qs)
        self.assertNotIn(self.prod_catoff_loaded.pk, prod_qs)

        sup_qs = set(form.fields["supplier"].queryset.values_list("pk", flat=True))
        self.assertIn(self.supplier_active.pk, sup_qs)
        self.assertNotIn(self.supplier_inactive.pk, sup_qs)

        # Enviar proveedor inactivo conserva sentinel __inactive__ y rechaza; al cambiar a activo sí registra
        self.client.force_login(self.warehouse)
        rejected = self.client.post(
            reverse("stock-entry"),
            self._lot_payload(
                self.prod_loaded,
                [{"number": "SENT-1", "quantity": "2", "unit_cost": "3.0000", "expiration_date": future.isoformat()}],
                supplier_id=self.supplier_inactive.pk,
            ),
        )
        self.assertEqual(rejected.status_code, 200)
        self.assertContains(rejected, f"__inactive__:{self.supplier_inactive.pk}")
        self.assertContains(rejected, "está inactivo")
        self.assertFalse(Lot.objects.filter(product=self.prod_loaded, number_normalized="SENT-1").exists())

        # Reenviar el sentinel generado tampoco pasa
        sentinel_resubmit = self.client.post(
            reverse("stock-entry"),
            self._lot_payload(
                self.prod_loaded,
                [{"number": "SENT-1", "quantity": "2", "unit_cost": "3.0000", "expiration_date": future.isoformat()}],
                supplier_id=f"__inactive__:{self.supplier_inactive.pk}",
            ),
        )
        self.assertEqual(sentinel_resubmit.status_code, 200)
        self.assertContains(sentinel_resubmit, "está inactivo")

        # Cambio a proveedor activo registra limpiamente
        ok_resp = self.client.post(
            reverse("stock-entry"),
            self._lot_payload(
                self.prod_loaded,
                [{"number": "SENT-1", "quantity": "2", "unit_cost": "3.0000", "expiration_date": future.isoformat()}],
                supplier_id=self.supplier_active.pk,
            ),
        )
        self.assertRedirects(
            ok_resp, reverse("stock-receipt", args=(StockReceipt.objects.get(product=self.prod_loaded).pk,))
        )

    # ── FIX06-01, management_form y validación no enmascarada ────────────────

    def test_empty_post_header_csrf_tampered_management_forms_and_non_masking_validation(self) -> None:
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)
        future = today + timedelta(days=30)
        confirm_initial_load(
            actor=self.warehouse,
            product=self.prod_loaded,
            lots=[LotInput("INI-BASE", 5, Decimal("2.0000"), future)],
        )

        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.warehouse)
        csrf_client.get(reverse("stock-entry"))
        tok = csrf_client.cookies["csrftoken"].value

        # FIX06-01: POST vacío con X-CSRFToken ya no queda unbound
        r_empty = csrf_client.post(reverse("stock-entry"), data={}, HTTP_X_CSRFTOKEN=tok)
        self.assertEqual(r_empty.status_code, 200)
        self.assertContains(r_empty, "Seleccione un producto.")
        self.assertContains(r_empty, "1 formulario como mínimo")

        # Filas en blanco
        r_blank = csrf_client.post(
            reverse("stock-entry"),
            {**self._lot_payload(self.prod_loaded, [{}, {}, {}, {}]), "csrfmiddlewaretoken": tok},
        )
        self.assertEqual(r_blank.status_code, 200)
        self.assertContains(r_blank, "1 formulario como mínimo")

        # Tampering de management_form
        for payload in (
            {"product": str(self.prod_loaded.pk), "csrfmiddlewaretoken": tok},
            {
                "product": str(self.prod_loaded.pk),
                "lots-TOTAL_FORMS": "-1",
                "lots-INITIAL_FORMS": "0",
                "lots-MIN_NUM_FORMS": "1",
                "lots-MAX_NUM_FORMS": "1000",
                "csrfmiddlewaretoken": tok,
            },
            {
                "product": str(self.prod_loaded.pk),
                "lots-TOTAL_FORMS": "abc",
                "lots-INITIAL_FORMS": "0",
                "lots-MIN_NUM_FORMS": "1",
                "lots-MAX_NUM_FORMS": "1000",
                "csrfmiddlewaretoken": tok,
            },
            {
                "product": str(self.prod_loaded.pk),
                "lots-TOTAL_FORMS": "5000",
                "lots-INITIAL_FORMS": "0",
                "lots-MIN_NUM_FORMS": "1",
                "lots-MAX_NUM_FORMS": "1000",
                "csrfmiddlewaretoken": tok,
            },
        ):
            r = csrf_client.post(reverse("stock-entry"), payload)
            self.assertEqual(r.status_code, 200)
            self.assertContains(r, 'role="alert"')

        # Combo multi-error sin enmascarar errores posteriores + dígitos árabes / coma / notación científica / NUL
        r_combo = csrf_client.post(
            reverse("stock-entry"),
            {
                **self._lot_payload(
                    self.prod_loaded,
                    [
                        {"number": "dup-e", "quantity": "0", "unit_cost": "1e2", "expiration_date": tomorrow.isoformat()},
                        {"number": "OK-E2", "quantity": "٥", "unit_cost": "1,50", "expiration_date": today.isoformat()},
                        {"number": " DUP-E ", "quantity": "3", "unit_cost": "2.00", "expiration_date": tomorrow.isoformat()},
                    ],
                ),
                "csrfmiddlewaretoken": tok,
            },
        )
        self.assertEqual(r_combo.status_code, 200)
        self.assertContains(r_combo, "notación científica")
        self.assertContains(r_combo, "posterior a hoy en Lima")
        self.assertContains(r_combo, "está repetido")
        self.assertContains(r_combo, "ASCII")

        # Byte NUL en número y producto
        r_nul = csrf_client.post(
            reverse("stock-entry"),
            {
                **self._lot_payload(
                    self.prod_loaded,
                    [{"number": "L\x00BAD", "quantity": "2", "unit_cost": "1.00", "expiration_date": tomorrow.isoformat()}],
                ),
                "csrfmiddlewaretoken": tok,
            },
        )
        self.assertEqual(r_nul.status_code, 200)
        self.assertContains(r_nul, 'role="alert"')
        self.assertEqual(Lot.objects.filter(product=self.prod_loaded).count(), 1)

    # ── Servicio: promedio ponderado HALF_UP, ceros previos y FIX06-02 ───────

    def test_weighted_cost_half_up_zero_prior_stock_atomic_and_fix06_02_savepoint(self) -> None:
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)
        future = today + timedelta(days=40)

        # 1. Empate exacto .12345 con HALF_UP -> 1.1235
        confirm_initial_load(
            actor=self.warehouse,
            product=self.prod_loaded,
            lots=[LotInput("HALF-0", 1, Decimal("1.0000"), future)],
        )
        register_stock_entry(
            actor=self.warehouse2,
            product=self.prod_loaded,
            lots=[LotInput("HALF-1", 1, Decimal("1.2469"), future)],
        )
        self.prod_loaded.refresh_from_db()
        self.assertEqual(self.prod_loaded.average_cost, Decimal("1.1235"))

        # 2. Producto agotado (previous_quantity == 0) toma costo entrante
        confirm_initial_load(
            actor=self.warehouse,
            product=self.prod_exhausted,
            lots=[LotInput("EXH-OLD", 3, Decimal("2.0000"), future)],
        )
        Lot.objects.filter(product=self.prod_exhausted).update(available_quantity=0)
        register_stock_entry(
            actor=self.warehouse,
            product=self.prod_exhausted,
            lots=[LotInput("EXH-NEW", 4, Decimal("5.5000"), future)],
        )
        self.prod_exhausted.refresh_from_db()
        self.assertEqual(self.prod_exhausted.average_cost, Decimal("5.5000"))

        # 3. DOC-03AH-01 vigente incluye todas las unidades físicas, también las vencidas.
        confirm_initial_load(
            actor=self.warehouse,
            product=self.prod_expired_only,
            lots=[LotInput("EXP-OLD", 5, Decimal("2.0000"), tomorrow)],
        )
        Lot.objects.filter(product=self.prod_expired_only).update(expiration_date=today)
        register_stock_entry(
            actor=self.warehouse,
            product=self.prod_expired_only,
            lots=[LotInput("EXP-NEW", 5, Decimal("6.0000"), future)],
        )
        self.prod_expired_only.refresh_from_db()
        self.assertEqual(self.prod_expired_only.average_cost, Decimal("4.0000"))

        # DOC03AI allows another delivery; a contradictory expiration still rejects the whole attempt.
        before_lots = list(Lot.objects.filter(product=self.prod_loaded).order_by("pk").values())
        for dup_name in ("  half-0  ", "HALF-1"):
            with self.assertRaises(ValidationError):
                register_stock_entry(
                    actor=self.warehouse,
                    product=self.prod_loaded,
                    lots=[
                        LotInput("NEW-SHOULD-ROLLBACK", 3, Decimal("9.0000"), future),
                        LotInput(dup_name, 2, Decimal("3.0000"), future + timedelta(days=1)),
                    ],
                )
        self.prod_loaded.refresh_from_db()
        self.assertEqual(self.prod_loaded.average_cost, Decimal("1.1235"))
        self.assertEqual(list(Lot.objects.filter(product=self.prod_loaded).order_by("pk").values()), before_lots)

        # 5. Sin carga inicial / inexistente / controles expiracion False (FIX06-02)
        with self.assertRaisesMessage(ValidationError, "no tiene carga inicial confirmada"):
            register_stock_entry(
                actor=self.warehouse,
                product=self.prod_no_load,
                lots=[LotInput("NL-1", 1, Decimal("2.0000"), future)],
            )
        with self.assertRaisesMessage(ValidationError, "ya no existe"):
            register_stock_entry(
                actor=self.warehouse,
                product=Product(pk=uuid.uuid4(), category=self.cat_active, name="X", barcode="X", sale_price=Decimal("2.00")),
                lots=[LotInput("MISS-1", 1, Decimal("2.0000"), future)],
            )
        locked_like = Product(
            pk=self.prod_loaded.pk,
            category=self.cat_active,
            name=self.prod_loaded.name,
            barcode=self.prod_loaded.barcode,
            sale_price=self.prod_loaded.sale_price,
            is_active=True,
            controls_expiration=False,
        )
        with patch.object(Product.objects, "select_for_update") as mock_sfu:
            mock_sfu.return_value.filter.return_value.first.return_value = locked_like
            with self.assertRaisesMessage(ValidationError, "no está disponible para registrar entradas"):
                register_stock_entry(
                    actor=self.warehouse,
                    product=self.prod_loaded,
                    lots=[LotInput("NOEXP-1", 1, Decimal("2.0000"), future)],
                )

        # 6. FIX06-02 Savepoint IntegrityError traducido limpiamente dentro de transaction.atomic() exterior
        with patch.object(Lot.objects, "bulk_create", side_effect=IntegrityError("colisión única")):
            with self.assertRaisesMessage(ValidationError, "entró en conflicto"):
                with transaction.atomic():
                    register_stock_entry(
                        actor=self.warehouse,
                        product=self.prod_loaded,
                        lots=[LotInput("SAVEPOINT-1", 2, Decimal("3.0000"), future)],
                    )
        self.assertEqual(list(Lot.objects.filter(product=self.prod_loaded).order_by("pk").values()), before_lots)

        # 7. CT-ROLLBACK-01: RuntimeError inesperado revierte por completo lotes y promedio
        with patch.object(Lot.objects, "bulk_create", side_effect=RuntimeError("caída simulada")):
            with self.assertRaises(RuntimeError):
                register_stock_entry(
                    actor=self.warehouse,
                    product=self.prod_loaded,
                    lots=[LotInput("RB-E1", 2, Decimal("50.0000"), future)],
                )
        self.prod_loaded.refresh_from_db()
        self.assertEqual(self.prod_loaded.average_cost, Decimal("1.1235"))
        self.assertEqual(list(Lot.objects.filter(product=self.prod_loaded).order_by("pk").values()), before_lots)

    # ── Trazabilidad de lotes, constancia, Kardex, inmutabilidad y RN-28 ─────

    def test_lot_preservation_kardex_constancia_received_at_and_rn28_pos_fefo(self) -> None:
        today = timezone.localdate()
        t_init = datetime(2026, 11, 11, 9, 0, tzinfo=dt_timezone.utc)
        t_entry = datetime(2026, 11, 11, 11, 30, tzinfo=dt_timezone.utc)

        with patch("django.utils.timezone.now", return_value=t_init):
            load = confirm_initial_load(
                actor=self.warehouse,
                product=self.prod_loaded,
                supplier=self.supplier_active,
                lots=[LotInput("INI-R28", 4, Decimal("2.0000"), today + timedelta(days=30))],
            )

        # Venta previa a la reposición (unit_cost == 2.0000)
        CashShift.objects.create(cash_register=self.register, seller=self.seller, opening_amount=Decimal("50.00"))
        d1 = add_product_to_draft(actor=self.seller, product_id=self.prod_loaded.pk, quantity=1)
        sale_before = checkout_sale(
            actor=self.seller, draft_id=d1.pk, cash_received=Decimal("20.00"), idempotency_key=uuid.uuid4()
        )
        old_line = SaleLine.objects.get(sale=sale_before)
        self.assertEqual(old_line.unit_cost, Decimal("2.0000"))

        # Entrada posterior via HTTP por segundo almacenero, proveedor largo 160 chars, lote 64 chars y fila en blanco
        # Quedan 3 x 2.0000 = 6.0000 + (2 x 4.0000 + 3 x 6.0000) = 6 + 26 = 32 / 8 = 4.0000
        long_lot = "R" * 64
        self.client.force_login(self.warehouse2)
        with patch("django.utils.timezone.now", return_value=t_entry):
            entry_resp = self.client.post(
                reverse("stock-entry"),
                self._lot_payload(
                    self.prod_loaded,
                    [
                        {"number": long_lot, "quantity": "2", "unit_cost": "4.0000", "expiration_date": (today + timedelta(days=10)).isoformat()},
                        {},
                        {"number": "POST-60D", "quantity": "3", "unit_cost": "6.0000", "expiration_date": (today + timedelta(days=60)).isoformat()},
                        {},
                    ],
                    supplier_id=self.supplier_long.pk,
                ),
            )
        receipt = StockReceipt.objects.get(product=self.prod_loaded)
        self.assertRedirects(entry_resp, reverse("stock-receipt", args=(receipt.pk,)))
        self.prod_loaded.refresh_from_db()
        self.assertEqual(self.prod_loaded.average_cost, Decimal("4.0000"))
        self.assertEqual(self.prod_loaded.sellable_stock, 8)

        # Verifica lotes, is_initial y responsible por lote + inmutabilidad received_at en entradas posteriores
        ini_lot = Lot.objects.get(product=self.prod_loaded, number_normalized="INI-R28")
        sub_early = Lot.objects.get(product=self.prod_loaded, number_normalized=long_lot)
        sub_late = Lot.objects.get(product=self.prod_loaded, number_normalized="POST-60D")
        self.assertTrue(ini_lot.is_initial)
        self.assertFalse(sub_early.is_initial)
        self.assertFalse(sub_late.is_initial)
        self.assertEqual(ini_lot.responsible, self.warehouse)
        self.assertEqual(sub_early.responsible, self.warehouse2)
        self.assertEqual(sub_late.supplier, self.supplier_long)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Lot.objects.filter(pk=sub_early.pk).update(received_at=t_init)
        with self.assertRaises(IntegrityError), transaction.atomic():
            raw_pk = sub_early.pk.hex if connection.vendor == "sqlite" else str(sub_early.pk)
            with connection.cursor() as cur:
                cur.execute("UPDATE inventory_lot SET received_at = %s WHERE id = %s", [t_init, raw_pk])

        # Carga conserva sus lotes; la recepción tiene documento propio con sus snapshots.
        cert_resp = self.client.get(reverse("inventory-load-created", args=(load.pk,)))
        self.assertContains(cert_resp, "Recepciones con constancia propia")
        self.assertContains(cert_resp, self.warehouse.display_name)
        self.assertContains(cert_resp, self.warehouse2.display_name)
        cert_resp = self.client.get(reverse("stock-receipt", args=(receipt.pk,)))
        self.assertContains(cert_resp, self.supplier_long.name)
        self.assertContains(cert_resp, long_lot)
        self.assertContains(cert_resp, "S/ 4,00")

        # Kardex distingue Carga inicial vs Entrada de mercadería
        mov_resp = self.client.get(reverse("product-movements", args=(self.prod_loaded.pk,)))
        self.assertContains(mov_resp, f"Carga inicial — Lote INI-R28 ({self.supplier_active.name})")
        self.assertContains(mov_resp, f"Recepción {receipt.correlative} — Lote {long_lot} ({self.supplier_long.name})")
        self.assertContains(mov_resp, "Venta V-")

        # Venta posterior consume por FEFO (primero el lote de +10 días = sub_early (2u), luego +30 días = ini_lot (1u))
        # y guarda nuevo snapshot unit_cost == 4.0000 sin alterar la venta previa (RN-28)
        d2 = add_product_to_draft(actor=self.seller, product_id=self.prod_loaded.pk, quantity=3)
        sale_after = checkout_sale(
            actor=self.seller, draft_id=d2.pk, cash_received=Decimal("40.00"), idempotency_key=uuid.uuid4()
        )
        old_line.refresh_from_db()
        new_line = SaleLine.objects.get(sale=sale_after)
        self.assertEqual(old_line.unit_cost, Decimal("2.0000"))
        self.assertEqual(new_line.unit_cost, Decimal("4.0000"))

        sub_early.refresh_from_db()
        ini_lot.refresh_from_db()
        sub_late.refresh_from_db()
        self.assertEqual(sub_early.available_quantity, 0)
        self.assertEqual(ini_lot.available_quantity, 2)
        self.assertEqual(sub_late.available_quantity, 3)

        # Constancia sigue conservando cantidades iniciales/ingresadas originales pese a ventas
        cert_after = self.client.get(reverse("inventory-load-created", args=(load.pk,)))
        self.assertEqual(cert_after.context["lots"][0].original_initial_quantity, 4)

    # ── RN-29, @never_cache, revocación y frontera PREVISTO/FUTURO ───────────

    def test_role_matrix_cache_control_actor_revocation_and_no_hu_sol_routes(self) -> None:
        future = (timezone.localdate() + timedelta(days=30)).isoformat()
        future_date = timezone.localdate() + timedelta(days=30)
        confirm_initial_load(
            actor=self.warehouse,
            product=self.prod_loaded,
            lots=[LotInput("PERM-0", 5, Decimal("2.0000"), future_date)],
        )

        # Anónimo redirige a login
        anon = Client()
        r_anon = anon.get(reverse("stock-entry"))
        self.assertEqual(r_anon.status_code, 302)
        self.assertEqual(r_anon["Location"], f"/?next={reverse('stock-entry')}")

        # VENDEDOR y ADMIN reciben 403 en GET y POST sin mutar lotes
        before_lots = Lot.objects.count()
        for actor in (self.seller, self.admin):
            with self.subTest(role=actor.role.code):
                self.client.force_login(actor)
                self.assertEqual(self.client.get(reverse("stock-entry")).status_code, 403)
                self.assertEqual(
                    self.client.post(
                        reverse("stock-entry"),
                        self._lot_payload(
                            self.prod_loaded,
                            [{"number": "NOPE", "quantity": "1", "unit_cost": "1.00", "expiration_date": future}],
                        ),
                    ).status_code,
                    403,
                )
        self.assertEqual(Lot.objects.count(), before_lots)

        # ALMACENERO obtiene no-store / no-cache
        self.client.force_login(self.warehouse)
        r_wh = self.client.get(reverse("stock-entry"))
        self.assertEqual(r_wh.status_code, 200)
        self.assertIn("no-store", r_wh.headers.get("Cache-Control", ""))
        self.assertIn("no-cache", r_wh.headers.get("Cache-Control", ""))

        # Suspensión concurrente de categoría / producto bloquea en servicio
        toggle_category_status(actor=self.admin, category=self.cat_active, is_active=False)
        with self.assertRaisesMessage(ValidationError, "no está disponible para registrar entradas"):
            register_stock_entry(
                actor=self.warehouse,
                product=self.prod_loaded,
                lots=[LotInput("CAT-LOCK", 1, Decimal("2.00"), future_date)],
            )
        toggle_category_status(actor=self.admin, category=self.cat_active, is_active=True)
        toggle_product_availability(actor=self.admin, product=self.prod_loaded, is_active=False)
        with self.assertRaisesMessage(ValidationError, "no está disponible para registrar entradas"):
            register_stock_entry(
                actor=self.warehouse,
                product=self.prod_loaded,
                lots=[LotInput("PROD-LOCK", 1, Decimal("2.00"), future_date)],
            )
        toggle_product_availability(actor=self.admin, product=self.prod_loaded, is_active=True)

        # Actor revocado / rol cambiado / anónimo rechazado con PermissionDenied
        stale_wh = Account.objects.select_related("role").get(pk=self.warehouse2.pk)
        deactivate_employee(actor=self.admin, account=Account.objects.get(pk=self.warehouse2.pk))
        with self.assertRaises(PermissionDenied):
            register_stock_entry(
                actor=stale_wh,
                product=self.prod_loaded,
                lots=[LotInput("REV-1", 1, Decimal("2.00"), future_date)],
            )
        Account.objects.filter(pk=self.warehouse2.pk).update(is_active=True)
        update_employee(
            actor=self.admin,
            account=Account.objects.get(pk=self.warehouse2.pk),
            display_name=self.warehouse2.display_name,
            email=self.warehouse2.email,
            role=self.seller_role,
        )
        with self.assertRaises(PermissionDenied):
            register_stock_entry(
                actor=stale_wh,
                product=self.prod_loaded,
                lots=[LotInput("DEM-1", 1, Decimal("2.00"), future_date)],
            )
        with self.assertRaises(PermissionDenied):
            register_stock_entry(
                actor=AnonymousUser(),
                product=self.prod_loaded,
                lots=[LotInput("ANON-1", 1, Decimal("2.00"), future_date)],
            )

        # Frontera PREVISTO/FUTURO: cero rutas de solicitudes de reposición HU-SOL-* en URL resolver
        def _collect(patterns, prefix=""):
            found = []
            for p in patterns:
                if isinstance(p, URLPattern):
                    found.append(f"{prefix}{p.pattern}::{p.name or ''}")
                elif isinstance(p, URLResolver):
                    found.extend(_collect(p.url_patterns, f"{prefix}{p.pattern}"))
            return found

        all_urls = _collect(get_resolver().url_patterns)
        sol_matches = [
            u for u in all_urls
            if any(tok in u.lower() for tok in ("solicitud", "replenish", "reposicion", "sol-"))
        ]
        self.assertEqual(sol_matches, [])
