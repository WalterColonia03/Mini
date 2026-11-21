"""03-Q: multiproduct checkout and crossed category edits on private PG only."""
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from queue import Queue
from threading import Event
import time
from django.db import connection, connections, transaction, DatabaseError
from django.core.exceptions import ValidationError
from django.utils import timezone
from audit03l_concurrency import contest
from catalog.models import Category, Product
from catalog.services import update_product, product_edit_snapshot
from identity.models import Account, Role
from inventory.models import Lot
from inventory.services import confirm_initial_load, LotInput
from cash.models import CashRegister
from cash.services import open_cash_shift
from sales.models import Sale, SaleLine, SaleDraft
from sales.services import add_product_to_draft, checkout_sale

def run_cases():
    actors={}
    for alias,code in [('admin','ADMIN'),('warehouse','ALMACENERO'),('seller','VENDEDOR')]:
        role,_=Role.objects.get_or_create(code=code,defaults={'name':code})
        actors[alias]=Account.objects.create_user('q-'+alias+'@audit03.invalid',None,role=role,display_name='Q '+alias)
    CashRegister.objects.create(code='CAJA-01')
    shift=open_cash_shift(actor=actors['seller'],opening_amount=Decimal('50.00'))
    cases=[]
    for scenario in ('edit-first','checkout-first','natural-cycle','edit-code','crossed-three'):
        a=Category.objects.create(name='Q A '+scenario)
        b=Category.objects.create(name='Q B '+scenario)
        p=Product.objects.create(category=a,name='Q P '+scenario,barcode='QP-'+scenario,sale_price=Decimal('8.50'))
        q=Product.objects.create(category=b,name='Q Q '+scenario,barcode='QQ-'+scenario,sale_price=Decimal('6.00'))
        for product in (p,q):
            confirm_initial_load(actor=actors['warehouse'],product=product,lots=[LotInput('BASE',10,Decimal('2.50'),timezone.localdate()+timedelta(days=30))])
        draft=add_product_to_draft(actor=actors['seller'],product_id=p.pk,quantity=2)
        add_product_to_draft(actor=actors['seller'],product_id=q.pk,quantity=1)
        snap=product_edit_snapshot(q)
        key=uuid4()
        def edit():
            changed=update_product(actor=actors['admin'],product=Product.objects.get(pk=q.pk),name=(snap['name']+' MOD' if scenario=='edit-code' else snap['name']),barcode=(snap['barcode']+'-NEW' if scenario=='edit-code' else snap['barcode']),sale_price=snap['sale_price'],minimum_stock=snap['minimum_stock'],category=Category.objects.get(pk=a.pk),expected_snapshot=snap)
            return {'category':str(changed.category_id)}
        def pay():
            sale=checkout_sale(actor=actors['seller'],draft_id=draft.pk,cash_received=Decimal('30.00'),idempotency_key=key)
            return {'id':str(sale.pk),'total':str(sale.total_amount)}
        def state():
            return {'products':list(Product.objects.filter(pk__in=[p.pk,q.pk]).order_by('pk').values('id','category_id','name','barcode','sale_price','minimum_stock','is_active')),
                    'lots':list(Lot.objects.filter(product_id__in=[p.pk,q.pk]).order_by('product_id').values('product_id','available_quantity','initial_quantity','unit_cost')),
                    'draft':list(SaleDraft.objects.filter(pk=draft.pk).values('status')),
                    'sales':list(Sale.objects.filter(draft=draft).values('id','total_amount','cash_received','change_given')),
                    'lines':list(SaleLine.objects.filter(sale__draft=draft).order_by('product_id').values('product_id','product_snapshot_name','product_snapshot_barcode','quantity','unit_price'))}
        before=state()
        if scenario in ('edit-first','checkout-first','edit-code'):
            race=contest(edit,pay) if scenario in ('edit-first','edit-code') else contest(pay,edit)
        elif scenario == 'crossed-three':
            ready=Queue();release=Event();ids=Queue()
            p_snapshot=product_edit_snapshot(p)
            def edit_p():
                changed=update_product(actor=actors['admin'],product=Product.objects.get(pk=p.pk),name=p_snapshot['name'],barcode=p_snapshot['barcode'],sale_price=p_snapshot['sale_price'],minimum_stock=p_snapshot['minimum_stock'],category=Category.objects.get(pk=b.pk),expected_snapshot=p_snapshot)
                return {'category':str(changed.category_id)}
            def hook(execute,sql,params,many,context):
                if 'catalog_category' in sql and 'FOR UPDATE' in sql and sql.lstrip().upper().startswith('SELECT'):
                    ready.put(True)
                    if not release.wait(12):raise RuntimeError('coordinator did not release edits')
                return execute(sql,params,many,context)
            def invoke(fn,kind):
                try:
                    with connection.cursor() as cur:
                        cur.execute('SELECT pg_backend_pid()');ids.put((kind,cur.fetchone()[0]))
                    if kind in ('editP','editQ'):
                        with connection.execute_wrapper(hook):value=fn()
                    else:value=fn()
                    return {'status':'committed','value':value}
                except ValidationError as e:return {'status':'rejected','messages':e.messages}
                except DatabaseError as e:return {'status':'database-error','type':type(e).__name__,'sqlstate':getattr(e.__cause__,'sqlstate',None)}
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=3) as pool:
                f1=pool.submit(invoke,edit_p,'editP');f2=pool.submit(invoke,edit,'editQ')
                ready.get(timeout=10);ready.get(timeout=10)
                f3=pool.submit(invoke,pay,'pay')
                pids=dict(ids.get(timeout=10) for _ in range(3));wait_seen=False;event=None
                deadline=time.monotonic()+8
                while time.monotonic()<deadline and not f3.done():
                    with connection.cursor() as cur:
                        cur.execute('SELECT wait_event_type,wait_event,pg_blocking_pids(pid) FROM pg_stat_activity WHERE pid=%s',[pids['pay']]);row=cur.fetchone()
                    if row and row[0]=='Lock' and any(pids[k] in row[2] for k in ('editP','editQ')):wait_seen=True;event=row[1];break
                    time.sleep(.02)
                release.set()
                r1=f1.result(timeout=20);r2=f2.result(timeout=20);r3=f3.result(timeout=20)
            race={'editP':r1,'edit':r2,'checkout':r3,'checkout_waited_for_edits':wait_seen,'wait_event':event,'distinct_connections':len(set(pids.values()))==3,'auxiliary':'pause before real category queries; no extra database row locks'}
        elif scenario == 'natural-cycle':
            # Pause only the real edit immediately before SELECT category FOR UPDATE.
            # It has already locked Q via the optimistic conditional update.
            held=Event(); release_edit=Event(); ids=Queue()
            def hook(execute, sql, params, many, context):
                if 'catalog_category' in sql and 'FOR UPDATE' in sql and sql.lstrip().upper().startswith('SELECT'):
                    held.set()
                    if not release_edit.wait(12):raise RuntimeError('coordinator did not release edit')
                return execute(sql, params, many, context)
            def invoke(fn, kind):
                try:
                    with connection.cursor() as cur:
                        cur.execute('SELECT pg_backend_pid()');ids.put((kind,cur.fetchone()[0]))
                    if kind=='edit':
                        with connection.execute_wrapper(hook): result=fn()
                    else: result=fn()
                    return {'status':'committed','value':result}
                except ValidationError as e:return {'status':'rejected','messages':e.messages}
                except DatabaseError as e:return {'status':'database-error','type':type(e).__name__,'sqlstate':getattr(e.__cause__,'sqlstate',None)}
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=2) as pool:
                fe=pool.submit(invoke,edit,'edit')
                if not held.wait(10):raise RuntimeError('edit did not lock Q and reach category')
                fp=pool.submit(invoke,pay,'pay')
                pids=dict(ids.get(timeout=10) for _ in range(2));wait_seen=False;event=None
                deadline=time.monotonic()+8
                while time.monotonic()<deadline and not fp.done():
                    with connection.cursor() as cur:
                        cur.execute('SELECT wait_event_type,wait_event,pg_blocking_pids(pid) FROM pg_stat_activity WHERE pid=%s',[pids['pay']]);row=cur.fetchone()
                    if row and row[0]=='Lock' and pids['edit'] in row[2]:wait_seen=True;event=row[1];break
                    time.sleep(.02)
                release_edit.set()
                rp=fp.result(timeout=20);re=fe.result(timeout=20)
            race={'checkout':rp,'edit':re,'checkout_waited_for_edit':wait_seen,'wait_event':event,'distinct_connections':pids['pay']!=pids['edit'],'auxiliary':'pause before edit category query, no auxiliary database row locks'}
        else:
            # Hold exactly P and A in the checkout transaction before calling real checkout,
            # mirroring locks its joined SELECT can acquire before reaching Q. Auxiliary
            # lock makes a concrete interleaving; it is not a claim of natural frequency.
            locked=Event(); proceed=Event(); ids=Queue()
            def worker_pay():
                try:
                    with connection.cursor() as cur:
                        cur.execute('SELECT pg_backend_pid()'); ids.put(('pay',cur.fetchone()[0]))
                    with transaction.atomic():
                        with connection.cursor() as cur:
                            cur.execute('SELECT p.id FROM catalog_product p JOIN catalog_category c ON c.id=p.category_id WHERE p.id=%s FOR UPDATE OF p,c',[p.pk]);cur.fetchone()
                        locked.set()
                        if not proceed.wait(10):raise RuntimeError('coordinator did not release checkout')
                        result=pay()
                    return {'status':'committed','value':result}
                except ValidationError as e:return {'status':'rejected','messages':e.messages}
                except DatabaseError as e:return {'status':'database-error','type':type(e).__name__,'sqlstate':getattr(e.__cause__,'sqlstate',None)}
                finally:connections.close_all()
            def worker_edit():
                try:
                    with connection.cursor() as cur:
                        cur.execute('SELECT pg_backend_pid()'); ids.put(('edit',cur.fetchone()[0]))
                    if not locked.wait(10):raise RuntimeError('checkout did not lock P/A')
                    result=edit()
                    return {'status':'committed','value':result}
                except ValidationError as e:return {'status':'rejected','messages':e.messages}
                except DatabaseError as e:return {'status':'database-error','type':type(e).__name__,'sqlstate':getattr(e.__cause__,'sqlstate',None)}
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=2) as pool:
                fp=pool.submit(worker_pay);fe=pool.submit(worker_edit)
                pids=dict(ids.get(timeout=10) for _ in range(2)); wait_seen=False; wait_event=None
                deadline=time.monotonic()+8
                while time.monotonic()<deadline and not fe.done():
                    with connection.cursor() as cur:
                        cur.execute('SELECT wait_event_type,wait_event,pg_blocking_pids(pid) FROM pg_stat_activity WHERE pid=%s',[pids['edit']]); row=cur.fetchone()
                    if row and row[0]=='Lock' and pids['pay'] in row[2]:wait_seen=True;wait_event=row[1];break
                    time.sleep(.02)
                proceed.set()
                rp=fp.result(timeout=20);re=fe.result(timeout=20)
            race={'checkout':rp,'edit':re,'edit_waited_for_checkout':wait_seen,'wait_event':wait_event,'distinct_connections':pids['pay']!=pids['edit'],'auxiliary':'checkout transaction prelocks P and category A, then invokes checkout_sale'}
        middle=state()
        # Complete each safe rejection or deadlock victim explicitly after checking conservation.
        retry={}
        if not Sale.objects.filter(draft=draft).exists():
            retry['pay']=pay()
            retry['same_idempotency']=pay()==retry['pay']
        if Product.objects.get(pk=q.pk).category_id!=a.pk:
            retry['edit']=edit()
        after=state()
        sale=Sale.objects.get(draft=draft)
        checks={'distinct_connections':race['distinct_connections'],
                'no_database_error':(race['checkout']['status']!='database-error' and race['edit']['status']!='database-error' and (scenario!='crossed-three' or race['editP']['status']!='database-error')) if scenario in ('natural-cycle','crossed-three') else True,
                'wait_observed':(race['edit_waited_for_checkout'] if scenario=='forced-cycle' else race['checkout_waited_for_edit'] if scenario=='natural-cycle' else race['checkout_waited_for_edits'] if scenario=='crossed-three' else race['lock_observed']),
                'one_sale':len(after['sales'])==1,'amount':str(sale.total_amount)=='23.00' and str(sale.change_given)=='7.00',
                'stock':sorted(row['available_quantity'] for row in after['lots'])==[8,9],
                'details':len(after['lines'])==2 and sorted(row['quantity'] for row in after['lines'])==[1,2],
                'category_updated':Product.objects.get(pk=q.pk).category_id==a.pk and (scenario!='crossed-three' or Product.objects.get(pk=p.pk).category_id==b.pk),
                'retry_idempotent':retry.get('same_idempotency',True),
                'current_sale_snapshot':scenario!='edit-code' or any(row['product_id']==q.pk and row['product_snapshot_name']==snap['name']+' MOD' and row['product_snapshot_barcode']==snap['barcode']+'-NEW' for row in after['lines']),
                'no_partial_sale':len(middle['sales']) in (0,1) and (len(middle['lines'])==2 if middle['sales'] else len(middle['lines'])==0)}
        cases.append({'id':'PG-Q-'+scenario,'ok':all(checks.values()),'checks':checks,'race':race,'before':before,'after_race':middle,'after_retry':after,'retry':retry})
    return cases
