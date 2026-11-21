"""Ejecución verificada en servidor (check, makemigrations y suite completa aislada SQLite :memory:) para Sublote 02-E."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "r1-pmv/manage.py").is_file())
PROJECT = ROOT / "r1-pmv"
PYTHON = PROJECT / ".venv/Scripts/python.exe"
OUT = ROOT / "auditoria_por_etapas/resultados/evidencias/02-E-20261114/servidor"
OUT.mkdir(parents=True, exist_ok=True)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_cmd(name: str, args: list[str], env: dict[str, str]) -> dict:
    proc = subprocess.run(
        [str(PYTHON), "manage.py", *args],
        cwd=str(PROJECT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    (OUT / f"{name}.stdout.log").write_text(proc.stdout, encoding="utf-8")
    (OUT / f"{name}.stderr.log").write_text(proc.stderr, encoding="utf-8")
    return {
        "command": f"python manage.py {' '.join(args)}",
        "returncode": proc.returncode,
        "passed": proc.returncode == 0,
        "stdout_tail": proc.stdout.splitlines()[-20:],
        "stderr_tail": proc.stderr.splitlines()[-20:],
    }


def main() -> None:
    prod_db = PROJECT / "r1_pmv.sqlite3"
    db_before = sha256_file(prod_db)

    env = os.environ.copy()
    env["APP_ENV"] = "test"
    env["DJANGO_SECRET_KEY"] = secrets.token_urlsafe(48)
    env["PYTHONUTF8"] = "1"

    started = datetime.now(timezone.utc).isoformat()
    results = {
        "started_utc": started,
        "stage": "02-E",
        "check": run_cmd("manage_check", ["check"], env),
        "makemigrations_check": run_cmd(
            "makemigrations_check",
            ["makemigrations", "--check", "--dry-run"],
            env,
        ),
        "full_test_suite": run_cmd(
            "full_test_suite",
            ["test", "identity", "app_platform", "catalog", "inventory", "cash", "sales", "tests", "-v", "2"],
            env,
        ),
    }
    finished = datetime.now(timezone.utc).isoformat()
    db_after = sha256_file(prod_db)

    results["finished_utc"] = finished
    results["prod_db_unchanged"] = db_before == db_after
    results["prod_db_sha256"] = db_after
    results["all_passed"] = all(
        results[k]["passed"] for k in ("check", "makemigrations_check", "full_test_suite")
    ) and results["prod_db_unchanged"]

    (OUT / "resumen.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Informe de verificación en servidor · Sublote 02-E (14/11/2026)",
        "",
        f"- **Inicio UTC:** `{started}`",
        f"- **Fin UTC:** `{finished}`",
        f"- **Base protegida (`r1_pmv.sqlite3`) intacta:** `{results['prod_db_unchanged']}` (`sha256`: `{db_after}`)",
        "",
        "## Comandos ejecutados",
        "",
        f"1. `{results['check']['command']}` -> código `{results['check']['returncode']}` (`{'OK' if results['check']['passed'] else 'FALLO'}`)",
        f"2. `{results['makemigrations_check']['command']}` -> código `{results['makemigrations_check']['returncode']}` (`{'OK' if results['makemigrations_check']['passed'] else 'FALLO'}`)",
        f"3. `{results['full_test_suite']['command']}` -> código `{results['full_test_suite']['returncode']}` (`{'OK' if results['full_test_suite']['passed'] else 'FALLO'}`)",
        "",
        "## Cierre de suite completa",
        "",
        "```text",
        *results["full_test_suite"]["stderr_tail"][-10:],
        "```",
    ]
    (OUT / "INFORME.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"ok": results["all_passed"], "db_unchanged": results["prod_db_unchanged"]}, ensure_ascii=False))
    if not results["all_passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
