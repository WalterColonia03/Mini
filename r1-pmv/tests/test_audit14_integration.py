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


class Stage14Closing2HistoriesAndRolesTest(TestCase):
    """Cobertura 14-CIERRE-2: historiales estables, borrador/reclasificación y salida segura."""

    @classmethod
    def setUpTestData(cls):
        from identity.models import Account, Role

        cls.admin_role, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
        cls.wh_role, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
        cls.seller_role, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

        cls.password = "ClaveSegura14Cierre2!"
        cls.admin = Account.objects.create_user(
            email="admin.c2@pruebas.invalid",
            password=cls.password,
            display_name="Admin Cierre 2",
            role=cls.admin_role,
            is_active=True,
        )
        cls.warehouse = Account.objects.create_user(
            email="almacen.c2@pruebas.invalid",
            password=cls.password,
            display_name="Almacenero Cierre 2",
            role=cls.wh_role,
            is_active=True,
        )
        cls.seller_a = Account.objects.create_user(
            email="vendedor.a.c2@pruebas.invalid",
            password=cls.password,
            display_name="Vendedor A Cierre 2",
            role=cls.seller_role,
            is_active=True,
        )
        cls.seller_b = Account.objects.create_user(
            email="vendedor.b.c2@pruebas.invalid",
            password=cls.password,
            display_name="Vendedor B Cierre 2",
            role=cls.seller_role,
            is_active=True,
        )
        cls.register, _ = CashRegister.objects.get_or_create(code="CAJA-01", defaults={"is_active": True})

    def _client_as(self, account):
        client = Client()
        client.force_login(account)
        return client

    def test_80_cash_shift_history_ties_pagination_dates_and_seller_scope(self):
        from cash.models import CashShift, CashShiftClose

        now = timezone.now()
        created_shifts = []
        for idx in range(26):
            owner = self.seller_a if idx < 14 else self.seller_b
            shift = CashShift.objects.create(
                cash_register=self.register,
                seller=owner,
                opening_amount=Decimal(f"{100 + idx}.00"),
                status=CashShift.Status.CLOSED,
            )
            CashShift.objects.filter(pk=shift.pk).update(opened_at=now)
            CashShiftClose.objects.create(
                cash_shift=shift,
                counted_amount=Decimal(f"{120 + idx}.00"),
                expected_amount=Decimal(f"{120 + idx}.00"),
                difference=Decimal("0.00"),
                closed_by=owner,
            )
            created_shifts.append(shift)

        expected_global_ids = [
            s.pk for s in sorted(created_shifts, key=lambda obj: obj.pk, reverse=True)
        ]

        admin_client = self._client_as(self.admin)
        p1 = admin_client.get("/caja/turnos/")
        self.assertEqual(p1.status_code, 200)
        p1_ids = [obj.pk for obj in p1.context["shifts"]]
        p2 = admin_client.get("/caja/turnos/?page=2")
        self.assertEqual(p2.status_code, 200)
        p2_ids = [obj.pk for obj in p2.context["shifts"]]

        self.assertEqual(len(p1_ids), 25)
        self.assertEqual(len(p2_ids), 1)
        self.assertEqual(len(set(p1_ids) & set(p2_ids)), 0)
        self.assertEqual(p1_ids + p2_ids, expected_global_ids)
        self.assertIn("Turnos encontrados (conjunto filtrado completo):</strong> 26", p1.content.decode())
        self.assertIn("Turnos encontrados (conjunto filtrado completo):</strong> 26", p2.content.decode())

        # Valid range preserves filter params across pagination
        today_str = timezone.localdate().isoformat()
        filtered_all_p1 = admin_client.get(
            f"/caja/turnos/?fecha_desde={today_str}&fecha_hasta={today_str}"
        )
        self.assertEqual(filtered_all_p1.status_code, 200)
        self.assertEqual(filtered_all_p1.context["total_shifts_count"], 26)
        self.assertIn(f"fecha_desde={today_str}", filtered_all_p1.context["next_url"])
        self.assertIn(f"fecha_hasta={today_str}", filtered_all_p1.context["next_url"])
        filtered_p1 = admin_client.get(
            f"/caja/turnos/?fecha_desde={today_str}&fecha_hasta={today_str}&vendedor={self.seller_a.pk}"
        )
        self.assertEqual(filtered_p1.status_code, 200)
        self.assertEqual(filtered_p1.context["total_shifts_count"], 14)

        # Validation hardening: never HTTP 500 on malformed/overflow/repeated/Unicode params
        bad_queries = [
            "/caja/turnos/?fecha_hasta=9999-12-31",
            "/caja/turnos/?fecha_desde=2026-02-30",
            "/caja/turnos/?fecha_desde=no-es-fecha",
            "/caja/turnos/?fecha_desde=2026-11-15&fecha_hasta=2026-11-10",
            "/caja/turnos/?page=0",
            "/caja/turnos/?page=-1",
            "/caja/turnos/?page=99",
            "/caja/turnos/?page=%C2%B2",
            "/caja/turnos/?page=1&page=2",
            "/caja/turnos/?fecha_desde=2026-11-01&fecha_desde=2026-11-02",
            "/caja/turnos/?vendedor=%00",
        ]
        for query in bad_queries:
            res = admin_client.get(query)
            self.assertEqual(res.status_code, 200, f"Debe responder 200 controlado en {query}")
            self.assertTrue(res.context["has_invalid_query"], f"Debe marcar error en {query}")

        # Seller scope isolation + parameter tampering block
        seller_a_client = self._client_as(self.seller_a)
        res_tamper = seller_a_client.get(f"/caja/turnos/?vendedor={self.seller_b.pk}")
        self.assertEqual(res_tamper.status_code, 200)
        self.assertTrue(all(obj.seller_id == self.seller_a.pk for obj in res_tamper.context["shifts"]))
        self.assertEqual(res_tamper.context["total_shifts_count"], 14)

        b_shift = next(obj for obj in created_shifts if obj.seller_id == self.seller_b.pk)
        res_foreign_close = seller_a_client.get(f"/caja/turnos/{b_shift.pk}/cerrado/")
        self.assertEqual(res_foreign_close.status_code, 404)

    def test_81_sales_history_and_shift_sales_ties_totals_and_role_boundaries(self):
        from cash.models import CashShift, CashShiftClose
        from sales.models import Sale, SaleLine

        cat = Category.objects.create(name="Hist Cierre 2 Cat", is_active=True)
        prod = Product.objects.create(
            name="Producto Costo Privado",
            barcode="INT-HIST-C2",
            barcode_type="INTERNAL",
            barcode_normalized="INT-HIST-C2",
            search_name="producto costo privado",
            category=cat,
            unit="UND",
            sale_price=Decimal("10.00"),
            average_cost=Decimal("4.3333"),
            minimum_stock=1,
            controls_expiration=True,
        )

        shift_a_closed = CashShift.objects.create(
            cash_register=self.register,
            seller=self.seller_a,
            opening_amount=Decimal("50.00"),
            status=CashShift.Status.CLOSED,
        )
        CashShiftClose.objects.create(
            cash_shift=shift_a_closed,
            counted_amount=Decimal("50.00"),
            expected_amount=Decimal("50.00"),
            difference=Decimal("0.00"),
            closed_by=self.seller_a,
        )
        shift_b_closed = CashShift.objects.create(
            cash_register=self.register,
            seller=self.seller_b,
            opening_amount=Decimal("50.00"),
            status=CashShift.Status.CLOSED,
        )
        CashShiftClose.objects.create(
            cash_shift=shift_b_closed,
            counted_amount=Decimal("50.00"),
            expected_amount=Decimal("50.00"),
            difference=Decimal("0.00"),
            closed_by=self.seller_b,
        )
        shift_a_open = CashShift.objects.create(
            cash_register=self.register,
            seller=self.seller_a,
            opening_amount=Decimal("80.00"),
            status=CashShift.Status.OPEN,
        )

        same_ts = timezone.now()
        created_sales = []
        for idx in range(26):
            if idx < 2:
                owner, shift = self.seller_a, shift_a_open
            elif idx < 14:
                owner, shift = self.seller_a, shift_a_closed
            else:
                owner, shift = self.seller_b, shift_b_closed
            sale = Sale.objects.create(
                cash_shift=shift,
                seller=owner,
                seller_snapshot_name=owner.display_name,
                cash_register_snapshot_code=self.register.code,
                total_amount=Decimal("10.00"),
                base_amount=Decimal("8.47"),
                igv_amount=Decimal("1.53"),
                discount_amount=Decimal("0.00"),
                cash_received=Decimal("10.00"),
                change_given=Decimal("0.00"),
                correlative=f"V-0000{idx + 1:04d}",
                idempotency_key=uuid.uuid4(),
            )
            Sale.objects.filter(pk=sale.pk).update(confirmed_at=same_ts)
            SaleLine.objects.create(
                sale=sale,
                position=1,
                product=prod,
                product_snapshot_name=prod.name,
                product_snapshot_barcode=prod.barcode,
                quantity=1,
                unit_price=Decimal("10.00"),
                amount=Decimal("10.00"),
                unit_cost=Decimal("4.3333"),
            )
            created_sales.append(sale)

        expected_ids = [
            s.pk
            for s in sorted(
                created_sales,
                key=lambda obj: (obj.correlative, str(obj.pk)),
                reverse=True,
            )
        ]

        admin_client = self._client_as(self.admin)
        p1 = admin_client.get("/ventas/historial/")
        p2 = admin_client.get("/ventas/historial/?page=2")
        self.assertEqual(p1.status_code, 200)
        self.assertEqual(p2.status_code, 200)
        p1_ids = [s.pk for s in p1.context["sales"]]
        p2_ids = [s.pk for s in p2.context["sales"]]
        self.assertEqual(len(p1_ids), 25)
        self.assertEqual(len(p2_ids), 1)
        self.assertEqual(p1_ids + p2_ids, expected_ids)
        self.assertIn("Total vendido (filtrado):", p1.content.decode())
        self.assertEqual(p1.context["total_sales_count"], 26)
        self.assertEqual(p2.context["total_sales_count"], 26)
        self.assertEqual(p1.context["total_vendido"], Decimal("260.00"))
        self.assertEqual(p2.context["total_vendido"], Decimal("260.00"))

        today_str = timezone.localdate().isoformat()
        sales_filt_p1 = admin_client.get(
            f"/ventas/historial/?fecha_desde={today_str}&fecha_hasta={today_str}&correlativo=V-"
        )
        self.assertEqual(sales_filt_p1.status_code, 200)
        self.assertEqual(sales_filt_p1.context["total_sales_count"], 26)
        self.assertIn(f"fecha_desde={today_str}", sales_filt_p1.context["next_url"])
        self.assertIn("correlativo=V-", sales_filt_p1.context["next_url"])

        # Validation hardening on /ventas/historial/
        for bad_q in [
            "/ventas/historial/?fecha_hasta=9999-12-31",
            "/ventas/historial/?fecha_desde=2026-11-20&fecha_hasta=2026-11-01",
            "/ventas/historial/?page=99",
            "/ventas/historial/?page=%C2%B2",
            "/ventas/historial/?page=1&page=2",
            "/ventas/historial/?correlativo=x&correlativo=y",
            "/ventas/historial/?correlativo=%00",
        ]:
            res = admin_client.get(bad_q)
            self.assertEqual(res.status_code, 200)
            self.assertTrue(res.context["has_invalid_query"], f"Esperaba error controlado en {bad_q}")

        # Admin views receipt: never "Nueva venta", never purchase unit_cost
        sample_sale = created_sales[0]
        rec_admin = admin_client.get(f"/ventas/constancia/{sample_sale.pk}/")
        self.assertEqual(rec_admin.status_code, 200)
        html_admin = rec_admin.content.decode()
        self.assertNotIn("Nueva venta", html_admin)
        self.assertNotIn("4.3333", html_admin)
        self.assertNotIn("4,3333", html_admin)

        # Seller navigation & shift history + forbidden cross-role routes
        seller_a_client = self._client_as(self.seller_a)
        hist_a = seller_a_client.get("/ventas/historial/")
        self.assertEqual(hist_a.status_code, 200)
        hist_a_html = hist_a.content.decode()
        self.assertIn("Ventas del turno", hist_a_html)
        self.assertIn("Mis turnos", hist_a_html)
        self.assertEqual(hist_a.context["total_sales_count"], 14)

        shift_hist_a = seller_a_client.get("/ventas/historial/turno/")
        self.assertEqual(shift_hist_a.status_code, 200)
        self.assertEqual(len(shift_hist_a.context["sales"]), 2)
        self.assertEqual(shift_hist_a.context["shift_total"], Decimal("20.00"))
        self.assertIn("Mis turnos", shift_hist_a.content.decode())

        foreign_sale = next(s for s in created_sales if s.seller_id == self.seller_b.pk)
        self.assertEqual(seller_a_client.get(f"/ventas/constancia/{foreign_sale.pk}/").status_code, 404)
        self.assertEqual(seller_a_client.get("/productos/").status_code, 403)
        self.assertEqual(seller_a_client.get("/productos/categorias/").status_code, 403)
        self.assertEqual(seller_a_client.get("/inventario/stock/").status_code, 403)

    def test_82_draft_grouping_update_remove_last_line_and_discard(self):
        from cash.models import CashShift
        from inventory.services import LotInput, confirm_initial_load
        from sales.models import SaleDraft, SaleDraftLine

        cat = Category.objects.create(name="Borrador C2 Cat", is_active=True)
        prod = Product.objects.create(
            name="Gaseosa Borrador C2",
            barcode="INT-DRAFT-C2",
            barcode_type="INTERNAL",
            barcode_normalized="INT-DRAFT-C2",
            search_name="gaseosa borrador c2",
            category=cat,
            unit="UND",
            sale_price=Decimal("4.50"),
            minimum_stock=1,
            controls_expiration=True,
        )
        confirm_initial_load(
            actor=self.warehouse,
            product=prod,
            lots=[LotInput("L-C2", 10, Decimal("2.50"), timezone.localdate() + timedelta(days=60))],
        )
        shift = CashShift.objects.create(
            cash_register=self.register,
            seller=self.seller_a,
            opening_amount=Decimal("50.00"),
            status=CashShift.Status.OPEN,
        )

        seller_client = self._client_as(self.seller_a)
        # Group repeat additions into single draft line (2 + 3 = 5)
        r1 = seller_client.post("/ventas/", {"product_id": str(prod.pk), "quantity": "2"})
        r2 = seller_client.post("/ventas/", {"product_id": str(prod.pk), "quantity": "3"})
        self.assertEqual(r1.status_code, 302)
        self.assertEqual(r2.status_code, 302)

        draft = SaleDraft.objects.get(cash_shift=shift, status=SaleDraft.Status.ACTIVE)
        self.assertEqual(draft.lines.count(), 1)
        line = draft.lines.get()
        self.assertEqual(line.quantity, 5)

        # Update line quantity -> 4
        ru = seller_client.post(f"/ventas/lineas/{line.pk}/", {"quantity": "4"})
        self.assertEqual(ru.status_code, 302)
        line.refresh_from_db()
        self.assertEqual(line.quantity, 4)

        # Remove the sole line -> draft itself must become DISCARDED so cash close succeeds
        rr = seller_client.post(f"/ventas/lineas/{line.pk}/quitar/")
        self.assertEqual(rr.status_code, 302)
        draft.refresh_from_db()
        self.assertEqual(draft.status, SaleDraft.Status.DISCARDED)
        self.assertFalse(SaleDraftLine.objects.filter(draft=draft).exists())

        # Re-add and test explicit discard leaves lot stock intact & allows cash close
        seller_client.post("/ventas/", {"product_id": str(prod.pk), "quantity": "2"})
        rd = seller_client.post("/ventas/descartar/")
        self.assertEqual(rd.status_code, 302)
        prod.refresh_from_db()
        self.assertEqual(prod.lots.get().available_quantity, 10)

        rc = seller_client.post("/caja/cerrar/", {"counted_amount": "50.00"})
        self.assertEqual(rc.status_code, 302)
        shift.refresh_from_db()
        self.assertEqual(shift.status, CashShift.Status.CLOSED)

    def test_83_admin_reclassifies_product_while_seller_has_open_draft(self):
        from cash.models import CashShift
        from catalog.services import product_edit_snapshot
        from django.core import signing
        from inventory.services import LotInput, confirm_initial_load
        from sales.models import Sale

        cat_a = Category.objects.create(name="Cat Origen C2", is_active=True)
        cat_b = Category.objects.create(name="Cat Destino C2", is_active=True)
        prod = Product.objects.create(
            name="Yogurt Reclasificado C2",
            barcode="INT-RECLAS-C2",
            barcode_type="INTERNAL",
            barcode_normalized="INT-RECLAS-C2",
            search_name="yogurt reclasificado c2",
            category=cat_a,
            unit="UND",
            sale_price=Decimal("7.50"),
            minimum_stock=1,
            controls_expiration=True,
        )
        confirm_initial_load(
            actor=self.warehouse,
            product=prod,
            lots=[LotInput("L-REC", 8, Decimal("4.00"), timezone.localdate() + timedelta(days=45))],
        )
        CashShift.objects.create(
            cash_register=self.register,
            seller=self.seller_a,
            opening_amount=Decimal("20.00"),
            status=CashShift.Status.OPEN,
        )

        seller_client = self._client_as(self.seller_a)
        seller_client.post("/ventas/", {"product_id": str(prod.pk), "quantity": "2"})
        checkout_page = seller_client.get("/ventas/cobrar/")
        self.assertEqual(checkout_page.status_code, 200)
        form = checkout_page.context["form"]

        # Admin reclassifies category while keeping price and barcode
        admin_client = self._client_as(self.admin)
        snapshot_token = signing.dumps(product_edit_snapshot(prod), salt="catalog.product-edit")
        reclass = admin_client.post(
            f"/productos/{prod.pk}/editar/",
            {
                "name": prod.name,
                "barcode_type": prod.barcode_type,
                "barcode": prod.barcode,
                "category": str(cat_b.pk),
                "sale_price": "7.50",
                "minimum_stock": "1",
                "edit_snapshot": snapshot_token,
            },
        )
        self.assertEqual(reclass.status_code, 302)
        prod.refresh_from_db()
        self.assertEqual(prod.category_id, cat_b.pk)

        # Seller finishes checkout seamlessly after reclassification
        pay = seller_client.post(
            "/ventas/cobrar/",
            {
                "cash_received": "20.00",
                "idempotency_key": str(form["idempotency_key"].value()),
                "expected_subtotal": str(form["expected_subtotal"].value()),
                "draft_signature": str(form["draft_signature"].value()),
            },
        )
        self.assertEqual(pay.status_code, 302)
        sale = Sale.objects.order_by("-confirmed_at", "-id").first()
        self.assertEqual(sale.total_amount, Decimal("15.00"))
        self.assertEqual(prod.lots.get().available_quantity, 6)

    def test_84_logout_warnings_and_cross_seller_shift_isolation(self):
        from cash.models import CashShift
        from inventory.services import LotInput, confirm_initial_load
        from sales.models import SaleDraft

        cat = Category.objects.create(name="Logout C2 Cat", is_active=True)
        prod = Product.objects.create(
            name="Galleta Salida C2",
            barcode="INT-OUT-C2",
            barcode_type="INTERNAL",
            barcode_normalized="INT-OUT-C2",
            search_name="galleta salida c2",
            category=cat,
            unit="UND",
            sale_price=Decimal("3.00"),
            minimum_stock=1,
            controls_expiration=True,
        )
        confirm_initial_load(
            actor=self.warehouse,
            product=prod,
            lots=[LotInput("L-OUT", 6, Decimal("1.50"), timezone.localdate() + timedelta(days=60))],
        )

        # Admin logout prompt must not mention open cash shift
        admin_client = self._client_as(self.admin)
        out_admin = admin_client.get("/salir/")
        self.assertEqual(out_admin.status_code, 200)
        self.assertNotIn("turno abierto", out_admin.content.decode().lower())

        # Seller A opens shift and prepares a draft
        seller_a_client = self._client_as(self.seller_a)
        shift = CashShift.objects.create(
            cash_register=self.register,
            seller=self.seller_a,
            opening_amount=Decimal("40.00"),
            status=CashShift.Status.OPEN,
        )
        seller_a_client.post("/ventas/", {"product_id": str(prod.pk), "quantity": "2"})
        draft = SaleDraft.objects.get(cash_shift=shift, status=SaleDraft.Status.ACTIVE)

        # Viewing logout page warns but cancels cleanly without discarding draft
        out_a_get = seller_a_client.get("/salir/")
        self.assertEqual(out_a_get.status_code, 200)
        html_a = out_a_get.content.decode()
        self.assertIn("turno abierto", html_a.lower())
        self.assertIn("venta en preparación", html_a.lower())
        draft.refresh_from_db()
        self.assertEqual(draft.status, SaleDraft.Status.ACTIVE)

        # Confirming logout discards draft, keeps shift open and stock unchanged, and expires session
        out_a_post = seller_a_client.post("/salir/")
        self.assertEqual(out_a_post.status_code, 302)
        draft.refresh_from_db()
        shift.refresh_from_db()
        self.assertEqual(draft.status, SaleDraft.Status.DISCARDED)
        self.assertEqual(shift.status, CashShift.Status.OPEN)
        self.assertEqual(prod.lots.get().available_quantity, 6)
        self.assertEqual(seller_a_client.get("/ventas/").status_code, 302)

        # Seller B without open shift does not receive misleading open-shift prompt, and cannot hijack A's shift
        seller_b_client = self._client_as(self.seller_b)
        out_b_get = seller_b_client.get("/salir/")
        self.assertEqual(out_b_get.status_code, 200)
        self.assertNotIn("turno abierto", out_b_get.content.decode().lower())
        open_b = seller_b_client.post("/caja/abrir/", {"opening_amount": "10.00"})
        self.assertIn(open_b.status_code, (200, 409))
        self.assertEqual(CashShift.objects.filter(status=CashShift.Status.OPEN).count(), 1)
        pos_b = seller_b_client.post("/ventas/", {"product_id": str(prod.pk), "quantity": "1"})
        self.assertEqual(pos_b.status_code, 200)
        self.assertIn("Requiere turno abierto", pos_b.content.decode())
        self.assertFalse(SaleDraft.objects.filter(status=SaleDraft.Status.ACTIVE).exists())
        checkout_b = seller_b_client.post(
            "/ventas/cobrar/",
            {"cash_received": "10.00", "idempotency_key": str(uuid.uuid4())},
        )
        self.assertEqual(checkout_b.status_code, 302)
        self.assertEqual(prod.lots.get().available_quantity, 6)

        # Seller A logs back in via real form and recovers the open shift without old draft
        login_res = seller_a_client.post("/", {"email": self.seller_a.email, "password": self.password})
        self.assertEqual(login_res.status_code, 302)
        pos_a = seller_a_client.get("/ventas/")
        self.assertEqual(pos_a.status_code, 200)
        self.assertEqual(pos_a.context["current_shift"].pk, shift.pk)
        self.assertIsNone(pos_a.context["draft"])

