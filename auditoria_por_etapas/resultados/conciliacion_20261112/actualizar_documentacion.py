"""Conciliación documental autorizada. No importa Django ni abre bases o .env."""
from pathlib import Path
import hashlib, json, re, shutil

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
if "FUENTE-PRINCIPAL-20261112" in (ROOT/"08_Historias_de_Usuario.md").read_text(encoding="utf-8"):
    raise SystemExit("Corte historico protegido. Editar08 y usar fuente_unica_20261112/regenerar_vistas.py y validar_fuente.py.")

BASE = HERE / 'BASELINE'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return p.read_text(encoding='utf-8-sig')
def write(rel, text):
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.rstrip()+'\n', encoding='utf-8')

def snapshot():
    if (HERE/'FUENTES.json').exists(): return
    docs = sorted([p for p in ROOT.iterdir() if p.is_file() and p.suffix.lower()=='.md'])
    docs += sorted((ROOT/'auditoria_por_etapas').glob('*.md'))
    docs += sorted((ROOT/'auditoria_por_etapas/resultados').glob('ETAPA-*.md'))
    docs += [ROOT/'auditoria_por_etapas/resultados/ESTADO_GENERAL.md']
    docs += sorted(p for p in (ROOT/'auditoria_por_etapas/resultados/anexos').rglob('*') if p.is_file())
    docs += [p for p in (ROOT/'r1-pmv').glob('*.md')]
    docs += [p for p in (ROOT/'r1-pmv/docs').rglob('*') if p.is_file() and p.suffix.lower()=='.md']
    hours = ROOT/'r1-pmv/evidencias/CONTROL_DE_HORAS_Y_ESTADO.md'
    if hours.exists(): docs += [hours]
    manifest = []
    for p in sorted(set(docs)):
        rel = p.relative_to(ROOT)
        dest = BASE/rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        manifest.append({'path':rel.as_posix(), 'sha256':sha(p), 'bytes':p.stat().st_size})
    write(HERE.relative_to(ROOT)/'FUENTES.json', json.dumps(manifest, ensure_ascii=False, indent=2))

if __name__=='__main__':
    snapshot()
    print('Baseline preservada:', len(json.loads(read(HERE/'FUENTES.json'))), 'fuentes documentales')

LINK = 'auditoria_por_etapas/resultados/conciliacion_20261112'
SELECTED = set('HU-AUTH-01 HU-AUTH-02 HU-AUTH-03 HU-USR-01 HU-USR-02 HU-USR-03 HU-USR-04 HU-USR-05 HU-CAT-01 HU-CAT-02 HU-PROD-01 HU-PROD-02 HU-PROD-03 HU-PROD-04 HU-PROD-05 HU-PROD-06 HU-PROV-01 HU-PROV-02 HU-PROV-04 HU-INV-01a HU-INV-01b HU-INV-02 HU-INV-03 HU-INV-04 HU-CAJA-01 HU-CAJA-02 HU-CAJA-05 HU-VEN-01a HU-VEN-01b HU-VEN-01c HU-VEN-02a HU-VEN-05a HU-VEN-05b'.split())
ORIGINAL9 = set('HU-AUTH-01 HU-AUTH-03 HU-PROD-02 HU-INV-01a HU-CAJA-01 HU-VEN-01b HU-VEN-01c HU-VEN-02a HU-CAJA-02'.split())

def notice(name):
    return f'> **Vigente: 12/11/2026 · conciliación documental autorizada.** Requisito aceptado no equivale a implementación o verificación. [Mapa y decisiones]({LINK}/CONSOLIDACION.md) · [Encargos verificables]({LINK}/ENCARGOS.md) · [Versión anterior íntegra]({LINK}/BASELINE/{name}). Jira no forma parte de este seguimiento.\n\n'

def old(name): return read(BASE/name)
def replace_once(s, before, after):
    assert before in s, before[:100]
    return s.replace(before, after, 1)

def revise_requirements():
    s = old('08_Historias_de_Usuario.md')
    # Conservar las 74 HU y sus 219 ordinales; retirar de la capa vigente el collage QA histórico.
    body = s[s.index('## 8.1 '):s.index('## 8.7 ')]
    body = body.replace('sus nombres, apellidos, correo electrónico y su rol', 'su Nombre completo (nombres y apellidos juntos, hasta 120 caracteres, no único), correo electrónico y su rol')
    body = body.replace('y que sea único dentro del producto', 'y que no se repita dentro de la misma carga; las recepciones posteriores conservan identidad propia conforme a DOC-03AI-01')
    body = body.replace('Como administrador, quiero que el costo promedio del producto se recalcule al confirmar entradas posteriores a su carga inicial, para que los cálculos de rentabilidad reflejen el valor real pagado sin duplicar el alcance de `HU-INV-01a`.', 'Como almacenero, quiero registrar recepciones posteriores directas con identidad propia y costo promedio coherente, para incorporar mercadería autorizada por el procedimiento externo del negocio, sin repetir la carga inicial ni duplicar existencias al reenviar.')
    body = body.replace('### HU-INV-01b · Inventario — Recalcular el costo promedio en entradas posteriores','### HU-INV-01b · Registrar recepción posterior y actualizar costo promedio')
    body = body.replace('entrada posterior autorizada con cantidad y costo de compra', 'recepción posterior directa confirmada por ALMACENERO, con identidad propia, cantidad y costo de compra')
    body = body.replace('usando las unidades anteriores y las ingresadas conforme a RN-14', 'usando todas las unidades físicas registradas anteriores, incluidas las vencidas pendientes de baja, y las ingresadas conforme a RN-14; el reintento de la misma clave/contenido devuelve la recepción previa sin nuevos efectos')
    body = body.replace('entonces el sistema exige procesarla como Vencimiento e impide registrarla como daño físico conforme a la regla RN-05.', 'entonces permite Vencimiento si la causa es caducidad o Robo o faltante con explicación si esa es la causa real, y rechaza Daño o rotura conforme a RN-05.')
    body = body.replace('entonces el sistema exige asociarlo a un lote o crear uno nuevo con su fecha de vencimiento.', 'entonces exige asociarlo a un lote o crear uno nuevo con fecha de vencimiento fiable, motivo y costo conforme a RN-14; un hallazgo vencido se registra solo como no vendible, nunca como recepción ordinaria.')
    body = body.replace('Dado que un movimiento de entrada nació de una reposición aprobada (HU-SOL-05a), cuando abro el detalle, entonces muestra el proveedor y la referencia de recepción.', 'Dado que un movimiento nació de una recepción directa, cuando abro el detalle, entonces muestra su referencia propia, responsable y proveedor o ausencia declarada; si en el futuro nació de HU-SOL-05a, mostrará además la solicitud aprobada sin inventar esa relación para entradas actuales.')
    body = body.replace('los reportes analíticos de gestión ya permiten su exportación', 'la exportación de gestión permanece futura en HU-REP-09')
    body = body.replace('La bodega comercializa exclusivamente productos envasados por unidad con código de barras.', 'El alcance de esta versión admite productos envasados por unidad con código de barras; no afirma que esa sea toda la actividad real del negocio.')
    j = s[s.index('## Cambio de estado de una categoría'):s.index('**Adenda03-O')]
    j = j.replace('CAT03 (renombrar), CAT04 (eliminar) y PROD03 (lector) mantienen su clasificación futura.', 'CAT03 (renombrar) y CAT04 (eliminar) mantienen su clasificación futura. PROD03 fue seleccionado y ampliado en los cortes O/P/Y/Z.')
    extra = '''## 8.7 Complementos vigentes y procedencia

Los 219 CA base conservan su identidad HU/ordinal. Los cambios de este corte afectan USR03/CA01, INV01a/CA02, INV01b/CA01, INV02/CA02, INV03/CA01 e INV04/CA02; el cuerpo anterior está archivado. Los contratos de recepción, valoración, permisos, descuentos, bloqueo, seguridad y consultas se añaden con identidad `ID-original/C-nn` en ENCARGOS; son parte del criterio de aceptación de las HU afectadas, no meras notas opcionales.

La antigua §8.7 QA/UX se conserva íntegra en BASELINE: mezcla varias HU por fila y reutiliza ordinales, por lo que sus rótulos CA no sustituyen los actuales. Kardex corresponde a INV04; historial de bajas a INV05; historial de ajustes a INV06; descuentos no corresponden a VEN03. Los vínculos a pruebas de esa tabla se consideran evidencia histórica, no aprobación automática de criterios revisados.

DOC03-01/02 conservan categoría activa, UND/vencimiento y código editable con unicidad e historia intacta. PROP03C-LIMITES/NOMBRE se ratifican expresamente desde12/11 por delegación: mínimo10 por defecto, rango0..999999; unicidad de nombre comercial normalizado global incl. inactivos, sin quitar acentos. No se atribuye la aprobación original al mero «continúa».

HU-PROD-03 mantiene la copia expresa del campo temporal mediante «Usar código», aviso de duplicado y GTIN/código interno del cuerpo actualizado. Las fases O/P/Y/Z sustituyen pendientes anteriores del lector; las muestras físicas no certifican todos los dispositivos. Productos legacy ambiguos requieren clasificación comprobada antes de reservar equivalencias.

Los 33 requisitos seleccionados, 41 futuros y ocho ideas están separados en09. Criterios futuros no se declaran implementados. En particular bloqueo300s pasa a requisito antes del piloto; recuperación por correo conserva propuesta histórica pendiente de refinamiento, sin certificar seguridad de un código4dígitos.

'''
    write('08_Historias_de_Usuario.md', '# 8. Historias de usuario y criterios vigentes\n\n'+notice('08_Historias_de_Usuario.md')+body+extra+j)

    s = old('07_Reglas_de_Negocio.md')
    s = s[s.index('## 7.1 '):]
    s = s.replace('Una única carga inicial directa por producto; las entradas posteriores requieren reposición aprobada, salvo ajustes administrativos de inventario','Una carga inicial única; recepción posterior directa con identidad propia; ajustes administrativos separados; SOL futuro')
    s = s.replace('los lotes vencidos o que vencen hoy no se ingresan ni se venden','no se reciben ni venden lotes vencidos; ajuste físico vencido excepcional queda no vendible')
    s = s.replace('Cada cuenta tiene un único rol y el servidor autoriza las nueve historias según la matriz del PMV','Cada cuenta tiene un único rol; separar consulta y operación conforme a matriz vigente')
    s = replace_once(s, 'Después de esa confirmación, toda entrada ordinaria de mercadería del encargado del almacén debe estar vinculada a una solicitud de reposición previamente aprobada. Esta restricción no elimina las regularizaciones extraordinarias que el administrador registra mediante `HU-INV-03` para cuadrar el conteo físico; dichas regularizaciones quedan identificadas como ajustes, no como una nueva carga inicial.', 'Después de esa confirmación, ALMACENERO registra recepciones ordinarias directas con identidad propia, autor, lotes, cantidades, costos e idempotencia (DOC-03AB-01/03AI-01). La autorización de compra se gestiona fuera del sistema como política adoptada en este corte. HU-SOL-01..05b permanece futuro. ADMIN registra regularizaciones por conteo mediante HU-INV-03, identificadas como ajustes y nunca como nueva carga inicial o compra ficticia.')
    s = s.replace('Ningún lote cuya fecha de caducidad sea igual o anterior a esa fecha puede registrarse como nueva mercadería ni venderse en el mostrador.', 'Ningún lote cuya fecha de caducidad sea igual o anterior a esa fecha puede registrarse por carga inicial/recepción ordinaria ni venderse. Como excepción de conteo físico, ADMIN puede registrar existencia vencida encontrada con fecha fiable, motivo y costo conforme a RN-14; queda inmediatamente no vendible y no simula una compra.')
    a=s.index('### RN-14 '); b=s.index('### RN-15 ',a)
    s=s[:a]+'''### RN-14 · Promedio móvil sobre existencia física registrada

El costo de entrada es decimal positivo con hasta cuatro posiciones. El costo promedio se calcula con todas las unidades físicas registradas, incluidas vencidas pendientes de baja; disponibilidad comercial y valoración son conceptos diferentes. La carga inicial usa suma(cantidad×costo)/suma(cantidad). La recepción posterior usa `(Q×C + q×c)/(Q+q)`, con Q físico/C promedio bloqueados dentro de la transacción. Resultado HALF_UP4; presentación HALF_UP2.

Venta, baja y ajuste negativo retiran unidades al promedio vigente sin reponderar costos de los lotes restantes. La expiración sola no altera el promedio. Cuando stock físico total=0, promedio vigente=0; snapshots de salidas conservan el costo previo. Ajuste positivo con stock previo usa su promedio; sin stock exige costo positivo documentado y fuente/motivo, o se rechaza para investigar. No inventar costo histórico desconocido ni recalcular ventas pasadas con el costo de hoy.

DOC-03AH-01 y sus C-01..04 detallan ejemplos, concurrencia y tratamiento de legado. Política de control interno aceptada12/11; implementación pendiente. No acredita conformidad contable/fiscal.

---

'''+s[b:]
    a=s.index('| Operación de Sprint 1'); b=s.index('Ocultar una opción',a)
    s=s[:a]+'''| Operación del alcance vigente | ADMIN | ALMACENERO | VENDEDOR |
|---|:---:|:---:|:---:|
| Ingresar/salir propia sesión | Sí | Sí | Sí |
| Mantener personal/categorías/productos/proveedores | Sí | No | No |
| Consultar catálogo/proveedores/inventario | Sí | Sí | No; consulta POS vendible |
| Carga inicial/recepción | No | Sí | No |
| Baja de inventario | Sí | Sí | No |
| Ajuste físico | Sí | No | No |
| Consultar cargas/recepciones/bajas/movimientos | Sí | Sí | No |
| Abrir/preparar/cobrar/cerrar turno propio | No | No | Sí |
| Consultar ventas/constancias/turnos | Global | No | Solo propios; filtros según HU |
| Portal técnico | Sin permiso por rol comercial | No | No |

La constancia destinada al cliente nunca muestra costo de compra, incluso si la abre ADMIN. Las funciones futuras no aparecen como disponibles por figurar en esta matriz. DEC-12-PERMISOS-HISTORIAL-Y-MENU especifica solicitudes directas/propiedad/navegación.

'''+s[b:]
    s=s.replace('El vendedor consulta sus ventas del turno activo; el administrador consulta el historial consolidado cuando las historias correspondientes estén disponibles','El vendedor consulta ventas propias según HU seleccionadas; ADMIN consulta historial global; costos excluidos de constancia')
    s=s.replace('Para mantener el trabajo enfocado en lo indispensable para el minimarket, se establecen los siguientes acuerdos operativos:', 'Los puntos1–2 describen funcionalidades FUTURAS de anulación/devolución (no disponibles en R1). El punto3 es preparación de entorno de demostración, no evidencia de datos productivos:')
    s=s.replace('*Próximo documento: 08 — Historias de Usuario (`08_Historias_de_Usuario.md`)*','')
    s+='''\n## 7.7 Aplicabilidad y complementos de este corte

RN02/08/09/11/15/16/18/23 describen funciones futuras; RN13/21 están fuera del horizonte fiscal actual. No se usan para exigir pantallas no seleccionadas. RN22 se selecciona antes del piloto; RN24 conserva requisito documentado, no certificación de seguridad integral.

Nuevos cobros no aceptan descuento discrecional (DEC-11-DESCUENTOS-ALCANCE); los históricos permanecen intactos. Límite venta/efectivo/apertura9,999,999.99; cierre acumulado hasta capacidad14,2 (DEC-11-TOPE-EFECTIVO-FORM). RN27 describe modelo interno de precios con18% incluido; el régimen tributario/productos reales no se han confirmado y debe comprobarse aplicabilidad antes de uso real. La constancia RN26 no reemplaza canal oficial.

El detalle verificable aceptado de recepción/lotes, inventario, identidad, permisos, bloqueos, seguridad y consultas reside en ENCARGOS.md, enlazado al comienzo. No se renumeran RN existentes. Toda exigencia nueva mantiene estado de implementación pendiente hasta evidencia propia.
'''
    write('07_Reglas_de_Negocio.md', '# 7. Reglas de negocio vigentes\n\n'+notice('07_Reglas_de_Negocio.md')+s)

def stage(hu):
    if hu.startswith('HU-AUTH-'): return '01' if hu in ('HU-AUTH-01','HU-AUTH-02') else '02'
    if hu.startswith(('HU-USR-','HU-LOG-')): return '02'
    if hu.startswith(('HU-CAT-','HU-PROD-')): return '07' if hu=='HU-PROD-06' else '03'
    if hu.startswith('HU-PROV-'): return '04'
    if hu=='HU-INV-01a': return '05'
    if hu=='HU-INV-01b' or hu.startswith('HU-SOL-'): return '06'
    if hu.startswith('HU-INV-'): return '08'
    if hu.startswith('HU-CAJA-'): return '12' if hu=='HU-CAJA-05' else '09'
    if hu in ('HU-VEN-01a','HU-VEN-01b','HU-VEN-04'): return '10'
    if hu=='HU-VEN-01c': return '11'
    if hu.startswith('HU-VEN-'): return '12'
    return '13'

WORK = [
('DOC-03AH-01','P0','Valoración coherente','RN14/28; INV01a/b/02/03, VEN01c','Diagnóstico de valoración y costos legacy','unitarias secuencia/zero; carreras; rollback'),
('DOC-03AI-01','P0','Recepción propia y reintentos','RN01/14/19; INV01a/b/04','DOC-03AB-01, DOC-03AH-01; informe lote/entrada','doble POST igual/divergente; colisiones; pérdida respuesta'),
('DEC-11-MODELO-AUDITORIA-VENTAS','P0','Asignaciones lote y snapshots','RN25/26/28; VEN01c/02a, INV04','Modelo movimientos e informe legado','FEFO multilote; atomicidad completa; historia'),
('DEC-11-DESCUENTOS-ALCANCE','P0','Suspender nuevos descuentos','VEN01b/c/02a/05a/b; RN25/27','Distinguir nueva operación/reintento histórico','manipulación; histórico; caja/IGV/reintento'),
('PROP-09-DB-01','P0','Checks de caja/borrador','PROP-10-04; CAJA02/VEN01b','Diagnóstico de datos inválidos','DB directa; diferencia negativa válida; rollback'),
('CT-ROLLBACK-01-POST-ESCRITURA','P0','Concurrencia y caída real','RN25; SEC-15-CONC-02; INT/E2E','PG17 aislado; barrera observable','muerte postwrite/precommit; recuperación; reintento'),
('DEC-12-PERMISOS-HISTORIAL-Y-MENU','P1','Permisos y consulta por rol','RN07/29; PROD01,CAJA05,VEN05a/b','Matriz vigente','roles/propiedad; menú; URL directa sin datos'),
('DOC-02-04','P1','Personal/reset/revocación','USR02..05; RN12/17/24/29','Eventos técnicos; dominio correo/colisiones','cookies; bloqueo tras rename; concurrencia; confirmación'),
('DOC-01-06','P1','Portal/tráfico/eventos','SEC15ADMIN/TRAFICO/OBS/RETENCION','Entorno/IP/volumen/finalidad reales','perímetro; logs sin secretos; transacción y fallo'),
('DEC-10-BLOQUEO-INACTIVIDAD','P1','Bloqueo300s del puesto','VEN01a; RN22','Sesión y reloj servidor; revocación','pestañas; reloj; preservación borrador; reautenticación'),
('DEC-11-TOPE-EFECTIVO-FORM','P1','Límites operación y acumulado','CAJA01/02; VEN01c; RN10/27','PROP-09-DB-01','máximo±centavo; cierre con suma superior a venta'),
('RN-05','P1','Causa de baja y ajuste nuevo','INV02/03; RN03/04/05/14/20','DOC-03AH/AI; costo/fecha fiables','vencido robado; ajuste vencido no vendible; carrera'),
('DEC-05-LOTE-ESPACIOS','P1','Identidad de lote y límites','INV01a/b; PROP05/06VALID','Informe colisiones; DOC03AI','normalización; fronteras; datos legacy'),
('DEC-08-KARDEX-COMPRAS','P1','Movimientos y saldo fiable','INV04; RN25','Asignaciones/recepción; diagnóstico historia','saldo apertura; filtros/páginas; origen desconocido'),
('DEC-08-CONSTANCIA-MERMA','P2','Constancia de baja','INV02/CA04','RN-05; idempotencia','consulta/impresión/roles; inmutabilidad'),
('DEC-04B-ESTADO-OMITIDO','P1','Proveedor destino explícito','PROV04; DEC04RUCVALIDACION','Actor lock; contrato proveedor','omisión/alteración/repetición; no mutación'),
('DEC-12-ORDEN-LINEAS-RECIBO','P2','Orden, filtros y paginación','VEN02a/05a/b; CAJA05; PROP12ORDEN','Posición/snapshots; medición volumen','empates; 25/26filas; filtro; legado'),
('DEC-07-VENCIDOS-FILTRO','P2','Alertas y vencidos separados','PROD06; DEC07INACTIVOS/DASHDIAS','Definición físico/vendible','medianocheLima; inactivos; etiquetas/conteos'),
('PROP-10-03','P2','GET informativo y revisión precio','VEN01b/c; RN30','Firma del borrador','GET no muta; pestaña vieja; cambio concurrente'),
('S1-OPS-DB-01','P1','Despliegue/backup/restauración','S1-CI-01/ST-BASE/PG17','P0/P1, ambiente y acceso autorizados','CI real; restauración clon; smoke; seguridad'),
('DOC-00-01','P1','Trazabilidad y revisión documental','DOC00-05/07/08/09/12/13; PROP05GEVID','Todos los contratos','IDs/enlaces; hashes; no cierre indebido')
]

def rewrite_scrum():
    src=old('09_Product_Backlog.md')
    rows=[]
    for line in src.splitlines():
        cells=[c.strip().strip('`') for c in line.strip().strip('|').split('|')]
        if len(cells)>=9 and re.fullmatch(r'HU-[A-Z]+-\d+[a-z]?',cells[1]): rows.append(cells[:9])
    assert len(rows)==74
    assert sum(int(x[5]) for x in rows)==231
    current_titles=dict(re.findall(r'^### (HU-[A-Z]+-\d+[a-z]?) · (.+)$',read(ROOT/'08_Historias_de_Usuario.md'),re.M))
    for row in rows:
        row[2]=current_titles[row[1]]
        row[8]=row[8].replace('`','')
        if row[1]=='HU-PROD-02':row[8]='HU-AUTH-01; categoría activa existente (CAT02 o datos iniciales)'
    header='# 9. Product Backlog vigente\n\n'+notice('09_Product_Backlog.md')
    header+='''## Objetivo y alcance

R1 de consolidación debe permitir operar caja única en efectivo con identidad, catálogo, recepción, inventario y consulta trazables, sin pérdidas/duplicados ni permisos indebidos. Se seleccionan33 HU (nueve históricas y24 adicionales, incluido bloqueo de pantalla previo al piloto). Otras41 siguen futuras; ocho ideas quedan fuera. El orden siguiente expresa prioridad de producto; la secuencia técnica y dependencias están en16. No hay Sprint nuevo comprometido ni fechas/personas/capacidad verificadas.

Los SP que se conservan son estimaciones de la línea base (74 HU/231 SP), no una nueva estimación del trabajo restante. Los219 CA base más contratos suplementarios determinan aceptación. Los nueve seleccionados originalmente sumaban40 SP/41 CA; no representan la cobertura actual. La selección vigente queda aceptada por delegación12/11. Implementación y verificación se consultan en03/04, no se deducen de esta tabla.

## Lista vigente por selección

| Orden vigente | ID | Necesidad | Selección | Etapa fuente | SP históricos | Dependencia funcional histórica a contrastar |
|---:|---|---|---|---|---:|---|
'''
    # El orden de paquetes críticos prima; aquí se agrupan necesidades funcionales seleccionadas.
    ordered=sorted(rows,key=lambda r:(r[1] not in SELECTED,int(r[0])))
    for i,r in enumerate(ordered,1):
        sel='R1 consolidación' if r[1] in SELECTED else 'FUTURO, sin Sprint'
        header+=f'| {i} | {r[1]} | {r[2]} | {sel} | {stage(r[1])} | {r[5]} | {r[8]} |\n'
    header+='''\n## Ocho ideas fuera del horizonte

HU-CLI-01/02/03 (clientes), HU-VEN-02b/02c (boleta/factura), HU-VEN-03 (PDF/correo), HU-VEN-08 (exportar historial) y HU-VEN-09 (peso/granel). Sin CA seleccionados/SP comprometidos. El supuesto de exportación disponible se corrige: REP09 también es futuro. El catálogo completo y motivos siguen en08/BASELINE.

## Complementos seleccionados y exclusiones

Los encargos de recepción/idempotencia, valoración, trazabilidad lote/venta, descuentos nuevos deshabilitados, permisos, seguridad técnica, checks, constancias, Kardex, alertas y navegación se vinculan a HU existentes en16 y ENCARGOS. Activar/desactivar categoría conserva PROP-E00-HU-02/J-CA1..4. Stock consolidado y panel mínimo actual tienen el contrato DEC07; no se adjudica entrega de DASH/REP completos.

Se difieren SOL, INV05/06, CAT03/04, PROV03, caja manual/aprobación/forzada, consulta VEN04 sin turno, sesión única/correo/cierre remoto/LOG UI, anulaciones/Yape/configuración/reportes y propuestas RET. No se impone una solución técnica masiva por el solo hecho de estar propuesta.

Los enlaces de dependencia de la tabla preservan procedencia: una solicitud SOL futura no bloquea la recepción directa seleccionada (DOC03AB); una alerta no exige reportes completos. Para trabajo autorizado se usa el grafo vigente de16. No se usa Jira ni se recrean Sprints anteriores.
'''
    write('09_Product_Backlog.md',header)
    task='# 16. Trabajo pendiente y dependencias vigentes\n\n'+notice('16_Task_Breakdown.md')
    task+='''Los67 IDs y216h del desglose original permanecen en BASELINE; no son trabajo ejecutado ni estimación vigente. Se reutilizan IDs de decisiones/tareas existentes para encargos sin colisión. Cada fila hereda el contrato de ENCARGOS y su matriz; no crea otra HU. Estado salvo la fila documental: ACEPTADO, implementación no autorizada en esta fase. Costo relativo se evalúa al refinar; no inventar SP, horas o responsables.

| ID original | Prioridad | Resultado verificable | HU/RN/vínculo | Dependencias antes de aceptar entrega | Pruebas mínimas |
|---|---|---|---|---|---|
'''
    for x in WORK: task+='| '+' | '.join(x)+' |\n'
    task+='''\n## Secuencia y preparación

Primero diagnóstico reproducible de datos y contratos de recepción/costos/ventas; luego persistencia y servicios, después consultas/UI, y finalmente pruebas de aceptación por rol/integrales. Se pueden preparar pruebas, formularios y especificación en paralelo cuando no dependen de datos pendientes. El orden de locks se establece globalmente, no por parches aislados.

Un encargo está listo para implementar cuando entradas/roles/efectos/errores/legado están definidos, dependencia técnica satisfecha o planificada, y existe autorización de implementación. Tráfico/retención/normativa/despliegue mantienen investigación C antes de fijar parámetros. Las correcciones nuevas aquí no se aplican automáticamente al código.

La fila DOC00-01 tiene implementación documental en este corte y verificación estructural propia; no implica cierre de entrega software. Las pruebas existentes que consagran valoración antigua o descuentos deben actualizarse junto al cambio autorizado, preservando el resultado histórico.
'''
    write('16_Task_Breakdown.md',task)
    planning='''# 14. Planificación vigente del siguiente incremento

'''+notice('14_Sprint_Planning.md')+'''## Situación real

Existe una versión integrada con434 pruebas automáticas aprobadas en SQLite aislado y evidencia histórica por etapas; también existen brechas P0/P1 y criterios recién revisados. No hay evidencia suficiente para declarar release listo ni un Sprint actual terminado. Las fechas10–23octubre, seis Developers,40 SP,216h,192/240h de capacidad y tarifa académica son cortes históricos, no compromisos ni mediciones actuales.

## Objetivo propuesto para el próximo Sprint

Conseguir que cada entrada y venta conserve origen, costo y cantidades coherentes, con reintentos seguros y permisos comerciales inequívocos. Es una propuesta de objetivo, no un Sprint ya iniciado. La selección concreta corresponde al equipo al conocer capacidad y estimar trabajo restante; no se comprometen todos los21 encargos a un único Sprint.

Candidatos iniciales: DOC03AH (valoración), DOC03AI (recepción), DEC11MODELO (asignaciones/snapshots), DEC11DESCUENTOS y checks críticos; dependencias y pruebas en16. Preparar simultáneamente diagnóstico de datos, pruebas y revisión de permisos. Bloqueo de pantalla, seguridad técnica y despliegue son condiciones antes del piloto aunque no quepan en ese primer incremento.

## Preparación y Definition of Done

Para seleccionar: criterio comprendido, dependencia/legado identificado, prueba verificable y tamaño estimado por quienes implementan. Para Hecho: código autorizado integrado, todos los CA seleccionados y suplementos cumplidos, pruebas apropiadas sin exclusiones ocultas, rechazo sin mutación, concurrenciaPG cuando proceda, navegador por roles, migración ensayada y reversible, docs/evidencia coherentes y revisión independiente. Una tarea documental terminada no cumple la DoD del software.

PG17 sigue objetivo; PG18.4 es evidencia parcial; SQLite no prueba locksPG. La aceptación de decisiones y una suite verde no levantan brechas de auditoría. CI, recuperación y despliegue deben tener resultados propios.

## Seguimiento

Usar09 para necesidades/orden,16 para tareas/dependencias,03 para criterios,04 para evidencia y ESTADO_GENERAL para auditorías. Un solo registro de decisión: CONSOLIDACION+ENCARGOS. No duplicar estados en Jira. No asignar personas/fechas reales ni horas ejecutadas sin evidencia del equipo.

La Guía Scrum oficial define Product Backlog emergente, Sprint Backlog y Definition of Done; aplicar estos artefactos no acredita reuniones ni participantes inexistentes. Fuente y aplicabilidad en FUENTES_EXTERNAS.md.
'''
    write('14_Sprint_Planning.md',planning)

def inventory_criteria():
    s=read(ROOT/'08_Historias_de_Usuario.md')
    matches=list(re.finditer(r'^### (HU-[A-Z]+-\d+[a-z]?) · (.+)$',s,re.M))
    inventory=[]
    for i,m in enumerate(matches):
        end=matches[i+1].start() if i+1<len(matches) else s.index('## 8.6 ')
        chunk=s[m.end():end]
        for c in re.finditer(r'^  (\d+)\. (.+)$',chunk,re.M):
            inventory.append({'id':f'{m[1]}/CA-{int(c[1]):02d}', 'hu':m[1], 'title':m[2], 'criterion':c[2], 'line':s[:m.end()+c.start()].count('\n')+1,'stage':stage(m[1]),'selected':m[1] in SELECTED})
    assert len(matches)==74 and len(inventory)==219,(len(matches),len(inventory))
    write(HERE.relative_to(ROOT)/'INVENTARIO_CA.json',json.dumps(inventory,ensure_ascii=False,indent=2))
    text='# 3. Matriz vigente de requisitos y verificación\n\n'+notice('03_Matriz_de_Trazabilidad_y_Pruebas.md')
    text+='''## Alcance y lectura

74 HU/219 CA base,33 HU seleccionadas y41 futuras, más ocho ideas sin CA. No se declara CUMPLE por asignación a Sprint ni por434 tests verdes. «Muestra previa» significa que el informe indicado documenta su observación y sus límites; se debe evaluar el criterio revisado y suplementos antes de aceptar entrega actual. Las pruebas históricas con nombres/cortes diferentes no se suman para simular una ejecución integrada.

Los CA suplementarios tienen identidad de apartado/C-nn en ENCARGOS. Se verifican junto a la HU afectada, sin renumerar219 CA base ni reutilizar ordinales de la antigua tabla QA. E2E/INT/CT/ST/PT/MT de la matriz anterior se conservan como IDs históricos y su ejecución vigente requiere evidencia propia. Los encargos16 especifican extensiones necesarias.

| ID estable | Requisito abreviado (texto completo en08) | Alcance | Evidencia/estado vigente | Dependencia de aceptación |
|---|---|---|---|---|
'''
    modified={'HU-USR-03/CA-01','HU-PROD-02/CA-04','HU-INV-01a/CA-02','HU-INV-01b/CA-01','HU-INV-02/CA-02','HU-INV-03/CA-01','HU-INV-04/CA-02','HU-CAJA-05/CA-01','HU-CAJA-05/CA-02','HU-VEN-01b/CA-02','HU-VEN-05a/CA-02'}
    missing={'HU-INV-02/CA-04','HU-INV-03/CA-01','HU-INV-04/CA-01','HU-INV-04/CA-04'}
    for c in inventory:
        crit=c['criterion'].replace('|','/').replace('`','')
        if len(crit)>145: crit=crit[:142]+'…'
        if not c['selected']: state='FUTURO; sin entrega actual exigida'
        elif c['hu']=='HU-VEN-01a': state='PENDIENTE; no implementado según etapa10'
        elif c['id'] in modified: state='REVISADO12/11; requiere implementación/verificación del nuevo contrato'
        elif c['id'] in missing: state='PARCIAL/PENDIENTE documentado en etapa08'
        else: state=f'[Muestra previa y límites de etapa{c["stage"]}](auditoria_por_etapas/resultados/ETAPA-{c["stage"]}.md); revisar suplementos'
        scope='Seleccionado' if c['selected'] else 'Futuro'
        dep='Encargos por HU/RN + DoD14' if c['selected'] else 'Refinamiento y selección posterior'
        text+=f'| {c["id"]} | {crit} | {scope} | {state} | {dep} |\n'
    text+='\n## Índice de criterios suplementarios\n\n| ID único | Contrato | Estado de prueba |\n|---|---|---|\n'
    enc=read(HERE/'ENCARGOS.md'); current=None; supplemental=[]
    for line in enc.splitlines():
        if line.startswith('## '): current=line[3:].split(' · ')[0]
        m=re.match(r'\*\*(C-\d+)\.',line)
        if m:
            ident=f'{current}/{m[1]}'; supplemental.append(ident)
            text+=f'| {ident} | [Encargo {current}]({LINK}/ENCARGOS.md) | NO VERIFICADO como contrato nuevo; conserva evidencia histórica aparte |\n'
    assert len(supplemental)==len(set(supplemental))
    for n in range(1,5): text+=f'| PROP-E00-HU-02/J-CA{n} | Estado de categoría;08 §Cambio de estado | Muestras03-J y posteriores; no reejecutado aquí |\n'
    text+='''\n## Comprobaciones integrales pendientes

CT-ROLLBACK-01-POST-ESCRITURA y recuperación del motor; PG17; concurrencia entre roles y recursos con conexiones independientes; E2E por navegador sobre build actual; CI productiva; backup/restauración; volumen para PT-SEARCH-01/PT-CHECKOUT-01; teclado, impresión,390×844, historial vendedor y dispositivos reales con cobertura definida. No son defectos por no ejecutarse. La falta comprobada de asignaciones por lote, bloqueo de pantalla o constancia de baja sí es brecha frente al alcance seleccionado.

Las30 afirmaciones QA originales conservan procedencia en inventario00 y BASELINE. Para su aceptación vigente se sustituyen vínculos semánticamente erróneos (KardexINV06, alertasINV05, descuentoVEN03) por los contratos correctos. No se transfieren sus rótulos CA al catálogo base.
'''
    write('03_Matriz_de_Trazabilidad_y_Pruebas.md',text)
    return inventory,supplemental

if __name__=='__main__':
    revise_requirements()
    rewrite_scrum()
    inv,sup=inventory_criteria()
    print('Actualizados requisitos, backlog, tareas, planning y matriz:',len(inv),'CA base;',len(sup),'criterios suplementarios nuevos')

def rewrite_design_and_guides():
    src=old('02_Diseno_Tecnico_R1_PMV.md')
    constraints=src[src.index('### Restricciones e índices mínimos'):src.index('## 2.6 ')]
    constraints=constraints.replace('`UNIQUE(lot.product_id, lot.number_normalized)`','Unicidad de línea/lote normalizado dentro de recepción; identidad comercial puede repetirse en otra recepción (DOC03AI)')
    constraints=constraints.replace('Impide crear un producto enlatado sin control de vencimiento','Impide producto sin control de vencimiento en alcanceUND')
    constraints=constraints.replace('`UNIQUE(sale.number)` y `UNIQUE(idempotency_record.operation, key)`','Correlativo venta único; clave idempotente única por operación en registro propio o entidad confirmada equivalente, con actor y huella verificados')
    constraints=constraints.replace('checks `initial_qty > 0`, `0 <= available_qty <= initial_qty`, `unit_cost > 0`','Cantidad recibida original>0 e inmutable; saldo disponible>=0; costo>0; capacidad acumulada y movimientos de ajuste separados del original recibido')
    constraints=constraints.replace('Evita stock negativo o lote vacío','No confundir cantidad original recibida con capacidad tras ajuste positivo; conciliar saldo con movimientos')
    constraints=constraints.replace('índice FEFO `(product_id, expiration_date, received_at, id)` condicionado a `available_qty > 0`','Índice FEFO candidato por producto/vencimiento/ingreso/ID; medir antes de crear o cambiar')
    operations=src[src.index('## 2.10 '):src.index('## 2.15 ')]
    operations=operations.replace('roles, tres cuentas de prueba, categoría', 'roles, tres cuentas activas de prueba (una por rol) y una cuenta inactiva de prueba, categoría')
    operations=operations.replace('aplicadas automáticamente', 'aplicadas en CI/entorno autorizado; la base operativa requiere autorización separada')
    operations=operations.replace('no se agrega otro runner durante el Sprint salvo acuerdo del equipo','los soportes aislados de auditoría pueden invocar el runner estándar sin reemplazar sus tests ni excluir módulos')
    operations=operations.replace('Una migración destructiva queda prohibida en Sprint 1', 'No se autoriza migración destructiva por esta conciliación')
    operations=operations.replace('Ninguna eliminación se ejecuta durante la simulación documental','Es objetivo de retención del diseño; no se ha ejecutado ni autorizado eliminación operativa')
    gates=src[src.index('## 2.16 '):src.index('## 2.17 ')]
    design='# 2. Diseño técnico vigente y brechas de implementación\n\n'+notice('02_Diseno_Tecnico_R1_PMV.md')+'''## 2.1 Arquitectura y alcance

Monolito modular Django5.2/Python3.12, plantillas y servicios transaccionales, una caja física, tres roles exclusivos. PostgreSQL17 sigue motor objetivo; la suite actual usa SQLite aislado y existen muestrasPG18.4, sin equivalencia automática de concurrencia/versión. No se cambian dependencias, infraestructura ni bases en esta conciliación.

Alcance vigente33 HU de09 más contratos de ENCARGOS. Lo especificado aquí es diseño requerido, no inventario de tablas ya implementadas. Las simulaciones de seis Developers y fechas/216h/67tareas quedaron en BASELINE y no acreditan equipo, capacidad o aceptación real.

## 2.2 Responsabilidad de capas

Plantillas ayudan con formularios/foco/mensajes; vistas autentican/validan forma y llaman servicios; servicios reautorizan, validan reglas y manejan transacciones/locks; modelos/BD protegen tipos, FK, unicidad y checks. Ninguna cifra, rol, vendedor/turno o estado enviado por el navegador es autoridad. GET no muta datos de negocio.

La aplicación usa HTML y formularios Django. El contrato existente devuelve errores de campo mediante200 cuando corresponde y redirige tras POST válido;401/409/422 de un diseño API previo no se exigen a todas las vistas HTML. Navegación anónima redirige al ingreso; rol ajeno deniega403 y propiedad puede ocultarse con404. No exponer SQL/stack/secretos. El mismo rechazo debe conservar datos independientemente del códigoHTTP.

## 2.3 Modelo e invariantes

Identidad/catálogo/inventario/caja/ventas mantienen FK y datos históricos. Código de producto editable no cambia identidad ni snapshots. GTIN y código interno conservan equivalencias/reservas ya aceptadas; legacy ambiguo requiere clasificación antes de migrar. Nombre comercial normalizado único incl.inactivos, empleados/proveedores pueden ser homónimos. Todos los productos del alcance sonUND con vencimiento.

Una carga inicial por producto; recepciones posteriores separadas por identidad/clave/huella, no compartiendo la constancia de carga como si fueran el mismo evento. Una recepción por producto puede tener varios lotes; multiproducto/SOL futuros. Número comercial normalizado no es UUID de ingreso: permitir recepciones distintas del mismo lote coherente con fecha/costo/proveedor propios (DOC03AI). Ajuste de existencia vencida soloADMIN y no vendible; ninguna entrada ordinaria vencida.

Venta confirmada requiere cabecera, líneas ordenadas, snapshots producto/precio/costo/vendedor/caja, asignaciones por lote, movimiento de efectivo y de inventario, correlativo y resultado idempotente atómicos. El código actual no implementa todas esas garantías: asignaciones y snapshots vendedor/caja son brechas; tampoco se atribuyen tablas genéricas por analogía. Se permiten estructuras equivalentes más simples si preservan cada garantía con evidencia. DraftLine retenidas no sustituyen asignaciones históricas.

RN25 exige venta irrepetible; clave UUID y huella canónica pueden vivir en la entidad confirmada con unicidad y controles de actor/contenido, sin obligación de tabla genérica `idempotency_record`. Misma clave/contenido devuelve original; distinto contenido rechaza. No se requiere cabeceraHTTP si el formulario existente transporta una clave validada con las mismas garantías.

## 2.4 Autorización y exposición

RN29 y DEC12PERMISOS son la matriz única: ADMIN mantiene maestros/personal, ajusta inventario, registra bajas y consulta global; ALMACENERO recibe/da de baja y consulta inventario; VENDEDOR opera solo su turno y consulta propios. Portal técnico no se concede por rol comercial. Históricos/constancia cliente no exponen costos. La normalización/máximo254 y reset trazable de personal se detallan en DOC02-04; no confundir resetADMIN con recuperación por correo futura.

## 2.5 Dinero, costo, tiempo y datos

Dinero Decimal2, costo Decimal4, HALF_UP. RN14 usa físico registrado para promedio móvil, no stock vendible. Venta/baja/ajuste negativo no reponderan por costos de compra restantes; al agotar físico, promedio vigente0 y snapshots previos intactos. Entrada actualiza ponderado, ajuste positivo sigue su política explícita. Costos legacyNULL permanecen desconocidos salvo evidencia inequívoca.

Límite operación venta/efectivo/apertura9,999,999.99; cierre acumulado admite14,2; diferencia=contado−esperado y puede ser negativa. Nuevo descuento discrecional deshabilitado como requisito pendiente de código; históricos permanecen. Base=HALF_UP(total/1.18,2),IGV=total−base describe modelo interno uniforme, no certificación tributaria.

Timestamps UTC, negocio/pantalla America/Lima. Físico suma disponible; vendible requiere fecha>hoy y disponibilidad comercial de producto/categoría. FEFO total fecha→ingreso→ID. No usar CHECK dependiente del reloj. Referencias históricas no se reconstruyen con datos maestros actuales.

'''+constraints+'''## 2.6 Transacciones y orden de locks

El diseño anterior omitía locks de actores incorporados por auditorías. La implementación siguiente debe documentar un orden global compatible con todas las rutas (actor, caja/turno, borrador, producto/lote, contador/derivados), ordenando conjuntos de IDs; no copiar la secuencia histórica de un solo servicio. `PROP-09-LOCK-ORDER-01` y `SEC-15-CONC-02` requieren verificar parejas de operaciones y ausencia de inversiones. La unicidad en BD sigue siendo barrera final. No se considera probado solo por usar `atomic()`.

Idempotencia no habilita leer venta ajena ni aplicar política nueva a una confirmación histórica. Cobro/cierre comparten exclusión de turno; venta/recepción/baja/ajuste comparten producto/lotes y actor revalidado. El resultado concurrente debe corresponder a un orden serial válido. Fallo en cualquier derivado revierte operación completa; reintentos técnicos limitados solo ante error transitorio comprobado, nunca ante validación de negocio.

## 2.7 Contratos web y presentación

Rutas reales se consultan en urls.py y matrices de etapa. Superficies principales: ingreso/salida, empleados, categorías/productos, proveedores, carga/entrada/stock/vencimientos/bajas/ajustes/movimientos, apertura/cierre/turnos, borrador/cobro/constancia/historial. No prometer endpointsREST del diseño histórico ni pantallas de funciones futuras.

Encargos define campos/límites, confirmación de estado, error contextual, consulta propia/global, orden persistido, paginación25 y no mutaciónGET. Pantalla bloqueada tras300s requiere servidor+reautenticación, preserva borrador/turno y no es logout ni bloqueo de ingreso15min. Etiquetas, teclado, foco, ancho estrecho e impresión requieren prueba visual propia.

## 2.8 Seguridad y eventos

Sesión de servidor, rotación/revocación, Argon2id, CSRF en escrituras, HTTPS/cookies seguras en red, permisos dentro del caso de uso, secretos fuera de repositorio y logs sanitizados. Son controles requeridos; configuración productiva no examinada. Portal técnico restringido; tráfico/retención requieren medir entorno y fijar política explícita. No confundir mensajes uniformes con prueba estadística de tiempos ni filtro con evento instrumentado. Contratos DOC01-06 y DOC02-04.

## 2.9 Legado y migración

Cada encargo produce diagnóstico de colisiones, referencias, valores, origen y cobertura histórica antes de migrar. Carga/entrada de una misma familia, costosNULL, orden de líneas antiguo y asignaciones faltantes necesitan tratamiento específico. No inventar historia, fusionar maestros ni actualizar datos del usuario en este trabajo. Preservar migraciones aplicadas; nuevas restricciones requieren ensayo sobre clon y rollback. `sales.0004` añade producto; `sales.0005` añade costo unitario.

'''+operations+gates+'''## 2.17 Exclusiones vigentes

SOL, anulaciones/Yape/fiscalidad, multirrol/múltiples cajas/sedes, productos sin vencimiento o por peso, correo/sesión única/cierre remoto/LOG UI, caja manual/forzada/aprobada y reportes completos permanecen futuros o fuera según09. Mermas, recepción directa, personal y bloqueo de ingreso sí están seleccionados; pantalla300s es nueva puerta del piloto. No ocultar esas brechas bajo exclusiones históricas deSprint1.

## 2.18 Compatibilidad y evidencia

Versiones exactas ejecutadas y hashes están en VERIFICACION.md; compatibilidad esperada y política de soporte en FUENTES_EXTERNAS.md. CI, backup/restore, NFR05/10 y despliegue continúan pendientes de evidencia adecuada. Un dry-run sin migraciones nuevas no demuestra migraciones aplicadas a la base operativa.
'''
    write('02_Diseno_Tecnico_R1_PMV.md',design)
    write('01_Proyecto_y_Releases.md','# 1. Proyecto y releases vigentes\n\n'+notice('01_Proyecto_y_Releases.md')+'''## Objetivo de producto

Control interno de un minimarket con una caja, venta en efectivo, productosUND con vencimiento, tres roles exclusivos y trazabilidad de existencias/dinero. La aplicación no sustituye emisión tributaria autorizada ni acredita todas las condiciones para operar un negocio real.

## Release de consolidación

R1 de consolidación incorpora33 HU seleccionadas,41 futuras y ocho ideas fuera del horizonte; catálogo y selección exactos en08/09. Las nueve HU/40 SP originales son baseline histórica. La ampliación incorpora identidad/personal, catálogo/lector, proveedores, recepción/inventario, historial y bloqueo de puesto antes del piloto, con los encargos de integridad/seguridad de16. La aceptación12/11 es documental; no transforma extras anteriores en aprobaciones históricas.

Criterios de resultado: recepción identificable/idempotente; costo consistente; venta con trazabilidad por lotes y snapshots; límites/roles seguros; inventario/constancias/caja concordantes; evidencia integral reproducible y recuperación ensayada. Descuentos nuevos discrecionales se deshabilitan en el contrato; implementación sigue pendiente.

## Alcance temporal y recursos

No hay fechas, equipo disponible, velocidad ni presupuesto real verificados para el siguiente Sprint. Planning14 y tareas16 son preparación del próximo incremento. Estimaciones académicas216h, capacidad192/240h y tarifaS/25 no se reportan como horas, dinero invertido o capacidad actual. No se reabren ni se renumeran Sprints históricos para aparentar continuidad.

## Responsabilidades

El responsable del producto delegó en el asesor recomendaciones/documentación en esta conversación. Implementación/despliegue y cambios de datos operativos se autorizan aparte. Developers estiman y seleccionan trabajo según capacidad real; la revisión independiente comprueba CA/DoD. No se inventan reuniones o participantes.

## Puertas y riesgos

Antes del piloto: P0/P1 resueltos con evidencia, PG17 objetivo probado, CI/backup/restauración/despliegue y E2E por roles, tratamiento seguro de legado, operación fiscal externa/datos personales aplicables aclarados. Ausencia de lector/teléfono/impresora reales se declara como límite. Las pruebas434 en SQLite no cierran esas puertas.

Mantener una fuente por función: RN07 reglas, HU08 criterios,09 alcance/orden,02 diseño,16 trabajos,03 cobertura,04 evidencia,14 siguiente incremento,21 diferencias actuales. CONSOLIDACION/ENCARGOS es el registro único de decisiones; ESTADO_GENERAL es estado de auditorías. Nunca usar una planificación como evidencia de funcionamiento.
''')
    write('21_Alcance_Actual_y_Diferencias.md','# 21. Alcance y diferencias vigentes\n\n'+notice('21_Alcance_Actual_y_Diferencias.md')+'''## Lo seleccionado y lo comprobado

La selección vigente es33 HU de09, con219 CA base en el catálogo completo y60 criterios suplementarios nuevos en ENCARGOS (más J-CA1..4 de categoría). Software actual y selección difieren.434 pruebas automáticas integradas pasaron en SQLite nuevo; check y makemigrations dry-run pasaron. Se revalidó un subconjunto de historial/idempotencia conPG18.4. Ningún resultado convierte los contratos revisados en implementados.

## Brechas prioritarias verificadas por inspección

| Área | Comportamiento actual / fuente | Requisito vigente | Trabajo |
|---|---|---|---|
| Entrada | register_stock_entry reutiliza carga y no tiene recepción propia | Entrada directa con identidad/idempotencia | DOC03AB/AI |
| Valoración | Entrada excluye vencidos y baja/ajuste repondera lotes restantes | Promedio móvil sobre físico; salidas conservan costo | DOC03AH |
| Venta | Descuenta lotes pero no persiste asignaciones; no snapshots vendedor/caja | RN25/26 con trazabilidad histórica | DEC11MODELO |
| Descuento | Campo/cobro permiten importe discrecional | Nuevas ventas sin descuento, históricos preservados | DEC11DESCUENTOS |
| Bloqueo de puesto | RN22/HUVEN01a no implementado | Servidor bloquea300s, reautenticación | DEC10BLOQUEO |
| Baja/ajuste | Falta constancia dedicada/nuevo lote; motivo vencido forzado | Causa real, constancia y ajuste fiable no vendible | RN05, INV02/03 |
| Movimientos | Kardex parcial sin saldo/filtros completos ni lotes de venta | INV04 completo con legado explícito | DEC08KARDEX |
| Seguridad | Límites tráfico/eventos/admin técnico/retención con brechas | Contratos y medición15 | DOC01/02,SEC15 |
| Historia/caja | OrdenUUID/empates y límites acumulados requieren corrección | Posición persistida/desempate/topes coherentes | DEC11TOPE/DEC12ORDEN |

Detalle, alternativas, decisiones, estado y fuentes precisas: CONSOLIDACION/ENCARGOS. Estas filas no autorizan cambios de código ni DB. Los costosNULL, identidadGTIN antigua y recepción incompleta no se inventan por migración.

## Rectificaciones de auditoría

Etapa09 sí tiene informe y evidencia; se corrige el NOEJECUTADO que arrastraban10–12. Chrome09 contiene67comprobaciones funcionales más control cero_page_errors=68, no70. 04-D tiene evidencia de revocación y deja el caso raw sin petición/servicio fuera de muestra. El fallo de Product._state.adding se corrigió en05-L y está integrado en434pruebas; no mantenerlo abierto por informes antiguos. Un empate de orden de turnos sigue siendo problema de diseño aunque una repetición pase.

05-L prueba interrupción HTTP mientras espera bloqueo antes de escritura; post-escritura/COMMIT/motor siguen pendientes. Soporte12PG usa Client de Django en hilos, no socketsHTTP; la nueva corrida lo describe correctamente. Filtros de VEN05b/CA02 y apertura de detalle/CA03 no se contradicen.

## Fuera de evidencia actual

Etapas13–16 sin informe principal;17 tiene conciliación parcial, no cierre. PG17 no disponible localmente;18.4 no lo reemplaza. XLSX ausente. CI, despliegue real, backup/restore, dispositivos físicos completos, análisis volumétrico y cumplimiento legal no certificados. Fuentes externas y aplicabilidad en el registro homónimo. No se inventa certeza absoluta.
''')
    write('20_Corte_De_Exposicion_Martes.md','# 20. Corte de exposición y estado demostrable\n\n'+notice('20_Corte_De_Exposicion_Martes.md')+'''El corte del martes13/10 es histórico y queda en BASELINE. Este archivo no fija una exposición nueva ni afirma un release terminado.

A12/11 se puede presentar el inventario completo de13etapas, la conciliación de decisiones, los33requisitos seleccionados y la evidencia automática434/434 enSQLite, junto con la revalidación parcialPG18.4. Mostrar expresamente brechas de recepción, valoración, trazabilidad, seguridad y consultas; no vender contratos nuevos como pantallas listas.

Una demostración usa únicamente datos ficticios y el alcance realmente comprobado. Constancia interna no es comprobante fiscal. Preparar recorrido por tres roles y describir exclusiones; la demostración actual no cuenta como revisión independiente/CI/despliegue productivo sin evidencia específica. Próximo incremento y DoD en14; lista de encargos en16; resultado reproducible en04.
''')

if __name__=='__main__':
    rewrite_design_and_guides()
    print('Actualizados diseño, proyecto, alcance y corte de exposición')

STAGES = {
'00':('Inventario y planificación','Inventario completo del corte, no aprobación funcional','DOC00-01/05/07/08/09/12/13; matriz219 y catálogo74+8','Revisión17 de trazabilidad y semántica'),
'01':('Ingreso y bloqueo','Auditado en muestras; seguridad transversal abierta','Tráfico/admin/retención/logs; correo254/IDNA;5fallos/15min','SEC-15-TRAFICO-01 y SEC-15-OBS-01'),
'02':('Sesión y personal','Auditado en muestras; contratos revisados pendientes','Reset/desbloqueo auditado, nombre120, confirmación y concurrencia','DOC-02-04 / SEC-15-CONC-02'),
'03':('Categorías y productos','03-AJ y anexos posteriores contrastados; sin cierre integral','Catálogo/lector aceptados; valoración/recepción/legacy/migraciones pendientes','DOC-03AH-01 / DOC-03AI-01'),
'04':('Proveedores','04-D reconocido; no queda detenido artificialmente en04-C','Revocación muestras04-D; RUC/formato y estado explícito; raw bypass pendiente','DEC-04B-ESTADO-OMITIDO / SEC-15-CONC-02'),
'05':('Carga inicial','05-L vigente; suite integrada elimina fallo heredado','PG17, recuperación postwrite, costos/recepción y despliegue','05-M / CT-ROLLBACK-01-POST-ESCRITURA'),
'06':('Recepción posterior','06-F auditado con conflictos hoy decididos documentalmente','Entrada directa aceptada; recepción propia/costo nuevo sin implementar','DOC-03AI-01 / DOC-03AH-01'),
'07':('Stock y vencimientos','Muestras ejecutadas; políticas/volumen pendientes','Alertas activas vs vencidos físicos, filtros y panel mínimo','DEC-07-VENCIDOS-FILTRO / PT-SEARCH-01'),
'08':('Bajas, ajustes y movimientos','Parcial frente a HU existentes y contratos revisados','Constancia, lote nuevo, costo/motivo y Kardex completo','RN-05 / DEC-08-KARDEX-COMPRAS'),
'09':('Caja','EJECUTADA; se rectifica NOEJECUTADO heredado en10–12','20tests y6casosPG históricos; Chrome67funcionales+1control; checks/topes/orden pendientes','PROP-09-DB-01 / DEC-11-TOPE-EFECTIVO-FORM'),
'10':('Preparación y bloqueo de puesto','Borrador auditado; bloqueo300s no implementado','VEN01a seleccionado antes de piloto; GETprecio/concurrencia/UX','DEC-10-BLOQUEO-INACTIVIDAD / PROP-10-03'),
'11':('Cobro y exactitud','Muestras ejecutadas; integridad y política nuevas pendientes','Lotes/snapshots, nuevos descuentos deshabilitados, límites y caída','DEC-11-MODELO-AUDITORIA-VENTAS'),
'12':('Constancias e historial','Muestras y nueva comprobación parcialPG; sin cierre integral','Permisos/orden/paginación/UX; filtrosCA02 y detalleCA03 conciliados','DEC-12-ORDEN-LINEAS-RECIBO / PROP-12-CAJA-HIST-CHROME-VENDEDOR')
}

def update_audits_and_evidence():
    state='''# Estado general vigente de auditorías · 12/11/2026

Esta tabla sustituye como estado actual las notas anteriores. [Estado anterior íntegro](conciliacion_20261112/BASELINE/auditoria_por_etapas/resultados/ESTADO_GENERAL.md) · [Mapa consolidado](conciliacion_20261112/CONSOLIDACION.md) · [Encargos](conciliacion_20261112/ENCARGOS.md) · [Verificación nueva](conciliacion_20261112/VERIFICACION.md).

Se identificaron13informes originales00–12 y todos sus anexos pertinentes. Esta revisión agrega17 como conciliación documental parcial;13–16 no se declaran ejecutadas. Las decisiones adoptadas12/11 no demuestran implementación.434/434 tests integradosSQLite, check y dry-run aprobados; nueva muestraPG18.4 de consultas/idempotencia. No hay cierre integral ni autorización de código/DB/despliegue.

| Etapa | Fecha del estado | Cobertura | Estado vigente | Bloqueos/decisiones | Próximo cursor |
|---|---|---|---|---|---|
'''
    for number,(name,status,limits,cursor) in STAGES.items():
        state+=f'| [{number}](ETAPA-{number}.md) {name} | 12/11/2026 | Inventario y evidencia del informe/anexos originales | {status} | {limits} | {cursor} |\n'
        original=old(f'auditoria_por_etapas/resultados/ETAPA-{number}.md')
        adenda=f'''# Adenda vigente de ETAPA-{number} · 12/11/2026

**Estado actual:** {status}. **Pendientes compartidos:** {limits}. **Próximo cursor:** {cursor}.

[Mapa consolidado y decisiones](conciliacion_20261112/CONSOLIDACION.md) · [Contratos de implementación](conciliacion_20261112/ENCARGOS.md) · [Verificación integrada](conciliacion_20261112/VERIFICACION.md) · [Informe original íntegro](conciliacion_20261112/BASELINE/auditoria_por_etapas/resultados/ETAPA-{number}.md).

Las decisiones nuevas se aceptan desde12/11 por delegación explícita del usuario. No se cambia el resultado histórico de una muestra ni se declara cerrado el módulo. Requisitos recién revisados requieren nueva implementación/verificación. Las referencias de línea del texto histórico remiten a BASELINE. Los anexos conservan su fecha y vigencia original; los estados actuales se consultan en el mapa.

## Rectificaciones transversales aplicables

Etapa09 sí tiene ejecución/evidencia (Chrome67funcionales+1control), aunque10–12 y estado general antiguos la dejaban pendiente. 04-D acredita revocación en sus muestras; su límite raw sin petición/servicio permanece. El fallo `_state.adding` de inventario fue corregido05-L e incluido en434tests actuales. Los informes antiguos que lo separaban no prueban fallo actual. El empate de orden de turnos no se considera corregido por repetir una corrida. Soporte12PG es DjangoClient concurrente contraPG, no redHTTP por sockets. 05-Linterrupción antes de escribir no prueba caída postwrite. HU-VEN-05b pide filtrosCA02 y detalleCA03; no hay conflicto de líneas expandidas.

---

## Informe y resultados históricos conservados

'''
        write(f'auditoria_por_etapas/resultados/ETAPA-{number}.md',adenda+original)
    for n,name,cursor in [('13','Paneles/reportes y futuro','Inventariar HU-DASH/REP/CONF y extras actuales sin atribuir entrega completa'),('14','Integración y resiliencia','CT-ROLLBACK-01-POST-ESCRITURA; E2E sobre build actual'),('15','Seguridad y datos','SEC15TRAFICO/OBS/ADMIN/CONC/RETENCION y aplicabilidad'),('16','Despliegue y recuperación','PG17; CI; S1-OPS-DB-01/02 y smoke')]:
        state+=f'| {n} {name} | 12/11/2026 | Prompt disponible, sin informe principal localizado | NO EJECUTADA como auditoría completa | No confundir ausencia de prueba con defecto | {cursor} |\n'
    state+='| [17](ETAPA-17.md) Conciliación | 12/11/2026 | Fuentes, decisiones, planning y criterios | DOCUMENTACIÓN ACTUALIZADA; revisión integral parcial | Implementación y pruebasC siguen abiertas | Revisión independiente de contratos y siguiente encargoP0 |\n'
    state+='''\n## Regla de continuidad

El orden de resolución va por integridad/costo/recepción/venta, permisos/seguridad, consultas/UX y evidencia de despliegue. No es obligatorio reejecutar una etapa histórica completa para investigar un caso concreto; conservar su ID y alcance. Los futuros siguen futuros. No declarar cierre por aceptar políticas, generar documentos o aprobar una suite parcial.
'''
    write('auditoria_por_etapas/resultados/ESTADO_GENERAL.md',state)
    write('auditoria_por_etapas/resultados/ETAPA-17.md','''# ETAPA-17 · Conciliación documental y revisión crítica parcial

Fecha12/11/2026. Alcance: inventario de13informes00–12/anexos, contraste de planificación y código pertinente, revisión de vigencia, suite completaSQLite y muestraPG18.4, decisiones por delegación y actualización documental. Exclusión: implementación de cambios funcionales, base operativa, despliegue, auditoría nueva completa13–16 y cierre global.

Entregables: [mapa](conciliacion_20261112/CONSOLIDACION.md), [encargos](conciliacion_20261112/ENCARGOS.md), [índice trazable](conciliacion_20261112/INDICE_IDS.md), [fuentes/huellas](conciliacion_20261112/FUENTES.json), [verificación](conciliacion_20261112/VERIFICACION.md), planning raíz01/02/03/04/07/08/09/14/16/20/21 y controles. Preservación: BASELINE íntegra de138fuentes; código y DB no implementados/modificados por esta conciliación.

Hallazgos:9sí ejecutada;04Dposterior al cursor; fallos heredados mezclados con revisiones; ordinalesQA ambiguos; fuentes Scrum históricas presentadas como actuales; implementación extra sin política; recepción/costo/asignaciones de lote/snapshots/seguridad/consultas todavía incompletas. Se corrigen referencias y selección sin cambiar historia. No se evalúa auditoría por modelo autor, sino por argumentos/evidencia/límites.

Resultados nuevos434/434,check,dry-run y subconjuntoPG en VERIFICACION. Los60criterios suplementarios nuevos no se han ejecutado como software nuevo.33HU seleccionadas/41futuras/ocho ideas;219CA base conservados. La validación estructural final figura en VALIDACION_DOCUMENTAL.json, sin equivaler a revisión humana independiente.

Siguiente cursor: revisión independiente de especificaciones y diagnósticoDOC03AH/AI/DEC11MODELO en clon antes de implementación autorizada. En paralelo investigar C de entorno/tráfico/datos reales. Estado: **PARCIAL; auditoría global abierta**.
''')
    write('04_Evidencias.md','# 4. Evidencias vigentes y procedencia\n\n'+notice('04_Evidencias.md')+f'''## Código integrado

[Verificación12/11]({LINK}/VERIFICACION.md):434/434 testsDjango sin fallos/errores/omitidos, SQLite nuevo;check y dry-run de migraciones aprobados.503archivos protegidos conservados durante la ejecución. Primer intento de soporte fallido conservado aparte. Nueva muestraPG18.4: filtrosNUL/fechaLima, queries constantes y dos reintentos concurrentes→una venta; noHTTP sockets/no navegador.

## Auditorías por etapa

[Estado general](auditoria_por_etapas/resultados/ESTADO_GENERAL.md) enlaza13informes originales con adendas vigentes y17parcial. Cada informe conserva herramientas,base,muestras,omisiones y anexos; no sumar sus contadores ni trasladar aprobación a contratos nuevos. Los artefactos principales antiguos se mantienen en sus rutas; BASELINE conserva documentos de procedencia.

## Documentación nueva

[InventarioCA]({LINK}/INVENTARIO_CA.json), [IDs y referencias]({LINK}/INDICE_IDS.md), [validación estructural]({LINK}/VALIDACION_DOCUMENTAL.json) y [manifiesto de cambios]({LINK}/CAMBIOS.json). La aceptación de políticas no equivale a software implementado;60CA suplementarios nuevos permanecen por verificar tras cambios autorizados.

## Ausencias y límites

XLSXausente;PG17/CI/backup-restore/despliegue/E2E actual completo/NFRvolumen/dispositivos y revisión independiente sin evidencia de cierre. Lo no ejecutado no se marca defecto. Las brechas comprobadas frente a HU seleccionadas sí se mantienen visibles. Las antiguas cifras0/191/202/etc. describen sus cortes originales; no se borran ni se presentan como ejecución actual.
''')
    write('r1-pmv/CONTROL_SPRINTS.md','''# Control vigente de trabajo y Sprints · 12/11/2026

[Planificación vigente](../09_Product_Backlog.md) · [Planning siguiente incremento](../14_Sprint_Planning.md) · [Tareas/dependencias](../16_Task_Breakdown.md) · [Registro histórico íntegro](../auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/r1-pmv/CONTROL_SPRINTS.md).

S1/S2/S3 y sus marcas «completada» son cortes históricos. No se heredan como DoD actual. No existe aquí evidencia de nuevas fechas/capacidad/equipo ni un Sprint nuevo iniciado.33HU seleccionadas para R1 de consolidación;41futuras y ocho ideas fuera. Reactivar empleado corresponde a HU-USR-05, no HU-USR-04. Kardex corresponde a INV04; descuentos no a VEN03; bloqueo ingreso15min no es pantalla300s.

Decisiones12/11 aceptadas por delegación, implementación separada.434pruebas integradasSQLite y muestraPG18.4 no cierran los cambios nuevos. Estado de auditoría en ESTADO_GENERAL; evidencia en04. No se usa Jira. SP originales231 y216h de67tareas no son velocidad ni horas reales; no se suman a nuevas estimaciones.
''')
    write('r1-pmv/evidencias/CONTROL_DE_HORAS_Y_ESTADO.md','''# Control de horas y estado vigente · 12/11/2026

No se dispone de registro verificable de horas reales por persona/tarea en esta revisión. Las216h estimadas,192/240h de capacidad académica,24h de reserva y45.5h de ventana/camino no son horas efectivamente trabajadas. La tarifaS/25 tampoco acredita gasto real. No se inventan tiempos ni costo del proyecto a partir del tiempo del agente.

[Desglose vigente](../../16_Task_Breakdown.md) · [Planning](../../14_Sprint_Planning.md) · [Evidencia](../../04_Evidencias.md) · [Registro anterior íntegro](../../auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/r1-pmv/evidencias/CONTROL_DE_HORAS_Y_ESTADO.md).

Las marcas de entrega histórica conservan su fecha; no cumplen automáticamente la DoD actual. Aceptación documental y software tienen estados distintos. CI, revisión independiente, despliegue y pruebas pendientes no se completan por actualizar este archivo. Jira no se utiliza.
''')
    write('r1-pmv/docs/seguridad.md','''# Seguridad: contrato vigente y evidencia · 12/11/2026

[Diseño](../../02_Diseno_Tecnico_R1_PMV.md) · [Contratos DOC01-06/DOC02-04](../../auditoria_por_etapas/resultados/conciliacion_20261112/ENCARGOS.md) · [Verificación](../../auditoria_por_etapas/resultados/conciliacion_20261112/VERIFICACION.md) · [Baseline](../../auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/r1-pmv/docs/seguridad.md).

Tres roles comerciales exclusivos. `seed_pmv` contiene tres cuentas activas (una por rol) y una cuarta inactiva de prueba; no existe cuarto rol. Semillas no autorizadas en base operativa. Secretos del ambiente no se inspeccionaron ni modificaron.

Sesión servidor/CSRF/Argon2/permisos existentes tienen pruebas acotadas. Middleware revoca sesión rechazada y04D verifica muestras de reactivación; no protege automáticamente escrituras externas a servicios. Revalidar actor/propiedad dentro de la transacción; denegar sin mutación. ConfiguraciónHTTPS/cookies/perímetro productivos no examinados.

Requisitos pendientes: portal técnico restringido, limitación de tráfico medida, retención explícita, eventos fiables y redacción de exc_info, carrerasintegrales y bloqueo300s antes del piloto. ResetADMIN/desbloqueo explícito auditado; cambio de correo/reactivación no limpia sanción silenciosamente como política nueva. Mensajes uniformes5fallos/15min no sustituyen esas capas. HUD-LOGpantalla es futura; logging técnico es actual.

PG17 objetivo;SQLite no demuestra locks. PruebasPG18.4 acotadas no certifican toda seguridad. No rotar secretos, publicar conexiones, modificar.env ni ejecutar semillas por una instrucción histórica. Migración/despliegue requieren autorización separada.
'''.replace('HUD-LOGpantalla','HU-LOG-01/pantalla'))
    write('r1-pmv/docs/alcance_comercial_y_normativo.md','''# Alcance comercial y contraste normativo · 12/11/2026

[Fuentes primarias y límites](../../auditoria_por_etapas/resultados/conciliacion_20261112/FUENTES_EXTERNAS.md) · [Estado anterior](../../auditoria_por_etapas/resultados/conciliacion_20261112/BASELINE/r1-pmv/docs/alcance_comercial_y_normativo.md) · [Alcance actual](../../21_Alcance_Actual_y_Diferencias.md).

La constancia del sistema es control interno sin validez tributaria. SUNAT dispone de canales oficiales comoSEE-SOL y reglas de obligación según contribuyente; régimen/RUC/canal del negocio no están confirmados por el repositorio. El sistema no integra emisión ni conciliación fiscal. El cálculo uniforme18% no prueba tratamiento fiscal correcto de todos los productos. Confirmar aplicabilidad antes de uso real; no transformar una preferencia técnica en obligación legal.

Se tratan cuentas/proveedores y hace falta revisar finalidad, responsables, acceso, retención, ejercicio de derechos e incidentes según tratamiento real y normativa aplicable. Se corroboró la existencia del reglamentoDS016-2024-JUS y su entrada en vigor general mediante fuentes oficiales; no se acredita cumplimiento integral, ni se fija un plazo normativo ficticio de logs. Un enlaceMINJUSDH devolvió418 y se sustituyó la corroboración porANPD/ElPeruano. Consultar FUENTES_EXTERNAS para referencias directas.

No se verificó la situación real de atención al consumidor ni se seleccionó Libro de Reclamaciones como módulo. No inferir ausencia del mecanismo del negocio porque no esté integrado al software. La referencia histórica se conserva, sin convertirla en certificación vigente.

Operación adoptada en esta versión: cajaúnica/efectivo/UND/vencimiento; recepción directa con compra autorizada externamente como política propuesta y aceptada hoy por delegación, no hecho observado del minimarket; costo promedio interno sobre físico; nuevos descuentos discrecionales deshabilitados en contrato; futuros de Yape/anulación/SOL/reportes y facturación separados. Código aún debe implementar varias de estas decisiones. Condiciones técnicas antes del piloto: P0/P1,PG17,CI,recuperación,despliegue y evidencia integral.
''')

if __name__=='__main__':
    update_audits_and_evidence()
    print('Actualizadas13adendas,estado general,17parcial,evidencias y controles')

def index_ids():
    reports=list((BASE/'auditoria_por_etapas/resultados').glob('ETAPA-*.md'))
    reports+=list((BASE/'auditoria_por_etapas/resultados/anexos').glob('*.md'))
    reports += [BASE/n for n in ('02_Diseno_Tecnico_R1_PMV.md','03_Matriz_de_Trazabilidad_y_Pruebas.md','16_Task_Breakdown.md')]
    pattern=re.compile(r'(?<![A-Za-z0-9_-])(?:DOC-\d{2}[A-Z]*-[A-Z0-9][A-Za-z0-9_-]*|DOC\d{2}-\d+|DEC-[A-Za-z0-9][A-Za-z0-9_-]*|PROP-[A-Za-z0-9][A-Za-z0-9_-]*|(?:OBS|SEC|SUP|E00|E01|E02|E03|CT|PT|MT|INT|ST|BUG|FIX|DEF|DT|NFR|DB|S1)-[A-Za-z0-9][A-Za-z0-9_-]*|(?:SUP|FIX|DEF)\d{2}[A-Z]*-\d+)')
    data={}
    for p in sorted(reports):
        for n,line in enumerate(read(p).splitlines(),1):
            for m in pattern.finditer(line):
                ident=m[0].rstrip('-_')
                if ident.endswith(('DOC-02','PROP-E02','PROP-12')): continue
                key=(p.relative_to(BASE).as_posix(),n)
                if key not in data.setdefault(ident,[]): data[ident].append(key)
    maprows=[]
    consolidated=read(HERE/'CONSOLIDACION.md')
    lines=[]
    for line in consolidated.splitlines():
        cells=[c.strip() for c in line.strip('|').split('|')]
        if line.startswith('|') and len(cells)==7 and ' · P' in cells[3]:
            cls,pri=cells[3].split(' · ',1)
            cells=cells[:3]+[cls,pri]+cells[4:]
            line='| '+' | '.join(cells)+' |'
        elif line.startswith('| ID / alias compartidos |'):
            line=line.replace('Clase / prioridad','Clasificación | Prioridad')
        elif line=='|---|---|---|---|---|---|---|':
            line='|---|---|---|---|---|---|---|---|'
        lines.append(line)
    write(HERE.relative_to(ROOT)/'CONSOLIDACION.md','\n'.join(lines))
    for line in lines:
        c=[x.strip() for x in line.strip('|').split('|')]
        if len(c)==8 and c[4].startswith('P'): maprows.append(c)
    def family(ident):
        aliases={'DOC03-02':'DOC03-01','DEC-04':'DOC-00-04','E00-COV-01':'DOC-00-14','E00-HU02':'PROP-E00-HU-02','E03-OBS-01':'OBS-00-15'}
        lookup=aliases.get(ident,ident)
        for c in maprows:
            if re.search(r'(?<![A-Za-z0-9_-])'+re.escape(lookup)+r'(?![A-Za-z0-9_-])',c[0]): return c[0],c[3]+' · '+c[4],c[5]
        if ident=='DEC-09':return 'Búsqueda POS; lector de altaPROD03 distinto de venta','B/D · P2','Conservar consulta por código/nombre y evidencia10; no exigir lector físico por una decisión de búsqueda digitada'
        if ident.startswith(('E00-ENV-01','E00-HTTP-')): return 'Aislamiento/denegación sin mutación de muestras00','D · P1','Muestra acreditada en su fuente; otras rutas/métodos no cubiertos automáticamente'
        if ident.startswith(('DT-','DB-','NFR-','S1-')): return 'Diseño/tarea original preservada; encargo vigente en02/16','B/C · según criterio','No equivale a trabajo ejecutado; conservar ID y revisar requisito actualizado/evidencia'
        if ident.startswith(('CT-','PT-','MT-','INT-','ST-')): return 'Verificación por escenario original','C · P1/P2','Consultar resultado exacto por corte; no se hereda aprobado por mención ni por suite general'
        if ident.startswith(('BUG-','FIX','DEF','E00-UI','E02-U','E02-R','E02-P','E02-F')): return 'Hallazgo/prueba/superficie histórico; no decisión comercial adicional','D/C · según muestra','Conservar observación original; comparar resultado posterior y contratos nuevos'
        if 'RET-' in ident or ident in ('PROP-E01-HU-01',) or ident.startswith('PROP-E02-HU-'): return 'Funcionalidades futuras / refinamiento HU existente','E · P3','No seleccionado; no crear HU duplicada'
        if ident.startswith(('PROP-E00','DOC-00')): return 'DOC-00-01 / trazabilidad, alcance y extras','B · P1','Incorporado al corte vigente; descuento/category/stock/panel según contratos, no aprobación automática del código'
        if ident.startswith(('PROP-E01','DOC-01','SEC-15')): return 'DOC-01-06 / seguridad técnica y evidencia','B/C · P1','Contrato o investigación abierta; tráfico/retención/despliegue no inventados'
        if ident.startswith('E01-'):return 'Inventario de campos, riesgos o pruebas de acceso','D/C · según muestra','Elemento de auditoría01; leer resultado específico antes de asumir cumplimiento actual'
        if ident.startswith('E03-'):return 'Inventario de catálogo y superficie','D/C · según muestra','Elemento de auditoría03; conservar revisiones posteriores por identidad y estado'
        if ident.startswith(('PROP-E02','DOC-02','E02-')): return 'DOC-02-04 / sesión y personal','B/C · P1/P2','Refinamiento o evidencia de personal; sin implementación nueva por este documento'
        if ident.startswith(('PROP-03','DEC-03','OBS-03','PROP-E03')):
            if any(x in ident for x in ('03X','03G','03K')): return 'DEC-03X-IDENTIDAD / lector y clasificación legacy','D/C · P1','Muestras O/P/Y/Z; legado/dispositivo no cubierto requiere prueba'
            return 'Catálogo, DOC-03AH-01/DOC-03AI-01 y alcance','B/C · P1/P2','Conservar ID de propuesta; garantías de catálogo y recepción/valoración en contratos'
        if ident.startswith(('PROP-04','OBS-04','DOC-04','SUP04')): return 'DEC-04B-ESTADO-OMITIDO / proveedor y revocación','B/D/C · P1/P2','Proveedor con destino explícito, muestra04D y límites de acceso; futuras ediciones separadas'
        if ident.startswith(('PROP-05','OBS-05')): return 'Carga inicial, límites y evidencia propia','B/C · P1','Contrato entradas y validación; correcciones posteriores05/07 no abren decisión nueva'
        if ident.startswith('PROP-06'): return 'DOC-03AB/AH/AI / recepción y costo','B/C · P0/P1','Recepción directa aceptada; identidad/valoración pendientes'
        if ident.startswith('PROP-07'): return 'DEC-07-VENCIDOS-FILTRO / alertas y rendimiento','B/C · P2','Contrato panel/alertas; medir antes de índice'
        if ident.startswith('PROP-08'): return 'RN-05 / DEC-08-KARDEX-COMPRAS y constancia','B/C · P1','Completar HU existentes y probar contratos'
        if ident.startswith('PROP-09'): return 'Caja, checks y orden de locks','B/C · P0/P1','Cumplir integridad; funciones futurasCAJA separadas'
        if ident.startswith('PROP-10'): return 'Bloqueo de pantalla, borrador y consulta','B/C · P1/P2','VEN01a seleccionado; VEN04 completo futuro; GET/qty/concurrencia pendientes'
        if ident.startswith('PROP-11'): return 'Integridad de venta y política de descuento','B/C · P0/P1','Lotes/atómica/límites; descuento futuro no se habilita'
        if ident.startswith('PROP-12'): return 'Historia, permisos, orden y paginación','B/C · P2','Contrato de consulta/UX; evidencia específica pendiente'
        return 'Investigación/documentación transversal del escenario original','C · P2','No se afirma resuelto; conservar fuente y revisar caso antes de aceptar entrega'
    structured=[]
    md='''# Índice de identificadores originales y procedencia

Extracción de los13informes originales y59anexosMarkdown preservados, más diseño/matriz/desglose originales para conservarDT/DB/NFR/S1. Incluye propuestas/decisiones, casos de prueba, hallazgos y elementos de interfaz: **no todos son pendientes ni preguntas de negocio**. La clasificación de la familia es una guía de tratamiento; las filas D/C requieren respetar el resultado/alcance exacto de la fuente, nunca dan todos los casos por resueltos. El mapa consolidado registra decisiones compartidas; el índice evita perder alias o renumerar IDs. Los rangos expresados en la fuente se conservan allí; no se inventa un ID inexistente para expandirlos.

Las líneas remiten a BASELINE, anterior a adendas. JSON conserva todas las apariciones; la tabla muestra la primera y cantidad. CriteriosHU individuales: INVENTARIO_CA.json/matriz03; contratos actuales: ENCARGOS. No se atribuye defecto a una mera mención.

| ID original | Familia compartida | Tratamiento | Primera fuente (línea original) | Apariciones |
|---|---|---|---|---:|
'''
    for ident,refs in sorted(data.items()):
        fam,cls,state=family(ident)
        structured.append({'id':ident,'group':fam,'classification':cls,'current_treatment':state,'references':[{'file':p,'line':n} for p,n in refs]})
        p,n=refs[0]
        md+=f'| {ident} | {fam} | {cls}: {state} | [{Path(p).name}](BASELINE/{p}):{n} | {len(refs)} |\n'
    write(HERE.relative_to(ROOT)/'INDICE_IDS.md',md)
    write(HERE.relative_to(ROOT)/'INDICE_IDS.json',json.dumps(structured,ensure_ascii=False,indent=2))
    return len(structured)

if __name__=='__main__':
    print('Identificadores históricos trazados:',index_ids())

def final_consistency():
    s=read(ROOT/'02_Diseno_Tecnico_R1_PMV.md')
    rows=re.findall(r'^\| `DT-\d+`[^\n]+',old('02_Diseno_Tecnico_R1_PMV.md'),re.M)
    dt='\n## 2.19 Trazabilidad de decisiones técnicas DT\n\nLos IDs originales se conservan; sus formulaciones vigentes son las siguientes. No son evidencia de ejecución.\n\n| ID | Decisión vigente | Aplicabilidad |\n|---|---|---|\n'
    decisions=[
        ('DT-01','Web interna responsiva, mismo origen','Conservada; pruebas visuales por alcance'),
        ('DT-02','Monolito Django5.2/Python3.12, templates;HTMX opcional','Python3.12.10/Django5.2.18 ejecutados; otras versiones no acreditadas aquí'),
        ('DT-03','PostgreSQL17 objetivo y migraciones nativas','18.4 evidencia parcial; no actualizar motor sin plan'),
        ('DT-04','Tres roles exclusivos;3cuentas activas +1inactiva ficticia','Alineado con seed_pmv; ninguna cuenta/rol real inferido'),
        ('DT-05','Sesión servidor, cookies seguras/CSRF/Argon2','Despliegue real no verificado'),
        ('DT-06','Cualquier categoría activa,UND,vencimiento; ajuste vencido excepcional no vendible','DOC03-01 y RN03 vigente'),
        ('DT-07','Lote normalizado y recepción propia;FEFO fecha/ingreso/ID','DOC03AI/DEC05ESPACIOS sustituyen unicidad global producto+número'),
        ('DT-08','Decimal2/4,HALF_UP; costo móvil físico y topes separados','RN14 y DEC11TOPE; fiscalidad real pendiente'),
        ('DT-09','Salir conserva turno; descarta borrador con confirmación','RN30; bloqueo pantalla es otro flujo'),
        ('DT-10','Caja única y turnoOPEN global único','Permisos/locks/constraint y pruebas concurrentes'),
        ('DT-11','BorradorACTIVE solo con líneas, sin reserva','GET no muta; cantidad1..999999'),
        ('DT-12','V-00000001 global único, ascendente e inmutable','Idempotencia y atomicidad completos'),
        ('DT-13','Local,CI efímero,demostración; redBD privada','DockerCompose del diseño no acredita despliegue real'),
        ('DT-14','Backupcustom/manifiesto/SHA256;7diarias+4semanales;restore aislado','Objetivo de diseño, sin eliminación operativa ni restauración verificada aquí'),
        ('DT-15','Volumen de referencia2,000productos/20,000lotes/300ventas-día','PruebasNFR05 pendientes; no estimación de actividad real')]
    assert len(rows)==len(decisions)==15
    for row in decisions:dt+='| '+' | '.join(row)+' |\n'
    write('02_Diseno_Tecnico_R1_PMV.md',s+dt)
    # Correcciones precisas detectadas al comprobar el código actual.
    for name in ['07_Reglas_de_Negocio.md','08_Historias_de_Usuario.md','16_Task_Breakdown.md']:
        s=read(ROOT/name)
        if name.startswith('07_'):
            s=s.replace('R1-PMV lo registra y las historias posteriores implementan sus alertas','el alcance vigente incluye alertas según producto/categoría activos y vencidos físicos')
            s=s.replace('En Sprint 1, `HU-PROD-02` solo registra y recupera este umbral; no se exige todavía una alerta visual. Cuando se implementen `HU-PROD-01`, `HU-PROD-04`, `HU-SOL-01`, `HU-REP-05` o `HU-DASH-03`, las existencias vendibles iguales o inferiores al umbral configurado —no siempre a 10— activarán las señales, sugerencias o reportes descritos por cada historia.', 'El alcance vigente exige alerta de stock vendible igual o inferior al mínimo configurado para producto y categoría activos, de forma coherente en catálogo, stock y panel mínimo. Los vencidos físicos se muestran aunque estén comercialmente inactivos. SOL/REP/DASH completos siguen futuros; no se atribuye su entrega a esta alerta.')
            s=s.replace('Si una persona ingresa una contraseña incorrecta 5 veces consecutivas para una cuenta reconocida, esa cuenta se bloquea por 15 minutos para proteger el acceso.', 'Cinco intentos fallidos consecutivos bloquean el identificador normalizado durante 15 minutos, con comportamiento uniforme para identificador reconocido, inexistente o cuenta inactiva, evitando revelar existencia/estado. El reset administrativo y desbloqueo explícito siguen DOC-02-04; un cambio de correo o reactivación no limpia silenciosamente la sanción.')
            s=s.replace('Esta condición se exige al crear cuentas de empleados o al cambiar la clave mediante recuperación.', 'Esta condición se exige al crear cuentas o restablecer contraseña mediante ADMIN; también se aplicará al flujo de recuperación cuando sea seleccionado y refinado.')
            s=s.replace('Esta ruta mínima no equivale al historial general previsto en `HU-VEN-05a` y `HU-VEN-05b`.', 'Esta ruta mínima no sustituye los historiales seleccionados HU-VEN-05a y HU-VEN-05b, que tienen sus propios filtros/criterios y permisos.')
            s=s.replace('El comprobante de pago oficial exigido por la ley (boleta de venta o factura) se emite por fuera del sistema mediante el canal autorizado que utiliza el minimarket.', 'La emisión oficial que corresponda al régimen real debe resolverse por un canal autorizado externo; el repositorio no demuestra qué canal utiliza el negocio ni su aplicabilidad tributaria concreta.')
            s=s.replace('La boleta o factura real se entrega por el canal autorizado habitual.', 'La boleta o factura que corresponda se emite mediante el canal externo autorizado; su operación real debe confirmarse antes del piloto.')
            s=s.replace('| HU-INV-01a, HU-INV-03, HU-SOL-05a, HU-SOL-05b |','| HU-INV-01a, HU-INV-01b, HU-INV-03; HU-SOL-05a/05b futuros |')
            s=s.replace('| HU-INV-01a, HU-INV-01b, HU-SOL-05a, HU-SOL-05b, HU-REP-07 |','| HU-INV-01a/01b/02/03, HU-VEN-01c; HU-SOL-05a/05b y HU-REP-07 futuros |')
            s=s.replace('Cada vez que el encargado del almacén registre una baja de mercadería,','Cada vez que ADMIN o ALMACENERO registre una baja de mercadería,')
            s=s.replace('De este modo, los reportes posteriores de ganancia reflejan la rentabilidad real de la operación y no se distorsionan si con compras posteriores cambia el costo promedio de ese producto en el almacén.', 'Esto permite calcular margen bruto histórico según el costo registrado, sin sustituirlo por promedios de compras posteriores. No demuestra rentabilidad neta del negocio: faltan gastos y otros factores. Cuando el costo histórico sea desconocido, el reporte debe informar esa cobertura y no presentar margen completo ni usar el costo actual como sustituto.')
        if name.startswith('08_'):
            s=s.replace('Como administrador, quiero registrar ajustes positivos o negativos tras contar físicamente los estantes,','Como administrador, quiero registrar ajustes positivos o negativos de productos con carga inicial confirmada tras contar físicamente los estantes,')
            s=s.replace('Como administrador o dueño, quiero consultar el historial de turnos pasados con sus totales de ventas y cuadres, para revisar diferencias de dinero y desempeño.', 'Como ADMIN quiero consultar todos los turnos y como VENDEDOR solo los propios, incluidos los cerrados, con sus ventas y cuadres, para revisar diferencias sin acceder al dinero de otro empleado.')
            s=s.replace('Dado que accedo al historial de turnos, cuando la lista carga, entonces veo por cada turno:', 'Dado que accedo al historial de turnos autorizado (ADMIN global, VENDEDOR solo propios), cuando la lista carga, entonces veo por cada turno:')
            s=s.replace('Dado que aplico filtros por vendedor o rango de fechas, cuando consulto, entonces la pantalla muestra los turnos correspondientes.', 'Dado que aplico rango de fechas y, solo como ADMIN, filtro por vendedor, cuando consulto, entonces muestra turnos correspondientes sin ampliar el conjunto autorizado ni permitir acceso directo a un turno ajeno.')
            s=s.replace('entonces el total cobrado en efectivo y canales digitales coincide con los registros internos guardados.', 'entonces el total en efectivo coincide con los registros confirmados; los canales digitales no se presentan como disponibles hasta seleccionar e implementar HU-VEN-07.')
            s=s.replace('Los cambios de este corte afectan USR03/CA01, INV01a/CA02, INV01b/CA01, INV02/CA02, INV03/CA01 e INV04/CA02;', 'Los cambios de este corte afectan USR03/CA01, INV01a/CA02, INV01b/CA01, INV02/CA02, INV03/CA01, INV04/CA02, CAJA05/CA01–02 y VEN05a/CA02;')
            s=s.replace('sin exigir todavía una alerta visual en Sprint 1 (RN-06; PROP-03C-LIMITES aceptada, 10/11/2026)', 'y el alcance vigente aplica alertas coherentes con RN-06 (PROP-03C-LIMITES ratificada por delegación el12/11/2026; la procedencia anterior se conserva en BASELINE)')
            s=s.replace('producto enlatado activo por nombre o digitando su código de barras', 'producto activo de cualquier categoría activa del alcanceUND/vencimiento, por nombre o digitando su código de barras')
            s=s.replace('sin requerir lector físico en Sprint 1', 'sin requerir lector físico para esta consultaPOS; el lector del altaPROD03 tiene su propio contrato')
            s=s.replace('en Sprint 1 los ingresos posteriores a la apertura', 'en el alcance vigente los ingresos posteriores a la apertura')
            s=s.replace('Los cambios de este corte afectan USR03/CA01, INV01a/CA02,', 'Los cambios de este corte afectan USR03/CA01, PROD02/CA04, VEN01b/CA02, INV01a/CA02,')
            s=s.replace('cuando se confirma una recepción posterior directa confirmada por ALMACENERO,', 'cuando ALMACENERO confirma una recepción posterior directa,')
            s=s.replace('Dado que un producto ya completó su carga inicial y tiene existencias previas,', 'Dado que un producto ya completó su carga inicial, tenga o no existencias remanentes,')
            s=s.replace('entonces exige un número comercial no vacío que normaliza a mayúsculas y que no se repita dentro de la misma carga; las recepciones posteriores conservan identidad propia conforme a DOC-03AI-01, una cantidad entera positiva, un costo unitario positivo con máximo cuatro decimales y una fecha de vencimiento posterior a la fecha actual de `America/Lima` (RN-03).', 'entonces exige número comercial no vacío normalizado y no repetido dentro de la carga, cantidad entera positiva, costo unitario positivo con máximo cuatro decimales y vencimiento posterior a hoy en America/Lima (RN-03); límites y normalización siguen ENCARGOS/DEC-05-LOTE-ESPACIOS. Las recepciones posteriores conservan identidad propia conforme a DOC-03AI-01.')
            for hu,rules in [('HU-INV-01b','RN-01, RN-03, RN-14, RN-19, RN-29'),('HU-INV-02','RN-04, RN-05, RN-14, RN-20, RN-29'),('HU-INV-03','RN-01, RN-03, RN-14, RN-29'),('HU-INV-04','RN-01, RN-14, RN-25, RN-28, RN-29'),('HU-CAJA-05','RN-10, RN-29')]:
                pattern=r'(### '+re.escape(hu)+r' ·[^\n]+\n(?:(?!### ).)*?- \*\*Reglas de negocio:\*\* )[^\n]+'
                s,n=re.subn(pattern,lambda m:m[1]+rules,s,count=1,flags=re.S)
                assert n==1,hu
        write(name,s)
    # Mejorar espaciado de términos frecuentes sin alterar IDs, código, rutas ni URLs.
    replacements={'13informes':'13 informes','59anexos':'59 anexos','80archivos':'80 archivos','138fuentes':'138 fuentes','33HU':'33 HU','41futuras':'41 futuras','219CA':'219 CA','60criterios':'60 criterios','434pruebas':'434 pruebas','434tests':'434 tests','503archivos':'503 archivos','67comprobaciones':'67 comprobaciones','68elementos':'68 elementos','67funcionales':'67 funcionales','20tests':'20 tests','6casosPG':'6 casos PG','15ventas':'15 ventas','74historias':'74 historias','33requisitos':'33 requisitos','60CA':'60 CA','219criterios':'219 criterios','21encargos':'21 encargos','13etapas':'13 etapas','13adendas':'13 adendas','antes12/11':'antes del 12/11','desde12/11':'desde el 12/11','por delegación12/11':'por delegación del 12/11','Fecha12/11':'Fecha: 12/11','Consulta:12/11':'Consulta: 12/11','A12/11':'A 12/11','300segundos':'300 segundos','cuentas activas3':'cuentas activas 3','verificación12/11':'verificación del 12/11'}
    docs=[p for p in ROOT.glob('*.md') if p.name not in ('Argon auditoria 02.md','REPORTE_CAOS_Y_UX_QA.md','PLAN DE CHATGPT.MD')]
    docs += [HERE/n for n in ['CONSOLIDACION.md','ENCARGOS.md','VERIFICACION.md','FUENTES_EXTERNAS.md','INDICE_IDS.md']]
    docs += [ROOT/'auditoria_por_etapas/resultados/ESTADO_GENERAL.md',ROOT/'auditoria_por_etapas/resultados/ETAPA-17.md',ROOT/'r1-pmv/CONTROL_SPRINTS.md',ROOT/'r1-pmv/evidencias/CONTROL_DE_HORAS_Y_ESTADO.md',ROOT/'r1-pmv/docs/seguridad.md',ROOT/'r1-pmv/docs/alcance_comercial_y_normativo.md']
    for p in docs:
        s=read(p)
        for before,after in replacements.items():s=s.replace(before,after)
        write(p.relative_to(ROOT),s)
    # Este plan es exclusivamente histórico; se conserva byte a byte, sin retoques editoriales.
    (ROOT/'PLAN DE CHATGPT.MD').write_bytes((BASE/'PLAN DE CHATGPT.MD').read_bytes())

if __name__=='__main__':
    final_consistency()
    # La matriz se deriva del texto definitivo, no de la versión anterior al ajuste editorial.
    inventory_criteria()
