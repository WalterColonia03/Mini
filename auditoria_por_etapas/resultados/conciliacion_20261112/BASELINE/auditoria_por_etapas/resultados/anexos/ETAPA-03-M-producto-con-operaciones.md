# 03-M · Desactivar un producto durante cobro y entrada

10/11/2026, 20:38–20:43, America/Lima. Sublote completado: **4/4 carreras PostgreSQL y 27/27 comprobaciones Chrome**. Continuación de 03-L, protocolo completo aplicado. Se conservaron cambios preexistentes. Este corte modifica únicamente soportes de auditoría e informes; no requirió cambios en servicios de la aplicación.

## Inventario, clasificación y trazabilidad del tramo

| ID / fuente precisa | Rol, pantalla, ruta, acción y salida | Clasificación, comprobación y resultado |
|---|---|---|
| HU-PROD-05/CA01 y CA03, 08:249–256; backlog 09:69; CONTROL_SPRINTS:39 | ADMIN, Productos, POST `/productos/<id>/disponibilidad/`, botón Deshabilitar; ocultos CSRF y `is_active=false`. Mensaje ««AUD03 Bebida de prueba» ahora está inactivo.» y etiqueta Inactivo | Seleccionado e implementado. Estado explícito sin borrado. CUMPLE en servidor y Chrome; conservar categoría, existencias e históricos. Prioridad alta. |
| HU-PROD-05/CA02, 08:255; guía21:72 | Mismo ADMIN, botón Habilitar, `is_active=true`; posterior consulta y cobro del VENDEDOR | Seleccionado, precisado por usuario. CUMPLE muestra de categoría activa y stock vigente positivo. No repite aquí las variantes de vencimiento/cero stock de K. |
| HU-PROD-01, HU-PROD-05/CA01; VEN-01b/01c, 08:556–576 y agregado QA08:874 | ALMACENERO, Catálogo de productos: nombre/categoría/código/precio/stock/mínimo/estado. VENDEDOR, Preparar venta y `/ventas/cobrar/`; búsqueda `query`, efectivo `cash_received`, descuento, firma y clave de intento del formulario | Seleccionado. CUMPLE: producto inactivo excluido de búsqueda; borrador abierto rechaza cobro sin mutar datos. La ficha contigua sigue ofrecida. Prioridad alta. |
| Frontera INV-01b; `StockEntryProductForm` y `register_stock_entry` | ALMACENERO, `/inventario/entrada/`; producto con carga previa, proveedor opcional y filas lote/cantidad/costo/vencimiento. Confirmar entrada | Implementado adicional al texto de PROD05, que habla de suspender venta. Se comprueba bloqueo de entrada, sin presentarlo como auditoría integral de INV01b. CUMPLE comportamiento observado. Conflicto RN-01 sigue pendiente en06. |
| RN-03/14/19/25/27/28/29/30; tareas S1-VEN01C-PAY, TXDB y MAN en16 | Vencimiento, costo, transacción, dinero, históricos y rol. `toggle_product_availability` → `checkout_sale` / `register_stock_entry` | Pruebas técnicas de frontera de alta prioridad. CONTROL_SPRINTS es evidencia histórica de planificación, no sustituye la ejecución. Autorizaciones negativas y extremos ya tienen evidencia previa; no se repitieron en M. |

Inventario inverso: Deshabilitar/Habilitar y etiqueta se vinculan a PROD05; búsqueda y oferta al vendedor a PROD05/CA01–02; alerta de rechazo a revalidación VEN01c; constancias a RN-28; stock y alerta «Stock bajo» a PROD01/RN-06. El bloqueo adicional de entradas queda clasificado expresamente. No se incorpora una pantalla de confirmación al estado de producto: la decisión anterior de confirmación corresponde a categorías.

## Servidor: ambos órdenes de confirmación

PostgreSQL 18.4, read committed, clúster nuevo con marca propia, conexión localhost y sin cargar `.env`. Migraciones únicamente en esa base. Dos conexiones ejecutan los servicios reales; una tercera observa espera `transactionid` y `pg_blocking_pids` del ganador antes de liberarlo. En cada escenario la categoría permanece activa y con versión cero. Existe una segunda ficha vendible en la misma categoría, con cuatro unidades y costo 1,00.

| Caso reproducible | Esperado y observado |
|---|---|
| PG-M-venta-primero-suspension | Desactivar confirma; el cobro espera y rechaza con «Un producto o precio cambió. Revisa la venta antes de confirmar el cobro.». Conserva stock20, borrador ACTIVE de dos unidades, caja OPEN de50,00; sin venta ni correlativo nuevo. |
| PG-M-venta-primero-venta | Cobro confirma primero: dos unidades, total17,00, efectivo20,00, vuelto3,00, stock18. Desactivar espera y confirma después. Otra incorporación al borrador se rechaza. |
| PG-M-entrada-primero-suspension | Entrada espera y rechaza con «El producto no está disponible para registrar entradas.». Conserva stock20, promedio2,5000, lote inicial, proveedor y responsable. |
| PG-M-entrada-primero-entrada | Entrada confirma cinco unidades a costo4,0000: stock25 y promedio2,8000. Conserva proveedor y almacenero de recepción. Después se desactiva; otra entrada con lote diferente rechaza sin cambios. |

**4/4 CUMPLE en las muestras**. La ficha contigua conserva identidad, disponibilidad, stock y costo. Se cotejan también ventas, detalles, caja, correlativos, borradores, bajas y ajustes en el escenario correspondiente. Preparación explícita: descartar el borrador rechazado entre escenarios para abrir el siguiente. [Datos, bloqueos y aserciones](../evidencias/03-M-postgresql-20261111T013828523975Z.json).

## Navegador y persistencia

Chrome157.0.8103.39, tres contextos autenticados por menús ADMIN/ALMACENERO/VENDEDOR, servidor HTTP y SQLite nuevos con desafío HMAC. La ficha objetivo comienza con19 unidades, una venta histórica y borrador de dos unidades. La ficha contigua comienza con4 unidades y su propia venta histórica. Para preparar esta última se descartó el borrador de fixture, se cobró una unidad de control y se recreó el borrador objetivo; estos pasos son preparación, no parte del resultado auditado.

El vendedor abre Cobrar y el almacenero completa una entrada de5 unidades a costo4,00, lote M-CHROME, vencimiento31/01/2027 y proveedor vacío. ADMIN deshabilita solamente la ficha objetivo. Se observan:

- Mensaje de éxito y etiqueta Inactivo. La categoría sigue activa.
- Cobro antiguo rechazado: «El producto «AUD03 Bebida de prueba» ya no está disponible para la venta. Quítalo de la venta en preparación para continuar.»
- Entrada antigua rechazada: «Seleccione un producto activo que ya tenga carga inicial.». La captura conserva los campos del lote ingresado.
- Instantánea comercial sin cambios tras ambos rechazos. Catálogo del almacenero conserva19 unidades; búsqueda de venta excluye la ficha.
- Ficha contigua visible como Disponible,4 unidades con Stock bajo, y ofrecida al vendedor. Constancia histórica propia íntegra tras la suspensión final.
- Tras habilitar, el cobro de dos unidades termina:17 unidades y tres ventas totales contando las dos históricas de fixture. Una nueva desactivación conserva constancias, tablas comerciales y datos de la ficha salvo su estado.

**27/27 CUMPLE en la corrida final.** [Casos y solicitudes](../evidencias/03-K-frontier-product-20261111T014304366278Z/browser.json) · [Instantáneas](../evidencias/03-K-frontier-product-20261111T014304366278Z/checkpoints.json) · [Estado visible](../evidencias/03-K-frontier-product-20261111T014304366278Z/01-producto-inactivo.png) · [Cobro rechazado](../evidencias/03-K-frontier-product-20261111T014304366278Z/02-cobro-rechazado.png) · [Entrada rechazada](../evidencias/03-K-frontier-product-20261111T014304366278Z/03-entrada-rechazada.png). Capturas inspeccionadas. La carpeta K-frontier-product reutiliza el runner aislado de K; su cobertura corresponde a M.

Se retienen dos intentos iniciales, sin atribuir sus fallos al producto: `03-K-frontier-product-20261111T014121377023Z` tuvo24/25 por esperar «4» en una celda que decía «4 Stock bajo»; `...20261111T014226942611Z` tuvo26/27 por buscar el mensaje de éxito con role=alert, ausente en el contenedor general. La captura demuestra el mensaje visible. Se corrigieron ambos selectores y se repitió en otra base nueva. La ausencia de semántica de anuncio del mensaje general queda como observación de accesibilidad para15; no se afirma aprobación con lector de pantalla.

## Propuestas, reproducción y límites

**AUD03M-TEST01, tarea de pruebas implementada y verificada:** conservar estos cuatro casos de simultaneidad y el recorrido multirrol como regresión reproducible de PROD05. **PROP-03M-CA-ENT, criterio propuesto para06:** dado un producto inactivo al confirmar una entrada posterior, rechazar toda la entrada sin lotes ni cambios de costo; si la entrada confirmó antes de la desactivación, conservar su autoría y existencias. Comportamiento verificado aquí; incorporación al alcance de06 pendiente junto con RN-01, que exige reposición aprobada. No se crea una HU duplicada de catálogo.

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03m_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03k_run.py' frontier-product
```

Cada ejecución crea sus datos y detiene su servidor; todos los puertos de este corte quedaron cerrados. Se conservaron las bases preexistentes por hash. El XLSX estaba ausente al comenzar; conservar su ausencia no verifica su contenido. No se repitió la suite completa porque no cambió código funcional. Los bloqueos demostrados son de PostgreSQL; el recorrido Chrome/SQLite es secuencial.

Permanecen NO EJECUTADOS en este corte: nuevas carreras SQLite, reclasificación durante cobro, cobro de varias categorías, caída/recuperación, recepción integral de paquetes y retiros por lote. La desactivación comercial no implementa cuarentena ni trazabilidad venta→lote ni retirada del mercado. Las once pruebas propuestas de [recepción y retiros](ETAPA-03-recepcion-y-retiros-pendientes.md) conservan sus estados; no se certifica cumplimiento legal ni se cierran06/11/14/15/16. Balance base de etapa03 sin cambio:21 CUMPLE muestra y6 PREVISTO/FUTURO, además de los cuatro criterios suplementarios de categoría.

**Siguiente cursor exacto:03-N / HU-PROD-04/CA05, 08:245.** Categorías A y B activas, ficha con20 unidades vigentes, borrador de dos unidades y turno OPEN. Abrir edición ADMIN y cobro VENDEDOR. Reclasificar A→B con firma vigente y comprobar conservación de identidad, lotes y venta histórica; repetir con B desactivada antes del envío, exigiendo rechazo íntegro. En PostgreSQL sincronizar reclasificación y cobro en ambos órdenes, registrar bloqueo o error y saldos; luego suspensión de B frente a reclasificación hacia B. Estos casos siguen NO EJECUTADOS. Cobro con varias categorías y recepción/retiro completos quedan clasificados para sus etapas.
