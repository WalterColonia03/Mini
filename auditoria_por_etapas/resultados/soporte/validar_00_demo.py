"""Verify the documentary baseline without executing the application."""
from pathlib import Path
from urllib.parse import unquote
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import re

ROOT = Path(__file__).resolve().parents[3]
AUD = ROOT/'auditoria_por_etapas'
OUT = AUD/'resultados/evidencias/00-DEMO-INTERNET-20261115'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
errors = []
def check(ok, message):
    if not ok: errors.append(message)

baseline = json.loads((OUT/'linea-base.json').read_text(encoding='utf-8'))
protected = json.loads((AUD/'resultados/evidencias/DEMO-INTERNET-20261115/producto-antes.json').read_text(encoding='utf-8'))
changed = [n for n,h in protected.items() if not (ROOT/n).exists() or sha(ROOT/n)!=h]
check(not changed, 'Producto o base alterados: '+str(changed))
check(sha(ROOT/'08_Historias_de_Usuario.md')==baseline['source08_sha256'],'08 cambiado después del inventario')
check(all(sha(ROOT/'r1-pmv'/n)==h for n,h in baseline['sources_01K'].items()),'Fuentes01-K cambiadas')

spec=importlib.util.spec_from_file_location('derivadas',AUD/'resultados/fuente_unica_20261112/regenerar_vistas.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
source,hs,ts,cs=m.parse();errors.extend(m.document_errors(source,hs,ts,cs))
expected={};m.write=lambda p,t:expected.update({p:t.rstrip()+'\n'});m.generate()
check(all(p.read_text(encoding='utf-8')==t for p,t in expected.items()),'Vistas derivadas desfasadas')
prompts=sorted(AUD.glob('[0-9][0-9]_*.md'))
check([p.name[:2] for p in prompts]==[f'{i:02}' for i in range(18)],'Inventario de prompts incompleto')
for p in prompts:
    s=p.read_text(encoding='utf-8')
    check(s.count('```')==2,p.name+': bloque copiable inválido')
    check(all(t in s for t in ['PROTOCOLO_COMUN.md','CONTINUIDAD_Y_SEGUNDA_PASADA.md','OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md','CT-ENTREGA-ACADEMICA','ACTUALIZACIÓN ESPECÍFICA DEMO-INTERNET']),p.name+': falta contexto común')

prior00=(OUT/'antes/auditoria_por_etapas/resultados/ETAPA-00.md').read_text(encoding='utf-8')
current00=(AUD/'resultados/ETAPA-00.md').read_text(encoding='utf-8')
check(current00.endswith(prior00),'Informe00 anterior no conservado íntegro como texto')
state=(AUD/'resultados/ESTADO_GENERAL.md').read_text(encoding='utf-8')
priorstate=(OUT/'antes/auditoria_por_etapas/resultados/ESTADO_GENERAL.md').read_text(encoding='utf-8')
rows=lambda s:[r for r in s.splitlines() if r.startswith('|') and not r.startswith('| [00]')]
check(rows(state)==rows(priorstate),'Filas de etapas01–17 alteradas en00')
check('**Cursor:** `02-DEMO-TRAZABILIDAD-01`' in state,'Cursor global incorrecto')
check('Cursor vigente:** `02-DEMO-TRAZABILIDAD-01`' in current00,'Cursor00 incorrecto')
closure=json.loads((AUD/'resultados/evidencias/01-K-20261115/cierre.json').read_text(encoding='utf-8'))
check(sha(AUD/'resultados/ETAPA-01.md')==closure['archivos_documentales']['auditoria_por_etapas/resultados/ETAPA-01.md'],'Informe01-K alterado')
scope=['auditoria_por_etapas/resultados/ETAPA-00.md','auditoria_por_etapas/resultados/soporte/00-DEMO-INTERNET-mapa.md',
       'auditoria_por_etapas/resultados/ESTADO_GENERAL.md','auditoria_por_etapas/LEEME.md','auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md',
       'auditoria_por_etapas/OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md','16_Task_Breakdown.md','auditoria_por_etapas/resultados/REVISION-PROMPTS-DEMO-INTERNET.md']
checked_links=[]
for name in scope:
    p=ROOT/name; s=p.read_text(encoding='utf-8')
    old=OUT/'antes'/name
    oldrefs=set(re.findall(r'\]\(([^)\n]+)\)',old.read_text(encoding='utf-8'))) if old.exists() else set()
    for href in set(re.findall(r'\]\(([^)\n]+)\)',s))-oldrefs:
        if re.match(r'^(https?://|mailto:)',href):continue
        target,_,anchor=unquote(href).partition('#')
        dest=(p.parent/target).resolve() if target else p
        if dest==OUT/'validacion.json':continue
        check(dest.exists(),f'Enlace inexistente {name}: {href}')
        checked_links.append({'file':name,'href':href})
check('01-K-20261115/triage-regresion.json' in (OUT/'fallos-heredados.json').read_text(encoding='utf-8'),'Triage heredado ausente')
manifest={n:sha(ROOT/n) for n in scope}
result={'date_utc':datetime.now(timezone.utc).isoformat(),'passed':not errors,'errors':errors,'source08_sha256':baseline['source08_sha256'],
        'protected_files_checked':len(protected),'product_changes':changed,'sources_01K_checked':len(baseline['sources_01K']),
        'historical_stage00_preserved':current00.endswith(prior00),'other_stage_rows_preserved':rows(state)==rows(priorstate),
        'prompts_checked':len(prompts),'prompt_hashes':{p.name:sha(p) for p in prompts},'new_local_links_checked':len(checked_links),'artifact_hashes':manifest,
        'functional_tests':0,'browser_tests':0,'real_transfers':0,'public_tested':False,
        'scope':'Línea base estática e integridad documental; sin aprobación funcional',
        'cursor':'02-DEMO-TRAZABILIDAD-01'}
(OUT/'validacion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['passed','errors','protected_files_checked','sources_01K_checked','prompts_checked','new_local_links_checked','cursor']},ensure_ascii=True))
raise SystemExit(bool(errors))
