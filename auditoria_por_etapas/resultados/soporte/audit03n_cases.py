"""HU-PROD-04/CA05: classify A to B while checkout or B suspension competes.

Run only through audit03n_pg.py, which creates a fresh private cluster.
"""
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

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
from sales.services import add_product_to_draft, checkout_sale, discard_active_draft


def state(product, shift, draft, a, b):
    product = Product.objects.get(pk=product.pk)
    return {
        'product': product_edit_snapshot(product),
        'average_cost': str(product.average_cost),
        'categories': list(Category.objects.filter(pk__in=[a.pk,b.pk]).order_by('name').values('id','name','is_active','state_version')),
        'lots': list(Lot.objects.filter(product=product).order_by('pk').values('id','product_id','number','initial_quantity','available_quantity','unit_cost','expiration_date')),
        'shift': list(CashShift.objects.filter(pk=shift.pk).values('status','opening_amount')),
        'draft': list(SaleDraft.objects.filter(pk=draft.pk).values('id','status')),
        'lines': list(SaleDraftLine.objects.filter(draft=draft).values('id','product_id','quantity','unit_price')),
        'sales': list(Sale.objects.filter(cash_shift=shift).order_by('correlative').values('id','total_amount','cash_received','change_given','correlative')),
        'details': list(SaleLine.objects.filter(product=product).order_by('sale__correlative').values('id','sale_id','product_id','product_snapshot_name','product_snapshot_barcode','quantity','unit_price')),
        'counter': list(SaleCounter.objects.values('next_value')),
    }


def run_cases():
    actors = {}
    for alias, code in [('admin','ADMIN'),('warehouse','ALMACENERO'),('seller','VENDEDOR')]:
        role,_ = Role.objects.get_or_create(code=code, defaults={'name':code})
        actors[alias] = Account.objects.create_user('n-'+alias+'@audit03.invalid',None,role=role,display_name='AUD03 N '+alias)
    CashRegister.objects.create(code='CAJA-01')
    shift = open_cash_shift(actor=actors['seller'],opening_amount=Decimal('50.00'))
    cases=[]
    for scenario in ('venta','suspension'):
        for first in ('reclasificacion',scenario):
            label=scenario+'-'+first
            a=Category.objects.create(name='AUD03 N A '+label)
            b=Category.objects.create(name='AUD03 N B '+label)
            product=Product.objects.create(category=a,name='AUD03 N ficha '+label,barcode='N-'+label,sale_price=Decimal('8.50'))
            confirm_initial_load(actor=actors['warehouse'],product=product,lots=[LotInput('BASE',21,Decimal('2.50'),timezone.localdate()+timedelta(days=30))])
            olddraft=add_product_to_draft(actor=actors['seller'],product_id=product.pk,quantity=1)
            historical=checkout_sale(actor=actors['seller'],draft_id=olddraft.pk,cash_received=Decimal('10.00'),idempotency_key=uuid4())
            draft=add_product_to_draft(actor=actors['seller'],product_id=product.pk,quantity=2)
            expected=product_edit_snapshot(Product.objects.get(pk=product.pk))
            before=state(product,shift,draft,a,b)
            key=uuid4()

            def reclassify():
                edited=update_product(actor=actors['admin'],product=Product.objects.get(pk=product.pk),
                    name=expected['name'],barcode=expected['barcode'],sale_price=expected['sale_price'],
                    minimum_stock=expected['minimum_stock'],category=Category.objects.get(pk=b.pk),
                    expected_snapshot=expected)
                return {'id':str(edited.pk),'category':str(edited.category_id)}

            def other():
                if scenario=='venta':
                    sale=checkout_sale(actor=actors['seller'],draft_id=draft.pk,cash_received=Decimal('20.00'),idempotency_key=key)
                    return {'id':str(sale.pk),'total':str(sale.total_amount)}
                changed=toggle_category_status(actor=actors['admin'],category=Category.objects.get(pk=b.pk),is_active=False,expected_version=0)
                return {'active':changed.is_active,'version':changed.state_version}

            race=contest(reclassify,other) if first=='reclasificacion' else contest(other,reclassify)
            after=state(product,shift,draft,a,b)
            retry = None
            if scenario=='venta' and first=='reclasificacion' and race['contender']['status']=='rejected':
                # A changed joined category may invalidate PostgreSQL's locked rowset.
                # Safe rejection is acceptable only with no side effects and a successful explicit retry.
                rejected_state = after
                retry_sale = checkout_sale(actor=actors['seller'],draft_id=draft.pk,cash_received=Decimal('20.00'),idempotency_key=key)
                retry_again = checkout_sale(actor=actors['seller'],draft_id=draft.pk,cash_received=Decimal('20.00'),idempotency_key=key)
                after = state(product,shift,draft,a,b)
                retry = {'rejected_state':rejected_state,'same_sale':retry_sale.pk==retry_again.pk,
                         'rejection_unchanged':all(rejected_state[k]==before[k] for k in ('lots','sales','details','draft','lines','counter','shift'))}
            sale=scenario=='venta'
            rejected=scenario=='suspension' and first=='suspension'
            wanted=dict(before['product'],category_id=str(a.pk if rejected else b.pk))
            original_line=[row for row in before['details'] if row['sale_id']==historical.pk]
            retained_line=[row for row in after['details'] if row['sale_id']==historical.pk]
            checks={
                'real_wait':race['lock_observed'] and race['blocker_matches_winner'] and race['distinct_connections'],
                'first_commits':race['winner']['status']=='committed',
                'second_expected':race['contender']['status']==('rejected' if rejected or retry else 'committed'),
                'product_identity_and_commercial':after['product']==wanted,
                'category_state':all(c['is_active']==(sale or c['id']==a.pk) and c['state_version']==(0 if sale or c['id']==a.pk else 1) for c in after['categories']),
                'historical_line_preserved':original_line==retained_line and len(original_line)==1,
                'cost_shift_lines_preserved':all(after[k]==before[k] for k in ('average_cost','shift','lines')),
                'stock':sum(row['available_quantity'] for row in after['lots'])==(18 if sale else 20),
                'sale_count':len(after['sales'])==len(before['sales'])+int(sale),
                'draft_status':after['draft'][0]['status']==('DISCARDED' if sale else 'ACTIVE'),
            }
            if retry:
                checks['safe_rejection_and_retry']=retry['same_sale'] and retry['rejection_unchanged']
            if sale:
                current_sale=Sale.objects.filter(idempotency_key=key).first()
                if current_sale is None:
                    cases.append({'id':'PG-N-'+label,'ok':False,'checks':checks,'race':race,'before':before,'after':after,'retry':retry})
                    discard_active_draft(actor=actors['seller'])
                    continue
                checks['sale_money']=current_sale.total_amount==Decimal('17.00') and current_sale.cash_received==Decimal('20.00') and current_sale.change_given==Decimal('3.00')
                newlines=[line for line in after['details'] if line['sale_id']==current_sale.pk]
                checks['sale_snapshot']=len(newlines)==1 and newlines[0]['product_id']==product.pk and newlines[0]['product_snapshot_barcode']==expected['barcode'] and newlines[0]['quantity']==2
            else:
                checks['no_side_effects']=all(after[k]==before[k] for k in ('lots','sales','details','draft','counter'))
                checks['sellable_after']=Product.objects.get(pk=product.pk).is_sellable==rejected
            cases.append({'id':'PG-N-'+label,'ok':all(checks.values()),'checks':checks,'race':race,'before':before,'after':after,'retry':retry})
            if not sale:
                discard_active_draft(actor=actors['seller'])
    return cases
