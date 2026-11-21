# 16. Trabajo pendiente y dependencias vigentes

## Revalidación Etapa 07 (`07-B` · 14/11/2026 · consultas de stock, vencimientos y escala)

Sin cambios al producto en esta sesión (`r1-pmv` `f0d6fa81...`, `08` `ae58b33f...`, vistas `07/09/03` regeneradas sin errores): revalidados en servidor (`652/652 OK`, `128/128` integración, sondas `probes-07b.json`), Chrome real (`7/7` vacío + `41/41` poblado/móvil) y PostgreSQL `18.4` (`5/5` aislado + concurrencia `checkout_sale` + `PT-SEARCH-01` `2,001`/`20,002` lotes). Permanece abierto el incumplimiento contractual `DEC-07-VENCIDOS-FILTRO` / `HU-PROD-06/CA-03` (tabla única combinada ante `?dias=7`, alternativas A/B/C documentadas) y quedan como **`PROPUESTA`** sin aprobar ni implementar: `PROP-07-DEC07-SEPARACION-01`, `PROP-07-ESCALA-PAGINACION-01` (cuello real `2,0–4,4 MB` HTML + `prefetch` `20k` frente a `30–120 ms` SQL), `PROP-07-IDX-01` (`648 kB` efectivo solo junto a paginación/agregación), `PROP-07-MOBILE-01` (recorte horizontal tabla/nav en `390×844`), `PROP-07-FILTRO-UX-01` y `PROP-07-ALERTAS-INACTIVOS`. Cursor local: `07-C-DEC-07-VENCIDOS-FILTRO`. [Informe 07-B](auditoria_por_etapas/resultados/ETAPA-07.md#reval-07-b-20261114) · [Disposiciones 07-B](auditoria_por_etapas/resultados/soporte/07-B-inventario-y-disposiciones.md).

## Sublote 02-E · 14/11/2026 · sesión, personal y auditoría técnica (`H02E-01..04`)

Implementado y verificado dentro de `identity/` (`check=0`, `makemigrations --check=0`, `652/652 OK`, Chrome `1366×768` + `390×844` `29/29` + `10` acciones auditadas, `5/5` PostgreSQL `18.4`): `H02E-01` (`/salir/` condicional y atomicidad con `SaleDraft.Status.DISCARDED`/`CashShift`), `H02E-02` (`employee-state-confirm` + `.summary-list` móvil), `H02E-03` (conservación de `LoginAttempt` en reactivación/renombre, purga de sesiones en reset, `unlock_account` explícito auditado) y `H02E-04` (`IdentityAuditEvent` `0006` + `RequestIdMiddleware` + `identity.audit` sanitizado con `persist_db=False` en rechazos HTTP). Permanece `PARCIAL` `DOC-02-04` por informe IDNA (`PROP-02E-IDNA-01`) y `PG 17`; `DOC-01-06/C-02` permanece `PARCIAL` global por `/admin/login/` (`01-F`), `SEC-15-RETENCION-01` y `SEC-15-OBS-01`; `DOC-02-03` (`display_name` vs nombres/apellidos) y `HU-LOG-01` (`W`) quedan documentados con alternativas sin alterar modelo ni exponer funciones futuras. Cursor local: `02-F-IDNA-Y-ETAPA15-SEC-01`. [Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) · [Disposiciones](auditoria_por_etapas/resultados/soporte/02-E-disposiciones.md).

## Sublote01-E · 14/11/2026 · revalidación primera pasada

S1-AUTH01-UI/SVC/AUTO y DOC-02-04: alinear correo de ingreso a254, probar cuenta254 y peticiones255/319/320/321 sin contador, conservar límites históricos como evidencia anterior. Corrección acotada de formulario/prueba; no modifica política deIDNA ni cuentas existentes. [Aceptación y resultados](auditoria_por_etapas/resultados/soporte/01-E-disposiciones.md). DOC-01-06 conserva tareas independientes de canal técnico, presupuesto de tráfico, retención y eventos. No marcar estas tareas ni etapa02/15 completas por esta corrección.

## Sublote 01-F · 14/11/2026 · superficie `/admin/`, tráfico, eventos y despliegue (`2cef34b5...`)

Ejecución de primera pasada ampliada sin cambios al producto (`128/128` `identity + audit01e_probes`, `25/25` Chrome, `5/5` PostgreSQL `18.4`, `7/7` HTTP, `5/5` sondas de seguridad): cierra evidencia empírica de `CP-HU-AUTH-01-002` y `CP-HU-AUTH-02-001` en muestra aislada/PG y deja `CP-DOC-01-06-001` ABIERTO (`C-01` INCUMPLE bypass `/admin/login/`, `C-02` PARCIAL sin evento en `/admin/login/` ni sumidero durable, `C-03` CUMPLE en sonda aislada). Permanecen abiertas para `15`/autorización explícita: `SEC-15-ADMIN-01` (perímetro `/admin/` y unificación de sesión/bloqueo), `DOC-01-04` (orden Argon2 vs `locked_until`), `SEC-15-TRAFICO-01` (`HTTP-07`), `SEC-15-RETENCION-01` (acumulación `LoginAttempt`/`IdentityAuditEvent`), `SEC-15-OBS-01` (persistencia/sumidero de logs y `/admin/`), más estáticos con `DEBUG=False` (`StaticFilesHandler`/`collectstatic`) y detalles menores (`identity/tests.py` nombres de cookie fijos, UX `.skip-link`/barra `390×844` y `/favicon.ico`). Próximo cursor: `01-G-DESPLIEGUE-Y-CONTRATO-01`. [Informe 01-F](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-f) · [Disposiciones](auditoria_por_etapas/resultados/soporte/01-F-inventario-y-disposiciones.md).

## Revalidación puntual Etapa 06 · 14/11/2026 · inventario y recepción posterior

Sin edición de producto en esta sesión: verificados `DOC-03AB/03AH/03AI-01` y `DEC-05-LOTE-ESPACIOS` en build estabilizado `4d1c9637...` (`583/583` pruebas Django ejecutadas: `82/82` + `4/4` `inventory`, `497/497` resto incl. `identity`; `11/11` servidor; `93/93` Chrome; `10/10` PostgreSQL `18.4`). Quedan como propuestas trazables de interfaz/formulario (sin aplicar): `PROP-06-UI-MOVIL-01` (`overflow-wrap: anywhere` en columna de lote `64` chars de `stock_receipt.html` en `1366×900` y `390×844`, tras resolverse externamente en `app.css` la compresión vertical `<dd>` de `"S/ 3,12"`), `PROP-06-TOPBAR-01` (`<h1>` específico para `stock-receipt` y navegación móvil), `PROP-06-FORM-01..03` (resumen accesible de errores `#stock-entry-errors`, coherencia tarjeta 2 con `min_num=1` y copy de prerrequisito en `stock_entry_form.html`), y `PROP-06-CTA-01` (`button-secondary` en `stock_overview.html`). `PG 17`, `SIGKILL`, `HU-SOL-*` (`W`) y datos operativos mantienen sus alcances. [Adenda ETAPA-06](auditoria_por_etapas/resultados/ETAPA-06.md#adenda-06-20261114).

## Corte vigente14-CIERRE · 14/11/2026 Lima

Cerradas en integración14 las tareas de historia/reenvío de ajuste, lote nuevo, costoQ0, límites monetarios y checks seleccionados; corregidos formatos de precio y recuperación histórica. Migración0011 y cash0004/sales0007 comprobadas en bases ficticias;634tests,157checkpointsChrome,19PG. Las tareas de seguridad global, recuperación ante muerte de proceso, despliegue/CI, datos operativos y dispositivos conservan etapa15. No se cierran historias futuras ni las auditorías individuales por extensión.

[Informe y evidencia](auditoria_por_etapas/resultados/ETAPA-14.md#cierre-14) · [Ajustes](auditoria_por_etapas/resultados/soporte/14-CIERRE-ajustes.md) · [Dinero](auditoria_por_etapas/resultados/soporte/14-CIERRE-dinero.md). Las secciones fechadas anteriores se conservan como antecedentes.


> **Fuente funcional principal:** [08 · planificación unificada](08_Historias_de_Usuario.md). Las fichas, RN y contratos de08 definen lo esperado; este documento conserva su papel de contexto, diseño, ejecución o evidencia. Las vistas07/09/03 se derivan de08.


> **Vigente: 12/11/2026 · conciliación documental autorizada.** Requisito aceptado no equivale a implementación o verificación. [Mapa y decisiones](auditoria_por_etapas/resultados/conciliacion_20261112/CONSOLIDACION.md) · [Encargos verificables](auditoria_por_etapas/resultados/conciliacion_20261112/ENCARGOS.md) · [Versión anterior íntegra](auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/16_Task_Breakdown.md). Jira no forma parte de este seguimiento.

Los67 IDs y216h del desglose original permanecen en BASELINE; no son trabajo ejecutado ni estimación vigente. Se reutilizan IDs de decisiones/tareas existentes para encargos sin colisión. Cada fila hereda el contrato normativo de08 y su matriz derivada03; no crea otra HU. El estado del corte documental del 12/11, salvo su fila documental, fue ACEPTADO con implementación pendiente de autorización. La tabla final de 14-D registra las correcciones autorizadas y ejecutadas en esa sesión. Costo relativo se evalúa al refinar; no inventar SP, horas o responsables.

| ID original | Prioridad | Resultado verificable | HU/RN/vínculo | Dependencias antes de aceptar entrega | Pruebas mínimas |
|---|---|---|---|---|---|
| DOC-03AH-01 | P0 | Valoración coherente | RN14/28; INV01a/b/02/03, VEN01c | Diagnóstico de valoración y costos legacy | unitarias secuencia/zero; carreras; rollback |
| DOC-03AI-01 | P0 | Recepción propia y reintentos | RN01/14/19; INV01a/b/04 | DOC-03AB-01, DOC-03AH-01; informe lote/entrada | doble POST igual/divergente; colisiones; pérdida respuesta |
| DEC-11-MODELO-AUDITORIA-VENTAS | P0 | Asignaciones lote y snapshots | RN25/26/28; VEN01c/02a, INV04 | Modelo movimientos e informe legado | FEFO multilote; atomicidad completa; historia |
| DEC-11-DESCUENTOS-ALCANCE | P0 | Suspender nuevos descuentos | VEN01b/c/02a/05a/b; RN25/27 | Distinguir nueva operación/reintento histórico | manipulación; histórico; caja/IGV/reintento |
| PROP-09-DB-01 | P0 | Checks de caja/borrador | PROP-10-04; CAJA02/VEN01b | Diagnóstico de datos inválidos | DB directa; diferencia negativa válida; rollback |
| CT-ROLLBACK-01-POST-ESCRITURA | P0 | Concurrencia y caída real | RN25; SEC-15-CONC-02; INT/E2E | PG17 aislado; barrera observable | muerte postwrite/precommit; recuperación; reintento |
| DEC-12-PERMISOS-HISTORIAL-Y-MENU | P1 | Permisos y consulta por rol | RN07/29; PROD01,CAJA05,VEN05a/b | Matriz vigente | roles/propiedad; menú; URL directa sin datos |
| DOC-02-04 | P1 | Personal/reset/revocación | USR02..05; RN12/17/24/29 | Eventos técnicos; dominio correo/colisiones | cookies; bloqueo tras rename; concurrencia; confirmación |
| DOC-01-06 | P1 | Portal/tráfico/eventos | SEC15ADMIN/TRAFICO/OBS/RETENCION | Entorno/IP/volumen/finalidad reales | perímetro; logs sin secretos; transacción y fallo |
| DEC-10-BLOQUEO-INACTIVIDAD | P1 | Bloqueo300s del puesto | VEN01a; RN22 | Sesión y reloj servidor; revocación | pestañas; reloj; preservación borrador; reautenticación |
| DEC-11-TOPE-EFECTIVO-FORM | P1 | Límites operación y acumulado | CAJA01/02; VEN01c; RN10/27 | PROP-09-DB-01 | máximo±centavo; cierre con suma superior a venta |
| RN-05 | P1 | Causa de baja y ajuste nuevo | INV02/03; RN03/04/05/14/20 | DOC-03AH/AI; costo/fecha fiables | vencido robado; ajuste vencido no vendible; carrera |
| DEC-05-LOTE-ESPACIOS | P1 | Identidad de lote y límites | INV01a/b; PROP05/06VALID | Informe colisiones; DOC03AI | normalización; fronteras; datos legacy |
| DEC-08-KARDEX-COMPRAS | P1 | Movimientos y saldo fiable | INV04; RN25 | Asignaciones/recepción; diagnóstico historia | saldo apertura; filtros/páginas; origen desconocido |
| DEC-08-CONSTANCIA-MERMA | P2 | Constancia de baja | INV02/CA04 | RN-05; idempotencia | consulta/impresión/roles; inmutabilidad |
| DEC-04B-ESTADO-OMITIDO | P1 | Proveedor destino explícito | PROV04; DEC04RUCVALIDACION | Actor lock; contrato proveedor | omisión/alteración/repetición; no mutación |
| DEC-12-ORDEN-LINEAS-RECIBO | P2 | Orden, filtros y paginación | VEN02a/05a/b; CAJA05; PROP12ORDEN | Posición/snapshots; medición volumen | empates; 25/26filas; filtro; legado |
| DEC-07-VENCIDOS-FILTRO | P2 | Alertas y vencidos separados | PROD06; DEC07INACTIVOS/DASHDIAS | Definición físico/vendible | medianocheLima; inactivos; etiquetas/conteos |
| PROP-10-03 | P2 | GET informativo y revisión precio | VEN01b/c; RN30 | Firma del borrador | GET no muta; pestaña vieja; cambio concurrente |
| S1-OPS-DB-01 | P1 | Despliegue/backup/restauración | S1-CI-01/ST-BASE/PG17 | P0/P1, ambiente y acceso autorizados | CI real; restauración clon; smoke; seguridad |
| DOC-00-01 | P1 | Trazabilidad y revisión documental | DOC00-05/07/08/09/12/13; PROP05GEVID | Todos los contratos | IDs/enlaces; hashes; no cierre indebido |

## Secuencia y preparación

La tarea DEC-07-VENCIDOS-FILTRO incluye la regresión del panel mínimo. Contrastar las siete cifras de ADMIN, las tres de ALMACENERO y las opciones de VENDEDOR con el servidor, el estado de las filas y el destino de cada enlace. Comprobar fecha, recarga tras un cobro y acceso denegado. CP002 tiene ejecución verificada en primera pasada 13-B-final, limitada al caso; CP001 no se aprueba por extensión. [Caso escrito](08_Historias_de_Usuario.md#CP-DEC-07-VENCIDOS-FILTRO-002) · [Evidencia y límites](auditoria_por_etapas/resultados/ETAPA-13.md).

13-B completó la revalidación visual del build final, cobro de una fixture independiente, vacíos/error/permisos/D11 y consistencia/volumen PostgreSQL18.4. Las correcciones técnicas aceptadas abarcan claridad del enlace general y del umbral, recepción, fallo recuperable, validación de fechas del historial y una sentencia para las métricas del rol. No amplían a HU-DASH/REP/CONF ni cierran destinos completos. El bloqueo anterior de navegador quedó superado y se conserva con sus evidencias fechadas. PostgreSQL17, volumen real/SLA y despliegue mantienen sus límites. Etapa13 finalizada para el alcance mínimo; la continuación14-D se documenta debajo. [Disposiciones finales](auditoria_por_etapas/resultados/soporte/13-B-disposiciones.md).

Primero diagnóstico reproducible de datos y contratos de recepción/costos/ventas; luego persistencia y servicios, después consultas/UI, y finalmente pruebas de aceptación por rol/integrales. Se pueden preparar pruebas, formularios y especificación en paralelo cuando no dependen de datos pendientes. El orden de locks se establece globalmente, no por parches aislados.

Un encargo está listo para implementar cuando entradas/roles/efectos/errores/legado están definidos, dependencia técnica satisfecha o planificada, y existe autorización de implementación. Tráfico/retención/normativa/despliegue mantienen investigación C antes de fijar parámetros. Las correcciones nuevas aquí no se aplican automáticamente al código.

La fila DOC00-01 tiene implementación documental en este corte y verificación estructural propia; no implica cierre de entrega software. Las pruebas de descuentos se actualizaron en 14-D junto al cambio autorizado y con evidencia histórica preservada. Las de valoración antigua requieren el mismo tratamiento al completar DOC-03AH-01.

## Encargo transversal de veracidad visible

CT-COHERENCIA-UI, aceptado por solicitud expresa: inventariar literal/ruta/rol/estado, enlazar requisito y prueba, comparar servidor/persistencia y siguiente rol. Corregir textos o comportamiento según08 cuando se autorice implementación; no rebajar criterios para justificar un bug. Casos CP-VISIBLE-001..004. Entrega: evidencia por fila y pendientes sin ocultar. La actualización documental del 12/11 quedó terminada. El recorrido de 14-D aporta evidencia conectada y mantiene parciales los contratos consignados en la tabla siguiente.

## Estado de tareas tras14-D · 13/11/2026

| ID existente | Trabajo verificado del sublote | Pendiente |
|---|---|---|
| DEC-11-DESCUENTOS-ALCANCE | Implementado nuevo cobro sin descuento y recuperación de venta histórica. Regresión servidor y Chrome acreditan el alcance del informe | Concurrencia y caídas conservan etapa 15 |
| RN-05 | Corregida validación de causa/fecha/detalle. Robo explicado de vencido admitido. Vencimiento prematuro rechazado | Costo de salida, ajuste de lote nuevo, constancia y carreras |
| CT-ROLLBACK-01-POST-ESCRITURA | C-03 tiene nueva evidencia del recorrido por roles y rechazos sin mutación | C-01/02 y restoC-03 pendientes de PostgreSQL, caída, backup/restauración, CI y despliegue |
| DOC-00-01 | IDs de14-A corregidos en anexo vigente, caso conectado en08 y vistas regeneradas. C16 obtiene venta por identidad de operación | Conciliación completa en17 y segunda pasada |
| DOC-03AH-01 / DEC-11-MODELO / DEC-08-KARDEX | Brechas reobservadas al seguir la misma venta y merma | Cursor14-E-KARDEX-01. Primero costo/orígenes y asignaciones, después saldos/filtros/paginación |
| DEC-08-CONSTANCIA-MERMA | El correlativo y registro de baja aparecen en movimientos | Constancia dedicada inmutable |

Las filas complementan el corte documental anterior. El estado general de aceptación de las otras tareas conserva sus límites. El nuevo caso CP-INTEGRACION-ROLES-001 es una tarea de verificación sustentada en HUs/RN vigentes. [Evidencia y decisiones](auditoria_por_etapas/resultados/soporte/14-D-disposiciones.md).

## Estado de tareas tras14-E · 13/11/2026

Este corte continúa14-D sin modificar la aceptación general de otros módulos. [Informe vigente](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-e) · [Disposiciones](auditoria_por_etapas/resultados/soporte/14-E-disposiciones.md).

| ID existente | Trabajo implementado y revalidado | Pendiente |
|---|---|---|
| DOC-03AH-01, RN-14/28 | Q físico en recepción, promedio constante en salidas, cero al agotar, snapshot de venta/baja/ajuste. C-01..03 muestra secuencial, C-04 rollback por excepción | CapturaQ0 de costo fiable documentado, valoración operativa de legado, concurrenciaPG y caída real |
| RN-05 | Captura de costo histórico de baja y ajuste, migración nullable sin backfill ensayada | Ajuste con lote nuevo, constancia dedicada, inmutabilidad y carreras |
| CT-ROLLBACK-01-POST-ESCRITURA | Fallo sintético tras escritura real en cuatro servicios, sin efectos persistidos | Caída de proceso, recuperación/backup y conexiones concurrentes en15 |
| DEC-11-MODELO-AUDITORIA-VENTAS | Costos de venta conservados tras nuevos ingresos y agotamiento | Asignaciones reales por lote, snapshots vendedor/caja y orden histórico: cursor14-F-ASIGNACIONES-01 |
| DOC-03AI-01, DEC-08-KARDEX-COMPRAS | Dependencia de valoración parcialmente resuelta | Recepción propia/idempotente, identidad comercial de lote, orígenes durables y saldo/filtros/paginación |

La propuesta de diagnóstico read-only se conserva en el inventario14-E. Su diseño no equivale a un diagnóstico ejecutado de datos reales. Las tareas de14-F requieren selección e implementación técnica con evidencia; no se consideran entregadas por describirlas.

## Estado de tareas tras14-F · 13/11/2026

| Tarea existente | Resultado verificado | Pendiente |
|---|---|---|
| DEC-11-MODELO-AUDITORIA-VENTAS | AsignacionesFEFO, snapshots de lote/vendedor/caja, posición, reenvío secuencial y ocho fallos postwrite. Sale como ingreso de efectivo conciliado con cierre | ConcurrenciaPG, caída real, protección de historia ante escritura directa |
| DEC-12-ORDEN-LINEAS-RECIBO | Orden de líneas persistido independiente deUUID, ausencia histórica declarada | Empate de turnos, paginación y demás tramos del contrato |
| DEC-08-KARDEX-COMPRAS/C-02 | Consulta interna de asignaciones completas, ausentes y parciales, costoNULL y permiso denegado | C-01 y paginación/filtros/totalesC-03, relación con recepciones propias |
| CT-COHERENCIA-UI, CP-INTEGRACION-ROLES-001 | Reejecución conectada44 checkpoints sobre build14-F, desde maestros hasta cierre. Escenario específico12 checkpoints | Impresión física, volumen y totalidad de contratos de cada HU |
| DOC-03AI-01 | Inventario y requisito previo disponibles | Cursor14-G-RECEPCIONES-01, identidad propia/idempotencia, lote comercial repetido e historia fiable |

[Inventario14-F](auditoria_por_etapas/resultados/soporte/14-F-inventario.md) · [Informe14-F](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-f). Los informes14-D/E conservan los resultados y el build de sus cortes. La regularización operativa de datos y el costo documentado de ajusteQ0 mantienen sus pendientes.

## Estado14-G · 13/11/2026 Lima

| Tarea existente | Ejecutado en muestra | Pendiente |
|---|---|---|
| DOC-03AI-01 / HU-INV-01b |Cabecera/líneas/contador,UUIDHTTP,huella,correlativos,reintentos,instantáneas,fecha coherente y rollback;584tests|ConcurrenciaPG,caída real,diagnóstico y datos operativos; nuevas cargas iniciales con historia fiable|
| DEC-05-LOTE-ESPACIOS/C01 |Normalización espacios sin fusionarAB12,comparación legado sin reescribir;10tests14-G con variantes|Inventario de colisiones operativas antes de migrar, protecciónbypass y resto deC02/C03|
| INV-04/CA02 |Origen de recepción enlazado y desconocido rotulado;selección merma/ajuste por procedencia|Cursor14-H-KARDEX-SALDOS-01:saldo cronológico/filtros/paginación con origen incompleto explícito|

Se preservaron fallos intermedios, dos regresiones reales corregidas y fixtures actualizadas según contrato. [Informe](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-g). No cerrar otrasHU por la suite global.


## Estado14-H1 · dependencia de Kardex

DOC03AI/INV01a: cabecera y líneas originales, migración sin backfill, separación original/actual, enlace desde movimientos, legado no cuantificado, cuatro fallos postwrite y ocho tests nuevos.592/592regresión;16+44+23checkpointsChrome. El nuevo CP-HU-INV-01a-003 aporta evidencia acotada y no cierra los cincoCA completos.

Siguiente14-H2-KARDEX-SALDOS-01: ordenar eventos por instante+ID, conciliar por lote, calcular antes de filtrar/paginar, páginas25, períodoLima/tipo/errores y saldos no disponibles ante origen incierto. Revalidar H1/G/F y cadena. PG/caída/defensaSQL/volumen y constancia demerma conservan sus tareas.

[Informe14-H1](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-h1) · [Fundamento y límites](auditoria_por_etapas/resultados/soporte/14-H-disposiciones.md).


## Estado14-H2 · 14/11/2026

DEC08/INV04: consulta derivada, conciliaciónporlote, apertura/cierre, filtros alminuto,tipo,página25,errores/duplicados,variación total, estadosdesconocidos y móvil.12tests nuevos;604/604regresión;20+44observacionesChrome.08casosactualizados;sinHU nueva ni migración.

14-I-MERMA-01: capturar constanciademerma yresultadoidempotente, preservarlegado, probarroles/errores/rollback yrevalidarKardex/costo/caja. Autorhistóricodeajustes/lote nuevo/costoQ0 siguen pendientespropios. Medirvolumen ylecturasconcurrentesPG en15; no cerrar esas tareas por paginar HTML.

[Informe14-H2](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-h2) · [Decisiones](auditoria_por_etapas/resultados/soporte/14-H2-disposiciones.md).


## Continuación14-I · 14/11/2026 Lima

RN-05 / DEC-08-CONSTANCIA-MERMA: vista, fotografías y reintento persistente implementados y verificados en muestra.10tests nuevos,614/614 de regresión,26+44 checkpointsChrome con conjuntos solapados. Tareas no cerradas: concurrenciaPG, protecciónSQL, recuperación, volumen, impresora física y diagnóstico operativo. Próximo14-J-AJUSTES-HISTORIA-01: fotografiar autor y lote de ajustes existentes, motivo y costo, conservar legado; revalidar Kardex y cadena. Lote nuevo/costo desde físico0 mantienen sublote propio posterior.

[Informe14-I](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-i) · [Disposiciones](auditoria_por_etapas/resultados/soporte/14-I-disposiciones.md).

## Estado 12-B (Etapa 12) · 14/11/2026 Lima

| Tarea existente | Trabajo verificado en muestra aislada (`12-B`) | Pendiente |
|---|---|---|
| `DEC-12-PERMISOS-HISTORIAL-Y-MENU` | Matriz `ADMIN`/`ALMACENERO`/`VENDEDOR A/B`/anónimo/cookie revocada en `/empleados/`, enlaces laterales vendedor, cero costos en constancia y `403`/`404` por URL directa | Tráfico/retención/despliegue global en Etapa `15` |
| `DEC-12-ORDEN-LINEAS-RECIBO` | Orden `3` líneas UUID inverso + aviso legado, desempate `CashShift`/`Sale`, paginación `25/26` con filtros preservados y total íntegro, revisión precio `C-04` en `/ventas/cobrar/`, teclado, `@media print` y `.receipt-table` móvil `390×844` | Medición SLA de volumen (`PT-SEARCH-01`), impresora térmica física y `PG 17` (`Etapa 15`) |
| `S1-OPS-DB-01` (parcial Etapa 12) | Round-trip migraciones `cash 0004<->0005` y `sales 0007<->0008` + `makemigrations --check --dry-run` sin cambios en `audit` | Respaldo y aplicación controlada en `r1-pmv/r1_pmv.sqlite3` / PostgreSQL productivo (`Etapa 15`) |

[Informe 12-B](auditoria_por_etapas/resultados/ETAPA-12.md#vigente-12-b).
