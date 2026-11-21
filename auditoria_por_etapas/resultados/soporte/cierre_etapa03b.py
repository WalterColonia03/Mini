"""Verify the recorded 03-B cut. Use --write once to save its evidence."""
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
OUTPUT = EVIDENCE / "03-B-cierre.json"
BASELINE = EVIDENCE / "03-B-inventario-20261110T010633144160Z/baseline.json"
BROWSER = EVIDENCE / "03-B-browser-20261110T020505026105Z"
TESTS = EVIDENCE / "03-B-tests-20261110T020324334766Z/result.json"
POSTGRES = EVIDENCE / "03-B-postgresql-20261110T020354212138Z.json"
EDITED = {
    "r1-pmv/catalog/models.py",
    "r1-pmv/catalog/views.py",
    "r1-pmv/catalog/templates/catalog/product_list.html",
    "r1-pmv/identity/static/identity/app.css",
}
ADDED_TO_AUDIT = [
    "r1-pmv/catalog/migrations/0004_product_search_name.py",
    "r1-pmv/catalog/test_audit03_catalogue.py",
]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    baseline = read(BASELINE)
    protected = {p: digest(ROOT / p) == old for p, old in baseline["protected_hashes"].items()}
    changed = {p for p, old in baseline["source_hashes"].items() if digest(ROOT / p) != old}
    tests = read(TESTS)
    chrome = read(BROWSER / "browser.json")
    server = read(BROWSER / "result.json")
    pg = read(POSTGRES)
    fixture = read(BROWSER / "fixture.json")
    final = read(BROWSER / "orm-final.json")
    criteria = read(EVIDENCE / "03-A-criterios.json")
    for row in criteria:
        if row["id"].startswith("HU-PROD-01/"):
            row["execution"] = "CUMPLE muestra03-B"
    counts = Counter(row["execution"] for row in criteria)
    documents = ["ETAPA-03.md", "anexos/ETAPA-03-inventario.md", "anexos/ETAPA-03-B-catalogo.md", "ESTADO_GENERAL.md"]
    missing = []
    links_checked = 0
    for relative in documents:
        doc = RESULTS / relative
        for target in re.findall(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8-sig")):
            if "://" in target or target.startswith("#"):
                continue
            path = (doc.parent / target.split("#")[0]).resolve()
            if args.write and path == OUTPUT:
                continue
            links_checked += 1
            if not path.is_file():
                missing.append([relative, target])

    checks = {
        "baseline_protected_files_unchanged": all(protected.values()),
        "expected_source_changes": changed == EDITED,
        "all_runs_preserved_prior_files": all(
            all(result["protected_unchanged"].values()) for result in (tests, server, pg)
        ),
        "catalogue_regression": tests["methods"] == 62 and tests["failures"] == 0,
        "browser": len(chrome["cases"]) == 43 and not chrome["errors"] and all(c["ok"] for c in chrome["cases"]) and server["browser_exit"] == 0,
        "postgres": len(pg["cases"]) == 5 and not pg.get("error") and all(c["ok"] for c in pg["cases"]),
        "ports_closed_at_end_of_runs": pg["port_closed"] and server["port_closed"],
        "business_snapshot_unchanged": fixture["snapshot"] == final,
        "criteria": len(criteria) == len({c["id"] for c in criteria}) == 27
        and counts == {
            "CUMPLE muestra03-A": 5, "CUMPLE muestra03-B": 3, "PREVISTO/FUTURO": 6,
            "CONFLICTO DE FUENTES": 2, "NO EJECUTADO como auditoría completa; regresión automática ejecutada": 11,
        },
        "report_links": not missing,
    }
    report = {
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "checks": checks,
        "baseline": BASELINE.relative_to(RESULTS).as_posix(),
        "protected_unchanged": protected,
        "changed_from_baseline": sorted(changed),
        "files_outside_baseline_inventory": ADDED_TO_AUDIT,
        "application_sha256": {p: digest(ROOT / p) for p in sorted(changed.union(ADDED_TO_AUDIT))},
        "criteria_counts": dict(counts),
        "criteria": criteria,
        "results": {
            "django": [tests["methods"] - tests["failures"], tests["methods"]],
            "browser_http_orm": [sum(c["ok"] for c in chrome["cases"]), len(chrome["cases"])],
            "postgres": [sum(c["ok"] for c in pg["cases"]), len(pg["cases"])],
            "snapshotted_rows": {k: len(v) for k, v in final.items()},
            "evidence": [p.relative_to(RESULTS).as_posix() for p in [TESTS, BROWSER / "browser.json", BROWSER / "result.json", POSTGRES]],
        },
        "links_checked": links_checked,
        "missing_links": missing,
        "cursor": "03-C / HU-PROD-02 / CA-01 (08:218), ADMIN, Registrar producto, GET /productos/nuevo/",
    }
    print(json.dumps({"checks": checks, "changed": sorted(changed), "missing": missing, "links": links_checked}, ensure_ascii=False))
    if not all(checks.values()):
        raise SystemExit(1)
    if args.write:
        with OUTPUT.open("x", encoding="utf-8") as out:
            json.dump(report, out, indent=2, ensure_ascii=False)
            out.write("\n")


if __name__ == "__main__":
    main()
