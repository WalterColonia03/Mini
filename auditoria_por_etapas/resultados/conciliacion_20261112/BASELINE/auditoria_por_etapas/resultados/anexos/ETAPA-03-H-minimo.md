# Etapa 03-H · Stock mínimo: contrato entre formulario y servicio

Informe actualizado el **10/11/2026, America/Lima**. Las ejecuciones conservadas ocurrieron el **09/11, 23:26–23:30 de Lima** (10/11, 04:26–04:30 UTC). Sublote técnico concluido; decisiones de máximo y nombres pendientes. No se modificó el alcance aceptado de categorías, unidad, vencimiento ni código editable.

## Inventario y trazabilidad del sublote

Se leyó completo el protocolo y se retomó el cursor de03-G. Inventario anterior a la corrección: [03-H-inventario](../evidencias/03-H-inventario-20261110T042627868086Z.json). Se contrastaron HU-PROD-02/CA04 (08:221), HU-PROD-04/CA02 (08:242), RN06 (07:102–108), autorización RN29, PROP-03C-LIMITES y PROP-03C-NOMBRE. El código de formularios, modelo, servicios y rutas permite seguir ambas direcciones; los demás campos conservan la auditoría03-C/D y no se presentan como reejecutados íntegramente.

| Elemento, actor y fuente | UI / servidor / salida | Esperado y observado | Estado y siguiente acción |
|---|---|---|---|
| PROD02-CA04, ADMIN; RN06 | Menú Registrar producto → GET/POST `/productos/nuevo/`; ProductRegistrationForm → register_canned_product → Product.clean_fields | Inicial10; vacío/omitido10; 0 y999999 guardados. HTTP rechaza −1,0.5,NaN,1e6,1000000,texto, sin escrituras | PARCIAL: H01–04 verifican formulario; máximo sin decisión y servicio admite1000000 |
| PROD04-CA02, ADMIN; RN06 | Catálogo → `/productos/<uuid>/editar/`; ProductEditForm → update_product → modelo | Cambio a0 y luego999999 persistió; vacío e inválidos rechazados; fracción visible con error y foco | CUMPLE en muestra H07–09 para edición. La política transversal del tope continúa PARCIAL en PROD02-CA04; no se repitieron todos los umbrales de alertas03-B/D |
| Consulta ALMACENERO, PROD01 y RN29 | Menú Productos; fila, mínimo y stock vigente | Mínimo999999, cero vigentes, «Stock bajo» y «Sin stock vigente»; sin edición | CUMPLE muestra H05 |
| Consulta VENDEDOR y denegaciones, PROD02-CA05/RN29 | Menú Preparar venta; acceso directo al alta/edición; visitante | Sin posibilidad de agregar producto sin lotes. ALMACENERO/VENDEDOR reciben403 en POST de alta/edición sin cambios; visitante GET edición302 al ingreso | CUMPLE muestra H06/H10/H11; no audita todo ventas |
| Servicio de alta/edición; regla entero RN06 | Objetos Python float/Decimal/bool antes de coerción IntegerField | Antes0.5→0, Decimal1.5→1 y True→1. Después error de minimum_stock sin guardar | INCUMPLE inicial → corregido FIX03H-01, P2. Dos métodos nuevos y probes antes/después |
| Máximo PROP-03C-LIMITES | Guarda MaxValueValidator en ambos formularios; no equivalente comercial en servicio | 1000000 rechazado por HTTP pero aceptado por llamada interna al servicio, antes y después | PARCIAL P2; escoger máximo y luego unificar capas. No es un bypass HTTP demostrado |
| Nombre PROP-03C-NOMBRE | Formularios rechazan homónimos normalizados; sin unicidad de nombre en esquema | PG-C06 de03-C demostró dos altas previamente validadas con nombre igual y códigos distintos | Decisión pendiente, evidencia histórica; no se volvió a ejecutar ni se impuso unicidad |

Campo `minimum_stock`, etiqueta **Existencia mínima**: input numérico, paso1, mínimo0, máximo HTML999999; sin precisión fraccionaria. Alta opcional, inicial10; vacío y omisión guardan10. Edición obligatoria, inicial valor persistido. Ayuda de alta «Entero de 0 a 999 999. Si lo deja vacío, se guardará 10.»; edición omite la frase del valor predeterminado. `IntegerField` valida en servidor. Mensajes observados: «Introduzca un número entero.» en el formulario, obligatoriedad al vaciar edición, límite superior de999999 y límite inferior0. La validación nueva del servicio devuelve «El mínimo debe ser un número entero.». El mínimo es un umbral, no crea existencias. Volver, cancelar, códigos y precios conservan su clasificación previa; no fueron una nueva auditoría completa de navegación en03-H.

## Corrección y pruebas

**FIX03H-01 · P2 · validación de entrada del servicio.** `catalog/models.py:114` comprueba fracciones, booleanos y valores no finitos antes de que `IntegerField` convierta objetos numéricos con `int()`. Respeta `exclude` para los errores ya detectados por ModelForm. Alta y edición ya llamaban a `full_clean`; ambas reciben el error de campo. No se cambió esquema, tope, permisos ni bloqueos. No se afirma que `save()` directo, SQL o `QuerySet.update()` ejecuten esta validación.

La prueba nueva `catalog/test_audit03_limits.py` exige rechazo de0.5, Decimal1.5, True, infinito y NaN. En alta exige cero filas; en edición compara todos los campos de Product y exige conservarlos, aunque se hayan enviado otro nombre, código y precio. Los dos métodos iniciales fallaron con8 fallos y2 errores de subcasos, algunos encadenados tras una inserción; esto no representa diez defectos diferentes. Tras corregir, los dos métodos y22 de regresión pasaron.

| Evidencia | Resultado y límite |
|---|---|
| [Probe previo](../evidencias/03-H-probe-20261110T042659237619Z/result.json) | 11 observaciones: truncamiento al alta y edición reproducido; sin pretensión de aprobación del máximo |
| [Pruebas previas](../evidencias/03-H-tests-20261110T042730963824Z/result.json) | 2 métodos,8 fallos y2 errores; salida completa en tests.txt del mismo directorio |
| [Regresión final](../evidencias/03-H-tests-20261110T042756100441Z/result.json) | **24/24 métodos**, check sin incidencias y makemigrations --check --dry-run sin cambios |
| [Primer navegador](../evidencias/03-H-browser-20261110T042844036974Z/browser.json) | **NO EJECUTADO funcionalmente**,0 casos: discrepancia de cabecera de desafío en el soporte. Abortó antes de enviar credenciales; puerto cerrado. Se corrigió el nombre de cabecera de03-H y se repitió, conservando el intento |
| [Navegador final](../evidencias/03-H-browser-20261110T042912719703Z/browser.json) | **27/27 comprobaciones** Chrome157/Playwright, HTTP real y snapshots ORM; cero errores. ADMIN, ALMACENERO, VENDEDOR y visitante |
| [Probe posterior](../evidencias/03-H-probe-20261110T043008623021Z/result.json) | 11 observaciones:7 rechazos y4 aceptaciones; 0,999999 y1000000 siguen aceptados en alta,1000000 también en edición; fracciones/bool rechazados, negativo rechazado |
| [Cierre verificable](../evidencias/03-H-cierre.json) | Hashes, alcance de cambios, cobertura, enlaces, estado de muestra y continuidad |

H01 inicial; H02 tres altas; H03 omisión; H04 seis rechazos de alta; H05 almacenero; H06 vendedor; H07 dos ediciones; H08 siete rechazos; H09 error visible; H10 dos roles denegados; H11 visitante; H12 conservación final:27 comprobaciones. No sumar estos casos a los métodos Django como si fueran una única suite.

Se inspeccionaron las capturas [alta](../evidencias/03-H-browser-20261110T042912719703Z/01-minimo.png) y [error de edición](../evidencias/03-H-browser-20261110T042912719703Z/09-error-edicion.png). La primera muestra valor10, límites/ayuda y vencimiento obligatorio; la segunda conserva0.5, enfoca el campo e informa error sin redirigir a éxito. No se verificó lector de pantalla ni otro navegador en este sublote.

## Entorno y reproducción

Cada ejecución genera una base SQLite nueva con marcador, configuración sin `.env` de uso, cuentas ficticias y servidor127.0.0.1 efímero. Verifica desafío HMAC antes del ingreso. Base del navegador final: `datos/etapa03h-20261110T042912719703Z/audit.sqlite3`. Retiene tres categorías y cuatro productos activos, UND y vencimiento obligatorio, con mínimos0,10,10,999999. No hay lotes, cargas, ventas, líneas ni borradores. Un turno ficticio OPEN por S/50 permanece igual al inicial. No se cerró caja ni se borraron sesiones.

Todos los runs preservaron por SHA256 base original, bases previas y XLSX. El cierre vuelve a compararlos y registra la base retenida. Los dos servidores de navegador terminaron con puerto cerrado. No hubo migración ni limpieza en la base original. Las migraciones0003/0004 de otros sublotes siguen pendientes para uso real. Comparación comercial de snapshots acotada a los campos enumerados por el soporte; no garantiza identidad de todas las tablas/timestamps.

Desde la raíz del workspace, PowerShell:

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03h_run.py' tests catalog.test_audit03_limits catalog.test_audit03_registration catalog.test_audit03_edit catalog.tests.ProductRegistrationTests catalog.tests.ProductEditTests
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03h_run.py' browser
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit03h_run.py' probe
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/cierre_etapa03h.py'
```

Ejecutar secuencialmente: los hashes incluyen bases de auditorías anteriores. Cada repetición retiene su propia evidencia; el cierre verifica los runs identificados aquí, no sustituye automáticamente evidencia por la última. No se ejecutó PostgreSQL en03-H: la corrección ocurre antes de SQL y no cambia esquema ni bloqueos; las carreras previas no se reatribuyen a este corte. Suite global del proyecto NO EJECUTADA.

## Propuestas, decisiones y cursor

**AUD03H-T01**, tarea técnica implementada/verificada: impedir truncamiento del mínimo en validación de modelo usada por servicios. **AUD03H-TEST01**, implementada/verificada: los dos métodos de rechazo y conservación de campos; vincular a RN06/PROD02-CA04/PROD04-CA02. No son nuevas HU y no cambian estados históricos de sprint/backlog.

**PROP-03C-LIMITES** continúa pendiente. A) aceptar999999 como máximo y reflejarlo en CA04, modelo/servicios, ayudas y pruebas; B) acordar otro máximo y actualizar esas mismas capas. Si se añade restricción de base, examinar datos previos y abortar ante incompatibilidades, sin recortar valores automáticamente. Criterio propuesto: dado un ADMIN, al guardar alta o edición con entero entre0 y el máximo acordado se conserva ese valor; por encima o por debajo se informa el campo y no se guarda ningún cambio; alta omitida guarda10. Probar fronteras en UI, HTTP, servicio y base según la restricción elegida. Decisión comercial no deducible de HAL-005 ni de «continúa».

**PROP-03C-NOMBRE** continúa pendiente. A) nombres únicos tras normalización acordada, con examen de colisiones previas, restricción persistente, error de campo y prueba concurrente PostgreSQL; B) homónimos permitidos con códigos distintos, eliminando el rechazo obligatorio actual del formulario y distinguiendo resultados por código/categoría. La alternativa de aviso informativo permanece disponible en el anexo03-C. No fusionar ni renombrar productos existentes automáticamente. Criterios y tareas dependen de la elección; no se declara ninguna implementada por escribir esta propuesta.

Las dos consultas se formularon en el chat; no consta respuesta al cierre. **Cursor exacto: 03-H / PROP-03C-LIMITES / HU-PROD-02 CA04,08:221 — recibir decisión del máximo; después PROP-03C-NOMBRE.** FIX03H-01 ya está corregido y verificado: no repetirlo como hallazgo pendiente. Barcode to PC Server sigue elegido, con lectura física y aviso inmediato pendientes según el anexo del lector. Confirmación/control de versión de estados, migraciones de uso real y pruebas transversales conservan sus límites.

Balance sin cambios: **20 CUMPLE en la muestra,1 PARCIAL,6 PREVISTO/FUTURO** de27 CA. La diferencia de máximo impide cerrar CA04. Ningún otro módulo se presenta como terminado.
