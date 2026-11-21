# Adenda vigente de ETAPA-01 · 14/11/2026 · 01-E

<a id="vigente-01-e"></a>

**Primera pasada, revalidación acotada solicitada de ingreso y bloqueo. Sublote01-E terminado; etapa01 PARCIAL con seguridad transversal abierta.** No se inicia la segunda pasada global:15–17 permanecen pendientes y00 debe precederla. El encargo actual de01 prevalece para este sublote sin alterar esa secuencia ni cerrar otros módulos.

**Cursor exacto: `01-F-ADMIN-PERIMETRO-01`.** Partir de la matriz y build01-E; definir/verificar canal técnico permitido frente a entrada comercial, probar staff y superuser ficticios con bloqueo activo y sesión compartida, antes de considerar cubierto DOC-01-06/C-01. Si falta configuración del despliegue, conservar alternativas y avanzar independientemente con SEC-15-TRAFICO-01/SEC-15-RETENCION-01/SEC-15-OBS-01; no elegir presupuesto ni plazo sin hechos. Cursor general15-SEGURIDAD-BASELINE-01 permanece vigente para la secuencia global.

## 01-E.1 Línea base, alcance y conservación

Lectura completa de PROTOCOLO_COMUN y CONTINUIDAD_Y_SEGUNDA_PASADA; consulta del estado vigente posterior a14. Inventario previo [01-E](soporte/01-E-inventario.md), con siete CA de dosHU seleccionadas, RN12/17/29, tareas, contratos, diez grupos de rutas,21elementos de login,4campos y9componentes internos. El inventario histórico se conserva con rectificación de la tarjeta ADMIN: ahora dice «resumen diario de ventas», no «reportes». AUTH02 sí está seleccionada en08 vigente: la exclusión histórica dejó de ser vigente desde la conciliación12/11.

Alcance de producto: login en identity/urls/views/forms/services/models, templates y pruebas. Salida/personal y pantallas de destino se usan como preparación/puertas de acceso, sin certificar sus procesos. Excluidos recuperación por correo, sesión única/remota (futuras), bloqueo de puesto300s, CRUD completo, cifras de panel, negocio con datos previos, concurrenciaPG nueva, carga/latencia, proxy/TLS/despliegue, normativa y operación real. `/admin/`, tráfico, acumulación y eventos se analizan como superficies separadas.

HEAD `7816d3328115cf5aa5bcdd0985fffd795b3ae084`, árbol con cambios previos conservados. Build inicial de209archivos `f693be9de6b3baf8cacbc95e841d18ee5030620fc6e17f29600d08b7be8ea85d`; final `f6b155a933bd3f57684ef1dd4a61a7ba44a2a30ded68a80a46bb4100748ed71a`. Algoritmo y manifiestos por archivo en [runner](soporte/audit01e.py), [antes](evidencias/01-E-20261114/build-before.json) y [final](evidencias/01-E-20261114/build-final.json). No comparar el agregado con builds antiguos de distinto conjunto sin comparar archivos.

08 de entrada SHA256 `478256e0a373c5ec082b8be98ec82fabacb7943c5f2f5141518529d6dd329219`; salida `ff85b85e07872a97fa2d2bef5b49730fb1a6238a3fe2c2867d8ef75e73d5b431`, también en `build-final.json → documents → 08_Historias_de_Usuario.md` y [verificación](evidencias/01-E-20261114/verificacion-final.json). Se preservó la versión previa de08/07/09/03/02/16 y ambos informes en [antes](evidencias/01-E-20261114/antes/ETAPA-01.md). Las secciones anteriores siguen íntegras debajo; no heredan CUMPLE a este build por copia.

## 01-E.2 Entorno y evidencia nueva

Windows, Python3.12.10/Django5.2.18 del entorno existente. `audit01e_settings` bloquea carga de.env y fuerza APP_ENV=test,DEBUG=False. Base nueva exclusiva `auditoria_por_etapas/resultados/datos/01-E-20261114/audit.sqlite3`; migraciones solo allí. Cinco cuentas ficticias finales: tres roles activos no staff, una inactiva y un vendedor con correo254. Claves aleatorias en archivo de datos privado, sin incluirlas en informes/capturas. Probes staff/superuser viven solo en la base efímera de tests. Cookies `audit01e_sessionid` y `audit01e_csrftoken` separadas del uso habitual.

Servidor127.0.0.1:8781 sin autoreload; Brave mediante CUA. Segundo contexto por hostlocalhost, con cookies separadas pero misma base. Un reinicio del proceso durante el cambio de formulario preservó sesiónADMIN y bloqueoALMACENERO. La suite usa SQLite en memoria con nombres de cookies estándar por compatibilidad de pruebas. No conecta a base operativa ni demuestra locksPG.

Servidor de este sublote detenido al finalizar; la base aislada se conserva para evidencia. [Sanitización](evidencias/01-E-20261114/sanitizacion.json):56archivos de evidencia revisados, sin coincidencias de claves de fixtures ni claveDjango; capturas inspeccionadas con campos de contraseña vacíos. No equivale a una auditoría global de secretos del repositorio.

**58/58 pruebas iniciales;120/120 regresión final deidentity y tres probes,33.359s.** Son conjuntos solapados, no178pruebas diferentes. [Inicial](evidencias/01-E-20261114/antes/tests.txt), [final](evidencias/01-E-20261114/identity-regression.txt), [metadatos](evidencias/01-E-20261114/identity-regression.json). Tres probes pasan al demostrar admin alternativo/acumulación/retención: no son aprobaciones de seguridad.

**24 checkpoints de navegador aceptados de28 registros capturados.** [Manifiesto](evidencias/01-E-20261114/browser-manifest.json), [captura final](evidencias/01-E-20261114/login-final.png), [bloqueo](evidencias/01-E-20261114/bloqueo.png). UI01,UI02 inicial,UI07 yUI08 se conservan excluidos por snapshot transitorio/sustituido; usar UI02-confirmado,UI12 yUI20. UI23 es una comprobación adicional no contabilizada: atributo maxlength254 observado, longitud de valor no verificable con lecturaDOM sanitizada (`10` no se interpreta como longitud real ni fallo del producto). No se ocultan estos límites.

Para UI15 se preparó `locked_until=ahora+115s` únicamente en ALMACENERO; para UI16, `ahora−1s`. [Preparación115](evidencias/01-E-20261114/clock-115.json), [expiración](evidencias/01-E-20261114/clock--1.json). No hubo nueva espera real15min. Comparación [ORM antes](evidencias/01-E-20261114/orm-before-expiry.json)/[después](evidencias/01-E-20261114/orm-final.json): fallo5→contador0/plazoNULL, last_login y sesiones persistidos, sin altas/cambios comerciales en tablas vacías. No demuestra preservación de datos comerciales preexistentes.

## 01-E.3 Matriz requisito → ejecución y retorno

T = `identity-regression.txt`; U = checkpoint del manifiesto. CUMPLE se restringe a la muestra secuencial descrita. Inventario principal7/7CA revisados,6/7CUMPLE acotados,1/7PARCIAL. No es aprobación global deAUTH ni seguridad.

| Fuente precisa | Esperado / ubicación | Observado y evidencia nueva | Estado / siguiente acción |
|---|---|---|---|
| 08 AUTH01/CA01; RN12/29 | Correo normalizado, tres roles activos, sesión y opciones; LoginForm→authenticate_active_account→create_server_session | T all_three_roles, unicode_casefold; U09/10ADMIN,13VENDEDOR,16/17ALMACENERO; U22 cuenta254. ADMIN accede a empleados por menú U11. Sesión persiste en recarga/reinicio | CUMPLE muestra / P1; operaciones de destino excluidas |
| AUTH01/CA02 | Clave errónea e inexistente no enumeran | T wrong_unknown_inactive; U04 yU12 mismo «Correo o contraseña incorrectos», sin clave repoblada. U02-confirmado/03/24 validación de campo | CUMPLE muestra / P1; latencia estadística NO EJECUTADA |
| AUTH01/CA03 | Inactiva+clave válida rechaza igual, sin sesión | T yU20; ORM inactiva last_loginNULL,failures1. U08 no acredita este caso | CUMPLE muestra / P1; desactivación concurrente pertenece02/15 |
| AUTH01/CA04; RN29 | Acceso ajeno denegado sin datos/mutación | T identity_routes_authorization_and_method_boundaries y permisos; U14/18VEN/ALM empleados denegados, U19visitante→login, U21next no elude; cuentas conservadas en tests y negocio vacío sin cambios | PARCIAL / P1; matriz completa de rutas/objetos/datos comerciales fuera de este sublote |
| AUTH02/CA01; RN17 | Quinto fallo bloquea900s; uniforme activa/inactiva/inexistente | T fifth_failure_exactly_fifteen_minutes/inactive_unknown; U04,f2,f3,f4 generales;f5 bloqueo15; ORMfailures5 | CUMPLE secuencial / P1; PG nuevo NO EJECUTADO |
| AUTH02/CA02; RN17 | Cualquier clave/otra sesión rechazada; minutos restantes sin ampliar plazo | T locked_shared,minutes_round_up: fronteras0/59/60/839/840/899; U05clave correcta,U06otra cookie normalizada,U15muestra2preparado; no es contador vivo | CUMPLE muestra / P1; no equiparar con límite de tráfico |
| AUTH02/CA03; RN17 | En igualdad900s ingresa y reinicia; error posterior empieza nueva serie | T exact_expiration,second_cycle,success_before_fifth,wrong_after_expiration; U16/17ingreso después de plazo preparado; ORM0,NULL | CUMPLE reloj controlado / P1; ciclo real01-C solo heredado |
| DOC02-04; AUTH01 frontera | Cuenta254 válida,255+rechazo de campo sin intentos | Antes formulario320: T histórico creaba4filas en254/255/319/320. Después T solo1fila; cuenta254autentica, U22 y maxlength254 observado | CORREGIDO y VERIFICADO en muestra / P2; IDNA no corregido ni aprobado |
| Diseño02 sesión/CSRF/next | Escritura CSRF; host/esquema seguro, permisos posteriores | T CSRF ausente/alterado/origen ajeno403 sin contador, rotación sesión/CSRF, flags, escape y no repoblación; next interno/externo/downgrade/prioridad; U21 yU22 | CUMPLE casos T / P1; HTTPS/proxy productivo NO EJECUTADO |
| DOC01-06/C01 | admin fuera de entrada comercial y sin bypass | Probe staff ysuperuser: bloqueados en `/`, entran por `/admin/login/` y alcanzan `/inicio/`; lista Account403staff sin permisos,200superuser. No se concede staff por rol comercial | INCUMPLE aislamiento en endpoint de aplicación probado / P1; perímetro productivo NO EJECUTADO, cursor01-F |
| SEC15TRAFICO/RETENCION | Medir límites y conservación de estado sin invalidarRN17 | 12identificadores desconocidos→12respuestas200 y12filasfailures1; no límite global observado en muestra pequeña. Fila antigua60d permanece tras éxito y pasa a0 | PARCIAL investigación / P1/P2; no prueba de carga, ni ausencia de limitador externo, ni plazo aceptado |
| DOC01-06/C02–03 | Eventos con resultado/requestID y sin secretos inclusoexc_info | Servicio no instrumenta eventos dedicados; LoginAttempt es estado mutable, no bitácora. T valida redacción de mensaje/keys y filtros de excepción Django; no prueba instrumentación de todos los eventos ni destinoexc_info | C02 INCUMPLE instrumentación del login por inspección; C03 PARCIAL / P1; SEC15OBS pendiente |
| CT-COHERENCIA-UI/C01..04 | Textos/promesas trazados y verdad operativa | 21/21elementoslogin trazados estáticamente; campos/mensajes y roles en navegador. U06 rectificado a resumen diario. U20flash sin caso dinámico; cifra/acción comercial no aprobada | PARCIAL transversal / P2; responsive/teclado completo/lector y destinos fuera de muestra |

El sentido inverso se registra en inventario01-E: cada texto, control, campo, ruta y persistencia apunta a AUTH01/02, RN17/29, diseño o dependencia. No se añadenHU para funciones auxiliares. No se encontraron acciones de recuperación, registro libre o sesión única en login; continúan FUTURAS, no defectos actuales.

## 01-E.4 Cambios aceptados, recomendaciones y coherencia

Único cambio funcional propio: `identity/forms.py` explicita254; `identity/test_auth_audit01.py` actualiza frontera conforme al contrato y añade cuenta válida254. [Diff propio](evidencias/01-E-20261114/cambios-propios.diff). Aceptación fundada en DOC02-04 y autorización acotada del encargo, no en recomendación autónoma ni existencia de código. **ACEPTADA→IMPLEMENTADA→VERIFICADA en muestra**. Sin migración, cambio de claves operativas, limpieza, despliegue ni cambio de políticas futuras.

08 incorpora precisión técnica y estados de cuatro casos con evidencia;07/09/03 e índice regenerados (74HU,287criterios,113casos escritos, sin crecimiento artificial).02y16sincronizados.14no requiere nuevo Sprint ni reasignar tareas históricas. [Disposiciones](soporte/01-E-disposiciones.md) contiene beneficio, alternativa, riesgo, costo e impacto para admin, tráfico/NAT, retención, eventos,IDNA, límites de clave yUX. Lo cuantitativo sigue propuesto/investigación; no se acepta por redactarlo.

El validador histórico12/11 retornaFAIL por su guardia de «ningún cambio de producto» frente a su snapshot12/11, incluyendo cambios heredados de13/14. Se conserva [salida](evidencias/01-E-20261114/validacion-documental.txt), sin ocultar ni modificar la guardia para obtener verde. El control específico [validar01e.py](soporte/validar01e.py) verifica estructura/enlaces normativos mediante generador, igualdad de vistas, delta propio de dosarchivos frente a la base real01-E, estabilidad del build y bases protegidas; resultado en verificacion-final.json. No confundir validación documental con ejecución funcional.

## 01-E.5 Reproducción, pendientes y cursor

Desde la raíz, usar `.\r1-pmv\.venv\Scripts\python.exe`:

1. `auditoria_por_etapas/resultados/soporte/audit01e.py tests identity` ejecuta120tests en memoria. No suma a los58iniciales. Los probes documentan defectos esperados.
2. `audit01e.py setup` es solo para base inexistente; se niega a resembrar cuentas existentes. Para repetir navegador en otra sesión preparar otro directorio/settings identificados, sin borrar este.
3. Servidor: PYTHONPATH absoluto a `auditoria_por_etapas/resultados/soporte`, desde `r1-pmv`, `manage.py runserver 127.0.0.1:8781 --noreload --insecure --settings=audit01e_settings`. Datos/cookies/puerto exclusivos. Seguir los checkpoints, no usar credenciales reales ni guardar claves en navegador.
4. `auditoria_por_etapas/resultados/soporte/validar01e.py` reproduce control de este sublote. Para ampliar, crear nueva evidencia/build sin sobrescribir01-E.

Heredado, no reejecutado: cuatro casosPG01-D y ciclo904.663s01-C, accesibilidad1366×768previa, integración14. Sus servicios compatibles pueden orientar regresión, pero no acreditan el build/carga/perímetro actual. Las muestras de permisos actuales no cierran02–14 ni15. No probado: PostgreSQL nuevo, carreras autenticación/desactivación/renombrado, HTTPS/proxy, escala/DoS, retención real, eventos completos/exc_info, ancho estrecho y aceptación humana. No hay conclusión de coincidencia100%.

**Siguiente caso01-F-ADMIN-PERIMETRO-01:** usar staff/superuser ficticios sin mezclar roles comerciales; cinco fallos en `/`; confirmar rechazo de clave correcta; entrar por `/admin/login/` conCSRF; verificar sesión/`/inicio/` y permisos por modelo; después contrastar con el canal de mantenimiento configurado y la entrada comercial real autorizada. Este sublote ya demuestra bypass en aplicación local; falta resolver/verificar el perímetro o deshabilitación elegida, no repetir la misma muestra como cierre. En ausencia de hechos, registrar alternativas y medir tráfico/retención en aislamiento sin fijar políticas arbitrarias.

---

# Adenda anterior de ETAPA-01 · 12/11/2026 (conservada)

> **Fuente funcional principal:** [08 · planificación unificada](../../08_Historias_de_Usuario.md). Las fichas, RN y contratos de08 definen lo esperado; este documento conserva su papel de contexto, diseño, ejecución o evidencia. Las vistas07/09/03 se derivan de08.


**Estado actual:** Auditado en muestras; seguridad transversal abierta. **Pendientes compartidos:** Tráfico/admin/retención/logs; correo254/IDNA;5fallos/15min. **Próximo cursor:** SEC-15-TRAFICO-01 y SEC-15-OBS-01.

[Mapa consolidado y decisiones](conciliacion_20261112/CONSOLIDACION.md) · [Contratos de implementación](conciliacion_20261112/ENCARGOS.md) · [Verificación integrada](conciliacion_20261112/VERIFICACION.md) · [Informe original íntegro](conciliacion_20261112/BASELINE/auditoria_por_etapas/resultados/ETAPA-01.md).

Las decisiones nuevas se aceptan desde12/11 por delegación explícita del usuario. No se cambia el resultado histórico de una muestra ni se declara cerrado el módulo. Requisitos recién revisados requieren nueva implementación/verificación. Las referencias de línea del texto histórico remiten a BASELINE. Los anexos conservan su fecha y vigencia original; los estados actuales se consultan en el mapa.

## Rectificaciones transversales aplicables

Etapa09 sí tiene ejecución/evidencia (Chrome67funcionales+1control), aunque10–12 y estado general antiguos la dejaban pendiente. 04-D acredita revocación en sus muestras; su límite raw sin petición/servicio permanece. El fallo `_state.adding` de inventario fue corregido05-L e incluido en434tests actuales. Los informes antiguos que lo separaban no prueban fallo actual. El empate de orden de turnos no se considera corregido por repetir una corrida. Soporte12PG es DjangoClient concurrente contraPG, no redHTTP por sockets. 05-Linterrupción antes de escribir no prueba caída postwrite. HU-VEN-05b pide filtrosCA02 y detalleCA03; no hay conflicto de líneas expandidas.

---

## Informe y resultados históricos conservados

# ETAPA 01 — Ingreso, credenciales y protección de acceso

**AUDITORÍA DE ETAPA 01 COMPLETADA CON HALLAZGOS ABIERTOS · 09/11/2026, America/Lima.** El ingreso y el bloqueo quedaron inventariados, contrastados con planificación y ejecutados con datos aislados en servidor, navegador y concurrencia PostgreSQL. La conformidad por requisito conserva sus estados en §3. El cierre 01-D y las obligaciones de continuidad constan en §7.2 y §9.

**Siguiente cursor · ETAPA-02 / HU-AUTH-03 / CA-01 / GET y POST `/salir/`.** VENDEDOR con sesión y turno propio OPEN, sin borrador ACTIVE con líneas. Usar «Cerrar sesión», comprobar la advertencia, confirmar y verificar sesión invalidada, pantalla de ingreso y turno/propietario conservados. La base de etapa 02 debe ser distinta de las de 00/01.

## 1. Alcance, fuentes y criterios de cierre

Se leyó completo `PROTOCOLO_COMUN.md`, el estado general, ETAPA-00 y su anexo de formularios generados. Se inspeccionaron `identity/urls.py`, el tramo de ingreso de `views.py`, `forms.py`, `services.py`, `models.py`, `login.html`, navegación en `base.html`/`dashboard.html`, autorización y pruebas relacionadas. Configuración, Django instalado y admin se consultaron solo en lo pertinente. No se encontraron `AGENTS.md` en ancestros ni en los árboles de trabajo examinados.

El inventario **precedió a los recorridos**: dos HU/siete CA, RN-12/17/29, seis subtareas AUTH01 y dependencias técnicas; diez entradas de rutas/recursos, 21 elementos de UI, cuatro campos/controles y nueve componentes de persistencia/decisión. Los IDs locales son unidades de auditoría, no nuevos requisitos aceptados. Las siete rutas propias de identity se delimitan entre ingreso, personal/salida y panel; no se revisaron superficialmente como siete flujos completos.

| Fuente / entregable | Papel y revisión |
|---|---|
| [Inventario documental](anexos/ETAPA-01-planificacion.md) | Citas precisas de 21, 01, 07, 08, 09, 02, 03, 14, 16 y CONTROL_SPRINTS; HU/CA, reglas, tareas, discrepancias y propuestas. |
| [Inventario inverso](anexos/ETAPA-01-superficie.md) | Cada ruta, acción, mensaje, campo, salida y primer destino; fuentes de UI/código y superficies técnicas. Las filas estáticas no son resultados de ejecución. |
| [Correcciones y pruebas](anexos/ETAPA-01-codigo-y-pruebas.md) | Línea base preservada, diff propio, fallos antes y pruebas después; límites de Cliente Django/SQLite. |
| `PLANIFICACION_SCRUM_R1PMV.xlsx` | Procedencia/fecha/papel revalidados por anexo de etapa00 y hash `a9604b90d08dead7b815817f859004a802353aaf6f91f7e78a4467fa18406b49`; no se abrió para editar ni se usó como aceptación. Corte histórico, AUTH02 pendiente. |

AUTH-01 está seleccionada R1 (`09:46`). AUTH-02 está en backlog posterior (`09:75`) y descrita como implementación adicional actual (`21:23`): se audita esa implementación sin adjudicarle selección histórica. RN-17 (`07:219`) y AUTH02 (`08:30–32`) fijan **cinco fallos/15 minutos**. `03:302`, `16:326` y CONTROL:92 conservan relatos de **5 minutos**. El conflicto documentado DOC-00-05 queda conciliado por vigencia en01-D; se usa el requisito actual de quince minutos y se conserva el relato histórico. Jira queda excluido.

Exclusiones: altas/ediciones/desactivaciones de personal como proceso, salida con borradores, sesión única/expiración por inactividad, operaciones comerciales, exactitud de panel/reportes, CRUD/permisos completos de admin, TLS/infraestructura productiva, carga/tiempos estadísticos y concurrencia comercial PostgreSQL. El cierre 01-D sí ensaya concurrencia de ingreso. Los destinos se usan para comprobar la puerta de autorización; no se aprueban sus módulos.

## 2. Entorno, aislamiento y conservación

- Windows/PowerShell, Python 3.12.10 del `.venv`, Django 5.2.18; hashes Argon2 del proyecto. No se instalaron dependencias ni se leyeron secretos de `.env`.
- [audit01_settings.py](soporte/audit01_settings.py) bloquea carga de `.env`, fija APP_ENV=test/DEBUG=False y **base exclusiva** `resultados/datos/etapa01-20261109/audit.sqlite3`. Cookies `audit01_sessionid`/`audit01_csrftoken`. El runner usa SQLite en memoria y cookies estándar únicamente para compatibilidad de tests existentes.
- Servidor Django aislado `127.0.0.1:8766`, sin autoreload; HTTP local con estáticos `--insecure`. `localhost:8766` permitió otro ámbito de cookies del navegador, conectado a la misma base. Ambos hosts se verificaron por desafío HMAC `X-Audit01-Proof` antes de enviar credenciales; no se guardaron sus valores.
- Cinco fixtures iniciales `AUD01`: ADMIN, ALMACENERO, VENDEDOR activos no staff; VENDEDOR inactivo; ADMIN staff sin superusuario ni permisos de modelo. Credenciales aleatorias en archivo local excluido `datos/.../.credentials.json`, nunca en informes/logs/capturas. [Preparación](evidencias/01-preparacion.json).
- HTTP creó **cinco cuentas adicionales** `AUD01HTTP` por ejecución (`20261109120317eaf5da` en 01-A y `202611091226025a110c` en 01-B), para no alterar los contadores del recorrido visual. Cada repetición crea otro conjunto identificado; no limpia ni resemilla conjuntos existentes. Sus claves no se persisten.
- Las migraciones se aplicaron solo a la nueva base. No hay productos, lotes, turnos ni ventas. El script HTTP compara contenido/hash y conteo de **todos los modelos de catalog/inventory/cash/sales**, además de verificar las bases protegidas y la inmutabilidad de las cuentas ficticias frente a intentos no autorizados. Esta muestra vacía acredita ausencia de altas/efectos comerciales en los rechazos enviados; no demuestra inmutabilidad de registros comerciales preexistentes.
- Hash original antes/después: `4406ecd5babab34f0bb264e82c134eb21563494f9faf50e462d50c30c9d2ea95`. Hash base etapa00: `19546d1c77d5874c8d0d5061cba97be8abfe9f03435600ef40a6c9c9c9209b5e`. No se abrieron para operar; se leyeron para hash.
- Repositorio `r1-pmv`, HEAD `7816d3328115cf5aa5bcdd0985fffd795b3ae084`, con numerosos cambios previos. Se preservaron; copias de las fuentes intervenidas en `datos/.../baseline-auth/`. [Diff exclusivo de esta etapa](evidencias/01-auth-cambios.diff). La raíz documental no es repositorio Git.

Los estados de bloqueo se probaron con reloj controlado en tests. Para tiempo restante visual se movió **solo `locked_until` del fixture almacenero**, primero a +115 segundos y luego a −1 segundo, con [evidencia de preparación](evidencias/01-ui-clock-almacen-115.json) y [expiración preparada](evidencias/01-ui-clock-almacen--1.json). En 01-A/B se usó tiempo preparado. Para la comprobación de reloj real de 01-C véase §7.1. HTTP usa el mismo tipo de preparación en sus cuentas propias.

## 3. Matriz de trazabilidad ejecutada

Referencias `08`, `07`, etc. corresponden a documentos numerados de la raíz. `T` = suite [53 tests, manifiesto 01-B](evidencias/01-auth-tests-20261109-122521-777224.json) ([corte 01-A 45 tests](evidencias/01-auth-tests-20261109-115809-570846.json)); `H` = [70 comprobaciones HTTP/ORM 01-B](evidencias/01-http-202611091226025a110c.json) ([corte 01-A 51 comprobaciones](evidencias/01-http-20261109120317eaf5da.json)); `UI-nn` = captura y TXT `evidencias/01-ui-nn-*.{png,txt}`. CUMPLE significa exclusivamente los casos y entorno indicados.

| ID / fuente | Actor, requisito y ubicación | Esperado → observado / evidencia | Estado, prioridad y siguiente acción |
|---|---|---|---|
| AUTH-01 CA-01 / `08:18`, AT/MT-AUTH01-01, `03:60`; RN12 `07:165–169` | Tres roles activos; `/` → LoginForm → servicio → sesión → `/inicio/` | Correo con mayúsculas/espacios (incluidos espacios Unicode `\u00a0` y tabuladores) identifica misma cuenta; clave válida crea sesión/last_login y menú del rol. UI04/06/10, T `all_three_roles…` y `unicode_casefold…`, H ROLE/SESSION/COOKIE. Recarga conserva almacenero en UI20. | CUMPLE flujo secuencial probado / P1. 01-C añade Chrome, teclado, historial y acceso por rol (§7.1). |
| AUTH-01 CA-02 / `08:19`, AT/MT/ST-AUTH01-02/01; `03:61` | Visitante; cuenta existente con clave errónea e inexistente | Mismo literal «Correo o contraseña incorrectos», HTTP200 sin sesión autenticada; password vacía en respuesta. UI11/13, T `wrong_unknown_inactive…`, H UNIFORM. | CUMPLE casos de mensaje/servidor / P1. Uniformidad temporal NO EJECUTADA. |
| AUTH-01 CA-03 / `08:20`, AT/MT-AUTH01-03, ST-AUTH01-02; `03:62` | Cuenta inactiva con clave correcta | Mismo mensaje general, no revela inactividad ni crea sesión. UI12, T, H UNIFORM-inactive. | CUMPLE caso probado / P1. No equivale a auditar desactivación/revocación, etapa02. |
| AUTH-01 CA-04 / `08:21`, AT/MT/ST-AUTH01-04/03; RN29 `07:333–347` | Visitante; ADMIN/ALMACENERO/VENDEDOR intentan destinos ajenos | UI07 y UI09: empleados denegados a almacén/vendedor, sin lista; UI08 visitante redirigido. T + H (01-B) comprueban las 7 rutas de `identity/urls.py` (`/`, `/inicio/`, `/salir/`, `/empleados/`, `/empleados/nuevo/`, `/empleados/<uuid>/editar/`, `/empleados/<uuid>/estado/`): visitante recibe 302 a `/?next=…`, almacén/vendedor reciben 403 sin lista ni cambio de `is_active`/datos, métodos no permitidos devuelven 405; `caja/abrir` deniega ADMIN. Tablas comerciales sin cambios. | **PARCIAL** / P1. Resto de rutas de otros módulos, propiedad de objetos y datos comerciales existentes en etapas02–15. No declarar RN29 completa. |
| AUTH-02 CA-01 / `08:30`; RN17 `07:219` | Cuenta activa; quinto fallo en `/` | Fallos1–4 generales; quinto muestra15 y guarda bloqueo. UI-fallo1..5/UI14; H LOCK1..5/duración; T comprueba plazo exacto T+900. Inactiva/inexistente mismo quinto mensaje en T. | CUMPLE secuencial / P1. Cuatro escenarios PostgreSQL ejecutados en 01-D (§7.2), conservando el límite de esa muestra. |
| AUTH-02 CA-02 / `08:31`; RN17 | Identificador bloqueado; cualquier clave/otra sesión/variante normalizada | Clave correcta sigue rechazada UI15; otro host/cookies y mayúsculas conserva bloqueo UI16; UI17 muestra2; H confirma2/1 y no extensión; T fronteras 0/59/60/839/840/899 segundos transcurridos. | CUMPLE casos secuenciales / P1. No afirmar contador vivo: se actualiza al enviar. Retención/tráfico separados. |
| AUTH-02 CA-03 / `08:32`; RN17 | Expiración y acceso válido | Preparación UI a pasado → ingreso almacenero UI19, sesión UI20. H EXPIRY contador0/fecha nula. T en igualdad exacta T+900, éxito conserva fila; fallo tras expirar cuenta1 y cinco nuevos fallos completan un segundo ciclo de bloqueo exacto en T2+900; éxito antes de quinto reinicia. | CUMPLE en reloj controlado y en el ciclo real de 01-C / P1. 01-C añade un ciclo con 904,663 s reales entre quinto fallo y acceso correcto (§7.1). |
| S1-AUTH01-UI / `16:81`; E01-U01..21 | Formulario, mensajes, ayudas, controles, enlaces | Inventario inverso completo; etiquetas/textos y mensajes observados en UI01..18. Errores vacíos UI02, formato UI03; menús de tres roles observados. Promesas de reportes/inventario/ventas solo inventariadas. | PARCIAL / P2. 01-C verificó teclado, foco e historial del login a 1366×768. Otros tamaños y las funciones anunciadas por las tarjetas siguen fuera de esta muestra. |
| S1-AUTH01-SVC/AUTO / `16:82,84`; S1-SEC-02 / `16:66` | Validación servidor, hash, CSRF y sesión | T + H prueban ausencia/alteración/origen externo CSRF→403 sin contador; válido permite ingresar, sesión/CSRF rotados en T; flags HttpOnly/Lax H. | CUMPLE segmento probado / P1. CI, TLS, proxy y seguridad global NO EJECUTADOS. |
| E01-F01..04 / LoginForm, login_view; propuesta CA-01 | Entradas, normalización y destino | Límites/errores de §4; T + H (01-B) verifican `next` escapado, URLs externas/esquema inválido/HTTPS downgrade rechazadas, prioridad de `POST["next"]` sobre `GET["next"]` contradictorio, anulación cuando `POST["next"]` es externo, `next` a ruta local inexistente (`302` → `404` sin secretos y sesión conservada), URL absoluta mismo host, `next="/"` sin bucle y sesión ya autenticada ignorando `next` hacia `/inicio/`. | CUMPLE controles ensayados en servidor/HTTP, PARCIAL contrato de límites y UI / P2. 01-C añade el límite de teclado, el retorno de 404 y el descarte de destino externo en Chrome (§7.1). |
| E01-P01..09 / modelo/servicio; propuesta CA-02 | Persistencia de identidad/contador | T identifica HMAC64, agregado por correo, fila estable y sin credenciales; bloqueo de una cuenta no bloquea otros roles; sesión previa continúa activa. H valida sesión DB, last_login y negocios sin cambios. | CUMPLE observación acotada / P1. Sesión previa no revocada es observación, no aceptación de AUTH04. |
| S1-AUTH01-MAN/REV / `16:85–86` | Recorrido real y revisión independiente | Navegador IAB (en 01-A) y revisión de código/documentos; errores/fallos/tres roles observados. | PARCIAL / P2. 01-C ejecutó el ingreso en Chrome estable para Windows a 1366×768. Pendientes la aceptación humana independiente y el recorrido transversal de nueve HU. |
| DOC-00-05 / 03:302, 16:326, CONTROL:92 | Duración histórica5 vs actual15 | Código, requisito y ejecución actual15. | CONCILIADO por vigencia / P1 documental. Complementos actuales enlazados, estados históricos conservados. |
| DOC-01-01 / 09:3,75; 21:23; XLSX | Selección AUTH02 | El backlog declara su papel histórico. Implementación adicional y selección histórica se concilian por fecha y función de la fuente. | CONCILIADO documentalmente en 01-D / P2. Una asignación comercial nueva de release conserva su decisión propia. |

## 4. Campos, acciones, mensajes y salidas

El [anexo inverso](anexos/ETAPA-01-superficie.md) enumera individualmente E01-U01..21, R01..10 y P01..09; forma parte del inventario de esta etapa. No hay tabla/filtro/descarga/impresión ni salida comercial en login. El éxito se expresa por redirección/sesión, sin mensaje de éxito adicional. Texto «Acceso seguro» no se toma como garantía.

| Campo/salida | Contrato efectivo y persistencia | Casos ejecutados / omisiones |
|---|---|---|
| Correo de trabajo (`email`) | Inicial vacío; requerido; tipo email; autocomplete username/autofoco; máximo formulario320, cuenta254. Recorta extremos (incluidos espacios Unicode `\u00a0`, `\t`) y aplica `casefold()` en servicio; no modifica correo guardado. Error vacío, solo espacios, formato, nulo o longitud; repuebla escapado en rechazo. | UI vacío/formato/mayúsculas/espacios; T 254/255/319/320 aceptan validación y rechazan credenciales uniformemente; 321 error sin intento adicional. En 01-B (`T`): solo espacios (`"     "`) y parte local no ASCII (`josé@…`, `straße@…`) se rechazan en `LoginForm` sin tocar `LoginAttempt`; dominios IDN (`@münchen.invalid`, `@straße.invalid` ↔ `@STRASSE.INVALID`) se aceptan y normalizan por `casefold()`; dominio IDN en Unicode vs punycode (`@xn--mnchen-3ya.invalid`) producen identificadores distintos porque `normalize_email` no aplica IDNA. Diferencia 320/254 y política IDNA registradas como pendientes de decisión. |
| Contraseña (`password`) | Inicial vacía; requerida; tipo password; autocomplete current-password; `strip=False`; sin máximo propio. No se repuebla. Comparación hash Argon2; no se guarda texto en sesión/contador. | UI correcta/errónea/vacía; T nulo, espacios significativos, contraseña de solo espacios (`"     "` pasa formulario por `strip=False` y cuenta 1 fallo) y contraseña larga de 97 caracteres (>72 bytes) verificada sin truncamiento; H ausencia del valor enviado en respuestas/estado guardado. No se ensayó carga masiva; proponer máximo sin truncar. |
| CSRF oculto | Generado; exigido por middleware; cookie HttpOnly/Lax. No evidencia de valores. | T/H faltante, inválido, origen ajeno→403 sin avance del contador; token válido autentica. Secure/TLS productivo NO EJECUTADO. |
| `next` oculto condicional | Opcional; POST antes que GET; escapado; destino permitido por host/esquema; no almacena dato comercial. | T/H interno, externo, `//externo`, `javascript:` y otros malformados; T HTTPS→HTTP y escape; UI `next` empleados termina 403 vendedor. En 01-B (`T` y `H`): prioridad `POST["next"]` sobre `GET["next"]` contradictorio, fallback cuando `POST["next"]=""`, anulación a `/inicio/` cuando `POST["next"]` es externo, URL absoluta del mismo host, `next="/"` sin bucle, destino local inexistente (`302` → `404` seguro conservando sesión) y sesión ya autenticada ignorando `next` hacia `/inicio/`. 01-C añade el límite de teclado, el retorno de 404 y el descarte de destino externo en Chrome (§7.1). |
| Mensajes generales y bloqueo | Error credenciales único antes del quinto. Bloqueo con techo en minutos/min1; no revela existencia en estados equivalentes; nueva petición recalcula. | UI/H/T descritos; literal15 y2 visible; H1; precisión segundos y segundo ciclo completo de bloqueo tras expiración en T. Sin análisis estadístico de latencia. |
| Enlaces auxiliares y opciones por rol | Marca/inicio/saltar contenido, menú, salir, volver a inicio tras403; nombres/rol visibles. | ADMIN usa menú Empleados; tres roles usan confirmación de salida solo para preparar login; vendedor vuelve al inicio desde403. En 01-C se activó el salto, se recorrió el formulario con teclado y se comprobaron ambos errores asociados. Operación completa de menús inventariada y remitida, no aprobada. |

## 5. Hallazgos, correcciones y superficies separadas

| ID / prioridad | Evidencia antes → resultado actual | Estado y decisión |
|---|---|---|
| FIX-E01-01 / P2 | POST sin claves se enlazaba como None, sin errores. Ahora se enlaza por método POST. Regresión inicial falla; T y H HTTP-EMPTY confirman dos errores sin contador. | CORREGIDO y VERIFICADO en servidor. Formulario normal vacío también observado UI02; no confundir ese envío con POST sin claves. |
| FIX-E01-02 / P2 | GET/POST de login sin cabecera anti-cache. Ahora `never_cache`, `no-store/private` en T y GET H. | CORREGIDO, verificación HTTP. Volver atrás en IAB produjo ERR_CACHE_MISS y el control bloqueó su página data; ese resultado era inconcluso en IAB. En 01-C Chrome hizo GET al volver y al recargar, con clave vacía (§7.1). |
| FIX-E01-03 / P1 | Reporte estándar de excepción DEBUG=False podía incluir contraseña en POST/locales; setting genérico no bastaba. Añadidos decoradores sensibles a vista/servicio. En 01-B se verificó además `RedactSensitiveDataFilter` sobre `record.getMessage()` y se documentó que `record.exc_info` se formatea después del filtro. | CORREGIDO en `identity`, regresiones verificadas. Sin envío de correo ni impresión del reporte; no garantía sobre todos los loggers/middleware/`exc_info`/DEBUG=True/infraestructura. |
| E01-S01/S02, DOC-01-04 / P1 | Diseño `02:277` exige límite IP/sesión. No existe en aplicación inspeccionada; hash se calcula incluso bloqueado. H muestra tres identificadores nuevos procesados, sin ser ensayo de saturación. | **INCUMPLE diseño en capa aplicación**; despliegue NO EXAMINADO. Política de umbral/ventana/IP fiable pendiente: PROP-E01-T-TRAFICO. No fijar números arbitrarios. |
| E01-S03, DOC-01-05 / P2 | H GROWTH: tres correos nuevos→tres filas; repetir último conserva número de filas y contador2. Éxito conserva fila, sin TTL/limpieza en código. | EXTRA SIN REQUISITO de retención definido; riesgo operativo confirmado en muestra pequeña, sin carga. PROP-E01-T-RETENCION pendiente. |
| E01-S04, DOC-01-06 / P1 | Los datos históricos T/H de 01-B acreditan reglas distintas para staff en Django admin y el login comercial. El bloqueo de ingreso comercial no cubre a una identidad staff autenticada por el portal técnico. En Chrome 01-C se observaron por separado la denegación a no-staff y la admisión de staff sin permisos de modelo. | **PARCIAL / EXTRA SIN REQUISITO comercial**. Pendiente decidir si se necesita el portal en despliegue y qué control de acceso o política de autenticación deberá compartir. Los permisos por modelo están sin auditar. |
| E01-S07 / P1 | En 01-D se ejecutaron cuatro escenarios de ingreso con PostgreSQL 18.4, conexiones independientes y esperas por fila observadas. | CUMPLE muestra concurrente de §7.2. La concurrencia de operaciones comerciales y configuración productiva pertenece a etapa15. |
| E01-S08, DOC-01-07 / P2 | Igualdad de mensajes y filtrado acotado comprobados. | NO EJECUTADO análisis temporal estadístico ni observabilidad completa. |

No se cambiaron modelos, formularios, URLs, plantillas, claves del operador ni selección comercial. Los cambios propios de aplicación son `identity/views.py`, `identity/services.py` y `identity/test_auth_audit01.py` (34 métodos en 01-B). El diff está separado de modificaciones previas. No hay migración nueva.

## 6. Propuestas y trazabilidad posterior

Las propuestas completas con actor/necesidad, precondiciones, Dado/Cuando/Entonces, límites, errores, permisos, efectos y dependencias están en [planificación §6](anexos/ETAPA-01-planificacion.md) y [superficie §8](anexos/ETAPA-01-superficie.md). **Su aceptación sigue pendiente**; pruebas o código no las convierten en HU aceptadas.

| Propuesta | Situación en este sublote / destino |
|---|---|
| PROP-E01-CA-01 y CA-NAVEGACION | Contrato normalización/campos/next; verificado en servidor y HTTP (incluyendo `POST` vs `GET` contradictorio, destino inexistente, sesión activa y fronteras Unicode/IDN); en 01-C se ejecutaron las fronteras de teclado y los destinos ordinarios en Chrome. Permanecen abiertas la longitud de cuenta y la política IDNA. Ampliar complemento vigente AUTH01 sin renumerar históricos. |
| PROP-E01-CA-02 | Contrato identificador/otra sesión/reloj/no extensión/equivalencia inactiva/inexistente y segundo ciclo tras expiración verificados secuencialmente; decisión DOC-01-02/03 pendiente; no eliminar uniformidad útil. |
| PROP-E01-CA-SECRETOS | Corrección implementada y verificada en `identity` y filtro de mensaje en `RedactSensitiveDataFilter`; pendiente formalización documental y tratamiento de `record.exc_info` en `app_platform` (etapa 15). |
| PROP-E01-T-TRAFICO / RETENCION / ADMIN | Tareas técnicas PROPUESTAS; alternativas y riesgos documentados (incluido el cruce de sesión `/admin/login/` → `/inicio/`), no implementadas por falta de política inferible. |
| PROP-E01-T-CONCURRENCIA, PR-03 | Cuatro escenarios de ingreso implementados y verificados con PostgreSQL efímero en 01-D. Ampliaciones comerciales en etapa15. |
| PROP-E01-PR-01 / PR-02 | Suite de entradas y temporal ampliada a 34 tests propios (53 totales) y 70 comprobaciones HTTP/ORM, más recorrido parcial de navegador de 01-A. Los recorridos visuales de historial, campos y admin se completaron en 01-C/D. La revisión humana independiente continúa en etapa17. |
| PROP-E01-PR-04 | Perímetro/exposición con muestra HTTP ampliada y redacción; carga/admin completo/latencia pendientes. |
| PROP-E01-HU-01 | Refinamiento **de HU-LOG-01 existente**, sin duplicar HU ni crear cuarto rol. Consulta de accesos/bloqueo con privacidad/retención; propuesta para etapa02, sin pantalla implementada por este informe. |

Actualizar backlog/matriz mediante apéndice actual fechado, con vínculo a siete CA y evidencias de01, preservando sus estados históricos. AUTH-01 CA4 permanece parcial, AUTH02 conserva discrepancia de selección. «Reportes» de tarjeta pública debe conciliarse en etapa13, sin declarar REP-01 terminada.

## 7. Pruebas, evidencia y reproducción

| Ejecución | Resultado comprobado | Alcance/omisiones |
|---|---|---|
| Regresiones iniciales | [4 métodos,5 fallos incluyendo subtests](evidencias/01-auth-regresiones-antes-final.txt) | Reproducción previa de3 defectos; no contiene secretos. |
| Suite después, primer corte 01-A | [45/45,8,503s](evidencias/01-auth-tests-despues.txt) y [45/45,8,645s](evidencias/01-auth-tests-20261109-115809-570846.txt) | 26 nuevos + 19 existentes en 01-A. |
| Suite ampliada 01-B con runner reproducible | [53/53,10,999s](evidencias/01-auth-tests-20261109-122521-777224.txt), [manifiesto 01-B](evidencias/01-auth-tests-20261109-122521-777224.json) | 34 nuevos + 19 existentes. SQLite memoria; no suite completa del proyecto. |
| HTTP real 01-A, 09/11 12:03 Lima | [51/51 expectativas observadas](evidencias/01-http-20261109120317eaf5da.json) | Corte inicial preservado. |
| HTTP real 01-B, 09/11 12:26 Lima | [70/70 expectativas observadas](evidencias/01-http-202611091226025a110c.json) | Añade `next` contradictorio/inexistente/autenticado, rutas `identity`, POST no-staff/mayúsculas en `/admin/login/` y bypass de sesión hacia `/inicio/`. **70/70 no significa 70 requisitos aprobados**. |
| Navegador IAB,09/11 ~11:54–11:57 Lima | 20 pares PNG/TXT y5 TXT de fallos | Recorrido de 01-A descrito abajo; en 01-B el entorno no dispone de herramienta de navegador (`NO EJECUTADO` visual adicional). |
| check/migraciones | Sin incidencias, sin cambios detectados | Configuración aislada; no aceptación global. |

Recorrido visual conservado: UI01 ingreso;02 vacíos;03 formato;04 ADMIN normalizado;05 Empleados vía menú;06 almacenero;07 denegación;08 visitante→next;09 vendedor next denegado;10 menú vendedor;11 clave errónea;12 inactiva;13 inexistente;14 quinto bloqueo;15 correcta bloqueada;16 otra sesión;17 dos minutos;18 recarga;19 expirado acceso;20 recarga sesión. Las capturas14,19,20 se inspeccionaron además como imágenes locales. Captura18 conserva pantalla, pero no prueba que recargar un POST enviase nueva petición ni que actualizara minutos. Tras reinicio de servidor se obtuvieron19/20; el intento posterior de volver atrás produjo ERR_CACHE_MISS/página data bloqueada por herramienta, sin atribuirlo automáticamente a Django. Una pestaña nueva mostró sesión almacenero en el árbol accesible, pero no produjo artefacto persistente21: **no se cuenta como evidencia persistida**.

Al continuar en 01-A y durante toda la sesión 01-B, la herramienta de navegador no estuvo disponible en el entorno. Conforme a `PROTOCOLO_COMUN.md` §2, no se sustituye la prueba visual por cliente HTTP/Django: los casos adicionales de `next`, normalización Unicode/IDN, rutas `identity` y `/admin/login/` quedaron verificados en servidor/HTTP (`T` y `H`), y sus casos visuales quedaron abiertos al cierre de 01-B bajo `E01-B-01` y `E01-B-02`.

Comandos desde la raíz; no usar arranque/semillas ordinarias ni ejecutar prepare otra vez:

```powershell
& './r1-pmv/.venv/Scripts/python.exe' './auditoria_por_etapas/resultados/soporte/audit01.py' inspect
& './r1-pmv/.venv/Scripts/python.exe' './auditoria_por_etapas/resultados/soporte/audit01.py' check
& './r1-pmv/.venv/Scripts/python.exe' './auditoria_por_etapas/resultados/soporte/run_auth01_tests.py'
# En terminal dedicada, para HTTP/navegador:
& './r1-pmv/.venv/Scripts/python.exe' './auditoria_por_etapas/resultados/soporte/audit01.py' serve
# En otra terminal; primero verificar identidad, luego pruebas:
& './r1-pmv/.venv/Scripts/python.exe' './auditoria_por_etapas/resultados/soporte/audit01.py' proof
& './r1-pmv/.venv/Scripts/python.exe' './auditoria_por_etapas/resultados/soporte/audit01_http.py'
```

`run_auth01_tests.py` guarda manifiesto/log con fecha única. `audit01_http.py` crea cinco cuentas nuevas por repetición y guarda JSON único con esperado/observado. El lanzador preserva evidencia anterior en `evidencias/repeticiones/`. Las credenciales iniciales de navegador se leen localmente sin imprimir; si se recrea otro entorno hay que usar una carpeta/configuración nueva, no borrar estos datos.

### 7.1. Corte 01-C del 9 de noviembre de 2026

Se retomó el inventario de §1 y el cursor E01-B-01 sobre la base ya preparada. Google Chrome estable 157.0.8103.39 ejecutó las pantallas en Windows 11, compilación 26200, con perfil temporal y viewport interior de 1366×768. Playwright Core 1.62.1 manejó Chrome en modo headless. El recorrido de historial conservó la configuración de caché de Chrome, sin interceptar la red. El soporte tomó las credenciales ficticias del archivo local de preparación y verificó con `proof` la identidad del servidor antes de usarlas. Django usó SQLite. La regresión de 18 métodos tuvo su propia base en memoria.

| Fuente y caso | Esperado y observado | Estado de la muestra |
|---|---|---|
| AUTH-01/CA-02, R01/R02, U11–13/U16, FIX-E01-02. Visitante en `/` | GET con foco en correo y ambos campos vacíos. Un POST con clave errónea devolvió 200, el mensaje uniforme y la clave vacía. Contador de ADMIN de 0 a 1, sin variación de `last_login` ni cookie de sesión. Atrás hizo GET 200, recuperó el mismo correo y dejó la clave vacía. Recargar ese GET vació ambos campos. El foco siguió en correo, el contador en 1 y `/inicio/` pidió autenticación. Los cuatro documentos declararon `no-store` y `private`. | CUMPLE / P1 en Chrome. El correo restaurado por historial es observable en ese equipo. Se midió la recarga del GET recuperado. [Secuencia, cabeceras y lecturas de base](evidencias/01-C-historial-2026-11-09T21-00-56-325Z/resultados.json) |
| AUTH-01/CA-01/04, RN-12/29. Sesión y primer destino | ADMIN corrigió sus credenciales en la misma pestaña. El contador volvió a 0, cambió `last_login` y abrió Empleados por menú con 200. Atrás con sesión pasó por GET `/` 302 y volvió al panel con 200. ALMACENERO conservó su propio panel al recargar, sin enlace Empleados, y recibió 403 al solicitar ese destino. El menú y la sesión persistida de VENDEDOR se comprobaron en el ensayo RN-17. | CUMPLE para ingreso. CA-04 sigue PARCIAL para el conjunto de permisos. [Historial y puertas por rol](evidencias/01-C-historial-2026-11-09T21-00-56-325Z/resultados.json) |
| S1-AUTH01-UI, S1-ENV-01, NFR-06/07, `02:358–359`, `03:163`. U02/U03/U11–13/U18 | Desde el autofoco, Mayús+Tab llevó a marca y salto. Intro enfocó `main#contenido`. Tab recorrió correo, contraseña y botón. Ambos campos mostraron anillo de foco de 3 px tras la transición. Intro en vacío mostró «Este campo es obligatorio.» junto a cada control con etiqueta, `aria-invalid` y referencia al error. Los centros de los campos y botón eran operables y el documento no desbordó horizontalmente. | CUMPLE en el formulario a este viewport / P2. La revisión humana independiente y el recorrido de nueve HU de MT-COMPAT-01 siguen pendientes. [Salto visible](evidencias/01-C-historial-2026-11-09T21-00-56-325Z/05-salto.png) · [Errores por campo](evidencias/01-C-historial-2026-11-09T21-00-56-325Z/06-errores-campos.png) |
| E01-F01/F04, PROP-E01-CA-01. Correo y `next` | Al teclear el carácter 321 el valor quedó en 320, con cero POST. Un destino local inexistente produjo 302 y 404 con «Volver al inicio», que regresó al panel de almacén. Con un destino externo ordinario, el servidor eligió `/inicio/`, que respondió 200. Se observaron cero solicitudes al exterior durante el envío. | CUMPLE en esos bordes / P2. El máximo de 254 del modelo y la equivalencia IDNA continúan como decisiones. [Cinco casos Chrome](evidencias/01-chrome-b02-20261109T205838-198Z/observaciones.json) |
| E01-R09/S04, DOC-01-06. Puerta técnica en perfiles independientes | El almacenero sin staff recibió el mensaje de Django, 200, clave vacía y ninguna cookie de sesión. La cuenta staff de prueba entró al índice, que indicó que carecía de permisos para ver o editar modelos. | PARCIAL / P1. Esta observación cubre la entrada. Faltan política aceptada para proteger el portal y alcance de permisos. Los cinco fallos visuales constan en la fila siguiente. [Rechazo](evidencias/01-chrome-b02-20261109T205838-198Z/admin-rechazo.png) · [Índice staff](evidencias/01-chrome-b02-20261109T205838-198Z/admin-staff.png) |
| AUTH-02/CA-01–03, RN-17. VENDEDOR, reloj real | El quinto fallo se procesó a las 15:57:11 Lima y fijó el vencimiento a las 16:12:11,579883. Otra sesión, con correo normalizado y clave correcta, mostró 15, 2 y 1 minuto(s), manteniendo el contador en 5 y el mismo vencimiento. El envío válido de las 16:12:16 produjo 302, abrió el panel y guardó sesión VENDEDOR, contador 0 y bloqueo nulo. Entre los envíos del quinto fallo y el éxito transcurrieron 904,663 s de reloj monotónico. | CUMPLE esta secuencia / P1. Diez eventos de navegador y lectura ORM, sin ajustar reloj ni fixture. Este ensayo guardó DOM observado y datos sanitizados, sin PNG. [Evidencia de reloj real](evidencias/01-C-espera-20261109T205701803Z.json) |
| E01-R09/S04. Cinco errores en Django admin | Perfil nuevo de Chrome y cinco claves aleatorias erróneas de la cuenta staff. Cada POST respondió 200 en la misma pantalla, con mensaje general idéntico, clave vacía y sin sesión. La quinta respuesta mantuvo el mensaje general, sin minutos de bloqueo. El agregado de LoginAttempt conservó 23 filas, 29 fallos y 3 fechas de bloqueo entre ambas lecturas. | PARCIAL como superficie / P1. El requisito y la protección propia de este canal continúan por definir. Los datos son observaciones de rechazo. [Cinco respuestas y agregado](evidencias/01-chrome-admin-failures-20261109T211121-168Z/observaciones.json) · [Quinto rechazo](evidencias/01-chrome-admin-failures-20261109T211121-168Z/quinto-rechazo.png) |
| AUTH-01/CA-01–03 y AUTH-02/CA-01–03, RN-17. Regresión secuencial | Pasaron 18/18 métodos existentes en 6,623 s. Se observaron mensajes iguales para clave errónea, inactiva e inexistente, límites con reloj controlado, aislamiento entre identidades, CSRF válido con rotación y persistencia de sesión. La validación negativa de CSRF sigue sustentada por los resultados de 01-B. | CUMPLE casos seleccionados / P1. Son repeticiones de la suite de §7. [Métodos, hashes y comandos](evidencias/01-C-regresion-identity-20261109.json) |
| E01-S01/S02, DOC-01-04. Tráfico | La lista de middleware de `config/settings.py:36` y el servicio de ingreso no implementan el presupuesto por IP/sesión de `02:277`. El Compose versionado declara db, migrate y web (`compose.yaml:1–40`). El Dockerfile inicia Gunicorn y el Compose local sustituye el comando por runserver. Estos archivos no muestran un limitador en el punto de entrada. | INCUMPLE en aplicación / P1. Despliegue real NO EXAMINADO. Pendiente identificar responsable, ventana y límite. |
| E01-S03, DOC-01-05. Retención | A las 16:01 Lima, de 23 filas había 8 con contador cero, 12 positivas sin fecha de bloqueo, 1 con bloqueo vigente y 2 que conservaban fecha vencida. Consulta agregada de solo lectura en la base de pruebas. | EXTRA SIN REQUISITO de plazo / P2. Esta distribución no estima crecimiento productivo. La decisión afecta a la continuidad de los contadores 1–4. [SQL, instante y distribución](evidencias/01-retencion-20261109T210100073850Z.json) |

**Criterio propuesto para PROP-E01-CA-01, pendiente de aceptación.** Dado un visitante que recibió un rechazo, cuando vuelve al login y recarga el GET, entonces la clave queda vacía, continúa sin sesión y el contador solo cambia con otro envío que alcance la validación de credenciales. PR-01 puede conservar este recorrido como regresión. En terminales compartidos queda por decidir si se permite restaurar el correo al volver atrás. Los datos actuales describen lo que hizo Chrome. Los refinamientos de HU-LOG-01 y las tareas de tráfico, retención y administración se mantienen en §6.

**Reproducción de 01-C.** Desde la raíz, arrancar `audit01.py serve` y verificar `audit01.py proof` como se indica en §7. Ejecutar con Node 24 y el Chrome instalado. El ensayo temporal necesita uso exclusivo de la cuenta ficticia VENDEDOR hasta que termine.

```powershell
node --disable-warning=ExperimentalWarning ./auditoria_por_etapas/resultados/soporte/audit01_historial.cjs
node --disable-warning=ExperimentalWarning ./auditoria_por_etapas/resultados/soporte/audit01_chrome_b02.cjs
node ./auditoria_por_etapas/resultados/soporte/espera_real_01c.cjs
node --disable-warning=ExperimentalWarning ./auditoria_por_etapas/resultados/soporte/audit01_chrome_admin_failures.cjs
```

El recorrido de historial terminó con **14/14 comprobaciones**, incluidas dos de conservación, y ocho capturas. La primera ejecución se interrumpió tras nueve observaciones por un selector ambiguo de la herramienta. Se precisó la etiqueta y se repitió el recorrido antes de ampliarlo con la corrección de credenciales en la misma pestaña. El bloque de fronteras y portal terminó con cinco casos. Sus primeras cuatro observaciones se repitieron. Los conteos se informan por ejecución. [Historia de la primera ejecución](evidencias/01-C-historial-2026-11-09T20-56-38-235Z/resultados.json) · [Versión intermedia de 13 comprobaciones](evidencias/01-C-historial-2026-11-09T20-57-15-663Z/resultados.json) · [Primer corte de fronteras](evidencias/01-chrome-b02-20261109T205610-697Z/observaciones.json)

En esta sesión `audit01.py check` devolvió cero incidencias y ninguna migración pendiente de generar. Las comprobaciones nuevas verifican el código existente. Los tres arreglos del producto pertenecen a los cortes anteriores. Los cambios de 01-C afectan a la evidencia, el soporte reproducible y los dos informes.

### 7.2. Cierre 01-D y alcance final

El cierre abarca el inventario completo del tramo, sus recorridos y la clasificación de cada hallazgo. El [anexo de cierre y traspaso](anexos/ETAPA-01-cierre-y-traspaso.md) enlaza los siete CA, cada grupo del inventario inverso y los trabajos que continúan en las etapas correspondientes. AUTH-01/CA-04 mantiene PARCIAL en su autorización transversal. Los límites de tráfico, retención, administración y observabilidad conservan los estados detallados en §9.

| Caso y requisito | Resultado comprobado | Evidencia y límite |
|---|---|---|
| E01-F01 / PROP-E01-CA-01, Chrome Windows 1366×768 | Cuatro casos. Correo con espacios NBSP/tabulador y mayúsculas ingresó como ADMIN. Sólo espacios y parte local Unicode mostraron error de campo y no añadieron filas. Un dominio IDN ficticio inexistente llegó al mensaje uniforme y agregó una fila de intentos. Las tres respuestas rechazadas dejaron clave vacía y ninguna sesión. | [JSON y tres capturas](evidencias/01-D-unicode-2026-11-09T21-59-32-996Z/observaciones.json). La equivalencia de Unicode y punycode continúa como decisión de contrato. |
| AUTH-01/CA-01–03 y RN-17, cuentas preexistentes | 20/20 métodos en memoria, 8,625 s, cero errores, fallos u omisiones. Se repitieron los 18 métodos de 01-C y se añadieron dos regresiones. Cuenta con contraseña inutilizable conserva rechazo uniforme y quinto bloqueo. Una cuenta con hash PBKDF2 configurado admite el ingreso normalizado tras un fallo y persiste identidad/contador cero. | [Manifiesto de 20 métodos](evidencias/01-D-regresion-20261109-170211.json). Los dos métodos nuevos están al final de `identity/test_auth_audit01.py`. Son 36 métodos propios acumulados, de los cuales se seleccionó el subconjunto indicado para este corte. |
| E01-PG-01, RN-17, primera fila | Dos POST simultáneos, dos conexiones y barrera justo antes de INSERT. Terminaron con una fila, dos fallos, mensaje general y ninguna sesión. | [Cuatro escenarios PostgreSQL](evidencias/01-D-postgresql-20261109T220349Z.json). Django Client con CSRF válido y persistencia PostgreSQL real. |
| E01-PG-01, quinto fallo | Cinco conexiones enviaron errores concurrentes. Cuatro recibieron el mensaje general y una el bloqueo. Persistieron cinco fallos y vencimiento a 900 s. | Mismo manifiesto. Concurrencia limitada a esos cinco clientes y una cuenta ficticia. |
| E01-PG-01, éxito/fallo concurrentes | Desde cuatro fallos, éxito primero y error esperando dejó contador 1 y una sesión correcta. Quinto fallo primero y clave correcta esperando dejó bloqueo y ninguna sesión. Las dos secuencias comprobaron espera real mediante `pg_blocking_pids`. | PostgreSQL 18.4, aislamiento read committed, conexiones distintas. Una ejecución por escenario con orden controlado. No ensayo de carga. |
| Conciliación de fuentes | DOC-01-01 distingue selección histórica de AUTH-02 y entrega adicional actual. DOC-00-05 mantiene el relato histórico de cinco minutos con referencia al requisito actual y su evidencia de quince. | Complemento fechado enlazado desde 09, 03 y 21. Sin reasignar Sprint, SP ni aceptación comercial. |

El clúster PostgreSQL se creó en un directorio temporal marcado, con puerto loopback y credenciales efímeras. Migraciones y verificaciones corrieron únicamente en su base. Docker Desktop carecía de motor disponible y se utilizó PostgreSQL nativo ya instalado. Dos intentos de preparación fallaron por los permisos de un directorio temporal creado en modo 0700. Otro arranque heredó una tubería de salida y quedó esperando su cierre. Se corrigió el soporte usando permisos heredados normales en su carpeta propia y captura de salida en archivo. La cuarta ejecución completó los cuatro escenarios y eliminó sólo su clúster, tras verificar ruta y marca. Esos fallos del soporte se conservan como INCOMPLETO. [Intento 1](evidencias/01-D-postgresql-20261109T215906Z.json) · [Intento 2](evidencias/01-D-postgresql-20261109T215921Z.json) · [Intento 3](evidencias/01-D-postgresql-20261109T220133Z.json)

Reproducción desde la raíz mediante los soportes siguientes. El ensayo PostgreSQL prepara y elimina su propia instancia. El recorrido Unicode requiere primero el servidor `audit01.py serve` y `proof` de §7. Las credenciales permanecen locales.

```powershell
& ./r1-pmv/.venv/Scripts/python.exe -B ./auditoria_por_etapas/resultados/soporte/regresion_final_01d.py
& ./r1-pmv/.venv/Scripts/python.exe -B ./auditoria_por_etapas/resultados/soporte/concurrencia_pg_01d.py
node --disable-warning=ExperimentalWarning ./auditoria_por_etapas/resultados/soporte/audit01_campos_unicode.cjs
```

El soporte de revisión final volvió a inspeccionar login, validadores, modelo, plantillas, control de roles, configuración y pruebas. No surgió otro defecto inequívoco del producto dentro del contrato definido. Este corte añadió dos pruebas de compatibilidad, soporte, evidencia y conciliación documental. Los tres arreglos de código de aplicación se mantienen identificados en §5. Check y generación de migraciones en seco volvieron a terminar sin incidencias ni cambios. La suite completa del producto queda fuera de la ejecución de este corte.

## 8. Conservación y cierre operativo

El servidor quedó **detenido**, sin listener 8766 ni procesos Python `audit01.py serve` activos al finalizar 01-B. La [persistencia final de 01-B](evidencias/repeticiones/20261109-122609-844456-01-persistencia.json) (preservando también el [corte 01-A](evidencias/repeticiones/20261109-120800-611774-01-persistencia.json)) registra 15 cuentas ficticias (5 iniciales `AUD01` y 10 `AUD01HTTP` de las dos ejecuciones HTTP), 23 filas de intentos, 26 sesiones de auditoría y cero productos/lotes/turnos/ventas, con hashes protegidos sin cambios.

El [cierre01](evidencias/01-cierre.json) y su repetición fechada en `evidencias/repeticiones/` conservan las comprobaciones estructurales de hashes original/00, puerto cerrado, enlaces/artefactos, fuentes de pruebas y búsqueda de secretos conocidos en archivos textuales. Esta búsqueda es acotada, no un escáner universal. Reproducir con `& './r1-pmv/.venv/Scripts/python.exe' './auditoria_por_etapas/resultados/soporte/verificar_cierre_01.py'`; las repeticiones conservan el corte anterior. No son pruebas nuevas de negocio.

No se borraron cuentas, registros ni datos reales. Las sesiones y contadores de auditoría permanecen para continuidad; la sesión del navegador almacenero puede seguir persistida. Eso no equivale a probar expiración de sesión al cerrar navegador. La aplicación solo tiene los cambios propios declarados arriba, sobre el trabajo previo.

### 8.1. Cierre del sublote 01-C

El servidor aislado quedó detenido. El sondeo TCP de 127.0.0.1:8766 devuelve conexión rechazada y la consulta de procesos confirma cero workers del servidor. Las cuentas siguen siendo las 15 de preparación y las 15 tablas comerciales conservan cero filas. Se conservaron las filas de intentos y las sesiones de prueba para continuidad. Las bases original y etapa00 mantienen sus hashes de preparación. Las fuentes de autenticación coinciden con los manifiestos de 01-B y la regresión 01-C. [Cierre reproducible](evidencias/01-C-cierre-20261109.json)

La inspección del entorno encontró que la enumeración de listeners de Windows omitía el puerto mientras aceptaba conexiones. Por ello el cierre comprueba también conexión TCP efectiva y procesos, evitando depender de una única vista del sistema. La búsqueda de secretos en archivos textuales se limita a las cinco claves de fixtures, sus correos y la llave aislada conocidos. Las imágenes se inspeccionaron visualmente. El informe conserva el alcance de cada comprobación.

Repetir el cierre con el servidor detenido y un nombre de archivo nuevo mediante el soporte siguiente.

```powershell
& ./r1-pmv/.venv/Scripts/python.exe -B ./auditoria_por_etapas/resultados/soporte/verificar_cierre_01c.py --archivo 01-C-cierre-20261109-repeticion.json --cursor E01-B-03
```

### 8.2. Conservación final de etapa 01

El servidor HTTP de la auditoría quedó detenido y el PostgreSQL temporal fue detenido y eliminado por su soporte. La continuidad conserva 15 cuentas ficticias, 24 filas de intentos y las sesiones generadas. La fila adicional corresponde al caso IDN de 01-D. Se comprobaron las 15 tablas comerciales vacías y los hashes de las bases original y etapa00. Los resultados históricos conservan el código y contexto que verificaron en su fecha. [Verificación final de etapa](evidencias/01-D-cierre-final-20261109-verificado.json)

El primer cotejo operativo 01-D obtuvo 27/28 comprobaciones por una comparación que omitía una variante de salto de línea al final del archivo antiguo de pruebas. El contenido de los métodos anteriores coincide con su SHA256 al conservar las tres líneas finales originales. Se corrigió únicamente ese cotejo del soporte y se generó un manifiesto nuevo. [Primer cotejo](evidencias/01-D-cierre-final-20261109.json)

Repetir el cierre final con un archivo nuevo.

```powershell
& ./r1-pmv/.venv/Scripts/python.exe -B ./auditoria_por_etapas/resultados/soporte/verificar_cierre_01d.py --archivo 01-D-cierre-repeticion-20261109.json
```

## 9. Hallazgos abiertos y punto de inicio de etapa 02

La actividad de auditoría de esta etapa está completada con los estados de requisito anteriores. Los trabajos siguientes quedan asignados y conservan sus evidencias y alternativas en el anexo de traspaso.

| Trabajo pendiente | Estado, prioridad y siguiente verificación | Destino |
|---|---|---|
| DOC-01-04 / PROP-E01-T-TRAFICO / `02:277` | INCUMPLE en aplicación, P1. Obtener configuración efectiva del punto de entrada. Acordar capa, presupuesto, ventana, IP fiable, respuesta y tratamiento de redes compartidas. Despliegue real NO EXAMINADO. | Etapa15, SEC-15-TRAFICO-01 |
| DOC-01-05 / RETENCION | EXTRA SIN REQUISITO de plazo, P2. Elegir retención y el significado de contadores 1–4 antiguos. Probar limpieza de datos ficticios preservando bloqueos vivos y concurrencia. | Etapa15, SEC-15-RETENCION-01; LOG-01 en02 |
| DOC-01-06 / ADMIN | PARCIAL, P1. Elegir si se requiere el portal y cómo se limita/protege. Sus puertas y cinco fallos están observados. Auditar permisos por modelo y controles compartidos según contrato. | Etapa15, SEC-15-ADMIN-01 |
| DOC-01-07 / observabilidad | NO EJECUTADO análisis estadístico de tiempos, P2. Examinar observabilidad productiva y filtrado de `record.exc_info` con datos ficticios. | Etapa15, SEC-15-OBS-01 |
| AUTH-01/CA-04, RN-29 | PARCIAL transversal, P1. Completar rutas/objetos y datos de cada módulo, denegación sin exposición ni mutación. | Etapas02–14 y revisión15 |
| DOC-01-02/03, correo320/254, IDNA | PROPUESTO / DECISIÓN PENDIENTE, P2. Complementos de criterios y alternativas en el anexo. Revisarlos con las altas y cambios de personal para mantener un contrato común. | Etapa02, antes de modificar normalización/alta |
| S1-AUTH01-REV y selección release | Aceptación humana independiente y selección comercial pendientes. Los siete criterios conservan el resultado técnico de este informe. | Etapa17 / responsable de producto |

**Cursor exacto para el nuevo chat · ETAPA-02 / HU-AUTH-03 / CA-01 / `08:41` / `03:69` / GET y POST `/salir/`.** Crear datos aislados propios de02. VENDEDOR autenticado, turno propio OPEN, sin borrador ACTIVE con líneas. Recorrer menú Cerrar sesión, advertencia y confirmación. Comprobar sesión invalidada, regreso al ingreso, turno abierto y propietario conservados. Luego CA-02 incorpora un borrador con líneas para cancelar/confirmar. AUTH-04a/04b/05, USR-01..06 y LOG-01 deben clasificarse antes de probarlos, según el prompt02 y el protocolo común.
