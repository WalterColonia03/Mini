# ETAPA 01 — Correcciones y pruebas de autenticación

Fecha: 09/11/2026 (America/Lima). Este anexo registra comprobaciones Django Client/ORM y unitarias. **No constituye evidencia de navegador**, de despliegue, de PostgreSQL concurrente ni de todos los módulos que aparecen como destinos protegidos.

## Conservación y entorno

Se leyó `PROTOCOLO_COMUN.md` completo. No se encontraron archivos `AGENTS.md` mediante el censo de la raíz. `r1-pmv` ya tenía modificaciones amplias en aplicación y documentos. Antes de editar se copiaron exactamente `identity/views.py`, `forms.py`, `services.py` y `tests.py` en `resultados/datos/etapa01-20261109/baseline-auth/`, excluido por el `.gitignore` de resultados. No se restauró ni sobrescribió el trabajo previo.

Cambios propios: dos archivos de aplicación (`views.py`, `services.py`) y nuevo `identity/test_auth_audit01.py`. `forms.py`, `models.py`, `urls.py`, plantillas y `tests.py` preexistente quedaron sin edición de este sublote. El diff contra la copia inicial se conserva en [01-auth-cambios.diff](../evidencias/01-auth-cambios.diff).

Se usó Python 3.12 del entorno `r1-pmv/.venv`, configuración **audit01_settings**, con `TEST.NAME=:memory:` y las cookies llamadas `sessionid`/`csrftoken` solo dentro del runner para compatibilidad con pruebas preexistentes. Django informó `file:memorydb_default?mode=memory&cache=shared`; las migraciones y las pruebas operaron en esa base efímera, destruida al terminar. No se arrancó `manage.py` con la configuración del operador. No se alteró la base HTTP aislada para estas pruebas. Los secretos de fixtures de los tests nuevos se generan al ejecutarlos; no se imprimen ni persisten como evidencia.

## Defectos reproducidos y cambios

| ID | Fuente / defecto inicial | Corrección | Evidencia / clasificación |
|---|---|---|---|
| FIX-E01-01 | `identity/views.py`, `request.POST or None`: un POST sin claves se convertía en formulario sin enlazar y no mostraba los dos errores de obligatoriedad | Enlazar mediante `request.method == "POST"`, incluso con QueryDict vacío | INCUMPLE inicial → CUMPLE caso corregido; P2; `test_empty_post_is_bound_and_reports_both_required_fields` |
| FIX-E01-02 | Login GET y POST fallido carecían de `Cache-Control`; la respuesta fallida conserva el identificador enviado | Aplicar `never_cache` a login; cabeceras `no-store` y `private` verificadas | Endurecimiento de privacidad implementado/verificado, P2; no prueba el comportamiento de todos los navegadores o proxies; `test_get_and_failed_post_are_not_cacheable` |
| FIX-E01-03 | Con DEBUG=False, `ExceptionReporter` incluía contraseña en POST y variables locales del servicio. El setting `SENSITIVE_POST_PARAMETERS` no sustituye los marcadores que lee Django | `sensitive_post_parameters()` y `sensitive_variables()` en login, `sensitive_variables()` exterior a `transaction.atomic` en servicio | INCUMPLE inicial → CUMPLE casos corregidos; P1; dos tests de filtro de informes. No se envió correo ni se imprimió el informe sensible |

La redacción usa el mecanismo documentado de [Django 5.2 para filtrar informes](https://docs.djangoproject.com/en/5.2/howto/error-reporting/#filtering-sensitive-information), contrastado con `.venv/Lib/site-packages/django/views/debug.py:190–218,244–304`. El efecto de caché coincide con la documentación de [never_cache](https://docs.djangoproject.com/en/5.2/topics/http/decorators/#caching). La comprobación de filtrado cubre errores inducidos en la vista y servicio; no certifica todos los loggers, excepciones de middleware, DEBUG=True ni infraestructura externa.

## Antes y después

- [Regresiones antes, corte final](../evidencias/01-auth-regresiones-antes-final.txt): **4 métodos, 5 fallos** contando los dos subtests GET/POST de caché. Los fallos son mensajes de aserción sin valores secretos. El primer corte [antes](../evidencias/01-auth-regresiones-antes.txt) tenía una aserción del servicio que inspeccionaba texto y no variables locales; se reforzó antes de editar la aplicación, y el corte final reprodujo la exposición local.
- [Después, corte 01-A](../evidencias/01-auth-tests-despues.txt) y [manifiesto 01-A](../evidencias/01-auth-tests-20261109-115809-570846.json): **45 métodos aprobados** (26 nuevos + 19 preexistentes).
- [Después, ampliación 01-B](../evidencias/01-auth-tests-20261109-122521-777224.txt) y [manifiesto 01-B](../evidencias/01-auth-tests-20261109-122521-777224.json): **53 métodos aprobados en 10,999 s**; 34 nuevos en `identity/test_auth_audit01.py`, 16 preexistentes `AuthenticationAndAuthorizationTests` y tres preexistentes de bloqueo. Check de sistema sin incidencias. Las advertencias 403/404/405 corresponden a rechazos esperados. La suite completa del proyecto **NO fue ejecutada** por este sublote.

### Cobertura de los 34 tests nuevos (`identity/test_auth_audit01.py`)

| Grupo / fuente | Casos ejecutados y esperado confirmado | Límite |
|---|---|---|
| AUTH-01 CA1 | Tres roles activos, correo con espacios exteriores (incluidos espacios Unicode `\u00a0` y tabuladores) y mayúsculas, sesión persistida con identidad/rol, ausencia de contraseña enviada en sesión | Solo fixtures ficticios y SQLite |
| AUTH-01 CA2/CA3 | Clave errónea, inexistente e inactiva: mismo literal general, sin identidad de sesión ni modificación de cuentas | Sin análisis estadístico de tiempos |
| AUTH-02 CA1 / RN-17 | Fallos 1–4 generales, quinto bloquea hasta T+15 exacto; inactiva/inexistente misma respuesta al quinto | Bloqueo por identificador, no límite global/IP |
| AUTH-02 CA2 | Otra sesión y variante normalizada conservan bloqueo; clave válida o errónea no extienden fecha ni incrementan; minutos redondean hacia arriba en segundos 0,59,60,839,840,899 | Reloj controlado por patch, no espera de 15 minutos real |
| AUTH-02 CA3 | En T+900 acceso válido, contador cero/fila estable; clave incorrecta en T+900 inicia contador en uno; cinco nuevos fallos tras expirar completan un segundo ciclo de bloqueo exacto en T2+15; éxito antes del quinto reinicia consecutividad | No PostgreSQL concurrente |
| Efectos entre cuentas | Bloquear ADMIN no bloquea ALMACENERO/VENDEDOR; una sesión autenticada previamente permanece operativa | Persistencia de sesión previa es comportamiento observado, no nueva HU aceptada |
| Campos y normalización Unicode/IDN | Vacío, solo espacios en correo (`"     "` → error de campo sin tocar `LoginAttempt`) vs solo espacios en contraseña (`"     "` → llega al servicio y suma 1 fallo por `strip=False`); formato inválido; carácter nulo; correo 254/255/319/320/321; parte local no ASCII (`josé@...`, `straße@...`) rechazada por `EmailValidator` sin intento; dominios IDN (`@münchen.invalid`, `@straße.invalid` ↔ `@STRASSE.INVALID`) aceptados y normalizados por `.casefold()`; dominio IDN en Unicode vs punycode (`@xn--mnchen-3ya.invalid`) generan identificadores distintos porque `normalize_email` no aplica IDNA; contraseña con espacios significativos y contraseña larga (>72 bytes, 97 caracteres) verificada sin truncamiento en Argon2; fallo no repuebla password; next escapa HTML | Formulario permite correo hasta 320 mientras Account máximo es 254; no se cambió política de longitudes ni de IDNA |
| CSRF/sesión | Ausente, inválido y origen externo →403, cero LoginAttempt; token válido permite acceso; rotación CSRF y sesión, antigua sesión eliminada; cookie HttpOnly/Lax | No inspección TLS de despliegue |
| Redirección `next` y rutas `identity` / AUTH-01 CA4 | Host externo, URL relativa a esquema, javascript, triple barra o malformada → inicio; HTTPS no permite downgrade; prioridad de `POST["next"]` sobre `GET["next"]` contradictorio, fallback a `GET["next"]` cuando `POST["next"]=""`, y anulación hacia `/inicio/` cuando `POST["next"]` es externo; URL absoluta del mismo host aceptada; `next="/"` redirige a `/` y luego a `/inicio/` sin bucle; `next` a ruta local inexistente (`/ruta-inexistente-aud01/`) redirige y devuelve 404 sin filtrar secretos y conservando sesión activa; sesión ya autenticada en `GET/POST /?next=...` redirige a `/inicio/` ignorando `next`; todas las rutas de `identity/urls.py` (`/inicio/`, `/salir/`, `/empleados/`, `/empleados/nuevo/`, `/empleados/<uuid>/editar/`, `/empleados/<uuid>/estado/`) redirigen visitante a `/?next=...`, deniegan con 403 a `ALMACENERO`/`VENDEDOR` sin mutar cuentas ni filtrar correos inactivos, y rechazan métodos no permitidos con 405 | No se afirma auditoría funcional de las operaciones de empleados (etapa 02) ni de los demás módulos |
| Superficie `/admin/login/` | Rechazo `200` sin sesión ni `LoginAttempt` ante `POST` directo con contraseña válida de `ADMIN`, `ALMACENERO`, `VENDEDOR` no-staff e `inactivo`; rechazo `200` de cuenta `staff` cuando envía correo en mayúsculas/espacios (`ModelBackend` no usa `email_normalized`); cuenta `staff` bloqueada en `/` puede autenticarse en `/admin/login/` y esa sesión accede también a `/` (`302`) e `/inicio/` (`200`), eludiendo el bloqueo comercial | Política de perímetro de `/admin/` pendiente (DOC-01-06 / etapa 15) |
| Petición / almacenamiento | GET no autentica, PUT/DELETE→405; LoginAttempt solo identifier HMAC de 64 caracteres, contador/fechas; rechazo no almacena credenciales | Password sin máximo propio; retención y tráfico pendientes separados |
| Correcciones y filtro de logs | POST vacío, no-store/private, redacción POST y locales con DEBUG=False; `RedactSensitiveDataFilter` redacta claves sensibles en `record.getMessage()` | `RedactSensitiveDataFilter` no formatea ni filtra `record.exc_info`; no es prueba visual ni garantía absoluta de no exposición |

Los 19 métodos existentes añadidos al comando verifican sus propias aserciones de sesión, Argon2, CSRF, menús, rutas por rol y bloqueo. Incluyen un caso de salida y referencias a ventas; ejecutarlos como regresión **no completa las etapas 02/10**.

## Reproducción

Desde la raíz, con `audit01_settings.py` existente, el lanzador reproducible conserva cada log y manifiesto con fecha única:

```powershell
& './r1-pmv/.venv/Scripts/python.exe' './auditoria_por_etapas/resultados/soporte/run_auth01_tests.py'
```

La ejecución ampliada de 01-B [manifiesto](../evidencias/01-auth-tests-20261109-122521-777224.json) / [log](../evidencias/01-auth-tests-20261109-122521-777224.txt) confirmó **53/53 en 10,999 s** (y se conservan los cortes de 01-A de 45/45 en [manifiesto 01-A](../evidencias/01-auth-tests-20261109-115809-570846.json) y [primer corte](../evidencias/01-auth-tests-despues.txt)). Comando equivalente sin captura automática de evidencia:

```powershell
& './r1-pmv/.venv/Scripts/python.exe' -c 'import os,sys; sys.path[:0]=["r1-pmv", "auditoria_por_etapas/resultados/soporte"]; os.environ["DJANGO_SETTINGS_MODULE"]="audit01_settings"; import django; django.setup(); from django.conf import settings; settings.DATABASES["default"]["TEST"]["NAME"]=":memory:"; settings.SESSION_COOKIE_NAME="sessionid"; settings.CSRF_COOKIE_NAME="csrftoken"; from django.core.management import call_command; call_command("test", "identity.test_auth_audit01", "identity.tests.AuthenticationAndAuthorizationTests", "identity.tests.EmployeeEditDeactivateTests.test_login_lock_expires_after_fifteen_minutes", "identity.tests.EmployeeEditDeactivateTests.test_unknown_identifier_has_the_same_lock_response", "identity.tests.EmployeeEditDeactivateTests.test_success_resets_counter_without_deleting_throttle_row", verbosity=2, interactive=False)'
```

No sobrescribir las evidencias históricas al repetir; usar otro nombre con fecha. Las cuatro regresiones iniciales se ejecutaron con los mismos overrides y etiquetas individuales `identity.test_auth_audit01.LoginAudit01Tests.test_empty_post_is_bound_and_reports_both_required_fields`, `test_get_and_failed_post_are_not_cacheable`, `test_exception_filter_redacts_submitted_credentials`, `test_service_exception_filter_redacts_credential_locals` sobre los archivos aún sin corregir.

## Pendientes y decisiones que estas pruebas no resuelven

El servicio calcula el hash antes de rechazar un identificador bloqueado; eso conserva trabajo comparable pero no acota tráfico/CPU. La acumulación de filas por identificadores nuevos, la retención, límites por IP/sesión y `/admin/` son superficies separadas. No se introdujo una política sin requisito decidido. No hubo prueba de carga, ventanas de volumen, carreras PostgreSQL ni evaluación de tiempos. La suite no sustituye el recorrido de navegador exigido por el protocolo, ni demuestra revocación completa por cambio de personal (etapa 02).

