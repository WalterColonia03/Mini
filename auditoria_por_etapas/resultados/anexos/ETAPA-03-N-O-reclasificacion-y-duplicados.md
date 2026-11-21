# 03-N / 03-O · Reclasificación y aviso de código duplicado

10/11/2026, America/Lima. Se retomó03-N leyendo completo el protocolo y el estado general. La instrucción «continua y aplica las correcciones/mejora de lo pendiente» selecciona en este corte el aviso pendiente de HU-PROD-03/CA02, sin ampliar el alcance a inventario integral o retiros. Se aplicó ui-ux-pro-max: validación próxima al campo, descripción accesible y foco estable. No se cambió el diseño general.

## Inventario y clasificación previa del sublote

| Requisito / fuente | Elementos reales y actores | Estado y prioridad |
|---|---|---|
| HU-PROD-04/CA05,08:245; RN-28/29; QA08:872/876 | ADMIN, Productos→Editar, GET/POST `/productos/<uuid>/editar/`. Categoría actual y destino, nombre, código, precio, mínimo y firma `edit_snapshot`; Guardar cambios/Cancelar. Error de categoría o ficha obsoleta, mensaje actualizado | Seleccionado e implementado. N profundiza reclasificación y efecto en cobro/históricos. CUMPLE muestra. Alta. |
| HU-VEN-01c/CA03,08:573; tareas16 S1-VEN01C-TXDB/MAN | VENDEDOR, Preparar venta→Cobrar; efectivo20,00, descuento0, borrador de2 unidades a8,50, constancia y FEFO | Frontera, no auditoría completa de venta. Rechazo conservador durante cambio simultáneo: reintento explícito verificado. Alta. |
| HU-PROD-03/CA01–02,08:225–232; PROP-03G-SCAN-T02; 21:74/09:237 históricos | ADMIN, alta/edición, Escanear código, campo temporal, Usar código, Cancelar/Escape. Teclado/Barcode to PC, sin POST de guardado automático | Anteriormente futuro con captura física ya probada enK9. Aviso CA02 seleccionado por instrucción actual, implementado y verificado por teclado Chrome. Nueva lectura física de este aviso: NO EJECUTADA. Alta. |
| HU-PROD-02/CA03 y PROD-04/CA03; RN-28/29 | Nueva consulta GET `/productos/codigos/comprobar/`, `barcode` obligatorio y `product_id` opcional solo para edición. Respuesta mínima `duplicate` o `error`, sin escrituras | Dependencia técnica de CA02, no nueva HU. Solo ADMIN. Probada ante anónimo/almacenero/vendedor y método incorrecto. Alta. |
| RN-03/06/27/28/29; 01/02/03/07/09/14/16 y matriz previa03 | Catálogo consultado por ALMACENERO, mostrador/constancias por VENDEDOR, precio conIGV, stock, identidad e históricos | Se conserva el inventario anterior. O no cambia formato ni unicidad del modelo, precios, mínimos, vencimientos o permisos. Tareas históricas no se reinterpretan como ejecución. |

Inventario inverso del aviso: consulta pendiente→«Comprobando código…»; existente→«El código de barras ya está registrado» y Usar código deshabilitado; no encontrado→«Sin duplicados en esta consulta. Se volverá a comprobar al guardar.»; fallo de red/sesión→«No se pudo comprobar el código. Se validará al guardar.». Todos derivan de CA02 o de informar honestamente su dependencia de red. Campo manual recibe el mismo aviso junto al input. `role=status`, `aria-live=polite`, `aria-describedby`; no mueve el foco al llegar respuesta. El estilo deshabilitado distingue la acción bloqueada. No se comprobó un lector de pantalla real.

Contrato de entrada: mismo campo y patrón del formulario,1–64 caracteres tras recorte, letrasASCII/números/espacios/guiones; vacío/formato/65 caracteres→400. Unicidad mediante `Product.normalize_barcode`, ignora espacios/mayúsculas e incluye fichas y categorías inactivas. UUID propio válido excluye solo esa ficha; inválido400/inexistente404. Anónimo302; trabajadores403; POST405. Todas las respuestas de la vista sin caché. No devuelve nombre, precio, existencias ni identificador de otra ficha. La API no sustituye las restricciones de servidor/BD al guardar.

## N: reclasificación en PostgreSQL y Chrome

[PostgreSQL final](../evidencias/03-N-postgresql-20261111T015409407083Z.json):4/4 casos con conexiones independientes y bloqueo `transactionid` observado por `pg_blocking_pids`; clúster18.4 nuevo/read committed. Producto con20 unidades vigentes después de una venta histórica; categoríaA yB activas, turnoOPEN50,00, borrador2 unidades.

| Orden | Resultado observado |
|---|---|
| Reclasificar→cobrar | A→B confirma. Cobro simultáneo rechaza «La venta en preparación cambió. Revisa el resumen antes de confirmar el cobro.». Conserva lotes, borrador, caja, ventas y correlativo. Reintento explícito confirma17,00 y stock18; repetir la misma clave devuelve la misma venta. |
| Cobrar→reclasificar | Cobro confirma17,00, efectivo20,00/vuelto3,00, stock18. Reclasificación espera y confirma aB. Conserva identidad e histórico. |
| Reclasificar→suspenderB | Reclasificación confirma; B se desactiva después. Producto enB no vendible. Conserva20 unidades, costo, borrador e histórico. |
| SuspenderB→reclasificar | B se desactiva; reclasificación rechaza «Seleccione una categoría activa.». Ficha permanece enA vendible, sin efectos comerciales. |

El rechazo del primer orden es seguro y admite reintento; no hay requisito que prometa cobro ininterrumpido durante cambios de catálogo. Se conserva como comportamiento observado. La primera versión del soporte suponía que ambos servicios confirmarían y buscaba una venta inexistente: evidencia `03-N-postgresql-20261111T015224784736Z.json`, error del soporte. La segunda registró3/4 bajo esa expectativa (`...015247441587Z.json`). Se agregó evidencia de integridad y reintento idempotente antes de aceptar el resultado; no se cambió código funcional de venta/catálogo para fabricar éxito.

[Chrome final](../evidencias/03-K-reclassify-20261111T015739066270Z/browser.json):27/27. ADMIN reclasificaA→B con pantalla de cobro abierta. ALMACENERO veB/20 unidades/Disponible; constancia anterior íntegra; cobro posterior confirma y quedan18. Se abre otra edición B→A y otro ADMIN desactivaA antes de enviar. El formulario rechaza «Escoja una opción válida. Esa opción no está entre las disponibles.»; retiene precio9,50 y mínimo11 escritos pero no guarda nada. GET/POST directos de edición por vendedor/almacenero devuelven403, con CSRF válido del contexto aislado. [Instantáneas](../evidencias/03-K-reclassify-20261111T015739066270Z/checkpoints.json) · [Reclasificado](../evidencias/03-K-reclassify-20261111T015739066270Z/01-reclasificado.png) · [Destino rechazado](../evidencias/03-K-reclassify-20261111T015739066270Z/03-destino-inactivo.png). Captura de rechazo inspeccionada.

Intentos ChromeN retenidos: `...015423105806Z` terminó tras3checks por buscar cookieCSRF estándar en vez de la propia del runner; `...015623098100Z`26/27 por texto esperado «Seleccione» frente a «Escoja». Correcciones del soporte y repetición, no defectos atribuidos a la aplicación.

## O: mejora implementada y comprobaciones

Cambios: vista y ruta de consulta,8 métodos de prueba, partial de captura, contexto de edición conid propio, JavaScript y CSS local. Debounce250ms; al escribir otra lectura se cancela la consulta anterior y se invalida su resultado; tiempo máximo5s. Consultar no escribe ni crea productos. Se conserva el diálogo protector, el reemplazo Ctrl+A,64 caracteres y guardado expreso. Un duplicado confirmado impide copiar desde el diálogo; la entrada manual y el envío directo siguen sujetos al rechazo definitivo del servidor. Si la red falla se permite copiar para seguir trabajando, mostrando que solo se validará al guardar. No se promete unicidad por una respuesta anticipada.

FIX03O-01: al probar el nuevo aviso, el cambio de foco al pulsar Usar código disparaba `change` para el mismo valor y deshabilitaba la acción durante el clic. Se evita repetir la consulta si el valor no cambió. Primera corrida deO conservada (`03-K-barcode-check-20261111T015549608567Z`):11checks y timeout en siguiente Registrar porque el diálogo seguía abierto. La repetición `...015703446000Z` pasó32checks. La revisión visual detectó que el botón deshabilitado tenía el mismo aspecto que uno activo; se añadió estilo específico y una comprobación más, sin afectar otros botones.

**Resultado final O:33/33 Chrome**, incluye duplicado normalizado,10 relecturas sin concatenar ni sobrescribir campos, Enter sin envío,64/65, respuesta tardía descartada, fallo de red con rechazo final del duplicado, entrada manual, código propio al editar, código ajeno rechazado, edición conservando identidad/históricos, rechazo y alta manual sinJavaScript. [Corrida final](../evidencias/03-K-barcode-check-20261111T015848208296Z/barcode.json) · [Captura del aviso](../evidencias/03-K-barcode-check-20261111T015848208296Z/01-duplicado.png) · [Control de conservación](../evidencias/03-K-barcode-check-20261111T015848208296Z/result.json). No se usó teléfono paraO; la evidencia física K9 conserva su alcance anterior.

**Regresión:326/326 métodos** de catalog/inventory/sales/cash/identity, incluidos8 nuevos. Comprobaciones Django y ausencia de migraciones por generar correctas. [Resultado](../evidencias/03-K-tests-20261111T015806678855Z/result.json) · [Log](../evidencias/03-K-tests-20261111T015806678855Z/tests.txt). Datos de prueba exclusivos, sin.env. Los servicios comerciales mantienen los hashes deM. No hubo migración nueva ni despliegue sobre la base original.

Incidencia de soporte adicional: primer lanzamiento del modo barcode-check falló con KeyError por clave de diccionario accidentalmente convertida en tupla (`03-K-barcode-check-20261111T015529367360Z`). El `finally` detuvo el servidor. Se corrigió el mapeo antes de ejecutar el navegador; no cuenta como prueba funcional. No se elimina su base ni evidencia parcial.

## Trazabilidad actualizada y reproducción

AUD03N-TEST01:4casosPG y27checksChrome implementados/verificados. PROP-03G-SCAN-T02/AUD03O-UI01: aviso de duplicado seleccionado/implementado/verificado en software. AUD03O-TEST01:8métodosAPI,33checksChrome yregresión326. No se alteran horas ni estados históricos de sprints.

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03n_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k_run.py' reclassify
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k_run.py' barcode-check
$env:AUDIT03K_DEFAULT_COOKIES='1'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k_run.py' tests catalog inventory sales cash identity
Remove-Item Env:AUDIT03K_DEFAULT_COOKIES
```

Ejecutar secuencialmente. Chrome157.0.8103.39, SQLite nueva con marca, credenciales ficticias, cookies propias y desafíoHMAC; los tests de regresión usan nombres estándar solo dentro del runner. Puertos de ejecuciones finales cerrados, bases preexistentes conservadas por hash; XLSX ausente desde antes, sin certificar su contenido. No certifica desempeño ni conformidad legal.

## Pendientes y cursor

Balance vigente del alcance seleccionado:23 de27 criterios base CUMPLE en sus muestras,4 PREVISTO/FUTURO deCAT03/04. La captura física deCA01 aportaK9; el avisoCA02 tiene evidencia software nueva, comprobación física de este aviso pendiente. Se mantienen los4criterios suplementarios de categoría. No supone finalización de etapa03 completa.

**Cursor03-P / PROP-03G-SCAN-T02 / validación física del aviso.** Base nueva, ADMIN enRegistrar producto, dos códigosA/B: Aexistente (incluido inactivo), Bnuevo. Abrir Escanear código y leer A varias veces: exigir código exacto, aviso y Usar código bloqueado, ceroPOST; leer B: habilitar copiar, conservar otros campos, guardar una sola ficha; volver a leerB y verificar rechazo sin duplicarlo. En edición deA, leerA propio debe permitirse yB ajeno bloquearse. Si no hay teléfono, registrar NO EJECUTADO y continuar independiente con la revisión de despliegue/migraciones pendientes solo en copia nueva. No aplicar migraciones a la base operativa sin comprobar su estado y estrategia.

Persisten fuera de este sublote: concurrencia de reclasificaciones cruzadas y ventas con múltiples productos/categorías, carga y recepción integral de paquetes, cuarentena/retiro por lote y asignación venta→lote, recuperación de fallos, accesibilidad con lector de pantalla y despliegue real. El [anexo de recepción/retiros](ETAPA-03-recepcion-y-retiros-pendientes.md) mantiene sus11casos y decisiones pendientes. Las etapas06/11/14/15/16 siguen sin auditoría integral aprobada.
