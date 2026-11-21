# Etapa 02 · Sesión y personal

Actualizado **09/11/2026, America/Lima**. **EN CURSO: sublote 02-A completado en el alcance secuencial de HU-AUTH-03; sublote 02-B de empleados pendiente de recorrido profundo.** No se declara terminado identity, cash, sales ni el sistema. Las propuestas y riesgos abiertos conservan sus estados.

## 1. Alcance, procedencia y fuentes

Se leyó completo el [protocolo](../PROTOCOLO_COMUN.md), el estado general y el [traspaso de01](anexos/ETAPA-01-cierre-y-traspaso.md). El cursor recibido fue AUTH03/CA01, vendedor con turno propio abierto y sin borrador con líneas. Se inventariaron las once HU solicitadas antes de ejecutar el sublote: **33 CA, de los que 18 corresponden a funciones actuales y 15 a funciones futuras**. El anexo previo decía 32 y el complemento de03 decía 17 actuales: ambos recuentos eran incorrectos.

Fuentes pertinentes contrastadas: `21:7–15,21–31,42–44`; `01:91–103,116–134`; `07:165–170,215–228,277–281,333–360`; `08:36–153,869,877`; `09:46–47,76–78,118–124`; `02:80–95,250–279`; `03:65–71,277–307`; `14:75,95`; `16:89–98`; `r1-pmv/CONTROL_SPRINTS.md:20,44–45,58–59`. Los números iniciales identifican los documentos de la raíz. El contrato lógico `/logout` se materializa en `/salir/`; no se exige que exista una ruta literal `/logout`.

Se preservó el árbol con cambios preexistentes; el repositorio Git está en `r1-pmv`, no en la raíz. No se encontraron `AGENTS.md` aplicables en la búsqueda realizada. Ya existían la base `etapa02-20261109`, los anexos de planificación/superficie, scripts, once métodos de auditoría, evidencia parcial y cambios llamados `FIX-E02-01..07`. **No se atribuyen a esta sesión.** El informe principal no existía y el estado decía NO EJECUTADO. Los nombres o marcas verdes de ese material no acreditan cobertura íntegra. [Estado Git y hashes iniciales](evidencias/02-A-20261109T231223297870Z/baseline.json).

El XLSX conserva su papel histórico: se reutilizó su inventario de procedencia de00 y se verificó SHA-256, sin abrirlo ni modificarlo. Se corrigieron nombres de hojas inexistentes y la referencia errónea A52: USR05 figura en `4. Product Backlog Pendiente!A8`. [Procedencia del libro](anexos/ETAPA-00-fuentes.md) · [Planificación reconciliada](anexos/ETAPA-02-planificacion.md). Jira no forma parte de esta auditoría.

## 2. Inventario y clasificación bidireccional

| HU | CA | Selección / implementación observada | Estado de esta revisión |
|---|---:|---|---|
| AUTH-03 | 3 | R1 seleccionado; salida manual implementada | CUMPLE la muestra secuencial documentada; 02-A completado con observaciones abiertas |
| AUTH-04a | 3 | PREVISTO/FUTURO; sesión única ausente | Dos sesiones ADMIN permanecen habilitadas. No es prestación disponible |
| AUTH-04b | 2 | PREVISTO/FUTURO; depende de04a | Descarte por reemplazo de sesión no implementado; salida manual no equivale a04b |
| AUTH-05 | 5 | PREVISTO/FUTURO | Sin recuperación por correo, código ni flujo de renovación |
| USR-01 | 3 | Implementación adicional: lista/búsqueda | PARCIAL; CA03 visual NO EJECUTADO |
| USR-02 | 4 | Implementación adicional: alta | PARCIAL; CA04 confirmación visual NO EJECUTADO |
| USR-03 | 3 | Implementación adicional: edición/rol | PARCIAL; sesiones en navegador y nombres/apellidos pendientes |
| USR-04 | 3 | Implementación adicional: desactivación | PARCIAL; regresiones secuenciales y riesgos de reenvío/concurrencia |
| USR-05 | 2 | Implementación adicional: reactivación | PARCIAL; CA02 permisos completos tras reingreso NO EJECUTADO |
| USR-06 | 2 | PREVISTO/FUTURO | Sin botón de cierre remoto independiente ni su mensaje; desactivar no equivale a esta HU |
| LOG-01 | 3 | PREVISTO/FUTURO | Sin bitácora consultable de ingresos/salidas/bloqueos. LoginAttempt y last_login no son historial |

Cada criterio tiene actor, texto esperado, fuente y línea, ubicación, observación, estado, prioridad y siguiente acción en el [inventario de 33 CA](anexos/ETAPA-02-criterios.md), con [JSON reproducible](anexos/ETAPA-02-criterios.json). Los tres CA de AUTH03 están verificados en la muestra; doce CA de empleados tienen evidencia parcial y tres quedan NO EJECUTADO para su resultado específico. Los quince futuros no se cuentan como aprobados.

El [inventario inverso](anexos/ETAPA-02-superficie.md) identifica **13 grupos de rutas, 26 unidades de interfaz, 11 entradas/controles y 7 decisiones de persistencia**. Incluye etiqueta, finalidad, valor inicial, obligatoriedad, normalización, formato, límites, errores, éxito y persistencia. Los grupos de rutas no son trece endpoints independientes; agrupan dependencias de caja/venta y respuestas de error. No hay exportación ni impresión específica en salida/personal. Constancias y actas comerciales permanecen fuera de este sublote.

| Unidades inversas | Evidencia nueva / estado | Continuidad |
|---|---|---|
| R01–R02; U01,U03–U08; F01 aplicado a salida; P01 | A01–A14, A20–A22, snapshots y regresiones; CUMPLE muestra de salida, CSRF y método | F01 en empleados continúa en02-B; la redacción de U06/U07 conserva DOC-02-05 |
| R09–R11; P02 | Reingreso, menú, aislamiento de turno, rechazo POST ajeno, stock/caja sin cambios | Solo relación con AUTH03; no aprueba caja/ventas completas |
| R03–R08; U02,U09–U24; F02–F11; P03–P07 | Inspección y regresión de servidor parcial; navegador profundo NO EJECUTADO | 02-B con cada CA y frontera del inventario |
| R12–R13; U25–U26 | Inspección; puertas por rol en cliente Django | Falta recorrido visual nuevo de403/404 y cambio de permisos |

RN-29/30 sustentan salida y propiedad del turno. RN-12/24 sustentan correo único y contraseña en empleados, con evidencia parcial de servidor. RN-17 se hereda de01 para login; efectos de reactivación sobre bloqueo necesitan decisión. RN-18 corresponde a recuperación futura. Las cinco tareas S1-AUTH03-UI/SVC/AUTO/MAN/REV se mantienen diferenciadas: ejecución local y capturas apoyan UI/SVC/MAN; **CI e independencia humana de la revisión NO EJECUTADOS**. No se cambia su estado histórico para fabricar aceptación.

## 3. Entorno aislado y ejecución reproducible

- Windows, Python del entorno `r1-pmv/.venv`, Django y SQLite; Chrome instalado en modo headless, dos contextos independientes, viewport1366×768. Segundo contexto representa otro navegador/sesión; no se probó un segundo motor o equipo físico.
- Base nueva: `datos/etapa02a-20261109T231223297870Z/audit.sqlite3`. Cuatro cuentas ficticias `@audit02a.invalid`: ADMIN, ALMACENERO y dos VENDEDORES. Una caja, un producto, un lote de20 unidades, precio8.50 y apertura50.00. Claves aleatorias locales, sin impresión en informes ni capturas.
- El nuevo soporte no lee `.env`, exige directorio marcado, crea un directorio nuevo por ejecución y no dispone de reset/flush. Servidor loopback en puerto53531 para esta ejecución; prueba HMAC de identidad antes de enviar credenciales. `--insecure` de runserver sirvió estáticos exclusivamente en este entorno local con DEBUG=False.
- Original y bases00/01/02 previas conservaron sus hashes. No hubo semillas destructivas, reinicios ni restauración de datos del usuario. Los scripts antiguos `run_live_audit02.py`/`prepare --reset` **no se ejecutaron**: contienen reseteos incompatibles con la conservación exigida.

Desde la raíz, comandos PowerShell:

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/inventario_etapa02.py'
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/run_etapa02_revalidacion.py'
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit02a_run.py' run
```

La segunda orden usa SQLite en memoria y deja informe fechado; la tercera crea **otra** base nueva y conserva las anteriores. No regenerar los inventarios de estado después de avanzar02-B sin actualizar antes el generador, que codifica este corte02-A. [Configuración aislada](soporte/audit02a_settings.py) · [Orquestador](soporte/audit02a_run.py) · [Casos Chrome](soporte/audit02a_chrome.cjs).

## 4. Resultados de HU-AUTH-03

[Registro completo del navegador y snapshots](evidencias/02-A-20261109T231223297870Z/browser.json). Contiene **32 registros favorables: 31 comprobaciones con aserción y una observación A20 de texto sin turno**. No son32 CA. A20 guardó `open_shifts=0`; se reforzó después la aserción del script para futuras ejecuciones, sin atribuir ese cambio a la ejecución ya realizada. No hubo errores JavaScript de página registrados. La revisión visual de capturas confirmó advertencias legibles, botones, identificación por rol y pantalla de ingreso sin datos del empleado en los retrocesos observados.

| ID / fuente | Precondición y acción | Esperado y observado | Estado / prioridad |
|---|---|---|---|
| A00 | Instancia aislada, prueba HMAC | Servidor y directorio corresponden antes del login | CUMPLE, P1 |
| A01–A02, AUTH03/CA01 (`08:41`, `03:69`) | Vendedor1 abre turno50.00 desde menú; sin borrador; menú Cerrar sesión y confirmar | Advierte conservación del turno; ingreso; cero sesiones de ese usuario. Mismo UUID, dueño, importe y estado OPEN; lote20, cero ventas/cierres | CUMPLE muestra, P1 |
| A03–A06, CA03 (`08:43`, `03:71`) | Atrás dos veces; cookie anterior; URL y POST directo | Chrome muestra ingreso sin barra de usuario. Cookie revocada obtiene302 en inicio y POST ventas. Seis rutas exigen ingreso; sin mutación comercial | CUMPLE muestra, P1 |
| A07–A10, CA02 (`08:42`, `03:70`) | Reingreso del dueño, agregar2 unidades, salir y cancelar | Recupera turno sin borrador anterior; nueva venta tiene una línea. Advertencia explícita; cancelar vuelve a inicio y conserva snapshot de sesión/borrador/turno/lote; línea visible al volver | CUMPLE muestra, P1 |
| A11 | Borrador activo; POST salir sinCSRF y PUT conCSRF válido |403 y405 respectivamente; mismo estado de negocio y sesión | CUMPLE muestra, P1 |
| A12–A14, CA02/03 | Confirmar salida con una línea y luego Atrás dos veces | Draft DISCARDED, timestamp, cero líneas; sesión eliminada. Mismo turno OPEN, importe50.00 y lote20, sin venta ni cierre. Retroceso muestra ingreso | CUMPLE muestra, P1 |
| A15–A18, CA03 + RN29/30 | Segundo contexto con vendedor2: menú abrir/preparar/cerrar y POST directo a esas tres rutas | Ve que la caja pertenece a vendedor1; no puede preparar ni cerrar. Los tres POST devuelven200 con rechazo de negocio y sin cambiar turno/borrador/lote/cierres/ventas. No se confunde200 de formulario inválido con éxito | CUMPLE muestra, P1 |
| A19, CA03 | Vendedor1 vuelve a ingresar | Recupera el mismo turno y lista vacía; borrador anterior sigue descartado | CUMPLE muestra, P1 |
| A20–A22, CA01/RN29 | Dueño cierra turno para probar salida sin turno; ADMIN y ALMACENERO también salen desde menú | Las tres salidas revocan sesión y preservan estado comercial. Redacción sin turno conserva observación DOC-02-05 | CUMPLE comportamiento, P3 redacción pendiente |
| A23, AUTH04a | Dos contextos con mismo ADMIN | Ambos acceden200 al inicio; sesión única no implementada. Después ambos salen | PREVISTO/FUTURO; observación de ausencia, P2 |

Ejemplos visuales: [sin borrador](evidencias/02-A-20261109T231223297870Z/A01-sin-borrador.png), [con borrador](evidencias/02-A-20261109T231223297870Z/A08-con-borrador.png), [Atrás tras salir](evidencias/02-A-20261109T231223297870Z/A03-ATRAS-SALIR.png), [turno ajeno](evidencias/02-A-20261109T231223297870Z/A15-turno-ajeno.png). Son cuentas y datos ficticios.

## 5. Regresión de servidor y límites de empleados

**89/89 métodos aprobados:** 11 de `identity.test_etapa02_audit`, 40 de `identity.tests`, 36 de `identity.test_auth_audit01` y dos de `sales.tests` sobre salida/cancelación. `check` y `makemigrations --check --dry-run` aprobados. No es la suite completa del proyecto. [JSON por método](evidencias/02-revalidacion-20261109T231223296324Z.json) · [Log sanitizado](evidencias/02-revalidacion-20261109T231223296324Z.txt).

Los tests acreditan búsqueda por nombre/correo, alta, edición de nombre, duplicado activo/inactivo normalizado, política RN24 con frontera7, correo254/255, POST vacío, restricciones de rol propio/turno abierto, revocación al desactivar y reactivar sin revivir cookie antigua. La evidencia es de formulario/servicio/cliente Django; **no equivale a UI de empleados**.

Límites concretos: `test_fix_e02_03b` comprueba `role_code` almacenado en sesión, no el menú ni todas las puertas tras el cambio. El test de último administrador llama servicio usando otro actor ADMIN inactivo para alcanzar esa rama: no representa dos administradores activos concurrentes. Historial conservado se probó con un `CashShift` cerrado, no con toda la cadena de ventas/cargas. El test cuyo nombre incluye AUTH03/CA01 empieza con borrador; el CA01 sin borrador se acredita por A01/A02 nuevos. No se toma el docstring «exhaustiva» como cobertura de RN18 ni de funcionalidades futuras.

## 6. Hallazgos, correcciones y decisiones

| ID | Evidencia / clasificación | Prioridad y tratamiento |
|---|---|---|
| DOC-02-PROCEDENCIA | Anexos y cambios FIX-E02 preexistían; faltaba informe principal. El complemento03 afirmaba evidencia Chrome de todos los CA sin registro completo de empleados; la prueba anterior no inspeccionaba Atrás inmediatamente ni confirmaba salida sin borrador | P1 documental. Corregido el estado/cobertura, conservados los archivos previos y la [copia del anexo anterior](evidencias/02-A-20261109T231223297870Z/planificacion-pre-reconciliacion.md). Evidencia nueva para esos casos de salida |
| DOC-02-CONTEO |33 CA reales,18 actuales; nombres de hojas y celda XLSX erróneos | P2 documental. Corregido y generado inventario por ID/línea; no se cambiaron requisitos históricos |
| E02-SOPORTE-01 | El cierre inicial consultó el puerto inmediatamente después de terminar el proceso y registró `port_closed=false`; la comprobación posterior encontró puerto cerrado | P2 soporte. Se conserva el [resultado original](evidencias/02-A-20261109T231223297870Z/closure.json), se añade [cierre verificado](evidencias/02-A-20261109T231223297870Z/closure-verified.json) y se ajusta espera acotada a5s. La ejecución funcional del navegador fue exitosa; el orquestador original terminó1 por ese cierre prematuro |
| DOC-02-03 | CA de edición dice nombres/apellidos; UI tiene Nombre completo120 | PARCIAL documental, P2. Mantener campo único y precisar contrato, o separar con migración. Decisión pendiente; no rebajar el CA |
| DOC-02-04 | Cambio administrativo de contraseña opcional no está en CA base deUSR03 | EXTRA SIN REQUISITO, P2. Conservar y proponer criterio de permisos, mensajes, invalidación y política de bloqueo. No es AUTH05 |
| DOC-02-05 | Vendedor sin turno ve «tu turno abierto»; ADMIN/almacén ven condición de turno | Observación editorial P3; PROP-E02-CA-01. No bloqueó flujo; no se cambió producto por decisión de redacción |
| E02-REV-01 | POST `/estado/` alterna valor actual, sin intención de desactivar/reactivar enviada. Inferencia de reactivación por reenvío/página obsoleta | NO EJECUTADO, P1. Caso temprano obligatorio de02-B; reproducir antes de corregir. Propuesta técnica: estado deseado idempotente o rechazo por versión obsoleta |
| E02-REV-02/03/04 | Carrera de correo único, último ADMIN y apertura de turno frente a cambio de rol/desactivación; inspección sin locks comunes | NO EJECUTADO concurrente, P1. Especificar/reproducir en PostgreSQL; SQLite no acredita bloqueos. Coordinación con etapa15 |
| E02-REV-05 | Sesiones existentes: código sincroniza rol, revoca por desactivación e invalida por cambio de hash de clave | PARCIAL servidor, P1. Probar dos sesiones del empleado + ADMIN, permisos posteriores, cambio de propia clave, desactivar/reactivar antes de usar cookie previa |
| DOC-02-BLOQUEO | Reactivar/cambiar correo o clave limpia LoginAttempt; RN17 no define explícitamente ese desbloqueo | EXTRA SIN REQUISITO de política, P2. Alternativas: mantener plazo o autorizar desbloqueo administrativo trazable. Pendiente, PROP-E02-CA-03 |

**No se modificó código funcional del producto en02-A.** Se corrigieron inventario, afirmaciones de evidencia y soporte de auditoría; las correcciones históricas FIX-E02 se conservaron y se revalidaron con la suite actual. No se oculta un incumplimiento funcional probado: los riesgos de empleados listados requieren todavía su reproducción y se entregan con casos concretos.

Propuestas existentes preservadas, todas **PROPUESTO**, sin nuevas HU duplicadas: `PROP-E02-CA-01..03` refinan salida, campos y efectos sobre sesiones; `PROP-E02-HU-01..04` son refinamientos técnicos de AUTH04a/04b/05, USR06 y LOG01 ya existentes, no historias implementadas. LOG01 reutiliza `PROP-E01-HU-01` y retención de etapa15. `PROP-E02-PR-01..03` identifican suites; la ejecución de un test no acepta automáticamente un criterio nuevo. [Detalle de propuestas y alternativas](anexos/ETAPA-02-planificacion.md).

## 7. Omisiones, cierre y cursor exacto

NO EJECUTADO en este corte: recorrido visual completo de empleados; límites de cada campo de alta/edición y mensajes completos; reenvío de estado; sesiones de empleados en dos navegadores tras cambios; historial comercial completo de cuenta desactivada; último administrador/duplicados/rol-turno concurrentes en PostgreSQL; logout concurrente con cobro, alta de línea o segundo puesto; bfcache en otros motores/dispositivos; CI y revisión humana independiente. Las funcionalidades futuras conservan PREVISTO/FUTURO. No se afirman seguridad total ni coincidencia100%.

Estado final de datos: un turno **CLOSED** por acción explícita del dueño después de verificar su conservación OPEN al salir; un acta contado/esperado50.00; borrador DISCARDED sin líneas; lote20; cero ventas; cero sesiones de las cuatro cuentas. [ORM final](evidencias/02-A-20261109T231223297870Z/orm-final.json). El servidor de auditoría quedó detenido; hashes protegidos verificados en el cierre.

**Próximo cursor: 02-B / HU-USR-01 / CA-01 (`08:86`) / ADMIN → menú Empleados → GET `/empleados/`.** Preparar una base nueva exclusiva de02-B sin resetear00/01/02/02-A; crear cuentas ficticias activas e inactivas para los tres roles. Cotejar cada fila nombre/correo/rol/estado con ORM; después CA02 búsqueda/limpieza y CA03 distinción de estados. Antes del primer ciclo de desactivación, reproducir **E02-REV-01** con dos páginas ADMIN: ambas muestran empleado activo, la primera desactiva y la segunda pulsa su botón antiguo «Desactivar»; comprobar estado y sesiones. No marcar aprobado ni arreglar sin preservar el caso previo. Seguir luego USR02/03/04/05 por su matriz y reservar PostgreSQL para las carreras.

Los hallazgos de01 conservan sus destinos y estados. Las etapas03–17 no se declaran auditadas por estas pruebas.
