"""Record only source changes made after this sublot's own baseline."""
from __future__ import annotations

import difflib
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
OLD = ROOT / "auditoria_por_etapas/resultados/datos/01-I-20261115/fuentes-antes"
OUT = ROOT / "auditoria_por_etapas/resultados/evidencias/01-I-20261115"
files = sorted(p.relative_to(OLD) for p in OLD.rglob("*") if p.is_file())
parts = []
summary = []
for rel in files:
    before = (OLD / rel).read_bytes()
    after = (APP / rel).read_bytes()
    if before == after:
        continue
    old_lines = before.decode("utf-8").splitlines(keepends=True)
    new_lines = after.decode("utf-8").splitlines(keepends=True)
    parts.extend(difflib.unified_diff(old_lines, new_lines, fromfile="antes/" + rel.as_posix(), tofile="despues/" + rel.as_posix(), lineterm="\n"))
    summary.append({"archivo": rel.as_posix(), "antes_sha256": hashlib.sha256(before).hexdigest(), "despues_sha256": hashlib.sha256(after).hexdigest()})
added = APP / "identity/test_audit01i_security.py"
summary.append({"archivo": added.relative_to(APP).as_posix(), "antes_sha256": None, "despues_sha256": hashlib.sha256(added.read_bytes()).hexdigest()})
(OUT / "cambios-producto.diff").write_text("".join(parts), encoding="utf-8", newline="")
(OUT / "cambios-producto.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"archivos": len(summary), "diff": "cambios-producto.diff"}, ensure_ascii=False))
