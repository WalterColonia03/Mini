# Servidor 14-F · Asignaciones e historia de venta

Primera pasada, 13/11/2026 Lima. Contratos DEC-11-MODELO-AUDITORIA-VENTAS/C-01..04, DEC-12-ORDEN-LINEAS-RECIBO/C-01 en su tramo de líneas y DEC-08-KARDEX-COMPRAS/C-02. Se usaron cuentas ficticias, SQLite aislada, servicios transaccionales y Django Client con loginHTTP y CSRF para el runner.08 ejecutado tuvo SHA256 ddadb1091e8501a00c0ae9ff9da212bce65446000131f137cede389ebc5313ad.

## Antes y después

| Caso | Observación anterior | Resultado final |
|---|---|---|
| F01/F02, A3/B7 vende4 |Saldo0/6 correcto y asignaciones ausentes|Asignaciones3/1 persistidas y saldo0/6|
| F03/F04, identidad histórica |Cambiar vendedor/caja cambiaba constancia|Fotografías originales preservadas|
| F05, reenvío |Una venta secuencial|Misma venta y asignaciones, sin nuevo descuento ni efectivo|
| F06, almacenero intenta cobrar |403|403 con persistencia idéntica|
| F07/F08, contratoA3/B2 vende5 |Costo3 conservado y promedio0, asignaciones ausentes|Asignaciones3/2, costo3 y promedio0|
| F09/F10, tres líneas con UUID3,1,2 |OrdenB,C,A, posición ausente|OrdenA,B,C con posiciones1,2,3|
| F11/F12, legado |NULL conservado, constancia usaba datos actuales sin aviso|Dato histórico no disponible, NULL y asignaciones vacías preservados|

El runner inicial obtuvo5/12 y el final12/12. La corrida intermedia después también obtuvo12/12, con una huella anterior de models.py. Se reejecutó contra el build final para dejar correspondencia exacta. [Antes](asignaciones-antes.json) · [Intermedia](asignaciones-despues.json) · [Final](asignaciones-final.json).

## Pruebas de regresión y migración

Ocho tests nuevos comprueban el cobroHTTP, suma exacta y snapshots de lote, reenvío, cierre, fotografía/orden, rollback, permisos, legado y migración. Cada test contiene variantes explícitas. El test de fallos observa escritura real antes de generar una excepción en contador existente, Sale, SaleLine, primera asignación, primer descuento del lote, segunda asignación, segundo descuento y descarte del borrador. Compara todas las22 tablas de negocio y completa un control positivo posterior. Se conserva el contador anterior y ninguna venta parcial queda confirmada.

La variante contractual abre100, vende5×10, cierra150 y reenvía después del cierre. Se mantiene una venta, un total50 en el turno y dos asignaciones3/2. Así se verifica la representación de Sale como ingreso de efectivo de la venta conforme a la equivalencia aceptada en08.

El ensayo de migración retrocede sales hasta0005 en una base temporal, crea venta/línea antigua, avanza a0006 y exige todos los valores previos idénticos. Vendedor/caja/posición nuevos quedanNULL y la tabla de asignaciones vacía. La consulta antigua usa ordenUUID declarado. El test de movimientos materializa FKproductoNULL y cobertura parcial, comprueba leyendas y GET sin mutación. Una edición técnica del maestro de lote conserva número/vencimiento/ingreso capturados en la asignación.

| Ejecución | Resultado |
|---|---|
| Suite focal inicial |38/38 en19.264s, antes de ampliar puntos de fallo y cobertura parcial|
| Tests14-F definitivos |8/8 en2.791s|
| Primera suite completa |572/573, falló fixture de constancia sin snapshots. También hubo cambios de archivos durante esa corrida|
| Suite completa final |574/574 en76.868s, fuentes estables, system check sin incidencias y makemigrations --check sin diferencias|

[Suite focal](14f-acotada.txt) · [Ocho tests](14f-final.txt) · [Primera corrida completa](corrida-1/regresion-final.txt) · [Regresión final](regresion-final.txt) · [Manifiesto estable](regresion-manifiesto.json). Los conjuntos se solapan.

La fixture ReceiptTests creaba directamente una venta y exigía el nombre actual de caja. Se añadieron los snapshots conocidos y posición1 a esa fixture para representar una constancia con historia capturada. El caso de datos desconocidos tiene prueba propia. La [fuente anterior](antes/r1-pmv/sales/tests.py) se recuperó retirando exactamente las tres líneas añadidas y su SHA256 coincide con el manifiesto inicial. Las expectativas funcionales conservan el requisito de constancia histórica.

## Evidencia reproducible

Desde la raíz de planificación, usar una salida inédita.

```powershell
r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-F-20261113/servidor/asignaciones.py auditoria_por_etapas/resultados/evidencias/14-F-20261113/servidor/repeticion.json
r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-F-20261113/servidor/regresion.py auditoria_por_etapas/resultados/evidencias/14-F-20261113/servidor/regresion-nueva
```

El primer runner crea una SQLite nueva junto alJSON y elimina sesiones, intentos de autenticación y hashes de credenciales de esa base ficticia al terminar. Las bases anteriores recibieron el mismo saneamiento, con huella de ventas/líneas/lotes/asignaciones idéntica. El segundo crea una base en memoria y manifiestos antes/después. [Saneamiento de bases anteriores](sanitizacion-bases.json) · [Verificación final de las tres bases, solo lectura](verificacion-bases-final.json). La base operativa quedó fuera del alcance.

Concurrencia PostgreSQL, interrupción real de proceso, impresión física, protección ante escrituras directas y datos operativos siguen pendientes. La fórmula y derechos del flujo normal están revalidados en este entorno. La recepción propia y el Kardex completo requieren la continuación14-G.
