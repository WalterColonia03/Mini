# Etapa 00 — inventario de código y superficie web

Extracción inicial: 2026-11-05. Reanudación y cotejo de archivos: 2026-11-09 (America/Lima). Este anexo inventaría identificadores y conexiones estáticas; **ninguna HU, módulo ni prueba se declara aprobada por aparecer aquí**. Las ejecuciones acotadas del agente principal se informan en `../ETAPA-00.md`, sin extender sus resultados a otras filas.

## Fuentes y reproducción

- Aplicación activa: `r1-pmv`, Django; montaje raíz en `r1-pmv/config/urls.py:4`. `qr-minimarket` no es una segunda aplicación web: el inventario de fuentes lo registra como carpeta de imagen.
- `ETAPA-00-inventario-codigo.csv`: catálogo por tipo, módulo, fuente, línea, identificador y detalle, con estado `NO EXAMINADO`. Para localizar una ocurrencia use la combinación `tipo + fuente:línea + identificador`; si varias ocurrencias comparten una línea, consérvese además el orden de fila CSV. No son nuevos IDs de HU.
- `ETAPA-00-fuentes-codigo.json`: SHA256 de las 77 fuentes leídas por la extracción AST/HTML inicial. `ETAPA-00-deriva-codigo-09nov.json`: cotejo y manifiesto complementario de todos los `.py/.html/.js/.css` locales, excluidos dependencias, `.git` y cachés. El segundo manifiesto inventaría archivos técnicos no analizados por el primero; no inventaría sus reglas internas.
- `../evidencias/00-rutas-resueltas.json`: expansión del resolver hecha por el agente principal en configuración aislada el 05/11; **resolver una URL no equivale a solicitarla**. No se volvió a arrancar la aplicación para redactar este anexo.
- Reproducción de extracción estática: desde la raíz, `r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/anexos/inventariar_codigo_00.py`. Reescribe los tres archivos derivados iniciales; para conservar el corte original, copiar los artefactos antes de repetir en otra fecha.
- Reproducción del cotejo documental: `r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/anexos/cerrar_inventario_codigo_00.py`. No importa Django, no usa `.env`, no conecta a una base, no ejecuta pruebas y no modifica código de aplicación. La fecha de este constructor corresponde a esta continuación; actualizarla para otro corte.

## Cobertura sintáctica y sus límites

Cotejo: **77 archivos comparados, 0 cambios de bytes** respecto al corte 05/11. El manifiesto complementario enumera 128 archivos de código/plantilla/estilo; 51 no tenían hash en el corte AST/HTML y no se puede afirmar su estabilidad entre fechas. La comparación no acredita ausencia de cambios anteriores al 05/11 ni ausencia de cambios Git sin confirmar.

| Tipo de ocurrencia | Cantidad | Interpretación |
|---|---|---|
| accion_javascript | 9 | Inventariado; NO EXAMINADO semánticamente |
| admin_clase | 9 | Inventariado; NO EXAMINADO semánticamente |
| campo_formulario | 42 | Inventariado; NO EXAMINADO semánticamente |
| campo_formulario_modelo | 11 | Inventariado; NO EXAMINADO semánticamente |
| campo_modelo | 125 | Inventariado; NO EXAMINADO semánticamente |
| campo_personalizado | 1 | Inventariado; NO EXAMINADO semánticamente |
| configuracion_formulario | 20 | Inventariado; NO EXAMINADO semánticamente |
| elemento_ui | 359 | Inventariado; NO EXAMINADO semánticamente |
| formulario | 18 | Inventariado; NO EXAMINADO semánticamente |
| manager | 1 | Inventariado; NO EXAMINADO semánticamente |
| mensaje_servidor | 180 | Inventariado; NO EXAMINADO semánticamente |
| modelo | 18 | Inventariado; NO EXAMINADO semánticamente |
| montaje_admin | 1 | Inventariado; NO EXAMINADO semánticamente |
| plantilla | 36 | Inventariado; NO EXAMINADO semánticamente |
| prueba_definida | 191 | Inventariado; NO EXAMINADO semánticamente |
| restriccion_modelo | 20 | Inventariado; NO EXAMINADO semánticamente |
| ruta | 41 | Inventariado; NO EXAMINADO semánticamente |
| salida_dinamica_ui | 359 | Inventariado; NO EXAMINADO semánticamente |
| servicio | 32 | Inventariado; NO EXAMINADO semánticamente |
| texto_salida_ui | 916 | Inventariado; NO EXAMINADO semánticamente |
| validador | 9 | Inventariado; NO EXAMINADO semánticamente |
| vista | 48 | Inventariado; NO EXAMINADO semánticamente |

Los 48 registros `vista` incluyen auxiliares; no son 48 endpoints. Las 41 rutas de negocio incluyen dos alias de confirmación. Las 36 plantillas incluyen base, errores 403/404 y `identity/protected_placeholder.html`; una plantilla presente no garantiza ruta ni estado accesible. Los 916 textos y 359 expresiones dinámicas son ocurrencias, con duplicados entre plantillas; no son mensajes únicos ni requisitos independientes. Los 180 mensajes de servidor son llamadas sintácticas (incluyen variables y f-strings), no los mensajes finales renderizados. Los 42 campos de formulario declarados y 11 derivados de ModelForm se superponen conceptualmente con campos del modelo. Los 125 campos son declaraciones directas: quedan fuera campos heredados de Django, M2M implícitos, campos de sesión y formularios generados por el admin.

El extractor no reemplaza el inventario funcional de cada etapa: no expande HTML generado por `{{ form }}`, mensajes localizados de Django, todos los estados de JavaScript, mensajes definidos como constantes ni callbacks heredados. Atributos HTML y restricciones se conservan como fuente, sin verificar normalización, valor inicial, límites, persistencia o error. El cierre funcional de cada campo sigue pendiente. Las fuentes técnicas complementarias incluyen migraciones, comandos de gestión, settings y arranque; se identificaron por archivo/hash y requieren lectura focalizada en las etapas correspondientes. Las reglas de formularios se contrastarán con servicios, modelos y base, no solo con widgets HTML.

## Módulos, modelos, formularios y pruebas definidas

| Módulo | Rutas negocio | Modelos | Formularios | Plantillas | Métodos test_* |
|---|---|---|---|---|---|
| identity | 7 | 3 | 3 | 8 | 48 |
| catalog | 10 | 2 | 3 | 7 | 36 |
| inventory | 11 | 5 | 6 | 9 | 41 |
| cash | 5 | 3 | 2 | 5 | 12 |
| sales | 8 | 5 | 4 | 5 | 46 |
| app_platform | 0 | 0 | 0 | 0 | 8 |
| templates | 0 | 0 | 0 | 2 | 0 |

Los **191 métodos test_*** son definiciones estáticas (48 identidad, 36 catálogo, 41 inventario, 12 caja, 46 ventas, 8 plataforma), **cero ejecuciones de pruebas desde este anexo**. No se tomó la cifra histórica 191 como un resultado nuevo. `config/test_runner.py:10` descubre aplicaciones locales y la carpeta `tests`; no se inspeccionaron resultados de test por inferencia del nombre. El CSV identifica cada método con clase, archivo y línea. La carpeta `r1-pmv/tests` no aportó métodos test_* en este corte. Los tests de semillas/reset son código de prueba; no autorizan ejecutar reset ni esas semillas sobre datos del usuario.

| Módulo | Tipo | Identificador | Fuente precisa |
|---|---|---|---|
| identity | formulario | LoginForm | r1-pmv/identity/forms.py:6 |
| identity | formulario | EmployeeCreationForm | r1-pmv/identity/forms.py:46 |
| identity | formulario | EmployeeEditForm | r1-pmv/identity/forms.py:84 |
| identity | modelo | Role | r1-pmv/identity/models.py:11 |
| identity | modelo | LoginAttempt | r1-pmv/identity/models.py:27 |
| identity | modelo | Account | r1-pmv/identity/models.py:58 |
| catalog | formulario | CategoryForm | r1-pmv/catalog/forms.py:14 |
| catalog | formulario | ProductRegistrationForm | r1-pmv/catalog/forms.py:28 |
| catalog | formulario | ProductEditForm | r1-pmv/catalog/forms.py:104 |
| catalog | modelo | Category | r1-pmv/catalog/models.py:14 |
| catalog | modelo | Product | r1-pmv/catalog/models.py:35 |
| inventory | formulario | InitialLoadProductForm | r1-pmv/inventory/forms.py:14 |
| inventory | formulario | StockEntryProductForm | r1-pmv/inventory/forms.py:42 |
| inventory | formulario | LotInputForm | r1-pmv/inventory/forms.py:70 |
| inventory | formulario | SupplierForm | r1-pmv/inventory/forms.py:112 |
| inventory | formulario | StockWriteOffForm | r1-pmv/inventory/forms.py:145 |
| inventory | formulario | PhysicalAdjustmentForm | r1-pmv/inventory/forms.py:170 |
| inventory | modelo | InitialInventoryLoad | r1-pmv/inventory/models.py:16 |
| inventory | modelo | Lot | r1-pmv/inventory/models.py:37 |
| inventory | modelo | Supplier | r1-pmv/inventory/models.py:113 |
| inventory | modelo | StockWriteOff | r1-pmv/inventory/models.py:131 |
| inventory | modelo | PhysicalAdjustment | r1-pmv/inventory/models.py:162 |
| cash | formulario | CashOpeningForm | r1-pmv/cash/forms.py:6 |
| cash | formulario | CashCloseForm | r1-pmv/cash/forms.py:32 |
| cash | modelo | CashRegister | r1-pmv/cash/models.py:12 |
| cash | modelo | CashShift | r1-pmv/cash/models.py:24 |
| cash | modelo | CashShiftClose | r1-pmv/cash/models.py:60 |
| sales | formulario | ProductSearchForm | r1-pmv/sales/forms.py:8 |
| sales | formulario | AddDraftLineForm | r1-pmv/sales/forms.py:23 |
| sales | formulario | UpdateDraftLineForm | r1-pmv/sales/forms.py:32 |
| sales | formulario | CheckoutForm | r1-pmv/sales/forms.py:40 |
| sales | modelo | SaleCounter | r1-pmv/sales/models.py:15 |
| sales | modelo | SaleDraft | r1-pmv/sales/models.py:28 |
| sales | modelo | SaleDraftLine | r1-pmv/sales/models.py:63 |
| sales | modelo | Sale | r1-pmv/sales/models.py:92 |
| sales | modelo | SaleLine | r1-pmv/sales/models.py:124 |

## Todas las rutas de negocio y permisos declarados

A = Administrador (`ADMIN`), L = Almacenero (`ALMACENERO`), V = Vendedor (`VENDEDOR`); visitante = no autenticado, no un cuarto registro de `Role`. Fuente: `identity/models.py:11`. El decorador `identity/authorization.py:17` redirige al visitante y rechaza roles fuera de lista; esto es una descripción del código. Todas las combinaciones de actor/ruta/HTTP siguen `NO EJECUTADO` salvo los casos que el informe principal identifique con evidencia concreta.

`Auth` significa cuenta autenticada. En `/inicio/` se comprueba además que el código del rol sea válido (`identity/views.py:57`). GET/POST no implica que todas sus acciones estén permitidas en cualquier estado. En formularios, consultar el CSV para acciones y campos asociados y la columna `plantillas` para la pantalla fuente.

| Nombre URL | Ruta | HTTP | Roles | Vista | Plantilla |
|---|---|---|---|---|---|
| login | `/` | GET, POST | Público | r1-pmv/identity/views.py:27 | identity/login.html |
| dashboard | `/inicio/` | GET | Auth | r1-pmv/identity/views.py:56 | identity/dashboard.html |
| logout | `/salir/` | GET, POST | Auth | r1-pmv/identity/views.py:68 | identity/logout_confirm.html |
| employee-list | `/empleados/` | GET | A | r1-pmv/identity/views.py:84 | identity/employee_list.html |
| employee-create | `/empleados/nuevo/` | GET, POST | A | r1-pmv/identity/views.py:98 | identity/employee_form.html |
| employee-edit | `/empleados/<uuid:account_id>/editar/` | GET, POST | A | r1-pmv/identity/views.py:129 | identity/employee_edit.html |
| employee-deactivate | `/empleados/<uuid:account_id>/estado/` | POST | A | r1-pmv/identity/views.py:167 | Redirección/acción; ver vista |
| category-list | `/productos/categorias/` | GET | A | r1-pmv/catalog/views.py:39 | catalog/category_list.html |
| category-create | `/productos/categorias/nueva/` | GET, POST | A | r1-pmv/catalog/views.py:48 | catalog/category_form.html |
| category-toggle | `/productos/categorias/<uuid:category_id>/estado/` | POST | A | r1-pmv/catalog/views.py:63 | Redirección/acción; ver vista |
| product-expirations | `/productos/vencimientos/` | GET | A,L | r1-pmv/catalog/views.py:163 | catalog/product_expirations.html |
| product-list | `/productos/` | GET | A,L | r1-pmv/catalog/views.py:79 | catalog/product_list.html |
| product-entry | `/productos/nuevo/` | GET, POST | A | r1-pmv/catalog/views.py:98 | catalog/product_form.html |
| product-created | `/productos/<uuid:product_id>/registrado/` | GET | A | r1-pmv/catalog/views.py:112 | catalog/product_created.html |
| product-created-alias | `/productos/<uuid:product_id>/creado/` | GET | A | r1-pmv/catalog/views.py:112 | catalog/product_created.html |
| product-edit | `/productos/<uuid:product_id>/editar/` | GET, POST | A | r1-pmv/catalog/views.py:121 | catalog/product_edit.html |
| product-toggle | `/productos/<uuid:product_id>/disponibilidad/` | POST | A | r1-pmv/catalog/views.py:147 | Redirección/acción; ver vista |
| inventory-load | `/inventario/carga-inicial/` | GET, POST | L | r1-pmv/inventory/views.py:75 | inventory/initial_load_form.html |
| inventory-load-created-alias | `/inventario/carga-inicial/<uuid:load_id>/creada/` | GET | A,L | r1-pmv/inventory/views.py:101 | inventory/initial_load_created.html |
| inventory-load-created | `/inventario/cargas/<uuid:load_id>/` | GET | A,L | r1-pmv/inventory/views.py:101 | inventory/initial_load_created.html |
| stock-entry | `/inventario/entrada/` | GET, POST | L | r1-pmv/inventory/views.py:130 | inventory/stock_entry_form.html |
| supplier-list | `/inventario/proveedores/` | GET | A,L | r1-pmv/inventory/views.py:162 | inventory/supplier_list.html |
| supplier-create | `/inventario/proveedores/nuevo/` | GET, POST | A | r1-pmv/inventory/views.py:175 | inventory/supplier_form.html |
| supplier-toggle | `/inventario/proveedores/<uuid:supplier_id>/estado/` | POST | A | r1-pmv/inventory/views.py:199 | Redirección/acción; ver vista |
| stock-writeoff | `/inventario/bajas/nueva/` | GET, POST | A,L | r1-pmv/inventory/views.py:215 | inventory/writeoff_form.html |
| physical-adjustment | `/inventario/ajustes/nuevo/` | GET, POST | A | r1-pmv/inventory/views.py:278 | inventory/adjustment_form.html |
| stock-overview | `/inventario/stock/` | GET | A,L | r1-pmv/inventory/views.py:338 | inventory/stock_overview.html |
| product-movements | `/inventario/productos/<uuid:product_id>/movimientos/` | GET | A,L | r1-pmv/inventory/views.py:387 | inventory/product_movements.html |
| cash-open | `/caja/abrir/` | GET, POST | V | r1-pmv/cash/views.py:17 | cash/cash_open.html |
| cash-close | `/caja/cerrar/` | GET, POST | V | r1-pmv/cash/views.py:57 | cash/cash_close.html |
| cash-shift-opened | `/caja/turnos/<uuid:shift_id>/abierto/` | GET | V | r1-pmv/cash/views.py:46 | cash/cash_shift_opened.html |
| cash-shift-closed | `/caja/turnos/<uuid:shift_id>/cerrado/` | GET | A,V | r1-pmv/cash/views.py:89 | cash/cash_shift_closed.html |
| cash-shift-history | `/caja/turnos/` | GET | A,V | r1-pmv/cash/views.py:104 | cash/cash_shift_history.html |
| sales-draft | `/ventas/` | GET, POST | V | r1-pmv/sales/views.py:74 | sales/sales_draft.html |
| sales-checkout | `/ventas/cobrar/` | GET, POST | V | r1-pmv/sales/views.py:172 | sales/sales_checkout.html |
| sales-receipt | `/ventas/constancia/<uuid:sale_id>/` | GET | A,V | r1-pmv/sales/views.py:261 | sales/sales_receipt.html |
| sales-line-update | `/ventas/lineas/<uuid:line_id>/` | POST | V | r1-pmv/sales/views.py:127 | Redirección/acción; ver vista |
| sales-line-remove | `/ventas/lineas/<uuid:line_id>/quitar/` | POST | V | r1-pmv/sales/views.py:152 | Redirección/acción; ver vista |
| sales-draft-discard | `/ventas/descartar/` | POST | V | r1-pmv/sales/views.py:163 | Redirección/acción; ver vista |
| sales-shift-history | `/ventas/historial/turno/` | GET | V | r1-pmv/sales/views.py:275 | sales/sales_shift_history.html |
| sales-history | `/ventas/historial/` | GET | A,V | r1-pmv/sales/views.py:299 | sales/sales_history.html |

Restricciones adicionales ya localizadas, todavía no certificadas: `cash/views.py:50` limita confirmación de apertura al vendedor propietario; `cash/views.py:92` y `:111` limitan cierre/historial al propietario cuando el actor es vendedor. `sales/views.py:264` y `:305` limitan constancia/historial al vendedor propietario; administrador consulta más ampliamente. `sales/services.py:35` exige turno propio abierto y `:128`, `:155`, `:194` enlazan líneas/borrador/cobro al actor. Deben probarse con dos vendedores diferentes en las etapas 09–15; tres roles distintos no prueban aislamiento entre usuarios del mismo rol.

## Superficie adicional /admin/

Hay **65 patrones bajo `/admin/`**, además de las 41 rutas de negocio: **106 patrones resueltos**. Incluyen nueve grupos de modelo (ocho propios + Group de Django), redirecciones, vistas de infraestructura y dos patrones de captura; no son 65 páginas independientes ni 65 peticiones ejecutadas. Lista literal con nombre/callback en el JSON del resolver. Montaje: `config/urls.py:5`. Las clases admin están en `identity/admin.py:7`, `catalog/admin.py:6`, `inventory/admin.py:7` y `cash/admin.py:6`; `LotInline` explica por qué hay nueve clases propias pero ocho registros de modelos propios.

La autorización de Django Admin depende de `is_active/is_staff` y permisos Django; **no equivale al rol de negocio Administrador**. `identity/admin.py:23` expone estado staff/superuser/grupos/permisos; `identity/admin.py:26` muestra los campos de alta. Las plantillas, validaciones y acciones heredadas de Django no forman parte de las 36 plantillas locales y no fueron inventariadas campo a campo. No se entró al admin ni se creó superusuario en este trabajo.

Clasificación provisional de esa superficie: `EXTRA SIN REQUISITO` para sus operaciones administrativas frente a las HUs de negocio; decisión de despliegue/alcance pendiente. La guía `21_Alcance_Actual_y_Diferencias.md` advierte que su login no comparte RN-17. Opciones para etapa 15: documentarlo como herramienta técnica restringida y probar permisos/controles propios, o excluirlo del despliegue operativo según decisión explícita. No se deshabilita ni se modifica ahora por inferencia.

| Patrón admin | Nombre |
|---|---|
| /admin/ | admin:index |
| /admin/login/ | admin:login |
| /admin/logout/ | admin:logout |
| /admin/password_change/ | admin:password_change |
| /admin/password_change/done/ | admin:password_change_done |
| /admin/autocomplete/ | admin:autocomplete |
| /admin/jsi18n/ | admin:jsi18n |
| /admin/r/<path:content_type_id>/<path:object_id>/ | admin:view_on_site |
| /admin/auth/group/ | admin:auth_group_changelist |
| /admin/auth/group/add/ | admin:auth_group_add |
| /admin/auth/group/<path:object_id>/history/ | admin:auth_group_history |
| /admin/auth/group/<path:object_id>/delete/ | admin:auth_group_delete |
| /admin/auth/group/<path:object_id>/change/ | admin:auth_group_change |
| /admin/auth/group/<path:object_id>/ | admin: |
| /admin/identity/role/ | admin:identity_role_changelist |
| /admin/identity/role/add/ | admin:identity_role_add |
| /admin/identity/role/<path:object_id>/history/ | admin:identity_role_history |
| /admin/identity/role/<path:object_id>/delete/ | admin:identity_role_delete |
| /admin/identity/role/<path:object_id>/change/ | admin:identity_role_change |
| /admin/identity/role/<path:object_id>/ | admin: |
| /admin/identity/account/<id>/password/ | admin:auth_user_password_change |
| /admin/identity/account/ | admin:identity_account_changelist |
| /admin/identity/account/add/ | admin:identity_account_add |
| /admin/identity/account/<path:object_id>/history/ | admin:identity_account_history |
| /admin/identity/account/<path:object_id>/delete/ | admin:identity_account_delete |
| /admin/identity/account/<path:object_id>/change/ | admin:identity_account_change |
| /admin/identity/account/<path:object_id>/ | admin: |
| /admin/catalog/category/ | admin:catalog_category_changelist |
| /admin/catalog/category/add/ | admin:catalog_category_add |
| /admin/catalog/category/<path:object_id>/history/ | admin:catalog_category_history |
| /admin/catalog/category/<path:object_id>/delete/ | admin:catalog_category_delete |
| /admin/catalog/category/<path:object_id>/change/ | admin:catalog_category_change |
| /admin/catalog/category/<path:object_id>/ | admin: |
| /admin/catalog/product/ | admin:catalog_product_changelist |
| /admin/catalog/product/add/ | admin:catalog_product_add |
| /admin/catalog/product/<path:object_id>/history/ | admin:catalog_product_history |
| /admin/catalog/product/<path:object_id>/delete/ | admin:catalog_product_delete |
| /admin/catalog/product/<path:object_id>/change/ | admin:catalog_product_change |
| /admin/catalog/product/<path:object_id>/ | admin: |
| /admin/inventory/initialinventoryload/ | admin:inventory_initialinventoryload_changelist |
| /admin/inventory/initialinventoryload/add/ | admin:inventory_initialinventoryload_add |
| /admin/inventory/initialinventoryload/<path:object_id>/history/ | admin:inventory_initialinventoryload_history |
| /admin/inventory/initialinventoryload/<path:object_id>/delete/ | admin:inventory_initialinventoryload_delete |
| /admin/inventory/initialinventoryload/<path:object_id>/change/ | admin:inventory_initialinventoryload_change |
| /admin/inventory/initialinventoryload/<path:object_id>/ | admin: |
| /admin/inventory/lot/ | admin:inventory_lot_changelist |
| /admin/inventory/lot/add/ | admin:inventory_lot_add |
| /admin/inventory/lot/<path:object_id>/history/ | admin:inventory_lot_history |
| /admin/inventory/lot/<path:object_id>/delete/ | admin:inventory_lot_delete |
| /admin/inventory/lot/<path:object_id>/change/ | admin:inventory_lot_change |
| /admin/inventory/lot/<path:object_id>/ | admin: |
| /admin/cash/cashregister/ | admin:cash_cashregister_changelist |
| /admin/cash/cashregister/add/ | admin:cash_cashregister_add |
| /admin/cash/cashregister/<path:object_id>/history/ | admin:cash_cashregister_history |
| /admin/cash/cashregister/<path:object_id>/delete/ | admin:cash_cashregister_delete |
| /admin/cash/cashregister/<path:object_id>/change/ | admin:cash_cashregister_change |
| /admin/cash/cashregister/<path:object_id>/ | admin: |
| /admin/cash/cashshift/ | admin:cash_cashshift_changelist |
| /admin/cash/cashshift/add/ | admin:cash_cashshift_add |
| /admin/cash/cashshift/<path:object_id>/history/ | admin:cash_cashshift_history |
| /admin/cash/cashshift/<path:object_id>/delete/ | admin:cash_cashshift_delete |
| /admin/cash/cashshift/<path:object_id>/change/ | admin:cash_cashshift_change |
| /admin/cash/cashshift/<path:object_id>/ | admin: |
| /admin/^(?P<app_label>auth\|identity\|catalog\|inventory\|cash)/$ | admin:app_list |
| /admin/(?P<url>.*)$ | admin: |

## Dependencias y enlace hacia planificación

| Origen → efecto | Fuentes precisas | Etapas y comprobación pendiente |
|---|---|---|
| Cuenta/rol/sesión → cada acción y propietario | `identity/models.py:58`, `authorization.py:17`, `services.py:31`, `:64` | 01–02; después repetir acceso directo en cada módulo y 15 |
| Categoría activa → producto activo/vendible | `catalog/models.py:35`, `catalog/services.py:12`, `:26`, `:36` | 03; impacto en carga, consulta y venta en 05/07/10/14 |
| Producto registrado sin lotes → todavía sin stock vendible | `catalog/models.py:106`, `:112`, `:122` propiedades de stock; `inventory/models.py:16`, `:37` | 03 → 05 → 10; el alta no reemplaza la carga inicial |
| Carga inicial/lotes → cantidades, costo promedio y vencimiento | `inventory/services.py:67`, `:134`; `inventory/models.py:37` | 05 y 07; fechas Lima, normalización y rechazo atómico pendientes |
| Proveedor → entrada posterior → lote y costo | `inventory/services.py:161`, `:182`, `:314`; `inventory/models.py:113` | 04 y 06; proveedor inactivo, carga previa y constancia de reposición pendientes |
| Merma/ajuste → lote, costo, movimiento consultado | `inventory/services.py:196`, `:260`; `inventory/views.py:387` | 08; el índice de movimientos no acredita saldo ni historias de bajas/ajustes completas |
| Caja activa CAJA-01 → turno vendedor → borrador | `cash/services.py:15`, `sales/services.py:35`, `:77` | 09–10; datos de caja y límites de concurrencia pendientes |
| Borrador → cobro → venta, correlativo, FEFO y efectivo | `sales/services.py:194`, `:295`, `:343`, `:377` | 11; idempotencia y concurrencia requieren pruebas propias, PostgreSQL cuando corresponda |
| Venta confirmada → constancia/historial y cierre | `sales/views.py:261`, `:275`, `:299`; `cash/services.py:43` | 09/12; administrador vs vendedor propietario; no comprobante fiscal |
| Catálogo/inventario/ventas → resumen del panel | `identity/views.py:183` | 13; panel diario no demuestra HU-REP-01 por rango/medio de pago |
| Settings/entorno/migraciones → todas las funciones | `config/settings.py:7`, `:20`, `config/env.py:11`, `:51`; manifiesto complementario | 00/15; comprobar DB efectiva, no usar APP_ENV=test solo como garantía de aislamiento |

Mapa de búsqueda, no aprobación: identidad se enlaza con AUTH/USR/VEN-01a; catálogo con CAT/PROD; inventario con PROV/INV/PROD-06; caja con CAJA; ventas con VEN; resumen con REP. El anexo `ETAPA-00-planificacion.md` determina selección R1, posterior, adicional o conflicto para cada HU/CA. No asignar el descuento a HU-VEN-03 (PDF/correo fuera de horizonte), ni preparación de borrador a HU-VEN-01a (bloqueo inactividad). Los alias de confirmación, shell base, errores y admin carecen de una HU autónoma validada: vincularlos como soporte técnico o proponer requisito, sin crear HUs ficticias por cada botón.

## Cursor exacto y trabajo no ejecutado

1. Mantener este inventario congelado como corte 05/11, cotejado 09/11. El informe principal enlaza la evidencia nueva de navegador; no sobrescribir `NO EXAMINADO` masivamente por haber pasado un arranque.
2. Primera revisión funcional: etapa 01, `HU-AUTH-01`/`HU-AUTH-02`, campos `LoginForm.email/password` (`identity/forms.py:6`), ruta `/`, servidor `authenticate_active_account` (`identity/services.py:31`), modelo `LoginAttempt` (`identity/models.py:27`) y mensajes. Comparar cada CA, no trasladar cobertura histórica de `03`.
3. Para cada etapa siguiente expandir las ocurrencias CSV a una matriz de campo/salida con valor inicial, tipo, longitud, normalización, precisión, obligatoriedad, mensaje y persistencia; incluir variantes HTML dinámicas y errores de Django. Registrar las pruebas fronterizas como pendientes hasta ejecutarlas.
4. En etapa 15 revisar `/admin/login/` primero y documentar la decisión de superficie administrativa; después permisos staff/grupos/objeto, comandos de mantenimiento y concurrencia. Inventario de subrutas completo para el resolver guardado, inventario semántico del admin `NO EXAMINADO`.
5. Semillas, reset, migraciones reversibles, restauración, despliegue, SUNAT, pagos digitales, reportes futuros y normas: no ejecutados ni aprobados por este anexo. Ningún módulo funcional se cierra aquí.

