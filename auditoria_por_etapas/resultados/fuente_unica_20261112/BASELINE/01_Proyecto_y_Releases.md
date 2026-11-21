# 1. Proyecto y releases vigentes

> **Vigente: 12/11/2026 · conciliación documental autorizada.** Requisito aceptado no equivale a implementación o verificación. [Mapa y decisiones](auditoria_por_etapas/resultados/conciliacion_20261112/CONSOLIDACION.md) · [Encargos verificables](auditoria_por_etapas/resultados/conciliacion_20261112/ENCARGOS.md) · [Versión anterior íntegra](auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/01_Proyecto_y_Releases.md). Jira no forma parte de este seguimiento.

## Objetivo de producto

Control interno de un minimarket con una caja, venta en efectivo, productosUND con vencimiento, tres roles exclusivos y trazabilidad de existencias/dinero. La aplicación no sustituye emisión tributaria autorizada ni acredita todas las condiciones para operar un negocio real.

## Release de consolidación

R1 de consolidación incorpora33 HU seleccionadas,41 futuras y ocho ideas fuera del horizonte; catálogo y selección exactos en08/09. Las nueve HU/40 SP originales son baseline histórica. La ampliación incorpora identidad/personal, catálogo/lector, proveedores, recepción/inventario, historial y bloqueo de puesto antes del piloto, con los encargos de integridad/seguridad de16. La aceptación12/11 es documental; no transforma extras anteriores en aprobaciones históricas.

Criterios de resultado: recepción identificable/idempotente; costo consistente; venta con trazabilidad por lotes y snapshots; límites/roles seguros; inventario/constancias/caja concordantes; evidencia integral reproducible y recuperación ensayada. Descuentos nuevos discrecionales se deshabilitan en el contrato; implementación sigue pendiente.

## Alcance temporal y recursos

No hay fechas, equipo disponible, velocidad ni presupuesto real verificados para el siguiente Sprint. Planning14 y tareas16 son preparación del próximo incremento. Estimaciones académicas216h, capacidad192/240h y tarifaS/25 no se reportan como horas, dinero invertido o capacidad actual. No se reabren ni se renumeran Sprints históricos para aparentar continuidad.

## Responsabilidades

El responsable del producto delegó en el asesor recomendaciones/documentación en esta conversación. Implementación/despliegue y cambios de datos operativos se autorizan aparte. Developers estiman y seleccionan trabajo según capacidad real; la revisión independiente comprueba CA/DoD. No se inventan reuniones o participantes.

## Puertas y riesgos

Antes del piloto: P0/P1 resueltos con evidencia, PG17 objetivo probado, CI/backup/restauración/despliegue y E2E por roles, tratamiento seguro de legado, operación fiscal externa/datos personales aplicables aclarados. Ausencia de lector/teléfono/impresora reales se declara como límite. Las pruebas434 en SQLite no cierran esas puertas.

Mantener una fuente por función: RN07 reglas, HU08 criterios,09 alcance/orden,02 diseño,16 trabajos,03 cobertura,04 evidencia,14 siguiente incremento,21 diferencias actuales. CONSOLIDACION/ENCARGOS es el registro único de decisiones; ESTADO_GENERAL es estado de auditorías. Nunca usar una planificación como evidencia de funcionamiento.
