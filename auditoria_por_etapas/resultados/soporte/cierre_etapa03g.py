"""Verificar evidencias y continuidad de03-G. --write guarda el corte una vez."""
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
BASELINE = EVIDENCE / "03-G-inventario-20261110T041634814752Z.json"
BROWSER = EVIDENCE / "03-G-browser-20261110T041945048165Z"
TESTS = EVIDENCE / "03-G-tests-20261110T041750658883Z/result.json"
OUTPUT = EVIDENCE / "03-G-cierre.json"
CHANGED = {
    "21_Alcance_Actual_y_Diferencias.md",
    "08_Historias_de_Usuario.md", "09_Product_Backlog.md", "02_Diseno_Tecnico_R1_PMV.md",
    "03_Matriz_de_Trazabilidad_y_Pruebas.md", "16_Task_Breakdown.md",
}
DOCS = ["ETAPA-03.md", "ESTADO_GENERAL.md", "anexos/ETAPA-03-inventario.md",
        "anexos/ETAPA-03-B-catalogo.md", "anexos/ETAPA-03-C-alta.md",
        "anexos/ETAPA-03-D-edicion.md", "anexos/ETAPA-03-E-disponibilidad.md", "anexos/ETAPA-03-F-alcance.md", "anexos/ETAPA-03-G-codigo-y-lector.md", "anexos/ETAPA-03-Barcode-to-PC.md"]
EXPECTED = {"CUMPLE": 20, "PARCIAL": 1, "PREVISTO/FUTURO": 6}


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    write = parser.parse_args().write
    before, tests = read(BASELINE), read(TESTS)
    browser, server = read(BROWSER / "browser.json"), read(BROWSER / "result.json")
    initial, final = read(BROWSER / "orm-initial.json"), read(BROWSER / "orm-final.json")
    cases = {case["id"]: case for case in browser["cases"]}
    changed = {p for p, h in before["source_hashes"].items() if digest(ROOT / p) != h}
    protected = {p: digest(ROOT / p) == h for p, h in before["protected_hashes"].items()}
    criteria = read(EVIDENCE / "03-F-cierre.json")["criteria"]
    for criterion in criteria:
        if criterion["id"] == "HU-PROD-04/CA-03":
            criterion["execution"] = "CUMPLE muestra03-G"
            criterion["scope"] = "Código editable DOC03-02 aceptado por usuario; auditado03-G"
            criterion["previous_text"] = criterion["text"]
            criterion["text"] = "ADMIN corrige código normalizado único conservando identidad/referencias y datos históricos; duplicado/inválido rechaza sin guardar cambios."
    counts = Counter(c["execution"].split(" muestra")[0].split(" como")[0] for c in criteria)
    local_links = set()
    for doc in [*(RESULTS / name for name in DOCS), *(ROOT / name for name in CHANGED if name.endswith(".md"))]:
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
    source_hashes = {p: digest(ROOT / p) for p in sorted(changed)}
    evidence_hashes = {p.relative_to(RESULTS).as_posix(): digest(p) for p in [
        TESTS, BROWSER / "browser.json", BROWSER / "orm-initial.json", BROWSER / "orm-final.json"]}
    checks = {
        "source_scope": changed == CHANGED,
        "protected_files": all(protected.values()),
        "run_protection": all(all(r["protected_unchanged"].values()) for r in [tests, server]),
        "regression": tests["methods"] == 10 and tests["failures"] == 0,
        "chrome": len(cases) == len(browser["cases"]) == 53 and all(c["ok"] for c in cases.values())
                  and not browser["errors"] and server["browser_exit"] == 0,
        "servers_stopped": server["port_closed"],
        "turn_preserved": initial["cash.CashShift"] == final["cash.CashShift"],
        "old_sale_preserved": initial["sales.Sale"][0] in final["sales.Sale"]
            and initial["sales.SaleLine"][0] in final["sales.SaleLine"],
        "final_business_state": len(final["catalog.Category"]) == len(final["catalog.Product"]) == 3
            and len(final["sales.Sale"]) == 2 and final["inventory.Lot"][0]["available_quantity"] == 17
            and len(active_ids) == len(active_lines) == 1 and active_lines[0]["quantity"] == 1
            and len(final["sales.SaleDraft"]) == 3 and final["cash.CashShift"][0]["status"] == "OPEN",
        "decision_and_code": cases["D15-code-edit"]["classification"].startswith("DOC03-02 accepted"),
        "scanner_not_overclaimed": cases["G01-keyboard-leading-zero"]["mode"] == "simulated keyboard; no physical reader"
            and "remains pending" in cases["G02-duplicate-observation"]["observation"],
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
        "support_sha256": {p.relative_to(RESULTS).as_posix(): digest(p) for p in [RESULTS / "soporte/audit03d_browser.cjs", RESULTS / "soporte/audit03g_browser.cjs", RESULTS / "soporte/audit03g_run.py", RESULTS / "soporte/audit03g_settings.py"]},
        "retained_database": final_db.relative_to(ROOT).as_posix(), "retained_database_sha256": digest(final_db),
        "criteria": criteria, "counts": counts, "matrix_counts": matrix_counts,
        "links_checked": len(local_links), "missing": missing,
        "accepted_decision": before["authority"],
        "status": "Auditoría de etapa03 completada en la muestra, con hallazgos y decisiones abiertos; otros módulos sin cierre",
        "cursor": "03-H / PROP-03C-LIMITES / HU-PROD-02 CA04, 08:221; decidir máximo del mínimo, después homónimos y lector real",
        "limits": ["No conformidad total", "Lector físico no ejecutado; aviso inmediato de duplicado pendiente", "Seis criterios futuros", "Suite global no ejecutada",
                   "Sin nueva ejecución PostgreSQL; sin cambios SQL/servicios",
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
