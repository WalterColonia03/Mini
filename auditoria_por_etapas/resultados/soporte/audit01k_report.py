"""Write the scoped local-demo closure only after the recorded checks passed."""
from pathlib import Path
import hashlib
import json
import re

ROOT=Path(__file__).resolve().parents[3]
RESULTS=ROOT/'auditoria_por_etapas/resultados'
OUT=RESULTS/'evidencias/01-K-20261115'
def read(name): return json.loads((OUT/name).read_text(encoding='utf-8'))
for name, count in [('navegador-01k.json',26),('chrome-roles.json',18),('chrome-efecto-entre-roles.json',5),('literales-browser.json',79)]:
    checks=read(name)['checks']
    assert len(checks)==count and all(c['ok'] for c in checks), name
assert 'Ran 139 tests' in (OUT/'identity-final-venv.txt').read_text(encoding='utf-8-sig')
expiry=read('expiracion-real-browser.json')
assert expiry['ok'] and expiry['espera_real_segundos']>=900
assert read('expiracion-real-despues.json')['failures']==0
assert read('expiracion-real-despues.json')['locked_until'] is None
build=read('build-final.json')
planhash=hashlib.sha256((ROOT/'08_Historias_de_Usuario.md').read_bytes()).hexdigest()
original=(RESULTS/'ETAPA-01.md').read_text(encoding='utf-8')
archive='evidencias/01-J-20261115/antes/auditoria_por_etapas__resultados__ETAPA-01.md'
assert (RESULTS/archive).exists()
anchors='\n'.join(f'<a id="{x}"></a>' for x in dict.fromkeys(re.findall(r'<a id="([^"]+)"',original)))
report=f'''# ETAPA 01 · Ingreso y bloqueo · cierre académico local

<a id="vigente-01-k"></a>

**15/11/2026 · 01-K · Primera pasada, revisión y profundización. CERRADA Y APROBADA al 100 % para el alcance de demostración local definido aquí: 2 HU, 7 CA, 4 CP y 21 grupos de interfaz de entrada inventariados.** No es la segunda pasada global. La confirmación del responsable conserva etapa01 = ingreso/bloqueo y etapa02 = sesión/personal. La siguiente revisión es `02-LOCAL-TRAZABILIDAD-01`.

La aprobación se refiere al ingreso, el bloqueo y las barreras de entrada por rol especificadas en los cuatro casos. No aprueba el contenido ni las operaciones internas de las pantallas de destino. La regresión ampliada tuvo **663/666 pruebas correctas y3 fallos externos**; esos resultados se conservan y no se presentan como una suite aprobada ni como cierre del sistema completo.

## Contexto, autoridad y fuentes

El responsable aclaró que se trata de un proyecto universitario: el profesor representa al dueño de un minimarket que pasa del cuaderno a un sistema de control. Revocó los extras de01-J y exige correspondencia literal HU/CA/CP ↔ interfaz. Esta instrucción autoriza la retirada y las correcciones acotadas; ni los informes ni una propuesta autorizan funciones nuevas. [Decisión completa y escenario de factura asignado a ventas](soporte/01-K-alcance-local.md).

Se leyeron protocolo común y continuidad, estado existente, HU-AUTH-01/02, RN-17/RN-29 y contratos pertinentes de08; se contrastaron01/02/14/16/21, rutas, formularios, servicios, modelos, plantillas, autorización y pruebas.07/09/03 son vistas regeneradas, no fuentes independientes. El archivo `PLANIFICACION_SCRUM_R1PMV.xlsx` no está en la raíz vigente y no se usó ni modificó.14 y estimaciones permanecen sin cambios; no se añadieron HU ni CA nuevos. Catálogo vigente:74HU,287criterios y113casos escritos, sin confundirlos con ejecuciones.

- HEAD `{build['git_head']}`; build de{build['fuentes_n']} fuentes `{build['build_sha256']}`. [Manifiesto](evidencias/01-K-20261115/build-final.json). El árbol incluye cambios anteriores ajenos a esta revisión; no se restauró el repositorio.
- 08 SHA-256 `{planhash}`. Los literales se ejecutaron con la versión guardada en `literales-browser.json`; el cierre modifica estados/evidencias y no cambia los literales probados. [Validación de cierre](evidencias/01-K-20261115/cierre.json).
- Windows, Python3.12.10, Django5.2.18, Chrome157.0.8103.78, HTTP loopback127.0.0.1:8800, DEBUG=False y estáticos WhiteNoise. SQLite propio en `datos/01-K-20261115`, pruebas Django en memoria y PostgreSQL18.4 efímero. No se carga `.env`;10cuentas ficticias iniciales, claves aleatorias y cookies independientes.
- La base principal mantiene SHA-256 `{build['documentos_y_bases']['r1-pmv/r1_pmv.sqlite3']}`. No se migró ni restauró. La diferencia respecto de huellas mucho más antiguas ya existía al comenzar01-H y su causa no se atribuye a este sublote.

## Planificación → ejecución

| Criterio seleccionado | Caso / requisito | Evidencia y observado | Resultado |
|---|---|---|---|
| AUTH-01/CA-01 | CP-HU-AUTH-01-001, RN-29 | Tres roles activos ingresan con correo normalizado, llegan a inicio y conservan sesión al recargar; `chrome-roles.json`, `http-probes.json`, identity139 | CUMPLE |
| AUTH-01/CA-02 | CP-HU-AUTH-01-002 | Correo inexistente y clave incorrecta: «Correo o contraseña incorrectos», sin sesión ni distinción visible; literales79 | CUMPLE |
| AUTH-01/CA-03 | CP-HU-AUTH-01-002 | Cuenta inactiva con clave correcta recibe exactamente el mismo mensaje; sin sesión | CUMPLE |
| AUTH-01/CA-04 | CP-HU-AUTH-01-003, RN-29 | Vendedor→alta producto; almacenero→cobro; admin→apertura caja; visitante→historial. GET/POST con CSRF y datos poblados;31combinaciones adicionales×2métodos, sin exposición ni cambios de tablas de negocio/cuentas. Pruebas `test_audit01k_permissions.py` y cruce Chrome5 | CUMPLE para las barreras de entrada; propiedad de objetos y operaciones completas en sus etapas |
| AUTH-02/CA-01 | CP-HU-AUTH-02-001, RN-17 | Quinto fallo fija15min después de validar clave; contador compartido en BD, carreras PG5 y pruebas de reloj | CUMPLE |
| AUTH-02/CA-02 | CP-HU-AUTH-02-001 | Otra sesión con clave correcta sigue bloqueada; minutos redondeados hacia arriba, mínimo1; reintento no extiende plazo; ingreso de otros roles no lo libera | CUMPLE |
| AUTH-02/CA-03 | CP-HU-AUTH-02-001 | Frontera899/900s controlada y acceso real posterior a {expiry['espera_real_segundos']:.3f}s de pared:302→inicio; contador0 y plazo nulo | CUMPLE |

Los cuatro CP mantienen sus pasos y resultados esperados. La precisión literal se integra bajo sus CA existentes en08, por instrucción expresa de alinear la demostración. No se rebaja un criterio para justificar un fallo. El porcentaje refiere a estos requisitos y casos finitos, no a todas las combinaciones imaginables de módulos ajenos.

## Comportamiento → planificación: inventario de entrada

Todos los literales y variables están en [HU-AUTH-01](../../08_Historias_de_Usuario.md#HU-AUTH-01) y [HU-AUTH-02](../../08_Historias_de_Usuario.md#HU-AUTH-02); esta tabla permite localizar el elemento observado sin duplicar una fuente de textos editable.

| Grupo | Pantalla / acción / salida | Respaldo y clasificación |
|---|---|---|
| U01 | Marca «Minimarket», subtítulo y enlace a `/` | AUTH01/CA01, CP001; presentación seleccionada |
| U02 | Título de documento «Ingresar — Sistema de gestión» | AUTH01/CA01, CP001; seleccionado |
| U03 | «Saltar al contenido», destino `#contenido`, foco de teclado | AUTH01/CA01, CP001; seleccionado |
| U04 | Introducción y bienvenida exactas | AUTH01/CA01, CP001; seleccionado |
| U05 | Explicación de operaciones por puesto | AUTH01/CA01/04, RN29; solo acceso, no aprobación de destinos |
| U06 | Tarjeta Administrador y descripción | AUTH01/CA01/04, CP001/003; seleccionado |
| U07 | Tarjeta Almacenero y descripción | AUTH01/CA01/04, CP001/003; seleccionado |
| U08 | Tarjeta Vendedor y descripción | AUTH01/CA01/04, CP001/003; seleccionado |
| U09 | «Acceso seguro», «Iniciar sesión», ayuda | AUTH01/CA01/02/03, CP001/002; seleccionado |
| U10 | Correo, etiqueta, placeholder, valor conservado y longitud | AUTH01/CA01/02/03, CP001/002; seleccionado |
| U11 | Contraseña, etiqueta, placeholder, enmascarado, no repoblación | AUTH01/CA01/02/03, CP001/002; seleccionado |
| U12 | Botón POST «Iniciar sesión» | AUTH01/02, cuatro CP; seleccionado |
| U13 | Obligatorio en ambos campos | AUTH01/CA01/02/03, CP002; seleccionado |
| U14 | Formato de correo y carácter nulo | AUTH01/CA01/02/03, CP002; seleccionado |
| U15 | Máximo inclusivo254, error255 y normalización antes de longitud | AUTH01/CA01/02/03, CP002, DOC02-04; seleccionado |
| U16 | Error general idéntico: incorrecta/inexistente/inactiva | AUTH01/CA02/03, CP002; seleccionado |
| U17 | Bloqueo: quinto fallo, minutos variables y otra sesión | AUTH02/CA01..03, RN17, CP001; seleccionado |
| U18 | CSRF oculto, next interno;403técnico/405 sin cuerpo | AUTH01/CA01/04, CP002/003; soporte interno, sin función comercial extra |
| U19 |403 de permisos y404 de ruta inexistente/admin | AUTH01/CA04, CP003, DOC01-06/C01; literales seleccionados |
| U20 | Nota de permisos, pie e iconos decorativos | AUTH01/CA01/04, CP001/003; presentación seleccionada |
| U21 | Inicio/menu según rol y navegación autorizada | AUTH01/CA01/04 y RN29; acceso seleccionado, semántica completa corresponde a módulos destino |

### Campos, rutas y efectos

| Campo | Inicial / formato / límite | Validación, salida y persistencia |
|---|---|---|
| `email` | Vacío en GET; requerido, correo,254máximo tras strip | Se normaliza con casefold; formato/vacío/nulo/exceso no crean contador. No se altera la cuenta. Valores255/319/320/321 rechazados en HTTP;254válido con espacios/mayúsculas ingresa. Unicode y punycode siguen siendo identificadores distintos: no se incorpora una conversión nueva. |
| `password` | Vacío; requerido; texto oculto, sin strip ni nueva política de alta | No se repuebla tras rechazo ni se guarda en texto claro. Literal obligatorio/nulo especificado en08. |
| `csrfmiddlewaretoken` | Generado por framework, oculto | Ausente/incorrecto:403antes de autenticar, contador sin cambio. No se publica su valor. |
| `next` | Opcional, oculto si existe | Destino mismo host/esquema admitido; externo se ignora→inicio; permisos se aplican también en destino. No concede rol ni se persiste como permiso. |

`GET/POST /` = entrada; `GET /inicio/` = destino autorizado; `PUT/DELETE /` con CSRF válido =405, sin CSRF =403. Rutas de `/empleados/`, productos, caja, inventario y ventas se ejercitan como barreras seleccionadas; la gestión de personal y `/salir/` conservan etapa02. `/admin/`, `/admin/login/` y rutas por modelo =404 para visitante/staff/superuser, sin autenticador alternativo. CSS/JS/favicon =200 desde WSGI local. La existencia de CSS estático de Django admin no publica rutas ni modelos.

Persistencia: `LoginAttempt` usa HMAC de correo normalizado, contador y plazo compartidos; éxito conserva fila y pone0. Sesión se crea en servidor con rol y rotación. `IdentityAuditEvent` conserva el mecanismo técnico previamente aceptado; fallo de registro no permite autenticarse. Los eventos contienen identificadores internos: no se afirma anonimización integral. No se añade limpieza automática ni plazo legal de seguridad. Los datos de negocio poblados para CP003 se conservan después de rechazos.

## Cambios, decisiones y recomendaciones

| ID / tipo | Fundamento y beneficio | Riesgo / costo / impacto / estado |
|---|---|---|
|01K-RETIRAR-J, alcance/arquitectura | Revocación explícita del responsable: eliminados diagnóstico de identidad, test01J y configuración nginx de tráfico; Compose vuelve a demostración. Reduce extras sin respaldo | Costo bajo; no se ofrecen esos mecanismos como funciones. EJECUTADA; [huellas de retirada](evidencias/01-K-20261115/retiro-01j.json) |
|01K-LITERAL, diseño/CA/pruebas | La traducción previa decía «menos de254» aunque acepta254. Corregido a «como máximo254»; se detallan textos existentes dentro de HU/CA/CP | Costo bajo, sin migración ni cambio de límite; riesgo de divergencia literal controlado por4tests y79checks. ACEPTADA por instrucción de corregir/alinear, IMPLEMENTADA y VERIFICADA |
|01K-PERMISOS, tarea/pruebas | Completar CP003 con CSRFválido, datos poblados y barreras adicionales | Costo bajo; no confundir esta muestra con validación de operaciones internas. VERIFICADA |
|01K-RECOMENDACIONES-EXTERNAS | Las propuestas de tráfico, alojamiento, mantenimiento externo y política legal de bitácora no corresponden al proyecto aclarado | No seleccionadas para demo; no quedan como decisiones o bloqueos de01. No se acepta una propuesta solo por estar escrita |
|01K-FACTURA, necesidad de otraHU/RN/CA | Caso100IncaKola3L, factura de empresa recuperada2meses después por RUC/número/fecha, sin borrado | Beneficio: recuperación documental. Costo/arquitectura deben estimarse en ventas; riesgo: confundir constancia interna con factura fiscal. REGISTRADA para conciliación tributaria/funcional posterior, sin promesa de emisión fiscal aquí |

No se añadieron funciones, límites porIP, roles ni políticas de contraseña al ingreso. Las recomendaciones retiradas no se convierten en aceptadas por haber tenido pruebas verdes. Las de otros módulos permanecen bajo su propio alcance.

## Pruebas reproducibles y límites

| Evidencia nueva01-K | Resultado / alcance |
|---|---|
| [identity-final-venv.txt](evidencias/01-K-20261115/identity-final-venv.txt) |139/139 OK, incluye pruebas de otras funciones identity como regresión, no cierre de02 |
| [literales-permisos.txt](evidencias/01-K-20261115/literales-permisos.txt) |9/9 OK:4formulario+5permisos, incluidas en139. Primer intento asumió erróneamente merma prohibida al admin; RN29 la permite. Se corrigió la expectativa de prueba, no el producto; log fallido conservado |
| [navegador-01k.json](evidencias/01-K-20261115/navegador-01k.json) |26/26 Chrome,1366/390/320px, teclado, estilo, errores y límites visuales |
| [chrome-roles.json](evidencias/01-K-20261115/chrome-roles.json) / [cruce](evidencias/01-K-20261115/chrome-efecto-entre-roles.json) |18/18 +5/5; tres roles, rechazo uniforme, bloqueo entre contextos; subconjuntos solapados |
| [literales-browser.json](evidencias/01-K-20261115/literales-browser.json) |79/79: contraste exacto UI/planificación y estados. Capturas sin contraseñas; inspección visual de pantalla de bloqueo |
| [http-probes.json](evidencias/01-K-20261115/http-probes.json) |8grupos HTTP/ORM:CSRF, métodos,254/255 y más, destino, revocación puntual, ausencia de límite porIP y estáticos. La sonda de salida/desactivación no aprueba toda02 |
| [postgresql-01k-latest.json](evidencias/01-K-20261115/postgresql-01k-latest.json) |5/5escenarios: primera fila, cinco fallos, éxito→fallo, fallo→éxito y ausencia de bypassadmin. PG18.4; no se atribuye ejecución a PG17 |
| [expiración real](evidencias/01-K-20261115/expiracion-real-browser.json) / [antes](evidencias/01-K-20261115/expiracion-real-antes.json) / [después](evidencias/01-K-20261115/expiracion-real-despues.json) |Espera real del mismo sublote, sin mover reloj ni fecha en BD;302→inicio y contador0. Tiempo de pared; no se afirma medición monotónica completa |
| [regresion-final.txt](evidencias/01-K-20261115/regresion-final.txt) / [triage](evidencias/01-K-20261115/triage-regresion.json) |663/666 OK,3FAIL preservados. Caja y FEFO suponen timestamps distintos; reproducción controlada confirma fragilidad ante empates. El orden del borrador/recibo puede diferir del orden de captura si empatan: pendiente propio de10/12. Diez archivos implicados idénticos a baseline01K; no se atribuyen estos fallos al mensaje del login ni se declaran resueltos |
| [django-check.txt](evidencias/01-K-20261115/django-check.txt) / [migrations-check.txt](evidencias/01-K-20261115/migrations-check.txt) |Sin incidencias; sin migraciones nuevas |

El intento inicial con `python` global carecía de Django y no ejecutó pruebas; se conserva su log y se usó el intérprete `.venv` del proyecto. `test_reset_demo_db` se excluye por ser comando de reinicio ajeno a01; no se lo cuenta aprobado. No se suman conjuntos solapados para inventar cobertura.

Desde `r1-pmv` en PowerShell:

```powershell
$env:PYTHONPATH = (Resolve-Path '../auditoria_por_etapas/resultados/soporte').Path
$labels = Get-ChildItem identity -Filter 'test*.py' | Where-Object Name -ne 'test_reset_demo_db.py' | ForEach-Object {{ 'identity.' + $_.BaseName }}
& './.venv/Scripts/python.exe' -X utf8 -B manage.py test @labels --settings=audit01k_settings -v 1
& './.venv/Scripts/python.exe' -X utf8 -B manage.py check --settings=audit01k_settings
& './.venv/Scripts/python.exe' -X utf8 -B manage.py makemigrations --check --dry-run --settings=audit01k_settings
```

Los runners `soporte/audit01k*.py` y `.cjs` detallan fixtures, solicitudes y aserciones; se ejecutaron solo en datos01K. Para repetir navegador usar una carpeta/identificador de auditoría nuevo, `prepare`, `collectstatic`, servidor `serve --no-static`, y después navegador/roles/cruce/literales/HTTP. No volver a preparar la evidencia cerrada ni tocar la base principal. El runner PG crea y retira su clúster efímero. [Cierre de entorno y conservación](evidencias/01-K-20261115/cierre.json).

## Evidencia anterior y cursor exacto

Se conserva [el informe anterior completo]({archive}), sus pruebas y capturas.01I revalidaba otro build y tenía decisiones de despliegue: esas conclusiones de alcance fueron sustituidas por la aclaración del responsable. El contenido de01J retirado conserva manifiesto de huellas y evidencia histórica de ejecución, sin convertirse en requisitos actuales. [Nota01J](soporte/01-J-decisiones-y-entrega.md).

**Revalidado01K:** interfaz y literales, campos, roles, rechazo, persistencia/CSRF/destino, permisos seleccionados con datos, bloqueo/expiración, PG18.4 y admin ausente. **Heredado como antecedente, no sumado a las pruebas nuevas:** la espera real y los fallos corregidos de01I, sus decisiones técnicas previas y resultados de otras etapas. **NO APLICA a esta aprobación local:** alojamiento/dominio, contratos comerciales y pruebas de publicación pública. **FUERA DE ESTE CIERRE:** CRUD de personal/salida (02), semántica del tablero y demás operaciones, y caso tributario de ventas. No hay pendiente propio de ingreso dentro del alcance seleccionado.

**Cursor para la próxima sesión:** `02-LOCAL-TRAZABILIDAD-01` → leer protocolo/continuidad con aclaración local, informe02 y HU-AUTH-03 / HU-USR seleccionadas; inventariar de nuevo mensajes/acciones/CA/CP y contrastar evidencia02-E. Revisar allí lo obsoleto del contexto anterior sin heredar aprobación global. Los hallazgos externos de regresión quedan registrados para09/10/12/14; continuar02 no los borra.

### Anclas históricas

Estas anclas conservan navegación desde citas antiguas. Su contenido y estado por fecha están en el informe archivado; el estado vigente es01-K.

{anchors}
'''
(OUT/'documentos-antes-cierre'/'ETAPA-01.md').write_text(original,encoding='utf-8')
(RESULTS/'ETAPA-01.md').write_text(report,encoding='utf-8')

p=RESULTS/'ESTADO_GENERAL.md'
s=p.read_text(encoding='utf-8')
(OUT/'documentos-antes-cierre'/'ESTADO_GENERAL.md').write_text(s,encoding='utf-8')
rows_before=[x for x in s.splitlines() if x.startswith('|') and not x.startswith('| [01]')]
s=re.sub(r'(?m)^\*\*Actualización 01-[EFGHIJ][^\n]*\n\n?', '', s)
header,rest=s.split('\n',1)
note=('**Vigente01-K ·15/11/2026:** Etapa01 **CERRADA Y APROBADA para demostración local**,2HU/7CA/4CP del ingreso/bloqueo. '
      '139/139 identity,79/79 literales Chrome,5/5 escenariosPG18.4 y expiración real. '
      'Regresión ampliada663/666:3fallos externos registrados, sin aprobación global. '
      'No hay pendientes de alojamiento, dominio o contratos para este alcance académico. '
      'El responsable confirmó conservar etapas01y02. **Siguiente cursor `02-LOCAL-TRAZABILIDAD-01`.** '
      '[Informe01K](ETAPA-01.md#vigente-01-k) · [Alcance](soporte/01-K-alcance-local.md).\n\n'
      '**Lectura de estados anteriores:** las filas02–17 conservan evidencia de sus fechas, no se reauditan ni aprueban aquí. '
      'Sus referencias históricas a infraestructura/condiciones comerciales no son bloqueos de la demostración local. '
      'El cursor local acordado01→02 prevalece para la siguiente sesión; la secuencia global anterior queda como antecedente.\n\n')
s=header+'\n\n'+note+rest.lstrip('\n')
s=re.sub(r'(?m)^\| \[01\].*$', '| [01](ETAPA-01.md#vigente-01-k) Ingreso y bloqueo |15/11/2026| Primera pasada profundizada01-K:2HU,7CA,4CP,21grupos de entrada;139/139identity,79/79literales,26+18+5Chrome solapados,5/5PG18.4, expiración real y permisos con datos poblados | **100% CERRADA Y APROBADA para demostración local del alcance definido** | Sin pendientes propios del ingreso; no cierra02 ni operaciones de destinos. Regresión externa663/666, triage de3fallos en09/10/12/14 | `02-LOCAL-TRAZABILIDAD-01` |', s)
assert rows_before==[x for x in s.splitlines() if x.startswith('|') and not x.startswith('| [01]')]
p.write_text(s,encoding='utf-8')
print(json.dumps({'report':'ETAPA-01.md','scope':'2HU / 7CA / 4CP','other_stage_rows_unchanged':True,'plan_sha256':planhash}))
