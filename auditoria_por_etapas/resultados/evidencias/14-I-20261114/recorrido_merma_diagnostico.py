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
FIXTURE={}

def prepare(db,password):
    original_prepare(db,password)
    from django.db import connection
    from django.utils import timezone
    from catalog.models import Category,Product
    from identity.models import Account
    from inventory.models import Supplier
    from inventory.services import confirm_initial_load,LotInput
    today=timezone.localdate()
    category=Category.objects.create(name='Familia 14I')
    worker=Account.objects.get(email='almacenero@example.invalid')
    supplier=Supplier.objects.create(name='Proveedor 14I',ruc='20000000014')
    p=Product.objects.create(name='Producto 14I',category=category,barcode='INT-14I',sale_price=Decimal('10'))
    load=confirm_initial_load(actor=worker,product=p,supplier=supplier,lots=[LotInput('A',10,Decimal('3'),today+timedelta(days=30))])
    FIXTURE.update(product=str(p.pk),lot=str(load.lots.get().pk),actor=str(worker.pk),category=str(category.pk))
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
        w.get_by_role('link',name='Dar de baja',exact=True).click()
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
        after=self.observe('I05-baja-confirmada','ALMACENERO',w,lambda s,t:s['lotes'][0]['available_quantity']==8 and len(s['bajas'])==1,photo=True)
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
        self.observe('I10-admin-observa','ADMIN',a,lambda s,t:'B-00000001' in t and 'Almacén 14I' in t and a.get_by_test_id('closing-balance').inner_text()=='8',same=after,photo=True)
        w2=self.connect(browser,'ALMACENERO',password)
        reply=self.post(w2,payload)
        second=base.witness(self.db)
        base.save(self.out/'I11-reintento-otra-sesion.json',dict(http=reply.status,antes=after,despues=second,sin_mutacion=after['sha256']==second['sha256']))
        self.steps.append('I11-reintento-otra-sesion')
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
        base.save(self.out/'diagnostico.json',dict(constancia_dedicada=dedicated,reintento_otra_sesion_sin_mutacion=after['sha256']==second['sha256'],
            autor_actual_en_merma='Empleado renombrado 14I' in text,lote_actual_en_merma='Lote NUEVO' in text,
            notas='Renombrado ORM controlado después de baja; navegación y confirmación anteriores por Chrome. No demuestra edición UI ni concurrenciaPG.'))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('salida',type=Path);args=parser.parse_args()
    base.prepare=prepare;base.Journey=Journey
    try:base.main(args.salida)
    finally:
        p=args.salida/'ejecucion.json'
        if p.exists():
            data=json.loads(p.read_text(encoding='utf-8'));data.update(sublote='14-I diagnóstico',runner14i_sha256=base.sha(Path(__file__).read_bytes()));base.save(p,data)
