"""Expande metadatos del admin instalado y compara el resolver. Inhabilita SQL."""
import inspect
import json
import os
from pathlib import Path
import sys

RESULTADOS = Path(__file__).resolve().parents[1]
APP = RESULTADOS.parents[1] / "r1-pmv"
sys.path.insert(0, str(APP))
os.environ["DJANGO_SETTINGS_MODULE"] = "audit_settings"

import django
from django.db import connection


def rechazar_sql(*args, **kwargs):
    raise RuntimeError("El inventario solo admite inspección de metadatos.")


def campos(form):
    return [
        {"nombre": name, "tipo": field.__class__.__name__,
         "widget": field.widget.__class__.__name__, "obligatorio": field.required}
        for name, field in form.base_fields.items()
    ]


def origen(cls):
    return f"{cls.__module__}.{cls.__qualname__}:{inspect.getsourcelines(cls)[1]}"


def patrones(items, prefijo="", ns=""):
    from django.urls import URLResolver
    for item in items:
        path = prefijo + str(item.pattern)
        if isinstance(item, URLResolver):
            yield from patrones(item.url_patterns, path, ns + (item.namespace + ":" if item.namespace else ""))
        else:
            yield "/" + path, ns + (item.name or ""), item.callback.__module__ + "." + item.callback.__name__


OPERACIONES = {
    "index": "Inicio administrativo", "login": "Formulario de acceso administrativo",
    "logout": "Cerrar sesión técnica", "password_change": "Cambio de clave propia",
    "password_change_done": "Confirmación de cambio", "autocomplete_view": "Respuesta JSON de autocompletado",
    "i18n_javascript": "Recurso de localización JavaScript", "shortcut": "Redirección a objeto",
    "app_index": "Índice por aplicación", "catch_all_view": "Resolución final / error",
    "changelist_view": "Listado, búsqueda, filtros y acciones según registro",
    "add_view": "Formulario de alta", "history_view": "Historial administrativo del objeto",
    "delete_view": "Confirmación de borrado", "change_view": "Ficha y formulario del objeto",
    "view": "Redirección heredada a ficha", "user_change_password": "Formulario de clave de cuenta",
}


with connection.execute_wrapper(rechazar_sql):
    django.setup()
    from django.contrib import admin
    from django.contrib.admin.forms import AdminAuthenticationForm
    from django.contrib.auth import get_user_model
    from django.contrib.auth.forms import AdminPasswordChangeForm, PasswordChangeForm
    from django.test import RequestFactory
    from django.urls import get_resolver

    # El generador de formularios inspecciona permisos del request. El actor
    # transitorio permite enumerar el conjunto máximo sin guardar una cuenta.
    request = RequestFactory().get("/admin/")
    request.user = get_user_model()(is_staff=True, is_active=True, is_superuser=True)
    modelos = {}
    for model, registro in sorted(admin.site._registry.items(), key=lambda pair: pair[0]._meta.label_lower):
        obj = model()
        modelos[model._meta.label_lower] = {
            "registro": origen(registro.__class__),
            "columnas": list(registro.get_list_display(request)),
            "filtros": list(registro.get_list_filter(request)),
            "busqueda": list(registro.get_search_fields(request)),
            "acciones_si_autorizado": list(registro.get_actions(request)),
            "alta": campos(registro.get_form(request)),
            "edicion": campos(registro.get_form(request, obj, change=True)),
            "solo_lectura": list(registro.get_readonly_fields(request, obj)),
            "formularios_en_linea": [
                {"modelo": inline.model._meta.label_lower, "clase": origen(inline.__class__),
                 "campos": campos(inline.get_formset(request, obj).form),
                 "solo_lectura": list(inline.get_readonly_fields(request, obj)), "can_delete": inline.can_delete}
                for inline in registro.get_inline_instances(request, obj)
            ],
        }
    rutas = list(patrones(get_resolver().url_patterns))
    corte = json.loads((RESULTADOS / "evidencias/00-rutas-resueltas.json").read_text(encoding="utf-8"))
    original = [(row["route"], row["name"], row["callback"]) for row in corte]
    if rutas != original:
        raise RuntimeError("El resolver difiere del inventario inicial. Revisar antes de publicar.")
    admin_rutas = [
        {"ruta": ruta, "nombre": nombre, "callback": cb, "funcion": OPERACIONES[cb.rsplit(".", 1)[1]]}
        for ruta, nombre, cb in rutas if ruta.startswith("/admin/")
    ]
    resultado = {
        "django": django.get_version(), "patrones_totales": len(rutas),
        "patrones_admin": len(admin_rutas), "resolver_igual_al_corte_5nov": True,
        "sql": 0, "peticiones_servidas": 0,
        "metodo": "Metadatos de clases con objeto y actor transitorios sin persistencia.",
        "modelos": modelos,
        "formularios_tecnicos": {
            cls.__name__: {"origen": origen(cls), "campos": campos(cls)}
            for cls in (AdminAuthenticationForm, PasswordChangeForm, AdminPasswordChangeForm)
        },
        "rutas_admin": admin_rutas,
    }
(RESULTADOS / "anexos/ETAPA-00-admin-metadatos.json").write_text(
    json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"{len(rutas)} patrones coincidentes, {len(admin_rutas)} administrativos, {len(modelos)} modelos registrados.")
