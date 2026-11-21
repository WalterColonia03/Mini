from datetime import datetime, timezone as datetime_timezone, date
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.forms import LotInputForm
from inventory.models import InitialInventoryLoad, Lot
from inventory.services import LotInput, confirm_initial_load


class ReceiptDateTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        cls.worker = Account.objects.create_user("dates@test.invalid", None, role=role, display_name="Fechas")
        cls.category = Category.objects.create(name="Fechas de prueba")

    def test_midnight_in_lima_changes_eligibility_atomically(self):
        moments = [(datetime(2026,11,12,4,59,59,tzinfo=datetime_timezone.utc), date(2026,11,11), True),
                   (datetime(2026,11,12,5,0,0,tzinfo=datetime_timezone.utc), date(2026,11,12), False)]
        for index,(moment,local_day,accepted) in enumerate(moments):
            with self.subTest(moment=moment), patch("django.utils.timezone.now", return_value=moment):
                self.assertEqual(timezone.localdate(), local_day)
                product = Product.objects.create(name=f"Reloj {index}", barcode=f"DATE-{index}",
                                                 category=self.category, sale_price=Decimal("5.00"))
                before = (list(Lot.objects.values()), list(InitialInventoryLoad.objects.values()))
                lot = LotInput("DATE",1,Decimal("1.00"),date(2026,11,12))
                if accepted:
                    confirm_initial_load(actor=self.worker, product=product, lots=[lot])
                    self.assertEqual(Lot.objects.get(product=product).received_at, moment)
                else:
                    with self.assertRaisesMessage(ValidationError,"vencimiento debe ser posterior"):
                        confirm_initial_load(actor=self.worker, product=product, lots=[lot])
                    self.assertEqual(before,(list(Lot.objects.values()), list(InitialInventoryLoad.objects.values())))

    def test_twenty_year_anniversary_matches_form_model_and_service(self):
        moment = datetime(2026,11,11,17,0,tzinfo=datetime_timezone.utc)
        for index,(expiration,accepted) in enumerate([(date(2046,11,11),True),(date(2046,11,12),False),
                                                      (date(2046,12,31),False),(date(2047,1,1),False)]):
            with self.subTest(expiration=expiration), patch("django.utils.timezone.now",return_value=moment):
                product = Product.objects.create(name=f"Futuro {index}",barcode=f"FUTURE-{index}",
                                                 category=self.category,sale_price=Decimal("5.00"))
                form = LotInputForm(data={"number":"F","quantity":"1","unit_cost":"1.00",
                                          "expiration_date":expiration.isoformat()})
                self.assertEqual(form.is_valid(),accepted)
                lot=LotInput("F",1,Decimal("1.00"),expiration)
                model_lot=Lot(number="F",initial_quantity=1,available_quantity=1,
                              unit_cost=Decimal("1.00"),expiration_date=expiration)
                if accepted:
                    model_lot.clean()
                    confirm_initial_load(actor=self.worker,product=product,lots=[lot])
                else:
                    with self.assertRaisesMessage(ValidationError,"20 años"):
                        model_lot.clean()
                    with self.assertRaisesMessage(ValidationError,"20 años"):
                        confirm_initial_load(actor=self.worker,product=product,lots=[lot])
                    self.assertFalse(product.lots.exists())

    def test_leap_day_anniversary_uses_last_day_of_february(self):
        self.assertEqual(Lot.latest_expiration_date(date(2080,2,29)),date(2100,2,28))
