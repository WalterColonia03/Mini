"""Purpose-built FEFO ties in an isolated marked DB, no operational data."""
from datetime import timedelta
from decimal import Decimal
from uuid import UUID
from unittest.mock import patch


def prepare():
    from django.utils import timezone
    from catalog.models import Product, Category
    from identity.models import Account
    from inventory.models import InitialInventoryLoad, Lot
    worker=Account.objects.get(email='warehouse@audit03.invalid')
    category=Category.objects.get(name='Higiene')
    now=timezone.now()
    today=timezone.localdate()
    product=Product.objects.create(name='Salida FEFO',barcode='FEFO-AD',category=category,sale_price=Decimal('3.00'))
    load=InitialInventoryLoad.objects.create(product=product,responsible=worker)
    # Deliberately create in a different order from FEFO and reverse lot numbers
    # relative to UUID order. Patch only creation time, using normal model save.
    specimens=[
        (50,'A-TARDE',60,now-timedelta(days=3),2),
        (30,'A-UUID-MAYOR',30,now-timedelta(days=1),2),
        (20,'Z-UUID-MENOR',30,now-timedelta(days=1),2),
        (40,'Z-INGRESO-ANTIGUO',30,now-timedelta(days=2),2),
        (10,'VENCIDO',0,now-timedelta(days=4),5),
    ]
    for identifier,number,days,received,quantity in specimens:
        with patch('django.utils.timezone.now',return_value=received):
            Lot.objects.create(id=UUID(int=identifier),product=product,initial_load=load,responsible=worker,
                               number=number,initial_quantity=quantity,available_quantity=quantity,
                               unit_cost=Decimal('1.00'),expiration_date=today+timedelta(days=days))
    return {'product_id':str(product.pk),'code':product.barcode,
            'order':[str(UUID(int=n)) for n in [40,20,30,50]],'expired':str(UUID(int=10)),
            'quantities':[3,2,3]}
