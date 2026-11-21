# 4. Evidencias vigentes y procedencia

> **Fuente funcional principal:** [08 · planificación unificada](08_Historias_de_Usuario.md). Las fichas, RN y contratos de08 definen lo esperado; este documento conserva su papel de contexto, diseño, ejecución o evidencia. Las vistas07/09/03 se derivan de08.


> **Vigente: 12/11/2026 · conciliación documental autorizada.** Requisito aceptado no equivale a implementación o verificación. [Mapa y decisiones](auditoria_por_etapas/resultados/conciliacion_20261112/CONSOLIDACION.md) · [Encargos verificables](auditoria_por_etapas/resultados/conciliacion_20261112/ENCARGOS.md) · [Versión anterior íntegra](auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/04_Evidencias.md). Jira no forma parte de este seguimiento.

## Sublote 07-B (primera pasada acotada · 14–15/11/2026)

Sin editar `r1-pmv/` (`f0d6fa81...`, `0` modificaciones en módulos de Etapa 07; `r1_pmv.sqlite3` intacta; `08` `ae58b33f...`, vistas `07/09/03` regeneradas sin errores): [Informe 07-B](auditoria_por_etapas/resultados/ETAPA-07.md#reval-07-b-20261114) · [Anexo e inventario](auditoria_por_etapas/resultados/soporte/07-B-inventario-y-disposiciones.md#vigente-07-b-inventario) · [Checks `0`](auditoria_por_etapas/resultados/evidencias/07-checks-20261115T030006326519Z-0bd8334a/summary.json) · [Suite `652/652 OK`](auditoria_por_etapas/resultados/evidencias/07-tests-20261115T030019474414Z-07d23f68/test_output.txt) · [Integración/sesión `128/128 OK`](auditoria_por_etapas/resultados/evidencias/07-tests-20261115T025754350067Z-c399928f/test_output.txt) · [Sondas servidor](auditoria_por_etapas/resultados/evidencias/07-B-20261114/probes-07b.json) · [Campos/cabeceras HTTP](auditoria_por_etapas/resultados/evidencias/07-B-20261114/probes-07b-fields-headers.json) · [Chrome `48/48`](auditoria_por_etapas/resultados/evidencias/07-B-20261114/browser-07b-summary.json) · [PostgreSQL `18.4` (`5/5`)](auditoria_por_etapas/resultados/evidencias/07-postgresql-20261115T025829083471Z.json) · [Bench `PT-SEARCH-01` `2,001`/`20,002` (`c7bfe1fa...`)](auditoria_por_etapas/resultados/evidencias/07-B-20261114/pg-bench-07b-20261115T024804Z.json). Revalida `RN-03`, `RN-06` y `H13-02`; confirma incumplimiento abierto de `DEC-07-VENCIDOS-FILTRO` (`C-02`) y `HU-PROD-06/CA-03` (`EXP_7_ROWS: 3`, `SEPARATE: False`) y cuello de botella HTTP (`3,56–3,63 s` sin paginar); mantiene `NO EJECUTADO` `PG 17` (ausente en host), SLA `NFR-05` post-paginación e historias `W`.

## Sublote 02-E (segunda pasada acotada · 14/11/2026)

[Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) · [Servidor (`652/652 OK` en `252.300s`)](auditoria_por_etapas/resultados/evidencias/02-E-20261114/servidor/INFORME.md) · [Navegador Chrome (`29/29` + `10` acciones + móvil `390×844`)](auditoria_por_etapas/resultados/evidencias/02-E-20261114/navegador/INFORME.md) · [PostgreSQL `18.4` (`5/5` COMPLETE)](auditoria_por_etapas/resultados/evidencias/02-E-20261114/postgresql/INFORME.md) · [Diagnóstico pre-edición](auditoria_por_etapas/resultados/evidencias/02-E-20261114/diagnostico-antes.json) · [Build final](auditoria_por_etapas/resultados/evidencias/02-E-20261114/build-final.json). Conserva límites explícitos de `PG 17`, `/admin/login/`, sumidero durable/retención (`SEC-15`), estudio IDNA y exclusión de funciones `W`.

## Código integrado

[Verificación12/11](auditoria_por_etapas/resultados/conciliacion_20261112/VERIFICACION.md):434/434 testsDjango sin fallos/errores/omitidos, SQLite nuevo;check y dry-run de migraciones aprobados.503 archivos protegidos conservados durante la ejecución. Primer intento de soporte fallido conservado aparte. Nueva muestraPG18.4: filtrosNUL/fechaLima, queries constantes y dos reintentos concurrentes→una venta; noHTTP sockets/no navegador.

## Auditorías por etapa

[Estado general](auditoria_por_etapas/resultados/ESTADO_GENERAL.md) enlaza13 informes originales00–12 con adendas vigentes;13–17 están pendientes. La conciliación anterior se conserva como antecedente documental y no como ejecución de17. Cada informe conserva herramientas,base,muestras,omisiones y anexos; no sumar sus contadores ni trasladar aprobación a contratos nuevos. Los artefactos principales antiguos se mantienen en sus rutas; BASELINE conserva documentos de procedencia.

## Documentación nueva

[InventarioCA](auditoria_por_etapas/resultados/conciliacion_20261112/INVENTARIO_CA.json), [IDs y referencias](auditoria_por_etapas/resultados/conciliacion_20261112/INDICE_IDS.md), [validación estructural](auditoria_por_etapas/resultados/conciliacion_20261112/VALIDACION_DOCUMENTAL.json) y [manifiesto de cambios](auditoria_por_etapas/resultados/conciliacion_20261112/CAMBIOS.json). La aceptación de políticas no equivale a software implementado;60 CA suplementarios nuevos permanecen por verificar tras cambios autorizados.

## Ausencias y límites

XLSXausente;PG17/CI/backup-restore/despliegue/E2E actual completo/NFRvolumen/dispositivos y revisión independiente sin evidencia de cierre. Lo no ejecutado no se marca defecto. Las brechas comprobadas frente a HU seleccionadas sí se mantienen visibles. Las antiguas cifras0/191/202/etc. describen sus cortes originales; no se borran ni se presentan como ejecución actual.
