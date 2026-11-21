# 9. Product Backlog vigente

> **Vigente: 12/11/2026 · conciliación documental autorizada.** Requisito aceptado no equivale a implementación o verificación. [Mapa y decisiones](auditoria_por_etapas/resultados/conciliacion_20261112/CONSOLIDACION.md) · [Encargos verificables](auditoria_por_etapas/resultados/conciliacion_20261112/ENCARGOS.md) · [Versión anterior íntegra](auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/09_Product_Backlog.md). Jira no forma parte de este seguimiento.

## Objetivo y alcance

R1 de consolidación debe permitir operar caja única en efectivo con identidad, catálogo, recepción, inventario y consulta trazables, sin pérdidas/duplicados ni permisos indebidos. Se seleccionan33 HU (nueve históricas y24 adicionales, incluido bloqueo de pantalla previo al piloto). Otras41 siguen futuras; ocho ideas quedan fuera. El orden siguiente expresa prioridad de producto; la secuencia técnica y dependencias están en16. No hay Sprint nuevo comprometido ni fechas/personas/capacidad verificadas.

Los SP que se conservan son estimaciones de la línea base (74 HU/231 SP), no una nueva estimación del trabajo restante. Los219 CA base más contratos suplementarios determinan aceptación. Los nueve seleccionados originalmente sumaban40 SP/41 CA; no representan la cobertura actual. La selección vigente queda aceptada por delegación del 12/11. Implementación y verificación se consultan en03/04, no se deducen de esta tabla.

## Lista vigente por selección

| Orden vigente | ID | Necesidad | Selección | Etapa fuente | SP históricos | Dependencia funcional histórica a contrastar |
|---:|---|---|---|---|---:|---|
| 1 | HU-AUTH-01 | Ingresar con mi cuenta de trabajo | R1 consolidación | 01 | 5 | Ninguna |
| 2 | HU-AUTH-03 | Salir de mi cuenta al terminar | R1 consolidación | 02 | 2 | HU-AUTH-01 |
| 3 | HU-PROD-02 | Registrar un producto por unidad con vencimiento | R1 consolidación | 03 | 5 | HU-AUTH-01; categoría activa existente (CAT02 o datos iniciales) |
| 4 | HU-INV-01a | Registrar las existencias iniciales por lotes | R1 consolidación | 05 | 5 | HU-PROD-02 |
| 5 | HU-CAJA-01 | Abrir el turno de caja | R1 consolidación | 09 | 5 | HU-AUTH-01 |
| 6 | HU-VEN-01b | Preparar una venta y revisar existencias | R1 consolidación | 10 | 5 | HU-CAJA-01 y HU-INV-01a |
| 7 | HU-VEN-01c | Cobrar en efectivo y descontar existencias | R1 consolidación | 11 | 5 | HU-VEN-01b |
| 8 | HU-VEN-02a | Generar una constancia interna de venta | R1 consolidación | 12 | 3 | HU-VEN-01c |
| 9 | HU-CAJA-02 | Cerrar y cuadrar la caja | R1 consolidación | 09 | 5 | Habilitación: HU-CAJA-01; integración del recorrido: HU-VEN-01c |
| 10 | HU-CAT-02 | Categorías — Crear nueva categoría de productos | R1 consolidación | 03 | 2 | HU-AUTH-01 |
| 11 | HU-CAT-01 | Categorías — Ver lista de categorías de productos | R1 consolidación | 03 | 1 | HU-AUTH-01 y datos iniciales de categoría |
| 12 | HU-PROD-01 | Productos — Ver catálogo completo de productos | R1 consolidación | 03 | 3 | HU-PROD-02 |
| 13 | HU-PROD-04 | Productos — Editar datos de un producto | R1 consolidación | 03 | 3 | HU-PROD-02 |
| 14 | HU-PROD-05 | Productos — Gestionar estado de disponibilidad comercial | R1 consolidación | 03 | 2 | HU-PROD-02 |
| 15 | HU-PROD-06 | Productos — Consultar vencimientos de productos | R1 consolidación | 07 | 3 | HU-INV-01a |
| 16 | HU-VEN-05a | Ventas — Consultar las ventas de mi turno | R1 consolidación | 12 | 2 | HU-VEN-01c y HU-CAJA-01 |
| 17 | HU-VEN-05b | Ventas — Consultar el historial de ventas con filtros | R1 consolidación | 12 | 3 | HU-VEN-01c |
| 18 | HU-CAJA-05 | Caja — Consultar historial de turnos de caja | R1 consolidación | 12 | 3 | HU-CAJA-02 |
| 19 | HU-VEN-01a | Ventas — Bloquear la pantalla de venta por inactividad | R1 consolidación | 10 | 3 | HU-CAJA-01 |
| 20 | HU-AUTH-02 | Autenticación — Bloquear cuenta por intentos fallidos | R1 consolidación | 01 | 3 | HU-AUTH-01 |
| 21 | HU-USR-02 | Usuarios — Crear cuenta de nuevo empleado | R1 consolidación | 02 | 5 | HU-AUTH-01 |
| 22 | HU-USR-01 | Usuarios — Listar empleados del sistema | R1 consolidación | 02 | 2 | HU-AUTH-01 y cuentas iniciales |
| 23 | HU-USR-04 | Usuarios — Desactivar cuenta de empleado | R1 consolidación | 02 | 3 | HU-USR-01 |
| 24 | HU-INV-02 | Inventario — Registrar baja de inventario por merma | R1 consolidación | 08 | 5 | HU-INV-01a |
| 25 | HU-INV-03 | Inventario – Realizar ajuste por conteo físico | R1 consolidación | 08 | 5 | HU-INV-01a |
| 26 | HU-INV-04 | Mercadería — Consultar movimientos de un producto | R1 consolidación | 08 | 2 | HU-INV-01a, HU-VEN-01c, HU-INV-02 y HU-INV-03 |
| 27 | HU-PROV-02 | Proveedores — Registrar nuevo proveedor | R1 consolidación | 04 | 3 | HU-AUTH-01 |
| 28 | HU-PROV-01 | Proveedores — Ver lista de proveedores | R1 consolidación | 04 | 2 | HU-AUTH-01 |
| 29 | HU-PROV-04 | Proveedores — Gestionar estado de vigencia del proveedor | R1 consolidación | 04 | 2 | HU-PROV-01 |
| 30 | HU-INV-01b | Registrar recepción posterior y actualizar costo promedio | R1 consolidación | 06 | 2 | HU-INV-01a |
| 31 | HU-USR-03 | Usuarios — Editar datos y rol de un empleado | R1 consolidación | 02 | 3 | HU-USR-02 |
| 32 | HU-USR-05 | Usuarios — Reactivar cuenta de empleado | R1 consolidación | 02 | 2 | HU-USR-04 |
| 33 | HU-PROD-03 | Productos — Escanear código de barras para registrar producto | R1 consolidación | 03 | 5 | HU-PROD-02 |
| 34 | HU-INV-05 | Inventario — Consultar historial de bajas | FUTURO, sin Sprint | 08 | 2 | HU-INV-02 |
| 35 | HU-INV-06 | Inventario — Consultar historial de ajustes | FUTURO, sin Sprint | 08 | 2 | HU-INV-03 |
| 36 | HU-VEN-06a | Ventas — Anular una venta cobrada en efectivo | FUTURO, sin Sprint | 12 | 3 | HU-VEN-01c y HU-VEN-02a |
| 37 | HU-VEN-06c | Ventas — Definir el destino de la mercadería devuelta | FUTURO, sin Sprint | 12 | 3 | HU-VEN-06a y HU-INV-02 |
| 38 | HU-VEN-07 | Cobrar con Yape y registrar el código de operación | FUTURO, sin Sprint | 12 | 2 | HU-VEN-01b y HU-VEN-01c |
| 39 | HU-VEN-06b | Ventas — Anular una venta cobrada con Yape | FUTURO, sin Sprint | 12 | 2 | HU-VEN-06a y HU-VEN-07 |
| 40 | HU-CAJA-03 | Caja — Registrar movimiento manual de efectivo | FUTURO, sin Sprint | 09 | 3 | HU-CAJA-01 |
| 41 | HU-CAJA-04 | Caja — Ver resumen del turno activo | FUTURO, sin Sprint | 09 | 2 | HU-CAJA-01, HU-VEN-01c y HU-CAJA-03 |
| 42 | HU-CAJA-06 | Caja — Aprobar cierre de turno | FUTURO, sin Sprint | 09 | 2 | HU-CAJA-02 |
| 43 | HU-CAJA-07 | Caja – Forzar cierre de turno de caja | FUTURO, sin Sprint | 09 | 5 | HU-CAJA-01 |
| 44 | HU-CONF-01 | Configuración — Ver configuración actual del negocio | FUTURO, sin Sprint | 13 | 1 | HU-AUTH-01 |
| 45 | HU-CONF-02 | Configuración — Actualizar configuración del negocio | FUTURO, sin Sprint | 13 | 3 | HU-CONF-01 |
| 46 | HU-SOL-01 | Reposición – Crear solicitud de reposición | FUTURO, sin Sprint | 06 | 3 | HU-PROD-02, HU-PROV-02 |
| 47 | HU-SOL-02 | Reposición — Listar solicitudes con filtro por estado | FUTURO, sin Sprint | 06 | 2 | HU-SOL-01 |
| 48 | HU-SOL-03 | Reposición — Aprobar solicitud de reposición | FUTURO, sin Sprint | 06 | 3 | HU-SOL-01 |
| 49 | HU-SOL-04 | Reposición — Rechazar solicitud de reposición | FUTURO, sin Sprint | 06 | 2 | HU-SOL-01 |
| 50 | HU-SOL-05a | Reposición — Completar la recepción total de una solicitud | FUTURO, sin Sprint | 06 | 5 | HU-SOL-03, HU-INV-01a, HU-INV-01b |
| 51 | HU-SOL-05b | Reposición — Registrar una recepción parcial con saldo pendiente | FUTURO, sin Sprint | 06 | 3 | HU-SOL-05a |
| 52 | HU-REP-05 | Reportes – Consultar reporte de productos bajo stock mínimo | FUTURO, sin Sprint | 13 | 3 | HU-INV-01a |
| 53 | HU-DASH-03 | Resumen del negocio – Ver alertas operativas (stock crítico, vencimientos y turnos) | FUTURO, sin Sprint | 13 | 5 | HU-INV-01a, HU-CAJA-05 y HU-PROD-06 |
| 54 | HU-DASH-01 | Resumen del negocio — Ver indicadores de ventas en tiempo real | FUTURO, sin Sprint | 13 | 5 | HU-VEN-01c |
| 55 | HU-REP-01 | Reportes — Consultar reporte analítico de ventas totales por período | FUTURO, sin Sprint | 13 | 5 | HU-VEN-01c |
| 56 | HU-REP-02 | Reportes – Consultar reporte completo de ranking de productos más vendidos | FUTURO, sin Sprint | 13 | 3 | HU-VEN-01c |
| 57 | HU-REP-04 | Reportes — Ver ventas por método de pago | FUTURO, sin Sprint | 13 | 2 | HU-VEN-01c y HU-VEN-07 |
| 58 | HU-REP-06 | Reportes — Ver resumen general del inventario | FUTURO, sin Sprint | 13 | 2 | HU-INV-01a |
| 59 | HU-REP-07 | Reportes — Ver margen de ganancia por producto | FUTURO, sin Sprint | 13 | 5 | HU-VEN-01c y HU-INV-01a |
| 60 | HU-REP-08 | Reportes — Ver mermas agrupadas por motivo | FUTURO, sin Sprint | 13 | 3 | HU-INV-02 |
| 61 | HU-DASH-02 | Resumen del negocio — Ver gráfico de evolución de ventas por día | FUTURO, sin Sprint | 13 | 3 | HU-VEN-01c |
| 62 | HU-DASH-04 | Resumen del negocio – Ver ranking de productos más vendidos | FUTURO, sin Sprint | 13 | 3 | HU-VEN-01c |
| 63 | HU-DASH-05 | Resumen del negocio — Ver solicitudes de reposición pendientes | FUTURO, sin Sprint | 13 | 2 | HU-SOL-01 |
| 64 | HU-REP-03 | Reportes — Ver ventas desglosadas por día | FUTURO, sin Sprint | 13 | 3 | HU-VEN-01c |
| 65 | HU-REP-09 | Reportes — Exportar reportes analíticos de gestión a PDF | FUTURO, sin Sprint | 13 | 3 | HU-REP-01, HU-REP-02, HU-REP-05, HU-REP-07 y HU-REP-08 |
| 66 | HU-AUTH-04a | Autenticación — Cerrar automáticamente la sesión previa | FUTURO, sin Sprint | 02 | 5 | HU-AUTH-01, HU-AUTH-03 |
| 67 | HU-AUTH-04b | Autenticación — Descartar venta sin confirmar al cerrarse la sesión | FUTURO, sin Sprint | 02 | 3 | HU-AUTH-04a, HU-VEN-01b |
| 68 | HU-AUTH-05 | Autenticación — Recuperar contraseña por correo | FUTURO, sin Sprint | 02 | 5 | HU-AUTH-01 |
| 69 | HU-USR-06 | Usuarios — Forzar cierre de sesión remoto | FUTURO, sin Sprint | 02 | 3 | HU-USR-01 y HU-AUTH-01 |
| 70 | HU-LOG-01 | Supervisión de accesos – Consultar registro de accesos | FUTURO, sin Sprint | 02 | 3 | HU-AUTH-01 y HU-AUTH-02 |
| 71 | HU-CAT-03 | Categorías — Editar nombre de categoría | FUTURO, sin Sprint | 03 | 1 | HU-CAT-02 |
| 72 | HU-CAT-04 | Categorías — Eliminar categoría sin productos | FUTURO, sin Sprint | 03 | 2 | HU-CAT-02 y HU-PROD-01 |
| 73 | HU-VEN-04 | Ventas – Buscar producto por código de barras | FUTURO, sin Sprint | 10 | 3 | HU-VEN-01b |
| 74 | HU-PROV-03 | Proveedores — Editar datos de un proveedor | FUTURO, sin Sprint | 04 | 2 | HU-PROV-02 |

## Ocho ideas fuera del horizonte

HU-CLI-01/02/03 (clientes), HU-VEN-02b/02c (boleta/factura), HU-VEN-03 (PDF/correo), HU-VEN-08 (exportar historial) y HU-VEN-09 (peso/granel). Sin CA seleccionados/SP comprometidos. El supuesto de exportación disponible se corrige: REP09 también es futuro. El catálogo completo y motivos siguen en08/BASELINE.

## Complementos seleccionados y exclusiones

Los encargos de recepción/idempotencia, valoración, trazabilidad lote/venta, descuentos nuevos deshabilitados, permisos, seguridad técnica, checks, constancias, Kardex, alertas y navegación se vinculan a HU existentes en16 y ENCARGOS. Activar/desactivar categoría conserva PROP-E00-HU-02/J-CA1..4. Stock consolidado y panel mínimo actual tienen el contrato DEC07; no se adjudica entrega de DASH/REP completos.

Se difieren SOL, INV05/06, CAT03/04, PROV03, caja manual/aprobación/forzada, consulta VEN04 sin turno, sesión única/correo/cierre remoto/LOG UI, anulaciones/Yape/configuración/reportes y propuestas RET. No se impone una solución técnica masiva por el solo hecho de estar propuesta.

Los enlaces de dependencia de la tabla preservan procedencia: una solicitud SOL futura no bloquea la recepción directa seleccionada (DOC03AB); una alerta no exige reportes completos. Para trabajo autorizado se usa el grafo vigente de16. No se usa Jira ni se recrean Sprints anteriores.
