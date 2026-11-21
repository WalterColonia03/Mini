"""Stage 09 Revalidation Browser Harness (2026-11-14) in isolated SQLite.

Reuses audit09_settings.py without touching operational or archived databases.
Outputs to auditoria_por_etapas/resultados/evidencias/09-reval-20261114/browser/.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import secrets
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SUPPORT = Path(__file__).resolve().parent
sys.path.insert(0, str(SUPPORT))

import audit09_run as base  # noqa: E402

ROOT = base.ROOT
APP = base.APP
RESULTS = base.RESULTS
REVAL_OUT = RESULTS / "evidencias" / "09-reval-20261114"


def reval_protected_hashes() -> dict[str, str | None]:
    protected = [
        *APP.glob("*.sqlite3"),
        *sorted(
            p
            for p in (RESULTS / "datos").rglob("*.sqlite3")
            if p.parent.name.startswith("etapa09-") and not p.parent.name.startswith("etapa09-reval-")
        ),
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]
    return {str(p.relative_to(ROOT)): base.digest(p) if p.exists() else None for p in protected}


def r1_source_hash() -> tuple[int, str]:
    ps = sorted(
        p
        for p in APP.rglob("*")
        if p.is_file()
        and not any(x in p.parts for x in (".venv", "__pycache__", "staticfiles", ".pytest_cache", ".mypy_cache", ".git"))
        and p.suffix not in (".sqlite3", ".pyc")
    )
    h = hashlib.sha256()
    for p in ps:
        h.update(f"{p.relative_to(APP).as_posix()}:{base.digest(p)}\n".encode("utf-8"))
    return len(ps), h.hexdigest()


def run_reval_checks() -> int:
    start_hashes = reval_protected_hashes()
    start_cnt, start_build = r1_source_hash()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)
    run_dir = RESULTS / "datos" / f"etapa09-reval-checks-{stamp}"
    out_dir = REVAL_OUT / "checks"
    run_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    base.write(run_dir / "marker.json", {"run": run_dir.name, "created_utc": stamp})
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")
    os.environ.update(AUDIT09_RUN_DIR=str(run_dir), AUDIT09_OUT=str(out_dir), AUDIT09_DEFAULT_COOKIES="1")
    base.setup(default_cookies=True)
    from django.core.management import execute_from_command_line

    buf = io.StringIO()
    exit_code = 0
    old_cwd = Path.cwd()
    try:
        os.chdir(APP)
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            for argv in (["manage.py", "check"], ["manage.py", "makemigrations", "--check", "--dry-run"]):
                try:
                    execute_from_command_line(argv)
                except SystemExit as exc:
                    exit_code = max(exit_code, int(exc.code or 0))
    finally:
        os.chdir(old_cwd)
    out_text = buf.getvalue()
    (out_dir / "checks.txt").write_text(out_text, encoding="utf-8")
    end_cnt, end_build = r1_source_hash()
    end_hashes = {k: (base.digest(ROOT / k) if (ROOT / k).exists() else None) == v for k, v in start_hashes.items()}
    summary = {
        "stamp_utc": stamp,
        "exit_code": exit_code,
        "output": out_text,
        "source_count": end_cnt,
        "source_build_hash": end_build,
        "source_unchanged": (start_cnt == end_cnt and start_build == end_build),
        "protected_unchanged": all(end_hashes.values()),
    }
    base.write(out_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if (exit_code == 0 and summary["source_unchanged"] and summary["protected_unchanged"]) else 1


def run_reval_tests(tag: str, targets: list[str]) -> int:
    start_hashes = reval_protected_hashes()
    start_cnt, start_build = r1_source_hash()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)
    run_dir = RESULTS / "datos" / f"etapa09-reval-{tag}-{stamp}"
    out_dir = REVAL_OUT / tag
    run_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    base.write(run_dir / "marker.json", {"run": run_dir.name, "created_utc": stamp})
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")
    os.environ.update(AUDIT09_RUN_DIR=str(run_dir), AUDIT09_OUT=str(out_dir), AUDIT09_DEFAULT_COOKIES="1")
    base.setup(default_cookies=True)
    from django.core.management import execute_from_command_line

    buf = io.StringIO()
    argv = ["manage.py", "test", *targets, "-v", "2"]
    exit_code = 0
    old_cwd = Path.cwd()
    started = time.perf_counter()
    try:
        os.chdir(APP)
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            try:
                execute_from_command_line(argv)
            except SystemExit as exc:
                exit_code = int(exc.code or 0)
    finally:
        os.chdir(old_cwd)
    elapsed = round(time.perf_counter() - started, 3)
    out_text = buf.getvalue()
    (out_dir / "test_output.txt").write_text(out_text, encoding="utf-8")
    end_cnt, end_build = r1_source_hash()
    end_hashes = {k: (base.digest(ROOT / k) if (ROOT / k).exists() else None) == v for k, v in start_hashes.items()}
    summary = {
        "stamp_utc": stamp,
        "targets": targets,
        "exit_code": exit_code,
        "elapsed_seconds": elapsed,
        "tail": out_text.strip().splitlines()[-12:],
        "source_count": end_cnt,
        "source_build_hash": end_build,
        "source_unchanged": (start_cnt == end_cnt and start_build == end_build),
        "protected_unchanged": all(end_hashes.values()),
    }
    base.write(out_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if (exit_code == 0 and summary["source_unchanged"] and summary["protected_unchanged"]) else 1


def run_reval_browser() -> int:
    start_hashes = reval_protected_hashes()
    start_cnt, start_build = r1_source_hash()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)
    run_dir = RESULTS / "datos" / f"etapa09-reval-browser-{stamp}"
    out_dir = REVAL_OUT / "browser"
    run_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    base.write(run_dir / "marker.json", {"run": run_dir.name, "created_utc": stamp})
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")

    os.environ.update(
        AUDIT09_RUN_DIR=str(run_dir),
        AUDIT09_OUT=str(out_dir),
        AUDIT09_PYTHON=sys.executable,
    )
    result = {
        "action": "reval-browser",
        "run": run_dir.name,
        "started_utc": stamp,
        "evidence": str(out_dir.relative_to(ROOT)),
    }
    server = None
    stderr_fh = None
    port = 0
    try:
        base.setup(default_cookies=False)
        base.prepare_empty_migrated_db()
        base.prepare_stage09_fixtures(run_dir, out_dir)
        base.write(out_dir / "orm-initial.json", base.snapshot())

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        os.environ["AUDIT09_PORT"] = str(port)
        stderr_log = out_dir / "server-stderr.log"
        stderr_fh = stderr_log.open("w", encoding="utf-8")
        server = subprocess.Popen(
            [sys.executable, str(SUPPORT / "audit09_run.py"), "serve"],
            stdout=subprocess.DEVNULL,
            stderr=stderr_fh,
        )
        for _ in range(100):
            with socket.socket() as sock:
                if sock.connect_ex(("127.0.0.1", port)) == 0:
                    break
            if server.poll() is not None:
                raise RuntimeError("Django runserver terminated early")
            time.sleep(0.1)

        child = subprocess.run(
            ["node", str(SUPPORT / "audit09_reval_browser.cjs")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=240,
        )
        result.update(
            browser_exit=child.returncode,
            browser_output=child.stdout,
            browser_error=child.stderr,
        )
        base.write(out_dir / "orm-final.json", base.snapshot())
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error_message"] = str(exc)
        raise
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
            result["port_closed"] = False
            for _ in range(50):
                with socket.socket() as sock:
                    if sock.connect_ex(("127.0.0.1", port)) != 0:
                        result["port_closed"] = True
                        break
                time.sleep(0.1)
        if stderr_fh is not None:
            stderr_fh.close()
        end_cnt, end_build = r1_source_hash()
        result["protected_unchanged"] = {
            k: (base.digest(ROOT / k) if (ROOT / k).exists() else None) == v for k, v in start_hashes.items()
        }
        result["source_count"] = end_cnt
        result["source_build_hash"] = end_build
        result["source_unchanged"] = (start_cnt == end_cnt and start_build == end_build)
        result["original_sha256"] = base.digest(base.APP / "r1_pmv.sqlite3")
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        base.write(out_dir / "result.json", result)
        print(
            base.json.dumps(
                {
                    "evidence": result["evidence"],
                    "browser_exit": result.get("browser_exit"),
                    "port_closed": result.get("port_closed"),
                    "source_unchanged": result["source_unchanged"],
                    "source_build_hash": end_build,
                    "protected_unchanged": all(result["protected_unchanged"].values()),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    if (
        result.get("browser_exit", 1) != 0
        or not result.get("port_closed")
        or not result["source_unchanged"]
        or not all(result["protected_unchanged"].values())
    ):
        return 1
    return 0


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "browser"
    if action == "checks":
        raise SystemExit(run_reval_checks())
    if action == "tests":
        tag = sys.argv[2]
        targets = sys.argv[3:]
        raise SystemExit(run_reval_tests(tag, targets))
    if action == "browser":
        raise SystemExit(run_reval_browser())
    raise SystemExit(f"Unknown action: {action}")
