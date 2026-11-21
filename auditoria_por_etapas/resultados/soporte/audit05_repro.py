"""Pre-fix Stage 05 reproduction probes (isolated SQLite + ephemeral PostgreSQL 18.4).
Never loads operator .env and never mutates existing SQLite DBs.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
SUPPORT = Path(__file__).resolve().parent
PG_BIN = Path("C:/Program Files/PostgreSQL/18/bin")

STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
RUN_DIR = RESULTS / "datos" / f"etapa05-repro-{STAMP}"
OUT_DIR = RESULTS / "evidencias" / f"05-repro-{STAMP}"
RUN_DIR.mkdir(parents=True)
OUT_DIR.mkdir(parents=True)
(RUN_DIR / "marker.json").write_text(
    json.dumps({"run": RUN_DIR.name, "created_utc": STAMP}), encoding="utf-8"
)
(RUN_DIR / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")


def digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


protected = [
    *APP.glob("*.sqlite3"),
    *(RESULTS / "datos").rglob("*.sqlite3"),
    ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
]
start_hashes = {str(p.relative_to(ROOT)): digest(p) for p in protected}

os.environ.update(
    AUDIT05_RUN_DIR=str(RUN_DIR),
    AUDIT05_DEFAULT_COOKIES="1",
    DJANGO_SETTINGS_MODULE="audit05_settings",
)
sys.path.insert(0, str(APP))
sys.path.insert(0, str(SUPPORT))

import django

django.setup()

from django.contrib.auth import load_backend
from django.core.management import call_command
from django.test import Client
from django.test.utils import setup_test_environment

setup_test_environment()
from django.urls import reverse
from django.utils import timezone as tz

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    call_command("migrate", interactive=False, verbosity=0)

from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.forms import LotInputForm, LotInputFormSet
from inventory.models import InitialInventoryLoad, Lot, Supplier
from inventory.services import LotInput, confirm_initial_load

admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

pw = secrets.token_urlsafe(16) + "A1!"
admin = Account.objects.create_user("admin.r5@test.invalid", pw, display_name="Admin R5", role=admin_role)
wh = Account.objects.create_user("wh.r5@test.invalid", pw, display_name="Wh R5", role=wh_role)
seller = Account.objects.create_user("seller.r5@test.invalid", pw, display_name="Seller R5", role=seller_role)
inactive_wh = Account.objects.create_user(
    "wh.inact@test.invalid", pw, display_name="Wh Inact", role=wh_role, is_active=False
)

cat = Category.objects.create(name="Cat Repro05")
prod = Product.objects.create(
    category=cat, name="Producto Repro05", barcode="775050500001", sale_price=Decimal("5.00"), minimum_stock=10
)
prod2 = Product.objects.create(
    category=cat, name="Producto Loaded05", barcode="775050500002", sale_price=Decimal("6.00"), minimum_stock=10
)
today = tz.localdate()
tomorrow = today + timedelta(days=1)
future = today + timedelta(days=45)

load2 = confirm_initial_load(
    actor=wh,
    product=prod2,
    lots=[LotInput("BASE-05", 10, Decimal("2.5000"), future)],
)

client = Client(enforce_csrf_checks=True)
client.force_login(wh)
get_form = client.get(reverse("inventory-load"))
csrf = get_form.cookies["csrftoken"].value

findings: dict[str, object] = {
    "stamp_utc": STAMP,
    "protected_absent_at_start": [k for k, v in start_hashes.items() if v is None],
}

# 1. Empty POST {}
empty_resp = client.post(reverse("inventory-load"), {"csrfmiddlewaretoken": csrf})
empty_html = empty_resp.content.decode("utf-8", errors="replace")
findings["empty_post"] = {
    "status": empty_resp.status_code,
    "has_alert": 'role="alert"' in empty_html or "errorlist" in empty_html,
    "is_bound_bug_reproduced": ('role="alert"' not in empty_html and "errorlist" not in empty_html),
}

# 2. Tampered management_form cases
mgmt_cases = {}
for label, overrides in [
    ("missing_management_form", {"product": str(prod.pk), "lots-0-number": "L1", "lots-0-quantity": "2", "lots-0-unit_cost": "1.00", "lots-0-expiration_date": tomorrow.isoformat()}),
    ("negative_total_forms", {"product": str(prod.pk), "lots-TOTAL_FORMS": "-1", "lots-INITIAL_FORMS": "0", "lots-MIN_NUM_FORMS": "1", "lots-MAX_NUM_FORMS": "1000"}),
    ("alpha_total_forms", {"product": str(prod.pk), "lots-TOTAL_FORMS": "abc", "lots-INITIAL_FORMS": "0", "lots-MIN_NUM_FORMS": "1", "lots-MAX_NUM_FORMS": "1000"}),
    ("huge_total_forms_5000", {"product": str(prod.pk), "lots-TOTAL_FORMS": "5000", "lots-INITIAL_FORMS": "0", "lots-MIN_NUM_FORMS": "1", "lots-MAX_NUM_FORMS": "1000"}),
]:
    c_no_raise = Client(enforce_csrf_checks=True, raise_request_exception=False)
    c_no_raise.force_login(wh)
    c_no_raise.get(reverse("inventory-load"))
    tok = c_no_raise.cookies["csrftoken"].value
    try:
        r = client.post(reverse("inventory-load"), {**overrides, "csrfmiddlewaretoken": csrf})
        mgmt_cases[label] = {"status": r.status_code, "raised": None}
    except Exception as exc:
        r_http = c_no_raise.post(reverse("inventory-load"), {**overrides, "csrfmiddlewaretoken": tok})
        mgmt_cases[label] = {
            "status_with_exception_handler": r_http.status_code,
            "raised": f"{type(exc).__name__}: {exc}",
        }
findings["management_form_tamper"] = mgmt_cases

# 3. LotInputForm NUL byte, Arabic digits, comma decimal, today expiration, all blank
nul_form = LotInputForm(
    data={
        "number": "LOT\x00A",
        "quantity": "2",
        "unit_cost": "1.5000",
        "expiration_date": tomorrow.isoformat(),
    }
)
arabic_form = LotInputForm(
    data={
        "number": "LOT-AR",
        "quantity": "٥",
        "unit_cost": "٢.٥٠",
        "expiration_date": tomorrow.isoformat(),
    }
)
comma_form = LotInputForm(
    data={
        "number": "LOT-COMMA",
        "quantity": "2",
        "unit_cost": "1,50",
        "expiration_date": tomorrow.isoformat(),
    }
)
today_form = LotInputForm(
    data={
        "number": "LOT-TODAY",
        "quantity": "2",
        "unit_cost": "1.50",
        "expiration_date": today.isoformat(),
    }
)
findings["lot_form_checks"] = {
    "nul_byte_form_valid": nul_form.is_valid(),
    "arabic_digits_form_valid": arabic_form.is_valid(),
    "arabic_digits_cleaned": arabic_form.cleaned_data if arabic_form.is_valid() else dict(arabic_form.errors),
    "comma_decimal_form_valid": comma_form.is_valid(),
    "comma_decimal_errors": dict(comma_form.errors),
    "today_expiration_form_valid": today_form.is_valid(),
}

# Combo bug: lot 0 has invalid qty 0, lot 1 has today expiration
combo_resp = client.post(
    reverse("inventory-load"),
    {
        "csrfmiddlewaretoken": csrf,
        "product": str(prod.pk),
        "lots-TOTAL_FORMS": "2",
        "lots-INITIAL_FORMS": "0",
        "lots-MIN_NUM_FORMS": "1",
        "lots-MAX_NUM_FORMS": "1000",
        "lots-0-number": "L-1",
        "lots-0-quantity": "0",
        "lots-0-unit_cost": "1.50",
        "lots-0-expiration_date": tomorrow.isoformat(),
        "lots-1-number": "L-2",
        "lots-1-quantity": "2",
        "lots-1-unit_cost": "1.50",
        "lots-1-expiration_date": today.isoformat(),
    },
)
combo_html = combo_resp.content.decode("utf-8")
findings["combo_lot0_qty0_lot1_today"] = {
    "status": combo_resp.status_code,
    "reports_today_error_on_first_submit": "posterior a hoy en Lima" in combo_html,
}

# All 4 lot rows blank
blank_lots_resp = client.post(
    reverse("inventory-load"),
    {
        "csrfmiddlewaretoken": csrf,
        "product": str(prod.pk),
        "lots-TOTAL_FORMS": "4",
        "lots-INITIAL_FORMS": "0",
        "lots-MIN_NUM_FORMS": "1",
        "lots-MAX_NUM_FORMS": "1000",
    },
)
blank_html = blank_lots_resp.content.decode("utf-8")
findings["all_blank_lots"] = {
    "status": blank_lots_resp.status_code,
    "has_alert": 'role="alert"' in blank_html,
    "contains_al_menos_1": "Envíe al menos 1 formulario" in blank_html or "al menos" in blank_html.lower(),
}

# 4. Space normalization in Lot vs Supplier
findings["lot_normalize_spaces"] = {
    "single_space": Lot.normalize_number("lot 1"),
    "double_space": Lot.normalize_number("lot  1"),
    "collapses_internal_spaces": Lot.normalize_number("lot  1") == Lot.normalize_number("lot 1"),
}

# 5. Service direct unsaved/deleted product
deleted_pk = prod.pk
try:
    missing_prod = Product(pk=secrets.token_bytes(16).hex(), category=cat, name="X", barcode="X", sale_price=Decimal("1.00"))
    confirm_initial_load(actor=wh, product=missing_prod, lots=[LotInput("L-X", 1, Decimal("1.00"), tomorrow)])
    findings["nonexistent_product_service"] = "unexpected_success"
except Exception as exc:
    findings["nonexistent_product_service"] = f"{type(exc).__name__}: {exc}"

# 6. Cache-Control on Stage 05 routes
admin_client = Client(enforce_csrf_checks=True)
admin_client.force_login(admin)
cc_results = {}
for label, c_obj, url in [
    ("inventory-load (WH)", client, reverse("inventory-load")),
    ("inventory-load-created (WH)", client, reverse("inventory-load-created", args=(load2.pk,))),
    ("inventory-load-created-alias (ADMIN)", admin_client, reverse("inventory-load-created-alias", args=(load2.pk,))),
    ("stock-overview (WH)", client, reverse("stock-overview")),
    ("product-movements (WH)", client, reverse("product-movements", args=(prod2.pk,))),
    ("product-list (WH)", client, reverse("product-list")),
    ("product-expirations (WH)", client, reverse("product-expirations")),
]:
    r = c_obj.get(url)
    cc_results[label] = {
        "status": r.status_code,
        "cache_control": r.headers.get("Cache-Control", ""),
        "has_no_store": "no-store" in r.headers.get("Cache-Control", ""),
    }
findings["cache_control_stage05_routes"] = cc_results

# 7. RN-06 stock_overview (<) vs product_list (<=) when sellable_stock == minimum_stock == 10
plist_html = client.get(reverse("product-list")).content.decode("utf-8")
so_resp = client.get(reverse("stock-overview"))
so_html = so_resp.content.decode("utf-8")
findings["rn06_minimum_equal_10_discrepancy"] = {
    "product_list_shows_stock_bajo": "Stock bajo" in plist_html,
    "stock_overview_low_stock_ctx_count": len(so_resp.context["low_stock"]),
    "stock_overview_shows_stock_bajo": "Stock bajo" in so_html,
    "stock_overview_shows_OK": ">OK<" in so_html,
}

# 8. Explain ModelBackend.get_user on inactive_wh
backend = load_backend("django.contrib.auth.backends.ModelBackend")
backend_user = backend.get_user(inactive_wh.pk)
c_inact = Client()
c_inact.force_login(inactive_wh)
inact_dash = c_inact.get(reverse("dashboard"))
findings["inactive_session_probe"] = {
    "model_backend_get_user_returns": None if backend_user is None else f"{backend_user.email} (is_active={backend_user.is_active})",
    "dashboard_status": inact_dash.status_code,
    "dashboard_location": inact_dash.headers.get("Location"),
    "auth_user_id_still_in_session": "_auth_user_id" in c_inact.session,
}

# 9. Real PostgreSQL 18.4 NUL byte crash repro
pg_report = {}
cluster = (Path(tempfile.gettempdir()) / ("audit05-repro-pg-" + secrets.token_hex(8))).resolve()
cluster.mkdir(exist_ok=False)
dbdir = cluster / "data"
pw_pg = secrets.token_urlsafe(32)
pwfile = cluster / "pw"
pwfile.write_text(pw_pg, encoding="utf-8")
with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    pg_port = s.getsockname()[1]

pg_started = False
try:
    subprocess.run(
        [str(PG_BIN / "initdb.exe"), "-D", str(dbdir), "-U", "audit05r", "--pwfile", str(pwfile), "--auth-host=scram-sha-256", "--auth-local=scram-sha-256", "--encoding=UTF8", "--locale=C"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
    )
    pwfile.unlink()
    subprocess.run(
        [str(PG_BIN / "pg_ctl.exe"), "-D", str(dbdir), "-l", str(cluster / "pg.log"), "-o", f"-h 127.0.0.1 -p {pg_port} -c log_statement=none", "-w", "start"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
    )
    pg_started = True
    import psycopg
    from psycopg import sql
    from django.db import connections
    from django.conf import settings

    with psycopg.connect(host="127.0.0.1", port=pg_port, user="audit05r", password=pw_pg, dbname="postgres", autocommit=True) as pconn:
        pconn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier("audit05_repro")))

    connections.close_all()
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "audit05_repro",
        "USER": "audit05r",
        "PASSWORD": pw_pg,
        "HOST": "127.0.0.1",
        "PORT": pg_port,
        "CONN_MAX_AGE": 0,
        "CONN_HEALTH_CHECKS": False,
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "TIME_ZONE": "America/Lima",
        "OPTIONS": {"options": "-c statement_timeout=15000 -c lock_timeout=8000"},
    }
    del connections["default"]
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    r_wh = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    u_wh = Account.objects.create_user("pg.r5@test.invalid", pw, display_name="PG R5", role=r_wh)
    c_pg = Category.objects.create(name="PG Repro05")
    p_pg = Product.objects.create(category=c_pg, name="Prod PG Repro05", barcode="775099900001", sale_price=Decimal("4.00"))
    pg_client = Client(enforce_csrf_checks=True)
    pg_client.force_login(u_wh)
    pg_csrf = pg_client.get(reverse("inventory-load")).cookies["csrftoken"].value

    # NUL byte in lot number on PostgreSQL via HTTP POST
    try:
        r_nul = pg_client.post(
            reverse("inventory-load"),
            {
                "csrfmiddlewaretoken": pg_csrf,
                "product": str(p_pg.pk),
                "lots-TOTAL_FORMS": "1",
                "lots-INITIAL_FORMS": "0",
                "lots-MIN_NUM_FORMS": "1",
                "lots-MAX_NUM_FORMS": "1000",
                "lots-0-number": "LOT\x00PG",
                "lots-0-quantity": "2",
                "lots-0-unit_cost": "1.5000",
                "lots-0-expiration_date": tomorrow.isoformat(),
            },
        )
        pg_report["nul_lot_number_http"] = {"status": r_nul.status_code}
    except Exception as exc:
        pg_report["nul_lot_number_http"] = {"exception": f"{type(exc).__name__}: {exc}"}

    # NUL byte in product field on PG
    try:
        r_nul_p = pg_client.post(
            reverse("inventory-load"),
            {
                "csrfmiddlewaretoken": pg_csrf,
                "product": "bad\x00uuid",
                "lots-TOTAL_FORMS": "1",
                "lots-INITIAL_FORMS": "0",
                "lots-MIN_NUM_FORMS": "1",
                "lots-MAX_NUM_FORMS": "1000",
                "lots-0-number": "L-1",
                "lots-0-quantity": "2",
                "lots-0-unit_cost": "1.5000",
                "lots-0-expiration_date": tomorrow.isoformat(),
            },
        )
        pg_report["nul_product_http"] = {"status": r_nul_p.status_code}
    except Exception as exc:
        pg_report["nul_product_http"] = {"exception": f"{type(exc).__name__}: {exc}"}

    # Direct service NUL byte on PG
    try:
        confirm_initial_load(actor=u_wh, product=p_pg, lots=[LotInput("LOT\x00SVC", 1, Decimal("1.00"), tomorrow)])
        pg_report["nul_lot_number_service"] = "unexpected_success"
    except Exception as exc:
        pg_report["nul_lot_number_service"] = f"{type(exc).__name__}: {exc}"

    connections.close_all()
finally:
    if pg_started:
        subprocess.run(
            [str(PG_BIN / "pg_ctl.exe"), "-D", str(dbdir), "-m", "fast", "-w", "stop"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
        )
    with socket.socket() as s:
        pg_report["port_closed"] = s.connect_ex(("127.0.0.1", pg_port)) != 0

findings["postgresql_repro"] = pg_report

end_hashes = {str(p.relative_to(ROOT)): digest(p) == start_hashes[str(p.relative_to(ROOT))] for p in protected}
findings["protected_unchanged"] = all(end_hashes.values())

repro_file = OUT_DIR / "repro.json"
repro_file.write_text(json.dumps(findings, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print(json.dumps({"repro": str(repro_file.relative_to(ROOT)), "findings": findings}, ensure_ascii=False, indent=2, default=str))
