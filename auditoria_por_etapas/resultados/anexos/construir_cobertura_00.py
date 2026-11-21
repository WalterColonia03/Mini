"""Build a coverage index, without running application code or tests."""
from pathlib import Path
import csv
import json
import re
from collections import Counter

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
plan = json.loads((OUT / 'ETAPA-00-planificacion.json').read_text(encoding='utf-8'))
with (OUT / 'ETAPA-00-inventario-codigo.csv').open(encoding='utf-8-sig', newline='') as f:
    code = list(csv.DictReader(f))
routes = {r['identificador']: r for r in code if r['tipo'] == 'ruta'}
sources = {}

def line_at(source):
    path, number = source.rsplit(':', 1)
    if path not in sources:
        sources[path] = (ROOT / path).read_text(encoding='utf-8-sig').splitlines()
    return sources[path][int(number) - 1].strip()

# Explicit candidate locations, not a declaration of CA implementation.
by_hu = {
    'HU-AUTH-01': ['login','dashboard'], 'HU-AUTH-02':['login'], 'HU-AUTH-03':['logout'],
    'HU-AUTH-04a':['login','logout'], 'HU-AUTH-04b':['logout','sales-draft'],
    'HU-USR-01':['employee-list'], 'HU-USR-02':['employee-create'],
    'HU-USR-03':['employee-edit'], 'HU-USR-04':['employee-deactivate'],
    'HU-USR-05':['employee-deactivate'],
    'HU-CAT-01':['category-list'], 'HU-CAT-02':['category-create'],
    'HU-PROD-01':['product-list'], 'HU-PROD-02':['product-entry','product-created','product-created-alias'],
    'HU-PROD-04':['product-edit'], 'HU-PROD-05':['product-toggle'],
    'HU-PROD-06':['product-expirations'],
    'HU-PROV-01':['supplier-list'], 'HU-PROV-02':['supplier-create'], 'HU-PROV-04':['supplier-toggle'],
    'HU-INV-01a':['inventory-load','inventory-load-created','inventory-load-created-alias'],
    'HU-INV-01b':['stock-entry'], 'HU-INV-02':['stock-writeoff'],
    'HU-INV-03':['physical-adjustment'], 'HU-INV-04':['product-movements'],
    'HU-CAJA-01':['cash-open','cash-shift-opened'], 'HU-CAJA-02':['cash-close','cash-shift-closed'],
    'HU-CAJA-05':['cash-shift-history'],
    'HU-VEN-01b':['sales-draft','sales-line-update','sales-line-remove','sales-draft-discard'],
    'HU-VEN-01c':['sales-checkout'], 'HU-VEN-02a':['sales-receipt'],
    'HU-VEN-04':['sales-draft'], 'HU-VEN-05a':['sales-shift-history'], 'HU-VEN-05b':['sales-history'],
    'HU-DASH-01':['dashboard'], 'HU-DASH-03':['dashboard','stock-overview','product-expirations'],
    'HU-REP-05':['stock-overview'], 'HU-REP-06':['stock-overview'],
}
modules = {'AUTH':['identity'], 'USR':['identity'], 'LOG':['identity'],
           'CAT':['catalog'], 'PROD':['catalog'], 'PROV':['inventory'],
           'INV':['inventory','catalog'], 'SOL':['inventory'], 'CAJA':['cash'],
           'VEN':['sales'], 'CONF':['config'], 'DASH':['identity'],
           'REP':['identity','sales','inventory'], 'CLI':[]}

def stage(hu):
    ident, module = hu['id'], hu['modulo']
    if module == 'AUTH': return '02' if ident in {'HU-AUTH-03','HU-AUTH-04a','HU-AUTH-04b'} else '01'
    if module == 'USR': return '02'
    if module in {'CAT','PROD'}: return '07' if ident == 'HU-PROD-06' else '03'
    if module == 'PROV': return '04'
    if module == 'INV': return '05' if ident == 'HU-INV-01a' else ('06' if ident == 'HU-INV-01b' else '08')
    if module == 'SOL': return '06'
    if module == 'CAJA': return '09'
    if module == 'VEN':
        if ident in {'HU-VEN-01a','HU-VEN-01b','HU-VEN-04'}: return '10'
        if ident in {'HU-VEN-02a','HU-VEN-05a','HU-VEN-05b','HU-VEN-02b','HU-VEN-02c','HU-VEN-03'}: return '12'
        return '11'
    return '13'

def candidate_details(names):
    selected = [routes[n] for n in names]
    return {
        'rutas_candidatas': '; '.join(r['detalle'] for r in selected) or 'SIN RUTA ASIGNADA: localizar o mantener futuro',
        'vistas_candidatas': '; '.join(sorted({r['vista'] for r in selected if r['vista']})),
        'pantallas_candidatas': '; '.join(sorted({r['plantillas'] for r in selected if r['plantillas']})),
        'roles_codigo_candidatos': '; '.join(sorted({r['roles'] for r in selected if r['roles']})),
    }

def model_refs(mods):
    return '; '.join(f"{r['identificador']} ({r['fuente']}:{r['linea']})" for r in code if r['tipo']=='modelo' and r['modulo'] in mods)

def test_refs(mods):
    return '; '.join(sorted({r['fuente'] for r in code if r['tipo']=='prueba_definida' and r['modulo'] in mods}))

hist = {r['criterio']: r for r in plan['matriz_historica_r1']}
rows = []
for hu in plan['historias']:
    mods, primary = modules[hu['modulo']], stage(hu)
    common = {
        'hu':hu['id'], 'modulo_plan':hu['modulo'], 'actor_plan':hu['actor'],
        'seleccion_documental':hu['seleccion'], 'fuente_hu':hu['fuente_hu'],
        'fuente_backlog':hu.get('fuente_backlog',''),
        'adicional_declarado':str(hu.get('adicional_declarado') or ''),
        'etapa_primaria':primary, 'modulos_codigo_candidatos':'; '.join(mods),
        'reglas':'; '.join(hu['reglas']), 'dependencias_hu':'; '.join(hu['dependencias']),
        'modelos_candidatos_por_modulo':model_refs(mods),
        'pruebas_definidas_candidatas_por_modulo':test_refs(mods),
        'tipo_vinculo':'CANDIDATO DE LOCALIZACION; no equivalencia CA-prueba verificada',
        'estado_ejecucion':'NO EJECUTADO', 'evidencia_nueva':'NINGUNA EN ESTA MATRIZ; ver casos bootstrap separados de ETAPA-00',
        'observado':'Identificador y fuentes inventariados; comportamiento del CA no examinado',
        'prioridad_revision':'P1 (R1/seguridad)' if hu['seleccion']=='R1 SELECCIONADO' or hu['modulo']=='AUTH' else 'P2 (conciliacion/futuro)',
        'siguiente_accion':f'Etapa {primary}: conciliar alcance; inventariar campos y ejecutar criterio con servidor, persistencia y roles si seleccionado',
    }
    common.update(candidate_details(by_hu.get(hu['id'],[])))
    if not hu['criterios']:
        exact = next((f'08_Historias_de_Usuario.md:{i}' for i,line in enumerate((ROOT/'08_Historias_de_Usuario.md').read_text(encoding='utf-8-sig').splitlines(),1)
                      if 841 <= i <= 855 and hu['id'] in line),hu['fuente_hu'])
        rows.append(common | {'tipo_registro':'IDEA_SIN_CA', 'id':hu['id'], 'fuente':exact,
                              'requisito_o_grupo':line_at(exact), 'estado_revision':'PREVISTO/FUTURO',
                              'esperado':'Fuera del horizonte: no exigir implementacion sin decision de incorporacion',
                              'siguiente_accion':'Mantener idea fuera del horizonte; documentar decision antes de crear CA o probar funcionalidad'})
        continue
    for ca in hu['criterios']:
        old = hist.get(ca['id'],{})
        extra = ''
        if hu['id']=='HU-PROD-01':
            extra = 'CONFLICTO A CONCILIAR: actor vendedor en 08:204 vs ADMIN/ALMACENERO en catalog/views.py:77; detalle en nota MD'
        rows.append(common | {'tipo_registro':'CA_BASE', 'id':ca['id'], 'fuente':ca['fuente'],
                              'requisito_o_grupo':line_at(ca['fuente']), 'estado_revision':'NO EXAMINADO',
                              'esperado':'Criterio de la fuente; confirmar vigencia antes de evaluar',
                              'conflicto_o_limite':extra,
                              'fuente_matriz_historica':old.get('fuente',''),
                              'pruebas_planificadas_historicas':'; '.join(old.get('pruebas_planificadas',[]))})

qa = [
    (869,'02',['employee-list','employee-edit'],['identity']),
    (870,'09',['cash-open','cash-shift-opened','cash-shift-history'],['cash']),
    (871,'08',['stock-writeoff','physical-adjustment'],['inventory']),
    (872,'08',['product-edit','product-movements','sales-receipt'],['catalog','inventory','sales']),
    (873,'05',['inventory-load','stock-entry','inventory-load-created','product-movements'],['inventory']),
    (874,'11',['sales-draft','sales-checkout'],['sales']),
    (875,'12',['sales-receipt','sales-history','sales-shift-history'],['sales']),
    (876,'03',['category-list','category-toggle','product-entry','product-edit'],['catalog','inventory','sales']),
    (877,'01',['login','dashboard','logout'],['identity']),
]
for lineno, primary, names, mods in qa:
    source = f'08_Historias_de_Usuario.md:{lineno}'
    raw = line_at(source)
    cells = [cell.strip() for cell in raw.strip('|').split('|')]
    rows.append({'tipo_registro':'GRUPO_QA_HISTORICO', 'id':f'QA-HIST-08-L{lineno}',
                 'fuente':source,'requisito_o_grupo':cells[1], 'hu':cells[0],
                 'actor_plan':'Ver actor por afirmación en ETAPA-00-agregados-QA.md',
                 'seleccion_documental':'ANEXO QA HISTORICO; incorporacion por criterio pendiente',
                 'etapa_primaria':primary, 'modulos_codigo_candidatos':'; '.join(mods),
                 **candidate_details(names),
                 'modelos_candidatos_por_modulo':model_refs(mods),
                 'pruebas_definidas_candidatas_por_modulo':test_refs(mods),
                 'pruebas_planificadas_historicas':cells[3] if len(cells)>3 else '',
                 'tipo_vinculo':'Grupo historico; no CA atomico ni equivalencia verificada',
                 'estado_revision':'NO EXAMINADO', 'estado_ejecucion':'NO EJECUTADO',
                 'evidencia_nueva':'NINGUNA EN ESTA MATRIZ',
                 'esperado':'Decidir la vigencia de cada afirmación y preparar su contraste funcional',
                 'observado':f'Grupo desglosado bajo QA00-L{lineno} en ETAPA-00-agregados-QA.md',
                 'conflicto_o_limite':'DOC-00-09: etiquetas reutilizadas; no sustituir CA base',
                 'prioridad_revision':'P1 (trazabilidad)',
                 'siguiente_accion':f'Etapa {primary}: contrastar afirmaciones del anexo QA, conciliar alcance y reunir evidencia'})

# Findings from the recorded walkthrough are deliberately narrower than each story.
observations = {
    'HU-AUTH-01/CA-01': ('E00-UI-01', 'Tres cuentas aceptadas en el recorrido. Falta el contraste sistemático de los menús y del estado de sesión.', '20261109-08-http.json'),
    'HU-AUTH-01/CA-04': ('E00-HTTP-01', 'GET/POST de alta con almacenero y vendedor devuelven 403. El snapshot de negocio coincide antes y después.', '20261109-08-http.json'),
    'HU-AUTH-03/CA-01': ('E00-UI-05', 'Los tres usuarios sin turno ni borrador regresaron al ingreso tras confirmar la salida. Queda el caso con turno.', '20261109-07-sesion-cerrada.txt'),
    'HU-PROD-01/CA-01': ('E00-UI-03/04', 'Almacén vio el producto con disponibilidad textual. El vendedor recibió 403. Requiere conciliar el actor y la salida numérica.', '20261109-04-almacen-catalogo.txt'),
    'HU-PROD-02/CA-01': ('E00-UI-02', 'Alta con categoría ficticia activa. La categoría sembrada del CA y el control de vencimiento siguen pendientes.', '20261109-02-producto-creado.txt'),
    'HU-PROD-02/CA-02': ('E00-UI-02', 'Se guardó 6.50. Quedan límites, formato inválido e interpretación del precio.', '00-persistencia.json'),
    'HU-PROD-02/CA-04': ('E00-UI-02', 'Se conservó el 10 visible inicialmente. Vacío, cero y límites siguen pendientes.', '00-persistencia.json'),
    'HU-PROD-02/CA-05': ('E00-UI-02 / E00-HTTP-01', 'Alta ADMIN con cero unidades y no vendible. Intentos directos de almacenero y vendedor denegados sin altas adicionales.', '20261109-08-http.json'),
}
for row in rows:
    if row['id'] in observations:
        case, observation, evidence_file = observations[row['id']]
        evidence_path = OUT.parent / 'evidencias' / evidence_file
        if not evidence_path.is_file():
            raise FileNotFoundError(evidence_path)
        row.update(estado_revision='PARCIAL (muestra 00, revisión individual pendiente)',
                   estado_ejecucion='EJECUTADO EN MUESTRA 00-A',
                   evidencia_nueva=f'{case} | ../evidencias/{evidence_file} | ../ETAPA-00.md §6',
                   observado=observation)

assert len([r for r in rows if r['tipo_registro']=='CA_BASE']) == 219
assert len([r for r in rows if r['tipo_registro']=='IDEA_SIN_CA']) == 8
assert len([r for r in rows if r['tipo_registro']=='GRUPO_QA_HISTORICO']) == 9
assert len({r['id'] for r in rows}) == len(rows) == 236
assert sum(1 for r in rows if r.get('seleccion_documental')=='R1 SELECCIONADO') == 41
columns = list(dict.fromkeys(key for row in rows for key in row))
with (OUT/'ETAPA-00-cobertura.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer = csv.DictWriter(f,fieldnames=columns)
    writer.writeheader()
    writer.writerows(rows)

modules_count = Counter(r['modulo_plan'] for r in rows if r['tipo_registro']=='CA_BASE')
stage_count = Counter(r['etapa_primaria'] for r in rows if r['tipo_registro']=='CA_BASE')
summary = {'fecha_construccion':'2026-11-09','fecha_inventario_origen':plan['fecha_local'],
           'ca_base':219,'ca_r1':41,'ca_posteriores':178,'hu_con_ca':74,'ideas_sin_ca':8,
           'grupos_qa_historicos':9,'filas_totales':236,
           'ca_por_modulo':dict(sorted(modules_count.items())),
           'ca_por_etapa_primaria':dict(sorted(stage_count.items())),
           'ejecuciones_funcionales_por_este_script':0}
(OUT/'ETAPA-00-cobertura-conteos.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
reverse = []
resolved = json.loads((OUT.parent/'evidencias/00-rutas-resueltas.json').read_text(encoding='utf-8'))
for route in resolved:
    hu_candidates = [hu for hu, names in by_hu.items() if route['name'] in names]
    static = routes.get(route['name'],{})
    is_admin = route['route'].startswith('/admin/')
    qa_candidates = [f'QA-HIST-08-L{ln}' for ln, _, names, _ in qa if route['name'] in names]
    reverse.append({
        'ruta':route['route'], 'nombre':route['name'], 'callback':route['callback'],
        'fuente':f"{static['fuente']}:{static['linea']}" if static else 'r1-pmv/config/urls.py:5 (montaje admin; detalle en resolver)',
        'hu_candidatas':'; '.join(hu_candidates), 'grupos_qa_candidatos':'; '.join(qa_candidates),
        'clasificacion':'SUPERFICIE TECNICA DJANGO: alcance pendiente' if is_admin else ('VINCULO CANDIDATO' if hu_candidates else 'EXTRA SIN REQUISITO ATOMICO ASIGNADO'),
        'estado_revision':'INVENTARIADO','estado_ejecucion':'NO EJECUTADO EN ESTA MATRIZ',
        'etapa_siguiente':'15' if is_admin else ('03' if route['name']=='category-toggle' else ('07' if route['name']=='stock-overview' else '; '.join(sorted({stage(h) for h in plan['historias'] if h['id'] in hu_candidates})))),
        'limite':'Ruta existente no acredita HU completa; resolver admin incluye catch-all, no equivale a pantallas independientes',
    })
assert len(reverse)==106 and sum(r['ruta'].startswith('/admin/') for r in reverse)==65
with (OUT/'ETAPA-00-cobertura-inversa.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(reverse[0]))
    writer.writeheader()
    writer.writerows(reverse)
print(json.dumps(summary,ensure_ascii=False))
