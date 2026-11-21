"""Verificar evidencias y continuidad de03-E. --write guarda el corte una vez."""
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
BASELINE = EVIDENCE / "03-E-inventario-20261110T031347695888Z.json"
BROWSER = EVIDENCE / "03-E-browser-20261110T033002861512Z"
TESTS = EVIDENCE / "03-E-tests-20261110T032641479670Z/result.json"
PG = EVIDENCE / "03-E-postgresql-20261110T033046250292Z.json"
OUTPUT = EVIDENCE / "03-E-cierre.json"
CHANGED = {
    "r1-pmv/catalog/services.py", "r1-pmv/catalog/views.py",
    "r1-pmv/catalog/templates/catalog/category_list.html",
    "r1-pmv/catalog/templates/catalog/product_list.html",
    "r1-pmv/catalog/templates/catalog/product_created.html",
    "r1-pmv/catalog/test_audit03_catalogue.py",
}
NEW_TEST = "r1-pmv/catalog/test_audit03_availability.py"
DOCS = ["ETAPA-03.md", "ESTADO_GENERAL.md", "anexos/ETAPA-03-inventario.md",
        "anexos/ETAPA-03-B-catalogo.md", "anexos/ETAPA-03-C-alta.md",
        "anexos/ETAPA-03-D-edicion.md", "anexos/ETAPA-03-E-disponibilidad.md"]
EXPECTED = {"CUMPLE": 18, "PARCIAL": 1, "CONFLICTO DE FUENTES": 2, "PREVISTO/FUTURO": 6}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    write = parser.parse_args().write
    before, tests, pg = read(BASELINE), read(TESTS), read(PG)
    browser, server = read(BROWSER / "browser.json"), read(BROWSER / "result.json")
    initial, final = read(BROWSER / "orm-initial.json"), read(BROWSER / "orm-final.json")
    cases = {case["id"]: case for case in browser["cases"]}
    changed = {p for p, h in before["source_hashes"].items() if digest(ROOT / p) != h}
    protected = {p: digest(ROOT / p) == h for p, h in before["protected_hashes"].items()}
    criteria = read(EVIDENCE / "03-D-cierre.json")["criteria"]
    for criterion in criteria:
        if criterion["id"].startswith("HU-PROD-05/"):
            criterion["execution"] = "CUMPLE muestra03-E"
            criterion["scope"] = "Implementado adicionalmente; auditado en la muestra03-E"
    counts = Counter(c["execution"].split(" muestra")[0].split(" como")[0] for c in criteria)
    local_links = set()
    for name in DOCS:
        doc = RESULTS / name
        for target in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8-sig")):
            if "://" not in target and not target.startswith("#"):
                local_links.add((doc.parent / target.split("#")[0]).resolve())
    missing = sorted(str(p) for p in local_links if not p.is_file() and not (write and p == OUTPUT))
    matrix = (RESULTS / "anexos/ETAPA-03-inventario.md").read_text(encoding="utf-8")
    rows = [line.split("|") for line in matrix.splitlines() if re.match(r"\| (?:CAT|PROD)\d+/CA\d+ ·", line)]
    matrix_counts = Counter(row[4].strip().split(" muestra")[0].split(" tras")[0] for row in rows)
    active_ids = {d["id"] for d in final["sales.SaleDraft"] if d["status"] == "ACTIVE"}
    active_lines = [line for line in final["sales.SaleDraftLine"] if line["draft_id"] in active_ids]
    final_db = RESULTS / "datos" / server["run"] / "audit.sqlite3"
    source_hashes = {p: digest(ROOT / p) for p in sorted(changed | {NEW_TEST})}
    evidence_hashes = {p.relative_to(RESULTS).as_posix(): digest(p) for p in [
        TESTS, PG, BROWSER / "browser.json", BROWSER / "orm-initial.json", BROWSER / "orm-final.json"]}
    checks = {
        "source_scope": changed == CHANGED,
        "protected_files": all(protected.values()),
        "run_protection": all(all(r["protected_unchanged"].values()) for r in [tests, pg, server]),
        "regression": tests["methods"] == 82 and tests["failures"] == 0,
        "chrome": len(cases) == len(browser["cases"]) == 34 and all(c["ok"] for c in cases.values())
                  and not browser["errors"] and server["browser_exit"] == 0,
        "postgres": len(pg["cases"]) == 6 and all(c["ok"] for c in pg["cases"]) and not pg.get("error"),
        "servers_stopped": server["port_closed"] and pg["port_closed"],
        "observed_business_fields_preserved": initial == final,
        "final_business_state": len(final["catalog.Category"]) == 1 and len(final["catalog.Product"]) == 3
            and len(final["sales.Sale"]) == len(final["sales.SaleLine"]) == 1
            and sorted(lot["available_quantity"] for lot in final["inventory.Lot"]) == [4, 19]
            and len(active_ids) == len(active_lines) == 1 and active_lines[0]["quantity"] == 2
            and len(final["cash.CashShift"]) == 1 and final["cash.CashShift"][0]["status"] == "OPEN",
        "coverage": len(criteria) == len({c["id"] for c in criteria}) == 27 and counts == EXPECTED,
        "matrix_matches": len(rows) == 27 and matrix_counts == EXPECTED,
        "links": not missing,
    }
    if OUTPUT.exists():
        previous = read(OUTPUT)
        checks["saved_sources_and_evidence_match"] = (
            previous["sources_sha256"] == source_hashes and previous["evidence_sha256"] == evidence_hashes
            and previous["retained_database_sha256"] == digest(final_db)
        )
    report = {
        "verified_utc": datetime.now(timezone.utc).isoformat(), "checks": checks,
        "baseline": BASELINE.name, "protected_unchanged": protected,
        "sources_sha256": source_hashes, "evidence_sha256": evidence_hashes,
        "retained_database": final_db.relative_to(ROOT).as_posix(), "retained_database_sha256": digest(final_db),
        "criteria": criteria, "counts": counts, "matrix_counts": matrix_counts,
        "links_checked": len(local_links), "missing": missing,
        "status": "Auditoría de etapa03 completada en la muestra, con hallazgos y decisiones abiertos; otros módulos sin cierre",
        "cursor": "03-F / DOC03-01 / HU-PROD-02 CA01, 08:218 frente a08:876 y16:328; decisión de alcance de enlatados",
        "limits": ["No conformidad total", "Seis criterios futuros", "Suite global no ejecutada",
                   "Dos sesiones del mismo administrador en PG, sin carrera con cobro/inventario",
                   "Comparación de campos enumerados, no de todas las tablas", "Migraciones de uso real pendientes"],
    }
    print(json.dumps({"checks": checks, "counts": counts, "matrix_counts": matrix_counts, "missing": missing}, ensure_ascii=False))
    if not all(checks.values()):
        raise SystemExit(1)
    if write:
        with OUTPUT.open("x", encoding="utf-8") as output:
            json.dump(report, output, ensure_ascii=False, indent=2)
            output.write("\n")


if __name__ == "__main__":
    main()
