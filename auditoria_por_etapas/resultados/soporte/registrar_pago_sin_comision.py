"""Apply the user's cost decision to active documentation; no product changes."""
from pathlib import Path
import hashlib
import importlib.util
import json

ROOT=Path(__file__).resolve().parents[3]
AUD=ROOT/'auditoria_por_etapas'
OUT=AUD/'resultados/evidencias/PAY-SIN-COMISION-20261115'
OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
roots=['00_LEEME_PLANIFICACION.md','01_Proyecto_y_Releases.md','02_Diseno_Tecnico_R1_PMV.md','08_Historias_de_Usuario.md',
       '14_Sprint_Planning.md','16_Task_Breakdown.md','21_Alcance_Actual_y_Diferencias.md',
       '07_Reglas_de_Negocio.md','09_Product_Backlog.md','03_Matriz_de_Trazabilidad_y_Pruebas.md']
names=roots+[str(p.relative_to(ROOT)).replace('\\','/') for p in sorted(AUD.glob('[0-9][0-9]_*.md'))]
names += ['auditoria_por_etapas/'+n for n in ['LEEME.md','PROTOCOLO_COMUN.md','CONTINUIDAD_Y_SEGUNDA_PASADA.md','OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md','PAGOS_YAPE_Y_MIXTOS.md']]
names += ['auditoria_por_etapas/resultados/ESTADO_GENERAL.md','auditoria_por_etapas/resultados/fuente_unica_20261112/INDICE_DERIVADO.json']
assert not (OUT/'fuentes-antes.json').exists(),'Decision already recorded; do not overwrite history'
before=[]
for n in names:
    p=ROOT/n;dest=OUT/'antes'/n;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
    before.append({'path':n,'sha256':sha(p)})
(OUT/'fuentes-antes.json').write_text(json.dumps(before,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def replace(p,old,new):
    s=p.read_text(encoding='utf-8');assert old in s,f'Expected text missing in {p.name}: {old[:55]}'
    p.write_text(s.replace(old,new),encoding='utf-8')

old='consulta Ayudantes es alternativa a evaluar, no API ni afiliación autorizada.'
new='Yape Empresa/Ayudantes queda descartado por costo: el usuario requiere cero comisión de cobro. Yape común/QR Plin son candidatos de recepción, sin consulta delegada ni API gratuita verificadas.'
for n in roots:
    p=ROOT/n;s=p.read_text(encoding='utf-8')
    if old in s:p.write_text(s.replace(old,new),encoding='utf-8')

p=ROOT/'08_Historias_de_Usuario.md'
replace(p,'El mecanismo independiente para comprobar abonos y la política delegada de reintegros requieren resolución verificable;',
          'El usuario exige cero comisión de cobro y descarta Yape Empresa/Ayudantes por costo. El mecanismo independiente para comprobar abonos y la política delegada de reintegros requieren resolución verificable;')
replace(p,'La modalidad se decide y prueba antes de habilitar dinero real. Yape Empresa/Ayudantes es una alternativa oficial de consulta delegada con costo y requisitos por confirmar para la cuenta; no se contrata por esta regla ni acredita API automática. Una pasarela con notificación verificable es otra alternativa sujeta a afiliación.',
          'La modalidad se decide y prueba antes de habilitar dinero real. Por respuesta expresa del usuario15/11/2026 se exige cero comisión de cobro; Yape Empresa/Ayudantes queda descartado por costo. Yape común y QR Plin interoperable son candidatos de recepción, no canales gratuitos de consulta delegada o API verificados. Una pasarela solo podría seleccionarse si se acreditan costo permitido, elegibilidad y confirmación auténtica; no se infiere gratuidad por tener QR. [Decisión y fuentes](auditoria_por_etapas/resultados/DECISION-PAGOS-SIN-COMISION.md).')
replace(p,'Conciliar cobros brutos, comisiones si aplican y dinero neto por separado, sin descontar una comisión del total pagado por el comprador.',
          'El canal elegido para esta entrega debe recibir el cobro sin comisión; verificarlo para la modalidad exacta, sin confundir comisión de envío con recepción ni con costos de la cuenta. No inventar cargos ni descontarlos del total pagado por el comprador.')
replace(p,'Necesidades ACEPTADAS como objetivo; método de comprobación externa',
          'Necesidades ACEPTADAS como objetivo, incluida cero comisión de cobro por respuesta posterior del15/11/2026; Yape Empresa/Ayudantes descartado. Método de comprobación externa')
replace(p,'vuelto depende solo del efectivo entregado/aplicado y se separan bruto, comisiones y neto cuando existan. No se anuncia validación bancaria automática si la fuente es humana.',
          'vuelto depende solo del efectivo entregado/aplicado y el canal elegido recibe el cobro sin comisión, acreditado con las condiciones vigentes de esa modalidad. No se infiere gratuidad de cuenta o integración ni se anuncia validación bancaria automática si la fuente es humana.')
replace(p,'1. Ejecutar los tres modos; consultar pagos, constancias, historial y cierre; cotejar neto/comisión cuando exista.',
          '1. Verificar condiciones vigentes de cero comisión de cobro del canal elegido, separadas de costos de cuenta/integración; ejecutar los tres modos y consultar pagos, constancias, historial y cierre.')
replace(p,'Ventas80, efectivo aplicado30 y gaveta130, Yape50, vuelto10 en mixto; no duplicación ni mezcla de comisión con deuda del cliente.',
          'Ventas80, efectivo aplicado30 y gaveta130, Yape50, vuelto10 en mixto; no duplicación. Modalidad de recepción sin comisión acreditada; si falta esa evidencia, no aprobar el criterio. No inventar gastos ni una API gratuita.')

replace(ROOT/'02_Diseno_Tecnico_R1_PMV.md','El canal externo sigue pendiente: Ayudantes ofrece consulta humana sin facultad de transferir, no una API conocida.',
        'El canal externo sigue pendiente: Ayudantes está descartado por comisión. QR común/Plin puede resolver recepción sin comisión; no demuestra consulta delegada de solo lectura ni API gratuita. Compartir una sesión bancaria, fijar una pantalla abierta o retransmitir notificaciones no resuelve esa separación de permisos.')
replace(ROOT/'14_Sprint_Planning.md','resolver canal/refenciaYape y política de reintegros;',
        'resolver canal/referencia Yape sin comisión de cobro y política de reintegros;')
replace(ROOT/'16_Task_Breakdown.md','| PAY-CANAL | Fuente legítima sin dueño presente; referencia,permisos,costo,disponibilidad | DECISIÓN PENDIENTE; Ayudantes reduce acceso al dinero, no falsedad en registro; costo no aceptado |',
        '| PAY-CANAL | Fuente legítima sin dueño presente y sin comisión de cobro; referencia, permisos y disponibilidad | Cero comisión ACEPTADO; Ayudantes DESCARTADO. QR común/Plin son candidatos, no verificación delegada o API demostradas; mecanismo pendiente |')

for p in sorted(AUD.glob('[0-9][0-9]_*.md')):
    s=p.read_text(encoding='utf-8')
    marker='No se exige comprar dominio ni inventar una empresa real.'
    assert marker in s
    s=s.replace(marker,marker+' El canal de cobro debe ser sin comisión; Yape Empresa/Ayudantes está descartado por costo. Consultar la decisión vigente en `auditoria_por_etapas/resultados/DECISION-PAGOS-SIN-COMISION.md`; recibir gratis no demuestra consulta delegada ni integración gratuita.')
    s=s.replace('Ayudantes Yape es alternativa pendiente de afiliación/costo y no una API.','Ayudantes Yape está descartado por comisión. QR común/Plin son candidatos de recepción; no hay consulta delegada ni API gratuitas verificadas.')
    s=s.replace('AyudantesYape es alternativa pendiente de afiliación/costo y no unaAPI.','Ayudantes Yape está descartado por comisión. QR común/Plin son candidatos de recepción; no hay consulta delegada ni API gratuitas verificadas.')
    p.write_text(s,encoding='utf-8')

notice='\n\n**Decisión posterior del15/11/2026 — PAY-CANAL-01-SIN-COMISION:** el usuario exige cero comisión de cobro. Yape Empresa/Ayudantes queda descartado por costo. La recepción con QR común/Plin es candidata; no se ha verificado consulta delegada o API gratuita que resuelva la amenaza interna. [Decisión y fuentes](resultados/DECISION-PAGOS-SIN-COMISION.md). El cursor funcional continúa en02-DEMO-TRAZABILIDAD-01.\n'
for n in ['LEEME.md','PROTOCOLO_COMUN.md','CONTINUIDAD_Y_SEGUNDA_PASADA.md']:
    p=AUD/n;s=p.read_text(encoding='utf-8');first,rest=s.split('\n',1);p.write_text(first+notice+'\n'+rest,encoding='utf-8')

p=AUD/'OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md'
s=p.read_text(encoding='utf-8')
line=next(r for r in s.splitlines() if r.startswith('| Yape |'))
s=s.replace(line,'| Yape | Operación sin dueño presente y cero comisión de cobro. Ayudantes descartado por costo. Yape común/QR Plin son candidatos para recibir, sin consulta delegada/API gratuita comprobada. Mecanismo y riesgo residual pendientes; ver [decisión](resultados/DECISION-PAGOS-SIN-COMISION.md) |')
s=s.replace('mediante consulta delegada con permisos limitados o integración verificable.','mediante consulta delegada con permisos limitados o integración verificable, en una modalidad sin comisión de cobro.')
p.write_text(s,encoding='utf-8')
p=AUD/'PAGOS_YAPE_Y_MIXTOS.md';s=p.read_text(encoding='utf-8')
s=s.replace('Se recomienda evaluar consulta delegada mediante Yape Empresa/Ayudantes; disponibilidad, costo y aceptación del riesgo residual siguen pendientes.',
            'El usuario requiere cero comisión de cobro: Yape Empresa/Ayudantes queda descartado. QR Yape común/Plin son candidatos de recepción; consulta delegada, referencia y aceptación del riesgo residual siguen pendientes. Ver [decisión y fuentes](resultados/DECISION-PAGOS-SIN-COMISION.md).')
s=s.replace('## Alternativa sin dueño presente: resultado de investigación','## Investigación anterior y decisión de costo posterior')
s=s.replace('No se ha aceptado costo ni realizado afiliación.','El usuario descartó esta alternativa por costo; no se realizó afiliación.')
s=s.replace('Comisión publicada; entrada manual y riesgo residual de falsedad. RECOMENDADA PARA EVALUAR, no afiliada ni aceptada automáticamente','DESCARTADA por la exigencia de cero comisión; se conserva como antecedente, no recomendación vigente')
s=s.replace('| Integración oficial con proveedor |','| QR Yape común o Plin interoperable | Recepción sin comisión en la modalidad publicada; pagador puede usar Yape | CANDIDATO de recepción. No se verificó consulta delegada/API gratuita ni cuenta del usuario; no dar credenciales al cajero |\n| Integración oficial con proveedor |')
p.write_text(s,encoding='utf-8')
p=AUD/'resultados/ESTADO_GENERAL.md';s=p.read_text(encoding='utf-8')
s=s.replace('(fuente legítima sin dueño; Ayudantes propuesta con costo, noAPI)','(fuente legítima sin dueño y sin comisión; Ayudantes descartado, mecanismo pendiente)')
first,rest=s.split('\n',1)
status='\n\n**Decisión de pago vigente15/11/2026:** cero comisión de cobro ACEPTADO; Yape Empresa/Ayudantes DESCARTADO por el usuario. QR común/Plin solo resuelven recepción candidata; no hay consulta delegada/API gratuita verificada. RN-02 y CT-ENTREGA-ACADEMICA/C-02 actualizados, sin ejecutar producto. [Decisión y fuentes](DECISION-PAGOS-SIN-COMISION.md). El inventario00 anterior conserva su versión; este cambio de costo exige revalidación en11/15/16/17.\n'
p.write_text(first+status+'\n'+rest,encoding='utf-8')

spec=importlib.util.spec_from_file_location('v',AUD/'resultados/fuente_unica_20261112/regenerar_vistas.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
print(json.dumps(m.generate(),ensure_ascii=True))
print('Cost decision recorded; product and previous evidence untouched.')
