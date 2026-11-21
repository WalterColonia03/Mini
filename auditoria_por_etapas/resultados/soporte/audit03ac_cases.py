from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot, Supplier
from inventory.services import LotInput, confirm_initial_load, register_stock_entry, toggle_supplier_status
from audit03l_concurrency import contest


def run_cases():
    warehouse_role,_=Role.objects.get_or_create(code='ALMACENERO',defaults={'name':'Almacenero'})
    admin_role,_=Role.objects.get_or_create(code='ADMIN',defaults={'name':'Administrador'})
    worker=Account.objects.create_user('receiver@audit03.invalid',None,role=warehouse_role,display_name='Receptor')
    admin=Account.objects.create_user('manager@audit03.invalid',None,role=admin_role,display_name='Administrador')
    future=timezone.localdate()+timedelta(days=30)
    cases=[]
    for operation in [confirm_initial_load, register_stock_entry]:
        for deactivate_first in [True,False]:
            index=len(cases)
            category=Category.objects.create(name=f'Categoría {index}')
            product=Product.objects.create(name=f'Producto {index}',barcode=f'SUP-{index}',
                                           category=category,sale_price=Decimal('5.00'))
            supplier=Supplier.objects.create(name=f'Proveedor {index}',ruc=str(index).zfill(11))
            if operation is register_stock_entry:
                confirm_initial_load(actor=worker,product=product,
                                     lots=[LotInput('BASE',3,Decimal('1.00'),future)],supplier=supplier)
            initial_lots=list(Lot.objects.filter(product=product).order_by('pk').values())
            cached=Supplier.objects.get(pk=supplier.pk)
            def receipt():
                return str(operation(actor=worker,product=product,supplier=cached,
                                     lots=[LotInput('NEW',2,Decimal('2.00'),future)]).pk)
            def deactivate():
                return toggle_supplier_status(actor=admin,supplier=Supplier.objects.get(pk=supplier.pk)).is_active
            race=contest(deactivate,receipt) if deactivate_first else contest(receipt,deactivate)
            product.refresh_from_db();supplier.refresh_from_db()
            expected_new=0 if deactivate_first else 1
            expected_base=1 if operation is register_stock_entry else 0
            checks={
                'real_lock':race['lock_observed'] and race['distinct_connections'],
                'winner_committed':race['winner']['status']=='committed',
                'contender':race['contender']['status']==('rejected' if deactivate_first else 'committed'),
                'message':not deactivate_first or 'El proveedor seleccionado está inactivo.' in race['contender'].get('messages',[]),
                'inactive':not supplier.is_active,
                'initial_rows_preserved':list(Lot.objects.filter(product=product,number='BASE').order_by('pk').values())==initial_lots,
                'lot_count':Lot.objects.filter(product=product).count()==expected_base+expected_new,
                'load_count':InitialInventoryLoad.objects.filter(product=product).count()==int(bool(expected_base+expected_new)),
                'stock':sum(Lot.objects.filter(product=product).values_list('available_quantity',flat=True))==expected_base*3+expected_new*2,
                'cost':product.average_cost==Decimal(('1.0000' if expected_base else '0') if deactivate_first else ('1.4000' if expected_base else '2.0000')),
            }
            cases.append({'id':f'PG-AC-{operation.__name__}-deactivate-first-{deactivate_first}',
                          'ok':all(checks.values()),'checks':checks,'race':race})
    return cases
