# Disposiciones 14-G · 13/11/2026 Lima

Primera pasada. El encargo y la delegación de integración vigentes cubren corregir producto conforme a HU-INV-01b, DOC-03AI-01, RN-01/03/14/19/29 y DEC-05-LOTE-ESPACIOS. El diagnóstico Chrome previo reproduce ausencia de identidad y reintento, lote comercial bloqueado y nombres históricos variables. Las siguientes concreciones implementan requisitos aceptados; no constituyen ampliación comercial por existir en el código.

| ID | Decisión y fundamento | Estado / beneficio / riesgo / costo / impacto |
|---|---|---|
| D14G-01 |Cabecera StockReceipt, líneas StockReceiptLine y contador global. Una línea enlaza un lote físico; guarda cantidad/costo/vencimiento originales. ContratoDOC03AI|Implementado/verificado en muestra. Identifica procedencias y protege cantidades tras ajuste. Costo medio de esquema/servicios/UI; riesgo de migración mitigado con prueba aislada|
| D14G-02 |UUID obligatoriaHTTP, huella canónica del producto/proveedor/líneas ordenadas; costo4 y número normalizado. Actor comprobado separadamente|Implementado/verificado. Reenvío igual recupera confirmación; divergencia no muta. Llamada interna sin clave significa ingreso nuevo y generaUUID; consumidores con reintento deben persistir su clave. No hay deduplicación temporal|
| D14G-03 |Consultar el resultado confirmado tras expiración/desactivación no crea stock; actor revocado sigue denegado|Concreción técnica aceptadaDOC03AI/C02. VerificaciónHTTP/BD con cambio de fecha/estados. Evita perder confirmación por estado posterior. Una clave ajena no muestra datos de otra recepción|
| D14G-04 |Eliminar unicidad global del número, conservar unicidad de carga inicial y de línea dentro de recepción; comprobar fechas coherentes|Implementado/verificado. PermiteC10 yC5 con procedencias distintas. Normaliza espacios para nuevos datos y comparación; no fusiona ni reescribe legado. Diagnóstico operativo previo a despliegue sigue pendiente|
| D14G-05 |La migración no rellena recepciones antiguas. FK a carga e is_initial no bastan para reconstruir historia|Implementado/verificado sobre filas ficticias conservadas. Constancia de carga/consulta explican maestros actuales y origen incompleto. Snapshots de nuevas cargas iniciales siguen pendientes; no declararlos resueltos|
| D14G-06 |MostrarR-######## en selección de baja/ajuste y enlazar procedencia de entradas, asignaciones de venta, bajas/ajustes en movimientos|Necesidad derivada del lote comercial repetido, aceptada dentro del contrato de trazabilidad. Costo bajo, evita elegir una entrega equivocada. MuestraChrome/HTTP; historial completo de merma aún pendiente|
| D14G-07 |Conservar trigger de inmutabilidad received_at al reconstruir Lot enSQLite, en ambos sentidos de migración|Defecto de regresión identificado y corregido. GarantíaFEFO existente; coste bajo. Pruebas SQL/ORM históricas pasan. PostgreSQL requiere su revalidación15|
| D14G-08 |Prefetch con relaciones en consulta para respetar presupuesto de consultas existente|Defecto de regresión corregido sin subir el umbral15 de la prueba. Costo bajo; volumen real/SLA pendientes|
| D14G-09 |Adaptar fixturesHTTP con UUID y expectativas de ruta propia; rechazo de lote repetido pasa a fecha contradictoria|Cambio de contrato ya aceptado, no rebaja para aprobar suite. Snapshot completo anterior preservado. Pruebas nuevas comprueban reintento, lote comercial repetido y contradicción|

La alternativa de agrupar todo en InitialInventoryLoad no preserva identidad ni proveedor/autor/costo por entrega. La alternativa de una tabla genérica de eventos/idempotencia añade complejidad sin necesidad demostrada de otros consumidores. El esquema elegido mantiene monolito, servicios y formularios existentes; ninguna infraestructura externa se modifica.

La reversión de0008 después de registrar entregas repetidas puede encontrar datos incompatibles con la antigua unicidad global del lote. No se debe resolver eliminando o fusionando recepciones. El ensayo de respaldo/restauración y la estrategia de reversión con datos nuevos quedan en15; esta sesión solo migró bases ficticias.

La revisiónUI usa componentes actuales, etiquetas visibles, aviso de éxito con referencia y explicación junto al dato histórico incierto. La búsqueda de la guía UI/UX sobre confirmación recomendó mensaje breve de éxito; el resultado sobre borrado no se aplicó. La guía de verificación del flujo se aplicó a formulario→servidor→datos→constancia, continuando variantes por el mandato explícito de auditoría. No se envió ningún mensaje externo.

## Pendientes y recomendaciones

| Trabajo | Beneficio | Riesgo/costo/impacto | Estado |
|---|---|---|---|
| Diagnóstico de origen y colisiones en copia operativa autorizada |Saber qué historia es demostrable|Costo medio de investigación; no inferir entradas de fechas/FK|Datos del negocio pendientes; no tocar base operativa|
| Snapshots y cantidades fiables en nuevas cargas iniciales |Evitar nombres actuales presentados como historia|Costo medio; dependenciaINV01a/03AI, contratos ya aceptados|Pendiente, actualmente rotulado como maestros actuales|
| ConcurrenciaPG del contador y misma clave; caída real |Demostrar serialización/recuperación|Costo medio, entorno aislado; afecta integridad|Pendiente15, SQLite no basta|
| Saldo cronológico/filtros/paginación |Conciliar movimientos con físico|Costo medio, referencias de ingreso/salida ya disponibles|Cursor14-H-KARDEX-SALDOS-01|
| Constancia propia de merma y fotografía de actor |Explicar bajas después de cambios|Costo medio; no asumir que enlace a recepción la sustituye|Pendiente propio del inventario14|

No se añadieronHU ni se cambió selecciónMoSCoW.08 conserva74HU/287criterios/112casos, con estados parciales y especificación técnica incorporada antes de regenerar07/09/03.02/14/16/21 y continuidad se actualizan en el mismo corte. [Inventario](14-G-inventario.md) · [Informe](../ETAPA-14.md#vigente-14-g).
