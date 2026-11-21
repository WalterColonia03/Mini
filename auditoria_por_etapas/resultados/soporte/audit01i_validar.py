"""Validate 01-I traceability without reclassifying earlier stages."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "auditoria_por_etapas/resultados"
OUT = RESULTS / "evidencias/01-I-20261115"
OLD = OUT / "documentos-antes"
APP = ROOT / "r1-pmv"

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def data(name: str):
    return json.loads((OUT / name).read_text(encoding="utf-8"))

checks = {}
original_report = (OLD / "auditoria_por_etapas__resultados__ETAPA-01.md").read_bytes()
report = (RESULTS / "ETAPA-01.md").read_bytes()
checks["reporte_anterior_preservado_byte_a_byte"] = report.endswith(original_report)
new_adenda = report[:-len(original_report)].decode("utf-8")
checks["adenda_y_cursor"] = 'id="vigente-01-i"' in new_adenda and "01-J-PERIMETRO-RETENCION-IDNA-01" in new_adenda

old_status = (OLD / "auditoria_por_etapas__resultados__ESTADO_GENERAL.md").read_text(encoding="utf-8")
new_status = (RESULTS / "ESTADO_GENERAL.md").read_text(encoding="utf-8")
row = re.compile(r"(?m)^\| \[(\d\d)\]\(ETAPA-\d\d\.md[^\n]*")
old_rows = {m.group(1): m.group(0) for m in row.finditer(old_status)}
new_rows = {m.group(1): m.group(0) for m in row.finditer(new_status)}
other_rows = [k for k in old_rows if k not in {"01", "15"}]
checks["filas_otros_modulos_intactas"] = bool(other_rows) and all(old_rows[k] == new_rows.get(k) for k in other_rows)
checks["fila_15_solo_corrige_rn"] = old_rows["15"].replace("`/admin/login/` elude `RN-18`", "`/admin/login/` elude `RN-17`") == new_rows["15"]

sources = [(RESULTS / "ETAPA-01.md", new_adenda), (RESULTS / "soporte/01-I-inventario-y-disposiciones.md", (RESULTS / "soporte/01-I-inventario-y-disposiciones.md").read_text(encoding="utf-8"))]
for name in ("02_Diseno_Tecnico_R1_PMV.md", "16_Task_Breakdown.md", "21_Alcance_Actual_y_Diferencias.md"):
    path = ROOT / name
    content = path.read_text(encoding="utf-8")
    sections = content.split("\n## ", 2)
    sources.append((path, sections[1] if len(sections) > 1 else ""))
source08 = (ROOT / "08_Historias_de_Usuario.md").read_text(encoding="utf-8")
sources.append((ROOT / "08_Historias_de_Usuario.md", "\n".join(line for line in source08.splitlines() if "01-I" in line)))
missing = []
link_count = 0
for file, content in sources:
    for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)]+)\)", content):
        if target.startswith(("http://", "https://", "mailto:", "#")):
            continue
        path_text = unquote(target.split("#", 1)[0].split("?", 1)[0])
        if not path_text:
            continue
        link_count += 1
        path = (file.parent / path_text).resolve()
        if not path.exists():
            missing.append({"origen": file.relative_to(ROOT).as_posix(), "destino": target})
checks["enlaces_nuevos_locales_existen"] = not missing

before, final = data("build-antes.json"), data("build-final.json")
actual_sources = {name: sha(APP / name) for name in final["fuentes"]}
# The baseline is ordered using Windows Path ordering; preserve its manifest order.
canonical = "".join(f"{name}\0{digest}\n" for name, digest in actual_sources.items()).encode("utf-8")
checks["build_final_fuentes"] = actual_sources == final["fuentes"] and hashlib.sha256(canonical).hexdigest() == final["build_sha256"]
checks["build_01h_coincide_entrada"] = data("revision-evidencia-anterior.json")["build_previo_coincide_con_inicio_01i"]
checks["plan_08_sha"] = sha(ROOT / "08_Historias_de_Usuario.md") == "57e9fcbb4d80385e2c89445eb1edb8cdf35631237bb1ad99b7c48ef0188a609c"
checks["bases_protegidas"] = all(sha(ROOT / name) == digest for name, digest in final["documentos_y_bases"].items() if name.endswith(".sqlite3"))
checks["final_services_coincide_con_pg"] = data("postgresql-01i-latest.json")["fuentes_sha256"]["identity/services.py"] == sha(APP / "identity/services.py")
checks["pg_5_sin_fallos"] = len(data("postgresql-01i-latest.json")["escenarios"]) == 5 and all(e["resultado"] == "PASS" for e in data("postgresql-01i-latest.json")["escenarios"])
checks["espera_real_y_contador"] = all(c["ok"] for c in data("espera-real-01i.json")["checks"]) and data("espera-real-01i.json")["checks"][-1]["elapsed_since_fifth_event_seconds"] >= 900 and data("despues-espera.json")["fallos"] == 0 and data("despues-espera.json")["locked_until_utc"] is None
checks["chrome_final_sin_fallos"] = all(all(c["ok"] for c in data(name)["checks"]) for name in ("chrome-roles-final.json", "chrome-efecto-entre-roles-final.json", "admin-final.json", "foco-y-errores-final.json"))
checks["regresion_657"] = bool(re.search(r"Ran 657 tests in [\d.]+s\s+OK", (OUT / "regresion-integrada-final.txt").read_text(encoding="utf-8")))
checks["regresion_focal_11"] = bool(re.search(r"Ran 11 tests in [\d.]+s\s+OK", (OUT / "regresion-seguridad-final.txt").read_text(encoding="utf-8")))
checks["cierre_operativo"] = data("cierre-operativo.json")["coincidencias"] == [] and all(data("cierre-operativo.json")["puertos_loopback_cerrados"].values())
generator = subprocess.run([str(APP / ".venv/Scripts/python.exe"), "-X", "utf8", "-B", str(RESULTS / "fuente_unica_20261112/regenerar_vistas.py"), "--check"], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
checks["vistas_derivadas"] = generator.returncode == 0
result = {
    "capturado_utc": datetime.now(timezone.utc).isoformat(),
    "checks": checks,
    "enlaces_locales_nuevos_revisados": link_count,
    "enlaces_faltantes": missing,
    "filas_de_otras_etapas_revisadas": len(other_rows),
    "generador": {"exit": generator.returncode, "stdout": generator.stdout.strip(), "stderr": generator.stderr.strip()},
    "limitaciones": "Existencia de archivos, no validez semántica de todos los enlaces externos, anclas ni de revisiones humanas no realizadas.",
}
(OUT / "validacion-final.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"checks": len(checks), "fallos": [k for k, v in checks.items() if not v], "enlaces": link_count, "faltantes": missing}, ensure_ascii=False))
if not all(checks.values()):
    raise SystemExit(1)
