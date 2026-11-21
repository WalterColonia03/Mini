"""Read-only witness of the populated browser fixture after dashboard navigation."""
from pathlib import Path
import json, os, sqlite3
from audit13_run import RESULTS

run = Path(os.environ['AUDIT13_RUN_DIR']).resolve()
if run.parent != (RESULTS/'datos').resolve() or not run.name.startswith('etapa13-'):
    raise SystemExit('Invalid run')
if json.loads((run/'marker.json').read_text(encoding='utf-8'))['run'] != run.name:
    raise SystemExit('Wrong marker')
with sqlite3.connect((run/'audit.sqlite3').as_uri()+'?mode=ro',uri=True) as conn:
    conn.row_factory = sqlite3.Row
    queries = {
        'sales':'SELECT correlative, total_amount,discount_amount FROM sales_sale ORDER BY correlative',
        'drafts':'SELECT d.status, p.name, l.quantity, l.unit_price FROM sales_saledraft d JOIN sales_saledraftline l ON l.draft_id=d.id JOIN catalog_product p ON p.id=l.product_id',
        'sale_product_lot':"SELECT number, available_quantity FROM inventory_lot WHERE number='A13-venta-integracion-0'",
        'shifts':'SELECT status, COUNT(*) AS count FROM cash_cashshift GROUP BY status',
    }
    print(json.dumps({'run':run.name,'opened':'sqlite mode=ro','observed':{key:[dict(row) for row in conn.execute(q)] for key,q in queries.items()}},indent=2,ensure_ascii=False))
