"""Verify stage-00 artifacts and isolation; does not execute business stories.

Run from any directory with r1-pmv/.venv/Scripts/python.exe.
Previous reports are preserved when a subsequent verification differs.
"""
from __future__ import annotations

import ast
from collections import Counter
from contextlib import redirect_stdout
import csv
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.parse import unquote
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
RESULT = ROOT / "auditoria_por_etapas/resultados"
ANNEX = RESULT / "anexos"
EVIDENCE = RESULT / "evidencias"
TARGET = EVIDENCE / "00-cierre-verificacion-final.json"
checks = []


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def read_csv(name):
    with (ANNEX / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(name, observed, expected):
    checks.append({"comprobacion": name, "observado": observed,
                   "esperado": expected, "cumple": observed == expected})


def command(args):
    return subprocess.run(args, cwd=ROOT, text=True, encoding="utf-8",
                          errors="replace", capture_output=True, check=True).stdout


plan = read_json(ANNEX / "ETAPA-00-planificacion.json")
stories = plan["historias"]
check("HU con criterios", sum(bool(x["criterios"]) for x in stories), 74)
check("ideas sin criterios", sum(not x["criterios"] for x in stories), 8)
check("CA base", sum(len(x["criterios"]) for x in stories), 219)
check("HU R1", sum(x["seleccion"] == "R1 SELECCIONADO" for x in stories), 9)
check("CA matriz historica R1", len(plan["matriz_historica_r1"]), 41)
check("reglas", len(plan["reglas"]), 30)
check("tareas", len(plan["tareas"]), 67)
coverage = read_csv("ETAPA-00-cobertura.csv")
base = [r for r in coverage if r["tipo_registro"] == "CA_BASE"]
check("filas matriz cobertura", len(coverage), 236)
check("CA cobertura identificados sin duplicados", len({r["id"] for r in base}), 219)
check("CA con muestra parcial", sum(r["estado_revision"].startswith("PARCIAL") for r in base), 8)
check("CA no ejecutados", sum(r["estado_ejecucion"] == "NO EJECUTADO" for r in base), 211)
check("CA declarados cumple", sum(r["estado_revision"].startswith("CUMPLE") for r in base), 0)

code = read_csv("ETAPA-00-inventario-codigo.csv")
counts = Counter(r["tipo"] for r in code)
for key, expected in {"plantilla": 36, "modelo": 18, "prueba_definida": 191,
                      "formulario": 18, "campo_formulario": 42,
                      "campo_formulario_modelo": 11, "ruta": 41}.items():
    check("indice codigo: " + key, counts[key], expected)
check("ocurrencias codigo", len(code), 2446)
forms = read_json(ANNEX / "ETAPA-00-formularios-generados.json")
check("clases formulario generadas", len(forms["formularios"]), 18)
check("campos efectivos", sum(len(f["campos"]) for f in forms["formularios"]), 53)
check("campos gestion formset", len(forms["LotInputFormSet"]["campos_gestion"]), 4)
admin = read_json(ANNEX / "ETAPA-00-admin-metadatos.json")
for key, expected in {"patrones_totales": 106, "patrones_admin": 65,
                      "resolver_igual_al_corte_5nov": True, "sql": 0,
                      "peticiones_servidas": 0}.items():
    check("metadatos admin: " + key, admin[key], expected)
check("modelos registrados admin", len(admin["modelos"]), 9)
check("formularios tecnicos admin", len(admin["formularios_tecnicos"]), 3)

ui = read_csv("ETAPA-00-superficie-ui.csv")
check("localizaciones UI", len(ui), 2367)
origins = [r["fila_origen_desde_1"] for r in ui if r["fila_origen_desde_1"].isdigit()]
check("procedencias originales unicas UI", len(set(origins)), 1859)
check("localizaciones suplementarias UI", len(ui) - len(origins), 508)
invalid = []
line_counts = {}
for row in code + ui:
    source = ROOT / row["fuente"]
    if source not in line_counts:
        line_counts[source] = len(source.read_text(encoding="utf-8-sig").splitlines()) if source.exists() else 0
    if not 1 <= int(row["linea"]) <= line_counts[source]:
        invalid.append(row["fuente"] + ":" + row["linea"])
check("coordenadas invalidas codigo/UI", invalid, [])
check("UI sin etapa o comprobacion pendiente",
      sum(not r["etapa"] or not r["verificacion_pendiente"] for r in ui), 0)

sources = read_json(ANNEX / "ETAPA-00-fuentes-codigo.json")
check("hashes iniciales codigo", len(sources), 77)
check("codigo cambiado desde inventario",
      [p for p, digest in sources.items() if not (ROOT / p).exists() or sha(ROOT / p) != digest], [])
documental = read_json(ANNEX / "ETAPA-00-fuentes-revalidacion-20261109.json")
check("fuentes documentales y cambios previos con hash", len(documental["checked"]), 66)
check("fuentes documentales o cambios previos alterados",
      [r["path"] for r in documental["checked"] if sha(ROOT / r["path"]) != r["sha256_baseline"]], [])
baseline = read_json(ANNEX / "ETAPA-00-fuentes-inventario.json")["git"]
check("Git HEAD conservado", command(["git", "-C", str(ROOT / "r1-pmv"), "log", "-1", "--format=%H %cI %s"]).strip(), baseline["head"])
check("Git lista cambios conservada", command(["git", "-C", str(ROOT / "r1-pmv"), "status", "--porcelain", "--untracked-files=all"]).strip().splitlines(), baseline["status"])
prepared = read_json(EVIDENCE / "00-preparacion.json")
check("hash base original conservado", sha(ROOT / "r1-pmv/r1_pmv.sqlite3"), prepared["original_before"]["sha256"])

book = read_json(EVIDENCE / "00-libro-cotejo.json")
check("libro conservado", sha(ROOT / book["archivo"]), book["sha256"])
check("HU declaradas implementadas en libro", len(book["hu_declaradas_implementadas_celdas"]), 28)
check("HU declaradas pendientes en libro", len(book["hu_declaradas_pendientes_celdas"]), 46)
check("CA cotejados en libro", len(book["ca_declarados_celdas_hoja_2"]), 97)
http = read_json(EVIDENCE / "20261109-08-http.json")
check("evidencia HTTP previa: aprobadas/total", [http["passed"], http["total"]], [25, 25])

docs = [RESULT / "ETAPA-00.md", RESULT / "ESTADO_GENERAL.md", *ANNEX.glob("*.md")]
missing_links = []
link_count = 0
for doc in docs:
    text = doc.read_text(encoding="utf-8-sig")
    for link in re.findall(r"\]\(([^)]+)\)", text):
        if link.startswith(("https:", "http:", "#")):
            continue
        path = (doc.parent / unquote(link.split("#")[0]).strip("<>")).resolve()
        link_count += 1
        if path != TARGET and not path.exists():
            missing_links.append({"documento": doc.name, "enlace": link})
check("enlaces locales inexistentes (excluye salida de este script)", missing_links, [])
check("cursor etapa siguiente", "Cursor activo: ETAPA-01 / HU-AUTH-01 / CA-01" in (RESULT / "ESTADO_GENERAL.md").read_text(encoding="utf-8"), True)
check("informe completado como inventario", "COMPLETADA en su alcance de inventario" in (RESULT / "ETAPA-00.md").read_text(encoding="utf-8"), True)

# Test only the evidence writer in a temporary directory, without importing Django.
tree = ast.parse((RESULT / "soporte/audit00.py").read_text(encoding="utf-8"))
node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "output")
with TemporaryDirectory(prefix="audit00-output-") as temporary:
    env = {"EVIDENCE": Path(temporary), "json": json, "datetime": datetime, "ZoneInfo": ZoneInfo}
    exec(compile(ast.Module(body=[node], type_ignores=[]), "output_extracted", "exec"), env)
    with redirect_stdout(io.StringIO()):
        env["output"]("sample.json", {"case": 1})
        original = Path(temporary) / "sample.json"
        first = (original.read_bytes(), original.stat().st_mtime_ns)
        env["output"]("sample.json", {"case": 1})
        check("escritura repetida identica preserva bytes/mtime", (original.read_bytes(), original.stat().st_mtime_ns) == first, True)
        env["output"]("sample.json", {"case": 2})
        check("escritura distinta conserva evidencia anterior", (original.read_bytes(), original.stat().st_mtime_ns) == first, True)
        repeats = list((Path(temporary) / "repeticiones").glob("*.json"))
        check("escritura distinta crea una repeticion", len(repeats), 1)
        check("repeticion contiene nuevo valor", read_json(repeats[0]), {"case": 2})

processes = command(["powershell.exe", "-NoProfile", "-Command",
    "$p=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(w)?\\.exe$' -and $_.CommandLine -match 'audit00\\.py.*serve' } | Select-Object -ExpandProperty ProcessId); ConvertTo-Json -InputObject $p"])
check("procesos servidor audit00 activos", json.loads(processes), [])

report = {"fecha_lima": datetime.now(ZoneInfo("America/Lima")).isoformat(),
          "herramienta": "Python: CSV/JSON/AST/hash, Git y CIM de solo lectura",
          "alcance": "Integridad del cierre de inventario. Sin peticiones HTTP ni ejecucion de historias. Las cifras de pruebas anteriores conservan su fecha.",
          "enlaces_comprobados": link_count,
          "comprobaciones": checks,
          "aprobadas": sum(c["cumple"] for c in checks), "total": len(checks),
          "archivos_de_cierre_sha256": {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p)
              for p in [*docs, Path(__file__), *ANNEX.glob("*.json"), *ANNEX.glob("*.csv")]},
          "cursor": "ETAPA-01 / HU-AUTH-01 / CA-01 / 08_Historias_de_Usuario.md:18",
          "otras_etapas": "NO EJECUTADAS como etapa; no aceptadas por este cierre"}
destination = TARGET
if TARGET.exists():
    directory = EVIDENCE / "repeticiones"
    directory.mkdir(exist_ok=True)
    destination = directory / (datetime.now().strftime("%Y%m%d-%H%M%S-%f-") + TARGET.name)
with destination.open("x", encoding="utf-8") as handle:
    json.dump(report, handle, ensure_ascii=False, indent=2)
print(json.dumps({"archivo": str(destination.relative_to(ROOT)), "aprobadas": report["aprobadas"],
                  "total": report["total"], "fallos": [c for c in checks if not c["cumple"]]}, ensure_ascii=True))
sys.exit(0 if report["aprobadas"] == report["total"] else 1)
