# Disposiciones de integración14-F · 13/11/2026

Primera pasada, continuación14-F-ASIGNACIONES-01. El encargo de auditoría de la sesión y la delegación vigente cubren correcciones técnicas de la integración. RN-25/28 y DEC-11-MODELO ya exigen asignaciones y fotografías históricas. DEC-12-ORDEN exige posición estable de línea. Los cambios se apoyan en esos requisitos y en el diagnóstico previo conservado.

| ID | Fundamento y estado | Resolución | Cobertura y pendientes |
|---|---|---|---|
| D14F-01 |Requisito aceptado RN-25, DEC-11/C-01. IMPLEMENTADO y VERIFICADO en muestra|Asignación por línea/lote duranteFEFO, fotografía del número/vencimiento/ingreso y suma exacta antes del commit|A3/B7→venta4 asigna3/1. A3/B2→venta5 asigna3/2. PG y escritura directa pendientes15|
| D14F-02 |Requisito aceptado DEC-11/C-03 y DEC-12/C-01. IMPLEMENTADO y VERIFICADO|Nombre de vendedor y código de caja capturados bajo bloqueo, posición positiva única por línea|Renombrar maestros conserva documento y orden. Empates de turnos y demás C-01 de DEC-12 conservan pendientes|
| D14F-03 |Concreción técnica aceptada bajo DEC-11/C-04. IMPLEMENTADA y VERIFICADA|Migración nullable sin backfill. Consulta de desconocido y cobertura parcial. Costo mostrado solo en consulta interna permitida|Migración0005→0006 comparó todas las columnas antiguas. Base operativa y reconstrucción sustentada pendientes|
| D14F-04 |Equivalencia técnica permitida expresamente por DEC-11/02, aceptada en el alcance de una caja y venta en efectivo|Sale representa el único evento de ingreso de la venta. Turno/correlativo/clave/autor/instante/total lo identifican. Cierre suma una vez el total|Apertura100+venta50=cierre150, reintento posterior intacto, ocho fallos postwrite. Nuevos medios, anulaciones y caja manual requieren revalidar el diseño|
| D14F-05 |Corrección de evidencia autorizada por auditoría. IMPLEMENTADA y VERIFICADA|Fixture ReceiptTests incorpora datos históricos conocidos y posición1|Primera corrida572/573 falló por nombre de caja sin snapshot. Final574/574. La fuente previa coincide por hash con el manifiesto inicial|
| D14F-06 |Verificación transversal solicitada. EJECUTADA|RecorridoChrome de12 checkpoints para asignación/historia/legado y repetición de44 checkpoints desde alta de maestros hasta cierre|Fixtures separadas con build final común. Mantienen límites propios y conjuntos solapados|

## Beneficio, alternativas e impacto

Guardar el lote real permite explicar cada salida después de recibir nueva mercadería o editar maestros. El costo relativo es medio por migración y transacciones, y afecta ventas, movimientos, constancia e historial. Los snapshots de lote preservan evidencia aunque se modifique su ficha. La igualdad entre suma asignada y línea se verifica en el servicio con pruebas de fallos.

La representación de ingreso en Sale aprovecha el modelo de venta exclusivamente en efectivo y la suma ya utilizada por cierre. Mantiene una fuente por evento. Una tabla adicional de movimientos sería una alternativa para orígenes heterogéneos, con costo medio/alto de migración, vínculo único y conciliación para evitar doble conteo. Esa alternativa queda propuesta para necesidades futuras seleccionadas. La equivalencia adoptada se integró en08/02 con evidencia de importe, turno, reintento y rollback.

Los registros históricos ausentes mantienenNULL. La consulta explica ausencia, asignación parcial o identidad no confirmada cuando solo coincide un código. El beneficio es evitar atribuciones históricas falsas. Investigar procedencia de datos reales tiene costo adicional y requiere hechos del negocio. La interfaz nueva conserva los controles habituales y presenta avisos junto al dato afectado. La consulta local de la guía UI/UX devolvió la recomendación de explicar estados vacíos, aplicada a estas ausencias.

## Cambios y revalidación

| Superficie | Implementación | Evidencia |
|---|---|---|
| Persistencia |sales/models.py y sales/migrations/0006_sale_lot_traceability.py|Asignaciones positivas/únicas y FK protegidas. Campos nullable y migración sobre historia ficticia|
| Cobro |sales/services.py|Bloqueos actor/caja/turno y producto/lotes, captura/suma bajo transacción, reenvío y rollback|
| Lecturas de venta |sales_receipt.html y sales_history.html|Captura de vendedor/caja y orden reabiertos en Chrome, costo fuera de constancia|
| Inventario interno |inventory/views.py y product_movements.html|Lotes y costo de salida, ausencia/parcial, accesoADMIN/ALMACENERO y403VENDEDOR|
| Pruebas |sales/test_audit14f_allocations.py y sales/tests.py|Ocho nuevos tests, fixture corregida,574/574 final|
| Planificación |08 primero, derivados07/09/03,02/14/16/21 y continuidad|Requisitos preservados y estados parciales con build identificado|

[Inventario y alternativas](14-F-inventario.md) · [Servidor](../evidencias/14-F-20261113/servidor/INFORME.md) · [Navegador](../evidencias/14-F-20261113/navegador/RESUMEN.md).

## Límites y siguiente sublote

La evidencia secuencialSQLite cubre errores de aplicación y excepciones tras escritura. ConcurrenciaPostgreSQL, caída real, protección de datos ante acceso directo y despliegue siguen en15. La impresión física mantiene su pendiente propio. El margen permanece futuro.

La recepción posterior aún reutiliza la carga inicial y la consultaKardex carece de saldo/filtros/paginación completos. La siguiente tarea14-G-RECEPCIONES-01 debe resolver origen e idempotencia de recepción con datos anteriores clasificados. Constancia de merma, ajuste con lote nuevo/costo documentadoQ0 y valoración operativa conservan su cursor pendiente.
