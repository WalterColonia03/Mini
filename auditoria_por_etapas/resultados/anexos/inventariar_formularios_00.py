"""Censo de metadatos de formularios usando el Django instalado, sin ejecutar SQL."""
import ast
import inspect
import json
import os
import sys
from collections import Counter
from importlib import import_module
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
APP = ROOT / "r1-pmv"
sys.path[:0] = [str(HERE.parent / "soporte"), str(APP)]
os.environ["DJANGO_SETTINGS_MODULE"] = "audit_settings"

import django

django.setup()
from django import forms
from django.conf import settings
from django.db import connection
from django.utils.translation import override


def source(obj):
    path = Path(inspect.getsourcefile(obj))
    return f"{path.relative_to(ROOT).as_posix()}:{inspect.getsourcelines(obj)[1]}"


def forbid_sql(*args, **kwargs):
    raise RuntimeError("La extracción debe permanecer libre de SQL")


def describe_validator(val):
    target = val if inspect.isfunction(val) else type(val)
    out = {"tipo": target.__name__, "fuente": source(target)}
    for name in ("limit_value", "code", "message"):
        value = getattr(val, name, None)
        if value is not None and not callable(value):
            out[name] = str(value) or "Plural en tiempo de validación (ver fuente)"
    return out


def symbols(path):
    return ast.parse(path.read_text(encoding="utf-8-sig")).body


def class_fields(cls_node):
    return {node.targets[0].id: node.lineno for node in cls_node.body
            if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)}


def field_record(form, name, field, source_hint):
    bf = form[name]
    widget = field.widget
    rec = {"nombre": name, "etiqueta": str(bf.label), "fuente": source_hint,
           "clase": type(field).__name__, "implementacion_campo": source(type(field)),
           "widget": type(widget).__name__, "input_type": getattr(widget, "input_type", None),
           "oculto": widget.is_hidden, "obligatorio_form": field.required,
           "attrs_widget": widget.attrs, "ayuda": str(field.help_text),
           "inicial_sin_instancia": field.initial if not callable(field.initial) else "función",
           "limites": {}, "validadores": [describe_validator(v) for v in field.validators],
           "mensajes_de_campo": {k: str(v) or "Plantilla plural (ver implementación)"
                                 for k, v in field.error_messages.items()}}
    for attr in ("strip", "min_length", "max_length", "min_value", "max_value",
                 "max_digits", "decimal_places", "input_formats"):
        value = getattr(field, attr, None)
        if value is not None:
            rec["limites"][attr] = list(value) if attr == "input_formats" else value
    if isinstance(field, forms.ModelChoiceField):
        rec["opciones"] = {"modelo": field.queryset.model._meta.label, "vacía": field.empty_label,
                           "selección": "QuerySet perezoso; ver origen de clase/__init__"}
    elif isinstance(field, forms.ChoiceField):
        rec["opciones"] = [[k, str(v)] for k, v in field.choices]
    clean_func = getattr(type(form), "clean_" + name, None)
    if clean_func:
        rec["limpieza_adicional"] = source(clean_func)
    return rec


def get_forms():
    records = []
    for fpath in sorted(APP.glob("*/forms.py")):
        module = import_module(f"{fpath.parent.name}.forms")
        for node in symbols(fpath):
            if not isinstance(node, ast.ClassDef):
                continue
            cls = getattr(module, node.name)
            if not issubclass(cls, forms.BaseForm):
                continue
            form = cls()
            fields = class_fields(node)
            rows = []
            for name, field in form.fields.items():
                if name in fields:
                    origin = f"{fpath.relative_to(ROOT).as_posix()}:{fields[name]}"
                else:
                    mdl = cls._meta.model
                    mfile = Path(inspect.getsourcefile(mdl))
                    mnode = next(n for n in symbols(mfile)
                                 if isinstance(n, ast.ClassDef) and n.name == mdl.__name__)
                    origin = f"{mfile.relative_to(ROOT).as_posix()}:{class_fields(mnode)[name]}"
                rows.append(field_record(form, name, field, origin))
            records.append({"modulo": fpath.parent.name, "formulario": cls.__name__, "fuente": source(cls),
                            "campos": rows})
    return records


def main():
    with connection.execute_wrapper(forbid_sql), override(settings.LANGUAGE_CODE):
        records = get_forms()
        from inventory.forms import LotInputFormSet
        from identity.forms import LoginForm
        lots = LotInputFormSet(prefix="lots")
        mgmt = lots.management_form
        setup = {k: getattr(lots, k) for k in ("prefix", "extra", "min_num", "max_num", "absolute_max",
                                                "validate_min", "validate_max", "can_delete", "can_order")}
        setup["filas_iniciales_sin_datos"] = lots.total_form_count()
        setup["campos_gestion"] = [{**field_record(mgmt, n, f, source(type(mgmt))),
                                    "inicial_gestion": mgmt.initial.get(n), "nombre_html": mgmt[n].html_name}
                                   for n, f in mgmt.fields.items()]
        setup["mensajes"] = {k: str(v) or "Plural según cantidad" for k, v in lots.error_messages.items()}
        login = LoginForm()
        html = {bf.name: str(bf) for bf in login}
        counts = Counter(r["modulo"] for r in records)
        payload = {"django": django.get_version(), "idioma": settings.LANGUAGE_CODE,
                   "alcance": "Metadatos sin SQL, formulario vacío por defecto, sin petición HTTP",
                   "formularios_por_modulo": counts, "formularios": records, "LotInputFormSet": setup,
                   "widgets_login_inicial": html}
    dst = HERE / "ETAPA-00-formularios-generados.json"
    dst.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(f"{len(records)} formularios, {sum(len(r['campos']) for r in records)} campos, "
          f"{len(setup['campos_gestion'])} campos de gestión, 1 formset. {dst.name}")


if __name__ == "__main__":
    main()
