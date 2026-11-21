# Adenda vigente de ETAPA-11 · 12/11/2026

**Estado actual:** Muestras ejecutadas; integridad y política nuevas pendientes. **Pendientes compartidos:** Lotes/snapshots, nuevos descuentos deshabilitados, límites y caída. **Próximo cursor:** DEC-11-MODELO-AUDITORIA-VENTAS.

[Mapa consolidado y decisiones](conciliacion_20261112/CONSOLIDACION.md) · [Contratos de implementación](conciliacion_20261112/ENCARGOS.md) · [Verificación integrada](conciliacion_20261112/VERIFICACION.md) · [Informe original íntegro](conciliacion_20261112/BASELINE/auditoria_por_etapas/resultados/ETAPA-11.md).

Las decisiones nuevas se aceptan desde12/11 por delegación explícita del usuario. No se cambia el resultado histórico de una muestra ni se declara cerrado el módulo. Requisitos recién revisados requieren nueva implementación/verificación. Las referencias de línea del texto histórico remiten a BASELINE. Los anexos conservan su fecha y vigencia original; los estados actuales se consultan en el mapa.

## Rectificaciones transversales aplicables

Etapa09 sí tiene ejecución/evidencia (Chrome67funcionales+1control), aunque10–12 y estado general antiguos la dejaban pendiente. 04-D acredita revocación en sus muestras; su límite raw sin petición/servicio permanece. El fallo `_state.adding` de inventario fue corregido05-L e incluido en434tests actuales. Los informes antiguos que lo separaban no prueban fallo actual. El empate de orden de turnos no se considera corregido por repetir una corrida. Soporte12PG es DjangoClient concurrente contraPG, no redHTTP por sockets. 05-Linterrupción antes de escribir no prueba caída postwrite. HU-VEN-05b pide filtrosCA02 y detalleCA03; no hay conflicto de líneas expandidas.

---

## Informe y resultados históricos conservados

# Etapa 11 · Cobro en efectivo, descuentos, exactitud e integridad

Actualizado: **11/11/2026** (America/Lima; marcas UTC `20261111T2349Z`–`20261112T0018Z` en corridas y artefactos; cierre documental `12/11/2026`).  
Estado del módulo en este corte: **`AUDITORÍA COMPLETADA EN ALCANCE VIGENTE CON CONFLICTOS DE DESCUENTOS Y DECISIONES ABIERTAS · 11-A`**.

> **Alcance estricto y no cierre global.** Esta etapa audita `HU-VEN-01c/CA-01..06`, el cobro en efectivo, los descuentos implementados sin historia asignada, el cálculo decimal base/IGV (`ROUND_HALF_UP`), el descuento FEFO y exclusión de vencidos, la idempotencia, el doble envío, el cambio en vivo de precio/stock entre pantallas, la reversión atómica ante error, la advertencia tributaria previa a confirmar y los efectos atómicos entre `sales` ([`sales/models.py`](../../r1-pmv/sales/models.py#L1-L149), [`sales/forms.py`](../../r1-pmv/sales/forms.py#L61-L126), [`sales/services.py`](../../r1-pmv/sales/services.py#L302-L543), [`sales/views.py`](../../r1-pmv/sales/views.py#L198-L399), [`sales_checkout.html`](../../r1-pmv/sales/templates/sales/sales_checkout.html#L1-L150)), `cash` ([`cash/services.py`](../../r1-pmv/cash/services.py#L1-L120), [`cash/views.py`](../../r1-pmv/cash/views.py#L80-L160)) e `inventory`/`admin` ([`_admin_summary`](../../r1-pmv/identity/views.py#L225-L265), [`product_movements`](../../r1-pmv/inventory/views.py#L520-L600)). **No da por cerrada `ETAPA-09`** (`NO EJECUTADO`), **no cierra el ciclo completo de constancias e historiales** (`HU-VEN-02a`, `HU-VEN-05a/05b`, `HU-CAJA-05` → **Etapa 12**), **no implementa ni aprueba** `HU-VEN-03/06a/06b/06c/07` (`PREVISTO/FUTURO`), ni sustituye `PT-CHECKOUT-01`, `MT-COMPAT-01` solo teclado, `390×844`, `SIGKILL`, `PostgreSQL 17`, el fallo preexistente [`inventory/test_audit07_stock_expirations.py#L491`](../../r1-pmv/inventory/test_audit07_stock_expirations.py#L491) ni el despliegue de migraciones en `r1_pmv.sqlite3`. Los aportes hermanos de Etapa 12 observados en el árbol (`19:14:54`) se atribuyen explícitamente sin presentar Etapa 12 como terminada.

---

## 1. Alcance, inventario documental y conflictos

### 1.1 Código, migraciones, plantillas y estilos auditados
- **Rutas `sales` ([`sales/urls.py#L1-L14`](../../r1-pmv/sales/urls.py#L1-L14)):**
  - `GET/POST /ventas/cobrar/` (`sales-checkout`) → [`sales_checkout`](../../r1-pmv/sales/views.py#L198-L372).
  - Contrato de enlace y verificación cruzada de acceso/render hacia rutas hermanas de Etapa 12: `GET /ventas/constancia/<uuid:sale_id>/` (`sales-receipt`, [`sales_receipt`](../../r1-pmv/sales/views.py#L375-L399)), `GET /ventas/historial/turno/` (`sales-shift-history`, [`sales_shift_history`](../../r1-pmv/sales/views.py#L404-L428)) y `GET /ventas/historial/` (`sales-history`, [`sales_history`](../../r1-pmv/sales/views.py#L437-L450)).
- **Modelos y migraciones ([`sales/models.py#L1-L149`](../../r1-pmv/sales/models.py#L1-L149), `sales/migrations/0001..0005`):**
  - `SaleCounter` (`id=1`, `next_value`), `SaleDraft`, `SaleDraftLine`, `Sale` (`total_amount`, `base_amount`, `igv_amount`, `discount_amount` añadido en [`0003_sale_discount_amount.py#L1-L19`](../../r1-pmv/sales/migrations/0003_sale_discount_amount.py#L1-L19), `cash_received`, `change_given`, `correlative` único `V-00000001`, `idempotency_key` `UUIDField(unique=True)`, `confirmed_at`) y `SaleLine` (`product` nullable `PROTECT`, `product_snapshot_name`, `product_snapshot_barcode`, `quantity`, `unit_price`, `amount`, `unit_cost` de 4 decimales nullable y `editable=False`).
- **Formulario, servicios y plantilla de cobro:** [`CheckoutForm`](../../r1-pmv/sales/forms.py#L61-L126), [`checkout_sale`](../../r1-pmv/sales/services.py#L302-L543) y auxiliares ([`_validate_money_decimal`](../../r1-pmv/sales/services.py#L52-L63), [`_verify_idempotent_sale`](../../r1-pmv/sales/services.py#L66-L84), [`_lock_seller_actor`](../../r1-pmv/sales/services.py#L87-L96), [`draft_signature`](../../r1-pmv/sales/services.py#L140-L145), [`_check_reviewed_draft`](../../r1-pmv/sales/services.py#L148-L156), [`_locked_draft_lines_and_products`](../../r1-pmv/sales/services.py#L159-L169)), [`sales_checkout.html`](../../r1-pmv/sales/templates/sales/sales_checkout.html#L1-L150) y [`identity/static/identity/app.css`](../../r1-pmv/identity/static/identity/app.css).
- **Integración transversal verificada:** [`cash/services.py#L1-L120`](../../r1-pmv/cash/services.py#L1-L120), [`cash/views.py#L80-L160`](../../r1-pmv/cash/views.py#L80-L160), [`cash_close.html#L1-L72`](../../r1-pmv/cash/templates/cash/cash_close.html#L1-L72), [`_admin_summary`](../../r1-pmv/identity/views.py#L225-L265) y [`product_movements`](../../r1-pmv/inventory/views.py#L520-L600).
- **Suite nueva de la etapa:** [`CheckoutAndDiscountAudit11Tests`](../../r1-pmv/sales/test_audit11_checkout.py#L1-L551) (`10` métodos de prueba).
- **Atribución de cambios hermanos de Etapa 12 y línea de tiempo (`19:14:54`):**
  - El bloque pre-borrador para reintento idempotente cuando el borrador ya fue descartado ([`sales/views.py#L205-L275`](../../r1-pmv/sales/views.py#L205-L275)), el banner literal *`CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO`* + fila condicional `Subtotal`/`Descuento` + `@media print` en [`sales_receipt.html#L1-L100`](../../r1-pmv/sales/templates/sales/sales_receipt.html#L1-L100), los estilos `/* Audit 12 */` en [`app.css#L2332-L2525`](../../r1-pmv/identity/static/identity/app.css#L2332-L2525) (modificados a las `19:14:54`) y la suite [`sales/test_audit12_receipts_history.py`](../../r1-pmv/sales/test_audit12_receipts_history.py) corresponden a trabajo hermano de Etapa 12.
  - Por transparencia de cronología: la corrida limpia de `sales`+`cash` (`dcfe6fbb`, `78/78`) finalizó a las `19:14:07` (justo antes del ajuste puramente CSS en `app.css#L2332-L2525` a las `19:14:54`), mientras que la corrida de las otras 4 apps (`61c6bec0`, `325/325`, `19:15:19`), el recorrido completo en Chrome (`d9560c03`, `60` ítems + `9` PNG, `19:16:43`), la suite aislada de Etapa 12 (`88b915e1`, `5/5`, `19:17:01`) y `checks` (`f692635d`, `19:18:37`) se ejecutaron **después** de `19:14:54` sobre el árbol final.

### 1.2 Fuentes consultadas
- Protocolo y etapa: [`../PROTOCOLO_COMUN.md`](../PROTOCOLO_COMUN.md), [`../11_Cobro_y_descuentos.md`](../11_Cobro_y_descuentos.md), [`ESTADO_GENERAL.md`](ESTADO_GENERAL.md).
- Planificación rectora: [`01_Proyecto_y_Releases.md#L85-L160`](../../01_Proyecto_y_Releases.md#L85-L160), [`02_Diseno_Tecnico_R1_PMV.md#L100-L270`](../../02_Diseno_Tecnico_R1_PMV.md#L100-L270), [`03_Matriz_de_Trazabilidad_y_Pruebas.md#L100-L200`](../../03_Matriz_de_Trazabilidad_y_Pruebas.md#L100-L200), [`07_Reglas_de_Negocio.md#L55-L406`](../../07_Reglas_de_Negocio.md#L55-L406), [`08_Historias_de_Usuario.md#L555-L680`](../../08_Historias_de_Usuario.md#L555-L680), [`09_Product_Backlog.md#L35-L140`](../../09_Product_Backlog.md#L35-L140), [`16_Task_Breakdown.md#L135-L185`](../../16_Task_Breakdown.md#L135-L185), [`21_Alcance_Actual_y_Diferencias.md#L1-L87`](../../21_Alcance_Actual_y_Diferencias.md#L1-L87) y [`r1-pmv/CONTROL_SPRINTS.md#L1-L94`](../../r1-pmv/CONTROL_SPRINTS.md#L1-L94).
- Jira está excluido (`21:3`) y `PLANIFICACION_SCRUM_R1PMV.xlsx` no existe (`False`).

### 1.3 Conflictos documentales, fronteras heredadas y exclusiones
1. **`CONFLICTO DE FUENTES` / `EXTRA SIN REQUISITO` (`DEC-11-DESCUENTOS-ALCANCE`):** Ni `01`, `07`, `08` ni `09` contemplan descuentos en ventas ni reglas de tope/autorización; [`21_Alcance_Actual_y_Diferencias.md#L25`](../../21_Alcance_Actual_y_Diferencias.md#L25) y [`CONTROL_SPRINTS.md#L89`](../../r1-pmv/CONTROL_SPRINTS.md#L89) advierten explícitamente sobre el error de etiquetar descuentos como `HU-VEN-03` (que en `08` es envío de comprobante PDF por correo) y registran los descuentos vigentes (`sales.0003`, `CheckoutForm`, `checkout_sale`, `_admin_summary`) como **«Sin identificador de HU validado»**. Hoy cualquier `VENDEDOR` puede aplicar un descuento en soles (`0 <= discount < subtotal`, total neto `>= 0.01`) sin tope porcentual, motivo ni autorización de `ADMIN`.
2. **Modelo físico vs entidades lógicas de [`02_Diseno_Tecnico_R1_PMV.md#L100-L270`](../../02_Diseno_Tecnico_R1_PMV.md#L100-L270) (`DEC-11-MODELO-AUDITORIA-VENTAS`):** El diseño lógico enumera `inventory_movement`, `idempotency_record`, `sale_lot_allocation`, `cash_movement` y `audit_event`. En el código actual no existen tablas separadas para esos cinco conceptos: la idempotencia se verifica contra `Sale.idempotency_key` (únicamente si la venta llegó a persistirse), la asignación FEFO rebaja `Lot.available_quantity` en sitio sin tabla `sale_lot_allocation` (el Kardex muestra `-sl.quantity` agregado por `SaleLine`) y no existe bitácora persistida de intentos fallidos/descuentos.
3. **Frontera heredada `DEC-03AG` (`RN-28`, `SaleLine.unit_cost`):** El costo unitario ponderado histórico de 4 decimales (`nullable`, `editable=False`, añadido en `sales.0004`) se copia desde `Product.average_cost` al confirmar (`V-00000001..03` registraron `1.7500`, `6.0000`, `2.0824` y `4.0000`), manteniendo filas legadas con `NULL` cuando preceden a la columna/migración.
4. **PostgreSQL (`03_Matriz:168`) y migraciones pendientes:** La matriz cita `PostgreSQL 17`; las pruebas de concurrencia se ejecutaron en **PostgreSQL `18.4`**. Las migraciones existentes (`sales.0001..0005`) permanecen probadas solo en bases aisladas sin tocar `r1_pmv.sqlite3`.
5. **Suites externas separadas (`88b915e1`, `54251f2e`):** [`sales.test_audit12_receipts_history`](../../r1-pmv/sales/test_audit12_receipts_history.py) (`5/5 OK` en `88b915e1`) y el bloque externo [`54251f2e`](evidencias/11-tests-20261112T001701839181Z-54251f2e/summary.json) (`sales.test_audit10_draft`, `cash.test_audit09_cash`, `inventory.test_audit03aj_session`, `inventory.test_audit07_stock_expirations`: `25 OK + 1 FAIL` por la regresión preexistente en [`inventory/test_audit07_stock_expirations.py#L491`](../../r1-pmv/inventory/test_audit07_stock_expirations.py#L491) `AssertionError: 2 != 0`) se mantienen estrictamente fuera de la suma limpia `403/403`.

---

## 2. Entorno, aislamiento, conservación e instantánea final

- **Plataforma y motores:** Windows (`win32`), Python `3.12` (`.venv`), Django `5.2.18`, **Chrome `157.0.8103.78`** vía Playwright (`1366×900`, `es-PE`), **PostgreSQL `18.4`** (`read committed`, puerto efímero `51046`).
- **Aislamiento criptográfico ([`audit11_settings.py`](soporte/audit11_settings.py#L1-L61)):** bloquea `.env`, exige directorio `etapa11-*` con `marker.json`, usa cookies propias (`audit11_sessionid`, `audit11_csrftoken`), enlaza `127.0.0.1` en puerto efímero y firma respuestas HTTP con HMAC-SHA256 (`X-Audit11-Challenge`, `X-Audit11-Proof`, `X-Audit11-Run`).
- **Conservación verificada:**
  - `r1-pmv/r1_pmv.sqlite3` intacta en todas las corridas finales y tras el cierre: **`SHA256 = 4406ECD5BABAB34F0BB264E82C134EB21563494F9FAF50E462D50C30C9D2EA95`**.
  - `PLANIFICACION_SCRUM_R1PMV.xlsx` ausente (`XLSX_EXISTS=False`), `protected_unchanged: true` en `checks`, `tests`, Chrome (`d9560c03`) y PostgreSQL (`5d147544`), y puertos/clúster cerrados (`port_closed: true`).
- **Instantánea ORM final del recorrido Chrome** ([`orm-final.json`](evidencias/11-browser-20261112T001618451328Z-d9560c03/orm-final.json) · [`result.json`](evidencias/11-browser-20261112T001618451328Z-d9560c03/result.json)):
  - **Cuentas ficticias:** `Admin Audit11` (`ADMIN`), `Lucia Almacen11` (`ALMACENERO`), `Carmen Vendedora11` (`VENDEDOR`).
  - **Turno de caja (`CAJA-01`):** `1` turno en estado **`CLOSED`** (`opening_amount: 100.00`, `expected_amount: 175.65`, `counted_amount: 175.65`, `difference: 0.00`).
  - **Contador y borradores:** `SaleCounter.next_value = 4`; **`4` `SaleDraft` en estado `DISCARDED`** (3 consumidos al confirmar venta y 1 descartado manualmente), conservando **`4` `SaleDraftLine`** asociadas a los 3 borradores cobrados.
  - **3 ventas y 4 líneas confirmadas:**
    - `V-00000001`: `Conserva Centavos Exactos` `3 × 3.55 = 10.65`, `discount = 1.00`, `total = 9.65`, `base = 8.18`, `igv = 1.47`, `cash_received = 9.65`, `change_given = 0.00`, `unit_cost = 1.7500`.
    - `V-00000002`: `Atun FEFO MultiLote` `6 × 4.50` (`unit_cost = 2.0824`) + `ProductoUltraExtensoSinEspacios...160chars` `1 × 12.00` (`unit_cost = 6.0000`) = `39.00`, `discount = 4.00`, `total = 35.00`, `base = 29.66`, `igv = 5.34`, `cash_received = 50.00`, `change_given = 15.00`.
    - `V-00000003`: `Sardina Cambio Precio` (`PRC-01`, actualizada en vivo de `15.50 → 22.00` y renombrada post-venta a `Sardina Nombre Modificado PostVenta 11`, conservando en `SaleLine` el snapshot `15.50` / `"Sardina Cambio Precio"` con `unit_cost = 4.0000`) `2 × 15.50 = 31.00`, `discount = 0.00`, `total = 31.00`, `base = 26.27`, `igv = 4.73`, `cash_received = 35.00`, `change_given = 4.00`.
  - **Stock FEFO en `Atun FEFO MultiLote` (`10` lotes totales en BD):** `FEFO-VENC-PAST` (`5` intactos, `2026-11-09`), `FEFO-VENC-HOY` (`6` intactos, `2026-11-11`), `FEFO-ZERO-EXP` (`0`, `2026-11-12`, agotado antes de la venta), `FEFO-TIE-B` (`2 → 0`, `2026-11-16`), `FEFO-TIE-A` (`3 → 0`, `2026-11-16`) y `FEFO-FAR` (`10 → 9`, `2026-12-11`) ⇒ físico final **`20`**, vigente **`9`**.

---

## 3. Inventario clasificado y matriz entre roles

### 3.1 Pantallas, rutas, formularios, campos, límites y salidas ejecutadas
| Superficie / Recurso | Ruta / Símbolo | Etiqueta, tipo, límites y normalización | Salida, errores y acciones | Estado en este corte |
|---|---|---|---|---|
| Cobro en efectivo | `GET/POST /ventas/cobrar/` ([`sales_checkout`](../../r1-pmv/sales/views.py#L198-L372), [`CheckoutForm`](../../r1-pmv/sales/forms.py#L61-L126), [`sales_checkout.html`](../../r1-pmv/sales/templates/sales/sales_checkout.html#L1-L150)) | `discount_amount`: decimal opcional `0.00..9999999.99`, ASCII estricto sin `+`/`e`/`E`, `-0.00 → 0.00`; `cash_received`: decimal obligatorio `0.01..9999999.99`, `autofocus`, ASCII sin `+`/`e`/`E`; ocultos `idempotency_key`, `expected_subtotal`, `draft_signature` | Banner tributario interno (`sales_checkout.html#L12`); vista previa en centavos `BigInt` (`(total * 100n + 59n) / 118n`, `badInput`, `> 999999999n` → `—`); bloqueo doble envío + reseteo `pageshow`; redirect con alerta si cambia precio o desaparece el borrador; `302` a `/ventas/constancia/<uuid>/`; `no-store` | **CUMPLE** muestra en alcance vigente (`FIX11-01..05`; brecha de tope `DEC-11-TOPE-EFECTIVO-FORM`) |
| Servicio atómico de cobro | [`checkout_sale`](../../r1-pmv/sales/services.py#L302-L543) | Valida actor `VENDEDOR`, UUID idempotencia, decimales `0.00..999999999999.99` (`bool`/no finito/exp `<-2`), turno `OPEN`, borrador `ACTIVE` con líneas, producto/categoría activos, stock vigente, firma de precios, `0 <= discount < subtotal`, `cash_received >= total` | `transaction.atomic()` con orden `Account → CashShift → Sale idempotency → SaleDraft → SaleDraftLine/Product (UUID) → Category (PK) → SaleCounter → Sale/SaleLine → Lot FEFO`; `draft.status = DISCARDED` | **CUMPLE** alcance vigente (`FIX11-01/02/03`; conserva `SaleDraftLine` post-cobro; descuentos sin HU) |
| Constancia interna (enlace y contrato post-cobro) | `GET /ventas/constancia/<uuid:sale_id>/` ([`sales_receipt`](../../r1-pmv/sales/views.py#L375-L399), [`sales_receipt.html`](../../r1-pmv/sales/templates/sales/sales_receipt.html#L1-L100)) | Muestra `correlative`, fecha Lima, vendedor, caja, medio `Efectivo`, `Subtotal`, `- Descuento` condicional, `Base imponible`, `IGV (18%)`, `Total`, `Efectivo recibido`, `Vuelto` y banner `CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO` | `SELLER` limitado a `seller=request.user`; `ADMIN` acceso global; `ALMACENERO` `403`; envoltura sin desborde (`850 == 850`, `docScrollWidth == 1366`); `no-store` | **VERIFICADO** como salida de `checkout_sale` (ciclo completo e historiales → **Etapa 12**) |
| Impacto en cierre de caja | `GET/POST /caja/cerrar/` ([`cash_close`](../../r1-pmv/cash/views.py#L80-L160), [`close_cash_shift`](../../r1-pmv/cash/services.py#L86-L120), [`cash_close.html`](../../r1-pmv/cash/templates/cash/cash_close.html#L1-L72)) | Agrega `Sale.objects.filter(cash_shift=shift).aggregate(Sum("total_amount"))` (neto tras descuento) al esperado | `100.00 + 75.65 = 175.65`, `difference = 0.00`, `no-store`; carrera contra `checkout_sale` serializada en PG (`5d147544`) | **CUMPLE** vínculo cobro→cierre (`ETAPA-09` caja completa sigue aparte) |
| Panel admin y Kardex almacén | `GET /inicio/` ([`_admin_summary`](../../r1-pmv/identity/views.py#L225-L265)), `GET /inventario/stock/`, `GET /inventario/productos/<id>/movimientos/` | `Ventas de hoy = 3`, `Total vendido hoy = S/ 75,65`, `Descuentos otorgados hoy = S/ 5,00`; Kardex lista `SaleLine` `-cantidad` por venta con usuario | Reflejo exacto en `ADMIN` y `ALMACENERO` sin `unit_cost` visible en vistas de vendedor; Kardex sin desglose por lote | **CUMPLE** muestra entre roles (`DEC-11-MODELO-AUDITORIA-VENTAS` abierto) |

### 3.2 Elementos clasificados como `PREVISTO/FUTURO` o asignados a Etapa 12
- **`HU-VEN-02a/CA-01..04`, `HU-VEN-05a`, `HU-VEN-05b`, `HU-CAJA-05`** (gestión/filtros de historiales y reimpresión autónoma de constancias): solo verificados como enlace inmediato post-cobro y control de acceso; pendientes de auditoría integral en **Etapa 12**.
- **`HU-VEN-03`** (`08:602`, comprobante PDF/correo): **`PREVISTO/FUTURO` / `NO EJECUTADO`**, además del conflicto ya trazado en `21:25` y `CONTROL_SPRINTS:89`.
- **`HU-VEN-06a`, `HU-VEN-06b`, `HU-VEN-06c`, `HU-VEN-07`** (`08:620-666`, anulaciones, devoluciones y pagos Yape/Plin/mixtos): **`PREVISTO/FUTURO` (`NO EJECUTADO`)**.

### 3.3 Matriz de efectos entre roles
| Rol / Actor | `/ventas/cobrar/` | `/ventas/constancia/<id>/` | `/ventas/historial/turno/` y `/ventas/historial/` | Efecto transversal comprobado |
|---|---|---|---|---|
| **VENDEDOR (dueño con turno `OPEN`)** | `200` / `302` post-cobro | `200` (solo ventas propias) | `200` turno / `200` propias | Descuenta lotes FEFO, suma neto en caja, habilita `Nueva venta` |
| **VENDEDOR sin turno o desactivado en vuelo** | Redirige a `/ventas/` o falla con `PermissionDenied` en bloqueo `Account` | `200` si ya vendió antes; `403`/login si desactivado | `403`/login si desactivado | Verificado bajo concurrencia real en PG `18.4` (`account_lock_checkout_vs_deactivation`) |
| **ADMINISTRADOR** | **`403`** | `200` en constancias de cualquier vendedor | `403` turno / `200` historial general | Cambia precio en vivo (`15.50 → 22.00`), fuerza alerta de refresco en `/ventas/cobrar/`, lee `Ventas de hoy`, `Total vendido` y `Descuentos otorgados hoy` en `/inicio/` |
| **ALMACENERO** | **`403`** | **`403`** | **`403`** | Registra mermas/entradas que cambian stock vigente; ve stock físico/vigente actualizado y Kardex `-6` en `/inventario/productos/<id>/movimientos/` |
| **Visitante anónimo** | `302` → `/` | `302` → `/` | `302` → `/` | Protegido; `Cache-Control: max-age=0, no-cache, no-store, must-revalidate, private` |

---

## 4. Auditoría bidireccional: planificación ↔ comportamiento

### 4.1 Planificación → Comportamiento
| Requisito / Caso | Criterio verificado | Resultado | Evidencia clave |
|---|---|---|---|
| **`HU-VEN-01c/CA-01..06`** (`08:566-576`) | Total = suma líneas (`CA-01`); insuficiente rechazado (`CA-02`); exacto vuelto `0.00` y excedente vuelto exacto (`CA-03`); advertencia tributaria antes de confirmar (`CA-04`: `sales_checkout.html#L12`); descuento FEFO sin vencer (`CA-05`); actualización atómica de venta, lotes y caja + reversión ante error (`CA-06`) | **CUMPLE** muestra en alcance vigente | `d9560c03`, `dcfe6fbb`, `5d147544` (`CT_ROLLBACK_02_pg`) |
| **`RN-03`, `RN-10`, `RN-19`, `RN-29`, `RN-30`** (`07`) | Bloqueo de lotes con `expiration_date <= hoy Lima`, permiso exclusivo `VENDEDOR` con turno `OPEN`, solo efectivo en R1, `Category.is_active` obligatorio al cobrar, `Product.is_sellable` | **CUMPLE** | `FEFO-VENC-PAST` y `FEFO-VENC-HOY` intactos (`5` y `6`); `CATOFF-01` rechazado |
| **`RN-25`, `RN-26`, `RN-27`, `RN-28`** (`07`, `ST-BASE-02`, `AT-TIME-02`) | Base = `ROUND_HALF_UP(total / 1.18, 2)`, IGV = `total - base` (ej. `9.65 → 8.18 + 1.47`; `35.00 → 29.66 + 5.34`; `31.00 → 26.27 + 4.73`), correlativo único `V-00000001..`, `draft_signature` ante cambio de precio/nombre en vivo, `SaleLine.unit_cost` 4 decimales (`DEC-03AG`), frontera medianoche Lima `04:59:59Z`/`05:00:00Z` | **CUMPLE** | `orm-final.json`, `5d147544` (`lima_midnight_utc_boundary`: `5→0`, `nov11=1, nov12=1`), `test_audit11_checkout.py` |
| **Descuentos en venta (`sales.0003`, `CheckoutForm`, `_admin_summary`)** | Funciona para monto `0 <= d < subtotal` (`total >= 0.01`), descuenta antes de calcular base/IGV y refleja en cierre (`75.65`) y panel (`S/ 5,00`), pero carece de HU, tope porcentual, motivo o autorización | **`EXTRA SIN REQUISITO` / `CONFLICTO DE FUENTES`** | `21_Alcance:25`, `CONTROL_SPRINTS:89`, `DEC-11-DESCUENTOS-ALCANCE` |
| **`CT-CONC-03`, `CT-CONC-04`, `CT-CONC-05`, `CT-ROLLBACK-02`** (`03_Matriz`) | Contención última unidad (baja vs cobro), doble envío idempotente (mismo y distinto payload), carrera cobro vs cierre de caja, reversión atómica completa sin quemar correlativo | **CUMPLE** en **PostgreSQL `18.4`** | `5d147544` (`8/8`), con divergencia frente a `PG 17` (`03_Matriz:168`) |
| **`PT-CHECKOUT-01`** | Latencia bajo carga p95 `<= 500 ms` | **`NO EJECUTADO`** | Excluido de esta auditoría funcional (`→ Etapa 15`) |
| **`MT-COMPAT-01`** | Desktop `1366×900` Chrome (`es-PE`): **CUMPLE** (`0px` overflow); navegación **solo teclado**, móvil `390×844` y lector | **PARCIAL (`NO EJECUTADO` teclado completo y `390×844`)** | `d9560c03` (`layout_metrics`), pendiente `390×844` y teclado integral |

### 4.2 Comportamiento → Planificación (servidor, PostgreSQL 18.4 e integridad)
1. **Concurrencia real en PostgreSQL `18.4` ([`5d147544/pg_report.json`](evidencias/11-pg-20261112T001056379737Z-5d147544/pg_report.json)) — `8/8` comprobados bajo `READ COMMITTED`:**
   - `pg_migrate_clean`: migraciones limpias desde cero en base temporal `PostgreSQL 18.4` (puerto `51046`).
   - `CT_CONC_03_stock_contention`: baja de almacén `B-00000001` (`pid=27188`, `pg_blocking_pids=[6716]`) gana el bloqueo de `Lot` y deja `lot_after=1`; el cobro concurrente revierte con `ValidationError`.
   - `CT_CONC_04a_idempotent_same_payload`: doble POST concurrente con igual `idempotency_key` (`pid=27436`, bloqueado por `31160`): ambos retornan **`V-00000001`** sin duplicar venta ni descontar stock dos veces.
   - `CT_CONC_04b_idempotent_divergent_payload`: reintento concurrente con igual `idempotency_key` pero payload distinto (`pid=21372`, bloqueado por `3576`): primero emite **`V-00000002`** y el segundo falla con **`ValidationError`** gracias a `_verify_idempotent_sale`.
   - `CT_CONC_05_checkout_vs_cash_close`: carrera cobro `8.00` vs cierre de caja (`pid=12128`, bloqueado por `6132`): serializados en `CashShift`, dando `expected=74.00, diff=0.00` exactos.
   - `account_lock_checkout_vs_deactivation`: desactivación concurrente de vendedor bloqueada por `Account` (`pid=1744`, `blockers=[32456]`), provocando **`PermissionDenied`** al confirmar.
   - `CT_ROLLBACK_02_pg`: error simulado dentro de la transacción deja `sales_unchanged: true`, **`SaleCounter` intacto (`4`)**, `lots_intact: [1, 7]` y **`draft_still_active: true`**.
   - `lima_midnight_utc_boundary`: frontera `04:59:59Z` (`23:59:59` del 11/11 Lima) vs `05:00:00Z` (`00:00:00` del 12/11 Lima): stock vigente pasa `5 → 0`, y las ventas del `11/11` y `12/11` quedan separadas (`nov11=1, nov12=1`).
2. **Orden de bloqueos e idempotencia:** `checkout_sale` valida entradas, verifica idempotencia temprana fuera de lock (`L328-337`) y dentro de `transaction.atomic()` adquiere `Account` → `CashShift` → re-verifica idempotencia (`Sale`) → `SaleDraft` → `SaleDraftLine`/`Product` (orden UUID) → `Category` (orden PK) → `SaleCounter` → `Sale`/`SaleLine` → `Lot` FEFO (`expiration_date, received_at, id`). En capa web, la ruta hermana de Etapa 12 ([`sales/views.py#L205-L275`](../../r1-pmv/sales/views.py#L205-L275)) intercepta el reintento POST incluso cuando el borrador ya pasó a `DISCARDED`.
3. **Asimetría de tope entre `CheckoutForm` (`9,999,999.99`) y `checkout_sale` (`999,999,999,999.99`):** `CheckoutForm` y el JS de `sales_checkout.html` (`> 999999999n` centavos) limitan efectivo y descuento a `S/ 9,999,999.99` (alineado con `MAX_CASH_AMOUNT` de `cash/services.py`), mientras `Sale` (`max_digits=14`) y `checkout_sale` (`MAX_SALE_MONEY`) aceptan hasta `999,999,999,999.99`. En [`repro.json#L172-L180`](evidencias/11-repro-20261111T235301278519Z/repro.json#L172-L180) se reprodujo un borrador con subtotal `19,999,999.98` que sí acepta `checkout_sale`, pero no puede cobrarse desde el formulario web (`DEC-11-TOPE-EFECTIVO-FORM`).
4. **Retención de `SaleDraftLine` tras cobro:** A diferencia de `discard_active_draft`, `checkout_sale` marca `draft.status = DISCARDED` (`L539-L541`) sin borrar sus `SaleDraftLine` (`4` líneas retenidas en los `3` borradores cobrados de `orm-final.json`). No rompe `one_active_sale_draft_per_shift`, pero mantiene datos redundantes respecto a `SaleLine`.
5. **Kardex sin tabla `sale_lot_allocation`:** En `/inventario/productos/<id>/movimientos/`, el Almacenero ve `-6` para `V-00000002` en una sola fila de `SaleLine` sin detalle de los lotes consumidos (`FEFO-TIE-B`, `FEFO-TIE-A`, `FEFO-FAR`), coherente con `DEC-11-MODELO-AUDITORIA-VENTAS`.
6. **Cabeceras y layout:** `Checkout`, `receipt`, `shift_history` y `history` devuelven `Cache-Control: max-age=0, no-cache, no-store, must-revalidate, private`, `docScrollWidth == 1366` y `0` errores JS/consola.

---

## 5. Defectos reproducidos, correcciones aplicadas y suites externas

### 5.1 Reproducción previa a correcciones ([`evidencias/11-repro-20261111T235301278519Z/repro.json`](evidencias/11-repro-20261111T235301278519Z/repro.json#L1-L482))
Antes de aplicar `FIX11-*` se reprodujeron y documentaron:
- Aceptación de tipos/exponentes inválidos en `checkout_sale` (`bool`, exponentes `< -2`, infinitos) y omisión de verificación completa de payload en reintento idempotente (solo chequeaba igualdad sin validar `seller_id`/`draft_id`/`cash_received`/`discount_amount`/subtotal esperado de forma integral).
- Falta de bloqueo `select_for_update()` sobre `Account` en `checkout_sale` frente a desactivación concurrente.
- En `CheckoutForm`, aceptación de dígitos Unicode no ASCII, signo `+` inicial y notación científica `e`/`E`, además de cálculo visual erróneo de descuento tras error de POST en `sales_checkout`.
- Desaparición silenciosa o `500`/estado inconsistente en `sales_checkout` si el borrador se descartaba en otra pestaña antes del POST, y ausencia de `@never_cache` en todas las vistas de cierre/constancias/cobro revisadas.
- Reproducción visual previa de constancia (`pre-fix-receipt.png`, ver §7.4): carecía del rótulo literal `CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO`, omitía la fila `Subtotal` pese a `- S/ 2,00` de descuento, omitía `Medio de pago`/`Ventas del turno` y desbordaba un nombre de 160 caracteres sin espacios fuera del borde derecho de la tarjeta.

### 5.2 Correcciones aplicadas en Etapa 11 (`FIX11-01..06`) vs aportes hermanos
- **`FIX11-01` ([`sales/services.py#L52-L96`](../../r1-pmv/sales/services.py#L52-L96)):** Endurecimiento en servicio mediante `_validate_money_decimal` (rechaza `bool`, no `Decimal`, `NaN`/`Infinity`, `< 0`, escala `< -2`, `> MAX_SALE_MONEY`), `_verify_idempotent_sale` (valida `seller_id`, `draft_id`, `cash_received`, `discount_amount` y `(total_amount + discount_amount) == expected_subtotal`) y `_lock_seller_actor` (bloquea `identity_account` sin `JOIN` sobre `Role`).
- **`FIX11-02` ([`sales/forms.py#L100-L126`](../../r1-pmv/sales/forms.py#L100-L126)):** `clean_cash_received` y `clean_discount_amount` rechazan valores no ASCII, `+` inicial o notación `e`/`E`, redondean a `0.01` y normalizan `-0.00 → 0.00`.
- **`FIX11-03` ([`sales/views.py#L277-L280,L326-L360`](../../r1-pmv/sales/views.py#L277-L360)):** Redirección controlada (*«No tienes una venta en preparación.»*) cuando el borrador desaparece entre pantallas y recálculo exacto de `applied_discount` al re-renderizar errores de formulario en `sales_checkout`.
- **`FIX11-04` (`@never_cache` en vistas críticas):** Garantía `Cache-Control: no-store` verificada en `sales_checkout`, `sales_receipt`, `sales_shift_history`, `sales_history` y `cash_close`.
- **`FIX11-05` ([`sales_checkout.html#L90-L146`](../../r1-pmv/sales/templates/sales/sales_checkout.html#L90-L146)):** Reescritura JS en centavos `BigInt` (`(total * 100n + 59n) / 118n`), manejo de `badInput`, `—` ante desborde `> 999999999n`, bloqueo de doble envío y reseteo en evento `pageshow`.
- **`FIX11-06` ([`sales/test_audit11_checkout.py#L1-L551`](../../r1-pmv/sales/test_audit11_checkout.py#L1-L551)):** `10` pruebas unitarias y de integración cubriendo exactitud, descuentos, idempotencia, FEFO/vencidos, cambio de precio/stock, rollback ante error y permisos entre roles.
- **Separación explícita:** [`sales/views.py#L205-L275`](../../r1-pmv/sales/views.py#L205-L275), [`sales_receipt.html#L1-L100`](../../r1-pmv/sales/templates/sales/sales_receipt.html#L1-L100) y [`app.css#L2332-L2525`](../../r1-pmv/identity/static/identity/app.css#L2332-L2525) pertenecen al alcance hermano de **Etapa 12**; y [`inventory/test_audit07_stock_expirations.py#L491`](../../r1-pmv/inventory/test_audit07_stock_expirations.py#L491) (`AssertionError: 2 != 0`) se dejó intacto por estar fuera de alcance.

---

## 6. Decisiones abiertas y propuestas trazables

### 6.1 Decisiones abiertas (sin imposición silenciosa)
1. **`DEC-11-DESCUENTOS-ALCANCE` — ¿Qué política formal rige los descuentos en venta (`EXTRA SIN REQUISITO`)?**
   - **Alternativa A:** Mantener el descuento discrecional actual por `VENDEDOR` (`0 <= d < subtotal`, `total >= 0.01`), incorporando una HU y RN retrospectivas que lo formalicen.
   - **Alternativa B (Recomendada para negocio):** Formalizar `HU` y `RN` con tope porcentual/monto máximo para `VENDEDOR` y exigencia de motivo obligatorio o autorización/credencial de `ADMIN` sobre el umbral.
   - **Alternativa C:** Retirar el campo en R1 PMV hasta la aprobación explícita de un requisito en backlog.
2. **`DEC-11-MODELO-AUDITORIA-VENTAS` — ¿Basta el modelo físico vigente frente a las 5 entidades lógicas de `02_Diseno_Tecnico`?**
   - **Alternativa A:** Documentar en `02_Diseno_Tecnico` que R1 PMV usa `Sale.idempotency_key`, rebaja directa en `Lot`, `SaleLine` y `StockWriteOff`/`StockLoad`/`PhysicalAdjustment` sin tablas adicionales.
   - **Alternativa B:** Incorporar modelos físicos `SaleLotAllocation`, `IdempotencyRecord` (para registrar rechazos/errores pre-commit) y `AuditEvent` antes de cerrar R1.
3. **`DEC-11-TOPE-EFECTIVO-FORM` — Asimetría `9,999,999.99` (`CheckoutForm`/JS/`cash`) vs `999,999,999,999.99` (`Sale`/`checkout_sale`):**
   - **Alternativa A:** Alinear `MAX_SALE_MONEY` / validación de servicio en `9,999,999.99` para prohibir borradores que luego no pueden cobrarse por UI web.
   - **Alternativa B:** Elevar `CheckoutForm`, la guarda JS `BigInt` y `MAX_CASH_AMOUNT` en `cash/services.py` al límite de 14 dígitos del modelo si se esperan operaciones mayores.

### 6.2 Propuestas trazables de documentación y backlog
- **`PROP-11-HU-DESC-01` (`08_Historias_de_Usuario.md` / `09_Product_Backlog.md`):** Crear historia específica de descuento en venta (asignando ID validado distinto de `HU-VEN-03`) si se elige Alternativa A o B de `DEC-11-DESCUENTOS-ALCANCE`.
- **`PROP-11-RN-DESC-01` (`07_Reglas_de_Negocio.md`):** Definir `RN` de descuento (tope máximo, redondeo, prohibición de `total <= 0`, visibilidad en constancia/cierre/panel y si requiere motivo o aprobación).
- **`PROP-11-TRAZA-LOTES-01` (`02_Diseno_Tecnico_R1_PMV.md` / `inventory`):** Definir si `product_movements` debe desglosar los lotes consumidos en cada `SaleLine` mediante `SaleLotAllocation`.
- **`PROP-11-CHECKOUT-MAX-01` (`sales/forms.py`, `sales/services.py`, `cash/services.py`):** Sincronizar tope monetario único entre borrador, cobro UI, servicio y cierre de caja según `DEC-11-TOPE-EFECTIVO-FORM`.
- **`PROP-11-05` (`r1-pmv/sales/services.py`, `tests`):** Decidir si `checkout_sale` debe depurar o archivar `SaleDraftLine` al pasar `SaleDraft` a `DISCARDED` (hoy quedan retenidas), añadiendo prueba de regresión si se modifica.

---

## 7. Evidencia reproducible y resultados de pruebas

### 7.1 Corridas finales limpias, separadas y verificación del árbol
| Corrida / Artefacto | Alcance exacto | Resultado | Marca UTC / Notas |
|---|---|---|---|
| [`11-checks-20261112T001835926218Z-f692635d/summary.json`](evidencias/11-checks-20261112T001835926218Z-f692635d/summary.json) | `manage.py check` + `makemigrations --check --dry-run` | **`0` (`OK`)** | `19:18:37` Lima (posterior a `app.css` `19:14:54`); `protected_unchanged: true` |
| [`11-tests-20261112T001359087847Z-dcfe6fbb/summary.json`](evidencias/11-tests-20261112T001359087847Z-dcfe6fbb/summary.json) | `sales.tests`, `test_audit03ag_cost`, `test_audit03r_review`, `test_audit03s_review`, `test_audit11_checkout`, `cash.tests` | **`78/78 OK`** (`7.325s`) | `19:14:07` Lima (inmediatamente anterior a CSS de Etapa 12 en `app.css#L2332-L2525`) |
| [`11-tests-20261112T001433013380Z-61c6bec0/summary.json`](evidencias/11-tests-20261112T001433013380Z-61c6bec0/summary.json) | `catalog`, `identity`, `app_platform`, `inventory` (incl. `test_audit04..06`, `08`, `test_lot_receipt_time`, `test_receipt_*`) | **`325/325 OK`** (`45.201s`) | **`403/403` limpias combinadas** (`19:15:19` Lima) |
| [`11-browser-20261112T001618451328Z-d9560c03/browser.json`](evidencias/11-browser-20261112T001618451328Z-d9560c03/browser.json) | Chrome `157.0.8103.78`, `1366×900`, `es-PE`, flujos de `VENDEDOR`, `ADMIN`, `ALMACENERO`, anónimo + layout + cache headers | **`59` func. + `cero_page_errors` (`60` ítems) + `8` PNG post-fix** | `19:16:43` Lima (posterior a `19:14:54`); `docScrollWidth: 1366`, `page_errors: []`, `port_closed: true` |
| [`11-pg-20261112T001056379737Z-5d147544/pg_report.json`](evidencias/11-pg-20261112T001056379737Z-5d147544/pg_report.json) | `PostgreSQL 18.4`, `READ COMMITTED`, puerto `51046` | **`8/8 OK`** | `19:11:05` Lima; `pg_blocking_pids`, doble POST, rollback, desactivación y medianoche Lima |
| [`11-tests-20261112T001658671691Z-88b915e1/summary.json`](evidencias/11-tests-20261112T001658671691Z-88b915e1/summary.json) | **Separada (Etapa 12):** `sales.test_audit12_receipts_history` | **`5/5 OK`** (`1.268s`) | No sumada a `403/403` (`19:17:01` Lima) |
| [`11-tests-20261112T001701839181Z-54251f2e/summary.json`](evidencias/11-tests-20261112T001701839181Z-54251f2e/summary.json) | **Separada (suites externas):** `sales.test_audit10_draft`, `cash.test_audit09_cash`, `inventory.test_audit03aj_session`, `inventory.test_audit07_stock_expirations` | **`25 OK + 1 FAIL`** (`2.942s`) | No sumada a `403/403`; único fallo externo en [`test_audit07_stock_expirations.py#L491`](../../r1-pmv/inventory/test_audit07_stock_expirations.py#L491) (`2 != 0`) |

### 7.2 Artefactos históricos previos de la sesión (`11-*`, NO aditivos)
Se conservan en `auditoria_por_etapas/resultados/evidencias/` los registros previos de reproducción e iteración (no se suman ni sustituyen a §7.1):
- **Reproducciones (`11-repro-*`):** `20261111T234913244085Z`, `234936437471Z`, `234955143331Z`, `235011088300Z`, `235029874196Z`, `235242740207Z`, y [`11-repro-20261111T235301278519Z/repro.json`](evidencias/11-repro-20261111T235301278519Z/repro.json).
- **Checks intermedios:** `9cf20fd5`, `5bc22090`, `a080a650`.
- **Pruebas intermedias:** `be2e1788`, `8fd5bf81`, `b9d5b4cb`, `6bfb45c2`, `a6d6d7a4`, `2476add5`, `6c533487`.
- **Navegador y PG previos:** `bf9b4851`, `53308b51`, `d1c106ab` (Chrome); `60836881`, `c378f6e2` (PostgreSQL).

### 7.3 Comandos reproducibles
- Runner general y pruebas/navegador: [`auditoria_por_etapas/resultados/soporte/audit11_run.py`](soporte/audit11_run.py) con configuración [`audit11_settings.py`](soporte/audit11_settings.py).
- Concurrencia real PostgreSQL `18.4`: [`auditoria_por_etapas/resultados/soporte/audit11_pg.py`](soporte/audit11_pg.py).

### 7.4 Capturas inspeccionadas directamente (`1` pre-fix + `8` post-fix)
| Captura | Contexto y verificación visual directa en los píxeles renderizados |
|---|---|
| [`pre-fix-receipt.png`](evidencias/11-repro-20261111T235301278519Z/pre-fix-receipt.png) | Pre-fix: muestra `AVISO:` genérico sin `CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO`, omite fila `Subtotal` pese a `- S/ 2,00`, omite `Medio de pago`/`Ventas del turno` y desborda el nombre continuo de 160 caracteres fuera del borde derecho de la tarjeta |
| [`post-fix-checkout.png`](evidencias/11-browser-20261112T001618451328Z-d9560c03/post-fix-checkout.png) | `Carmen Vendedora11` (`Vendedor`) en `/ventas/cobrar/`: aviso azul de constancia interna no SUNAT, `Atun FEFO MultiLote` (`6 × S/ 4,50 = S/ 27,00`) + producto de 160 caracteres envuelto en 2 líneas sin desborde (`Subtotal S/ 39,00`), `Descuento S/ 4,00`, `Efectivo recibido S/ 50,00`, resumen `Total S/ 35,00 / Base S/ 29,66 / IGV S/ 5,34 / Vuelto S/ 15,00` y error controlado previo mostrado sin pérdida de diseño |
| [`post-fix-receipt-tax.png`](evidencias/11-browser-20261112T001618451328Z-d9560c03/post-fix-receipt-tax.png) | `V-00000001` (`Conserva Centavos Exactos`, `3 × S/ 3,55 = S/ 10,65`, `- S/ 1,00` descuento, `Base S/ 8,18`, `IGV S/ 1,47`, `Total S/ 9,65`, `Efectivo S/ 9,65`, `Vuelto S/ 0,00`), banner `CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO` y botón `Nueva venta` |
| [`post-fix-receipt.png`](evidencias/11-browser-20261112T001618451328Z-d9560c03/post-fix-receipt.png) | `V-00000002`: tabla completa con nombre de 160 caracteres envuelto dentro de la celda sin desbordar, `Subtotal S/ 39,00`, `Descuento - S/ 4,00`, `Base S/ 29,66`, `IGV S/ 5,34`, `Total S/ 35,00`, `Efectivo S/ 50,00`, `Vuelto S/ 15,00` y banners de control interno |
| [`post-fix-shift-history.png`](evidencias/11-browser-20261112T001618451328Z-d9560c03/post-fix-shift-history.png) | `Mis ventas del turno` (`Carmen Vendedora11`): muestra `3` ventas del turno (`V-00000003` `S/ 31,00`, `V-00000002` `S/ 35,00`, `V-00000001` `S/ 9,65`) y botón `Ver constancia` sin recorte |
| [`post-fix-cash-close.png`](evidencias/11-browser-20261112T001618451328Z-d9560c03/post-fix-cash-close.png) | `Cerrar turno` (`CAJA-01`, `Carmen Vendedora11`): `Monto inicial S/ 100,00`, `Total cobrado S/ 75,65`, `Monto esperado S/ 175,65`, `Monto contado S/ 175,65`, `Diferencia Exacto S/ 0,00` |
| [`post-fix-admin-dashboard.png`](evidencias/11-browser-20261112T001618451328Z-d9560c03/post-fix-admin-dashboard.png) | `Panel principal` (`Admin Audit11`): `Ventas de hoy 3`, `Total vendido hoy S/ 75,65`, `Descuentos otorgados hoy S/ 5,00`, `Turnos de caja abiertos 0`, `Lotes por vencer (30 días) 5`, `Lotes vencidos con stock 2` |
| [`post-fix-warehouse-stock.png`](evidencias/11-browser-20261112T001618451328Z-d9560c03/post-fix-warehouse-stock.png) | `Inventario actual` (`Lucia Almacen11`): banners rojos conservando intactos `FEFO-VENC-PAST` (`5 unid.`) y `FEFO-VENC-HOY` (`6 unid.`), alerta ámbar con el producto largo envuelto y tabla reflejando `Atun FEFO MultiLote` con `20` físico / `9` vigente |
| [`post-fix-kardex.png`](evidencias/11-browser-20261112T001618451328Z-d9560c03/post-fix-kardex.png) | `Movimientos: Atun FEFO MultiLote` (`Lucia Almacen11`): cabecera `STOCK FÍSICO ACTUAL: 20 UNID. · STOCK VIGENTE: 9 UNID.` y fila superior `▼ Venta \| Venta V-00000002 \| -6 \| Carmen Vendedora11` sobre entradas previas |

---

## 8. Pendientes, límites y cursor exacto

- **No ejecutado en esta etapa:**
  - `PT-CHECKOUT-01` (rendimiento `<= 500 ms` p95 bajo carga → **Etapa 15**).
  - `MT-COMPAT-01` en recorrido **solo teclado** completo, viewport móvil `390×844` y lector de pantalla.
  - Caída física abrupta del proceso (`SIGKILL`) en mitad de `checkout_sale`.
  - Ejecución directa en **`PostgreSQL 17`** (`03_Matriz:168`; validado en `18.4`).
  - Despliegue de migraciones pendientes en la base operativa `r1_pmv.sqlite3` (intacta por protocolo).
  - Resolución del fallo preexistente [`inventory/test_audit07_stock_expirations.py#L491`](../../r1-pmv/inventory/test_audit07_stock_expirations.py#L491) (`2 != 0`).
  - Ciclo completo de constancias, reimpresión, vendedor ajeno e historiales (`HU-VEN-02a`, `HU-VEN-05a/05b`, `HU-CAJA-05` → **Etapa 12**) y auditoría de apertura/cierre de caja como módulo (**`ETAPA-09`**, aún `NO EJECUTADO`).
- **Siguiente cursor exacto:** **`ETAPA-12 / HU-VEN-02a/CA-01`** *(conservando `ETAPA-09 / HU-CAJA-01/CA-01` pendiente `NO EJECUTADO` en [`ESTADO_GENERAL.md`](ESTADO_GENERAL.md), además de las decisiones abiertas `DEC-11-DESCUENTOS-ALCANCE`, `DEC-11-MODELO-AUDITORIA-VENTAS`, `DEC-11-TOPE-EFECTIVO-FORM` y las herencias de etapas previas)*.
