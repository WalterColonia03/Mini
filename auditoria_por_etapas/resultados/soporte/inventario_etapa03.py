"""Capture scope and immutable pre-edit hashes; does not open business databases."""
import ast
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[1]
ROOT = RESULTS.parent.parent
APP = ROOT / 'r1-pmv'

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    out = RESULTS / 'evidencias' / ('03-inventario-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True)
    sources = ['21_Alcance_Actual_y_Diferencias.md','01_Proyecto_y_Releases.md','07_Reglas_de_Negocio.md','08_Historias_de_Usuario.md','09_Product_Backlog.md','02_Diseno_Tecnico_R1_PMV.md','03_Matriz_de_Trazabilidad_y_Pruebas.md','14_Sprint_Planning.md','16_Task_Breakdown.md','r1-pmv/CONTROL_SPRINTS.md']
    ids = [f'HU-CAT-{n:02}' for n in range(1,5)] + [f'HU-PROD-{n:02}' for n in range(1,6)]
    current = None
    criteria = []
    for line, text in enumerate((ROOT/'08_Historias_de_Usuario.md').read_text(encoding='utf-8').splitlines(),1):
        match = re.match(r'### (HU-[A-Z]+-\d+[a-z]?)',text)
        if match: current = match[1]
        ca = re.match(r'\s+(\d+)\. (.*)',text)
        if current in ids and ca:
            criteria.append({'id':f'{current}/CA-{int(ca[1]):02}','source':f'08_Historias_de_Usuario.md:{line}','text':ca[2], 'scope':'PREVISTO/FUTURO' if current in ['HU-CAT-03','HU-CAT-04','HU-PROD-03'] else 'R1 seleccionado' if current=='HU-PROD-02' else 'Implementado adicionalmente; pendiente de auditoría','execution':'NO EJECUTADO'})
    source_hits = []
    for file in sources:
        for line,text in enumerate((ROOT/file).read_text(encoding='utf-8').splitlines(),1):
            if re.search(r'HU-(?:CAT-0[1-4]|PROD-0[1-5])|QA-FIX-CAT|RN-(?:03|06|27|28|29)|categor[ií]a|enlatado',text,re.I):
                source_hits.append({'source':f'{file}:{line}','text':text})
    surface = []
    for file in [*sorted((APP/'catalog').rglob('*.py')),*sorted((APP/'catalog/templates').rglob('*.html'))]:
        if '__pycache__' in str(file): continue
        for line,text in enumerate(file.read_text(encoding='utf-8').splitlines(),1):
            if (file.suffix=='.html' and text.strip()) or re.search(r'def |class |path\(|label|help_text|raise |messages\.|max_length|validators|models\..*Field|fields =',text):
                surface.append({'source':f'{file.relative_to(ROOT).as_posix()}:{line}','text':text,'status':'NO EXAMINADO'})
    protected = [*APP.glob('*.sqlite3'),*sorted((RESULTS/'datos').rglob('*.sqlite3')),ROOT/'PLANIFICACION_SCRUM_R1PMV.xlsx']
    code = [p for p in APP.rglob('*') if p.is_file() and p.suffix in {'.py','.html','.css','.md'} and not any(x in p.parts for x in ['.venv','.git','__pycache__','staticfiles'])]
    report={'started_utc':datetime.now(timezone.utc).isoformat(),'timezone':'America/Lima','criteria':criteria,'source_hits':source_hits,'surface':surface,'protected_hashes':{str(p.relative_to(ROOT).as_posix()):digest(p) for p in protected},'source_hashes':{str(p.relative_to(ROOT).as_posix()):digest(p) for p in [*(ROOT/f for f in sources),*code]},'git_status':subprocess.check_output(['git','-C',str(APP),'status','--short'],encoding='utf-8'),'git_head':subprocess.check_output(['git','-C',str(APP),'rev-parse','HEAD'],encoding='utf-8').strip()}
    (out/'inventory.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    # Back up only files which this sublot may edit, outside application and database paths.
    for rel in ['catalog/models.py','catalog/forms.py','catalog/services.py','catalog/templates/catalog/category_form.html']:
        p=out/'before'/rel; p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((APP/rel).read_bytes())
    print(json.dumps({'evidence':str(out.relative_to(ROOT)),'criteria':len(criteria),'future':sum(c['scope']=='PREVISTO/FUTURO' for c in criteria),'surface_lines':len(surface),'protected_files':len(protected)}))

if __name__=='__main__': main()
