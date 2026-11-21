"""Stage 07 audit tests: inventory stock overview/alerts, catalog expirations (HU-PROD-06),
dashboard summary parity, timezone boundaries, active/inactive consistency, N+1 avoidance, and POS contrast.
"""
from __future__ import annotations

import html
import uuid
from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from cash.models import CashRegister, CashShift
from catalog.models import Category, Product
from identity.models import Account, Role
from sales.services import add_product_to_draft, sellable_stock_for_product
from sales.views import _search_products

from .models import Lot, StockWriteOff, Supplier
from .services import LotInput, confirm_initial_load, register_stock_entry, write_off_stock


class Stage07StockExpirationsAuditTests(TestCase):
    password = "Test-only-Passw0rd7!"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

        cls.admin = Account.objects.create_user(
            "admin.audit07@test.invalid", cls.password, display_name="Admin Audit07", role=cls.admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "wh.audit07@test.invalid", cls.password, display_name="Lucia Almacen07", role=cls.wh_role
        )
        cls.warehouse2 = Account.objects.create_user(
            "wh2.audit07@test.invalid", cls.password, display_name="Pedro Almacen07", role=cls.wh_role
        )
        cls.seller = Account.objects.create_user(
            "seller.audit07@test.invalid", cls.password, display_name="Carmen Vendedora07", role=cls.seller_role
        )

    def _seed_complex_scenario(self) -> dict:
        today = timezone.localdate()
        cat_active = Category.objects.create(name="Lacteos Audit07", is_active=True)
        cat_off = Category.objects.create(name="Snacks Suspendidos07", is_active=False)
        sup = Supplier.objects.create(name="Proveedor Central 07 SAC", ruc="20700000001")

        # 1. Mixed product: expired (-2d, today), zero-qty lot, equal sellable == minimum_stock (RN-06), ties on +1d
        p_mix = Product.objects.create(
            category=cat_active,
            name="Leche Mezcla Audit07",
            barcode="775070000001",
            sale_price=Decimal("6.50"),
            minimum_stock=10,
        )
        t_early = timezone.now() - timedelta(hours=3)
        t_late = timezone.now() - timedelta(hours=1)
        with patch("django.utils.timezone.now", return_value=t_early):
            load_mix = confirm_initial_load(
                actor=self.warehouse,
                product=p_mix,
                supplier=sup,
                lots=[
                    LotInput("MIX-PAST-2D", 3, Decimal("2.0000"), today + timedelta(days=1)),
                    LotInput("mix-today-0d", 4, Decimal("2.1000"), today + timedelta(days=1)),
                    LotInput("MIX-ZERO-0", 5, Decimal("2.2000"), today + timedelta(days=1)),
                    LotInput("MIX-TIE-Z-FIRST", 2, Decimal("2.3000"), today + timedelta(days=1)),
                    LotInput("MIX-DAY07", 6, Decimal("2.4000"), today + timedelta(days=7)),
                ],
            )
        with patch("django.utils.timezone.now", return_value=t_late):
            lot_tie_late = Lot.objects.create(
                product=p_mix,
                initial_load=load_mix,
                supplier=sup,
                responsible=self.warehouse2,
                is_initial=False,
                number="MIX-TIE-A-SECOND",
                initial_quantity=2,
                available_quantity=2,
                unit_cost=Decimal("2.5000"),
                expiration_date=today + timedelta(days=1),
            )
        Lot.objects.filter(product=p_mix, number_normalized="MIX-PAST-2D").update(
            expiration_date=today - timedelta(days=2)
        )
        Lot.objects.filter(product=p_mix, number_normalized="MIX-TODAY-0D").update(expiration_date=today)
        Lot.objects.filter(product=p_mix, number_normalized="MIX-ZERO-0").update(available_quantity=0)

        # 2. Edge 30/31 days with GTIN barcode producing 2+ ProductBarcodeKey rows (no POS qty inflation)
        p_edge = Product.objects.create(
            category=cat_active,
            name="Yogurt GTIN 30D",
            barcode="036000291452",
            barcode_type=Product.BarcodeType.GTIN,
            sale_price=Decimal("5.00"),
            minimum_stock=3,
        )
        confirm_initial_load(
            actor=self.warehouse,
            product=p_edge,
            supplier=sup,
            lots=[
                LotInput("EDGE-D30", 4, Decimal("2.0000"), today + timedelta(days=30)),
                LotInput("EDGE-D31", 5, Decimal("2.1000"), today + timedelta(days=31)),
            ],
        )

        # 3. Only expired today (physical=8, sellable=0 -> Sin stock vendible, absent from POS)
        p_expired = Product.objects.create(
            category=cat_active,
            name="Conserva Vencida Hoy",
            barcode="775070000003",
            sale_price=Decimal("7.00"),
            minimum_stock=5,
        )
        confirm_initial_load(
            actor=self.warehouse,
            product=p_expired,
            supplier=sup,
            lots=[LotInput("ONLY-VENC-HOY", 8, Decimal("3.0000"), today + timedelta(days=1))],
        )
        Lot.objects.filter(product=p_expired).update(expiration_date=today)

        # 4. minimum_stock == 0 with 0 stock (low stock) vs valid stock > +30d (OK)
        p_zero_empty = Product.objects.create(
            category=cat_active,
            name="Avena MinCero Vacia",
            barcode="775070000004",
            sale_price=Decimal("3.00"),
            minimum_stock=0,
        )
        p_zero_ok = Product.objects.create(
            category=cat_active,
            name="Sal MinCero Sana",
            barcode="775070000005",
            sale_price=Decimal("2.00"),
            minimum_stock=0,
        )
        confirm_initial_load(
            actor=self.warehouse,
            product=p_zero_ok,
            lots=[LotInput("SAL-OK-60", 7, Decimal("1.0000"), today + timedelta(days=60))],
        )

        # 5. Inactive product with expired (-1d) and upcoming (+4d) lots
        p_inactive = Product.objects.create(
            category=cat_active,
            name="Jugo Producto Inactivo",
            barcode="775070000006",
            sale_price=Decimal("8.00"),
            minimum_stock=10,
        )
        confirm_initial_load(
            actor=self.warehouse,
            product=p_inactive,
            lots=[
                LotInput("INACT-VENC-1D", 3, Decimal("3.0000"), today + timedelta(days=1)),
                LotInput("INACT-PROX-4D", 2, Decimal("3.0000"), today + timedelta(days=4)),
            ],
        )
        Lot.objects.filter(product=p_inactive, number_normalized="INACT-VENC-1D").update(
            expiration_date=today - timedelta(days=1)
        )
        p_inactive.is_active = False
        p_inactive.save(update_fields=["is_active"])

        # 6. Active product inside inactive category (sellable=2 <= min=10; OBS-05-STOCK-CAT-INACTIVA)
        cat_tmp = Category.objects.create(name="Temporal Activa07", is_active=True)
        p_cat_off = Product.objects.create(
            category=cat_tmp,
            name="Galletas Cat Desactivada",
            barcode="775070000007",
            sale_price=Decimal("4.50"),
            minimum_stock=10,
        )
        confirm_initial_load(
            actor=self.warehouse,
            product=p_cat_off,
            lots=[LotInput("CATOFF-PROX-3D", 2, Decimal("2.0000"), today + timedelta(days=3))],
        )
        p_cat_off.category = cat_off
        p_cat_off.save(update_fields=["category"])

        return {
            "today": today,
            "p_mix": p_mix,
            "lot_tie_late": lot_tie_late,
            "p_edge": p_edge,
            "p_expired": p_expired,
            "p_zero_empty": p_zero_empty,
            "p_zero_ok": p_zero_ok,
            "p_inactive": p_inactive,
            "p_cat_off": p_cat_off,
        }

    def test_role_matrix_anonymous_and_http_contract(self) -> None:
        for url_name in ("stock-overview", "product-expirations", "dashboard"):
            url = reverse(url_name)
            resp = self.client.get(url)
            self.assertRedirects(resp, f"{reverse('login')}?next={url}", fetch_redirect_response=False)

        # VENDEDOR gets 403 on inventory/catalog consults and no summary on dashboard
        self.client.force_login(self.seller)
        self.assertEqual(self.client.get(reverse("stock-overview")).status_code, 403)
        self.assertEqual(self.client.get(reverse("product-expirations")).status_code, 403)
        self.assertEqual(self.client.get(reverse("product-list")).status_code, 403)
        dash_seller = self.client.get(reverse("dashboard"))
        self.assertEqual(dash_seller.status_code, 200)
        self.assertIsNone(dash_seller.context["summary"])
        self.assertNotContains(dash_seller, "Resumen general")

        # ADMIN & ALMACENERO access + @never_cache headers + role-specific footer actions
        for user in (self.admin, self.warehouse):
            self.client.force_login(user)
            for url_name in ("stock-overview", "product-expirations", "dashboard"):
                r = self.client.get(reverse(url_name))
                self.assertEqual(r.status_code, 200)
                cc = r.get("Cache-Control", "")
                self.assertIn("no-store", cc)
                self.assertIn("no-cache", cc)

        self.client.force_login(self.warehouse)
        wh_dash = self.client.get(reverse("dashboard"))
        self.assertIsNotNone(wh_dash.context["summary"])
        self.assertNotContains(wh_dash, "Ventas de hoy")
        wh_stock = self.client.get(reverse("stock-overview"))
        self.assertContains(wh_stock, reverse("inventory-load"))
        self.assertContains(wh_stock, reverse("stock-entry"))
        self.assertContains(wh_stock, reverse("stock-writeoff"))
        self.assertNotContains(wh_stock, reverse("physical-adjustment"))

        self.client.force_login(self.admin)
        adm_dash = self.client.get(reverse("dashboard"))
        self.assertContains(adm_dash, "Ventas de hoy")
        adm_stock = self.client.get(reverse("stock-overview"))
        self.assertContains(adm_stock, reverse("physical-adjustment"))
        self.assertContains(adm_stock, reverse("stock-writeoff"))
        self.assertNotContains(adm_stock, reverse("inventory-load"))

        # Strict POST -> 405 Method Not Allowed with valid CSRF
        csrf_client = Client(enforce_csrf_checks=True)
        token = csrf_client.get(reverse("login")).cookies["csrftoken"].value
        csrf_client.force_login(self.admin)
        token = csrf_client.get(reverse("logout")).cookies.get("csrftoken", None)
        token = token.value if token else csrf_client.cookies["csrftoken"].value
        for url_name in ("stock-overview", "product-expirations"):
            post_resp = csrf_client.post(
                reverse(url_name),
                {"csrfmiddlewaretoken": token, "dias": "7"},
            )
            self.assertEqual(post_resp.status_code, 405)

    def test_exact_date_boundaries_zero_lots_and_deterministic_ordering(self) -> None:
        # Clean DB initially -> green empty states
        self.client.force_login(self.warehouse)
        empty_stock = self.client.get(reverse("stock-overview"))
        self.assertContains(empty_stock, "Sin alertas de stock bajo ni de vencimiento.")
        empty_exp = self.client.get(reverse("product-expirations"))
        self.assertContains(empty_exp, "No hay lotes con unidades disponibles que estén vencidos o venzan en los próximos 30 días.")

        data = self._seed_complex_scenario()
        exp_resp = self.client.get(reverse("product-expirations"))
        self.assertEqual(exp_resp.status_code, 200)
        lots = list(exp_resp.context["lots"])
        lot_numbers = [l.number_normalized for l in lots]

        # Zero-quantity lot, +31d lot, +60d lot must NOT appear; expired + <=30d DO appear in deterministic order:
        # -2d: MIX-PAST-2D; -1d: INACT-VENC-1D; 0d (Conserva < Leche): ONLY-VENC-HOY, MIX-TODAY-0D;
        # +1d (Leche ties by received_at, id!): MIX-TIE-Z-FIRST before MIX-TIE-A-SECOND;
        # +3d: CATOFF-PROX-3D; +4d: INACT-PROX-4D; +7d: MIX-DAY07; +30d: EDGE-D30
        self.assertEqual(
            lot_numbers,
            [
                "MIX-PAST-2D",
                "INACT-VENC-1D",
                "ONLY-VENC-HOY",
                "MIX-TODAY-0D",
                "MIX-TIE-Z-FIRST",
                "MIX-TIE-A-SECOND",
                "CATOFF-PROX-3D",
                "INACT-PROX-4D",
                "MIX-DAY07",
                "EDGE-D30",
            ],
        )
        self.assertNotIn("MIX-ZERO-0", lot_numbers)
        self.assertNotIn("EDGE-D31", lot_numbers)
        self.assertNotIn("SAL-OK-60", lot_numbers)
        self.assertEqual(exp_resp.context["expired_count"], 4)
        self.assertEqual(exp_resp.context["upcoming_count"], 6)

        # Delta strings + blocked label + inactive badges + direct writeoff link only on expired lots
        self.assertContains(exp_resp, "Venció hace 2 días")
        self.assertContains(exp_resp, "Venció ayer (hace 1 día)")
        self.assertContains(exp_resp, "Vence hoy")
        self.assertContains(exp_resp, "En 1 día")
        self.assertContains(exp_resp, "En 30 días")
        self.assertContains(exp_resp, "Bloqueado para venta", count=4)
        self.assertContains(exp_resp, "Producto inactivo", count=2)
        self.assertContains(exp_resp, "Categoría desactivada", count=1)

        expired_pks = [str(l.pk) for l in lots if l.days_remaining <= 0]
        upcoming_pks = [str(l.pk) for l in lots if l.days_remaining > 0]
        for pk in expired_pks:
            self.assertContains(exp_resp, f"{reverse('stock-writeoff')}?lote={pk}")
        for pk in upcoming_pks:
            self.assertNotContains(exp_resp, f"{reverse('stock-writeoff')}?lote={pk}")

        # stock_overview alerts share identical normalized uppercase numbers and deterministic order
        stock_resp = self.client.get(reverse("stock-overview"))
        so_expired = [l.number_normalized for l in stock_resp.context["expired_lots"]]
        so_expiring = [l.number_normalized for l in stock_resp.context["expiring_lots"]]
        self.assertEqual(so_expired, ["MIX-PAST-2D", "INACT-VENC-1D", "ONLY-VENC-HOY", "MIX-TODAY-0D"])
        self.assertEqual(
            so_expiring,
            ["MIX-TIE-Z-FIRST", "MIX-TIE-A-SECOND", "CATOFF-PROX-3D", "INACT-PROX-4D", "MIX-DAY07", "EDGE-D30"],
        )
        # Normalized uppercase MIX-TODAY-0D shown instead of raw "mix-today-0d"
        self.assertContains(stock_resp, "Lote MIX-TODAY-0D")
        self.assertNotContains(stock_resp, "mix-today-0d")
        self.assertGreater(data["lot_tie_late"].received_at, Lot.objects.get(number_normalized="MIX-TIE-Z-FIRST").received_at)

    def test_dias_filter_boundaries_and_strict_ascii_validation(self) -> None:
        self._seed_complex_scenario()
        self.client.force_login(self.warehouse)

        valid_cases = [
            ("", 30, 10),
            ("1", 1, 6),     # 4 expired + 2 ties (+1d)
            ("7", 7, 9),     # +7d MIX-DAY07 included, +30d excluded
            ("29", 29, 9),   # +30d EDGE-D30 excluded
            ("30", 30, 10),  # +30d EDGE-D30 included
            ("31", 31, 11),  # +31d EDGE-D31 included
            ("3650", 3650, 12),  # +60d SAL-OK-60 included
        ]
        for raw, exp_days, exp_count in valid_cases:
            with self.subTest(valid_dias=raw):
                resp = self.client.get(reverse("product-expirations"), {"dias": raw})
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(resp.context["days"], exp_days)
                self.assertEqual(len(resp.context["lots"]), exp_count)
                self.assertEqual(list(resp.context["messages"]), [])

        range_invalid = ("0", "-5", "3651", "999999999")
        for raw in range_invalid:
            with self.subTest(range_invalid=raw):
                resp = self.client.get(reverse("product-expirations"), {"dias": raw})
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(resp.context["days"], 30)
                self.assertEqual(len(resp.context["lots"]), 10)
                self.assertContains(resp, "entre 1 y 3650. Se muestran 30 días por defecto.")

        format_invalid = ("abc", "7.5", "+7", "٥", "1\x00", "٥٥")
        for raw in format_invalid:
            with self.subTest(format_invalid=raw):
                resp = self.client.get(reverse("product-expirations"), {"dias": raw})
                self.assertEqual(resp.status_code, 200)
                self.assertEqual(resp.context["days"], 30)
                self.assertEqual(len(resp.context["lots"]), 10)
                self.assertContains(resp, "Ingrese un número entero válido de días. Se muestran 30 días por defecto.")

    def test_active_inactive_parity_and_rn06_across_dashboard_stock_catalog_and_pos(self) -> None:
        data = self._seed_complex_scenario()
        self.client.force_login(self.admin)

        dash = self.client.get(reverse("dashboard"))
        stock = self.client.get(reverse("stock-overview"))
        cat_list = self.client.get(reverse("product-list"))
        exp = self.client.get(reverse("product-expirations"))

        summary = dash.context["summary"]
        low_names = {p.name for p in stock.context["low_stock"]}

        # OBS-05-RESUMEN-MINIMO & OBS-05-STOCK-CAT-INACTIVA parity:
        # Exactly 3 active low-stock products: p_mix (10 == 10), p_expired (0 <= 5), p_zero_empty (0 == 0).
        # Inactive product & inactive-category product MUST be excluded from low_stock on BOTH dashboard and stock_overview!
        self.assertEqual(
            low_names,
            {"Leche Mezcla Audit07", "Conserva Vencida Hoy", "Avena MinCero Vacia"},
        )
        self.assertEqual(summary["low_stock"], len(stock.context["low_stock"]))
        self.assertEqual(summary["low_stock"], 3)
        self.assertEqual(summary["expiring"], stock.context["expiring_lots"].count())
        self.assertEqual(summary["expiring"], exp.context["upcoming_count"])
        self.assertEqual(summary["expired"], stock.context["expired_lots"].count())
        self.assertEqual(summary["expired"], exp.context["expired_count"])

        # Inactive banners show explicit status suffix and stock_overview does not highlight inactive/suspended products as red alerts
        html_stock = stock.content.decode("utf-8")
        unescaped_stock = html.unescape(html_stock)
        self.assertIn("<strong>Jugo Producto Inactivo</strong> (Inactivo)", unescaped_stock)
        self.assertIn("<strong>Galletas Cat Desactivada</strong> (Categoría desactivada)", unescaped_stock)
        # Extract row for Galletas Cat Desactivada -> ensure red #c0392b span is NOT applied on qty 2
        row_cat_off = unescaped_stock.split("Galletas Cat Desactivada")[2].split("</tr>")[0]
        self.assertNotIn("#c0392b", row_cat_off)
        self.assertIn("Categoría desactivada", row_cat_off)

        # Catalog list contract stays intact (including Categoría desactivada & Sin stock vigente)
        self.assertContains(cat_list, "Categoría desactivada")
        self.assertContains(cat_list, "Sin stock vigente")

        # POS search parity: excludes expired-only, inactive product, inactive category,
        # and computes exact sellable stock on multi-key GTIN + multi-lot without inflation!
        p_edge = data["p_edge"]
        self.assertGreaterEqual(p_edge.barcode_keys.count(), 2)
        gtin_results = list(_search_products("036000291452"))
        self.assertEqual(len(gtin_results), 1)
        self.assertEqual(gtin_results[0].sellable_quantity, 9)  # 4 (D30) + 5 (D31), NOT 9 * 3 keys!

        mix_results = list(_search_products("Leche Mezcla Audit07"))
        self.assertEqual(len(mix_results), 1)
        self.assertEqual(mix_results[0].sellable_quantity, 10)  # excludes 3(-2d) + 4(0d) + 0-lot = 17 physical -> 10 sellable
        self.assertEqual(data["p_mix"].physical_stock, 17)
        self.assertEqual(data["p_mix"].sellable_stock, 10)
        self.assertEqual(sellable_stock_for_product(data["p_mix"]), 10)

        for blocked_query in ("Conserva Vencida Hoy", "Jugo Producto Inactivo", "Galletas Cat Desactivada"):
            self.assertEqual(list(_search_products(blocked_query)), [])

    def test_lima_utc_midnight_transition_synchronized_across_all_views(self) -> None:
        cat = Category.objects.create(name="Lacteos TZ07")
        prod = Product.objects.create(
            category=cat,
            name="Yogurt Medianoche Lima",
            barcode="775070009001",
            sale_price=Decimal("4.50"),
            minimum_stock=2,
        )
        reg = CashRegister.objects.create(code="CAJA-TZ07")
        CashShift.objects.create(cash_register=reg, seller=self.seller, opening_amount=Decimal("50.00"))
        lot_exp_date = date(2026, 11, 12)

        before_midnight = datetime(2026, 11, 12, 4, 59, 59, tzinfo=dt_timezone.utc)  # 2026-11-11 23:59:59 America/Lima
        at_midnight = datetime(2026, 11, 12, 5, 0, 0, tzinfo=dt_timezone.utc)       # 2026-11-12 00:00:00 America/Lima

        with patch("django.utils.timezone.now", return_value=before_midnight):
            confirm_initial_load(
                actor=self.warehouse,
                product=prod,
                lots=[LotInput("L-TZ-12NOV", 5, Decimal("2.0000"), lot_exp_date)],
            )
            self.assertEqual(timezone.localdate(), date(2026, 11, 11))
            self.assertEqual(prod.physical_stock, 5)
            self.assertEqual(prod.sellable_stock, 5)
            self.assertTrue(prod.is_sellable)
            self.assertEqual(sellable_stock_for_product(prod), 5)
            self.assertEqual(list(_search_products("Yogurt Medianoche"))[0].sellable_quantity, 5)

            self.client.force_login(self.admin)
            dash_before = self.client.get(reverse("dashboard")).context["summary"]
            exp_before = self.client.get(reverse("product-expirations"), {"dias": "1"})
            self.assertEqual((dash_before["expired"], dash_before["expiring"], dash_before["low_stock"]), (0, 1, 0))
            self.assertContains(exp_before, "Próximo")
            self.assertContains(exp_before, "En 1 día")

        with patch("django.utils.timezone.now", return_value=at_midnight):
            self.assertEqual(timezone.localdate(), date(2026, 11, 12))
            self.assertEqual(prod.physical_stock, 5)
            self.assertEqual(prod.sellable_stock, 0)
            self.assertFalse(prod.is_sellable)
            self.assertEqual(sellable_stock_for_product(prod), 0)
            self.assertEqual(list(_search_products("Yogurt Medianoche")), [])
            with self.assertRaises(ValidationError):
                add_product_to_draft(actor=self.seller, product_id=prod.pk, quantity=1)

            self.client.force_login(self.admin)
            dash_after = self.client.get(reverse("dashboard")).context["summary"]
            stock_after = self.client.get(reverse("stock-overview"))
            exp_after = self.client.get(reverse("product-expirations"), {"dias": "1"})
            self.assertEqual((dash_after["expired"], dash_after["expiring"], dash_after["low_stock"]), (1, 0, 1))
            self.assertContains(stock_after, "Sin stock vendible")
            self.assertContains(stock_after, "Lote L-TZ-12NOV")
            self.assertContains(exp_after, "Vencido")
            self.assertContains(exp_after, "Vence hoy")
            self.assertContains(exp_after, "Bloqueado para venta")

    def test_stock_overview_and_dashboard_avoid_n_plus_one_lot_queries(self) -> None:
        cat = Category.objects.create(name="Abarrotes Perf07")
        # Unsaved Product model safety guard (pk is None) -> 0 queries
        unsaved = Product(category=cat, name="No guardado", barcode="775070099900", sale_price=Decimal("1.00"))
        with self.assertNumQueries(0):
            self.assertEqual(unsaved.physical_stock, 0)
            self.assertEqual(unsaved.sellable_stock, 0)

        today = timezone.localdate()
        self.client.force_login(self.admin)

        def create_n_products(start_idx: int, count: int) -> None:
            for i in range(start_idx, start_idx + count):
                p = Product.objects.create(
                    category=cat,
                    name=f"Producto Perf {i:03d}",
                    barcode=f"77507088{i:04d}",
                    sale_price=Decimal("4.00"),
                    minimum_stock=5,
                )
                confirm_initial_load(
                    actor=self.warehouse,
                    product=p,
                    lots=[
                        LotInput(f"P{i}-A", 3, Decimal("1.5000"), today + timedelta(days=5)),
                        LotInput(f"P{i}-B", 4, Decimal("1.6000"), today + timedelta(days=15)),
                    ],
                )
                Lot.objects.filter(product=p, number_normalized=f"P{i}-A").update(
                    expiration_date=today - timedelta(days=1)
                )

        create_n_products(1, 2)
        with CaptureQueriesContext(connection) as q_small_stock:
            self.assertEqual(self.client.get(reverse("stock-overview")).status_code, 200)
        with CaptureQueriesContext(connection) as q_small_dash:
            self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

        create_n_products(3, 12)
        with CaptureQueriesContext(connection) as q_large_stock:
            self.assertEqual(self.client.get(reverse("stock-overview")).status_code, 200)
        with CaptureQueriesContext(connection) as q_large_dash:
            self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)

        # Adding 12 products (+24 lots) MUST NOT increase query counts on stock_overview or dashboard
        self.assertEqual(len(q_small_stock), len(q_large_stock))
        self.assertEqual(len(q_small_dash), len(q_large_dash))

    def test_expirations_writeoff_cross_role_lifecycle(self) -> None:
        data = self._seed_complex_scenario()
        expired_lot = Lot.objects.get(product=data["p_expired"])
        self.client.force_login(self.warehouse)

        exp_before = self.client.get(reverse("product-expirations"))
        writeoff_href = f"{reverse('stock-writeoff')}?lote={expired_lot.pk}"
        self.assertContains(exp_before, writeoff_href)

        # Warehouse writes off all 8 expired units via targeted ?lote= link
        post_resp = self.client.post(
            writeoff_href,
            {
                "lot_id": str(expired_lot.pk),
                "quantity": "8",
                "reason": StockWriteOff.Reason.EXPIRATION,
                "notes": "Retiro de conserva vencida hoy",
                "idempotency_key": str(uuid.uuid4()),
            },
        )
        self.assertRedirects(post_resp, reverse("stock-writeoff-receipt", args=(StockWriteOff.objects.get(lot=expired_lot).pk,)))

        exp_after = self.client.get(reverse("product-expirations"))
        stock_after = self.client.get(reverse("stock-overview"))
        self.assertEqual(exp_after.context["expired_count"], 3)
        self.assertNotContains(exp_after, "ONLY-VENC-HOY")
        self.assertNotContains(stock_after, "Lote ONLY-VENC-HOY")

        self.client.force_login(self.admin)
        dash_after = self.client.get(reverse("dashboard"))
        self.assertEqual(dash_after.context["summary"]["expired"], 3)
        self.assertEqual(dash_after.context["summary"]["low_stock"], 3)

        # Stocking an active replacement lot lifts low_stock when sellable > minimum_stock
        register_stock_entry(
            actor=self.warehouse,
            product=data["p_expired"],
            lots=[LotInput("REP-CONSERVA-01", 10, Decimal("3.2000"), data["today"] + timedelta(days=90))],
        )
        dash_restocked = self.client.get(reverse("dashboard"))
        self.assertEqual(dash_restocked.context["summary"]["low_stock"], 2)
