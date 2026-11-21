"""Suspension and checkout in both lock orders, private PostgreSQL only."""
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.utils import timezone

from audit03l_concurrency import contest
from catalog.models import Category, Product
from catalog.services import toggle_product_availability
from identity.models import Account, Role
from inventory.models import Lot
from inventory.services import confirm_initial_load, LotInput
from cash.models import CashRegister, CashShift
from cash.services import open_cash_shift
from sales.models import Sale, SaleLine, SaleCounter, SaleDraft, SaleDraftLine
from sales.services import add_product_to_draft, checkout_sale


def state(product, shift, draft):
    return {
        'product_active': Product.objects.get(pk=product.pk).is_active,
        'category': list(Category.objects.filter(pk=product.category_id).values('is_active','state_version')),
        'lot': list(Lot.objects.filter(product=product).values('number','initial_quantity','available_quantity')),
        'shift': list(CashShift.objects.filter(pk=shift.pk).values('status','opening_amount')),
        'draft': list(SaleDraft.objects.filter(pk=draft.pk).values('status')),
        'lines': list(SaleDraftLine.objects.filter(draft=draft).values('quantity','unit_price')),
        'sales': list(Sale.objects.filter(cash_shift=shift).values('total_amount','cash_received','change_given','correlative')),
        'details': list(SaleLine.objects.filter(product=product).values('product_snapshot_barcode','quantity','unit_price')),
        'counter': list(SaleCounter.objects.values('next_value')),
    }


def run_sale_cases():
    actors = {}
    for alias, code in [('admin','ADMIN'),('warehouse','ALMACENERO'),('seller','VENDEDOR')]:
        role,_ = Role.objects.get_or_create(code=code, defaults={'name':code})
        actors[alias] = Account.objects.create_user('m-sale-'+alias+'@audit03.invalid',None,role=role,display_name='AUD03 M '+alias)
    CashRegister.objects.create(code='CAJA-01')
    shift = open_cash_shift(actor=actors['seller'], opening_amount=Decimal('50.00'))
    cases=[]
    for first in ('suspension','venta'):
        category=Category.objects.create(name='AUD03 M '+first)
        product=Product.objects.create(category=category,name='AUD03 M producto '+first,barcode='M-SALE-'+first,sale_price=Decimal('8.50'))
        confirm_initial_load(actor=actors['warehouse'],product=product,lots=[LotInput('L-BASE',20,Decimal('2.50'),timezone.localdate()+timedelta(days=30))])
        neighbor=Product.objects.create(category=category,name='Control '+first,barcode='CONTROL-'+first,sale_price=Decimal('3.00'))
        confirm_initial_load(actor=actors['warehouse'],product=neighbor,lots=[LotInput('CONTROL',4,Decimal('1.00'),timezone.localdate()+timedelta(days=30))])
        neighbor_before=neighbor_state(neighbor)
        draft=add_product_to_draft(actor=actors['seller'],product_id=product.pk,quantity=2)
        before=state(product,shift,draft)
        key=uuid4()
        def suspend():
            updated=toggle_product_availability(actor=actors['admin'],product=Product.objects.get(pk=product.pk),is_active=False)
            return {'active':updated.is_active}
        def checkout():
            sale=checkout_sale(actor=actors['seller'],draft_id=draft.pk,cash_received=Decimal('20.00'),idempotency_key=key)
            return {'id':str(sale.pk),'total':str(sale.total_amount)}
        sale_first=first=='venta'
        race=contest(checkout,suspend) if sale_first else contest(suspend,checkout)
        after=state(product,shift,draft)
        try:
            add_product_to_draft(actor=actors['seller'],product_id=product.pk,quantity=1)
            subsequent={'rejected':False}
        except ValidationError as error:
            subsequent={'rejected':True,'messages':error.messages}
        unchanged=('shift','lines') if sale_first else ('shift','lines','lot','sales','details','draft','counter')
        checks={
            'wait_observed':race['lock_observed'] and race['distinct_connections'],
            'first_committed':race['winner']['status']=='committed',
            'second_expected':race['contender']['status']==('committed' if sale_first else 'rejected'),
            'product_only_inactive':after['product_active'] is False and before['product_active'] is True and after['category']==before['category']==[{'is_active':True,'state_version':0}],
            'neighbor_preserved': neighbor_before==neighbor_state(neighbor),
            'stock':after['lot'][0]['available_quantity']==(18 if sale_first else 20),
            'conserved':all(before[k]==after[k] for k in unchanged),
            'sale_count':len(after['sales'])==len(before['sales'])+(1 if sale_first else 0),
            'details':after['details']==([{'product_snapshot_barcode':product.barcode,'quantity':2,'unit_price':Decimal('8.50')}] if sale_first else []),
            'draft_status':after['draft']==[{'status':'DISCARDED' if sale_first else 'ACTIVE'}],
            'next_add_rejected':subsequent['rejected'] and after==state(product,shift,draft),
        }
        if sale_first:
            checks['money']=after['sales'][-1]['total_amount']==Decimal('17.00') and after['sales'][-1]['change_given']==Decimal('3.00')
        cases.append({'id':'PG-M-venta-primero-'+first,'ok':all(checks.values()),'checks':checks,'race':race,'before':before,'after':after,'subsequent':subsequent,'neighbor_before':neighbor_before,'neighbor_after':neighbor_state(neighbor)})
        # Each scenario needs its own active draft; close the retained rejected one as test fixture setup.
        if not sale_first:
            from sales.services import discard_active_draft
            discard_active_draft(actor=actors['seller'])
    return cases

def neighbor_state(product):
    return {'product':list(Product.objects.filter(pk=product.pk).values('name','barcode','is_active','category_id','sale_price','average_cost')),
            'lots':list(Lot.objects.filter(product=product).values('initial_quantity','available_quantity','unit_cost')),
            'sellable':Product.objects.get(pk=product.pk).is_sellable}
