# 03-S · Resumen revisado frente a cambios concurrentes

10/11/2026, America/Lima. Se leyó completo PROTOCOLO_COMUN y se retomó 03-S desde ESTADO_GENERAL y ETAPA-03-R. Git contenía numerosos cambios previos que se conservaron. El XLSX estaba ausente; no se abrió ni recreó. La auditoría no declara terminadas venta, inventario ni otras etapas. El [inventario completo de 9 HU/27 CA y cuatro suplementarios](ETAPA-03-inventario.md) conserva el alcance y clasificaciones.

## Inventario y trazabilidad

Fuentes contrastadas: 01 y 14 selección R1, 02 diseño y roles, 03 matriz, 07 RN25/27/29/30, 08 VEN01b/CA05 y VEN01c/CA01–05, PROD04, 09 backlog, 16 S1-VEN01C-TXDB/IDEM, 21 alcance y CONTROL_SPRINTS. Etiquetas históricas no acreditan ejecución nueva. El subconjunto es una frontera de catálogo→borrador→cobro, no una revisión integral de venta.

| ID / fuente | Actor, superficie, acción o salida | Clasificación y siguiente paso |
|---|---|---|
| VEN01b/CA05, 08:560; RN27/30 | VENDEDOR dueño, `/ventas/`, P×2/Q×1, cantidad entera, importe y total antes de cobrar | CUMPLE muestra: cambio en otra pestaña sin movimiento hasta confirmar; límites de cantidades fuera de este sublote. |
| VEN01c/CA01–05, 08:571–575; RN25/29/30 | `/ventas/cobrar/`, resumen, efectivo, descuento, confirmar, aviso, constancia; UUID de intento y campos ocultos de subtotal/firma de estado | INCUMPLE al inicio para carrera reproducida; CUMPLE muestra tras FIX03S-01. No aprobar todos los CA de venta. |
| PROD04/CA01/03/04, 08:241–244 | ADMIN cambia precio/nombre/código; foto de venta y revalidación | Frontera: precio obsoleto probado PG; cambio simultáneo nombre/código con resumen web →03-T. |
| RN29, 07:333 | GET/POST de gestión de producto por ALMACENERO/VENDEDOR | 403 sin mutaciones en navegador de muestra. |
| AUD03S-RESUMEN-CONC01 | Comparación de resumen vs mutación posterior antes de bloqueo | Antes INCUMPLE P1; después CUMPLE en tres intercalaciones, no universal. |

Campos y límites: precio con IGV, dos decimales y cantidad entera se cubrieron previamente en C/D; no se repiten sus fronteras. `expected_subtotal` decimal oculto y `draft_signature` texto serializado comparan UUID, producto, nombre, código, cantidad y precio, en orden de línea; idempotency_key UUID, efectivo decimal y CSRF. La serialización no es una firma autenticada. Los mensajes «La venta en preparación cambió. Revisa el resumen antes de confirmar el cobro» y aviso de cambio de precio requieren revisión expresa. La interfaz muestra resumen, importe por línea, total, Confirmar y Cancelar; constancia y otras salidas se trazan en etapas10–12.

## Defecto y corrección

**FIX03S-01 · P1 · venta confirmada con resumen obsoleto.** La vista comprobaba subtotal y firma antes de llamar al servicio. Si el borrador cambiaba después de esa comparación, el servicio tomaba como punto de partida la nueva versión y su comparación interna no detectaba que el vendedor vio otra. [Reproducción anterior](../evidencias/03-S-postgresql-20261111T032415235724Z.json): Django **test Client**, CSRF, dos conexiones PostgreSQL y pausa instrumentada en la llamada al servicio después de la comparación, sin locks auxiliares. Un cambio P2→P3 pasó de resumen S/25,50 a venta S/34,00 (HTTP302). También se cobró P1/Q2 en vez de P2/Q1 conservando S/25,50. Las marcas `ok` de esa evidencia indican que se reprodujo el escenario, no cumplimiento funcional. No se usó socket HTTP ni navegador en esa carrera.

La vista transmite ambos valores al servicio. La serialización es compartida; bajo los locks de turno, borrador, líneas y productos ordenados se vuelve a comparar el subtotal y el estado revisado **antes de refrescar precios o confirmar venta**. La rama principal también bloquea categorías y valida disponibilidad, conservando el orden de 03-Q. Se usan productos bloqueados para nombre/código; cambio de precio exige el aviso y confirmación posterior. La idempotencia ya confirmada se consulta primero. Las llamadas internas al servicio que no entregan ambos valores mantienen el contrato anterior por compatibilidad: no se afirma que tengan revisión de pantalla. No hay migración.

Cuatro métodos nuevos cubren cambio de cantidad, sustitución con igual total, cambio previo al refresco de precio y reintento idempotente. La firma no está autenticada, por lo que no acredita resistencia a valores forjados; esa evaluación se transfiere a etapa15 y no se describe como realizada.

## Pruebas y resultados

PostgreSQL18.4, READ COMMITTED, clúster/base nuevos aislados, cuentas ficticias y sin `.env`. **3/3 casos** posteriores a la corrección usando Django test Client con CSRF y conexiones PG separadas: subtotal distinto, igual subtotal y cambio de borrador con precio de catálogo obsoleto. Primer POST HTTP200 con aviso, cero venta y lotes/correlativo/borrador conservados; revisión y reintento generan una venta e idempotencia. En precio obsoleto se necesitó otra confirmación tras refresco. La pausa marca el intervalo bajo prueba, no añade bloqueos de filas. [Evidencia y aserciones](../evidencias/03-S-postgresql-20261111T032748462197Z.json).

Chrome157 headless, SQLite nueva marcada `datos/etapa03k-20261111T032724611710Z-4f696853/audit.sqlite3`, servidor localhost verificado por HMAC, cuentas ficticias y sin `.env`: **23/23 comprobaciones secuenciales**, sin atribuirles concurrencia. Dos pestañas cambian P2/Q1 a P1/Q2 con igual subtotal; POST antiguo intacto y POST sin firma rechazados, reintento expreso confirma P1/Q2. Roles ALMACENERO/VENDEDOR recibieron403 en edición. [Navegador](../evidencias/03-S-equal-reclassify-20261111T032724611710Z-4f696853/browser.json) · [Instantáneas](../evidencias/03-S-equal-reclassify-20261111T032724611710Z-4f696853/checkpoints.json) · [Cierre](../evidencias/03-S-equal-reclassify-20261111T032724611710Z-4f696853/result.json). Una captura equivalente del recorrido anterior se inspeccionó; lector de pantalla NO EJECUTADO.

Suite final **332/332 métodos** catalog, inventory, sales, cash e identity en SQLite de prueba, incluyendo los cuatro nuevos; check y makemigrations sin cambios. [Resultado](../evidencias/03-K-tests-20261111T032808941201Z/result.json) · [Log](../evidencias/03-K-tests-20261111T032808941201Z/tests.txt).

Regresión PostgreSQL tras modificación del servicio: [Q 5/5](../evidencias/03-Q-postgresql-20261111T032850834372Z.json), [R 3/3](../evidencias/03-R-postgresql-20261111T032953852373Z.json), [L 4/4](../evidencias/03-L-postgresql-20261111T033016948537Z.json), [M 4/4](../evidencias/03-M-postgresql-20261111T033026685087Z.json) y [N 4/4](../evidencias/03-N-postgresql-20261111T033036045663Z.json). En R el hook anterior buscaba un JOIN que el nuevo helper ya no ejecuta y falló `...032904739969Z`; se adaptó al bloqueo real de líneas, manteniendo observación de espera y escenarios, y se repitió. No atribuir el error de soporte al producto. El primer navegador anterior se detuvo 21/22 por filtro equivocado del soporte, corregido antes de repetirse.

Los servidores/clústeres finales se detuvieron y puertos cerraron; hashes de bases protegidas y original intactos. No se restauraron ni limpiaron datos. Bases aisladas y resultados se conservan; no se ejecutó despliegue.

## Reproducción y tareas

Ejecutar secuencialmente desde la raíz; los soportes crean entornos nuevos.

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03s_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03s_equal_run.py' reclassify
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03q_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03r_pg.py'
$env:AUDIT03K_DEFAULT_COOKIES='1'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k_run.py' tests catalog inventory sales cash identity
Remove-Item Env:AUDIT03K_DEFAULT_COOKIES
```

AUD03S-RESUMEN-CONC01 y AUD03S-TEST01 son tareas técnicas implementadas/verificadas en estas muestras, no nuevas HU. Vincular a VEN01b/CA05, VEN01c/CA04–05, RN25/29/30, S1-VEN01C-TXDB/IDEM al actualizar matriz/backlog; conservar estados históricos.

## Pendientes y cursor exacto

**03-T / AUD03T-CATALOGO-RESUMEN01:** en PostgreSQL aislado abrir resumen P×2/Q×1; pausar POST después de revisión en vista y antes de bloquear productos; ADMIN cambia nombre o código de P sin cambiar precio y VENDEDOR reanuda. Comprobar que se exige revisión del producto efectivamente mostrado, sin venta/lotes/caja/correlativo, y que reintento explícito produce snapshot actual e idempotente. Cubrir también carrera de cambio de categoría sin cambio de etiqueta, evaluar comportamiento según criterio vigente y verificar roles en navegador. Estado **NO EJECUTADO**; no asumir error por inspección.

23/27 CA base mantienen CUMPLE en muestras y cuatro CAT03/04 PREVISTO/FUTURO; cuatro suplementarios conservan sus resultados. La protección de firmas contra falsificación y todos los clientes se derivan a seguridad15; observación RN28 de costo histórico a etapa11; recepción/retiros PROP-03-RET-T01..T11 y despliegue real siguen pendientes. No se afirma coincidencia total ni aprobación de otros módulos.
