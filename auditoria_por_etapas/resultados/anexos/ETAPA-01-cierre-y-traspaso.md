# Etapa 01 · Cierre de auditoría y traspaso

Revisión del 09/11/2026, America/Lima. Complemento actual de [ETAPA-01](../ETAPA-01.md), actualizado con el cierre 01-D. El estado efectivo de la etapa y su cierre operativo se mantienen en ese informe y en [ESTADO_GENERAL](../ESTADO_GENERAL.md). Este anexo registra el alcance revisado, la trazabilidad y las obligaciones que continúan abiertas.

## Alcance auditado

La auditoría del ingreso público comprende HU-AUTH-01/02, siete criterios, RN-12/17/29, seis subtareas de AUTH-01, las entradas GET/POST de `/`, los primeros destinos y sus controles de identidad. Hay inventario previo, pruebas de servidor, persistencia y recorridos de navegador con cuentas ficticias. Cada hallazgo conserva estado, prioridad y destino. El estado final es **auditoría completada con hallazgos abiertos en el alcance de ingreso y bloqueo**. Los estados de los requisitos continúan individualizados en la tabla siguiente.

El protocolo §3 permite documentar alternativas cuando falta una decisión y continuar el trabajo independiente. §4 exige conservar las omisiones y un cursor preciso. El cierre de auditoría permite iniciar la etapa 02 con esas obligaciones visibles. La protección de despliegue, la revisión humana independiente y la autorización transversal siguen pendientes de sus respectivas evidencias.

## Trazabilidad de los siete criterios

Las referencias `08`, `07`, `03` y `09` indican los documentos numerados de la raíz. `T` corresponde a los 53 métodos de 01-B y `H` a sus 70 observaciones HTTP/ORM. El informe principal contiene los vínculos de cada caso, el resultado esperado y observado y las limitaciones de los entornos.

| Criterio y fuente | Actor y comportamiento revisado | Evidencia disponible | Estado al cierre 01-D y obligación restante |
|---|---|---|---|
| AUTH-01/CA-01, `08:18`, `03:60` | Tres roles activos, correo normalizado, ingreso, sesión y destino autorizado | T/H, UI04/06/10 de 01-A, historial de ADMIN/ALMACENERO y ensayo temporal VENDEDOR de 01-C | CUMPLE los flujos secuenciales descritos. La auditoría de operaciones del destino continúa en sus etapas. |
| AUTH-01/CA-02, `08:19`, `03:61` | Visitante, correo inexistente o clave errónea, error general y ausencia de sesión | T/H, UI11/13, rechazo e historial de 01-C | CUMPLE la comparación de mensaje y estado. La comparación estadística de tiempos pertenece a DOC-01-07, etapa 15. |
| AUTH-01/CA-03, `08:20`, `03:62` | Cuenta inactiva con clave correcta, mensaje uniforme y ninguna sesión | T/H, UI12, regresión de 18 métodos de 01-C | CUMPLE el rechazo ensayado. Desactivar una cuenta y comprobar sus sesiones existentes corresponde a etapa 02. |
| AUTH-01/CA-04, `08:21`, `03:63`, RN-29 | Cuenta autenticada, menú por rol y solicitudes directas ajenas sin datos ni cambios | Puertas de personal en T/H, UI07/09 y 01-C; muestra de apertura de caja denegada | PARCIAL para RN-29. Faltan permisos y propiedad sobre los datos comerciales de etapas 02–14 y revisión transversal en 15. |
| AUTH-02/CA-01, `08:30`, RN-17 `07:219` | Quinto fallo consecutivo, plazo persistido de 900 s | T/H, UI14 y serie VENDEDOR con reloj real de 01-C | CUMPLE secuencial. E01-PG-01 verificó cuatro escenarios concurrentes en PostgreSQL 18.4. El alcance se limita a esas ejecuciones. |
| AUTH-02/CA-02, `08:31` | Bloqueo desde otra sesión, clave correcta rechazada y minutos restantes | T/H, UI15–18 y ensayo temporal de 01-C | CUMPLE estados secuenciales descritos. El mensaje se recalcula con la petición. Tráfico, retención y administración conservan alcance separado. |
| AUTH-02/CA-03, `08:32` | Expiración, ingreso válido, contador cero y reinicio del ciclo | T/H con reloj controlado, UI19/20 con fecha preparada y reloj real 01-C | CUMPLE en esos entornos. El ensayo real terminó tras 904663 ms desde el quinto envío hasta el envío válido, según su reloj monotónico. |

[Suite 01-B](../evidencias/01-auth-tests-20261109-122521-777224.json) · [HTTP 01-B](../evidencias/01-http-202611091226025a110c.json) · [Historial 01-C](../evidencias/01-C-historial-2026-11-09T21-00-56-325Z/resultados.json) · [Regresión 01-C](../evidencias/01-C-regresion-identity-20261109.json) · [Espera real 01-C](../evidencias/01-C-espera-20261109T205701803Z.json)

## Conciliación documental y decisiones

| Identificador | Clasificación precisa y fundamento | Alternativas, estado y siguiente trabajo |
|---|---|---|
| DOC-01-01, selección de AUTH-02 | `09:3` declara que el backlog es un corte histórico. `09:75` conserva AUTH-02 posterior, sin Sprint. `21:23` describe su implementación adicional. Ambas afirmaciones son compatibles cuando se distingue su fecha y papel. El registro anterior de CONFLICTO DE FUENTES queda conciliado documentalmente mediante este complemento. | Registrar AUTH-02 como **implementada adicionalmente y verificada de forma acotada**, conservando su selección histórica. Una nueva asignación de release/Sprint o aceptación comercial permanece pendiente si se desea. Es una decisión distinta de constatar el código y las pruebas. |
| DOC-00-05, cinco frente a quince minutos | `03:302`, `16:326` y CONTROL:92 mantienen relatos históricos de cinco minutos. RN-17, los CA de AUTH-02 y `08:877` fijan quince minutos para el comportamiento actual. | Conciliación documental por fecha y vigencia. Enlazar la prueba actual y conservar el antecedente histórico. |
| DOC-01-02, identificador inexistente | RN-17 menciona cuenta reconocida. El servicio aplica estados equivalentes por identificador normalizado, también inexistente. Es EXTRA SIN REQUISITO explícito en el CA base, coherente con evitar revelar existencia. | Aceptar el complemento PROP-E01-CA-02 con equivalencia de respuestas, o especificar otro control opaco para inexistentes y volver a comprobar enumeración. **PROPUESTO**, sin aceptación específica registrada. |
| DOC-01-03, inactiva con clave correcta | El acceso rechazado de una cuenta inactiva contribuye al contador. AUTH-01/CA-03 exige rechazo uniforme. RN-17 habla de contraseñas incorrectas y no resuelve expresamente este caso. | Documentar los intentos rechazados equivalentes por privacidad, o acordar un contador alternativo que conserve respuestas opacas. **DECISIÓN PENDIENTE**. Revisar con la desactivación y reactivación de etapa 02. |
| PROP-E01-CA-01, longitudes | LoginForm admite 320 caracteres y Account almacena como máximo 254. T cubre 254/255/319/320/321, Chrome impide teclear el carácter 321. La diferencia es observable y no existe un criterio aceptado que elija un límite común. | Alinear ingreso y alta a 254, o documentar el máximo técnico mayor del ingreso. Revisar datos heredados y mensajes antes de una modificación. **DECISIÓN PENDIENTE**, vinculada a los formularios de personal de etapa 02. |
| PROP-E01-CA-01, equivalencia IDNA | `strip().casefold()` conserva representaciones distintas de un dominio Unicode y su punycode. T distingue ambos identificadores. Las fuentes piden normalización de espacios y mayúsculas, sin contrato expreso de conversión IDNA. | Documentar las representaciones actualmente admitidas, o aceptar conversión IDNA con análisis de colisiones y migración de cuentas existentes. **PROPUESTO**, sin aceptación específica. El ingreso no debe cambiar aisladamente la clave de cuenta que crean los formularios de personal. |
| DOC-01-04, tráfico | `02:277` exige defensa por IP/sesión. La aplicación inspeccionada carece de ese limitador. | **INCUMPLE en aplicación, P1**. Despliegue real NO EXAMINADO. PROP-E01-T-TRAFICO continúa en etapa 15 con definición de ventana, umbral, origen fiable y redes compartidas. |
| DOC-01-05, retención | LoginAttempt conserva filas, incluso tras éxito. La regla no define plazo ni ventana de caducidad de los intentos 1–4. | **EXTRA SIN REQUISITO de retención, P2**. PROP-E01-T-RETENCION continúa en 15. Preservar bloqueos vivos y significado de consecutividad. LOG-01 de etapa 02 aporta las necesidades de consulta y privacidad. |
| DOC-01-06, administración técnica | Django admin utiliza otra autenticación, requisitos staff y permisos propios. ADMIN comercial y staff son dimensiones distintas. | **PARCIAL / EXTRA SIN REQUISITO comercial, P1**. Elegir portal deshabilitado, restringido por red, o habilitado con controles definidos. PROP-E01-T-ADMIN continúa en etapa 15. |
| DOC-01-07 | La comparación estadística de tiempos y la observabilidad productiva carecen de ensayo. | **NO EJECUTADO**, P2. Continúa en etapa15. |
| E01-PG-01 | Cuatro casos sobre PostgreSQL real, incluidos dos con espera de fila observada, terminaron correctamente. | **CUMPLE la muestra**, P1. La concurrencia comercial y configuración productiva siguen en etapa15. |

Los refinamientos completos ya están definidos en [planificación de etapa 01, §6](ETAPA-01-planificacion.md). Se reutilizan sus identificadores para mantener la trazabilidad.

## Configuración local de despliegue examinada

La revisión de solo lectura localizó `r1-pmv/compose.yaml`, `Dockerfile`, `config/settings.py`, `requirements.txt`, `README.md`, `docs/seguridad.md` y `docs/alcance_comercial_y_normativo.md`. El Compose declara PostgreSQL, migración y web con runserver y puertos en loopback. La imagen inicia Gunicorn. Settings configura cookies, HTTPS y confianza en `X-Forwarded-Proto` para demo/production. La documentación exige ese encabezado al proxy. Los archivos examinados carecen de configuración de Nginx, Caddy, Traefik, WAF o limitación de solicitudes. La ausencia de esos archivos no permite determinar los controles del despliegue real.

No se necesita resolver el proveedor o los límites de producción para iniciar etapa 02. Etapa 15 debe obtener la configuración efectiva del punto de entrada y contrastarla con `02:277`. La búsqueda local se efectuó sin abrir `.env`, credenciales o servicios externos.

## Entradas actuales de backlog y matriz

El complemento fechado del backlog debe registrar AUTH-01 con CA-04 parcial y AUTH-02 como implementación adicional observada. Debe enlazar las tareas ya propuestas de tráfico, retención, admin y concurrencia, y el refinamiento existente de HU-LOG-01. Las alternativas de longitud, IDNA y equivalencia de rechazos necesitan estado **PROPUESTO** o **DECISIÓN PENDIENTE**. La solicitud de terminar la auditoría autoriza su revisión y documentación, sin elegir por sí sola una política específica.

El complemento de la matriz debe enlazar los cuatro CA AUTH-01 a `AT/MT-AUTH01-01..04`, `ST-AUTH01-01..03` y sus resultados actuales. Los tres CA AUTH-02 se enlazan a PROP-E01-PR-02 y a las ejecuciones de 01-A/B/C. La matriz debe conservar los estados y las limitaciones de la tabla anterior, incluyendo CA-04 parcial, el ensayo real y la concurrencia pendiente. Las tareas S1-AUTH01-AUTO y S1-AUTH01-REV siguen pendientes de evidencia propia de CI y revisión humana independiente. Las ejecuciones locales sustentan la auditoría actual.

## Continuidad y obligaciones ejecutables

| Destino | Caso o tarea concreta | Estado y dependencia |
|---|---|---|
| Cierre operativo de01 | Hashes, quince cuentas, tablas comerciales, enlaces y servicios detenidos | Verificador01-D ejecutado después de las pruebas e informes, con evidencia final enlazada desde ETAPA-01. |
| Superficie admin de01 | Cinco fallos de staff en perfil nuevo Chrome, mensaje genérico constante, sin sesión | Ejecutado y documentado en01-C. Política y permisos completos pendientes de15. |
| Etapa 01, campos | Cuatro casos Unicode, espacios e IDN completados en Chrome en01-D | Respuestas, filas y capturas en el informe. Cuenta IDN existente y punycode conservan evidencia de servidor de01-B. |
| Etapa 02, AUTH-03/CA-01 | VENDEDOR con sesión y turno propio OPEN, sin borrador ACTIVE con líneas. Menú Salir, advertencia, confirmar. Comprobar sesión invalidada e ingreso, turno y propietario conservados | Primer cursor de etapa 02, `08:41`, `03:69`, RN-30 `07:357`, GET/POST `/salir/`. Preparar datos aislados propios de esa etapa. |
| Etapa 02, AUTH-03/CA-02–03 | Borrador con al menos una línea. Cancelar conserva sesión/borrador. Confirmar descarta líneas y revoca sesión sin afectar stock/caja. Atrás/URL/cookie y reingreso del dueño/otro vendedor | Caso posterior al CA-01. `08:42–43`, `03:70–71`. El borrador pertenece a CA-02 y no a la precondición de CA-01. |
| Etapa 02, USR/AUTH-04/LOG | Clasificar primero su selección. Auditar alta/cambio/desactivación y efecto sobre sesiones, y refinamiento PROP-E01-HU-01 de LOG-01 | Sin aprobación inferida por el login. Reutilizar decisiones de correo, IDNA y rechazos al revisar formularios de personal. |
| Etapas 03–14 | Continuar AUTH-01/CA-04 por rutas, objeto/propiedad y datos comerciales de cada módulo | Cada denegación debe comprobar ausencia de exposición y mutación. Registrar cobertura por ruta y rol. |
| Etapa 15 | PROP-E01-T-TRAFICO, RETENCION, ADMIN; DOC-01-07 y concurrencia comercial | Mantener estados por requisito. Incluye infraestructura efectiva, latencia y filtrado de excepciones. E01-PG-01 aporta antecedente de ingreso PostgreSQL de cuatro escenarios. |
| Etapa 17 | Conciliar decisiones y cobertura pendiente, incluido S1-AUTH01-REV | La aceptación humana independiente y el cierre transversal requieren evidencia propia. |

El siguiente cursor funcional es **ETAPA-02 / HU-AUTH-03 / CA-01 / `/salir/` / VENDEDOR con turno propio abierto y sin borrador activo con líneas**. La información de login de etapa 01 permanece como antecedente reproducible.

## Cobertura final del inventario inverso

Cada grupo enumera todas sus unidades. El detalle de cada etiqueta, campo, ruta y persistencia se conserva en el inventario original.

| Unidades | Estado al cierre y evidencia | Continuidad |
|---|---|---|
| R01–R02, F01–F04, U01–U05, U10–U19, U21 | CUMPLE los casos de ingreso/validación/CSRF/destino probados en T/H y Chrome A/C/D | Longitud/IDNA y restauración del correo requieren contrato explícito. |
| U06–U08 | PARCIAL en las promesas de las tarjetas públicas. Texto y asignación inventariados | Producto/personal/inventario/caja/ventas/reportes en02–13. |
| U09 | EXTRA SIN REQUISITO medible. «Acceso seguro» observado como texto | No define aceptación de seguridad global. |
| U20 | NO APLICA a un mensaje de éxito de login. La vista expresa éxito por sesión/redirección | El contenedor de mensajes de base se reutiliza en otros flujos. |
| R03 | CUMPLE acceso y menú de los tres roles | Cifras y reportes de panel pendientes de13. |
| R04–R08 | PARCIAL. Puertas y métodos de identity comprobados en H/T, menú y denegación en Chrome | Salida y gestión de personal completas en02. |
| R09 | PARCIAL. Staff/no-staff y cinco errores en portal independiente observados | Política y permisos por modelo en15. |
| R10 | CUMPLE carga observada de estilos y recursos de la pantalla en navegador local | CDN y despliegue real fuera de muestra. |
| P01–P09 | CUMPLE persistencia y decisiones en los casos T/H, reloj real y cuatro escenarios PostgreSQL | Retención, equivalencia IDNA, observabilidad y permisos globales continúan con sus estados. |

[Cuatro escenarios PG](../evidencias/01-D-postgresql-20261109T220349Z.json) · [Regresión final20](../evidencias/01-D-regresion-20261109-170211.json) · [Unicode en Chrome](../evidencias/01-D-unicode-2026-11-09T21-59-32-996Z/observaciones.json) · [Cinco fallos en admin](../evidencias/01-chrome-admin-failures-20261109T211121-168Z/observaciones.json)

Los vínculos fechados añadidos al final de09,03 y21 permiten localizar este complemento sin reasignar estados históricos. Las propuestas de criterio siguen siendo propuestas. El producto conserva el incumplimiento de tráfico en aplicación y los demás hallazgos abiertos.
