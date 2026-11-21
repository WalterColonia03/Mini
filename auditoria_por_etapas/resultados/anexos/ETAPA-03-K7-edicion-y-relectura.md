# 03-K7 · Captura de códigos y edición desde dos pantallas

10/11/2026, America/Lima. ADMIN registra y edita. ALMACENERO consulta el catálogo. VENDEDOR consulta en mostrador con turno abierto. Se usaron cuentas ficticias distintas para los dos administradores y bases exclusivas. Las muestras de este corte usaron el teclado de Chrome para reproducir la secuencia Ctrl+A y código. La evidencia física de 03-K6 corresponde a 35 capturas de una misma etiqueta en alta.

| Trazabilidad | Prueba y efecto observado | Estado y prioridad |
|---|---|---|
| HU-PROD-02/CA03, HU-PROD-03/CA01 y PROP-03K-RELECTURA | En alta se alternaron A/B/A/B/B. Solo quedó B y se creó una ficha al pulsar Registrar. En edición se alternaron A/C/A. Guardar conservó el UUID y el código de la constancia anterior. Se rechazó el código de otra ficha y se aceptó una corrección manual. | CUMPLE en Chrome con teclado emulado. Dos etiquetas físicas y edición con teléfono, NO EJECUTADO. |
| HU-PROD-04/CA01–05 y pedido de evitar sobrescrituras | Dos ADMIN abrieron la misma versión. El primero cambió el precio de S/ 8,50 a S/ 9,20. Antes del arreglo, el segundo cambió el mínimo a 17 y al guardar restauró el precio a S/ 8,50. Después, la misma acción dejó S/ 9,20 y mínimo 10 y mostró el conflicto. El segundo abrió «Revisar ficha actual» y pudo guardar 17 manteniendo S/ 9,20. | INCUMPLE inicial, corregido y CUMPLE en las muestras de edición comercial. P1. |
| PROP-03K-RELECTURA, foco equivocado | El formulario abrió con el foco en Nombre. Una lectura emulada en ese momento reemplazó el nombre en pantalla. El código siguió intacto. Cancelar conservó el nombre en la base. | Riesgo reproducido, P1. Cursor del corte K7 dirigido a una captura con foco aislado. |
| HU-PROD-01, HU-PROD-04, RN-06/27/29 | Tras el guardado posterior del mínimo 18, almacén vio precio 9,20, 19 unidades y mínimo 18. El vendedor encontró la ficha vendible a S/ 9,20. La constancia previa, el lote, los datos del turno y el borrador cotejados coincidieron con la instantánea inicial. | CUMPLE en la muestra. |
| Reintento de edición | El doble clic en Chrome produjo un solo POST. Por separado, se enviaron realmente dos POST iguales en SQLite. Ambos obtuvieron redirección y el estado final correspondió a una sola modificación. | CUMPLE en los casos ejecutados. |

**Criterio suplementario de trabajo K7.** Dadas dos pantallas de la misma ficha, si alguien guarda primero un cambio comercial, el servidor rechaza un envío posterior que usaría datos antiguos para modificar la ficha. El formulario conserva lo escrito y ofrece abrir los valores vigentes. Un reenvío que pide exactamente lo que ya está guardado es idempotente. Es una protección implementada en respuesta al objetivo del usuario y verificada en edición. No se agrega al conteo histórico de CA.

El GET entrega una referencia firmada a los datos abiertos. El POST verifica la firma y el producto. El servicio comprueba los valores comerciales vigentes en la transacción antes de escribir. La comparación comprende nombre, código, categoría, precio, mínimo y estado del producto. El coste y las cantidades de los lotes quedan fuera de esa comparación. Los clientes internos que llamen al servicio sin la referencia conservan su contrato previo. No se requirió una migración nueva para K7.

| Ejecución conservada | Resultado |
|---|---|
| [Chrome antes de corregir](../evidencias/03-K-keyboard-20261110T183956099863Z/keyboard.json) | 25/27 comprobaciones. Una detectó la pérdida de precio. La otra fue un error del soporte que buscaba el código en la columna de categoría. Se corrigió la posición y se comprobó también el precio y el mínimo. |
| [Chrome después](../evidencias/03-K-keyboard-20261111T010725864129Z/keyboard.json) · [Instantáneas](../evidencias/03-K-keyboard-20261111T010725864129Z/orm-checkpoints.json) | 32/32 observaciones en Chrome 157. Dos de ellas acreditan que se reprodujo el foco equivocado. No cuentan como aprobación de esa protección. |
| [Concurrencia PostgreSQL](../evidencias/03-K7-postgresql-20261111T010817323136Z.json) | 2/2 en PostgreSQL 18.4 con espera de bloqueo observada. Dos conexiones compitieron sobre la misma ficha, precio frente a mínimo y código frente a nombre. En cada caso solo persistió el envío ganador. |
| [Concurrencia SQLite](../evidencias/03-K-sqlite-race-20261111T010846464247Z/result.json) · [Contraprueba](../evidencias/03-K-sqlite-race-20261110T185008205808Z/result.json) | 3/3 en archivo nuevo. La contraprueba, con la comparación atómica desactivada en el soporte aislado, produjo un HTTP 500 en cada carrera. |
| [Regresión](../evidencias/03-K-tests-20261111T010655936590Z/tests.txt) · [Cierre y resultados intermedios](../evidencias/03-K7-cierre.json) | 318/318 métodos de catalog, inventory, sales, cash e identity. Una ejecución anterior falló por los nombres de cookies del soporte de prueba. Pasaron las comprobaciones Django y la detección de migraciones pendientes de generar. |

**Reproducción.** Desde la raíz, ejecutar secuencialmente en PowerShell. Los soportes crean datos nuevos y comprueban que los archivos protegidos presentes conserven sus hashes. El XLSX no estaba en la ruta prevista al comenzar las ejecuciones finales de K7. No se puede certificar su integridad actual. Los servidores HTTP y el clúster temporal informaron puerto cerrado.

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k_run.py' keyboard
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k_run.py' sqlite-race
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k7_pg.py'
$env:AUDIT03K_DEFAULT_COOKIES='1'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k_run.py' tests catalog inventory sales cash identity
Remove-Item Env:AUDIT03K_DEFAULT_COOKIES
```
