# 14. Sprint Planning 1 — `R1-PMV`

> **Actualización 05/11/2026:** Plan histórico de Sprint 1 y del corte de octubre de 2026; no es una instrucción de trabajo vigente. Jira ya no se usa ni se evalúa en este proyecto; las referencias posteriores se conservan solo como contexto histórico. Véase [Guía de alcance y diferencias](21_Alcance_Actual_y_Diferencias.md).

> **Estado actualizado 12-oct-2026:** Sprint activo y 67 ítems técnicos asignados. La auditoría de ejecución detectó una divergencia entre el remoto GitHub y la base Django local; `S1-PLAT-01 / SCRUM-290` debe consolidarlas antes de continuar trabajo paralelo. La ruta operativa vigente y simplificada está en `prompts_sprint_1/03_RUTA_SIMPLE_DE_DESARROLLO.md`.
>
> **Regla de honestidad:** ninguna casilla de participación, prueba, aceptación o trabajo realizado se marca por efecto de esta simulación. Al iniciar el Sprint, todas las incidencias comienzan en `Por hacer`.

## 14.1 Ficha del Sprint

| Campo | Línea base |
|---|---|
| Nombre en Jira | `Sprint 1 — PMV` |
| Inicio previsto | Sábado 10 de octubre de 2026, hora real que se registre al iniciar Jira |
| Corte de exposición | Martes 13 de octubre de 2026, 20:00 (America/Lima) |
| Fin máximo del Sprint | Viernes 23 de octubre de 2026; dos semanas calendario como máximo |
| Duración | Hasta 14 días calendario; sábado, domingo, lunes y martes son cuatro jornadas comprometidas de 8 h por Developer |
| Versión | `R1-PMV` |
| Sprint Goal | Venta en efectivo completa desde el ingreso hasta el cuadre de la caja única |
| Alcance | 9 Stories / 40 Story Points |
| Backlog posterior | 65 Stories / 191 SP, sin Sprint ni versión |
| Capacidad hasta la exposición | 192 h-persona: 6 Developers × 4 días × 8 h |
| Trabajo técnico del Sprint | 216 h; excede en 24 h la capacidad máxima del corte, aun sin reuniones ni defectos |
| Capacidad posterior | Se registra con horas reales después de la exposición; no se inventa una disponibilidad de 50 h por Developer |
| Tasks transversales | 16 / 57 h |
| Subtasks de Stories | 51 / 159 h |
| Trabajo técnico total | 67 incidencias / 216 h |
| Reserva de línea base | 24 h de equipo, 4 h por Developer; utilizable solo dentro del Sprint máximo y no antes de registrar el avance real |
| Ruta de precedencia / cronograma nivelado | 34 h lógicas; 45.5 h de ventana técnica para todo el Sprint. Por sí sola excede el corte de 32 h y confirma que el martes no puede prometerse el Sprint completo |
| Velocidad histórica | No existe; aparecerá después de cerrar el primer Sprint |

Los 40 SP expresan tamaño relativo de las Stories. Las 216 h son topes iniciales para Tasks/Subtasks, no horas que deban consumirse; la implementación debe elegir la solución mínima de los prompts corregidos. No existe conversión entre ambas medidas.

## 14.2 Participación real y regla académica

### Registro mínimo antes de iniciar formalmente el Sprint

| Participante | Rol | Disponibilidad confirmada hasta mar. 20:00 | Asignación / evidencia requerida |
|---|---|:---:|---|
| Des.1 - Velasquez | Developer | 32 h | Validar la cuenta Jira y registrar tiempo real |
| Des.2 - Nolasco | Developer | 32 h | Validar la cuenta Jira y registrar tiempo real |
| Des.3 - Castillo | Developer | 32 h | Validar la cuenta Jira y registrar tiempo real |
| Des.4 - Alcalde | Developer | 32 h | Validar la cuenta Jira y registrar tiempo real |
| Des.5 - Walter Luis Colonia Infantas | Developer | 32 h | Dueño de tareas finales `S1-VEN01C-MAN` y `S1-CAJA02-REV`; validar cuenta Jira y registrar tiempo real |
| Des.6 - Angeles | Developer | 32 h | Validar la cuenta Jira y registrar tiempo real |

Los seis integrantes y sus cuentas asignables ya fueron comprobados y los 67 ítems técnicos están asignados en Jira. La validación académica final la realiza el profesor durante la exposición; no se registra una aceptación anticipada en Jira.

### Panel simulado de los seis Developers

| Perfil simulado | Perspectiva aplicada | Decisión de planificación |
|---|---|---|
| Des.1 - Velasquez | Arquitectura, datos, inventario y concurrencia | Acepta modelo relacional, locks ordenados, FEFO e invariantes con 36 h propuestas |
| Des.2 - Nolasco | Servicios, autenticación y seguridad | Acepta autorización server-side, transacciones e idempotencia con 36 h propuestas |
| Des.3 - Castillo | UI, HTMX y accesibilidad | Acepta contratos, estados de error, teclado y trabajo paralelo con 36 h propuestas |
| Des.4 - Alcalde | Caja, integración y operación | Acepta caja única, carrera cobro/cierre y despliegue reproducible con 36 h propuestas |
| Des.5 - Walter Luis Colonia Infantas | Datos iniciales, automatización y cierre | Ejecuta seeds, seguridad y matrices automáticas; queda con el ensayo manual de cobro y la revisión final de cierre |
| Des.6 - Angeles | QA, constancia y recuperación | Acepta snapshots, E2E, backup/restore y revisión con 36 h propuestas |

Este panel prueba coherencia del reparto; no afirma que las seis personas reales participaron.

## 14.3 Tema 1 — Por qué es valioso

### Sprint Goal

> Permitir que el minimarket complete una venta en efectivo desde el ingreso del trabajador hasta el cuadre de su única caja: registrar un producto enlatado, cargar sus lotes, abrir el turno, preparar y cobrar, descontar existencias por FEFO, entregar una constancia interna y cerrar la caja con integridad recuperable.

El Sprint valida el recorrido central con datos ficticios. Usuarios administrativos avanzados, proveedores, reposición, mermas, pagos digitales, reportes y comprobantes tributarios permanecen fuera de Sprint 1.

## 14.4 Tema 2 — Qué se pronostica completar

| Orden | Story | Resultado | SP | Dependencia de integración | Coordinación inicial | Revisión independiente |
|---:|---|---|---:|---|---|---|
| 1 | `HU-AUTH-01` | Ingresar con cuenta y autorización server-side | 5 | Datos/seguridad transversales | Des.5 - Walter Luis Colonia Infantas | Des.4 - Alcalde |
| 2 | `HU-AUTH-03` | Salir sin reutilizar sesión y resolver borrador/turno | 2 | `HU-AUTH-01` | Des.5 - Walter Luis Colonia Infantas | Des.4 - Alcalde |
| 3 | `HU-PROD-02` | Registrar producto enlatado no vendible sin stock | 5 | `HU-AUTH-01`, categoría seed | Des.2 - Nolasco | Des.6 - Angeles |
| 4 | `HU-INV-01a` | Confirmar una sola carga inicial multilot atómica | 5 | `HU-PROD-02` | Des.1 - Velasquez | Des.6 - Angeles |
| 5 | `HU-CAJA-01` | Abrir un único turno global | 5 | `HU-AUTH-01`, caja seed | Des.4 - Alcalde | Des.1 - Velasquez |
| 6 | `HU-VEN-01b` | Persistir borrador y revisar stock sin descontar | 5 | `HU-CAJA-01`, `HU-INV-01a` | Des.3 - Castillo | Des.6 - Angeles |
| 7 | `HU-VEN-01c` | Cobrar una vez, aplicar FEFO y confirmar todo o nada | 5 | `HU-VEN-01b` | Des.1 - Velasquez / Des.2 - Nolasco | Des.6 - Angeles |
| 8 | `HU-VEN-02a` | Mostrar/reabrir última constancia histórica | 3 | `HU-VEN-01c` | Des.6 - Angeles | Des.2 - Nolasco |
| 9 | `HU-CAJA-02` | Cerrar una vez, cuadrar y resolver carrera con cobro | 5 | `HU-CAJA-01`, integración con `HU-VEN-01c` | Des.6 - Angeles | Des.5 - Walter Luis Colonia Infantas |
|  | **Total** | **Recorrido completo** | **40** |  |  |  |

Las dependencias anteriores son de integración/aceptación. Interfaz, servicios y pruebas preparatorias pueden comenzar en paralelo mediante contratos y fixtures. Solo los enlaces `[H]` de `16_Task_Breakdown.md` se cargan como `blocks` en Jira.

## 14.5 Tema 3 — Cómo se realizará

### Composición del trabajo

| Grupo | Incidencias | Horas |
|---|---:|---:|
| Arquitectura, plataforma, CI, BD, seguridad, ambientes, QA-BD y recuperación | 16 Tasks | 57 |
| `HU-AUTH-01` | 6 Subtasks | 16 |
| `HU-AUTH-03` | 5 Subtasks | 8 |
| `HU-PROD-02` | 5 Subtasks | 16 |
| `HU-INV-01a` | 6 Subtasks | 20 |
| `HU-CAJA-01` | 6 Subtasks | 16 |
| `HU-VEN-01b` | 5 Subtasks | 20 |
| `HU-VEN-01c` | 8 Subtasks | 28 |
| `HU-VEN-02a` | 5 Subtasks | 15 |
| `HU-CAJA-02` | 5 Subtasks | 20 |
| **Total** | **67** | **216** |

### Capacidad individual simulada

| Developer | Tasks | Subtasks | Total | Capacidad técnica | Reserva técnica |
|---|---:|---:|---:|---:|---:|
| Des.1 - Velasquez | 8 | 28 | **36 h** | 40 h | **4 h** |
| Des.2 - Nolasco | 9 | 27 | **36 h** | 40 h | **4 h** |
| Des.3 - Castillo | 11 | 25 | **36 h** | 40 h | **4 h** |
| Des.4 - Alcalde | 9 | 27 | **36 h** | 40 h | **4 h** |
| Des.5 - Walter Luis Colonia Infantas | 14 | 22 | **36 h** | 40 h (línea base) | **4 h** |
| Des.6 - Angeles | 6 | 30 | **36 h** | 40 h | **4 h** |
| **Equipo** | **57** | **159** | **216 h** | **240 h** | **24 h** |

Las columnas Tasks/Subtasks contienen horas, no cantidad de incidencias. Para el corte de exposición cada Developer dispone de 32 h reales; por tanto, aun si las dedicara íntegramente a los ítems técnicos, quedan al menos 4 h de su carga planificada después del martes. La reserva absorbe defectos e incertidumbre y no permite incorporar otra Story.

### Red de integración del recorrido

```text
HU-AUTH-01 ──┬──► HU-AUTH-03
             ├──► HU-PROD-02 ──► HU-INV-01a ─┐
             └──► HU-CAJA-01 ─────────────────┴──► HU-VEN-01b ──► HU-VEN-01c
                                                                        ├──► HU-VEN-02a
                                                                        └──► HU-CAJA-02
```

### Ruta de precedencia y nivelación de recursos recalculadas

```text
S1-ARQ-01 (4) → S1-DB-01 (4) → S1-DB-02 (5) → S1-DB-03 (4)
→ S1-INV01A-VALID (3) → S1-INV01A-TXDB (5) → S1-INV01A-AUTO (4)
→ S1-INV01A-MAN (2) → S1-INV01A-REV (3)
```

- La ruta de precedencia más larga es de **34 h de trabajo secuencial equivalente**. Es un resultado del grafo, no el calendario final de una persona.
- Al respetar responsable único, orden de cada responsable y las dependencias `[H]`, la nivelación de las 67 incidencias requiere **45.5 h de ventana técnica** desde el final del Planning. La secuencia está explícita en `16_Task_Breakdown.md`.
- El calendario de 50 h era una hipótesis de capacidad de la línea base. Se reemplaza por el compromiso comprobable del corte: **32 h reales por Developer hasta el martes 20:00**. El Sprint completo continúa dentro del máximo de dos semanas y se reestima con el tiempo restante real después de la exposición.
- La exposición ocurre antes de que termine la ventana técnica completa: 32 h de calendario son menores que las 45.5 h niveladas. Se mantiene la reserva para defectos; no se utiliza para declarar trabajo no realizado.
- Grafo validado: **67 nodos, 0 referencias duras faltantes y 0 ciclos**. El corte y las prioridades de las primeras 32 h están en `20_Corte_De_Exposicion_Martes.md`.

### Cronograma por resultados verificables

| Jornada | Fecha / corte | Pronóstico observable; no estado anticipado |
|---:|---|---|
| 1 | Sáb. 10-oct | Inicio real en Jira; arquitectura, repositorio, CI, seguridad y modelo de datos trazables. |
| 2 | Dom. 11-oct | Migraciones, constraints, UI de acceso/producto/caja y contratos en progreso. El domingo cuenta como 8 h reales, sin multiplicador académico. |
| 3 | Lun. 12-oct | Seeds, servicios de acceso/autorización, producto, inventario y caja con sus pruebas iniciales. |
| 4 | Mar. 13-oct, 20:00 | Corte de exposición: tablero, horas reales, evidencias y solo las HU que cumplan DoD en `Hecho`; las demás permanecen con su estado real. |
| Después del corte | Hasta vie. 23-oct | Reestimar lo restante según Jira y continuar sin ampliar alcance. Walter Luis Colonia Infantas cierra `S1-VEN01C-MAN` y `S1-CAJA02-REV` cuando sus predecesoras se cumplan. |

Un hito que no se alcance se refleja como tal en Jira; nunca se mueve artificialmente una incidencia para coincidir con esta tabla.

## 14.6 Estrategia de calidad y simulación

Cada CA tiene implementación, prueba automática, prueba manual, revisión distinta y evidencia esperada en `03_Matriz_de_Trazabilidad_y_Pruebas.md`. La simulación de mesa cubre:

1. dos cargas iniciales simultáneas;
2. dos aperturas simultáneas;
3. dos ventas por las últimas unidades;
4. doble clic/reintento de cobro;
5. fallos inducidos en carga y cobro;
6. cobro concurrente con cierre y doble cierre;
7. constancia consultada después de cambiar datos maestros;
8. backup con checksum y restore en BD limpia.

La planificación supera la simulación cuando existe una respuesta determinista y trazada para cada escenario. Esto no significa que las pruebas del software hayan sido ejecutadas.

El recorrido completo de mesa, incluidos lote inválido, logout con borrador y restauración, se conserva en `17_Simulacion_6_Developers.md` con once escenarios y estado explícito `Coherente documental / no ejecutado`.

## 14.7 Riesgos y respuestas

| Riesgo | Señal | Respuesta acordada |
|---|---|---|
| Identidad Jira no comprobada | Un alias no coincide con su cuenta real o se asigna a otra persona | Detener solo la asignación afectada, comprobar `accountId`/nombre visible y corregir antes de registrar tiempo |
| Ruta crítica de BD se retrasa | `S1-DB-03` no termina antes del corte de h17 | Concentrar apoyo; proteger integridad, no eliminar constraints/migraciones |
| Sobreventa o duplicación | Una prueba deja stock negativo, dos ventas o dos correlativos | Bug bloqueante; Story no pasa DoD ni piloto |
| Caja inconsistente | Coexisten turnos, doble cierre o venta fuera del cuadre | Detener flujo y corregir transacción/locks |
| Autorización solo visual | URL directa modifica datos | Bug de seguridad bloqueante |
| Constancia mutable o con costo | Cambia tras editar producto o expone costo | Bloquear `HU-VEN-02a` y usar snapshots/DTO permitido |
| Dependencias convertidas en cadena total | Trabajo espera innecesariamente otra Story | Usar contratos/fixtures y distinguir `[H]` de `[I]` |
| Backup sin recuperación | Hay archivo, pero no restore satisfactorio | Piloto no autorizado |
| Consumir reserva antes del corte | Se usan horas de reserva con ruta crítica abierta | Swarming sobre el Sprint Goal; no quitar calidad ni declarar HU terminadas |
| Confundir simulación con evidencia | Casilla `Done/Aprobado` sin log real | Revertir estado y registrar solo `Pendiente` |

## 14.8 Resultado de la simulación de Planning

| Control | Resultado |
|---|---|
| 9 Stories / 40 SP seleccionadas | Pasa |
| 65 Stories / 191 SP fuera de Sprint y versión | Pasa |
| 41/41 CA trazados | Pasa |
| 16 Tasks + 51 Subtasks | Pasa |
| 216 h de trabajo técnico total | Pasa; línea base completa |
| Corte de martes: 192 h-persona < 216 h | Pasa; se reconoce que el Sprint completo no puede prometerse para la exposición |
| 36 h planificadas por Developer | Pasa como distribución del Sprint; cada uno dispone de 32 h hasta el corte |
| Reserva 24 h / 10 % | Pasa como reserva de Sprint, no como horas disponibles antes de la exposición |
| Responsable distinto de revisor en 67/67 incidencias | Pasa |
| Grafo duro acíclico y ruta de precedencia 34 h | Pasa |
| Nivelación por responsable: 45.5 h tras Planning | Pasa documentalmente para el Sprint completo; no es una promesa de terminar al corte de h32 |
| BD, seguridad, CI, despliegue, backup y restore visibles | Pasa |
| Evidencias reales inventadas | Pasa: ninguna |

**Veredicto de simulación: PASA DOCUMENTALMENTE — plan coherente y cargable en Jira, con nivelación de recursos explícita.**

**Veredicto para inicio real: GO ACADÉMICO CON CONTROLES.** Antes de pulsar *Start sprint* se comprueba la correspondencia de las seis cuentas Jira, las 32 h hasta el corte, el alcance de 9 HU/40 SP, las 216 h, las decisiones y la carga de Jira. El profesor valida el avance real durante la exposición; no se requiere PO ni SM en Jira.

## 14.9 Checklist previo a `Start sprint`

- [ ] Las seis cuentas Jira fueron comprobadas contra los seis Developers reales; ningún correo se dedujo ni se publica innecesariamente.
- [ ] Los seis Developers registran 8 h reales por día desde sábado hasta el corte del martes a las 20:00.
- [ ] Las decisiones `DEC-01..DEC-11` y `DT-01..DT-15` fueron ratificadas.
- [ ] Existen 74 Stories; solo 9 tienen Sprint 1 y `R1-PMV`.
- [ ] Existen 16 Tasks y 51 Subtasks sin Story Points.
- [ ] Se cargaron 216 h propuestas, responsables, revisores y evidencias esperadas.
- [ ] Solo dependencias `[H]` usan `blocks`; las `[I]` no bloquean inicio preparatorio.
- [ ] Se registró el instante real de inicio; el tablero tiene el corte `h=32` y el Sprint no excede dos semanas.
- [ ] Se revisó el calendario nivelado de 45.5 h como plan total, sin usarlo para afirmar terminación el martes.
- [ ] Walter Luis Colonia Infantas tiene asignadas las tareas finales `S1-VEN01C-MAN` y `S1-CAJA02-REV`.
- [ ] Las nueve Stories cumplen DoR.
- [ ] Todas las incidencias están en `Por hacer`, sin pruebas ni evidencias ficticias.
