# Disposiciones 14-H2 · 14/11/2026 Lima

Primera pasada. El encargo de integración y la delegación técnica ya aplicada cubren realizar HU-INV-04 y DEC-08-KARDEX-COMPRAS, con RN01/14/25/28/29 y contratos históricos de entradas/ventas. No se interpreta «continúa» como autorización nueva de alcance comercial, despliegue o datos operativos.

| ID | Decisión y fundamento | Beneficio, riesgo, costo e impacto | Estado |
|---|---|---|---|
| D14H2-01 |Derivar eventos de InitialLoadLine/StockReceiptLine/SaleLotAllocation/bajas/ajustes; ordenar por instante+ID estable, sin tabla de saldo duplicada|Concilia historia con físico y reduce divergencia entre dos saldos. Costo medio. Historial completo se carga en memoria: rendimiento/volumen pendientes15|Aceptada como concreción deINV04/DEC08; implementada|
| D14H2-02 |Comprobar cada lote y bloquear saldos ante origen incompleto, relaciones incoherentes, asignación parcial, producto ambiguo, secuencia negativa o discrepancia|Evita que errores compensados por lote aparenten conciliación. Costo medio; limita historia cuantificable del legado|Implementada; no inferir apertura desde stock actual|
| D14H2-03 |Calcular saldos completos antes de seleccionar período/tipo/página. Apertura/cierre de todos los tipos, variación del filtro en todo el conjunto|Evita saldo ficticio−22 y total solo de página. Costo bajo/medio; resumen explica la distinción|Concreción ya exigida porC01/C03|
| D14H2-04 |PeríodoLima al minuto, ambos extremos o ninguno, inclusivo al final; tipos cerrados; página positiva hasta9dígitos; parámetros repetidos rechazados|Hace reproducible el caso porhoras y evita errores500/interpretación ambigua. Costo bajo, sin límite comercial nuevo|Incorporado en08 antes del cierre; errores conservan valores y no muestran resultado válido|
| D14H2-05 |Saldo desconocido no oculta movimientos conservados; nombre/autor/proveedor original siguen en cargas/recepciones, y legado se etiqueta no confirmado|Conserva evidencia útil sin presentarla como completa. Costo bajo. Datos reales requieren investigación|Implementada dentro deDOC03AI yDEC08/C02|
| D14H2-06 |Si aparece un lote nuevo entre consultas del historial, degradar saldo e indicar nueva consulta sinKeyError|Evita fallo de lectura durante cambios. Costo bajo. El ensayo de intercalación determinista no demuestra aislamiento o toda carreraPG|Prueba específica, consistencia concurrente global pendiente15|
| D14H2-07 |Adaptar prueba antigua que exigía ausencia de filtros/saldo:INV04 ya está seleccionado; mantener ausencia de historialesINV05/06 futuros|No confundir defecto seleccionado con exclusión legítima. Snapshot del test anterior preservado|Corrección de expectativa respaldada por08, sin rebajar criterio|
| D14H2-08 |Ancho mínimo del detalle y tabla desplazable; cifras del resumen no se parten|Corrección de defecto móvil observado enChrome390. Costo bajo y cambioCSS acotado; no implica teléfono físico|Revalidación visual exigida antes de cierre|

La guía UI/UX Pro Max se aplica a etiquetas asociadas y errores junto al control, usando componentes actuales. La consulta local devolvió Form Labels y Submit Feedback, pertinentes al filtroGET. No se agrega animación/carga artificial ni se anuncia éxito de una consulta inválida. La revisión de capturas, además de los assertsDOM, detectó la compresión móvil.

## Alternativas y pendientes

| Recomendación | Beneficio | Riesgo/costo/impacto | Disposición |
|---|---|---|---|
| Snapshot consistente de lectura enPG y paginación bajo escrituras simultáneas |Evitar mezcla temporal o desplazamiento entre páginas mientras cambia el historial|Costo medio; evaluar consulta única o aislamiento de lectura. Probar con conexiones reales y volumen, sin bloquear todas las escrituras por comodidad|Etapa15; no acreditado porSQLite ni intercalación simulada|
| Optimizar historial grande tras medir |Mantener tiempo/memoria de consulta acotados|Costo medio; alternativa de consultaSQL unificada o libroeventos necesita justificar complejidad y migración|MediciónNFR pendiente;25filas de salida no prueban costo constante|
| Apertura histórica de corte con procedencia |Hacer útil saldo en legado incompleto|Costo medio y riesgo de inventar datos; requiere evidencia del negocio, fecha, responsable y autorización explícita de datos|Investigación; no aceptada automáticamente ni implementada|
| Constancia de merma y autor/origen inmutables |Explicar bajas después de cambios de maestro|Costo medio; reutilizarHU-INV-02/RN05, no crearHU redundante. No sustituirla por un enlace de recepción|Siguiente sublote14-I; criterio seleccionado pendiente|

[Inventario](14-H2-inventario.md) · [Informe](../ETAPA-14.md#vigente-14-h2). No se cierra ningún módulo completo por completar este sublote.
