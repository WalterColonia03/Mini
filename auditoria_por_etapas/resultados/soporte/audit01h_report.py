"""Prepend the 01-H report and replace only the stage 01 state row."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "auditoria_por_etapas/resultados"
BEFORE = RESULTS / "evidencias/01-H-20261115/documentos-antes"
report_path = RESULTS / "ETAPA-01.md"
status_path = RESULTS / "ESTADO_GENERAL.md"
for path in (report_path, status_path):
    saved = BEFORE / ("auditoria_por_etapas__resultados__" + path.name)
    if hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(saved.read_bytes()).digest():
        raise SystemExit(f"Cambio concurrente en {path.name}; no se sobrescribe")

adenda = '''# Adenda vigente de ETAPA-01 · 15/11/2026 · 01-H

<a id="vigente-01-h"></a>

**Primera pasada, sublote acotado de profundización desde `01-G-DESPLIEGUE-Y-CONTRATO-01`: etapa 01 PARCIAL.** Se revalidaron ingreso y bloqueo con visitante y los tres roles, navegador, servidor y PostgreSQL. El canal Django `/admin/` sigue eludiendo el bloqueo en aplicación; tráfico, retención y observabilidad son superficies independientes abiertas. No se declaran terminados otros módulos ni se inicia la segunda pasada global.

**Cobertura:** 2/2 HU y 7/7 criterios seleccionados inventariados; 6/7 criterios **CUMPLE en muestra** y AUTH-01/CA-04 **PARCIAL**. Hay 21/21 grupos de pantalla inventariados y trazados, con estados dinámicos no ejecutados expresamente identificados. [Inventario de requisitos, tareas, rutas, campos, textos y propuestas](soporte/01-H-inventario-y-disposiciones.md). La clasificación no certifica seguridad completa ni sustituye revisión humana independiente.

## 01-H.1 · Línea base, autorización y conservación

- Se leyeron completos `PROTOCOLO_COMUN.md` y `CONTINUIDAD_Y_SEGUNDA_PASADA.md`, el estado existente y los fragmentos relevantes de 01/02/03/07/08/09/14/16/21, código y pruebas. No se usa Jira; el XLSX histórico no se localizó. Las entradas 01-A..F y anexos permanecen debajo sin reescribir su evidencia.
- `08` de entrada SHA-256 `ae58b33fe0a50783b7bd1bae2784fd2ad104022f51ed42f73fef49a67cd6e8f3`; salida `ad5e92486716bd32fe496dccdb54999cbbba530ddf03d799fc12c8415cc21aad`. La planificación ya aceptaba las HU y reglas; se añadieron resultados a cinco casos existentes, sin aprobar nuevas políticas, HU o cambios de selección. `07/09/03` se regeneraron de esa huella; `02/16` recogen decisiones y tareas abiertas. El generador valida 74 HU, 287 criterios y 113 casos escritos, no 287 ejecuciones.
- `r1-pmv` HEAD `7816d3328115cf5aa5bcdd0985fffd795b3ae084`, con 205 cambios preexistentes en `git status` incluyendo archivos no versionados. Build de 218 fuentes inventariadas: `37d8b07626519a6b084dbae8521e1e88c9e9c9dd1732d1f587257646e5f77d3d` antes y `856bd31db0759f0b9c6c71f171b704253f46da6940c0f1ab46e65861ef61362e` después. La **única diferencia de fuentes** es `identity/tests.py`; el código ejecutable auditado no cambió. [Manifiesto antes](evidencias/01-H-20261115/build-antes.json) · [final](evidencias/01-H-20261115/build-ultimo.json).
- El único cambio en el repositorio de aplicación corrige una prueba dentro del alcance expresamente pedido: usa los nombres de cookie de Django configurados. Se acepta por ser una corrección técnica del caso de CSRF/sesión ya aceptado, sustentada por un fallo reproducido; no se adopta una política comercial. [Diff aislado](evidencias/01-H-20261115/identity-tests-cambio-01h.diff) · [antes de editar](datos/01-H-20261115/identity-tests-antes.py). No se modificaron vistas, servicios, modelos, rutas ni configuración de producto.
- Al comenzar 01-H, la base principal ya tenía hash `83e79733798e2e00af2b8f11b7a23aac2b1727d16707d078873d5a36d441bb6c`, diferente del `c60b4027d4d2f0953ddcbb828cd6412e9889f9794537de9c50aed7f92fdded58` registrado antes por 01-G y 15-A. **El origen y contenido del cambio son desconocidos**; no se atribuye a una persona ni a una prueba. Se hizo solo lectura SQLite `mode=ro`: `quick_check=ok`, sin fixtures 01-G/deploy encontrados en el conteo acotado. El hash `83e797...` permaneció igual durante 01-H; no se restauró ni modificó esa base. [Observación agregada](evidencias/01-H-20261115/base-principal-observacion.json).
- Entorno: Windows, Python/Django 5.2.18, Chrome 157.0.8103.78 controlado por Playwright, SQLite exclusiva `datos/01-H-20261115/audit.sqlite3` con cuentas ficticias y sin cargar `.env`; suites en `:memory:`; PostgreSQL 18.4 efímero de loopback, `read committed`. Los servidores de prueba y el clúster se detuvieron; no se tocó despliegue ni base operativa. El identificador 01-H evita sobrescribir los archivos 01-G ya presentes en el espacio compartido.

## 01-H.2 · Matriz de ejecución y resultados

| Requisito / prueba | Esperado y observado | Estado / evidencia |
|---|---|---|
| AUTH-01/CA-01; RN-29 | Cada rol entra con correo en mayúsculas/espacios, ve su rol y mantiene sesión al recargar; los tres lo hicieron en contextos separados. | **CUMPLE en muestra**, sin aprobar panel ni operaciones de destino. [Chrome roles](evidencias/01-H-20261115/chrome-roles.json). |
| AUTH-01/CA-02/03 | Clave errónea, correo inexistente y cuenta inactiva devuelven exactamente «Correo o contraseña incorrectos», sin cookie de sesión y con clave vacía. | **CUMPLE en muestra**, no prueba inexistencia de diferencias temporales. [Chrome roles](evidencias/01-H-20261115/chrome-roles.json) · [suite final](evidencias/01-H-20261115/tests-identity-final.txt). |
| AUTH-01/CA-04 | Visitante redirigido; ADMIN 200 en empleados y ALMACENERO/VENDEDOR 403 sin el dato ficticio consultado. La suite comprueba una matriz adicional de GET directos. | **PARCIAL** para permisos globales y POST con datos comerciales preexistentes; la base comercial de esta muestra estaba vacía. [Chrome](evidencias/01-H-20261115/chrome-roles.json) · [ORM final](evidencias/01-H-20261115/orm-final-real.json). |
| AUTH-02/CA-01/02; RN-17 | Cinco fallos, uno iniciado en otra prueba y cuatro posteriores, bloquearon; otro contexto con clave válida vio 15 minutos y no recibió sesión. Reloj controlado ensaya 15/14/2/1 minutos, inactiva/inexistente y que el reintento no extienda plazo. | **CUMPLE en muestra**. Con ADMIN bloqueado, almacenero y vendedor ingresaron sin desbloquearlo y recibieron 403 en empleados. [Chrome](evidencias/01-H-20261115/chrome-roles.json) · [efecto entre roles](evidencias/01-H-20261115/chrome-efecto-entre-roles.json) · [suite](evidencias/01-H-20261115/tests-identity-final.txt). |
| AUTH-02/CA-03; vencimiento | Quinto fallo registrado a las 10:01:38 Lima; vencimiento 10:16:38. A las 10:16:11 la clave válida aún devolvía 1 minuto; a las 10:16:41 ingresó y recargó el panel. El contador quedó 0 y `locked_until` nulo. | **CUMPLE en esta secuencia real**: 903,027 s de reloj de pared desde el evento; los últimos 29,713 s de espera se midieron con reloj monotónico, sin modificar el reloj. No se afirma cronometraje monotónico continuo de los 15 minutos. [Estado previo](evidencias/01-H-20261115/antes-espera.json) · [Chrome](evidencias/01-H-20261115/espera-real-01h.json) · [estado posterior](evidencias/01-H-20261115/despues-espera.json). La espera 01-C se conserva como histórica. |
| CSRF, campos, sesión y destino | CSRF ausente/inválido 403 sin nuevos intentos; PUT/DELETE 405; correo 255/319/320/321 y nulo sin filas; correo válido 254, mayúsculas/espacios y `next` externo terminaron en `/inicio/`; cookie anterior revocada tras salida. | **CUMPLE en los casos ejecutados**. Unicode y punycode crearon dos identificadores separados; decisión IDNA pendiente. [HTTP](evidencias/01-H-20261115/http-probes.json) · [suite](evidencias/01-H-20261115/tests-identity-final.txt). |
| Cookies y pruebas | Antes, el caso existente pasó con nombres predeterminados y falló con nombres configurados (`KeyError`). Después del ajuste pasó en ambos; un Client `secure=True` con Referer válido obtuvo 302 y cookies `Secure`, `HttpOnly`, `SameSite=Lax`. | **VERIFICADO en test aislado**, no se examinó TLS ni proxy real. [Fallo previo](evidencias/01-H-20261115/contract-probes.json) · [default](evidencias/01-H-20261115/cookie-default-despues.txt) · [personalizadas](evidencias/01-H-20261115/cookie-custom-despues.txt) · [HTTPS simulado](evidencias/01-H-20261115/tls-cookies-simulados.json). Una sonda previa sin Referer produjo 403 en HTTPS simulado; no se atribuye al producto como defecto. |
| Concurrencia RN-17 | Primera fila simultánea: una fila y dos fallos; cinco fallos: una fila, contador 5 y vencimiento ~900 s; éxito/fallo en ambos órdenes con espera observada en PG; admin concurrente elude bloqueo. | **5/5 escenarios de sonda completados**, incluyendo uno que demuestra un incumplimiento; PG 18.4, no PG 17 ni ensayo de carga. [PG final](evidencias/01-H-20261115/postgresql-01h-20261115T150253Z.json). El [primer intento incompleto](evidencias/01-H-20261115/postgresql-01h-20261115T150156Z.json) usaba un texto de bloqueo anterior; se ajustó ese detector y el orden de la barrera antes de repetir. |
| DOC-01-06/C-01 y admin | Staff/superuser ficticios bloqueados por `/` entraron por `/admin/login/`, obtuvieron una sesión sin `role_code` y alcanzaron `/inicio/`; superuser pudo abrir la administración de cuentas. | **INCUMPLE en aplicación**; falta examinar canal y restricciones de red reales. [Chrome](evidencias/01-H-20261115/chrome-manifest.json) · [PG](evidencias/01-H-20261115/postgresql-01h-20261115T150253Z.json) · [sonda de servicio](evidencias/01-H-20261115/security-probes.json). |
| Tráfico y Argon2 | Seis POST con identificadores diferentes y cabeceras XFF simuladas devolvieron 200; código/middleware revisados no muestran limitador de aplicación. En cuentas ya bloqueadas se observaron llamadas de hash tanto para conocida como inexistente. | **PARCIAL / INVESTIGACIÓN**: no se probó el punto de entrada real ni se definieron IP fiable, presupuesto o NAT. N=20 por grupo es medición local, no certificación estadística ni de carga. [HTTP](evidencias/01-H-20261115/http-probes.json) · [medición](evidencias/01-H-20261115/contract-probes.json). |
| Retención, eventos y exposición | Sin comando de purga identificado ni plazo aceptado. Muestra ficticia antes del ensayo final: 17 filas de intentos y 39 eventos; de 29 eventos de fallo/bloqueo, 29 tenían identificador tipo correo y 26 metadatos de existencia/estado. `LoginAttempt` sí almacena identificador HMAC de 64 caracteres. | **PARCIAL / INVESTIGACIÓN**: HMAC del contador no anonimiza los eventos; acceso, volumen y plazo reales no examinados. [Privacidad agregada](evidencias/01-H-20261115/privacidad-agregada.json) · [retención](evidencias/01-H-20261115/contract-probes.json). |
| DOC-01-06/C-02/03 | Los eventos de login/logout observados tienen request ID; `/admin/login/` generó 0 eventos en sonda. Filtro y fallo de handler con canarios no dejaron acceder ni expusieron el canario. | **C-02 PARCIAL**, **C-03 CUMPLE en sonda controlada**; no se demuestra sumidero durable, retención ni ausencia universal de filtraciones. [Sondas](evidencias/01-H-20261115/security-probes.json). |
| Estáticos y pantalla | Con handler de prueba, CSS/JS devuelven 200; WSGI simple y DEBUG=False devolvió 404 para cuatro recursos y Chrome mostró formulario sin estilo. | **INCUMPLE en ese montaje local**, despliegue real **NO EXAMINADO**. [HTTP crudo](evidencias/01-H-20261115/raw-wsgi-probe.json) · [Chrome](evidencias/01-H-20261115/chrome-raw-wsgi.json) · [captura](evidencias/01-H-20261115/navegador/01-H-raw-wsgi-sin-estilos.png). Se conserva el [primer intento de guion incompleto](evidencias/01-H-20261115/chrome-raw-wsgi-intento-incompleto.json): el evento de respuesta CSS no apareció en Playwright aunque la petición directa y la consola mostraban el 404; se corrigió la comprobación y repitió. |

La suite focal pasó **83/83 en 18,771 s** después del ajuste de prueba. Chrome registró **26/26**, **18/18**, **5/5** y **4/4** comprobaciones en conjuntos que se solapan, más 2/2 en WSGI sin estáticos: son comprobaciones técnicas, no sumas de CA, y algunas confirman defectos. [Suite](evidencias/01-H-20261115/tests-identity-final.txt) · [Chrome principal](evidencias/01-H-20261115/chrome-manifest.json) · [roles](evidencias/01-H-20261115/chrome-roles.json) · [interacción entre roles](evidencias/01-H-20261115/chrome-efecto-entre-roles.json) · [vencimiento](evidencias/01-H-20261115/espera-real-01h.json).

## 01-H.3 · Decisiones, exclusiones y reproducción

La [tabla de disposiciones](soporte/01-H-inventario-y-disposiciones.md#disposiciones-y-alternativas) explica beneficio, alternativas, riesgo, costo e impacto de admin, límites de tráfico, orden del hash, retención, minimización de eventos, estáticos, IDNA y revisión UX móvil. Solo `01H-TEST-COOKIE` fue aceptada como corrección técnica acotada e implementada/verificada; el resto permanece **PROPUESTA/INVESTIGACIÓN**. En particular, la elección entre deshabilitar o aislar admin depende del uso real de soporte; tampoco se inventan presupuesto por IP, plazo de conservación ni resultado de diagnóstico IDNA. El portal LOG visual continúa futuro.

No se ejecutaron infraestructura/proxy/TLS real, PG 17, acceso con datos reales, CI, carga productiva, cobertura global de permisos, lectores de pantalla ni revisión humana independiente. La captura móvil del salto y su geometría medida difieren; no se declara defecto confirmado sin revisión de foco/transición. La muestra de tiempos no demuestra ausencia de enumeración. Las pruebas antiguas de otros builds se conservan como históricas, no se presentan como ejecuciones 01-H.

Repetición de la suite en base de test `:memory:` desde `r1-pmv`, con la llave aislada de 01-H y sin leer `.env`:

```powershell
$env:PYTHONPATH = (Resolve-Path '../auditoria_por_etapas/resultados/soporte').Path
& './.venv/Scripts/python.exe' -X utf8 -B './manage.py' test identity.tests identity.test_auth_audit01 identity.test_audit13_summary audit01e_probes --settings=audit01h_settings -v 2
```

Los soportes `audit01h.py`, `audit01h_chrome.cjs`, `audit01h_roles.cjs`, `audit01h_cross_roles.cjs`, `audit01h_espera_real.cjs`, `audit01h_lock_snapshot.py`, `audit01h_pg.py` y `audit01h_tls_cookies.py` conservan pasos y comprobaciones. Para repetir HTTP/navegador/PG sin alterar esta evidencia, copiar los soportes con un **nuevo identificador de carpeta y puerto**, actualizar sus rutas constantes de datos/evidencia y preparar una base ficticia nueva; no reutilizar ni resetear la base preservada. El guion ahora rechaza preparar la base 01-H existente después de retirar sus credenciales. La prueba de tiempo real depende de ejecutar primero los cinco fallos y conservar el reloj. Los artefactos preparados antes de cambios están en [documentos antes](evidencias/01-H-20261115/documentos-antes/08_Historias_de_Usuario.md).

Quedaron 10 cuentas ficticias, 17 filas de intentos, 9 sesiones y 45 eventos en la base aislada; tablas comerciales a cero. Se retiró el archivo temporal de contraseñas ficticias y se conservó la llave ficticia solo en la carpeta de datos ignorada. Puertos 8794/8795 cerrados; 48 archivos textuales inspeccionados sin coincidencias con los secretos ficticios conocidos. La inspección no es universal ni OCR. [Cierre operativo](evidencias/01-H-20261115/cierre-operativo.json) · [Validación documental](evidencias/01-H-20261115/validacion-final-2.json).

**Cursor local exacto `01-I-PERIMETRO-Y-POLITICAS-01`:** para `DOC-01-06/C-01`, determinar si soporte necesita `/admin/` y cómo llega el tráfico comercial; con datos ficticios reensayar staff/superuser bloqueados desde ese punto y decidir deshabilitación o canal separado. En paralelo, levantar topología/NAT y presupuesto para `SEC-15-TRAFICO-01`, finalidad/plazo para `SEC-15-RETENCION-01` y protección/minimización de eventos para `SEC-15-OBS-01`; continuar diagnóstico IDNA y despliegue de estáticos sin intervenir datos reales. Si faltan esos hechos, conservar alternativas y avanzar con pruebas independientes. Cursor global de primera pasada: **`16-NORMATIVA-BASELINE-01`**, luego 17, 00 y segunda pasada global.

---

'''

old_report = report_path.read_bytes()
old_status = status_path.read_bytes().decode("utf-8")
line_ending = "\r\n" if "\r\n" in old_status else "\n"
old_status = old_status.replace("(sublotes 01-F / 02-E / 07-B / 15-A / revalidaciones)", "(sublotes 01-H / 02-E / 07-B / 15-A / revalidaciones)", 1)
row = (
    "| [01](ETAPA-01.md#vigente-01-h) Ingreso y bloqueo | 15/11/2026 | Primera pasada `01-H`: 2/2 HU, 7/7 CA y 21/21 grupos inventariados; 6/7 CA cumplen en muestra, 1/7 parcial; `83/83` suite, Chrome 26/26 + 18/18 + 5/5 + 4/4 (conjuntos solapados), PG 18.4 `5/5`; expiración real tras 903,027 s de pared y contador 0 | **PARCIAL**; corrección acotada de prueba de cookies validada, sin cambios de código ejecutable | `/admin/login/` elude bloqueo (`DOC-01-06/C-01` INCUMPLE); tráfico/retención/observabilidad y canal real abiertos; eventos almacenan identificador; IDNA, TLS/proxy reales y PG17 pendientes; base principal ya difería del hash histórico al iniciar 01-H | `01-I-PERIMETRO-Y-POLITICAS-01`; global `16-NORMATIVA-BASELINE-01` |"
)
new_status, count = re.subn(r"(?m)^\| \[01\]\(ETAPA-01\.md[^\r\n]*", lambda _: row, old_status)
if count != 1:
    raise SystemExit("No se encontró una única fila de etapa 01")
heading_end = new_status.find(line_ending)
summary = (
    "\n\n**Actualización 01-H (15/11/2026):** primera pasada acotada de ingreso; 83/83 pruebas, "
    "26/26 + 18/18 + 5/5 + 4/4 comprobaciones Chrome solapadas, 5/5 escenarios PG 18.4 y vencimiento real "
    "tras 903,027 s de reloj de pared. `DOC-01-06/C-01` incumple en aplicación por el bypass de admin; "
    "tráfico, retención, eventos con identificador, IDNA y despliegue real siguen abiertos. "
    "Corrección aceptada y verificada de una prueba de cookies, sin cambiar producto ejecutable. "
    "La base principal ya presentaba una huella distinta de la histórica al iniciar el sublote y conservó su huella durante este. "
    "Cursor local `01-I-PERIMETRO-Y-POLITICAS-01`; global `16-NORMATIVA-BASELINE-01`. "
    "[Informe 01-H](ETAPA-01.md#vigente-01-h) · [Inventario y propuestas](soporte/01-H-inventario-y-disposiciones.md).\n"
)
if heading_end < 0:
    raise SystemExit("Estado general sin encabezado")
summary = summary.replace("\n", line_ending)
new_status = new_status[:heading_end] + summary + new_status[heading_end:]
report_path.write_bytes(adenda.replace("\n", line_ending).encode("utf-8") + old_report)
status_path.write_bytes(new_status.encode("utf-8"))
print("01-H agregado a ETAPA-01 y actualizada únicamente la fila de etapa 01")
