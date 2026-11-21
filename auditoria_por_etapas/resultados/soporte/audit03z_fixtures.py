"""Fixtures for the marked 03-Z database initialized by the browser runner."""
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4


def inventory():
    return {
        'criteria': ['HU-PROD-03/CA01-02', 'HU-PROD-04/CA03', 'RN-28', 'RN-29'],
        'screens': ['alta de producto', 'captura temporal', 'edición', 'catálogo', 'preparación de venta'],
        'inputs': ['tipo interno/GTIN/sin clasificar', 'lecturas Ctrl+A', 'nombre', 'código', 'instantánea de edición'],
        'outputs': ['valor temporal', 'Usar código', 'aviso de duplicado', 'rechazo de edición', 'stock e históricos'],
        'cases': ['reemplazo con selección colapsada: igual y distinto', 'patrón repetido legítimo',
                  'rechazo de clasificación solapada', 'clasificación sin colisión', 'permisos y consultas'],
    }


def prepare_legacy():
    codes = [('Anterior Z1', '012345678905', 'UNCLASSIFIED'), ('Anterior Z2', '0012345678905', 'UNCLASSIFIED'),
             ('Anterior Z3', '4006381333931', 'UNCLASSIFIED')]
    _prepare_products(codes)


def prepare_package_sample():
    codes = [('Unidad AA', '4006381333931', 'GTIN'), ('Interno BB', '00-BB', 'INTERNAL'),
             ('Unidad CC', '012345678905', 'GTIN')]
    _prepare_products(codes, extra_lot=True)


def _prepare_products(codes, extra_lot=False):
    from django.utils import timezone
    from catalog.models import Category, Product
    from identity.models import Account
    from inventory.services import confirm_initial_load, LotInput
    from sales.services import add_product_to_draft, checkout_sale

    category = Category.objects.get(name='Higiene')
    warehouse = Account.objects.get(email='warehouse@audit03.invalid')
    seller = Account.objects.get(email='seller@audit03.invalid')
    for index, (name, code, kind) in enumerate(codes, start=1):
        product = Product.objects.create(name=name, barcode=code, barcode_type=kind, category=category, sale_price=Decimal('3.00'))
        lot = LotInput(f'Z-{index}', 4 + index, Decimal('1.00'), timezone.localdate() + timedelta(days=60))
        lots = [lot]
        if extra_lot:
            lots.append(LotInput(f'AA-{index}', 2, Decimal('1.00'), timezone.localdate() + timedelta(days=90)))
        confirm_initial_load(actor=warehouse, product=product, lots=lots)
        draft = add_product_to_draft(actor=seller, product_id=product.pk, quantity=1)
        checkout_sale(actor=seller, draft_id=draft.pk, cash_received=Decimal('5.00'), idempotency_key=uuid4())
