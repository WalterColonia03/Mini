# 3. Matriz de trazabilidad y plan de pruebas de `R1-PMV`

> **Actualización 05/11/2026:** Matriz histórica de planificación de Sprint 1. Los casos son objetivos de prueba, no evidencia de ejecución actual. Jira ya no se usa ni se evalúa en este proyecto; las referencias posteriores se conservan solo como contexto histórico. Véase [Guía de alcance y diferencias](21_Alcance_Actual_y_Diferencias.md).

> **Estado:** planificado. Este documento define cobertura y resultados esperados; no afirma que exista código, que una prueba haya sido ejecutada ni que una Story esté terminada.
>
> **Alcance inmutable:** 9 Stories, 40 Story Points y exactamente 41 criterios de aceptación en Sprint 1. Las 16 Tasks transversales y 51 Subtasks citadas aquí no son historias y no llevan Story Points.
>
> **Regla de evidencia:** todas las evidencias figuran inicialmente como `Pendiente`. Un resultado de simulación textual demuestra coherencia de la planificación, no funcionamiento del software. Los resultados reales se registran en `04_Evidencias.md` y Jira.

## 3.1 Convenciones

| Código | Significado |
|---|---|
| `CA` | Criterio de aceptación numerado en `08_Historias_de_Usuario.md` |
| `RN` | Regla de negocio de `07_Reglas_de_Negocio.md` |
| `DEC` | Decisión de producto/operación de `01_Proyecto_y_Releases.md` |
| `DT` | Decisión técnica de `02_Diseno_Tecnico_R1_PMV.md` |
| `NFR` | Requisito no funcional de la sección 2.14 |
| `AT-*` | Caso automático planificado, unitario o de integración |
| `CT-*` | Caso concurrente/rollback planificado contra PostgreSQL real |
| `MT-*` | Caso manual funcional planificado |
| `ST-*` | Caso de seguridad/autorización planificado |
| `E2E-*` | Recorrido automatizado o manual de punta a punta planificado |
| `EV-*` | Paquete de evidencia esperado; su estado inicial es `Pendiente` |

Una CA puede compartir una Subtask con otras CA. Esto no reduce su obligación de tener al menos un caso automático cuando sea técnicamente automatizable, un caso manual observable y una comprobación por una persona distinta.

Las tablas escriben cada clave de Task/Subtask de forma explícita. No se usan rangos ni abreviaturas que puedan confundirse con una clave distinta al copiar la planificación a Jira.

## 3.2 Cobertura de Tasks transversales

| Task | Resultado verificable | Cubre | Prueba/evidencia prevista |
|---|---|---|---|
| `S1-ARQ-01` | Arquitectura, contratos y decisiones ratificados | `DT-01..DT-15`, todas las HU | Acta real de decisión, revisión de `02` y contrato de rutas (`EV-ARQ-01`) |
| `S1-PLAT-01` | Repositorio, revisión y construcción reproducible | `NFR-08`, todas las HU | Clon limpio, instalación y build repetidos por otro Developer (`EV-PLAT-01`) |
| `S1-CI-01` | Pipeline con análisis, migraciones, pruebas y build | DoD, `NFR-01..NFR-04`, `NFR-08` | URL/log inmutable de una ejecución real (`EV-CI-01`) |
| `S1-DB-01` | Modelo y diccionario trazados | RN de inventario/caja/venta | Diagrama revisado y correspondencia modelo–migración (`EV-DB-01`) |
| `S1-DB-02` | Migraciones crean esquema desde cero | Integridad de las 9 HU, `NFR-08` | `AT-DB-01`: base vacía → migrate sin pasos manuales (`EV-DB-02`) |
| `S1-DB-03` | Constraints, FK e índices críticos existen | `NFR-01`, `NFR-02`, `NFR-04` | `AT-DB-02`: introspección + intentos inválidos (`EV-DB-03`) |
| `S1-DB-04` | Seeds idempotentes de categoría, caja, roles y 3 cuentas | AUTH/PROD/CAJA | `AT-DB-03`: seed dos veces sin duplicar (`EV-DB-04`) |
| `S1-DB-05` | Reset exclusivo de local/CI y fixtures reproducibles | Todas las pruebas | `AT-DB-04`: reset repetible y denegado en demo (`EV-DB-05`) |
| `S1-SEC-01` | Secretos externos, configuración separada y usuario de BD con mínimo privilegio | DoD-5, `NFR-08`, `NFR-09` | Segmento de configuración/secretos de `ST-BASE-01` y permisos de BD (`EV-SEC-01`) |
| `S1-SEC-02` | Hash, sesión/cookies, CSRF, validación, logs y autorización server-side por rol/propiedad | `RN-29`, las 9 HU, `NFR-03`, `NFR-09` | Segmento aplicativo de `ST-BASE-01` y matriz `ST-BASE-02` (`EV-SEC-02`) |
| `S1-ENV-01` | Local, CI y demo reproducibles; despliegue, smoke y matriz del navegador/teclado objetivo | `NFR-06..NFR-09` | Compose, manifiesto, health, smoke y `MT-COMPAT-01` en Chrome/Windows/1366×768 con teclado (`EV-ENV-01`) |
| `S1-QA-DB-01` | Migración y seed comprobados desde base vacía | `S1-DB-02`, `S1-DB-03`, `S1-DB-04`, `S1-DB-05` | Reporte `AT-DB-01`, `AT-DB-02`, `AT-DB-03`, `AT-DB-04` (`EV-QA-DB-01`) |
| `S1-QA-DB-02` | Rollback completo ante fallos inducidos | INV01A/VEN01C, `NFR-01` | `CT-ROLLBACK-01..02`, comparación antes/después (`EV-QA-DB-02`) |
| `S1-QA-DB-03` | Carreras de carga, caja, cobro y cierre resueltas | `NFR-02` | `CT-CONC-01..05`, dos conexiones y resultado único (`EV-QA-DB-03`) |
| `S1-OPS-DB-01` | Backup con manifiesto, retención y SHA-256 | Puerta de piloto, `NFR-10` | Archivo, manifiesto, checksum y log real (`EV-OPS-BKP-01`) |
| `S1-OPS-DB-02` | Restore en ambiente limpio y recorrido íntegro | Puerta de piloto, `NFR-10` | Log, conteos, tiempo y smoke real (`EV-OPS-RST-01`) |

## 3.3 Matriz completa de las 41 CA

En la columna **Implementación** se distinguen interfaz (`UI`) y servicio/persistencia. En **Prueba/Revisión** aparecen las Subtasks que producen y revisan los casos. Todos los paquetes `EV-*` comienzan en `Pendiente`.

### HU-AUTH-01 — Ingresar con mi cuenta de trabajo (4 CA)

| CA | Resultado y datos de prueba | RN / NFR | Implementación | Prueba/Revisión | Casos previstos | Evidencia |
|---|---|---|---|---|---|---|
| 1 | Cuenta activa + credenciales correctas → sesión rotada y pantalla de su rol | `RN-29`, `NFR-03` | `S1-AUTH01-UI`, `S1-AUTH01-SVC`, `S1-SEC-02` | `S1-AUTH01-AUTO`, `S1-AUTH01-MAN`, `S1-AUTH01-REV` | `AT-AUTH01-01`, `MT-AUTH01-01` | `EV-AUTH01-CA01` |
| 2 | Correo inexistente y clave errónea → mismo mensaje general, sin revelar el dato fallido | `NFR-03`, `NFR-09` | `S1-AUTH01-UI`, `S1-AUTH01-SVC` | `S1-AUTH01-AUTO`, `S1-AUTH01-MAN`, `S1-AUTH01-REV` | `AT-AUTH01-02`, `ST-AUTH01-01`, `MT-AUTH01-02` | `EV-AUTH01-CA02` |
| 3 | Cuenta inactiva con clave correcta → mismo mensaje general y ninguna sesión | `NFR-03`, `NFR-09` | `S1-AUTH01-SVC`, `S1-SEC-02` | `S1-AUTH01-AUTO`, `S1-AUTH01-MAN`, `S1-AUTH01-REV` | `AT-AUTH01-03`, `ST-AUTH01-02`, `MT-AUTH01-03` | `EV-AUTH01-CA03` |
| 4 | Cada cuenta ve solo su menú y una URL/POST de otro rol responde prohibido sin mutar datos | `RN-29`, `NFR-03` | `S1-AUTH01-UI`, `S1-AUTH01-AUTHZ`, `S1-SEC-02` | `S1-AUTH01-AUTO`, `S1-AUTH01-MAN`, `S1-AUTH01-REV` | `AT-AUTH01-04`, `ST-AUTH01-03`, `MT-AUTH01-04` | `EV-AUTH01-CA04` |

### HU-AUTH-03 — Salir de mi cuenta al terminar (3 CA)

| CA | Resultado y datos de prueba | RN / NFR | Implementación | Prueba/Revisión | Casos previstos | Evidencia |
|---|---|---|---|---|---|---|
| 1 | Sin borrador activo, confirmar «Salir» revoca la sesión y vuelve al login; si había turno, permanece abierto y ligado al mismo vendedor | `RN-30`, `NFR-01`, `NFR-03` | `S1-AUTH03-UI`, `S1-AUTH03-SVC`, `S1-SEC-02` | `S1-AUTH03-AUTO`, `S1-AUTH03-MAN`, `S1-AUTH03-REV` | `AT-AUTH03-01`, `MT-AUTH03-01` | `EV-AUTH03-CA01` |
| 2 | Con borrador activo con líneas, confirmar la salida descarta sus líneas sin cambiar caja/stock y revoca la sesión; cancelar conserva sesión y borrador | `RN-30`, `NFR-01`, `NFR-03` | `S1-AUTH03-UI`, `S1-AUTH03-SVC` | `S1-AUTH03-AUTO`, `S1-AUTH03-MAN`, `S1-AUTH03-REV` | `AT-AUTH03-02`, `MT-AUTH03-02` | `EV-AUTH03-CA02` |
| 3 | Tras salir, botón Atrás/URL/cookie no recuperan datos ni ejecutan acciones; el mismo vendedor puede retomar su turno y otro no puede apropiárselo | `RN-29`, `RN-30`, `NFR-03`, `NFR-09` | `S1-AUTH03-UI`, `S1-AUTH03-SVC`, `S1-SEC-02` | `S1-AUTH03-AUTO`, `S1-AUTH03-MAN`, `S1-AUTH03-REV` | `ST-AUTH03-01`, `MT-AUTH03-03` | `EV-AUTH03-CA03` |

### HU-PROD-02 — Registrar un producto enlatado (5 CA)

| CA | Resultado y datos de prueba | RN / NFR | Implementación | Prueba/Revisión | Casos previstos | Evidencia |
|---|---|---|---|---|---|---|
| 1 | ADMIN registra la ficha en la categoría sembrada y el producto queda con control de vencimiento obligatorio; la fecha se captura después en cada lote | `RN-29`, `DT-06`, `NFR-03` | `S1-PROD02-UI`, `S1-PROD02-SVC`, `S1-DB-01`, `S1-DB-02`, `S1-DB-03`, `S1-DB-04` | `S1-PROD02-AUTO`, `S1-PROD02-MAN`, `S1-PROD02-REV` | `AT-PROD02-01`, `MT-PROD02-01` | `EV-PROD02-CA01` |
| 2 | Precio `> 0` y máximo 2 decimales; cero, negativo, texto o 3 decimales se rechazan en servidor | `RN-27`, `NFR-04` | `S1-PROD02-UI`, `S1-PROD02-SVC`, `S1-DB-03` | `S1-PROD02-AUTO`, `S1-PROD02-MAN`, `S1-PROD02-REV` | `AT-PROD02-02`, `MT-PROD02-02` | `EV-PROD02-CA02` |
| 3 | Código normalizado repetido → conflicto y una sola fila de producto | `NFR-02`, `NFR-04` | `S1-PROD02-SVC`, `S1-DB-03` | `S1-PROD02-AUTO`, `S1-PROD02-MAN`, `S1-PROD02-REV` | `AT-PROD02-03`, `CT-PROD02-01`, `MT-PROD02-03` | `EV-PROD02-CA03` |
| 4 | Mínimo acepta entero `>= 0`; vacío aplica 10; decimal/negativo se rechaza | `RN-06`, `NFR-04` | `S1-PROD02-UI`, `S1-PROD02-SVC`, `S1-DB-03` | `S1-PROD02-AUTO`, `S1-PROD02-MAN`, `S1-PROD02-REV` | `AT-PROD02-04`, `MT-PROD02-04` | `EV-PROD02-CA04` |
| 5 | Producto recién creado tiene existencia física/vendible cero y no aparece disponible para cobro; ALMACENERO/VENDEDOR por URL directa no pueden crearlo | `RN-29`, `DT-06`, `NFR-03`, `NFR-04` | `S1-PROD02-SVC`, `S1-SEC-02`, `S1-DB-01`, `S1-DB-03` | `S1-PROD02-AUTO`, `S1-PROD02-MAN`, `S1-PROD02-REV` | `AT-PROD02-05`, `ST-PROD02-01`, `MT-PROD02-05` | `EV-PROD02-CA05` |

### HU-INV-01a — Registrar existencias iniciales por lotes (5 CA)

| CA | Resultado y datos de prueba | RN / NFR | Implementación | Prueba/Revisión | Casos previstos | Evidencia |
|---|---|---|---|---|---|---|
| 1 | ALMACENERO guarda la primera carga con uno/varios lotes válidos; otro rol no altera datos y una segunda carga directa, incluso simultánea, se rechaza | `RN-01`, `RN-29`, `NFR-02`, `NFR-03` | `S1-INV01A-UI`, `S1-INV01A-VALID`, `S1-INV01A-TXDB`, `S1-SEC-02`, `S1-DB-03` | `S1-INV01A-AUTO`, `S1-INV01A-MAN`, `S1-INV01A-REV` | `AT-INV01A-01`, `ST-INV01A-01`, `CT-CONC-01`, `MT-INV01A-01` | `EV-INV01A-CA01` |
| 2 | Lote comercial no vacío, uppercase y único por producto; cantidad entera positiva, costo positivo ≤4 decimales y vencimiento `> hoy Lima`; toda frontera inválida se rechaza | `RN-03`, `RN-14`, `DT-07`, `DT-08`, `NFR-04`, `NFR-11` | `S1-INV01A-UI`, `S1-INV01A-VALID`, `S1-DB-03` | `S1-INV01A-AUTO`, `S1-INV01A-MAN`, `S1-INV01A-REV` | `AT-INV01A-02`, `AT-TIME-01`, `MT-INV01A-02` | `EV-INV01A-CA02` |
| 3 | Un lote inválido dentro de un grupo revierte cabecera, lotes, movimientos y costo | `RN-01`, `NFR-01` | `S1-INV01A-VALID`, `S1-INV01A-TXDB`, `S1-QA-DB-02` | `S1-INV01A-AUTO`, `S1-INV01A-MAN`, `S1-INV01A-REV` | `AT-INV01A-03`, `CT-ROLLBACK-01`, `MT-INV01A-03` | `EV-INV01A-CA03` |
| 4 | Suma de saldos coincide con lotes y costo promedio ponderado queda a 4 decimales `HALF_UP` | `RN-14`, `NFR-04` | `S1-INV01A-TXDB`, `S1-DB-01`, `S1-DB-03` | `S1-INV01A-AUTO`, `S1-INV01A-MAN`, `S1-INV01A-REV` | `AT-INV01A-04`, `MT-INV01A-04` | `EV-INV01A-CA04` |
| 5 | Cada lote conserva número uppercase, cantidad, costo, vencimiento e ingreso inmutable para FEFO | `RN-19`, `DT-07`, `NFR-11` | `S1-INV01A-VALID`, `S1-INV01A-TXDB` | `S1-INV01A-AUTO`, `S1-INV01A-MAN`, `S1-INV01A-REV` | `AT-INV01A-05`, `MT-INV01A-05` | `EV-INV01A-CA05` |

### HU-CAJA-01 — Abrir el turno de caja (4 CA)

| CA | Resultado y datos de prueba | RN / NFR | Implementación | Prueba/Revisión | Casos previstos | Evidencia |
|---|---|---|---|---|---|---|
| 1 | VENDEDOR sin turno declara `0.00` o positivo y abre la caja única; otro rol por acceso directo no modifica datos | `RN-10`, `RN-29`, `NFR-03`, `NFR-04` | `S1-CAJA01-UI`, `S1-CAJA01-SVC`, `S1-SEC-02`, `S1-DB-03` | `S1-CAJA01-AUTO`, `S1-CAJA01-MAN`, `S1-CAJA01-REV` | `AT-CAJA01-01`, `ST-CAJA01-01`, `MT-CAJA01-01` | `EV-CAJA01-CA01` |
| 2 | Negativo, texto, vacío o más de 2 decimales se rechaza y no crea turno | `RN-10`, `NFR-04` | `S1-CAJA01-UI`, `S1-CAJA01-SVC` | `S1-CAJA01-AUTO`, `S1-CAJA01-MAN`, `S1-CAJA01-REV` | `AT-CAJA01-02`, `MT-CAJA01-02` | `EV-CAJA01-CA02` |
| 3 | Dos aperturas simultáneas → exactamente un turno `OPEN`; la otra recibe conflicto controlado | `RN-10`, `NFR-02` | `S1-CAJA01-SVC`, `S1-CAJA01-CONC`, `S1-DB-03` | `S1-CAJA01-AUTO`, `S1-CAJA01-MAN`, `S1-CAJA01-REV`, `S1-QA-DB-03` | `CT-CONC-02`, `MT-CAJA01-03` | `EV-CAJA01-CA03` |
| 4 | Turno guarda vendedor autenticado, caja, UTC, presentación Lima y monto exacto; cliente no puede suplantar vendedor y otro rol por URL directa no abre caja | `RN-10`, `RN-29`, `NFR-03`, `NFR-11` | `S1-CAJA01-SVC`, `S1-CAJA01-CONC`, `S1-SEC-02` | `S1-CAJA01-AUTO`, `S1-CAJA01-MAN`, `S1-CAJA01-REV` | `AT-CAJA01-03`, `ST-CAJA01-01`, `MT-CAJA01-04` | `EV-CAJA01-CA04` |

### HU-VEN-01b — Preparar una venta y revisar existencias (5 CA)

| CA | Resultado y datos de prueba | RN / NFR | Implementación | Prueba/Revisión | Casos previstos | Evidencia |
|---|---|---|---|---|---|---|
| 1 | Solo el VENDEDOR dueño de un turno abierto puede agregar la primera línea válida y crear el único borrador activo; una pantalla vacía no lo crea | `RN-10`, `RN-29`, `RN-30`, `NFR-03` | `S1-VEN01B-UI`, `S1-VEN01B-SVC`, `S1-SEC-02` | `S1-VEN01B-AUTO`, `S1-VEN01B-MAN`, `S1-VEN01B-REV` | `AT-VEN01B-01`, `ST-VEN01B-01`, `MT-VEN01B-01` | `EV-VEN01B-CA01` |
| 2 | Búsqueda por nombre/código digitado selecciona producto; no exige lector físico | `DEC-09`, `NFR-05`, `NFR-06` | `S1-VEN01B-UI`, `S1-VEN01B-SVC` | `S1-VEN01B-AUTO`, `S1-VEN01B-MAN`, `S1-VEN01B-REV` | `AT-VEN01B-02`, `MT-VEN01B-02`, `PT-SEARCH-01` | `EV-VEN01B-CA02` |
| 3 | Cantidad entera positiva y no mayor al stock vendible; límites se revalidan en servidor | `RN-03`, `NFR-04` | `S1-VEN01B-UI`, `S1-VEN01B-SVC` | `S1-VEN01B-AUTO`, `S1-VEN01B-MAN`, `S1-VEN01B-REV` | `AT-VEN01B-03`, `MT-VEN01B-03` | `EV-VEN01B-CA03` |
| 4 | Lote con vencimiento igual/anterior al día Lima no suma a disponibilidad | `RN-03`, `NFR-04`, `NFR-11` | `S1-VEN01B-SVC`, `S1-DB-03` | `S1-VEN01B-AUTO`, `S1-VEN01B-MAN`, `S1-VEN01B-REV` | `AT-VEN01B-04`, `AT-TIME-02`, `MT-VEN01B-04` | `EV-VEN01B-CA04` |
| 5 | Borrador muestra precio, línea, base, IGV y total exactos sin cambiar lotes ni caja; quitar su última línea lo descarta y deja de bloquear el cierre | `RN-27`, `RN-30`, `NFR-01`, `NFR-04` | `S1-VEN01B-UI`, `S1-VEN01B-SVC` | `S1-VEN01B-AUTO`, `S1-VEN01B-MAN`, `S1-VEN01B-REV` | `AT-VEN01B-05`, `MT-VEN01B-05`, `AT-CAJA02-04` | `EV-VEN01B-CA05` |

### HU-VEN-01c — Cobrar en efectivo y descontar existencias (6 CA)

| CA | Resultado y datos de prueba | RN / NFR | Implementación | Prueba/Revisión | Casos previstos | Evidencia |
|---|---|---|---|---|---|---|
| 1 | Efectivo no numérico, con más de 2 decimales o menor al total se rechaza; el faltante se informa cuando aplica y no se crea venta/correlativo/movimiento ni cambian lotes | `RN-25`, `RN-30`, `NFR-01`, `NFR-04` | `S1-VEN01C-UI`, `S1-VEN01C-PAY`, `S1-VEN01C-TXDB` | `S1-VEN01C-AUTO`, `S1-VEN01C-MAN`, `S1-VEN01C-REV` | `AT-VEN01C-01`, `MT-VEN01C-01` | `EV-VEN01C-CA01` |
| 2 | Efectivo igual/mayor produce vuelto exacto decimal, incluido caso de centavos | `RN-25`, `RN-27`, `DT-08`, `NFR-04` | `S1-VEN01C-UI`, `S1-VEN01C-PAY` | `S1-VEN01C-AUTO`, `S1-VEN01C-MAN`, `S1-VEN01C-REV` | `AT-VEN01C-02`, `MT-VEN01C-02` | `EV-VEN01C-CA02` |
| 3 | Solo el VENDEDOR dueño con turno abierto puede cobrar; múltiples lotes descuentan FEFO estable, saltan vencidos y nunca quedan negativos bajo carrera | `RN-03`, `RN-19`, `RN-29`, `NFR-02`, `NFR-03`, `NFR-04`, `NFR-11` | `S1-VEN01C-PAY`, `S1-VEN01C-FEFO`, `S1-VEN01C-TXDB`, `S1-SEC-02`, `S1-DB-03` | `S1-VEN01C-AUTO`, `S1-VEN01C-MAN`, `S1-VEN01C-REV`, `S1-QA-DB-03` | `AT-VEN01C-03`, `ST-VEN01C-01`, `CT-CONC-03`, `MT-VEN01C-03` | `EV-VEN01C-CA03` |
| 4 | Fallo inducido después de cada etapa revierte venta, correlativo, caja, lotes, asignaciones y borrador; el cobro se mide también en el volumen objetivo | `RN-25`, `NFR-01`, `NFR-05` | `S1-VEN01C-TXDB`, `S1-QA-DB-02`, `S1-ENV-01` | `S1-VEN01C-AUTO`, `S1-VEN01C-MAN`, `S1-VEN01C-REV` | `CT-ROLLBACK-02`, `PT-CHECKOUT-01`, `MT-VEN01C-04` | `EV-VEN01C-CA04` |
| 5 | Doble clic/reintento con misma clave y hash devuelve la misma venta; clave reutilizada con otro contenido se rechaza | `RN-25`, `NFR-02` | `S1-VEN01C-IDEM`, `S1-VEN01C-TXDB` | `S1-VEN01C-AUTO`, `S1-VEN01C-MAN`, `S1-VEN01C-REV`, `S1-QA-DB-03` | `AT-VEN01C-04`, `CT-CONC-04`, `MT-VEN01C-05` | `EV-VEN01C-CA05` |
| 6 | Venta guarda snapshots de nombre, precio y costo a 4 decimales; cambios maestros posteriores no alteran historial | `RN-28`, `NFR-12` | `S1-VEN01C-TXDB`, `S1-DB-01`, `S1-DB-03` | `S1-VEN01C-AUTO`, `S1-VEN01C-MAN`, `S1-VEN01C-REV` | `AT-VEN01C-05`, `MT-VEN01C-06` | `EV-VEN01C-CA06` |

### HU-VEN-02a — Generar una constancia interna (4 CA)

| CA | Resultado y datos de prueba | RN / NFR | Implementación | Prueba/Revisión | Casos previstos | Evidencia |
|---|---|---|---|---|---|---|
| 1 | La constancia usa el correlativo global ya confirmado `V-00000001`; refrescar/reabrir no crea otro | `RN-25`, `RN-26`, `NFR-02`, `NFR-12` | `S1-VEN02A-UI`, `S1-VEN02A-SVC` | `S1-VEN02A-AUTO`, `S1-VEN02A-MAN`, `S1-VEN02A-REV` | `AT-VEN02A-01`, `MT-VEN02A-01` | `EV-VEN02A-CA01` |
| 2 | DTO histórico muestra Lima, vendedor/caja, líneas, base, IGV, total, efectivo y vuelto; nunca muestra costo | `RN-26`, `RN-27`, `RN-28`, `NFR-09`, `NFR-11`, `NFR-12` | `S1-VEN02A-UI`, `S1-VEN02A-SVC` | `S1-VEN02A-AUTO`, `S1-VEN02A-MAN`, `S1-VEN02A-REV` | `AT-VEN02A-02`, `ST-VEN02A-01`, `MT-VEN02A-02` | `EV-VEN02A-CA02` |
| 3 | Pantalla/impresión exhibe literalmente la advertencia de control interno y no simula SUNAT | `RN-26` | `S1-VEN02A-UI`, `S1-VEN02A-SVC` | `S1-VEN02A-AUTO`, `S1-VEN02A-MAN`, `S1-VEN02A-REV` | `AT-VEN02A-03`, `MT-VEN02A-03` | `EV-VEN02A-CA03` |
| 4 | «Última constancia» abre mediante su correlativo la misma venta autorizada tras recarga; cambios a producto no alteran importes | `RN-26`, `RN-29`, `NFR-03`, `NFR-12` | `S1-VEN02A-UI`, `S1-VEN02A-SVC`, `S1-SEC-02` | `S1-VEN02A-AUTO`, `S1-VEN02A-MAN`, `S1-VEN02A-REV` | `AT-VEN02A-04`, `ST-VEN02A-02`, `MT-VEN02A-04` | `EV-VEN02A-CA04` |

### HU-CAJA-02 — Cerrar y cuadrar caja (5 CA)

| CA | Resultado y datos de prueba | RN / NFR | Implementación | Prueba/Revisión | Casos previstos | Evidencia |
|---|---|---|---|---|---|---|
| 1 | Solo el VENDEDOR dueño del turno puede declarar un contado decimal no negativo con hasta 2 decimales; dato inválido o rol ajeno no modifica el turno | `RN-10`, `RN-29`, `NFR-03`, `NFR-04` | `S1-CAJA02-UI`, `S1-CAJA02-SVC`, `S1-SEC-02` | `S1-CAJA02-AUTO`, `S1-CAJA02-MAN`, `S1-CAJA02-REV` | `AT-CAJA02-01`, `ST-CAJA02-01`, `MT-CAJA02-01` | `EV-CAJA02-CA01` |
| 2 | Esperado = inicial + ventas en efectivo confirmadas; en Sprint 1 no existen salidas manuales, por lo que valen cero. La diferencia produce cuadre, sobrante o faltante exactos | `RN-10`, `RN-25`, `DT-08`, `NFR-04` | `S1-CAJA02-UI`, `S1-CAJA02-SVC` | `S1-CAJA02-AUTO`, `S1-CAJA02-MAN`, `S1-CAJA02-REV` | `AT-CAJA02-02`, `MT-CAJA02-02` | `EV-CAJA02-CA02` |
| 3 | Cierre guarda vendedor/UTC, cambia a `CLOSED`, impide vender y un segundo cierre no altera el acta | `RN-10`, `RN-29`, `NFR-02`, `NFR-03`, `NFR-11` | `S1-CAJA02-SVC`, `S1-DB-03` | `S1-CAJA02-AUTO`, `S1-CAJA02-MAN`, `S1-CAJA02-REV`, `S1-QA-DB-03` | `AT-CAJA02-03`, `CT-CONC-05`, `MT-CAJA02-03` | `EV-CAJA02-CA03` |
| 4 | Borrador activo con líneas bloquea cierre; descartarlo o quitar su última línea habilita cierre. Cobro y cierre concurrentes dejan uno de dos estados íntegros | `RN-30`, `NFR-01`, `NFR-02` | `S1-CAJA02-UI`, `S1-CAJA02-SVC` | `S1-CAJA02-AUTO`, `S1-CAJA02-MAN`, `S1-CAJA02-REV`, `S1-QA-DB-03` | `AT-CAJA02-04`, `CT-CONC-05`, `MT-CAJA02-04` | `EV-CAJA02-CA04` |
| 5 | Tras cierre, otro VENDEDOR puede abrir un nuevo turno; nunca coexisten dos `OPEN` | `RN-10`, `RN-29`, `NFR-02`, `NFR-03` | `S1-CAJA02-SVC`, `S1-CAJA01-CONC` | `S1-CAJA02-AUTO`, `S1-CAJA02-MAN`, `S1-CAJA02-REV` | `AT-CAJA02-05`, `CT-CONC-02`, `MT-CAJA02-05` | `EV-CAJA02-CA05` |

**Control:** `4 + 3 + 5 + 5 + 4 + 5 + 6 + 4 + 5 = 41 CA`.

## 3.4 Especificación de pruebas críticas transversales

| ID | Preparación y acción | Resultado esperado |
|---|---|---|
| `AT-DB-01` | Crear PostgreSQL vacío y aplicar migraciones | Todas las migraciones aplicadas sin paso manual ni drift |
| `AT-DB-02` | Inspeccionar `DB-C01..DB-C16`; intentar violar las restricciones de datos, roles y vencimiento, y revisar presencia/uso de índices y FK | Las restricciones rechazan la escritura y dejan la transacción limpia; los índices y protecciones estructurales existen conforme al diseño |
| `AT-DB-03` | Ejecutar seed dos veces | Exactamente 3 cuentas, 3 roles, 1 categoría, 1 caja y 1 contador |
| `AT-DB-04` | Ejecutar reset en local/CI y luego en demo | Local/CI queda reproducible; demo rechaza la acción |
| `CT-CONC-01` | Dos conexiones intentan primera carga del mismo producto | Una confirma; otra recibe conflicto; no hay lotes huérfanos |
| `CT-CONC-02` | Dos vendedores intentan abrir la caja a la vez | Existe exactamente un turno abierto |
| `CT-CONC-03` | Dos confirmaciones compiten por las últimas unidades con claves distintas | Solo las ventas que tienen stock confirman; saldo nunca negativo |
| `CT-CONC-04` | Dos solicitudes idénticas usan simultáneamente la misma clave | Una sola venta/correlativo/movimiento; ambas obtienen resultado coherente |
| `CT-CONC-05` | Un hilo cobra mientras otro cierra; repetir dos cierres | Cobro entra antes del cierre o se rechaza después; solo un acta final |
| `CT-ROLLBACK-01` | Forzar fallo después de insertar parte de una carga multilot | No quedan carga, lotes, movimientos ni costo modificado |
| `CT-ROLLBACK-02` | Forzar fallo después de cada etapa del cobro | Venta, stock, caja, correlativo, asignaciones e idempotencia permanecen coherentes |
| `ST-BASE-01` | Inspeccionar hash, cookie, CSRF, configuración y logs | No hay claves recuperables, secretos o tokens completos; escritura sin CSRF falla |
| `ST-BASE-02` | Ejecutar cada operación con los 3 roles y sin sesión | Solo la celda autorizada de `02` modifica datos; el resto recibe 401/403 |
| `AT-TIME-01` | Congelar UTC alrededor de medianoche de Lima y cargar lotes para ayer/hoy/mañana | Solo fecha posterior al día de Lima se acepta |
| `AT-TIME-02` | Congelar los mismos instantes y consultar stock vendible | Hoy y vencidos se excluyen sin depender de la zona del navegador |
| `MT-COMPAT-01` | Recorrer las nueve HU en Chrome estable sobre Windows 10/11 a 1366×768 usando teclado | No hay corte, solapamiento ni operación principal inaccesible; navegador, SO y viewport quedan registrados |
| `PT-SEARCH-01` | Después de completar el recorrido, cargar opcionalmente 2 000 productos/20 000 lotes y repetir búsqueda | p95 ≤ 2 s con ambiente, muestra y consulta registrados; no bloquea el desarrollo funcional |
| `PT-CHECKOUT-01` | Con volumen de referencia, repetir cobro controlado | p95 ≤ 3 s y ninguna violación de integridad |
| `E2E-R1-01` | Login ADMIN → producto; logout/login ALMACENERO → lotes; logout/login VENDEDOR → caja, venta, constancia y cierre | Las 9 HU se recorren en orden, con leyenda interna y cuadre exacto |

Las pruebas concurrentes deben usar PostgreSQL 17 real y conexiones separadas. SQLite, mocks o llamadas secuenciales no constituyen evidencia de concurrencia.

## 3.5 Datos de prueba mínimos

Los nombres son etiquetas de fixture, no credenciales reales.

| Fixture | Estado inicial | Uso |
|---|---|---|
| `ACC-ADMIN-ACTIVA` | rol ADMIN, activa | Producto y denegaciones cruzadas |
| `ACC-ALM-ACTIVA` | rol ALMACENERO, activa | Carga inicial y denegaciones cruzadas |
| `ACC-VEN-ACTIVA` | rol VENDEDOR, activa | Caja, ventas y constancia |
| `ACC-INACTIVA` | inactiva | Mensaje general de login |
| `PROD-SIN-STOCK` | enlatado, stock 0, mínimo 10 | Alta de producto/carga inicial |
| `PROD-FEFO` | tres lotes vigentes y uno vencido | FEFO, exclusión y reparto entre lotes |
| `LOT-A/LOT-B` | mismo vencimiento, distinto ingreso | Segundo criterio FEFO |
| `LOT-C/LOT-D` | mismo vencimiento e ingreso simulado, UUID ordenable | Desempate técnico estable |
| `SHIFT-OPEN` | monto inicial conocido, vendedor dueño | Borrador, cobro y cierre |
| `DRAFT-ACTIVE` | al menos una línea, sin descuento | Logout y bloqueo de cierre |
| `SALE-CONFIRMED` | snapshots y correlativo conocido | Constancia e inmutabilidad |

Las contraseñas, UUID, fechas exactas e importes se generan en fixtures o variables de entorno. Los casos de dinero deben incluir al menos: `0.00`, `0.01`, un precio con IGV como `118.00`, pago exacto, pago mayor, faltante, sobrante y faltante de cierre.

## 3.6 Evidencia exigida

Cada `EV-*` real debe enlazar desde Jira y contener:

| Campo | Contenido obligatorio |
|---|---|
| Identidad | ID de prueba, HU/CA, Task/Subtask y commit/build |
| Contexto | fecha UTC, ambiente, versión, migración y datos/fixture |
| Ejecución | pasos o comando reproducible sin secretos |
| Resultado | esperado, obtenido y estado `Aprobado/Fallido/Bloqueado` |
| Prueba automática | log completo o reporte JUnit/HTML y enlace de pipeline |
| Prueba manual | capturas relevantes y registro paso a paso; no solo la pantalla final |
| Persistencia | consulta o aserción que demuestre estado final/rollback sin exponer credenciales |
| Revisión | nombre del Developer distinto, fecha y observaciones |
| Defectos | Bug Jira vinculado si el resultado difiere |

Una captura aislada no demuestra atomicidad, idempotencia, autorización ni concurrencia. Para esos casos se requiere log/aserción antes-después y, cuando corresponda, barrera de dos conexiones.

## 3.7 Simulación textual con seis Developers

La simulación de planificación se ejecuta como una revisión de mesa, no como prueba del producto:

| Developer simulado | Casos que desafía | Revisor cruzado simulado | Pregunta de control |
|---|---|---|---|
| Des.1 - Velasquez | `CT-CONC-01`, `CT-CONC-03`, `CT-ROLLBACK-01` | Des.4 - Alcalde | ¿Puede quedar lote/stock incoherente bajo carrera o fallo? |
| Des.2 - Nolasco | `ST-BASE-01/02`, AUTH01 y checkout atómico | Des.6 - Angeles | ¿Una URL o cuerpo manipulado evade rol o totales? |
| Des.3 - Castillo | formularios, HTMX, teclado y mensajes de las 9 HU | Des.5 - Walter Luis Colonia Infantas | ¿Cada estado de error se entiende y conserva foco/datos correctos? |
| Des.4 - Alcalde | `CT-CONC-02/05`, despliegue, smoke y cierre | Des.1 - Velasquez | ¿Caja/cierre siguen íntegros si dos acciones coinciden? |
| Des.5 - Walter Luis Colonia Infantas | `AT-DB-01`, `AT-DB-02`, `AT-DB-03`, `AT-DB-04`, matrices automáticas y fixtures | Des.3 - Castillo | ¿La prueba es repetible desde una base vacía? |
| Des.6 - Angeles | constancia, `E2E-R1-01`, backup/restore | Des.2 - Nolasco | ¿El historial se conserva y el sistema se puede recuperar? |

### Procedimiento de simulación

1. Leer literalmente una CA y sus RN/NFR.
2. Partir del fixture indicado y anotar estado de tablas/turno/stock/caja.
3. Simular la acción normal, la frontera inválida y, si corresponde, carrera o interrupción.
4. Comparar el estado esperado en interfaz, servicio y persistencia.
5. Confirmar que existe Task de implementación, prueba y revisión distinta.
6. Registrar solamente `Coherente`, `Defecto documental` o `Decisión faltante`. Nunca registrar `Prueba aprobada` ni `Done` por una simulación.
7. Corregir todo defecto documental y repetir la traza completa afectada.

### Condiciones para que la planificación supere la simulación

- 41/41 CA tienen RN/NFR, implementación, prueba y evidencia esperada.
- 67/67 Tasks/Subtasks tienen al menos una relación de cobertura y no existen IDs huérfanos.
- Las carreras de carga, apertura, stock, doble cobro y cierre tienen resultado único definido.
- Todo fallo transaccional especifica qué datos deben permanecer sin cambios.
- Ningún flujo depende exclusivamente de validación o permiso del navegador.
- La constancia usa snapshots, no muestra costo y puede reabrirse sin generar otro correlativo.
- Backup y restore son actividades y evidencias diferentes.
- Ninguna evidencia planificada aparece como ejecutada.

Superar estas condiciones significa **«plan coherente para ejecución»**. Una Story solo pasa a `Hecho` con pruebas ejecutadas, revisión independiente y Definition of Done; el profesor observa y valida el avance académico durante la exposición.

## 3.8 Recorrido integral y puerta de piloto

`E2E-R1-01` enlaza las nueve Stories, pero no sustituye sus 41 casos:

```text
HU-AUTH-01 → HU-PROD-02 → HU-AUTH-03
             ↓ cambio de cuenta
HU-AUTH-01 → HU-INV-01a → HU-AUTH-03
             ↓ cambio de cuenta
HU-AUTH-01 → HU-CAJA-01 → HU-VEN-01b → HU-VEN-01c
             → HU-VEN-02a → HU-CAJA-02 → HU-AUTH-03
```

Para autorizar piloto controlado deben existir resultados reales satisfactorios de:

1. `E2E-R1-01` y 41/41 CA.
2. `ST-BASE-01/02`.
3. `CT-CONC-01..05` y `CT-ROLLBACK-01..02`.
4. pipeline reproducible y smoke de demostración.
5. `S1-OPS-DB-01` y `S1-OPS-DB-02`, con checksum y restore limpio.
6. comprobación visible de «CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO».
7. validación académica del profesor al exponer, sin reemplazar la Definition of Done ni marcar trabajo no ejecutado.

Hasta que eso ocurra, el estado de la puerta es **`Pendiente`**.

---

## 3.9 Extensión de Matriz de Trazabilidad Post-Auditoría Caos y UX (`BUG-001` a `BUG-037` — 202 Pruebas Automatizadas)

Tras la ejecución de la auditoría exploratoria multi-rol y de usabilidad (`REPORTE_CAOS_Y_UX_QA.md`), se incorporaron **39 nuevas pruebas unitarias y de integración** (elevando la suite de **163 a 202 pruebas automatizadas en verde**), garantizando trazabilidad completa entre hallazgo, Historia de Usuario, Criterio de Aceptación, tarea técnica e implementación:

| ID Bug | Historia (HU) | Criterio / Regla | Tarea / Subtarea | Implementación (Archivo / Símbolo) | Caso de Prueba Unitaria (`manage.py test`) | Estado |
|---|---|---|---|---|---|---|
| `BUG-001` | `HU-USR-03`, `HU-CAJA-01` | `CA-USR03-04`, `RN-03` | `S3-USR03-SVC` | `identity/services.py::update_employee` | `identity.tests.EmployeeEditDeactivateTests.test_cannot_change_role_of_seller_with_open_shift` | ✅ PASS |
| `BUG-002` | `HU-CAJA-05`, `HU-CAJA-02` | `CA-CAJA05-02`, `RN-04` | `S2-CAJA05-UI` | `cash/models.py::CashShiftClose` (`difference_type`, `difference_amount`, `get_difference_type_display`) | `cash.tests.CashShiftHistoryTests.test_shift_history_renders_shortage_surplus_and_exact_labels_and_amounts` | ✅ PASS |
| `BUG-003` | `HU-INV-02`, `HU-INV-03` | `CA-INV02-04`, `NFR-05` | `S3-INV02-UI`, `S3-INV03-UI` | `inventory/views.py::_is_inventory_key_processed`, `_mark_inventory_key_processed` | `inventory.tests.PhysicalAdjustmentTests.test_failed_validation_does_not_consume_idempotency_key_in_writeoff_or_adjustment` | ✅ PASS |
| `BUG-004` | `HU-PROD-04`, `HU-INV-06` | `CA-PROD04-03`, `CA-INV06-01` | `S2-PROD04-SVC` | `sales/models.py::SaleLine.product` (`0004_saleline_product`), `catalog/services.py::update_product`, `inventory/views.py::product_movements` | `inventory.tests.PhysicalAdjustmentTests.test_barcode_change_preserves_sales_in_product_movements_kardex` | ✅ PASS |
| `BUG-005` | `HU-INV-01b` | `CA-INV01B-01..04`, `RN-14` | `S3-INV01B-UI`, `S3-INV01B-AUTO` | `inventory/views.py::stock_entry_create`, `inventory/services.py::register_stock_entry`, `inventory/urls.py` (`stock-entry`) | `inventory.tests.PhysicalAdjustmentTests.test_stock_entry_view_registers_subsequent_lots_and_links_supplier`, `test_bug005_register_stock_entry_excludes_expired_lots_from_average_cost` | ✅ PASS |
| `BUG-006` | `HU-VEN-01a`, `HU-VEN-01c`, `HU-PROD-04` | `CA-VEN01C-01`, `RN-10` | `S1-VEN01C-SVC` | `sales/services.py::checkout_sale`, `sales/views.py::sales_draft`, `sales_line_update`, `sales_checkout` | `sales.tests.SalesHistoryTests.test_price_change_during_checkout_warns_seller_and_updates_draft_line_price`, `test_bug006_draft_warns_seller_when_catalog_price_changes_during_preparation` | ✅ PASS |
| `BUG-007` | `HU-VEN-01b`, `HU-VEN-01c` | `CA-VEN01C-02`, `NFR-05` | `S1-VEN01C-UI` | `sales/forms.py::CheckoutForm` (`expected_subtotal`), `sales/views.py::sales_checkout` | `sales.tests.SalesHistoryTests.test_multitab_draft_modification_warns_seller_on_checkout` | ✅ PASS |
| `BUG-008` | `HU-VEN-02a` | `CA-VEN02A-04`, `RN-01` | `S1-VEN02A-UI` | `sales/templates/sales/sales_receipt.html` | `sales.tests.SalesHistoryTests.test_sales_receipt_hides_nueva_venta_for_admin_and_shows_back_to_history` | ✅ PASS |
| `BUG-009` | `HU-PROD-04`, `HU-CAJA-01`, `HU-CAJA-02`, `HU-VEN-01c` | `CA-PROD02-03`, `CA-CAJA01-03` | `S1-CAJA01-UI`, `S2-PROD04-UI` | `catalog/forms.py::ProductEditForm`, `cash/forms.py::CashOpeningForm`, `CashCloseForm`, `sales/forms.py::CheckoutForm` | `catalog.tests.ProductExpirationsTests.test_product_edit_rejects_scientific_notation_and_excessive_minimum_stock`, `cash.tests.CashShiftHistoryTests.test_cash_open_and_close_reject_scientific_notation_and_absurd_amounts` | ✅ PASS |
| `BUG-010` | `HU-INV-02`, `HU-INV-03` | `NFR-05` | `S3-INV02-UI`, `S3-INV03-UI` | `inventory/views.py::_resolve_inventory_idempotency_key` | `inventory.tests.PhysicalAdjustmentTests.test_missing_idempotency_key_still_prevents_rapid_duplicate_adjustment` | ✅ PASS |
| `BUG-011` | `HU-PROV-01..04`, `HU-INV-01a`, `HU-INV-01b` | `CA-PROV01-01`, `CA-INV01A-01` | `S3-PROV-MODEL`, `S3-INV01B-SVC` | `inventory/models.py::Lot.supplier` (`0003_lot_supplier`), `inventory/services.py::confirm_initial_load`, `register_stock_entry`, `product_expirations.html` | `inventory.tests.PhysicalAdjustmentTests.test_stock_entry_view_registers_subsequent_lots_and_links_supplier` | ✅ PASS |
| `BUG-012` | `HU-INV-01a`, `HU-INV-03` | `CA-INV01A-02` | `S1-INV01A-UI` | `inventory/views.py::initial_load_created`, `initial_load_created.html` | `inventory.tests.PhysicalAdjustmentTests.test_initial_load_created_preserves_original_quantity_and_alias_url` | ✅ PASS |
| `BUG-013` | `HU-PROD-02`, `HU-PROD-04` | `CA-PROD02-02`, `NFR-04` | `S1-PROD02-SVC`, `S2-PROD04-SVC` | `catalog/forms.py::BARCODE_PATTERN`, `catalog/services.py::update_product` | `catalog.tests.ProductExpirationsTests.test_barcode_rejects_xss_and_special_characters_on_create_and_edit` | ✅ PASS |
| `BUG-014` | `HU-INV-01a`, `HU-INV-01b` | `CA-INV01A-03`, `RN-07` | `S1-INV01A-VALID` | `inventory/forms.py::LotInputForm.clean_expiration_date`, `inventory/services.py::_validate_lots` | `inventory.tests.PhysicalAdjustmentTests.test_absurd_future_expiration_year_9999_is_rejected` | ✅ PASS |
| `BUG-015` | `HU-VEN-03`, `HU-VEN-05a`, `HU-VEN-05b` | `CA-VEN05A-01`, `CA-VEN05B-01` | `S2-VEN05-UI` | `sales/views.py::sales_history`, `sales_shift_history`, `sales_history.html`, `sales_shift_history.html` | `sales.tests.SalesHistoryTests.test_sales_history_and_shift_history_display_discount_column_and_totals` | ✅ PASS |
| `BUG-016` | `HU-INV-05`, `HU-REP-01` | `CA-INV05-01` | `S1-AUTH01-UI` | `identity/views.py::dashboard`, `_admin_summary`, `identity/templates/identity/dashboard.html` | `identity.tests.EmployeeEditDeactivateTests.test_dashboard_for_admin_and_warehouse_includes_expired_lots_and_single_h1` | ✅ PASS |
| `BUG-017` | `HU-AUTH-03`, `HU-VEN-01b` | `CA-AUTH03-02` | `S1-AUTH03-UI` | `identity/templates/identity/logout_confirm.html` | `identity.tests.EmployeeEditDeactivateTests.test_logout_confirm_shows_minimarket_title_and_draft_warning_for_seller` | ✅ PASS |
| `BUG-018` | Transversal UI (`Sprint 2` y `Sprint 3`) | `NFR-07` (Usabilidad y consistencia visual) | `S1-PLAT-01` | `identity/static/identity/app.css` | Inspección DOM/CSS y suite de vistas HTTP 200 | ✅ PASS |
| `BUG-019` | `HU-USR-01` | `CA-USR01-01` | `S2-USR01-UI` | `identity/templates/identity/employee_list.html` | `identity.tests.EmployeeEditDeactivateTests.test_employee_list_does_not_render_broken_bootstrap_dismiss_button` | ✅ PASS |
| `BUG-020` | `HU-AUTH-03`, Transversal UI | `NFR-07` | `S1-AUTH03-UI`, `S1-PLAT-01` | `identity/templates/identity/base.html`, `logout_confirm.html` | `identity.tests.EmployeeEditDeactivateTests.test_logout_confirm_shows_minimarket_title_and_draft_warning_for_seller` | ✅ PASS |
| `BUG-021` | `HU-CAT-02`, `HU-PROD-02`, `HU-INV-01a`, `HU-VEN-01b` | `CA-CAT02-01` | `S2-CAT02-SVC`, `S1-PROD02-UI` | `catalog/models.py`, `catalog/forms.py`, `inventory/services.py`, `sales_draft.html`, `identity/forms.py` | `catalog.tests.ProductExpirationsTests.test_active_custom_category_can_be_used_to_register_product` | ✅ PASS |
| `BUG-022` | `HU-INV-01a`, `HU-CAJA-02` | `NFR-07` (Formato numérico `es-PE`) | `S1-INV01A-UI`, `S1-CAJA02-UI` | `inventory/templates/inventory/initial_load_created.html`, `cash/templates/cash/cash_shift_closed.html` | `inventory.tests.PhysicalAdjustmentTests.test_initial_load_created_preserves_original_quantity_and_alias_url` | ✅ PASS |
| `BUG-023` | `HU-PROD-02`, `HU-INV-01a`, `HU-CAJA-01`, `HU-CAJA-02`, `HU-VEN-02a` | `NFR-07` (Navegación y semántica HTML) | `S1-PROD02-UI`, `S1-INV01A-UI`, `S1-CAJA02-UI` | `catalog/urls.py`, `inventory/urls.py`, `dashboard.html`, `stock_overview.html`, `cash_shift_opened.html` | `catalog.tests.ProductExpirationsTests.test_product_created_alias_url_and_catalog_link`, `cash.tests.CashShiftHistoryTests.test_bug023_and_bug031_cash_open_shows_owner_and_shift_opened_has_sales_draft_link` | ✅ PASS |
| `BUG-024` | `HU-INV-01a`, `HU-INV-01b`, `HU-INV-06` | `CA-INV01A-02`, `CA-INV01B-02`, `CA-INV06-01` | `QA-FIX-INV-01` | `inventory/models.py::Lot.is_initial` (`0004_lot_is_initial`), `inventory/services.py::register_stock_entry`, `inventory/views.py::initial_load_created`, `product_movements` | `inventory.tests.PhysicalAdjustmentTests.test_bug024_stock_entry_preserves_initial_load_lots_and_labels_subsequent_entries_in_kardex` | ✅ PASS |
| `BUG-025` | `HU-VEN-01b`, `HU-VEN-01c` | `CA-VEN01C-02`, `NFR-05` | `QA-FIX-SALES-01` | `sales/forms.py::CheckoutForm.draft_signature`, `sales/views.py::_draft_signature`, `sales_checkout` | `sales.tests.SalesHistoryTests.test_bug025_checkout_detects_same_subtotal_product_swap_via_draft_signature` | ✅ PASS |
| `BUG-026` | `HU-AUTH-01` | `CA-AUTH01-03`, `NFR-03` | `QA-FIX-IDENT-01` | `identity/views.py::login_view` (`login_locked_until`), `config/settings.py` (`SESSION_EXPIRE_AT_BROWSER_CLOSE`) | `identity.tests.EmployeeEditDeactivateTests.test_bug026_login_rate_limit_expires_after_five_minutes` | ✅ PASS |
| `BUG-027` | `HU-INV-01a`, `HU-INV-01b` | `CA-INV01A-03` | `QA-FIX-INV-01` | `inventory/forms.py::LotInputForm.clean_unit_cost`, `inventory/services.py::_validate_lots` | `inventory.tests.PhysicalAdjustmentTests.test_bug027_lot_unit_cost_rejects_scientific_notation_and_excessive_values` | ✅ PASS |
| `BUG-028` | `HU-CAT-01`, `HU-CAT-02`, `HU-PROD-04` | `CA-CAT02-01`, `CA-PROD04-01` | `QA-FIX-CAT-01` | `catalog/services.py::toggle_category_status`, `catalog/views.py::category_toggle`, `catalog/forms.py::ProductEditForm`, `category_form.html`, `category_list.html` | `catalog.tests.ProductExpirationsTests.test_bug028_category_toggle_and_product_edit_category_and_barcode_search` | ✅ PASS |
| `BUG-029` | `HU-VEN-03`, `HU-VEN-01c` | `CA-VEN03-02` | `QA-FIX-SALES-01` | `sales/views.py::sales_checkout`, `sales/templates/sales/sales_checkout.html` (`recalc()`) | `sales.tests.SalesHistoryTests.test_bug029_checkout_renders_discounted_totals_on_validation_error` | ✅ PASS |
| `BUG-030` | `HU-INV-01a` (`HUECO-09`) | `CA-INV01A-04` | `QA-FIX-CAT-01` | `catalog/management/commands/seed_demo.py` | `catalog.tests.ProductExpirationsTests.test_bug030_seed_demo_populates_weighted_average_cost` | ✅ PASS |
| `BUG-031` | `HU-CAJA-01`, `HU-PROD-01`, Transversal UI | `CA-CAJA01-02`, `CA-PROD01-02`, `NFR-07` | `QA-FIX-CASH-01`, `QA-FIX-CAT-01`, `QA-FIX-UI-01` | `cash/templates/cash/cash_open.html`, `catalog/views.py::product_list`, `templates/403.html`, `templates/404.html` | `cash.tests.CashShiftHistoryTests.test_bug023_and_bug031_cash_open_shows_owner_and_shift_opened_has_sales_draft_link`, `catalog.tests.ProductExpirationsTests.test_bug028_category_toggle_and_product_edit_category_and_barcode_search` | ✅ PASS |
| `BUG-032` | `HU-INV-01a`, `HU-INV-01b`, `HU-INV-06`, `HU-PROV-01..04` | `CA-INV01A-02`, `CA-INV01B-02`, `CA-INV06-01` | `QA-FIX-INV-01` | `inventory/models.py::Lot.responsible` (`0005_lot_responsible`), `inventory/services.py::confirm_initial_load`, `register_stock_entry`, `inventory/views.py::initial_load_created`, `product_movements`, `initial_load_created.html`, `stock_overview.html` | `inventory.tests.PhysicalAdjustmentTests.test_bug032_subsequent_stock_entry_records_second_warehouse_worker_and_admin_can_view_load` | ✅ PASS |
| `BUG-033` | `HU-CAT-01`, `HU-PROD-04`, `HU-INV-01a`, `HU-INV-01b`, `HU-VEN-01a..01c` | `CA-CAT01-02`, `CA-PROD04-01`, `CA-VEN01B-02` | `QA-FIX-CAT-01`, `QA-FIX-INV-01`, `QA-FIX-SALES-01` | `catalog/models.py::Product.clean`, `Product.is_sellable`, `inventory/forms.py::InitialLoadProductForm`, `StockEntryProductForm`, `sales/views.py::_search_products`, `sales/services.py::add_product_to_draft`, `update_draft_line`, `checkout_sale` | `catalog.tests.ProductExpirationsTests.test_bug033_product_with_inactive_category_can_update_price_and_name`, `inventory.tests.PhysicalAdjustmentTests.test_bug033_inactive_category_excludes_products_from_initial_load_and_stock_entry_forms`, `sales.tests.SalesHistoryTests.test_bug033_and_bug037_inactive_category_or_product_blocks_search_draft_line_update_and_checkout` | ✅ PASS |
| `BUG-035` | `HU-VEN-01b`, `HU-VEN-01c` | `CA-VEN01C-02`, `NFR-05` | `QA-FIX-SALES-01` | `sales/views.py::_draft_signature`, `sales/views.py::sales_checkout` | `sales.tests.SalesHistoryTests.test_bug035_and_bug036_draft_signature_includes_draft_id_and_checkout_renders_hidden_field_errors` | ✅ PASS |
| `BUG-036` | `HU-INV-02`, `HU-INV-03`, `HU-VEN-01c` | `CA-INV02-04`, `CA-INV03-04`, `NFR-05` | `QA-FIX-INV-01`, `QA-FIX-SALES-01` | `inventory/views.py::stock_writeoff_create`, `physical_adjustment_create`, `writeoff_form.html`, `adjustment_form.html`, `sales/templates/sales/sales_checkout.html` | `inventory.tests.PhysicalAdjustmentTests.test_bug036_writeoff_and_adjustment_prioritize_posted_lot_id_and_render_hidden_field_errors`, `sales.tests.SalesHistoryTests.test_bug035_and_bug036_draft_signature_includes_draft_id_and_checkout_renders_hidden_field_errors` | ✅ PASS |
| `BUG-037` | `HU-VEN-01b`, `HU-INV-02`, `HU-INV-03`, `HU-PROD-04` | `CA-VEN01B-03`, `RN-14`, `RN-28` | `QA-FIX-SALES-01`, `QA-FIX-INV-01`, `QA-FIX-CAT-01` | `sales/services.py::update_draft_line`, `inventory/services.py::_recalculate_product_average_cost`, `catalog/services.py::update_product` | `sales.tests.SalesHistoryTests.test_bug033_and_bug037_inactive_category_or_product_blocks_search_draft_line_update_and_checkout`, `inventory.tests.PhysicalAdjustmentTests.test_bug005_writeoff_and_physical_adjustment_recalculate_average_cost`, `catalog.tests.ProductExpirationsTests.test_bug004_product_barcode_update_preserves_historical_sale_line_snapshot` | ✅ PASS |

> **Complemento de auditoría · 09/11/2026.** Los siete criterios de AUTH-01/02 tienen evidencia acotada en el cierre. AUTH-01/CA-04 permanece PARCIAL transversal. Las marcas históricas conservan su fecha. [Resultados de etapa 01](auditoria_por_etapas/resultados/ETAPA-01.md) · [Decisiones y traspaso](auditoria_por_etapas/resultados/anexos/ETAPA-01-cierre-y-traspaso.md)

> **Complemento de auditoría ·09/11/2026 (cierre02-D).** 11 HU/33 CA:15 CUMPLE muestra,3 PARCIAL por nombres/apellidos y confirmación,15 PREVISTO/FUTURO. AUTH03 R1 seleccionado; USR01..05 adicional implementado, auditado en navegador/servidor.163/163 métodos,32/32 salida,20/20 empleados y6 escenarios PostgreSQL. Eventos técnicos R1 siguen INCUMPLE; propuestas/decisiones no aceptadas automáticamente. AUTH04a/04b/05,USR06 yLOG01 no disponibles. Estados históricos preservados. [Resultados y límites](auditoria_por_etapas/resultados/ETAPA-02.md) · [Criterios](auditoria_por_etapas/resultados/anexos/ETAPA-02-criterios.md) · [Cierre y traspaso](auditoria_por_etapas/resultados/anexos/ETAPA-02-cierre-y-traspaso.md).

## Adenda vigente de catálogo · 09/11/2026 · DOC03-01

Las tablas de R1 conservan el criterio histórico de categoría sembrada. La decisión aceptada para el catálogo actual sustituye ese alcance en HU-PROD-02/CA01 por cualquier categoría activa, con UND y vencimiento obligatorio; los otros cuatro criterios no cambian por esta decisión.

| ID vigente | Resultado requerido | Actor / referencias | Evidencia y límite |
|---|---|---|---|
| HU-PROD-02/CA01, revisión DOC03-01 | Alta en categoría activa arbitraria; inactiva/inexistente rechazada; UND y control de vencimiento obligatorios | ADMIN; RN03/29; HU-PROD-02:218 | [Auditoría03-F](auditoria_por_etapas/resultados/anexos/ETAPA-03-F-alcance.md), nueva ejecución identificada allí; no heredar PASS histórico |
| HU-PROD-01, actores DOC-00-14 | ADMIN/ALMACENERO consultan catálogo; VENDEDOR solo consulta autorizada en venta | Instrucción explícita del usuario, RN29, VEN01b | Misma evidencia03-F; no ampliar permiso de vendedor al catálogo |

El mínimo máximo sigue PARCIAL y el código editable conserva DOC03-02. Esta adenda no cambia los resultados de pruebas anteriores, la categoría de seis CA futuros ni la cobertura de otros módulos.

**HU-PROD-04/CA03 revisado, DOC03-02 (09/11/2026):** esperado ADMIN corrige código único conservando UUID/referencias e históricos; duplicado/inválido rechaza sin cambios. Implementación ProductEditForm→update_product; evidencia nueva en el anexo03-G. La fila/resultado histórico que exigía bloqueo no se reetiqueta. HU-PROD-03 conserva sus dos CA sin ejecución física; la entrada de teclado simulada no equivale al lector real. [Detalle y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-G-codigo-y-lector.md).


## Adenda de auditoría03-I · 10/11/2026

| Requisito vigente | Implementación | Evidencia nueva | Resultado |
|---|---|---|---|
| PROD02-CA04/RN06: entero0..999999, alta omitida10 | Formularios, Product, servicios y CHECK0005 | H01–12 repetidos en03-I; ProductPolicyTests; PG-I07 | CUMPLE muestra; máximo aceptado |
| PROD02-CA01/PROD04-CA04: nombre único ignorando mayúsculas/espacios redundantes | search_name UNIQUE, savepoint y error de name | I01–09;8 métodos nuevos; carreras PG-I04/05, inactivoPG-I06, históricoPG-I08 | CUMPLE muestra |
| Migración sin alterar datos incompatibles | catalog.0005 preflight | PG-I01/02 abortan sin cambios; PG-I03 éxito conservando campos comerciales | CUMPLE aislado; uso real PENDIENTE |

91/91 métodos de catálogo,36/36 comprobaciones Chrome/HTTP/ORM,8/8 PostgreSQL. Primer catálogo90/91 por fixture de dos productos con igual nombre: adaptado al contrato conservando aserciones de disponibilidad; evidencia inicial retenida. Tablas históricas mantienen su fecha y no son resultados de esta ejecución.

[Evidencia y límites03-I](auditoria_por_etapas/resultados/anexos/ETAPA-03-I-politicas.md).


## Ciclo de estado de categoría · 10/11/2026

| ID suplementario | Superficie | Evidencia |
|---|---|---|
| PROP-E00-HU-02 / J-CA1 | Lista, revisión de efectos, cancelar, volver y recargar | J01–03, J19, J23–25 |
| J-CA2 | Confirmación, consulta de catálogo/venta, carga y entrada, línea de borrador, cobro y constancia | J04, J07–12, J20, J26 |
| J-CA3 | Datos de revisión y actualización de versión en una sola escritura | J05/06 y J21/22, J-R1–R3 en dos motores |
| J-CA4 | ADMIN, ALMACENERO, VENDEDOR y visitante | J13/14 y pruebas de acceso de catálogo |

Los cuatro criterios tienen evidencia en la muestra de 03-J. Se contabilizan aparte de los 27 CA base.

[Auditoría 03-J](auditoria_por_etapas/resultados/anexos/ETAPA-03-J-estado-categoria.md).

## Reactivación de producto · HU-PROD-05/CA02

El 10/11/2026 el usuario aceptó PROP-03E-CA01 como aclaración del criterio existente. ADMIN habilita la ficha, ALMACENERO consulta el motivo de disponibilidad y VENDEDOR con turno abierto consulta el precio y las unidades vigentes. Se comprobaron cinco fichas en Chrome con lotes futuros, vencidos, con vencimiento hoy, sin lotes y con categoría suspendida. El informe de etapa conserva los resultados por ficha y la comparación de constancia, borrador e inventario. [Etapa 03, corte K](auditoria_por_etapas/resultados/ETAPA-03.md#etapa-03-k).

## Casos complementarios de catálogo · 10/11/2026

| HU y criterio | Evidencia del corte fechado (ver vigencia 03-P/W al final) |
|---|---|
| HU-PROD-04/CA01–05 · Edición de una misma ficha por dos ADMIN | Guardado obsoleto rechazado, recuperación, reenvío idéntico y conservación de los datos históricos. Chrome con dos cuentas y comprobación de persistencia. Dos carreras en PostgreSQL y tres en SQLite. [Corte 03-K7](auditoria_por_etapas/resultados/anexos/ETAPA-03-K7-edicion-y-relectura.md). |
| HU-PROD-02/CA03, HU-PROD-03/CA01, HU-PROD-04/CA03 · PROP-03K-RELECTURA | Captura opcional mientras el diálogo está abierto, revisión, cancelación y guardado expreso. Las pruebas con teléfono y las efectuadas por teclado tienen registros separados. CA02 del lector, advertencia inmediata de duplicado, sigue prevista. [Captura en Chrome](auditoria_por_etapas/resultados/anexos/ETAPA-03-K8-captura.md) · [Informe y cursor físico](auditoria_por_etapas/resultados/ETAPA-03.md). |
| INV-01a/01b, RN-03 y dependencias de baja y venta | Recepción de varios productos y presentación por paquete, conservación de lotes, cuarentena y retiros selectivos. Once pruebas integrales propuestas para sus etapas. [Propuestas y brechas](auditoria_por_etapas/resultados/anexos/ETAPA-03-recepcion-y-retiros-pendientes.md). |


**Ejecución03-N/O,10/11/2026:** PROD04/CA05→4carrerasPG/27checksChrome; PROD03/CA02→vista product_barcode_check, diálogo y campo manual→8métodosAPI y33checksChrome. Regresión326/326. Roles, formato64, normalización/inactivos, ficha propia, respuesta tardía, red fallida y sinJS probados. Lectura física del aviso nuevo NO EJECUTADA; no sustituir con emulación ni cerrar otras etapas. [Detalle y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-N-O-reclasificacion-y-duplicados.md).

**Vigencia 03-P/W, 10/11/2026:** las filas y adendas anteriores conservan su fecha; el aviso de PROD03/CA02 fue probado físicamente en P. El flujo de CA01 y su discrepancia literal están precisados en W; la conciliación individual enlaza evidencia sin modificar resultados históricos. [Matriz 03-W](auditoria_por_etapas/resultados/anexos/ETAPA-03-W-conciliacion.md).

**Actualización03-X,11/11/2026 (ejecución10/11):** PROD03/CA02 queda PARCIAL en la frontera EAN13/UPC12: seis lecturas físicas recibieron12 dígitos ante una ficha almacenada con13 y el aviso no indicó duplicado. La unicidad literal conserva sus muestras favorables.69/69 controles navegador/HTTP/ORM,16/16 servicio/DB y9/9 observación física; estos últimos acreditan la observación, no la equivalencia. DEC-03X-IDENTIDAD y PROP-03X-CA01..03/T01..03 son propuestas pendientes, sin cambio funcional, fusión ni migración. No se modifican estimaciones/sprints históricos ni se aprueban otras etapas. [Evidencia, alternativas y criterios](auditoria_por_etapas/resultados/anexos/ETAPA-03-X-codigos-ean-upc.md).

**Actualización 03-Y · 11/11/2026.** PROD03/CA02 CUMPLE en las muestras literales y GTIN admitidas. Evidencia de Chrome, teléfono, rechazo de valores concatenados como GTIN y colisiones concurrentes. La recepción de paquetes y el retiro por lote siguen en sus tramos. [Evidencia 03-Y](auditoria_por_etapas/resultados/anexos/ETAPA-03-Y-identidad.md).

**03-Z · 11/11/2026.** PROD03/CA01 y PROD04/CA03, relecturas con pérdida de selección y edición de anteriores con históricos. [Casos, evidencia física y resultados](auditoria_por_etapas/resultados/anexos/ETAPA-03-Z-relectura-interna.md).

**03-AA · 11/11/2026.** PROP-03-RET-T01 parcialmente ejecutado en la frontera del catálogo. [Consultas y exactitud del saldo](auditoria_por_etapas/resultados/evidencias/03-AA-aa-box-20261111T165403451847Z-71d9a79a/browser.json).

**11/11/2026 · 03-AB, recepción.** INV-01a CA01–04 verificados en muestras de Chrome/PostgreSQL, CA05 parcial. INV-01b con costo posterior verificado y conflicto RN-01 abierto. H-03AB-01..03 corregidos,79 comprobaciones Chrome y337 métodos de regresión. [Detalle y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-AB-recepcion.md).

**11/11/2026 · 03-AC / 05-B.** H-03AC-01 corrige la validación transaccional de proveedor de recepción. H-03AC-02 aplica el aniversario exacto para el límite anunciado de20 años. PROV04 aporta la frontera de desactivación. 29 controles Chrome,4 carreras PostgreSQL,343 métodos de regresión. [Pruebas y pendientes](auditoria_por_etapas/resultados/anexos/ETAPA-03-AC-proveedor-y-fechas.md).

**11/11/2026 · 03-AD / 05-C.** INV01a/CA05 y RN-19 verificados mediante vencimiento, ingreso, UUID y exclusión de vencidos. H-03AD-01 corrigió modificación del instante por save y añadió inventory0006 para update, bulk_update y SQL directo. Migración ensayada en copia, despliegue pendiente. [Evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-AD-fefo-e-ingreso.md).


**Auditoría 11/11/2026 · 03-AH, propuesta pendiente.** DOC-03AH-01 requiere seleccionar cómo se valora stock vencido y cómo merma/ajuste afectan al promedio. PROP-03AH-CA01/02 y T-03AH-VAL01/TEST02 están propuestos, no aceptados ni implementados; T-03AH-TEST01 reproduce la divergencia y conservación histórica. No se alteran CA ni estados históricos. [Alternativas, criterios y pruebas](auditoria_por_etapas/resultados/anexos/ETAPA-03-AH-valoracion-vencidos.md).


**Auditoría 11/11/2026 · 03-AI.** PROP-03-RET-T05 dispone de muestra de pérdida de respuesta en reposición y reenvíos sin duplicación de lotes. No acredita idempotencia por intención: DOC-03AI-01 y PROP-03AI-REC01/TEST02 son propuestas pendientes. No modifica estados históricos. [Criterios, alternativas y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-AI-reposicion-respuesta.md).
