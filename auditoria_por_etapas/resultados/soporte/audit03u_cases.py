"""03-U: web checkout vs category suspension, real contention and two products."""
from datetime import timedelta
from decimal import Decimal
from html.parser import HTMLParser
from uuid import UUID,uuid4
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from audit03l_concurrency import contest
from catalog.models import Category, Product
from catalog.services import update_product, product_edit_snapshot, toggle_category_status
from identity.models import Account, Role
from inventory.models import Lot
from inventory.services import confirm_initial_load, LotInput
from cash.models import CashRegister, CashShift
from cash.services import open_cash_shift
from sales.models import Sale, SaleLine, SaleCounter, SaleDraft, SaleDraftLine
from sales.services import add_product_to_draft, checkout_sale

class Inputs(HTMLParser):
    def __init__(self): super().__init__(); self.data={}
    def handle_starttag(self,tag,attrs):
        if tag=='input':
            v=dict(attrs)
            if v.get('name'):self.data[v['name']]=v.get('value','')

def run_cases():
    actors={}
    for alias,code in [('admin','ADMIN'),('warehouse','ALMACENERO'),('seller','VENDEDOR')]:
        role,_=Role.objects.get_or_create(code=code,defaults={'name':code})
        actors[alias]=Account.objects.create_user('u-'+alias+'@audit03.invalid',None,role=role,display_name='AUD03 U '+alias)
    CashRegister.objects.create(code='CAJA-01')
    shift=open_cash_shift(actor=actors['seller'],opening_amount=Decimal('50.00'))
    cases=[]
    for first in ('suspension','checkout'):
        a=Category.objects.create(name='U A '+first);b=Category.objects.create(name='U B '+first)
        p=Product.objects.create(category=a,name='U P '+first,barcode='UP-'+first,sale_price=Decimal('8.50'))
        q=Product.objects.create(category=a,name='U Q '+first,barcode='UQ-'+first,sale_price=Decimal('6.00'))
        for product in (p,q):
            confirm_initial_load(actor=actors['warehouse'],product=product,lots=[LotInput('BASE',10,Decimal('2.50'),timezone.localdate()+timedelta(days=60))])
        historic_draft=add_product_to_draft(actor=actors['seller'],product_id=p.pk,quantity=1)
        history=checkout_sale(actor=actors['seller'],draft_id=historic_draft.pk,cash_received=Decimal('10.00'),idempotency_key=uuid4())
        draft=add_product_to_draft(actor=actors['seller'],product_id=p.pk,quantity=2)
        add_product_to_draft(actor=actors['seller'],product_id=q.pk,quantity=1)
        client=Client(enforce_csrf_checks=True);client.force_login(actors['seller'])
        initial=client.get(reverse('sales-checkout'));assert initial.status_code==200
        parser=Inputs();parser.feed(initial.content.decode());data=parser.data
        data.update(cash_received='50.00',discount_amount='')
        expected=product_edit_snapshot(Product.objects.get(pk=p.pk))
        update_product(actor=actors['admin'],product=Product.objects.get(pk=p.pk),name=expected['name'],barcode=expected['barcode'],sale_price=expected['sale_price'],minimum_stock=expected['minimum_stock'],category=b,expected_snapshot=expected)
        def state():
            return {'categories':list(Category.objects.filter(pk__in=[a.pk,b.pk]).order_by('pk').values('id','is_active','state_version')),
                'products':list(Product.objects.filter(pk__in=[p.pk,q.pk]).order_by('pk').values('id','category_id','name','barcode','sale_price','is_active')),
                'draft':list(SaleDraft.objects.filter(pk=draft.pk).values('id','status')),
                'lines':list(SaleDraftLine.objects.filter(draft=draft).order_by('product_id').values('product_id','quantity','unit_price')),
                'lots':list(Lot.objects.filter(product_id__in=[p.pk,q.pk]).order_by('product_id').values('product_id','available_quantity')),
                'sale':list(Sale.objects.filter(draft=draft).values('id','total_amount','cash_received','change_given','correlative')),
                'details':list(SaleLine.objects.filter(sale__draft=draft).order_by('product_id').values('product_id','quantity','unit_price','product_snapshot_name','product_snapshot_barcode')),
                'historic':list(SaleLine.objects.filter(sale=history).values('product_id','quantity','unit_price','product_snapshot_name','product_snapshot_barcode')),
                'counter':list(SaleCounter.objects.values('next_value')),
                'shift':list(CashShift.objects.filter(pk=shift.pk).values('id','status','opening_amount'))}
        before=state()
        def suspend():
            c=toggle_category_status(actor=actors['admin'],category=Category.objects.get(pk=b.pk),is_active=False,expected_version=0)
            return {'active':c.is_active,'version':c.state_version}
        def pay():
            resp=client.post(reverse('sales-checkout'),data)
            body=resp.content.decode()
            return {'http':resp.status_code,'review':('ya no está disponible' in body or 'producto o precio cambió' in body.lower()),'location_is_receipt':(resp.get('Location') or '').startswith('/ventas/constancia/')}
        race=contest(suspend,pay) if first=='suspension' else contest(pay,suspend)
        after=state(); sold=first=='checkout'
        pay_result=race['winner']['value'] if sold else race['contender']['value']
        checks={'wait_observed':race['lock_observed'] and race['blocker_matches_winner'] and race['distinct_connections'],
          'first_action_committed':race['winner']['status']=='committed','second_action_completed':race['contender']['status']=='committed',
          'category_inactive':not Category.objects.get(pk=b.pk).is_active,'product_reclassified':Product.objects.get(pk=p.pk).category_id==b.pk,
          'historical_unchanged':after['historic']==before['historic'],'commercial_product_unchanged':after['products']==before['products'],
          'shift_unchanged':after['shift']==before['shift'],
          'expected_response':pay_result['http']==(302 if sold else 200) and (pay_result['location_is_receipt'] if sold else pay_result['review']),
          'expected_sale_count':len(after['sale'])==int(sold),
          'expected_draft_state':after['draft'][0]['status']==('DISCARDED' if sold else 'ACTIVE')}
        if not sold:
            checks['rejected_without_mutation']=all(after[k]==before[k] for k in ('lots','sale','details','draft','lines','counter','shift','historic'))
            reactivated=toggle_category_status(actor=actors['admin'],category=Category.objects.get(pk=b.pk),is_active=True,expected_version=1)
            get=client.get(reverse('sales-checkout'));parser=Inputs();parser.feed(get.content.decode());retry=parser.data
            retry.update(cash_received='50.00',discount_amount='')
            resp=client.post(reverse('sales-checkout'),retry);final=state();sale=Sale.objects.filter(draft=draft).first()
            checks['reactivation_and_retry']=reactivated.is_active and resp.status_code==302 and len(final['sale'])==1
        else:
            final=after;sale=Sale.objects.filter(draft=draft).first()
            # An additional sale cannot offer the suspended product.
            try:add_product_to_draft(actor=actors['seller'],product_id=p.pk,quantity=1); checks['next_sale_blocked']=False
            except Exception as error:
                from django.core.exceptions import ValidationError
                checks['next_sale_blocked']=isinstance(error,ValidationError)
        replay=checkout_sale(actor=actors['seller'],draft_id=draft.pk,cash_received=Decimal('50.00'),idempotency_key=sale.idempotency_key) if sale else None
        checks['service_replay_idempotent']=bool(replay and replay.pk==sale.pk and Sale.objects.filter(draft=draft).count()==1)
        checks['final_lots']=all(x['available_quantity']==(7 if x['product_id']==p.pk else 9) for x in final['lots'])
        checks['one_sale_23_soles']=len(final['sale'])==1 and final['sale'][0]['total_amount']==Decimal('23.00')
        checks['two_sale_lines']=len(final['details'])==2 and sum(x['quantity'] for x in final['details'])==3
        checks['historic_still_preserved']=final['historic']==before['historic']
        cases.append({'id':'PG-U-'+first,'ok':all(checks.values()),'checks':checks,'race':race,'before':before,'after':after,'final':final,
            'method':'Django test Client CSRF checkout vs real category service, independent PostgreSQL connections; contest wraps winner in transaction and observes pg_blocking_pids; no socket HTTP'})
    return cases
