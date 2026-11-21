"""Cierre verificable14, conserva antecedentes y deriva07/09/03 desde08."""
import hashlib, importlib.util, json, re, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];RESULTS=HERE.parents[1]
read=lambda p:p.read_text(encoding='utf-8')
write=lambda p,s:p.write_text(s.rstrip()+'\n',encoding='utf-8')
sha=lambda b:hashlib.sha256(b).hexdigest()
load=lambda p:json.loads(read(p))
LINK='auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114'
assert not (HERE/'08-final.md').exists(),'No sobrescribir cierre previo'
server=load(HERE/'servidor/regresion-final/manifiesto.json')
assert server['status']==0 and server['fuentes_estables']
runtime=server['despues'];assert runtime['sha256']=='ec783ac6febb289f70efbda37d7e742ad1305088982ad1e4e6f6694549cdd172'
runs=['navegador/cadena-final','navegador/ajustes-final','navegador/merma-final','navegador/kardex-final','navegador/dinero-final','navegador/precio-final-2','complementos-chrome-2']
for folder in runs:
    run=load(HERE/folder/'ejecucion.json')
    assert run['estado']=='recorrido_completo' and run['build_estable'] and run['build_final']==runtime['sha256'],folder
pg=load(HERE/'postgresql/final/compatibilidad-build.json');assert pg['pg_success'] and pg['runtime_matches_declared_frozen']
s=read(ROOT/'08_Historias_de_Usuario.md')
s=re.sub(r'\*\*Revisión:14/11/2026\.\*\*[^\n]+','**Revisión:14/11/2026.** Primera pasada:13 finalizada para panel mínimo;14 COMPLETADA para integración entre roles, navegador y persistencia delimitada.634/634 servidor,157 checkpointsChrome y19/19 PostgreSQL aislado. No cierra todos los módulos ni15–17. [Informe, versiones y cursor15-SEGURIDAD-BASELINE-01](auditoria_por_etapas/resultados/ETAPA-14.md#cierre-14). Después17, preparar00 y segunda pasada01–17.',s,count=1)
states={
'CP-HU-INV-03-001':'EJECUTADO en primera pasada14-CIERRE,14/11/2026: ajustes existentes/nuevos, costoQ0, historia, roles, reenvío y efectos entre módulos verificados en bases aisladas. No acredita datos operativos ni defensa anteSQL privilegiado.',
'CP-DEC-11-TOPE-EFECTIVO-FORM-001':'EJECUTADO en primera pasada14-CIERRE: límites por operación/acumulados, formatos, recuperación histórica y checks probados en SQLite/Chrome/PostgreSQL18.4. Migración operativa no ejecutada.',
'CP-INTEGRACION-ROLES-001':'EJECUTADO en primera pasada14-CIERRE. Cadena y variantes delimitadas comprobadas en Chrome/servidor/persistencia, con revalidación de ajustes, movimientos, merma, dinero y precio. Completa etapa14 para este alcance; los contratos transversales globales y etapas15–17 no se declaran completos.',
'CP-RN-05-001':'EJECUTADO en muestras14-CIERRE: C01..03 y reintentos secuenciales/concurrentes de merma/ajuste con19casosPG complementarios. El contrato transversal no acredita toda concurrencia posible, recuperación ante caída ni operación.',
'CP-HU-INV-02-001':'EJECUTADO en muestras14-I revalidadas en14-CIERRE: causas, constancia, fotografías, roles, costo y legado. Impresiónweb observada; dispositivo físico y escrituraSQL privilegiada no verificados.',
'CP-HU-INV-02-002':'EJECUTADO en muestras14-CIERRE: exceso y claves inválidas/divergentes rechazan; mismaUUID recupera un resultado entre sesiones y en PostgreSQL concurrente. Sin nueva baja ni descuento duplicado.',
}
for ident,status in states.items():
    start=s.index('<a id="'+ident+'"></a>');end=s.find('<a id="',start+1)
    if end<0:end=len(s)
    part=s[start:end];part=re.sub(r'\*\*Estado:\*\*[^\n]*','**Estado:** '+status,part,count=1)
    pos=part.index('\n',part.index('**Cubre:**'))
    part=part[:pos+1]+f'**Evidencia vigente14-CIERRE:** [Cobertura y límites](auditoria_por_etapas/resultados/soporte/14-CIERRE-cobertura.md), [regresión]({LINK}/servidor/regresion-final/resultado.txt), [PostgreSQL]({LINK}/postgresql/INFORME.md). Los resultados anteriores conservan su fecha y build.\n'+part[pos+1:]
    s=s[:start]+part+s[end:]
write(ROOT/'08_Historias_de_Usuario.md',s);(HERE/'08-final.md').write_bytes((ROOT/'08_Historias_de_Usuario.md').read_bytes())
hash08=sha((ROOT/'08_Historias_de_Usuario.md').read_bytes())
contexts={
'02_Diseno_Tecnico_R1_PMV.md':'PhysicalAdjustment guarda UUID/huella y fotografías; Lot.adjustment_origin identifica lote encontrado y Kardex suma el ajuste una sola vez. Mismo actor/clave/contenido recupera registro; legado nullable no se rellena. Actor→producto→lote se bloquean antes de efectos. Q0 exige costo/fuente y Q>0 conserva promedio. Detalle GET ADMIN/ALM; soloADMIN confirma. Dinero separa tope de operación9,999,999.99 y acumulado14,2; capacidad se valida bajo bloqueo del turno antes de venta. cash0004/sales0007 diagnostican datos antes de checks. No migración operativa. Véanse soporte de ajustes y dinero para campos, alternativas e impactos.',
'16_Task_Breakdown.md':'Cerradas en integración14 las tareas de historia/reenvío de ajuste, lote nuevo, costoQ0, límites monetarios y checks seleccionados; corregidos formatos de precio y recuperación histórica. Migración0011 y cash0004/sales0007 comprobadas en bases ficticias;634tests,157checkpointsChrome,19PG. Las tareas de seguridad global, recuperación ante muerte de proceso, despliegue/CI, datos operativos y dispositivos conservan etapa15. No se cierran historias futuras ni las auditorías individuales por extensión.',
'14_Sprint_Planning.md':'Etapa14 COMPLETADA para la cadena conectada y sus variantes delimitadas. El cierre usa el build congelado y evidencia reproducible, no solo el estado del sprint. Próximo15-SEGURIDAD-BASELINE-01: inventariar permisos/sesiones/entorno/respaldos y no atribuir como nuevos los19casosPG de14. No desplegar ni migrar datos operativos a partir de este informe.',
'21_Alcance_Actual_y_Diferencias.md':'Se resuelven los pendientes funcionales propios de14: ajustes con historia y reenvío persistente, lote nuevo de origenAJUSTE, costo documentado desde físico0 y cierre acumulado válido. Precio ambiguo y recuperación histórica corregidos. Los157checkpoints y634tests no equivalen a todos los80CA de módulos dependientes; estado por elemento en cobertura14-CIERRE.15–17 y segunda pasada siguen pendientes.',
'01_Proyecto_y_Releases.md':'Primera pasada14 completada para integración de los tres roles en datos ficticios; no aprobación global de release, piloto, despliegue ni todos los módulos. Se mantiene catálogo74HU,287criterios y113casos escritos. No nuevas HU comerciales ni cambio de selección, MoSCoW o estimaciones. Próximo15, luego16/17 y segunda pasada00→01–17.',
'00_LEEME_PLANIFICACION.md':'Estado vigente:14 COMPLETADA en primera pasada para integración por roles;15–17 pendientes. Cursor15-SEGURIDAD-BASELINE-01. Conservar evidencias y límites históricos; al concluir17 preparar00 y ejecutar segunda pasada01–17.08 actualizado y07/09/03 reproducidos; no se declara100%delproducto.',
'r1-pmv/CONTROL_SPRINTS.md':'Cierre local14:634/634pruebas en132.064s,157checkpointsChrome en siete recorridos,19/19PostgreSQL18.4 aislado; fuentes estables. Ajustes, dinero y cadena revalidados. No apruebaCI/despliegue/operación; cursor15-SEGURIDAD-BASELINE-01.',
}
for name,body in contexts.items():
    p=ROOT/name;old=read(p);first,rest=old.split('\n',1);prefix='../' if name.startswith('r1-pmv/') else ''
    current=f'\n\n## Corte vigente14-CIERRE · 14/11/2026 Lima\n\n{body}\n\n[Informe y evidencia]({prefix}auditoria_por_etapas/resultados/ETAPA-14.md#cierre-14) · [Ajustes]({prefix}auditoria_por_etapas/resultados/soporte/14-CIERRE-ajustes.md) · [Dinero]({prefix}auditoria_por_etapas/resultados/soporte/14-CIERRE-dinero.md). Las secciones fechadas anteriores se conservan como antecedentes.\n\n'
    write(p,first+current+rest)
header=f'''# ETAPA-14 · Integración por roles

<a id="cierre-14"></a>
## Cierre vigente · 14/11/2026 Lima

**COMPLETADA en primera pasada para las conexiones identity, catalog, inventory, cash y sales, navegador y persistencia del recorrido delimitado.** Se resolvieron los pendientes propios de14, se comprobó la cadena ADMIN→ALMACENERO→VENDEDOR→ALM/ADMIN→VENDEDOR y se revalidaron sus variantes. No se declaran terminados los módulos individuales ni15–17. Próximo cursor **15-SEGURIDAD-BASELINE-01**.

### Versión y conservación de evidencia

| Elemento | Corte final |
|---|---|
|Pasada/alcance|Primera, continuación14-I; ajustes/historia/Q0 y cierre monetario, más regresión de la cadena y dependencias afectadas|
|08 anterior|`9b291fc4bd4f15cd00042e36836e8425305b09572cd969a124aebc1700909ab2`; [copia](evidencias/14-CIERRE-20261114/08-antes.md)|
|08 ejecutado|`32270f6b6f32d8aec7c3f4883f20eef2229e3bb26da8f0c0369fd047e3f8e700`; [copia](evidencias/14-CIERRE-20261114/08-ejecutado.md), concreción técnica antes de las corridas finales|
|08 final|`{hash08}`; [copia](evidencias/14-CIERRE-20261114/08-final.md).74HU/287criterios/113casos escritos; solo estados/evidencia final después de pruebas|
|HEAD|`7816d3328115cf5aa5bcdd0985fffd795b3ae084`, cambios locales anteriores conservados; no commit/despliegue|
|Build de ejecución|203fuentes de módulos, SHA256 `{runtime['sha256']}`. [Regresión/manifiesto](evidencias/14-CIERRE-20261114/servidor/regresion-final/manifiesto.json)|
|Build canónico|209fuentes, SHA256 `ef8bc3fa42ebf84377ec8b910f38acee1ecc7e12f0c252a59ab72adbcbccdd65`; [manifiesto final](evidencias/14-CIERRE-20261114/build-final.json). Conjuntos distintos comparados por archivo|
|Entorno|Python3.12.10/Django5.2.18/SQLite3.49.1; Chrome157.0.8103.78/Playwright1.65.1 real headless; PostgreSQL18.4 aislado con barreras/PID. Bases temporales, loopback, datos ficticios; clúster detenido|

[Informe anterior íntegro](evidencias/14-CIERRE-20261114/antes-ETAPA-14.md) · [Estado anterior](evidencias/14-CIERRE-20261114/antes-ESTADO_GENERAL.md) · [Producto anterior](evidencias/14-CIERRE-20261114/producto-antes.zip) · [Documentación anterior](evidencias/14-CIERRE-20261114/documentacion-antes.zip).

### Inventario, aceptación y correcciones

Se aplicaron completos protocolo/continuidad. El inventario previo independiente identificó13necesidades de cierre CI14-01..13, y el mapa previo de23HU/80CA conserva su papel de dependencias, no de80aprobaciones globales. [Matriz final y clasificación](soporte/14-CIERRE-cobertura.md) · [Diagnóstico independiente preservado](soporte/14-CIERRE-revision-independiente.md). Se enlazan las etapas01–12 por criterio, se distingue lo revalidado de lo heredado y no se seleccionan INV05/06, REP08 ni SOL futuros.

La orden del usuario «corrige todo los pendientes … hasta … completada» autoriza resolver defectos técnicos de14; ningún informe se usa como permiso autónomo. Las concreciones se integraron en08 antes de repetir pruebas. Las alternativas, beneficio, riesgo, costo e impacto están en [ajustes](soporte/14-CIERRE-ajustes.md) y [dinero](soporte/14-CIERRE-dinero.md). Se completan HU/RN/tareas existentes; no hace falta inventar HU para una clave interna o cada mensaje.02/14/16/21 y vistas07/09/03 quedan coherentes.

| Pendiente | Resultado y vínculo requisito→producto→prueba |
|---|---|
|Ajuste existente y lote nuevo|HU-INV-03/CA01..03, RN05C02: ADMIN+2/−3 sobreA10@3 deja9; nuevo origenAJUSTE no duplica entradaKardex. INV03 tests, J01..16/J19..27|
|Costo desde físico0|RN14/DOC03AHC03: Q0sin costo/fuente rechaza;4@2.5 documentadas→venta2→merma1 deja1 y costos históricos2.5. J17..24, tests,PG|
|Historia y recuperación|INV03CA03/INV04CA03/RN05C04: UUID/huella/snapshots, detalleADMIN/ALM,VEN403; nombres antiguos conservados, legado explícito. J05..16/J28..30, merma26, PG dobleUUID|
|Dinero y capacidad|DEC11C01..03: venta/apertura9,999,999.99; cierre14,2, diferencia permitida negativa y coherente. Dos ventas5m cierran10m; overflow antes de venta sin mutación. M01..13, cash tests,PG|
|Precio y reintento histórico|Revisión independienteCI12/13: formas ambiguas rechazadas, servicioDecimal; recuperar descuento/efectivo históricos no crea venta nueva.142tests focales integrados en634|
|Cambio de precio entre roles|DEC12C04: GET conserva borrador10; POST de revisión actualiza solo línea a12 y pide confirmar; segundoPOST cobra12/cierre112. P01..08. Esta revisión permitida no se confunde con rechazo atómico|
|Legado y mensajes|Selector vacío, claves malformadas, merma de origen desconocido, cabecera incompleta y doble origen:15observaciones complementarias; saldo«No disponible», sin historia inventada ni mutación. Resumen enfocaba error y móvil390 sin desbordamiento de detalle|
|Cadena/efectos y servidor|AltasUI→carga10→apertura100→cobro14.20→merma1→stock5→cierre114.20; roles/estado/vencimiento/errores con testigos.44checkpoints y regresión;19PG complementarios|

### Pruebas y resultados

| Ejecución final | Resultado, evidencia y significado |
|---|---|
|Servidor aislado|[634/634](evidencias/14-CIERRE-20261114/servidor/regresion-final/resultado.txt),132.064s; check sin incidencias y makemigrations sin cambios. Incluye pruebas anteriores y nuevas; no634criterios distintos|
|Cadena principal Chrome|[44 checkpoints](evidencias/14-CIERRE-20261114/navegador/cadena-final/ejecucion.json), creación de categoría/producto/proveedor porUI, carga/cobro/baja/consulta/cierre y rechazos|
|Ajustes Chrome|[31 checkpoints](evidencias/14-CIERRE-20261114/navegador/ajustes-final/ejecucion.json), historia, Q0/lote nuevo/venta/merma/cierre, roles, error/foco/recarga/móvil|
|Merma Chrome revalidada|[26 checkpoints](evidencias/14-CIERRE-20261114/navegador/merma-final/ejecucion.json), mismas condicionesI sobre buildfinal|
|Kardex Chrome revalidado|[20 checkpoints](evidencias/14-CIERRE-20261114/navegador/kardex-final/ejecucion.json), origen, saldos/filtros/paginación/legado y permisos|
|Dinero y precio Chrome|[13 monetarios](evidencias/14-CIERRE-20261114/navegador/dinero-final/ejecucion.json) y [8 de precio](evidencias/14-CIERRE-20261114/navegador/precio-final-2/ejecucion.json)|
|Estados complementarios Chrome|[15 checkpoints](evidencias/14-CIERRE-20261114/complementos-chrome-2/ejecucion.json), fixture costo3 explícito; corte1 preservado y no usado para afirmar valoraciónlegacy|
|PostgreSQL real|[19/19](evidencias/14-CIERRE-20261114/postgresql/INFORME.md), conexiones y esperas verificadas, UUID/correlativos/orígenes, venta vs salidas, rollback por excepción y checks. DjangoClient concurrente no se atribuye aChrome|
|Coherencia documental/build|[Validación reproducible](evidencias/14-CIERRE-20261114/validacion-final.json):07/09/03+índice idénticos a generación08, criterios compatibles, archivos finales iguales, enlaces vigentes comprobados|

**157 checkpointsChrome en siete recorridos**, con solapamiento entre suites. Los errores comparan21tablas de negocio y rol/activo; hashes de sesión/último acceso no se interpretan como venta. Fixturesseparadas permiten reproducir estados; SQL de renombrado/legado se rotula como control aislado, no acciónUI.

Se conservan intentos diagnósticos fallidos: dinero anterior revela el defecto; focales intermedios encontraron desfase temporal de migración/fixture;629/630 requirió actualizar un test heredado para enviarUUID ahora obligatoria. Ajustes1/2 fallaron por comparar URL con fragmento#id_delta; los datos eran iguales. Precio1 esperaba quePOSTnoactualizara el borrador, pero DEC12C04 exige revisión explícita; se corrigió el runner y se verificó que únicamente cambia esa línea, sin cambiar producto. Estas corridas no se cuentan como aprobadas.

### Límites y cursor

No quedan pendientes funcionales propios del alcance14delimitado. Permanecen **NO EJECUTADOS como etapas completas**15(seguridad/operación),16(normativa/viabilidad) y17(conciliación). Los19PG son evidencia acotada nueva, no cierre15. PG17, muerte real de proceso/reinicio, respaldo/restauración,CI/despliegue,privilegiosSQL,volumen/SLA y diagnóstico/migración de datos operativos requieren pruebas propias. Impresora, lector/pantalla y móvil físicos no se acreditan porChrome. Apertura con solo mercadería vencida sin carga inicial sigue investigación de negocio; no se inventa política. El desempate de historial de turnos conserva deuda adyacente12 y no aprueba su criterio global.

**Cursor exacto15-SEGURIDAD-BASELINE-01:** primera pasada, leer protocolo y prompt15; registrar08/buildfinal14y cambios posteriores; inventariar permisos/sesiones/configuración/entorno, copiar mapa de pruebasPG como heredado compatible, seleccionar primer sublote de seguridad y recuperación aislada. No migrar/desplegar datos reales sin autorización propia. Después15→16→17; actualizar00y ejecutar segunda pasada01–17. No se declara coincidencia total de todos los módulos ni aptitud de operación real.

## Antecedentes preservados · informe14-I y sublotes previos

'''
old=read(RESULTS/'ETAPA-14.md');write(RESULTS/'ETAPA-14.md',header+old.split('\n',1)[1])
p=RESULTS/'ESTADO_GENERAL.md';s=read(p)
s=s.replace('(actualizado14-I)','(cierre14-CIERRE)',1)
start=s.index('La etapa13 está finalizada');end=s.index('\n\n| Etapa',start)
s=s[:start]+'La etapa13 está finalizada para el panel mínimo. **Etapa14 COMPLETADA en primera pasada para integración por roles y persistencia delimitada.**634/634servidor,157checkpointsChrome y19/19PG sobre buildfinal estable. No cierra módulos individuales ni15–17. **Cursor15-SEGURIDAD-BASELINE-01.** [Informe final](ETAPA-14.md#cierre-14) · [Cobertura](soporte/14-CIERRE-cobertura.md) · [Estado anterior íntegro](evidencias/14-CIERRE-20261114/antes-ESTADO_GENERAL.md).'+s[end:]
s=re.sub(r'^\| \[14\].*$', '| [14](ETAPA-14.md#cierre-14) Integración por roles |14/11/2026|Primera pasada: cadena3roles, ajustes/historia/Q0, merma,Kardex,dinero,precio.634/634servidor,157Chrome,19/19PG;23HU80CA como mapa de dependencias, sin cierre global.|**COMPLETADA para alcance14 delimitado**|Pendientes funcionales propios resueltos; operación/seguridad global15,negocio16,conciliación17 conservan límites.|15-SEGURIDAD-BASELINE-01|',s,count=1,flags=re.M)
s=s.replace('| 14-J-AJUSTES-HISTORIA-01, integración parcial |','| 15-SEGURIDAD-BASELINE-01,14completada |',1)
s=s.replace('| Pruebas aisladas; CT-ROLLBACK, SEC15 y S1-OPS/CI con evidencia propia |','| 15-SEGURIDAD-BASELINE-01: inventario actual y primer sublote aislado;19PG14 heredados con compatibilidad |',1)
write(p,s)
p=ROOT/'auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md';s=read(p);s=s[:s.index('## Punto de entrada')]+'''## Punto de entrada

Primera pasada14 **COMPLETADA para integración por roles y persistencia delimitada**,14/11/2026;634/634servidor,157checkpointsChrome y19/19PostgreSQL aislado. Los resultados anteriores permanecen en [ETAPA14](resultados/ETAPA-14.md#cierre-14) y [ESTADO_GENERAL](resultados/ESTADO_GENERAL.md). No se declara cierre de otros módulos ni segunda pasada.

**Cursor15-SEGURIDAD-BASELINE-01.** Leer protocolo/prompt15; inventariar permisos, sesiones, configuración, entorno, transacciones y recuperación contra08final/build14identificados. Clasificar como heredados los19casosPG de14, comparando archivos antes de reutilizarlos; seleccionar un sublote aislado de seguridad/recuperación. No atribuirle una corrida nueva ni aprobaciónPG17, muerte de proceso, respaldos,CI/despliegue,volumen o base operativa. Esas verificaciones siguen pendientes.

Secuencia15→16→17; después actualizar00 y segunda pasada01–17. Conservar hechos de negocio desconocidos, límites de dispositivos y normativa; no inventar una política de apertura con solo vencidos. [Protocolo](PROTOCOLO_COMUN.md) y [matriz de cobertura](resultados/soporte/14-CIERRE-cobertura.md).
''';write(p,s)
sys.path.insert(0,str(RESULTS/'fuente_unica_20261112'));import regenerar_vistas as views
print(json.dumps(dict(plan08_final=hash08,conteos=views.generate()),ensure_ascii=False))
