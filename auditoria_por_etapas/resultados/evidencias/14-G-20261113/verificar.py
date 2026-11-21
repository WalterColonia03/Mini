"""Huellas de producto y comparación de vistas. Ejecutar desde cualquier carpeta."""
import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
APP = ROOT / "r1-pmv"
GEN = OUT.parents[1] / "fuente_unica_20261112"
DOCS = (
    "08_Historias_de_Usuario.md", "07_Reglas_de_Negocio.md", "09_Product_Backlog.md",
    "03_Matriz_de_Trazabilidad_y_Pruebas.md", "02_Diseno_Tecnico_R1_PMV.md",
    "14_Sprint_Planning.md", "16_Task_Breakdown.md", "21_Alcance_Actual_y_Diferencias.md",
)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def product():
    names = subprocess.check_output(
        ["git", "-C", str(APP), "ls-files", "-co", "--exclude-standard", "-z"]
    ).decode("utf-8").split("\0")
    paths = sorted(set(p for p in names if p and not p.startswith("evidencias/") and
                       Path(p).suffix in {".py", ".html", ".css", ".js", ".svg", ".ps1", ".sh"}))
    return {p: digest((APP / p).read_bytes()) for p in paths}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("momento", choices=["antes", "final", "comparar"])
    args = parser.parse_args()
    files = product()
    sys.path.insert(0, str(GEN))
    import regenerar_vistas as views
    expected = {}
    views.write = lambda path, value: expected.update({path: value.rstrip() + "\n"})
    totals = views.generate()
    matching = {p.name: p.read_text(encoding="utf-8") == v for p, v in expected.items()}
    record = dict(at_utc=datetime.now(timezone.utc).isoformat(), pasada=1, sublote="14-G",
                  head=subprocess.check_output(["git", "-C", str(APP), "rev-parse", "HEAD"], text=True).strip(),
                  status=subprocess.check_output(["git", "-C", str(APP), "status", "--short"], text=True).splitlines(),
                  archivos=len(files), build=digest(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()),
                  fuentes=files, documentos={p: digest((ROOT / p).read_bytes()) for p in DOCS},
                  conteos=totals, vistas_reproducidas=matching)
    report = {k: v for k, v in record.items() if k not in {"status", "fuentes"}}
    if args.momento != "comparar":
        with (OUT / f"build-{args.momento}.json").open("x", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        if args.momento == "antes":
            with zipfile.ZipFile(OUT / "planificacion-antes.zip", "x", zipfile.ZIP_DEFLATED) as archive:
                for p in DOCS:
                    archive.write(ROOT / p, p)
    if args.momento != "antes":
        old = json.loads((OUT / "build-antes.json").read_text(encoding="utf-8"))
        report["fuentes_cambiadas"] = sorted(p for p in files.keys() | old["fuentes"].keys()
                                              if files.get(p) != old["fuentes"].get(p))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(matching.values()) else 1

if __name__ == "__main__":
    sys.exit(main())
