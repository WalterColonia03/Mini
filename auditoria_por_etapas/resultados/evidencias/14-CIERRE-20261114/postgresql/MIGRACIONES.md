# Diagnóstico previo de migraciones monetarias · etapa 14

**4/4 comprobaciones aprobadas**, primera pasada, ejecución adicional del 14/11/2026, 10:31:29–10:31:33 Lima. [Resultados completos](migraciones-legacy/results.json), [runner exacto ejecutado](migraciones-legacy/runner-ejecutado.py). Se usó `MigrationExecutor` real y modelos históricos sobre **SQLite `:memory:`**, independiente de la corrida PostgreSQL de 19 casos. La base fue creada para esta prueba con datos ficticios y desaparece al cerrar la conexión. No se consultaron, corrigieron ni migraron datos operativos.

El punto de partida fue el esquema anterior a `cash/0004_integration_money_limits` y `sales/0007_integration_money_limits`, con `cash/0003_cashshiftclose` y `sales/0006_sale_lot_traceability`. Se insertaron fixtures mediante sus modelos históricos, evitando las restricciones nuevas que precisamente se evalúan. Cada rechazo compara todos los campos de las filas de cierre/turno o venta/línea/borrador antes y después y consulta `django_migrations`.

| Caso | Entrada y resultado observado |
|---|---|
| cash-invalid-rejected | Cierre con contado −1.00, esperado 100.00, diferencia 0.00. `cash0004` lanza `RuntimeError`: un cierre incompatible. Todos los valores permanecen iguales y la migración no figura aplicada. |
| cash-valid-applied | El arnés cambia explícitamente solo la fixture a contado 100.00 y diferencia 0.00. `cash0004` aplica sus restricciones sin alterar ningún campo original del cierre ni del turno. |
| sales-invalid-rejected | Línea con cantidad 1.000.000 y venta con total −1.00. `sales0007` lanza `RuntimeError`: una línea y una venta fuera de capacidad. Los valores permanecen iguales y la migración no figura aplicada. |
| sales-valid-applied | El arnés cambia explícitamente solo las fixtures a cantidad 999.999 y total/base/efectivo 10.000.000.00. `sales0007` aplica conservando todos los campos originales; no recorta la venta histórica al límite menor de una operación nueva. |

Las correcciones entre casos son preparación controlada de datos ficticios, no un saneamiento automático ejecutado por las migraciones. Los mensajes conservados distinguen diagnóstico y bloqueo de la decisión de regularizar. La comprobación de venta histórica de 10.000.000.00 acredita compatibilidad del almacenamiento al endurecer las restricciones, no autorización para registrar nuevas ventas por encima del límite por operación.

Build de ejecución antes/después, estable: `ec783ac6febb289f70efbda37d7e742ad1305088982ad1e4e6f6694549cdd172`. Versión 08 ejecutada: `32270f6b6f32d8aec7c3f4883f20eef2229e3bb26da8f0c0369fd047e3f8e700`, [copia conservada](../08-ejecutado.md). Es evidencia nueva de las precondiciones de DEC-11-TOPE-EFECTIVO-FORM, complementaria a PG14-12/13; no se hereda como prueba de producción ni completa la etapa 15.

Reproducción desde la raíz del repositorio, usando una carpeta de salida que aún no exista:

```powershell
& ./r1-pmv/.venv/Scripts/python.exe auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/postgresql/diagnosticar_migraciones.py <directorio-de-evidencia-nuevo>
```

El arnés fuerza SQLite en memoria antes de abrir conexiones, deshabilita la lectura de `.env`, no recibe una DSN externa y conserva una copia exacta de su código y las huellas de fuentes en cada corrida. Las condiciones inválidas de cada módulo se probaron juntas: esta prueba no afirma haber aislado por separado cada rama del diagnóstico. Los seis rechazos SQL en PostgreSQL se encuentran en [PG14-12](INFORME.md). Cursor de este sublote: diagnóstico aislado de cash0004/sales0007 completado; no queda un caso pendiente dentro de esta matriz.
