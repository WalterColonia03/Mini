"""Congela la matriz de criterios base y la evidencia específica de integración."""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
source = (ROOT / "08_Historias_de_Usuario.md").read_text(encoding="utf-8")
stories = "AUTH-01 AUTH-03 CAT-01 CAT-02 PROD-01 PROD-02 PROD-03 PROD-05 PROD-06 PROV-01 PROV-02 PROV-04 INV-01a INV-02 INV-04 CAJA-01 CAJA-02 CAJA-05 VEN-01b VEN-01c VEN-02a VEN-05a VEN-05b".split()
# Cada valor es el subconjunto ejercitado. PARCIAL mantiene las variantes ausentes.
evidence = {
    "AUTH-01": {1: "B01/02/03", 4: "B04/05b/11/12b/15/20b; S01..05"},
    "CAT-01": {1: "B06/21/22/24"},
    "CAT-02": {1: "B05/06"},
    "PROD-01": {1: "B08 y consulta posterior", 3: "B29/33, muestra de stock 6/5"},
    "PROD-02": {1: "B07/08", 2: "B07/08, precio3.55", 4: "B07/08, mínimo de fixture", 5: "B08 y testigo DB"},
    "PROD-05": {1: "S08, producto inactivado con borrador"},
    "PROD-06": {2: "S13, pasa a vencer hoy, bloqueo del cobro"},
    "PROV-01": {1: "B10/12"},
    "PROV-02": {1: "B09/10/12, proveedor utilizado en carga directa"},
    "INV-01a": {1: "B14/05b; S01", 2: "B12/13/14", 3: "B13, fecha inválida sin mutación", 4: "B14/18", 5: "B14/27 y testigo DB"},
    "INV-02": {1: "B30/31/32; S11", 2: "S12/14/15/16; B30b", 3: "B32; S15/16", 4: "B32/34, correlativo sin constancia dedicada"},
    "INV-04": {1: "B34", 2: "B34, solo carga inicial", 3: "B34, etiqueta carga inicial"},
    "CAJA-01": {1: "B16/17", 4: "B17/04/12b; S02"},
    "CAJA-02": {1: "B37/38", 2: "B38, cuadre exacto114.20", 3: "B38/39; S18", 4: "S07", 5: "B40"},
    "VEN-01b": {1: "B17/19/40", 2: "B18/19", 3: "B19, cantidad4", 4: "S13", 5: "B19/20 y testigo BD"},
    "VEN-01c": {1: "B25; S06/08/09/13", 2: "B26/27/38", 3: "B27/29, FEFO3+1; S13", 4: "B27, asignaciones lote ausentes", 5: "S17", 6: "B27/28, snapshot producto/precio/costo"},
    "VEN-02a": {1: "B27/28", 2: "B27/28/36", 3: "B27/28/36", 4: "B28/36, misma constancia sin cambio de catálogo"},
    "VEN-05b": {1: "B35", 3: "B36"},
}
discrepancies = {
    ("INV-02", 4): "PARCIAL. Correlativo persistido, falta constancia dedicada RN-05/C-03.",
    ("INV-04", 1): "INCUMPLE. Sin saldo resultante por fila ni lote de salida de la venta.",
    ("INV-04", 4): "INCUMPLE. Vista product_movements sin filtros por fechas/tipo.",
    ("VEN-01c", 4): "PARCIAL. Falta persistencia de asignaciones de lotes DEC-11-MODELO.",
}
rows = []
for story in stories:
    for match in re.finditer(r"\*\*HU-" + re.escape(story) + r"/CA-(\d+)\.\*\* (.+)", source):
        ca = int(match[1])
        case = evidence.get(story, {}).get(ca, "")
        status = "PARCIAL" if case else "NO EJECUTADO"
        detail = "Muestra de integración. Las restantes condiciones y fronteras del criterio requieren sus casos." if case else "Sin nueva ejecución particular del CA en 14-D. Antecedentes enlazados en el inventario."
        if (story, ca) in discrepancies:
            status, detail = discrepancies[(story, ca)].split(". ", 1)
        rows.append({"criterio": f"HU-{story}/CA-{ca:02}", "fuente": f"08_Historias_de_Usuario.md#HU-{story}-CA-{ca:02}", "texto": match[2], "clasificacion": status, "evidencia_14D": case, "limite": detail})
result = {
    "historias": len(stories),
    "criterios_base": len(rows),
    "criterios_con_muestra": sum(bool(x["evidencia_14D"]) for x in rows),
    "estado_por_criterio": {s: sum(x["clasificacion"] == s for x in rows) for s in sorted({x["clasificacion"] for x in rows})},
    "leyenda": "B remite al prefijo del JSON en navegador/recorrido3. S remite al ID de servidor/variantes-despues.json. Un campo extraído no prueba su comportamiento.",
    "criterios": rows,
}
(HERE / "criterios-base.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in result.items() if k != "criterios"}, ensure_ascii=False))
