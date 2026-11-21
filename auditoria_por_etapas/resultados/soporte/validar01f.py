"""Validate Stage 01-F artifacts, primary source invariants, protected DB hashes, open ports and sanitization."""
from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "auditoria_por_etapas/resultados/evidencias/01-F-20261114"
DATA = ROOT / "auditoria_por_etapas/resultados/datos/01-F-20261114"

sys.path.insert(0, str(ROOT / "auditoria_por_etapas/resultados/fuente_unica_20261112"))
import regenerar_vistas as views  # noqa: E402


def snapshot_r1() -> tuple[str, dict[str, str]]:
    r1 = ROOT / "r1-pmv"
    src_files: dict[str, str] = {}
    h_build = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(r1):
        dirnames[:] = sorted(d for d in dirnames if d not in {".venv", "__pycache__", ".pytest_cache", ".git"})
        for fname in sorted(filenames):
            p = Path(dirpath) / fname
            if p.suffix in {".sqlite3", ".pyc"}:
                continue
            rel = p.relative_to(r1).as_posix()
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            src_files[rel] = digest
            h_build.update(rel.encode("utf-8") + b"\x00" + digest.encode("ascii") + b"\n")
    return h_build.hexdigest(), src_files


def check_links(rel_path: str) -> list[str]:
    p = ROOT / rel_path
    text = p.read_text(encoding="utf-8")
    broken: list[str] = []
    for label, target in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text):
        if target.startswith(("http://", "https://", "#")):
            continue
        clean = target.split("#", 1)[0]
        if not clean:
            continue
        resolved = (p.parent / clean).resolve()
        if not resolved.exists():
            broken.append(f"{rel_path}: {label} -> {target}")
    return broken


def main() -> int:
    before = json.loads((OUT / "build-before.json").read_text(encoding="utf-8"))
    build_after_sha, src_after = snapshot_r1()

    # Check Stage 01 own source scope remained unchanged
    scope_files = [
        "identity/urls.py", "identity/views.py", "identity/forms.py", "identity/services.py",
        "identity/models.py", "identity/admin.py", "identity/middleware.py", "identity/authorization.py",
        "identity/templates/identity/login.html", "identity/templates/identity/base.html",
        "config/urls.py", "config/settings.py", "app_platform/logging.py",
    ]
    scope_delta = [f for f in scope_files if before["source_files"].get(f) != src_after.get(f)]

    # Document invariants & derived views
    s, hs, tests, criteria = views.parse()
    doc_errors = views.document_errors(s, hs, tests, criteria)
    expected: dict[Path, str] = {}
    orig_write = views.write
    views.write = lambda p, t: expected.update({p: t.rstrip() + "\n"})
    try:
        views.generate()
    finally:
        views.write = orig_write
    derived_mismatch = [
        p.relative_to(ROOT).as_posix()
        for p, t in expected.items()
        if p.read_text(encoding="utf-8") != t
    ]

    # Protected DB hashes
    protected_db_now = {
        rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        for rel in before["protected_database_sha256"]
        if (ROOT / rel).exists()
    }
    protected_equal = protected_db_now == before["protected_database_sha256"]

    # Port 8782 closed & temporary secret file removed
    with socket.socket() as sock:
        sock.settimeout(0.5)
        port_8782_open = sock.connect_ex(("127.0.0.1", 8782)) == 0
    cred_file_present = (DATA / ".credentials.json").exists()

    # Links in ETAPA-01.md and ESTADO_GENERAL.md
    broken_links = check_links("auditoria_por_etapas/resultados/ETAPA-01.md") + check_links("auditoria_por_etapas/resultados/ESTADO_GENERAL.md")
    etapa01_text = (ROOT / "auditoria_por_etapas/resultados/ETAPA-01.md").read_text(encoding="utf-8")
    estado_text = (ROOT / "auditoria_por_etapas/resultados/ESTADO_GENERAL.md").read_text(encoding="utf-8")
    cursor_present = (
        "01-F" in etapa01_text and "01-F" in estado_text
        and "SEC-15-" in etapa01_text and "SEC-15-" in estado_text
    )

    # Secret sanitization scan over 01-F text evidence & reports
    secret_tokens = ["csrfmiddlewaretoken", "audit01f_sessionid=", "audit01f_csrftoken="]
    key_txt = (DATA / ".django-key").read_text(encoding="utf-8").strip() if (DATA / ".django-key").exists() else ""
    if key_txt:
        secret_tokens.append(key_txt)
    secret_hits: list[str] = []
    scan_paths = list(OUT.rglob("*.json")) + list(OUT.rglob("*.txt")) + [
        ROOT / "auditoria_por_etapas/resultados/ETAPA-01.md",
        ROOT / "auditoria_por_etapas/resultados/ESTADO_GENERAL.md",
        ROOT / "auditoria_por_etapas/resultados/soporte/01-F-inventario-y-disposiciones.md",
    ]
    for sp in scan_paths:
        if sp.is_file():
            content = sp.read_text(encoding="utf-8", errors="replace")
            for tok in secret_tokens:
                # ignore literal token names in probe IDs/keys by checking = assignment or key material
                if tok == key_txt and tok in content:
                    secret_hits.append(f"{sp.relative_to(ROOT)}: django-key")
                elif tok.endswith("=") and tok in content:
                    secret_hits.append(f"{sp.relative_to(ROOT)}: {tok}")

    passed = (
        not doc_errors
        and not derived_mismatch
        and not scope_delta
        and protected_equal
        and not port_8782_open
        and not cred_file_present
        and not broken_links
        and cursor_present
        and not secret_hits
    )
    report = {
        "primary_sha256": hashlib.sha256((ROOT / "08_Historias_de_Usuario.md").read_bytes()).hexdigest(),
        "build_before_sha256": before["build_sha256"],
        "build_after_sha256": build_after_sha,
        "scope_source_delta": scope_delta,
        "document_errors": doc_errors,
        "derived_mismatch": derived_mismatch,
        "protected_databases_equal": protected_equal,
        "port_8782_open": port_8782_open,
        "cred_file_present": cred_file_present,
        "broken_links": broken_links,
        "cursor_present": cursor_present,
        "secret_hits": secret_hits,
        "passed": passed,
    }
    (OUT / "verificacion-final-01f.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
