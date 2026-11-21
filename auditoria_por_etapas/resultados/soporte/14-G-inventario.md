# Inventario 14-G · recepción propia

Primera pasada, inicio 13/11/2026 Lima. Cursor de entrada14-G-RECEPCIONES-01.08 SHA256 `8d4a7cbede73eac5b09524363e35d4780dc91d8e25ba6fa8f62de32a66c9984c`; build190 `7630c859296fd71dd4607133a461165e1b2d012d5679190652c5e0522bf4fa93`. [Snapshot](../evidencias/14-G-20261113/producto-antes.zip). Producto seleccionado: HU-INV-01b, dos CA; DOC-03AI-01, cuatro criterios. INV-04/CA-02 es dependencia de consulta. Los demás módulos conservan su evidencia anterior.

## Contrato y clasificación inicial

| ID de08 | Acción esperada | Estado inicial y evidencia nueva |
|---|---|---|
| HU-INV-01b/CA-01 |Entrada propia, promedio físico y reintento|INCUMPLE:20/4.5000 correcto, pero redirige a carga y UUID ignorado|
| HU-INV-01b/CA-02 |Precisión4/presentación2, costo histórico intacto|PARCIAL:Chrome observa4.50; cálculo y salidas revalidados14-E/F, no heredarlos como prueba14-G|
| DOC-03AI-01/C-01 |UUID, R-00000001, autor, recepción/lotes/costo atómicos|INCUMPLE:sin modelo/constancia propios|
| DOC-03AI-01/C-02 |Misma clave/actor/contenido recupera confirmación; cambio rechaza|INCUMPLE:reenvío igual da error de lote; misma clave con loteD/cantidad11 vuelve a ingresar|
| DOC-03AI-01/C-03 |Otro ingreso real del loteC, origen propio; carrera una confirmación|INCUMPLE:segunda entregaC5@8 rechazada; carreras NO EJECUTADAS|
| DOC-03AI-01/C-04 |Inválido no consume clave ni produce efectos parciales|PARCIAL:validaciones anteriores existen; nueva comprobación postwrite pendiente|
| HU-INV-04/CA-02, dependencia |Referencia/responsable/proveedor de la recepción|INCUMPLE:consulta de entrada sin recepción propia y datos maestros variables|

RN-01 vincula cada entrada a lotes; RN-03 exige vencimiento posterior al día de Lima; RN-14 define promedio físico HALF_UP4; RN-19 ordena FEFO por vencimiento/ingreso/ID; RN-29 limita alta a ALMACENERO y consulta a ADMIN/ALMACENERO. DEC-05-LOTE-ESPACIOS normaliza número. DOC-03AB permite entrada directa; solicitudes y recepción multiproducto siguen futuras. CT-ROLLBACK exige rechazo sin mutación y prueba posterior a escritura. CT-COHERENCIA-UI exige que el éxito y la constancia correspondan al evento real.

## Rutas, acciones y mensajes

| Ruta/pantalla | Rol | Elementos y respaldo | Tratamiento |
|---|---|---|---|
| /inventario/entrada/ GET |ALMACENERO|«Registrar entrada de mercadería por lotes», «Producto con carga inicial previa», «Proveedor (opcional)», filas de lote, «Confirmar entrada», «Cancelar», «Ver inventario»; INV01b|Inventariar controles porJSON de navegador; producto/categoría/proveedor activos al confirmar|
| /inventario/entrada/ POST |ALMACENERO|«Entrada de lotes registrada… Costo promedio actualizado», validaciones de lote/costo/cantidad/fecha y estados; RN03/14/29|Éxito exige commit; clave oculta no debe omitirse ni regenerarse al corregir|
| /inventario/cargas/{UUID}/ |ADMIN/ALMACENERO|Carga inicial y tabla de entradas posteriores, cantidad/costo/autor/proveedor actuales; INV01a/DOC03AI|Referencia técnica heredada no prueba recepción; nuevos eventos necesitan su constancia|
| /inventario/productos/{UUID}/movimientos/ |ADMIN/ALMACENERO|«Entrada de mercadería», lote, cantidad, autor; INV04/CA02|Origen propio y fotografía por evento; no ampliar a saldo/filtros/paginación en este corte|
| /inventario/stock/ |ADMIN/ALMACENERO|Físico/vigente, costo y enlace movimientos; RN03/14|Efectos antes/después y permisos; mantener existencia vencida separada de vendible|
| Constancia de recepción, ruta nueva propuesta |ADMIN/ALMACENERO|R-########, producto/código, autor/proveedor o ausencia, instante, cantidad original/costo/vencimiento; DOC03AI|Implementación técnica cubierta por contrato aceptado, no nuevo alcance comercial|

ADMIN y VENDEDOR no registran recepción; VENDEDOR tampoco consulta costos/constancia. Cuenta revocada o estado inválido debe rechazarse por servidor. La UI no reemplaza permisos. Lecturas no mutan datos.

## Campos y salidas

| Campo/salida | Inicial/tipo/límite | Normalización, validación y persistencia |
|---|---|---|
| Producto |Vacío, obligatorio, UUID seleccionado|Activo/categoría activa, con carga previa; revalidación servidor|
| Proveedor |Sin proveedor, opcional, UUID|Activo si elegido. Ausencia declarada distinta de historia desconocida|
| Lote |Vacío, obligatorio, texto64|trim y mayúsculas actuales; NUL rechazado; repetición dentro de entrada rechazada; no confundir con reintento|
| Cantidad |Vacío, entero1..999999|DígitosASCII; no fracción/bool; cantidad original inmutable en constancia|
| Costo unitario |Vacío, decimal0.0001..9999999.9999,4decimales|Sin notación científica/no finitos; almacenamiento4, lectura monetaria2 o4 declarada|
| Vencimiento |Vacío, fecha obligatoria|Posterior a hoyLima y hasta20años. Lote comercial igual con otra fecha requiere rechazo|
| Clave de recepción |UUID oculta nueva por formulario, propuesta de implementación|Obligatoria enPOST; misma clave tras error; huella canónica independiente de ordenHTML|
| Referencia |R-00000001..R-99999999, servidor|Global, única, sin reinicio; agotamiento rechaza antes de mutar|
| Autor/instante |Sesión/reloj de servidor|No aceptarlos del cliente. Conservar fotografía histórica|
| Cantidad recibida/costo/importe |Derivados del ingreso confirmado|No usar capacidad mutable del lote como cantidad histórica|
| Promedio después de recepción |Calculado físico, HALF_UP4, visible2|10@3 +10@6=20@4.5000; +5@8=25@5.2000|

Los textos literales/controles completos y estados recorridos constan en los JSON. Los límites completos del formulario tienen antecedentes05/06, no se declaran revalidados por lectura. El cursor exacto añade variantes de UUID, estados, vencimiento, rollback, roles y consulta tras modificar maestros.

## Dependencias, tareas y decisiones

[Etapa05](../ETAPA-05.md), [Etapa06](../ETAPA-06.md), [Etapa08](../ETAPA-08.md), [14-E](../ETAPA-14.md#vigente-14-e), [14-F](../ETAPA-14.md#vigente-14-f). Fuente principal [08](../../../08_Historias_de_Usuario.md#contrato-DOC-03AI-01); diseño [02](../../../02_Diseno_Tecnico_R1_PMV.md); tareaP0 DOC-03AI en [16](../../../16_Task_Breakdown.md).04 proveedores,05 carga,07 vencimientos,11venta y09caja son dependencias, no módulos cerrados por este sublote.

| Recomendación | Beneficio | Riesgo/costo/impacto | Estado |
|---|---|---|---|
| Cabecera de recepción + líneas históricas + contador, enlazadas al lote físico |Identidad/reenvío y documento estable|Costo medio, migración y servicios; evita derivar historia de saldos mutables|Concreción técnica del contrato aceptado; implementación y pruebas pendientes al inventariar|
| Huella canónica y UUID obligatoriaHTTP |Reintento fiable tras pérdida de respuesta|Costo medio; conservar clave en errores y estados cambiados|Requisito DOC03AI/C02|
| Sustituir unicidad global del lote por unicidad dentro de recepción y fecha coherente |Permite entregas reales distintas|Costo medio; revalidar FEFO, búsquedas y mensajes que distinguen mismo número|Requisito DOC03AI/C03; no agrupar saldos de procedencias distintas|
| Sin backfill basado en FK/fecha; declarar desconocido |Evita historia inventada|Requiere diagnóstico operativo externo; no bloquea esquema nullable nuevo|Datos reales pendientes, opciones reconstrucción con evidencia o conservación desconocida|
| ConcurrenciaPG y caída real |Integridad bajo competencia|Costo medio, entorno aislado específico|Pendiente15; SQLite no acredita bloqueo por fila|

No se requiere una HU nueva para estas correcciones: INV01b y sus contratos ya expresan la necesidad. La implementación no cambia la selección de solicitudes, compras multiproducto o contabilidad fiscal.

## Resultado final14-G, sin sustituir el diagnóstico anterior

La clasificación anterior describe el build inicial. El corte final está en [ETAPA-14](../ETAPA-14.md#vigente-14-g) y la matrizJSON identifica ocho criterios exactos. HU-INV-01b/CA01 y DOC03AI/C03 permanecenPARCIALES por concurrencia/alcance; los otros seis cumplen en la muestra descrita. Cualquier dato operativo y demás criterios deINV04 conservan pendientes. Los10tests nuevos,584de regresión y23+44checkpointsChrome son conjuntos solapados.

Las siete rutas específicas son entrada,carga,stock,movimientos,recepción,baja y ajuste; las rutas de identidad/POS/caja/historial son dependencias del recorrido conectado, inventariadas en14-D/F y reejecutadas en cadena-final14-G. Se mantienen las11familias de campos/salidas anteriores. La nueva constancia implementa producto/código,fechaLima,responsable,proveedor/RUC o ausencia,referencia,cantidadUND,costo4,importe2,vencimiento y promedio histórico2; salen de valores persistidos y no de maestros actuales.

| Literal o plantilla nueva | Estado/rol | Requisito y evidencia |
|---|---|---|
| «RecepciónR-######## confirmada para…» / «Recepción confirmada» |POSTconfirmado/ALMACENERO|DOC03AI/C01;Chrome02/04|
| «Datos originales del ingreso… Las salidas y ajustes posteriores no cambian esta constancia interna.» |ConsultaADMIN/ALMACENERO|SnapshotsDOC03AI;Chrome09/23 y testajuste+4|
| «Costo promedio después de esta recepción» |Consulta,valorhistórico|RN14/CA02;4.50 tras físico2, no costoactual5.20|
| «Sin proveedor asignado» |Recepción nueva sin proveedor|Ausencia explícitaDOC03AI;Chrome04/20|
| «Falta la clave de recepción. Vuelva a abrir el formulario.» / «La clave… no es válida…» |POSTsinUUID/inválida|C02/C04;pruebaHTTPsinmutación|
| «La clave de recepción ya fue utilizada con otro contenido o responsable.» |UUIDdivergente|C02;Chrome08 y servidoractorajeno|
| «El lote… ya existe con otro vencimiento. Aclare la fecha antes de confirmar.» |Fechacontradictoria|DOC03AI;Chrome15/servidor|
| «Se agotó la capacidad de referencias de recepción. Solicite revisión administrativa.» |Contador99999999|DOC03AI;servidor,noChrome|
| «Ver recepción»,R-######## enlotedesalida/selección|ADMIN/ALMACENERO|INV04/CA02,procedencia;Chrome18/20 yHTTPajuste|
| «Sin constancia propia de recepción. Origen histórico incompleto; los nombres corresponden a los maestros actuales.» |Movimiento sinlíneapropia|Tratamientolegadocontrato;Chrome20|
| «Constancia interna de ingreso de mercadería. No sustituye un comprobante del proveedor.» |Constancia|DOC03AB/AI,evitarpromesafiscal;Chrome02/11/23|

Los controles internos de contador/huella/línea son tareas de diseño02 que satisfacenINV01b; no se crea unaHU por tabla. El comportamiento→planificación no detectó un extra comercial sin respaldo en estas superficies. Persisten limitaciones explícitas dellegacy,carga inicial,Kardex y merma; no se acepta todo elproducto por elcorte.
