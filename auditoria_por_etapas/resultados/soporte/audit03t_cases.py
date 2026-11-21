"""03-T controlled PostgreSQL interleavings: Django test Client + real catalog service."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Event
from unittest.mock import patch
from html.parser import HTMLParser
from django.db import connection, connections
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from cash.models import CashRegister
from cash.services import open_cash_shift
from catalog.models import Category, Product
from catalog.services import update_product, product_edit_snapshot
from identity.models import Account, Role
from inventory.models import Lot
from inventory.services import confirm_initial_load, LotInput
from sales.models import Sale, SaleLine, SaleDraft, SaleDraftLine, SaleCounter
from sales.services import add_product_to_draft, checkout_sale
from sales import views
import uuid

class Inputs(HTMLParser):
    def __init__(self): super().__init__(); self.data={}
    def handle_starttag(self,tag,attrs):
        if tag=='input':
            value=dict(attrs)
            if value.get('name'): self.data[value['name']]=value.get('value','')

def run_cases():
    actors={}
    for alias,role in [('seller','VENDEDOR'),('warehouse','ALMACENERO'),('admin','ADMIN')]:
        obj,_=Role.objects.get_or_create(code=role,defaults={'name':role})
        actors[alias]=Account.objects.create_user('t-'+alias+'@audit03.invalid',None,role=obj,display_name='AUD03 T '+alias)
    CashRegister.objects.create(code='CAJA-01')
    shift=open_cash_shift(actor=actors['seller'],opening_amount=Decimal('50.00'))
    cases=[]
    for mode in ('name','barcode','category'):
        category=Category.objects.create(name='T origen '+mode)
        destination=Category.objects.create(name='T destino '+mode)
        p=Product.objects.create(category=category,name='T P '+mode,barcode='TP-'+mode,sale_price=Decimal('8.50'))
        q=Product.objects.create(category=category,name='T Q '+mode,barcode='TQ-'+mode,sale_price=Decimal('8.50'))
        for product in (p,q):
            confirm_initial_load(actor=actors['warehouse'],product=product,lots=[LotInput('BASE',10,Decimal('2.50'),timezone.localdate()+timedelta(days=30))])
        hist_draft=add_product_to_draft(actor=actors['seller'],product_id=p.pk,quantity=1)
        history=checkout_sale(actor=actors['seller'],draft_id=hist_draft.pk,cash_received=Decimal('10.00'),idempotency_key=uuid.uuid4())
        draft=add_product_to_draft(actor=actors['seller'],product_id=p.pk,quantity=2)
        add_product_to_draft(actor=actors['seller'],product_id=q.pk,quantity=1)
        client=Client(enforce_csrf_checks=True);client.force_login(actors['seller'])
        initial=client.get(reverse('sales-checkout'));assert initial.status_code==200
        parser=Inputs();parser.feed(initial.content.decode());data=parser.data
        data.update(cash_received='100.00',discount_amount='')
        def state():
            return {'draft':list(SaleDraft.objects.filter(pk=draft.pk).values('id','status')),
                'draft_lines':list(SaleDraftLine.objects.filter(draft=draft).order_by('product_id').values('product_id','quantity','unit_price')),
                'products':list(Product.objects.filter(pk__in=[p.pk,q.pk]).order_by('pk').values('id','category_id','name','barcode','sale_price')),
                'lots':list(Lot.objects.filter(product_id__in=[p.pk,q.pk]).order_by('product_id').values('product_id','available_quantity')),
                'sales':list(Sale.objects.filter(draft=draft).values('id','total_amount','cash_received','change_given','idempotency_key')),
                'lines':list(SaleLine.objects.filter(sale__draft=draft).order_by('product_id').values('product_id','product_snapshot_name','product_snapshot_barcode','quantity','unit_price')),
                'historical':list(SaleLine.objects.filter(sale=history).values('product_id','product_snapshot_name','product_snapshot_barcode','quantity','unit_price')),
                'shift':list(type(shift).objects.filter(pk=shift.pk).values()),
                'counter':list(SaleCounter.objects.values('next_value'))}
        before=state();waiting=Event();release=Event();orig=views.checkout_sale
        def pause(*args,**kwargs):
            waiting.set()
            if not release.wait(15): raise RuntimeError('pause not released')
            return orig(*args,**kwargs)
        def submit():
            try:
                with connection.cursor() as c: c.execute('SELECT pg_backend_pid()');pid=c.fetchone()[0]
                with patch.object(views,'checkout_sale',side_effect=pause): response=client.post(reverse('sales-checkout'),data)
                return {'status':response.status_code,'location':response.get('Location'),'pid':pid,'review_message':b'revisa el resumen' in response.content.lower()},response
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(submit)
            if not waiting.wait(10):raise RuntimeError('checkout did not reach service')
            with connection.cursor() as c:c.execute('SELECT pg_backend_pid()');mutation_pid=c.fetchone()[0]
            p=Product.objects.get(pk=p.pk)
            kwargs=dict(actor=actors['admin'],product=p,name=p.name,barcode=p.barcode,sale_price=p.sale_price,
                minimum_stock=p.minimum_stock,category=destination if mode=='category' else p.category,
                expected_snapshot=product_edit_snapshot(p))
            if mode=='name':kwargs['name']='T nombre nuevo '+mode
            if mode=='barcode':kwargs['barcode']='T-NUEVO-'+mode
            updated=update_product(**kwargs)
            during=state();release.set();response,http=future.result(timeout=20)
        after=state()
        checks={'view_reached_service':waiting.is_set(),'separate_connections':response['pid']!=mutation_pid,
            'mutation_committed':during['products']!=before['products'],'history_preserved':during['historical']==before['historical'],
            'draft_unchanged_by_edit':during['draft_lines']==before['draft_lines'],
            'stock_unchanged_by_edit':during['lots']==before['lots'],
            'shift_unchanged_by_edit':during['shift']==before['shift']}
        observed={'response':response,'after':after}
        if mode in ('name','barcode'):
            checks['rejected_stale_summary']=response['status']==200 and response['review_message'] and not after['sales']
            checks['no_mutation_on_reject']=all(after[k]==during[k] for k in ('draft','draft_lines','products','lots','historical','counter','shift'))
            parser=Inputs();parser.feed(http.content.decode());retry=parser.data
            retry.update(cash_received='100.00',discount_amount='')
            result=client.post(reverse('sales-checkout'),retry)
            final=state();sale=Sale.objects.filter(draft=draft).first()
            replay=checkout_sale(actor=actors['seller'],draft_id=draft.pk,cash_received=Decimal('100.00'),idempotency_key=sale.idempotency_key) if sale else None
            checks['explicit_retry']=result.status_code==302 and len(final['sales'])==1
        else:
            final=after;sale=Sale.objects.filter(draft=draft).first()
            replay=checkout_sale(actor=actors['seller'],draft_id=draft.pk,cash_received=Decimal('100.00'),idempotency_key=sale.idempotency_key) if sale else None
            checks['sale_with_same_visible_summary']=response['status']==302 and len(final['sales'])==1
        checks['replay_idempotent']=bool(replay and replay.pk==sale.pk and Sale.objects.filter(draft=draft).count()==1)
        checks['final_stock']=all(item['available_quantity']==(7 if item['product_id']==p.pk else 9) for item in final['lots'])
        checks['final_history_preserved']=final['historical']==before['historical']
        checks['current_product_snapshot']=any(item['product_id']==p.pk and item['product_snapshot_name']==updated.name and item['product_snapshot_barcode']==updated.barcode for item in final['lines'])
        checks['two_lines_correct']=len(final['lines'])==2 and sum(x['quantity'] for x in final['lines'])==3
        checks['one_sale_total']=len(final['sales'])==1 and final['sales'][0]['total_amount']==Decimal('25.50')
        observed['final']=final
        cases.append({'id':'PG-T-'+mode,'ok':all(checks.values()),'checks':checks,'observed':observed,'before':before,'after_mutation':during,
            'method':'Django test Client with CSRF and real administrator catalog service on independent PostgreSQL connection, paused before checkout service, no HTTP socket or extra row locks'})
    return cases
