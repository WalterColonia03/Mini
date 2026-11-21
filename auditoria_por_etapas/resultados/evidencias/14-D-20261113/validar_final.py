"""Valida el corte documental y su compatibilidad con evidencia, sin abrir bases."""
import ast
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
GEN = OUT.parents[1] / "fuente_unica_20261112"
sys.path.insert(0, str(GEN))
import regenerar_vistas as views

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return path.read_text(encoding="utf-8-sig")

def main():
    errors = []
    source, stories, cases, criteria = views.parse()
    errors.extend(views.document_errors(source, stories, cases, criteria))
    expected = {}
    views.write = lambda p, v: expected.update({p: v.rstrip() + "\n"})
    views.generate()
    derived = {str(p.relative_to(ROOT)): read(p) == v for p, v in expected.items()}
    if not all(derived.values()):
        errors.append("Vistas derivadas desfasadas")
    ids = {c["id"] for c in criteria}
    covered = {cid for case in cases for cid in case["covers"]}
    if ids != covered:
        errors.append("Criterios/casos sin correspondencia")
    for case in cases:
        if not all(case[k] for k in ("preconditions", "data", "steps", "expected")):
            errors.append("Caso incompleto " + case["id"])
    final = json.loads(read(OUT / "build-final.json"))
    document_changes = [p for p, h in final["documentos"].items() if sha(ROOT / p) != h]
    if document_changes:
        errors.append("Documentos difieren del manifiesto final")
    changed = [p for p, h in final["fuentes"].items() if sha(ROOT / "r1-pmv" / p) != h]
    if changed:
        errors.append("Producto difiere del manifiesto final")
    for p in final["fuentes"]:
        if p.endswith(".py"):
            ast.parse(read(ROOT / "r1-pmv" / p), filename=p)
    browser = json.loads(read(OUT / "navegador/recorrido3/build-final.json"))
    incompatible = [p for p, h in browser["archivos"].items() if final["fuentes"].get(p) != h]
    if incompatible:
        errors.append("Manifiesto navegador incompatible")
    run = json.loads(read(OUT / "navegador/recorrido3/ejecucion.json"))
    image_index = json.loads(read(OUT / "navegador/recorrido3/indice.json"))
    changed_evidence = [p for p, h in image_index.items() if sha(OUT / "navegador/recorrido3" / p) != h]
    if changed_evidence:
        errors.append("Evidencia navegador alterada")
    if run["estado"] != "recorrido_completo" or not run["build_estable"] or len(run["pasos"]) != 44:
        errors.append("Recorrido incompleto o inestable")
    variants = json.loads(read(OUT / "servidor/variantes-despues.json"))
    if len(variants["variantes"]) != 18 or any(r["resultado"] != "CUMPLE" for r in variants["variantes"]):
        errors.append("Variantes servidor incompletas")
    suite = read(OUT / "servidor/regresion-final.txt")
    if "Ran 560 tests" not in suite or not re.search(r"^OK\s*$", suite, re.M):
        errors.append("Regresión final sin resultado esperado")
    inventory = json.loads(read(OUT / "inventario/criterios-base.json"))
    criteria_text = {c["id"]: c["text"] for c in criteria}
    mismatched = [r["criterio"] for r in inventory["criterios"]
                  if criteria_text.get(r["criterio"]) != r["texto"]]
    if mismatched:
        errors.append("Criterios de inventario incompatibles con08")
    prior = json.loads(read(OUT / "build-antes.json"))
    with zipfile.ZipFile(OUT / "planificacion-antes.zip") as z:
        bad_prior = [p for p, h in prior["documentos"].items()
                     if hashlib.sha256(z.read(p)).hexdigest() != h]
    if bad_prior:
        errors.append("Snapshot de planificación anterior alterado")
    docs = [ROOT / p for p in (
        "00_LEEME_PLANIFICACION.md", "01_Proyecto_y_Releases.md",
        "02_Diseno_Tecnico_R1_PMV.md", "03_Matriz_de_Trazabilidad_y_Pruebas.md",
        "07_Reglas_de_Negocio.md", "08_Historias_de_Usuario.md", "09_Product_Backlog.md",
        "14_Sprint_Planning.md", "16_Task_Breakdown.md", "21_Alcance_Actual_y_Diferencias.md",
        "auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md",
        "auditoria_por_etapas/resultados/ETAPA-14.md", "auditoria_por_etapas/resultados/ESTADO_GENERAL.md",
        "auditoria_por_etapas/resultados/soporte/14-D-inventario.md",
        "auditoria_por_etapas/resultados/soporte/14-D-disposiciones.md",
    )]
    docs += [OUT / "navegador/RESUMEN.md", OUT / "servidor/INFORME.md"]
    broken = []
    checked = 0
    for p in docs:
        content = read(p).split("## Informe y resultados históricos conservados")[0]
        content = re.sub(r"```.*?```", "", content, flags=re.S)
        for link in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", content):
            if re.match(r"^https?://", link):
                continue
            file, _, anchor = unquote(link.strip("<>")).partition("#")
            target = (p.parent / file).resolve() if file else p
            checked += 1
            if target == OUT / "validacion-final.json":
                continue
            if not target.exists():
                broken.append({"documento": str(p.relative_to(ROOT)), "destino": link})
            elif anchor and target.name == "08_Historias_de_Usuario.md" and f'id="{anchor}"' not in source:
                broken.append({"documento": str(p.relative_to(ROOT)), "ancla": anchor})
    if broken:
        errors.append("Enlaces o anclas rotos")
    report = dict(at_utc=datetime.now(timezone.utc).isoformat(), pasada=1, sublote="14-D",
                  source08_sha256=sha(ROOT / "08_Historias_de_Usuario.md"),
                  build=final["build"], conteos=views.counts(source, stories, cases, criteria),
                  derivados_identicos=derived, archivos_navegador_compatibles=len(browser["archivos"]),
                  archivos_navegador_incompatibles=incompatible, fuentes_finales_cambiadas=changed,
                  documentos_finales_cambiados=document_changes, evidencia_navegador_alterada=changed_evidence,
                  navegador_checkpoints=len(run["pasos"]), servidor_variantes=len(variants["variantes"]),
                  regresion_final=560, criterios_inventario=len(inventory["criterios"]),
                  clasificacion_ca=dict(Counter(r["clasificacion"] for r in inventory["criterios"])),
                  criterios_inventario_incompatibles=mismatched, snapshot_anterior_alterado=bad_prior,
                  enlaces_comprobados=checked, enlaces_rotos=broken, errores=errors, aprobado=not errors,
                  limite="Valida evidencia y estructura del corte. Etapa14 permanece PARCIAL por sus contratos pendientes.")
    (OUT / "validacion-final.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return bool(errors)

if __name__ == "__main__":
    sys.exit(main())
