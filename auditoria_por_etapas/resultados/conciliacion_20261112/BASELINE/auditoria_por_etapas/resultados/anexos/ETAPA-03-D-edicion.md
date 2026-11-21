# Etapa 03-D · Edición del producto

**Corte del 09/11/2026, America/Lima.** HU-PROD-04, criterios 01, 02, 04 y 05 cumplen en la muestra. El criterio 03 mantiene el conflicto documental sobre el código editable. El recorrido usa ADMIN para editar, ALMACENERO para consultar y VENDEDOR desde su turno propio. El siguiente caso es **03-E / HU-PROD-05 / CA-01**, 08:254. [Inventario antes de corregir](../evidencias/03-D-inventario-20261110T025844751936Z.json).

## Criterios, reglas y tareas

| Fuente y requisito | Esperado y resultado observado | Estado y siguiente acción |
|---|---|---|
| HU-PROD-04/CA-01 · 08:241. Nuevo precio hacia adelante y conservación del pasado | Se pasó de S/ 8,50 a S/ 9,20. Catálogo y consulta de venta mostraron 9,20. La línea preparada conservó 8,50 hasta intentar cobrar. El servidor actualizó esa línea, mostró el aviso y pidió revisar el total. Al confirmar otra vez, dos unidades se cobraron a 18,40 con vuelto 11,60 de un pago de 30,00. La constancia histórica mantuvo 8,50 | **CUMPLE muestra.** D03–10, D29. Carreras de edición contra cobro quedan en 15 |
| CA-02 · 08:242 y RN-06, 07:102–108 | Tras el cobro quedaron 17 unidades vigentes. Cambiar el mínimo a 17 activó Stock bajo, y reducirlo a 16 retiró la alerta en la consulta del almacenero | **CUMPLE muestra.** D11. El resumen consolidado de inventario conserva el pendiente de 07 |
| CA-03 · 08:243 frente a agregado QA 08:872 y matriz 03:280 | El formulario permite cambiar el código. Se editó a AUD03D-NUEVO, la venta lo encontró por el nuevo código y dejó de encontrarlo por el anterior. La constancia conservó el código anterior. Dos ediciones simultáneas hacia un mismo código normalizado dejaron un ganador y un rechazo | **CONFLICTO DE FUENTES.** D01, D15–16, PG-D01/D02. DOC03-02 conserva las alternativas de bloquear futuras ediciones o formalizar correcciones administrativas |
| CA-04 · 08:244 | Se guardó «AUD03D Atún nuevo», colapsando espacios. El catálogo, los resultados de búsqueda y la línea del borrador mostraron ese nombre. La constancia histórica conservó el nombre original | **CUMPLE muestra.** D12–14. PROP-03C-NOMBRE mantiene la decisión sobre unicidad de nombres |
| CA-05 · 08:245, QA 08:876 | Se reasignó a Alternativa activa y el almacenero vio el cambio. Se rechazaron categoría ajena inactiva y UUID ausente. Vacío conservó la categoría actual. Tras desactivar esa categoría se pudo editar precio conservándola, y después se volvió a Productos enlatados | **CUMPLE muestra.** D17–19, D21, D25–26, PG-D03/D04. La revalidación del servicio se corrigió para una selección anterior a la suspensión |

La HU es una ampliación implementada posterior a R1 según 09:68 y CONTROL_SPRINTS:38. La tarea histórica S2-PROD04-AUTO y los identificadores S2-PROD04-SVC/UI aparecen en la matriz. QA-FIX-CAT-01, 16:328, incluye edición, preservación de categoría actual inactiva, código y búsqueda. RN-27 sustenta el precio final, RN-28 los datos históricos y RN-29 el control por rol. La matriz 03:282 vincula la advertencia de precio a BUG-006. Estos enlaces se contrastaron con el comportamiento efectivo.

## Pantalla, ruta, campos y mensajes

La entrada normal fue **Productos → Editar**, ruta `GET/POST /productos/<uuid>/editar/`, vista `product_edit`, formulario `ProductEditForm`, servicio `update_product` y plantilla `catalog/product_edit.html`. UUID inexistente devolvió 404. Los otros dos roles obtuvieron 403 en GET y POST autenticados con CSRF válido, y el visitante fue redirigido al ingreso. Se comprobó la conservación de la base tras rechazos. [Casos D01–D29 y subcasos](../evidencias/03-D-browser-20261110T030352675316Z/browser.json).

| Elemento | Contrato observado y casos |
|---|---|
| Nombre del producto | Precargado y obligatorio. Hasta 160 caracteres, con letra o número, espacios interiores colapsados. D18 rechazó vacío, 161 caracteres y «ATÚN OCUPADO» frente a «Atún ocupado». D27 aceptó 160. La búsqueda usa la clave casefold/NFC existente. Se conserva la distinción de tildes |
| Código de barras | Precargado, editable, obligatorio, hasta 64 caracteres. Admite letras ASCII, números, espacios y guiones. Su clave normalizada es única. D18 rechazó vacío, 65 y «du pli cado» frente a DUPLICADO. D27 aceptó 64. La ayuda describe los caracteres admitidos y la comparación |
| Categoría | Precargada, opcional en edición. Vacío conserva la actual. Ofrece activas y la actual, aun cuando esté inactiva. D17/D21/D25/D26 verificaron esas transiciones. El servicio lee de nuevo producto y categoría dentro de la transacción antes de confirmar la reclasificación |
| Precio final con IGV (S/) | Precargado, obligatorio, paso 0.01, rango de interfaz 0.01 a 9999999.99. D18 rechazó vacío, cero, negativo, 1.001, 1e2, texto y 10000000.00. D27 aceptó el máximo. D03 conservó dos decimales en persistencia y la salida mostró coma decimal |
| Existencia mínima | Precargada y obligatoria al editar. Rango actual 0 a 999999. D18 rechazó vacío, negativo, fracción, texto y 1000000. D27 aceptó el máximo. D11 comprobó la alerta exactamente en el umbral |
| Guardar cambios | POST válido redirige al catálogo y muestra «Producto «…» actualizado.». POST vacío devuelve cuatro errores obligatorios. Los rechazos conservan los datos. Al fallar precio, el mensaje se enlaza al campo y este recibe el foco |
| Cancelar | Se cambió precio a 11,00 en pantalla y se canceló. Regresó al catálogo conservando todos los datos del estado anterior. D02 |
| Vista móvil y nombres largos | Un mensaje de éxito con 160 caracteres continuos excedía el viewport. La envoltura del texto corrige el desbordamiento. Se reutilizó el estilo de campos y panel del alta. El caso final a 390 × 844 y las capturas muestran formulario, ayudas y acciones dentro del ancho |
| Históricos y borrador | La constancia se cotejó antes y después por texto renderizado y la línea histórica por persistencia. Se probaron cambios de precio, nombre, código y categoría. Las capturas muestran la advertencia y el nuevo total. El borrador final conserva una unidad a 9,20 |

El mensaje exacto del primer intento de cobro fue «El precio de «AUD03 Bebida de prueba» cambió de S/ 8.50 a S/ 9.20. Verifica el nuevo total antes de confirmar el cobro.». La revisión de la constancia se limitó a esta venta sintética. La impresión física, el conjunto de reportes y el ciclo completo de caja conservan sus auditorías propias. [Aviso al cobrar](../evidencias/03-D-browser-20261110T030352675316Z/07-aviso-precio.png) · [Error de edición](../evidencias/03-D-browser-20261110T030352675316Z/20-error.png) · [Móvil](../evidencias/03-D-browser-20261110T030352675316Z/28-movil.png).

## Correcciones y propuestas

- **FIX-03D-01, P2.** El POST vacío dejaba el formulario sin errores. Se usa un formulario enlazado también para un cuerpo vacío y se enfoca el primer error. Cada mensaje y ayuda tiene el identificador que el control referencia.
- **FIX-03D-02, P2.** La edición permitía duplicar el nombre al cambiar una vocal acentuada a mayúscula. Se reutiliza la clave normalizada que ya usaba el alta. La distinción de tildes y la decisión sobre dos escrituras previamente validadas permanecen en PROP-03C-NOMBRE.
- **FIX-03D-03, P1.** El servicio aceptó una categoría que se había desactivado después de cargar la selección. Ahora lee bajo bloqueo el producto actual y la categoría. El estado inactivo solo se conserva cuando corresponde a la categoría que el producto ya tenía. La muestra PostgreSQL confirmó rechazo y conservación del precio y categoría previos.
- **FIX-03D-04, P1 en datos previos.** El ModelForm ya había cambiado el código de la instancia cuando el servicio intentaba recuperar la relación de detalles antiguos sin `product_id`. Se toma el código anterior de la fila persistida. La nueva regresión usa un detalle antiguo sin vínculo, efectúa el POST real y comprueba asociación recuperada, código histórico EDIT-1 y precio histórico 8,50. Esta corrección conserva la política preexistente de recuperación por código anterior.
- **FIX-03D-05, P2.** El mensaje de éxito de un nombre largo producía desplazamiento horizontal. Se permite el salto del texto en los mensajes y en el encabezado del formulario. La plantilla usa los controles existentes del proyecto. Las ayudas y los mensajes de longitud reutilizan los límites del alta.
- **PROP-03D-BORRADOR, criterio propuesto para CA-01.** Dado un borrador con precio anterior, cuando ADMIN cambia la ficha y VENDEDOR confirma el cobro, mostrar la variación, recalcular el total pendiente y requerir una nueva confirmación. La primera confirmación conserva ventas y lotes. El comportamiento ya está implementado y verificado. Incorporar D06–D09 a la matriz de PROD-04 y enlazar BUG-006.
- **PROP-03D-HISTORICO, prueba propuesta para QA-FIX-CAT-01.** Dado un detalle heredado sin vínculo de producto y con el código anterior, al corregir el código desde el formulario recuperar la asociación y conservar los campos históricos. La regresión está implementada. La procedencia de datos heredados que hayan reutilizado códigos requiere evaluación propia en 12/15.
- **PROP-03D-ESTADO, prueba propuesta para CA-05.** Mantener dos casos en la matriz: conservar categoría actual inactiva al editar datos comerciales, y rechazar la reclasificación hacia otra categoría que se haya suspendido. Ambos casos están verificados. La simultaneidad amplia de edición, suspensión y cobro queda pendiente en 15.

## Ejecuciones, evidencia y límites

| Ejecución | Resultado y archivo |
|---|---|
| Chrome inicial | 46/51. Fallaron POST vacío, duplicado acentuado, conservación tras ese duplicado, asociación/foco del error y ancho móvil. [Antes](../evidencias/03-D-browser-20261110T030010177604Z/browser.json) |
| Django antes de corregir | Cuatro métodos, tres fallos. La prueba adicional de vínculo heredado también falló antes de corregir el código anterior. [Primera regresión](../evidencias/03-D-tests-20261110T030036511029Z/tests.txt) · [Detalle heredado](../evidencias/03-D-tests-20261110T030314191882Z/tests.txt) |
| PostgreSQL inicial | 3/4. La categoría suspendida fue aceptada. [Antes](../evidencias/03-D-postgresql-20261110T030130784258Z.json) |
| PostgreSQL intermedio | 4/4 funcionales. La verificación de conservación detectó el cambio de la base del navegador aislado que seguía ejecutándose en paralelo. Se identificó esa única base y se repitió PostgreSQL después del cierre del navegador. El resultado intermedio se conserva. [Registro](../evidencias/03-D-postgresql-20261110T030400515408Z.json) |
| Django final | **76/76 métodos**. Incluye los 73 de catálogo y tres regresiones puntuales de venta sobre precio/histórico. `check` y `makemigrations --check --dry-run` pasaron. [Log](../evidencias/03-D-tests-20261110T030339870193Z/tests.txt) |
| Chrome final | **51/51** comprobaciones, Chrome 157.0.8103.39. Tres roles y visitante, datos aislados, navegación, HTTP y persistencia. [Casos](../evidencias/03-D-browser-20261110T030352675316Z/browser.json) · [Cierre del proceso](../evidencias/03-D-browser-20261110T030352675316Z/result.json) |
| PostgreSQL final | **4/4**, PostgreSQL 18.4, read committed. Dos conexiones colisionaron al cambiar códigos, una fue rechazada y conservó su precio original. Se comprobó la reclasificación suspendida y la conservación de la categoría actual inactiva. [Resultados](../evidencias/03-D-postgresql-20261110T030458286776Z.json) |

La base final del navegador es `datos/etapa03d-20261110T030352675316Z/audit.sqlite3`. Contiene tres productos y tres categorías, un lote con 17 de sus 20 unidades iniciales, dos ventas, un turno OPEN y un borrador ACTIVE con una unidad. Los dos borradores previos quedan DISCARDED según el comportamiento actual de cobro. La primera venta a 8,50 se preparó con servicios del sistema como dato inicial. La segunda se confirmó mediante Chrome. [Fixture](../evidencias/03-D-browser-20261110T030352675316Z/fixture.json) · [Antes](../evidencias/03-D-browser-20261110T030352675316Z/orm-initial.json) · [Después](../evidencias/03-D-browser-20261110T030352675316Z/orm-final.json).

La conservación de la base original, las bases retenidas y el XLSX se cotejó por SHA-256. Los servidores de prueba terminaron. El recorrido amplía la evidencia de la etapa 03 y mantiene las etapas de venta, caja, inventario e históricos en sus estados anteriores. La suite completa del proyecto, teclado móvil físico, lector de pantalla y edición concurrente del mismo producto frente a cobro permanecen sin ejecutar en este corte. [Cierre y cobertura](../evidencias/03-D-cierre.json).

Ejecutar cada comando hasta que termine antes de iniciar el siguiente.

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03d_run.py' tests catalog sales.tests.SalesHistoryTests.test_price_change_during_checkout_warns_seller_and_updates_draft_line_price sales.tests.SalesHistoryTests.test_bug006_draft_warns_seller_when_catalog_price_changes_during_preparation sales.tests.ReceiptTests.test_receipt_uses_snapshots_not_live_product_data
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03d_run.py' browser
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03d_pg.py'
```

**Cursor exacto 03-E / HU-PROD-05 / CA-01, 08:254.** Crear otra base aislada con producto y categoría activos, lote vigente de 20 unidades, una venta histórica y un borrador ACTIVE de dos unidades en turno propio. ADMIN entra por Productos → Deshabilitar. VENDEDOR busca, actualiza la línea y trata de cobrar. Comprobar rechazos y conservación de lotes, histórico, turno y borrador. Después reactivar el producto con categoría activa e inactiva por separado y verificar la etiqueta comercial.

