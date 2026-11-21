"""Chrome: cambio de precio entre roles, GET sin mutación y revisión explícita."""
import argparse
import importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('money14',HERE/'recorrido_dinero.py')
money=importlib.util.module_from_spec(spec);spec.loader.exec_module(money)
base=money.base
def prepare(db,password):
    money.prepare(db,password)
    from catalog.models import Product
    from django.db import connection
    Product.objects.filter(pk=money.FIXTURE['product']).update(sale_price=10)
    connection.close()
class Journey(base.Journey):
    def run(self,browser,password):
        a=self.connect(browser,'ADMIN',password);v=self.connect(browser,'VENDEDOR',password)
        base.link(v,'/caja/abrir/');base.fill(v,'opening_amount','100');base.button(v,'Abrir turno')
        base.link(v,'/ventas/');base.fill(v,'query','INT-MONEY14');base.button(v,'Buscar')
        base.fill(v,'quantity','1');base.button(v,'Agregar');base.link(v,'/ventas/cobrar/')
        self.observe('P01-revision-original','VENDEDOR',v,lambda s,t:s['borrador'][0]['unit_price']==10,photo=True)
        a.goto(self.base+'/productos/'+money.FIXTURE['product']+'/editar/')
        base.fill(a,'sale_price','12');base.button(a,'Guardar cambios')
        changed=self.observe('P02-admin-cambia-precio','ADMIN',a,lambda s,t:s['productos'][0]['sale_price']==12,photo=True)
        v.reload();self.observe('P03-GET-no-muta','VENDEDOR',v,lambda s,t:s['borrador'][0]['unit_price']==10,same=changed,photo=True)
        base.fill(v,'cash_received','12');base.button(v,'Confirmar cobro')
        reviewed=self.observe('P04-POST-exige-revision','VENDEDOR',v,lambda s,t:len(s['ventas'])==0 and s['borrador'][0]['unit_price']==12 and 'precio' in t.lower(),photo=True)
        differences=[name for name,h in changed['por_tabla'].items() if reviewed['por_tabla'][name]!=h]
        assert differences==['sales_saledraftline'],differences
        base.save(self.out/'P04-efecto-permitido.json',dict(tablas_cambiadas=differences,contrato='DEC-12-ORDEN-LINEAS-RECIBO/C-04: POST actualiza revisión, no confirma venta, stock ni caja'))
        v.reload();self.observe('P05-revision-actualizada','VENDEDOR',v,same=reviewed,photo=True)
        base.fill(v,'cash_received','12');base.button(v,'Confirmar cobro')
        sale=self.observe('P06-cobro-revisado','VENDEDOR',v,lambda s,t:s['ventas'][0]['total_amount']==12 and s['lotes'][0]['available_quantity']==9,photo=True)
        base.link(a,'/ventas/historial/');self.observe('P07-admin-observa','ADMIN',a,same=sale)
        base.link(v,'/caja/cerrar/');base.fill(v,'counted_amount','112');base.button(v,'Cerrar turno')
        self.observe('P08-cierre','VENDEDOR',v,lambda s,t:s['cierres'][0]['expected_amount']==112 and s['cierres'][0]['difference']==0,photo=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('salida',type=Path);args=p.parse_args()
    base.prepare=prepare;base.Journey=Journey;base.main(args.salida)
