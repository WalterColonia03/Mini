# Control vigente de trabajo y Sprints · 12/11/2026

## Sublote 02-E · 14/11/2026 Lima (segunda pasada acotada · sesión y personal)

`identity/` incorpora `H02E-02..04` (`employee-state-confirm`, `.summary-list` móvil, conservación de `LoginAttempt`, purga de sesiones en reset, `unlock_account` y `IdentityAuditEvent` `0006` + `identity.audit` sanitizado) y revalida `H02E-01`: `check=0`, `makemigrations --check=0`, `652/652 OK` (`252.300s`), Chrome `29/29` + `10` acciones auditadas y `5/5` PostgreSQL `18.4`; `r1_pmv.sqlite3` intacta. Mantiene `HU-AUTH-04a/04b/05`, `HU-USR-06` y `HU-LOG-01` fuera de alcance y conserva `15-SEGURIDAD-BASELINE-01`. [Informe 02-E](../auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e).

## Corte vigente14-CIERRE · 14/11/2026 Lima

Cierre local14:634/634pruebas en132.064s,157checkpointsChrome en siete recorridos,19/19PostgreSQL18.4 aislado; fuentes estables. Ajustes, dinero y cadena revalidados. No apruebaCI/despliegue/operación; cursor15-SEGURIDAD-BASELINE-01.

[Informe y evidencia](../auditoria_por_etapas/resultados/ETAPA-14.md#cierre-14) · [Ajustes](../auditoria_por_etapas/resultados/soporte/14-CIERRE-ajustes.md) · [Dinero](../auditoria_por_etapas/resultados/soporte/14-CIERRE-dinero.md). Las secciones fechadas anteriores se conservan como antecedentes.


> **Fuente funcional principal:** [08 · planificación unificada](../08_Historias_de_Usuario.md). Las fichas, RN y contratos de08 definen lo esperado; este documento conserva su papel de contexto, diseño, ejecución o evidencia. Las vistas07/09/03 se derivan de08.


[Planificación vigente](../09_Product_Backlog.md) · [Planning siguiente incremento](../14_Sprint_Planning.md) · [Tareas/dependencias](../16_Task_Breakdown.md) · [Registro histórico íntegro](../auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/r1-pmv/CONTROL_SPRINTS.md).

S1/S2/S3 y sus marcas «completada» son cortes históricos. No se heredan como DoD actual. No existe aquí evidencia de nuevas fechas/capacidad/equipo ni un Sprint nuevo iniciado.33 HU seleccionadas para R1 de consolidación;41 futuras y ocho ideas fuera. Reactivar empleado corresponde a HU-USR-05, no HU-USR-04. Kardex corresponde a INV04; descuentos no a VEN03; bloqueo ingreso15min no es pantalla300s.

Decisiones12/11 aceptadas por delegación, implementación separada.434 pruebas integradasSQLite y muestraPG18.4 no cierran los cambios nuevos. Estado de auditoría en ESTADO_GENERAL; evidencia en04. No se usa Jira. SP originales231 y216h de67tareas no son velocidad ni horas reales; no se suman a nuevas estimaciones.


## Revalidación14-H2 · 14/11/2026 Lima

Kardex secuencial: saldo/filtros/paginación y origen desconocido verificados;604/604regresión,20+44observacionesChrome. H1yaaportó fotografía inicial. Etapa14parcial;14-I-MERMA-01. Historiadeajustes,PG/volumen y datosoperativos siguenpendientes. [Informe](../auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-h2).


## Continuación14-I · 14/11/2026 Lima

Revalidación local14-I:614/614 pruebas,26 checkpointsChrome específicos y44 de cadena; conjuntos solapados. Constancia y reintento de merma resueltos en muestra. Etapa14 parcial y próximo14-J-AJUSTES-HISTORIA-01. No acredita despliegue, PostgreSQL concurrente ni cierre de otros módulos.

[Informe14-I](../auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-i) · [Disposiciones](../auditoria_por_etapas/resultados/soporte/14-I-disposiciones.md).

## Revalidación Etapa 12 (12-B) · 14/11/2026 Lima

Revalidación en muestra aislada del tramo constancias e historiales (`HU-VEN-02a`, `05a`, `05b`, `HU-CAJA-05`, `DEC-12-PERMISOS-HISTORIAL-Y-MENU` y `DEC-12-ORDEN-LINEAS-RECIBO`): `85/85` en suite Django del tramo (`cash`/`sales`/`14b`), `12/12` verificaciones Chrome (`1366×900`, `1366×768`, `390×844` y `@media print`, incluido ajuste CSS móvil de `.receipt-table`) y PostgreSQL `18.4` (`4→4`, `7→7`, `26` registros paginados a `25`, doble `POST` concurrente = `1` venta, corte medianoche Lima). Conserva `S1/S2/S3` solo como registro histórico; las tareas operativas de `PG 17`, SLA real, impresora térmica física y aplicación de migraciones sobre `r1_pmv.sqlite3` quedan pendientes en Etapa `15`. [Informe 12-B](../auditoria_por_etapas/resultados/ETAPA-12.md#vigente-12-b).
