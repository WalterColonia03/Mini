# Navegador de 14-E

Primera pasada, continuación del cursor14-E-KARDEX-01. Este lote examina costo móvil físico y preservación del costo de salidas conforme a DOC-03AH-01/C-01..02, RN-14 y RN-28. Se conectan la recepción de HU-INV-01b, cobro de HU-VEN-01c, baja de HU-INV-02 y consultas de ADMIN. El flujo conserva como dependencia la información histórica de origen, asignación por lote y Kardex de 14-F.

## Inventario de la muestra

| Superficie y actor | Entradas, acción y salida | Criterios y alcance |
|---|---|---|
| ADMIN, inventario y Ver carga | Stock físico/vigente, costo promedio con dos decimales, lotes iniciales y posteriores, costos de adquisición por lote, responsable, proveedor y fecha | DOC-03AH-01/C-01..02, RN-14, DEC-07-VENCIDOS-FILTRO. Testigo DB a cuatro decimales |
| ALMACENERO, Entrada de mercadería | Producto con carga previa, proveedor opcional, lote64, cantidad entera1..999999, costo positivo hasta4decimales, vencimiento posterior a hoy. Confirmar entrada, mensaje de costo actualizado y detalle | HU-INV-01b y DOC-03AH-01/C-01. Ruta /inventario/entrada/ |
| VENDEDOR, Apertura de caja | Monto inicial100. Caja única CAJA-01, turno abierto | HU-CAJA-01 dependencia del recorrido |
| VENDEDOR, Preparar venta | Búsqueda INT-F-COSTO-14E, resultado20 vigentes después de entrada; agregar1 | HU-VEN-01b, RN-03 y RN-30 |
| VENDEDOR, Cobrar | Total8,00, efectivo10,00, vuelto2,00, constancia V-00000001, costo histórico de línea guardado | HU-VEN-01c, DOC-03AH-01/C-02, RN-28. Costo de compra fuera de constancia conforme RN-26 |
| ALMACENERO, Merma | Lote seleccionado, cantidad, motivoDAÑO/VENCIMIENTO, detalle por daño. Confirmar baja. Correlativo y stock restante | HU-INV-02, RN-04/05/20, DOC-03AH-01/C-02 |
| ADMIN, movimientos, ventas, constancia | Entradas y salidas, referencia de venta, total8,00, proveedor, autor, costo actual en Ver carga, constancia histórica después de agotamiento | HU-INV-04, HU-VEN-05b, HU-VEN-02a, RN-28 |
| VENDEDOR, Cerrar turno | Contado108,00, esperado108,00, diferencia0 | HU-CAJA-02 dependencia del recorrido |

Las capturas JSON guardan texto visible, campos con etiqueta, tipo, valor, límites y opciones, ruta, rol, instante y testigo de todas las tablas de negocio. Los valores secretos y campos ocultos de sesión/CSRF se omiten. El formulario de recepción se registra antes de llenarlo en02, permitiendo inspeccionar sus valores iniciales. Las nuevas validaciones de costo y snapshots se contrastaron en la corrida final. Fronteras completas de cada campo, variantes de permisos, ajustes y concurrencia tienen cobertura propia fuera de esta muestra.

## Fixture y aislamiento

F-COSTO14E se crea por ORM en SQLite nueva antes de las operaciones de UI. Tres cuentas y roles ficticios, una caja, categoría, productoUND con vencimiento obligatorio y precio8,00, proveedor ficticio, carga inicial y dos lotes. Las18 unidades físicas tienen promedio3,0000. LoteA tiene8, costo3,0000 y fecha de ayer en Lima. LoteB tiene10, costo3,0000 y fecha hoy+7. La fixture representa un saldo histórico con unidades ya vencidas. La carga inicial con fecha vencida no se envía a través del formulario. Ese origen controlado queda declarado en fixture.json.

El almacenero recibe por UI10 unidades del nuevo loteC a6,0000 y vencimiento hoy+30. La fórmula contractual da (18×3+10×6)/28=4,0714. El vendedor vende1 y almacén da baja1 por daño del loteB, luego agota el resto mediante baja8 vencidas deA, baja8 por daño deB y baja10 por daño deC. Costo contractual4,0714 se conserva hasta agotar, cuando queda0. Venta y cuatro bajas deben conservar4,0714 como costo histórico.

Las capturas del recorrido usan Chrome157.0.8103.78, Playwright1.65.1, Django5.2.18 y SQLite3.49.1, tres contextos, zona America/Lima, es-PE y viewport1280×900. Se usa servidorWSGI loopback y middleware completo del producto. Los testigos consultan SQLite en modo solo lectura. El runner crea y elimina únicamente su base temporal y cierra el servidor al finalizar.

## Diagnóstico anterior a la corrección

El recorrido BEFORE completó22 checkpoints entre17:30:10 y17:30:24 Lima el13/11/2026, conservados en antes/. Snapshot08e8acd6d39ce5fc5c526d2dfa8c326f2c19b0f46ef032c6b0245bd89ac3644847. Build180 archivos849dba031ad52612261b94758562a8b277902dca586d4925f05ac6edb438472e, idéntico al inicio/final.

| Efecto | Físico | Promedio esperado | Promedio observado DB | VisibleADMIN/ALMACENERO |
|---|---|---|---|---|
| Fixture |18|3,0000|3,0000|3,00|
| Recepción10×6 |28|4,0714|4,5000|4,50|
| Venta1 |27|4,0714|4,5000|4,50|
| Merma1 |26|4,0714|4,6667|4,67|
| Baja8vencidas |18|4,0714|4,6667|Mensaje de baja guardada, sin costo en selector|
| Baja8vigentesB |10|4,0714|6,0000|Mensaje de baja guardada, sin costo en selector|
| Baja10vigentesC |0|0,0000|6,0000|ADMIN observa6,00 pese a físico0|
| Snapshot venta |—|4,0714|4,5000|Constancia muestra importes de venta, sin costo|

Se reprodujeron la exclusión indebida de unidades vencidas del denominador de recepción, reponderación después de merma y conservación de promedio6 con stock0. Las bajas carecían de campo de costo histórico. Las unidades se conservaron y el turno cerró108,00 exacto. «recorrido_completo» indica terminación del arnés, con los INCUMPLE registrados en comparaciones-costo.json. [Comparaciones](antes/comparaciones-costo.json) · [Ejecución](antes/ejecucion.json) · [Fixture](antes/fixture.json).

Se inspeccionaron visualmente las capturas antes/01-inicial-costo,03-recepcion-confirmada,09-admin-postmerma-costo y15-admin-cero-costo. Los valores y mensajes coinciden con los testigos de DB, con costo formateado a dos decimales. Esta evidencia se conserva después de corregir.

## Ejecución final

La corrida final completó23 checkpoints entre19:59:30 y19:59:45 Lima el13/11/2026. Son las00:59 del14/11 en los metadatosUTC. Conserva22 capturas y23 JSON de observación. Incluye la nueva variante02b de recepción con costo0, rechazada por servidor con el mensaje de mínimo0,0001, conservando hash de todas las tablas de negocio. Corregir a6,0000 permitió completar el recorrido desde el mismo formulario.

| Efecto | Físico y vigente | Costo DB | Resultado |
|---|---|---|---|
| Recepción10×6 sobre físico18/promedio3 |28 y20|4,0714|CUMPLE C-01|
| Venta1 del loteB |27 y19|4,0714|CUMPLE C-02 en esta salida|
| Merma1 por daño del loteB |26 y18|4,0714|CUMPLE C-02 en esta salida|
| Baja8vencidas del loteA |18 y18|4,0714|CUMPLE C-02 con vencidos físicos|
| Baja8 restantes del loteB |10 y10|4,0714|CUMPLE C-02 con existencia restante|
| Baja10 del loteC, agotamiento |0 y0|0,0000|CUMPLE reinicio al agotar|
| Historia posterior al agotamiento |Venta8,00 y cuatro bajas de1/8/8/10|SaleLine y cuatro StockWriteOff.unit_cost4,0714|CUMPLE conservación del costo de salida|
| Cierre del turno |Apertura100,00 y venta8,00|Esperado108,00, contado108,00, diferencia0|CUMPLE en esta muestra|

La consultaADMIN muestra4,07 después de recepción, venta y merma, y0,00 al agotar. El vendedor sólo ve importes de venta y su constancia conserva total8,00, base6,78, IGV1,22, recibido10,00 y vuelto2,00. El runner comprueba que la constancia no contiene rótulos de costo de compra. Se inspeccionaron visualmente las capturas finales02b,03,06,09-admin-postmerma-costo,15-admin-cero-costo y16. Los mensajes, roles y cifras corresponden a los testigos, y los campos se ven legibles en1280×900.

Plan08 iniciale8acd6d39ce5fc5c526d2dfa8c326f2c19b0f46ef032c6b0245bd89ac3644847. Build de182 archivosf9927d5136a2f833693076bf589d155b3d467a32b7dab5b1be1561f7f6cf9978, estable durante la ejecución. Incluye inventory0007_output_unit_cost y la corrección del algoritmo. La comparación posterior detectó edición en inventory/test_audit14e_valuation.py, con el código funcional y las plantillas idénticos a la captura. Los manifiestos guardan cada huella para contrastar con el build de cierre del agente principal. [Ejecución](final/ejecucion.json) · [Comparaciones](final/comparaciones-costo.json) · [Manifiesto](final/build-final.json) · [Índice](final/indice.json).

DOC-03AH-01/C-01 y la secuencia de venta/merma/agotamiento deC-02 tienen esta evidencia nueva. Ajustes deC-03, concurrencia/rollback deC-04, stock legado, migración sobre datos anteriores, recepción con identidad propia y saldos/asignaciones de Kardex conservan sus verificaciones y pendientes independientes. La ejecución aplica migraciones a base nueva; por sí sola no comprueba migración de una base operativa ni reconstrucción de costo histórico.

El runner --final exige costo4,0714 después de recepción y salidas, cero al agotamiento, presentación4,07/0,00 y snapshots de venta y cuatro bajas intactos. El resultadoBEFORE se conserva íntegro. El directorio del comando siguiente debe cambiarse para ejecutar otra vez, ya que el existente se protege contra sobrescritura.

```powershell
$env:PYTHONPATH='C:/Users/walte/AppData/Local/Temp/audit14d-browser-6f523915'
r1-pmv/.venv/Scripts/python auditoria_por_etapas/resultados/evidencias/14-E-20261113/navegador/recorrido_costo.py auditoria_por_etapas/resultados/evidencias/14-E-20261113/navegador/final --final
```

El runner reutiliza las utilidades del archivo conservado de14-D. El argumento de salida debe ser un directorio nuevo. Playwright se instaló temporalmente en la ruta indicada durante14-D y Chrome estable se utiliza mediante channel. Para repetir en otro equipo, emplear entorno de pruebas con Playwright o instalación temporal propia, cambiar PYTHONPATH si corresponde y conservar el runner14-D en su ruta relativa. E14_CHROME admite un ejecutable de Chrome explícito. Las fechas son relativas al día de Lima al ejecutar.
