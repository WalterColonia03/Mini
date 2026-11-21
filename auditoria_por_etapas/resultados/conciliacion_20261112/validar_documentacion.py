"""Valida la conciliación documental y conservación. No conecta a bases de datos."""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
if "FUENTE-PRINCIPAL-20261112" in (ROOT/"08_Historias_de_Usuario.md").read_text(encoding="utf-8"):
    raise SystemExit("Corte historico protegido. Editar08 y usar fuente_unica_20261112/regenerar_vistas.py y validar_fuente.py.")

BASE=HERE/'BASELINE'
def read(p):return p.read_text(encoding='utf-8-sig')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads(read(HERE/'FUENTES.json'))
baseline_bad=[x['path'] for x in manifest if sha(BASE/x['path'])!=x['sha256']]
changes=[{'path':x['path'],'before_sha256':x['sha256'],'after_sha256':sha(ROOT/x['path'])} for x in manifest if (ROOT/x['path']).exists() and sha(ROOT/x['path'])!=x['sha256']]
new_docs=list(HERE.glob('*.md'))+[ROOT/x['path'] for x in changes if x['path'].endswith('.md')]+[ROOT/'auditoria_por_etapas/resultados/ETAPA-17.md']
broken=[]
future={'VALIDACION_DOCUMENTAL.json','CAMBIOS.json'}
for p in sorted(set(new_docs)):
    content=read(p)
    if re.search(r'ETAPA-\d\d\.md$',p.name) and p.name!='ETAPA-17.md':content=content.split('## Informe y resultados históricos conservados')[0]
    for m in re.finditer(r'\[[^\]\n]*\]\(([^)\n]+)\)',content):
        href=m[1].strip('<>')
        if re.match(r'^(https?://|mailto:|#)',href):continue
        rel=unquote(href.split('#')[0])
        target=(p.parent/rel).resolve()
        if not target.exists() and target.name not in future:broken.append({'file':p.relative_to(ROOT).as_posix(),'target':href,'line':content[:m.start()].count('\n')+1})
hu=re.findall(r'^### (HU-[A-Z]+-\d+[a-z]?) ·',read(ROOT/'08_Historias_de_Usuario.md'),re.M)
ca=json.loads(read(HERE/'INVENTARIO_CA.json'))
backlog=re.findall(r'^\| \d+ \| (HU-[A-Z]+-\d+[a-z]?) \|',read(ROOT/'09_Product_Backlog.md'),re.M)
supp=re.findall(r'^\| ([^|\n]+/C-\d+) \|',read(ROOT/'03_Matriz_de_Trazabilidad_y_Pruebas.md'),re.M)
selected={x['hu'] for x in ca if x['selected']}
state=read(ROOT/'auditoria_por_etapas/resultados/ESTADO_GENERAL.md')
missing_stages=[f'{i:02}' for i in range(13) if f'[{i:02}](ETAPA-{i:02}.md)' not in state]
protected=json.loads(read(HERE/'VERIFICACION/integrated-20261112T214843Z-4c3c50/protected-before.json'))
code_or_db_changes=[]
for rel,digest in protected.items():
    p=ROOT/rel
    if p.suffix.lower()=='.md':continue
    if not p.exists() or sha(p)!=digest:code_or_db_changes.append(rel)
raw_ids=json.loads(read(HERE/'INDICE_IDS.json'))
matrix_ids=re.findall(r'^\| (HU-[A-Z]+-\d+[a-z]?/CA-\d+) \|',read(ROOT/'03_Matriz_de_Trazabilidad_y_Pruebas.md'),re.M)
baseline_text='\n'.join(read(BASE/x['path']) for x in manifest if x['path'].lower().endswith('.md'))
supplemental_collisions=[ident for ident in supp if ident in baseline_text]
line_errors=[]
hu_source=read(ROOT/'08_Historias_de_Usuario.md').splitlines()
for c in ca:
    if c['criterion'] not in hu_source[c['line']-1]:line_errors.append(c['id'])
result={'date':'2026-11-12','baseline_files':len(manifest),'baseline_hash_errors':baseline_bad,'changed_document_count':len(changes),'validated_markdown_files':len(set(new_docs)),'broken_new_links':broken,'hu_count':len(hu),'unique_hu_count':len(set(hu)),'backlog_count':len(backlog),'hu_backlog_equal':set(hu)==set(backlog),'base_ca_count':len(ca),'unique_base_ca_count':len({x['id'] for x in ca}),'matrix_ca_equal':set(matrix_ids)=={x['id'] for x in ca},'selected_hu_count':len(selected),'future_hu_count':len(set(hu)-selected),'outside_ideas':8,'new_supplemental_count':len(supp),'unique_new_supplemental_count':len(set(supp)),'historical_category_supplemental_count':4,'historical_identifiers_indexed':len(raw_ids),'missing_original_stages':missing_stages,'code_or_database_changes':code_or_db_changes}
result['new_id_collisions_with_baseline']=supplemental_collisions
result['criterion_source_line_errors']=line_errors
result['passed']=not any([baseline_bad,broken,code_or_db_changes,missing_stages,supplemental_collisions,line_errors]) and len(hu)==len(set(hu))==len(backlog)==74 and len(ca)==len(matrix_ids)==219 and len(selected)==33 and len(supp)==len(set(supp))==60 and result['hu_backlog_equal'] and result['matrix_ca_equal']
(HERE/'CAMBIOS.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2),encoding='utf-8')
(HERE/'VALIDACION_DOCUMENTAL.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True,indent=2))
raise SystemExit(0 if result['passed'] else 1)
