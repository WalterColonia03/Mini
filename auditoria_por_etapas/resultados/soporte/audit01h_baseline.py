"""Capture reproducible, non-secret hashes for the isolated 01-H audit."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
OUT = ROOT / "auditoria_por_etapas/resultados/evidencias/01-H-20261115"
EXCLUDED = {".git", ".venv", "__pycache__", "staticfiles", "evidencias"}
EXTENSIONS = {".py", ".html", ".css", ".js", ".svg", ".yaml", ".yml", ".txt"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True, choices=("antes", "despues", "final", "ultimo"))
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    destination = OUT / ("build-" + args.label + ".json")
    if destination.exists():
        raise SystemExit("Snapshot exists; refusing to overwrite it")
    paths = sorted(
        p for p in APP.rglob("*")
        if p.is_file() and not (set(p.relative_to(APP).parts) & EXCLUDED)
        and (p.suffix.lower() in EXTENSIONS or p.name == "Dockerfile")
    )
    source = {p.relative_to(APP).as_posix(): sha(p) for p in paths}
    canonical = "".join(f"{name}\0{digest}\n" for name, digest in source.items()).encode("utf-8")
    tracked = [
        "08_Historias_de_Usuario.md", "07_Reglas_de_Negocio.md", "09_Product_Backlog.md",
        "03_Matriz_de_Trazabilidad_y_Pruebas.md", "02_Diseno_Tecnico_R1_PMV.md",
        "14_Sprint_Planning.md", "16_Task_Breakdown.md", "21_Alcance_Actual_y_Diferencias.md",
        "r1-pmv/r1_pmv.sqlite3", "auditoria_por_etapas/resultados/datos/etapa00-20261105/audit.sqlite3",
        "auditoria_por_etapas/resultados/datos/etapa01-20261109/audit.sqlite3",
        "auditoria_por_etapas/resultados/datos/01-E-20261114/audit.sqlite3",
        "auditoria_por_etapas/resultados/datos/01-F-20261114/audit.sqlite3",
        "auditoria_por_etapas/resultados/datos/01-G-20261114/audit.sqlite3",
    ]
    protected = {name: sha(ROOT / name) for name in tracked if (ROOT / name).is_file()}
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=APP, capture_output=True, text=True, check=True).stdout.strip()
    status = subprocess.run(["git", "status", "--porcelain=v1", "--untracked-files=all"], cwd=APP, capture_output=True, text=True, check=True).stdout.splitlines()
    result = {
        "capturado_utc": datetime.now(timezone.utc).isoformat(),
        "git_head": head,
        "git_cambios_preexistentes_n": len(status),
        "git_status": status,
        "build_algoritmo": "sha256 de rutas relativas NUL sha256 de archivos, ordenadas; extensiones explícitas, sin .env ni bases",
        "build_sha256": hashlib.sha256(canonical).hexdigest(),
        "fuentes_n": len(source),
        "fuentes": source,
        "documentos_y_bases": protected,
    }
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"archivo": destination.relative_to(ROOT).as_posix(), "build_sha256": result["build_sha256"], "fuentes_n": len(source), "git_cambios": len(status), "db_principal_sha256": protected.get("r1-pmv/r1_pmv.sqlite3")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
