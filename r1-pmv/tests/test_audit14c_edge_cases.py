"""
ETAPA 14-C — Auditoría comportamiento→planificación y edge cases
================================================================
Tests adicionales para completar la auditoría de integración:
  - PROP-14-03: admin desactiva producto mientras vendedor tiene borrador activo
  - Comportamiento→planificación: funciones implementadas vs HUs documentadas
  - Edge cases: descartar borrador, precio cambiado, búsqueda de producto,
    caja ya abierta, stock insuficiente en checkout, constancia de venta

Fecha: 13/11/2026  |  Base: SQLite aislada (TestCase)
Pasada: Primera  |  Alcance: cross-module behavior verification
"""
from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from django.urls import reverse
from django.test import TestCase, Client, override_settings
from django.utils import timezone

from identity.models import Account, Role
from catalog.models import Category, Product
from inventory.models import InitialInventoryLoad, Lot, Supplier
from cash.models import CashRegister, CashShift, CashShiftClose
from sales.models import Sale, SaleDraft, SaleDraftLine, SaleCounter, SaleLine


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


def _create_product_with_stock(warehouse, *, name, barcode, sale_price, stock=20, days=60):
    cat = Category.objects.create(name=f"Cat-{barcode}", is_active=True)
    prod = Product.objects.create(
        name=name, barcode=barcode, barcode_type="INTERNAL",
        barcode_normalized=barcode, search_name=name.lower(),
        category=cat, unit="UND", sale_price=Decimal(str(sale_price)),
        minimum_stock=2, controls_expiration=True,
        average_cost=Decimal("3.0000"),
    )
    load = InitialInventoryLoad.objects.create(product=prod, responsible=warehouse)
    Lot.objects.create(
        product=prod, initial_load=load, number=f"LOTE-{barcode}",
        number_normalized=f"LOTE-{barcode}", initial_quantity=stock,
        available_quantity=stock, unit_cost=Decimal("3.0000"),
        expiration_date=date.today() + timedelta(days=days),
    )
    return prod, cat


@override_settings(TIME_ZONE="America/Lima")
class PROP14_03_AdminDeactivatesProductWithDraftTest(TestCase):
    """PROP-14-03: Admin desactiva producto mientras vendedor tiene borrador activo."""

    @classmethod
    def setUpTestData(cls):
        _setup_roles()
        cls.admin = _make_account("admin14c@pruebas.invalid", "ADMIN")
        cls.warehouse = _make_account("almacen14c@pruebas.invalid", "ALMACENERO")
        cls.seller = _make_account("vendedor14c@pruebas.invalid", "VENDEDOR")
        CashRegister.objects.get_or_create(code="CAJA-01", defaults={"is_active": True})

    def _client_as(self, email):
        c = Client()
        _login(c, email)
        return c

    def test_C01_checkout_fails_after_product_deactivation(self):
        """Vendedor agrega producto al borrador. Admin lo desactiva. El cobro debe fallar."""
        prod, cat = _create_product_with_stock(
            self.warehouse, name="Queso14C", barcode="INT-C01-QUESO",
            sale_price="8.50", stock=10,
        )
        seller_c = self._client_as("vendedor14c@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("100.00"), status="OPEN",
        )

        # Seller adds product to draft
        seller_c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "2"})
        draft = SaleDraft.objects.filter(seller=self.seller, status="ACTIVE").first()
        self.assertIsNotNone(draft, "Debe existir borrador activo")
        self.assertEqual(draft.lines.count(), 1)

        # Admin deactivates the product
        admin_c = self._client_as("admin14c@pruebas.invalid")
        prod.is_active = False
        prod.save(update_fields=["is_active"])

        # Seller tries to checkout — should fail because product is now inactive
        from sales.services import draft_totals, draft_signature
        totals = draft_totals(draft)
        sig = draft_signature(draft.pk, draft.lines.all())
        r = seller_c.post("/ventas/cobrar/", {
            "cash_received": "20.00",
            "idempotency_key": str(uuid.uuid4()),
            "expected_subtotal": str(totals.total),
            "draft_signature": sig,
        })
        # Should NOT create a sale
        self.assertFalse(
            Sale.objects.filter(seller=self.seller, draft=draft).exists(),
            "La venta NO debe crearse con producto desactivado"
        )

    def test_C02_checkout_fails_after_category_deactivation(self):
        """Admin desactiva la categoría del producto en el borrador. Cobro rechazado."""
        prod, cat = _create_product_with_stock(
            self.warehouse, name="Leche14C", barcode="INT-C02-LECHE",
            sale_price="6.00", stock=10,
        )
        seller_c = self._client_as("vendedor14c@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("100.00"), status="OPEN",
        )

        seller_c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "1"})
        draft = SaleDraft.objects.filter(seller=self.seller, status="ACTIVE").first()
        self.assertIsNotNone(draft)

        # Admin deactivates category
        cat.is_active = False
        cat.save(update_fields=["is_active"])

        from sales.services import draft_totals, draft_signature
        totals = draft_totals(draft)
        sig = draft_signature(draft.pk, draft.lines.all())
        r = seller_c.post("/ventas/cobrar/", {
            "cash_received": "10.00",
            "idempotency_key": str(uuid.uuid4()),
            "expected_subtotal": str(totals.total),
            "draft_signature": sig,
        })
        self.assertFalse(
            Sale.objects.filter(seller=self.seller, draft=draft).exists(),
            "La venta NO debe crearse con categoría desactivada"
        )


@override_settings(TIME_ZONE="America/Lima")
class BehaviorToPlanningTest(TestCase):
    """Auditoría comportamiento→planificación: funciones implementadas vs HUs."""

    @classmethod
    def setUpTestData(cls):
        _setup_roles()
        cls.admin = _make_account("admin14cb@pruebas.invalid", "ADMIN")
        cls.warehouse = _make_account("almacen14cb@pruebas.invalid", "ALMACENERO")
        cls.seller = _make_account("vendedor14cb@pruebas.invalid", "VENDEDOR")
        CashRegister.objects.get_or_create(code="CAJA-01", defaults={"is_active": True})

    def _client_as(self, email):
        c = Client()
        _login(c, email)
        return c

    # ── Búsqueda de productos (comportamiento presente, HU respaldada) ──────

    def test_C10_search_products_active_only(self):
        """La búsqueda solo retorna productos activos con categoría activa."""
        prod, _ = _create_product_with_stock(
            self.warehouse, name="BuscaActivo14C", barcode="INT-C10-BA",
            sale_price="5.00", stock=10,
        )
        inactive_cat = Category.objects.create(name="CatInact14C", is_active=False)
        Product.objects.create(
            name="BuscaInactCat14C", barcode="INT-C10-BIC", barcode_type="INTERNAL",
            barcode_normalized="INT-C10-BIC", search_name="buscainactcat14c",
            category=inactive_cat, unit="UND", sale_price=Decimal("5.00"),
            minimum_stock=1, controls_expiration=True, is_active=True,
        )
        seller_c = self._client_as("vendedor14cb@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("50.00"), status="OPEN",
        )
        r = seller_c.get("/ventas/", {"query": "busca"})
        self.assertEqual(r.status_code, 200)
        content = r.content.decode()
        self.assertIn("BuscaActivo14C", content, "Producto activo debe aparecer")
        self.assertNotIn("BuscaInactCat14C", content, "Producto con cat inactiva NO aparece")

    def test_C11_search_products_expired_lots_hidden(self):
        """La búsqueda no muestra productos cuyo único lote está vencido."""
        cat = Category.objects.create(name="CatExp14C", is_active=True)
        prod_exp = Product.objects.create(
            name="SoloVencido14C", barcode="INT-C11-VE", barcode_type="INTERNAL",
            barcode_normalized="INT-C11-VE", search_name="solovencido14c",
            category=cat, unit="UND", sale_price=Decimal("5.00"),
            minimum_stock=1, controls_expiration=True, average_cost=Decimal("2.00"),
        )
        load = InitialInventoryLoad.objects.create(product=prod_exp, responsible=self.warehouse)
        Lot.objects.create(
            product=prod_exp, initial_load=load, number="LOTE-C11-VE",
            number_normalized="LOTE-C11-VE", initial_quantity=10,
            available_quantity=10, unit_cost=Decimal("2.00"),
            expiration_date=date.today() - timedelta(days=1),
        )
        seller_c = self._client_as("vendedor14cb@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("50.00"), status="OPEN",
        )
        r = seller_c.get("/ventas/", {"query": "solovencido"})
        self.assertEqual(r.status_code, 200)
        self.assertNotContains(r, "SoloVencido14C")

    # ── Descartar borrador (comportamiento implementado) ────────────────────

    def test_C12_discard_draft(self):
        """El vendedor puede descartar un borrador activo sin afectar stock."""
        prod, _ = _create_product_with_stock(
            self.warehouse, name="Descartable14C", barcode="INT-C12-DES",
            sale_price="5.00", stock=10,
        )
        seller_c = self._client_as("vendedor14cb@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("50.00"), status="OPEN",
        )
        seller_c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "3"})
        draft = SaleDraft.objects.filter(seller=self.seller, status="ACTIVE").first()
        self.assertIsNotNone(draft)

        # Discard
        seller_c.post("/ventas/descartar/")
        draft.refresh_from_db()
        self.assertEqual(draft.status, "DISCARDED", "El borrador debe estar descartado")
        # Stock unchanged
        lot = Lot.objects.get(number_normalized="LOTE-INT-C12-DES")
        self.assertEqual(lot.available_quantity, 10, "Stock no debe cambiar al descartar")

    # ── Constancia de venta por rol ─────────────────────────────────────────

    def test_C13_seller_sees_own_receipt(self):
        """El vendedor ve la constancia de su propia venta."""
        prod, _ = _create_product_with_stock(
            self.warehouse, name="Constancia14C", barcode="INT-C13-CON",
            sale_price="10.00", stock=10,
        )
        seller_c = self._client_as("vendedor14cb@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("100.00"), status="OPEN",
        )
        seller_c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "1"})
        draft = SaleDraft.objects.filter(seller=self.seller, status="ACTIVE").first()
        from sales.services import draft_totals, draft_signature
        totals = draft_totals(draft)
        sig = draft_signature(draft.pk, draft.lines.all())
        seller_c.post("/ventas/cobrar/", {
            "cash_received": "20.00",
            "idempotency_key": str(uuid.uuid4()),
            "expected_subtotal": str(totals.total),
            "draft_signature": sig,
        })
        sale = Sale.objects.filter(seller=self.seller).order_by("-pk").first()
        self.assertIsNotNone(sale)

        # Seller can see receipt
        r = seller_c.get(f"/ventas/constancia/{sale.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Constancia de venta")

    def test_C14_admin_sees_any_receipt(self):
        """El admin ve la constancia de cualquier venta."""
        prod, _ = _create_product_with_stock(
            self.warehouse, name="ConstAdmin14C", barcode="INT-C14-CA",
            sale_price="10.00", stock=10,
        )
        seller_c = self._client_as("vendedor14cb@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("100.00"), status="OPEN",
        )
        seller_c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "1"})
        draft = SaleDraft.objects.filter(seller=self.seller, status="ACTIVE").first()
        from sales.services import draft_totals, draft_signature
        totals = draft_totals(draft)
        sig = draft_signature(draft.pk, draft.lines.all())
        seller_c.post("/ventas/cobrar/", {
            "cash_received": "20.00",
            "idempotency_key": str(uuid.uuid4()),
            "expected_subtotal": str(totals.total),
            "draft_signature": sig,
        })
        sale = Sale.objects.filter(seller=self.seller).order_by("-pk").first()

        # Admin sees receipt
        admin_c = self._client_as("admin14cb@pruebas.invalid")
        r = admin_c.get(f"/ventas/constancia/{sale.pk}/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Constancia de venta")

    # ── Cierre de caja calcula diferencia ───────────────────────────────────

    def test_C15_cash_close_calculates_difference(self):
        """Al cerrar caja, expected = opening + ventas; difference = counted - expected."""
        prod, _ = _create_product_with_stock(
            self.warehouse, name="CierreCalc14C", barcode="INT-C15-CC",
            sale_price="15.00", stock=10,
        )
        seller_c = self._client_as("vendedor14cb@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        shift = CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("50.00"), status="OPEN",
        )
        # Sell one unit = 15.00
        seller_c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "1"})
        draft = SaleDraft.objects.filter(seller=self.seller, status="ACTIVE").first()
        from sales.services import draft_totals, draft_signature
        totals = draft_totals(draft)
        sig = draft_signature(draft.pk, draft.lines.all())
        seller_c.post("/ventas/cobrar/", {
            "cash_received": "20.00",
            "idempotency_key": str(uuid.uuid4()),
            "expected_subtotal": str(totals.total),
            "draft_signature": sig,
        })

        # Close with counted = 64.00 (expected = 50 + 15 = 65 → diff = -1.00)
        seller_c.post("/caja/cerrar/", {"counted_amount": "64.00"})
        shift.refresh_from_db()
        self.assertEqual(shift.status, "CLOSED")
        close = CashShiftClose.objects.get(cash_shift=shift)
        self.assertEqual(close.expected_amount, Decimal("65.00"))
        self.assertEqual(close.counted_amount, Decimal("64.00"))
        self.assertEqual(close.difference, Decimal("-1.00"))

    # ── Correlativo de venta secuencial ─────────────────────────────────────

    def test_C16_sale_correlative_sequential(self):
        """Las ventas reciben correlativos secuenciales V-00000001, V-00000002..."""
        prod, _ = _create_product_with_stock(
            self.warehouse, name="Correl14C", barcode="INT-C16-COR",
            sale_price="5.00", stock=20,
        )
        seller_c = self._client_as("vendedor14cb@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("100.00"), status="OPEN",
        )

        # Ensure counter is at a known starting point for this test
        counter, _ = SaleCounter.objects.get_or_create(id=1, defaults={"next_value": 1})
        start_value = counter.next_value

        for expected in range(start_value, start_value + 2):
            seller_c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "1"})
            draft = SaleDraft.objects.get(seller=self.seller, status="ACTIVE")
            from sales.services import draft_totals, draft_signature
            key = uuid.uuid4()
            response = seller_c.post("/ventas/cobrar/", {
                "cash_received": "10.00",
                "idempotency_key": str(key),
                "expected_subtotal": str(draft_totals(draft).total),
                "draft_signature": draft_signature(draft.pk, draft.lines.all()),
            })
            sale = Sale.objects.get(seller=self.seller, idempotency_key=key)
            self.assertRedirects(response, reverse("sales-receipt", args=(sale.pk,)))
            self.assertEqual(sale.correlative, f"V-{expected:08d}")
        counter.refresh_from_db()
        self.assertEqual(counter.next_value, start_value + 2)

    # ── SaleLine snapshot de producto ───────────────────────────────────────

    def test_C17_sale_line_has_product_snapshot(self):
        """La línea de venta guarda snapshot del nombre y código del producto."""
        prod, _ = _create_product_with_stock(
            self.warehouse, name="Snapshot14C", barcode="INT-C17-SNP",
            sale_price="7.00", stock=10,
        )
        seller_c = self._client_as("vendedor14cb@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("100.00"), status="OPEN",
        )
        seller_c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "2"})
        draft = SaleDraft.objects.filter(seller=self.seller, status="ACTIVE").first()
        from sales.services import draft_totals, draft_signature
        totals = draft_totals(draft)
        sig = draft_signature(draft.pk, draft.lines.all())
        seller_c.post("/ventas/cobrar/", {
            "cash_received": "20.00",
            "idempotency_key": str(uuid.uuid4()),
            "expected_subtotal": str(totals.total),
            "draft_signature": sig,
        })
        sale = Sale.objects.filter(seller=self.seller).order_by("-pk").first()
        line = SaleLine.objects.filter(sale=sale).first()
        self.assertIsNotNone(line)
        self.assertEqual(line.product_snapshot_name, "Snapshot14C")
        self.assertEqual(line.product_snapshot_barcode, "INT-C17-SNP")
        self.assertEqual(line.unit_cost, Decimal("3.0000"), "unit_cost snapshot del costo promedio")
        self.assertEqual(line.amount, Decimal("14.00"), "amount = 7.00 * 2")

    # ── Turno ya abierto — no puede abrir otro ─────────────────────────────

    def test_C18_cannot_open_second_shift(self):
        """Un segundo vendedor no puede abrir turno si ya hay uno abierto."""
        seller2 = _make_account("vendedor2.14cb@pruebas.invalid", "VENDEDOR")
        seller_c = self._client_as("vendedor14cb@pruebas.invalid")
        CashShift.objects.filter(status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("50.00"), status="OPEN",
        )
        seller2_c = self._client_as("vendedor2.14cb@pruebas.invalid")
        count_before = CashShift.objects.filter(status="OPEN").count()
        r = seller2_c.post("/caja/abrir/", {"opening_amount": "100.00"})
        # Should not create a second open shift
        self.assertEqual(
            CashShift.objects.filter(status="OPEN").count(), count_before,
            "No debe permitir abrir un segundo turno"
        )

    # ── IGV calculado correctamente ─────────────────────────────────────────

    def test_C19_igv_calculation(self):
        """La venta calcula base e IGV correctamente (factor 1.18)."""
        prod, _ = _create_product_with_stock(
            self.warehouse, name="IGV14C", barcode="INT-C19-IGV",
            sale_price="11.80", stock=10,
        )
        seller_c = self._client_as("vendedor14cb@pruebas.invalid")
        CashShift.objects.filter(seller=self.seller, status="OPEN").delete()
        reg = CashRegister.objects.get(code="CAJA-01")
        CashShift.objects.create(
            cash_register=reg, seller=self.seller,
            opening_amount=Decimal("100.00"), status="OPEN",
        )
        seller_c.post("/ventas/", {"product_id": str(prod.pk), "quantity": "1"})
        draft = SaleDraft.objects.filter(seller=self.seller, status="ACTIVE").first()
        from sales.services import draft_totals, draft_signature
        totals = draft_totals(draft)
        sig = draft_signature(draft.pk, draft.lines.all())
        seller_c.post("/ventas/cobrar/", {
            "cash_received": "20.00",
            "idempotency_key": str(uuid.uuid4()),
            "expected_subtotal": str(totals.total),
            "draft_signature": sig,
        })
        sale = Sale.objects.filter(seller=self.seller).order_by("-pk").first()
        self.assertIsNotNone(sale)
        self.assertEqual(sale.total_amount, Decimal("11.80"))
        # base = 11.80 / 1.18 = 10.00
        self.assertEqual(sale.base_amount, Decimal("10.00"))
        self.assertEqual(sale.igv_amount, Decimal("1.80"))

