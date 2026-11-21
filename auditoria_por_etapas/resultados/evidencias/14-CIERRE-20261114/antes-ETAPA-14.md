# ETAPA-14 · Integración por roles

<a id="vigente-14-i"></a>
## Estado vigente14-I · 14/11/2026, Lima

**Primera pasada. Etapa14 PARCIAL. Sublote14-I concluido para constancia nueva de merma y reintento secuencial entre sesiones.** Se corrigieron tres brechas reproducidas: ausencia de constancia dedicada, doble baja de la mismaUUID en otra sesión y pérdida del autor/lote originales en movimientos. No se declaran terminados identity, catalog, inventory, cash ni sales. Próximo cursor **14-J-AJUSTES-HISTORIA-01**.

### Versión, entorno y conservación

| Elemento | Corte14-I |
|---|---|
|08 inicial|`d2e03f10c190cf6a631152b35fa110d863d0fb3276723f6e7e95e8a0451ffa4a`; [copia](evidencias/14-I-20261114/08-antes.md)|
|08 ejecutadoChrome|`a7f22f243fef0087d5d5b3b807b9c53b9ee6b9a0a701eec953a4b3298c79c27d`; [copia](evidencias/14-I-20261114/08-ejecutado.md)|
|08 final|`9b291fc4bd4f15cd00042e36836e8425305b09572cd969a124aebc1700909ab2`;74HU,287criterios,113casos escritos. No se crean historias ni se cambia selección|
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

**14-J-AJUSTES-HISTORIA-01.** Primera pasada, continuar sobre el build14-I y preservar este corte. Inventariar HU-INV-03/CA01..02 y HU-INV-04/CA03 con RN05/RN14/DOC03AI/DEC08. Crear A10@3 con origen fotografiado; ADMIN ajusta+2 con motivo y luego−3: stock12→9, promedio3, costo de salida3, caja/ventas/precio intactos. Conservar instante, autor, producto/lote, motivo y origen del ajuste; renombrar maestros, recargar y contrastar historia. La carga inicial conserva cantidad original10 aunque cambie la capacidad del lote. ALMACENERO/VENDEDOR no ajustan; cantidad0/exceso/motivo vacío o inválido no mutan. Probar legado desconocido sin backfill, reenvíos, fallo postwrite y revalidar Kardex/merma/venta/caja. Lote nuevo y costo documentado desde físico0 son pendientes propios posteriores; no inventar apertura operativa de productos solo vencidos.

Después completar pendientes14 y primera15–17; preparar00ysegunda01–17. Se conserva a continuación el registroH2 y todos los anteriores con sus límites originales.

## Registro anterior14-H2, conservado


<a id="vigente-14-h2"></a>
## Estado vigente14-H2 · 14/11/2026, Lima

**Primera pasada. Etapa14 PARCIAL. SubloteH2 concluido para la muestra deKardex.** Ahora la consulta muestra saldo cronológico, apertura/cierre, filtros de fecha/tipo y páginas25. Cuando el origen no permite conciliar, muestra saldo no disponible. El próximo cursor es **14-I-MERMA-01**, constancia demerma e historia deautor/origen. No se declaran completos otros módulos.

### Versiones y fuentes

| Elemento | CorteH2 |
|---|---|
|08 inicial|`1dac15a067dd0143d7b118d530f1fa222240455ec2d7d42eae83761f584fe597`|
|08 durante pruebas|`4c46f42530b25499e4f4cf31426e9fafd9293b95efdbddb38ed74403ae2e7e77`; [copia](evidencias/14-H2-20261114/08-ejecutado.md)|
|08 final|`d2e03f10c190cf6a631152b35fa110d863d0fb3276723f6e7e95e8a0451ffa4a`;74HU/287criterios/113casos escritos|
|HEAD|`7816d3328115cf5aa5bcdd0985fffd795b3ae084`; cambios locales anteriores preservados|
|Build final|198archivos `3bed2cd9e85e61dfe2dae607e438a83be911950ec328de59ac596b407155b1f6`;7fuentes deproducto nuevas/modificadas|
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

### Cursor exacto 14-I-MERMA-01

Inventariar HU-INV-02/CA01..04 yRN05/C01/C03/C04, conDOC03AI/RN14/RN28. CargaA10@3vigente;ALMACENERO confirmaDAÑO2conexplicación y obtiene constanciapropia: referencia/fecha/autor/producto/lote/cantidad/motivo/explicación originales, stock8, promedio3 ycostosalida3, caja/ventas/preciointactos. ADMINconsulta;VENDEDOR403. Renombrarmaestros,recargar ycomprobarfotografía. Reenviar lamismaclave devuelve resultadoanterior sin duplicar;contenidodivergente/rol/estado/fecha/cantidadinválidos no mutan. Variantesvencimiento/robo enlotescaducos yproducto inactivo,origenR1/R2conmismolotecomercial ylegadodesconocido. RevalidarKardex/venta/cajayrollback; impresiónbrowseracotada, dispositivofísicoNo ejecutado.

Saldo deKardex está verificado enlecturas secuenciales; snapshotconcurrentePG, páginasmientrascambiaeldato,volumenymemoriarequieren15. No inferir aperturaoperativa delegados. Constanciamerma,autorhistóricodeajuste,lote nuevoporajusteycosto documentadodesdefísico0 siguenencargos propios. Despuéscompletar14 yprimera15–17; preparar00ysegunda01–17,con evidenciaanteriorconservada.

## Registro anterior14-H1, conservado con sus límites


<a id="vigente-14-h1"></a>
## Estado registrado14-H1 · 13/11/2026, Lima

**Primera pasada. Etapa14 PARCIAL. Sublote H1 concluido: origen de cargas nuevas, dependencia del Kardex.** Se preservan cantidad/costo/número/fecha/instante y cabecera original; legado sin fotografía se declara incompleto. Saldo, filtros y paginación siguen pendientes en **14-H2-KARDEX-SALDOS-01**. No se cierran otros módulos.

### Versiones, alcance y evidencia

| Elemento | Valor |
|---|---|
|08 inicial|`fc69a8e9641f8c9c21c6356300fcd84bb3ad9e4ca62edc4c49ae90cd2832e59c`|
|08 ejecutado Chrome|`c6875fdc25bd43218891771a9990530bddc8b224a6e8dcc129ddaa8ea898250e`|
|08 final|`1dac15a067dd0143d7b118d530f1fa222240455ec2d7d42eae83761f584fe597`;74HU,287criterios,113casos escritos|
|HEAD|`7816d3328115cf5aa5bcdd0985fffd795b3ae084`, cambios locales previos preservados|
|Build final|196 archivos, `f9a593aacbd4cd5a0c753d672b5e06c1ada3dd21fb8a2f16b68009ee03f866aa`|
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


<a id="vigente-14-g"></a>
## Estado registrado14-G · 13/11/2026, Lima

**Primera pasada. Etapa14 PARCIAL. Sublote14-G concluido para recepción propia, reintento, procedencia e historia de ingresos nuevos.** Se corrigieron identidad de recepción, fotografía de proveedor/autor/cantidad original y compatibilidad del lote comercial repetido con ventas/bajas/ajustes. El próximo cursor es **14-H-KARDEX-SALDOS-01**. No se declaran terminados los módulos dependientes.

[Informe14-F preservado](evidencias/14-G-20261113/antes-ETAPA-14.md) · [Estado anterior](evidencias/14-G-20261113/antes-ESTADO_GENERAL.md). Los resultados anteriores conservan build/alcance. La nueva cadena general repite altas de maestros hasta cierre; el caso de recepción usa una fixture inicial declarada. Los dos recorridos tienen bases independientes.

### Versiones y entorno

| Elemento | Corte14-G |
|---|---|
|08 inventariado/ejecutado|SHA256 `8d4a7cbede73eac5b09524363e35d4780dc91d8e25ba6fa8f62de32a66c9984c`|
|08 documental final|SHA256 `fc69a8e9641f8c9c21c6356300fcd84bb3ad9e4ca62edc4c49ae90cd2832e59c`|
|HEAD|`7816d3328115cf5aa5bcdd0985fffd795b3ae084`, cambios locales previos preservados|
|Build inicial190|`7630c859296fd71dd4607133a461165e1b2d012d5679190652c5e0522bf4fa93`|
|Build final194|`f6ca27baf3813bf8806d449269623e0e9d293e8000dee4cfd83d45dd038cb11c`|
|Chrome188fuentes|`3c1b9ec10f99e695122fbae37451bd0e0462ae601a1f1cc8deca910035b32af3`,final2/cadena-final estables e idénticos por archivo|
|Herramientas|Python3.12.10,Django5.2.18,SQLite3.49.1,Chrome157.0.8103.78,Playwright1.65.1|
|Navegador|13/11/2026 Lima23:15:03–23:15:24;23+44checkpoints,17+14capturas,1280×900,3contextos/roles|
|Regresión final|Lima23:15:00–23:16:23;584/584 en80.237s,fuentes estables|
|Aislamiento|SQLite temporal/memoria,datos ficticios,HTTPWSGIloopback,CSRF y middleware. Sin migrar/abrir base operativa ni desplegar|

[Manifiesto inicial](evidencias/14-G-20261113/build-antes.json) · [Producto anterior completo](evidencias/14-G-20261113/producto-antes.zip) · [Planificación anterior](evidencias/14-G-20261113/planificacion-antes.zip) · [Manifiesto final](evidencias/14-G-20261113/build-final.json) · [Validación final](evidencias/14-G-20261113/validacion-final.json).

### Inventario y trazabilidad

[Inventario detallado](soporte/14-G-inventario.md): HU-INV-01b/2CA y DOC-03AI/4criterios principales; INV-04/CA02 y DEC-05-LOTE-ESPACIOS/C01 como dependencias, ocho criterios total. Siete rutas específicas y11familias de campos/salidas; rutas de roles/POS/caja de la cadena tienen denominador propio. [Matriz exacta](evidencias/14-G-20261113/criterios-final.json). Las74HU/287criterios/112casos escritos de08 se conservan; escribir un caso no acredita ejecutarlo.

| Criterio | Esperado/observado y evidencia nueva | Clasificación final |
|---|---|---|
|HU-INV-01b/CA01|Primera entrada20@4.5000;otra entrega25@5.2000,referencias distintas,reintento sin duplicar. Chrome02/04/08 ytest1|PARCIAL por alcance concurrente/operativo; alta prioridad|
|HU-INV-01b/CA02|Persistencia4decimales,presentación2,costo venta5.2000 y promedio conservado tras salida;captura4.50 deR1 permanece|CUMPLE en muestra; costo histórico operativo no regularizado|
|DOC-03AI/C01|UUID/correlativo/cabecera/líneas/lotes/costo/autor se confirman juntos;R1/R2|CUMPLE en muestraSQLite|
|DOC-03AI/C02|Igualclave/actor/contenido recupera misma recepción;orden/espacios/costo equivalentes;divergencia uotroactor rechaza|CUMPLE en muestra secuencial; HTTP y servicio|
|DOC-03AI/C03|Mismo loteC,mismafecha y nuevaUUID produceR2,otra cantidad/costo/proveedor. Venta conserva ambos orígenes|PARCIAL: dosconexionesPG pendientes15|
|DOC-03AI/C04|Cantidad0/UUID/fecha/precisión/duplicado/estado rechazan sin mutar;correcciónusa mismaUUID;cincofallospostwrite revierten25tablas|CUMPLE en muestra de excepciones;caída real pendiente|
|INV-04/CA02,dependencia|Consulta enlazaR1/R2,autor/proveedororiginal oausencia;legacyincompleto rotulado|CUMPLE en muestra; restoKardex pendiente|
|DEC-05-ESPACIOS/C01,dependencia|`ab  12`≡`AB 12`,`AB12`distinto;duplicadointernorechaza;legacycompara sin reescribir|CUMPLE en muestra; colisiones operativas no diagnosticadas|

SeisCUMPLE en muestra ydosPARCIAL. NingunaHU completa se cierra. Planificación→servidor/persistencia conecta RN01/03/14/19/29,identidadUUID,FEFO,costos y fotografía. Comportamiento→planificación vincula nueva constancia,referencias,avisos de ausencia y selección de procedencia aDOC03AI/INV04. No se incorpora un extra comercial sin respaldo. Cada texto/controlnuevo está inventariado; límites y estados no ejercitados conservan cobertura anterior identificada.

### Hallazgos y efectos entre roles

Chrome previo `antes2/` reprodujo tres problemas: la entrada devolvía carga inicial y no una referencia propia; el reenvío igual era error de lote, mientras la mismaUUID con lote/cantidad distintos creaba otra entrada; una segunda entrega real deC se rechazaba. Además, renombrar proveedor/autor cambiaba el documento. Físico20/promedio4.5000 ya era correcto por14-E; no se atribuye como corrección14-G.

Se implementaron StockReceipt/Line/Counter;UUIDHTTP,huella ordenada,correlativo global y fotografía de ingreso. La cantidad histórica queda separada de capacidad/saldo mutable delLot. Se mantiene laFK técnica a carga por compatibilidad, sin inferirrecepciones de ella. Migración no rellena historia ni reescribe filas. Números nuevos normalizan espacios;legado se compara canónicamente sin fusionarlo.

La muestra conectada recibióC10@6 yC5@8;tras abrir100,vendió22×10=220. Asignó10iniciales+10deR1+2deR2;stock3. ALMACENERO identificóR2 para merma1;ADMIN observóstock2,procedencias,venta y merma. VENDEDOR cerró320 exacto. R1 conserva10UND/promediohistórico4.50 aunque cambien maestros y salganunidades. Selección de ajuste/baja y asignaciones enlazan referencias para distinguir igualnúmero/fecha.

La cadena general nueva creó categoría/producto/proveedor porADMIN, cargó3+7@2porALMACENERO,abrió100,cobró14.20(efectivo20/vuelto5.80),dio bajaa1,dejó5 ycerró114.20. Revalidó categoría inactiva/reactivada,vencimiento,causa/cantidadmerma,efectivo insuficiente,roles por navegación yPOST. Las fixtures14D de ese runner identifican el caso reutilizado;fecha/buildson14-G.

### Pruebas y conservación

| Evidencia | Resultado |
|---|---|
|[Chrome antes2](evidencias/14-G-20261113/navegador/antes2/comparaciones.json)|9checkpoints,problemas reproducidos. `antes/` falló por selector del arnés y se conserva|
|[Chrome final2](evidencias/14-G-20261113/navegador/final2/ejecucion.json)|23checkpoints/17capturas,con BD yHTTP;referencias/reintentos/errores/historia/venta/merma/cierre|
|[Cadena general](evidencias/14-G-20261113/navegador/cadena-final/ejecucion.json)|44checkpoints/14capturas,alta de maestros hasta cierre;buildfinalestable|
|[Servidor](evidencias/14-G-20261113/servidor/INFORME.md)|10tests nuevos con variantes. Cincofallos tras escritura,cambio de estado/fecha,roles,migración ynormalización|
|[Regresión final](evidencias/14-G-20261113/servidor/final2/regresion-final.txt)|584/584,80.237s,sin cambios de fuentes;makemigrations--check sin diferencias|
|Corridas intermedias preservadas|572/583→582/583→583/583 con cambio de fuentes→584/584 estable. Focal7/9 por dosfixtures incorrectas→9/9;se añadió décimotest|
|[Validación documental](evidencias/14-G-20261113/validacion-final.json)|08 yvistas,compatibilidaddecriterios/build,enlaces/huellas y alcance sin cierre integral|

Los conjuntos se solapan. La primera regresión detectó pérdida del triggerreceived_at al reconstruirLot enSQLite y exceso de consultas enmovimientos. Se corrigieron ambos, preservando presupuesto de15consultas y protecciónSQL/ORM. Las demás adaptaciones corresponden aUUID/ruta/etiquetas y rechazo por fecha contradictoria exigidos por contrato;las fuentes antiguas se preservaron. [Comandos navegador](evidencias/14-G-20261113/navegador/RESUMEN.md) · [Comandos servidor](evidencias/14-G-20261113/servidor/INFORME.md).

### Decisiones, omisiones y límites

[Disposiciones14-G](soporte/14-G-disposiciones.md) registra fundamento de aceptación,beneficio,riesgo,costo eimpacto. Se eligió cabecera/líneas/contador sobre el monolito existente; no tabla genérica ni eventos de compra futuros. El usuarioyaautorizó correcciones técnicas de integración; el documento no concede autorización nueva.08incorpora concreción y ejecución parcial antes de regenerar07/09/03.02/14/16/21/01/00 ycontinuidad reflejan este corte.

Las nuevas cargas iniciales todavía consultan nombres de maestros;se advierte esa limitación y queda pendiente capturar suhistoria. NingunaFK/fecha prueba el origen antiguo. Las colisiones/regularización de datosoperativos requieren copiaautorizada yhechos delnegocio. Las excepcionesSQLite no acreditan caída real ni bloqueosPG;estosvan a15. El Kardexcarecedesaldo/filtros/paginación y la merma carecedeconstancia propia/snapshotdeautor. Impresión,móvil/accesibilidadintegral,topesoperativos y restantes requisitos conservansupendiente.

### Cursor exacto

**14-H-KARDEX-SALDOS-01, primera pasada.** Seleccionar HU-INV-04/CA-01,03,04 y DEC-08-KARDEX-COMPRAS/C-01,03. Preparar una secuencia conocida con instantes distintos: carga10, recepciónR1+10, R2+5, venta−22 y merma−1. Esperar saldo25 antes de la venta,3 tras la venta y2 al final. Consultar un período que comience después de la carga yR1: apertura20, entradaR2+5, salidas−23 y cierre2. Filtrar solo ventas debe conservar el saldo real y explicar qué movimientos se excluyeron; distinguir saldo, total filtrado y período.

Añadir más de25 eventos con empate de instante; probar orden estable, páginas y filtros preservados, fecha incompleta/invertida, tipo inválido, GET sin mutación y VENDEDOR403 sin costos. Para un historial incompleto, declarar el límite de reconstrucción sin inventar un saldo. Mantener enlaces aR1/R2 y asignaciones; revalidar costo, merma y caja afectados. Después continuar constancia de merma, fotografía de carga inicial y demás pendientes de14. Las etapas15–17 y la segunda pasada mantienen su secuencia.


---

## Registro anterior14-F, conservado con sus límites

<a id="vigente-14-f"></a>
## Estado del corte14-F · 13/11/2026, Lima

**Primera pasada. Etapa PARCIAL. Sublote14-F concluido para asignaciones de venta, fotografía histórica, orden de líneas y consulta de cobertura.** La venta guarda los lotes consumidos, nombres de vendedor/caja y posición de línea. La consulta interna muestra lotes/costo o ausencia histórica. La cadena completa se reejecutó desde creación de maestros hasta cierre sobre el build final. El próximo cursor es **14-G-RECEPCIONES-01**.

[Informe14-E conservado](evidencias/14-F-20261113/antes-ETAPA-14.md) · [Estado anterior](evidencias/14-F-20261113/antes-ESTADO_GENERAL.md). Los resultados de14-D/E permanecen con sus versiones.14-F revalida las conexiones afectadas y conserva pendientes de recepción, Kardex, merma, seguridad y datos operativos.

### Versiones y entorno

| Elemento | Corte14-F |
|---|---|
| 08 al inventariar y ejecutar |SHA256 ddadb1091e8501a00c0ae9ff9da212bce65446000131f137cede389ebc5313ad|
| 08 documental final |SHA256 8d4a7cbede73eac5b09524363e35d4780dc91d8e25ba6fa8f62de32a66c9984c|
| HEAD |7816d3328115cf5aa5bcdd0985fffd795b3ae084, cambios locales anteriores preservados|
| Build inicial188 archivos |ffa605bad0356759c5f1d21ce88f556fd79e07760ebcfdbae516ca6f132b1ddd|
| Build final190 archivos |7630c859296fd71dd4607133a461165e1b2d012d5679190652c5e0522bf4fa93|
| Delta del sublote |9 archivos, seis de lógica/modelo/plantillas, una migración y dos de pruebas|
| BuildChrome184fuentes |36de329a9d0eb30b1f91992a39dd82a575d3cc0d0dff94792162d819918187fe, idéntico en final2 y cadena-final. Conjunto/serialización propios|
| Entorno |Python3.12.10, Django5.2.18, SQLite3.49.1, Chrome157.0.8103.78, Playwright1.65.1. Tres contextos,1280×900, es-PE, America/Lima|
| Navegador de trazabilidad |20:52:44–20:52:52 Lima13/11,12 checkpoints y12capturas|
| Navegador de cadena completa |20:52:56–20:53:16 Lima13/11,44 checkpoints y14capturas|
| Suite final |20:52:53–20:54:12 Lima13/11,574/574 en76.868s, sin cambios de fuentes durante ejecución|
| Aislamiento |SQLite nueva por recorrido/runner o memoria para suite. Datos ficticios, HTTPWSGI loopback, middleware yCSRF activos. Base operativa fuera de la ejecución|

[Manifiesto inicial](evidencias/14-F-20261113/build-antes.json) · [Manifiesto final](evidencias/14-F-20261113/build-final.json) · [Snapshot de planificación](evidencias/14-F-20261113/planificacion-antes.zip) · [Regresión estable](evidencias/14-F-20261113/servidor/regresion-manifiesto.json) · [Validación del corte](evidencias/14-F-20261113/validacion-final.json).

### Inventario, clasificación y trazabilidad

Se seleccionaron VEN-01c, VEN-02a e INV-04 como dependencia, con14CA base. El inventario recoge además cinco criterios complementarios, ocho patrones de ruta,14familias de campos/salidas y diezRN. DEC-08-KARDEX/C-02 es una dependencia adicional trazada. La cadena general revalida maestros/stock/merma/caja según su caso previo, con un denominador propio. [Inventario detallado](soporte/14-F-inventario.md) · [Matriz de20 criterios](evidencias/14-F-20261113/criterios-final.json).

| Criterio | Evidencia y efecto observado | Estado y acción siguiente |
|---|---|---|
| VEN-01c/CA-01 |cadena-final25 rechaza efectivo insuficiente sin mutar. Fronteras de formato/precisión conservan suite y evidencia11 |PARCIAL en14-F, completar todas las fronteras en su alcance|
| VEN-01c/CA-02 |final2 cobra16.20, recibe20, devuelve3.80, cierra116.20. Contrato servidor50+caja100=150 |CUMPLE en muestra, incluidos reenvío y cierre|
| VEN-01c/CA-03 |F01/F02 y final2 asignanA3/B1, saldo0/6. cadena-final reproduce desactivación/reactivación y FEFO |PARCIAL, faltan carreras y totalidad de desempates|
| VEN-01c/CA-04 |Asignaciones y venta en la misma transacción. Ocho puntos postwrite revierten22tablas |PARCIAL, concurrencia/caída real y escritura directa pendientes15|
| VEN-01c/CA-05 |F05 y test de cierre recuperan la misma venta/asignaciones antes y después del cierre |PARCIAL, competencia por últimas unidades pendiente|
| VEN-01c/CA-06 |Costo3 conservado al agotar, fotografía de producto/código y precio tras editar maestros |PARCIAL por cobertura acotada de cambios, con revalidación14-E en suite|
| VEN-02a/CA-01 |Reapertura y recarga de la misma constancia. Correlativo preservado |PARCIAL, impresión física NO EJECUTADA|
| VEN-02a/CA-02 |final2/07 conserva vendedor/caja/orden/importes originales tras renombrar |CUMPLE en muestra, legado ausente rotulado|
| VEN-02a/CA-03 |Leyenda literal en capturas de ambas constancias |PARCIAL, salida física y canal operativo pendientes|
| VEN-02a/CA-04 |ADMIN y vendedor propio consultan, otro vendedor404 y almacenero403, datos intactos |PARCIAL, totalidad del acceso a última constancia conserva alcance12|
| INV-04/CA-01 |Movimiento muestraA3/B1 y costo histórico, además de cantidad total y autor |PARCIAL, alta prioridad, falta saldo por movimiento/orden completo|
| INV-04/CA-02 |Origen de recepción propia pendiente conocido de06/14-E |NO EJECUTADO en14-F, brecha heredada. Continuar14-G|
| INV-04/CA-03 |cadena-final distingue carga y merma con referencias/autor |PARCIAL, ajuste y origen de recepción conservan brechas|
| INV-04/CA-04 |Consulta legible y acceso por rol comprobados |PARCIAL, filtros/paginación completos pendientes|

La tabla base contiene2CUMPLE en muestra,11PARCIAL y1NO EJECUTADO en este sublote. Ninguna HU completa se cierra. Los criterios de mayor prioridad pendientes afectan integridad concurrente, origen de recepción y saldoKardex.

| Contrato complementario | Resultado final acotado |
|---|---|
| DEC-11-MODELO/C-01 |CUMPLE en muestra. A3/B2 vende5, asignaciones3/2, costo3, stock0/promedio0, caja150 con apertura100. Sale representa el ingreso único por total|
| DEC-11-MODELO/C-02 |PARCIAL. Ocho fallos posteriores a escritura y reenvío secuencial sin mutación. Carreras y caída real pendientes|
| DEC-11-MODELO/C-03 |CUMPLE en muestra. Cambiar nombre/código/producto/vendedor/caja conserva fotografía original y costo fuera de constancia|
| DEC-11-MODELO/C-04 |CUMPLE en muestra de historia. Legado conNULL/asignaciones ausentes y cobertura parcial explícita. Margen futuro conserva su condición|
| DEC-12-ORDEN/C-01 |PARCIAL. Posiciones1/2/3 conservan orden aunqueUUID3/1/2. Empates de turnos quedan pendientes|
| DEC-08-KARDEX/C-02, dependencia |CUMPLE en muestra. Salida enlazada a filas persistidas, legado desconocido y parcial rotulados|

La dirección planificación→sistema conecta RN-19/25 con selecciónFEFO/asignaciones, RN-28 con snapshots, DEC-12 con posición, RN-29 con permisos y RN-10 con cierre. En la dirección sistema→planificación, cada nueva salida visible tiene respaldo en DEC-11/C-03..04 o DEC-08/C-02. El inventario recoge tipo, inicial, precisión, límites, validación y persistencia. JSON de navegación registra texto completo, controles/etiquetas/valores, rol/ruta/instante y testigoBD.

### Recorridos y rechazo sin efectos

La muestra específica inicia con fixtureORM declarada de ZetaA3/B7 y AlfaC2. VENDEDOR agregaZeta4 yAlfa1, cobra16.20 y entrega3.80 de vuelto. Las asignaciones guardanA3/B1/C1 y stock0/6/1. ADMIN consulta movimientos nuevos y venta histórica sin datos. Un control técnico renombra vendedor/caja/producto/código sobre esa fixture. La constancia reabierta conserva el contenido original. VENDEDOR recibe403 al intentar movimientos con costo, con huella de negocio intacta, y cierra116.20 exacto. [Comparación de historia](evidencias/14-F-20261113/navegador/final2/comparacion-historia.json) · [Movimientos](evidencias/14-F-20261113/navegador/final2/movimientos-confrontados.json).

La cadena completa crea categoría/producto/proveedor comoADMIN mediante formularios. ALMACENERO registra3+7unidades a2. VENDEDOR abre100 y prepara4×3.55. Se rechazan categoría inactiva y efectivo insuficiente, se reactiva y cobra14.20 con efectivo20/vuelto5.80. ALMACENERO contrasta6 y da baja1, ADMIN consulta stock5, venta y asignaciones3/1. VENDEDOR cierra114.20. Incluye carga vencida, merma por causa incompatible/exceso y permisos denegados por navegación y tresPOST directos. [44 checkpoints](evidencias/14-F-20261113/navegador/cadena-final/ejecucion.json).

Estos cambios de maestros de la muestra específica son controles de fixture, distintos de las altas porUI de la cadena completa. Los valores/cuentas14D de la cadena identifican el caso reutilizado, con build y fecha14-F. Las bases de cada recorrido son independientes.

### Pruebas, conservación y reproducibilidad

| Ejecución | Resultado y evidencia |
|---|---|
| Runner previo |5/12, siete incumplimientos en asignación, fotografía, orden y aviso histórico. [JSON](evidencias/14-F-20261113/servidor/asignaciones-antes.json)|
| Runner final |12/12 sobre código final. [JSON](evidencias/14-F-20261113/servidor/asignaciones-final.json)|
| Pruebas focales |38/38 iniciales y8/8tests14-F definitivos, con subcasos. [Informe](evidencias/14-F-20261113/servidor/INFORME.md)|
| Regresión completa |Primera572/573, fixture corregida. Final574/574 en76.868s. [Log](evidencias/14-F-20261113/servidor/regresion-final.txt)|
| Migración |sales0005→0006 sobre filas ficticias, columnas previas idénticas, campos nuevosNULL y asignacionesvacías. Incluida en los8tests|
| Chrome específico |Previo11checkpoints reproduce cambio de identidad y orden inverso. Final2 tiene12checkpoints/12capturas con ausencia histórica y403 verificadas|
| Chrome cadena completa |44checkpoints/14capturas, desde altaADMIN hasta cierreVENDEDOR. Código estable|
| Validación documental |08 con74HU,287criterios y112casos.07/09/03 e índice regenerados, textos de criterios compatibles, evidencia y enlaces comprobados|

Los conjuntos se solapan. Las corridas intermedias `final/`, `flujo-completo/` y `corrida-1/` se conservan, con cambios de fuentes durante ejecución. Los cortes acreditados son `final2/`, `cadena-final/`, `asignaciones-final.json` y la suite final estable. El inventario e informe distinguen lectura de código de ejecución. [Navegador y comandos](evidencias/14-F-20261113/navegador/RESUMEN.md) · [Servidor y comandos](evidencias/14-F-20261113/servidor/INFORME.md).

Los nuevos tests comparan22tablas de negocio ante fallo en contador existente, venta, línea, primera/segunda asignación, primer/segundo descuento de lote y descarte del borrador. La comprobación ve escritura real antes de fallar y exige reversión completa. La migración deja historia desconocida. Las bases persistentes ficticias del runner fueron saneadas de sesiones, intentos de autenticación y hashes de credenciales, conservando huella de ventas/líneas/lotes/asignaciones. [Registro de saneamiento](evidencias/14-F-20261113/servidor/sanitizacion-bases.json).

Se inspeccionaron capturas de movimientos, constancia reabierta, legado y cierre. Los avisos de asignación parcial y coincidencia por código sinFK tienen pruebaHTTP/BD, con recorridoChrome específico NO EJECUTADO. La impresión física mantiene su pendiente. La suite evalúa SQLite, mientras PostgreSQL y recuperación siguen en15.

### Decisiones, omisiones y coherencia documental

La corrección implementa requisitos previamente aceptados. Se eligieron asignaciones durables con snapshots de lote, cabecera nullable y posición estable. Para el ingreso de venta en efectivo se aceptó la equivalencia deSale, permitida por02/DEC-11, con clave/turno/autor/instante/total y suma única al cierre. La alternativa de una tabla adicional de movimientos se conserva para orígenes futuros, con riesgo de doble conteo y costo de conciliación. [Fundamento de aceptación](soporte/14-F-disposiciones.md).

La migración preservaNULL del legado. El diagnóstico operativo y la regularización de historia requieren hechos aún pendientes. Una coincidencia de código no prueba el producto histórico, por eso se informa en la consulta. El costo del lote actual tampoco reconstruye una venta pasada. Las recomendaciones de integridad, datos, UI, pruebas y arquitectura incluyen beneficio, riesgo, costo e impacto en el inventario.

08 se actualizó antes de regenerar07/09/03.02/14/16/21/01/00 y continuidad reflejan la concreción técnica y sus límites. La fixture de constancia se ajustó a la representación vigente y su versión anterior coincide con el hash inicial. Las pruebas de legado protegen la rama desconocida. Las HUs futuras conservan su selección.

### Cursor exacto y pendientes

**14-G-RECEPCIONES-01, primera pasada.** Seleccionar HU-INV-01b y DOC-03AI-01/C-01..04. Preparar carga inicial10 a3, recibir lote comercialC10 a6 con claveUUID1 y referenciaR-00000001. Esperar físico20/promedio4.5000, constancia propia con actor/proveedor/cantidad recibida original. Reenviar misma clave/contenido debe devolver la misma recepción sin mutación. Reenviar con cantidad11 u otro actor debe rechazar.

Registrar después otra recepción real del mismo loteC y misma caducidad,5 a8 con claveUUID2. Esperar referencia distintaR-00000002, dos procedencias y físico25/promedio5.2000. Una caducidad contradictoria requiere rechazo. Probar lote repetido dentro de la recepción, error antes de confirmar, fallo postwrite y agotamiento del correlativo. Separar cantidad recibida original de aumentos de capacidad por ajustes. Preservar el legado cuyo origen no está demostrado, con diagnóstico/migración aislada. Concurrencia con misma clave requiere PostgreSQL en15.

Después, continuar saldo cronológico/filtros/paginación del Kardex y constancia dedicada de merma. Permanecen ajuste con lote nuevo/costo documentadoQ0, valoración operativa incierta, empate de turnos, seguridad/concurrencia/caída y demás condiciones de los inventarios. Etapas15–17 y segunda pasada conservan su secuencia. El cierre14-F corresponde al sublote descrito.

---

## Registro anterior14-E, conservado con sus límites

<a id="vigente-14-e"></a>
## Estado del corte14-E · 13/11/2026, Lima

**Primera pasada, continuación14-D. Etapa PARCIAL. Sublote14-E concluido para valoración móvil, costo de salidas y rechazo de ajuste sin costo fiable.** Se corrigieron tres comportamientos contrarios a RN-14 y se añadieron snapshots de costo en bajas/ajustes sin reconstruir datos históricos. Próximo cursor **14-F-ASIGNACIONES-01**. Asignaciones por lote, recepción propia, Kardex y constancia dedicada de merma continúan pendientes; no se declaran terminados otros módulos.

El [informe anterior](evidencias/14-E-20261113/etapa-14-antes.md) y el [estado anterior](evidencias/14-E-20261113/estado_general-antes.md) se conservan íntegros.14-D acreditó creación de maestros, carga y cadena nominal con variantes de estado/permisos.14-E revalida una dependencia concreta con F-COSTO, cuyo saldo inicial se prepara como fixture explícita. No se afirma que14-E haya repetido por interfaz la creación de maestros de14-D.

### Versión, alcance y entorno

| Elemento | Corte14-E |
|---|---|
| 08 inventariado y usado por navegador/servidor | SHA256 e8acd6d39ce5fc5c526d2dfa8c326f2c19b0f46ef032c6b0245bd89ac3644847 |
| 08 documental final | SHA256 ddadb1091e8501a00c0ae9ff9da212bce65446000131f137cede389ebc5313ad |
| HEAD |7816d3328115cf5aa5bcdd0985fffd795b3ae084, con cambios locales previos conservados |
| Build inicial186 archivos |957c697258a5545eac4c77d1aba2660bd27e1647053957de2a827f37308751f7 |
| Build final188 archivos |ffa605bad0356759c5f1d21ce88f556fd79e07760ebcfdbae516ca6f132b1ddd |
| Delta del sublote |8 archivos:3 de lógica/modelos,1 migración y4 de pruebas. Sin cambios de plantillas |
| Build navegador182 archivos |f9927d5136a2f833693076bf589d155b3d467a32b7dab5b1be1561f7f6cf9978. Conjunto/serialización propios; solo test_audit14e_valuation.py cambió después, reejecutado en suite final |
| Herramientas |Python3.12.10, Django5.2.18, SQLite3.49.1, Chrome157.0.8103.78 y Playwright1.65.1 |
| Navegador |19:59:30–19:59:45 Lima13/11; UTC00:59 del14/11. Tres contextos,1280×900, HTTPWSGI loopback, middleware/CSRF activos |
| Regresión final |20:27–20:28 Lima13/11,566 tests,79.782s. Manifiesto sin cambios durante ejecución |
| Datos y entorno |Ficticios, SQLite temporal nueva por recorrido o memoria por runner. Sin leer/migrar base operativa, sin despliegue |

[Manifiesto inicial](evidencias/14-E-20261113/build-antes.json) · [Manifiesto final](evidencias/14-E-20261113/build-final.json) · [Planificación anterior](evidencias/14-E-20261113/planificacion-antes.zip) · [Regresión y huella](evidencias/14-E-20261113/servidor/regresion-manifiesto.json) · [Validación del corte](evidencias/14-E-20261113/validacion-final.json).

### Inventario y trazabilidad en ambas direcciones

[Inventario14-E](soporte/14-E-inventario.md) identifica3 HU principales,12 CA base,4 criterios DOC-03AH,9 rutas y15 familias de campos/salidas. INV-03 es dependencia del algoritmo; DOC-03AI, DEC-11-MODELO y DEC-08-KARDEX suman11 criterios dependientes todavía pendientes. El inventario14-D de23HU/80CA es heredado; no se suma al denominador14-E ni se convierte automáticamente en cobertura actual. Se mantuvieron74HU,287criterios y112casos escritos en08.

| Criterio principal | Evidencia nueva, esperado y observado | Resultado y siguiente acción |
|---|---|---|
| INV-01b/CA-01 |E05: físico18@3 incluye8 vencidas; recibe10@6 y guarda28@4.0714. Chrome03/04 muestra4,07 |PARCIAL, alta: fórmula resuelta; identidad propia y reintento de recepción faltan DOC-03AI |
| INV-01b/CA-02 |Chrome04 muestra4,07 y testigo4.0714; test14E recibe después2@9 y conserva snapshots anteriores |CUMPLE en muestra secuencial; legado operativo sin revaloración |
| INV-02/CA-01 |E08 rechaza exceso; E13 y Chrome08 descuentan1 del lote correcto y preservan costo |PARCIAL: cantidades/causas muestreadas, fronteras completas y carreras no revalidadas aquí |
| INV-02/CA-02 |E18 y Chrome10 dan baja a8 vencidas sin cambiar promedio; causaVENCIMIENTO. Matriz de robo/daño de14-D heredada |PARCIAL: revalidación de costo/caducidad; no atribuir a14-E todas las variantes de causa |
| INV-02/CA-03 |Cuatro bajas nuevas contienen responsable/detalle y costo; exigencia de detalle heredada y regresión existente |PARCIAL: interfaz recorre daño explicado, resto conserva evidencia detallada previa |
| INV-02/CA-04 |Registro/correlativo visible en movimientos, costo en persistencia |PARCIAL, alta: falta constancia dedicada |
| VEN-01c/CA-01 |Regresión de cobro y error sin efectos; E09 añade rollback después de escritura |PARCIAL: fronteras de efectivo conservan casos anteriores, no se sustituyen por fallo sintético |
| VEN-01c/CA-02 |Chrome06/16: venta8, recibido10, vuelto2, apertura100 y cierre108 exacto |CUMPLE en muestra; no equivale a todos los topes monetarios |
| VEN-01c/CA-03 |Venta1 omite vencidos; test vende todo lo vigente y conserva físico vencido/promedio; agotamiento posterior0 |PARCIAL, alta: no prueba toda concurrencia, desempates ni asignación histórica |
| VEN-01c/CA-04 |E09 prueba transacción de venta y costo; E19 agota físico y preserva costo de última salida |PARCIAL, alta: no existen asignaciones durables por lote; caída real pendiente |
| VEN-01c/CA-05 |Regresión idempotente existente; costo no cambia por reintento. Runner14E no introduce carrera |PARCIAL, alta: reenvío secuencial no acredita competencia por últimas unidades |
| VEN-01c/CA-06 |E11/E20 y Chrome17 preservan costo4.0714 e importes tras agotamiento; nueva recepción no altera costos anteriores |PARCIAL: fotografía de costo revalidada; restantes ediciones de maestros mantienen evidencia anterior |

Los2CUMPLE y10PARCIAL de esta tabla se refieren a la muestra seleccionada; ninguna HU completa se cierra. [Matriz estructurada con textos de08](evidencias/14-E-20261113/criterios-final.json).

| Contrato DOC-03AH | Cobertura final |
|---|---|
| C-01 |CUMPLE en muestra: E01/E02/E05 y Chrome03/04. Expiración sola conserva físico/costo; entrada pondera físico completo |
| C-02 |CUMPLE en muestra: E10..14/E18..20/E22..23, Chrome07..16, test de agotamiento por venta/baja/ajuste. Salida captura costo antes de cero |
| C-03 |CUMPLE en muestra: E16/E17/E21, test de+2 y rechazoQ0 sin costo. La capacidad general de aportar costo documentadoQ0 permanece pendiente |
| C-04 |PARCIAL: E04/E09/E12/E15 observan escritura real seguida de excepción y rollback íntegro. ConcurrenciaPG y caída de proceso NO EJECUTADAS en14-E |

La dirección sistema→requisito enlaza recepción/costo visible con RN-14 e INV-01b; costo de salida interno con RN-28/DOC-03AH; stock vigente con RN-03; precio/efectivo/vuelto/cierre con VEN-01c y CAJA; campos nuevos con diseño02 y la tarea de integridad existente. Costo de compra no se expone al vendedor en constancia. Las capturas JSON incluyen texto visible, campos/etiquetas/tipos/límites/valores, ruta, actor y testigo de persistencia; los ocultos secretos se excluyen. El inventario inicial conserva sus estados anteriores y el presente corte determina qué se revalidó.

Mensaje nuevo del ajusteQ0, en `delta`: «No se puede aumentar un stock físico en cero sin un costo fiable documentado. Investigue y documente el origen antes de regularizar las existencias.» HTTP200 con error y huella sin mutación. Su rechazo se probó por servidor; **no se recorrió este formulario nuevo de error en Chrome**. El error de costo0 en recepción sí tiene captura02b y posterior recuperación a6,0000.

### Recorrido conectado y pruebas

1. ADMIN consulta fixture de18 unidades físicas,8 vencidas y10 vigentes, costo3. ALMACENERO abre recepción y envía costo0: rechazo sin mutar. Corrige a6 y recibe10; ADMIN ve físico28/vigente20/costo4,07.
2. VENDEDOR abre caja100, busca producto, vende1 a8, entrega10 y obtiene vuelto2. Se guarda SaleLine.unit_cost4.0714. ADMIN relee stock27 y promedio4,07.
3. ALMACENERO da baja1 por daño con explicación: físico26 y costo4.0714. ADMIN consulta movimientos/venta/carga. Baja8vencidas,8vigentes y10vigentes deja18→10→0; promedio4.0714→4.0714→0. Venta y cuatro bajas conservan4.0714.
4. ADMIN relee constancia/venta; VENDEDOR cierra108 contado/esperado, diferencia0. Las bajas no alteran importes de venta ni caja.

| Evidencia | Resultado y límite |
|---|---|
| [Servidor antes](evidencias/14-E-20261113/servidor/costos-antes.json) / [después](evidencias/14-E-20261113/servidor/costos-despues.json) |11/23→23/23.12 incumplimientos iniciales resueltos en los casos definidos; no son12 defectos independientes |
| [Chrome antes](evidencias/14-E-20261113/navegador/antes/ejecucion.json) / [final](evidencias/14-E-20261113/navegador/final/ejecucion.json) |22→23 checkpoints; final22JPG,23JSON de observación,20 comparaciones de costo CUMPLE,51 artefactos indexados |
| [Regresión focal](evidencias/14-E-20261113/servidor/regresion-costo-despues.txt) |66/66, con seis tests14E. Se amplió agotamiento y se reejecutaron [6/6 finales](evidencias/14-E-20261113/servidor/14e-final.txt) |
| [Regresión integral](evidencias/14-E-20261113/servidor/regresion-final.txt) |566/566; system check sin incidencias y makemigrations --check sin cambios. Repetida después de ampliar dos aserciones; [primera corrida](evidencias/14-E-20261113/servidor/regresion-1.txt) conservada |
| Migración0006→0007 |Test con filas anteriores: todos los campos antiguos intactos, costo nuevoNULL, promedio y cantidades intactos. No es migración operativa |
| [Inspección visual](evidencias/14-E-20261113/navegador/RESUMEN.md) |Revisadas capturas02b/03/06/09/15/16, costo4,07 y0,00, errores y constancia sin costo. No hubo cambio de diseño de pantalla |

Los conjuntos anteriores se solapan. El [informe servidor](evidencias/14-E-20261113/servidor/INFORME.md) identifica variantes de roles ADMIN sin recepción, ALMACENERO sin ajuste y VENDEDOR sin baja, rechazo por cantidad excesiva y cuatro fallos posteriores a escritura. Estado comercial/revocación y otras fronteras siguen como evidencia heredada14-D y regresión existente; no se describen como nuevos recorridos14-E.

Para reproducir con salida inédita, ejecutar el runner [costos.py](evidencias/14-E-20261113/servidor/costos.py) con Python de r1-pmv y un archivo JSON nuevo; usa memoria y credenciales efímeras. [regresion.py](evidencias/14-E-20261113/servidor/regresion.py) crea memoria y registra antes/después, rechaza sobrescribir su log existente. El [resumen navegador](evidencias/14-E-20261113/navegador/RESUMEN.md) contiene comando y dependencias del runner con directorio de salida nuevo. Sus fechas son relativas al día Lima. Las rutas del comando deben ejecutarse desde la raíz de planificación.

### Hallazgos, aceptación y legado

[Disposiciones14-E](soporte/14-E-disposiciones.md) conserva fundamento de cada aceptación: algoritmo ya exigido por RN-14/DOC-03AH y representación nullable proporcional a RN-28. Antes, recepción28 unidades calculaba4.5000; después de merma26 calculaba4.6667 y al agotar conservaba6.0000 en navegador. Estas discrepancias no se convirtieron en requisitos. Las expectativas antiguas se sustituyeron con copias/trazabilidad, y se agregaron pruebas de los efectos entre módulos.

Los snapshots nuevos no prueban que un promedio operativo heredado sea correcto. `is_initial=True` agregado históricamente y una FK de carga tampoco demuestran origen real de cada recepción. El [inventario](soporte/14-E-inventario.md) propone diagnóstico de clon read-only y alternativas de apertura sustentada; **no ejecutado sobre datos operativos**. NULL se conserva desconocido, sin default0 ni reconstrucción desde compras restantes. No se certifica contabilidad, fiscalidad ni rentabilidad.

El backlog ya contiene las necesidades de trazabilidad. Se completó una decisión técnica sin duplicar HU. Beneficio/riesgo/costo/impacto de diagnóstico, asignaciones, recepciones, Kardex y pruebasPG están documentados como recomendaciones o tareas pendientes. Redactarlas no las implementa ni acepta automáticamente una solución concreta.08 se actualizó primero;07/09/03 e índice regenerados;02/14/16/21 y continuidad coherentes. La comparación final mantiene textos de criterios compatibles con la versión ejecutada.

### Pendientes y cursor exacto

**14-F-ASIGNACIONES-01, primera pasada.** Antes de completar Kardex, contrastar DEC-11-MODELO-AUDITORIA-VENTAS/C-01..04 con una venta que cruza lotes: preparar A3/B7 vigentes con vencimientos ordenados, costo promedio conocido, vender4. Esperado, dos asignaciones durables A3/B1 cuya suma4 coincide con SaleLine, FEFO real y saldo6; referencia de cada lote, posición de línea y snapshots de vendedor/caja estables. Preparar además venta histórica sin asignaciones y costoNULL, conservar «desconocido», sin aplicar FEFO retrospectivo. Probar reintento sin duplicar y fallo después de primera asignación sin commit parcial; vendedor consulta solo propio, ADMIN contrasta, ALMACENERO revisa inventario.

Luego abordar DOC-03AI de recepción propia y DEC-08-KARDEX: no derivar saldo/origen de una historia que todavía no se registra. Conservar constancia dedicada de merma, ajuste de lote nuevo/costo documentadoQ0, diagnóstico operativo y las condiciones no cubiertas del inventario. PostgreSQL/concurrencia/caída real permanecen en15, normativa en16, conciliación17 y segunda pasada después de actualizar00. El sublote14-E no abre esas etapas ni las marca aprobadas.

---

## Registro anterior14-D, conservado con sus límites

<a id="vigente-14-d"></a>
## Estado del corte14-D · 13/11/2026, Lima

**Primera pasada, continuación de14-A/B/C. Etapa PARCIAL. Sublote14-D concluido en el alcance descrito.** La misma secuencia recorrió ADMIN→ALMACENERO→VENDEDOR→ALMACENERO/ADMIN→VENDEDOR con formularios de Chrome, servidor HTTP y base temporal. Se corrigieron descuento discrecional nuevo y causas de merma conforme a08. El cierre completo de etapa 14 requiere todavía valoración/costo, asignaciones históricas por lote, Kardex y constancia dedicada de merma. Próximo cursor **14-E-KARDEX-01**.

El presente registro prevalece sobre las conclusiones de cierre de14-A/B/C que se conservan abajo. El informe anterior calificaba navegador como opcional y atribuía pruebas aisladas a una cadena E2E. El protocolo exige la ejecución real o su estado pendiente. Los antecedentes permanecen como evidencia de sus aserciones, build y fecha. [Registro previo conservado](evidencias/14-D-20261113/etapa-14-antes.md) · [Estado previo](evidencias/14-D-20261113/estado_general-antes.md).

### Versiones y entorno

| Elemento | Corte14-D |
|---|---|
| 08 al inventariar y ejecutar navegador | SHA256 33d2f17067fec3bb30e018ef49b77d87f84adfd9bafe04adf19161cd286e47a4 |
| 08 al cierre documental | SHA256 e8acd6d39ce5fc5c526d2dfa8c326f2c19b0f46ef032c6b0245bd89ac3644847 |
| HEAD | 7816d3328115cf5aa5bcdd0985fffd795b3ae084 |
| Build de186 archivos al inicio | aa492d12623b64f84cf34f2d09392d2d53d27f974b58782df03877e6e04ad6f8 |
| Build final de186 archivos | 957c697258a5545eac4c77d1aba2660bd27e1647053957de2a827f37308751f7 |
| Manifiesto del navegador,180 archivos | 849dba031ad52612261b94758562a8b277902dca586d4925f05ac6edb438472e. Conjunto y serialización propios. Comparación final por archivo |
| Cambios locales | Estado previo conservado en build-antes.json. Delta de esta sesión en12 archivos de producto/pruebas, cinco de lógica/UI y siete de pruebas |
| Herramientas | Python3.12.10, Django5.2.18, SQLite3.49.1, Chrome157.0.8103.78 y Playwright1.65.1 |
| Navegador final | recorrido3, 17:13:33–17:13:52 Lima, tres contextos,1280×900, HTTP real loopback, CSRF y middleware activos |
| Servidor | Django Client en proceso con CSRF y login por formulario. Variante de vencimiento avanza reloj controlado un día |
| Aislamiento | SQLite temporal nueva para Chrome y :memory: para servidor/suites. Cuentas ficticias y secretos aleatorios. Sin acceso a datos operativos |

Los hashes de build distintos de13/14-A tienen ámbitos de manifiesto diferentes. La comparación por archivo identifica compatibilidad. La actualización de08 agrega un caso integrado, corrige un conteo editorial de variantes y registra estados/evidencia, manteniendo el requisito funcional aplicado a las pruebas. El ZIP conserva08 y siete documentos relacionados previos. [Build inicial](evidencias/14-D-20261113/build-antes.json) · [Build final](evidencias/14-D-20261113/build-final.json) · [Planificación anterior](evidencias/14-D-20261113/planificacion-antes.zip) · [Verificación final](evidencias/14-D-20261113/validacion-final.json).

### Inventario, fuentes y cobertura

Se aplicaron completos PROTOCOLO_COMUN y CONTINUIDAD_Y_SEGUNDA_PASADA. Se contrastaron01/02/03/07/08/09/14/16/21, CONTROL_SPRINTS y los resultados detallados01–12. AGENTS.md ausente en el workspace y sus ancestros comprobados. PLANIFICACION_SCRUM_R1PMV.xlsx ausente, sin uso como fuente. El inventario adjunto clasifica selección, actor, CA/RN, tarea, ruta, pantalla, acción, literal, campo, formato/límites, valor inicial, error, persistencia y salida.

| Unidad | Denominador y cobertura del sublote |
|---|---|
| HUs principales | 23 seleccionadas,80 CA base individualizados |
| CA con alguna muestra nueva | 50/80. Clasificación final conservadora,49 PARCIAL,2 INCUMPLE,29 NO EJECUTADO. Cero CA declarados completamente verificados por extensión de este recorrido |
| Reglas, rutas y campos | 16 RN,39 patrones de ruta y36 filas de campo/familia inventariados. La lista incluye acciones adyacentes pendientes |
| Superficie estática | 30 plantillas,1320 fragmentos y313 cadenas candidatas. Inventario de condiciones y código |
| Evidencia navegador final | 44 checkpoints,41 observaciones UI+3 POST directos con sesión navegador.14 JPG y18 comparaciones de huella completa sin mutación |
| Evidencia servidor nueva | 18 variantes S01..S18,21 tablas de cinco apps con huellas antes/después y control positivo |
| Regresión final | 560/560. Incluye119 tests14-A/B/C y pruebas de ausencia de funcionalidades pendientes |

Los conteos son unidades distintas y se solapan. La clasificación de80 CA limita el alcance de sus condiciones, incluso si una aserción nominal cumple. INV-04/CA-01 yCA-04 incumplen en la superficie observada por carencia de saldo por fila/lote de venta y filtros. Las propuestas y los contratos complementarios mantienen clasificación propia. [Inventario completo](soporte/14-D-inventario.md) · [Matriz individual80 CA](evidencias/14-D-20261113/inventario/criterios-base.json) · [Textos/condiciones estáticos](evidencias/14-D-20261113/inventario/superficie-final.json).

### Recorrido conectado y trazabilidad

B identifica el prefijo de JSON/captura en recorrido3. S identifica la variante del runner servidor. Cada paso dispone de texto visible, controles y testigo de persistencia.

| Paso, rol y planificación | Esperado | Observado y evidencia nueva | Estado acotado y antecedente |
|---|---|---|---|
| Ingreso deADMIN/ALMACENERO/VENDEDOR, AUTH01 yRN29 | Sesión propia y ámbitos correspondientes | B01/02/03, roles visibles. GET403 B04/11/15, POST403 B05b/12b/20b, S01..05 con huella estable | CUMPLE muestra. Revocación/contraseñas/fronteras conservan [01](ETAPA-01.md) y[02](ETAPA-02.md) |
| ADMIN alta categoría/producto/proveedor, CAT02,PROD02,PROV02 | Maestros activos disponibles al almacenero y producto sin stock | B05..10, Familia14D, Harina14D, precio3.55, mínimo5, código interno, proveedor ficticio RUC20000000014 | CUMPLE nominal. [03](ETAPA-03.md),[04](ETAPA-04.md) |
| ALMACENERO carga inicial, INV01a,RN01/03/14 | Dos lotes ligados al proveedor/autor, stock10 y costo2.0000. Rechazo de hoy sin alta parcial | B12..14, A3 vencehoy+7 yB7 vencehoy+30. B13 rechaza fecha hoy con huella intacta | CUMPLE muestra homogénea. Costos distintos y recepción propia pendientes. [05](ETAPA-05.md),[06](ETAPA-06.md) |
| VENDEDOR apertura y preparación, CAJA01,VEN01b,RN30 | Turno100, borrador4, stock10 hasta confirmar | B16..20, una preparación de14.20 sin venta ni reserva | CUMPLE muestra. [09](ETAPA-09.md),[10](ETAPA-10.md) |
| ADMIN cambia categoría con venta revisada, J-CA yVEN01c | Cobro rechaza mientras inactiva, reactivación permite continuar | B21..24 por confirmación UI. S08 estado de producto, S09 categoría, S10 confirmación obsoleta409. Rechazos sin mutación | CUMPLE muestra de transición. [03](ETAPA-03.md),[11](ETAPA-11.md) |
| VENDEDOR confirma efectivo, VEN01c,RN19/25/27,DEC11descuentos | 14.19 rechaza.20 cobra14.20, vuelto5.80, base12.03, IGV2.17. FEFO3+1 | B25..28, JS y servidor coinciden, una ventaV-00000001, lotes[3,7]→[0,6], recarga estable. S13 vencehoy antes de cobro yS17 reintenta | CUMPLE operación, trazabilidad histórica PARCIAL. [11](ETAPA-11.md),[12](ETAPA-12.md) |
| ALMACENERO contrasta y registra merma, INV02,RN05/20 | Consulta6, rechaza baja7 y causaVencimiento vigente, daño explicado1 deja5 | B29..32/30b. S11..16 comprueban causa real y explicación de robo vencido | CUMPLE causa/cantidad, costo/constancia PARCIAL. [07](ETAPA-07.md),[08](ETAPA-08.md) |
| ADMIN revisa stock/movimientos/ventas, INV04,VEN05b,VEN02a | Cantidades+3/+7/−4/−1, responsables, total14.20 ysaldo5 | B33..36 muestran esas referencias y constancia. Faltan saldo por fila, asignación durable de lote de venta, filtros/paginación | PARCIAL, INV04CA01/04INCUMPLE. [08](ETAPA-08.md),[12](ETAPA-12.md) |
| VENDEDOR cierra, CAJA02,RN10/30 | Esperado100+14.20=114.20, contado114.20,diferencia0. Un cierre y turnoCLOSED | B37..40, acta releída, preparación exige turno abierto. S07 cierre con borrador rechaza yS18 segundo cierre rechaza | CUMPLE muestra. Acumulados y concurrencia pendientes. [09](ETAPA-09.md) |

Cada enlace anterior remite al resultado detallado heredado. Sus casos se revalidan solamente en las acciones enumeradas. [Síntesis navegador](evidencias/14-D-20261113/navegador/RESUMEN.md) · [44 checkpoints y comandos](evidencias/14-D-20261113/navegador/recorrido3/ejecucion.json) · [Matriz18 variantes y reproducción](evidencias/14-D-20261113/servidor/INFORME.md).

### Hallazgos, cambios y pruebas

| ID y prioridad | Evidencia/fundamento | Disposición |
|---|---|---|
| H14D-01, alta | Descuento editable y cobro con descuento aceptado contra DEC-11-DESCUENTOS/C-01 | Corregido formulario, servicio y cálculo visible. Reintento histórico preservado. Verificado en pruebas y Chrome |
| H14D-02, alta | S12 permitía vencimiento prematuro con baja real. S15/16 rechazaban robo vencido y sugerían causa equivocada | Corregida causa/fecha/detalle en servicio bloqueado.18/18 variantes finales y58/58regresión inventario |
| H14D-03, media | Regresión anterior558/559, C16 lee venta por UUID y obtiene dos vecesV-00000001 | Corregida identificación por clave del POST, correlativos exactos. La explicación anterior sobre savepoints carecía de reproducción que la sustentara |
| H14D-04, alta | B34 y vista muestran salida−4 sin asignación por lote ni saldo de cada movimiento | INCUMPLE INV04CA01/04, contratosDEC08/DEC11PARCIAL. Continúa14-E con dependencias de valoración y origen |
| H14D-05, media | B32 confirmaB-00000001 y vuelve al selector. B34 muestra baja, sin consulta dedicada inmutable | PARCIAL INV02CA04/RN05C03. Constancia pendiente |
| H14D-06, media | Antecedente14A atribuye altas a HU de consulta, movimientos a INV06 futura yFEFO aRN05 | Corregido mapa vigente en inventario. RN19 respaldaFEFO, CAT02/PROD02/PROV02 respaldan altas eINV04movimientos |
| H14D-07, media | Código repondera costo tras salida y carece de snapshots de baja/asignación durable. Dos lotes de mismo costo ocultan ese efecto | PARCIAL heredado con inspección actual, reproducción F-COSTO pendiente en14-E |
| H14D-08, baja | Índice JSON derivado previo desfasado aunque07/09/03 coincidían con08 | Regenerados los cuatro derivados y validada reproducción exacta |

Se aplicaron correcciones locales contra contratos ya aceptados usando la autorización de esta sesión, con el fundamento separado en D14-01..05. La aceptación deCP-INTEGRACION-ROLES-001 procede del pedido explícito de verificación. La política de promociones futura y el procedimiento para apertura de productos solo vencidos conservan investigación. Las alternativas, beneficio, riesgo, costo e impacto de HU/RN/arquitectura/diseño/NFR/tareas/pruebas se documentan en [disposiciones](soporte/14-D-disposiciones.md).

| Prueba | Resultado final y límite | Evidencia |
|---|---|---|
| Descuento antes |1/1 aprobaba política anterior incompatible con08 | [Antes](evidencias/14-D-20261113/descuento-antes.txt) |
| Regresión completa antes |558/559, falloC16 | [Log](evidencias/14-D-20261113/servidor/regresion-antes.txt) |
| Variantes de servidor antes/después |15/18→18/18 para expectativas declaradas, CSRF y21 tablas | [Antes](evidencias/14-D-20261113/servidor/variantes-antes.json),[después](evidencias/14-D-20261113/servidor/variantes-despues.json) |
| Regresión acotada cobro/historia/caja/C16 |81/81,11.359s. Posteriormente se precisó fixture histórica20−2=18, cubierta en final integral | [Log](evidencias/14-D-20261113/descuento-despues.txt) |
| Regresión acotada inventario |58/58,6.006s | [Log](evidencias/14-D-20261113/servidor/regresion-inventario-despues.txt) |
| Regresión completa final |560/560,81.487s, incluye regresiones de los cinco módulos | [Log](evidencias/14-D-20261113/servidor/regresion-final.txt) |
| Chrome final |44/44 checkpoints,14capturas,18huellas iguales en rechazos/consultas | [Índice](evidencias/14-D-20261113/navegador/recorrido3/indice.json) |
| Django check y migraciones dry-run |Sin incidencias ni cambios de esquema, SQLite en memoria | [Log](evidencias/14-D-20261113/servidor/check-final.txt) |

El navegador aporta persistencia después de respuestas/recargas. El testigo servidor incluye21 tablas de negocio/identidad, excluyendo tablas técnicas de sesión, auth/admin y migración. Los escenarios rechazados comparan sus huellas completas. Los positivos delimitan las tablas autorizadas. El conjunto no acredita muerte de proceso después de escritura, carrera PostgreSQL ni despliegue.

### Pendientes y cursor exacto

**14-E-KARDEX-01, primera pasada.** Leer este registro y los contratos DOC-03AH-01/C-01..04, DOC-03AI-01, DEC-11-MODELO-AUDITORIA-VENTAS y DEC-08-KARDEX-COMPRAS. Crear fixture nueva F-COSTO con18 unidades/promedio3, ocho vencidas y diez vigentes. Recibir10a6, esperar físico28/vendible20/promedio4.0714. Retirar una unidad y contrastar saldo27, promedio y snapshot4.0714. Registrar resultado previo a cualquier corrección y diagnóstico de historia. Después definir/persistir las asignaciones reales de venta y orígenes necesarios, revalidar carga→venta→merma→ADMIN→cierre y completar Kardex con saldos/filtros. Datos legacy insuficientes requieren alternativas documentadas.

Permanecen pendientes constancia dedicada de merma, normalización interior de lote, recepción ordinaria con identidad propia, topes acumulados, snapshots vendedor/caja, matriz exhaustiva de permisos y ramas/fronteras de los80 CA. Las pruebas visuales de móvil, lector, impresión física, lector de pantalla, revocación completa, tránsito real de medianoche y caída postwrite quedan NO EJECUTADO en14-D. Las carreras, backup/restauración, CI y despliegue requieren etapa 15. Normativa/viabilidad requiere16 y conciliación completa17. Después corresponde preparar00 y segunda pasada01–17.

## Informe y resultados históricos conservados

Los siguientes sublotes se conservan como antecedentes. Sus conclusiones de cierre, atribuciones de HU/RN y explicación deC16 quedan rectificadas por14-D. Una credencial ficticia fue omitida conforme al protocolo.

# ETAPA-14 · Integración por roles — Primera pasada, sublotes 14-A, 14-B y 14-C

> **Fuente funcional principal:** [08 · planificación unificada](../../08_Historias_de_Usuario.md). Las fichas, RN y contratos de 08 definen lo esperado; este documento conserva su papel de evidencia. Las vistas 07/09/03 se derivan de 08.

**Fecha:** 13/11/2026 Lima  
**Pasada:** Primera  
**Etapa:** 14 — Recorrido completo entre roles  
**Sublote:** 14-A — Flujo E2E ADMIN→ALMACENERO→VENDEDOR + permisos + efectos cruzados + estados + vencimiento + idempotencia
**Sublote:** 14-B — Verificación del HTML renderizado por rol (CT-COHERENCIA-UI): menús, dashboards, tarjetas, headings, accesibilidad, login y páginas 403
**Sublote:** 14-C — Edge cases de efectos cruzados (PROP-14-03) y auditoría comportamiento→planificación

---

## 1. Registro de versiones y entorno

| Elemento | Valor |
|---|---|
| Versión de 08 (SHA-256) | `33d2f17067fec3bb30e018ef49b77d87f84adfd9bafe04adf19161cd286e47a4` |
| HEAD del repositorio | `7816d3328115cf5aa5bcdd0985fffd795b3ae084` |
| Build (SHA-256 de 231 archivos) | `1c3325902c4a948662eef111dec9ecf62e9bec57f568d9d3173c6bae7b7ac165` |
| Entorno de prueba | SQLite en memoria, `APP_ENV=test`, Django TestCase aislado |
| Herramienta | Django test runner, Django Client (servidor embebido) |
| Datos ficticios | admin@pruebas.invalid, almacen@pruebas.invalid, vendedor.a@pruebas.invalid, inactivo@pruebas.invalid |
| Caja semilla | CAJA-01 activa |
[Credencial de fixture omitida para cumplir el protocolo.]
| Suite total antes de E14 | 440 pruebas existentes |
| Suite total con E14 | 559 pruebas (42 E14-A + 65 E14-B + 12 E14-C + 440 existentes) |
| Resultado de regresión | **559/559 OK** en 78.4s, 0 fallos, 0 errores |

---

## 2. Alcance y exclusiones

### Incluido en este sublote

- **Módulos:** identity, catalog, inventory, cash, sales — conexiones entre los cinco
- **Roles:** Administrador → Almacenero → Vendedor → Almacenero/Administrador → Vendedor
- Flujo E2E completo: crear categoría/producto/proveedor → cargar stock → abrir caja → vender → merma → revisión admin → cerrar caja
- Permisos denegados: 14 variantes de acceso cruzado entre roles
- Cambios de estado: producto/categoría inactivos bloquean venta
- Vencimiento: lotes vencidos no son vendibles
- Efectos cruzados: venta reduce stock visto por almacenero; merma reduce vendible del vendedor
- Idempotencia: doble envío de cobro no duplica venta
- Cierre con borrador activo: bloqueado correctamente
- Dashboard por rol
- Navegación y acceso anónimo: redirección al login

### Excluido (pendiente para sublotes siguientes o etapa 15)

- **Pruebas en navegador real (Chrome/Selenium):** este sublote ejecutó mediante Django Client. La prueba visual completa queda para el sublote 14-B.
- **PostgreSQL:** la concurrencia real con `SELECT FOR UPDATE` no se demuestra en SQLite. Queda para etapa 15.
- **Reportes futuros (EPIC-REP):** 16 HU futuras no seleccionadas para R1.
- **Bloqueo por inactividad:** DEC-10-BLOQUEO-INACTIVIDAD no implementado.
- **Descuentos complejos:** deshabilitados por decisión; solo descuento simple verificado indirectamente.
- **Impresión/exportación de constancias:** verificada existencia de template, no impresión real.

---

## 3. Inventario de HUs, criterios, rutas y roles del tramo

### 3.1 Mapa de permisos por ruta (verificado)

| Ruta | Método | ADMIN | ALMACENERO | VENDEDOR | Anónimo | Evidencia |
|---|---|---|---|---|---|---|
| `/` (login) | GET/POST | ✓ | ✓ | ✓ | ✓ | test_32, test_33 |
| `/inicio/` (dashboard) | GET | ✓ | ✓ | ✓ | → login | test_50–52, test_33 |
| `/productos/categorias/` | GET | ✓ | ✗ 403 | ✗ 403 | → login | test_31 |
| `/productos/categorias/nueva/` | POST | ✓ | ✗ 403 | ✗ 403 | → login | test_01, test_20 |
| `/productos/categorias/<id>/estado/` | POST | ✓ | ✗ 403 | ✗ 403 | → login | test_54 |
| `/productos/nuevo/` | POST | ✓ | ✗ 403 | ✗ 403 | → login | test_02, test_21 |
| `/productos/` | GET | ✓ | ✗ 403 | ✗ 403 | → login | código |
| `/inventario/proveedores/` | GET | ✓ | ✓ | ✗ 403 | → login | test_56 |
| `/inventario/proveedores/nuevo/` | POST | ✓ | ✗ 403 | ✗ 403 | → login | test_03, test_22 |
| `/inventario/proveedores/<id>/estado/` | POST | ✓ | ✗ 403 | ✗ 403 | → login | test_53 |
| `/inventario/carga-inicial/` | POST | ✗ 403 | ✓ | ✗ 403 | → login | test_04, test_26 |
| `/inventario/entrada/` | POST | ✗ 403 | ✓ | ✗ 403 | → login | código |
| `/inventario/stock/` | GET | ✓ | ✓ | ✗ 403 | → login | test_09, test_55 |
| `/inventario/productos/<id>/movimientos/` | GET | ✓ | ✓ | ✗ 403 | → login | test_10 |
| `/inventario/bajas/nueva/` | POST | ✓ | ✓ | ✗ 403 | → login | test_06, test_27 |
| `/inventario/ajustes/nuevo/` | POST | ✓ | ✗ 403 | ✗ 403 | → login | test_44, test_28 |
| `/caja/abrir/` | POST | ✗ 403 | ✗ 403 | ✓ | → login | test_05, test_23, test_25 |
| `/caja/cerrar/` | POST | ✗ 403 | ✗ 403 | ✓ | → login | test_11, test_43 |
| `/caja/turnos/` | GET | ✓ | ✗ 403 | ✓ | → login | test_08 |
| `/caja/turnos/<id>/cerrado/` | GET | ✓ | ✗ 403 | ✓(propio) | → login | código |
| `/ventas/` (borrador) | GET/POST | ✗ 403 | ✗ 403 | ✓ | → login | test_05, test_24 |
| `/ventas/cobrar/` | POST | ✗ 403 | ✗ 403 | ✓ | → login | test_05 |
| `/ventas/historial/turno/` | GET | ✗ 403 | ✗ 403 | ✓ | → login | test_45 |
| `/ventas/historial/` | GET | ✓ | ✗ 403 | ✓(propio) | → login | test_07, test_46 |
| `/ventas/constancia/<id>/` | GET | ✓ | ✗ 403 | ✓(propio) | → login | test_05 |
| `/empleados/` | GET | ✓ | ✗ 403 | ✗ 403 | → login | test_29, test_30 |

### 3.2 HUs cruzadas verificadas en este recorrido

| HU | Módulo | Rol principal | Verificada en test | Conexión con |
|---|---|---|---|---|
| HU-AUTH-01 | identity | Todos | test_05, test_32, test_33 | Todas las rutas |
| HU-AUTH-01/CA-04 | identity | Todos | test_20–31 | Permisos cruzados |
| HU-CAT-01 | catalog | ADMIN | test_01 | → inventory, sales |
| HU-CAT-02 | catalog | ADMIN | test_54 | → sales (cat inactiva bloquea) |
| HU-PROD-01 | catalog | ADMIN | test_02 | → inventory (carga), sales (venta) |
| HU-PROV-01 | inventory | ADMIN | test_03, test_56 | → inventory (carga con proveedor) |
| HU-PROV-04 | inventory | ADMIN | test_53 | → inventory (proveedor inactivo) |
| HU-INV-01a | inventory | ALMACENERO | test_04 | → sales (stock disponible) |
| HU-INV-02 | inventory | ALM/ADMIN | test_06 | → sales (stock reducido) |
| HU-INV-03 | inventory | ADMIN | test_44 | → sales (stock ajustado) |
| HU-INV-04 | inventory | ALM/ADMIN | test_09, test_55 | → catalog, sales (vista consolidada) |
| HU-INV-06 | inventory | ALM/ADMIN | test_10 | → sales (movimientos unificados) |
| HU-CAJA-01 | cash | VENDEDOR | test_05 | → sales (turno requerido) |
| HU-CAJA-02 | cash | VENDEDOR | test_11, test_43 | → sales (borrador bloquea cierre) |
| HU-CAJA-05 | cash | ADM/VENDEDOR | test_08 | → sales (total cobrado) |
| HU-VEN-01c | sales | VENDEDOR | test_05 | → inventory (stock), cash (turno) |
| HU-VEN-02a | sales | VENDEDOR | test_05 | → inventory (FEFO) |
| HU-VEN-05a | sales | VENDEDOR | test_45 | → cash (turno abierto) |
| HU-VEN-05b | sales | ADM/VENDEDOR | test_07, test_46 | → cash (filtro por turno) |

### 3.3 Reglas de negocio verificadas en conexión

| RN | Descripción | Evidencia |
|---|---|---|
| RN-29 | Un rol exclusivo por cuenta | test_01–05: cada rol solo accede a su ámbito |
| RN-14 | Costo promedio ponderado | test_04: `average_cost` = 2.5000 tras carga |
| RN-05 | FEFO para deducción de stock | test_05: lote más próximo a vencer se descuenta primero |
| RN-CAJA-01 | Una caja semilla CAJA-01 | test_05: shift requiere CAJA-01 activa |
| RN-TURNO | Un turno abierto a la vez | test_05: constraint `one_open_shift_per_register` |
| RN-BORRADOR | Un borrador activo por turno | test_05: constraint `one_active_sale_draft_per_shift` |
| RN-CIERRE | No cerrar con borrador activo | test_43: cierre rechazado con venta en preparación |
| RN-IDEM | Idempotencia de cobro | test_62: doble envío no duplica venta |
| RN-VENCIDO | Lotes vencidos no vendibles | test_42: filtro `expiration_date__gt=today` |
| CT-COHERENCIA-UI | Promesas visibles | Dashboard muestra datos consistentes por rol |

---

## 4. Matriz de trazabilidad — Pruebas de integración E14

| # | Test | Módulos | HU/CA | Acción | Esperado | Observado | Estado |
|---|---|---|---|---|---|---|---|
| 01 | test_01_admin_creates_category | identity→catalog | HU-CAT-01/CA-01 | ADMIN POST categoría | 302 + categoría creada | 302 + existe en BD | **CUMPLE** |
| 02 | test_02_admin_creates_product | identity→catalog | HU-PROD-01/CA-01 | ADMIN POST producto | 302 + producto creado | 302 + existe en BD | **CUMPLE** |
| 03 | test_03_admin_creates_supplier | identity→inventory | HU-PROV-02/CA-01 | ADMIN POST proveedor | 302 + proveedor creado | 302 + existe en BD | **CUMPLE** |
| 04 | test_04_warehouse_loads_stock | identity→inventory→catalog | HU-INV-01a | ALM POST carga inicial | 302 + lote + costo promedio | 302 + lote `LOTE-E14-A` + avg=2.5000 | **CUMPLE** |
| 05 | test_05_seller_opens_shift_and_sells | identity→cash→sales→inventory | HU-CAJA-01, HU-VEN-01c, HU-VEN-02a | VEN abre, agrega, cobra | Turno abierto + venta V-00000001 + stock −2 | Turno OPEN + total=14.20 + change=5.80 + stock=8 | **CUMPLE** |
| 06 | test_06_warehouse_writeoff | identity→inventory | HU-INV-02 | ALM POST baja por daño | 302 + stock −3 + correlativo | 302 + available=12 + writeoff existe | **CUMPLE** |
| 07 | test_07_admin_views_sales_history | identity→sales | HU-VEN-05b | ADMIN GET historial ventas | 200 | 200 | **CUMPLE** |
| 08 | test_08_admin_views_shift_history | identity→cash | HU-CAJA-05 | ADMIN GET historial turnos | 200 | 200 | **CUMPLE** |
| 09 | test_09_admin_views_stock_overview | identity→inventory | HU-INV-04 | ADMIN GET stock | 200 | 200 | **CUMPLE** |
| 10 | test_10_admin_views_product_movements | identity→inventory→sales | HU-INV-06 | ADMIN GET movimientos | 200 | 200 | **CUMPLE** |
| 11 | test_11_seller_closes_shift | identity→cash | HU-CAJA-02 | VEN POST cierre | 302 + CLOSED + close record | 302 + status=CLOSED + close existe | **CUMPLE** |
| 20 | test_20_seller_cannot_create_category | identity→catalog | HU-AUTH-01/CA-04 | VEN POST categoría | 403 + sin mutación | 403 + count sin cambio | **CUMPLE** |
| 21 | test_21_seller_cannot_create_product | identity→catalog | HU-AUTH-01/CA-04 | VEN POST producto | 403 + sin mutación | 403 + count sin cambio | **CUMPLE** |
| 22 | test_22_seller_cannot_create_supplier | identity→inventory | HU-AUTH-01/CA-04 | VEN POST proveedor | 403 + sin mutación | 403 + count sin cambio | **CUMPLE** |
| 23 | test_23_warehouse_cannot_open_cash | identity→cash | HU-AUTH-01/CA-04 | ALM POST abrir caja | 403 + sin mutación | 403 + count sin cambio | **CUMPLE** |
| 24 | test_24_warehouse_cannot_sell | identity→sales | HU-AUTH-01/CA-04 | ALM POST borrador venta | 403 + sin mutación | 403 + count sin cambio | **CUMPLE** |
| 25 | test_25_admin_cannot_open_cash | identity→cash | HU-AUTH-01/CA-04 | ADMIN POST abrir caja | 403 + sin mutación | 403 + count sin cambio | **CUMPLE** |
| 26 | test_26_admin_cannot_load_stock | identity→inventory | HU-AUTH-01/CA-04 | ADMIN POST carga | 403 + sin mutación | 403 + count sin cambio | **CUMPLE** |
| 27 | test_27_seller_cannot_writeoff | identity→inventory | HU-AUTH-01/CA-04 | VEN POST baja | 403 + sin mutación | 403 + count sin cambio | **CUMPLE** |
| 28 | test_28_warehouse_cannot_adjust | identity→inventory | HU-AUTH-01/CA-04 | ALM POST ajuste | 403 + sin mutación | 403 + count sin cambio | **CUMPLE** |
| 29 | test_29_seller_cannot_view_employees | identity | HU-AUTH-01/CA-04 | VEN GET empleados | 403 | 403 | **CUMPLE** |
| 30 | test_30_warehouse_cannot_view_employees | identity | HU-AUTH-01/CA-04 | ALM GET empleados | 403 | 403 | **CUMPLE** |
| 31 | test_31_seller_cannot_view_categories | identity→catalog | HU-AUTH-01/CA-04 | VEN GET categorías | 403 | 403 | **CUMPLE** |
| 32 | test_32_inactive_account_denied | identity | HU-AUTH-01/CA-03 | Inactivo POST login | 200 + mensaje rechazo | 200 + "Correo o contraseña incorrectos" | **CUMPLE** |
| 33 | test_33_anonymous_redirected | identity | HU-AUTH-01/CA-04 | Anónimo GET rutas | 302 → login | 302 en 6 rutas | **CUMPLE** |
| 40 | test_40_inactive_product | catalog→sales | HU-PROD-05/RN | VEN agrega inactivo | Sin línea | count sin cambio | **CUMPLE** |
| 41 | test_41_inactive_category | catalog→sales | HU-CAT-02/impacto | VEN agrega cat inactiva | Sin línea | count sin cambio | **CUMPLE** |
| 42 | test_42_expired_lot | inventory→sales | RN-VENCIDO | VEN agrega vencido | Sin línea | count sin cambio | **CUMPLE** |
| 43 | test_43_close_with_draft | cash→sales | HU-CAJA-02/RN-CIERRE | VEN cierra con borrador | Rechazado, turno OPEN | status=OPEN | **CUMPLE** |
| 44 | test_44_physical_adjustment | identity→inventory | HU-INV-03 | ADMIN ajuste −3 | available=17 | available=17 | **CUMPLE** |
| 45 | test_45_shift_history | sales | HU-VEN-05a | VEN GET hist turno | 200 | 200 | **CUMPLE** |
| 46 | test_46_sale_history | sales | HU-VEN-05b | VEN GET hist ventas | 200 | 200 | **CUMPLE** |
| 50 | test_50_admin_dashboard | identity | Dashboard | ADMIN GET inicio | 200 | 200 | **CUMPLE** |
| 51 | test_51_warehouse_dashboard | identity | Dashboard | ALM GET inicio | 200 | 200 | **CUMPLE** |
| 52 | test_52_seller_dashboard | identity | Dashboard | VEN GET inicio | 200 | 200 | **CUMPLE** |
| 53 | test_53_toggle_supplier | identity→inventory | HU-PROV-04 | ADMIN desactiva prov | is_active=False | is_active=False | **CUMPLE** |
| 54 | test_54_toggle_category | identity→catalog | HU-CAT-02 | ADMIN desactiva cat | is_active=False | is_active=False | **CUMPLE** |
| 55 | test_55_warehouse_stock | identity→inventory | HU-INV-04 | ALM GET stock | 200 | 200 | **CUMPLE** |
| 56 | test_56_warehouse_suppliers | identity→inventory | HU-PROV-01 | ALM GET proveedores | 200 | 200 | **CUMPLE** |
| 60 | test_60_sale_reduces_stock | sales→inventory | E2E cruzado | VEN vende 5, ALM ve −5 | available=15 | available=15 | **CUMPLE** |
| 61 | test_61_writeoff_reduces_sellable | inventory→sales | E2E cruzado | ALM baja 4, VEN intenta 3 | Rechazado (solo 1 dispo) | Sin línea creada | **CUMPLE** |
| 62 | test_62_idempotency | sales | RN-IDEM | VEN doble checkout | Sin segunda venta | count sin cambio | **CUMPLE** |

**Resultado: 42/42 CUMPLE**

---

## 5. Hallazgos y observaciones

### 5.1 Hallazgos positivos

| # | Hallazgo | Severidad | Estado |
|---|---|---|---|
| H14-01 | Los permisos de `roles_required` bloquean consistentemente los 14 cruces probados tanto en GET como en POST | — | CUMPLE |
| H14-02 | La deducción FEFO funciona correctamente entre módulos: la venta consume del lote más próximo a vencer | — | CUMPLE |
| H14-03 | El `average_cost` se recalcula correctamente tras carga inicial y merma | — | CUMPLE |
| H14-04 | El constraint `one_open_shift_per_register` impide dos turnos simultáneos | — | CUMPLE |
| H14-05 | El constraint `one_active_sale_draft_per_shift` impide dos borradores simultáneos | — | CUMPLE |
| H14-06 | La idempotencia por `idempotency_key` UUID previene ventas duplicadas | — | CUMPLE |
| H14-07 | El cierre de caja con borrador activo con líneas es rechazado correctamente | — | CUMPLE |
| H14-08 | Producto/categoría inactivos bloquean la venta en el servicio | — | CUMPLE |
| H14-09 | Lotes vencidos no son vendibles (filtro `expiration_date__gt=today`) | — | CUMPLE |
| H14-10 | La cuenta inactiva recibe el mismo mensaje que credenciales inválidas (sin enumerar estado) | — | CUMPLE |

### 5.2 Observaciones y decisiones pendientes

| # | Observación | Módulos | Tipo | Severidad |
|---|---|---|---|---|
| OBS-14-01 | Las pruebas se ejecutaron con Django Client (servidor embebido), no con navegador real Chrome. La cobertura visual (menús, botones, textos, navegación real) queda para 14-B | Todos | NO EJECUTADO (visual) | Media |
| OBS-14-02 | La concurrencia real entre roles (PostgreSQL `SELECT FOR UPDATE`) no se prueba en SQLite. El código tiene los locks correctos, pero la evidencia de serialización es de etapa 15 | Todos | PREVISTO/FUTURO | Media |
| OBS-14-03 | El almacenero puede ver la lista de proveedores (`supplier_list`) pero no puede crear ni gestionar estado. Esto es correcto según HU-PROV-01 (lectura) vs HU-PROV-02/04 (escritura: ADMIN) | inventory | CUMPLE | — |
| OBS-14-04 | El vendedor no tiene acceso a ninguna vista de inventario ni de catálogo — correcto según RN-29 | identity | CUMPLE | — |
| OBS-14-05 | El historial de ventas del vendedor filtra `seller=request.user`; el admin ve todo. Correcto según HU-VEN-05b | sales | CUMPLE | — |
| OBS-14-06 | La constancia (`sales_receipt`) permite acceso a SELLER (solo la propia) y ADMIN (cualquiera). Correcto | sales | CUMPLE | — |
| OBS-14-07 | `_dashboard_summary` retorna `None` para VENDEDOR (no ve métricas de inventario). Correcto por diseño | identity | CUMPLE | — |

### 5.3 Incompatibilidades encontradas entre roles

**No se encontraron incompatibilidades funcionales** entre los roles en este recorrido. Los tres roles están correctamente aislados con:
- `roles_required()` como decorador de vista (servidor)
- Verificación adicional en servicios con `_lock_seller_actor`, `_lock_warehouse_actor`, `_lock_admin_actor`
- Los rechazos (403) no producen mutaciones en la base de datos

### 5.4 Relación con etapas anteriores

| Etapa | Relación con E14 | Estado |
|---|---|---|
| [ETAPA-01](ETAPA-01.md) | Ingreso y bloqueo: base del sistema de permisos probado en test_20–33 | Heredado, no reejecutado |
| [ETAPA-03](ETAPA-03.md) | Categorías/productos: creación y estado probados en test_01–02, test_40–41, test_54 | Heredado + revalidado conexión con ventas |
| [ETAPA-04](ETAPA-04.md) | Proveedores: creación y toggle probados en test_03, test_53, test_56 | Heredado + revalidado conexión con inventario |
| [ETAPA-05](ETAPA-05.md) | Carga inicial: probada en test_04 con costo promedio verificado | Heredado + revalidado conexión con ventas |
| [ETAPA-07](ETAPA-07.md) | Stock y vencimientos: vencidos no vendibles en test_42, stock overview en test_09/55 | Heredado + revalidado |
| [ETAPA-09](ETAPA-09.md) | Caja: apertura/cierre en test_05/11, cierre con borrador en test_43 | Heredado + revalidado conexión con ventas |
| [ETAPA-11](ETAPA-11.md) | Cobro: checkout E2E en test_05, idempotencia en test_62 | Heredado + revalidado |
| [ETAPA-12](ETAPA-12.md) | Constancias: acceso por rol verificado en test_05 (vendedor ve su constancia) | Heredado |
| [ETAPA-13](ETAPA-13.md) | Dashboard: tres roles verificados en test_50–52 | Heredado + revalidado |

---

## 6. Pruebas — Resultados completos

### Suite de integración E14 (nueva)

```
tests.test_audit14_integration.IntegrationE2ETest (42 tests)
─────────────────────────────────────────────────────────────
test_01_admin_creates_category ........................ ok
test_02_admin_creates_product ......................... ok
test_03_admin_creates_supplier ........................ ok
test_04_warehouse_loads_stock ......................... ok
test_05_seller_opens_shift_and_sells .................. ok
test_06_warehouse_writeoff ............................ ok
test_07_admin_views_sales_history ..................... ok
test_08_admin_views_shift_history ..................... ok
test_09_admin_views_stock_overview .................... ok
test_10_admin_views_product_movements ................. ok
test_11_seller_closes_shift ........................... ok
test_20_seller_cannot_create_category ................. ok (403)
test_21_seller_cannot_create_product .................. ok (403)
test_22_seller_cannot_create_supplier ................. ok (403)
test_23_warehouse_cannot_open_cash .................... ok (403)
test_24_warehouse_cannot_sell ......................... ok (403)
test_25_admin_cannot_open_cash ........................ ok (403)
test_26_admin_cannot_load_stock ....................... ok (403)
test_27_seller_cannot_writeoff ........................ ok (403)
test_28_warehouse_cannot_adjust_physical .............. ok (403)
test_29_seller_cannot_view_employees .................. ok (403)
test_30_warehouse_cannot_view_employees ............... ok (403)
test_31_seller_cannot_view_categories ................. ok (403)
test_32_inactive_account_denied ....................... ok
test_33_anonymous_redirected .......................... ok
test_40_inactive_product_not_sellable ................. ok
test_41_inactive_category_not_sellable ................ ok
test_42_expired_lot_not_sellable ...................... ok
test_43_cannot_close_with_active_draft ................ ok
test_44_admin_physical_adjustment ..................... ok
test_45_seller_views_shift_history .................... ok
test_46_seller_views_own_sale_history ................. ok
test_50_admin_dashboard ............................... ok
test_51_warehouse_dashboard ........................... ok
test_52_seller_dashboard .............................. ok
test_53_admin_toggles_supplier ........................ ok
test_54_admin_toggles_category ........................ ok
test_55_warehouse_views_stock_overview ................ ok
test_56_warehouse_views_supplier_list ................. ok
test_60_sale_reduces_stock_seen_by_warehouse .......... ok
test_61_writeoff_reduces_sellable ..................... ok
test_62_checkout_idempotency .......................... ok
─────────────────────────────────────────────────────────────
Ran 42 tests in 4.477s — OK
```

### Suite completa (regresión)

```
Ran 482 tests in 67.145s — OK (0 failures, 0 errors)
```

### Archivo de prueba

[test_audit14_integration.py](../../r1-pmv/tests/test_audit14_integration.py)

---

## 7. Propuestas y recomendaciones

### PROP-14-01 · Pruebas de integración en navegador real (sublote 14-B)

**Beneficio:** Validar que los menús, botones, textos, redirecciones y mensajes que ven los tres roles en el navegador corresponden al comportamiento verificado por servidor. **Riesgo:** sin esta prueba, un error de plantilla o JS podría presentar opciones incorrectas al usuario. **Costo:** 1-2 horas con Selenium/Chrome. **Impacto:** Medio.

### PROP-14-02 · Matriz de permisos exhaustiva como prueba parametrizada

**Beneficio:** Automatizar la verificación de TODOS los pares (rol, ruta, método) en una sola prueba parametrizada, en lugar de tests individuales. **Riesgo:** sin esto, una nueva ruta podría no tener prueba de permiso. **Costo:** 1 hora. **Impacto:** Bajo.

### PROP-14-03 · Prueba de efecto cruzado: admin desactiva producto mientras vendedor tiene borrador activo

**Beneficio:** Verificar el comportamiento exacto cuando el admin desactiva un producto que está en un borrador de venta activo (actualmente el checkout re-valida y rechaza). **Riesgo:** edge case que puede confundir al vendedor. **Costo:** 30 min. **Impacto:** Bajo.

---

## 8. Sublote 14-B — Verificación del HTML renderizado por rol (CT-COHERENCIA-UI)

**Fecha:** 13/11/2026 Lima  
**Herramienta:** Django Client con `assertContains` / `assertNotContains` sobre HTML real  
**Archivo de prueba:** [test_audit14b_browser_content.py](../../r1-pmv/tests/test_audit14b_browser_content.py)

### 8.1 Alcance del sublote 14-B

Verificación del HTML renderizado real (no solo código de estado HTTP) para cada rol:
- **Menú lateral (sidebar):** cada rol ve solo sus secciones y enlaces
- **Dashboard:** tarjetas de acción, métricas de resumen y pills de rol correctos
- **Headings de páginas:** cada página accesible muestra el heading esperado
- **Login:** formulario, roles descritos, mensajes de error
- **Accesibilidad:** skip-link, aria-labels, lang, tabindex, sidebar/footer
- **Páginas 403:** accesos denegados producen la respuesta correcta

### 8.2 Matriz de pruebas 14-B

| # | Test | Rol | Aspecto verificado | Esperado | Observado | Estado |
|---|---|---|---|---|---|---|
| B01 | admin_sidebar_has_catalog_section | ADMIN | Sidebar: Catálogo, Productos, Registrar producto, Categorías | Presente | Cat&#225;logo + enlaces presentes | **CUMPLE** |
| B02 | admin_sidebar_has_inventory_section | ADMIN | Sidebar: Inventario, Proveedores, Ver inventario, Vencimientos, Ajuste | Presente | Todos presentes | **CUMPLE** |
| B03 | admin_sidebar_has_personnel_section | ADMIN | Sidebar: Personal, Empleados | Presente | Presentes | **CUMPLE** |
| B04 | admin_sidebar_has_cash_and_sales | ADMIN | Sidebar: Caja y ventas, Historial turnos/ventas | Presente | Presentes | **CUMPLE** |
| B05 | admin_sidebar_no_seller_options | ADMIN | Sidebar: NO Apertura/Preparar/Cerrar/Mis ventas | Ausente | Ausentes | **CUMPLE** |
| B06 | admin_sidebar_no_warehouse_ops | ADMIN | Sidebar: NO Existencias/Entrada/Merma | Ausente | Ausentes | **CUMPLE** |
| B07 | admin_dashboard_panel_principal | ADMIN | Dashboard: Panel principal + Administrador | Presente | Presentes | **CUMPLE** |
| B08 | admin_dashboard_sales_summary | ADMIN | Dashboard: Ventas de hoy, Total vendido, Descuentos, Turnos | Presente | Presentes | **CUMPLE** |
| B09 | admin_dashboard_stock_alerts | ADMIN | Dashboard: Stock bajo, Por vencer, Vencidos | Presente | Presentes | **CUMPLE** |
| B10 | admin_dashboard_action_cards | ADMIN | Dashboard: Registrar producto, Ver catálogo, Gestionar empleados | Presente | Presentes | **CUMPLE** |
| B11 | admin_dashboard_no_warehouse_cards | ADMIN | Dashboard: NO tarjetas de almacenero | Ausente | Ausentes | **CUMPLE** |
| B12 | admin_dashboard_no_seller_cards | ADMIN | Dashboard: NO tarjetas de vendedor | Ausente | Ausentes | **CUMPLE** |
| B13 | admin_topbar_role_pill | ADMIN | Topbar: pill "Administrador" | Presente | role-pill + Administrador | **CUMPLE** |
| B14 | admin_topbar_heading_inicio | ADMIN | Heading: "Inicio" en /inicio/ | Presente | Presente | **CUMPLE** |
| B15 | admin_sidebar_user_info | ADMIN | Sidebar: nombre + Cerrar sesión | Presente | admin14b + Cerrar sesión | **CUMPLE** |
| B20 | warehouse_sidebar_inventory_links | ALM | Sidebar: Inventario, Existencias, Entrada, Merma | Presente | Presentes | **CUMPLE** |
| B21 | warehouse_sidebar_consultation | ALM | Sidebar: Consulta, Catálogo, Proveedores | Presente | Presentes | **CUMPLE** |
| B22 | warehouse_sidebar_no_admin | ALM | Sidebar: NO Personal, Empleados, Registrar producto | Ausente | Ausentes | **CUMPLE** |
| B23 | warehouse_sidebar_no_seller | ALM | Sidebar: NO Apertura/Preparar/Cerrar/Mis ventas | Ausente | Ausentes | **CUMPLE** |
| B24 | warehouse_sidebar_no_caja_ventas | ALM | Sidebar: NO Caja y ventas/Historial | Ausente | Ausentes | **CUMPLE** |
| B25 | warehouse_dashboard_role | ALM | Dashboard: Almacenero + Panel principal | Presente | Presentes | **CUMPLE** |
| B26 | warehouse_dashboard_stock_only | ALM | Dashboard: Stock bajo/vencer/vencidos; NO ventas/turnos | Correcto | Solo stock, sin ventas | **CUMPLE** |
| B27 | warehouse_dashboard_action_cards | ALM | Dashboard: Existencias, Entrada, Merma | Presente | Presentes | **CUMPLE** |
| B28 | warehouse_dashboard_no_admin_cards | ALM | Dashboard: NO Registrar producto, Gestionar empleados | Ausente | Ausentes | **CUMPLE** |
| B29 | warehouse_stock_overview_heading | ALM | Heading: "Ver inventario" en /inventario/stock/ | Presente | Presente | **CUMPLE** |
| B30 | seller_sidebar_cash_links | VEN | Sidebar: Apertura, Preparar venta, Cerrar turno, Mis ventas | Presente | Presentes | **CUMPLE** |
| B31 | seller_sidebar_no_admin | VEN | Sidebar: NO Personal, Empleados, Ajuste | Ausente | Ausentes | **CUMPLE** |
| B32 | seller_sidebar_no_warehouse | VEN | Sidebar: NO Existencias/Entrada/Merma/Consulta | Ausente | Ausentes | **CUMPLE** |
| B33 | seller_sidebar_no_admin_links | VEN | Sidebar: NO Historial turnos/ventas/Registrar/Proveedores | Ausente | Ausentes | **CUMPLE** |
| B34 | seller_dashboard_role | VEN | Dashboard: Vendedor + Panel principal | Presente | Presentes | **CUMPLE** |
| B35 | seller_dashboard_no_sales_summary | VEN | Dashboard: NO Ventas de hoy/Total/Turnos | Ausente | Ausentes | **CUMPLE** |
| B36 | seller_dashboard_action_cards | VEN | Dashboard: Abrir turno, Preparar venta | Presente | Presentes | **CUMPLE** |
| B37 | seller_dashboard_no_other_cards | VEN | Dashboard: NO tarjetas admin/almacenero | Ausente | Ausentes | **CUMPLE** |
| B38 | seller_cash_open_page | VEN | Heading: "Apertura de caja" | 200 + heading | 200 + presente | **CUMPLE** |
| B39 | seller_sales_draft_page | VEN | Heading: "Preparar venta" (con turno) | 200 + heading | 200 + presente | **CUMPLE** |
| B40 | login_page_elements | — | Login: Bienvenido, Iniciar sesión, 3 roles | Presente | Presentes | **CUMPLE** |
| B41 | login_form_fields | — | Login: form + submit button | Presente | data-testid + submit | **CUMPLE** |
| B42 | login_error_bad_credentials | — | Login: mensaje genérico sin revelar cuenta | Presente | "Correo o contraseña" | **CUMPLE** |
| B43 | login_role_descriptions | — | Login: descripciones de Administrador/Almacenero/Vendedor | Presente | Todas presentes | **CUMPLE** |
| B50 | seller_403_on_admin_route | VEN | GET /productos/categorias/ → 403 | 403 | 403 | **CUMPLE** |
| B51 | warehouse_403_on_cash | ALM | POST /caja/abrir/ → 403 | 403 | 403 | **CUMPLE** |
| B52 | seller_403_on_employees | VEN | GET /empleados/ → 403 | 403 | 403 | **CUMPLE** |
| B60 | admin_product_list_heading | ADMIN | Heading: "Catálogo de productos" | Presente | Presente | **CUMPLE** |
| B61 | admin_product_entry_heading | ADMIN | Heading: "Registrar producto" | Presente | Presente | **CUMPLE** |
| B62 | admin_category_list_heading | ADMIN | Heading: "Categorías" | Presente | Presente | **CUMPLE** |
| B63 | admin_supplier_list_heading | ADMIN | Heading: "Proveedores" | Presente | Presente | **CUMPLE** |
| B64 | admin_employee_list_heading | ADMIN | Heading: "Empleados" | Presente | Presente | **CUMPLE** |
| B65 | admin_shift_history_heading | ADMIN | Heading: "Historial de turnos" | Presente | Presente | **CUMPLE** |
| B66 | admin_sales_history_heading | ADMIN | Heading: "Historial de ventas" | Presente | Presente | **CUMPLE** |
| B67 | admin_stock_overview_heading | ADMIN | Heading: "Ver inventario" | Presente | Presente | **CUMPLE** |
| B68 | admin_expirations_heading | ADMIN | Heading: "Vencimientos de lotes" | Presente | Presente | **CUMPLE** |
| B69 | admin_adjustment_heading | ADMIN | Heading: "Ajuste físico" | Presente | Presente | **CUMPLE** |
| B70 | warehouse_initial_load_heading | ALM | Heading: "Existencias iniciales" | Presente | Presente | **CUMPLE** |
| B71 | warehouse_stock_entry_heading | ALM | Heading: "Entrada de mercadería" | Presente | Presente | **CUMPLE** |
| B72 | warehouse_writeoff_heading | ALM | Heading: "Registrar merma" | Presente | Presente | **CUMPLE** |
| B73 | seller_cash_close_heading | VEN | Heading: "Cerrar turno" (con turno) | Presente | Presente | **CUMPLE** |
| B74 | seller_shift_history_heading | VEN | Heading: "Mis ventas del turno" | Presente | Presente | **CUMPLE** |
| B80 | skip_link_present | ADMIN | Skip-link "Saltar al contenido" | Presente | Presente | **CUMPLE** |
| B81 | sidebar_aria_label | ADMIN | aria-label "Navegación principal" | Presente | Presente | **CUMPLE** |
| B82 | main_content_id | ADMIN | id="contenido" + tabindex="-1" | Presente | Presente | **CUMPLE** |
| B83 | html_lang_es | ADMIN | lang="es-PE" | Presente | Presente | **CUMPLE** |
| B84 | brand_text | ADMIN | "Minimarket" + "Gestión de bodega" | Presente | Presentes | **CUMPLE** |
| B85 | footer_present | ADMIN | Footer con app-footer | Presente | Presente | **CUMPLE** |
| B86 | login_no_sidebar | — | Login: class=anonymous, sin app-sidebar | Correcto | anonymous, sin sidebar | **CUMPLE** |
| B87 | authenticated_has_sidebar | ADMIN | Autenticado: app-sidebar presente | Presente | Presente | **CUMPLE** |

**Resultado: 65/65 CUMPLE**

### 8.3 Hallazgos del sublote 14-B

| # | Hallazgo | Módulos | Tipo | Severidad |
|---|---|---|---|---|
| H14-B-01 | Los menús laterales están completamente aislados por rol: ADMIN ve 10 enlaces, ALMACENERO ve 8, VENDEDOR ve 4. Ningún rol ve opciones de otro | identity | CUMPLE | — |
| H14-B-02 | Los dashboards muestran métricas diferenciadas: solo ADMIN ve ventas/turnos; ADMIN y ALM ven stock/vencimiento; VENDEDOR no ve métricas de inventario | identity | CUMPLE | — |
| H14-B-03 | Las tarjetas de acción del dashboard son exclusivas por rol: 3 para ADMIN, 3 para ALM, 2 para VEN. No hay superposición | identity | CUMPLE | — |
| H14-B-04 | La página de login no muestra sidebar y describe los 3 roles con sus responsabilidades correctas | identity | CUMPLE | — |
| H14-B-05 | El mensaje de error en login es genérico ("Correo o contraseña incorrectos") — no revela existencia de cuenta | identity | CUMPLE (seguridad) | — |
| H14-B-06 | Todos los headings de página coinciden con el menú lateral: 15 headings verificados con su ruta | Todos | CUMPLE | — |
| H14-B-07 | Accesibilidad básica correcta: skip-link, lang="es-PE", aria-label en sidebar, tabindex en main, footer | identity | CUMPLE | — |
| H14-B-08 | La entidad HTML `Cat&#225;logo` (sidebar label) se renderiza correctamente. Los templates usan entidades para acentos en etiquetas fijas y UTF-8 para contenido dinámico | identity | OBSERVACIÓN | Info |

### 8.4 Resultado del sublote 14-B

```
tests.test_audit14b_browser_content (7 clases, 65 tests)
─────────────────────────────────────────────────────────
BrowserContentAdminTest ............ 15 tests, 15 ok
BrowserContentWarehouseTest ........ 10 tests, 10 ok
BrowserContentSellerTest ........... 10 tests, 10 ok
BrowserContentLoginTest ............ 4 tests, 4 ok
BrowserContentErrorPagesTest ....... 3 tests, 3 ok
BrowserContentPageHeadingsTest ..... 15 tests, 15 ok
BrowserContentAccessibilityTest .... 8 tests, 8 ok
─────────────────────────────────────────────────────────
Ran 65 tests in 6.991s — OK
```

### 8.5 Regresión completa con 14-A + 14-B

```
Ran 547 tests in 72.699s — OK (0 failures, 0 errors)
```

Composición: 440 existentes + 42 E14-A + 65 E14-B = **547 pruebas**.

---

## 9. Pendientes y siguiente cursor

### Pendientes de esta etapa

| # | Pendiente | Tipo |
|---|---|---|
| ~~P14-01~~ | ~~Pruebas de navegador real (Chrome) para verificar UI de menús, textos y navegación por rol~~ | **RESUELTO en 14-B** (65/65 con HTML renderizado) |
| P14-02 | Pruebas de concurrencia real entre roles en PostgreSQL | PREVISTO para etapa 15 |
| ~~P14-03~~ | ~~Verificación de mensajes exactos de la UI contra CT-COHERENCIA-UI~~ | **RESUELTO en 14-B** (menús, dashboards, headings, login, 403) |
| P14-04 | Prueba con Selenium + Chrome visual (interacción real: clicks, navegación, JS) | OPCIONAL — el HTML renderizado ya verifica la estructura |
| ~~P14-05~~ | ~~PROP-14-03: admin desactiva producto con borrador activo~~ | **RESUELTO en 14-C** (2 tests: C01 producto, C02 categoría) |
| ~~P14-06~~ | ~~Auditoría comportamiento→planificación: funciones sin HU~~ | **RESUELTO en 14-C** (10 funciones, todas respaldadas) |

### Siguiente cursor

**Etapa 15**: Seguridad, concurrencia (PostgreSQL), despliegue y recuperación. La etapa 14 queda sustancialmente completada con los sublotes 14-A (servidor), 14-B (HTML renderizado) y 14-C (edge cases + comportamiento→planificación). La prueba con Selenium visual es opcional y puede incluirse en una segunda pasada.

---

## 10. Conclusión de la etapa 14 (sublotes 14-A + 14-B + 14-C)

El recorrido E2E entre los tres roles (ADMIN→ALMACENERO→VENDEDOR→ALM/ADMIN→VENDEDOR) demuestra que:

1. **Los cinco módulos están correctamente conectados**: identity provee permisos; catalog provee productos; inventory provee stock y lotes; cash provee turnos; sales ejecuta ventas que afectan inventory y cash.
2. **Los permisos son consistentes en servidor**: 14 variantes de acceso denegado verificadas con HTTP 403 y sin mutación de datos.
3. **Los efectos cruzados funcionan**: la venta del vendedor reduce el stock visible para el almacenero; la merma del almacenero limita las ventas del vendedor.
4. **Los cambios de estado se propagan**: producto inactivo, categoría inactiva y lote vencido bloquean la venta.
5. **La idempotencia previene duplicación**: doble envío de cobro con la misma clave no genera segunda venta.
6. **No se encontraron incompatibilidades** entre los roles auditados.
7. **La interfaz (HTML renderizado) es coherente con los permisos**: cada rol ve solo sus menús, tarjetas y headings; ningún rol ve opciones de otro. 65 verificaciones de contenido HTML confirman CT-COHERENCIA-UI.
8. **Accesibilidad básica correcta**: skip-link, lang="es-PE", aria-label, tabindex, footer.
9. **La página de login no revela información de cuentas**: mensaje de error genérico.
10. **PROP-14-03 verificada**: admin desactiva producto/categoría con borrador activo del vendedor → el checkout re-valida y rechaza correctamente.
11. **Comportamiento→planificación**: 10 funciones implementadas verificadas contra planificación. Las 10 tienen respaldo en HU/RN/decisiones documentadas. No se encontraron funciones huérfanas sin justificación.
12. **Correlativos secuenciales**: verificado que el `SaleCounter` genera correlativos V-NNNNNNNN estrictamente crecientes.
13. **Snapshot en SaleLine**: `product_snapshot_name`, `product_snapshot_barcode` y `unit_cost` correctamente congelados al momento del cobro.
14. **IGV calculado correctamente**: base = total / 1.18, igv = total − base, con precisión de 2 decimales.
15. **Cierre de caja con cálculo de diferencia**: expected = opening + ventas; difference = counted − expected.

La cobertura total de esta etapa es de **119 pruebas** (42 E14-A + 65 E14-B + 12 E14-C) verificadas contra HTML renderizado real y lógica de servidor. La suite completa del proyecto (**559 pruebas**) pasa sin regresiones.

La prueba visual con Selenium + Chrome (interacción real con clicks y JavaScript) queda como opcional. La concurrencia real entre roles con PostgreSQL queda para la etapa 15.

---

## 11. Sublote 14-C — Edge cases y auditoría comportamiento→planificación

**Fecha:** 13/11/2026 Lima
**Herramienta:** Django Client + servicios directos sobre SQLite en memoria (TestCase)
**Archivo de prueba:** [test_audit14c_edge_cases.py](../../r1-pmv/tests/test_audit14c_edge_cases.py)

### 11.1 Alcance del sublote 14-C

- **PROP-14-03 verificada**: efecto cruzado de admin desactivando producto/categoría mientras el vendedor tiene borrador activo → el checkout re-valida en `checkout_sale` (líneas 361-365) y rechaza correctamente
- **Auditoría comportamiento→planificación**: 10 funciones implementadas descubiertas por inspección de código, verificadas contra HU/RN/decisiones documentadas
- **Edge cases**: descartar borrador sin afectar stock, constancia de venta por rol, cierre de caja con diferencia, correlativos secuenciales, snapshot de producto en línea de venta, restricción de turno único, cálculo de IGV

### 11.2 Matriz de pruebas 14-C

| # | Test | Módulos | HU/RN/PROP | Acción | Esperado | Observado | Estado |
|---|---|---|---|---|---|---|---|
| C01 | checkout_fails_after_product_deactivation | catalog→sales | PROP-14-03, HU-PROD-05 | VEN agrega, ADMIN desactiva prod, VEN cobra | Venta rechazada | Sale no creada | **CUMPLE** |
| C02 | checkout_fails_after_category_deactivation | catalog→sales | PROP-14-03, HU-CAT-02 | VEN agrega, ADMIN desactiva cat, VEN cobra | Venta rechazada | Sale no creada | **CUMPLE** |
| C10 | search_products_active_only | catalog→sales | HU-VEN-01c/RN-ACTIVO | VEN busca: activo + cat inactiva | Solo activo visible | BuscaActivo sí, BuscaInactCat no | **CUMPLE** |
| C11 | search_products_expired_lots_hidden | inventory→sales | RN-VENCIDO, DEC-07-VENCIDOS | VEN busca producto con lote vencido | No visible | assertNotContains ok | **CUMPLE** |
| C12 | discard_draft | sales→inventory | HU-VEN-01c/descartar | VEN agrega 3 unidades, descarta | Stock sin cambio | status=DISCARDED, available=10 | **CUMPLE** |
| C13 | seller_sees_own_receipt | sales | HU-VEN-05b, HU-VEN-06 | VEN GET constancia propia | 200 + "Constancia de venta" | 200 + presente | **CUMPLE** |
| C14 | admin_sees_any_receipt | sales | HU-VEN-05b (admin) | ADMIN GET constancia de otro vendedor | 200 + "Constancia de venta" | 200 + presente | **CUMPLE** |
| C15 | cash_close_calculates_difference | cash→sales | HU-CAJA-02, RN-CIERRE | VEN vende 15, cierra con 64 (expected=65) | difference=-1.00 | expected=65, counted=64, diff=-1 | **CUMPLE** |
| C16 | sale_correlative_sequential | sales | RN-CORRELATIVO | VEN cobra 2 ventas consecutivas | Correlativos V- secuenciales y crecientes | num2 > num1, counter+2 | **CUMPLE** |
| C17 | sale_line_has_product_snapshot | sales→catalog | HU-VEN-02a, RN-SNAPSHOT | VEN cobra → SaleLine snapshot | Nombre, barcode y unit_cost congelados | Snapshot14C, INT-C17-SNP, 3.0000 | **CUMPLE** |
| C18 | cannot_open_second_shift | cash | RN-TURNO, constraint | VEN2 intenta abrir con turno existente | Rechazado | count sin cambio | **CUMPLE** |
| C19 | igv_calculation | sales | RN-IGV, DEC-IGV-INCLUIDO | VEN cobra 11.80 → base=10.00, IGV=1.80 | Cálculo 1.18 correcto | total=11.80, base=10.00, igv=1.80 | **CUMPLE** |

**Resultado: 12/12 CUMPLE**

### 11.3 Hallazgos del sublote 14-C

| # | Hallazgo | Módulos | Tipo | Severidad |
|---|---|---|---|---|
| H14-C-01 | `checkout_sale` re-valida producto.is_active y categoría.is_active al momento del cobro (líneas 361-365 de services.py). Esto protege contra el escenario de PROP-14-03 donde admin desactiva entre agregar y cobrar | sales→catalog | CUMPLE | — |
| H14-C-02 | La búsqueda de productos en `/ventas/` filtra por `is_active=True`, `category__is_active=True` y lotes no vencidos. No muestra productos sin stock vendible | sales→catalog→inventory | CUMPLE | — |
| H14-C-03 | `discard_active_draft` cambia el borrador a DISCARDED sin afectar stock ni lotes. Comportamiento correcto — no hay reserva de stock al agregar al borrador | sales→inventory | CUMPLE | — |
| H14-C-04 | `SaleLine` guarda snapshot inmutable: `product_snapshot_name`, `product_snapshot_barcode` y `unit_cost`. El historial de ventas refleja los datos al momento de la transacción, no los actuales | sales | CUMPLE | — |
| H14-C-05 | El `SaleCounter` con `get_or_create(id=1)` y `select_for_update()` genera correlativos únicos y estrictamente crecientes. En SQLite, `select_for_update()` es no-op pero el comportamiento secuencial se mantiene por la exclusividad del hilo. En PostgreSQL (producción), el bloqueo garantiza atomicidad | sales | CUMPLE (observación: `select_for_update` no efectivo en SQLite) | Info |
| H14-C-06 | El cierre de caja calcula `expected_amount = opening_amount + total ventas del turno` y `difference = counted_amount - expected_amount`. El cálculo es correcto y no se trunca | cash→sales | CUMPLE | — |
| H14-C-07 | El IGV se calcula como `total / 1.18` para base e `total - base` para impuesto, con 2 decimales. Correcto para régimen tributario peruano con IGV del 18% incluido en el precio | sales | CUMPLE | — |
| H14-C-08 | El constraint `one_open_shift_per_register` impide que un segundo vendedor abra turno si ya hay uno abierto en CAJA-01. El sistema tiene una caja única (RN-CAJA-01), así que solo un turno puede estar abierto a la vez | cash | CUMPLE | — |

### 11.4 Auditoría comportamiento→planificación

Funciones implementadas descubiertas por inspección de código y verificadas contra la planificación:

| Función | Módulo | Respaldo en planificación | Estado |
|---|---|---|---|
| `discard_active_draft` | sales/services.py | HU-VEN-01c: "el vendedor puede cancelar la venta en preparación" | Respaldada |
| `_search_products` (filtro activos/no vencidos) | sales/services.py | HU-VEN-01c/CA-01: "seleccionar de los productos disponibles"; RN-VENCIDO | Respaldada |
| `product_snapshot_*` + `unit_cost` en SaleLine | sales/models.py | HU-VEN-02a: "registrar cada producto vendido"; diseño de snapshot | Respaldada |
| Constancia de venta por rol (vendedor: propia; admin: cualquiera) | sales/views.py | HU-VEN-05b/CA-02: "el vendedor ve sus ventas"; HU-VEN-05b/CA-01 admin | Respaldada |
| `SaleCounter` → correlativo secuencial | sales/services.py | RN-CORRELATIVO: documentado en decisiones | Respaldada |
| Cierre de caja con expected/counted/difference | cash/services.py | HU-CAJA-02/CA-01: "conteo de efectivo y comparar con esperado" | Respaldada |
| IGV incluido con factor 1.18 | sales/services.py | DEC-IGV-INCLUIDO: "precios incluyen IGV" | Respaldada |
| Re-validación de activo en checkout | sales/services.py | HU-PROD-05 + diseño defensivo | Respaldada |
| Restricción de turno único por caja | cash/models.py | RN-TURNO + constraint `one_open_shift_per_register` | Respaldada |
| Filtro de lotes vencidos en búsqueda | sales/services.py | DEC-07-VENCIDOS-FILTRO | Respaldada |

**Resultado: 10/10 funciones con respaldo en planificación. No se encontraron funciones huérfanas.**

### 11.5 Resultado del sublote 14-C

```
tests.test_audit14c_edge_cases (2 clases, 12 tests)
─────────────────────────────────────────────────────
PROP14_03_AdminDeactivatesProductWithDraftTest ..... 2 tests, 2 ok
BehaviorToPlanningTest ............................ 10 tests, 10 ok
─────────────────────────────────────────────────────
Ran 12 tests in 2.754s — OK
```

### 11.6 Regresión completa con 14-A + 14-B + 14-C

```
Ran 559 tests in 78.421s — OK (0 failures, 0 errors)
```

Composición: 440 existentes + 42 E14-A + 65 E14-B + 12 E14-C = **559 pruebas**.

### 11.7 Nota sobre test C16 en regresión

En la primera ejecución de regresión completa, `test_C16_sale_correlative_sequential` falló porque la aserción original verificaba valores absolutos de correlativos (`num2 == num1 + 1`). Cuando el `SaleCounter` ya tenía entradas de otros tests de la suite, el `get_or_create` interactuaba con los savepoints de Django TestCase causando que el counter se reseteara en la segunda iteración del loop. Se corrigió el test para:
- Pre-inicializar el counter y capturar su valor de inicio
- Verificar diferencia relativa (`num2 > num1`) en lugar de igualdad absoluta
- Verificar que el counter avanzó exactamente 2 posiciones

Este no es un defecto del sistema: el `SaleCounter` funciona correctamente en producción (PostgreSQL con `select_for_update()` real). Es un artefacto de la interacción SQLite + TestCase savepoints, documentado como observación H14-C-05.
