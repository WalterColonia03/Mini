"""Materializa el cierre H1 solo si la regresión final terminó sin errores."""
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

def read(p): return p.read_text(encoding='utf-8-sig')
def obj(p): return json.loads(read(p))
def write(p,s): p.write_text(s.rstrip()+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

suite=obj(OUT/'servidor/final2/regresion-manifiesto.json')
log=read(OUT/'servidor/final2/regresion-final.txt')
assert suite['salida']==0 and not suite['cambios_durante_prueba']
assert 'Ran 592 tests' in log and '\nOK\n' in log and 'No changes detected' in log
files=runpy.run_path(str(OUT/'verificar.py'))['product']()
assert files==suite['fuentes']
build=suite['build']; source=sha(ROOT/'08_Historias_de_Usuario.md')
before=obj(OUT/'build-antes.json')
browser={n:obj(OUT/'navegador'/n/'ejecucion.json') for n in ('antes','despues','final','cadena-final','recepciones-final')}
for n,count in (('final',16),('cadena-final',44),('recepciones-final',23)):
    assert browser[n]['estado']=='recorrido_completo' and browser[n]['build_estable'] and len(browser[n]['pasos'])==count
runtime_differences={}
for n in ('final','cadena-final','recepciones-final'):
    executed=obj(OUT/'navegador'/n/'build-final.json')['archivos']
    diff=[p for p,h in executed.items() if files.get(p)!=h]
    assert diff==['inventory/test_audit14h_initial_history.py'],diff
    runtime_differences[n]=diff

_,_,_,criteria=views.parse()
spec={c['id']:c['text'] for c in criteria}
rows=[]
for cid,status,detail in [
 ('HU-INV-01a/CA-01','CUMPLE','Muestra de carga única ALMACENERO, ADMIN/VENDEDOR denegados; no aprobación universal de roles.'),
 ('HU-INV-01a/CA-02','PARCIAL','Normalización, costo4, límites y vencimiento revalidados por suite y muestra UI; no toda frontera de cada campo en Chrome.'),
 ('HU-INV-01a/CA-03','PARCIAL','Rechazo secuencial y cuatro fallos posteriores a escritura sin residuos; carreraPG/caída real pendientes15.'),
 ('HU-INV-01a/CA-04','CUMPLE','Muestra3×2.1234+7×4 = promedio3.4370; UI3.44, físico10; prueba de expiración conserva físico.'),
 ('HU-INV-01a/CA-05','PARCIAL','Fotografía de número/cantidad/costo/fecha/instante y guard recibido preservados; FEFO revalidado en cadenas, defensa SQL integral pendiente.'),
 ('HU-INV-04/CA-01','INCUMPLE','Sigue sin saldo y con orden descendente; no implementado enH1.'),
 ('HU-INV-04/CA-02','PARCIAL','Revalidación de referencias/autor/proveedor de recepción en23 checkpoints; SOL futuro y totalidad deKardex no cerrada.'),
 ('HU-INV-04/CA-03','PARCIAL','Carga nueva con origen/cantidad/autor conservados; ajuste conserva motivo; resto de historia/autor de bajas/ajustes abierto.'),
 ('HU-INV-04/CA-04','INCUMPLE','Filtros de período/tipo ausentes; H2 pendiente.'),
 ('DEC-08-KARDEX-COMPRAS/C-01','INCUMPLE','Sin saldo apertura/cierre/total filtrado ni orden ascendente; no se cuentan como ejecutados.'),
 ('DEC-08-KARDEX-COMPRAS/C-02','PARCIAL','Asignaciones y referencias revalidadas en recepción conectada y cadena; saldo por lote conciliado pendiente.'),
 ('DEC-08-KARDEX-COMPRAS/C-03','PARCIAL','Permisos y GET no mutante revalidados; paginación25 y totales de conjunto ausentes.'),
]:
    rows.append(dict(criterio=cid,texto=spec[cid],clasificacion=status,alcance=detail,
        grupo='Dependencia ejecutada' if cid.startswith('HU-INV-01a') else 'Kardex inventariado',
        evidencia='servidor/INFORME.md; navegador/RESUMEN.md',siguiente='14-H2-KARDEX-SALDOS-01; etapa15 donde se indica'))
write(OUT/'criterios-final.json',json.dumps(dict(pasada=1,sublote='14-H1',criterios=rows,
    clasificaciones=dict(Counter(r['clasificacion'] for r in rows))),ensure_ascii=False,indent=2))

server=f'''# Servidor 14-H1 · primera pasada

Base SQLite en memoria nueva por corrida; APP_ENV=test y configuración sustituida antes de django.setup. No se leyó ni migró la base operativa. Python3.12.10, Django5.2.18, SQLite3.49.1. Build final196 archivos `{build}`. Comando desde la raíz:

```powershell
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-H-20261113/servidor/regresion.py <directorio-nuevo>
```

| Ejecución preservada | Resultado | Interpretación |
|---|---|---|
| [corrida-1](corrida-1/regresion-final.txt) |589/591;1fallo+1error;86.190s|Expectativas anteriores de costo2 y contexto subsequent_lots; actualizadas conforme a08. Siete tests nuevos pasaron|
| [final, intermedia](final/regresion-final.txt) |591/592;1fallo;99.743s|La fixture añadida exigía salida del loteA con igual vencimiento y posible instante empatado. FEFO podía elegirB porUUID. Se separaron vencimientosA/B/POST; no se alteróFEFO|
| [final2, vigente](final2/regresion-final.txt) |592/592 OK|Fuentes estables, sin migraciones pendientes de generar. [Manifiesto](final2/regresion-manifiesto.json)|

Ocho tests nuevos en inventory/test_audit14h_initial_history.py: fotografía ante renombres/ajuste/recepción/venta/merma; proveedor ausente/cantidad999999/costo9999999.9999/número64/escapeHTML; vencimiento y producto inactivo; legado sin original; cuatro fallos postwrite; rol/fecha/estado/repetición; consulta/alias/cache/GET/POST; migración. Cuatro puntos postwrite guardaron antes de lanzar excepción: cabecera, lotes, líneas, promedio. Se contrastan26 tablas de negocio de catalog/inventory/cash/sales; sesiones/login quedan fuera de esa igualdad.

Migración inventory0008→0009 conserva columnas y filas anteriores, añade cabecerasNULL y cero líneas inferidas; la prohibiciónSQL de modificar received_at permanece. No se simuló corte real del proceso ni carreraPG ni reversión con datos nuevos. Las relaciones y snapshots dependen del servicio para consistencia transversal; no se certifican ante escrituras arbitrarias.

La suite global incluye pruebas históricas que se reejecutan; no sustituye cobertura navegador ni aprueba todas las HU. [Caso](../../../../../08_Historias_de_Usuario.md#CP-HU-INV-01a-003) · [Matriz acotada](../criterios-final.json).
'''
write(OUT/'servidor/INFORME.md',server)

browser_report=f'''# Navegador 14-H1 · primera pasada

Chrome157.0.8103.78, Playwright1.65.1, WSGI local en puerto aleatorio, SQLite temporal independiente por recorrido; es-PE/America-Lima. Cuentas y datos ficticios. El runner borra únicamente su propia base temporal al cerrar. No guarda contraseñas ni cookies/tokens; los JSON registran rutas, controles, texto y testigos sanitizados.

| Evidencia | Checkpoints / capturas | Resultado |
|---|---|---|
| [antes](antes/ejecucion.json) |3 /3|Las4comparaciones originales fueron falsas: producto, autor, proveedor y costo4. No exige que el defecto pase|
| [después, intermedia](despues/ejecucion.json) |15 /13|Fotografía y consulta móvil funcionaron; conservada como ejecución anterior|
| [final H1](final/ejecucion.json) |16 /14|4comparaciones verdaderas, carga UI3+7, renombres técnicos, ajuste UI+2, original3/disponible5, ADMIN consulta, VENDEDOR403, reenvío sin efectos, legado explícito y tabla móvil desplazada|
| [cadena general final](cadena-final/ejecucion.json) |44 /14|ADMIN crea categoría/producto/proveedor; almacenero carga3+7; vendedor abre100 y cobra14.20, almacenero merma1; admin observa5 y venta; vendedor cierra114.20 exacto|
| [recepciones final](recepciones-final/ejecucion.json) |23 /17|Carga10@3 porfixture; entradasUI10@6 y5@8, referenciasR1/R2/reintento; venta22, merma1, stock2 y cierre320; cantidades originales conservadas|

Son recorridos con cobertura solapada; no83casos independientes ni cierre completo de módulos. Las16observaciones H1 separan fixtures de maestros/renombres/ausencia histórica (preparaciónORM/SQL declarada) de accionesUI. La cadena44 demuestra el alta de maestros por administrador desde interfaz. El móvil es una ventana390×844, no un teléfono físico; escritorio1280×900. Las capturas03,10,13,13b y14 se revisan visualmente para cabecera original, cantidades, desplazamiento y legado.

Los tres recorridos finales tienen código de ejecución estable. Respecto del manifiesto final196 cambió solo inventory/test_audit14h_initial_history.py al corregir vencimientos de la fixtureFEFO; ningún modelo, servicio, vista, plantilla ni migración cambió después de esos navegadores. La compatibilidad se comprueba por archivo, no por atribuirles la huella completa posterior. 08 ejecutado `{browser['final']['plan08_inicio']}`;08 final `{source}` conserva los criterios y agrega resultado/evidencia al caso.

Reproducción desde raíz, con Playwright disponible en el entorno temporal ya instalado:

```powershell
$env:PYTHONPATH='C:/Users/walte/AppData/Local/Temp/audit14d-browser-6f523915'
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-H-20261113/navegador/recorrido_carga.py <directorio-nuevo> --final
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-D-20261113/navegador/recorrido.py <otro-directorio-nuevo>
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-G-20261113/navegador/recorrido_recepciones.py <tercer-directorio-nuevo> --final
```

Cada carpeta tiene indice.json, ejecución, fuente08 de inicio y manifiestos de producto. El entorno temporal puede caducar; las versiones/herramientas quedan registradas para reproducirlo. Saldos/filtros/paginación no se ejecutaron como implementados; impresión física,PG,caída real y datos operativos tampoco.
'''
write(OUT/'navegador/RESUMEN.md',browser_report)

report=f'''<a id="vigente-14-h1"></a>
## Estado vigente14-H1 · 13/11/2026, Lima

**Primera pasada. Etapa14 PARCIAL. Sublote H1 concluido: origen de cargas nuevas, dependencia del Kardex.** Se preservan cantidad/costo/número/fecha/instante y cabecera original; legado sin fotografía se declara incompleto. Saldo, filtros y paginación siguen pendientes en **14-H2-KARDEX-SALDOS-01**. No se cierran otros módulos.

### Versiones, alcance y evidencia

| Elemento | Valor |
|---|---|
|08 inicial|`{before['documentos']['08_Historias_de_Usuario.md']}`|
|08 ejecutado Chrome|`{browser['final']['plan08_inicio']}`|
|08 final|`{source}`;74HU,287criterios,113casos escritos|
|HEAD|`{before['head']}`, cambios locales previos preservados|
|Build final|196 archivos, `{build}`|
|Entorno|Python3.12.10/Django5.2.18/SQLite3.49.1;Chrome157.0.8103.78/Playwright1.65.1;WSGI loopback y bases ficticias separadas|
|Compatibilidad visual|Tres recorridos finales estables; solo difiere una fixture de test con respecto al build final, sin cambio de runtime. No se atribuye la huella posterior a capturas anteriores|

[Informe anterior íntegro](evidencias/14-H-20261113/antes-ETAPA-14.md) · [Estado anterior](evidencias/14-H-20261113/antes-ESTADO_GENERAL.md) · [Fuente y producto previos](evidencias/14-H-20261113/build-antes.json) · [Inventario bidireccional](soporte/14-H-inventario.md) · [Decisiones y recomendaciones](soporte/14-H-disposiciones.md).

El diagnóstico Chrome mostró pérdida de tres nombres originales y costo unitario redondeado. La nueva cabecera/InitialLoadLine guarda la fotografía en la transacción existente. La migración dejaNULL/ausencia de líneas en datos anteriores; no reconstruye historia a partir de FK, capacidad o fechas. La pantalla separa original3 de disponible5 tras ajuste+2, promedio inicial de actual y proveedor original del desactivado/renombrado. Movimientos enlaza la carga y declara cantidades antiguas desconocidas.

### Resultado y cobertura

Se inventariaron12criterios:5de la dependenciaINV01a y7deINV04/DEC08. Clasificación final: **2CUMPLE en muestra,7PARCIAL,3INCUMPLE**. Los tres incumplimientos son saldo/orden, filtros y apertura/cierre/total del Kardex; no están resueltos por H1. [Texto literal y estado de cada criterio](evidencias/14-H-20261113/criterios-final.json). Las13familias de salida nuevas/modificadas tienen ruta, rol, significado y evidencia en el inventario. Los campos de alta conservan requisitos; no se afirma toda frontera en Chrome.

Servidor:589/591 inicial;591/592 intermedia con un supuestoFEFO incorrecto enfixture; **592/592 final**, ocho tests nuevos y cuatro fallos postwrite comprobados, fuentes estables. [Comandos, resultados y límites](evidencias/14-H-20261113/servidor/INFORME.md). La corrección defixture separa vencimientos; no cambia FEFO para fabricar el resultado.

Chrome: **16 checkpoints H1,44 de cadena general y23 de recepción conectada**, con bases y alcance independientes que se solapan. La cadena revalida ADMIN→ALMACENERO→VENDEDOR→ALMACENERO/ADMIN→VENDEDOR desde maestros a cierre; las denegaciones, fecha/estado, reenvío y errores conservan testigos sin mutación según cada caso. [Navegador](evidencias/14-H-20261113/navegador/RESUMEN.md). No se presentan esos checkpoints como83criterios distintos.

Se revalidan las conexiones concretas de05 carga,06 recepción,08 ajuste/merma/movimientos,11 cobro y12 consulta/caja, manteniendo enlaces y límites de [14-E](#vigente-14-e),[14-F](#vigente-14-f),[14-G](#vigente-14-g). Sus demás pruebasPG, políticas, dispositivos y cobertura exhaustiva son heredadas o pendientes, no reejecutadas por extensión. La suite no cierra etapas enteras.

08 incorpora concreción y CP-HU-INV-01a-003 antes de regenerar07/09/03;02/14/16/21 y contexto00/01 se sincronizan. El fundamento es el requisito histórico ya aceptado y la delegación técnica vigente, no el mero texto de la propuesta. [Validación reproducible](evidencias/14-H-20261113/validacion-final.json).

### Cursor exacto y no ejecutado

**14-H2-KARDEX-SALDOS-01.** Crear carga nueva10@3 con fotografía, R1C10@6 y R2C5@8, vender22 y merma1:10+10+5−22−1=2. Inventariar cada control/mensaje y probar orden ascendente instante+ID, saldo por movimiento y conciliación por lote. Período posterior aR1 debe abrir20 y cerrar2; filtro solo venta conserva saldo real3 y variación−22, sin omitir entradas al calcular. Crear más de25eventos con empates y verificar páginas estables, total filtrado completo, parámetros y rechazos de fecha incompleta/invertida/tipo/página. GET/403 no mutan.

Si falta fotografía, asignación o identidad inequívoca, o hay desajuste por lote, mostrar saldo no disponible; nunca inferir apertura desde stock actual. Mantener referencias y fotografías H1/G/F. Después constancia de merma y otros pendientes14. Legado operativo, ajuste desde físico0 con costo documentado, volumen, escritura directa, concurrenciaPG, caída real y recuperación siguen abiertos.15–17 y segunda pasada01–17 pendientes; no se migró ni desplegó en operación.

## Registro anterior14-G, conservado con sus límites
'''
p=RES/'ETAPA-14.md';old=read(p)
assert 'id="vigente-14-h1"' not in old
write(p,'# ETAPA-14 · Integración por roles\n\n'+report+'\n'+old.split('\n',1)[1].replace('## Estado vigente14-G','## Estado registrado14-G',1))

p=RES/'ESTADO_GENERAL.md';s=read(p)
s=s.replace('(actualizado 14-G)','(actualizado 14-H1)',1)
start=s.index('La etapa13 está finalizada');end=s.index('\n\n| Etapa',start)
s=s[:start]+'La etapa13 está finalizada para el panel mínimo. La etapa14 concluyó H1, dependencia de historia inicial: fotografía de cargas nuevas y legado explícito. Sigue **PARCIAL** por saldo/filtros/paginación del Kardex, constancia de merma y demás pendientes.592/592regresión;16checkpointsChrome específicos,44de cadena y23de recepción, con alcance solapado. **Cursor14-H2-KARDEX-SALDOS-01.**15–17 y segunda pasada permanecen pendientes. [Informe vigente](ETAPA-14.md#vigente-14-h1) · [Estado anterior](evidencias/14-H-20261113/antes-ESTADO_GENERAL.md).'+s[end:]
s=re.sub(r'^\| \[14\].*$', '| [14](ETAPA-14.md#vigente-14-h1) Integración por roles |13/11/2026|Primera pasadaH1:12criterios inventariados;5dependencia y7Kardex;13familias de salida.16+44+23checkpointsChrome;8tests nuevos;592/592regresión.|**PARCIAL. H1 concluido**|Fotografía nueva verificada;3criterios de saldo/filtros incumplen;PG,legado operativo,merma y demás pendientes.|14-H2-KARDEX-SALDOS-01:10+10+5−22−1=2, apertura20 y paginación25|',s,flags=re.M)
s=s.replace('| 14-H-KARDEX-SALDOS-01, integración parcial |','| 14-H2-KARDEX-SALDOS-01, integración parcial |')
s+='\n\n## Registro vigente14-H1 · 13/11/2026 Lima\n\n'+f'Primera pasada.08final `{source}`;build196 `{build}`;HEAD se conserva.74HU/287criterios/113casos escritos. Se preservaron evidencia y producto previos, se corrigió historia de carga nueva y se revalidó el recorrido completo.592/592regresión;16+44+23checkpointsChrome con cobertura solapada.2CUMPLE en muestra,7PARCIAL,3INCUMPLE entre12criterios. Cursor14-H2-KARDEX-SALDOS-01. [Informe](ETAPA-14.md#vigente-14-h1) · [Validación](evidencias/14-H-20261113/validacion-final.json).'
s=s.replace('## Registro vigente14-G','## Registro anterior14-G')
write(p,s)

for name,section in {
'02_Diseno_Tecnico_R1_PMV.md':'''## Concreción14-H1 · fotografía de carga inicial

InitialInventoryLoad agrega cabecera nullable nombre160/código64/unidad8/autor120/proveedor160/RUC11/promedio14,4; ausencia de proveedor se guarda como cadena vacía y NULL representa legado. InitialLoadLine conserva número64, cantidad positiva, costo positivo14,4, vencimiento e instante original, con FK PROTECT y loteOneToOne. Unicidadcarga/número. El servicio existente valida y bloquea actor→producto→categoría→proveedor, crea cabecera/lotes/líneas y promedio dentro de una transacción. No se rellena historia antigua ni se reconstruye Lot; el guardreceived_at continúa vigente.

Consulta separa foto original y stock/costo actuales; Kardex usa la línea capturada y enlaza carga, sin deducir cantidad de capacidad. Las relaciones transversales y snapshots se protegen por el servicio, no se garantiza defensa ante SQL arbitrario. Cuatro fallos postwrite y migración aditiva verificados en SQLite. Reversión0009 elimina la foto; recuperación/PG requieren15. Saldo/filtros/paginación quedan enH2. Se descartaJSON sin esquema frente al patrón tipado ya empleado enrecepción.''',
'16_Task_Breakdown.md':'''## Estado14-H1 · dependencia de Kardex

DOC03AI/INV01a: cabecera y líneas originales, migración sin backfill, separación original/actual, enlace desde movimientos, legado no cuantificado, cuatro fallos postwrite y ocho tests nuevos.592/592regresión;16+44+23checkpointsChrome. El nuevo CP-HU-INV-01a-003 aporta evidencia acotada y no cierra los cincoCA completos.

Siguiente14-H2-KARDEX-SALDOS-01: ordernar eventos por instante+ID, conciliar por lote, calcular antes de filtrar/paginar, páginas25, períodoLima/tipo/errores y saldos no disponibles ante origen incierto. Revalidar H1/G/F y cadena. PG/caída/defensaSQL/volumen y constancia demerma conservan sus tareas.'''.replace('ordernar','ordenar'),
'14_Sprint_Planning.md':'''## Resultado y preparación14-H1

Se ejecutó primero la dependencia de fotografía inicial del Kardex. Cabecera/líneas nuevas conservan origen y cantidades; legado explícito.592/592regresión,16+44+23checkpointsChrome con conjuntos solapados. La etapa14 siguePARCIAL. El próximo sublote14-H2-KARDEX-SALDOS-01 mantiene los criterios de saldo/filtros/paginación; no se rebajaron para terminarH1. Preparar la secuencia10+10+5−22−1, período con apertura20 y más de25eventos. PG/recuperación/datos operativos y constancia demerma pendientes.''',
'21_Alcance_Actual_y_Diferencias.md':'''## Diferencia verificada14-H1

La historia de nuevas cargas iniciales ya no depende de nombres actuales ni capacidad mutable deLot. Se conservan cabecera y líneas originales y se distingue legado. Corrección técnica dentro deDOC03AI/INV01a ya seleccionados, sinHU nueva ni cambioMoSCoW; CP-HU-INV-01a-003 aumenta casos escritos a113.592/592regresión y16+44+23checkpointsChrome acreditan muestras conectadas, no cierre completo. Saldo/orden/filtros/paginaciónKardex siguen incumplimientos en14-H2-KARDEX-SALDOS-01; merma,PG,datooperativo y demás pendientes se conservan.''',
'01_Proyecto_y_Releases.md':'''## Continuación14-H1

Fotografía de carga inicial implementada como dependencia del Kardex y verificada en base ficticia.592/592regresión,16checkpoints específicos,44de cadena general y23de recepción conectada. Se mantienen separados original y actual, y no se inventa legado. La etapa14 sigueparcial; cursor14-H2-KARDEX-SALDOS-01. No se declara entrega delrelease ni de módulos completos.''',
}.items():
    p=ROOT/name
    write(p,read(p)+'\n\n'+section+'\n\n[Informe14-H1](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-h1) · [Fundamento y límites](auditoria_por_etapas/resultados/soporte/14-H-disposiciones.md).')

p=ROOT/'auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md';s=read(p)
s=s.replace('**14-H-KARDEX-SALDOS-01**,continuación14-G','**14-H2-KARDEX-SALDOS-01**,continuación de la dependencia14-H1')
s=s.replace('sobrebuild14-G','sobre runtime14-H1')
s=s.replace('ETAPA-14.md#vigente-14-g','ETAPA-14.md#vigente-14-h1')
s=s.replace('Snapshots de nuevas cargas iniciales,constancia de merma,costo documentado desdefísico0 y garantías de concurrencia conservan pendientes.','Fotografías de cargas nuevas verificadas enH1; legado desconocido conserva investigación. Constancia de merma,costo documentado desde físico0 y garantías de concurrencia conservan pendientes.')
write(p,s)
p=RES/'soporte/14-H-inventario.md';s=read(p).replace('en14familias','en13familias').replace('no son14HUs','no son13HUs');write(p,s)
print(json.dumps(dict(build=build,source08=source,criterios=len(rows),runtime_differences=runtime_differences),indent=2))
