"""Read-only audit closure checks; outputs no known credentials or tokens."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import socket
from zoneinfo import ZoneInfo

ROOT=Path(__file__).resolve().parents[3]
RESULT=ROOT/'auditoria_por_etapas/resultados'
DATA=RESULT/'datos/etapa01-20261109'
rows=[]
def record(case,passed,detail=None):
    rows.append({'case':case,'passed':bool(passed),'detail':detail})
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

baseline=json.loads((DATA/'prepared.json').read_text())['baseline']
for name,expected in baseline.items():
    record('protected-database:'+name,digest(ROOT/name)==expected,{'sha256':digest(ROOT/name)})
for name in ('forms.py','tests.py'):
    record('preexisting-preserved:'+name,(DATA/'baseline-auth'/name).read_bytes()==(ROOT/'r1-pmv/identity'/name).read_bytes())
manifest_a=json.loads((RESULT/'evidencias/01-auth-tests-20261109-115809-570846.json').read_text())
record('test-log-integrity-01a',digest(RESULT/'evidencias'/manifest_a['log'])==manifest_a['log_sha256'])
manifest=json.loads((RESULT/'evidencias/01-auth-tests-20261109-122521-777224.json').read_text())
for name,expected in manifest['source_sha256'].items():
    record('tested-source:'+name,digest(ROOT/name)==expected)
record('test-log-integrity-01b',digest(RESULT/'evidencias'/manifest['log'])==manifest['log_sha256'] and manifest['exit_code']==0)
http_a=json.loads((RESULT/'evidencias/01-http-20261109120317eaf5da.json').read_text())
record('http-51-expectations-01a',http_a['total']==51 and http_a['passed']==51 and all(row['passed'] for row in http_a['results']))
http=json.loads((RESULT/'evidencias/01-http-202611091226025a110c.json').read_text())
record('http-70-expectations-01b',http['total']==70 and http['passed']==70 and all(row['passed'] for row in http['results']))
for name,expected in http['source_hashes'].items():
    record('http-source:'+name,digest(ROOT/'r1-pmv'/name)==expected)

pictures=sorted((RESULT/'evidencias').glob('01-ui-*.png'))
record('20-browser-captures',len(pictures)==20)
for picture in pictures:
    record('capture-pair:'+picture.name,picture.with_suffix('.txt').exists() and picture.stat().st_size>0)
with socket.socket() as connection:
    connection.settimeout(1)
    record('no-listener-8766',connection.connect_ex(('127.0.0.1',8766))!=0)

docs=[RESULT/'ETAPA-01.md',RESULT/'ESTADO_GENERAL.md',*sorted((RESULT/'anexos').glob('ETAPA-01*.md'))]
for doc in docs:
    missing=[]
    for ref in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        if ref.startswith(('https:','http:','#')):
            continue
        target=(doc.parent/ref.split('#')[0]).resolve()
        if target==RESULT/'evidencias/01-cierre.json':
            continue # This execution creates that file below.
        if not target.exists():
            missing.append(ref)
    record('local-links:'+doc.name,not missing,missing)

known_secrets=[(DATA/'.django-key').read_text().strip()]
known_secrets += [v['password'] for v in json.loads((DATA/'.credentials.json').read_text()).values()]
scan_files=docs+list((RESULT/'evidencias').glob('01-*.json'))+list((RESULT/'evidencias').glob('01-*.txt'))+list((RESULT/'evidencias').glob('01-*.diff'))
leaked=[]
for file in scan_files:
    content=file.read_text(encoding='utf-8')
    if any(secret in content for secret in known_secrets):
        leaked.append(file.name)
record('known-secret-text-scan',not leaked,{'files_checked':len(scan_files),'offending_filenames':leaked,
    'limit':'Known audit01 key and five initial fixture passwords only; no universal leak guarantee'})
record('stage-remains-partial','PARCIAL' in (RESULT/'ETAPA-01.md').read_text(encoding='utf-8'))
record('cursor-present',all('E01-B-01' in doc.read_text(encoding='utf-8') for doc in docs[:2]))
payload={'date_lima':datetime.now(ZoneInfo('America/Lima')).isoformat(),'checks':rows,
    'passed':sum(row['passed'] for row in rows),'total':len(rows),
    'method':'Filesystem SHA256/link checks, known-secret text scan, loopback TCP connect; read-only',
    'shutdown_note':'01-B server started, verified with proof, executed 70 HTTP/ORM checks, and stopped in finally block; 0 listeners on 8766.',
    'final_persistence':'repeticiones/20261109-122609-844456-01-persistencia.json',
    'report_hashes':{str(doc.relative_to(RESULT)):digest(doc) for doc in docs},
    'limits':['No full project suite','No PostgreSQL','Browser unavailable in 01-B']}
path=RESULT/'evidencias/01-cierre.json'
if path.exists():
    path=RESULT/'evidencias/repeticiones'/(datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'-01-cierre.json')
with path.open('x',encoding='utf-8') as handle:
    json.dump(payload,handle,ensure_ascii=False,indent=2)
print(json.dumps({'evidence':str(path.relative_to(ROOT)),'passed':payload['passed'],'total':payload['total'],
    'failed':[row['case'] for row in rows if not row['passed']]},ensure_ascii=False))
raise SystemExit(0 if payload['passed']==payload['total'] else 1)
