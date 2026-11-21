"""Verificar evidencias y continuidad de 03-D. --write guarda el corte una vez."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

RESULTS = Path(__file__).resolve().parents[1]
ROOT = RESULTS.parent.parent
EVIDENCE = RESULTS / "evidencias"
BASELINE = EVIDENCE / "03-D-inventario-20261110T025844751936Z.json"
BROWSER = EVIDENCE / "03-D-browser-20261110T030352675316Z"
TESTS = EVIDENCE / "03-D-tests-20261110T030339870193Z/result.json"
PG = EVIDENCE / "03-D-postgresql-20261110T030458286776Z.json"
OUTPUT = EVIDENCE / "03-D-cierre.json"
CHANGED = {
    "r1-pmv/catalog/forms.py", "r1-pmv/catalog/services.py", "r1-pmv/catalog/views.py",
    "r1-pmv/catalog/templates/catalog/product_edit.html", "r1-pmv/identity/static/identity/app.css",
}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    write = parser.parse_args().write
    before = read(BASELINE)
    tests = read(TESTS)
    pg = read(PG)
    browser = read(BROWSER / "browser.json")
    server = read(BROWSER / "result.json")
    initial = read(BROWSER / "orm-initial.json")
    final = read(BROWSER / "orm-final.json")
    cases = {case["id"]: case for case in browser["cases"]}
    changed = {p for p, h in before["source_hashes"].items() if digest(ROOT / p) != h}
    protected = {p: digest(ROOT / p) == h for p, h in before["protected_hashes"].items()}
    criteria = read(EVIDENCE / "03-C-cierre.json")["criteria"]
    for criterion in criteria:
        if criterion["id"] in {"HU-PROD-04/CA-01", "HU-PROD-04/CA-02", "HU-PROD-04/CA-04", "HU-PROD-04/CA-05"}:
            criterion["execution"] = "CUMPLE muestra03-D"
    counts = Counter(c["execution"].split(" muestra")[0].split(" como")[0] for c in criteria)
    local_links = set()
    for name in ["ETAPA-03.md", "ESTADO_GENERAL.md", "anexos/ETAPA-03-inventario.md",
                 "anexos/ETAPA-03-B-catalogo.md", "anexos/ETAPA-03-C-alta.md", "anexos/ETAPA-03-D-edicion.md"]:
        doc = RESULTS / name
        for target in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8-sig")):
            if "://" not in target and not target.startswith("#"):
                local_links.add((doc.parent / target.split("#")[0]).resolve())
    missing = sorted(str(p) for p in local_links if not p.is_file() and not (write and p == OUTPUT))
    old_sale = initial["sales.Sale"][0]
    old_line = initial["sales.SaleLine"][0]
    checks = {
        "source_scope": changed == CHANGED,
        "protected_files": all(protected.values()),
        "run_protection": all(all(r["protected_unchanged"].values()) for r in [tests, pg, server]),
        "regression": tests["methods"] == 76 and tests["failures"] == 0,
        "chrome": len(cases) == 51 and all(c["ok"] for c in cases.values()) and not browser["errors"] and server["browser_exit"] == 0,
        "postgres": len(pg["cases"]) == 4 and all(c["ok"] for c in pg["cases"]) and not pg.get("error"),
        "servers_stopped": server["port_closed"] and pg["port_closed"],
        "past_sale_preserved": old_sale in final["sales.Sale"] and old_line in final["sales.SaleLine"],
        "final_business_state": len(final["catalog.Product"]) == 3 and len(final["sales.Sale"]) == 2
        and final["inventory.Lot"][0]["available_quantity"] == 17
        and initial["cash.CashShift"] == final["cash.CashShift"]
        and sum(d["status"] == "ACTIVE" for d in final["sales.SaleDraft"]) == 1,
        "coverage": len(criteria) == len({c["id"] for c in criteria}) == 27 and counts == {
            "CUMPLE": 15, "PARCIAL": 1, "NO EJECUTADO": 3, "CONFLICTO DE FUENTES": 2, "PREVISTO/FUTURO": 6},
        "links": not missing,
    }
    report = {
        "verified_utc": datetime.now(timezone.utc).isoformat(), "checks": checks,
        "baseline": BASELINE.name, "protected_unchanged": protected,
        "sources_sha256": {p: digest(ROOT / p) for p in sorted(changed | {"r1-pmv/catalog/test_audit03_edit.py"})},
        "evidence_sha256": {p.relative_to(RESULTS).as_posix(): digest(p) for p in [
            TESTS, PG, BROWSER / "browser.json", BROWSER / "orm-initial.json", BROWSER / "orm-final.json"]},
        "criteria": criteria, "counts": counts, "links_checked": len(local_links), "missing": missing,
        "cursor": "03-E / HU-PROD-05 / CA-01 (08:254), ADMIN, Productos -> Deshabilitar, con lote e histórico y borrador ACTIVE de dos unidades",
    }
    print(json.dumps({"checks": checks, "counts": counts, "missing": missing}, ensure_ascii=False))
    if not all(checks.values()):
        raise SystemExit(1)
    if write:
        with OUTPUT.open("x", encoding="utf-8") as output:
            json.dump(report, output, ensure_ascii=False, indent=2)
            output.write("\n")


if __name__ == "__main__":
    main()

