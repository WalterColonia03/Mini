# 03-AE / 05-D · Carga inicial frente a desactivación

11/11/2026, America/Lima. Sublote de frontera catálogo–inventario completado en las muestras descritas. Protocolo común leído completo. No se cambió código funcional ni se aplicaron migraciones sobre la base operativa.

## Inventario y trazabilidad previa

Se reutiliza el inventario por criterio de [03-AB](ETAPA-03-AB-recepcion.md) y se añade el [inventario previo del ensayo](../evidencias/03-AE-ae-initial-20261111T173009717921Z-b0e29f78/inventory-before.json). La nueva cobertura corresponde a HU-INV-01a/CA01–03, frontera HU-PROD-05 y HU-CAT-01 y muestra parcial PROP-03-RET-T06. Las reglas de disponibilidad son las del catálogo vigente y las validaciones de carga inicial; ninguna propuesta de retiro sanitario se convierte en requisito aprobado mediante esta prueba.

| Elemento | Clasificación y comprobación |
|---|---|
| Existencias iniciales, GET/POST `/inventario/carga-inicial/` | Actual, frontera05. ALMACENERO selecciona producto, proveedor opcional, número de lote, cantidad UND, costo y vencimiento. Se envía un formulario abierto antes de desactivar. |
| Productos, deshabilitar/habilitar | Actual03, ADMIN. Se modifica únicamente la disponibilidad del producto A. |
| Categorías, confirmación de estado | Actual03, ADMIN. Se suspende y reactiva Higiene mediante confirmación. La firma de estado se usa en el flujo existente. |
| `/ventas/`, consulta de producto | Actual, consulta autorizada VENDEDOR. Producto afectado ausente durante desactivación y visible con tres unidades después de reactivar y cargar. |
| Error de formulario | «Este producto ya tiene una carga inicial registrada o no está disponible.» El producto deja de estar entre las opciones; lote y cantidad se conservan. |
| Error de servicio | «El producto no está disponible para la carga inicial.» Rechazo transaccional cuando la desactivación gana. |
| Salidas | Instantáneas de producto, costo, cargas y lotes; capturas de rechazo; resultado de carreras con conexiones distintas y bloqueo real. |
| Recepción posterior | Evidencia anterior03-L/M: dos órdenes contra categoría/producto. Se referencia sin atribuirla como nueva ejecución. |

## Planificación → comportamiento y comportamiento → planificación

La condición de producto disponible se comprobó tanto en formulario antiguo como por POST directo y servicio concurrente. La persistencia se cotejó después de cada rechazo y luego de una reactivación. El comportamiento adicional observado es que una recepción que confirma primero permanece registrada cuando la desactivación confirma después; la desactivación impide ofrecer el producto, sin eliminar existencias.

**PROP-03AE-CA01, propuesta de precisión para INV-01a:** al confirmar, revalidar producto y categoría; si están inactivos, rechazar toda la carga sin crear lotes ni modificar costo. Si la carga confirma antes de la desactivación, conservar carga, lotes y costo. El ensayo acredita este comportamiento; la redacción suplementaria queda propuesta, sin inventar una HU nueva ni aprobar un proceso de cuarentena.

**AUD03AE-TEST01, tarea de pruebas realizada:** conservar dos recorridos con roles separados y cuatro intercalaciones de servicios reales en PostgreSQL. Soporte nuevo `audit03ae_browser.cjs`, `audit03ae_cases.py`, `audit03ae_pg.py`; extensión acotada de `audit03y_browser_run.py` para la acción `ae-initial` y sus instantáneas.

## Resultados

Chrome157.0.8103.39 automatizado, servidor Django y SQLite exclusivos: **29/29 comprobaciones**. ADMIN desactiva, ALMACENERO confirma la pantalla antigua, el POST vuelve con error y la instantánea comercial permanece idéntica. Reenvío directo del POST también rechaza. Tras reactivar y abrir una pantalla nueva se registra una sola carga, tres unidades y costo2.0000. Se repite para producto y categoría. Se inspeccionó visualmente la captura de rechazo por categoría.

[Comprobaciones Chrome](../evidencias/03-AE-ae-initial-20261111T173009717921Z-b0e29f78/browser.json) · [Rechazo de categoría](../evidencias/03-AE-ae-initial-20261111T173009717921Z-b0e29f78/category-rechazo.png) · [Persistencia final](../evidencias/03-AE-ae-initial-20261111T173009717921Z-b0e29f78/orm-final.json).

PostgreSQL18.4, READ COMMITTED, conexiones separadas: **4/4 casos**. Cada carrera comprobó bloqueo real y diez condiciones de resultado; no equivale a cuarenta escenarios independientes.

| Objetivo / orden de confirmación | Resultado observado |
|---|---|
| Producto desactivado antes de carga | Carga rechazada; cero cargas/lotes/saldo/costo nuevos. |
| Carga antes de desactivar producto | Una carga, dos lotes, tres unidades, costo3.0000; desactivación posterior conservó esos datos. |
| Categoría desactivada antes de carga | Carga rechazada; cero cargas/lotes/saldo/costo nuevos. |
| Carga antes de desactivar categoría | Una carga, dos lotes, tres unidades, costo3.0000; desactivación posterior conservó esos datos. |

Los dos lotes PostgreSQL aportan 2 unidades a2.00 y1 a5.00. En los cuatro casos se conservan los lotes y costo1.0000 del producto contiguo. La suspensión de categoría sí afecta la disponibilidad comercial de sus miembros. [Evidencia de las cuatro carreras](../evidencias/03-AE-postgresql-20261111T172913629199Z.json).

La entrada posterior ya tiene ambos órdenes contra categoría en [03-L](ETAPA-03-L-suspension-con-operaciones.md) y contra producto en [03-M](ETAPA-03-M-producto-con-operaciones.md), además de sus recorridos por navegador. Se evita confundir aquella reposición con la primera carga verificada aquí.

## Conservación, reproducción y límites

Ambos runners verificaron 164 archivos protegidos sin cambios y cierre de sus puertos. Original SHA256 `4406ecd5babab34f0bb264e82c134eb21563494f9faf50e462d50c30c9d2ea95`. El XLSX estaba ausente al comenzar; no se comprobó contenido inexistente. Estado final de Chrome: A yB activos, tres unidades cada uno, dos cargas y dos lotes; C sin carga, cero ventas, turno ficticio OPEN. Las cuentas y datos aislados se conservaron. [Cierre](../evidencias/03-AE-ae-initial-20261111T173009717921Z-b0e29f78/result.json).

Desde la raíz, ejecutar secuencialmente; cada comando crea un entorno nuevo:

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03ae_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03y_browser_run.py' ae-initial
```

No aparecieron defectos funcionales nuevos en estas muestras. No se repitieron los346 métodos de03-AD porque no hubo cambios de aplicación. Chrome fue secuencial; la simultaneidad se ejecutó en PostgreSQL. No se volvió a usar el teléfono ni se probó recuperación de caída. Despliegue de correcciones anteriores, clasificación de cinco fichas, RN-01, recepción multiproducto indivisible y trazabilidad persistente venta→lote mantienen sus pendientes. La desactivación comercial no demuestra un retiro sanitario integral. CAT03/04 siguen futuros; las otras etapas no se declaran terminadas.

## Cursor exacto

**05-E / AUD05E-CONCILIACION-INV01a**, consolidar los cinco criterios de carga inicial y PROP-03-RET-T01–T06/T11 contra evidencias03-AB–AE y03-L/M; separar muestras ejecutadas, recuperación ante respuesta incierta y decisiones de recepción multiproducto. Resolver documentalmente qué falta para cerrar05, manteniendo RN-01 en06 y trazabilidad/retirada en07–08/11–12/16. No repetir pruebas aprobadas sin un cambio o una brecha concreta.
