"""Read-only audit of 01-H document links, evidence and preservation."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import socket
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "auditoria_por_etapas/resultados"
EVIDENCE = RESULTS / "evidencias/01-H-20261115"
BACKUP = EVIDENCE / "documentos-antes"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


report = (RESULTS / "ETAPA-01.md").read_bytes()
old_report = (BACKUP / "auditoria_por_etapas__resultados__ETAPA-01.md").read_bytes()
marker = "# Adenda vigente de ETAPA-01 · 14/11/2026 · 01-F".encode()
prefix, prior = report.split(marker, 1)
report_historico_identico = marker + prior == old_report

status = (RESULTS / "ESTADO_GENERAL.md").read_bytes().decode("utf-8")
old_status = (BACKUP / "auditoria_por_etapas__resultados__ESTADO_GENERAL.md").read_bytes().decode("utf-8")
old_row = re.findall(r"(?m)^\| \[01\]\(ETAPA-01\.md[^\r\n]*", old_status)
new_row = re.findall(r"(?m)^\| \[01\]\(ETAPA-01\.md[^\r\n]*", status)
assert len(old_row) == len(new_row) == 1
restored_status, n = re.subn(r"(?m)^\| \[01\]\(ETAPA-01\.md[^\r\n]*", lambda _: old_row[0], status)
assert n == 1
restored_status, n = re.subn(r"\r\n\*\*Actualización 01-H \(15/11/2026\):\*\*[^\r\n]*\r\n", "", restored_status)
restored_status = restored_status.replace("(sublotes 01-H / 02-E / 07-B / 15-A / revalidaciones)", "(sublotes 01-F / 02-E / 07-B / 15-A / revalidaciones)", 1)
status_historico_identico_salvo_fila_y_adenda = n == 1 and restored_status == old_status

source_sha = sha(ROOT / "08_Historias_de_Usuario.md")
derived = {}
for name in ("07_Reglas_de_Negocio.md", "09_Product_Backlog.md", "03_Matriz_de_Trazabilidad_y_Pruebas.md"):
    derived[name] = source_sha in (ROOT / name).read_text(encoding="utf-8")[:500]
index = read_json(RESULTS / "fuente_unica_20261112/INDICE_DERIVADO.json")
spec = importlib.util.spec_from_file_location("generator01h", RESULTS / "fuente_unica_20261112/regenerar_vistas.py")
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)
source, stories, cases, criteria = module.parse()
source_errors = module.document_errors(source, stories, cases, criteria)

targets = [
    (RESULTS / "ETAPA-01.md", prefix.decode("utf-8")),
    (RESULTS / "soporte/01-H-inventario-y-disposiciones.md", (RESULTS / "soporte/01-H-inventario-y-disposiciones.md").read_text(encoding="utf-8")),
    (RESULTS / "ESTADO_GENERAL.md", "\n".join(new_row + re.findall(r"(?m)^\*\*Actualización 01-H[^\r\n]*", status))),
]
missing = []
links_count = 0
for base, text in targets:
    for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
        raw = target.strip().split("#", 1)[0]
        if not raw or re.match(r"^(?:https?:|mailto:)", raw):
            continue
        links_count += 1
        if not (base.parent / unquote(raw)).exists():
            missing.append({"documento": base.name, "destino": raw})

before = read_json(EVIDENCE / "build-antes.json")
after = read_json(EVIDENCE / "build-ultimo.json")
source_changes = sorted(k for k in set(before["fuentes"]) | set(after["fuentes"]) if before["fuentes"].get(k) != after["fuentes"].get(k))
current_changed = sorted(name for name, digest in after["fuentes"].items() if not (ROOT / "r1-pmv" / name).is_file() or sha(ROOT / "r1-pmv" / name) != digest)
db_path = ROOT / "r1-pmv/r1_pmv.sqlite3"
db_unchanged = sha(db_path) == before["documentos_y_bases"]["r1-pmv/r1_pmv.sqlite3"] == after["documentos_y_bases"]["r1-pmv/r1_pmv.sqlite3"]
wait = read_json(EVIDENCE / "espera-real-01h.json")
end = read_json(EVIDENCE / "despues-espera.json")
wait_checks = wait["checks"]
real_wait_ok = all(item["ok"] for item in wait_checks) and wait_checks[-1]["elapsed_since_fifth_event_seconds"] >= 900 and end["fallos"] == 0 and end["locked_until_utc"] is None
pg = read_json(EVIDENCE / "postgresql-01h-20261115T150253Z.json")
pg_ok = pg["resultado"].startswith("PASS") and len(pg["escenarios"]) == 5 and all(item.get("resultado") == "PASS" for item in pg["escenarios"])
test_text = (EVIDENCE / "tests-identity-final.txt").read_text(encoding="utf-8")
suite_ok = "Ran 83 tests" in test_text and re.search(r"(?m)^OK\s*$", test_text) is not None
ports = {}
for port in (8794, 8795):
    with socket.socket() as sock:
        sock.settimeout(1)
        ports[str(port)] = sock.connect_ex(("127.0.0.1", port)) != 0

result = {
    "08_sha256": source_sha,
    "08_sin_errores_de_esquema": not source_errors,
    "errores_08": source_errors,
    "conteos_planificacion": module.counts(source, stories, cases, criteria),
    "vistas_huella_08": derived,
    "indice_huella_08": index["source_sha256"] == source_sha,
    "informe_anterior_byte_a_byte": report_historico_identico,
    "estado_anterior_salvo_encabezado_resumen_y_fila_01": status_historico_identico_salvo_fila_y_adenda,
    "enlaces_locales_en_alcance": links_count,
    "enlaces_faltantes": missing,
    "cambios_en_fuentes_del_build": source_changes,
    "fuentes_modificadas_tras_manifestar_build_final": current_changed,
    "base_principal_sha256_constante_durante_01h": db_unchanged,
    "espera_real_y_reset_observados": real_wait_ok,
    "cinco_escenarios_pg_completados": pg_ok,
    "suite_focal_83_ok": suite_ok,
    "puertos_cerrados": ports,
    "credenciales_ficticias_temporales_retiradas": not (RESULTS / "datos/01-H-20261115/.credentials.json").exists(),
}
out = EVIDENCE / "validacion-final-3.json"
if out.exists():
    raise SystemExit("No se sobrescribe validación existente")
out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
assert not source_errors and all(derived.values()) and index["source_sha256"] == source_sha
assert report_historico_identico and status_historico_identico_salvo_fila_y_adenda and not missing
assert source_changes == ["identity/tests.py"] and not current_changed and db_unchanged
assert real_wait_ok and pg_ok and suite_ok and all(ports.values()) and result["credenciales_ficticias_temporales_retiradas"]
