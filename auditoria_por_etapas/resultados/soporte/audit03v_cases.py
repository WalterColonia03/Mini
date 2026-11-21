"""03-V: actual service calls, three independent concurrent connections and real wait evidence."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from queue import Queue
from threading import Event
from uuid import uuid4
import time
from django.core.exceptions import ValidationError
from django.db import connection, connections, transaction, DatabaseError
from django.utils import timezone
from catalog.models import Category, Product
from catalog.services import update_product, product_edit_snapshot, toggle_category_status
from identity.models import Account, Role
from inventory.models import Lot
from inventory.services import confirm_initial_load, LotInput
from cash.models import CashRegister, CashShift
from cash.services import open_cash_shift
from sales.models import Sale, SaleLine, SaleCounter, SaleDraft, SaleDraftLine
from sales.services import add_product_to_draft, checkout_sale


def run_cases():
    actors={}
    for alias,code in [('admin','ADMIN'),('admin2','ADMIN'),('warehouse','ALMACENERO'),('seller','VENDEDOR')]:
        role,_=Role.objects.get_or_create(code=code,defaults={'name':code})
        actors[alias]=Account.objects.create_user('v-'+alias+'@audit03.invalid',None,role=role,display_name='AUD03 V '+alias)
    CashRegister.objects.create(code='CAJA-01')
    shift=open_cash_shift(actor=actors['seller'],opening_amount=Decimal('50.00'))
    cases=[]
    for scenario in ('edit-first','suspend-first','checkout-first'):
        a=Category.objects.create(name='V A '+scenario);b=Category.objects.create(name='V B '+scenario)
        p=Product.objects.create(category=a,name='V P '+scenario,barcode='VP-'+scenario,sale_price=Decimal('8.50'))
        q=Product.objects.create(category=a,name='V Q '+scenario,barcode='VQ-'+scenario,sale_price=Decimal('6.00'))
        for product in (p,q):
            confirm_initial_load(actor=actors['warehouse'],product=product,lots=[LotInput('BASE',10,Decimal('2.50'),timezone.localdate()+timedelta(days=60))])
        hd=add_product_to_draft(actor=actors['seller'],product_id=p.pk,quantity=1)
        hist=checkout_sale(actor=actors['seller'],draft_id=hd.pk,cash_received=Decimal('10'),idempotency_key=uuid4())
        draft=add_product_to_draft(actor=actors['seller'],product_id=p.pk,quantity=2)
        add_product_to_draft(actor=actors['seller'],product_id=q.pk,quantity=1)
        key=uuid4(); snap=product_edit_snapshot(p)
        def edit():
            product=update_product(actor=actors['admin'],product=Product.objects.get(pk=p.pk),name=snap['name'],barcode=snap['barcode'],sale_price=snap['sale_price'],minimum_stock=snap['minimum_stock'],category=b,expected_snapshot=snap)
            return {'category':str(product.category_id)}
        def suspend():
            category=toggle_category_status(actor=actors['admin2'],category=Category.objects.get(pk=b.pk),is_active=False,expected_version=0)
            return {'active':category.is_active,'version':category.state_version}
        def pay():
            sale=checkout_sale(actor=actors['seller'],draft_id=draft.pk,cash_received=Decimal('50'),idempotency_key=key)
            return {'id':str(sale.pk),'total':str(sale.total_amount)}
        functions={'edit':edit,'suspend':suspend,'pay':pay}
        def state():
            return {'categories':list(Category.objects.filter(pk__in=[a.pk,b.pk]).order_by('pk').values('id','is_active','state_version')),
              'products':list(Product.objects.filter(pk__in=[p.pk,q.pk]).order_by('pk').values('id','category_id','name','barcode','sale_price','is_active')),
              'lots':list(Lot.objects.filter(product_id__in=[p.pk,q.pk]).order_by('product_id').values('product_id','available_quantity')),
              'draft':list(SaleDraft.objects.filter(pk=draft.pk).values('id','status')),
              'draft_lines':list(SaleDraftLine.objects.filter(draft=draft).order_by('product_id').values('product_id','quantity','unit_price')),
              'sale':list(Sale.objects.filter(draft=draft).values('id','total_amount','cash_received','change_given','correlative')),
              'details':list(SaleLine.objects.filter(sale__draft=draft).order_by('product_id').values('product_id','quantity','unit_price','product_snapshot_name','product_snapshot_barcode')),
              'history':list(SaleLine.objects.filter(sale=hist).values('product_id','quantity','unit_price','product_snapshot_name','product_snapshot_barcode')),
              'counter':list(SaleCounter.objects.values('next_value')),
              'shift':list(CashShift.objects.filter(pk=shift.pk).values('id','status','opening_amount'))}
        before=state(); ids=Queue(); held=Event(); release=Event(); second_held=Event(); release_second=Event()
        def worker(kind,hold=False,hold_second=False):
            try:
                with connection.cursor() as cur:cur.execute('SELECT pg_backend_pid()');ids.put((kind,cur.fetchone()[0]))
                if hold or hold_second:
                    with transaction.atomic():
                        value=functions[kind]()
                        if hold:held.set();gate=release
                        else:second_held.set();gate=release_second
                        if not gate.wait(15):raise RuntimeError('coordinator timeout')
                else:value=functions[kind]()
                return {'status':'committed','value':value}
            except ValidationError as e:return {'status':'rejected','messages':e.messages}
            except DatabaseError as e:return {'status':'database-error','sqlstate':getattr(e.__cause__,'sqlstate',None),'type':type(e).__name__}
            finally:connections.close_all()
        def waitblocked(waiter,blocker):
            until=time.monotonic()+8
            while time.monotonic()<until:
                with connection.cursor() as cur:
                    cur.execute('SELECT wait_event_type,wait_event,pg_blocking_pids(pid) FROM pg_stat_activity WHERE pid=%s',[waiter]); row=cur.fetchone()
                if row and row[0]=='Lock' and blocker in row[2]:return {'observed':True,'event':row[1]}
                time.sleep(.02)
            return {'observed':False}
        with ThreadPoolExecutor(max_workers=3) as pool:
            first={'edit-first':'edit','suspend-first':'suspend','checkout-first':'pay'}[scenario]
            f1=pool.submit(worker,first,True);name,pid=ids.get(timeout=10);pids={name:pid}
            if not held.wait(10):raise RuntimeError('first operation did not hold transaction')
            if scenario=='edit-first':
                f2=pool.submit(worker,'suspend');f3=pool.submit(worker,'pay')
                for _ in range(2):name,pid=ids.get(timeout=10);pids[name]=pid
                waits={'suspend_on_edit':waitblocked(pids['suspend'],pids['edit']), 'pay_on_edit':waitblocked(pids['pay'],pids['edit'])}
            elif scenario=='suspend-first':
                f2=pool.submit(worker,'edit');name,pid=ids.get(timeout=10);pids[name]=pid
                w1=waitblocked(pids['edit'],pids['suspend'])
                f3=pool.submit(worker,'pay');name,pid=ids.get(timeout=10);pids[name]=pid
                waits={'edit_on_suspend':w1,'pay_on_edit':waitblocked(pids['pay'],pids['edit'])}
            else:
                f2=pool.submit(worker,'edit');name,pid=ids.get(timeout=10);pids[name]=pid
                w1=waitblocked(pids['edit'],pids['pay'])
                f3=pool.submit(worker,'suspend',False,True);name,pid=ids.get(timeout=10);pids[name]=pid
                if not second_held.wait(10):raise RuntimeError('suspension did not hold category')
                waits={'edit_on_pay':w1,'suspend_held_concurrently':{'observed':True}}
                release_second.set()
                f3.result(timeout=15)
            release.set()
            results={first:f1.result(timeout=20)}
            remaining={'edit-first':('suspend','pay'),'suspend-first':('edit','pay'),'checkout-first':('edit','suspend')}[scenario]
            results[remaining[0]]=f2.result(timeout=20);results[remaining[1]]=f3.result(timeout=20)
        after=state(); oldcat=Product.objects.get(pk=p.pk).category_id
        checks={'distinct_connections':len(set(pids.values()))==3,'waits_observed':all(v['observed'] for v in waits.values()),
          'no_database_error':all(v['status']!='database-error' for v in results.values()),'suspension_committed':results['suspend']['status']=='committed',
          'historical_unchanged':after['history']==before['history'],'shift_unchanged':after['shift']==before['shift'],
          'one_or_zero_sales':len(after['sale'])<=1,'no_partial':(len(after['details'])==2 if after['sale'] else not after['details']),
          'rejection_preserves_stock':bool(after['sale']) or after['lots']==before['lots'],
          'rejection_preserves_draft':bool(after['sale']) or (after['draft']==before['draft'] and after['draft_lines']==before['draft_lines']),
          'rejection_preserves_counter':bool(after['sale']) or after['counter']==before['counter'],
          'suspension_active_false':not Category.objects.get(pk=b.pk).is_active}
        if scenario in ('suspend-first','checkout-first'):
            checks['edit_rejected_inactive']=results['edit']['status']=='rejected' and oldcat==a.pk
        else:checks['edit_committed']=results['edit']['status']=='committed' and oldcat==b.pk
        if scenario=='checkout-first':checks['checkout_committed_before_suspend']=results['pay']['status']=='committed' and len(after['sale'])==1
        if scenario=='suspend-first':checks['checkout_valid_or_safe_rejection']=results['pay']['status'] in ('committed','rejected')
        if scenario=='edit-first' and not after['sale']:
            checks['checkout_safely_rejected']=results['pay']['status']=='rejected'
        retry={};sale=Sale.objects.filter(draft=draft).first()
        if not sale:
            toggle_category_status(actor=actors['admin2'],category=Category.objects.get(pk=b.pk),is_active=True,expected_version=1)
            try:retry['sale']=pay();sale=Sale.objects.get(draft=draft)
            except ValidationError as e:retry['error']=e.messages
        if sale:
            replay=checkout_sale(actor=actors['seller'],draft_id=draft.pk,cash_received=Decimal('50'),idempotency_key=key)
            checks['retry_idempotent']=replay.pk==sale.pk and Sale.objects.filter(draft=draft).count()==1
            final=state();checks['one_sale_total']=len(final['sale'])==1 and final['sale'][0]['total_amount']==Decimal('23.00')
            checks['final_stock']=all(row['available_quantity']==(7 if row['product_id']==p.pk else 9) for row in final['lots'])
            checks['final_history']=final['history']==before['history']
        else:checks['retry_idempotent']=False;final=state()
        cases.append({'id':'PG-V-'+scenario,'ok':all(checks.values()),'checks':checks,'results':results,'waits':waits,'pids':pids,
          'before':before,'after_race':after,'after_retry':final,'retry':retry,
          'method':'three real services, three independent PG connections; coordinator holds completed service transaction(s) to force specific order; no synthetic row locks; no HTTP'})
    return cases
