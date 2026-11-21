# Superficie de la aplicación y navegación entre pantallas

Etapa 00-C, 9 de noviembre de 2026, America/Lima. El [índice por ocurrencia](ETAPA-00-superficie-ui.csv) permite seguir un elemento desde su plantilla o función de servidor hasta sus rutas de origen, actor declarado, destino, HU o propuesta candidata, reglas asociadas y etapa de comprobación. La clasificación funcional de esta extracción es **NO EJECUTADO**. Los casos que sí se observaron en navegador tienen sus resultados individuales en el [informe principal](../ETAPA-00.md).

## Cobertura del índice

El generador comprobó archivo y número de línea de las 2.446 filas del [inventario original](ETAPA-00-inventario-codigo.csv). Seleccionó las 1.859 ocurrencias correspondientes a interfaz y mensajes, conservando su número de registro CSV, contado desde 1 sin cabecera. Las otras 587 filas pertenecen a modelos, servicios, pruebas y otras definiciones que conservan su clasificación en el inventario original.

| Origen | Registros | Contenido |
|---|---:|---|
| Índice de código | 1.859 | 36 plantillas, 359 elementos, 916 textos, 359 expresiones dinámicas, 9 acciones JavaScript y 180 llamadas de mensajes del servidor |
| Extracción complementaria de plantillas | 459 | 328 aperturas o alternativas de condiciones y bucles, 106 referencias nominales a URL, 23 controles CSRF y 2 recursos estáticos de la base |
| Extracción complementaria de servidor | 29 | 28 destinos de redirección, incluido el retorno dinámico, y el mensaje constante de credenciales inválidas |
| Presentación y cálculo en cliente | 20 | 12 expresiones de cálculo del cobro y 8 condiciones de presentación CSS por medio o ancho |
| **Total** | **2.367** | Localizaciones de fuente. Un envío puede tener registros distintos para botón, etiqueta, condición, mensaje y destino. |

Cada fila clasifica una función de presentación o interacción y señala una comprobación futura. Para reconstruir una pantalla, filtrar por `fuente`, ordenar por `linea` y consultar las condiciones de las filas `rama_plantilla`. `contexto_al_inicio_de_linea` indica los bloques abiertos al empezar esa línea. Las ramas que empiezan o terminan dentro de la misma línea se distinguen por su expresión y orden en la fuente. `actor_de_la_ruta` indica quién puede llegar a la vista según el código. La condición de la plantilla puede limitar quién llega a ver una columna o un botón.

Las columnas HU/RN contienen candidatos procedentes del [mapa inverso de rutas](ETAPA-00-cobertura-inversa.csv). Una RN se atribuye a la HU de la pantalla o del destino y requiere cotejo con la fila particular. Los enlaces pueden asociar un mismo elemento con la HU de origen y la HU del destino. Las columnas vacías de requisito o regla significan atribución pendiente o pieza transversal. Para los cuatro extras se incluyen las propuestas y decisiones registradas en el [anexo de extras](ETAPA-00-extras-inversos.md). La aceptación de los criterios corresponde a las etapas funcionales.

## Cobertura de pantallas y acciones

| Superficie | Plantillas del tramo | Acciones o salidas cuya comprobación queda en cola |
|---|---|---|
| Identidad y personal | `login`, `dashboard`, `logout_confirm`, `employee_list`, `employee_form`, `employee_edit` | Iniciar/cerrar sesión, distinguir errores de credenciales y de formato, menú por rol, operaciones sobre empleados y métricas/alertas. Etapas 01, 02 y 13. |
| Catálogo | `category_list`, `category_form`, `product_list`, `product_form`, `product_created`, `product_edit`, `product_expirations` | Filtrar catálogo, registrar/editar, cambiar estado, comprobar confirmación y consultar próxima caducidad. Etapas 03 y 07. |
| Proveedores, entradas e inventario | `supplier_list`, `supplier_form`, `initial_load_form`, `initial_load_created`, `stock_entry_form`, `stock_overview`, `writeoff_form`, `adjustment_form`, `product_movements` | Proveedor, formularios repetidos de lotes, responsables, constancia, estado y alertas de stock, merma, ajuste y movimientos. Etapas 04–08. |
| Caja | `cash_open`, `cash_shift_opened`, `cash_close`, `cash_shift_closed`, `cash_shift_history` | Apertura, titular, diferencia de cierre, acta imprimible, filtros/consulta de turnos y alcance de datos por rol. Etapas 09 y 12. |
| Ventas | `sales_draft`, `sales_checkout`, `sales_receipt`, `sales_shift_history`, `sales_history` | Búsqueda, adición/cambio/retiro de líneas, descarte, cobro, descuento, vuelto, constancia imprimible e historiales. Etapas 10–12. |
| Transversal | `identity/base.html`, `403.html`, `404.html` | Navegación condicional, avisos flash, roles y estados de error. Base heredada y plantillas de error de Django. Etapas 01, 02, 14 y 15 según elemento. |
| Sin llamada de render localizada | `identity/protected_placeholder.html` | El texto «La preparación y el cobro de ventas aún no están disponibles» convive en el árbol con rutas activas de ventas. La inspección de referencias no encontró una vista que utilice la plantilla. Estado NO EXAMINADO en uso. Mantener separada de las promesas efectivamente observadas. Comprobación de vigencia en etapa 17. |

El censo por archivos y los índices de rutas concuerdan. De las 36 plantillas, 32 aparecen en una llamada directa de render de las vistas inventariadas. Las otras cuatro se identifican individualmente en las últimas dos filas. Las dos parejas de alias de confirmación de producto y carga reutilizan pantallas. Las siete acciones sin plantilla directa redirigen a sus respectivas listas o borrador. Los destinos tras cambiar estado de empleado, categoría, producto o proveedor están en `identity/views.py:179`, `catalog/views.py:72,156` e `inventory/views.py:207`. Actualizar, retirar una línea y descartar el borrador regresan a ventas en `sales/views.py:146,157,166`. Todas las referencias nominales `{% url %}` de las plantillas propias resuelven a uno de los 41 nombres de negocio del índice.

Para las 180 llamadas de mensajes se ubicó su función generadora y ruta candidata en 179 casos. La restante es `PermissionDenied` del decorador compartido en `identity/authorization.py`. La ruta que recibe la solicitud determina la pantalla de denegación. El mensaje común de autenticación se identifica además en `identity/services.py:17`. Los textos específicos de validación incorporados por Django y los campos generados por formularios tienen su inventario en el sublote de formularios. En una vista con varios servicios posibles, la asignación es una guía para verificar la llamada y el efecto. Puede haber errores lanzados por más de una ruta.

## Salidas JavaScript y presentación

`sales/templates/sales/sales_checkout.html:88–121` contiene el bloque de JavaScript propio. El cálculo local lee el subtotal, interpreta decimales con punto o coma, usa céntimos enteros, actualiza total/base/IGV/vuelto y presenta un guion en las ramas inválidas. Recalcula al introducir descuento o efectivo. Etapa 11 comparará esa presentación con las cifras guardadas y los mensajes del servidor. Los botones de acta de cierre y constancia solicitan la impresión del navegador en `cash/templates/cash/cash_shift_closed.html:40` y `sales/templates/sales/sales_receipt.html:13`. La regla de impresión en `identity/static/identity/app.css:510` oculta la navegación y los controles marcados para la salida impresa. Son candidatos de comprobación en etapas 09 y 12.

La plantilla base enlaza dos recursos locales, el icono y la hoja de estilos. La búsqueda en los archivos propios del proyecto activo no encontró archivos JavaScript externos. Los ocho bloques `@media` indexan condiciones de presentación, incluida la reducción de movimiento. La adaptación visual y la impresión tienen estado NO EJECUTADO en esta extracción. Las bibliotecas, sus plantillas administrativas y los recursos del proyecto externo de referencia quedan en sus censos separados.

## Reproducción y límites

Ejecutar desde la raíz del proyecto. El script usa la biblioteca estándar de Python, trata las fuentes como texto y sobrescribe únicamente el CSV derivado de esta superficie.

```powershell
& './r1-pmv/.venv/Scripts/python.exe' './auditoria_por_etapas/resultados/anexos/inventariar_superficie_00.py'
```

El generador comprueba las 36 rutas de archivos de plantilla, las 41 rutas del mapa de negocio, las coordenadas de los registros originales y que cada ocurrencia UI original tenga una sola fila de procedencia. Los 508 registros adicionales quedan con el número de origen vacío y conservan archivo y línea. El índice describe condiciones escritas, posibles salidas y su procedencia. La combinación de parámetros, sesiones, datos y estados que hace aparecer cada variante se comprobará en la etapa asignada. El primer caso funcional de ingreso sigue siendo HU-AUTH-01/CA-01 en la etapa 01.
