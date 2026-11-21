# 09. Product Backlog priorizado

> **Actualización 05/11/2026:** Corte histórico del backlog. Sus asignaciones y estados describen la planificación original, no el avance actual ni un compromiso de funciones entregadas. Jira ya no se usa ni se evalúa en este proyecto; las referencias posteriores se conservan solo como contexto histórico. Véase [Guía de alcance y diferencias](21_Alcance_Actual_y_Diferencias.md).

> **Propósito:** mantener una única lista ordenada de las necesidades de la bodega. El Product Backlog es emergente: orden, prioridad, Story Points, dependencias, Sprint y versión se gestionan y consultan de forma exclusiva en este documento. Solo el alcance de Sprint 1 ha sido seleccionado para ejecución; las demás historias permanecen activas en el backlog sin Sprint asignado.
>
> **Línea base actual:** 74 historias de usuario activas · 231 Story Points · 43 Indispensables (147 SP) · 28 Importantes (74 SP) · 3 Deseables (10 SP) · 8 ideas fuera del horizonte (0 SP). Escala relativa: 1, 2, 3 y 5 Story Points.

---

## 9.1 Criterios de ordenación

El equipo de Developers mantiene el orden académico del Product Backlog considerando:

1. **Valor para la bodega:** primero se atiende el flujo indispensable que permite abrir la caja, cobrar latas en efectivo, emitir la constancia interna y cuadrar el dinero.
2. **Dependencias:** una historia habilitadora se programa antes que las historias que dependen de ella.
3. **Control operativo:** el ingreso seguro, el control de existencias por lotes, la caja única y el cobro ordenado se atienden temprano.
4. **Claridad del trabajo:** las historias próximas deben estar claras antes de seleccionarse.
5. **Aprendizaje empírico:** el alcance posterior se ajustará con la evidencia de las historias terminadas en cada Sprint; no constituye una promesa anticipada.

Los Story Points representan el tamaño relativo y la complejidad estimada por el equipo de Developers. **No equivalen a horas de trabajo.** La velocidad real del equipo no existe previamente y solo se conocerá tras cerrar un Sprint con trabajo Hecho y comprobado.

La columna **Depende de** expresa precedencia funcional para completar o aceptar una Story, no una prohibición automática de comenzar todas sus Tasks. Los Developers pueden trabajar en paralelo sobre contratos, interfaz, persistencia y pruebas preparatorias cuando el diseño aprobado lo permita. En Jira se usa un enlace bloqueante solo si la entrega predecesora es indispensable para ejecutar o validar la sucesora; las dependencias de integración se etiquetan como tales y no crean una cadena artificial de inicio a fin.

---

## 9.2 Corte del primer release

### `R1-PMV` — Venta en efectivo en caja única de mostrador

- **Sprint:** Sprint 1.
- **Fechas:** inicio sábado 10 de octubre de 2026; corte de exposición martes 13 a las 20:00; fin máximo viernes 23 de octubre de 2026.
- **Alcance seleccionado:** 9 historias de usuario, 40 Story Points.
- **Resultado esperado:** un empleado identificado puede registrar un producto enlatado, ingresar existencias iniciales por lotes con vencimiento, abrir la caja única con dinero inicial, preparar y cobrar una venta en efectivo vendiendo primero lo que vence antes, emitir una constancia interna numerada y cerrar la caja cuadrando el dinero.
- **Límite documental:** `HU-VEN-02a` produce únicamente una constancia interna de la bodega sin validez tributaria. La boleta o factura oficial se entrega por el canal autorizado habitual del minimarket.
- **Datos preparados:** antes de operar se crean de forma reproducible la categoría activa «Productos enlatados», la caja única y tres cuentas ficticias separadas con roles exclusivos `ADMIN`, `ALMACENERO` y `VENDEDOR`. Las credenciales reales no forman parte de este documento.

---

## 9.3 Lista maestra ordenada

### 9.3.1 Sprint 1 / `R1-PMV` — Seleccionado (9 HUs · 40 SP)

| Orden | ID | Historia de usuario | Epic | Prioridad | SP | Versión | Sprint | Depende de |
|:---:|---|---|---|:---:|:---:|:---:|:---:|---|
| 1 | `HU-AUTH-01` | Ingresar con mi cuenta de trabajo | Ingreso y personal | Indispensable | 5 | `R1-PMV` | Sprint 1 | Ninguna |
| 2 | `HU-AUTH-03` | Salir de mi cuenta al terminar | Ingreso y personal | Indispensable | 2 | `R1-PMV` | Sprint 1 | `HU-AUTH-01` |
| 3 | `HU-PROD-02` | Registrar un producto enlatado | Productos y proveedores | Indispensable | 5 | `R1-PMV` | Sprint 1 | `HU-AUTH-01` y preparación inicial de la categoría “Productos enlatados” |
| 4 | `HU-INV-01a` | Registrar las existencias iniciales por lotes | Mercadería y reposición | Indispensable | 5 | `R1-PMV` | Sprint 1 | `HU-PROD-02` |
| 5 | `HU-CAJA-01` | Abrir el turno de caja | Ventas y caja | Indispensable | 5 | `R1-PMV` | Sprint 1 | `HU-AUTH-01` |
| 6 | `HU-VEN-01b` | Preparar una venta y revisar existencias | Ventas y caja | Indispensable | 5 | `R1-PMV` | Sprint 1 | `HU-CAJA-01` y `HU-INV-01a` |
| 7 | `HU-VEN-01c` | Cobrar en efectivo y descontar existencias | Ventas y caja | Indispensable | 5 | `R1-PMV` | Sprint 1 | `HU-VEN-01b` |
| 8 | `HU-VEN-02a` | Generar una constancia interna de venta | Ventas y caja | Indispensable | 3 | `R1-PMV` | Sprint 1 | `HU-VEN-01c` |
| 9 | `HU-CAJA-02` | Cerrar y cuadrar la caja | Ventas y caja | Indispensable | 5 | `R1-PMV` | Sprint 1 | Habilitación: `HU-CAJA-01`; integración del recorrido: `HU-VEN-01c` |
| **Total** | | **9 historias seleccionadas** | | | **40** | | | |

---

### 9.3.2 Product Backlog posterior sin Sprint comprometido (65 HUs · 191 SP)

Estas 65 historias permanecen activas en el Product Backlog. No tienen Sprint ni versión asignados anticipadamente. Su selección se evaluará en futuros refinamientos y reuniones de planificación conforme a la velocidad real obtenida.

| Orden | ID | Historia de usuario | Epic | Prioridad | SP | Versión | Sprint | Depende de |
|:---:|---|---|---|:---:|:---:|:---:|:---:|---|
| 10 | `HU-CAT-02` | Categorías — Crear nueva categoría de productos | Productos y proveedores | Indispensable | 2 | — | — | `HU-AUTH-01` |
| 11 | `HU-CAT-01` | Categorías — Ver lista de categorías de productos | Productos y proveedores | Indispensable | 1 | — | — | `HU-AUTH-01` y datos iniciales de categoría |
| 12 | `HU-PROD-01` | Productos — Ver catálogo completo de productos | Productos y proveedores | Indispensable | 3 | — | — | `HU-PROD-02` |
| 13 | `HU-PROD-04` | Productos — Editar datos de un producto | Productos y proveedores | Importante | 3 | — | — | `HU-PROD-02` |
| 14 | `HU-PROD-05` | Productos — Gestionar estado de disponibilidad comercial | Productos y proveedores | Importante | 2 | — | — | `HU-PROD-02` |
| 15 | `HU-PROD-06` | Productos — Consultar vencimientos de productos | Productos y proveedores | Indispensable | 3 | — | — | `HU-INV-01a` |
| 16 | `HU-VEN-05a` | Ventas — Consultar las ventas de mi turno | Ventas y caja | Indispensable | 2 | — | — | `HU-VEN-01c` y `HU-CAJA-01` |
| 17 | `HU-VEN-05b` | Ventas — Consultar el historial de ventas con filtros | Ventas y caja | Indispensable | 3 | — | — | `HU-VEN-01c` |
| 18 | `HU-CAJA-05` | Caja — Consultar historial de turnos de caja | Ventas y caja | Indispensable | 3 | — | — | `HU-CAJA-02` |
| 19 | `HU-VEN-01a` | Ventas — Bloquear la pantalla de venta por inactividad | Ventas y caja | Indispensable | 3 | — | — | `HU-CAJA-01` |
| 20 | `HU-AUTH-02` | Autenticación — Bloquear cuenta por intentos fallidos | Ingreso y personal | Indispensable | 3 | — | — | `HU-AUTH-01` |
| 21 | `HU-USR-02` | Usuarios — Crear cuenta de nuevo empleado | Ingreso y personal | Indispensable | 5 | — | — | `HU-AUTH-01` |
| 22 | `HU-USR-01` | Usuarios — Listar empleados del sistema | Ingreso y personal | Indispensable | 2 | — | — | `HU-AUTH-01` y cuentas iniciales |
| 23 | `HU-USR-04` | Usuarios — Desactivar cuenta de empleado | Ingreso y personal | Indispensable | 3 | — | — | `HU-USR-01` |
| 24 | `HU-INV-02` | Inventario — Registrar baja de inventario por merma | Mercadería y reposición | Indispensable | 5 | — | — | `HU-INV-01a` |
| 25 | `HU-INV-03` | Inventario – Realizar ajuste por conteo físico | Mercadería y reposición | Indispensable | 5 | — | — | `HU-INV-01a` |
| 26 | `HU-INV-04` | Mercadería — Consultar movimientos de un producto | Mercadería y reposición | Importante | 2 | — | — | `HU-INV-01a`, `HU-VEN-01c`, `HU-INV-02` y `HU-INV-03` |
| 27 | `HU-INV-05` | Inventario — Consultar historial de bajas | Mercadería y reposición | Importante | 2 | — | — | `HU-INV-02` |
| 28 | `HU-INV-06` | Inventario — Consultar historial de ajustes | Mercadería y reposición | Importante | 2 | — | — | `HU-INV-03` |
| 29 | `HU-VEN-06a` | Ventas — Anular una venta cobrada en efectivo | Ventas y caja | Indispensable | 3 | — | — | `HU-VEN-01c` y `HU-VEN-02a` |
| 30 | `HU-VEN-06c` | Ventas — Definir el destino de la mercadería devuelta | Ventas y caja | Indispensable | 3 | — | — | `HU-VEN-06a` y `HU-INV-02` |
| 31 | `HU-VEN-07` | Cobrar con Yape y registrar el código de operación | Ventas y caja | Indispensable | 2 | — | — | `HU-VEN-01b` y `HU-VEN-01c` |
| 32 | `HU-VEN-06b` | Ventas — Anular una venta cobrada con Yape | Ventas y caja | Importante | 2 | — | — | `HU-VEN-06a` y `HU-VEN-07` |
| 33 | `HU-CAJA-03` | Caja — Registrar movimiento manual de efectivo | Ventas y caja | Importante | 3 | — | — | `HU-CAJA-01` |
| 34 | `HU-CAJA-04` | Caja — Ver resumen del turno activo | Ventas y caja | Importante | 2 | — | — | `HU-CAJA-01`, `HU-VEN-01c` y `HU-CAJA-03` |
| 35 | `HU-CAJA-06` | Caja — Aprobar cierre de turno | Ventas y caja | Importante | 2 | — | — | `HU-CAJA-02` |
| 36 | `HU-CAJA-07` | Caja – Forzar cierre de turno de caja | Ventas y caja | Importante | 5 | — | — | `HU-CAJA-01` |
| 37 | `HU-CONF-01` | Configuración — Ver configuración actual del negocio | Control del negocio | Indispensable | 1 | — | — | `HU-AUTH-01` |
| 38 | `HU-CONF-02` | Configuración — Actualizar configuración del negocio | Control del negocio | Indispensable | 3 | — | — | `HU-CONF-01` |
| 39 | `HU-PROV-02` | Proveedores — Registrar nuevo proveedor | Productos y proveedores | Indispensable | 3 | — | — | `HU-AUTH-01` |
| 40 | `HU-PROV-01` | Proveedores — Ver lista de proveedores | Productos y proveedores | Indispensable | 2 | — | — | `HU-AUTH-01` |
| 41 | `HU-PROV-04` | Proveedores — Gestionar estado de vigencia del proveedor | Productos y proveedores | Importante | 2 | — | — | `HU-PROV-01` |
| 42 | `HU-INV-01b` | Inventario — Recalcular el costo promedio en entradas posteriores | Mercadería y reposición | Indispensable | 2 | — | — | `HU-INV-01a` |
| 43 | `HU-SOL-01` | Reposición – Crear solicitud de reposición | Mercadería y reposición | Indispensable | 3 | — | — | `HU-PROD-02`, `HU-PROV-02` |
| 44 | `HU-SOL-02` | Reposición — Listar solicitudes con filtro por estado | Mercadería y reposición | Indispensable | 2 | — | — | `HU-SOL-01` |
| 45 | `HU-SOL-03` | Reposición — Aprobar solicitud de reposición | Mercadería y reposición | Indispensable | 3 | — | — | `HU-SOL-01` |
| 46 | `HU-SOL-04` | Reposición — Rechazar solicitud de reposición | Mercadería y reposición | Importante | 2 | — | — | `HU-SOL-01` |
| 47 | `HU-SOL-05a` | Reposición — Completar la recepción total de una solicitud | Mercadería y reposición | Indispensable | 5 | — | — | `HU-SOL-03`, `HU-INV-01a`, `HU-INV-01b` |
| 48 | `HU-SOL-05b` | Reposición — Registrar una recepción parcial con saldo pendiente | Mercadería y reposición | Indispensable | 3 | — | — | `HU-SOL-05a` |
| 49 | `HU-REP-05` | Reportes – Consultar reporte de productos bajo stock mínimo | Control del negocio | Indispensable | 3 | — | — | `HU-INV-01a` |
| 50 | `HU-DASH-03` | Resumen del negocio – Ver alertas operativas (stock crítico, vencimientos y turnos) | Control del negocio | Indispensable | 5 | — | — | `HU-INV-01a`, `HU-CAJA-05` y `HU-PROD-06` |
| 51 | `HU-DASH-01` | Resumen del negocio — Ver indicadores de ventas en tiempo real | Control del negocio | Indispensable | 5 | — | — | `HU-VEN-01c` |
| 52 | `HU-REP-01` | Reportes — Consultar reporte analítico de ventas totales por período | Control del negocio | Indispensable | 5 | — | — | `HU-VEN-01c` |
| 53 | `HU-REP-02` | Reportes – Consultar reporte completo de ranking de productos más vendidos | Control del negocio | Indispensable | 3 | — | — | `HU-VEN-01c` |
| 54 | `HU-REP-04` | Reportes — Ver ventas por método de pago | Control del negocio | Importante | 2 | — | — | `HU-VEN-01c` y `HU-VEN-07` |
| 55 | `HU-REP-06` | Reportes — Ver resumen general del inventario | Control del negocio | Importante | 2 | — | — | `HU-INV-01a` |
| 56 | `HU-REP-07` | Reportes — Ver margen de ganancia por producto | Control del negocio | Importante | 5 | — | — | `HU-VEN-01c` y `HU-INV-01a` |
| 57 | `HU-REP-08` | Reportes — Ver mermas agrupadas por motivo | Control del negocio | Importante | 3 | — | — | `HU-INV-02` |
| 58 | `HU-DASH-02` | Resumen del negocio — Ver gráfico de evolución de ventas por día | Control del negocio | Importante | 3 | — | — | `HU-VEN-01c` |
| 59 | `HU-DASH-04` | Resumen del negocio – Ver ranking de productos más vendidos | Control del negocio | Importante | 3 | — | — | `HU-VEN-01c` |
| 60 | `HU-DASH-05` | Resumen del negocio — Ver solicitudes de reposición pendientes | Control del negocio | Importante | 2 | — | — | `HU-SOL-01` |
| 61 | `HU-REP-03` | Reportes — Ver ventas desglosadas por día | Control del negocio | Importante | 3 | — | — | `HU-VEN-01c` |
| 62 | `HU-REP-09` | Reportes — Exportar reportes analíticos de gestión a PDF | Control del negocio | Deseable | 3 | — | — | `HU-REP-01`, `HU-REP-02`, `HU-REP-05`, `HU-REP-07` y `HU-REP-08` |
| 63 | `HU-AUTH-04a` | Autenticación — Cerrar automáticamente la sesión previa | Ingreso y personal | Indispensable | 5 | — | — | `HU-AUTH-01`, `HU-AUTH-03` |
| 64 | `HU-AUTH-04b` | Autenticación — Descartar venta sin confirmar al cerrarse la sesión | Ingreso y personal | Indispensable | 3 | — | — | `HU-AUTH-04a`, `HU-VEN-01b` |
| 65 | `HU-AUTH-05` | Autenticación — Recuperar contraseña por correo | Ingreso y personal | Importante | 5 | — | — | `HU-AUTH-01` |
| 66 | `HU-USR-06` | Usuarios — Forzar cierre de sesión remoto | Ingreso y personal | Importante | 3 | — | — | `HU-USR-01` y `HU-AUTH-01` |
| 67 | `HU-USR-03` | Usuarios — Editar datos y rol de un empleado | Ingreso y personal | Importante | 3 | — | — | `HU-USR-02` |
| 68 | `HU-USR-05` | Usuarios — Reactivar cuenta de empleado | Ingreso y personal | Importante | 2 | — | — | `HU-USR-04` |
| 69 | `HU-LOG-01` | Supervisión de accesos – Consultar registro de accesos | Ingreso y personal | Importante | 3 | — | — | `HU-AUTH-01` y `HU-AUTH-02` |
| 70 | `HU-CAT-03` | Categorías — Editar nombre de categoría | Productos y proveedores | Importante | 1 | — | — | `HU-CAT-02` |
| 71 | `HU-CAT-04` | Categorías — Eliminar categoría sin productos | Productos y proveedores | Deseable | 2 | — | — | `HU-CAT-02` y `HU-PROD-01` |
| 72 | `HU-PROD-03` | Productos — Escanear código de barras para registrar producto | Productos y proveedores | Deseable | 5 | — | — | `HU-PROD-02` |
| 73 | `HU-VEN-04` | Ventas – Buscar producto por código de barras | Ventas y caja | Importante | 3 | — | — | `HU-VEN-01b` |
| 74 | `HU-PROV-03` | Proveedores — Editar datos de un proveedor | Productos y proveedores | Importante | 2 | — | — | `HU-PROV-02` |
| **Total** | | **65 historias activas sin Sprint comprometido** | | | **191** | | | |

---

## 9.4 Ideas fuera del horizonte académico

Estas ocho historias no forman parte de las 74 historias de usuario activas ni suman puntos en el Product Backlog. Se conservan registradas para documentar explícitamente el motivo de su exclusión.

| ID | Historia | Epic | Prioridad | SP | Motivo explícito de exclusión |
|---|---|---|:---:|:---:|---|
| `HU-CLI-01` | Clientes — Listar clientes registrados | Productos y proveedores | Fuera del alcance | 0 | El registro y seguimiento formal de clientes con comprobantes nominales excede la atención en mostrador a público general. |
| `HU-CLI-02` | Clientes — Captura y reconocimiento de clientes en ventas nominales | Productos y proveedores | Fuera del alcance | 0 | La captura de DNI o RUC con validación fiscal corresponde a la facturación electrónica futura, fuera del horizonte académico. |
| `HU-CLI-03` | Clientes — Editar correo electrónico de cliente | Productos y proveedores | Fuera del alcance | 0 | Depende del mantenimiento de clientes nominales, función fuera del alcance del minimarket. |
| `HU-VEN-02b` | Ventas — Emitir boleta nominal de más de S/ 700.00 | Ventas y caja | Fuera del alcance | 0 | La emisión de comprobantes de pago autorizados con valor tributario se efectúa por el canal externo del negocio. |
| `HU-VEN-02c` | Ventas — Emitir factura comercial con RUC | Ventas y caja | Fuera del alcance | 0 | La facturación electrónica con RUC se gestiona por el canal tributario oficial fuera de este sistema. |
| `HU-VEN-03` | Ventas – Generar comprobante en PDF o reenviar por correo | Ventas y caja | Fuera del alcance | 0 | El despacho digital de comprobantes electrónicos oficiales está supeditado a la facturación futura fuera de alcance. |
| `HU-VEN-08` | Ventas — Exportar historial de ventas a PDF | Ventas y caja | Fuera del alcance | 0 | Las consultas comerciales se atienden directamente en pantalla; los reportes analíticos cubren la exportación de gestión. |
| `HU-VEN-09` | Ventas — Registrar venta a granel o por peso | Ventas y caja | Fuera del alcance | 0 | La bodega comercializa exclusivamente productos envasados por unidad identificados con código de barras. |

---

## 9.5 Consolidado de control

### 9.5.1 Por prioridad

| Prioridad | Historias activas | Story Points | % de historias | % de puntos |
|---|---:|---:|---:|---:|
| Indispensable | 43 | 147 | 58.1 % | 63.6 % |
| Importante | 28 | 74 | 37.8 % | 32.0 % |
| Deseable | 3 | 10 | 4.1 % | 4.3 % |
| **Total activo** | **74** | **231** | **100.0 %** | **100.0 %** |

---

### 9.5.2 Por horizonte

| Horizonte | Naturaleza | Historias | Story Points | Estado |
|---|---|---:|---:|---|
| Sprint 1 / `R1-PMV` | Selección comprometida | 9 | 40 | Inicia sáb. 10-oct; corte de avance mar. 13-oct 20:00; final máximo vie. 23-oct. El corte no obliga a cerrar las 9 HU. |
| Product Backlog posterior | Sin Sprint ni versión comprometida | 65 | 191 | Activo y reordenable según valor y dependencias |
| **Total activo** | | **74** | **231** | |

---

### 9.5.3 Por Epic

| Epic | Historias activas | Story Points | Aporte a la bodega |
|---|---:|---:|---|
| Ingreso y personal | 13 | 44 | Identificación de empleados, cuentas y seguridad de acceso. |
| Productos y proveedores | 14 | 36 | Artículos enlatados, categorías y proveedores de mercadería. |
| Mercadería y reposición | 13 | 41 | Lotes con vencimiento, costo promedio, pedidos y entradas de almacén. |
| Ventas y caja | 18 | 59 | Atención en mostrador, caja única, cobro en efectivo y constancia interna. |
| Control del negocio | 16 | 51 | Resumen del negocio, alertas de vencimiento, reportes de ganancia y parámetros. |
| **Total** | **74** | **231** | |

---

### 9.5.4 Por tamaño

| Tamaño | Historias de usuario | Story Points acumulados |
|:---:|---:|---:|
| 1 SP | 3 | 3 |
| 2 SP | 23 | 46 |
| 3 SP | 29 | 87 |
| 5 SP | 19 | 95 |
| **Total** | **74** | **231** |

---

## 9.6 Reglas de registro en Jira

1. Registrar las cinco Epics y las 74 historias de usuario activas; las ocho ideas fuera del alcance pueden conservarse con estado descartado y 0 Story Points.
2. Asignar la versión `R1-PMV` y el Sprint 1 únicamente a las nueve historias seleccionadas de la sección 9.3.1.
3. Configurar Sprint 1 con inicio real el sábado 10 de octubre, corte de exposición el martes 13 a las 20:00 y fecha máxima de fin el viernes 23 de octubre de 2026.
4. Mantener las 65 historias posteriores sin Sprint y sin versión hasta que el equipo las seleccione formalmente en reuniones posteriores.
5. No crear asignaciones anticipadas para futuros Sprints en Jira.
6. Estimar las historias de usuario en Story Points relativos y las tareas con esfuerzo de trabajo.
7. Crear las Tasks técnicas transversales y las Subtasks específicas de las nueve Stories conforme al desglose aprobado; no tratarlas como HUs nuevas ni asignarles Story Points.
8. Reflejar en Jira únicamente las dependencias duras mediante `blocks / is blocked by`; registrar las dependencias de integración o aceptación sin impedir trabajo preparatorio paralelo.
9. Mantener cada Subtask vinculada a una de las nueve Stories y cada Task transversal enlazada a las Stories que apoya, con criterio/RN/NFR, evidencia esperada, responsable y revisor distintos cuando se ratifique el reparto.
10. Usar las 216 h y los responsables de `16_Task_Breakdown.md` como propuesta de carga. Registrar 32 h disponibles por Developer hasta el corte (192 h-persona), tiempo real y trabajo restante; todas las incidencias y pruebas se crean en `Por hacer`: la simulación documental no constituye ejecución.
11. No modificar Story Points durante el Sprint sin justificación y acuerdo del equipo.

---

## 9.7 Verificación de coherencia

- [x] Sprint 1 contiene exactamente 9 historias de usuario y 40 Story Points.
- [x] Existen 74 historias de usuario activas sin IDs repetidos.
- [x] Las historias activas suman exactamente 231 Story Points.
- [x] Se encuentran registradas exactamente 8 ideas fuera del horizonte académico con 0 Story Points.
- [x] Ninguna historia posterior está asignada a futuros Sprints.
- [x] `HU-INV-01a` tiene asignados 5 Story Points.
- [x] `HU-CAT-02` permanece activa pero no pertenece a Sprint 1.
- [x] Se eliminó cualquier monto mínimo obligatorio para la apertura de caja.
- [x] Se sustituyeron las palabras técnicas por expresiones cotidianas del negocio.
- [x] Los nombres de las nueve historias de Sprint 1 coinciden fielmente con los definidos en el archivo 08.
- [x] No se realiza equivalencia entre horas y Story Points ni se asume una velocidad histórica previa.

> **Complemento de auditoría · 09/11/2026.** La selección histórica de AUTH-02 se conserva y su implementación adicional consta en el cierre. Los refinamientos y tareas pendientes mantienen el estado PROPUESTO. [Resultados de etapa 01](auditoria_por_etapas/resultados/ETAPA-01.md) · [Decisiones y traspaso](auditoria_por_etapas/resultados/anexos/ETAPA-01-cierre-y-traspaso.md)

> **Complemento de auditoría ·09/11/2026 (cierre02-D).** 11 HU/33 CA:15 CUMPLE muestra,3 PARCIAL por nombres/apellidos y confirmación,15 PREVISTO/FUTURO. AUTH03 R1 seleccionado; USR01..05 adicional implementado, auditado en navegador/servidor.163/163 métodos,32/32 salida,20/20 empleados y6 escenarios PostgreSQL. Eventos técnicos R1 siguen INCUMPLE; propuestas/decisiones no aceptadas automáticamente. AUTH04a/04b/05,USR06 yLOG01 no disponibles. Estados históricos preservados. [Resultados y límites](auditoria_por_etapas/resultados/ETAPA-02.md) · [Criterios](auditoria_por_etapas/resultados/anexos/ETAPA-02-criterios.md) · [Cierre y traspaso](auditoria_por_etapas/resultados/anexos/ETAPA-02-cierre-y-traspaso.md).

## Adenda del alcance actual · 09/11/2026 · DOC03-01

Para HU-PROD-02 se acepta registrar productos de cualquier categoría activa, por unidad UND y con vencimiento obligatorio. Su denominación vigente es «Registrar un producto por unidad con vencimiento» y CA01 está actualizado en08. La selección, título, estimación y alcance de la tabla histórica de Sprint1/R1 anterior se conservan; esta adenda no asigna retrospectivamente puntos, fechas o sprints ni suma una HU duplicada. DOC-00-14 se concilia con el pedido del usuario: HU-PROD-01 consulta de ADMIN/ALMACENERO; VENDEDOR mediante VEN-01b. CAT03/04 y PROD03 siguen futuros. [Decisión y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-F-alcance.md).

**Adenda DOC03-02 (09/11/2026):** HU-PROD-04 incorpora corrección ADMIN del código, con unicidad normalizada e históricos conservados, por decisión expresa. Se mantiene el mismo ID y no se reestima ni cambia el Sprint histórico. HU-PROD-03 usará Barcode to PC Server; tecnología identificada, integración/aviso al leer aún sin aceptación de ejecución. No se declara implementada la HU futura. [Detalle y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-G-codigo-y-lector.md).


## Adenda03-I · 10/11/2026 · decisiones aceptadas

PROP-03C-LIMITES y PROP-03C-NOMBRE aceptadas mediante «bien, continua»: mínimo0..999999/predeterminado10 y nombre único normalizado. Se refinan PROD02-CA01/CA04 y PROD04-CA04 sin añadir HU, puntos ni alterar estados históricos de Sprint. Implementadas y verificadas en muestra aislada, migración de uso real pendiente.

[Evidencia y límites03-I](auditoria_por_etapas/resultados/anexos/ETAPA-03-I-politicas.md).


## Refinamiento de categorías · 10/11/2026

El usuario aceptó confirmar la activación y desactivación con explicación de impacto y rechazar la pantalla antigua cuando otro administrador haya cambiado el estado. La propuesta existente PROP-E00-HU-02 incorpora los cuatro criterios suplementarios de la adenda de 08. Implementación y pruebas en datos aislados completadas. El despliegue de catalog.0006 queda pendiente. Se conservan las asignaciones y estimaciones históricas.

[Auditoría 03-J](auditoria_por_etapas/resultados/anexos/ETAPA-03-J-estado-categoria.md).


**Adenda03-O,10/11/2026:** HU-PROD-03 seleccionado para catálogo actual por petición de aplicar mejoras pendientes, sin cambiar estimación ni Sprint históricos. CA01 cuenta con captura físicaK9; CA02 implementado y verificado por Chrome/API enO, aviso físico nuevo pendiente. Se mantiene Barcode to PC y confirmación expresa de copia/guardado. CAT03/04 continúan futuros. [Detalle y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-N-O-reclasificacion-y-duplicados.md).

**Vigencia 03-P/W, 10/11/2026:** PROD03/CA02 tiene evidencia física del aviso en P; CA01 usa campo temporal y copia expresa, con discrepancia literal frente al criterio original documentada en W. CAT03/04 permanecen futuros. No cambian estimaciones ni estados históricos de sprint. [Conciliación](auditoria_por_etapas/resultados/anexos/ETAPA-03-W-conciliacion.md).

**Actualización03-X,11/11/2026 (ejecución10/11):** PROD03/CA02 queda PARCIAL en la frontera EAN13/UPC12: seis lecturas físicas recibieron12 dígitos ante una ficha almacenada con13 y el aviso no indicó duplicado. La unicidad literal conserva sus muestras favorables.69/69 controles navegador/HTTP/ORM,16/16 servicio/DB y9/9 observación física; estos últimos acreditan la observación, no la equivalencia. DEC-03X-IDENTIDAD y PROP-03X-CA01..03/T01..03 son propuestas pendientes, sin cambio funcional, fusión ni migración. No se modifican estimaciones/sprints históricos ni se aprueban otras etapas. [Evidencia, alternativas y criterios](auditoria_por_etapas/resultados/anexos/ETAPA-03-X-codigos-ean-upc.md).

**Actualización 03-Y · 11/11/2026.** DEC-03X-IDENTIDAD resuelta por el usuario. Implementadas la clasificación explícita y las reservas únicas. Pendientes la migración operativa y la revisión individual de cinco fichas. [Evidencia 03-Y](auditoria_por_etapas/resultados/anexos/ETAPA-03-Y-identidad.md).


**Auditoría 11/11/2026 · 03-AH, propuesta pendiente.** DOC-03AH-01 requiere seleccionar cómo se valora stock vencido y cómo merma/ajuste afectan al promedio. PROP-03AH-CA01/02 y T-03AH-VAL01/TEST02 están propuestos, no aceptados ni implementados; T-03AH-TEST01 reproduce la divergencia y conservación histórica. No se alteran CA ni estados históricos. [Alternativas, criterios y pruebas](auditoria_por_etapas/resultados/anexos/ETAPA-03-AH-valoracion-vencidos.md).


**Auditoría 11/11/2026 · 03-AI.** PROP-03-RET-T05 dispone de muestra de pérdida de respuesta en reposición y reenvíos sin duplicación de lotes. No acredita idempotencia por intención: DOC-03AI-01 y PROP-03AI-REC01/TEST02 son propuestas pendientes. No modifica estados históricos. [Criterios, alternativas y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-AI-reposicion-respuesta.md).
