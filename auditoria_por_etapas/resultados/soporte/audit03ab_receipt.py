"""03-AB receipt fixtures, only used by the marked isolated audit runner."""
from decimal import Decimal
from datetime import timedelta


def inventory():
    from inventory.forms import InitialLoadProductForm, StockEntryProductForm, LotInputForm
    return {
        'criteria': ['INV-01a/CA01-05', 'INV-01b/CA01-02', 'PROP-03-RET-T01/03/05/11'],
        'rules': ['RN-01', 'RN-03', 'RN-14', 'RN-19', 'RN-29'],
        'scope': 'sequential one-product receipts with multiple lots and explicit unit quantities',
        'routes': ['/inventario/carga-inicial/', '/inventario/entrada/', '/inventario/cargas/<uuid>/'],
        'forms': {cls.__name__: {
            name: {'label': field.label, 'required':field.required, 'type':type(field).__name__,
                   'minimum':str(getattr(field,'min_value',None)), 'maximum':str(getattr(field,'max_value',None)),
                   'length':getattr(field,'max_length',None), 'decimals':getattr(field,'decimal_places',None)}
            for name,field in cls.base_fields.items()}
            for cls in [InitialLoadProductForm, StockEntryProductForm, LotInputForm]},
        'actions': ['confirm initial receipt', 'confirm later entry', 'cancel', 'reload', 'replay HTTP POST'],
        'outputs': ['form errors','receipt quantities, supplier, expiration, cost','catalogue and sale quantities'],
        'pending': ['approved replenishment request conflict', 'multi-product single transaction',
                    'PostgreSQL concurrency', 'physical packaging conversion', 'quarantine and recalls'],
    }


def prepare():
    from django.utils import timezone
    from catalog.models import Product, Category
    from inventory.models import Supplier
    from identity.models import Account
    import audit03k_run as base
    import os
    from pathlib import Path

    category=Category.objects.get(name='Higiene')
    products=[]
    for name,code,kind in [('Recepción A','4006381333931','GTIN'),
                           ('Recepción B','00-REC-B','INTERNAL'),('Recepción C','012345678905','GTIN')]:
        p=Product.objects.create(name=name,barcode=code,barcode_type=kind,category=category,sale_price=Decimal('9.00'))
        products.append({'id':str(p.pk),'name':name,'barcode':code})
    supplier=Supplier.objects.create(name='Proveedor ficticio AB',ruc='00000000001')
    warehouse=Account.objects.get(email='warehouse@audit03.invalid')
    base.write(Path(os.environ['AUDIT03_OUT'])/'fixture.json', {
        'products':products,'supplier_id':str(supplier.pk),'warehouse_id':str(warehouse.pk),
        'future':(timezone.localdate()+timedelta(days=60)).isoformat(),
        'later':(timezone.localdate()+timedelta(days=90)).isoformat(),
        'today':timezone.localdate().isoformat()})
