# 03-AD / 05-C · Fecha de ingreso y salida FEFO

11 de noviembre de2026, America/Lima. Continuación del cursor05-C. Fuentes del tramo: HU-INV-01a/CA05 (08:326), RN-19 (07:231–241), diseño DT-07, tareas S1-INV01A-TXDB y S1-VEN01C-FEFO. Se conserva el inventario de catálogo y recepción de03-AB/AC. La frontera ejecutada de venta corresponde al descuento de lotes, sin cierre integral de las etapas de cobro e historial.

## Inventario y clasificación

| Requisito, acción o salida | Clasificación | Verificación |
|---|---|---|
| Instante de ingreso asignado por servidor y conservado | SELECCIONADO, INV01a/CA05 y RN-19 | Alta y salida autorizadas, intento de guardar otra fecha, update, bulk_update y SQL directo. |
| FEFO por vencimiento | SELECCIONADO, RN-19 | Lote de vencimiento posterior ingresado antes que los demás. Sale después de los de vencimiento próximo. |
| Desempate por instante de ingreso | SELECCIONADO, RN-19 | Entre lotes con igual vencimiento, se consume primero el de ingreso más antiguo. |
| Desempate final por UUID | SELECCIONADO, RN-19 | Dos lotes con igual vencimiento e ingreso, insertados en orden inverso y con números comerciales que ordenarían de otro modo. |
| Exclusión de vencidos | Regla vigente de disponibilidad y frontera de07/11 | Lote que vence hoy conserva sus cinco unidades durante todas las ventas. |
| Búsqueda y cobro | VENDEDOR, rutas /ventas/, /ventas/cobrar/ y /ventas/constancia/<uuid>/ | Consultar código, indicar3/2/3 unidades en ventas sucesivas, revisar resumen, introducir efectivo exacto, confirmar. |
| Reenvío de cobro | Frontera de idempotencia existente | Repetir el POST confirmado conserva los lotes. Dos solicitudes concurrentes con la misma intención producen una sola venta. |
| Inventario final | ALMACENERO, /inventario/stock/ | Cinco unidades físicas, cero vigentes y estado «Sin stock vendible». |
| Administración técnica | Campo received_at no editable generado por auto_now_add. Inline de carga lo expone solo para lectura | Inspección de modelo/admin. La auditoría completa del administrador técnico sigue en15. |

Los campos comerciales ejercitados fueron query, quantity, cash_received y los valores de revisión e idempotencia generados por el formulario. Las cuentas y artículos son ficticios. El navegador comprueba el identificador del servidor aislado antes de autenticarse. El inventario previo consta en cada ejecución.

## Hallazgo y corrección

**H-03AD-01 · Prioridad alta, corregido en código y migración de ensayo.** El campo con auto_now_add generaba la fecha al crear, pero una llamada posterior a save podía reemplazarla y alterar el desempate FEFO. Se reprodujo con guardado completo y con update_fields. La validación del modelo ahora rechaza el cambio con «El instante de ingreso del lote no se puede modificar».

La migración inventory0006 añade una protección persistente en SQLite y PostgreSQL. Un trigger rechaza cualquier UPDATE que cambie received_at. Guardar el mismo valor continúa permitido, así como descontar existencias sin modificar la fecha. La validación del modelo ofrece un error de dominio y la base cubre actualizaciones masivas y SQL que omiten save.

Se ensayaron reversión y reaplicación de la migración en PostgreSQL con lotes existentes, conservando todas sus columnas. En una copia nueva de la base original SQLite se aplicaron las migraciones pendientes de catálogo0003–0007 e inventory0006 y se cotejaron columnas comerciales, relaciones, claves e integridad. La base operativa sigue pendiente de migración.

## Escenario y resultados esperados

El fixture crea cinco lotes con UUID conocidos y tiempos controlados al crearlos. El orden de inserción es distinto del orden FEFO. Los lotes válidos tienen dos unidades cada uno. El lote vencido tiene cinco.

| Orden esperado | Lote | Condición |
|---|---|---|
| 1 | Z-INGRESO-ANTIGUO, UUID40 | Vence en30 días, ingresó hace dos días |
| 2 | Z-UUID-MENOR, UUID20 | Vence en30 días, ingresó hace un día |
| 3 | A-UUID-MAYOR, UUID30 | Mismo vencimiento e ingreso que UUID20 |
| 4 | A-TARDE, UUID50 | Vence en60 días, ingresó hace tres días |
| Excluido | VENCIDO, UUID10 | Vence hoy, ingresó hace cuatro días |

Después de vender3,2 y3 unidades, los saldos de los cuatro lotes vigentes deben ser [0,1,2,2], [0,0,1,2] y [0,0,0,0]. El lote vencido mantiene5. Cada venta y reenvío coteja todos los campos de los lotes para comprobar que solo cambian las cantidades disponibles. PostgreSQL repite los dos primeros descuentos y confirma el último mediante dos peticiones simultáneas con idéntica clave y borrador.

La prueba de concurrencia observa el bloqueo real entre conexiones. En el caso verificado ambas peticiones devuelven el mismo UUID de venta, existe una sola venta para el borrador y no se descuenta nuevamente el lote.

La asignación de cada venta a sus lotes puede reconstruirse en este ensayo por las instantáneas antes/después. El modelo de venta no conserva una entidad de asignación venta→lote. Esta brecha previamente documentada para retiros sanitarios sigue abierta y requiere su propio criterio, diseño y migración.

## Reproducción

```powershell
$python = 'r1-pmv/.venv/Scripts/python.exe'
$support = 'auditoria_por_etapas/resultados/soporte'
& $python -X utf8 "$support/audit03y_browser_run.py" ad-fefo
& $python -X utf8 "$support/audit03ad_pg.py"
& $python -X utf8 "$support/audit03ad_migrations.py"
$env:AUDIT03K_DEFAULT_COOKIES = '1'
& $python -X utf8 "$support/audit03k_run.py" tests catalog inventory sales cash identity
Remove-Item Env:AUDIT03K_DEFAULT_COOKIES
```

**Cursor05-D / INV01a-CA01–03 y PROP-03-RET-T06.** Completar la frontera de recepción contra desactivación de producto o categoría entre selección y confirmación. Reutilizar las evidencias previas pertinentes de03 para evitar repeticiones y verificar los órdenes concurrentes que falten, con saldo y costo íntegros. Mantener la decisión RN-01, la recepción multiproducto indivisible y la trazabilidad venta→lote para retiros en sus tramos.

## Evidencia final

24/24 comprobaciones de Chrome y346/346 métodos de regresión. PostgreSQL aprobó tres casos de migración/protección, FEFO y reenvío simultáneo. El caso concurrente observó un bloqueo real. El cotejo visual final muestra cinco unidades físicas vencidas, cero vigentes y «Sin stock vendible». [Navegador y saldos por venta](../evidencias/03-AD-ad-fefo-20261111T172528211721Z-2dbcafee/browser.json) · [Inventario final](../evidencias/03-AD-ad-fefo-20261111T172528211721Z-2dbcafee/inventario-final.png) · [PostgreSQL](../evidencias/03-AD-postgresql-20261111T172429108245Z.json) · [Migración en copia SQLite](../evidencias/03-AD-migrations-20261111T172507444169Z/result.json) · [Regresión](../evidencias/03-K-tests-20261111T172343659488Z/result.json).

[Defecto de fecha reproducido](../evidencias/03-K-tests-20261111T172130433685Z/tests.txt). Los primeros dos recorridos de navegador terminaron después de comprobar los tres cobros, por selectores ambiguos o demasiado restrictivos al consultar inventario. Se corrigieron los selectores y el recorrido completo pasó. Las corridas previas se conservaron. La base original mantuvo SHA256 4406ecd5babab34f0bb264e82c134eb21563494f9faf50e462d50c30c9d2ea95. Los servicios y puertos de prueba quedaron cerrados.

La protección persistente requiere inventory0006. Se ensayó en los dos motores soportados, SQLite y PostgreSQL. No reescribe las fechas antiguas. La creación de fixtures utilizó tiempos controlados antes de guardar cada lote. Se preservan las fechas reales de los datos existentes.
