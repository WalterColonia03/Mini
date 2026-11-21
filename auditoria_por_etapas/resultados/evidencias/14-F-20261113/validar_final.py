"""Valida el corte 14-F. Solo lee fuentes y bases ficticias; no ejecuta Django."""
import ast
import hashlib
import json
import re
import sqlite3
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[3]
sys.path.insert(0, str(OUT.parents[1] / "fuente_unica_20261112"))
import regenerar_vistas as views


def read(path):
    return path.read_text(encoding="utf-8-sig")


def obj(path):
    return json.loads(read(path))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    if {c["id"] for c in criteria} != {cid for c in cases for cid in c["covers"]}:
        errors.append("Correspondencia criterios/casos incompleta")
    for case in cases:
        if not all(case[k] for k in ("preconditions", "data", "steps", "expected")):
            errors.append("Caso incompleto: " + case["id"])

    final = obj(OUT / "build-final.json")
    changed_docs = [p for p, h in final["documentos"].items() if sha(ROOT / p) != h]
    changed_code = [p for p, h in final["fuentes"].items() if sha(ROOT / "r1-pmv" / p) != h]
    if changed_docs or changed_code:
        errors.append("Fuentes/documentos difieren del manifiesto final")
    for p in final["fuentes"]:
        if p.endswith(".py"):
            ast.parse(read(ROOT / "r1-pmv" / p), filename=p)

    prior = obj(OUT / "build-antes.json")
    with zipfile.ZipFile(OUT / "planificacion-antes.zip") as archive:
        bad_prior = [p for p, h in prior["documentos"].items()
                     if hashlib.sha256(archive.read(p)).hexdigest() != h]
        old_source = archive.read("08_Historias_de_Usuario.md").decode("utf-8-sig")
    if bad_prior:
        errors.append("Planificacion anterior alterada")
    before_hashes = obj(OUT / "servidor/huellas-antes.json")
    bad_before = []
    for row in before_hashes:
        relative = Path(row["Path"]).relative_to(ROOT)
        if sha(OUT / "servidor/antes" / relative) != row["Hash"].lower():
            bad_before.append(str(relative))
    if sha(OUT / "servidor/antes/r1-pmv/sales/tests.py") != prior["fuentes"]["sales/tests.py"]:
        bad_before.append("sales/tests.py")
    if bad_before:
        errors.append("Snapshot de codigo anterior alterado")

    browser_reports = {}
    evidence_changes = []
    for name in ("antes", "final", "final2", "flujo-completo", "cadena-final"):
        folder = OUT / "navegador" / name
        index = obj(folder / "indice.json")
        for p, h in index.items():
            if sha(folder / p) != h:
                evidence_changes.append(name + "/" + p)
        run = obj(folder / "ejecucion.json")
        browser_reports[name] = dict(checkpoints=len(run["pasos"]),
            capturas=len(list(folder.glob("*.jpg"))), build_estable=run["build_estable"],
            archivos_indexados=len(index), evidencia_final=name in ("final2", "cadena-final"))
        if name in ("final2", "cadena-final"):
            files = obj(folder / "build-final.json")["archivos"]
            incompatible = [p for p, h in files.items() if final["fuentes"].get(p) != h]
            browser_reports[name].update(archivos_compatibles=len(files) - len(incompatible),
                                         incompatibles=incompatible)
            target = 12 if name == "final2" else 44
            if (incompatible or not run["build_estable"] or len(run["pasos"]) != target
                    or run["estado"] != "recorrido_completo"):
                errors.append("Navegador final incompleto/incompatible: " + name)
            if run["plan08_inicio"] != prior["documentos"]["08_Historias_de_Usuario.md"]:
                errors.append("08 ejecutado por navegador no corresponde al snapshot")
    if evidence_changes:
        errors.append("Evidencia navegador difiere de indice")
    history = obj(OUT / "navegador/final2/comparacion-historia.json")
    if not history["misma_historia"] or history["original"]["productos"] != history["orden_esperado"]:
        errors.append("Fotografia u orden historico no conservados")

    variants = obj(OUT / "servidor/asignaciones-final.json")
    if len(variants["casos"]) != 12 or any(c["resultado"] != "CUMPLE" for c in variants["casos"]):
        errors.append("Casos servidor incompletos")
    if any(final["fuentes"].get(p) != h for p, h in variants["fuentes_sha256"].items()):
        errors.append("Fuentes del runner final incompatibles")
    if variants["08_sha256"] != prior["documentos"]["08_Historias_de_Usuario.md"]:
        errors.append("08 servidor no corresponde al snapshot")
    suite = read(OUT / "servidor/regresion-final.txt")
    manifest = obj(OUT / "servidor/regresion-manifiesto.json")
    if ("Ran 574 tests" not in suite or not re.search(r"^OK\s*$", suite, re.M)
            or "No changes detected" not in suite or manifest["salida"]
            or manifest["cambios_durante_prueba"] or manifest["build"] != final["build"]):
        errors.append("Regresion final fallida/incompatible")

    inventory = obj(OUT / "criterios-final.json")
    texts = {c["id"]: c["text"] for c in criteria}
    mismatched = [c["criterio"] for c in inventory["criterios"] if texts.get(c["criterio"]) != c["texto"]]
    old_mismatched = [c["criterio"] for c in inventory["criterios"] if c["texto"] not in old_source]
    if mismatched or old_mismatched or len(inventory["criterios"]) != 20:
        errors.append("Inventario incompatible con08 final/ejecutado")
    classifications = {}
    for group in ("CA base", "Criterio complementario", "Dependencia"):
        classifications[group] = dict(Counter(c["clasificacion"] for c in inventory["criterios"] if c["grupo"] == group))

    databases = obj(OUT / "servidor/verificacion-bases-final.json")["bases"]
    for row in databases:
        db = OUT / "servidor" / row["base"]
        if sha(db) != row["sha256"]:
            errors.append("Base ficticia difiere del corte: " + db.name)
        with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as con:
            counts = [con.execute("SELECT COUNT(*) FROM " + table).fetchone()[0]
                      for table in ("django_session", "identity_loginattempt")]
            counts.append(con.execute("SELECT COUNT(*) FROM identity_account WHERE password <> '!' ").fetchone()[0])
        if any(counts):
            errors.append("Base ficticia conserva datos de autenticacion: " + db.name)

    docs = [ROOT / p for p in (
        "00_LEEME_PLANIFICACION.md", "01_Proyecto_y_Releases.md", "02_Diseno_Tecnico_R1_PMV.md",
        "03_Matriz_de_Trazabilidad_y_Pruebas.md", "07_Reglas_de_Negocio.md", "08_Historias_de_Usuario.md",
        "09_Product_Backlog.md", "14_Sprint_Planning.md", "16_Task_Breakdown.md",
        "21_Alcance_Actual_y_Diferencias.md", "auditoria_por_etapas/CONTINUIDAD_Y_SEGUNDA_PASADA.md",
        "auditoria_por_etapas/resultados/ETAPA-14.md", "auditoria_por_etapas/resultados/ESTADO_GENERAL.md",
        "auditoria_por_etapas/resultados/soporte/14-F-inventario.md",
        "auditoria_por_etapas/resultados/soporte/14-F-disposiciones.md")]
    docs += [OUT / "navegador/RESUMEN.md", OUT / "servidor/INFORME.md"]
    broken = []
    checked = 0
    for path in docs:
        content = read(path)
        if path.name == "ETAPA-14.md":
            content = content.split("## Registro anterior14-E, conservado con sus límites")[0]
        content = re.sub(r"```.*?```", "", content, flags=re.S)
        for link in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", content):
            if re.match(r"^https?://", link):
                continue
            file, _, anchor = unquote(link.strip("<>")).partition("#")
            target = (path.parent / file).resolve() if file else path
            checked += 1
            if target == OUT / "validacion-final.json":
                continue
            if not target.exists():
                broken.append({"documento": str(path.relative_to(ROOT)), "destino": link})
            elif anchor and target.name == "08_Historias_de_Usuario.md" and f'id="{anchor}"' not in source:
                broken.append({"documento": str(path.relative_to(ROOT)), "ancla": anchor})
    if broken:
        errors.append("Enlaces o anclas rotos")

    report = dict(at_utc=datetime.now(timezone.utc).isoformat(), pasada=1, sublote="14-F",
        source08_sha256=sha(ROOT / "08_Historias_de_Usuario.md"), build=final["build"],
        conteos=views.counts(source, stories, cases, criteria), derivados_identicos=derived,
        documentos_finales_cambiados=changed_docs, fuentes_finales_cambiadas=changed_code,
        snapshot_anterior_alterado=bad_prior, codigo_anterior_alterado=bad_before,
        navegador=browser_reports, evidencia_navegador_alterada=evidence_changes,
        servidor_variantes=12, regresion_final=574, criterios_inventario=20,
        clasificacion_por_grupo=classifications, criterios_incompatibles=mismatched,
        criterios_incompatibles_con_08_ejecutado=old_mismatched, bases_ficticias_saneadas=len(databases),
        enlaces_comprobados=checked, enlaces_rotos=broken, errores=errors, aprobado=not errors,
        limite="Valida evidencia y estructura del corte; etapa14 permanece PARCIAL. No ejecuta casos nuevos de producto.")
    (OUT / "validacion-final.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
