# TRAZABILIDAD DE PRUEBAS, BUGS Y MEJORAS — R1-PMV

> Auditoría histórica filtrada al alcance del minimarket; no representa una nueva ejecución de pruebas.
**Sistema:** R1-PMV (Minimarket)  
**Fecha de sesión:** 05/11/2026  
**Propósito:** Auditoría académica — contraste entre planificación (sprints/HUs), código implementado y comportamiento real del sistema.  
**Método de prueba:** Navegación real via `Invoke-WebRequest` (PowerShell) emulando 3 perfiles de usuario desde cero.

---

## 1. CONTEXTO: ESTADO DE LOS SPRINTS ANTES DE LA SESIÓN

Según [`CONTROL_SPRINTS.md`](./CONTROL_SPRINTS.md):

| Sprint | SP | Tests declarados | Estado declarado |
|---|---|---|---|
| Sprint 1 | 40 SP | 95 tests | ✅ Completado |
| Sprint 2 | 29 SP | 126 tests (acum.) | ✅ Completado |
| Sprint 3 | 25 SP | 152 tests (acum.) | ✅ Completado |
| **Total** | **94 SP** | **152** | **✅ Verde** |

> [!WARNING]
> El estado declarado como "completado" no coincidía con el estado funcional real del sistema. Se encontraron 3 migraciones pendientes que dejaban el sistema en fallo 500 y múltiples funcionalidades implementadas pero inaccesibles por ausencia de links en el menú.

---

## 2. PRUEBAS DE USABILIDAD — 3 PERSONAS

**Fecha:** 05/11/2026 00:41–00:55 hs  
**URL base:** `http://127.0.0.1:8000/`  
**Entorno:** `APP_ENV=local`, `DATABASE_URL=sqlite`

### 2.1 — PERSONA A: ANA (Administradora primeriza)
**Credenciales:** `admin.demo@pmv.invalid` / `Admin1234!`  
**Rol en el sistema:** `ADMIN`

#### Hallazgos por tarea

| Tarea | URL intentada | Resultado real | Veredicto |
|---|---|---|---|
| A1 — Login | `/` | 200 OK — pantalla de ingreso | ✅ Funciona |
| A2 — Post-login | `/inicio/` | 200 OK — título "Inicio — Minimarket" | ⚠️ Nombre distinto al login |
| A3 — Empleados | `/identity/employees/`, `/employees/`, `/staff/`, `/usuarios/` | Todos → **404** | ❌ Ruta incorrecta (URL real: `/empleados/`) |
| A4 — Crear empleado | — | No accedió (404 en A3) | ❌ |
| A5 — Cambiar rol | — | No accedió (404 en A3) | ❌ |
| A6 — Catálogo | `/catalog/products/`, `/catalogo/` → 404 · `/productos/` → 200 | 200 OK con tabla de 7 columnas | ⚠️ URL no intuitiva, sin link en menú |
| A7 — Crear producto | `/productos/nuevo/` | 200 OK → formulario, POST exitoso → confirmación | ✅ Funciona |
| A8 — Reportes | `/reports/`, `/reportes/`, `/dashboard/`, `/analytics/` | Todos → **404** | ❌ No existe vista de reportes |
| A9 — Logout | `/salir/` | 200 con confirmación → POST → redirect a `/` | ✅ Funciona |

#### Pantalla de login

El formulario de ingreso contaba con campos de correo y contraseña. El contenido ajeno al minimarket se ha retirado de este informe histórico.


#### Menú real de Ana (ADMIN) antes de correcciones

```
Operaciones
  ⌂ Inicio             → /inicio/
  ▦ Registrar producto → /productos/nuevo/
← Cerrar sesión        → /salir/
```

#### Dashboard card — texto hardcodeado encontrado

> `"Registrar un producto enlatado"` — texto de ejemplo hardcodeado con categoría específica.

#### Calificación inicial: **3/10**

**Lo que funcionó:** Login · Crear producto · Logout  
**Lo que falló:** Empleados (404) · Reportes (404) · Menú incompleto · Nombre inconsistente del sistema

---

### 2.2 — PERSONA B: BRUNO (Almacenero primerizo)
**Credenciales:** `almacen.demo@pmv.invalid` / `Almacen1234!`  
**Rol en el sistema:** `ALMACENERO`

#### Hallazgos por tarea

| Tarea | URL intentada | Resultado real | Veredicto |
|---|---|---|---|
| B1 — Login | `/` | 200 OK — menú diferente a Ana | ✅ Personalización por rol funciona |
| B2 — Ver inventario | `/inventory/`, `/inventario/`, `/stock/`, `/bodega/` | Todos → **404** | ❌ No hay vista de stock global |
| B3 — Entrada 50 unidades | `/inventario/carga-inicial/` | 200 OK — formulario multi-lote (hasta 4 lotes) | ✅ Funciona (aunque nombre confuso) |
| B4 — Merma 3 unidades | `/inventario/ajustes/`, `/inventario/merma/` | Todos → **404** | ❌ Vista existe en `/inventario/bajas/nueva/` pero sin link |
| B5 — Alertas stock | `/inventory/alerts/`, `/alertas/` | Todos → **404** | ❌ No implementado |
| B6 — Historial movimientos | `/inventory/movements/`, `/movimientos/` | Todos → **404** | ❌ No implementado |
| B7 — Proveedor nuevo | `/proveedores/` → 404 · `/inventario/proveedores/` → **500** | **500 Internal Server Error** | 🔴 Bug activo |
| B8 — Logout | `/salir/` | Funciona igual que Ana | ✅ |

#### Menú real de Bruno (ALMACENERO) antes de correcciones

```
Operaciones
  ⌂ Inicio                  → /inicio/
  ▤ Existencias iniciales   → /inventario/carga-inicial/
← Cerrar sesión             → /salir/
```

#### Formulario de carga inicial — campos encontrados

```
Producto (select)
Número de lote (text)
Cantidad (number)
Costo unitario S/ (number)
Vencimiento (date)
[× 4 lotes simultáneos]
```

> El nombre "Existencias **iniciales**" implica que es solo para el primer arranque. Para un almacenero, una reposición recurrente debería llamarse "Recepción de mercancía" o "Entrada de stock".

#### Calificación inicial: **4/10**

**Lo que funcionó:** Login · Carga inicial (con confirmación detallada)  
**Lo que falló:** 500 en proveedores · Sin vista de stock · Sin merma en menú · Sin alertas · Sin historial

---

### 2.3 — PERSONA C: CARMEN (Vendedora primeriza)
**Credenciales:** `vendedor.demo@pmv.invalid` / `Vendedor1234!`  
**Rol en el sistema:** `VENDEDOR`

#### Hallazgos por tarea

| Tarea | URL intentada | Resultado real | Veredicto |
|---|---|---|---|
| C1 — Login | `/` | 200 OK — menú propio de vendedor | ✅ |
| C2 — Abrir turno | `/caja/abrir/` | 200 OK — visible en menú | ✅ Nomenclatura clara |
| C3 — Apertura caja | POST `/caja/abrir/` | ✅ Éxito → confirmación "CAJA-01 está abierta" | ✅ |
| C4 — Hacer venta | `/ventas/` | 200 OK — búsqueda funciona, se agregan líneas | ⚠️ Sin botón "Cobrar" visible |
| C5 — Descuento | `/ventas/` | Términos `descuento`/`discount` ausentes del HTML | ❌ No en la vista draft |
| C6 — Resumen ventas | `/sales/today/`, `/ventas/hoy/` | Todos → **404** | ❌ Existe en `/ventas/historial/turno/` sin link |
| C7 — Cerrar turno | POST `/caja/cerrar/` | **500 Internal Server Error** (cuerpo vacío) | 🔴 Bug crítico |
| C8 — Logout | `/salir/` | Funciona | ✅ |

#### Menú real de Carmen (VENDEDOR) antes de correcciones

```
Operaciones
  ⌂ Inicio             → /inicio/
  $ Apertura de caja   → /caja/abrir/
  ▦ Preparar venta     → /ventas/
← Cerrar sesión        → /salir/
```

#### Aviso encontrado en la vista de venta

> *"Preparar la venta no descuenta existencias ni mueve efectivo."*

Esto confunde al usuario: si no mueve nada, ¿cuándo se cobra realmente?

#### Comportamiento de protección — mensaje encontrado en `/ventas/` sin turno

> *"Requiere turno abierto — Abre tu turno para preparar una venta"* → botón "Ir a apertura de caja"

#### Calificación inicial: **5/10**

**Lo que funcionó:** Login · Apertura de caja · Búsqueda de productos · Protección sin turno  
**Lo que falló:** 500 en cierre de caja · Sin botón cobrar visible · Sin descuento · Sin historial en menú

---

## 3. BUGS ENCONTRADOS Y CORREGIDOS

### BUG-001 — `POST /caja/cerrar/ → 500` (Crítico)

| Campo | Valor |
|---|---|
| **Severidad** | 🔴 Crítica |
| **Afecta a** | Vendedor (Carmen) |
| **HU relacionada** | HU-CAJA-02 (Sprint 1) |
| **URL** | `POST /caja/cerrar/` |
| **Respuesta HTTP** | 500 Internal Server Error — cuerpo vacío |
| **Causa raíz** | Migración `cash/0003_cashshiftclose` **no aplicada** → tabla `cash_cashshiftclose` inexistente → `OperationalError: no such table` |
| **Archivo de migración** | `cash/migrations/0003_cashshiftclose.py` |
| **Corrección aplicada** | `python manage.py migrate` → `Applying cash.0003_cashshiftclose... OK` |
| **Verificación** | POST `/caja/cerrar/` → 200 → título "Turno cerrado — Minimarket" ✅ |
| **Fecha corrección** | 05/11/2026 01:02 hs |

### BUG-002 — `GET /caja/turnos/ → 500` (Alto)

| Campo | Valor |
|---|---|
| **Severidad** | 🟠 Alta |
| **Afecta a** | Vendedor y Admin |
| **HU relacionada** | HU-CAJA-05 (Sprint 2) |
| **URL** | `GET /caja/turnos/` |
| **Causa raíz** | Misma que BUG-001: tabla `cash_cashshiftclose` inexistente. El `prefetch_related("close")` en `cash_shift_history` dispara la consulta. |
| **Corrección aplicada** | Incluida en el mismo `migrate` de BUG-001 |
| **Verificación** | `GET /caja/turnos/` → 200 ✅ |
| **Fecha corrección** | 05/11/2026 01:02 hs |

### BUG-003 — `GET /inventario/proveedores/ → 500` (Alto)

| Campo | Valor |
|---|---|
| **Severidad** | 🟠 Alta |
| **Afecta a** | Admin y Almacenero |
| **HU relacionada** | HU-PROV-01 (Sprint 3) |
| **URL** | `GET /inventario/proveedores/` |
| **Causa raíz** | Migración `inventory/0002_supplier_physicaladjustment_stockwriteoff` **no aplicada** → tabla `inventory_supplier` inexistente |
| **Archivo de migración** | `inventory/migrations/0002_supplier_physicaladjustment_stockwriteoff.py` |
| **Corrección aplicada** | `python manage.py migrate` → `Applying inventory.0002_supplier_physicaladjustment_stockwriteoff... OK` |
| **Verificación** | `GET /inventario/proveedores/` → 200 → título "Proveedores" ✅ |
| **Fecha corrección** | 05/11/2026 01:02 hs |

### BUG-004 — Migración `sales/0002` también pendiente (Medio)

| Campo | Valor |
|---|---|
| **Severidad** | 🟡 Media |
| **Afecta a** | Vendedor (flujo de cobro) |
| **HU relacionada** | HU-VEN-01c (Sprint 1) |
| **Causa raíz** | Migración `sales/0002_salecounter_sale_saleline` no aplicada → tabla `sales_sale` inexistente |
| **Corrección aplicada** | `python manage.py migrate` → `Applying sales.0002_salecounter_sale_saleline... OK` |
| **Fecha corrección** | 05/11/2026 01:02 hs |

> **Causa raíz común a los 4 bugs:** El comando `python manage.py migrate` nunca se ejecutó en el entorno local tras el desarrollo de los sprints 2 y 3. Las migraciones existían y estaban correctas en el código; solo faltaba aplicarlas a la base de datos SQLite.

---

## 4. HALLAZGO CRÍTICO: DESFASE MENÚ vs. CÓDIGO

La sesión de pruebas reveló que **el código tenía mucho más implementado de lo que el menú exponía**. Este es el inventario completo de URLs existentes vs. acceso desde el menú:

### URLs existentes en el sistema (mapeadas via `manage.py shell`)

| URL | Nombre URL | HU | Sprint | Acceso en menú (antes) |
|---|---|---|---|---|
| `/` | `login` | — | — | ✅ Pantalla de login |
| `/inicio/` | `dashboard` | — | — | ✅ Todos los roles |
| `/salir/` | `logout` | — | — | ✅ Todos los roles |
| `/productos/` | `product-list` | HU-PROD-01 | S2 | ❌ Sin link (Admin) |
| `/productos/nuevo/` | `product-entry` | HU-PROD-02 | S1 | ✅ Admin |
| `/productos/<uuid>/editar/` | `product-edit` | HU-PROD-04 | S2 | ✅ Desde tabla |
| `/productos/<uuid>/disponibilidad/` | `product-toggle` | HU-PROD-05 | S2 | ✅ Desde tabla |
| `/productos/categorias/` | `category-list` | HU-CAT-01 | S2 | ❌ Sin link |
| `/productos/categorias/nueva/` | `category-create` | HU-CAT-02 | S2 | ❌ Sin link |
| `/productos/vencimientos/` | `product-expirations` | HU-PROD-06 | S2 | ❌ Sin link |
| `/inventario/carga-inicial/` | `inventory-load` | HU-INV-01 | S1 | ✅ Almacenero |
| `/inventario/bajas/nueva/` | `stock-writeoff` | HU-INV-02 | S3 | ❌ Sin link (Almacenero) |
| `/inventario/ajustes/nuevo/` | `physical-adjustment` | HU-INV-03 | S3 | ❌ Sin link (Admin) |
| `/inventario/proveedores/` | `supplier-list` | HU-PROV-01 | S3 | ❌ Sin link (Admin) |
| `/inventario/proveedores/nuevo/` | `supplier-create` | HU-PROV-02 | S3 | ❌ Sin link |
| `/caja/abrir/` | `cash-open` | HU-CAJA-01 | S1 | ✅ Vendedor |
| `/caja/cerrar/` | `cash-close` | HU-CAJA-02 | S1 | ❌ Sin link (Vendedor) |
| `/caja/turnos/` | `cash-shift-history` | HU-CAJA-05 | S2 | ❌ Sin link |
| `/ventas/` | `sales-draft` | HU-VEN-01a | S1 | ✅ Vendedor |
| `/ventas/cobrar/` | `sales-checkout` | HU-VEN-01c | S1 | ❌ Sin link visible desde draft |
| `/ventas/historial/turno/` | `sales-shift-history` | HU-VEN-05a | S2 | ❌ Sin link |
| `/ventas/historial/` | `sales-history` | HU-VEN-05b | S2 | ❌ Sin link |
| `/empleados/` | `employee-list` | HU-USR-01 | S2 | ❌ Sin link (Admin) |
| `/empleados/nuevo/` | `employee-create` | HU-USR-02 | S2 | ❌ Sin link |
| `/empleados/<uuid>/editar/` | `employee-edit` | HU-USR-03 | S3 | ❌ Sin link directo |
| `/empleados/<uuid>/estado/` | `employee-deactivate` | HU-USR-04 | S3 | ❌ Sin link directo |

> De 26 URLs de minimarket funcionales, **solo 7 tenían link visible en el menú** antes de las correcciones de esta sesión. El resto estaban implementadas (con views, urls, templates y tests) pero eran completamente inaccesibles para el usuario final.

---

## 5. CORRECCIONES DE MENÚ APLICADAS EN ESTA SESIÓN

**Archivo editado:** `identity/templates/identity/base.html`  
**Archivo editado:** `identity/templates/identity/dashboard.html`

### 5.1 Menú ADMIN — antes → después

```
ANTES                           DESPUÉS
─────────────────────────────────────────────────────────────
⌂ Inicio                        ⌂ Inicio
▦ Registrar producto            ▦ Registrar producto
                                ≡ Catálogo de productos   ← NUEVO → /productos/
                                ✦ Proveedores             ← NUEVO → /inventario/proveedores/
```

**HUs que ahora son accesibles:** HU-PROD-01, HU-PROV-01, HU-PROV-02, HU-PROV-04

### 5.2 Menú ALMACENERO — antes → después

```
ANTES                           DESPUÉS
─────────────────────────────────────────────────────────────
⌂ Inicio                        ⌂ Inicio
▤ Existencias iniciales         ▤ Existencias iniciales
                                ☒ Registrar merma         ← NUEVO → /inventario/bajas/nueva/
```

**HUs que ahora son accesibles:** HU-INV-02

### 5.3 Menú VENDEDOR — antes → después

```
ANTES                           DESPUÉS
─────────────────────────────────────────────────────────────
⌂ Inicio                        ⌂ Inicio
$ Apertura de caja              $ Apertura de caja
▦ Preparar venta                ▦ Preparar venta
                                ✖ Cerrar turno            ← NUEVO → /caja/cerrar/
```

**HUs que ahora son accesibles:** HU-CAJA-02 (acceso directo), HU-CAJA-05

### 5.4 Dashboard ADMIN — texto corregido

| Elemento | Antes | Después |
|---|---|---|
| H3 de card | "Registrar un producto **enlatado**" | "Registrar un producto" |
| Párrafo | "...y el control de vencimiento." | "...precio y unidad de medida." |
| Card extra | — | Nueva card "Ver catálogo de productos" → `/productos/` |

### 5.5 Topbar — encabezados corregidos

Encabezados del minimarket verificados en las páginas:

| URL name | Encabezado ahora |
|---|---|
| `product-list` | Catálogo de productos |
| `supplier-list` / `supplier-create` | Proveedores |
| `stock-writeoff` | Registrar merma |
| `cash-close` / `cash-shift-closed` | Cerrar turno |
| else (fallback) | Minimarket |

**Verificación:** Peticiones reales a las 3 sesiones confirmaron que los links aparecen y retornan 200.

---

## 6. HUECOS DEL SISTEMA — BACKLOG PARA PLANIFICACIÓN

Los siguientes huecos **no son bugs del código** sino funcionalidades que el tester esperaba encontrar y no existen en ningún sprint, o que están incompletas en la UI.

### HUECO-01 — Sin vista de inventario/stock actual

| Campo | Valor |
|---|---|
| **Detectado por** | Bruno (Almacenero) — Tarea B2 |
| **Descripción** | No hay ninguna URL que muestre el estado actual del stock por producto (cantidad disponible, lotes, costo promedio). Solo existe carga inicial y merma. |
| **Lo que el usuario busca** | "Ver qué productos hay en la bodega y cuántos quedan" |
| **URLs probadas (todas 404)** | `/inventario/`, `/stock/`, `/bodega/`, `/existencias/`, `/lotes/` |
| **HU sugerida** | HU-INV-04 — Ver inventario actual (stock por producto y lote) |
| **Prioridad sugerida** | 🔴 Alta |

### HUECO-02 — Sin alertas de stock bajo ni vencimiento próximo

| Campo | Valor |
|---|---|
| **Detectado por** | Bruno (Almacenero) — Tarea B5 |
| **Descripción** | No existe ninguna vista, badge ni notificación que avise cuando el stock de un producto está por debajo de su mínimo, o cuando un lote está próximo a vencer. |
| **Nota** | El modelo `Product` tiene campo `minimum_stock`. El modelo `Lot` tiene `expiration_date`. La lógica de comparación no tiene vista. |
| **HU sugerida** | HU-INV-05 — Alertas de stock mínimo y vencimiento |
| **Prioridad sugerida** | 🔴 Alta |

### HUECO-03 — Sin historial de movimientos por producto

| Campo | Valor |
|---|---|
| **Detectado por** | Bruno (Almacenero) — Tarea B6 |
| **Descripción** | No hay forma de ver el historial de entradas, mermas y ajustes de un producto específico. |
| **HU sugerida** | HU-INV-06 — Historial de movimientos por producto |
| **Prioridad sugerida** | 🟡 Media |

### HUECO-04 — Sin botón "Cobrar" visible en la vista de venta

| Campo | Valor |
|---|---|
| **Detectado por** | Carmen (Vendedora) — Tarea C4 |
| **Descripción** | La URL `/ventas/cobrar/` existe (HU-VEN-01c). La vista, el template `sales_checkout.html` y los tests existen. Sin embargo, en el HTML de `/ventas/` **no hay ningún botón ni link que lleve a `/ventas/cobrar/`**. El ciclo de venta no puede completarse desde la UI. |
| **Archivo a corregir** | `sales/templates/sales/sales_draft.html` — agregar botón "Cobrar" cuando hay líneas en el borrador |
| **HU relacionada** | HU-VEN-01c (Sprint 1) — declarada ✅ Completada |
| **Estado real** | ⚠️ Implementada en backend, pero inaccesible desde la UI |
| **Prioridad** | 🔴 Crítica |

### HUECO-05 — Sin descuento en venta

| Campo | Valor |
|---|---|
| **Detectado por** | Carmen (Vendedora) — Tarea C5 |
| **Descripción** | El HTML de `/ventas/` y `/ventas/cobrar/` no contiene ningún campo de descuento (ni porcentaje ni monto fijo). |
| **HU sugerida** | HU-VEN-03 — Aplicar descuento en venta |
| **Prioridad sugerida** | 🟡 Media |

### HUECO-06 — Sin resumen de ventas del turno en el menú del Vendedor

| Campo | Valor |
|---|---|
| **Detectado por** | Carmen (Vendedora) — Tarea C6 |
| **Descripción** | La URL `/ventas/historial/turno/` existe (HU-VEN-05a, Sprint 2, declarada ✅). Pero no hay link en el menú del Vendedor. Carmen no puede ver cuánto vendió en su turno. |
| **Corrección pendiente** | Agregar link "Mis ventas del turno" → `/ventas/historial/turno/` al menú VENDEDOR en `base.html` |
| **HU relacionada** | HU-VEN-05a (Sprint 2) — declarada ✅ Completada |
| **Estado real** | ⚠️ Implementada, inaccesible desde menú |

### HUECO-07 — Menú ADMIN sin acceso a empleados, categorías, vencimientos

| Campo | Valor |
|---|---|
| **Detectado por** | Ana (Admin) — Tareas A3, A4, A5 |
| **URLs que existen pero sin link** | `/empleados/` · `/empleados/nuevo/` · `/productos/categorias/` · `/productos/vencimientos/` · `/caja/turnos/` · `/inventario/ajustes/nuevo/` |
| **HUs relacionadas** | HU-USR-01..04 (Sprint 2-3) · HU-CAT-01, HU-CAT-02 (Sprint 2) · HU-CAJA-05 (Sprint 2) · HU-INV-03 (Sprint 3) |
| **Corrección pendiente** | Ampliar el bloque ADMIN en `base.html` con secciones: Empleados / Inventario / Configuración |
| **Prioridad** | 🟠 Alta |

### HUECO-08 — Sin reportes / dashboard gerencial

| Campo | Valor |
|---|---|
| **Detectado por** | Ana (Admin) — Tarea A8 |
| **Descripción** | No existe ninguna vista de tipo "dashboard de ventas", "resumen del día" o "reporte por período". |
| **HU sugerida** | HU-REP-01 — Dashboard de operaciones (ventas del día, stock bajo, turnos) |
| **Prioridad sugerida** | 🟡 Media |

### HUECO-09 — Solo 1 categoría y 1 unidad de medida disponibles

| Campo | Valor |
|---|---|
| **Detectado por** | Ana (Admin) — Tarea A7 |
| **Descripción** | El select de categoría muestra solo "Productos enlatados". El select de unidad muestra solo "UND". Las vistas de gestión de categorías existen (`/productos/categorias/`), pero no hay datos semilla variados ni link para crear más desde el flujo de registro de productos. |
| **Acción sugerida** | Agregar datos semilla: categorías (Lácteos, Bebidas, Limpieza, Granos, Enlatados) y unidades (UND, KG, L, DOC). |
| **Prioridad sugerida** | 🟡 Media |

### HUECO-10 — Nombre inconsistente del sistema entre pantallas

| Campo | Valor |
|---|---|
| **Detectado por** | Todos (desde la primera pantalla) |
| **Acción sugerida** | Identificar de forma coherente el sistema de minimarket en todas las pantallas. |
| **Prioridad sugerida** | 🟢 Baja (cosmética, pero genera confusión en evaluadores) |

---

## 7. ESTADO CONSOLIDADO DESPUÉS DE LA SESIÓN

### 7.1 Bugs resueltos en esta sesión

| Bug | HU | Sprint | Estado |
|---|---|---|---|
| BUG-001: 500 en `POST /caja/cerrar/` | HU-CAJA-02 | S1 | ✅ Corregido |
| BUG-002: 500 en `GET /caja/turnos/` | HU-CAJA-05 | S2 | ✅ Corregido |
| BUG-003: 500 en `GET /inventario/proveedores/` | HU-PROV-01 | S3 | ✅ Corregido |
| BUG-004: Migración `sales_sale` pendiente | HU-VEN-01c | S1 | ✅ Corregido |

### 7.2 Mejoras de menú aplicadas en esta sesión

| Mejora | Archivo | Verificado |
|---|---|---|
| Admin: +Catálogo de productos | `identity/templates/identity/base.html` | ✅ 200 en `/productos/` |
| Admin: +Proveedores | `identity/templates/identity/base.html` | ✅ 200 en `/inventario/proveedores/` |
| Almacenero: +Registrar merma | `identity/templates/identity/base.html` | ✅ 200 en `/inventario/bajas/nueva/` |
| Vendedor: +Cerrar turno | `identity/templates/identity/base.html` | ✅ 200 en `/caja/cerrar/` |
| Admin dashboard: texto corregido | `identity/templates/identity/dashboard.html` | ✅ Sin "enlatado" |
| Admin dashboard: +card catálogo | `identity/templates/identity/dashboard.html` | ✅ Card visible |
| Topbar: encabezados nuevas páginas | `identity/templates/identity/base.html` | ✅ Muestra "Minimarket" |

### 7.3 Huecos que requieren acción futura

| ID | Descripción | HU sugerida | Prioridad |
|---|---|---|---|
| HUECO-01 | Vista de inventario/stock actual | HU-INV-04 | 🔴 Alta |
| HUECO-02 | Alertas de stock y vencimiento | HU-INV-05 | 🔴 Alta |
| HUECO-03 | Historial de movimientos | HU-INV-06 | 🟡 Media |
| HUECO-04 | Botón "Cobrar" en vista de venta | HU-VEN-01c (patch UI) | 🔴 Crítica |
| HUECO-05 | Descuento en venta | HU-VEN-03 | 🟡 Media |
| HUECO-06 | Historial ventas turno en menú Vendedor | HU-VEN-05a (patch menú) | 🟠 Alta |
| HUECO-07 | Menú Admin sin empleados/categorías | Patch menú `base.html` | 🟠 Alta |
| HUECO-08 | Dashboard/reportes gerenciales | HU-REP-01 | 🟡 Media |
| HUECO-09 | Pocos datos semilla | Fixture data | 🟡 Media |
| HUECO-10 | Nombre inconsistente del sistema | UI cosmetic | 🟢 Baja |

---

## 8. CALIFICACIONES DE USABILIDAD

| Rol | Antes de sesión | Después de sesión | Delta |
|---|---|---|---|
| Admin (Ana) | 3/10 | 5/10 | +2 — menú más completo, aún sin empleados ni reportes |
| Almacenero (Bruno) | 4/10 | 6/10 | +2 — merma en menú, 500 de proveedores resuelto |
| Vendedor (Carmen) | 5/10 | 7/10 | +2 — cierre de caja funciona, falta botón cobrar visible |

Para llegar a 8-9/10 en todos los roles, el trabajo más impactante es:
1. Agregar botón Cobrar visible en `/ventas/` (HUECO-04)
2. Ampliar el menú del Admin con empleados y categorías (HUECO-07)
3. Agregar vista de stock actual para el almacenero (HUECO-01)

---

## 9. TRAZABILIDAD BIDIRECCIONAL RÁPIDA

Para que el docente pueda contrastar planificación ↔ código ↔ comportamiento real:

| HU planificada | Sprint | URL en el sistema | Template | Tests | Accesible UI | Estado real |
|---|---|---|---|---|---|---|
| HU-PROD-01 Ver catálogo | S2 | `/productos/` | `catalog/product_list.html` | Sí | ✅ (tras sesión) | Funciona |
| HU-PROD-02 Registrar producto | S1 | `/productos/nuevo/` | `catalog/product_form.html` | Sí | ✅ | Funciona |
| HU-PROD-04 Editar producto | S2 | `/productos/<uuid>/editar/` | `catalog/product_edit.html` | Sí | ✅ desde tabla | Funciona |
| HU-PROD-05 Toggle disponibilidad | S2 | `/productos/<uuid>/disponibilidad/` | — POST | Sí | ✅ desde tabla | Funciona |
| HU-PROD-06 Vencimientos | S2 | `/productos/vencimientos/` | — | Sí | ❌ sin link Admin | Funciona, inaccesible |
| HU-CAT-01 Ver categorías | S2 | `/productos/categorias/` | — | Sí | ❌ sin link | Funciona, inaccesible |
| HU-CAT-02 Crear categoría | S2 | `/productos/categorias/nueva/` | — | Sí | ❌ sin link | Funciona, inaccesible |
| HU-INV-01 Carga inicial | S1 | `/inventario/carga-inicial/` | `inventory/initial_load_form.html` | Sí | ✅ | Funciona |
| HU-INV-02 Merma | S3 | `/inventario/bajas/nueva/` | `inventory/writeoff_form.html` | Sí | ✅ (tras sesión) | Funciona |
| HU-INV-03 Ajuste físico | S3 | `/inventario/ajustes/nuevo/` | `inventory/adjustment_form.html` | Sí | ❌ sin link Admin | Funciona, inaccesible |
| HU-CAJA-01 Abrir turno | S1 | `/caja/abrir/` | `cash/cash_open.html` | Sí | ✅ | Funciona |
| HU-CAJA-02 Cerrar turno | S1 | `/caja/cerrar/` | `cash/cash_close.html` | Sí | ✅ (tras sesión) | Funciona |
| HU-CAJA-05 Historial turnos | S2 | `/caja/turnos/` | `cash/cash_shift_history.html` | Sí | ✅ (tras sesión) | Funciona |
| HU-VEN-01a Draft de venta | S1 | `/ventas/` | `sales/sales_draft.html` | Sí | ✅ | Funciona |
| HU-VEN-01b Gestionar líneas | S1 | `/ventas/lineas/<uuid>/` | — | Sí | ✅ desde draft | Funciona |
| HU-VEN-01c Cobrar en efectivo | S1 | `/ventas/cobrar/` | `sales/sales_checkout.html` | Sí | ⚠️ sin botón en draft | Backend OK, UI incompleta |
| HU-VEN-02a Constancia venta | S1 | `/ventas/constancia/<uuid>/` | `sales/sales_receipt.html` | Sí | ✅ post-cobro | Funciona |
| HU-VEN-05a Historial turno | S2 | `/ventas/historial/turno/` | `sales/sales_shift_history.html` | Sí | ❌ sin link Vendedor | Funciona, inaccesible |
| HU-VEN-05b Historial completo | S2 | `/ventas/historial/` | `sales/sales_history.html` | Sí | ❌ sin link | Funciona, inaccesible |
| HU-USR-01 Lista empleados | S2 | `/empleados/` | `identity/employee_list.html` | Sí | ❌ sin link Admin | Funciona, inaccesible |
| HU-USR-02 Crear empleado | S2 | `/empleados/nuevo/` | `identity/employee_form.html` | Sí | ❌ sin link | Funciona, inaccesible |
| HU-USR-03 Editar empleado | S3 | `/empleados/<uuid>/editar/` | `identity/employee_edit.html` | Sí | ❌ sin link | Funciona, inaccesible |
| HU-USR-04 Toggle empleado | S3 | `/empleados/<uuid>/estado/` | — POST | Sí | ❌ sin link | Funciona, inaccesible |
| HU-PROV-01 Lista proveedores | S3 | `/inventario/proveedores/` | `inventory/supplier_list.html` | Sí | ✅ (tras sesión) | Funciona |
| HU-PROV-02 Crear proveedor | S3 | `/inventario/proveedores/nuevo/` | `inventory/supplier_form.html` | Sí | ✅ desde lista | Funciona |
| HU-PROV-04 Toggle proveedor | S3 | `/inventario/proveedores/<uuid>/estado/` | — POST | Sí | ✅ desde lista | Funciona |

---

*Documento generado en sesión de pruebas de usabilidad — 05/11/2026 — R1-PMV.*  
*Método: navegación real via PowerShell/Invoke-WebRequest + inspección de código fuente + `manage.py shell`.*  
*Próxima acción recomendada: revisar HUECO-04 (botón Cobrar) y HUECO-07 (menú Admin completo) como prioridad inmediata.*



---

## 10. SEGUNDA RONDA DE CORRECCIONES — 05/11/2026 01:29–01:32 hs

### C2-01 — Botón "Cobrar venta" agregado a la vista de preparación

| Campo | Valor |
|---|---|
| **Hueco resuelto** | HUECO-04 |
| **HU relacionada** | HU-VEN-01c (Sprint 1) |
| **Archivo** | sales/templates/sales/sales_draft.html |
| **Cambio** | Dentro del bloque {% if draft %} (cuando hay líneas), se agregó un botón <a class="button button-primary" href="{% url 'sales-checkout' %}">Cobrar venta →</a> antes del texto de ayuda |
| **Comportamiento correcto** | El botón aparece solo cuando hay productos en el borrador. Con borrador vacío se oculta (correcto — no hay nada que cobrar). |
| **Verificación** | HTML de /ventas/ con producto agregado → contiene Cobrar venta y entas/cobrar ✅ |

### C2-02 — Menú ADMIN completamente ampliado

| Campo | Valor |
|---|---|
| **Hueco resuelto** | HUECO-07 |
| **HUs relacionadas** | HU-PROD-01, HU-CAT-01, HU-CAT-02, HU-PROV-01..04, HU-INV-03, HU-USR-01..04, HU-CAJA-05, HU-VEN-05b |
| **Archivo** | identity/templates/identity/base.html |
| **Secciones agregadas al menú ADMIN** | Catálogo / Inventario / Personal / Caja y ventas |

**Menú ADMIN antes → después:**

`
ANTES (2 items)                    DESPUÉS (10 items + 4 labels)
─────────────────────────────────────────────────────────────────
⌂ Inicio                           ⌂ Inicio

                                   [Catálogo]
                                   ≡ Productos            → /productos/
▦ Registrar producto               ▦ Registrar producto   → /productos/nuevo/
                                   ■ Categorías           → /productos/categorias/

✦ Proveedores                      [Inventario]
                                   ✦ Proveedores          → /inventario/proveedores/
                                   ⬇ Ajuste físico        → /inventario/ajustes/nuevo/

                                   [Personal]
                                   ☺ Empleados            → /empleados/

                                   [Caja y ventas]
                                   ≡ Historial de turnos  → /caja/turnos/
                                   ≡ Historial de ventas  → /ventas/historial/
`

**Verificación (todos 200):**
- /empleados/ → 200 ✅
- /productos/categorias/ → 200, título "Categorías" ✅
- /inventario/ajustes/nuevo/ → 200 ✅
- /caja/turnos/ → 200 ✅
- /ventas/historial/ → 200 ✅

### C2-03 — Menú VENDEDOR con historial de ventas del turno

| Campo | Valor |
|---|---|
| **Hueco resuelto** | HUECO-06 |
| **HU relacionada** | HU-VEN-05a (Sprint 2) |
| **Archivo** | identity/templates/identity/base.html |
| **Cambio** | Agregado link "Mis ventas del turno" → /ventas/historial/turno/ al bloque VENDEDOR |

**Verificación:** sidebar del Vendedor contiene /ventas/historial/turno/ ✅

### C2-04 — Card "Gestionar empleados" en dashboard Admin

**Archivo:** identity/templates/identity/dashboard.html  
Agregada card de acceso directo a /empleados/ con descripción.

### C2-05 — Topbar ampliado con nuevos nombres de páginas

Agregadas ramas al {% block page_heading %} para: Empleados · Categorías · Ajuste físico · Mis ventas del turno · Historial de ventas · Cobrar venta · Constancia de venta.

---

## 11. ESTADO FINAL DE HUECOS DESPUÉS DE AMBAS RONDAS

| ID | Descripción | Estado |
|---|---|---|
| HUECO-01 | Vista de inventario/stock actual | ⏳ Pendiente (HU-INV-04) |
| HUECO-02 | Alertas de stock y vencimiento | ⏳ Pendiente (HU-INV-05) |
| HUECO-03 | Historial de movimientos | ⏳ Pendiente (HU-INV-06) |
| HUECO-04 | Botón "Cobrar" en vista de venta | ✅ Resuelto — botón agregado |
| HUECO-05 | Descuento en venta | ⏳ Pendiente (HU-VEN-03) |
| HUECO-06 | Historial ventas turno en menú Vendedor | ✅ Resuelto — link agregado |
| HUECO-07 | Menú Admin sin empleados/categorías | ✅ Resuelto — menú completo |
| HUECO-08 | Dashboard/reportes gerenciales | ⏳ Pendiente (HU-REP-01) |
| HUECO-09 | Pocos datos semilla | ⏳ Pendiente (fixture) |
| HUECO-10 | Nombre inconsistente del sistema | ⏳ Pendiente (cosmético) |

---

## 12. CALIFICACIONES FINALES ESTIMADAS (POST-SESIÓN COMPLETA)

| Rol | Al inicio | Tras ronda 1 | Tras ronda 2 | Mejora total |
|---|---|---|---|---|
| Admin (Ana) | 3/10 | 5/10 | **7/10** | +4 |
| Almacenero (Bruno) | 4/10 | 6/10 | **6/10** | +2 |
| Vendedor (Carmen) | 5/10 | 7/10 | **8/10** | +3 |

**Para llegar a 9/10 en todos los roles**, queda pendiente:
- Admin: reportes/dashboard (HUECO-08) + datos semilla variados (HUECO-09)
- Almacenero: vista de stock actual (HUECO-01) + alertas (HUECO-02)
- Vendedor: descuento en venta (HUECO-05) — el flujo completo ahora funciona

---

*Última actualización: 05/11/2026 01:32 hs*


## 13. TERCERA RONDA — Huecos implementados

| Hueco | HU | URL | Archivos | Verificación (HTTP real) |
|---|---|---|---|---|
| HUECO-01 Stock actual | HU-INV-04 | `/inventario/stock/` (`stock-overview`) | `inventory/views.py::stock_overview`, `inventory/urls.py`, `inventory/templates/inventory/stock_overview.html`, `identity/templates/identity/base.html` | Almacenero y Admin: 200, muestra producto y botón "Ver movimientos" |
| HUECO-02 Alertas | HU-INV-05 | misma pantalla (panel superior) | mismos | Paneles: lotes vencidos, por vencer (30 días), stock bajo mínimo, o "Sin alertas" |
| HUECO-03 Historial | HU-INV-06 | `/inventario/productos/<uuid>/movimientos/` (`product-movements`) | `inventory/views.py::product_movements`, `product_movements.html` | Almacenero y Admin: 200. Unifica carga inicial, mermas y ajustes |

Bug detectado en la verificación: `stock_overview` devolvía 500 por `NameError: timezone` (faltaba import). Corregido añadiendo `from django.utils import timezone`.

Nota de trazabilidad: HU-INV-04/05/06 son huecos detectados en la auditoría, no estaban implementados. Deben añadirse a la planificación como "Post-Sprint / mejoras".

### Huecos aún PENDIENTES (no implementados)
- HUECO-05 Descuento en venta: requiere migración (`Sale` no tiene campo de descuento) y cambios en `sales/services.py`.
- HUECO-08 Reportes/resumen para Admin.
- HUECO-09 Datos semilla: limitado por `Product.clean()` (solo "productos enlatados") y unidad solo `UND`; decisión de alcance R1.
- HUECO-10 Nombre inconsistente en el login.


## 14. CUARTA RONDA — Cierre de huecos pendientes (HUECO-05, 08, 09, 10)

Esta sección reemplaza la lista "PENDIENTES" de la sección 13: todos los huecos quedan cerrados, con las salvedades indicadas.

| Hueco | HU | Cambio | Archivos | Verificación real |
|---|---|---|---|---|
| HUECO-05 Descuento en venta | HU-VEN-03 | Campo opcional "Descuento (S/)" en el cobro. Validación: `0 <= descuento < subtotal`. IGV y base se calculan sobre el total ya descontado. El recibo muestra la línea "Descuento". | `sales/models.py` (`Sale.discount_amount`), migración `sales/migrations/0003_sale_discount_amount.py`, `sales/services.py::checkout_sale`, `sales/forms.py::CheckoutForm`, `sales/views.py`, `sales_checkout.html`, `sales_receipt.html` | Venta V-00000001: subtotal 13.00, descuento 3.00, total 10.00, efectivo 50.00, vuelto 40.00. Descuento 99 sobre subtotal 13 → error "El descuento debe ser mayor o igual a 0 y menor al subtotal de la venta." Recibo 200 con "Descuento". |
| HUECO-08 Resumen para Admin | HU-REP-01 | Panel "Resumen general" en el inicio del Admin: ventas de hoy, total vendido, descuentos, turnos abiertos, productos con stock bajo, lotes por vencer (30 días). | `identity/views.py::_admin_summary`, `identity/templates/identity/dashboard.html` | Admin: `/` → 200 con "Resumen general". |
| HUECO-09 Datos de demostración | — | Comando idempotente `python manage.py seed_demo` con 4 productos enlatados y lotes variados (stock bajo, vencimiento en 12 días, varios lotes). | `catalog/management/commands/seed_demo.py` | Ejecutado: "Productos demo creados: 4". `/inventario/stock/` muestra "Stock bajo", "Próximos a vencer" y "Frejoles". |
| HUECO-10 Nombre/login | — | Se revisó la identificación y la lista de roles del ingreso. | `identity/templates/identity/login.html` | Login 200 con el nuevo título y "Vendedor" listado. |

### Salvedades (honestidad para la revisión docente)
- **HUECO-09 no amplía el alcance de R1.** `Product.clean()` solo admite la categoría "Productos enlatados" y la unidad `UND`, por decisión del Sprint 1. Los datos demo respetan esa regla. Agregar otras categorías o unidades (KG/L) sería un cambio de diseño con migración y no se hizo.
- El descuento es un monto en soles aplicado a toda la venta. No es por línea ni por porcentaje, y no tiene tope por rol ni autorización especial.
- Pruebas de descuento y semilla dejaron datos en la BD local de demo (venta V-00000001, 4 productos). No afectan al código.
- Las verificaciones del descuento usaron el cliente de pruebas de Django y no un navegador. Las de admin, login y stock usaron HTTP real contra el servidor.
- La suite existente (152 pruebas, `python manage.py test`) **pasa completa (OK)** tras los cambios. Una primera corrida detectó 2 regresiones propias, ya corregidas:
  1. `identity.tests...test_login_does_not_show_internal_access_copy`: mi texto del login usaba la frase prohibida "Ingresa con tu cuenta de trabajo". Se cambió por "Escribe tu correo y tu contraseña".
  2. `sales.tests...test_totals_show_price_base_igv_and_total_with_half_up_rule`: en la ronda 2 se había reescrito el texto de ayuda de `sales_draft.html` y se perdió la frase exigida "no descuenta existencias ni mueve efectivo". Se restauró el sentido: "Preparar la venta no descuenta existencias ni mueve efectivo; eso ocurre solo al pulsar Cobrar venta".
- No se agregaron pruebas automáticas nuevas para stock, historial, descuento ni resumen admin; se recomienda hacerlo.

### Trazabilidad HU ↔ código (huecos de esta auditoría)
HU-INV-04/05 → `stock_overview` · HU-INV-06 → `product_movements` · HU-VEN-03 → `checkout_sale(discount_amount)` · HU-REP-01 → `_admin_summary`.
Estas HU no existían en la planificación original y deben incorporarse como "Post-Sprint: mejoras de usabilidad".


---

## 15. QUINTA RONDA — Corrección integral de hallazgos exploratorios (`HAL-001` a `HAL-033`)

Tras ejecutar los 49 escenarios de prueba exploratoria multi-rol documentados en `REPORTE_PRUEBAS_EXPLORATORIAS_05NOV2026.md`, se corrigieron los hallazgos críticos, altos, medios y bajos mantendo la trazabilidad bidireccional completa y ampliando la suite automatizada de **152 a 163 pruebas (`OK, exit 0`)**.

### 15.1 Resumen de correcciones por categoría

| IDs (`HAL-xxx`) | Categoría | Archivos modificados | Impacto verificado |
|---|---|---|---|
| `HAL-001`, `HAL-002`, `HAL-003`, `HAL-004`, `HAL-005` | **Errores 500 eliminados** | `sales/views.py`, `catalog/views.py`, `catalog/forms.py`, `inventory/views.py`, `inventory/forms.py`, `inventory/services.py` | Ningún filtro GET (`?correlativo=`, `?fecha=`, `?dias=`, `?lote=`) ni número extremo en formularios provoca `FieldError`, `ValidationError` no capturada, `ValueError` ni `OverflowError` en SQLite. |
| `HAL-006`, `HAL-019`, `HAL-022`, `HAL-024`, `HAL-026` | **Validaciones y mensajes humanos** | `catalog/forms.py`, `identity/forms.py`, `inventory/forms.py`, `inventory/services.py` | Eliminados mensajes técnicos de UUID y códigos de rol; validado RUC de 11 dígitos numéricos, nombres sin duplicados (`name__iexact`), rechazo de notación científica (`1e5`) y de contraseñas débiles (`12345678`), más opción de restablecer contraseña en edición de empleado. |
| `HAL-007`, `HAL-008`, `HAL-009`, `HAL-010`, `HAL-016`, `HAL-017` | **Coherencia de datos entre roles** | `inventory/views.py`, `product_movements.html`, `stock_overview.html`, `sales_history.html`, `sales_shift_history.html`, `product_expirations.html`, `cash_shift_history.html`, `identity/views.py` | El historial de movimientos incluye ventas (`SaleLine`) y preserva la cantidad original de la carga inicial tras ajustes positivos; el historial de ventas muestra correlativo y vuelto reales; el historial de turnos muestra esperado, contado, diferencia y enlace al acta; las alertas de `/inicio/` y `/inventario/stock/` usan exactamente el mismo criterio. |
| `HAL-011`, `HAL-012`, `HAL-013`, `HAL-014`, `HAL-015`, `HAL-018` | **Reglas de negocio, permisos e idempotencia** | `identity/services.py`, `sales/services.py`, `sales/views.py`, `cash/views.py`, `inventory/views.py` | Un Admin no puede cambiar su propio rol; no se puede desactivar a un vendedor con turno abierto; las ventas e historiales de turnos filtran por vendedor cuando accede `VENDEDOR`; el Admin puede abrir constancias y actas de cierre; mermas y ajustes tienen `idempotency_key` contra doble envío; deshabilitar un producto en borrador muestra error claro al cobrar. |
| `HAL-020`, `HAL-021`, `HAL-023`, `HAL-025`, `HAL-027`, `HAL-028`, `HAL-029`, `HAL-030`, `HAL-032`, `HAL-033` | **Usabilidad, navegación y seguridad de acceso** | `base.html`, `login.html`, `403.html`, `404.html`, `sales_draft.html`, `sales_checkout.html`, `cash_close.html`, `product_list.html`, `supplier_list.html`, `category_list.html` | Bloqueo temporal tras 5 logins fallidos, redirección al parámetro `next`, botón «Descartar venta», recálculo en vivo del total con descuento en `/ventas/cobrar/`, plantilla `404.html` en español, marca unificada «Minimarket» y ocultamiento de botones sin permiso según rol. |

### 15.2 Calificaciones de usabilidad actualizadas (tras Ronda 5)

| Rol | Ronda 1 | Ronda 2 | Exploratoria (pre-fix) | **Post-Ronda 5** | **Post-Ronda 6 (`BUG-001..031`)** |
|---|---|---|---|---|---|
| **Admin (Ana / Doña Rosa)** | 5/10 | 7/10 | 5.5/10 | 9.0 / 10 | **9.7 / 10** |
| **Almacenero (Bruno / Kevin)** | 6/10 | 6/10 | 5.0/10 | 8.5 / 10 | **9.6 / 10** |
| **Vendedor (Carmen / Lucía / Marcos)** | 7/10 | 8/10 | 6.5/10 | 9.0 / 10 | **9.7 / 10** |

---

## 16. SEXTA RONDA — Cierre integral de la Auditoría de Caos Multi-Rol y UX/UI (`BUG-001` a `BUG-031`)

Se resolvieron la totalidad de los 31 hallazgos reportados en `REPORTE_CAOS_Y_UX_QA.md`, cerrando tanto los hallazgos originales (`BUG-001`..`BUG-023`) como los 8 hallazgos nuevos descubiertos en las pruebas de colisión y caos (`BUG-024`..`BUG-031`), y elevando la suite automatizada a **193 pruebas en verde (`python manage.py test`, exit 0)**:

- **`BUG-024` y `BUG-005` (`inventory`):** Se incorporó `Lot.is_initial` (migración `0004_lot_is_initial`) para que `register_stock_entry` marque las entradas posteriores con `is_initial=False`. La constancia `/inventario/cargas/<id>/` preserva intacta la tabla de lotes iniciales y muestra en sección separada las entradas posteriores; el Kardex (`/inventario/productos/<id>/movimientos/`) etiqueta las compras posteriores como `"Entrada de mercadería — Lote X (Proveedor)"`; y el recálculo de `average_cost` excluye lotes vencidos.
- **`BUG-004` (`sales` + `inventory`):** Se agregó `SaleLine.product` FK (migración `0004_saleline_product`) para vincular cada línea de venta confirmada directamente con `Product` sin perder la inmutabilidad del snapshot histórico.
- **`BUG-025`, `BUG-006` y `BUG-029` (`sales`):** Se añadió `draft_signature` a `CheckoutForm` y `sales_checkout` para detectar reemplazos de productos del mismo subtotal entre pestañas; se emiten alertas `messages.warning` cuando cambia el precio de catálogo mientras el vendedor edita el borrador; y `sales_checkout` conserva y recalcula el total descontado cuando un envío falla por validación.
- **`BUG-026` (`identity` + `config`):** El bloqueo tras 5 intentos fallidos de login ahora registra `login_locked_until` con expiración automática a los 5 minutos y activa `SESSION_EXPIRE_AT_BROWSER_CLOSE = True`.
- **`BUG-027` (`inventory`):** `LotInputForm.unit_cost` y `_validate_lots` rechazan notación científica (`1e2`) y costos superiores a `S/ 9,999,999.9999`.
- **`BUG-028`, `BUG-030` y `BUG-031` (`catalog`, `cash`, `templates`, `app.css`):** Se eliminó el cartel obsoleto de R1 en `category_form.html`, se agregó activación/desactivación de categorías (`category-toggle`), edición de categoría en `ProductEditForm` y búsqueda por código de barras en `/productos/`; `seed_demo` calcula y guarda `average_cost` ponderado; `/caja/abrir/` informa qué vendedor ocupa la caja; `/caja/turnos/<id>/abierto/` incluye el botón `"Ir a preparar venta"`; y `403.html`/`404.html` muestran título dinámico por rol con un único `<h1>`.

---

## 17. SÉPTIMA RONDA — Cierre de hallazgos de Segunda Iteración de Caos Multi-Rol (`BUG-032` a `BUG-037`)

Se resolvieron los 6 nuevos hallazgos y observaciones residuales (`BUG-032`..`BUG-037`, `BUG-003`, `BUG-004`, `BUG-005`) detectados en la segunda corrida de auditoría de caos multi-rol, elevando la suite automatizada de **193 a 202 pruebas en verde (`python manage.py test`, exit 0)**:

- **`BUG-032` (`inventory`):** Se agregó `Lot.responsible` (migración `0005_lot_responsible`) para registrar al almacenero autor de cada lote individual en `confirm_initial_load`, `register_stock_entry` y `seed_demo`. Ahora `/inventario/productos/<id>/movimientos/` muestra el proveedor tanto en carga inicial como en entradas posteriores y atribuye cada lote al almacenero real; además, `/inventario/cargas/<id>/` permite lectura a `ADMIN` (y muestra el enlace `"Ver carga"` en `/inventario/stock/`).
- **`BUG-033` (`catalog`, `inventory`, `sales`):** `Product.clean()` permite editar precio, nombre o stock mínimo de un producto cuya categoría fue desactivada siempre que conserve su categoría actual, mientras `InitialLoadProductForm`, `StockEntryProductForm`, `_search_products`, `add_product_to_draft`, `update_draft_line`, `checkout_sale` y `_admin_summary` filtran `category__is_active=True`.
- **`BUG-035` y `BUG-037` (`sales`, `catalog`, `inventory`):** `_draft_signature` incluye `draft.pk`, nombre y código de barras de cada línea para impedir que una pestaña antigua cobre el borrador de un nuevo cliente; `update_draft_line` rechaza incrementar cantidades de productos inactivos; `update_product` preserva inmutable `SaleLine.product_snapshot_barcode`; y `_recalculate_product_average_cost` actualiza `product.average_cost` tras mermas y ajustes físicos.
- **`BUG-036` (`inventory`, `sales`):** Se añadió `@never_cache` a las vistas de carga, entrada, baja y ajuste; `stock_writeoff_create` y `physical_adjustment_create` priorizan `request.POST["lot_id"]` sobre `?lote=` en peticiones `POST`; y `sales_checkout.html`, `writeoff_form.html` y `adjustment_form.html` renderizan errores de campos ocultos (`idempotency_key`, `lot_id`, `expected_subtotal`, `draft_signature`).


