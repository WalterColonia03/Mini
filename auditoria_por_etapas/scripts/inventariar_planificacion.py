"""Inventario documental de etapa 00; no ejecuta ni acepta requisitos."""
from pathlib import Path
from collections import Counter
import json
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "auditoria_por_etapas/resultados/anexos"
OUT.mkdir(parents=True, exist_ok=True)

def lines(name):
    return (ROOT / name).read_text(encoding="utf-8-sig").splitlines()

def ref(name, number):
    return f"{name}:{number}"

backlog = {}
for no, line in enumerate(lines("09_Product_Backlog.md"), 1):
    if not line.startswith("|"):
        continue
    cells = [c.strip().strip("`") for c in line.strip("|").split("|")]
    if len(cells) == 9 and re.fullmatch(r"HU-[A-Z]+-\d+[a-z]?", cells[1]):
        backlog[cells[1]] = {"seleccion": "R1 SELECCIONADO" if cells[6] == "R1-PMV" else "PREVISTO/FUTURO", "dependencias": re.findall(r"HU-[A-Z]+-\d+[a-z]?", cells[8]), "fuente": ref("09_Product_Backlog.md", no)}
    elif len(cells) == 6 and re.fullmatch(r"HU-[A-Z]+-\d+[a-z]?", cells[0]):
        backlog[cells[0]] = {"seleccion": "FUERA DEL HORIZONTE", "dependencias": [], "fuente": ref("09_Product_Backlog.md", no)}

declaradas = {}
for no, line in enumerate(lines("r1-pmv/CONTROL_SPRINTS.md"), 1):
    if line.startswith("| HU-"):
        match = re.search(r"HU-[A-Z]+-\d+[a-z]?", line)
        declaradas[match.group()] = ref("r1-pmv/CONTROL_SPRINTS.md", no)

stories = []
current = None
for no, line in enumerate(lines("08_Historias_de_Usuario.md"), 1):
    match = re.match(r"### (HU-[A-Z]+-\d+[a-z]?) · (.*)", line)
    if match:
        current = {"id": match[1], "nombre": match[2], "modulo": match[1].split("-")[1], "fuente": ref("08_Historias_de_Usuario.md", no), "reglas": [], "actor": "", "criterios": [], **backlog[match[1]]}
        current["fuente_hu"] = ref("08_Historias_de_Usuario.md", no)
        current["fuente_backlog"] = backlog[match[1]]["fuente"]
        current["estado_ejecucion"] = "NO EXAMINADO"
        current["adicional_declarado"] = declaradas.get(match[1]) if current["seleccion"] != "R1 SELECCIONADO" else None
        stories.append(current)
    elif line.startswith("## "):
        current = None
    elif current and line.startswith("- **Historia:**"):
        actor = re.search(r"Como (.*?),? quiero", line)
        current["actor"] = actor[1] if actor else "Consultar fuente"
    elif current and line.startswith("- **Reglas de negocio:**"):
        current["reglas"] = re.findall(r"RN-\d+", line)
    elif current and (match := re.match(r"  (\d+)\. (.*)", line)):
        current["criterios"].append({"id": f"{current['id']}/CA-{int(match[1]):02d}", "fuente": ref("08_Historias_de_Usuario.md", no), "estado": "NO EXAMINADO"})

for sid, entry in backlog.items():
    if entry["seleccion"] == "FUERA DEL HORIZONTE":
        stories.append({"id": sid, "modulo": sid.split("-")[1], "actor": "No detallado", "nombre": "Idea sin CA detallados", "reglas": [], "criterios": [], "fuente_hu": "08_Historias_de_Usuario.md:843", "fuente_backlog": entry["fuente"], "estado_ejecucion": "NO APLICA: fuera del horizonte; no aprobado", "adicional_declarado": None, **entry})

rules = []
for no, line in enumerate(lines("07_Reglas_de_Negocio.md"), 1):
    if line.startswith("| RN-"):
        cells = [c.strip() for c in line.strip("|").split("|")]
        rules.append({"id": cells[0], "nombre": cells[1], "historias": re.findall(r"HU-[A-Z]+-\d+[a-z]?", cells[3]), "fuente": ref("07_Reglas_de_Negocio.md", no), "estado": "NO EXAMINADO" if cells[0] not in {"RN-13", "RN-21"} else "FUERA DEL HORIZONTE"})

tasks = []
parent = "TRANSVERSAL"
for no, line in enumerate(lines("16_Task_Breakdown.md"), 1):
    if line.startswith("## "):
        match = re.search(r"HU-[A-Z]+-\d+[a-z]?", line)
        parent = match[0] if match else "TRANSVERSAL"
    if re.match(r"\| S1-[A-Z0-9-]+ \|", line):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) == 10:
            tasks.append({"id": cells[0], "tipo": cells[1], "padre": parent, "referencias": cells[4], "dependencias": cells[5], "fuente": ref("16_Task_Breakdown.md", no), "estado": "PLAN HISTORICO / NO EXAMINADO"})
        elif len(cells) == 9:
            tasks.append({"id": cells[0], "tipo": cells[1], "padre": parent, "referencias": cells[3], "dependencias": cells[4], "fuente": ref("16_Task_Breakdown.md", no), "estado": "PLAN HISTORICO / NO EXAMINADO"})

matrix = []
parent = None
for no, line in enumerate(lines("03_Matriz_de_Trazabilidad_y_Pruebas.md"), 1):
    if line.startswith("### HU-"):
        parent = re.search(r"HU-[A-Z]+-\d+[a-z]?", line)[0]
    elif line.startswith("## "):
        parent = None
    if parent and re.match(r"\| \d+ \|", line):
        cells = [c.strip() for c in line.strip("|").split("|")]
        matrix.append({"criterio": f"{parent}/CA-{int(cells[0]):02d}", "pruebas_planificadas": re.findall(r"(?:AT|ST|CT|MT|PT|OT|IT)-[A-Z0-9-]+", line), "evidencias_planificadas": re.findall(r"EV-[A-Z0-9-]+", line), "fuente": ref("03_Matriz_de_Trazabilidad_y_Pruebas.md", no), "estado": "NO EJECUTADO EN ETAPA 00"})

assert len(stories) == 82 and len(rules) == 30 and len(tasks) == 67 and len(matrix) == 41
assert sum(len(s["criterios"]) for s in stories if s["seleccion"] == "R1 SELECCIONADO") == 41
data = {"fecha_local": "2026-11-05", "metodo": "Extraccion estatica de identificadores y referencias; no ejecuta pruebas", "historias": stories, "reglas": rules, "tareas": tasks, "matriz_historica_r1": matrix}
(OUT / "ETAPA-00-planificacion.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

report = ["# ETAPA 00 — Índice de planificación", "", "Fecha: 5 de noviembre de 2026 (America/Lima). Método: lectura del protocolo completo y extracción estática de identificadores con referencias; sin ejecución de HU, CA ni pruebas funcionales. Ningún estado histórico se convierte en aprobación actual.", "", "Este índice se regenera con `python auditoria_por_etapas/scripts/inventariar_planificacion.py`. Las citas son rutas relativas a la raíz del proyecto y números de línea. El JSON adjunto conserva un registro individual por criterio y sus referencias. La evaluación semántica en profundidad se reserva a las etapas correspondientes.", "", "## Alcance y papel de las fuentes", "", "| Fuente | Papel / vigencia |", "|---|---|", "| 01_Proyecto_y_Releases.md:3,7-11 | Plan histórico de octubre; identifica 07/08/09 como requisitos y futuro, r1-pmv como código. Jira retirado. |", "| 02_Diseno_Tecnico_R1_PMV.md:26,80,349 | Diseño histórico R1; DT-01..15 y NFR-01..12. La matriz de constancias fue actualizada y debe conciliarse con RN-29. |", "| 03_Matriz_de_Trazabilidad_y_Pruebas.md:3,5,7,271 | Matriz histórica de R1: objetivos de prueba y anexo QA histórico; no lista completa del producto ni evidencia de esta ejecución. |", "| 07_Reglas_de_Negocio.md:9 | Catálogo de 30 RN; RN-13/RN-21 fuera de horizonte. |", "| 08_Historias_de_Usuario.md:3,5,841,863 | Requisitos actuales/futuros, ideas fuera y anexo QA histórico; no catálogo de funcionalidades aceptadas. |", "| 09_Product_Backlog.md:42,59,134 | Selección R1 de 9 HU, 65 posteriores sin Sprint, 8 ideas excluidas. |", "| 14_Sprint_Planning.md:3,20-29; 16_Task_Breakdown.md:3,17-22 | Plan y desglose históricos: 67 tareas, 216 horas estimadas, sin acreditar ejecución. |", "| r1-pmv/CONTROL_SPRINTS.md:3,69-94 | Declaraciones históricas de Sprints 1–3 y mejoras; marcas y cifras no se reejecutaron aquí. |", "| 21_Alcance_Actual_y_Diferencias.md:3,5,23-29,42 | Guía de revisión del 5/11 y resultados de otra ejecución; punto de partida, con contradicciones pendientes. |", "", "La fecha y vigencia del libro PLANIFICACION_SCRUM_R1PMV.xlsx se inventarían por separado en el anexo de fuentes/entorno; no se usó como autoridad ni se modificó en este índice.", "", "## Conteos reproducibles", ""]
report += [f"- HU con CA numerados: {sum(bool(s['criterios']) for s in stories)}; CA base individuales: {sum(len(s['criterios']) for s in stories)}.", f"- Selección R1: {sum(s['seleccion']=='R1 SELECCIONADO' for s in stories)} HU / {sum(len(s['criterios']) for s in stories if s['seleccion']=='R1 SELECCIONADO')} CA; posteriores: {sum(s['seleccion']=='PREVISTO/FUTURO' for s in stories)} HU; fuera: {sum(s['seleccion']=='FUERA DEL HORIZONTE' for s in stories)} ideas sin CA detallados.", f"- Reglas: {len(rules)}. Tareas de 16: {len(tasks)} ({sum(t['tipo']=='Task' for t in tasks)} Tasks / {sum(t['tipo'].startswith('Subtask') for t in tasks)} Subtasks). Filas CA de matriz R1: {len(matrix)}.", "- Los 9 agregados QA de 08:869-877 se inventarían aparte, sin sumarlos a los CA base: usan etiquetas reutilizadas y agrupaciones de HU, por lo que no existe un ID de CA inequívoco por afirmación.", "", "## HU, CA y dependencias por módulo", "", "`R1 SELECCIONADO` describe el compromiso histórico; `PREVISTO/FUTURO` describe su posición en 09, incluso cuando CONTROL declara implementaciones posteriores. Todos los CA quedan NO EXAMINADO en esta extracción. Un adicional declarado exige contrastar código y ejecución antes de afirmar cumplimiento.", ""]
for module in dict.fromkeys(s["modulo"] for s in stories):
    report += [f"### {module}", "", "| HU / actor | Selección / declaración adicional | CA base (índice individual en JSON) | RN / dependencias | Fuentes HU; backlog |", "|---|---|---|---|---|"]
    for s in stories:
        if s["modulo"] != module:
            continue
        ca = "; ".join(f"CA-{i+1:02d} L{c['fuente'].rsplit(':',1)[1]}" for i,c in enumerate(s["criterios"])) or "Sin CA detallados"
        extra = f"; adicional declarado en {s['adicional_declarado']}" if s["adicional_declarado"] else ""
        report.append(f"| {s['id']} — {s['actor']} | {s['seleccion']}{extra} | {ca} | {', '.join(s['reglas']) or '—'} / {', '.join(s['dependencias']) or '—'} | {s['fuente_hu']}; {s['fuente_backlog']} |")
    report.append("")
report += ["## Reglas e identificadores relacionados", "", "| RN | Nombre | HU declaradas en regla | Fuente / estado |", "|---|---|---|---|"]
for r in rules:
    report.append(f"| {r['id']} | {r['nombre']} | {', '.join(r['historias']) or '—'} | {r['fuente']} / {r['estado']} |")
report += ["", "## Tareas técnicas: identidad, pertenencia y dependencias", "", "Estado de todas estas filas: PLAN HISTÓRICO / NO EXAMINADO. No son HU ni prueba de trabajo realizado. [H] y [I] conservan el significado de 16:35-36; su referencia no reactiva Jira.", "", "| ID | Tipo / padre | CA/RN/NFR declarados | Dependencias | Fuente |", "|---|---|---|---|---|"]
for t in tasks:
    report.append(f"| {t['id']} | {t['tipo']} / {t['padre']} | {t['referencias']} | {t['dependencias']} | {t['fuente']} |")
report += ["", "## Casos planificados de R1: índice de cobertura histórica", "", "El inventario de pruebas reales del código se mantiene separado. AT/ST/CT/MT/PT aquí son nombres del plan; no se infiere que existan, se ejecutaran o aprobaran. La relación original puede contener errores semánticos.", "", "| CA base | Pruebas planificadas | Fuente | Estado nuevo |", "|---|---|---|---|"]
for m in matrix:
    report.append(f"| {m['criterio']} | {', '.join(m['pruebas_planificadas'])} | {m['fuente']} | NO EJECUTADO |")
report += ["", "## Adicionales observados, conflictos, propuestas y cursor", "", "Véase `ETAPA-00-conflictos-planificacion.md`, que distingue observación estática, declaraciones de otras sesiones y decisiones pendientes. El índice no cambia la selección de 09 ni los resultados históricos. Próximo cursor documental: ETAPA 01, HU-AUTH-01/CA-01 (08:18), cotejarlo con el ingreso y permisos de servidor; antes de tratar HU-AUTH-02, revisar la sustitución del caso BUG-026 y registrar la vigencia de los casos de 03."]
(OUT / "ETAPA-00-planificacion.md").write_text("\n".join(report)+"\n", encoding="utf-8")
print(json.dumps({"hu": len(stories), "ca_base":sum(len(s['criterios']) for s in stories), "reglas":len(rules), "tareas":len(tasks), "ca_matriz_r1":len(matrix)}, ensure_ascii=False))
