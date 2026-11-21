from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.db import IntegrityError, connection, transaction
from django.utils import timezone

from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import Lot
from inventory.services import LotInput, confirm_initial_load


class LotReceiptTimeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role=Role.objects.create(code=Role.Code.WAREHOUSE,name="Almacenero")
        worker=Account.objects.create_user("time@test.invalid",None,role=role,display_name="Fecha de ingreso")
        category=Category.objects.create(name="Ingresos")
        product=Product.objects.create(name="Unidad",barcode="TIME-01",category=category,sale_price=Decimal("3.00"))
        confirm_initial_load(actor=worker,product=product,
                             lots=[LotInput("L",3,Decimal("1.00"),timezone.localdate()+timedelta(days=30))])

    def test_saved_timestamp_cannot_be_rewritten(self):
        for fields in [None, ["received_at"]]:
            with self.subTest(update_fields=fields):
                lot=Lot.objects.get()
                original=lot.received_at
                lot.received_at=original-timedelta(days=1)
                with self.assertRaisesMessage(ValidationError,"El instante de ingreso del lote no se puede modificar."):
                    lot.save(update_fields=fields)
                lot.refresh_from_db()
                self.assertEqual(lot.received_at,original)

    def test_stock_update_preserves_original_timestamp(self):
        lot=Lot.objects.get()
        original=lot.received_at
        lot.available_quantity=2
        lot.save(update_fields=["available_quantity"])
        lot.refresh_from_db()
        self.assertEqual(lot.received_at,original)
        self.assertEqual(lot.available_quantity,2)

    def test_bulk_and_direct_updates_cannot_rewrite_timestamp(self):
        lot=Lot.objects.get()
        original=lot.received_at
        lot.received_at=original-timedelta(days=1)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Lot.objects.filter(pk=lot.pk).update(received_at=lot.received_at)
        with self.assertRaises(IntegrityError), transaction.atomic():
            Lot.objects.bulk_update([lot],["received_at"])
        with self.assertRaises(IntegrityError), transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("UPDATE inventory_lot SET received_at = %s", [lot.received_at])
        lot.refresh_from_db()
        self.assertEqual(lot.received_at,original)
        self.assertEqual(Lot.objects.filter(pk=lot.pk).update(received_at=original),1)
