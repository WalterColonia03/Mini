# Estado general vigente de auditorías · 13/11/2026 (actualizado 14-C)

> **Fuente funcional principal:** [08 · planificación unificada](../../08_Historias_de_Usuario.md). Las fichas, RN y contratos de08 definen lo esperado; este documento conserva su papel de contexto, diseño, ejecución o evidencia. Las vistas07/09/03 se derivan de08.


Esta tabla sustituye como estado actual las notas anteriores. [Estado anterior íntegro](conciliacion_20261112/BASELINE/auditoria_por_etapas/resultados/ESTADO_GENERAL.md) · [Mapa consolidado](conciliacion_20261112/CONSOLIDACION.md) · [Encargos](conciliacion_20261112/ENCARGOS.md) · [Verificación nueva](conciliacion_20261112/VERIFICACION.md).

La etapa 13 está **FINALIZADA en primera pasada** para el panel mínimo y sus consultas. La etapa 14 completó los **sublotes 14-A, 14-B y 14-C** con 119 pruebas de integración (42 servidor + 65 HTML renderizado/CT-COHERENCIA-UI + 12 edge cases/comportamiento→planificación) y regresión completa 559/559 OK. **El próximo cursor es etapa 15.** Las etapas 15–17 y la segunda pasada siguen pendientes. Los informes 00–12 conservan sus propios hallazgos. La conciliación y las 434 pruebas SQLite anteriores pertenecen a su corte original. [Cierre 13-B-final](ETAPA-13.md#cierre-13-b-final) · [Informe 14](ETAPA-14.md) · [Antecedente de conciliación](ANTECEDENTE_CONCILIACION_20261112.md).

| Etapa | Fecha del estado | Cobertura | Estado vigente | Bloqueos/decisiones | Próximo cursor |
|---|---|---|---|---|---|
| [00](ETAPA-00.md) Inventario y planificación | 12/11/2026 | Inventario y evidencia del informe/anexos originales | Inventario completo del corte, no aprobación funcional | DOC00-01/05/07/08/09/12/13; matriz219 y catálogo74+8 | Revisión17 de trazabilidad y semántica |
| [01](ETAPA-01.md) Ingreso y bloqueo | 12/11/2026 | Inventario y evidencia del informe/anexos originales | Auditado en muestras; seguridad transversal abierta | Tráfico/admin/retención/logs; correo254/IDNA;5fallos/15min | SEC-15-TRAFICO-01 y SEC-15-OBS-01 |
| [02](ETAPA-02.md) Sesión y personal | 12/11/2026 | Inventario y evidencia del informe/anexos originales | Auditado en muestras; contratos revisados pendientes | Reset/desbloqueo auditado, nombre120, confirmación y concurrencia | DOC-02-04 / SEC-15-CONC-02 |
| [03](ETAPA-03.md) Categorías y productos | 12/11/2026 | Inventario y evidencia del informe/anexos originales | 03-AJ y anexos posteriores contrastados; sin cierre integral | Catálogo/lector aceptados; valoración/recepción/legacy/migraciones pendientes | DOC-03AH-01 / DOC-03AI-01 |
| [04](ETAPA-04.md) Proveedores | 12/11/2026 | Inventario y evidencia del informe/anexos originales | 04-D reconocido; no queda detenido artificialmente en04-C | Revocación muestras04-D; RUC/formato y estado explícito; raw bypass pendiente | DEC-04B-ESTADO-OMITIDO / SEC-15-CONC-02 |
| [05](ETAPA-05.md) Carga inicial | 12/11/2026 | Inventario y evidencia del informe/anexos originales | 05-L vigente; suite integrada elimina fallo heredado | PG17, recuperación postwrite, costos/recepción y despliegue | 05-M / CT-ROLLBACK-01-POST-ESCRITURA |
| [06](ETAPA-06.md) Recepción posterior | 12/11/2026 | Inventario y evidencia del informe/anexos originales | 06-F auditado con conflictos hoy decididos documentalmente | Entrada directa aceptada; recepción propia/costo nuevo sin implementar | DOC-03AI-01 / DOC-03AH-01 |
| [07](ETAPA-07.md) Stock y vencimientos | 12/11/2026 | Inventario y evidencia del informe/anexos originales | Muestras ejecutadas; políticas/volumen pendientes | Alertas activas vs vencidos físicos, filtros y panel mínimo | DEC-07-VENCIDOS-FILTRO / PT-SEARCH-01 |
| [08](ETAPA-08.md) Bajas, ajustes y movimientos | 12/11/2026 | Inventario y evidencia del informe/anexos originales | Parcial frente a HU existentes y contratos revisados | Constancia, lote nuevo, costo/motivo y Kardex completo | RN-05 / DEC-08-KARDEX-COMPRAS |
| [09](ETAPA-09.md) Caja | 12/11/2026 | Inventario y evidencia del informe/anexos originales | EJECUTADA; se rectifica NOEJECUTADO heredado en10–12 | 20 tests y6 casos PG históricos; Chrome67 funcionales+1control; checks/topes/orden pendientes | PROP-09-DB-01 / DEC-11-TOPE-EFECTIVO-FORM |
| [10](ETAPA-10.md) Preparación y bloqueo de puesto | 12/11/2026 | Inventario y evidencia del informe/anexos originales | Borrador auditado; bloqueo300s no implementado | VEN01a seleccionado antes de piloto; GETprecio/concurrencia/UX | DEC-10-BLOQUEO-INACTIVIDAD / PROP-10-03 |
| [11](ETAPA-11.md) Cobro y exactitud | 12/11/2026 | Inventario y evidencia del informe/anexos originales | Muestras ejecutadas; integridad y política nuevas pendientes | Lotes/snapshots, nuevos descuentos deshabilitados, límites y caída | DEC-11-MODELO-AUDITORIA-VENTAS |
| [12](ETAPA-12.md) Constancias e historial | 12/11/2026 | Inventario y evidencia del informe/anexos originales | Muestras y nueva comprobación parcialPG; sin cierre integral | Permisos/orden/paginación/UX; filtrosCA02 y detalleCA03 conciliados | DEC-12-ORDEN-LINEAS-RECIBO / PROP-12-CAJA-HIST-CHROME-VENDEDOR |
| [13](ETAPA-13.md#cierre-13-b-final) Tablero, reportes y futuro | 13/11/2026 | Tres roles en navegador, cobro UI, recarga, vacíos, fallos, permisos, D11 y teclado. Servidor 100/100 por fixture y regresión 160/160. PG18.4 37/37 y 6/6 pruebas, con concurrencia y volumen sintético. Los conjuntos se solapan. | **FINALIZADA en primera pasada para el panel mínimo y sus consultas** | H13-01 a H13-08 y D11 resueltos en el alcance. PG17 y SLA productivo pendientes de validación propia. 16 HU/39 CA de DASH/REP/CONF siguen futuras. | 14 · Integración por roles, EJECUTADA |
| [14](ETAPA-14.md) Integración por roles | 13/11/2026 | 119 pruebas (42 servidor E2E + 65 HTML/CT-COHERENCIA-UI + 12 edge cases/comportamiento→planificación); regresión 559/559 OK; 25 rutas × 4 niveles; 19 HU cruzadas; 10 RN; 15 headings; 3 dashboards; menú lateral × 3 roles; login + 403 + accesibilidad; 10 funciones comportamiento→planificación; PROP-14-03 verificada | **EJECUTADA — sublotes 14-A + 14-B + 14-C completados** | Concurrencia PG en etapa 15; Selenium visual opcional en segunda pasada | 15 seguridad/concurrencia |
| 15 Seguridad, concurrencia, despliegue y recuperación | 13/11/2026 | Prompt disponible; primera pasada pendiente | NO EJECUTADA | EntornoPG, permisos, sesiones, tráfico, logs, respaldo y recuperación | Pruebas aisladas; CT-ROLLBACK, SEC15 y S1-OPS/CI con evidencia propia |
| 16 Normativa y viabilidad | 13/11/2026 | Prompt disponible; primera pasada pendiente | NO EJECUTADA | Datos reales y aplicabilidad del canal fiscal/protección de datos | Fuentes oficiales vigentes y límites de las promesas del software |
| [17](ETAPA-17.md) Conciliación y evaluación de cierre | 13/11/2026 | Registro de continuidad; auditoría pendiente | NO EJECUTADA | Requiere resultados13–16 y conciliación de todos los tramos | Ejecutar prompt17; después preparar segunda pasada01–17 |

## Regla de continuidad

El orden de resolución va por integridad/costo/recepción/venta, permisos/seguridad, consultas/UX y evidencia de despliegue. No es obligatorio reejecutar una etapa histórica completa para investigar un caso concreto; conservar su ID y alcance. Los futuros siguen futuros. No declarar cierre por aceptar políticas, generar documentos o aprobar una suite parcial.

## Unificación documental de este corte

[Revisión y registro anterior](fuente_unica_20261112/REVISION.md) · [Validación estructural anterior](fuente_unica_20261112/VALIDACION.json). El corte12/11reunía74fichas completas,219CA base,60criterios de contratos,4J-CA y4criterios de veracidad visible, con110casos escritos. El sublote13-A conserva HUs, criterios y selección; añade CP-DEC-07-VENCIDOS-FILTRO-002 con ejecución parcial:111casos escritos y287criterios. [Validación13](evidencias/13-A-20261113/planificacion/validacion.json).07/09/03 se regeneraron desde08SHA256 `5735fb283b70bca02ed551e0000c72df2025eaef9b977607b1e4a2b890e5a1d9`;02/14/16/21 se sincronizaron. Casos escritos no equivalen a ejecuciones aprobadas.

## Registro del sublote13-A

[Informe y cursor exacto](ETAPA-13.md) · [Estado antes de13](evidencias/13-A-20261113/estado-general-antes.md) · [Build final](evidencias/13-A-20261113/build-final.json). HEAD `7816d3328115cf5aa5bcdd0985fffd795b3ae084`, build local `f0918e86fad95a023c7a5fafe08ab6ebe8a61109a31669b349a5f94f13831e74`. Corregidos filtro de días fuera de rango, badgecrítico en inactivos, promesa de reportes, claridad de fecha/actualización y consulta por rol. Servidor revalidado; capturas iniciales no aprueban interfaz final. Los futuros CONF/DASH/REP siguen futuros. Las dependencias03/07/09/11/12solo tienen la revalidación acotada descrita; no se actualizan sus filas a cerrado.

## Secuencia de continuación confirmada

Primera pasada:13→14→15→16→17. Después:actualizar00 y ejecutar segunda pasada01–17 contra versiones identificadas de planificación y producto, conservando evidencias de la primera. [Guía de trabajo y aceptación](../CONTINUIDAD_Y_SEGUNDA_PASADA.md). Este estado corrige la clasificación prematura de17 y el nombre de16; no borra ni reetiqueta como ejecutadas pruebas históricas.

## Antecedente parcial 13-B · 13/11/2026, antes del cierre visual

Servidor/PostgreSQL y documentación completados dentro del alcance del panel mínimo; etapaPARCIAL por bloqueo externo visual. [Informe y cursor](ETAPA-13.md#9-continuación13-b-13112026--primera-pasada) · [Bloqueo y recuperación intentada](soporte/13-B-navegador.md) · [Disposiciones](soporte/13-B-disposiciones.md). Corregidos corte de métricas en una sentencia, fechas del historial, enlaces/textos y mensaje500.08final f4f6f82177685bfd492f5473bed945cd9add67b2a700639f40fe7444d449bc48; build99686b95a2c1d612bd4944a6cc0e7d16ab601c3f73d142e546a5f0c8ca30e215. Vistas07/09/03regeneradas;02/14/16/21coherentes;CP002PARCIAL. No se ejecutaron14ni segunda pasada.

## Cierre vigente 13-B-final · 13/11/2026 Lima

La revalidación visual resolvió el bloqueo del registro anterior en el mismo build de 183 archivos. CP002 quedó verificado para el panel mínimo. La venta única de S/7.10 y el cambio de lote de 3 a 1 persistieron tras recargar. El cierre conserva las ejecuciones anteriores y deja disponibles la constancia, los datos de contraste, las comparaciones por archivo y la validación de las vistas derivadas. [Navegador final](soporte/13-B-final-navegador.md) · [Disposiciones finales](soporte/13-B-disposiciones.md) · [Validación documental](evidencias/13-B-final-20261113/planificacion/validacion.json).

## Registro del sublote 14-A · 13/11/2026 Lima

[Informe y cursor exacto](ETAPA-14.md) · HEAD `7816d3328115cf5aa5bcdd0985fffd795b3ae084` · Build (231 archivos) `1c3325902c4a948662eef111dec9ecf62e9bec57f568d9d3173c6bae7b7ac165` · 08 SHA-256 `33d2f17067fec3bb30e018ef49b77d87f84adfd9bafe04adf19161cd286e47a4`.

42 pruebas de integración E2E con Django Client (servidor embebido) sobre base SQLite en memoria. Recorrido ADMIN→ALMACENERO→VENDEDOR→ALM/ADMIN→VENDEDOR. 14 variantes de permisos denegados (403), cambios de estado, vencimiento, idempotencia y efectos cruzados entre módulos. 19 HU cruzadas, 10 RN, 25 rutas verificadas. [Suite de prueba](../../r1-pmv/tests/test_audit14_integration.py).

## Registro del sublote 14-B · 13/11/2026 Lima

65 pruebas de verificación del HTML renderizado por rol (CT-COHERENCIA-UI) con Django Client + assertContains/assertNotContains. Menús laterales, dashboards, tarjetas de acción, headings de 15 páginas, login, páginas 403, accesibilidad (skip-link, lang, aria-label, tabindex). Regresión total: **547/547 OK** (72.7s). 0 incompatibilidades entre roles. 8 hallazgos positivos en el sublote 14-B. [Suite de prueba](../../r1-pmv/tests/test_audit14b_browser_content.py).

Excluidos: Selenium + Chrome visual con interacción real (clicks, JS) — opcional; concurrencia PostgreSQL (etapa 15). La etapa 14 queda EJECUTADA en primera pasada para los sublotes 14-A y 14-B.

## Registro del sublote 14-C · 13/11/2026 Lima

12 pruebas de edge cases y auditoría comportamiento→planificación: PROP-14-03 verificada (admin desactiva producto/categoría con borrador activo → checkout rechaza), búsqueda filtra activos y no vencidos, descartar borrador sin efecto en stock, constancia por rol, cierre de caja con diferencia, correlativos secuenciales, snapshot de SaleLine, turno único, IGV con factor 1.18. 10 funciones implementadas verificadas contra planificación — todas respaldadas por HU/RN/decisión. Regresión total: **559/559 OK** (78.4s). [Suite de prueba](../../r1-pmv/tests/test_audit14c_edge_cases.py).

Excluidos: Selenium visual (opcional, segunda pasada); concurrencia PostgreSQL (etapa 15). La etapa 14 queda EJECUTADA en primera pasada con los tres sublotes 14-A, 14-B y 14-C.
