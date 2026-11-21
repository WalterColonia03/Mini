"""Actualiza documentación del corte14-I y deriva vistas; no conecta bases."""
import hashlib
import importlib.util
import json
import re
import shutil
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
RESULTS=HERE.parents[1]
LINK='auditoria_por_etapas/resultados/evidencias/14-I-20261114'
sha=lambda data:hashlib.sha256(data).hexdigest()
read=lambda p:p.read_text(encoding='utf-8')
save=lambda p,s:p.write_text(s.rstrip()+'\n',encoding='utf-8')
if (HERE/'08-ejecutado.md').exists():raise SystemExit('Cierre ya iniciado; no sobrescribir evidencia previa.')
shutil.copy2(ROOT/'08_Historias_de_Usuario.md',HERE/'08-ejecutado.md')
s=read(ROOT/'08_Historias_de_Usuario.md')
s=re.sub(r'\*\*Revisión:14/11/2026\.\*\*[^\n]+',
    '**Revisión:14/11/2026.** Primera pasada: etapa13 finalizada para el panel mínimo; integración14-I verifica en muestra la constancia histórica de merma y el reintento entre sesiones. La etapa14 sigue PARCIAL por historia de ajustes, lote nuevo/costo documentado y otros pendientes. Build, evidencia y cursor14-J-AJUSTES-HISTORIA-01 en [ETAPA-14](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-i).15–17 y segunda pasada conservan la [secuencia](auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md).',s,count=1)
evidence=f'**Evidencia de ejecución:** [Servidor14-I]({LINK}/servidor/INFORME.md), [Chrome14-I]({LINK}/navegador/RESUMEN.md).'
states={
 'CP-HU-INV-02-001':'EJECUTADO PARCIAL en primera pasada14-I,14/11/2026: causas, constancia nueva, fotografía, roles y costo comprobados en muestras SQLite/Chrome. No acredita impresión física, resistencia a SQL privilegiado ni todas las fronteras de entrada.',
 'CP-HU-INV-02-002':'EJECUTADO PARCIAL en primera pasada14-I,14/11/2026: exceso y reenvío secuencial de mismaUUID en sesiones independientes rechazan/recuperan sin duplicar. Dos conexiones concurrentes PostgreSQL NO EJECUTADAS; pendiente15.',
 'CP-RN-05-001':'EJECUTADO PARCIAL en primera pasada14-I,14/11/2026: C01/C03 verificados en muestra de merma; parte secuencialC04. C02 de ajuste con lote nuevo y concurrenciaC04 siguen pendientes.',
}
for ident,state in states.items():
    start=s.index('<a id="'+ident+'"></a>');end=s.find('<a id="',start+1)
    if end<0:end=len(s)
    part=s[start:end]
    part=re.sub(r'\*\*Estado:\*\*[^\n]*','**Estado:** '+state,part,count=1)
    pos=part.index('\n',part.index('**Cubre:**'))
    part=part[:pos+1]+evidence+'\n'+part[pos+1:]
    s=s[:start]+part+s[end:]
idx=s.index('<a id="CP-INTEGRACION-ROLES-001"></a>')
idx2=s.index('**Precondiciones:**',idx)
s=s[:idx2]+f'**Revalidación14-I:** [44 checkpoints nuevos]({LINK}/navegador/cadena-final/ejecucion.json), mismo caso y datos ficticios, build actual. Se conserva el antecedente14-D; el alcance transversal completo sigue parcial.\n'+s[idx2:]
save(ROOT/'08_Historias_de_Usuario.md',s)
digest08=sha((ROOT/'08_Historias_de_Usuario.md').read_bytes())

context={
 '02_Diseno_Tecnico_R1_PMV.md':'''StockWriteOff incorpora UUID única nullable y huella de contenido normalizado; campos nullable de producto/código/unidad, responsable, número/vencimiento y origen. No se reconstruye legado. write_off_stock valida actor vigente, recupera misma operación antes de validar disponibilidad/fecha actuales y confirma fotografía+baja+stock/costo atómicamente. Clave ajena o divergente rechaza. HTTP exige UUID; llamadas internas sin clave son operaciones nuevas. Consulta GET por ADMIN/ALMACENERO, enlace desde Kardex e impresión web usan el mismo registro. El estado comercial inactivo no impide merma legítima. Migración0010 verificada solo en bases ficticias. No hay edición pública de constancia; protección frente a SQL privilegiado y concurrenciaPG conservan tarea15.''',
 '16_Task_Breakdown.md':'''RN-05 / DEC-08-CONSTANCIA-MERMA: vista, fotografías y reintento persistente implementados y verificados en muestra.10tests nuevos,614/614 de regresión,26+44 checkpointsChrome con conjuntos solapados. Tareas no cerradas: concurrenciaPG, protecciónSQL, recuperación, volumen, impresora física y diagnóstico operativo. Próximo14-J-AJUSTES-HISTORIA-01: fotografiar autor y lote de ajustes existentes, motivo y costo, conservar legado; revalidar Kardex y cadena. Lote nuevo/costo desde físico0 mantienen sublote propio posterior.''',
 '14_Sprint_Planning.md':'''Sublote14-I concluye para constancia nueva de merma e idempotencia secuencial entre sesiones. La etapa14 sigue PARCIAL: no se completa por aprobar614tests. Preparar14-J-AJUSTES-HISTORIA-01 con A10@3, ajuste ADMIN+2 y−3, renombrados y errores sin mutación. No seleccionar historias globales INV05/06 o REP08; PostgreSQL/recuperación/datos operativos siguen pendientes.''',
 '21_Alcance_Actual_y_Diferencias.md':'''Se resolvieron falta de constancia de merma, duplicación de unaUUID al cambiar sesión y lectura de autor/lote actuales como historia. Los registros nuevos preservan fotografía y los anteriores muestran ausencia explícita. Primera pasada14-I:6/7 criterios principales cumplen en muestra y1parcial por concurrencia.614/614 servidor,26+44 Chrome. Sigue pendiente historia de ajustes, lote nuevo/costo documentado, garantíasPG y operación. No se cierra release ni otros módulos.''',
 '01_Proyecto_y_Releases.md':'''Constancia y reintento de merma corregidos dentro de los contratos seleccionados; revalidados entre roles en bases ficticias. Se preservan las HU, MoSCoW y puntos; no se incorpora un módulo comercial nuevo. Primera pasada14 sigue PARCIAL, cursor14-J-AJUSTES-HISTORIA-01.15–17 y segunda pasada pendientes. Sin migración operativa ni despliegue.''',
 '00_LEEME_PLANIFICACION.md':'''Corte vigente14-I: constancia histórica e idempotencia de merma verificadas en muestra. Fuente08 y vistas07/09/03 coherentes. Primera pasada14 PARCIAL, cursor14-J-AJUSTES-HISTORIA-01; después completar14/15–17 y preparar segunda pasada01–17. No se sustituyen las fechas ni límites de resultados previos.''',
 'r1-pmv/CONTROL_SPRINTS.md':'''Revalidación local14-I:614/614 pruebas,26 checkpointsChrome específicos y44 de cadena; conjuntos solapados. Constancia y reintento de merma resueltos en muestra. Etapa14 parcial y próximo14-J-AJUSTES-HISTORIA-01. No acredita despliegue, PostgreSQL concurrente ni cierre de otros módulos.''',
}
for name,body in context.items():
    p=ROOT/name
    prefix='../' if name.startswith('r1-pmv/') else ''
    save(p,read(p)+f'\n\n## Continuación14-I · 14/11/2026 Lima\n\n{body}\n\n[Informe14-I]({prefix}auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-i) · [Disposiciones]({prefix}auditoria_por_etapas/resultados/soporte/14-I-disposiciones.md).\n')

cursor='''**14-J-AJUSTES-HISTORIA-01.** Primera pasada, continuar sobre el build14-I y preservar este corte. Inventariar HU-INV-03/CA01..02 y HU-INV-04/CA03 con RN05/RN14/DOC03AI/DEC08. Crear A10@3 con origen fotografiado; ADMIN ajusta+2 con motivo y luego−3: stock12→9, promedio3, costo de salida3, caja/ventas/precio intactos. Conservar instante, autor, producto/lote, motivo y origen del ajuste; renombrar maestros, recargar y contrastar historia. La carga inicial conserva cantidad original10 aunque cambie la capacidad del lote. ALMACENERO/VENDEDOR no ajustan; cantidad0/exceso/motivo vacío o inválido no mutan. Probar legado desconocido sin backfill, reenvíos, fallo postwrite y revalidar Kardex/merma/venta/caja. Lote nuevo y costo documentado desde físico0 son pendientes propios posteriores; no inventar apertura operativa de productos solo vencidos.'''
continuity=ROOT/'auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md'
c=read(continuity);start=c.index('## Punto de entrada')
c=c[:start]+f'''## Punto de entrada

El próximo cursor de primera pasada es **14-J-AJUSTES-HISTORIA-01**, continuación14-I. La constancia histórica de merma y el reintento secuencial entre sesiones tienen evidencia nueva; la etapa14 sigue **PARCIAL**. La cadena de altas, carga, caja, cobro, merma, revisión y cierre se revalidó en Chrome. Los resultados anteriores conservan fecha, build y límites.

Consultar [ESTADO_GENERAL](resultados/ESTADO_GENERAL.md), [PROTOCOLO_COMUN](PROTOCOLO_COMUN.md) y [ETAPA14 vigente](resultados/ETAPA-14.md#vigente-14-i). {cursor}

Concurrencia PostgreSQL, protección de historia ante SQL privilegiado, volumen, recuperación, dispositivo físico y diagnóstico/migración operativa no se aprobaron.15–17 siguen pendientes de primera pasada; después17 preparar00 y segunda01–17. [ETAPA17](resultados/ETAPA-17.md) conserva preparación documental.
'''
save(continuity,c)

header=f'''# ETAPA-14 · Integración por roles

<a id="vigente-14-i"></a>
## Estado vigente14-I · 14/11/2026, Lima

**Primera pasada. Etapa14 PARCIAL. Sublote14-I concluido para constancia nueva de merma y reintento secuencial entre sesiones.** Se corrigieron tres brechas reproducidas: ausencia de constancia dedicada, doble baja de la mismaUUID en otra sesión y pérdida del autor/lote originales en movimientos. No se declaran terminados identity, catalog, inventory, cash ni sales. Próximo cursor **14-J-AJUSTES-HISTORIA-01**.

### Versión, entorno y conservación

| Elemento | Corte14-I |
|---|---|
|08 inicial|`d2e03f10c190cf6a631152b35fa110d863d0fb3276723f6e7e95e8a0451ffa4a`; [copia](evidencias/14-I-20261114/08-antes.md)|
|08 ejecutadoChrome|`a7f22f243fef0087d5d5b3b807b9c53b9ee6b9a0a701eec953a4b3298c79c27d`; [copia](evidencias/14-I-20261114/08-ejecutado.md)|
|08 final|`{digest08}`;74HU,287criterios,113casos escritos. No se crean historias ni se cambia selección|
|HEAD|`7816d3328115cf5aa5bcdd0985fffd795b3ae084`; cambios locales previos conservados|
|Build de ejecuciones|195fuentes runtime/tests de módulos, SHA256 `cd148c66cc77dd2d1994e4d6048a2250f5c1a5bd75b939873c1effef35e1a1df`; [manifiesto](evidencias/14-I-20261114/navegador/final-2/build-final.json)|
|Build completo|[Manifiesto final](evidencias/14-I-20261114/build-final.json), conjunto canónico adicional con scripts/tests raíz. Las huellas de conjuntos diferentes no se igualan; comparación por archivo|
|Entorno|Python3.12.10/Django5.2.18/SQLite3.49.1; Chrome157.0.8103.78/Playwright1.65.1, WSGIloopback, cuentas ficticias y bases temporales separadas|
|Compatibilidad|Regresión final y ambos Chrome estables e idénticos por archivo. Inicial14-I coincide con todos los archivos comparables deH2. No base operativa ni despliegue|

[InformeH2 preservado](evidencias/14-I-20261114/antes-ETAPA-14.md) · [Estado anterior](evidencias/14-I-20261114/antes-ESTADO_GENERAL.md) · [Producto anterior](evidencias/14-I-20261114/producto-antes.zip) · [Planificación anterior](evidencias/14-I-20261114/planificacion-antes.zip) · [Inventario bidireccional](soporte/14-I-inventario.md) · [Disposiciones y recomendaciones](soporte/14-I-disposiciones.md).

### Hallazgos y correcciones

| Hallazgo | Antes / evidencia | Cambio y resultado |
|---|---|---|
| H14I-01 · P1, integridad |MismaUUID/actor/contenido en nueva sesión registra segunda baja: stock8→6. DiagnósticoI11|UUID y huella persistentes, actor vigente y transacción; misma operación devuelve misma constancia aun tras cambio de sesión/estado/fecha o agotamiento. NuevoI06..11b y tests. ConcurrenciaPG sigue pendiente|
| H14I-02 · P2, requisito omitido |POST vuelve al formulario, sin constancia. CA04/RN05C03 incumplidos|Vista dedicada y enlace desde Kardex con referencia/fecha/autor/producto/lote/cantidad/motivo/explicación/costo/origen. ADMIN/ALM consultan; VENDEDOR403; POSTconsulta405|
| H14I-03 · P2, historia |Renombrar autor/lote cambia texto de merma pasada. DiagnósticoI12|Fotografía al confirmar, conservada tras renombrado; legado muestra ausencia en vez de nombres actuales. Migración0010 nullable sin backfill; historia ante SQL privilegiado no verificada|
| H14I-04 · propuestaUX |Errores existentes no tienen resumen enfocable/anuncio integral|Recomendación R14I-01, costo bajo/medio y beneficio teclado/lector. No se acepta automáticamente ni se declara implementada|

Se reutilizó StockWriteOff para evitar duplicar documentos. Clave requeridaHTTP; llamadas internas sin clave son nueva operación explícita. Se mantiene correlativoB existente y no se presenta su mecanismo como prueba de concurrencia. La leyenda identifica constancia interna no fiscal. Tres fallos postwrite revierten baja/clave/stock/costo y dejan posible reintento. Sin cambios en precio o caja por registrar merma.

### Trazabilidad y cobertura nueva

Siete criterios principales inventariados antes de ejecutar: **6 CUMPLE en muestra,1 PARCIAL**. [Texto literal y matriz final](evidencias/14-I-20261114/criterios-final.json).22familias de superficie trazadas en el inventario final, con etiquetas y límites; la lista no equivale a toda la aplicación. No hay extras comerciales aceptados solo por existir en código.

| Criterio / actor | Esperado y observado | Estado / siguiente acción |
|---|---|---|
|INV02/CA01 · ALM/ADMIN|A10@3, daño2 deja8;11/0/fracción/cantidad fuera de rango rechazan; R2 identificado entre dosC|CUMPLE en muestra; máximo999999 no recorrido enChrome|
|INV02/CA02 · ALM/ADMIN|Daño de vencido y vencimiento prematuro rechazan; robo explicado y vencimiento admitidos|CUMPLE en muestra; fechaLima controlada|
|INV02/CA03 · ALM/ADMIN|Daño/robo exigen detalle; conserva responsable original tras renombrado|CUMPLE en muestra; lector de pantalla pendiente|
|INV02/CA04 · ALM/ADMIN|B correlativo, constancia recuperable por GET; datos originales persistidos|CUMPLE en muestra; no impresión física|
|RN05/C01 · ALM|Robo de vencido/inactivo válido, causa real; precio/ventas/caja intactos y costo de salida capturado|CUMPLE en muestra; no regularización de datos operativos|
|RN05/C03 · ADMIN/ALM, VEN denegado|Constancia original, legado explícito, impresiónCSS y despacho instrumentado; lectura sin mutación|CUMPLE en muestra de aplicación; SQL privilegiado/dispositivo físico pendientes|
|RN05/C04 · roles conectados|Clave igual recupera misma baja; diferente contenido/actor rechaza; no duplicación secuencial, rollback probado|PARCIAL; dosconexionesPG y carrera venta/baja/ajuste no ejecutadas|

Dependencias revalidadas: INV04 muestra−2/saldo8, autor y enlace histórico; DOC03AI distingue R1/R2 con mismo loteC; RN14 conserva promedio3 y costo salida3 hasta agotar, luego promedio0. Estas muestras no cierran esos contratos completos. INV03/RN05C02 de lote nuevo y costo documentado permanecen fuera de este sublote; INV05/06/REP08 globales siguen futuros.

### Cadena entre roles y pruebas

Chrome nuevo reejecutó ADMINcrea categoría/producto/proveedor→ALMcarga3+7@2→VENabre100 y cobra4×3.55=14.20, recibe20/vuelto5.80→ALMcontrasta6ymerma1→ADMINve5yventa→VENcierra114.20exacto. Incluye denegaciones, categoría desactivada/reactivada, fecha inválida y efectivo insuficiente sin mutación. Persistencia se contrasta tras respuesta/recarga.

La cadena enlaza los resultados detallados de [01](ETAPA-01.md), [02](ETAPA-02.md), [03](ETAPA-03.md), [04](ETAPA-04.md), [05](ETAPA-05.md), [06](ETAPA-06.md), [07](ETAPA-07.md), [08](ETAPA-08.md), [09](ETAPA-09.md), [10](ETAPA-10.md), [11](ETAPA-11.md) y [12](ETAPA-12.md) mediante inventario14-D y las dependencias14-F/G/H1/H2. Solo los pasos y pruebas identificados se revalidan aquí; sus restantes fronteras, dispositivos, políticas, migraciones operativas y carreras son heredadas o no ejecutadas. No se vuelven a anunciar como probadas por enlazarlas.

| Evidencia reproducible | Resultado y límites |
|---|---|
|[Servidor](evidencias/14-I-20261114/servidor/INFORME.md)|10tests nuevos; **614/614** final en79.261s, sin migración pendiente.21tablas de negocio, fallos postwrite/migración/roles/fecha/estado/UUID/historia. Las corridas fallidas se conservan|
|[Chrome](evidencias/14-I-20261114/navegador/RESUMEN.md)|**26checkpoints específicos+44 de cadena**,17+14capturas, bases independientes y cobertura solapada; no70criterios distintos|
|[Diagnóstico antes](evidencias/14-I-20261114/navegador/diagnostico-3/diagnostico.json)|12checkpoints; tres brechas reproducidas. Intentos anteriores fallaron por arnés y permanecen registrados|
|[Validación final](evidencias/14-I-20261114/validacion-final.json)|Coherencia08/vistas, build, criterios y archivos; no aprobación funcional universal|

### Decisiones, límites y cursor

08 se actualizó antes de regenerar07/09/03;02/14/16/21 y contexto00/01/control/continuidad se sincronizaron. Fundamento: requisitos seleccionados deINV02/RN05 y delegación técnica vigente registrada enD14I-01..06. No se añade HU comercial ni se acepta la propuestaUX por redactarla. Se registran alternativas, beneficio, riesgo, costo e impacto de diseño, arquitectura, NFR, pruebas y necesidades pendientes.

No ejecutado: concurrencia realPG; muerte de proceso; protección anteSQL privilegiado; volumen/SLA; migración o diagnóstico operativo; impresora física, móvil físico y accesibilidad integral; rama de nueva merma con origen legado/ambiguo enChrome. Datos faltantes no se reconstruyen. El sublote termina con evidencia acotada; **no hay coincidencia total de la etapa14**.

{cursor}

Después completar pendientes14 y primera15–17; preparar00ysegunda01–17. Se conserva a continuación el registroH2 y todos los anteriores con sus límites originales.

## Registro anterior14-H2, conservado

'''
old=read(RESULTS/'ETAPA-14.md').split('\n',1)[1]
save(RESULTS/'ETAPA-14.md',header+old)
state=read(RESULTS/'ESTADO_GENERAL.md')
state=re.sub(r'^# Estado general[^\n]*','# Estado general vigente de auditorías · 14/11/2026 (actualizado14-I)',state,count=1)
start=state.index('La etapa13 está finalizada');end=state.index('\n\n',start)
state=state[:start]+'''La etapa13 está finalizada para el panel mínimo. La etapa14 concluyó el sublote14-I de constancia histórica de merma y reintento entre sesiones. Sigue **PARCIAL** por historia de ajustes, lote nuevo/costo documentado y demás pendientes.614/614 de regresión;26observacionesChrome específicas y44 de cadena. **Cursor14-J-AJUSTES-HISTORIA-01.**15–17 y segunda pasada pendientes. [Informe vigente](ETAPA-14.md#vigente-14-i) · [Estado anterior](evidencias/14-I-20261114/antes-ESTADO_GENERAL.md).'''+state[end:]
state=re.sub(r'^\| \[14\][^\n]*','| [14](ETAPA-14.md#vigente-14-i) Integración por roles |14/11/2026|Primera14-I:7criterios principales,22familias;6CUMPLE en muestra,1PARCIAL.26+44observacionesChrome;10tests nuevos;614/614regresión.|**PARCIAL. Sublote14-I concluido**|Constancia y reintento secuencial verificados. Historia ajustes, lote nuevo/costo,PG,volumen y operación pendientes.|14-J-AJUSTES-HISTORIA-01: ADMIN+2/−3 sobreA10@3, fotografía, errores y efectos entre roles|',state,count=1,flags=re.M)
state=state.replace('| 14-I-MERMA-01, integración parcial |','| 14-J-AJUSTES-HISTORIA-01, integración parcial |',1)
save(RESULTS/'ESTADO_GENERAL.md',state)

inv=RESULTS/'soporte/14-I-inventario.md'
inventory=read(inv).replace('«Detalle / explicación»','«Detalle (obligatorio para Daño y Robo)»')
inventory+='''

## Resultado de superficie14-I

22familias trazadas:18iniciales y4concreciones siguientes. La familiaI-UI18 deja de estar ausente en este build; UUID deI-UI05 pasa a requeridaHTTP. Las clasificaciones iniciales se conservan como diagnóstico, no como estado final.

| Familia nueva | Ruta / rol / estado / literal | Respaldo y evidencia |
|---|---|---|
|I-UI19|GET /inventario/bajas/{UUID}/ ADMIN/ALM; «Baja confirmada», «Constancia de merma {B}», «Datos conservados de la baja de mercadería.»|INV02/CA04, RN05/C03; I05/I13/I14, tests snapshot/roles|
|I-UI20|Referencia; Fecha y hora de Lima; Responsable original; Producto original; Código original; Lote original; Vencimiento original; Origen registrado; Cantidad retirada; Motivo; Explicación; Costo unitario de salida|Datos persistidos al commit; formatosB,dd/mm/aaaa HH:mm:ss, fecha, texto escapado, cantidadentera+UND, costoS/4decimales. «Sin explicación registrada» si vacío; «No disponible» siNULL. I13/I22/I23/I24/I25 ytests|
|I-UI21|«Imprimir», «Registrar otra baja», «Ver movimientos», «Ver inventario»; «Ver constancia de merma» desdeKardex|RN05/C03,INV04/CA03; acciones GET/navegación y window.print. I12..18; impresiónfísicaNOEJECUTADA|
|I-UI22|«Registro anterior o incompleto: la fotografía original de producto, lote, origen o responsable no está disponible. No se reconstruye con los maestros actuales.»; «Fotografía histórica de merma no disponible. Consulte los datos conservados en su constancia.»; «Constancia interna de merma. No es un comprobante de pago.»|CT-COHERENCIA-UI,RN05/C03,DOC03AI; I25 y legacytest para constancia; avisoKardex inspeccionado, rama específica enChromeNOEJECUTADA|

La vista reutiliza clases existentes;12salidas y4acciones no son16HU nuevas. La clave/huella/modelo/migración se trazan aRN05/C04 y diseño02. No hay extra comercial sin requisito incorporado. Clasificación por criterio y evidencia exacta en criterios-final.json; errores de UUID requeridos se capturan en testsHTTP, no todos se forzaron porChrome. Estado vacío de selector, teclado y lector de pantalla conservan NOEJECUTADO en este sublote.
'''
save(inv,inventory)

sys.path.insert(0,str(RESULTS/'fuente_unica_20261112'))
import regenerar_vistas as views
print(json.dumps({'08_final':digest08,'regeneracion':views.generate()},ensure_ascii=False))
