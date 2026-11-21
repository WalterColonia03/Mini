# Servidor 14-E · F-COSTO · 13/11/2026

Primera pasada, continuación del cursor 14-E-KARDEX-01. Alcance comprobado en este anexo, promedio móvil físico, snapshots de costo de venta/baja/ajuste, agotamiento, rechazo de ajuste sin costo fiable, rollback, roles y migración de costos desconocidos. El protocolo y la continuidad se leyeron completos. La evidencia de 14-D permanece como antecedente y las observaciones siguientes corresponden al build 14-E.

## Fuente, inventario y entorno

El contrato aceptado DOC-03AH-01/C-01..04 y RN-14 prescribe sumar existencias físicas vencidas al valorar recepciones, conservar promedio en salidas y ajustes con físico, ponerlo en cero al agotar físico y conservar costo histórico. RN-28 protege el costo de venta conocido y el desconocido. RN-29 define los roles, RN-05 regula baja y ajuste. Se contrastaron los servicios, modelos y pruebas pertinentes antes de ejecutar. Se conservaron 10 fuentes completas de trabajo, incluidas 08 y las pruebas con expectativas anteriores, en [antes](antes/) y sus [huellas](huellas-antes.json).

| Superficie | Actor | Campo o salida | Uso en los casos |
|---|---|---|---|
| `/productos/categorias/nueva/` | ADMIN | `name` | Categoría ficticia F-COSTO |
| `/productos/nuevo/` | ADMIN | nombre, código interno, categoría, UND, precio, mínimo, control de vencimiento | Producto ficticio costo 3 y precio 10 tras carga |
| `/inventario/carga-inicial/` | ALMACENERO | producto y formset número/cantidad/costo/vencimiento | Dos lotes 8 y 10, costo 3, fechas distintas |
| `/inventario/entrada/` | ALMACENERO | producto y formset número/cantidad/costo/vencimiento |10 unidades a6 |
| `/caja/abrir/` | VENDEDOR | monto inicial |10 |
| `/ventas/` | VENDEDOR | producto/cantidad |1 y20 |
| `/ventas/cobrar/` | VENDEDOR | efectivo, revisión, firma, clave | Cobro y snapshot |
| `/inventario/bajas/nueva/` | ALMACENERO | lote/cantidad/motivo/detalle/clave | Baja 1, agotamiento de vencidos y baja final |
| `/inventario/ajustes/nuevo/` | ADMIN | lote/delta/motivo/clave | Ajuste +2, ajuste final negativo, rechazo con físico 0 |
| Persistencia | Servidor | `Product.average_cost`, stock físico/vendible, `SaleLine.unit_cost`, `StockWriteOff.unit_cost`, `PhysicalAdjustment.unit_cost` | Comparación exacta a cuatro decimales e igualdad histórica |

Se usa Django Client con WSGI en proceso y SQLite en memoria. El runner reutiliza las funciones de aislamiento de 14-D, crea cuentas ficticias con contraseña aleatoria, inicia sesión por HTTP y presenta CSRF válido. Los datos iniciales se crean por formularios. La fecha local se adelanta un día para convertir 8 unidades en vencidas. Ninguna base operativa recibe migraciones o escrituras de esta ejecución.

Los rechazos y fallos comparan huellas de 21 tablas de identity, catalog, inventory, cash y sales, incluidos datos, tiempos y claves. Sesiones técnicas, auth y migrations quedan fuera de esa comparación. La suite de regresión usa su base de prueba independiente. El test de migración aplica 0006→0007 sobre filas antiguas y comprueba conservación de sus campos.

## Matriz de ejecución

| Caso | Requisito y operación | Esperado | Antes | Después |
|---|---|---|---|---|
| E01 | DOC03AH/C-01, carga 18 a 3 | Físico 18, vendible 18, C3 | CUMPLE | CUMPLE |
| E02 | RN-14, solo vence el lote 8 | Físico 18, vendible 10, C3 | CUMPLE | CUMPLE |
| E03 | RN-29, ADMIN intenta recepción |403, huella idéntica | CUMPLE | CUMPLE |
| E04 | DOC03AH/C-04, fallo después de insertar lotes de recepción | Escritura observada y rollback completo | CUMPLE | CUMPLE |
| E05 | DOC03AH/C-01, recepción 10 a 6 con físico18 |28 físico,20 vendible, C4.0714 | INCUMPLE, C4.5000 | CUMPLE |
| E06 | RN-29, ALMACENERO intenta ajuste+2 |403, huella idéntica | CUMPLE | CUMPLE |
| E07 | RN-29, VENDEDOR intenta baja |403, huella idéntica | CUMPLE | CUMPLE |
| E08 | HU-INV-02, baja 999 excede lote |200 con error, huella idéntica | CUMPLE | CUMPLE |
| E09 | DOC03AH/C-04, fallo tras descuento físico de venta | Escritura observada y rollback completo | CUMPLE | CUMPLE |
| E10 | DOC03AH/C-02, venta 1 |27 físico,19 vendible, C4.0714 | INCUMPLE, C4.5000 | CUMPLE |
| E11 | RN-28, snapshot de esa venta |4.0714 | INCUMPLE,4.5000 | CUMPLE |
| E12 | DOC03AH/C-04, fallo tras descuento físico de baja | Escritura observada y rollback completo | CUMPLE | CUMPLE |
| E13 | DOC03AH/C-02, baja1 |26 físico,18 vendible, C4.0714 | INCUMPLE, C4.6667 | CUMPLE |
| E14 | DOC03AH/C-02, snapshot baja |4.0714 | INCUMPLE, campo ausente | CUMPLE |
| E15 | DOC03AH/C-04, fallo tras aumento físico de ajuste | Escritura observada y rollback completo | CUMPLE | CUMPLE |
| E16 | DOC03AH/C-03, ajuste+2 con físico previo |28 físico,20 vendible, C4.0714 | INCUMPLE, C4.5000 | CUMPLE |
| E17 | RN-14, snapshot ajuste |4.0714 | INCUMPLE, campo ausente | CUMPLE |
| E18 | DOC03AH/C-02, baja 8 vencidas |20 físico/vendible, C4.0714 | INCUMPLE, C4.5000 | CUMPLE |
| E19 | DOC03AH/C-02, venta 20 agota todo el físico | Físico0, C0 | INCUMPLE, C4.5000 | CUMPLE |
| E20 | RN-28, conservación de snapshots anteriores | Filas originales idénticas tras agotar | CUMPLE | CUMPLE |
| E21 | DOC03AH/C-03, ajuste+2 desde físico 0 sin costo documentado |200 con error, huella idéntica | INCUMPLE, aceptó y mutó | CUMPLE |
| E22 | DOC03AH/C-02, agotar físico mediante baja | C0 | INCUMPLE, C7 | CUMPLE |
| E23 | DOC03AH/C-02, agotar físico mediante ajuste negativo | C0 | INCUMPLE, C7 | CUMPLE |

El escenario aplica venta 1 y después baja1, de modo que 26 unidades preceden al ajuste+2. Los casos de agotamiento por baja/ajuste se ejecutan en savepoints independientes. La variante E21 previa se revierte después de registrar su incumplimiento para mantener independiente la comprobación posterior.

E04/E09/E12/E15 inyectan un RuntimeError después de la escritura real mediante wrappers sobre `Lot.objects.bulk_create` o `Lot.save`. Registran que los datos cambiaron dentro de la transacción y que todas las huellas vuelven al estado anterior tras la excepción. La evidencia cubre rollback SQLite y mantiene pendiente la serialización concurrente PostgreSQL.

## Tests incorporados y expectativas heredadas

Se añadieron seis pruebas en [test_audit14e_valuation.py](../../../../../r1-pmv/inventory/test_audit14e_valuation.py).

| Prueba | Cobertura adicional |
|---|---|
| `test_http_physical_cost_receipt_sale_writeoff_adjustment_and_history` | Flujo HTTP F-COSTO, nueva recepción a9 recalcula C4.4000, conserva snapshots y reenvío de baja |
| `test_zero_stock_resets_average_preserves_last_cost_and_rejects_unpriced_adjustment` | Agotar vendible conservando8 vencidas mantieneC3, agotar físico mediante venta/baja/ajuste poneC0, recepción posterior2 a7 estableceC7 y conserva salidaC3 |
| `test_role_and_input_rejections_do_not_mutate_cost_or_stock` | Tres permisos denegados y exceso de baja/ajuste con igualdad completa de 13 tablas |
| `test_runtime_failure_after_write_rolls_back_all_cost_operations` | Cuatro puntos de fallo después de escritura con rollback y registro de escritura efectiva |
| `test_legacy_unknown_costs_are_not_filled_from_current_average` | Costos NULL de venta/baja/ajuste continúan NULL después de recibir con otro costo |
| `test_upgrade_preserves_old_rows_with_unknown_cost` | Migración0006→0007 real, filas antiguas reciben NULL y conservan campos, fechas, costo del producto y stock |

Las siguientes expectativas quedaron sustituidas con fundamento en08 y copia anterior conservada.

| Fuente anterior | Expectativa sustituida | Expectativa vigente |
|---|---|---|
| `inventory/tests.py`, caso BUG-005 recepción | Excluir10 vencidas a2 y recibir10 a6 produce C6 | Incluir físico produce C4 |
| `inventory/tests.py`, caso BUG-005 baja/ajuste | Al retirar lote de costo2 queda promedio4 | Conserva promedio móvil3 |
| `inventory/test_audit06_stock_entry.py`, variante vencidos | Excluir5 vencidas a2 al recibir5 a6 produce C6 | Físico10, C4 |
| `inventory/test_audit08_writeoffs_adjustments_movements.py`, impacto costo | Baja cambia3→4, salida posterior toma4, agotar conserva4 y ajuste+3 sin costo acepta | Conserva3, snapshot3, agotar pone0, ajuste sin costo rechaza |

Las pruebas válidas de carga, HALF_UP, snapshots previos y costo desconocido permanecen en el conjunto ejecutado. Los documentos históricos que describen BUG-005/BUG-037 contienen el comportamiento de su corte. Su existencia conserva contexto y no reemplaza RN-14 vigente.

## Revisión independiente de la implementación

Se inspeccionaron los cambios del agente principal en servicios, modelos y migración. La recepción suma todas las cantidades físicas con promedio anterior bloqueado. Los retiros llaman `reset_average_cost_if_empty` después de persistir el movimiento, dentro de la transacción que conserva el lock del producto. Ese helper consulta lotes persistidos, incluidos vencidos, y evita basarse en una caché de stock precargada. La venta captura el promedio del producto bloqueado antes de descontar. Baja y ajuste guardan su costo antes del eventual reset.

Los campos nuevos `unit_cost` son decimales de cuatro posiciones y permiten NULL sin un valor por defecto inventado. La migración agrega esos campos y conserva la historia anterior. El rechazo de ajuste positivo sin físico ocurre antes de escribir el ajuste. Las pruebas ejecutadas no encontraron una divergencia nueva en estas rutas.

Quedan fuera de la aprobación de este sublote el diagnóstico/revaloración de existencias operativas cuyo promedio proviene del algoritmo anterior, ajuste desde físico 0 aportando costo documentado mediante interfaz, costo y valor total de salida visible en Kardex, constancia dedicada de merma, asignaciones durables por lote, saldos/filtros y concurrencia PostgreSQL. Los snapshots nuevos están persistidos y comprobados en servidor. Los costos históricos NULL requieren cobertura explícita en futuras consultas.

## Evidencia y reproducción

| Ejecución | Resultado | Evidencia |
|---|---|---|
| Runner antes |11/23 cumplen,12 incumplen | [costos-antes.json](costos-antes.json) |
| Runner después |23/23 cumplen | [costos-despues.json](costos-despues.json) |
| Regresión acotada con expectativas actualizadas |66/66,12.995s | [regresion-costo-despues.txt](regresion-costo-despues.txt) |
| Seis pruebas 14-E finales con fronteras adicionales |6/6,2.287s | [14e-final.txt](14e-final.txt) |

Los conjuntos se solapan. La matriz de 23 operaciones constituye un denominador de casos del runner, y los seis tests usan subcasos. Estos numeradores no aprueban las historias completas ni los cuatro criterios del contrato en su totalidad. DOC03AH/C-04 sigue PARCIAL por concurrencia PostgreSQL, C-03 se verificó para Q>0 y rechazo sin costoQ0; el contrato general conserva pendiente el camino con costo fiable documentado desde físico0.

```powershell
# Desde la raíz de planificación, usar salida nueva para preservar registros anteriores.
r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-E-20261113/servidor/costos.py auditoria_por_etapas/resultados/evidencias/14-E-20261113/servidor/repeticion-nueva.json

# Desde r1-pmv
$env:APP_ENV='test'
$env:DJANGO_DEBUG='false'
$env:PYTHONUTF8='1'
.venv/Scripts/python.exe manage.py test inventory.test_audit14e_valuation inventory.tests inventory.test_audit06_stock_entry inventory.test_audit08_writeoffs_adjustments_movements sales.test_audit03ag_cost --verbosity 1
```

El [runner](costos.py) contiene el escenario y sus aserciones. Cada JSON guarda los hashes de servicios/modelos y de08 vigentes al ejecutar. La huella completa de producto y la regresión integral se registran desde la coordinación de 14-E. Próximo cursor de servidor, contraste de Kardex y salida histórica tras una nueva recepción con costo distinto, incluyendo datos heredados NULL y el valor de cada movimiento.


La regresión integral final fue566/566 en79.782s, sin cambios de fuentes durante la ejecución y sin migraciones faltantes. [Log](regresion-final.txt) · [Manifiesto](regresion-manifiesto.json) · [Runner aislado](regresion.py). La corrida inicial566/566 se conserva en regresion-1.txt; se repitió tras dos nuevas aserciones del test de agotamiento, sin modificar runtime.
