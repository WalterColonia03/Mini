from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from identity.models import Account, Role
from .models import Category, Product
from .services import update_product


class EditBoundaryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        cls.admin = Account.objects.create_user("edicion@audit.invalid", None, role=role, display_name="Edición")
        cls.category = Category.objects.create(name="Productos enlatados")

    def setUp(self):
        self.client.force_login(self.admin)
        self.product = Product.objects.create(category=self.category, name="Producto editable", barcode="EDIT-1", sale_price=Decimal("8.50"))
        self.url = reverse("product-edit", args=[self.product.pk])
        self.data = dict(name=self.product.name, barcode=self.product.barcode, category=str(self.category.pk), sale_price="8.50", minimum_stock="10")
        self.data["edit_snapshot"] = self.client.get(self.url).context["form"].initial["edit_snapshot"]

    def test_empty_edit_reports_required_fields_and_retains_product(self):
        response = self.client.post(self.url, {})
        self.assertEqual(set(response.context["form"].errors), {"name", "barcode", "sale_price", "minimum_stock", "edit_snapshot"})
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Producto editable")
        self.assertEqual(self.product.sale_price, Decimal("8.50"))

    def test_accented_duplicate_is_rejected_and_original_remains(self):
        Product.objects.create(category=self.category, name="Atún ocupado", barcode="OTHER", sale_price=Decimal("3.00"))
        response = self.client.post(self.url, {**self.data, "name": "ATÚN OCUPADO"})
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "name", ["Ya existe un producto registrado con este nombre."])
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Producto editable")

    def test_reclassification_revalidates_a_stale_category(self):
        destination = Category.objects.create(name="Destino")
        Category.objects.filter(pk=destination.pk).update(is_active=False)
        with self.assertRaises(ValidationError) as error:
            update_product(actor=self.admin, product=self.product, category=destination, name="Cambio",
                           barcode=self.product.barcode, sale_price=Decimal("9.20"), minimum_stock=10)
        self.assertEqual(error.exception.message_dict["category"], ["Seleccione una categoría activa."])
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Producto editable")
        self.assertEqual(self.product.category_id, self.category.pk)

    def test_current_inactive_category_may_be_preserved(self):
        Category.objects.filter(pk=self.category.pk).update(is_active=False)
        response = self.client.post(self.url, {**self.data, "category": "", "sale_price": "9.20"})
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.category_id, self.category.pk)
        self.assertEqual(self.product.sale_price, Decimal("9.20"))

    def test_http_code_change_relinks_legacy_detail_without_changing_snapshot(self):
        import uuid
        from cash.models import CashRegister, CashShift
        from sales.models import Sale, SaleLine

        role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
        seller = Account.objects.create_user("ventas@audit.invalid", None, role=role, display_name="Ventas")
        shift = CashShift.objects.create(
            cash_register=CashRegister.objects.create(code="AUD-D"), seller=seller, opening_amount=Decimal("20.00")
        )
        sale = Sale.objects.create(
            cash_shift=shift, seller=seller, total_amount=Decimal("8.50"), base_amount=Decimal("7.20"),
            igv_amount=Decimal("1.30"), cash_received=Decimal("10.00"), change_given=Decimal("1.50"),
            correlative="V-AUD-D", idempotency_key=uuid.uuid4()
        )
        line = SaleLine.objects.create(
            sale=sale, product=None, product_snapshot_name=self.product.name,
            product_snapshot_barcode=self.product.barcode, quantity=1,
            unit_price=Decimal("8.50"), amount=Decimal("8.50")
        )
        response = self.client.post(self.url, {**self.data, "barcode": "EDIT-NEW", "sale_price": "9.20"})
        self.assertEqual(response.status_code, 302)
        line.refresh_from_db()
        self.assertEqual(line.product_id, self.product.pk)
        self.assertEqual(line.product_snapshot_barcode, "EDIT-1")
        self.assertEqual(line.unit_price, Decimal("8.50"))

