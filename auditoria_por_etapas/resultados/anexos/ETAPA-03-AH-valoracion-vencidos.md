# 03-AH / 06-C · Vencimiento, reposición, merma y costo histórico

11/11/2026, America/Lima. Sublote de observación y conciliación terminado; **política de valoración pendiente**. No se modificó código funcional ni se aprobaron etapas06–08/11. Se leyó completo el protocolo y se retomó el cursor de03-AG. Cambios preexistentes preservados; repositorio `r1-pmv`; sin AGENTS.md encontrados en el espacio inspeccionado. XLSX ausente, no leído ni modificado. No se usa Jira.

## Alcance y clasificación previa

El [inventario completo de catálogo](ETAPA-03-inventario.md) y [conciliación03-W](ETAPA-03-W-conciliacion.md), con sus adendas posteriores, conservan nueve HU/27CA,23 CUMPLE en muestras previas y cuatro futuros CAT03/04. No se repitieron ni se reclasificaron esas pruebas. DOC03-01 permite categorías activas distintas de enlatados con UND/vencimiento; lector conserva alcance y evidencias Y/Z; activar/desactivar no es retiro sanitario.

| Elemento | Fuente precisa / papel | Clasificación de este corte |
|---|---|---|
| INV01b/CA01–02 | 08:330–336;07:181–195;09:97 | Implementado adicional al R1. Cantidad anterior y valoración frente a vencidos PARCIAL; no aprobar política por una fórmula aislada. |
| RN28;VEN01c/CA06 | 07:325–329;03:121;02:117,143;16:153–155 | Seleccionado. Conservación de costo por venta verificada en esta frontera. |
| INV02/CA01–03;RN04/05/20 | 08:340–346;07:80 y siguientes;09:79 | Implementado adicional. Muestra de baja parcial y motivo de vencimiento; resto de HU NO EXAMINADO aquí. |
| INV02/CA04 | 08:347 | Constancia completa de merma NO EJECUTADA en este sublote. Un registro ORM no acredita pantalla/impresión. |
| INV03/CA01–03 | 08:351–358;09:80 | Implementado adicional. Ajustes +2 y−2 en lote existente; creación de lote nuevo y límites completos NO EJECUTADOS. |
| Recálculo después de merma/ajuste | 16:329 QA-FIX-INV-01;03:281,312 BUG005/037;CONTROL_SPRINTS:92;inventory/tests.py:826 | Comportamiento adicional respaldado por tareas/pruebas históricas; exige conciliar su fórmula con RN14. Marcas «Hecho/PASS» históricas no prueban coherencia global. |
| Roles | guía21, tabla de recorrido; views y services de inventory | ALMACENERO recibe y da de baja; ADMIN ajusta; VENDEDOR vende. Tres POST denegados verificados. |

Fuentes01/09/14 conservan alcance históricoR1 y asignación de releases, no evidencia funcional. Se contrastaron símbolos concretos `register_stock_entry`, `_recalculate_product_average_cost`, `write_off_stock`, `register_physical_adjustment` y copia de costo en `checkout_sale`. No se infirió una política contable o legal externa.

## Inventario de interfaz y entradas del sublote

[Inventario estructurado anterior a la corrida](../evidencias/03-AH-ah-cost-20261111T175450781262Z-e560658d/inventory-before.json). Formularios de carga/reposición conservan límites y normalización inventariados en03-AB/AC. No se reaprobaron todos los extremos.

| Ruta / actor / acción | Campo o salida; regla e inicial | Ejecución y límite |
|---|---|---|
| carga-inicial y entrada;ALMACENERO | Producto obligatorio, proveedor opcional; lote/número,cantidad,costo,vencimiento. Dos lotes10×2 y10×4; posterior10×6. | Menú→formulario→confirmación→constancia. Normalización/duplicados/extremos conservan pruebas previas. |
| `/ventas/`, `/ventas/cobrar/`;VENDEDOR | Búsqueda por código, cantidad2, precio9, efectivo20. Salida venta18/vuelto2. | Venta antes y después; FEFO y costos persistidos contrastados. No se realizó auditoría integral de caja. |
| `/inventario/stock/`;ALMACENERO | Stock físico/vigente calculados, mínimo10, alertas. | Tras vencimiento muestra18/10. Se inspeccionó separación y captura; no se aprueba toda etapa07. |
| `/inventario/bajas/nueva/`;ALMACENERO | Selección lote; `lot_id`UUID oculto obligatorio; clave idempotenciaUUID oculta opcional de formulario. Cantidad entera1..999999. Motivo obligatorio Vencimiento/Daño/Robo. Notas opcionales salvo Daño/Robo; sin maxlength en formulario. | SeleccionaAH-A, cantidad1, Daño con notas: rechazo. Cambia a Vencimiento: persiste una baja y responsable. Claves alteradas/reenvío/límites de notas NO EJECUTADOS aquí. |
| `/inventario/ajustes/nuevo/`;ADMIN | Selección lote; UUID y clave oculta; delta entero−999999..999999, cero prohibido. Motivo obligatorio hasta300 caracteres; servicio retira espacios exteriores. | SeleccionaAH-B, +2 y−2 con motivo ficticio. No se ejecutaron extremos, cero o texto largo. |
| `/inventario/cargas/<uuid>/`;ALMACENERO | Costo promedio mostrado con dos decimales; lotes y saldo actuales. | Se observan4,50 y luego5,00; captura inspeccionada. La página es consulta actual, no un snapshot de costo de cada recepción. |
| `/ventas/constancia/<uuid>/`;VENDEDOR | Texto histórico y costo oculto. | Recarga tras los movimientos conserva exactamente texto inicial; detalleORM sigue3.0000. |

Los inputs visibles de cantidad/motivo/delta se rellenaron expresamente. Metadatos `initial=None` del inventario describen los formularios; no acreditan todos los valores que una vista pueda precargar. El aviso de rechazo observado contiene «el motivo debe ser»; fuente del mensaje completo: «El lote está vencido; el motivo debe ser «Vencimiento».». Se verificó que ese rechazo no alteró ninguna instantánea comercial. No se atribuye comprobación literal de los mensajes de éxito: el éxito se acreditó por redirección y persistencia.

## Secuencia reproducida: resultado observado, no aprobación de política

| Paso | Cantidades A/B/C | Costo producto | Costo histórico venta1 | Evaluación |
|---|---|---|---|---|
| CargaA10×2+B10×4, venta2 FEFO | 8/10/—,18 vigentes |3.0000|3.0000|CUMPLE muestra inicial/RN28|
| Avanzar fecha de negocio hasta vencimientoA | 8 vencidas/10 vigentes/— |3.0000|3.0000|Fecha por sí sola no escribe costo ni stock;18 físicas/10 vigentes|
| EntradaC10×6 |8/10/10|4.5000|3.0000|Usa10×promedio3 más60 sobre20. Política pendiente frente a costo propio de B4|
| Baja1 de A vencido |7/10/10|5.0000|3.0000|Vigentes no cambian; recálculo `(10×4+10×6)/20` cambia costo|
| Ajuste +2 en B |7/12/10|4.9091|3.0000|Recálculo de lotes;histórico conservado|
| Ajuste −2 en B |7/10/10|5.0000|3.0000|Regresa al costo por lotes;histórico conservado|
| Nueva venta2 |7/8/10|5.0000|3.0000|Nueva venta guarda5.0000;vencido no se vende|

**H-03AH-01 / DOC-03AH-01, P1, CONFLICTO DE FUENTES / política insuficiente.** RN14 exige promedio móvil en entradas. Las tareas y pruebas BUG005/037 exigen recálculo desde lotes después de merma/ajuste. No se define de manera coherente el evento de revaloración al vencer, la valoración de las unidades retiradas ni qué representa el promedio cuando se mezclan existencias vencidas y vigentes. El resultado observado implica que retirar una unidad ya no vendible cambia el costo de una futura venta aunque no varíe su inventario vendible. **No se etiqueta CUMPLE para el conjunto de valoración.** No se modifica la regla ni la implementación por una elección arbitraria. La corrección03-AG de guardar el costo de cada venta sigue válida y se verifica aquí.

## Decisión y propuestas trazables

**DOC-03AH-01: alternativas pendientes, ninguna seleccionada.** Deben definirse con el responsable del producto, sin presentarlas como recomendación contable:

1. **Promedio móvil coherente:** conservar el costo unitario ante salidas/mermas; definir expresamente la base física o vendible y el tratamiento de vencimiento. En una variante vendible que mantiene costo3 al excluir A, la entrada produce4.5 y la baja posterior de A no lo cambia. Requiere cambiar la expectativa de recálculo de merma/ajuste y definir cómo valorar sobrantes.
2. **Valoración por lotes vigentes:** actualizar al excluir A a4; entrada produce5 y la baja de A deja5. Requiere revisar RN14, momento de actualización (fecha/consulta/operación) y aplicación uniforme a ventas, ajustes y costos históricos. No basta cambiar una función aislada.
3. **Dos métricas explícitas:** conservar promedio móvil para costo de venta y mostrar por separado valoración de lotes vendibles. Requiere nombres, estados, reglas y criterios nuevos; evitar que un único `average_cost` cambie de significado.

**PROP-03AH-CA01, propuesta suplementaria INV01b/RN14:** dado un producto con lotes de costos distintos y uno vencido, cuando se repone o se retira exclusivamente stock vencido, entonces la base y el costo calculado coinciden con la política seleccionada, con cuatro decimalesHALF_UP y visualización a dos; las ventas confirmadas conservan su costo. ActorALMACENERO;ADMIN consulta/ajusta;VENDEDOR solo consulta/vende. No renumerar CA originales.

**PROP-03AH-CA02, propuesta INV02/03:** dado un ajuste o baja, cuando se confirma, entonces queda definida y verificable su valoración y el efecto en el promedio, además de cantidad/motivo/responsable; rechazos no alteran ninguno. Definir también stock cero, todo vencido, mezcla, sobrantes y recuperación tras reintento. No implementado.

**T-03AH-VAL01, propuesta:** seleccionarDOC-03AH-01, actualizar RN14 y adendas de tareas/matriz preservando historial; implementar una única política explícita y sus pruebas. **T-03AH-TEST01, implementada/verificada:** recorridoChrome y evidenciaORM de la divergencia e históricos. **T-03AH-TEST02, propuesta:** una vez seleccionada la política, probar merma/reposición/cobro concurrentes en PostgreSQL y cambio de díaLima; no validar una expectativa de valoración inventada. No requiere duplicar HU de recepción/merma/ajuste.

## Evidencia, entorno y límites

Chrome157.0.8103.39 automatizado con Playwright, tres cuentas ficticias, Django/SQLite nueva, HMAC de instancia, sin `.env`. **30/30 comprobaciones de observación**, incluyendo tres POST403 (vendedor a baja/ajuste, almacenero a ajuste) con persistencia inalterada. Ese conteo no transforma la política observada en aprobada. **6/6 regresiones acotadas**: cuatro de costo históricoAG y dos BUG005; `check` y migraciones sin cambios. La suite350 previa no se volvió a ejecutar completa porque no cambió código funcional. Sin PostgreSQL nuevo, sin escáner físico ni despliegue.

Simulación explícita: `timezone.localdate` del servidor aislado pasa de11/11/2026 a10/01/2027 mediante archivo de prueba; no se alteraron relojWindows, fechas persistidas de lotes ni `timezone.now`. Por ello timestamps de operaciones siguen11/11 mientras la fecha de negocio de la prueba es10/01. No representa espera real de60 días ni verifica coherencia de timestamps bajo viajes temporales. El soporte comprueba marca y ruta de base antes de instalar la simulación.

- [Navegador, estados y30 controles](../evidencias/03-AH-ah-cost-20261111T175450781262Z-e560658d/browser.json)
- [Stock vencido](../evidencias/03-AH-ah-cost-20261111T175450781262Z-e560658d/01-vencido.png), [reposicion4,50](../evidencias/03-AH-ah-cost-20261111T175450781262Z-e560658d/02-reposicion.png), [baja y costo5,00](../evidencias/03-AH-ah-cost-20261111T175450781262Z-e560658d/03-baja-revalora.png)
- [Regresión6](../evidencias/03-K-tests-20261111T175540850175Z/result.json), [log](../evidencias/03-K-tests-20261111T175540850175Z/tests.txt)
- [Cierre de servidor y bases](../evidencias/03-AH-ah-cost-20261111T175450781262Z-e560658d/result.json)

Base ficticia conservada `datos/etapa03k-AH-20261111T175450781262Z-e560658d/audit.sqlite3`: tres productos, tres lotes, dos ventas, una baja, dos ajustes;A7 vencidas/B8/C10 vigentes,25 físicas/18 vigentes. Turno ficticioOPEN. Puerto cerrado y archivos protegidos sin cambios; original SHA256 `4406ecd5babab34f0bb264e82c134eb21563494f9faf50e462d50c30c9d2ea95`.

```powershell
r1-pmv/.venv/Scripts/python.exe -X utf8 auditoria_por_etapas/resultados/soporte/audit03y_browser_run.py ah-cost
$env:AUDIT03K_DEFAULT_COOKIES='1'
r1-pmv/.venv/Scripts/python.exe -X utf8 auditoria_por_etapas/resultados/soporte/audit03k_run.py tests sales.test_audit03ag_cost inventory.tests.PhysicalAdjustmentTests.test_bug005_register_stock_entry_excludes_expired_lots_from_average_cost inventory.tests.PhysicalAdjustmentTests.test_bug005_writeoff_and_physical_adjustment_recalculate_average_cost
```

## Cursor exacto independiente

**03-AI / 06-D / AUD03AI-REPOSICION-RESPUESTA01:** producto con carga inicial y stock vigente; preparar entrada posterior válida y simular pérdida de respuesta antes de entregarPOST y después del commit. Reenviar la misma petición, comparar número de lotes/cantidad/costo/responsable y recuperación por inventario/constancia entre roles. Separar duplicado de lote de verdadera idempotencia y documentar resultados sin crear una cabecera de recepción no seleccionada. DOC-03AH-01 queda pendiente sin bloquear esta prueba independiente. RN01, recepción multiproducto, despliegue, cuarentena y retiro sanitario conservan sus pendientes; no se cierra ningún módulo por este sublote.


**Corrección de atribución, 03-AI (11/11/2026).** Los POST403 de este corte no aseguraban token CSRF propio: acreditan rechazo sin escritura, pero por sí solos no prueban autorización por rol. La corrida final03-AI verificó explícitamente cinco combinaciones con CSRF válido y plantilla de permiso. Costos, datos y demás observaciones conservan su evidencia. [Detalle y resultados](ETAPA-03-AI-reposicion-respuesta.md).
