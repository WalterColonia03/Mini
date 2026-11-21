"""Stage 15 (15-A) Server Security, Permissions, CSRF, Sessions, Passwords, /admin/, Logging & Deployment Runner.

Runs against the intact r1-pmv build without modifying product files or touching operational databases.
"""
from __future__ import annotations

import contextlib
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from html.parser import HTMLParser
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time
import traceback
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "r1-pmv/manage.py").exists())
HERE.mkdir(parents=True, exist_ok=True)
STAMP = datetime.now(dt_timezone.utc).isoformat()
PYTHON = ROOT / "r1-pmv/.venv/Scripts/python.exe"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_build() -> dict:
    names = (
        subprocess.check_output(
            ["git", "-C", str(ROOT / "r1-pmv"), "ls-files", "-co", "--exclude-standard", "-z"]
        )
        .decode()
        .split("\0")
    )
    files = {
        n: digest((ROOT / "r1-pmv" / n).read_bytes())
        for n in sorted(set(names))
        if n
        and not n.startswith("evidencias/")
        and Path(n).suffix in {".py", ".html", ".css", ".js", ".svg", ".ps1", ".sh"}
    }
    return {
        "count": len(files),
        "sha256": digest(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()),
        "files": files,
    }


class _LinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict[str, str]] = []
        self._current_href: str | None = None
        self._text_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_dict = dict(attrs)
        if tag == "a" and attr_dict.get("href"):
            self._current_href = attr_dict["href"]
            self._text_parts = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_href is not None:
            self.links.append(
                {"href": self._current_href, "text": " ".join("".join(self._text_parts).split())}
            )
            self._current_href = None
            self._text_parts = []


report: dict = {
    "started_utc": STAMP,
    "etapa": "ETAPA-15",
    "sublote": "15-A",
    "pasada": 1,
    "cursor_entrada": "15-SEGURIDAD-BASELINE-01",
    "plan08_sha256": digest((ROOT / "08_Historias_de_Usuario.md").read_bytes()),
    "head": subprocess.check_output(["git", "-C", str(ROOT / "r1-pmv"), "rev-parse", "HEAD"], text=True).strip(),
    "before_build": {k: v for k, v in compute_build().items() if k != "files"},
    "cases": [],
}


def run_case(case_id: str, fn) -> None:
    t0 = time.monotonic()
    try:
        details = fn() or {}
        report["cases"].append(
            {"id": case_id, "ok": True, "seconds": round(time.monotonic() - t0, 3), **details}
        )
    except Exception as exc:
        report["cases"].append(
            {
                "id": case_id,
                "ok": False,
                "seconds": round(time.monotonic() - t0, 3),
                "error": type(exc).__name__,
                "detail": str(exc),
                "traceback": traceback.format_exc(),
            }
        )
    print(f"[{case_id}] ok={report['cases'][-1]['ok']}", flush=True)


# 1. Execute full existing unit test suite in subprocess on disposable SQLite DB
def case_existing_suite() -> dict:
    env = os.environ.copy()
    env.update(
        {
            "APP_ENV": "test",
            "DJANGO_DEBUG": "false",
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
            "DJANGO_ALLOWED_HOSTS": "testserver,127.0.0.1,localhost",
        }
    )
    proc = subprocess.run(
        [str(PYTHON), "-B", "manage.py", "test", "--verbosity=1"],
        cwd=str(ROOT / "r1-pmv"),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    combined = (proc.stdout or "") + "\n" + (proc.stderr or "")
    (HERE / "regresion-suite.txt").write_text(combined, encoding="utf-8")
    assert proc.returncode == 0, f"Suite failed with returncode={proc.returncode}"
    m = re.search(r"Ran (\d+) tests", combined)
    assert m and "OK" in combined, "Test suite output missing Ran N tests / OK"
    tests_ran = int(m.group(1))
    assert tests_ran >= 640, f"Expected >=640 tests, got {tests_ran}"
    return {"returncode": proc.returncode, "tests_ran": tests_ran, "log_file": "regresion-suite.txt"}

# Configure in-process isolated Django with DisposableSqliteTestRunner
sys.path.insert(0, str(ROOT / "r1-pmv"))
os.environ.update(
    {
        "APP_ENV": "test",
        "DJANGO_DEBUG": "false",
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
        "DJANGO_SETTINGS_MODULE": "config.settings",
        "DJANGO_ALLOWED_HOSTS": "testserver,127.0.0.1,localhost",
    }
)
from config import env as config_env

config_env.load_dotenv = lambda path=None: None

import django

django.setup()

from django.conf import settings
from django.contrib import admin as django_admin
from django.contrib.auth.hashers import identify_hasher, make_password
from django.contrib.sessions.models import Session
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, transaction
from django.db.models.deletion import ProtectedError
from django.test import Client
from django.test.utils import setup_test_environment
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import salted_hmac

from app_platform.logging import RedactSensitiveDataFilter
from cash.models import CashRegister, CashShift, CashShiftClose
from cash.services import close_cash_shift, open_cash_shift
from catalog.models import Category, Product
from catalog.services import create_category, register_canned_product
from identity.forms import EmployeeCreationForm, EmployeeEditForm, LoginForm
from identity.models import Account, LoginAttempt, Role
from identity.services import (
    INVALID_CREDENTIALS_MESSAGE,
    authenticate_active_account,
    create_employee,
    deactivate_employee,
    reactivate_employee,
    update_employee,
)
from inventory.models import (
    InitialInventoryLoad,
    InitialLoadLine,
    Lot,
    PhysicalAdjustment,
    StockReceipt,
    StockWriteOff,
    Supplier,
)
from inventory.services import (
    LotInput,
    confirm_initial_load,
    create_supplier,
    register_physical_adjustment,
    register_stock_entry,
    write_off_stock,
)
from sales.models import Sale, SaleDraft, SaleDraftLine
from sales.services import add_product_to_draft, checkout_sale

# Create isolated disposable SQLite DB for in-process Stage 15 checks
import tempfile

TEMP_DB_DIR = Path(tempfile.mkdtemp(prefix="audit15-srv-sqlite-"))
TEMP_DB_PATH = TEMP_DB_DIR / "audit15_srv.sqlite3"
settings.DATABASES["default"]["NAME"] = str(TEMP_DB_PATH)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    call_command("migrate", interactive=False, verbosity=0)
setup_test_environment()

PW_ALL = "Audit15!Valid9"
roles = {
    code: Role.objects.update_or_create(code=code, defaults={"name": label})[0]
    for code, label in Role.Code.choices
}
admin_user = Account.objects.create_user(
    "admin@audit15.invalid", PW_ALL, display_name="Ana Admin", role=roles[Role.Code.ADMIN]
)
admin2_user = Account.objects.create_user(
    "admin2@audit15.invalid", PW_ALL, display_name="Beto Admin", role=roles[Role.Code.ADMIN]
)
warehouse_user = Account.objects.create_user(
    "almacen@audit15.invalid", PW_ALL, display_name="Bruno Almacen", role=roles[Role.Code.WAREHOUSE]
)
seller_user = Account.objects.create_user(
    "vendedor@audit15.invalid", PW_ALL, display_name="Carla Ventas", role=roles[Role.Code.SELLER]
)
seller2_user = Account.objects.create_user(
    "vendedor2@audit15.invalid", PW_ALL, display_name="Diego Ventas", role=roles[Role.Code.SELLER]
)
inactive_user = Account.objects.create_user(
    "inactivo@audit15.invalid",
    PW_ALL,
    display_name="Elena Inactiva",
    role=roles[Role.Code.SELLER],
    is_active=False,
)
staff_user = Account.objects.create_user(
    "staff@audit15.invalid",
    PW_ALL,
    display_name="Soporte Staff",
    role=roles[Role.Code.ADMIN],
    is_staff=True,
    is_superuser=True,
)

register = CashRegister.objects.get_or_create(code="CAJA-01")[0]
cat = create_category(actor=admin_user, name="Lácteos Audit15")
prod = register_canned_product(
    actor=admin_user,
    name="Leche Audit15",
    barcode="775150000001",
    category=cat,
    unit=Product.Unit.UNIT,
    sale_price=Decimal("6.50"),
    minimum_stock=3,
    barcode_type=Product.BarcodeType.INTERNAL,
)
sup = create_supplier(actor=admin_user, name="Proveedor Audit15", ruc="20123456789", phone="014445566")
future_date = timezone.localdate() + timedelta(days=60)
init_load = confirm_initial_load(
    actor=warehouse_user,
    product=prod,
    supplier=sup,
    lots=[LotInput("L-INIT-01", 20, Decimal("3.5000"), future_date)],
)
lot_main = init_load.lots.get()
receipt_doc = register_stock_entry(
    actor=warehouse_user,
    product=prod,
    supplier=sup,
    lots=[LotInput("L-REC-01", 10, Decimal("4.1000"), future_date + timedelta(days=30))],
)
writeoff_doc = write_off_stock(
    actor=warehouse_user,
    lot=lot_main,
    quantity=1,
    reason=StockWriteOff.Reason.DAMAGE,
    notes="Envase abollado en prueba",
)
adj_doc = register_physical_adjustment(
    actor=admin_user,
    lot=lot_main,
    delta=-1,
    reason="Diferencia de conteo en auditoría 15",
)

# Seller 1 opens shift, makes 1 sale, closes shift, then opens a second shift with an active draft
shift_closed = open_cash_shift(actor=seller_user, opening_amount=Decimal("50.00"))
draft_for_sale = add_product_to_draft(actor=seller_user, product_id=prod.pk, quantity=2)
sale_doc = checkout_sale(
    actor=seller_user,
    draft_id=draft_for_sale.pk,
    cash_received=Decimal("20.00"),
    idempotency_key=secrets. token_hex(16)[:8] + "-0000-4000-8000-000000000001",
)
close_cash_shift(actor=seller_user, counted_amount=Decimal("63.00"))

shift_open = open_cash_shift(actor=seller_user, opening_amount=Decimal("40.00"))
draft_active = add_product_to_draft(actor=seller_user, product_id=prod.pk, quantity=1)
draft_line_active = draft_active.lines.get()


def db_digest() -> dict[str, str]:
    with connection.cursor() as cur:
        tables = sorted(
            t
            for t in connection.introspection.table_names()
            if t.startswith(("identity_", "catalog_", "inventory_", "cash_", "sales_"))
            and t != "identity_loginattempt"
        )
        out = {}
        for t in tables:
            cur.execute(f'SELECT * FROM "{t}" ORDER BY 1')
            out[t] = digest(json.dumps(cur.fetchall(), default=str, sort_keys=True).encode())
        return out


# 2. SRV15-01: Exhaustive Route x Role x Method Permission Matrix
def case_permission_matrix() -> dict:
    routes = [
        # (name, path, method, allowed_roles, expected_ok_status)
        ("dashboard", reverse("dashboard"), "GET", {"ADMIN", "ALMACENERO", "VENDEDOR"}, {200}),
        ("logout-get", reverse("logout"), "GET", {"ADMIN", "ALMACENERO", "VENDEDOR"}, {200}),
        ("employee-list", reverse("employee-list"), "GET", {"ADMIN"}, {200}),
        ("employee-create-get", reverse("employee-create"), "GET", {"ADMIN"}, {200}),
        ("employee-create-post", reverse("employee-create"), "POST", {"ADMIN"}, {200}),
        ("employee-edit-get", reverse("employee-edit", args=[seller2_user.pk]), "GET", {"ADMIN"}, {200}),
        ("employee-edit-post", reverse("employee-edit", args=[seller2_user.pk]), "POST", {"ADMIN"}, {200}),
        ("employee-state-confirm", reverse("employee-state-confirm", args=[seller2_user.pk]), "GET", {"ADMIN"}, {200}),
        ("employee-deactivate-post", reverse("employee-deactivate", args=[seller2_user.pk]), "POST", {"ADMIN"}, {400}),
        ("category-list", reverse("category-list"), "GET", {"ADMIN"}, {200}),
        ("category-create-get", reverse("category-create"), "GET", {"ADMIN"}, {200}),
        ("category-create-post", reverse("category-create"), "POST", {"ADMIN"}, {200}),
        ("category-state-confirm", reverse("category-state-confirm", args=[cat.pk]), "GET", {"ADMIN"}, {200}),
        ("category-toggle-post", reverse("category-toggle", args=[cat.pk]), "POST", {"ADMIN"}, {400, 302}),
        ("product-expirations", reverse("product-expirations"), "GET", {"ADMIN", "ALMACENERO"}, {200}),
        ("product-list", reverse("product-list"), "GET", {"ADMIN", "ALMACENERO"}, {200}),
        ("product-entry-get", reverse("product-entry"), "GET", {"ADMIN"}, {200}),
        ("product-entry-post", reverse("product-entry"), "POST", {"ADMIN"}, {200}),
        ("product-barcode-check", reverse("product-barcode-check") + "?barcode=775150000001", "GET", {"ADMIN"}, {200}),
        ("product-created", reverse("product-created", args=[prod.pk]), "GET", {"ADMIN"}, {200}),
        ("product-created-alias", reverse("product-created-alias", args=[prod.pk]), "GET", {"ADMIN"}, {200}),
        ("product-edit-get", reverse("product-edit", args=[prod.pk]), "GET", {"ADMIN"}, {200}),
        ("product-edit-post", reverse("product-edit", args=[prod.pk]), "POST", {"ADMIN"}, {200}),
        ("product-toggle-post", reverse("product-toggle", args=[prod.pk]), "POST", {"ADMIN"}, {400, 302}),
        ("inventory-load-get", reverse("inventory-load"), "GET", {"ALMACENERO"}, {200}),
        ("inventory-load-post", reverse("inventory-load"), "POST", {"ALMACENERO"}, {200}),
        ("inventory-load-created-alias", reverse("inventory-load-created-alias", args=[init_load.pk]), "GET", {"ADMIN", "ALMACENERO"}, {200}),
        ("inventory-load-created", reverse("inventory-load-created", args=[init_load.pk]), "GET", {"ADMIN", "ALMACENERO"}, {200}),
        ("stock-entry-get", reverse("stock-entry"), "GET", {"ALMACENERO"}, {200}),
        ("stock-entry-post", reverse("stock-entry"), "POST", {"ALMACENERO"}, {200}),
        ("stock-receipt", reverse("stock-receipt", args=[receipt_doc.pk]), "GET", {"ADMIN", "ALMACENERO"}, {200}),
        ("supplier-list", reverse("supplier-list"), "GET", {"ADMIN", "ALMACENERO"}, {200}),
        ("supplier-create-get", reverse("supplier-create"), "GET", {"ADMIN"}, {200}),
        ("supplier-create-post", reverse("supplier-create"), "POST", {"ADMIN"}, {200}),
        ("supplier-toggle-post", reverse("supplier-toggle", args=[sup.pk]), "POST", {"ADMIN"}, {400, 302}),
        ("stock-writeoff-get", reverse("stock-writeoff"), "GET", {"ADMIN", "ALMACENERO"}, {200}),
        ("stock-writeoff-post", reverse("stock-writeoff"), "POST", {"ADMIN", "ALMACENERO"}, {200}),
        ("stock-writeoff-receipt", reverse("stock-writeoff-receipt", args=[writeoff_doc.pk]), "GET", {"ADMIN", "ALMACENERO"}, {200}),
        ("physical-adjustment-get", reverse("physical-adjustment"), "GET", {"ADMIN"}, {200}),
        ("physical-adjustment-post", reverse("physical-adjustment"), "POST", {"ADMIN"}, {200}),
        ("physical-adjustment-detail", reverse("physical-adjustment-detail", args=[adj_doc.pk]), "GET", {"ADMIN", "ALMACENERO"}, {200}),
        ("stock-overview", reverse("stock-overview"), "GET", {"ADMIN", "ALMACENERO"}, {200}),
        ("product-movements", reverse("product-movements", args=[prod.pk]), "GET", {"ADMIN", "ALMACENERO"}, {200}),
        ("cash-open-get", reverse("cash-open"), "GET", {"VENDEDOR"}, {200}),
        ("cash-open-post", reverse("cash-open"), "POST", {"VENDEDOR"}, {200}),
        ("cash-close-get", reverse("cash-close"), "GET", {"VENDEDOR"}, {200}),
        ("cash-close-post", reverse("cash-close"), "POST", {"VENDEDOR"}, {200}),
        ("cash-shift-opened", reverse("cash-shift-opened", args=[shift_open.pk]), "GET", {"VENDEDOR"}, {200}),
        ("cash-shift-closed", reverse("cash-shift-closed", args=[shift_closed.pk]), "GET", {"ADMIN", "VENDEDOR"}, {200}),
        ("cash-shift-history", reverse("cash-shift-history"), "GET", {"ADMIN", "VENDEDOR"}, {200}),
        ("sales-draft-get", reverse("sales-draft"), "GET", {"VENDEDOR"}, {200}),
        ("sales-draft-post", reverse("sales-draft"), "POST", {"VENDEDOR"}, {200}),
        ("sales-checkout-get", reverse("sales-checkout"), "GET", {"VENDEDOR"}, {200}),
        ("sales-checkout-post", reverse("sales-checkout"), "POST", {"VENDEDOR"}, {200, 302}),
        ("sales-receipt", reverse("sales-receipt", args=[sale_doc.pk]), "GET", {"ADMIN", "VENDEDOR"}, {200}),
        ("sales-line-update-post", reverse("sales-line-update", args=[draft_line_active.pk]), "POST", {"VENDEDOR"}, {200, 302}),
        ("sales-shift-history", reverse("sales-shift-history"), "GET", {"VENDEDOR"}, {200}),
        ("sales-history", reverse("sales-history"), "GET", {"ADMIN", "VENDEDOR"}, {200}),
    ]
    actors = {
        "ANON": None,
        "ADMIN": admin_user,
        "ALMACENERO": warehouse_user,
        "VENDEDOR": seller_user,
    }
    checked = 0
    denied_403 = 0
    anon_302 = 0
    # Known catalog views missing @never_cache in current build
    known_missing_no_store = {
        "category-create-get",
        "category-create-post",
        "product-entry-get",
        "product-entry-post",
        "product-created",
        "product-created-alias",
        "product-edit-get",
        "product-edit-post",
        "product-toggle-post",
    }
    observed_missing_no_store: set[str] = set()
    for r_name, path, method, allowed_roles, ok_statuses in routes:
        for actor_label, user_obj in actors.items():
            client = Client()
            if user_obj is not None:
                client.force_login(user_obj)
            # Send empty payload on POST so valid actors hit form validation (200/400) without mutating DB
            if r_name in ("category-toggle-post", "product-toggle-post", "supplier-toggle-post"):
                payload = {"is_active": "invalid_bool"}
            else:
                payload = {}
            before = db_digest() if actor_label != "ADMIN" or method == "GET" else None
            resp = client.get(path) if method == "GET" else client.post(path, payload)
            checked += 1
            if actor_label == "ANON":
                assert resp.status_code == 302, f"Anon {method} {path} returned {resp.status_code}"
                assert resp.headers["Location"].startswith(reverse("login")), f"Anon redirect {resp.headers['Location']}"
                anon_302 += 1
            elif actor_label in allowed_roles:
                assert resp.status_code in ok_statuses, f"{actor_label} {method} {path} ({r_name}) returned {resp.status_code}, expected {ok_statuses}"
                if "no-store" not in resp.headers.get("Cache-Control", ""):
                    assert r_name in known_missing_no_store, f"Unexpected missing Cache-Control no-store on {r_name}"
                    observed_missing_no_store.add(r_name)
            else:
                assert resp.status_code == 403, f"Unauthorized {actor_label} {method} {path} ({r_name}) returned {resp.status_code}"
                body = resp.content.decode("utf-8")
                if r_name == "product-barcode-check":
                    assert resp.headers.get("Content-Type", "").startswith("application/json")
                    assert json.loads(body).get("error") == "No tiene permiso para esta operación."
                    assert "no-store" in resp.headers.get("Cache-Control", "")
                else:
                    assert 'data-testid="permission-denied"' in body
                    assert "No tienes permiso para esta operación" in body
                denied_403 += 1
            if before is not None and actor_label not in allowed_roles:
                assert db_digest() == before, f"DB mutated on unauthorized request {actor_label} {method} {path}"

    # Verify VENDEDOR ownership isolation (seller2 cannot view seller1's shift, sale receipt, or filtered histories)
    c_seller2 = Client()
    c_seller2.force_login(seller2_user)
    for own_path in (
        reverse("cash-shift-opened", args=[shift_open.pk]),
        reverse("cash-shift-closed", args=[shift_closed.pk]),
        reverse("sales-receipt", args=[sale_doc.pk]),
    ):
        r_own = c_seller2.get(own_path)
        assert r_own.status_code == 404, f"Seller2 accessed Seller1 resource {own_path}: {r_own.status_code}"

    # Seller2 querying /caja/turnos/ or /ventas/historial/ with seller1's filters cannot see seller1's data
    r_sh_s2 = c_seller2.get(reverse("cash-shift-history") + f"?vendedor={seller_user.pk}")
    assert r_sh_s2.status_code == 200 and seller_user.display_name not in r_sh_s2.content.decode("utf-8")
    r_vh_s2 = c_seller2.get(reverse("sales-history") + f"?vendedor={seller_user.pk}&turno={shift_closed.pk}")
    vh_s2_html = r_vh_s2.content.decode("utf-8")
    assert r_vh_s2.status_code == 200
    assert r_vh_s2.context["total_sales_count"] == 0
    assert seller_user.display_name not in vh_s2_html
    assert reverse("sales-receipt", args=[sale_doc.pk]) not in vh_s2_html
    assert "No se encontraron ventas con los filtros aplicados." in vh_s2_html

    # Verify HTTP 405 Method Not Allowed on GET-only / POST-only endpoints
    c_admin = Client()
    c_admin.force_login(admin_user)
    # Sales receipt must never expose unit cost or margin even to ADMIN
    r_adm_rec = c_admin.get(reverse("sales-receipt", args=[sale_doc.pk]))
    assert r_adm_rec.status_code == 200
    adm_rec_html = r_adm_rec.content.decode("utf-8")
    for forbidden_term in ("Costo", "Margen", "Ganancia", "average_cost"):
        assert forbidden_term not in adm_rec_html, f"Sales receipt exposed {forbidden_term}"

    # Warehouse views on product-list and supplier-list must be strictly read-only (no mutation links/forms)
    c_wh = Client()
    c_wh.force_login(warehouse_user)
    r_wh_prod = c_wh.get(reverse("product-list")).content.decode("utf-8")
    r_wh_sup = c_wh.get(reverse("supplier-list")).content.decode("utf-8")
    assert "/productos/nuevo/" not in r_wh_prod and "/editar/" not in r_wh_prod and "/disponibilidad/" not in r_wh_prod
    assert "/inventario/proveedores/nuevo/" not in r_wh_sup and "/estado/" not in r_wh_sup

    c_seller = Client()
    c_seller.force_login(seller_user)
    method_405_targets = [
        (c_admin, "POST", reverse("dashboard")),
        (c_admin, "POST", reverse("employee-list")),
        (c_admin, "GET", reverse("employee-deactivate", args=[seller2_user.pk])),
        (c_admin, "GET", reverse("category-toggle", args=[cat.pk])),
        (c_admin, "GET", reverse("product-toggle", args=[prod.pk])),
        (c_admin, "GET", reverse("supplier-toggle", args=[sup.pk])),
        (c_admin, "POST", reverse("stock-overview")),
        (c_admin, "POST", reverse("product-movements", args=[prod.pk])),
        (c_admin, "POST", reverse("cash-shift-history")),
        (c_admin, "POST", reverse("sales-history")),
        (c_seller, "GET", reverse("sales-line-update", args=[draft_line_active.pk])),
        (c_seller, "GET", reverse("sales-line-remove", args=[draft_line_active.pk])),
        (c_seller, "GET", reverse("sales-draft-discard")),
        (Client(), "DELETE", reverse("login")),
    ]
    for cl, m, p in method_405_targets:
        r405 = cl.get(p) if m == "GET" else cl.post(p, {}) if m == "POST" else cl.delete(p)
        assert r405.status_code == 405, f"Expected 405 on {m} {p}, got {r405.status_code}"

    return {
        "combinations_checked": checked,
        "anon_redirects_302": anon_302,
        "role_denials_403": denied_403,
        "seller_ownership_isolation_verified": 5,
        "sales_receipt_cost_redaction_verified": True,
        "warehouse_readonly_catalog_suppliers_verified": True,
        "method_405_verified": len(method_405_targets),
        "missing_never_cache_catalog_routes": sorted(observed_missing_no_store),
    }


run_case("SRV15-01-matriz-rutas-roles-metodos", case_permission_matrix)


# 3. SRV15-02: Menu vs Server Coherence (DEC-12-PERMISOS-HISTORIAL-Y-MENU)
def case_menu_vs_server() -> dict:
    role_users = {
        "ADMIN": admin_user,
        "ALMACENERO": warehouse_user,
        "VENDEDOR": seller_user,
    }
    expected_sidebar = {
        "ADMIN": {
            "/inicio/",
            "/productos/",
            "/productos/nuevo/",
            "/productos/categorias/",
            "/inventario/proveedores/",
            "/inventario/stock/",
            "/inventario/ajustes/nuevo/",
            "/productos/vencimientos/",
            "/empleados/",
            "/caja/turnos/",
            "/ventas/historial/",
            "/salir/",
        },
        "ALMACENERO": {
            "/inicio/",
            "/inventario/stock/",
            "/productos/vencimientos/",
            "/inventario/carga-inicial/",
            "/inventario/entrada/",
            "/inventario/bajas/nueva/",
            "/productos/",
            "/inventario/proveedores/",
            "/salir/",
        },
        "VENDEDOR": {
            "/inicio/",
            "/caja/abrir/",
            "/ventas/",
            "/caja/cerrar/",
            "/caja/turnos/",
            "/ventas/historial/",
            "/ventas/historial/turno/",
            "/salir/",
        },
    }
    summary = {}
    for role_code, user_obj in role_users.items():
        cl = Client()
        cl.force_login(user_obj)
        resp = cl.get(reverse("dashboard"))
        assert resp.status_code == 200
        parser = _LinkExtractor()
        parser.feed(resp.content.decode("utf-8"))
        hrefs = {item["href"] for item in parser.links if item["href"].startswith("/")}
        assert hrefs == expected_sidebar[role_code], f"Mismatch for {role_code}: got {hrefs} vs {expected_sidebar[role_code]}"
        # Every link rendered in dashboard/sidebar for this role must return 200 on GET
        for h in sorted(hrefs):
            r_link = cl.get(h)
            assert r_link.status_code == 200, f"Role {role_code} menu link {h} returned {r_link.status_code}"
        summary[role_code] = sorted(hrefs)
    return {"verified_roles": summary}


run_case("SRV15-02-coherencia-menu-vs-servidor", case_menu_vs_server)


# 4. SRV15-03: Transversal CSRF Enforcement
def case_csrf_transversal() -> dict:
    post_targets = [
        (None, reverse("login"), {"email": admin_user.email, "password": PW_ALL}),
        (seller_user, reverse("logout"), {}),
        (admin_user, reverse("employee-create"), {"display_name": "X", "email": "x@x.invalid", "role": roles["VENDEDOR"].pk, "password": PW_ALL}),
        (admin_user, reverse("employee-edit", args=[seller2_user.pk]), {"display_name": "X", "email": seller2_user.email, "role": roles["VENDEDOR"].pk}),
        (admin_user, reverse("employee-deactivate", args=[seller2_user.pk]), {"action": "desactivar"}),
        (admin_user, reverse("category-create"), {"name": "CSRF Cat"}),
        (admin_user, reverse("product-entry"), {"name": "CSRF Prod", "barcode": "999999", "category": cat.pk, "sale_price": "5.00", "unit": "UND", "min_stock_threshold": "0"}),
        (admin_user, reverse("supplier-create"), {"name": "CSRF Sup", "ruc": "20999999999"}),
        (admin_user, reverse("physical-adjustment"), {"lot_id": str(lot_main.pk), "delta": "-1", "reason": "CSRF"}),
        (warehouse_user, reverse("inventory-load"), {"product": str(prod.pk)}),
        (warehouse_user, reverse("stock-entry"), {"product": str(prod.pk)}),
        (warehouse_user, reverse("stock-writeoff"), {"lot_id": str(lot_main.pk), "quantity": "1", "reason": "ROBO", "notes": "CSRF"}),
        (seller2_user, reverse("cash-open"), {"opening_amount": "10.00"}),
        (seller_user, reverse("cash-close"), {"counted_amount": "40.00"}),
        (seller_user, reverse("sales-draft"), {"product_id": str(prod.pk), "quantity": "1"}),
        (seller_user, reverse("sales-checkout"), {"draft_id": str(draft_active.pk), "cash_received": "10.00"}),
    ]
    for user_obj, path, data in post_targets:
        for mode in ("missing", "invalid", "cross_origin"):
            cl = Client(enforce_csrf_checks=True)
            if user_obj is not None:
                cl.force_login(user_obj)
            cl.get(reverse("login") if user_obj is None else reverse("dashboard"))
            payload = dict(data)
            headers = {}
            if mode == "invalid":
                payload["csrfmiddlewaretoken"] = "invalid-csrf-token-value-12345"
            elif mode == "cross_origin":
                if settings.CSRF_COOKIE_NAME in cl.cookies:
                    payload["csrfmiddlewaretoken"] = cl.cookies[settings.CSRF_COOKIE_NAME].value
                headers["HTTP_ORIGIN"] = "https://evil.example.invalid"
            before_post = db_digest()
            resp = cl.post(path, payload, **headers)
            assert resp.status_code == 403, f"CSRF {mode} on {path} returned {resp.status_code}"
            assert db_digest() == before_post, f"DB mutated during rejected CSRF {mode} request to {path}"
    return {"endpoints_tested": len(post_targets), "modes": ["missing", "invalid", "cross_origin"], "db_unchanged": True}


run_case("SRV15-03-csrf-enforcement-transversal", case_csrf_transversal)


# 5. SRV15-04: Sessions, Cookies, Rotation & Mid-Session Revocation
def case_sessions_and_cookies() -> dict:
    cl = Client(enforce_csrf_checks=True)
    r_get = cl.get(reverse("login"))
    csrf_before = cl.cookies[settings.CSRF_COOKIE_NAME].value
    sess = cl.session
    sess["pre_login_marker"] = "anon15"
    sess.save()
    old_session_key = sess.session_key

    r_login = cl.post(
        reverse("login"),
        {"email": seller2_user.email, "password": PW_ALL, "csrfmiddlewaretoken": csrf_before},
    )
    assert r_login.status_code == 302
    new_session_key = cl.session.session_key
    csrf_after = cl.cookies[settings.CSRF_COOKIE_NAME].value
    session_cookie = cl.cookies[settings.SESSION_COOKIE_NAME]
    csrf_cookie = cl.cookies[settings.CSRF_COOKIE_NAME]

    assert new_session_key != old_session_key
    assert not Session.objects.filter(session_key=old_session_key).exists()
    assert csrf_after != csrf_before
    assert session_cookie["httponly"] is True
    assert session_cookie["samesite"] == "Lax"
    assert csrf_cookie["httponly"] is True
    assert csrf_cookie["samesite"] == "Lax"
    assert settings.SESSION_EXPIRE_AT_BROWSER_CLOSE is True

    # Role change updates session role_code immediately
    update_employee(
        actor=admin_user,
        account=seller2_user,
        display_name=seller2_user.display_name,
        email=seller2_user.email,
        role=roles[Role.Code.WAREHOUSE],
    )
    assert Session.objects.get(session_key=new_session_key).get_decoded().get("role_code") == Role.Code.WAREHOUSE
    assert cl.get(reverse("inventory-load")).status_code == 200
    assert cl.get(reverse("sales-draft")).status_code == 403

    # Restore role back to VENDEDOR
    update_employee(
        actor=admin_user,
        account=seller2_user,
        display_name=seller2_user.display_name,
        email=seller2_user.email,
        role=roles[Role.Code.SELLER],
    )

    # Deactivation immediately deletes Session rows and redirects on next request
    deactivate_employee(actor=admin_user, account=seller2_user)
    assert not Session.objects.filter(session_key=new_session_key).exists()
    r_after_deact = cl.get(reverse("dashboard"))
    assert r_after_deact.status_code == 302 and reverse("login") in r_after_deact.headers["Location"]
    reactivate_employee(actor=admin_user, account=seller2_user)

    return {
        "session_rotated_on_login": True,
        "csrf_rotated_on_login": True,
        "session_cookie_httponly": True,
        "csrf_cookie_httponly": True,
        "session_cookie_samesite": session_cookie["samesite"],
        "session_expire_at_browser_close": settings.SESSION_EXPIRE_AT_BROWSER_CLOSE,
        "session_cookie_age_seconds": settings.SESSION_COOKIE_AGE,
        "session_save_every_request": settings.SESSION_SAVE_EVERY_REQUEST,
        "idle_session_timeout_finding": (settings.SESSION_COOKIE_AGE == 1209600 and not settings.SESSION_SAVE_EVERY_REQUEST),
        "role_change_updates_active_session": True,
        "deactivation_deletes_session_row": True,
    }


run_case("SRV15-04-sesiones-cookies-rotacion-y-revocacion", case_sessions_and_cookies)


# 6. SRV15-05 & SRV15-06: Passwords (Argon2id, RN-24) and Login Lockout (RN-18) + Email Length Boundary
def case_passwords_and_lockout() -> dict:
    assert identify_hasher(admin_user.password).algorithm == "argon2"
    login_email_max = LoginForm.base_fields["email"].max_length
    emp_create_email_max = EmployeeCreationForm.base_fields["email"].max_length
    emp_edit_email_max = EmployeeEditForm.base_fields["email"].max_length
    account_model_email_max = Account._meta.get_field("email").max_length

    # LoginForm now enforces max_length=254 (fixed in 01-E), so 300-char emails are rejected before LoginAttempt
    long_email = "u" * (300 - len("@audit15.invalid")) + "@audit15.invalid"
    cl = Client()
    r_long = cl.post(reverse("login"), {"email": long_email, "password": PW_ALL})
    assert r_long.status_code == 200
    assert "email" in r_long.context["form"].errors
    long_id = salted_hmac("identity.login.throttle", Account.normalize_email(long_email), algorithm="sha256").hexdigest()
    assert not LoginAttempt.objects.filter(identifier=long_id).exists()

    # Verify RN-24 weak passwords rejected in EmployeeCreationForm
    weak_samples = ["Ab1!", "abcdefgh", "ABCDEFG1", "1234567", "password", "AAAAAAA1"]
    weak_rejected = 0
    for idx, wp in enumerate(weak_samples):
        form = EmployeeCreationForm(
            data={
                "display_name": f"Weak {idx}",
                "email": f"weak{idx}@audit15.invalid",
                "role": str(roles[Role.Code.SELLER].pk),
                "password": wp,
            }
        )
        assert not form.is_valid() and "password" in form.errors, f"Weak password accepted: {wp}"
        weak_rejected += 1

    return {
        "primary_hasher": identify_hasher(admin_user.password).algorithm,
        "password_hashers": settings.PASSWORD_HASHERS,
        "login_form_email_max_length": login_email_max,
        "employee_create_email_max_length": emp_create_email_max,
        "employee_edit_email_max_length": emp_edit_email_max,
        "account_model_email_max_length": account_model_email_max,
        "login_email_254_aligned": (login_email_max == 254 and account_model_email_max == 254),
        "long_email_300_rejected_without_loginattempt": True,
        "rn24_weak_passwords_rejected": weak_rejected,
    }


run_case("SRV15-05-06-argon2id-rn24-y-limite-email-login", case_passwords_and_lockout)


# 7. SRV15-07: Verify DOC-02-04 & HU-USR-05/CA-01 Lockout Preservation, Session Revocation & IdentityAuditEvent
def case_doc02_04_defects() -> dict:
    from identity.models import IdentityAuditEvent

    target = Account.objects.create_user(
        "locked.emp@audit15.invalid",
        PW_ALL,
        display_name="Empleado Bloqueado",
        role=roles[Role.Code.SELLER],
    )
    old_id = salted_hmac("identity.login.throttle", target.email_normalized, algorithm="sha256").hexdigest()
    lock_expiry = timezone.now() + timedelta(minutes=15)

    # 1) Deactivate, set 5-failure lockout, then reactivate -> must PRESERVE LoginAttempt
    deactivate_employee(actor=admin_user, account=target)
    LoginAttempt.objects.update_or_create(
        identifier=old_id, defaults={"failures": 5, "locked_until": lock_expiry}
    )
    reactivate_employee(actor=admin_user, account=target)
    attempt_after_reactivate = LoginAttempt.objects.get(identifier=old_id)
    reactivate_preserves_lockout = (
        attempt_after_reactivate.failures == 5 and attempt_after_reactivate.locked_until is not None
    )
    assert reactivate_preserves_lockout, "reactivate_employee cleared active lockout"

    # 2) Change email via update_employee without unlock -> must CARRY LoginAttempt from old_id to new_id
    update_employee(
        actor=admin_user,
        account=target,
        display_name=target.display_name,
        email="locked.emp.new@audit15.invalid",
        role=roles[Role.Code.SELLER],
    )
    attempt_old_after_rename = LoginAttempt.objects.get(identifier=old_id)
    new_id = salted_hmac("identity.login.throttle", target.email_normalized, algorithm="sha256").hexdigest()
    attempt_new_after_rename = LoginAttempt.objects.filter(identifier=new_id).first()
    email_change_carried_lockout = (
        attempt_old_after_rename.failures == 0
        and attempt_old_after_rename.locked_until is None
        and attempt_new_after_rename is not None
        and attempt_new_after_rename.failures == 5
        and attempt_new_after_rename.locked_until is not None
    )
    assert email_change_carried_lockout, "Email rename did not preserve/carry LoginAttempt"

    # 3) Explicit unlock_account=True resets LoginAttempt, allowing login, and resets session immediately on password change
    update_employee(
        actor=admin_user,
        account=target,
        display_name=target.display_name,
        email=target.email,
        role=roles[Role.Code.SELLER],
        unlock_account=True,
    )
    attempt_after_unlock = LoginAttempt.objects.get(identifier=new_id)
    explicit_unlock_cleared = attempt_after_unlock.failures == 0 and attempt_after_unlock.locked_until is None
    assert explicit_unlock_cleared, "Explicit unlock_account did not clear LoginAttempt"

    cl_emp = Client()
    r_login = cl_emp.post(reverse("login"), {"email": target.email, "password": PW_ALL})
    assert r_login.status_code == 302
    emp_sess_key = cl_emp.session.session_key
    assert Session.objects.filter(session_key=emp_sess_key).exists()
    update_employee(
        actor=admin_user,
        account=target,
        display_name=target.display_name,
        email=target.email,
        role=roles[Role.Code.SELLER],
        new_password="NewPass15!Valid",
    )
    session_deleted_immediately = not Session.objects.filter(session_key=emp_sess_key).exists()
    assert session_deleted_immediately, "update_employee(new_password=...) did not delete DB session"
    r_next = cl_emp.get(reverse("dashboard"))
    invalidated_on_next_request = r_next.status_code == 302
    assert invalidated_on_next_request

    # Clean up target and verify recorded technical audit actions
    deactivate_employee(actor=admin_user, account=target)
    audit_actions = sorted(
        set(IdentityAuditEvent.objects.filter(target_id=str(target.pk)).values_list("action", flat=True))
    )
    assert {"EMPLOYEE_DEACTIVATED", "EMPLOYEE_REACTIVATED", "EMPLOYEE_UPDATED", "ACCOUNT_UNLOCKED", "PASSWORD_RESET"}.issubset(
        set(audit_actions)
    )
    return {
        "reactivate_preserves_active_lockout": reactivate_preserves_lockout,
        "email_change_carries_active_lockout": email_change_carried_lockout,
        "explicit_unlock_clears_lockout": explicit_unlock_cleared,
        "session_deleted_immediately_on_pw_reset": session_deleted_immediately,
        "session_invalidated_on_next_http_request": invalidated_on_next_request,
        "identity_audit_actions": audit_actions,
    }


run_case("SRV15-07-doc02-04-lockout-sesiones-y-auditoria", case_doc02_04_defects)


# 8. SRV15-08: /admin/ Exposure, Lockout Bypass & Unprotected ModelAdmin Registry (DOC-01-06/C-01, SEC-15-CONC-02)
def case_admin_exposure() -> dict:
    registered_models = sorted(
        f"{model._meta.app_label}.{model._meta.object_name}"
        for model in django_admin.site._registry.keys()
    )
    # Lock staff_user on commercial login (5 failures)
    cl_anon = Client()
    for _ in range(5):
        cl_anon.post(reverse("login"), {"email": staff_user.email, "password": "WrongPassword99!"})
    staff_id = salted_hmac("identity.login.throttle", staff_user.email_normalized, algorithm="sha256").hexdigest()
    attempt = LoginAttempt.objects.get(identifier=staff_id)
    assert attempt.failures == 5 and attempt.locked_until is not None

    # Confirm commercial login rejects staff_user with 15 min lockout
    r_comm = cl_anon.post(reverse("login"), {"email": staff_user.email, "password": PW_ALL})
    assert r_comm.status_code == 200 and "15 minuto(s)" in r_comm.content.decode("utf-8")

    # Now log in via /admin/login/ with the same locked staff_user!
    cl_admin_site = Client()
    r_adm_login = cl_admin_site.post(
        "/admin/login/?next=/admin/",
        {"username": staff_user.email, "password": PW_ALL, "next": "/admin/"},
    )
    assert r_adm_login.status_code == 302 and r_adm_login.headers["Location"] == "/admin/"
    # And the resulting session accesses commercial /inicio/!
    r_bridge = cl_admin_site.get(reverse("dashboard"))
    assert r_bridge.status_code == 200

    # Reset staff_user LoginAttempt
    LoginAttempt.objects.filter(identifier=staff_id).delete()
    return {
        "admin_url_mounted": True,
        "registered_models": registered_models,
        "locked_staff_bypassed_via_admin_login": True,
        "admin_session_bridges_to_commercial_dashboard": r_bridge.status_code == 200,
    }


run_case("SRV15-08-admin-exposicion-y-puente-sesion", case_admin_exposure)


# 9. SRV15-09: Logging Redaction (msg + exc_info), X-Request-ID Middleware & 500.html Check
def case_logging_and_exc_info() -> dict:
    filt = RedactSensitiveDataFilter()
    secret_val = "SuperSecretPw987!"
    # 1) Message redaction works
    rec_msg = logging.LogRecord(
        name="audit15",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="login failed password=%s sessionid=%s",
        args=(secret_val, "sess_tok_999"),
        exc_info=None,
    )
    filt.filter(rec_msg)
    formatted_msg = logging.Formatter().format(rec_msg)
    msg_redacted = (secret_val not in formatted_msg) and ("sess_tok_999" not in formatted_msg)

    # 2) Traceback / exc_info redaction (fixed in post-14-CIERRE build)
    try:
        raise RuntimeError(f"Conn error password={secret_val} sessionid=sess_tok_999")
    except RuntimeError:
        exc_tuple = sys.exc_info()
    rec_exc = logging.LogRecord(
        name="audit15",
        level=logging.ERROR,
        pathname=__file__,
        lineno=2,
        msg="Unhandled exception in view",
        args=(),
        exc_info=exc_tuple,
    )
    filt.filter(rec_exc)
    formatted_exc = logging.Formatter().format(rec_exc)
    exc_info_redacted = (secret_val not in formatted_exc) and ("sess_tok_999" not in formatted_exc)
    assert exc_info_redacted, "RedactSensitiveDataFilter failed to redact exc_info"

    # 3) Check X-Request-ID response header + 500.html template
    cl_req = Client()
    r_login_get = cl_req.get(reverse("login"), HTTP_X_REQUEST_ID="audit15-req-corr-001")
    response_has_x_request_id = r_login_get.headers.get("X-Request-ID") == "audit15-req-corr-001"
    assert response_has_x_request_id
    tpl_500 = (ROOT / "r1-pmv/templates/500.html").read_text(encoding="utf-8")
    has_request_id_in_500 = "request_id" in tpl_500

    return {
        "msg_and_args_redacted": msg_redacted,
        "exc_info_redacted": exc_info_redacted,
        "response_echoes_x_request_id": response_has_x_request_id,
        "template_500_has_request_id": has_request_id_in_500,
    }


run_case("SRV15-09-logging-redaccion-exc-info-y-request-id", case_logging_and_exc_info)


# 10. SRV15-10: Django check --deploy across environments (local, demo, production)
def case_check_deploy() -> dict:
    scenarios = [
        ("local_default", {"APP_ENV": "local", "DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": "x" * 50}),
        ("demo_default", {"APP_ENV": "demo", "DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": "x" * 50, "DJANGO_ALLOWED_HOSTS": "demo.minimarket.local"}),
        ("demo_ssl_true", {"APP_ENV": "demo", "DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": "x" * 50, "DJANGO_ALLOWED_HOSTS": "demo.minimarket.local", "DJANGO_SECURE_SSL_REDIRECT": "true"}),
        ("production_default", {"APP_ENV": "production", "DJANGO_DEBUG": "false", "DJANGO_SECRET_KEY": "x" * 50, "DJANGO_ALLOWED_HOSTS": "prod.minimarket.local", "POSTGRES_DB": "a", "POSTGRES_USER": "b", "POSTGRES_PASSWORD": "c", "POSTGRES_HOST": "127.0.0.1"}),
    ]
    results = {}
    for label, extra_env in scenarios:
        code = (
            "import os, django; from config import env; env.load_dotenv = lambda path=None: None; "
            "django.setup(); from django.core.management import call_command; "
            "call_command('check', '--deploy')"
        )
        env = os.environ.copy()
        for k in list(env.keys()):
            if k.startswith(("DJANGO_", "POSTGRES_", "APP_ENV")):
                env.pop(k, None)
        env.update(extra_env)
        env["DJANGO_SETTINGS_MODULE"] = "config.settings"
        proc = subprocess.run(
            [str(PYTHON), "-B", "-c", code],
            cwd=str(ROOT / "r1-pmv"),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        warnings = [
            line.strip()
            for line in out.splitlines()
            if "(security.W" in line
        ]
        results[label] = {"returncode": proc.returncode, "warnings": warnings}
    return results


run_case("SRV15-10-check-deploy-por-ambiente", case_check_deploy)


# 11. SRV15-11 & SRV15-12: reset_demo_db ProtectedError Defect & seed_demo Incomplete Kardex Defect
def case_reset_demo_and_seed_demo_defects() -> dict:
    # 1) In our current DB (which has InitialLoadLine, StockReceipt, StockWriteOff, PhysicalAdjustment, Sale, CashShiftClose),
    # running reset_demo_db --confirm under APP_ENV=demo raises ProtectedError and rolls back!
    before = db_digest()
    protected_error_raised = False
    protected_error_detail = ""
    with patch.dict(
        "os.environ",
        {
            "APP_ENV": "demo",
            "SEED_ADMIN_PASSWORD": "Test-only-Admin1",
            "SEED_WAREHOUSE_PASSWORD": "Test-only-Warehouse1",
            "SEED_SELLER_PASSWORD": "Test-only-Seller1",
        },
        clear=False,
    ):
        try:
            call_command("reset_demo_db", confirm=True, stdout=io.StringIO())
        except ProtectedError as exc:
            protected_error_raised = True
            protected_error_detail = str(exc)[:300]
    assert protected_error_raised, "Expected ProtectedError on reset_demo_db when operational tables have rows"
    assert db_digest() == before, "reset_demo_db was not atomic on ProtectedError"

    # 2) Test seed_pmv + seed_demo on clean canned category and check Kardex (product_movements)
    with patch.dict(
        "os.environ",
        {
            "SEED_ADMIN_PASSWORD": "Test-only-Admin1",
            "SEED_WAREHOUSE_PASSWORD": "Test-only-Warehouse1",
            "SEED_SELLER_PASSWORD": "Test-only-Seller1",
        },
        clear=False,
    ):
        call_command("seed_pmv", stdout=io.StringIO())
        call_command("seed_demo", stdout=io.StringIO())
    demo_prod = Product.objects.get(barcode="7750001000011")
    demo_load = InitialInventoryLoad.objects.get(product=demo_prod)
    demo_has_initial_lines = InitialLoadLine.objects.filter(load=demo_load).exists()
    cl_admin = Client()
    cl_admin.force_login(admin_user)
    r_kardex = cl_admin.get(reverse("product-movements", args=[demo_prod.pk]))
    kardex_html = r_kardex.content.decode("utf-8")
    kardex_shows_unavailable = "No disponible" in kardex_html

    return {
        "reset_demo_db_raises_protected_error_with_movements": protected_error_raised,
        "reset_demo_db_error_excerpt": protected_error_detail,
        "seed_demo_creates_initial_load_line": demo_has_initial_lines,
        "seed_demo_product_kardex_shows_unavailable_defect": kardex_shows_unavailable,
    }


run_case("SRV15-11-12-defectos-reset-demo-db-y-seed-demo", case_reset_demo_and_seed_demo_defects)


# 12. SRV15-13: Dockerfile, compose.yaml & 01-create-runtime-roles.sh static inspection
def case_deployment_artifacts() -> dict:
    dockerfile = (ROOT / "r1-pmv/Dockerfile").read_text(encoding="utf-8")
    compose = (ROOT / "r1-pmv/compose.yaml").read_text(encoding="utf-8")
    init_sh = (ROOT / "r1-pmv/db/init/01-create-runtime-roles.sh").read_text(encoding="utf-8")
    pg_img_lines = [line.strip() for line in compose.splitlines() if "image:" in line]
    return {
        "dockerfile_base_image": dockerfile.splitlines()[0].strip(),
        "dockerfile_runs_nonroot_user": "USER pmv" in dockerfile,
        "dockerfile_cmd_uses_gunicorn": "gunicorn" in dockerfile,
        "design_02_target_python": "Python 3.12 (02_Diseno_Tecnico_R1_PMV.md §2.1)",
        "compose_postgres_image": pg_img_lines[0] if pg_img_lines else "missing",
        "compose_web_uses_runserver": "manage.py runserver" in compose,
        "compose_web_binds_loopback_only": "127.0.0.1:8000:8000" in compose,
        "init_sh_creates_migrator_and_app_user": ("migrator_user" in init_sh and "app_user" in init_sh),
        "backup_restore_scripts_in_repo": any((ROOT / "r1-pmv").glob("*backup*")) or any((ROOT / "r1-pmv/db").rglob("*backup*")),
    }


run_case("SRV15-13-artefactos-despliegue-compose-dockerfile", case_deployment_artifacts)
run_case("SRV15-00-regresion-completa-tests", case_existing_suite)

# Clean up temporary SQLite directory
connection.close()
import shutil

shutil.rmtree(TEMP_DB_DIR, ignore_errors=True)

report["after_build"] = {k: v for k, v in compute_build().items() if k != "files"}
report["source_stable"] = report["before_build"] == report["after_build"]
report["passed"] = sum(1 for c in report["cases"] if c["ok"])
report["total"] = len(report["cases"])
report["ok"] = report["passed"] == report["total"] and report["source_stable"]
report["finished_utc"] = datetime.now(dt_timezone.utc).isoformat()

(HERE / "resultados-servidor.json").write_text(
    json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(
    json.dumps(
        {k: report[k] for k in ("ok", "passed", "total", "source_stable")},
        ensure_ascii=False,
    )
)
sys.exit(0 if report["ok"] else 1)
