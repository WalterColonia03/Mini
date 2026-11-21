from pathlib import Path
import hashlib,json,tempfile,shutil
here=Path(__file__).resolve().parent
root=here.parents[3]/'r1-pmv'
old=here.parent/'02-INTEGRAL-20261120/paquete-entrega.json'
temp=Path(tempfile.gettempdir())
original=temp/'mm02-stage-1500968717/package'
dest=Path(tempfile.mkdtemp(prefix='mm03-candidato-'))
manifest={}
for f in json.loads(old.read_text()):
    source=root/f if (root/f).exists() else original/f
    target=dest/f
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(source,target)
    manifest[f]=hashlib.sha256(target.read_bytes()).hexdigest()
(here/'paquete.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
(dest/'.vercel').mkdir()
shutil.copyfile(original/'.vercel/project.json',dest/'.vercel/project.json')
print(dest)
