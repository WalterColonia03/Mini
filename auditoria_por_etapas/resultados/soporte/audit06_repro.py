"""Pre-fix Stage 06 reproduction probes (isolated SQLite + ephemeral PostgreSQL 18.4).
Never loads operator .env and never mutates existing SQLite DBs.
"""
from __future__ import annotations

import contextlib
import hashlib
import inspect
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
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
SUPPORT = Path(__file__).resolve().parent
PG_BIN = Path("C:/Program Files/PostgreSQL/18/bin")

STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
RUN_DIR = RESULTS / "datos" / f"etapa06-repro-{STAMP}"
OUT_DIR = RESULTS / "evidencias" / f"06-repro-{STAMP}"
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
    AUDIT06_RUN_DIR=str(RUN_DIR),
    AUDIT06_DEFAULT_COOKIES="1",
    DJANGO_SETTINGS_MODULE="audit06_settings",
)
sys.path.insert(0, str(APP))
sys.path.insert(0, str(SUPPORT))

import django

django.setup()

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import Client
from django.test.utils import setup_test_environment

setup_test_environment()
from django.urls import URLPattern, URLResolver, get_resolver, reverse
from django.utils import timezone as tz

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    call_command("migrate", interactive=False, verbosity=0)

from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.forms import LotInputForm, StockEntryProductForm
from inventory.models import InitialInventoryLoad, Lot, Supplier
from inventory.services import LotInput, confirm_initial_load, create_supplier, register_stock_entry


def collect_urls(patterns, prefix=""):
    routes = []
    for pat in patterns:
        if isinstance(pat, URLPattern):
            routes.append({"pattern": prefix + str(pat.pattern), "name": pat.name})
        elif isinstance(pat, URLResolver):
            routes.extend(collect_urls(pat.url_patterns, prefix + str(pat.pattern)))
    return routes


all_routes = collect_urls(get_resolver().url_patterns)
sol_routes = [
    r for r in all_routes
    if any(tok in (r["pattern"] + " " + (r["name"] or "")).lower() for tok in ("solicitud", "replenish", "reposicion", "sol-"))
]

admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

pw = secrets.token_urlsafe(16) + "A1!"
admin = Account.objects.create_user("admin.r6@test.invalid", pw, display_name="Admin R6", role=admin_role)
wh = Account.objects.create_user("wh.r6@test.invalid", pw, display_name="Wh R6", role=wh_role)
seller = Account.objects.create_user("seller.r6@test.invalid", pw, display_name="Seller R6", role=seller_role)

cat_on = Category.objects.create(name="Cat Activa R6", is_active=True)
cat_off = Category.objects.create(name="Cat Inactiva R6", is_active=False)

p_loaded = Product.objects.create(
    category=cat_on, name="Prod Loaded R6", barcode="775060600001", sale_price=Decimal("8.00"), minimum_stock=5
)
p_noload = Product.objects.create(
    category=cat_on, name="Prod NoLoad R6", barcode="775060600002", sale_price=Decimal("5.00"), minimum_stock=5
)
p_inact_loaded = Product.objects.create(
    category=cat_on, name="Prod InactiveLoaded R6", barcode="775060600003", sale_price=Decimal("5.00")
)
p_catoff_loaded = Product.objects.create(
    category=cat_on, name="Prod CatOffLoaded R6", barcode="775060600004", sale_price=Decimal("5.00")
)
p_exhausted = Product.objects.create(
    category=cat_on, name="Prod Exhausted R6", barcode="775060600005", sale_price=Decimal("5.00")
)
p_expired_only = Product.objects.create(
    category=cat_on, name="Prod ExpiredOnly R6", barcode="775060600006", sale_price=Decimal("5.00")
)

sup_on = create_supplier(actor=admin, name="Sup On R6", ruc="20606060001")
sup_off = create_supplier(actor=admin, name="Sup Off R6", ruc="20606060002")
sup_off.is_active = False
sup_off.save(update_fields=["is_active"])

today = tz.localdate()
tomorrow = today + timedelta(days=1)
future = today + timedelta(days=45)

load_main = confirm_initial_load(
    actor=wh,
    product=p_loaded,
    supplier=sup_on,
    lots=[LotInput("BASE-06", 10, Decimal("2.5000"), future)],
)
confirm_initial_load(actor=wh, product=p_inact_loaded, lots=[LotInput("INACT-01", 4, Decimal("2.00"), future)])
p_inact_loaded.is_active = False
p_inact_loaded.save(update_fields=["is_active"])

confirm_initial_load(actor=wh, product=p_catoff_loaded, lots=[LotInput("CATOFF-01", 4, Decimal("2.00"), future)])
p_catoff_loaded.category = cat_off
p_catoff_loaded.save(update_fields=["category"])

confirm_initial_load(actor=wh, product=p_exhausted, lots=[LotInput("EXH-01", 5, Decimal("2.0000"), future)])
Lot.objects.filter(product=p_exhausted).update(available_quantity=0)

confirm_initial_load(actor=wh, product=p_expired_only, lots=[LotInput("EXP-01", 5, Decimal("4.0000"), tomorrow)])
Lot.objects.filter(product=p_expired_only).update(expiration_date=today)

entry_url = reverse("stock-entry")
client = Client(enforce_csrf_checks=True)
client.force_login(wh)
get_form = client.get(entry_url)
csrf = get_form.cookies["csrftoken"].value

findings: dict[str, object] = {
    "stamp_utc": STAMP,
    "protected_absent_at_start": [k for k, v in start_hashes.items() if v is None],
    "route_count_total": len(all_routes),
    "hu_sol_routes_found": sol_routes,
    "stock_entry_create_source": inspect.getsource(sys.modules["inventory.views"].stock_entry_create),
    "register_stock_entry_source": inspect.getsource(register_stock_entry),
}

# 1. Empty POST with header X-CSRFToken vs with csrfmiddlewaretoken
empty_header_resp = client.post(entry_url, {}, HTTP_X_CSRFTOKEN=csrf)
empty_header_html = empty_header_resp.content.decode("utf-8", errors="replace")
empty_csrf_resp = client.post(entry_url, {"csrfmiddlewaretoken": csrf})
empty_csrf_html = empty_csrf_resp.content.decode("utf-8", errors="replace")

findings["empty_post"] = {
    "header_csrf_empty_body": {
        "status": empty_header_resp.status_code,
        "has_alert": 'role="alert"' in empty_header_html or "errorlist" in empty_header_html,
        "is_bound_bug_reproduced": ('role="alert"' not in empty_header_html and "errorlist" not in empty_header_html),
    },
    "body_csrf_only": {
        "status": empty_csrf_resp.status_code,
        "has_alert": 'role="alert"' in empty_csrf_html or "errorlist" in empty_csrf_html,
    },
}

# 2. Tampered management_form cases on /inventario/entrada/
mgmt_cases = {}
for label, overrides in [
    ("missing_management_form", {"product": str(p_loaded.pk), "lots-0-number": "L1", "lots-0-quantity": "2", "lots-0-unit_cost": "1.00", "lots-0-expiration_date": tomorrow.isoformat()}),
    ("negative_total_forms", {"product": str(p_loaded.pk), "lots-TOTAL_FORMS": "-1", "lots-INITIAL_FORMS": "0", "lots-MIN_NUM_FORMS": "1", "lots-MAX_NUM_FORMS": "1000"}),
    ("alpha_total_forms", {"product": str(p_loaded.pk), "lots-TOTAL_FORMS": "abc", "lots-INITIAL_FORMS": "0", "lots-MIN_NUM_FORMS": "1", "lots-MAX_NUM_FORMS": "1000"}),
    ("huge_total_forms_5000", {"product": str(p_loaded.pk), "lots-TOTAL_FORMS": "5000", "lots-INITIAL_FORMS": "0", "lots-MIN_NUM_FORMS": "1", "lots-MAX_NUM_FORMS": "1000"}),
]:
    c_no_raise = Client(enforce_csrf_checks=True, raise_request_exception=False)
    c_no_raise.force_login(wh)
    c_no_raise.get(entry_url)
    tok = c_no_raise.cookies["csrftoken"].value
    try:
        r = client.post(entry_url, {**overrides, "csrfmiddlewaretoken": csrf})
        mgmt_cases[label] = {"status": r.status_code, "raised": None, "has_alert": 'role="alert"' in r.content.decode("utf-8", errors="replace")}
    except Exception as exc:
        r_http = c_no_raise.post(entry_url, {**overrides, "csrfmiddlewaretoken": tok})
        mgmt_cases[label] = {
            "status_with_exception_handler": r_http.status_code,
            "raised": f"{type(exc).__name__}: {exc}",
        }
findings["management_form_tamper"] = mgmt_cases

# 3. StockEntryProductForm queryset & sentinel handling
form_obj = StockEntryProductForm()
prod_ids = set(form_obj.fields["product"].queryset.values_list("pk", flat=True))
sup_ids = set(form_obj.fields["supplier"].queryset.values_list("pk", flat=True))
findings["form_eligibility"] = {
    "includes_loaded": p_loaded.pk in prod_ids,
    "includes_exhausted": p_exhausted.pk in prod_ids,
    "includes_expired_only": p_expired_only.pk in prod_ids,
    "excludes_no_load": p_noload.pk not in prod_ids,
    "excludes_inactive_product": p_inact_loaded.pk not in prod_ids,
    "excludes_inactive_category": p_catoff_loaded.pk not in prod_ids,
    "includes_active_supplier": sup_on.pk in sup_ids,
    "excludes_inactive_supplier": sup_off.pk not in sup_ids,
}

# Sentinel rendering on StockEntryProductForm with inactive supplier
rejected_sup_resp = client.post(
    entry_url,
    {
        "csrfmiddlewaretoken": csrf,
        "product": str(p_loaded.pk),
        "supplier": str(sup_off.pk),
        "lots-TOTAL_FORMS": "1",
        "lots-INITIAL_FORMS": "0",
        "lots-MIN_NUM_FORMS": "1",
        "lots-MAX_NUM_FORMS": "1000",
        "lots-0-number": "L-SENTINEL",
        "lots-0-quantity": "2",
        "lots-0-unit_cost": "1.5000",
        "lots-0-expiration_date": tomorrow.isoformat(),
    },
)
rejected_sup_html = rejected_sup_resp.content.decode("utf-8", errors="replace")
findings["inactive_supplier_sentinel"] = {
    "status": rejected_sup_resp.status_code,
    "has_inactive_sentinel_value": f"__inactive__:{sup_off.pk}" in rejected_sup_html,
    "has_inactivo_label": "Inactivo (cambie la selección)" in rejected_sup_html,
}

# 4. LotInputForm checks + HTTP scientific notation + unmasked combo error
sci_resp = client.post(
    entry_url,
    {
        "csrfmiddlewaretoken": csrf,
        "product": str(p_loaded.pk),
        "lots-TOTAL_FORMS": "2",
        "lots-INITIAL_FORMS": "0",
        "lots-MIN_NUM_FORMS": "1",
        "lots-MAX_NUM_FORMS": "1000",
        "lots-0-number": "L-1",
        "lots-0-quantity": "0",
        "lots-0-unit_cost": "1e2",
        "lots-0-expiration_date": tomorrow.isoformat(),
        "lots-1-number": "L-2",
        "lots-1-quantity": "2",
        "lots-1-unit_cost": "1.50",
        "lots-1-expiration_date": today.isoformat(),
    },
)
sci_html = sci_resp.content.decode("utf-8", errors="replace")
findings["http_combo_validation"] = {
    "status": sci_resp.status_code,
    "rejects_sci_notation": "notación científica" in sci_html,
    "rejects_lot0_qty0": "mayor o igual a 1" in sci_html,
    "unmasks_lot1_today_lima": "posterior a hoy en Lima" in sci_html,
}

# 5. Direct service defects & edge cases BEFORE fixes
# 5a. IntegrityError inside outer transaction.atomic() when bulk_create fails with IntegrityError
orig_bulk = Lot.objects.bulk_create
def boom_integrity(*args, **kwargs):
    raise IntegrityError("Simulated DB unique violation inside bulk_create")

ie_behavior = {}
Lot.objects.bulk_create = boom_integrity
try:
    with transaction.atomic():
        register_stock_entry(
            actor=wh, product=p_loaded, lots=[LotInput("L-IE-TEST", 2, Decimal("3.00"), future)]
        )
    ie_behavior = {"result": "unexpected_commit"}
except ValidationError as exc:
    ie_behavior = {"result": "ValidationError", "messages": exc.messages}
except IntegrityError as exc:
    ie_behavior = {"result": "raw_IntegrityError_leaked", "message": str(exc)}
finally:
    Lot.objects.bulk_create = orig_bulk
findings["bulk_create_integrity_error_parity"] = ie_behavior

# 5b. Nonexistent/unsaved Product & No Initial Load
for label, fn in [
    ("unsaved_product", lambda: register_stock_entry(actor=wh, product=Product(category=cat_on, name="X", barcode="X", sale_price=Decimal("1.00")), lots=[LotInput("L-U", 1, Decimal("1.00"), tomorrow)])),
    ("deleted_product_pk", lambda: register_stock_entry(actor=wh, product=Product(pk=secrets.token_bytes(16).hex(), category=cat_on, name="Y", barcode="Y", sale_price=Decimal("1.00")), lots=[LotInput("L-D", 1, Decimal("1.00"), tomorrow)])),
    ("no_initial_load", lambda: register_stock_entry(actor=wh, product=p_noload, lots=[LotInput("L-NL", 1, Decimal("1.00"), tomorrow)])),
]:
    try:
        fn()
        findings[f"service_{label}"] = "unexpected_commit"
    except Exception as exc:
        findings[f"service_{label}"] = f"{type(exc).__name__}: {exc}"

# 5c. Previous quantity == 0 cases (exhausted vs expired-only)
register_stock_entry(actor=wh, product=p_exhausted, lots=[LotInput("EXH-NEW", 4, Decimal("6.2500"), future)])
p_exhausted.refresh_from_db()
register_stock_entry(actor=wh, product=p_expired_only, lots=[LotInput("EXP-NEW", 4, Decimal("1.5000"), future)])
p_expired_only.refresh_from_db()
findings["previous_qty_zero_cases"] = {
    "exhausted_average_cost": str(p_exhausted.average_cost),
    "expired_only_ignores_expired_cost_4_sets_1_5": str(p_expired_only.average_cost),
}

# 6. Cache-Control & Role boundaries on Stage 06 routes
c_anon = Client()
c_seller = Client(enforce_csrf_checks=True)
c_seller.force_login(seller)
c_admin = Client(enforce_csrf_checks=True)
c_admin.force_login(admin)

r_anon_get = c_anon.get(entry_url)
r_seller_get = c_seller.get(entry_url)
r_admin_get = c_admin.get(entry_url)
r_wh_get = client.get(entry_url)
findings["roles_and_cache_control"] = {
    "anon_get_status": r_anon_get.status_code,
    "anon_get_location": r_anon_get.headers.get("Location"),
    "seller_get_status": r_seller_get.status_code,
    "admin_get_status": r_admin_get.status_code,
    "wh_get_status": r_wh_get.status_code,
    "wh_get_cache_control": r_wh_get.headers.get("Cache-Control", ""),
    "wh_has_no_store": "no-store" in r_wh_get.headers.get("Cache-Control", ""),
}

# 7. Real PostgreSQL 18.4 NUL-byte + empty POST repro
pg_report = {}
cluster = (Path(tempfile.gettempdir()) / ("audit06-repro-pg-" + secrets.token_hex(8))).resolve()
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
        [str(PG_BIN / "initdb.exe"), "-D", str(dbdir), "-U", "audit06r", "--pwfile", str(pwfile), "--auth-host=scram-sha-256", "--auth-local=scram-sha-256", "--encoding=UTF8", "--locale=C"],
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

    with psycopg.connect(host="127.0.0.1", port=pg_port, user="audit06r", password=pw_pg, dbname="postgres", autocommit=True) as pconn:
        pconn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier("audit06_repro")))

    connections.close_all()
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "audit06_repro",
        "USER": "audit06r",
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
    u_wh = Account.objects.create_user("pg.r6@test.invalid", pw, display_name="PG R6", role=r_wh)
    c_pg = Category.objects.create(name="PG Repro06")
    p_pg = Product.objects.create(category=c_pg, name="Prod PG Repro06", barcode="775099900006", sale_price=Decimal("4.00"))
    confirm_initial_load(actor=u_wh, product=p_pg, lots=[LotInput("PG-INIT-06", 5, Decimal("2.0000"), future)])

    pg_client = Client(enforce_csrf_checks=True)
    pg_client.force_login(u_wh)
    pg_csrf = pg_client.get(entry_url).cookies["csrftoken"].value

    # Empty POST on PG with X-CSRFToken header
    r_empty_pg = pg_client.post(entry_url, {}, HTTP_X_CSRFTOKEN=pg_csrf)
    pg_report["empty_post_header_csrf_pg"] = {
        "status": r_empty_pg.status_code,
        "has_alert": 'role="alert"' in r_empty_pg.content.decode("utf-8", errors="replace"),
    }

    # NUL byte in lot number via HTTP POST on PG
    r_nul = pg_client.post(
        entry_url,
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
    pg_report["nul_lot_number_http"] = {
        "status": r_nul.status_code,
        "has_alert": 'role="alert"' in r_nul.content.decode("utf-8", errors="replace"),
    }

    # NUL byte in product field via HTTP POST on PG
    r_nul_p = pg_client.post(
        entry_url,
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
    pg_report["nul_product_http"] = {
        "status": r_nul_p.status_code,
        "has_alert": 'role="alert"' in r_nul_p.content.decode("utf-8", errors="replace"),
    }

    # Direct service NUL byte on PG
    try:
        register_stock_entry(actor=u_wh, product=p_pg, lots=[LotInput("LOT\x00SVC", 1, Decimal("1.00"), tomorrow)])
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

