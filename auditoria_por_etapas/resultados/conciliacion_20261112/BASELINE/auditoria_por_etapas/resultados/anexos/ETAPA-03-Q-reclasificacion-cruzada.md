# 03-Q · Reclasificaciones cruzadas y venta multiproducto

10/11/2026, America/Lima. Se leyó completo PROTOCOLO_COMUN y se retomó el cursor de 03-P. Este corte evalúa la frontera de catálogo con cobro, no aprueba integralmente ventas, inventario ni seguridad. El árbol ya estaba ampliamente modificado; se conservaron cambios previos. XLSX ausente, sin abrir ni reconstruir.

## Inventario y trazabilidad del sublote

El [inventario de 9 HU/27 CA y cuatro suplementarios](ETAPA-03-inventario.md) conserva clasificación, campos, rutas y salidas completas. Se contrastaron 01, 02, 03, 07, 08, 09, 14, 16, 21 y CONTROL_SPRINTS; R1 seleccionó venta pero edición de producto se implementó después. Los estados históricos no sustituyen pruebas. No se encontraron instrucciones AGENTS aplicables.

| ID y fuente | Actor, campos, acción, resultado | Estado y prioridad |
|---|---|---|
| HU-PROD-04 CA05, 08:245 | ADMIN, Productos → Editar `/productos/<uuid>/editar/`, categoría activa, nombre, código, precio, mínimo y firma de edición; Guardar/Cancelar. P:A→B, Q:B→A | Seleccionado y CUMPLE en muestra Chrome y PG. P1: defecto de concurrencia corregido abajo. |
| RN29, 07:333; PROD04 | ALMACENERO consulta catálogo; VENDEDOR consulta venta; GET/POST edición denegados | CUMPLE muestra Chrome con 403 y sin cambios. |
| VEN01c CA03, 08:573; RN28/29/30; S1-VEN01C-TXDB | VENDEDOR, borrador P×2/Q×1, cobro y constancia; categoría, precio, stock, efectivo, vuelta, instantáneas | Frontera ejecutada; no auditoría integral de caja/venta. Históricos comerciales examinados según campos del soporte. |
| AUD03Q-CONC01 | Dos ediciones cruzadas más cobro, conexiones independientes, transacciones y espera real | Antes INCUMPLE P1 por interbloqueo; después CUMPLE en las intercalaciones probadas. No universal. |
| VEN01c CA06, 08:576; RN28, 07:324 | Costo promedio histórico de cada línea | **PARCIAL / observación estática P1**: `SaleLine` y creación de línea inspeccionadas sin campo de costo histórico; ejecución funcional específica NO EJECUTADA. Traspaso a etapa11, no corregido aquí. |

El campo categoría parte de la categoría actual y ofrece activas; el rechazo de destino inactivo se probó en N. El contrato de los demás campos, normalización, errores y límites se conserva en D/I/P; no se reejecuta aquí cada frontera. El ciclo de venta solo usa entradas ficticias. El catálogo muestra producto, categoría, existencias y estado; el navegador comprueba permisos y conservación, no una carrera real.

## Hallazgo y corrección

**FIX03Q-01, P1, cobro ante reclasificación concurrente.** `checkout_sale` bloqueaba líneas con `SELECT FOR UPDATE` unido a producto y categoría antes de la consulta ordenada de productos. Una edición bloquea producto y luego categoría destino. PostgreSQL18.4 reprodujo el ciclo con servicios reales, sin bloqueos auxiliares: Q queda bloqueado por la edición, pausada justo antes de pedir categoría A; cobro bloquea otras filas y espera Q; al reanudar, PostgreSQL detectó deadlock SQLSTATE `40P01` y abortó cobro. No hubo venta parcial en esa muestra; reintento completó una sola venta. La frecuencia natural no se midió. [Antes](../evidencias/03-Q-postgresql-20261111T021841212145Z.json). Un ensayo previo con bloqueos auxiliares también reprodujo el ciclo; no se confunde con esta reproducción sin ellos.

Se modificó `sales/services.py`: bloquear solo filas de línea, después productos en orden UUID y categorías en orden UUID, y revalidar el estado de esas filas bloqueadas. Para conservar snapshots actuales se usa en cada línea la instancia de producto ya bloqueada, no la instancia obtenida antes de esperar. Se mantienen restricciones y atomicidad; no hubo migración. Un primer intento del soporte/fix produjo KeyError cuando la categoría cambió durante el JOIN; se eliminó ese JOIN bloqueante y se repitió. Evidencias intermedias se conservan en los archivos 03-Q-postgresql con fecha anterior al resultado final. La corrección cubre el ciclo reproducido; no prueba ausencia de todos los interbloqueos del sistema.

## Ejecución y resultados

PostgreSQL18.4, READ COMMITTED, clúster y base nuevos exclusivos, sin `.env`, conexiones independientes, espera comprobada mediante `pg_blocking_pids`, tiempo límite y servicios reales. **5/5 escenarios**: edición primero, cobro primero, ciclo reproducido sin bloqueo auxiliar, cambio simultáneo de nombre/código y las dos ediciones cruzadas con cobro en tres conexiones. En el último se pausaron ambas ediciones antes de consultar categoría y se observó al cobro esperar producto; ambas ediciones y una venta de S/23 confirmaron, stock y dos líneas correctas, reintento de la misma clave devolvió la misma venta. En el cambio de código/nombre la venta conservó los valores de la ficha bloqueada. Las pausas instrumentan orden, no agregan locks. [Resultado y cada comprobación](../evidencias/03-Q-postgresql-20261111T022120470211Z.json).

Regresión PostgreSQL en código definitivo: suspensión de categoría vs cobro/entrada 4/4, suspensión de producto vs cobro/entrada 4/4 y reclasificación vs cobro/suspensión 4/4. [L](../evidencias/03-L-postgresql-20261111T022145356888Z.json) · [M](../evidencias/03-M-postgresql-20261111T022145356888Z.json) · [N](../evidencias/03-N-postgresql-20261111T022145361122Z.json). No equivalen a una prueba completa de entradas ni de concurrencia general.

Chrome157 en base SQLite nueva marcada `datos/etapa03k-20261111T022054827383Z/audit.sqlite3`, servidor local con desafío HMAC, cuentas ficticias y sin `.env`: **27/27 comprobaciones secuenciales**. ADMIN cambia P:A→B y Q:B→A con borrador ya abierto; ALMACENERO observa categorías y 20/6 unidades; los dos roles no administradores reciben 403 en GET/POST directo de edición; VENDEDOR cobra dos líneas y quedan18/5, preservando constancia anterior. No acredita concurrencia del navegador. [Observaciones](../evidencias/03-K-reclassify-20261111T022054827383Z/browser.json) · [Instantáneas](../evidencias/03-K-reclassify-20261111T022054827383Z/checkpoints.json) · [Cierre](../evidencias/03-K-reclassify-20261111T022054827383Z/result.json).

Intento Chrome anterior `...021726658069Z`:20/21 por expectativa del soporte ante texto adicional «Stock bajo»; se corrigió selector y repitió. Otra ejecución paralela del runner chocó al crear una carpeta con timestamp idéntico y terminó antes de navegador; se repitió secuencialmente. No son fallos del producto.

Suite definitiva en SQLite aislada: **326/326 métodos** de catalog, inventory, sales, cash e identity; check y makemigrations --check --dry-run incluidos. [Resultado](../evidencias/03-K-tests-20261111T022113097844Z/result.json) · [Log](../evidencias/03-K-tests-20261111T022113097844Z/tests.txt). No suma pruebas repetidas como cobertura independiente. Original y bases protegidas conservaron SHA256; servidores/clústeres de las ejecuciones finales se detuvieron y puertos se cerraron. Se conservan bases y resultados de intentos.

## Reproducción

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03q_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03l_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03m_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03n_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03q_browser_run.py' reclassify
$env:AUDIT03K_DEFAULT_COOKIES='1'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k_run.py' tests catalog inventory sales cash identity
Remove-Item Env:AUDIT03K_DEFAULT_COOKIES
```

Ejecutar en serie; cada runner crea un entorno nuevo. `audit03q_pg.py` y `audit03q_cases.py` conservan la regresión reproducible; las pausas se describen en cada caso. AUD03Q-CONC01 es tarea técnica verificada en muestra, no HU nueva. No se alteran estados históricos de Sprint.

## Pendientes y cursor

**03-R / AUD03R-PRECIO-CONC01:** inspeccionar rama de refresco de precio en `sales/services.py` alrededor de línea268, que aún usa `select_for_update` con JOIN, y sincronizar en PostgreSQL aislado precio obsoleto en borrador multiproducto frente a edición/reclasificación y otro cobro. Comprobar espera, posibles ciclos, mensajes, ningún cambio parcial, snapshots y reintento. Aún **NO EJECUTADO**: no afirmar defecto solo por inspección. Continuar después con navegador y roles si corresponde.

La muestra mantiene 23/27 criterios base CUMPLE y cuatro futuros, con los cuatro suplementarios anteriores. Despliegue real NO EJECUTADO; recepción/retiros por lote siguen en sus etapas según [anexo](ETAPA-03-recepcion-y-retiros-pendientes.md). La ausencia de costo histórico se transfiere como observación para VEN01c/CA06 y RN28 a etapa11; verificar ejecución y decidir corrección allí. Quedan por probar otras intercalaciones, dispositivos y lector de pantalla.
