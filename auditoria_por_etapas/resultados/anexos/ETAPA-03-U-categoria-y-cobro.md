# 03-U · Reclasificación, suspensión de categoría y cobro multiproducto

10/11/2026, America/Lima. Se leyó completo PROTOCOLO_COMUN y se retomó el cursor de 03-T. El árbol Git ya tenía cambios preexistentes y se conservaron. XLSX ausente, sin abrir ni reconstruir. El [inventario de 9 HU/27 CA y cuatro suplementarios](ETAPA-03-inventario.md) mantiene la clasificación del tramo; este corte no aprueba otras etapas.

## Inventario y trazabilidad previa

Fuentes: 01/14 selección R1, 02 diseño/roles, 03 matriz histórica, 07 RN03/25/27/28/29/30, 08 PROD04/CA05 y VEN01b/01c, 08:902–905 J-CA1..4 de PROP-E00-HU-02, 09 backlog, 16 tareas S1-VEN01C-TXDB/IDEM, 21 alcance y CONTROL_SPRINTS. Las etiquetas históricas no prueban funcionamiento. Edición de producto y estado de categoría son posteriores a R1; la confirmación de estado de categoría fue aceptada en03-J. El XLSX solo conserva su inventario histórico; no se usa como fuente nueva.

| ID/fuente | Actor, ruta, acción y salida | Estado en el sublote |
|---|---|---|
| PROD04/CA05, 08:245 | ADMIN Productos→Editar `/productos/<uuid>/editar/`; P pasa de categoría activa A a activa B | CUMPLE muestra: P conserva identidad, campos comerciales, lotes y venta histórica. P→B terminó **antes** de la competencia en PG. |
| PROP-E00-HU-02/J-CA1..4, 08:902–905 | ADMIN Categorías→Desactivar, pantalla de impacto, confirmación y versión; luego reactivar | CUMPLE muestras: suspensión excluye venta sin borrar producto o borrador; reactivación permite venta con stock vigente. No es edición/eliminación de categoría. |
| VEN01b/CA05 y VEN01c/CA03–05; RN25/27/29/30 | VENDEDOR propietario, borrador P×2/Q×1, `/ventas/cobrar/`, efectivo y resumen, aviso/reintento/constancia | CUMPLE muestras de frontera: un rechazo íntegro o una venta, según orden. No cierra auditoría integral de venta/caja. |
| RN29, 07:333 | ALMACENERO consulta catálogo; VENDEDOR venta; GET/POST directos de gestión de categoría denegados | CUMPLE navegador con CSRF y 403, sin cambios. |
| AUD03U-CATEGORIA-VENTA01 | Competencia de suspensión B y cobro después de P→B | **2/2 PG**; no se ejecutaron tres operaciones simultáneas. |

Campos y salidas: categoría destino elegida entre activas; nombre, código, precio y mínimo permanecen sin cambios. Pantalla de impacto distingue confirmar/cancelar y versión de categoría. Cobro presenta dos líneas, precio, cantidad, total, efectivo y aviso «El producto … ya no está disponible … Quítalo de la venta en preparación para continuar». El control de versión y límites de campos se estudiaron en J/D, no se reejecutan aquí en todas sus fronteras. El subtotal incluye IGV conforme RN27; este corte no valida legislación ni cálculo completo de impuesto.

## PostgreSQL: ambos órdenes tras reclasificar

PostgreSQL18.4 READ COMMITTED, clúster/base nuevos, cuentas ficticias y sin `.env`. Dos conexiones; Django **test Client** con CSRF usa vista y servicio reales, sin socket HTTP. P fue reclasificado A→B antes de la carrera; se mantuvo abierta la transacción ganadora hasta observar espera mediante `pg_blocking_pids`. P×2/Q×1 en borrador, venta previa ficticia P×1 y turno abierto. No afirmar que reclasificación, suspensión y cobro compitieron simultáneamente.

| Orden observado | Efecto y conservación |
|---|---|
| Suspensión gana; cobro espera | B queda inactiva. POST responde200 y rechaza cobro; conserva lote, borrador, turno, venta previa y correlativo. Al reactivar B por servicio y reintentar se confirma una venta de S/23, P2/Q1. |
| Cobro gana; suspensión espera | POST responde302; se confirma una venta de S/23, luego B queda inactiva y una venta posterior de P se rechaza. |

**2/2 escenarios**, esperas reales observadas, stocks finales P7/Q9 (P tenía una unidad descontada en fixture anterior), identidad e histórico preservados. Repetir la clave devuelve la misma venta **a nivel de servicio**, no se afirma replay HTTP. El correlativo observado queda2→2 en rechazo y2→3 tras reintento; efectivo50 y vuelto27 en esa venta. Las instantáneas están en [evidencia PG](../evidencias/03-U-postgresql-20261111T034421069411Z.json). No se hizo una venta independiente de Q en esta prueba; sí se verificó stock Q. La suspensión antes de reclasificar se probó anteriormente en03-N por servicio, no en el nuevo recorrido web.

## Navegador secuencial entre roles

Chrome157 headless y Playwright, servidor solo local con desafío HMAC, cuentas ficticias sin `.env`, base nueva `datos/etapa03k-20261111T034440987277Z-46258ffc/audit.sqlite3`. **35/35 comprobaciones**: ADMIN reclasifica P y suspende B tras revisar impacto; ALMACENERO ve P con categoría desactivada/20 unidades y Q disponible/6; los dos roles sin gestión reciben403 en GET/POST de categoría con CSRF. VENDEDOR recibe el rechazo de cobro sin cambios comerciales, ADMIN reactiva B y VENDEDOR confirma expresamente una sola venta de S/25,50, P2/Q1; quedan18/5. Constancia histórica preservada. El importe difiere de PG por precios de las fixtures, no es una discrepancia funcional.

[Navegador](../evidencias/03-U-browser-reclassify-20261111T034440987277Z-46258ffc/browser.json) · [Instantáneas](../evidencias/03-U-browser-reclassify-20261111T034440987277Z-46258ffc/checkpoints.json) · [Rechazo inspeccionado](../evidencias/03-U-browser-reclassify-20261111T034440987277Z-46258ffc/01-rechazo.png) · [Cierre](../evidencias/03-U-browser-reclassify-20261111T034440987277Z-46258ffc/result.json). El navegador fue secuencial, no demuestra concurrencia. No se probó lector de pantalla real ni todas las dimensiones de accesibilidad.

No se halló un defecto inequívoco nuevo y no se cambió código funcional. No se repitió la suite de332 métodos de03-T: este corte añadió solo soportes de auditoría y no cambió aplicación; aquella regresión conserva su fecha y alcance. Servidores y clúster finales detenidos, puertos cerrados y bases protegidas y original con hashes intactos. No se restauró, limpió ni migró la base original.

## Reproducción, propuestas y límites

Ejecutar secuencialmente desde la raíz, entornos nuevos; no borrar ni resetear las bases existentes:

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03u_pg.py'
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03u_browser_run.py' reclassify
```

AUD03U-CATEGORIA-VENTA01 es tarea técnica verificada en dos órdenes, no una HU nueva. Vincular evidencia a PROD04/CA05, PROP-E00-HU-02 y VEN01c/CA03–05 sin cambiar estados históricos de backlog/sprint.

**Decisión de alcance pendiente, no defecto:** la categoría no se muestra en el resumen ni forma parte de su firma de estado. Alternativa A: conservar la política actual (reclasificación activa no interrumpe; suspensión sí bloquea), respaldada por muestras03-T/U. Alternativa B: mostrar categoría y exigir revisión tras reclasificar; requiere criterios aceptados y pruebas de cambios simultáneos y borradores. No se infiere B del criterio de reclasificación.

**Cursor 03-V / AUD03V-TRIPLE-CATEGORIA01:** en PostgreSQL nuevo sincronizar tres operaciones reales en conexiones independientes: ADMIN1 reclasifica P A→B, ADMIN2 suspende B y VENDEDOR confirma borrador P×2/Q×1. Medir orden de locks y esperas con `pg_blocking_pids`, timeout y semántica de operaciones; verificar ganador o rechazo, ausencia de efectos parciales, histórico y correlativo, reactivación/reintento idempotente. Registrar qué intercalaciones se fuerzan. **NO EJECUTADO en U**; no inferir ausencia de deadlocks de dos carreras separadas. La reproducción secuencial por roles ya está en U.

23/27 CA base siguen CUMPLE en sus muestras,4 CAT03/04 PREVISTO/FUTURO y cuatro suplementarios con evidencia anterior. Seguridad de firma no autenticada→15, costo histórico→11, recepción/retiros PROP-03-RET-T01..T11→05–08/11/12/14–16 y despliegue real pendientes. No declarar coincidencia total.
