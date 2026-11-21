# Etapa13-B · Disposición de hallazgos y propuestas

> **Estado vigente 13-B-final, 13/11/2026, primera pasada:** aceptación visual completada; las disposiciones finales están al final de este anexo. Los apartados intermedios conservan la investigación y el bloqueo anteriores, ya superado. [Evidencia nueva de navegador](13-B-final-navegador.md).

Primera pasada,13/11/2026, America/Lima. Este anexo conserva13-A como antecedente y registra las decisiones del alcance vigente. La verificación dinámica se identifica por evidencia en los anexos de navegador, servidor y PostgreSQL; aceptar una precisión no la da por verificada.

## Entrada y autorización

08 de entrada SHA256 `5735fb283b70bca02ed551e0000c72df2025eaef9b977607b1e4a2b890e5a1d9`, idéntico al final13-A. HEAD `7816d3328115cf5aa5bcdd0985fffd795b3ae084`. La primera comparación de178archivos emitió cero diferencias; durante el trabajo paralelo, la captura persistida de16:38:17Z ya registró cambios de13-B en `identity/templates/identity/dashboard.html` e `inventory/templates/inventory/stock_overview.html`. Por tanto, [baseline.json](../evidencias/13-B-20261113/baseline.json) es una captura intermedia, no un manifiesto idéntico al build final13-A. Su campo `inherited_build_sha256` identifica únicamente el antecedente. Se conserva sin reescribir para no ocultar esa secuencia. Ocho documentos preservados antes de la edición en [antes.zip](../evidencias/13-B-20261113/planificacion/antes.zip). Se conservan los cambios locales preexistentes; no hay commit ni despliegue.

El encargo autoriza correcciones técnicas acotadas/reversibles del panel y consultas necesarias para explicar cifras, enlaces, mensajes y permisos. RN-06, RN-29, DEC-07-VENCIDOS-FILTRO y CT-COHERENCIA-UI respaldan las precisiones siguientes. No se acepta una propuesta por estar escrita ni se selecciona una HU futura.

## Decisiones técnicas aceptadas

- **PROP-13-LINK-CONTEXTO / H13-06:** conservar la consulta general, rotular todas las fechas y explicar Fecha exacta para cotejar el día del panel. El resultado general243.39 y el diario60.06 representan conjuntos distintos, no una suma defectuosa. Esta alternativa elimina la ambigüedad sin añadir filtros implícitos ni reporte nuevo; costo bajo, riesgo de texto desfasado mitigado al seguir el enlace y filtrar el día de la fixture.
- **PROP-13-MENSAJES / H13-07:** precisar inclusión de igualdad en el mínimo y recepción de bienes. La fórmula `vendible <= mínimo` y la autorización de recepción ya están aceptadas; no se cambia umbral, política de compra ni flujo futuroSOL. La consulta fallida debe explicar fallo y permitir recuperación sin ceros ni detalles técnicos. Los literales finales y su ejecución se registran al terminar la implementación.
- **PROP-13-PANEL-CONTRATO / H13-01..05:** conservar fechaLima única, siete cifrasADMIN, tresALMACENERO, ausencia de resumenVENDEDOR, separación entre ventas del día y estados actuales, recarga manual, límites1..3650y30por defecto.13-A ya implementó estas correcciones;13-B revalida el build final, sin convertir capturas antiguas en evidencia nueva.

## Investigaciones delimitadas

- **PROP-13-CORTE-CONSISTENTE / H13-08:**13-A detectó posibilidad de mezcla de commits pero no la reprodujo. El contrato original no prometía una transacción global de toda la pantalla. La investigación13-B debe demostrar si las métricas presentan un estado incompatible y, de confirmarse, aplicar una corrección proporcional bajoCT-COHERENCIA-UI. Se documentarán aislamiento, conexiones, escritura y alcance exacto; no se afirma atomicidad por usar `atomic()` ni por probarSQLite.
- **PROP-13-NFR-CONSULTA:** medir volumen sintético declarado antes de decidir índices/caché. DT-15 referencia2000productos/20000lotes/300ventas-día no describe actividad real; no existe SLA particular del panel. La medición no demuestra capacidad de producción ni necesita una política de negocio inventada para cerrar la exactitud de la consulta actual.

## Futuro explícito

**PROP-13-FUTUROS-REFINAR:** las16HU/39CA deCONF/DASH/REP permanecen futuras (MoSCoWW). Frecuencia automática/períodos, ranking/denominadores, margen/costo comparable, logo histórico, PDF/formatos yYape exigen refinamiento/selección posterior. La autorización técnica actual no elige prioridades comerciales ni crea obligaciones fiscales. Su ausencia no bloquea el panel mínimo aceptado; una promesa visible de esas funciones sí sería un defecto actual.

## Hallazgos y disposición vigente

| Hallazgo | Disposición y fundamento | Evidencia y límite |
|---|---|---|
| H13-01 | Corrección heredada de13-A revalidada en servidor; continúa pendiente aceptación visual de todos los límites. | D06/D07 de13-B incluyen1/3650, fuera de rango, formato, Unicode, repetición, espacios, nulo y cadenas extremas/ceros. Navegador solo30→1. |
| H13-02 | Badge de stock en producto/categoría inactivos resuelto y observado de nuevo en catálogoADMIN; existencias y estado conservados. | B02 muestra4unidades en categoría inactiva y8en producto inactivo sinStock bajo; igualdad5/5activa sí. La captura corresponde al recorrido parcial, no certifica todo el build final ni la etapa03. |
| H13-03 | Promesa de reportes retirada; reobservada en login. | B01 anuncia resumen diario, sinREPfuturo. El inventario/docstring usaDEC07. |
| H13-04 | FechaLima, diario frente a actual y recarga heredados, comprobados enADMIN y en servidor. | ObservaciónADMIN inicial y FINAL-lima-date/ROLE. Pendientes tres roles del build final por navegador. |
| H13-05 | Consulta restringida por rol implementada; precisión nueva del corte requiere consulta única7/3/0. | Pruebas de valores/roles de13-B; PostgreSQL documenta plan y número de consultas. No era fugaHTML demostrada en13-A. |
| H13-06 | Propuesta técnica aceptada e implementada: «Historial de ventas (todas las fechas)» y ayuda deFecha exacta del díaLima. | H13-06-link-context yD10-today/range verdes en servidor; destino general sigue deliberadamente general. Visual final pendiente. |
| H13-07 | Propuesta técnica aceptada e implementada: «Stock vigente en el mínimo o por debajo» y «Registra lotes de mercadería recibida para productos que ya tienen carga inicial.». | H13-07-threshold/equality/receipt verdes; no cambia≤ni concede autorización de compra. Visual final pendiente. |
| H13-08 | Defecto demostrado5/5enPG18.4 con conexiones independientes; corrección técnica aceptada en08 antes de modificar consulta: una sentencia por rol. | No se relega a15 para fabricar cierre. La verificación final de concurrencia/volumen se registra en el anexoPostgreSQL. |

Servidor: [poblado100/100](../evidencias/13-B-servidor-20261113T164755068835Z/results.json) y [vacío100/100](../evidencias/13-B-servidor-20261113T164757087079Z/results.json), conjuntos solapados. [Recorrido y bloqueo de navegador](13-B-navegador.md). Los hallazgos cuya corrección afecta presentación conservan el pendiente de aceptación visual final; una suite verde no elimina ese requisito.

**Hallazgo nuevoD11:** cinco clases de fecha imposible/extrema producían500y una fecha noISO era aceptada. Se corrigió validación de fecha del historial para informar error sin consulta fallida ni mutación. D11 incluye caracteres nulos, fecha exacta/inicial/final inválida, rango invertido, vendedor/turno inválidos y longitud; no declara auditado todo ventas. El estado500 genérico ahora dice «No se pudo completar la solicitud», permite actualizar una consulta o volver al inicio y distingue la cautela de revisar el estado antes de repetir una operación; no consultaBDpara renderizar. FAILURE/RECOVERY sobre panel, stock, vencimientos e historial comprueban500sin ceros/detalles y recuperación200. Su experiencia visual permanece pendiente.

## Disposición de propuestas

| Propuesta13-A | Decisión actual | Pendiente legítimo |
|---|---|---|
| PROP-13-PANEL-CONTRATO | Precisión técnica aceptada e integrada en08; implementación y servidor comprobados por caso. | Revalidación visual final deCP002; no se declara verificado todoCT. |
| PROP-13-LINK-CONTEXTO | Aceptada alternativa de historial general claramente rotulado; implementada y verificada servidor. | Navegador final enlace→fecha→total. No requiere decidir/reportarREPfuturo. |
| PROP-13-CORTE-CONSISTENTE | Aceptada corrección de defecto reproducido, con consulta única/snapshot de sentencia. | Alcance/versiones/resultados específicos enPostgreSQL; no garantía global. |
| PROP-13-NFR-CONSULTA | Aceptada medición sintética proporcionada, sin decisión anticipada de índices/caché. | Volumen real ySLArequieren investigación operacional; no bloquean por sí mismos el panel actual. |
| PROP-13-MENSAJES | Aceptadas precisiones de igualdad, recepción y error recuperable; implementadas y verificadas servidor. | Visual final y teclado/foco/pantalla estrecha. |
| PROP-13-FUTUROS-REFINAR | Futuro explícito fuera del alcance actual. | Selección comercial/refinamiento de16HU/39CA; no se convierten en bloqueos artificiales. |

## Continuidad y bloqueo

La herramienta de navegador perdió acceso y la alternativa nativa se detuvo por no poder determinar laURLpara aplicar su política; se respetó esa detención. El trabajo independiente servidor/PostgreSQL/documentación continúa, pero la etapa permanecePARCIAL. Falta restaurar acceso de navegador autorizado y ejecutar13-B-01final,13-B-02cobroUIy13-B-03visual con fixtures nuevas, versiones y capturas propias. Al cerrar13seguirá14; no se ejecuta14ni se inicia segunda pasada en este encargo.

## Resultado independiente final13-B

[PostgreSQL](13-B-postgresql.md):37/37comprobaciones y6/6tests, incluyendo25lecturasconcurrentes/22commits, vacíos y efectos del cobro por servicios. H13-08resuelto y verificado enPG18.4 para snapshot de sentencia;17no probado. [Servidor](13-B-servidor.md):100/100porfixture y160/160regresión final. Los conjuntos se solapan. PROP-NFRmedida con2008productos/20014lotes/30006ventas; noíndice/cachéjustificado por esa muestra. Disposiciones técnicas independientes completas; aceptaciónvisual pendiente según anexo yCP002.

## Disposición final · 13-B-final · 13/11/2026 Lima · primera pasada

Las propuestas se aceptaron por su correspondencia con RN-06, RN-29, DEC-07 y CT-COHERENCIA-UI y por defectos/ambigüedades demostrados; no por su mera existencia en código o en este documento. El cierre incorpora [navegador final](13-B-final-navegador.md) y [compatibilidad verificada del build](../evidencias/13-B-final-20261113/validacion-evidencia.json). No hubo nuevos cambios de producto durante esta revalidación. Las disposiciones siguientes sustituyen los pendientes visuales de las tablas anteriores.

| Hallazgo | Disposición final | Fundamento y comprobación |
|---|---|---|
| H13-01 | Resuelto y verificado | V05–V12: 1/30/3650, vacío, inválidos y 5000 dígitos; retorno a 30, aviso y conteos/listas coherentes. Variantes adicionales en D06/D07 servidor. |
| H13-02 | Resuelto y verificado | V03/V04: producto/categoría inactivos sin alerta crítica, manteniendo existencias/estado; igualdad activa 5/5 sí alerta. No cambia vigencia ni política de stock. |
| H13-03 | Resuelto y verificado | V01 login sin promesa de reportes. Las 16 HU/39 CA futuras siguen excluidas. |
| H13-04 | Resuelto y verificado | V02/V25/V29 e I01–I12: fecha Lima, diario frente a estado actual, recarga explícita y efecto posterior al cobro. |
| H13-05 | Resuelto y verificado | UI 7/3/0 y denegaciones; servidor restringe datos por rol; PG registra 1/1/0 consultas de métricas. No se presenta como corrección de una fuga HTML antes demostrada. |
| H13-06 | Propuesta técnica aceptada, implementada y verificada | V13–V14: historial general rotulado y ayuda del día; 243.39 general frente a 60.06 diario. El enlace no promete abrir solo las ventas del panel. |
| H13-07 | Propuesta técnica aceptada, implementada y verificada | V03 igualdad y V25/P04 mercadería recibida. F01–F08 acreditan error de consulta y recuperación sin ceros. No altera umbral ni concede permiso comercial de compra. |
| H13-08 | Defecto resuelto y verificado en PG18.4 | 5/5 reproducciones previas y corrección a una sentencia aceptada primero en 08. Revalidación de 5 intercalaciones y 25 lecturas/22 commits independientes. Snapshot de sentencia, sin garantía global de página/destinos. |
| D11 | Resuelto y verificado en el alcance del historial enlazado | V15–V22 mensajes, no filas ante filtros inválidos, sin 500 y recuperación; variantes/extremos y rechazo sin mutación en servidor/PG. No cierra todo ventas. |

| Propuesta | Disposición final y límite |
|---|---|
| PROP-13-PANEL-CONTRATO | Técnica aceptada, implementada y verificada para CP002; caso actualizado en 08 con el alcance demostrado. No aprueba CP001 ni todo CT. |
| PROP-13-LINK-CONTEXTO | Técnica aceptada, implementada y verificada; se conserva consulta general explícita, conciliada con Fecha exacta. No requiere un reporte nuevo. |
| PROP-13-CORTE-CONSISTENTE | Técnica aceptada, implementada y verificada en PostgreSQL18.4; el defecto vigente no se traslada a otra etapa. Compatibilidad con el motor objetivo17 queda sin certificar, como límite de entorno. |
| PROP-13-NFR-CONSULTA | Investigación técnica completada para muestra declarada. Sin índice/caché añadido: mediciones locales no justifican esa complejidad. Volumen real y SLA continúan investigación operacional, sin inventarlos ni prometer rendimiento de producción. |
| PROP-13-MENSAJES | Técnica aceptada, implementada y verificada: igualdad, recepción, error recuperable, foco/teclado y pantalla estrecha de las superficies revisadas. |
| PROP-13-FUTUROS-REFINAR | Futuro explícitamente fuera del alcance actual. Selección comercial y refinamiento de reportes, ranking, margen, PDF, Yape y configuración pendientes; no bloquean el panel mínimo ni se declaran entregados. |

No queda defecto vigente demostrado del panel o sus consultas comprometidas sin resolver. La evidencia de servidor/PG se conserva con fecha y hashes originales; la nueva UI completa lo que faltaba. Etapa 13 FINALIZADA en primera pasada, alcance mínimo. Próximo cursor 14, sin ejecutarlo ni iniciar segunda pasada.
