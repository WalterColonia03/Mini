# Disposiciones, recomendaciones y decisiones pendientes · Etapa 15 (`15-A`)

- **Fecha:** `2026-11-14` / `2026-11-15` (America/Lima)
- **Pasada:** `Primera pasada`
- **Build auditado:** `7816d3328115cf5aa5bcdd0985fffd795b3ae084` / `f94faec701beaf938f5af06c2de605337f699f87abf83179e0600dbdb9041907` (`216` fuentes auditables git; sin modificaciones de producto en Etapa 15)
- **Planificación `08`:** `69b886a3be2610546c30e9d587c28813e50ad4e79ad644847aa7c20ba50b87e2` (sin modificaciones de Etapa 15)
- **Estado de autorización:** Ninguna propuesta de este documento fue aplicada a `r1-pmv/` ni integrada en `08_Historias_de_Usuario.md`. Todas quedan en **`PROPUESTA · PENDIENTE DE AUTORIZACIÓN`** o clasificadas por falta de hechos del negocio/entorno.

---

## 1. Hallazgos previos verificados como resueltos en el build estabilizado (`f94faec7...`)

Antes del congelamiento del corte ejecutado por Etapa 15, el producto incorporó correcciones en `identity/`, `app_platform/` y `config/` que fueron revalidadas en `SRV15-07` y `SRV15-09`:

| Referencia previa | Comportamiento verificado en `f94faec7...` | Evidencia en Etapa 15 |
|---|---|---|
| Conservación de bloqueo `RN-18` al reactivar / cambiar correo (`DOC-02-04/C-03`) | `identity/services.py::reactivate_employee` ya no reinicia `LoginAttempt` activo; `update_employee` traslada el registro mediante `_carry_login_attempt` al cambiar el correo. | `SRV15-07-doc02-04-lockout-sesiones-y-auditoria` (`ok=true`), `CHK-NAV-02`. |
| Revocación inmediata de sesiones al cambiar clave (`DOC-02-04/C-01`) | `identity/services.py::update_employee` invoca `_delete_account_sessions` al asignar `new_password`, además de la revocación al desactivar en `deactivate_employee` (`_delete_account_sessions`). | `SRV15-07` (`ok=true`), `CHK-NAV-07` (`evictedImmediatelyToLogin: true`). |
| Confirmación intersticial e idempotencia/unlock explícito (`DOC-02-04/C-02,C-04`) | Existe ruta GET `/empleados/<uuid>/estado/confirmar/` (`employee-state-confirm`, `employee_state_confirm.html`) previa al `POST /empleados/<uuid>/estado/` (`employee-deactivate`) y acción `unlock_account` registrada en `IdentityAuditEvent`. | `SRV15-01`, `CHK-NAV-07` (`doc02_04_has_state_confirm: true`). |
| Redacción de excepciones y correlación de petición (`DOC-01-06/C-03`) | `app_platform/logging.py::RedactSensitiveDataFilter` redácta secretos en mensaje y en `exc_info`/`exc_text`; adjunto a `identity.audit` y `django.request` en `config/settings.py`; `identity/middleware.py::RequestIdMiddleware` genera/devuelve `X-Request-ID`. | `SRV15-09-logging-redaccion-exc-info-y-request-id` (`ok=true`), salidas `identity_audit` en navegador. |

---

## 2. Propuestas técnicas y funcionales abiertas (`PROPUESTA`)

| ID | Área | Estado | Propuesta resumida | Riesgo si se posterga | Costo / Alcance |
|---|---|---|---|---|---|
| `PROP-15-SEC-CACHE-01` | Cabeceras HTTP y JSON 403 (`catalog/`) | `PROPUESTA` | Agregar `@never_cache` en 5 vistas de `catalog` y estandarizar respuesta 403/JSON en `product_barcode_check`. | Alto en equipos compartidos (caché de formularios/fichas); bajo en permiso pues el servidor igual responde `403`. | Bajo (`catalog/views.py`, tests). |
| `PROP-15-SEC-LOCK300-01` | Bloqueo por inactividad (`300 s`) y TTL sesión | `PROPUESTA` | Implementar bloqueo por inactividad `HU-VEN-01a` / `RN-22` / `DEC-10` y definir TTL de sesión (`SESSION_SAVE_EVERY_REQUEST` / edad máxima). | Alto en mostrador compartido: ventana de `14` días (`1209600 s`) sin bloqueo automático ante abandono de caja. | Medio (`identity/middleware.py`, `navigation.js`, vista desbloqueo, `08`/`02`). |
| `PROP-15-SEC-ADMIN-01` | Exposición de `/admin/` | `PROPUESTA` | Restringir o deshabilitar `/admin/` en producción comercial, aplicar `RN-18` y protección de sesión separada o impedir puente a `/inicio/`, y bloquear escrituras sin servicios sobre 9 modelos. | Crítico: bypass de bloqueo de 15 min de `RN-18` y mutación directa sin invariantes de dominio ni caja. | Medio (`config/urls.py`, `settings.py`, `admin.py`, `02`). |
| `PROP-15-SEC-LOG500-01` | `request_id` en `500.html` y bitácora durable | `PROPUESTA` | Mostrar `request_id` en `templates/500.html`, configurar sumidero/rotación durable de logs y definir política `DOC-01-05`. | Medio: dificulta soporte en fallos `500` y deja eventos solo en consola/stream en despliegues sin sumidero. | Bajo–Medio (`templates/500.html`, `config/settings.py`, ops). |
| `PROP-15-OPS-COMPOSE-01` | Despliegue, roles PG y respaldo/restauración | `PROPUESTA` | Alinear `Dockerfile` (`python:3.13-slim` vs `3.12`), reemplazar `runserver` en `compose.yaml` por WSGI (ej. Gunicorn), documentar/automatizar `pg_dump`/`pg_restore` con SHA-256 (`S1-OPS-DB-01`) y aclarar dueño `migrator_user` en `db/init/01-create-runtime-roles.sh`. | Crítico para operación real: servidor de desarrollo expuesto sin TLS/workers y ausencia de automatización verificable de backup ante fallos de disco. | Medio (`Dockerfile`, `compose.yaml`, scripts `ops/`, `db/init/`). |
| `PROP-15-OPS-DEMO-01` | Comandos `reset_demo_db` y `seed_demo` | `PROPUESTA` | Ordenar limpieza de `Sale`/`SaleDraft`/`ProtectedError` en `reset_demo_db` y generar `InitialLoadLine` coherente en `seed_demo`. | Bajo en producción, Medio en pruebas/capacitación: `reset_demo_db` falla con ventas previas y Kardex muestra `"No disponible"`. | Bajo (`identity/management/commands/`, `catalog/management/commands/`). |
| `PROP-15-CONC-PG-01` | Bloqueos PG y validación PG 17 | `PROPUESTA` | Homologar `select_for_update(no_key=True)` en bloqueo de actor cuando proceda (`sales._lock_seller_actor`) y ejecutar suite `PG15-01..15` contra **PostgreSQL 17** exacto. | Bajo–Medio: posible contención innecesaria de claves foráneas en alta concurrencia y brecha de versión PG `18.4` vs `17` de `compose.yaml`. | Bajo (`sales/services.py`, entorno Docker/PG 17). |
| `PROP-15-DOC-HIST-01` | Conciliación documental `DEC-12` (`VENDEDOR`) | `PROPUESTA` | Conciliar `08` (`DEC-12/C-02` redactado originalmente con `403` para `/caja/turnos/` y `/ventas/historial/`) con el contrato vigente de `12-B` y `base.html` (`200` filtrado a `seller=request.user` y enlace en sidebar). | Medio documental: discrepancia aparente entre ficha literal `DEC-12/C-02` y menú implementado. | Bajo (documental en `08` y vistas derivadas, sujeto a autorización). |

### Detalle estructurado por propuesta

#### `PROP-15-SEC-CACHE-01` — `@never_cache` en `catalog/` y consistencia de `product_barcode_check`
- **Situación observada:** En `SRV15-01` (`9` combinaciones ruta×método) y `CHK-NAV-03` (`productNewMissingNoStoreHeader: true`), las vistas `category_create`, `product_entry`, `product_created`, `product_created_alias`, `product_edit` y `product_toggle` (`catalog/views.py`) responden sin `Cache-Control: no-store`. Adicionalmente, `product_barcode_check` valida manualmente `request.user.role.code != Role.Code.ADMIN` y responde `JsonResponse` `403` (`"No tiene permiso para esta operación."`) en lugar de compartir decorador estándar.
- **Rol afectado:** `ADMIN` (y usuarios posteriores en el mismo navegador compartido).
- **Necesidad y beneficio:** Evitar reconstrucción de pantallas administrativas sensibles desde historial/caché tras cerrar sesión o cambiar de usuario.
- **Alternativas:** (a) Aplicar `@never_cache` explícito en esas vistas (recomendado); (b) aplicar encabezado global `no-store` mediante middleware para rutas autenticadas.
- **Riesgo, costo e impacto:** Riesgo de implementación mínimo; costo bajo (`catalog/views.py`); mejora `S1-SEC-01` y coherencia con `identity`, `inventory`, `cash` y `sales`.

#### `PROP-15-SEC-LOCK300-01` — Bloqueo de terminal por inactividad (`300 s`) y política de expiración de sesión
- **Situación observada:** En `SRV15-04`, `SESSION_COOKIE_AGE = 1209600` (14 días) y `SESSION_SAVE_EVERY_REQUEST = False`. En navegador (`CHK-NAV-04-05`), `navigationJsHasInactivityLock` devolvió `false` y `navigation.js` no implementa bloqueo automático a `300 s`.
- **Rol afectado:** `VENDEDOR` principalmente (`HU-VEN-01a`, `RN-22`, `DEC-10-BLOQUEO-INACTIVIDAD`), además de puestos compartidos `ADMIN`/`ALMACENERO`.
- **Necesidad y beneficio:** Cumplir la historia R1 seleccionada `HU-VEN-01a` y evitar operaciones no autorizadas en mostrador si un vendedor se aleja sin cerrar sesión, conservando borrador y turno abierto al desbloquear con su clave.
- **Alternativas:** (a) Implementar estado de bloqueo en sesión servidor + temporizador UI (`300 s`) compartido entre pestañas con límite de `5` fallos y revalidación al desbloquear (`DEC-10`); (b) ajustar `SESSION_COOKIE_AGE` por entorno y activar `SESSION_SAVE_EVERY_REQUEST = True`.
- **Riesgo, costo e impacto:** Riesgo alto en mostrador mientras falte; costo medio (backend + JS + tests + navegador).

#### `PROP-15-SEC-ADMIN-01` — Deshabilitación o endurecimiento de `/admin/` en producción comercial
- **Situación observada:** En `config/urls.py`, `/admin/` está montado sin condición de entorno. `SRV15-08`, `CHK-NAV-06` y la captura `04-admin-bypass-en-chrome.png` confirman que: (1) `/admin/login/` autentica mediante `ModelBackend` eludiendo los `5` fallos / `15` min de `LoginAttempt` (`RN-18`) y redirige con sesión válida a `/inicio/`; (2) expone `9` modelos (`auth.Group`, `cash.CashRegister`, `cash.CashShift`, `catalog.Category`, `catalog.Product`, `identity.Account`, `identity.Role`, `inventory.InitialInventoryLoad`, `inventory.Lot`) fuera de los servicios transaccionales.
- **Rol afectado:** Personal técnico con `is_staff`/`is_superuser` y cuentas `ADMIN` con permisos Django Admin.
- **Necesidad y beneficio:** Cumplir `DOC-01-06/C-01` impidiendo elusión de `RN-18` y mutaciones que rompan invariantes contables/stock/último admin.
- **Alternativas:** (a) Montar `/admin/` solo cuando un flag explícito de mantenimiento/entorno esté habilitado (recomendado para PMV comercial), retirar puente o separar cookie de sesión, y hacer los `ModelAdmin` de solo lectura; (b) mantener `/admin/` activo pero reemplazar `AdminSite.login` por autenticación unificada con `LoginAttempt` + bloqueo de escritura.
- **Riesgo, costo e impacto:** Riesgo crítico mientras siga abierto; costo medio.

#### `PROP-15-SEC-LOG500-01` — `request_id` visible en error `500` y sumidero/retención de bitácora
- **Situación observada:** `SRV15-09` comprobó que `templates/500.html` no expone `request_id` (`template_500_has_request_id: false`), aunque `RequestIdMiddleware` ya envía cabecera `X-Request-ID` y `RedactSensitiveDataFilter` redácta secretos en mensaje y traceback (`exc_info`/`exc_text`). Los logs siguen saliendo por consola sin archivo rotativo ni política de retención definida.
- **Rol afectado:** Operación/soporte técnico y los tres roles en errores inesperados (`DOC-01-06/C-02`).
- **Necesidad y beneficio:** Facilitar correlación entre incidente reportado en pantalla e `identity_audit` / logs del servidor, sin filtrar trazas técnicas.
- **Alternativas:** Renderizar `request_id` en vista/plantilla `handler500` y definir `RotatingFileHandler`/syslog + rotación externa al autorizar `DOC-01-05`.
- **Riesgo, costo e impacto:** Costo bajo para `500.html` y medio para infraestructura de logs.

#### `PROP-15-OPS-COMPOSE-01` — Despliegue `Dockerfile`/`compose.yaml`, script de roles PostgreSQL y respaldo/restauración
- **Situación observada:**
  1. `Dockerfile` declara `FROM python:3.13-slim`, distinto de `Python 3.12` especificado en `02_Diseno` (y `3.12.10` del entorno local).
  2. `compose.yaml` arranca Django con `manage.py runserver` y servicio PostgreSQL `postgres:17`, sin servicio reverse proxy HTTPS ni servidor WSGI (`SRV15-13`).
  3. `db/init/01-create-runtime-roles.sh` concede `DEFAULT PRIVILEGES` para tablas creadas por `migrator_user`, lo que exige que toda migración corra como `migrator_user` y no como superusuario (`PG15-14`: `init_sh_default_privileges_require_migrator_owner_finding: true`). Si `migrate` corre como superusuario `postgres`, `app_user` queda sin permisos salvo `GRANT` explícito posterior.
  4. No existen scripts versionados de respaldo ni restauración verificada en el repositorio (`SRV15-13`: `backup_restore_scripts_in_repo: false`), aunque `PG15-15` probó que `pg_dump`/`pg_restore` nativos sobre el esquema actual restauran `26` tablas e invariantes HTTP correctamente cuando existe rol compatible.
- **Rol afectado:** Administrador de sistema / despliegue.
- **Necesidad y beneficio:** Garantizar paso seguro a producción local o VPS con mínimo privilegio, HTTPS (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_*` según `check --deploy` en `SRV15-10`) y recuperación comprobada ante desastres.
- **Alternativas:** Publicar perfil Compose de producción (Gunicorn + `Caddy`/`Nginx` TLS + Python `3.12-slim` + migrador `migrator_user` explícito) acompañado de script `backup_pg.ps1/.sh` y `restore_verify_pg.ps1/.sh` con SHA-256 (`S1-OPS-DB-01`).
- **Riesgo, costo e impacto:** Crítico antes de operar datos reales; costo medio.

#### `PROP-15-OPS-DEMO-01` — Fallos en utilidades `reset_demo_db` y `seed_demo`
- **Situación observada:** `SRV15-11-12` verificó que `reset_demo_db --confirm` falla con `ProtectedError` sobre `Sale.draft` si existen ventas confirmadas en la base, y que `seed_demo` no genera `InitialLoadLine`, causando visualización `"No disponible"` en Kardex de producto (`seed_demo_creates_initial_load_line: false`).
- **Rol afectado:** Soporte / demos / pruebas manuales.
- **Necesidad y beneficio:** Permitir reinicio limpio de ambientes demo sin errores referenciales y con Kardex consistente.
- **Alternativas:** Eliminar `Sale` / `StockAllocation` antes de `SaleDraft` dentro de `reset_demo_db` (mantenido bloqueado fuera de `--confirm` / `DEV/TEST`) y usar servicios de inventario en `seed_demo`.
- **Riesgo, costo e impacto:** Bajo en producción; costo bajo.

#### `PROP-15-CONC-PG-01` — Compatibilidad PostgreSQL 17 y uniformidad de `no_key=True`
- **Situación observada:** Bajo PostgreSQL `18.4` (`PG15-01..15`), los bloqueos `FOR UPDATE` / `FOR NO KEY UPDATE`, muerte de worker HTTP con transacción colgada (`PG15-12`) y caída abrupta `pg_ctl stop -m immediate` (`PG15-13`) pasaron `15/15` sin interbloqueos ni corrupción. Sin embargo, `compose.yaml` declara `postgres:17` (no instalado localmente) y `sales` aún bloquea actor sin `no_key=True` en la ruta de venta comparada con `cash` (`09`).
- **Rol afectado:** `VENDEDOR`, `ALMACENERO`, `ADMIN` bajo concurrencia simultánea.
- **Alternativas:** Ejecutar `ejecutar_pg15.py` sobre instancia aislada de `postgres:17` y evaluar `no_key=True` homogéneo al bloquear actor.

#### `PROP-15-DOC-HIST-01` — Conciliación documental de `DEC-12-PERMISOS-HISTORIAL-Y-MENU`
- **Situación observada:** En el build vigente (`f94faec7...`, heredero de `12-B`), el menú lateral del `VENDEDOR` incluye «Mi historial de ventas» (`/ventas/historial/`) y «Mi historial de turnos» (`/caja/turnos/`), ambos devolviendo HTTP `200` filtrado estrictamente a `seller=request.user` (verificado en `CHK-NAV-04-05` y captura `03-logout-advertencia-borrador.png`), manteniendo `404` al pedir una constancia ajena. En `15-A-inventario.md` (`DEC-12/C-02`), la ficha resumida aludía a `403` para esas rutas según la redacción inicial anterior a `12-B`.
- **Necesidad y beneficio:** Evitar que la segunda pasada clasifique como defecto un comportamiento ya aceptado en `12-B` (o, si el negocio exige `403` estricto en esas dos rutas, autorizar la restricción).

---

## 3. Hechos de negocio y pruebas fuera de alcance local (sin ejecución o pendientes de definición externa)

| Elemento | Clasificación | Motivo y comando/condición pendiente |
|---|---|---|
| PostgreSQL `17` exacto (`compose.yaml`) | `NO EJECUTADO` | El equipo dispone únicamente de PostgreSQL `18.4`; se requiere contenedor/motor `postgres:17` para ejecutar `ejecutar_pg15.py` contra la versión exacta de despliegue. |
| Tráfico HTTPS/TLS real, proxy inverso, `ALLOWED_HOSTS` productivo y alertas `check --deploy` en dominio real (`DOC-01-04`, `S1-SEC-01`) | `NO EJECUTADO` / Pendiente de topología | `check --deploy` (`SRV15-10`) reporta advertencia esperada sobre clave efímera y red HTTP loopback; falta definir si operará en LAN HTTPS autofirmado, túnel TLS o VPS con proxy. |
| Política operativa de respaldo, custodia externa y retención de bitácora/datos (`DOC-01-05`, `S1-OPS-DB-01`) | Pendiente de decisión del negocio | `PG15-15` demostró viabilidad técnica de `pg_dump`/`pg_restore`; faltan frecuencia RPO/RTO, responsable, cifrado de copias y días de retención exigidos. |
| Corte eléctrico/SIGKILL real sobre hardware servidor, concurrencia alta (`PT-CHECKOUT-01`/`PT-SEARCH-01`) y entorno Docker completo | `NO EJECUTADO` | En Etapa 15 se simuló caída abrupta en PostgreSQL (`PG15-13`: `pg_ctl stop -m immediate`) y desconexión abrupta de worker (`PG15-12`); faltan pruebas de carga productiva y daemon Docker activo en el host. |
| Enumeración por tiempo de respuesta (`Argon2` antes del check de bloqueo en `DOC-01-04`) | Abierto / heredado de `01-F` | Mantener evaluación conjunta con Etapa 01 y `DOC-01-04` al autorizar correcciones de seguridad. |
