# ETAPA 01 — Inventario inverso de superficie y perímetro

Corte estático: **09/11/2026, America/Lima**. Se leyó completo el protocolo común. `rg --files -g AGENTS.md` no encontró instrucciones locales en el árbol. Este anexo inventaría el código observado antes de las correcciones de 01; **no acredita ejecución de navegador, HTTP ni base de datos**. La evidencia ejecutada y el estado final se concilian en [ETAPA-01](../ETAPA-01.md). No se modificó la aplicación desde esta revisión. Las referencias de funciones son también anclas si una corrección posterior desplaza las líneas.

## 1. Alcance, actores y clasificación

| Elemento | Selección / respaldo | Clasificación de esta revisión |
|---|---|---|
| Formulario público de ingreso, rechazo y sesión | HU-AUTH-01 CA1–4, `08_Historias_de_Usuario.md:13–21`; RN-29, `07_Reglas_de_Negocio.md:333–347` | Actual; comportamiento por comprobar en informe principal |
| Cinco fallos, 15 minutos, tiempo restante, expiración | HU-AUTH-02 CA1–3, `08:25–32`; RN-17, `07:215–219`; guía 21:23 | Implementado adicional; vigencia documental en anexo de planificación |
| Visitante | Persona sin sesión, sin rol persistido | Actor público de `/`; debe ser redirigido desde operaciones privadas |
| ADMIN / ALMACENERO / VENDEDOR | `Role.Code`, `identity/models.py:11–24`; rol FK obligatorio de Account | Tres roles exclusivos; no equivalen a `is_staff` ni `is_superuser` |
| Otras HUs de identity (salida, personal, panel) | Rutas observadas debajo | NO EXAMINADO como flujo funcional de esta etapa; etapas 02/13 |
| Límite IP/sesión | `02_Diseno_Tecnico_R1_PMV.md:277`, seguridad punto 9 | Requisito técnico separado; ausencia en aplicación inspeccionada, despliegue NO EXAMINADO |
| Retención/limpieza del estado de intentos | No se encontró plazo aceptado ni trabajo de limpieza | EXTRA SIN REQUISITO definido; propuesta técnica, sin inventar plazo |
| Administración Django | `config/urls.py:5`, `identity/admin.py`; guía21:23 | Superficie técnica adicional, separada; permisos y mutaciones completas en etapa 15 |

## 2. Pantallas, rutas y acciones

Fuentes: `r1-pmv/identity/urls.py:5–13`, `views.py` (funciones indicadas), `config/urls.py:4–10`.

| ID inventario | Ruta / métodos declarados | Actor / acción / salida | Persistencia y vínculo |
|---|---|---|---|
| E01-R01 | `/`, GET | Visitante abre login; cuenta ya autenticada redirige `/inicio/` | Sin autenticación nueva; AUTH01 entrada |
| E01-R02 | `/`, POST | Visitante envía email/password; validación de formato; error de campo, credenciales o bloqueo; éxito 302 | LoginAttempt; sesión Django y `last_login` en éxito; AUTH01/02 |
| E01-R03 | `/inicio/`, GET | Cuenta autenticada con rol soportado; menú, identidad y panel según rol | `dashboard`; acceso/rol pertenece al tramo; exactitud de totales etapa13 |
| E01-R04 | `/salir/`, GET/POST | Cuenta autenticada; confirmación/cierre de sesión y posible descarte | AUTH03/RN30, etapa02. Solo dependencia para preparar recorridos 01 |
| E01-R05 | `/empleados/`, GET | ADMIN; listado de cuentas de roles soportados | USR01, etapa02; acceso denegado es candidato AUTH01/CA4 |
| E01-R06 | `/empleados/nuevo/`, GET/POST | ADMIN; alta y validación | USR02, etapa02 |
| E01-R07 | `/empleados/<uuid:account_id>/editar/`, GET/POST | ADMIN; edición | USR03, etapa02 |
| E01-R08 | `/empleados/<uuid:account_id>/estado/`, POST | ADMIN; desactivar/reactivar | USR04/05, etapa02 |
| E01-R09 | `/admin/`, `/admin/login/` | Sitio y formulario independientes de Django | Véase §7, no equivale a login público |
| E01-R10 | `/static/identity/app.css`, `/static/identity/favicon.svg` | Recursos públicos enlazados por base | Presentación; no autenticación ni autorización de negocio |

No hay enlace propio visible para registro libre, recuperar clave, mostrar contraseña o recordar sesión en `login.html`. AUTH04/05 no se deducen implementadas por pertenecer al catálogo de historias. El POST del formulario carece de `action`: se envía a la URL actual, incluida su query; `next` se toma de POST y luego GET. Los métodos distintos de GET/POST en `/` están rechazados por decorador. Las rutas propuestas `/login` de diseño y `/` del producto deben conciliarse como divergencia documental, no asumir alias existente.

## 3. Inventario completo de la pantalla pública y sus salidas

Fuentes: `identity/templates/identity/login.html:1–32`, `base.html:1–14,162–203`; `forms.py:6–26`; `views.py:26–50`; `services.py:17–67`. Los textos se enumeran para trazabilidad, no como resultados ya verificados.

| ID | Elemento visible / acción | Propósito, condición, salida | Respaldo y clasificación |
|---|---|---|---|
| E01-U01 | Título «Ingresar — Sistema de gestión» | Título de documento del login | Presentación AUTH01 |
| E01-U02 | Marca «Minimarket / Sistema de gestión», enlace `/` | Regresar a ingreso; `aria-label=Minimarket, inicio` | Navegación auxiliar AUTH01 |
| E01-U03 | «Saltar al contenido», `#contenido` | Enlace accesible; main con tabindex -1 | Ayuda técnica, sin CA explícito |
| E01-U04 | «Gestión de minimarket»; «Bienvenido. Escribe tu correo y tu contraseña.» | Identifica sistema y solicita las dos credenciales | AUTH01 |
| E01-U05 | «Cada persona ve solo las operaciones de su puesto: administración, almacén y caja.» | Promesa de autorización; no basta ocultar opciones | AUTH01 CA1/4 y RN29; requiere servidor |
| E01-U06 | Tarjeta Administrador: «Productos, empleados, proveedores y reportes.» | Descripción pública, sin botón | Mezcla funciones actuales con «reportes» amplio: PARCIAL/ambigüedad, no acredita REP; etapa13 |
| E01-U07 | Tarjeta Almacenero: «Inventario, mermas y alertas de stock.» | Descripción pública, sin botón | Inventario/ampliaciones; auditoría funcional etapas05–08 |
| E01-U08 | Tarjeta Vendedor: «Turno de caja y ventas.» | Descripción pública, sin botón | RN29; auditoría funcional etapas09–12 |
| E01-U09 | «Acceso seguro» | Promesa general de presentación | No es certificación ni prueba de cobertura de admin/tráfico |
| E01-U10 | «Iniciar sesión» y «Usa tu cuenta de trabajo para continuar.» | Encabezado y ayuda del formulario | AUTH01 |
| E01-U11 | Campo «Correo de trabajo» | Ver ficha E01-F01 | AUTH01 |
| E01-U12 | Campo «Contraseña» | Ver ficha E01-F02 | AUTH01 |
| E01-U13 | Botón «Iniciar sesión» | Submit POST; `novalidate` permite enviar errores al servidor | AUTH01/02 |
| E01-U14 | «Tus permisos y acciones dependen del rol asignado.» | Ayuda permanente | AUTH01 CA1/4, RN29 |
| E01-U15 | Footer «Minimarket · Sistema de gestión» | Identidad de página | Presentación |
| E01-U16 | Error «Correo o contraseña incorrectos» | Cuenta inexistente, contraseña errónea, cuenta inactiva o rol no admitido, antes del bloqueo | AUTH01 CA2/3; mismo literal del servicio |
| E01-U17 | «Demasiados intentos fallidos consecutivos. Inténtelo nuevamente en {minutos} minuto(s).» | Error no asociado a campo; quinto intento y cualquier clave durante bloqueo | AUTH02 CA1/2; techo de minutos con mínimo 1; no hay contador JavaScript en vivo |
| E01-U18 | Errores de campo obligatorios/formato/longitud/nulo | `form.email.errors` / `form.password.errors`; `role=alert` | Validación técnica; distinguir de error de credenciales |
| E01-U19 | Errores globales en `data-testid=login-error`, `role=alert` | Lista Django en contenedor de alerta | AUTH01/02 |
| E01-U20 | Mensajes flash de base, `aria-live=polite` | Se muestran si existe cola messages; éxito/error/info según tags | Login no añade éxito a cola en la vista inspeccionada; no inventar mensaje de éxito |
| E01-U21 | CSRF y `next` ocultos | Control técnico y navegación, no salida visual | Fichas E01-F03/04 |

No hay tablas, filtros, descarga, impresión ni salida comercial en la pantalla de ingreso. El éxito se manifiesta por redirección y sesión, no por un mensaje textual específico.

### Fichas de campos

| ID / nombre | Etiqueta y propósito | Inicial, obligación, tipo/formato/límites | Limpieza, errores, persistencia |
|---|---|---|---|
| E01-F01 `email` | Correo de trabajo; identificador de cuenta | Vacío; obligatorio; EmailInput/email; autocomplete=username, autofocus; placeholder=nombre@empresa.com; máximo formulario 320 en el corte previo; modelo cuenta 254 | EmailField recorta espacios; servicio `strip().casefold()`; no cambia correo almacenado durante ingreso. Vacío «Este campo es obligatorio.»; inválido «Introduzca una dirección de correo electrónico válida.»; nulo y exceso según Django. Tras rechazo se repuebla el correo, escapado por plantilla. Throttle almacena HMAC, no email en claro. Desajuste 320/254 requiere decisión/documentación; 319/320/321 son casos separados. |
| E01-F02 `password` | Contraseña de la cuenta | Vacío; obligatorio; PasswordInput/password; autocomplete=current-password; placeholder=Ingrese su contraseña; `strip=False`; sin máximo explícito en formulario | Espacios significativos; no se repuebla al rechazar (`render_value=False`); vacío/nulo errores Django. Verificación hash; no campo contraseña en LoginAttempt. Límite de cuerpo HTTP no sustituye un máximo aceptado de contraseña. |
| E01-F03 `csrfmiddlewaretoken` | Prueba técnica de origen de POST | Oculto; valor generado por Django; obligatorio por middleware en escritura | No almacenar ni mostrar evidencia en claro. Ausente/manipulado debe 403 antes del servicio. Cookie CSRF HttpOnly/SameSite Lax; Secure solo demo/production. |
| E01-F04 `next` | Destino posterior al ingreso | Oculto solo si hay valor; opcional; inicial POST o query GET; sin validación de longitud propia | Django escapa atributo HTML. Tras éxito `url_has_allowed_host_and_scheme` acepta host actual y HTTPS si petición segura; rechazo vuelve dashboard. No es permiso: el destino debe reautorizar rol. No se persiste como dato de cuenta/negocio. |

Mensajes de traducción/límites y widgets expandidos se conservan en [formularios 00](ETAPA-00-formularios-generados.md). El cuerpo máximo predeterminado de Django es 2.621.440 bytes y 1.000 campos (`django/conf/global_settings.py:315,319`); el proyecto no los redefine. **No se ensayó en esta revisión carga masiva ni se propone ejecutarla sobre el servidor del usuario.**

## 4. Primer destino y navegación que comunica autorización

`base.html:25–130` condiciona enlaces por `user.role.code`; `base.html:117–122,160` muestra inicial/nombre y nombre de rol. Los valores están escapados de forma predeterminada. Ocultar enlaces es evidencia estática de UI, no de permisos del servidor. `identity/authorization.py:18–34` comprueba autenticación y rol de la cuenta cargada; las operaciones concretas deben probarse con petición directa.

| Actor | Enlaces de sidebar visibles declarados (etiqueta → ruta) | Tramo respaldado / límite |
|---|---|---|
| Todos autenticados | Inicio → `/inicio/`; marca → `/inicio/`; Cerrar sesión → `/salir/` | AUTH01 ingreso/rol; salida completa etapa02 |
| ADMIN | Productos → `/productos/`; Registrar producto → `/productos/nuevo/`; Categorías → `/productos/categorias/`; Proveedores → `/inventario/proveedores/`; Ver inventario y alertas → `/inventario/stock/`; Vencimientos de lotes → `/productos/vencimientos/`; Ajuste físico → `/inventario/ajustes/nuevo/`; Empleados → `/empleados/`; Historial de turnos → `/caja/turnos/`; Historial de ventas → `/ventas/historial/` | AUTH01 CA1/4 solo acceso autorizado; operaciones en etapas02–13 |
| ALMACENERO | Ver inventario y alertas → `/inventario/stock/`; Vencimientos de lotes → `/productos/vencimientos/`; Existencias iniciales → `/inventario/carga-inicial/`; Entrada de mercadería → `/inventario/entrada/`; Registrar merma → `/inventario/bajas/nueva/`; Catálogo de productos → `/productos/`; Proveedores → `/inventario/proveedores/` | Igual; ampliación respecto RN29 R1 debe permanecer identificada |
| VENDEDOR | Apertura de caja → `/caja/abrir/`; Preparar venta → `/ventas/`; Cerrar turno → `/caja/cerrar/`; Mis ventas del turno → `/ventas/historial/turno/` | Igual; propiedad y negocio en etapas09–12 |

`dashboard.html:8–11` muestra nombre de rol y «Sesión activa». Sus tarjetas (líneas43–96) replican acciones y prometen: alta producto con stock cero; catálogo con precio/disponibilidad/mínimo; consulta/alta/edición/desactivación de empleados; lotes iniciales con cantidad/costo/vencimiento; reposición de productos ya cargados; merma por daño/vencimiento/rotura; declarar efectivo inicial; buscar productos/ver existencias antes de cobrar. Están inventariadas, pero estas promesas no se aprueban en etapa01.

Salidas de resumen (`dashboard.html:19–27`): ADMIN ve número y total S/ de ventas de hoy, descuentos S/, turnos abiertos; ADMIN/ALMACENERO ven productos con stock bajo, lotes por vencer 30 días y lotes vencidos con stock. Botones: inventario, vencimientos y para ADMIN historial de ventas (`:29–35`). Clasificación: NO EXAMINADO como reporte; etapa13. Un login correcto no demuestra exactitud de estas cifras.

## 5. Persistencia y decisiones de servidor del login

| ID / elemento | Fuente precisa del corte | Conducta estática y casos que deben verificarse |
|---|---|---|
| E01-P01 normalización | `Account.normalize_email`, models.py:78–79 | `strip().casefold()`; variantes comparten cuenta y clave de intentos. No se modifican email/email_normalized durante login. |
| E01-P02 identificador de bloqueo | `authenticate_active_account`, services.py:33–36 | HMAC SHA256 de correo normalizado, sal fija del propósito y SECRET_KEY del despliegue; PK 64 caracteres. No equivale a anonimización absoluta; rotar clave cambia identificador. |
| E01-P03 fila de estado | models.py:27–33 | `identifier` PK; `failures` positivo pequeño, inicial0; `locked_until` fecha nullable; `updated_at` auto_now. Sin FK a cuenta ni IP/sesión; sirve también para desconocidos. |
| E01-P04 ciclo de intento | services.py:35–61 | `get_or_create`, transacción y `select_for_update`; consulta cuenta y trabajo hash; bloqueo en quinto fallo; timestamp calculado al procesar; rechazo bloqueado no prolonga plazo ni aumenta contador. SQLite no prueba bloqueo por fila. |
| E01-P05 cuenta activa/rol | services.py:50 | Acceso requiere cuenta, activa, clave válida y rol dentro de tres códigos. Fallos de inactiva/rol también incrementan contador aunque la clave sea correcta; no distinguir estado en respuesta. |
| E01-P06 expiración | services.py:45–49 | Estricto `locked_until > now` bloquea; en igualdad/expirado reinicia fallos y fecha antes de evaluar resultado. Reintento válido permitido; inválido inicia nuevo ciclo en1. |
| E01-P07 éxito | services.py:50–56,64–67 | Conserva fila para estabilidad concurrente, pone fallos0 y guarda fecha actual. `login()` rota/crea sesión servidor; `role_code` almacenado. Django señal de login actualiza `last_login`; consultar DB para acreditarlo. |
| E01-P08 sesión | config/settings.py:76–84 | Backend DB; cookie HttpOnly/SameSite Lax; cerrar navegador previsto; Secure depende entorno. No hay TTL de inactividad de 5min configurado. Backend Django default edad14 días (`global_settings.py:486`), asunto completo etapa02. |
| E01-P09 rechazo | LoginForm y servicio | Error de formato no llama autenticación; error de credenciales puede crear/actualizar LoginAttempt, pero no sesión autenticada ni datos de negocio. «No modifica datos» debe referirse a datos protegidos, no exigir cero cambios al contador esperado. |

No se observa registro de cada intento individual: la tabla conserva un agregado por identificador. No confundir crecimiento por nuevos identificadores con una fila por cada fallo repetido. Éxito no elimina fila y no hay vencimiento automático; `updated_at` permite estudiar retención, pero no hay proceso de limpieza en el código buscado.

## 6. Hallazgos estáticos separados y decisiones pendientes

| ID | Hallazgo, evidencia e inferencia delimitada | Estado / prioridad | Siguiente acción |
|---|---|---|---|
| E01-S01 | No hay limitador IP/sesión/global en servicio ni middleware. Diseño02:277 lo exige; bloqueo por correo no limita volumen distribuido ni correos nuevos. Configuración proxy externa no inspeccionada. | INCUMPLE en capa de aplicación respecto diseño; despliegue NO EXAMINADO / P1 | Definir umbral/ventana y fuente fiable de IP; PROP-E01-T-TRAFICO |
| E01-S02 | El hasheo ocurre antes de devolver bloqueo (services.py:37–46 del corte), incluso para cuenta inexistente. Es trabajo comparable útil contra enumeración, pero consume CPU durante bloqueo. No se midió latencia ni resistencia a carga. | PARCIAL defensa de tráfico / P1 | Evaluar junto limitador; conservar respuesta uniforme; no declarar vulnerabilidad explotada sin prueba |
| E01-S03 | No hay TTL/limpieza de LoginAttempt; una fila por correo normalizado nuevo de formato válido. La expiración libera acceso pero no borra registro. | EXTRA SIN REQUISITO de retención / P2 | Definir política antes de eliminar, proteger bloqueo vigente y concurrencia; PROP-E01-T-RETENCION |
| E01-S04 | `/admin/login/` utiliza backend distinto del servicio 5/15, confirmado por ruta de código. | PARCIAL perímetro, adicional sin HU de operación / P1 | Prueba aislada staff; decisión de exposición; PROP-E01-T-ADMIN, etapa15 |
| E01-S05 | Config define `SENSITIVE_POST_PARAMETERS`, pero Django `SafeExceptionReporterFilter` lee `request.sensitive_post_parameters` (debug.py:206–223). En corte previo `login_view` no tiene decorador; la configuración por sí sola no protege POST de reporte de excepción. | INCUMPLE defensa de datos ante excepción en corte previo / P1 | Reproducir sin secretos reales y aplicar decorador + prueba; delegado a corrección de aplicación; estado final en ETAPA01 |
| E01-S06 | Login público no tiene `never_cache` en corte previo; plantilla puede devolver correo repoblado al fallar. `dashboard` y logout sí lo tienen. | PARCIAL privacidad de navegación / P2 | Verificar cabecera/comportamiento, considerar `never_cache`; estado final en ETAPA01 |
| E01-S07 | Transacción/select_for_update expresa intención de serializar intentos, pero SQLite no acredita el comportamiento concurrente de PostgreSQL. | NO EJECUTADO / P1 | Dos conexiones PG y barrera; quinto intento, primer registro, éxito concurrente; PROP-E01-T-CONCURRENCIA |
| E01-S08 | Uniformidad textual no demuestra uniformidad de tiempos entre algoritmos/estado de hash ni confidencialidad de reportes/logs. | NO EJECUTADO como análisis estadístico / P2 | Medir en entorno controlado y revisar observabilidad aparte; no usar microbenchmark casual como garantía |
| E01-S09 | `next` admite destino local aunque rol no autorizado; el destino debe denegar sin efectos. No hay allowlist de rutas de negocio en login. | PARCIAL hasta ejecución / P1 | Matriz de destinos locales/externos/esquema y roles; PROP-E01-CA-NAVEGACION |

Las filas E01-S05/06 describen la línea base y pueden haber sido corregidas durante la misma etapa por otro agente. No sustituir esta observación histórica por una afirmación de incumplimiento final: usar pruebas y diff del informe principal.

## 7. Django `/admin/` como superficie independiente

Fuentes: `config/urls.py:5`, `identity/admin.py:7–27`, `config/settings.py:59–60`; Django instalado `contrib/admin/sites.py:202–208,414–450`, `contrib/admin/forms.py:7–27`, `contrib/auth/backends.py:59–72`, `contrib/auth/base_user.py:36–37`.

- El sitio usa la misma Account y sesión Django, pero `AdminAuthenticationForm` → `authenticate` → `ModelBackend`, sin servicio `authenticate_active_account`. La condición de puerta es activa + staff. ADMIN de negocio sin staff no basta; ALMACENERO/VENDEDOR con staff no queda excluido automáticamente por su rol comercial. Esto describe código, no concede ni inventa privilegios a las cuentas reales.
- `username` representa `Account.USERNAME_FIELD=email`; campo contraseña estándar; CSRF y `next` del login estándar. Mensaje de credenciales de staff difiere del formulario público. Modelo backend consulta `get_by_natural_key` sobre email; no usa `email_normalized`. Por tanto no se debe transferir evidencia de normalización de `/` a `/admin/login/`.
- Login Django estándar usa `sensitive_post_parameters` y `never_cache`; ello no protege automáticamente la vista pública personalizada.
- `AccountAdmin` permite gestionar rol, activa, staff, superuser, grupos y permisos por fieldsets. `RoleAdmin` permite código/nombre. Son operaciones técnicas y pueden cambiar identidad sin pasar por servicios de negocio (por ejemplo las condiciones de desactivación). Sus efectos completos están NO EXAMINADOS y asignados a etapa15.
- `LoginAttempt` no está registrado en admin. No hay interfaz administrativa propia de desbloqueo ni evidencia de política para borrar intentos.
- El inventario00 contiene 65 patrones administrativos, nueve modelos, familias de lista/alta/edición/historial/borrado y formularios; véase [perímetro00](ETAPA-00-admin-y-perimetro.md). Este anexo no repite ni aprueba esos 65 casos.

Alternativas de alcance, **pendientes**: (A) deshabilitar/montar solo en canal de mantenimiento privado; (B) mantener público con protección de tráfico/autenticación documentada, cuentas staff dedicadas, mínimo privilegio y pruebas separadas; (C) integrar bloqueo compartido cuidadosamente en backend, definiendo si cuenta bloqueada en `/` debe impedir admin y cómo recuperar acceso. Riesgos: A cambia operación técnica; B deja dos contratos; C puede crear bloqueo de administración provocado por terceros. No elegir ni aplicar silenciosamente.

## 8. Propuestas trazables (no aceptadas por este anexo)

**PROP-E01-T-TRAFICO — tarea técnica propuesta, P1.** Necesidad: impedir que múltiples identificadores o sesiones eludan defensa de volumen. Dependencias: diseño02 §2.9.9, infraestructura real, IP confiable, volumen legítimo del minimarket. Decidir umbral, ventana, combinación global/origen/identificador, almacenamiento compartido y respuesta/reintento. Criterios propuestos: Dado el umbral configurado, cuando se supera desde el mismo origen o distribuido según política, entonces se rechaza antes del trabajo costoso y no se autentica; tras la ventana se recupera. Cambiar correo o abrir sesión no evade el control definido; una cabecera X-Forwarded-For fabricada no cambia origen salvo proxy autorizado. Mensaje uniforme y sin revelar existencia. Pruebas: límites N-1/N/N+1, varias sesiones/workers, backend indisponible y usuarios legítimos en NAT. No fijar N arbitrariamente ni confundirlo con los cinco fallos de RN17.

**PROP-E01-T-RETENCION — tarea técnica propuesta, P2.** Necesidad: limitar acumulación sin romper bloqueo persistente. Política de plazo y justificación operativa pendientes. Criterios propuestos: Dado un estado inactivo más antiguo que la retención aprobada, cuando se ejecuta limpieza por lotes, entonces elimina solo elegibles, conserva bloqueos vigentes y no toca cuentas/sesiones/datos comerciales; debe ser idempotente y medible sin registrar identificadores sensibles. Definir efecto de limpiar un contador 1–4 antiguo y si «consecutivos» tolera ventana. Pruebas: fronteras temporales y carrera entre limpieza e intento en PostgreSQL. No se agregó borrado automático en esta etapa.

**PROP-E01-T-ADMIN — tarea técnica propuesta, P1.** Necesidad: contrato verificable de acceso de mantenimiento. Precondiciones: alternativa A/B/C decidida, cuentas ficticias staff/no staff y datos aislados. Criterios propuestos: Dado no staff, ningún rol comercial puede entrar; dada cuenta staff autorizada, solo permisos técnicos concedidos; fallo cinco veces y bloqueo se comportan según política explícita para cada puerta; inactivo se rechaza. Probar cruce sesión `/`↔`/admin/`, normalización, acceso directo, CSRF, no filtración y operaciones que eluden reglas de servicios. No crear una HU comercial de administración técnica solo para justificar una ruta extra.

**PROP-E01-T-CONCURRENCIA — tarea técnica y prueba propuesta, P1.** Precondición PostgreSQL desechable aislado. Dos conexiones reales, sincronizar creación de primera fila y cinco fallos/suceso válido sobre mismo identificador. Criterios: una fila, ninguna actualización perdida ni 500, plazo único de15min, resultado compatible con orden serializado. Añadir múltiples identificadores y recuperación por error; no sustituir con SQLite ni mock de bloqueo.

**PROP-E01-CA-NAVEGACION — criterios propuestos para AUTH01, P1.** Dado `next` externo/protocolo no permitido, cuando el ingreso es correcto, entonces destino `/inicio/`; dado destino local autorizado, entonces se conserva; dado destino local prohibido por rol, entonces el servidor destino deniega y conserva datos protegidos. Entradas: query/POST contradictorios, URL absoluta mismo host, `//otro`, esquema no HTTP, HTTPS→HTTP, comillas/HTML, recurso inexistente. Mensajes no incluyen secretos. Aclarar si volver al formulario con sesión activa ignora `next` por decisión de producto.

**PROP-E01-CA-SECRETOS — criterios técnicos propuestos para AUTH01, P1.** Dada una excepción al autenticar con datos ficticios, cuando se genera reporte estándar con DEBUG=False, entonces contraseña/CSRF y variables sensibles no aparecen en claro; dado rechazo normal, contraseña no reaparece en HTML ni URL, errores uniformes y sin datos de cuenta. Verificar también cabeceras de cache y navegación atrás. Una prueba de reporte estándar no garantiza todos los sinks de logs o producción.

Para incorporar: vincular tareas al bloque de seguridad de diseño/backlog y nuevos casos de prueba a matriz actual sin reescribir estados históricos de R1. Ninguna propuesta por sí sola significa implementado o verificado.

## 9. Conciliación de correcciones durante la etapa

El trabajo de corrección paralelo reprodujo la exposición de POST y variables en el reporte estándar con DEBUG=False, el cache del ingreso y el POST totalmente vacío sin errores de campos. El código posterior añade `@sensitive_post_parameters()`, `@sensitive_variables()` y `@never_cache` sobre `login_view` (`views.py:27–29`), enlaza el formulario por método POST (`:37`) y protege variables de `authenticate_active_account` (`services.py:31`). Las observaciones E01-S05/S06 quedan **CORREGIDAS con verificación acotada** en la evidencia [regresiones antes](../evidencias/01-auth-regresiones-antes-final.txt) y [pruebas después](../evidencias/01-auth-tests-despues.txt), producida por ese trabajo. El POST vacío añade un defecto de validación corregido; no se cambiaron los límites de email/contraseña. La ejecución final y sus alcances exactos pertenecen al informe principal, no a la inspección estática de este anexo.

## 10. Reproducción de esta inspección y límites

Comandos de solo lectura desde raíz:

```powershell
rg -n 'LoginAttempt|authenticate_active_account|locked_until|SENSITIVE_POST_PARAMETERS|sensitive_post_parameters' r1-pmv/identity r1-pmv/app_platform r1-pmv/config -g '*.py'
rg -n 'rate.?limit|throttl|clearsessions' r1-pmv -g '*.py' -g '*.md' -g '!evidencias/**'
rg -n 'path\(' r1-pmv/identity/urls.py r1-pmv/config/urls.py
```

La búsqueda no inspecciona configuración externa de proxy ni credenciales. No se leyó `.env`, no se abrió base del usuario y no se generó tráfico de carga. La ausencia de un mecanismo en archivos inspeccionados no demuestra su ausencia en infraestructura. **Todos los recorridos ejecutados y correcciones deben consultarse en ETAPA-01; este anexo por sí solo deja navegador, persistencia y concurrencia NO EJECUTADOS.**

