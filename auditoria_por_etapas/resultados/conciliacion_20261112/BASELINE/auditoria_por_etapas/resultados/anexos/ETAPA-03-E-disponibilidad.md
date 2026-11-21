# Etapa 03-E · Disponibilidad de productos y repetición del cambio de estado

09/11/2026, America/Lima. **Auditoría del sublote ejecutada, con límites explícitos.** Los tres criterios de HU-PROD-05 cumplen en la muestra final. El estado de categoría sigue siendo una ampliación implementada sin HU dedicada aceptada. Este corte completa la revisión de los 27 criterios base de etapa03: 18 CUMPLE en la muestra, 1 PARCIAL, 2 CONFLICTO DE FUENTES y 6 PREVISTO/FUTURO. No significa conformidad total del catálogo ni cierre de inventario, ventas o seguridad.

## 1. Inventario previo y trazabilidad

Se leyó completo el protocolo y el estado general; se conservaron los sublotes anteriores y los cambios preexistentes. [Inventario previo de 03-E](../evidencias/03-E-inventario-20261110T031347695888Z.json) registra criterios, acciones, campos, fuentes, hashes y estado Git. La ampliación acotada al reintento de categoría quedó [inventariada antes de corregirse](../evidencias/03-E-categoria-alcance-20261110T032613381136Z.json). El libro XLSX conserva el papel histórico descrito en la matriz; no se abrió ni modificó.

`08` es Historias de Usuario; `07`, Reglas; `09`, Backlog; `16`, Task Breakdown; `03`, Matriz de Trazabilidad de la raíz. HU-PROD-05 está en 08:249–256 y 09:69, adicional a R1 según CONTROL_SPRINTS:39. Su campo de RN en la HU está vacío; las relaciones con RN03/06/28/29/30 abajo son trazabilidad de esta auditoría, no una modificación silenciosa de la HU. Los agregados QA 08:874/876 respaldan el bloqueo de borrador/cobro y el ciclo de categoría. QA-FIX-CAT-01, QA-FIX-INV-01 y QA-FIX-SALES-01 (16:328–331) son tareas agregadas; este corte acredita solamente las acciones indicadas. S2-PROD05-AUTO identifica evidencia histórica, sin heredar su resultado ni declarar revisada una tarea inexistente en16.

| Criterio / fuente / actor | Acción y código | Esperado y observado | Evidencia final | Estado / prioridad / siguiente acción |
|---|---|---|---|---|
| PROD05/CA01 · 08:254 · ADMIN→VENDEDOR | Productos → Deshabilitar; `views.product_toggle_availability` → `services.toggle_product_availability` | Inactivo excluido de consulta de venta; búsqueda sin Agregar, actualizar cantidad y cobrar rechazan; borrador conserva dos unidades | E02–E07; Django efecto de disponibilidad y regresión SalesHistoryTests | CUMPLE muestra. P1 resuelto; carrera con cobro→15 |
| PROD05/CA02 · 08:255 · ADMIN→VENDEDOR/ALMACENERO | Habilitar → búsqueda de venta/selectores de inventario | Con categoría activa y lote vigente vuelve con 19 unidades y S/8,50. Sin stock, solo vencidos o categoría inactiva permanece fuera de venta | E12–E19, cuatro combinaciones de estados; E13/14 extremos | CUMPLE muestra bajo RN03 y QA876. P1; explicitar precondiciones en criterio propuesto |
| PROD05/CA03 · 08:256 · ADMIN/ALMACENERO; histórico autorizado | Catálogo, constancia y persistencia | Etiqueta exacta «Inactivo»; no borra ficha, lotes, borrador ni venta; constancia igual para vendedor dueño y ADMIN | E03/E10/E11/E28; snapshots de campos especificados | CUMPLE muestra tras corrección. P2; histórico ampliado→12 |
| Estado de categoría · 08:876, 16:328; PROP-E00-HU-02 | Categorías → Desactivar/Activar | Desactivar categoría no cambia banderas de productos. Reactivarla conserva producto individualmente inactivo | E15–E19; repetición E15-category-replay; PG-E05/06 | EXTRA SIN HU dedicada; comportamiento implementado y verificado; confirmación/decisión documental pendientes |

RN03: el artículo con cuatro unidades vencidas sigue sin oferta vendible. RN06: catálogo conserva cantidad vigente y mínimo; el resumen integral corresponde a07. RN28: se conserva la fotografía de la venta en los campos muestreados y en la constancia. RN29: ADMIN gestiona; ALMACENERO consulta y VENDEDOR consulta exclusivamente en su venta; peticiones directas denegadas. RN30: el borrador conserva sus líneas y el turno OPEN; no hay venta nueva por el rechazo. RN01 se usa como frontera de inventario, sin validar aquí las reglas completas de carga/reposición.

## 2. Superficies, entradas y salidas

| Superficie / entrada | Contrato actual y estado inicial | Mensaje, persistencia y cobertura |
|---|---|---|
| `/productos/`, fila y botones | ADMIN: Editar, Deshabilitar/Habilitar; ALMACENERO consulta. Producto inicial activo; categoría activa; precio8,50, mínimo10, vigentes19 | «Inactivo», «Disponible», «Categoría desactivada» o «Sin stock vigente» según condiciones. E01–04/E10/E12–19. El estado por sí solo no genera existencias |
| POST `/productos/<uuid>/disponibilidad/` | UUID de producto existente, CSRF, campo oculto `is_active`: texto exacto `true` o `false`. Deshabilitar envía false; Habilitar true. No es campo libre de precio/stock | ««nombre» ahora está activo/inactivo.»; inválidos vacío, yes y2: «Seleccione un estado válido para el producto.» y redirección sin cambios. E20–24 |
| Compatibilidad de servicio y petición antigua | Si falta `is_active`, se conserva alternancia; en servicio el argumento opcional es bool o None. Se lee fila actual bajo bloqueo transaccional | Repetir una petición antigua SIN estado sigue alternando. La garantía de reintento corresponde a los botones actuales con estado explícito. Django y PG-E03 verifican lectura de objetos antiguos |
| POST `/productos/categorias/<uuid>/estado/` | ADMIN; UUID+CSRF+estado explícito. Activa por defecto. No renombra, elimina ni reactiva automáticamente productos | «Categoría «nombre» ahora está activa/inactiva.»; `2` rechazado sin escritura; repetición conserva destino. Error de estado: «Seleccione un estado válido para la categoría.»; texto cotejado en código, conservación ejecutada en E15-category-invalid |
| `/productos/<uuid>/registrado/` y alias `/creado/` | Salida administrativa ya inventariada; datos actuales | Etiqueta inactiva alineada a «Inactivo». Este cambio de texto no tuvo recorrido visual independiente en03-E; catálogo sí. Alias y otras salidas tienen evidencia previa03-C |
| `/ventas/`, actualización de línea y `/ventas/cobrar/` | VENDEDOR dueño con turno OPEN; borrador ACTIVE2; tentativa cantidad3, efectivo30 | Actualizar: «El producto seleccionado no está disponible para la venta.». Cobro indica que el producto ya no está disponible y debe quitarse. E05–07; se conservan campos comerciales comprobados |
| `/inventario/entrada/`, `/inventario/carga-inicial/` | ALMACENERO; producto con carga y producto sin carga | Inactivos excluidos. Servicios `register_stock_entry` y `confirm_initial_load` rechazan objetos cargados antes de la suspensión, sin nuevas filas. E08/E09/E19 + Django |
| Constancia `/ventas/constancia/<uuid>/` | VENDEDOR dueño y ADMIN | Mismo texto de `#constancia-interna`, snapshots de nombre/código/precio/cantidad, antes y después. E11/E28 |
| Recarga, Atrás, móvil390×844 | Acciones de estado mediante POST→redirect→GET; tabla con desplazamiento horizontal | Recarga/Atrás no cambian estado. Botón alcanzable al desplazar tabla; no prueba exhaustiva de accesibilidad. E25–27 |

Servidor de producto: GET/PUT de ADMIN 405, UUID inexistente404, POST sin CSRF403; ALMACENERO y VENDEDOR reciben403 tanto en GET como POST directo; visitante GET302. Estos rechazos no cambiaron los campos comerciales observados. La matriz de permisos de categoría se ejecutó en03-A y sus regresiones están incluidas en82 métodos. No se extrapolan estos códigos a todas las rutas del sistema.

## 3. Defectos reproducidos y cambios

| ID / severidad | Antes | Corrección y resultado |
|---|---|---|
| FIX03E-01 · P1 · producto | Reenviar el formulario de Deshabilitar volvía a activar. Dos objetos con estado antiguo también aplicaban una alternancia equivocada | Estado objetivo oculto, validación de servidor y lectura con `select_for_update`; guardar solo si cambia. Reenvíos conservan estado y `updated_at`; llamadas antiguas leen estado fresco. E04, Django, PG-E01/02/03 |
| FIX03E-02 · P2 · mensajes | «Producto deshabilitado» difería de CA03. «Ahora está disponible» se mostraba al habilitar incluso sin stock/categoría activa | Etiqueta «Inactivo» y mensaje «activo/inactivo». Las filas explican la disponibilidad efectiva. E03/E10/E12/E13/E17 |
| FIX03E-03 · P1 · categoría | Reenviar Desactivar reactivaba el grupo. Se reprodujo tras corregir producto | Mismo contrato de estado objetivo, validación y bloqueo de fila. E15-category-replay, Django y PG-E05/06. Implementa la parte de reintento de PROP-E00-HU-02; no implica aceptar la HU propuesta completa |

Archivos modificados respecto al manifiesto03-E: `catalog/services.py`, `views.py`, `templates/catalog/category_list.html`, `product_list.html`, `product_created.html` y expectativa de etiqueta en `test_audit03_catalogue.py`. Nuevo `catalog/test_audit03_availability.py`: ocho métodos. Sin cambios de esquema en03-E. Se conservaron los arreglos de03-A/B/C/D y las modificaciones ajenas preexistentes.

`git diff --check` del repositorio completo detectó líneas vacías finales en `catalog/forms.py:178`, `identity/static/identity/app.css:805` e `identity/tests.py:537`; esos archivos conservan el hash previo a03-E. Es un límite de formato preexistente en este corte, no una prueba funcional fallida ni una verificación limpia del repositorio entero.

## 4. Ejecuciones, entorno y conservación

Chrome157.0.8103.39 mediante Playwright, capturas PNG inspeccionadas, Windows y virtualenv del proyecto. SQLite nueva por ejecución con marca, cookies propias y prueba HMAC antes de ingresar; tres cuentas ficticias y visitante. No se carga `.env`. PostgreSQL18.4 en clúster nuevo propio, READ COMMITTED, detenido al acabar. No se migró ni escribió en la base original.

| Ejecución | Resultado y significado | Evidencia |
|---|---|---|
| Navegador inicial | 31 comprobaciones,23 positivas y8 negativas; varias reflejan el mismo defecto. Se restituyó la suspensión después del reintento fallido para continuar casos independientes | [Inicial](../evidencias/03-E-browser-20261110T031505677093Z/browser.json) |
| Django inicial | Seis métodos nuevos, siete fallos de aserción/subcasos | [Log](../evidencias/03-E-tests-20261110T032216300260Z/tests.txt) |
| PostgreSQL inicial | 3/4; falla objeto con estado antiguo. Coincidencia de resultado concurrente en esa ejecución no garantizaba reintentos | [Inicial PG](../evidencias/03-E-postgresql-20261110T032219634598Z.json) |
| Categoría, reproducción independiente | 33 comprobaciones,32 positivas; falla solo repetición de Desactivar | [Antes de FIX03E-03](../evidencias/03-E-browser-20261110T032528496946Z/browser.json) |
| Django final | **82/82 métodos**:81 de catálogo y una regresión de efecto en ventas. `check` y `makemigrations --check --dry-run` sin incidencias | [Resultado](../evidencias/03-E-tests-20261110T032641479670Z/result.json) · [Log](../evidencias/03-E-tests-20261110T032641479670Z/tests.txt) |
| Navegador/HTTP/ORM final | **34/34**, sin errores del soporte. Incluye solicitudes directas y observaciones ORM, no34 recorridos visuales independientes | [Casos](../evidencias/03-E-browser-20261110T033002861512Z/browser.json) · [Servidor y protección](../evidencias/03-E-browser-20261110T033002861512Z/result.json) |
| PostgreSQL final | **6/6**: dos solicitudes de desactivar y dos de activar, por producto y categoría; objetos antiguos; conservación de otros campos. Dos conexiones del mismo ADMIN sincronizadas antes de SELECT FOR UPDATE | [PG final](../evidencias/03-E-postgresql-20261110T033046250292Z.json) |

No sumar ejecuciones intermedias como cobertura independiente. La suite completa del proyecto quedó NO EJECUTADA. El test PG usa dos sesiones de la misma cuenta, no dos administradores con decisiones opuestas ni una carrera contra cobro/inventario.

Base final retenida: `datos/etapa03e-20261110T033002861512Z/audit.sqlite3`. Una categoría, tres productos, dos cargas y dos lotes:19 unidades vigentes tras la venta fixture y4 vencidas del segundo artículo. Una venta, una línea histórica; dos borradores y dos líneas (uno ACTIVE con2 y otro DISCARDED de preparación); turno OPEN. Las sesiones ficticias se conservan. Los estados comerciales regresaron a los valores de preparación; no se afirma cerrar turno o limpiar datos.

[Inicial](../evidencias/03-E-browser-20261110T033002861512Z/orm-initial.json) y [final](../evidencias/03-E-browser-20261110T033002861512Z/orm-final.json) comparan los campos enumerados en `audit03_run.snapshot`: identidad/nombre/clave/estado de categoría; identidad/ficha comercial de producto; cantidades de lotes; identidad/producto de cargas; estado/monto inicial del turno; importes de venta; snapshots y cantidad de línea; estado de borradores y cantidad/precio de líneas. 03-E añade código normalizado, clave de nombre y costo medio. No compara todos los campos de todas las tablas: `updated_at`, sesiones y registros técnicos quedan fuera; la prueba unitaria sí verifica que repetir el mismo estado de producto no reescribe `updated_at`.

Capturas inspeccionadas: [Inactivo](../evidencias/03-E-browser-20261110T033002861512Z/02-inactivo.png), [activo sin stock](../evidencias/03-E-browser-20261110T033002861512Z/13-activo-sin-stock.png), [rechazo al cobrar](../evidencias/03-E-browser-20261110T033002861512Z/07-cobro-denegado.png), [móvil](../evidencias/03-E-browser-20261110T033002861512Z/25-movil.png). La captura móvil contiene tres mensajes pendientes de tres peticiones inválidas deliberadas; no es evidencia de que una sola petición produzca tres errores.

La verificación de [cierre](../evidencias/03-E-cierre.json) comprueba hashes protegidos, alcance de cambios, resultados, puertos cerrados, enlaces y27 criterios únicos. Fechas de archivo UTC10/11 corresponden a la noche09/11 en Lima. Original, bases anteriores y XLSX conservados.

## 5. Reproducción

Desde la raíz, ejecutar en este orden, esperando que termine cada comando. Cada runner crea una base nueva y conserva las anteriores; ejecutarlos simultáneamente podría comparar el hash de una base mientras otro recorrido aún la modifica.

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03e_run.py' tests catalog sales.tests.SalesHistoryTests.test_bug033_and_bug037_inactive_category_or_product_blocks_search_draft_line_update_and_checkout
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03e_run.py' browser
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03e_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/cierre_etapa03e.py'
```

Los tres primeros producen nuevos archivos con marca UTC. El último verifica las evidencias fechadas enlazadas en este informe. Los verificadores de cierres anteriores conservan expectativas del código de su corte: no describen una regresión vigente para ejecutar contra modificaciones posteriores. En particular, el runner de navegador03-B conserva la expectativa de etiqueta anterior; su resultado histórico no se reescribió. Las 82 pruebas finales sí incluyen la expectativa nueva.

## 6. Propuestas, límites y continuidad

**PROP-03E-CA01 · propuesta documental para PROD05/CA02, no nueva HU.** Dado un producto inactivo, categoría activa y existencias vigentes positivas, cuando ADMIN solicita activarlo, entonces VENDEDOR dueño de turno lo consulta con precio vigente y existencias calculadas. Si categoría inactiva, stock cero o solo vencidos, la ficha queda activa, se explica la causa en catálogo y no se ofrece en venta. Permisos, errores y conservación según tablas anteriores. Implementación existente verificada; añadir precondiciones al criterio y referencias RN03/29, sujeto a aceptación documental.

**PROP-E00-HU-02 / CA propuesto03-B y PROP-E03-T01, actualización.** Reenvío de estado explícito implementado y verificado en productos y categorías; la parte técnica dejó de estar totalmente pendiente. Siguen propuestos confirmación con explicación de impacto, política ante dos decisiones opuestas y control de versión. Alternativas: A) aceptar que prevalezca el último estado serializado; B) exigir versión y avisar conflicto para decisión posterior. La UI actual aplica A por mecanismo técnico, sin declarar aceptada su política comercial. Los clientes antiguos sin destino explícito siguen alternando. Desplegar UI y servidor conjuntamente; decidir aparte retirar la compatibilidad.

**PROP-03E-TEST01 · ampliación pendiente de pruebas transversales.** Carrera de suspensión/activación contra cobro y entrada de inventario, dos administradores distintos con intenciones opuestas, caída/reintento entre servicios y muestreo de todas las tablas históricas →15 y12. No fueron ejecutadas. Lector de pantalla físico, otros navegadores, carga/volumen y escáner físico quedan sin ejecutar; escáner es futuro. Edición/eliminación de categoría continúa futura; administrar estado no las implementa. La administración técnica Django corresponde a15.

**Cursor de continuidad03-F / DOC03-01 / HU-PROD-02 CA01 (08:218, contraste08:876 y16:328).** Resolver si se mantiene enlatados, se acepta cualquier producto por unidad con vencimiento o se planifica venta general con otros modelos. Alternativas y consecuencias en ETAPA-03 §6; luego DOC03-02/PROD04-CA03 (08:243 frente a08:872), PROP-03C-LIMITES y PROP-03C-NOMBRE. Registrar decisión antes de modificar alcance o ampliar restricciones. Las tareas independientes de los cinco sublotes ya tienen resultado; estos pendientes no se sustituyen por una aprobación automática. Etapas04–17 conservan su estado.
