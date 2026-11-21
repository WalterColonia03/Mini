# 2. Diseño técnico vigente y brechas de implementación

**Antecedente del 15/11.** [Primera revisión del puente Android](auditoria_por_etapas/resultados/REVISION-PROPUESTA-GEMINI-PAGOS.md). El brief posterior fija la dirección por capas y conserva el ensayo como condición para habilitar dinero real.


**Objetivo vigente · 20/11/2026.** Demostrar el minimarket por HTTPS público con efectivo, digital y mixto, QR estático de una cuenta Yape propia y cero comisión de cobro. El cajero atiende sin el dueño en el flujo ordinario. La dirección por capas está aceptada; el puente Android y la asociación al pedido requieren ensayo. Para devoluciones quedan por decidir canal financiado, permisos y límites. [Contrato funcional](08_Historias_de_Usuario.md#contrato-CT-ENTREGA-ACADEMICA) · [Diseño y ensayo](auditoria_por_etapas/PAGOS_YAPE_Y_MIXTOS.md).

## Diseño de pagos para refinar e implementar

En el borrador sin aportes, la ficha comercial conserva el precio vigente y la línea conserva el precio revisado por el vendedor. Una consulta puede mostrar ambos. El primer intento sobre un precio vencido actualiza la línea y pide revisar. La confirmación posterior crea la instantánea de venta y la asignación al lote. La constancia lee esa instantánea. Para un aporte anterior al cambio, el modelo propuesto de pedido durable debe recuperar su versión o la obligación por el importe recibido. [Caso de precio de 03](auditoria_por_etapas/resultados/ETAPA-03.md#precio-03-publico).

La aplicación actual registra efectivo. Propuesta trazada aHU-VEN-07/10: separar intento de pago, abono recibido, aplicación a venta y reintegro; cada hecho tiene importe,estado,origen,actor,referencia e idempotencia. No basta agregar medio=MIXTO aSale. Restricciones enBD y transacciones deben proteger referencias y saldos; un abono externo no se deshace con rollbackDjango. Conservar abonos sin aplicar ante cancelación/error y recuperar estado tras timeout.

El QR estático identifica al receptor. Cada sesión de cobro nace en un pedido durable antes de pagar. Propuesta de diseño: registrar observación receptora, crédito, aplicación al pedido/venta y, en su caso, obligación, reserva y desembolso como hechos distintos. Un desafío completado por el pagador es una señal de asociación. Si el mismo conjunto de señales admite dos asignaciones, conservar en revisión. El identificador de entrega y el código corto no identifican de forma universal la transferencia. Probar reintento y unicidad entre turnos, sin llamadas externas dentro de una transacción de BD.

Conservar el efectivo entregado, el vuelto y el neto aplicado por aporte. La aplicación o reserva agota capacidad por origen solo una vez. Una cancelación preserva los abonos recibidos, incluso antes de existir Sale. Recuperar el mismo pedido tras el fallo de confirmación. Contrastar con el descarte de SaleDraft, el rechazo del cierre con borrador activo y el cálculo de efectivo en los servicios de ventas y caja; diseñar conservación de casos pendientes sin impedir el siguiente cobro. Restringir configuración del QR a ADMIN y datos visibles del receptor. Revisar viabilidad del puente conforme a términos, custodia y evidencia del titular.

Reintegro sin nuevoYape requiere política de medio y permisos; no mover fondos digitales a gaveta automáticamente. Migrar ventas antiguas como efectivo conocido, sin inventar abonos. Ensayar migración/reversión en copia. Para publicar: Django,estáticos,BDdurable,HTTPS y autenticación; proveedor se evalúa en15 sin compra inferida. Medir servidor y espera externa por separado; p95<=2s es propuesta a contrastar, no SLA verificado.

**Antecedentes inferiores:** conservan fecha/build y alcance anterior; no sustituyen el objetivo ni estado de este corte.

## Diseño de ingreso vigente 01-K

`LoginForm` valida correo de hasta 254 caracteres, con mensaje inclusivo preciso; `Account.normalize_email` aplica `strip().casefold()`. `LoginAttempt` conserva el contador compartido y plazo de RN-17 en base; `authenticate_active_account` serializa su actualización y crea sesión solo si procede. `/admin/` permanece fuera de rutas. Se retiran diagnósticos y configuraciones de tráfico añadidos en 01-J. No hay migración nueva. Los errores de campos, rechazo, bloqueo y 403/404 se especifican literalmente en HU-AUTH-01/02 de08. La semántica del tablero y de los destinos sigue en sus módulos.

## Revalidación Etapa 07 (`07-B` · 14/11/2026 Lima · stock, vencimientos y volumen `PT-SEARCH-01`)

Sin modificaciones al producto (`r1-pmv` `f0d6fa81...` / `c7bfe1fa...` sin cambios en `catalog/`, `inventory/`, `sales/` ni `identity/views.py`): `_dashboard_summary` mantiene instantánea única (`SELECT ... CROSS JOIN ...`) con corte `America/Lima` y `stock_overview`/`product_expirations` emiten `@never_cache` (`max-age=0, no-cache, no-store, must-revalidate, private`), `O(1)` sentencias (`7` y `4`) y rechazo ASCII estricto (`1..3650`, `\x00` seguro). Queda reproducido el incumplimiento de `DEC-07-VENCIDOS-FILTRO` y `HU-PROD-06/CA-03` porque `/productos/vencimientos/` renderiza una sola tabla mezclada sin separar «Próximos a vencer» (`hoy < fecha <= hoy+D`) de «Vencidos» (`fecha <= hoy`). El ensayo `PT-SEARCH-01` en PostgreSQL `18.4` (`2,001` productos / `20,002` filas `inventory_lot`, `8,288 kB`) demuestra que un índice parcial experimental (`idx_lot_exp_avail_gt0 ON inventory_lot (expiration_date, received_at, id) WHERE available_quantity > 0`, `648 kB`) transforma escaneos a `Bitmap Index Scan` / `Index Only Scan` (`30–120 ms` SQL total), pero el `95 %+` de la latencia HTTP (`3,56–3,63 s` mediana y `2,0–4,4 MB` HTML) deriva de tablas sin paginar e hidratación Python de `20,002` `Lot` vía `prefetch_related("lots")`; por ello `PROP-07-IDX-01` y `PROP-07-ESCALA-PAGINACION-01` permanecen como **`PROPUESTA`** antes de cualquier migración. [Informe 07-B](auditoria_por_etapas/resultados/ETAPA-07.md#reval-07-b-20261114) · [Disposiciones 07-B](auditoria_por_etapas/resultados/soporte/07-B-inventario-y-disposiciones.md).

## Corte vigente14-CIERRE · 14/11/2026 Lima

PhysicalAdjustment guarda UUID/huella y fotografías; Lot.adjustment_origin identifica lote encontrado y Kardex suma el ajuste una sola vez. Mismo actor/clave/contenido recupera registro; legado nullable no se rellena. Actor→producto→lote se bloquean antes de efectos. Q0 exige costo/fuente y Q>0 conserva promedio. Detalle GET ADMIN/ALM; soloADMIN confirma. Dinero separa tope de operación9,999,999.99 y acumulado14,2; capacidad se valida bajo bloqueo del turno antes de venta. cash0004/sales0007 diagnostican datos antes de checks. No migración operativa. Véanse soporte de ajustes y dinero para campos, alternativas e impactos.

[Informe y evidencia](auditoria_por_etapas/resultados/ETAPA-14.md#cierre-14) · [Ajustes](auditoria_por_etapas/resultados/soporte/14-CIERRE-ajustes.md) · [Dinero](auditoria_por_etapas/resultados/soporte/14-CIERRE-dinero.md). Las secciones fechadas anteriores se conservan como antecedentes.

## Revalidación puntual Etapa 06 · 14/11/2026 Lima

Sin cambios al código ni migraciones en esta sesión: revalidación sobre build estabilizado `4d1c9637...` (`inventory/` sin cambios desde `10:24`) para `HU-INV-01b`, `DOC-03AB/03AH/03AI-01` y `DEC-05-LOTE-ESPACIOS` con `583/583` pruebas Django ejecutadas (`82/82` núcleo `inventory`, `4/4` `test_audit03aj_session`, `497/497` resto incl. `identity`), `11/11` servidor, `10/10` casos PostgreSQL `18.4` (bloqueo `catalog_product`, carrera entrada↔cobro↔merma↔ajuste, triggers `23514` y rollback pos-escritura con `bulk_create`) y Chrome escritorio/móvil (`93/93`, observando desbordamiento horizontal de lote `64` chars en `stock_receipt.html` tanto en `1366×900` como en `390×844`, recorte de cabecera móvil, `<h1>` `"Minimarket"` en `stock-receipt` y anclaje `min_num=1` en tarjeta 1; la compresión vertical `<dd>` de `"S/ 3,12"` vista en una corrida previa quedó resuelta tras ajuste concurrente en `app.css`). [Adenda ETAPA-06](auditoria_por_etapas/resultados/ETAPA-06.md#adenda-06-20261114). `PG 17`, `SIGKILL` y base operativa siguen en Etapa `15`.


## Sublote 02-E · 14/11/2026 Lima · segunda pasada acotada (`H02E-01..04`)

En `identity/`, `H02E-02..04` implementan confirmación explícita de estado (`GET /empleados/<uuid:account_id>/estado/confirmar/`, `employee-state-confirm`, `employee_state_confirm.html` y apilamiento móvil `.summary-list` en `app.css`), preservación de bloqueo `LoginAttempt` en reactivación y cambio de correo (`_migrate_or_preserve_login_attempt`), purga de sesiones en BD tras reset administrativo de contraseña (`_delete_account_sessions`), desbloqueo explícito `unlock_account` en `EmployeeEditForm`/`employee_edit.html`, y auditoría transaccional/sanitizada con `IdentityAuditEvent` (migración aditiva `identity.0006`), `RequestIdMiddleware` y `identity.audit` (`persist_db=False` en rechazos HTTP; `"sessions_revoked": true` sin falso redactado). Revalidado `H02E-01` en `/salir/` con `652/652` servidor (`SQLite :memory:`), Chrome `1366×768` + `390×844` y `5/5` PostgreSQL `18.4` (`FOR NO KEY UPDATE` / `FOR UPDATE` en `open_cash_shift` vs `update_employee`, `last_admin_race`, `duplicate_email_race` y rollback atómico de borrador/auditoría); `r1_pmv.sqlite3` intacta. `HU-AUTH-04a/04b/05`, `HU-USR-06` y `HU-LOG-01` (`W`) continúan sin rutas ni UI; `DOC-01-06/C-02` permanece `PARCIAL` global por `/admin/login/`, retención `SEC-15-RETENCION-01` y sumidero `SEC-15-OBS-01`. [Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e) · [Disposiciones](auditoria_por_etapas/resultados/soporte/02-E-disposiciones.md).


## Sublote 01-F · 14/11/2026 Lima · revalidación primera pasada (build `2cef34b5...`)

Sin cambios de código por Etapa 01 en este sublote: sobre el build concurrente `2cef34b5...` (`128/128` `identity + audit01e_probes`, `83/83` núcleo Etapa 01, `25/25` Chrome `157.0.8103.78`, `5/5` PostgreSQL `18.4`, `7/7` HTTP socket, `5/5` sondas técnicas), se revalida `CP-HU-AUTH-01-002` y `CP-HU-AUTH-02-001` y se comprueba el estado de `DOC-01-06`: `C-03` cumple en sonda aislada (`RedactSensitiveDataFilter` redácta `exc_info` y `BrokenHandler` falla cerrado), `C-02` queda PARCIAL (`IdentityAuditEvent` + `X-Request-ID` en `/` y `/salir/` con salida a consola sin sumidero durable ni eventos en `/admin/login/`) y `C-01` incumple (`/admin/login/` elude el bloqueo de 15 min de `/` para `staff`/`superuser` e inicia sesión compartida sin clave `role_code`, aceptada en `/inicio/`). `authenticate_active_account` sigue ejecutando Argon2 (`check_password`/`set_password`) antes de comprobar `locked_until > now` (`DOC-01-04`), no existe limitación de tráfico en `/` (`HTTP-07`, `6/6` `200` con `X-Forwarded-For` rotado), y con `DEBUG=False` el servicio WSGI de desarrollo requiere `StaticFilesHandler` porque el proyecto no declara `WhiteNoise` ni `collectstatic` en `Dockerfile`. [Adenda ETAPA-01](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-f) · [Disposiciones](auditoria_por_etapas/resultados/soporte/01-F-inventario-y-disposiciones.md).


## Segunda pasada Etapa 12 (12-B · 14/11/2026 Lima)

En alcance estricto de constancias e historiales (`DEC-12-PERMISOS-HISTORIAL-Y-MENU` y `DEC-12-ORDEN-LINEAS-RECIBO`): `CashShift.Meta.ordering = ["-opened_at", "-id"]` y `CashShiftClose` resuelven empates temporales sin migrar filas previas; `sales_history` y `cash_shift_history` paginan a `25` por página preservando filtros validados y conservando el resumen agregado sobre todo el conjunto filtrado (`Paginator`, guardas `> 0`, no numérico, duplicados, `\x00` y fechas inválidas con `HTTP 200`); `sales_checkout` detecta cambios concurrentes de `product.sale_price` entre el `GET` y el `POST` de cobro, actualiza subtotales del borrador y exige confirmación explícita (`DEC-12/C-04`); `base.html` incorpora «Mi historial de ventas» y «Mi historial de turnos» para `VENDEDOR` y `<h1>` «Acta de cierre» en `/caja/turnos/<id>/cerrado/`; y `app.css` ajusta `.receipt-table { min-width: 560px }` bajo `@media (max-width: 720px)` manteniendo `@media print` intacto. La suite Stage 12 (`85/85`), Chrome escritorio/móvil/print (`12/12`, `0` errores) y PostgreSQL `18.4` (`4→4`, `7→7`, `EXPLAIN JSON`, `[302, 302]` concurrente = `1` venta, `26` empatados) acreditan el tramo aislado; migraciones `cash 0004..0005` y `sales 0007..0008` siguen sin aplicarse en `r1-pmv/r1_pmv.sqlite3` (`c60b4027...`), y `PG 17`, impresora térmica física y `SIGKILL` conservan alcance de Etapa `15`. [Informe 12-B](auditoria_por_etapas/resultados/ETAPA-12.md#vigente-12-b).


> **Fuente funcional principal:** [08 · planificación unificada](08_Historias_de_Usuario.md). Las fichas, RN y contratos de08 definen lo esperado; este documento conserva su papel de contexto, diseño, ejecución o evidencia. Las vistas07/09/03 se derivan de08.


> **Vigente: 12/11/2026 · conciliación documental autorizada.** Requisito aceptado no equivale a implementación o verificación. [Mapa y decisiones](auditoria_por_etapas/resultados/conciliacion_20261112/CONSOLIDACION.md) · [Encargos verificables](auditoria_por_etapas/resultados/conciliacion_20261112/ENCARGOS.md) · [Versión anterior íntegra](auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/02_Diseno_Tecnico_R1_PMV.md). Jira no forma parte de este seguimiento.

## 2.1 Arquitectura y alcance

Monolito modular Django5.2/Python3.12, plantillas y servicios transaccionales, una caja física, tres roles exclusivos. PostgreSQL17 sigue motor objetivo; la suite actual usa SQLite aislado y existen muestrasPG18.4, sin equivalencia automática de concurrencia/versión. No se cambian dependencias, infraestructura ni bases en esta conciliación.

Alcance vigente33 HU seleccionadas en08, incluidos sus contratos;09 es la vista de backlog. Lo especificado aquí es diseño requerido, no inventario de tablas ya implementadas. Las simulaciones de seis Developers y fechas/216h/67tareas quedaron en BASELINE y no acreditan equipo, capacidad o aceptación real.

## 2.2 Responsabilidad de capas

Plantillas ayudan con formularios/foco/mensajes; vistas autentican/validan forma y llaman servicios; servicios reautorizan, validan reglas y manejan transacciones/locks; modelos/BD protegen tipos, FK, unicidad y checks. Ninguna cifra, rol, vendedor/turno o estado enviado por el navegador es autoridad. GET no muta datos de negocio.

La aplicación usa HTML y formularios Django. El contrato existente devuelve errores de campo mediante200 cuando corresponde y redirige tras POST válido;401/409/422 de un diseño API previo no se exigen a todas las vistas HTML. Navegación anónima redirige al ingreso; rol ajeno deniega403 y propiedad puede ocultarse con404. No exponer SQL/stack/secretos. El mismo rechazo debe conservar datos independientemente del códigoHTTP.

Precisión01-E (14/11/2026): LoginForm explicita máximo254 alineado con Account/DOC-02-04. Recorta extremos antes de validar longitud; el servicio conserva casefold. Un rechazo por longitud no alcanza el contador. Sin migración ni canonicalizaciónIDNA. `/admin/login/` es superficie independiente y su acceso/limitación productiva sigue pendiente de DOC-01-06; corregir un campo del login no cierra ese contrato.

## 2.3 Modelo e invariantes

Identidad/catálogo/inventario/caja/ventas mantienen FK y datos históricos. Código de producto editable no cambia identidad ni snapshots. GTIN y código interno conservan equivalencias/reservas ya aceptadas; legacy ambiguo requiere clasificación antes de migrar. Nombre comercial normalizado único incl.inactivos, empleados/proveedores pueden ser homónimos. Todos los productos del alcance sonUND con vencimiento.

Una carga inicial por producto; recepciones posteriores separadas por identidad/clave/huella, no compartiendo la constancia de carga como si fueran el mismo evento. Una recepción por producto puede tener varios lotes; multiproducto/SOL futuros. Número comercial normalizado no es UUID de ingreso: permitir recepciones distintas del mismo lote coherente con fecha/costo/proveedor propios (DOC03AI). Ajuste de existencia vencida soloADMIN y no vendible; ninguna entrada ordinaria vencida.

Venta confirmada requiere cabecera, líneas ordenadas, snapshots producto/precio/costo/vendedor/caja, asignaciones por lote, movimiento de efectivo y de inventario, correlativo y resultado idempotente atómicos. En14-F el cobro persiste asignaciones por lote, posición de línea y snapshots vendedor/caja. `Sale` representa el único ingreso de efectivo de esa venta y el cierre suma su total una vez por turno. La equivalencia se documenta en08 y se prueba con rollback, reenvío y cierre. ConcurrenciaPG, caída real y protección ante escritura directa requieren evidencia propia en15. Las consultas usan la historia confirmada y conservan el borrador conforme PROP-11-05.

RN25 exige venta irrepetible; clave UUID y huella canónica pueden vivir en la entidad confirmada con unicidad y controles de actor/contenido, sin obligación de tabla genérica `idempotency_record`. Misma clave/contenido devuelve original; distinto contenido rechaza. No se requiere cabeceraHTTP si el formulario existente transporta una clave validada con las mismas garantías.

## 2.4 Autorización y exposición

RN29 y DEC12PERMISOS son la matriz única: ADMIN mantiene maestros/personal, ajusta inventario, registra bajas y consulta global; ALMACENERO recibe/da de baja y consulta inventario; VENDEDOR opera solo su turno y consulta propios. Portal técnico no se concede por rol comercial. Históricos/constancia cliente no exponen costos. La normalización/máximo254 y reset trazable de personal se detallan en DOC02-04; no confundir resetADMIN con recuperación por correo futura.

## 2.5 Dinero, costo, tiempo y datos

Dinero Decimal2, costo Decimal4, HALF_UP. RN14 usa físico registrado para promedio móvil, no stock vendible. Venta/baja/ajuste negativo no reponderan por costos de compra restantes; al agotar físico, promedio vigente0 y snapshots previos intactos. Entrada actualiza ponderado, ajuste positivo sigue su política explícita. Costos legacyNULL permanecen desconocidos salvo evidencia inequívoca.

En14-E, recepción toma Q físico previo dentro del lock de producto, incluyendo vencidos. Venta/baja/ajuste capturan costo antes de cambiar stock; el helper `reset_average_cost_if_empty` consulta lotes persistidos y pone promedio0 solo si no queda cantidad física positiva. Las salidas con remanente no reponderan. Ajuste positivoQ0 sin costo fiable se rechaza antes de escribir. `inventory0007_output_unit_cost` agrega costo nullable a baja/ajuste sin default/backfill. La migración ensayada conserva las filas antiguas; no demuestra saneamiento de una base operativa. [Diseño y diagnóstico](auditoria_por_etapas/resultados/soporte/14-E-inventario.md).

Límite operación venta/efectivo/apertura9,999,999.99; cierre acumulado admite14,2; diferencia=contado−esperado y puede ser negativa. 14-D implementó la suspensión del descuento discrecional nuevo en formulario/servicio y la recuperación idempotente con importes históricos. Formulario de reintento validado por separado, con actor, clave, borrador, subtotal y efectivo originales. La comprobación histórica precede la política nueva. Evidencia SQLite y Chrome en [disposiciones14-D](auditoria_por_etapas/resultados/soporte/14-D-disposiciones.md). Base=HALF_UP(total/1.18,2),IGV=total−base describe modelo interno uniforme, no certificación tributaria.

Timestamps UTC, negocio/pantalla America/Lima. Físico suma disponible; vendible requiere fecha>hoy y disponibilidad comercial de producto/categoría. FEFO total fecha→ingreso→ID. No usar CHECK dependiente del reloj. Referencias históricas no se reconstruyen con datos maestros actuales.

### Restricciones e índices mínimos

| ID | Restricción o índice | Motivo |
|---|---|---|
| `DB-C01` | `UNIQUE(account.email_normalized)` | Login inequívoco |
| `DB-C02` | `UNIQUE(category.name_normalized)` | Seed idempotente y sin categorías duplicadas |
| `DB-C03` | `UNIQUE(product.barcode_normalized)` | Código de barras irrepetible |
| `DB-C04` | checks de precio `> 0`, mínimo `>= 0`, costo `>= 0` | Integridad aunque se evada el formulario |
| `DB-C05` | `UNIQUE(initial_inventory_load.product_id)` | Impide segunda carga inicial, incluso concurrente |
| `DB-C06` | Unicidad de línea/lote normalizado dentro de recepción; identidad comercial puede repetirse en otra recepción (DOC03AI) | Alcance de unicidad del lote acordado |
| `DB-C07` | Cantidad recibida original>0 e inmutable; saldo disponible>=0; costo>0; capacidad acumulada y movimientos de ajuste separados del original recibido | No confundir cantidad original recibida con capacidad tras ajuste positivo; conciliar saldo con movimientos |
| `DB-C08` | Índice FEFO candidato por producto/vencimiento/ingreso/ID; medir antes de crear o cambiar | Selección estable de lotes vendibles |
| `DB-C09` | índice único parcial de `cash_shift(register_id)` donde estado=`OPEN` | Una sola caja abierta bajo carrera |
| `DB-C10` | índice único parcial de `sale_draft(shift_id)` donde estado=`ACTIVE` | Un borrador activo observable |
| `DB-C11` | Correlativo venta único; clave idempotente única por operación en registro propio o entidad confirmada equivalente, con actor y huella verificados | Correlativo e idempotencia |
| `DB-C12` | Evento de venta representado por `Sale`, clave de cobro única y vínculo único con borrador. Cierre suma cada total del turno una vez | Equivalencia aceptada14-F en08, reintento y rollback revalidados |
| `DB-C13` | índices de búsqueda por código, nombre normalizado, turno/fecha de venta y vencimiento | Volumen de referencia y consultas del flujo |
| `DB-C14` | FK restrictivas desde ventas, detalles, asignaciones, lotes y turnos | Protege historial |
| `DB-C15` | `CHECK(role.code IN ('ADMIN','ALMACENERO','VENDEDOR'))` | Impide roles fuera de los tres autorizados en R1 |
| `DB-C16` | `CHECK(product.controls_expiration = TRUE)` en R1 | Impide producto sin control de vencimiento en alcanceUND |

La condición «vencimiento posterior al día actual de Lima» y las sumas entre filas no se expresan como `CHECK` dependiente del reloj. Se validan dentro del servicio transaccional con un reloj inyectable y se cubren con pruebas de integración. Las restricciones simples sí viven en PostgreSQL.

## 2.6 Transacciones y orden de locks

El diseño anterior omitía locks de actores incorporados por auditorías. La implementación siguiente debe documentar un orden global compatible con todas las rutas (actor, caja/turno, borrador, producto/lote, contador/derivados), ordenando conjuntos de IDs; no copiar la secuencia histórica de un solo servicio. `PROP-09-LOCK-ORDER-01` y `SEC-15-CONC-02` requieren verificar parejas de operaciones y ausencia de inversiones. La unicidad en BD sigue siendo barrera final. No se considera probado solo por usar `atomic()`.

Idempotencia no habilita leer venta ajena ni aplicar política nueva a una confirmación histórica. Cobro/cierre comparten exclusión de turno; venta/recepción/baja/ajuste comparten producto/lotes y actor revalidado. El resultado concurrente debe corresponder a un orden serial válido. Fallo en cualquier derivado revierte operación completa; reintentos técnicos limitados solo ante error transitorio comprobado, nunca ante validación de negocio.

## 2.7 Contratos web y presentación

Rutas reales se consultan en urls.py y matrices de etapa. Superficies principales: ingreso/salida, empleados, categorías/productos, proveedores, carga/entrada/stock/vencimientos/bajas/ajustes/movimientos, apertura/cierre/turnos, borrador/cobro/constancia/historial. No prometer endpointsREST del diseño histórico ni pantallas de funciones futuras.

Encargos define campos/límites, confirmación de estado, error contextual, consulta propia/global, orden persistido, paginación25 y no mutaciónGET. Pantalla bloqueada tras300s requiere servidor+reautenticación, preserva borrador/turno y no es logout ni bloqueo de ingreso15min. Etiquetas, teclado, foco, ancho estrecho e impresión requieren prueba visual propia.

El panel mínimo de Inicio consulta ventas y descuentos confirmados del día de Lima para ADMIN. Los turnos abiertos y las cantidades de productos o lotes son estados al consultar. El servidor prepara las cifras permitidas para el rol y la plantilla identifica la fecha, la ventana de 30 días y la actualización al abrir o recargar. ALMACENERO recibe las consultas de inventario. VENDEDOR accede a las operaciones de su puesto. Para conciliar un enlace se compara el período y el filtro del destino con los de la cifra. [Caso del panel mínimo](08_Historias_de_Usuario.md#CP-DEC-07-VENCIDOS-FILTRO-002).

Precisión técnica13-B: una única sentenciaSELECT con agregados/subconsultas debe producir las siete cifrasADMIN o las tresALMACENERO con el mismo díaLima y snapshot de sentencia; VENDEDOR no consulta métricas del negocio. La reproducción PostgreSQL18.4 detectó mezcla de commits entre lecturas anteriores. Esta solución no cambia aislamiento global, no mantiene transacciones abiertas durante navegación, no añade caché ni índices sin medición, y no promete un corte compartido con consultas de destino posteriores. PostgreSQL17 sigue objetivo; la evidencia18.4 conserva esa diferencia. El enlace de ventas identifica todas las fechas y explica Fecha exacta; textos de mínimo incluyen igualdad y entrada significa mercadería recibida. El error500 no depende de consultas adicionales, no presenta ceros ni detalles técnicos y ofrece recuperación. [Decisiones y alcance de evidencia13-B](auditoria_por_etapas/resultados/soporte/13-B-disposiciones.md).

El 13/11/2026 se verificó el mismo build en navegador con los tres roles, el cobro y la recarga, las consultas vacías o fallidas, los filtros y los permisos. La prueba en PostgreSQL 18.4 cubre la consistencia de las cifras devueltas por una sentencia. [Resultado del panel mínimo](auditoria_por_etapas/resultados/ETAPA-13.md#cierre-13-b-final).

## 2.8 Seguridad y eventos

Sesión de servidor, rotación/revocación, Argon2id, CSRF en escrituras, HTTPS/cookies seguras en red, permisos dentro del caso de uso, secretos fuera de repositorio y logs sanitizados. Son controles requeridos; configuración productiva no examinada. Portal técnico restringido; tráfico/retención requieren medir entorno y fijar política explícita. No confundir mensajes uniformes con prueba estadística de tiempos ni filtro con evento instrumentado. Contratos DOC01-06 y DOC02-04.

## 2.9 Legado y migración

Cada encargo produce diagnóstico de colisiones, referencias, valores, origen y cobertura histórica antes de migrar. Carga/entrada de una misma familia, costosNULL, orden de líneas antiguo y asignaciones faltantes necesitan tratamiento específico. No inventar historia, fusionar maestros ni actualizar datos del usuario en este trabajo. Preservar migraciones aplicadas; nuevas restricciones requieren ensayo sobre clon y rollback. `sales.0004` añade producto; `sales.0005` añade costo unitario.

## 2.10 Migraciones y datos iniciales

- Las migraciones Django son versionadas, revisadas y aplicadas en CI/entorno autorizado; la base operativa requiere autorización separada; no se modifica una migración que ya llegó a demostración.
- `RunSQL` se usa solamente para índices parciales, checks o triggers justificados, con operación inversa cuando sea segura.
- CI crea PostgreSQL vacío, ejecuta todas las migraciones, aplica seeds dos veces y confirma que la segunda ejecución no duplica filas.
- El comando idempotente de datos ficticios crea roles, tres cuentas activas de prueba (una por rol) y una cuenta inactiva de prueba, categoría «Productos enlatados», caja `CAJA-01` y contador inicial. Las contraseñas proceden del ambiente y no del repositorio.
- El reset de prueba solo puede ejecutarse en ambientes marcados expresamente como `local` o `ci`; debe negarse en demostración.
- No se cargan productos, lotes, ventas ni cierres ficticios como si fueran evidencia del Sprint. Los fixtures de prueba permanecen identificados como tales.

## 2.11 Ambientes, CI y despliegue

| Ambiente | Datos | Acceso | Propósito |
|---|---|---|---|
| Local | Fixtures ficticios reiniciables | Equipo | Desarrollo y prueba individual |
| CI | PostgreSQL efímero por ejecución | Pipeline | Migraciones, análisis y pruebas automáticas |
| Demostración | Datos ficticios controlados | HTTPS y equipo autorizado | Revisión integrada y Sprint Review |

### Pipeline obligatorio

1. Instalación reproducible de dependencias fijadas.
2. Formato/lint y comprobaciones estáticas.
3. `python manage.py check --deploy` con configuración de demostración segura.
4. Base vacía → migraciones → seeds dos veces → comprobación de drift.
5. Pruebas unitarias e integración con el runner estándar `python manage.py test`; los soportes aislados de auditoría pueden invocar el runner estándar sin reemplazar sus tests ni excluir módulos.
6. Pruebas de concurrencia e idempotencia contra PostgreSQL real, no SQLite.
7. Construcción de imagen identificada por commit.
8. Playwright del recorrido crítico en ambiente efímero o de integración.
9. Publicación del artefacto solo si todas las puertas anteriores terminan correctamente.

### Despliegue y reversión

- El despliegue de demostración es manual y autorizado desde un artefacto ya comprobado en CI.
- Antes de una migración con datos se crea backup y manifiesto.
- Se aplica migración una sola vez, se inicia la nueva imagen y se ejecuta smoke test: `ready`, login, lectura de categoría y acceso autorizado.
- Si falla la aplicación, se vuelve a la imagen anterior. No se autoriza migración destructiva por esta conciliación; los cambios de esquema son aditivos para permitir reversión de aplicación o, en caso extremo, restauración controlada.
- La base no expone puerto público. HTTPS es obligatorio si el enlace sale del equipo local.

## 2.12 Observabilidad y auditoría

- Logs estructurados con UTC, nivel, evento, `request_id`, usuario interno cuando exista, módulo, duración y resultado.
- Cada respuesta de error muestra un `request_id` que permite correlacionar sin revelar internals.
- Eventos mínimos: login exitoso/fallido sin contraseña, logout, producto creado/rechazado, carga confirmada/rechazada, apertura/conflicto, cobro/rollback/reintento idempotente y cierre/conflicto.
- Métricas mínimas del host: disponibilidad de aplicación, conexión a BD, latencia y conteo de respuestas 5xx. Observabilidad avanzada queda fuera del PMV.
- El registro de auditoría no sustituye las evidencias de prueba y no se marca como implementado hasta existir una ejecución real.

## 2.13 Backup y restauración

### Backup (`S1-OPS-DB-01`)

1. Ejecutar `pg_dump` en formato custom, sin propietarios ni credenciales embebidas.
2. Nombrar el archivo con ambiente y timestamp UTC.
3. Generar manifiesto con versión PostgreSQL, commit, última migración, tamaño y conteos de control.
4. Calcular SHA-256 y almacenarlo junto al manifiesto.
5. Guardar la copia cifrada fuera del repositorio y del volumen activo de PostgreSQL.
6. Conservar 7 diarias y 4 semanales. Es objetivo de retención del diseño; no se ha ejecutado ni autorizado eliminación operativa.

### Restauración (`S1-OPS-DB-02`)

1. Crear una base limpia aislada con la misma versión mayor.
2. Verificar checksum antes de restaurar.
3. Ejecutar `pg_restore`, comprobar migraciones y ejecutar checks de integridad.
4. Comparar conteos del manifiesto y verificar correlativos, un turno, productos, lotes y una constancia histórica.
5. Ejecutar el recorrido de smoke test sin afectar demostración.
6. Registrar duración y resultado real en `04_Evidencias.md`; hasta entonces el estado es `Pendiente`.

Objetivos propuestos para el piloto: **RPO máximo 24 horas** y **RTO máximo 2 horas**. La puerta de piloto exige una restauración real satisfactoria, no solo la existencia de un archivo.

## 2.14 Requisitos no funcionales de R1-PMV

| ID | Requisito verificable | Método previsto |
|---|---|---|
| `NFR-01` | Ninguna operación transaccional deja venta, stock, caja o carga a medias | Fallos inducidos e inspección posterior |
| `NFR-02` | Doble solicitud no crea dos cargas, turnos, ventas, correlativos ni cierres | Pruebas concurrentes con barrera |
| `NFR-03` | Toda operación protegida rechaza sesión ausente, rol incorrecto y URL directa | Matriz de autorización automática/manual |
| `NFR-04` | Dinero usa decimal exacto; `base + IGV = total`; stock nunca es negativo | Pruebas de frontera y constraints |
| `NFR-05` | En volumen de referencia, búsqueda responde en ≤ 2 s p95 y cobro en ≤ 3 s p95 en el host de demostración acordado | Ensayo repetible, ambiente y muestra registrados |
| `NFR-06` | Flujo principal operable con teclado, foco visible, etiquetas y mensajes asociados al campo | Revisión manual y Playwright básico |
| `NFR-07` | Compatible con Chrome estable en Windows 10/11 a 1366×768 como mínimo; una comprobación en Edge queda como uso de reserva, no como puerta de R1 | Matriz manual registrada |
| `NFR-08` | Instalación, migración, seeds y build son reproducibles desde un clon limpio | Pipeline y guía repetida por otro Developer |
| `NFR-09` | Logs permiten correlacionar fallos sin incluir secretos ni datos sensibles | Inspección de logs de casos positivos/negativos |
| `NFR-10` | Backup cumple checksum/retención y restore recupera el recorrido en ≤ 2 h | Ejecución separada de backup y restore |
| `NFR-11` | Fechas se almacenan en UTC y reglas de vencimiento/visualización usan Lima | Pruebas alrededor de medianoche de Lima |
| `NFR-12` | Una venta y constancia confirmadas permanecen inmutables aunque cambien datos maestros | Consulta histórica después de modificar fixture maestro |

Los umbrales de rendimiento son una línea base de aceptación para la demostración, no una promesa de producción. El reporte debe incluir equipo, versión, datos, número de ejecuciones y percentil; una afirmación sin esos datos no constituye evidencia.

## 2.16 Puertas técnicas

Antes de comenzar una Story:

- sus CA y RN están trazados en `03`;
- las decisiones necesarias de esta línea base están ratificadas;
- existen contratos o fixtures que permitan trabajo paralelo;
- la Task/Subtask tiene resultado y evidencia esperada.

Antes de marcar una Story como Hecha:

- migraciones aplican desde base vacía;
- autorización, servicio y constraints relevantes están comprobados;
- pruebas automáticas y manuales asociadas tienen resultado real;
- un revisor distinto comprobó sus CA;
- no existen Bugs críticos/graves abiertos;
- `04_Evidencias.md` enlaza evidencia real, no una descripción futura.

Antes del piloto controlado, además:

- el recorrido E2E completo es satisfactorio;
- el despliegue y smoke test son satisfactorios;
- backup y restauración se ejecutaron por separado con checksum válido;
- la constancia exhibe la advertencia tributaria;
- existe autorización académica/documentada antes de un piloto, si el curso lo permite.

## 2.17 Exclusiones vigentes

SOL, anulaciones/Yape/fiscalidad, multirrol/múltiples cajas/sedes, productos sin vencimiento o por peso, correo/sesión única/cierre remoto/LOG UI, caja manual/forzada/aprobada y reportes completos permanecen futuros o fuera según09. Mermas, recepción directa, personal y bloqueo de ingreso sí están seleccionados; pantalla300s es nueva puerta del piloto. No ocultar esas brechas bajo exclusiones históricas deSprint1.

## 2.18 Compatibilidad y evidencia

Versiones exactas ejecutadas y hashes están en VERIFICACION.md; compatibilidad esperada y política de soporte en FUENTES_EXTERNAS.md. CI, backup/restore, NFR05/10 y despliegue continúan pendientes de evidencia adecuada. Un dry-run sin migraciones nuevas no demuestra migraciones aplicadas a la base operativa.

## 2.19 Trazabilidad de decisiones técnicas DT

Los IDs originales se conservan; sus formulaciones vigentes son las siguientes. No son evidencia de ejecución.

| ID | Decisión vigente | Aplicabilidad |
|---|---|---|
| DT-01 | Web interna responsiva, mismo origen | Conservada; pruebas visuales por alcance |
| DT-02 | Monolito Django5.2/Python3.12, templates;HTMX opcional | Python3.12.10/Django5.2.18 ejecutados; otras versiones no acreditadas aquí |
| DT-03 | PostgreSQL17 objetivo y migraciones nativas | 18.4 evidencia parcial; no actualizar motor sin plan |
| DT-04 | Tres roles exclusivos;3cuentas activas +1inactiva ficticia | Alineado con seed_pmv; ninguna cuenta/rol real inferido |
| DT-05 | Sesión servidor, cookies seguras/CSRF/Argon2 | Despliegue real no verificado |
| DT-06 | Cualquier categoría activa,UND,vencimiento; ajuste vencido excepcional no vendible | DOC03-01 y RN03 vigente |
| DT-07 | Lote normalizado y recepción propia;FEFO fecha/ingreso/ID | DOC03AI/DEC05ESPACIOS sustituyen unicidad global producto+número |
| DT-08 | Decimal2/4,HALF_UP; costo móvil físico y topes separados | RN14 y DEC11TOPE; fiscalidad real pendiente |
| DT-09 | Salir conserva turno; descarta borrador con confirmación | RN30; bloqueo pantalla es otro flujo |
| DT-10 | Caja única y turnoOPEN global único | Permisos/locks/constraint y pruebas concurrentes |
| DT-11 | BorradorACTIVE solo con líneas, sin reserva | GET no muta; cantidad1..999999 |
| DT-12 | V-00000001 global único, ascendente e inmutable | Idempotencia y atomicidad completos |
| DT-13 | Local,CI efímero,demostración; redBD privada | DockerCompose del diseño no acredita despliegue real |
| DT-14 | Backupcustom/manifiesto/SHA256;7diarias+4semanales;restore aislado | Objetivo de diseño, sin eliminación operativa ni restauración verificada aquí |
| DT-15 | Volumen de referencia2,000productos/20,000lotes/300ventas-día | PruebasNFR05 pendientes; no estimación de actividad real |

## Revalidación técnica 14-D · 13/11/2026

La causa de baja se valida con el lote bloqueado y la fecha Lima. VENCIMIENTO requiere fecha<=hoy, DAÑO requiere fecha>hoy y explicación, ROBO/FALTANTE exige explicación con independencia de fecha. Se reutilizan servicio transaccional, idempotencia y orden de locks vigentes. Esta corrección acotada carece de migración de datos. Valoración RN14, constancia dedicada y asignaciones históricas siguen en los encargos originales.

La evidencia E2E enlaza lecturas de navegador, peticiones HTTP y huellas de persistencia en una sola cadena de tres roles. Se registran un manifiesto de archivos y una base aislada por ejecución. El historial actual permite observar cantidades por operación, y la auditoría mantiene abierta la implementación de saldo por movimiento, filtros/paginación y asignación por lote. [Caso](08_Historias_de_Usuario.md#CP-INTEGRACION-ROLES-001) · [Informe](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-d).

## Revalidación técnica14-E · 13/11/2026

Promedio y snapshots de costo revalidados en SQLite aislado y Chrome. Se conserva el orden actor→producto→lotes y las transacciones de servicios. El helper de salida exige que el llamador posea el lock del producto; no pretende ser una operación de inventario independiente. Las fallas después de escritura revierten recepción, venta, baja y ajuste. PostgreSQL, caída real y recuperación requieren evidencia propia.

El diagnóstico de legado está diseñado para un clon explícito en solo lectura. Ni el costo de adquisición del lote restante ni el promedio actual permiten reconstruir inequívocamente salidas anteriores. No se aplicó una apertura de valoración ni se leyó la base operativa. Asignaciones, snapshots de caja/vendedor, referencia de recepción y saldo de Kardex siguen pendientes14-F. [Resultado14-E](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-e).

## Revalidación técnica14-F · 13/11/2026

`sales.0006_sale_lot_traceability` añade `SaleLotAllocation` con FK PROTECT a línea/lote, cantidad positiva, unicidad por línea/lote y snapshots de número64, vencimiento e ingreso. Posición positiva única por venta ordena cada línea. Encabezado vendedor120/caja32 y posición son nullable para conservar el legado. El ensayo0005→0006 verifica columnas antiguas idénticas, nuevos camposNULL y cero asignaciones inferidas.

El servicio bloquea actor, caja y turno, conserva el bloqueo de productos/categorías/lotes y captura los valores históricos antes de completar. Cada asignación se guarda durante FEFO, seguida del descuento del lote. Se comprueba suma por línea antes del commit. Los checks protegen cantidad/unicidad, y la congruencia entre productos y suma depende del servicio. La prueba de fallos cubre ocho puntos posteriores a escritura. Integridad ante escrituras directas y carreras reales conserva etapa15.

Constancia e historial presentan vendedor/caja guardados. El legado usa «No disponible (registro anterior)» y advierte ausencia del orden original, con posiciónNULL ordenada determinísticamente porUUID. Movimientos internos muestran lotes persistidos, cantidad/vencimiento y costo4decimales. Cobertura parcial se rotula explícitamente, y la coincidencia por código sin FK se declara pendiente de confirmar identidad.

La revisión de UI mantuvo componentes existentes y aplicó la guía de estados vacíos para expresar datos históricos ausentes. Las observacionesChrome validan las leyendas y acceso por rol. Pendientes siguen recepción propia, saldo cronológico/filtros/paginación y constancia de merma. [Evidencia14-F](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-f) · [Decisiones](auditoria_por_etapas/resultados/soporte/14-F-disposiciones.md).

## Concreción14-G · recepción y procedencia

StockReceipt almacena referencia/UUID/huella y snapshots; StockReceiptLine captura cantidad/costo/vencimiento original y OneToOne al lote físico; StockReceiptCounter reservaR-######## global. Se conserva laFK técnicaLot→InitialInventoryLoad por compatibilidad, pero no se usa como identidad de recepción ni como prueba del origen antiguo. La migración0008 no crea recepciones históricas ni modifica filas previas. Reinstala el triggerreceived_at enSQLite tras reconstrucción y en reversión.

El servicio bloquea actor→contador global→producto→categoría→proveedor, dentro de una transacción. El contador serializa altas de recepción para una caja/minimarket; su costo concurrente requiere medir en15. No hay dependencia inversa desde los otros servicios hacia este contador. Antes de validar estado temporal de una entrada nueva, una clave ya confirmada de igual actor/contenido devuelve su identidad. El actor debe seguir autorizado. El formulario exigeUUID; llamadas internas sin clave representan ingreso nuevo. Huella ordenada de líneas normalizadas; igualdad monetaria a4decimales.

Número comercial igual en recepciones distintas creaLot distinto; misma fecha obligatoria, por comparación canónica incluso con grafía antigua. Una restricción mantiene unicidad por carga inicial; otra por recepción+número. Las filas de nuevas recepciones guardan los valores originales aunque aumente la capacidad técnica delLot. La consulta y las selecciones de baja/ajuste distinguen referencias. Bajas/ajustes y asignaciones de venta enlazan la recepción de su lote. No se cambia el algoritmoFEFO.

584/584regresión,23checkpointsChrome de recepción conectada y44de cadena general con fuentes estables. ConcurrenciaPG/caída, diagnóstico operativo, snapshots de carga inicial, saldo/filtros/paginación y constancia de merma permanecen pendientes. [Informe14-G](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-g) · [Decisiones](auditoria_por_etapas/resultados/soporte/14-G-disposiciones.md).


## Concreción14-H1 · fotografía de carga inicial

InitialInventoryLoad agrega cabecera nullable nombre160/código64/unidad8/autor120/proveedor160/RUC11/promedio14,4; ausencia de proveedor se guarda como cadena vacía y NULL representa legado. InitialLoadLine conserva número64, cantidad positiva, costo positivo14,4, vencimiento e instante original, con FK PROTECT y loteOneToOne. Unicidadcarga/número. El servicio existente valida y bloquea actor→producto→categoría→proveedor, crea cabecera/lotes/líneas y promedio dentro de una transacción. No se rellena historia antigua ni se reconstruye Lot; el guardreceived_at continúa vigente.

Consulta separa foto original y stock/costo actuales; Kardex usa la línea capturada y enlaza carga, sin deducir cantidad de capacidad. Las relaciones transversales y snapshots se protegen por el servicio, no se garantiza defensa ante SQL arbitrario. Cuatro fallos postwrite y migración aditiva verificados en SQLite. Reversión0009 elimina la foto; recuperación/PG requieren15. Saldo/filtros/paginación quedan enH2. Se descartaJSON sin esquema frente al patrón tipado ya empleado enrecepción.

[Informe14-H1](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-h1) · [Fundamento y límites](auditoria_por_etapas/resultados/soporte/14-H-disposiciones.md).


## Concreción14-H2 · consulta deKardex

inventory/ledger.py deriva entradas desdeInitialLoadLine/StockReceiptLine, ventas yallocations, bajas yajustes. Orden total instante+IDdeorigen+tipo. Concilia cantidades porlote ytotal; faltante/relaciónincoherente/asignaciónparcial/identidadambigua/secuencianegativa/desajuste impidensaldo. La consulta no crea anclas ni mutaBD. Evento sinorigen conocido conserva cantidadNo disponible, noLot.initial_quantity.

MovementFilterForm valida períodoLima por minuto inclusivo, tipos, parámetrosrepetidos y página. select_period calculaapertura/cierre antesdefiltrar y paginar25; variación delconjuntofiltrado completo. Datosinválidos no retornanresultados engañosos. Enlaces mantienen filtros. Prefetch/select_related conservanpresupuestoqueries existente; historial completo enmemoria, noSLAvolumen. Lote nuevo entrelecturas produce aviso sin500,pero consistenciaconcurrentePGrequiere15. CSSlocalmantiene tabla desplazable y cifras legibles en390px. Sinmigración.

[Informe14-H2](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-h2) · [Decisiones](auditoria_por_etapas/resultados/soporte/14-H2-disposiciones.md).


## Continuación14-I · 14/11/2026 Lima

StockWriteOff incorpora UUID única nullable y huella de contenido normalizado; campos nullable de producto/código/unidad, responsable, número/vencimiento y origen. No se reconstruye legado. write_off_stock valida actor vigente, recupera misma operación antes de validar disponibilidad/fecha actuales y confirma fotografía+baja+stock/costo atómicamente. Clave ajena o divergente rechaza. HTTP exige UUID; llamadas internas sin clave son operaciones nuevas. Consulta GET por ADMIN/ALMACENERO, enlace desde Kardex e impresión web usan el mismo registro. El estado comercial inactivo no impide merma legítima. Migración0010 verificada solo en bases ficticias. No hay edición pública de constancia; protección frente a SQL privilegiado y concurrenciaPG conservan tarea15.

[Informe14-I](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-i) · [Disposiciones](auditoria_por_etapas/resultados/soporte/14-I-disposiciones.md).

## Etapa 02 · entrega de pruebas del 20/11/2026

El POST de ingreso conserva una transacción exterior a SessionMiddleware. El servicio bloquea solo la fila de la cuenta antes del identificador de intentos y lee el rol vigente. La escritura de sesión termina antes de liberar el bloqueo. Los errores de servidor revierten la transacción. Se mantiene la regla de turno abierto. El resumen de desactivación distingue rechazo y éxito. Los formularios explican los máximos inclusivos de 120/254. [Segunda pasada pública del 20/11](auditoria_por_etapas/resultados/ETAPA-02.md#entrega-02-publica).
