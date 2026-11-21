"""Kardex en Chrome real y SQLite temporal; fixtures explícitas de movimientos."""
import argparse
import importlib.util
import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('audit14d',HERE.parents[1]/'14-D-20261113/navegador/recorrido.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
original_prepare=base.prepare
base.ACTORS={'ADMIN':'Administración 14H2','ALMACENERO':'Almacén 14H2','VENDEDOR':'Venta 14H2'}
FIXTURE={};FINAL=False

def prepare(db,password):
    original_prepare(db,password)
    from django.db import connection
    from django.utils import timezone
    from catalog.models import Category,Product
    from identity.models import Account
    from inventory.models import Supplier,Lot,InitialInventoryLoad
    from inventory.services import confirm_initial_load,register_stock_entry,write_off_stock,register_physical_adjustment,LotInput
    from cash.models import CashRegister,CashShift
    from sales.services import add_product_to_draft,checkout_sale
    today=timezone.localdate();day=today-timedelta(days=1)
    moment=lambda hour:datetime.combine(day,time(hour),tzinfo=ZoneInfo('America/Lima'))
    category=Category.objects.create(name='Familia 14H2')
    worker=Account.objects.get(email='almacenero@example.invalid')
    admin=Account.objects.get(email='admin@example.invalid');seller=Account.objects.get(email='vendedor@example.invalid')
    supplier=Supplier.objects.create(name='Proveedor 14H2',ruc='20000000014')
    products=[Product.objects.create(name=name,category=category,barcode='INT-H2-'+str(i),sale_price=Decimal('10'))
        for i,name in enumerate(('Secuencia 14H2','Páginas 14H2','Legado 14H2'))]
    product,pages,legacy=products
    with patch('django.utils.timezone.now',return_value=moment(9)):
        confirm_initial_load(actor=worker,product=product,supplier=supplier,lots=[LotInput('INICIAL',10,Decimal('3'),today+timedelta(days=30))])
        shift=CashShift.objects.create(cash_register=CashRegister.objects.first(),seller=seller,opening_amount=100)
    for hour,qty,cost in ((10,10,'6'),(11,5,'8')):
        with patch('django.utils.timezone.now',return_value=moment(hour)):
            receipt=register_stock_entry(actor=worker,product=product,supplier=supplier,
                lots=[LotInput('C',qty,Decimal(cost),today+timedelta(days=60))])
    with patch('django.utils.timezone.now',return_value=moment(12)):
        draft=add_product_to_draft(actor=seller,product_id=product.pk,quantity=22)
        checkout_sale(actor=seller,draft_id=draft.pk,cash_received=Decimal('220'),idempotency_key=uuid.uuid4())
    with patch('django.utils.timezone.now',return_value=moment(13)):
        write_off_stock(actor=worker,lot=receipt.lines.get().lot,quantity=1,reason='ROBO',notes='Faltante ficticio 14H2')
    with patch('django.utils.timezone.now',return_value=moment(8)):
        load=confirm_initial_load(actor=worker,product=pages,lots=[LotInput('PAGINA',50,Decimal('2'),today+timedelta(days=30))])
    for i in range(26):
        with patch('django.utils.timezone.now',return_value=moment(9)):
            register_physical_adjustment(actor=admin,lot=load.lots.get(),delta=1,reason=f'Recuento ficticio {i}')
    header=InitialInventoryLoad.objects.create(product=legacy,responsible=worker)
    Lot.objects.create(product=legacy,initial_load=header,number='LEGADO',initial_quantity=10,available_quantity=5,unit_cost=Decimal('3'),expiration_date=today+timedelta(days=30))
    FIXTURE.update(product=str(product.pk),pages=str(pages.pk),legacy=str(legacy.pk),day=day.isoformat(),
        last_lot=str(receipt.lines.get().lot_id),description='Maestros y movimientos por ORM/servicios con instantes controlados; navegación/filtros/roles por UI.')
    connection.close()

class Journey(base.Journey):
    def run(self,browser,password):
        a=self.connect(browser,'ADMIN',password);w=self.connect(browser,'ALMACENERO',password);v=self.connect(browser,'VENDEDOR',password)
        base.save(self.out/'fixture.json',FIXTURE)
        path=f"/inventario/productos/{FIXTURE['product']}/movimientos/"
        pages=f"/inventario/productos/{FIXTURE['pages']}/movimientos/"
        legacy=f"/inventario/productos/{FIXTURE['legacy']}/movimientos/"
        period={'desde':FIXTURE['day']+'T10:01','hasta':FIXTURE['day']+'T13:00','tipo':'venta'}
        base.link(a,'/inventario/stock/')
        a.get_by_role('row').filter(has_text='Secuencia 14H2').get_by_role('link',name='Ver movimientos').click()
        original=self.observe('01-historia-completa','ADMIN',a,photo=True)
        if not FINAL:
            a.goto(self.base+path+'?'+urlencode(period))
            self.observe('02-filtro-ignorado','ADMIN',a,same=original,photo=True)
            ignored=a.locator('table tbody tr').count()!=1
            a.goto(self.base+pages+'?tipo=ajuste&page=2')
            self.observe('03-pagina-ignorada','ADMIN',a,same=original,photo=True)
            base.save(self.out/'comparaciones.json',dict(filtro_ignorado=ignored,
                sin_saldo=a.get_by_role('columnheader',name='Saldo',exact=True).count()==0,
                sin_paginacion=a.locator('table tbody tr').count()>25))
            return
        assert a.locator('tbody tr [data-testid="movement-balance"]').all_inner_texts()==['10','20','25','3','2']
        assert a.get_by_test_id('opening-balance').inner_text()=='0'
        assert a.get_by_test_id('closing-balance').inner_text()=='2'
        for name,value in period.items():
            base.selector(a,name).select_option(value) if name=='tipo' else base.fill(a,name,value)
        base.button(a,'Aplicar filtros')
        self.observe('02-solo-venta','ADMIN',a,lambda s,t:a.get_by_test_id('opening-balance').inner_text()=='20' and a.get_by_test_id('closing-balance').inner_text()=='2' and a.get_by_test_id('filtered-delta').inner_text()=='-22',same=original,photo=True)
        assert a.locator('tbody tr').count()==1 and a.get_by_test_id('movement-balance').inner_text()=='3'
        a.reload();self.observe('03-recarga-filtro','ADMIN',a,same=original)
        a.get_by_role('link',name='Limpiar filtros').click()
        base.fill(a,'desde',period['desde']);base.button(a,'Aplicar filtros')
        self.observe('04-periodo-incompleto','ADMIN',a,lambda s,t:'Complete Desde y Hasta' in t,same=original,photo=True)
        a.goto(self.base+path+'?'+urlencode({'desde':period['hasta'],'hasta':period['desde']}))
        self.observe('05-periodo-invertido','ADMIN',a,lambda s,t:'Desde no puede ser posterior' in t,same=original)
        for key,query,message in [('06-tipo-invalido',{'tipo':'sql'},'Escoja una opción válida'),
                ('07-pagina-invalida',{'page':'0'},'Página debe ser un entero'),
                ('08-pagina-fuera',{'page':'999'},'La página solicitada no existe')]:
            a.goto(self.base+path+'?'+urlencode(query));self.observe(key,'ADMIN',a,lambda s,t:message in t,same=original,photo=True)
        a.goto(self.base+path+'?tipo=venta&tipo=merma')
        self.observe('09-parametro-repetido','ADMIN',a,lambda s,t:'No repita el parámetro tipo' in t,same=original)
        tomorrow=(datetime.fromisoformat(FIXTURE['day'])+timedelta(days=2)).date().isoformat()
        a.goto(self.base+path+'?'+urlencode({'desde':tomorrow+'T00:00','hasta':tomorrow+'T23:59'}))
        self.observe('10-periodo-vacio','ADMIN',a,lambda s,t:'No hay movimientos coincidentes' in t and a.get_by_test_id('opening-balance').inner_text()=='2' and a.get_by_test_id('closing-balance').inner_text()=='2',same=original,photo=True)
        a.goto(self.base+pages+'?'+urlencode({'tipo':'ajuste','desde':FIXTURE['day']+'T09:00','hasta':FIXTURE['day']+'T09:00'}))
        first=a.locator('tbody tr[data-event-id]').evaluate_all('rows=>rows.map(r=>r.dataset.eventId)')
        self.observe('11-pagina-uno','ADMIN',a,lambda s,t:len(first)==25 and a.get_by_test_id('filtered-count').inner_text()=='26' and a.get_by_test_id('filtered-delta').inner_text()=='+26' and a.get_by_test_id('opening-balance').inner_text()=='50',same=original,photo=True)
        a.get_by_role('link',name='Siguiente').click()
        second=a.locator('tbody tr[data-event-id]').evaluate_all('rows=>rows.map(r=>r.dataset.eventId)')
        self.observe('12-pagina-dos','ADMIN',a,lambda s,t:len(second)==1 and a.get_by_test_id('movement-balance').inner_text()=='76' and a.get_by_test_id('filtered-delta').inner_text()=='+26',same=original,photo=True)
        assert not set(first)&set(second) and first+second==sorted(first+second)
        assert base.selector(a,'desde').input_value()==FIXTURE['day']+'T09:00'
        a.get_by_role('link',name='Anterior').click()
        self.observe('13-volver-pagina','ADMIN',a,lambda s,t:a.locator('tbody tr[data-event-id]').evaluate_all('rows=>rows.map(r=>r.dataset.eventId)')==first,same=original)
        w.goto(self.base+path+'?'+urlencode(period))
        self.observe('14-almacenero-lee','ALMACENERO',w,lambda s,t:w.get_by_test_id('movement-balance').inner_text()=='3',same=original,photo=True)
        self.denied('15-vendedor-403','VENDEDOR',v,path)
        token=next(c['value'] for c in w.context.cookies() if c['name']=='csrftoken')
        reply=w.request.post(self.base+path,headers={'X-CSRFToken':token})
        assert reply.status==405 and base.witness(self.db)['sha256']==original['sha256']
        base.save(self.out/'16-post-405.json',dict(http=reply.status,sin_mutacion=True));self.steps.append('16-post-405')
        w.set_viewport_size({'width':390,'height':844})
        self.observe('17-movil-filtros','ALMACENERO',w,same=original,photo=True)
        assert w.evaluate('document.documentElement.scrollWidth<=innerWidth')
        region=w.get_by_role('region',name='Movimientos, tabla desplazable');region.evaluate('e=>e.scrollLeft=e.scrollWidth')
        self.observe('18-movil-saldo','ALMACENERO',w,same=original,photo=True)
        w.set_viewport_size({'width':1280,'height':900})
        w.goto(self.base+legacy)
        self.observe('19-legado-sin-saldo','ALMACENERO',w,lambda s,t:w.get_by_test_id('closing-balance').inner_text()=='No disponible' and 'Sin fotografía de entrada' in t,same=original,photo=True)
        with closing(sqlite3.connect(self.db)) as con:
            con.execute('UPDATE inventory_lot SET available_quantity=3 WHERE id=?',[FIXTURE['last_lot'].replace('-','')]);con.commit()
        changed=base.witness(self.db)
        a.goto(self.base+path)
        self.observe('20-desajuste-no-inventa-saldo','ADMIN',a,lambda s,t:'Las cantidades por lote no concilian' in t and a.get_by_test_id('closing-balance').inner_text()=='No disponible',same=changed,photo=True)
        base.save(self.out/'comparaciones.json',dict(saldos=True,filtros=True,paginacion=True,roles=True,legado=True,desajuste=True))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('salida',type=Path);parser.add_argument('--final',action='store_true');args=parser.parse_args()
    FINAL=args.final;base.prepare=prepare;base.Journey=Journey
    try:base.main(args.salida)
    finally:
        p=args.salida/'ejecucion.json'
        if p.exists():
            data=json.loads(p.read_text(encoding='utf-8'));data.update(sublote='14-H2',runner14h2_sha256=base.sha(Path(__file__).read_bytes()));base.save(p,data)
