# 21. Alcance y diferencias vigentes

**Objetivo vigente · 20/11/2026.** Demostrar el minimarket por HTTPS público con efectivo, digital y mixto, QR estático de una cuenta Yape propia y cero comisión de cobro. El cajero atiende sin el dueño en el flujo ordinario. La dirección por capas está aceptada; el puente Android y la asociación al pedido requieren ensayo. Para devoluciones quedan por decidir canal financiado, permisos y límites. [Contrato funcional](08_Historias_de_Usuario.md#contrato-CT-ENTREGA-ACADEMICA) · [Diseño y ensayo](auditoria_por_etapas/PAGOS_YAPE_Y_MIXTOS.md).

Brecha al 20/11. El checkout inspeccionado en r1-pmv registra efectivo. El ingreso digital, el desafío, las aplicaciones parciales y los reintegros aún requieren implementación y prueba. Una imagen QR en el proyecto no acredita titularidad o integración. Caja única y consulta del vendedor limitada a su turno abierto. 01-K conserva evidencia local y 02-E permanece PARCIAL. [Detalle del corte documental](auditoria_por_etapas/resultados/REVISION-PROMPTS-YAPE-20261120.md).

**Antecedentes inferiores:** conservan fecha/build y alcance anterior; no sustituyen el objetivo ni estado de este corte.

## Resultado vigente de Etapa01

Etapa01 cerrada para su demostración local:2HU,7CA y4CP de ingreso/bloqueo, con límites de cobertura del [informe01K](auditoria_por_etapas/resultados/ETAPA-01.md#vigente-01-k). `139/139` identity, `79/79` literales Chrome y `5/5` escenarios PostgreSQL18.4. La regresión ampliada obtuvo663/666: tres fallos externos se conservan y se remiten a sus etapas; no se declara cierre del sistema completo. Se elimina el agregado01J y se precisa el mensaje máximo254 sin cambiar el límite ni agregar reglas.

## Revalidación Etapa 07 (`07-B` · 14/11/2026 Lima)

Sin editar producto ni autorizar cambios en `r1-pmv/` (`f0d6fa81...` / `c7bfe1fa...` idénticos en tramo `07`), se revalida `H13-02` resuelto en `/productos/`, `/inventario/stock/` y POS, corte único de sentencia en `/inicio/` (`_dashboard_summary`) y separación `FUTURO (W)` de `HU-DASH-03` y `HU-REP-01..09`. Se confirma vigente la brecha funcional **`DEC-07-VENCIDOS-FILTRO` / `HU-PROD-06/CA-03`** (`/productos/vencimientos/?dias=7` mezcla vencidos y próximos en una tabla única) y la medición **`PT-SEARCH-01`** en PostgreSQL `18.4` (`2,001`/`20,002`): índice parcial (`648 kB`) acelera SQL (`30–120 ms`), pero paginación HTML y agregación SQL (`PROP-07-ESCALA-PAGINACION-01`) son requisito previo para bajar latencia HTTP desde `3,56–3,63 s`. Quedan pendientes `PG 17`, SLA operativo, móvil horizontal `390px` (`PROP-07-MOBILE-01`) y cursor `07-C-DEC-07-VENCIDOS-FILTRO` ([Informe 07-B](auditoria_por_etapas/resultados/ETAPA-07.md#reval-07-b-20261114)).

## Corte vigente14-CIERRE · 14/11/2026 Lima

Se resuelven los pendientes funcionales propios de14: ajustes con historia y reenvío persistente, lote nuevo de origenAJUSTE, costo documentado desde físico0 y cierre acumulado válido. Precio ambiguo y recuperación histórica corregidos. Los157checkpoints y634tests no equivalen a todos los80CA de módulos dependientes; estado por elemento en cobertura14-CIERRE.15–17 y segunda pasada siguen pendientes.

[Informe y evidencia](auditoria_por_etapas/resultados/ETAPA-14.md#cierre-14) · [Ajustes](auditoria_por_etapas/resultados/soporte/14-CIERRE-ajustes.md) · [Dinero](auditoria_por_etapas/resultados/soporte/14-CIERRE-dinero.md). Las secciones fechadas anteriores se conservan como antecedentes.

## Revalidación acotada 02-E (segunda pasada · 14/11/2026 Lima)

Implementado y verificado en `identity/` (`check=0`, `makemigrations=0`, `652/652 OK`, Chrome `1366×768` + `390×844` `29/29` + `10` acciones auditadas, `5/5` PostgreSQL `18.4`; `r1_pmv.sqlite3` intacta): `H02E-01` (`/salir/` condicional y atómico), `H02E-02` (`/empleados/<uuid>/estado/confirmar/` y responsividad móvil), `H02E-03` (preservación de bloqueo `LoginAttempt`, purga de sesiones en reset, `unlock_account` explícito auditado) y `H02E-04` (`IdentityAuditEvent` `0006` + `identity.audit` sanitizado con `persist_db=False` en rechazos HTTP). Siguen `FUTURO / NO DISPONIBLE` (`0` rutas/UI): `HU-AUTH-04a/04b/05`, `HU-USR-06` y `HU-LOG-01`; permanecen abiertos `DOC-01-06/C-01..02` en `/admin/login/`, sumidero/retención `SEC-15`, estudio IDNA (`PROP-02E-IDNA-01`) y `PG 17` ([Informe 02-E](auditoria_por_etapas/resultados/ETAPA-02.md#vigente-02-e)).

## Revalidación puntual Etapa 06 · 14/11/2026 Lima

Sin modificar código ni migraciones en esta sesión: revalidado tramo `inventory` de recepción posterior (`DOC-03AB-01` política directa en corte R1 con autorización externa, `DOC-03AH-01`, `DOC-03AI-01` y `DEC-05-LOTE-ESPACIOS`) con evidencia aislada PostgreSQL `18.4` (`10/10`) y Chrome escritorio+móvil (`93/93`), manteniendo `HU-SOL-01..05b` y `HU-DASH-05` separados como `FUTURO (W)` con `0` rutas/plantillas/servicios. Se registran hallazgos visuales móviles/UI como recomendaciones sin aplicar y permanecen abiertos `PG 17`, caída real `SIGKILL` y diagnóstico/migración operativa ([Adenda ETAPA-06](auditoria_por_etapas/resultados/ETAPA-06.md#adenda-06-20261114)).


> **Fuente funcional principal:** [08 · planificación unificada](08_Historias_de_Usuario.md). Las fichas, RN y contratos de08 definen lo esperado; este documento conserva su papel de contexto, diseño, ejecución o evidencia. Las vistas07/09/03 se derivan de08.


> **Vigente: 12/11/2026 · conciliación documental autorizada.** Requisito aceptado no equivale a implementación o verificación. [Mapa y decisiones](auditoria_por_etapas/resultados/conciliacion_20261112/CONSOLIDACION.md) · [Encargos verificables](auditoria_por_etapas/resultados/conciliacion_20261112/ENCARGOS.md) · [Versión anterior íntegra](auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/21_Alcance_Actual_y_Diferencias.md). Jira no forma parte de este seguimiento.

## Lo seleccionado y lo comprobado

El corte del 12/11 reunió 33 HU seleccionadas, 219 CA base en el catálogo completo, 60 criterios de contratos, 4 criterios J de categoría, 4 de CT-COHERENCIA-UI y 110 casos escritos. En ese corte pasaron 434 pruebas automáticas integradas en SQLite, el check y el dry-run de migraciones. Se revalidó una muestra de historial e idempotencia en PG18.4. La actualización del 13/11 añade un caso de panel mínimo. La selección se conserva y la nueva matriz derivada de 08 registra 111 casos escritos.

## Brechas prioritarias verificadas por inspección

| Área | Comportamiento actual / fuente | Requisito vigente | Trabajo |
|---|---|---|---|
| Entrada |14-G guarda recepción propia,UUID/huella,referencia y líneas históricas;sin backfill de legado |Entrada directa con identidad/idempotencia;concurrencia y datos operativos pendientes|DOC03AB/AI|
| Valoración |14-E corrigió promedio físico, salidas y agotamiento; baja/ajuste capturan costo nuevo. Legado operativo sin regularizar | Promedio móvil y snapshots conforme RN-14; faltan costo documentadoQ0 y garantías concurrentes | DOC03AH |
| Venta |14-F persiste asignaciones y snapshots vendedor/caja, con posición por línea y legado explícito | RN25/26, integridad concurrente y recuperación pendientes15 | DEC11MODELO |
| Descuento |14-D suspendió descuento discrecional nuevo y preservó reintento histórico. Revalidado en suite14-F | Conservar fotografía histórica y rechazar nuevos descuentos | DEC11DESCUENTOS |
| Bloqueo de puesto | RN22/HUVEN01a no implementado | Servidor bloquea300s, reautenticación | DEC10BLOQUEO |
| Baja/ajuste |14-D corrigió causa y14-E capturó costo. Faltan constancia dedicada/nuevo lote/costo documentadoQ0 | Causa real, constancia y ajuste fiable no vendible | RN05, INV02/03 |
| Movimientos |14-F muestra lotes de venta y cobertura histórica. Saldo/filtros/paginación pendientes | INV04 completo con legado explícito | DEC08KARDEX |
| Seguridad | Límites tráfico/eventos/admin técnico/retención con brechas | Contratos y medición15 | DOC01/02,SEC15 |
| Historia/caja |14-F fija orden de líneas. Empates de turnos y límites acumulados conservan pendientes | Posición persistida/desempate/topes coherentes | DEC11TOPE/DEC12ORDEN |

Contrato vigente y casos:08. Mapa, alternativas y fuentes históricas: CONSOLIDACION; ENCARGOS remite a08. Estas filas no autorizan cambios de código ni DB. Los costosNULL, identidadGTIN antigua y recepción incompleta no se inventan por migración.

## Rectificaciones de auditoría

Etapa09 sí tiene informe y evidencia; se corrige el NOEJECUTADO que arrastraban10–12. Chrome09 contiene67 comprobaciones funcionales más control cero_page_errors=68, no70. 04-D tiene evidencia de revocación y deja el caso raw sin petición/servicio fuera de muestra. El fallo de Product._state.adding se corrigió en05-L y está integrado en434 pruebas; no mantenerlo abierto por informes antiguos. Un empate de orden de turnos sigue siendo problema de diseño aunque una repetición pase.

05-L prueba interrupción HTTP mientras espera bloqueo antes de escritura; post-escritura/COMMIT/motor siguen pendientes. Soporte12PG usa Client de Django en hilos, no socketsHTTP; la nueva corrida lo describe correctamente. Filtros de VEN05b/CA02 y apertura de detalle/CA03 no se contradicen.

## Fuera de evidencia actual

Al comienzo del 13/11, la primera pasada había llegado hasta la etapa 12. El nuevo sublote del panel mínimo de la etapa 13 contrasta las cifras y permisos, con evidencia por build y pendientes propios. Las 16 HU de DASH/REP/CONF conservan su clasificación futura. Siguen pendientes las auditorías 14–17 y la actualización de 00 para la segunda pasada. PG17, CI, despliegue real, recuperación, dispositivos físicos, volumen y aplicabilidad normativa conservan los límites de sus respectivos informes. El XLSX sigue ausente. [Etapa 13](auditoria_por_etapas/resultados/ETAPA-13.md).

La continuación13-B conserva esa selección y corrige dentro del panel mínimo y consultas enlazadas las ambigüedades de historial/umbral/recepción, mensajes de fallo, validación de fechas y mezcla de commits demostrada en PostgreSQL. Las mediciones sintéticas no representan volumen real ni un SLA; probar18.4 no valida automáticamente el motor objetivo17. El bloqueo de navegador del corte intermedio se conserva como antecedente y quedó superado: 13-B-final acredita tres roles, cobro completo por interfaz en fixture independiente, persistencia/recarga, vacíos/fallos, filtros, permisos e interacción del mismo build. Etapa13 FINALIZADA en primera pasada para el panel mínimo y consultas acotadas, sin cerrar HUs futuras ni otros módulos. La continuación14-D se documenta debajo; segunda pasada pendiente. [Disposiciones y límites13-B](auditoria_por_etapas/resultados/soporte/13-B-disposiciones.md) · [Navegador final](auditoria_por_etapas/resultados/soporte/13-B-final-navegador.md).

## Diferencias revalidadas14-D · 13/11/2026

El corte añade CP-INTEGRACION-ROLES-001 y mantiene74 HU y287 criterios, ahora112 casos escritos. El recorrido conectado de navegador creó maestros y existencias, cobró14.20, contrastó10−4−1=5 unidades y cerró114.20 con apertura100. Se revalidaron permisos, estado comercial, vencimiento y rechazos mediante UI y solicitudes directas. 44 checkpoints Chrome,18 variantes Client y560 pruebas integrales tienen ámbitos distintos y solapados.

Quedaron corregidas la oferta de descuento discrecional nuevo, las causas de merma incompatibles con fecha y la selección aleatoria de venta en C16. Continúan incompletos el costo de salida/valoración RN14, asignaciones históricas de venta por lote, origen propio de recepción, Kardex con saldos/filtros/paginación, constancia dedicada de merma, topes acumulados y otras condiciones inventariadas. La evidencia normal con costo2.0000 en ambos lotes acredita esa fixture.

La etapa 14 permanece PARCIAL, con cursor14-E-KARDEX-01. Los informes de otros módulos y las etapas 15–17 conservan sus estados. [Inventario de80 CA](auditoria_por_etapas/resultados/soporte/14-D-inventario.md) · [Informe vigente](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-d).

## Diferencias revalidadas14-E · 13/11/2026

Sustituye únicamente la brecha de cálculo/captura de costo descrita en el corte14-D. Recepción18@3(incluidas8vencidas)+10@6 produce28@4.0714; venta/baja/ajuste preservan promedio y costo histórico; físico0 deja promedio0. Campo nullable de baja/ajuste conservaNULL de legado. Se rechazó ajuste+Q0 sin costo fiable.

La muestra Chrome23 checkpoints cerró caja108,00 con venta8,00 y apertura100,00; servidor23/23 y regresión566/566. Se conservan74HU,287criterios y112casos escritos; CP-DOC-03AH-01-001 queda EJECUTADO PARCIAL. Asignaciones, recepción propia, Kardex, constancia de merma, lote nuevo/costo documentado de ajuste, concurrencia y demás contratos conservan pendientes. Cursor14-F-ASIGNACIONES-01. [Informe vigente](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-e) · [Disposiciones](auditoria_por_etapas/resultados/soporte/14-E-disposiciones.md).

## Diferencias revalidadas14-F · 13/11/2026

Venta de4 desde A3/B7 guarda asignaciones3/1, saldo6 y costo histórico. ContratoA3/B2 vende5, deja0, guarda costo3 y cierre150 tras apertura100. Constancia conserva nombres/caja/orden después de editar maestros. El legado sin datos muestra ausencia o cobertura parcial. Se verificó la equivalencia de Sale como ingreso de efectivo por venta en R1.

Servidor12/12, ocho pruebas nuevas, regresión574/574, Chrome12 checkpoints específicos y44de cadena completa. Los conjuntos se solapan.08 sigue con74HU,287criterios y112casos escritos, con contratos ejecutados parcialmente. La etapa14 quedaPARCIAL por DOC-03AI, saldo/filtros/paginación del Kardex, constancia de merma y condiciones abiertas. Cursor14-G-RECEPCIONES-01. [Informe](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-f) · [Disposiciones](auditoria_por_etapas/resultados/soporte/14-F-disposiciones.md).

## Revalidación14-G · 13/11/2026 Lima

StockReceipt/Line/Counter resuelven identidad propia,reenvío y fotografía del ingreso nuevo. Permiten entregas reales distintas del mismo lote comercial con fecha coherente. Constancia y consulta conservan historia aunque cambien maestros o se ajuste/salga stock. Regresión584/584 estable,23checkpoints de recepción conectada y44de cadena general;fuentes y evidencia preservadas. MigraciónSQLite conserva filas y triggerFEFO. PostgreSQL/caída,dato operativo,carga inicial histórica,Kardex completo y constancia de merma permanecen pendientes. Cursor14-H-KARDEX-SALDOS-01. [Informe](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-g).


## Diferencia verificada14-H1

La historia de nuevas cargas iniciales ya no depende de nombres actuales ni capacidad mutable deLot. Se conservan cabecera y líneas originales y se distingue legado. Corrección técnica dentro deDOC03AI/INV01a ya seleccionados, sinHU nueva ni cambioMoSCoW; CP-HU-INV-01a-003 aumenta casos escritos a113.592/592regresión y16+44+23checkpointsChrome acreditan muestras conectadas, no cierre completo. Saldo/orden/filtros/paginaciónKardex siguen incumplimientos en14-H2-KARDEX-SALDOS-01; merma,PG,datooperativo y demás pendientes se conservan.

[Informe14-H1](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-h1) · [Fundamento y límites](auditoria_por_etapas/resultados/soporte/14-H-disposiciones.md).


## Diferencia verificada14-H2 · 14/11/2026

Kardex yaimplementa ordenascendente,saldo conocido,filtrosypaginación25. Si no puedereconstruir origen/conciliarporlote, muestraNo disponible; se evita inventar pasado desdeactual. Se mantieneINV04seleccionado yHUINV05/06futuras;no nuevaHU/criterio ni ampliación comercial.6criterioscumplen enmuestra y1parcial;604/604suite,20+44Chrome. Etapa14parcial,cursor14-I-MERMA-01; constanciademerma,historiaajuste,PG/volumen/operaciónpendientes.

[Informe14-H2](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-h2) · [Decisiones](auditoria_por_etapas/resultados/soporte/14-H2-disposiciones.md).


## Continuación14-I · 14/11/2026 Lima

Se resolvieron falta de constancia de merma, duplicación de unaUUID al cambiar sesión y lectura de autor/lote actuales como historia. Los registros nuevos preservan fotografía y los anteriores muestran ausencia explícita. Primera pasada14-I:6/7 criterios principales cumplen en muestra y1parcial por concurrencia.614/614 servidor,26+44 Chrome. Sigue pendiente historia de ajustes, lote nuevo/costo documentado, garantíasPG y operación. No se cierra release ni otros módulos.

[Informe14-I](auditoria_por_etapas/resultados/ETAPA-14.md#vigente-14-i) · [Disposiciones](auditoria_por_etapas/resultados/soporte/14-I-disposiciones.md).

## Revalidación Etapa 12 (12-B) · 14/11/2026 Lima

Se completó en muestra aislada el tramo `sales` constancia/historiales y `cash` historial/actas (`HU-VEN-02a`, `05a`, `05b`, `HU-CAJA-05` y contratos `DEC-12-*`): desempate determinista de turnos (`-opened_at`, `-id`), paginación de `25` filas con preservación de filtros y totales globales filtrados, enlaces directos de historial para `VENDEDOR`, título «Acta de cierre», revisión obligatoria tras cambio de precio antes de cobrar (`DEC-12/C-04`), tolerancia móvil `390×844` sin solapamiento en `.receipt-table`, recuperación por reintento idempotente (`draft=None` y borrador nuevo activo) y revocación de sesión por desactivación UI en SQLite (`85/85` del tramo), Chrome (`12/12` + `9` layouts) y PostgreSQL `18.4`. `HU-VEN-02b/02c/03/08` (`W` fuera de horizonte) y `HU-VEN-06a..c/07/CONF-01..02` (`W`/futuros) permanecen separados sin botones ni rutas prometidas. En regresión completa (`644` tests), `643/644` pasan y `1` falla en el módulo externo `test_audit14f_allocations` por escritura `IdentityAuditEvent` introducida en `01-F` ante `403`. `PG 17`, SLA real, impresora térmica física y despliegue sobre `r1_pmv.sqlite3` siguen pendientes en Etapa `15`. [Informe 12-B](auditoria_por_etapas/resultados/ETAPA-12.md#vigente-12-b).

## Etapa 02 · entrega de pruebas del 20/11/2026

La demostración de etapa 02 dispone de un proyecto HTTPS aislado con PostgreSQL temporal. El servicio de sesión conserva el bloqueo de la cuenta hasta guardar la sesión. Continúa diferida la suspensión con turno abierto. Receptor y reintegro conservan su alcance de 11/15. [Segunda pasada pública del 20/11](auditoria_por_etapas/resultados/ETAPA-02.md#entrega-02-publica).
