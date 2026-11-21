"""Concreciones aceptadas de14 antes de revalidación; no conecta bases."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
p=ROOT/'08_Historias_de_Usuario.md';s=p.read_text(encoding='utf-8')
assert '**Concreción14-CIERRE' not in s
marker='<a id="CP-HU-INV-03-001"></a>'
text='''**Concreción14-CIERRE, aceptada14/11/2026.** La orden expresa del responsable de corregir los pendientes hasta completar14 respalda esta realización técnica de HU-INV-03, RN05 y RN14: se reutiliza PhysicalAdjustment con fotografía de producto/código/unidad, responsable, lote/vencimiento/origen y costo/fuente; UUID persistente única y huella de contenido para recuperar la misma operación del mismo actor entre sesiones. HTTP exige clave; llamadas internas sin clave representan operaciones nuevas. Un lote nuevo referencia su ajuste de origen; no se inventa compra, recepción ni segunda carga inicial. Se rechaza duplicar el número comercial normalizado de un lote existente: el conteo debe seleccionar su origen ya registrado. La política de recepciones sucesivas del mismo lote comercial no cambia.

ADMIN registra y ADMIN/ALMACENERO consultan `/inventario/ajustes/{UUID}/`, enlazado desde movimientos. Legado sin fotografía muestra ausencia explícita, sin completar nombres desde maestros actuales. Con Q0 se exige costo positivo hasta9999999.9999 a4decimales y referencia documental de1..300 caracteres; con Q>0 se usa el promedio vigente y se rechaza un costo distinto. Motivo1..300, número de lote1..64, variación entera no nula de−999999..999999, nuevo lote positiva, fecha fiable hasta20años; vencido permanece físico no vendible. Producto sin carga inicial exige investigar apertura, no inventarla. La referencia es declarada por el operador, no certifica autenticidad legal.

Se acepta el resumen de errores enfocable, con enlaces a campos y mensajes inline, como concreción de CT-COHERENCIA-UI/C03 para este formulario. Se conserva la interfaz existente. La migración deja NULL en historia ausente y el efecto lote/ajuste/costo/origen es atómico. [Alternativas, beneficio, riesgo, costo e impacto](auditoria_por_etapas/resultados/soporte/14-CIERRE-ajustes.md). Aceptación e implementación no equivalen a prueba aprobada: consultar resultados de14-CIERRE.

'''
s=s.replace(marker,text+marker,1)
marker='<a id="CP-DEC-11-TOPE-EFECTIVO-FORM-001"></a>'
text='''**Concreción14-CIERRE, dinero.** Se separan los límites de nueva operación y acumulación; bajo el bloqueo del turno se comprueba apertura+suma de ventas confirmadas+nueva venta antes de escribir venta, contador o stock. Los reintentos históricos conocidos conservan sus importes originales hasta la capacidad14,2; no se aplican retroactivamente las prohibiciones nuevas de descuento ni el tope por operación. Esto no permite crear descuentos nuevos. Formularios y servicios rechazan formatos ambiguos antes de convertirlos. Los checks de cantidad y cierre/montos se acompañan de diagnóstico previo en migración, sin recorte ni backfill. Son restricciones de integridad de los contratos ya aceptados; la orden de corrección de14 habilita implementarlas, no migrar la base operativa.

'''
s=s.replace(marker,text+marker,1)
p.write_text(s,encoding='utf-8')
sys.path.insert(0,str(HERE.parents[1]/'fuente_unica_20261112'))
import regenerar_vistas as views
print(views.generate())
(HERE/'08-ejecutado.md').write_bytes(p.read_bytes())
