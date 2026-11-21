# 03-AI / 06-D · Respuesta perdida en reposición

11/11/2026, America/Lima. Sublote completado en muestras, sin cambios funcionales ni cierre de otras etapas. Protocolo leído completo; estado y cursorAH consultados; cambios preexistentes conservados. Repositorio en `r1-pmv`, sin AGENTS.md encontrados en el espacio inspeccionado. XLSX ausente, no leído ni modificado. Jira no se usa.

## Inventario y fuentes

Catálogo conserva [inventario03](ETAPA-03-inventario.md), [conciliaciónW](ETAPA-03-W-conciliacion.md) y adendas:9HU/27CA,23 CUMPLE en muestras previas,4 futurosCAT03/04 y4 suplementarios. No se repitieron esos27 criterios. Categorías, lector y pendientes de desactivación/retiro conservan su alcance.

Fuentes: HU-INV-01b/CA01–02 (`08:330–336`), autoría/consulta (`08:873`), RN01/14/29 (`07:50,181–195,333 y siguientes`), PROP-03-RET-T05/T11 ([traspaso](ETAPA-03-recepcion-y-retiros-pendientes.md)), recepción03-AB/AF, `16:329 QA-FIX-INV-01`, backlog09:97, CONTROL_SPRINTS:63. Fuentes01/02/14 y guía21 conservan su papel de alcance/diseño/roles, no evidencia funcional. No se extiende la idempotencia de cobroRN25 a recepción como criterio ya aceptado.

| ID / actor | Planificación → implementación → observado | Clasificación |
|---|---|---|
| INV01b/CA01–02;ALMACENERO | StockEntryProductForm/LotInputFormSet→stock_entry_create→register_stock_entry. Base10×2; entrada3×4+2×5→15/costo2.8000; otra2×6+3×7→20/costo3.7500. | CUMPLE muestras vigentes; política de vencidosDOC-03AH-01 pendiente. |
| PROP-03-RET-T05 | Abortar antes de entregarPOST no escribe; reenviar confirma. Trascommit y respuesta perdida, reenvío rechaza duplicado sin volver a escribir. | CUMPLE recuperación observada; PARCIAL idempotencia por intención. |
| Unicidad/atomicidad | Reenvíos exacto, normalizado, cantidad cambiada y mezcla de fila nueva con existente:200 con error y snapshot inalterado. | CUMPLE cuatro muestras; no caída de proceso/motor. |
| Adenda08:873;ALMACENERO/ADMIN | Nueva sesión recupera cuatro lotes posteriores bajoUUID inicial;ADMIN consulta200;VENDEDOR recibe403. | CUMPLE ficha acumulada, no constancia individual de recepción. |
| RN29/T11 | POST conCSRF propio válido:ADMIN/VENDEDOR no reciben;VENDEDOR no registra bajas/ajustes;ALMACENERO no ajusta.403 con plantilla de permiso. | CUMPLE cinco combinaciones; sesión vencida pendienteAJ. |
| VENDEDOR | MenúPreparar venta→buscar código muestra20 unidades; no se agrega línea ni cobra. | CUMPLE consulta sin escrituras; sin nueva prueba de históricos. |
| RN01 | Entrada directa sin solicitud aprobada. | CONFLICTO DE FUENTES / DOC-03AB-01 abierto. |

## Campos, acciones, mensajes y salidas

[Inventario anterior al ensayo](../evidencias/03-AI-ai-recovery-20261111T180122782821Z-8568faba/inventory-before.json); límites detallados03-AB/AC vigentes. Producto obligatorio con carga inicial, proveedor opcional activo; número de lote obligatorio normalizado/único por producto, cantidad entera positiva, costo positivo hasta4 decimales y vencimiento futuro. Se usan fechas reales futuras; sin reloj simulado. No se reaprobaron vacíos, máximos o formatos anteriores.

Confirmar entrada envíaPOST `/inventario/entrada/` con campos de producto/proveedor/lotes, gestión del formset yCSRF; se comprobó ausencia de `idempotency_key`. La vista devuelve302 a `/inventario/cargas/<UUID-inicial>/` al guardar, o200 con formulario de errores al rechazar. Se observó «El lote AI-D ya existe para este producto.»; mezclarAI-NUEVO conAI-E existente tampoco guarda ninguna fila nueva. El formulario conserva la entrada rechazada visible; no se verificó cada campo individual tras el error.

Recuperación desde Inicio→Ver inventario y alertas→RecepciónA→Ver carga, con otra sesión del almacenero: mismoUUID,20UND,costoS/3,75 y cuatro lotes posteriores, con cantidades/costos/proveedor/responsable. `is_initial=False` distingue las cuatro filas. Las columnas previas de los tres primeros lotes permanecen idénticas. Recarga no escribe. Captura inspeccionada. El título sigue Existencias iniciales/Carga inicial confirmada y hay sección Entradas posteriores de mercadería: es ficha acumulada, no constancia individual de la respuesta perdida.

## Secuencia y resultados

1. CargaAI-BASE10×2. PrepararAI-B3×4 yAI-C2×5. Abortar antes de entregarPOST:Chrome `net::ERR_CONNECTION_RESET`, snapshot comercial idéntico.
2. Reenviar el mismo payload autenticado:302 a referencia inicial, tres lotes/15 unidades/costo2.8000.
3. PrepararAI-D2×6 yAI-E3×7. EntregarPOST, esperar302 del servidor y abortar su respuesta al navegador:Chrome muestra error, pero persisten cinco lotes/20 unidades/costo3.7500.
4. Reenvíos idéntico, AI-D con espacios/minúsculas, cantidad9 y mezclaAI-NUEVO+AI-E:rechazo controlado y snapshot sin cambios. También se reenvió por botón y se capturó error visible.
5. Recuperar en otra sesión, consultarADMIN y vendedor, comprobar cinco denegaciones conCSRF válido y cuerpo de autorización. Consultas/rechazos no escriben comercio.

**57/57 comprobaciones finales Chrome157.0.8103.39/HTTP/ORM y6/6 métodos de regresión acotada**:dos de límites de recepción y cuatro de costosAG. `check` y migraciones sin cambios. No se suman controles repetidos como casos nuevos. Sin PostgreSQL nuevo:son secuenciales, no prueban bloqueos/concurrencia. La suite350 sigue siendo evidenciaAG, no ejecuciónAI.

Se simula transporte con Playwright `route.abort` y `route.fetch(maxRedirects:0)`. No se apaga servidor/motor ni corta físicamente la red. Tras302 se verifican efectos persistidos; no es una simulación de transacción parcialmente confirmada. Payload solo en memoria; no se publicanCSRF ni credenciales.

## Hallazgos y propuestas

**OBS-03AI-01,P2,PARCIAL:** la unicidad impide duplicar estos lotes, pero no constituye idempotencia persistente por intención. El reintento devuelve error, no el resultado anterior como éxito; no identifica una recepción individual. Cambiar todos los números sería otra entrada según las reglas actuales; no se ejecutó ni se presume deduplicación semántica. No se declara defecto inequívoco sin criterio seleccionado.

**PROP-03AI-REC01, propuesta suplementaria INV01b/T05:** dado un operador sin respuesta, cuando consulta inventario, entonces puede identificar producto/lotes/cantidades/responsable y continuar sin duplicarlos. ActorALMACENERO;ADMIN consulta;VENDEDOR sin acceso a ficha. Proponer ayuda para consultar antes de cambiar números y reintentar; no implementada.

**DOC-03AI-01, alternativas pendientes:** mantener rechazo de lotes repetidos con instrucciones y ficha acumulada; o seleccionar recepción identificable con clave persistente que devuelva resultado anterior y rechace la misma clave con otro contenido. La segunda exige modelo, atomicidad, permisos, retención y definición de recepción individual/multiproducto. No se crea como arreglo tácito.

**T-03AI-TEST01, implementada/verificada:** dos pérdidas de respuesta, cuatro reenvíos, recuperación y permisos conCSRF válido. **PROP-03AI-TEST02, propuesta:** seleccionada la política, probar misma intención desde dos sesiones, cambio de payload, reinicio y recuperación. Carreras de lotes03-AB permanecen evidencia previa, no prueba nueva de idempotencia.

### Corrección de evidencia y soporte

LosPOST403 de AG/AH y la primera corridaAI no asegurabanCSRF propio. Por sí solos solo acreditan rechazo sin escritura, no su causa de autorización. La corrida finalAI subsana cinco combinaciones conCSRF válido y plantilla de permiso. Se añaden notas aAG/AH conservando resultados de costo y evidencias originales. LosGET403 no tienen esa ambigüedad.

Un primer runner de regresión tuvo6 métodos correctos pero salida1:se lanzó mientras el navegador escribía su base ficticia y el guardián detectó justamente esa base activa. Original y demás bases permanecieron iguales. Se repitió secuencialmente con navegador detenido:6/6,salida0,todos los hashes intactos. No se modifica el guardián ni se oculta el primer resultado.

## Evidencia, conservación y reproducción

- [57 controles, transporte y estados](../evidencias/03-AI-ai-recovery-20261111T180122782821Z-8568faba/browser.json)
- [Rechazo visible](../evidencias/03-AI-ai-recovery-20261111T180122782821Z-8568faba/01-reintento-rechazado.png) · [Recuperación inspeccionada](../evidencias/03-AI-ai-recovery-20261111T180122782821Z-8568faba/02-recuperacion.png)
- [Servidor detenido y hashes](../evidencias/03-AI-ai-recovery-20261111T180122782821Z-8568faba/result.json)
- [Regresión final6](../evidencias/03-K-tests-20261111T180154202346Z/result.json) · [Primer control con base activa](../evidencias/03-K-tests-20261111T180132865448Z/result.json)

Base nueva marcada `datos/etapa03k-AI-20261111T180122782821Z-8568faba/audit.sqlite3`:tres productos, una carga técnica, cinco lotes,20 unidades deA,costo3.7500;cero ventas/bajas/ajustes. Turno ficticioOPEN. HMAC antes de autenticar, sin `.env`, puerto cerrado. OriginalSHA256 `4406ecd5babab34f0bb264e82c134eb21563494f9faf50e462d50c30c9d2ea95`;bases protegidas previas intactas.

```powershell
r1-pmv/.venv/Scripts/python.exe -X utf8 auditoria_por_etapas/resultados/soporte/audit03y_browser_run.py ai-recovery
# Esperar que termine antes de iniciar otro runner que proteja todas las bases.
$env:AUDIT03K_DEFAULT_COOKIES='1'
r1-pmv/.venv/Scripts/python.exe -X utf8 auditoria_por_etapas/resultados/soporte/audit03k_run.py tests inventory.test_receipt_boundaries sales.test_audit03ag_cost
```

## Cursor exacto

**03-AJ / 06-E / AUD03AJ-SESION-RECEPCION01:** abrir reposición en sesiónALMACENERO, invalidar esa sesión mediante flujo controlado de prueba y confirmar formulario antiguo. Comprobar redirección/error, ausencia de escrituras y conservación/pérdida de campos; reautenticar y recuperar por menú antes de confirmar una sola vez. Repetir denegación por cambio de rol/desactivación si no está cubierta, conCSRF válido y snapshots. No confundir salida con caída del servidor. DOC-03AH-01/DOC-03AI-01 siguen abiertos; despliegue, recepción multiproducto, cuarentena y retiro sanitario pendientes.
