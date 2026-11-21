"""Inventario de plantilla por variante de render. Sin arranque Django ni acceso a BD."""
import argparse
import ast
import hashlib
import json
import re
from html import unescape
from html.parser import HTMLParser
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
PRODUCT = ROOT / "r1-pmv"
# Ruta y rol se refieren a la pantalla, no conceden acceso a todos sus botones.
SCREENS = [
    ("identity/base", "marco de todas las rutas", "según rama", "HU-AUTH-01; RN-29; CT-COHERENCIA-UI"),
    ("identity/login", "/", "visitante", "HU-AUTH-01"),
    ("identity/dashboard", "/inicio/", "A M V", "DEC-07-VENCIDOS-FILTRO; RN-29"),
    ("identity/logout_confirm", "/salir/", "A M V", "HU-AUTH-03"),
    ("catalog/category_list", "/productos/categorias/", "A", "HU-CAT-01; PROP-E00-HU-02"),
    ("catalog/category_form", "/productos/categorias/nueva/", "A", "HU-CAT-02"),
    ("catalog/category_state_confirm", "/productos/categorias/{id}/estado/confirmar/", "A", "PROP-E00-HU-02"),
    ("catalog/product_list", "/productos/", "A M", "HU-PROD-01; HU-PROD-04; HU-PROD-05; RN-06"),
    ("catalog/product_form", "/productos/nuevo/", "A", "HU-PROD-02; HU-PROD-03"),
    ("catalog/barcode_capture", "/productos/nuevo/ (diálogo)", "A", "HU-PROD-03"),
    ("catalog/product_created", "/productos/{id}/registrado/", "A", "HU-PROD-02"),
    ("catalog/product_expirations", "/productos/vencimientos/", "A M", "HU-PROD-06; DEC-07-VENCIDOS-FILTRO"),
    ("inventory/supplier_list", "/inventario/proveedores/", "A M", "HU-PROV-01; HU-PROV-04"),
    ("inventory/supplier_form", "/inventario/proveedores/nuevo/", "A", "HU-PROV-02; DEC-04-RUC-VALIDACION"),
    ("inventory/initial_load_form", "/inventario/carga-inicial/", "M", "HU-INV-01a; DEC-05-LOTE-ESPACIOS"),
    ("inventory/initial_load_created", "/inventario/cargas/{id}/", "A M", "HU-INV-01a; HU-INV-01b; DOC-03AI-01"),
    ("inventory/stock_overview", "/inventario/stock/", "A M", "RN-03; RN-06; DEC-07-VENCIDOS-FILTRO"),
    ("inventory/writeoff_form", "/inventario/bajas/nueva/", "A M", "HU-INV-02; RN-05; RN-20"),
    ("inventory/product_movements", "/inventario/productos/{id}/movimientos/", "A M", "HU-INV-04; DEC-08-KARDEX-COMPRAS"),
    ("cash/cash_open", "/caja/abrir/", "V", "HU-CAJA-01"),
    ("cash/cash_shift_opened", "/caja/turnos/{id}/abierto/", "V propio", "HU-CAJA-01; HU-CAJA-02"),
    ("cash/cash_close", "/caja/cerrar/", "V", "HU-CAJA-02; RN-30"),
    ("cash/cash_shift_closed", "/caja/turnos/{id}/cerrado/", "V propio; A", "HU-CAJA-02; HU-CAJA-05"),
    ("cash/cash_shift_history", "/caja/turnos/", "V propio; A", "HU-CAJA-05; DEC-12-PERMISOS-HISTORIAL-Y-MENU"),
    ("sales/sales_draft", "/ventas/", "V propio", "HU-VEN-01b; RN-03; RN-27; RN-30"),
    ("sales/sales_checkout", "/ventas/cobrar/", "V propio", "HU-VEN-01c; DEC-11-DESCUENTOS-ALCANCE; RN-25; RN-27"),
    ("sales/sales_receipt", "/ventas/constancia/{id}/", "V propio; A", "HU-VEN-02a; RN-26; RN-27"),
    ("sales/sales_shift_history", "/ventas/historial/turno/", "V propio", "HU-VEN-05a"),
    ("sales/sales_history", "/ventas/historial/", "V propio; A", "HU-VEN-05b; RN-07; DEC-12-ORDEN-LINEAS-RECIBO"),
    ("403", "respuesta 403", "rol denegado", "HU-AUTH-01/CA-04; RN-29"),
]
PLACE = re.compile(r"{%.*?%}|{#.*?#}|{{.*?}}", re.S)
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}


class Template(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tokens = []
        self.rows = []
        self.stack = []
        self.condition = []
        self.source = source

    def expand(self, token):
        return re.sub(r"TPL(\d+)END", lambda m: self.tokens[int(m[1])], token)

    def row(self, kind, content, line, tag=None):
        content = " ".join(unescape(content).split())
        if content:
            self.rows.append(dict(linea=line, tipo=kind, nodo=tag or (self.stack[-1] if self.stack else ""), variante=list(self.condition), literal=content))

    def handle_starttag(self, tag, attrs):
        line = self.getpos()[0]
        attrs = dict(attrs)
        for attr in ("aria-label", "placeholder", "title", "alt", "href", "action", "onclick"):
            if attr in attrs:
                self.row(attr, self.expand(attrs[attr] or ""), line, tag)
        if tag in {"button", "input", "select", "textarea", "form"}:
            attrs_text = " ".join(f"{k}={self.expand(attrs[k])}" for k in ("method", "type", "name", "value", "min", "max", "maxlength", "step") if attrs.get(k))
            self.row("control", attrs_text or tag, line, tag)
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in self.stack:
            last = len(self.stack) - self.stack[::-1].index(tag) - 1
            del self.stack[last:]

    def handle_data(self, data):
        if any(x in self.stack for x in ("script", "style")):
            return
        # Los fragmentos de una misma frase separada por un elemento inline conservan su línea y nodo.
        line = self.getpos()[0]
        for part in re.split(r"(TPL\d+END)", data):
            expanded = self.expand(part)
            if expanded.startswith("{%"):
                expression = " ".join(expanded[2:-2].split())
                if expression.startswith(("if ", "for ")):
                    self.condition.append(expression)
                elif expression.startswith("elif ") and self.condition:
                    self.condition[-1] = expression
                elif expression in {"empty", "else"} and self.condition:
                    self.condition[-1] = expression + " [" + self.condition[-1] + "]"
                elif expression in {"endif", "endfor"} and self.condition:
                    self.condition.pop()
            elif not expanded.startswith("{#"):
                self.row("variable" if expanded.startswith("{{") else "texto", expanded, line + len(part) - len(part.lstrip("\n")))
            line += part.count("\n")

    def parse(self):
        def protect(match):
            self.tokens.append(match[0])
            return f"TPL{len(self.tokens)-1}END" + "\n" * match[0].count("\n")
        self.feed(PLACE.sub(protect, self.source))
        self.close()
        return self.rows


def visible_python(path, names):
    module = ast.parse(path.read_text(encoding="utf-8"))
    rows = []
    # Se filtran cadenas que parecen mensajes/etiquetas, sin serializar datos de sesión.
    for node in module.body:
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef)) or node.name not in names:
            continue
        for child in ast.walk(node):
            if isinstance(child, (ast.Constant, ast.JoinedStr)):
                if isinstance(child, ast.JoinedStr):
                    raw = ast.unparse(child)
                elif isinstance(child.value, str):
                    raw = child.value
                else:
                    continue
                if not 3 < len(raw) < 500 or "\n" in raw or (not any(c.isspace() for c in raw) and not any(c in raw for c in "áéíóúñ")):
                    continue
                if raw == ast.get_docstring(node):
                    continue
                rows.append(dict(linea=child.lineno, funcion=node.name, cadena=raw))
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("salida", type=Path)
    destination = parser.parse_args().salida
    files = []
    for name, route, roles, requirement in SCREENS:
        if "/" in name:
            app, short = name.split("/")
            path = PRODUCT / app / "templates" / app / (short + ".html")
        else:
            path = PRODUCT / "templates" / (name + ".html")
        files.append(dict(fuente=path.relative_to(ROOT).as_posix(), sha256=hashlib.sha256(path.read_bytes()).hexdigest(), ruta=route, roles=roles, requisito_de_pantalla=requirement, elementos=Template(path.read_text(encoding="utf-8")).parse()))
    extra = {
        "identity/forms": "LoginForm",
        "catalog/forms": "CategoryForm ProductRegistrationForm",
        "inventory/forms": "InitialLoadProductForm LotInputForm BaseLotInputFormSet StockWriteOffForm SupplierForm ReceiptSupplierChoiceField ReceiptSupplierSelect",
        "cash/forms": "CashOpeningForm CashCloseForm _clean_cash_amount",
        "sales/forms": "ProductSearchForm AddDraftLineForm UpdateDraftLineForm CheckoutForm",
        "catalog/services": "create_category register_canned_product toggle_product_availability toggle_category_status",
        "inventory/services": "confirm_initial_load _validate_lots create_supplier write_off_stock toggle_supplier_status",
        "cash/services": "open_cash_shift close_cash_shift",
        "sales/services": "add_product_to_draft checkout_sale _verify_idempotent_sale _own_open_shift",
        "catalog/views": "category_create category_toggle product_toggle_availability product_expirations",
        "inventory/views": "supplier_create supplier_toggle stock_writeoff_create product_movements",
        "cash/views": "cash_shift_history",
        "sales/views": "sales_draft sales_checkout sales_draft_discard sales_history",
    }
    strings = {}
    for file, names in extra.items():
        p = PRODUCT / (file + ".py")
        strings[file] = visible_python(p, names.split())
    destination.write_text(json.dumps({"metodo":"Fuente estática. Cada rama/variable requiere evidencia de su propio estado. Las cadenas Python son candidatas; incluyen fragmentos técnicos y de formatos.", "plantillas": files, "cadenas_por_componente": strings}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
