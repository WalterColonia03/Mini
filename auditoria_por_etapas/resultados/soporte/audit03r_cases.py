"""03-R stale prices under concurrent checkout/edit on isolated PostgreSQL only."""
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from queue import Queue
import time
from django.db import connection, connections, DatabaseError
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
from sales.models import Sale, SaleLine, SaleDraft, SaleDraftLine, SaleCounter
from sales.services import add_product_to_draft, checkout_sale

def run_cases():
    actors={}
    for alias,code in [('admin','ADMIN'),('warehouse','ALMACENERO'),('seller','VENDEDOR')]:
        role,_=Role.objects.get_or_create(code=code,defaults={'name':code})
        actors[alias]=Account.objects.create_user('r-'+alias+'@audit03.invalid',None,role=role,display_name='AUD03 R '+alias)
    CashRegister.objects.create(code='CAJA-01')
    shift=open_cash_shift(actor=actors['seller'],opening_amount=Decimal('50.00'))
    cases=[]
    for mode in ('reclassify','price-again','two-checkouts'):
        a=Category.objects.create(name='R A '+mode)
        b=Category.objects.create(name='R B '+mode)
        p=Product.objects.create(category=a,name='R P '+mode,barcode='RP-'+mode,sale_price=Decimal('8.50'))
        q=Product.objects.create(category=b,name='R Q '+mode,barcode='RQ-'+mode,sale_price=Decimal('6.00'))
        for item in (p,q):
            confirm_initial_load(actor=actors['warehouse'],product=item,lots=[LotInput('BASE',10,Decimal('2.50'),timezone.localdate()+timedelta(days=30))])
        draft=add_product_to_draft(actor=actors['seller'],product_id=p.pk,quantity=2)
        add_product_to_draft(actor=actors['seller'],product_id=q.pk,quantity=1)
        def edit(product, *, price=None, category=None):
            current=Product.objects.get(pk=product.pk); snap=product_edit_snapshot(current)
            changed=update_product(actor=actors['admin'],product=current,name=snap['name'],barcode=snap['barcode'],sale_price=price or snap['sale_price'],minimum_stock=snap['minimum_stock'],category=category or current.category,expected_snapshot=snap)
            return {'category':str(changed.category_id),'price':str(changed.sale_price)}
        edit(p,price=Decimal('9.00'))
        key=uuid4()
        def pay():
            sale=checkout_sale(actor=actors['seller'],draft_id=draft.pk,cash_received=Decimal('40.00'),idempotency_key=key)
            return {'id':str(sale.pk),'total':str(sale.total_amount)}
        def state():
            return {'products':list(Product.objects.filter(pk__in=[p.pk,q.pk]).order_by('pk').values('id','category_id','name','barcode','sale_price')),
              'lots':list(Lot.objects.filter(product_id__in=[p.pk,q.pk]).order_by('product_id').values('product_id','available_quantity','initial_quantity')),
              'draft':list(SaleDraft.objects.filter(pk=draft.pk).values('status')),
              'draft_lines':list(SaleDraftLine.objects.filter(draft=draft).order_by('product_id').values('product_id','quantity','unit_price')),
              'sales':list(Sale.objects.filter(draft=draft).values('id','total_amount','cash_received','change_given')),
              'lines':list(SaleLine.objects.filter(sale__draft=draft).order_by('product_id').values('product_id','product_snapshot_name','product_snapshot_barcode','quantity','unit_price')),
              'counter':list(SaleCounter.objects.values('next_value'))}
        before=state()
        if mode!='two-checkouts':
            race=contest(lambda:edit(q,category=a) if mode=='reclassify' else edit(p,price=Decimal('10.00')),pay)
            refresh=race['contender']
            observed=race['lock_observed'] and race['distinct_connections']
        else:
            locked=Event();release=Event();ids=Queue()
            def hook(execute,sql,params,many,context):
                result=execute(sql,params,many,context)
                if 'sales_saledraftline' in sql and 'FOR UPDATE' in sql:
                    locked.set()
                    if not release.wait(12):raise RuntimeError('refresh not released')
                return result
            def worker(which):
                try:
                    with connection.cursor() as c:
                        c.execute('SELECT pg_backend_pid()');ids.put((which,c.fetchone()[0]))
                    if which=='first':
                        with connection.execute_wrapper(hook):value=pay()
                    else:value=pay()
                    return {'status':'committed','value':value}
                except ValidationError as e:return {'status':'rejected','messages':e.messages}
                except DatabaseError as e:return {'status':'database-error','type':type(e).__name__,'sqlstate':getattr(e.__cause__,'sqlstate',None)}
                finally:connections.close_all()
            with ThreadPoolExecutor(max_workers=2) as pool:
                one=pool.submit(worker,'first')
                if not locked.wait(10):raise RuntimeError('first refresh did not reach locked draft lines')
                two=pool.submit(worker,'second'); pids=dict(ids.get(timeout=10) for _ in range(2));observed=False;evt=None
                deadline=time.monotonic()+8
                while time.monotonic()<deadline and not two.done():
                    with connection.cursor() as c:
                        c.execute('SELECT wait_event_type,wait_event,pg_blocking_pids(pid) FROM pg_stat_activity WHERE pid=%s',[pids['second']]);row=c.fetchone()
                    if row and row[0]=='Lock' and pids['first'] in row[2]:observed=True;evt=row[1];break
                    time.sleep(.02)
                release.set(); first=one.result(timeout=20);second=two.result(timeout=20)
            race={'first':first,'second':second,'lock_observed':observed,'wait_event':evt,'distinct_connections':pids['first']!=pids['second'],'instrumentation':'pause after actual refresh draft-line FOR UPDATE, before product locks; no additional row locks'}
            refresh=first
        middle=state()
        expected=Decimal('10.00') if mode=='price-again' else Decimal('9.00')
        price_rows=[line for line in middle['draft_lines'] if line['product_id']==p.pk]
        checks={'real_wait':observed,'refresh_rejected':refresh['status']=='rejected',
           'message':any('precio' in m.lower() for m in refresh.get('messages',[])),
           'refreshed_to_latest':len(price_rows)==1 and price_rows[0]['unit_price']==expected,
           'no_sale_or_lot_change':middle['sales']==before['sales'] and middle['lines']==before['lines'] and middle['lots']==before['lots'],
           'draft_active':middle['draft'][0]['status']=='ACTIVE','counter_unchanged':middle['counter']==before['counter']}
        if mode=='two-checkouts':checks['both_rejected']=race['second']['status']=='rejected'
        try:
            result=pay(); repeat=pay(); after=state(); sale=Sale.objects.get(pk=result['id'])
            checks.update(retry_success=True,idempotent=result==repeat,one_sale=len(after['sales'])==1,
              correct_total=sale.total_amount==expected*2+Decimal('6.00'), correct_stock=sorted(x['available_quantity'] for x in after['lots'])==[8,9],
              snapshot_correct=len(after['lines'])==2 and any(x['product_id']==p.pk and x['unit_price']==expected for x in after['lines']))
            retry={'sale':result,'same_sale':result==repeat}
        except Exception as e:
            checks['retry_success']=False;retry={'exception':type(e).__name__};after=state()
        cases.append({'id':'PG-R-'+mode,'ok':all(checks.values()),'checks':checks,'race':race,'before':before,'after_race':middle,'after_retry':after,'retry':retry})
        if SaleDraft.objects.filter(pk=draft.pk,status='ACTIVE').exists():
            from sales.services import discard_active_draft
            discard_active_draft(actor=actors['seller'])
    return cases
