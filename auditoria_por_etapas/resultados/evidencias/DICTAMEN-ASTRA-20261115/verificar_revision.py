"""Solo evidencia: hashes y contraejemplos en memoria; no importa Django ni abre DB."""
from pathlib import Path
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
DOCS = ['08_Historias_de_Usuario.md', '02_Diseno_Tecnico_R1_PMV.md',
        '16_Task_Breakdown.md', '07_Reglas_de_Negocio.md',
        '09_Product_Backlog.md', '03_Matriz_de_Trazabilidad_y_Pruebas.md',
        'auditoria_por_etapas/PROTOCOLO_COMUN.md',
        'auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md',
        'auditoria_por_etapas/resultados/ESTADO_GENERAL.md',
        'auditoria_por_etapas/OBJETIVO_Y_CRITERIOS_DE_ENTREGA.md',
        'auditoria_por_etapas/PAGOS_YAPE_Y_MIXTOS.md',
        'auditoria_por_etapas/resultados/DECISION-PAGOS-SIN-COMISION.md',
        'auditoria_por_etapas/resultados/REVISION-PROPUESTA-GEMINI-PAGOS.md']

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def snapshot():
    files = {s: sha(ROOT/s) for s in DOCS}
    excluded = {'.git', '.venv', 'venv', '__pycache__', 'evidencias', 'node_modules', '.pytest_cache', 'staticfiles'}
    extensions = {'.py', '.html', '.css', '.js', '.svg', '.json', '.yaml', '.yml', '.txt', '.md', '.toml'}
    for p in (ROOT/'r1-pmv').rglob('*'):
        if not p.is_file() or any(x in excluded for x in p.relative_to(ROOT/'r1-pmv').parts):
            continue
        if p.suffix in extensions or p.name in {'Dockerfile', '.env.example', '.gitignore', '.dockerignore', 'r1_pmv.sqlite3'}:
            files[p.relative_to(ROOT).as_posix()] = sha(p)
    product = {k:v for k,v in files.items() if k.startswith('r1-pmv/') and not k.endswith('.sqlite3')}
    manifest_hash = hashlib.sha256(json.dumps(product,sort_keys=True).encode()).hexdigest()
    git = lambda *args: subprocess.check_output(['git','-C',str(ROOT/'r1-pmv'),*args],text=True).strip()
    return {'time_utc':datetime.now(timezone.utc).isoformat(),'date_lima':'2026-11-15',
            'scope':'Hashes de archivos, sin abrir DB; no suite funcional',
            'head':git('rev-parse','HEAD'),'git_status':git('status','--porcelain'),
            'product_manifest_sha256':manifest_hash,'product_files':len(product),'files':files}

def write(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if sys.argv[1] == 'baseline':
    before = OUT/'antes.json'
    if before.exists():
        raise SystemExit('No sobrescribir evidencia inicial')
    s=snapshot();write('antes.json',s)
    print(json.dumps({k:s[k] for k in ['head','product_manifest_sha256','product_files']},indent=2))
elif sys.argv[1] == 'modelos':
    # Contraejemplo exacto del algoritmo descrito por Gemini, no del producto.
    active=[{'order':'B','amount':300}]
    event={'real_order':'A_cancelado','amount':300}
    naive=next(x for x in active if x['amount']==event['amount'])
    assert naive['order'] != event['real_order']
    # Misma descripción visible admite dos orígenes bancarios distintos.
    visible=lambda bank: (bank['amount'],bank['name'],bank['code'],bank['minute'])
    a={'bank_operation':'A','amount':300,'name':'Ana','code':'123','minute':'12:00'}
    b={**a,'bank_operation':'B'}
    assert visible(a)==visible(b) and a['bank_operation']!=b['bank_operation']
    # Retransmisión local y nueva notificación del mismo movimiento son distintos problemas.
    notifications=[{'local':'N1','actual_bank':'X','amount':300},
                   {'local':'N2','actual_bank':'X','amount':300}]
    unique_locals={x['local']:x for x in notifications}
    assert sum(x['amount'] for x in unique_locals.values())==600
    assert sum({x['actual_bank']:x['amount'] for x in notifications}.values())==300
    # Todo reparto a céntimos de una compra de 10, con billete de 20.
    tested=0
    for digital in range(1001):
        total=1000;cash=total-digital;tender=2000;change=tender-cash
        assert cash+digital==total and tender-change==cash and change>=0
        tested+=1
    D=Decimal
    assert D('3.00')+D('7.00')==D('10.00')
    # Contraejemplo de verificar reintegros sin reservar bajo bloqueo.
    balance=1000
    reads=[balance,balance]
    accepted=[700<=v for v in reads]
    assert all(accepted) and 700*2>balance
    write('modelos.json',{'status':'PROBADO: modelos aislados, NO producto ni banco',
        'django_imported':False,'db_opened':False,'network':False,
        'results':[
          {'case':'M01','expected':'Algoritmo por importe asigna A tardío a B','observed':naive['order'],'passes_counterexample':True},
          {'case':'M02','expected':'Nombre/monto/código/minuto no identifican operación universal','same_visible':visible(a),'passes_counterexample':True},
          {'case':'M03','expected':'Dos IDs locales pueden duplicar un solo abono','naive_cents':600,'real_cents':300,'passes_counterexample':True},
          {'case':'M04','expected':'E+Y=T; R-vuelto=E','splits_checked':tested,'passed':True},
          {'case':'M05','expected':'3+7=10 con Decimal','passed':True},
          {'case':'M06','expected':'Dos lecturas antes de reservar permiten 14 sobre saldo10','naive_accepted':accepted,'passes_counterexample':True}],
        'limits':'No demuestra frecuencia de colisión, campos reales Yape, autenticidad, rendimiento, locks PostgreSQL ni seguridad del producto.'})
    print('6 modelos comprobados; 1001 repartos exactos; ninguna prueba de producto o banco.')
elif sys.argv[1] == 'final':
    a=json.loads((OUT/'antes.json').read_text(encoding='utf-8'));b=snapshot()
    changed=[k for k in sorted(set(a['files'])|set(b['files'])) if a['files'].get(k)!=b['files'].get(k)]
    write('validacion.json',{'time_utc':b['time_utc'],'files_compared':len(a['files']),
        'protected_unchanged':not changed,'changes':changed,'head':b['head'],
        'product_manifest_sha256':b['product_manifest_sha256'],
        'git_status_unchanged':a['git_status']==b['git_status'],
        'report_sha256':sha(ROOT/'auditoria_por_etapas/resultados/DICTAMEN-PAGOS-ASTRA.md'),
        'no_functional_tests':True,'no_transfers':True,'no_deployment':True})
    print(json.dumps({'protected_unchanged':not changed,'changes':changed},indent=2))
