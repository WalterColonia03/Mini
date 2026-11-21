"""Lee exclusivamente 08 como fuente funcional; deriva 07,09,03 e índice JSON.
No modifica la fuente, el software ni las bases. Ejecutar después de editar 08.
"""
from pathlib import Path
import hashlib,json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=ROOT/'08_Historias_de_Usuario.md'
def write(p,s):p.write_text(s.rstrip()+'\n',encoding='utf-8')
def parse():
    s=SOURCE.read_text(encoding='utf-8')
    assert '<!-- FUENTE-PRINCIPAL-20261112 -->' in s
    header=s.split('<a id="reglas">')[0]
    hs=[]
    for m in re.finditer(r'^### (HU-[A-Z]+-\d+[a-z]?) · (.*?)\n(.*?)(?=^### HU-|\Z)',header,re.M|re.S):
        ident,title,b=m.groups()
        ep,mos,sp,old=re.search(r'\*\*Épica:\*\* (EPIC-\w+)\. \*\*Prioridad MoSCoW:\*\* ([MSCW])\. \*\*Puntos Fibonacci:\*\* (\d+) \(orientativos; anteriores:(\d+)\)',b).groups()
        get=lambda p:re.search(p,b,re.M)[1].strip()
        hs.append(dict(id=ident,title=title,epic=ep,priority=mos,sp=int(sp),old_sp=int(old),order=int(get(r'^\*\*Orden de producto:\*\* (\d+)')),selected='**Alcance:** R1 seleccionado' in b,description=get(r'^\*\*Descripción de la HU:\*\* (.*)$'),rules=get(r'^\*\*Reglas relacionadas:\*\* (.*?)\. \*\*Dependencias'),dependency=get(r'\*\*Dependencias funcionales:\*\* (.*)$'),stage=get(r'^\*\*Procedencia:\*\* ETAPA-(\d+)'),criteria=[dict(id=x,text=t) for x,t in re.findall(r'^\*\*(HU-[^*]+/CA-\d+)\.\*\* (.*)$',b,re.M)]))
    tests=[]
    for m in re.finditer(r'^##### (CP-[A-Z0-9a-z-]+) · ([^\n]+)\n\n\*\*Cubre:\*\* (.*?)\. \*\*Estado:\*\* ([^\n]+)\n\*\*Precondiciones:\*\* ([^\n]+)\n\*\*Datos de prueba:\*\* ([^\n]+)\n\n(.*?)\n\n\*\*Resultados esperados:\*\* ([^\n]+)',s,re.M|re.S):
        ident,title,covers,state,pre,data,steps,expected=m.groups()
        tests.append(dict(id=ident,title=title,covers=covers.split(', '),state=state,preconditions=pre,data=data,steps=re.findall(r'^\d+\. (.*)$',steps,re.M),expected=expected))
    criteria=[dict(id=x,text=t) for x,t in re.findall(r'^\*\*([A-Z][A-Za-z0-9-]+/(?:CA|C)-\d+)\.\*\* (.*)$',s,re.M)]
    criteria.extend(dict(id=f'J-CA{n}',text=t) for n,t in re.findall(r'^\| J-CA(\d)\.[^|]+\| (.*?) \|$',s,re.M))
    return s,hs,tests,criteria

def generate():
    s,hs,tests,criteria=parse()
    assert len(hs)==74 and len(tests)==110 and len(criteria)==287,(len(hs),len(tests),len(criteria))
    digest=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    banner=f'> **VISTA DERIVADA.** Fuente principal: [08 · planificación](08_Historias_de_Usuario.md). No editar requisitos aquí. Generada desde SHA256 `{digest}`. Los cambios se hacen en08 y se regeneran estas vistas.\n\n'
    rn=s.split('## Anexo normativo · Reglas de negocio',1)[1].split('<a id="contratos">',1)[0].strip()
    write(ROOT/'07_Reglas_de_Negocio.md','# 7. Reglas de negocio · vista de la fuente principal\n\n'+banner+rn)
    lines=['# 9. Product Backlog · vista de la fuente principal','',banner,'Prioridad respecto a R1 de consolidación: M=Must, S=Should, C=Could, W=Won’t en este horizonte.33 HU seleccionadas,41 futuras; las8 ideas excluidas están en08. Puntos de la HU completa orientativos, no compromiso del equipo ni estimación de trabajo restante. Una prioridadS/C no permite incumplir una función visible. No hay Sprint, fecha, equipo o capacidad nuevos verificados.','','| Orden | ID | Épica | Título | MoSCoW | Fibonacci orientativo | SP anteriores | Selección | Dependencia |','|---:|---|---|---|:---:|---:|---:|---|---|']
    for h in sorted(hs,key=lambda x:x['order']):
        lines.append(f'| {h["order"]} | [{h["id"]}](08_Historias_de_Usuario.md#{h["id"]}) | {h["epic"]} | {h["title"]} | {h["priority"]} | {h["sp"]} | {h["old_sp"]} | {"R1 seleccionado" if h["selected"] else "FUTURO, requiere refinamiento"} | {h["dependency"]} |')
    lines+=['',f'Totales orientativos: catálogo {sum(h["sp"] for h in hs)} SP; R1 {sum(h["sp"] for h in hs if h["selected"])} SP; futuros {sum(h["sp"] for h in hs if not h["selected"])} SP. Procedencia histórica:231 SP. No sumar la fila futura a un Sprint actual.','', 'La aceptación del alcance no demuestra implementación. [Trabajos y dependencias](16_Task_Breakdown.md), [preparación del siguiente incremento](14_Sprint_Planning.md), [cobertura de pruebas](03_Matriz_de_Trazabilidad_y_Pruebas.md) y [diferencias comprobadas](21_Alcance_Actual_y_Diferencias.md) deben seguir estas fichas.']
    write(ROOT/'09_Product_Backlog.md','\n'.join(lines))
    lines=['# 3. Matriz de trazabilidad y pruebas · vista de la fuente principal','',banner,'Cobertura de diseño:219 CA base,60 criterios de encargos,4J-CA y4 de coherencia visible;110 casos escritos con pasos, datos y resultados esperados en08. La cobertura de diseño no es cobertura de ejecución. Ningún nuevo caso se considera aprobado por tener una fila.','','La evidencia previa por etapa permanece íntegra; sus conclusiones valen para el build/criterios/casos efectivamente probados. [Verificación previa](auditoria_por_etapas/resultados/conciliacion_20261112/VERIFICACION.md), [matriz antes de esta unificación](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/03_Matriz_de_Trazabilidad_y_Pruebas.md) y [mapa de discrepancias](auditoria_por_etapas/resultados/conciliacion_20261112/CONSOLIDACION.md).434 pruebas SQLite y muestraPG18.4 no equivalen a ejecutar los110 casos nuevos ni toda la interfaz.','','| Criterio | Alcance | Casos escritos | Fuente/evidencia previa | Ejecución de estos casos |','|---|---|---|---|---|']
    indexed={}
    for t in tests:
        for c in t['covers']:indexed.setdefault(c,[]).append(t['id'])
    byhu={h['id']:h for h in hs}
    for c in criteria:
        cid=c['id'];hu=cid.split('/')[0];h=byhu.get(hu)
        scope='R1' if h and h['selected'] else 'FUTURO' if h else 'Transversal según aplicabilidad en08'
        evidence=f'[ETAPA-{h["stage"]}](auditoria_por_etapas/resultados/ETAPA-{h["stage"]}.md)' if h and int(h['stage'])<=12 else 'Consultar mapa; sin atribuir ejecución de etapa futura'
        anchor=cid.replace('/','-') if not cid.startswith('J-CA') else 'contrato-PROP-E00-HU-02'
        links=', '.join(f'[{tid}](08_Historias_de_Usuario.md#{tid})' for tid in indexed.get(cid,[]))
        lines.append(f'| [{cid}](08_Historias_de_Usuario.md#{anchor}) | {scope} | {links} | {evidence} | NO EJECUTADO en este corte documental |')
    lines+=['','## Índice de casos con datos y resultados','','| Caso | Propósito | Detalle completo |','|---|---|---|']
    for t in tests:lines.append(f'| {t["id"]} | {t["title"]} | [Pasos, datos y resultado esperado](08_Historias_de_Usuario.md#{t["id"]}) |')
    lines+=['','## Registro de ejecución requerido','','Cada ejecución debe registrar caso/criterio exacto, build/hash, fecha, rol, fixture, versión del motor, herramienta/capa, observado, esperado, resultado, evidencia sanitizada y limitación. Para inspección inversa agregar literal visible/ruta/estado y requisito que lo respalda. Si no se ha recorrido, registrar NO EXAMINADO; si faltó entorno, NO EJECUTADO. No convertir ninguno en defecto ni cumplimiento sin evidencia.']
    write(ROOT/'03_Matriz_de_Trazabilidad_y_Pruebas.md','\n'.join(lines))
    index=dict(source=SOURCE.name,source_sha256=digest,stories=hs,tests=tests,criteria=criteria,generated=True,authority='08 exclusivamente; este JSON es derivado')
    write(HERE/'INDICE_DERIVADO.json',json.dumps(index,ensure_ascii=False,indent=2))
    return dict(hu=len(hs),criteria=len(criteria),cases=len(tests),sp=sum(h['sp'] for h in hs),selected_sp=sum(h['sp'] for h in hs if h['selected']))
if __name__=='__main__':print(json.dumps(generate(),ensure_ascii=False))
