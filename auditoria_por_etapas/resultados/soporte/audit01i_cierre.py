"""Check this sublot's own outputs and retire only its temporary fixture credentials."""
from __future__ import annotations

import hashlib
import json
import socket
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "auditoria_por_etapas/resultados/datos/01-I-20261115"
OUT = ROOT / "auditoria_por_etapas/resultados/evidencias/01-I-20261115"
expected = (ROOT / "auditoria_por_etapas/resultados/datos/01-I-20261115").resolve()
if DATA.resolve() != expected or DATA.name != "01-I-20261115":
    raise SystemExit("Carpeta de datos inesperada")

secrets = [(DATA / ".django-key").read_text(encoding="utf-8").strip()]
for name in (".credentials.json", ".roles-final.json"):
    document = json.loads((DATA / name).read_text(encoding="utf-8"))
    secrets.extend(row["password"] for row in document.values() if isinstance(row, dict) and "password" in row)
secrets = sorted({value for value in secrets if len(value) >= 12})

scanned = 0
matches = []
for path in OUT.rglob("*"):
    if not path.is_file() or path.suffix.lower() not in {".json", ".txt", ".log", ".md", ".py", ".cjs", ".diff"}:
        continue
    body = path.read_bytes()
    scanned += 1
    if any(value.encode("utf-8") in body for value in secrets):
        matches.append(path.relative_to(OUT).as_posix())
if matches:
    print(json.dumps({"archivos_con_coincidencia": matches, "secreto_impreso": False}, ensure_ascii=False))
    raise SystemExit("Se conservan credenciales temporales hasta resolver coincidencias")

def port_closed(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.7)
        return sock.connect_ex(("127.0.0.1", port)) != 0

ports = {str(port): port_closed(port) for port in (8796, 64735)}
if not all(ports.values()):
    raise SystemExit("El puerto de una instancia propia sigue abierto")

before = json.loads((OUT / "build-antes.json").read_text(encoding="utf-8"))
after = json.loads((OUT / "build-final.json").read_text(encoding="utf-8"))
protected_before = before["documentos_y_bases"]
protected_after = after["documentos_y_bases"]
db_names = sorted(k for k in protected_before if k.endswith(".sqlite3"))
unchanged = {k: protected_before[k] == protected_after.get(k) for k in db_names}
if not all(unchanged.values()):
    raise SystemExit("Una base protegida cambió; conservar evidencia y revisar")

for name in (".credentials.json", ".roles-final.json"):
    path = (DATA / name).resolve()
    if path.parent != expected or path.name != name:
        raise SystemExit("Ruta temporal inesperada")
    path.unlink()

result = {
    "capturado_utc": datetime.now(timezone.utc).isoformat(),
    "fuente_de_secretos": "solo claves y contraseñas ficticias creadas para 01-I",
    "secretos_distintos_examinados": len(secrets),
    "archivos_textuales_examinados": scanned,
    "coincidencias": [],
    "limitacion": "No es revisión universal ni OCR de imágenes; no examina otros secretos desconocidos.",
    "credenciales_temporales_retiradas": [".credentials.json", ".roles-final.json"],
    "llave_ficticia_conservada_en_datos_ignorados": True,
    "puertos_loopback_cerrados": ports,
    "bases_preexistentes_sin_cambio": unchanged,
    "sha256_bd_principal": hashlib.sha256((ROOT / "r1-pmv/r1_pmv.sqlite3").read_bytes()).hexdigest(),
}
(OUT / "cierre-operativo.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"archivos_revisados": scanned, "coincidencias": len(matches), "puertos_cerrados": ports, "bases_sin_cambio": all(unchanged.values())}, ensure_ascii=False))
