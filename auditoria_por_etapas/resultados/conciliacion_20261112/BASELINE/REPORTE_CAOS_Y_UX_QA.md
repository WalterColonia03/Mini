# Reporte de Auditoría QA Exploratoria, Caos Multi-Rol y UX/UI — Sistema R1-PMV

> Documento histórico filtrado al alcance del minimarket; los totales originales incluyen casos retirados y no deben interpretarse como métricas actuales.

- **Fecha de ejecución:** 5 de noviembre de 2026
- **Sistema bajo prueba:** `R1-PMV` (Gestión de Minimarket)
- **Entorno:** Django 5.2 / SQLite (`APP_ENV=local`, `LANGUAGE_CODE=es-pe`, `TIME_ZONE=America/Lima`, servidor en `http://127.0.0.1:8000/`)
- **Metodología:** Pruebas exploratorias simultáneas multi-sesión (`Invoke-WebRequest` + `django.test.Client` e inspección de DOM/HTML/CSS renderizado), Monkey & Chaos Testing de colisiones en vivo entre 7 sesiones concurrentes, abandono de flujos a mitad de camino, caza de promesas falsas frente a [`CONTROL_SPRINTS.md`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/CONTROL_SPRINTS.md) y [`AUDITORIA_USABILIDAD_05NOV2026.md`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/AUDITORIA_USABILIDAD_05NOV2026.md), y auditoría contable cruzada de Kardex y Caja.
- **Regla de oro aplicada:** **Cero modificaciones al código fuente durante la auditoría.** Base de datos `r1_pmv.sqlite3` respaldada antes de iniciar y restaurada íntegramente al finalizar, eliminando todo script temporal.

---

## 1. Resumen Ejecutivo

Se ejecutaron **148 escenarios de prueba** encarnando simultáneamente a trabajadores novatos en su primer día laboral:
- **Doña Rosa (`ADMIN` — `admin.demo@pmv.invalid`):** Dueña impaciente, edita precios, categorías y roles en caliente, desactiva registros repetidamente y exige que cada sol y cada lata cuadren.
- **Kevin (`ALMACENERO` 1 — `almacen.demo@pmv.invalid`) y Pedro (`ALMACENERO` 2 — `pedro.qa@pmv.invalid`):** Jóvenes en su primer empleo, acostumbrados a anotar en cuaderno; desconocen términos como *"FEFO"*, *"delta"*, *"stock vendible"* o *"idempotencia"* y se confunden cuando llega mercadería nueva o cuando un segundo almacenero recibe compras en otro turno.
- **Lucía (`VENDEDOR` 1 — `vendedor.demo@pmv.invalid`):** Cajera con fila de clientes apurados; abre múltiples pestañas, deja borradores a medias, se equivoca al digitar montos y aprieta dos veces el botón de cobrar.
- **Marcos (`VENDEDOR` 2 — `marcos.qa@pmv.invalid`):** Cajero del turno tarde creado en vivo por Doña Rosa; intenta abrir caja o vender mientras Lucía tiene el turno abierto, o manipular líneas ajenas.

### 1.1 Métricas Globales de la Auditoría

| Categoría de Prueba | Escenarios Ejecutados | Pasaron sin Observaciones | Fallaron (Bugs Activos / Históricos / UX / Promesas Falsas) |
| :--- | :---: | :---: | :---: |
| **Pilar A — AI Slop, Esquizofrenia CSS, Formato y Jerga** | 32 | 9 | **23** (15 plantillas con estructura Bootstrap vs. `app.css`) |
| **Pilar B — Promesas Falsas vs. Realidad y Planificación** | 25 | 12 | **13** |
| **Pilar C — Procesos Abandonados y Caminos sin Salida** | 23 | 13 | **10** |
| **Pilar D — Caos Multi-Rol, Inputs Destructivos y URLs** | 48 | 29 | **19** |
| **Sección 3 — Verificación Cruzada Contable (Kardex y Caja)** | 20 | 11 | **9** |
| **TOTAL** | **148** | **74 (50.0 %)** | **74 (50.0 %)** |

### 1.2 Distribución de Hallazgos Técnicos y de Negocio por Severidad (`BUG-001` a `BUG-037`)

| Severidad | Cantidad Total | Hallazgos Activos en Vivo (Sin Parchear) | Hallazgos Históricos Verificados (Rondas Previas) | Impacto Principal en el Negocio |
| :--- | :---: | :--- | :--- | :--- |
| **CRÍTICA** | **6** | **`BUG-032`** *(+ residuo de inmutabilidad en `BUG-004` y bloqueo 403 Admin en `/caja/cerrar/` de `BUG-001`)* | `BUG-001`, `BUG-002`, `BUG-003`, `BUG-004`, `BUG-024` | Falsificación del responsable en el Kardex y en la constancia al registrar Entradas Posteriores (`/inventario/entrada/`) por un segundo almacenero (`Lot` carece de FK `responsible`), omisión del proveedor en lotes iniciales del Kardex y bloqueo `HTTP 403` al Administrador en `/inventario/cargas/<id>/` (`BUG-032`); mutación retroactiva de `product_snapshot_barcode` en recibos históricos emitidos (`BUG-004`). |
| **ALTA** | **12** | **`BUG-033`**, **`BUG-035`** | `BUG-005`..`BUG-010`, `BUG-025`, `BUG-026`, `BUG-027` | Desactivar una Categoría bloquea la edición de sus productos existentes en `/productos/<id>/editar/`, engaña al almacenero mostrándolos en el select de `/inventario/entrada/` para rechazarlos al enviar, pero sigue permitiendo su venta normal en `/ventas/` (`BUG-033`); `_draft_signature` no incluye `draft.pk`, permitiendo que una pestaña vieja del Cliente 1 cobre automáticamente el nuevo borrador del Cliente 2 si lleva los mismos productos (`BUG-035`). |
| **MEDIA** | **12** | **`BUG-036`**, **`BUG-037`** | `BUG-011`..`BUG-017`, `BUG-028`, `BUG-029`, `BUG-030` | Fallo silencioso (`HTTP 200` sin mensaje de error en pantalla) cuando fallan campos ocultos (`idempotency_key`, `lot_id`) y discrepancia donde `?lote=<id1>` en la URL ignora `lot_id=<id2>` del POST en Bajas/Ajustes (`BUG-036`); `update_draft_line` permite aumentar la cantidad de un producto deshabilitado en el borrador y `checkout_sale` no advierte si cambió el nombre del producto ni recalcula `average_cost` tras mermas o ajustes (`BUG-037`). |
| **BAJA / UX-SLOP** | **7** | Observaciones visuales y de copy activas en `BUG-018`, `BUG-021`, `BUG-022` | `BUG-018`..`BUG-023`, `BUG-031` | Convivencia de 15 plantillas con clases Bootstrap 5 sin contenedor `.panel` frente a las plantillas nativas de `app.css`; textos *"Registrar producto enlatado"* hardcodeados pese a soportar múltiples categorías; mezcla de coma decimal (`S/ 15,00`) en HTML y punto decimal (`S/ 15.00`) en mensajes de validación. |

---

## 2. Catálogo de Hallazgos Técnicos y de Negocio (`BUG-001` a `BUG-037`)

### 2.1 Nuevos Hallazgos Activos Detectados en la Auditoría en Vivo (`BUG-032` a `BUG-037`)

---

### `BUG-032` [CRÍTICA — ACTIVO] — Falsificación del responsable en Entradas Posteriores (`/inventario/entrada/`), omisión del proveedor de Carga Inicial en el Kardex y bloqueo `HTTP 403` a Doña Rosa (`ADMIN`) en `/inventario/cargas/<id>/`
- **Rol / Persona:** Kevin (`ALMACENERO` 1) + Pedro (`ALMACENERO` 2) + Doña Rosa (`ADMIN`).
- **Módulo / Archivos afectados:** [`inventory/models.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/inventory/models.py#L37-L64) (`Lot`), [`inventory/services.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/inventory/services.py#L314-L329) (`register_stock_entry`), [`inventory/views.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/inventory/views.py#L97-L120) (`initial_load_created`) y [`inventory/views.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/inventory/views.py#L388-L408) (`product_movements`).
- **Pasos exactos para reproducir:**
  1. **Kevin (`ALMACENERO` 1)** registra la Carga Inicial de `Esparragos Gourmet QA 300g` en `POST /inventario/carga-inicial/` seleccionando `supplier = Agroindustrias del Sur SAC` y el lote `ESP-L1` (`20` und. a `S/ 8.0000`).
  2. En el turno noche, **Pedro (`ALMACENERO` 2)** inicia sesión y registra una compra posterior en `POST /inventario/entrada/` para `Esparragos Gourmet QA 300g` con el lote `ESP-L2` (`10` und. a `S/ 10.0000`, proveedor `Agroindustrias del Sur SAC`).
  3. **Doña Rosa (`ADMIN`)** abre el Kardex en `GET /inventario/productos/<product_id>/movimientos/` para auditar quién recibió cada lote y de qué proveedor, e intenta abrir la constancia de carga en `GET /inventario/cargas/<load_id>/`.
- **Expectativa de un usuario novato:**
  - Que el Kardex muestre que `ESP-L2` fue ingresado por **`Pedro Almacen Noche`**, que muestre el proveedor `Agroindustrias del Sur SAC` también en el lote inicial `ESP-L1`, y que la dueña del minimarket (`ADMIN`) pueda abrir la constancia `/inventario/cargas/<load_id>/` sin recibir un error de permisos.
- **Resultado real obtenido (Evidencia HTTP/HTML/BD):**
  1. **Atribución falsa de responsabilidad en el Kardex:** Como el modelo `Lot` no tiene un campo `responsible` y `register_stock_entry` asocia todos los lotes posteriores al `InitialInventoryLoad` original (`existing_load`), `product_movements` ([`inventory/views.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/inventory/views.py#L391-L395)) toma siempre `lot.initial_load.responsible.display_name`. El HTML renderizado en `/inventario/productos/<id>/movimientos/` imprime:
     ```html
     <td>▲ Entrada</td>
     <td>Entrada de mercadería — Lote ESP-L2 (Agroindustrias del Sur SAC)</td>
     <td><strong>+10</strong></td>
     <td>Almacenero Demo</td>
     ```
     ¡Le atribuye a **Kevin (`Almacenero Demo`)** todas las entradas posteriores que registre **Pedro** o cualquier otro almacenero en el futuro!
  2. **Omisión del proveedor en lotes de Carga Inicial dentro del Kardex:** En [`inventory/views.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/inventory/views.py#L396-L400), el código hace:
     ```python
     if lot.is_initial:
         desc = f"Carga inicial — Lote {lot.number}"
     else:
         supplier_suffix = f" ({lot.supplier.name})" if lot.supplier else ""
         desc = f"Entrada de mercadería — Lote {lot.number}{supplier_suffix}"
     ```
     Aunque `ESP-L1` fue registrado con `supplier = Agroindustrias del Sur SAC`, el Kardex imprime solo `<td>Carga inicial — Lote ESP-L1</td>` omitiendo el proveedor.
  3. **Bloqueo `HTTP 403` para el Administrador en `/inventario/cargas/<load_id>/`:** `initial_load_created` tiene el decorador `@roles_required(Role.Code.WAREHOUSE)` (excluyendo a `Role.Code.ADMIN`). Cuando Doña Rosa intenta consultar `GET /inventario/cargas/<load_id>/`, recibe **`HTTP 403 Acceso denegado`**, y en `/inventario/stock/` el botón `Ver carga` está oculto para `ADMIN`.

---

### `BUG-033` [ALTA — ACTIVO] — Contradicción transversal al desactivar una Categoría (`POST /productos/categorias/<id>/estado/`): bloquea la edición del producto al Admin, tiende una trampa a Almacén y sigue vendiendo el producto en Caja
- **Rol / Persona:** Doña Rosa (`ADMIN`) + Kevin (`ALMACENERO`) + Lucía (`VENDEDOR`).
- **Módulo / Archivos afectados:** [`catalog/models.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/catalog/models.py#L93-L94) (`Product.clean`), [`catalog/services.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/catalog/services.py#L64-L71) (`update_product`), [`inventory/forms.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/inventory/forms.py#L33-L65) (`InitialLoadProductForm`, `StockEntryProductForm`), [`sales/views.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/sales/views.py#L53-L64) (`_search_products`) y [`sales/services.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/sales/services.py#L84-L87) (`add_product_to_draft`, `checkout_sale`).
- **Pasos exactos para reproducir:**
  1. Doña Rosa crea la categoría `Conservas Gourmet QA`, registra el producto `Esparragos Gourmet QA 300g` (`S/ 15.00`) y Kevin carga 20 unidades.
  2. Doña Rosa va a `/productos/categorias/` y pulsa **Desactivar** en `Conservas Gourmet QA` (`POST /productos/categorias/<id>/estado/` -> `HTTP 302`, `is_active=False`).
  3. **Acción 1 (Doña Rosa — Admin):** Entra a `/productos/<prod_id>/editar/` para cambiar el precio de `15.00` a `16.50` manteniendo su categoría actual y pulsa **Guardar cambios** (`POST`).
  4. **Acción 2 (Kevin — Almacenero):** Entra a `GET /inventario/entrada/` (o `/inventario/carga-inicial/`), selecciona `Esparragos Gourmet QA 300g` de la lista desplegable, llena el lote `ESP-L3` y pulsa **Confirmar entrada** (`POST`).
  5. **Acción 3 (Lucía — Vendedora):** Busca `Esparragos` en `GET /ventas/?query=Esparragos`, lo agrega al borrador y lo cobra en `POST /ventas/cobrar/`.
- **Expectativa de un usuario novato:**
  - Coherencia entre módulos: que Doña Rosa pueda editar los datos de un producto aunque su categoría esté inactiva, y que si un producto no admite operaciones por tener su categoría inactiva, no aparezca como seleccionable en el `<select>` de Almacén.
- **Resultado real obtenido (Evidencia HTTP/HTML):**
  1. **Bloqueo al editar producto en `/productos/<id>/editar/`:** Aunque `update_product` ([`catalog/services.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/catalog/services.py#L65)) intentó permitir mantener la categoría inactiva (`if not category.is_active and category.pk != product.category_id:`), en la línea 70 ejecuta `product.full_clean(validate_unique=False)`, donde `Product.clean()` ([`catalog/models.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/catalog/models.py#L93-L94)) lanza incondicionalmente:
     ```html
     <div class="text-danger small mt-1">Seleccione una categoría activa.</div>
     ```
     Doña Rosa queda impedida de actualizar el precio, código o stock mínimo del producto (`HTTP 200`, precio sigue en `15.00`).
  2. **Trampa en `/inventario/entrada/` y `/inventario/carga-inicial/`:** `StockEntryProductForm` y `InitialLoadProductForm` filtran `Product.objects.filter(is_active=True, ...)` **sin filtrar `category__is_active=True`**. Kevin ve el producto disponible en el `<select>`, digita todos los datos de los lotes y al enviar recibe `HTTP 200` con el rechazo: `"El producto no está disponible para registrar entradas."`.
  3. **Asimetría con Ventas (`/ventas/`):** En Caja, `_search_products`, `add_product_to_draft` y `checkout_sale` ignoran `product.category.is_active`, permitiendo vender el producto sin restricción.

---

### `BUG-035` [ALTA — ACTIVO] — Colisión multi-pestaña entre dos clientes seguidos en `/ventas/cobrar/`: `_draft_signature` no incluye `draft.pk` y permite que una pestaña rezagada del Cliente 1 cobre el borrador del Cliente 2
- **Rol / Persona:** Lucía (`VENDEDOR` 1).
- **Módulo / Archivos afectados:** [`sales/views.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/sales/views.py#L36-L40) (`_draft_signature`) y [`sales/views.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/sales/views.py#L168-L210) (`sales_checkout`).
- **Pasos exactos para reproducir:**
  1. El **Cliente 1** pide `1 × Esparragos Gourmet QA 300g` (`S/ 15.00`). Lucía lo agrega al borrador (`draft_1`) y abre `/ventas/cobrar/` en la **Pestaña 1** (`idempotency_key = K1`) y por descuido también en la **Pestaña 2** (`idempotency_key = K2`, con `cash_received = 20.00` ya digitado).
  2. Lucía confirma el cobro del Cliente 1 en la **Pestaña 1** (`POST /ventas/cobrar/` con `K1` -> `HTTP 302 Location: /ventas/constancia/f1c2f118-.../`). `draft_1` pasa a estado `DISCARDED`.
  3. Segundos después, el **Cliente 2** en la fila pide también `1 × Esparragos Gourmet QA 300g` (`S/ 15.00`). En la Pestaña 1, Lucía agrega el producto, creándose un nuevo borrador activo (`draft_2`).
  4. Lucía ve la **Pestaña 2** (que había quedado abierta del Cliente 1 con `idempotency_key = K2`, `expected_subtotal = 15.00` y `draft_signature = "<prod_id>:1:15.00"`) y pulsa **Confirmar cobro**.
- **Expectativa de un usuario novato:**
  - Que la Pestaña 2 rechace el cobro porque estaba vinculada al `draft_1` (que ya fue cobrado y cerrado), en vez de cobrar silenciosamente el `draft_2` del nuevo cliente.
- **Resultado real obtenido (Evidencia HTTP/BD):**
  - En [`sales/views.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/sales/views.py#L36-L40), `_draft_signature(draft)` calcula únicamente:
    ```python
    return "|".join(f"{l.product_id}:{l.quantity}:{l.unit_price:.2f}" for l in draft.lines.all())
    ```
    **No incluye `draft.pk`** en la firma, ni `CheckoutForm` envía `draft_id`.
  - En `sales_checkout`, la vista carga `draft = active_draft_for_actor(actor=request.user)` (que ahora es `draft_2`), comprueba que `draft_signature` (`"<prod_id>:1:15.00"`) y `expected_subtotal` (`15.00`) coinciden, y **ejecuta `checkout_sale` sobre `draft_2` (`HTTP 302 Location: /ventas/constancia/b7992e6e-.../`)**, cobrando y descontando del inventario el pedido del Cliente 2 con los datos de la pestaña vieja del Cliente 1.

---

### `BUG-036` [MEDIA — ACTIVO] — Fallo silencioso (`HTTP 200` sin mensajes de error) cuando fallan campos ocultos (`idempotency_key`, `lot_id`) y discrepancia donde `?lote=` en la URL ignora `lot_id` del POST en Bajas y Ajustes
- **Rol / Persona:** Lucía (`VENDEDOR`), Kevin (`ALMACENERO`) y Doña Rosa (`ADMIN`).
- **Módulo / Archivos afectados:** [`sales/templates/sales/sales_checkout.html`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/sales/templates/sales/sales_checkout.html#L19-L31), [`inventory/templates/inventory/writeoff_form.html`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/inventory/templates/inventory/writeoff_form.html#L33-L43), [`inventory/templates/inventory/adjustment_form.html`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/inventory/templates/inventory/adjustment_form.html#L34-L45) e [`inventory/views.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/inventory/views.py#L218-L276).
- **Pasos exactos para reproducir:**
  1. **Caso A (Campos ocultos corruptos):** Enviar `POST /ventas/cobrar/` con `idempotency_key="not-a-uuid"` (o `expected_subtotal="abc"`), o `POST /inventario/bajas/nueva/?lote=<uuid>` con `idempotency_key="invalid-uuid"`.
  2. **Caso B (Discrepancia `?lote=` vs `lot_id`):** En `POST /inventario/ajustes/nuevo/?lote=<lot1_uuid>`, enviar en el cuerpo del formulario `lot_id=<lot2_uuid>`, `delta=-1`, `reason="Prueba mismatch"`.
  3. **Caso C (`POST` sin `lote`):** Enviar `POST /inventario/bajas/nueva/` o `POST /inventario/ajustes/nuevo/` con `lot_id=""` vacío.
- **Resultado real obtenido (Evidencia HTTP/HTML/BD):**
  - **En el Caso A:** `form.is_valid()` devuelve `False`, pero como las 3 plantillas solo muestran `form.non_field_errors` y los errores de campos visibles (ocultando los errores de `idempotency_key`, `lot_id` y `expected_subtotal`), el servidor responde **`HTTP 200` sin ninguna alerta ni texto de error en toda la página**. El usuario pulsa el botón una y otra vez sin saber por qué el formulario no hace nada.
  - **En el Caso B:** En [`inventory/views.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/inventory/views.py#L218) y línea 272:
    ```python
    lot_id = request.GET.get("lote") or (request.POST.get("lot_id") if request.method == "POST" else None)
    ```
    Como el `<form method="post">` no tiene atributo `action`, conserva `?lote=<lot1_uuid>` en la URL. El backend prioriza `request.GET.get("lote")` e **ignora por completo `form.cleaned_data["lot_id"]`**, aplicando el ajuste `-1` sobre `lot1` (`18 -> 17`) en lugar de `lot2` (`10 -> 10`).
  - **En el Caso C:** Si `selected_lot` es `None`, `if request.method == "POST" and selected_lot and form.is_valid():` no entra al bloque y devuelve `HTTP 200` con la tabla de lotes sin ningún mensaje de error.

---

### `BUG-037` [MEDIA — ACTIVO] — `update_draft_line` (`POST /ventas/lineas/<id>/`) permite aumentar la cantidad de un producto DESHABILITADO por el Admin, `checkout_sale` no advierte cambios de nombre/código en vivo, y las mermas/ajustes no recalculan `average_cost`
- **Rol / Persona:** Lucía (`VENDEDOR` 1) + Doña Rosa (`ADMIN`) + Kevin (`ALMACENERO`).
- **Módulo / Archivos afectados:** [`sales/services.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/sales/services.py#L124-L145) (`update_draft_line`), [`sales/views.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/sales/views.py#L36-L40) (`_draft_signature`), [`inventory/services.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/inventory/services.py#L172-L265) (`write_off_stock`, `register_physical_adjustment`).
- **Pasos exactos para reproducir:**
  1. **Caso 1 (Producto deshabilitado en borrador):** Lucía agrega `1` unidad de `Esparragos Gourmet QA 300g` a su borrador en `/ventas/`. Doña Rosa deshabilita el producto en `POST /productos/<id>/disponibilidad/` (`is_active=False`). Lucía cambia la cantidad de `1` a `5` en `/ventas/` y pulsa **Actualizar** (`POST /ventas/lineas/<line_id>/`).
  2. **Caso 2 (Cambio de nombre del producto durante el cobro):** Mientras Lucía está en `/ventas/cobrar/` viendo `Esparragos Gourmet QA 300g`, Doña Rosa edita el nombre del producto a `Conserva Cambiada QA`. Lucía pulsa **Confirmar cobro**.
  3. **Caso 3 (`average_cost` estático tras baja total de un lote caro):** Un producto tiene el Lote 1 (`20` und. a `S/ 8.0000`) y el Lote 2 (`10` und. a `S/ 10.0000`), con `average_cost = S/ 8.6667`. Kevin da de baja por merma las `10` unidades del Lote 2 (quedando solo las `20` unidades de `S/ 8.0000`).
- **Resultado real obtenido (Evidencia HTTP/BD):**
  - **Caso 1:** `update_draft_line` no verifica `if not line.product.is_active:`. Permite a Lucía subir la cantidad a `5` (`HTTP 302`, 0 errores) y recién la bloquea cuando entra a `/ventas/cobrar/` e intenta confirmar el pago.
  - **Caso 2:** Ni `_draft_signature` ni `checkout_sale` verifican si cambió `product.name` o `product.barcode`, emitiendo la constancia de venta con el nuevo nombre sin avisarle a la cajera.
  - **Caso 3:** Ni `write_off_stock` ni `register_physical_adjustment` recalculan `product.average_cost`, que permanece congelado en `S/ 8.6667` aunque el lote de `S/ 10.0000` ya no exista en almacén.

---

### 2.2 Catálogo de Hallazgos de la Línea Base y Estado de Verificación (`BUG-001` a `BUG-031`)

---

### `BUG-001` [CRÍTICA] — Cambiar el rol de la vendedora a Almacenera mientras tiene turno abierto bloqueaba `CAJA-01` para siempre, y el Administrador sigue recibiendo `HTTP 403` si intenta cerrar un turno abandonado en `/caja/cerrar/`
- **Rol / Persona:** Doña Rosa (`ADMIN`) + Lucía (`VENDEDOR` 1) + Marcos (`VENDEDOR` 2).
- **Módulo / Archivos afectados:** [`identity/services.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/identity/services.py#L67-L123) (`update_employee`), [`cash/views.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/cash/views.py#L55-L84) (`cash_close`).
- **Pasos exactos para reproducir:**
  1. Lucía (`VENDEDOR`) abre turno en `/caja/abrir/` (`POST /caja/abrir/` con `opening_amount=100.00`) y prepara una venta en `/ventas/`.
  2. Doña Rosa (`ADMIN`) entra a `/empleados/<lucia_id>/editar/` y envía `POST` intentando cambiar el campo `role` de `VENDEDOR` a `ALMACENERO`.
  3. Además, si Lucía abandona el local dejando `CAJA-01` abierta, Doña Rosa (`ADMIN`) intenta entrar a `/caja/cerrar/` para cerrar el turno y liberar la caja para Marcos (`VENDEDOR` 2).
- **Resultado real obtenido:**
  - `update_employee` ([`identity/services.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/identity/services.py#L89-L97)) ahora bloquea el cambio de rol con `HTTP 200` mostrando: `"No se puede cambiar el rol de un empleado con un turno de caja abierto. Cierre el turno primero."`.
  - **Fallo operativo persistente:** `cash_close` (`/caja/cerrar/`) tiene `@roles_required(Role.Code.SELLER)`. **Doña Rosa (`ADMIN`) recibe `HTTP 403 Acceso denegado` en `/caja/cerrar/`**. Si una cajera se retira por emergencia dejando su turno abierto, ni el Administrador ni el otro cajero (`Marcos`) pueden cerrar esa caja directamente; Doña Rosa está obligada a resetearle la contraseña a Lucía en `/empleados/<id>/editar/`, cerrar su propia sesión e iniciar sesión como Lucía para poder liberar `CAJA-01`.

---

### `BUG-002` [CRÍTICA — VERIFICADO] — El historial de turnos `/caja/turnos/` mostraba `S/ ()` en blanco en la columna "Diferencia"
- **Rol / Persona:** Doña Rosa (`ADMIN`).
- **Módulo / Archivos afectados:** [`cash/templates/cash/cash_shift_history.html`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/cash/templates/cash/cash_shift_history.html#L35-L41) y [`cash/models.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/cash/models.py#L80-L97) (`CashShiftClose`).
- **Estado actual verificado:** Se agregaron las propiedades `difference_type`, `difference_amount` y `get_difference_type_display` en `CashShiftClose` y la utilidad `.text-primary` en `app.css`, mostrando `S/ -15,00 (Faltante)` o `S/ 10,00 (Sobrante)`.

---

### `BUG-003` [CRÍTICA — PARCIAL] — Idempotencia de Bajas (`/inventario/bajas/nueva/`) y Ajustes (`/inventario/ajustes/nuevo/`) almacenada solo en sesión volátil (`request.session`) en lugar de Base de Datos
- **Rol / Persona:** Kevin (`ALMACENERO`) y Doña Rosa (`ADMIN`).
- **Módulo / Archivos afectados:** [`inventory/views.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/inventory/views.py#L45-L67) (`_mark_inventory_key_processed`, `stock_writeoff_create`, `physical_adjustment_create`).
- **Estado actual verificado:** Ya no consume la clave cuando falla una validación de formulario, pero **a diferencia de `Sale.idempotency_key` (que es una columna `UUIDField(unique=True)` en BD), las bajas y ajustes guardan la clave únicamente en `request.session["processed_inventory_keys"]`**, y además las vistas carecen del decorador `@never_cache`. Si el usuario vuelve atrás con el navegador tras una baja exitosa y cambia la cantidad para registrar una segunda merma real en el mismo lote, el `idempotency_key` cacheado en el DOM hace que el sistema descarte su segunda baja diciendo falsamente `"Esta baja ya fue registrada anteriormente."`.

---

### `BUG-004` [CRÍTICA — ACTIVO PARCIAL] — `update_product` sobrescribe retroactivamente `product_snapshot_barcode` en todas las ventas históricas (`SaleLine`) al editar el código de barras de un producto
- **Rol / Persona:** Doña Rosa (`ADMIN`) + Kevin (`ALMACENERO`).
- **Módulo / Archivos afectados:** [`catalog/services.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/catalog/services.py#L74-L80) (`update_product`) y [`sales/models.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/sales/models.py#L124-L141) (`SaleLine`).
- **Pasos exactos para reproducir:**
  1. Se realiza y confirma una venta del producto `Esparragos Gourmet QA 300g` con código `7759900112233` (se emite la constancia `V-00000001` con `product_snapshot_name="Esparragos Gourmet QA 300g"` y `product_snapshot_barcode="7759900112233"`).
  2. Posteriormente, Doña Rosa edita el producto en `POST /productos/<id>/editar/` cambiando el nombre a `Esparragos Nuevo Nombre` y el código a `7759900119999`.
  3. Se consulta la constancia histórica `GET /ventas/constancia/<sale_id>/` y el Kardex `GET /inventario/productos/<id>/movimientos/`.
- **Resultado real obtenido (Evidencia en Vivo):**
  - Aunque ya se agregó la FK `SaleLine.product` (migración `0004_saleline_product`) para que el Kardex no dependa del código de barras, en [`catalog/services.py`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/catalog/services.py#L78-L80) se dejó la sentencia:
    ```python
    SaleLine.objects.filter(product_snapshot_barcode=old_barcode).update(
        product_snapshot_barcode=product.barcode
    )
    ```
  - Esto **viola la inmutabilidad histórica de las constancias de venta (`SaleLine`)**: la constancia emitida en el pasado muestra ahora un híbrido inconsistente con el nombre antiguo (`Esparragos Gourmet QA 300g`) pero el código de barras nuevo (`7759900119999`). Además, las filas de `Venta` en `/inventario/productos/<id>/movimientos/` siguen sin indicar de qué lote específico se descontaron las unidades vendidas por FEFO.

---

### Tabla Consolidada de Verificación de `BUG-005` a `BUG-031`

| ID | Descripción del Hallazgo | Estado en Vivo | Evidencia / Comportamiento Actual |
| :--- | :--- | :---: | :--- |
| **`BUG-005`** | `HU-INV-01b`: Recálculo de `average_cost` en entradas posteriores incluía lotes vencidos. | ✅ **Corregido** | `register_stock_entry` filtra `expiration_date__gt=current_date` al promediar lotes vigentes. |
| **`BUG-006`** | Cambio de precio por el Admin mientras la vendedora edita `/ventas/` sobrescribía el precio sin avisar. | ✅ **Corregido** | `sales_draft` y `sales_line_update` emiten `messages.warning` cuando `unit_price` cambia respecto a `old_price`. |
| **`BUG-007`** + **`BUG-025`** | Desincronización multi-pestaña en `/ventas/cobrar/` al quitar o cambiar productos del mismo subtotal. | ⚠️ **Parcial (`BUG-035`)** | Detecta cambios dentro del mismo borrador vía `draft_signature`, pero **no incluye `draft.pk` (`BUG-035`)**, permitiendo cobrar el borrador de un segundo cliente desde una pestaña vieja. |
| **`BUG-008`** | Admin veía botón `"Nueva venta"` en `/ventas/constancia/<id>/` que llevaba a `403`. | ✅ **Corregido** | `sales_receipt.html` condiciona el botón `"Nueva venta"` a `user.role.code == 'VENDEDOR'`. |
| **`BUG-009`** + **`BUG-027`** | Notación científica (`1e5`, `1e2`) y montos extremos aceptados en formularios de precios, caja y lotes. | ✅ **Corregido** | `ProductRegistrationForm`, `ProductEditForm`, `LotInputForm`, `CashOpeningForm`, `CashCloseForm` y `CheckoutForm` rechazan `"e"` y valores mayores a `9,999,999.99`. |
| **`BUG-010`** | Bajas y ajustes sin `idempotency_key` permitían duplicados en ráfaga. | ⚠️ **Parcial (`BUG-036`)** | Genera clave automática de 2 s, pero si `idempotency_key` es inválido falla silenciosamente sin mostrar error (`BUG-036`). |
| **`BUG-011`** | Módulo Proveedores desconectado de los lotes de inventario. | ⚠️ **Parcial (`BUG-032`)** | Se agregó `Lot.supplier` y se muestra en `/productos/vencimientos/`, pero **sigue ausente en `/inventario/stock/` y en los lotes de Carga Inicial del Kardex (`BUG-032`)**. |
| **`BUG-012`** | Ajustes físicos positivos mutaban `lot.initial_quantity` en la constancia y el Kardex. | ⚠️ **Parcial** | Las vistas restan `positive_adj` para mostrar la cantidad original, pero en BD `lot.initial_quantity` sigue incrementándose incluso cuando `available_quantity + delta <= initial_quantity`. |
| **`BUG-013`** | Códigos de barras aceptaban payloads `<script>` y símbolos arbitrarios. | ✅ **Corregido** | Validado con `BARCODE_PATTERN = re.compile(r"^[A-Za-z0-9\s\-]+$")`. |
| **`BUG-014`** | Fechas de vencimiento en el año `9999` aceptadas en carga de lotes. | ✅ **Corregido** | Rechaza años mayores a `today.year + 20`. |
| **`BUG-015`** | Historiales de ventas omitían la columna `Descuento (S/)`. | ✅ **Corregido** | Presente en `/ventas/historial/` y `/ventas/historial/turno/`. |
| **`BUG-016`** | Discrepancia de alertas en `/inicio/` y falta de resumen para `ALMACENERO`. | ✅ **Corregido** | `/inicio/` muestra las alertas unificadas para `ADMIN` y `ALMACENERO`. |
| **`BUG-017`** | `GET /salir/` no advertía que cerrar sesión en otra pestaña descartaría cualquier borrador futuro. | ✅ **Corregido** | `logout_confirm.html` advierte siempre al rol `VENDEDOR`. |
| **`BUG-018`** | 15 plantillas escritas con clases de Bootstrap 5 sin hoja de estilos Bootstrap. | ⚠️ **Parcheado en CSS** | `app.css` mapea las clases principales, pero los formularios de Sprints 2–3 siguen sin contenedor `.panel` blanco. |
| **`BUG-019`** | Botón `.btn-close` sin JS en `/empleados/`. | ✅ **Corregido** | Eliminado de `employee_list.html`. |
| **`BUG-020`** + **`BUG-031`** | Marca inconsistente en `/salir/`, `403.html`, `404.html` y falta de titular en `/caja/abrir/`. | ✅ **Corregido** | Títulos dinámicos por rol en `/salir/`, `403.html` y `404.html`, y nombre del cajero titular visible en `/caja/abrir/`. |
| **`BUG-021`** + **`BUG-028`** | Restricción de categoría `"Productos enlatados"`, falta de toggle en categorías y textos residuales. | ⚠️ **Parcial (`BUG-033`)** | Se agregó `category-toggle`, pero **desactivar una categoría rompe la edición de sus productos y engaña a Almacén (`BUG-033`)**, y `/productos/nuevo/` sigue diciendo *"Registrar producto enlatado"*. |
| **`BUG-022`** | Mezcla de formatos numéricos (coma decimal vs. punto decimal). | ⚠️ **Parcial** | Las plantillas usan `|floatformat:2` (coma `S/ 15,00`), pero **todos los mensajes de error de Python usan f-strings con punto (`S/ 15.00`)**. |
| **`BUG-023`** | Caminos sin salida en pantallas de confirmación y rutas alias `/creado/` y `/creada/`. | ✅ **Corregido** | Rutas alias operativas y botón `"Ir a preparar venta"` agregado en `/caja/turnos/<id>/abierto/`. |
| **`BUG-024`** | Entradas posteriores (`/inventario/entrada/`) se mezclaban con Carga Inicial en constancia y Kardex. | ⚠️ **Parcial (`BUG-032`)** | `Lot.is_initial` separa las tablas y cambia la etiqueta en el Kardex, pero **sigue reutilizando `InitialInventoryLoad` y atribuyendo todas las entradas posteriores al almacenero que hizo la carga inicial (`BUG-032`)**. |
| **`BUG-026`** | Bloqueo de login tras 5 intentos fallidos no expiraba nunca. | ✅ **Corregido** | Expiración de 5 minutos con `login_locked_until` y `SESSION_EXPIRE_AT_BROWSER_CLOSE = True`. |
| **`BUG-029`** | En `/ventas/cobrar/`, tras un error de validación se perdía la visualización del total con descuento. | ✅ **Corregido** | El backend calcula `display_totals` y el JS ejecuta `recalc()` al cargar el DOM. |
| **`BUG-030`** | `seed_demo` creaba los 4 productos demo con `average_cost = 0.0000`. | ✅ **Corregido** | `seed_demo` calcula y actualiza el `average_cost` ponderado (`4.2000`, `8.5000`, `3.1000`, `3.2214`). |

---

## 3. Auditoría de "AI Slop" y Defectos Visuales / CSS (Pilar A)

### 3.1 Esquizofrenia Visual: Diseño Nativo (`app.css`) vs. Plantillas con Estructura Bootstrap 5

El archivo base [`identity/templates/identity/base.html`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/identity/templates/identity/base.html) carga únicamente [`/static/identity/app.css`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/identity/static/identity/app.css). Aunque al final de `app.css` (líneas 1790–2020) se añadieron reglas CSS para mapear clases de Bootstrap 5 (`.btn`, `.form-control`, `.table`, `.badge`, `.row`), **conviven dos arquitecturas visuales completamente distintas dentro de la misma aplicación**:
1. **Pantallas nativas (`app.css` — Sprint 1):** Usan `<section class="page-heading">` con `eyebrow`, `<div class="content-grid content-grid-aside">`, tarjetas blancas con sombra `<form class="panel form-panel">`, `<aside class="panel info-panel">` y `<div class="table-wrap">`.
2. **Pantallas tipo Bootstrap (Sprints 2 y 3):** En `/empleados/nuevo/`, `/empleados/<id>/editar/`, `/productos/<id>/editar/`, `/productos/categorias/nueva/`, `/inventario/proveedores/nuevo/`, `/inventario/bajas/nueva/` y `/inventario/ajustes/nuevo/`, los formularios usan `<div class="row justify-content-center"><div class="col-md-6">` **sin contenedor `.panel`**, por lo que los inputs quedan flotando directamente sobre el fondo gris de la aplicación sin tarjeta blanca, sin borde y sin panel lateral de ayuda.
3. **Esquizofrenia de formato numérico (Coma vs. Punto en la misma vista):**
   - Debido a `LANGUAGE_CODE = "es-pe"`, Django formatea `{{ valor|floatformat:2 }}` con **coma decimal** (`S/ 15,00`, `S/ 6,50`).
   - En cambio, los atributos HTML (`placeholder="0.00"`), textos de ayuda (`"Se acepta 0.00"`) y **todos los mensajes de error o advertencia generados en Python** (`f"El efectivo recibido (S/ {cash_received}) es insuficiente para cubrir el total (S/ {total})."`, `f"El precio unitario de «...» se actualizó de S/ {old_price:.2f} a S/ {new_line.unit_price:.2f}."`) usan **punto decimal** (`S/ 15.00`). Un cajero novato ve en el mismo recuadro `"insuficiente para cubrir el total (S/ 10.00)"` a la izquierda y `"Total a cobrar: S/ 10,00"` a la derecha.

### 3.2 Tabla Completa de Pantallas Inspeccionadas (AI Slop, CSS y Propuestas de Mejora)

| Pantalla / Ruta | Problemas de Estilos CSS / Maquetación | Frases con "AI Slop", Jerga o Inconsistencias Textuales | Propuesta Concreta de Mejora |
| :--- | :--- | :--- | :--- |
| **Login**<br>`GET /` | Tarjeta `.login-card` bien estilizada. | Promete para el Administrador *"Productos, empleados, proveedores y reportes"*, cuando no existe ningún módulo ni menú de reportes. | Cambiar la descripción a *"Catálogo, inventario, empleados y supervisión de caja y ventas"*. |
| **Confirmación Salir**<br>`GET /salir/` | Usa `.panel.empty-state`. | El botón `Cancelar` apunta de forma estática a `href="/inicio/"` en vez de regresar a la pantalla donde estaba trabajando el usuario. | Volver a la URL previa segura (`HTTP_REFERER`) o a `/ventas/` si tiene venta activa. |
| **Inicio Minimarket**<br>`GET /inicio/` | Usa `.dashboard-hero`, `.panel.form-panel` y `.action-grid`. | **Redundancia decorativa (AI Slop):** En menos de 150 px repite 3 veces el nombre del rol (`<span class="role-pill">Administrador</span>` en topbar, `<p class="eyebrow">Administrador</p>` en hero y `<div class="date-card"><span>Sesión activa</span><strong>Administrador</strong></div>`) y duplica *"Operaciones autorizadas"* / *"Operaciones de tu puesto"*. La tarjeta `.date-card` ni siquiera muestra la fecha. | Mostrar la fecha real de Lima en `.date-card` y eliminar la repetición triple del rol. |
| **Catálogo de Productos**<br>`GET /productos/` | Usa clases Bootstrap (`.input-group`, `.table-bordered`). | No tiene botón **`+ Registrar producto`** en la esquina superior derecha para el `ADMIN` (a diferencia de `/empleados/`, `/productos/categorias/` y `/inventario/proveedores/` que sí tienen botón de creación en la cabecera). | Agregar `<a href="{% url 'product-entry' %}" class="btn btn-primary">+ Registrar producto</a>` en la cabecera para `ADMIN`. |
| **Registrar Producto**<br>`GET /productos/nuevo/` | Usa `.panel.form-panel` y `.info-panel`. | **Copy obsoleto y contradictorio:** El título dice **`<h2>Registrar producto enlatado</h2>`** y el panel lateral dice *"Los productos enlatados requieren fecha de vencimiento"*, aunque el sistema ya permite crear y seleccionar cualquier categoría (`Bebidas`, `Lácteos`, `Limpieza`). | Cambiar a *"Registrar producto"* y actualizar el texto lateral para no restringirlo a enlatados. |
| **Editar Producto**<br>`GET /productos/<id>/editar/` | Formulario flotante `.col-md-7` sin `.panel`. | Si la categoría actual del producto fue desactivada, rechaza cualquier edición de precio o stock mínimo con `"Seleccione una categoría activa."` (`BUG-033`). | Envolver en `.panel.form-panel` y permitir conservar la categoría actual en `Product.clean()`. |
| **Categorías**<br>`GET /productos/categorias/`<br>`GET /productos/categorias/nueva/` | Formulario de nueva categoría sin `.panel`. | Permite desactivar cualquier categoría sin advertir qué productos activos pertenecen a ella ni qué pasará con sus entradas de almacén (`BUG-033`). | Mostrar la cantidad de productos asociados a cada categoría y unificar el comportamiento de categorías inactivas. |
| **Vencimientos**<br>`GET /productos/vencimientos/` | Usa `.input-group` y `.table-responsive`. | Cuando un lote aparece con badge rojo **`Vencido`**, no hay ningún botón en la fila para ir a **`Dar de baja`** (`/inventario/bajas/nueva/?lote=<id>`), obligando a Kevin a copiar el código del lote y buscarlo manualmente en otra pantalla. | Añadir columna `Acción` con enlace directo a `/inventario/bajas/nueva/?lote={{ lot.pk }}` para lotes vencidos. |
| **Carga Inicial y Entrada de Mercadería**<br>`GET /inventario/carga-inicial/`<br>`GET /inventario/entrada/` | Usa `.panel.form-panel` y `.lot-grid`. | `/inventario/carga-inicial/` sigue diciendo *"Ingresa uno o varios lotes de un producto enlatado"*. Ambos selectores muestran productos cuya categoría está inactiva y luego los rechazan al enviar el POST (`BUG-033`). | Filtrar `category__is_active=True` en ambos querysets y quitar la palabra *"enlatado"*. |
| **Constancia de Carga**<br>`GET /inventario/cargas/<id>/` | Usa `.panel` y `.table-wrap`. | Devuelve **`HTTP 403`** al Administrador (`BUG-032`). Cuando un segundo almacenero registra una entrada posterior en `/inventario/entrada/`, la cabecera de esta constancia sigue mostrando como `Responsable` y `Confirmada` los datos de la carga inicial original (`BUG-032`). | Permitir acceso de lectura a `ADMIN` y almacenar `Lot.responsible` en cada lote ingresado. |
| **Baja por Merma y Ajuste Físico**<br>`GET /inventario/bajas/nueva/`<br>`GET /inventario/ajustes/nuevo/` | Formularios sin `.panel` blanco. | Si falla un campo oculto (`idempotency_key` o `lot_id`), devuelve `HTTP 200` sin mostrar ningún mensaje de error (`BUG-036`). En `/inventario/ajustes/nuevo/`, la tabla lista incluso lotes con `Disponible: 0` sin indicar el stock físico total del producto. | Mostrar errores de campos ocultos en la alerta superior y usar `form.cleaned_data["lot_id"]` en el POST. |
| **Stock e Inventario**<br>`GET /inventario/stock/` | Abuso de `style="..."` inline en paneles y celdas. | No muestra el `Costo promedio` del producto ni el proveedor de los lotes, y oculta el botón `Ver carga` para el rol `ADMIN` (`BUG-032`). | Añadir columna `Costo prom. (S/)` y habilitar `Ver carga` también para el Administrador. |
| **Movimientos (Kardex)**<br>`GET /inventario/productos/<id>/movimientos/` | Usa `.table-wrap`. | Atribuye todas las entradas posteriores al responsable de la carga inicial (`BUG-032`), omite el proveedor en los lotes de carga inicial (`BUG-032`) y no indica de qué lote salieron las ventas descontadas por FEFO (`BUG-004`). | Guardar `Lot.responsible`, mostrar el proveedor en lotes iniciales y registrar el lote consumido por cada venta. |
| **Preparar Venta y Cobro**<br>`GET /ventas/`<br>`GET /ventas/cobrar/` | Usa `.sales-layout` y `.panel`. | En `/ventas/`, la columna `Disponible` del buscador no descuenta las unidades que Lucía ya tiene agregadas en su borrador. En `/ventas/cobrar/`, si falla un campo oculto no muestra ningún error (`BUG-036`) y mezcla punto (`S/ 10.00`) en errores con coma (`S/ 10,00`) en el resumen. | Mostrar en `/ventas/` cuántas unidades ya están en el borrador y unificar el separador decimal. |

---

## 4. Tabla de "Promesas Incumplidas" (Pilar B: Lo que dice la pantalla vs. Realidad vs. Planificación)

| # | Dónde se promete (Pantalla / Documento) | Texto Exacto que Promete la Acción | Qué Ocurre en la Realidad al Intentarlo | Contraste con [`CONTROL_SPRINTS.md`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/CONTROL_SPRINTS.md) / [`AUDITORIA_USABILIDAD_05NOV2026.md`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/AUDITORIA_USABILIDAD_05NOV2026.md) |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Entrada de Mercadería (`/inventario/entrada/`)** y **Kardex (`/inventario/productos/<id>/movimientos/`)** | En `/inventario/productos/<id>/movimientos/`: Columna **`Responsable`** para cada movimiento de entrada. | **Promesa incumplida (`BUG-032`):** Cuando un segundo almacenero (`Pedro`) registra una compra posterior en `/inventario/entrada/`, tanto la constancia `/inventario/cargas/<id>/` como el Kardex dicen que el responsable fue **`Almacenero Demo` (`Kevin`)**, porque `Lot` no guarda quién registró la entrada posterior y reutiliza `lot.initial_load.responsible`. | En `AUDITORIA_USABILIDAD_05NOV2026.md` §16 se declaró resuelto `BUG-024` agregando solo el booleano `Lot.is_initial`, sin agregar `Lot.responsible`. |
| **2** | **Carga Inicial (`/inventario/carga-inicial/`)** vs. **Kardex (`/inventario/productos/<id>/movimientos/`)** | En `/inventario/carga-inicial/`: Campo **`Proveedor (opcional)`** para asociar el proveedor a los lotes iniciales. | Si Kevin selecciona un proveedor en la Carga Inicial, el Kardex (`/inventario/productos/<id>/movimientos/`) **no muestra el proveedor** en la fila `Carga inicial — Lote X` (solo lo muestra en entradas posteriores), y si Doña Rosa (`ADMIN`) intenta ver la constancia `/inventario/cargas/<id>/` recibe **`HTTP 403 Acceso denegado`** (`BUG-032`). | `HU-PROV-01..04` y `BUG-011` prometían trazabilidad del proveedor por lote, pero el Admin sigue bloqueado con `403` en la constancia de carga y el Kardex omite el proveedor inicial. |
| **3** | **Categorías (`/productos/categorias/`)** vs. **Editar Producto y Almacén** | Botón **`Desactivar`** categoría en `/productos/categorias/`. | **Comportamiento incoherente (`BUG-033`):** Al desactivar una categoría, Doña Rosa ya no puede editar el precio ni el stock mínimo de los productos de esa categoría (`/productos/<id>/editar/` la rechaza con `"Seleccione una categoría activa."`); Kevin sigue viendo esos productos en el `<select>` de `/inventario/entrada/` pero al enviar el formulario recibe error; y Lucía sigue vendiéndolos en `/ventas/` como si nada hubiera pasado. | Se agregó el toggle de categorías en `BUG-028` sin actualizar `Product.clean()`, `InitialLoadProductForm`, `StockEntryProductForm` ni `_search_products`. |
| **5** | **Constancia de Venta (`/ventas/constancia/<id>/`)** | En `sales/models.py`: *"Confirmed, immutable sale — One line of a confirmed sale with historical product snapshots."* | Si Doña Rosa corrige el código de barras de un producto en `/productos/<id>/editar/`, `update_product` **modifica retroactivamente `product_snapshot_barcode`** en todas las ventas ya confirmadas en el pasado, dejando constancias con el nombre viejo pero el código nuevo (`BUG-004`). | El parche de `BUG-004` agregó `SaleLine.product` FK pero conservó el `.update(product_snapshot_barcode=...)` sobre ventas históricas. |
| **6** | **Login (`/`)**<br>Tarjeta de roles | *"Administrador: Productos, empleados, proveedores y reportes."* | No existe ninguna sección, menú ni exportación de **Reportes**; solo un recuadro con 7 contadores del día en `/inicio/`. | `HU-REP-01` implementó únicamente el recuadro `_admin_summary` en `/inicio/`. |
| **7** | **Buscador de `/ventas/`**<br>Columna `Disponible` | Muestra `Disponible: N` junto al botón `Agregar` de cada producto. | No descuenta las unidades que la vendedora ya tiene dentro de su `Venta en preparación`. Si hay `4` disponibles y Lucía ya agregó `3` al borrador, la tabla sigue diciendo `Disponible: 4`; cuando intenta agregar `2` más, falla con error. | `HU-VEN-01a` especifica que el borrador no reserva stock en BD, pero la UI no informa cuánto del stock disponible ya está en el borrador actual. |
| **8** | **Anulación de Ventas y Cierre Administrativo de Caja** | Operación diaria de mostrador y supervisión del Administrador. | **No existe anulación/devolución de ventas confirmadas**, y **el Administrador recibe `HTTP 403` en `/caja/cerrar/`** si necesita cerrar un turno abandonado por un vendedor (`BUG-001`). | Ausente en la planificación de los Sprints 1–3. |

---

## 5. Bitácora de los Procesos Abandonados y Colisiones Multi-Rol (Pilares C y D)

### 5.1 Bitácora del Pilar C — Procesos Abandonados a la Mitad

#### Escenario C.1: Venta abandonada en el mostrador con descuento a medias e intento de cerrar caja (`Lucía`)
1. Lucía (`VENDEDOR`) abre turno en `CAJA-01` (`S/ 100.00`), agrega 4 productos a `/ventas/`, entra a `GET /ventas/cobrar/`, escribe un descuento a medias y sin confirmar el cobro se va a `/inicio/`, luego a `/ventas/historial/turno/` y finalmente a `/caja/cerrar/`.
2. **Resultado en `GET /caja/cerrar/` y `POST /caja/cerrar/`:** El sistema detecta `has_active_draft=True`, bloquea el cierre (`HTTP 200`) y le muestra un mensaje claro con un botón directo `<a class="button button-secondary" href="/ventas/">Ir a la venta en preparación</a>`, donde dispone del botón `Descartar venta`.

#### Escenario C.2: Abandono y manipulación multi-pestaña en `/ventas/cobrar/` (`Lucía`)
1. **Sub-caso C.2a (Quitar todos los productos uno por uno en la Pestaña 2 mientras la Pestaña 1 sigue en `/ventas/cobrar/`):** Al quitar la última línea en la Pestaña 2, el borrador pasa a `DISCARDED`. Cuando Lucía pulsa **Confirmar cobro** en la Pestaña 1, recibe `HTTP 302 Location: /ventas/` con el mensaje `"No tienes una venta en preparación."`.
2. **Sub-caso C.2b (Modificar cantidades o cambiar un producto por otro del mismo precio en la Pestaña 2 dentro del mismo borrador):** `expected_subtotal` y `draft_signature` detectan la diferencia en la Pestaña 1 (`HTTP 200`), actualizan el resumen en pantalla y muestran: `"Los productos de la venta en preparación fueron modificados en otra pestaña. El nuevo subtotal es S/ ...; revisa el resumen antes de confirmar el cobro."`.
3. **Sub-caso C.2c (Pestaña 2 rezagada del Cliente 1 cobra por accidente el nuevo borrador del Cliente 2 — `BUG-035`):** Si Lucía abrió `/ventas/cobrar/` en dos pestañas para el Cliente 1 (`1 × Esparragos` a `S/ 15.00`), cobró en la Pestaña 1, luego armó un nuevo borrador idéntico (`1 × Esparragos` a `S/ 15.00`) para el Cliente 2 y pulsó **Confirmar cobro** en la Pestaña 2 vieja, **como `_draft_signature` no incluye `draft.pk`, la Pestaña 2 cobra silenciosamente la venta del Cliente 2 (`HTTP 302`)**.

#### Escenario C.3: Carga inicial con la 3.ª fila incompleta (solo fecha de vencimiento) y retroceso con el navegador (`Kevin`)
1. Kevin (`ALMACENERO`) llena 2 filas de lotes en `/inventario/carga-inicial/`, deja la 3.ª fila solo con `lots-2-expiration_date` y sin cantidad ni costo, y envía (`POST /inventario/carga-inicial/`).
2. El formset rechaza atómicamente todo el envío (`HTTP 200`, 0 lotes creados) marcando `"Este campo es obligatorio."` en los 3 campos faltantes de la 3.ª fila. Al limpiar la 3.ª fila, cambiar de producto y reenviar, la carga se confirma sin residuos (`HTTP 302`).
3. **Fallo al usar el botón "Atrás" del navegador en Bajas y Ajustes (`BUG-003` / `BUG-036`):** Como `/inventario/bajas/nueva/` y `/inventario/ajustes/nuevo/` no tienen `@never_cache`, si Kevin registra una merma, vuelve atrás con el navegador para registrar otra merma distinta del mismo lote y envía, el formulario reutiliza el `idempotency_key` cacheado y descarta la operación diciendo `"Esta baja ya fue registrada anteriormente."`.

#### Escenario C.4: Arrepentimiento en cierre de sesión (`/salir/`) y Caminos sin Salida (*Dead-ends*)
1. Si Lucía abre `GET /salir/` en una pestaña (ve la advertencia de que se descartará su venta en preparación), no confirma el `POST`, sigue agregando productos en otra pestaña y luego envía `POST /salir/` en la primera pestaña, el sistema descarta limpiamente el borrador activo y cierra la sesión (`HTTP 302 Location: /`).
2. **Caminos sin salida verificados:**
   - `/ventas/constancia/<id>/`, `/caja/turnos/<id>/cerrado/`, `/caja/turnos/<id>/abierto/`, `/productos/<id>/creado/` y `/inventario/carga-inicial/<id>/creada/` cuentan con botones de continuación para el rol correspondiente.
   - **Bloqueo para el Admin (`BUG-032`):** `/inventario/cargas/<id>/` y `/inventario/carga-inicial/<id>/creada/` bloquean a Doña Rosa (`ADMIN`) con **`HTTP 403`**.

---

### 5.2 Bitácora del Pilar D — Caos Multi-Rol y Modificaciones Absurdas

#### Colisiones en Vivo entre Doña Rosa (`ADMIN`), Kevin/Pedro (`ALMACENERO`) y Lucía/Marcos (`VENDEDOR`)
1. **Caso 1 — Doña Rosa cambia el precio de `S/ 5.00` a `S/ 99.00` mientras Lucía está en `/ventas/cobrar/`:**
   - Al pulsar **Confirmar cobro**, `checkout_sale` detecta el cambio de precio, actualiza `line.unit_price` a `99.00`, detiene el cobro (`HTTP 200`) y muestra: `"El precio de «...» cambió de S/ 5.00 a S/ 99.00. Verifica el nuevo total antes de confirmar el cobro."`.
   - **Variante (`BUG-037`):** Si Doña Rosa cambia el **nombre** o **código de barras** del producto manteniendo el mismo precio mientras Lucía está en `/ventas/cobrar/`, el sistema **no avisa nada** y emite la constancia con el nuevo nombre.
2. **Caso 2 — Doña Rosa deshabilita el producto X mientras Lucía opera:**
   - Si Lucía está en `/ventas/cobrar/` y pulsa **Confirmar cobro**, recibe `HTTP 200` con: `"El producto «...» ya no está disponible para la venta. Quítalo de la venta en preparación para continuar."`.
   - **Fallo en `/ventas/` (`BUG-037`):** Si Lucía está en `/ventas/` y actualiza la cantidad de la línea (`POST /ventas/lineas/<id>/`) de `1` a `5` después de que Doña Rosa deshabilitó el producto, **`update_draft_line` permite aumentar la cantidad a `5` sin ningún error ni advertencia**.
3. **Caso 3 — Kevin da de baja por merma todas las unidades del producto X mientras Lucía está en `/ventas/cobrar/`:**
   - Al pulsar **Confirmar cobro**, Lucía recibe `HTTP 200` con: `"Stock insuficiente para '...'. Disponible: 0, solicitado: ..."` sin descontar stock negativo ni generar error `500`.
4. **Caso 4 — Doña Rosa intenta cambiar el rol de Lucía a Almacenera con turno abierto:**
   - Cambiar el rol de Lucía con turno abierto es bloqueado (`HTTP 200`: `"No se puede cambiar el rol de un empleado con un turno de caja abierto. Cierre el turno primero."`).

## 6. Verificación Cruzada de Números (Sección 3 — Auditoría Contable y de Kardex)

### 6.1 Auditoría Cruzada de Kardex y Stock por Producto

Se ejecutó el ciclo completo sobre el producto de auditoría:
- **Carga inicial (`Kevin`):** Lote `AUD-L1` (`+20` und. a `S/ 6.0000`, vence en 10 días) y Lote `AUD-L2` (`+10` und. a `S/ 9.0000`, vence en 180 días), con proveedor `Agroindustrias del Sur SAC`.
- **Entrada posterior (`Pedro` — 2.º almacenero):** Lote `AUD-L3` (`+10` und. a `S/ 11.0000`, vence en 240 días), con proveedor `Agroindustrias del Sur SAC`.
- **Ventas en caja (`Lucía`):** Venta 1 (`-2` und.) y Venta 2 (`-3` und. con descuento), descontadas por FEFO del lote más próximo a vencer (`AUD-L1`).
- **Baja por merma (`Kevin`):** `-4` und. por daño sobre `AUD-L1`.
- **Ajuste físico positivo (`Doña Rosa`):** `+3` und. sobre `AUD-L1`.
- **Ajuste físico negativo (`Doña Rosa`):** `-2` und. sobre `AUD-L2`.

$$\text{Stock Esperado} = 30\text{ (carga inicial)} + 10\text{ (entrada)} - 5\text{ (ventas)} - 4\text{ (merma)} + 3\text{ (ajuste +)} - 2\text{ (ajuste -)} = \mathbf{32\text{ unidades}}$$

| Pantalla Consultada | Stock Físico / Vendible | ¿Cuadran las Unidades? | Hallazgos / Discrepancias de Trazabilidad Detectadas |
| :--- | :---: | :---: | :--- |
| **`GET /inventario/stock/`** | Físico: `32` \| Vendible: `32` | ✅ Sí (`32 = 32`) | Las unidades cuadran, pero **no muestra el `average_cost`** (que tampoco se recalcula tras mermas o ajustes — `BUG-037`) y **oculta el botón `Ver carga` para Doña Rosa (`ADMIN`)** (`BUG-032`). |
| **`GET /productos/vencimientos/?dias=30`** | Lote `AUD-L1`: `14` disponibles | ✅ Sí (`20 - 5 - 4 + 3 = 14`) | Cuadra exactamente con el saldo del lote `AUD-L1` tras aplicar FEFO, merma y ajuste positivo. |
| **`GET /inicio/`** *(Resumen Admin y Almacenero)* | Alertas de stock bajo, por vencer y vencidos | ✅ Sí | Los contadores de `/inicio/` coinciden exactamente con los paneles superiores de `/inventario/stock/`. |
| **`GET /inventario/cargas/<load_id>/`** | `32 UND` físicas (`AUD-L1`: `14`, `AUD-L2`: `8`, `AUD-L3`: `10`) | ⚠️ **Unidades sí, Acceso y Responsable no (`BUG-032`)** | Doña Rosa (`ADMIN`) recibe **`HTTP 403`** al intentar abrir esta URL. Para Kevin/Pedro, la cabecera atribuye toda la constancia al almacenero de la carga inicial. |
| **`GET /inventario/productos/<id>/movimientos/`** *(Kardex)* | Suma algebraica: `+20 + 10 + 10 - 2 - 3 - 4 + 3 - 2 = 32` | ⚠️ **Suma sí, metadatos incompletos (`BUG-032`, `BUG-004`)** | 1) La entrada posterior `AUD-L3` hecha por `Pedro` aparece con **`Responsable: Almacenero Demo (Kevin)`** (`BUG-032`).<br>2) Los lotes iniciales `AUD-L1` y `AUD-L2` omiten el nombre del proveedor (`BUG-032`).<br>3) Las filas de `Venta` no indican que salieron del lote `AUD-L1` (`BUG-004`). |

### 6.2 Auditoría Cruzada del Turno de Caja (`CAJA-01`)

Secuencia ejecutada en el turno de `Lucía`:
- **Apertura (`POST /caja/abrir/`):** `S/ 150.00`
- **Venta 1 (sin descuento):** Subtotal `S/ 20.00`, Descuento `S/ 0.00`, Total cobrado `S/ 20.00` (Efectivo `S/ 50.00`, Vuelto `S/ 30.00`)
- **Venta 2 (con descuento):** Subtotal `S/ 30.00`, Descuento `S/ 5.00`, Total cobrado `S/ 25.00` (Efectivo `S/ 30.00`, Vuelto `S/ 5.00`)
- **Cierre (`POST /caja/cerrar/`):** Esperado $\text{S/ } 150.00 + \text{S/ } 45.00 = \mathbf{\text{S/ } 195.00}$ | Contado declarado: **`S/ 180.00`** | Diferencia: **`S/ -15.00` (Faltante)**.

| Pantalla Consultada | Apertura | Ventas Netas | Descuentos | Esperado | Contado | Diferencia | ¿Cuadra? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`GET /ventas/historial/turno/`** *(con turno abierto)* | — | `S/ 45,00` | `S/ 5,00` | — | — | — | ✅ Sí cuadra. |
| **`GET /ventas/historial/`** | — | `S/ 45,00` *(filtrado)* | `S/ 5,00` *(filtrado)* | — | — | — | ✅ Sí cuadra. |
| **`GET /caja/turnos/<id>/cerrado/`** *(Acta de cierre)* | `S/ 150,00` | *(Implícito: `45,00`)* | — | `S/ 195,00` | `S/ 180,00` | `Faltante S/ -15,00` | ✅ Sí cuadra (`150 + 45 = 195`, diferencia `-15,00`). |
| **`GET /caja/turnos/`** *(Historial de turnos)* | `S/ 150,00` | — | — | `S/ 195,00` | `S/ 180,00` | `S/ -15,00 (Faltante)` | ✅ Sí cuadra. |
| **`GET /inicio/`** *(Resumen del día Admin)* | — | Acumulado del día | Acumulado del día | — | — | — | ✅ Sí cuadra con las ventas confirmadas del día en Lima. |

---

## 7. Limpieza y Restauración del Entorno

1. **Restauración íntegra de la base de datos:** Se detuvo el servidor de pruebas y se restauró `r1_pmv.sqlite3` desde el respaldo previo a la auditoría (`r1_pmv.backup_20261105_1245.sqlite3`), verificando que el archivo SQLite quede idéntico bit a bit a su estado inicial.
2. **Eliminación de archivos temporales:** Se eliminaron los respaldos temporales `r1_pmv.backup_*.sqlite3` y el script temporal de verificación en `scratch/audit_live_verification.py`.
3. **Aplicación posterior de correcciones y pruebas automatizadas:** A solicitud del usuario, tras concluir la fase de auditoría pura se implementaron las correcciones de `BUG-032` a `BUG-037` (y residuales de `BUG-003`, `BUG-004`, `BUG-005`) documentadas en la Sección 8.

---

## 8. Registro de Corrección y Trazabilidad Scrum (`BUG-032` a `BUG-037` — 202 Pruebas en Verde)

Todos los problemas detectados en esta auditoría fueron corregidos en el código fuente, respaldados con **9 nuevas pruebas unitarias y de integración** (elevando la suite total de **193 a 202 tests en verde**, `exit 0`) y trazados en [`08_Historias_de_Usuario.md`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/08_Historias_de_Usuario.md), [`16_Task_Breakdown.md`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/16_Task_Breakdown.md), [`03_Matriz_de_Trazabilidad_y_Pruebas.md`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/03_Matriz_de_Trazabilidad_y_Pruebas.md), [`CONTROL_SPRINTS.md`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/CONTROL_SPRINTS.md) y [`AUDITORIA_USABILIDAD_05NOV2026.md`](file:///c:/Users/walte/OneDrive/Imágenes/planificacion_limpia/r1-pmv/AUDITORIA_USABILIDAD_05NOV2026.md):

| ID | Historias de Usuario | Subtarea WBS | Corrección Técnica Aplicada | Prueba Automatizada (`manage.py test`) | Estado |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **`BUG-032`** | `HU-INV-01a`, `HU-INV-01b`, `HU-INV-06`, `HU-PROV-01..04` | `QA-FIX-INV-01` | Migración `0005_lot_responsible` (`Lot.responsible` FK) poblada en `confirm_initial_load`, `register_stock_entry` y `seed_demo`; proveedor visible en lotes de carga inicial y posteriores en `product_movements`; acceso de lectura para `ADMIN` en `initial_load_created` (`/inventario/cargas/<id>/`) y botón `"Ver carga"` en `stock_overview.html`. | `inventory.tests.PhysicalAdjustmentTests.test_bug032_subsequent_stock_entry_records_second_warehouse_worker_and_admin_can_view_load` | ✅ **Corregido** |
| **`BUG-033`** | `HU-CAT-01`, `HU-PROD-04`, `HU-INV-01a`, `HU-INV-01b`, `HU-VEN-01a..01c` | `QA-FIX-CAT-01`, `QA-FIX-INV-01`, `QA-FIX-SALES-01` | `Product.clean()` permite editar precio, nombre o stock mínimo de un producto cuya categoría fue desactivada si mantiene su categoría actual; `InitialLoadProductForm`, `StockEntryProductForm`, `_search_products`, `add_product_to_draft`, `update_draft_line`, `checkout_sale` y `_admin_summary` filtran `category__is_active=True`. | `catalog.tests.ProductExpirationsTests.test_bug033_product_with_inactive_category_can_update_price_and_name`, `inventory.tests.PhysicalAdjustmentTests.test_bug033_inactive_category_excludes_products_from_initial_load_and_stock_entry_forms`, `sales.tests.SalesHistoryTests.test_bug033_and_bug037_inactive_category_or_product_blocks_search_draft_line_update_and_checkout` | ✅ **Corregido** |
| **`BUG-035`** | `HU-VEN-01b`, `HU-VEN-01c` | `QA-FIX-SALES-01` | `_draft_signature(draft)` incluye `draft.pk`, nombre y código de barras de cada línea (`f"{draft.pk}|..."`), impidiendo que una pestaña antigua cobre el borrador de un nuevo cliente con igual producto y subtotal. | `sales.tests.SalesHistoryTests.test_bug035_and_bug036_draft_signature_includes_draft_id_and_checkout_renders_hidden_field_errors` | ✅ **Corregido** |
| **`BUG-036`** + **`BUG-003`** | `HU-INV-02`, `HU-INV-03`, `HU-VEN-01c` | `QA-FIX-INV-01`, `QA-FIX-SALES-01` | `@never_cache` en vistas de carga, entrada, baja y ajuste; prioridad de `request.POST["lot_id"]` sobre `?lote=` en peticiones `POST`; y renderizado visible de errores de campos ocultos (`form.hidden_fields`) en `sales_checkout.html`, `writeoff_form.html` y `adjustment_form.html`. | `inventory.tests.PhysicalAdjustmentTests.test_bug036_writeoff_and_adjustment_prioritize_posted_lot_id_and_render_hidden_field_errors`, `sales.tests.SalesHistoryTests.test_bug035_and_bug036_draft_signature_includes_draft_id_and_checkout_renders_hidden_field_errors` | ✅ **Corregido** |
| **`BUG-037`** + **`BUG-004`** + **`BUG-005`** | `HU-VEN-01b`, `HU-PROD-04`, `HU-INV-02`, `HU-INV-03` | `QA-FIX-SALES-01`, `QA-FIX-CAT-01`, `QA-FIX-INV-01` | `update_draft_line` valida `line.product.is_active` y `line.product.category.is_active`; `update_product` preserva inmutable `SaleLine.product_snapshot_barcode` en ventas históricas; y `_recalculate_product_average_cost` recalcula `product.average_cost` tras mermas y ajustes físicos. | `sales.tests.SalesHistoryTests.test_bug033_and_bug037_inactive_category_or_product_blocks_search_draft_line_update_and_checkout`, `catalog.tests.ProductExpirationsTests.test_bug004_product_barcode_update_preserves_historical_sale_line_snapshot`, `inventory.tests.PhysicalAdjustmentTests.test_bug005_writeoff_and_physical_adjustment_recalculate_average_cost` | ✅ **Corregido** |
