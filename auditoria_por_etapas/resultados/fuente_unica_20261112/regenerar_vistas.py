"""Deriva07/09/03 e índice desde08 sin congelar el tamaño del catálogo.
No modifica08, el producto ni bases. Documentación no equivale a evidencia.
"""
from pathlib import Path
from collections import Counter
import hashlib,json,re
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
SOURCE=ROOT/'08_Historias_de_Usuario.md'
def write(p,s):p.write_text(s.rstrip()+'\n',encoding='utf-8')
def required(pattern,text,label):
    m=re.search(pattern,text,re.M)
    if not m:raise ValueError(f'Falta o está mal formado {label}')
    return m
def parse(source_text=None):
    s=SOURCE.read_text(encoding='utf-8') if source_text is None else source_text
    if '<!-- FUENTE-PRINCIPAL-20261112 -->' not in s:raise ValueError('No se reconoce la fuente principal08')
    if '<a id="reglas">' not in s:raise ValueError('Falta delimitación de reglas')
    header=s.split('<a id="reglas">',1)[0]
    hs=[]
    # Primero encabezados amplios: no omitir silenciosamente una ficha mal formada.
    headings=list(re.finditer(r'^### (HU-\S+)([^\n]*)$',header,re.M))
    for i,m in enumerate(headings):
        ident=m[1];title=required(r'^ · (.+)$',m[2],f'título de {ident}')[1]
        if not re.fullmatch(r'HU-[A-Z]+-\d+[a-z]?',ident):raise ValueError(f'ID de HU no reconocido: {ident}')
        b=header[m.end():headings[i+1].start() if i+1<len(headings) else len(header)]
        ep,mos,sp,old=required(r'\*\*Épica:\*\* (EPIC-\w+)\. \*\*Prioridad MoSCoW:\*\* ([MSCW])\. \*\*Puntos Fibonacci:\*\* (\d+) \(orientativos; anteriores:\s*(\d+|—)\)',b,f'épica/MoSCoW/Fibonacci de {ident}').groups()
        get=lambda p,label:required(p,b,f'{label} de {ident}')[1].strip()
        scope=get(r'^\*\*Alcance:\*\* (.+)$','alcance')
        if not scope.startswith(('R1 seleccionado','FUTURO')):raise ValueError(f'Alcance no reconocido en {ident}')
        hs.append(dict(id=ident,title=title,epic=ep,priority=mos,sp=int(sp),old_sp=None if old=='—' else int(old),order=int(get(r'^\*\*Orden de producto:\*\* (\d+)','orden')),selected=scope.startswith('R1 seleccionado'),description=get(r'^\*\*Descripción de la HU:\*\* (.+)$','descripción'),rules=get(r'^\*\*Reglas relacionadas:\*\* (.*?)\. \*\*Dependencias','reglas'),dependency=get(r'\*\*Dependencias funcionales:\*\* (.+)$','dependencias'),stage=get(r'^\*\*Procedencia:\*\* ETAPA-(\d+)','procedencia'),criteria=[dict(id=x,text=t) for x,t in re.findall(r'^\*\*(HU-[^*]+/CA-\d+)\.\*\* (.+)$',b,re.M)]))
    tests=[]
    headings=list(re.finditer(r'^##### (CP-\S+)([^\n]*)$',s,re.M))
    for i,m in enumerate(headings):
        ident=m[1];title=required(r'^ · (.+)$',m[2],f'título de {ident}')[1]
        if not re.fullmatch(r'CP-[A-Za-z0-9-]+',ident):raise ValueError(f'ID de caso no reconocido: {ident}')
        b=s[m.end():headings[i+1].start() if i+1<len(headings) else len(s)]
        b=re.split(r'^#{1,4} |^<a id="',b,maxsplit=1,flags=re.M)[0]
        covers,state=required(r'^\*\*Cubre:\*\* (.+?)\. \*\*Estado:\*\* (.+)$',b,f'cobertura/estado de {ident}').groups()
        field=lambda name:required(r'^\*\*'+name+r':\*\* (.+)$',b,f'{name} de {ident}')[1]
        evidence=re.search(r'^\*\*Evidencia de ejecución:\*\* (.+)$',b,re.M)
        tests.append(dict(id=ident,title=title,covers=[x.strip() for x in covers.split(',')],state=state,preconditions=field('Precondiciones'),data=field('Datos de prueba'),steps=re.findall(r'^\d+\. (.+)$',b,re.M),expected=field('Resultados esperados'),execution_evidence=evidence[1] if evidence else None))
    if re.search(r'^\*\*(?:CA|C)-\S+',s,re.M):raise ValueError('Criterio sin identidad compuesta HU/contrato')
    criteria=[dict(id=x,text=t) for x,t in re.findall(r'^\*\*([A-Z][A-Za-z0-9-]+/(?:CA|C)-\d+)\.\*\* (.+)$',s,re.M)]
    if len(re.findall(r'^\*\*([A-Z][A-Za-z0-9-]+/(?:CA|C)-[^\s*]+)',s,re.M))!=len(criteria):raise ValueError('Hay un criterio con formato no reconocido')
    category=re.findall(r'^\| J-CA(\d+)\.[^|]+\| (.+?) \|$',s,re.M)
    if len(re.findall(r'^\| J-CA\S+',s,re.M))!=len(category):raise ValueError('Hay un criterio J-CA mal formado')
    criteria.extend(dict(id=f'J-CA{n}',text=t) for n,t in category)
    return s,hs,tests,criteria
def counts(s,hs,tests,criteria):
    epics=re.findall(r'^## (EPIC-[A-Z]+) ·',s,re.M)
    outside=s.split('<a id="fuera">',1)[1] if '<a id="fuera">' in s else ''
    outside=outside.split('## Evidencia,',1)[0]
    ideas=re.findall(r'^\|\s*`?(HU-[A-Z]+-\d+[a-z]?)`?\s*\|',outside,re.M)
    cids=[c['id'] for c in criteria]
    return dict(stories=len(hs),selected=sum(h['selected'] for h in hs),future=sum(not h['selected'] for h in hs),outside_ideas=len(ideas),outside_ids=ideas,epics=len(epics),epic_ids=epics,base_criteria=sum('/CA-' in cid for cid in cids),category_criteria=sum(cid.startswith('J-CA') for cid in cids),visible_criteria=sum(cid.startswith('CT-COHERENCIA-UI/C-') for cid in cids),contract_criteria=sum('/C-' in cid and not cid.startswith('CT-COHERENCIA-UI/') for cid in cids),written_cases=len(tests),fibonacci_catalog=sum(h['sp'] for h in hs),fibonacci_selected=sum(h['sp'] for h in hs if h['selected']))
def document_errors(s,hs,tests,criteria):
    """Invariantes y declaraciones de08, no cantidades históricas fijas."""
    errors=[]
    def require(ok,msg):
        if not ok:errors.append(msg)
    n=counts(s,hs,tests,criteria)
    for label,ids in [('HU',[h['id'] for h in hs]),('criterio',[c['id'] for c in criteria]),('caso',[t['id'] for t in tests]),('épica',n['epic_ids']),('idea excluida',n['outside_ids'])]:
        require(bool(ids) or label=='idea excluida',f'No hay {label}');require(len(ids)==len(set(ids)),f'ID duplicado de {label}')
    require(not ({h['id'] for h in hs}&set(n['outside_ids'])),'Una HU también figura como idea excluida')
    require(set(h['order'] for h in hs)==set(range(1,len(hs)+1)),'Orden de producto incompleto/duplicado')
    require(all(h['sp'] in [1,2,3,5,8,13] for h in hs),'Puntos fuera de Fibonacci acordado')
    require(all((h['priority']=='W')==(not h['selected']) for h in hs),'MoSCoW y alcance contradictorios')
    covered=Counter(cid for t in tests for cid in t['covers']);cids={c['id'] for c in criteria}
    require(cids==set(covered),'Criterios sin caso o referencias inexistentes: '+str(sorted(cids^set(covered))))
    base_ids={c['id'] for c in criteria if '/CA-' in c['id']};attached=set()
    for h in hs:
        require(h['epic'] in n['epic_ids'],f'Épica inexistente en {h["id"]}')
        require(bool(h['description'] and h['criteria'] and h['dependency']),f'Ficha incompleta {h["id"]}')
        for c in h['criteria']:
            attached.add(c['id']);require(c['id'].startswith(h['id']+'/CA-'),f'Criterio de otra HU en {h["id"]}: {c["id"]}')
    require(attached==base_ids,'CA fuera de su ficha o sin HU')
    for t in tests:
        require(bool(t['preconditions'] and t['data'] and t['steps'] and t['expected']),f'Caso incompleto {t["id"]}')
        require(len(t['covers'])==len(set(t['covers'])),f'Cobertura duplicada en {t["id"]}')
        state=t['state'].upper()
        affirmative=bool(re.search(r'\b(EJECUTAD[OA]|VERIFICAD[OA]|APROBAD[OA]|REPROBAD[OA]|FALLID[OA]|CUMPLE|INCUMPLE)\b',state)) and not re.search(r'\bNO (EJECUTAD[OA]|VERIFICAD[OA])\b',state)
        require(not affirmative or bool(re.search(r'\[[^\]]+\]\([^)]+\)',t.get('execution_evidence') or '')),f'Estado de ejecución sin enlace preciso de evidencia: {t["id"]}')
    top=s.split('## Fichas de historias',1)[0]
    declaration=re.search(r'Alcance:\s*(\d+)\s*HU,\s*(\d+)\s*seleccionadas para R1 y\s*(\d+)\s*futuras;\s*(\d+)\s*ideas excluidas',top)
    require(bool(declaration),'Falta declaración de alcance vigente en cabecera')
    if declaration:require(tuple(map(int,declaration.groups()))==(n['stories'],n['selected'],n['future'],n['outside_ideas']),'Declaración de alcance desfasada')
    for m in re.finditer(r'Las\s*(\d+)\s*HU seleccionadas',top):require(int(m[1])==n['selected'],'Cantidad de HU seleccionadas desfasada en cabecera')
    for m in re.finditer(r'Las\s*(\d+)\s*futuras',top):require(int(m[1])==n['future'],'Cantidad de HU futuras desfasada en cabecera')
    totals=re.search(r'Total:\s*(\d+)\s*HU/\s*(\d+)\s*SP orientativos;\s*R1:\s*(\d+)\s*SP',top)
    require(bool(totals),'Falta declaración de totalesHU/SP')
    if totals:require(tuple(map(int,totals.groups()))==(n['stories'],n['fibonacci_catalog'],n['fibonacci_selected']),'TotalesHU/SP desfasados')
    table=re.findall(r'^\| \[(EPIC-[A-Z]+)\]\(#[^)]+\) \|[^|]+\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|$',top,re.M)
    require(Counter(row[0] for row in table)==Counter(n['epic_ids']),'Tabla de épicas incompleta/duplicada')
    for eid,*values in table:
        group=[h for h in hs if h['epic']==eid];sel=[h for h in group if h['selected']]
        require(tuple(map(int,values))==(len(group),len(sel),len(group)-len(sel),sum(h['sp'] for h in group),sum(h['sp'] for h in sel)),f'Totales desfasados en {eid}')
    declaration=re.search(r'Los\s*(\d+)\s*CA base se completan con\s*(\d+)\s*criterios de contratos y\s*(\d+)\s*criterios\s*J.*?CT-COHERENCIA-UI añade\s*(\d+)\s*criterios',top,re.S)
    require(bool(declaration),'Falta declaración de cobertura vigente')
    if declaration:require(tuple(map(int,declaration.groups()))==(n['base_criteria'],n['contract_criteria'],n['category_criteria'],n['visible_criteria']),'Declaración de criterios desfasada')
    declared_cases=re.search(r'hay\s*(\d+)\s*casos escritos',top)
    require(bool(declared_cases),'Falta declaración de casos escritos')
    if declared_cases:require(int(declared_cases[1])==len(tests),'Cantidad de casos declarada desfasada')
    declared_criteria=re.search(r'No son\s*(\d+)\s*casos ejecutados',top)
    if declared_criteria:require(int(declared_criteria[1])==len(criteria),'Cantidad total de criterios desfasada en cabecera')
    rn_section=s.split('## Anexo normativo · Reglas de negocio',1)[1].split('<a id="contratos">',1)[0]
    rn_ids=re.findall(r'^### (RN-\d+) ·',rn_section,re.M)
    require(bool(rn_ids) and len(rn_ids)==len(set(rn_ids)),'RN ausentes o duplicadas')
    return errors
def generate(source_text=None):
    s,hs,tests,criteria=parse(source_text)
    errors=document_errors(s,hs,tests,criteria)
    if errors:raise ValueError('\n'.join(errors))
    n=counts(s,hs,tests,criteria)
    digest=hashlib.sha256(SOURCE.read_bytes() if source_text is None else s.encode('utf-8')).hexdigest()
    banner=f'> **VISTA DERIVADA.** Fuente principal: [08 · planificación](08_Historias_de_Usuario.md). No editar requisitos aquí. Generada desde SHA256 `{digest}`. Los cambios se hacen en08 y se regeneran estas vistas.\n\n'
    outputs={}
    rn=s.split('## Anexo normativo · Reglas de negocio',1)[1].split('<a id="contratos">',1)[0].strip()
    outputs[ROOT/'07_Reglas_de_Negocio.md']='# 7. Reglas de negocio · vista de la fuente principal\n\n'+banner+rn
    lines=['# 9. Product Backlog · vista de la fuente principal','',banner,f'Prioridad respecto a R1 de consolidación: M=Must, S=Should, C=Could, W=Won’t en este horizonte. {n["selected"]} HU seleccionadas, {n["future"]} futuras; {n["outside_ideas"]} ideas excluidas en08. Puntos de la HU completa orientativos, no compromiso del equipo ni trabajo restante. Una prioridadS/C no permite incumplir una función visible. No se infiere Sprint, fecha, equipo o capacidad a partir de estos tamaños.','','| Orden | ID | Épica | Título | MoSCoW | Fibonacci orientativo | SP anteriores | Selección | Dependencia |','|---:|---|---|---|:---:|---:|---:|---|---|']
    for h in sorted(hs,key=lambda x:x['order']):
        prior='—' if h['old_sp'] is None else str(h['old_sp'])
        lines.append(f'| {h["order"]} | [{h["id"]}](08_Historias_de_Usuario.md#{h["id"]}) | {h["epic"]} | {h["title"]} | {h["priority"]} | {h["sp"]} | {prior} | {"R1 seleccionado" if h["selected"] else "FUTURO, requiere refinamiento"} | {h["dependency"]} |')
    lines+=['',f'Totales orientativos: catálogo {n["fibonacci_catalog"]} SP; R1 {n["fibonacci_selected"]} SP; futuros {n["fibonacci_catalog"]-n["fibonacci_selected"]} SP. La procedencia de tamaños anteriores se conserva por ficha; «—» identifica una historia sin estimación previa. No sumar trabajo futuro a un Sprint actual.','', 'La aceptación del alcance no demuestra implementación. [Trabajos y dependencias](16_Task_Breakdown.md), [preparación del siguiente incremento](14_Sprint_Planning.md), [cobertura de pruebas](03_Matriz_de_Trazabilidad_y_Pruebas.md) y [diferencias comprobadas](21_Alcance_Actual_y_Diferencias.md) deben seguir estas fichas.']
    outputs[ROOT/'09_Product_Backlog.md']='\n'.join(lines)
    lines=['# 3. Matriz de trazabilidad y pruebas · vista de la fuente principal','',banner,f'Cobertura de diseño: {n["base_criteria"]} CA base, {n["contract_criteria"]} criterios de encargos, {n["category_criteria"]} J-CA y {n["visible_criteria"]} de coherencia visible; {len(tests)} casos escritos con pasos, datos y resultados esperados en08. La cobertura de diseño no es cobertura de ejecución. Ningún caso se considera aprobado por tener una fila.','','La evidencia previa permanece fechada y acotada a su build, requisitos y casos. [Verificación anterior](auditoria_por_etapas/resultados/conciliacion_20261112/VERIFICACION.md), [matriz antes de la unificación](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/03_Matriz_de_Trazabilidad_y_Pruebas.md) y [mapa de discrepancias](auditoria_por_etapas/resultados/conciliacion_20261112/CONSOLIDACION.md). La existencia de un informe o el número de tests aprobados no verifica automáticamente estos casos.','','| Criterio | Alcance | Casos escritos | Registro de etapa / evidencia | Estado declarado de los casos |','|---|---|---|---|---|']
    indexed={}
    for t in tests:
        for c in t['covers']:indexed.setdefault(c,[]).append(t)
    byhu={h['id']:h for h in hs}
    for c in criteria:
        cid=c['id'];h=byhu.get(cid.split('/')[0])
        scope='R1' if h and h['selected'] else 'FUTURO' if h else 'Transversal según aplicabilidad en08'
        stage=ROOT/f'auditoria_por_etapas/resultados/ETAPA-{h["stage"]}.md' if h else None
        evidence=f'[Registro ETAPA-{h["stage"]}](auditoria_por_etapas/resultados/ETAPA-{h["stage"]}.md); consultar alcance y estado, sin inferir ejecución' if stage and stage.exists() else 'Consultar estado general; sin evidencia atribuida automáticamente'
        cases=indexed.get(cid,[]);explicit=[t['execution_evidence'] for t in cases if t.get('execution_evidence')]
        if explicit:evidence+='; '+ '; '.join(dict.fromkeys(explicit))
        anchor=cid.replace('/','-') if not cid.startswith('J-CA') else 'contrato-PROP-E00-HU-02'
        links=', '.join(f'[{t["id"]}](08_Historias_de_Usuario.md#{t["id"]})' for t in cases)
        states='; '.join(dict.fromkeys(t['state'] for t in cases))
        lines.append(f'| [{cid}](08_Historias_de_Usuario.md#{anchor}) | {scope} | {links} | {evidence} | {states} |')
    lines+=['','## Índice de casos con datos y resultados','','| Caso | Propósito | Detalle completo |','|---|---|---|']
    for t in tests:lines.append(f'| {t["id"]} | {t["title"]} | [Pasos, datos y resultado esperado](08_Historias_de_Usuario.md#{t["id"]}) |')
    lines+=['','## Registro de ejecución requerido','','El estado anterior copia la declaración de08 y no es certificación del generador. Los resultados se conservan en evidencia fechada por caso/criterio, build/hash, rol, fixture, versión del motor, herramienta/capa, esperado, observado y limitaciones. Si se declara ejecución en una ficha, añadir **Evidencia de ejecución:** con referencia precisa; sin ella el validador rechaza la declaración. Una etapa pendiente puede tener un archivo de preparación: su existencia no prueba ejecución. Para inspección inversa registrar literal/ruta/estado y requisito. NO EXAMINADO y NO EJECUTADO no equivalen a defecto ni cumplimiento.']
    outputs[ROOT/'03_Matriz_de_Trazabilidad_y_Pruebas.md']='\n'.join(lines)
    outputs[HERE/'INDICE_DERIVADO.json']=json.dumps(dict(source=SOURCE.name,source_sha256=digest,stories=hs,tests=tests,criteria=criteria,counts=n,generated=True,authority='08 exclusivamente; este JSON es derivado'),ensure_ascii=False,indent=2)
    for p,txt in outputs.items():write(p,txt)
    return dict(hu=len(hs),criteria=len(criteria),cases=len(tests),sp=n['fibonacci_catalog'],selected_sp=n['fibonacci_selected'])
if __name__=='__main__':print(json.dumps(generate(),ensure_ascii=False))
