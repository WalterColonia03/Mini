"""Validate this session against its actual baseline, without replacing historical guards."""
import hashlib
import difflib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'auditoria_por_etapas/resultados/evidencias/01-E-20261114'
sys.path.insert(0,str(ROOT/'auditoria_por_etapas/resultados/fuente_unica_20261112'))
import regenerar_vistas as views
before = json.loads((OUT/'build-before.json').read_text(encoding='utf-8'))
after = json.loads((OUT/'build-final.json').read_text(encoding='utf-8'))
s,hs,tests,criteria = views.parse()
errors = views.document_errors(s,hs,tests,criteria)
expected = {}
views.write = lambda p,t: expected.update({p:t.rstrip()+'\n'})
views.generate()
mismatch = [str(p.relative_to(ROOT)) for p,t in expected.items() if p.read_text(encoding='utf-8') != t]
delta = [p for p,h in after['source_files'].items() if before['source_files'].get(p)!=h]
allowed = ['identity/forms.py','identity/test_auth_audit01.py']
stable = all(hashlib.sha256((ROOT/'r1-pmv'/p).read_bytes()).hexdigest()==h for p,h in after['source_files'].items())
protected = before['protected_database_sha256']==after['protected_database_sha256']
orm_before = json.loads((OUT/'orm-before-expiry.json').read_text(encoding='utf-8'))
orm_after = json.loads((OUT/'orm-final.json').read_text(encoding='utf-8'))
business_unchanged = orm_before['business']==orm_after['business']
ui = json.loads((OUT/'browser-manifest.json').read_text(encoding='utf-8'))
valid_ui = [x['id'] for x in ui['records'] if x['id'] not in ui['excluded']]
diff = ''
for name in ('forms.py','test_auth_audit01.py'):
    old = (OUT/'antes'/name).read_text(encoding='utf-8').splitlines(True)
    new = (ROOT/'r1-pmv/identity'/name).read_text(encoding='utf-8').splitlines(True)
    diff += ''.join(difflib.unified_diff(old,new,fromfile='antes/'+name,tofile='identity/'+name))
(OUT/'cambios-propios.diff').write_text(diff,encoding='utf-8')
for name in ('ETAPA-01.md','ESTADO_GENERAL.md'):
    text = (ROOT/'auditoria_por_etapas/resultados'/name).read_text(encoding='utf-8')
    if '01-F-ADMIN-PERIMETRO-01' not in text: errors.append('Missing cursor in '+name)
report = {'scope':'01-E against actual14Nov baseline, not historical12Nov no-product-change guard',
    'primary_sha256':after['documents']['08_Historias_de_Usuario.md'],
    'build_sha256':after['build_sha256'],'source_files':len(after['source_files']),
    'structural_errors':errors,'derived_mismatch':mismatch,'own_source_delta':delta,
    'source_stable_after_tests':stable,'protected_database_hashes_equal':protected,
    'business_tables_unchanged_between_UI_snapshots':business_unchanged,
    'business_scope':'empty fictional business tables; no proof for preexisting commercial records',
    'valid_browser_checkpoints':valid_ui,'count_valid_browser_checkpoints':len(valid_ui),
    'test_result':json.loads((OUT/'identity-regression.json').read_text(encoding='utf-8')),
    'historical_validator':'failed its no-product-change guard against12Nov; kept in validacion-documental.txt; not suppressed',
    'passed':not errors and not mismatch and sorted(delta)==allowed and stable and protected and business_unchanged}
(OUT/'verificacion-final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
raise SystemExit(0 if report['passed'] else 1)
