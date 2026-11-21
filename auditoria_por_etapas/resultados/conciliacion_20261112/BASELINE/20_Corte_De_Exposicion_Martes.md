# 20. Corte operativo de exposición — Sprint 1 `R1-PMV`

> **Actualización 05/11/2026:** Corte histórico de octubre de 2026, no plan para la presentación actual. Jira ya no se usa ni se evalúa en este proyecto; las referencias posteriores se conservan solo como contexto histórico. Véase [Guía de alcance y diferencias](21_Alcance_Actual_y_Diferencias.md).

> **Corrección de ejecución 12-oct-2026:** antes de abrir más trabajo, `SCRUM-290` consolida el remoto y la base Django local. Para la exposición se prioriza un recorrido real integrado; pruebas simuladas, volumen, backup externo y documentación duplicada no sustituyen funcionalidad. Véase `prompts_sprint_1/03_RUTA_SIMPLE_DE_DESARROLLO.md`.

> **Supuesto de calendario:** el Sprint empieza el sábado 10 de octubre de 2026, hora Perú (`America/Lima`). El corte de exposición es el martes 13 de octubre a las 20:00. Si el botón **Start sprint** se pulsa a otra hora, se conserva este mismo plan en horas transcurridas y se reemplazan las fechas absolutas.
>
> **Regla de evidencia:** este documento programa trabajo futuro. No convierte una Task, Subtask o HU en `Hecho`; cada transición en Jira exige evidencia real enlazada.

## 20.1 Decisiones académicas confirmadas

| Tema | Decisión aplicable |
|---|---|
| Roles en Jira | Por instrucción del profesor, no se crean ni exigen cuentas de Product Owner ni Scrum Master. Jira tendrá a los seis Developers reales. |
| Aceptación | El profesor valida el resultado durante la exposición; no se registra una aceptación final anticipada en Jira. |
| Equipo disponible | Los seis Developers trabajan 8 horas reales cada día: sábado, domingo, lunes y martes. |
| Sprint | El Sprint puede continuar después de la exposición, pero nunca excede dos semanas. La exposición es un corte de avance, no el cierre obligado del Sprint. |
| Responsable de cierre | **D5 — Walter Luis Colonia Infantas** conserva las tareas finales de cobro/cierre: `S1-VEN01C-MAN` y `S1-CAJA02-REV`, además de verificar que el tablero y la evidencia real estén listos para la exposición. |

Los alias de los otros cinco Developers se mantienen hasta comprobarlos directamente en la lista de personas de Jira: D1 Velasquez, D2 Nolasco, D3 Castillo, D4 Alcalde y D6 Angeles. No se deducen correos electrónicos desde los alias ni se copian correos personales a documentos públicos.

## 20.2 Capacidad correctamente recalculada

| Cálculo | Resultado |
|---|---:|
| Developers | 6 |
| Horas por Developer hasta el corte | 4 días × 8 h = **32 h** |
| Capacidad máxima de personas hasta mar. 20:00 | **192 h-persona** |
| Trabajo técnico total del Sprint | **216 h** |
| Diferencia mínima aunque no existieran reuniones ni defectos | **24 h** |
| Ruta dura del plan | **34 h** desde el inicio técnico |
| Ventana técnica nivelada del Sprint completo | **45.5 h** después del Planning |

Conclusión: **no es posible ni correcto prometer las nueve HU terminadas el martes**. Incluso ignorando reuniones, 192 h son menores que las 216 h técnicas; además, la ruta dura de 34 h excede las 32 h disponibles para el corte. El Sprint mantiene sus 9 HU / 40 SP y continúa después de la demostración. Jira debe reflejar el avance real, no una terminación artificial.

El tiempo se registra en horas reales, no se duplica ni triplica por tratarse de domingo. Planning, Daily Scrum, coordinación, revisión de código, pruebas, corrección de Bugs y trabajo técnico cuentan como tiempo de equipo, pero solo una incidencia que cumpla su DoD puede pasar a `Hecho`.

## 20.3 Meta demostrable al corte `h=32`

La prioridad no es cerrar muchas tarjetas de forma ficticia: es dejar una base verificable, dos HU verticales con posibilidad real de `Hecho`, y el resto en el estado que demuestren sus evidencias.

| Estado objetivo al martes 20:00 | Contenido | Cómo se muestra al profesor |
|---|---|---|
| `Hecho`, solo si hay evidencia | `HU-AUTH-01` y `HU-PROD-02` (10 SP) | Ingreso con roles, autorización servidor, alta de producto enlatado sin stock; pruebas, PR/revisión y evidencia enlazadas. Si falta una prueba o revisión, quedan `En revisión`, no `Hecho`. |
| `En revisión` / `En progreso` | `HU-CAJA-01` y `HU-INV-01a` | Apertura única y carga por lotes pueden demostrarse únicamente hasta el punto realmente integrado. Se muestran subtareas, horas, impedimentos y pruebas aún pendientes. |
| `En progreso` | `HU-VEN-01b`, `HU-VEN-01c`, `HU-VEN-02a`, `HU-CAJA-02`, `HU-AUTH-03` | Mostrar contratos, UI o servicios terminados solo si existen; nunca simular un cobro, una constancia o un cierre que aún no pasó sus pruebas. |
| Evidencia transversal | Arquitectura, plataforma, CI, migraciones, constraints, seeds, seguridad y ambiente | Presentar enlaces reales al repositorio, pipeline, migración y tablero, con estado/resultado real. |

La cifra **10 SP** es el objetivo de historias completas posible al corte, no una afirmación de que ya están completadas. Si una de ellas no cumple todos sus criterios, la cantidad correcta de HU `Hecho` será menor. El profesor podrá comprobar simultáneamente el avance de las Tasks/Subtasks y las horas registradas.

## 20.4 Secuencia priorizada de las primeras 32 horas

`h=0` es el instante inmediatamente posterior al inicio real del Sprint. Las dependencias `[H]` de `16_Task_Breakdown.md` siguen siendo obligatorias. Esta tabla adelanta el trabajo que habilita una demostración vertical; no reduce controles de seguridad, base de datos, pruebas ni revisión.

| Ventana | Resultado prioritario | Ítems de referencia | Dueño principal |
|---|---|---|---|
| h0–8 | Contratos, repositorio, CI, arquitectura, modelo y seguridad base | `S1-ARQ-01`, `S1-PLAT-01`, `S1-CI-01`, `S1-DB-01`, `S1-SEC-01` | D1, D3, D5 Walter, D6 |
| h8–17 | Migraciones desde BD vacía, constraints, sesión/autorización y UI de acceso/producto/caja | `S1-DB-02`, `S1-DB-03`, `S1-SEC-02`, `S1-AUTH01-*`, `S1-PROD02-UI`, `S1-CAJA01-UI` | D2, D3, D4, D5 Walter, D6 |
| h17–26 | Servicios de acceso, producto, inventario y caja; seeds/fixtures; pruebas automatizadas iniciales | `S1-DB-04`, `S1-DB-05`, `S1-AUTH01-*`, `S1-PROD02-SVC`, `S1-INV01A-VALID`, `S1-CAJA01-SVC/CONC` | Equipo; D5 Walter cierra seguridad y acceso |
| h26–32 | Pruebas y revisión de acceso/producto; integración inicial de carga/caja; corte honesto en Jira | `S1-AUTH01-AUTO/MAN/REV`, `S1-PROD02-AUTO/MAN/REV`, `S1-CAJA01-AUTO/MAN`, `S1-INV01A-TXDB/AUTO`, `S1-QA-DB-01` | D1, D2, D4, D5 Walter, D6 |

Después del corte, Walter Luis Colonia Infantas ejecuta el ensayo manual de cobro `S1-VEN01C-MAN` cuando sus predecesoras reales estén terminadas y realiza la revisión independiente final de cierre `S1-CAJA02-REV`. Ninguna de esas dos tareas se adelanta por calendario si falla una predecesora.

## 20.5 Tablero y exposición

1. Pulsar **Start sprint** en la hora real de inicio y tomar una captura inicial del tablero, sin incidencias adelantadas a `Hecho`.
2. Cada Developer registra diariamente tiempo real contra la Task/Subtask en la que trabajó, actualiza `Tiempo restante` y enlaza PR, commit, pipeline, captura o prueba cuando exista.
3. Usar estados inequívocos: `Por hacer`, `En progreso`, `En revisión`, `Bloqueado` y `Hecho`. Si el flujo no tiene esos nombres, mapearlos sin alterar su significado.
4. El martes antes de las 20:00, congelar una vista del tablero, burndown y reporte de tiempo. Mostrar primero la hora real transcurrida y luego las HU con evidencia.
5. Exponer solo el recorrido que funcione en ese instante. Explicar las HU restantes como `En progreso` con sus subtareas, dependencias e impedimentos visibles.
6. El profesor realiza la validación académica presencial. No se crea un falso campo de aceptación final ni se marca `Hecho` por haber expuesto.

## 20.6 Trabajo de domingo en Perú

Este equipo desarrolla un proyecto académico; por ello no existe una remuneración laboral que registrar en Jira y el domingo aporta **8 h reales**, no 16 ni 24.

En un empleo privado peruano, el domingo es el día de descanso semanal preferente, no una regla automática de “pago triple”. Si se trabaja el día de descanso y se concede descanso sustitutorio, puede no corresponder sobretasa. Si no se concede sustitución en la misma semana, el Decreto Legislativo 713 reconoce el pago por la labor más una sobretasa de 100 %; al sumar la remuneración ordinaria del descanso ya incluida para remunerados mensuales, suele explicarse como tres remuneraciones diarias. El “triple pago” citado por SUNAFIL corresponde de forma característica al trabajo en **feriado nacional** sin descanso sustitutorio, no al mero hecho de trabajar un domingo. Fuentes: [Decreto Legislativo 713, arts. 1–4](https://www.leyes.congreso.gob.pe/Documentos/DecretosLegislativos/00713.pdf) y [orientación de SUNAFIL sobre feriados](https://www.gob.pe/institucion/sunafil/noticias/1421054-sunafil-te-corresponde-un-triple-pago-si-trabajas-este-feriado-23).
