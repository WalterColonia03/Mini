# 03-V · Reclasificación, suspensión y cobro simultáneos

10/11/2026, America/Lima. Se leyó completo PROTOCOLO_COMUN y se retomó el cursor de 03-U. El repositorio ya tenía cambios preexistentes, conservados. El XLSX estaba ausente y no se abrió ni recreó; su procedencia histórica está inventariada en 00/03. No se presenta como auditada integralmente venta, inventario ni seguridad.

## Alcance y trazabilidad previa

El [inventario completo de 9 HU/27 CA y cuatro suplementarios](ETAPA-03-inventario.md) mantiene la clasificación del tramo. Se contrastaron 01/14 release y sprint, 02 diseño/roles, 03 matriz, 07 RN03/25/27/28/29/30, 08 PROD04/CA05, VEN01b/01c y J-CA1..4 (08:902–905), 09 backlog, 16 S1-VEN01C-TXDB/IDEM, 21 alcance y CONTROL_SPRINTS. Las etiquetas históricas no prueban ejecución. PROD04 y estado de categoría son adicionales al R1 original; J-CA1..4 fueron aceptados en03-J. Categorías distintas de enlatados admitidas bajo DOC03-01 para UND y vencimiento obligatorio.

| Fuente y elemento | Actor, ruta/acción y efecto examinado | Estado de muestra |
|---|---|---|
| PROD04/CA05, 08:245 | ADMIN edita producto P, categoría activa A→B; nombre, código, precio, mínimo e identidad conservados | CUMPLE en las intercalaciones en que edición gana; rechaza destino inactivo si suspensión gana. |
| PROP-E00-HU-02/J-CA2, 08:903 | ADMIN suspende B con estado objetivo/versión; preserva productos, lotes, borrador e históricos | CUMPLE muestra de servicio; interfaz y permisos se ejercitaron separadamente en03-U. |
| VEN01b/01c y RN25/27/29/30 | VENDEDOR dueño intenta cobrar P×2/Q×1, turno abierto, precio, stock y total | CUMPLE en muestras de integridad descritas; no implica revisión integral de cobro o de normativa. |
| AUD03V-TRIPLE-CATEGORIA01 | Tres conexiones PostgreSQL, edición, suspensión y cobro simultáneos | 3/3 intercalaciones controladas, no prueba exhaustiva. |

Categoría destino activa requerida; P y Q tienen lotes vigentes, precios S/8,50 y S/6,00, total S/23 para P2/Q1. Existe venta histórica ficticia P1. Formatos y límites de nombre, código, precio y mínimo fueron inventariados previamente en C/D/I; no se reejecutan aquí todas sus fronteras. La interfaz de confirmar/cancelar categoría, consultas de ALMACENERO y rechazos HTTP de roles se probaron en03-U, no en este corte.

## PostgreSQL: tres intercalaciones reales

PostgreSQL18.4 READ COMMITTED, clúster y base nuevos exclusivos, cuentas ficticias y sin `.env`. Tres conexiones ejecutan los servicios reales `update_product`, `toggle_category_status` y `checkout_sale`; el soporte mantiene abierta la transacción ganadora para sincronizar orden y comprueba esperas con `pg_blocking_pids` y timeout. No se agregaron bloqueos sintéticos de filas. No se invocó vista web ni navegador en V; el resultado del replay es **de servicio**, no demostración de respuesta HTTP.

| Intercalación forzada | Espera y resultado observado |
|---|---|
| Edición primero | Suspensión y cobro esperan edición; P pasa a B, B se suspende y cobro rechaza «Un producto o precio cambió. Revisa la venta antes de confirmar el cobro.» sin venta, stock, borrador ni correlativo parcialmente modificados. Tras reactivar B, reintento confirma una venta y replay devuelve la misma. |
| Suspensión primero | Edición espera B y rechaza «Seleccione una categoría activa.»; cobro espera edición. P permanece en A activa y la venta P2/Q1 confirma S/23. |
| Cobro primero | Edición espera el producto bloqueado por el cobro; suspensión de B confirma mientras la transacción de cobro se mantiene retenida. El cobro confirma S/23 y la edición rechaza B inactiva. No se afirma que la suspensión esperara en este orden. |

**3/3 casos** con comprobaciones de conexiones distintas, esperas, ausencia de error de base, conservación de histórico y turno, stock, correlativo en rechazo, y una sola venta final; replay idempotente a nivel de servicio. El efectivo de prueba es50 y vuelto27; el stock final es P7/Q9 tras venta histórica previa P1 y venta nueva P2/Q1. Instantáneas antes, después y tras reintento están en [evidencia PostgreSQL](../evidencias/03-V-postgresql-20261111T034849421028Z.json). No se certifican todas las intercalaciones ni se reevalúa íntegramente FEFO, asignación de lote, caja o permisos.

Navegador **NO EJECUTADO en V**: V añade solo concurrencia de servicios; el recorrido secuencial completo ADMIN/ALMACENERO/VENDEDOR y permisos GET/POST permanece en [03-U:35/35](../evidencias/03-U-browser-reclassify-20261111T034440987277Z-46258ffc/browser.json), no se cuenta como ejecución nueva. Los escenarios HTTP/CSRF de dos operaciones tras reclasificar están en03-U, separados de V.

No se encontró defecto inequívoco nuevo y no se modificó código funcional. No se repitió la suite332 de03-T: este corte cambió solo soportes y documentación; aquella evidencia conserva fecha y alcance. El clúster terminó, puerto cerrado y SHA256 de bases protegidas y original conservados. No se limpió, restauró ni migró la base original.

## Reproducción y continuidad

Desde la raíz, crea clúster/base nuevos y no borra entornos anteriores:

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' -X utf8 'auditoria_por_etapas/resultados/soporte/audit03v_pg.py'
```

AUD03V-TRIPLE-CATEGORIA01, tarea técnica implementada/verificada en muestra, vincula PROD04/CA05, PROP-E00-HU-02 y VEN01c/CA03–05; incorporar referencia en matriz/backlog sin cambiar estados históricos. La opción de mostrar categoría en resumen y exigir reconfirmación ante reclasificación activa sigue pendiente de decisión documentada en03-U; no se exige por criterio vigente.

**Cursor 03-W / AUD03W-CONCILIACION-CATALOGO01:** conciliar inventario vigente de 9 HU/27 CA y cuatro criterios suplementarios contra resultados 03-A..V; verificar que cada fila identifique estado actual, evidencia reproducible y siguientes decisiones, actualizar las secciones históricas o marcarlas como históricas si inducen a confusión, y separar pendientes de despliegue, recepción/retiros y etapas11/15/16. Examinar primero PROD04/CA05 y PROP-E00-HU-02 frente a evidencia03-N/U/V. **NO EJECUTADO en V**. No declarar cierre global ni aprobar etapas posteriores.

23/27 criterios base siguen CUMPLE en sus muestras,4 CAT03/04 PREVISTO/FUTURO y cuatro suplementarios con evidencia anterior. Pendientes: serialización no autenticada/clientes internos→15; costo histórico→11; recepción/retiros PROP-03-RET-T01..T11→05–08/11/12/14–16; despliegue real. No afirmar coincidencia total.
