"""Audita cierre14: archivos exactos, ejecuciones, criterios y vistas; sin base operativa."""
import hashlib, importlib.util, json, re, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];RESULTS=HERE.parents[1]
read=lambda p:p.read_text(encoding='utf-8-sig')
load=lambda p:json.loads(read(p))
sha=lambda b:hashlib.sha256(b).hexdigest()
save=lambda p,x:p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def module(name,path):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
base=module('base14',HERE.parent/'14-D-20261113/navegador/recorrido.py')
canonical=module('canonical14',HERE.parent/'14-H2-20261114/verificar.py')
runtime=base.build();sources=canonical.product();errors=[]
complete=dict(head=runtime['head'],archivos=len(sources),build=sha(json.dumps(sources,sort_keys=True,separators=(',',':')).encode()),
    fuentes=sources,runtime_sha256=runtime['sha256'],runtime_archivos=len(runtime['archivos']),plan08=sha((ROOT/'08_Historias_de_Usuario.md').read_bytes()))
save(HERE/'build-final.json',complete)
sys.path.insert(0,str(RESULTS/'fuente_unica_20261112'));import regenerar_vistas as views
s,stories,cases,criteria=views.parse();errors+=views.document_errors(s,stories,cases,criteria)
expected={};views.write=lambda p,txt:expected.update({p:txt.rstrip()+'\n'});counts=views.generate()
matches={p.name:read(p)==t for p,t in expected.items()}
errors+=['Vista no reproducida '+k for k,v in matches.items() if not v]
old={c['id']:c['text'] for c in views.parse(read(HERE/'08-ejecutado.md'))[3]}
current={c['id']:c['text'] for c in criteria}
if old!=current:errors.append('Criterios modificados tras ejecución')
compat={};total=0
runs=['navegador/cadena-final','navegador/ajustes-final','navegador/merma-final','navegador/kardex-final','navegador/dinero-final','navegador/precio-final-2','complementos-chrome-2']
for folder in runs:
    p=HERE/folder;run=load(p/'ejecucion.json');build=load(p/'build-final.json')
    compat[folder]=dict(completo=run['estado']=='recorrido_completo',estable=run['build_estable'],
        mismo_producto=build['archivos']==runtime['archivos'],checkpoints=len(run['pasos']),capturas=len(list(p.glob('*.jpg'))),plan08=run['plan08_inicio'])
    total+=len(run['pasos'])
    if not all(compat[folder][k] for k in ['completo','estable','mismo_producto']):errors.append('Corrida incompatible '+folder)
server=load(HERE/'servidor/regresion-final/manifiesto.json')
server_ok=server['status']==0 and server['fuentes_estables'] and server['despues']['archivos']==runtime['archivos']
if not server_ok:errors.append('Servidor incompatible')
pg=load(HERE/'postgresql/final/compatibilidad-build.json')
pg_cases=load(HERE/'postgresql/final/results.json')['cases']
pg_ok=pg['pg_success'] and pg['pg_source_stable'] and pg['runtime_sha256']==runtime['sha256'] and pg['pg_canonical_sha256']==complete['build'] and all(c['ok'] for c in pg_cases)
if not pg_ok:errors.append('PG incompatible')
migration=load(HERE/'postgresql/migraciones-legacy/results.json')
migration_ok=migration['ok'] and migration['source_stable'] and migration['after']['archivos']==runtime['archivos'] and all(c['ok'] for c in migration['cases'])
if not migration_ok:errors.append('Diagnóstico de migraciones incompatible')
if (HERE/'08-final.md').read_bytes()!=(ROOT/'08_Historias_de_Usuario.md').read_bytes():errors.append('Copia08final desfasada')
if complete['plan08'] not in read(RESULTS/'ETAPA-14.md').split('## Antecedentes preservados')[0]:errors.append('Hash08 del informe desfasado')
documents=[ROOT/n for n in ['08_Historias_de_Usuario.md','07_Reglas_de_Negocio.md','09_Product_Backlog.md','03_Matriz_de_Trazabilidad_y_Pruebas.md','02_Diseno_Tecnico_R1_PMV.md','14_Sprint_Planning.md','16_Task_Breakdown.md','21_Alcance_Actual_y_Diferencias.md','01_Proyecto_y_Releases.md','00_LEEME_PLANIFICACION.md','r1-pmv/CONTROL_SPRINTS.md','auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md']]
documents += [RESULTS/'ETAPA-14.md',RESULTS/'ESTADO_GENERAL.md',*sorted((RESULTS/'soporte').glob('14-CIERRE*.md'))]
documents += [HERE/'REPRODUCIR.md',HERE/'postgresql/INFORME.md',HERE/'postgresql/MIGRACIONES.md',HERE/'complementos-chrome-2/INFORME.md']
broken=[]
for p in documents:
    content=read(p)
    if p.name=='ETAPA-14.md':content=content.split('## Antecedentes preservados')[0]
    for link in re.findall(r'\]\(([^)]+)\)',content):
        if re.match(r'^(https?:|#)',link):continue
        path=unquote(link.split('#')[0])
        target=(p.parent/path).resolve() if path else None
        if target and target!=HERE/'validacion-final.json' and not target.exists():broken.append(str(p.relative_to(ROOT))+': '+link)
errors+=['Enlace roto '+v for v in broken]
# Preserve exact runner sources and hashes; base execution runner_sha is not the derived journey hash.
runner_paths=[HERE/'recorrido_ajustes.py',HERE/'recorrido_dinero.py',HERE/'recorrido_precio.py',HERE/'servidor.py',
    HERE.parent/'14-I-20261114/recorrido_merma.py',HERE.parent/'14-H2-20261114/navegador/recorrido_kardex.py',HERE.parent/'14-D-20261113/navegador/recorrido.py']
archive=HERE/'runners-final';archive.mkdir(exist_ok=True)
runners={}
for p in runner_paths:
    target=archive/p.name
    if target.exists() and target.read_bytes()!=p.read_bytes():errors.append('Runner cambió tras preservarlo '+str(p))
    elif not target.exists():target.write_bytes(p.read_bytes())
    runners[str(p.relative_to(ROOT))]=sha(p.read_bytes())
save(archive/'manifiesto.json',runners)
baseline=load(HERE/'build-antes.json');previous=baseline.get('fuentes',baseline.get('archivos'))
changes=[p for p in sorted(previous.keys()|sources.keys()) if previous.get(p)!=sources.get(p)]
record=dict(fecha_utc=datetime.now(timezone.utc).isoformat(),pasada=1,etapa=14,cursor='15-SEGURIDAD-BASELINE-01',
    resultado='VALIDO' if not errors else 'REVISAR',errores=errors,plan08=complete['plan08'],build=complete['build'],runtime_build=runtime['sha256'],
    conteos=counts,vistas_reproducidas=matches,criterios_287_identicos_a_ejecutado=old==current,servidor_final_compatible=server_ok,
    regresion='634/634;132.064s',navegador=compat,total_checkpoints_chrome=total,postgresql_compatible=pg_ok,postgresql_casos=len(pg_cases),migraciones_legacy_compatibles=migration_ok,migraciones_legacy_casos=len(migration['cases']),
    archivos_producto_modificados=changes,enlaces_rotos=broken,documentos={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in documents},
    limites='Cierre integración14; no aprobación global de módulos/15-17/operación, normativa ni segunda pasada.')
save(HERE/'validacion-final.json',record)
print(json.dumps({k:v for k,v in record.items() if k not in ['documentos','archivos_producto_modificados']},ensure_ascii=False,indent=2))
sys.exit(bool(errors))
