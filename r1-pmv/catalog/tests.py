from __future__ import annotations

from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from identity.models import Account, Role

from .models import Category, Product


class CategoryTests(TestCase):
    def test_name_normalization_is_persisted(self) -> None:
        category = Category.objects.create(name=" Productos Enlatados ")
        self.assertEqual(category.name_normalized, "productos enlatados")


class ProductRegistrationTests(TestCase):
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
        cls.category = Category.objects.create(name="Productos enlatados")

    def payload(self, **overrides):
        data = {
            "name": "Atún en agua 170 g",
            "barcode": "7751234567890", "barcode_type": "INTERNAL",
            "category": str(self.category.pk),
            "unit": Product.Unit.UNIT,
            "sale_price": "8.90",
            "minimum_stock": "12",
        }
        data.update(overrides)
        return data

    def test_admin_registers_zero_stock_non_sellable_product(self) -> None:
        self.client.force_login(self.admin)

        response = self.client.post(reverse("product-entry"), self.payload())

        product = Product.objects.get()
        self.assertRedirects(response, reverse("product-created", args=(product.pk,)))
        self.assertEqual(product.category, self.category)
        self.assertEqual(product.unit, Product.Unit.UNIT)
        self.assertEqual(product.sale_price, Decimal("8.90"))
        self.assertEqual(product.minimum_stock, 12)
        self.assertTrue(product.controls_expiration)
        self.assertEqual(product.average_cost, Decimal("0.0000"))
        self.assertEqual(product.physical_stock, 0)
        self.assertEqual(product.sellable_stock, 0)
        self.assertFalse(product.is_sellable)

    def test_omitted_minimum_stock_defaults_to_ten(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(reverse("product-entry"), self.payload(minimum_stock=""))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Product.objects.get().minimum_stock, 10)

    def test_normalized_duplicate_barcode_is_rejected_without_second_row(self) -> None:
        Product.objects.create(
            category=self.category,
            name="Producto previo",
            barcode="775 123 456",
            sale_price=Decimal("3.50"),
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("product-entry"), self.payload(barcode=" 775123456 ")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe un producto con este código de barras")
        self.assertEqual(Product.objects.count(), 1)

    def test_invalid_prices_never_create_product(self) -> None:
        self.client.force_login(self.admin)
        for price in ("0", "-1", "1.999", "texto"):
            with self.subTest(price=price):
                response = self.client.post(reverse("product-entry"), self.payload(sale_price=price))
                self.assertEqual(response.status_code, 200)
                self.assertEqual(Product.objects.count(), 0)

    def test_invalid_minimums_never_create_product(self) -> None:
        self.client.force_login(self.admin)
        for minimum in ("-1", "1.5", "texto"):
            with self.subTest(minimum=minimum):
                response = self.client.post(
                    reverse("product-entry"), self.payload(minimum_stock=minimum)
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(Product.objects.count(), 0)

    def test_inactive_or_wrong_category_is_rejected(self) -> None:
        inactive = Category.objects.create(name="Otra categoría", is_active=False)
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("product-entry"), self.payload(category=str(inactive.pk))
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Product.objects.count(), 0)

    def test_non_admin_post_is_forbidden_and_does_not_create_product(self) -> None:
        for account in (self.warehouse, self.seller):
            with self.subTest(role=account.role.code):
                self.client.force_login(account)
                response = self.client.post(reverse("product-entry"), self.payload())
                self.assertEqual(response.status_code, 403)
                self.assertEqual(Product.objects.count(), 0)

    def test_database_rejects_product_without_expiration_control(self) -> None:
        with self.assertRaises(IntegrityError), transaction.atomic():
            Product.objects.create(
                category=self.category,
                name="Producto inválido",
                barcode="INVALID-001",
                sale_price=Decimal("2.00"),
                controls_expiration=False,
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 2 — HU-CAT-01, HU-CAT-02, HU-PROD-01, HU-PROD-04, HU-PROD-05, HU-PROD-06
# ═══════════════════════════════════════════════════════════════════════════════

class _CatalogS2Base(TestCase):
    """Base con roles y usuarios compartidos por todos los tests de Sprint 2."""
    password = "Test-only-Passw0rd"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.warehouse_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
        cls.admin = Account.objects.create_user(
            "admin2@test.invalid", cls.password, display_name="Admin", role=cls.admin_role
        )
        cls.warehouse = Account.objects.create_user(
            "wh2@test.invalid", cls.password, display_name="Almacén", role=cls.warehouse_role
        )
        cls.seller = Account.objects.create_user(
            "seller2@test.invalid", cls.password, display_name="Vendedor", role=cls.seller_role
        )
        cls.category = Category.objects.create(name="Enlatados")


# ── HU-CAT-01 ·  Lista de categorías ─────────────────────────────────────────

class CategoryListTests(_CatalogS2Base):
    def test_admin_can_see_category_list(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("category-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enlatados")

    def test_non_admin_gets_403(self) -> None:
        for user in (self.warehouse, self.seller):
            with self.subTest(role=user.role.code):
                self.client.force_login(user)
                self.assertEqual(self.client.get(reverse("category-list")).status_code, 403)


# ── HU-CAT-02 · Crear nueva categoría ────────────────────────────────────────

class CategoryCreateTests(_CatalogS2Base):
    def test_admin_creates_category(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(reverse("category-create"), {"name": "Bebidas"})
        self.assertRedirects(response, reverse("category-list"))
        self.assertTrue(Category.objects.filter(name_normalized="bebidas").exists())

    def test_duplicate_name_is_rejected(self) -> None:
        self.client.force_login(self.admin)
        # "Enlatados" ya existe desde setUpTestData
        response = self.client.post(reverse("category-create"), {"name": "ENLATADOS"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Category.objects.filter(name_normalized="enlatados").count(), 1)

    def test_non_admin_post_is_forbidden(self) -> None:
        self.client.force_login(self.seller)
        response = self.client.post(reverse("category-create"), {"name": "X"})
        self.assertEqual(response.status_code, 403)


# ── HU-PROD-01 · Catálogo de productos ───────────────────────────────────────

class ProductListTests(_CatalogS2Base):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.product = Product.objects.create(
            category=cls.category,
            name="Frijoles 400 g",
            barcode="1234567890001",
            sale_price=Decimal("3.50"),
        )

    def test_admin_sees_product_list(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("product-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Frijoles 400 g")

    def test_warehouse_sees_product_list(self) -> None:
        self.client.force_login(self.warehouse)
        response = self.client.get(reverse("product-list"))
        self.assertEqual(response.status_code, 200)

    def test_seller_gets_403(self) -> None:
        self.client.force_login(self.seller)
        self.assertEqual(self.client.get(reverse("product-list")).status_code, 403)

    def test_search_filters_by_name(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("product-list"), {"q": "Frijoles"})
        self.assertContains(response, "Frijoles 400 g")
        response2 = self.client.get(reverse("product-list"), {"q": "xyz_no_existe"})
        self.assertNotContains(response2, "Frijoles 400 g")

    def test_catalog_and_registration_page_show_current_sale_availability(self) -> None:
        from datetime import timedelta
        from django.utils import timezone
        from inventory.models import InitialInventoryLoad, Lot

        self.client.force_login(self.admin)
        list_url = reverse("product-list")
        detail_url = reverse("product-created", args=(self.product.pk,))
        self.assertContains(self.client.get(list_url), "Sin stock vigente")
        self.assertContains(self.client.get(detail_url), "No disponible para venta: sin stock vigente")

        load = InitialInventoryLoad.objects.create(product=self.product, responsible=self.warehouse)
        Lot.objects.create(
            product=self.product, initial_load=load, number="ACTUAL",
            initial_quantity=2, available_quantity=2, unit_cost=Decimal("1.0000"),
            expiration_date=timezone.localdate() + timedelta(days=10),
        )
        self.assertContains(self.client.get(list_url), ">Disponible<", html=False)
        self.assertContains(self.client.get(detail_url), "Disponible para venta")

        self.category.is_active = False
        self.category.save(update_fields=["is_active"])
        self.assertContains(self.client.get(list_url), "Categoría desactivada")
        self.assertContains(self.client.get(detail_url), "Categoría desactivada")


# ── HU-PROD-04 · Editar producto ─────────────────────────────────────────────

class ProductEditTests(_CatalogS2Base):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.product = Product.objects.create(
            category=cls.category,
            name="Sardinillas 125 g",
            barcode="9990000000001",
            sale_price=Decimal("5.20"),
        )

    def _edit_payload(self, **overrides):
        data = {
            "name": "Sardinillas 125 g",
            "barcode": "9990000000001",
            "sale_price": "5.20",
            "minimum_stock": "10",
        }
        response = self.client.get(reverse("product-edit", args=(self.product.pk,)))
        if response.status_code == 200:
            data["edit_snapshot"] = response.context["form"].initial["edit_snapshot"]
        data.update(overrides)
        return data

    def test_admin_can_edit_product_name(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("product-edit", args=(self.product.pk,)),
            self._edit_payload(name="Sardinillas light 125 g"),
        )
        self.assertRedirects(response, reverse("product-list"))
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Sardinillas light 125 g")

    def test_duplicate_barcode_is_rejected(self) -> None:
        other = Product.objects.create(
            category=self.category,
            name="Otro producto",
            barcode="1111111111111",
            sale_price=Decimal("2.00"),
        )
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("product-edit", args=(self.product.pk,)),
            self._edit_payload(barcode="1111111111111"),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe un producto con este código de barras")

    def test_non_admin_gets_403(self) -> None:
        self.client.force_login(self.seller)
        self.assertEqual(
            self.client.post(reverse("product-edit", args=(self.product.pk,)), self._edit_payload()).status_code,
            403,
        )


# ── HU-PROD-05 · Gestionar disponibilidad ────────────────────────────────────

class ProductToggleTests(_CatalogS2Base):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.product = Product.objects.create(
            category=cls.category,
            name="Choclo 300 g",
            barcode="2222222222222",
            sale_price=Decimal("2.80"),
        )

    def test_admin_toggles_availability(self) -> None:
        self.client.force_login(self.admin)
        was_active = self.product.is_active
        url = reverse("product-toggle", args=(self.product.pk,))
        self.client.post(url)
        self.product.refresh_from_db()
        self.assertEqual(self.product.is_active, was_active)
        self.client.post(url, {"is_active": "false", "version": self.product.updated_at.isoformat()})
        self.product.refresh_from_db()
        self.assertEqual(self.product.is_active, not was_active)

    def test_non_admin_gets_403(self) -> None:
        self.client.force_login(self.seller)
        self.assertEqual(
            self.client.post(reverse("product-toggle", args=(self.product.pk,))).status_code, 403
        )


# ── HU-PROD-06 · Consultar vencimientos ──────────────────────────────────────

class ProductExpirationsTests(_CatalogS2Base):
    def test_admin_accesses_expirations_page(self) -> None:
        self.client.force_login(self.admin)
        response = self.client.get(reverse("product-expirations"))
        self.assertEqual(response.status_code, 200)

    def test_warehouse_accesses_expirations_page(self) -> None:
        self.client.force_login(self.warehouse)
        response = self.client.get(reverse("product-expirations"))
        self.assertEqual(response.status_code, 200)

    def test_seller_gets_403(self) -> None:
        self.client.force_login(self.seller)
        self.assertEqual(self.client.get(reverse("product-expirations")).status_code, 403)

    def test_invalid_and_extreme_dias_parameters_fall_back_gracefully(self) -> None:
        self.client.force_login(self.admin)
        for bad_val in ("", "abc", "-5", "999999999"):
            with self.subTest(dias=bad_val):
                response = self.client.get(reverse("product-expirations"), {"dias": bad_val})
                self.assertEqual(response.status_code, 200)

    def test_active_custom_category_can_be_used_to_register_product(self) -> None:
        """BUG-021 / HU-CAT-02: Una categoría activa creada por el Admin puede usarse al registrar productos."""
        custom_cat = Category.objects.create(name="Bebidas y jugos", is_active=True)
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("product-entry"),
            {
                "name": "Jugo de durazno 500ml",
                "barcode": "775888999001", "barcode_type": "INTERNAL",
                "category": str(custom_cat.pk),
                "unit": Product.Unit.UNIT,
                "sale_price": "4.50",
                "minimum_stock": "12",
            },
        )
        prod = Product.objects.get(barcode="775888999001")
        self.assertRedirects(response, reverse("product-created", args=(prod.pk,)))
        self.assertEqual(prod.category, custom_cat)

    def test_barcode_rejects_xss_and_special_characters_on_create_and_edit(self) -> None:
        """BUG-013: El código de barras rechaza caracteres HTML/script en creación y edición."""
        prod = Product.objects.create(
            category=self.category,
            name="Producto Barcode Seguro",
            barcode="775000111222",
            sale_price=Decimal("5.00"),
        )
        self.client.force_login(self.admin)
        create_resp = self.client.post(
            reverse("product-entry"),
            {
                "name": "Producto XSS",
                "barcode": "<script>alert(1)</script>", "barcode_type": "INTERNAL",
                "category": str(self.category.pk),
                "unit": Product.Unit.UNIT,
                "sale_price": "5.00",
                "minimum_stock": "10",
            },
        )
        self.assertEqual(create_resp.status_code, 200)
        self.assertFalse(Product.objects.filter(name="Producto XSS").exists())

        edit_resp = self.client.post(
            reverse("product-edit", args=(prod.pk,)),
            {
                "edit_snapshot": self.client.get(reverse("product-edit", args=(prod.pk,))).context["form"].initial["edit_snapshot"],
                "name": prod.name,
                "barcode": "<script>alert(1)</script>",
                "sale_price": "5.00",
                "minimum_stock": "10",
            },
        )
        self.assertEqual(edit_resp.status_code, 200)
        prod.refresh_from_db()
        self.assertEqual(prod.barcode, "775000111222")

    def test_product_edit_rejects_scientific_notation_and_excessive_minimum_stock(self) -> None:
        """BUG-009: La edición de producto rechaza notación científica y topes absurdos."""
        prod = Product.objects.create(
            category=self.category,
            name="Producto Limites Edit",
            barcode="775000333444",
            sale_price=Decimal("6.00"),
            minimum_stock=10,
        )
        self.client.force_login(self.admin)
        for bad_price, bad_min in (("1e5", "10"), ("999999999.99", "10"), ("6.00", "999999999")):
            with self.subTest(price=bad_price, minimum=bad_min):
                resp = self.client.post(
                    reverse("product-edit", args=(prod.pk,)),
                    {
                        "edit_snapshot": self.client.get(reverse("product-edit", args=(prod.pk,))).context["form"].initial["edit_snapshot"],
                        "name": prod.name,
                        "barcode": prod.barcode,
                        "sale_price": bad_price,
                        "minimum_stock": bad_min,
                    },
                )
                self.assertEqual(resp.status_code, 200)
                prod.refresh_from_db()
                self.assertEqual(prod.sale_price, Decimal("6.00"))
                self.assertEqual(prod.minimum_stock, 10)

    def test_product_created_alias_url_and_catalog_link(self) -> None:
        """BUG-023: La ruta alias /productos/<id>/creado/ responde 200 e incluye enlace al catálogo."""
        prod = Product.objects.create(
            category=self.category,
            name="Producto Alias Creado",
            barcode="775000555666",
            sale_price=Decimal("4.20"),
        )
        self.client.force_login(self.admin)
        resp = self.client.get(reverse("product-created-alias", args=(prod.pk,)))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, reverse("product-list"))

    def test_bug028_category_toggle_and_product_edit_category_and_barcode_search(self) -> None:
        """BUG-028 y BUG-031: Categorías permiten activar/desactivar, editar categoría de producto y buscar por código de barras."""
        from catalog.services import create_category

        new_cat = create_category(actor=self.admin, name="Conservas gourmet")
        product = Product.objects.create(
            category=self.category,
            name="Espárragos en frasco",
            barcode="7751234009999",
            sale_price=Decimal("9.50"),
        )
        self.client.force_login(self.admin)

        cat_form_resp = self.client.get(reverse("category-create"))
        self.assertNotContains(cat_form_resp, "solo habilita la categoría")

        edit_resp = self.client.post(
            reverse("product-edit", args=(product.pk,)),
            {
                "edit_snapshot": self.client.get(reverse("product-edit", args=(product.pk,))).context["form"].initial["edit_snapshot"],
                "name": product.name,
                "barcode": product.barcode,
                "category": str(new_cat.pk),
                "sale_price": "9.50",
                "minimum_stock": "10",
            },
        )
        self.assertRedirects(edit_resp, reverse("product-list"))
        product.refresh_from_db()
        self.assertEqual(product.category, new_cat)

        toggle_resp = self.client.post(reverse("category-toggle", args=(new_cat.pk,)),
                                       {"is_active": "false", "state_version": new_cat.state_version, "confirm": "yes"})
        self.assertRedirects(toggle_resp, reverse("category-list"))
        new_cat.refresh_from_db()
        self.assertFalse(new_cat.is_active)

        search_resp = self.client.get(reverse("product-list"), {"q": "7751234009999"})
        self.assertEqual(search_resp.status_code, 200)
        self.assertContains(search_resp, product.name)

    def test_bug030_seed_demo_populates_weighted_average_cost(self) -> None:
        """BUG-030: El comando seed_demo calcula y persiste el average_cost ponderado de los productos demo."""
        from django.core.management import call_command
        from identity.models import Account, Role

        Category.objects.get_or_create(
            name_normalized="productos enlatados", defaults={"name": "Productos enlatados"}
        )
        wh_role, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
        Account.objects.create_user(
            email="warehouse.seed@example.com",
            password="StrongPassword!123",
            display_name="Kevin Seed",
            role=wh_role,
        )
        call_command("seed_demo")
        leche = Product.objects.get(barcode="7750001000042")
        self.assertGreater(leche.average_cost, Decimal("0.0000"))
        self.assertEqual(leche.average_cost, Decimal("3.2214"))

    def test_bug033_product_with_inactive_category_can_update_price_and_name(self) -> None:
        """BUG-033: Si la categoría de un producto fue desactivada, Admin aún puede editar precio/nombre manteniendo su categoría actual."""
        inactive_cat = Category.objects.create(name="Categoría Temporal", is_active=True)
        other_inactive = Category.objects.create(name="Otra Inactiva", is_active=False)
        prod = Product.objects.create(
            category=inactive_cat,
            name="Conserva Cat Inactiva",
            barcode="775000330001",
            sale_price=Decimal("6.00"),
            minimum_stock=10,
        )
        inactive_cat.is_active = False
        inactive_cat.save(update_fields=["is_active"])

        self.client.force_login(self.admin)
        resp = self.client.post(
            reverse("product-edit", args=(prod.pk,)),
            {
                "edit_snapshot": self.client.get(reverse("product-edit", args=(prod.pk,))).context["form"].initial["edit_snapshot"],
                "name": "Conserva Cat Inactiva Editada",
                "barcode": prod.barcode,
                "category": str(inactive_cat.pk),
                "sale_price": "7.50",
                "minimum_stock": "12",
            },
        )
        self.assertRedirects(resp, reverse("product-list"))
        prod.refresh_from_db()
        self.assertEqual(prod.name, "Conserva Cat Inactiva Editada")
        self.assertEqual(prod.sale_price, Decimal("7.50"))
        self.assertFalse(prod.is_sellable)

        # Cambiar a otra categoría inactiva distinta sí debe rechazarse
        bad_resp = self.client.post(
            reverse("product-edit", args=(prod.pk,)),
            {
                "edit_snapshot": self.client.get(reverse("product-edit", args=(prod.pk,))).context["form"].initial["edit_snapshot"],
                "name": prod.name,
                "barcode": prod.barcode,
                "category": str(other_inactive.pk),
                "sale_price": "7.50",
                "minimum_stock": "12",
            },
        )
        self.assertEqual(bad_resp.status_code, 200)
        prod.refresh_from_db()
        self.assertEqual(prod.category, inactive_cat)

    def test_bug004_product_barcode_update_preserves_historical_sale_line_snapshot(self) -> None:
        """BUG-004: Editar el código de barras de un producto no altera product_snapshot_barcode en ventas históricas."""
        import uuid as _uuid
        from cash.models import CashRegister, CashShift
        from sales.models import Sale, SaleLine

        prod = Product.objects.create(
            category=self.category,
            name="Conserva Snapshot",
            barcode="775000040001",
            sale_price=Decimal("8.00"),
        )
        reg = CashRegister.objects.create(code="CAJA-SNAP-04")
        shift = CashShift.objects.create(
            cash_register=reg, seller=self.seller, opening_amount=Decimal("20.00")
        )
        sale = Sale.objects.create(
            cash_shift=shift,
            seller=self.seller,
            total_amount=Decimal("8.00"),
            base_amount=Decimal("6.78"),
            igv_amount=Decimal("1.22"),
            cash_received=Decimal("10.00"),
            change_given=Decimal("2.00"),
            correlative="V-00990004",
            idempotency_key=_uuid.uuid4(),
        )
        sl = SaleLine.objects.create(
            sale=sale,
            product=prod,
            product_snapshot_name=prod.name,
            product_snapshot_barcode="775000040001",
            quantity=1,
            unit_price=Decimal("8.00"),
            amount=Decimal("8.00"),
        )

        self.client.force_login(self.admin)
        self.client.post(
            reverse("product-edit", args=(prod.pk,)),
            {
                "edit_snapshot": self.client.get(reverse("product-edit", args=(prod.pk,))).context["form"].initial["edit_snapshot"],
                "name": "Conserva Snapshot Renombrada",
                "barcode": "775000049999",
                "category": str(self.category.pk),
                "sale_price": "8.00",
                "minimum_stock": "10",
            },
        )
        sl.refresh_from_db()
        self.assertEqual(sl.product_snapshot_barcode, "775000040001")
        self.assertEqual(sl.product, prod)
