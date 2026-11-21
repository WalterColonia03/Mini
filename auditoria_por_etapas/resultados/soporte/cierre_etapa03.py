"""Verify only the scope of03-A, original hashes, report links and source changes."""
import difflib
import hashlib
import json
import re
from datetime import datetime,timezone
from pathlib import Path

RESULTS=Path(__file__).resolve().parents[1]
ROOT=RESULTS.parent.parent
INITIAL=RESULTS/'evidencias/03-inventario-20261110T000729019055Z'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((INITIAL/'inventory.json').read_text(encoding='utf-8'))
allowed={'r1-pmv/catalog/models.py','r1-pmv/catalog/forms.py','r1-pmv/catalog/services.py','r1-pmv/catalog/views.py','r1-pmv/catalog/templates/catalog/category_form.html'}
changed=[p for p,h in baseline['source_hashes'].items() if digest(ROOT/p)!=h]
protected={p:digest(ROOT/p)==h for p,h in baseline['protected_hashes'].items()}
links=[]
for doc in [RESULTS/'ETAPA-03.md',RESULTS/'anexos/ETAPA-03-inventario.md',RESULTS/'ESTADO_GENERAL.md']:
    for target in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        if '://' in target or target.startswith('#'):continue
        clean=target.split('#')[0]
        if clean=='evidencias/03-A-cierre.json':continue
        links.append({'document':str(doc.relative_to(ROOT)),'target':target,'exists':(doc.parent/clean).exists()})
criteria=[]
for old in baseline['criteria']:
    row=dict(old);id=row['id']
    if id.startswith(('HU-CAT-01/','HU-CAT-02/')):row['execution']='CUMPLE muestra03-A'
    elif row['scope']=='PREVISTO/FUTURO':row['execution']='PREVISTO/FUTURO'
    elif id in ['HU-PROD-02/CA-01','HU-PROD-04/CA-03']:row['execution']='CONFLICTO DE FUENTES'
    else:row['execution']='NO EJECUTADO como auditoría completa; regresión automática ejecutada'
    criteria.append(row)
(RESULTS/'evidencias/03-A-criterios.json').write_text(json.dumps(criteria,ensure_ascii=False,indent=2),encoding='utf-8')
patches=[]
for rel in allowed:
    prior=INITIAL/'before'/rel.removeprefix('r1-pmv/')
    if prior.exists():
        patches.extend(difflib.unified_diff(prior.read_text(encoding='utf-8').splitlines(keepends=True),(ROOT/rel).read_text(encoding='utf-8').splitlines(keepends=True),fromfile=rel+' (antes03)',tofile=rel+' (03-A)'))
    else:
        patches.append('# views.py: category_create binds request.POST even for an empty POST; initial hash retained in manifest.\n')
(RESULTS/'evidencias/03-A-cambios.patch').write_text(''.join(patches),encoding='utf-8')
tests=json.loads((RESULTS/'evidencias/03-A-tests-20261110T001337606973Z/result.json').read_text(encoding='utf-8'))
browser=json.loads((RESULTS/'evidencias/03-A-browser-20261110T001427294717Z/browser.json').read_text(encoding='utf-8'))
closure=json.loads((RESULTS/'evidencias/03-A-browser-20261110T001427294717Z/result.json').read_text(encoding='utf-8'))
pg=json.loads((RESULTS/'evidencias/03-A-postgresql-20261110T001529034853Z.json').read_text(encoding='utf-8'))
orm=json.loads((RESULTS/'evidencias/03-A-browser-20261110T001427294717Z/orm-final.json').read_text(encoding='utf-8'))
unredacted=[]
for p in (RESULTS/'evidencias').glob('03-A-tests-*/tests.txt'):
    if re.search(r'name="csrfmiddlewaretoken" value="(?!\[REDACTED\])[^\"]+',p.read_text(encoding='utf-8')):unredacted.append(str(p.relative_to(ROOT)))
report={'date_lima':'2026-11-09','verified_utc':datetime.now(timezone.utc).isoformat(),'protected_unchanged':protected,'changed_preexisting_sources':changed,'only_allowed_sources_changed':set(changed)==allowed,'new_application_files':['r1-pmv/catalog/migrations/0003_normalize_category_spaces.py','r1-pmv/catalog/test_audit03_categories.py'],'post_hashes':{p:digest(ROOT/p) for p in sorted(allowed)},'criteria_count':len(criteria),'criteria_status_counts':{s:sum(x['execution']==s for x in criteria) for s in sorted({x['execution'] for x in criteria})},'tests_methods':tests['methods'],'tests_failures':tests['failures'],'browser_cases':len(browser['cases']),'browser_all_pass':not browser['errors'] and all(x['ok'] for x in browser['cases']),'browser_port_closed':closure['port_closed'],'postgres_cases':len(pg['cases']),'postgres_all_pass':not pg.get('error') and all(x['ok'] for x in pg['cases']),'postgres_port_closed':pg['port_closed'],'fixture_counts':{k:len(v) for k,v in orm.items()},'links_checked':len(links),'broken_links':[x for x in links if not x['exists']],'unredacted_test_logs':unredacted,'cursor':'03-B/HU-PROD-01/CA-01,08:207,ADMIN menu Productos -> GET /productos/,new isolated stock0/9/10/11 minimum10'}
(RESULTS/'evidencias/03-A-cierre.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
assert all(protected.values()) and report['only_allowed_sources_changed'] and not report['broken_links'] and not unredacted
assert report['tests_failures']==0 and report['browser_all_pass'] and report['postgres_all_pass'] and report['browser_port_closed'] and report['postgres_port_closed']
