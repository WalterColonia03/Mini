"""Add the 01-I report and update only its live state and a rule citation."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "auditoria_por_etapas/resultados"
BEFORE = RESULTS / "evidencias/01-I-20261115/documentos-antes"
report_path = RESULTS / "ETAPA-01.md"
status_path = RESULTS / "ESTADO_GENERAL.md"
for path in (report_path, status_path):
    saved = BEFORE / ("auditoria_por_etapas__resultados__" + path.name)
    if hashlib.sha256(path.read_bytes()).digest() != hashlib.sha256(saved.read_bytes()).digest():
        raise SystemExit(f"Cambio concurrente en {path.name}; no se sobrescribe")

adenda = '''# Adenda vigente de ETAPA-01 · 15/11/2026 · 01-I

<a id="vigente-01-i"></a>

**Primera pasada, revisión completa del informe anterior y profundización de ingreso desde `01-I-PERIMETRO-Y-POLITICAS-01`: etapa 01 PARCIAL.** La instrucción de esta sesión autoriza corregir defectos de la auditoría y del producto dentro de este tramo. Se corrigieron el bypass de Django admin, el trabajo de contraseña durante bloqueo, la ausencia de diagnóstico al fallar una inserción de bitácora y la entrega de estáticos en WSGI local. El tráfico agregado, la conservación, el sumidero y el despliegue real siguen abiertos; las etapas de destino no se declaran terminadas.

Se revisó el informe anterior de principio a fin y la existencia de sus 141 enlaces locales a archivos. No se infiere de ello lectura integral de cada anexo ni verificación de enlaces externos. Se conserva literalmente el informe previo debajo de esta adenda: sus observaciones describen sus propios builds. El inventario detalla **2/2 HU, 7/7 criterios y 21/21 grupos de pantalla** identificados; **6/7 CA CUMPLEN en muestra y 1/7 permanece PARCIAL** para autorización global. Las muestras 01-I amplían, pero no aprueban, todos los objetos, rutas, módulos ni una revisión humana independiente. [Inventario actualizado, matriz inversa y decisiones](soporte/01-I-inventario-y-disposiciones.md) · [revisión de evidencia previa](evidencias/01-I-20261115/revision-evidencia-anterior.json).

## 01-I.1 · Línea base, decisiones y conservación

- Se aplicaron `PROTOCOLO_COMUN.md` y `CONTINUIDAD_Y_SEGUNDA_PASADA.md`; esta es la **primera pasada profundizada de etapa 01**, no la segunda pasada global. `identity/urls.py`, vistas, formularios, servicios, modelos, plantillas y pruebas se trazaron en ambos sentidos con visitante y tres roles; Django admin, tráfico, registros y estáticos se trataron como superficies separadas.
- HEAD `7816d3328115cf5aa5bcdd0985fffd795b3ae084`; al comenzar había **205 cambios preexistentes** según `git status` completo y se preservaron. Build de 218 fuentes `856bd31db0759f0b9c6c71f171b704253f46da6940c0f1ab46e65861ef61362e` → 219 fuentes `4e7ffd8b7a15e2eac15be685343fe5f485fdbbff8c17251a86a57bb81ceb8e23`; método y lista en manifiestos. `.dockerignore` y `README.md` no forman parte del hash de fuentes y se registran aparte. [Antes](evidencias/01-I-20261115/build-antes.json) · [final](evidencias/01-I-20261115/build-final.json) · [nueve archivos de este sublote](evidencias/01-I-20261115/cambios-producto.json) · [diff respecto a su propia línea base](evidencias/01-I-20261115/cambios-producto.diff).
- `08` SHA-256 de entrada `ad5e92486716bd32fe496dccdb54999cbbba530ddf03d799fc12c8415cc21aad` y salida `57e9fcbb4d80385e2c89445eb1edb8cdf35631237bb1ad99b7c48ef0188a609c`: se actualizaron resultados de cinco casos existentes y se precisaron RN-17 y DOC-01-06. Se regeneraron y comprobaron `07/09/03` desde esa fuente; el catálogo declara 74 HU, 287 criterios y 113 casos escritos, no 287 ejecuciones. `02`, `16` y `21` incorporan las decisiones vigentes; los documentos anteriores se conservaron en [respaldo](evidencias/01-I-20261115/documentos-antes/08_Historias_de_Usuario.md).
- `01I-ADMIN-01` adopta despublicar `/admin/` en la aplicación comercial: era una alternativa ya prevista por DOC-01-06/C-01, corroborada por el bypass y la instrucción expresa de corregirlo. Deja sin esa interfaz a soporte; si se necesita, deberá diseñarse un canal separado seguro. `01I-HASH-01`, `01I-LOG-01` y `01I-STATIC-01` se aceptan como correcciones técnicas de defectos reproducidos, con riesgos y límites en el anexo. No se acepta automáticamente ninguna propuesta pendiente ni se inventan políticas comerciales. [Fallas antes](evidencias/01-I-20261115/regresion-antes.txt) · [bitácora antes](evidencias/01-I-20261115/bitacora-antes.txt) · [regresión final](evidencias/01-I-20261115/regresion-seguridad-final.txt).
- La base principal tenía al inicio SHA-256 `83e79733798e2e00af2b8f11b7a23aac2b1727d16707d078873d5a36d441bb6c`, ya distinta del hash `c60b4027...` registrado por 01-G/15-A antes de 01-H. Su origen es desconocido. Esa base y las demás bases protegidas mantuvieron sus huellas en 01-I; no se restauraron ni modificaron. [Cierre](evidencias/01-I-20261115/cierre-operativo.json).

## 01-I.2 · Resultado y evidencia reproducible

| Tramo | Resultado y alcance |
|---|---|
| Visitante y tres roles | Chrome verificó ingreso con correo normalizado, sesión persistida, mensaje uniforme para clave incorrecta, inactiva e inexistente, y denegación entre roles. La suite creó datos comerciales ficticios y verificó que rechazos GET/POST con CSRF no los modificaran. **AUTH-01/CA-04 sigue PARCIAL para permisos globales**. [Roles final, 18/18](evidencias/01-I-20261115/chrome-roles-final.json) · [efectos, 5/5](evidencias/01-I-20261115/chrome-efecto-entre-roles-final.json) · [suite focal](evidencias/01-I-20261115/regresion-seguridad-final.txt). |
| RN-17: cinco fallos, otra sesión y tiempo | Cinco fallos bloquean 15 minutos; otro contexto con clave correcta sigue denegado y el ingreso de los otros roles no libera la cuenta. El servicio no ejecuta hash cuando el bloqueo sigue vigente, para identificadores conocidos o desconocidos; el quinto plazo se fija después del cálculo. Los ensayos de reloj controlado no sustituyen una prueba de volumen ni de ausencia de canal temporal. [Seguridad, 11/11](evidencias/01-I-20261115/regresion-seguridad-final.txt) · [PG 18.4, 5/5 escenarios](evidencias/01-I-20261115/postgresql-01i-latest.json). |
| Expiración real | Quinto evento 10:41:21 Lima, vencimiento 10:56:21, ingreso y recarga correctos 10:56:24, **902,941 s** de reloj de pared; contador 0 y plazo nulo. Se midieron monotónicamente los últimos **598,197 s**, no los 15 minutos completos. El quinto fallo y primera denegación se hicieron en build intermedio; se reinició el servidor con la corrección de bitácora y se verificó que el mismo bloqueo persistía en build final antes del vencimiento y que después el ingreso funcionaba. [Antes](evidencias/01-I-20261115/antes-espera.json) · [build final bloqueado](evidencias/01-I-20261115/pre-expiracion-build-final.json) · [espera](evidencias/01-I-20261115/espera-real-01i.json) · [contador](evidencias/01-I-20261115/despues-espera.json). |
| CSRF, rutas y sesión | CSRF ausente/inválido 403 sin nuevos intentos; PUT/DELETE 405; límites de correo y `next` externo comprobados en HTTP del build intermedio, y pruebas existentes reejecutadas en build final. No se demuestran cookies ni proxy/TLS de producción. [HTTP](evidencias/01-I-20261115/http-probes.json) · [regresión integrada](evidencias/01-I-20261115/regresion-integrada-final.txt). |
| Django admin | El bypass que 01-H observó en su build se corrigió quitando las rutas comerciales: staff bloqueado no obtiene sesión, `/admin/` responde 404; superuser vendedor conserva su rol y obtiene 403 en empleados. **DOC-01-06/C-01 cumple en esta muestra de aplicación; perímetro y canal real no examinados.** [Navegador final, 4/4](evidencias/01-I-20261115/admin-final.json) · [PG concurrente](evidencias/01-I-20261115/postgresql-01i-latest.json). |
| Bitácora | Antes, una excepción al insertar el evento de rechazo se descartaba sin diagnóstico. Con fallo inyectado se registra la clase de error sin el mensaje sensible y se preserva el rechazo; si ambos canales fallan, sigue denegado pero puede perderse el diagnóstico. No acredita sumidero durable, retención ni minimización real. [Antes](evidencias/01-I-20261115/bitacora-antes.txt) · [después](evidencias/01-I-20261115/regresion-seguridad-final.txt). |
| Presentación y estáticos | CSS, JS y favicon 200 en WSGI crudo con WhiteNoise y `collectstatic` aislado. Chrome intermedio 26/26; en build final foco/errores 6/6 a 1366/390/320 px. La duda 01-H sobre solapamiento del salto no se reproduce en esas muestras. No se construyó la imagen Docker: [motor no disponible](evidencias/01-I-20261115/docker-estado.json); producción, proxy y lectores de pantalla **NO EJECUTADOS**. [HTTP](evidencias/01-I-20261115/http-probes.json) · [Chrome intermedio](evidencias/01-I-20261115/navegador-01i.json) · [foco final](evidencias/01-I-20261115/foco-y-errores-final.json) · [captura 320](evidencias/01-I-20261115/navegador/01-I-formulario-error-final-320.png). |

La regresión integrada pasó **657/657 en 101,733 s** en SQLite `:memory:`: incluye identity (salvo `test_reset_demo_db`), cash, catalog, inventory, sales y app_platform; no se ejecutó reinicio de datos demo. Las 11 pruebas focales están incluidas, no son 11 adicionales. PG 18.4 ejecutó creación concurrente de primera fila, cinco fallos, ambos órdenes éxito/fallo y ruta admin concurrente; es una muestra local, no PG 17 ni producción. Las cifras Chrome son comprobaciones técnicas solapadas, no criterios independientes ni suma de cobertura. [Regresión](evidencias/01-I-20261115/regresion-integrada-final.txt) · [PG](evidencias/01-I-20261115/postgresql-01i-latest.json).

Para repetir las regresiones focales sin la base operativa, desde `r1-pmv`, con dependencias instaladas y sin cargar `.env`:

```powershell
$env:PYTHONPATH = (Resolve-Path '../auditoria_por_etapas/resultados/soporte').Path
& './.venv/Scripts/python.exe' -X utf8 -B './manage.py' test identity.test_audit01i_security --settings=audit01i_settings -v 2
```

Los guiones `audit01i.py`, `audit01i_roles.cjs`, `audit01i_cross_roles.cjs`, `audit01i_espera_real.cjs`, `audit01i_pg.py` y `audit01i_lock_snapshot.py` contienen los pasos; para repetir navegador/PG copiar los soportes a un **identificador nuevo**, cambiar directorios y puertos y preparar otra base ficticia. El primer intento de navegador por discrepancia del encabezado HMAC se conserva [incompleto](evidencias/01-I-20261115/navegador-intento-hmac-incompleto.json): fue fallo del guion de prueba, se corrigió y repitió; no se atribuye al producto. Las etiquetas `HTTP-01-IET-ROOT` y `HTTP-08-STATICFILES-HANDLER` son nombres heredados del guion; la sonda se ejecutó con **WSGI crudo y WhiteNoise**, no con StaticFilesHandler.

La primera [validación documental](evidencias/01-I-20261115/validacion-intento-orden-windows.json) comparó el hash agregado usando orden lexicográfico de cadenas en lugar del orden de rutas Windows del manifiesto. Los hashes individuales coincidían; se corrigió el validador para respetar el orden registrado y se repitió. No fue un cambio de producto. [Resultado final](evidencias/01-I-20261115/validacion-final.json).

## 01-I.3 · Pendientes y cursor

Persisten como **propuesta o investigación**, con beneficio, riesgo, costo e impacto en el [anexo](soporte/01-I-inventario-y-disposiciones.md): política y presupuesto de tráfico distribuido y confianza de proxy/NAT; acumulación, protección y plazos de `LoginAttempt`/eventos; privacidad de identificadores y metadatos; colisiones Unicode/punycode; eventual canal técnico de soporte; construcción de imagen, TLS/proxy, PG 17, carga y accesibilidad asistida reales. Seis identificadores ficticios obtuvieron 200 sin límite agregado observado: no es prueba de carga ni prueba de que exista protección en el perímetro real.

La base aislada final contiene 14 cuentas ficticias, 12 sesiones y 53 eventos, con tablas comerciales vacías; los casos de negocio poblados se realizaron aparte en memoria. Se retiraron solo los dos archivos temporales propios de contraseñas ficticias; la llave ficticia queda en datos ignorados. Puertos 8796 y 64735 cerrados; 47 archivos textuales de evidencia no contienen los 15 secretos ficticios conocidos examinados. No se afirma escaneo universal ni OCR. [Estado ORM](evidencias/01-I-20261115/orm-final.json) · [cierre](evidencias/01-I-20261115/cierre-operativo.json).

**Cursor local exacto `01-J-PERIMETRO-RETENCION-IDNA-01`:** obtener hechos de topología, necesidad de soporte, volumen y conservación; diseñar y revalidar límite agregado, ciclo de vida/privacidad de registros e IDNA con datos aislados; ejecutar build Docker, proxy/TLS y PG 17 cuando exista entorno representativo. Mantener `AUTH-01/CA-04` parcial hasta cubrir rutas y objetos faltantes, y no inventar decisiones. **Cursor global de primera pasada `16-NORMATIVA-BASELINE-01`**, después 17, 00 y segunda pasada global.

---

'''

old_report = report_path.read_bytes()
old_status = status_path.read_bytes().decode("utf-8")
line_ending = "\r\n" if "\r\n" in old_status else "\n"
old_status = old_status.replace("(sublotes 01-H / 02-E / 07-B / 15-A / revalidaciones)", "(sublotes 01-I / 02-E / 07-B / 15-A / revalidaciones)", 1)
old_citation = "`/admin/login/` elude `RN-18`"
if old_status.count(old_citation) != 2:
    raise SystemExit("Referencias 15-A inesperadas; no se modifica estado")
old_status = old_status.replace(old_citation, "`/admin/login/` elude `RN-17`")
row = (
    "| [01](ETAPA-01.md#vigente-01-i) Ingreso y bloqueo | 15/11/2026 | Primera pasada revisada `01-I`: 2/2 HU, 7/7 CA y 21/21 grupos inventariados; 6/7 CA cumplen en muestra, 1/7 parcial; `657/657` regresión, `11/11` focal incluida, Chrome final 18/18 + 5/5 + 4/4 + 6/6 (conjuntos solapados), PG 18.4 `5/5`; expiración real tras 902,941 s de pared | **PARCIAL**; bypass admin, hash en bloqueo, diagnóstico de bitácora y estáticos WSGI local corregidos y verificados en muestra | Tráfico/retención/observabilidad y canal real abiertos; eventos con identificador; IDNA, imagen Docker, TLS/proxy, PG17 y permisos globales pendientes | `01-J-PERIMETRO-RETENCION-IDNA-01`; global `16-NORMATIVA-BASELINE-01` |"
)
new_status, count = re.subn(r"(?m)^\| \[01\]\(ETAPA-01\.md[^\r\n]*", lambda _: row, old_status)
if count != 1:
    raise SystemExit("No se encontró una única fila de etapa 01")
heading_end = new_status.find(line_ending)
if heading_end < 0:
    raise SystemExit("Estado general sin encabezado")
summary = (
    "\n\n**Actualización 01-I (15/11/2026):** revisión de la auditoría 01 y corrección del bypass de admin, "
    "hash durante bloqueo, diagnóstico de bitácora y estáticos WSGI local; 657/657 pruebas integradas "
    "(11 focales incluidas), PG 18.4 5/5 y vencimiento real tras 902,941 s de pared en secuencia de dos builds. "
    "La etapa sigue PARCIAL: tráfico, retención, privacidad, soporte, IDNA y despliegue real abiertos. "
    "En el resumen y fila históricos de 15-A se corrige únicamente la cita `RN-18` por `RN-17`; "
    "ese hallazgo describe el build anterior y 15 no se declara cerrada. "
    "Cursor local `01-J-PERIMETRO-RETENCION-IDNA-01`; global `16-NORMATIVA-BASELINE-01`. "
    "[Informe 01-I](ETAPA-01.md#vigente-01-i) · [Inventario y disposiciones](soporte/01-I-inventario-y-disposiciones.md).\n"
)
summary = summary.replace("\n", line_ending)
new_status = new_status[:heading_end] + summary + new_status[heading_end:]
report_path.write_bytes(adenda.replace("\n", line_ending).encode("utf-8") + old_report)
status_path.write_bytes(new_status.encode("utf-8"))
print("01-I agregado; informe anterior preservado; estado 01 y cita RN de 15-A corregidos")
