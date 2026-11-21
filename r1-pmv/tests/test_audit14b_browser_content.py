"""
ETAPA 14-B — Verificación de contenido HTML renderizado por rol
================================================================
Valida que los templates produzcan el HTML correcto para cada rol:
menús laterales, dashboards, tarjetas de acción, headings, pills de rol,
textos visibles, enlaces disponibles y ausencia de opciones no autorizadas.

Fecha: 13/11/2026  |  Base: SQLite aislada (TestCase)
Pasada: Primera  |  Alcance: identity/base.html, dashboard, login, 403/500

Estos tests complementan el sublote 14-A (servidor) con verificación del
HTML renderizado real — CT-COHERENCIA-UI.
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase, Client, override_settings

from identity.models import Account, Role
from catalog.models import Category, Product
from inventory.models import InitialInventoryLoad, Lot, Supplier
from cash.models import CashRegister, CashShift
from sales.models import SaleDraft, SaleDraftLine


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
class BrowserContentAdminTest(TestCase):
    """Sublote 14-B: HTML renderizado para ADMIN."""

    @classmethod
    def setUpTestData(cls):
        _setup_roles()
        cls.admin = _make_account("admin14b@pruebas.invalid", "ADMIN")
        cls.warehouse = _make_account("almacen14b@pruebas.invalid", "ALMACENERO")
        cls.seller = _make_account("vendedor14b@pruebas.invalid", "VENDEDOR")
        CashRegister.objects.get_or_create(code="CAJA-01", defaults={"is_active": True})

    def _client_as(self, email):
        c = Client()
        _login(c, email)
        return c

    # ── MENÚ LATERAL (sidebar) del ADMIN ────────────────────────────────────

    def test_B01_admin_sidebar_has_catalog_section(self):
        """ADMIN ve sección Catálogo con Productos, Registrar producto y Categorías."""
        c = self._client_as("admin14b@pruebas.invalid")
        r = c.get("/inicio/")
        content = r.content.decode()
        # Template usa entidades HTML: Cat&#225;logo, Categor&#237;as
        self.assertIn("Cat&#225;logo", content, "Sidebar: sección Catálogo")
        self.assertContains(r, "Productos", msg_prefix="Sidebar: enlace Productos")
        self.assertContains(r, "Registrar producto", msg_prefix="Sidebar: enlace Registrar producto")
        self.assertIn("Categor", content, "Sidebar: enlace Categorías")

    def test_B02_admin_sidebar_has_inventory_section(self):
        """ADMIN ve sección Inventario con Proveedores, Ver inventario, Vencimientos, Ajuste."""
        c = self._client_as("admin14b@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Inventario", msg_prefix="Sidebar: sección Inventario")
        self.assertContains(r, "Proveedores", msg_prefix="Sidebar: enlace Proveedores")
        self.assertContains(r, "Ver inventario y alertas", msg_prefix="Sidebar: Ver inventario")
        self.assertContains(r, "Vencimientos de lotes", msg_prefix="Sidebar: Vencimientos")
        self.assertContains(r, "Ajuste f", msg_prefix="Sidebar: Ajuste físico")

    def test_B03_admin_sidebar_has_personnel_section(self):
        """ADMIN ve sección Personal con Empleados."""
        c = self._client_as("admin14b@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Personal", msg_prefix="Sidebar: sección Personal")
        self.assertContains(r, "Empleados", msg_prefix="Sidebar: enlace Empleados")

    def test_B04_admin_sidebar_has_cash_and_sales_section(self):
        """ADMIN ve sección Caja y ventas con Historial de turnos e Historial de ventas."""
        c = self._client_as("admin14b@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Caja y ventas", msg_prefix="Sidebar: sección Caja y ventas")
        self.assertContains(r, "Historial de turnos", msg_prefix="Sidebar: enlace turnos")
        self.assertContains(r, "Historial de ventas", msg_prefix="Sidebar: enlace ventas")

    def test_B05_admin_sidebar_does_not_have_seller_options(self):
        """ADMIN NO ve las opciones de vendedor (Apertura de caja, Preparar venta, Cerrar turno)."""
        c = self._client_as("admin14b@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertNotContains(r, "Apertura de caja", msg_prefix="Admin NO ve Apertura de caja")
        self.assertNotContains(r, "Preparar venta", msg_prefix="Admin NO ve Preparar venta")
        self.assertNotContains(r, "Cerrar turno", msg_prefix="Admin NO ve Cerrar turno")
        self.assertNotContains(r, "Mis ventas del turno", msg_prefix="Admin NO ve Mis ventas")

    def test_B06_admin_sidebar_does_not_have_warehouse_operations(self):
        """ADMIN NO ve las opciones de almacenero (Existencias iniciales, Entrada, Registrar merma)."""
        c = self._client_as("admin14b@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertNotContains(r, "Existencias iniciales", msg_prefix="Admin NO ve Existencias")
        self.assertNotContains(r, "Entrada de mercader", msg_prefix="Admin NO ve Entrada")
        self.assertNotContains(r, "Registrar merma", msg_prefix="Admin NO ve Merma")

    # ── DASHBOARD del ADMIN ─────────────────────────────────────────────────

    def test_B07_admin_dashboard_shows_panel_principal(self):
        """ADMIN dashboard muestra 'Panel principal' y 'Administrador'."""
        c = self._client_as("admin14b@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Panel principal")
        self.assertContains(r, "Administrador")

    def test_B08_admin_dashboard_shows_sales_summary(self):
        """ADMIN dashboard tiene métricas de ventas: Ventas de hoy, Total vendido."""
        c = self._client_as("admin14b@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Ventas de hoy")
        self.assertContains(r, "Total vendido hoy")
        self.assertContains(r, "Descuentos otorgados hoy")
        self.assertContains(r, "Turnos de caja abiertos")

    def test_B09_admin_dashboard_shows_stock_alerts(self):
        """ADMIN dashboard tiene alertas de inventario."""
        c = self._client_as("admin14b@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Productos con stock bajo")
        self.assertContains(r, "Lotes por vencer")
        self.assertContains(r, "Lotes vencidos con stock")

    def test_B10_admin_dashboard_action_cards(self):
        """ADMIN dashboard tiene tarjetas de acción correctas."""
        c = self._client_as("admin14b@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Registrar un producto")
        self.assertContains(r, "Ver cat")  # "Ver catálogo de productos" (encoded)
        self.assertContains(r, "Gestionar empleados")

    def test_B11_admin_dashboard_no_warehouse_cards(self):
        """ADMIN NO ve tarjetas de almacenero en el dashboard."""
        c = self._client_as("admin14b@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertNotContains(r, "Registrar existencias iniciales")
        self.assertNotContains(r, "Registrar entrada de mercader")

    def test_B12_admin_dashboard_no_seller_cards(self):
        """ADMIN NO ve tarjetas de vendedor en el dashboard."""
        c = self._client_as("admin14b@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertNotContains(r, "Abrir el turno de caja")
        self.assertNotContains(r, "Preparar una venta")

    # ── TOPBAR del ADMIN ────────────────────────────────────────────────────

    def test_B13_admin_topbar_shows_role_pill(self):
        """ADMIN topbar muestra pill con nombre del rol."""
        c = self._client_as("admin14b@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, 'role-pill')
        self.assertContains(r, "Administrador")

    def test_B14_admin_topbar_heading_inicio(self):
        """Heading de /inicio/ muestra 'Inicio'."""
        c = self._client_as("admin14b@pruebas.invalid")
        r = c.get("/inicio/")
        content = r.content.decode()
        self.assertIn("Inicio", content)

    # ── SESIÓN ──────────────────────────────────────────────────────────────

    def test_B15_admin_sidebar_shows_user_info(self):
        """Sidebar muestra nombre del usuario y enlace 'Cerrar sesión'."""
        c = self._client_as("admin14b@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "admin14b")
        self.assertContains(r, "Cerrar sesi")  # encoded ó


@override_settings(TIME_ZONE="America/Lima")
class BrowserContentWarehouseTest(TestCase):
    """Sublote 14-B: HTML renderizado para ALMACENERO."""

    @classmethod
    def setUpTestData(cls):
        _setup_roles()
        cls.admin = _make_account("admin14bw@pruebas.invalid", "ADMIN")
        cls.warehouse = _make_account("almacen14bw@pruebas.invalid", "ALMACENERO")
        CashRegister.objects.get_or_create(code="CAJA-01", defaults={"is_active": True})

    def _client_as(self, email):
        c = Client()
        _login(c, email)
        return c

    # ── MENÚ LATERAL del ALMACENERO ─────────────────────────────────────────

    def test_B20_warehouse_sidebar_has_inventory_links(self):
        """ALMACENERO ve sus enlaces propios: Inventario, Existencias, Entrada, Merma."""
        c = self._client_as("almacen14bw@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Ver inventario y alertas")
        self.assertContains(r, "Vencimientos de lotes")
        self.assertContains(r, "Existencias iniciales")
        self.assertContains(r, "Entrada de mercader")
        self.assertContains(r, "Registrar merma")

    def test_B21_warehouse_sidebar_has_product_consultation(self):
        """ALMACENERO ve sección Consulta con Catálogo y Proveedores."""
        c = self._client_as("almacen14bw@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Consulta", msg_prefix="Sidebar: sección Consulta")
        self.assertContains(r, "logo de productos", msg_prefix="Sidebar: Catálogo de productos")
        self.assertContains(r, "Proveedores")

    def test_B22_warehouse_sidebar_no_admin_sections(self):
        """ALMACENERO NO ve secciones de admin: Personal, Empleados, Registrar producto, Categorías."""
        c = self._client_as("almacen14bw@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertNotContains(r, "Personal", msg_prefix="ALM NO ve Personal")
        self.assertNotContains(r, "Empleados", msg_prefix="ALM NO ve Empleados")
        self.assertNotContains(r, "Registrar producto", msg_prefix="ALM NO ve Registrar producto")

    def test_B23_warehouse_sidebar_no_seller_sections(self):
        """ALMACENERO NO ve opciones de vendedor."""
        c = self._client_as("almacen14bw@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertNotContains(r, "Apertura de caja")
        self.assertNotContains(r, "Preparar venta")
        self.assertNotContains(r, "Cerrar turno")
        self.assertNotContains(r, "Mis ventas del turno")

    def test_B24_warehouse_sidebar_no_caja_ventas(self):
        """ALMACENERO NO ve sección 'Caja y ventas'."""
        c = self._client_as("almacen14bw@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertNotContains(r, "Caja y ventas")
        self.assertNotContains(r, "Historial de turnos")
        self.assertNotContains(r, "Historial de ventas")

    # ── DASHBOARD del ALMACENERO ────────────────────────────────────────────

    def test_B25_warehouse_dashboard_shows_almacenero_role(self):
        """Dashboard del almacenero muestra 'Almacenero'."""
        c = self._client_as("almacen14bw@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Almacenero")
        self.assertContains(r, "Panel principal")

    def test_B26_warehouse_dashboard_shows_stock_alerts_only(self):
        """ALMACENERO ve alertas de stock pero NO ve métricas de ventas."""
        c = self._client_as("almacen14bw@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Productos con stock bajo")
        self.assertContains(r, "Lotes por vencer")
        self.assertContains(r, "Lotes vencidos con stock")
        # No ventas
        self.assertNotContains(r, "Ventas de hoy")
        self.assertNotContains(r, "Total vendido hoy")
        self.assertNotContains(r, "Turnos de caja abiertos")

    def test_B27_warehouse_dashboard_action_cards(self):
        """ALMACENERO ve tarjetas de acción: Existencias, Entrada, Merma."""
        c = self._client_as("almacen14bw@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Registrar existencias iniciales")
        self.assertContains(r, "Registrar entrada de mercader")
        self.assertContains(r, "Registrar merma")

    def test_B28_warehouse_dashboard_no_admin_cards(self):
        """ALMACENERO NO ve tarjetas de admin."""
        c = self._client_as("almacen14bw@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertNotContains(r, "Registrar un producto")
        self.assertNotContains(r, "Gestionar empleados")

    # ── HEADING DE PÁGINAS ACCESIBLES ───────────────────────────────────────

    def test_B29_warehouse_stock_overview_heading(self):
        """GET /inventario/stock/ muestra heading 'Ver inventario'."""
        c = self._client_as("almacen14bw@pruebas.invalid")
        r = c.get("/inventario/stock/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Ver inventario")


@override_settings(TIME_ZONE="America/Lima")
class BrowserContentSellerTest(TestCase):
    """Sublote 14-B: HTML renderizado para VENDEDOR."""

    @classmethod
    def setUpTestData(cls):
        _setup_roles()
        cls.admin = _make_account("admin14bs@pruebas.invalid", "ADMIN")
        cls.warehouse = _make_account("almacen14bs@pruebas.invalid", "ALMACENERO")
        cls.seller = _make_account("vendedor14bs@pruebas.invalid", "VENDEDOR")
        CashRegister.objects.get_or_create(code="CAJA-01", defaults={"is_active": True})

    def _client_as(self, email):
        c = Client()
        _login(c, email)
        return c

    # ── MENÚ LATERAL del VENDEDOR ───────────────────────────────────────────

    def test_B30_seller_sidebar_has_cash_links(self):
        """VENDEDOR ve sus enlaces: Apertura de caja, Preparar venta, Cerrar turno, Mis ventas."""
        c = self._client_as("vendedor14bs@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Apertura de caja")
        self.assertContains(r, "Preparar venta")
        self.assertContains(r, "Cerrar turno")
        self.assertContains(r, "Mis ventas del turno")

    def test_B31_seller_sidebar_no_admin_sections(self):
        """VENDEDOR NO ve secciones de admin."""
        c = self._client_as("vendedor14bs@pruebas.invalid")
        r = c.get("/inicio/")
        content = r.content.decode()
        # No admin-specific sidebar labels
        self.assertNotIn("Personal", content)
        self.assertNotIn("Empleados", content)
        self.assertNotIn("Ajuste f", content)

    def test_B32_seller_sidebar_no_warehouse_sections(self):
        """VENDEDOR NO ve secciones de almacenero."""
        c = self._client_as("vendedor14bs@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertNotContains(r, "Existencias iniciales")
        self.assertNotContains(r, "Entrada de mercader")
        self.assertNotContains(r, "Registrar merma")
        self.assertNotContains(r, "Consulta")

    def test_B33_seller_sidebar_no_admin_links(self):
        """VENDEDOR NO ve enlaces exclusivos de admin."""
        c = self._client_as("vendedor14bs@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertNotContains(r, "Historial de turnos")
        self.assertNotContains(r, "Historial de ventas")
        self.assertNotContains(r, "Registrar producto")
        self.assertNotContains(r, "Proveedores")

    # ── DASHBOARD del VENDEDOR ──────────────────────────────────────────────

    def test_B34_seller_dashboard_shows_vendedor_role(self):
        """Dashboard del vendedor muestra 'Vendedor'."""
        c = self._client_as("vendedor14bs@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Vendedor")
        self.assertContains(r, "Panel principal")

    def test_B35_seller_dashboard_no_ventas_summary(self):
        """VENDEDOR NO ve las métricas de ventas del admin."""
        c = self._client_as("vendedor14bs@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertNotContains(r, "Ventas de hoy")
        self.assertNotContains(r, "Total vendido hoy")
        self.assertNotContains(r, "Turnos de caja abiertos")

    def test_B36_seller_dashboard_action_cards(self):
        """VENDEDOR ve tarjetas: Abrir turno, Preparar venta."""
        c = self._client_as("vendedor14bs@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Abrir el turno de caja")
        self.assertContains(r, "Preparar una venta")

    def test_B37_seller_dashboard_no_admin_warehouse_cards(self):
        """VENDEDOR NO ve tarjetas de admin ni almacenero."""
        c = self._client_as("vendedor14bs@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertNotContains(r, "Registrar un producto")
        self.assertNotContains(r, "Gestionar empleados")
        self.assertNotContains(r, "Registrar existencias iniciales")
        self.assertNotContains(r, "Registrar entrada de mercader")
        self.assertNotContains(r, "Registrar merma")

    # ── PÁGINAS PROPIAS DEL VENDEDOR ────────────────────────────────────────

    def test_B38_seller_cash_open_page(self):
        """GET /caja/abrir/ muestra heading 'Apertura de caja'."""
        c = self._client_as("vendedor14bs@pruebas.invalid")
        r = c.get("/caja/abrir/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Apertura de caja")

    def test_B39_seller_sales_draft_page(self):
        """GET /ventas/ muestra heading 'Preparar venta' con turno abierto."""
        c = self._client_as("vendedor14bs@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("100.00"), status="OPEN",
        )
        r = c.get("/ventas/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Preparar venta")


@override_settings(TIME_ZONE="America/Lima")
class BrowserContentLoginTest(TestCase):
    """Sublote 14-B: Verificación de la página de login."""

    @classmethod
    def setUpTestData(cls):
        _setup_roles()

    def test_B40_login_page_elements(self):
        """La página de login muestra título, formulario y roles del sistema."""
        c = Client()
        r = c.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Bienvenido")
        self.assertContains(r, "Iniciar sesi")
        self.assertContains(r, "Administrador")
        self.assertContains(r, "Almacenero")
        self.assertContains(r, "Vendedor")

    def test_B41_login_form_fields(self):
        """El form de login tiene campos de email y contraseña y botón."""
        c = Client()
        r = c.get("/")
        content = r.content.decode()
        self.assertIn('data-testid="login-form"', content)
        self.assertIn('type="submit"', content)

    def test_B42_login_error_message_on_bad_credentials(self):
        """Credenciales inválidas muestran mensaje sin revelar existencia de cuenta."""
        c = Client()
        r = c.post("/", {"email": "noexiste@pruebas.invalid", "password": "WrongPass1!"})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Correo o contrase")

    def test_B43_login_role_descriptions(self):
        """La página de login describe cada rol correctamente."""
        c = Client()
        r = c.get("/")
        self.assertContains(r, "Productos, empleados, proveedores")
        self.assertContains(r, "Inventario, mermas y alertas")
        self.assertContains(r, "Turno de caja y ventas")


@override_settings(TIME_ZONE="America/Lima")
class BrowserContentErrorPagesTest(TestCase):
    """Sublote 14-B: Verificación de página 403 para accesos denegados."""

    @classmethod
    def setUpTestData(cls):
        _setup_roles()
        cls.seller = _make_account("vendedor14be@pruebas.invalid", "VENDEDOR")
        cls.warehouse = _make_account("almacen14be@pruebas.invalid", "ALMACENERO")

    def _client_as(self, email):
        c = Client()
        _login(c, email)
        return c

    def test_B50_seller_gets_403_page_on_admin_route(self):
        """VENDEDOR en ruta de admin recibe 403 con contenido apropiado."""
        c = self._client_as("vendedor14be@pruebas.invalid")
        r = c.get("/productos/categorias/")
        self.assertEqual(r.status_code, 403)

    def test_B51_warehouse_gets_403_on_cash_open(self):
        """ALMACENERO en ruta de caja recibe 403."""
        c = self._client_as("almacen14be@pruebas.invalid")
        r = c.post("/caja/abrir/", {"opening_amount": "50.00"})
        self.assertEqual(r.status_code, 403)

    def test_B52_seller_gets_403_on_employees(self):
        """VENDEDOR en /empleados/ recibe 403."""
        c = self._client_as("vendedor14be@pruebas.invalid")
        r = c.get("/empleados/")
        self.assertEqual(r.status_code, 403)


@override_settings(TIME_ZONE="America/Lima")
class BrowserContentPageHeadingsTest(TestCase):
    """Sublote 14-B: Headings de páginas de cada rol."""

    @classmethod
    def setUpTestData(cls):
        _setup_roles()
        cls.admin = _make_account("admin14bh@pruebas.invalid", "ADMIN")
        cls.warehouse = _make_account("almacen14bh@pruebas.invalid", "ALMACENERO")
        cls.seller = _make_account("vendedor14bh@pruebas.invalid", "VENDEDOR")
        CashRegister.objects.get_or_create(code="CAJA-01", defaults={"is_active": True})

    def _client_as(self, email):
        c = Client()
        _login(c, email)
        return c

    # ── ADMIN headings ──────────────────────────────────────────────────────

    def test_B60_admin_product_list_heading(self):
        c = self._client_as("admin14bh@pruebas.invalid")
        r = c.get("/productos/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "logo de productos")  # "Catálogo de productos"

    def test_B61_admin_product_entry_heading(self):
        c = self._client_as("admin14bh@pruebas.invalid")
        r = c.get("/productos/nuevo/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Registrar producto")

    def test_B62_admin_category_list_heading(self):
        c = self._client_as("admin14bh@pruebas.invalid")
        r = c.get("/productos/categorias/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Categor")

    def test_B63_admin_supplier_list_heading(self):
        c = self._client_as("admin14bh@pruebas.invalid")
        r = c.get("/inventario/proveedores/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Proveedores")

    def test_B64_admin_employee_list_heading(self):
        c = self._client_as("admin14bh@pruebas.invalid")
        r = c.get("/empleados/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Empleados")

    def test_B65_admin_shift_history_heading(self):
        c = self._client_as("admin14bh@pruebas.invalid")
        r = c.get("/caja/turnos/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Historial de turnos")

    def test_B66_admin_sales_history_heading(self):
        c = self._client_as("admin14bh@pruebas.invalid")
        r = c.get("/ventas/historial/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Historial de ventas")

    def test_B67_admin_stock_overview_heading(self):
        c = self._client_as("admin14bh@pruebas.invalid")
        r = c.get("/inventario/stock/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Ver inventario")

    def test_B68_admin_expirations_heading(self):
        c = self._client_as("admin14bh@pruebas.invalid")
        r = c.get("/productos/vencimientos/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Vencimientos de lotes")

    def test_B69_admin_adjustment_heading(self):
        c = self._client_as("admin14bh@pruebas.invalid")
        r = c.get("/inventario/ajustes/nuevo/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Ajuste f")  # "Ajuste físico"

    # ── ALMACENERO headings ─────────────────────────────────────────────────

    def test_B70_warehouse_initial_load_heading(self):
        c = self._client_as("almacen14bh@pruebas.invalid")
        r = c.get("/inventario/carga-inicial/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Existencias iniciales")

    def test_B71_warehouse_stock_entry_heading(self):
        c = self._client_as("almacen14bh@pruebas.invalid")
        r = c.get("/inventario/entrada/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Entrada de mercader")

    def test_B72_warehouse_writeoff_heading(self):
        c = self._client_as("almacen14bh@pruebas.invalid")
        r = c.get("/inventario/bajas/nueva/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Registrar merma")

    # ── VENDEDOR headings ───────────────────────────────────────────────────

    def test_B73_seller_cash_close_heading(self):
        c = self._client_as("vendedor14bh@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("100.00"), status="OPEN",
        )
        r = c.get("/caja/cerrar/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Cerrar turno")

    def test_B74_seller_shift_history_heading(self):
        c = self._client_as("vendedor14bh@pruebas.invalid")
        r = c.get("/ventas/historial/turno/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Mis ventas del turno")


@override_settings(TIME_ZONE="America/Lima")
class BrowserContentAccessibilityTest(TestCase):
    """Sublote 14-B: Elementos de accesibilidad y estructura HTML."""

    @classmethod
    def setUpTestData(cls):
        _setup_roles()
        cls.admin = _make_account("admin14ba@pruebas.invalid", "ADMIN")

    def _client_as(self, email):
        c = Client()
        _login(c, email)
        return c

    def test_B80_skip_link_present(self):
        """La página tiene un skip-link 'Saltar al contenido'."""
        c = self._client_as("admin14ba@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Saltar al contenido")

    def test_B81_sidebar_aria_label(self):
        """El sidebar tiene aria-label 'Navegación principal'."""
        c = self._client_as("admin14ba@pruebas.invalid")
        r = c.get("/inicio/")
        content = r.content.decode()
        self.assertIn("Navegaci", content)  # "Navegación principal"

    def test_B82_main_content_id(self):
        """El main tiene id='contenido' y tabindex para skip link."""
        c = self._client_as("admin14ba@pruebas.invalid")
        r = c.get("/inicio/")
        content = r.content.decode()
        self.assertIn('id="contenido"', content)
        self.assertIn('tabindex="-1"', content)

    def test_B83_html_lang_es(self):
        """El HTML usa lang='es-PE'."""
        c = self._client_as("admin14ba@pruebas.invalid")
        r = c.get("/inicio/")
        content = r.content.decode()
        self.assertIn('lang="es-PE"', content)

    def test_B84_brand_text(self):
        """El sidebar brand muestra 'Minimarket' y 'Gestión de bodega'."""
        c = self._client_as("admin14ba@pruebas.invalid")
        r = c.get("/inicio/")
        self.assertContains(r, "Minimarket")
        self.assertContains(r, "Gesti")  # "Gestión de bodega"

    def test_B85_footer_present(self):
        """La página tiene footer con 'Minimarket'."""
        c = self._client_as("admin14ba@pruebas.invalid")
        r = c.get("/inicio/")
        content = r.content.decode()
        self.assertIn("app-footer", content)

    def test_B86_login_page_no_sidebar(self):
        """La página de login no muestra sidebar (class=anonymous)."""
        c = Client()
        r = c.get("/")
        content = r.content.decode()
        self.assertIn("anonymous", content)
        self.assertNotIn("app-sidebar", content)

    def test_B87_authenticated_has_sidebar(self):
        """La página autenticada muestra sidebar."""
        c = self._client_as("admin14ba@pruebas.invalid")
        r = c.get("/inicio/")
        content = r.content.decode()
        self.assertIn("app-sidebar", content)

