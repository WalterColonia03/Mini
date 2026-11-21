"""Read-only witnesses for resumed 13-B; never opens operational databases."""
import hashlib, json, sqlite3, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / 'r1-pmv'
RESULTS = ROOT / 'auditoria_por_etapas/resultados'
OUT = RESULTS / 'evidencias/13-B-final-20261113'
OUT.mkdir(exist_ok=True)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def save(name, data):
    with (OUT / name).open('x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def manifest(name):
    files = {}
    for p in sorted(APP.rglob('*')):
        if not p.is_file() or any(x in p.relative_to(APP).parts for x in ('.git','.venv','__pycache__','evidencias','node_modules')):
            continue
        if p.suffix in {'.py','.html','.css','.js','.svg','.ps1','.sh'}:
            files[p.relative_to(ROOT).as_posix()] = sha(p.read_bytes())
    comparisons = {}
    for relative in ['13-A-20261113/baseline.json','13-A-20261113/build-final.json','13-B-20261113/manifest-20261113T165442172058Z.json']:
        old = json.loads((OUT.parent / relative).read_text(encoding='utf-8-sig'))
        previous = old['product_files_sha256']
        comparisons[relative] = dict(changed=[k for k in previous if files.get(k) != previous[k]], added=[k for k in files if k not in previous])
    report = dict(at_utc=datetime.now(timezone.utc).isoformat(), pasada=1, sublote='13-B-final',
        git_head=subprocess.check_output(['git','-C',str(APP),'rev-parse','HEAD'],text=True).strip(),
        git_status=subprocess.check_output(['git','-C',str(APP),'status','--short'],text=True),
        source08_sha256=sha((ROOT/'08_Historias_de_Usuario.md').read_bytes()),
        product_build_sha256=sha(json.dumps(files,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()),
        product_files_sha256=files, comparisons=comparisons)
    save(name, report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['git_status','product_files_sha256']},ensure_ascii=False))

def database(run_name, name):
    run = (RESULTS / 'datos' / run_name).resolve()
    assert run.parent == (RESULTS / 'datos').resolve() and run.name.startswith('etapa13-')
    assert json.loads((run/'marker.json').read_text())['run'] == run.name
    fixture = json.loads((run/'fixture.json').read_text(encoding='utf-8'))
    con = sqlite3.connect((run/'audit.sqlite3').as_uri()+'?mode=ro',uri=True)
    con.row_factory = sqlite3.Row
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name") if r[0].startswith(('catalog_','inventory_','sales_','cash_'))]
    rows = {t:[dict(r) for r in con.execute('SELECT * FROM "'+t+'" ORDER BY rowid')] for t in tables}
    report = dict(at_utc=datetime.now(timezone.utc).isoformat(), fixture=run.name,
        fixture_day_lima=fixture['date_lima'], layer='SQLite read-only witness, not browser execution',
        business_sha256=sha(json.dumps(rows,sort_keys=True,ensure_ascii=False).encode()),
        sales=[{k:r[k] for k in ['id','correlative','confirmed_at','total_amount','discount_amount','cash_received','change_given']} for r in rows['sales_sale']],
        drafts=rows.get('sales_saledraft',[]), draft_lines=rows.get('sales_saledraftline',[]),
        integration_lots=[r for r in rows['inventory_lot'] if r['product_id']==fixture.get('products',{}).get('venta-integracion','').replace('-','')],
        counts={t:len(r) for t,r in rows.items()})
    # Idempotency UUIDs are test-only, but unnecessary in public evidence.
    for row in report['drafts']:
        row.pop('idempotency_key',None)
    save(name,report)
    print(json.dumps(report,ensure_ascii=False))
    con.close()

if __name__ == '__main__':
    if sys.argv[1]=='manifest': manifest(sys.argv[2])
    elif sys.argv[1]=='database': database(sys.argv[2],sys.argv[3])
