# Etapa 03-G · Código editable aceptado y lector identificado

09/11/2026, America/Lima. **DOC03-02 resuelto por el usuario:** «Sí, podrá corregirlo si es único y conserva los históricos». Se acepta la corrección administrativa del código después del alta. El usuario también eligió **Barcode to PC Server** para lectura; su prueba física y la detección inmediata de duplicado siguen pendientes.

## Inventario, criterios y cambios

[Manifiesto previo](../evidencias/03-G-inventario-20261110T041634814752Z.json): HU-PROD-04/CA03, clasificación de los dos criterios HU-PROD-03, campos/rutas/acciones, decisión y hashes. Se conserva el protocolo y alcance de etapa03, sin cerrar inventario, ventas, administración técnica ni escáner.

| Elemento / fuente / actor | Antes y alcance aceptado | Evidencia y estado |
|---|---|---|
| PROD04/CA03 · 08:243 · ADMIN | Campo bloqueado en criterio frente a código editable del agregado08:872. Usuario acepta corregir si es único y conserva históricos | Historia/criterio actualizados con registro del texto previo. D15/D16/D18/D19/D29 y10 métodos: **CUMPLE muestra03-G con criterio revisado por decisión** |
| UUID y código normalizado · ProductEditForm→update_product | Misma ficha; código hasta64 con patrón permitido y clave única; no recrear producto ni actualizar snapshots anteriores | Nuevo código consultable, anterior ausente de búsqueda; histórico conserva texto. D15/D16 y prueba de detalle heredado |
| Roles · RN29 | ADMIN edita; ALMACENERO consulta y VENDEDOR consulta en venta autorizada | D22:403 en GET/POST para ambos; D23 visitante302; D24 UUID inexistente404 |
| RN28 / histórico | Preservar constancia pasada, nombre/código/precio/cantidad y vínculo del detalle observado | D09/D14/D16/D29; snapshot inicial permanece en final. No afirma conservación exhaustiva de todas las tablas |
| PROD03/CA01 · 08:231 · ADMIN | Barcode to PC Server elegido; captura por emulación de teclado propuesta | G01 conserva ceros iniciales mediante teclado simulado. **PREVISTO/FUTURO de incorporación; dispositivo real NO EJECUTADO** |
| PROD03/CA02 · 08:232 · ADMIN | Exige advertencia al leer, no solo al guardar | G02 observa ausencia de aviso tras escribir DUPLICADO y salir del campo. Validación final existe. **PREVISTO/FUTURO, pendiente implementar/verificar aviso** |

Cambios de este sublote: documentación08/09/02/03/16/21 y soporte de auditoría. No cambian modelos, formularios, servicios, rutas, permisos o plantillas de la aplicación respecto al cierre03-F. Se mantienen las restricciones, el histórico y las tareas futuras. No se atribuye la funcionalidad existente a una implementación nueva por modificar el criterio.

Tareas AUD03G-DOC01 aplicada y AUD03G-TEST01 ejecutada en la muestra; las tareas propuestas PROP-03G-SCAN-T01/T02/T03 y criterios del lector están en [Barcode to PC: mecanismo, configuración y pruebas pendientes](ETAPA-03-Barcode-to-PC.md). Las fuentes oficiales verificadas están enlazadas allí. El nombre del producto de terceros no implica que se haya instalado, conectado o aprobado.

## Evidencia nueva y resultado

Windows, virtualenv Django del proyecto, Chrome157.0.8103.39/Playwright, escritorio1366×900 y móvil390×844. Cada recorrido crea base marcada propia, cuentas ficticias, cookie propia, prueba HMAC de instancia y servidorlocalhost efímero; no carga `.env`. La venta inicial y los lotes son preparación ficticia; solo la segunda venta se ejecuta por navegador durante el recorrido ampliado de edición.

| Ejecución | Resultado exacto | Evidencia |
|---|---|---|
| Regresión de edición/código | **10/10 métodos**, check y detección de migraciones sin incidencias | [Resultado](../evidencias/03-G-tests-20261110T041750658883Z/result.json) · [Log](../evidencias/03-G-tests-20261110T041750658883Z/tests.txt) |
| Primer navegador | 53 comprobaciones,51 positivas y2 negativas; dos errores del soporte identificados, no ocultados | [Inicial](../evidencias/03-G-browser-20261110T041757169052Z/browser.json) |
| Navegador repetido tras corregir soporte | **53/53 comprobaciones Chrome/HTTP/ORM**, sin errores.51 del recorrido de edición y2 observaciones de teclado G01/G02 | [Final](../evidencias/03-G-browser-20261110T041945048165Z/browser.json) · [Servidor/protección](../evidencias/03-G-browser-20261110T041945048165Z/result.json) |

Los dos errores del soporte inicial fueron: D07 seleccionaba la primera línea de cualquier borrador del producto, pudiendo tomar la del borrador DISCARDED ordenada antes por UUID; D12 esperaba una clave con prefijo03g aunque el dato de prueba retenía03d. Se corrigió D07 para identificar la línea del borrador ACTIVE, también en el runner histórico03-D para su reproducción futura, y D12 para usar la expectativa del dato realmente enviado. D15 heredaba una etiqueta de clasificación anterior al acuerdo y se actualizó. Las evidencias históricas no se reescribieron. No se cuenta el resultado inicial como aprobado.

D15 cambió el código a AUD03D-NUEVO. D16 encontró el código nuevo, dejó de encontrar el anterior y mantuvo la constancia original. Los prefijos03D de estos datos son nombres ficticios reutilizados por el soporte; los archivos/entorno están aislados bajo03-G. D18/D19 rechazaron duplicados y formatos inválidos sin cambios de los campos comerciales comparados. El recorrido también confirmó precio8,50 histórico, precio nuevo9,20, advertencia antes de cobrar y segunda venta18,40; no constituye cierre de la etapa de cobro.

G01 simuló pulsaciones0012345678905 y Tab en alta, con ceros iniciales conservados y sin persistencia. G02 simuló DUPLICADO y Tab: no apareció aviso inmediato. El `ok=true` de G02 significa **observación reproducida de esa carencia**, no cumplimiento de HU-PROD-03/CA02. No se envió una lectura desde móvil ni desde Barcode to PC Server.

Capturas inspeccionadas de la evidencia final: [captura de teclado](../evidencias/03-G-browser-20261110T041945048165Z/G01-captura-teclado.png), [duplicado sin aviso inmediato](../evidencias/03-G-browser-20261110T041945048165Z/G02-duplicado-sin-aviso.png), [edición](../evidencias/03-G-browser-20261110T041945048165Z/01-edicion.png), [aviso de precio](../evidencias/03-G-browser-20261110T041945048165Z/07-aviso-precio.png). El propio aviso se mostraba correctamente incluso en la ejecución inicial; el fallo estaba en la selección de la línea para comprobar su precio.

Base final retenida `datos/etapa03g-20261110T041945048165Z/audit.sqlite3`: tres categorías, tres productos, lote17, dos ventas y tres borradores (uno ACTIVE con una unidad y dos DISCARDED de preparación/cobro), turno OPEN ficticio. Se conservan cuentas/sesiones. [Inicial](../evidencias/03-G-browser-20261110T041945048165Z/orm-initial.json) · [Final](../evidencias/03-G-browser-20261110T041945048165Z/orm-final.json). Los hashes de original, bases anteriores y XLSX se mantuvieron; servidor propio detenido.

No hubo nueva ejecución PostgreSQL: solo cambió documentación y soporte, con servicios/esquema sin cambios respecto a las carreras de código verificadas en03-D. Aquella evidencia sigue fechada y no se suma como nueva. Suite global, lector físico, otras simbologías/dispositivos y carreras de edición con cobro no se ejecutaron. Los datos heredados ambiguos con códigos reutilizados conservan su pendiente12/15.

## Reproducción y continuidad

Desde la raíz, comandos secuenciales que crean nuevas bases:

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03g_run.py' tests catalog.tests.ProductEditTests catalog.test_audit03_edit catalog.tests.ProductExpirationsTests.test_bug004_product_barcode_update_preserves_historical_sale_line_snapshot catalog.tests.ProductExpirationsTests.test_bug028_category_toggle_and_product_edit_category_and_barcode_search
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03g_run.py' browser
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/cierre_etapa03g.py'
```

El verificador revisa las evidencias fechadas enlazadas, no sustituye ejecutar una nueva auditoría tras cambios posteriores. [Cierre](../evidencias/03-G-cierre.json).

Balance actual: **20 CUMPLE en la muestra,1 PARCIAL y6 PREVISTO/FUTURO**. Los dos conflictos base quedaron resueltos mediante decisiones explícitas más comprobación; los resultados históricos mantienen su clasificación original. Cursor **03-H / PROP-03C-LIMITES / HU-PROD-02 CA04 (08:221)**: decidir si aceptar el máximo técnico999999 o exigir otro límite, después PROP-03C-NOMBRE. HU-PROD-03 tiene tecnología elegida y plan de incorporación; ningún criterio del lector físico está aprobado. Otras etapas sin cambios de estado.
