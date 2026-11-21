# 9. Product Backlog · vista de la fuente principal

> **VISTA DERIVADA.** Fuente principal: [08 · planificación](08_Historias_de_Usuario.md). No editar requisitos aquí. Generada desde SHA256 `600566eaab6729c5e18cff2e3df2c6202cb319e89140d83062217e30f3df7361`. Los cambios se hacen en08 y se regeneran estas vistas.


Prioridad respecto a R1 de consolidación: M=Must, S=Should, C=Could, W=Won’t en este horizonte. 35 HU seleccionadas, 40 futuras; 8 ideas excluidas en08. Puntos de la HU completa orientativos, no compromiso del equipo ni trabajo restante. Una prioridadS/C no permite incumplir una función visible. No se infiere Sprint, fecha, equipo o capacidad a partir de estos tamaños.

| Orden | ID | Épica | Título | MoSCoW | Fibonacci orientativo | SP anteriores | Selección | Dependencia |
|---:|---|---|---|:---:|---:|---:|---|---|
| 1 | [HU-AUTH-01](08_Historias_de_Usuario.md#HU-AUTH-01) | EPIC-SEG | Ingresar con mi cuenta de trabajo | M | 5 | 5 | R1 seleccionado | Ninguna. |
| 2 | [HU-AUTH-03](08_Historias_de_Usuario.md#HU-AUTH-03) | EPIC-SEG | Salir de mi cuenta al terminar | M | 2 | 2 | R1 seleccionado | HU-AUTH-01. |
| 3 | [HU-PROD-02](08_Historias_de_Usuario.md#HU-PROD-02) | EPIC-CAT | Registrar un producto por unidad con vencimiento | M | 5 | 5 | R1 seleccionado | HU-AUTH-01; categoría activa existente (CAT02 o datos iniciales). |
| 4 | [HU-INV-01a](08_Historias_de_Usuario.md#HU-INV-01a) | EPIC-INV | Registrar las existencias iniciales por lotes | M | 5 | 5 | R1 seleccionado | HU-PROD-02. |
| 5 | [HU-CAJA-01](08_Historias_de_Usuario.md#HU-CAJA-01) | EPIC-VEN | Abrir el turno de caja | M | 5 | 5 | R1 seleccionado | HU-AUTH-01. |
| 6 | [HU-VEN-01b](08_Historias_de_Usuario.md#HU-VEN-01b) | EPIC-VEN | Preparar una venta y revisar existencias | M | 5 | 5 | R1 seleccionado | HU-CAJA-01 y HU-INV-01a. |
| 7 | [HU-VEN-01c](08_Historias_de_Usuario.md#HU-VEN-01c) | EPIC-VEN | Cobrar en efectivo y descontar existencias | M | 13 | 5 | R1 seleccionado | HU-VEN-01b. |
| 8 | [HU-VEN-02a](08_Historias_de_Usuario.md#HU-VEN-02a) | EPIC-VEN | Generar una constancia interna de venta | M | 5 | 3 | R1 seleccionado | HU-VEN-01c. |
| 9 | [HU-CAJA-02](08_Historias_de_Usuario.md#HU-CAJA-02) | EPIC-VEN | Cerrar y cuadrar la caja | M | 5 | 5 | R1 seleccionado | Habilitación: HU-CAJA-01; integración del recorrido: HU-VEN-01c. |
| 10 | [HU-CAT-02](08_Historias_de_Usuario.md#HU-CAT-02) | EPIC-CAT | Categorías — Crear nueva categoría de productos | S | 2 | 2 | R1 seleccionado | HU-AUTH-01. |
| 11 | [HU-CAT-01](08_Historias_de_Usuario.md#HU-CAT-01) | EPIC-CAT | Categorías — Ver lista de categorías de productos | S | 1 | 1 | R1 seleccionado | HU-AUTH-01 y datos iniciales de categoría. |
| 12 | [HU-PROD-01](08_Historias_de_Usuario.md#HU-PROD-01) | EPIC-CAT | Productos — Ver catálogo completo de productos | M | 3 | 3 | R1 seleccionado | HU-PROD-02. |
| 13 | [HU-PROD-04](08_Historias_de_Usuario.md#HU-PROD-04) | EPIC-CAT | Productos — Editar datos de un producto | M | 3 | 3 | R1 seleccionado | HU-PROD-02. |
| 14 | [HU-PROD-05](08_Historias_de_Usuario.md#HU-PROD-05) | EPIC-CAT | Productos — Gestionar estado de disponibilidad comercial | M | 2 | 2 | R1 seleccionado | HU-PROD-02. |
| 15 | [HU-PROD-06](08_Historias_de_Usuario.md#HU-PROD-06) | EPIC-CAT | Productos — Consultar vencimientos de productos | M | 3 | 3 | R1 seleccionado | HU-INV-01a. |
| 16 | [HU-VEN-05a](08_Historias_de_Usuario.md#HU-VEN-05a) | EPIC-VEN | Ventas — Consultar las ventas de mi turno | M | 2 | 2 | R1 seleccionado | HU-VEN-01c y HU-CAJA-01. |
| 17 | [HU-VEN-05b](08_Historias_de_Usuario.md#HU-VEN-05b) | EPIC-VEN | Ventas — Consultar el historial de ventas con filtros | M | 5 | 3 | R1 seleccionado | HU-VEN-01c. |
| 18 | [HU-CAJA-05](08_Historias_de_Usuario.md#HU-CAJA-05) | EPIC-VEN | Caja — Consultar historial de turnos de caja | M | 3 | 3 | R1 seleccionado | HU-CAJA-02. |
| 19 | [HU-VEN-01a](08_Historias_de_Usuario.md#HU-VEN-01a) | EPIC-VEN | Ventas — Bloquear la pantalla de venta por inactividad | M | 8 | 3 | R1 seleccionado | HU-CAJA-01. |
| 20 | [HU-AUTH-02](08_Historias_de_Usuario.md#HU-AUTH-02) | EPIC-SEG | Autenticación — Bloquear cuenta por intentos fallidos | M | 3 | 3 | R1 seleccionado | HU-AUTH-01. |
| 21 | [HU-USR-02](08_Historias_de_Usuario.md#HU-USR-02) | EPIC-SEG | Usuarios — Crear cuenta de nuevo empleado | M | 5 | 5 | R1 seleccionado | HU-AUTH-01. |
| 22 | [HU-USR-01](08_Historias_de_Usuario.md#HU-USR-01) | EPIC-SEG | Usuarios — Listar empleados del sistema | S | 2 | 2 | R1 seleccionado | HU-AUTH-01 y cuentas iniciales. |
| 23 | [HU-USR-04](08_Historias_de_Usuario.md#HU-USR-04) | EPIC-SEG | Usuarios — Desactivar cuenta de empleado | M | 3 | 3 | R1 seleccionado | HU-USR-01. |
| 24 | [HU-INV-02](08_Historias_de_Usuario.md#HU-INV-02) | EPIC-INV | Inventario — Registrar baja de inventario por merma | M | 5 | 5 | R1 seleccionado | HU-INV-01a. |
| 25 | [HU-INV-03](08_Historias_de_Usuario.md#HU-INV-03) | EPIC-INV | Inventario – Realizar ajuste por conteo físico | M | 8 | 5 | R1 seleccionado | HU-INV-01a. |
| 26 | [HU-INV-04](08_Historias_de_Usuario.md#HU-INV-04) | EPIC-INV | Mercadería — Consultar movimientos de un producto | M | 8 | 2 | R1 seleccionado | HU-INV-01a, HU-VEN-01c, HU-INV-02 y HU-INV-03. |
| 27 | [HU-PROV-02](08_Historias_de_Usuario.md#HU-PROV-02) | EPIC-CAT | Proveedores — Registrar nuevo proveedor | S | 3 | 3 | R1 seleccionado | HU-AUTH-01. |
| 28 | [HU-PROV-01](08_Historias_de_Usuario.md#HU-PROV-01) | EPIC-CAT | Proveedores — Ver lista de proveedores | S | 2 | 2 | R1 seleccionado | HU-AUTH-01. |
| 29 | [HU-PROV-04](08_Historias_de_Usuario.md#HU-PROV-04) | EPIC-CAT | Proveedores — Gestionar estado de vigencia del proveedor | S | 2 | 2 | R1 seleccionado | HU-PROV-01. |
| 30 | [HU-INV-01b](08_Historias_de_Usuario.md#HU-INV-01b) | EPIC-INV | Registrar recepción posterior y actualizar costo promedio | M | 8 | 2 | R1 seleccionado | HU-INV-01a. |
| 31 | [HU-USR-03](08_Historias_de_Usuario.md#HU-USR-03) | EPIC-SEG | Usuarios — Editar datos y rol de un empleado | M | 8 | 3 | R1 seleccionado | HU-USR-02. |
| 32 | [HU-USR-05](08_Historias_de_Usuario.md#HU-USR-05) | EPIC-SEG | Usuarios — Reactivar cuenta de empleado | M | 2 | 2 | R1 seleccionado | HU-USR-04. |
| 33 | [HU-PROD-03](08_Historias_de_Usuario.md#HU-PROD-03) | EPIC-CAT | Productos — Escanear código de barras para registrar producto | C | 5 | 5 | R1 seleccionado | HU-PROD-02. |
| 34 | [HU-INV-05](08_Historias_de_Usuario.md#HU-INV-05) | EPIC-INV | Inventario — Consultar historial de bajas | W | 2 | 2 | FUTURO, requiere refinamiento | HU-INV-02. |
| 35 | [HU-INV-06](08_Historias_de_Usuario.md#HU-INV-06) | EPIC-INV | Inventario — Consultar historial de ajustes | W | 2 | 2 | FUTURO, requiere refinamiento | HU-INV-03. |
| 36 | [HU-VEN-06a](08_Historias_de_Usuario.md#HU-VEN-06a) | EPIC-VEN | Ventas — Anular una venta cobrada en efectivo | W | 3 | 3 | FUTURO, requiere refinamiento | HU-VEN-01c y HU-VEN-02a. |
| 37 | [HU-VEN-06c](08_Historias_de_Usuario.md#HU-VEN-06c) | EPIC-VEN | Ventas — Definir el destino de la mercadería devuelta | W | 3 | 3 | FUTURO, requiere refinamiento | HU-VEN-06a y HU-INV-02. |
| 38 | [HU-VEN-07](08_Historias_de_Usuario.md#HU-VEN-07) | EPIC-VEN | Cobrar con Yape y registrar el código de operación | M | 2 | 2 | R1 seleccionado | HU-VEN-01b y HU-VEN-01c. |
| 39 | [HU-VEN-06b](08_Historias_de_Usuario.md#HU-VEN-06b) | EPIC-VEN | Ventas — Anular una venta cobrada con Yape | W | 2 | 2 | FUTURO, requiere refinamiento | HU-VEN-06a y HU-VEN-07. |
| 40 | [HU-CAJA-03](08_Historias_de_Usuario.md#HU-CAJA-03) | EPIC-VEN | Caja — Registrar movimiento manual de efectivo | W | 3 | 3 | FUTURO, requiere refinamiento | HU-CAJA-01. |
| 41 | [HU-CAJA-04](08_Historias_de_Usuario.md#HU-CAJA-04) | EPIC-VEN | Caja — Ver resumen del turno activo | W | 2 | 2 | FUTURO, requiere refinamiento | HU-CAJA-01, HU-VEN-01c y HU-CAJA-03. |
| 42 | [HU-CAJA-06](08_Historias_de_Usuario.md#HU-CAJA-06) | EPIC-VEN | Caja — Aprobar cierre de turno | W | 2 | 2 | FUTURO, requiere refinamiento | HU-CAJA-02. |
| 43 | [HU-CAJA-07](08_Historias_de_Usuario.md#HU-CAJA-07) | EPIC-VEN | Caja – Forzar cierre de turno de caja | W | 5 | 5 | FUTURO, requiere refinamiento | HU-CAJA-01. |
| 44 | [HU-CONF-01](08_Historias_de_Usuario.md#HU-CONF-01) | EPIC-REP | Configuración — Ver configuración actual del negocio | W | 1 | 1 | FUTURO, requiere refinamiento | HU-AUTH-01. |
| 45 | [HU-CONF-02](08_Historias_de_Usuario.md#HU-CONF-02) | EPIC-REP | Configuración — Actualizar configuración del negocio | W | 3 | 3 | FUTURO, requiere refinamiento | HU-CONF-01. |
| 46 | [HU-SOL-01](08_Historias_de_Usuario.md#HU-SOL-01) | EPIC-INV | Reposición – Crear solicitud de reposición | W | 3 | 3 | FUTURO, requiere refinamiento | HU-PROD-02, HU-PROV-02. |
| 47 | [HU-SOL-02](08_Historias_de_Usuario.md#HU-SOL-02) | EPIC-INV | Reposición — Listar solicitudes con filtro por estado | W | 2 | 2 | FUTURO, requiere refinamiento | HU-SOL-01. |
| 48 | [HU-SOL-03](08_Historias_de_Usuario.md#HU-SOL-03) | EPIC-INV | Reposición — Aprobar solicitud de reposición | W | 3 | 3 | FUTURO, requiere refinamiento | HU-SOL-01. |
| 49 | [HU-SOL-04](08_Historias_de_Usuario.md#HU-SOL-04) | EPIC-INV | Reposición — Rechazar solicitud de reposición | W | 2 | 2 | FUTURO, requiere refinamiento | HU-SOL-01. |
| 50 | [HU-SOL-05a](08_Historias_de_Usuario.md#HU-SOL-05a) | EPIC-INV | Reposición — Completar la recepción total de una solicitud | W | 5 | 5 | FUTURO, requiere refinamiento | HU-SOL-03, HU-INV-01a, HU-INV-01b. |
| 51 | [HU-SOL-05b](08_Historias_de_Usuario.md#HU-SOL-05b) | EPIC-INV | Reposición — Registrar una recepción parcial con saldo pendiente | W | 3 | 3 | FUTURO, requiere refinamiento | HU-SOL-05a. |
| 52 | [HU-REP-05](08_Historias_de_Usuario.md#HU-REP-05) | EPIC-REP | Reportes – Consultar reporte de productos bajo stock mínimo | W | 3 | 3 | FUTURO, requiere refinamiento | HU-INV-01a. |
| 53 | [HU-DASH-03](08_Historias_de_Usuario.md#HU-DASH-03) | EPIC-REP | Resumen del negocio – Ver alertas operativas (stock crítico, vencimientos y turnos) | W | 5 | 5 | FUTURO, requiere refinamiento | HU-INV-01a, HU-CAJA-05 y HU-PROD-06. |
| 54 | [HU-DASH-01](08_Historias_de_Usuario.md#HU-DASH-01) | EPIC-REP | Resumen del negocio — Ver indicadores de ventas en tiempo real | W | 5 | 5 | FUTURO, requiere refinamiento | HU-VEN-01c. |
| 55 | [HU-REP-01](08_Historias_de_Usuario.md#HU-REP-01) | EPIC-REP | Reportes — Consultar reporte analítico de ventas totales por período | W | 5 | 5 | FUTURO, requiere refinamiento | HU-VEN-01c. |
| 56 | [HU-REP-02](08_Historias_de_Usuario.md#HU-REP-02) | EPIC-REP | Reportes – Consultar reporte completo de ranking de productos más vendidos | W | 3 | 3 | FUTURO, requiere refinamiento | HU-VEN-01c. |
| 57 | [HU-REP-04](08_Historias_de_Usuario.md#HU-REP-04) | EPIC-REP | Reportes — Ver ventas por método de pago | W | 2 | 2 | FUTURO, requiere refinamiento | HU-VEN-01c y HU-VEN-07. |
| 58 | [HU-REP-06](08_Historias_de_Usuario.md#HU-REP-06) | EPIC-REP | Reportes — Ver resumen general del inventario | W | 2 | 2 | FUTURO, requiere refinamiento | HU-INV-01a. |
| 59 | [HU-REP-07](08_Historias_de_Usuario.md#HU-REP-07) | EPIC-REP | Reportes — Ver margen de ganancia por producto | W | 5 | 5 | FUTURO, requiere refinamiento | HU-VEN-01c y HU-INV-01a. |
| 60 | [HU-REP-08](08_Historias_de_Usuario.md#HU-REP-08) | EPIC-REP | Reportes — Ver mermas agrupadas por motivo | W | 3 | 3 | FUTURO, requiere refinamiento | HU-INV-02. |
| 61 | [HU-DASH-02](08_Historias_de_Usuario.md#HU-DASH-02) | EPIC-REP | Resumen del negocio — Ver gráfico de evolución de ventas por día | W | 3 | 3 | FUTURO, requiere refinamiento | HU-VEN-01c. |
| 62 | [HU-DASH-04](08_Historias_de_Usuario.md#HU-DASH-04) | EPIC-REP | Resumen del negocio – Ver ranking de productos más vendidos | W | 3 | 3 | FUTURO, requiere refinamiento | HU-VEN-01c. |
| 63 | [HU-DASH-05](08_Historias_de_Usuario.md#HU-DASH-05) | EPIC-REP | Resumen del negocio — Ver solicitudes de reposición pendientes | W | 2 | 2 | FUTURO, requiere refinamiento | HU-SOL-01. |
| 64 | [HU-REP-03](08_Historias_de_Usuario.md#HU-REP-03) | EPIC-REP | Reportes — Ver ventas desglosadas por día | W | 3 | 3 | FUTURO, requiere refinamiento | HU-VEN-01c. |
| 65 | [HU-REP-09](08_Historias_de_Usuario.md#HU-REP-09) | EPIC-REP | Reportes — Exportar reportes analíticos de gestión a PDF | W | 3 | 3 | FUTURO, requiere refinamiento | HU-REP-01, HU-REP-02, HU-REP-05, HU-REP-07 y HU-REP-08. |
| 66 | [HU-AUTH-04a](08_Historias_de_Usuario.md#HU-AUTH-04a) | EPIC-SEG | Autenticación — Cerrar automáticamente la sesión previa | W | 5 | 5 | FUTURO, requiere refinamiento | HU-AUTH-01, HU-AUTH-03. |
| 67 | [HU-AUTH-04b](08_Historias_de_Usuario.md#HU-AUTH-04b) | EPIC-SEG | Autenticación — Descartar venta sin confirmar al cerrarse la sesión | W | 3 | 3 | FUTURO, requiere refinamiento | HU-AUTH-04a, HU-VEN-01b. |
| 68 | [HU-AUTH-05](08_Historias_de_Usuario.md#HU-AUTH-05) | EPIC-SEG | Autenticación — Recuperar contraseña por correo | W | 5 | 5 | FUTURO, requiere refinamiento | HU-AUTH-01. |
| 69 | [HU-USR-06](08_Historias_de_Usuario.md#HU-USR-06) | EPIC-SEG | Usuarios — Forzar cierre de sesión remoto | W | 3 | 3 | FUTURO, requiere refinamiento | HU-USR-01 y HU-AUTH-01. |
| 70 | [HU-LOG-01](08_Historias_de_Usuario.md#HU-LOG-01) | EPIC-SEG | Supervisión de accesos – Consultar registro de accesos | W | 3 | 3 | FUTURO, requiere refinamiento | HU-AUTH-01 y HU-AUTH-02. |
| 71 | [HU-CAT-03](08_Historias_de_Usuario.md#HU-CAT-03) | EPIC-CAT | Categorías — Editar nombre de categoría | W | 1 | 1 | FUTURO, requiere refinamiento | HU-CAT-02. |
| 72 | [HU-CAT-04](08_Historias_de_Usuario.md#HU-CAT-04) | EPIC-CAT | Categorías — Eliminar categoría sin productos | W | 2 | 2 | FUTURO, requiere refinamiento | HU-CAT-02 y HU-PROD-01. |
| 73 | [HU-VEN-04](08_Historias_de_Usuario.md#HU-VEN-04) | EPIC-VEN | Ventas – Buscar producto por código de barras | W | 3 | 3 | FUTURO, requiere refinamiento | HU-VEN-01b. |
| 74 | [HU-PROV-03](08_Historias_de_Usuario.md#HU-PROV-03) | EPIC-CAT | Proveedores — Editar datos de un proveedor | W | 2 | 2 | FUTURO, requiere refinamiento | HU-PROV-02. |
| 75 | [HU-VEN-10](08_Historias_de_Usuario.md#HU-VEN-10) | EPIC-VEN | Cobrar una venta combinando efectivo y Yape | M | 8 | — | R1 seleccionado | HU-VEN-01c, HU-VEN-07, HU-CAJA-01/02, HU-VEN-05a/05b. |

Totales orientativos: catálogo 276 SP; R1 156 SP; futuros 120 SP. La procedencia de tamaños anteriores se conserva por ficha; «—» identifica una historia sin estimación previa. No sumar trabajo futuro a un Sprint actual.

La aceptación del alcance no demuestra implementación. [Trabajos y dependencias](16_Task_Breakdown.md), [preparación del siguiente incremento](14_Sprint_Planning.md), [cobertura de pruebas](03_Matriz_de_Trazabilidad_y_Pruebas.md) y [diferencias comprobadas](21_Alcance_Actual_y_Diferencias.md) deben seguir estas fichas.
