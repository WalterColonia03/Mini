"""Conciliate stage 02 documentation; preserves the original 02-A report once."""
from pathlib import Path
import re

R = Path(__file__).resolve().parents[1]
ROOT = R.parent.parent
p = R / 'ETAPA-02.md'
snapshot = R / 'evidencias/ETAPA-02-corte-02-A.md'
if not snapshot.exists():
    snapshot.write_bytes(p.read_bytes())

inventory = R / 'soporte/inventario_etapa02.py'
s = inventory.read_text(encoding='utf-8')
observations = {
'HU-AUTH-03/CA-01': ('CUMPLE — muestra', '02-A final A01–A02,A20–A22: tres roles, salida sin borrador con/sin turno, conservación de turno y revocación.', 'DOC-02-05: precisar texto sin turno; eventos técnicos en SEC-15-OBS-02.'),
'HU-AUTH-03/CA-02': ('CUMPLE — muestra', '02-A A08–A14: cancelar conserva; confirmar descarta líneas y sesión sin alterar caja/stock. Dos tests de atomicidad incluidos en regresión163.', 'Concurrencia logout/cobro/alta de línea: etapa15, NO EJECUTADA.'),
'HU-AUTH-03/CA-03': ('CUMPLE — muestra', '02-A A03–A06,A13–A19: Atrás, cookie, URL y POST directo, otro vendedor; repetido tras correcciones.', 'Otros motores/dispositivos y peticiones comerciales en vuelo no ejecutados.'),
'HU-USR-01/CA-01': ('CUMPLE — muestra', '02-B B01: ADMIN desde menú; cinco filas y encabezados cotejados con ORM.', 'Sin pendiente funcional en muestra; volumen/paginación no prometidos.'),
'HU-USR-01/CA-02': ('CUMPLE — muestra', '02-B B02: nombre/correo, mayúsculas, espacios, ausencia de resultados y Limpiar.', 'Unicode avanzado y consulta de longitud extrema no ejecutados; etapa15.'),
'HU-USR-01/CA-03': ('CUMPLE — muestra', '02-B B01,B11–B13: estados Activo/Inactivo y acciones cotejados con ORM.', 'Conservar regresión de estado explícito.'),
'HU-USR-02/CA-01': ('CUMPLE — muestra', '02-B B07–B08: alta desde menú, fila guardada e ingreso de empleado en otra sesión.', 'Ningún pendiente del caso muestreado.'),
'HU-USR-02/CA-02': ('CUMPLE — muestra', '02-B B05,B06; fronteras servidor; PG duplicate_email: una fila y ValidationError controlado.', 'IDNA/normalización internacional conservan decisión transversal.'),
'HU-USR-02/CA-03': ('CUMPLE — muestra', '02-B B04–B08; 9 tests de fronteras: vacío, inválido, 120/121,254/255,7,roles manipulados; incluidos en163.', 'Otros alfabetos/dispositivos no ejecutados; no afirmar dominio infinito cubierto.'),
'HU-USR-02/CA-04': ('CUMPLE — muestra', '02-B B07: mensaje y fila de confirmación con nombre,correo,rol,estado coinciden con ORM.', 'Ningún pendiente de muestra.'),
'HU-USR-03/CA-01': ('PARCIAL / decisión documental', '02-B B09 edita nombre completo; servidor prueba120/121. No hay campos separados nombres/apellidos.', 'DOC-02-03: aprobar campo único o definir separación y migración.'),
'HU-USR-03/CA-02': ('CUMPLE — muestra', '02-B B10,B10A y fronteras: colisión rechazada, correo propio y normalización, error accesible y sin mutación.', 'Conservar regresión; política internacional pendiente.'),
'HU-USR-03/CA-03': ('CUMPLE — muestra', '02-B B09: sesión existente muestra rol nuevo, ventas403/inventario200; B14 turno bloquea cambio; PG ambos órdenes rol/apertura.', 'Admin externo y escritores que omitan servicios: etapa15.'),
'HU-USR-04/CA-01': ('PARCIAL / decisión de confirmación', '02-B B11–B12 y estado6: desactiva, revoca sesión, reenvío no reactiva. PG conserva último ADMIN. Botón directo sin segundo paso.', 'E02-REV-06: decidir si botón explícito constituye confirmación o exigir segundo paso; resultado persistente probado.'),
'HU-USR-04/CA-02': ('CUMPLE — muestra', '02-B B12: sesión anterior redirigida; ingreso de inactivo rechazado con mensaje genérico.', 'Peticiones ya en vuelo no cubiertas en todos los servicios; etapa15.'),
'HU-USR-04/CA-03': ('CUMPLE — muestra', '02-B B15 turno/acta; test history conserva venta/líneas/carga/lote/responsables y consulta ADMIN tras desactivar; stock8.', 'Bajas/ajustes y todos los historiales no ejecutados: etapas08/12/14; no aprobar esos módulos.'),
'HU-USR-05/CA-01': ('PARCIAL / decisión de confirmación', '02-B B13: reactiva y admite credenciales habituales, cookie revocada no revive. Acción directa sin segundo paso.', 'E02-REV-06 y DOC-02-BLOQUEO: confirmación y política de desbloqueo por reactivación.'),
'HU-USR-05/CA-02': ('CUMPLE — muestra', '02-B B13: rol ALMACENERO conservado, inventario200 y venta403 después de nuevo ingreso.', 'Otros endpoints se rigen por RN29; etapa14 integración completa.'),
}
start=s.index('OBSERVATIONS = {')
end=s.index('\nCODE = {',start)
s=s[:start]+'OBSERVATIONS = '+repr(observations)+'\n'+s[end:]
s=s.replace('Estado de ejecución de 02-A; empleados continúa en 02-B.', 'Cierre 02-D: 15 CA CUMPLE en muestra, 3 PARCIAL por decisión y 15 PREVISTO/FUTURO. Evidencias 02-A final, 02-B, PostgreSQL y regresión163 enlazadas en el informe.')
inventory.write_text(s,encoding='utf-8')

p.write_text('''# Etapa 02 · Sesión y personal

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
''',encoding='utf-8')

handoff='''# Etapa02 · Cierre y traspaso a03

09/11/2026, America/Lima. Auditoría02 completada con hallazgos y decisiones abiertos; no aprobación íntegra del módulo ni cierre global. [Informe](../ETAPA-02.md) · [Estado](../ESTADO_GENERAL.md) · [33 criterios](ETAPA-02-criterios.md).

Resultado final:163/163 métodos,32/32 comprobaciones de salida,20/20 de empleados y seis escenarios PostgreSQL.15 CA cumplen la muestra,3 parciales por nombres/apellidos y confirmación de desactivar/reactivar,15 futuros. Defectos inequívocos reproducidos y corregidos: reenvío de estado, tres carreras, atomicidad borrador/sesión y referencias accesibles de errores. No confundir inspección, servidor, navegador y concurrencia. Los cambios FIX-E02-01..07 ya existían en02-A; modificaciones posteriores están identificadas en el informe.

Pendientes con destino: SEC-15-OBS-02 registro técnico de eventos R1 (INCUMPLE aplicación), SEC-15-CONC-02 peticiones en vuelo/logout-cobro/admin externo, SEC-15-LIMITES-02 internacionalización/volumen/dispositivos, HIST-12/14 historial completo; decisiones DOC-02-03,04,05/BLOQUEO y E02-REV-06. No se implementaron funciones futuras. No hace falta repetir02 para iniciar catálogo; conservar estados abiertos en seguimiento.

Bases02-A y02-B retenidas, servicios detenidos; original y bases previas sin alteración.02-B deja cuatro sesiones ficticias en su base aislada, no afirmar cero. No ejecutar audit02.py prepare --reset ni run_live_audit02.py contra bases conservadas. Nuevos soportes crean bases por ejecución. No usar verificar_cierre02a.py para sobrescribir evidencia histórica: usar verificar_cierre02_final.py.

Texto para nuevo chat:

> Trabaja en C:/Users/walte/OneDrive/Imágenes/planificacion_limpia. Ejecuta auditoría etapa03, categorías y productos. Lee completo auditoria_por_etapas/PROTOCOLO_COMUN.md, resultados/ESTADO_GENERAL.md y anexos/ETAPA-02-cierre-y-traspaso.md. Etapa02 está auditada con hallazgos abiertos, no 100% aprobada. Primer cursor: HU-CAT-01/CA-01 (08:166), ADMIN desde menú de catálogo→GET /productos/categorias/. Inventaría antes HU/CA/RN/tareas y superficie, contrasta planificación↔comportamiento con navegador y datos nuevos aislados, otros roles y servidor. Conserva cambios preexistentes y bases00/01/02; atiende DOC-00-04/14 sin inventar decisión. Audita solo03, corrige defectos inequívocos, documenta alternativas no inferibles y actualiza ETAPA-03.md/ESTADO_GENERAL.md con evidencia y cursor.
'''
(R/'anexos/ETAPA-02-cierre-y-traspaso.md').write_text(handoff,encoding='utf-8')

p=R/'ESTADO_GENERAL.md';s=p.read_text(encoding='utf-8')
start=s.index('**Etapa 02 EN CURSO');end=s.index('\n\n| Etapa',start)
s=s[:start]+'**Etapa02: AUDITORÍA COMPLETADA CON HALLAZGOS Y DECISIONES ABIERTOS ·02-D.** 163/163 métodos,32/32 salida,20/20 empleados y6 escenarios PostgreSQL.15 CA cumplen muestra,3 parciales,15 futuros; eventos técnicos R1 siguen INCUMPLE en aplicación. Próximo cursor **ETAPA-03 / HU-CAT-01/CA-01 (08:166), ADMIN → GET /productos/categorias/**. [Informe02](ETAPA-02.md) · [Traspaso03](anexos/ETAPA-02-cierre-y-traspaso.md). Se conservan hallazgos y cierre de01.'+s[end:]
lines=s.splitlines()
for i,line in enumerate(lines):
    if line.startswith('| 02 Sesión'):
        lines[i]='| 02 Sesión y personal |09/11/2026|11 HU/33 CA:18 actuales,15 futuros;13 rutas agrupadas,26 UI,12 entradas,8 decisiones; identity→cash/sales|**AUDITORÍA COMPLETADA CON HALLAZGOS Y DECISIONES ABIERTOS ·02-D**;15 CA CUMPLE muestra,3 PARCIAL,15 futuros|163/163 métodos,32/32 salida,20/20 empleados,6 PG. Eventos técnicos R1 INCUMPLE; nombres/confirmación/bloqueo pendientes; carreras comerciales/admin externo→15. No atribuir FIX-E02 preexistentes a02-A|**ETAPA-03 / HU-CAT-01/CA-01**,08:166,ADMIN menú catálogo→GET /productos/categorias/. Leer traspaso02.|'
    if line.startswith('> Trabaja en C:/Users/walte'):
        lines[i]=handoff.split('Texto para nuevo chat:\n\n')[1].strip()
s='\n'.join(lines)+'\n'
s+='\n**Cierre02-D.** El corte02-A anterior queda como historia, sustituido para el cursor por02-D. Empleados02-B y carreras02-C ejecutados; correcciones y límites en [ETAPA-02](ETAPA-02.md), verificación en [cierre final](evidencias/02-D-cierre-final.json). Etapa15 recibe SEC-15-OBS-02 (evento técnico ausente), SEC-15-CONC-02 y SEC-15-LIMITES-02;12/14 reciben conservación histórica ampliada. No se cierran esos módulos.\n'
p.write_text(s,encoding='utf-8')

for name, prefix in [('09_Product_Backlog.md','> **Complemento de auditoría ·'),('03_Matriz_de_Trazabilidad_y_Pruebas.md','> **Complemento de auditoría reconciliado ·')]:
    p=ROOT/name;lines=p.read_text(encoding='utf-8').splitlines()
    for i,line in enumerate(lines):
        if line.startswith(prefix) and ('etapa 02' in line or '(02-A)' in line):
            lines[i]='> **Complemento de auditoría ·09/11/2026 (cierre02-D).** 11 HU/33 CA:15 CUMPLE muestra,3 PARCIAL por nombres/apellidos y confirmación,15 PREVISTO/FUTURO. AUTH03 R1 seleccionado; USR01..05 adicional implementado, auditado en navegador/servidor.163/163 métodos,32/32 salida,20/20 empleados y6 escenarios PostgreSQL. Eventos técnicos R1 siguen INCUMPLE; propuestas/decisiones no aceptadas automáticamente. AUTH04a/04b/05,USR06 yLOG01 no disponibles. Estados históricos preservados. [Resultados y límites](auditoria_por_etapas/resultados/ETAPA-02.md) · [Criterios](auditoria_por_etapas/resultados/anexos/ETAPA-02-criterios.md) · [Cierre y traspaso](auditoria_por_etapas/resultados/anexos/ETAPA-02-cierre-y-traspaso.md).'
    p.write_text('\n'.join(lines)+'\n',encoding='utf-8')

p=R/'anexos/ETAPA-02-superficie.md';s=p.read_text(encoding='utf-8')
s=s.replace('11 entradas/controles y 7 decisiones de persistencia','12 entradas/controles y 8 decisiones de persistencia')
s=s.replace('alterna `is_active` validando','aplica `action=desactivar/reactivar` explícita e idempotente (ausente/inválida/múltiple →400), validando')
s+='''
## Actualización de cierre02-D (prevalece sobre pendientes históricos de inspección)

E02-REV-01..04 fueron reproducidos y corregidos; REV05 verificado en navegador/servidor, con límites explícitos. REV06/07 conservan decisión; REV08 futuro. [Resultados por evidencia](../ETAPA-02.md). Las menciones NO EJECUTADO de la inspección inicial no son el estado actual: consultar matriz33 actual. F03..F10 tienen navegador y tests de fronteras; Unicode extremo queda no ejecutado.

| Entrada nueva | Contrato y pruebas |
|---|---|
|E02-F12 action|Oculto, obligatorio en POST estado; valor inicial desactivar para activo/reactivar para inactivo; exactamente una ocurrencia y uno de esos valores, sin normalización silenciosa. Inválido400 sin mutación, ya solicitado mensaje informativo, éxito302. B11 y seis tests de estado. El botón constituye acción directa; confirmación separada pendiente REV06.|

| Persistencia nueva | Contrato y pruebas |
|---|---|
|E02-P08 coordinación|Servicios de empleados bloquean Role ADMIN y recargan actor/objetivo; apertura caja bloquea Account antes de CashRegister. Último ADMIN/duplicado/rol/estado frente a apertura probados con dos conexiones PG. Logout comparte transacción descarte+sesión DB, rollback probado; evento técnico requerido ausente. No cubre escritores externos/admin, ni todos los requests en vuelo.|

Errores de F03..F10 ahora tienen destino aria-describedby existente y role=alert; ayudas conservan texto, sin cambiar contrato de negocio. B04A/B10A y tests de servidor verifican DOM, no lector de pantalla. U16 estado utiliza F12; R08 devuelve400 cuando falta contrato explícito. No hay pantalla nueva de confirmación.
'''
p.write_text(s,encoding='utf-8')
