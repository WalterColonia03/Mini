"""Verificar el corte03-H; --write lo guarda una vez sin reemplazar evidencia."""
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
BASELINE = EVIDENCE / "03-H-inventario-20261110T042627868086Z.json"
BROWSER = EVIDENCE / "03-H-browser-20261110T042912719703Z"
RUNS = [
    "03-H-probe-20261110T042659237619Z",
    "03-H-tests-20261110T042730963824Z",
    "03-H-tests-20261110T042756100441Z",
    "03-H-browser-20261110T042844036974Z",
    BROWSER.name,
    "03-H-probe-20261110T043008623021Z",
]
OUTPUT = EVIDENCE / "03-H-cierre.json"
DOCS = ["ETAPA-03.md", "ESTADO_GENERAL.md", "anexos/ETAPA-03-inventario.md",
        "anexos/ETAPA-03-H-minimo.md"]
EXPECTED = {"CUMPLE": 20, "PARCIAL": 1, "PREVISTO/FUTURO": 6}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    write = parser.parse_args().write
    before = read(BASELINE)
    runs = [read(EVIDENCE / name / "result.json") for name in RUNS]
    preprobe, pretests, tests, failed_server, server, probe = runs
    browser = read(BROWSER / "browser.json")
    failed_browser = read(EVIDENCE / RUNS[3] / "browser.json")
    initial, final = read(BROWSER / "orm-initial.json"), read(BROWSER / "orm-final.json")
    cases = {c["id"]: c for c in browser["cases"]}
    changed = {p for p, h in before["source_hashes"].items() if digest(ROOT / p) != h}
    protected = {p: digest(ROOT / p) == h for p, h in before["protected_hashes"].items()}
    criteria = read(EVIDENCE / "03-G-cierre.json")["criteria"]
    for criterion in criteria:
        if criterion["id"] == "HU-PROD-02/CA-04":
            criterion["evidence_03h"] = "FIX03H-01 corregido;24 métodos/27 comprobaciones; máximo sin decisión y distinto en servicio/formulario"
    counts = Counter(c["execution"].split(" muestra")[0].split(" como")[0] for c in criteria)
    matrix = (RESULTS / "anexos/ETAPA-03-inventario.md").read_text(encoding="utf-8")
    rows = [line.split("|") for line in matrix.splitlines() if re.match(r"\| (?:CAT|PROD)\d+/CA\d+ ·", line)]
    matrix_counts = Counter(row[4].strip().split(" muestra")[0].split(" tras")[0] for row in rows)
    local_links = set()
    for name in DOCS:
        doc = RESULTS / name
        for target in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
            if "://" not in target and not target.startswith("#"):
                local_links.add((doc.parent / target.split("#")[0]).resolve())
    missing = sorted(str(p) for p in local_links if not p.is_file() and not (write and p == OUTPUT))
    invalid = {"0.5", "1.5", "True"}
    pre_invalid = [o for o in preprobe["observations"] if o["input"] in invalid]
    post_invalid = [o for o in probe["observations"] if o["input"] in invalid]
    above = [o for o in probe["observations"] if o["input"] == "1000000"]
    unchanged_keys = [k for k in initial if k not in ("catalog.Product", "commerce")]
    final_db = RESULTS / "datos" / server["run"] / "audit.sqlite3"
    source_hashes = {p: digest(ROOT / p) for p in ["r1-pmv/catalog/models.py", "r1-pmv/catalog/test_audit03_limits.py"]}
    support = [RESULTS / ("soporte/" + name) for name in
               ["audit03h_run.py", "audit03h_settings.py", "audit03h_browser.cjs", "cierre_etapa03h.py"]]
    support_hashes = {p.relative_to(RESULTS).as_posix(): digest(p) for p in support}
    evidence_files = [EVIDENCE / name / "result.json" for name in RUNS]
    evidence_files += [BASELINE, BROWSER / "browser.json", BROWSER / "orm-initial.json", BROWSER / "orm-final.json"]
    evidence_files += list(BROWSER.glob("*.png"))
    evidence_files += [EVIDENCE / RUNS[i] / "tests.txt" for i in [1, 2]]
    evidence_hashes = {p.relative_to(RESULTS).as_posix(): digest(p) for p in evidence_files}
    docs_hashes = {name: digest(RESULTS / name) for name in DOCS}
    retained = {str((RESULTS / "datos" / r["run"] / "audit.sqlite3").relative_to(ROOT)):
                digest(RESULTS / "datos" / r["run"] / "audit.sqlite3") for r in runs}
    checks = {
        "source_scope": changed == {"r1-pmv/catalog/models.py"},
        "protected_files": all(protected.values()),
        "all_runs_protected": all(all(r["protected_unchanged"].values()) for r in runs),
        "regression": tests["methods"] == 24 and tests["failures"] == 0,
        "before_failure_retained": pretests["methods"] == 2 and pretests["failures"] == 10,
        "browser_abort_retained": not failed_browser["cases"] and failed_server["browser_exit"] == 1
            and failed_browser["errors"][0]["message"] == "Isolation mismatch",
        "chrome": len(cases) == len(browser["cases"]) == 27 and all(c["ok"] for c in cases.values())
            and not browser["errors"] and server["browser_exit"] == 0,
        "servers_stopped": server["port_closed"] and failed_server["port_closed"],
        "truncation_before": len(pre_invalid) == 6 and all(o["accepted"] for o in pre_invalid),
        "invalid_rejected_after": len(post_invalid) == 6 and all(not o["accepted"]
            and "minimum_stock" in o["fields"] for o in post_invalid),
        "maximum_pending_not_approved": len(above) == 2 and all(o["accepted"] for o in above)
            and cases["H04-create-reject-1000000"]["ok"] and cases["H08-edit-reject-1000000"]["ok"],
        "initial_nonproduct_state_preserved": all(initial[k] == final[k] for k in unchanged_keys),
        "final_business_state": len(final["catalog.Category"]) == 3 and len(final["catalog.Product"]) == 4
            and sorted(p["minimum_stock"] for p in final["catalog.Product"]) == [0, 10, 10, 999999]
            and all(p["unit"] == "UND" and p["controls_expiration"] and p["is_active"] for p in final["catalog.Product"])
            and all(not final[k] for k in ["inventory.Lot", "inventory.InitialInventoryLoad", "sales.Sale",
                                           "sales.SaleLine", "sales.SaleDraft", "sales.SaleDraftLine"])
            and final["cash.CashShift"][0]["status"] == "OPEN",
        "coverage": len(criteria) == len({c["id"] for c in criteria}) == 27 and counts == EXPECTED,
        "matrix_matches": len(rows) == 27 and matrix_counts == EXPECTED,
        "links": not missing,
    }
    if OUTPUT.exists():
        previous = read(OUTPUT)
        checks["saved_files_match"] = (
            previous["sources_sha256"] == source_hashes and previous["evidence_sha256"] == evidence_hashes
            and previous["support_sha256"] == support_hashes and previous["docs_sha256"] == docs_hashes
            and previous["retained_databases_sha256"] == retained)
    report = {
        "verified_utc": datetime.now(timezone.utc).isoformat(), "checks": checks,
        "baseline": BASELINE.name, "protected_unchanged": protected,
        "sources_sha256": source_hashes, "support_sha256": support_hashes,
        "evidence_sha256": evidence_hashes, "docs_sha256": docs_hashes,
        "retained_databases_sha256": retained, "browser_database": final_db.relative_to(ROOT).as_posix(),
        "criteria": criteria, "counts": counts, "matrix_counts": matrix_counts,
        "links_checked": len(local_links), "missing": missing,
        "status": "Sublote técnico03-H verificado; etapa03 con decisiones y hallazgos abiertos; otros módulos sin cierre",
        "cursor": "03-H / PROP-03C-LIMITES / HU-PROD-02 CA04,08:221: recibir máximo; después PROP-03C-NOMBRE",
        "pending_decisions": ["Máximo del mínimo; formulario999999 y servicio1000000", "Nombres únicos o homónimos con códigos distintos"],
        "limits": ["24 métodos y27 comprobaciones no son suite global", "Sin PostgreSQL nuevo en03-H",
                   "Validación de servicio/modelo, no garantía de toda escritura SQL/ORM", "Seis criterios futuros",
                   "Lector real y aviso inmediato pendientes", "Migraciones de uso real pendientes"],
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
