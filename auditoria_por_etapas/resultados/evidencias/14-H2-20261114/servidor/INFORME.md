# Servidor14-H2 · 14/11/2026 Lima

Primera pasada. Python3.12.10/Django5.2.18/SQLite3.49.1. Cada corrida configura APP_ENV=test y SQLite en memoria antes de django.setup; no conecta a la base operativa. Build198 `3bed2cd9e85e61dfe2dae607e438a83be911950ec328de59ac596b407155b1f6`. Fuente08 ejecutada `4c46f42530b25499e4f4cf31426e9fafd9293b95efdbddb38ed74403ae2e7e77`; fuente final `d2e03f10c190cf6a631152b35fa110d863d0fb3276723f6e7e95e8a0451ffa4a` conserva los sietecriterios y actualiza estados/evidencia.

```powershell
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-H2-20261114/servidor/regresion.py <directorio-nuevo>
```

| Corrida conservada | Resultado | Alcance |
|---|---|---|
| [corrida-1](corrida-1/regresion-final.txt) |595/603;8errores;84.154s|Error de fixture: load.lots.get() incluía recepción posterior. Se usa línea inicial capturada; no cambio de producto para aprobar|
| [final, antes deCSS](final/regresion-final.txt) |604/604;98.310s|Añadida prueba de intercalación delecturas; HTML funcional, defecto móvil aún pendiente|
| [final2, vigente](final2/regresion-final.txt) |604/604;97.397s|Fuentes estables y ninguna migración pendiente. [Manifiesto](final2/regresion-manifiesto.json)|

Doce tests nuevos en inventory/test_audit14h2_ledger.py verifican: casoescrito20+10−5−2+1=24; cursor10+10+5−22−1=2 yventa multilote;26ajustes al mismoinstante con25+1páginas;15variantes inválidas de fechas/tipo/página/duplicados; extremos de año1/9999 ysegundo59.999999delminutofinal; entrada heredada; asignación parcial eidentidadambigua; discrepancias compensadas porlote; FK deorigen incoherente; secuencia negativa; lote añadido entrelecturas; roles/métodos/productoinactivo/productovacío. GET yrechazos contrastan26tablas denegocio, excluyendo sesiones/login.

El caso escrito usa instantes09:00..13:00Lima deldía anterior alensayo en lugar de fijar12/11; cantidades/orden/resultados se conservan. El cursor adicional abre20 al10:01 yfiltra soloVenta: saldo3, cierre2, variación−22. El caso de páginas conserva total26/variación+26/apertura50/cierre76 enambaspáginas. La consulta sigue dentro del presupuesto histórico15queries ensu prueba existente; no suponeSLArendimiento ni costo constante.

Una expectativa histórica exigía ausencia de saldo/filtros; se reemplaza porpresencia conforme aINV04seleccionado. Las rutas globalesINV05/06 siguenausentes y su prueba se conserva. No hay migración nueva ni cambio en servicios deescritura. La prueba deintercalación no utiliza conexionesconcurrentes:demuestra que ellector no falla conKeyError anteun lote nuevo entrepasos, no aislamientoPG.

No ejecutado: carreraPG delKardex, paginación mientras se insertan datos, volumen productivo, caída real, regularización delegado. Dosramas deaviso (cabecera incompleta/dobleorigen) inspeccionadas, no inyectadas enH2; el resto deincertidumbres tieneprueba específica. [Criterios](../criterios-final.json) · [Caso](../../../../../08_Historias_de_Usuario.md#CP-HU-INV-04-001).
