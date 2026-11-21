"""Stage 03 Sublote B deepening runner against current post-02-E build (read-only on product).

Covers:
1. Full 12-route x method x role Cache-Control & security header matrix (reconciles 15-A).
2. UNCLASSIFIED legacy edit transitions, inactive product/category cross-module effects
   (inventory initial load, stock entry, write-off, physical adjustment, sales draft/checkout/remove).
3. Extreme boundaries, SQL wildcards (%, _, \\, \\x00), NFC/NFD, Turkish dotless i, zero-width chars,
   GTIN 8/11/12/13/14-bad-prefix, price/minimum_stock validation messages.
4. Scalability benchmark on /productos/ & /productos/categorias/ (500 SKUs, 1,500 lots, SQL count + HTML bytes).
5. seed_pmv + seed_demo + reset_demo_db isolation checks (confirming PROP-15-OPS-DEMO-01 impact).
6. Real Chromium 1366x900 + 390x844 inspection of sidebar active states, topbar h1, mobile clipping/overflow.
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
import time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

SUPPORT = Path(__file__).resolve().parent
RESULTS = SUPPORT.parent
ROOT = RESULTS.parent.parent
APP = ROOT / "r1-pmv"
sys.path[:0] = [str(APP), str(SUPPORT)]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(65536):
            h.update(chunk)
    return h.hexdigest()


def source_manifest_hash() -> dict:
    files = sorted(
        p for p in APP.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and ".venv" not in p.parts
        and "node_modules" not in p.parts
        and ".pytest_cache" not in p.parts
        and p.suffix not in {".sqlite3", ".pyc"}
    )
    lines = [f"{digest(p)}  {p.relative_to(APP).as_posix()}" for p in files]
    manifest = hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()
    return {"source_count": len(files), "source_manifest": manifest}


def setup_django() -> None:
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit03_reval_b_settings"
    import django

    django.setup()


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "serve":
        setup_django()
        from django.core.management import execute_from_command_line

        execute_from_command_line(
            ["manage.py", "runserver", "127.0.0.1:" + os.environ["AUDIT03_REVAL_B_PORT"], "--noreload", "--insecure"]
        )
        return

    from datetime import datetime, timezone

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)
    run_dir = RESULTS / "datos" / f"03-REVAL-B-{stamp}"
    out_dir = RESULTS / "evidencias" / f"03-REVAL-B-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "marker.json").write_text(json.dumps({"run": run_dir.name, "stage": "03-REVAL-B"}), encoding="utf-8")
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")
    os.environ["AUDIT03_REVAL_B_RUN_DIR"] = str(run_dir)
    os.environ["AUDIT03_REVAL_B_OUT_DIR"] = str(out_dir)

    protected = [
        *(
            p for p in (RESULTS / "datos").rglob("*.sqlite3")
            if p.parent != run_dir and p.parent.name.startswith(("03-", "etapa03"))
        ),
        ROOT / "08_Historias_de_Usuario.md",
        *sorted((APP / "catalog").rglob("*.py")),
    ]
    external_watch = [
        *(APP).glob("*.sqlite3"),
        ROOT / "07_Reglas_de_Negocio.md",
        ROOT / "09_Product_Backlog.md",
        ROOT / "03_Matriz_de_Trazabilidad_y_Pruebas.md",
    ]
    hashes_before = {str(p.relative_to(ROOT)): digest(p) for p in protected if p.exists()}
    ext_before = {str(p.relative_to(ROOT)): digest(p) for p in external_watch if p.exists()}
    manifest_before = source_manifest_hash()

    setup_django()

    from django.core.exceptions import ValidationError
    from django.core.management import call_command
    from django.db import connection
    from django.test import Client
    from django.test.utils import CaptureQueriesContext
    from django.utils import timezone as dj_tz

    from cash.models import CashRegister
    from cash.services import open_cash_shift
    from catalog.models import Category, Product, ProductBarcodeKey
    from catalog.services import (
        create_category,
        product_edit_snapshot,
        register_canned_product,
        toggle_category_status,
        toggle_product_availability,
        update_product,
    )
    from identity.models import Account, Role
    from inventory.models import InitialInventoryLoad, InitialLoadLine, Lot
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        register_physical_adjustment,
        register_stock_entry,
        write_off_stock,
    )
    from sales.models import Sale, SaleDraft, SaleDraftLine
    from sales.services import (
        add_product_to_draft,
        checkout_sale,
        remove_draft_line,
        update_draft_line,
    )

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    roles = {}
    for code, name in [
        (Role.Code.ADMIN, "Administrador"),
        (Role.Code.WAREHOUSE, "Almacenero"),
        (Role.Code.SELLER, "Vendedor"),
    ]:
        roles[code], _ = Role.objects.get_or_create(code=code, defaults={"name": name})

    creds = {}
    accounts = {}
    for alias, email, role_code, disp in [
        ("admin", "admin_b@reval03.invalid", Role.Code.ADMIN, "Admin B"),
        ("warehouse", "wh_b@reval03.invalid", Role.Code.WAREHOUSE, "Almacenero B"),
        ("seller", "sel_b@reval03.invalid", Role.Code.SELLER, "Vendedor B"),
    ]:
        pw = "Test03B-" + secrets.token_urlsafe(12) + "A1"
        acc = Account.objects.create_user(email, pw, display_name=disp, role=roles[role_code], is_active=True)
        accounts[alias] = acc
        creds[alias] = {"id": str(acc.pk), "email": email, "password": pw, "role": role_code}

    (run_dir / ".credentials.json").write_text(json.dumps(creds, indent=2), encoding="utf-8")
    CashRegister.objects.create(code="CAJA-01", is_active=True)
    open_cash_shift(actor=accounts["seller"], opening_amount=Decimal("100.00"))

    def login_client(alias: str) -> Client:
        c = Client()
        resp = c.post("/", {"email": creds[alias]["email"], "password": creds[alias]["password"]}, follow=False)
        assert resp.status_code == 302, f"Login failed for {alias}: {resp.status_code}"
        return c

    c_anon = Client()
    c_admin = login_client("admin")
    c_wh = login_client("warehouse")
    c_sel = login_client("seller")

    report: dict = {
        "started_utc": stamp,
        "build_manifest_before": manifest_before,
        "cache_matrix": [],
        "cache_summary": {},
        "unclassified_probes": {},
        "lifecycle_cross_module": {},
        "validation_and_search_probes": {},
        "scale_benchmark": {},
        "seed_demo_probe": {},
        "chrome_sublote_b": {},
    }

    # ── 1. Cache-Control & perimeter matrix across ALL 12 catalog URLs ─────────
    cat0 = create_category(actor=accounts["admin"], name="Lácteos Cache")
    prod0 = register_canned_product(
        actor=accounts["admin"],
        name="Leche Cache 1L",
        barcode="CACHE-001",
        barcode_type="INTERNAL",
        category=cat0,
        unit="UND",
        sale_price=Decimal("4.50"),
        minimum_stock=5,
    )
    snap0 = json.dumps(product_edit_snapshot(prod0))
    from django.core import signing
    signed_snap0 = signing.dumps(product_edit_snapshot(prod0), salt="catalog.product-edit")

    # Wait: reuse cat0/prod0 for 12-route cache header scan
    bad_uuid = "00000000-0000-0000-0000-000000000000"
    specs = [
        ("category-list", "GET", "/productos/categorias/", {}),
        ("category-create", "GET", "/productos/categorias/nueva/", {}),
        ("category-create", "POST_invalid", "/productos/categorias/nueva/", {"name": "   "}),
        ("category-create", "POST_valid_302", "/productos/categorias/nueva/", {"name": "Bebidas Cache"}),
        ("category-state-confirm", "GET", f"/productos/categorias/{cat0.pk}/estado/confirmar/", {}),
        ("category-state-confirm", "GET_stale_409", f"/productos/categorias/{cat0.pk}/estado/confirmar/?is_active=false&state_version=99", {}),
        ("category-state-confirm", "GET_bad_404", f"/productos/categorias/{bad_uuid}/estado/confirmar/", {}),
        ("category-toggle", "GET_405", f"/productos/categorias/{cat0.pk}/estado/", {}),
        ("category-toggle", "POST_invalid_400", f"/productos/categorias/{cat0.pk}/estado/", {"is_active": "false", "state_version": "0"}),
        ("category-toggle", "POST_valid_302", f"/productos/categorias/{cat0.pk}/estado/", {"is_active": "false", "state_version": str(cat0.state_version), "confirm": "yes"}),
        ("category-toggle", "POST_bad_404", f"/productos/categorias/{bad_uuid}/estado/", {}),
        ("product-list", "GET", "/productos/", {}),
        ("product-list", "GET_null_q", "/productos/?q=abc%00def", {}),
        ("product-entry", "GET", "/productos/nuevo/", {}),
        ("product-entry", "POST_invalid", "/productos/nuevo/", {"name": ""}),
        ("product-entry", "POST_valid_302", "/productos/nuevo/", {
            "name": "Producto Cache Dos", "barcode_type": "INTERNAL", "barcode": "CACHE-002",
            "category": str(Category.objects.get(name="Bebidas Cache").pk), "unit": "UND",
            "sale_price": "7.50", "minimum_stock": "",
        }),
        ("product-created", "GET", f"/productos/{prod0.pk}/registrado/", {}),
        ("product-created-alias", "GET", f"/productos/registrado/{prod0.pk}/", {}),
        ("product-created", "GET_bad_404", f"/productos/{bad_uuid}/registrado/", {}),
        ("product-barcode-check", "GET_valid", "/productos/codigos/comprobar/?barcode=CACHE-NEW&barcode_type=INTERNAL", {}),
        ("product-barcode-check", "GET_bad_400", "/productos/codigos/comprobar/?barcode=BAD!KEY&barcode_type=INTERNAL", {}),
        ("product-edit", "GET", f"/productos/{prod0.pk}/editar/", {}),
        ("product-edit", "POST_invalid", f"/productos/{prod0.pk}/editar/", {"name": "", "edit_snapshot": signed_snap0}),
        ("product-edit", "POST_valid_302", f"/productos/{prod0.pk}/editar/", {
            "name": "Leche Cache 1L", "barcode_type": "INTERNAL", "barcode": "CACHE-001",
            "category": "", "sale_price": "4.80", "minimum_stock": "6", "edit_snapshot": signed_snap0,
        }),
        ("product-edit", "GET_bad_404", f"/productos/{bad_uuid}/editar/", {}),
        ("product-toggle", "GET_405", f"/productos/{prod0.pk}/disponibilidad/", {}),
        ("product-toggle", "POST_invalid_302", f"/productos/{prod0.pk}/disponibilidad/", {"is_active": "maybe"}),
        ("product-toggle", "POST_valid_302", f"/productos/{prod0.pk}/disponibilidad/", {"is_active": "false"}),
        ("product-expirations", "GET", "/productos/vencimientos/", {}),
    ]

    for role_name, client in [("ADMIN", c_admin), ("ALMACENERO", c_wh), ("VENDEDOR", c_sel), ("ANON", c_anon)]:
        for route_name, case_kind, path, data in specs:
            if role_name != "ADMIN" and ("valid_302" in case_kind or "bad_404" in case_kind or "invalid" in case_kind or "stale" in case_kind or "null_q" in case_kind):
                # For non-ADMIN roles, test clean base GET/POST once per route to check 403/302/200 headers
                continue
            method = "POST" if case_kind.startswith("POST") else "GET"
            if role_name != "ADMIN" and route_name in {"category-toggle", "product-toggle"}:
                method = "POST"
            resp = client.post(path, data, follow=False) if method == "POST" else client.get(path, follow=False)
            cc = resp.get("Cache-Control", "")
            report["cache_matrix"].append({
                "role": role_name,
                "route": route_name,
                "case": case_kind,
                "method": method,
                "path": path.split("?")[0],
                "status": resp.status_code,
                "cache_control": cc,
                "has_no_store": "no-store" in cc.lower(),
                "pragma": resp.get("Pragma", ""),
                "expires": resp.get("Expires", ""),
                "x_content_type_options": resp.get("X-Content-Type-Options", ""),
            })

    # Re-enable cat0 and prod0 cleanly
    cat0.refresh_from_db()
    toggle_category_status(actor=accounts["admin"], category=cat0, is_active=True, expected_version=cat0.state_version)
    prod0.refresh_from_db()
    toggle_product_availability(actor=accounts["admin"], product=prod0, is_active=True)

    admin_missing_no_store = [
        f"{x['route']}:{x['case']}({x['status']})"
        for x in report["cache_matrix"]
        if x["role"] == "ADMIN" and x["status"] in (200, 302) and not x["has_no_store"]
    ]
    # Also check GET/POST standard pair count (reconcile exact 9 in 15-A)
    admin_get_post_missing = [
        f"{x['route']}:{x['method']}({x['status']})"
        for x in report["cache_matrix"]
        if x["role"] == "ADMIN" and x["case"] in {"GET", "POST_valid_302"} and not x["has_no_store"]
    ]
    denied_missing = [
        f"{x['role']}:{x['route']}:{x['method']}({x['status']})"
        for x in report["cache_matrix"]
        if x["status"] in (403, 405) and not x["has_no_store"]
    ]
    report["cache_summary"] = {
        "total_probes": len(report["cache_matrix"]),
        "admin_200_302_missing_no_store": admin_missing_no_store,
        "admin_get_post_standard_missing_no_store": admin_get_post_missing,
        "admin_get_post_standard_missing_count": len(admin_get_post_missing),
        "denied_403_405_missing_no_store": denied_missing,
        "denied_403_405_missing_count": len(denied_missing),
    }

    # ── 2. UNCLASSIFIED legacy workflow & transitions ─────────────────────────
    leg1 = Product.objects.create(
        category=cat0, name="Legado Interno Uno", barcode="000777",
        barcode_type=Product.BarcodeType.UNCLASSIFIED, unit="UND",
        sale_price=Decimal("3.20"), minimum_stock=5,
    )
    leg2 = Product.objects.create(
        category=cat0, name="Legado GTIN Dos", barcode="4006381333931",
        barcode_type=Product.BarcodeType.UNCLASSIFIED, unit="UND",
        sale_price=Decimal("6.50"), minimum_stock=5,
    )
    leg1_keys_before = list(ProductBarcodeKey.objects.filter(product=leg1).values_list("reading_key", flat=True))
    leg2_keys_before = list(ProductBarcodeKey.objects.filter(product=leg2).values_list("reading_key", flat=True))
    # Edit leg1 keeping UNCLASSIFIED (e.g., via GET/POST on product-edit)
    edit_get1 = c_admin.get(f"/productos/{leg1.pk}/editar/")
    html_leg1_get = edit_get1.content.decode("utf-8")
    has_unclassified_opt_before = 'value="UNCLASSIFIED"' in html_leg1_get
    snap_leg1 = signing.dumps(product_edit_snapshot(leg1), salt="catalog.product-edit")
    resp_keep_uncl = c_admin.post(f"/productos/{leg1.pk}/editar/", {
        "name": leg1.name, "barcode_type": "", "barcode": leg1.barcode,
        "category": str(cat0.pk), "sale_price": "3.40", "minimum_stock": "5",
        "edit_snapshot": snap_leg1,
    }, follow=False)
    leg1.refresh_from_db()
    # Now reclassify leg1 -> INTERNAL
    snap_leg1_v2 = signing.dumps(product_edit_snapshot(leg1), salt="catalog.product-edit")
    resp_reclass_int = c_admin.post(f"/productos/{leg1.pk}/editar/", {
        "name": leg1.name, "barcode_type": "INTERNAL", "barcode": "000777",
        "category": "", "sale_price": "3.50", "minimum_stock": "5",
        "edit_snapshot": snap_leg1_v2,
    }, follow=False)
    leg1.refresh_from_db()
    has_unclassified_opt_after = 'value="UNCLASSIFIED"' in c_admin.get(f"/productos/{leg1.pk}/editar/").content.decode("utf-8")

    # Try creating another GTIN product with 04006381333931 colliding with leg2's UNCLASSIFIED key (if UNCLASSIFIED indexes GTIN reading keys!)
    dup_uncl_err = None
    try:
        register_canned_product(
            actor=accounts["admin"], name="Choque Legado GTIN", barcode="04006381333931",
            barcode_type="GTIN", category=cat0, unit="UND", sale_price=Decimal("7.00"), minimum_stock=5,
        )
    except ValidationError as exc:
        dup_uncl_err = exc.message_dict if hasattr(exc, "message_dict") else exc.messages

    # Try reclassifying leg2 -> GTIN with invalid check digit vs valid 0-padded 14
    snap_leg2 = signing.dumps(product_edit_snapshot(leg2), salt="catalog.product-edit")
    resp_leg2_bad_gtin = c_admin.post(f"/productos/{leg2.pk}/editar/", {
        "name": leg2.name, "barcode_type": "GTIN", "barcode": "4006381333932",
        "category": str(cat0.pk), "sale_price": "6.50", "minimum_stock": "5",
        "edit_snapshot": snap_leg2,
    }, follow=False)
    resp_leg2_good_gtin = c_admin.post(f"/productos/{leg2.pk}/editar/", {
        "name": leg2.name, "barcode_type": "GTIN", "barcode": "04006381333931",
        "category": str(cat0.pk), "sale_price": "6.50", "minimum_stock": "5",
        "edit_snapshot": snap_leg2,
    }, follow=False)
    leg2.refresh_from_db()
    report["unclassified_probes"] = {
        "leg1_keys_before": leg1_keys_before,
        "leg2_keys_before": leg2_keys_before,
        "has_unclassified_option_before_reclass": has_unclassified_opt_before,
        "keep_unclassified_status": resp_keep_uncl.status_code,
        "keep_unclassified_barcode_type": leg1.barcode_type if resp_keep_uncl.status_code == 302 else None,
        "reclass_internal_status": resp_reclass_int.status_code,
        "reclass_internal_barcode_type": leg1.barcode_type,
        "has_unclassified_option_after_internal": has_unclassified_opt_after,
        "new_gtin_14_collides_with_unclassified_13": dup_uncl_err,
        "leg2_bad_gtin_status": resp_leg2_bad_gtin.status_code,
        "leg2_bad_gtin_errors": resp_leg2_bad_gtin.context["form"].errors.get_json_data() if resp_leg2_bad_gtin.status_code == 200 else None,
        "leg2_good_14padded_gtin_status": resp_leg2_good_gtin.status_code,
        "leg2_after_gtin_barcode": leg2.barcode,
        "leg2_keys_after": list(ProductBarcodeKey.objects.filter(product=leg2).values_list("reading_key", flat=True)),
    }

    # ── 3. Category & Product deactivation cross-module lifecycle + uniqueness ──
    cat_cycle = create_category(actor=accounts["admin"], name="Abarrotes Ciclo")
    cat_dest = create_category(actor=accounts["admin"], name="Destino Activo")
    p_act = register_canned_product(
        actor=accounts["admin"], name="Arroz Ciclo 1Kg", barcode="CICLO-001", barcode_type="INTERNAL",
        category=cat_cycle, unit="UND", sale_price=Decimal("5.00"), minimum_stock=10,
    )
    p_inact = register_canned_product(
        actor=accounts["admin"], name="Fideo Inactivo 500g", barcode="CICLO-002", barcode_type="INTERNAL",
        category=cat_cycle, unit="UND", sale_price=Decimal("3.00"), minimum_stock=5,
    )
    p_noload = register_canned_product(
        actor=accounts["admin"], name="Avena Sin Carga 200g", barcode="CICLO-003", barcode_type="INTERNAL",
        category=cat_cycle, unit="UND", sale_price=Decimal("2.50"), minimum_stock=5,
    )
    today = dj_tz.localdate()
    confirm_initial_load(actor=accounts["warehouse"], product=p_act, lots=[
        LotInput("LOT-VIG", 8, Decimal("3.00"), today + timedelta(days=60)),
        LotInput("LOT-EXP", 2, Decimal("3.00"), today + timedelta(days=1)),  # will NOT expire yet, let's also add an already-expired lot directly via Lot to test writeoff
    ])
    Lot.objects.create(
        product=p_act, responsible=accounts["warehouse"], number="LOT-YA-VENC",
        initial_quantity=3, available_quantity=3, unit_cost=Decimal("3.00"), expiration_date=today - timedelta(days=1),
    )
    confirm_initial_load(actor=accounts["warehouse"], product=p_inact, lots=[
        LotInput("LOT-IN-1", 12, Decimal("2.00"), today + timedelta(days=60)),
    ])
    toggle_product_availability(actor=accounts["admin"], product=p_inact, is_active=False)

    # Inactive product uniqueness (name & barcode blocked)
    inactive_name_err = None
    try:
        register_canned_product(
            actor=accounts["admin"], name="  fideo   inactivo  500G ", barcode="NEW-999",
            barcode_type="INTERNAL", category=cat_dest, unit="UND", sale_price=Decimal("3.00"), minimum_stock=5,
        )
    except ValidationError as exc:
        inactive_name_err = exc.messages
    inactive_bc_err = None
    try:
        register_canned_product(
            actor=accounts["admin"], name="Otro Nombre Distinto", barcode="ciclo-002",
            barcode_type="INTERNAL", category=cat_dest, unit="UND", sale_price=Decimal("3.00"), minimum_stock=5,
        )
    except ValidationError as exc:
        inactive_bc_err = exc.messages

    # Seller adds p_act to draft while cat_cycle is still active
    draft = add_product_to_draft(actor=accounts["seller"], product_id=p_act.pk, quantity=2)
    draft_line = SaleDraftLine.objects.get(draft=draft, product=p_act)

    # Inspect category confirmation GET screen
    confirm_get = c_admin.get(f"/productos/categorias/{cat_cycle.pk}/estado/confirmar/")
    # Deactivate cat_cycle
    toggle_category_status(actor=accounts["admin"], category=cat_cycle, is_active=False, expected_version=cat_cycle.state_version)
    cat_cycle.refresh_from_db()

    # Check /productos/ badges & stock_overview & inventory selects & inventory services
    prod_list_html = c_admin.get("/productos/?q=Ciclo").content.decode("utf-8")
    load_form_html = c_wh.get("/inventario/carga-inicial/").content.decode("utf-8")
    entry_form_html = c_wh.get("/inventario/entrada/").content.decode("utf-8")
    overview_ctx = c_wh.get("/inventario/stock/").context
    low_stock_ids = [str(p.pk) for p in overview_ctx["low_stock"]]

    def cap_err(fn):
        try:
            fn()
            return {"ok": True}
        except ValidationError as exc:
            return {"ok": False, "messages": exc.messages}

    init_blocked = cap_err(lambda: confirm_initial_load(
        actor=accounts["warehouse"], product=p_noload,
        lots=[LotInput("L-N1", 5, Decimal("1.00"), today + timedelta(days=30))],
    ))
    entry_blocked = cap_err(lambda: register_stock_entry(
        actor=accounts["warehouse"], product=p_act,
        lots=[LotInput("L-E1", 5, Decimal("3.00"), today + timedelta(days=30))],
    ))
    wo_exp_res = cap_err(lambda: write_off_stock(
        actor=accounts["warehouse"], lot=Lot.objects.get(product=p_act, number="LOT-YA-VENC"),
        quantity=1, reason="VENCIMIENTO",
    ))
    adj_res = cap_err(lambda: register_physical_adjustment(
        actor=accounts["admin"], lot=Lot.objects.get(product=p_act, number="LOT-VIG"),
        delta=-1, reason="Conteo con categoría desactivada",
    ))

    # Sales behavior while cat_cycle is inactive
    pos_search_html = c_sel.get("/ventas/?query=Arroz+Ciclo").content.decode("utf-8")
    pos_draft_banner_ok = "Arroz Ciclo 1Kg" in pos_search_html
    upd_blocked = cap_err(lambda: update_draft_line(actor=accounts["seller"], line_id=draft_line.pk, quantity=3))
    chk_blocked = cap_err(lambda: checkout_sale(
        actor=accounts["seller"], draft_id=draft.pk, cash_received=Decimal("20.00"), idempotency_key=uuid4(),
    ))
    # Can seller REMOVE the blocked line via /ventas/lineas/<id>/quitar/?
    rm_resp = c_sel.post(f"/ventas/lineas/{draft_line.pk}/quitar/", follow=False)
    draft.refresh_from_db()

    # Catalog update_product behavior with inactive category
    edit_keep_cat = cap_err(lambda: update_product(
        actor=accounts["admin"], product=p_act, name=p_act.name, barcode=p_act.barcode,
        sale_price=Decimal("5.20"), minimum_stock=10, category=cat_cycle,
        expected_snapshot=product_edit_snapshot(p_act),
    ))
    move_into_inact_cat = cap_err(lambda: update_product(
        actor=accounts["admin"], product=prod0, name=prod0.name, barcode=prod0.barcode,
        sale_price=prod0.sale_price, minimum_stock=prod0.minimum_stock, category=cat_cycle,
        expected_snapshot=product_edit_snapshot(prod0),
    ))

    # Reactivate cat_cycle -> p_act active again, p_inact stays individually False
    toggle_category_status(actor=accounts["admin"], category=cat_cycle, is_active=True, expected_version=cat_cycle.state_version)
    p_act.refresh_from_db()
    p_inact.refresh_from_db()
    pos_after_react = c_sel.get("/ventas/?query=Arroz+Ciclo").content.decode("utf-8")

    report["lifecycle_cross_module"] = {
        "inactive_product_duplicate_name_blocked": inactive_name_err,
        "inactive_product_duplicate_barcode_blocked": inactive_bc_err,
        "confirm_page_counts": {
            "status": confirm_get.status_code,
            "product_count": confirm_get.context["product_count"],
            "draft_count": confirm_get.context["draft_count"],
            "physical_units": confirm_get.context["physical_units"],
        },
        "badges_in_product_list_when_cat_inactive": {
            "has_categoria_desactivada": "Categoría desactivada" in prod_list_html,
            "has_inactivo": "Inactivo" in prod_list_html,
            "p_act_has_stock_bajo": "Stock bajo" in prod_list_html,
        },
        "inventory_when_cat_inactive": {
            "p_act_in_stock_overview_low_stock": str(p_act.pk) in low_stock_ids,
            "p_act_excluded_from_stock_entry_select": "Arroz Ciclo 1Kg" not in entry_form_html,
            "p_noload_excluded_from_initial_load_select": "Avena Sin Carga 200g" not in load_form_html,
            "initial_load_service": init_blocked,
            "stock_entry_service": entry_blocked,
            "writeoff_expired_lot_service": wo_exp_res,
            "physical_adjustment_service": adj_res,
        },
        "sales_when_cat_inactive": {
            "excluded_from_pos_search_results": "Arroz Ciclo 1Kg" not in pos_search_html.split("sales-search-panel")[1].split("</section>")[0] if "sales-search-panel" in pos_search_html else None,
            "line_preserved_in_active_draft_panel": pos_draft_banner_ok,
            "update_draft_line": upd_blocked,
            "checkout_sale": chk_blocked,
            "sales_count_still_zero": Sale.objects.count() == 0,
            "remove_blocked_line_http_status": rm_resp.status_code,
            "draft_status_after_removing_only_line": draft.status,
        },
        "edit_product_with_inactive_cat": {
            "keep_same_inactive_category": edit_keep_cat,
            "move_other_product_into_inactive_category": move_into_inact_cat,
        },
        "after_reactivating_category": {
            "p_inact_remains_inactive": p_inact.is_active is False,
            "p_act_back_in_pos_search": "Arroz Ciclo 1Kg" in pos_after_react,
        },
    }

    # ── 4. Extremes, SQL wildcards, Unicode confusables, errors, toggle bug ───
    from catalog.forms import CategoryForm, ProductRegistrationForm

    p_unicode = register_canned_product(
        actor=accounts["admin"], name="Atún Especial 170g", barcode="UNI-001", barcode_type="INTERNAL",
        category=cat_dest, unit="UND", sale_price=Decimal("4.90"), minimum_stock=5,
    )
    # Accents must remain distinct (PROP-03C-NOMBRE / CP-HU-PROD-04-001)
    p_no_accent = register_canned_product(
        actor=accounts["admin"], name="Atun Especial 170g", barcode="UNI-002", barcode_type="INTERNAL",
        category=cat_dest, unit="UND", sale_price=Decimal("4.90"), minimum_stock=5,
    )
    # 61x sharp s expands under casefold to 122 chars > Category.name_normalized(120)
    cat_ss_clean = cap_err(lambda: Category(name="ß" * 61).full_clean())
    # NFC vs NFD search & duplicate
    nfd_name = "Atu\u0301n Especial 170g"
    nfc_dup_err = cap_err(lambda: register_canned_product(
        actor=accounts["admin"], name=nfd_name, barcode="UNI-NFD", barcode_type="INTERNAL",
        category=cat_dest, unit="UND", sale_price=Decimal("4.90"), minimum_stock=5,
    ))
    dotless_search = c_admin.get("/productos/?q=At%C4%B1n")  # Turkish ı (should NOT crash)
    wildcard_pct = list(c_admin.get("/productos/?q=%25").context["products"].values_list("name", flat=True))
    wildcard_us = list(c_admin.get("/productos/?q=_").context["products"].values_list("name", flat=True))
    wildcard_bs = list(c_admin.get("/productos/?q=\\").context["products"].values_list("name", flat=True))
    zw_resp = c_admin.post("/productos/nuevo/", {
        "name": "Prod\u200bZero", "barcode_type": "INTERNAL", "barcode": "ZW-001",
        "category": str(cat_dest.pk), "unit": "UND", "sale_price": "5.00", "minimum_stock": "10",
    })
    zw_saved = Product.objects.filter(barcode="ZW-001").values_list("name", flat=True).first()

    # Exact form error literals across CategoryForm & ProductRegistrationForm
    def form_err(form_cls, payload):
        f = form_cls(payload)
        f.is_valid()
        return f.errors.get_json_data()

    cat_errs = {
        "empty": form_err(CategoryForm, {"name": "   "}),
        "punct": form_err(CategoryForm, {"name": "---"}),
        "len_121": form_err(CategoryForm, {"name": "A" * 121}),
        "ss_61_model_clean": cat_ss_clean,
    }
    prod_form_cases = {}
    for label, overrides in [
        ("empty_all", {"name": "", "barcode_type": "", "barcode": "", "category": "", "unit": "", "sale_price": "", "minimum_stock": ""}),
        ("name_161", {"name": "N" * 161}),
        ("name_punct", {"name": "***"}),
        ("name_dup", {"name": "atún   especial 170g"}),
        ("bc_len_65", {"barcode": "B" * 65}),
        ("bc_invalid_char_newline", {"barcode": "ABC\n123"}),
        ("bc_invalid_char_ñ", {"barcode": "ABC-ñ-123"}),
        ("gtin_8_digit", {"barcode_type": "GTIN", "barcode": "12345670"}),
        ("gtin_11_digit", {"barcode_type": "GTIN", "barcode": "12345678901"}),
        ("gtin_14_starts_with_1", {"barcode_type": "GTIN", "barcode": "10063813339314"}),
        ("gtin_bad_check_digit", {"barcode_type": "GTIN", "barcode": "4006381333932"}),
        ("price_zero", {"sale_price": "0.00"}),
        ("price_10M", {"sale_price": "10000000.00"}),
        ("price_3dec", {"sale_price": "1.234"}),
        ("price_plus", {"sale_price": "+10.00"}),
        ("price_sci", {"sale_price": "1e2"}),
        ("price_comma", {"sale_price": "10,50"}),
        ("price_fullwidth", {"sale_price": "\uff11\uff10"}),
        ("min_neg1", {"minimum_stock": "-1"}),
        ("min_1M", {"minimum_stock": "1000000"}),
        ("min_float", {"minimum_stock": "1.5"}),
        ("unit_kg", {"unit": "KG"}),
    ]:
        base = {
            "name": f"Valid {label}", "barcode_type": "INTERNAL", "barcode": f"BC-{label}",
            "category": str(cat_dest.pk), "unit": "UND", "sale_price": "5.00", "minimum_stock": "10",
        }
        base.update(overrides)
        if label in ("gtin_8_digit", "gtin_11_digit", "gtin_14_starts_with_1", "gtin_bad_check_digit"):
            # Form clean doesn't run model.full_clean(barcode reading_keys); full POST runs service too
            resp = c_admin.post("/productos/nuevo/", base)
            prod_form_cases[label] = {
                "http_status": resp.status_code,
                "errors": resp.context["form"].errors.get_json_data() if resp.status_code == 200 else {},
            }
        else:
            prod_form_cases[label] = form_err(ProductRegistrationForm, base)

    # Toggle availability without explicit is_active (no optimistic lock / blind flip defect)
    before_state = p_unicode.is_active
    c_admin.post(f"/productos/{p_unicode.pk}/disponibilidad/", {})
    p_unicode.refresh_from_db()
    after_first_omit = p_unicode.is_active
    c_admin.post(f"/productos/{p_unicode.pk}/disponibilidad/", {"is_active": "false"})
    p_unicode.refresh_from_db()
    after_explicit_false = p_unicode.is_active
    c_admin.post(f"/productos/{p_unicode.pk}/disponibilidad/", {"is_active": "false"})
    p_unicode.refresh_from_db()
    after_second_explicit_false = p_unicode.is_active

    report["validation_and_search_probes"] = {
        "distinct_accents_kept": p_unicode.pk != p_no_accent.pk,
        "nfc_nfd_duplicate_blocked": nfc_dup_err,
        "turkish_dotless_i_status": dotless_search.status_code,
        "wildcard_percent_matches": len(wildcard_pct),
        "wildcard_underscore_matches": len(wildcard_us),
        "wildcard_backslash_matches": len(wildcard_bs),
        "zero_width_preserved_in_name": repr(zw_saved),
        "category_errors": cat_errs,
        "product_errors": prod_form_cases,
        "product_toggle_omitted_is_active_flips": {
            "before": before_state,
            "after_omit": after_first_omit,
            "after_false_1": after_explicit_false,
            "after_false_2": after_second_explicit_false,
        },
        "model_service_boundaries": {
            "min_bool_true": cap_err(lambda: Product(
                category=cat_dest, name="Bool Min", barcode="BOOL-MIN", barcode_type="INTERNAL",
                sale_price=Decimal("1.00"), minimum_stock=True,
            ).full_clean()),
            "price_float_service": cap_err(lambda: register_canned_product(
                actor=accounts["admin"], name="Float Price", barcode="FLT-1", barcode_type="INTERNAL",
                category=cat_dest, unit="UND", sale_price=1.50, minimum_stock=5,
            )),
            "cat_delete_protected": None,
        },
    }
    try:
        cat_dest.delete()
        report["validation_and_search_probes"]["model_service_boundaries"]["cat_delete_protected"] = "DELETED"
    except Exception as exc:
        report["validation_and_search_probes"]["model_service_boundaries"]["cat_delete_protected"] = type(exc).__name__

    # ── 5. Run Real Chrome inspection BEFORE inserting 500 scale rows ─────────
    browser_ids = {"cat_id": str(cat_cycle.pk), "prod_id": str(p_act.pk)}
    (run_dir / ".browser-ids.json").write_text(json.dumps(browser_ids), encoding="utf-8")

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    env = os.environ.copy()
    env["AUDIT03_REVAL_B_PORT"] = str(port)
    srv_log = (out_dir / "server-stdout.txt").open("w", encoding="utf-8", errors="replace")
    srv_proc = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "serve"],
        env=env, cwd=str(APP), stdout=srv_log, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace",
    )
    try:
        deadline = time.time() + 45
        ready = False
        while time.time() < deadline:
            if srv_proc.poll() is not None:
                srv_log.flush()
                raise RuntimeError("Server exited early: " + (out_dir / "server-stdout.txt").read_text(encoding="utf-8"))
            with socket.socket() as probe:
                if probe.connect_ex(("127.0.0.1", port)) == 0:
                    ready = True
                    break
            time.sleep(0.25)
        if not ready:
            raise RuntimeError("Timeout starting server")
        ch = subprocess.run(
            ["node", str(SUPPORT / "audit03_reval_b_chrome.cjs")],
            env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=180,
        )
        if ch.returncode != 0:
            raise RuntimeError(f"Chrome sublote B failed ({ch.returncode}):\n{ch.stdout}\n{ch.stderr}")
        report["chrome_sublote_b"] = json.loads((out_dir / "browser-b-report.json").read_text(encoding="utf-8"))
    finally:
        srv_proc.terminate()
        try:
            srv_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            srv_proc.kill()
            srv_proc.wait()
        srv_log.close()

    # ── 6. Scalability & SQL Query Count on /productos/ & /categorias/ ───────
    cats_bulk = [
        Category(name=f"Cat Scale {i:02d}", name_normalized=f"cat scale {i:02d}")
        for i in range(50)
    ]
    Category.objects.bulk_create(cats_bulk)
    all_scale_cats = list(Category.objects.filter(name__startswith="Cat Scale "))
    prods_bulk = []
    for i in range(500):
        c = all_scale_cats[i % len(all_scale_cats)]
        prods_bulk.append(Product(
            category=c,
            name=f"ProdScale{i:04d} Generico",
            search_name=f"prodscale{i:04d} generico",
            barcode=f"SC-{i:06d}",
            barcode_type=Product.BarcodeType.INTERNAL,
            barcode_normalized=f"SC-{i:06d}",
            unit="UND",
            sale_price=Decimal("9.90"),
            minimum_stock=10,
            is_active=(i % 10 != 0),
        ))
    Product.objects.bulk_create(prods_bulk)
    created_scale = list(Product.objects.filter(barcode__startswith="SC-"))
    ProductBarcodeKey.objects.bulk_create([
        ProductBarcodeKey(product=p, reading_key=p.barcode_normalized) for p in created_scale
    ])
    lots_bulk = []
    for p in created_scale:
        for k in range(3):
            lots_bulk.append(Lot(
                product=p,
                responsible=accounts["warehouse"],
                number=f"L-{p.barcode}-{k}",
                number_normalized=f"L-{p.barcode}-{k}",
                initial_quantity=10,
                available_quantity=5,
                unit_cost=Decimal("4.00"),
                expiration_date=today + timedelta(days=30 * (k + 1) if k > 0 else -5),
            ))
    Lot.objects.bulk_create(lots_bulk)

    def bench_get(client: Client, url: str):
        with CaptureQueriesContext(connection) as ctx:
            t0 = time.perf_counter()
            r = client.get(url)
            dt_ms = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "url": url,
            "status": r.status_code,
            "sql_queries": len(ctx),
            "sql_ms": round(sum(float(q["time"]) for q in ctx) * 1000, 2),
            "http_ms": dt_ms,
            "html_bytes": len(r.content),
            "row_count": r.content.decode("utf-8").count("<tr>") - 1,
        }

    report["scale_benchmark"] = {
        "total_products": Product.objects.count(),
        "total_lots": Lot.objects.count(),
        "total_categories": Category.objects.count(),
        "admin_product_list_all": bench_get(c_admin, "/productos/"),
        "warehouse_product_list_all": bench_get(c_wh, "/productos/"),
        "admin_product_list_filtered": bench_get(c_admin, "/productos/?q=ProdScale0250"),
        "admin_category_list_all": bench_get(c_admin, "/productos/categorias/"),
    }

    # ── 7. seed_pmv + seed_demo + reset_demo_db with confirmed Sale ────────────
    seed_out = {}
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        # Make sure Enlatados exists like seed_pmv expects (reuse via seed_pmv)
        os.environ["SEED_ADMIN_PASSWORD"] = "Seed-" + secrets.token_urlsafe(12) + "A1"
        os.environ["SEED_WAREHOUSE_PASSWORD"] = "Seed-" + secrets.token_urlsafe(12) + "A1"
        os.environ["SEED_SELLER_PASSWORD"] = "Seed-" + secrets.token_urlsafe(12) + "A1"
        call_command("seed_pmv")
        call_command("seed_demo")
        out_second = io.StringIO()
    with contextlib.redirect_stdout(out_second):
        call_command("seed_demo")
    demo_prods = list(
        Product.objects.filter(category__name_normalized="productos enlatados")
        .values("name", "barcode", "barcode_type", "sale_price", "minimum_stock")
        .order_by("barcode")
    )
    demo_loads = InitialInventoryLoad.objects.filter(product__category__name_normalized="productos enlatados").count()
    demo_load_lines = InitialLoadLine.objects.filter(load__product__category__name_normalized="productos enlatados").count()

    # Create a confirmed sale on a demo product and test reset_demo_db --confirm
    d_p = Product.objects.get(barcode="7750001000011")
    d_draft = add_product_to_draft(actor=accounts["seller"], product_id=d_p.pk, quantity=1)
    checkout_sale(
        actor=accounts["seller"], draft_id=d_draft.pk, cash_received=Decimal("10.00"), idempotency_key=uuid4(),
    )
    os.environ["APP_ENV"] = "local"
    reset_err = None
    try:
        call_command("reset_demo_db", "--confirm")
        reset_err = "OK"
    except Exception as exc:
        reset_err = f"{type(exc).__name__}: {str(exc)[:220]}"
    finally:
        for k in ("SEED_ADMIN_PASSWORD", "SEED_WAREHOUSE_PASSWORD", "SEED_SELLER_PASSWORD"):
            os.environ.pop(k, None)

    report["seed_demo_probe"] = {
        "demo_products": demo_prods,
        "second_run_stdout": out_second.getvalue().strip(),
        "initial_loads_created": demo_loads,
        "initial_load_lines_created": demo_load_lines,
        "reset_demo_db_with_confirmed_sale": reset_err,
    }

    hashes_after = {str(p.relative_to(ROOT)): digest(p) for p in protected if p.exists()}
    ext_after = {str(p.relative_to(ROOT)): digest(p) for p in external_watch if p.exists()}
    manifest_after = source_manifest_hash()
    protected_unchanged = all(hashes_before.get(k) == v for k, v in hashes_after.items())

    report["protected_unchanged"] = protected_unchanged
    report["protected_hashes"] = hashes_after
    report["external_hashes_before"] = ext_before
    report["external_hashes_after"] = ext_after
    report["external_changed_keys"] = [k for k in ext_after if ext_before.get(k) != ext_after[k]]
    report["build_manifest_after"] = manifest_after
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()

    (out_dir / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "out_dir": str(out_dir.relative_to(ROOT)),
        "protected_unchanged": protected_unchanged,
        "source_manifest": manifest_after["source_manifest"],
        "cache_admin_missing_200_302": report["cache_summary"]["admin_200_302_missing_no_store"],
        "cache_admin_get_post_count": report["cache_summary"]["admin_get_post_standard_missing_count"],
        "cache_denied_missing_count": report["cache_summary"]["denied_403_405_missing_count"],
        "scale_500_admin_queries": report["scale_benchmark"]["admin_product_list_all"]["sql_queries"],
        "scale_500_admin_bytes": report["scale_benchmark"]["admin_product_list_all"]["html_bytes"],
        "chrome_page_errors": len(report["chrome_sublote_b"].get("page_errors", [])),
    }, ensure_ascii=False, indent=2))
    if not protected_unchanged:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
