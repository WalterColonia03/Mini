"""Validación documental y de conservación; no conecta a bases ni ejecuta producto.
Escribe únicamente VALIDACION.json y CAMBIOS.json en este directorio.
"""
from pathlib import Path
from urllib.parse import unquote
from decimal import Decimal,ROUND_HALF_UP
import ast,collections,hashlib,json,re
import regenerar_vistas as views
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OLD=ROOT/'auditoria_por_etapas/resultados/conciliacion_20261112'
def read(p):return p.read_text(encoding='utf-8-sig')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
s,hs,tests,criteria=views.parse()
counts=views.counts(s,hs,tests,criteria)
errors=views.document_errors(s,hs,tests,criteria)
def require(ok,msg):
    if not ok:errors.append(msg)
ids=[h['id'] for h in hs];cids=[c['id'] for c in criteria];tids=[t['id'] for t in tests]
oldca=json.loads(read(OLD/'INVENTARIO_CA.json'))
require({c['id'] for c in oldca}<={c['id'] for c in criteria if '/CA-' in c['id']},'Pérdida/cambio de identidad de CA históricos; admitir nuevos no autoriza borrar los anteriores')
original_selected={c['hu'] for c in oldca if c['selected']}
current_selected={h['id'] for h in hs if h['selected']}
selection_delta={'added':sorted(current_selected-original_selected),'removed':sorted(original_selected-current_selected)}
covered=collections.Counter(cid for t in tests for cid in t['covers'])
require(set(cids)==set(covered),'Criterios sin caso o casos con ID inexistente: '+str(set(cids)^set(covered)))
for h in hs:
    require(bool(h['description'] and h['criteria'] and h['dependency'] and h['epic']),f'Ficha incompleta {h["id"]}')
    require(any(h['id']+'/CA-' in ' '.join(t['covers']) for t in tests),f'HU sin caso {h["id"]}')
for t in tests:
    require(bool(t['preconditions'] and t['data'] and t['steps'] and t['expected']),f'Caso incompleto {t["id"]}')
    require(not any(x in t['expected'].lower() for x in ['resultado por definir','pendiente de redactar','tbd']),f'Placeholder {t["id"]}')
rn_section=s.split('## Anexo normativo · Reglas de negocio',1)[1].split('<a id="contratos">',1)[0]
original_rules=set(re.findall(r'^### (RN-\d+) ·',read(HERE/'BASELINE/07_Reglas_de_Negocio.md'),re.M))
require(original_rules<=set(re.findall(r'^### (RN-\d+) ·',rn_section,re.M)),'Pérdida de RN histórica sin tratamiento explícito')
# Reproducir en memoria sin sobrescribir vistas.
expected={}
views.write=lambda p,txt:expected.update({p:txt.rstrip()+'\n'})
if not errors:views.generate()
derived_mismatch=[p.relative_to(ROOT).as_posix() for p,txt in expected.items() if p.read_text(encoding='utf-8')!=txt]
require(not derived_mismatch,'Vistas desfasadas: '+str(derived_mismatch))
baseline_errors=[];changes=[]
for folder in (OLD,HERE,ROOT/'auditoria_por_etapas/resultados/continuidad_20261113'):
    if not (folder/'FUENTES.json').exists():continue
    manifest=json.loads(read(folder/'FUENTES.json'))
    for item in manifest:
        p=folder/'BASELINE'/item['path']
        if not p.exists() or sha(p)!=item['sha256']:baseline_errors.append(str(p.relative_to(ROOT)))
        if folder==HERE and (ROOT/item['path']).exists() and sha(ROOT/item['path'])!=item['sha256']:
            changes.append(dict(path=item['path'],before_sha256=item['sha256'],after_sha256=sha(ROOT/item['path'])))
require(not baseline_errors,'Snapshots alterados: '+str(baseline_errors))
protected=json.loads(read(OLD/'VERIFICACION/integrated-20261112T214843Z-4c3c50/protected-before.json'))
product_changes=[];protected_count=0
for rel,digest in protected.items():
    p=ROOT/rel
    if p.suffix.lower()=='.md':continue
    protected_count+=1
    if not p.exists() or sha(p)!=digest:product_changes.append(rel)
require(not product_changes,'Producto/base cambiados: '+str(product_changes))
# Nuevos IDs no colisionan con identificadores del corte anterior.
prior_text='\n'.join(read(HERE/'BASELINE'/x['path']) for x in json.loads(read(HERE/'FUENTES.json')) if x['path'].endswith('.md'))
new_ids=tids+[cid for cid in cids if cid.startswith('CT-COHERENCIA-UI/C-')]+['DEC-FUENTE-UNICA-20261112']
collisions=[ident for ident in new_ids if re.search(r'(?<![A-Za-z0-9/-])'+re.escape(ident)+r'(?![A-Za-z0-9/-])',prior_text)]
require(not collisions,'Colisión con ID anterior: '+str(collisions))
# Enlaces locales en documentos vigentes; cuerpo histórico se conserva sin reinterpretarlo.
docs=set(ROOT/x['path'] for x in changes if x['path'].endswith('.md'))
docs|={ROOT/'00_LEEME_PLANIFICACION.md',HERE/'REVISION.md',ROOT/'08_Historias_de_Usuario.md',ROOT/'07_Reglas_de_Negocio.md',ROOT/'09_Product_Backlog.md',ROOT/'03_Matriz_de_Trazabilidad_y_Pruebas.md'}
docs.update((ROOT/'auditoria_por_etapas').glob('*.md'))
docs.update((ROOT/'auditoria_por_etapas/resultados/continuidad_20261113').glob('*.md'))
broken=[];anchors_bad=[]
for p in sorted(docs):
    text=read(p)
    if p.name.startswith('ETAPA-') and p.name!='ETAPA-17.md':text=text.split('## Informe y resultados históricos conservados')[0]
    for m in re.finditer(r'\[[^\]\n]*\]\(([^)\n]+)\)',text):
        href=m[1].strip('<>')
        if re.match(r'^(https?://|mailto:)',href):continue
        filename,_,anchor=unquote(href).partition('#')
        target=(p.parent/filename).resolve() if filename else p
        if target.name in ['VALIDACION.json','CAMBIOS.json'] and target.parent==HERE:continue
        if not target.exists():broken.append(dict(file=p.relative_to(ROOT).as_posix(),target=href));continue
        if anchor and target==ROOT/'08_Historias_de_Usuario.md' and f'id="{anchor}"' not in s:anchors_bad.append(dict(file=p.relative_to(ROOT).as_posix(),anchor=anchor))
require(not broken,'Enlaces rotos: '+str(broken))
require(not anchors_bad,'Anclas rotas: '+str(anchors_bad))
# Aritmética de fixtures revisados, no ejecución del sistema.
q=lambda v,p:Decimal(v).quantize(Decimal(p),rounding=ROUND_HALF_UP)
arithmetic={'weighted_physical':str(q((Decimal(18)*3+Decimal(10)*6)/28,'0.0001')),'sale_base':str(q(Decimal(20)/Decimal('1.18'),'0.01')),'sale_tax':str(Decimal(20)-q(Decimal(20)/Decimal('1.18'),'0.01')),'cash_expected':100+20,'cash_change':50-20,'margin_fixture_percent':(10-6)/10*100}
require(arithmetic==dict(weighted_physical='4.0714',sale_base='16.95',sale_tax='3.05',cash_expected=120,cash_change=30,margin_fixture_percent=40.0),'Cálculos de fixture incorrectos')
for p in HERE.glob('*.py'):ast.parse(read(p),filename=p.name)
for name in ['actualizar_documentacion.py','validar_documentacion.py']:
    require('FUENTE-PRINCIPAL-20261112' in read(OLD/name),f'Importador histórico no protegido {name}')
require('aceptada, 10/11/2026' not in s,'Ratificación mal fechada')
require('rentabilidad real' not in s,'Promesa de rentabilidad real sin fundamento')
revision=re.search(r'(?:Revisión|Actualización):\s*(\d{2})/(\d{2})/(\d{4})',s.split('## Fichas de historias',1)[0])
date='-'.join(reversed(revision.groups())) if revision else '2026-11-13'
report=dict(date=date,scope='Documentación y conservación; no ejecución funcional ni aprobación automática de alcance',primary_sha256=sha(ROOT/'08_Historias_de_Usuario.md'),**counts,case_executions_this_cut=0,moscow=dict(collections.Counter(h['priority'] for h in hs)),selection_delta_from_original=selection_delta,derived_views_byte_identical=not errors and not derived_mismatch,baseline_hash_errors=baseline_errors,protected_non_markdown_files=protected_count,product_or_database_changes=product_changes,new_id_collisions=collisions,broken_links=broken,broken_primary_anchors=anchors_bad,fixture_arithmetic=arithmetic,errors=errors,passed=not errors)
(HERE/'VALIDACION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(HERE/'CAMBIOS.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if report['passed'] else 1)
