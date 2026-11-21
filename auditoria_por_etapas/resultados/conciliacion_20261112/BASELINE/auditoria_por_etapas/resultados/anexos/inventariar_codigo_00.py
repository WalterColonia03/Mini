"""Inventario estático reproducible. No importa Django, no conecta ni escribe BD."""
from pathlib import Path
import ast
import csv
import hashlib
import json
import re
from collections import Counter
from html import unescape
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
OUT = Path(__file__).resolve().parent
MODULES = ("identity", "catalog", "inventory", "cash", "sales")
PREFIXES = {"identity": "", "catalog": "productos/", "inventory": "inventario/", "cash": "caja/", "sales": "ventas/"}
rows = []
sources = {}

def compact(value):
    return " ".join(str(value).split())

def source(path):
    data = path.read_bytes()
    sources[path.relative_to(ROOT).as_posix()] = hashlib.sha256(data).hexdigest()
    return data.decode("utf-8-sig")

def add(kind, module, path, line, identifier, detail, **extra):
    rows.append({"tipo": kind, "modulo": module, "fuente": path.relative_to(ROOT).as_posix(), "linea": line,
                 "identificador": identifier, "detalle": compact(detail), "estado": "NO EXAMINADO", **extra})

views = {}
for module in MODULES:
    path = APP / module / "views.py"
    tree = ast.parse(source(path))
    for node in tree.body:
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        decorators = [ast.unparse(d) for d in node.decorator_list]
        roles = next((d for d in decorators if d.startswith("roles_required(")), "autenticado" if "login_required" in decorators else "publico/inspeccionar")
        methods = next((d for d in decorators if d.startswith("require_")), "sin decorador HTTP explícito")
        templates = sorted({a.args[1].value for a in ast.walk(node) if isinstance(a, ast.Call) and ast.unparse(a.func) == "render" and len(a.args) > 1 and isinstance(a.args[1], ast.Constant)})
        views[module, node.name] = {"roles": roles, "metodos": methods, "vista": f"{path.relative_to(ROOT).as_posix()}:{node.lineno}", "plantillas": ", ".join(templates)}
        add("vista", module, path, node.lineno, node.name, "; ".join(decorators) or "función auxiliar sin decoradores", **views[module, node.name])
    path = APP / module / "urls.py"
    tree = ast.parse(source(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and ast.unparse(node.func) == "path":
            route = ast.literal_eval(node.args[0])
            fn = ast.unparse(node.args[1]).split(".")[-1]
            name = next((ast.literal_eval(k.value) for k in node.keywords if k.arg == "name"), "")
            add("ruta", module, path, node.lineno, name, "/" + PREFIXES[module] + route, **views.get((module, fn), {}))

for module in (*MODULES, "app_platform", "config"):
    for path in sorted((APP / module).glob("*.py")):
        if path.name in {"urls.py", "views.py"}:
            if path.name == "views.py":
                text = source(path)
            else:
                continue
        elif path.name not in {"models.py", "forms.py", "services.py", "admin.py", "authorization.py", "test_runner.py"} and not path.name.startswith("test"):
            continue
        else:
            text = source(path)
        tree = ast.parse(text)
        for cls in (n for n in tree.body if isinstance(n, ast.ClassDef)):
            bases = ", ".join(ast.unparse(b) for b in cls.bases)
            fields = []
            for n in cls.body:
                if isinstance(n, ast.Assign) and isinstance(n.value, ast.Call) and (ast.unparse(n.value.func).startswith(("forms.", "models.")) or ast.unparse(n.value.func) == "RoleChoiceField"):
                    name = ast.unparse(n.targets[0])
                    fields.append(name)
                    add("campo_formulario" if path.name == "forms.py" else "campo_modelo", module, path, n.lineno, f"{cls.name}.{name}", ast.unparse(n.value))
            if path.name in {"models.py", "forms.py"}:
                kind = ("campo_personalizado" if cls.name == "RoleChoiceField" else "formulario") if path.name == "forms.py" else ("manager" if cls.name == "AccountManager" else "modelo")
                add(kind, module, path, cls.lineno, cls.name, f"bases={bases}; campos directos={', '.join(fields)}")
            if path.name == "forms.py":
                for meta in (n for n in cls.body if isinstance(n, ast.ClassDef) and n.name == "Meta"):
                    metadata = {ast.unparse(n.targets[0]): n for n in meta.body if isinstance(n, ast.Assign)}
                    if "fields" in metadata:
                        for field in ast.literal_eval(metadata["fields"].value):
                            add("campo_formulario_modelo", module, path, metadata["fields"].lineno, f"{cls.name}.{field}", "Derivado del modelo; ver campo_modelo y configuración del formulario")
                    for key in ("model", "labels", "widgets", "help_texts", "error_messages"):
                        if key in metadata:
                            add("configuracion_formulario", module, path, metadata[key].lineno, f"{cls.name}.Meta.{key}", ast.unparse(metadata[key].value))
                for n in ast.walk(cls):
                    if isinstance(n, (ast.Assign, ast.Expr)) and "self.fields[" in ast.unparse(n):
                        add("configuracion_formulario", module, path, n.lineno, cls.name, ast.unparse(n))
            for n in cls.body:
                if isinstance(n, ast.FunctionDef) and n.name.startswith("test_"):
                    add("prueba_definida", module, path, n.lineno, f"{cls.name}.{n.name}", "Definición estática; NO EJECUTADA en este inventario")
        if path.name in {"services.py", "authorization.py"}:
            for n in tree.body:
                if isinstance(n, ast.FunctionDef):
                    add("servicio", module, path, n.lineno, n.name, ast.unparse(n.args))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = ast.unparse(node.func)
                if name.split(".")[-1] in {"ValidationError", "PermissionDenied", "Http404"} or name.startswith("messages.") or name.endswith(".add_error"):
                    add("mensaje_servidor", module, path, node.lineno, name, ast.unparse(node))
                if name in {"models.CheckConstraint", "models.UniqueConstraint"}:
                    add("restriccion_modelo", module, path, node.lineno, name, ast.unparse(node))
                if name in {"MaxValueValidator", "MinValueValidator"}:
                    add("validador", module, path, node.lineno, name, ast.unparse(node))
            if path.name == "admin.py" and isinstance(node, ast.ClassDef):
                add("admin_clase", module, path, node.lineno, node.name, ast.unparse(node.bases[0]) if node.bases else "")

class TemplateInventory(HTMLParser):
    def __init__(self, path, module):
        super().__init__(convert_charrefs=True)
        self.path, self.module, self.stack = path, module, []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.stack.append(tag) if tag not in {"input", "meta", "link", "br", "hr", "img"} else None
        if tag in {"form", "input", "select", "textarea", "button", "a", "th", "label", "h1", "h2", "h3", "output"}:
            key = attrs.get("name", attrs.get("id", attrs.get("href", tag)))
            allowed = {k: v for k, v in attrs.items() if k in {"name", "id", "type", "value", "href", "action", "method", "required", "min", "max", "step", "minlength", "maxlength", "placeholder", "for", "onclick", "data-testid", "disabled", "aria-label"}}
            add("elemento_ui", self.module, self.path, self.getpos()[0], f"{tag}:{key}", json.dumps(allowed, ensure_ascii=False))
    def handle_endtag(self, tag):
        if tag in self.stack:
            self.stack = self.stack[:len(self.stack) - 1 - self.stack[::-1].index(tag)]
    def handle_data(self, data):
        if "script" in self.stack or "style" in self.stack:
            return
        text = compact(re.sub(r"\{%.*?%\}|\{#.*?#\}", "", data, flags=re.S))
        if text:
            add("texto_salida_ui", self.module, self.path, self.getpos()[0], self.stack[-1] if self.stack else "texto", unescape(text))

for path in sorted(APP.rglob("*.html")):
    if ".venv" in path.parts:
        continue
    module = path.relative_to(APP).parts[0]
    text = source(path)
    add("plantilla", module, path, 1, path.name, "Plantilla fuente; presencia en navegador y estados condicionales NO EJECUTADOS")
    TemplateInventory(path, module).feed(text)
    for match in re.finditer(r"\{\{\s*(.*?)\s*\}\}", text, flags=re.S):
        add("salida_dinamica_ui", module, path, text[:match.start()].count("\n") + 1, compact(match.group(1)), "Expresión de plantilla; valores, formatos, límites y persistencia pendientes de la etapa funcional")
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(r"addEventListener|\.textContent|alert\(|confirm\(|window.print|onclick=", line):
            add("accion_javascript", module, path, i, "interacción en plantilla", line.strip())

config = APP / "config" / "urls.py"
source(config)
add("montaje_admin", "config", config, 5, "admin.site.urls", "/admin/; subrutas generadas por Django pendientes de expansión; no equivalente a las 41 rutas explícitas de negocio")

fieldnames = ["tipo", "modulo", "fuente", "linea", "identificador", "detalle", "estado", "roles", "metodos", "vista", "plantillas"]
with (OUT / "ETAPA-00-inventario-codigo.csv").open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
(OUT / "ETAPA-00-fuentes-codigo.json").write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
summary = {module: dict(Counter(r["tipo"] for r in rows if r["modulo"] == module)) for module in sorted({r["modulo"] for r in rows})}
(OUT / "ETAPA-00-conteos-codigo.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(summary, ensure_ascii=False, indent=2))
