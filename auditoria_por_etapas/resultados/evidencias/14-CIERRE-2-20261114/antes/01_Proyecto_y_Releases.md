# 1. Proyecto y releases vigentes

## Corte vigente14-CIERRE · 14/11/2026 Lima

Primera pasada14 completada para integración de los tres roles en datos ficticios; no aprobación global de release, piloto, despliegue ni todos los módulos. Se mantiene catálogo74HU,287criterios y113casos escritos. No nuevas HU comerciales ni cambio de selección, MoSCoW o estimaciones. Próximo15, luego16/17 y segunda pasada00→01–17.

[Informe y evidencia](auditoria_por_etapas/resultados/ETAPA-14.md#cierre-14) · [Ajustes](auditoria_por_etapas/resultados/soporte/14-CIERRE-ajustes.md) · [Dinero](auditoria_por_etapas/resultados/soporte/14-CIERRE-dinero.md). Las secciones fechadas anteriores se conservan como antecedentes.


> **Fuente funcional principal:** [08 · planificación unificada](08_Historias_de_Usuario.md). Las fichas, RN y contratos de08 definen lo esperado; este documento conserva su papel de contexto, diseño, ejecución o evidencia. Las vistas07/09/03 se derivan de08.


> **Vigente: 12/11/2026 · conciliación documental autorizada.** Requisito aceptado no equivale a implementación o verificación. [Mapa y decisiones](auditoria_por_etapas/resultados/conciliacion_20261112/CONSOLIDACION.md) · [Encargos verificables](auditoria_por_etapas/resultados/conciliacion_20261112/ENCARGOS.md) · [Versión anterior íntegra](auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/01_Proyecto_y_Releases.md). Jira no forma parte de este seguimiento.

## Objetivo de producto

Control interno de un minimarket con una caja, venta en efectivo, productosUND con vencimiento, tres roles exclusivos y trazabilidad de existencias/dinero. La aplicación no sustituye emisión tributaria autorizada ni acredita todas las condiciones para operar un negocio real.

## Release de consolidación

R1 de consolidación incorpora33 HU seleccionadas,41 futuras y ocho ideas fuera del horizonte; catálogo y selección exactos en08/09. Las nueve HU/40 SP originales son baseline histórica. La ampliación incorpora identidad/personal, catálogo/lector, proveedores, recepción/inventario, historial y bloqueo de puesto antes del piloto, con los encargos de integridad/seguridad de16. La aceptación12/11 es documental; no transforma extras anteriores en aprobaciones históricas.

Criterios de resultado: recepción identificable/idempotente; costo consistente; venta con trazabilidad por lotes y snapshots; límites/roles seguros; inventario/constancias/caja concordantes; evidencia integral reproducible y recuperación ensayada. Descuentos nuevos discrecionales suspendidos en la implementación14-D, con revalidación de cobro/histórico/caja acotada en [ETAPA-14](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-d).

## Alcance temporal y recursos

No hay fechas, equipo disponible, velocidad ni presupuesto real verificados para el siguiente Sprint. Planning14 y tareas16 son preparación del próximo incremento. Estimaciones académicas216h, capacidad192/240h y tarifaS/25 no se reportan como horas, dinero invertido o capacidad actual. No se reabren ni se renumeran Sprints históricos para aparentar continuidad.

## Responsabilidades

El responsable del producto delegó en el asesor recomendaciones/documentación en esta conversación. Implementación/despliegue y cambios de datos operativos se autorizan aparte. Developers estiman y seleccionan trabajo según capacidad real; la revisión independiente comprueba CA/DoD. No se inventan reuniones o participantes.

## Puertas y riesgos

Antes del piloto: P0/P1 resueltos con evidencia, PG17 objetivo probado, CI/backup/restauración/despliegue y E2E por roles, tratamiento seguro de legado, operación fiscal externa/datos personales aplicables aclarados. Ausencia de lector/teléfono/impresora reales se declara como límite. Las pruebas434 en SQLite no cierran esas puertas.

Mantener08 como única definición funcional, incluidas RN y decisiones.07/09/03 son vistas derivadas;02 diseño,16 trabajos,04 evidencia,14 preparación del siguiente incremento y21 diferencias deben seguir08. CONSOLIDACION conserva el mapa y la procedencia; ESTADO_GENERAL conserva el estado de auditorías. Nunca usar una planificación como evidencia de funcionamiento.

Valoración móvil física y costos de salida revalidados en14-E con datos ficticios y navegador. La integración continúa parcial por asignaciones, recepción propia, Kardex y constancias. El tratamiento operativo del legado y PostgreSQL conservan sus encargos. [Estado14-E](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-e).

14-F agregó trazabilidad de lotes vendidos y fotografía de vendedor/caja/orden, con revalidación conectada en base aislada. La continuación14-G aborda recepción propia antes de saldo/filtros del Kardex. [Corte14-F](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-f).

14-G incorpora recepción por evento, referencias y reintento, con fotografía de autor/proveedor/cantidad original y enlaces de procedencia.584/584regresión,23+44checkpointsChrome con conjuntos solapados. Etapa14 parcial; continúa14-H-KARDEX-SALDOS-01. Las aprobaciones son del alcance demostrado, no delrelease completo. [Informe14-G](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-g).


## Continuación14-H1

Fotografía de carga inicial implementada como dependencia del Kardex y verificada en base ficticia.592/592regresión,16checkpoints específicos,44de cadena general y23de recepción conectada. Se mantienen separados original y actual, y no se inventa legado. La etapa14 sigueparcial; cursor14-H2-KARDEX-SALDOS-01. No se declara entrega delrelease ni de módulos completos.

[Informe14-H1](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-h1) · [Fundamento y límites](auditoria_por_etapas/resultados/soporte/14-H-disposiciones.md).


## Continuación14-H2 · 14/11/2026

ConsultaKardexcorregida yverificada enmuestrasaisladas:saldoesperado, filtros que no alteranhistoria,páginas ylegadoexplícito.604/604pruebas y20+44observacionesChrome. La cadena completa entre roles se revalidó; no equivale a entregar todoslos módulos ni aautorizarpiloto. Cursor14-I-MERMA-01.

[Informe14-H2](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-h2) · [Decisiones](auditoria_por_etapas/resultados/soporte/14-H2-disposiciones.md).


## Continuación14-I · 14/11/2026 Lima

Constancia y reintento de merma corregidos dentro de los contratos seleccionados; revalidados entre roles en bases ficticias. Se preservan las HU, MoSCoW y puntos; no se incorpora un módulo comercial nuevo. Primera pasada14 sigue PARCIAL, cursor14-J-AJUSTES-HISTORIA-01.15–17 y segunda pasada pendientes. Sin migración operativa ni despliegue.

[Informe14-I](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-i) · [Disposiciones](auditoria_por_etapas/resultados/soporte/14-I-disposiciones.md).
