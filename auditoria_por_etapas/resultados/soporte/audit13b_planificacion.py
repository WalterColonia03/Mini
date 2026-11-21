"""Conserva entrada 13-B y deriva vistas sin sobrescribir evidencia 13-A.

--preparar se ejecuta antes de editar08. --regenerar escribe07/09/03.
Sin argumentos compara las vistas y valida enlaces/estructura.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[3]
RESULTADOS = ROOT / "auditoria_por_etapas/resultados"
EVIDENCIA = RESULTADOS / "evidencias/13-B-20261113/planificacion"
GENERADOR = RESULTADOS / "fuente_unica_20261112/regenerar_vistas.py"
DOCS = ["08_Historias_de_Usuario.md", "02_Diseno_Tecnico_R1_PMV.md",
        "14_Sprint_Planning.md", "16_Task_Breakdown.md", "21_Alcance_Actual_y_Diferencias.md",
        "07_Reglas_de_Negocio.md", "09_Product_Backlog.md", "03_Matriz_de_Trazabilidad_y_Pruebas.md"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def preparar():
    EVIDENCIA.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(EVIDENCIA / "antes.zip", "x", zipfile.ZIP_DEFLATED) as copia:
        for nombre in DOCS:
            copia.write(ROOT / nombre, nombre)
    print("Entrada documental13-B conservada; no se sobrescribe13-A.")


def verificar(escribir=False):
    spec = importlib.util.spec_from_file_location("vistas13b", GENERADOR)
    vistas = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vistas)
    vistas.HERE = EVIDENCIA
    contenido = {}
    vistas.write = lambda ruta, texto: contenido.update({ruta: texto.rstrip() + "\n"})
    resumen = vistas.generate()
    if escribir:
        for ruta, texto in contenido.items():
            ruta.write_text(texto, encoding="utf-8")
    errores = ["Difiere del generador: " + ruta.name for ruta, texto in contenido.items()
               if not ruta.exists() or ruta.read_text(encoding="utf-8") != texto]
    with zipfile.ZipFile(EVIDENCIA / "antes.zip") as copia:
        anterior = copia.read(DOCS[0])
    antiguo = vistas.parse(anterior.decode("utf-8-sig").replace("\r\n", "\n"))
    nuevo = vistas.parse()
    errores.extend(vistas.document_errors(*nuevo))
    if nuevo[1] != antiguo[1] or nuevo[3] != antiguo[3]:
        errores.append("Cambió alguna HU o criterio de aceptación; revisar explícitamente el contrato")
    if {t["id"] for t in nuevo[2]} != {t["id"] for t in antiguo[2]}:
        errores.append("Cambió el inventario de casos escritos")
    for nombre in DOCS:
        for enlace in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", (ROOT / nombre).read_text(encoding="utf-8")):
            if enlace.startswith(("https:", "http:", "mailto:")):
                continue
            archivo, _, ancla = enlace.partition("#")
            destino = ROOT / (archivo or nombre)
            if not destino.exists() or (ancla and destino.name == DOCS[0] and f'id="{ancla}"' not in nuevo[0]):
                errores.append(f"{nombre}: {enlace}")
    return {"fecha_utc": datetime.now(timezone.utc).isoformat(), "pasada": 1, "etapa": 13,
            "sublote": "13-B", "alcance": "Estructura documental; no sustituye ejecución funcional",
            "sha256_08_anterior": sha(anterior), "sha256_08": sha((ROOT / DOCS[0]).read_bytes()),
            "sha256_generador": sha(GENERADOR.read_bytes()), "generador": resumen,
            "hu_y_criterios_identicos_al_corte_anterior": nuevo[1] == antiguo[1] and nuevo[3] == antiguo[3],
            "salidas": {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in contenido if p.exists()},
            "errores": errores, "correcto": not errores}


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser()
    parser.add_argument("--preparar", action="store_true")
    parser.add_argument("--regenerar", action="store_true")
    args = parser.parse_args()
    if args.preparar:
        preparar()
    else:
        informe = verificar(args.regenerar)
        print(json.dumps(informe, indent=2, ensure_ascii=False))
        raise SystemExit(0 if informe["correcto"] else 1)
