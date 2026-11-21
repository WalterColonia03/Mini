"""Run settled Stage 11 Django checks, Stage 11 suite, and full regression suite cleanly."""
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
SUPPORT = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]).resolve()
OUT.mkdir(parents=True, exist_ok=True)
PYTHON = str(PROJECT / ".venv/Scripts/python.exe")

STAGE11_LABELS = [
    "sales.test_audit11_checkout",
    "sales.test_audit14f_allocations",
    "sales.test_audit14closure_retry",
    "cash.test_audit14closure_money",
    "cash.test_audit09_cash",
    "sales.tests",
    "tests.test_audit14_integration",
    "tests.test_audit14c_edge_cases",
]


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_snapshot() -> dict:
    exts = {".py", ".html", ".css", ".js"}
    files = sorted(
        p
        for p in PROJECT.rglob("*")
        if p.is_file() and p.suffix in exts and ".venv" not in p.parts and "__pycache__" not in p.parts
    )
    manifest = {p.relative_to(PROJECT).as_posix(): sha_bytes(p.read_bytes()) for p in files}
    h = hashlib.sha256()
    s11_h = hashlib.sha256()
    s11_prefixes = ("sales/", "cash/", "inventory/")
    for rel, p in [(p.relative_to(PROJECT).as_posix(), p) for p in files]:
        data = p.read_bytes()
        h.update((rel + "\n").encode("utf-8"))
        h.update(data)
        if rel.startswith(s11_prefixes):
            s11_h.update((rel + "\n").encode("utf-8"))
            s11_h.update(data)
    return {
        "count": len(files),
        "sha256": h.hexdigest(),
        "stage11_modules_sha256": s11_h.hexdigest(),
        "files": manifest,
    }


def run_manage(args: list[str], log_name: str) -> dict:
    env = os.environ.copy()
    env.update(
        {
            "PYTHONPATH": f"{PROJECT}{os.pathsep}{SUPPORT}",
            "AUDIT11B_SECRET_KEY": secrets.token_urlsafe(48),
            "APP_ENV": "test",
            "DATABASE_URL": "sqlite",
            "DJANGO_DEBUG": "false",
        }
    )
    t0 = datetime.now(timezone.utc)
    proc = subprocess.run(
        [PYTHON, "manage.py", *args, "--settings=audit11b_test_settings"],
        cwd=PROJECT,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    t1 = datetime.now(timezone.utc)
    combined = (proc.stdout or "") + ("\n" if proc.stdout and proc.stderr else "") + (proc.stderr or "")
    (OUT / log_name).write_text(combined, encoding="utf-8")
    return {
        "args": args,
        "returncode": proc.returncode,
        "started_utc": t0.isoformat(),
        "finished_utc": t1.isoformat(),
        "duration_s": round((t1 - t0).total_seconds(), 2),
        "tail": combined.splitlines()[-12:],
    }


def diff_manifests(a: dict[str, str], b: dict[str, str]) -> dict:
    changed = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    added = sorted(set(b) - set(a))
    removed = sorted(set(a) - set(b))
    return {"changed": changed, "added": added, "removed": removed}


def main() -> int:
    prod_db = PROJECT / "r1_pmv.sqlite3"
    db_before = sha_bytes(prod_db.read_bytes())
    snap_before = build_snapshot()

    results = {
        "executed_utc": datetime.now(timezone.utc).isoformat(),
        "prod_db_before": db_before,
        "build_before": {
            "count": snap_before["count"],
            "sha256": snap_before["sha256"],
            "stage11_modules_sha256": snap_before["stage11_modules_sha256"],
        },
        "steps": {},
    }

    results["steps"]["check"] = run_manage(["check"], "01-check.txt")
    results["steps"]["makemigrations_check"] = run_manage(["makemigrations", "--check", "--dry-run"], "02-makemigrations.txt")
    results["steps"]["stage11_tests"] = run_manage(["test", *STAGE11_LABELS, "--verbosity=2"], "03-stage11-tests.txt")
    snap_mid = build_snapshot()
    results["stage11_diff_during_subset"] = diff_manifests(snap_before["files"], snap_mid["files"])

    results["steps"]["full_suite"] = run_manage(["test", "--verbosity=1"], "04-full-suite.txt")
    snap_after = build_snapshot()
    db_after = sha_bytes(prod_db.read_bytes())

    full_diff = diff_manifests(snap_before["files"], snap_after["files"])
    results["prod_db_after"] = db_after
    results["prod_db_unchanged"] = db_before == db_after
    results["build_after"] = {
        "count": snap_after["count"],
        "sha256": snap_after["sha256"],
        "stage11_modules_sha256": snap_after["stage11_modules_sha256"],
    }
    results["sources_stable"] = snap_before["sha256"] == snap_after["sha256"]
    results["stage11_modules_stable"] = snap_before["stage11_modules_sha256"] == snap_after["stage11_modules_sha256"]
    results["full_diff"] = full_diff

    summary_path = OUT / "server_summary.json"
    summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    ok = (
        results["prod_db_unchanged"]
        and all(step["returncode"] == 0 for step in results["steps"].values())
    )
    print(
        json.dumps(
            {
                "ok": ok,
                "check_rc": results["steps"]["check"]["returncode"],
                "mig_rc": results["steps"]["makemigrations_check"]["returncode"],
                "stage11_rc": results["steps"]["stage11_tests"]["returncode"],
                "full_rc": results["steps"]["full_suite"]["returncode"],
                "sources_stable": results["sources_stable"],
                "stage11_modules_stable": results["stage11_modules_stable"],
                "prod_db_unchanged": results["prod_db_unchanged"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
