"""Orquestador reproducible de pruebas HTTP, ORM y Chrome real contra servidor vivo en puerto 8767."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from pathlib import Path


SOPORTE_DIR = Path(__file__).resolve().parent
RESULTADOS_DIR = SOPORTE_DIR.parent
REPO_ROOT = RESULTADOS_DIR.parent.parent
EVIDENCIAS_DIR = RESULTADOS_DIR / "evidencias"
PYTHON_EXE = sys.executable


def wait_for_port(host: str, port: int, timeout: float = 15.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            if sock.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.25)
    return False


def run_step(cmd: list[str], label: str) -> str:
    print(f"=== [{label}] {' '.join(cmd)} ===", flush=True)
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise RuntimeError(f"Step {label} failed with exit code {proc.returncode}")
    return proc.stdout


def main() -> int:
    EVIDENCIAS_DIR.mkdir(parents=True, exist_ok=True)
    audit02_py = str(SOPORTE_DIR / "audit02.py")

    run_step([PYTHON_EXE, audit02_py, "prepare", "--reset"], "prepare-initial")

    server = subprocess.Popen(
        [PYTHON_EXE, audit02_py, "serve", "--host", "127.0.0.1", "--port", "8767"],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        if not wait_for_port("127.0.0.1", 8767, timeout=15.0):
            raise RuntimeError("El servidor aislado no abrió el puerto 8767 a tiempo.")

        proof_out = run_step(
            [PYTHON_EXE, audit02_py, "proof", "--host", "127.0.0.1", "--port", "8767"],
            "proof-live-server",
        )
        (EVIDENCIAS_DIR / "02-proof-servidor-vivo.json").write_text(proof_out, encoding="utf-8")

        run_step([PYTHON_EXE, str(SOPORTE_DIR / "audit02_http.py")], "http-orm-checks")

        run_step([PYTHON_EXE, audit02_py, "prepare", "--reset"], "prepare-chrome-02a")
        run_step(["node", str(SOPORTE_DIR / "audit02_chrome_sesion.cjs")], "chrome-sublot-02a")

        run_step([PYTHON_EXE, audit02_py, "prepare", "--reset"], "prepare-chrome-02b")
        run_step(["node", str(SOPORTE_DIR / "audit02_chrome_empleados.cjs")], "chrome-sublot-02b")

        inspect_out = run_step([PYTHON_EXE, audit02_py, "inspect"], "inspect-final-orm")
        (EVIDENCIAS_DIR / "02-orm-estado-final.json").write_text(inspect_out, encoding="utf-8")
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)

    # Verificar que el puerto 8767 haya quedado cerrado
    time.sleep(0.3)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        port_open = sock.connect_ex(("127.0.0.1", 8767)) == 0
    if port_open:
        raise RuntimeError("El puerto 8767 siguió abierto tras detener el servidor.")

    print(
        json.dumps(
            {
                "stage": "ETAPA-02",
                "live_run": "OK",
                "port_8767_closed_after_run": not port_open,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
