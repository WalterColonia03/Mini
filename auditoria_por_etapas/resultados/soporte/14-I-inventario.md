# Inventario previo 14-I · primera pasada · 14/11/2026 Lima

Alcance: HU-INV-02, constancia y reintento de merma entre identity/catalog/inventory/cash/sales. La cadena general se reejecuta separadamente. Se conserva H2 y no se trasladan sus aprobaciones al presente build. Inventario antes de ensayar; los resultados se incorporarán en ETAPA-14 y evidencias/14-I-20261114.

## Requisitos, reglas y tareas seleccionadas

| ID / clasificación inicial | Actor / necesidad | Planificación → implementación / salida | Caso previsto |
|---|---|---|---|
| HU-INV-02/CA01, R1 aceptado; NO EJECUTADO aquí | ALM/ADMIN: baja por lote y cantidad válida | forms.StockWriteOffForm → services.write_off_stock → StockWriteOff/Lot | I01 baja2 de A10@3; exceso/0/fracción y motivo inválido |
| HU-INV-02/CA02, R1; NO EJECUTADO | Causa real según día Lima | validación expiration_date y Reason | E vencido: vencimiento/robo sí, daño no; A vigente: vencimiento no |
| HU-INV-02/CA03, R1; PARCIAL por inspección | Explicación daño/robo y empleado | notes.strip, responsible FK; no fotografía del autor | vacío/NUL; renombrar empleado y recargar |
| HU-INV-02/CA04, R1; INCUMPLE por inspección pendiente de reproducción | Constancia correlativa | B-NNNNNNNN persistido; POST redirige formulario; no ruta dedicada | Confirmar; buscar documento; recargar |
| RN-05/C01, R1; NO EJECUTADO | Robo real en vencido, costo de salida sin caja/ventas/precio | validación causa; unit_cost; average_cost | E+ROBO, testigos todas tablas |
| RN-05/C03, R1; INCUMPLE por inspección | Constancia inmutable/roles/impresión | faltan vista y snapshots; Kardex usa autor/número actuales | consulta ADMIN/ALM, VENDEDOR403, cambio maestros |
| RN-05/C04, R1; PARCIAL por inspección | Una operación y recuperar resultado | deduplicación HTTP guardada en sesión; servicio sin clave | reenvío misma sesión, otra sesión, contenido distinto; PG pendiente15 |
| DOC-03AI/C03, dependencia revalidable; no nuevo requisito de recepción | Distinguir R1 y R2 con mismo lote comercial | selector por UUID + referencia receipt_line | baja del lote R2 conserva R1 |
| RN01/03/04/14/19/20/25/28/29, dependencias | Físico/vendible, causa, coste e historia | StockWriteOff/Lot/Product; ledger; sales; cash | precio/ventas/caja invariantes; salida costo3; consulta stock8 |
| RN-05/C02 + INV03, FUERA de este sublote | Lote nuevo por ajuste y costo físico0 | no se audita como completo | cursor posterior propio |
| HU-INV-04 y DEC08, dependencias | Movimientos y saldo | inventory.ledger / product_movements | merma -2 y saldo8; autor histórico |
| HU-INV-05/06, HU-REP-08, FUTURAS | Historial global/reporte agrupado | ausencia no es incumplimiento de este corte | no añadir pantallas globales |
| 16: RN-05 / DEC-08-CONSTANCIA-MERMA; 14: cursorI | tarea técnica de constancia, no nueva HU | modelo/servicio/vista, migración, pruebas | diagnóstico y concreción separada de aceptación |

Fuentes precisas:08 anclas HU-INV-02, RN-05, contrato-RN-05, contrato-DOC-03AI-01; CP-HU-INV-02-001/002, CP-RN-05-001;02 concrecionesH1/H2 y entidades de inventario;16 filasRN05/DEC08;14 preparaciónH2. 07/09/03 son vistas de08, no fuentes de aceptación independientes. 21 y01 delimitan release seleccionado frente a futuro. r1-pmv/CONTROL_SPRINTS no prueba funcionamiento. Sin workbook vigente en raíz: no se usa una hoja histórica como contrato.

## Superficie y trazabilidad inversa

| Familia | Ruta / rol / estado | Literal o plantilla; propósito y campos | Respaldo y límites |
|---|---|---|---|
| I-UI01 | /inventario/bajas/nueva/ ADMIN/ALM | «Registrar baja de inventario»; selector «Seleccione el lote a dar de baja» | INV02/CA01; físico, puede estar vencido/inactivo |
| I-UI02 | selector con stock>0 | Producto, Lote, Vencimiento, Disponible; «Dar de baja» | RN05; UUID distingue origen; cantidad actual, no original |
| I-UI03 | selector vacío | «No hay lotes con existencias disponibles.» | CT-COHERENCIA-UI; no equivale a stock vendible |
| I-UI04 | ?lote=UUID seleccionado | «Lote seleccionado: {producto} · {número} — Disponible: {n} u. · Vence: {fecha}» y referencia de ingreso | INV02 + DOC03AI; dato actual preconfirmación |
| I-UI05 | formulario | lot_id oculto: UUID obligatorio; idempotency_key oculto: UUID opcional en código inicial | RN05/C04; no debe deducir operación nueva de sesión |
| I-UI06 | formulario | «Cantidad a dar de baja»: entero, inicial vacío, requerido,1..999999 y<=saldo | CA01; HTML NumberInput min/max/step1; servidor propio |
| I-UI07 | formulario | «Motivo»: select VENCIMIENTO/DAÑO/ROBO; primera opción predeterminada Vencimiento | CA01/02; texto mostrado Vencimiento/Daño o rotura/Robo o faltante |
| I-UI08 | formulario | «Detalle (obligatorio para Daño y Robo)»: textarea, opcional de campo y obligatorio por causa; strip; rechaza NUL; sin máximo de negocio documentado | CA03/RN20; no inventar tope sin decisión |
| I-UI09 | formulario | «Confirmar baja» POST; «Cancelar» vuelve selector | CA01/04; no descuento en GET/cancelar |
| I-UI10 | POST inválido | mensajes junto al campo, errores generales y UUID ocultos | CT-COHERENCIA-UI; valor/clave se conservan; foco/anuncio por revisar |
| I-UI11 | POST válido | «Baja {correlativo} registrada correctamente.» y redirección | CA04: éxito exige commit; debe permitir recuperar constancia |
| I-UI12 | reenvío | «Esta baja ya fue registrada anteriormente.» / «La clave de operación ya fue utilizada para otra solicitud. Recargue el formulario e inténtelo nuevamente.» | RN05/C04; testigo sin mutación |
| I-UI13 | causa/cantidad | «La cantidad supera las existencias disponibles del lote.»; «Detalle obligatorio para Daño o rotura y Robo o faltante.» | CA01/03 |
| I-UI14 | fecha | «El lote aún no ha vencido; seleccione la causa real de la baja.»; «El lote está vencido; seleccione Vencimiento por caducidad o Robo o faltante si esa es la causa real.» | CA02/RN05 |
| I-UI15 | /inventario/productos/{id}/movimientos/ ADMIN/ALM | Merma ({causa}) · {B} — Lote {número}.{notas}, cantidad negativa, saldo, responsable | INV04, RN05/C03; lectura actual de nombres no prueba historia |
| I-UI16 | /inventario/stock/ y /ventas/ | físico/vendible tras baja; disponibilidad del vendedor | RN01/03/14; etapa07/10 dependencia, no cierre |
| I-UI17 | vendedor GET/POST baja/movimientos | 403 «Acceso denegado» | RN29/identity autorización servidor, testigo sin cambio |
| I-UI18 | salida esperada no implementada inicialmente | constancia: referencia/fecha/autor/producto/lote/cantidad/motivo/explicación/costo y origen | CA04 + RN05/C03; imprimir documento interno, no fiscal |

Mensajes literales dinámicos y valores reales se capturan por checkpoint en JSON; este inventario tiene18familias, no18elementos exhaustivos de todo el sistema. Fronteras no ensayadas y dispositivos físicos quedan NO EJECUTADOS. Login/menús/maestros/caja/POS tienen inventario previo14-D y se revalidan por el runner de cadena, no se presume que cubra cada campo histórico.

## Enlaces a resultados anteriores

[01 identidad](../ETAPA-01.md), [02 personal](../ETAPA-02.md), [03 catálogo](../ETAPA-03.md), [04 proveedores](../ETAPA-04.md), [05 carga](../ETAPA-05.md), [06 recepción](../ETAPA-06.md), [07 existencias](../ETAPA-07.md), [08 bajas](../ETAPA-08.md), [09 caja](../ETAPA-09.md), [10 borrador](../ETAPA-10.md), [11 cobro](../ETAPA-11.md), [12 historial](../ETAPA-12.md). Sus resultados son heredados salvo caso ejecutado con nueva evidencia14-I; tampoco604tests históricos equivalen a navegador o concurrenciaPG.


## Resultado de superficie14-I

22familias trazadas:18iniciales y4concreciones siguientes. La familiaI-UI18 deja de estar ausente en este build; UUID deI-UI05 pasa a requeridaHTTP. Las clasificaciones iniciales se conservan como diagnóstico, no como estado final.

| Familia nueva | Ruta / rol / estado / literal | Respaldo y evidencia |
|---|---|---|
|I-UI19|GET /inventario/bajas/{UUID}/ ADMIN/ALM; «Baja confirmada», «Constancia de merma {B}», «Datos conservados de la baja de mercadería.»|INV02/CA04, RN05/C03; I05/I13/I14, tests snapshot/roles|
|I-UI20|Referencia; Fecha y hora de Lima; Responsable original; Producto original; Código original; Lote original; Vencimiento original; Origen registrado; Cantidad retirada; Motivo; Explicación; Costo unitario de salida|Datos persistidos al commit; formatosB,dd/mm/aaaa HH:mm:ss, fecha, texto escapado, cantidadentera+UND, costoS/4decimales. «Sin explicación registrada» si vacío; «No disponible» siNULL. I13/I22/I23/I24/I25 ytests|
|I-UI21|«Imprimir», «Registrar otra baja», «Ver movimientos», «Ver inventario»; «Ver constancia de merma» desdeKardex|RN05/C03,INV04/CA03; acciones GET/navegación y window.print. I12..18; impresiónfísicaNOEJECUTADA|
|I-UI22|«Registro anterior o incompleto: la fotografía original de producto, lote, origen o responsable no está disponible. No se reconstruye con los maestros actuales.»; «Fotografía histórica de merma no disponible. Consulte los datos conservados en su constancia.»; «Constancia interna de merma. No es un comprobante de pago.»|CT-COHERENCIA-UI,RN05/C03,DOC03AI; I25 y legacytest para constancia; avisoKardex inspeccionado, rama específica enChromeNOEJECUTADA|

La vista reutiliza clases existentes;12salidas y4acciones no son16HU nuevas. La clave/huella/modelo/migración se trazan aRN05/C04 y diseño02. No hay extra comercial sin requisito incorporado. Clasificación por criterio y evidencia exacta en criterios-final.json; errores de UUID requeridos se capturan en testsHTTP, no todos se forzaron porChrome. Estado vacío de selector, teclado y lector de pantalla conservan NOEJECUTADO en este sublote.
