# Plan histórico de intervención técnica

> **ESTADO: EJECUTADO Y SUSTITUIDO COMO GUÍA OPERATIVA (9-oct-2026).** Este archivo conserva el diagnóstico y las instrucciones que originalmente se iban a entregar a Gemini. El trabajo documental ya fue aplicado en los archivos canónicos de la raíz; no debe usarse como fuente para cargar Jira ni para determinar el estado actual. Cualquier frase posterior en futuro o que indique «no modifiqué todavía» describe el momento en que se redactó este plan.

Sí: la ausencia de trabajo explícito de base de datos es un defecto importante. No es solo “una subtarea más”: afecta autenticación, productos, lotes, caja, ventas, correlativos, idempotencia, constancias, cierres y recuperación.

Sin ese trabajo, un equipo podría construir pantallas aparentemente funcionales que:

- pierdan todo al reiniciar;
- permitan dos cajas abiertas simultáneamente;
- dupliquen ventas;
- generen existencias negativas;
- cambien una constancia histórica cuando se edita el producto;
- no puedan restaurarse después de un fallo.

La BD no debe convertirse en una décima HU. Debe representarse mediante:

- `Task` técnicas transversales del Sprint, sin Story Points;
- `Subtask` de persistencia bajo las nueve HU;
- horas estimadas por los Developers;
- pruebas y evidencias concretas.

## Plan maestro de mejora

### Fase 0 — Resolver decisiones humanas

Gemini no debe inventar estas decisiones. Primero debe crear un registro con estado `[DECISIÓN PENDIENTE]`.

| Decisión | Responsable |
|---|---|
| Confirmar que será una aplicación web interna | Product Owner + Developers |
| Lenguajes, frameworks y versiones | Developers |
| Motor y versión de base de datos | Developers |
| Herramienta de migraciones | Developers |
| Alojamiento y ambientes | Developers |
| Navegador, dispositivo y viewport de caja | Product Owner + Developers |
| Roles y posibilidad de tener uno o varios roles | Product Owner |
| Comportamiento al salir con turno o venta pendiente | Product Owner |
| Si el PMV admite productos sin vencimiento | Product Owner |
| Formato y unicidad del número de lote | Product Owner + Developers |
| Formato y alcance del correlativo de venta | Product Owner |
| Precisión y redondeo de precios, costos e IGV | Product Owner + Developers |
| Volumen esperado de productos, lotes y ventas | Product Owner |
| Alcance, destino, retención y recuperación del backup | Developers + Product Owner |
| Habilidades técnicas de cada Developer | Los seis Developers |
| Product Owner y Scrum Master reales | Organización |

Condición de salida: ninguna decisión crítica pendiente y acta del Sprint Planning ratificada.

---

### Fase 1 — Corregir requisitos funcionales

Antes de diseñar la BD deben cerrarse estas inconsistencias:

1. Crear una matriz de permisos para administrador, almacenero y vendedor.
2. Definir si la demostración requiere tres cuentas o una cuenta multirrol.
3. Bloquear explícitamente una segunda carga inicial directa.
4. Eliminar o corregir la prueba de “producto sin vencimiento”.
5. Definir dónde se mostrará RN-06 durante Sprint 1, o limitarla al almacenamiento del umbral.
6. Definir formato, unicidad y comparación del lote.
7. Definir fecha de ingreso usada en FEFO.
8. Especificar fórmula del costo promedio y redondeo.
9. Especificar cálculo exacto de base e IGV.
10. Definir comportamiento del logout con venta pendiente y caja abierta.
11. Añadir una ruta mínima para volver a abrir la constancia.
12. Validar dinero contado numérico y no negativo.
13. Impedir doble cierre.
14. Definir qué constituye una venta pendiente.
15. Corregir la contradicción de Jira: 74 Stories en backlog, solo nueve dentro del Sprint.

Condición de salida: las nueve HU cumplen verdaderamente la Definition of Ready.

## Fase 2 — Crear la planificación técnica

Recomiendo crear dos documentos nuevos:

### `02_Diseno_Tecnico_R1_PMV.md`

Debe contener:

- decisiones técnicas aprobadas;
- arquitectura y componentes;
- ambientes;
- matriz de roles y autorización;
- modelo lógico de datos;
- contratos entre interfaz y servicio;
- transacciones y concurrencia;
- seguridad;
- migraciones y datos iniciales;
- despliegue y reversión;
- logs;
- backup y restauración;
- requisitos no funcionales.

### `03_Matriz_de_Trazabilidad_y_Pruebas.md`

Debe relacionar:

| HU/criterio | RN | Interfaz | Servicio | Persistencia | Prueba automática | Prueba manual | Evidencia |
|---|---|---|---|---|---|---|---|

Esta matriz permitirá detectar automáticamente criterios sin subtarea de BD, backend, interfaz o prueba.

`04_Evidencias.md` seguirá registrando resultados reales; el documento 03 solo define qué se deberá probar.

## Modelo mínimo de datos que debe planificarse

No obliga a usar exactamente estas tablas físicas, pero sí a conservar estos conceptos:

| Entidad lógica | Información mínima |
|---|---|
| Cuenta | Nombre, correo normalizado único, hash de contraseña, estado y rol o roles |
| Sesión | Cuenta, inicio, revocación y datos necesarios para invalidarla al salir |
| Rol/permiso | Acciones autorizadas por puesto |
| Categoría | Nombre único y seed de «Productos enlatados» |
| Producto | Categoría, nombre, código único, unidad, precio, mínimo, control de vencimiento y costo promedio |
| Carga inicial | Producto, responsable y fecha; única por producto |
| Lote | Producto, número, cantidad inicial/disponible, costo, vencimiento y fecha de ingreso |
| Caja | Identificación de la única caja |
| Turno | Vendedor, apertura, monto inicial, estado, cierre, esperado, contado y diferencia |
| Venta pendiente | Turno, vendedor y líneas todavía no cobradas, o mecanismo equivalente comprobable |
| Venta | Correlativo, vendedor, turno, base, IGV, total, efectivo, vuelto y clave de idempotencia |
| Detalle de venta | Producto y copias históricas de nombre, precio, costo y cantidad |
| Asignación de lote | Cantidad tomada de cada lote para demostrar FEFO |
| Migración | Versión del esquema aplicada |

Decisiones obligatorias de integridad:

- correo único;
- código de barras único;
- lote único dentro del alcance acordado;
- cantidades enteras válidas;
- dinero con decimal exacto, nunca punto flotante;
- una sola carga inicial por producto;
- un solo turno abierto global;
- existencias nunca negativas;
- correlativo único e inmutable;
- doble confirmación sin venta duplicada;
- timestamps inequívocos y presentación en Lima;
- ventas y turnos cerrados inmutables;
- relaciones históricas protegidas contra borrado accidental.

## Tasks técnicas transversales de BD

| ID propuesto | Resultado observable |
|---|---|
| `S1-ARQ-01` | Arquitectura, motor, versiones, ambientes y decisiones aprobadas |
| `S1-DB-01` | Diagrama y diccionario de datos con trazabilidad a HU/RN |
| `S1-DB-02` | Migraciones versionadas que crean una BD vacía sin pasos manuales |
| `S1-DB-03` | Restricciones, claves foráneas e índices comprobados |
| `S1-DB-04` | Seeds idempotentes de roles, cuentas ficticias, categoría y caja |
| `S1-DB-05` | Reinicio reproducible de datos de prueba |
| `S1-DB-06` | Configuración externa y usuario de BD con mínimo privilegio |
| `S1-QA-DB-01` | Migración y seeds comprobados desde una BD vacía |
| `S1-QA-DB-02` | Fallos inducidos demuestran rollback completo |
| `S1-QA-DB-03` | Pruebas concurrentes de caja, stock, cobro y cierre |
| `S1-OPS-DB-01` | Backup identificado por fecha, versión y checksum |
| `S1-OPS-DB-02` | Restauración en ambiente limpio y verificación del recorrido |

Estas Tasks apoyan varias Stories. No reciben Story Points.

## Subtasks de persistencia por HU

### HU-AUTH-01 / HU-AUTH-03

- Persistir cuentas con correo único, estado, rol y contraseña protegida.
- Crear e invalidar sesión del lado servidor.
- Autorizar operaciones en servidor, no solamente ocultar menús.
- Impedir acceso mediante URL directa después de salir.
- Probar cuenta activa, inactiva, error general y acceso prohibido.

### HU-PROD-02

- Persistir producto y categoría.
- Restringir código repetido.
- Guardar precio decimal, mínimo y control de vencimiento.
- Aplicar default de 10.
- Recuperar el producto para la posterior carga de lotes.
- Mantenerlo no vendible mientras no tenga existencias.

### HU-INV-01a

- Guardar la carga inicial y todos sus lotes dentro de una transacción.
- Impedir una segunda carga inicial.
- Revertir todo si un lote es inválido.
- Guardar fecha de ingreso inmutable.
- Calcular costo promedio según fórmula aprobada.
- Probar dos cargas simultáneas y múltiples lotes.

### HU-CAJA-01

- Crear apertura transaccional.
- Garantizar persistentemente un único turno abierto.
- Probar dos aperturas simultáneas.
- Guardar vendedor, fecha, hora y monto inicial.

### HU-VEN-01b

- Consultar productos y existencias vendibles.
- Excluir vencidos usando fecha de Lima.
- Definir si la venta pendiente se persiste o cómo se detecta.
- No modificar existencias antes de cobrar.
- Revalidar datos en servidor.

### HU-VEN-01c

- Transacción única para venta, pago, detalles, lotes, costo histórico y correlativo.
- Bloquear/revalidar lotes durante el cobro.
- Aplicar FEFO con desempates estables.
- Evitar sobreventa concurrente.
- Implementar una clave de idempotencia o mecanismo equivalente.
- Evitar `MAX(correlativo)+1` sin protección concurrente.
- Probar interrupciones en diferentes puntos de la transacción.

### HU-VEN-02a

- Reconstruir la constancia desde datos históricos de la venta.
- No tomar nombre, precio o costo actuales del producto.
- Mantener número e importes al volver a consultarla.
- Crear una ruta mínima para reabrirla.
- Definir explícitamente si Sprint 1 muestra, imprime o ambas.

### HU-CAJA-02

- Bloquear el turno durante el cierre.
- Revalidar que siga abierto.
- Verificar que no exista venta pendiente.
- Calcular esperado desde ventas confirmadas.
- Guardar contado, diferencia y estado.
- Resolver de manera consistente una carrera entre cobrar y cerrar.
- Impedir un segundo cierre.

## Otras subtareas técnicas faltantes

### P0 — obligatorias

- Flujo de repositorio, ramas y revisión.
- Instalación/build reproducibles.
- Integración continua con análisis y pruebas.
- Contratos de interfaz/servicio.
- Validaciones también en servidor.
- Hash seguro de contraseñas.
- Manejo seguro de sesión/cookies según arquitectura.
- Gestión externa de secretos.
- Protección frente a entradas maliciosas.
- Logs técnicos sin claves ni datos sensibles.
- Ambiente de prueba y ambiente de demostración.
- Despliegue repetible.
- Smoke test después del despliegue.
- Pruebas unitarias e integración automatizadas.
- Datos ficticios reproducibles.
- Accesibilidad básica: etiquetas, foco y teclado.
- Backup y restauración.
- Revisión técnica de seguridad.
- Prueba manual completa e independiente.

### P1 — si el pronóstico continúa sano

- Recorrido E2E automatizado.
- Línea base de rendimiento con volumen acordado.
- Compatibilidad en navegador y viewport objetivo.
- Auditoría ampliada de accesibilidad.
- Runbook de despliegue y reversión.

### P2 — diferible

- Pruebas de estrés superiores a una caja.
- Observabilidad y métricas avanzadas.
- Matriz extensa de navegadores.
- Alta disponibilidad o réplica.
- Backups automatizados con rotación avanzada.

## Cómo rehacer `16_Task_Breakdown.md`

Las nuevas tareas no deben sumarse encima de las 194 horas. Hay que reemplazar y desdoblar.

Ejemplos:

- `S1-EN-01` debe separarse en repositorio/revisión y CI.
- `S1-EN-02` debe dividirse en seed, reset y guía de prueba.
- `S1-EN-03` debe dividirse en navegación, estados comunes y accesibilidad básica.
- `S1-EN-04` debe dividirse en despliegue, configuración/secretos, logs, backup y restauración.
- `AUTH01-02` debe dividirse en credenciales/sesión, autorización e integración.
- `PROD02-03` debe dividirse en persistencia y pantalla.
- `INV01A-02` debe dividirse en validación y transacción.
- `CAJA01-01` debe dividirse en restricción concurrente y servicio de apertura.
- `VEN01C-02/03` debe dividirse en FEFO, concurrencia, transacción, correlativo, idempotencia y snapshots.

Las tareas actuales de pruebas deben dividir sus horas entre:

- prueba automática;
- caso manual documentado;
- comprobación independiente.

Cada fila nueva debe tener:

| Campo obligatorio |
|---|
| ID |
| Tipo Jira |
| Story padre o Stories apoyadas |
| Capa: UI, servicio, BD, QA, seguridad, plataforma |
| Resultado observable |
| CA/RN/NFR respaldado |
| Predecesora |
| Responsable inicial |
| Revisor distinto |
| Horas |
| Evidencia esperada |

La línea base `50 tareas / 194 h / 46 h` debe marcarse como provisional hasta terminar este desglose y reestimarlo.

## Orden de modificación documental

Gemini debe trabajar en este orden:

1. [01_Proyecto_y_Releases.md](C:/Users/walte/OneDrive/Imágenes/planificacion_limpia/01_Proyecto_y_Releases.md)
2. [07_Reglas_de_Negocio.md](C:/Users/walte/OneDrive/Imágenes/planificacion_limpia/07_Reglas_de_Negocio.md)
3. [08_Historias_de_Usuario.md](C:/Users/walte/OneDrive/Imágenes/planificacion_limpia/08_Historias_de_Usuario.md)
4. [09_Product_Backlog.md](C:/Users/walte/OneDrive/Imágenes/planificacion_limpia/09_Product_Backlog.md)
5. Crear `02_Diseno_Tecnico_R1_PMV.md`.
6. Crear `03_Matriz_de_Trazabilidad_y_Pruebas.md`.
7. [16_Task_Breakdown.md](C:/Users/walte/OneDrive/Imágenes/planificacion_limpia/16_Task_Breakdown.md)
8. [14_Sprint_Planning.md](C:/Users/walte/OneDrive/Imágenes/planificacion_limpia/14_Sprint_Planning.md)
9. [04_Evidencias.md](C:/Users/walte/OneDrive/Imágenes/planificacion_limpia/04_Evidencias.md)

`16` debe terminarse antes que `14`, porque sus horas, responsables y dependencias determinan capacidad y cronograma. `04` va al final porque depende del catálogo definitivo de pruebas.

## Capacidad y cronograma

Reglas:

1. Gemini prepara el desglose, pero no inventa horas.
2. Los seis Developers reestiman.
3. Se eliminan solapamientos con las tareas actuales.
4. Se recalculan cantidad de tareas, total de horas y carga individual.
5. Se recalcula reserva.
6. Se construye el camino crítico por tareas.
7. Se distinguen:
   - dependencias duras, que bloquean toda implementación;
   - dependencias de integración/aceptación, que permiten trabajar antes con contratos y datos simulados.
8. Si el trabajo obligatorio supera la capacidad, el Product Owner ajusta alcance; no se eliminan seguridad, migraciones, pruebas o restauración para “hacerlo caber”.

Como referencia, una reorganización mínima podría mantener gran parte de las 194 horas y añadir solo una revisión de seguridad, rondando 198 horas. No debe hacerse cifra canónica hasta que el equipo conozca la tecnología y reestime.

## Cambios por archivo

- `01`: fuentes canónicas nuevas, línea base técnica, tipos de issue, DoR y DoD técnicas, separación DoD/puerta de piloto.
- `07`: roles, primera carga, vencimiento, lotes, costo, redondeos, correlativo, cierre y autorización.
- `08`: criterios observables faltantes de las nueve HU.
- `09`: 74 Stories en backlog, nueve en Sprint; Tasks técnicas adicionales sin SP.
- `02` nuevo: arquitectura, datos, seguridad, ambientes y operaciones.
- `03` nuevo: trazabilidad y plan de pruebas.
- `16`: WBS ejecutable y reestimada.
- `14`: capacidad, camino crítico, cronograma y riesgos actualizados.
- `04`: plantillas de evidencia técnica, backup y restauración; todo inicialmente `Pendiente`.

## Procedimiento para Gemini Flash 3.8

No le entregaría todos los archivos para modificarlos de una sola vez.

1. Crear copia o rama de trabajo.
2. Auditoría de solo lectura.
3. Generar registro de decisiones.
4. Editar un archivo.
5. Mostrar diff y validaciones.
6. Obtener aprobación humana.
7. Continuar al archivo siguiente.
8. Después de `16`, detenerse para que los seis Developers estimen.
9. Actualizar `14` solo con cifras aprobadas.
10. Ejecutar una auditoría final sin editar.
11. Preparar una carga de prueba en Jira.
12. Cargar Jira real únicamente después de aprobación.

## Prompt maestro para Gemini Flash 3.8

```text
Actúa como editor técnico de la planificación del sistema del minimarket.

Objetivo:
Corregir y completar la planificación para que Sprint 1 pueda cargarse en
Jira y ejecutarse sin que los Developers tengan que inventar arquitectura,
persistencia, seguridad, pruebas, despliegue o recuperación.

Tu función es operativa:
- leer, comparar, redactar, normalizar, crear tablas y modificar Markdown;
- detectar inconsistencias y recalcular conteos;
- NO actuar como Product Owner;
- NO declarar participación, estimación, aceptación ni trabajo ejecutado.

Reglas inmutables salvo autorización humana explícita:
- 74 HUs activas y 231 SP;
- 9 HUs y 40 SP en Sprint 1 / R1-PMV;
- 65 HUs y 191 SP sin Sprint ni versión;
- 8 ideas excluidas y 0 SP;
- las Tasks/Subtasks técnicas no son nuevas HUs y no llevan Story Points;
- no asignar trabajo a Sprint 2 o Sprint 3;
- no marcar tareas, pruebas o evidencias como terminadas;
- no inventar nombres, claves Jira, tecnologías, estimaciones, responsables
  confirmados, credenciales o resultados;
- no modificar archivo_historico_* ni RESPUESTAS GEMINI;
- preservar UTF-8 y los identificadores existentes.

Si falta una decisión:
1. escribe [DECISIÓN PENDIENTE];
2. indica quién debe decidirla;
3. explica qué documentos y tareas quedan bloqueados;
4. detente en el checkpoint correspondiente.

Orden:
1. 01_Proyecto_y_Releases.md
2. 07_Reglas_de_Negocio.md
3. 08_Historias_de_Usuario.md
4. 09_Product_Backlog.md
5. crear 02_Diseno_Tecnico_R1_PMV.md
6. crear 03_Matriz_de_Trazabilidad_y_Pruebas.md
7. 16_Task_Breakdown.md
8. 14_Sprint_Planning.md
9. 04_Evidencias.md

Antes de editar cada archivo:
- presenta los cambios propuestos;
- identifica decisiones pendientes;
- espera aprobación.

Después de editar cada archivo:
- presenta el diff;
- informa IDs, conteos y sumas afectados;
- lista decisiones todavía pendientes;
- ejecuta una comprobación de coherencia;
- no continúes sin aprobación.

Para Sprint 1:
- hacer explícitos modelo de datos, migraciones, restricciones, índices,
  seeds, entornos, secretos, transacciones, concurrencia, idempotencia,
  costos históricos, correlativo, backup y restauración;
- tratar el trabajo compartido como Tasks y el específico como Subtasks;
- separar interfaz, servicio/persistencia, prueba automática, prueba manual
  y comprobación independiente;
- reemplazar tareas solapadas; no sumar todo encima de las 194 h;
- no inventar las nuevas horas: dejarlas “Por estimar por los Developers”
  hasta el checkpoint de estimación.

Al finalizar, generar un informe sin editar con:
- lista de archivos cambiados;
- 74/9/65/8 y Story Points verificados;
- cobertura criterio → tarea → prueba → evidencia;
- tareas sin estimar;
- carga por Developer y reserva, si ya fueron ratificadas;
- grafo de dependencias y ciclos;
- decisiones pendientes;
- riesgos residuales;
- confirmación de que no se inventaron evidencias ni estados.
```

## Criterio final para decir “ya está lista”

La planificación estará lista para Jira solamente cuando:

- las decisiones bloqueantes estén aprobadas;
- las nueve HU cumplan DoR;
- las 74 Stories estén preservadas;
- cada criterio tenga implementación, persistencia cuando corresponda, prueba y evidencia;
- migraciones y seeds estén planificados;
- concurrencia y rollback estén cubiertos;
- backup y restauración sean tareas distintas;
- responsables y horas hayan sido ratificados;
- nadie supere su disponibilidad;
- exista reserva explícita;
- el camino crítico quepa en diez días;
- no haya ciclos ni tareas huérfanas;
- Product Owner, Scrum Master y Developers estén registrados;
- ninguna evidencia ficticia aparezca como realizada.

No modifiqué todavía los documentos. Este plan deja a Gemini Flash 3.8 el trabajo operativo de edición y mantiene las decisiones de producto, arquitectura y estimación bajo control humano.
