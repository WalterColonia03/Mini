"""Publish and verify the completed, dated 03-X cut; no business DB connection."""
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[3]
RESULTS=ROOT/'auditoria_por_etapas/resultados'
LINK='anexos/ETAPA-03-X-codigos-ean-upc.md'
FULL='auditoria_por_etapas/resultados/'+LINK
summary=('**Etapa 03 hasta 03-X.** 69/69 controles navegador/HTTP/ORM,16/16 de servicio/DB y9/9 de observación física. '
         'El teléfono entregó UPC12 para la etiqueta EAN13 almacenada; la consulta no lo reconoció como duplicado. '
         '**PROD03/CA02 PARCIAL** en esta frontera:22 CA CUMPLE en muestras,1 PARCIAL y4 futuros;4 suplementarios conservan sus muestras. '
         'Base original intacta; política de identidad, despliegue y recepción/retiros pendientes. '
         '**Cursor03-Y / AUD03Y-PREFLIGHT-IDENTIDAD01**. [Evidencia y alternativas]('+LINK+').')

def read(p):return p.read_text(encoding='utf-8-sig')
def put(p,t):p.write_text(t,encoding='utf-8')
def append_once(p,text):
    t=read(p)
    if text not in t:put(p,t.rstrip()+'\n\n'+text+'\n')

for name in ['ETAPA-03.md','ESTADO_GENERAL.md']:
    p=RESULTS/name;t=read(p)
    t=re.sub(r'\*\*Etapa 03 hasta 03-W\.\*\*[^\n]+',lambda m:summary,t,count=1)
    if name=='ETAPA-03.md':
        t=t.replace('Balance vigente de los27CA base. **23 CUMPLE en sus muestras y4 PREVISTO/FUTURO**',
                    'Balance vigente de los27CA base. **22 CUMPLE en sus muestras,1 PARCIAL (PROD03/CA02, frontera EAN/UPC03-X) y4 PREVISTO/FUTURO**')
        t=t.replace('El encabezado y 03-W contienen el estado actual.','El encabezado y03-X contienen el estado actual;03-W conserva la conciliación anterior.')
    else:
        t=t.replace('Actualizado: **10/11/2026, America/Lima**.','Actualizado: **11/11/2026, America/Lima**.')
        t=re.sub(r'^\| 03 Categorías y productos \|[^\n]+',
          '| 03 Categorías y productos | 11/11/2026 | 9HU/27CA:22 CUMPLE muestras,1 PARCIAL PROD03/CA02,4 futuros;4 suplementarios | **03-X ejecutado software y teléfono**, hallazgos abiertos | EAN13 capturado como UPC12 no detecta duplicado de representación; política pendiente. Despliegue y recepción/retiros pendientes | **03-Y / AUD03Y-PREFLIGHT-IDENTIDAD01**: copia nueva, clasificar códigos y posibles colisiones sin imponer GTIN ni fusionar |',t,flags=re.M)
        t=re.sub(r'^> Retomar etapa 03 con PROTOCOLO_COMUN completo[^\n]+',
          '> Retomar etapa03 con PROTOCOLO_COMUN completo, ESTADO_GENERAL, ETAPA-03 y anexo03-X. Cursor03-Y / AUD03Y-PREFLIGHT-IDENTIDAD01: copia nueva marcada de la original, clasificar códigos y grupos candidatos a colisión bajo DEC-03X-IDENTIDAD. No migrar original ni inferir GTIN por longitud ni fusionar. La lectura físicaX ya está ejecutada; preservar PARCIAL de PROD03/CA02, discrepancia literal CA01 y pendientes de despliegue/recepción/retiros.',t,flags=re.M)
    put(p,t)
    append_once(p,'## Continuación 03-X · EAN/UPC\n\nActualización11/11/2026; ejecución10/11,23:00–23:04 Lima. '+summary)

p=RESULTS/'anexos/ETAPA-03-inventario.md';t=read(p)
t=t.replace('Inventario inicial y trazabilidad conciliada hasta 03-W','Inventario inicial y trazabilidad conciliada hasta 03-X')
t=re.sub(r'^\| PROD03/CA02 ·[^\n]+',
 '| PROD03/CA02 · 08:232 | Duplicado advertido al leer | Literal O/P/X correcto. EnX la etiqueta EAN13 existente se recibe como UPC12 y muestra Sin duplicados | PARCIAL en interoperabilidad EAN/UPC; muestras literales conservadas | P1, DEC-03X-IDENTIDAD; [evidencia03-X](ETAPA-03-X-codigos-ean-upc.md) |',t,flags=re.M)
t=t.replace('Balance actual: **23 CUMPLE en sus muestras y4 PREVISTO/FUTURO**.',
 'Balance actual03-X: **22 CUMPLE en sus muestras,1 PARCIAL (PROD03/CA02, frontera EAN/UPC) y4 PREVISTO/FUTURO**. Véase [03-X](ETAPA-03-X-codigos-ean-upc.md).')
put(p,t)
append_once(RESULTS/'anexos/ETAPA-03-W-conciliacion.md',
 '**Actualización posterior03-X:** la matriz anterior conserva su corteW. La lectura física EAN13→UPC12 amplía la frontera de PROD03/CA02 y deja ese criterio PARCIAL; balance22 CUMPLE muestras/1 PARCIAL/4 futuros. [Resultado y cursor vigente](ETAPA-03-X-codigos-ean-upc.md).')
for name in ['08_Historias_de_Usuario.md','09_Product_Backlog.md','03_Matriz_de_Trazabilidad_y_Pruebas.md','21_Alcance_Actual_y_Diferencias.md']:
    append_once(ROOT/name,'**Actualización03-X,11/11/2026 (ejecución10/11):** PROD03/CA02 queda PARCIAL en la frontera EAN13/UPC12: '
      'seis lecturas físicas recibieron12 dígitos ante una ficha almacenada con13 y el aviso no indicó duplicado. '
      'La unicidad literal conserva sus muestras favorables.69/69 controles navegador/HTTP/ORM,16/16 servicio/DB y9/9 observación física; '
      'estos últimos acreditan la observación, no la equivalencia. DEC-03X-IDENTIDAD y PROP-03X-CA01..03/T01..03 son propuestas pendientes, '
      'sin cambio funcional, fusión ni migración. No se modifican estimaciones/sprints históricos ni se aprueban otras etapas. '
      '[Evidencia, alternativas y criterios]('+FULL+').')
append_once(ROOT/'16_Task_Breakdown.md',
 '**Propuestas03-X,11/11/2026:** PROP-03X-T01, clasificar datos y posibles colisiones en copia; '
 'PROP-03X-T02, implementación condicionada a DEC-03X-IDENTIDAD; PROP-03X-T03, pruebas de representaciones, códigos internos, '
 'roles, histórico y concurrencia. Pendientes, sin horas/sprint asignados ni HU duplicada. '
 '[Criterios y evidencia]('+FULL+').')
p=RESULTS/LINK;t=read(p).replace('10/11/2026, America/Lima. Sublote','Actualizado11/11/2026, America/Lima; ejecución10/11,23:00–23:04 Lima. Sublote');put(p,t)

runs=['03-X-browser-20261111T040056659143Z-a42ce2ac','03-X-browser-20261111T040227561878Z-69a0d2f3','03-X-phone-20261111T040311661823Z-6ffff079']
records=[json.loads(read(RESULTS/'evidencias'/r/'result.json')) for r in runs]
assert all(r['port_closed'] and all(r['protected_unchanged'].values()) for r in records)
br=json.loads(read(RESULTS/'evidencias'/runs[1]/'browser.json'))
ph=json.loads(read(RESULTS/'evidencias'/runs[2]/'phone.json'))
assert len(br['cases'])==69 and all(c['ok'] for c in br['cases'])
assert len(br['service'])==16 and all(c['ok'] for c in br['service'])
assert ph['status']=='completed' and len(ph['checks'])==9 and all(c['ok'] for c in ph['checks'])
original=hashlib.sha256((ROOT/'r1-pmv/r1_pmv.sqlite3').read_bytes()).hexdigest()
assert original=='4406ecd5babab34f0bb264e82c134eb21563494f9faf50e462d50c30c9d2ea95'
missing=[]
for target in re.findall(r'\]\(([^)]+)\)',read(RESULTS/LINK)):
    if not target.startswith('https:') and not ((RESULTS/LINK).parent/target).resolve().exists():missing.append(target)
assert not missing,missing
result={'updated_lima':'2026-11-11','execution_lima':'2026-11-10 23:00–23:04',
 'browser_checks':69,'service_checks':16,'physical_checks':9,'physical_complete_readings':6,
 'original_sha256':original,'all_run_protected_files_unchanged':True,'all_run_ports_closed':True,
 'xlsx_present':(ROOT/'PLANIFICACION_SCRUM_R1PMV.xlsx').exists(),'missing_links':missing,
 'base_criteria':{'sample_pass':22,'partial':1,'future':4},'supplementary_sample_pass':4,
 'partial':'PROD03/CA02 EAN13/UPC12 interoperability; literal uniqueness passes samples',
 'functional_application_changes':False,'cursor':'03-Y / AUD03Y-PREFLIGHT-IDENTIDAD01','runs':runs}
put(RESULTS/'evidencias/03-X-cierre.json',json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False))
