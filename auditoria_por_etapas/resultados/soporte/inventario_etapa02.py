"""Build the 33 criterion inventory from current source lines, without DB access."""
import hashlib
import json
import re
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[1]
ROOT = RESULTS.parent.parent
SOURCE = ROOT / "08_Historias_de_Usuario.md"
FUTURE = {"HU-AUTH-04a", "HU-AUTH-04b", "HU-AUTH-05", "HU-USR-06", "HU-LOG-01"}
SELECTED = {"HU-AUTH-03", *FUTURE, *(f"HU-USR-{i:02d}" for i in range(1,6))}
OBSERVATIONS = {'HU-AUTH-03/CA-01': ('CUMPLE — muestra', '02-A final A01–A02,A20–A22: tres roles, salida sin borrador con/sin turno, conservación de turno y revocación.', 'DOC-02-05: precisar texto sin turno; eventos técnicos en SEC-15-OBS-02.'), 'HU-AUTH-03/CA-02': ('CUMPLE — muestra', '02-A A08–A14: cancelar conserva; confirmar descarta líneas y sesión sin alterar caja/stock. Dos tests de atomicidad incluidos en regresión163.', 'Concurrencia logout/cobro/alta de línea: etapa15, NO EJECUTADA.'), 'HU-AUTH-03/CA-03': ('CUMPLE — muestra', '02-A A03–A06,A13–A19: Atrás, cookie, URL y POST directo, otro vendedor; repetido tras correcciones.', 'Otros motores/dispositivos y peticiones comerciales en vuelo no ejecutados.'), 'HU-USR-01/CA-01': ('CUMPLE — muestra', '02-B B01: ADMIN desde menú; cinco filas y encabezados cotejados con ORM.', 'Sin pendiente funcional en muestra; volumen/paginación no prometidos.'), 'HU-USR-01/CA-02': ('CUMPLE — muestra', '02-B B02: nombre/correo, mayúsculas, espacios, ausencia de resultados y Limpiar.', 'Unicode avanzado y consulta de longitud extrema no ejecutados; etapa15.'), 'HU-USR-01/CA-03': ('CUMPLE — muestra', '02-B B01,B11–B13: estados Activo/Inactivo y acciones cotejados con ORM.', 'Conservar regresión de estado explícito.'), 'HU-USR-02/CA-01': ('CUMPLE — muestra', '02-B B07–B08: alta desde menú, fila guardada e ingreso de empleado en otra sesión.', 'Ningún pendiente del caso muestreado.'), 'HU-USR-02/CA-02': ('CUMPLE — muestra', '02-B B05,B06; fronteras servidor; PG duplicate_email: una fila y ValidationError controlado.', 'IDNA/normalización internacional conservan decisión transversal.'), 'HU-USR-02/CA-03': ('CUMPLE — muestra', '02-B B04–B08; 9 tests de fronteras: vacío, inválido, 120/121,254/255,7,roles manipulados; incluidos en163.', 'Otros alfabetos/dispositivos no ejecutados; no afirmar dominio infinito cubierto.'), 'HU-USR-02/CA-04': ('CUMPLE — muestra', '02-B B07: mensaje y fila de confirmación con nombre,correo,rol,estado coinciden con ORM.', 'Ningún pendiente de muestra.'), 'HU-USR-03/CA-01': ('PARCIAL / decisión documental', '02-B B09 edita nombre completo; servidor prueba120/121. No hay campos separados nombres/apellidos.', 'DOC-02-03: aprobar campo único o definir separación y migración.'), 'HU-USR-03/CA-02': ('CUMPLE — muestra', '02-B B10,B10A y fronteras: colisión rechazada, correo propio y normalización, error accesible y sin mutación.', 'Conservar regresión; política internacional pendiente.'), 'HU-USR-03/CA-03': ('CUMPLE — muestra', '02-B B09: sesión existente muestra rol nuevo, ventas403/inventario200; B14 turno bloquea cambio; PG ambos órdenes rol/apertura.', 'Admin externo y escritores que omitan servicios: etapa15.'), 'HU-USR-04/CA-01': ('PARCIAL / decisión de confirmación', '02-B B11–B12 y estado6: desactiva, revoca sesión, reenvío no reactiva. PG conserva último ADMIN. Botón directo sin segundo paso.', 'E02-REV-06: decidir si botón explícito constituye confirmación o exigir segundo paso; resultado persistente probado.'), 'HU-USR-04/CA-02': ('CUMPLE — muestra', '02-B B12: sesión anterior redirigida; ingreso de inactivo rechazado con mensaje genérico.', 'Peticiones ya en vuelo no cubiertas en todos los servicios; etapa15.'), 'HU-USR-04/CA-03': ('CUMPLE — muestra', '02-B B15 turno/acta; test history conserva venta/líneas/carga/lote/responsables y consulta ADMIN tras desactivar; stock8.', 'Bajas/ajustes y todos los historiales no ejecutados: etapas08/12/14; no aprobar esos módulos.'), 'HU-USR-05/CA-01': ('PARCIAL / decisión de confirmación', '02-B B13: reactiva y admite credenciales habituales, cookie revocada no revive. Acción directa sin segundo paso.', 'E02-REV-06 y DOC-02-BLOQUEO: confirmación y política de desbloqueo por reactivación.'), 'HU-USR-05/CA-02': ('CUMPLE — muestra', '02-B B13: rol ALMACENERO conservado, inventario200 y venta403 después de nuevo ingreso.', 'Otros endpoints se rigen por RN29; etapa14 integración completa.')}

CODE = {
    "HU-AUTH-03": "identity.views.logout_view; identity/logout_confirm.html; sales.services.discard_active_draft",
    "HU-USR-01": "identity.views.employee_list; identity/employee_list.html",
    "HU-USR-02": "identity.views.employee_create; EmployeeCreationForm; create_employee",
    "HU-USR-03": "identity.views.employee_edit; EmployeeEditForm; update_employee",
    "HU-USR-04": "identity.views.employee_deactivate; deactivate_employee; authenticate_active_account",
    "HU-USR-05": "identity.views.employee_deactivate; reactivate_employee",
}
rows=[]
hu=None
actor=""
for lineno,line in enumerate(SOURCE.read_text(encoding="utf-8").splitlines(),1):
    head=re.match(r"### (HU-[\w-]+) ·",line)
    if head:
        hu=head.group(1)
    if hu not in SELECTED:
        continue
    if line.startswith("- **Historia:**"):
        actor=line.split("Como ",1)[1].split(", quiero",1)[0]
    criterion=re.match(r"  (\d+)\. (.*)",line)
    if not criterion:
        continue
    key=f"{hu}/CA-{int(criterion.group(1)):02d}"
    if hu in FUTURE:
        state="PREVISTO/FUTURO"
        observation="Sin implementación seleccionada; inspección de rutas/modelos/plantillas."
        if hu=="HU-AUTH-04a":
            observation+=" A23 observa dos sesiones ADMIN simultáneas; no certifica este CA."
        next_action="Mantener en backlog; no probar como prestación disponible."
    else:
        state,observation,next_action=OBSERVATIONS[key]
    rows.append({"id":key,"hu":hu,"source":SOURCE.name,"line":lineno,"actor":actor,
                 "expected":criterion.group(2),"scope":"FUTURO" if hu in FUTURE else "R1 SELECCIONADO" if hu=="HU-AUTH-03" else "ADICIONAL IMPLEMENTADO",
                 "location":CODE.get(hu,"Sin ruta/acción específica implementada"),"observed":observation,
                 "status":state,"priority":"P1" if hu=="HU-AUTH-03" else "P2", "next":next_action})
assert len(rows)==33 and len({x["hu"] for x in rows})==11
data={"date":"2026-11-09 America/Lima","source_sha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),"criteria":rows}
(RESULTS / "anexos" / "ETAPA-02-criterios.json").write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf-8")
lines=["# Etapa 02 · Inventario de los 33 criterios", "", "Extraído de las once HU de `08_Historias_de_Usuario.md`. Fecha: 09/11/2026, America/Lima. Cierre 02-D: 15 CA CUMPLE en muestra, 3 PARCIAL por decisión y 15 PREVISTO/FUTURO. Evidencias 02-A final, 02-B, PostgreSQL y regresión163 enlazadas en el informe. Las ubicaciones de código son símbolos, no pruebas. [Informe y evidencias](../ETAPA-02.md).", "", "| ID / fuente | Actor / alcance | Esperado literal | Ubicación | Observado / evidencia | Estado / prioridad | Siguiente acción |", "|---|---|---|---|---|---|---|"]
for row in rows:
    cells=[f"{row['id']} / 08:{row['line']}",f"{row['actor']} / {row['scope']}",row['expected'],row['location'],row['observed'],f"{row['status']} / {row['priority']}",row['next']]
    lines.append("| "+" | ".join(c.replace("|","\\|") for c in cells)+" |")
(RESULTS / "anexos" / "ETAPA-02-criterios.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
print(json.dumps({"hu_count":11,"criterion_count":33,"current":18,"future":15}))
