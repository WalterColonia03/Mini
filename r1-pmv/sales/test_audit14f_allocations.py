"""14-F, asignaciones FEFO, identidad histórica y orden persistido."""
import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.apps import apps
from django.db import connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from cash.models import CashRegister, CashShift
from cash.services import close_cash_shift
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import Lot
from inventory.services import LotInput, confirm_initial_load
from sales.models import Sale, SaleCounter, SaleDraft, SaleLine
from sales.services import add_product_to_draft


class AllocationHistoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin, cls.warehouse, cls.seller, cls.other_seller = [
            Account.objects.create_user(
                email=f"{name.replace(' ', '.').lower()}@allocations.invalid", password=None, display_name=name,
                role=Role.objects.get_or_create(code=code, defaults={"name": code})[0],
            ) for name, code in (("Admin ficticio", "ADMIN"), ("Almacen ficticio", "ALMACENERO"),
                                 ("Vendedor original", "VENDEDOR"), ("Segundo vendedor", "VENDEDOR"))
        ]
        cls.category = Category.objects.create(name="Asignaciones ficticias")
        cls.product = Product.objects.create(
            category=cls.category, name="Leche ficticia", barcode="INT-14F", sale_price=Decimal("10.00"),
        )
        cls.future = timezone.localdate() + timedelta(days=30)
        confirm_initial_load(
            actor=cls.warehouse, product=cls.product,
            lots=[LotInput("A", 3, Decimal("3.0000"), cls.future),
                  LotInput("B", 7, Decimal("3.0000"), cls.future + timedelta(days=1))],
        )
        cls.register = CashRegister.objects.create(code="CAJA-01")
        cls.shift = CashShift.objects.create(
            cash_register=cls.register, seller=cls.seller, opening_amount=Decimal("100.00"),
        )

    def setUp(self):
        self.seller_client, self.admin_client, self.wh_client, self.other_client = [Client() for _ in range(4)]
        for client, actor in zip((self.seller_client, self.admin_client, self.wh_client, self.other_client),
                                 (self.seller, self.admin, self.warehouse, self.other_seller)):
            client.force_login(actor)

    def allocation_model(self):
        return apps.get_model("sales", "SaleLotAllocation")

    def snapshot(self):
        return {
            model._meta.label: list(model.objects.order_by("pk").values())
            for app in ("identity", "catalog", "inventory", "cash", "sales")
            for model in apps.get_app_config(app).get_models(include_auto_created=True)
        }

    def prepare(self, quantity):
        response = self.seller_client.post(reverse("sales-draft"), {
            "product_id": self.product.pk, "quantity": quantity,
        })
        self.assertEqual(response.status_code, 302)
        response = self.seller_client.get(reverse("sales-checkout"))
        self.assertEqual(response.status_code, 200)
        return {**response.context["form"].initial, "cash_received": str(quantity * 10)}

    def confirm(self, payload):
        response = self.seller_client.post(reverse("sales-checkout"), payload)
        sale = Sale.objects.get(idempotency_key=payload["idempotency_key"])
        self.assertRedirects(response, reverse("sales-receipt", args=(sale.pk,)))
        return sale

    def test_http_fefo_partial_allocation_retry_and_historical_lot(self):
        originals = {lot.number: lot for lot in self.product.lots.all()}
        payload = self.prepare(4)
        sale = self.confirm(payload)
        line = sale.lines.get()
        allocations = list(line.lot_allocations.all())
        self.assertEqual([(row.lot_snapshot_number, row.quantity) for row in allocations], [("A", 3), ("B", 1)])
        self.assertEqual(sum(row.quantity for row in allocations), line.quantity)
        for row in allocations:
            original = originals[row.lot_snapshot_number]
            self.assertEqual(row.lot_id, original.pk)
            self.assertEqual(row.lot_snapshot_expiration_date, original.expiration_date)
            self.assertEqual(row.lot_snapshot_received_at, original.received_at)
        self.assertEqual(list(self.product.lots.order_by("number").values_list("available_quantity", flat=True)), [0, 6])
        before = self.snapshot()
        response = self.seller_client.post(reverse("sales-checkout"), payload)
        self.assertRedirects(response, reverse("sales-receipt", args=(sale.pk,)))
        self.assertEqual(self.snapshot(), before)
        # Una modificación de la ficha de lote no altera su fotografía de la venta.
        allocation_before = list(self.allocation_model().objects.order_by("pk").values())
        Lot.objects.filter(pk=originals["A"].pk).update(
            number="RENOMBRADO", number_normalized="RENOMBRADO",
            expiration_date=self.future + timedelta(days=200),
        )
        self.assertEqual(list(self.allocation_model().objects.order_by("pk").values()), allocation_before)
        for client in (self.admin_client, self.wh_client):
            movement = client.get(reverse("product-movements", args=(self.product.pk,)))
            self.assertEqual(movement.status_code, 200)
            self.assertContains(movement, sale.correlative)
            self.assertContains(movement, "3,0000")
            self.assertContains(movement, f"A · 3 UND · Vence {originals['A'].expiration_date:%d/%m/%Y}")
            self.assertContains(movement, f"B · 1 UND · Vence {originals['B'].expiration_date:%d/%m/%Y}")

    def test_contract_three_plus_two_exhausts_stock_and_totals_cash_once(self):
        Lot.objects.filter(product=self.product, number="B").update(initial_quantity=2, available_quantity=2)
        payload = self.prepare(5)
        sale = self.confirm(payload)
        line = sale.lines.get()
        self.assertEqual(list(line.lot_allocations.values_list("lot_snapshot_number", "quantity")),
                         [("A", 3), ("B", 2)])
        self.product.refresh_from_db()
        self.assertEqual((self.product.physical_stock, self.product.average_cost), (0, Decimal("0")))
        self.assertEqual(line.unit_cost, Decimal("3.0000"))
        self.assertEqual((sale.total_amount, sale.cash_received, sale.change_given),
                         (Decimal("50"), Decimal("50"), Decimal("0")))
        close = close_cash_shift(actor=self.seller, counted_amount=Decimal("150"))
        self.assertEqual(close.expected_amount, Decimal("150"))
        self.assertEqual(close.difference, Decimal("0"))
        before = self.snapshot()
        self.assertRedirects(self.seller_client.post(reverse("sales-checkout"), payload),
                             reverse("sales-receipt", args=(sale.pk,)))
        self.assertEqual(self.snapshot(), before)

    def test_receipt_identity_and_line_order_survive_master_changes(self):
        self.prepare(1)
        for name in ("Segundo producto", "Tercer producto"):
            product = Product.objects.create(category=self.category, name=name, barcode=name, sale_price=Decimal("10"))
            confirm_initial_load(actor=self.warehouse, product=product,
                                 lots=[LotInput("X", 1, Decimal("3"), self.future)])
            add_product_to_draft(actor=self.seller, product_id=product.pk, quantity=1)
        draft = SaleDraft.objects.get(status="ACTIVE")
        expected_names = list(draft.lines.values_list("product__name", flat=True))
        response = self.seller_client.get(reverse("sales-checkout"))
        payload = {**response.context["form"].initial, "cash_received": "30.00"}
        ids = iter(uuid.UUID(int=value) for value in (3, 1, 2))
        with patch.object(SaleLine._meta.get_field("id"), "_get_default", lambda: next(ids)):
            sale = self.confirm(payload)
        self.assertEqual(list(sale.lines.values_list("product_snapshot_name", flat=True)), expected_names)
        self.assertEqual(list(sale.lines.values_list("position", flat=True)), [1, 2, 3])
        self.assertEqual(sale.seller_snapshot_name, "Vendedor original")
        self.assertEqual(sale.cash_register_snapshot_code, "CAJA-01")
        original = list(Sale.objects.values())
        Account.objects.filter(pk=self.seller.pk).update(display_name="Nombre actualizado")
        CashRegister.objects.filter(pk=self.register.pk).update(code="CAJA-CAMBIADA")
        Product.objects.filter(pk=self.product.pk).update(name="Producto actualizado", sale_price=Decimal("99"))
        for client in (self.admin_client, self.seller_client):
            response = client.get(reverse("sales-receipt", args=(sale.pk,)))
            self.assertEqual(response.status_code, 200)
            html = response.content.decode().split('id="constancia-interna">', 1)[1].split("</section>", 1)[0]
            self.assertIn("Vendedor original", html)
            self.assertIn("CAJA-01", html)
            self.assertNotIn("Nombre actualizado", html)
            self.assertNotIn("CAJA-CAMBIADA", html)
            self.assertNotIn("Producto actualizado", html)
            self.assertNotIn("unit_cost", html)
            self.assertNotIn("3,0000", html)
            positions = [html.index(name) for name in expected_names]
            self.assertEqual(positions, sorted(positions))
        self.assertEqual(list(Sale.objects.values()), original)

    def test_postwrite_failures_at_each_stage_roll_back_the_entire_checkout(self):
        payload = self.prepare(4)
        allocation_model = self.allocation_model()
        SaleCounter.objects.get_or_create(pk=1, defaults={"next_value": 1})
        before = self.snapshot()
        for model, failure_at in (
            (SaleCounter, 1), (Sale, 1), (SaleLine, 1), (allocation_model, 1),
            (Lot, 1), (allocation_model, 2), (Lot, 2), (SaleDraft, 1),
        ):
            with self.subTest(model=model.__name__, write_number=failure_at):
                original_save = model.save
                writes = []
                def save_then_fail(instance, *args, **kwargs):
                    original_save(instance, *args, **kwargs)
                    writes.append(self.snapshot() != before)
                    if len(writes) == failure_at:
                        raise RuntimeError(f"Fallo después de guardar {model.__name__}")
                with patch.object(model, "save", autospec=True, side_effect=save_then_fail):
                    with self.assertRaisesMessage(RuntimeError, "Fallo después"):
                        self.seller_client.post(reverse("sales-checkout"), payload)
                self.assertEqual(writes, [True] * failure_at)
                self.assertEqual(self.snapshot(), before)
        self.confirm(payload)
        self.assertEqual(allocation_model.objects.count(), 2)

    def test_denied_checkout_and_receipt_leave_history_intact(self):
        payload = self.prepare(4)
        before = self.snapshot()
        for client in (self.admin_client, self.wh_client):
            self.assertEqual(client.post(reverse("sales-checkout"), payload).status_code, 403)
            self.assertEqual(self.snapshot(), before)
        sale = self.confirm(payload)
        before = self.snapshot()
        self.assertEqual(self.wh_client.get(reverse("sales-receipt", args=(sale.pk,))).status_code, 403)
        self.assertEqual(self.other_client.get(reverse("sales-receipt", args=(sale.pk,))).status_code, 404)
        self.assertEqual(self.snapshot(), before)

    def test_legacy_has_unknown_snapshots_and_deterministic_order_without_allocations(self):
        sale = Sale.objects.create(
            cash_shift=self.shift, seller=self.seller, total_amount=Decimal("20"),
            base_amount=Decimal("16.95"), igv_amount=Decimal("3.05"), cash_received=Decimal("20"),
            change_given=Decimal("0"), correlative="V-LEGACY", idempotency_key=uuid.uuid4(),
        )
        for value in (2, 1):
            SaleLine.objects.create(id=uuid.UUID(int=value), sale=sale, product=self.product,
                product_snapshot_name=f"Anterior-{value}", product_snapshot_barcode="LEGACY",
                quantity=1, unit_price=Decimal("10"), amount=Decimal("10"))
        before = self.snapshot()
        response = self.admin_client.get(reverse("sales-receipt", args=(sale.pk,)))
        self.assertEqual(response.status_code, 200)
        html = response.content.decode().split('id="constancia-interna">', 1)[1].split("</section>", 1)[0]
        self.assertRegex(html.lower(), "no disponible|no capturad|no registrad|desconocid")
        self.assertLess(html.index("Anterior-1"), html.index("Anterior-2"))
        self.assertNotIn("Vendedor original", html)
        self.assertNotIn("CAJA-01", html)
        self.assertIsNone(sale.seller_snapshot_name)
        self.assertIsNone(sale.cash_register_snapshot_code)
        self.assertEqual(list(sale.lines.values_list("position", flat=True)), [None, None])
        self.assertEqual(self.allocation_model().objects.count(), 0)
        self.assertEqual(self.snapshot(), before)

    def test_movement_labels_legacy_barcode_match_and_partial_allocations(self):
        sale = self.confirm(self.prepare(4))
        line = sale.lines.get()
        # Crear dos estados anómalos independientes a partir de la misma venta en la base ficticia.
        with transaction.atomic():
            line.lot_allocations.all().delete()
            SaleLine.objects.filter(pk=line.pk).update(product=None, unit_cost=None)
            before = self.snapshot()
            response = self.admin_client.get(reverse("product-movements", args=(self.product.pk,)))
            self.assertContains(response, "identidad del producto no confirmada")
            self.assertContains(response, "Lotes de salida: No disponibles")
            self.assertContains(response, "Costo unitario de salida: No disponible")
            self.assertEqual(self.snapshot(), before)
            transaction.set_rollback(True)
        line.lot_allocations.filter(lot_snapshot_number="B").delete()
        before = self.snapshot()
        response = self.wh_client.get(reverse("product-movements", args=(self.product.pk,)))
        self.assertContains(response, "Asignación incompleta. Solo se muestran los lotes registrados.")
        self.assertContains(response, "A · 3 UND")
        self.assertNotContains(response, "B · 1 UND")
        self.assertEqual(self.snapshot(), before)


class LegacyAllocationMigrationTests(TransactionTestCase):
    def test_upgrade_preserves_unknown_history_without_fefo_backfill(self):
        role = Role.objects.create(code="VENDEDOR", name="Vendedor")
        actor = Account.objects.create_user(email="migration14f@example.invalid", password=None,
                                           display_name="Identidad actual", role=role)
        register = CashRegister.objects.create(code="CAJA-ACTUAL")
        shift = CashShift.objects.create(cash_register=register, seller=actor, opening_amount=Decimal("100"))
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        old_target = ("sales", "0005_saleline_unit_cost")
        try:
            executor.migrate([old_target])
            old_apps = executor.loader.project_state([old_target]).apps
            old_sale = old_apps.get_model("sales", "Sale").objects.create(
                seller_id=actor.pk, cash_shift_id=shift.pk, total_amount=Decimal("10"),
                base_amount=Decimal("8.47"), igv_amount=Decimal("1.53"), cash_received=Decimal("10"),
                change_given=Decimal("0"), correlative="V-OLD-14F", idempotency_key=uuid.uuid4(),
            )
            old_apps.get_model("sales", "SaleLine").objects.create(
                sale_id=old_sale.pk, product_snapshot_name="Producto anterior",
                product_snapshot_barcode="HIST", quantity=1, unit_price=Decimal("10"),
                amount=Decimal("10"), unit_cost=None,
            )
            before_sale = old_apps.get_model("sales", "Sale").objects.values().get()
            before_line = old_apps.get_model("sales", "SaleLine").objects.values().get()
            MigrationExecutor(connection).migrate(latest)
            after_sale, after_line = Sale.objects.values().get(), SaleLine.objects.values().get()
            self.assertIsNone(after_sale.pop("seller_snapshot_name"))
            self.assertIsNone(after_sale.pop("cash_register_snapshot_code"))
            self.assertIsNone(after_line.pop("position"))
            self.assertEqual(after_sale, before_sale)
            self.assertEqual(after_line, before_line)
            self.assertEqual(apps.get_model("sales", "SaleLotAllocation").objects.count(), 0)
        finally:
            MigrationExecutor(connection).migrate(latest)
