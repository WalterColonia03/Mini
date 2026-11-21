# 03-R · Precio obsoleto y confirmación del resumen

10/11/2026, America/Lima. Se leyó completo PROTOCOLO_COMUN y se retomó 03-R desde ESTADO_GENERAL y ETAPA-03-Q. El árbol tenía cambios preexistentes y se conservaron. El XLSX estaba ausente, no se abrió ni recreó. El [inventario de 9 HU/27 CA y cuatro suplementarios](ETAPA-03-inventario.md) conserva el tramo; no declarar terminadas otras etapas.

## Inventario y fuentes del sublote

Se contrastaron 01 (R1), 02 diseño y autorización, 03 matriz, 07 RN25/27/28/29/30, 08 HU-PROD-04/CA01 y VEN-01b/01c, 09 backlog, 14, 16 tareas técnicas, 21 alcance vigente, CONTROL_SPRINTS y código. Los estados históricos no prueban ejecución. PROD04/CA01 (08:241) exige precio nuevo hacia adelante y pasado conservado; VEN01b/CA05 exige resumen sin movimientos; VEN01c/CA01–05 exige integridad y confirmación, pero su auditoría integral permanece en 11.

| ID / ubicación | Actor, entrada o salida | Estado de esta muestra |
|---|---|---|
| PROD04/CA01 y RN29 | ADMIN, Productos→Editar, precio decimal final con IGV; Guardar; campos nombre/código/categoría/mínimo conservados | CUMPLE muestra; cambio 8,50→9,20 y consulta ALMACENERO. Límites de precio se conservan en C/D. |
| VEN01b/CA05, VEN01c y RN25/27/30 | VENDEDOR con turno propio, borrador P×2/Q×1, `/ventas/cobrar/`, efectivo, descuento, Confirmar; resumen, aviso y constancia | CUMPLE muestra de refresco, rechazo y reconfirmación; no aprueba cobro integral. |
| RN29, PROD04 | GET/POST edición directa ALMACENERO/VENDEDOR | 403 y sin cambios en muestra navegador. |
| AUD03R-PRECIO-CONC01 | `checkout_sale`: precio anterior vs precio vigente, refresco, segundo cobro y reclasificación | 3/3 PG en las intercalaciones ejecutadas; no demuestra ausencia universal de deadlocks. |
| FIX03R-01, validación de resumen | `expected_subtotal` decimal oculto y `draft_signature` texto oculto en POST; idempotency_key UUID y CSRF; mensaje de revisión y reintento | INCUMPLE inicialmente → CUMPLE omisión individual/conjunta en muestra. La firma no está autenticada y comparación/vista no es atómica con servicio. |

El formulario de edición tiene precio obligatorio positivo, dos decimales, con IGV; los valores de frontera y mensajes ya se documentan en C/D. El cobro presenta subtotal/total, cantidad, precio, efectivo, descuento, vuelto, Confirmar y Cancelar. El refresh actualiza precios de líneas y exige reconfirmar, no descuenta lotes. La firma se construye con UUID del borrador, producto, nombre, código, cantidad y precio; es texto de comparación, no firma criptográfica. Las ayudas y la salida de constancia ya inventariadas no se reauditan completamente aquí.

## Hallazgo y corrección

**FIX03R-01 · P1 · solicitud de cobro alterada.** Con CSRF válido y dos pestañas, el vendedor abrió el cobro y en otra pestaña cambió P de 2 a 3 unidades. El POST íntegro de la pestaña antigua respondió 200 con aviso y sin venta. El mismo POST al omitir `expected_subtotal` y `draft_signature` respondió 302 y creó una venta por S/29,50, descontando P3/Q1. Datos ficticios; no representa el clic normal de navegador. [Antes](../evidencias/03-R-altered-reclassify-20261111T025317671199Z-66b3aa8c/browser.json).

`sales/views.py` trata ahora la ausencia de cualquiera de los dos valores como resumen no verificable. Devuelve el resumen vigente, repone ambos valores y pide revisión antes de un nuevo POST explícito. No se afirma que valores enviados por un cliente sean a prueba de manipulación. Dos métodos nuevos, con tres subcasos, comprueban ausencia individual y conjunta, ausencia de venta/movimiento de lote, borrador activo y reintento; la prueba con solicitud directa y CSRF comprueba omisión conjunta tras cambio de otra pestaña. Se ajustaron pruebas históricas para enviar los valores obtenidos del GET normal sin retirar sus aserciones. No hay migración.

[Después: 6/6 comprobaciones navegador](../evidencias/03-R-altered-reclassify-20261111T025555676509Z-837d210a/browser.json) · [Estados](../evidencias/03-R-altered-reclassify-20261111T025555676509Z-837d210a/checkpoints.json) · [Captura revisada](../evidencias/03-R-altered-reclassify-20261111T025555676509Z-837d210a/01-revision-requerida.png). Ante omisión: HTTP200, cero ventas nuevas, P20/Q6, borrador ACTIVE; tras revisión expresa, una venta. No prueba defensa frente a valores forjados ni carrera entre vista y transacción.

## Ejecución y evidencia

Chrome157 headless, SQLite nueva marcada `datos/etapa03k-20261111T025612323774Z-69c9c66e/audit.sqlite3`, cuentas ficticias, local, sin `.env` y prueba HMAC de instancia: **27/27 comprobaciones**. ADMIN cambia P8,50→9,20 con borrador P×2/Q×1 y pantalla de cobro abierta. VENDEDOR recibe aviso, se refresca solo P, sin venta ni descuento; al confirmar de nuevo se registra S/22,40 y vuelto S/7,60, stock18/5, constancia anterior intacta. ALMACENERO observa precio y ambos roles sin gestión reciben403 en edición. [Navegador](../evidencias/03-R-ui-reclassify-20261111T025612323774Z-69c9c66e/browser.json) · [Instantáneas](../evidencias/03-R-ui-reclassify-20261111T025612323774Z-69c9c66e/checkpoints.json) · [Cierre](../evidencias/03-R-ui-reclassify-20261111T025612323774Z-69c9c66e/result.json). Captura del aviso inspeccionada; lector de pantalla NO EJECUTADO.

PostgreSQL18.4 READ COMMITTED, clúster/base nuevos de prueba, conexiones independientes y bloqueo observado: **3/3 escenarios**. Reclasificar Q durante refresco de P; cambiar P dos veces de8,50→9,00→10,00 mientras se refresca; dos cobros simultáneos con la misma clave. En el último ambos intentos iniciales rechazaron (aviso de precio y aviso genérico), sin venta, descuento de lotes ni cambio de correlativo; reintento confirmó una venta y la misma clave fue idempotente. En el doble cambio el aviso final fue8,50→10,00. [Casos y comprobaciones](../evidencias/03-R-postgresql-20261111T025346889645Z.json). Primera ejecución funcional3/3 `...025229415058Z` cerró con fallo de conservación porque una base nueva de navegador todavía cambiaba en paralelo; original intacta. Repetición secuencial con cierre limpio es la citada.

Regresión final **328/328 métodos** catalog, inventory, sales, cash e identity, en SQLite de prueba; check y makemigrations sin cambios. [Resultado](../evidencias/03-K-tests-20261111T025641628831Z/result.json) · [Log](../evidencias/03-K-tests-20261111T025641628831Z/tests.txt). Dos intentos de pruebas de ventas anteriores fallaron al usar fixtures de POST incompletas; se conservaron, se actualizaron a GET real y pasó 48/48 antes de la suite final. El resultado no implica repetir los 5 escenarios PG de 03-Q después de modificar solo la vista.

Los clústeres/servidores finales se detuvieron y sus puertos cerraron. La base original y bases protegidas conservaron SHA256, ver cierres individuales. No se hizo despliegue; los datos de prueba se conservan.

## Reproducción

Ejecutar secuencialmente desde la raíz; las pruebas crean nuevas bases, nunca borrar ni resetear las existentes.

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03r_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03r_ui_run.py' reclassify
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03r_altered_run.py' reclassify
$env:AUDIT03K_DEFAULT_COOKIES='1'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k_run.py' tests catalog inventory sales cash identity
Remove-Item Env:AUDIT03K_DEFAULT_COOKIES
```

AUD03R-PRECIO-CONC01 es tarea técnica verificada en muestras; AUD03R-REVIEW01 es tarea técnica implementada y verificada para omisiones, no nueva HU. Si se incorpora a backlog/matriz, vincularla a VEN01b/CA05, VEN01c/CA04–05 y RN25/29/30 sin alterar estados históricos.

## Pendientes y cursor exacto

**03-S / AUD03S-RESUMEN-CONC01:** probar en PostgreSQL y navegador/HTTP aislados el intervalo entre comparación de `draft_signature`/subtotal en `sales_checkout` y adquisición de locks en `checkout_sale`: abrir resumen de P×2/Q×1, pausar después de comparar, cambiar cantidad o sustituir producto desde otra pestaña del mismo vendedor, reanudar y observar venta, lotes, caja, correlativo y mensaje. Probar caso con mismo subtotal; controlar idempotencia y reintento. Luego evaluar solución que compare el resumen esperado bajo el mismo bloqueo que confirma el cobro. **NO EJECUTADO**, hipótesis de carrera, no defecto declarado. Evaluar separadamente controles no autenticados y decisiones de compatibilidad de clientes.

23/27 CA base siguen CUMPLE en muestras, cuatro CAT03/04 futuros y cuatro suplementarios. No se certifica concurrencia completa. Se mantiene observación RN28/CA06 de costo histórico para etapa11 y PROP-03-RET-T01..T11 para recepción/retiros; despliegue real no ejecutado. Resto de etapas no aprobadas por este corte.
