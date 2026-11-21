"""Read-only verification of preserved databases, product sources, links and closure."""
import hashlib
import json
import re
import socket
from datetime import datetime, timezone
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[1]
ROOT = RESULTS.parent.parent
EVIDENCE = RESULTS / "evidencias" / "02-A-20261109T231223297870Z"
initial = json.loads((EVIDENCE / "baseline.json").read_text(encoding="utf-8"))
closure = json.loads((EVIDENCE / "closure.json").read_text(encoding="utf-8"))
browser = json.loads((EVIDENCE / "browser.json").read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

protected = {rel: sha(ROOT / rel) == value for rel, value in initial["protected_databases"].items()}
product = {rel: sha(ROOT / rel) == value for rel, value in initial["source_sha256"].items()}
with socket.socket() as sock:
    sock.settimeout(1)
    closed = sock.connect_ex(("127.0.0.1", closure["port"])) != 0
docs = [RESULTS / "ETAPA-02.md", RESULTS / "ESTADO_GENERAL.md",
        *(RESULTS / "anexos").glob("ETAPA-02-*.md"),
        ROOT / "03_Matriz_de_Trazabilidad_y_Pruebas.md", ROOT / "09_Product_Backlog.md"]
missing=[]
links=0
for doc in docs:
    for target in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
        if target.startswith(("https:", "http:", "#")):
            continue
        target = target.split("#")[0]
        links += 1
        if not (doc.parent / target).exists():
            missing.append({"doc": str(doc.relative_to(ROOT)), "target": target})
criteria = json.loads((RESULTS / "anexos" / "ETAPA-02-criterios.json").read_text(encoding="utf-8"))
source_hash_matches = criteria["source_sha256"] == sha(ROOT / "08_Historias_de_Usuario.md")
assert len(criteria["criteria"])==33 and len({c["id"] for c in criteria["criteria"]})==33
result={
    "verified_utc": datetime.now(timezone.utc).isoformat(),
    "original_closure_port_closed": closure["port_closed"],
    "followup_port_closed": closed,
    "note": "Original immediate probe was premature; preserved unchanged. Follow-up verifies closed port. Runner now polls up to five seconds. Functional Chrome tests were not repeated after this support-only correction.",
    "protected_unchanged": protected,
    "product_sources_unchanged": all(product.values()),
    "changed_product_sources": [p for p,v in product.items() if not v],
    "browser_records": len(browser["cases"]), "browser_failed": browser["failed"],
    "A20_no_open_shifts": next(c for c in browser["cases"] if c["id"]=="A20-SIN-TURNO-ADVERTENCIA")["details"]["open_shifts"]==0,
    "criteria_count":33,"criteria_source_hash_matches":source_hash_matches,
    "checked_local_links":links,"missing_local_links":missing,
    "support_source_sha256": {p.name:sha(p) for p in [Path(__file__), *(RESULTS / "soporte").glob("audit02a*"), RESULTS / "soporte" / "inventario_etapa02.py", RESULTS / "soporte" / "run_etapa02_revalidacion.py"] if p.is_file()},
}
(EVIDENCE / "closure-verified.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
print(json.dumps({k:v for k,v in result.items() if k not in ("support_source_sha256",)},indent=2,ensure_ascii=False))
if not all(protected.values()) or not all(product.values()) or not closed or missing or not source_hash_matches:
    raise SystemExit(1)
