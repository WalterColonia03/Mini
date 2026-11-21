# 03-T · Cambios de catálogo durante la confirmación

10/11/2026, America/Lima. Se leyó completo PROTOCOLO_COMUN y se retomó el cursor de 03-S. Se preservaron los cambios preexistentes del repositorio y las bases; XLSX ausente, sin abrir ni recrear. El [inventario de 9 HU/27 CA y cuatro suplementarios](ETAPA-03-inventario.md) conserva la trazabilidad del tramo. Este corte no aprueba íntegramente ventas, inventario o seguridad.

## Inventario y fuentes

Fuentes consultadas: 01/14 selección R1, 02 diseño y matriz de permisos, 03 matriz, 07 RN25/27/28/29/30, 08 PROD04/CA03–05 y VEN01b/01c, 09 backlog, 16 S1-VEN01C-TXDB/IDEM, 21 alcance vigente y CONTROL_SPRINTS. Las etiquetas históricas no prueban ejecución. PROD04 es funcionalidad adicional al R1 original; VEN01b/01c integran R1. Persisten exclusiones: CAT03/04 previstos, recepción/retiros y despliegue no ejecutados.

| ID/fuente | Actor, ruta, entrada/acción y salida | Estado / prioridad |
|---|---|---|
| PROD04/CA03–04, 08:243–244; RN28/29 | ADMIN Productos→Editar `/productos/<uuid>/editar/`; nombre y código únicos, precio y mínimo conservados; guardar/cancelar | CUMPLE muestras: cambio se guarda con identidad y venta anterior conservadas; revisión de todos los límites corresponde a D/G/I. |
| PROD04/CA05, 08:245 | ADMIN reasigna categoría activa | CUMPLE muestra concurrente: A→B guardado y cobro posterior; categoría no aparece en resumen. |
| VEN01b/CA05 y VEN01c/CA03–05, 08:560,573–575; RN25/27/29/30 | VENDEDOR con turno, resumen P×2/Q×1, efectivo, confirmación, aviso y constancia; subtotal y serialización oculta | CUMPLE en muestras acotadas: nombre/código cambiados requieren revisión; venta sin cambios de resumen muestra comportamiento de categoría activa. No cierra auditoría de cobro. |
| RN29, 07:333 | ALMACENERO catálogo; VENDEDOR mostrador; GET/POST edición directa para ambos | CUMPLE navegador: 403 y sin cambios. |
| FIX03T-01 · P2 | Mensaje de resumen obsoleto atribuía cambio a otra pestaña, aunque pudo hacerlo ADMIN | INCUMPLE inicial → CUMPLE muestra: mensaje describe cambio y pide revisión sin atribuir causa. |

Campos: nombre y código se validan por normas de catálogo previamente inventariadas; precio final con IGV, mínimo y categoría de destino se mantienen en la ficha. En cobro: resumen con nombre/cantidad/precio/subtotal, descuento opcional, efectivo decimal, botón Confirmar y Cancelar, subtotal y estado serializado ocultos, UUID de idempotencia. El estado serializado incluye UUID de borrador y, para cada línea, identidad, nombre, código, cantidad y precio; no incluye categoría. No es firma criptográfica. Los límites, vacíos y formatos ya se revisaron en cortes anteriores y no se reejecutan íntegramente aquí.

## PostgreSQL: intercalaciones controladas

PostgreSQL18.4 READ COMMITTED, clúster y base aislados con cuentas ficticias, sin `.env`, dos conexiones independientes. Django test Client con CSRF ejecutó la vista real; se pausó la llamada al servicio tras comparar el resumen, sin introducir bloqueos auxiliares. No es navegador ni petición por socket. Se creó una venta histórica como fixture y un borrador posterior P×2/Q×1.

| Caso | Resultado observado |
|---|---|
| Nombre cambiado por ADMIN | Primer POST responde200 con solicitud de revisión, sin venta ni cambios a lotes, turno, correlativo o borrador. Reintento confirma una venta con nombre actual; snapshot previo intacto. |
| Código cambiado por ADMIN | Mismo rechazo y conservación; reintento confirma una venta con código actual e identidad conservada. |
| Categoría activa A→B sin cambiar nombre/código/precio | POST confirma una venta con el mismo resumen visible; lotes, dos líneas y venta histórica se conservan según el caso. La categoría no forma parte del resumen y se revalida su estado bajo bloqueo. No existe criterio que exija reconfirmar únicamente por reclasificación activa. |

**3/3 escenarios y todas sus aserciones**, incluido replay de idempotencia **a nivel de servicio**, no replay HTTP. [Evidencia PG](../evidencias/03-T-postgresql-20261111T033450703864Z.json). No se induce simultaneidad sobre todas las combinaciones, ni es auditoría integral de venta; no se hizo cambio funcional por estos resultados.

## Navegador y corrección del mensaje

Chrome157 headless con Playwright, servidor local aislado y desafío HMAC, cuentas ficticias, sin `.env`; base nueva `datos/etapa03k-20261111T033958715784Z-c91e0f04/audit.sqlite3`. La prueba es **secuencial**, no demuestra bloqueo concurrente. ADMIN cambia nombre y código con pantalla de cobro abierta; ALMACENERO observa ficha y stock, ambos roles no administradores reciben 403 en GET/POST directos de edición sin mutar. VENDEDOR recibe aviso y resumen actualizado, confirma expresamente, se registra una venta con snapshot actual y descuento único, y la constancia anterior conserva su contenido.

Al inspeccionar [captura anterior](../evidencias/03-T-browser-reclassify-20261111T033849664862Z-0c3c972b/01-resumen-actualizado.png), el mensaje decía que el cambio ocurrió «en otra pestaña», aunque lo había hecho ADMIN. `sales/views.py` ahora dice «El resumen de la venta en preparación cambió» y muestra subtotal actual y petición de revisión; conserva `role=alert`. Se actualizan las aserciones relacionadas en las pruebas y soporte de navegador. No se cambia la lógica de cobro ni se añade migración. Guía ui-ux-pro-max: error identificable y recuperable; lector de pantalla real no ejecutado.

**28/28 comprobaciones** después del cambio; [navegador](../evidencias/03-T-browser-reclassify-20261111T033958715784Z-c91e0f04/browser.json) · [instantáneas](../evidencias/03-T-browser-reclassify-20261111T033958715784Z-c91e0f04/checkpoints.json) · [captura nueva inspeccionada](../evidencias/03-T-browser-reclassify-20261111T033958715784Z-c91e0f04/01-resumen-actualizado.png) · [cierre](../evidencias/03-T-browser-reclassify-20261111T033958715784Z-c91e0f04/result.json). El mensaje muestra subtotal con punto decimal y el resumen utiliza coma; mejora de formato separada, pendiente de decisión y prueba, sin confundir valores.

Regresión después de corregir el texto: **332/332 métodos** catalog/inventory/sales/cash/identity, SQLite de prueba; check y makemigrations --check --dry-run sin incidencias. [Resultado](../evidencias/03-K-tests-20261111T034025997777Z/result.json) · [log](../evidencias/03-K-tests-20261111T034025997777Z/tests.txt). Las pruebas anteriores de PostgreSQL se hicieron antes del cambio exclusivamente textual y no se repitieron; no sumar ejecuciones como cobertura nueva. El servidor de navegador y clúster PG terminaron con puerto cerrado; bases protegidas y original conservaron hash.

## Reproducción y continuidad

Desde la raíz, secuencialmente; crea entornos nuevos y no restaura ni elimina bases existentes:

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03t_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03t_browser_run.py' reclassify
$env:AUDIT03K_DEFAULT_COOKIES='1'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k_run.py' tests catalog inventory sales cash identity
Remove-Item Env:AUDIT03K_DEFAULT_COOKIES
```

AUD03T-CATALOGO-RESUMEN01 es tarea técnica verificada en muestra; vincular a PROD04/CA03–05 y VEN01b/01c en matriz/backlog sin modificar estados históricos. FIX03T-01 implementado y verificado en navegador y regresión. `audit03t_cases.py` y `audit03t_browser.cjs` documentan los pasos.

**Cursor 03-U / AUD03U-CATEGORIA-VENTA01:** probar en PostgreSQL aislado, con resumen P×2/Q×1 abierto y dos categorías activas, la carrera de reclasificar P A→B seguida de suspensión de B frente al cobro web: ambos órdenes, registrar esperas, rechazo seguro, stock, caja, correlativo, histórico y reintento después de reactivar. Reproducir después estados secuenciales por ADMIN/VENDEDOR y consulta ALMACENERO. **NO EJECUTADO**: 03-N cubrió un producto por servicio, no este recorrido web multiproducto. Decidir si la política requiere aviso de reclasificación aunque la categoría no se muestre antes de alterar comportamiento.

Persisten serialización no autenticada y clientes internos sin resumen→15; costo histórico de venta→11; recepción/retiros PROP-03-RET-T01..T11→05–08/11/12/14–16; despliegue real pendiente. **23/27 CA base CUMPLE en muestras y 4 futuros**, más cuatro suplementarios con evidencia previa. No afirmar coincidencia total.
