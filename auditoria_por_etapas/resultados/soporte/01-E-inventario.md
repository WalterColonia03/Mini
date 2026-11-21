# Inventario previo a ejecución · 01-E · 14/11/2026 Lima

Primera pasada, revalidación acotada de01 solicitada expresamente; no inicio de segunda pasada global. Fuentes:08 HU-AUTH-01/02, RN-12/17/29, DOC-01-06, DOC-02-04, CT-COHERENCIA-UI;02 §§2.1/2.3/2.7/seguridad;16 DOC-01-06/DOC-02-04;21 seguridad;01/14 contexto R1;07/09/03 vistas derivadas. CONTROL_SPRINTS y tareas S1-AUTH01-UI/SVC/DB/AUTO/MAN/REV son historia, no aceptación actual. XLSX histórico no presente en raíz actual, no usado ni editado. Jira excluido. Sin AGENTS.md encontrados en árbol ni ancestros consultados.

## Requisitos clasificados antes de ejecutar

| ID | Actor / criterio | Clasificación / caso |
|---|---|---|
| AUTH01/CA01 | Tres roles activos, sesión y opciones propias | R1 seleccionado; normalización, éxito y persistencia |
| AUTH01/CA02 | Visitante, clave errónea/inexistente | R1 seleccionado; mensaje uniforme y sin sesión |
| AUTH01/CA03 | Cuenta inactiva | R1 seleccionado; mismo rechazo |
| AUTH01/CA04 | Visitante y roles ajenos | R1 seleccionado; URL/POST, rechazo sin mutación; alcance identity y muestras de destinos |
| AUTH02/CA01 | Quinto fallo consecutivo | R1 seleccionado desde08 vigente; no seguir exclusión histórica de09/11 |
| AUTH02/CA02 | Bloqueada, otra sesión, cualquier clave | R1 seleccionado; plazo y minutos restantes |
| AUTH02/CA03 | Plazo vencido, clave válida | R1 seleccionado; acceso y contador cero |
| RN17 | Identificador normalizado, estado uniforme, contador propio | Ingreso actual; recuperación por correo futura; reset/cambio correo dependencia02 |
| DOC01-06/C01 | admin técnico separado | Aceptado, requiere prueba independiente; no cubierto por login público |
| DOC01-06/C02–03 | Eventos y secretos | Aceptado; inspección y prueba histórica no prueban instrumentación global |
| DOC02-04/C03 | Rename/reactivación/reset y sanción | Dependencia02; no se cierra en01-E |
| CT-COHERENCIA-UI/C01–04 | Inventario, significado, permisos y regresión | Aplicables al login; no aprueba panel ni operaciones |
| AUTH04a/b, AUTH05 y LOG UI | Sesión única/remota/recuperación y bitácora visual | Futuro; ausencia no es defecto de este release |

## Superficie inversa actual

Se conservan IDs E01-R01..10,U01..21,F01..04,P01..09 del [inventario histórico](../anexos/ETAPA-01-superficie.md). Su evidencia antigua se hereda sin aprobación automática. Relectura actual de urls/views/forms/services/models/login/base y pruebas.

| Ruta/acción | Clasificación y alcance |
|---|---|
| GET/POST `/` | AUTH01/02, ingreso y rechazos; GET ignora credenciales, PUT405 |
| GET `/inicio/` | Destino/sesión de tres roles; métricas NO EXAMINADAS en01-E |
| GET/POST `/salir/` | Preparación del recorrido; HU-AUTH03 pertenece a02 |
| GET `/empleados/`, GET/POST `/empleados/nuevo/`, `/empleados/<uuid>/editar/`, POST `/empleados/<uuid>/estado/` | Puertas de autorización identity; CRUD completo pertenece a02 |
| `/admin/`, `/admin/login/`, `/admin/identity/account/` | Superficie técnica DOC01-06/C01, staff/superuser/permisos distintos |
| CSS/favicon/navigation.js | Presentación; no demuestra autorización |

Textos U01..21 se mantienen salvo U06: ahora «Productos, empleados, proveedores y resumen diario de ventas.» (cambio heredado de13, relectura nueva). U04 «Gestión de minimarket» / «Bienvenido. Escribe tu correo y tu contraseña.»; U05 «Cada persona ve solo las operaciones de su puesto: administración, almacén y caja.»; U07 «Inventario, mermas y alertas de stock.»; U08 «Turno de caja y ventas.»; U09 «Acceso seguro» (no certificación); U10 «Iniciar sesión» / «Usa tu cuenta de trabajo para continuar.»; U14 «Tus permisos y acciones dependen del rol asignado.»; U16 «Correo o contraseña incorrectos»; U17 «Demasiados intentos fallidos consecutivos. Inténtelo nuevamente en {minutos} minuto(s).». U01 título «Ingresar — Sistema de gestión», U02 marca «Minimarket / Sistema de gestión», U03 «Saltar al contenido», U15 pie «Minimarket · Sistema de gestión». U18 errores por requerido/formato/longitud/nulo; U19 contenedor role=alert; U20 mensajes flash solo si existe cola; U21 ocultos. Ninguna salida comercial, impresión, descarga, tabla o filtro en login. Éxito es redirección, sin flash propio.

| Campo/salida | Inicial/obligación/tipo/límite | Normalización/error/persistencia |
|---|---|---|
| F01 Correo de trabajo | Vacío, requerido,email; placeholder nombre@empresa.com, username/autofoco; formulario320, Account254 | strip/casefold; sin IDNA canónico; requerido, formato, longitud, nulo; se repuebla escapado, no modifica cuenta; intento HMAC64 |
| F02 Contraseña | Vacía, requerida,password; current-password; placeholder Ingrese su contraseña; sin máximo explícito | strip=False, espacios significativos; no repuebla; hashArgon2/PBKDF2, nunca texto en contador/sesión |
| F03 CSRF | Oculto generado, requerido enPOST | Ausente/alterado/origen ajeno403 antes de mutación; valores excluidos de evidencia |
| F04 next | Oculto condicional, opcional, POST antes queGET, sin límite propio | Escape HTML, host/esquema, HTTPS no downgrade; ruta reautoriza; no dato comercial |
| Minutos | ceil(restante/60), mínimo1 durante bloqueo | Recalcula al enviar, no reloj vivo; vencimiento exacto permite nuevo intento |

Componentes P01..09: normalización Account, HMAC LoginAttempt, contador/plazo/updated_at, transacción+select_for_update, comprobación hash, is_active/rol permitido, AuthenticationResult, login/sesión+last_login y autorización del destino. Son diseño para AUTH01/02/RN17, no HU nuevas. Retener fila estable evita carrera histórica; no demuestra política de retención. PostgreSQL/concurrencia y quince minutos de reloj real no se aprueban por SQLite/reloj controlado.
