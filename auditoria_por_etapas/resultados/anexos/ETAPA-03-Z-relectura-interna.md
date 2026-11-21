# 03-Z · Relectura de códigos internos y clasificación de fichas antiguas

11 de noviembre de 2026, hora de Lima. Se aplicó el protocolo común y se retomó el inventario de 03-Y. Este corte cubre HU-PROD-03/CA01–02 y HU-PROD-04/CA03. Se observó el alta de HU-PROD-02, la búsqueda de HU-PROD-01 y la consulta del vendedor en la frontera de venta.

## Inventario previo y trazabilidad

| Fuente y condición | Ruta, actor y acción | Resultado contrastado |
|---|---|---|
| Historias 08:231–232, 912 y 918. Captura temporal y revisión expresa | ADMIN abre «Escanear código» en `/productos/nuevo/`. «Código leído» empieza vacío, admite texto hasta 64 caracteres y conserva ceros y repeticiones. El diálogo comprueba el tipo y la disponibilidad | Se contrastaron texto temporal, botón «Usar código», campo del formulario y estado comercial. «Cancelar» conserva el campo de la ficha. Enter en la captura no registra productos. |
| Matriz 03:377, tareas 16:371 e identidad de 21:87 | ADMIN selecciona código interno, categoría activa, nombre y precio. «Registrar producto» envía la ficha al servidor | Dos lecturas producen dos entradas con límites definidos por Ctrl+A. El servidor recibe el código que se copió y confirmó. Una cadena concatenada puede ser por sí misma un código interno válido. |
| Historias 08:243 y decisión DOC03-02. RN-28/29 | ADMIN edita `/productos/<uuid>/editar/` y clasifica una ficha antigua como GTIN | Si otra ficha reserva una variante se muestra «Ya existe un producto con este código de barras». Deben conservarse las fichas y sus referencias. Si todas las variantes están libres o son propias, se conserva el UUID y se añade la reserva pertinente. |
| Consultas de catálogo y de venta y regla de roles | ALMACENERO entra por «Catálogo de productos» y VENDEDOR por «Preparar venta». Ambos buscan la variante de 14 dígitos de la ficha clasificada | Cada rol ve la misma ficha con seis unidades vigentes. Ambos recibieron 403 al solicitar la edición por GET y al enviar el formulario con token CSRF de su sesión. |

El [inventario previo del ensayo](../evidencias/03-Z-z-before-20261111T164236190387Z-f44e99df/inventory-before.json) identifica acciones, campos y salidas antes de sembrar datos. La base y las tres cuentas ficticias se crearon por ejecución. El navegador comprobó el identificador criptográfico del servidor local antes de iniciar sesión.

## Defecto y corrección

**H-03Z-01 · INCUMPLE antes de la corrección, prioridad alta.** Se reprodujo en Chrome la pérdida de selección entre el comando de reemplazo y el primer carácter. Se usó teclado automatizado y se colapsó expresamente la selección para aislar esa condición. El diálogo ofreció copiar `Z01Z01` al leer dos veces `Z01`, y `Z01NUEVO02` al leer dos etiquetas distintas. En el segundo caso el alta explícita guardó el valor concatenado en la base aislada. La observación física de 03-Y acredita la concatenación temporal allí registrada. Esta reproducción controlada identifica una causa suficiente, sin determinar el orden interno de los eventos del teléfono en aquella ejecución. [Caracterización y 14 comprobaciones](../evidencias/03-Z-z-before-20261111T164236190387Z-f44e99df/browser.json).

**Corrección verificada en Chrome.** El diálogo recuerda el comando Ctrl+A hasta la primera inserción y vuelve a seleccionar el contenido justo antes de escribir. Un movimiento voluntario del cursor con el teclado o el puntero conserva la edición manual. La corrección usa el comando de reemplazo y conserva códigos legítimos como `ABAB`, incluidos los de longitud máxima. Dos escaneos sin delimitador que entregan una sola cadena de longitud variable no pueden distinguirse a partir del texto recibido. El perfil ensayado del lector usa Ctrl+A seguido de BARCODE.

Con la corrección, las mismas secuencias dejaron `Z01` y `NUEVO02`. Se probaron además edición con la tecla Fin, cancelar, reemplazo con 64 caracteres, copia expresa, ausencia de POST durante la lectura y alta de una sola ficha `ABAB`. Las tres fichas antiguas se prepararon con lotes y ventas reales de prueba. Para las dos solapadas se intentó la clasificación en ambos sentidos y se cotejó toda la instantánea comercial después de cada rechazo. Para la tercera solo cambiaron el tipo y una reserva de lectura. Los saldos y detalles históricos coinciden con la instantánea anterior. **34/34 comprobaciones** en Chrome y **335/335 métodos** de regresión. [Casos de Chrome](../evidencias/03-Z-z-after-20261111T164646767674Z-a3a9756a/browser.json) · [Estado final](../evidencias/03-Z-z-after-20261111T164646767674Z-a3a9756a/orm-final.json) · [Regresión](../evidencias/03-K-tests-20261111T164543844233Z/result.json).

## Reproducción

Desde la raíz de trabajo, cada comando crea datos de ensayo nuevos. `z-before` describe la caracterización hecha con el JavaScript anterior a H-03Z-01. En el código corregido se usa `z-after`.

```powershell
$python = 'r1-pmv/.venv/Scripts/python.exe'
$support = 'auditoria_por_etapas/resultados/soporte'
& $python -X utf8 "$support/audit03y_browser_run.py" z-after
& $python -X utf8 "$support/audit03y_browser_run.py" z-phone
$env:AUDIT03K_DEFAULT_COOKIES = '1'
& $python -X utf8 "$support/audit03k_run.py" tests catalog inventory sales cash identity
Remove-Item Env:AUDIT03K_DEFAULT_COOKIES
```

Se conservaron los cambios preexistentes. La corrección está limitada al diálogo de captura. No hubo migraciones operativas en este corte. La recepción de mercancía mixta y los retiros sanitarios mantienen sus casos propios en el [traspaso de recepción y retiros](ETAPA-03-recepcion-y-retiros-pendientes.md).

## Lectura física y continuidad

Con las dos etiquetas Code 128 visibles a la vez y sin generar entradas por software, Chrome registró las dos primeras A exactas en 20 entradas y dos B exactas en la siguiente fase de 50 entradas. En conjunto hubo siete Ctrl+A y 70 eventos de entrada. El máximo fue diez caracteres, con cero valores fuera de los prefijos de las etiquetas, cero entradas en otros campos y cero Enter o Tab. Al terminar la captura, el campo definitivo seguía vacío. El soporte pulsó el botón real «Usar código», comprobó B como valor final y registró cero POST. La comparación inicial/final conserva productos, claves, lotes, ventas, líneas y borradores. [Registro físico](../evidencias/03-Z-z-phone-20261111T164928308022Z-13e15589/phone.json) · [Cierre y conservación](../evidencias/03-Z-z-phone-20261111T164928308022Z-13e15589/result.json).

Los dos intentos anteriores llegaron hasta A y cerraron el diálogo antes de completar B. En el primero hubo entradas que diferían de la etiqueta esperada. La evidencia no identifica su origen. Se conservaron ambos registros como incompletos y se sustituyó el cambio de imagen por dos etiquetas fijas. [Primer intento](../evidencias/03-Z-z-phone-20261111T164502190381Z-6948357a/phone.json) · [Segundo intento](../evidencias/03-Z-z-phone-20261111T164756108754Z-ff0c3b52/phone.json).

**PROD03/CA01 y PROD04/CA03: CUMPLE en las muestras indicadas.** La redacción vigente de CA01 identifica el campo temporal y el momento de la copia expresa según la adenda aceptada 08:912. El criterio original se conserva citado junto a la actualización. El ensayo no midió cantidades de mercancía recibida ni identificó un embalaje.

**03-AA / PROP-03-RET-T01, frontera catálogo–recepción**. Con tres artículos ficticios y un paquete de 12, contrastar el código exterior con el de unidad, identificar la ficha en las consultas autorizadas y verificar que la consulta por sí sola conserva los saldos. Trasladar el registro por proveedor, cantidad, lote y vencimiento a 05–06.
