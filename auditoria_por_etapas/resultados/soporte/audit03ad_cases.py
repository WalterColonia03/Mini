from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction

from catalog.models import Category
from cash.models import CashRegister
from cash.services import open_cash_shift
from identity.models import Role, Account
from inventory.models import Lot
from sales.models import Sale
from sales.services import add_product_to_draft, checkout_sale
from audit03ad_fefo import prepare
from audit03l_concurrency import contest


def run_cases():
    for name,code in [('warehouse','ALMACENERO'),('seller','VENDEDOR')]:
        role=Role.objects.create(code=code,name=code)
        Account.objects.create_user(name+'@audit03.invalid',None,role=role,display_name=name)
    Category.objects.create(name='Higiene')
    CashRegister.objects.create(code='CAJA-01')
    seller=Account.objects.get(email='seller@audit03.invalid')
    open_cash_shift(actor=seller,opening_amount=Decimal('50.00'))
    # Rehearse migration on existing rows, including a rollback and reapply.
    call_command('migrate','inventory','0005',verbosity=0,interactive=False)
    fixture=prepare()
    before=list(Lot.objects.order_by('pk').values())
    call_command('migrate','inventory','0006',verbosity=0,interactive=False)
    checks={'migration_preserves_rows':before==list(Lot.objects.order_by('pk').values())}
    lot=Lot.objects.get(pk=fixture['order'][0])
    original=lot.received_at
    lot.received_at-=timedelta(days=1)
    try:
        lot.save()
        checks['model_rejected']=False
    except ValidationError:
        checks['model_rejected']=True
    for mode in ['update','bulk','sql']:
        try:
            with transaction.atomic():
                if mode=='update':
                    Lot.objects.filter(pk=lot.pk).update(received_at=lot.received_at)
                elif mode=='bulk':
                    Lot.objects.bulk_update([lot],['received_at'])
                else:
                    with connection.cursor() as cursor:
                        cursor.execute('UPDATE inventory_lot SET received_at = %s WHERE id = %s',[lot.received_at,lot.pk])
            checks[mode+'_rejected']=False
        except IntegrityError:
            checks[mode+'_rejected']=True
    lot.refresh_from_db()
    checks['original_time']=lot.received_at==original
    cases=[{'id':'PG-AD-migration-guard','ok':all(checks.values()),'checks':checks}]
    checks={}
    for index,(quantity,expected) in enumerate([(3,[0,1,2,2]),(2,[0,0,1,2])]):
        draft=add_product_to_draft(actor=seller,product_id=fixture['product_id'],quantity=quantity)
        checkout_sale(actor=seller,draft_id=draft.pk,cash_received=Decimal(quantity*3),idempotency_key=uuid4())
        checks[f'fefo-{index}']=[Lot.objects.get(pk=pk).available_quantity for pk in fixture['order']]==expected
    checks['expired_untouched']=Lot.objects.get(pk=fixture['expired']).available_quantity==5
    checks['all_receipt_times_preserved']={str(l['id']):l['received_at'] for l in before}=={
        str(l.pk):l.received_at for l in Lot.objects.all()}
    cases.append({'id':'PG-AD-fefo','ok':all(checks.values()),'checks':checks})
    draft=add_product_to_draft(actor=seller,product_id=fixture['product_id'],quantity=3)
    key=uuid4()
    action=lambda: str(checkout_sale(actor=seller,draft_id=draft.pk,cash_received=Decimal('9.00'),idempotency_key=key).pk)
    race=contest(action,action)
    checks={'locks':race['lock_observed'] and race['distinct_connections'],
            'same_sale':race['winner']['value']==race['contender']['value'],
            'one_sale_for_draft':Sale.objects.filter(draft=draft).count()==1,
            'zero_vigente':all(Lot.objects.get(pk=pk).available_quantity==0 for pk in fixture['order']),
            'expired_untouched':Lot.objects.get(pk=fixture['expired']).available_quantity==5}
    cases.append({'id':'PG-AD-simultaneous-replay','ok':all(checks.values()),'checks':checks,'race':race})
    return cases
