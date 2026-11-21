"""Index the application's rendered surfaces by static source, without loading Django."""
import ast
import csv
import json
import re
from collections import Counter, defaultdict
from functools import cache
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
APP = ROOT / "r1-pmv"


def read_csv(name):
    with (OUT / name).open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


@cache
def lines(source):
    return (ROOT / source).read_text(encoding="utf-8-sig").splitlines()


code = read_csv("ETAPA-00-inventario-codigo.csv")
routes = {r["identificador"]: r for r in code if r["tipo"] == "ruta"}
inverse = {r["nombre"]: r for r in read_csv("ETAPA-00-cobertura-inversa.csv")
           if not r["ruta"].startswith("/admin/")}
assert set(routes) == set(inverse)
plan = json.loads((OUT / "ETAPA-00-planificacion.json").read_text(encoding="utf-8"))
rules = {r["id"]: r.get("reglas", []) for r in plan["historias"]}
route_templates = defaultdict(list)
route_views = defaultdict(list)
for name, route in routes.items():
    for template in filter(None, route["plantillas"].split(", ")):
        route_templates[template].append(name)
    route_views[route["vista"]].append(name)

SHARED = {
    "identity/base.html": ("Plantilla común", "Visitante / ADMIN / ALMACENERO / VENDEDOR", "01, 02, 14"),
    "403.html": ("Respuesta 403 de Django", "Condicionado a la denegación y sesión", "01, 15"),
    "404.html": ("Respuesta 404 de Django", "Visitante o rol de la sesión", "15"),
    "identity/protected_placeholder.html": ("Sin llamada render localizada", "Sin actor operativo asignado", "17"),
}
# Candidate routes for DTO, model and service validation that runs behind views.
HELPERS = {
    "_validate_strong_password": "employee-create employee-edit",
    "INVALID_CREDENTIALS_MESSAGE": "login",
    "create_employee": "employee-create", "update_employee": "employee-edit",
    "deactivate_employee": "employee-deactivate", "reactivate_employee": "employee-deactivate",
    "CategoryForm": "category-create", "Product": "product-entry product-edit",
    "ProductEditForm": "product-edit", "ProductRegistrationForm": "product-entry",
    "create_category": "category-create", "register_canned_product": "product-entry",
    "toggle_category_status": "category-toggle", "toggle_product_availability": "product-toggle",
    "update_product": "product-edit", "_attach_validation_error": "category-create product-entry product-edit",
    "LotInputForm": "inventory-load stock-entry", "PhysicalAdjustmentForm": "physical-adjustment",
    "SupplierForm": "supplier-create", "Lot": "inventory-load stock-entry",
    "_validate_lots": "inventory-load stock-entry", "confirm_initial_load": "inventory-load",
    "create_supplier": "supplier-create", "register_physical_adjustment": "physical-adjustment",
    "register_stock_entry": "stock-entry", "toggle_supplier_status": "supplier-toggle",
    "write_off_stock": "stock-writeoff", "_get_lot_or_404": "stock-writeoff physical-adjustment",
    "CashCloseForm": "cash-close", "CashOpeningForm": "cash-open",
    "close_cash_shift": "cash-close", "open_cash_shift": "cash-open",
    "CheckoutForm": "sales-checkout", "_own_open_shift": "sales-draft sales-line-update sales-line-remove sales-checkout",
    "_require_seller": "sales-draft sales-line-update sales-line-remove sales-draft-discard sales-checkout",
    "add_product_to_draft": "sales-draft", "checkout_sale": "sales-checkout",
    "remove_draft_line": "sales-line-remove", "update_draft_line": "sales-line-update",
    "_add_validation_error": "sales-draft sales-checkout",
}


@cache
def scopes(source):
    tree = ast.parse("\n".join(lines(source)))
    return [n for n in ast.walk(tree) if isinstance(n, (ast.ClassDef, ast.FunctionDef))]


def scope_routes(source, line, identifier):
    nodes = [n for n in scopes(source) if n.lineno <= line <= n.end_lineno]
    nodes.sort(key=lambda n: n.lineno)
    for node in nodes:
        direct = route_views.get(f"{source}:{node.lineno}")
        if direct:
            return direct
        if node.name in HELPERS:
            return HELPERS[node.name].split()
    return HELPERS.get(identifier, "").split()


def join(values):
    return " | ".join(dict.fromkeys(filter(None, values)))


CHECK = {
    "Navegación": "Seguir enlace con rol autorizado y contrastar ruta, objeto y permiso de destino.",
    "Acción": "Ejercer acción autorizada y observar respuesta, persistencia, reintento y rechazo sin mutación.",
    "Entrada": "Inspeccionar widget y valor inicial. En la etapa funcional comprobar límites, rechazo y persistencia.",
    "Error": "Provocar condición documentada y cotejar mensaje, ubicación, permiso y datos tras el rechazo.",
    "Confirmación": "Ejecutar operación con fixture y comparar confirmación con el registro guardado.",
    "Cálculo local": "Variar entrada en navegador y comparar importe mostrado con respuesta del servidor.",
    "Impresión": "Abrir vista previa y contrastar contenido, controles ocultos y permisos.",
    "Rama": "Preparar estados descritos y examinar salida correspondiente, incluidos vacíos y roles.",
    "Texto": "Localizar texto o ayuda en la pantalla que lo consume y contrastarlo con la operación descrita.",
    "Dato": "Contrastar valor mostrado con fixture, formato, actor y registro de origen.",
    "Estructura": "Revisar etiquetas, encabezados y orientación visual con rol y estado aplicables.",
}


def classify(t, ident, detail):
    tag = ident.split(":")[0]
    expr = (ident + " " + detail).lower()
    if t == "plantilla":
        return "Estructura"
    if t in ("rama_plantilla", "estado_css"):
        return "Rama"
    if t == "accion_javascript" or t == "calculo_js":
        return "Impresión" if "window.print" in detail else "Cálculo local"
    if t == "mensaje_servidor" or t == "mensaje_constante":
        return "Confirmación" if ident == "messages.success" else "Error" if ident != "messages.info" else "Texto"
    if t in {"destino_plantilla", "redireccion_servidor"}:
        return "Navegación"
    if t == "recurso_estatico": return "Estructura"
    if t == "proteccion_formulario":
        return "Entrada"
    if t == "elemento_ui":
        if tag == "a": return "Navegación"
        if tag in {"form", "button"}: return "Impresión" if "window.print" in detail else "Acción"
        if tag in {"input", "select", "textarea", "label"}: return "Entrada"
        return "Dato" if tag == "output" else "Estructura"
    if "error" in expr: return "Error"
    if tag in {"h1", "h2", "h3", "th", "dt", "legend"}: return "Estructura"
    if tag == "a": return "Navegación"
    if tag == "button": return "Acción"
    if "form." in expr or "field.label" in expr or tag == "label": return "Entrada"
    if t == "salida_dinamica_ui" or "{{" in detail or tag in {"dd", "td", "output"}: return "Dato"
    return "Texto"


url_tag = re.compile(r"""{%\s*url\s+['"]([^'"]+)['"]""")
token = re.compile(r"{%\s*(.*?)\s*%}")
rows = []
contexts = {}
supplement = []
templates = [r["fuente"] for r in code if r["tipo"] == "plantilla"]
actual = {p.relative_to(ROOT).as_posix() for directory in APP.glob("*/templates")
          for p in directory.rglob("*.html")}
actual.update(p.relative_to(ROOT).as_posix() for p in (APP / "templates").rglob("*.html"))
assert set(templates) == actual
for source in templates:
    stack = []
    for number, line in enumerate(lines(source), 1):
        contexts[source, number] = " / ".join(stack)
        for match in token.finditer(line):
            tag = match.group(1)
            kind = tag.split()[0]
            if kind in {"if", "for"}:
                supplement.append(("rama_plantilla", source, number, kind, tag))
                stack.append(tag)
            elif kind in {"elif", "else", "empty"}:
                supplement.append(("rama_plantilla", source, number, kind, tag + " (rama de " + stack[-1] + ")"))
                if kind == "elif":
                    stack[-1] = tag
                else:
                    stack[-1] = kind + " (" + stack[-1] + ")"
            elif kind in {"endif", "endfor"}:
                stack.pop()
            elif kind == "url":
                supplement.append(("destino_plantilla", source, number, kind, match.group(0)))
            elif kind == "csrf_token":
                supplement.append(("proteccion_formulario", source, number, kind, "Control CSRF de la petición"))
            elif kind == "static":
                resource = tag.split()[1].strip("'\"")
                assert (APP / resource.split("/")[0] / "static" / resource).is_file()
                supplement.append(("recurso_estatico",source,number,resource,match.group(0)))
    assert not stack, source

def add(t, source, line, ident, detail, base_row=""):
    page = source.split("/templates/")[-1] if source in templates else ""
    origin = route_templates.get(page, []) if page else []
    if source.endswith(".py"):
        origin = scope_routes(source, line, ident)
    links = [ident] if t == "redireccion_servidor" else url_tag.findall(detail)
    candidates = list(dict.fromkeys([*origin, *(r for r in links if r in routes)]))
    special, actor, stage = SHARED.get(page, ("", "", ""))
    sender = join(routes[r]["roles"].replace("roles_required(Role.Code.", "").replace("Role.Code.", "").replace(")", "").replace("WAREHOUSE","ALMACENERO").replace("SELLER","VENDEDOR") for r in origin)
    owner = sender or actor
    if not owner:
        owner = "Transversal (según ruta y sesión)"
    hu = [h for r in candidates for h in inverse[r]["hu_candidatas"].split("; ") if h]
    phase = [e for r in candidates for e in inverse[r]["etapa_siguiente"].split("; ") if e]
    qas = [inverse[r]["grupos_qa_candidatos"] for r in candidates]
    context = contexts.get((source,line), "")
    if "dashboard" in origin:
        phase.append("13")
        if "summary." in (ident + detail + context):
            hu += ["HU-DASH-01", "HU-DASH-03"]
    if "discount" in (ident + detail).lower() or "descuento" in detail.lower():
        hu.append("PROP-E00-HU-01")
    if "category-toggle" in candidates: hu.append("PROP-E00-HU-02")
    if "stock-overview" in candidates: hu.append("PROP-E00-HU-04")
    if "dashboard" in origin and "summary." in (ident+detail+context): hu.append("PROP-E00-HU-03")
    if source.endswith("authorization.py"):
        phase += ["01", "15"]; hu += ["HU-AUTH-01"]
    if source.endswith("app.css"):
        phase += ["12", "15"]
    if page == "identity/protected_placeholder.html":
        hu = []
    rn = [rule for h in hu for rule in rules.get(h, [])]
    if page in {"403.html","404.html","identity/base.html"} or source.endswith("authorization.py"):
        rn += ["RN-29"]
    category = classify(t, ident, detail)
    scope = special or ("Rutas candidatas" if origin else "Sin ruta de negocio directa")
    fields = [base_row, t, source, line, ident, detail, category, scope,
              join(origin), owner, context, join(links), join(hu), join(rn), join(qas),
              join([*phase,stage]) or "15", CHECK[category], "NO EJECUTADO EN ESTE ÍNDICE"]
    rows.append(fields)


types = {"texto_salida_ui", "salida_dinamica_ui", "elemento_ui", "accion_javascript", "mensaje_servidor", "plantilla"}
for record, row in enumerate(code, 1):
    line = int(row["linea"])
    assert 1 <= line <= len(lines(row["fuente"])), (record,row["fuente"],line)
    if row["tipo"] in types:
        add(row["tipo"], row["fuente"], line, row["identificador"], row["detalle"], record)
for source in sorted({r["vista"].rsplit(":",1)[0] for r in routes.values()}):
    tree = ast.parse("\n".join(lines(source)))
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and ast.unparse(n.func) == "redirect" and n.args:
            target = n.args[0]
            dest = target.value if isinstance(target, ast.Constant) else ast.unparse(target)
            supplement.append(("redireccion_servidor",source,n.lineno,dest,ast.unparse(n)))
for source in ("r1-pmv/identity/services.py", "r1-pmv/sales/templates/sales/sales_checkout.html", "r1-pmv/identity/static/identity/app.css"):
    for number, line in enumerate(lines(source), 1):
        if source.endswith(".py") and line.startswith("INVALID_CREDENTIALS_MESSAGE = "):
            supplement.append(("mensaje_constante",source,number,"INVALID_CREDENTIALS_MESSAGE",line.strip()))
        elif source.endswith(".html") and number > 88 and re.search(r"function (cents|fmt|recalc)|var (subtotal|discount|total|base|igv|cash) = |if \(subtotal|return match \?|^\s*recalc\(\);",line):
            supplement.append(("calculo_js",source,number,"previsualización",line.strip()))
        elif source.endswith(".css") and "@media" in line:
            supplement.append(("estado_css",source,number,"medio de presentación",line.strip()))
for item in supplement:
    add(*item)
assert len({r[0] for r in rows if r[0]}) == sum(r["tipo"] in types for r in code)
assert not {r[11] for r in rows if r[1]=="destino_plantilla" and r[11] not in routes}
with (OUT / "ETAPA-00-superficie-ui.csv").open("w",encoding="utf-8-sig",newline="") as stream:
    writer = csv.writer(stream)
    writer.writerow(("fila_origen_desde_1","tipo","fuente","linea","elemento","expresion_o_texto",
                     "funcion","asociacion","rutas_origen","actor_de_la_ruta","contexto_al_inicio_de_linea",
                     "destino_explicito","hu_o_propuesta_candidata","rn_asociadas_a_hu","grupos_qa_de_ruta",
                     "etapa","verificacion_pendiente","estado_ejecucion"))
    writer.writerows(rows)
print("Registros fuente revisados:",len(code))
print("Registros UI reutilizados:",sum(bool(r[0]) for r in rows))
print("Tipos del índice:",dict(Counter(r[1] for r in rows)))
print("Plantillas sin render directo:",[p for p in templates if p.split("/templates/")[-1] not in route_templates])
print("Mutaciones sin render directo:",[r for r in routes if not routes[r]["plantillas"]])
print("Mensajes sin ruta directa:",Counter((r[2],r[4]) for r in rows if r[1]=="mensaje_servidor" and not r[8]))
