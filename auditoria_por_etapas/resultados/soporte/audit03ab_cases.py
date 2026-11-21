from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import InitialInventoryLoad, Lot
from inventory.services import LotInput, confirm_initial_load, register_stock_entry
from audit03l_concurrency import contest


def run_cases():
    role,_=Role.objects.get_or_create(code='ALMACENERO',defaults={'name':'Almacenero'})
    actors=[Account.objects.create_user(f'receipt{i}@audit03.invalid',None,role=role,
                                       display_name=f'Receptor {i}') for i in range(2)]
    future=timezone.localdate()+timedelta(days=30)
    cases=[]
    for index,kind in enumerate(['initial','same-lot','different-lots']):
        category=Category.objects.create(name=f'Grupo recibo {index}')
        product=Product.objects.create(name=f'Artículo {index}',barcode=f'REC-{index}',
                                       category=category,sale_price=Decimal('5.00'))
        service=confirm_initial_load if kind=='initial' else register_stock_entry
        if kind!='initial':
            confirm_initial_load(actor=actors[0],product=product,
                                 lots=[LotInput('BASE',10,Decimal('1.00'),future)])
        def action(worker):
            number='R-2' if kind=='different-lots' and worker==1 else 'R-1'
            return lambda: str(service(actor=actors[worker],product=product,
                                       lots=[LotInput(number,2,Decimal('3.00'),future)]).pk)
        race=contest(action(0),action(1))
        lots=Lot.objects.filter(product=product)
        product.refresh_from_db()
        expected_lots={'initial':1,'same-lot':2,'different-lots':3}[kind]
        expected_qty={'initial':2,'same-lot':12,'different-lots':14}[kind]
        expected_cost={'initial':'3.0000','same-lot':'1.3333','different-lots':'1.5714'}[kind]
        expected_status='committed' if kind=='different-lots' else 'rejected'
        checks={
            'lock_observed':race['lock_observed'] and race['distinct_connections'],
            'winner_committed':race['winner']['status']=='committed',
            'contender_status':race['contender']['status']==expected_status,
            'one_load':InitialInventoryLoad.objects.filter(product=product).count()==1,
            'lots':lots.count()==expected_lots,
            'stock':sum(lots.values_list('available_quantity',flat=True))==expected_qty,
            'weighted_cost':product.average_cost==Decimal(expected_cost),
        }
        cases.append({'id':'PG-AB-'+kind,'ok':all(checks.values()),'checks':checks,'race':race})
    return cases
