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
errors=[]
def require(ok,msg):
    if not ok:errors.append(msg)
ids=[h['id'] for h in hs];cids=[c['id'] for c in criteria];tids=[t['id'] for t in tests]
require(len(ids)==len(set(ids))==74,'HU no son74 únicas')
require(len(cids)==len(set(cids))==287,'Criterios no son287 únicos')
require(len(tids)==len(set(tids))==110,'Casos no son110 únicos')
require(sum(h['selected'] for h in hs)==33,'Selección no es33')
require(set(h['order'] for h in hs)==set(range(1,75)),'Orden del backlog incompleto/duplicado')
require(all(h['sp'] in [1,2,3,5,8,13] for h in hs),'Puntos fuera de Fibonacci acordado')
require(all((h['priority']=='W')== (not h['selected']) for h in hs),'MoSCoW/alcance contradictorios')
require(collections.Counter(h['priority'] for h in hs)==dict(M=26,S=6,C=1,W=41),'Distribución MoSCoW inesperada')
oldca=json.loads(read(OLD/'INVENTARIO_CA.json'))
require({c['id'] for c in criteria if '/CA-' in c['id']}=={c['id'] for c in oldca},'Pérdida/cambio de identidad de CA base')
require({h['id'] for h in hs if h['selected']}=={c['hu'] for c in oldca if c['selected']},'Cambio inadvertido de selección')
covered=collections.Counter(cid for t in tests for cid in t['covers'])
require(set(cids)==set(covered),'Criterios sin caso o casos con ID inexistente: '+str(set(cids)^set(covered)))
for h in hs:
    require(bool(h['description'] and h['criteria'] and h['dependency'] and h['epic']),f'Ficha incompleta {h["id"]}')
    require(any(h['id']+'/CA-' in ' '.join(t['covers']) for t in tests),f'HU sin caso {h["id"]}')
for t in tests:
    require(bool(t['preconditions'] and t['data'] and t['steps'] and t['expected']),f'Caso incompleto {t["id"]}')
    require('NO EJECUTADO' in t['state'],f'Atribución indebida de ejecución {t["id"]}')
    require(not any(x in t['expected'].lower() for x in ['resultado por definir','pendiente de redactar','tbd']),f'Placeholder {t["id"]}')
rn_section=s.split('## Anexo normativo · Reglas de negocio',1)[1].split('<a id="contratos">',1)[0]
require(len(re.findall(r'^### RN-\d+ ·',rn_section,re.M))==30,'Faltan RN')
require(len(re.findall(r'^## EPIC-[A-Z]+ ·',s,re.M))==5,'Faltan épicas')
require(sum(h['sp'] for h in hs)==268 and sum(h['sp'] for h in hs if h['selected'])==146,'TotalesSP inconsistentes')
# Reproducir en memoria sin sobrescribir vistas.
expected={}
views.write=lambda p,txt:expected.update({p:txt.rstrip()+'\n'})
views.generate()
derived_mismatch=[p.relative_to(ROOT).as_posix() for p,txt in expected.items() if p.read_text(encoding='utf-8')!=txt]
require(not derived_mismatch,'Vistas desfasadas: '+str(derived_mismatch))
baseline_errors=[];changes=[]
for folder in (OLD,HERE):
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
new_ids=tids+[f'CT-COHERENCIA-UI/C-{i:02}' for i in range(1,5)]+['DEC-FUENTE-UNICA-20261112']
collisions=[ident for ident in new_ids if ident in prior_text]
require(not collisions,'Colisión con ID anterior: '+str(collisions))
# Enlaces locales en documentos vigentes; cuerpo histórico se conserva sin reinterpretarlo.
docs=set(ROOT/x['path'] for x in changes if x['path'].endswith('.md'))
docs|={ROOT/'00_LEEME_PLANIFICACION.md',HERE/'REVISION.md',ROOT/'08_Historias_de_Usuario.md',ROOT/'07_Reglas_de_Negocio.md',ROOT/'09_Product_Backlog.md',ROOT/'03_Matriz_de_Trazabilidad_y_Pruebas.md'}
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
report=dict(date='2026-11-12',scope='Documentación y conservación; no ejecución funcional',primary_sha256=sha(ROOT/'08_Historias_de_Usuario.md'),epics=5,stories=len(hs),selected=33,future=41,outside_ideas=8,base_criteria=219,contract_criteria=60,category_criteria=4,visible_criteria=4,written_cases=len(tests),case_executions_this_cut=0,moscow=dict(collections.Counter(h['priority'] for h in hs)),fibonacci_catalog=268,fibonacci_selected=146,derived_views_byte_identical=not derived_mismatch,baseline_hash_errors=baseline_errors,protected_non_markdown_files=protected_count,product_or_database_changes=product_changes,new_id_collisions=collisions,broken_links=broken,broken_primary_anchors=anchors_bad,fixture_arithmetic=arithmetic,errors=errors,passed=not errors)
(HERE/'VALIDACION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(HERE/'CAMBIOS.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if report['passed'] else 1)
