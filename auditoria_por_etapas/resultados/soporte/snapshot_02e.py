"""Captura la linea base inmutable de entrada al sublote 02-E."""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
EV_DIR = ROOT / "auditoria_por_etapas" / "resultados" / "evidencias" / "02-E-20261114"
R1 = ROOT / "r1-pmv"

DOC_FILES = [
    "00_LEEME_PLANIFICACION.md",
    "01_Proyecto_y_Releases.md",
    "02_Diseno_Tecnico_R1_PMV.md",
    "03_Matriz_de_Trazabilidad_y_Pruebas.md",
    "07_Reglas_de_Negocio.md",
    "08_Historias_de_Usuario.md",
    "09_Product_Backlog.md",
    "14_Sprint_Planning.md",
    "16_Task_Breakdown.md",
    "21_Alcance_Actual_y_Diferencias.md",
    "r1-pmv/CONTROL_SPRINTS.md",
    "auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md",
    "auditoria_por_etapas/resultados/ETAPA-02.md",
    "auditoria_por_etapas/resultados/ESTADO_GENERAL.md",
    "auditoria_por_etapas/resultados/fuente_unica_20261112/INDICE_DERIVADO.json",
]

EXCLUDED_PARTS = {".venv", "__pycache__", ".pytest_cache", ".git", "staticfiles"}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def collect_r1_files() -> dict[str, dict[str, object]]:
    files: dict[str, dict[str, object]] = {}
    for path in sorted(R1.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(R1)
        if any(part in EXCLUDED_PARTS for part in rel.parts):
            continue
        if path.suffix.startswith(".sqlite") or ".sqlite3" in path.name:
            continue
        if path.suffix == ".pyc":
            continue
        rel_str = rel.as_posix()
        files[rel_str] = {
            "sha256": sha256_file(path),
            "size": path.stat().st_size,
        }
    return files


def aggregate_hash(files: dict[str, dict[str, object]]) -> str:
    h = hashlib.sha256()
    for rel in sorted(files):
        h.update(f"{rel}:{files[rel]['sha256']}\n".encode("utf-8"))
    return h.hexdigest()


def main() -> None:
    EV_DIR.mkdir(parents=True, exist_ok=True)
    copies = {
        "08_Historias_de_Usuario.md": "08-antes.md",
        "auditoria_por_etapas/resultados/ETAPA-02.md": "antes-ETAPA-02.md",
        "auditoria_por_etapas/resultados/ESTADO_GENERAL.md": "antes-ESTADO_GENERAL.md",
        "02_Diseno_Tecnico_R1_PMV.md": "antes-02.md",
        "16_Task_Breakdown.md": "antes-16.md",
        "14_Sprint_Planning.md": "antes-14.md",
        "21_Alcance_Actual_y_Diferencias.md": "antes-21.md",
    }
    for src_rel, dst_name in copies.items():
        shutil.copy2(ROOT / src_rel, EV_DIR / dst_name)

    code_backup = EV_DIR / "antes-codigo"
    if not code_backup.exists():
        for app_name in ("identity", "app_platform"):
            src_app = R1 / app_name
            for path in src_app.rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                    dst = code_backup / app_name / path.relative_to(src_app)
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, dst)

    r1_files = collect_r1_files()
    docs = {}
    for rel in DOC_FILES:
        p = ROOT / rel
        docs[rel] = {"sha256": sha256_file(p), "size": p.stat().st_size}

    protected_dbs = {}
    for p in sorted(R1.glob("*.sqlite3*")):
        if p.is_file():
            protected_dbs[p.relative_to(ROOT).as_posix()] = {
                "sha256": sha256_file(p),
                "size": p.stat().st_size,
            }

    manifest = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "r1_file_count": len(r1_files),
        "r1_build_sha256": aggregate_hash(r1_files),
        "r1_files": r1_files,
        "documents": docs,
        "protected_databases": protected_dbs,
    }
    (EV_DIR / "build-antes.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "r1_file_count": manifest["r1_file_count"],
                "r1_build_sha256": manifest["r1_build_sha256"],
                "plan08_sha256": manifest["documents"]["08_Historias_de_Usuario.md"]["sha256"],
                "protected_databases": protected_dbs,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
