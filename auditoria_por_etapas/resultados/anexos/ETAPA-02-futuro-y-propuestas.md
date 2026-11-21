# Etapa 02 · Historias futuras y decisiones de identidad

Revisión **09/11/2026, America/Lima**. Complementa [ETAPA-02](../ETAPA-02.md), el [inventario por criterio](ETAPA-02-criterios.md) y el [anexo de planificación](ETAPA-02-planificacion.md). Se leyó completo `PROTOCOLO_COMUN.md`. No se usaron ni modificaron datos ni bases para esta inspección. Las rutas y símbolos se refieren a `r1-pmv`, observados durante 02-B; otros trabajos de 02-B pueden modificar servicios relacionados y deben volver a contrastarse al cierre. Las quince filas son **PREVISTO/FUTURO, no implementadas y NO EJECUTADAS como aceptación de funcionalidad**. Una inspección de código no sustituye prueba visual ni exhaustiva de un despliegue; tampoco constituye una aprobación.

## Fuentes, selección y evidencia

`01_Proyecto_y_Releases.md:116–132` selecciona para R1 nueve HU, incluyendo AUTH-03 y excluyendo las cinco de este anexo. `08_Historias_de_Usuario.md:47–77,136–153` contiene sus quince CA; `09_Product_Backlog.md:118–121,124` las mantiene sin Sprint comprometido y declara dependencias. El XLSX histórico se identificó sin modificar y su papel y SHA-256 constan en [ETAPA-00-fuentes](ETAPA-00-fuentes.md); no se vuelve a abrir ni se acepta un estado por él. RN-17 y RN-18 están en `07:215–228`; RN-24 en `07:277–281`; RN-29 y RN-30 en `07:333–360`.

Inspección acotada de `identity/urls.py:5–12`, `config/urls.py:5–10`, `identity/forms.py`, `identity/models.py`, `identity/views.py`, `identity/services.py` y las plantillas `login.html`, `employee_list.html` y `base.html`: no hay una interfaz/ruta comercial para recuperación por correo, acción independiente de cierre remoto, consulta de eventos, ni servicio que sustituya sesiones previas en `create_server_session`. Solo esta última ausencia tuvo observación directa de navegador: [02-A A23](../evidencias/02-A-20261109T231223297870Z/browser.json) abrió la misma cuenta ADMIN en dos contextos y ambos accedieron con HTTP 200; demuestra coexistencia en esa muestra, no un comportamiento general de todo despliegue ni cumplimiento de AUTH04a. No se probó una ejecución de AUTH04b, AUTH05, USR06 o LOG01 porque no hay flujo correspondiente.

## Matriz por criterio futuro

| CA / fuente / actor | Lo que pide `08` | Contraste actual y siguiente acción |
|---|---|---|
| AUTH-04a/01 `08:52`, empleado | Segundo ingreso cierra sesión anterior inmediatamente y solo deja activo nuevo puesto | A23 muestra ambas sesiones habilitadas. **PREVISTO/FUTURO**, P2; si se selecciona, probar dos contextos, peticiones simultáneas y sesión anterior. |
| AUTH-04a/02 `08:53`, empleado | Al actuar en el puesto anterior bloqueado, mensaje «La sesión fue abierta en otro dispositivo» | No hay flujo ni mensaje de reemplazo observado. **PREVISTO/FUTURO**, P2; especificar entrega del motivo sin exponer cookies. |
| AUTH-04a/03 `08:54`, empleado | Al interactuar otra vez, dirigir al ingreso y exigir credenciales | No existe el estado de reemplazo; el cierre voluntario AUTH03 no lo verifica. **PREVISTO/FUTURO**, P2; probar navegación, POST y cookie reemplazada. |
| AUTH-04b/01 `08:63`, vendedor | Al reemplazarse la sesión, descartar venta en curso y liberar lista | Depende de AUTH04a y VEN01b; el descarte al salir voluntariamente no acredita este caso. **PREVISTO/FUTURO**, P2. |
| AUTH-04b/02 `08:64`, vendedor | Descarte por reemplazo sin alterar existencias ni caja | No se ejecuta el disparador. **PREVISTO/FUTURO**, P2; cotejar lote, caja, líneas y turno antes/después. |
| AUTH-05/01 `08:73`, empleado | Solicitar por correo código numérico de 4 dígitos por 15 minutos | No hay formulario, generador ni envío de recuperación en superficie examinada. **PREVISTO/FUTURO**, P2. |
| AUTH-05/02 `08:74`, empleado | Código válido permite nueva contraseña con RN24 | El campo administrativo `new_password` no es una recuperación por correo/código. **PREVISTO/FUTURO**, P2. |
| AUTH-05/03 `08:75`, empleado | Código usado no admite reutilización | No hay código ni persistencia de uso; **PREVISTO/FUTURO**, P2. |
| AUTH-05/04 `08:76`, empleado | Tras más de 15 minutos, «El código ha caducado» y nuevo código | No hay flujo; **PREVISTO/FUTURO**, P2. Comprobar frontera exacta y mensaje después de definir el reloj de expiración. |
| AUTH-05/05 `08:77`, empleado | 5 códigos erróneos suspenden recuperación 15 minutos sin revelar existencia ni desconectar una sesión autenticada | `LoginAttempt` gestiona fallos de login, no contador de recuperación; **PREVISTO/FUTURO**, P2. |
| USR-06/01 `08:141`, ADMIN | Orden administrativa cierra sesión del empleado inmediatamente | La desactivación existente revoca sesiones **y** desactiva la cuenta; no es una acción de cierre remoto independiente. **PREVISTO/FUTURO**, P2. |
| USR-06/02 `08:142`, ADMIN/empleado | Al continuar, ingreso muestra «Tu sesión fue cerrada por el administrador» | No hay mensaje o causa de revocación específico; **PREVISTO/FUTURO**, P2. |
| LOG-01/01 `08:151`, ADMIN | Consultar nombre, evento ingreso/salida y fecha/hora | `Account.last_login` es solo el último ingreso y `LoginAttempt` mantiene estado agregado: ninguno es historial de eventos. **PREVISTO/FUTURO**, P2. |
| LOG-01/02 `08:152`, ADMIN | Filtrar lista por empleado o rango de fechas | No hay vista/filtros de historial de accesos. **PREVISTO/FUTURO**, P2. |
| LOG-01/03 `08:153`, ADMIN | Diferenciar evento de bloqueo | Contador de bloqueo no demuestra registro histórico diferenciado. **PREVISTO/FUTURO**, P2. |

El actor «dueño» de LOG01 es denominación de negocio; RN29 `07:333–347` contempla ADMIN, ALMACENERO y VENDEDOR, sin cuarto rol técnico. No se asume acceso para otros roles.

## Obligación técnica actual distinta de LOG01

`02_Diseno_Tecnico_R1_PMV.md:244` indica que, si hay borrador con líneas, al confirmar salida se marque `DISCARDED`, **se registre el evento y se elimine sesión en una operación atómica**. `02:321–323` solicita además logs estructurados con eventos mínimos de ingreso, rechazo y salida. LOG01 `08:146–153` pide una **consulta de historial** con filtros y pertenece al backlog futuro: estas dos obligaciones no son sinónimos.

Al inicio de 02-B, `identity/views.py::logout_view` llamaba al descarte transaccional y después a `django.contrib.auth.logout` sin transacción exterior común. Se confirmó mediante fallo inducido después de borrar la sesión; se corrigió envolviendo ambos en `transaction.atomic()`. El [resultado posterior](../evidencias/02-revalidacion-20261109T235142601148Z.json) registra dos métodos aprobados en SQLite de prueba en memoria: éxito normal y fallo inducido con borrador/sesión restaurados, turno y lote conservados. No demuestra concurrencia comercial en PostgreSQL.

En la vista actual no se ve emisión explícita de evento. `app_platform/logging.py` contiene un filtro de redacción, no un registro de eventos por sí mismo. La búsqueda de señales/emisores en `identity`, `app_platform` y `config` no encontró instrumentación explícita de esos eventos. **INCUMPLE la obligación de emisión en la aplicación inspeccionada, P2 (E02-LOG-TECH)**; el contrato conjunto es parcial porque descarte/sesión sí comparten transacción. El punto de entrada, los logs efectivos y observabilidad del despliegue son **NO EXAMINADOS**. La ausencia de consulta LOG01 no excusa una obligación de registro R1. SEC-15-OBS-02 debe definir persistencia transaccional y entrega fiable del evento, campos mínimos sin secretos y comportamiento ante fallo, antes de afirmar atomicidad del conjunto. Conservar por separado la decisión de retención de LOG01.

## Refinamientos existentes y pruebas propuestas

Las siguientes no son nuevas historias: amplían las propuestas ya registradas bajo `PROP-E02-HU-01..04` y `PROP-E01-HU-01`. Todas están **PROPUESTO**, sin aceptación ni implementación atribuida; los CA de08 permanecen sin cambios.

### PROP-E02-HU-01 · Reemplazo de sesión y venta

- Actor y beneficio: empleado, especialmente vendedor, desea evitar uso del puesto anterior y cobros a medias. Precondición: selección futura de AUTH04a y, para04b, turno propio y borrador con líneas.
- Dado un empleado con sesión A activa, cuando inicia con credenciales válidas en B, entonces solo B puede ejecutar acciones protegidas; A al intentar actuar recibe el motivo previsto y acceso al ingreso. Otro rol o un identificador ajeno no puede forzar el reemplazo por solicitud manipulada.
- Dado un vendedor con una línea sin cobrar, cuando B reemplaza A, entonces se descartan las líneas y se libera la venta sin modificar stock ni dinero; el estado/propietario del turno se preserva conforme RN30 salvo decisión expresa distinta. Repetir el reemplazo y competir con agregación/cobro debe dejar un único resultado íntegro; la prueba concurrente requiere PostgreSQL.
- **Decisión pendiente:** quién gana cuando dos ingresos válidos llegan simultáneamente; cómo presentar motivo fiable tras revocar la sesión sin conservar credenciales ni revelar datos; comportamiento con cobro ya en vuelo. Definir también caducidad del motivo y tratamiento de fallos de persistencia. No prescribir una tabla concreta como decisión ya tomada.

### PROP-E02-HU-02 · Recuperación por correo

- Actor y beneficio: empleado sin clave, para recuperar su acceso sin depender del administrador. Precondición: seleccionar AUTH05 y proveedor de envío configurado; las cinco obligaciones base están en RN17/18/24.
- Dado un identificador de correo, cuando se solicita código, entonces la respuesta pública debe ser equivalente para existente/inexistente; solo si procede se envía el código numérico de cuatro dígitos y quince minutos por canal configurado. Errores de proveedor no deben devolver secretos ni confirmar existencia a un visitante.
- Dado un código válido y nueva clave que cumpla RN24, cuando se confirma, entonces se cambia una sola vez; código usado o vencido falla y no modifica clave. Comprobar vacío, formato, 3/4/5 dígitos, cero inicial, reenvío, repetición y tiempos antes/en/después de 15 minutos. Usar proveedor de correo de prueba aislado, nunca una dirección real.
- Dado el quinto código erróneo, cuando se intenta continuar durante quince minutos, entonces solo el flujo de recuperación se suspende, sin revocar una sesión ya autenticada; tras el plazo, validar reinicio según RN17. Probar concurrencia de dos usos del mismo código y retención segura, sin almacenar códigos o credenciales en logs/capturas.
- **Decisiones pendientes:** límite de reenvío y solicitudes, qué ocurre exactamente en el instante de vencimiento, múltiples códigos activos/reemplazados, sesiones ya abiertas tras una recuperación satisfactoria y semántica de errores del proveedor. No presentar estas alternativas como reglas aceptadas.

### PROP-E02-HU-03 · Cierre remoto independiente

- Actor/beneficio: ADMIN autenticado necesita detener acceso de una cuenta sin necesariamente desactivarla. Precondición: empleado objetivo y por lo menos una sesión identificada; la operación debe exigir autorización de servidor y CSRF.
- Dado un empleado activo con sesión, cuando ADMIN confirma cierre remoto, entonces el objetivo ya no puede ejecutar acciones protegidas y recibe el mensaje de USR06 al siguiente intento; su cuenta no debe cambiar de estado por el mero cierre. Una solicitud de VENDEDOR, ALMACENERO o visitante se rechaza sin mutación ni exposición de datos.
- **Decisiones pendientes:** cerrar una o todas las sesiones de la cuenta, si se permite sobre uno mismo o último ADMIN, y si descartar o conservar borrador activo. Si se descarta, probar que caja y stock no cambien; si se conserva, definir quién lo puede recuperar. En ambos casos, conservar el turno y su dueño salvo decisión documentada.

### PROP-E02-HU-04 / PROP-E01-HU-01 · Registro de accesos

- Actor/beneficio: ADMIN supervisa accesos y detecta actividad inusual. Precondición: decidir captura, retención y permiso de consulta; no confundir con logs técnicos de R1.
- Dado un ingreso, salida o bloqueo, cuando ADMIN consulta, entonces ve actor disponible, tipo y fecha/hora inequívocas; el bloqueo se distingue. Dado filtro por empleado o intervalo, cuando se aplica, entonces solo devuelve eventos que cumplen; definir zona `America/Lima` de presentación y límites inclusivos antes de implementar. Rechazar acceso directo de otros roles sin entregar eventos ni alterar datos.
- Dado un identificador inexistente, cuando se registra un intento, entonces usar representación opaca acordada; nunca incluir contraseñas, códigos, cookies o tokens en la interfaz ni logs. Probar paginación/volumen y ausencia de mutación de cuentas si se acuerda; no prometer controles que aún no existen.
- **Decisiones pendientes:** plazo de retención, campos personales mínimos, acceso de administradores a sus propios eventos, precisión del reloj y políticas para sesiones expiradas, cierre remoto y entregas fallidas. La limpieza no debe eliminar bloqueos aún vigentes; coordinar `SEC-15-RETENCION-01` y `PROP-E01-T-RETENCION`.

## Tareas y casos propuestos sin reasignar históricos

`PROP-E02-PR-01..03` ya existen para servicios, HTTP/ORM y navegador. Extenderlos **solo si se seleccionan las HU futuras** con casos de las cuatro secciones: formulario vacío/inválido y fronteras, autenticación y autorización directa, efectos entre sesiones/roles y persistencia, correo ficticio, concurrencia PostgreSQL y UX/mensajes sin secretos. Vincular cada caso a los CA de la tabla; registrar `NO EJECUTADO` hasta ejecución real. Para R1, adjuntar la prueba local de atomicidad del logout a `S1-AUTH03-SVC` y mantener en `S1-SEC-02` la inspección del evento técnico mínimo de `02:244,321–323`; no crear otra HU LOG ni cambiar el estado histórico de Sprint para fabricar cumplimiento.

Para reproducir la inspección de ausencia en PowerShell desde la raíz, sin tocar bases:

```powershell
Get-Content 'r1-pmv/identity/urls.py'
rg -n -i 'user_logged_out|user_logged_in|logging\.getlogger|getLogger|logger\.|signal|auditlog|access.?event|event.?log' r1-pmv/identity r1-pmv/app_platform r1-pmv/config -g '*.py'
```

Una búsqueda sin coincidencias relevantes describe solamente las rutas y código examinados, no demuestra la ausencia de instrumentación en servidores externos.
