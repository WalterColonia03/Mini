"""Validación de evidencia H1: coherencia no equivale a aprobar toda la etapa."""
import ast
import hashlib
import json
import re
import runpy
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
sys.path.insert(0,str(OUT.parents[1]/'fuente_unica_20261112'))
import regenerar_vistas as views

def read(p): return p.read_text(encoding='utf-8-sig')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def obj(p): return json.loads(read(p))

def main():
    errors=[]
    source,stories,cases,criteria=views.parse()
    errors.extend(views.document_errors(source,stories,cases,criteria))
    expected={}
    views.write=lambda p,s:expected.update({p:s.rstrip()+'\n'})
    views.generate()
    derived={p.name:read(p)==s for p,s in expected.items()}
    if not all(derived.values()): errors.append('Vistas desfasadas')
    final=obj(OUT/'build-final.json');before=obj(OUT/'build-antes.json')
    files=runpy.run_path(str(OUT/'verificar.py'))['product']()
    if files!=final['fuentes']: errors.append('Producto final cambiado')
    for p in files:
        if p.endswith('.py'): ast.parse(read(ROOT/'r1-pmv'/p),filename=p)
    for p,h in final['documentos'].items():
        if sha(ROOT/p)!=h: errors.append('Documento cambiado: '+p)
    originals=[]
    for name,key in [('producto-antes.zip','fuentes'),('planificacion-antes.zip','documentos')]:
        with zipfile.ZipFile(OUT/name) as z:
            for p,h in before[key].items():
                if hashlib.sha256(z.read(p)).hexdigest()!=h: originals.append(name+'/'+p)
    if originals: errors.append('Snapshot previo alterado')
    with zipfile.ZipFile(OUT/'planificacion-antes.zip') as z:
        old_source=z.read('08_Historias_de_Usuario.md').decode('utf-8-sig')
    text_by_id={c['id']:c['text'] for c in criteria}
    inventory=obj(OUT/'criterios-final.json')
    for row in inventory['criterios']:
        if row['texto']!=text_by_id.get(row['criterio']) or row['texto'] not in old_source:
            errors.append('Criterio modificado: '+row['criterio'])
    if len(inventory['criterios'])!=12: errors.append('Inventario incompleto')
    if {c['id'] for c in criteria}!={cid for c in cases for cid in c['covers']}:
        errors.append('Correspondencia casos/criterios incompleta')
    for case in cases:
        if not all(case[k] for k in ('preconditions','data','steps','expected')):
            errors.append('Caso incompleto: '+case['id'])
    reports={}
    for name in ('antes','despues','final','cadena-final','recepciones-final'):
        folder=OUT/'navegador'/name
        for p,h in obj(folder/'indice.json').items():
            if sha(folder/p)!=h: errors.append('Evidencia alterada: '+name+'/'+p)
        run=obj(folder/'ejecucion.json')
        executed=obj(folder/'build-final.json')['archivos']
        diff=[p for p,h in executed.items() if files.get(p)!=h]
        reports[name]=dict(checkpoints=len(run['pasos']),capturas=len(list(folder.glob('*.jpg'))),
            build_estable=run['build_estable'],estado=run['estado'],fuentes_diferentes=diff,
            source08=run['plan08_inicio'])
        if name in ('final','cadena-final','recepciones-final'):
            target={'final':16,'cadena-final':44,'recepciones-final':23}[name]
            if (not run['build_estable'] or run['estado']!='recorrido_completo' or len(run['pasos'])!=target
                    or diff!=['inventory/test_audit14h_initial_history.py']):
                errors.append('Navegador final incompatible: '+name)
    if any(obj(OUT/'navegador/antes/comparaciones.json').values()): errors.append('Diagnóstico anterior no reproduce brecha')
    if not all(obj(OUT/'navegador/final/comparaciones.json').values()): errors.append('Fotografía final falla')
    suite=obj(OUT/'servidor/final2/regresion-manifiesto.json')
    log=read(OUT/'servidor/final2/regresion-final.txt')
    if (suite['salida'] or suite['cambios_durante_prueba'] or suite['build']!=final['build']
            or 'Ran 592 tests' not in log or '\nOK\n' not in log or 'No changes detected' not in log):
        errors.append('Regresión final incompatible')
    docs=[ROOT/p for p in (
        '00_LEEME_PLANIFICACION.md','01_Proyecto_y_Releases.md','02_Diseno_Tecnico_R1_PMV.md',
        '03_Matriz_de_Trazabilidad_y_Pruebas.md','07_Reglas_de_Negocio.md','08_Historias_de_Usuario.md',
        '09_Product_Backlog.md','14_Sprint_Planning.md','16_Task_Breakdown.md','21_Alcance_Actual_y_Diferencias.md',
        'auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md',
        'auditoria_por_etapas/resultados/ETAPA-14.md','auditoria_por_etapas/resultados/ESTADO_GENERAL.md',
        'auditoria_por_etapas/resultados/soporte/14-H-inventario.md','auditoria_por_etapas/resultados/soporte/14-H-disposiciones.md')]
    docs += [OUT/'servidor/INFORME.md',OUT/'navegador/RESUMEN.md']
    checked=0;broken=[]
    for path in docs:
        content=read(path)
        if path.name=='ETAPA-14.md': content=content.split('## Registro anterior14-G')[0]
        content=re.sub(r'```.*?```','',content,flags=re.S)
        for link in re.findall(r'\[[^\]\n]+\]\(([^)\n]+)\)',content):
            if re.match(r'^https?://',link): continue
            file,_,anchor=unquote(link.strip('<>')).partition('#')
            target=(path.parent/file).resolve() if file else path
            checked+=1
            if target==OUT/'validacion-final.json': continue
            if not target.exists(): broken.append(dict(documento=str(path.relative_to(ROOT)),destino=link))
            elif anchor and target.name=='08_Historias_de_Usuario.md' and f'id="{anchor}"' not in source:
                broken.append(dict(documento=str(path.relative_to(ROOT)),ancla=anchor))
    if broken: errors.append('Enlaces rotos')
    context={str(p.relative_to(ROOT)).replace('\\','/'):sha(p) for p in docs}
    if (OUT/'contexto-final.json').exists() and obj(OUT/'contexto-final.json')!=context:
        errors.append('Documentos difieren del contexto final registrado')
    report=dict(at_utc=datetime.now(timezone.utc).isoformat(),pasada=1,sublote='14-H1',
        alcance='Carga original, dependencia de Kardex. Etapa14PARCIAL; no aprobación total.',
        source08=sha(ROOT/'08_Historias_de_Usuario.md'),build=final['build'],
        conteos=views.counts(source,stories,cases,criteria),derivados_identicos=derived,
        originales_alterados=originals,criterios=12,clasificaciones=inventory['clasificaciones'],
        tests_nuevos=8,regresion=592,navegador=reports,
        enlaces_comprobados=checked,enlaces_rotos=broken,errores=errors,coherencia_verificada=not errors)
    if not errors:
        for filename, data in [('contexto-final.json',context),('validacion-final.json',report)]:
            if not (OUT/filename).exists():
                with (OUT/filename).open('x',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return bool(errors)

if __name__=='__main__': sys.exit(main())
