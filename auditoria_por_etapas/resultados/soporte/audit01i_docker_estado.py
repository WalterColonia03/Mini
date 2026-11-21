"""Record whether the local Docker daemon is available without building an image."""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[3]
result = subprocess.run(
    ["docker", "version", "--format", "{{.Server.Version}}"],
    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
)
record = {
    "capturado_utc": datetime.now(timezone.utc).isoformat(),
    "consulta": "docker version --format {{.Server.Version}}",
    "exit_code": result.returncode,
    "motor_responde": result.returncode == 0,
    "version_motor": result.stdout.strip() if result.returncode == 0 else None,
    "conexion_a_daemon_fallida": "failed to connect" in result.stderr.lower(),
    "imagen_construida": False,
}
output = root / "auditoria_por_etapas/resultados/evidencias/01-I-20261115/docker-estado.json"
output.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(record, ensure_ascii=False))
