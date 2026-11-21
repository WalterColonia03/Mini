"""Verifica evidencia y documentos sin modificar fuentes funcionales ni producto."""
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import unquote

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3];RESULTS=HERE.parents[1]
read=lambda p:p.read_text(encoding='utf-8')
load=lambda p:json.loads(read(p))
sha=lambda data:hashlib.sha256(data).hexdigest()
save=lambda p,data:p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sys.path.insert(0,str(RESULTS/'fuente_unica_20261112'))
import regenerar_vistas as views
s,stories,cases,criteria=views.parse()
errors=views.document_errors(s,stories,cases,criteria)
expected={};views.write=lambda p,txt:expected.update({p:txt.rstrip()+'\n'})
counts=views.generate()
matching={p.name:read(p)==text for p,text in expected.items()}
errors += ['Vista desfasada: '+name for name,ok in matching.items() if not ok]
executed=views.parse(read(HERE/'08-ejecutado.md'))[3]
indexed={c['id']:c['text'] for c in criteria};old={c['id']:c['text'] for c in executed}
ids=['HU-INV-02/CA-01','HU-INV-02/CA-02','HU-INV-02/CA-03','HU-INV-02/CA-04','RN-05/C-01','RN-05/C-03','RN-05/C-04']
proofs=[
 ('I02/I05/I24; tests_invalid_http_keys_and_fields / same_commercial_lot','A10→8; exceso y otros inválidos sin mutar; bajaR2 conservaR1','Máximo999999 enChrome pendiente'),
 ('I04/I20..23; test_service_types_expiry_and_inactive_product_policy','Causa real según fechaLima; daño vencido no, robo explicado y vencimiento sí','No prueba salto de medianoche concurrente'),
 ('I03/I13; test_snapshot_and_ledger_survive_master_changes','Detalle obligatorio y responsable original conservado','Accesibilidad integral no ejecutada'),
 ('I05/I11b/I13/I14; tests_snapshot/replay/legacy','Constancia correlativa recuperable, historia y ausencia explícita','Impresora física y escrituraSQL privilegiada no ejecutadas'),
 ('I22; Stage08.test_writeoff_http_date_and_real_cause_preserve_rejected_data','Robo vencido/inactivo conserva causa/costo, sin cambios de precio/caja/ventas','Caso operativo real no diagnosticado'),
 ('I13..18/I25; tests_receipt_roles_methods / legacy / escapes','ADMIN/ALM consulta; VEN403; POST405; fotografía y leyenda interna; mediaPrint','Print dispatch instrumentado; no impresora física'),
 ('I06/I07/I11/I19; tests_replay / postwrite_failures / stock_exhausted','UnaUUID, una baja entre sesiones; divergencia/actorrechazados; rollback tras escritura','Concurrencia realPG y ajuste nuevo pendientes'),
]
matrix=[]
for cid,(evidence,observed,limit) in zip(ids,proofs):
    identical=indexed[cid]==old[cid]
    if not identical:errors.append('Criterio cambió tras ejecución: '+cid)
    matrix.append(dict(id=cid,fuente='08_Historias_de_Usuario.md#'+cid.replace('/','-'),literal=indexed[cid],
        actor='ADMIN/ALMACENERO; VENDEDOR denegado',prioridad='P1' if cid.endswith('C-04') else 'P2',
        ruta='/inventario/bajas/nueva/ → /inventario/bajas/{UUID}/; /inventario/productos/{UUID}/movimientos/',
        codigo='inventory/services.write_off_stock; StockWriteOff; views.stock_writeoff_receipt; ledger',
        evidencia=evidence,observado=observed,estado='PARCIAL' if cid=='RN-05/C-04' else 'CUMPLE en muestra',
        limite_y_siguiente_accion=limit,criterio_identico_al_ejecutado=identical))
save(HERE/'criterios-final.json',dict(pasada=1,sublote='14-I',denominador_principal=7,cumple_muestra=6,parcial=1,
    dependencias='INV04/CA03,DOC03AI/C03,RN14 revalidadas en muestras, no contratos completos',matriz=matrix))

spec=importlib.util.spec_from_file_location('base14',HERE.parent/'14-D-20261113/navegador/recorrido.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
runtime=base.build()
spec2=importlib.util.spec_from_file_location('verifyH2',HERE.parent/'14-H2-20261114/verificar.py')
canonical=importlib.util.module_from_spec(spec2);spec2.loader.exec_module(canonical)
sources=canonical.product()
complete=dict(head=runtime['head'],archivos=len(sources),build=sha(json.dumps(sources,sort_keys=True,separators=(',',':')).encode()),
    fuentes=sources,runtime_sha256=runtime['sha256'],runtime_archivos=len(runtime['archivos']),plan08=sha((ROOT/'08_Historias_de_Usuario.md').read_bytes()))
save(HERE/'build-final.json',complete)
before=load(HERE/'build-antes.json')['archivos']
oldH2=load(HERE.parent/'14-H2-20261114/build-final.json')['fuentes']
baseline_compatible=all(oldH2.get(p)==h for p,h in before.items())
compatibility={}
for name in ['final-2','cadena-final']:
    run=load(HERE/'navegador'/name/'ejecucion.json')
    files=load(HERE/'navegador'/name/'build-final.json')['archivos']
    compatibility[name]=dict(completo=run['estado']=='recorrido_completo',estable=run['build_estable'],
        producto_identico=files==runtime['archivos'],checkpoints=len(run['pasos']),capturas=len(list((HERE/'navegador'/name).glob('*.jpg'))))
    if not all(compatibility[name][k] for k in ('completo','estable','producto_identico')):errors.append('Corrida incompatible: '+name)
server=load(HERE/'servidor/regresion-2/manifiesto.json')
server_ok=server['status']==0 and server['fuentes_estables'] and server['despues']['archivos']==runtime['archivos']
if not server_ok:errors.append('Servidor incompatible')
documents=[ROOT/n for n in ('08_Historias_de_Usuario.md','07_Reglas_de_Negocio.md','09_Product_Backlog.md','03_Matriz_de_Trazabilidad_y_Pruebas.md',
    '02_Diseno_Tecnico_R1_PMV.md','14_Sprint_Planning.md','16_Task_Breakdown.md','21_Alcance_Actual_y_Diferencias.md','01_Proyecto_y_Releases.md','00_LEEME_PLANIFICACION.md')]
documents += [RESULTS/'ETAPA-14.md',RESULTS/'ESTADO_GENERAL.md',RESULTS/'soporte/14-I-inventario.md',RESULTS/'soporte/14-I-disposiciones.md',HERE/'servidor/INFORME.md',HERE/'navegador/RESUMEN.md']
broken=[]
for p in documents:
    text=read(p)
    if p.name=='ETAPA-14.md':text=text.split('## Registro anterior14-H2, conservado')[0]
    for target in re.findall(r'\]\(([^)]+)\)',text):
        if re.match(r'^(https?:|#)',target):continue
        relative=unquote(target.split('#')[0])
        if relative and not (p.parent/relative).exists():broken.append(str(p.relative_to(ROOT))+': '+target)
errors += ['Enlace roto: '+b for b in broken]
changed=[p for p in sorted(before.keys()|runtime['archivos'].keys()) if before.get(p)!=runtime['archivos'].get(p)]
report=dict(fecha_utc=datetime.now(timezone.utc).isoformat(),pasada=1,sublote='14-I',cursor='14-J-AJUSTES-HISTORIA-01',
    fuente08=complete['plan08'],conteos=counts,vistas_reproducidas=matching,criterios_ejecutados_compatibles=all(x['criterio_identico_al_ejecutado'] for x in matrix),
    baselineH2_compatible=baseline_compatible,build_completo=complete['build'],runtime_build=runtime['sha256'],servidor_final_compatible=server_ok,
    navegador=compatibility,archivos_producto_modificados=changed,documentos={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in documents},
    enlaces_rotos=broken,errores=errors,resultado='VALIDO' if not errors else 'REVISAR',
    limites='No aprueba etapa completa, operación, concurrenciaPG, impresión física, SQL privilegiado ni otros módulos.')
save(HERE/'validacion-final.json',report)
print(json.dumps({k:v for k,v in report.items() if k not in ('documentos','archivos_producto_modificados')},ensure_ascii=False,indent=2))
sys.exit(bool(errors))
