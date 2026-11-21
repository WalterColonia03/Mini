"""DOC-03AH-01/RN-14/RN-28, primera pasada 14-E sobre datos ficticios."""
import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from cash.models import CashRegister, CashShift, CashShiftClose
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot, PhysicalAdjustment, StockWriteOff
from inventory.services import (
    LotInput, confirm_initial_load, register_physical_adjustment, register_stock_entry, write_off_stock,
)
from sales.models import Sale, SaleCounter, SaleDraft, SaleDraftLine, SaleLine
from sales.services import add_product_to_draft, checkout_sale


class MovingAverageIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin, cls.warehouse, cls.seller = [
            Account.objects.create_user(
                email=f"{code.lower()}@valuation.invalid", password=None, display_name=code,
                role=Role.objects.create(code=code, name=code),
            ) for code in ("ADMIN", "ALMACENERO", "VENDEDOR")
        ]
        cls.product = Product.objects.create(
            category=Category.objects.create(name="Valoración 14E"), name="F-COSTO",
            barcode="INT-F-COSTO", barcode_type="INTERNAL", sale_price=Decimal("10.00"),
        )
        today = timezone.localdate()
        confirm_initial_load(
            actor=cls.warehouse, product=cls.product, business_date=today - timedelta(days=1),
            lots=[LotInput("EXP", 8, Decimal("3.0000"), today),
                  LotInput("VIG", 10, Decimal("3.0000"), today + timedelta(days=30))],
        )
        cls.shift = CashShift.objects.create(
            cash_register=CashRegister.objects.create(code="CAJA-01"),
            seller=cls.seller, opening_amount=Decimal("10.00"),
        )

    def setUp(self):
        self.admin_client, self.warehouse_client, self.seller_client = [Client() for _ in range(3)]
        for client, actor in zip(
            (self.admin_client, self.warehouse_client, self.seller_client),
            (self.admin, self.warehouse, self.seller),
        ):
            client.force_login(actor)

    def snapshot(self):
        models = (Product, InitialInventoryLoad, Lot, PhysicalAdjustment, StockWriteOff,
                  CashRegister, CashShift, CashShiftClose, Sale, SaleCounter, SaleDraft, SaleDraftLine, SaleLine)
        return {model._meta.label: list(model.objects.order_by("pk").values()) for model in models}

    def assert_stock(self, physical, sellable, cost):
        self.product.refresh_from_db()
        self.assertEqual(self.product.physical_stock, physical)
        self.assertEqual(self.product.sellable_stock, sellable)
        self.assertEqual(self.product.average_cost, Decimal(cost))

    def receipt_payload(self):
        return {
            "idempotency_key": str(uuid.uuid4()),
            "product": self.product.pk, "lots-TOTAL_FORMS": 1, "lots-INITIAL_FORMS": 0,
            "lots-MIN_NUM_FORMS": 1, "lots-MAX_NUM_FORMS": 10, "lots-0-number": "REC",
            "lots-0-quantity": 10, "lots-0-unit_cost": "6.0000",
            "lots-0-expiration_date": (timezone.localdate() + timedelta(days=60)).isoformat(),
        }

    def checkout_payload(self):
        response = self.seller_client.get(reverse("sales-checkout"))
        self.assertEqual(response.status_code, 200)
        return {**response.context["form"].initial, "cash_received": "200.00"}

    def writeoff_payload(self, lot, quantity):
        return {"lot_id": lot.pk, "quantity": quantity, "reason": "ROBO",
                "notes": "Faltante confirmado por conteo", "idempotency_key": str(uuid.uuid4())}

    def test_http_physical_cost_receipt_sale_writeoff_adjustment_and_history(self):
        self.assert_stock(18, 10, "3.0000")
        response = self.warehouse_client.post(reverse("stock-entry"), self.receipt_payload())
        self.assertEqual(response.status_code, 302)
        self.assert_stock(28, 20, "4.0714")
        self.assertEqual(self.seller_client.post(reverse("sales-draft"), {
            "product_id": self.product.pk, "quantity": 1,
        }).status_code, 302)
        self.assertEqual(self.seller_client.post(
            reverse("sales-checkout"), self.checkout_payload()
        ).status_code, 302)
        self.assert_stock(27, 19, "4.0714")
        line = SaleLine.objects.get()
        self.assertEqual(line.unit_cost, Decimal("4.0714"))
        vig = self.product.lots.get(number="VIG")
        payload = self.writeoff_payload(vig, 1)
        self.assertEqual(self.warehouse_client.post(reverse("stock-writeoff"), payload).status_code, 302)
        self.assert_stock(26, 18, "4.0714")
        writeoff = StockWriteOff.objects.get()
        self.assertEqual(writeoff.unit_cost, Decimal("4.0714"))
        self.assertEqual(self.admin_client.post(reverse("physical-adjustment"), {
            "lot_id": vig.pk, "delta": 2, "reason": "Hallazgo por conteo",
            "idempotency_key": str(uuid.uuid4()),
        }).status_code, 302)
        self.assert_stock(28, 20, "4.0714")
        adjustment = PhysicalAdjustment.objects.get()
        self.assertEqual(adjustment.unit_cost, Decimal("4.0714"))
        prior = self.snapshot()
        # La segunda recepción recalcula el promedio, conservando las salidas anteriores.
        register_stock_entry(
            actor=self.warehouse, product=self.product,
            lots=[LotInput("NEXT", 2, Decimal("9.0000"), timezone.localdate() + timedelta(days=90))],
        )
        self.assert_stock(30, 22, "4.4000")
        after = self.snapshot()
        for model in (Sale, SaleLine, StockWriteOff, PhysicalAdjustment, CashShift):
            self.assertEqual(prior[model._meta.label], after[model._meta.label])
        # Un reenvío de baja tampoco vuelve a descontar ni altera el promedio nuevo.
        prior = after
        self.assertEqual(self.warehouse_client.post(reverse("stock-writeoff"), payload).status_code, 302)
        self.assertEqual(self.snapshot(), prior)

    def test_zero_stock_resets_average_preserves_last_cost_and_rejects_unpriced_adjustment(self):
        expired = self.product.lots.get(number="EXP")
        with transaction.atomic():
            draft = add_product_to_draft(actor=self.seller, product_id=self.product.pk, quantity=10)
            sale = checkout_sale(actor=self.seller, draft_id=draft.pk,
                                 cash_received=Decimal("100"), idempotency_key=uuid.uuid4())
            self.assert_stock(8, 0, "3.0000")
            self.assertEqual(sale.lines.get().unit_cost, Decimal("3.0000"))
            transaction.set_rollback(True)
        write_off_stock(actor=self.warehouse, lot=expired, quantity=8, reason="VENCIMIENTO")
        self.assert_stock(10, 10, "3.0000")
        vig = self.product.lots.get(number="VIG")
        for operation in ("sale", "writeoff", "adjustment"):
            with self.subTest(operation=operation), transaction.atomic():
                if operation == "sale":
                    draft = add_product_to_draft(actor=self.seller, product_id=self.product.pk, quantity=10)
                    result = checkout_sale(actor=self.seller, draft_id=draft.pk,
                                           cash_received=Decimal("100"), idempotency_key=uuid.uuid4()).lines.get()
                elif operation == "writeoff":
                    result = write_off_stock(actor=self.warehouse, lot=vig, quantity=10,
                                             reason="ROBO", notes="Conteo confirmado")
                else:
                    result = register_physical_adjustment(actor=self.admin, lot=vig, delta=-10,
                                                          reason="Conteo confirmado")
                self.assert_stock(0, 0, "0.0000")
                self.assertEqual(result.unit_cost, Decimal("3.0000"))
                before = self.snapshot()
                with self.assertRaises(ValidationError):
                    register_physical_adjustment(actor=self.admin, lot=vig, delta=2,
                                                 reason="Hallazgo sin costo fiable")
                self.assertEqual(self.snapshot(), before)
                response = self.admin_client.post(reverse("physical-adjustment"), {
                    "lot_id": vig.pk, "delta": 2, "reason": "Hallazgo sin costo fiable",
                    "idempotency_key": str(uuid.uuid4()),
                })
                self.assertEqual(response.status_code, 200)
                self.assertEqual(self.snapshot(), before)
                register_stock_entry(
                    actor=self.warehouse, product=self.product,
                    lots=[LotInput("RESTART", 2, Decimal("7.0000"), timezone.localdate() + timedelta(days=60))],
                )
                self.assert_stock(2, 2, "7.0000")
                result.refresh_from_db()
                self.assertEqual(result.unit_cost, Decimal("3.0000"))
                transaction.set_rollback(True)

    def test_role_and_input_rejections_do_not_mutate_cost_or_stock(self):
        vig = self.product.lots.get(number="VIG")
        requests = (
            (self.admin_client, "stock-entry", self.receipt_payload(), 403),
            (self.seller_client, "stock-writeoff", self.writeoff_payload(vig, 1), 403),
            (self.warehouse_client, "physical-adjustment",
             {"lot_id": vig.pk, "delta": 2, "reason": "Conteo confirmado"}, 403),
            (self.warehouse_client, "stock-writeoff", self.writeoff_payload(vig, 999), 200),
            (self.admin_client, "physical-adjustment",
             {"lot_id": vig.pk, "delta": -999, "reason": "Conteo confirmado"}, 200),
        )
        before = self.snapshot()
        for client, route, payload, status in requests:
            with self.subTest(route=route, status=status):
                self.assertEqual(client.post(reverse(route), payload).status_code, status)
                self.assertEqual(self.snapshot(), before)

    def test_runtime_failure_after_write_rolls_back_all_cost_operations(self):
        vig = self.product.lots.get(number="VIG")
        draft = add_product_to_draft(actor=self.seller, product_id=self.product.pk, quantity=1)
        operations = (
            ("receipt", "inventory.models.Lot.objects.bulk_create", Lot.objects.bulk_create,
             lambda: register_stock_entry(actor=self.warehouse, product=self.product,
                 lots=[LotInput("ROLLBACK", 10, Decimal("6"), timezone.localdate() + timedelta(days=90))])),
            ("sale", "inventory.models.Lot.save", Lot.save,
             lambda: checkout_sale(actor=self.seller, draft_id=draft.pk,
                 cash_received=Decimal("10"), idempotency_key=uuid.uuid4())),
            ("writeoff", "inventory.models.Lot.save", Lot.save,
             lambda: write_off_stock(actor=self.warehouse, lot=vig, quantity=1,
                 reason="ROBO", notes="Conteo confirmado")),
            ("adjustment", "inventory.models.Lot.save", Lot.save,
             lambda: register_physical_adjustment(actor=self.admin, lot=vig, delta=2,
                 reason="Conteo confirmado")),
        )
        for name, target, original, operation in operations:
            with self.subTest(operation=name):
                before = self.snapshot()
                writes = []
                def fail_after(*args, **kwargs):
                    original(*args, **kwargs)
                    writes.append(self.snapshot() != before)
                    raise RuntimeError("Fallo sintético después de escritura")
                with patch(target, autospec=True, side_effect=fail_after):
                    with self.assertRaisesMessage(RuntimeError, "Fallo sintético"):
                        operation()
                self.assertEqual(writes, [True])
                self.assertEqual(self.snapshot(), before)

    def test_legacy_unknown_costs_are_not_filled_from_current_average(self):
        vig = self.product.lots.get(number="VIG")
        legacy_writeoff = StockWriteOff.objects.create(lot=vig, quantity=1, reason="ROBO",
            notes="Registro anterior", responsible=self.warehouse, correlativo="B-00000001")
        legacy_adjustment = PhysicalAdjustment.objects.create(lot=vig, delta=1,
            reason="Registro anterior", responsible=self.admin)
        draft = add_product_to_draft(actor=self.seller, product_id=self.product.pk, quantity=1)
        sale = checkout_sale(actor=self.seller, draft_id=draft.pk,
                             cash_received=Decimal("10"), idempotency_key=uuid.uuid4())
        SaleLine.objects.filter(sale=sale).update(unit_cost=None)
        register_stock_entry(actor=self.warehouse, product=self.product,
            lots=[LotInput("NEW", 1, Decimal("9"), timezone.localdate() + timedelta(days=90))])
        legacy_writeoff.refresh_from_db()
        legacy_adjustment.refresh_from_db()
        self.assertIsNone(legacy_writeoff.unit_cost)
        self.assertIsNone(legacy_adjustment.unit_cost)
        self.assertIsNone(sale.lines.get().unit_cost)


class LegacyOutputCostMigrationTests(TransactionTestCase):
    def test_upgrade_preserves_old_rows_with_unknown_cost(self):
        role = Role.objects.create(code="ADMIN", name="Administrador")
        actor = Account.objects.create_user(
            email="migration@valuation.invalid", password=None, display_name="Actor ficticio", role=role,
        )
        product = Product.objects.create(
            category=Category.objects.create(name="Migración costo"),
            name="Producto histórico", barcode="MIG-COSTO", sale_price=Decimal("9"),
            average_cost=Decimal("3.0000"),
        )
        load = InitialInventoryLoad.objects.create(product=product, responsible=actor)
        lot = Lot.objects.create(
            product=product, initial_load=load, number="HIST", initial_quantity=10, available_quantity=9,
            unit_cost=Decimal("2.0000"), expiration_date=timezone.localdate() + timedelta(days=30),
        )
        executor = MigrationExecutor(connection)
        latest = executor.loader.graph.leaf_nodes()
        old_target = ("inventory", "0006_lot_received_at_immutable")
        try:
            executor.migrate([old_target])
            old_apps = executor.loader.project_state([old_target]).apps
            old_writeoff = old_apps.get_model("inventory", "StockWriteOff").objects.create(
                lot_id=lot.pk, quantity=1, reason="ROBO", notes="Registro anterior",
                responsible_id=actor.pk, correlativo="B-00000001",
            )
            old_adjustment = old_apps.get_model("inventory", "PhysicalAdjustment").objects.create(
                lot_id=lot.pk, delta=1, reason="Registro anterior", responsible_id=actor.pk,
            )
            originals = {
                "StockWriteOff": old_apps.get_model("inventory", "StockWriteOff").objects.values().get(),
                "PhysicalAdjustment": old_apps.get_model("inventory", "PhysicalAdjustment").objects.values().get(),
            }
            MigrationExecutor(connection).migrate(latest)
            for model, identifier in ((StockWriteOff, old_writeoff.pk), (PhysicalAdjustment, old_adjustment.pk)):
                migrated = model.objects.filter(pk=identifier).values().get()
                self.assertIsNone(migrated.pop("unit_cost"))
                if model in (StockWriteOff, PhysicalAdjustment):
                    for field in ("idempotency_key", "content_signature", "product_snapshot_name", "product_snapshot_barcode",
                                  "unit_snapshot", "responsible_snapshot_name", "lot_snapshot_number", "lot_snapshot_expiration_date", "origin_snapshot"):
                        self.assertIsNone(migrated.pop(field))
                if model is PhysicalAdjustment:
                    self.assertIsNone(migrated.pop("cost_source"))
                self.assertEqual(migrated, originals[model.__name__])
            product.refresh_from_db()
            self.assertEqual(product.average_cost, Decimal("3.0000"))
            self.assertEqual(product.physical_stock, 9)
        finally:
            MigrationExecutor(connection).migrate(latest)
