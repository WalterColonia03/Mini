"""Reproduce o verifica las vistas de 08 sin escribir en las evidencias de 20261112."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[3]
RESULTADOS = ROOT / "auditoria_por_etapas/resultados"
EVIDENCIA = RESULTADOS / "evidencias/13-A-20261113/planificacion"
GENERADOR = RESULTADOS / "fuente_unica_20261112/regenerar_vistas.py"
CASO = "CP-DEC-07-VENCIDOS-FILTRO-002"
DOCS = ["08_Historias_de_Usuario.md", "02_Diseno_Tecnico_R1_PMV.md",
        "14_Sprint_Planning.md", "16_Task_Breakdown.md", "21_Alcance_Actual_y_Diferencias.md"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verificar(escribir=False):
    spec = importlib.util.spec_from_file_location("vistas13", GENERADOR)
    vistas = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vistas)
    vistas.HERE = EVIDENCIA  # Solo el índice JSON lleva ruta relativa al generador.
    contenido = {}

    def capturar(ruta, texto):
        contenido[ruta] = texto.rstrip() + "\n"

    vistas.write = capturar
    resumen = vistas.generate()
    if escribir:
        for ruta, texto in contenido.items():
            ruta.write_text(texto, encoding="utf-8")
    errores = []
    for ruta, texto in contenido.items():
        if not ruta.exists() or ruta.read_text(encoding="utf-8") != texto:
            errores.append("Difiere del generador: " + ruta.name)

    actual = (ROOT / DOCS[0]).read_bytes()
    with zipfile.ZipFile(EVIDENCIA / "antes.zip") as copia:
        anterior = copia.read(DOCS[0])
    antiguo = vistas.parse(anterior.decode("utf-8-sig").replace("\r\n", "\n"))
    nuevo = vistas.parse()
    errores.extend(vistas.document_errors(*nuevo))
    def ids(elementos):
        return {item["id"] for item in elementos}
    if nuevo[1] != antiguo[1] or nuevo[3] != antiguo[3]:
        errores.append("Cambió alguna HU o criterio de aceptación")
    if ids(nuevo[2]) - ids(antiguo[2]) != {CASO} or ids(antiguo[2]) - ids(nuevo[2]):
        errores.append("Diferencia inesperada en los casos escritos")
    for nombre in DOCS + [p.name for p in contenido if p.suffix == ".md"]:
        for enlace in re.findall(r"\[[^\]\n]*\]\(([^)\n]+)\)", (ROOT / nombre).read_text(encoding="utf-8")):
            if enlace.startswith(("https:", "http:", "mailto:")):
                continue
            archivo, _, ancla = enlace.partition("#")
            destino = ROOT / (archivo or nombre)
            if not destino.exists() or (ancla and destino.name == DOCS[0] and f'id="{ancla}"' not in nuevo[0]):
                errores.append(f"{nombre}: {enlace}")
    return {"pasada": 1, "etapa": 13, "alcance": "Estructura documental, no ejecución funcional",
            "sha256_08_anterior": sha(anterior), "sha256_08": sha(actual),
            "sha256_generador": sha(GENERADOR.read_bytes()), "generador": resumen,
            "nuevo_caso": CASO, "hu_y_criterios_identicos_al_corte_anterior": nuevo[1] == antiguo[1] and nuevo[3] == antiguo[3],
            "salidas": {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in contenido if p.exists()},
            "errores": errores, "correcto": not errores}


if __name__ == "__main__":
    sys.dont_write_bytecode = True
    parser = argparse.ArgumentParser()
    parser.add_argument("--regenerar", action="store_true", help="Escribir vistas 07/09/03 y el índice del corte 13.")
    args = parser.parse_args()
    informe = verificar(escribir=args.regenerar)
    print(json.dumps(informe, indent=2, ensure_ascii=False))
    raise SystemExit(0 if informe["correcto"] else 1)
