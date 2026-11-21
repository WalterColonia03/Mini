"""Chrome real: ventas válidas acumuladas y cierre independiente del tope por venta."""
import argparse
import importlib.util
import json
import sqlite3
from contextlib import closing
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('base14',HERE.parent/'14-D-20261113/navegador/recorrido.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
original_prepare=base.prepare
FIXTURE={}

def prepare(db,password):
    original_prepare(db,password)
    from django.db import connection
    from django.utils import timezone
    from catalog.models import Category,Product
    from identity.models import Account
    from inventory.services import confirm_initial_load,LotInput
    p=Product.objects.create(name='Límite monetario14',category=Category.objects.create(name='Dinero14'),barcode='INT-MONEY14',sale_price=Decimal('5000000'))
    confirm_initial_load(actor=Account.objects.get(email='almacenero@example.invalid'),product=p,
        lots=[LotInput('A',10,Decimal('3'),timezone.localdate()+timedelta(days=30))])
    FIXTURE.update(product=str(p.pk));connection.close()

class Journey(base.Journey):
    def run(self,browser,password):
        a=self.connect(browser,'ADMIN',password);v=self.connect(browser,'VENDEDOR',password)
        base.link(v,'/caja/abrir/')
        before=self.observe('M01-apertura','VENDEDOR',v)
        base.fill(v,'opening_amount','10000000');base.button(v,'Abrir turno')
        self.observe('M02-apertura-sobre-tope','VENDEDOR',v,lambda s,t:bool(v.locator('.error-list').count()),same=before,photo=True)
        base.fill(v,'opening_amount','0');base.button(v,'Abrir turno')
        self.observe('M03-abierta','VENDEDOR',v,lambda s,t:len(s['turnos'])==1)
        base.link(v,'/ventas/');base.fill(v,'query','INT-MONEY14');base.button(v,'Buscar')
        base.fill(v,'quantity','2');base.button(v,'Agregar');base.link(v,'/ventas/cobrar/')
        before=self.observe('M04-total-sobre-tope','VENDEDOR',v,photo=True)
        base.fill(v,'cash_received','10000000');base.button(v,'Confirmar cobro')
        self.observe('M05-efectivo-sobre-tope','VENDEDOR',v,lambda s,t:bool(v.locator('.error-list').count()),same=before,photo=True)
        # POST de formulario vigente conservando todos sus campos para total>tope y efectivo permitido.
        base.fill(v,'cash_received','9999999.99');base.button(v,'Confirmar cobro')
        self.observe('M06-total-rechazado','VENDEDOR',v,lambda s,t:'El total no puede superar' in t,same=before,photo=True)
        base.link(v,'/ventas/')
        v.get_by_role('button',name='Descartar venta',exact=True).click()
        for i in (1,2):
            base.link(v,'/ventas/');base.fill(v,'query','INT-MONEY14');base.button(v,'Buscar')
            base.fill(v,'quantity','1');base.button(v,'Agregar');base.link(v,'/ventas/cobrar/')
            base.fill(v,'cash_received','5000000');base.button(v,'Confirmar cobro')
            self.observe(f'M0{6+i}-venta-valida','VENDEDOR',v,lambda s,t:len(s['ventas'])==i and s['ventas'][-1]['total_amount']==5000000,photo=True)
        base.link(a,'/ventas/historial/')
        self.observe('M09-admin-revisa','ADMIN',a,lambda s,t:len(s['ventas'])==2,photo=True)
        base.link(v,'/caja/cerrar/')
        before=self.observe('M10-formulario-cierre','VENDEDOR',v,photo=True)
        assert base.selector(v,'counted_amount').get_attribute('max')=='999999999999.99'
        base.fill(v,'counted_amount','1000000000000');base.button(v,'Cerrar turno')
        self.observe('M11-capacidad-rechazada','VENDEDOR',v,lambda s,t:bool(v.locator('.error-list').count()),same=before,photo=True)
        base.fill(v,'counted_amount','10000000');base.button(v,'Cerrar turno')
        after=self.observe('M12-cierre-acumulado','VENDEDOR',v,lambda s,t:s['cierres'][0]['expected_amount']==10000000 and s['cierres'][0]['difference']==0 and s['turnos'][0]['status']=='CLOSED',photo=True)
        v.reload();self.observe('M13-recarga','VENDEDOR',v,same=after)
        base.save(self.out/'resultado.json',dict(cierre=after['cierres'],sales=after['ventas'],nota='Maestros/carga por fixture; apertura, dos ventas y cierre por UI. Capacidad global se prueba además por servicio/PG.'))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('salida',type=Path);args=parser.parse_args()
    base.prepare=prepare;base.Journey=Journey
    base.main(args.salida)
