"""Cierre14: ajustes existentes/nuevos, historia, Q0 y consumo entre roles en Chrome."""
import argparse
import importlib.util
import sqlite3
from contextlib import closing
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
import uuid

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('base14',HERE.parent/'14-D-20261113/navegador/recorrido.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
original_prepare=base.prepare;FIXTURE={}
base.ACTORS={'ADMIN':'Admin original14J','ALMACENERO':'Almacén original14J','VENDEDOR':'Venta original14J'}

def prepare(db,password):
    original_prepare(db,password)
    from django.db import connection
    from django.utils import timezone
    from catalog.models import Category,Product
    from identity.models import Account
    from inventory.models import PhysicalAdjustment,InitialInventoryLoad,Lot,StockWriteOff
    from inventory.services import confirm_initial_load,LotInput,write_off_stock
    category=Category.objects.create(name='Ajustes14J')
    admin=Account.objects.get(email='admin@example.invalid');worker=Account.objects.get(email='almacenero@example.invalid')
    future=timezone.localdate()+timedelta(days=30)
    for key,qty in [('existing',10),('empty',1),('expired',2)]:
        p=Product.objects.create(name=key+'14J',category=category,barcode='INT-14J-'+key,sale_price=10)
        load=confirm_initial_load(actor=worker,product=p,lots=[LotInput('A-'+key,qty,Decimal('3'),future)])
        lot=load.lines.get().lot
        if key=='empty':write_off_stock(actor=worker,lot=lot,quantity=1,reason='ROBO',notes='Vaciar fixture Q0')
        FIXTURE[key]=str(p.pk);FIXTURE[key+'_lot']=str(lot.pk);FIXTURE[key+'_load']=str(load.pk)
    p=Product.objects.create(name='Legado actual14J',category=category,barcode='INT-14J-legacy',sale_price=10)
    load=InitialInventoryLoad.objects.create(product=p,responsible=worker)
    lot=Lot.objects.create(product=p,initial_load=load,number='LEGADO',initial_quantity=5,available_quantity=5,unit_cost=3,expiration_date=future)
    old=PhysicalAdjustment.objects.create(lot=lot,delta=1,unit_cost=None,reason='Motivo conservado',responsible=admin)
    merma=StockWriteOff.objects.create(lot=lot,quantity=1,reason='ROBO',notes='Merma previa conservada',responsible=worker,correlativo='LEGACY-J')
    FIXTURE.update(admin=str(admin.pk),legacy=str(p.pk),legacy_adjustment=str(old.pk),legacy_merma=str(merma.pk),
        future=future.isoformat(),today=timezone.localdate().isoformat())
    connection.close()

class Journey(base.Journey):
    def url(self,key):return self.base+'/inventario/ajustes/nuevo/?lote='+FIXTURE[key+'_lot']
    def stock(self,state,key):return sum(l['available_quantity'] for l in state['lotes'] if l['producto']==key+'14J')
    def form(self,page,values):
        for name,value in values.items():base.fill(page,name,value)
    def post(self,page,path,payload):
        token=next(c['value'] for c in page.context.cookies() if c['name']=='csrftoken')
        return page.request.post(self.base+path,form=payload,headers={'X-CSRFToken':token})
    def run(self,browser,password):
        a=self.connect(browser,'ADMIN',password);w=self.connect(browser,'ALMACENERO',password);v=self.connect(browser,'VENDEDOR',password)
        base.save(self.out/'fixture.json',FIXTURE)
        base.link(a,'/inventario/ajustes/nuevo/')
        a.get_by_role('row').filter(has_text='existing14J').get_by_role('link',name='Ajustar',exact=True).click()
        before=self.observe('J01-formulario','ADMIN',a,photo=True)
        key=base.selector(a,'idempotency_key').input_value()
        self.form(a,{'delta':'0','reason':'Conteo documentado'});base.button(a,'Confirmar ajuste')
        self.observe('J02-cero-rechazado','ADMIN',a,lambda s,t:'no puede ser cero' in t,same=before,photo=True)
        assert a.evaluate('document.activeElement.id')=='adjustment-errors'
        a.locator('#adjustment-errors a').first.click();assert a.evaluate('document.activeElement.name')=='delta'
        self.form(a,{'delta':'2','reason':' '});base.button(a,'Confirmar ajuste')
        self.observe('J03-motivo-vacio','ADMIN',a,lambda s,t:bool(a.locator('#adjustment-errors').count()),same=before)
        self.form(a,{'reason':'Recuento físico +2'});base.button(a,'Confirmar ajuste')
        plus=self.observe('J04-ajuste-positivo','ADMIN',a,lambda s,t:self.stock(s,'existing')==12 and '+2 UND' in t,photo=True)
        plus_url=a.url.split('#')[0]
        payload={'lot_id':FIXTURE['existing_lot'],'delta':'2','reason':'Recuento físico +2','idempotency_key':key,'unit_cost':'','cost_source':''}
        a2=self.connect(browser,'ADMIN',password)
        response=self.post(a2,'/inventario/ajustes/nuevo/',payload)
        base.save(self.out/'J05-diagnostico.json',dict(url=response.url,expected=plus_url,status=response.status,testigo=base.witness(self.db)))
        assert response.url==plus_url and base.witness(self.db)['sha256']==plus['sha256']
        self.steps.append('J05-reenvio-otra-sesion');base.save(self.out/'J05-reenvio-otra-sesion.json',dict(sin_mutacion=True,url=response.url,status=response.status))
        for case,change in [('J06-clave-divergente',{'delta':'1'}),('J07-clave-vacia',{'idempotency_key':''}),('J08-motivo-largo',{'idempotency_key':str(uuid.uuid4()),'reason':'x'*301})]:
            response=self.post(a,'/inventario/ajustes/nuevo/',{**payload,**change})
            assert response.status==200 and base.witness(self.db)['sha256']==plus['sha256']
            self.steps.append(case);base.save(self.out/(case+'.json'),dict(sin_mutacion=True,status=response.status))
        a.goto(self.url('existing'));self.form(a,{'delta':'-13','reason':'Faltante ficticio'});base.button(a,'Confirmar ajuste')
        self.observe('J09-exceso-negativo','ADMIN',a,lambda s,t:'supera las existencias' in t,same=plus)
        self.form(a,{'delta':'-3'});base.button(a,'Confirmar ajuste')
        minus=self.observe('J10-ajuste-negativo','ADMIN',a,lambda s,t:self.stock(s,'existing')==9 and 'S/ 3,0000' in t,photo=True)
        minus_url=a.url
        w.goto(minus_url);self.observe('J11-almacen-consulta','ALMACENERO',w,same=minus)
        self.denied('J12-vendedor-detalle','VENDEDOR',v,minus_url.removeprefix(self.base))
        for role,page in [('ALMACENERO',w),('VENDEDOR',v)]:
            response=self.post(page,'/inventario/ajustes/nuevo/',payload)
            assert response.status==403 and base.witness(self.db)['sha256']==minus['sha256']
            case='J13-post-denegado-'+role;self.steps.append(case);base.save(self.out/(case+'.json'),dict(status=403,sin_mutacion=True))
        with closing(sqlite3.connect(self.db)) as con:
            con.execute('UPDATE identity_account SET display_name=? WHERE id=?',['Admin renombrado14J',FIXTURE['admin'].replace('-','')])
            con.execute('UPDATE catalog_product SET name=? WHERE id=?',['Producto renombrado14J',FIXTURE['existing'].replace('-','')])
            con.execute('UPDATE inventory_lot SET number=?,number_normalized=? WHERE id=?',['CAMBIO','CAMBIO',FIXTURE['existing_lot'].replace('-','')]);con.commit()
        changed=base.witness(self.db);a.reload()
        self.observe('J14-snapshot-original','ADMIN',a,lambda s,t:all(x in a.get_by_test_id('adjustment-detail').inner_text() for x in ['Admin original14J','existing14J','A-EXISTING','Faltante ficticio']),same=changed,photo=True)
        a.get_by_role('link',name='Ver movimientos',exact=True).click()
        self.observe('J15-kardex-historia','ADMIN',a,lambda s,t:a.get_by_test_id('closing-balance').inner_text()=='9' and 'Admin original14J' in a.locator('table').inner_text(),same=changed,photo=True)
        a.goto(self.base+'/inventario/cargas/'+FIXTURE['existing_load']+'/')
        self.observe('J16-carga-original','ADMIN',a,lambda s,t:'10 UND' in t,same=changed,photo=True)

        base.link(a,'/inventario/ajustes/nuevo/');base.selector(a,'producto').select_option(FIXTURE['empty']);base.button(a,'Registrar lote nuevo por ajuste')
        before=base.witness(self.db)
        self.form(a,{'number':'NUEVO','expiration_date':FIXTURE['future'],'delta':'4','reason':'Conteo acreditado Q0'})
        base.button(a,'Confirmar ajuste')
        self.observe('J17-costo-Q0-ausente','ADMIN',a,lambda s,t:'costo fiable documentado' in t,same=before,photo=True)
        self.form(a,{'unit_cost':'2.5000'});base.button(a,'Confirmar ajuste')
        self.observe('J18-fuente-Q0-ausente','ADMIN',a,lambda s,t:'fuente del costo' in t,same=before)
        self.form(a,{'cost_source':'Acta ficticia de costo 14J'});base.button(a,'Confirmar ajuste')
        added=self.observe('J19-nuevo-lote-Q0','ADMIN',a,lambda s,t:self.stock(s,'empty')==4 and 'AJUSTE' in t and 'S/ 2,5000' in t,photo=True)
        a.get_by_role('link',name='Ver movimientos',exact=True).click()
        self.observe('J20-kardex-nuevo-origen','ADMIN',a,lambda s,t:a.get_by_test_id('closing-balance').inner_text()=='4',same=added,photo=True)
        base.link(v,'/caja/abrir/');base.fill(v,'opening_amount','100');base.button(v,'Abrir turno')
        base.link(v,'/ventas/');base.fill(v,'query','INT-14J-empty');base.button(v,'Buscar');base.fill(v,'quantity','2');base.button(v,'Agregar')
        base.link(v,'/ventas/cobrar/');base.fill(v,'cash_received','20');base.button(v,'Confirmar cobro')
        sale=self.observe('J21-venta-de-ajuste','VENDEDOR',v,lambda s,t:self.stock(s,'empty')==2 and s['lineas'][0]['unit_cost']==2.5,photo=True)
        base.link(w,'/inventario/bajas/nueva/');w.get_by_role('row').filter(has_text='NUEVO').get_by_role('link',name='Dar de baja',exact=True).click()
        self.form(w,{'quantity':'1','notes':'Daño de unidad encontrada'});base.selector(w,'reason').select_option('DAÑO');base.button(w,'Confirmar baja')
        merma=self.observe('J22-merma-de-ajuste','ALMACENERO',w,lambda s,t:self.stock(s,'empty')==1 and 'AJUSTE' in t and 'S/ 2,5000' in t,photo=True)
        a.goto(self.base+'/inventario/productos/'+FIXTURE['empty']+'/movimientos/')
        self.observe('J23-admin-concilia','ADMIN',a,lambda s,t:a.get_by_test_id('closing-balance').inner_text()=='1',same=merma,photo=True)
        base.link(v,'/caja/cerrar/');base.fill(v,'counted_amount','120');base.button(v,'Cerrar turno')
        self.observe('J24-cierre-cadena-ajuste','VENDEDOR',v,lambda s,t:s['cierres'][0]['expected_amount']==120 and s['cierres'][0]['difference']==0,photo=True)

        base.link(a,'/inventario/ajustes/nuevo/');base.selector(a,'producto').select_option(FIXTURE['expired']);base.button(a,'Registrar lote nuevo por ajuste')
        before=base.witness(self.db)
        self.form(a,{'number':'E-NUEVO','expiration_date':FIXTURE['today'],'delta':'2','reason':'Hallazgo vencido documentado'})
        base.button(a,'Confirmar ajuste')
        added=self.observe('J25-lote-vencido','ADMIN',a,lambda s,t:self.stock(s,'expired')==4,photo=True)
        base.link(w,'/inventario/stock/')
        row=w.get_by_role('row').filter(has_text='expired14J')
        self.observe('J26-fisico-vendible','ALMACENERO',w,lambda s,t:row.locator('td').all_inner_texts()[2:4]==['4','2'],same=added,photo=True)
        a.goto(self.base+'/inventario/ajustes/nuevo/?producto='+FIXTURE['expired'])
        self.form(a,{'number':'E-NUEVO','expiration_date':FIXTURE['today'],'delta':'2','reason':'No duplicar identidad'})
        base.button(a,'Confirmar ajuste')
        self.observe('J27-colision-lote','ADMIN',a,lambda s,t:'ya está registrado' in t,same=added)
        a.goto(self.base+'/inventario/ajustes/'+FIXTURE['legacy_adjustment']+'/')
        self.observe('J28-ajuste-legado','ADMIN',a,lambda s,t:'Registro anterior o incompleto' in t and 'No disponible' in a.get_by_test_id('adjustment-detail').inner_text(),same=added,photo=True)
        a.goto(self.base+'/inventario/productos/'+FIXTURE['legacy']+'/movimientos/')
        self.observe('J29-kardex-legado','ADMIN',a,lambda s,t:a.get_by_test_id('closing-balance').inner_text()=='No disponible' and 'Fotografía histórica de merma no disponible' in t,same=added,photo=True)
        a.goto(minus_url);a.set_viewport_size({'width':390,'height':844})
        self.observe('J30-movil-ajuste','ADMIN',a,same=added,photo=True)
        assert a.evaluate('document.documentElement.scrollWidth<=innerWidth')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('salida',type=Path);args=parser.parse_args()
    base.prepare=prepare;base.Journey=Journey;base.main(args.salida)
