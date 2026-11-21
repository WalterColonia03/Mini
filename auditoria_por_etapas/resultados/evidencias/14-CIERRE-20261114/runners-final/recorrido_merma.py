"""Chrome real, tres roles, merma y persistencia en SQLite efímera. No usa base operativa."""
import argparse
import importlib.util
import json
import sqlite3
from contextlib import closing
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('audit14d',HERE.parent/'14-D-20261113/navegador/recorrido.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
original_prepare=base.prepare
base.ACTORS={'ADMIN':'Administración 14I','ALMACENERO':'Almacén 14I','VENDEDOR':'Venta 14I'}
FIXTURE={};FINAL=False

def prepare(db,password):
    original_prepare(db,password)
    from django.db import connection
    from django.utils import timezone
    from catalog.models import Category,Product
    from identity.models import Account
    from inventory.models import Supplier,StockWriteOff,InitialInventoryLoad,Lot
    from inventory.services import confirm_initial_load,LotInput,register_stock_entry
    today=timezone.localdate()
    category=Category.objects.create(name='Familia 14I')
    worker=Account.objects.get(email='almacenero@example.invalid')
    supplier=Supplier.objects.create(name='Proveedor 14I',ruc='20000000014')
    p=Product.objects.create(name='Producto 14I',category=category,barcode='INT-14I',sale_price=Decimal('10'))
    load=confirm_initial_load(actor=worker,product=p,supplier=supplier,lots=[LotInput('A',10,Decimal('3'),today+timedelta(days=30))])
    FIXTURE.update(product=str(p.pk),lot=str(load.lots.get().pk),actor=str(worker.pk),category=str(category.pk))
    if FINAL:
        expired=Product.objects.create(name='Vencido 14I',category=category,barcode='INT-14I-E',sale_price=10)
        with patch('django.utils.timezone.localdate',return_value=today-timedelta(days=1)):
            eload=confirm_initial_load(actor=worker,product=expired,lots=[LotInput('E',3,Decimal('4'),today)])
        origins=Product.objects.create(name='Orígenes 14I',category=category,barcode='INT-14I-O',sale_price=10)
        confirm_initial_load(actor=worker,product=origins,lots=[LotInput('O',10,Decimal('3'),today+timedelta(days=60))])
        receipts=[register_stock_entry(actor=worker,product=origins,lots=[LotInput('C',q,Decimal(c),today+timedelta(days=60))]) for q,c in ((10,'6'),(5,'8'))]
        legacy=Product.objects.create(name='Legado actual 14I',category=category,barcode='INT-14I-L',sale_price=10)
        header=InitialInventoryLoad.objects.create(product=legacy,responsible=worker)
        lot=Lot.objects.create(product=legacy,initial_load=header,number='LEGADO',number_normalized='LEGADO',initial_quantity=5,available_quantity=4,unit_cost=3,expiration_date=today+timedelta(days=30))
        old=StockWriteOff.objects.create(lot=lot,quantity=1,reason='ROBO',notes='Dato antiguo conservado',responsible=worker,correlativo='LEGADO-14I')
        FIXTURE.update(expired=str(eload.lots.get().pk),expired_product=str(expired.pk),origin_product=str(origins.pk),
            r1_lot=str(receipts[0].lines.get().lot_id),r2_lot=str(receipts[1].lines.get().lot_id),r2_ref=receipts[1].correlative,legacy=str(old.pk))
    connection.close()

class Journey(base.Journey):
    def post(self,page,payload):
        token=next(c['value'] for c in page.context.cookies() if c['name']=='csrftoken')
        return page.request.post(self.base+'/inventario/bajas/nueva/',form=payload,headers={'X-CSRFToken':token})

    def run(self,browser,password):
        from django.db import connection
        from catalog.models import Product
        from identity.models import Account
        from inventory.models import Lot
        a=self.connect(browser,'ADMIN',password);w=self.connect(browser,'ALMACENERO',password);v=self.connect(browser,'VENDEDOR',password)
        base.save(self.out/'fixture.json',FIXTURE)
        path='/inventario/bajas/nueva/?lote='+FIXTURE['lot']
        movements=f"/inventario/productos/{FIXTURE['product']}/movimientos/"
        base.link(w,'/inventario/bajas/nueva/')
        w.get_by_role('row').filter(has_text='Producto 14I').get_by_role('link',name='Dar de baja',exact=True).click()
        initial=self.observe('I01-formulario','ALMACENERO',w,photo=True)
        key=base.selector(w,'idempotency_key').input_value()
        base.fill(w,'quantity','11');base.selector(w,'reason').select_option('DAÑO');base.fill(w,'notes','Frasco roto ficticio')
        base.button(w,'Confirmar baja')
        self.observe('I02-exceso','ALMACENERO',w,lambda s,t:'supera las existencias' in t,same=initial,photo=True)
        base.fill(w,'quantity','2');base.fill(w,'notes','')
        base.button(w,'Confirmar baja')
        self.observe('I03-sin-explicacion','ALMACENERO',w,lambda s,t:'Detalle obligatorio' in t,same=initial)
        base.fill(w,'notes','Frasco roto ficticio');base.selector(w,'reason').select_option('VENCIMIENTO')
        base.button(w,'Confirmar baja')
        self.observe('I04-fecha-incompatible','ALMACENERO',w,lambda s,t:'aún no ha vencido' in t,same=initial)
        base.selector(w,'reason').select_option('DAÑO');base.button(w,'Confirmar baja')
        after=self.observe('I05-baja-confirmada','ALMACENERO',w,lambda s,t:s['lotes'][0]['available_quantity']==8 and len(s['bajas'])==len(initial['bajas'])+1,photo=True)
        receipt_url=w.url
        reference=next(row['correlativo'] for row in after['bajas'] if row['correlativo'] not in {old['correlativo'] for old in initial['bajas']})
        dedicated='Constancia de merma' in w.locator('body').inner_text()
        payload={'lot_id':FIXTURE['lot'],'idempotency_key':key,'quantity':'2','reason':'DAÑO','notes':'Frasco roto ficticio'}
        reply=self.post(w,payload)
        assert reply.status==200 and base.witness(self.db)['sha256']==after['sha256']
        base.save(self.out/'I06-reintento-misma-sesion.json',dict(http=reply.status,sin_mutacion=True,recupera_constancia='Constancia de merma' in reply.text()))
        self.steps.append('I06-reintento-misma-sesion')
        reply=self.post(w,{**payload,'quantity':'1'})
        assert reply.status==200 and 'otra solicitud' in reply.text() and base.witness(self.db)['sha256']==after['sha256']
        base.save(self.out/'I07-contenido-divergente.json',dict(http=reply.status,sin_mutacion=True));self.steps.append('I07-contenido-divergente')
        self.denied('I08-vendedor-get','VENDEDOR',v,'/inventario/bajas/nueva/')
        reply=self.post(v,payload)
        assert reply.status==403 and base.witness(self.db)['sha256']==after['sha256']
        base.save(self.out/'I09-vendedor-post.json',dict(http=reply.status,sin_mutacion=True));self.steps.append('I09-vendedor-post')
        a.goto(self.base+movements)
        self.observe('I10-admin-observa','ADMIN',a,lambda s,t:reference in t and 'Almacén 14I' in t and a.get_by_test_id('closing-balance').inner_text()=='8',same=after,photo=True)
        w2=self.connect(browser,'ALMACENERO',password)
        reply=self.post(w2,payload)
        second=base.witness(self.db)
        base.save(self.out/'I11-reintento-otra-sesion.json',dict(http=reply.status,antes=after,despues=second,sin_mutacion=after['sha256']==second['sha256']))
        self.steps.append('I11-reintento-otra-sesion')
        if FINAL:
            assert dedicated and after['sha256']==second['sha256']
            changed_tables=[name for name in initial['por_tabla'] if initial['por_tabla'][name]!=after['por_tabla'][name]]
            assert set(changed_tables)=={'inventory_lot','inventory_stockwriteoff'}
            w2.goto(receipt_url)
            self.observe('I11b-constancia-recuperada','ALMACENERO',w2,lambda s,t:'Producto 14I' in t and 'S/ 3,0000' in t,same=after,photo=True)
        # Control técnico declarado: simula corrección posterior de maestros; no usa la UI como evidencia de edición.
        with closing(sqlite3.connect(self.db)) as con:
            con.execute('UPDATE catalog_product SET name=? WHERE id=?',['Producto renombrado 14I',FIXTURE['product'].replace('-','')])
            con.execute('UPDATE identity_account SET display_name=? WHERE id=?',['Empleado renombrado 14I',FIXTURE['actor'].replace('-','')])
            con.execute('UPDATE inventory_lot SET number=?,number_normalized=? WHERE id=?',['NUEVO','NUEVO',FIXTURE['lot'].replace('-','')])
            con.commit()
        changed=base.witness(self.db)
        a.reload()
        self.observe('I12-historia-tras-cambiar-maestros','ADMIN',a,same=changed,photo=True)
        text=a.locator('body').inner_text()
        if FINAL:
            assert 'Lote A' in text and 'Empleado renombrado 14I' not in text
            a.get_by_role('link',name='Ver constancia de merma').click()
            self.observe('I13-fotografia-original','ADMIN',a,lambda s,t:all(x in a.get_by_test_id('writeoff-receipt').inner_text() for x in ['Producto 14I','Almacén 14I','Lote original\nA','2 UND','S/ 3,0000']),same=changed,photo=True)
            a.reload();self.observe('I14-recarga','ADMIN',a,same=changed)
            self.denied('I15-vendedor-constancia','VENDEDOR',v,receipt_url.removeprefix(self.base))
            token=next(c['value'] for c in a.context.cookies() if c['name']=='csrftoken')
            response=a.request.post(receipt_url,headers={'X-CSRFToken':token})
            assert response.status==405 and base.witness(self.db)['sha256']==changed['sha256']
            base.save(self.out/'I16-constancia-solo-get.json',dict(http=response.status,sin_mutacion=True));self.steps.append('I16-constancia-solo-get')
            # Dispatch de impresión instrumentado; media print real. No se afirma impresora física.
            a.evaluate('window.print=()=>{window.auditPrintRequested=true}')
            a.get_by_role('button',name='Imprimir',exact=True).click();assert a.evaluate('window.auditPrintRequested===true')
            a.emulate_media(media='print')
            self.observe('I17-medio-impresion','ADMIN',a,same=changed,photo=True)
            assert not a.locator('.no-print').is_visible()
            a.emulate_media(media='screen');a.set_viewport_size({'width':390,'height':844})
            self.observe('I18-movil-constancia','ADMIN',a,same=changed,photo=True)
            assert a.evaluate('document.documentElement.scrollWidth<=innerWidth')
            a.set_viewport_size({'width':1280,'height':900})
            response=self.post(a,payload)
            assert response.status==200 and 'otra solicitud' in response.text() and base.witness(self.db)['sha256']==changed['sha256']
            base.save(self.out/'I19-clave-otro-actor.json',dict(http=response.status,sin_mutacion=True));self.steps.append('I19-clave-otro-actor')

            def submit(case,lot,reason,notes,qty='1',error=None):
                w.goto(self.base+'/inventario/bajas/nueva/?lote='+lot)
                before=base.witness(self.db)
                base.fill(w,'quantity',qty);base.selector(w,'reason').select_option(reason);base.fill(w,'notes',notes)
                base.button(w,'Confirmar baja')
                return self.observe(case,'ALMACENERO',w,lambda s,t:error in t if error else 'Constancia de merma' in t,same=before if error else None,photo=True)
            submit('I20-vencido-dano-rechazado',FIXTURE['expired'],'DAÑO','Daño ficticio',error='El lote está vencido')
            submit('I21-vencido-robo-sin-detalle',FIXTURE['expired'],'ROBO','',error='Detalle obligatorio')
            with closing(sqlite3.connect(self.db)) as con:
                con.execute('UPDATE catalog_product SET is_active=0 WHERE id=?',[FIXTURE['expired_product'].replace('-','')]);con.commit()
            submit('I22-vencido-inactivo-robo',FIXTURE['expired'],'ROBO','Faltante ficticio confirmado')
            submit('I23-vencido-inactivo-caducidad',FIXTURE['expired'],'VENCIMIENTO','')
            submit('I24-r2-mismo-lote-comercial',FIXTURE['r2_lot'],'ROBO','Faltante de R2')
            assert FIXTURE['r2_ref'] in w.get_by_test_id('writeoff-receipt').inner_text()
            with closing(sqlite3.connect(self.db)) as con:
                rows=dict(con.execute('SELECT id,available_quantity FROM inventory_lot'))
            assert rows[FIXTURE['r1_lot'].replace('-','')]==10 and rows[FIXTURE['r2_lot'].replace('-','')]==4
            a.goto(self.base+f"/inventario/bajas/{FIXTURE['legacy']}/")
            before=base.witness(self.db)
            self.observe('I25-legado-sin-inventar','ADMIN',a,lambda s,t:'Registro anterior o incompleto' in t and 'Dato antiguo conservado' in t and 'Legado actual 14I' not in a.get_by_test_id('writeoff-receipt').inner_text(),same=before,photo=True)
        base.save(self.out/'diagnostico.json',dict(constancia_dedicada=dedicated,reintento_otra_sesion_sin_mutacion=after['sha256']==second['sha256'],
            autor_actual_en_merma='Empleado renombrado 14I' in text,lote_actual_en_merma='Lote NUEVO' in text,
            notas='Renombrado SQL aislado controlado después de baja; confirmación por Chrome. Media print y dispatch instrumentado, no impresora física. No demuestra edición UI ni concurrenciaPG.'))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('salida',type=Path);parser.add_argument('--final',action='store_true');args=parser.parse_args()
    FINAL=args.final
    base.prepare=prepare;base.Journey=Journey
    try:base.main(args.salida)
    finally:
        p=args.salida/'ejecucion.json'
        if p.exists():
            data=json.loads(p.read_text(encoding='utf-8'));data.update(sublote='14-I diagnóstico',runner14i_sha256=base.sha(Path(__file__).read_bytes()));base.save(p,data)
