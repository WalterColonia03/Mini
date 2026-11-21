# 03-L · Suspensión de categoría durante cobro y entrada

10/11/2026, 20:34–20:35, America/Lima. Subconjunto de etapa 03 completado con cuatro carreras PostgreSQL y veinte comprobaciones en Chrome. Se leyó completo el protocolo y se retomó el cursor K9. Se conservaron los cambios preexistentes del repositorio. Este corte añade soportes y evidencia. Los servicios existentes cumplieron las cuatro carreras.

## Inventario del tramo ejecutado

| Fuente, clasificación y actor | Ruta, acción, campos o salida | Esperado y cobertura |
|---|---|---|
| PROP-E00-HU-02, J-CA1–4 aceptados en 08:898–905, agregado QA08:876. ADMIN | Categorías → Desactivar → Confirmar desactivación. GET de confirmación y POST `/productos/categorias/<id>/estado/`. Estado objetivo, versión y confirmación. Resumen de productos, borradores y existencias | Conservar los datos comerciales y excluir operaciones posteriores. Servidor `toggle_category_status`. CUMPLE en las muestras. |
| QA08:874, HU-PROD-05, frontera VEN-01c. VENDEDOR | Preparar venta → Cobrar → Confirmar cobro, `/ventas/cobrar/`. Efectivo 20,00, descuento cero, borrador de dos unidades de S/ 8,50. Alerta, resumen, constancia | Si la categoría gana la suspensión, rechazar el cobro sin descontar. Si gana el cobro, confirmar una sola venta y aplicar la suspensión a la operación posterior. |
| QA08:876, frontera INV-01b. ALMACENERO | Entrada de mercadería, `/inventario/entrada/`. Producto, proveedor opcional, lote, cantidad 5, costo 4,00 y fecha futura. Confirmar entrada | Revalidar la categoría. Conservar stock y costo ante rechazo. La entrada que ganó antes de suspender debe conservar su lote, proveedor y responsable. |
| HU-PROD-01 y consulta VEN-01b. ALMACENERO y VENDEDOR | Catálogo de productos y búsqueda en mostrador | Catálogo informa «Categoría desactivada» y conserva existencias físicas. Búsqueda excluye el producto. |
| RN-01/03/19/25/27/29/30. Tareas QA-FIX-CAT-01 y S1-VEN01C-TXDB/MAN | Autorización, estado comercial, vencimiento, transacción y datos del borrador | Cobertura acotada a categoría contra cobro/entrada. Las tareas históricas de 14/16/CONTROL_SPRINTS aportan trazabilidad. |

**Conflicto de alcance vigente.** RN-01 exige reposición aprobada para entradas posteriores. El servicio de entrada directa permite registrar lotes sin recibir una referencia de aprobación. Su selección comercial continúa pendiente en etapa 06. Esta corrida comprueba su respuesta al estado de la categoría.

## Resultados de servidor y persistencia

PostgreSQL 18.4, aislamiento read committed, clúster temporal propio, conexión local, cuentas ficticias y migraciones aplicadas únicamente a la base nueva. Dos conexiones ejecutaron los servicios reales. Se retuvo la transacción ganadora y una tercera conexión observó `pg_blocking_pids` y espera `transactionid` antes de liberarla. La consulta bloqueada incluía la categoría en los cuatro casos.

| Caso | Resultado |
|---|---|
| PG-L-venta-primero-suspension | Suspensión confirma. Cobro espera y rechaza con «Un producto o precio cambió. Revisa la venta antes de confirmar el cobro.». Stock 20, borrador ACTIVE de dos unidades y caja OPEN de 50,00. Sin venta ni correlativo nuevo. |
| PG-L-venta-primero-venta | Venta confirma primero, S/ 17,00, efectivo S/ 20,00 y vuelto S/ 3,00. Quedan 18 unidades, una venta y un detalle. La suspensión esperó, confirmó después y el intento de agregar el producto fue rechazado. |
| PG-L-entrada-primero-suspension | Entrada espera y rechaza. Conserva 20 unidades a costo promedio 2,5000, lote inicial, proveedor y responsable. |
| PG-L-entrada-primero-entrada | Entrada añade un lote de cinco unidades a costo 4,0000. Quedan 25 a promedio 2,8000, con proveedor y almacenero de recepción correctos. La categoría se desactiva después. Otra entrada con lote diferente rechaza y conserva el estado. |

**4/4 CUMPLE en las muestras.** Se cotejaron también ventas, detalles, borradores, caja, correlativo, bajas y ajustes en los escenarios de entrada. Los datos ficticios iniciales de cada escenario se prepararon mediante servicios. Entre los escenarios de venta se descartó el borrador rechazado como preparación explícita del siguiente caso. [Resultados y estados completos](../evidencias/03-L-postgresql-20261111T013408499660Z.json).

## Navegador y mensajes

Chrome 157.0.8103.39 con tres contextos autenticados por rol. Secuencia por menús y servidor HTTP aislado en SQLite. La ficha inicia con 19 unidades, una venta histórica de una unidad y un borrador de dos. Esta muestra usa la fixture de K, distinta de las 20 unidades de los casos PostgreSQL.

El vendedor y el almacenero abrieron sus formularios antes de la suspensión. El ADMIN revisó el impacto y confirmó. El cobro mostró «El producto «AUD03 Bebida de prueba» ya no está disponible para la venta. Quítalo de la venta en preparación para continuar.». La entrada mostró «Seleccione un producto activo que ya tenga carga inicial.». Ambos rechazos conservaron la instantánea comercial previa. El almacenero vio 19 unidades con la categoría desactivada y la búsqueda de venta excluyó el producto.

Después de una reactivación mediante confirmación, el vendedor cobró las dos unidades. Quedaron 17 unidades y dos ventas contando la anterior. Una suspensión posterior conservó la nueva constancia y las tablas cotejadas. **20/20 comprobaciones**, incluida la lectura de mensajes y persistencia. [Casos](../evidencias/03-K-frontier-20261111T013518362010Z/browser.json) · [Instantáneas](../evidencias/03-K-frontier-20261111T013518362010Z/checkpoints.json) · [Confirmación](../evidencias/03-K-frontier-20261111T013518362010Z/01-impacto.png) · [Cobro rechazado](../evidencias/03-K-frontier-20261111T013518362010Z/02-cobro-rechazado.png) · [Entrada rechazada](../evidencias/03-K-frontier-20261111T013518362010Z/03-entrada-rechazada.png).

El JSON de navegador conserva una etiqueta de modo heredada que menciona emulación de teclado. La ejecución realizó los flujos de formularios descritos. El soporte siguiente corrige esa descripción. El nombre de evidencia K-frontier refleja la reutilización del runner aislado, mientras su cobertura corresponde a este corte L.

## Reproducción, límites y cursor

Ejecutar desde la raíz secuencialmente. Cada comando crea su propio entorno, coteja archivos protegidos y detiene su servidor.

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03l_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k_run.py' frontier
```

Los dos resultados informan cierre del puerto y conservación de hashes de las bases presentes. El XLSX estaba ausente al comienzo de ambos ensayos. No se modificó código funcional ni se repitió la suite completa. Las pruebas de rendimiento, múltiples categorías en una sola venta, cambios de categoría del producto mientras se cobra y recuperación de caída del proceso siguen pendientes. Los conteos de impacto son informativos y pueden variar mientras se abre la confirmación. Las etapas 06/11/14/15 mantienen sus auditorías integrales pendientes.

**Siguiente cursor 03-M / HU-PROD-05/CA01.** Repetir las cuatro carreras sustituyendo la suspensión de categoría por desactivar únicamente el producto, con categoría siempre activa. Verificar ambos órdenes contra cobro y entrada. En navegador, abrir los formularios con ficha activa y después deshabilitar desde Productos. Exigir que la ficha contigua de la misma categoría conserve disponibilidad, stock e históricos. Clasificar aparte las carreras de reclasificación del producto y cobro de varias categorías.
