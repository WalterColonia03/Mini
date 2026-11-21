"""Check the cost-decision documentation; does not run the product."""
from pathlib import Path
from urllib.parse import unquote
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import re

ROOT=Path(__file__).resolve().parents[3]
AUD=ROOT/'auditoria_por_etapas'
OUT=AUD/'resultados/evidencias/PAY-SIN-COMISION-20261115'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((OUT/'fuentes-antes.json').read_text(encoding='utf-8'))
protected=json.loads((AUD/'resultados/evidencias/DEMO-INTERNET-20261115/producto-antes.json').read_text(encoding='utf-8'))
errors=[]
def check(ok,msg):
    if not ok:errors.append(msg)

product_changes=[p for p,h in protected.items() if not (ROOT/p).exists() or sha(ROOT/p)!=h]
check(not product_changes,'Producto/base alterados: '+str(product_changes))
check(all(sha(OUT/'antes'/v['path'])==v['sha256'] for v in before),'Snapshots alterados')
spec=importlib.util.spec_from_file_location('derived',AUD/'resultados/fuente_unica_20261112/regenerar_vistas.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
s,hs,ts,cs=m.parse();errors.extend(m.document_errors(s,hs,ts,cs))
olds,oldh,oldt,oldc=m.parse((OUT/'antes/08_Historias_de_Usuario.md').read_text(encoding='utf-8'))
counts=m.counts(s,hs,ts,cs)
check(counts==m.counts(olds,oldh,oldt,oldc),'Cambios de inventario no previstos')
for name,old,new in [('HU',oldh,hs),('CA',oldc,cs),('CP',oldt,ts)]:
    check({v['id'] for v in old}=={v['id'] for v in new},'IDs alterados: '+name)
oldci={v['id']:v for v in oldc};oldti={v['id']:v for v in oldt}
changed_criteria=[v['id'] for v in cs if v!=oldci[v['id']]]
changed_cases=[v['id'] for v in ts if v!=oldti[v['id']]]
check(changed_criteria==['CT-ENTREGA-ACADEMICA/C-02'],'Criterios cambiados inesperados: '+str(changed_criteria))
check(changed_cases==['CP-ACA-002'],'Casos cambiados inesperados: '+str(changed_cases))
check('cero comisión de cobro' in s and 'Yape Empresa/Ayudantes queda descartado por costo' in s,'Decisión no incorporada en08')
expected={};m.write=lambda p,t:expected.update({p:t.rstrip()+'\n'});m.generate()
check(all(p.read_text(encoding='utf-8')==t for p,t in expected.items()),'Derivados desfasados')
prompts=sorted(AUD.glob('[0-9][0-9]_*.md'))
check(len(prompts)==18,'No hay18prompts')
for p in prompts:
    body=p.read_text(encoding='utf-8')
    check(body.count('```')==2,p.name+': formato de prompt inválido')
    check('Yape Empresa/Ayudantes está descartado por costo' in body and 'DECISION-PAGOS-SIN-COMISION.md' in body,p.name+': decisión ausente')

state=(AUD/'resultados/ESTADO_GENERAL.md').read_text(encoding='utf-8')
oldstate=(OUT/'antes/auditoria_por_etapas/resultados/ESTADO_GENERAL.md').read_text(encoding='utf-8')
rows=lambda body:[r for r in body.splitlines() if r.startswith('|')]
check(rows(state)==rows(oldstate),'Se alteró el resultado de una etapa')
check('**Cursor:** `02-DEMO-TRAZABILIDAD-01`' in state,'Cursor funcional alterado')
report=AUD/'resultados/DECISION-PAGOS-SIN-COMISION.md'
changed=[{'path':v['path'],'before':v['sha256'],'after':sha(ROOT/v['path'])} for v in before if sha(ROOT/v['path'])!=v['sha256']]
new_links=[]
for p in [ROOT/v['path'] for v in changed if v['path'].endswith('.md')]+[report]:
    body=p.read_text(encoding='utf-8');old=OUT/'antes'/p.relative_to(ROOT)
    previous=set(re.findall(r'\]\(([^)\n]+)\)',old.read_text(encoding='utf-8'))) if old.exists() else set()
    for link in set(re.findall(r'\]\(([^)\n]+)\)',body))-previous:
        if re.match(r'^(https?://|mailto:)',link):continue
        target,_,anchor=unquote(link).partition('#')
        dest=(p.parent/target).resolve() if target else p
        if dest==OUT/'validacion.json':continue
        check(dest.exists(),'Enlace roto: '+str(p.relative_to(ROOT))+': '+link)
        if anchor and dest==ROOT/'08_Historias_de_Usuario.md':check(f'id="{anchor}"' in s,'Ancla08 inexistente: '+anchor)
        new_links.append({'file':str(p.relative_to(ROOT)),'link':link})
result={'date_utc':datetime.now(timezone.utc).isoformat(),'passed':not errors,'errors':errors,
        'scope':'Investigación y decisión documental de costo; sin prueba bancaria ni funcional',
        'source08_before':sha(OUT/'antes/08_Historias_de_Usuario.md'),'source08_after':sha(ROOT/'08_Historias_de_Usuario.md'),
        'counts':counts,'changed_criteria':changed_criteria,'changed_cases':changed_cases,'changed_documents':changed,
        'new_report_sha256':sha(report),'protected_files_checked':len(protected),'product_changes':product_changes,
        'prompts_checked':len(prompts),'new_local_links_checked':len(new_links),'stage_rows_unchanged':rows(state)==rows(oldstate),
        'functional_tests':0,'real_transfers':0,'provider_enrollments':0,'public_deployment_tested':False,
        'decision':'Cero comisión de cobro aceptado; Ayudantes descartado; canal de comprobación pendiente',
        'functional_cursor':'02-DEMO-TRAZABILIDAD-01','parallel_cursor':'PAY-CANAL-01-SIN-COMISION'}
(OUT/'validacion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['passed','errors','counts','changed_criteria','changed_cases','protected_files_checked','product_changes','functional_cursor']},ensure_ascii=True))
raise SystemExit(bool(errors))
