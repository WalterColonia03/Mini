# 14. Planificación vigente del siguiente incremento

## Revalidación Etapa 07 (`07-B` · 14/11/2026 Lima · stock, vencimientos y panel mínimo)

Revalidado sin cambios de código en `r1-pmv/` (`f0d6fa81...` / `c7bfe1fa...` idénticos en módulo `07`): `652/652 OK`, `128/128` integración/sesión, Chrome (`48/48` en `1366×900` + `390×844`), PG `18.4` (`5/5`) y `PT-SEARCH-01` (`2,001`/`20,002`). Quedan documentados sin editar producto el incumplimiento de separación «Próximos» vs «Vencidos» (`DEC-07-VENCIDOS-FILTRO` / `HU-PROD-06/CA-03`, alternativas A/B/C), el cuello de botella real de paginación HTML frente al índice parcial (`PROP-07-ESCALA-PAGINACION-01` + `PROP-07-IDX-01`), los ajustes móviles `390×844` (`PROP-07-MOBILE-01`) y las futuras `HU-DASH`/`HU-REP` (`W`) sin rutas. Cursor local: `07-C-DEC-07-VENCIDOS-FILTRO`. [Informe 07-B](auditoria_por_etapas/resultados/ETAPA-07.md#reval-07-b-20261114) · [Disposiciones](auditoria_por_etapas/resultados/soporte/07-B-inventario-y-disposiciones.md).

## Actualización 02-E · 14/11/2026 Lima (segunda pasada acotada · sesión y personal)

`identity` incorpora `H02E-02..04` y revalida `H02E-01` (`652/652 OK`, Chrome `1366×768` + `390×844` y `5/5` PostgreSQL `18.4`), manteniendo `HU-AUTH-04a/04b/05`, `HU-USR-06` y `HU-LOG-01` como futuras (`W`, no disponibles) y dejando abiertos para Etapa `15` la paridad `/admin/login/`, sumidero/retención de `IdentityAuditEvent` (`SEC-15-RETENCION-01`/`OBS-01`), informe IDNA y `PG 17`. [Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) · [Disposiciones](auditoria_por_etapas/resultados/soporte/02-E-disposiciones.md).

## Corte vigente14-CIERRE · 14/11/2026 Lima

Etapa14 COMPLETADA para la cadena conectada y sus variantes delimitadas. El cierre usa el build congelado y evidencia reproducible, no solo el estado del sprint. Próximo15-SEGURIDAD-BASELINE-01: inventariar permisos/sesiones/entorno/respaldos y no atribuir como nuevos los19casosPG de14. No desplegar ni migrar datos operativos a partir de este informe.

[Informe y evidencia](auditoria_por_etapas/resultados/ETAPA-14.md#cierre-14) · [Ajustes](auditoria_por_etapas/resultados/soporte/14-CIERRE-ajustes.md) · [Dinero](auditoria_por_etapas/resultados/soporte/14-CIERRE-dinero.md). Las secciones fechadas anteriores se conservan como antecedentes.


> **Fuente funcional principal:** [08 · planificación unificada](08_Historias_de_Usuario.md). Las fichas, RN y contratos de08 definen lo esperado; este documento conserva su papel de contexto, diseño, ejecución o evidencia. Las vistas07/09/03 se derivan de08.


> **Vigente: 12/11/2026 · conciliación documental autorizada.** Requisito aceptado no equivale a implementación o verificación. [Mapa y decisiones](auditoria_por_etapas/resultados/conciliacion_20261112/CONSOLIDACION.md) · [Encargos verificables](auditoria_por_etapas/resultados/conciliacion_20261112/ENCARGOS.md) · [Versión anterior íntegra](auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/14_Sprint_Planning.md). Jira no forma parte de este seguimiento.

## Situación real

Existe una versión integrada con434 pruebas automáticas aprobadas en SQLite aislado y evidencia histórica por etapas; también existen brechas P0/P1 y criterios recién revisados. No hay evidencia suficiente para declarar release listo ni un Sprint actual terminado. Las fechas10–23octubre, seis Developers,40 SP,216h,192/240h de capacidad y tarifa académica son cortes históricos, no compromisos ni mediciones actuales.

## Objetivo propuesto para el próximo Sprint

Conseguir que cada entrada y venta conserve origen, costo y cantidades coherentes, con reintentos seguros y permisos comerciales inequívocos. Es una propuesta de objetivo, no un Sprint ya iniciado. La selección concreta corresponde al equipo al conocer capacidad y estimar trabajo restante; no se comprometen todos los21 encargos a un único Sprint.

Candidatos iniciales: DOC03AH (valoración), DOC03AI (recepción), DEC11MODELO (asignaciones/snapshots) y checks críticos; dependencias y pruebas en16. DEC11DESCUENTOS tiene implementación y revalidación en 14-D. Preparar simultáneamente diagnóstico de datos, pruebas y revisión de permisos. Bloqueo de pantalla, seguridad técnica y despliegue son condiciones antes del piloto aunque no quepan en ese primer incremento.

## Preparación y Definition of Done

Para seleccionar: criterio comprendido, dependencia/legado identificado, prueba verificable y tamaño estimado por quienes implementan. Para Hecho: código autorizado integrado, todos los CA seleccionados y suplementos cumplidos, pruebas apropiadas sin exclusiones ocultas, rechazo sin mutación, concurrenciaPG cuando proceda, navegador por roles, migración ensayada y reversible, docs/evidencia coherentes y revisión independiente. Una tarea documental terminada no cumple la DoD del software.

PG17 sigue objetivo; PG18.4 es evidencia parcial; SQLite no prueba locksPG. La aceptación de decisiones y una suite verde no levantan brechas de auditoría. CI, recuperación y despliegue deben tener resultados propios.

## Seguimiento

Para cambios de ventas, turnos, stock vendible o vencimientos, repetir las consultas del panel afectadas por el cambio. La primera pasada de la etapa 13 aportó un caso de regresión vinculado a DEC-07 y a la veracidad de las cifras por rol. [Caso del panel](08_Historias_de_Usuario.md#CP-DEC-07-VENCIDOS-FILTRO-002).

Resultado 13-B-final, 13/11/2026: corte de métricas contrastado con conexiones PostgreSQL18.4 independientes y volumen sintético declarado; aceptación visual del build final completada, incluido cobro por interfaz, vacíos/errores y teclado a 390 px. Etapa 13 finalizada para el panel mínimo y consultas acotadas; no equivale a la definición de Hecho del release completo ni entrega HU futuras. PostgreSQL17 y despliegue no certificados. El bloqueo anterior de navegador se conserva como antecedente superado. Este es el corte13. La continuación14-D se documenta debajo; segunda pasada pendiente. [Cierre y evidencia](auditoria_por_etapas/resultados/ETAPA-13.md#cierre-13-b-final).

Usar09 para necesidades/orden,16 para tareas/dependencias,03 para criterios,04 para evidencia y ESTADO_GENERAL para auditorías. Las decisiones vigentes y contratos se leen en08; CONSOLIDACION/ENCARGOS conservan mapa y procedencia. No duplicar estados en Jira. No asignar personas/fechas reales ni horas ejecutadas sin evidencia del equipo.

La Guía Scrum oficial define Product Backlog emergente, Sprint Backlog y Definition of Done; aplicar estos artefactos no acredita reuniones ni participantes inexistentes. Fuente y aplicabilidad en FUENTES_EXTERNAS.md.

## Concordancia con las fichas unificadas

08 contiene MoSCoW y Fibonacci orientativos por HU; total catálogo268SP y R1seleccionado146SP, sin compromiso de Sprint. Definición de preparación: HU seleccionada, criterios base y complementarios comprendidos, casos con datos/esperado, dependencias y legado diagnosticados. Definition of Done incluye CT-COHERENCIA-UI: mensajes, ayudas, acciones y salidas visibles corresponden a comportamiento comprobado por rol/estado, sin promesas incumplidas. Las41HU futuras siguen fuera de este incremento.

## Resultado y preparación14-D · 13/11/2026

El sublote conectado de etapa 14 ejecutó Chrome con tres roles, datos ficticios nuevos, peticiones HTTP reales y persistencia. Corrigió descuento nuevo, causa de merma y selección de venta en una prueba no determinista conforme a contratos existentes. La regresión final fue560/560 y el recorrido final44 checkpoints, con conjuntos de cobertura diferenciados en el informe. La etapa 14 permanece PARCIAL por valoración, asignaciones, Kardex y constancia de merma.

El próximo sublote 14-E comienza con DOC-03AH-01 y DEC-11-MODELO-AUDITORIA-VENTAS para sustentar DEC-08-KARDEX-COMPRAS. Se exige evidencia de lote/costo/origen/saldo en el recorrido ADMIN→ALMACENERO→VENDEDOR→ADMIN. El cursor exacto y las decisiones pendientes constan en el informe. [Caso escrito](08_Historias_de_Usuario.md#CP-INTEGRACION-ROLES-001) · [Disposiciones](auditoria_por_etapas/resultados/soporte/14-D-disposiciones.md) · [Estado14-D](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-d).

## Resultado y preparación14-E · 13/11/2026

El sublote de valoración corrigió recepción sobre físico, conservación del promedio en salidas y cero al agotamiento; agrega costos históricos de baja/ajuste sin rellenar legado. Resultado23/23 casos HTTP/servidor,23 checkpoints Chrome y566/566 pruebas de regresión, con alcances que se solapan. La etapa14 sigue PARCIAL.

Cursor14-F-ASIGNACIONES-01: comprobar venta que cruza dos lotes y ausencia histórica, implementar el mínimo de asignaciones durables y snapshots exigidos por DEC-11-MODELO, antes de enlazar recepción propia y saldo de Kardex. El costo ficticio demostrado no regulariza valoración operativa previa. [Inventario14-E](auditoria_por_etapas/resultados/soporte/14-E-inventario.md) · [Informe](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-e).

## Resultado y preparación14-F · 13/11/2026

Asignaciones por lote, fotografía de vendedor/caja y orden persistido fueron implementados y comprobados en14-F. La regresión completa574/574 y los recorridosChrome de12 y44 checkpoints tienen alcances solapados. La migración conserva los registros anteriores con datos históricos desconocidos.

El próximo cursor14-G-RECEPCIONES-01 aborda DOC-03AI y HU-INV-01b antes de completar Kardex. Preparar dos recepciones reales del mismo lote comercial y verificar referencias distintas, reintento idempotente, cantidades originales y snapshots de autor/proveedor. Origen incompleto de legado requiere clasificación explícita. [Informe14-F](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-f).

## Continuación14-G · 13/11/2026

Recepción propia e idempotencia implementadas y verificadas en muestraSQLite/Chrome; selección de procedencias y salida posterior revalidadas. La etapa14 siguePARCIAL. Siguiente14-H-KARDEX-SALDOS-01:reconstruir secuencia conocida de10+10+5−22−1,esperar2;filtrar período/tipo sin alterar saldo real,paginar25preservandofiltros,ydeclararorigenincompleto. Diagnóstico operativo,PG,caída y captura histórica de carga inicial conservan pendientes. [Detalle](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-g).


## Resultado y preparación14-H1

Se ejecutó primero la dependencia de fotografía inicial del Kardex. Cabecera/líneas nuevas conservan origen y cantidades; legado explícito.592/592regresión,16+44+23checkpointsChrome con conjuntos solapados. La etapa14 siguePARCIAL. El próximo sublote14-H2-KARDEX-SALDOS-01 mantiene los criterios de saldo/filtros/paginación; no se rebajaron para terminarH1. Preparar la secuencia10+10+5−22−1, período con apertura20 y más de25eventos. PG/recuperación/datos operativos y constancia demerma pendientes.

[Informe14-H1](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-h1) · [Fundamento y límites](auditoria_por_etapas/resultados/soporte/14-H-disposiciones.md).


## Resultado y preparación14-H2 · 14/11/2026

Kardex con saldo conocido,filtros,páginas25 ylegado explícito verificado enmuestra;604/604regresión y20+44observacionesChrome.6de7criterioscumplen enmuestra;CA03parcial porautorhistóricodeajustes. Etapa14parcial. Siguiente14-I-MERMA-01, HU-INV-02/CA04yRN05/C03: constancia propia inmutable,roles,reenvío,variantesy efectoscruzados. NoagregarhistorialesglobalesINV05/06futuros. Volumen/concurrencia/recuperación/datosoperativosconservanpendientes.

[Informe14-H2](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-h2) · [Decisiones](auditoria_por_etapas/resultados/soporte/14-H2-disposiciones.md).


## Continuación14-I · 14/11/2026 Lima

Sublote14-I concluye para constancia nueva de merma e idempotencia secuencial entre sesiones. La etapa14 sigue PARCIAL: no se completa por aprobar614tests. Preparar14-J-AJUSTES-HISTORIA-01 con A10@3, ajuste ADMIN+2 y−3, renombrados y errores sin mutación. No seleccionar historias globales INV05/06 o REP08; PostgreSQL/recuperación/datos operativos siguen pendientes.

[Informe14-I](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-i) · [Disposiciones](auditoria_por_etapas/resultados/soporte/14-I-disposiciones.md).

## Revalidación Etapa 12 (12-B) · 14/11/2026 Lima

En segunda revisión del tramo de constancias e historiales (`HU-VEN-02a`, `05a`, `05b`, `HU-CAJA-05`, `DEC-12-PERMISOS-HISTORIAL-Y-MENU` y `DEC-12-ORDEN-LINEAS-RECIBO`), quedaron ejecutados en muestra aislada SQLite (`85/85` en el tramo), Chrome escritorio/móvil `390×844`/`@media print` (`12/12` grupos, `0` errores) y PostgreSQL `18.4` (`4→4`, `7→7`, `26` turnos/ventas paginados a `25`, doble `POST` concurrente = `1` venta, límite `America/Lima`). No cambia compromisos de Sprint ni cierra `15–17`; `PG 17`, SLA productivo, impresora física, `SIGKILL` y migración operativa de `r1-pmv/r1_pmv.sqlite3` permanecen pendientes. [Informe 12-B](auditoria_por_etapas/resultados/ETAPA-12.md#vigente-12-b).
