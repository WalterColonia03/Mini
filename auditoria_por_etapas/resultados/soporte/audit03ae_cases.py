from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from catalog.models import Category, Product
from catalog.services import toggle_category_status, toggle_product_availability
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot
from inventory.services import LotInput, confirm_initial_load
from audit03l_concurrency import contest


def run_cases():
    roles={}
    for code in ['ALMACENERO','ADMIN']:
        roles[code],_=Role.objects.get_or_create(code=code,defaults={'name':code})
    worker=Account.objects.create_user('receiver@audit03.invalid',None,role=roles['ALMACENERO'],display_name='Receptor')
    admin=Account.objects.create_user('manager@audit03.invalid',None,role=roles['ADMIN'],display_name='Administrador')
    future=timezone.localdate()+timedelta(days=30)
    cases=[]
    for target in ['product','category']:
        for deactivate_first in [True,False]:
            index=len(cases)
            category=Category.objects.create(name=f'Grupo {index}')
            product=Product.objects.create(name=f'Producto {index}',barcode=f'INIT-{index}',
                                           category=category,sale_price=Decimal('5.00'))
            neighbour=Product.objects.create(name=f'Contiguo {index}',barcode=f'OTHER-{index}',
                                             category=category,sale_price=Decimal('5.00'))
            confirm_initial_load(actor=worker,product=neighbour,
                                 lots=[LotInput('BASE',3,Decimal('1.00'),future)])
            neighbour_lots=list(Lot.objects.filter(product=neighbour).values())
            def receipt():
                return str(confirm_initial_load(actor=worker,product=product,
                           lots=[LotInput('NEW-1',2,Decimal('2.00'),future),
                                 LotInput('NEW-2',1,Decimal('5.00'),future)]).pk)
            def deactivate():
                if target=='product':
                    return toggle_product_availability(actor=admin,product=product,is_active=False).is_active
                return toggle_category_status(actor=admin,category=category,is_active=False).is_active
            race=contest(deactivate,receipt) if deactivate_first else contest(receipt,deactivate)
            product.refresh_from_db();category.refresh_from_db();neighbour.refresh_from_db()
            checks={
                'real_lock':race['lock_observed'] and race['distinct_connections'],
                'winner_committed':race['winner']['status']=='committed',
                'contender':race['contender']['status']==('rejected' if deactivate_first else 'committed'),
                'message':not deactivate_first or 'El producto no está disponible para la carga inicial.' in race['contender'].get('messages',[]),
                'target_inactive':not (product.is_active if target=='product' else category.is_active),
                'neighbour_intact':list(Lot.objects.filter(product=neighbour).values())==neighbour_lots and neighbour.average_cost==Decimal('1.0000'),
                'load_count':InitialInventoryLoad.objects.filter(product=product).count()==(0 if deactivate_first else 1),
                'lot_count':Lot.objects.filter(product=product).count()==(0 if deactivate_first else 2),
                'stock':sum(Lot.objects.filter(product=product).values_list('available_quantity',flat=True))==(0 if deactivate_first else 3),
                'cost':product.average_cost==Decimal('0' if deactivate_first else '3.0000'),
            }
            cases.append({'id':f'PG-AE-{target}-deactivate-first-{deactivate_first}',
                          'ok':all(checks.values()),'checks':checks,'race':race})
    return cases
