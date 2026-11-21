"""Read-only build witness. Does not read .env, credentials, databases or logs."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / 'r1-pmv'
EVIDENCE = ROOT / 'auditoria_por_etapas/resultados/evidencias/13-B-20261113'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def capture():
    prior = json.loads((EVIDENCE.parent/'13-A-20261113/build-final.json').read_text(encoding='utf-8-sig'))
    files = {}
    for p in sorted(APP.rglob('*')):
        if not p.is_file() or any(x in p.relative_to(APP).parts for x in ('.git','.venv','__pycache__','evidencias','node_modules')):
            continue
        if p.suffix in {'.py','.html','.css','.js','.svg','.ps1','.sh'}:
            files[p.relative_to(ROOT).as_posix()] = sha(p.read_bytes())
    old = prior['product_files_sha256']
    changed = [p for p in old if files.get(p) != old[p]]
    added = [p for p in files if p not in old]
    report = dict(at_utc=datetime.now(timezone.utc).isoformat(), pasada=1, sublote='13-B',
        git_head=subprocess.check_output(['git','-C',str(APP),'rev-parse','HEAD'],text=True).strip(),
        git_status=subprocess.check_output(['git','-C',str(APP),'status','--short'],text=True),
        source08_sha256=sha((ROOT/'08_Historias_de_Usuario.md').read_bytes()),
        product_build_sha256=sha(json.dumps(files,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()),
        hash_algorithm='SHA256 of UTF8 JSON path→SHA256, sort_keys=True, ensure_ascii=False, compact separators',
        product_files_sha256=files, comparison_13A_final=dict(changed=changed, added=added,
        removed=[p for p in old if p not in files]),
        scope='Local files; not deployed. Browser final verification blocked; see13-B-navegador.md.')
    target=EVIDENCE/('manifest-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json')
    with target.open('x',encoding='utf-8') as f:
        json.dump(report,f,ensure_ascii=False,indent=2)
    print(json.dumps(dict(path=str(target),build=report['product_build_sha256'],source08=report['source08_sha256'],files=len(files),changed=changed,added=added),ensure_ascii=False))

if __name__ == '__main__':
    capture()
