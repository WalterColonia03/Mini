"""Verificador final integral de integridad documental, build y evidencias · Sublote 02-E."""
from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "r1-pmv/manage.py").is_file())
HERE = Path(__file__).resolve().parent
R1 = ROOT / "r1-pmv"
EXPECTED_DB_SHA256 = "c60b4027d4d2f0953ddcbb828cd6412e9889f9794537de9c50aed7f92fdded58"

DOC_FILES = [
    "00_LEEME_PLANIFICACION.md",
    "01_Proyecto_y_Releases.md",
    "02_Diseno_Tecnico_R1_PMV.md",
    "03_Matriz_de_Trazabilidad_y_Pruebas.md",
    "04_Evidencias.md",
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
    "auditoria_por_etapas/resultados/soporte/02-E-inventario.md",
    "auditoria_por_etapas/resultados/soporte/02-E-disposiciones.md",
    "auditoria_por_etapas/resultados/fuente_unica_20261112/INDICE_DERIVADO.json",
]

LINK_AUDIT_DOCS = [
    "00_LEEME_PLANIFICACION.md",
    "01_Proyecto_y_Releases.md",
    "02_Diseno_Tecnico_R1_PMV.md",
    "03_Matriz_de_Trazabilidad_y_Pruebas.md",
    "04_Evidencias.md",
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
    "auditoria_por_etapas/resultados/soporte/02-E-inventario.md",
    "auditoria_por_etapas/resultados/soporte/02-E-disposiciones.md",
    "auditoria_por_etapas/resultados/evidencias/02-E-20261114/servidor/INFORME.md",
    "auditoria_por_etapas/resultados/evidencias/02-E-20261114/navegador/INFORME.md",
    "auditoria_por_etapas/resultados/evidencias/02-E-20261114/postgresql/INFORME.md",
]


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_r1_files() -> dict[str, dict]:
    excluded_dirs = {".venv", "__pycache__", ".git", ".pytest_cache", ".mypy_cache"}
    excluded_files = {"r1_pmv.sqlite3"}
    files: dict[str, dict] = {}
    for dirpath, dirnames, filenames in os.walk(R1):
        dirnames[:] = sorted(d for d in dirnames if d not in excluded_dirs)
        for fname in sorted(filenames):
            p = Path(dirpath) / fname
            if p.name in excluded_files or p.suffix in {".pyc", ".sqlite3"}:
                continue
            rel = p.relative_to(R1).as_posix()
            files[rel] = {"sha256": sha256_file(p), "size": p.stat().st_size}
    return files


def aggregate_hash(files: dict[str, dict]) -> str:
    h = hashlib.sha256()
    for rel in sorted(files):
        h.update(f"{rel}:{files[rel]['sha256']}:{files[rel]['size']}\n".encode("utf-8"))
    return h.hexdigest()


def github_slug(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"<[^>]+>", "", s)
    out = []
    for ch in s:
        cat = unicodedata.category(ch)
        if cat.startswith(("L", "N")) or ch in {" ", "-", "_"}:
            out.append(ch)
    slug = "".join(out).replace(" ", "-")
    return slug


def extract_anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    anchors: set[str] = set()
    for m in re.finditer(r'<a\s+id=["\']([^"\']+)["\']', text):
        anchors.add(m.group(1))
    counts: dict[str, int] = {}
    in_code = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if m:
            base = github_slug(m.group(1))
            if base:
                idx = counts.get(base, 0)
                counts[base] = idx + 1
                anchors.add(base if idx == 0 else f"{base}-{idx}")
    return anchors


def scan_links() -> list[dict]:
    anchor_cache: dict[Path, set[str]] = {}
    broken: list[dict] = []
    link_re = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)\)")
    for rel in LINK_AUDIT_DOCS:
        doc = ROOT / rel
        if not doc.is_file():
            broken.append({"doc": rel, "error": "missing_doc"})
            continue
        raw = doc.read_text(encoding="utf-8")
        if rel == "auditoria_por_etapas/resultados/ETAPA-02.md" and "## Informe y resultados históricos conservados" in raw:
            raw = raw.split("## Informe y resultados históricos conservados", 1)[0]
        # Strip fenced code blocks and inline code spans
        lines = []
        in_code = False
        for line in raw.splitlines():
            if line.strip().startswith("```"):
                in_code = not in_code
                continue
            if not in_code:
                lines.append(re.sub(r"`[^`]+`", "", line))
        cleaned = "\n".join(lines)
        for m in link_re.finditer(cleaned):
            href = m.group(1)
            if href.startswith(("http://", "https://", "mailto:", "file://")):
                continue
            if href.startswith("#"):
                target = doc
                frag = href[1:]
            else:
                path_part, _, frag = href.partition("#")
                target = (doc.parent / path_part).resolve()
            if not target.exists():
                broken.append({"doc": rel, "href": href, "error": "missing_target"})
                continue
            if frag and target.is_file() and target.suffix.lower() == ".md":
                if target not in anchor_cache:
                    anchor_cache[target] = extract_anchors(target)
                if frag not in anchor_cache[target] and frag.lower() not in anchor_cache[target]:
                    broken.append({"doc": rel, "href": href, "error": "missing_anchor"})
    return broken


def port_is_closed(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) != 0


def scan_secret_leaks() -> list[dict]:
    banned = [
        "Admin02E!99",
        "PgAudit02E!99",
        "User02E!99",
        "Secret02E!99",
        "CANARIO-SECRETO-PRUEBA",
        "django-insecure",
    ]
    targets = [
        HERE / "servidor",
        HERE / "navegador",
        HERE / "postgresql",
        ROOT / "auditoria_por_etapas/resultados/ETAPA-02.md",
        ROOT / "auditoria_por_etapas/resultados/ESTADO_GENERAL.md",
        ROOT / "auditoria_por_etapas/resultados/soporte/02-E-inventario.md",
        ROOT / "auditoria_por_etapas/resultados/soporte/02-E-disposiciones.md",
    ]
    leaks: list[dict] = []
    for t in targets:
        files = [t] if t.is_file() else [p for p in t.rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".json", ".log", ".txt"}]
        for f in files:
            content = f.read_text(encoding="utf-8", errors="replace")
            for pat in banned:
                if pat in content:
                    leaks.append({"file": f.relative_to(ROOT).as_posix(), "pattern": pat})
    return leaks


def main() -> None:
    antes = json.loads((HERE / "build-antes.json").read_text(encoding="utf-8"))

    # 1. Regenerate views idempotency check
    derived = [
        ROOT / "07_Reglas_de_Negocio.md",
        ROOT / "09_Product_Backlog.md",
        ROOT / "03_Matriz_de_Trazabilidad_y_Pruebas.md",
        ROOT / "auditoria_por_etapas/resultados/fuente_unica_20261112/INDICE_DERIVADO.json",
    ]
    before_derived = {p.name: sha256_file(p) for p in derived}
    regen = subprocess.run(
        [sys.executable, str(ROOT / "auditoria_por_etapas/resultados/fuente_unica_20261112/regenerar_vistas.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    regen_counts = json.loads(regen.stdout.strip())
    after_derived = {p.name: sha256_file(p) for p in derived}
    derived_byte_identical = before_derived == after_derived

    # 2. Protected DB check
    prod_db = R1 / "r1_pmv.sqlite3"
    db_sha = sha256_file(prod_db)
    prod_db_unchanged = db_sha == EXPECTED_DB_SHA256

    # 3. Build inventory & diff against build-antes.json
    r1_now = collect_r1_files()
    r1_prev = antes["r1_files"]
    added = sorted(set(r1_now) - set(r1_prev))
    removed = sorted(set(r1_prev) - set(r1_now))
    modified = sorted(k for k in (set(r1_now) & set(r1_prev)) if r1_now[k]["sha256"] != r1_prev[k]["sha256"])

    docs_now = {
        rel: {"sha256": sha256_file(ROOT / rel), "size": (ROOT / rel).stat().st_size}
        for rel in DOC_FILES
        if (ROOT / rel).is_file()
    }

    # 4. Evidences verification
    srv = json.loads((HERE / "servidor/resumen.json").read_text(encoding="utf-8"))
    nav = json.loads((HERE / "navegador/resumen.json").read_text(encoding="utf-8"))
    pg = json.loads((HERE / "postgresql/resumen.json").read_text(encoding="utf-8"))

    screenshots_exist = all((HERE / "navegador" / rel).is_file() for rel in nav.get("screenshots", []))
    ports_closed_now = port_is_closed(int(nav["port_used"])) and port_is_closed(int(pg["port"]))

    broken_links = scan_links()
    secret_leaks = scan_secret_leaks()

    checks = {
        "prod_db_unchanged": prod_db_unchanged,
        "derived_views_byte_identical": derived_byte_identical,
        "server_all_passed": bool(srv.get("all_passed")) and bool(srv.get("prod_db_unchanged")),
        "browser_all_passed": (
            bool(nav.get("all_passed"))
            and bool(nav.get("port_closed"))
            and bool(nav.get("no_horizontal_overflow"))
            and nav.get("page_errors") == []
            and nav.get("unexpected_console_errors") == []
            and nav.get("server_5xx") == []
            and screenshots_exist
        ),
        "pg_all_passed": (
            pg.get("status") == "COMPLETE"
            and bool(pg.get("port_closed"))
            and bool(pg.get("prod_db_unchanged"))
            and all(c.get("passed") for c in pg.get("cases", []))
        ),
        "ports_closed_now": ports_closed_now,
        "zero_broken_links": len(broken_links) == 0,
        "zero_secret_leaks": len(secret_leaks) == 0,
    }

    report = {
        "stage": "02-E",
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "r1_file_count_before": antes["r1_file_count"],
        "r1_build_sha256_before": antes["r1_build_sha256"],
        "r1_file_count_final": len(r1_now),
        "r1_build_sha256_final": aggregate_hash(r1_now),
        "r1_diff_summary": {"added": added, "removed": removed, "modified": modified},
        "regenerar_vistas": regen_counts,
        "protected_db": {"path": "r1-pmv/r1_pmv.sqlite3", "sha256": db_sha, "unchanged": prod_db_unchanged},
        "documents": docs_now,
        "checks": checks,
        "broken_links": broken_links,
        "secret_leaks": secret_leaks,
        "passed": all(checks.values()),
    }

    (HERE / "build-final.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"passed": report["passed"], "checks": checks, "broken_links": broken_links, "secret_leaks": secret_leaks}, ensure_ascii=False, indent=2))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
