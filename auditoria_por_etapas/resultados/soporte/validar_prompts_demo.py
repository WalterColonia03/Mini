"""Validate this documentation cut; no database access or product execution."""
from pathlib import Path
from urllib.parse import unquote
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import importlib.util
import json
import re

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'auditoria_por_etapas/resultados/evidencias/DEMO-INTERNET-20261115'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((OUT/'fuentes-antes.json').read_text(encoding='utf-8'))
protected=json.loads((OUT/'producto-antes.json').read_text(encoding='utf-8'))
errors=[]
def require(ok,msg):
    if not ok:errors.append(msg)

product_deltas=[n for n,h in protected.items() if not (ROOT/n).exists() or sha(ROOT/n)!=h]
require(not product_deltas,'Producto o base cambiados: '+str(product_deltas))
baseline_deltas=[x['path'] for x in before if sha(OUT/'antes'/x['path'])!=x['sha256']]
require(not baseline_deltas,'Snapshots modificados: '+str(baseline_deltas))
prompts=sorted((ROOT/'auditoria_por_etapas').glob('[0-9][0-9]_*.md'))
require([p.name[:2] for p in prompts]==[f'{i:02}' for i in range(18)],'Inventario de18prompts incompleto')
prompt_checks=[]
for p in prompts:
    s=p.read_text(encoding='utf-8')
    required=['PROTOCOLO_COMUN.md','CONTINUIDAD_Y_SEGUNDA_PASADA.md','OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md','CT-ENTREGA-ACADEMICA','OBJETIVO Y CONTEXTO VIGENTES:','REGLAS PARA EVITAR FALSOS CIERRES:','ACTUALIZACIÓN ESPECÍFICA DEMO-INTERNET:','auditoria_por_etapas/resultados/ESTADO_GENERAL.md']
    missing=[t for t in required if t not in s]
    require(not missing,p.name+': faltantes '+str(missing))
    require(s.count('```')==2,p.name+': bloque copiable inválido')
    require(f'ETAPA-{p.name[:2]}.md' in s,p.name+': salida de etapa incorrecta')
    prompt_checks.append(dict(file=p.name,passed=not missing,sha256=sha(p)))

spec=importlib.util.spec_from_file_location('v',ROOT/'auditoria_por_etapas/resultados/fuente_unica_20261112/regenerar_vistas.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
s,hs,tests,criteria=m.parse();errors.extend(m.document_errors(s,hs,tests,criteria))
counts=m.counts(s,hs,tests,criteria)
old=(OUT/'antes/08_Historias_de_Usuario.md').read_text(encoding='utf-8')
_,oldh,oldt,oldc=m.parse(old)
for label,previous,current in [('HU',oldh,hs),('CP',oldt,tests),('CA',oldc,criteria)]:
    require({x['id'] for x in previous}<={x['id'] for x in current},'Pérdida de IDs '+label)
require({x['id'] for x in hs}-{x['id'] for x in oldh}=={'HU-VEN-10'},'NuevaHU inesperada')
require(next(h for h in hs if h['id']=='HU-VEN-07')['selected'],'Yape no seleccionado')
require(next(h for h in hs if h['id']=='HU-VEN-10')['selected'],'Mixto no seleccionado')
expected={};m.write=lambda p,txt:expected.update({p:txt.rstrip()+'\n'})
if not m.document_errors(s,hs,tests,criteria):m.generate()
derived_deltas=[str(p.relative_to(ROOT)) for p,t in expected.items() if p.read_text(encoding='utf-8')!=t]
require(not derived_deltas,'Derivados desfasados: '+str(derived_deltas))
cpids={t['id'] for t in tests}
guide=ROOT/'auditoria_por_etapas/PAGOS_YAPE_Y_MIXTOS.md'
guide_refs=set(re.findall(r'CP-(?:HU|ACA)-[A-Za-z0-9-]+',guide.read_text(encoding='utf-8')))
require(not guide_refs-cpids,'CP sin definición en guía: '+str(guide_refs-cpids))

changed=[]
for x in before:
    p=ROOT/x['path']
    if sha(p)!=x['sha256']:changed.append(dict(path=x['path'],before=x['sha256'],after=sha(p)))
new=['auditoria_por_etapas/OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md','auditoria_por_etapas/PAGOS_YAPE_Y_MIXTOS.md','auditoria_por_etapas/resultados/REVISION-PROMPTS-DEMO-INTERNET.md']
new_links=[];broken=[]
for name in [x['path'] for x in changed]+new:
    p=ROOT/name;body=p.read_text(encoding='utf-8')
    past=OUT/'antes'/name
    oldrefs=set(re.findall(r'\]\(([^)\n]+)\)',past.read_text(encoding='utf-8'))) if past.exists() else set()
    for href in set(re.findall(r'\]\(([^)\n]+)\)',body))-oldrefs:
        if re.match(r'^(https?://|mailto:)',href):continue
        filename,_,anchor=unquote(href).partition('#')
        target=(p.parent/filename).resolve() if filename else p
        if target in [OUT/'VALIDACION.json',OUT/'CAMBIOS.json']:continue
        new_links.append(dict(file=name,href=href))
        if not target.exists():broken.append(dict(file=name,href=href))
        elif anchor and target==ROOT/'08_Historias_de_Usuario.md':require(f'id="{anchor}"' in s,'Ancla08 inexistente: '+href)
require(not broken,'Enlaces nuevos rotos: '+str(broken))

oldstate=(OUT/'antes/auditoria_por_etapas/resultados/ESTADO_GENERAL.md').read_text(encoding='utf-8')
state=(ROOT/'auditoria_por_etapas/resultados/ESTADO_GENERAL.md').read_text(encoding='utf-8')
unchanged_rows=lambda b:[r for r in b.splitlines() if r.startswith('|') and not r.startswith('| [01]')]
rows_preserved=unchanged_rows(oldstate)==unchanged_rows(state)
require(rows_preserved,'Filas de otras etapas alteradas')
report01_preserved=sha(ROOT/'auditoria_por_etapas/resultados/ETAPA-01.md')==json.loads((ROOT/'auditoria_por_etapas/resultados/evidencias/01-K-20261115/cierre.json').read_text(encoding='utf-8'))['archivos_documentales']['auditoria_por_etapas/resultados/ETAPA-01.md']
require(report01_preserved,'Informe01K alterado')

# Fixture arithmetic is only design verification, not a checkout execution.
total=Decimal('30');digital=Decimal('20');cash_applied=total-digital;received=Decimal('20')
fixture={'total':str(total),'yape':str(digital),'efectivo_aplicado':str(cash_applied),'vuelto':str(received-cash_applied),'gaveta_100_despues':str(Decimal('100')+cash_applied)}
require(fixture=={'total':'30','yape':'20','efectivo_aplicado':'10','vuelto':'10','gaveta_100_despues':'110'},'Aritmética mixta incorrecta')
report=dict(fecha_utc=datetime.now(timezone.utc).isoformat(),scope='Revisión documental e inspección de código, no ejecución funcional ni despliegue',passed=not errors,errors=errors,source08_sha256=sha(ROOT/'08_Historias_de_Usuario.md'),counts=counts,prompts=prompt_checks,protected_files=len(protected),product_or_database_changes=product_deltas,snapshot_changes=baseline_deltas,derived_mismatch=derived_deltas,new_local_links_checked=len(new_links),broken_new_links=broken,other_stage_rows_preserved=rows_preserved,report01K_preserved=report01_preserved,fixture_arithmetic_only=fixture,functional_tests_this_cut=0,real_transfers_this_cut=0,public_deployment_tested=False,pending_decisions=['PAY-CANAL-01','PAY-REINTEGRO-01'],cursor='00-DEMO-INTERNET-BASELINE-01 → 02-DEMO-TRAZABILIDAD-01')
(OUT/'VALIDACION.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(OUT/'CAMBIOS.json').write_text(json.dumps({'changed':changed,'new':[{'path':n,'sha256':sha(ROOT/n)} for n in new]},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:report[k] for k in ['passed','errors','source08_sha256','counts','protected_files','new_local_links_checked','cursor']},ensure_ascii=True))
raise SystemExit(bool(errors))
