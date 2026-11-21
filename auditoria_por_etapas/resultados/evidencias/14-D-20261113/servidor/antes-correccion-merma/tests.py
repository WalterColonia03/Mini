from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Category, Product
from identity.models import Account, Role

from .models import InitialInventoryLoad, Lot
from .services import LotInput, confirm_initial_load


class InitialInventoryLoadTests(TestCase):
    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
        cls.admin = Account.objects.create_user(
            "admin@test.invalid", cls.password, display_name="Admin", role=admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "warehouse@test.invalid", cls.password, display_name="Almacén", role=warehouse_role
        )
        cls.seller = Account.objects.create_user(
            "seller@test.invalid", cls.password, display_name="Vendedor", role=seller_role
        )
        category = Category.objects.create(name="Productos enlatados")
        cls.product = Product.objects.create(
            category=category,
            name="Leche evaporada",
            barcode="775000000001",
            sale_price=Decimal("4.80"),
        )

    def payload(self, *, second_expiration=None):
        future_1 = timezone.localdate() + timedelta(days=30)
        future_2 = second_expiration or timezone.localdate() + timedelta(days=60)
        return {
            "product": str(self.product.pk),
            "lots-TOTAL_FORMS": "3",
            "lots-INITIAL_FORMS": "0",
            "lots-MIN_NUM_FORMS": "1",
            "lots-MAX_NUM_FORMS": "1000",
            "lots-0-number": " lote-a ",
            "lots-0-quantity": "2",
            "lots-0-unit_cost": "1.0000",
            "lots-0-expiration_date": future_1.isoformat(),
            "lots-1-number": "Lote-B",
            "lots-1-quantity": "3",
            "lots-1-unit_cost": "2.0000",
            "lots-1-expiration_date": future_2.isoformat(),
            "lots-2-number": "",
            "lots-2-quantity": "",
            "lots-2-unit_cost": "",
            "lots-2-expiration_date": "",
        }

    def test_multiple_lots_are_confirmed_atomically_with_weighted_cost(self) -> None:
        self.client.force_login(self.warehouse)

        response = self.client.post(reverse("inventory-load"), self.payload())

        load = InitialInventoryLoad.objects.get()
        self.assertRedirects(response, reverse("inventory-load-created", args=(load.pk,)))
        confirmation = self.client.get(reverse("inventory-load-created", args=(load.pk,)))
        self.assertEqual(load.responsible, self.warehouse)
        self.assertEqual(Lot.objects.count(), 2)
        self.assertEqual(
            list(Lot.objects.values_list("number_normalized", flat=True)),
            ["LOTE-A", "LOTE-B"],
        )
        for lot in Lot.objects.all():
            self.assertEqual(lot.available_quantity, lot.initial_quantity)
            self.assertTrue(timezone.is_aware(lot.received_at))
        self.product.refresh_from_db()
        self.assertEqual(self.product.physical_stock, 5)
        self.assertEqual(self.product.average_cost, Decimal("1.6000"))
        self.assertTrue(self.product.is_sellable)
        self.assertContains(confirmation, "S/ 1,60")
        self.assertNotContains(confirmation, "S/ 1,6000")

    def test_invalid_middle_lot_rolls_back_entire_load(self) -> None:
        self.client.force_login(self.warehouse)
        response = self.client.post(
            reverse("inventory-load"),
            self.payload(second_expiration=timezone.localdate()),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "posterior a hoy en Lima")
        self.assertEqual(InitialInventoryLoad.objects.count(), 0)
        self.assertEqual(Lot.objects.count(), 0)
        self.product.refresh_from_db()
        self.assertEqual(self.product.average_cost, Decimal("0.0000"))

    def test_second_initial_load_is_rejected(self) -> None:
        first = LotInput(
            number="A-1",
            quantity=1,
            unit_cost=Decimal("2.0000"),
            expiration_date=timezone.localdate() + timedelta(days=30),
        )
        confirm_initial_load(actor=self.warehouse, product=self.product, lots=[first])

        with self.assertRaisesMessage(ValidationError, "ya tiene una carga inicial"):
            confirm_initial_load(actor=self.warehouse, product=self.product, lots=[first])
        self.assertEqual(InitialInventoryLoad.objects.count(), 1)
        self.assertEqual(Lot.objects.count(), 1)

    def test_duplicate_numbers_in_same_request_leave_no_residue(self) -> None:
        inputs = [
            LotInput(" lote-1 ", 1, Decimal("1.0000"), timezone.localdate() + timedelta(days=10)),
            LotInput("LOTE-1", 2, Decimal("2.0000"), timezone.localdate() + timedelta(days=20)),
        ]

        with self.assertRaisesMessage(ValidationError, "está repetido"):
            confirm_initial_load(actor=self.warehouse, product=self.product, lots=inputs)
        self.assertFalse(InitialInventoryLoad.objects.exists())
        self.assertFalse(Lot.objects.exists())

    def test_non_warehouse_post_is_forbidden_without_mutation(self) -> None:
        for account in (self.admin, self.seller):
            with self.subTest(role=account.role.code):
                self.client.force_login(account)
                response = self.client.post(reverse("inventory-load"), self.payload())
                self.assertEqual(response.status_code, 403)
                self.assertFalse(InitialInventoryLoad.objects.exists())
                self.assertFalse(Lot.objects.exists())


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 3 — HU-PROV-01, HU-PROV-02, HU-PROV-04 · Proveedores
# ═══════════════════════════════════════════════════════════════════════════════

class SupplierTests(TestCase):
    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        from inventory.models import Supplier
        admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Admin Prov")
        wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="WH Prov")
        seller_role = Role.objects.create(code=Role.Code.SELLER, name="Seller Prov")
        cls.admin = Account.objects.create_user(
            "adminp@test.invalid", cls.password, display_name="Admin", role=admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "whp@test.invalid", cls.password, display_name="WH", role=wh_role
        )
        cls.seller = Account.objects.create_user(
            "sellerp@test.invalid", cls.password, display_name="Seller", role=seller_role
        )
        cls.supplier = Supplier.objects.create(name="Distribuidora ABC", ruc="20123456789")

    # ── HU-PROV-01 ──

    def test_admin_sees_supplier_list(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("supplier-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Distribuidora ABC")

    def test_warehouse_sees_supplier_list(self) -> None:
        self.client.force_login(self.warehouse)
        self.assertEqual(self.client.get(reverse("supplier-list")).status_code, 200)

    def test_seller_gets_403_on_supplier_list(self) -> None:
        self.client.force_login(self.seller)
        self.assertEqual(self.client.get(reverse("supplier-list")).status_code, 403)

    def test_search_filters_by_name(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("supplier-list"), {"q": "ABC"})
        self.assertContains(response, "Distribuidora ABC")
        response2 = self.client.get(reverse("supplier-list"), {"q": "xyzNoExiste"})
        self.assertNotContains(response2, "Distribuidora ABC")

    # ── HU-PROV-02 ──

    def test_admin_creates_supplier(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(reverse("supplier-create"), {
            "name": "Proveedor Nuevo", "ruc": "20999999991", "phone": "999-000"
        })
        self.assertRedirects(response, reverse("supplier-list"))
        from inventory.models import Supplier
        self.assertTrue(Supplier.objects.filter(ruc="20999999991").exists())

    def test_duplicate_ruc_is_rejected(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(reverse("supplier-create"), {
            "name": "Otro", "ruc": "20123456789", "phone": ""
        })
        self.assertEqual(response.status_code, 200)
        from inventory.models import Supplier
        self.assertEqual(Supplier.objects.filter(ruc="20123456789").count(), 1)

    def test_non_admin_cannot_create_supplier(self) -> None:
        self.client.force_login(self.warehouse)
        self.assertEqual(self.client.post(reverse("supplier-create"), {
            "name": "X", "ruc": "20111111111", "phone": ""
        }).status_code, 403)

    # ── HU-PROV-04 ──

    def test_admin_toggles_supplier_status(self) -> None:
        self.client.force_login(self.admin)
        was_active = self.supplier.is_active
        self.client.post(reverse("supplier-toggle", args=(self.supplier.pk,)))
        self.supplier.refresh_from_db()
        self.assertEqual(self.supplier.is_active, not was_active)

    def test_non_admin_gets_403_on_toggle(self) -> None:
        self.client.force_login(self.warehouse)
        self.assertEqual(
            self.client.post(reverse("supplier-toggle", args=(self.supplier.pk,))).status_code, 403
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 3 — HU-INV-02 · Baja de inventario por merma
# ═══════════════════════════════════════════════════════════════════════════════

class StockWriteOffTests(TestCase):
    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        from datetime import timedelta
        from decimal import Decimal
        from django.utils import timezone
        from inventory.models import InitialInventoryLoad, Lot
        from inventory.services import LotInput, confirm_initial_load

        admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Admin WO")
        wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="WH WO")
        seller_role = Role.objects.create(code=Role.Code.SELLER, name="Seller WO")
        cls.admin = Account.objects.create_user(
            "adminwo@test.invalid", cls.password, display_name="Admin WO", role=admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "whwo@test.invalid", cls.password, display_name="WH WO", role=wh_role
        )
        cls.seller = Account.objects.create_user(
            "sellerwo@test.invalid", cls.password, display_name="Seller WO", role=seller_role
        )
        cat = Category.objects.create(name="Productos enlatados")
        cls.product = Product.objects.create(
            category=cat, name="Producto WO", barcode="WO001", sale_price=Decimal("3.00")
        )
        future = timezone.localdate() + timedelta(days=60)
        confirm_initial_load(
            actor=cls.warehouse,
            product=cls.product,
            lots=[LotInput("LOT-WO-01", 20, Decimal("1.50"), future)],
        )
        cls.lot = Lot.objects.get(product=cls.product)

    def _writeoff_url(self):
        return f"{reverse('stock-writeoff')}?lote={self.lot.pk}"

    def test_warehouse_accesses_writeoff_page(self) -> None:
        self.client.force_login(self.warehouse)
        self.assertEqual(self.client.get(self._writeoff_url()).status_code, 200)

    def test_seller_gets_403(self) -> None:
        self.client.force_login(self.seller)
        self.assertEqual(self.client.get(reverse("stock-writeoff")).status_code, 403)

    def test_admin_registers_writeoff(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(
            self._writeoff_url(),
            {
                "lot_id": str(self.lot.pk),
                "quantity": "5",
                "reason": "VENCIMIENTO",
                "notes": "",
            },
        )
        self.assertRedirects(response, reverse("stock-writeoff"))
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.available_quantity, 15)

    def test_quantity_exceeding_stock_is_rejected(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(
            self._writeoff_url(),
            {
                "lot_id": str(self.lot.pk),
                "quantity": "9999",
                "reason": "VENCIMIENTO",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_writeoff_reason_is_rejected_by_service(self) -> None:
        from inventory.models import StockWriteOff
        from inventory.services import write_off_stock

        with self.assertRaises(ValidationError):
            write_off_stock(actor=self.admin, lot=self.lot, quantity=1, reason="INVALIDO")
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.available_quantity, 20)
        self.assertFalse(StockWriteOff.objects.exists())

    def test_damage_reason_requires_notes(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(
            self._writeoff_url(),
            {
                "lot_id": str(self.lot.pk),
                "quantity": "1",
                "reason": "DAÑO",
                "notes": "",
            },
        )
        self.assertEqual(response.status_code, 200)


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 3 — HU-INV-03 · Ajuste por conteo físico
# ═══════════════════════════════════════════════════════════════════════════════

class PhysicalAdjustmentTests(TestCase):
    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        from datetime import timedelta
        from decimal import Decimal
        from django.utils import timezone
        from inventory.models import Lot
        from inventory.services import LotInput, confirm_initial_load

        admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Admin Adj")
        wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="WH Adj")
        seller_role = Role.objects.create(code=Role.Code.SELLER, name="Seller Adj")
        cls.admin = Account.objects.create_user(
            "adminadj@test.invalid", cls.password, display_name="Admin Adj", role=admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "whadj@test.invalid", cls.password, display_name="WH Adj", role=wh_role
        )
        cls.seller = Account.objects.create_user(
            "selleradj@test.invalid", cls.password, display_name="Seller Adj", role=seller_role
        )
        cat = Category.objects.create(name="Productos enlatados")
        cls.product = Product.objects.create(
            category=cat, name="Producto Adj", barcode="ADJ001", sale_price=Decimal("2.50")
        )
        future = timezone.localdate() + timedelta(days=90)
        confirm_initial_load(
            actor=cls.warehouse,
            product=cls.product,
            lots=[LotInput("LOT-ADJ-01", 10, Decimal("1.00"), future)],
        )
        cls.lot = Lot.objects.get(product=cls.product)

    def _adj_url(self):
        return f"{reverse('physical-adjustment')}?lote={self.lot.pk}"

    def test_admin_registers_positive_adjustment(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(
            self._adj_url(),
            {
                "lot_id": str(self.lot.pk),
                "delta": "3",
                "reason": "Conteo físico detectó 3 unidades adicionales.",
            },
        )
        self.assertRedirects(response, reverse("physical-adjustment"))
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.available_quantity, 13)

    def test_negative_adjustment_exceeding_stock_is_rejected(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(
            self._adj_url(),
            {
                "lot_id": str(self.lot.pk),
                "delta": "-9999",
                "reason": "Test faltante extremo.",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_zero_delta_is_rejected_by_form(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(
            self._adj_url(),
            {
                "lot_id": str(self.lot.pk),
                "delta": "0",
                "reason": "Ninguno.",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_warehouse_gets_403(self) -> None:
        self.client.force_login(self.warehouse)
        self.assertEqual(self.client.get(reverse("physical-adjustment")).status_code, 403)

    def test_invalid_uuid_in_lote_param_returns_404(self) -> None:
        self.client.force_login(self.admin)
        resp_adj = self.client.get(reverse("physical-adjustment"), {"lote": "no-es-uuid"})
        self.assertEqual(resp_adj.status_code, 404)
        resp_wo = self.client.get(reverse("stock-writeoff"), {"lote": "no-es-uuid"})
        self.assertEqual(resp_wo.status_code, 404)

    def test_huge_delta_is_rejected_without_overflow(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(
            self._adj_url(),
            {
                "lot_id": str(self.lot.pk),
                "delta": "99999999999999999999",
                "reason": "Desbordamiento",
            },
        )
        self.assertEqual(response.status_code, 200)

    def test_duplicate_idempotency_key_is_ignored(self) -> None:
        import uuid
        self.client.force_login(self.admin)
        key = str(uuid.uuid4())
        before = self.lot.available_quantity
        self.client.post(
            self._adj_url(),
            {"lot_id": str(self.lot.pk), "delta": "2", "reason": "Conteo 1", "idempotency_key": key},
        )
        self.client.post(
            self._adj_url(),
            {"lot_id": str(self.lot.pk), "delta": "2", "reason": "Conteo 1", "idempotency_key": key},
        )
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.available_quantity, before + 2)

    def test_positive_adjustment_does_not_alter_initial_load_in_movements(self) -> None:
        self.client.force_login(self.admin)
        self.client.post(
            self._adj_url(),
            {"lot_id": str(self.lot.pk), "delta": "5", "reason": "Ajuste positivo"},
        )
        resp = self.client.get(reverse("product-movements", args=(self.product.pk,)))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "+10")
        self.assertContains(resp, "+5")

    def test_failed_validation_does_not_consume_idempotency_key_in_writeoff_or_adjustment(self) -> None:
        """BUG-003: Si falla la validación de negocio, la clave de idempotencia no se quema."""
        import uuid
        from .models import StockWriteOff

        self.client.force_login(self.admin)
        key = str(uuid.uuid4())
        wo_url = f"{reverse('stock-writeoff')}?lote={self.lot.pk}"
        # 1) Intento fallido (DAÑO sin notas)
        r1 = self.client.post(
            wo_url,
            {
                "lot_id": str(self.lot.pk),
                "quantity": "1",
                "reason": StockWriteOff.Reason.DAMAGE,
                "notes": "",
                "idempotency_key": key,
            },
        )
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(StockWriteOff.objects.filter(lot=self.lot).count(), 0)

        # 2) Corrección con la misma clave de idempotencia: debe registrarse
        r2 = self.client.post(
            wo_url,
            {
                "lot_id": str(self.lot.pk),
                "quantity": "1",
                "reason": StockWriteOff.Reason.DAMAGE,
                "notes": "Lata abollada en anaquel",
                "idempotency_key": key,
            },
        )
        self.assertRedirects(r2, reverse("stock-writeoff"))
        self.assertEqual(StockWriteOff.objects.filter(lot=self.lot).count(), 1)

    def test_missing_idempotency_key_still_prevents_rapid_duplicate_adjustment(self) -> None:
        """BUG-010: Dos POST idénticos consecutivos sin idempotency_key no duplican el ajuste."""
        self.client.force_login(self.admin)
        before = self.lot.available_quantity
        payload = {"lot_id": str(self.lot.pk), "delta": "3", "reason": "Doble clic sin clave"}
        self.client.post(self._adj_url(), payload)
        self.client.post(self._adj_url(), payload)
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.available_quantity, before + 3)

    def test_stock_entry_view_registers_subsequent_lots_and_links_supplier(self) -> None:
        """BUG-005 y BUG-011: La vista /inventario/entrada/ permite registrar lotes posteriores con proveedor."""
        from .models import Supplier

        supplier = Supplier.objects.create(name="Distribuidora Sur", ruc="20555666777")
        self.client.force_login(self.warehouse)
        future = (timezone.localdate() + timedelta(days=90)).isoformat()
        response = self.client.post(
            reverse("stock-entry"),
            {
                "product": str(self.product.pk),
                "supplier": str(supplier.pk),
                "lots-TOTAL_FORMS": "1",
                "lots-INITIAL_FORMS": "0",
                "lots-MIN_NUM_FORMS": "1",
                "lots-MAX_NUM_FORMS": "1000",
                "lots-0-number": "LOTE-REP-01",
                "lots-0-quantity": "10",
                "lots-0-unit_cost": "3.0000",
                "lots-0-expiration_date": future,
            },
        )
        load = InitialInventoryLoad.objects.get(product=self.product)
        self.assertRedirects(response, reverse("inventory-load-created", args=(load.pk,)))
        new_lot = Lot.objects.get(product=self.product, number_normalized="LOTE-REP-01")
        self.assertEqual(new_lot.supplier, supplier)
        self.product.refresh_from_db()
        self.assertEqual(self.product.average_cost, Decimal("2.0000"))

    def test_barcode_change_preserves_sales_in_product_movements_kardex(self) -> None:
        """BUG-004: Editar el código de barras de un producto no oculta sus ventas históricas en el Kardex."""
        import uuid
        from cash.models import CashRegister, CashShift
        from catalog.services import update_product
        from sales.models import Sale, SaleLine

        reg = CashRegister.objects.create(code="CAJA-KARDEX")
        shift = CashShift.objects.create(
            cash_register=reg, seller=self.seller, opening_amount=Decimal("20.00")
        )
        sale = Sale.objects.create(
            cash_shift=shift,
            seller=self.seller,
            total_amount=Decimal("7.00"),
            base_amount=Decimal("5.93"),
            igv_amount=Decimal("1.07"),
            cash_received=Decimal("10.00"),
            change_given=Decimal("3.00"),
            correlative="V-00099901",
            idempotency_key=uuid.uuid4(),
        )
        SaleLine.objects.create(
            sale=sale,
            product_snapshot_name=self.product.name,
            product_snapshot_barcode=self.product.barcode,
            quantity=2,
            unit_price=Decimal("3.50"),
            amount=Decimal("7.00"),
        )
        update_product(
            actor=self.admin,
            product=self.product,
            name=self.product.name,
            barcode="ADJ001-NUEVO",
            sale_price=self.product.sale_price,
            minimum_stock=self.product.minimum_stock,
        )
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("product-movements", args=(self.product.pk,)))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Venta V-00099901")

    def test_initial_load_created_preserves_original_quantity_and_alias_url(self) -> None:
        """BUG-012, BUG-022 y BUG-023: /inventario/carga-inicial/<id>/creada/ conserva cantidad inicial original."""
        from .services import register_physical_adjustment

        register_physical_adjustment(
            actor=self.admin, lot=self.lot, delta=5, reason="Ingreso por conteo"
        )
        load = InitialInventoryLoad.objects.get(product=self.product)
        self.client.force_login(self.warehouse)
        resp = self.client.get(reverse("inventory-load-created-alias", args=(load.pk,)))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "10 UND")
        self.assertContains(resp, "15 UND")
        self.assertContains(resp, "S/ 1,00")

    def test_absurd_future_expiration_year_9999_is_rejected(self) -> None:
        """BUG-014: El año 9999 en fecha de vencimiento es rechazado."""
        from datetime import date

        new_prod = Product.objects.create(
            category=self.product.category,
            name="Producto 9999",
            barcode="99990001",
            sale_price=Decimal("4.00"),
        )
        with self.assertRaisesMessage(ValidationError, "20 años en el futuro"):
            confirm_initial_load(
                actor=self.warehouse,
                product=new_prod,
                lots=[LotInput("L-9999", 5, Decimal("1.5000"), date(9999, 12, 31))],
            )

    def test_bug024_stock_entry_preserves_initial_load_lots_and_labels_subsequent_entries_in_kardex(self) -> None:
        """BUG-024: Las entradas posteriores no alteran los lotes de la carga inicial y el Kardex las distingue."""
        from inventory.services import create_supplier, register_stock_entry

        today = timezone.localdate()
        new_prod = Product.objects.create(
            category=self.product.category,
            name="Producto BUG 024",
            barcode="7750000000241",
            sale_price=Decimal("7.50"),
        )
        load = confirm_initial_load(
            actor=self.warehouse,
            product=new_prod,
            lots=[LotInput("L-INI-24", 10, Decimal("3.0000"), today + timedelta(days=90))],
        )
        sup = create_supplier(actor=self.admin, name="Distribuidora Sur", ruc="20999888777")
        register_stock_entry(
            actor=self.warehouse,
            product=new_prod,
            lots=[LotInput("L-POST-24", 20, Decimal("4.5000"), today + timedelta(days=180))],
            supplier=sup,
        )
        self.client.force_login(self.warehouse)
        cert_resp = self.client.get(reverse("inventory-load-created", args=(load.pk,)))
        self.assertEqual(cert_resp.status_code, 200)
        self.assertEqual([l.number_normalized for l in cert_resp.context["lots"]], ["L-INI-24"])
        self.assertEqual([l.number_normalized for l in cert_resp.context["subsequent_lots"]], ["L-POST-24"])
        self.assertContains(cert_resp, "Entradas posteriores de mercadería")

        kardex_resp = self.client.get(reverse("product-movements", args=(new_prod.pk,)))
        self.assertEqual(kardex_resp.status_code, 200)
        self.assertContains(kardex_resp, "Carga inicial — Lote L-INI-24")
        self.assertContains(kardex_resp, "Entrada de mercadería — Lote L-POST-24 (Distribuidora Sur)")

    def test_bug005_register_stock_entry_excludes_expired_lots_from_average_cost(self) -> None:
        """BUG-005: El recálculo de costo promedio excluye lotes ya vencidos."""
        from inventory.services import register_stock_entry

        today = timezone.localdate()
        new_prod = Product.objects.create(
            category=self.product.category,
            name="Producto BUG 005",
            barcode="7750000000050",
            sale_price=Decimal("8.50"),
        )
        load = confirm_initial_load(
            actor=self.warehouse,
            product=new_prod,
            lots=[LotInput("L-EXP-05", 10, Decimal("2.0000"), today + timedelta(days=10))],
        )
        lot_old = load.lots.first()
        Lot.objects.filter(pk=lot_old.pk).update(expiration_date=today - timedelta(days=2))
        register_stock_entry(
            actor=self.warehouse,
            product=new_prod,
            lots=[LotInput("L-VIG-05", 10, Decimal("6.0000"), today + timedelta(days=120))],
        )
        new_prod.refresh_from_db()
        self.assertEqual(new_prod.average_cost, Decimal("6.0000"))

    def test_bug027_lot_unit_cost_rejects_scientific_notation_and_excessive_values(self) -> None:
        """BUG-027: LotInputForm y _validate_lots rechazan notación científica y costos desmesurados."""
        today = timezone.localdate()
        new_prod = Product.objects.create(
            category=self.product.category,
            name="Producto BUG 027",
            barcode="7750000000272",
            sale_price=Decimal("5.50"),
        )
        self.client.force_login(self.warehouse)
        response = self.client.post(
            reverse("inventory-load"),
            {
                "product": str(new_prod.pk),
                "lots-TOTAL_FORMS": "1",
                "lots-INITIAL_FORMS": "0",
                "lots-MIN_NUM_FORMS": "1",
                "lots-MAX_NUM_FORMS": "1000",
                "lots-0-number": "L-SCI",
                "lots-0-quantity": "10",
                "lots-0-unit_cost": "1e2",
                "lots-0-expiration_date": (today + timedelta(days=60)).isoformat(),
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "notación científica")

        with self.assertRaises(ValidationError):
            confirm_initial_load(
                actor=self.warehouse,
                product=new_prod,
                lots=[LotInput("L-MAX", 5, Decimal("10000000.0000"), today + timedelta(days=60))],
            )

    def test_bug032_subsequent_stock_entry_records_second_warehouse_worker_and_admin_can_view_load(self) -> None:
        """BUG-032: Entradas posteriores registran al almacenero real por lote, incluyen proveedor en carga inicial y permiten vista a Admin."""
        from inventory.models import Supplier
        from inventory.services import register_stock_entry

        today = timezone.localdate()
        wh_pedro = Account.objects.create_user(
            "pedro.wh@test.invalid",
            self.password,
            display_name="Pedro Almacén",
            role=self.warehouse.role,
        )
        sup_init = Supplier.objects.create(name="Distribuidora Inicial SAC", ruc="20555111221")
        sup_sub = Supplier.objects.create(name="Importadora Posterior SRL", ruc="20555111222")
        prod = Product.objects.create(
            category=self.product.category,
            name="Conserva Multi Almacenero",
            barcode="775000320001",
            sale_price=Decimal("7.00"),
        )
        load = confirm_initial_load(
            actor=self.warehouse,
            product=prod,
            supplier=sup_init,
            lots=[LotInput("L-KEVIN-1", 10, Decimal("4.0000"), today + timedelta(days=90))],
        )
        register_stock_entry(
            actor=wh_pedro,
            product=prod,
            supplier=sup_sub,
            lots=[LotInput("L-PEDRO-2", 5, Decimal("5.0000"), today + timedelta(days=120))],
        )

        self.client.force_login(self.admin)
        mov_resp = self.client.get(reverse("product-movements", args=(prod.pk,)))
        self.assertEqual(mov_resp.status_code, 200)
        self.assertContains(mov_resp, "Carga inicial — Lote L-KEVIN-1 (Distribuidora Inicial SAC)")
        self.assertContains(mov_resp, "Entrada de mercadería — Lote L-PEDRO-2 (Importadora Posterior SRL)")
        self.assertContains(mov_resp, self.warehouse.display_name)
        self.assertContains(mov_resp, "Pedro Almacén")

        load_resp = self.client.get(reverse("inventory-load-created", args=(load.pk,)))
        self.assertEqual(load_resp.status_code, 200)
        self.assertContains(load_resp, "Pedro Almacén")
        self.assertNotContains(load_resp, "Cargar otro producto")

        stock_resp = self.client.get(reverse("stock-overview"))
        self.assertContains(stock_resp, reverse("inventory-load-created", args=(load.pk,)))

    def test_bug033_inactive_category_excludes_products_from_initial_load_and_stock_entry_forms(self) -> None:
        """BUG-033: InitialLoadProductForm y StockEntryProductForm excluyen productos cuya categoría fue desactivada."""
        from inventory.forms import InitialLoadProductForm, StockEntryProductForm

        today = timezone.localdate()
        cat_inact = Category.objects.create(name="Cat Inactiva Inv", is_active=True)
        prod_no_load = Product.objects.create(
            category=cat_inact, name="Prod Sin Carga Cat Inact", barcode="775000331001", sale_price=Decimal("5.00")
        )
        prod_with_load = Product.objects.create(
            category=cat_inact, name="Prod Con Carga Cat Inact", barcode="775000331002", sale_price=Decimal("6.00")
        )
        confirm_initial_load(
            actor=self.warehouse,
            product=prod_with_load,
            lots=[LotInput("L-CAT-1", 5, Decimal("3.0000"), today + timedelta(days=60))],
        )
        cat_inact.is_active = False
        cat_inact.save(update_fields=["is_active"])

        self.assertNotIn(prod_no_load, InitialLoadProductForm().fields["product"].queryset)
        self.assertNotIn(prod_with_load, StockEntryProductForm().fields["product"].queryset)

    def test_bug036_writeoff_and_adjustment_prioritize_posted_lot_id_and_render_hidden_field_errors(self) -> None:
        """BUG-036: Baja y ajuste priorizan request.POST['lot_id'] sobre ?lote= y muestran errores de campos ocultos."""
        today = timezone.localdate()
        prod = Product.objects.create(
            category=self.product.category,
            name="Prod BUG 036",
            barcode="775000360001",
            sale_price=Decimal("8.00"),
        )
        load = confirm_initial_load(
            actor=self.warehouse,
            product=prod,
            lots=[
                LotInput("L-36-A", 10, Decimal("4.0000"), today + timedelta(days=60)),
                LotInput("L-36-B", 10, Decimal("6.0000"), today + timedelta(days=90)),
            ],
        )
        lot_a, lot_b = list(load.lots.order_by("number_normalized"))

        self.client.force_login(self.admin)
        # ?lote= apunta a lot_a pero el formulario envía lot_b en POST
        resp = self.client.post(
            f"{reverse('stock-writeoff')}?lote={lot_a.pk}",
            {
                "lot_id": str(lot_b.pk),
                "quantity": "3",
                "reason": "DAÑO",
                "notes": "Lata abollada en lote B",
            },
        )
        self.assertRedirects(resp, reverse("stock-writeoff"))
        lot_a.refresh_from_db()
        lot_b.refresh_from_db()
        self.assertEqual(lot_a.available_quantity, 10)
        self.assertEqual(lot_b.available_quantity, 7)

        # Enviar idempotency_key corrupto renderiza alerta de error visible
        bad_resp = self.client.post(
            f"{reverse('physical-adjustment')}?lote={lot_a.pk}",
            {
                "lot_id": str(lot_a.pk),
                "idempotency_key": "no-es-un-uuid",
                "delta": "2",
                "reason": "Conteo",
            },
        )
        self.assertEqual(bad_resp.status_code, 200)
        self.assertContains(bad_resp, "alert-danger")

    def test_bug005_writeoff_and_physical_adjustment_recalculate_average_cost(self) -> None:
        """BUG-005 residual: Dar de baja o ajustar físicamente un lote recalcula el costo promedio ponderado del producto."""
        from inventory.services import register_physical_adjustment, write_off_stock
        from inventory.models import StockWriteOff

        today = timezone.localdate()
        prod = Product.objects.create(
            category=self.product.category,
            name="Prod Costo Dinamico",
            barcode="775000059999",
            sale_price=Decimal("10.00"),
        )
        load = confirm_initial_load(
            actor=self.warehouse,
            product=prod,
            lots=[
                LotInput("L-C1", 10, Decimal("2.0000"), today + timedelta(days=60)),
                LotInput("L-C2", 10, Decimal("4.0000"), today + timedelta(days=90)),
            ],
        )
        prod.refresh_from_db()
        self.assertEqual(prod.average_cost, Decimal("3.0000"))

        lot_c1 = load.lots.get(number_normalized="L-C1")
        write_off_stock(
            actor=self.warehouse,
            lot=lot_c1,
            quantity=10,
            reason=StockWriteOff.Reason.DAMAGE,
            notes="Pérdida total lote C1",
        )
        prod.refresh_from_db()
        self.assertEqual(prod.average_cost, Decimal("4.0000"))

        register_physical_adjustment(
            actor=self.admin,
            lot=lot_c1,
            delta=10,
            reason="Hallazgo en almacén",
        )
        prod.refresh_from_db()
        self.assertEqual(prod.average_cost, Decimal("3.0000"))
