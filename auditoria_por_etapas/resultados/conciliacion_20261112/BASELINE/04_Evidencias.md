# 4. Registro de evidencias y estado verificable

> **Actualización 05/11/2026:** Registro histórico de planificación. Las casillas y los estados de esta versión no prueban el estado actual del sistema. Jira ya no se usa ni se evalúa en este proyecto; las referencias posteriores se conservan solo como contexto histórico. Véase [Guía de alcance y diferencias](21_Alcance_Actual_y_Diferencias.md).

> **Propósito:** separar con claridad tres cosas: validación documental ya realizada, simulación de planificación y evidencia futura del software. Jira conservará el estado operativo y los enlaces reales. Una simulación nunca convierte una Story en `Hecho`.
>
> **Fecha de corte documental:** 10 de octubre de 2026. El corte de exposición es martes 13 de octubre de 2026, 20:00 (`America/Lima`).

## 4.1 Estado honesto

| Elemento | Estado verificable |
|---|---|
| Línea base documental | Completada y sometida a controles cruzados |
| Simulación de seis Developers | Pasa documentalmente con calendario nivelado; no es ejecución de software |
| Registro de inicio académico | Se debe registrar el inicio real, las seis cuentas Jira y la disponibilidad de 32 h por Developer; por instrucción docente no se requieren PO/SM en Jira |
| Sprint 1 en Jira | No se afirma iniciado |
| Stories seleccionadas | 9 / 40 SP; el Sprint puede continuar tras la exposición, no se anticipa su cierre |
| Stories Hechas | 0 |
| Tasks/Subtasks terminadas | 0 |
| Pruebas reales ejecutadas | 0 registradas |
| Velocidad real | No disponible; ningún Sprint cerrado |
| Burndown real | No disponible hasta iniciar Jira |
| Enlace de demostración | Pendiente |
| Backup ejecutado | Pendiente |
| Restore ejecutado | Pendiente |
| Piloto controlado | No autorizado |

## 4.2 Evidencia de validación documental

Estos controles sí corresponden a trabajo documental realizado. No demuestran que el sistema exista.

| ID | Control | Resultado documental | Fuente |
|---|---|---|---|
| `EV-PLAN-01` | Backlog activo | 74 HU / 231 SP; IDs sin duplicar | `08`, `09` |
| `EV-PLAN-02` | Corte Sprint 1 | 9 HU / 40 SP | `09`, `14` |
| `EV-PLAN-03` | Backlog posterior | 65 HU / 191 SP, sin Sprint ni versión | `09` |
| `EV-PLAN-04` | Fuera de horizonte | 8 ideas / 0 SP | `09` |
| `EV-PLAN-05` | Reglas | RN-01 a RN-30 presentes en resumen y detalle, sin duplicados | `07` |
| `EV-PLAN-06` | Criterios de Sprint | 41 CA = 4+3+5+5+4+5+6+4+5 | `08`, `03` |
| `EV-PLAN-07` | WBS | 16 Tasks + 51 Subtasks = 67; 216 h | `16` |
| `EV-PLAN-08` | Capacidad | 36 h de ítems por Developer en todo el Sprint; corte verificable de 32 h por Developer / 192 h-persona hasta mar. 20:00 | `01`, `14`, `16`, `20` |
| `EV-PLAN-09` | Separación de revisión | Responsable distinto de revisor en 67/67 incidencias | `16` |
| `EV-PLAN-10` | Dependencias duras | 67 nodos, referencias existentes, 0 ciclos, ruta de precedencia 34 h | `16` |
| `EV-PLAN-11` | Trazabilidad | Los 67 IDs de `16` aparecen en `03`; 41/41 CA tienen implementación, prueba y evidencia | `03`, `16` |
| `EV-PLAN-12` | Evidencia honesta | Ningún resultado de código, prueba, backup, restore o aceptación fue marcado como ejecutado | Este documento |
| `EV-PLAN-13` | Simulación adversa | 11 escenarios con respuesta determinista y traza; todos permanecen no ejecutados | `17` |
| `EV-PLAN-14` | Nivelación de recursos | 45.5 h de ventana técnica para el Sprint completo; el corte académico es h32 por Developer y exige trabajo restante real visible | `14`, `16`, `17`, `20` |

Los comandos o cálculos de auditoría podrán adjuntarse al ticket de Planning. El resultado canónico se preserva en los documentos, no en una captura aislada.

## 4.3 Registro por Story

Completar una fila únicamente con evidencia real y enlazada. Todos los estados iniciales son `Pendiente`.

| Story / Jira | CA | Prueba automática | Prueba manual | Revisión independiente | Validación de exposición | Estado |
|---|---:|---|---|---|---|---|
| `HU-AUTH-01` / por asignar | 4 | Pendiente | Pendiente | Pendiente | Profesor, solo durante exposición | Por hacer |
| `HU-AUTH-03` / por asignar | 3 | Pendiente | Pendiente | Pendiente | Profesor, solo durante exposición | Por hacer |
| `HU-PROD-02` / por asignar | 5 | Pendiente | Pendiente | Pendiente | Profesor, solo durante exposición | Por hacer |
| `HU-INV-01a` / por asignar | 5 | Pendiente | Pendiente | Pendiente | Profesor, solo durante exposición | Por hacer |
| `HU-CAJA-01` / por asignar | 4 | Pendiente | Pendiente | Pendiente | Profesor, solo durante exposición | Por hacer |
| `HU-VEN-01b` / por asignar | 5 | Pendiente | Pendiente | Pendiente | Profesor, solo durante exposición | Por hacer |
| `HU-VEN-01c` / por asignar | 6 | Pendiente | Pendiente | Pendiente | Profesor, solo durante exposición | Por hacer |
| `HU-VEN-02a` / por asignar | 4 | Pendiente | Pendiente | Pendiente | Profesor, solo durante exposición | Por hacer |
| `HU-CAJA-02` / por asignar | 5 | Pendiente | Pendiente | Pendiente | Profesor, solo durante exposición | Por hacer |

Cada celda debe enlazar el paquete `EV-<HU>-CA<n>` definido en `03`; escribir solamente “funciona” o adjuntar una captura final no es evidencia suficiente.

## 4.4 Evidencias técnicas transversales

| Paquete | Resultado que deberá demostrarse | Estado inicial | Jira/enlace real |
|---|---|---|---|
| `EV-ARQ-01` | ADR, stack, contratos y límites ratificados | Pendiente | Por registrar |
| `EV-PLAT-01` | Clon/build reproducible y revisión por Pull Request | Pendiente | Por registrar |
| `EV-CI-01` | Pipeline de análisis, migraciones, pruebas y build | Pendiente | Por registrar |
| `EV-DB-01` | Modelo y diccionario coinciden con migraciones | Pendiente | Por registrar |
| `EV-DB-02` | PostgreSQL vacío migra sin paso manual | Pendiente | Por registrar |
| `EV-DB-03` | Constraints e índices rechazan estados inválidos | Pendiente | Por registrar |
| `EV-DB-04` | Seeds ejecutados dos veces sin duplicados | Pendiente | Por registrar |
| `EV-DB-05` | Reset reproducible permitido solo en local/CI | Pendiente | Por registrar |
| `EV-SEC-01` | Secretos externos, configuraciones separadas y usuario de BD con mínimo privilegio | Pendiente | Por registrar |
| `EV-SEC-02` | Hash, sesión/cookies, CSRF, validación, logs y matriz de autorización server-side | Pendiente | Por registrar |
| `EV-ENV-01` | Deploy, rollback, health, smoke y matriz Chrome/Windows/1366×768 | Pendiente | Por registrar |
| `EV-QA-DB-01` | Migración/seeds/reset desde BD limpia | Pendiente | Por registrar |
| `EV-QA-DB-02` | Rollback de carga/cobro/cierre | Pendiente | Por registrar |
| `EV-QA-DB-03` | Concurrencia de carga, caja, stock, cobro y cierre | Pendiente | Por registrar |
| `EV-OPS-BKP-01` | Backup, manifiesto, retención y checksum | Pendiente | Por registrar |
| `EV-OPS-RST-01` | Restore limpio, conteos, duración y smoke | Pendiente | Por registrar |

Backup y restauración son paquetes distintos. Un archivo de backup no demuestra recuperabilidad.

## 4.5 Formato obligatorio de una evidencia real

| Campo | Contenido |
|---|---|
| Identidad | HU/CA, prueba, Task/Subtask, Bug si existe |
| Versión | commit, build, imagen y última migración |
| Contexto | fecha UTC, ambiente, navegador/viewport y fixture |
| Acción | pasos o comando reproducible, sin secretos |
| Esperado | resultado previsto por CA/RN/NFR |
| Obtenido | salida, estado persistido y diferencias |
| Artefacto | log, reporte JUnit/HTML, consulta, captura o video pertinente |
| Revisión | Developer distinto, fecha, decisión y observaciones |
| Estado | `Aprobado`, `Fallido` o `Bloqueado`; nunca inferido por ausencia de error visible |
| Enlace | ticket Jira/PR/pipeline/almacenamiento autorizado |

Para atomicidad, idempotencia y concurrencia se exige estado antes/después y conexiones separadas cuando corresponda. Para seguridad se redactan contraseñas, cookies, CSRF, claves completas y cadenas de conexión.

## 4.6 Registro de pruebas críticas

| Grupo | IDs | Estado | Evidencia requerida |
|---|---|---|---|
| BD reproducible | `AT-DB-01..04` | Pendiente | Logs y conteos desde BD vacía |
| Concurrencia | `CT-CONC-01..05` | Pendiente | Barrera, dos conexiones y estado final único |
| Rollback | `CT-ROLLBACK-01..02` | Pendiente | Fallo inducido y comparación antes/después |
| Seguridad | `ST-BASE-01..02` | Pendiente | Configuración y matriz por rol/sin sesión |
| Tiempo Lima/UTC | `AT-TIME-01..02` | Pendiente | Reloj controlado alrededor de medianoche |
| Compatibilidad objetivo | `MT-COMPAT-01` | Pendiente | Chrome estable, Windows 10/11, 1366×768 y teclado registrados |
| Rendimiento | `PT-SEARCH-01`, `PT-CHECKOUT-01` | Pendiente | Equipo, volumen, muestra y percentil |
| Recorrido | `E2E-R1-01` | Pendiente | Nueve Stories y tres cuentas separadas |

## 4.7 Seguimiento diario e impedimentos

| Fecha / corte | Avance real hacia Sprint Goal | Impedimento | Dueño de seguimiento | Próxima revisión | Jira |
|---|---|---|---|---|---|
| Sáb. 10-oct | Registrar inicio real, horas y estado inicial | Por registrar | Equipo de Developers | Dom. 11-oct | Por registrar |
| Dom. 11-oct | Por registrar | Por registrar | Developer que detecta el impedimento | Lun. 12-oct | Por registrar |
| Lun. 12-oct | Por registrar | Por registrar | Developer que detecta el impedimento | Mar. 13-oct | Por registrar |
| Mar. 13-oct, 20:00 | Corte de exposición: horas, restante, estados y evidencias reales | Por registrar | Equipo de Developers | Día hábil siguiente | Por registrar |
| Después del corte | Reestimar hasta el máximo de dos semanas | Por registrar | Equipo de Developers | Por registrar | Por registrar |

## 4.8 Puerta de piloto controlado

- [ ] Las 9 Stories cumplen sus 41 CA y la DoD.
- [ ] `E2E-R1-01` satisfactorio con datos ficticios.
- [ ] Cero Bugs bloqueantes o graves abiertos.
- [ ] Pipeline, deploy y smoke satisfactorios.
- [ ] Autorización server-side y revisión de seguridad satisfactorias.
- [ ] Carreras y rollback críticos satisfactorios.
- [ ] Constancia con advertencia y sin costo visible.
- [ ] Backup real con checksum.
- [ ] Restore real en BD limpia dentro del RTO.
- [ ] Limitaciones del piloto documentadas.
- [ ] Autorización académica/documentada antes de cualquier piloto, si el curso lo permite.

Si falta una condición, solo se permite demostración controlada; no se autoriza piloto.

## 4.9 Checklist de exposición

- [ ] Product Goal, plazo, costo y límites del PMV.
- [ ] 74/231 y corte 9/40; 65/191 sin asignación futura.
- [ ] Stack, modelo de datos y decisiones explicadas.
- [ ] 67 incidencias / 216 h; corte de 192 h-persona y trabajo restante real visible.
- [ ] Matriz 41/41 y dependencias duras sin ciclos.
- [ ] Inicio real, cuentas de Developers y corte de exposición registrados; no hay PO/SM ficticios.
- [ ] Tablero y Burndown reales, solo si Jira fue iniciado.
- [ ] Stories `Hecho` únicamente con evidencia real.
- [ ] Enlace de demo solo si existe y fue comprobado.
- [ ] Velocidad solo después de cerrar Sprint 1.
