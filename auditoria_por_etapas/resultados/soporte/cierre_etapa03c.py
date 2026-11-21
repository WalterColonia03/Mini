"""Cotejar el corte 03-C. El modo --write crea el manifiesto histórico una vez."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

RESULTS = Path(__file__).resolve().parents[1]
ROOT = RESULTS.parent.parent
FILES = RESULTS / "evidencias"
BASELINE = FILES / "03-C-inventario-20261110T023647599819Z.json"
CHROME = FILES / "03-C-browser-20261110T024801097155Z"
TESTS = FILES / "03-C-tests-20261110T024749832414Z/result.json"
PG = FILES / "03-C-postgresql-20261110T024529647523Z.json"
CLOSURE = FILES / "03-C-cierre.json"
EDITS = {"r1-pmv/catalog/" + name for name in
         ["forms.py", "models.py", "services.py", "views.py", "templates/catalog/product_form.html"]}
REGRESSION = "r1-pmv/catalog/test_audit03_registration.py"


def read(file):
    return json.loads(file.read_text(encoding="utf-8-sig"))


def sha(file):
    return hashlib.sha256(file.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    write = parser.parse_args().write
    baseline = read(BASELINE)
    tests = read(TESTS)
    pg = read(PG)
    http = read(CHROME / "result.json")
    browser = read(CHROME / "browser.json")
    initial = read(CHROME / "orm-initial.json")
    final = read(CHROME / "orm-final.json")
    protected = {key: sha(ROOT / key) == prior for key, prior in baseline["protected_hashes"].items()}
    changed = {key for key, prior in baseline["source_hashes"].items() if sha(ROOT / key) != prior}
    criteria = read(FILES / "03-B-cierre.json")["criteria"]
    for row in criteria:
        if row["id"] in {"HU-PROD-02/CA-02", "HU-PROD-02/CA-03", "HU-PROD-02/CA-05"}:
            row["execution"] = "CUMPLE muestra03-C"
        elif row["id"] == "HU-PROD-02/CA-04":
            row["execution"] = "PARCIAL"
    counts = Counter(r["execution"].split(" muestra")[0].split(" como")[0] for r in criteria)
    links = set()
    for name in ["ETAPA-03.md", "ESTADO_GENERAL.md", "anexos/ETAPA-03-inventario.md",
                 "anexos/ETAPA-03-B-catalogo.md", "anexos/ETAPA-03-C-alta.md"]:
        document = RESULTS / name
        for target in re.findall(r"\]\(([^)]+)\)", document.read_text(encoding="utf-8-sig")):
            if "://" not in target and not target.startswith("#"):
                links.add((document.parent / target.split("#")[0]).resolve())
    missing = sorted(str(p) for p in links if not p.is_file() and not (write and p == CLOSURE))
    unchanged_business = ["cash.CashShift", "inventory.Lot", "inventory.InitialInventoryLoad",
                          "sales.Sale", "sales.SaleLine", "sales.SaleDraft", "sales.SaleDraftLine"]
    cases = {case["id"]: case for case in browser["cases"]}
    checks = {
        "protected": all(protected.values()) and all(all(run["protected_unchanged"].values()) for run in [pg, tests, http]),
        "scope": changed == EDITS and (ROOT / REGRESSION).is_file(),
        "django": tests["methods"] == 68 and tests["failures"] == 0,
        "browser_http_orm": len(cases) == 49 and all(c["ok"] for c in cases.values()) and not browser["errors"] and http["browser_exit"] == 0,
        "postgres": len(pg["cases"]) == 5 and all(c["ok"] for c in pg["cases"]) and not pg.get("error"),
        "open_name_observation": pg["observations"][0]["both_valid"] and pg["observations"][0]["stored"] == 2,
        "ports_closed": pg["port_closed"] and http["port_closed"],
        "business": len(initial["catalog.Product"]) == 0 and len(final["catalog.Product"]) == 3
        and all(initial[key] == final[key] for key in unchanged_business)
        and {c["name"] for c in final["catalog.Category"] if c["is_active"]} == {"Productos enlatados"},
        "coverage": len(criteria) == len({r["id"] for r in criteria}) == 27 and counts == {
            "CUMPLE": 11, "PARCIAL": 1, "NO EJECUTADO": 7, "CONFLICTO DE FUENTES": 2, "PREVISTO/FUTURO": 6},
        "links": not missing,
    }
    report = {
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "checks": checks, "baseline": BASELINE.name, "protected_unchanged": protected,
        "source_sha256": {p: sha(ROOT / p) for p in sorted(changed | {REGRESSION})},
        "evidence_sha256": {p.relative_to(RESULTS).as_posix(): sha(p) for p in [
            BASELINE, TESTS, CHROME / "browser.json", CHROME / "orm-initial.json", CHROME / "orm-final.json", PG]},
        "snapshotted_counts": {key:len(val) for key, val in final.items()},
        "criteria": criteria, "counts": counts, "links_total": len(links), "missing_links": missing,
        "next": "03-D / HU-PROD-04 / CA-01 (08:241), ADMIN, editar producto de S/ 8,50 a S/ 9,20 con venta histórica y borrador",
    }
    print(json.dumps({"checks": checks, "missing": missing, "links": len(links), "criteria_counts": counts}, ensure_ascii=False))
    if not all(checks.values()):
        raise SystemExit(1)
    if write:
        with CLOSURE.open("x", encoding="utf-8") as out:
            json.dump(report, out, indent=2, ensure_ascii=False)
            out.write("\n")


if __name__ == "__main__":
    main()

