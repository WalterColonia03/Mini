"""Construcción inicial revisable desde snapshot. No ejecuta ni modifica el producto.
Tras publicar, 08 es la fuente editable; este importador NO debe volver a ejecutarse.
"""
from pathlib import Path
import hashlib,json,re
from escenarios import CASES
from suplementarios import SUPPS,VISIBLE
from redaccion import preparar
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BASE=HERE/'BASELINE'
OLD=ROOT/'auditoria_por_etapas/resultados/conciliacion_20261112'
MARK='FUENTE-PRINCIPAL-20261112'
def read(p):return p.read_text(encoding='utf-8-sig')
def write(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s.rstrip()+'\n',encoding='utf-8')
if MARK in read(ROOT/'08_Historias_de_Usuario.md'):
    raise SystemExit('Importación ya publicada. Editar 08 y regenerar solo vistas; no sobrescribir fuente vigente.')
hu_text=read(BASE/'08_Historias_de_Usuario.md')
rn=read(BASE/'07_Reglas_de_Negocio.md').split('## 7.1',1)[1]
rn='## 7.1'+rn
rn=rn.replace('PROP-03C-LIMITES aceptada por el usuario el 10/11/2026','PROP-03C-LIMITES ratificada por delegación expresa el 12/11/2026; no se atribuye aceptación al «continúa» anterior')
rn=rn.replace('En Sprint 1, los ingresos posteriores','En R1 de consolidación, los ingresos posteriores')
rn=rn.replace('cuando se implemente `HU-VEN-05b`','conforme a `HU-VEN-05b`, seleccionada para R1 de consolidación')
rn=rn.replace('Esto permite calcular margen bruto histórico según el costo registrado, sin sustituirlo por promedios de compras posteriores.', 'Esto permite preparar un cálculo de margen comercial histórico sin sustituir el costo por promedios de compras posteriores. HU-REP-07 solo puede calcular un margen monetario cuando ingresos y costos tienen una base comparable documentada; si se desconoce el tratamiento del costo frente al IGV, informa «Margen no calculable con los datos disponibles». La política tributaria del costo requiere investigación antes de seleccionar ese reporte futuro.')
rn=rn.replace('Si el producto se encuentra en buen estado, regresa a las existencias disponibles para volver a venderse.', 'Si el producto se encuentra en buen estado y sigue vigente, regresa a su lote original como existencia vendible; estar íntegro no vuelve vendible un lote vencido. El destino del vencido y la evidencia de devolución se refinan antes de seleccionar esta función futura.')
rn=rn.replace('si está en buen estado, regresa a las existencias vendibles con prioridad de salida según vencimiento;', 'si está en buen estado y sigue vigente, regresa a su lote original como existencia vendible;')
rn=rn.replace('esta situación permite', 'esta situación permite')
rn=rn.replace('Esta situación permite al administrador ejecutar el cierre forzado de la caja para que otro vendedor pueda abrir su turno de trabajo.', 'En la funcionalidad futura HU-CAJA-07, esta situación habilita revisión administrativa y un cierre forzado trazable. Si no existe arqueo físico, contado y diferencia quedan «No declarado»: nunca se inventa un cuadre. El cierre original es irreversible; la aprobación futura HU-CAJA-06 agrega revisión y observación sin alterar importes ni reabrirlo.')
rn=rn.replace('El detalle verificable aceptado de recepción/lotes, inventario, identidad, permisos, bloqueos, seguridad y consultas reside en ENCARGOS.md, enlazado al comienzo.', 'El detalle verificable aceptado de recepción/lotes, inventario, identidad, permisos, bloqueos, seguridad y consultas reside en el anexo de contratos de la fuente principal 08. ENCARGOS conserva procedencia histórica y remite a esa fuente.')
rn=re.sub(r'^### (RN-\d+) ·',lambda m:f'<a id="{m[1]}"></a>\n\n### {m[1]} ·',rn,flags=re.M)
backlog=[]
for line in read(BASE/'09_Product_Backlog.md').splitlines():
    if re.match(r'^\| \d+ \| HU-',line):
        c=[x.strip() for x in line.split('|')[1:-1]]
        backlog.append(dict(order=int(c[0]),id=c[1],title=c[2],selected=c[3]=='R1 consolidación',stage=c[4],old_sp=int(c[5]),dependency=c[6]))
bm={h['id']:h for h in backlog}
should={'HU-USR-01','HU-CAT-01','HU-CAT-02','HU-PROV-01','HU-PROV-02','HU-PROV-04'}
new_sizes={'HU-INV-01b':(8,'Identidad propia, correlativo, idempotencia, trazabilidad y concurrencia de recepción.'),'HU-INV-03':(8,'Nuevos lotes por ajuste, valoración, legado y carreras de inventario.'),'HU-INV-04':(8,'Kardex con saldo real, asignaciones de lote, filtros y paginación.'),'HU-VEN-01c':(13,'Venta atómica con asignaciones, snapshots, idempotencia, política de descuentos y concurrencia real.'),'HU-USR-03':(8,'Cambio de rol, reset/desbloqueo explícito, revocación, invariantes y eventos.'),'HU-VEN-01a':(8,'Bloqueo en servidor compartido por pestañas y reautenticación con validación de estado.'),'HU-VEN-02a':(5,'Snapshots de vendedor/caja, orden de líneas y navegación/impresión coherente.'),'HU-VEN-05b':(5,'Propiedad de datos, filtros, totales y paginación estable.')}
epics=[];stories=[]
for em in re.finditer(r'^## 8\.[1-5] (EPIC-[A-Z]+) — (.*?) \(.*?\)\n(.*?)(?=^## 8\.|\Z)',hu_text,re.M|re.S):
    epic={'id':em[1],'title':em[2]};epics.append(epic)
    for m in re.finditer(r'^### (HU-[^ ]+) · (.*?)\n(.*?)(?=^### |\Z)',em[3],re.M|re.S):
        ident,title,body=m.groups(); h=dict(bm[ident]);h.update(epic=em[1],description=re.search(r'^- \*\*Historia:\*\* (.*)$',body,re.M)[1],rules=re.search(r'^- \*\*Reglas de negocio:\*\* (.*)$',body,re.M)[1])
        h['criteria']=[dict(id=f'{ident}/CA-{int(n):02}',text=t) for n,t in re.findall(r'^  (\d+)\. (.*)$',body,re.M)]
        h['priority']='W' if not h['selected'] else 'S' if ident in should else 'C' if ident=='HU-PROD-03' else 'M'
        h['sp'],h['size_reason']=new_sizes.get(ident,(h['old_sp'],'Se conserva tamaño previo como referencia orientativa; no mide trabajo restante.'))
        h['supplements']=[k for k,v in SUPPS.items() if ident in v['hus']]
        h['cases']=CASES[ident]
        stories.append(h)
assert len(stories)==74
byid={h['id']:h for h in stories}
def criterion(hu,n,text):byid[hu]['criteria'][n-1]['text']=text
for c in byid['HU-PROD-04']['criteria']:
    c['text']=c['text'].replace('aceptada el 10/11/2026','ratificada por delegación el 12/11/2026').replace('aceptada por el usuario el 10/11/2026','ratificada por delegación el 12/11/2026')
criterion('HU-PROV-04',1,'Dado un proveedor activo, cuando ADMIN revisa y confirma su desactivación, entonces deja de estar disponible para nuevas recepciones directas; un formulario antiguo que aún lo seleccione se rechaza sin ingresar stock. La historia conserva su identidad y datos conocidos. La elegibilidad de solicitudes SOL se aplicará cuando esa función futura sea seleccionada.')
criterion('HU-PROV-04',2,'Dado un proveedor inactivo, cuando ADMIN revisa y confirma su reactivación, entonces vuelve a estar disponible para nuevas recepciones sin alterar sus registros históricos ni otros proveedores. Las solicitudes SOL siguen futuras.')
criterion('HU-CAJA-06',1,'Dado un turno cerrado, cuando ADMIN revisa y aprueba el cierre, entonces registra el estado de revisión Aprobado, autor e instante sin modificar el cierre original, sus importes ni su condición irreversible; no reabre el turno.')
criterion('HU-CAJA-06',2,'Dado un cierre con sobrante o faltante, cuando ADMIN lo aprueba, entonces exige y conserva una observación de revisión junto con la diferencia original, sin convertirla artificialmente en cero.')
criterion('HU-CAJA-07',2,'Dado un turno elegible por inactividad, cuando ADMIN confirma su cierre forzado con motivo, entonces registra cierre administrativo, ventas acumuladas y autor y libera la caja sin inventar un arqueo; si no se contó efectivo, el contado y la diferencia se indican como No declarado. La política de borradores y carreras se refina antes de seleccionar esta función futura.')
criterion('HU-VEN-02a',3,'Dado que la constancia se visualiza o imprime, cuando se lee, entonces exhibe «CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO», sin logotipos ni leyendas de aprobación SUNAT y sin afirmar que ya se emitió o entregó una boleta/factura externa. El canal autorizado real se debe confirmar antes del piloto (RN-26).')
byid['HU-REP-07']['description']='Como dueño de la bodega, quiero consultar el margen comercial de las ventas con costo histórico conocido y base comparable documentada, para analizar la mercadería sin confundir esa medida con la rentabilidad neta del negocio.'
criterion('HU-REP-07',1,'Dado un conjunto de ventas con precio neto sin IGV y costo histórico cuya base comparable está documentada, cuando ADMIN consulta el reporte, entonces presenta ingresos netos, costo conservado y ganancia comercial; si falta costo o su base comparable, identifica la exclusión y no calcula una ganancia ficticia (RN-27, RN-28).')
criterion('HU-REP-07',2,'Dado un conjunto con datos comparables conocidos, cuando se calcula el margen, entonces muestra ganancia/ingreso neto ×100, con denominador y cobertura explícitos; si el ingreso neto es cero o faltan datos, indica No calculable, sin presentar el resultado como rentabilidad neta ni certificación fiscal.')
criterion('HU-VEN-06c',1,'Dadas unidades devueltas íntegras y todavía vigentes, cuando se confirma una anulación autorizada, entonces regresan al lote original identificado en la venta; las vencidas nunca se ofrecen como vendibles. El destino de devoluciones vencidas y los requisitos de evidencia se refinan antes de seleccionar esta función futura (RN-09).')
contracts_text=read(BASE/'auditoria_por_etapas/resultados/conciliacion_20261112/ENCARGOS.md')
contracts={}
for m in re.finditer(r'^## ([A-Z][A-Z0-9-]+) · (.*?)\n(.*?)(?=^## |\Z)',contracts_text,re.M|re.S):
    contracts[m[1]]={'id':m[1],'title':m[2],'body':m[3].strip(),'criteria':[dict(id=f'{m[1]}/{n}',text=t) for n,t in re.findall(r'^\*\*(C-\d+)\.\*\* (.*)$',m[3],re.M)]}
assert sum(len(v['criteria']) for v in contracts.values())==60
contracts['DOC-00-01']['body']=contracts['DOC-00-01']['body'].replace('La lista exacta está en09.', 'La selección, prioridad y tamaño orientativo están en las fichas de esta fuente08;09 es una vista derivada.')
clean=preparar(hu_text+'\n'+rn)
tests=[]
for h in stories:
    for i,c in enumerate(h['cases'],1):
        c['id']=f"CP-{h['id']}-{i:03}"
        c['covers']=[f"{h['id']}/CA-{x:02}" for x in c['criteria']]
        for key in ('title','preconditions','data','expected'):c[key]=clean(c[key])
        c['steps']=[clean(x) for x in c['steps']]
        c['hu']=h['id'];c['scope']='R1' if h['selected'] else 'FUTURO'
        tests.append(c)
for key,v in SUPPS.items():
    covers=[c['id'] for c in contracts[key]['criteria']] if key in contracts else [f'J-CA{i}' for i in range(1,5)]
    tests.append(dict(id=f'CP-{key}-001',title=f'Contrato {key}',hu=', '.join(v['hus']),scope='TRANSVERSAL',covers=covers,preconditions='F-BASE aislada; restaurar cada variante. Roles y estados indicados. Concurrencia solo en PostgreSQL con conexiones independientes.',data=v['data'],steps=v['steps'],expected=v['expected']))
for i,(ident,title,data,steps,expected) in enumerate(VISIBLE,1):
    tests.append(dict(id=ident,title=title,hu='Todas las HU seleccionadas y toda superficie visible',scope='TRANSVERSAL',covers=[f'CT-COHERENCIA-UI/C-{i:02}'],preconditions='Build identificado; datos ficticios aislados; inventario por rol, ruta y estado.',data=data,steps=steps,expected=expected))
def linkhu(ident):return f'[{ident}](#{ident})'
def render_case(c):
    return '\n'.join([f'<a id="{c["id"]}"></a>',f'##### {c["id"]} · {c["title"]}','',f'**Cubre:** {", ".join(c["covers"])}. **Estado:** DISEÑADO — NO EJECUTADO en este corte.',f'**Precondiciones:** {c["preconditions"]}',f'**Datos de prueba:** {c["data"]}','',*[(f'{i}. {step}') for i,step in enumerate(c['steps'],1)],'',f'**Resultados esperados:** {c["expected"]}',''])
def counts(items):return len(items),sum(x['sp'] for x in items)
header=f'''# Planificación principal del minimarket

<!-- {MARK} -->

**Corte: 12/11/2026. Autoridad funcional: este archivo08.** La planificación define el comportamiento esperado; código, interfaz y auditorías aportan evidencia de lo que ocurre. Una implementación existente no aprueba un requisito. Los documentos07/09/03 son vistas derivadas;01/02/14/16/20/21 describen contexto, diseño, ejecución y diferencias y deben ajustarse a esta fuente. No resuelven contradicciones alterando silenciosamente este contrato.

La decisión **DEC-FUENTE-UNICA-20261112** está ACEPTADA por instrucción expresa: unificar épicas, historias, prioridad MoSCoW, tamaño Fibonacci, descripción, criterios, casos escritos, datos y resultados esperados; auditar también cada promesa visible. Alcance:74 HU,33 seleccionadas para R1 y41 futuras;8 ideas excluidas. La aceptación documental no autoriza implementación del producto ni cambia estados históricos de auditoría.

## Cómo leer y mantener esta fuente

- Una ficha define cada HU y conserva sus identificadores. Los219 CA base se completan con60 criterios de contratos y4 criteriosJ de categorías; CT-COHERENCIA-UI añade4 criterios transversales de veracidad visible. No son287 casos ejecutados.
- **PROPUESTA → ACEPTADA → IMPLEMENTADA → VERIFICADA.** Las33 HU seleccionadas tienen especificación aceptada por delegación; los cambios requieren implementación autorizada y evidencia propia. Las41 futuras mantienen criterios para refinamiento, no un compromiso de entrega ni aprobación de seguridad de todos sus detalles históricos.
- MoSCoW se aplica al horizonte R1: **M** obligatorio para el incremento coherente; **S** conveniente; **C** opcional por valor relativo; **W** fuera de este horizonte. Una función seleccionada/visible debe cumplir todos sus criterios aunque seaS/C; diferirla exige cambio explícito de alcance y retirar promesas engañosas.
- Puntos Fibonacci1/2/3/5/8/13 expresan tamaño relativo orientativo de la HU completa. Son propuesta de dimensionamiento del asesor; el equipo que implemente debe refinarlos. No equivalen a horas, trabajo restante, velocidad o compromiso de Sprint. Se conservan SP anteriores como procedencia. Las futuras mantienen tamaño histórico provisional.
- Antes de cambiar una ficha: registrar motivo, fuente y decisión; actualizar RN/contratos relacionados, casos, vistas derivadas, tareas y evidencia afectada. Una contradicción es un hallazgo hasta resolverla con trazabilidad; no se reduce el requisito para acomodar un defecto.
- Un caso escrito indica cómo verificar; no demuestra que se ejecutó. La evidencia previa434/434 en SQLite y la muestraPG18.4 se conservan con sus límites en [VERIFICACION](auditoria_por_etapas/resultados/conciliacion_20261112/VERIFICACION.md). No verifican por sí solas los nuevos contratos ni toda la interfaz.

## Índice de épicas y dimensionamiento

| Épica | Objetivo | HU | R1 | Futuras | SP orientativos catálogo | SP R1 |
|---|---|---:|---:|---:|---:|---:|
'''
for e in epics:
    hs=[h for h in stories if h['epic']==e['id']];selected=[h for h in hs if h['selected']]
    header+=f'| [{e["id"]}](#{e["id"]}) | {e["title"]} | {len(hs)} | {len(selected)} | {len(hs)-len(selected)} | {sum(h["sp"] for h in hs)} | {sum(h["sp"] for h in selected)} |\n'
header+=f'\nTotal:74 HU/{sum(h["sp"] for h in stories)} SP orientativos; R1:{sum(h["sp"] for h in stories if h["selected"])} SP. Referencia anterior:231 SP. Ninguno de estos totales representa un Sprint comprometido.\n'
header+='''
## Datos comunes y método de prueba

**F-BASE.** Base nueva y aislada por caso; fecha controlada12/11/2026 en America/Lima. Roles ficticios: ADMIN, ALMACENERO, vendedorA, vendedorB y cuenta inactiva. Correos del dominio reservado `pruebas.invalid`; contraseñas ficticias de RN-24, sin reutilizar secretos reales. Cada variante restaura el estado descrito; no se encadenan pruebas sin indicarlo.

Lácteos activa; Leche1L activa, código INT-LECHE-1, UND, precio S/10.00, mínimo10, vencimiento obligatorio. LoteA:10 unidades a2.0000, vence13/11/2026; loteB:10 a4.0000, vence12/12/2026; físico/vendible20, promedio3.0000. Arroz:5 unidades a2.0000, precio5.00, mínimo10, lote vigente. Los casos que requieren producto sin carga eliminan esa preparación únicamente en su clon. CAJA-01 comienza sin turno salvo que el caso requiera A abierto con S/100.00.

**F-COSTO** sustituye el estado de Leche: físico18, promedio3, ocho unidades vencidas pendientes de baja y diez vigentes; proviene de una carga20 y venta2 anterior al vencimiento. No agrega vencidos invisiblemente a F-BASE. Los lotesE y datos de informes son variantes explícitas, no cambios a la fórmula base. Los días futuros usados en pruebas son datos sintéticos con reloj controlado.

Para cada rechazo comparar antes/después: actor/sesión, borrador, producto, lotes, promedio, recepciones, ventas/detalles/asignaciones, correlativos, movimientos y turno, según alcance. UnHTTP400/403 no basta. En concurrencia registrar conexiones independientes, barrera que pruebe solapamiento, resultado serial permitido y ausencia de mutaciones parciales; SQLite no demuestra locks de PostgreSQL. En interfaz usar navegador real y evidencia sanitizada por rol/estado; Django Client no acredita una prueba visual.

Los númerosRUC son ficticios para probar formato, no identidad de empresa ni validación SUNAT. El fixture de margen con costo comparable es un supuesto de prueba explícito; no resuelve la política tributaria real.

## Fichas de historias
'''
parts=[header]
for e in epics:
    parts.extend([f'<a id="{e["id"]}"></a>',f'## {e["id"]} · {e["title"]}',''])
    for h in (h for h in stories if h['epic']==e['id']):
        parts.extend([f'<a id="{h["id"]}"></a>',f'### {h["id"]} · {h["title"]}','',f'**Épica:** {h["epic"]}. **Prioridad MoSCoW:** {h["priority"]}. **Puntos Fibonacci:** {h["sp"]} (orientativos; anteriores:{h["old_sp"]}).',f'**Alcance:** {"R1 seleccionado; especificación ACEPTADA" if h["selected"] else "FUTURO; W en R1; requiere refinamiento antes de seleccionarse"}. **Implementación/verificación:** ver evidencia por criterio; no se presume completa.',f'**Descripción de la HU:** {h["description"]}',f'**Reglas relacionadas:** {h["rules"]}. **Dependencias funcionales:** {h["dependency"]}.',f'**Estimación:** {h["size_reason"]}',f'**Procedencia:** ETAPA-{h["stage"]}; ficha anterior preservada en [snapshot](auditoria_por_etapas/resultados/fuente_unica_20261112/BASELINE/08_Historias_de_Usuario.md). Las etapas13–16 no cuentan con informe de ejecución completo en el inventario.',f'**Contratos complementarios:** {", ".join(f"[{k}](#contrato-{k})" for k in h["supplements"]) or "Condiciones comunes y CT-COHERENCIA-UI"}.','', '#### Criterios de aceptación',''])
        for c in h['criteria']:parts.extend([f'<a id="{c["id"].replace("/","-")}"></a>',f'**{c["id"]}.** {c["text"]}',''])
        parts.append('#### Casos de prueba escritos\n')
        parts.extend(render_case(c) for c in h['cases'])
parts+=['<a id="reglas"></a>','## Anexo normativo · Reglas de negocio','',rn,'<a id="contratos"></a>','## Anexo normativo · Decisiones y encargos implementables','']
common=contracts_text.split('## Condiciones comunes para todos los cambios seleccionados',1)[1].split('## DOC-03AB-01',1)[0]
parts+=['### Condiciones comunes',common,'Cada contrato conserva ID, justificación, alcance/excepciones, dependencias, requisitos, migración y criterios verificables. Estado de decisión: ACEPTADA por delegación12/11; implementación de cambios PENDIENTE DE AUTORIZACIÓN SEPARADA; verificación de esos cambios NO EJECUTADA. CT-ROLLBACK es investigación/prueba pendiente, no defecto demostrado.']
for key,c in contracts.items():
    body=c['body'].replace('ENCARGOS/', 'contratos/').replace('este registro','esta fuente principal')
    body=re.sub(r'^\*\*(C-\d+)\.\*\*',lambda m:f'<a id="{key}-{m[1]}"></a>\n\n**{key}/{m[1]}.**',body,flags=re.M)
    parts.extend([f'<a id="contrato-{key}"></a>',f'### {key} · {c["title"]}','',body,'',render_case(next(t for t in tests if t['id']==f'CP-{key}-001'))])
parts+=['<a id="contrato-PROP-E00-HU-02"></a>','### PROP-E00-HU-02 · Ciclo de vida de categorías','',hu_text.split('## Cambio de estado de una categoría',1)[1].split('\n',1)[1],render_case(next(t for t in tests if t['id']=='CP-PROP-E00-HU-02-001'))]
parts+=['<a id="contrato-CT-COHERENCIA-UI"></a>','## CT-COHERENCIA-UI · Toda promesa visible es auditable','', 'Requisito ACEPTADO por instrucción expresa del usuario. Aplica a las páginas y estados alcanzables, mensajes, etiquetas, tablas, ayudas, botones, menús, impresión y resultados que pueda leer cada rol. Una frase equivocada se corrige junto con su comportamiento según el requisito aceptado. Si no existe requisito, se registra extra o contradicción y se define su tratamiento; no se toma el texto implementado como aprobación comercial.']
for c in (t for t in tests if t['id'].startswith('CP-VISIBLE-')):
    cid=c['covers'][0];parts += [f'<a id="{cid.replace("/","-")}"></a>',f'**{cid}.** Dada la superficie y los estados descritos en {c["id"]}, cuando se revisan desde cada rol, entonces {c["expected"][0].lower()+c["expected"][1:]}','',render_case(c)]
outside=hu_text.split('## 8.6 Ideas fuera del horizonte académico',1)[1].split('---',1)[0]
outside=outside.replace('Los comprobantes de pago autorizados con valor tributario se emiten por el canal externo habitual de la bodega.', 'Emisión fiscal fuera del sistema; canal real/aplicabilidad por confirmar antes del piloto, sin dar por cierta una operación externa.')
outside=outside.replace('La facturación electrónica con RUC se gestiona por el canal autorizado externo.', 'Emisión fiscal fuera del sistema; canal real y aplicabilidad requieren confirmación.')
parts+=['<a id="fuera"></a>','## Ideas excluidas y asuntos que requieren refinamiento',outside,'Las ocho ideas son W, sin puntos ni casos operativos comprometidos: no constituyen HU listas para desarrollo. Conservar sus IDs no exige inventar estimaciones o cumplimiento. AUTH05 (seguridad del código), CAJA07 (borradores/arqueo), VEN06 (devolución/reembolso) y REP07 (base comparable del costo) requieren refinamiento específico; sus casos son especificación futura acotada, no una certificación de preparación.','', '## Evidencia, discrepancias y siguiente trabajo','', 'El [mapa consolidado](auditoria_por_etapas/resultados/conciliacion_20261112/CONSOLIDACION.md) conserva clasificación A/B/C/D/E, prioridad, estado, fuente y dependencias; el [índice de IDs](auditoria_por_etapas/resultados/conciliacion_20261112/INDICE_IDS.md) mantiene trazabilidad histórica. La [conciliación de este corte](auditoria_por_etapas/resultados/fuente_unica_20261112/REVISION.md) registra cambios y límites. Las divergencias comprobadas de promedio, recepción, merma y modelo de venta siguen abiertas hasta implementación y verificación. No se declara cerrado ningún módulo.','', '## Técnicas de planificación','', 'MoSCoW y Fibonacci son técnicas elegidas para este proyecto, no mandatos de Scrum. [Agile Business Consortium: MoSCoW](https://www.agilebusiness.org/resource/what-is-moscow-prioritization/) define prioridades respecto a un horizonte; [Scrum Guide](https://scrumguides.org/scrum-guide.html) atribuye el dimensionamiento a quienes realizan el trabajo. Por eso estas cifras son orientativas hasta refinamiento con el equipo.']
write(ROOT/'08_Historias_de_Usuario.md','\n\n'.join(parts))
data={'date':'2026-11-12','source':'08_Historias_de_Usuario.md','epics':epics,'stories':stories,'contracts':contracts,'tests':tests}
write(HERE/'INDICE_DERIVADO.json',json.dumps(data,ensure_ascii=False,indent=2))
print(json.dumps({'stories':len(stories),'base_criteria':sum(len(h['criteria']) for h in stories),'tests':len(tests),'supplemental':60,'category':4,'visible':4},ensure_ascii=False))
