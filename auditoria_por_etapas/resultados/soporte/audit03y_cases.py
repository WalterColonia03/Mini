from decimal import Decimal
from catalog.models import Category, Product, ProductBarcodeKey
from catalog.services import register_canned_product
from catalog.barcodes import reading_keys
from identity.models import Role, Account
from audit03l_concurrency import contest


def run_cases():
    role,_=Role.objects.get_or_create(code='ADMIN', defaults={'name':'Administrador'})
    actors=[Account.objects.create_user(f'p{i}@audit03.invalid',None,role=role,display_name=f'Operador {i}') for i in range(2)]
    cases=[]
    for i,(first_kind,second_kind) in enumerate([('GTIN','GTIN'),('INTERNAL','GTIN'),('GTIN','INTERNAL'),('GTIN','GTIN')]):
        payload=f'01234567{i}00'
        digit=(-sum(int(ch)*(3 if j%2==0 else 1) for j,ch in enumerate(reversed(payload))))%10
        upc=payload+str(digit)
        codes=[upc, '0'+upc] if i!=3 else ['00'+upc,upc]
        categories=[Category.objects.create(name=f'Grupo {i} {j}') for j in range(2)]
        def action(j,kind):
            return lambda: str(register_canned_product(actor=actors[j],name=f'Producto {i} {j}',barcode=codes[j],barcode_type=kind,category=categories[j],unit='UND',sale_price=Decimal('2.00'),minimum_stock=1).pk)
        race=contest(action(0,first_kind),action(1,second_kind))
        records=Product.objects.filter(category__in=categories)
        checks={'contention':race['lock_observed'] and race['distinct_connections'], 'committed':race['winner']['status']=='committed',
                'duplicate_rejected':race['contender']['status']=='rejected' and 'Ya existe un producto con este código de barras.' in race['contender'].get('messages',[]),
                'one_product':records.count()==1 and records.first().barcode==codes[0],
                'only_winner_keys':set(ProductBarcodeKey.objects.filter(product__in=records).values_list('reading_key',flat=True))==reading_keys(codes[0],first_kind)}
        cases.append({'id':f'PG-Y-{i+1}-{first_kind}-{second_kind}','ok':all(checks.values()),'checks':checks,'race':race})
    return cases
