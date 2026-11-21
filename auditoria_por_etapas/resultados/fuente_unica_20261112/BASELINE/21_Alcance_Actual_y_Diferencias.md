# 21. Alcance y diferencias vigentes

> **Vigente: 12/11/2026 · conciliación documental autorizada.** Requisito aceptado no equivale a implementación o verificación. [Mapa y decisiones](auditoria_por_etapas/resultados/conciliacion_20261112/CONSOLIDACION.md) · [Encargos verificables](auditoria_por_etapas/resultados/conciliacion_20261112/ENCARGOS.md) · [Versión anterior íntegra](auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/21_Alcance_Actual_y_Diferencias.md). Jira no forma parte de este seguimiento.

## Lo seleccionado y lo comprobado

La selección vigente es33 HU de09, con219 CA base en el catálogo completo y60 criterios suplementarios nuevos en ENCARGOS (más J-CA1..4 de categoría). Software actual y selección difieren.434 pruebas automáticas integradas pasaron en SQLite nuevo; check y makemigrations dry-run pasaron. Se revalidó un subconjunto de historial/idempotencia conPG18.4. Ningún resultado convierte los contratos revisados en implementados.

## Brechas prioritarias verificadas por inspección

| Área | Comportamiento actual / fuente | Requisito vigente | Trabajo |
|---|---|---|---|
| Entrada | register_stock_entry reutiliza carga y no tiene recepción propia | Entrada directa con identidad/idempotencia | DOC03AB/AI |
| Valoración | Entrada excluye vencidos y baja/ajuste repondera lotes restantes | Promedio móvil sobre físico; salidas conservan costo | DOC03AH |
| Venta | Descuenta lotes pero no persiste asignaciones; no snapshots vendedor/caja | RN25/26 con trazabilidad histórica | DEC11MODELO |
| Descuento | Campo/cobro permiten importe discrecional | Nuevas ventas sin descuento, históricos preservados | DEC11DESCUENTOS |
| Bloqueo de puesto | RN22/HUVEN01a no implementado | Servidor bloquea300s, reautenticación | DEC10BLOQUEO |
| Baja/ajuste | Falta constancia dedicada/nuevo lote; motivo vencido forzado | Causa real, constancia y ajuste fiable no vendible | RN05, INV02/03 |
| Movimientos | Kardex parcial sin saldo/filtros completos ni lotes de venta | INV04 completo con legado explícito | DEC08KARDEX |
| Seguridad | Límites tráfico/eventos/admin técnico/retención con brechas | Contratos y medición15 | DOC01/02,SEC15 |
| Historia/caja | OrdenUUID/empates y límites acumulados requieren corrección | Posición persistida/desempate/topes coherentes | DEC11TOPE/DEC12ORDEN |

Detalle, alternativas, decisiones, estado y fuentes precisas: CONSOLIDACION/ENCARGOS. Estas filas no autorizan cambios de código ni DB. Los costosNULL, identidadGTIN antigua y recepción incompleta no se inventan por migración.

## Rectificaciones de auditoría

Etapa09 sí tiene informe y evidencia; se corrige el NOEJECUTADO que arrastraban10–12. Chrome09 contiene67 comprobaciones funcionales más control cero_page_errors=68, no70. 04-D tiene evidencia de revocación y deja el caso raw sin petición/servicio fuera de muestra. El fallo de Product._state.adding se corrigió en05-L y está integrado en434 pruebas; no mantenerlo abierto por informes antiguos. Un empate de orden de turnos sigue siendo problema de diseño aunque una repetición pase.

05-L prueba interrupción HTTP mientras espera bloqueo antes de escritura; post-escritura/COMMIT/motor siguen pendientes. Soporte12PG usa Client de Django en hilos, no socketsHTTP; la nueva corrida lo describe correctamente. Filtros de VEN05b/CA02 y apertura de detalle/CA03 no se contradicen.

## Fuera de evidencia actual

Etapas13–16 sin informe principal;17 tiene conciliación parcial, no cierre. PG17 no disponible localmente;18.4 no lo reemplaza. XLSX ausente. CI, despliegue real, backup/restore, dispositivos físicos completos, análisis volumétrico y cumplimiento legal no certificados. Fuentes externas y aplicabilidad en el registro homónimo. No se inventa certeza absoluta.
