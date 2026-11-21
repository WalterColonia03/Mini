# Etapa 03-B · Catálogo, búsqueda y umbral

**09/11/2026, America/Lima.** Se auditaron los tres criterios de HU-PROD-01 desde el catálogo, con cuentas de administrador y almacenero. El vendedor consultó un producto desde su propio turno de venta. El estado de la historia en este alcance es **CUMPLE en la muestra**. La redacción histórica sobre los actores sigue en DOC-00-14. [Matriz de la etapa](ETAPA-03-inventario.md).

## Inventario previo y fuentes

| Elemento | Clasificación de entrada y fuente | Comprobación prevista |
|---|---|---|
| HU-PROD-01/CA-01 | Adicional a R1, 08:204–207 y 09:67. CONTROL_SPRINTS:37 declaraba terminada la HU. Candidato E03-OBS-01 por ausencia de cantidad en la plantilla | Comparar cada columna con 11 productos y sus lotes. Examinar las vistas de los dos roles autorizados |
| HU-PROD-01/CA-02 | Búsqueda por nombre o código, 08:208. QA-FIX-CAT-01 en 16:328 y BUG-031 en la matriz 03:307 | Consultar por nombre y código completos y parciales, probar entradas límite y comprobar limpiar, recargar y volver |
| HU-PROD-01/CA-03 y RN-06 | 08:209 y 07:102–108 exigen la señal cuando la cantidad vendible es menor o igual al mínimo propio | Probar ambos lados del umbral, la igualdad, el cero y mínimos distintos de 10 |
| RN-03 y DT-06 | 07:70–76 y diseño 02, tabla de decisiones técnicas. El vencimiento se evalúa en la fecha de negocio de Lima | Incluir lotes vencidos ayer, que vencen hoy, vigentes y agotados |
| Roles | 08:204 menciona al vendedor en el catálogo. Guía 21:11–14 y alcance autorizado reservan la lista al administrador y almacenero | Menú de cada rol, GET denegado al vendedor, consulta permitida en venta y redirección del visitante |
| Tareas y evidencia | S1-ENV-01 y S1-SEC-02 de 16:66–67 son dependencias. S2-PROD01-AUTO enumeraba cuatro pruebas de acceso y búsqueda como CA1–4. La HU tiene tres CA con otro contenido | Conservar la evidencia histórica y verificar los ordinales contra 08:207–209. El listado y el umbral carecían de prueba directa en ese informe |

Se recogieron antes de corregir los identificadores de criterio, el estado de Git y hashes de fuentes, base original, bases retenidas y XLSX. El libro conserva la función y el corte del 05/11 descritos en el inventario 03-A. [Manifiesto previo](../evidencias/03-B-inventario-20261110T010633144160Z/baseline.json).

## Pantalla, campos, acciones y salidas

La ruta es `GET /productos/`, atendida por `catalog.views.product_list` y `catalog/product_list.html`. La consulta lee `Product`, `Category` y `Lot`. El administrador llega por **Productos** y el almacenero por **Catálogo de productos**. La acción **Preparar venta** del vendedor abre otra ruta con su propio control de turno.

| Elemento | Formato, valor inicial, persistencia o mensaje | Resultado y trazabilidad |
|---|---|---|
| Campo de búsqueda `q` | Texto opcional, inicialmente vacío, sin máximo de aplicación declarado. GET por nombre o código. Se quitan espacios exteriores. Un valor de 4096 caracteres sin coincidencia dio lista vacía. No persiste en el producto | CA-02. Vacío y solo espacios devuelven el catálogo. Nombre parcial, código con espacios internos y dígitos de ancho completo cubiertos entre navegador y Django |
| Buscar, limpiar, Enter, recarga y Atrás | La etiqueta identifica el campo. Buscar envía el filtro y la cruz «Limpiar búsqueda» vuelve a la lista. Chrome recupera la consulta y el resultado anterior con Atrás | C04–C09, C14. Estado del GET consistente con el texto y la fila visible |
| Lista y mensajes | «No hay productos registrados.» en base vacía. «No se encontraron productos con «ninguno».» en una consulta sin coincidencias. Un carácter nulo recibe «La búsqueda contiene un carácter no válido.» con el mensaje asociado al campo | C01, C05 y C10. Las búsquedas literales por signos y texto HTML conservaron la tabla y los datos |
| Nombre, código y categoría | Texto escapado en cada fila. El catálogo incluye los productos y categorías suspendidos. La clave normalizada se usa internamente para buscar | C03, C13. El nombre comercial sigue visible con su escritura original |
| Precio de venta | Soles con dos decimales, 8,50 en las filas de prueba. Importe persistido de la ficha | CA-01. La escritura de precio y su validación de IGV corresponden a PROD-02 |
| Existencias vigentes (UND) | Entero calculado como suma de cantidades disponibles de lotes con fecha posterior a hoy en Lima. En ausencia de unidades vigentes muestra 0 | CA-01. En el lote mixto hubo 4 + 5 vigentes, 50 vencidas, 3 que vencían hoy y 0 en un lote agotado. La suma visible fue 9 |
| Stock mínimo y «Stock bajo» | Umbral entero persistido del artículo. La alerta tiene texto visible y se muestra al alcanzar o bajar del umbral | CA-03/RN-06. Con mínimo 10 hubo alerta en 0, 9 y 10 unidades, y desapareció en 11. Con mínimo 0 hubo alerta en cero. Con mínimo 3, cuatro unidades quedaron por encima |
| Disponibilidad | Producto deshabilitado, Categoría desactivada, Disponible o Sin stock vigente. El estado se muestra junto a la cantidad vigente que físicamente conserva el artículo | C03. Un producto inactivo conservó sus 9 unidades, la alerta y el aviso de deshabilitado. Un producto con categoría inactiva conservó sus 11 unidades y el aviso de categoría |
| Acciones por rol | ADMIN ve Editar y Habilitar/Deshabilitar. ALMACENERO ve las mismas columnas de datos sin acciones. El listado admite GET. POST con token válido devolvió 405 | C11–C17. El vendedor obtuvo 403 al abrir el catálogo y consultó 11 unidades a S/ 8,50 desde su venta autorizada. El visitante recibió 302 hacia el ingreso |
| Presentación | Tabla completa en el escritorio probado, 1366×768. A 390×844 la tabla se desplaza de forma independiente y se puede llegar a las acciones | C02 y C18. La comprobación móvil se limitó al viewport y al desplazamiento del contenedor. [Escritorio](../evidencias/03-B-browser-20261110T020505026105Z/C02-catalogue.png) · [Móvil](../evidencias/03-B-browser-20261110T020505026105Z/C18-mobile-actions.png) |

## Hallazgos y cambios

| Hallazgo y prioridad | Comportamiento reproducido | Corrección verificada |
|---|---|---|
| E03-OBS-01, P1 para CA-01/03 | Las filas solo mostraban el mínimo y disponibilidad. Productos con 9, 10 y 11 vigentes se veían como «Disponible» sin cantidad ni señal de umbral | La consulta ORM agrega los lotes vigentes por producto en la misma consulta. La plantilla reutiliza la cantidad para mostrar existencias, alerta inclusiva y disponibilidad |
| Búsqueda con entrada inválida, P1 para CA-02 | La misma entrada inválida devolvió la lista completa en SQLite y una respuesta 500 en PostgreSQL | La vista valida antes de filtrar. Ambos motores devuelven el formulario con un error de campo y cero filas |
| Mayúsculas acentuadas, P2 para CA-02 | «Atún» tenía coincidencia, «ATÚN» devolvía cero en SQLite y en PostgreSQL con locale C | Se usa una clave de nombre con Unicode casefold y NFC guardada por el modelo. La migración 0004 rellena los nombres previos. «ATÚN» y su versión con acento descompuesto encuentran «Atún». «Atun» conserva la distinción de tilde |
| Historial y anchura de la tabla, P2 para navegación | En el primer recorrido Chrome restauró un filtro incoherente al usar Atrás. La tabla adicional requería desplazamiento lateral en el escritorio ensayado | El formulario desactiva el autocompletado para recuperar la consulta del GET. Las celdas admiten saltos de línea en escritorio. Chrome confirmó que URL, campo y resultado coinciden al volver y que las ocho columnas caben en 1028 px de contenido |

**Decisión de implementación.** La unidad de la nueva columna es el stock de lotes vigentes. El estado comercial tiene su propia columna. La búsqueda ignora diferencias entre mayúsculas y minúsculas y conserva las tildes. Es una decisión técnica que mantiene la escritura del producto y evita que el resultado dependa de la configuración regional del servidor. Aplicar `catalog.0004_product_search_name` queda pendiente en el despliegue de uso. Una futura importación masiva que omita `Product.save()` deberá mantener la clave de búsqueda.

## Evidencia antes y después

| Prueba | Resultado | Evidencia |
|---|---|---|
| Django inicial | 10 métodos, 12 fallos de aserción contando subcasos. Identificó la columna ausente y el caso de consulta inválida | [Log inicial](../evidencias/03-B-tests-20261110T010641541584Z/tests.txt) |
| Chrome inicial | 27/40 comprobaciones positivas. Fallaron las 11 comparaciones de filas, el caso Atrás y la consulta inválida | [Chrome inicial](../evidencias/03-B-browser-20261110T010857906402Z/browser.json) |
| PostgreSQL inicial | Se observaron la cantidad ausente y el HTTP 500. Una consulta de diagnóstico del soporte falló al leer el locale e interrumpió ese recorrido | [PostgreSQL inicial](../evidencias/03-B-postgresql-20261110T011014276681Z.json) |
| Controles intermedios | 61/61 métodos tras la primera corrección. En Chrome, cuatro nombres con tildes se compararon mal porque el soporte interpretaba la salida de Python con otra codificación. Se fijó UTF-8. La consulta de diagnóstico de PostgreSQL se ajustó a su versión y confirmó la diferencia «Atún»/«ATÚN» | [Django](../evidencias/03-B-tests-20261110T020054712835Z/result.json) · [Chrome](../evidencias/03-B-browser-20261110T020104229903Z/browser.json) · [PostgreSQL](../evidencias/03-B-postgresql-20261110T020150414989Z.json) |
| Django final | **62/62 métodos** en SQLite de prueba. Incluye los 11 métodos de 03-B, 15 de categorías y 36 de catalog.tests. Comprobaciones de Django y migraciones sin incidencias | [Log con métodos](../evidencias/03-B-tests-20261110T020324334766Z/tests.txt) |
| Chrome final | **43/43 comprobaciones** combinando navegación, peticiones y estado de la base. Tres sesiones independientes y un contexto de visitante. Se verificó que las lecturas y los rechazos conservaron los datos de negocio del fixture | [Observaciones](../evidencias/03-B-browser-20261110T020505026105Z/browser.json) · [Fixture](../evidencias/03-B-browser-20261110T020505026105Z/fixture.json) · [Estado final](../evidencias/03-B-browser-20261110T020505026105Z/orm-final.json) |
| PostgreSQL final | **5/5 comprobaciones** en PostgreSQL 18.4. Incluyen suma por fecha, error de campo, búsqueda Unicode, conservación de un producto preexistente durante la migración y cantidades de lote tras las lecturas | [Resultados PostgreSQL](../evidencias/03-B-postgresql-20261110T020354212138Z.json) |

Los resultados de los recorridos intermedios se conservan con su fecha. El corte final del navegador contiene 11 productos, 2 categorías, 13 lotes, un turno ficticio abierto y cero ventas. La base es `datos/etapa03b-20261110T020505026105Z/audit.sqlite3`. Se crearon algunas fechas vencidas directamente en el fixture para representar lotes que ya caducaron en almacén. Se comprobó el cierre de los servidores y la conservación por hash de la base original, las bases anteriores y el XLSX.

Desde la raíz del proyecto se reproducen las pruebas en una nueva instancia con estos comandos:

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03b_run.py' tests catalog.test_audit03_catalogue catalog.test_audit03_categories catalog.tests
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03b_run.py' browser
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03b_pg.py'
```

## Propuestas y límites

**Criterio adicional propuesto para CA-02.** Dado un producto con nombre acentuado y un código válido, cuando ADMIN o ALMACENERO busca el mismo nombre en otra combinación de mayúsculas, recupera la ficha con su nombre original. Una entrada inválida devuelve un error asociado al campo sin listar productos ni cambiar la base. Esta conducta está implementada y verificada en 03-B. Su incorporación formal a 08 y a la matriz de aceptación queda propuesta.

**Tarea de trazabilidad propuesta.** Incorporar a la matriz vigente los casos C03 por umbral y PG03B-migration para datos previos. Conservar los cuatro casos históricos de S2-PROD01-AUTO como pruebas de acceso y búsqueda y referenciar por separado los tres CA originales.

**Pendiente de 07.** La lectura de `inventory/views.py::stock_overview` mostró una comparación estricta con el mínimo. Probar allí un producto activo con 10 unidades vigentes y mínimo 10. La comprobación de ese resumen queda NO EJECUTADA en 03-B. También quedan fuera de la muestra el volumen de 2000 productos/20000 lotes, lectores de pantalla reales, motores con otras configuraciones regionales y operaciones concurrentes de inventario o cobro.

**Siguiente cursor** en 03-C, HU-PROD-02/CA-01 (08:218). Crear una base nueva con «Productos enlatados» activa. ADMIN abre Registrar producto y completa la ficha con precio final S/ 8,50 y mínimo vacío. Contrastar persistencia y disponibilidad. Continuar con fronteras de precio, código, mínimo y permisos de alta.
