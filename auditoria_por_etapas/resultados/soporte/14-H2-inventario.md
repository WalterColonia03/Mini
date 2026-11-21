# Inventario 14-H2 · 14/11/2026 Lima

Primera pasada. Cursor14-H2-KARDEX-SALDOS-01.08 inicial `1dac15a067dd0143d7b118d530f1fa222240455ec2d7d42eae83761f584fe597`, build196 `f9a593aacbd4cd5a0c753d672b5e06c1ada3dd21fb8a2f16b68009ee03f866aa`. SinAGENTS/XLSX encontrados en el workspace. Cambios y evidencia previos conservados en [snapshot](../evidencias/14-H2-20261114/build-antes.json). No se usaJira ni base operativa.

| Criterio | Estado inicial y alcance | Caso exigido |
|---|---|---|
| HU-INV-04/CA-01 |INCUMPLE: orden descendente, no saldo|Cronología total instante+ID, cantidad/lote/saldo; conciliación por lote|
| HU-INV-04/CA-02 |PARCIAL heredadoG/H1|Referencias de recepción y snapshots; SOL sigue futuro|
| HU-INV-04/CA-03 |PARCIAL heredadoH1|Carga capturada y ajuste con motivo/autor; no inferir historia antigua|
| HU-INV-04/CA-04 |INCUMPLE: controles ausentes|Fecha/hora y tipo; búsqueda, vacío, errores y recarga|
| DEC-08-KARDEX-COMPRAS/C-01 |INCUMPLE: sin apertura/cierre/variación|10+10+5−22−1=2; apertura20 desde10:01; filtrar venta conserva saldo3|
| DEC-08-KARDEX-COMPRAS/C-02 |PARCIAL heredadoF/G|Asignaciones de venta persistidas; desconocida/parcial/identidad ambigua no inventadas|
| DEC-08-KARDEX-COMPRAS/C-03 |PARCIAL: roles sin páginas|GET ADMIN/ALMACENERO no muta, VENDEDOR403;25filas/página, total del conjunto|

RN01/14/25/28/29, DOC03AI, CT-COHERENCIA-UI sustentan el tramo. CP-HU-INV-04-001 y CP-DEC-08-KARDEX-COMPRAS-001 tienen secuencia20+10−5−2+1=24 y26eventos empatados; el cursor10+10+5−22−1 añade venta que cruza tres procedencias. No confundir las dosfixtures. INV05/06 globales siguen futuras; constancia de merma es otro pendiente seleccionado.

## Rutas, acciones y campos inventariados antes de implementar

Entrada desde `/inventario/stock/`, enlace «Ver movimientos», hacia `/inventario/productos/{UUID}/movimientos/`. ADMIN/ALMACENERO consultan; VENDEDOR403; anónimo login; POST autorizado405. Consulta no crea ni modifica negocio. Rutas de carga, recepción y salida son dependencias: se revalidan enlaces y cadena, no sus módulos enteros.

| Campo/salida prevista | Formato, valor inicial y validación | Fuente |
|---|---|---|
| Desde/Hasta(Lima) |Vacíos=toda historia. Par opcional, ISOlocal YYYY-MM-DDTHH:mm, máximo16caracteres. Ambas o ninguna; rango no invertido; minuto final incluido; no fecha inferida del navegador|INV04/CA04,DEC08/C01 yfixture porhoras|
| Tipo |Todos; Entradas/Ventas/Mermas/Ajustes/Todas las salidas. Lista cerrada. Salidas=venta,merma,ajuste negativo|INV04/CA04|
| Página |Omitida/vacía=1; enteroASCII positivo hasta9dígitos; fuera del conjunto o formato inválido informa, sin500.25filas|DEC08/C03; límite técnico de parser|
| Saldo apertura/cierre |Todos los tipos del período, aunque el filtro oculte filas. No depende de página|DEC08/C01|
| Saldo por fila |Calculado antes de filtros y paginación; no repetir saldo−22 como si no hubiera entradas|DEC08/C01|
| Variación del filtro |Suma de cantidades documentadas en todo el conjunto, no página;No disponible si haycantidad/identidad desconocida|DEC08/C01/C03|
| Origen/saldo no disponible |Datos insuficientes, asignaciones incompletas, FK incoherente, secuencia negativa o discrepancia por lote. No derivar apertura restando desde stock actual|DOC03AI/DEC08/C02|
| Parámetros repetidos |Rechazo explícito de desde/hasta/tipo/page duplicados; sin reinterpretación ambigua|Validación de consulta/CT-COHERENCIA|

Se mantiene cabecera físico/vigente actual separada del saldo histórico. Las cantidades de entrada usan líneas originalesH1/G; las salidas usan asignacionesF o se declaran desconocidas. Un total coincidente no basta si dos lotes discrepan compensándose.

## Decisiones y límites

Se aplica delegación técnica vigente para realizarINV04/DEC08 ya seleccionados. Cálculo derivado en consulta, sin tabla de saldo mutable ni migración; costo medio de servicio/formulario/plantilla/pruebas. Beneficio: revisar existencias con procedencia y filtros fiables. Riesgo: volumen y concurrencia de lecturas entre tablas; medir en15, no prometer snapshot transaccional de PostgreSQL niSLA. Ante inconsistencia, saldo no disponible. Alternativa de saldo inicial de corte operativo requiere evidencia y autorización de datos; no se implementa.

[05](../ETAPA-05.md) · [06](../ETAPA-06.md) · [08](../ETAPA-08.md) · [14-F](../ETAPA-14.md#vigente-14-f) · [14-G](../ETAPA-14.md#vigente-14-g) · [14-H1](../ETAPA-14.md#vigente-14-h1). La matriz final distinguirá revalidado de heredado y pendientes; ninguna aprobación se transfiere automáticamente.

## Comportamiento → planificación: superficie final

Cada fila siguiente corresponde a una familia de literales/variables visibles en la misma rutaGET. ADMIN/ALMACENERO ven los resultados; VENDEDOR recibe403 antes de consultar costos. Capturas yJSON de cada paso registran texto/control/ruta/rol/testigo de negocio; no se presenta un escaneo de plantillas como prueba dinámica.

| Familia / literal o plantilla | Significado y validación | Requisito y prueba |
|---|---|---|
| Stock físico actual: {Q} unid. · Stock vigente: {V} unid.; Movimientos: {producto} |Datos actuales del producto; no el saldo al cierre de otro período|RN14/INV04; cadena44 yChrome01/02|
| Filtros de movimientos; Desde (Lima); Hasta (Lima); Tipo |Etiquetas asociadas; entrada vacía inicial; formato/normalización/topes del inventario previo|INV04/CA04; Chrome02/04/05/06|
| Fechas y horas de Lima. Complete ambas fechas o deje ambas vacías para toda la historia. El minuto final está incluido. |Par opcional, horaLima y fin inclusivo. No conversiones según navegador|DEC08/C01; server minute_end yyear_boundaries|
| Todos / Entradas / Ventas / Mermas / Ajustes / Todas las salidas |Valores cerrados; salidas incluye ajuste negativo. El filtro solo selecciona filas|INV04/CA04; casoescrito20+10−5−2+1 yChrome02|
| Aplicar filtros; Limpiar filtros |GET recuperable; cambio de filtro vuelve a1; limpiar elimina parámetros|INV04/CA04/C03; Chrome02/03/04|
| Complete Desde y Hasta, o deje ambos vacíos.; Desde no puede ser posterior a Hasta. |Error visible sin resultado numérico válido|INV04/CA04; Chrome04/05 yserver invalid_dates|
| Ingrese una fecha y hora válida: AAAA-MM-DDTHH:MM (Lima).; Asegúrese de que este valor tenga como máximo16caracteres (tiene{n}). |Formato/calendario/longitud de fecha; mensaje de longitud localizado porDjango|Validación de consulta; server invalid_dates yHTML del formulario|
| Escoja una opción válida. {valor} no es una de las opciones disponibles. |Mensaje localizado de ChoiceField; valor escapado|INV04/CA04; Chrome06. Primera automatización esperaba«Seleccione» y se corrigió sin cambiar producto|
| Página debe ser un entero positivo de hasta 9 dígitos.; La página solicitada no existe para estos filtros. |Formato/tope/rango; no ir silenciosamente aotra página|DEC08/C03; Chrome07/08 yserver invalid_pages|
| No repita el parámetro {desde/hasta/tipo/page}.; No se realizó la consulta. Corrija los filtros indicados. |Duplicados rechazados; no filas ni resumen, errores cerca de campos|Validación/CT-COHERENCIA; Chrome09 yserver repeated_keys|
| Resumen del período; Apertura, cierre y saldo por movimiento consideran todos los tipos de operación, incluso los que oculta el filtro. No dependen de la página. |Apertura antes delinicio; cierre alminuto final; ambos calculados con todos los tipos|DEC08/C01; Chrome02/10/11/12|
| Saldo de apertura (UND); Saldo de cierre (UND); Variación documentada del filtro (UND); Movimientos coincidentes, todas las páginas |Enteros oNo disponible, variación con signo, contador completo. Tabla25 no limita total.−22/20/2 y26/+26/50/76|DEC08/C01/C03; Chrome02/11/12|
| Saldo reconstruido desde los registros conservados y conciliado por lote con el stock físico actual. |Resultado de conciliación, no garantía sobre documentos ausentes o escrituras externas|DEC08/C01; server known_cases yper_lot|
| Saldo no disponible. Los registros conservados no permiten reconstruir y conciliar el saldo de este producto. |Se anulan saldos globales y de filas sin esconder movimientos conocidos|DEC08/C02; Chrome19/20; serverlegacy/incomplete/ambiguous/compensating|
| Sin fotografía de entrada para uno o más lotes.; La cabecera de una carga está incompleta.; Un lote tiene más de un origen registrado.; Hay una relación de origen inconsistente. |Razones específicas de origen; no inventar tipo dellegado conis_initial|DOC03AI/DEC08; Chrome19 yserver inconsistent_origin. Cabecera incompleta/dobleorigen: ramas porinspección, variantes directas no ejecutadas enH2|
| Una venta tiene asignaciones de lote ausentes o incompletas.; La identidad de un producto vendido no está confirmada. |Ausencia/partial yFKNULL; no inferirFEFO para pasado ni identidad porbarcode|DEC08/C02; server incomplete_allocation/ambiguous|
| La secuencia registrada produce una cantidad negativa por lote.; Las cantidades por lote no concilian con el stock físico actual.; La variación registrada no concilia con el stock físico actual. |No basta coincidencia deltotal; errorcompensado porlote bloquea saldo|DEC08/C01; Chrome20 yserver negative/compensating|
| El inventario cambió durante la consulta. Vuelva a consultar. |Lote visto en salida después de cargar catálogo de lotes; evita500, no acredita aislamientoPG|Consulta robusta; servernew_lot_seen_between_reads, no concurrencia real|
| Fecha; Tipo; Detalle; Cantidad; Saldo; Responsable; fecha/hora:segundos(Lima); ▲Entrada/▼Venta/▼Merma/⇅Ajuste |Orden instante+ID; cantidad firmada; saldo acumulado previoalfiltro. UUIDestable como desempate interno, no dato que operador debaintroducir|INV04/CA01; Chrome01/02/11/12|
| Recepción {R} — Lote {n} ({proveedor/Sin proveedor asignado}); Ver recepción; Carga inicial — Lote {n} ({proveedor}); Ver carga inicial |Cantidad y responsables capturados, enlaces propios. Sinproveedor en carga omiteparéntesis|INV04/CA02/03; Chrome01 ycadena44; recepciones específicas14-G/H1heredadas, runtime revalidado porsuite|
| Entrada de origen no confirmado — Lote {n} ({proveedor}); Origen histórico incompleto. Cantidad original no disponible; los nombres corresponden a los maestros actuales. |CantidadNo disponible; no clasifica elorigen porflag antiguo|DOC03AI/INV04; Chrome19|
| Venta {V}; Coincidencia por código histórico; identidad del producto no confirmada.; Lotes de salida; Asignación incompleta. Solo se muestran los lotes registrados.; Lotes de salida: No disponibles (registro anterior o incompleto). |Asignaciones persistidas; nunca FEFO deducido. Número/qty/vencimiento y enlaceR porasignación|DEC08/C02; Chrome02 ytests incompleto; evidencia anteriorF enlazada|
| Costo unitario de salida: S/{costo4} oNo disponible; Merma ({causa}) · {M} — Lote{n}.{notas}; Ajuste físico — Lote{n}.{motivo} |Costo histórico venta; bajas/ajustes incluyen motivo y autor registrado (nombreactual, pendiente fotografía en14-I). Datos visibles escapados porplantilla|INV04/CA01/03, RN28; Chrome01,cadena44,suite de trazabilidad|
| No hay movimientos coincidentes con estos filtros.; Página{n}de{total} ·25movimientosporpágina; Anterior; Siguiente; ←Volver alinventario |Vacío distingueconsulta válida; enlaces conservan filtro y límites; tabla horizontal conetiqueta/foco|DEC08/C03 yCT-COHERENCIA; Chrome10/11/12/13/17/18|

Son24familias de superficie delKardex, trazadas a7criterios principales. Los mensajes compartidos de login/403/base, formulario de carga, recepción/cobro/baja/cierre conservan los inventarios detallados anteriores y la revalidación acotada de cadena. No se contabilizan aquí como nuevas funciones ni se declaran auditados por completo.
