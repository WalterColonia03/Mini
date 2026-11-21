# Inventario 14-H · Kardex, saldos y consultas

Primera pasada,13/11/2026 Lima. Cursor14-H-KARDEX-SALDOS-01.08 inicialSHA256 `fc69a8e9641f8c9c21c6356300fcd84bb3ad9e4ca62edc4c49ae90cd2832e59c`; build194 `f6ca27baf3813bf8806d449269623e0e9d293e8000dee4cfd83d45dd038cb11c`. Cambios locales anteriores preservados. No se encontróAGENTS aplicable niXLSX en el workspace; no se usaJira. [Snapshot de producto](../evidencias/14-H-20261113/producto-antes.zip).

## Requisitos inventariados antes de implementar

**División ejecutada:** H1 resuelve la dependencia de fotografía inicial. Las filas de saldo/filtros/paginación que siguen son inventario y trabajo pendiente H2; sus controles propuestos no existen todavía. La matriz final por criterio se conserva en [criterios-final.json](../evidencias/14-H-20261113/criterios-final.json). No se transfieren aprobaciones de etapas anteriores.

| ID | Estado inicial por inspección | Acción prevista y evidencia exigida |
|---|---|---|
| HU-INV-04/CA-01 |INCUMPLE: orden descendente y sin saldo|Orden ascendente instante+ID, saldo por movimiento y conciliación con stock; Chrome y servidor|
| HU-INV-04/CA-02 |PARCIAL heredado14-G|Revalidar referencias y proveedor/autor de recepción en la consulta nueva; SOL sigue futuro|
| HU-INV-04/CA-03 |PARCIAL: etiqueta carga/ajuste, pero datos maestros actuales|Revalidar motivo/autor y captura original de carga nueva; legado explícito|
| HU-INV-04/CA-04 |INCUMPLE: sin filtros|Período/tipo, errores y vacío; conservar parámetros|
| DEC-08-KARDEX-COMPRAS/C-01 |INCUMPLE: no apertura/cierre/total filtrado|Secuencia10+10+5−22−1=2; período con apertura20; filtro venta no recalcula saldo ignorando entradas|
| DEC-08-KARDEX-COMPRAS/C-02 |PARCIAL heredado14-F/G|Asignaciones persistidas, referencias de recepción; legado sin asignación no atribuido porFEFO|
| DEC-08-KARDEX-COMPRAS/C-03 |PARCIAL: permisos, sin paginación25|ADMIN/ALMACENERO GET sin mutación, VENDEDOR403, páginas y totales del conjunto filtrado|
| HU-INV-01a/CA-01..05, dependencia |Evidencia previa05; no cierre heredado|Captura de cantidades y cabecera originales para sustentar saldo; transacción/errores/permisos y regresión sin cambiar sus criterios|

Son siete criterios principales deINV04/DEC08 y cincoCA de la dependenciaINV01a. DOC03AI exige cantidad original y snapshots de carga/entrada; CT-ROLLBACK exige atomicidad; CT-COHERENCIA-UI exige significado de saldo/filtro/página. RN01/14/19/25/28/29 respaldan identidad de lote, cantidades, FEFO, historia y roles. No se agrega unaHU por función de consulta.

## Superficies y significado

| Ruta/pantalla | Rol/acción | Texto/campos/salida y respaldo |
|---|---|---|
| /inventario/stock/ |ADMIN/ALMACENERO, enlaceVer movimientos|Entrada alKardex; stock físico/vigente no son saldo de período|
| /inventario/productos/{UUID}/movimientos/ |ADMIN/ALMACENERO, GET|Movimientos, fecha,tipo,detalle,cantidad,responsable; nueva columnaSaldo y controles de período/tipo/página; INV04|
| Misma ruta directa |VENDEDOR/anonimo/POST|403 ologin; POST405 para rol autorizado, ninguna mutación|
| /inventario/carga-inicial/ y /inventario/cargas/{UUID}/ |ALMACENERO confirma; ADMIN/ALMACENERO leen|Cantidad original, número/costo/vencimiento/autor/proveedor y nombre/código capturados para cargas nuevas; DOC03AI/INV01a|
| /inventario/recepciones/{UUID}/ |ADMIN/ALMACENERO|ReferenciaR, cantidades originales y snapshots ya implementados14-G; revalidar enlaces|
| Venta/baja/ajuste |Origen de eventos|Venta por línea y asignaciones; merma/ajuste por lote, motivo y autor. No crear constancia de merma ficticia|

| Campo/salida | Tipo, inicial, límites | Validación y significado previsto |
|---|---|---|
| Desde/Hasta(Lima) |Opcionales en conjunto, fecha+hora al minuto|ISOlocal, ambas o ninguna, rango no invertido. Minuto final incluido; no interpretar según reloj del navegador|
| Tipo |Todos inicial; carga,recepción,entrada heredada,venta,merma,ajuste,salidas|Lista cerrada. SALIDAS reúne venta/merma/ajuste negativo; filtros no cambian saldos reales|
| Página |1 inicial, entero positivo|25filas; parámetros preservados; inválida informa sin500|
| Saldo apertura/cierre |EnteroUND oNo disponible|Incluye todos los movimientos del período, independientemente del tipo seleccionado|
| Saldo por movimiento |EnteroUND oNo disponible|Se calcula antes de filtrar/paginar; no mostrar saldo reconstruido como demostrado|
| Variación del filtro |Entero con signo oNo disponible|Conjunto filtrado completo, nunca suma de página solamente|
| Cantidad de registros |Entero|Total filtrado y página actual identificados|
| Origen incompleto |Mensaje junto al registro/resumen|No inventar cantidades originales, producto histórico, lotes de venta o saldo inicial|

La consulta actual no conserva fotografía de carga; `initial_quantity` puede aumentar por ajuste y `is_initial` antiguo no acredita el origen. Para saldos sustentados se requiere capturar las cargas nuevas sin backfill y comprobar cantidades por lote contra asignaciones/bajas/ajustes y saldo disponible. Si hay origen desconocido, asignación incompleta, identidad ambigua, saldo negativo o discrepancia, la consulta debe declarar el saldo no disponible. La suma que coincide con stock por casualidad no demuestra la historia.

## Alternativas, costo y alcance autorizado

| Propuesta/concreción | Beneficio | Riesgo/costo/impacto | Fundamento/estado |
|---|---|---|---|
| Fotografía confirmada en carga nueva, nullable para legado |Sustentar cantidad/autor originales y saldo|Costo medio, migración y servicio; sin reescribir legado|DOC03AI yDB-C07 ya aceptados; concreción técnica dentro de delegación14|
| Saldo calculado desde movimientos con comprobación por lote |Verificar stock sin mantener segundo saldo mutable|Costo medio de consulta; volumen/concurrencia necesitan15|INV04/DEC08 aceptados; no supone historia completa por fecha/FK|
| MostrarNo disponible si no concilia |Evitar decisiones sobre saldo inventado|Reduce cobertura numérica de legado hasta investigar|Requisito de historia; no añadir ancla operativa sin hechos/autorización|
| Filtro local por minuto y resumen separado de tipo/página |Explicar lo observado por el operador|Costo bajo/medio; concretar inclusive/minuto en08|CasoCP-HU-INV-04-001 usa10:00..13:00, no basta filtro diario|
| Paginación estable25 |Lectura manejable y enlaces reproducibles|Costo medio; carga completa en memoria requiere límite de volumen medido|DEC08/C03; no prometerSLA no medido|

Alternativa de guardar saldo inicial de corte operativo: requiere evidencia y autorización de datos, queda pendiente. No usar `stock actual−movimientos` para inventar el pasado. Libro de eventos completo en tabla nueva puede evaluarse si volumen/consistencia lo exige; no se impone ahora sin necesidad demostrada.

[05 carga](../ETAPA-05.md) · [08 movimientos](../ETAPA-08.md) · [14-E costo](../ETAPA-14.md#vigente-14-e) · [14-F asignaciones](../ETAPA-14.md#vigente-14-f) · [14-G recepción](../ETAPA-14.md#vigente-14-g). Diseño02, tareas16 y preparación14 requieren actualización junto con08/07/09/03. Primera pasada15–17 y segunda pasada siguen pendientes.

## Superficie realmente modificada H1

ADMIN/ALMACENERO consultan `/inventario/cargas/{UUID}/` y su alias `/inventario/carga-inicial/{UUID}/creada/`; VENDEDOR403, anónimo login, POST autorizado405. ALMACENERO confirma en `/inventario/carga-inicial/`; los otros roles403. No se añaden campos editables ni endpoints. Número/cantidad/costo/vencimiento/proveedor y errores de formulario conservan el inventario detallado de [05](../ETAPA-05.md) y [cadena14-D](../evidencias/14-D-20261113/navegador/RESUMEN.md), con revalidación explícita del caso nuevo y regresión.

| Literal o plantilla visible | Significado, estado y límites | Fuente / evidencia |
|---|---|---|
| Existencias confirmadas; Carga inicial confirmada; Consulta el registro de carga y las recepciones posteriores de este producto |Carga persistida, no promesa de completar Kardex|INV01a; Chrome02,03,10|
| Datos originales de la carga inicial; Código del producto al confirmar; Responsable de carga inicial; Carga inicial confirmada; Costo promedio inicial; Proveedor al confirmar |Cabecera capturada: nombre160/código64/autor120/proveedor160/RUC11/unidad8; NULL legado, cadena vacía proveedor ausente, promedio decimal14,4 mostrado2. Fecha Lima|DOC03AI,INV01a04/05; Chrome03,04; test originales|
| Sin proveedor asignado |Ausencia conocida al confirmar; no sustituye NULL legado|Test no_supplier; cadena general con proveedor|
| Lotes de la carga inicial; Las cantidades y los datos originales se conservan aunque cambien los maestros o las existencias |Fotografía nueva; servicio no altera líneas por operaciones posteriores. Protección SQL directa completa pendiente15|INV01a/03AI; Chrome10 y test original tras recepción/venta/merma|
| Lote; Cantidad cargada; Disponible actual; Costo unitario original; Vencimiento original; Ingreso (Lima) |Número normalizado64; original1..999999; disponible físico actual; costo positivo hasta9999999.9999 a4; fechaoriginal; instantecopiado deLot. Datos no editables|DEC05,INV01a; Chrome02,10,13/13b; test límites|
| Datos actuales del producto; Producto actual; Existencias físicas actuales; Costo promedio actual |Maestros/cantidades actuales separados de historia; promedio actual a2, sin afirmar stock vendible|RN14/CT-COHERENCIA; Chrome03,10,14|
| Origen histórico incompleto. Cantidad original no disponible: esta carga no tiene una fotografía confirmada. Los datos actuales no acreditan sus valores originales. |Estado sin fotografía, no inferir cantidades originales|DOC03AI; Chrome14 y test legado/migración|
| Lotes vinculados sin fotografía original; Datos actuales. El vínculo a la carga no demuestra el origen de cada ingreso. Cantidad original no disponible; no se ha reconstruido una recepción. |No clasificar entradas antiguas solamente por `is_initial`|DOC03AI; Chrome14|
| Lote actual; Disponible actual; Costo unitario actual; Vencimiento actual; Proveedor actual; Responsable registrado (nombre actual); No disponible |Consulta del legado con alcance de cada campo explícito; no inventar responsable desde cabecera|DOC03AI; Chrome14 y test legado|
| Recepciones con constancia propia; R-########; fecha y responsable |Enlaces a documentos separados; no agregar sus cantidades a la carga inicial|INV01b; revalidación de recepción23 checkpoints|
| Cargar otro producto; Registrar entrada posterior; Ver inventario; Ir al inicio |Primeros dos solo ALMACENERO, navegación a rutas existentes; ADMIN solo consulta|RN29; Chrome y suite|
| Carga inicial — Lote {número} ({proveedor}); +{cantidad}; {responsable}; Ver carga inicial |Kardex usa fotografía y enlaza carga; proveedor ausente omite paréntesis|INV04/CA03; Chrome11,12; cadena44|
| Origen histórico incompleto. Cantidad original no disponible; los nombres corresponden a los maestros actuales. |Kardex heredado sin cuantía original; no se usa para aprobar saldo|INV04/DEC08; Chrome15|

Las salidas sanitizadas completas (texto/control/ruta/rol/huella) están en cada JSON del navegador. Las etiquetas, estados y mensajes nuevos se agrupan aquí en13familias; no son13HUs. Los menús/layout compartidos se reobservan en la cadena, sin afirmar auditoría exhaustiva de sus componentes.
