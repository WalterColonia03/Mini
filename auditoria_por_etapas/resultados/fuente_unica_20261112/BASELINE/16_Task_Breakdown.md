# 16. Trabajo pendiente y dependencias vigentes

> **Vigente: 12/11/2026 · conciliación documental autorizada.** Requisito aceptado no equivale a implementación o verificación. [Mapa y decisiones](auditoria_por_etapas/resultados/conciliacion_20261112/CONSOLIDACION.md) · [Encargos verificables](auditoria_por_etapas/resultados/conciliacion_20261112/ENCARGOS.md) · [Versión anterior íntegra](auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/16_Task_Breakdown.md). Jira no forma parte de este seguimiento.

Los67 IDs y216h del desglose original permanecen en BASELINE; no son trabajo ejecutado ni estimación vigente. Se reutilizan IDs de decisiones/tareas existentes para encargos sin colisión. Cada fila hereda el contrato de ENCARGOS y su matriz; no crea otra HU. Estado salvo la fila documental: ACEPTADO, implementación no autorizada en esta fase. Costo relativo se evalúa al refinar; no inventar SP, horas o responsables.

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

Primero diagnóstico reproducible de datos y contratos de recepción/costos/ventas; luego persistencia y servicios, después consultas/UI, y finalmente pruebas de aceptación por rol/integrales. Se pueden preparar pruebas, formularios y especificación en paralelo cuando no dependen de datos pendientes. El orden de locks se establece globalmente, no por parches aislados.

Un encargo está listo para implementar cuando entradas/roles/efectos/errores/legado están definidos, dependencia técnica satisfecha o planificada, y existe autorización de implementación. Tráfico/retención/normativa/despliegue mantienen investigación C antes de fijar parámetros. Las correcciones nuevas aquí no se aplican automáticamente al código.

La fila DOC00-01 tiene implementación documental en este corte y verificación estructural propia; no implica cierre de entrega software. Las pruebas existentes que consagran valoración antigua o descuentos deben actualizarse junto al cambio autorizado, preservando el resultado histórico.
