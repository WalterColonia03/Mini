# 03-X · Códigos EAN/UPC: captura, unicidad y búsqueda

Actualizado11/11/2026, America/Lima; ejecución10/11,23:00–23:04 Lima. Sublote `AUD03X-CODIGO-EAN-UPC01`. Se leyó completo PROTOCOLO_COMUN; se preservan los cambios preexistentes del repositorio. No se modificó código funcional, reglas comerciales ni migraciones. La equivalencia entre representaciones sigue siendo una decisión de alcance, no una corrección aplicada implícitamente.

## Inventario y fuentes antes de ejecutar

El inventario global conserva 9 HU/27 CA y cuatro criterios suplementarios, [conciliados en03-W](ETAPA-03-W-conciliacion.md). Este sublote profundiza tres historias —PROD01, PROD02 y PROD03—, con una prueba negativa de edición como frontera de PROD04. No reaudita CAT, precio, mínimo, suspensiones, inventario o venta integral. El [inventario previo de esta ejecución](../evidencias/03-X-browser-20261111T040227561878Z-69a0d2f3/inventory-before.json) se escribió antes del navegador. Su descripción general de búsqueda parcial se precisa aquí: solo catálogo es parcial por código; venta es exacta normalizada.

| Elemento / fuente | Clasificación y actor | Interfaz → servidor → persistencia / salida |
|---|---|---|
| PROD01/CA02, 08:208; tareas históricas S1-VEN01B-UI/SVC, 16:139 | Actual. ADMIN/ALMACENERO catálogo; VENDEDOR consulta de venta | Menú Productos/Catálogo de productos → `/productos/?q=` → `catalog.views.product_list`, contiene código normalizado. Menú Preparar venta → `/ventas/?query=` → `sales.views._search_products`, igualdad del código normalizado y existencias vigentes |
| PROD02/CA03 y CA05, 08:220/222; RN29, 07:333; S1-PROD02-UI/SVC/AUTO/MAN/REV, 16:104–108 | Actual. ADMIN alta, otros roles denegados | Registrar producto → POST `/productos/nuevo/` → ProductRegistrationForm → register_canned_product → Product y UNIQUE barcode_normalized. Éxito `/registrado/`; duplicado no persiste |
| PROD03/CA01–02, 08:231–232 y adenda08:912, guía21:77/80 | Actual seleccionado03-O. Conflicto literal CA01 ya documentado enW | Escanear código → diálogo con Código leído → GET `/productos/codigos/comprobar/` → revisión y Usar código → campo definitivo → guardado expreso. Duplicado bloquea copia; lectura no crea fila |
| PROD04/CA03, 08:243 | Actual; frontera negativa ADMIN | Editar → `/productos/<uuid>/editar/`, incluye edit_snapshot vigente. Código propio permitido por consulta; código ajeno rechazado; UUID y campos comerciales permanecen |
| Campo `barcode` y `barcode_normalized`, models:68/109, forms:12/99/189 | Actual, obligatorio; no es campo numérico | Texto hasta64; letras ASCII, dígitos, espacios y guiones en formulario; NFKC, elimina espacios y casefold en clave. Conserva ceros. No existe selector EAN/UPC ni contrato de dígito de control. En este corte se prueban dos cadenas y variantes con espacios, no todas las fronteras de64 |
| Campos auxiliares de alta | Actual, preparación del ensayo | Nombre único ficticio, Higiene activa, UND, S/3,00 y S/4,50, mínimo predeterminado10, vencimiento obligatorio. No se revalida exhaustivamente precio/mínimo aquí |
| Mensajes y acciones reales | Actual, respaldado PROD02/03 | «Sin duplicados en esta consulta. Se volverá a comprobar al guardar.»; «El código de barras ya está registrado»; al enviar duplicado «Ya existe un producto con este código de barras.»; Usar código, Cancelar, Registrar producto, Editar, Guardar cambios, Buscar; búsqueda sin stock muestra ausencia de existencias vendibles |
| Equivalencia EAN-13/UPC-A, dígito de control y política de códigos internos | PROPUESTA/PENDIENTE, no seleccionada por estas HU | No se infiere de «código irrepetible» que todo código numérico sea GTIN ni que deban retirarse todos sus ceros. Ver opciones y criterios propuestos abajo |

Se contrastaron fragmentos de01 (DEC09),02 (código normalizado único),03 (PROD02 y VEN01B),07 (RN29),08,09 (adendas de selección),14/16 y CONTROL_SPRINTS. Sus estados históricos no acreditan las pruebas actuales. XLSX ausente al iniciar; no se abrió, recreó ni modificó. La fuente externa GS1 solo fundamenta una alternativa de representación: no amplía el alcance contratado ni verifica asignación comercial de los códigos ficticios.

## Resultados software reproducidos

Chrome157.0.8103.39 real, modo headless, Playwright, viewport1366×900, cuentas ficticias y base nueva `datos/etapa03k-X-20261111T040227561878Z-69a0d2f3/audit.sqlite3`. Instancia comprobada mediante desafío HMAC antes de enviar credenciales. No se cargó `.env` real. Soporte [runner](../soporte/audit03x_run.py) y [navegador](../soporte/audit03x_browser.cjs).

**69/69 comprobaciones de navegador/HTTP/ORM y 16/16 comprobaciones adicionales de servicio/DB.** El contador69 incluye una comprobación agregada de esas16; no son85 casos independientes. [Resultado del recorrido](../evidencias/03-X-browser-20261111T040227561878Z-69a0d2f3/browser.json), [puntos de persistencia](../evidencias/03-X-browser-20261111T040227561878Z-69a0d2f3/checkpoints.json), [cierre](../evidencias/03-X-browser-20261111T040227561878Z-69a0d2f3/result.json).

| Caso y trazabilidad | Esperado según contrato actual / observado | Estado / prioridad |
|---|---|---|
| X01 alta EAN `0012345678905`, luego UPC `012345678905`; PROD02/03 | Diálogo permite cada cadena nueva, no escribe; copia expresa conserva ceros y guardado crea dos UUID distintos. Ambas claves normalizadas quedan distintas | CUMPLE contrato literal; equivalencia pendiente, P1 antes de usar ambas representaciones |
| X02 duplicados exactos y `00 12345678905` / ` 012345678905 `; PROD02/03 | Diálogo avisa y bloquea copia. Envío manual directo del formulario se rechaza con error de campo; las instantáneas comerciales comparadas no cambian | CUMPLE muestra |
| X03 edición de EAN; PROD04 frontera | Consulta del código propio permite; UPC ajeno bloquea. Envío manual UPC rechazado, sin cambio comercial | CUMPLE muestra |
| X04 búsqueda ADMIN/ALMACENERO; PROD01 | EAN recupera EAN; UPC recupera ambas fichas por coincidencia parcial; variante EAN con espacio recupera EAN. Consulta permanece en campo | CUMPLE coincidencia parcial vigente; no afirmar búsqueda exacta de catálogo |
| X05 búsqueda VENDEDOR; frontera VEN01B | Antes de lotes no ofrece ninguna. Tras carga ficticia: EAN→EAN7 unidades, UPC→UPC11 unidades; EAN con espacio→EAN. No selecciona producto ni crea borrador/venta | CUMPLE consulta autorizada; no aprobación de venta ni carga inicial |
| X06 permisos RN29 | ALMACENERO/VENDEDOR GET alta, edición y API→403; POST alta/edición con CSRF válido→403. Vendedor catálogo→403; visitante alta/API→302. Sin cambios comerciales | CUMPLE peticiones concretas, no certificación integral de seguridad |
| X07 servicio/DB | Ceros iniciales conservados y claves distintas;12 rechazos de servicio: ADMIN duplicados por ValidationError, trabajadores PermissionDenied; UNIQUE SQL impide otra fila EAN; instantánea intacta | CUMPLE en SQLite aislado; PostgreSQL NO EJECUTADO aquí |

La carga de7/11 unidades fue preparación explícita por `confirm_initial_load`, con lotes ficticios futuros a60 días y costo1,00; no recorrido de recepción. Se conserva turno ficticio OPEN, dos productos, dos lotes, cero borradores y cero ventas. Las instantáneas comparan los campos comerciales enumerados por el soporte; no equivalen a un volcado íntegro de todas las tablas de autenticación.

**Intento anterior conservado:** [primera ejecución](../evidencias/03-X-browser-20261111T040056659143Z-a42ce2ac/browser.json) terminó con47 comprobaciones correctas y una expectativa incorrecta del soporte: esperaba ambas fichas en la consulta UPC del vendedor. La implementación usa igualdad de código, distinto del catálogo. Se corrigió esa expectativa tras inspeccionar `sales/views.py:54–64`; la repetición completa se hizo en otra base. No fue un defecto funcional corregido ni se borró la evidencia fallida.

Comandos desde raíz del proyecto:

```powershell
& r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/soporte/audit03x_run.py browser
& r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/soporte/audit03x_run.py phone
```

Cada comando crea una base nueva marcada y conserva anteriores; `phone` requiere operador y escritorio, muestra una etiqueta y espera confirmación física sin introducir caracteres por automatización. No ejecutar modos internos manualmente contra bases ajenas. Credenciales efímeras permanecen en archivos locales de soporte; no incluirlos en informes/capturas.

## Prueba física

El usuario confirmó disponibilidad del teléfono y pulsó personalmente el botón de observación después de leer. Chrome visible, base independiente `datos/etapa03k-X-20261111T040311661823Z-6ffff079/audit.sqlite3`, solo una ficha preexistente con `0012345678905`, sin lotes, borradores ni ventas. El soporte mostró una etiqueta EAN-13 sintética de ese valor dentro del diálogo, con95 módulos y dígito de control comprobado; la superposición es instrumentación del ensayo, no una nueva pantalla del producto. No se escribieron, pegaron ni simularon caracteres en los campos de código.

Se observaron **seis llegadas completas de `012345678905`**,72 eventos input confiables y seis Ctrl+A. No hubo concatenación, Enter, Tab, entradas en otros campos ni POST. El operador confirmó la observación. Campo final de la ficha vacío y datos comerciales intactos. **9/9 controles de observación y conservación**, que acreditan lo ocurrido; no significan aprobación de la equivalencia. [Eventos y resultado](../evidencias/03-X-phone-20261111T040311661823Z-6ffff079/phone.json), [captura observada](../evidencias/03-X-phone-20261111T040311661823Z-6ffff079/observed.png), [cierre](../evidencias/03-X-phone-20261111T040311661823Z-6ffff079/result.json), [soporte](../soporte/audit03x_phone.cjs).

**H-03X-01 · PARCIAL · P1 · PROD03/CA02:** con la representación13 ya almacenada, la lectura recibida de12 mostró «Sin duplicados en esta consulta. Se volverá a comprobar al guardar.» y habilitó Usar código. La prueba software X01 demuestra que ambas cadenas pueden guardarse como fichas distintas; la prueba física se detuvo sin copiar ni guardar. No se atribuye al teléfono una segunda alta que no realizó. Se acredita una brecha operativa de interoperabilidad, mientras que el control de duplicados literales sigue CUMPLE en sus muestras. No hay evidencia para afirmar que Django eliminó un cero: el primer valor completo recibido ya tenía12 dígitos. No se inspeccionó ni cambió la configuración interna del móvil/servidor en este corte.

Balance actualizado respecto aW: **22 CA CUMPLE en sus muestras, 1 PARCIAL (PROD03/CA02 por esta frontera) y4 PREVISTO/FUTURO**; cuatro suplementarios CUMPLE en sus muestras. Los éxitos literales previos deP se conservan. CA01 conserva la discrepancia de redacción ya registrada. La decisión de equivalencia queda abierta; no se declara un INCUMPLE de una política GTIN todavía no seleccionada.

## Decisión de alcance y propuestas, no implementadas

GS1 documenta representaciones de GTIN de longitud fija14 mediante relleno a la izquierda con ceros. Bajo esa representación, ambas cadenas de ensayo dan `00012345678905`; esta igualdad es una inferencia numérica aplicada al par ficticio, no prueba de que pertenezca a un artículo comercial asignado. El catálogo admite también códigos internos alfanuméricos. [GS1: formato GTIN en EDI](https://support.gs1.org/support/solutions/articles/43000734355-what-is-the-required-format-of-gtin-in-gs1-edi-standards-), consulta10/11/2026, página modificada02/09/2024. No se impone formato EDI a la aplicación.

**DEC-03X-IDENTIDAD, pendiente:** elegir y documentar el significado de un código. Alternativas:

1. Conservar identificadores literales normalizados actuales. Documentar política única de captura/ingreso y que las dos representaciones no se resuelven entre sí en venta. Evita reinterpretar códigos internos; mantiene riesgo de dos fichas para el mismo artículo o de no encontrarlo al leer otra representación.
2. Distinguir explícitamente GTIN de código interno; para GTIN validar longitud/dígito y comparar una clave canónica, conservando el texto original para presentación. Requiere decisión sobre datos anteriores, búsqueda, errores y colisiones; no fusionar UUID, lotes ni históricos automáticamente.
3. Asociar alias autorizados a una ficha, conservando código principal. Necesita unicidad de alias global, permisos, prevención de ambigüedad y migración revisada; permite controlar excepciones sin inferir que toda cadena numérica sea GTIN.

**PROP-03X-CA01**, ampliación de PROD02/CA03 y PROD03/CA02, propuesta: dado ADMIN y una ficha identificada como GTIN, cuando ingresa otra representación aceptada del mismo identificador, entonces se advierte antes de copiar y se rechaza la segunda alta sin efectos; códigos internos conservan su política expresa. Depende de DEC-03X-IDENTIDAD; no aprobado ni implementado.

**PROP-03X-CA02**, ampliación PROD01/VEN01B, propuesta: dado un producto con existencias vendibles y una representación aceptada, cuando un rol autorizado busca ese identificador, entonces se recupera la misma ficha de forma inequívoca; si hay colisión histórica se informa y no se elige arbitrariamente. Nunca agrega ni cobra por buscar. Incluye desactivados, sin stock y permisos como casos negativos.

**PROP-03X-CA03**, precisión documental PROD03/CA01, propuesta: dado el diálogo abierto, cuando llega una lectura, entonces se conserva el valor recibido en el campo temporal; tras revisión y «Usar código» se copia a la ficha y solo el guardado expreso persiste. Mantener el texto original como antecedente; no cambiar el criterio para ocultar la discrepancia señalada enW.

**PROP-03X-T01**, tarea de diseño/datos: decidir formato y preparar análisis de colisiones en una copia nueva, con informe por grupos y sin fusiones. **PROP-03X-T02**, implementación condicionada: validación/índice/consulta/alias según alternativa, errores coherentes en formulario, API, servicio y DB. **PROP-03X-T03**, pruebas propuestas: pares12/13/14 con ceros, códigos internos numéricos, dígito inválido, UPC-E/EAN8 fuera de alcance por defecto, edición propia/ajena, inactivo, concurrente PostgreSQL, captura física y servidor, consulta entre roles y conservación de históricos. Son tareas y criterios sobre HU existentes; no se duplica HU para el mismo beneficio.

## Límites y continuidad

La muestra software demuestra unicidad literal y consultas; no demuestra equivalencia comercial, otras simbologías ni todos los lectores. Sin cambios funcionales, no se repitió la suite332 de03-T ni pruebas de concurrencia. Despliegue de0003–0006 sigue pendiente; la copia de03-P no equivale a despliegue. Recepción multiproducto/retiros por lote sigue [pendiente integral](ETAPA-03-recepcion-y-retiros-pendientes.md). Las demás etapas conservan sus estados y CAT03/04 siguen futuros. No hay aprobación universal del lector ni coincidencia total.

Los tres servidores de este corte terminaron y sus puertos se comprobaron cerrados. Las bases protegidas conservaron SHA256; original `r1-pmv/r1_pmv.sqlite3`: `4406ecd5babab34f0bb264e82c134eb21563494f9faf50e462d50c30c9d2ea95`. No se tocó la configuración del lector. Los datos ficticios quedan retenidos y las ventanas del ensayo cerradas. El conteo general de rutas/plantillas se hereda deW; no se reenumeró enX.

**Cursor exacto 03-Y / AUD03Y-PREFLIGHT-IDENTIDAD01:** preparar una copia nueva marcada de la base original y, sin migrar ni cambiar el original, inventariar clases de códigos y grupos candidatos a colisión bajo las alternativas DEC-03X-IDENTIDAD; no inferir GTIN por longitud ni fusionar fichas. Contrastar con las tres propuestas de este anexo y dejar una decisión concreta revisable. Si el usuario ya eligió política al retomar, incorporar esa elección y ejecutar sus casos aislados; si no, continuar solo con análisis y documentación independientes. La lectura física X está ejecutada y no debe repetirse como pendiente genérico del aviso.
