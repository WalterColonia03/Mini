"""Compare source inventory without importing Django, opening databases or reading secrets."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json
import subprocess
import re

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BASELINE = json.loads((OUT / "ETAPA-00-fuentes-inventario.json").read_text(encoding="utf-8"))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def git(*args):
    return subprocess.run(["git", "-c", "core.quotepath=false", "-C", str(ROOT / "r1-pmv"), *args],
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout.strip()

checked = []
for entry in BASELINE["root_files"]:
    path = ROOT / entry["path"]
    current = sha(path) if path.is_file() else None
    checked.append({"path": entry["path"], "sha256_baseline": entry["sha256"],
                    "sha256_current": current, "unchanged": current == entry["sha256"]})
for relative, old_hash in BASELINE["git"]["changed_file_hashes"].items():
    path = ROOT / "r1-pmv" / relative
    current = sha(path) if path.is_file() else None
    checked.append({"path": "r1-pmv/" + relative, "sha256_baseline": old_hash,
                    "sha256_current": current, "unchanged": current == old_hash})
status = git("status", "--short", "--untracked-files=all").splitlines()
head = git("log", "-1", "--format=%H %cI %s")
report = {
    "generated_lima": datetime.now(timezone(timedelta(hours=-5))).isoformat(),
    "baseline_generated_lima": BASELINE["generated_lima"],
    "scope": "Root file hashes and 49 preexisting tracked changes; Git path/status comparison. No app/test execution.",
    "head": head,
    "head_unchanged": head == BASELINE["git"]["head"],
    "branch": git("branch", "--show-current"),
    "status": status,
    "status_unchanged": status == BASELINE["git"]["status"],
    "checked": checked,
    "changed": [row["path"] for row in checked if not row["unchanged"]],
    "baseline_hashed_untracked": False,
    "limitations": ["Untracked files were not hashed in the original sources inventory; same status does not prove their content unchanged.",
                    "No spreadsheet cells, formulas, rendered layout or test outcomes were examined."]
}
plan = json.loads((OUT / "ETAPA-00-planificacion.json").read_text(encoding="utf-8"))
stories = plan["historias"]
criteria = [criterion for story in stories for criterion in story["criterios"]]
r1_criteria = {criterion["id"] for story in stories if story["seleccion"] == "R1 SELECCIONADO" for criterion in story["criterios"]}
references = []
def find_refs(value):
    if isinstance(value, dict):
        for key, child in value.items():
            if key.startswith("fuente") and isinstance(child, str) and re.search(r":\d+$", child):
                references.append(child)
            else:
                find_refs(child)
    elif isinstance(value, list):
        for child in value:
            find_refs(child)
find_refs(plan)
unresolved = []
for reference in sorted(set(references)):
    name, line = reference.rsplit(":", 1)
    file = ROOT / name
    if not file.is_file() or int(line) > len(file.read_text(encoding="utf-8-sig").splitlines()):
        unresolved.append(reference)
report["planning_structure"] = {
    "stories_including_out_of_horizon": len(stories),
    "base_criteria": len(criteria),
    "unique_base_criteria": len({row["id"] for row in criteria}),
    "rules": len(plan["reglas"]), "tasks": len(plan["tareas"]),
    "unique_tasks": len({row["id"] for row in plan["tareas"]}),
    "r1_matrix_rows": len(plan["matriz_historica_r1"]),
    "matrix_matches_r1_criterion_ids": {row["criterio"] for row in plan["matriz_historica_r1"]} == r1_criteria,
    "unique_references_checked": len(set(references)),
    "unresolved_file_line_references": unresolved,
    "semantic_acceptance": "NO EXAMINADO; IDs and file/line existence only."
}
(OUT / "ETAPA-00-fuentes-revalidacion-20261109.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"generated_lima": report["generated_lima"], "hashed": len(checked),
                  "changed": report["changed"], "head_unchanged": report["head_unchanged"],
                  "status_unchanged": report["status_unchanged"],
                  "planning_structure": report["planning_structure"]}, ensure_ascii=False))
