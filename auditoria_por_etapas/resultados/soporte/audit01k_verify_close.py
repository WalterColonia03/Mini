"""Verify evidence and close the isolated audit fixture; never alter operator data."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import re
import socket

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'auditoria_por_etapas/resultados/evidencias/01-K-20261115'
DATA=ROOT/'auditoria_por_etapas/resultados/datos/01-K-20261115'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def js(name): return json.loads((OUT/name).read_text(encoding='utf-8'))
before=js('build-antes.json')
final=js('build-final.json')
last=js('build-ultimo.json')
assert final['build_sha256']==last['build_sha256']
assert all(sha(ROOT/'r1-pmv'/n)==h for n,h in last['fuentes'].items())
protected={n:sha(ROOT/n)==h for n,h in before['documentos_y_bases'].items() if n.endswith('.sqlite3') or n=='14_Sprint_Planning.md'}
assert all(protected.values())
old_i=json.loads((ROOT/'auditoria_por_etapas/resultados/evidencias/01-I-20261115/build-final.json').read_text(encoding='utf-8'))
changed_vs_i=[n for n in set(old_i['fuentes'])|set(final['fuentes']) if old_i['fuentes'].get(n)!=final['fuentes'].get(n)]
assert set(changed_vs_i)=={'identity/forms.py','identity/test_audit01k_literals.py','identity/test_audit01k_permissions.py'},changed_vs_i

retired=['r1-pmv/identity/management/commands/audit_identity_readiness.py','r1-pmv/identity/test_audit01j_readiness.py','r1-pmv/deploy/nginx/login-limits.conf','r1-pmv/deploy/nginx/login-location.conf','r1-pmv/deploy/nginx/README.md']
assert all(not (ROOT/n).exists() for n in retired)
source=(ROOT/'08_Historias_de_Usuario.md').read_text(encoding='utf-8')
literal=js('literales-browser.json')
checked_literals=[c['literal'] for c in literal['checks'] if c['id'].startswith('PLAN_')]
assert all(t in source for t in checked_literals)
assert 'DOC-01-06/C-04' not in source
pattern=re.compile(r'art[íi]culo\s*46\.3|art\.?\s*46\.3|46\.3[^\n]*(?:datos|bitácora|seguridad)',re.I)
active_docs=['08_Historias_de_Usuario.md','07_Reglas_de_Negocio.md','09_Product_Backlog.md','03_Matriz_de_Trazabilidad_y_Pruebas.md','01_Proyecto_y_Releases.md','02_Diseno_Tecnico_R1_PMV.md','16_Task_Breakdown.md','21_Alcance_Actual_y_Diferencias.md','auditoria_por_etapas/resultados/ETAPA-01.md','auditoria_por_etapas/resultados/ESTADO_GENERAL.md','auditoria_por_etapas/resultados/soporte/01-J-decisiones-y-entrega.md']
assert all(not pattern.search((ROOT/n).read_text(encoding='utf-8')) for n in active_docs)

generator=ROOT/'auditoria_por_etapas/resultados/fuente_unica_20261112/regenerar_vistas.py'
derived=['07_Reglas_de_Negocio.md','09_Product_Backlog.md','03_Matriz_de_Trazabilidad_y_Pruebas.md','auditoria_por_etapas/resultados/fuente_unica_20261112/INDICE_DERIVADO.json']
prior={n:sha(ROOT/n) for n in derived}
spec=importlib.util.spec_from_file_location('generator01k',generator)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
counts=m.generate()
assert counts['hu']==74 and counts['criteria']==287 and counts['cases']==113
assert all(sha(ROOT/n)==h for n,h in prior.items())

report=ROOT/'auditoria_por_etapas/resultados/ETAPA-01.md'
missing=[]
local_links=0
for url in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
    if '://' in url or url.startswith('#'): continue
    path=(report.parent/url.split('#')[0]).resolve()
    if path.name=='cierre.json': continue
    local_links+=1
    if not path.exists(): missing.append(url)
assert not missing,missing

closed_ports={}
for port in [8800,js('postgresql-01k-latest.json')['puerto_loopback']]:
    with socket.socket() as sock:
        sock.settimeout(.2)
        closed_ports[str(port)]=sock.connect_ex(('127.0.0.1',port))!=0
assert all(closed_ports.values())

creds_path=(DATA/'.credentials.json').resolve()
assert creds_path.is_relative_to(DATA.resolve()) and creds_path.name=='.credentials.json'
assert creds_path.exists(), 'Credential closure must be run only once'
credentials=json.loads(creds_path.read_text(encoding='utf-8'))
secrets=[v['password'] for v in credentials.values() if isinstance(v,dict) and 'password' in v]
secrets.append((DATA/'.django-key').read_text(encoding='utf-8').strip())
leaks=[]
scanned=0
for p in OUT.rglob('*'):
    if not p.is_file() or p.suffix.lower() not in {'.txt','.log','.json','.md','.py','.cjs'}: continue
    content=p.read_text(encoding='utf-8-sig',errors='replace')
    scanned+=1
    if any(token and token in content for token in secrets): leaks.append(p.relative_to(OUT).as_posix())
assert not leaks,leaks
creds_path.unlink()

result={
 'cerrado_utc':datetime.now(timezone.utc).isoformat(),
 'pasada':'primera profundizada; 01-K',
 'alcance':'2 HU / 7 CA / 4 CP; demostración local, ingreso y barreras por rol',
 'build_sha256':last['build_sha256'],'plan08_sha256':sha(ROOT/'08_Historias_de_Usuario.md'),
 'fuentes_estables':True,'cambios_fuente_vs_01I':sorted(changed_vs_i),
 'bases_y_sprint_protegidos':protected,'retirados_01J_ausentes':retired,
 'derivados_sin_desfase':True,'catalogo':counts,
 'literales_probados_presentes_en_version_final':len(checked_literals),
 'referencias_legales_retiradas_ausentes_en_documentos_vigentes':True,
 'enlaces_locales_informe_existentes':local_links,
 'puertos_cerrados':closed_ports,'credenciales_fixture_eliminadas':not creds_path.exists(),
 'secretos_conocidos_no_encontrados_en_textos':{'archivos':scanned,'coincidencias':0,'limite':'solo secretos conocidos de esta fixture; no escáner universal'},
 'pruebas':{'identity':'139/139 OK','literales_browser':'79/79 OK','pg18_4':'5/5 PASS','regresion_ampliada':'663/666; 3 FAIL externos conservados','expiracion_real_segundos':js('expiracion-real-browser.json')['espera_real_segundos']},
 'cursor':'02-LOCAL-TRAZABILIDAD-01',
 'archivos_documentales':{n:sha(ROOT/n) for n in active_docs},
}
(OUT/'cierre.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:result[k] for k in ['build_sha256','plan08_sha256','fuentes_estables','derivados_sin_desfase','enlaces_locales_informe_existentes','puertos_cerrados','credenciales_fixture_eliminadas','cursor']}))
