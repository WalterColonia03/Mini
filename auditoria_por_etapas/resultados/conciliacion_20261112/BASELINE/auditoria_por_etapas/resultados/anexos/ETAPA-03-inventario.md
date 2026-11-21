# Etapa 03 · Inventario inicial y trazabilidad conciliada hasta 03-X

09/11/2026, America/Lima. Se inventarió antes de cambiar código. [Captura inicial, textos exactos y hashes](../evidencias/03-inventario-20261110T000729019055Z/inventory.json). Las referencias `08`, `07`, `16`, `03`, `02`, `09`, `21` corresponden a los documentos numerados de la raíz; no a etapas. Las líneas del código en el JSON son **anteriores** a las correcciones; se usan también símbolos estables.

## Fuentes, vigencia y alcance

Se leyó completo el protocolo y el estado general, y el traspaso de02. No hay AGENTS.md aplicable en las carpetas del tramo ni en los antecesores comprobados. El repositorio está en `r1-pmv`, no en la raíz. Su estado previo, HEAD y hashes están capturados; la sesión no parte de un árbol limpio y no atribuye cambios antiguos a esta auditoría.

| Fuente precisa | Papel en esta etapa | Clasificación |
|---|---|---|
| 01:17,94,126,134; 09:34–54; 14:66,76 | R1 selecciona PROD-02, enlatados, categoría preparada, unidad UND y vencimiento | Línea base histórica seleccionada; DOC03-01 resolvió el alcance actual en03-F, preservando R1 |
| 08:161–256 | Nueve HU y 27 CA base | Inventario individual abajo; no son nueve HU completadas |
| 09:65–69; CONTROL_SPRINTS:35–39 | CAT01/02 y PROD01/04/05 declaradas implementadas después de R1 | Implementado adicionalmente; etiquetas históricas no acreditan cumplimiento |
| 09:125–127 y adenda03-O | CAT03/04 y PROD03 sin release histórico | CAT03/04:4CA futuros. PROD03 seleccionado ahora por pedido de mejoras; no modifica Sprint histórico. |
| 08:872,874,876; 16:328; 03:280,282,285,289,297,304,307,309 | Agregados QA: código editable/snapshot, disponibilidad en borrador, categorías activas | Afirmaciones separadas; no sobrescriben los ordinales de los CA base |
| 21:11–14; 02:84–98; 07:333–350 | Roles y superficies | ADMIN gestiona, ALMACENERO consulta; VENDEDOR consulta en venta. Este es también el alcance explícito del pedido actual |
| 02:105–106,160 | Modelos y unicidad normalizada de categoría/producto | Restricciones técnicas actuales; no confundir con clasificación comercial del producto |
| 03:73–83 | Cinco CA de PROD02 con tareas AT/MT/CT/ST | Matriz R1, no matriz completa de catálogo actual |
| `evidencias/HU-CAT-01/S2-CAT01-AUTO`, `HU-CAT-02/S2-CAT02-AUTO`, `HU-PROD-01/S2-PROD01-AUTO`, `HU-PROD-04/S2-PROD04-AUTO`, `HU-PROD-05/S2-PROD05-AUTO` | Evidencia histórica de tareas y estados | No se heredan sus resultados; la nueva ejecución está en el informe |

**Libro XLSX:** no se abrió ni modificó en03. Se inventarió su papel desde `ETAPA-00-fuentes.md:56–77`: corte interno OOXML 05/11/2026 00:10:21–22 Lima; cuatro hojas, 28 HU declaradas implementadas, 46 pendientes, 97 ordinales; representa el corte de planificación de esa fecha. Hash comprobado en el corte inicial03-A, entonces igual al inventariado (el XLSX estaba ausente al cierre03-W): `a9604b90d08dead7b815817f859004a802353aaf6f91f7e78a4467fa18406b49`. Sus estados no prueban funcionamiento. Revisión de contenido/fórmulas/formato NO EJECUTADA en03; no se usó como fuente normativa nueva.

## Cada HU y criterio

ADMIN realiza las acciones de gestión. Cada fila identifica las consultas de otros roles. B remite al navegador de 03-A. Los casos C están en los anexos 03-B y 03-C, y D en el anexo 03-D. T indica Django y PG indica PostgreSQL. E remite al anexo03-E de disponibilidad. La revisión funcional de la muestra concluye con decisiones de alcance abiertas.

| ID / fuente exacta | Requisito y ubicación | Esperado → observado / evidencia | Estado de auditoría | Prioridad / siguiente acción |
|---|---|---|---|---|
| CAT01/CA01 · 08:166 | Lista todos los nombres; `category_list` / `category_list.html` | Vacía→con filas activas/inactivas; orden normalizado; T lista, B03/B13 | CUMPLE muestra | P2, volumen/Unicode fuera de muestra |
| CAT01/CA02 · 08:167 | Mensaje de lista vacía | «No hay categorías registradas.»; T lista, B01/captura | CUMPLE muestra | Sin pendiente del caso |
| CAT02/CA01 · 08:176 | Nombre no vacío, retirar espacios, activo y utilizable; form→service→model | Antes guardaba espacios interiores; después normaliza y B14b usa la categoría para alta real | CUMPLE muestra tras FIX03-01 | P1, DOC03-01 resuelto por usuario en03-F |
| CAT02/CA02 · 08:177 | Duplicado por mayúsculas/espacios → «La categoría ya existe», sin fila | Antes duplicados interiores/error500 en carrera; T duplicados, B04/B14 y PG03-01 corrigen ambos | CUMPLE muestra tras FIX03-01/03 | P1, migración sobre base real no aplicada |
| CAT02/CA03 · 08:178 | Vacío → «El nombre es obligatorio», sin fila | Antes texto distinto/POST vacío sin error; T vacío, B05/B09 | CUMPLE muestra tras FIX03-02 | P2, lector de pantalla real no ejecutado |
| CAT03/CA01 · 08:187 | Renombrar y reflejar en productos | Sin ruta/acción comercial de edición; existe admin técnico genérico | PREVISTO/FUTURO | P3, decidir incorporación; admin→15 |
| CAT03/CA02 · 08:188 | Nombre de otra categoría → rechazar edición | No hay formulario comercial de edición | PREVISTO/FUTURO | P3, no confundir alta duplicada con editar |
| CAT04/CA01 · 08:197 | Eliminar vacía y desaparecer | Desactivar conserva fila; no es eliminación | PREVISTO/FUTURO | P3, proteger referencias si se implementa |
| CAT04/CA02 · 08:198 | No eliminar vinculada, mensaje exacto | FK `Product.category` PROTECT; no prueba del CA de UI; admin genérico no auditado | PREVISTO/FUTURO | P3, no aprobar por inspección de FK |
| PROD01/CA01 · 08:207 | ADMIN y ALMACENERO consultan nombre, código, categoría, precio y existencias | C02/C03/C13 y PG03B-stock-dates. Se añadió cantidad vigente. En el caso mixto se muestran 9 de 62 unidades físicas | CUMPLE muestra 03-B | P1 corregido. DOC-00-14 conciliado en03-F con instrucción del usuario |
| PROD01/CA02 · 08:208 | Buscar por nombre o código y recuperar la consulta | C04–C11/C14. Búsqueda parcial, nombre con mayúsculas acentuadas, código normalizado, vacío, caracteres literales, error, recarga y Atrás. PG confirmó nombre previo a la migración | CUMPLE muestra 03-B | P2 corregido. Aplicar 0004 al desplegar |
| PROD01/CA03 · 08:209 | Mostrar alerta si las existencias vigentes son iguales o inferiores al mínimo | C03. Con mínimo 10 aparece en 0, 9 y 10 unidades. Desaparece en 11. Los casos con mínimo 0 y 3 confirman que se usa el umbral propio | CUMPLE muestra 03-B | P1 corregido. El inventario consolidado se verifica en 07 |
| PROD02/CA01 · 08:218 revisado DOC03-01 | Cualquier categoría activa, UND/vencimiento; nombre único normalizado (aceptado10/11) | Decisión expresa del usuario. 03-F C04/C16 guardan en enlatados/Higiene; C09/C21 rechazan categoría inválida y F02 rechaza KG; C17 conserva controltrue 03-I I01–03/I06 y PG-I04/06 verifican nombres; | CUMPLE muestra 03-F/I | P1 DOC03-01 y PROP-03C-NOMBRE resueltos; despliegue pendiente |
| PROD02/CA02 · 08:219 | Soles finales con IGV, positivos y máximo dos decimales | C04/C05 guardaron 8.50 y mostraron S/ 8,50. C09/C16/C17 acreditan extremos y rechazos sin escritura | CUMPLE muestra 03-C | P1. Cálculo de impuesto al cobrar corresponde a 11 |
| PROD02/CA03 · 08:220 | Código normalizado irrepetible | C07/C09/C18 y PG-C01/C02. Dos inserciones equivalentes en PostgreSQL dejaron un producto y un error de campo | CUMPLE muestra 03-C | P1. Nombres homónimos tratados en PROP-03C-NOMBRE |
| PROD02/CA04 · 08:221 revisado10/11 | Entero0..999999; alta vacía/omitida10 | Decisión aceptada;03-I H01–04/H07–09,91 métodos y PG-I07: formulario/servicio/base rechazan1000000; FIX03H-01 conserva rechazo de fracciones | CUMPLE muestra 03-I | P2 PROP-03C-LIMITES resuelta; despliegue0005 pendiente |
| PROD02/CA05 · 08:222 | Alta con stock cero y acceso solo ADMIN | C11–15/C17 y PG-C03. Almacenero vio cero y vendedor con turno no pudo agregar. Ambos recibieron cuatro 403, sin cambios en datos comerciales | CUMPLE muestra 03-C | P1. Alta y consulta probadas en datos aislados |
| PROD03/CA01 · 08:231 y adenda 08:912 | Llenar el campo temporal al leer y copiar mediante «Usar código» | Prueba física K9/P/Z. En Z el segundo interno sustituyó al primero | CUMPLE en muestras. Redacción alineada con la adenda aceptada | [03-Z](ETAPA-03-Z-relectura-interna.md) |
| PROD03/CA02 · 08:232 | Duplicado advertido al leer | En 03-Y la lectura UPC12 reconoció el EAN13 registrado. El diálogo bloqueó la copia. Servidor y base cotejados | CUMPLE en muestras literales y de GTIN admitido | [Resultados y límites](ETAPA-03-Y-identidad.md) |
| PROD04/CA01 · 08:241 | Nuevo precio hacia adelante, pasado conservado | D03–10/D29. S/ 8,50 histórico, S/ 9,20 actualizado. Aviso y nueva confirmación antes de cobrar S/ 18,40 por dos unidades | CUMPLE muestra 03-D | P1. 03-R probó refresco/cobro en muestras; demás carreras→15 |
| PROD04/CA02 · 08:242 | Umbral actualizado al editar | D11. Con 17 vigentes, mínimo17 activa alerta y mínimo16 la retira en catálogo de almacenero | CUMPLE muestra 03-D | P1. Resumen de inventario →07 |
| PROD04/CA03 · 08:243 revisado DOC03-02 | ADMIN corrige el código único conservando identidad e históricos | Muestras G/Y. En Z, clasificación solapada rechazada en ambos sentidos sin alterar los historiales. Clasificación válida reservó la variante libre | CUMPLE en muestras | [03-Z](ETAPA-03-Z-relectura-interna.md) |
| PROD04/CA04 · 08:244 revisado10/11 | Nombre actualizado y único normalizado, históricos conservados | D12–14;03-I I04/05/07/08 y PG-I05/08: propio nombre permitido, duplicado rechazado con rollback y snapshot de venta conservado | CUMPLE muestra 03-I | P2 PROP-03C-NOMBRE resuelta; despliegue pendiente |
| PROD04/CA05 · 08:245 | Reclasificación de categoría | D17/D21/D25/D26 y PG-D03/D04. Otra activa aceptada, otra inactiva rechazada, categoría actual inactiva conservada | CUMPLE muestra 03-D | P1. Reclasificación y carreras adicionales verificadas en03-N/U/V; demás intercalaciones→15 |
| PROD05/CA01 · 08:254 | Inactivo excluido de mostrador | E02–07: búsqueda excluye, actualizar/cobrar rechazan; borrador ACTIVE2 y lote19 conservados | CUMPLE muestra 03-E | P1. 03-M probó suspensión frente a cobro/entrada; otras carreras→15 |
| PROD05/CA02 · 08:255 | Reactivar con categoría activa y stock vigente positivo habilita oferta con precio actual | E12–19 y K, cinco fichas, incluida caducidad hoy y lotes mixtos. Vendedor ve 19 a S/ 8,50 en una sola | CUMPLE muestra 03-E y 03-K | PROP-03E-CA01 aceptada. 03-M cubre suspensión/cobro en muestra; otras carreras→15 |
| PROD05/CA03 · 08:256 | Etiqueta Inactivo e historial conservado | E03/E10/E11/E28: etiqueta corregida; constancias ADMIN/vendedor y campos comerciales conservados | CUMPLE muestra 03-E | P2. Todos los históricos/tablas→12 |

Balance 03-Z: 23 CUMPLE en muestras y 4 PREVISTO/FUTURO. [Alcance, relecturas y continuidad](ETAPA-03-Y-identidad.md).

## Reglas y tareas identificadas · corte histórico 03-A

Las acciones de la tabla siguiente describen 03-A, no el estado actual. Para evidencia y pendientes vigentes, ver [03-W](ETAPA-03-W-conciliacion.md).

| ID / fuente | Función y estado03-A | Acción pendiente |
|---|---|---|
| RN01 · 07:13; inventory services | Cargas/entradas bloqueadas por categoría inactiva, prueba directa nueva; regla integral fuera03 | Etapas05/06 |
| RN03 · 07:70–76 | R1 enlatados y vencimiento obligatorio; datos aislados con lote futuro | DOC03-01; vencimiento completo→07 |
| RN06 · 07:102–108 | Umbral10 configurable y alerta vendible≤mínimo | NO EJECUTADO integral, cursor PROD01/CA03 |
| RN27 · 07:309; RN30 · 07:371 | Precio con IGV; 18% es regla local del sistema, no verificación legal | Precio→03-C; cálculo/cobro→11; normativa→16 |
| RN28 · 07:40, sección RN28; 08:872 | Confirmación e historial inmutable | Un snapshot/constancia preservados por cambio de categoría, PARCIAL transversal |
| RN29 · 07:333–350 | Gestión ADMIN y separación de roles | Categorías navegador/HTTP/servicios verificados; producto pendiente |
| DB-C02 · 02:160 | Clave normalizada única | Duplicado secuencial, carrera real PG y migración colisión probados |
| S1-DB-01/02/03/04 · 16:60–63 | Modelo, migraciones, restricciones y seeds | Migración propia ejecutada solo aislada; no ejecutar seeds contra base del usuario |
| S1-PROD02-UI · 16:104 | Seis campos accesibles y mensajes | Inventariado; solo alta B14b, no verificación completa |
| S1-PROD02-SVC · 16:105 | Validación/permiso/default/stock/categoría sembrada | Conflicto de alcance; regresión no cierra tarea |
| S1-PROD02-AUTO · 16:106 | Registro y fronteras | `catalog.tests` reejecutado; sin atribuir CI ni concurrencia producto |
| S1-PROD02-MAN · 16:107 | Todos los CA con categoría preparada | NO EJECUTADO integral |
| S1-PROD02-REV · 16:108 | Revisión independiente | NO EJECUTADO: esta sesión no es revisión por otro agente/persona |
| S2-CAT01-AUTO, S2-CAT02-AUTO | Referencias históricas en carpetas de evidencia | Nueva cobertura listada en informe; vacío/espacios/mensajes/carrera faltaban en evidencia acotada anterior |
| S2-PROD01-AUTO, S2-PROD04-AUTO, S2-PROD05-AUTO | Referencias históricas en carpetas de evidencia | PROD-01 se verificó en 03-B. Edición y estado siguen pendientes de auditoría visual |
| S2-CAT02-SVC; S2-PROD04-SVC/UI · 03:280,285,297 | IDs citados por matriz QA | No se inventan subtareas/horas ausentes de16; documentar enlace verificable |
| QA-FIX-CAT-01 · 16:328 | Ciclo de categoría, código, límites, seed, búsqueda, alias | PARCIAL de esta ejecución; no dar por aprobado el conjunto |
| QA-FIX-INV-01, QA-FIX-SALES-01 · 16:329,331 | Dependencias de categoría sobre entradas/venta | Solo fronteras03-A verificadas; no cierra05–12 |

## Rutas, pantallas, acciones y salidas · corte histórico 03-A

**HISTÓRICO:** las rutas, textos y acciones siguientes describen el inventario previo. El mapa actual de 12 patrones/9 plantillas y las confirmaciones posteriores están en [03-W](ETAPA-03-W-conciliacion.md).

Prefijo comercial `/productos/`. Diez patrones, nueve del alcance03 y uno derivado a07; siete plantillas, seis de03. `A` ADMIN, `L` ALMACENERO, `V` VENDEDOR. En03-A se probó en categorías denegación directa GET/POST para L/V y redirección de visitante; no extrapolarla al resto de rutas.

| Superficie y archivo/símbolo | Rol / método y acciones | Salidas/textos y respaldo | Estado03-A |
|---|---|---|---|
| `/categorias/`, `views.category_list`, `category_list.html` | A GET; + Nueva categoría; Activar/Desactivar | Título Categorías; Nombre/Estado/Acciones; Activa/Inactiva; lista vacía; ayuda «activas… inmediatamente… nuevos productos» | CAT01 verificada; estado extra respaldado por QA876, propuesta E00-HU02 |
| `/categorias/nueva/`, `category_create`, `category_form.html` | A GET/POST; Guardar, Cancelar→lista; foco nombre | Nueva categoría; ayuda registrar/editar; error junto al campo; éxito «Categoría «…» creada correctamente.» | CAT02 verificada en muestra |
| `/categorias/<uuid>/estado/`, `category_toggle` | A POST; alterna sin estado objetivo ni confirmación; GET405/UUID ausente404 | «Categoría «…» ahora está activa/inactiva.»; mantiene fila y vínculos | EXTRA SIN HU dedicada; QA876 implementado y efectos comprobados; repetición/confirmación pendientes |
| `/`, `product_list`, `product_list.html` | A/L GET; Buscar, limpiar ✕; A Editar/Deshabilitar/Habilitar | Nombre, Categoría, Código, Precio(S/), Stock mínimo, Disponibilidad, Acciones. «Producto deshabilitado», «Categoría desactivada», «Disponible», «Sin stock vigente». Vacío y sin coincidencias | PROD01/05; B20 solo frontera categoría. Consulta de vendedor en esta ruta fuera del alcance de roles pedido |
| `/nuevo/`, `product_create`, `product_form.html` | A GET/POST; Registrar producto; volver/cancelar→inicio | «Registrar producto enlatado»; cero existencias/no disponible; panel UND, IGV, mínimo10; fecha/costo/cantidad por lote | PROD02; B14b prueba uso de categoría y revela conflicto de alcance |
| `/<uuid>/registrado/` y `/<uuid>/creado/`, `product_created`, `product_created.html` | A GET, dos rutas misma salida; registrar otro/ver catálogo/ir inicio | Código,categoría,precio,mínimo,stock físico,disponibilidad actual; registro creado con cero, datos actuales | PROD02/CA05 + extra alias QA023; B14b usa ruta registrada; alias solo regresión |
| `/<uuid>/editar/`, `product_edit`, `product_edit.html` | A GET/POST; Guardar cambios, Cancelar→catálogo | Nombre actual; campos; errores; «Producto «…» actualizado.» | PROD04; código editable entra en DOC03-02. NO EXAMINADO en navegador03-A |
| `/<uuid>/disponibilidad/`, `product_toggle_availability` | A POST; alterna; mensaje ««…» ahora está activo/inactivo.» | PROD05; petición no contiene estado objetivo | NO EXAMINADO profundo; repetir/reintentar y concurrencia pendientes |
| `/vencimientos/`, `product_expirations.html` | A/L GET; días y Filtrar | Fecha corte, ayuda FEFO, Producto/Categoría/Lote/Proveedor/Vence/Cant./Estado; Vencido/Próximo; vacío; error días inválidos/default30 | NO APLICA a sublote03-A: pertenece07/PROD06; patrón inventariado, no aprobado |
| Menú `identity/base.html:32–39,83–84`; tarjetas dashboard:43–52 | A Productos/Registrar/Categorías; L Catálogo; V Preparar venta | Nombres y enlaces diferenciados por rol | Navegación categorías/consulta L/venta V ejecutada, B01/B12/B15 |
| `/admin/catalog/category/` y subrutas Django admin | Cuenta staff/superuser técnica; listado, alta, cambio, borrado y acciones genéricas | `catalog/admin.py::CategoryAdmin`; sin flujo comercial CAT03/CAT04 | EXTRA superficie técnica, NO EJECUTADO; etapa15. No equiparar rol ADMIN comercial a is_staff |
| `/admin/catalog/product/` y subrutas Django admin | Cuenta técnica; filtros/búsqueda/cambio/borrado genéricos | ProductAdmin; readonly normalizado/control/costo/fechas; FK protegidas | NO EJECUTADO,15; no declarar equivalencia con permisos comerciales |
| `/ventas/`, actualización línea, `/ventas/cobrar/`, constancia | V propietario; nombre/código/stock/precio en búsqueda autorizada | Categoría inactiva excluye búsqueda, rechaza modificar/cobrar; constancia conserva nombre/código/precio | B15–B18/B21; solo frontera, no cierre10–12 |
| Inventario carga inicial/entrada y catálogo L | L consulta y selectores; servicio valida categoría fresca | Inactiva se excluye; petición directa a servicios no guarda | B19/B20 y T efectos; no cierre05/06/07 |

Las rutas UUID también son entradas manipulables; categoría sin UUID válido no resuelve, UUID inexistente404. Formulario tiene CSRF oculto (no dato de negocio), validación de servidor y escape HTML; sin token403 comprobado en tests. No se guardaron tokens en capturas/informes.

## Campos: contrato identificado en 03-A, no aprobación actual

**HISTÓRICO:** para cambios de normas de nombre, mínimo, estado, control de versión y captura, ver [03-W](ETAPA-03-W-conciliacion.md) y anexos enlazados.

| Pantalla / campo | Etiqueta, propósito, inicial y obligatorio | Tipo/límites/normalización identificados | Error y persistencia / ejecución |
|---|---|---|---|
| Categoría `name` | Nombre de la categoría; organizar catálogo; vacío; requerido, autofocus | Texto hasta120; strip y colapso espacios Unicode; clave casefold hasta120; al menos letra/número | Vacío «El nombre es obligatorio»; duplicado «La categoría ya existe»; >120 error Django; clave expandida error normalizado. Se guarda nombre y clave, active=true. B02–B09, T y PG |
| Categoría `id` / `is_active` | UUID ruta; botón Activar/Desactivar; inicial true | UUID servidor; POST ignora `is_active` extra en alta; estado se alterna, no input editable | Denegados no cambian; conserva created_at/productos. Reintento no es operación idempotente: propuesta pendiente |
| Alta/edición producto `name` | Nombre del producto; alta vacío; edición actual; obligatorio | Texto160; colapso espacios; letra/número; duplicado iexact en formulario | «…debe contener letras o números» / «Ya existe un producto registrado con este nombre.»; modelo solo strip. B14b valor normal; resto pendiente |
| Alta/edición `barcode` | Código de barras; vacío/actual; obligatorio; inputmode numeric | Texto64; patrón ASCII letras/dígitos/espacios/guion; clave NFKC sin espacios+casefold; UNIQUE | Mensaje caracteres permitidos / «Ya existe un producto con este código de barras.». Editable en código, contradice CA04-03. Extremos/norm. pendiente |
| Alta/edición `category` | Categoría; select de UUID activo; alta sin selección; edición actual | Alta requerida; edición opcional (vacío conserva actual); actuales inactivas incluidas solo para preservar; otra inactiva rechazada | «Seleccione una categoría válida de la lista.»/«Seleccione una categoría activa.». FK PROTECT; B14b elección activa nueva; inactiva regresión, no UI completa |
| Alta `unit` | Unidad de medida; inicial UND; requerido | Select único Unidad(UND); CHECK unit=UND | Campo no aparece en edición. B14b UND; POST alterado pendiente |
| Alta/edición `sale_price` | Precio final con IGV(S/); vacío/actual; requerido | Decimal, step0.01, >0; formulario max9.999.999,99; modelo12 dígitos/2dec; rechaza e/E en formulario | «Mayor que cero…dos decimales»; «El precio no puede superar…»; no notación científica. B14b3,50; resto pendiente; sin aval fiscal |
| Alta/edición `minimum_stock` | Existencia mínima; alta inicial10, vacío→10; edición actual/requerida | Entero ≥0 y ≤999999 en formulario; step1; modelo PositiveInteger | Ayuda default10; negativos/decimal/máximo en regresión, nueva tabla valores pendiente |
| Producto `controls_expiration` | No editable, ayuda control obligatorio | true y CHECK; no opción sin vencimiento | B14b true; ámbito enlatado no se deduce de esta bandera |
| Producto `is_active`, stock, costo, fechas, UUID | Estado inicialtrue; stock derivado0; costo0; fechas servidor | No campos libres de alta; stock físico de lotes, vendible de fechas; disponibilidad requiere producto/categoría activos | Detalle creado muestra datos actuales. B14b0; lote de fixture19 después de venta; restante inventario pendiente |
| Catálogo `q` | Buscar por nombre o código; inicialvacío, opcional | GET texto sin max declarado en plantilla; strip; nombre icontains OR clave de código normalizada icontains | Preserva q; texto vacío/coincidencias y ✕ limpiar; sin auditoría de extremos03-A |
| Vencimiento `dias` | Próximos días; inicial30; control min1/max3650 | Entero GET; inválido aplica30 con mensaje, corte fecha local | Inventariado, NO APLICA sublote03-A→07 |

Mensajes exactos adicionales y cada línea de plantilla, modelo, formulario, servicio, ruta y prueba localizada se conservan en `inventory.json.surface` (524 localizaciones iniciales, no 524 requisitos aprobados). En el corte histórico03-A las pantallas de producto quedaron pendientes. Los resultados vigentes están en la conciliación siguiente y en los anexos03-B aE; admin técnico, futuros y pruebas transversales conservan sus exclusiones. Esto completa el mapa del tramo, sin afirmar ejecución exhaustiva de todos sus elementos.


## Conciliación histórica de superficies, campos, reglas y tareas · 03-E

**Corte03-E:** supersedido por las adendas F–W y la [conciliación vigente03-W](ETAPA-03-W-conciliacion.md).

Las tablas anteriores conservan la identificación previa03-A para no borrar lo que se observó antes de corregir. Esta tabla sustituye sus estados de ejecución pendientes cuando hay evidencia posterior; los contratos detallados por campo están en los anexos indicados. Las fuentes de alcance siguen clasificadas como R1, adicional implementado, futuro o conflicto en cada HU.

| Elemento identificado | Resultado posterior y evidencia | Pendiente o límite |
|---|---|---|
| Lista/búsqueda: q, precio, existencias, mínimo, disponibilidad, mensajes vacío/sin coincidencias/error | 03-B C01–C14:9 vigentes de62 físicas, umbral propio, normalización y conservación de consulta. Campo, reglas y extremos en anexo03-B | RN06 resumen completo→07; carga/volumen pendiente |
| Alta: nombre, código, categoría, unidad, precio IGV, mínimo, estado/control/stock/costo no editables | 03-C inventario por campo y casos por campo, fronteras HTML y servidor, error/foco/persistencia. S1-PROD02-UI/SVC/AUTO/MAN contrastadas en la muestra | Categoría/enlatados en conflicto, máximo del mínimo parcial, homónimos pendiente; revisión independiente S1-PROD02-REV no ejecutada |
| Confirmación registrada/creada, enlaces y salidas | 03-C alta/alias; muestra datos actuales. En03-E etiqueta inactiva cambia a Inactivo por coherencia | Variante inactiva de confirmación no recorrida visualmente en03-E; catálogo sí |
| Edición: nombre/código/categoría/precio/mínimo, errores y vuelta al catálogo | 03-D D01–D29; huella histórica y nuevo precio/código/umbral. S2-PROD04-SVC/UI/AUTO contrastadas; extremos y mensajes en anexo03-D | Código editable en conflicto; históricos con reutilización de códigos→12/15 |
| Estado de producto y categoría: UUID, CSRF, campo oculto is_active | 03-E: true/false explícitos, inválidos rechazados, botón repetido conserva estado. Servicio bloquea/lee fila actual; omisión mantiene alternancia antigua | Reintento garantizado para contrato explícito; dos intenciones opuestas y confirmación pendientes |
| Etiquetas y mensajes de estado | Inactivo exacto; «ahora está activo/inactivo» evita prometer disponibilidad. Producto activo bajo categoría inactiva sigue bloqueado | Capturas/efectos en03-E; no equivale a que todo producto activo pueda cobrarse |
| Menús ADMIN/ALMACENERO/VENDEDOR, permisos y acceso directo | Recorridos y denegaciones03-A aE: gestiónADMIN, consultaALMACENERO, venta autorizadaVENDEDOR | DOC-00-14 documental; admin técnico→15 |
| RN03/06/27/28/29/30 y RN01 como frontera | Disponibilidad/fechas, umbral catálogo, precio final, snapshots, permisos y conservación del borrador/turno ejecutados según anexos | No aprobación completa de reglas transversales ni legal/fiscal |
| S1-DB y DB-C02, PROP-E03-T02 | Unicidad y migraciones probadas en entornos propios; datos previos modelados en pruebas | Migraciones0003/0004 sobre base real no aplicadas |
| S2-CAT01/02, S2-PROD01/04/05-AUTO; QA-FIX-CAT-01 | Nuevos resultados03-A aE sustituyen inferencia basada solo en evidencias históricas | No certificar todas las acciones de QA-FIX-CAT-01; seed/costo demo y alcance integral fuera de pruebas de este corte |
| QA-FIX-INV-01 / QA-FIX-SALES-01 | Efectos de suspensión y cambios de catálogo comprobados en inventario/borrador/histórico | Auditorías05–12,14/15 siguen pendientes |
| Editar/eliminar categorías; escáner | CAT03/04 y PROD03 futuros, seis CA; no hay experiencia comercial equivalente acreditada | No aprobados por admin técnico o campo que acepta teclado |
| Vencimientos detallados, admin técnico y otras superficies transversales | Inventariados y derivados a07/15 | NO EJECUTADO como auditoría integral |

**Conciliación03-F.** DOC03-01 y DOC-00-14 resueltos: cualquier categoría activa por unidad y con vencimiento obligatorio; ADMIN/ALMACENERO en catálogo, VENDEDOR en venta autorizada. [Decisión,20 métodos y53 comprobaciones](ETAPA-03-F-alcance.md) · [Cierre](../evidencias/03-F-cierre.json). El único cambio de estado de CA es PROD02-CA01 por revisión aceptada; los conflictos históricos se conservan en sus anexos.

**Conciliación03-G.** DOC03-02 aceptado por usuario: ADMIN puede corregir código único manteniendo históricos. [Decisión y pruebas](ETAPA-03-G-codigo-y-lector.md) · [Lector elegido y trabajo pendiente](ETAPA-03-Barcode-to-PC.md) · [Cierre](../evidencias/03-G-cierre.json). Los seis CA futuros conservan esa clasificación: elegir Barcode to PC Server no demuestra captura física ni aviso inmediato de duplicado.

**Cursor vigente 03-K / HU-PROD-03 CA01 / PROP-03G-SCAN-T01.** Verificar lectura física en el alta aislada de un producto. Si el equipo no está disponible, registrar NO EJECUTADO y retomar PROP-03E-CA01 / PROD05-CA02.

**Conciliación03-H,10/11/2026.** FIX03H-01 corrige fracciones/bool/no finitos en validación de Product usada por alta y edición;24 métodos y27 comprobaciones finales. Máximo y homónimos continúan pendientes, sin respuesta a las consultas. No cambia la cuenta20/1/6; CA04 no se eleva a CUMPLE por la corrección parcial. [Campos, rutas, acciones, evidencia y propuestas](ETAPA-03-H-minimo.md) · [Cierre](../evidencias/03-H-cierre.json). Las superficies históricas anteriores mantienen su fecha y se interpretan con estos cortes posteriores.


**Conciliación03-I,10/11/2026.** Máximo999999 y nombres únicos aceptados/aplicados:91 métodos,36 comprobaciones navegador/HTTP/ORM,8 PostgreSQL. CA04 de mínimo pasa a CUMPLE muestra; refinamientos de nombre en CA existentes. Balance21 CUMPLE/6 futuros. Conciliaciones03-H y anteriores conservan historia de decisiones entonces pendientes. [Políticas, campos, evidencia y límites](ETAPA-03-I-politicas.md) · [Cierre](../evidencias/03-I-cierre.json). No hay aprobación global ni de otros módulos.

**Actualización 03-J.** Aceptada y verificada la confirmación de cambio de estado con impacto y rechazo de pantallas antiguas. Se sumó una ruta de lectura y una plantilla al inventario previo. Los cuatro criterios suplementarios J-CA1 a J-CA4 corresponden a PROP-E00-HU-02 y constan en la matriz de este sublote. El balance de los 27 CA base se conserva. [Superficies, entradas, salidas y evidencia](ETAPA-03-J-estado-categoria.md).

**Cursor vigente 03-K2 / HU-PROD-03 CA01.** Restablecer la conexión al servidor y probar Code 128 `00CAT03K`. La aclaración de HU-PROD-05/CA02 ya fue aceptada y verificada. [Sublote K](ETAPA-03-K-lector-y-reactivacion.md).


## Continuación 03-K2

El 10/11/2026 a las 12:58 Lima, después de que el usuario informó la conexión, la lectura física Code 128 llegó al campo ADMIN como 00CAT03K, con ocho eventos de entrada y ambos ceros iniciales. Se observó inmediatamente Enter, envío POST y navegación a la ficha registrada. La base aislada guardó exactamente un producto con ese código, precio 8.50, mínimo 10, UND y vencimiento obligatorio. HU-PROD-03/CA01 CUMPLE en esta muestra física. La propuesta de revisar antes de guardar queda pendiente de ajustar el perfil de salida. El perfil interno del lector y sus versiones después de la reconexión no se inspeccionaron. La prueba acredita el resultado de extremo a extremo en navegador y persistencia, con conexión informada por el operador. El servidor Django finalizó y todos los archivos protegidos conservaron sus hashes.

**Cursor 03-K3 / PROP-03G-SCAN-T01.** Configurar la salida del lector para enviar el código sin Enter y repetir una lectura física en alta nueva, verificando campo exacto, cero POST y cero productos hasta pulsar Registrar. Después abordar el aviso inmediato de duplicado de HU-PROD-03/CA02, que sigue previsto.


**Actualización 03-K4.** Perfil BARCODE sin Enter verificado en dos muestras. La lectura final acumuló dos copias del código. Cursor 03-K5 / PROP-03K-RELECTURA. [Resultados y propuesta](ETAPA-03-K4-perfil-y-relectura.md).


## Continuación 03-K5 · captura individual y alta explícita

10/11/2026, 13:14–13:16 Lima. El usuario aclaró que la versión móvil ofrece cámara y un botón de captura, sin opción visible Single scan. Esta interacción es suficiente para la prueba. En la base nueva el código físico 00CAT03K llegó con ocho eventos de entrada y dos ceros iniciales. Hasta confirmar el operador hubo cero Enter, cero Tab, cero POST y cero productos. Después de la confirmación humana, el soporte de auditoría pulsó explícitamente Registrar producto, observó la página de alta y comprobó un producto persistido con el código exacto. Se verificó así la separación temporal entre captura y guardado mediante acciones normales del formulario.

ALMACENERO entró desde Catálogo de productos y vio Higiene, precio 8,50, mínimo 10, cero unidades y Sin stock vigente, sin botones de gestión. VENDEDOR entró desde Preparar venta, con turno propio abierto, y buscó el código. La ficha sin stock no se ofreció. El servidor terminó y las bases protegidas y XLSX conservaron su hash. Las capturas y los registros JSON permiten reproducir y verificar estas observaciones. El clic de guardado lo ejecutó la automatización después de confirmar la captura física el usuario.

HU-PROD-03/CA01 CUMPLE en esta muestra de captura física y alta. El control de guardado explícito CUMPLE muestra. El usuario puede tomar varias capturas del mismo código. Se acreditó anteriormente que se concatenan en el campo enfocado. Releer con el campo vacío o su texto completo seleccionado evita añadir al valor previo. El reemplazo mediante una segunda lectura física queda NO EJECUTADO. La cadena concatenada puede cumplir el formato y ser única, por lo que no debe suponerse que la validación de duplicados la detectará como error de lectura. Ese riesgo se mantiene en PROP-03K-RELECTURA.

Cursor vigente **03-K6 / PROP-03K-RELECTURA**. Definir y verificar la interacción de reemplazo ante una segunda captura, conservando códigos legítimos y entrada manual. HU-PROD-03/CA02 sigue pendiente de selección e implementación de aviso inmediato al leer. La auditoría no modificó el código de la aplicación durante este corte. La planificación conserva los 27 CA base con 21 del alcance implementado que cumplen en muestras y seis previstos, uno de estos últimos con evidencia física favorable de CA01. Los cuatro criterios suplementarios de categoría conservan su evidencia previa.


[Evidencia física y guardado](../evidencias/03-K-physical-20261110T181416503086Z/physical.json) · [Persistencia final](../evidencias/03-K-physical-20261110T181416503086Z/orm-final.json).

**03-N/O,10/11/2026.** Matriz vigente actualizada arriba. CAT03/04 permanecen futuros. El XLSX, cuyo hash anterior se conserva como evidencia histórica, estaba ausente al comenzar las últimas ejecuciones. No se verificó su contenido actual. Ver [inventario ampliado de ruta, campos, estados y salidas](ETAPA-03-N-O-reclasificacion-y-duplicados.md).

**03-P,10/11/2026.** Aviso físico completado en muestra y cuatro migraciones aplicadas a copia nueva; fuente conservada. No se reatribuyen a P las pruebas históricas de los demás CA. Próximo cursor03-Q, reclasificaciones cruzadas y borrador multiproducto. [Inventario del sublote y evidencia](ETAPA-03-P-aviso-fisico-y-migraciones.md).

**03-Q,10/11/2026.** PROD04/CA05 conserva CUMPLE en muestra; se corrigió deadlock con cobro multiproducto, 5/5 carreras PG y 27/27 Chrome secuencial. Rama de refresco de precio queda NO EJECUTADA como carrera en 03-R. [Evidencia](ETAPA-03-Q-reclasificacion-cruzada.md).

**03-R,10/11/2026.** PROD04/CA01 conserva CUMPLE en muestra de precio y roles; refresco de precio verificado en tres carreras PG. Omisión de controles del resumen corregida; carrera entre vista y servicio NO EJECUTADA, cursor03-S. [Evidencia](ETAPA-03-R-precios-y-resumen.md).

**03-S,10/11/2026.** Se corrigió carrera de resumen web ante cambios de borrador; 3/3 casos PG y 23/23 comprobaciones secuenciales en navegador. Cambio concurrente de nombre/código ante resumen web pendiente03-T. [Evidencia](ETAPA-03-S-resumen-atomico.md).

**03-T,10/11/2026.** PROD04/CA03–05 y resumen de cobro: nombre/código cambiados requieren revisión en muestras PG; categoría activa permite cobro con resumen igual. Corregido aviso que atribuía el cambio a otra pestaña. [Evidencia](ETAPA-03-T-catalogo-y-resumen.md).

**03-U,10/11/2026.** PROD04/CA05 y estado de categoría: después de reclasificar, 2/2 órdenes suspensión/cobro PG y 35/35 comprobaciones secuenciales entre roles. Tres operaciones simultáneas siguen NO EJECUTADAS, cursor03-V. [Evidencia](ETAPA-03-U-categoria-y-cobro.md).

**03-V,10/11/2026.** PROD04/CA05 y PROP-E00-HU-02:3/3 intercalaciones controladas de servicios con edición, suspensión y cobro simultáneos; navegador secuencial03-U. Conciliación documental pendiente03-W. [Evidencia](ETAPA-03-V-concurrencia-triple.md).

**03-W,10/11/2026.** Conciliación vigente de27CA, cuatro suplementarios,12 rutas y9 plantillas, con límites y contradicción literal de CA01. Próximo cursor03-X. [Matriz](ETAPA-03-W-conciliacion.md).
