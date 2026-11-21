# 03-AC / 05-B · Proveedor y fechas al confirmar recepción

11 de noviembre de2026, America/Lima. Se retomó el cursor05-B y se leyó completo el protocolo común. Este corte continúa la frontera entre catálogo, proveedor, carga inicial y entrada posterior.

## Inventario y trazabilidad

Fuentes: HU-INV-01a/CA02–03 y CA05 (08:323–326), HU-INV-01b (08:335–336), HU-PROV-04 (08:302–309), RN-03/19/29, inventario de campos03-AB y PROP-03-RET-T04/T06. La exclusión de proveedor inactivo también está implementada en los dos formularios y servicios de recepción. PROV04 habla de pedidos de reposición. La comprobación sobre entradas directas conserva la diferencia de alcance documentada en06 y DOC-03AB-01.

| Elemento | Requisito y clasificación | Ejecución |
|---|---|---|
| Proveedor opcional en carga inicial y entrada posterior | IMPLEMENTADO. Selector de proveedores activos, vacío significa sin proveedor | Formulario abierto, desactivación en otra sesión, rechazo del envío viejo, reactivación y nueva confirmación. |
| POST de carga/entrada | INV01a/CA03 y frontera INV01b. Revalidar y conservar estado ante rechazo | Comparación completa de productos, cargas y lotes, cantidades y costos antes/después. |
| Estado de proveedor | PROV04, ADMIN modifica. ALMACENERO y VENDEDOR carecen de esa acción | ADMIN desactiva/reactiva desde lista. Los otros roles intentan POST con token CSRF propio y reciben403. |
| Datos del proveedor ya cargados en memoria | Tarea técnica derivada de recepción vigente | Pruebas directas de proveedor desactivado, reactivado y eliminado después de obtener la instancia. |
| Recepción frente a desactivación simultánea | PROP-03-RET-T06. Mantener un orden consistente entre ambas operaciones | PostgreSQL, carga inicial y entrada posterior, dos órdenes por operación. |
| Vencimiento en Lima | INV01a/CA02 y RN-03 | Reloj fijado antes y después de medianoche local. El mismo vencimiento pasa de futuro a hoy y se rechaza sin residuos. |
| Límite anunciado de20 años | Validación adicional preexistente en formulario, modelo y servicio | Frontera exacta del aniversario, día siguiente, fin del año20, comienzo del año21 y cálculo de aniversario desde29 de febrero. |
| Fecha de ingreso | INV01a/CA05 y RN-19 | Petición de formulario con un valor de ingreso manipulado. La recepción conserva la fecha generada por el servidor. La edición directa por todas las vías y FEFO completo siguen pendientes. |

Las rutas probadas fueron `/inventario/carga-inicial/`, `/inventario/entrada/`, `/inventario/proveedores/` y la acción POST de estado del proveedor seleccionada desde la tabla. Se usaron ADMIN, ALMACENERO y VENDEDOR ficticios con sesiones separadas. El navegador verificó el desafío criptográfico del servidor aislado antes de iniciar sesión.

El formulario conserva producto, número de lote y cantidad después del rechazo. El proveedor inactivo desaparece de la selección. El aviso de campo pide una opción válida. La reactivación permite seleccionar de nuevo al proveedor y guardar una sola recepción. La confirmación persiste la referencia al proveedor. Una carga con proveedor vacío guarda una referencia nula conforme al campo opcional vigente.

## Hallazgos y correcciones

**H-03AC-01 · Prioridad alta, corregido.** Ambos servicios comprobaban `supplier.is_active` sobre la instancia recibida. Cuando esa instancia se había obtenido antes de una desactivación, la operación podía guardar existencias con el proveedor ya inactivo. La prueba previa reprodujo aceptación indebida en carga inicial y entrada posterior. Se añadió una consulta con bloqueo del registro actual dentro de la transacción. El servicio rechaza proveedores inactivos o eliminados y reconoce una reactivación aunque la instancia anterior siguiera marcada como inactiva.

El orden de bloqueos mantiene producto/categoría antes de proveedor en recepción. La desactivación modifica el proveedor y espera cuando una recepción ya posee su bloqueo. Si la desactivación se confirma primero, el receptor lee el estado inactivo al obtener el bloqueo y rechaza la carga completa. Si la recepción se confirma primero, sus lotes permanecen asociados al proveedor y la desactivación posterior no altera ese historial.

**H-03AC-02 · Prioridad media, corregido.** La validación anunciaba un máximo de20 años, pero comparaba exclusivamente el año. Con fecha base11/11/2026 aceptaba31/12/2046. La primera prueba de caracterización confirmó esa aceptación. La validación compartida ahora calcula el aniversario exacto, 11/11/2046 en ese ejemplo. Para el caso29/02/2080, cuyo aniversario cae en un año sin29 de febrero, se utiliza28/02/2100. Formulario, modelo y servicio usan el mismo cálculo. Esta interpretación alinea el límite con el mensaje existente.

## Pruebas y límites

La prueba de medianoche fija04:59:59 UTC y05:00:00 UTC del12/11/2026. En Lima corresponden al final del11 y al inicio del12. Un lote que vence el12 se admite en la primera situación y se rechaza en la segunda. La fecha de ingreso se comprobó contra el reloj del servidor.

Las cuatro carreras PostgreSQL usan conexiones independientes y observación de bloqueos reales. Cada orden coteja estado del proveedor, cabecera, lotes anteriores, lotes nuevos, saldo y costo. El proveedor inactivo conserva los lotes que se recibieron antes de la desactivación. La prueba no atribuye a desactivar un proveedor el efecto de retirar mercancía del mercado.

La primera corrida de navegador se interrumpió en el soporte después de reactivar el proveedor. Recargar la página de un POST rechazado volvió a enviar la solicitud y terminó en la constancia, por lo que el soporte dejó de encontrar el selector esperado. Se corrigió la navegación del ensayo para abrir un formulario nuevo mediante GET. La aceptación después de reactivar el proveedor corresponde a la regla vigente.

## Reproducción

```powershell
$python = 'r1-pmv/.venv/Scripts/python.exe'
$support = 'auditoria_por_etapas/resultados/soporte'
& $python -X utf8 "$support/audit03y_browser_run.py" ac-supplier
& $python -X utf8 "$support/audit03ac_pg.py"
$env:AUDIT03K_DEFAULT_COOKIES = '1'
& $python -X utf8 "$support/audit03k_run.py" tests catalog inventory sales cash identity
Remove-Item Env:AUDIT03K_DEFAULT_COOKIES
```

**Cursor05-C / HU-INV-01a-CA05 y RN-19.** Preparar lotes ficticios con vencimientos iguales y fechas de ingreso distintas, después empate completo con UUID diferentes. Verificar las vías que pueden editar el instante de ingreso y la selección FEFO real en una salida autorizada, conservando las referencias históricas. Auditar únicamente esa frontera de venta y mantener las etapas11/12 pendientes. DOC-03AB-01, recepción multiproducto indivisible, cuarentena y retiros mantienen su traspaso.

## Evidencia y conservación

29/29 comprobaciones en Chrome, cuatro carreras PostgreSQL y343/343 métodos de regresión. Las bases operativas y los ensayos anteriores conservaron SHA256. Servicios de ensayo detenidos y puertos cerrados. [Chrome](../evidencias/03-AC-ac-supplier-20261111T171405144997Z-87619aa4/browser.json) · [Rechazo visible](../evidencias/03-AC-ac-supplier-20261111T171405144997Z-87619aa4/inventory-load-link-rechazo.png) · [Fecha máxima](../evidencias/03-AC-ac-supplier-20261111T171405144997Z-87619aa4/fecha-limite.png) · [PostgreSQL](../evidencias/03-AC-postgresql-20261111T171037164135Z.json) · [Regresión final](../evidencias/03-K-tests-20261111T171347502254Z/result.json).

[Defecto de proveedor reproducido](../evidencias/03-K-tests-20261111T170954823785Z/tests.txt) · [Caracterización del límite anual previo y primer conjunto de regresión](../evidencias/03-K-tests-20261111T171212923892Z/tests.txt) · [Primer recorrido de navegador interrumpido](../evidencias/03-AC-ac-supplier-20261111T171131139219Z-23558f23/browser.json).

La captura conserva el mensaje genérico de selección inválida. En su lugar de la lista, el navegador muestra la opción vacía «Sin proveedor asignado» porque el proveedor inactivo desapareció. El sistema rechaza ese envío antiguo. Como mejora pendiente de interfaz en04, conservar explícitamente la identificación del proveedor rechazado para que un segundo envío implique revisar la elección del proveedor opcional.
