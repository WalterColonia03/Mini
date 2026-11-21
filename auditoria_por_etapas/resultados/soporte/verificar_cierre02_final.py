"""Read-only final verification, retaining historical 02-A closure evidence."""
import hashlib
import json
import re
import socket
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

R = Path(__file__).resolve().parents[1]
ROOT = R.parent.parent
E = R / 'evidencias'
def read(p):
    return json.loads(p.read_text(encoding='utf-8'))
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()
def closed(port):
    with socket.socket() as sock:
        sock.settimeout(1)
        return sock.connect_ex(('127.0.0.1',port)) != 0

a = E / '02-A-20261109T235435476251Z'
b = E / '02-B-20261109T235313324286Z'
baseline = read(a/'baseline.json')
ac = read(a/'closure.json')
bc = read(b/'closure.json')
ab,bb = read(a/'browser.json'),read(b/'browser.json')
pg = read(E/'02-C-pg-20261109T235144128048Z.json')
reg = read(E/'02-revalidacion-20261109T235435484826Z-7c6ff184eb0b.json')
criteria = read(R/'anexos/ETAPA-02-criterios.json')
protected={name:sha(ROOT/name)==expected for name,expected in baseline['protected_databases'].items()}
product={name:sha(ROOT/name)==expected for name,expected in baseline['source_sha256'].items()}
product.update({name:sha(ROOT/name)==expected for name,expected in bc['source_sha256_after'].items()})
product.update({name:sha(ROOT/name)==expected for name,expected in reg['source_sha256_after'].items()})
ports={str(port):closed(port) for port in (ac['port'],bc['port'],pg['port'])}
docs=[R/'ETAPA-02.md', R/'ESTADO_GENERAL.md',*(R/'anexos').glob('ETAPA-02-*.md'),ROOT/'09_Product_Backlog.md',ROOT/'03_Matriz_de_Trazabilidad_y_Pruebas.md']
missing=[];links=0
for doc in docs:
    for target in re.findall(r'\]\(([^)]+)\)',doc.read_text(encoding='utf-8')):
        if target.startswith(('http:','https:','#')):
            continue
        target=target.split('#')[0];links+=1
        if not (doc.parent/target).exists():
            # The report links this output itself; it is written by this check.
            if (doc.parent/target).resolve()!=(E/'02-D-cierre-final.json').resolve():
                missing.append({'doc':str(doc.relative_to(ROOT)),'target':target})
counts=Counter(c['status'].split(' — ')[0].split(' / ')[0] for c in criteria['criteria'])
result={
 'verified_utc':datetime.now(timezone.utc).isoformat(),
 'scope':'02-D closure; 02-A original evidence not rewritten',
 'protected_unchanged':protected,
 'final_a_database_unchanged':sha(R/'datos/etapa02a-20261109T235435476251Z/audit.sqlite3')==ac['final_database_sha256'],
 'final_b_database_unchanged':sha(R/'datos/etapa02a-b-20261109T235313324286Z/audit.sqlite3')==bc['database_sha256'],
 'product_sources_match_final_tested_versions':all(product.values()),
 'changed_product_sources':[name for name,ok in product.items() if not ok],
 'ports_closed_now':ports,
 'browser_a':{'count':len(ab['cases']),'failed':ab['failed']},
 'browser_b':{'count':len(bb['cases']),'failed':bb['failed'],'errors':bb['errors']},
 'postgres':{'case_count':len(pg['cases']),'status':pg['status'],'all_blocking_observed':all(c['postgres_blocking_observed'] for c in pg['cases'])},
 'regression':{'method_count':reg['method_count'],'failure_count':reg['failure_count'],'checks':reg['checks']},
 'criteria_count':len(criteria['criteria']),'criteria_unique':len({c['id'] for c in criteria['criteria']})==33,
 'criteria_status_counts':dict(counts),'criteria_source_hash_matches':criteria['source_sha256']==sha(ROOT/'08_Historias_de_Usuario.md'),
 'checked_local_links':links,'missing_local_links':missing,
 'document_sha256':{str(p.relative_to(ROOT)):sha(p) for p in docs},
 'support_sha256':{str(p.relative_to(ROOT)):sha(p) for p in (R/'soporte').glob('*02*') if p.is_file()},
}
ok=all(protected.values()) and all(product.values()) and all(ports.values()) and result['final_a_database_unchanged'] and result['final_b_database_unchanged'] and not missing and not ab['failed'] and not bb['failed'] and not bb['errors'] and reg['method_count']==163 and reg['failure_count']==0 and pg['status']=='COMPLETE' and len(pg['cases'])==6 and result['criteria_source_hash_matches'] and dict(counts)=={'CUMPLE':15,'PREVISTO/FUTURO':15,'PARCIAL':3}
result['verification_passed']=ok
(E/'02-D-cierre-final.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('document_sha256','support_sha256')},indent=2,ensure_ascii=False))
raise SystemExit(0 if ok else 1)
