"""Read-only, ID-level comparison of the historical workbook and the stage 00 baseline."""
import hashlib
import json
import re
from pathlib import Path

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[3]
RESULTS = Path(__file__).resolve().parents[1]
book_path = ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx"
hash_before = hashlib.sha256(book_path.read_bytes()).hexdigest()
plan = json.loads((RESULTS / "anexos/ETAPA-00-planificacion.json").read_text(encoding="utf-8"))
by_id = {record["id"]: record for record in plan["historias"] if record["criterios"]}
base_ca = {ca["id"] for record in by_id.values() for ca in record["criterios"]}
workbook = load_workbook(book_path, read_only=True)
try:
    _, selected, tests, future = workbook.worksheets
    selected_ids, future_ids, ca_refs = {}, {}, {}
    current = None
    for row in selected.iter_rows(min_row=4):
        if isinstance(row[0].value, str) and re.fullmatch(r"HU-[A-Z]+-\d+[a-z]?", row[0].value):
            current = row[0].value
            selected_ids[current] = row[0].coordinate
        ordinal = re.fullmatch(r"CA-(\d+)", str(row[4].value))
        if current and ordinal:
            key = f"{current}/CA-{int(ordinal[1]):02d}"
            if key in ca_refs:
                raise ValueError(f"Repeated workbook key: {key}")
            ca_refs[key] = row[4].coordinate
    for (cell,) in future.iter_rows(min_row=4, max_col=1):
        if re.fullmatch(r"HU-[A-Z]+-\d+[a-z]?", str(cell.value)):
            future_ids[cell.value] = cell.coordinate
    result = {
        "archivo": book_path.name,
        "sha256": hash_before,
        "fuentes": [f"{sheet.title}!{sheet.calculate_dimension()}" for sheet in workbook.worksheets],
        "metodo": "Lectura OOXML de solo lectura. Identidad de HU y ordinal de CA. Las etiquetas reflejan declaraciones del libro.",
        "hu_declaradas_implementadas_celdas": selected_ids,
        "hu_declaradas_pendientes_celdas": future_ids,
        "ca_declarados_celdas_hoja_2": ca_refs,
        "fila_3_pruebas_encabezado": tests["C3"].value,
        "filas_con_nombre_test_columna_C": sum("test_" in str(cell.value) for (cell,) in tests.iter_rows(min_row=4,min_col=3,max_col=3)),
        "base_08_ausente_de_ambas_hojas": sorted(set(by_id) - (selected_ids.keys() | future_ids.keys())),
        "hu_en_ambas_hojas": sorted(selected_ids.keys() & future_ids.keys()),
        "hu_externas_a_08_con_ca": sorted((selected_ids.keys() | future_ids.keys()) - set(by_id)),
        "ordinales_del_libro_sin_par_en_08": sorted(ca_refs.keys() - base_ca),
        "ordinales_08_sin_par_en_hoja_2_para_las_hu_de_esa_hoja": sorted(ca for hu in selected_ids if hu in by_id for c in by_id[hu]["criterios"] if (ca := c["id"]) not in ca_refs),
        "ejecuciones_funcionales": 0,
    }
finally:
    workbook.close()
if hashlib.sha256(book_path.read_bytes()).hexdigest() != hash_before:
    raise RuntimeError("Workbook changed during inspection")
(RESULTS / "evidencias/00-libro-cotejo.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print("HU indicadas en las hojas 2 y 4, CA numerados y filas con nombre de test:", len(selected_ids), len(future_ids), len(ca_refs), result["filas_con_nombre_test_columna_C"])
for name in ("base_08_ausente_de_ambas_hojas", "hu_en_ambas_hojas", "hu_externas_a_08_con_ca", "ordinales_del_libro_sin_par_en_08", "ordinales_08_sin_par_en_hoja_2_para_las_hu_de_esa_hoja"):
    print(name, result[name])
