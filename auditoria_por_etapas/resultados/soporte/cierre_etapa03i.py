"""Verifica el corte03-I; --write guarda una vez y no sustituye evidencia."""
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
BASELINE = EVIDENCE / "03-I-inventario-20261110T165406169875Z.json"
BROWSER = EVIDENCE / "03-I-browser-20261110T165730633729Z"
TESTS = EVIDENCE / "03-I-tests-20261110T165640773189Z"
INITIAL_TESTS = EVIDENCE / "03-I-tests-20261110T165543164740Z"
PG = EVIDENCE / "03-I-postgresql-20261110T165843365196Z.json"
OUTPUT = EVIDENCE / "03-I-cierre.json"
CHANGED = {
    "21_Alcance_Actual_y_Diferencias.md", "07_Reglas_de_Negocio.md", "08_Historias_de_Usuario.md",
    "09_Product_Backlog.md", "02_Diseno_Tecnico_R1_PMV.md", "03_Matriz_de_Trazabilidad_y_Pruebas.md",
    "16_Task_Breakdown.md", "r1-pmv/catalog/forms.py", "r1-pmv/catalog/models.py",
    "r1-pmv/catalog/services.py", "r1-pmv/catalog/test_audit03_catalogue.py",
}
NEW = ["r1-pmv/catalog/test_audit03_policy.py", "r1-pmv/catalog/migrations/0005_product_name_and_minimum_policy.py"]
DOCS = ["ETAPA-03.md", "ESTADO_GENERAL.md", "anexos/ETAPA-03-inventario.md", "anexos/ETAPA-03-I-politicas.md"]
EXPECTED = {"CUMPLE": 21, "PREVISTO/FUTURO": 6}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    write = parser.parse_args().write
    before, tests, initial_tests, pg = read(BASELINE), read(TESTS / "result.json"), read(INITIAL_TESTS / "result.json"), read(PG)
    browser, server = read(BROWSER / "browser.json"), read(BROWSER / "result.json")
    initial, final = read(BROWSER / "orm-initial.json"), read(BROWSER / "orm-final.json")
    changed = {p for p, h in before["source_hashes"].items() if digest(ROOT / p) != h}
    protected = {p: digest(ROOT / p) == h for p, h in before["protected_hashes"].items()}
    cases = {c["id"]: c for c in browser["cases"]}
    pgcases = {c["id"]: c for c in pg["cases"]}
    criteria = read(EVIDENCE / "03-H-cierre.json")["criteria"]
    source_lines = (ROOT / "08_Historias_de_Usuario.md").read_text(encoding="utf-8").splitlines()
    for criterion in criteria:
        if criterion["id"] in ["HU-PROD-02/CA-01", "HU-PROD-02/CA-04", "HU-PROD-04/CA-04"]:
            criterion["text_before_03i"] = criterion["text"]
            line = source_lines[int(criterion["source"].split(":")[-1]) - 1]
            criterion["text"] = re.sub(r"^\s*\d+\.\s*", "", line)
            criterion["execution"] = "CUMPLE muestra03-I"
            criterion["decision_03i"] = "Máximo999999 y nombre único aceptados por usuario10/11/2026"
    counts = Counter(c["execution"].split(" muestra")[0].split(" como")[0] for c in criteria)
    matrix = (RESULTS / "anexos/ETAPA-03-inventario.md").read_text(encoding="utf-8")
    rows = [line.split("|") for line in matrix.splitlines() if re.match(r"\| (?:CAT|PROD)\d+/CA\d+ ·", line)]
    matrix_counts = Counter(row[4].strip().split(" muestra")[0].split(" tras")[0] for row in rows)
    local_links = set()
    docs = [*(RESULTS / name for name in DOCS), *(ROOT / name for name in CHANGED if name.endswith(".md"))]
    for doc in docs:
        for target in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
            if "://" not in target and not target.startswith("#"):
                local_links.add((doc.parent / target.split("#")[0]).resolve())
    missing = sorted(str(p) for p in local_links if not p.is_file() and not (write and p == OUTPUT))
    nonproducts = [k for k in initial if k not in ("catalog.Product", "commerce")]
    final_db = RESULTS / "datos" / server["run"] / "audit.sqlite3"
    sources = {p: digest(ROOT / p) for p in sorted(CHANGED | set(NEW))}
    support = {p.relative_to(RESULTS).as_posix(): digest(p) for p in
               [*(RESULTS / "soporte").glob("audit03i*.*"), Path(__file__).resolve()]}
    evidence_files = [BASELINE, PG, BROWSER / "result.json", BROWSER / "browser.json",
                      BROWSER / "orm-initial.json", BROWSER / "orm-final.json",
                      TESTS / "result.json", TESTS / "tests.txt", INITIAL_TESTS / "result.json", INITIAL_TESTS / "tests.txt"]
    evidence_files += list(BROWSER.glob("*.png"))
    evidence = {p.relative_to(RESULTS).as_posix(): digest(p) for p in evidence_files}
    docs_hashes = {name: digest(RESULTS / name) for name in DOCS}
    checks = {
        "source_scope": changed == CHANGED,
        "protected_files": all(protected.values()),
        "all_runs_protected": all(all(r["protected_unchanged"].values()) for r in [tests, initial_tests, server, pg]),
        "regression": tests["methods"] == 91 and tests["failures"] == 0,
        "initial_fixture_failure_retained": initial_tests["methods"] == 91 and initial_tests["failures"] == 1,
        "chrome": len(cases) == len(browser["cases"]) == 36 and all(c["ok"] for c in cases.values())
            and not browser["errors"] and server["browser_exit"] == 0,
        "postgresql": len(pgcases) == len(pg["cases"]) == 8 and all(c["ok"] for c in pgcases.values()) and not pg.get("error"),
        "servers_stopped": server["port_closed"] and pg["port_closed"],
        "nonproduct_state_preserved": all(initial[k] == final[k] for k in nonproducts),
        "retained_business_state": len(final["catalog.Category"]) == 3 and len(final["catalog.Product"]) == 6
            and sorted(p["minimum_stock"] for p in final["catalog.Product"]) == [0, 10, 10, 10, 999999, 999999]
            and sum(p["is_active"] for p in final["catalog.Product"]) == 5
            and all(p["unit"] == "UND" and p["controls_expiration"] for p in final["catalog.Product"])
            and all(not final[k] for k in ["inventory.Lot", "inventory.InitialInventoryLoad", "sales.Sale", "sales.SaleLine", "sales.SaleDraft", "sales.SaleDraftLine"])
            and final["cash.CashShift"][0]["status"] == "OPEN",
        "coverage": len(criteria) == len({c["id"] for c in criteria}) == 27 and counts == EXPECTED,
        "matrix_matches": len(rows) == 27 and matrix_counts == EXPECTED,
        "links": not missing,
    }
    if OUTPUT.exists():
        previous = read(OUTPUT)
        checks["saved_files_match"] = (previous["sources_sha256"] == sources and previous["evidence_sha256"] == evidence
            and previous["support_sha256"] == support and previous["docs_sha256"] == docs_hashes
            and previous["retained_database_sha256"] == digest(final_db))
    report = {
        "verified_utc": datetime.now(timezone.utc).isoformat(), "checks": checks,
        "baseline": BASELINE.name, "authority": before["authority"], "protected_unchanged": protected,
        "sources_sha256": sources, "evidence_sha256": evidence, "support_sha256": support, "docs_sha256": docs_hashes,
        "retained_database": final_db.relative_to(ROOT).as_posix(), "retained_database_sha256": digest(final_db),
        "criteria": criteria, "counts": counts, "matrix_counts": matrix_counts,
        "links_checked": len(local_links), "missing": missing,
        "status": "Sublote03-I verificado; etapa03 con propuestas/límites abiertos, sin cierre de otros módulos",
        "cursor": "03-J / PROP-E00-HU-02 y PROP-E03-T01 / estado de categoría: conciliar confirmación e información de impacto; no asumir aceptación",
        "limits": ["Migraciones0003/0004/0005 no aplicadas en base original", "Suite global no ejecutada",
                   "Seis CA futuros", "Lector físico/aviso inmediato pendientes", "Comparación comercial acotada a campos del soporte",
                   "UNIQUE protege clave almacenada; SQL que cambie nombre sin clave requiere disciplina de escritura"],
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
