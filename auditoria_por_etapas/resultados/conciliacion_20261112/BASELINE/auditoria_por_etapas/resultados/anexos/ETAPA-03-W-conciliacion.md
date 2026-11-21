# 03-W · Conciliación vigente del catálogo

10/11/2026, America/Lima. Se leyó completo PROTOCOLO_COMUN y se conciliaron los cortes 03-A a 03-V, sin nuevas pruebas funcionales, cambios de aplicación ni conexión a la base original; solo se leyó su archivo para SHA256. Se preserva el [inventario inicial y matrices detalladas](ETAPA-03-inventario.md), con sus secciones antiguas señaladas como históricas. Se contrastaron fuentes 01/02/03/07/08/09/14/16/21, CONTROL_SPRINTS y código actual. Las etiquetas de sprints y antecedentes no se reinterpretan como pruebas. El XLSX estuvo ausente: el hash anterior es histórico, no una verificación actual. Las rutas y plantillas se enumeraron en el código; este recuento estructural no acredita cada comportamiento.

## Los 27 criterios base

La tabla detalla el requisito, resultado y siguiente acción en [inventario individual](ETAPA-03-inventario.md#cada-hu-y-criterio); aquí se concilia cada ID con una evidencia principal. **CUMPLE** significa solo la muestra especificada en el anexo, no ejecución exhaustiva. Cuatro criterios de edición/eliminación comercial de categorías son futuros; Django admin técnico pertenece a15. Código de estado de las 23 filas activas: **CUMPLE muestra**; los cuatro futuros se identifican individualmente.

| ID / fuente | Requisito resumido | Estado | Evidencia principal y límites |
|---|---|---|---|
| CAT01/CA01 · 08:166 | Lista todos los nombres; category_list / category_list.html | CUMPLE muestra | [Anexo de muestra](ETAPA-03-inventario.md) |
| CAT01/CA02 · 08:167 | Mensaje de lista vacía | CUMPLE muestra | [Anexo de muestra](ETAPA-03-inventario.md) |
| CAT02/CA01 · 08:176 | Nombre no vacío, retirar espacios, activo y utilizable; form→service→model | CUMPLE muestra | [Anexo de muestra](ETAPA-03-inventario.md) |
| CAT02/CA02 · 08:177 | Duplicado por mayúsculas/espacios → «La categoría ya existe», sin fila | CUMPLE muestra | [Anexo de muestra](ETAPA-03-inventario.md) |
| CAT02/CA03 · 08:178 | Vacío → «El nombre es obligatorio», sin fila | CUMPLE muestra | [Anexo de muestra](ETAPA-03-inventario.md) |
| CAT03/CA01 · 08:187 | Renombrar y reflejar en productos | PREVISTO/FUTURO | Sin acción comercial seleccionada; admin técnico →15 |
| CAT03/CA02 · 08:188 | Nombre de otra categoría → rechazar edición | PREVISTO/FUTURO | Sin acción comercial seleccionada; admin técnico →15 |
| CAT04/CA01 · 08:197 | Eliminar vacía y desaparecer | PREVISTO/FUTURO | Sin acción comercial seleccionada; admin técnico →15 |
| CAT04/CA02 · 08:198 | No eliminar vinculada, mensaje exacto | PREVISTO/FUTURO | Sin acción comercial seleccionada; admin técnico →15 |
| PROD01/CA01 · 08:207 | ADMIN y ALMACENERO consultan nombre, código, categoría, precio y existencias | CUMPLE muestra | [Anexo de muestra](ETAPA-03-B-catalogo.md) |
| PROD01/CA02 · 08:208 | Buscar por nombre o código y recuperar la consulta | CUMPLE muestra | [Anexo de muestra](ETAPA-03-B-catalogo.md) |
| PROD01/CA03 · 08:209 | Mostrar alerta si las existencias vigentes son iguales o inferiores al mínimo | CUMPLE muestra | [Anexo de muestra](ETAPA-03-B-catalogo.md) |
| PROD02/CA01 · 08:218 revisado DOC03-01 | Cualquier categoría activa, UND/vencimiento; nombre único normalizado (aceptado10/11) | CUMPLE muestra | [Anexo de muestra](ETAPA-03-I-politicas.md) |
| PROD02/CA02 · 08:219 | Soles finales con IGV, positivos y máximo dos decimales | CUMPLE muestra | [Anexo de muestra](ETAPA-03-C-alta.md) |
| PROD02/CA03 · 08:220 | Código normalizado irrepetible | CUMPLE muestra | [Anexo de muestra](ETAPA-03-C-alta.md) |
| PROD02/CA04 · 08:221 revisado10/11 | Entero0..999999; alta vacía/omitida10 | CUMPLE muestra | [Anexo de muestra](ETAPA-03-I-politicas.md) |
| PROD02/CA05 · 08:222 | Alta con stock cero y acceso solo ADMIN | CUMPLE muestra | [Anexo de muestra](ETAPA-03-C-alta.md) |
| PROD03/CA01 · 08:231 | Captura ADMIN: texto original y adenda de copia expresa | CUMPLE muestra | [K8](ETAPA-03-K8-captura.md), [P](ETAPA-03-P-aviso-fisico-y-migraciones.md); discrepancia literal explicada abajo |
| PROD03/CA02 · 08:232 | Duplicado advertido al leer | CUMPLE muestra | [Consulta O y captura física P](ETAPA-03-P-aviso-fisico-y-migraciones.md) |
| PROD04/CA01 · 08:241 | Nuevo precio hacia adelante, pasado conservado | CUMPLE muestra | [Anexo de muestra](ETAPA-03-R-precios-y-resumen.md) |
| PROD04/CA02 · 08:242 | Umbral actualizado al editar | CUMPLE muestra | [Anexo de muestra](ETAPA-03-D-edicion.md) |
| PROD04/CA03 · 08:243 revisado DOC03-02 | ADMIN corrige código único conservando identidad e históricos | CUMPLE muestra | [Anexo de muestra](ETAPA-03-T-catalogo-y-resumen.md) |
| PROD04/CA04 · 08:244 revisado10/11 | Nombre actualizado y único normalizado, históricos conservados | CUMPLE muestra | [Anexo de muestra](ETAPA-03-T-catalogo-y-resumen.md) |
| PROD04/CA05 · 08:245 | Reclasificación de categoría | CUMPLE muestra | [D](ETAPA-03-D-edicion.md), [N/O](ETAPA-03-N-O-reclasificacion-y-duplicados.md), [U](ETAPA-03-U-categoria-y-cobro.md), [V](ETAPA-03-V-concurrencia-triple.md) |
| PROD05/CA01 · 08:254 | Inactivo excluido de mostrador | CUMPLE muestra | [Anexo de muestra](ETAPA-03-M-producto-con-operaciones.md) |
| PROD05/CA02 · 08:255 | Reactivar con categoría activa y stock vigente positivo habilita oferta con precio actual | CUMPLE muestra | [Anexo de muestra](ETAPA-03-K-lector-y-reactivacion.md) |
| PROD05/CA03 · 08:256 | Etiqueta Inactivo e historial conservado | CUMPLE muestra | [Anexo de muestra](ETAPA-03-E-disponibilidad.md) |

**Precisión de fuentes, PROD03/CA01:** 08:231 dice que el campo de código se llena automáticamente al leer. La adenda posterior 08:912 recoge revisión y copia expresa aceptadas en K8/K9, y 21:77 confirma ese flujo vigente. La lectura física llena el campo temporal del diálogo; solo tras pulsar «Usar código» se copia a la ficha. K5 probó captura directa en una interfaz anterior; no prueba copia automática al campo final del diseño actual. Se mantiene CUMPLE en la muestra del alcance posterior precisado, pero queda **CONFLICTO DE REDACCIÓN** con el texto literal original: se propone aclarar la redacción del criterio sin borrar su formulación histórica ni rebajar protección. No hay coincidencia literal total.

## Cuatro criterios suplementarios de categoría

| ID y actor | Esperado / muestra | Estado / evidencia |
|---|---|---|
| J-CA1 · ADMIN | Revisar impacto, cancelar o volver sin escritura | CUMPLE muestra J01–03/J19/J23–25; [J](ETAPA-03-J-estado-categoria.md) |
| J-CA2 · ADMIN/ALMACENERO/VENDEDOR | Confirmar suspensión y reactivación conservando lotes/borrador/históricos; bloquear operaciones afectadas | CUMPLE muestra J04/J07–12/J19–20/J26, [L](ETAPA-03-L-suspension-con-operaciones.md), [U](ETAPA-03-U-categoria-y-cobro.md) y [V](ETAPA-03-V-concurrencia-triple.md) |
| J-CA3 · ADMIN | Pantalla antigua/reenviada no revierte estado; 409 y revisión | CUMPLE muestra J05/06/J21/22, J-R1–R3 SQLite y PG; [J](ETAPA-03-J-estado-categoria.md) |
| J-CA4 · roles | Solo ADMIN revisa/confirma; trabajadores 403 y visitante redirigido | CUMPLE muestra J13–18 y [U](ETAPA-03-U-categoria-y-cobro.md) |

## Mapa inverso vigente de rutas y salidas

`catalog/urls.py` contiene **12 patrones**: 11 del alcance03 y `/productos/vencimientos/` de07. Hay **9 plantillas**, 8 del tramo03 incluida la parcial de captura, y `product_expirations.html` de07. Tres formularios y dos modelos. ADMIN=A, ALMACENERO=L, VENDEDOR=V. Recuento incluye alias, no implica una pantalla adicional.

| Ruta bajo `/productos/` | Actores / acción y salida | Respaldo, estado y evidencia |
|---|---|---|
| `categorias/` | A lista, alta, activar/desactivar | CAT01/02, PROP-E00-HU-02; [A](ETAPA-03-inventario.md), [J](ETAPA-03-J-estado-categoria.md) |
| `categorias/nueva/` | A GET/POST nombre; éxito/errores y cancelar | CAT02; [A](ETAPA-03-inventario.md) |
| `categorias/<uuid>/estado/confirmar/` | A revisa impacto, cancelar o continuar; consulta de estado/versión | J-CA1/3/4; [J](ETAPA-03-J-estado-categoria.md) |
| `categorias/<uuid>/estado/` | A POST objetivo `is_active`, `state_version`, `confirm=yes`; inválido400, obsoleto409, éxito redirección | J-CA2–4; [J](ETAPA-03-J-estado-categoria.md); alternancia heredada del servicio interno no equivale al POST comercial |
| `/` | A/L buscan por `q`; nombre, categoría, código, precio, mínimo, existencias vigentes, alerta y disponibilidad; A edita/cambia estado | PROD01/04/05; [B](ETAPA-03-B-catalogo.md), [E](ETAPA-03-E-disponibilidad.md) |
| `nuevo/` | A registra ficha por unidad, activa y con vencimiento obligatorio; título «Registrar producto» | PROD02 y alcance [F](ETAPA-03-F-alcance.md) |
| `codigos/comprobar/` | A GET, código y UUID propio opcional; duplicado/error sin datos de otra ficha | PROD03/CA02, [O](ETAPA-03-N-O-reclasificacion-y-duplicados.md) y [P](ETAPA-03-P-aviso-fisico-y-migraciones.md); L/V 403 |
| `<uuid>/registrado/`, `<uuid>/creado/` | A detalle actual, registrar otro/ver catálogo; segundo es alias | PROD02; [C](ETAPA-03-C-alta.md); no afirmar estado histórico congelado |
| `<uuid>/editar/` | A nombre/código/categoría/precio/mínimo y `edit_snapshot`, guardar/cancelar | PROD04; [K7](ETAPA-03-K7-edicion-y-relectura.md), [T](ETAPA-03-T-catalogo-y-resumen.md) |
| `<uuid>/disponibilidad/` | A POST estado objetivo; omisión conserva alternancia heredada | PROD05; [E](ETAPA-03-E-disponibilidad.md), [M](ETAPA-03-M-producto-con-operaciones.md) |
| `vencimientos/` | A/L fechas y filtro | PROD06→07, NO AUDITADO integralmente aquí |
| `admin/catalog/...` | Staff técnico de Django, distinto de ADMIN comercial | EXTRA técnico, NO EJECUTADO en03;→15 |
| Menús y `/ventas/`/cobro/constancia | A gestión; L consulta; V solo venta autorizada | [U](ETAPA-03-U-categoria-y-cobro.md), frontera no aprobación de10–12 |

Campos vigentes: categoría `name` hasta120, no vacío, colapso de espacios y clave casefold; producto `name` hasta160, no vacío, clave NFC/casefold; `barcode` hasta64, obligatorio, letras ASCII/dígitos/guiones y `\s` en la expresión de servidor: no afirmar que cada whitespace esté probado; `category` activa o actual inactiva en edición, vacía conserva actual; `unit` UND; `sale_price` S/0,01–9 999 999,99, hasta dos decimales; `minimum_stock` 0–999999, alta vacía→10 y edición requerida; `controls_expiration` verdadero y no editable. `edit_snapshot` se declara `required=False` pero `clean_edit_snapshot` rechaza omisión, firma inválida u otra ficha. Reglas detalladas, mensajes y pruebas de límites: [C](ETAPA-03-C-alta.md), [D](ETAPA-03-D-edicion.md), [I](ETAPA-03-I-politicas.md), [K7](ETAPA-03-K7-edicion-y-relectura.md), [O](ETAPA-03-N-O-reclasificacion-y-duplicados.md). Cada campo no se reprobó en W.

## Decisiones, riesgos y traspaso

- **Despliegue y migraciones 0003–0006: NO EJECUTADO.** Ensayo en copia SQLite P, preflight y hashes [P](ETAPA-03-P-aviso-fisico-y-migraciones.md). Elegir destino real, respaldo verificable, ventana y recuperación antes de desplegar; la copia no prueba un despliegue PostgreSQL.
- **EAN-13/UPC-A: decisión abierta.** Las cadenas se distinguen y las primeras lecturas físicas con EAN/UPC no llegaron al campo; Code128 sí. Definir política de equivalencia si se usan ambas, sin convertir automáticamente ni fusionar datos. [K](ETAPA-03-K-lector-y-reactivacion.md).
- **Reclasificación activa:** conservar comportamiento actual o mostrar categoría y exigir revisión; decisión de alcance en [U](ETAPA-03-U-categoria-y-cobro.md). Tres carreras V son muestras, no demostración universal.
- **Recepción/retiros:** tres HU propuestas y PROP-03-RET-T01..T11 siguen NO EJECUTADOS integralmente; derivación a05–08/11/12/14–16 y brecha observada de asociación venta→lote, prueba integral pendiente. [Anexo](ETAPA-03-recepcion-y-retiros-pendientes.md). Ensayos L/M de suspensión no los cierran.
- **Seguridad/concurrencia→15:** serialización de resumen sin autenticación y llamadas internas sin resumen; SQL directo puede no recalcular clave normalizada. Riesgos de perímetro, no vulnerabilidad demostrada por W. **Costo promedio histórico→11:** ausencia de campo observada estáticamente en Q; prueba funcional pendiente. **Normativa→16:** sin conclusión legal o fiscal.
- **CAT03/04 futuros:** no confundir desactivar con eliminar, ni admin técnico con rol comercial. El escáner PROD03 fue seleccionado después: la adenda J/02-F que lo llama futuro corresponde a su fecha; la selección O y evidencia física P son posteriores.
- **Otros límites:** lector de pantalla real, volumen/Unicode exhaustivos, otros lectores y simbologías; alertas de03-T con formatos de separador distintos; no se certifican. El pedido del usuario de no cerrar otros módulos se mantiene.

## Evidencia y próximo cursor

En 03-W: inventario estructural por inspección de `catalog/urls.py`, `forms.py`, `models.py`, plantillas y cotejo de anexos/evidencias; **no se ejecutaron** navegador, PostgreSQL, suite o migraciones en W. El último resultado de regresión funcional es [332/332 de03-T](../evidencias/03-K-tests-20261111T034025997777Z/result.json); 03-V contiene 3/3 intercalaciones PG, y 03-U 35/35 comprobaciones secuenciales de navegador. No son nuevas ejecuciones de W. No se modifica aplicación, base ni historial de sprints.

**Cursor 03-X / AUD03X-CODIGO-EAN-UPC01:** con base y roles ficticios, inventariar tratamiento literal de el par ficticio EAN-13 `0012345678905`/UPC-A `012345678905` antes de elegir política: alta de ambas cadenas, búsqueda por cada una, normalización, duplicados y consulta vendedor autorizada; comprobar en navegador, servidor y persistencia sin forzar equivalencia. Identificar qué lectura física fue realmente recibida; si no hay teléfono, marcar la parte física NO EJECUTADA y conservar evidencia técnica separada. Registrar alternativas de alcance y datos previos; no reetiquetar automáticamente productos. **NO EJECUTADO en W.**

Balance: **23 CUMPLE en muestras de alcance vigente, 4 PREVISTO/FUTURO y 4 suplementarios CUMPLE en muestras**, más la discrepancia literal de CA01 indicada. No es coincidencia total ni aprobación de otro módulo.

**Actualización posterior03-X:** la matriz anterior conserva su corteW. La lectura física EAN13→UPC12 amplía la frontera de PROD03/CA02 y deja ese criterio PARCIAL; balance22 CUMPLE muestras/1 PARCIAL/4 futuros. [Resultado y cursor vigente](ETAPA-03-X-codigos-ean-upc.md).
