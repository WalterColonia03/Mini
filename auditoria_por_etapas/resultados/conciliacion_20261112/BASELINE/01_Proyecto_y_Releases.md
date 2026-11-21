# 1. Plan maestro del proyecto

> **Actualización 05/11/2026:** Jira ya no se utiliza ni se evalúa. El resto de este documento conserva el plan histórico de octubre de 2026; sus instrucciones y dependencias relacionadas con Jira no están vigentes. Las fechas, estimaciones y objetivos originales no acreditan implementación ni aceptación. Para revisar las funcionalidades actuales y las diferencias conocidas, consulte [Guía de alcance y diferencias](21_Alcance_Actual_y_Diferencias.md).

## 1.1 Lectura y trazabilidad actual

- `07_Reglas_de_Negocio.md`, `08_Historias_de_Usuario.md` y `09_Product_Backlog.md` contienen requisitos y trabajo futuro; su inclusión no demuestra que estén implementados.
- `02_Diseno_Tecnico_R1_PMV.md`, `03_Matriz_de_Trazabilidad_y_Pruebas.md`, `14_Sprint_Planning.md`, `16_Task_Breakdown.md` y `20_Corte_De_Exposicion_Martes.md` recogen el diseño y la planificación históricos de Sprint 1.
- `r1-pmv/` contiene el sistema y las pruebas disponibles. Los resultados deben atribuirse a la ejecución concreta que los generó; las cifras históricas no garantizan el estado actual.
- `21_Alcance_Actual_y_Diferencias.md` reúne diferencias identificadas entre documentos y sistema y explica los límites de la demostración. Las discrepancias pendientes deben corregirse y verificarse antes de presentar los criterios correspondientes como cumplidos.
- `archivo_historico_jira/` y las referencias a Jira son material histórico, no requisitos de evaluación ni fuente de estado vigente.

## 1.2 Objetivo del proyecto

### Product Goal

> El propósito es que una sola bodega pueda registrar productos enlatados, anotar existencias por lote, abrir su única caja, cobrar ventas en efectivo, entregar una constancia interna y cuadrar el dinero al final del turno.

### Objetivo temporal y económico

- **Inicio operativo del Sprint 1:** sábado 10 de octubre de 2026, en la hora real registrada al iniciar Jira.
- **Fin del horizonte académico:** jueves 19 de noviembre de 2026.
- **Duración:** 6 semanas, organizadas en 3 Sprints de 2 semanas.
- **Equipo:** 6 Developers.
- **Dedicación comprometida para el primer corte:** 8 horas por día y por Developer desde sábado hasta martes 13 a las 20:00 (32 h por Developer; 192 h-persona).
- **Tarifa académica de planificación:** S/ 25.00 por hora.
- **Costo académico del corte de exposición:** `6 × 32 h × S/ 25.00 = S/ 4,800.00` como referencia; no es remuneración ni pago dominical.
- **Costo total del horizonte:** se recalcula a partir de las horas reales de cada Sprint; no se infiere desde el corte de cuatro días.

El costo corresponde al trabajo del equipo, incluidos los eventos Scrum. No incluye local, equipos físicos, lector de código de barras, comprobantes tributarios ni servicios externos de facturación. Si se usan herramientas o infraestructura sin costo (niveles gratuitos de desarrollo), se registran como costo S/ 0 y como supuesto de trabajo, no como recurso ilimitado.

## 1.3 Alcance y uso piloto

### Incluido en el horizonte del minimarket

- Acceso con cuenta de trabajo y permisos para atender.
- Registro de productos y categorías.
- Control de existencias por lotes.
- Turno único de caja, atención, cobro en efectivo y cuadre de dinero.
- Funciones de control, reposición y consulta que se elijan según la velocidad real.
- Acceso para demostración y comprobación del recorrido de venta.

### No incluido en el Sprint 1

- Boleta o factura oficial con validez tributaria.
- Trámites directos ante SUNAT u operadores de facturación electrónica.
- Operación en varias sedes, venta por internet, contabilidad y planillas.
- Venta por peso, crédito, delivery o varias cajas al mismo tiempo.

El Sprint 1 generará una **constancia interna de venta**, identificada de forma visible como no válida como comprobante de pago oficial ni boleta o factura. Para realizar ventas comerciales formales, el minimarket deberá emitir los comprobantes mediante el canal oficial externo o incorporar más adelante funciones tributarias.

### Momentos de uso

| Momento de uso | Propósito | Datos permitidos |
|---|---|---|
| Preparación del trabajo | Información ficticia para elaborar las funciones | Datos ficticios |
| Prueba y exposición | Información ficticia controlada para comprobar el recorrido | Datos ficticios controlados |
| Piloto controlado | Uso limitado después de aprobar el recorrido completo | Sin comprobantes tributarios ni datos sensibles reales |

No se llamará uso comercial al piloto mientras falten las aprobaciones necesarias, una copia de seguridad comprobada, recuperación comprobada y el canal oficial de comprobantes tributarios.

## 1.4 Equipo de Developers, perfiles de planificación y decisiones

| Integrante | Rol principal | Participación esperada |
|---|---|---|
| Des.1 - Velasquez | Developer | Arquitectura modular, PostgreSQL, migraciones, inventario y concurrencia; revisión cruzada de caja |
| Des.2 - Nolasco | Developer | Servicios Django, autenticación, autorización, seguridad y pruebas de integración; revisión cruzada de ventas |
| Des.3 - Castillo | Developer | Interfaz web, HTMX, accesibilidad y flujo de punto de venta; revisión cruzada de producto |
| Des.4 - Alcalde | Developer | Caja, integración, despliegue, configuración y operación; revisión cruzada de inventario |
| Des.5 - Walter Luis Colonia Infantas | Developer | Datos iniciales, autenticación, automatización de pruebas y control de calidad; tareas finales de cobro/cierre y revisión cruzada de constancias |
| Des.6 - Angeles | Developer | Interfaz, constancias, observabilidad, pruebas manuales y documentación; revisión cruzada de acceso |

Los seis perfiles corresponden a los Developers reales declarados por el equipo. El profesor indicó que no se requiere Product Owner ni Scrum Master en Jira. La validación académica final ocurre ante el profesor durante la exposición, no como una aceptación anticipada en el tablero.

### Decisiones organizativas confirmadas

- **[DECISIÓN 01-01] Corte académico del Sprint.**  
  *Regla:* Sprint inicia el sábado 10 de octubre de 2026; los seis Developers trabajan sábado, domingo, lunes y martes, ocho horas por día. El corte de exposición es el martes 13 a las 20:00 (`America/Lima`).  
  *Implicación:* hay 192 h-persona hasta el corte; el Sprint de 216 h técnicas no se declara terminado solo por llegar a la exposición.
- **[DECISIÓN 01-02] Roles académicos en Jira.**  
  *Regla:* no crear PO ni SM ficticios. Jira registra Developers, incidencias, tiempo, evidencia y estado real.  
  *Implicación:* el profesor constata el avance al exponer; no existe aceptación final previa que marcar en Jira.
- **[DECISIÓN 01-03] Identidad y cierre técnico.**  
  *Regla:* D5 es Walter Luis Colonia Infantas y queda responsable de `S1-VEN01C-MAN` y `S1-CAJA02-REV` cuando sus dependencias estén cumplidas. Los nombres visibles y `accountId` de las seis cuentas se comprueban en Jira antes de asignar; no se deducen correos.  
  *Implicación:* las últimas validaciones de cobro/cierre tienen dueño explícito sin sustituir la revisión independiente ni alterar dependencias.

### Decisiones funcionales y técnicas adoptadas para la línea base R1-PMV

| ID | Decisión cerrada | Alcance |
|---|---|---|
| `DEC-01` | Aplicación web interna, modular y monolítica | Un solo minimarket y una sola caja; no es aplicación móvil ni multitienda |
| `DEC-02` | Tres cuentas de demostración separadas y un solo rol por cuenta | Administrador, encargado del almacén y vendedor; no existe cuenta multirrol en R1 |
| `DEC-03` | El logout voluntario está permitido con turno abierto | Si existe una venta en preparación, el vendedor debe descartarla explícitamente antes de salir; el turno queda abierto y vinculado al mismo vendedor |
| `DEC-04` | R1 admite únicamente productos enlatados con vencimiento obligatorio | El modelo conserva `controla_vencimiento` para ampliaciones futuras, pero R1 siempre lo registra como verdadero |
| `DEC-05` | Número de lote alfanumérico, normalizado en mayúsculas y único por producto | El desempate técnico usa el identificador interno de ingreso, no el orden lexicográfico del lote comercial |
| `DEC-06` | Correlativo de venta global `V-00000001` | Es único, inmutable, creciente y se asigna dentro de la transacción de cobro |
| `DEC-07` | Dinero con decimal exacto | Precios y totales a 2 decimales; costos internos a 4; redondeo comercial `ROUND_HALF_UP` únicamente en los puntos definidos en RN-14 y RN-27 |
| `DEC-08` | Fecha de negocio `America/Lima` y almacenamiento de instantes en UTC | Las fechas de vencimiento son fechas calendario; los eventos guardan timestamp UTC inmutable |
| `DEC-09` | Chrome estable en Windows 10/11, escritorio de 1366×768 como mínimo | Uso por teclado y lector opcional que se comporta como teclado; móvil fuera de R1 |
| `DEC-10` | Volumen de diseño de R1 | Hasta 2,000 productos, 20,000 lotes, 300 ventas/día, 20 líneas/venta y 3 sesiones autenticadas; una sola confirma cobros |
| `DEC-11` | Backup lógico, checksum y restauración independiente | Retención de 7 copias diarias y 4 semanales en almacenamiento controlado; restauración probada en BD limpia antes del piloto |

Las decisiones de arquitectura, versiones, ambientes, autorización y datos se detallan en `02_Diseno_Tecnico_R1_PMV.md`. Cambiarlas exige un ADR y análisis de impacto sobre 03, 14 y 16.

Ningún integrante es dueño exclusivo de una parte del trabajo. Quien coordina una historia recibe apoyo del equipo completo para lograr el incremento.

## 1.5 Calendario de Sprints y releases

| Sprint / Versión | Fechas | Resultado esperado | Estado de alcance |
|---|---|---|---|
| Sprint 1 / `R1-PMV` | Sáb. 10-oct a vie. 23-oct como máximo; exposición mar. 13-oct 20:00 | Venta en efectivo desde el ingreso del trabajador hasta el cuadre de caja | 9 historias, 40 SP; corte de 192 h-persona para mostrar avance real, no cierre obligatorio |
| Sprint 2 | Sáb. 24-oct a vie. 06-nov | Contenido pendiente de definir después del cierre de Sprint 1 con la velocidad real | Pendiente de acordar |
| Sprint 3 | Sáb. 07-nov a vie. 20-nov | Contenido pendiente de definir después de revisar los resultados anteriores | Pendiente de acordar |
| Presentación final | Vie. 20-nov | Muestra del producto realmente alcanzado y de sus métricas reales | Sesión de cierre |

Solo el Sprint 1 tiene alcance seleccionado. Los Sprints 2 y 3 no tienen historias, puntos, versión ni alcance comprometido; se definirán a partir de la velocidad real y los aprendizajes obtenidos.

## 1.6 Por qué `R1-PMV` es un producto mínimo viable

El primer release `R1-PMV` permite trabajar el recorrido mínimo: ingresar, registrar producto, cargar lotes, abrir caja, preparar venta, cobrar efectivo, descontar primero lo que vence antes, entregar constancia interna y cuadrar caja.

El corte contiene exactamente 9 historias y 40 Story Points:

1. `HU-AUTH-01` — Ingresar con mi cuenta de trabajo — 5 SP.
2. `HU-AUTH-03` — Salir de mi cuenta al terminar — 2 SP.
3. `HU-PROD-02` — Registrar un producto enlatado — 5 SP.
4. `HU-INV-01a` — Registrar las existencias iniciales por lotes — 5 SP.
5. `HU-CAJA-01` — Abrir el turno de caja — 5 SP.
6. `HU-VEN-01b` — Preparar una venta y revisar existencias — 5 SP.
7. `HU-VEN-01c` — Cobrar en efectivo y descontar existencias — 5 SP.
8. `HU-VEN-02a` — Generar una constancia interna de venta — 3 SP.
9. `HU-CAJA-02` — Cerrar y cuadrar la caja — 5 SP.

La categoría «Productos enlatados», los tres roles y la caja única se preparan mediante semillas idempotentes. Las tres cuentas ficticias de demostración se aprovisionan con un comando repetible y contraseñas temporales suministradas como secretos del ambiente; ninguna credencial se guarda en el repositorio.

Los 40 puntos son una estimación relativa, no horas ni velocidad. Los seis Developers los contrastan al iniciar el Sprint el 10 de octubre y registran cualquier ajuste en Jira. No existe velocidad real antes del cierre del Sprint 1.

## 1.7 Capacidad y reglas de estimación de tareas

Para Sprint 1:

- **Capacidad comprobable hasta la exposición:** `6 Developers × 4 días × 8 h = 192 h-persona`.
- **Línea base de trabajo técnico completo:** 67 Tasks/Subtasks y 216 horas, repartidas en 36 h por Developer; excede en 24 h la capacidad máxima del corte aun antes de sumar eventos o Bugs.
- **Lectura correcta del calendario:** la ruta de precedencia de 34 h y la nivelación de 45.5 h después del Planning corresponden al Sprint completo. No autorizan a marcar las 9 HU terminadas a las 32 h de corte.
- **Trabajo posterior:** se programa con tiempo restante real en Jira y sin sobrepasar el máximo de dos semanas. La reserva no autoriza añadir Stories.
- **Estructura del trabajo técnico:** el trabajo de Sprint 1 se desglosa en `Tasks` técnicas compartidas (transversales de arquitectura, base de datos, migraciones, semillas, seguridad, CI/CD, backup y restauración) y `Subtasks` específicas bajo cada una de las 9 Stories (interfaz, servicio/persistencia, prueba automática, prueba manual y comprobación independiente).
- **Regla de horas:** las horas de `16_Task_Breakdown.md` provienen de la simulación conjunta de los seis perfiles, se usan como pronóstico inicial y deberán ratificarse o sustituirse en el Planning real.
- **Reserva de capacidad:** 4 horas técnicas por Developer, 24 horas de equipo; es capacidad distribuida en huecos de la nivelación, no una promesa de que todo el equipo quedará libre al final. No autoriza agregar Stories y protege correcciones, integración e incertidumbre.

Las horas sirven para organizar tareas/subtareas y los Story Points para estimar el tamaño relativo de historias. No existe una fórmula de conversión matemática directa entre ambos.

## 1.8 Configuración de Jira y gobierno técnico

### Estructura y tipos de incidencia

- **Plantilla:** Scrum.
- **Clave sugerida:** `SVM`.
- **Jerarquía:** `Epic`, `Story`, `Task`, `Bug` y `Subtask`.
  - `Epic`: Grandes iniciativas temáticas del minimarket (5 Epics identificadas).
  - `Story`: Requisitos funcionales con valor de negocio. **Solo las Stories llevan Story Points.** En Sprint 1 se incluyen exactamente 9 Stories (40 SP). Las 65 Stories restantes permanecen en el Backlog general sin Sprint ni versión (191 SP).
  - `Task`: Trabajo técnico compartido o transversal de infraestructura, plataforma, modelo relacional, migraciones versionadas, semillas de datos, pipeline de integración, pruebas transversales y procedimientos de backup/restauración. **No son nuevas HUs, no tienen valor de usuario directo y no llevan Story Points.**
  - `Subtask`: Trabajo técnico específico perteneciente a una Story concreta. Debe cubrir, según corresponda y sin crear trabajo ficticio:
    1. *Interfaz de usuario (UI):* Pantallas, formularios, validaciones de cliente, estados y accesibilidad básica.
    2. *Servicio y persistencia:* Lógica de negocio, consultas SQL/ORM transaccionales, restricciones e integridad en servidor.
    3. *Prueba automática:* Pruebas unitarias o de integración automatizadas para cada criterio.
    4. *Prueba manual funcional:* Casos de prueba documentados paso a paso con datos de entrada y salida esperada.
    5. *Comprobación independiente entre pares:* Verificación por un Developer distinto al autor.
  - `Bug`: Incidencias o defectos detectados durante el desarrollo o validación. Un Bug detectado antes de aceptar la historia se vincula a ella e impide marcarla como Hecha.
- **Componentes:** Ingreso y personal, Productos y proveedores, Mercadería y reposición, Ventas y caja, Control del negocio.
- **Versiones:** Únicamente `R1-PMV` como versión creada para el primer release. Las futuras versiones se crearán cuando el equipo las acuerde.
- **Story Points:** Únicamente en Stories.
- **Horas previstas y restantes:** En Tasks y Subtasks.
- **Dependencias:** `blocks / is blocked by` se reserva para precedencias duras. Las dependencias de integración o aceptación se registran como `relates to` más el campo `Integración requerida`, permitiendo trabajo paralelo con contratos y datos simulados.

### Plataforma de referencia aprobada para la simulación

- Python 3.13, Django 5.2 LTS y plantillas server-side con HTMX 2.0.
- PostgreSQL 17 y migraciones nativas de Django; Docker Compose para reproducibilidad local y de demostración.
- Runner estándar de Django (`python manage.py test`) para pruebas y GitHub Actions para CI. El recorrido crítico puede verificarse manualmente en navegador; no se exige Playwright en Sprint 1.
- Despliegue de demostración en un host Linux controlado, con secretos externos al repositorio, HTTPS cuando exista acceso por red y PostgreSQL no expuesto públicamente.
- Las versiones de parche se fijan en archivos de dependencias y se actualizan solo mediante Pull Request con pipeline exitoso.

### Flujo de estados

`Por hacer → En desarrollo → En revisión → En validación → Hecho`

- Si una tarea tiene un problema o dificultad, se marca con bandera (*flag*) y comentario explicativo en Jira.
- Solo la columna derecha del tablero se mapea a Hecho.
- Terminar subtareas no mueve automáticamente la Story a Hecho: aún debe superar la revisión entre compañeros, la validación funcional y la Definition of Done.

### Campos mínimos de una Story

- Resumen con identificador canónico del minimarket (ej. `HU-AUTH-01`).
- Historia: «Como [rol del minimarket] quiero [acción/necesidad] para [beneficio/valor]».
- Criterios de aceptación observables, verificables e inequívocos.
- Epic asociada, prioridad, Story Points y componente. La versión `R1-PMV` y Sprint 1 se asignan únicamente a las nueve Stories seleccionadas; las otras 65 quedan sin ambos campos.
- Dependencias enlazadas (`blocks / is blocked by`).
- Sprint asignado solo cuando cumpla la Definition of Ready y los Developers la seleccionen formalmente.

### Campos mínimos de una Task o Subtask

- Clave e identificador canónico de planificación (ej. `S1-DB-01` o `S1-AUTH01-01`).
- Tipo Jira (`Task` o `Subtask`), Story padre o Stories apoyadas y capa (`UI`, `Servicio`, `BD`, `QA`, `Seguridad` o `Plataforma`).
- Resultado observable y técnico concreto (evitando títulos vagos como «programar» o «probar»).
- Criterio de aceptación (CA), Regla de negocio (RN) o Requisito no funcional (NFR) al que aporta.
- Responsable inicial asignado y revisor entre pares distinto.
- Predecesora dura o dependencia de integración, diferenciadas explícitamente.
- Horas estimadas y horas restantes; al cargar Jira ambas comienzan iguales y solo la estimación ratificada se considera compromiso real.
- Evidencia esperada: script, migración versionada, captura, log de ejecución de pruebas, checksum o demostración.

## 1.9 Definition of Ready (DoR)

Una historia de usuario puede ser seleccionada para el Sprint 1 únicamente cuando:

- Expresa con claridad actor, necesidad y valor comercial para el minimarket.
- Tiene criterios de aceptación observables, objetivos y testeables.
- Sus reglas de negocio (`07_Reglas_de_Negocio.md`) y restricciones técnicas asociadas (`02_Diseno_Tecnico_R1_PMV.md`) están identificadas.
- Sus dependencias funcionales y técnicas están enlazadas y son viables dentro del Sprint.
- Cabe holgadamente en el Sprint y no supera 5 Story Points sin ser dividida.
- Cuenta con desglose técnico suficiente en UI, servicio/persistencia, pruebas y comprobación independiente según corresponda.
- Cuenta con estimación y compromiso de los seis Developers; la cuenta Jira de cada responsable se comprueba antes de registrar tiempo.
- Tiene prioridad, Epic, componente y versión `R1-PMV` asignada.
- No mantiene decisiones funcionales o técnicas bloqueantes; por indicación académica, no se exige PO ni SM como requisito de Jira.

## 1.10 Definition of Done (DoD) y puerta de piloto

### Definition of Done para una Story

Una Story pasa a estado **Hecho** (*Done*) únicamente cuando se verifican todos los siguientes requisitos:

1. **Criterios cumplidos:** Cumple al 100 % los criterios de aceptación funcionales definidos en `08_Historias_de_Usuario.md`.
2. **Tareas completadas:** Todas las subtareas que correspondan a sus criterios —UI, servicio/persistencia, pruebas y verificación independiente— están terminadas en Jira con horas restantes en cero.
3. **Integridad y persistencia:** Los datos se persisten en base de datos relacional respetando tipos exactos (decimales para dinero, nunca flotantes), claves foráneas, restricciones de no nulidad, no existencias negativas y unicidad requerida.
4. **Transacciones y atomicidad:** Las operaciones que cambian varios datos o protegen invariantes —carga inicial, apertura/cierre y cobro— se ejecutan dentro de transacciones ACID con rollback completo ante cualquier fallo.
5. **Calidad de software y seguridad:** El código sigue estándares limpios, no incluye contraseñas ni secretos quemados en el código fuente, y las contraseñas se almacenan con hashing seguro.
6. **Pruebas automatizadas:** Pruebas unitarias e integración pertinentes ejecutadas con éxito en el pipeline reproducible; el recorrido crítico E2E es obligatorio para la puerta de piloto.
7. **Pruebas manuales registradas:** Casos de prueba ejecutados y documentados en Jira conforme a `03_Matriz_de_Trazabilidad_y_Pruebas.md`.
8. **Revisión por pares (Peer Review):** Código revisado y aprobado por al menos un Developer diferente al implementador.
9. **Comprobación independiente de criterios:** Verificación funcional independiente realizada por el Developer asignado para control cruzado.
10. **Sin defectos críticos:** Cero Bugs bloqueantes o graves abiertos asociados a la historia.
11. **Validación académica de exposición:** el profesor revisa el incremento realmente demostrado. Esta revisión no permite marcar una Story `Hecho` si faltan los diez controles anteriores.

### Puerta de control para el Piloto Controlado

Ningún despliegue se considerará apto para uso piloto controlado mientras no supere la puerta de control obligatoria:

- Recorrido integral de venta en mostrador (ingreso → producto → lote → apertura de caja → venta → cobro en efectivo → constancia interna → cierre de caja) comprobado de punta a punta.
- Procedimiento de copia de seguridad (*backup*) ejecutado y archivo verificado con checksum.
- Procedimiento de restauración (*restore*) ejecutado exitosamente en un ambiente limpio, comprobando la integridad total de los datos.
- Confirmación explícita de que la constancia interna muestra la leyenda obligatoria de control interno sin validez tributaria.
- Aprobación académica/documentada antes de encender un piloto, si el curso lo autoriza.

## 1.11 Métricas y evidencia honesta

Durante el Sprint se mostrarán en Jira:

- Tablero real sin alterar estados para la exposición.
- Burndown del Sprint para seguir el avance diario.
- Sprint Report y registro de cambios en Jira.
- Story Points terminados hasta el momento, sin llamarlos velocidad.
- Horas restantes de tareas para coordinación interna.
- Avisos de dificultades y decisiones de adaptación del equipo.

Antes de cerrar Sprint 1 no hay velocidad real; la gráfica de velocidad utiliza Sprints completados. Una historia incompleta aporta 0 SP a la velocidad, aunque varias tareas estén terminadas. La exposición del martes 13 a las 20:00 mostrará el estado real que exista en Jira.

## 1.12 Matriz de la rúbrica del profesor

| Pregunta evaluada | Evidencia que debe abrirse |
|---|---|
| Objetivo, tiempo y costo | Secciones 1.2 y 1.5 de `01_Proyecto_y_Releases.md` |
| Backlog completo y ordenado | Product Backlog en Jira y `09_Product_Backlog.md` |
| Primer release y fecha | Versión `R1-PMV`, con corte de exposición martes 13 de octubre 20:00 y fin máximo viernes 23 de octubre de 2026 |
| Por qué es PMV y por qué 40 SP | Sección 1.6 de `01_Proyecto_y_Releases.md` y registro de estimación en Sprint Planning |
| Planning con todos e inicio | `14_Sprint_Planning.md` y registro en Jira |
| Tareas completas y coherentes | `16_Task_Breakdown.md` y tareas organizadas en Jira |
| Arquitectura, persistencia y seguridad | `02_Diseno_Tecnico_R1_PMV.md` |
| Matriz de cobertura y pruebas | `03_Matriz_de_Trazabilidad_y_Pruebas.md` |
| Cronograma de trabajo | Red de dependencias y enlaces `blocks` en Jira |
| Simulación de los seis Developers y fallos adversos | `17_Simulacion_6_Developers.md` |
| Carga y auditoría previa a iniciar Jira | `18_Guia_Carga_Jira.md` |
| Entregables terminados | Registros de prueba, capturas y enlace de acceso de prueba o demostración en `04_Evidencias.md` |
| Estado actual del tablero | Tablero real en Jira, sin alterar estados para la exposición |
| Velocidad real | Explicar que surge al cerrar Sprint 1; durante el Sprint mostrar Burndown |
| Uso del producto | Demostración en funcionamiento; declarar momentos de uso con precisión |
| Cumple criterios | Criterios de aceptación más DoD y evidencias en Jira |

## 1.13 Riesgos principales

| Riesgo | Respuesta |
|---|---|
| Sobrecompromiso sin velocidad histórica | Recorrido mínimo de 9 historias y 40 Story Points; mostrar el corte real de 192 h-persona y reestimar el trabajo restante sin alterar el Sprint Goal |
| Tareas genéricas o sin resultado claro | Definir tareas técnicas con resultado observable, capa arquitectónica y evidencia esperada obligatoria |
| Demora en la revisión entre compañeros | Revisión rotativa entre compañeros; todos elaboran y todos comprueban |
| Dependencias no previstas | Enlaces `blocks / is blocked by` en Jira y frentes coordinados |
| Pérdida de integridad o transacciones incompletas | Modelo relacional estricto, migraciones versionadas y transacciones ACID en `02_Diseno_Tecnico_R1_PMV.md` |
| Duplicación de ventas o correlativos bajo concurrencia | Mecanismo de idempotencia y generación atómica de correlativos |
| Documento interno presentado como comprobante legal | Mensaje obligatorio en la constancia y alcance SUNAT explícitamente excluido |
| Datos falsos para la exposición | Mostrar únicamente estados, fechas y métricas generados por el trabajo real en Jira |
| Pérdida o corrupción de datos en piloto | Procedimientos independientes de backup y restauración comprobados antes de autorizar el piloto |

## 1.14 Referencias operativas

- Scrum Guide vigente: <https://scrumguides.org/scrum-guide.html>
- Jira, uso del Scrum backlog: <https://support.atlassian.com/jira-software-cloud/docs/use-your-scrum-backlog/>
- Jira, Velocity Chart: <https://support.atlassian.com/jira-software-cloud/docs/view-and-understand-the-velocity-chart/>
- Jira, Burndown: <https://support.atlassian.com/jira-software-cloud/docs/what-is-the-sprint-burndown-report/>
- SUNAT, tipos de comprobantes electrónicos: <https://cpe.sunat.gob.pe/informacion_general/tipos_comprobantes_pago>

## Ampliación del catálogo actual · DOC03-01 · 09/11/2026

Decisión expresa del usuario: **productos de cualquier categoría, por unidad y con vencimiento obligatorio**. Amplía el catálogo actual respecto de la restricción de enlatados de DEC-04. Las referencias anteriores a R1-PMV, sus nueve HU, puntos, fechas y categoría preparada se conservan como línea base histórica; no describen una restricción comercial vigente del catálogo ampliado. No se admite peso ni ausencia de vencimiento. Esta decisión no selecciona las HU futuras de editar/eliminar categoría o escanear, ni acredita otros módulos. [Decisión, implementación y evidencia](auditoria_por_etapas/resultados/anexos/ETAPA-03-F-alcance.md).
