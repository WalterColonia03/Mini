"""Cierre H2 con resultados comprobados; conserva los informes anteriores."""
import hashlib
import json
import re
import runpy
import sys
from collections import Counter
from pathlib import Path

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
RES=OUT.parents[1]
sys.path.insert(0,str(RES/'fuente_unica_20261112'))
import regenerar_vistas as views

def read(p):return p.read_text(encoding='utf-8-sig')
def obj(p):return json.loads(read(p))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,s):p.write_text(s.rstrip()+'\n',encoding='utf-8')

assert 'id="vigente-14-h2"' not in read(RES/'ETAPA-14.md')
suite=obj(OUT/'servidor/final2/regresion-manifiesto.json')
log=read(OUT/'servidor/final2/regresion-final.txt')
assert suite['salida']==0 and not suite['cambios_durante_prueba'] and 'Ran 604 tests' in log and '\nOK\n' in log
files=runpy.run_path(str(OUT/'verificar.py'))['product']()
assert files==suite['fuentes']
for name,count in [('final3',20),('cadena-final2',44)]:
    folder=OUT/'navegador'/name;run=obj(folder/'ejecucion.json')
    assert run['estado']=='recorrido_completo' and run['build_estable'] and len(run['pasos'])==count
    assert all(files[p]==h for p,h in obj(folder/'build-final.json')['archivos'].items())

p=ROOT/'08_Historias_de_Usuario.md';s=read(p)
lines=s.splitlines();lines[4]='**Revisión:14/11/2026.** Primera pasada: etapa13 finalizada para el panel mínimo; integración14-H2 verifica en muestra saldos, filtros y páginas delKardex con origen incompleto explícito. La etapa14 siguePARCIAL por constancia demerma, autor histórico de ajustes y demás pendientes. Build, evidencia y cursor14-I-MERMA-01 en [ETAPA-14](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-h2).15–17 y segunda pasada conservan la [secuencia](auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md).'
s='\n'.join(lines)+'\n'
start=s.index('##### CP-HU-INV-04-001');end=s.index('<a id="HU-INV-05">',start)
fragment=s[start:end].replace('**Estado:** DISEÑADO — NO EJECUTADO en este corte.','**Estado:** EJECUTADO PARCIAL14-H2. Secuencia, filtros, saldo conocido, paginación y permisos en SQLite/Chrome; autor histórico de ajustes y garantías concurrentes conservan pendientes.\n**Evidencia de ejecución:** [Servidor14-H2](auditoria_por_etapas/resultados/evidencias/14-H2-20261114/servidor/INFORME.md), [Navegador14-H2](auditoria_por_etapas/resultados/evidencias/14-H2-20261114/navegador/RESUMEN.md).')
s=s[:start]+fragment+s[end:]
start=s.index('##### CP-DEC-08-KARDEX-COMPRAS-001');end=s.index('<a id="contrato-DEC-07-VENCIDOS-FILTRO">',start)
fragment=s[start:end]
fragment=fragment.replace('**Estado:** EJECUTADO PARCIAL.14-F contrastaC-02 para asignaciones nuevas, ausencia histórica y dato parcial. C-01 y paginación/filtros/totales deC-03 siguen pendientes.','**Estado:** EJECUTADO en muestra14-H2 paraC01/C02/C03: SQLite secuencial yChrome, saldos conocidos, filtros, páginas, legado y permisos. ConcurrenciaPG, estabilidad entre páginas mientras cambian datos y volumen requieren15; no se transfieren garantías delbuild14-F.')
fragment=fragment.replace('**Evidencia de ejecución:**','**Evidencia de ejecución:** [Servidor14-H2](auditoria_por_etapas/resultados/evidencias/14-H2-20261114/servidor/INFORME.md), [Chrome14-H2](auditoria_por_etapas/resultados/evidencias/14-H2-20261114/navegador/RESUMEN.md). Antecedente14-F conservado:')
fragment=fragment.replace('**Datos de prueba:** Movimientos conocidos','**Datos de prueba:** Cursor adicional14-H2:10+10+5−22−1=2, venta22 con asignaciones10/10/2; período posterior alsegundo ingreso abre20/cierra2. Movimientos conocidos')
s=s[:start]+fragment+s[end:]
write(p,s)
views.generate()
source=sha(p);build=suite['build'];before=obj(OUT/'build-antes.json');executed=sha(OUT/'08-ejecutado.md')

_,_,_,criteria=views.parse();texts={c['id']:c['text'] for c in criteria}
specs=[
 ('HU-INV-04/CA-01','CUMPLE','Secuencias20/30/25/23/24 y10/20/25/3/2; orden ascendente, lote y saldo. Legado odesajusteNo disponible.','01,02,19,20; test_written_case,three_origins,negative_sequence,compensating_discrepancy'),
 ('HU-INV-04/CA-02','CUMPLE','ReferenciasR1/R2, responsable/proveedor capturados y asignaciones preservadas. SOL futuro noaplica aentrada directa.','01,02; three_origins; regresión14-G/H1'),
 ('HU-INV-04/CA-03','PARCIAL','Carga etiquetada/capturada y ajuste con motivo/autor visibles. Nombre delautor de ajustes sigue maestroactual, sin fotografía histórica.','01,11,12; test_written_case; test_audit08 traceability'),
 ('HU-INV-04/CA-04','CUMPLE','Fechas/tipo/períodoLima/errores/vacío yparámetros; controles yrecarga probados.','02..10,14; invalid_dates,empty_period,written_case'),
 ('DEC-08-KARDEX-COMPRAS/C-01','CUMPLE','Apertura/cierre independientedeltipo, saldo real porfila, variación filtrada; no resta retrospectiva desdeactual.','02,10..12; known_cases,per_lot'),
 ('DEC-08-KARDEX-COMPRAS/C-02','CUMPLE','Salida22 atribuida10/10/2; incompleta/identidadambigua señalaausencia ynoinventaFEFO.','02,19; incomplete_allocation,legacy_input; regresión14-F'),
 ('DEC-08-KARDEX-COMPRAS/C-03','CUMPLE','25+1 ajustes empatados, orden estableUUID, filtros/variación26constantes. GET/403/405 sinmutación.','11..16; same_instant_pages,roles_methods'),
]
rows=[dict(criterio=cid,texto=texts[cid],clasificacion=status,alcance='Muestra ejecutada; no garantía universal. '+detail,
    evidencia=case,pendiente='Concurrencia/volumen15; historia de ajustes y datosoperativos según informe') for cid,status,detail,case in specs]
write(OUT/'criterios-final.json',json.dumps(dict(pasada=1,sublote='14-H2',criterios=rows,
    clasificaciones=dict(Counter(r['clasificacion'] for r in rows))),ensure_ascii=False,indent=2))

write(OUT/'servidor/INFORME.md',f'''# Servidor14-H2 · 14/11/2026 Lima

Primera pasada. Python3.12.10/Django5.2.18/SQLite3.49.1. Cada corrida configura APP_ENV=test y SQLite en memoria antes de django.setup; no conecta a la base operativa. Build198 `{build}`. Fuente08 ejecutada `{executed}`; fuente final `{source}` conserva los sietecriterios y actualiza estados/evidencia.

```powershell
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-H2-20261114/servidor/regresion.py <directorio-nuevo>
```

| Corrida conservada | Resultado | Alcance |
|---|---|---|
| [corrida-1](corrida-1/regresion-final.txt) |595/603;8errores;84.154s|Error de fixture: load.lots.get() incluía recepción posterior. Se usa línea inicial capturada; no cambio de producto para aprobar|
| [final, antes deCSS](final/regresion-final.txt) |604/604;98.310s|Añadida prueba de intercalación delecturas; HTML funcional, defecto móvil aún pendiente|
| [final2, vigente](final2/regresion-final.txt) |604/604;97.397s|Fuentes estables y ninguna migración pendiente. [Manifiesto](final2/regresion-manifiesto.json)|

Doce tests nuevos en inventory/test_audit14h2_ledger.py verifican: casoescrito20+10−5−2+1=24; cursor10+10+5−22−1=2 yventa multilote;26ajustes al mismoinstante con25+1páginas;15variantes inválidas de fechas/tipo/página/duplicados; extremos de año1/9999 ysegundo59.999999delminutofinal; entrada heredada; asignación parcial eidentidadambigua; discrepancias compensadas porlote; FK deorigen incoherente; secuencia negativa; lote añadido entrelecturas; roles/métodos/productoinactivo/productovacío. GET yrechazos contrastan26tablas denegocio, excluyendo sesiones/login.

El caso escrito usa instantes09:00..13:00Lima deldía anterior alensayo en lugar de fijar12/11; cantidades/orden/resultados se conservan. El cursor adicional abre20 al10:01 yfiltra soloVenta: saldo3, cierre2, variación−22. El caso de páginas conserva total26/variación+26/apertura50/cierre76 enambaspáginas. La consulta sigue dentro del presupuesto histórico15queries ensu prueba existente; no suponeSLArendimiento ni costo constante.

Una expectativa histórica exigía ausencia de saldo/filtros; se reemplaza porpresencia conforme aINV04seleccionado. Las rutas globalesINV05/06 siguenausentes y su prueba se conserva. No hay migración nueva ni cambio en servicios deescritura. La prueba deintercalación no utiliza conexionesconcurrentes:demuestra que ellector no falla conKeyError anteun lote nuevo entrepasos, no aislamientoPG.

No ejecutado: carreraPG delKardex, paginación mientras se insertan datos, volumen productivo, caída real, regularización delegado. Dosramas deaviso (cabecera incompleta/dobleorigen) inspeccionadas, no inyectadas enH2; el resto deincertidumbres tieneprueba específica. [Criterios](../criterios-final.json) · [Caso](../../../../../08_Historias_de_Usuario.md#CP-HU-INV-04-001).
''')

write(OUT/'navegador/RESUMEN.md',f'''# Navegador14-H2 · 14/11/2026 Lima

Primera pasada; Chrome157.0.8103.78, Playwright1.65.1, WSGI loopback/puertoaleatorio, SQLite temporal independiente; datos ficticios, es-PE/America-Lima. Contraseñas yCSRF no se guardan. CadaJSON conserva texto/controles/ruta/rol ytestigo denegocio; manifiestos registran versión y fuentes.

| Carpeta | Observaciones/capturas | Resultado |
|---|---|---|
| [antes](antes/ejecucion.json) |3/3|Filtro y página ignorados, sin saldo; trescomparaciones de defecto verdaderas|
| [despues](despues/ejecucion.json) |5/3|Incompleto: runner esperaba«Seleccione» yDjango mostraba«Escoja». Producto rechazó opción inválida; no se cambia elmensaje paraaprobar|
| [final](final/ejecucion.json) |20/15|Funcional completo; revisiónvisual descubrió lotes y−22partidos enmóvil|
| [final2](final2/ejecucion.json) |20/15|Incluye degradaciónlectura, antes deCSSfinal|
| [cadena-final](cadena-final/ejecucion.json) |44/14|Cadena general antes deCSSfinal|
| [final3 vigente](final3/ejecucion.json) |20/15|Saldos/filtros/páginas/roles/legado/desajuste yCSSmóvil verificados|
| [cadena-final2 vigente](cadena-final2/ejecucion.json) |44/14|Revalidaciónconectada de ADMIN hasta cierre deVENDEDOR sobre runtimefinal|

El casoKardex prepara maestros ymovimientos porORM/servicios con relojcontrolado:10@3,R1C10@6,R2C5@8, venta22ymerma1;estadospersistidos ylecturaChrome son reales,pero no se atribuye altaUI aesa fixture. La cadena44sícrea categoría/producto/proveedor porADMIN, carga3+7 porALMACENERO, abre100/vende4×3.55=14.20 porVENDEDOR, merma1deja5,ADMINcontrasta yVENDEDORcierra114.20sin diferencia.

ChromeKardex prueba menú→consulta, saldos10/20/25/3/2, filtro10:01..13:00soloVenta conapertura20/cierre2/variación−22/saldo3,recarga/limpiar,períodoincompleto/invertido,tipo/páginainválida/fuera,parámetrorepetido,vacío conapertura/cierre2,25+1ajustesempatadosconvariación26ypreservaciónparámetros,lecturaALMACENERO,403VENDEDOR,POST405sinmutación,móvil390×844ytable-scroll,legadoNo disponible ydesajusteinducidoSQLquenofinge saldo. Las lecturas/rechazoscomparan huellas; la modificaciónSQLfinal esun control técnico declarado, no operación deusuario.

Capturas finales02/12/17/18/19/20 revisadas para semántica ysaldos, navegación, legibilidad móvil yavisos. La correcciónCSS mantiene ancho300del detalle, tabladesplazable y−22enunalínea. Escritorio1280×900; móvil esun viewport, no teléfonofísico. No se afirma impresión ni accesibilidadcompleta.

Fuente08 ejecutada `{executed}`; final `{source}`. Los manifiestos de final3 ycadena-final2 coinciden porarchivo conelbuildfinal198 `{build}`;ambosrecorridosestables. La fuente08finalañade resultados sin cambiar lossietecriterios. Las64observaciones finalestienenalcance solapado; no64HU/criterios.

```powershell
$env:PYTHONPATH='C:/Users/walte/AppData/Local/Temp/audit14d-browser-6f523915'
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-H2-20261114/navegador/recorrido_kardex.py <directorio-nuevo> --final
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-D-20261113/navegador/recorrido.py <otro-directorio-nuevo>
```

El entornoPlaywrighttemporalpuedecaducar; lasversionesestánregistradas. `recorrido_kardex_inicial.py` conserva elrunnerprevioconexpectativalocalizadaerrónea. Sin--final, elrunner soloregistradiagnóstico; reproducirel«antes» requiere elproductoarchivado. No se restauró automáticamente sobretrabajoposterior.
''')

cursor='14-I-MERMA-01'
report=f'''<a id="vigente-14-h2"></a>
## Estado vigente14-H2 · 14/11/2026, Lima

**Primera pasada. Etapa14 PARCIAL. SubloteH2 concluido para la muestra deKardex.** Ahora la consulta muestra saldo cronológico, apertura/cierre, filtros de fecha/tipo y páginas25. Cuando el origen no permite conciliar, muestra saldo no disponible. El próximo cursor es **{cursor}**, constancia demerma e historia deautor/origen. No se declaran completos otros módulos.

### Versiones y fuentes

| Elemento | CorteH2 |
|---|---|
|08 inicial|`{before['documentos']['08_Historias_de_Usuario.md']}`|
|08 durante pruebas|`{executed}`; [copia](evidencias/14-H2-20261114/08-ejecutado.md)|
|08 final|`{source}`;74HU/287criterios/113casos escritos|
|HEAD|`{before['head']}`; cambios locales anteriores preservados|
|Build final|198archivos `{build}`;7fuentes deproducto nuevas/modificadas|
|Entorno|Python3.12.10/Django5.2.18/SQLite3.49.1;Chrome157.0.8103.78/Playwright1.65.1;WSGIlocal, basesficticiasseparadas|
|Compatibilidad|Final3 ycadena-final2 coinciden porarchivo conelproducto final; corridasestables. Sinmigración nueva, baseoperativa ni despliegue|

[Informe H1 preservado](evidencias/14-H2-20261114/antes-ETAPA-14.md) · [Estado anterior](evidencias/14-H2-20261114/antes-ESTADO_GENERAL.md) · [Snapshot previo](evidencias/14-H2-20261114/build-antes.json) · [Inventario bidireccional](soporte/14-H2-inventario.md) · [Decisiones y recomendaciones](soporte/14-H2-disposiciones.md).

### Hallazgos, cambios y pruebas

El diagnósticoChrome reprodujo filtros/página ignorados y ausencia desaldo. La consulta nueva deriva eventos desde fotografíasH1/G y asignacionesF, comprueba cantidades porlote y ordena porinstante+ID. Calcula antes defiltrar/paginar. Corrige tresincumplimientos iniciales sin reducir loscriterios: cronología/saldo, filtros y apertura/cierre/variación.

Caso escrito20+10−5−2+1 deja24; salidas5y2 conservansaldos25y23, aperturareal20ycierre24. Cursor10+10+5−22−1 deja2; elperíododespuésdeR1abre20, soloVenta muestra−22ysaldo3,cierre2.26ajustesempatadosproducen25+1filas,total26yvariación+26enambaspáginas. Un totalqueconcilia porcasualidadconerrorescompensadosporlote no aprueba saldo.

La revisiónvisualdescubrió un defectomóvil aunconchecksfuncionalesverdes: lotes y−22partidos. CSSacotadomantienedetallelegible ytabladeancho desplazable, sin desbordar la página. Se reejecutaron navegadoryregresióntrascorregirlo. Lasexpectativas antiguas deausencia defiltros/saldo seajustaron aINV04seleccionado; INV05/06 siguenfuturas.

Servidor:595/603enprimera corrida por8erroresdefixture deorigen;604/604antesdeCSSy **604/604final**,12tests nuevos,97.397s,fuentesestablesysincambiosdemigración. [Informe reproducible](evidencias/14-H2-20261114/servidor/INFORME.md). Chrome **20observaciones específicas+44decadena**,15+14capturasfinales. [Resultadosycomandos](evidencias/14-H2-20261114/navegador/RESUMEN.md). Losconjuntos se solapan.

### Cobertura y pendientes

Sietecriteriosprincipales, **6CUMPLE enmuestra y1PARCIAL**. CA03permaneceparcialporqueautor deajuste noestá fotografiado históricamente; se observanmotivo yresponsableactual. [Textoliteral,estadoyevidencia porcriterio](evidencias/14-H2-20261114/criterios-final.json).24familias decontroles/mensajes/salidas trazadas; dosramas deaviso(cabeceraincompleta/dobleorigen) soloporinspección,noinyectadas. No se declara coincidenciatotal.

Se revalidó la cadenaADMIN→ALMACENERO→VENDEDOR→ALMACENERO/ADMIN→VENDEDOR desdealtas hasta cierre; permisos,errores,estado,vencimientoypersistencia según44pasos. Los servicios y resultadosde[05](ETAPA-05.md),[06](ETAPA-06.md),[08](ETAPA-08.md),[11](ETAPA-11.md) y[12](ETAPA-12.md) se enlazan mediante [14-F](#vigente-14-f),[14-G](#vigente-14-g),[14-H1](#vigente-14-h1). Sus demásestados/carreras/dispositivos siguenheredadosono reejecutados; no se completaron esosmódulosporlasuite.

08seactualizó,07/09/03se regeneraron,02/14/16/21y00/01/continuidad/controlse sincronizaron. [Verificación final](evidencias/14-H2-20261114/validacion-final.json) prueba coherencia/snapshots/compatibilidad, no aprobación integral. Elfundamento esINV04/DEC08aceptados ydelegaciónvigente; ningunapropuesta comercial seacepta por redactarla.

### Cursor exacto {cursor}

Inventariar HU-INV-02/CA01..04 yRN05/C01/C03/C04, conDOC03AI/RN14/RN28. CargaA10@3vigente;ALMACENERO confirmaDAÑO2conexplicación y obtiene constanciapropia: referencia/fecha/autor/producto/lote/cantidad/motivo/explicación originales, stock8, promedio3 ycostosalida3, caja/ventas/preciointactos. ADMINconsulta;VENDEDOR403. Renombrarmaestros,recargar ycomprobarfotografía. Reenviar lamismaclave devuelve resultadoanterior sin duplicar;contenidodivergente/rol/estado/fecha/cantidadinválidos no mutan. Variantesvencimiento/robo enlotescaducos yproducto inactivo,origenR1/R2conmismolotecomercial ylegadodesconocido. RevalidarKardex/venta/cajayrollback; impresiónbrowseracotada, dispositivofísicoNo ejecutado.

Saldo deKardex está verificado enlecturas secuenciales; snapshotconcurrentePG, páginasmientrascambiaeldato,volumenymemoriarequieren15. No inferir aperturaoperativa delegados. Constanciamerma,autorhistóricodeajuste,lote nuevoporajusteycosto documentadodesdefísico0 siguenencargos propios. Despuéscompletar14 yprimera15–17; preparar00ysegunda01–17,con evidenciaanteriorconservada.

## Registro anterior14-H1, conservado con sus límites
'''
p=RES/'ETAPA-14.md';old=read(p)
write(p,'# ETAPA-14 · Integración por roles\n\n'+report+'\n'+old.split('\n',1)[1].replace('## Estado vigente14-H1','## Estado registrado14-H1',1))
p=RES/'ESTADO_GENERAL.md';s=read(p)
s=s.replace('# Estado general vigente de auditorías · 13/11/2026 (actualizado 14-H1)','# Estado general vigente de auditorías · 14/11/2026 (actualizado 14-H2)',1)
start=s.index('La etapa13 está finalizada');end=s.index('\n\n| Etapa',start)
s=s[:start]+f'La etapa13 está finalizada para el panel mínimo. La etapa14 concluyóH2: saldos, filtros ypaginación deKardex verificados enmuestra. Sigue **PARCIAL** por constanciademerma, historia deajustesydemás pendientes.604/604regresión;20observacionesChrome específicas y44decadena. **Cursor{cursor}.**15–17 ysegunda pasada pendientes. [Informe vigente](ETAPA-14.md#vigente-14-h2) · [Estado anterior](evidencias/14-H2-20261114/antes-ESTADO_GENERAL.md).'+s[end:]
s=re.sub(r'^\| \[14\].*$',f'| [14](ETAPA-14.md#vigente-14-h2) Integración por roles |14/11/2026|PrimeraH2:7criterios/24familias;6CUMPLEen muestra,1PARCIAL.20+44observacionesChrome;12tests nuevos;604/604regresión.|**PARCIAL. H2 concluido**|Kardex secuencial verificado. Merma, historiaajustes,PG,volumen,datooperativo pendientes.|{cursor}:baja2deA10@3,constancia histórica, reenvío ystock8|',s,flags=re.M)
s=s.replace('| 14-H2-KARDEX-SALDOS-01, integración parcial |',f'| {cursor}, integración parcial |')
s=s.replace('## Registro vigente14-H1','## Registro anterior14-H1')
s+=f'\n\n## Registro vigente14-H2 · 14/11/2026 Lima\n\nPrimera pasada.08final `{source}`;build198 `{build}`.74HU/287criterios/113casos.6CUMPLE enmuestra,1PARCIAL;20+44observacionesChrome,604/604regresión. Fuentes anteriores preservadas yvistas regeneradas. Cursor{cursor}; etapanocompleta. [Informe](ETAPA-14.md#vigente-14-h2) · [Validación](evidencias/14-H2-20261114/validacion-final.json).'
write(p,s)

sections={
'02_Diseno_Tecnico_R1_PMV.md':'''## Concreción14-H2 · consulta deKardex

inventory/ledger.py deriva entradas desdeInitialLoadLine/StockReceiptLine, ventas yallocations, bajas yajustes. Orden total instante+IDdeorigen+tipo. Concilia cantidades porlote ytotal; faltante/relaciónincoherente/asignaciónparcial/identidadambigua/secuencianegativa/desajuste impidensaldo. La consulta no crea anclas ni mutaBD. Evento sinorigen conocido conserva cantidadNo disponible, noLot.initial_quantity.

MovementFilterForm valida períodoLima por minuto inclusivo, tipos, parámetrosrepetidos y página. select_period calculaapertura/cierre antesdefiltrar y paginar25; variación delconjuntofiltrado completo. Datosinválidos no retornanresultados engañosos. Enlaces mantienen filtros. Prefetch/select_related conservanpresupuestoqueries existente; historial completo enmemoria, noSLAvolumen. Lote nuevo entrelecturas produce aviso sin500,pero consistenciaconcurrentePGrequiere15. CSSlocalmantiene tabla desplazable y cifras legibles en390px. Sinmigración.''',
'14_Sprint_Planning.md':f'''## Resultado y preparación14-H2 · 14/11/2026

Kardex con saldo conocido,filtros,páginas25 ylegado explícito verificado enmuestra;604/604regresión y20+44observacionesChrome.6de7criterioscumplen enmuestra;CA03parcial porautorhistóricodeajustes. Etapa14parcial. Siguiente{cursor}, HU-INV-02/CA04yRN05/C03: constancia propia inmutable,roles,reenvío,variantesy efectoscruzados. NoagregarhistorialesglobalesINV05/06futuros. Volumen/concurrencia/recuperación/datosoperativosconservanpendientes.''',
'16_Task_Breakdown.md':f'''## Estado14-H2 · 14/11/2026

DEC08/INV04: consulta derivada, conciliaciónporlote, apertura/cierre, filtros alminuto,tipo,página25,errores/duplicados,variación total, estadosdesconocidos y móvil.12tests nuevos;604/604regresión;20+44observacionesChrome.08casosactualizados;sinHU nueva ni migración.

{cursor}: capturar constanciademerma yresultadoidempotente, preservarlegado, probarroles/errores/rollback yrevalidarKardex/costo/caja. Autorhistóricodeajustes/lote nuevo/costoQ0 siguen pendientespropios. Medirvolumen ylecturasconcurrentesPG en15; no cerrar esas tareas por paginar HTML.''',
'21_Alcance_Actual_y_Diferencias.md':f'''## Diferencia verificada14-H2 · 14/11/2026

Kardex yaimplementa ordenascendente,saldo conocido,filtrosypaginación25. Si no puedereconstruir origen/conciliarporlote, muestraNo disponible; se evita inventar pasado desdeactual. Se mantieneINV04seleccionado yHUINV05/06futuras;no nuevaHU/criterio ni ampliación comercial.6criterioscumplen enmuestra y1parcial;604/604suite,20+44Chrome. Etapa14parcial,cursor{cursor}; constanciademerma,historiaajuste,PG/volumen/operaciónpendientes.''',
'01_Proyecto_y_Releases.md':f'''## Continuación14-H2 · 14/11/2026

ConsultaKardexcorregida yverificada enmuestrasaisladas:saldoesperado, filtros que no alteranhistoria,páginas ylegadoexplícito.604/604pruebas y20+44observacionesChrome. La cadena completa entre roles se revalidó; no equivale a entregar todoslos módulos ni aautorizarpiloto. Cursor{cursor}.''',
}
for name,content in sections.items():
    p=ROOT/name;write(p,read(p)+'\n\n'+content+'\n\n[Informe14-H2](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-h2) · [Decisiones](auditoria_por_etapas/resultados/soporte/14-H2-disposiciones.md).')
p=ROOT/'00_LEEME_PLANIFICACION.md';s=read(p).replace('14-D/E/F/G/H1.','14-D/E/F/G/H1/H2.').replace('14-H2-KARDEX-SALDOS-01',cursor);write(p,s)
p=ROOT/'auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md';s=read(p)
s=s.replace('**14-H2-KARDEX-SALDOS-01**,continuación de la dependencia14-H1',f'**{cursor}**,continuación14-H2')
s=s.replace('sobre runtime14-H1','sobre runtime14-H2')
s=s.replace('ETAPA-14.md#vigente-14-h1','ETAPA-14.md#vigente-14-h2')
s=s.replace('El cursor aborda saldo cronológico,filtros y paginación,con origen incompleto explícito.','Saldo cronológico,filtros y paginación tienen evidencia secuencial14-H2; el cursor aborda constancia demerma e historia inmutable, con legadodesconocido explícito.')
write(p,s)
p=ROOT/'r1-pmv/CONTROL_SPRINTS.md';s=read(p).replace('](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-g)','](../auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-g)')
write(p,s+f'\n\n## Revalidación14-H2 · 14/11/2026 Lima\n\nKardex secuencial: saldo/filtros/paginación y origen desconocido verificados;604/604regresión,20+44observacionesChrome. H1yaaportó fotografía inicial. Etapa14parcial;{cursor}. Historiadeajustes,PG/volumen y datosoperativos siguenpendientes. [Informe](../auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-h2).')
print(json.dumps(dict(source08=source,build=build,criterios=len(rows),cursor=cursor),indent=2))
