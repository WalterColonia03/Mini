# ETAPA-15 · Seguridad, concurrencia, despliegue y recuperación

<a id="sublote-15-a"></a>
## Sublote `15-A` · Primera pasada (`14–15/11/2026`, America/Lima)

**PARCIAL en primera pasada dentro del sublote `15-A` (seguridad transversal, control de acceso en servidor/menús, CSRF/sesiones, concurrencia/caída/privilegios/respaldo bajo PostgreSQL 18.4 y artefactos de despliegue).** Todas las comprobaciones se ejecutaron sin modificar `r1-pmv/` ni `08_Historias_de_Usuario.md`, y todas las propuestas identificadas permanecen en estado **`PROPUESTA · PENDIENTE DE AUTORIZACIÓN`**. No se declaran cerradas las etapas `16` o `17` ni se inicia la segunda pasada global.

- **Cursor de entrada:** `15-SEGURIDAD-BASELINE-01`
- **Próximo cursor de Etapa 15:** `15-SEGURIDAD-CORRECCIONES-PENDIENTES` (correcciones autorizadas y brechas de negocio/PG 17)
- **Secuencia global vigente:** `15 → 16 → 17 → 00 → segunda pasada 01–17` (próximo paso global: `16-NORMATIVA-BASELINE-01`)

---

### 1. Identificación de versión, build y conservación de evidencia

| Elemento | Valor verificado en `15-A` |
|---|---|
| Pasada y alcance | `Primera pasada` · `identity`, `config`, servicios transaccionales (`catalog`, `inventory`, `cash`, `sales`), `compose.yaml`, `Dockerfile`, `db/init/01-create-runtime-roles.sh`, documentación de seguridad y `tests` |
| Planificación `08` de entrada (heredada `14-CIERRE`) | `478256e0a373c5ec082b8be98ec82fabacb7943c5f2f5141518529d6dd329219` |
| Planificación `08` ejecutada en los 3 runners (`plan08`) | `69b886a3be2610546c30e9d587c28813e50ad4e79ad644847aa7c20ba50b87e2` (`74` HU, `219` CA base + `60` contratos + `4` J-CA + `4` `CT-COHERENCIA-UI` = `287` criterios y `113` casos escritos) |
| Planificación `08` al cierre del workspace (actualización paralela externa) | `ae58b33fe0a50783b7bd1bae2784fd2ad104022f51ed42f73fef49a67cd6e8f3` (sin ediciones de Etapa 15) |
| `HEAD` (`r1-pmv/.git`) | `7816d3328115cf5aa5bcdd0985fffd795b3ae084` |
| Build inicial de entrada tras `14-CIERRE` | `ef8bc3fa42ebf84377ec8b910f38acee1ecc7e12f0c252a59ab72adbcbccdd65` (`209` fuentes canónicas) / `ec783ac6febb289f70efbda37d7e742ad1305088982ad1e4e6f6694549cdd172` (`203` fuentes runtime) |
| Build auditado en Etapa 15 (`216` fuentes git `.py/.html/.css/.js/.svg/.ps1/.sh`) | `f94faec701beaf938f5af06c2de605337f699f87abf83179e0600dbdb9041907` (`source_stable: true` en servidor, PG 18.4 y navegador; `264` archivos no ignorados en `r1-pmv/` = `0cb9b80f1905c102fb29221a7ea70fa3e05754d347e288863bd3fb2e9f3afb70`) |
| Base operativa `r1-pmv/r1_pmv.sqlite3` | Intacta: `c60b4027d4d2f0953ddcbb828cd6412e9889f9794537de9c50aed7f92fdded58` |
| Entorno aislado ejecutado | SQLite efímera temporal; PostgreSQL `18.4` (`read committed`, clúster efímero detenido, eliminado y puerto cerrado); Chrome real headless (`1366×768`, perfil temporal eliminado y puerto cerrado) |

#### Distinción entre evidencia revalidada y heredada
- **Revalidado íntegramente sobre el build `f94faec7...`:** regresión completa de `652` tests Django, matriz de permisos de rutas/roles/métodos (`232` combinaciones), coherencia menú vs servidor, CSRF en `16` endpoints, cookies/sesiones, Argon2id/`RN-24`, cambios de `02-E` / `DOC-02-04` (preservación de bloqueo al reactivar o cambiar correo, revocación de sesión al cambiar clave, confirmación intersticial, `IdentityAuditEvent`), exposición `/admin/`, redacción en `RedactSensitiveDataFilter` + `X-Request-ID`, `check --deploy`, defectos de comandos demo (`reset_demo_db`/`seed_demo`), artefactos Docker/Compose, `15/15` casos reales de PostgreSQL `18.4` (`pg_blocking_pids`, muerte OS, WAL recovery, roles `app_user`/`migrator_user`, `pg_dump`/`pg_restore`) y `6/6` comprobaciones reales en Chrome.
- **Marcado explícitamente como no reutilizable por cambio de build:** la corrida PG heredada de `14-CIERRE-20261114/postgresql/final/results.json` (`ef8bc3fa...` vs `f94faec7...`) quedó clasificada en `PG15-00` como `HISTORICA_NO_REUTILIZABLE_POR_CAMBIO_DE_BUILD` y reemplazada por los `15` casos ejecutados en `ejecutar_pg15.py`.
- **Heredado sin reejecución específica de Etapa 15:** tiempo de respuesta de Argon2id previo a verificar `LoginAttempt` en `01-F` (`DOC-01-04` permanece abierto en Etapa 01 / `SEC-15`), carga/SLA productivo (`PT-SEARCH-01`/`PT-CHECKOUT-01`) y pruebas sobre **PostgreSQL `17`**.

---

### 2. Inventario bidireccional y disposiciones

- [Inventario bidireccional completo (planificación ↔ comportamiento, rutas y orden de bloqueos)](soporte/15-A-inventario.md)
- [Disposiciones, hallazgos resueltos en `f94faec7...`, propuestas `PROPUESTA` y hechos de negocio pendientes](soporte/15-A-disposiciones.md)

#### Síntesis planificación → comportamiento
| Grupo evaluado | Estado observado | Evidencia principal | Observación |
|---|---|---|---|
| `HU-AUTH-01/02/03`, `RN-12`, `RN-17`, `RN-18`, `RN-24`, `RN-25`, `RN-29`, `RN-30` | **CUMPLE en muestra aislada y PG 18.4** *(en interfaz comercial; `/admin/` excluido)* | `SRV15-01..07`, `PG15-01..06`, `CHK-NAV-01..05,07` | Separación de roles (`403` HTML en acceso cruzado comercial), `302` anónimo, CSRF `403`, rotación/revocación de sesión, Argon2id y bloqueo de `5` fallos / `15` min verificados. |
| `DOC-02-04` (`HU-USR-01..05`, confirmación y bloqueo) | **CUMPLE en muestra** (actualizado en `f94faec7...`) | `SRV15-01`, `SRV15-07`, `CHK-NAV-07` | Confirmación `/empleados/<uuid>/estado/confirmar/`, traslado de `LoginAttempt`, preservación al reactivar, purga inmediata de sesiones al cambiar clave y `IdentityAuditEvent`. |
| `HU-VEN-01a`, `RN-22`, `DEC-10-BLOQUEO-INACTIVIDAD` (bloqueo `300 s`) | **INCUMPLE** *(HU R1 seleccionada sin implementar)* | `SRV15-04`, `CHK-NAV-04-05`, `navigation.js` | `SESSION_COOKIE_AGE = 1209600` (`14` días), `SESSION_SAVE_EVERY_REQUEST = False` y `navigationJsHasInactivityLock: false` (`PROP-15-SEC-LOCK300-01`). |
| `DOC-01-06` (`C-01` `/admin/`, `C-02` bitácora y `500.html`, `C-03` redacción) | **PARCIAL** (`C-01` incumple, `C-02` parcial, `C-03` cumple en sonda) | `SRV15-08`, `SRV15-09`, `CHK-NAV-06`, `04-admin-bypass-en-chrome.png` | `RedactSensitiveDataFilter` redácta `msg`/`args`/`exc_info` y `RequestIdMiddleware` devuelve `X-Request-ID`, pero `/admin/login/` elude `RN-18` y expone `9` modelos + puente a `/inicio/`, `templates/500.html` omite `request_id`, y los eventos salen por consola sin sumidero/retención durable. |
| `S1-SEC-01` / `cache` en vistas (`catalog/`) | **PARCIAL** | `SRV15-01`, `CHK-NAV-03` | `9` combinaciones ruta×método en `catalog/` omiten `Cache-Control: no-store` (`productNewMissingNoStoreHeader: true`); `product_barcode_check` retorna `JsonResponse` `403` inline (`PROP-15-SEC-CACHE-01`). |
| `CT-ROLLBACK-01-POST-ESCRITURA`, `RN-05`, `S1-OPS-DB-02`, `S1-OPS-DB-01` | **CUMPLE en PG 18.4**; **`PARCIAL` en artefactos/versión PG 17** | `PG15-01..15`, `SRV15-13` | Cero deadlocks y recuperación íntegra ante `kill` OS (`PG15-12`), `pg_ctl -m immediate` (`PG15-13`), privilegios `app_user`/`migrator_user` (`PG15-14`) y `pg_dump`/`pg_restore` (`PG15-15`). Faltan prueba en **PG 17**, scripts versionados en repo (`backup_restore_scripts_in_repo: false`), TLS/WSGI en `compose.yaml` (`runserver`) y alineación `Python 3.13-slim` vs `3.12` (`PROP-15-OPS-COMPOSE-01`). |
| `HU-AUTH-04a/04b/05`, `HU-USR-06`, `HU-LOG-01` (`W`) | **FUTURO / NO DISPONIBLE** | Inventario `15-A` | Sin rutas comerciales ni promesas engañosas en UI. |

---

### 3. Evidencia ejecutada y resultados de pruebas

#### 3.1 Suite Servidor ([ejecutar_servidor.py](evidencias/15-A-20261114/servidor/ejecutar_servidor.py) · [resultados JSON](evidencias/15-A-20261114/servidor/resultados-servidor.json) · [log 652 tests](evidencias/15-A-20261114/servidor/regresion-suite.txt)) — **`12/12 OK`**

| Caso | Resultado | Duración | Observaciones verificadas |
|---|---|---|---|
| `SRV15-00-regresion-completa-tests` | `OK` | `176.485 s` | `652/652` tests Django en base desechable (`returncode=0`; log `Ran 652 tests in 172.015s — OK`). |
| `SRV15-01-matriz-rutas-roles-metodos` | `OK` | `12.859 s` | `232` combinaciones; `58` redirecciones `302` anónimo; `96` denegaciones `403`; `5` aislamientos de vendedor; costo oculto en constancia; catálogo/proveedores solo lectura para `ALMACENERO`; detecta `9` combinaciones `catalog/` sin `no-store` y JSON `403` en `product-barcode-check`. |
| `SRV15-02-coherencia-menu-vs-servidor` | `OK` | `0.516 s` | Coherencia de enlaces visibles por rol (`ADMIN`, `ALMACENERO`, `VENDEDOR`) frente a respuesta en servidor. |
| `SRV15-03-csrf-enforcement-transversal` | `OK` | `3.500 s` | `16` endpoints × `3` modos (`missing`, `invalid`, `cross_origin`), `db_unchanged=true`. |
| `SRV15-04-sesiones-cookies-rotacion-y-revocacion` | `OK` | `0.219 s` | Rotación de sesión y token CSRF al autenticar, `HttpOnly`, `SameSite=Lax`, `EXPIRE_AT_BROWSER_CLOSE=True`; evidencia `SESSION_COOKIE_AGE=1209600` y `SESSION_SAVE_EVERY_REQUEST=False`. |
| `SRV15-05-06-argon2id-rn24-y-limite-email-login` | `OK` | `0.000 s` | `primary_hasher="argon2"`, `max_length=254` en formularios de ingreso/alta y validación `RN-24`. |
| `SRV15-07-doc02-04-lockout-sesiones-y-auditoria` | `OK` | `0.343 s` | Conservación de bloqueo en reactivación y cambio de correo, desbloqueo explícito, purga de sesiones al cambiar clave y emisión de `IdentityAuditEvent`. |
| `SRV15-08-admin-exposicion-y-puente-sesion` | `OK` | `0.594 s` | Confirma `/admin/` activo (`9` modelos registrados), bypass de bloqueo `RN-18` por `/admin/login/` y puente de sesión hacia `/inicio/`. |
| `SRV15-09-logging-redaccion-exc-info-y-request-id` | `OK` | `0.000 s` | Redacción en `msg`/`args`/`exc_info`, eco de `X-Request-ID`, hallazgo **`template_500_has_request_id=false`**. |
| `SRV15-10-check-deploy-por-ambiente` | `OK` | `4.516 s` | `check --deploy` `returncode=0` en `local_default`, `demo_ssl_true` y `production_default` (con advertencias `security.W009` esperadas por clave efímera y `security.W004` en local sin HSTS). |
| `SRV15-11-12-defectos-reset-demo-db-y-seed-demo` | `OK` | `0.437 s` | Confirma `ProtectedError` en `reset_demo_db` con ventas (`Sale.draft`) y `seed_demo_creates_initial_load_line=false`. |
| `SRV15-13-artefactos-despliegue-compose-dockerfile` | `OK` | `0.000 s` | `Dockerfile` (`python:3.13-slim`, usuario no root, `gunicorn`) vs `Python 3.12` en `02_Diseno`; `compose.yaml` (`postgres:17`, `runserver`); `backup_restore_scripts_in_repo=false`. |

#### 3.2 Suite PostgreSQL 18.4 Aislada ([ejecutar_pg15.py](evidencias/15-A-20261114/postgresql/ejecutar_pg15.py) · [resultados JSON](evidencias/15-A-20261114/postgresql/resultados-pg15.json)) — **`15/15 OK`**

| Caso | Resultado | Duración | Tabla bloqueada / mecanismo observado | Resultado concurrente o de recuperación |
|---|---|---|---|---|
| `PG15-00-contraste-herencia-14-CIERRE` | `OK` | `0.297 s` | Comparativa vs `14-CIERRE` | Marcada `HISTORICA_NO_REUTILIZABLE_POR_CAMBIO_DE_BUILD` (`ef8bc3fa...` vs `f94faec7...`). |
| `PG15-01-login-5to-fallo-vs-clave-correcta` | `OK` | `0.891 s` | `identity_loginattempt` | `failures=5`; ambos hilos devuelven `"bloqueo15"`. |
| `PG15-02-ultimo-admin-desactivacion-mutua` | `OK` | `0.203 s` | `identity_role` | `1` desactivación exitosa, `1` `ValidationError`; `ADMIN` activo conservado. |
| `PG15-03-empleado-correo-duplicado-normalizado` | `OK` | `0.312 s` | `identity_role` | `1` alta exitosa, `1` `ValidationError` por unicidad normalizada (`RN-25`). |
| `PG15-04-desactivar-vendedor-vs-turno-y-cobro` | `OK` | `0.875 s` | `identity_account` | Serializa desactivación frente a apertura de caja (`RN-29`) y cobro. |
| `PG15-05-cambio-rol-vs-caja-y-borrador` | `OK` | `0.563 s` | `identity_account` | Serializa cambio de rol frente a apertura de caja y borrador activo. |
| `PG15-06-logout-descarte-vs-checkout-venta` | `OK` | `0.500 s` | `identity_account` | Descarte serializado frente a `checkout_sale` (`ValidationError` limpio). |
| `PG15-07-08-apertura-y-cierre-caja-concurrentes` | `OK` | `0.297 s` | `cash_cashregister` (`FOR NO KEY UPDATE`) | Turno abierto único preservado; cierre concurrente serializado sin duplicar acta. |
| `PG15-09-dos-ventas-fefo-multilote-y-salecounter` | `OK` | `0.422 s` | `catalog_product` | Dos ventas concurrentes con descuento FEFO exacto y correlativos consecutivos, sin deadlock. |
| `PG15-10-checkout-venta-vs-cambio-precio` | `OK` | `0.828 s` | `catalog_product` | Actualización de precio y cobro serializados (`ValidationError` en conflicto). |
| `PG15-11-carga-inicial-simultanea` | `OK` | `0.250 s` | `catalog_product` | `1` carga inicial exitosa, `1` `ValidationError` (`RN-01`). |
| `PG15-12-muerte-real-proceso-postwrite-y-reintento` | `OK` | `2.515 s` | `kill` OS real sobre worker `idle in transaction` | `26/26` tablas idénticas tras muerte abrupta; reintento idempotente exitoso (`V-00000006`). |
| `PG15-13-caida-abrupta-motor-pg-wal-recovery-y-reintento` | `OK` | `13.109 s` | `pg_ctl stop -m immediate` + WAL recovery | `26/26` tablas intactas; reintento tras reinicio genera recepción `R-00000001`. |
| `PG15-14-privilegios-roles-bd-app-user-vs-ddl` | `OK` | `0.235 s` | Roles BD `app_user` vs `migrator_user` | `app_user` bloqueado en `CREATE/DROP/ALTER TABLE`; evidencia dependencia de dueño `migrator_user` en `01-create-runtime-roles.sh`. |
| `PG15-15-backup-pg-dump-manifiesto-y-pg-restore` | `OK` | `2.079 s` | `pg_dump` custom (`131092 B`) + `pg_restore` | `26/26` tablas restauradas con conteos y digests SHA-256 idénticos ([manifiesto](evidencias/15-A-20261114/postgresql/backup_restore_artifacts/manifest.json)) + `6` smoke HTTP. |

#### 3.3 Suite Navegador Chrome Real ([ejecutar_navegador15.py](evidencias/15-A-20261114/navegador/ejecutar_navegador15.py) · [browser-report JSON](evidencias/15-A-20261114/navegador/browser-report.json)) — **`6/6 OK`**

| Check Chrome (`1366×768`) | Resultado | Duración | Evidencia visual y hallazgos clave |
|---|---|---|---|
| `CHK-NAV-01-anonimo-login-cookies-almacenamiento` | `OK` | `1.248 s` | Login `/` con `no-store`, `localStorage`/`sessionStorage` vacíos, cookie de sesión oculta a JS. |
| `CHK-NAV-02-bloqueo-rn18-5-fallos-en-chrome` | `OK` | `5.541 s` | Al 5.º fallo muestra aviso de `15` min ([captura](evidencias/15-A-20261114/navegador/01-login-bloqueo-15min.png)). |
| `CHK-NAV-03-roles-menus-403-y-cabeceras` | `OK` | `12.252 s` | `HttpOnly` + `SameSite=Lax`, `X-Frame-Options: DENY`, menús por rol (`11` `ADMIN`, `8` `ALMACENERO`), `403` comercial limpio ([captura](evidencias/15-A-20261114/navegador/02-admin-403-ruta-vendedor.png)); confirma falta de `no-store` en `/productos/nuevo/`. |
| `CHK-NAV-04-05-vendedor-borrador-logout-y-ausencia-bloqueo300s` | `OK` | `10.732 s` | Barra `VENDEDOR` con historiales propios (`200`), constancia ajena `404`, advertencia y descarte de borrador en `/salir/` ([captura](evidencias/15-A-20261114/navegador/03-logout-advertencia-borrador.png)); confirma `navigationJsHasInactivityLock: false`. |
| `CHK-NAV-06-admin-bypass-rn18-y-404-amigable` | `OK` | `8.035 s` | Confirma bypass de bloqueo `RN-18` mediante `/admin/login/` y puente de sesión hacia `/inicio/` ([captura](evidencias/15-A-20261114/navegador/04-admin-bypass-en-chrome.png)); `404` comercial amigable sin traza. |
| `CHK-NAV-07-desactivacion-revoca-otra-sesion-en-chrome` | `OK` | `6.552 s` | Flujo en dos pasos `/empleados/<id>/estado/confirmar/` + POST expulsa inmediatamente la sesión paralela al login (`0` errores de consola/página/red). |

---

### 4. Pendientes y criterios para avanzar de `15-A`

1. **Correcciones de seguridad y despliegue pendientes de autorización (`PROPUESTA` en `15-A-disposiciones.md`):**
   - `PROP-15-SEC-ADMIN-01` (cierre de `/admin/login/` / eliminación de bypass `RN-18` y modelos mutables sin servicio),
   - `PROP-15-SEC-LOCK300-01` (`HU-VEN-01a` / `RN-22` bloqueo a `300 s` y política de edad/renovación de sesión),
   - `PROP-15-SEC-CACHE-01` (`@never_cache` en `catalog/` y consistencia de `product_barcode_check`),
   - `PROP-15-SEC-LOG500-01` (`request_id` en `templates/500.html` y sumidero/retención durable de logs),
   - `PROP-15-OPS-COMPOSE-01` (alineación `Python 3.12` vs `3.13-slim`, reemplazo de `runserver` por WSGI/TLS, automatización de backup/restauración con SHA-256 y aclaración de `migrator_user`),
   - `PROP-15-OPS-DEMO-01` (`reset_demo_db` y `seed_demo`), `PROP-15-CONC-PG-01` y `PROP-15-DOC-HIST-01`.
2. **Validaciones externas no ejecutadas localmente:** prueba completa de `ejecutar_pg15.py` sobre **`postgres:17`** (versión declarada en `compose.yaml`), tráfico HTTPS real detrás de proxy inverso (`DOC-01-04`), definición de política de retención/backup por parte del negocio (`DOC-01-05`), carga productiva (`PT-SEARCH-01`/`PT-CHECKOUT-01`) y corte eléctrico real.
3. **Siguiente etapa global del calendario:** iniciar Etapa **16** (`16-NORMATIVA-BASELINE-01`) en primera pasada antes de Etapa **17**, manteniendo bloqueada la modificación de `r1-pmv/` y `08_Historias_de_Usuario.md` para Etapa 15 hasta recibir autorización expresa del usuario.
