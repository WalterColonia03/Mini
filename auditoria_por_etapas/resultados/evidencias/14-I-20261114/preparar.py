"""Preserva el corte previo sin abrir bases de datos ni copiar secretos."""
import importlib.util
import json
import shutil
import subprocess
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
spec = importlib.util.spec_from_file_location('base14', HERE.parent/'14-D-20261113/navegador/recorrido.py')
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
if (HERE/'build-antes.json').exists():
    raise SystemExit('El corte anterior ya existe; no sobrescribir.')
base.save(HERE/'build-antes.json', base.build())
for name in ('ETAPA-14.md', 'ESTADO_GENERAL.md'):
    shutil.copy2(HERE.parents[1]/name, HERE/('antes-'+name))
shutil.copy2(ROOT/'08_Historias_de_Usuario.md', HERE/'08-antes.md')
with zipfile.ZipFile(HERE/'producto-antes.zip','w',zipfile.ZIP_DEFLATED) as z:
    for name in base.build()['archivos']:
        z.write(ROOT/'r1-pmv'/name, name)
    for p in (ROOT/'r1-pmv/tests').glob('*.py'):
        z.write(p, p.relative_to(ROOT/'r1-pmv'))
with zipfile.ZipFile(HERE/'planificacion-antes.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.glob('*.md'):
        z.write(p,p.name)
    for name in ('PROTOCOLO_COMUN.md','CONTINUIDAD_Y_SEGUNDA_PASADA.md'):
        z.write(ROOT/'auditoria_por_etapas'/name, 'auditoria_por_etapas/'+name)
(HERE/'git-status-antes.txt').write_text(subprocess.check_output(['git','-C',str(ROOT/'r1-pmv'),'status','--short'],text=True),encoding='utf-8')
base.save(HERE/'corte-antes.json',{'pasada':1,'cursor':'14-I-MERMA-01','08_sha256':base.sha((ROOT/'08_Historias_de_Usuario.md').read_bytes()),'build':base.build()['sha256']})
print(json.dumps(json.loads((HERE/'corte-antes.json').read_text()),indent=2))
