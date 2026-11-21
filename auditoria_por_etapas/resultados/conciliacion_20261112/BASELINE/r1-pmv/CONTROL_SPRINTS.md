# Control de estado — Sprints R1-PMV

> **Lectura actual:** registro histórico de resultados declarados. Los totales y marcas de completado corresponden a ejecuciones anteriores y no acreditan que cada criterio de aceptación siga cumplido. Para discrepancias conocidas y límites, consulte [la guía actual](../21_Alcance_Actual_y_Diferencias.md).

## Sprint 1 — COMPLETADO ✅

**Periodo:** Sprint 1  
**HUs implementadas:** 9 / 9  
**Story Points:** 40 SP  
**Tests (suite final):** 95 tests, OK, exit 0  

| HU | Descripción | Estado |
|---|---|---|
| HU-PROD-02 | Registrar producto enlatado | ✅ Completada |
| HU-INV-01a | Registrar carga inicial de inventario | ✅ Completada |
| HU-VEN-01b | Preparar una venta y revisar existencias | ✅ Registrada históricamente |
| HU-CAJA-01 | Abrir turno de caja | ✅ Completada |
| HU-CAJA-02 | Cerrar turno de caja | ✅ Completada |
| HU-AUTH-01 | Ingresar con cuenta de trabajo | ✅ Registrada históricamente |
| HU-AUTH-03 | Cerrar sesión | ✅ Registrada históricamente |
| HU-VEN-01c | Cobrar en efectivo y descontar existencias | ✅ Completada |
| HU-VEN-02a | Ver constancia de venta | ✅ Completada |

---

## Sprint 2 — COMPLETADO ✅

**Periodo:** Sprint 2  
**HUs implementadas:** 11 / 11  
**Story Points:** 29 SP  
**Tests (suite final):** 126 tests, OK, exit 0  

| HU | Descripción | Estado |
|---|---|---|
| HU-CAT-01 | Ver lista de categorías | ✅ Completada |
| HU-CAT-02 | Crear nueva categoría | ✅ Completada |
| HU-PROD-01 | Ver catálogo completo de productos | ✅ Completada |
| HU-PROD-04 | Editar datos de un producto | ✅ Completada |
| HU-PROD-05 | Gestionar estado de disponibilidad | ✅ Completada |
| HU-PROD-06 | Consultar vencimientos de productos | ✅ Completada |
| HU-VEN-05a | Historial de ventas del turno actual | ✅ Completada |
| HU-VEN-05b | Historial completo de ventas | ✅ Completada |
| HU-CAJA-05 | Historial de turnos de caja | ✅ Completada |
| HU-USR-01 | Lista de empleados | ✅ Completada |
| HU-USR-02 | Crear nuevo empleado | ✅ Completada |

---

## Sprint 3 — COMPLETADO ✅

**Periodo:** Sprint 3  
**HUs implementadas:** 8 / 8  
**Story Points:** 25 SP  
**Tests (suite final):** 152 tests, OK, exit 0  

| HU | Descripción | Estado |
|---|---|---|
| HU-USR-03 | Editar datos y rol de empleado | ✅ Completada |
| HU-USR-04 | Desactivar/reactivar cuenta de empleado | ✅ Completada |
| HU-PROV-01 | Ver lista de proveedores | ✅ Completada |
| HU-PROV-02 | Registrar nuevo proveedor | ✅ Completada |
| HU-PROV-04 | Gestionar estado de vigencia del proveedor | ✅ Completada |
| HU-INV-01b | Recalcular costo promedio en entradas posteriores | ✅ Completada |
| HU-INV-02 | Registrar baja de inventario por merma | ✅ Completada |
| HU-INV-03 | Ajuste por conteo físico | ✅ Completada |

---

## Resumen acumulado

| Sprint | SP | Tests | Estado |
|---|---|---|---|
| Sprint 1 | 40 SP | 95 | ✅ OK |
| Sprint 2 | 29 SP | 126 (acum.) | ✅ OK |
| Sprint 3 | 25 SP | 152 (acum.) | ✅ OK |
| Post-Sprint (Rondas 1–5) | — | 163 (acum.) | ✅ OK |
| Post-Sprint (Auditoría Caos y UX `BUG-001..037`) | — | 202 (acum.) | ✅ OK |
| **Total** | **94 SP** | **202** | **✅ Verde** |



## Post-Sprint — Mejoras de usabilidad y corrección de hallazgos exploratorios (05-NOV-2026)

| HU / Ref. | Descripción | Estado | Evidencia |
|---|---|---|---|
| Sin identificador de HU validado | Ver stock actual | Disponible en interfaz | `/inventario/stock/` (`inventory/views.py::stock_overview`) |
| Sin identificador de HU validado | Alertas de stock y vencimiento | Disponible en interfaz | Panel en `/inventario/stock/` unificado con `/inicio/` |
| HU-INV-04 (parcial) | Historial de movimientos por producto (incluye ventas, entradas, mermas y ajustes) | Requiere validar todos los criterios | `/inventario/productos/<id>/movimientos/` (`inventory/views.py::product_movements`) |
| Sin identificador de HU validado | Descuento en venta (monto S/) con recálculo en vivo en caja | Disponible en interfaz | Migración `sales/0003`, `checkout_sale`, `sales_checkout.html` |
| Sin identificador de HU validado | Resumen del negocio | Disponible en interfaz | Panel en `/inicio/` (`identity/views.py::_admin_summary`) |
| `HAL-001`..`HAL-033` | Corrección de 33 hallazgos de pruebas exploratorias (errores 500, coherencia entre roles, permisos, idempotencia y usabilidad) | ✅ Completada | 163 tests en verde (`manage.py test`) · `REPORTE_PRUEBAS_EXPLORATORIAS_05NOV2026.md` §8 |
| `BUG-001`..`BUG-037` | Corrección integral de los 37 hallazgos de la Auditoría de Caos Multi-Rol y UX/UI (bloqueo de cambio de rol con turno abierto, diferencias en historial de turnos, idempotencia y `@never_cache` en mermas/ajustes con prioridad de `POST lot_id`, FK `SaleLine.product` e inmutabilidad de snapshot en Kardex/constancias, migraciones `Lot.supplier`, `Lot.is_initial` y `Lot.responsible` con acceso de `ADMIN` a `/inventario/cargas/<id>/`, recálculo de `average_cost` en entradas/mermas/ajustes, sincronización de precios/disponibilidad y firma `draft_signature` con `draft.pk` multi-pestaña en cobro, expiración de 5 min en bloqueo de login, validación de `unit_cost` contra notación científica, ciclo de vida completo de categorías activas/inactivas, `seed_demo` con `average_cost`, y unificación de estilos CSS) | ✅ Completada | **202 tests en verde (`manage.py test`)** · `REPORTE_CAOS_Y_UX_QA.md` §8 |

Detalle y verificación completa: `AUDITORIA_USABILIDAD_05NOV2026.md` (secciones 13, 14, 15, 16 y 17), `REPORTE_PRUEBAS_EXPLORATORIAS_05NOV2026.md` (sección 8) y `REPORTE_CAOS_Y_UX_QA.md` (sección 8).
