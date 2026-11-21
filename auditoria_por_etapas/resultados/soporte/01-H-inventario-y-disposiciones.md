# 01-H · Inventario, trazabilidad y decisiones

**Fecha:** 15/11/2026, America/Lima. Primera pasada acotada de la etapa 01; entrada solicitada `01-G-DESPLIEGUE-Y-CONTRATO-01`. Se usa `01-H` para no sobrescribir el soporte y los datos `01-G` ya existentes en el espacio compartido. No inicia la segunda pasada global. [Informe](../ETAPA-01.md#vigente-01-h).

Fuentes vigentes: [08](../../../08_Historias_de_Usuario.md), HU-AUTH-01/02, RN-17/29, DOC-01-06, DOC-02-04 y CT-COHERENCIA-UI; [02](../../../02_Diseno_Tecnico_R1_PMV.md), [16](../../../16_Task_Breakdown.md), 01/14/21 y `CONTROL_SPRINTS`. [07/09/03](../../../03_Matriz_de_Trazabilidad_y_Pruebas.md) son vistas derivadas. Los inventarios [01-E](01-E-inventario.md), [01-F](01-F-inventario-y-disposiciones.md) y [original](../anexos/ETAPA-01-superficie.md) se conservan: sus referencias 320 caracteres, tarjeta «reportes», selección histórica de AUTH-02 y rutas de empleado deben leerse en su fecha. Aquí el correo admite **254** y AUTH-02 está seleccionada en R1. XLSX histórico no localizado; no usado. Jira no se examina.

## Requisitos, reglas y tareas

| ID | Actor / obligación | Clasificación y evidencia 01-H |
|---|---|---|
| AUTH-01/CA-01 | ADMIN, ALMACENERO, VENDEDOR activos: ingreso, sesión y opciones de rol | R1; **CUMPLE en muestra**: tres contextos, normalización, recarga y sesión; no aprueba operaciones de destino. Chrome R03, suite focal. |
| AUTH-01/CA-02 | Visitante: correo inexistente o clave errónea, mismo texto general | R1; **CUMPLE en muestra**; Chrome R05/R06 y pruebas de servidor. No acredita ausencia de canal temporal. |
| AUTH-01/CA-03 | Cuenta inactiva: mismo mensaje y sin sesión | R1; **CUMPLE en muestra**; Chrome R05/R06 y suite. |
| AUTH-01/CA-04 | Rol no autorizado: denegar sin exposición ni mutación | R1; **PARCIAL**: visitante redirigido; ADMIN 200 y ALMACENERO/VENDEDOR 403 en empleados; muestras de rutas en suite. No se cubren todas las rutas, objetos y POST con datos de negocio preexistentes. |
| AUTH-02/CA-01 | Quinto rechazo consecutivo activa bloqueo 15 min | R1; **CUMPLE en muestra**: Chrome y reloj controlado; cinco conexiones PG. |
| AUTH-02/CA-02 | Bloqueada: cualquier clave, minutos restantes, otra sesión | R1; **CUMPLE en muestra**: segundo contexto y fronteras con reloj simulado; no mide tiempo restante continuamente en pantalla. |
| AUTH-02/CA-03 | Al vencer, clave correcta accede y reinicia contador | R1; **CUMPLE en muestra**, con reloj controlado y también en Chrome tras 903,027 s de reloj de pared desde el quinto fallo; los últimos 29,713 s de espera se midieron monotónicamente. Contador posterior 0 y fecha nula. Se conserva 01-C como evidencia histórica. |
| RN-17 | Mismo identificador normalizado para existente/inactivo/inexistente; cinco fallos, 15 min y reinicio | Aplicable a ingreso; **CUMPLE en las muestras anteriores**. Recuperación es HU-AUTH-05, futura y no ensayada; `/admin/` es superficie separada y elude el control. |
| RN-29 | Un rol comercial y autorización servidor | **PARCIAL**: pruebas directas de muestra; roles de staff/superuser no equivalen a roles comerciales. |
| DOC-02-04/C-03 | Renombrar/reactivar preserva bloqueo; desbloqueo explícito | **CUMPLE en sonda de servicio aislada**; no cierra todo el proceso de personal ni todas las carreras. |
| DOC-01-06/C-01 | Canal comercial no elude el control mediante admin | **INCUMPLE en aplicación**: staff/superuser bloqueados entran por `/admin/login/` y alcanzan `/inicio/`; configuración real del perímetro no examinada. |
| DOC-01-06/C-02 | Eventos con contexto sin secretos, transaccionalidad y rechazo seguro | **PARCIAL**: portal público instrumentado en muestra; admin observado con cero eventos nuevos, colector y retención real no examinados. |
| DOC-01-06/C-03 | No filtrar datos sensibles en error/log | **CUMPLE en sonda controlada** de canarios y falla de handler; no prueba ausencia universal de filtración. |
| CT-COHERENCIA-UI/C-01..04 | Mensajes, semántica, promesas y clasificación | **PARCIAL** en ingreso; las promesas de menú requieren permisos de todos los módulos. Los 21 elementos abajo están inventariados; no todos los estados dinámicos se recorrieron en navegador. |
| S1-AUTH01-UI/SVC/AUTHZ/AUTO/MAN/REV | UI, servicio, permisos, automatización, recorrido y revisión independiente | Se revalidan muestras UI/SVC/AUTO/MAN. AUTHZ global y revisión humana independiente **NO EJECUTADAS**; no se altera su estado histórico. |
| S1-SEC-01/02; S1-DB-01..05; S1-ENV-01; S1-CI-01 | Seguridad, datos, entorno y CI | Solo los subcasos identificados en este informe; CI, migración operativa y despliegue real **NO EJECUTADOS**. |
| AUTH-03, AUTH-04a/04b, AUTH-05, USR, LOG UI | Salida, sesión única, recuperación, personal y bitácora visual | AUTH-03/USR son dependencia de etapa 02; AUTH-04a/04b/05 y LOG UI futuros, no se declaran implementados ni auditados aquí. |

Numerador/denominador: **7/7 CA seleccionados inventariados; 6/7 CUMPLE en muestra y 1/7 PARCIAL**, sin extender ese resultado a todo RN-29, administración técnica ni módulos de destino. Las muestras son finitas y no son aceptación humana independiente.

## Rutas y acciones inversas

| ID | Método/ruta y acción | Vínculo / estado 01-H |
|---|---|---|
| R01/R02 | GET/POST `/`: abrir/enviar credenciales; PUT/DELETE | AUTH-01/02, RN-17; probados login y errores; PUT/DELETE 405. GET autenticado y demás variantes: suite. |
| R03 | GET `/inicio/`: ver identidad, rol y opciones | AUTH-01/CA-01; recarga 200 de tres roles. Las cifras y acciones internas no se aprueban aquí. |
| R04 | GET/POST `/salir/`: confirmar salida | AUTH-03, etapa 02; dependencia para prueba de cookie revocada, no cierre integral de logout. |
| R05 | GET `/empleados/` | AUTH-01/CA-04; muestra de puerta 200/403/redirección, contenido y negocio de personal en etapa 02. |
| R06–R08 | `/empleados/nuevo/`, `/empleados/<uuid>/editar/`, `/empleados/<uuid>/estado/confirmar/` y `/empleados/<uuid>/estado/` | USR/etapa 02; inventariados, sin reauditar ciclo completo. |
| R09 | `/admin/`, `/admin/login/`, `/admin/identity/account/` | DOC-01-06; probado staff/superuser ficticio, no todos los permisos/modelos ni red productiva. |
| R10 | `/static/identity/app.css`, `navigation.js`, `favicon.svg`; `/static/admin/css/base.css` | Diseño/UX, no autorización; 200 con handler de prueba, 404 en WSGI simple con DEBUG=False. Proxy real no examinado. |

## Pantalla, campos y salida inversa

Todos son para visitante en `/` salvo estado de error/éxito expresamente indicado. **21/21 grupos U inventariados y relacionados**; clasificación de ejecución por fila. Las referencias U corresponden al inventario histórico, no a 21 casos independientes.

| ID | Literal / acción / condición | Necesidad y estado en este corte |
|---|---|---|
| U01 | Título «Ingresar — Sistema de gestión» | AUTH-01/presentación; visto en navegador y DOM. |
| U02 | Marca «Minimarket · Sistema de gestión», enlace de inicio | Navegación de entrada; visible. Destino del enlace no recorrido en este sublote. |
| U03 | «Saltar al contenido» | Accesibilidad; inventariado. La captura móvil muestra solapamiento transitorio pero la geometría medida lo situó fuera del viewport: requiere comprobar manualmente foco/transición, **PARCIAL**. |
| U04 | «Gestión de minimarket» y «Bienvenido. Escribe tu correo y tu contraseña.» | AUTH-01; visible en Chrome. |
| U05 | «Cada persona ve solo las operaciones de su puesto: administración, almacén y caja.» | AUTH-01/CA-04 y RN-29; visible; promesa global **PARCIAL**. |
| U06 | Administrador: «Productos, empleados, proveedores y resumen diario de ventas.» | RN-29/etapas 02, 03, 04, 13; visible, semántica de cada módulo fuera de este sublote. |
| U07 | Almacenero: «Inventario, mermas y alertas de stock.» | RN-29/etapas 05–08; visible, funcionamiento de cada operación no revalidado aquí. |
| U08 | Vendedor: «Turno de caja y ventas.» | RN-29/etapas 09–12; visible, operación completa no revalidada aquí. |
| U09 | «Acceso seguro» | Presentación, no certificación; visible, alcance de seguridad **PARCIAL** por admin/tráfico. |
| U10 | «Iniciar sesión», «Usa tu cuenta de trabajo para continuar.» | AUTH-01; visible. |
| U11 | «Correo de trabajo» | AUTH-01; ficha F01, visible y ensayado. |
| U12 | «Contraseña» | AUTH-01; ficha F02, visible y ensayada. |
| U13 | Botón «Iniciar sesión» | AUTH-01/02; POST probado. |
| U14 | «Tus permisos y acciones dependen del rol asignado.» | RN-29; visible; semántica global parcial. |
| U15 | «Minimarket · Sistema de gestión» al pie | Presentación; visible. |
| U16 | «Correo o contraseña incorrectos» | AUTH-01/CA-02/03; literal uniforme verificado en tres casos de Chrome. |
| U17 | «Demasiados intentos fallidos consecutivos. Inténtelo nuevamente en {minutos} minuto(s).» | AUTH-02; quince mostrado en dos contextos y un minuto antes del vencimiento real; fronteras de redondeo con reloj controlado en servidor. |
| U18 | Errores requeridos, formato, longitud y nulo | AUTH-01/validación; casos de servidor reejecutados; recorridos visuales de cada variante **NO EJECUTADOS** en 01-H. |
| U19 | Contenedor de errores globales, `role=alert` | AUTH-01/02/accesibilidad; mensaje visible; semántica con lector de pantalla **NO EJECUTADA**. |
| U20 | Mensajes flash, cuando existen | Base/CT-COHERENCIA-UI; estado dinámico **NO EJECUTADO**. El ingreso correcto de este código no crea mensaje propio. |
| U21 | CSRF y `next` ocultos condicionales | Seguridad/navegación; CSRF negativo HTTP 403 sin intentos y destinos en suite; valores no registrados en evidencia. |

| Campo/salida | Inicial, obligatoriedad, tipo y límites | Normalización, errores y persistencia |
|---|---|---|
| F01 `email` | Vacío, obligatorio, EmailInput, máximo **254**, `autocomplete=username`, autofoco; placeholder «nombre@empresa.com» | `strip().casefold()`; 255/319/320/321 y nulo rechazados sin nuevas filas; formato inválido se valida antes de credenciales. El correo se repuebla escapado. Unicode/punycode generan identificadores distintos; decisión IDNA pendiente. |
| F02 `password` | Vacía, obligatoria, PasswordInput, `autocomplete=current-password`; sin máximo propio definido en formulario | `strip=False`; espacios significativos, no se repuebla tras rechazo; hash Argon2/PBKDF2. No se registra contraseña en informes. |
| F03 CSRF | Oculto, generado; obligatorio al POST | Ausente/inválido 403 sin incremento; rotación y flags en suite. TLS y proxy reales no examinados. |
| F04 `next` | Oculto si existe, opcional; POST precede query | Escapado; solo host/esquema permitido; el destino local vuelve a autorizar. URLs externas probadas en suite/HTTP. |
| Minutos / éxito | Entero redondeado hacia arriba, mínimo 1; éxito 302 a destino seguro o `/inicio/` | 15/14/2/1 y vencimiento exacto con reloj simulado; persistencia de contador/cookie y no extensión del bloqueo verificadas en suite. |

P01–P09 del [anexo inverso](../anexos/ETAPA-01-superficie.md) describen normalización, HMAC, contador, transacción, roles, expiración, sesión y rechazo. Se corrige su lectura histórica: hoy existe `IdentityAuditEvent` además de `LoginAttempt`; **no** puede inferirse privacidad de todos los registros a partir del HMAC de una tabla.

## Disposiciones y alternativas

| ID / tipo | Problema y alternativas | Beneficio, riesgo, costo e impacto | Estado |
|---|---|---|---|
| `01H-TEST-COOKIE` / pruebas | Prueba de CSRF asumía `csrftoken` y `sessionid`; usar nombres de `settings`. | Beneficio: prueba también configuraciones válidas; riesgo bajo, afecta solo test; costo bajo, impacto `identity/tests.py` y caso AUTH-01. | **ACEPTADA como corrección técnica del caso ya aceptado**, por alcance explícito de pruebas y evidencia de fallo; **IMPLEMENTADA y VERIFICADA** con nombres por defecto y personalizados. No cambia regla de negocio ni producto ejecutable. |
| `PROP-01F-ADMIN` / arquitectura y seguridad | Deshabilitar admin en entrada comercial o aislar canal de mantenimiento y unificar controles. | Beneficio: cierra bypass; riesgo: impedir soporte o falsa protección por proxy; costo bajo/medio, afecta `config`, permisos y operación. Falta elegir canal real. | **PROPUESTA**; DOC-01-06/C-01 ya aceptado e incumplido. |
| `PROP-E01-T-TRAFICO` / RNF y tarea | Presupuesto por origen confiable/agregado antes del trabajo costoso, tras medir NAT y proxy. | Beneficio: limita abuso y crecimiento; riesgo: bloquear tienda compartida o confiar en XFF manipulable; costo medio, afecta borde, login y pruebas. | **PROPUESTA/INVESTIGACIÓN**; sin inventar ventana ni afirmar cobertura productiva. |
| `PROP-01F-TRAF-HASH` / diseño | Durante bloqueo se ejecuta Argon2. A: revisar bloqueo antes del hash para todos los identificadores; B: limitar en entrada antes del servicio, o combinar. | Ahorro CPU; riesgo de diferencia temporal, privacidad y carreras; costo bajo/medio, afecta `services.py`, pruebas PG y medición. Los requisitos vigentes no fijan por sí solos la alternativa técnica ni el presupuesto. | **PROPUESTA**; observación verificada, no se cambia contrato para justificar código. |
| `PROP-E01-T-RETENCION` / tarea y datos | `LoginAttempt` e `IdentityAuditEvent` crecen; acordar vida de contador y bitácora y limpieza protegida. | Acota volumen; borrar bloqueos/1–4 o evidencia perjudica seguridad; costo medio, afecta migraciones/comando/PG y operaciones. | **PROPUESTA/INVESTIGACIÓN**; ningún plazo aprobado ni borrado ejecutado. |
| `PROP-E01-HU-01` / HU-LOG-01 y privacidad | Los eventos ficticios de ingreso guardan identificador de correo y metadatos de existencia/estado, aunque `LoginAttempt` use HMAC. Considerar identificador opaco para desconocidos y acceso/retención, manteniendo trazabilidad necesaria. | Reduce exposición; riesgo de perder correlación o trazabilidad tras rotar clave; costo medio y efecto en auditoría, consultas, migración y política de datos. | **PROPUESTA**, no activar la pantalla LOG futura; hechos reales y plazo pendientes. [Conteos sin identificadores](../evidencias/01-H-20261115/privacidad-agregada.json). |
| `PROP-01F-STATIC-DEPLOY` / diseño y arquitectura | Servir estáticos con solución en aplicación o proxy/`collectstatic`, según topología. | Recupera CSS/JS; riesgo de configuración distinta en despliegue real; costo bajo/medio, afecta imagen, proxy y pruebas de despliegue. | **PROPUESTA**; WSGI simple reproducido, despliegue real no examinado. |
| `PROP-02E-IDNA-01` / RN y criterios | Unicode y punycode forman dos identificadores; diagnosticar colisiones antes de canonicalizar o conservar política explícita. | Evita cuentas/contadores ambiguos; riesgo de colisiones y cambio de identidad existente; costo medio, afecta alta, edición e ingreso. | **PROPUESTA**, decisión pendiente; sin consultas ni migración sobre datos reales. |
| `PROP-01H-UX-SALTO` / diseño y prueba | Repetir manualmente foco y transición del salto en móvil; captura y geometría difieren. | Evita obstrucción/accesibilidad falsa; riesgo bajo y costo bajo, impacto `base.html`/CSS. | **INVESTIGACIÓN**, no atribuir defecto confirmado a una captura en transición. |

El benchmark local de 20 muestras por grupo describe tiempos del proceso aislado; no establece equivalencia estadística ni seguridad frente a enumeración o carga productiva. Las propuestas no se convierten en decisiones por su presencia en esta tabla. No se crean nuevas HU ni se promueven historias futuras.
