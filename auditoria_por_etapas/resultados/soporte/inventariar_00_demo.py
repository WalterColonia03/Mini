"""Static baseline only: does not import Django, connect to DB or start servers."""
from pathlib import Path
from datetime import datetime, timezone
import ast
import hashlib
import importlib.util
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / 'r1-pmv'
OUT = ROOT / 'auditoria_por_etapas/resultados/evidencias/00-DEMO-INTERNET-20261115'
OUT.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
write = lambda name, value: (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

# Freeze preceding documents once. Re-running the inventory never replaces them.
snapshots = ['auditoria_por_etapas/resultados/ETAPA-00.md', 'auditoria_por_etapas/resultados/ESTADO_GENERAL.md',
             'auditoria_por_etapas/LEEME.md', 'auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md',
             'auditoria_por_etapas/OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md', '16_Task_Breakdown.md',
             'auditoria_por_etapas/resultados/REVISION-PROMPTS-DEMO-INTERNET.md']
for name in snapshots:
    dest = OUT/'antes'/name
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT/name).read_bytes())

previous = json.loads((ROOT/'auditoria_por_etapas/resultados/evidencias/01-K-20261115/build-final.json').read_text(encoding='utf-8'))
protected = json.loads((ROOT/'auditoria_por_etapas/resultados/evidencias/DEMO-INTERNET-20261115/producto-antes.json').read_text(encoding='utf-8'))
errors = []
changed = [p for p,h in protected.items() if not (ROOT/p).exists() or sha(ROOT/p)!=h]
if changed: errors.append({'product_changed': changed})
old_sources = previous['fuentes']
source_changes = [p for p,h in old_sources.items() if not (APP/p).exists() or sha(APP/p)!=h]
if source_changes: errors.append({'sources_changed_since_01K': source_changes})

spec = importlib.util.spec_from_file_location('views08', ROOT/'auditoria_por_etapas/resultados/fuente_unica_20261112/regenerar_vistas.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
source, stories, cases, criteria = m.parse()
errors.extend(m.document_errors(source, stories, cases, criteria))
counts = m.counts(source, stories, cases, criteria)
expected = {}; m.write = lambda p,t: expected.update({p:t.rstrip()+'\n'})
m.generate()
if any(p.read_text(encoding='utf-8')!=t for p,t in expected.items()): errors.append('Derived documents differ')

routes = []; classes = []; functions = []; tests = []; fields = []; messages = []; templates = []
apps = ['identity','catalog','inventory','cash','sales','app_platform','config']
prefixes = {'identity':'/','catalog':'/productos/','inventory':'/inventario/','cash':'/caja/','sales':'/ventas/'}
candidate_stages = {'identity':['01','02','13','15'],'catalog':['03','07'],'inventory':['04','05','06','07','08'],
                    'cash':['09','12'],'sales':['10','11','12'],'app_platform':['15'],'config':['15']}
for rel in sorted(old_sources):
    p = APP/rel
    module = rel.split('/')[0]
    if module not in apps and not rel.startswith('templates/'): continue
    if p.suffix == '.html':
        body = p.read_text(encoding='utf-8')
        templates.append({'file':rel,'sha256':sha(p),'lines':len(body.splitlines()),'stage_candidates':candidate_stages.get(module,['transversal'])})
    if p.suffix != '.py': continue
    try: tree = ast.parse(p.read_text(encoding='utf-8-sig'),filename=rel)
    except SyntaxError as e:
        errors.append({'ast':rel,'line':e.lineno}); continue
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            item={'file':rel,'line':node.lineno,'name':node.name,'decorators':[ast.unparse(d) for d in node.decorator_list]}
            if node.name.startswith('test_'): tests.append(item)
            elif p.name in {'views.py','services.py','authorization.py','middleware.py'}: functions.append(item)
        if isinstance(node, ast.ClassDef) and p.name in {'models.py','forms.py'}:
            item={'file':rel,'line':node.lineno,'name':node.name,'bases':[ast.unparse(b) for b in node.bases]}
            classes.append(item)
            for child in node.body:
                if isinstance(child,ast.Assign) and isinstance(child.value,ast.Call):
                    fields.append({'file':rel,'line':child.lineno,'class':node.name,'name':','.join(ast.unparse(t) for t in child.targets),'declaration':ast.unparse(child.value)})
        if isinstance(node,ast.Call):
            fn=ast.unparse(node.func)
            if p.name=='urls.py' and fn in {'path','re_path'}:
                raw=node.args[0].value if node.args and isinstance(node.args[0],ast.Constant) else ast.unparse(node.args[0])
                name=next((k.value.value for k in node.keywords if k.arg=='name' and isinstance(k.value,ast.Constant)),None)
                routes.append({'file':rel,'line':node.lineno,'pattern':raw,'full_route':prefixes.get(module,'')+str(raw),
                               'view':ast.unparse(node.args[1]),'name':name,'kind':'include' if isinstance(node.args[1],ast.Call) else 'view',
                               'stage_candidates':candidate_stages.get(module,['transversal'])})
            if fn in {'ValidationError','messages.error','messages.success','messages.warning','messages.info'} and node.args:
                messages.append({'file':rel,'line':node.lineno,'call':fn,'expression':ast.unparse(node.args[-1]),'status':'INVENTARIADO; verificar literal y CA/CP en etapa propia'})

index = {h['id']:h for h in stories}
requirements=[]
for c in criteria:
    h=index.get(c['id'].split('/')[0])
    linked=[t['id'] for t in cases if c['id'] in t['covers']]
    requirements.append({**c,'selected':h['selected'] if h else None,'stage':h['stage'] if h else 'transversal',
                         'cases':linked,'result_this_cut':'NO EJECUTADO; inventario estático'})
write('requisitos.json',{'stories':stories,'criteria':requirements,'cases':cases,'warning':'Los estados históricos de CP no son reejecución en esta línea base.'})
write('superficies.json',{'method':'AST estático; sin resolver Django, formularios heredados ni navegador',
                        'routes':routes,'classes':classes,'fields':fields,'functions':functions,'tests':tests,'messages':messages,'templates':templates,
                        'limits':['No demuestra permisos efectivos','No enumera estados dinámicos ni campos heredados','Candidatos de etapa no equivalen a trazabilidad exacta HU/CA/CP']})
triage=json.loads((ROOT/'auditoria_por_etapas/resultados/evidencias/01-K-20261115/triage-regresion.json').read_text(encoding='utf-8'))
write('fallos-heredados.json',{'source':'01-K-20261115/triage-regresion.json','source_sha256':sha(ROOT/'auditoria_por_etapas/resultados/evidencias/01-K-20261115/triage-regresion.json'),
                             'test_ids':triage['reproduccion']['tests'],'result':'3 fallos HEREDADOS; no reejecutados ni resueltos en00'})
build={'captured_utc':datetime.now(timezone.utc).isoformat(),'git_head':subprocess.check_output(['git','-C',str(APP),'rev-parse','HEAD'],text=True).strip(),
       'git_status':subprocess.check_output(['git','-C',str(APP),'status','--short'],text=True).splitlines(),
       'source08_sha256':sha(ROOT/'08_Historias_de_Usuario.md'),'build_01K_sha256':previous['build_sha256'],
       'build_method':previous['build_algoritmo'],'sources_01K':old_sources,'source_changes':source_changes,
       'protected_files_checked':len(protected),'protected_changes':changed,'main_db_sha256':sha(APP/'r1_pmv.sqlite3'),
       'counts':counts,'inventory_counts':{'named_routes':sum(r['kind']=='view' for r in routes),'route_includes':sum(r['kind']=='include' for r in routes),
                                        'templates':len(templates),'classes_models_forms':len(classes),'direct_field_assignments':len(fields),
                                        'service_view_functions':len(functions),'test_methods_defined':len(tests),'message_calls':len(messages)},
       'pass':'actualización preparatoria de línea base; no segunda pasada funcional', 'functional_tests':0,'browser_tests':0,'real_transfers':0,'public_tested':False,
       'errors':errors,'inventory_passed':not errors,'next_cursor':'02-DEMO-TRAZABILIDAD-01'}
write('linea-base.json',build)
print(json.dumps({k:build[k] for k in ['inventory_passed','errors','source08_sha256','source_changes','protected_files_checked','protected_changes','inventory_counts','next_cursor']},ensure_ascii=True))
raise SystemExit(bool(errors))
