<a id="vigente-02-e"></a>

# Continuación 02-E · 14/11/2026 Lima (Segunda pasada acotada · sesión, personal y eventos)

> **Fuente funcional principal:** [08 · planificación unificada](../../08_Historias_de_Usuario.md). Las fichas, RN y contratos de08 definen lo esperado; este informe registra la segunda pasada acotada de Etapa 02 (`identity`, `/empleados/*`, `/salir/` y coordinación `cash`/`sales`) y conserva íntegramente las adendas e informes previos debajo de esta sección. Las vistas `07`/`09`/`03` se regeneraron desde `08`.

- **Pasada, sublote y build:** Segunda pasada acotada (`02-E`, 14/11/2026) respecto al corte inicial [build-antes.json](evidencias/02-E-20261114/build-antes.json) (`260` archivos en `r1-pmv`, SHA-256 `bd948897...`) y [08-antes.md](evidencias/02-E-20261114/08-antes.md), con inventario final en [build-final.json](evidencias/02-E-20261114/build-final.json). La base protegida `r1-pmv/r1_pmv.sqlite3` permaneció inalterada (`c60b4027d4d2f0953ddcbb828cd6412e9889f9794537de9c50aed7f92fdded58`).
- **Alcance y roles:** Tres roles (`ADMIN`, `VENDEDOR`, `ALMACENERO`) más visitante anónimo; `HU-AUTH-03`, `HU-USR-01..05`, `DOC-02-04/C-01..04`, `DOC-01-06/C-02..03`, `RN-12/17/24/29/30`, `CT-COHERENCIA-UI` y coordinación con `CashShift` / `SaleDraft`. Las historias futuras `HU-AUTH-04a/04b/05`, `HU-USR-06` y `HU-LOG-01` (`W`) continúan explícitamente **`FUTURO / NO DISPONIBLE`**.

## Resumen de hallazgos diagnósticos y correcciones autorizadas (`H02E-01..04`)

| ID | Contrato | Diagnóstico previo ([diagnostico-antes.json](evidencias/02-E-20261114/diagnostico-antes.json)) | Cambio aplicado / resultado verificado en `02-E` |
|---|---|---|---|
| `H02E-01` | `HU-AUTH-03/CA-01..03`, `DOC-02-04/C-04` | `logout_view` y `logout_confirm.html` ya distinguían turno `OPEN`, borrador y roles sin caja; faltaba revalidación visual completa y evento atómico. | **Revalidado (CUMPLE en muestra):** textos condicionales comprobados en `ADMIN`, `ALMACENERO` y `VENDEDOR` (con/sin turno y borrador); cancelar conserva sesión y borrador; confirmar descarta a `SaleDraft.Status.DISCARDED`, preserva `CashShift.Status.OPEN` y emite `LOGOUT_SUCCESS` en transacción atómica (SQLite y PG `18.4`). |
| `H02E-02` | `HU-USR-04/CA-01`, `HU-USR-05/CA-01`, `DOC-02-04/C-02` | `list_posts_directly_to_estado: true`, `has_confirm_url_in_urls: false`, `GET /estado/` `405`. | **IMPLEMENTADO Y VERIFICADO:** [urls.py](../../r1-pmv/identity/urls.py), [views.py](../../r1-pmv/identity/views.py), [employee_list.html](../../r1-pmv/identity/templates/identity/employee_list.html) y [employee_state_confirm.html](../../r1-pmv/identity/templates/identity/employee_state_confirm.html) incorporan `GET /empleados/<uuid:account_id>/estado/confirmar/` (`employee-state-confirm`, solo `ADMIN`) con identidad, rol, estado actual/destino y advertencias reales (sesiones, historial, bloqueo vigente, turno `OPEN`, autodesactivación). En inspección visual móvil (`390×844`) se corrigió el desbordamiento de `.summary-list` en [app.css](../../r1-pmv/identity/static/identity/app.css). |
| `H02E-03` | `DOC-02-04/C-03`, `RN-17`, `HU-USR-03`, `HU-USR-05` | `reactivate_wiped_failures: true`, `email_rename_wiped_old_lockout: true`, `sessions_count_after_pwd_reset_still_persisted: 2`, `edit_form_has_unlock_field: false`. | **IMPLEMENTADO Y VERIFICADO:** [services.py](../../r1-pmv/identity/services.py), [forms.py](../../r1-pmv/identity/forms.py) y [employee_edit.html](../../r1-pmv/identity/templates/identity/employee_edit.html) conservan `LoginAttempt` en reactivación y cambio de correo (`_migrate_or_preserve_login_attempt`), purgan sesiones en BD (`_delete_account_sessions`) tras `new_password`, y agregan casilla explícita `unlock_account` auditada con `ACCOUNT_UNLOCKED`. |
| `H02E-04` | `DOC-01-06/C-02..03`, `02:244,321-323` | `has_identity_audit_model: false`, `captured_identity_audit_records: 0`; tracebacks sin sanitizar en `permission_denied`. | **IMPLEMENTADO Y VERIFICADO en superficie comercial (`DOC-01-06/C-02` sigue `PARCIAL` global):** [models.py](../../r1-pmv/identity/models.py), [0006_identityauditevent.py](../../r1-pmv/identity/migrations/0006_identityauditevent.py), [audit.py](../../r1-pmv/identity/audit.py), [middleware.py](../../r1-pmv/identity/middleware.py), [authorization.py](../../r1-pmv/identity/authorization.py), [logging.py](../../r1-pmv/app_platform/logging.py) y [settings.py](../../r1-pmv/config/settings.py) incorporan `IdentityAuditEvent`, `RequestIdMiddleware` y logger `identity.audit`. Rechazos HTTP usan `persist_db=False` (sin mutar BD en `403`/revocación) y el patrón `_SENSITIVE_KEY_RE` se ajustó para no redactar `"sessions_revoked": true`. |

## Resultados reproducibles finales (pos-edición)

| Verificación | Comando / script | Resultado exacto observado | Límites |
|---|---|---|---|
| Servidor e integración completa (`SQLite :memory:`) | `& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit02e_server.py'` | `check` (`0`), `makemigrations --check --dry-run` (`0`, `No changes detected`), suite completa **`652/652 OK`** en `252.300s` (incluye [test_audit02e_contracts.py](../../r1-pmv/identity/test_audit02e_contracts.py)); `r1_pmv.sqlite3` intacta. | Motor SQLite en memoria; no prueba `PG 17` ni sumidero externo. ([INFORME](evidencias/02-E-20261114/servidor/INFORME.md), [resumen.json](evidencias/02-E-20261114/servidor/resumen.json)) |
| Navegador real Chrome (`1366×768` + `390×844` + multicontexto) | `& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit02e_browser.py'` | `all_passed: true`, **`29/29`** checkpoints + **`10`** acciones auditadas (`audit_actions_present`), `page_errors: 0`, `unexpected_console_errors: 0` (`2` `403` esperados por acceso denegado a `/empleados/`), `server_5xx: 0`, `no_horizontal_overflow: true` (`innerWidth=docScrollWidth`), puerto `63557` cerrado y `9` capturas `.jpg` revisadas. | Muestra en Chrome headless con fixture temporal aislada; excluye lectores físicos. ([INFORME](evidencias/02-E-20261114/navegador/INFORME.md), [resumen.json](evidencias/02-E-20261114/navegador/resumen.json)) |
| Concurrencia y atomicidad PostgreSQL `18.4` (`read committed`) | `& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit02e_pg.py'` | **`5/5` COMPLETE** con `pg_blocking_pids` observado (`last_admin_race`, `duplicate_email_race`, `open_shift_vs_role_change` en `identity_account` `FOR NO KEY UPDATE` vs `FOR UPDATE`, `lockout_preservation_pg` y `logout_atomic_pg` con rollback/commit), `audit_events_total: 13`, puerto `61077` cerrado y cero procesos `audit02e` residuales. | Motor `PostgreSQL 18.4` local en Windows, distinto del objetivo `PostgreSQL 17`. ([INFORME](evidencias/02-E-20261114/postgresql/INFORME.md), [resumen.json](evidencias/02-E-20261114/postgresql/resumen.json)) |

## Cobertura, exclusiones futuras y recomendaciones abiertas

- **Cobertura R1 del sublote `02-E`:** `HU-AUTH-03` (`3/3` CA, `CP-001/002`), `HU-USR-01` (`3/3` CA, `CP-001`), `HU-USR-02` (`4/4` CA, `CP-001/002`), `HU-USR-03` (`3/3` CA, `CP-001/002`), `HU-USR-04` (`3/3` CA, `CP-001`), `HU-USR-05` (`2/2` CA, `CP-001`) verificadas en muestra `02-E`; `DOC-02-04/C-01..04` queda **`EJECUTADO PARCIAL`** por informe IDNA (`PROP-02E-IDNA-01`) y `PG 17`; `DOC-01-06/C-02` permanece **`PARCIAL`** global (superficie comercial cubierta en `02-E`, `/admin/login/` con `0` eventos y sin sumidero durable según `01-F`).
- **Funciones futuras (`W`, NO DISPONIBLES):** `HU-AUTH-04a`, `HU-AUTH-04b`, `HU-AUTH-05`/`RN-18`, `HU-USR-06` y `HU-LOG-01` mantienen `Estado: DISEÑADO — NO EJECUTADO` en [08](../../08_Historias_de_Usuario.md) sin rutas, plantillas ni servicios.
- **Recomendaciones abiertas y detalle de impacto:** Véase [inventario 02-E](soporte/02-E-inventario.md) y [disposiciones y alternativas 02-E](soporte/02-E-disposiciones.md) para análisis completo (Beneficio, Riesgo, Costo, Impacto y Alternativas) de `DOC-02-03` (`display_name` vs nombres/apellidos), `SEC-15-RETENCION-01` / `SEC-15-OBS-01` (retención de `IdentityAuditEvent`/`LoginAttempt`, sumidero externo y paridad `/admin/login/`), `PROP-02E-IDNA-01` (equivalencias Unicode/punycode) y eventual `HU-LOG-01`.
- **Reemplazo frente a primera pasada (`02-D`):** Se superan con evidencia nueva las brechas `E02-LOG-TECH` (en superficie comercial), `E02-REV-06` (confirmación explícita de estado) y `DOC-02-04` (preservación de bloqueo y desbloqueo/reset trazables); permanecen heredados y vigentes los hallazgos globales de Etapa `15` (`SEC-15-ADMIN-01`, `SEC-15-TRAFICO-01`, `SEC-15-RETENCION-01`, `SEC-15-OBS-01`, `PG 17`, `SIGKILL`, cierre de caja vs logout concurrente).
- **Cursor exacto:** Conserva la secuencia global pendiente **`15-SEGURIDAD-BASELINE-01 → 16 → 17 → 00 → segunda pasada`**; dentro de Etapa `02`, el próximo cursor local es **`02-F-IDNA-Y-ETAPA15-SEC-01`**.

---

## Adenda anterior · 12/11/2026

> **Fuente funcional principal:** [08 · planificación unificada](../../08_Historias_de_Usuario.md). Las fichas, RN y contratos de08 definen lo esperado; este documento conserva su papel de contexto, diseño, ejecución o evidencia. Las vistas07/09/03 se derivan de08.


**Estado actual:** Auditado en muestras; contratos revisados pendientes. **Pendientes compartidos:** Reset/desbloqueo auditado, nombre120, confirmación y concurrencia. **Próximo cursor:** DOC-02-04 / SEC-15-CONC-02.

[Mapa consolidado y decisiones](conciliacion_20261112/CONSOLIDACION.md) · [Contratos de implementación](conciliacion_20261112/ENCARGOS.md) · [Verificación integrada](conciliacion_20261112/VERIFICACION.md) · [Informe original íntegro](conciliacion_20261112/BASELINE/auditoria_por_etapas/resultados/ETAPA-02.md).

Las decisiones nuevas se aceptan desde12/11 por delegación explícita del usuario. No se cambia el resultado histórico de una muestra ni se declara cerrado el módulo. Requisitos recién revisados requieren nueva implementación/verificación. Las referencias de línea del texto histórico remiten a BASELINE. Los anexos conservan su fecha y vigencia original; los estados actuales se consultan en el mapa.

## Rectificaciones transversales aplicables

Etapa09 sí tiene ejecución/evidencia (Chrome67funcionales+1control), aunque10–12 y estado general antiguos la dejaban pendiente. 04-D acredita revocación en sus muestras; su límite raw sin petición/servicio permanece. El fallo `_state.adding` de inventario fue corregido05-L e incluido en434tests actuales. Los informes antiguos que lo separaban no prueban fallo actual. El empate de orden de turnos no se considera corregido por repetir una corrida. Soporte12PG es DjangoClient concurrente contraPG, no redHTTP por sockets. 05-Linterrupción antes de escribir no prueba caída postwrite. HU-VEN-05b pide filtrosCA02 y detalleCA03; no hay conflicto de líneas expandidas.

---

## Informe y resultados históricos conservados

# Etapa 02 · Sesión y personal

Actualizado **09/11/2026, America/Lima. AUDITORÍA COMPLETADA CON HALLAZGOS Y DECISIONES ABIERTOS · cierre 02-D.** Se completaron los sublotes de salida, empleados, concurrencia y conciliación. Esto permite continuar etapa03; no declara cumplimiento total de identity, cash, sales ni del sistema. **15 CA CUMPLE en la muestra, 3 PARCIAL por decisiones de contrato y 15 PREVISTO/FUTURO**. La ausencia de eventos técnicos de acceso sigue siendo un incumplimiento abierto distinto de LOG01 futuro.

## 1. Alcance, procedencia y fuentes

Se aplicó completo el [protocolo](../PROTOCOLO_COMUN.md). Alcance: AUTH03/04a/04b/05, USR01..06 y LOG01, ADMIN/VENDEDOR/ALMACENERO; conexión identidad→caja/venta solo para sesiones, autorización e integridad. Inventario previo a ejecución: once HU,33 CA (18 actuales,15 futuros). No se modificaron HU históricas ni Sprint para fabricar aceptación. XLSX histórico inventariado en00, sin editar ni usar sus estados como prueba: [fuentes](anexos/ETAPA-00-fuentes.md).

Fuentes: `21:7–15,21–31,42–44`; `01:91–103,116–134`; `07:165–170,215–228,277–281,333–360`; `08:36–153,869,877`; `09:46–47,76–78,118–124`; `02:80–95,244,250–279,321–323`; `03:65–71,277–307`; `14:75,95`; `16:89–98`; `r1-pmv/CONTROL_SPRINTS.md:20,44–45,58–59`. Los prefijos numéricos identifican documentos de la raíz; símbolos de código permiten resolver líneas desplazadas. Contrato lógico /logout implementado como /salir/.

**Sí:02-A trabajó sobre los archivos guardados con FIX-E02-01..07 y test_etapa02_audit.py, no sobre baseline-identity.** El [baseline original](evidencias/02-A-20261109T231223297870Z/baseline.json) registra fuentes de trabajo, cambios Git y bases; la regresión original ejecutó los once tests preexistentes. Los anexos planificación/superficie y scripts audit02* ya existían; se inspeccionaron, conciliaron conteos33/18/15, referencias XLSX y afirmaciones de evidencia. Se separó inspección de prueba nueva y no se atribuyeron esos arreglos a02-A. El [informe original conservado](evidencias/ETAPA-02-corte-02-A.md) es un corte histórico (sus rutas relativas eran desde resultados, no desde evidencias). La [copia del anexo previo](evidencias/02-A-20261109T231223297870Z/planificacion-pre-reconciliacion.md) conserva su contenido anterior. La autoría, comportamiento del botón de otro IDE y causalidad de una reescritura no se demuestran solo por timestamps; `Argon auditoria 02.md` es una fuente contrastada, no una garantía independiente.

El verificador de02-A registró57 enlaces locales sin faltantes en aquel corte. Posteriormente09_Product_Backlog tenía enlace a un cierre inexistente; eso no invalida retroactivamente el resultado ni acredita quién lo reescribió. Se corrigió durante02-B y ahora se actualiza el complemento con el cierre real. El nuevo cierre verifica enlaces actuales sin sobrescribir closure-verified.json histórico.

## 2. Inventario y trazabilidad

[Matriz individual de33 CA](anexos/ETAPA-02-criterios.md) · [JSON](anexos/ETAPA-02-criterios.json) · [Planificación, RN y tareas](anexos/ETAPA-02-planificacion.md) · [Superficie inversa](anexos/ETAPA-02-superficie.md) · [Futuros y propuestas Dado/Cuando/Entonces](anexos/ETAPA-02-futuro-y-propuestas.md).

| HU | CA | Clasificación y resultado |
|---|---:|---|
| AUTH03 |3| R1 seleccionado; CUMPLE muestra secuencial con/sin borrador/turno, cancelar/confirmar, tres roles, Atrás y accesos directos |
| USR01 |3| Adicional implementado; CUMPLE muestra lista, búsqueda, estados |
| USR02 |4| Adicional implementado; CUMPLE muestra alta, duplicado, validación, confirmación e ingreso nuevo |
| USR03 |3| CA02/03 CUMPLE muestra; CA01 PARCIAL: nombre completo frente a nombres/apellidos |
| USR04 |3| CA02/03 CUMPLE muestra; CA01 PARCIAL por interpretación de confirmación, aunque desactivación/revocación probadas |
| USR05 |2| CA02 CUMPLE muestra; CA01 PARCIAL por interpretación de confirmación; reactivación/ingreso probados |
| AUTH04a/04b/05, USR06, LOG01 |15| PREVISTO/FUTURO: sesión única, descarte por reemplazo, correo/código, cierre remoto independiente y bitácora consultable no disponibles |

Inventario inverso:13 grupos de rutas,26 UI,12 entradas/controles,8 decisiones de persistencia; el cierre añade acción explícita F12 y coordinación transaccional P08. R01–02/U01,U03–08/P01 cubiertos por02-A; R03–08/U02,U09–24/F02–12/P03–08 por02-B, fronteras y PostgreSQL; R09–12/P02 por efectos entre roles; R13 con403 en navegador y errores de recurso en pruebas de servidor, sin afirmar recorrido de toda página404. No hay exportación/impresión específica de empleados/salida.

RN12/24: normalización, duplicado y clave; RN29: permisos de servidor; RN30: salida conserva turno; RN17: comportamiento administrativo de desbloqueo observado pero política pendiente; RN18: recuperación futura. S1-AUTH03-UI/SVC/AUTO/MAN tiene evidencia local; CI y revisión humana independiente NO EJECUTADAS. Las tareas históricas no se cierran automáticamente por esta auditoría.

## 3. Entorno y resultados reproducibles

Windows, Python .venv, Django/SQLite de prueba; Chrome real headless1366×768 con contextos independientes (dos en02-A,cinco en02-B). No representa dos motores ni dos equipos. Bases nuevas por corrida, credenciales ficticias, sin .env real, servidor loopback validado por HMAC antes del ingreso. No se ejecutaron scripts antiguos con prepare --reset. Original y bases previas conservadas por SHA256; servicios de prueba detenidos.

| Lote | Evidencia | Resultado y límite |
|---|---|---|
|02-A original|[browser](evidencias/02-A-20261109T231223297870Z/browser.json), [89 métodos](evidencias/02-revalidacion-20261109T231223296324Z.json)|31 aserciones+1 observación; no inventar32 aserciones históricas. Corrección de sondeo de cierre conservada en closure-verified histórico |
|02-A final tras correcciones|[browser](evidencias/02-A-20261109T235435476251Z/browser.json), [cierre](evidencias/02-A-20261109T235435476251Z/closure.json)|32/32 comprobaciones; cancelación, revocación, turno propio/ajeno, tres roles. Puerto52301 cerrado y siete bases protegidas iguales |
|02-B empleados|[anexo de escenarios](anexos/ETAPA-02-B-navegador.md), [browser final](evidencias/02-B-20261109T235313324286Z/browser.json), [cierre](evidencias/02-B-20261109T235313324286Z/closure.json)|20/20 aserciones; menú→lista/alta/edición/rol/estado; ingreso nuevo y sesiones existentes, roles prohibidos, errores accesibles DOM. Puerto62274 cerrado |
|Reenvío estado|[antes](evidencias/02b-estado-antes-20261109T234721439614Z.json), [después](evidencias/02b-estado-despues-20261109T234758228261Z.json)|Fallo reproducido,6/6 métodos después; B11 confirma formulario antiguo no reactiva |
|Atomicidad logout|[antes](evidencias/02-revalidacion-20261109T235125136023Z.json), [después](evidencias/02-revalidacion-20261109T235142601148Z.json)|Antes1 fallo; después2/2, fallo inducido tras eliminar sesión restaura borrador/líneas/sesión; turno/stock conservados. SQLite, no concurrencia comercial |
|Fronteras|[9 métodos](evidencias/02-revalidacion-20261109T235233158090Z.json)|Vacíos, POST alterado, nombre120/121, correo254/255, duplicado activo/inactivo normalizado, rol inválido, clave opcional, dos sesiones invalidadas por cambio de clave, CSRF/roles, contraseña no repoblada y asociaciones de error |
|Historial|[1 método](evidencias/02-revalidacion-20261109T235428402509Z-a2bca7829e84.json)|Venta/líneas/cierre/acta/carga/lote/responsables conservados tras desactivar; consulta ADMIN y stock8. Servicio/cliente Django, no navegador de venta/carga |
|02-C PostgreSQL18.4|[reproducción3](evidencias/02-C-pg-20261109T234807328259Z.json), [verificación6](evidencias/02-C-pg-20261109T235144128048Z.json)|Dos conexiones y espera observada por pg_blocking_pids: último ADMIN, correo duplicado y apertura frente a desactivar/cambiar rol en ambos órdenes.6 escenarios favorables; cluster aislado conservado, puerto56273 cerrado |
|02-D regresión final|[163 métodos y checks](evidencias/02-revalidacion-20261109T235435484826Z-7c6ff184eb0b.json)|163/163,0 fallos; check y makemigrations --check --dry-run aprobados; SQLite memoria, bases protegidas iguales. No es toda la suite del proyecto |

Reproducir desde raíz (cada navegador crea otra base y preserva anteriores):

```powershell
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/inventario_etapa02.py'
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/run_etapa02_final.py'
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit02a_run.py' run
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/audit02b_run.py' run
& 'r1-pmv/.venv/Scripts/python.exe' 'auditoria_por_etapas/resultados/soporte/concurrencia_pg_02.py'
```

El soporte PG exige binarios PostgreSQL locales y crea cluster nuevo; --reproduce solo corresponde al código anterior y no es verificación de la versión corregida. El runner de regresión añade sufijo aleatorio para evitar colisión de nombres en ejecuciones simultáneas. La corrida162 anterior no sustituye la final163.

## 4. Defectos corregidos en02-B/C y comprobación

| ID / prioridad | Antes → después, ubicación y evidencia |
|---|---|
|E02-REV-01 P1|POST estado alternaba la cuenta; reenvío antiguo podía reactivar. Ahora employee_deactivate + employee_list.html envían action desactivar/reactivar explícita e idempotente; ausente/inválida/repetida400, CSRF403, otro rol403. Formulario guardado antes del cambio exige recarga.6 tests y B11 |
|E02-REV-02 P1|Carrera de correo podía propagar IntegrityError. create/update_employee serializan mutaciones y convierten conflicto con savepoint en ValidationError; restaura valores en memoria. PG deja una sola cuenta y error controlado |
|E02-REV-03 P1|Dos ADMIN podían desactivarse mutuamente y dejar cero activos. Servicios bloquean fila compartida Role ADMIN y recargan actor/objetivo; actor desactivado ya no puede mutar. PG conserva uno activo; test antiguo que usaba actor inactivo ajustado para exigir rechazo |
|E02-REV-04 P1|Abrir turno competía con desactivación/cambio de rol. cash.open_cash_shift bloquea y recarga Account antes de caja y valida vendedor activo; servicios identity comparten bloqueo de cuenta. PG prueba ambos órdenes para estado/rol, sin turno de inactivo/almacenero |
|E02-ATOMIC-01 P1|Descarte y eliminación de sesión no compartían transacción. logout_view ahora transaction.atomic para ambos con backend DB.2 tests incluido rollback después de borrar sesión; falta registro técnico del evento |
|E02-UI-01 P2|aria-describedby apuntaba a errores/ayudas inexistentes. employee_form/edit añaden ids de formulario y role=alert. B04A/B10A finales y regresión; no ensayo de lector de pantalla |

Los cambios funcionales nuevos son acotados a identity y bloqueo de apertura en cash; se preservó el amplio árbol Git preexistente. No atribuir todo git diff a02. No se requirió migración. Los FIX-E02-01..07 anteriores siguen siendo procedencia histórica; ahora hay modificaciones posteriores en algunos de esos archivos, por lo que su hash actual no debe igualarse al baseline de02-A.

## 5. Hallazgos abiertos, propuestas y destinos

| ID / estado / prioridad | Decisión o trabajo pendiente y destino |
|---|---|
|E02-LOG-TECH INCUMPLE aplicación / P2|02:244,321–323 exige evento de salida atómico y logs mínimos de ingreso/rechazo/salida. No hay emisor explícito en aplicación inspeccionada. Un filtro de redacción no es instrumentación. Despliegue NO EXAMINADO. SEC-15-OBS-02: definir persistencia transaccional/entrega fiable, campos sin secretos, fallo de registro y retención; elegir diseño antes de afirmar atomicidad evento+sesión. LOG01 futuro no excusa este requisito actual |
|DOC-02-03 PARCIAL P2|Nombre completo120 frente a nombres/apellidos. Mantener campo único con aceptación explícita del contrato o separar con migración; CA03/01 sigue parcial |
|E02-REV-06 PARCIAL P2|USR04/01 y05/01 dicen confirmar. Botón directo identificado puede constituir confirmación o requerirse segundo paso; decisión de alcance pendiente, no se inventó modal ni se aprobó interpretación silenciosa |
|DOC-02-04 / BLOQUEO EXTRA SIN REQUISITO P2|Cambio administrativo de clave y limpieza de LoginAttempt al reactivar/cambiar correo/clave. Elegir mantener plazo o autorizar desbloqueo trazable; PROP-E02-CA-03. No es recuperación por correo |
|DOC-02-05 PARCIAL editorial P3|Texto del vendedor sin turno presupone turno abierto; definir texto condicional. PROP-E02-CA-01 |
|SEC-15-CONC-02 NO EJECUTADO P1|Logout vs cobro/alta de línea; login vs desactivación/reactivación en vuelo; escrituras por Django admin o fuera de servicios. Locks probados no protegen automáticamente todos esos caminos. Integrar etapas09–11/15 |
|SEC-15-LIMITES-02 NO EJECUTADO P2|Búsqueda Unicode avanzada/longitud extrema, IDNA, volumen/latencia, motores/dispositivos, lector de pantalla, despliegue/CI. Política internacional heredada de01 |
|HIST-12/14 NO EJECUTADO P2|Conservación de todos los tipos de historial, bajas/ajustes y cadena íntegra; muestra venta/carga/turno no aprueba módulos08/12/14 |

Propuestas siguen PROPUESTO, sin duplicar HU: PROP-E02-CA-01..03, PROP-E02-HU-01..04 y PROP-E01-HU-01; tareas/pruebas PROP-E02-PR-01..03. El [anexo futuro](anexos/ETAPA-02-futuro-y-propuestas.md) contiene actor, precondiciones, entradas/límites, errores, permisos, efectos, dependencias y alternativas. No se implementaron sesión única, correo/código, cierre remoto independiente ni bitácora de accesos. No hay fundamento para coincidencia100%.

## 6. Cierre y cursor

02-A final conserva lote20, borrador descartado sin líneas, turno cerrado por su dueño después de probar que salir lo dejaba abierto, cero ventas y sesiones.02-B final conserva seis cuentas ficticias, lote20, turno cerrado/acta, cero ventas y cuatro sesiones ficticias (contextos cerrados, sin simular logout final); el servidor está detenido. Bases y cluster aislados se retienen como evidencia, sin limpieza destructiva. [Verificación final de archivos y entorno](evidencias/02-D-cierre-final.json).

**Próximo cursor: ETAPA-03 / HU-CAT-01/CA-01,08:166, ADMIN → menú de catálogo → GET /productos/categorias/.** Leer protocolo, estado general y [traspaso](anexos/ETAPA-02-cierre-y-traspaso.md); crear datos aislados nuevos, resolver por ID la ubicación vigente y registrar conflictos DOC-00-04/14. Las decisiones de02 continúan abiertas en sus destinos; etapas03–17 no se declaran auditadas por este cierre.
