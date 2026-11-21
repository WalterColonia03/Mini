# 03-Y · Identidad de productos al leer el código de barras

11 de noviembre de 2026, America/Lima. El administrador distingue expresamente «GTIN de fabricante» y «Código interno». El usuario eligió esta política después de revisar el análisis de la copia original. El fallo de referencia es H-03X-01: la etiqueta `0012345678905` entregaba `012345678905` al navegador y la aplicación ofrecía crear otra ficha. [Observación anterior](ETAPA-03-X-codigos-ean-upc.md).

## Alcance, inventario y decisión

Se leyeron el protocolo y el estado general. Se retomó el inventario W/X de HU-CAT-01..04 y PROD-01..05. Este sublote cubre PROD02/CA03 (alta), PROD03/CA01–02 (lectura y aviso), PROD04/CA03 (edición e históricos) y la búsqueda de PROD01/CA02 y VEN01b como frontera. RN-28/29 respaldan históricos y roles. Fuentes: 08:208,220,231–232,243 y916, matriz03, adendas09/16/21 y DEC-03X-IDENTIDAD. [Inventario previo sobre datos](../evidencias/03-Y-identity-20261111T161915632116Z/inventory-before.json).

| Acción y fuente | Actor, entrada y salida | Comprobación |
|---|---|---|
| Registrar, PROD02 | ADMIN, `/productos/nuevo/`. Tipo requerido sin selección inicial, código textual de hasta64 caracteres, categoría, nombre, precio y mínimo. La confirmación muestra tipo y código ingresados | GTIN requiere control válido en 12/13 dígitos o 14 con primer dígito cero. El interno admite el formato literal anterior, incluidos ceros iniciales. Una colisión con ficha activa o inactiva impide el alta. |
| Escanear, PROD03 | ADMIN, diálogo de captura y campo manual. Consulta GET `/productos/codigos/comprobar/` con código, tipo e ID propio opcional. El botón Usar código copia después de revisión | Compara las representaciones reservadas por otras fichas. Mensaje «El código de barras ya está registrado» y botón deshabilitado. Si el usuario cambia de tipo se invalida la consulta anterior. |
| Editar, PROD04 | ADMIN, `/productos/<uuid>/editar/`. Elección de tipo y código, instantánea firmada y Guardar cambios | Editar una variante propia conserva el UUID. Las fichas antiguas permiten conservar la clasificación pendiente o elegir tipo. La firma incluye tipo para detectar ediciones simultáneas. |
| Buscar, PROD01/VEN01b | ALMACENERO/ADMIN, catálogo por `q`. VENDEDOR, consulta autorizada en `/ventas/` por `query` | La búsqueda exacta reconoce las variantes reservadas. El catálogo conserva búsqueda parcial. La suma de unidades vigentes corresponde al producto. Consulta sin altas, cobros ni movimientos. |
| Reserva de lecturas y migración0007, PROP-03X-T01..03 | Tarea técnica. Una clave de lectura única en `ProductBarcodeKey` pertenece a un solo UUID. Producto y cambios de claves se guardan dentro de la misma transacción | Los internos y anteriores reservan una clave normalizada literal. El GTIN reserva su representación de14 y las formas de13/12 obtenidas únicamente del relleno permitido. Se comprueba cruce interno↔GTIN en ambos órdenes. |

Se conservaron como alternativas históricas la identificación literal y el mantenimiento manual de alias. Se implementó la segunda alternativa del anexo X, clasificación expresa. Longitud y dígito de control describen el formato. El administrador determina el tipo a partir del artículo. No se consultaron identificadores comerciales reales en servicios externos. La representación con ceros de relleno sigue la guía de GS1. El cálculo no verifica titularidad ni asignación. [GS1, sección 4.3](https://ref.gs1.org/guidelines/2d-in-retail/1.1.0/) · [GS1, alcance de la comprobación del dígito](https://www.gs1.dk/en/vaerktojer/beregn-dit-kontrolciffer).

## Datos y resultados

- Preflight en copia nueva y abierta solo para lectura. Cinco fichas activas de13 dígitos, cinco claves normalizadas coherentes, cero colisiones y cero códigos con dígito de control GTIN válido. Ningún tipo inferido. 15/15 comprobaciones sintéticas del clasificador. Sin cambios en copia ni fuente. [Resultados](../evidencias/03-Y-identity-20261111T161915632116Z/result.json).
- Migración ensayada en **otra** copia SQLite. Se aplicaron 0003–0007. Quedaron cinco fichas UNCLASSIFIED y cinco claves literales de sus propietarios. Se cotejaron filas y columnas comerciales anteriores, UUID, relaciones, ventas e inventario. Integridad correcta y cero incidencias FK. El SHA256 de la base original se conservó. [Ensayo de migración](../evidencias/03-Y-migrations-20261111T162718225424Z/result.json).
- Chrome real, SQLite aislado, roles ADMIN/ALMACENERO/VENDEDOR y desafío HMAC antes de autenticación. 41/41 comprobaciones con entrada automatizada. GTIN13 → aviso de duplicado con12 y14, rechazo íntegro al intentar guardar un interno solapado. Un dígito de control erróneo se rechazó como GTIN y se aceptó como interno. En edición el cambio a una representación propia conservó UUID y detalle histórico. Con siete unidades recibidas y una vendida, tanto nombre como variantes mostraron seis unidades. Consulta de gestión denegada al vendedor y almacenero. [Recorrido](../evidencias/03-Y-browser-20261111T162549906985Z-9e883df0/browser.json) · [Captura](../evidencias/03-Y-browser-20261111T162549906985Z-9e883df0/duplicado-GTIN.png).
- PostgreSQL aislado. Cuatro pares de altas concurrentes en categorías distintas con espera real `transactionid`. En cada par se creó una ficha con sus claves y se rechazó la segunda con error de duplicado. Incluye GTIN→GTIN, interno→GTIN, GTIN→interno y variante14→12. [Resultados](../evidencias/03-Y-postgresql-20261111T162803982769Z.json).
- Regresión final en SQLite de prueba: 335/335 métodos, incluidos casos de colisión entre dos anteriores al intentar clasificar uno, inactivos y formatos no admitidos. Chequeos Django y migraciones sin cambios por generar. La primera corrida de332 métodos registró11 errores/fallos por formularios históricos sin el nuevo campo obligatorio, sus aserciones dependientes y el número de campos requerido. Se actualizaron las entradas de prueba y se concentró el mensaje de duplicado del formulario en la validación del modelo. [Corrida inicial](../evidencias/03-K-tests-20261111T162459264125Z/result.json) · [Corrida final](../evidencias/03-K-tests-20261111T162903761819Z/result.json).

## Reproducción y límites

Ejecutar con el Python del proyecto, desde la raíz. Cada runner crea su entorno aislado y conserva las bases anteriores. Los modos `browser` y `phone` se ejecutan por separado. El segundo requiere un operador con cámara y Chrome visible.

```powershell
$py = 'r1-pmv/.venv/Scripts/python.exe'
$s = 'auditoria_por_etapas/resultados/soporte'
& $py -X utf8 "$s/audit03y_preflight.py"
& $py -X utf8 "$s/audit03y_migrations.py"
& $py -X utf8 "$s/audit03y_browser_run.py" browser
& $py -X utf8 "$s/audit03y_pg.py"
& $py -X utf8 "$s/audit03y_browser_run.py" phone
$env:AUDIT03K_DEFAULT_COOKIES='1'
& $py -X utf8 "$s/audit03k_run.py" tests catalog inventory sales cash identity
Remove-Item Env:AUDIT03K_DEFAULT_COOKIES
```

El alcance implementado comprende GTIN-12 y GTIN-13 de artículos unitarios y sus representaciones con relleno. UPC-E, EAN-8, identificación de cajas, conversión caja→unidad y recepción de varios productos requieren casos propios. La migración operativa y la clasificación humana de los cinco registros siguen pendientes. Los servicios antiguos que omiten tipo conservan la compatibilidad como sin clasificar. El alta comercial exige una elección. Las escrituras masivas o SQL ajenas a los servicios no constituyen una vía auditada de gestión de claves. Los retiros y la cuarentena por lote siguen en el [traspaso de recepción y retiros](ETAPA-03-recepcion-y-retiros-pendientes.md).

## Prueba física, repetición y continuidad

El teléfono conectado emitió 180 entradas de teclado de confianza en 15 tandas de 12 dígitos y 15 Ctrl+A. Al final de 12 tandas el campo temporal contenía el UPC12 exacto. En dos contenía dos copias concatenadas y en una contenía tres. El último valor fue el UPC12 exacto. Chrome mostró «El código de barras ya está registrado», deshabilitó «Usar código» y dejó vacío el campo definitivo. Cero Enter, Tab, POST o entradas en otros campos. La comparación anterior/posterior incluyó fichas, claves, lotes y registros comerciales. Pasaron los 9 controles físicos. El rótulo 03-X en la captura procede del instrumento reutilizado; el directorio, la selección GTIN y los controles identifican esta ejecución 03-Y. [Registro de teclado y controles](../evidencias/03-Y-phone-20261111T162954154680Z-6afbba6d/phone.json) · [Captura](../evidencias/03-Y-phone-20261111T162954154680Z-6afbba6d/observed.png).

Se reprodujeron en Chrome ambos valores concatenados de 24 y 36 dígitos como GTIN. En cada caso el diálogo bloqueó la copia y el servidor rechazó el intento de alta manual. El cotejo de la base aislada confirmó que ninguna fila comercial cambió. Pasaron 47/47 controles en esta segunda corrida automatizada. Los internos de longitud variable requieren un caso separado porque una repetición puede ser parte legítima de su código. [Pruebas por caso](../evidencias/03-Y-browser-20261111T163627687822Z-baab0881/browser.json).

**03-Z / AUD03Z-RELECTURA-INTERNA01**. En Chrome aislado, seleccionar código interno y reproducir una secuencia delimitada con Ctrl+A en la que llegan concatenadas dos lecturas iguales y dos distintas. Contrastar con un código interno legítimo de patrón repetido. Verificar el valor temporal, la confirmación de copia, el POST y el estado comercial antes/después. Después, PROD04/CA03: probar por navegador dos fichas antiguas con representaciones solapadas e históricos, y una tercera sin solapamiento.
