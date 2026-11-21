"""Isolated Stage 06 Revalidation Runner (checks, comprehensive server/boundary/role audit, browser harness).
Preserves legacy audit06_run.py untouched; reuses audit06_settings.py isolation (never loads .env, never touches r1_pmv.sqlite3).
"""
from __future__ import annotations

import contextlib
import hashlib
from html.parser import HTMLParser
import io
import json
import os
import secrets
import socket
import subprocess
import sys
import time
import uuid
from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
SUPPORT = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def extract_input_value(html: str, name: str) -> str | None:
    class _Parser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.value: str | None = None

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag != "input" or self.value is not None:
                return
            attr_map = dict(attrs)
            if attr_map.get("name") == name:
                self.value = attr_map.get("value")

    parser = _Parser()
    parser.feed(html)
    return parser.value


def extract_role_alerts(html: str) -> list[str]:
    class _Parser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.alerts: list[str] = []
            self._stack: list[tuple[str, bool, list[str]]] = []

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            is_alert = dict(attrs).get("role") == "alert"
            self._stack.append((tag, is_alert, []))

        def handle_data(self, data: str) -> None:
            for _, is_alert, buf in self._stack:
                if is_alert:
                    buf.append(data)

        def handle_endtag(self, tag: str) -> None:
            if not self._stack:
                return
            _, is_alert, buf = self._stack.pop()
            if is_alert:
                text = " ".join("".join(buf).split())
                if text:
                    self.alerts.append(text)

    parser = _Parser()
    parser.feed(html)
    return parser.alerts


def setup(default_cookies: bool = False) -> None:
    if str(APP) not in sys.path:
        sys.path.insert(0, str(APP))
    if str(SUPPORT) not in sys.path:
        sys.path.insert(0, str(SUPPORT))
    if default_cookies:
        os.environ["AUDIT06_DEFAULT_COOKIES"] = "1"
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit06_settings"
    import django

    django.setup()


def prepare_empty_migrated_db() -> None:
    from django.core.management import call_command

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)


def make_run_dir(tag: str) -> tuple[Path, Path, str]:
    stamp = datetime.now(dt_timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)
    run_dir = RESULTS / "datos" / f"etapa06-reval-{tag}-{stamp}"
    out_dir = RESULTS / "evidencias" / f"06-reval-{tag}-{stamp}"
    run_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    write_json(run_dir / "marker.json", {"run": run_dir.name, "created_utc": stamp})
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")
    return run_dir, out_dir, stamp


def protected_hashes() -> dict[str, str | None]:
    protected = [
        *APP.glob("*.sqlite3"),
        *(
            p
            for d in (RESULTS / "datos").iterdir()
            if d.is_dir() and d.name.startswith(("etapa00", "etapa06", "06-"))
            for p in d.rglob("*.sqlite3")
        ),
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]
    return {str(p.relative_to(ROOT)): digest(p) if p.exists() else None for p in protected}


def snapshot() -> dict:
    from cash.models import CashShift
    from catalog.models import Category, Product
    from inventory.models import (
        InitialInventoryLoad,
        InitialLoadLine,
        Lot,
        PhysicalAdjustment,
        StockReceipt,
        StockReceiptCounter,
        StockReceiptLine,
        StockWriteOff,
        Supplier,
    )
    from sales.models import Sale, SaleLine, SaleLotAllocation

    return {
        "categories": list(Category.objects.order_by("name").values("id", "name", "is_active", "state_version")),
        "suppliers": list(Supplier.objects.order_by("name", "ruc").values("id", "name", "ruc", "is_active")),
        "loads": list(
            InitialInventoryLoad.objects.order_by("confirmed_at", "pk").values(
                "id",
                "product_id",
                "responsible_id",
                "confirmed_at",
                "product_snapshot_name",
                "responsible_snapshot_name",
                "supplier_snapshot_name",
                "average_cost_snapshot",
            )
        ),
        "initial_load_lines": list(
            InitialLoadLine.objects.order_by("load_id", "number", "pk").values(
                "id", "load_id", "lot_id", "number", "quantity", "unit_cost", "expiration_date", "received_at"
            )
        ),
        "stock_receipt_counters": list(
            StockReceiptCounter.objects.order_by("key").values("key", "last_number")
        ),
        "stock_receipts": list(
            StockReceipt.objects.order_by("correlative", "pk").values(
                "id",
                "correlative",
                "product_id",
                "responsible_id",
                "supplier_id",
                "idempotency_key",
                "content_signature",
                "confirmed_at",
                "product_snapshot_name",
                "product_snapshot_barcode",
                "responsible_snapshot_name",
                "supplier_snapshot_name",
                "supplier_snapshot_ruc",
                "average_cost_after",
            )
        ),
        "stock_receipt_lines": list(
            StockReceiptLine.objects.order_by("receipt_id", "number", "pk").values(
                "id", "receipt_id", "lot_id", "number", "quantity", "unit_cost", "expiration_date"
            )
        ),
        "lots": list(
            Lot.objects.order_by("product_id", "number_normalized", "received_at", "pk").values(
                "id",
                "product_id",
                "initial_load_id",
                "supplier_id",
                "responsible_id",
                "is_initial",
                "number",
                "number_normalized",
                "initial_quantity",
                "available_quantity",
                "unit_cost",
                "expiration_date",
                "received_at",
            )
        ),
        "products": list(
            Product.objects.order_by("barcode").values(
                "id", "name", "barcode", "category_id", "is_active", "minimum_stock", "average_cost"
            )
        ),
        "cash_shifts": list(CashShift.objects.order_by("opened_at").values("id", "status", "seller_id")),
        "sales": list(Sale.objects.order_by("correlative").values("id", "correlative", "total_amount", "seller_id")),
        "sale_lines": list(
            SaleLine.objects.order_by("pk").values(
                "id", "sale_id", "product_id", "quantity", "unit_price", "amount", "unit_cost"
            )
        ),
        "sale_lot_allocations": list(
            SaleLotAllocation.objects.order_by("line_id", "lot_id").values(
                "id", "line_id", "lot_id", "quantity", "lot_snapshot_number", "lot_snapshot_expiration_date"
            )
        ),
        "write_offs": list(
            StockWriteOff.objects.order_by("correlativo").values(
                "id", "correlativo", "lot_id", "quantity", "unit_cost", "reason"
            )
        ),
        "physical_adjustments": list(
            PhysicalAdjustment.objects.order_by("created_at", "pk").values(
                "id", "lot_id", "delta", "unit_cost", "reason"
            )
        ),
    }


def prepare_stage06_fixtures(run_dir: Path, out_dir: Path) -> dict:
    from django.utils import timezone as tz

    from cash.models import CashRegister
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.models import Lot
    from inventory.services import LotInput, confirm_initial_load, create_supplier

    admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    creds = {}
    accounts = {}
    for key, email, display, role in [
        ("admin", "admin@audit06r.invalid", "Admin Audit06R", admin_role),
        ("warehouse", "warehouse@audit06r.invalid", "Lucia Almacen06R", wh_role),
        ("warehouse2", "warehouse2@audit06r.invalid", "Pedro Almacen06R", wh_role),
        ("seller", "seller@audit06r.invalid", "Vendedor Audit06R", seller_role),
    ]:
        pw = secrets.token_urlsafe(18) + "A1!"
        creds[key] = {"email": email, "password": pw}
        accounts[key] = Account.objects.create_user(email, pw, display_name=display, role=role)

    (run_dir / ".credentials.json").write_text(json.dumps(creds), encoding="utf-8")

    cat_drinks = Category.objects.create(name="Bebidas Audit06R", is_active=True)
    cat_food = Category.objects.create(name="Abarrotes Audit06R", is_active=True)
    cat_inactive = Category.objects.create(name="Categoría Suspendida Audit06R", is_active=False)

    p_entry1 = Product.objects.create(
        category=cat_drinks,
        name="Jugo Natural Naranja 1L",
        barcode="775060600001",
        sale_price=Decimal("7.50"),
        minimum_stock=5,
    )
    # F-COSTO: 18@3.0000 total (8 expired + 10 sellable) -> +10@6 -> 28@4.0714
    p_fcosto = Product.objects.create(
        category=cat_drinks,
        name="Leche Evaporada FCOSTO 400g",
        barcode="775060600010",
        sale_price=Decimal("5.00"),
        minimum_stock=4,
    )
    p_exhausted = Product.objects.create(
        category=cat_food,
        name="Arroz Extra Costeño 1kg",
        barcode="775060600002",
        sale_price=Decimal("4.80"),
        minimum_stock=8,
    )
    p_expired_only = Product.objects.create(
        category=cat_drinks,
        name="Yogurt Vencido Audit06R",
        barcode="775060600003",
        sale_price=Decimal("5.50"),
        minimum_stock=3,
    )
    p_no_load = Product.objects.create(
        category=cat_food,
        name="Conserva Sin Carga Audit06R",
        barcode="775060600004",
        sale_price=Decimal("6.00"),
        minimum_stock=5,
    )
    p_inactive_loaded = Product.objects.create(
        category=cat_food,
        name="Atún Inactivo Audit06R",
        barcode="775060600005",
        sale_price=Decimal("5.90"),
        minimum_stock=5,
    )
    p_catoff_loaded = Product.objects.create(
        category=cat_food,
        name="Fideo Categoría Suspendida Audit06R",
        barcode="775060600006",
        sale_price=Decimal("4.20"),
        minimum_stock=5,
    )

    sup_active = create_supplier(
        actor=accounts["admin"],
        name="Distribuidora Andina SAC",
        ruc="20506070801",
        phone="014401234",
    )
    sup_long = create_supplier(
        actor=accounts["admin"],
        name="Proveedor Corporativo Alimentos y Bebidas Mayorista Metropolitana del Perú SAC " + ("X" * 40),
        ruc="20506070802",
        phone="999888777",
    )
    sup_race = create_supplier(
        actor=accounts["admin"],
        name="Proveedor En Carrera Audit06R",
        ruc="20506070803",
        phone="987654321",
    )

    today = tz.localdate()
    tomorrow = today + timedelta(days=1)
    soon_10 = today + timedelta(days=10)
    soon_20 = today + timedelta(days=20)
    future_45 = today + timedelta(days=45)
    future_60 = today + timedelta(days=60)
    future_90 = today + timedelta(days=90)

    load_entry1 = confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_entry1,
        supplier=sup_active,
        lots=[
            LotInput("L01-INI-LATE", 4, Decimal("2.0000"), future_90),
            LotInput("L02-INI-EARLY", 6, Decimal("3.0000"), soon_20),
        ],
    )
    load_fcosto = confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_fcosto,
        supplier=sup_active,
        lots=[
            LotInput("FC-EXP-01", 8, Decimal("3.0000"), tomorrow),
            LotInput("FC-VIG-01", 10, Decimal("3.0000"), future_90),
        ],
    )
    Lot.objects.filter(product=p_fcosto, number_normalized="FC-EXP-01").update(expiration_date=today)

    load_exhausted = confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_exhausted,
        supplier=sup_active,
        lots=[LotInput("EXH-INI-01", 5, Decimal("2.0000"), future_45)],
    )
    Lot.objects.filter(product=p_exhausted).update(available_quantity=0)

    load_expired = confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_expired_only,
        lots=[LotInput("L-VENCE-HOY", 8, Decimal("2.0000"), tomorrow)],
    )
    Lot.objects.filter(product=p_expired_only).update(expiration_date=today)

    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_inactive_loaded,
        lots=[LotInput("INACT-INI-01", 4, Decimal("2.0000"), future_45)],
    )
    p_inactive_loaded.is_active = False
    p_inactive_loaded.save(update_fields=["is_active"])

    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_catoff_loaded,
        lots=[LotInput("CATOFF-INI-01", 4, Decimal("2.0000"), future_45)],
    )
    p_catoff_loaded.category = cat_inactive
    p_catoff_loaded.save(update_fields=["category"])

    CashRegister.objects.create(code="CAJA-01")

    fixture = {
        "today": today.isoformat(),
        "tomorrow": tomorrow.isoformat(),
        "soon_10": soon_10.isoformat(),
        "soon_20": soon_20.isoformat(),
        "future_45": future_45.isoformat(),
        "future_60": future_60.isoformat(),
        "future_90": future_90.isoformat(),
        "categories": {
            "drinks": {"id": str(cat_drinks.pk), "name": cat_drinks.name, "state_version": cat_drinks.state_version},
            "food": {"id": str(cat_food.pk), "name": cat_food.name, "state_version": cat_food.state_version},
            "inactive": {"id": str(cat_inactive.pk), "name": cat_inactive.name},
        },
        "products": {
            "entry1": {"id": str(p_entry1.pk), "name": p_entry1.name, "barcode": p_entry1.barcode, "load_id": str(load_entry1.pk)},
            "fcosto": {"id": str(p_fcosto.pk), "name": p_fcosto.name, "barcode": p_fcosto.barcode, "load_id": str(load_fcosto.pk)},
            "exhausted": {"id": str(p_exhausted.pk), "name": p_exhausted.name, "barcode": p_exhausted.barcode, "load_id": str(load_exhausted.pk)},
            "expired_only": {"id": str(p_expired_only.pk), "name": p_expired_only.name, "barcode": p_expired_only.barcode, "load_id": str(load_expired.pk)},
            "no_load": {"id": str(p_no_load.pk), "name": p_no_load.name},
            "inactive": {"id": str(p_inactive_loaded.pk), "name": p_inactive_loaded.name},
            "cat_off": {"id": str(p_catoff_loaded.pk), "name": p_catoff_loaded.name},
        },
        "suppliers": {
            "active": {"id": str(sup_active.pk), "name": sup_active.name, "ruc": sup_active.ruc},
            "long": {"id": str(sup_long.pk), "name": sup_long.name, "ruc": sup_long.ruc},
            "race": {"id": str(sup_race.pk), "name": sup_race.name, "ruc": sup_race.ruc},
        },
    }
    write_json(out_dir / "fixture.json", fixture)
    return fixture


def run_server_suite() -> int:
    """Execute Stage 06 full server/HTTP/service/boundary revalidation in an isolated SQLite DB."""
    start_hashes = protected_hashes()
    run_dir, out_dir, stamp = make_run_dir("server")
    os.environ.update(AUDIT06_RUN_DIR=str(run_dir), AUDIT06_OUT=str(out_dir), AUDIT06_DEFAULT_COOKIES="1")
    setup(default_cookies=True)

    from django.core.exceptions import PermissionDenied, ValidationError
    from django.test import Client
    from django.urls import URLPattern, URLResolver, get_resolver, reverse
    from django.utils import timezone as tz

    from cash.models import CashRegister
    from cash.services import open_cash_shift
    from catalog.models import Category, Product
    from catalog.services import toggle_category_status, toggle_product_availability
    from identity.models import Account, Role
    from inventory.models import (
        InitialInventoryLoad,
        Lot,
        StockReceipt,
        StockReceiptCounter,
        StockReceiptLine,
        StockWriteOff,
        Supplier,
    )
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        create_supplier,
        register_physical_adjustment,
        register_stock_entry,
        toggle_supplier_status,
        write_off_stock,
    )
    from sales.models import SaleLine
    from sales.services import add_product_to_draft, checkout_sale

    prepare_empty_migrated_db()

    results: list[dict] = []

    def record(case_id: str, ok: bool, details: dict | None = None) -> None:
        results.append({"id": case_id, "ok": bool(ok), "details": details or {}})
        if not ok:
            raise AssertionError(f"Case failed: {case_id} -> {details}")

    def collect_urls(patterns, prefix=""):
        out_urls = []
        for pat in patterns:
            if isinstance(pat, URLPattern):
                out_urls.append((prefix + str(pat.pattern), pat.name or ""))
            elif isinstance(pat, URLResolver):
                out_urls.extend(collect_urls(pat.url_patterns, prefix + str(pat.pattern)))
        return out_urls

    def make_payload(product_id, supplier_id="", lots=None, key=None, total_forms=None, initial_forms="0"):
        lots = lots if lots is not None else [{}]
        data = {
            "idempotency_key": str(key or uuid.uuid4()),
            "product": str(product_id),
            "supplier": str(supplier_id),
            "lots-TOTAL_FORMS": str(len(lots) if total_forms is None else total_forms),
            "lots-INITIAL_FORMS": str(initial_forms),
            "lots-MIN_NUM_FORMS": "1",
            "lots-MAX_NUM_FORMS": "1000",
        }
        for idx, row in enumerate(lots):
            for field in ("number", "quantity", "unit_cost", "expiration_date"):
                data[f"lots-{idx}-{field}"] = str(row.get(field, ""))
        return data

    # Base accounts & master fixtures
    r_adm = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    r_wh = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    r_sel = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
    pw = secrets.token_urlsafe(16) + "A1!"
    adm = Account.objects.create_user("admin@srv06.invalid", pw, display_name="Admin Srv06", role=r_adm)
    wh1 = Account.objects.create_user("wh1@srv06.invalid", pw, display_name="Almacenero Uno", role=r_wh)
    wh2 = Account.objects.create_user("wh2@srv06.invalid", pw, display_name="Almacenero Dos", role=r_wh)
    sel = Account.objects.create_user("sel@srv06.invalid", pw, display_name="Vendedor Uno", role=r_sel)

    CashRegister.objects.create(code="CAJA-01")
    cat = Category.objects.create(name="Lácteos Srv06", is_active=True)
    leche = Product.objects.create(
        category=cat, name="Leche F-COSTO", barcode="775000000101", sale_price=Decimal("8.00"), minimum_stock=5
    )
    extra_prod = Product.objects.create(
        category=cat, name="Avena Frontera Srv06", barcode="775000000102", sale_price=Decimal("4.50"), minimum_stock=5
    )
    legacy_prod = Product.objects.create(
        category=cat, name="Producto Legado Srv06", barcode="775000000103", sale_price=Decimal("3.00"), minimum_stock=5
    )
    sup_a = create_supplier(actor=adm, name="Proveedor Alfa SAC", ruc="20111111111", phone="999111222")
    sup_off = create_supplier(actor=adm, name="Proveedor Inactivo SAC", ruc="20222222222", phone="")
    toggle_supplier_status(actor=adm, supplier=sup_off, is_active=False)

    today = tz.localdate()
    tomorrow = today + timedelta(days=1)
    future_60 = today + timedelta(days=60)
    future_90 = today + timedelta(days=90)

    # Setup Leche F-COSTO: 19@3 initially -> sell 1 at average 3 -> leaves exact 18@3 (8 expired + 10 sellable)
    confirm_initial_load(
        actor=wh1,
        product=leche,
        supplier=sup_a,
        lots=[
            LotInput("FC-EXP", 8, Decimal("3.0000"), tomorrow),
            LotInput("FC-VIG", 11, Decimal("3.0000"), future_90),
        ],
    )
    Lot.objects.filter(product=leche, number_normalized="FC-EXP").update(expiration_date=today)
    open_cash_shift(actor=sel, opening_amount=Decimal("50.00"))
    draft = add_product_to_draft(actor=sel, product_id=leche.pk, quantity=1)
    pre_sale = checkout_sale(actor=sel, draft_id=draft.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4())
    pre_sale_cost = SaleLine.objects.get(sale=pre_sale).unit_cost
    confirm_initial_load(actor=wh1, product=extra_prod, lots=[LotInput("INI-FR", 5, Decimal("2.0000"), future_60)])
    confirm_initial_load(actor=wh1, product=legacy_prod, lots=[LotInput("INI-LEG", 5, Decimal("2.0000"), future_60)])

    # 1. Absence of HU-SOL / HU-DASH futures
    all_urls = collect_urls(get_resolver().url_patterns)
    sol_urls = [u for u in all_urls if any(k in (u[0] + u[1]).lower() for k in ("solicitud", "reposic", "sol-", "dash-05"))]
    sol_templates = [
        str(p.relative_to(APP))
        for p in APP.rglob("*.html")
        if any(k in p.name.lower() for k in ("solicitud", "reposic"))
    ]
    record("S06R-FUTUROS-01", len(sol_urls) == 0 and len(sol_templates) == 0, {"sol_urls": sol_urls, "sol_templates": sol_templates})

    # 2. CP-DOC-03AB-01-001 + F-COSTO via HTTP & Roles
    c_anon = Client()
    r_anon_entry = c_anon.get(reverse("stock-entry"))
    c_wh1 = Client(enforce_csrf_checks=True)
    c_wh1.force_login(wh1)
    c_wh2 = Client(enforce_csrf_checks=True)
    c_wh2.force_login(wh2)
    c_adm = Client(enforce_csrf_checks=True)
    c_adm.force_login(adm)
    c_sel = Client(enforce_csrf_checks=True)
    c_sel.force_login(sel)

    r_get_entry = c_wh1.get(reverse("stock-entry"))
    csrf_tok = c_wh1.cookies["csrftoken"].value

    # Attempt as ADMIN and VENDEDOR with valid payload -> 403 and zero writes
    key_fc1 = uuid.UUID("11111111-1111-4111-8111-111111111111")
    before_denied = snapshot()
    adm_get = c_adm.get(reverse("stock-entry"))
    c_adm.get(reverse("supplier-create"))
    adm_csrf = c_adm.cookies["csrftoken"].value
    adm_post = c_adm.post(
        reverse("stock-entry"),
        {**make_payload(leche.pk, "", [{"number": "C", "quantity": "10", "unit_cost": "6.0000", "expiration_date": future_60.isoformat()}], key=key_fc1), "csrfmiddlewaretoken": adm_csrf},
    )
    sel_get = c_sel.get(reverse("stock-entry"))
    c_sel.get(reverse("logout"))
    sel_csrf = c_sel.cookies["csrftoken"].value
    sel_post = c_sel.post(
        reverse("stock-entry"),
        {**make_payload(leche.pk, "", [{"number": "C", "quantity": "10", "unit_cost": "6.0000", "expiration_date": future_60.isoformat()}], key=key_fc1), "csrfmiddlewaretoken": sel_csrf},
    )
    record(
        "S06R-ROLES-DENEGADOS-01",
        r_anon_entry.status_code == 302
        and adm_get.status_code == 403
        and adm_post.status_code == 403
        and sel_get.status_code == 403
        and sel_post.status_code == 403
        and snapshot() == before_denied,
        {"anon": r_anon_entry.status_code, "adm_get": adm_get.status_code, "adm_post": adm_post.status_code, "sel_get": sel_get.status_code, "sel_post": sel_post.status_code},
    )

    # ALMACENERO confirms direct receipt WITHOUT supplier & WITHOUT SOL (CP-DOC-03AB-01-001 + DOC-03AH-01/C-01)
    r_fc1 = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(leche.pk, "", [{"number": "C", "quantity": "10", "unit_cost": "6.0000", "expiration_date": future_60.isoformat()}], key=key_fc1), "csrfmiddlewaretoken": csrf_tok},
    )
    receipt1 = StockReceipt.objects.get(idempotency_key=key_fc1)
    leche.refresh_from_db()
    r_rec1_wh = c_wh1.get(reverse("stock-receipt", args=(receipt1.pk,)))
    r_rec1_adm = c_adm.get(reverse("stock-receipt", args=(receipt1.pk,)))
    r_rec1_sel = c_sel.get(reverse("stock-receipt", args=(receipt1.pk,)))
    r_rec1_anon = c_anon.get(reverse("stock-receipt", args=(receipt1.pk,)))
    rec1_text = r_rec1_wh.content.decode("utf-8")
    adm_rec1_text = r_rec1_adm.content.decode("utf-8")
    record(
        "S06R-DOC03AB-FCOSTO-01",
        r_fc1.status_code == 302
        and receipt1.correlative == "R-00000001"
        and receipt1.supplier_id is None
        and receipt1.average_cost_after == Decimal("4.0714")
        and leche.physical_stock == 28
        and leche.sellable_stock == 20
        and leche.average_cost == Decimal("4.0714")
        and "Sin proveedor asignado" in rec1_text
        and "4,07" in rec1_text
        and "solicitud aprobada" not in rec1_text.lower()
        and r_rec1_adm.status_code == 200
        and "Registrar otra recepción" not in adm_rec1_text
        and r_rec1_sel.status_code == 403
        and r_rec1_anon.status_code == 302,
        {
            "correlative": receipt1.correlative,
            "physical": leche.physical_stock,
            "sellable": leche.sellable_stock,
            "avg": str(leche.average_cost),
            "cache_control": r_rec1_wh.headers.get("Cache-Control"),
        },
    )

    # 3. Replay identical / divergent / cross-actor / lost-context & second commercial delivery C@8 -> R-00000002
    snap_r1 = snapshot()
    r_fc1_replay = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(leche.pk, "", [{"number": " c ", "quantity": "10", "unit_cost": "6.0000", "expiration_date": future_60.isoformat()}], key=key_fc1), "csrfmiddlewaretoken": csrf_tok},
    )
    r_fc1_div = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(leche.pk, "", [{"number": "C", "quantity": "11", "unit_cost": "6.0000", "expiration_date": future_60.isoformat()}], key=key_fc1), "csrfmiddlewaretoken": csrf_tok},
    )
    c_wh2.get(reverse("stock-entry"))
    wh2_csrf = c_wh2.cookies["csrftoken"].value
    r_fc1_other = c_wh2.post(
        reverse("stock-entry"),
        {**make_payload(leche.pk, "", [{"number": "C", "quantity": "10", "unit_cost": "6.0000", "expiration_date": future_60.isoformat()}], key=key_fc1), "csrfmiddlewaretoken": wh2_csrf},
    )
    record(
        "S06R-DOC03AI-REPLAY-01",
        r_fc1_replay.status_code == 302
        and r_fc1_replay.url.endswith(f"/inventario/recepciones/{receipt1.pk}/")
        and r_fc1_div.status_code == 200
        and "otro contenido o responsable" in r_fc1_div.content.decode("utf-8")
        and r_fc1_other.status_code == 200
        and "otro contenido o responsable" in r_fc1_other.content.decode("utf-8")
        and snapshot() == snap_r1,
        {"replay_url": r_fc1_replay.url, "div_status": r_fc1_div.status_code, "other_status": r_fc1_other.status_code},
    )

    # Second real delivery of lot C with same date, new key -> R-00000002, qty 5@8 -> 33 @ 4.6667
    key_fc2 = uuid.UUID("22222222-2222-4222-8222-222222222222")
    r_fc2 = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(leche.pk, sup_a.pk, [{"number": "C", "quantity": "5", "unit_cost": "8.0000", "expiration_date": future_60.isoformat()}], key=key_fc2), "csrfmiddlewaretoken": csrf_tok},
    )
    receipt2 = StockReceipt.objects.get(idempotency_key=key_fc2)
    leche.refresh_from_db()
    # Contradictory date for C must reject cleanly
    snap_r2 = snapshot()
    r_fc_bad_date = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(leche.pk, sup_a.pk, [{"number": " c ", "quantity": "5", "unit_cost": "8.0000", "expiration_date": future_90.isoformat()}]), "csrfmiddlewaretoken": csrf_tok},
    )
    # Exit 1 by POS + deplete physical to 0 -> verify RN-28 & zero reset
    draft2 = add_product_to_draft(actor=sel, product_id=leche.pk, quantity=1)
    sale2 = checkout_sale(actor=sel, draft_id=draft2.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4())
    leche.refresh_from_db()
    avg_after_sale2 = leche.average_cost
    sale2_cost = SaleLine.objects.get(sale=sale2).unit_cost
    pre_sale_cost_after = SaleLine.objects.get(sale=pre_sale).unit_cost
    # Deplete all remaining physical units of leche
    for lot in Lot.objects.filter(product=leche, available_quantity__gt=0):
        reason = StockWriteOff.Reason.EXPIRATION if lot.expiration_date <= today else StockWriteOff.Reason.DAMAGE
        write_off_stock(actor=wh1, lot=lot, quantity=lot.available_quantity, reason=reason, notes="Agotamiento F-COSTO prueba")
    leche.refresh_from_db()
    # Positive adjustment Q0 without cost rejected
    q0_rejected = False
    try:
        register_physical_adjustment(actor=adm, lot=Lot.objects.filter(product=leche).first(), delta=2, reason="Sin costo")
    except ValidationError:
        q0_rejected = True
    receipt1.refresh_from_db()
    record(
        "S06R-DOC03AH-CICLO-02",
        r_fc2.status_code == 302
        and receipt2.correlative == "R-00000002"
        and r_fc_bad_date.status_code == 200
        and "ya existe con otro vencimiento" in r_fc_bad_date.content.decode("utf-8")
        and pre_sale_cost == Decimal("3.0000")
        and pre_sale_cost_after == Decimal("3.0000")
        and sale2_cost == Decimal("4.6666")
        and avg_after_sale2 == Decimal("4.6666")
        and leche.physical_stock == 0
        and leche.average_cost == Decimal("0.0000")
        and receipt1.average_cost_after == Decimal("4.0714")
        and q0_rejected,
        {"r2": receipt2.correlative, "sale2_cost": str(sale2_cost), "avg_zero": str(leche.average_cost), "q0_rejected": q0_rejected},
    )

    # 4. Replay after deactivation/expiry + swapped lot order + key preservation after qty=0 error
    key_swap = uuid.uuid4()
    lots_ab = [
        LotInput("SWAP-B", 2, Decimal("3.0000"), future_90),
        LotInput("SWAP-A", 3, Decimal("4.0000"), future_60),
    ]
    rec_swap1 = register_stock_entry(actor=wh1, product=extra_prod, lots=lots_ab, supplier=sup_a, idempotency_key=key_swap)
    rec_swap2 = register_stock_entry(actor=wh1, product=extra_prod, lots=list(reversed(lots_ab)), supplier=sup_a, idempotency_key=key_swap)

    # Now deactivate product, category, supplier AND advance clock past lot expiration -> wh1 HTTP replay STILL recovers 302!
    toggle_product_availability(actor=adm, product=extra_prod, is_active=False)
    toggle_category_status(actor=adm, category=cat, is_active=False)
    toggle_supplier_status(actor=adm, supplier=sup_a, is_active=False)
    with patch("inventory.services.timezone.localdate", return_value=future_90 + timedelta(days=5)):
        r_post_disable_replay = c_wh1.post(
            reverse("stock-entry"),
            {
                **make_payload(
                    extra_prod.pk,
                    sup_a.pk,
                    [
                        {"number": "SWAP-A", "quantity": "3", "unit_cost": "4.0000", "expiration_date": future_60.isoformat()},
                        {"number": "SWAP-B", "quantity": "2", "unit_cost": "3.0000", "expiration_date": future_90.isoformat()},
                    ],
                    key=key_swap,
                ),
                "csrfmiddlewaretoken": csrf_tok,
            },
        )
    # Restore category, product, supplier
    toggle_category_status(actor=adm, category=cat, is_active=True)
    toggle_product_availability(actor=adm, product=extra_prod, is_active=True)
    toggle_supplier_status(actor=adm, supplier=sup_a, is_active=True)

    # Key preservation across validation error (qty=0 then qty=2 with same key)
    key_fix = uuid.uuid4()
    r_err_fix = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(extra_prod.pk, sup_a.pk, [{"number": "FIX-KEY-1", "quantity": "0", "unit_cost": "2.0000", "expiration_date": future_60.isoformat()}], key=key_fix), "csrfmiddlewaretoken": csrf_tok},
    )
    preserved_key = extract_input_value(r_err_fix.content.decode("utf-8"), "idempotency_key")
    r_ok_fix = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(extra_prod.pk, sup_a.pk, [{"number": "FIX-KEY-1", "quantity": "2", "unit_cost": "2.0000", "expiration_date": future_60.isoformat()}], key=preserved_key), "csrfmiddlewaretoken": csrf_tok},
    )
    record(
        "S06R-DOC03AI-EXH-RECUP-02",
        rec_swap1.pk == rec_swap2.pk
        and r_post_disable_replay.status_code == 302
        and r_post_disable_replay.url.endswith(f"/inventario/recepciones/{rec_swap1.pk}/")
        and preserved_key == str(key_fix)
        and r_ok_fix.status_code == 302,
        {"rec_swap": rec_swap1.correlative, "replay_after_disable": r_post_disable_replay.status_code, "preserved_key": preserved_key},
    )

    # Counter exhaustion at 99999999 -> rejects before mutating product/lots
    counter = StockReceiptCounter.objects.get(key="global")
    saved_num = counter.last_number
    counter.last_number = 99999999
    counter.save(update_fields=["last_number"])
    snap_cap = snapshot()
    cap_msg = None
    try:
        register_stock_entry(
            actor=wh1,
            product=extra_prod,
            lots=[LotInput("CAP-FAIL", 1, Decimal("2.0000"), future_60)],
        )
    except ValidationError as exc:
        cap_msg = "; ".join(exc.messages)
    finally:
        StockReceiptCounter.objects.filter(key="global").update(last_number=saved_num)
    record(
        "S06R-COUNTER-MAX-01",
        cap_msg is not None and "agotó" in cap_msg.lower() and snapshot()["lots"] == snap_cap["lots"],
        {"cap_msg": cap_msg},
    )

    # 5. CP-DEC-05-LOTE-ESPACIOS-001 (C-01..C-03 boundaries & midnight Lima)
    # C-01 internal duplicate (" ab  12 " + "AB 12") rejected; (" ab  12 " + "AB12") accepted as 2 lines; legacy "OLD  CODE"
    snap_before_c01 = snapshot()
    r_dup_spaces = c_wh1.post(
        reverse("stock-entry"),
        {
            **make_payload(
                extra_prod.pk,
                "",
                [
                    {"number": " ab  12 ", "quantity": "1", "unit_cost": "2.0000", "expiration_date": future_60.isoformat()},
                    {"number": "AB 12", "quantity": "1", "unit_cost": "2.0000", "expiration_date": future_60.isoformat()},
                ],
            ),
            "csrfmiddlewaretoken": csrf_tok,
        },
    )
    r_distinct_ab12 = c_wh1.post(
        reverse("stock-entry"),
        {
            **make_payload(
                extra_prod.pk,
                "",
                [
                    {"number": " ab  12 ", "quantity": "1", "unit_cost": "2.0000", "expiration_date": future_60.isoformat()},
                    {"number": "AB12", "quantity": "1", "unit_cost": "2.5000", "expiration_date": future_60.isoformat()},
                ],
            ),
            "csrfmiddlewaretoken": csrf_tok,
        },
    )
    # Legacy "OLD  CODE" un-normalized in DB
    leg_lot = Lot.objects.filter(product=legacy_prod).first()
    Lot.objects.filter(pk=leg_lot.pk).update(number="OLD  CODE", number_normalized="OLD  CODE")
    snap_leg_bad = snapshot()
    r_leg_conflict = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(legacy_prod.pk, "", [{"number": " old code ", "quantity": "1", "unit_cost": "2.0000", "expiration_date": future_90.isoformat()}]), "csrfmiddlewaretoken": csrf_tok},
    )
    leg_lot.refresh_from_db()
    record(
        "S06R-DEC05-ESPACIOS-01",
        r_dup_spaces.status_code == 200
        and "AB 12 está repetido" in r_dup_spaces.content.decode("utf-8")
        and r_distinct_ab12.status_code == 302
        and Lot.objects.filter(product=extra_prod, number_normalized="AB 12").count() == 1
        and Lot.objects.filter(product=extra_prod, number_normalized="AB12").count() == 1
        and r_leg_conflict.status_code == 200
        and "ya existe con otro vencimiento" in r_leg_conflict.content.decode("utf-8")
        and leg_lot.number_normalized == "OLD  CODE",
        {"distinct_ab12_status": r_distinct_ab12.status_code, "legacy_kept": leg_lot.number_normalized},
    )

    # C-02 exact field boundary matrix
    max20 = Lot.latest_expiration_date(today)
    over20 = max20 + timedelta(days=1)
    boundary_cases = []

    def test_http_boundary(label, lot_overrides, expect_accept: bool):
        base_row = {"number": "BND-OK", "quantity": "1", "unit_cost": "1.0000", "expiration_date": tomorrow.isoformat()}
        base_row.update(lot_overrides)
        before_s = snapshot()
        resp = c_wh1.post(
            reverse("stock-entry"),
            {**make_payload(legacy_prod.pk, "", [base_row]), "csrfmiddlewaretoken": csrf_tok},
        )
        ok_status = (resp.status_code == 302) if expect_accept else (resp.status_code == 200 and snapshot() == before_s)
        boundary_cases.append({"label": label, "expect_accept": expect_accept, "status": resp.status_code, "ok": ok_status})
        if not ok_status:
            raise AssertionError(f"HTTP boundary failed for {label}: status={resp.status_code}, expect_accept={expect_accept}")

    test_http_boundary("num_empty", {"number": ""}, False)
    test_http_boundary("num_spaces", {"number": "   "}, False)
    test_http_boundary("num_len_1", {"number": "X"}, True)
    test_http_boundary("num_len_64", {"number": "L" * 64}, True)
    test_http_boundary("num_len_65", {"number": "L" * 65}, False)
    test_http_boundary("num_nul", {"number": "A\x00B"}, False)
    test_http_boundary("qty_0", {"quantity": "0"}, False)
    test_http_boundary("qty_neg", {"quantity": "-1"}, False)
    test_http_boundary("qty_1", {"quantity": "1", "number": "Q1"}, True)
    test_http_boundary("qty_999999", {"quantity": "999999", "number": "QMAX"}, True)
    test_http_boundary("qty_1000000", {"quantity": "1000000"}, False)
    test_http_boundary("qty_float", {"quantity": "1.5"}, False)
    test_http_boundary("qty_arabic", {"quantity": "\u0665"}, False)
    test_http_boundary("cost_0", {"unit_cost": "0"}, False)
    test_http_boundary("cost_neg", {"unit_cost": "-1"}, False)
    test_http_boundary("cost_0_0001", {"unit_cost": "0.0001", "number": "CMIN"}, True)
    test_http_boundary("cost_9999999_9999", {"unit_cost": "9999999.9999", "number": "CMAX"}, True)
    test_http_boundary("cost_5dec", {"unit_cost": "1.00001"}, False)
    test_http_boundary("cost_exp", {"unit_cost": "1e2"}, False)
    test_http_boundary("cost_over_max", {"unit_cost": "10000000.0000"}, False)
    test_http_boundary("cost_arabic", {"unit_cost": "\u0665.00"}, False)
    test_http_boundary("exp_today", {"expiration_date": today.isoformat()}, False)
    test_http_boundary("exp_tomorrow", {"expiration_date": tomorrow.isoformat(), "number": "EXP-TMR"}, True)
    test_http_boundary("exp_20y", {"expiration_date": max20.isoformat(), "number": "EXP-20Y"}, True)
    test_http_boundary("exp_20y_plus_1d", {"expiration_date": over20.isoformat()}, False)

    # Check "+1.00" explicitly and bool as int in service
    svc_bool_rejected = False
    try:
        register_stock_entry(actor=wh1, product=legacy_prod, lots=[LotInput("BOOL-1", True, Decimal("1.0000"), tomorrow)])
    except ValidationError:
        svc_bool_rejected = True
    plus_cost_resp = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(legacy_prod.pk, "", [{"number": "PLUS-COST", "quantity": "1", "unit_cost": "+1.00", "expiration_date": tomorrow.isoformat()}]), "csrfmiddlewaretoken": csrf_tok},
    )

    # Lima midnight boundary: 2026-11-15T04:59:59Z = 2026-11-14 23:59:59 Lima vs 05:00:00Z = 2026-11-15 00:00:00 Lima
    utc_before_lima_mid = datetime(2026, 11, 15, 4, 59, 59, tzinfo=dt_timezone.utc)
    utc_at_lima_mid = datetime(2026, 11, 15, 5, 0, 0, tzinfo=dt_timezone.utc)
    target_exp = date(2026, 11, 15)
    with patch("django.utils.timezone.now", return_value=utc_before_lima_mid):
        r_mid_before = c_wh1.post(
            reverse("stock-entry"),
            {**make_payload(legacy_prod.pk, "", [{"number": "MID-LIMA-1", "quantity": "1", "unit_cost": "1.0000", "expiration_date": target_exp.isoformat()}]), "csrfmiddlewaretoken": csrf_tok},
        )
    with patch("django.utils.timezone.now", return_value=utc_at_lima_mid):
        r_mid_at = c_wh1.post(
            reverse("stock-entry"),
            {**make_payload(legacy_prod.pk, "", [{"number": "MID-LIMA-2", "quantity": "1", "unit_cost": "1.0000", "expiration_date": target_exp.isoformat()}]), "csrfmiddlewaretoken": csrf_tok},
        )
    leap_check = (
        Lot.latest_expiration_date(date(2080, 2, 29)) == date(2100, 2, 28)
        and Lot.latest_expiration_date(date(2024, 2, 29)) == date(2044, 2, 29)
    )
    record(
        "S06R-DEC05-FRONTERAS-02",
        svc_bool_rejected
        and r_mid_before.status_code == 302
        and r_mid_at.status_code == 200
        and "posterior a hoy en Lima" in r_mid_at.content.decode("utf-8")
        and leap_check,
        {
            "boundary_count": len(boundary_cases),
            "svc_bool_rejected": svc_bool_rejected,
            "http_plus_sign_unit_cost_status": plus_cost_resp.status_code,
            "mid_before_lima_status": r_mid_before.status_code,
            "mid_at_lima_status": r_mid_at.status_code,
            "leap_check": leap_check,
        },
    )

    # C-03 & Formset edge cases: all blank, blank card 1 + valid card 2 (Django min_num=1 pins index 0), valid card 1 + blank rest, partial card 2, tampered management_form, 5 valid lots (>4 cards)
    snap_before_formset = snapshot()
    r_all_blank = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(legacy_prod.pk, "", [{}, {}, {}, {}]), "csrfmiddlewaretoken": csrf_tok},
    )
    all_blank_alerts = extract_role_alerts(r_all_blank.content.decode("utf-8"))
    r_blank_c1_valid_c2 = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(legacy_prod.pk, "", [{}, {"number": "SPARSE-C2", "quantity": "1", "unit_cost": "2.0000", "expiration_date": tomorrow.isoformat()}, {}, {}]), "csrfmiddlewaretoken": csrf_tok},
    )
    r_partial_card2 = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(legacy_prod.pk, "", [{"number": "PART-C1", "quantity": "1", "unit_cost": "2.0000", "expiration_date": tomorrow.isoformat()}, {"number": "PARTIAL-C2"}, {}, {}]), "csrfmiddlewaretoken": csrf_tok},
    )
    r_tamper_empty = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(legacy_prod.pk, "", [{"number": "T1", "quantity": "1", "unit_cost": "1.0000", "expiration_date": tomorrow.isoformat()}], total_forms=""), "csrfmiddlewaretoken": csrf_tok},
    )
    r_tamper_neg = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(legacy_prod.pk, "", [{"number": "T2", "quantity": "1", "unit_cost": "1.0000", "expiration_date": tomorrow.isoformat()}], total_forms="-1"), "csrfmiddlewaretoken": csrf_tok},
    )
    snap_after_invalid_formsets = snapshot()
    r_sparse_c1_valid = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(legacy_prod.pk, "", [{"number": "SPARSE-C1", "quantity": "1", "unit_cost": "2.0000", "expiration_date": tomorrow.isoformat()}, {}, {}, {}]), "csrfmiddlewaretoken": csrf_tok},
    )
    sparse_rec_id = r_sparse_c1_valid.url.strip("/").split("/")[-1]
    sparse_lines_count = StockReceiptLine.objects.filter(receipt_id=sparse_rec_id).count()
    r_5_lots = c_wh1.post(
        reverse("stock-entry"),
        {
            **make_payload(
                legacy_prod.pk,
                "",
                [{"number": f"FIVE-{idx}", "quantity": "1", "unit_cost": "2.0000", "expiration_date": tomorrow.isoformat()} for idx in range(1, 6)],
            ),
            "csrfmiddlewaretoken": csrf_tok,
        },
    )
    five_rec_id = r_5_lots.url.strip("/").split("/")[-1]
    five_lines_count = StockReceiptLine.objects.filter(receipt_id=five_rec_id).count()

    # Inactive supplier sentinel check
    snap_before_sup = snapshot()
    r_sup_inact = c_wh1.post(
        reverse("stock-entry"),
        {**make_payload(legacy_prod.pk, sup_off.pk, [{"number": "SUP-OFF-1", "quantity": "1", "unit_cost": "2.0000", "expiration_date": tomorrow.isoformat()}]), "csrfmiddlewaretoken": csrf_tok},
    )
    sup_off_text = r_sup_inact.content.decode("utf-8")
    record(
        "S06R-DEC05-FORMSET-03",
        r_all_blank.status_code == 200
        and any("1 formulario como mínimo" in a for a in all_blank_alerts)
        and r_blank_c1_valid_c2.status_code == 200
        and r_partial_card2.status_code == 200
        and r_tamper_empty.status_code == 200
        and r_tamper_neg.status_code == 200
        and snap_after_invalid_formsets == snap_before_formset
        and r_sparse_c1_valid.status_code == 302
        and sparse_lines_count == 1
        and r_5_lots.status_code == 302
        and five_lines_count == 5
        and r_sup_inact.status_code == 200
        and snapshot() == snap_before_sup
        and f"__inactive__:{sup_off.pk}" in sup_off_text,
        {
            "all_blank_alerts": all_blank_alerts,
            "blank_c1_valid_c2": r_blank_c1_valid_c2.status_code,
            "partial_card2": r_partial_card2.status_code,
            "tamper_empty": r_tamper_empty.status_code,
            "tamper_neg": r_tamper_neg.status_code,
            "sparse_c1_valid": r_sparse_c1_valid.status_code,
            "five_lots_lines": five_lines_count,
        },
    )

    # 6. CT-COHERENCIA-UI & security header check + VENDEDOR receipt cost isolation
    r_sel_sale_receipt = c_sel.get(reverse("sales-receipt", args=(sale2.pk,)))
    sel_receipt_text = r_sel_sale_receipt.content.decode("utf-8")
    r_adm_kardex = c_adm.get(reverse("product-movements", args=(leche.pk,)))
    adm_kardex_text = r_adm_kardex.content.decode("utf-8")
    record(
        "S06R-COHERENCIA-01",
        "no-store" in (r_get_entry.headers.get("Cache-Control") or "")
        and r_get_entry.headers.get("X-Frame-Options") == "DENY"
        and r_get_entry.headers.get("X-Content-Type-Options") == "nosniff"
        and "4.6666" not in sel_receipt_text
        and "4,6666" not in sel_receipt_text
        and "4.0714" not in sel_receipt_text
        and "4,0714" not in sel_receipt_text
        and "R-00000001" in adm_kardex_text
        and "R-00000002" in adm_kardex_text,
        {
            "entry_headers": dict(r_get_entry.headers),
            "seller_receipt_status": r_sel_sale_receipt.status_code,
            "kardex_shows_receipts": ("R-00000001" in adm_kardex_text and "R-00000002" in adm_kardex_text),
        },
    )

    end_hashes = {k: (digest(ROOT / k) if (ROOT / k).exists() else None) == v for k, v in start_hashes.items()}
    summary = {
        "stamp_utc": stamp,
        "cases_total": len(results),
        "cases_passed": sum(1 for r in results if r["ok"]),
        "results": results,
        "protected_unchanged": all(end_hashes.values()),
    }
    write_json(out_dir / "report.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0 if (summary["cases_passed"] == summary["cases_total"] and summary["protected_unchanged"]) else 1


def run_browser() -> int:
    start_hashes = protected_hashes()
    run_dir, out_dir, stamp = make_run_dir("browser")
    os.environ.update(AUDIT06_RUN_DIR=str(run_dir), AUDIT06_OUT=str(out_dir), AUDIT06_PYTHON=sys.executable)
    result = {
        "action": "browser",
        "run": run_dir.name,
        "started_utc": stamp,
        "evidence": str(out_dir.relative_to(ROOT)),
    }
    server = None
    port = 0
    try:
        setup(default_cookies=False)
        prepare_empty_migrated_db()
        prepare_stage06_fixtures(run_dir, out_dir)
        write_json(out_dir / "orm-initial.json", snapshot())

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        os.environ["AUDIT06_PORT"] = str(port)
        server = subprocess.Popen(
            [sys.executable, __file__, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(100):
            with socket.socket() as sock:
                if sock.connect_ex(("127.0.0.1", port)) == 0:
                    break
            if server.poll() is not None:
                raise RuntimeError("Django runserver terminated early")
            time.sleep(0.1)

        child = subprocess.run(
            ["node", str(SUPPORT / "audit06_reval_browser.cjs")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=240,
        )
        result.update(browser_exit=child.returncode, browser_output=child.stdout, browser_error=child.stderr)
        write_json(out_dir / "orm-final.json", snapshot())
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
            result["port_closed"] = False
            for _ in range(50):
                with socket.socket() as sock:
                    if sock.connect_ex(("127.0.0.1", port)) != 0:
                        result["port_closed"] = True
                        break
                time.sleep(0.1)
        result["protected_unchanged"] = {k: (digest(ROOT / k) if (ROOT / k).exists() else None) == v for k, v in start_hashes.items()}
        result["original_sha256"] = digest(APP / "r1_pmv.sqlite3")
        result["finished_utc"] = datetime.now(dt_timezone.utc).isoformat()
        write_json(out_dir / "result.json", result)
        print(
            json.dumps(
                {
                    "evidence": result["evidence"],
                    "browser_exit": result.get("browser_exit"),
                    "port_closed": result.get("port_closed"),
                    "protected_unchanged": all(result["protected_unchanged"].values()),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    if result.get("browser_exit", 1) != 0 or not result.get("port_closed") or not all(result["protected_unchanged"].values()):
        return 1
    return 0


def run_checks() -> int:
    start_hashes = protected_hashes()
    run_dir, out_dir, stamp = make_run_dir("checks")
    os.environ.update(AUDIT06_RUN_DIR=str(run_dir), AUDIT06_OUT=str(out_dir), AUDIT06_DEFAULT_COOKIES="1")
    setup(default_cookies=True)
    from django.core.management import execute_from_command_line

    buf = io.StringIO()
    exit_code = 0
    old_cwd = Path.cwd()
    try:
        os.chdir(APP)
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            for argv in (["manage.py", "check"], ["manage.py", "makemigrations", "--check", "--dry-run"]):
                try:
                    execute_from_command_line(argv)
                except SystemExit as exc:
                    exit_code = max(exit_code, int(exc.code or 0))
    finally:
        os.chdir(old_cwd)
    out_text = buf.getvalue()
    (out_dir / "checks.txt").write_text(out_text, encoding="utf-8")
    end_hashes = {k: (digest(ROOT / k) if (ROOT / k).exists() else None) == v for k, v in start_hashes.items()}
    summary = {
        "stamp_utc": stamp,
        "exit_code": exit_code,
        "output": out_text,
        "protected_unchanged": all(end_hashes.values()),
    }
    write_json(out_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if (exit_code == 0 and all(end_hashes.values())) else 1


def run_tests(targets: list[str]) -> int:
    start_hashes = protected_hashes()
    run_dir, out_dir, stamp = make_run_dir("tests")
    os.environ.update(AUDIT06_RUN_DIR=str(run_dir), AUDIT06_OUT=str(out_dir), AUDIT06_DEFAULT_COOKIES="1")
    setup(default_cookies=True)
    from django.core.management import execute_from_command_line

    buf = io.StringIO()
    argv = ["manage.py", "test", *targets, "-v", "2"]
    exit_code = 0
    started = time.monotonic()
    old_cwd = Path.cwd()
    try:
        os.chdir(APP)
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            try:
                execute_from_command_line(argv)
            except SystemExit as exc:
                exit_code = int(exc.code or 0)
    finally:
        os.chdir(old_cwd)
    duration = round(time.monotonic() - started, 3)
    output_text = buf.getvalue()
    (out_dir / "test_output.txt").write_text(output_text, encoding="utf-8")
    end_hashes = {k: (digest(ROOT / k) if (ROOT / k).exists() else None) == v for k, v in start_hashes.items()}
    summary = {
        "stamp_utc": stamp,
        "targets": targets,
        "exit_code": exit_code,
        "duration_s": duration,
        "evidence_txt": str((out_dir / "test_output.txt").relative_to(ROOT)),
        "protected_unchanged": all(end_hashes.values()),
        "tail": output_text.splitlines()[-25:],
    }
    write_json(out_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if (exit_code == 0 and all(end_hashes.values())) else 1


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: audit06_reval_run.py [serve|snapshot|checks|tests ...|server|browser]")
    action = sys.argv[1]
    if action == "serve":
        setup(default_cookies=False)
        from django.core.management import execute_from_command_line

        execute_from_command_line(["manage.py", "runserver", f"127.0.0.1:{os.environ['AUDIT06_PORT']}", "--noreload", "--insecure"])
        return 0
    if action == "snapshot":
        setup(default_cookies=False)
        print(json.dumps(snapshot(), ensure_ascii=False, default=str))
        return 0
    if action == "checks":
        return run_checks()
    if action == "tests":
        targets = sys.argv[2:] or ["inventory.test_audit06_stock_entry"]
        return run_tests(targets)
    if action == "server":
        return run_server_suite()
    if action == "browser":
        return run_browser()
    raise SystemExit(f"Unknown action: {action}")


if __name__ == "__main__":
    raise SystemExit(main())
