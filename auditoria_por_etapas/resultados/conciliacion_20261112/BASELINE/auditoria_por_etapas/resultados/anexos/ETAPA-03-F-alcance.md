# Etapa 03-F · Alcance aceptado del catálogo y conciliación de actores

**09/11/2026, America/Lima. DOC03-01 resuelto por decisión expresa del usuario.** Respuesta: «Productos de cualquier categoría, por unidad y con vencimiento obligatorio». DOC-00-14 se concilia con el pedido original: Administrador y almacenero; vendedor solo en consultas de venta autorizadas. No se infiere la aceptación de otros cambios a partir de estas decisiones.

## Inventario previo, versión y autoridad

El [manifiesto previo](../evidencias/03-F-inventario-20261110T034057076474Z.json) identifica dos elementos: HU-PROD-02/CA01 (08:218, DOC03-01) y actores de HU-PROD-01 (08:203, DOC-00-14), pantallas, campos, mensajes, reglas y tareas, además de hashes de fuentes y datos protegidos. Se leyó el protocolo completo y el estado general. No se encontraron nuevas instrucciones AGENTS en el tramo. La skill ui-ux-pro-max, ya utilizada en esta auditoría, orientó la revisión acotada de ayudas/etiquetas; no hubo rediseño de página.

La clasificación inicial era CONFLICTO DE FUENTES: DEC-04 en01:94, RN03 en07:76 y PROD02/CA01 limitaban enlatados/categoría preparada, mientras08:876 y16:328 habilitaban categorías activas arbitrarias. La decisión del usuario sustituye esa restricción para el catálogo actual, sin reescribir la selección, estimaciones o resultados históricos de R1. La HU y CA actuales se actualizaron con fecha y referencia de decisión. No se rebajó unilateralmente el criterio para aprobar la implementación.

| ID / actor / fuente | Requisito vigente | Implementación y evidencia | Estado y siguiente acción |
|---|---|---|---|
| HU-PROD-02/CA01 · ADMIN · 08:218 revisado por DOC03-01 | Registrar en cualquier categoría activa, UND y control de vencimiento obligatorio; inactiva/inexistente rechazada sin alta | Formulario→servicio→modelo; F01/F02, C01/C04/C09/C16/C17/C21 de esta ejecución;20 métodos | **CUMPLE muestra03-F, criterio revisado por decisión aceptada**. Históricos03-A aE conservan CONFLICTO |
| HU-PROD-01 actores · ADMIN/ALMACENERO; VENDEDOR en venta · 08:203 | Consulta administrativa para ADMIN/ALMACENERO; consulta del vendedor mediante venta autorizada | F03/F04, C11–15/C19, regresión ProductListTests | **DOC-00-14 conciliado** con instrucción original. No añade permiso de vendedor al catálogo |
| Categoría / unidad / vencimiento | Selección de UUID activo; UND único; bandera de control no editable y true | C09 rechaza vacío/inactiva/inexistente y KG. F02 repite KG en Higiene. C17 envía controls_expiration=false y conserva true/UND/stock0 | Implementación existente verificada. No se admite peso ni omitir vencimiento |
| Alta: título, ayuda principal y panel lateral | «Registrar producto»; categoría activa, por unidad y vencimiento obligatorio | product_form.html; F01 y capturas escritorio/móvil | Texto actualizado y verificado. Campos, límites y rutas conservados |
| Decisiones restantes | Código editable, homónimos, máximo del mínimo y propuestas de estado | No forman parte de DOC03-01 | Pendientes según informe general; no aceptadas por inferencia |

## Cambios concretos

1. `catalog/templates/catalog/product_form.html`: título «Registrar producto» y ayudas aplicables a todos los productos admitidos. No cambian modelo, formularios de datos, servicios, rutas ni permisos.
2. `08_Historias_de_Usuario.md`: título/historia/CA01 de PROD02 y actores de PROD01. Registro de revisión añadido al final con redacción previa y nueva, decisión, fecha y límites. Las líneas de los criterios originales se conservaron en esta revisión.
3. `07_Reglas_de_Negocio.md`: RN03 distingue R1 histórico del alcance actual; RN30 extiende la descripción del cálculo uniforme existente a los productos del catálogo. Se mantiene la regla local del software, sin evaluar tratamiento tributario real de otras categorías.
4. Adendas en01,02,03,09,16 y21: alcance actual, contrato técnico ya existente, matriz vigente, tareas documentales/UI/pruebas y decisión trazable. Se conservan las tablas históricas de sprints, puntos, fechas y categorías preparadas. `14_Sprint_Planning.md`, CONTROL_SPRINTS y XLSX permanecen sin cambios.

El servicio mantiene su nombre interno `register_canned_product` y la restricción `product_unit_und_in_r1` por compatibilidad; esos identificadores no imponen clasificación comercial. No se cambió código por cosmética ni se creó una migración innecesaria. La fiscalidad por categoría, productos por peso/sin vencimiento y las HU futuras de editar/eliminar categorías y escáner no se implementaron aquí.

Tareas nuevas trazadas en16: **AUD03F-DOC01** aplicada; **AUD03F-UI01** implementada y verificada; **AUD03F-TEST01** ejecutada en la muestra indicada. Son tareas de auditoría, no nuevas historias ni aceptación retroactiva de Sprint1.

## Entorno y pruebas nuevas

Base nueva `datos/etapa03f-20261110T034318782440Z/audit.sqlite3`, tres cuentas ficticias y visitante, servidor localhost con puerto efímero y prueba HMAC antes de ingresar, sin cargar `.env`. Chrome157.0.8103.39/Playwright, escritorio1366×768 y móvil390×844. Capturas posteriores al ingreso, sin secretos. El runner conserva las bases anteriores y la original por hash; servidor propio detenido al final.

| Ejecución | Resultado exacto | Evidencia |
|---|---|---|
| Regresión de alta y consulta | **20/20 métodos**: ProductRegistrationTests, RegistrationBoundaryTests, ProductListTests y alta en categoría personalizada. Check y detección de migraciones sin incidencias | [Resultado](../evidencias/03-F-tests-20261110T034307344201Z/result.json) · [Log](../evidencias/03-F-tests-20261110T034307344201Z/tests.txt) |
| Chrome/HTTP/ORM | **53/53 comprobaciones**, sin error de soporte:49 casos del flujo de alta repetidos y4 verificaciones explícitas F01–F04 de esta decisión | [Casos](../evidencias/03-F-browser-20261110T034318782440Z/browser.json) · [Cierre del servidor](../evidencias/03-F-browser-20261110T034318782440Z/result.json) |
| Persistencia | Tres productos con UND/controls_expiration=true, sin lotes, cargas, ventas o borradores; turno ficticio OPEN conservado | [Inicial](../evidencias/03-F-browser-20261110T034318782440Z/orm-initial.json) · [Final](../evidencias/03-F-browser-20261110T034318782440Z/orm-final.json) |

F01 comprueba título y ayudas. C16 registra Jabón neutro/HIG-01 en Higiene con0,01 y mínimo0. F02 rechaza KG sin cambios de negocio. F03 lo muestra al almacenero sin stock. F04 busca como vendedor y confirma ausencia de Agregar por stock0; GET directo al catálogo devuelve403. C17 intenta false para vencimiento, stock75 y costo20; se guarda con controltrue, cero lotes y costo0. C21 desactiva Higiene desde otra pestaña y rechaza la selección antigua, sin nueva ficha. Los otros rechazos y fronteras están identificados individualmente en browser.json.

La muestra termina con tres categorías: Productos enlatados activa, Higiene suspendida por el casoC21 y Suspendida inactiva desde preparación. Los tres productos siguen individualmente activos. Las cuentas/sesiones y el turno OPEN son ficticios y se retienen; no se afirma cerrar caja. La comparación cubre los campos de `snapshot()` documentados en03-E, no todas las tablas del sistema.

Capturas inspeccionadas: [formulario vigente](../evidencias/03-F-browser-20261110T034318782440Z/01-alta.png), [alta en Higiene](../evidencias/03-F-browser-20261110T034318782440Z/16-otra-categoria.png), [móvil](../evidencias/03-F-browser-20261110T034318782440Z/20-movil.png). Texto legible y formulario sin desbordamiento del documento en390px. No se ejecutó lector de pantalla físico ni otros navegadores.

No hubo ejecución nueva de PostgreSQL: el cambio funcional es texto y no modifica validaciones, SQL, bloqueos ni esquema. Las carreras de03-C/D/E siguen siendo evidencia fechada de sus cortes; no se cuentan como pruebas nuevas. Suite global, carga por lotes del producto de higiene y cobro posterior de ese artículo NO EJECUTADOS en03-F; sus módulos mantienen su cobertura propia.

## Reproducción y cierre

Ejecutar desde la raíz, secuencialmente; cada ejecución crea datos nuevos y conserva los anteriores:

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03f_run.py' tests catalog.tests.ProductRegistrationTests catalog.test_audit03_registration catalog.tests.ProductListTests catalog.tests.ProductExpirationsTests.test_active_custom_category_can_be_used_to_register_product
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03f_run.py' browser
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/cierre_etapa03f.py'
```

El último comando verifica las evidencias fechadas enlazadas en este anexo, fuentes y datos protegidos. [Cierre reproducible](../evidencias/03-F-cierre.json). Los cierres anteriores conservaron sus criterios y hashes históricos; no deben ejecutarse como si fueran expectativas del código/documentación actuales.

Balance vigente: **19 CUMPLE en la muestra, 1 PARCIAL, 1 CONFLICTO DE FUENTES y6 PREVISTO/FUTURO**, sobre27 criterios. La transición de PROD02-CA01 se debe a decisión aceptada más verificación nueva, no a reetiquetar el pasado. Cursor: **03-G / DOC03-02 / HU-PROD-04 CA03 (08:243 frente a08:872)**, política de código editable. Las alternativas siguen documentadas; cualquier decisión posterior tendrá su propio registro. Luego máximo del mínimo y homónimos. No se inició ni cerró otra etapa.
