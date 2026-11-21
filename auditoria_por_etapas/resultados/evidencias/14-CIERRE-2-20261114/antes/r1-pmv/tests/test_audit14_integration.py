"""
ETAPA 14 — Pruebas de integración entre roles
===============================================
Recorrido completo ADMIN → ALMACENERO → VENDEDOR → ALM/ADMIN → VENDEDOR
con datos ficticios, base aislada, efectos cruzados y permisos denegados.

Fecha: 13/11/2026  |  Base: SQLite aislada (TestCase)
Roles ficticios: admin@pruebas.invalid, almacen@pruebas.invalid,
                 vendedor.a@pruebas.invalid
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.sessions.backends.db import SessionStore
from django.test import TestCase, Client, override_settings
from django.utils import timezone

from identity.models import Account, Role
from catalog.models import Category, Product
from inventory.models import (
    InitialInventoryLoad, Lot, Supplier, StockWriteOff, PhysicalAdjustment,
)
from cash.models import CashRegister, CashShift, CashShiftClose
from sales.models import Sale, SaleDraft, SaleDraftLine, SaleLine, SaleCounter


PASSWORD = "PruebaSegura9!"


def _setup_roles():
    Role.objects.get_or_create(code="ADMIN", defaults={"name": "Administrador"})
    Role.objects.get_or_create(code="ALMACENERO", defaults={"name": "Almacenero"})
    Role.objects.get_or_create(code="VENDEDOR", defaults={"name": "Vendedor"})


def _make_account(email, role_code):
    role = Role.objects.get(code=role_code)
    return Account.objects.create_user(
        email=email, password=PASSWORD, display_name=email.split("@")[0], role=role,
    )


def _login(client, email):
    ok = client.login(email=email, password=PASSWORD)
    assert ok, f"Login failed for {email}"


@override_settings(TIME_ZONE="America/Lima")
class IntegrationE2ETest(TestCase):
    """Flujo completo E2E entre los tres roles — primera pasada etapa 14."""

    @classmethod
    def setUpTestData(cls):
        _setup_roles()
        cls.admin = _make_account("admin@pruebas.invalid", "ADMIN")
        cls.warehouse = _make_account("almacen@pruebas.invalid", "ALMACENERO")
        cls.seller = _make_account("vendedor.a@pruebas.invalid", "VENDEDOR")
        cls.inactive = _make_account("inactivo@pruebas.invalid", "VENDEDOR")
        cls.inactive.is_active = False
        cls.inactive.save(update_fields=["is_active"])
        CashRegister.objects.get_or_create(code="CAJA-01", defaults={"is_active": True})

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _client_as(self, email):
        c = Client()
        _login(c, email)
        return c

    def _post(self, client, url, data=None, **kw):
        return client.post(url, data=data or {}, **kw)

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 1 — ADMIN crea categoría, producto y proveedor
    # ══════════════════════════════════════════════════════════════════════════

    def test_01_admin_creates_category(self):
        c = self._client_as("admin@pruebas.invalid")
        r = c.post("/productos/categorias/nueva/", {"name": "Lácteos Prueba E14"})
        self.assertEqual(r.status_code, 302, "Admin: crear categoría debe redirigir")
        self.assertTrue(Category.objects.filter(name="Lácteos Prueba E14").exists())

    def test_02_admin_creates_product(self):
        c = self._client_as("admin@pruebas.invalid")
        cat = Category.objects.create(name="Cat E14", is_active=True)
        r = c.post("/productos/nuevo/", {
            "name": "Leche E14",
            "barcode": "INT-E14-LECHE",
            "barcode_type": "INTERNAL",
            "category": str(cat.pk),
            "unit": "UND",
            "sale_price": "10.00",
            "minimum_stock": "5",
            "controls_expiration": "on",
        })
        self.assertIn(r.status_code, (301, 302), "Admin: crear producto debe redirigir")
        self.assertTrue(Product.objects.filter(name="Leche E14").exists())

    def test_03_admin_creates_supplier(self):
        c = self._client_as("admin@pruebas.invalid")
        r = c.post("/inventario/proveedores/nuevo/", {
            "name": "Proveedor E14",
            "ruc": "20123456789",
            "phone": "999888777",
        })
        self.assertEqual(r.status_code, 302, "Admin: crear proveedor debe redirigir")
        self.assertTrue(Supplier.objects.filter(ruc="20123456789").exists())

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 2 — ALMACENERO registra existencias (carga inicial)
    # ══════════════════════════════════════════════════════════════════════════

    def test_04_warehouse_loads_stock(self):
        c = self._client_as("almacen@pruebas.invalid")
        cat = Category.objects.create(name="Cat Load E14", is_active=True)
        prod = Product.objects.create(
            name="Arroz E14", barcode="INT-E14-ARROZ", barcode_type="INTERNAL",
            barcode_normalized="INT-E14-ARROZ", search_name="arroz e14",
            category=cat, unit="UND", sale_price=Decimal("5.00"),
            minimum_stock=3, controls_expiration=True,
        )
        tomorrow = date.today() + timedelta(days=60)
        r = c.post("/inventario/carga-inicial/", {
            "product": str(prod.pk),
            "lots-TOTAL_FORMS": "1",
            "lots-INITIAL_FORMS": "0",
            "lots-MIN_NUM_FORMS": "1",
            "lots-MAX_NUM_FORMS": "10",
            "lots-0-number": "LOTE-E14-A",
            "lots-0-quantity": "20",
            "lots-0-unit_cost": "2.5000",
            "lots-0-expiration_date": str(tomorrow),
        })
        self.assertIn(r.status_code, (301, 302), "Almacenero: carga inicial debe redirigir")
        self.assertTrue(Lot.objects.filter(product=prod, number_normalized="LOTE-E14-A").exists())
        prod.refresh_from_db()
        self.assertEqual(prod.average_cost, Decimal("2.5000"))

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 3 — VENDEDOR abre caja y cobra
    # ══════════════════════════════════════════════════════════════════════════

    def test_05_seller_opens_shift_and_sells(self):
        # Setup
        c = self._client_as("vendedor.a@pruebas.invalid")
        cat = Category.objects.create(name="Cat Sell E14", is_active=True)
        prod = Product.objects.create(
            name="Yogurt E14", barcode="INT-E14-YOG", barcode_type="INTERNAL",
            barcode_normalized="INT-E14-YOG", search_name="yogurt e14",
            category=cat, unit="UND", sale_price=Decimal("7.10"),
            minimum_stock=2, controls_expiration=True,
            average_cost=Decimal("3.0000"),
        )
        tomorrow = date.today() + timedelta(days=30)
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.warehouse)
        Lot.objects.create(
            product=prod, initial_load=load, number="LOTE-SELL-A",
            number_normalized="LOTE-SELL-A", initial_quantity=10,
            available_quantity=10, unit_cost=Decimal("3.0000"),
            expiration_date=tomorrow,
        )
        # Open shift
        r = c.post("/caja/abrir/", {"opening_amount": "100.00"})
        self.assertIn(r.status_code, (301, 302), "Vendedor: abrir caja debe redirigir")
        shift = CashShift.objects.filter(seller=self.seller, status="OPEN").first()
        self.assertIsNotNone(shift, "Debe existir un turno abierto")

        # Add product to draft
        r = c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "2"})
        self.assertIn(r.status_code, (301, 302), "Vendedor: agregar producto a borrador")
        draft = SaleDraft.objects.filter(seller=self.seller, status="ACTIVE").first()
        self.assertIsNotNone(draft)
        self.assertEqual(draft.lines.count(), 1)

        # Checkout
        from sales.services import draft_totals, draft_signature
        totals = draft_totals(draft)
        sig = draft_signature(draft.pk, draft.lines.all())
        idem_key = str(uuid.uuid4())
        r = c.post("/ventas/cobrar/", {
            "cash_received": "20.00",
            "idempotency_key": idem_key,
            "expected_subtotal": str(totals.total),
            "draft_signature": sig,
        })
        self.assertIn(r.status_code, (301, 302), "Vendedor: cobrar debe redirigir a constancia")
        sale = Sale.objects.filter(seller=self.seller).first()
        self.assertIsNotNone(sale, "Debe existir la venta confirmada")
        self.assertEqual(sale.total_amount, Decimal("14.20"))
        self.assertEqual(sale.cash_received, Decimal("20.00"))
        self.assertEqual(sale.change_given, Decimal("5.80"))
        # Stock decremented
        lot = Lot.objects.get(number_normalized="LOTE-SELL-A")
        self.assertEqual(lot.available_quantity, 8, "Stock debe reducirse de 10 a 8")

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 4 — ALMACENERO contrasta stock y merma
    # ══════════════════════════════════════════════════════════════════════════

    def test_06_warehouse_writeoff(self):
        c = self._client_as("almacen@pruebas.invalid")
        cat = Category.objects.create(name="Cat WO E14", is_active=True)
        prod = Product.objects.create(
            name="Queso E14", barcode="INT-E14-QUESO", barcode_type="INTERNAL",
            barcode_normalized="INT-E14-QUESO", search_name="queso e14",
            category=cat, unit="UND", sale_price=Decimal("12.00"),
            minimum_stock=2, controls_expiration=True,
            average_cost=Decimal("6.0000"),
        )
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.warehouse)
        lot = Lot.objects.create(
            product=prod, initial_load=load, number="LOTE-WO-A",
            number_normalized="LOTE-WO-A", initial_quantity=15,
            available_quantity=15, unit_cost=Decimal("6.0000"),
            expiration_date=date.today() + timedelta(days=5),
        )
        r = c.post("/inventario/bajas/nueva/", {
            "lot_id": str(lot.pk),
            "quantity": "3",
            "reason": "DAÑO",
            "notes": "Rotura durante transporte E14",
            "idempotency_key": str(uuid.uuid4()),
        })
        self.assertIn(r.status_code, (301, 302), "Almacenero: baja debe redirigir")
        lot.refresh_from_db()
        self.assertEqual(lot.available_quantity, 12, "Stock debe reducirse de 15 a 12")
        self.assertTrue(StockWriteOff.objects.filter(lot=lot, quantity=3).exists())

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 5 — ADMIN revisa movimientos y ventas
    # ══════════════════════════════════════════════════════════════════════════

    def test_07_admin_views_sales_history(self):
        c = self._client_as("admin@pruebas.invalid")
        r = c.get("/ventas/historial/")
        self.assertEqual(r.status_code, 200, "Admin: historial de ventas debe ser 200")

    def test_08_admin_views_shift_history(self):
        c = self._client_as("admin@pruebas.invalid")
        r = c.get("/caja/turnos/")
        self.assertEqual(r.status_code, 200, "Admin: historial de turnos debe ser 200")

    def test_09_admin_views_stock_overview(self):
        c = self._client_as("admin@pruebas.invalid")
        r = c.get("/inventario/stock/")
        self.assertEqual(r.status_code, 200, "Admin: vista stock debe ser 200")

    def test_10_admin_views_product_movements(self):
        c = self._client_as("admin@pruebas.invalid")
        cat = Category.objects.create(name="Cat Mov E14", is_active=True)
        prod = Product.objects.create(
            name="Mantequilla E14", barcode="INT-E14-MANTQ", barcode_type="INTERNAL",
            barcode_normalized="INT-E14-MANTQ", search_name="mantequilla e14",
            category=cat, unit="UND", sale_price=Decimal("8.00"),
            minimum_stock=1, controls_expiration=True,
        )
        r = c.get(f"/inventario/productos/{prod.pk}/movimientos/")
        self.assertEqual(r.status_code, 200, "Admin: movimientos de producto debe ser 200")

    # ══════════════════════════════════════════════════════════════════════════
    # PASO 6 — VENDEDOR cierra caja
    # ══════════════════════════════════════════════════════════════════════════

    def test_11_seller_closes_shift(self):
        c = self._client_as("vendedor.a@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        shift = CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("100.00"), status="OPEN",
        )
        r = c.post("/caja/cerrar/", {"counted_amount": "100.00"})
        self.assertIn(r.status_code, (301, 302), "Vendedor: cerrar caja debe redirigir")
        shift.refresh_from_db()
        self.assertEqual(shift.status, "CLOSED")
        close = CashShiftClose.objects.filter(cash_shift=shift).first()
        self.assertIsNotNone(close, "Debe existir registro de cierre")

    # ══════════════════════════════════════════════════════════════════════════
    # PERMISOS DENEGADOS — Acciones cruzadas entre roles
    # ══════════════════════════════════════════════════════════════════════════

    def test_20_seller_cannot_create_category(self):
        c = self._client_as("vendedor.a@pruebas.invalid")
        count_before = Category.objects.count()
        r = c.post("/productos/categorias/nueva/", {"name": "Hack E14"})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Category.objects.count(), count_before, "Sin mutación")

    def test_21_seller_cannot_create_product(self):
        c = self._client_as("vendedor.a@pruebas.invalid")
        cat = Category.objects.create(name="Cat Deny E14")
        count_before = Product.objects.count()
        r = c.post("/productos/nuevo/", {
            "name": "Hack", "barcode": "HACK-E14", "barcode_type": "INTERNAL",
            "category": str(cat.pk), "unit": "UND", "sale_price": "1.00",
            "minimum_stock": "1", "controls_expiration": "on",
        })
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Product.objects.count(), count_before)

    def test_22_seller_cannot_create_supplier(self):
        c = self._client_as("vendedor.a@pruebas.invalid")
        count_before = Supplier.objects.count()
        r = c.post("/inventario/proveedores/nuevo/", {
            "name": "HackProv", "ruc": "20999999999",
        })
        self.assertEqual(r.status_code, 403)
        self.assertEqual(Supplier.objects.count(), count_before)

    def test_23_warehouse_cannot_open_cash(self):
        c = self._client_as("almacen@pruebas.invalid")
        count_before = CashShift.objects.count()
        r = c.post("/caja/abrir/", {"opening_amount": "50.00"})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(CashShift.objects.count(), count_before)

    def test_24_warehouse_cannot_sell(self):
        c = self._client_as("almacen@pruebas.invalid")
        cat = Category.objects.create(name="Cat NV E14")
        prod = Product.objects.create(
            name="ProdNoVenta", barcode="INT-NV-E14", barcode_type="INTERNAL",
            barcode_normalized="INT-NV-E14", search_name="prodnoventa",
            category=cat, unit="UND", sale_price=Decimal("5.00"),
            minimum_stock=1, controls_expiration=True,
        )
        count_before = SaleDraft.objects.count()
        r = c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "1"})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(SaleDraft.objects.count(), count_before)

    def test_25_admin_cannot_open_cash(self):
        c = self._client_as("admin@pruebas.invalid")
        count_before = CashShift.objects.count()
        r = c.post("/caja/abrir/", {"opening_amount": "50.00"})
        self.assertEqual(r.status_code, 403)
        self.assertEqual(CashShift.objects.count(), count_before)

    def test_26_admin_cannot_load_stock(self):
        c = self._client_as("admin@pruebas.invalid")
        cat = Category.objects.create(name="Cat AdminLoad E14")
        prod = Product.objects.create(
            name="ProdAdminLoad", barcode="INT-AL-E14", barcode_type="INTERNAL",
            barcode_normalized="INT-AL-E14", search_name="prodadminload",
            category=cat, unit="UND", sale_price=Decimal("5.00"),
            minimum_stock=1, controls_expiration=True,
        )
        count_before = InitialInventoryLoad.objects.count()
        tomorrow = date.today() + timedelta(days=30)
        r = c.post("/inventario/carga-inicial/", {
            "product": str(prod.pk),
            "lots-TOTAL_FORMS": "1", "lots-INITIAL_FORMS": "0",
            "lots-MIN_NUM_FORMS": "1", "lots-MAX_NUM_FORMS": "10",
            "lots-0-number": "LOTE-ADM", "lots-0-quantity": "5",
            "lots-0-unit_cost": "1.0000", "lots-0-expiration_date": str(tomorrow),
        })
        self.assertEqual(r.status_code, 403)
        self.assertEqual(InitialInventoryLoad.objects.count(), count_before)

    def test_27_seller_cannot_writeoff(self):
        c = self._client_as("vendedor.a@pruebas.invalid")
        count_before = StockWriteOff.objects.count()
        r = c.post("/inventario/bajas/nueva/", {
            "lot_id": str(uuid.uuid4()), "quantity": "1", "reason": "DAÑO",
            "notes": "hack",
        })
        self.assertEqual(r.status_code, 403)
        self.assertEqual(StockWriteOff.objects.count(), count_before)

    def test_28_warehouse_cannot_adjust_physical(self):
        c = self._client_as("almacen@pruebas.invalid")
        count_before = PhysicalAdjustment.objects.count()
        r = c.post("/inventario/ajustes/nuevo/", {
            "lot_id": str(uuid.uuid4()), "delta": "5", "reason": "ajuste prueba",
        })
        self.assertEqual(r.status_code, 403)
        self.assertEqual(PhysicalAdjustment.objects.count(), count_before)

    def test_29_seller_cannot_view_employees(self):
        c = self._client_as("vendedor.a@pruebas.invalid")
        r = c.get("/empleados/")
        self.assertEqual(r.status_code, 403)

    def test_30_warehouse_cannot_view_employees(self):
        c = self._client_as("almacen@pruebas.invalid")
        r = c.get("/empleados/")
        self.assertEqual(r.status_code, 403)

    def test_31_seller_cannot_view_categories(self):
        c = self._client_as("vendedor.a@pruebas.invalid")
        r = c.get("/productos/categorias/")
        self.assertEqual(r.status_code, 403)

    def test_32_inactive_account_denied(self):
        c = Client()
        r = c.post("/", {"email": "inactivo@pruebas.invalid", "password": PASSWORD})
        self.assertEqual(r.status_code, 200, "Login page re-displayed")
        self.assertContains(r, "Correo o contraseña incorrectos")

    def test_33_anonymous_redirected(self):
        c = Client()
        for url in ["/inicio/", "/productos/", "/inventario/stock/",
                     "/caja/abrir/", "/ventas/", "/ventas/historial/"]:
            r = c.get(url)
            self.assertIn(r.status_code, (301, 302), f"Anonymous → {url} redirect")

    # ══════════════════════════════════════════════════════════════════════════
    # CAMBIOS DE ESTADO — producto/categoría desactivados impiden venta
    # ══════════════════════════════════════════════════════════════════════════

    def test_40_inactive_product_not_sellable(self):
        """Un producto desactivado por admin no debe poder agregarse al borrador."""
        cat = Category.objects.create(name="Cat IS E14", is_active=True)
        prod = Product.objects.create(
            name="Inactivo E14", barcode="INT-IS-E14", barcode_type="INTERNAL",
            barcode_normalized="INT-IS-E14", search_name="inactivo e14",
            category=cat, unit="UND", sale_price=Decimal("5.00"),
            minimum_stock=1, controls_expiration=True, is_active=False,
            average_cost=Decimal("2.0000"),
        )
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.warehouse)
        Lot.objects.create(
            product=prod, initial_load=load, number="LOTE-IS",
            number_normalized="LOTE-IS", initial_quantity=10,
            available_quantity=10, unit_cost=Decimal("2.0000"),
            expiration_date=date.today() + timedelta(days=30),
        )
        c = self._client_as("vendedor.a@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("50.00"), status="OPEN",
        )
        count_before = SaleDraftLine.objects.count()
        r = c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "1"})
        self.assertEqual(SaleDraftLine.objects.count(), count_before,
                         "Producto inactivo: sin línea de borrador")

    def test_41_inactive_category_not_sellable(self):
        """Un producto con categoría inactiva no debe poder venderse."""
        cat = Category.objects.create(name="Cat InactCat E14", is_active=False)
        prod = Product.objects.create(
            name="ProdCatOff E14", barcode="INT-CO-E14", barcode_type="INTERNAL",
            barcode_normalized="INT-CO-E14", search_name="prodcatoff e14",
            category=cat, unit="UND", sale_price=Decimal("5.00"),
            minimum_stock=1, controls_expiration=True, is_active=True,
            average_cost=Decimal("2.0000"),
        )
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.warehouse)
        Lot.objects.create(
            product=prod, initial_load=load, number="LOTE-CO",
            number_normalized="LOTE-CO", initial_quantity=10,
            available_quantity=10, unit_cost=Decimal("2.0000"),
            expiration_date=date.today() + timedelta(days=30),
        )
        c = self._client_as("vendedor.a@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("50.00"), status="OPEN",
        )
        count_before = SaleDraftLine.objects.count()
        r = c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "1"})
        self.assertEqual(SaleDraftLine.objects.count(), count_before)

    # ══════════════════════════════════════════════════════════════════════════
    # VENCIMIENTO — lotes vencidos no son vendibles
    # ══════════════════════════════════════════════════════════════════════════

    def test_42_expired_lot_not_sellable(self):
        cat = Category.objects.create(name="Cat Exp E14", is_active=True)
        prod = Product.objects.create(
            name="Vencido E14", barcode="INT-VE-E14", barcode_type="INTERNAL",
            barcode_normalized="INT-VE-E14", search_name="vencido e14",
            category=cat, unit="UND", sale_price=Decimal("5.00"),
            minimum_stock=1, controls_expiration=True,
            average_cost=Decimal("2.0000"),
        )
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.warehouse)
        Lot.objects.create(
            product=prod, initial_load=load, number="LOTE-VE",
            number_normalized="LOTE-VE", initial_quantity=10,
            available_quantity=10, unit_cost=Decimal("2.0000"),
            expiration_date=date.today() - timedelta(days=1),  # VENCIDO
        )
        c = self._client_as("vendedor.a@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("50.00"), status="OPEN",
        )
        count_before = SaleDraftLine.objects.count()
        r = c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "1"})
        self.assertEqual(SaleDraftLine.objects.count(), count_before,
                         "Lote vencido no debe permitir venta")

    # ══════════════════════════════════════════════════════════════════════════
    # CIERRE CON BORRADOR ACTIVO — bloqueo
    # ══════════════════════════════════════════════════════════════════════════

    def test_43_cannot_close_with_active_draft(self):
        c = self._client_as("vendedor.a@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        cat = Category.objects.create(name="Cat Draft E14", is_active=True)
        prod = Product.objects.create(
            name="DraftBlock E14", barcode="INT-DB-E14", barcode_type="INTERNAL",
            barcode_normalized="INT-DB-E14", search_name="draftblock e14",
            category=cat, unit="UND", sale_price=Decimal("5.00"),
            minimum_stock=1, controls_expiration=True,
            average_cost=Decimal("2.0000"),
        )
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.warehouse)
        Lot.objects.create(
            product=prod, initial_load=load, number="LOTE-DB",
            number_normalized="LOTE-DB", initial_quantity=10,
            available_quantity=10, unit_cost=Decimal("2.0000"),
            expiration_date=date.today() + timedelta(days=30),
        )
        reg = CashRegister.objects.get(code="CAJA-01")
        shift = CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("50.00"), status="OPEN",
        )
        # Add line to draft
        r = c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "1"})
        self.assertIn(r.status_code, (301, 302))
        # Try close
        r = c.post("/caja/cerrar/", {"counted_amount": "50.00"})
        shift.refresh_from_db()
        self.assertEqual(shift.status, "OPEN",
                         "Turno no debe cerrarse con borrador activo")

    # ══════════════════════════════════════════════════════════════════════════
    # ADMIN: ajuste físico (solo admin puede)
    # ══════════════════════════════════════════════════════════════════════════

    def test_44_admin_physical_adjustment(self):
        c = self._client_as("admin@pruebas.invalid")
        cat = Category.objects.create(name="Cat Adj E14", is_active=True)
        prod = Product.objects.create(
            name="Ajustable E14", barcode="INT-AJ-E14", barcode_type="INTERNAL",
            barcode_normalized="INT-AJ-E14", search_name="ajustable e14",
            category=cat, unit="UND", sale_price=Decimal("10.00"),
            minimum_stock=1, controls_expiration=True,
            average_cost=Decimal("4.0000"),
        )
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.warehouse)
        lot = Lot.objects.create(
            product=prod, initial_load=load, number="LOTE-AJ",
            number_normalized="LOTE-AJ", initial_quantity=20,
            available_quantity=20, unit_cost=Decimal("4.0000"),
            expiration_date=date.today() + timedelta(days=60),
        )
        r = c.post("/inventario/ajustes/nuevo/", {
            "lot_id": str(lot.pk),
            "delta": "-3",
            "reason": "Conteo E14: faltaron 3",
            "idempotency_key": str(uuid.uuid4()),
        })
        self.assertIn(r.status_code, (301, 302))
        lot.refresh_from_db()
        self.assertEqual(lot.available_quantity, 17)

    # ══════════════════════════════════════════════════════════════════════════
    # VENDEDOR: historial del turno y constancia
    # ══════════════════════════════════════════════════════════════════════════

    def test_45_seller_views_shift_history(self):
        c = self._client_as("vendedor.a@pruebas.invalid")
        r = c.get("/ventas/historial/turno/")
        self.assertEqual(r.status_code, 200)

    def test_46_seller_views_own_sale_history(self):
        c = self._client_as("vendedor.a@pruebas.invalid")
        r = c.get("/ventas/historial/")
        self.assertEqual(r.status_code, 200)

    # ══════════════════════════════════════════════════════════════════════════
    # DASHBOARD — cada rol ve lo suyo
    # ══════════════════════════════════════════════════════════════════════════

    def test_50_admin_dashboard(self):
        c = self._client_as("admin@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertEqual(r.status_code, 200)

    def test_51_warehouse_dashboard(self):
        c = self._client_as("almacen@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertEqual(r.status_code, 200)

    def test_52_seller_dashboard(self):
        c = self._client_as("vendedor.a@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertEqual(r.status_code, 200)

    # ══════════════════════════════════════════════════════════════════════════
    # ADMIN: gestión de proveedores y categorías (toggle)
    # ══════════════════════════════════════════════════════════════════════════

    def test_53_admin_toggles_supplier(self):
        c = self._client_as("admin@pruebas.invalid")
        sup = Supplier.objects.create(name="ToggleProv E14", ruc="20111222333")
        r = c.post(f"/inventario/proveedores/{sup.pk}/estado/", {"is_active": "false"})
        self.assertIn(r.status_code, (301, 302))
        sup.refresh_from_db()
        self.assertFalse(sup.is_active)

    def test_54_admin_toggles_category(self):
        c = self._client_as("admin@pruebas.invalid")
        cat = Category.objects.create(name="ToggleCat E14", is_active=True)
        r = c.post(f"/productos/categorias/{cat.pk}/estado/", {
            "is_active": "false",
            "state_version": str(cat.state_version),
            "confirm": "yes",
        })
        self.assertIn(r.status_code, (301, 302))
        cat.refresh_from_db()
        self.assertFalse(cat.is_active)

    # ══════════════════════════════════════════════════════════════════════════
    # ALMACENERO: stock overview y movimientos (lectura)
    # ══════════════════════════════════════════════════════════════════════════

    def test_55_warehouse_views_stock_overview(self):
        c = self._client_as("almacen@pruebas.invalid")
        r = c.get("/inventario/stock/")
        self.assertEqual(r.status_code, 200)

    def test_56_warehouse_views_supplier_list(self):
        c = self._client_as("almacen@pruebas.invalid")
        r = c.get("/inventario/proveedores/")
        self.assertEqual(r.status_code, 200)

    # ══════════════════════════════════════════════════════════════════════════
    # EFECTO CRUZADO — venta reduce stock que almacenero ve actualizado
    # ══════════════════════════════════════════════════════════════════════════

    def test_60_sale_reduces_stock_seen_by_warehouse(self):
        """Tras una venta del vendedor, el almacenero ve stock actualizado."""
        cat = Category.objects.create(name="Cat Cross E14", is_active=True)
        prod = Product.objects.create(
            name="Cross E14", barcode="INT-CRS-E14", barcode_type="INTERNAL",
            barcode_normalized="INT-CRS-E14", search_name="cross e14",
            category=cat, unit="UND", sale_price=Decimal("10.00"),
            minimum_stock=1, controls_expiration=True,
            average_cost=Decimal("4.0000"),
        )
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.warehouse)
        lot = Lot.objects.create(
            product=prod, initial_load=load, number="LOTE-CRS",
            number_normalized="LOTE-CRS", initial_quantity=20,
            available_quantity=20, unit_cost=Decimal("4.0000"),
            expiration_date=date.today() + timedelta(days=60),
        )
        # Seller sells 5
        seller_c = self._client_as("vendedor.a@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("100.00"), status="OPEN",
        )
        seller_c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "5"})
        draft = SaleDraft.objects.filter(seller=self.seller, status="ACTIVE").first()
        if draft:
            from sales.services import draft_totals, draft_signature
            totals = draft_totals(draft)
            sig = draft_signature(draft.pk, draft.lines.all())
            seller_c.post("/ventas/cobrar/", {
                "cash_received": "100.00",
                "idempotency_key": str(uuid.uuid4()),
                "expected_subtotal": str(totals.total),
                "draft_signature": sig,
            })

        # Warehouse checks
        lot.refresh_from_db()
        self.assertEqual(lot.available_quantity, 15,
                         "El stock visto por almacenero debe reflejar la venta")

    # ══════════════════════════════════════════════════════════════════════════
    # EFECTO CRUZADO — merma del almacenero reduce vendible del vendedor
    # ══════════════════════════════════════════════════════════════════════════

    def test_61_writeoff_reduces_sellable(self):
        """Tras una merma del almacenero, el vendedor no puede vender más de lo disponible."""
        cat = Category.objects.create(name="Cat WOSell E14", is_active=True)
        prod = Product.objects.create(
            name="WOSell E14", barcode="INT-WOS-E14", barcode_type="INTERNAL",
            barcode_normalized="INT-WOS-E14", search_name="wosell e14",
            category=cat, unit="UND", sale_price=Decimal("5.00"),
            minimum_stock=1, controls_expiration=True,
            average_cost=Decimal("2.0000"),
        )
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.warehouse)
        lot = Lot.objects.create(
            product=prod, initial_load=load, number="LOTE-WOS",
            number_normalized="LOTE-WOS", initial_quantity=5,
            available_quantity=5, unit_cost=Decimal("2.0000"),
            expiration_date=date.today() + timedelta(days=30),
        )
        # Warehouse does writeoff of 4
        wh_c = self._client_as("almacen@pruebas.invalid")
        wh_c.post("/inventario/bajas/nueva/", {
            "lot_id": str(lot.pk), "quantity": "4", "reason": "DAÑO",
            "notes": "Dañados E14", "idempotency_key": str(uuid.uuid4()),
        })
        lot.refresh_from_db()
        self.assertEqual(lot.available_quantity, 1)

        # Seller tries to add 3 to draft — should fail
        seller_c = self._client_as("vendedor.a@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("50.00"), status="OPEN",
        )
        count_before = SaleDraftLine.objects.count()
        seller_c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "3"})
        # Should not create a draft line for 3 when only 1 available
        drafts_after = SaleDraftLine.objects.filter(
            draft__seller=self.seller, product=prod
        )
        if drafts_after.exists():
            self.fail("No debería poder agregar 3 unidades cuando solo hay 1 disponible")

    # ══════════════════════════════════════════════════════════════════════════
    # IDEMPOTENCIA — doble envío de cobro
    # ══════════════════════════════════════════════════════════════════════════

    def test_62_checkout_idempotency(self):
        """El mismo idempotency_key no debe generar dos ventas."""
        cat = Category.objects.create(name="Cat Idem E14", is_active=True)
        prod = Product.objects.create(
            name="Idem E14", barcode="INT-ID-E14", barcode_type="INTERNAL",
            barcode_normalized="INT-ID-E14", search_name="idem e14",
            category=cat, unit="UND", sale_price=Decimal("10.00"),
            minimum_stock=1, controls_expiration=True,
            average_cost=Decimal("4.0000"),
        )
        load = InitialInventoryLoad.objects.create(product=prod, responsible=self.warehouse)
        Lot.objects.create(
            product=prod, initial_load=load, number="LOTE-ID",
            number_normalized="LOTE-ID", initial_quantity=10,
            available_quantity=10, unit_cost=Decimal("4.0000"),
            expiration_date=date.today() + timedelta(days=60),
        )
        c = self._client_as("vendedor.a@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("50.00"), status="OPEN",
        )
        c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "1"})
        draft = SaleDraft.objects.filter(seller=self.seller, status="ACTIVE").first()
        self.assertIsNotNone(draft)
        from sales.services import draft_totals, draft_signature
        totals = draft_totals(draft)
        sig = draft_signature(draft.pk, draft.lines.all())
        idem_key = str(uuid.uuid4())
        checkout_data = {
            "cash_received": "20.00",
            "idempotency_key": idem_key,
            "expected_subtotal": str(totals.total),
            "draft_signature": sig,
        }
        r1 = c.post("/ventas/cobrar/", checkout_data)
        sales_count_after_first = Sale.objects.count()
        # Second attempt with same key
        r2 = c.post("/ventas/cobrar/", checkout_data)
        self.assertEqual(Sale.objects.count(), sales_count_after_first,
                         "Doble envío no debe crear segunda venta")
