# Disposiciones de integración 14-D · 13/11/2026

Primera pasada. El encargo de esta sesión exige comprobar el recorrido entre identity, catalog, inventory, cash y sales, corregir producto dentro del alcance autorizado y mantener la fuente08. Se interpretó ese encargo como autorización para correcciones técnicas locales contra reglas ya aceptadas. Los contratos12/11 aportan el requisito. El protocolo y los informes aportan el procedimiento y la evidencia.

## Decisiones y fundamento

| ID | Estado y fundamento | Cambio y evidencia | Alcance pendiente |
|---|---|---|---|
| D14-01, descuentos | ACEPTADA previamente en DEC-11-DESCUENTOS-ALCANCE/C-01..03. IMPLEMENTADA y revalidada en esta sesión | Formulario nuevo sin control de descuento. Parámetro positivo/negativo/inválido/múltiple rechazado con texto literal. Servicio rechaza antes de modificar borrador/stock/caja. Reintento de venta histórica se valida antes de aplicar política nueva. Histórico20−2=18 recuperado por servicio y HTTP, también después del cierre. [Regresión](../evidencias/14-D-20261113/servidor/regresion-final.txt) | Concurrencia y fallos de proceso conservan etapa 15. Resto de VEN conserva sus brechas |
| D14-02, causa real de merma | ACEPTADA previamente en RN-05 y HU-INV-02/CA-02. IMPLEMENTADA y revalidada para causa/fecha/detalle | Vencimiento solo desde la fecha Lima del lote. Daño solo antes. Robo/faltante con explicación en ambas situaciones. S12/15/16 antes incumplían y después cumplen las expectativas acotadas. [Informe servidor](../evidencias/14-D-20261113/servidor/INFORME.md) | RN-05/C-01 conserva costo de salida pendiente. C-02 ajuste nuevo, C-03 constancia y C-04 concurrencia pendientes |
| D14-03, prueba C16 | Corrección de evidencia autorizada por auditoría, IMPLEMENTADA y VERIFICADA | Seleccionar venta por clave enviada y exigir correlativo consecutivo exacto. Corrida previa558/559 falló con dos lecturas del mismo UUID, final560/560 pasó | La prueba comprueba secuencia secuencial. Carreras del contador exigen PostgreSQL |
| D14-04, caso conectado | ACEPTADO como especificación de prueba por el pedido explícito de recorrido y CT-COHERENCIA-UI/C-04 | CP-INTEGRACION-ROLES-001 en08, datos y expectativas propias. 44 checkpoints de Chrome y18 variantes Client. Criterios transversales PARCIAL por las brechas anotadas | Conserva los requisitos completos de cada HU y el resto de CT-ROLLBACK |
| D14-05, precisión editorial | ACEPTADA por coherencia de fuente, sin cambiar la política de RN-05 | CP-HU-INV-02-001 enumeraba tres variantes admitidas y decía «acepta dos». Se expresa aceptación de las tres variantes independientes | Constancia y costo del caso completo siguen pendientes |

La suspensión del descuento se reprodujo antes del cambio ejecutando la prueba heredada que admitía10.64 de descuento sobre10.65. El resultado verde evidenciaba el comportamiento contrario al contrato vigente. Se adaptaron las pruebas del cobro nuevo a precio completo y se materializaron fixtures monetarias históricas para conservar la cobertura de constancia/historial con descuento. El nuevo test de causas de merma protege una regresión concreta que las pruebas anteriores omitían. [Reproducción del descuento previo](../evidencias/14-D-20261113/descuento-antes.txt) · [Fuentes de merma previas](../evidencias/14-D-20261113/servidor/antes-correccion-merma/).

## Cambios y revalidación

| Superficie | Archivos o función | Comprobación |
|---|---|---|
| Cobro | sales/forms.py, views.py, services.py, templates/sales/sales_checkout.html | Validación de cero/ausencia, conservación de identidad histórica, vuelto JS5.80, error por efectivo14.19 y confirmación14.20 |
| Merma | inventory/services.py | Validación después de bloquear producto/lote, error de campo coherente, autor y fecha conservados |
| Regresión | sales/tests.py, test_audit11_checkout.py, test_audit12_receipts_history.py, cash/test_audit09_cash.py, tests/test_audit14c_edge_cases.py, inventory/tests.py, test_audit08_writeoffs_adjustments_movements.py | 560/560 final, 81 pruebas acotadas del cobro y58 de inventario. Los conjuntos se solapan |
| Planificación | 08 primero, vistas07/09/03 regeneradas, contexto01/02/14/16/21 y continuidad | 74 HU,287 criterios,112 casos escritos. El caso nuevo aporta trazabilidad, sin crear una historia duplicada |

La revisión independiente del agente servidor examinó las rutas de descuento y C16. El agente de inventario corrigió IDs del antecedente y clasificó80 CA. El agente de navegador ejecutó HTTP real y controles del cliente con tres sesiones. El agente principal inspeccionó las capturas26,30b,34,38 y contrastó cifras con los testigos. Los módulos03–12 conservan el alcance y los pendientes propios de sus informes.

## Recomendaciones y trabajo siguiente

| Referencia reutilizada | Necesidad y beneficio | Alternativas, riesgo y costo relativo | Impacto y aceptación |
|---|---|---|---|
| DOC-03AH-01 / RN14 / RN28 | Conservar promedio móvil físico y costo de cada salida permite conciliar margen e inventario después de vender o dar baja | Completar servicios y snapshots. Recalcular desde costos actuales pierde historia. Costo medio-alto por datos antiguos | Alta prioridad, contrato ACEPTADO, implementación completa pendiente. Primer paso del cursor14-E |
| DEC-11-MODELO-AUDITORIA-VENTAS | Guardar asignación real por lote para que ADMIN audite lo que VENDEDOR consumió | Filas de asignación ligadas a SaleLine dentro de la misma transacción. Un registro genérico de movimientos es alternativa si mantiene garantías. Costo medio-alto, migración y diagnóstico legacy | Impacto alto, ACEPTADO como necesidad. Decisión concreta de representación pendiente de diseño verificable |
| DEC-08-KARDEX-COMPRAS / HU-INV-04 | Mostrar saldo inicial, cambios y saldo final con filtros estables permite contrastar caja/ventas/almacén | Completar consulta desde orígenes persistidos. La reconstrucción de lotes desconocidos requiere evidencia histórica. Costo medio, dependiente de recepción/asignación/costo | ACEPTADO, PARCIAL. Cursor14-E-KARDEX-01 |
| RN-05/C-03 / HU-INV-02/CA-04 | Constancia dedicada de baja facilita revisar autor, causa, cantidad y costo después de cerrar la jornada | Vista inmutable vinculada a baja existente. PDF exportable agrega mantenimiento y puede diferirse si impresión web cumple lo aceptado. Costo medio | ACEPTADO, pendiente. El correlativo mostrado en mensaje aporta solo una parte |
| CT-COHERENCIA-UI / NFR de accesibilidad | Un resumen de errores enfocable facilita recuperar formularios por teclado y lector de pantalla | Conservar errores junto al campo y añadir foco/enlaces cuando proceda. Riesgo de foco inesperado si se aplica al editar. Costo bajo-medio | PROPUESTA de mejora UX, requiere caso de teclado/lector propio. La revisión visual actual cubre escritorio1280×900 |
| CT-ROLLBACK / SEC-15-CONC-02 | Demostrar atomicidad frente a carrera y caída real protege ventas, caja y stock compartidos | PostgreSQL17 aislado, conexiones independientes y barrera postwrite. Costo medio-alto. SQLite carece de la semántica de bloqueo objetivo | ACEPTADO como prueba, pendiente etapa 15 |
| RN-05 apertura de producto solo vencido | Permitir regularizar un conteo real sin fingir recepción vendible | Procedimiento de inventario de apertura o ajuste con origen propio. Falta conocer operación y documentación reales. Costo medio, riesgo de inventar fechas/costos | INVESTIGACIÓN pendiente de negocio. Continúan los trabajos independientes |

Se reutilizan HUs, reglas y tareas existentes porque ya describen estas necesidades. La propuesta UX y las alternativas de representación conservan su condición de propuesta. La aceptación de requisitos existentes se sustenta en08 y su registro de delegación, y las correcciones locales se sustentan en el encargo de esta sesión. Se preservó la evidencia previa, con una credencial ficticia del antiguo informe14 redactada para cumplir el protocolo.
