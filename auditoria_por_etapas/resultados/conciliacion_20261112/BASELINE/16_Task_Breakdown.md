# 16. Plan ejecutable de Tasks y Subtasks — Sprint 1 `R1-PMV`

> **Actualización 05/11/2026:** Desglose histórico de Sprint 1. Sus instrucciones de carga y seguimiento en Jira han quedado retiradas. Jira ya no se usa ni se evalúa en este proyecto; las referencias posteriores se conservan solo como contexto histórico. Véase [Guía de alcance y diferencias](21_Alcance_Actual_y_Diferencias.md).

> **Estado:** línea base obtenida mediante una simulación de planificación de los seis Developers. No acredita participación ni trabajo ejecutado; se carga inicialmente en Jira como `Por hacer`. El corte académico confirmado es `h=32` por Developer (martes 13 a las 20:00); véase `20_Corte_De_Exposicion_Martes.md`.

> **Corrección operativa del 12-oct-2026:** la ejecución vigente está en `prompts_sprint_1/03_RUTA_SIMPLE_DE_DESARROLLO.md`. `S1-PLAT-01` debe consolidar la base Django local y el remoto antes de abrir trabajo paralelo. Cuando una tarea AUTO muestra `S1-CI-01` como `[H]`, CI es obligatorio para cerrar/aceptar la tarea, pero no impide escribir ni ejecutar primero la prueba local. Las horas son topes de planificación, no una obligación de consumirlas.
>
> **Alcance inmutable:** 9 Stories, 40 Story Points. Las Tasks y Subtasks de este documento no llevan Story Points.

---

## 16.1 Resultado cuantitativo y reglas de uso

| Concepto | Línea base del Sprint 1 |
|---|---:|
| Stories seleccionadas | 9 |
| Story Points, solo en Stories | 40 SP |
| Tasks técnicas transversales | 16 |
| Subtasks pertenecientes a Stories | 51 |
| Total de Tasks + Subtasks | 67 |
| Trabajo técnico previsto | 216 h |
| Capacidad de referencia del Sprint completo | 240 h; hipótesis previa que se reestima con el tiempo real |
| Capacidad máxima hasta la exposición | 192 h-persona (6 × 4 × 8 h) |
| Reserva explícita de línea base | 24 h (10 %), no disponible para declarar alcance adelantado |
| Carga prevista por Developer | 36 h |
| Reserva por Developer | 4 h |

Reglas:

- Cada fila corresponde a una incidencia que se creará en Jira; ninguna se marca como terminada antes de producir y revisar su evidencia.
- `Task` representa trabajo compartido por varias Stories. `Subtask` pertenece a una de las nueve Stories.
- Las horas son una estimación de coordinación, no una conversión de Story Points. El responsable coordina la incidencia y el revisor debe ser una persona distinta.
- La estimación de cada incidencia incluye elaborar la evidencia y atender su revisión. Las Subtasks terminadas no convierten automáticamente una Story en `Hecho`.
- `[H]` significa dependencia dura: impide completar técnicamente la incidencia y se registra como `blocks / is blocked by`.
- `[I]` significa dependencia de integración o aceptación: permite desarrollar antes mediante contratos, fixtures o dobles de prueba, pero debe estar satisfecha para aceptar la Story. No debe registrarse como bloqueo estricto.
- En el corte de martes se registra tiempo real, trabajo restante y estado. Las 216 h no caben íntegramente en las 192 h-persona; después del corte se reestima sin ampliar alcance.
- El tiempo real, el trabajo restante, los Bugs y el estado vivo se registran solamente en Jira.

### Abreviaturas de responsables

| Código | Developer |
|---|---|
| D1 | Des.1 - Velasquez |
| D2 | Des.2 - Nolasco |
| D3 | Des.3 - Castillo |
| D4 | Des.4 - Alcalde |
| D5 | Des.5 - Walter Luis Colonia Infantas |
| D6 | Des.6 - Angeles |

---

## 16.2 Tasks técnicas transversales — 16 Tasks / 57 h

| ID | Tipo | Stories apoyadas / capa | Resultado observable | Trazabilidad | Predecesoras | Resp. | Revisor | h | Evidencia esperada |
|---|---|---|---|---|---|---|---|---:|---|
| S1-ARQ-01 | Task | Todas / arquitectura | Registrar stack aprobado, componentes, contratos HTTP, límites transaccionales y ambientes | DoR; DT-01 a DT-15 | Ninguna | D1 | D2 | 4 | ADR/acta técnica y contratos versionados |
| S1-PLAT-01 | Task | Todas / plataforma | Consolidar el remoto oficial y la base Django local en un único repositorio, con PR, guía y construcción reproducible | DoD-5,8 | Ninguna | D6 | D1 | 3 | PR de integración, repositorio único, guía y pruebas base |
| S1-CI-01 | Task | Todas / CI | Ejecutar en GitHub Actions análisis, pruebas, build y comprobación de migraciones en cada cambio revisable | DoD-5,6,8 | [H] S1-PLAT-01 | D3 | D4 | 4 | Workflow y ejecución inicial registrada |
| S1-DB-01 | Task | Todas / BD | Elaborar modelo lógico y diccionario con roles, cuentas, sesiones, categorías, productos, cargas, lotes, caja, turnos, ventas, detalles, asignaciones e idempotencia | RN-01, RN-03, RN-10, RN-12, RN-14, RN-19, RN-25, RN-26, RN-27, RN-28, RN-29 | [H] S1-ARQ-01 | D1 | D2 | 4 | Diagrama y diccionario trazado |
| S1-DB-02 | Task | Todas / BD | Crear migraciones versionadas que levanten PostgreSQL vacío sin pasos manuales | DoD-3; NFR-01, NFR-02, NFR-08 | [H] S1-DB-01 | D2 | D3 | 5 | Migraciones y log desde BD vacía |
| S1-DB-03 | Task | Todas / BD | Implementar claves, unicidad, checks, índices y protección de referencias históricas, cantidades no negativas, roles permitidos y vencimiento obligatorio de R1 | DoD-3; RN-10, RN-12, RN-25, RN-26 | [H] S1-DB-02 | D2 | D3 | 4 | Catálogo de restricciones e intentos rechazados |
| S1-DB-04 | Task | Todas / datos | Crear seeds idempotentes de roles, cuentas ficticias, categoría `Productos enlatados` y caja única, sin secretos reales | HU-AUTH-01; HU-PROD-02; HU-CAJA-01 | [H] S1-DB-02; [I] S1-SEC-02 | D5 | D6 | 3 | Comando repetido dos veces sin duplicados |
| S1-DB-05 | Task | Todas / datos de prueba | Proveer reinicio seguro y fixture pequeño del recorrido; el dataset 2 000/20 000 se genera aparte y solo después del flujo funcional | DoD-6,7; NFR-05 | [H] S1-DB-04 | D5 | D6 | 3 | Script con guardas, fixture funcional y volumen opcional |
| S1-SEC-01 | Task | Todas / seguridad y configuración | Externalizar secretos, configurar usuario de BD con mínimo privilegio y separar configuración de prueba/demostración | DoD-5; NFR-08, NFR-09 | [H] S1-ARQ-01 | D5 | D6 | 4 | Variables documentadas, permisos y prueba sin secretos en repositorio |
| S1-SEC-02 | Task | AUTH/PROD/INV/CAJA/VEN / seguridad | Definir baseline de hash, sesión/cookies, CSRF, validación de entradas, autorización de servidor y logs sin datos sensibles | DoD-5; HU-AUTH-01, HU-AUTH-03; RN-29; NFR-03, NFR-09 | [H] S1-SEC-01 | D5 | D6 | 4 | Checklist de seguridad y casos negativos |
| S1-ENV-01 | Task | Todas / ambiente local | Preparar configuraciones locales `test`/`demo`, arranque/reversión repetibles, health check y comprobación Chrome/Windows/1366×768 con teclado | Puerta de piloto; NFR-06, NFR-07, NFR-08, NFR-09 | [H] S1-PLAT-01, S1-DB-02, S1-SEC-01; [I] S1-CI-01 | D4 | D5 | 4 | Guía local, health check y comprobación de compatibilidad |
| S1-QA-DB-01 | Task | Todas / QA-BD | Verificar migraciones, restricciones, seeds y reset partiendo de una BD vacía | DoD-3,6 | [H] S1-DB-03, S1-DB-04, S1-DB-05, S1-CI-01 | D6 | D1 | 3 | Ejecución automatizada y reporte |
| S1-QA-DB-02 | Task | INV/VEN/CAJA / QA transaccional | Inducir fallos y demostrar rollback sin lotes, venta, cobro o cierre parciales | DoD-4; RN-25 | [H] S1-INV01A-TXDB, S1-VEN01C-TXDB, S1-CAJA02-SVC | D3 | D4 | 3 | Pruebas de fallo y consultas de integridad |
| S1-QA-DB-03 | Task | INV/CAJA/VEN / QA concurrente | Probar cargas, aperturas, cobros, correlativos, stock y cierres concurrentes sin duplicación ni negativos | RN-01, RN-10, RN-19, RN-25, RN-26 | [H] S1-CAJA01-CONC, S1-VEN01C-IDEM, S1-CAJA02-SVC; [I] S1-INV01A-TXDB | D3 | D4 | 4 | Suite concurrente `CT-CONC-01..05` y resultados repetibles |
| S1-OPS-DB-01 | Task | Todas / operación | Ejecutar `pg_dump` de demo, identificarlo por ambiente/fecha/commit y verificar checksum; documentar cifrado/destino/retención si no están autorizados | Puerta de piloto; NFR-10 | [H] S1-ENV-01, S1-DB-05 | D4 | D5 | 2 | Dump fuera de Git, comando y checksum verificado |
| S1-OPS-DB-02 | Task | Todas / operación | Restaurar el dump en una BD temporal PostgreSQL 17 y realizar comprobaciones de integridad y smoke test corto | Puerta de piloto; NFR-10 | [H] S1-OPS-DB-01, S1-QA-DB-01; [I] nueve Stories integradas | D4 | D5 | 3 | Log, tres comprobaciones, duración y smoke test |
| **Subtotal** |  |  | **16 Tasks** |  |  |  |  | **57** |  |

---

## 16.3 `HU-AUTH-01` — Ingresar con mi cuenta — 6 Subtasks / 16 h

| ID | Tipo / capa | Resultado observable | CA/RN/NFR | Predecesoras | Resp. | Revisor | h | Evidencia esperada |
|---|---|---|---|---|---|---|---:|---|
| S1-AUTH01-UI | Subtask / UI | Formulario accesible de ingreso, mensaje general y navegación por puesto sin filtrar datos sensibles | CA1-4; NFR-06 | [H] S1-ARQ-01, S1-PLAT-01; [I] S1-AUTH01-SVC | D6 | D1 | 3 | Capturas y comprobación de teclado/foco |
| S1-AUTH01-SVC | Subtask / servicio-BD | Normalizar correo, verificar hash y estado activo, crear sesión de servidor y devolver siempre error general ante rechazo | CA1-3; RN-12; NFR-03, NFR-09 | [H] S1-DB-02, S1-SEC-02; [I] S1-DB-04 | D5 | D6 | 4 | Pruebas de servicio y sesión persistida |
| S1-AUTH01-AUTHZ | Subtask / seguridad | Autorizar cada operación en servidor y ocultar rutas/menús no permitidos según matriz de permisos | CA1,4; RN-29; NFR-03 | [H] S1-AUTH01-SVC, S1-SEC-02 | D5 | D6 | 3 | Matriz y respuestas permitida/prohibida |
| S1-AUTH01-AUTO | Subtask / QA automática | Automatizar ingreso válido, correo/clave erróneos, cuenta inactiva y URL prohibida | CA1-4 | [H] S1-AUTH01-SVC, S1-AUTH01-AUTHZ, S1-CI-01 | D5 | D6 | 3 | Suite verde en CI |
| S1-AUTH01-MAN | Subtask / QA manual | Documentar y ejecutar los cuatro criterios con cuentas ficticias | CA1-4 | [H] S1-AUTH01-UI, S1-AUTH01-AUTO | D1 | D2 | 1.5 | Caso paso a paso y resultado real |
| S1-AUTH01-REV | Subtask / revisión independiente | Verificar criterios, autorización directa y evidencias por una persona distinta | CA1-4; DoD | [H] S1-AUTH01-MAN | D4 | D5 | 1.5 | Checklist independiente y observaciones/Bugs |
| **Subtotal** |  | **6 Subtasks** |  |  |  |  | **16** |  |

## 16.4 `HU-AUTH-03` — Salir de mi cuenta — 5 Subtasks / 8 h

| ID | Tipo / capa | Resultado observable | CA/RN/NFR | Predecesoras | Resp. | Revisor | h | Evidencia esperada |
|---|---|---|---|---|---|---|---:|---|
| S1-AUTH03-UI | Subtask / UI | Mostrar `Salir`, advertir que el turno continúa y, si hay borrador, permitir confirmar descarte o cancelar; limpiar la pantalla al salir | CA1-3; RN-30 | [H] S1-AUTH01-UI; [I] S1-AUTH03-SVC | D3 | D4 | 1 | Capturas de salida sin/con borrador y cancelación |
| S1-AUTH03-SVC | Subtask / servicio-seguridad | Descartar atómicamente el borrador activo si se confirma, preservar el turno y su dueño, invalidar la sesión e impedir reutilización | CA1-3; RN-29, RN-30; NFR-03, NFR-09 | [H] S1-AUTH01-SVC, S1-AUTH01-AUTHZ | D5 | D6 | 3 | Borrador/sesión/turno antes y después |
| S1-AUTH03-AUTO | Subtask / QA automática | Automatizar logout sin borrador, confirmación/cancelación con borrador, botón atrás, reingreso del dueño y bloqueo de otro vendedor | CA1-3 | [H] S1-AUTH03-UI, S1-AUTH03-SVC, S1-CI-01 | D5 | D6 | 2 | Suite verde en CI |
| S1-AUTH03-MAN | Subtask / QA manual | Ejecutar las variantes de salida y comprobar sesión, borrador, turno, pantalla limpia y propiedad del vendedor | CA1-3 | [H] S1-AUTH03-AUTO | D2 | D3 | 1 | Caso manual y capturas |
| S1-AUTH03-REV | Subtask / revisión independiente | Comprobar todos los criterios y la decisión aprobada sobre turno/venta pendiente | CA1-3; DoD | [H] S1-AUTH03-MAN | D4 | D5 | 1 | Checklist y referencia de decisión |
| **Subtotal** |  | **5 Subtasks** |  |  |  |  | **8** |  |

## 16.5 `HU-PROD-02` — Registrar producto enlatado — 5 Subtasks / 16 h

| ID | Tipo / capa | Resultado observable | CA/RN/NFR | Predecesoras | Resp. | Revisor | h | Evidencia esperada |
|---|---|---|---|---|---|---|---:|---|
| S1-PROD02-UI | Subtask / UI | Formulario accesible con nombre, código, categoría, unidad, precio y mínimo; informa que el control de vencimiento es obligatorio y que la fecha se registrará por lote | CA1-5; RN-06, RN-27 | [H] S1-ARQ-01; [I] S1-PROD02-SVC | D3 | D4 | 4 | Capturas, foco, validaciones y estados |
| S1-PROD02-SVC | Subtask / servicio-BD | Autorizar ADMIN; validar y persistir nombre, código normalizado único, categoría sembrada, unidad, precio decimal, mínimo 10 por defecto y control de vencimiento obligatorio, con cero stock | CA1-5; RN-06, RN-27, RN-29 | [H] S1-DB-03; [I] S1-AUTH01-AUTHZ | D2 | D3 | 5 | Registro completo persistido y entradas/duplicado rechazados |
| S1-PROD02-AUTO | Subtask / QA automática | Automatizar registro válido, código repetido, precio y mínimo inválidos, default y no vendible sin lotes | CA1-5 | [H] S1-PROD02-SVC, S1-CI-01 | D2 | D3 | 3 | Suite verde en CI |
| S1-PROD02-MAN | Subtask / QA manual | Ejecutar todos los criterios con la categoría preparada y verificar cero existencias | CA1-5 | [H] S1-PROD02-UI, S1-PROD02-AUTO; [I] S1-DB-04 | D3 | D4 | 2 | Caso manual y consulta de catálogo |
| S1-PROD02-REV | Subtask / revisión independiente | Comprobar criterios, permisos, persistencia y evidencia | CA1-5; DoD | [H] S1-PROD02-MAN | D6 | D1 | 2 | Checklist y observaciones/Bugs |
| **Subtotal** |  | **5 Subtasks** |  |  |  |  | **16** |  |

## 16.6 `HU-INV-01a` — Existencias iniciales por lotes — 6 Subtasks / 20 h

| ID | Tipo / capa | Resultado observable | CA/RN/NFR | Predecesoras | Resp. | Revisor | h | Evidencia esperada |
|---|---|---|---|---|---|---|---:|---|
| S1-INV01A-UI | Subtask / UI | Capturar uno o varios lotes y mostrar resumen, errores y confirmación sin guardar parcialmente | CA1-5 | [H] S1-ARQ-01; [I] S1-PROD02-UI, S1-INV01A-VALID | D3 | D4 | 3 | Capturas de lote único/múltiple y errores |
| S1-INV01A-VALID | Subtask / servicio | Autorizar ALMACENERO y validar cantidad entera positiva, costo decimal positivo, fecha posterior a hoy en Lima, lote normalizado/único y primera carga | CA1-3; RN-01, RN-03, RN-29; NFR-03 | [H] S1-DB-03; [I] S1-PROD02-SVC, S1-AUTH01-AUTHZ | D2 | D3 | 3 | Casos válidos, inválidos y de rol directo |
| S1-INV01A-TXDB | Subtask / servicio-BD | Guardar carga y lotes atómicamente, bloquear segunda carga, conservar ingreso y calcular costo promedio aprobado | CA1-5; RN-01, RN-14, RN-19 | [H] S1-DB-03, S1-INV01A-VALID; [I] S1-PROD02-SVC | D1 | D2 | 5 | Estado antes/después y rollback completo |
| S1-INV01A-AUTO | Subtask / QA automática | Automatizar múltiples lotes, inválido intermedio, vencido/hoy, segunda carga, costo promedio y rollback | CA1-5 | [H] S1-INV01A-TXDB, S1-CI-01 | D1 | D2 | 4 | Suite verde y consultas de integridad |
| S1-INV01A-MAN | Subtask / QA manual | Ejecutar carga única/múltiple y verificar existencias, lotes, costo y rechazo total | CA1-5 | [H] S1-INV01A-UI, S1-INV01A-AUTO | D4 | D5 | 2 | Caso manual y cálculos comparados |
| S1-INV01A-REV | Subtask / revisión independiente | Verificar criterios, atomicidad y decisiones de lote/costo sin usar el caso inválido de producto sin vencimiento | CA1-5; DoD | [H] S1-INV01A-MAN; [I] S1-QA-DB-02 | D6 | D1 | 3 | Checklist y observaciones/Bugs |
| **Subtotal** |  | **6 Subtasks** |  |  |  |  | **20** |  |

## 16.7 `HU-CAJA-01` — Abrir turno de caja — 6 Subtasks / 16 h

| ID | Tipo / capa | Resultado observable | CA/RN/NFR | Predecesoras | Resp. | Revisor | h | Evidencia esperada |
|---|---|---|---|---|---|---|---:|---|
| S1-CAJA01-UI | Subtask / UI | Formulario de apertura y resumen con monto, vendedor, fecha/hora y mensajes de bloqueo | CA1-4; RN-10, RN-29 | [H] S1-ARQ-01; [I] S1-CAJA01-SVC | D4 | D5 | 2 | Capturas de monto cero, positivo e inválido |
| S1-CAJA01-SVC | Subtask / servicio-BD | Validar monto decimal no negativo, vendedor autorizado y persistir apertura transaccional | CA1,2,4; RN-10, RN-29 | [H] S1-DB-03; [I] S1-AUTH01-AUTHZ | D4 | D5 | 3 | Turno persistido y entradas inválidas rechazadas |
| S1-CAJA01-CONC | Subtask / BD-concurrencia | Garantizar un único turno abierto global bajo dos aperturas simultáneas | CA3; RN-10 | [H] S1-CAJA01-SVC | D4 | D5 | 3 | Dos solicitudes concurrentes: una sola aceptada |
| S1-CAJA01-AUTO | Subtask / QA automática | Automatizar montos, permisos, datos guardados y apertura duplicada/concurrente | CA1-4 | [H] S1-CAJA01-CONC, S1-CI-01 | D6 | D1 | 4 | Suite verde en CI |
| S1-CAJA01-MAN | Subtask / QA manual | Ejecutar aperturas válidas e inválidas y verificar caja única | CA1-4 | [H] S1-CAJA01-UI, S1-CAJA01-AUTO | D1 | D2 | 2 | Caso manual y resumen de turno |
| S1-CAJA01-REV | Subtask / revisión independiente | Comprobar criterios, restricción global y evidencia | CA1-4; DoD | [H] S1-CAJA01-MAN | D1 | D2 | 2 | Checklist y observaciones/Bugs |
| **Subtotal** |  | **6 Subtasks** |  |  |  |  | **16** |  |

## 16.8 `HU-VEN-01b` — Preparar venta y revisar existencias — 5 Subtasks / 20 h

| ID | Tipo / capa | Resultado observable | CA/RN/NFR | Predecesoras | Resp. | Revisor | h | Evidencia esperada |
|---|---|---|---|---|---|---|---:|---|
| S1-VEN01B-UI | Subtask / UI | Buscar por nombre/código, agregar/cambiar/quitar líneas y mostrar precio, cantidad, importe, base, IGV y total | CA2,3,5; RN-27, RN-30 | [H] S1-ARQ-01; [I] S1-PROD02-UI, S1-VEN01B-SVC | D3 | D4 | 5 | Recorrido y capturas de la venta preparada |
| S1-VEN01B-SVC | Subtask / servicio-BD | Exigir turno propio abierto; crear el borrador `ACTIVE` con la primera línea válida, descartarlo al quitar la última, consultar stock vendible en Lima, validar enteros/stock y calcular importes sin descontar | CA1-5; RN-03, RN-27, RN-29, RN-30 | [H] S1-DB-03; [I] S1-AUTH01-AUTHZ, S1-INV01A-TXDB, S1-CAJA01-SVC | D3 | D4 | 6 | Respuestas de servicio, ciclo de vida del borrador y stock sin cambio |
| S1-VEN01B-AUTO | Subtask / QA automática | Automatizar búsqueda, turno cerrado, cantidades, vencidos, stock insuficiente, importes, creación con primera línea, descarte al quitar la última e inmutabilidad; medir búsqueda con el volumen objetivo | CA1-5; NFR-05 | [H] S1-VEN01B-SVC, S1-CI-01; [I] S1-ENV-01 | D2 | D3 | 3 | Suite verde y reporte `PT-SEARCH-01` con ambiente/muestra |
| S1-VEN01B-MAN | Subtask / QA manual | Ejecutar preparación completa, quitar la última línea y confirmar que ningún lote ni efectivo se modifica ni queda borrador activo vacío | CA1-5 | [H] S1-VEN01B-UI, S1-VEN01B-AUTO; [I] HU-INV-01a y HU-CAJA-01 integradas | D2 | D3 | 2 | Caso manual, cálculos y consulta de lotes |
| S1-VEN01B-REV | Subtask / revisión independiente | Comprobar criterios, persistencia del borrador, cálculos e integración con inventario/caja | CA1-5; DoD | [H] S1-VEN01B-MAN | D6 | D1 | 4 | Checklist y observaciones/Bugs |
| **Subtotal** |  | **5 Subtasks** |  |  |  |  | **20** |  |

## 16.9 `HU-VEN-01c` — Cobrar y descontar existencias — 8 Subtasks / 28 h

| ID | Tipo / capa | Resultado observable | CA/RN/NFR | Predecesoras | Resp. | Revisor | h | Evidencia esperada |
|---|---|---|---|---|---|---|---:|---|
| S1-VEN01C-UI | Subtask / UI | Capturar efectivo, informar faltante, mostrar vuelto y bloquear confirmaciones repetidas mientras se procesa | CA1,2,5 | [H] S1-VEN01B-UI; [I] S1-VEN01C-PAY | D3 | D4 | 4 | Capturas de pago insuficiente/exacto/mayor |
| S1-VEN01C-PAY | Subtask / servicio | Autorizar al VENDEDOR dueño, revalidar turno/borrador, efectivo decimal y calcular faltante/vuelto sin mutar datos ante rechazo | CA1,2,3; RN-25, RN-27, RN-29, RN-30; NFR-03 | [H] S1-DB-03; [I] S1-VEN01B-SVC, S1-CAJA01-SVC, S1-AUTH01-AUTHZ | D4 | D5 | 3 | Pruebas de cálculo, propiedad/rol y estado inalterado |
| S1-VEN01C-FEFO | Subtask / servicio-BD | Seleccionar y bloquear lotes vigentes por vencimiento, ingreso e identificador interno; dividir salida sin negativos | CA3; RN-03, RN-19 | [H] S1-DB-03; [I] S1-INV01A-TXDB | D1 | D2 | 5 | Asignaciones de lote y caso concurrente |
| S1-VEN01C-TXDB | Subtask / servicio-BD | Guardar venta, pago, detalles, asignaciones, stock y snapshots históricos en una transacción | CA3,4,6; RN-25, RN-28 | [H] S1-DB-03; [I] S1-VEN01C-PAY, S1-VEN01C-FEFO | D1 | D2 | 6 | Venta completa y fallos sin residuos |
| S1-VEN01C-IDEM | Subtask / servicio-BD | Generar correlativo atómico e inmutable y resolver reintentos mediante clave de idempotencia sin `MAX+1` inseguro | CA4,5; RN-25, RN-26 | [H] S1-VEN01C-TXDB | D2 | D3 | 2 | Misma respuesta al reintento y correlativos únicos |
| S1-VEN01C-AUTO | Subtask / QA automática | Automatizar pagos, FEFO, lotes vencidos, stock, rollback, snapshots, reintento y correlativo; medir cobro con el volumen objetivo | CA1-6; NFR-05 | [H] S1-VEN01C-PAY, S1-VEN01C-FEFO, S1-VEN01C-TXDB, S1-VEN01C-IDEM, S1-CI-01; [I] S1-ENV-01 | D2 | D3 | 3 | Suite verde, consultas de integridad y reporte `PT-CHECKOUT-01` |
| S1-VEN01C-MAN | Subtask / QA manual | Ejecutar cobro completo, fallo inducido y doble confirmación con verificación de caja/lotes | CA1-6 | [H] S1-VEN01C-UI, S1-VEN01C-AUTO; [I] S1-QA-DB-03, HU-VEN-01b integrada | D5 | D6 | 3 | Caso manual, cálculos y estados antes/después |
| S1-VEN01C-REV | Subtask / revisión independiente | Verificar los seis criterios, atomicidad, concurrencia, idempotencia y evidencia | CA1-6; DoD | [H] S1-VEN01C-MAN; [I] S1-QA-DB-02 | D6 | D1 | 2 | Checklist y observaciones/Bugs |
| **Subtotal** |  | **8 Subtasks** |  |  |  |  | **28** |  |

## 16.10 `HU-VEN-02a` — Constancia interna de venta — 5 Subtasks / 15 h

| ID | Tipo / capa | Resultado observable | CA/RN/NFR | Predecesoras | Resp. | Revisor | h | Evidencia esperada |
|---|---|---|---|---|---|---|---:|---|
| S1-VEN02A-UI | Subtask / UI | Mostrar constancia accesible con correlativo, fecha Lima, vendedor, caja, líneas, importes, efectivo, vuelto y leyenda legal visible | CA1-3; RN-26, RN-27 | [H] S1-ARQ-01; [I] S1-VEN02A-SVC | D6 | D1 | 4 | Captura/impresión y revisión de leyenda |
| S1-VEN02A-SVC | Subtask / servicio-BD | Recuperar por el correlativo del enlace «Última constancia» una venta autorizada desde snapshots, sin recalcular ni exponer costo | CA1,2,4; RN-26, RN-27, RN-28 | [H] S1-DB-03; [I] S1-VEN01C-TXDB, S1-VEN01C-IDEM | D6 | D1 | 3 | Consulta repetida con mismos datos/importes |
| S1-VEN02A-AUTO | Subtask / QA automática | Automatizar correlativo inmutable, contenido histórico, ruta de reapertura, autorización y leyenda obligatoria | CA1-4 | [H] S1-VEN02A-UI, S1-VEN02A-SVC, S1-CI-01 | D4 | D5 | 4 | Suite verde en CI |
| S1-VEN02A-MAN | Subtask / QA manual | Generar, cerrar y reabrir por correlativo la constancia y comparar todos los importes sin mostrar costo | CA1-4 | [H] S1-VEN02A-AUTO; [I] HU-VEN-01c integrada | D1 | D2 | 2.5 | Caso manual, captura y comparación |
| S1-VEN02A-REV | Subtask / revisión independiente | Comprobar contenido, permanencia y advertencia de no validez tributaria | CA1-4; DoD | [H] S1-VEN02A-MAN | D2 | D3 | 1.5 | Checklist y observaciones/Bugs |
| **Subtotal** |  | **5 Subtasks** |  |  |  |  | **15** |  |

## 16.11 `HU-CAJA-02` — Cerrar y cuadrar caja — 5 Subtasks / 20 h

| ID | Tipo / capa | Resultado observable | CA/RN/NFR | Predecesoras | Resp. | Revisor | h | Evidencia esperada |
|---|---|---|---|---|---|---|---:|---|
| S1-CAJA02-UI | Subtask / UI | Capturar contado no negativo y mostrar esperado, diferencia, exacto/sobrante/faltante, bloqueo y acta | CA1-4; RN-10, RN-30 | [H] S1-CAJA01-UI; [I] S1-CAJA02-SVC | D4 | D5 | 3.5 | Capturas de tres resultados y errores |
| S1-CAJA02-SVC | Subtask / servicio-BD | Autorizar al VENDEDOR dueño, bloquear/revalidar turno, impedir borrador activo con líneas y doble cierre, calcular movimientos confirmados y guardar cierre atómico frente a cobros concurrentes | CA1-5; RN-10, RN-25, RN-29, RN-30; NFR-03 | [H] S1-DB-03; [I] S1-CAJA01-CONC, S1-VEN01C-TXDB, S1-AUTH01-AUTHZ | D6 | D1 | 5 | Turno cerrado inmutable, permisos y carreras resueltas |
| S1-CAJA02-AUTO | Subtask / QA automática | Automatizar contado, cuadre, sobrante/faltante, bloqueo solo por borrador con líneas, habilitación al quitar la última, doble cierre, cobro concurrente y apertura posterior | CA1-5 | [H] S1-CAJA02-SVC, S1-CI-01 | D4 | D5 | 4 | Suite verde en CI |
| S1-CAJA02-MAN | Subtask / QA manual | Ejecutar cierre completo, comprobar bloqueo con líneas y habilitación tras quitar la última, y verificar que no se venda después y que otro vendedor abra el siguiente turno | CA1-5 | [H] S1-CAJA02-UI, S1-CAJA02-AUTO; [I] S1-QA-DB-03, HU-VEN-01c integrada | D2 | D3 | 3.5 | Caso manual, acta y consulta de turno |
| S1-CAJA02-REV | Subtask / revisión independiente | Comprobar cálculo, bloqueo, inmutabilidad, carrera cobrar/cerrar y evidencia | CA1-5; DoD | [H] S1-CAJA02-MAN; [I] S1-QA-DB-02 | D5 | D6 | 4 | Checklist y observaciones/Bugs |
| **Subtotal** |  | **5 Subtasks** |  |  |  |  | **20** |  |

---

## 16.12 Reconciliación completa

| Grupo | Incidencias | Horas |
|---|---:|---:|
| Tasks transversales | 16 | 57 |
| HU-AUTH-01 | 6 | 16 |
| HU-AUTH-03 | 5 | 8 |
| HU-PROD-02 | 5 | 16 |
| HU-INV-01a | 6 | 20 |
| HU-CAJA-01 | 6 | 16 |
| HU-VEN-01b | 5 | 20 |
| HU-VEN-01c | 8 | 28 |
| HU-VEN-02a | 5 | 15 |
| HU-CAJA-02 | 5 | 20 |
| **Total** | **67** | **216** |

## 16.13 Balance por Developer

| Developer | Tasks transversales | Subtasks de Stories | Trabajo previsto | Capacidad técnica | Reserva técnica |
|---|---:|---:|---:|---:|---:|
| D1 - Velasquez | 8 h | 28 h | **36 h** | 40 h | **4 h** |
| D2 - Nolasco | 9 h | 27 h | **36 h** | 40 h | **4 h** |
| D3 - Castillo | 11 h | 25 h | **36 h** | 40 h | **4 h** |
| D4 - Alcalde | 9 h | 27 h | **36 h** | 40 h | **4 h** |
| D5 - Walter Luis Colonia Infantas | 14 h | 22 h | **36 h** | 40 h (línea base) | **4 h** |
| D6 - Angeles | 6 h | 30 h | **36 h** | 40 h | **4 h** |
| **Equipo** | **57 h** | **159 h** | **216 h** | **240 h** | **24 h** |

Cada Developer dispone de 32 h hasta el corte. Aun en el caso irreal de dedicar todas esas horas a trabajo técnico, restan al menos 4 h de la carga asignada por persona; los eventos, Bugs y bloqueos aumentan ese trabajo restante. La reserva no autoriza nuevas Stories. Se usa para defectos, incertidumbre técnica y adaptación necesaria para proteger el Sprint Goal. Si se consume, se registra la causa en Jira.

---

## 16.14 Red de dependencias y camino crítico simulado

### Dependencias funcionales de integración

```text
HU-AUTH-01 ──┬──[I]──► HU-AUTH-03
             ├──[I]──► HU-PROD-02 ──[I]──► HU-INV-01a ─┐
             └──[I]──► HU-CAJA-01 ──────────────────────┴──[I]──► HU-VEN-01b
                                                            │
                                                            ▼
                                                       HU-VEN-01c
                                                         ├──[I]──► HU-VEN-02a
                                                         └──[I]──► HU-CAJA-02
```

Son enlaces de integración/aceptación: las capas pueden desarrollarse en paralelo desde contratos y fixtures; la Story no se acepta hasta demostrar la integración real.

### Ruta de precedencia y calendario nivelado calculados

```text
S1-ARQ-01 (4)
  → S1-DB-01 (4)
  → S1-DB-02 (5)
  → S1-DB-03 (4)
  → S1-INV01A-VALID (3)
  → S1-INV01A-TXDB (5)
  → S1-INV01A-AUTO (4)
  → S1-INV01A-MAN (2)
  → S1-INV01A-REV (3)
```

- Duración lógica máxima recalculada sobre todas las dependencias `[H]`: **34 horas de trabajo secuencial equivalente**. Esta cifra mide precedencia; no presupone que todas las tareas de responsables distintos se puedan ejecutar como una sola persona ni es, por sí sola, el calendario del Sprint.
- Al respetar el responsable propuesto, que una persona no ejecuta dos ítems a la vez y todas las dependencias `[H]`, el calendario técnico nivelado de esta WBS tiene un *makespan* de **45.5 horas** contado desde el fin del Planning. La secuencia completa está en 16.15.
- La hipótesis previa insertaba 2 h de Planning antes de esa ventana y la terminaba en h47.5 de un Sprint de 50 h brutas. Esa hipótesis no es la capacidad confirmada del corte: `h32` ocurre antes del fin de la ruta nivelada y solo permite mostrar el avance real.
- La red no contiene ciclos. La restauración puede probarse con fixtures reproducibles en paralelo y la puerta de piloto reutiliza esa evidencia junto con el recorrido integrado final.

No se fuerza una cadena artificial de nueve Stories: UI, servicios y pruebas se preparan en paralelo; solo la integración y aceptación mantienen el orden del recorrido del negocio.

---

## 16.15 Nivelación de referencia para el Sprint completo

Esta tabla es un pronóstico para validar que el plan completo es realizable, no evidencia de que el trabajo ya ocurrió. Para las primeras 32 h, la prioridad de demostración y el corte operativo son los de `20_Corte_De_Exposicion_Martes.md`; al terminar la exposición se reprograma usando las horas restantes reales de Jira.

| Tramo | D1 | D2 | D3 | D4 | D5 | D6 | Resultado de control |
|---|---|---|---|---|---|---|---|
| Día 1 | Arquitectura y comienzo del modelo | Revisión de arquitectura y preparación de migraciones | Pipeline CI y contratos de venta | Preparación de ambiente | Seguridad/configuración | Repositorio y build | Contratos, flujo de cambios y decisiones técnicas visibles |
| Días 2-3 | Modelo, inventario y FEFO | Migraciones, restricciones y producto | UI de acceso/producto/venta | Caja y despliegue | Seeds, sesión y autorización | UI común y prueba de BD vacía | Esquema reproducible; tres frentes funcionales activos |
| Días 4-5 | Transacción de lotes y sus pruebas | Producto, validación de lotes y QA de venta | Producto/venta preparados | Apertura única y UI de caja | Login/logout y seguridad | Revisiones de producto/inventario/caja | Producto, lotes, acceso y caja conectables |
| Días 6-7 | FEFO y transacción de venta | Idempotencia, correlativo y pruebas | Servicio/UI de preparación de venta | Pago, constancia y QA de caja | Casos de cobro | Constancia y servicio de cierre | Cobro íntegro listo para pruebas concurrentes |
| Día 8 | QA manual de flujos asignados | QA manual y revisión de constancia | Rollback y concurrencia | QA automática y backup | QA manual de cobro y revisiones | Revisiones independientes y cierre | Fallos, carreras y reintentos comprobados |
| Día 9 | Revisión y corrección | Revisión y corrección | Recorrido integrado | Restore y smoke test | Revisión y corrección | Recorrido y accesibilidad | Incremento candidato y evidencia completa |
| Día 10 | Cierre de evidencia y reserva restante | Cierre de evidencia y reserva restante | Cierre de evidencia y reserva restante | Cierre de evidencia y reserva restante | Cierre de evidencia y reserva restante | Cierre de evidencia y reserva restante | Validación final, Review y decisión de piloto sin ocultar defectos |

La simulación asigna 36 h de Tasks/Subtasks a cada Developer. No interpreta erróneamente las 40 h técnicas como una disponibilidad continua ni reserva el día 10 completo: los trabajos tienen dependencias y responsables concretos. La siguiente es la nivelación no preemptiva usada para comprobar que las 67 incidencias caben; `t=0` es el instante inmediatamente posterior a las 2 h de Planning real.

| Developer | Secuencia nivelada de sus ítems (`inicio–fin`, h) | Trabajo | Último fin |
|---|---|---:|---:|
| D1 - Velasquez | `S1-ARQ-01` 0–4; `S1-DB-01` 4–8; `S1-VEN01C-FEFO` 17–22; `S1-VEN01C-TXDB` 22–28; `S1-INV01A-TXDB` 28–33; `S1-INV01A-AUTO` 33–37; `S1-CAJA01-MAN` 37–39; `S1-VEN02A-MAN` 39–41.5; `S1-AUTH01-MAN` 41.5–43; `S1-CAJA01-REV` 43–45 | 36 h | 45 |
| D2 - Nolasco | `S1-DB-02` 8–13; `S1-DB-03` 13–17; `S1-PROD02-SVC` 17–22; `S1-INV01A-VALID` 22–25; `S1-PROD02-AUTO` 25–28; `S1-VEN01C-IDEM` 28–30; `S1-VEN01C-AUTO` 30–33; `S1-VEN01B-AUTO` 33–36; `S1-VEN01B-MAN` 36–38; `S1-CAJA02-MAN` 38–41.5; `S1-VEN02A-REV` 41.5–43; `S1-AUTH03-MAN` 43–44 | 36 h | 44 |
| D3 - Castillo | `S1-CI-01` 3–7; `S1-VEN01B-UI` 7–12; `S1-VEN01C-UI` 12–16; `S1-AUTH03-UI` 16–17; `S1-VEN01B-SVC` 17–23; `S1-PROD02-UI` 23–27; `S1-INV01A-UI` 27–30; `S1-PROD02-MAN` 30–32; `S1-QA-DB-02` 33–36; `S1-QA-DB-03` 36–40 | 36 h | 40 |
| D4 - Alcalde | `S1-CAJA01-UI` 4–6; `S1-CAJA02-UI` 6–9.5; `S1-ENV-01` 13–17; `S1-CAJA01-SVC` 17–20; `S1-VEN01C-PAY` 20–23; `S1-CAJA01-CONC` 23–26; `S1-CAJA02-AUTO` 26–30; `S1-VEN02A-AUTO` 30–34; `S1-OPS-DB-01` 34–36; `S1-INV01A-MAN` 37–39; `S1-OPS-DB-02` 39–42; `S1-AUTH01-REV` 43–44.5; `S1-AUTH03-REV` 44.5–45.5 | 36 h | **45.5** |
| D5 - Walter Luis Colonia Infantas | `S1-SEC-01` 4–8; `S1-SEC-02` 8–12; `S1-DB-04` 13–16; `S1-AUTH01-SVC` 16–20; `S1-DB-05` 20–23; `S1-AUTH01-AUTHZ` 23–26; `S1-AUTH01-AUTO` 26–29; `S1-AUTH03-SVC` 29–32; `S1-VEN01C-MAN` 33–36; `S1-AUTH03-AUTO` 36–38; `S1-CAJA02-REV` 41.5–45.5 | 36 h | **45.5** |
| D6 - Angeles | `S1-PLAT-01` 0–3; `S1-VEN02A-UI` 4–8; `S1-AUTH01-UI` 8–11; `S1-CAJA02-SVC` 17–22; `S1-VEN02A-SVC` 22–25; `S1-CAJA01-AUTO` 26–30; `S1-QA-DB-01` 30–33; `S1-PROD02-REV` 33–35; `S1-VEN01C-REV` 36–38; `S1-VEN01B-REV` 38–42; `S1-INV01A-REV` 42–45 | 36 h | 45 |

| Hora bruta del Sprint | Uso común / regla de capacidad |
|---|---|
| 0–2 | Planning real y ratificación: 2 h comunes por Developer. No se marca trabajo técnico como realizado. |
| 2–47.5 | Secuencia anterior desplazada 2 h. Cada Developer posee 9.5 h de huecos dentro de la ventana: se usan 6 h para coordinación flexible/rotativa y 3.5 h como reserva técnica. |
| 47.5–48 | Medio bloque de reserva/cierre de evidencia por Developer; completa las 4 h de reserva individual. |
| 48–50 | Review y Retrospective: 2 h comunes por Developer. La aceptación y las evidencias siguen siendo reales, nunca simuladas. |

La composición de `50 h brutas` descrita en esta referencia deja de ser un compromiso de capacidad: la capacidad confirmada antes de la exposición es de 32 h por Developer. Las últimas dos incidencias de Walter Luis Colonia Infantas permanecen explícitas (`S1-VEN01C-MAN`, `S1-CAJA02-REV`) y solo se inician cuando sus predecesoras `[H]` estén cumplidas.

---

## 16.16 Orden seguro de carga en Jira

1. Crear las 74 Stories del Product Backlog; dejar las 65 no seleccionadas sin Sprint ni versión.
2. Crear `R1-PMV` y cargar en Sprint 1 solo las nueve Stories/40 SP.
3. Crear las 16 Tasks transversales sin Story Points y enlazar las Stories apoyadas.
4. Crear las 51 Subtasks bajo su Story padre, también sin Story Points.
5. Cargar responsables, revisores, horas, trazabilidad y evidencia esperada.
6. Registrar como `blocks / is blocked by` únicamente los enlaces `[H]`; documentar los `[I]` como integración/aceptación.
7. Confirmar automáticamente los controles `67`, `216 h`, `36 h por Developer`, `24 h de reserva`, ausencia de ciclos, ruta de precedencia de `34 h` y nivelación de `45.5 h` tras Planning / fin técnico en hora `47.5`.
8. Comprobar las seis cuentas Jira, registrar inicio/corte, puntos, horas, responsables y disponibilidad de los seis Developers; no crear PO/SM ficticios.
9. Asignar el Sprint solo cuando las nueve Stories satisfagan la DoR.
10. Iniciar todas las incidencias en `Por hacer`; Jira registrará desde entonces el estado real.

## 16.17 Controles de salida antes de iniciar

- [ ] Stack, roles, logout, lotes, redondeos, correlativo, volumen y backup aprobados.
- [ ] 9 Stories y 40 SP dentro de Sprint 1; 65 Stories y 191 SP fuera del Sprint y sin versión.
- [ ] 16 Tasks y 51 Subtasks creadas sin Story Points.
- [ ] 216 h ratificadas y 36 h asignadas a cada Developer.
- [ ] Corte de exposición registrado: 32 h por Developer / 192 h-persona hasta martes 20:00; la ventana nivelada de 45.5 h se conserva como referencia para el Sprint completo.
- [ ] Responsable y revisor distintos en las 67 incidencias.
- [ ] Dependencias duras sin ciclos y dependencias de integración correctamente diferenciadas.
- [ ] Cada criterio cubierto por implementación, prueba automática, prueba manual y revisión independiente.
- [ ] Migraciones, seeds, reset, seguridad, CI, despliegue, backup y restore visibles en Jira.
- [ ] Ninguna prueba, evidencia, participación ni aceptación marcada como realizada antes de ocurrir.

---

## 16.18 Tareas y Subtareas de Corrección y Endurecimiento Post-Auditoría QA/UX (`BUG-001` a `BUG-037`)

Para preservar la trazabilidad del desglose técnico (WBS) con las correcciones aplicadas tras la auditoría de caos multi-rol y UX/UI (`REPORTE_CAOS_Y_UX_QA.md`), se registran las subtareas técnicas de remediación vinculadas a sus respectivas Historias de Usuario y módulos:

| Subtarea QA/Fix | Story Padre | Módulo | Descripción Técnica del Trabajo Realizado | Bugs Cerrados | Estado |
|---|---|---|---|---|---|
| `QA-FIX-IDENT-01` | `HU-USR-01`, `HU-USR-03`, `HU-AUTH-01`, `HU-AUTH-03` | `identity` | Bloqueo de cambio de rol con turno `OPEN` (`update_employee`), protección del último Admin activo, expiración temporal de 5 minutos (`login_locked_until`) y `SESSION_EXPIRE_AT_BROWSER_CLOSE = True` tras 5 intentos fallidos de login, resumen de lotes vencidos para `ADMIN` y `ALMACENERO` en `/inicio/`, corrección de marca en `/salir/`, eliminación de doble `<h1>` y botones Bootstrap huérfanos. | `BUG-001`, `BUG-016`, `BUG-017`, `BUG-019`, `BUG-020`, `BUG-021`, `BUG-023`, `BUG-026` | ✅ Hecho |
| `QA-FIX-UI-01` | Transversal (`S1-PLAT-01`) | `identity/static`, `templates` | Unificación del sistema de diseño en `identity/static/identity/app.css` para las 15 plantillas de Sprints 2 y 3 (`.btn`, `.table`, `.table-bordered`, `.align-middle`, `.form-control`, `.form-select`, `.badge`, `.row`, `.justify-content-center`, `.text-end`, `.text-primary`, `.alert-*`), encabezados dinámicos en `base.html`, y títulos por rol con único `<h1>` en `403.html` y `404.html`. | `BUG-018`, `BUG-020`, `BUG-031` | ✅ Hecho |
| `QA-FIX-CAT-01` | `HU-CAT-01`, `HU-CAT-02`, `HU-PROD-01`, `HU-PROD-02`, `HU-PROD-04` | `catalog` | Habilitación de todas las categorías activas en registro y edición de productos (`ProductEditForm`), activación/desactivación de categorías (`category-toggle`), preservación de categoría actual en `Product.clean()` al editar precio/nombre de productos con categoría desactivada, inmutabilidad de `SaleLine.product_snapshot_barcode` al actualizar código de barras en `update_product`, búsqueda por nombre o código de barras en `/productos/`, validación alfanumérica de `barcode` (`BARCODE_PATTERN`), rechazo de notación científica (`1e5`) y topes en `ProductEditForm`, cálculo de `average_cost` ponderado en `seed_demo`, y ruta alias `/productos/<id>/creado/`. | `BUG-004`, `BUG-009`, `BUG-013`, `BUG-021`, `BUG-023`, `BUG-028`, `BUG-030`, `BUG-031`, `BUG-033` | ✅ Hecho |
| `QA-FIX-INV-01` | `HU-INV-01a`, `HU-INV-01b`, `HU-PROV-01..04`, `HU-INV-02`, `HU-INV-03`, `HU-INV-06` | `inventory` | Creación de vista `/inventario/entrada/` (`stock-entry`), migraciones `0003_lot_supplier`, `0004_lot_is_initial` y `0005_lot_responsible` para registrar proveedor y almacenero responsable en cada lote individual, habilitación de lectura para `ADMIN` en `/inventario/cargas/<id>/` y botón `"Ver carga"` en `/inventario/stock/`, proveedor visible en lotes iniciales y posteriores del Kardex, filtro `category__is_active=True` en `InitialLoadProductForm` y `StockEntryProductForm`, recálculo de `average_cost` en entradas, mermas y ajustes físicos (`_recalculate_product_average_cost`), `@never_cache` y prioridad de `POST lot_id` con renderizado de errores de campos ocultos en mermas y ajustes, y ruta alias `/inventario/carga-inicial/<id>/creada/`. | `BUG-003`, `BUG-005`, `BUG-010`, `BUG-011`, `BUG-012`, `BUG-014`, `BUG-022`, `BUG-023`, `BUG-024`, `BUG-027`, `BUG-032`, `BUG-033`, `BUG-036` | ✅ Hecho |
| `QA-FIX-CASH-01` | `HU-CAJA-01`, `HU-CAJA-02`, `HU-CAJA-05` | `cash` | Propiedades `difference_type`, `difference_amount` y `get_difference_type_display` en `CashShiftClose`, validación contra notación científica y montos desmesurados en `CashOpeningForm` y `CashCloseForm`, visualización del vendedor titular y hora en `/caja/abrir/` cuando la caja está ocupada, y botón directo `"Ir a preparar venta"` en `cash_shift_opened.html`. | `BUG-002`, `BUG-009`, `BUG-022`, `BUG-023`, `BUG-031` | ✅ Hecho |
| `QA-FIX-SALES-01` | `HU-VEN-01a`, `HU-VEN-01b`, `HU-VEN-01c`, `HU-VEN-02a`, `HU-VEN-03`, `HU-VEN-05a..05b` | `sales` | Migración `0004_saleline_product` vinculando `SaleLine` a `Product`, validación de `product.is_active` y `category.is_active` en `_search_products`, `add_product_to_draft`, `update_draft_line` y `checkout_sale`, inclusión de `draft.pk`, nombre y código de barras en `_draft_signature` para impedir cobros cruzados entre borradores desde pestañas antiguas, renderizado de errores de campos ocultos en `sales_checkout.html`, preservación de totales descontados al fallar validación en `/ventas/cobrar/`, ocultamiento de `Nueva venta` para `ADMIN` en `sales_receipt.html`, y columna `Descuento (S/)` con totales en historiales. | `BUG-004`, `BUG-006`, `BUG-007`, `BUG-008`, `BUG-009`, `BUG-015`, `BUG-021`, `BUG-023`, `BUG-025`, `BUG-029`, `BUG-033`, `BUG-035`, `BUG-036`, `BUG-037` | ✅ Hecho |

## Adenda de tareas de auditoría03-F · 09/11/2026

Estas tareas técnicas/documentales aplican la decisión actual DOC03-01; no reestiman ni declaran completadas retrospectivamente las tareas de Sprint1.

| ID / tipo | Trabajo acotado | Dependencia | Estado y evidencia |
|---|---|---|---|
| AUD03F-DOC01 / tarea documental | Conciliar categoría arbitraria, UND/vencimiento y actores, preservando la línea base R1 | DOC03-01 aceptada por usuario; DOC-00-14 definido en pedido | Aplicada; [detalle y verificación](auditoria_por_etapas/resultados/anexos/ETAPA-03-F-alcance.md) |
| AUD03F-UI01 / tarea UI | Ajustar título y ayuda de alta al alcance aceptado | AUD03F-DOC01 | Implementada; resultado visual en el anexo |
| AUD03F-TEST01 / tarea de pruebas | Alta no enlatada, categorías/estados inválidos, unidad alterada, vencimiento protegido, consulta entre roles | AUD03F-UI01; datos ficticios aislados | Ejecución y omisiones en el anexo; no equivale a suite global |

**AUD03G-DOC01 / tarea documental:** aplicar DOC03-02 y registrar Barcode to PC Server sin duplicar HU. **AUD03G-TEST01 / tarea de pruebas:** repetir edición/código/histórico con datos aislados, comprobar entrada de teclado y separar dispositivo real no ejecutado. Tareas propuestas de incorporación del lector: perfil/foco, aviso de duplicado al terminar lectura, pruebas de dispositivo/reintento/permisos. Resultados y condiciones en el anexo03-G; no cambiar horas ni estados históricos de Sprint. [Detalle y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-G-codigo-y-lector.md).


## Adenda03-I · 10/11/2026 · tareas de reglas aceptadas

| ID | Requisito y tarea | Estado verificable |
|---|---|---|
| AUD03I-MIN01 | PROD02-CA04/RN06: máximo999999 en modelo/servicios y CHECK | Implementado;91 métodos catálogo, navegador y PG-I07 |
| AUD03I-NOM01 | PROD02-CA01/PROD04-CA04: clave única, rechazo de nombre con rollback y ayudas | Implementado;8 métodos nuevos incluidos en91, I01–09 navegador, PG-I04/05/06/08 |
| AUD03I-MIG01 | Migración0005: detectar conflictos antes de escribir, conservar nombres visibles/FK | Verificada PG-I01/02/03; despliegue real PENDIENTE |
| AUD03I-DOC01 | Conciliar decisiones, fuentes, matriz y cursor sin rehacer sprints | Documentado03-I |

No son HU nuevas ni ejecución completa de otros módulos.

[Evidencia y límites03-I](auditoria_por_etapas/resultados/anexos/ETAPA-03-I-politicas.md).


## PROP-E03-T01 · conciliación del 10/11/2026

Dentro de esta tarea se completaron la revisión previa de impacto, cancelación sin escritura y confirmación condicionada a la versión de la categoría. Se verificó el rechazo de reenvíos y de dos administradores con pantallas de distinta antigüedad en SQLite y PostgreSQL. La migración 0006 inicia en cero las versiones de categorías existentes. La carrera entre cambio de categoría y un cobro o entrada de mercadería simultáneos conserva su traspaso a la etapa 15.

[Auditoría 03-J](auditoria_por_etapas/resultados/anexos/ETAPA-03-J-estado-categoria.md).


**AUD03N-TEST01 / AUD03O-UI01 / AUD03O-TEST01,10/11/2026:** reclasificación concurrente verificada; PROP-03G-SCAN-T02 seleccionada e implementada como aviso de duplicado, consulta ADMIN de solo lectura, tratamiento de respuestas tardías/fallos, semántica accesible y botón deshabilitado distinguible. Pruebas4PG+27ChromeN,33ChromeO,326regresión incluidas8API. Pendiente prueba físicaO. No cambia horas ni estados históricos. [Detalle y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-N-O-reclasificacion-y-duplicados.md).

**Propuestas03-X,11/11/2026:** PROP-03X-T01, clasificar datos y posibles colisiones en copia; PROP-03X-T02, implementación condicionada a DEC-03X-IDENTIDAD; PROP-03X-T03, pruebas de representaciones, códigos internos, roles, histórico y concurrencia. Pendientes, sin horas/sprint asignados ni HU duplicada. [Criterios y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-X-codigos-ean-upc.md).

**Actualización 03-Y · 11/11/2026.** Se ensayó la migración literal de los datos previos, la reserva transaccional de claves, las búsquedas por tipo y las validaciones de navegador y servidor. Queda probar la concatenación de lecturas de códigos internos con longitud variable. [Evidencia 03-Y](auditoria_por_etapas/resultados/anexos/ETAPA-03-Y-identidad.md).

**11/11/2026 · 03-AB, recepción.** INV-01a CA01–04 verificados en muestras de Chrome/PostgreSQL, CA05 parcial. INV-01b con costo posterior verificado y conflicto RN-01 abierto. H-03AB-01..03 corregidos,79 comprobaciones Chrome y337 métodos de regresión. [Detalle y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-AB-recepcion.md).

**11/11/2026 · 03-AC / 05-B.** H-03AC-01 corrige la validación transaccional de proveedor de recepción. H-03AC-02 aplica el aniversario exacto para el límite anunciado de20 años. PROV04 aporta la frontera de desactivación. 29 controles Chrome,4 carreras PostgreSQL,343 métodos de regresión. [Pruebas y pendientes](auditoria_por_etapas/resultados/anexos/ETAPA-03-AC-proveedor-y-fechas.md).

**11/11/2026 · 03-AD / 05-C.** INV01a/CA05 y RN-19 verificados mediante vencimiento, ingreso, UUID y exclusión de vencidos. H-03AD-01 corrigió modificación del instante por save y añadió inventory0006 para update, bulk_update y SQL directo. Migración ensayada en copia, despliegue pendiente. [Evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-AD-fefo-e-ingreso.md).
