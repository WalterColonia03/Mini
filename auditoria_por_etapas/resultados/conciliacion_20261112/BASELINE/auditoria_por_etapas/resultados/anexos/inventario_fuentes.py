"""Inventario de solo lectura: archivos, Git y metadatos OOXML; nunca importa Django."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import Counter
import hashlib
import json
import subprocess
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
LIMA = timezone(timedelta(hours=-5))
SKIP = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def safe_file(path):
    return not any(p in SKIP for p in path.parts) and path.name not in {'.env', '.env.local', '.env.production'}

def git(*args):
    return subprocess.run(['git', '-c', 'core.quotepath=false', '-C', str(ROOT / 'r1-pmv'), *args], capture_output=True, text=True, encoding='utf-8', check=True).stdout.strip()

inventory = {'generated_lima': datetime.now(LIMA).isoformat(), 'root': str(ROOT), 'scope': 'Solo metadatos, rutas y hashes. No ejecuta aplicacion ni pruebas. Excluye secretos y dependencias.'}
directories = {}
for directory in sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name != 'auditoria_por_etapas'):
    files = sorted(p for p in directory.rglob('*') if p.is_file() and safe_file(p.relative_to(ROOT)))
    directories[directory.name] = {'count': len(files), 'extensions': dict(Counter(p.suffix.lower() or '[sin extension]' for p in files)), 'paths': [p.relative_to(ROOT).as_posix() for p in files]}
inventory['directories'] = directories
inventory['root_files'] = [{ 'path':p.name,'bytes':p.stat().st_size,'modified_lima':datetime.fromtimestamp(p.stat().st_mtime,LIMA).isoformat(),'sha256':sha(p)} for p in sorted(ROOT.iterdir()) if p.is_file() and safe_file(p)]
inventory['git'] = {'head': git('log','-1','--format=%H %cI %s'), 'branch':git('branch','--show-current'), 'status':git('status','--short','--untracked-files=all').splitlines()}
changed = git('diff','--name-only').splitlines()
inventory['git']['tracked_changed_count'] = len(changed)
inventory['git']['changed_file_hashes'] = {p:sha(ROOT/'r1-pmv'/p) for p in changed if safe_file(Path(p)) and (ROOT/'r1-pmv'/p).is_file()}
inventory['git']['untracked_file_count'] = len(git('ls-files','--others','--exclude-standard').splitlines())
book = ROOT/'PLANIFICACION_SCRUM_R1PMV.xlsx'
with zipfile.ZipFile(book) as z:
    core = ET.fromstring(z.read('docProps/core.xml'))
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    inventory['xlsx'] = {'sha256':sha(book), 'metadata': { e.tag.rsplit('}',1)[-1]:e.text for e in core if e.tag.rsplit('}',1)[-1] in {'created','modified','revision','title','description'}},'sheets':[{k:v for k,v in e.attrib.items() if k in {'name','sheetId','state'}} for e in wb.findall('{*}sheets/{*}sheet')], 'worksheet_dimensions': {i.filename: ET.fromstring(z.read(i.filename)).find('{*}dimension').attrib.get('ref') for i in z.infolist() if i.filename.startswith('xl/worksheets/sheet') and i.filename.endswith('.xml') and ET.fromstring(z.read(i.filename)).find('{*}dimension') is not None}, 'cell_values_examined':False}
(OUT/'ETAPA-00-fuentes-inventario.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'directories':{k:{'count':v['count'],'extensions':v['extensions']} for k,v in directories.items()},'git':{k:v for k,v in inventory['git'].items() if k not in {'status','changed_file_hashes'}},'xlsx':inventory['xlsx']},ensure_ascii=False,indent=2))
