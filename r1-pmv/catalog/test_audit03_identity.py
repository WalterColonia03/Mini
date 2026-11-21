from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from .barcodes import reading_keys
from .models import Category, Product, ProductBarcodeKey


class ExplicitBarcodeIdentityTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='Prueba identidad')

    def product(self, name, barcode, kind):
        return Product.objects.create(name=name, barcode=barcode, category=self.category,
                                      sale_price=Decimal('2.00'), barcode_type=kind)

    def test_legacy_literals_cannot_be_merged_by_reclassifying_one(self):
        a = self.product('Anterior A', '012345678905', 'UNCLASSIFIED')
        b = self.product('Anterior B', '0012345678905', 'UNCLASSIFIED')
        a.barcode_type = 'GTIN'
        with self.assertRaises(ValidationError):
            a.full_clean()
        with self.assertRaises(IntegrityError), transaction.atomic():
            a.save(update_fields=['barcode_type'])
        a.refresh_from_db()
        self.assertEqual(a.barcode_type, 'UNCLASSIFIED')
        self.assertEqual(set(ProductBarcodeKey.objects.values_list('reading_key','product_id')), {(a.barcode,a.pk),(b.barcode,b.pk)})

    def test_inactive_gtin_still_reserves_all_representations(self):
        p = self.product('GTIN', '0012345678905', 'GTIN')
        p.is_active = False
        p.save(update_fields=['is_active'])
        with self.assertRaises(IntegrityError), transaction.atomic():
            self.product('Interno', '012345678905', 'INTERNAL')
        self.assertEqual(Product.objects.count(),1)
        self.assertEqual(p.barcode_keys.count(),3)

    def test_nonretail_and_short_codes_require_literal_policy(self):
        for raw in ['10012345678902','96385074','0012345678906']:
            with self.subTest(raw=raw):
                with self.assertRaises(ValidationError):
                    reading_keys(raw,'GTIN')
                self.assertEqual(reading_keys(raw,'INTERNAL'),{raw})
