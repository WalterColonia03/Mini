# Estado general vigente de auditorías · 14/11/2026 (revalidación01-E)

**Actualización01-E:** primera pasada, revalidación acotada solicitada de ingreso/bloqueo.120/120testsidentity y24checkpointsBrave aceptados; correo de login corregido a254 conforme a DOC02-04. SieteCA principales revisados:6CUMPLE en muestra secuencial y1PARCIAL; admin alternativo/tráfico/retención/eventos abiertos. **Cursor local `01-F-ADMIN-PERIMETRO-01`**. No inicia segunda pasada global ni cierra otros módulos. La secuencia general conserva15→16→17→00→segunda pasada. [Informe01-E](ETAPA-01.md#vigente-01-e) · [Inventario](soporte/01-E-inventario.md) · [Verificación](evidencias/01-E-20261114/verificacion-final.json) · [Estado anterior conservado](evidencias/01-E-20261114/antes/ESTADO_GENERAL.md).

**Revalidación acotada Etapa 04 (14/11/2026):** Primera pasada sobre build `1dd0f04c...` y `08` `ff85b85e...` (`HEAD 7816d332...`). `635/635` servidor (`SQLite :memory:`), `24/24` suite Etapa 04 (2 pruebas legacy aún aprueban toggle sin destino), `4/4` PostgreSQL 18.4 (`audit04_pg.py`) y `14/14` Chrome + vistas cruzadas (`audit04e_full.py`) reproduciendo **`DEF-04-DEC04-C02-OMIT-TARGET`** (`POST estado` sin `is_active` alterna `302`) y **`DEF-04-DEC04-C01-HOMONYMS-NO-RUC-CROSSMODULE`** (`Kardex`, `Vencimientos` y fila «Proveedor actual» omiten RUC), más observaciones UX (`OBS-04` `maxlength`/normalización, `GAP-04` confirmación y propuestas `PROPUESTA` sin aplicar). Sin cambios al producto ni a `08`; `r1_pmv.sqlite3` intacta. **Cursor local `04-CORRECCION-DEC04-PROV-01`**; mantiene secuencia global `15→16→17→00→segunda pasada`. [Informe04](ETAPA-04.md#reval-04-20261114) · [Browser JSON](evidencias/04-reval-20261114/browser-20261114T212427329168Z/browser-checks.json) · [PG 18.4](evidencias/04-postgresql-20261114T161715727147Z.json).

> **Fuente funcional principal:** [08 · planificación unificada](../../08_Historias_de_Usuario.md). Las fichas, RN y contratos de08 definen lo esperado; este documento conserva su papel de contexto, diseño, ejecución o evidencia. Las vistas07/09/03 se derivan de08.


Esta tabla sustituye como estado actual las notas anteriores. [Estado anterior íntegro](conciliacion_20261112/BASELINE/auditoria_por_etapas/resultados/ESTADO_GENERAL.md) · [Mapa consolidado](conciliacion_20261112/CONSOLIDACION.md) · [Encargos](conciliacion_20261112/ENCARGOS.md) · [Verificación nueva](conciliacion_20261112/VERIFICACION.md).

La etapa13 está finalizada para el panel mínimo. **Etapa14 COMPLETADA en primera pasada para integración por roles y persistencia delimitada.**634/634servidor,157checkpointsChrome y19/19PG sobre buildfinal estable. No cierra módulos individuales ni15–17. **Cursor15-SEGURIDAD-BASELINE-01.** [Informe final](ETAPA-14.md#cierre-14) · [Cobertura](soporte/14-CIERRE-cobertura.md) · [Estado anterior íntegro](evidencias/14-CIERRE-20261114/antes-ESTADO_GENERAL.md).

| Etapa | Fecha del estado | Cobertura | Estado vigente | Bloqueos/decisiones | Próximo cursor |
|---|---|---|---|---|---|
| [00](ETAPA-00.md) Inventario y planificación | 12/11/2026 | Inventario y evidencia del informe/anexos originales | Inventario completo del corte, no aprobación funcional | DOC00-01/05/07/08/09/12/13; matriz219 y catálogo74+8 | Revisión17 de trazabilidad y semántica |
| [01](ETAPA-01.md#vigente-01-e) Ingreso y bloqueo | 14/11/2026 | Primera pasada01-E:7CA,21elementoslogin trazados;120/120testsidentity y24checkpointsBrave;6CA cumplen en muestra,1parcial | Sublote01-E terminado; etapaPARCIAL. Correo254corregido/verificado;5fallos/15min revalidados secuencialmente | Admin alternativo demostrado; tráfico/retención/eventos/IDNA yPG nuevo pendientes. Ciclo real15min anterior solo heredado | 01-F-ADMIN-PERIMETRO-01; SEC-15-TRAFICO-01/RETENCION-01/OBS-01 |
| [02](ETAPA-02.md) Sesión y personal | 12/11/2026 | Inventario y evidencia del informe/anexos originales | Auditado en muestras; contratos revisados pendientes | Reset/desbloqueo auditado, nombre120, confirmación y concurrencia | DOC-02-04 / SEC-15-CONC-02 |
| [03](ETAPA-03.md) Categorías y productos | 12/11/2026 | Inventario y evidencia del informe/anexos originales | 03-AJ y anexos posteriores contrastados; sin cierre integral | Catálogo/lector aceptados; valoración/recepción/legacy/migraciones pendientes | DOC-03AH-01 / DOC-03AI-01 |
| [04](ETAPA-04.md#reval-04-20261114) Proveedores | 14/11/2026 | Revalidación acotada corte 14/11 (`1dd0f04c`/`ff85b85e`): 635/635 servidor, 24/24 Etapa 04 (2 legacy), 4/4 PG 18.4, 14/14 Chrome (`3` CUMPLE en muestra, `5` PARCIAL / `8` CA R1; `2` FUTURO; `2` INCUMPLE `DEC-04/C-01,C-02`). `admin/` no ejecutado | **PARCIAL CON DEFECTOS ABIERTOS DE CONTRATO VIGENTE** | Reproducidos `DEF-04-DEC04-C02-OMIT-TARGET` (POST omitido alterna `302`) y `DEF-04-DEC04-C01-HOMONYMS-NO-RUC-CROSSMODULE` (RUC omitido en Kardex/Vencimientos/«Proveedor actual»); `GAP-04` confirmación, `OBS-04` `maxlength`/normalización; corrección sin autorizar y `PG 17` pendiente | `04-CORRECCION-DEC04-PROV-01` / `SEC-15-CONC-02` |
| [05](ETAPA-05.md) Carga inicial | 12/11/2026 | Inventario y evidencia del informe/anexos originales | 05-L vigente; suite integrada elimina fallo heredado | PG17, recuperación postwrite, costos/recepción y despliegue | 05-M / CT-ROLLBACK-01-POST-ESCRITURA |
| [06](ETAPA-06.md#adenda-06-20261114) Recepción posterior | 14/11/2026 | Revalidación puntual post-`14-CIERRE` (`7a50fb73...`, `08` `4f696b6a...`): checks `0`, `inventory` `82/82 + 4/4` (`03-AJ`), `11/11` servidor (`25` fronteras), `93/93` Chrome (`1366×900`+`390×844`), `10/10` PG `18.4`, `372/372` resto sin `identity` (`495/497` con `identity`: `2` fallos WIP `etapa02`) | **REVALIDADA EN MUESTRA AISLADA Y PG 18.4 (PARCIAL)** | `DOC-03AB-01` directo con autorización externa; `HU-SOL-01..05b` y `HU-DASH-05` `FUTURO (W)` separados (`0` rutas); hallazgos UI/UX (`390×844` `<dd>` `stock_receipt`, wrap lote 64, topbar `stock-receipt`, `min_num=1` tarjeta 1, `#stock-entry-errors`); `PG 17`, `SIGKILL` y base operativa pendientes | `06-UX-MOVIL-RECEPCION-01` / `15-SEGURIDAD-BASELINE-01` |
| [07](ETAPA-07.md) Stock y vencimientos | 12/11/2026 | Inventario y evidencia del informe/anexos originales | Muestras ejecutadas; políticas/volumen pendientes | Alertas activas vs vencidos físicos, filtros y panel mínimo | DEC-07-VENCIDOS-FILTRO / PT-SEARCH-01 |
| [08](ETAPA-08.md) Bajas, ajustes y movimientos | 12/11/2026 | Inventario y evidencia del informe/anexos originales | Parcial frente a HU existentes y contratos revisados | Constancia/ajustes/Q0/Kardex revalidados en14; consulta global futura y operación conservan límites | Revalidación acotada14-CIERRE; no cierre global08 |
| [09](ETAPA-09.md) Caja | 12/11/2026 | Inventario y evidencia del informe/anexos originales | EJECUTADA; se rectifica NOEJECUTADO heredado en10–12 | 20 tests y6 casos PG históricos; Chrome67 funcionales+1control históricos; checks/topes resueltos14-CIERRE, orden/operación pendientes | PROP-09-DB-01 / DEC-11-TOPE-EFECTIVO-FORM |
| [10](ETAPA-10.md) Preparación y bloqueo de puesto | 12/11/2026 | Inventario y evidencia del informe/anexos originales | Borrador auditado; bloqueo300s no implementado | VEN01a seleccionado antes de piloto; GETprecio/revisión revalidados14, bloqueo/concurrencia global/UX pendientes | DEC-10-BLOQUEO-INACTIVIDAD / PROP-10-03 |
| [11](ETAPA-11.md) Cobro y exactitud | 12/11/2026 | Inventario y evidencia del informe/anexos originales | Muestras ejecutadas; integridad y política nuevas pendientes | Lotes/snapshots revalidados en muestra14-F, descuentos nuevos deshabilitados, límites/reintentos revalidados14; caída real pendiente | DEC-11-MODELO-AUDITORIA-VENTAS |
| [12](ETAPA-12.md) Constancias e historial | 12/11/2026 | Inventario y evidencia del informe/anexos originales | Muestras y nueva comprobación parcialPG; sin cierre integral | Permisos/orden/paginación/UX; filtrosCA02 y detalleCA03 conciliados | DEC-12-ORDEN-LINEAS-RECIBO / PROP-12-CAJA-HIST-CHROME-VENDEDOR |
| [13](ETAPA-13.md#cierre-13-b-final) Tablero, reportes y futuro | 13/11/2026 | Tres roles en navegador, cobro UI, recarga, vacíos, fallos, permisos, D11 y teclado. Servidor 100/100 por fixture y regresión 160/160. PG18.4 37/37 y 6/6 pruebas, con concurrencia y volumen sintético. Los conjuntos se solapan. | **FINALIZADA en primera pasada para el panel mínimo y sus consultas** | H13-01 a H13-08 y D11 resueltos en el alcance. PG17 y SLA productivo pendientes de validación propia. 16 HU/39 CA de DASH/REP/CONF siguen futuras. | 15-SEGURIDAD-BASELINE-01,14completada |
| [14](ETAPA-14.md#cierre-14) Integración por roles |14/11/2026|Primera pasada: cadena3roles, ajustes/historia/Q0, merma,Kardex,dinero,precio.634/634servidor,157Chrome,19/19PG;23HU80CA como mapa de dependencias, sin cierre global.|**COMPLETADA para alcance14 delimitado**|Pendientes funcionales propios resueltos; operación/seguridad global15,negocio16,conciliación17 conservan límites.|15-SEGURIDAD-BASELINE-01|
| 15 Seguridad, concurrencia, despliegue y recuperación | 13/11/2026 | Prompt disponible; primera pasada pendiente | NO EJECUTADA | EntornoPG, permisos, sesiones, tráfico, logs, respaldo y recuperación | 15-SEGURIDAD-BASELINE-01: inventario actual y primer sublote aislado;19PG14 heredados con compatibilidad |
| 16 Normativa y viabilidad | 13/11/2026 | Prompt disponible; primera pasada pendiente | NO EJECUTADA | Datos reales y aplicabilidad del canal fiscal/protección de datos | Fuentes oficiales vigentes y límites de las promesas del software |
| [17](ETAPA-17.md) Conciliación y evaluación de cierre | 13/11/2026 | Registro de continuidad; auditoría pendiente | NO EJECUTADA | Requiere resultados13–16 y conciliación de todos los tramos | Ejecutar prompt17; después preparar segunda pasada01–17 |

## Regla de continuidad

El orden de resolución va por integridad/costo/recepción/venta, permisos/seguridad, consultas/UX y evidencia de despliegue. No es obligatorio reejecutar una etapa histórica completa para investigar un caso concreto; conservar su ID y alcance. Los futuros siguen futuros. No declarar cierre por aceptar políticas, generar documentos o aprobar una suite parcial.

## Unificación documental de este corte

[Revisión y registro anterior](fuente_unica_20261112/REVISION.md) · [Validación estructural anterior](fuente_unica_20261112/VALIDACION.json). El corte12/11reunía74fichas completas,219CA base,60criterios de contratos,4J-CA y4criterios de veracidad visible, con110casos escritos. El sublote13-A conserva HUs, criterios y selección; añade CP-DEC-07-VENCIDOS-FILTRO-002 con ejecución parcial:111casos escritos y287 criterios. [Validación13](evidencias/13-A-20261113/planificacion/validacion.json).07/09/03 se regeneraron desde08SHA256 `5735fb283b70bca02ed551e0000c72df2025eaef9b977607b1e4a2b890e5a1d9`;02/14/16/21 se sincronizaron. Casos escritos no equivalen a ejecuciones aprobadas.

## Registro del sublote13-A

[Informe y cursor exacto](ETAPA-13.md) · [Estado antes de13](evidencias/13-A-20261113/estado-general-antes.md) · [Build final](evidencias/13-A-20261113/build-final.json). HEAD `7816d3328115cf5aa5bcdd0985fffd795b3ae084`, build local `f0918e86fad95a023c7a5fafe08ab6ebe8a61109a31669b349a5f94f13831e74`. Corregidos filtro de días fuera de rango, badgecrítico en inactivos, promesa de reportes, claridad de fecha/actualización y consulta por rol. Servidor revalidado; capturas iniciales no aprueban interfaz final. Los futuros CONF/DASH/REP siguen futuros. Las dependencias03/07/09/11/12solo tienen la revalidación acotada descrita; no se actualizan sus filas a cerrado.

## Secuencia de continuación confirmada

Primera pasada:13→14→15→16→17. Después:actualizar00 y ejecutar segunda pasada01–17 contra versiones identificadas de planificación y producto, conservando evidencias de la primera. [Guía de trabajo y aceptación](../CONTINUIDAD_Y_SEGUNDA_PASADA.md). Este estado corrige la clasificación prematura de17 y el nombre de16; no borra ni reetiqueta como ejecutadas pruebas históricas.

## Antecedente parcial 13-B · 13/11/2026, antes del cierre visual

Servidor/PostgreSQL y documentación completados dentro del alcance del panel mínimo; etapaPARCIAL por bloqueo externo visual. [Informe y cursor](ETAPA-13.md#9-continuación13-b-13112026--primera-pasada) · [Bloqueo y recuperación intentada](soporte/13-B-navegador.md) · [Disposiciones](soporte/13-B-disposiciones.md). Corregidos corte de métricas en una sentencia, fechas del historial, enlaces/textos y mensaje500.08final f4f6f82177685bfd492f5473bed945cd9add67b2a700639f40fe7444d449bc48; build99686b95a2c1d612bd4944a6cc0e7d16ab601c3f73d142e546a5f0c8ca30e215. Vistas07/09/03regeneradas;02/14/16/21coherentes;CP002PARCIAL. No se ejecutaron14ni segunda pasada.

## Cierre vigente 13-B-final · 13/11/2026 Lima

La revalidación visual resolvió el bloqueo del registro anterior en el mismo build de 183 archivos. CP002 quedó verificado para el panel mínimo. La venta única de S/7.10 y el cambio de lote de 3 a 1 persistieron tras recargar. El cierre conserva las ejecuciones anteriores y deja disponibles la constancia, los datos de contraste, las comparaciones por archivo y la validación de las vistas derivadas. [Navegador final](soporte/13-B-final-navegador.md) · [Disposiciones finales](soporte/13-B-disposiciones.md) · [Validación documental](evidencias/13-B-final-20261113/planificacion/validacion.json).

## Antecedente del sublote 14-A, rectificado por14-D · 13/11/2026 Lima

[Informe y cursor exacto](ETAPA-14.md) · HEAD `7816d3328115cf5aa5bcdd0985fffd795b3ae084` · Build (231 archivos) `1c3325902c4a948662eef111dec9ecf62e9bec57f568d9d3173c6bae7b7ac165` · 08 SHA-256 `33d2f17067fec3bb30e018ef49b77d87f84adfd9bafe04adf19161cd286e47a4`.

42 pruebas de integración E2E con Django Client (servidor embebido) sobre base SQLite en memoria. Recorrido ADMIN→ALMACENERO→VENDEDOR→ALM/ADMIN→VENDEDOR. 14 variantes de permisos denegados (403), cambios de estado, vencimiento, idempotencia y efectos cruzados entre módulos. 19 HU cruzadas, 10 RN, 25 rutas verificadas. [Suite de prueba](../../r1-pmv/tests/test_audit14_integration.py).

## Antecedente del sublote 14-B, rectificado por14-D · 13/11/2026 Lima

65 pruebas de verificación del HTML renderizado por rol (CT-COHERENCIA-UI) con Django Client + assertContains/assertNotContains. Menús laterales, dashboards, tarjetas de acción, headings de 15 páginas, login, páginas 403, accesibilidad (skip-link, lang, aria-label, tabindex). Regresión total: **547/547 OK** (72.7s). 0 incompatibilidades entre roles. 8 hallazgos positivos en el sublote 14-B. [Suite de prueba](../../r1-pmv/tests/test_audit14b_browser_content.py).

Excluidos: Selenium + Chrome visual con interacción real (clicks, JS) — opcional; concurrencia PostgreSQL (etapa 15). La etapa 14 queda EJECUTADA en primera pasada para los sublotes 14-A y 14-B.

## Antecedente del sublote 14-C, rectificado por14-D · 13/11/2026 Lima

12 pruebas de edge cases y auditoría comportamiento→planificación: PROP-14-03 verificada (admin desactiva producto/categoría con borrador activo → checkout rechaza), búsqueda filtra activos y no vencidos, descartar borrador sin efecto en stock, constancia por rol, cierre de caja con diferencia, correlativos secuenciales, snapshot de SaleLine, turno único, IGV con factor 1.18. 10 funciones implementadas verificadas contra planificación — todas respaldadas por HU/RN/decisión. Regresión total: **559/559 OK** (78.4s). [Suite de prueba](../../r1-pmv/tests/test_audit14c_edge_cases.py).

Excluidos: Selenium visual (opcional, segunda pasada); concurrencia PostgreSQL (etapa 15). La etapa 14 queda EJECUTADA en primera pasada con los tres sublotes 14-A, 14-B y 14-C.

## Registro anterior14-D · 13/11/2026 Lima

La cadena nominal nueva fue ejecutada porChrome real en SQLite temporal. ADMIN creó categoría/producto/proveedor, ALMACENERO registró10 unidades en dos lotes, VENDEDOR abrió100 y cobró14.20 con vuelto5.80, ALMACENERO registró merma1, ADMIN observó5 unidades y la venta, VENDEDOR cerró114.20 con diferencia0. Se observaron rechazos de rol, estado, fecha, efectivo y merma con huellas de negocio iguales.

Las conclusiones anteriores de14-A/B/C permanecen como antecedentes.14-D corrigió sus atribuciones deHU/RN, la omisión de navegador y la explicación del falloC16. La corrida previa fue558/559 y la final560/560. El inventario80 CA conserva49 PARCIAL,2 INCUMPLE y29 NO EJECUTADO, con muestra nueva vinculada a50. Ninguna HU completa se aprueba por extensión.

HEAD7816d3328115cf5aa5bcdd0985fffd795b3ae084. Build186 archivos957c697258a5545eac4c77d1aba2660bd27e1647053957de2a827f37308751f7.08finale8acd6d39ce5fc5c526d2dfa8c326f2c19b0f46ef032c6b0245bd89ac3644847. La planificación conserva74 HU/287 criterios y añadeCP-INTEGRACION-ROLES-001 para112 casos escritos.07/09/03 e índice regenerados,02/14/16/21coherentes con el corte.

El cursor14-E-KARDEX-01 comienza con18 unidades/promedio3, ocho vencidas y diez vigentes, recepción de 10 a 6 y salida1. Verificar28/4.0714 y luego27/4.0714 con costo de salida preservado, antes de abordar asignaciones durables y saldos/filtros de Kardex. [Inventario](soporte/14-D-inventario.md) · [Disposiciones](soporte/14-D-disposiciones.md) · [Navegador](evidencias/14-D-20261113/navegador/RESUMEN.md) · [Servidor](evidencias/14-D-20261113/servidor/INFORME.md) · [Verificación final](evidencias/14-D-20261113/validacion-final.json).

## Registro anterior14-E · 13/11/2026 Lima

Primera pasada, alcance acotado de costo/valoración, sin declarar terminados otros módulos.08finalSHA256 `ddadb1091e8501a00c0ae9ff9da212bce65446000131f137cede389ebc5313ad`; build188archivos `ffa605bad0356759c5f1d21ce88f556fd79e07760ebcfdbae516ca6f132b1ddd`. HEAD se conserva.74HU,287criterios,112casos escritos.

El runner pasó11/23→23/23; Chrome23 checkpoints con base ficticia nueva;566/566regresión sin cambios durante ejecución. La migración nullable conserva costo desconocido de bajas/ajustes antiguos. Recepción usa físico incluidas unidades vencidas; salidas conservan promedio y snapshot; agotamiento pone promedio0. Rechazo de ajusteQ0 sin costo fiable no muta. C-01..03 DOC-03AH cumplen en muestra secuencial y C-04 queda parcial por PG/caída; no se transforma esto en aprobación de las3HU. El inventario12CA conserva2CUMPLE en muestra y10PARCIAL.

Se actualizaron08 y vistas07/09/03, diseño02, tareas16 y contexto14/21/continuidad. Asignaciones, recepción propia y Kardex quedan en14-F; diagnóstico operativo y regularización requieren hechos del negocio. Próximo caso exacto A3/B7 vender4, persistir asignacionesA3/B1 y preservar historia desconocida. [Informe](ETAPA-14.md#vigente-14-e) · [Inventario](soporte/14-E-inventario.md) · [Disposiciones](soporte/14-E-disposiciones.md) · [Servidor](evidencias/14-E-20261113/servidor/INFORME.md) · [Navegador](evidencias/14-E-20261113/navegador/RESUMEN.md) · [Validación](evidencias/14-E-20261113/validacion-final.json).

## Registro anterior14-F · 13/11/2026 Lima

Primera pasada.08finalSHA256 `8d4a7cbede73eac5b09524363e35d4780dc91d8e25ba6fa8f62de32a66c9984c`, build190archivos `7630c859296fd71dd4607133a461165e1b2d012d5679190652c5e0522bf4fa93`, HEAD `7816d3328115cf5aa5bcdd0985fffd795b3ae084`. La selección conserva74HU,287criterios y112casos escritos, con estados de ejecución parcial actualizados.

El runner5/12→12/12 demostró la brecha y su corrección. Las ventas nuevas guardan asignacionesA3/B1 oA3/B2, vendedor/caja y posición. Legado sin información mantieneNULL y aviso. Sale representa el ingreso de efectivo por venta conforme a la equivalencia aceptada en08 y comprobada con cierre/reenvío/rollback. Ocho tests nuevos cubren ocho puntos de fallo postwrite y migración. La primera suite572/573 identificó una fixture de constancia incompleta. La final574/574 pasó con fuentes estables.

Chrome verificó12checkpoints específicos y44en la cadena completa desde maestros hasta cierre. En el inventario14CA,2cumplen en muestra,11sonparciales y1noejecutado en14-F. Los cinco criterios complementarios y la dependenciaKardex tienen clasificación propia. Recepción propia y Kardex completo permanecen abiertos. Próximo caso carga10@3, recepciónC10@6→20@4.5000 y otraC5@8→25@5.2000, referencias distintas y reintento sin duplicar.

[Informe](ETAPA-14.md#vigente-14-f) · [Inventario](soporte/14-F-inventario.md) · [Disposiciones](soporte/14-F-disposiciones.md) · [Servidor](evidencias/14-F-20261113/servidor/INFORME.md) · [Navegador](evidencias/14-F-20261113/navegador/RESUMEN.md) · [Validación](evidencias/14-F-20261113/validacion-final.json). Las otras etapas conservan sus límites y el estado de segunda pasada sigue pendiente.

## Registro anterior14-G · 13/11/2026 Lima

Primera pasada.08finalSHA256 `fc69a8e9641f8c9c21c6356300fcd84bb3ad9e4ca62edc4c49ae90cd2832e59c`;build194 `f6ca27baf3813bf8806d449269623e0e9d293e8000dee4cfd83d45dd038cb11c`;HEAD7816d3328115cf5aa5bcdd0985fffd795b3ae084.74HU/287criterios/112casos escritos.20archivos del producto cambiaron, con fuente anterior preservada.

La evidenciaChrome anterior mostró UUID ignorada, constancia de carga compartida, segunda entrega del mismo lote rechazada y nombres históricos variables. AhoraR1/R2 conservan origen y cantidad; el reenvío igual devuelve la misma recepción y divergencia rechaza. Carga10@3,recepciónC10@6 yC5@8 dejan25@5.2000; venta22/merma1 dejan2, apertura100+cobro220=cierre320. La cadena general repite altas porADMIN hasta cierre114.20 en base separada.

Dieztests nuevos,584/584regresión final estable,23+44checkpointsChrome. Se corrigió pérdida de triggerSQLite y presupuesto de consultas, además de actualizar expectativas antiguas al contrato vigente. Los ocho criterios inventariados tienen6CUMPLE en muestra y2PARCIAL. No se cierraHU completa ni se extrapola aPG o datos operativos. Siguiente14-H-KARDEX-SALDOS-01:saldo cronológico,filtros,paginación y tratamiento de origen incompleto.

[Informe](ETAPA-14.md#vigente-14-g) · [Inventario](soporte/14-G-inventario.md) · [Disposiciones](soporte/14-G-disposiciones.md) · [Servidor](evidencias/14-G-20261113/servidor/INFORME.md) · [Navegador](evidencias/14-G-20261113/navegador/RESUMEN.md) · [Validación](evidencias/14-G-20261113/validacion-final.json).


## Registro anterior14-H1 · 13/11/2026 Lima

Primera pasada.08final `1dac15a067dd0143d7b118d530f1fa222240455ec2d7d42eae83761f584fe597`;build196 `f9a593aacbd4cd5a0c753d672b5e06c1ada3dd21fb8a2f16b68009ee03f866aa`;HEAD se conserva.74HU/287criterios/113casos escritos. Se preservaron evidencia y producto previos, se corrigió historia de carga nueva y se revalidó el recorrido completo.592/592regresión;16+44+23checkpointsChrome con cobertura solapada.2CUMPLE en muestra,7PARCIAL,3INCUMPLE entre12criterios. Cursor14-H2-KARDEX-SALDOS-01. [Informe](ETAPA-14.md#vigente-14-h1) · [Validación](evidencias/14-H-20261113/validacion-final.json).


## Registro vigente14-H2 · 14/11/2026 Lima

Primera pasada.08final `d2e03f10c190cf6a631152b35fa110d863d0fb3276723f6e7e95e8a0451ffa4a`;build198 `3bed2cd9e85e61dfe2dae607e438a83be911950ec328de59ac596b407155b1f6`.74HU/287criterios/113casos.6CUMPLE enmuestra,1PARCIAL;20+44observacionesChrome,604/604regresión. Fuentes anteriores preservadas yvistas regeneradas. Cursor14-I-MERMA-01; etapanocompleta. [Informe](ETAPA-14.md#vigente-14-h2) · [Validación](evidencias/14-H2-20261114/validacion-final.json).
