from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from cash.models import CashRegister, CashShift
from catalog.models import Category, Product
from catalog.services import update_product
from identity.models import Account, Role
from inventory.forms import PhysicalAdjustmentForm, StockWriteOffForm
from inventory.models import InitialInventoryLoad, Lot, PhysicalAdjustment, StockWriteOff, Supplier
from inventory.services import (
    LotInput,
    confirm_initial_load,
    register_physical_adjustment,
    register_stock_entry,
    write_off_stock,
)
from sales.models import Sale, SaleLine
from sales.services import add_product_to_draft, checkout_sale, sellable_stock_for_product


class Stage08WriteOffsAdjustmentsMovementsTests(TestCase):
    password = "Audit08#TestPass123"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

        cls.admin = Account.objects.create_user(
            "admin.audit08@test.invalid", cls.password, display_name="Admin Audit08", role=cls.admin_role
        )
        cls.wh1 = Account.objects.create_user(
            "wh1.audit08@test.invalid", cls.password, display_name="Lucia Almacen08", role=cls.wh_role
        )
        cls.wh2 = Account.objects.create_user(
            "wh2.audit08@test.invalid", cls.password, display_name="Pedro Almacen08", role=cls.wh_role
        )
        cls.seller = Account.objects.create_user(
            "seller.audit08@test.invalid", cls.password, display_name="Carmen Vendedora08", role=cls.seller_role
        )

        cls.category = Category.objects.create(name="Abarrotes Audit08")
        cls.supplier1 = Supplier.objects.create(name="Proveedor Uno 08", ruc="20808080001")
        cls.supplier2 = Supplier.objects.create(name="Proveedor Dos 08", ruc="20808080002")

        cls.register = CashRegister.objects.create(code="CAJA-A08")
        cls.shift = CashShift.objects.create(
            cash_register=cls.register, seller=cls.seller, opening_amount=Decimal("50.00")
        )

    def _create_loaded_product(
        self,
        *,
        name: str,
        barcode: str,
        lots: list[LotInput],
        sale_price: Decimal = Decimal("8.00"),
        minimum_stock: int = 5,
        supplier: Supplier | None = None,
    ) -> tuple[Product, InitialInventoryLoad]:
        product = Product.objects.create(
            category=self.category,
            name=name,
            barcode=barcode,
            sale_price=sale_price,
            minimum_stock=minimum_stock,
        )
        load = confirm_initial_load(
            actor=self.wh1,
            product=product,
            lots=lots,
            supplier=supplier,
        )
        product.refresh_from_db()
        return product, load

    # ── Matriz de roles, anónimo y @never_cache ─────────────────────────────

    def test_role_matrix_and_cache_control(self) -> None:
        today = timezone.localdate()
        prod, load = self._create_loaded_product(
            name="Arroz Roles 08",
            barcode="775080000101",
            lots=[LotInput("ROL-01", 15, Decimal("3.0000"), today + timedelta(days=45))],
        )
        lot = load.lots.get()

        anon = Client()
        for url in (
            reverse("stock-writeoff"),
            f"{reverse('stock-writeoff')}?lote={lot.pk}",
            reverse("physical-adjustment"),
            f"{reverse('physical-adjustment')}?lote={lot.pk}",
            reverse("product-movements", args=(prod.pk,)),
        ):
            res = anon.get(url)
            self.assertEqual(res.status_code, 302)
            self.assertIn("next=", res["Location"])

        self.assertEqual(
            anon.post(
                f"{reverse('stock-writeoff')}?lote={lot.pk}",
                {"lot_id": str(lot.pk), "quantity": "1", "reason": "VENCIMIENTO"},
            ).status_code,
            302,
        )
        self.assertEqual(
            anon.post(
                f"{reverse('physical-adjustment')}?lote={lot.pk}",
                {"lot_id": str(lot.pk), "delta": "1", "reason": "Test"},
            ).status_code,
            302,
        )

        # VENDEDOR: 403 en GET y POST sin mutación
        self.client.force_login(self.seller)
        self.assertEqual(self.client.get(reverse("stock-writeoff")).status_code, 403)
        self.assertEqual(
            self.client.post(
                f"{reverse('stock-writeoff')}?lote={lot.pk}",
                {"lot_id": str(lot.pk), "quantity": "1", "reason": "VENCIMIENTO"},
            ).status_code,
            403,
        )
        self.assertEqual(self.client.get(reverse("physical-adjustment")).status_code, 403)
        self.assertEqual(
            self.client.post(
                f"{reverse('physical-adjustment')}?lote={lot.pk}",
                {"lot_id": str(lot.pk), "delta": "1", "reason": "Test"},
            ).status_code,
            403,
        )
        self.assertEqual(self.client.get(reverse("product-movements", args=(prod.pk,))).status_code, 403)

        # ALMACENERO: permitido writeoff + movements, 403 en ajuste físico (GET y POST)
        self.client.force_login(self.wh1)
        r_wo_get = self.client.get(reverse("stock-writeoff"))
        r_mov_get = self.client.get(reverse("product-movements", args=(prod.pk,)))
        self.assertEqual(r_wo_get.status_code, 200)
        self.assertIn("no-store", r_wo_get.headers.get("Cache-Control", ""))
        self.assertEqual(r_mov_get.status_code, 200)
        self.assertIn("no-store", r_mov_get.headers.get("Cache-Control", ""))
        self.assertEqual(self.client.get(reverse("physical-adjustment")).status_code, 403)
        self.assertEqual(
            self.client.post(
                f"{reverse('physical-adjustment')}?lote={lot.pk}",
                {"lot_id": str(lot.pk), "delta": "2", "reason": "No autorizado"},
            ).status_code,
            403,
        )

        # ADMIN: acceso a todas + @never_cache
        self.client.force_login(self.admin)
        for url in (
            reverse("stock-writeoff"),
            reverse("physical-adjustment"),
            reverse("product-movements", args=(prod.pk,)),
        ):
            resp = self.client.get(url)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("no-store", resp.headers.get("Cache-Control", ""))

        lot.refresh_from_db()
        self.assertEqual(lot.available_quantity, 15)
        self.assertFalse(StockWriteOff.objects.exists())
        self.assertFalse(PhysicalAdjustment.objects.exists())

    # ── DEF08-02: Guards de actor bloqueado y lote inexistente ──────────────

    def test_actor_lock_and_missing_lot_guards_in_services(self) -> None:
        today = timezone.localdate()
        prod, load = self._create_loaded_product(
            name="Guardas Actor 08",
            barcode="775080000102",
            lots=[LotInput("GRD-01", 10, Decimal("2.0000"), today + timedelta(days=30))],
        )
        lot = load.lots.get()

        with self.assertRaises(PermissionDenied):
            write_off_stock(actor=AnonymousUser(), lot=lot, quantity=1, reason="VENCIMIENTO")
        with self.assertRaises(PermissionDenied):
            register_physical_adjustment(actor=AnonymousUser(), lot=lot, delta=1, reason="Test")
        with self.assertRaises(PermissionDenied):
            write_off_stock(actor=self.seller, lot=lot, quantity=1, reason="VENCIMIENTO")
        with self.assertRaises(PermissionDenied):
            register_physical_adjustment(actor=self.wh1, lot=lot, delta=1, reason="Test")

        # Actor obsoleto en memoria luego desactivado/degradado en BD
        stale_wh = Account.objects.create_user(
            "stale.wh@test.invalid", self.password, display_name="Stale WH", role=self.wh_role
        )
        stale_admin = Account.objects.create_user(
            "stale.adm@test.invalid", self.password, display_name="Stale ADM", role=self.admin_role
        )
        Account.objects.filter(pk=stale_wh.pk).update(is_active=False)
        Account.objects.filter(pk=stale_admin.pk).update(role=self.seller_role)

        with self.assertRaises(PermissionDenied):
            write_off_stock(actor=stale_wh, lot=lot, quantity=1, reason="VENCIMIENTO")
        with self.assertRaises(PermissionDenied):
            register_physical_adjustment(actor=stale_admin, lot=lot, delta=1, reason="Demoted")

        # Lote None / sin guardar / UUID inexistente -> ValidationError sin DoesNotExist ni AttributeError
        for bad_lot in (None, Lot(product=prod), Lot(id=uuid.uuid4(), product=prod)):
            with self.assertRaises(ValidationError):
                write_off_stock(actor=self.wh1, lot=bad_lot, quantity=1, reason="VENCIMIENTO")
            with self.assertRaises(ValidationError):
                register_physical_adjustment(actor=self.admin, lot=bad_lot, delta=1, reason="Missing")

        lot.refresh_from_db()
        self.assertEqual(lot.available_quantity, 10)
        self.assertFalse(StockWriteOff.objects.exists())
        self.assertFalse(PhysicalAdjustment.objects.exists())

    # ── DEF08-01 & DEF08-03: Validaciones HTTP, tipos y límites ──────────────

    def test_empty_post_no_500_and_strict_type_digit_null_validations(self) -> None:
        today = timezone.localdate()
        prod, load = self._create_loaded_product(
            name="Validaciones 08",
            barcode="775080000103",
            lots=[LotInput("VAL-01", 20, Decimal("2.0000"), today + timedelta(days=30))],
        )
        lot = load.lots.get()

        self.client.force_login(self.admin)

        # POST vacío sin ?lote= y con ?lote=: jamás 500, siempre 200 con error visible
        for url in (
            reverse("stock-writeoff"),
            f"{reverse('stock-writeoff')}?lote={lot.pk}",
            reverse("physical-adjustment"),
            f"{reverse('physical-adjustment')}?lote={lot.pk}",
        ):
            r_empty = self.client.post(url, data={})
            self.assertEqual(r_empty.status_code, 200)
            self.assertIn("alert-danger", r_empty.content.decode())

        # Formularios rechazan dígitos Unicode no ASCII ("٥"), guiones bajos ("1_0") y byte nulo
        self.assertFalse(
            StockWriteOffForm(
                data={"lot_id": str(lot.pk), "quantity": "٥", "reason": "VENCIMIENTO", "notes": ""}
            ).is_valid()
        )
        self.assertFalse(
            StockWriteOffForm(
                data={"lot_id": str(lot.pk), "quantity": "1_0", "reason": "VENCIMIENTO", "notes": ""}
            ).is_valid()
        )
        self.assertFalse(
            StockWriteOffForm(
                data={"lot_id": str(lot.pk), "quantity": "1", "reason": "DAÑO", "notes": "roto\x00x"}
            ).is_valid()
        )
        self.assertFalse(
            PhysicalAdjustmentForm(
                data={"lot_id": str(lot.pk), "delta": "٥", "reason": "Conteo"}
            ).is_valid()
        )
        self.assertFalse(
            PhysicalAdjustmentForm(
                data={"lot_id": str(lot.pk), "delta": "1_0", "reason": "Conteo"}
            ).is_valid()
        )
        self.assertFalse(
            PhysicalAdjustmentForm(
                data={"lot_id": str(lot.pk), "delta": "+2", "reason": "x\x00y"}
            ).is_valid()
        )
        # +10 explícito en PhysicalAdjustmentForm SÍ debe aceptarse según ayuda en pantalla
        f_plus = PhysicalAdjustmentForm(
            data={"lot_id": str(lot.pk), "delta": "+10", "reason": "Conteo con +10"}
        )
        self.assertTrue(f_plus.is_valid())
        self.assertEqual(f_plus.cleaned_data["delta"], 10)

        # Servicios rechazan bool, byte nulo, overflow y reason > 300 chars sin mutar
        with self.assertRaises(ValidationError):
            write_off_stock(actor=self.wh1, lot=lot, quantity=True, reason="VENCIMIENTO")
        with self.assertRaises(ValidationError):
            write_off_stock(actor=self.wh1, lot=lot, quantity=0, reason="VENCIMIENTO")
        with self.assertRaises(ValidationError):
            write_off_stock(actor=self.wh1, lot=lot, quantity=1_000_000, reason="VENCIMIENTO")
        with self.assertRaises(ValidationError):
            write_off_stock(actor=self.wh1, lot=lot, quantity=21, reason="VENCIMIENTO")
        with self.assertRaises(ValidationError):
            write_off_stock(actor=self.wh1, lot=lot, quantity=1, reason="DAÑO", notes="   ")
        with self.assertRaises(ValidationError):
            write_off_stock(actor=self.wh1, lot=lot, quantity=1, reason="DAÑO", notes="a\x00b")

        with self.assertRaises(ValidationError):
            register_physical_adjustment(actor=self.admin, lot=lot, delta=True, reason="Bool")
        with self.assertRaises(ValidationError):
            register_physical_adjustment(actor=self.admin, lot=lot, delta=0, reason="Cero")
        with self.assertRaises(ValidationError):
            register_physical_adjustment(actor=self.admin, lot=lot, delta=1_000_000, reason="Max")
        with self.assertRaises(ValidationError):
            register_physical_adjustment(actor=self.admin, lot=lot, delta=-1_000_000, reason="Min")
        with self.assertRaises(ValidationError):
            register_physical_adjustment(actor=self.admin, lot=lot, delta=-21, reason="Supera stock")
        with self.assertRaises(ValidationError):
            register_physical_adjustment(actor=self.admin, lot=lot, delta=1, reason="a\x00b")
        with self.assertRaises(ValidationError):
            register_physical_adjustment(actor=self.admin, lot=lot, delta=1, reason="A" * 301)

        lot.refresh_from_db()
        self.assertEqual(lot.available_quantity, 20)
        self.assertFalse(StockWriteOff.objects.exists())
        self.assertFalse(PhysicalAdjustment.objects.exists())

    # ── HU-INV-02: Vencimiento en medianoche Lima, notas, correlativos y agotamiento ─

    def test_writeoff_expired_lot_lima_midnight_correlatives_and_depletion(self) -> None:
        exp_date = date(2026, 11, 12)
        before_mid = datetime(2026, 11, 12, 4, 59, 59, tzinfo=dt_timezone.utc)  # 2026-11-11 23:59:59 Lima
        at_mid = datetime(2026, 11, 12, 5, 0, 0, tzinfo=dt_timezone.utc)        # 2026-11-12 00:00:00 Lima

        with patch("django.utils.timezone.now", return_value=before_mid):
            prod, load = self._create_loaded_product(
                name="Yogurt Merma TZ",
                barcode="775080000104",
                lots=[LotInput("MERMA-TZ-1", 10, Decimal("2.5000"), exp_date)],
            )
            lot = load.lots.get()
            # 23:59:59 Lima -> aún vigente; se permite DAÑO con detalle obligatorio
            wo1 = write_off_stock(
                actor=self.wh1,
                lot=lot,
                quantity=2,
                reason=StockWriteOff.Reason.DAMAGE,
                notes="Envase abollado en exhibición.",
            )
            self.assertEqual(wo1.correlativo, "B-00000001")

        with patch("django.utils.timezone.now", return_value=at_mid):
            # 00:00:00 Lima del día de vencimiento -> ya vencido; bloquea DAÑO/ROBO
            for bad_reason in (StockWriteOff.Reason.DAMAGE, StockWriteOff.Reason.THEFT):
                with self.assertRaisesMessage(ValidationError, "El lote está vencido"):
                    write_off_stock(
                        actor=self.wh1, lot=lot, quantity=2, reason=bad_reason, notes="Motivo bloqueado"
                    )
            lot.refresh_from_db()
            self.assertEqual(lot.available_quantity, 8)

            # VENCIMIENTO sí procede y agota las 8 unidades restantes
            wo2 = write_off_stock(
                actor=self.admin, lot=lot, quantity=8, reason=StockWriteOff.Reason.EXPIRATION, notes=""
            )
            self.assertEqual(wo2.correlativo, "B-00000002")

        lot.refresh_from_db()
        self.assertEqual(lot.available_quantity, 0)
        # Al llegar a 0 unidades disponibles, el lote ya no aparece en el selector de bajas
        self.client.force_login(self.wh1)
        wo_list = self.client.get(reverse("stock-writeoff"))
        self.assertNotContains(wo_list, "MERMA-TZ-1")

        # Si existe una brecha en correlativos (ej. B-00000010), el siguiente continúa en B-00000011
        StockWriteOff.objects.filter(pk=wo2.pk).update(correlativo="B-00000010")
        prod2, load2 = self._create_loaded_product(
            name="Galleta Correlativo Gap",
            barcode="775080000105",
            lots=[LotInput("GAP-01", 5, Decimal("1.0000"), exp_date + timedelta(days=30))],
        )
        wo3 = write_off_stock(
            actor=self.wh2,
            lot=load2.lots.get(),
            quantity=1,
            reason=StockWriteOff.Reason.THEFT,
            notes="Faltante de mostrador",
        )
        self.assertEqual(wo3.correlativo, "B-00000011")

    # ── DEF08-05: Idempotencia, no consumo en fallo y rechazo por alteración ─

    def test_idempotency_replay_vs_tampered_payload_rejection(self) -> None:
        today = timezone.localdate()
        prod, load = self._create_loaded_product(
            name="Idem Producto 08",
            barcode="775080000106",
            lots=[LotInput("IDEM-01", 30, Decimal("2.0000"), today + timedelta(days=40))],
        )
        lot = load.lots.get()

        self.client.force_login(self.admin)
        idem_wo = str(uuid.uuid4())
        wo_url = f"{reverse('stock-writeoff')}?lote={lot.pk}"

        # Primer POST legítimo -> 302
        r1 = self.client.post(
            wo_url,
            {
                "lot_id": str(lot.pk),
                "quantity": "3",
                "reason": StockWriteOff.Reason.DAMAGE,
                "notes": "Rotura confirmada",
                "idempotency_key": idem_wo,
            },
        )
        self.assertRedirects(r1, reverse("stock-writeoff"))

        # Reenvío idéntico con misma clave -> 302 info sin duplicar
        r2 = self.client.post(
            wo_url,
            {
                "lot_id": str(lot.pk),
                "quantity": "3",
                "reason": StockWriteOff.Reason.DAMAGE,
                "notes": "Rotura confirmada",
                "idempotency_key": idem_wo,
            },
            follow=True,
        )
        self.assertContains(r2, "Esta baja ya fue registrada anteriormente.")

        # Reuso de misma clave con payload distinto -> 200 error, SIN redirigir ni mutar
        r3_tampered = self.client.post(
            wo_url,
            {
                "lot_id": str(lot.pk),
                "quantity": "9",
                "reason": StockWriteOff.Reason.THEFT,
                "notes": "Alterado",
                "idempotency_key": idem_wo,
            },
        )
        self.assertEqual(r3_tampered.status_code, 200)
        self.assertContains(r3_tampered, "La clave de operación ya fue utilizada para otra solicitud")

        lot.refresh_from_db()
        self.assertEqual(lot.available_quantity, 27)
        self.assertEqual(StockWriteOff.objects.filter(lot=lot).count(), 1)

        # Misma protección en ajustes físicos
        idem_adj = str(uuid.uuid4())
        adj_url = f"{reverse('physical-adjustment')}?lote={lot.pk}"
        ra1 = self.client.post(
            adj_url,
            {"lot_id": str(lot.pk), "delta": "+4", "reason": "Conteo A", "idempotency_key": idem_adj},
        )
        self.assertRedirects(ra1, reverse("physical-adjustment"))

        ra2_tampered = self.client.post(
            adj_url,
            {"lot_id": str(lot.pk), "delta": "-8", "reason": "Conteo B", "idempotency_key": idem_adj},
        )
        self.assertEqual(ra2_tampered.status_code, 200)
        self.assertContains(ra2_tampered, "La clave de operación ya fue utilizada para otra solicitud")

        lot.refresh_from_db()
        self.assertEqual(lot.available_quantity, 31)
        self.assertEqual(PhysicalAdjustment.objects.filter(lot=lot).count(), 1)

    # ── Impacto en stock, costo promedio (DOC-03AH-01) y ventas POS/FEFO ───────

    def test_stock_cost_doc03ah01_and_pos_sale_unit_cost_impact(self) -> None:
        today = timezone.localdate()
        prod, load = self._create_loaded_product(
            name="Aceite Impacto Costo 08",
            barcode="775080000107",
            lots=[
                LotInput("COST-A", 10, Decimal("2.0000"), today + timedelta(days=20)),
                LotInput("COST-B", 10, Decimal("4.0000"), today + timedelta(days=50)),
            ],
            sale_price=Decimal("9.00"),
            minimum_stock=4,
        )
        lot_a = load.lots.get(number_normalized="COST-A")
        lot_b = load.lots.get(number_normalized="COST-B")
        self.assertEqual(prod.average_cost, Decimal("3.0000"))

        # Venta previa antes de la merma conserva snapshot unit_cost = 3.0000
        d1 = add_product_to_draft(actor=self.seller, product_id=prod.pk, quantity=2)
        s1 = checkout_sale(
            actor=self.seller, draft_id=d1.pk, cash_received=Decimal("20.00"), idempotency_key=uuid.uuid4()
        )
        line1 = SaleLine.objects.get(sale=s1)
        self.assertEqual(line1.unit_cost, Decimal("3.0000"))
        lot_a.refresh_from_db()
        self.assertEqual(lot_a.available_quantity, 8)

        # Merma total de las 8u restantes de COST-A -> avg_cost pasa a 4.0000 (solo COST-B)
        write_off_stock(
            actor=self.wh1, lot=lot_a, quantity=8, reason=StockWriteOff.Reason.DAMAGE, notes="Cajas dañadas"
        )
        prod.refresh_from_db()
        self.assertEqual(prod.average_cost, Decimal("4.0000"))
        self.assertEqual(sellable_stock_for_product(prod), 10)

        # Ajuste positivo de +10u en COST-B -> initial_quantity sube de 10 a 20, available = 20, sellable = 20
        register_physical_adjustment(actor=self.admin, lot=lot_b, delta=10, reason="Cajas ubicadas en altillo")
        lot_b.refresh_from_db()
        self.assertEqual((lot_b.initial_quantity, lot_b.available_quantity), (20, 20))
        self.assertEqual(sellable_stock_for_product(prod), 20)

        # Venta posterior consume de COST-B y captura nuevo unit_cost = 4.0000 sin tocar line1
        d2 = add_product_to_draft(actor=self.seller, product_id=prod.pk, quantity=2)
        s2 = checkout_sale(
            actor=self.seller, draft_id=d2.pk, cash_received=Decimal("20.00"), idempotency_key=uuid.uuid4()
        )
        line1.refresh_from_db()
        line2 = SaleLine.objects.get(sale=s2)
        self.assertEqual(line1.unit_cost, Decimal("3.0000"))
        self.assertEqual(line2.unit_cost, Decimal("4.0000"))

        # DOC-03AH-01: ajuste negativo hasta 0 deja el average_cost previo sin modificar
        register_physical_adjustment(actor=self.admin, lot=lot_b, delta=-18, reason="Pérdida total en conteo")
        prod.refresh_from_db()
        self.assertEqual(prod.physical_stock, 0)
        self.assertEqual(prod.average_cost, Decimal("4.0000"))

        # Política actual: PhysicalAdjustment permite +delta sobre lote en 0 e incluso vencido
        Lot.objects.filter(pk=lot_b.pk).update(expiration_date=today - timedelta(days=1))
        register_physical_adjustment(actor=self.admin, lot=lot_b, delta=3, reason="Conteo sobre lote vencido")
        prod.refresh_from_db()
        self.assertEqual((prod.physical_stock, prod.sellable_stock), (3, 0))
        # Si solo queda stock en lote vencido, _recalculate_product_average_cost cae al fallback de lotes disponibles
        self.assertEqual(prod.average_cost, Decimal("4.0000"))

    # ── DEF08-06: Kardex cross-product barcode isolation y trazabilidad ───────

    def test_product_movements_isolates_reused_barcode_and_preserves_legacy_null_product_lines(self) -> None:
        today = timezone.localdate()
        prod_a, load_a = self._create_loaded_product(
            name="Producto A BarcodeViejo",
            barcode="775080999001",
            lots=[LotInput("LOTA-01", 10, Decimal("2.0000"), today + timedelta(days=60))],
            supplier=self.supplier1,
        )
        # Venta moderna de Producto A (SaleLine.product = prod_a)
        draft_a = add_product_to_draft(actor=self.seller, product_id=prod_a.pk, quantity=2)
        sale_a = checkout_sale(
            actor=self.seller, draft_id=draft_a.pk, cash_received=Decimal("20.00"), idempotency_key=uuid.uuid4()
        )
        # Venta heredada con product=None apuntando al código viejo de prod_a
        sale_legacy = Sale.objects.create(
            cash_shift=self.shift,
            seller=self.seller,
            total_amount=Decimal("8.00"),
            base_amount=Decimal("6.78"),
            igv_amount=Decimal("1.22"),
            cash_received=Decimal("10.00"),
            change_given=Decimal("2.00"),
            correlative="V-00088801",
            idempotency_key=uuid.uuid4(),
        )
        SaleLine.objects.create(
            sale=sale_legacy,
            product=None,
            product_snapshot_name=prod_a.name,
            product_snapshot_barcode="775080999001",
            quantity=1,
            unit_price=Decimal("8.00"),
            amount=Decimal("8.00"),
        )

        # Se cambia el código de barras de prod_a y se crea prod_b reutilizando el código viejo
        update_product(
            actor=self.admin,
            product=prod_a,
            name=prod_a.name,
            barcode="775080999002",
            sale_price=prod_a.sale_price,
            minimum_stock=prod_a.minimum_stock,
        )
        prod_b, load_b = self._create_loaded_product(
            name="Producto B CodigoReusado",
            barcode="775080999001",
            lots=[LotInput("lotb-min", 5, Decimal("3.0000"), today + timedelta(days=60))],
            supplier=self.supplier2,
        )

        self.client.force_login(self.wh1)
        mov_a = self.client.get(reverse("product-movements", args=(prod_a.pk,)))
        mov_b = self.client.get(reverse("product-movements", args=(prod_b.pk,)))

        self.assertContains(mov_a, sale_a.correlative)
        self.assertContains(mov_a, "V-00088801")
        self.assertNotContains(mov_b, sale_a.correlative)
        self.assertNotContains(mov_b, "V-00088801")
        self.assertContains(mov_b, "Carga inicial — Lote LOTB-MIN (Proveedor Dos 08)")

    def test_product_movements_traceability_trailing_period_and_bounded_queries(self) -> None:
        today = timezone.localdate()
        prod, load = self._create_loaded_product(
            name="Fideos Trazabilidad 08",
            barcode="775080000108",
            lots=[LotInput("TRAZ-01", 20, Decimal("2.0000"), today + timedelta(days=60))],
            supplier=self.supplier1,
        )
        lot = load.lots.get()
        register_stock_entry(
            actor=self.wh2,
            product=prod,
            supplier=self.supplier2,
            lots=[LotInput("TRAZ-02", 5, Decimal("2.2000"), today + timedelta(days=90))],
        )
        d = add_product_to_draft(actor=self.seller, product_id=prod.pk, quantity=3)
        sale = checkout_sale(
            actor=self.seller, draft_id=d.pk, cash_received=Decimal("30.00"), idempotency_key=uuid.uuid4()
        )
        wo = write_off_stock(
            actor=self.wh1,
            lot=lot,
            quantity=2,
            reason=StockWriteOff.Reason.DAMAGE,
            notes="Paquete roto en traslado.",
        )
        register_physical_adjustment(
            actor=self.admin,
            lot=lot,
            delta=-1,
            reason="Faltante de conteo.",
        )

        self.client.force_login(self.admin)
        with CaptureQueriesContext(connection) as q_ctx:
            resp = self.client.get(reverse("product-movements", args=(prod.pk,)))
        self.assertEqual(resp.status_code, 200)
        self.assertLessEqual(len(q_ctx), 15)

        html = resp.content.decode()
        self.assertIn("Carga inicial — Lote TRAZ-01 (Proveedor Uno 08)", html)
        self.assertIn("Entrada de mercadería — Lote TRAZ-02 (Proveedor Dos 08)", html)
        self.assertIn(f"Venta {sale.correlative}", html)
        self.assertIn(f"Merma (Daño o rotura) · {wo.correlativo} — Lote TRAZ-01. Paquete roto en traslado.", html)
        self.assertIn("Ajuste físico — Lote TRAZ-01. Faltante de conteo.", html)
        self.assertIn(self.wh1.display_name, html)
        self.assertIn(self.wh2.display_name, html)
        self.assertIn(self.seller.display_name, html)
        self.assertIn(self.admin.display_name, html)

    # ── Frontera explícita de historias/criterios incompletos en R1-PMV ─────

    def test_explicit_gaps_not_implemented_in_r1_remain_absent(self) -> None:
        self.client.force_login(self.admin)
        today = timezone.localdate()
        prod, load = self._create_loaded_product(
            name="Frontera Alcance 08",
            barcode="775080000109",
            lots=[LotInput("FRON-01", 10, Decimal("2.0000"), today + timedelta(days=30))],
        )
        wo = write_off_stock(
            actor=self.wh1, lot=load.lots.get(), quantity=1, reason=StockWriteOff.Reason.EXPIRATION
        )

        # HU-INV-02/CA-04: no existe ruta dedicada de constancia interna de merma
        self.assertEqual(self.client.get(f"/inventario/bajas/{wo.pk}/").status_code, 404)
        self.assertEqual(self.client.get("/inventario/bajas/constancia/").status_code, 404)

        # HU-INV-05 & HU-INV-06: no existen historiales globales ni rutas dedicadas
        self.assertEqual(self.client.get("/inventario/bajas/").status_code, 404)
        self.assertEqual(self.client.get("/inventario/bajas/historial/").status_code, 404)
        self.assertEqual(self.client.get("/inventario/ajustes/").status_code, 404)
        self.assertEqual(self.client.get("/inventario/ajustes/historial/").status_code, 404)

        # HU-INV-04/CA-01, CA-04: movimientos sin columna saldo ni filtros HTML
        mov = self.client.get(reverse("product-movements", args=(prod.pk,)))
        html = mov.content.decode().lower()
        self.assertNotIn("<th", html.split("responsable")[1].split("</tr>")[0])  # sin columna extra tras Responsable
        self.assertNotIn("<form", html)
