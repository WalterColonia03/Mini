# Formularios y salidas generadas de la etapa 00

**Resultado del inventario 00-C.** La extracción obtuvo 18 clases propias de formulario y 53 campos efectivos, con el detalle del widget, la etiqueta, la obligatoriedad, las opciones, la ayuda, los límites, la limpieza, los validadores y sus mensajes disponibles. A estos se suma un formset fabricado por Django que reutiliza cuatro campos de lote y agrega cuatro campos técnicos de gestión. El JSON conserva cada registro por módulo, clase y campo, con las líneas de origen. [Datos de la extracción](ETAPA-00-formularios-generados.json).

Se ejecutó introspección con el intérprete del proyecto, Django 5.2.18, configuración de auditoría y traducción `es-pe`. El extractor construyó formularios vacíos, el formulario de gestión y los dos widgets iniciales de ingreso. Una barrera sobre la conexión rechazaba SQL durante la extracción, incluidas las consultas que resultarían de enumerar un selector de entidades. Las referencias a modelos de los selectores identifican qué entidad abastece cada lista. El anexo técnico previo permite localizar los valores calculados por las vistas, los controles escritos directamente en HTML y las llamadas de validación en servidor. Los estados de acceso, persistencia, mensajes visibles y pruebas funcionales conservan la evidencia de sus respectivas etapas.

## Ingreso y mensajes

La ruta pública `/` usa `identity/views.py:27`, `identity/forms.py:6` e `identity/templates/identity/login.html:21–27` dentro de `r1-pmv`. El formulario HTML envía POST y usa `novalidate`. El marcado conserva los atributos HTML `required` en los widgets. La vista decide la autenticación después de que Django limpie los campos. Con petición POST sin campos en absoluto, `request.POST or None` deja el formulario sin enlazar. Un envío del formulario normal proporciona los nombres de los campos y el control CSRF.

| Origen de UI | Condición, salida y efecto esperado según fuente | Planificación y caso que corresponde ejecutar |
|---|---|---|
| `login.html:22`, token CSRF | Control técnico oculto de Django para autorizar el origen de la petición. Su valor se genera por petición. | Rechazo de CSRF del ingreso en etapa 01; revisión transversal en etapa 15. |
| `login.html:23`, `next` | Control oculto condicional. La vista toma primero POST y luego GET. Tras autenticar, acepta el destino si pasa la comprobación de host y esquema, y en otro caso dirige a `dashboard` (`identity/views.py:32,38–45`). | Navegación de AUTH-01/CA-01 y CA-04. Confirmar que la vista destino vuelve a autorizar el rol. |
| **`login.html:24`, `form.non_field_errors`** | Cuando la vista asocia un error a `None`, se genera una lista en un contenedor con `role="alert"`. Correo de formato válido con credenciales rechazadas o cuenta inactiva devuelve **«Correo o contraseña incorrectos»**. El bloqueo presenta **«Demasiados intentos fallidos consecutivos. Inténtelo nuevamente en {minutos} minuto(s).»**. La vista recibe los minutos del servicio (`identity/views.py:46–50`, `identity/services.py:17,30–61`). | AUTH-01/CA-02–03 (`08:19–20`), AUTH-02/CA-01–03 y RN-17 (`08:30–32`). Ejecución dedicada en etapa 01. |
| **`login.html:25`, `form.email` y `form.email.errors`** | Etiqueta «Correo de trabajo», entrada vacía de tipo `email`, foco inicial, `autocomplete=username`, obligatoria y máximo 320. Django recorta espacios exteriores. En campo vacío figura «Este campo es obligatorio.», para formato inválido «Introduzca una dirección de correo electrónico válida.» y para carácter nulo «Los caracteres nulos no están permitidos.». El validador de longitud usa plural según el dato. Con parámetros 320 y 321, el catálogo instalado produce «Asegúrese de que este valor tenga menos de 320 caracteres (tiene 321).». Se formateó la plantilla del mensaje, sin ejecutar un intento de ingreso. La lista se presenta con `role="alert"` junto al campo. | Entrada de AUTH-01/CA-01–03. Los CA no prescriben el literal para formato ni la traducción del límite. Confirmar 319/320/321 y vacío en etapa 01. La definición de correo de cuenta tiene máximo 254 en `identity/models.py:61`. |
| **`login.html:26`, `form.password` y `form.password.errors`** | Etiqueta «Contraseña», entrada inicial vacía de tipo `password`, obligatoria, conserva los espacios (`strip=False`), `autocomplete=current-password`. La clase del formulario carece de límite explícito de longitud. Widget con `render_value=False` evita repoblar el valor al mostrar errores. Vacío y carácter nulo usan los mensajes de obligatoriedad y carácter nulo. La plantilla presenta los errores del campo en un contenedor con `role="alert"`. | Entrada y error de formato de AUTH-01. Corroborar rechazo y tratamiento de espacios con cuenta ficticia en etapa 01. |
| **`login.html:27`, botón «Iniciar sesión»** | POST a la página. Si la limpieza de formato falla, la vista vuelve a mostrar el formulario. Si pasa, el servicio normaliza el identificador y contrasta las credenciales. El camino aceptado usa una sesión de servidor con el rol de la cuenta. Las ramas de intentos usan `LoginAttempt`. La etapa 00-A registró el ingreso normal de tres roles. | AUTH-01/CA-01 y AUTH-02. Etapa 01 revisará los mensajes, los cambios de contador y la persistencia por cada escenario. |

Fuentes de la aplicación para la normalización y los efectos: `identity/models.py:78–79`, `identity/services.py:30–67`, `identity/views.py:33–50`. Fuentes del Django efectivamente instalado en `r1-pmv/.venv/Lib/site-packages/django/`: `forms/fields.py:85,202,275,625`, `core/validators.py:209,488,655`, `forms/widgets.py:397,422–430`, `forms/forms.py:253,264,324,341`, `forms/utils.py:141` y `forms/templates/django/forms/errors/list/ul.html:1`. La localización explica por qué el texto del máximo puede decir «menos de» aunque el comparador de `MaxLengthValidator` acepte igualdad. Se remite a la etapa 01 la comprobación del texto realmente visible para una entrada que alcance el servidor.

## Destino de cada formulario

Las fuentes de definición y los límites concretos de cada campo constan en el JSON, incluidas las configuraciones que se agregan en `__init__`. Los nombres de la segunda columna permiten saltar del registro a la vista específica. Los enlaces a HU corresponden al alcance candidato ya clasificado en la matriz documental.

| Clase | Vista y uso de negocio | Actor y etapa |
|---|---|---|
| LoginForm | `identity/views.py:33`, ingreso y errores | Visitante, tres roles con cuenta. 01 |
| EmployeeCreationForm | `identity/views.py:100`, alta de empleado | ADMIN. 02 |
| EmployeeEditForm | `identity/views.py:137`, datos cargados de la cuenta seleccionada y nueva contraseña opcional | ADMIN. 02 |
| CategoryForm | `catalog/views.py:49`, alta de categoría | ADMIN. 03 |
| ProductRegistrationForm | `catalog/views.py:99`, datos y umbral del producto nuevo | ADMIN. 03 |
| ProductEditForm | `catalog/views.py:123`, edición con instancia existente. Selector de categorías activas y categoría actual de la instancia según `catalog/forms.py:122–141` | ADMIN. 03 |
| SupplierForm | `inventory/views.py:176`, alta y contacto de proveedor | ADMIN. 04 |
| InitialLoadProductForm | `inventory/views.py:76`, selección de producto sin carga y proveedor activo opcional | ALMACENERO. 05 |
| StockEntryProductForm | `inventory/views.py:131`, selección de producto con carga y proveedor activo opcional | ALMACENERO. 06 |
| LotInputForm | `inventory/views.py:77,132`, número, unidades, costo y vencimiento por fila del formset en ambas altas | ALMACENERO. 05/06 |
| StockWriteOffForm | `inventory/views.py:229`, cantidad/motivo/detalle, lote y clave en campos ocultos | ADMIN y ALMACENERO. 08 |
| PhysicalAdjustmentForm | `inventory/views.py:291`, ajuste firmado y motivo, lote y clave en campos ocultos | ADMIN. 08 |
| CashOpeningForm | `cash/views.py:21`, monto inicial | VENDEDOR. 09 |
| CashCloseForm | `cash/views.py:67`, monto contado | VENDEDOR. 09 |
| ProductSearchForm | `sales/views.py:75`, búsqueda por GET | VENDEDOR. 10 |
| AddDraftLineForm | `sales/views.py:82`, recepción del producto y cantidad de la línea. Controles HTML manuales en `sales/templates/sales/sales_draft.html:52,54` con cantidad inicial 1 | VENDEDOR. 10 |
| UpdateDraftLineForm | `sales/views.py:128`, actualización de cantidad. La plantilla presenta el valor de la línea en `sales/templates/sales/sales_draft.html:84` | VENDEDOR. 10 |
| CheckoutForm | `sales/views.py:188,229`, importes, clave, subtotal esperado y firma. Los valores iniciales de estos últimos provienen del borrador o de una clave generada por la vista | VENDEDOR. 11 |

Los formularios estándar muestran los atributos generados en la situación inicial. La vista puede poblar campos con un empleado, producto, lote seleccionado o borrador. Los errores de negocio añadidos por vistas/servicios y las condiciones de presentación de cada plantilla se consultan en [inventario del código](ETAPA-00-inventario-codigo.csv). Las pruebas de flujo definirán el valor persistido, los mensajes visibles y el comportamiento de rechazo. Nombres de tipos tales como `PasswordInput` u «oculto» identifican dos propiedades distintas: el último indicador del JSON corresponde a un control de tipo `hidden`.

## Filas dinámicas de lotes

La factoría `inventory/forms.py:107` configura `LotInputFormSet`. En ambos formularios la vista usa el prefijo `lots`. En una instancia vacía se obtienen 4 filas (mínimo 1 más 3 adicionales). Los nombres de controles por fila adoptan la forma `lots-0-number`, `lots-0-quantity`, `lots-0-unit_cost` y `lots-0-expiration_date`, seguidos por los índices siguientes. La plantilla de carga inicial inserta el formulario de gestión, los errores del conjunto y las filas en `inventory/templates/inventory/initial_load_form.html:44–53`. La de entrada hace lo propio en `inventory/templates/inventory/stock_entry_form.html:42–51`.

Los campos de gestión ocultos son `lots-TOTAL_FORMS` (inicial 4), `lots-INITIAL_FORMS` (0), `lots-MIN_NUM_FORMS` (1) y `lots-MAX_NUM_FORMS` (1000). Los dos primeros son obligatorios. El servidor tiene `validate_min=True`, `validate_max=False`, `max_num=1000` y `absolute_max=2000`. Esos números describen la configuración técnica de Django. Las etapas 05/06 deberán identificar el límite comercial aceptado y observar errores de gestión, filas incompletas, validación de lote y persistencia atómica.

## Reproducción y comprobación

Desde la raíz se ejecuta el extractor con el entorno Python del proyecto.

```powershell
& './r1-pmv/.venv/Scripts/python.exe' './auditoria_por_etapas/resultados/anexos/inventariar_formularios_00.py'
```

El comando regenera exclusivamente el JSON derivado del censo. Las 53 claves clase/campo corresponden a los 42 campos explícitos y 11 derivados de ModelForm del inventario inicial. La fase de metadatos se ejecutó con bloqueo de SQL. **Estado funcional de 00-C: NO EJECUTADO.** Las comprobaciones de 00-A y 00-B permanecen en sus evidencias fechadas. El próximo caso funcional corresponde a **etapa 01, HU-AUTH-01/CA-01, `08_Historias_de_Usuario.md:18`, GET y POST de `/` en la instancia aislada**.
