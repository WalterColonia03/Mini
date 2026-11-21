"""Verify preserved evidence and regenerate planning; no business writes or DB access."""
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import audit13b_planificacion as planning

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / 'auditoria_por_etapas/resultados'
OUT = RESULTS / 'evidencias/13-B-final-20261113'
planning.EVIDENCIA = OUT / 'planificacion'

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(name, result):
    with (OUT / name).open('x', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

def verify():
    base = read(OUT / 'baseline.json')
    assert sha(ROOT / 'r1-pmv/identity/views.py') == base['product_files_sha256']['r1-pmv/identity/views.py']
    assert all(sha(ROOT / p) == h for p, h in base['product_files_sha256'].items())
    inherited = {}
    for folder in ['13-B-servidor-20261113T164755068835Z', '13-B-servidor-20261113T164757087079Z']:
        p = OUT.parent / folder / 'results.json'
        data = read(p)
        assert data['passed'] == data['total'] == 100
        assert all(x['status'] == 'CUMPLE' for x in data['results'])
        assert all(sha(ROOT / 'r1-pmv' / f) == h for f, h in data['sha256_files'].items())
        inherited[folder] = {'sha256': sha(p), 'passed': 100, 'code_hashes_match': True, 'source08_at_execution': data['sha256_08']}
    pgpath = OUT.parent / '13-B-PG-20261113T165253183453Z/results.json'
    pg = read(pgpath)
    assert len(pg['cases']) == 37 and all(x['ok'] for x in pg['cases'])
    assert pg['identity_views_sha256'] == sha(ROOT / 'r1-pmv/identity/views.py')
    assert pg['reader_pid'] != pg['writer_pid'] and pg['port_closed']
    inherited[pgpath.parent.name] = {'sha256': sha(pgpath), 'passed': 37, 'code_hash_matches': True, 'source08_at_execution': pg['plan08_sha256'], 'version': pg['postgres_version'], 'isolation': pg['isolation'], 'volume': pg['volume']['total_rows']}
    for folder, name, count in [('13-B-20261113','regresion-final.txt',160),('13-B-PG-20261113T165253183453Z','regression-postgresql.txt',6)]:
        p = OUT.parent / folder / name
        txt = p.read_text(encoding='utf-8-sig')
        assert re.search(r'Ran\s+' + str(count) + r'\s+tests?',txt) and re.search(r'^OK\s*$',txt,re.M)
        inherited[folder+'/'+name] = {'sha256':sha(p),'tests':count,'ok':True}
    before, draft, after, final = [read(OUT / n) for n in ['B02-before.json','B02-draft.json','B02-after-reload.json','B03-final-sin-mutacion.json']]
    assert before['sales'] == draft['sales'] and len(before['sales']) == 5
    assert before['integration_lots'] == draft['integration_lots'] and draft['integration_lots'][0]['available_quantity'] == 3
    assert draft['draft_lines'][0]['quantity'] == 2 and draft['draft_lines'][0]['unit_price'] == 3.55
    new = [s for s in after['sales'] if s['id'] not in {b['id'] for b in before['sales']}]
    assert len(new) == 1 and (new[0]['total_amount'],new[0]['cash_received'],new[0]['change_given']) == (7.1,10,2.9)
    assert after['integration_lots'][0]['available_quantity'] == 1
    assert after['business_sha256'] == final['business_sha256']
    assert all(v == 0 for v in read(OUT / 'B03-vacio-final.json')['counts'].values())
    for name in ['N04-teclado.json','N05-teclado.json','N06-historial-teclado.json']:
        d = read(OUT / name)
        assert d['viewport'] == 390 and d['documentWidth'] <= 390 and d['focused'] and d['scrollLeft'] > 0 and d['outline'] == 'solid'
    evidence = dict(at_utc=datetime.now(timezone.utc).isoformat(), pasada=1, sublote='13-B-final',
        product_build_sha256=base['product_build_sha256'], source08_browser=base['source08_sha256'],
        product_files_unchanged=len(base['product_files_sha256']), inherited_evidence=inherited,
        ui_integration=dict(fixture=before['fixture'],fixture_day_lima=before['fixture_day_lima'],draft_no_sales_or_stock_mutation=True,new_sales=1,total='7.10',received='10.00',change='2.90',lot_before=3,lot_after=1,reloads_errors_denials_business_hash_unchanged=True),
        empty_all_business_tables_zero=True,keyboard_three_tables_390=True,
        note='Evidence verification, not a new execution of inherited tests. Counts overlap. Browser actions documented in DOM/screenshots and narrative; DB witnesses do not substitute them.')
    save('validacion-evidencia.json', evidence)
    print(json.dumps(evidence,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    if sys.argv[1] == 'prepare':
        planning.preparar()
        with zipfile.ZipFile(OUT/'informes-antes.zip','x',zipfile.ZIP_DEFLATED) as z:
            for rel in ['ETAPA-13.md','ESTADO_GENERAL.md','soporte/13-B-disposiciones.md','soporte/13-B-navegador.md','soporte/13-B-servidor.md','soporte/13-B-postgresql.md']:
                z.write(RESULTS/rel,rel)
    elif sys.argv[1] == 'verify':
        verify()
    elif sys.argv[1] in ['regenerate','planning']:
        result = planning.verificar(sys.argv[1]=='regenerate')
        result['sublote'] = '13-B-final'
        if sys.argv[1]=='regenerate': save('planificacion/validacion.json',result)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        assert result['correcto']
    elif sys.argv[1] == 'index':
        files = {p.relative_to(OUT).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size,saved_mtime_utc=datetime.fromtimestamp(p.stat().st_mtime,timezone.utc).isoformat()) for p in sorted(OUT.rglob('*')) if p.is_file()}
        save('indice.json',dict(at_utc=datetime.now(timezone.utc).isoformat(),pasada=1,sublote='13-B-final',files=files,note='mtime is filesystem save time, not inferred browser observation time. Explicit .meta.json has observation metadata where present. Index excludes itself.'))
        print(json.dumps({'files':len(files),'dom_files':len(list(OUT.glob('[VEIFNPZ]*.txt'))),'screenshots':len(list(OUT.glob('*.jpg')))}))
