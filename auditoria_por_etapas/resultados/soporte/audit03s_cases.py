"""03-S: real Django HTTP requests, distinct DB connections, controlled view-to-service pause."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from decimal import Decimal
from threading import Event
from unittest.mock import patch
from django.db import connection,connections
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from cash.models import CashRegister
from cash.services import open_cash_shift
from catalog.models import Category,Product
from identity.models import Account,Role
from inventory.models import Lot
from inventory.services import confirm_initial_load,LotInput
from sales.models import Sale,SaleLine,SaleDraft,SaleDraftLine,SaleCounter
from sales.services import add_product_to_draft
from sales import views

def run_cases():
    actors={}
    for alias,role in [('seller','VENDEDOR'),('warehouse','ALMACENERO')]:
        obj,_=Role.objects.get_or_create(code=role,defaults={'name':role})
        actors[alias]=Account.objects.create_user('s-'+alias+'@audit03.invalid',None,role=obj,display_name='AUD03 S '+alias)
    CashRegister.objects.create(code='CAJA-01')
    open_cash_shift(actor=actors['seller'],opening_amount=Decimal('50.00'))
    cases=[]
    for mode in ('different-total','same-total','price-refresh'):
        category=Category.objects.create(name='S categoría '+mode)
        p=Product.objects.create(category=category,name='S P '+mode,barcode='SP-'+mode,sale_price=Decimal('8.50'))
        q=Product.objects.create(category=category,name='S Q '+mode,barcode='SQ-'+mode,sale_price=Decimal('8.50'))
        for product in (p,q):
            confirm_initial_load(actor=actors['warehouse'],product=product,lots=[LotInput('BASE',10,Decimal('2.50'),timezone.localdate()+timedelta(days=30))])
        draft=add_product_to_draft(actor=actors['seller'],product_id=p.pk,quantity=2)
        add_product_to_draft(actor=actors['seller'],product_id=q.pk,quantity=1)
        if mode=='price-refresh':
            Product.objects.filter(pk=p.pk).update(sale_price=Decimal('9.50'))
        a=Client(enforce_csrf_checks=True);a.force_login(actors['seller'])
        initial=a.get(reverse('sales-checkout'));assert initial.status_code==200
        # Test client does not populate context without Django test environment.
        from html.parser import HTMLParser
        class Inputs(HTMLParser):
            def __init__(self): super().__init__(); self.data={}
            def handle_starttag(self,tag,attrs):
                if tag=='input':
                    value=dict(attrs)
                    if value.get('name'): self.data[value['name']]=value.get('value','')
        parser=Inputs();parser.feed(initial.content.decode());data=parser.data
        data.update(cash_received='100.00',discount_amount='')
        b=Client(enforce_csrf_checks=True);b.cookies=a.cookies.copy()
        lines={x.product_id:x for x in SaleDraftLine.objects.filter(draft=draft)}
        def state():
            return {'draft':list(SaleDraft.objects.filter(pk=draft.pk).values('id','status')),
                'draft_lines':list(SaleDraftLine.objects.filter(draft=draft).order_by('product_id').values('product_id','quantity','unit_price')),
                'products':list(Product.objects.filter(pk__in=[p.pk,q.pk]).order_by('pk').values('id','name','barcode','sale_price')),
                'lots':list(Lot.objects.filter(product_id__in=[p.pk,q.pk]).order_by('product_id').values('product_id','available_quantity')),
                'sales':list(Sale.objects.filter(draft=draft).values('id','total_amount','cash_received','change_given','idempotency_key')),
                'lines':list(SaleLine.objects.filter(sale__draft=draft).order_by('product_id').values('product_id','product_snapshot_name','product_snapshot_barcode','quantity','unit_price')),
                'counter':list(SaleCounter.objects.values('next_value'))}
        before=state();waiting=Event();release=Event();orig=views.checkout_sale
        def pause(*args,**kwargs):
            waiting.set()
            if not release.wait(15):raise RuntimeError('pause not released')
            return orig(*args,**kwargs)
        def submit():
            try:
                with connection.cursor() as c:c.execute('SELECT pg_backend_pid()');pid=c.fetchone()[0]
                with patch.object(views,'checkout_sale',side_effect=pause):
                    result=a.post(reverse('sales-checkout'),data)
                return {'status':result.status_code,'location':result.get('Location'),'pid':pid,'review_message':b'revisa el resumen' in result.content.lower()}, result
            finally:connections.close_all()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future=pool.submit(submit)
            if not waiting.wait(10):raise RuntimeError('checkout did not reach service; view comparison did not pass')
            with connection.cursor() as c:c.execute('SELECT pg_backend_pid()');mutation_pid=c.fetchone()[0]
            def update(product,qty):
                return b.post(reverse('sales-line-update',args=(lines[product.pk].pk,)),{'quantity':str(qty),'csrfmiddlewaretoken':data['csrfmiddlewaretoken']}).status_code
            statuses=[update(p,3)] if mode=='different-total' else [update(q,2)] if mode=='price-refresh' else [update(p,1),update(q,2)]
            during=state();release.set();response, http_response=future.result(timeout=20)
        after=state()
        checks={'view_reached_service':waiting.is_set(),'csrf_mutations_accepted':all(x==302 for x in statuses),'separate_connections':response['pid']!=mutation_pid,
                'changed_draft':during['draft_lines']!=before['draft_lines'],'original_form_subtotal':'25.50'==str(data['expected_subtotal'])}
        observed={'response':response,'mutation_statuses':statuses,'sale_recorded_after_changed_summary':len(after['sales'])==1,
                  'same_subtotal': mode=='same-total','sale_total':str(after['sales'][0]['total_amount']) if after['sales'] else None,
                  'sale_quantities':[{ 'product_id':str(x['product_id']),'quantity':x['quantity']} for x in after['lines']]}
        if response['status']==200 and not after['sales']:
            parser=Inputs();parser.feed(http_response.content.decode());retry_data=parser.data
            retry_data.update(cash_received='100.00',discount_amount='')
            retried=a.post(reverse('sales-checkout'),retry_data)
            first_retry_status=retried.status_code
            second_status=None
            if retried.status_code==200:
                parser=Inputs();parser.feed(retried.content.decode());retry_data=parser.data
                retry_data.update(cash_received='100.00',discount_amount='')
                retried=a.post(reverse('sales-checkout'),retry_data);second_status=retried.status_code
            sale=Sale.objects.filter(draft=draft).first()
            from sales.services import checkout_sale
            replay=checkout_sale(actor=actors['seller'],draft_id=draft.pk,cash_received=Decimal('100.00'),idempotency_key=sale.idempotency_key) if sale else None
            final=state()
            observed['retry']={'status':retried.status_code,'first_retry_status':first_retry_status,'extra_confirmation_status':second_status,'one_sale':len(final['sales'])==1,'same_sale_on_replay':bool(replay and replay.pk==sale.pk),
                               'total':str(sale.total_amount) if sale else None,'after':final}
        retry=observed.get('retry',{})
        checks.update(rejected_stale_summary=response['status']==200 and response['review_message'] and not after['sales'],
            preserves_draft_and_stock=after['draft_lines']==during['draft_lines'] and after['lots']==during['lots'] and after['counter']==during['counter'],
            explicit_retry_once=retry.get('one_sale',False) and retry.get('same_sale_on_replay',False) and retry.get('status')==302,
            price_refresh_extra_review=(mode!='price-refresh' or retry.get('first_retry_status')==200))
        cases.append({'id':'PG-S-'+mode,'ok':all(checks.values()),'checks':checks,'observed':observed,'before':before,'after_mutation':during,'after_checkout':after,
                      'method':'real Django Client HTTP view with CSRF, paused at call to actual checkout service, separate connections, no additional locks'})
        if SaleDraft.objects.filter(pk=draft.pk,status='ACTIVE').exists():
            from sales.services import discard_active_draft
            discard_active_draft(actor=actors['seller'])
    return cases

