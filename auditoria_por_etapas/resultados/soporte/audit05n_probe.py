"""Stage 05-N isolated Django HTTP/ORM probe (no edits to r1-pmv/).

Covers:
1. Empty eligible-product state & GET form count/field attributes on /inventario/carga-inicial/.
2. Formset & #initial-load-errors behavior:
   - all blank, product-only, concurrent product_form.non_field_errors duplication check
   - Card 0 blank + Card 1 valid (observes Django min_num=1 empty_permitted=False behavior)
   - Card 0 blank + Card 1 invalid (focus + href anchor)
   - TOTAL_FORMS=5 (5 lots atomic confirm)
   - Tampered/missing management_form (TOTAL_FORMS missing / '0' / 'abc' / '-1') -> verifies no 500!
3. /productos/vencimientos/ filter edge cases & empty state.
4. /inventario/productos/<id>/movimientos/ filter validation & pagination (>25 movements, page 1/2/99).
5. HTML role visibility checks (ALMACENERO vs ADMIN on initial_load_created & stock_overview).
"""
from __future__ import annotations

import contextlib
import hashlib
import html as html_lib
import io
import json
import os
import re
import secrets
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)

TMP_DIR = Path(tempfile.gettempdir()).resolve() / f"audit05n-probe-{STAMP}"
TMP_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = TMP_DIR / "audit05n_probe.sqlite3"

PROTECTED = [
    *APP.glob("*.sqlite3"),
    *(RESULTS / "datos").rglob("*.sqlite3"),
    ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
]


def sha256_or_none(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def extract_error_summary(html_text: str) -> str:
    m = re.search(r'<div[^>]*id="initial-load-errors"[^>]*>(.*?)</div>', html_text, re.S)
    if not m:
        return ""
    return re.sub(r"\s+", " ", html_lib.unescape(re.sub(r"<[^>]+>", " ", m.group(1)))).strip()


start_hashes = {str(p.relative_to(ROOT)): sha256_or_none(p) for p in PROTECTED}
report: dict = {
    "started_utc": STAMP,
    "cases": [],
    "observations": {},
}


def record(case_id: str, ok: bool, details: dict) -> None:
    report["cases"].append({"id": case_id, "ok": ok, "details": details})


try:
    sys.path.insert(0, str(APP))
    os.environ.update(
        APP_ENV="test",
        DJANGO_DEBUG="false",
        DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
        DJANGO_SETTINGS_MODULE="config.settings",
    )
    from config import env

    env.load_dotenv = lambda path=None: None
    from django.conf import settings

    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(DB_PATH),
        }
    }
    settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
    settings.CSRF_COOKIE_SECURE = False
    settings.SESSION_COOKIE_SECURE = False
    settings.SECURE_SSL_REDIRECT = False

    import django

    django.setup()

    from django.core.management import call_command
    from django.db import connections
    from django.test import Client
    from django.utils import timezone as tz

    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.forms import InitialLoadProductForm, LotInputForm, LotInputFormSet, MovementFilterForm
    from inventory.models import InitialInventoryLoad, Lot
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        create_supplier,
        register_physical_adjustment,
        register_stock_entry,
    )

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    pw = secrets.token_urlsafe(16) + "A1!"
    admin = Account.objects.create_user("admin05n@invalid.test", pw, display_name="Admin 05N", role=admin_role)
    wh = Account.objects.create_user("wh05n@invalid.test", pw, display_name="Almacenero 05N", role=wh_role)
    Role.objects.filter(pk=seller_role.pk)  # keep role used

    cat = Category.objects.create(name="Abarrotes 05N", is_active=True)
    supplier = create_supplier(actor=admin, name="Proveedor Base 05N SAC", ruc="20555555511")

    today = tz.localdate()
    f45 = today + timedelta(days=45)
    f90 = today + timedelta(days=90)

    c_wh = Client()
    c_wh.force_login(wh)
    c_admin = Client()
    c_admin.force_login(admin)

    # --- 1. Empty catalog / zero eligible products & zero lots expirations ---
    r_empty_load = c_wh.get("/inventario/carga-inicial/")
    html_empty_load = html_lib.unescape(r_empty_load.content.decode("utf-8"))
    m_select = re.search(r'<select[^>]*name="product"[^>]*>(.*?)</select>', html_empty_load, re.S)
    product_options_empty = re.findall(r'<option[^>]*value="([^"]*)"[^>]*>(.*?)</option>', m_select.group(1), re.S) if m_select else []
    rendered_lot_indices = re.findall(r'name="lots-(\d+)-number"', html_empty_load)

    r_empty_exp = c_wh.get("/productos/vencimientos/")
    html_empty_exp = html_lib.unescape(r_empty_exp.content.decode("utf-8"))

    record(
        "N1_empty_catalog_and_expirations_formset_shape",
        r_empty_load.status_code == 200
        and len(product_options_empty) == 1
        and product_options_empty[0] == ("", "Seleccione un producto")
        and r_empty_exp.status_code == 200
        and len(rendered_lot_indices) == 4,
        {
            "empty_load_status": r_empty_load.status_code,
            "empty_product_options": product_options_empty,
            "rendered_lot_card_indices": rendered_lot_indices,
            "exp_empty_status": r_empty_exp.status_code,
            "exp_empty_has_mensaje": "no hay lotes" in html_empty_exp.lower() or "sin lotes" in html_empty_exp.lower() or "ning" in html_empty_exp.lower(),
        },
    )

    p1 = Product.objects.create(category=cat, name="Producto CardEdge 05N", barcode="775059900001", sale_price=Decimal("4.50"), minimum_stock=5)
    p2 = Product.objects.create(category=cat, name="Producto FiveLots 05N", barcode="775059900002", sale_price=Decimal("9.90"), minimum_stock=5)
    p3 = Product.objects.create(category=cat, name="Producto KardexPag 05N", barcode="775059900003", sale_price=Decimal("6.00"), minimum_stock=5)
    p4 = Product.objects.create(category=cat, name="Producto StaleRace 05N", barcode="775059900004", sale_price=Decimal("3.00"), minimum_stock=5)

    pf = InitialLoadProductForm()
    lf0 = LotInputForm(prefix="lots-0")
    mf = MovementFilterForm()
    report["observations"]["form_fields_spec"] = {
        "InitialLoadProductForm": {
            k: {"type": type(f).__name__, "required": f.required, "label": str(f.label), "widget_attrs": dict(f.widget.attrs)}
            for k, f in pf.fields.items()
        },
        "LotInputForm": {
            k: {
                "type": type(f).__name__,
                "required": f.required,
                "label": str(f.label),
                "max_length": getattr(f, "max_length", None),
                "min_value": str(getattr(f, "min_value", None)),
                "max_value": str(getattr(f, "max_value", None)),
                "decimal_places": getattr(f, "decimal_places", None),
                "widget_attrs": dict(f.widget.attrs),
            }
            for k, f in lf0.fields.items()
        },
        "LotInputFormSet": {
            "extra": LotInputFormSet.extra,
            "min_num": LotInputFormSet.min_num,
            "max_num": LotInputFormSet.max_num,
            "validate_min": LotInputFormSet.validate_min,
        },
        "MovementFilterForm": {
            k: {
                "type": type(f).__name__,
                "required": f.required,
                "label": str(f.label),
                "max_length": getattr(f, "max_length", None),
                "choices": list(getattr(f, "choices", [])) if hasattr(f, "choices") else None,
                "widget_attrs": dict(f.widget.attrs),
            }
            for k, f in mf.fields.items()
        },
    }

    def base_mgmt(total: int = 4) -> dict[str, str]:
        return {
            "lots-TOTAL_FORMS": str(total),
            "lots-INITIAL_FORMS": "0",
            "lots-MIN_NUM_FORMS": "1",
            "lots-MAX_NUM_FORMS": "1000",
        }

    def lot_row(i: int, num: str = "", qty: str = "", cost: str = "", exp: str = "") -> dict[str, str]:
        return {
            f"lots-{i}-number": num,
            f"lots-{i}-quantity": qty,
            f"lots-{i}-unit_cost": cost,
            f"lots-{i}-expiration_date": exp,
        }

    # --- 2. #initial-load-errors & min_num=1 Card 0 blank behavior ---
    all_blank = {**base_mgmt(4), "product": "", "supplier": ""}
    for i in range(4):
        all_blank.update(lot_row(i))
    r_all_blank = c_wh.post("/inventario/carga-inicial/", all_blank)
    h_all_blank = html_lib.unescape(r_all_blank.content.decode("utf-8"))

    # Product selected, Card 0 blank, Card 1 VALID -> Django min_num=1 sets lots-0.empty_permitted=False -> REJECTED at 200!
    card1_valid = {**base_mgmt(4), "product": str(p1.pk), "supplier": str(supplier.pk)}
    card1_valid.update(lot_row(0))
    card1_valid.update(lot_row(1, "L-CARD1-ONLY", "6", "2.50", f45.isoformat()))
    card1_valid.update(lot_row(2))
    card1_valid.update(lot_row(3))
    r_c1_valid = c_wh.post("/inventario/carga-inicial/", card1_valid)
    h_c1_valid = html_lib.unescape(r_c1_valid.content.decode("utf-8"))

    # Card 0 blank, Card 1 INVALID -> verify both #id_lots-0-* and #id_lots-1-quantity appear in summary
    card1_bad = {**base_mgmt(4), "product": str(p1.pk), "supplier": str(supplier.pk)}
    card1_bad.update(lot_row(0))
    card1_bad.update(lot_row(1, "L-CARD1-BAD", "0", "2.50", f45.isoformat()))
    card1_bad.update(lot_row(2))
    card1_bad.update(lot_row(3))
    r_c1_bad = c_wh.post("/inventario/carga-inicial/", card1_bad)
    h_c1_bad = html_lib.unescape(r_c1_bad.content.decode("utf-8"))

    # Card 0 VALID (standard case) -> creates load so N6 can inspect
    card0_valid = {**base_mgmt(4), "product": str(p1.pk), "supplier": str(supplier.pk)}
    card0_valid.update(lot_row(0, "L-CARD0-OK", "6", "2.50", f45.isoformat()))
    card0_valid.update(lot_row(1))
    card0_valid.update(lot_row(2))
    card0_valid.update(lot_row(3))
    r_c0_ok = c_wh.post("/inventario/carga-inicial/", card0_valid)
    p1.refresh_from_db()

    # Check non_field_errors duplication when service raises ValidationError (race: p4 loaded after GET? No, product_form uses queryset active & unloaded -> ModelChoiceField rejects already-loaded; to trigger service ValidationError, confirm p4 load between GET & POST? Wait: ModelChoiceField queries fresh DB on POST! Instead deactivate category -> service/ModelChoiceField? Same! Only way service fails with non_field_error is e.g. supplier deactivated or same-millisecond race/mock; check inactive supplier between GET and POST -> wait: supplier is ReceiptSupplierChoiceField which accepts __inactive__ only? No, supplier.clean/service _lock_receipt_supplier raises ValidationError! Let's test inactive supplier!)
    sup_race = create_supplier(actor=admin, name="Proveedor Desactivado Race", ruc="20555555599")
    # supplier is initially active; deactivate it and send raw UUID via POST -> ReceiptSupplierChoiceField checks is_active? No, let's see what renders!
    sup_race.is_active = False
    sup_race.save()
    sup_inactive_post = {**base_mgmt(4), "product": str(p4.pk), "supplier": str(sup_race.pk), **lot_row(0, "L-SUP-OFF", "2", "1.00", f45.isoformat())}
    for i in (1, 2, 3):
        sup_inactive_post.update(lot_row(i))
    r_sup_off = c_wh.post("/inventario/carga-inicial/", sup_inactive_post)
    h_sup_off = html_lib.unescape(r_sup_off.content.decode("utf-8"))

    record(
        "N2_formset_card_edges_and_summary",
        r_all_blank.status_code == 200
        and 'id="initial-load-errors"' in h_all_blank
        and r_c1_valid.status_code == 200
        and 'href="#id_lots-0-number"' in h_c1_valid
        and r_c1_bad.status_code == 200
        and 'href="#id_lots-1-quantity"' in h_c1_bad
        and r_c0_ok.status_code == 302
        and p1.physical_stock == 6
        and r_sup_off.status_code == 200,
        {
            "all_blank_summary": extract_error_summary(h_all_blank),
            "card0_blank_card1_valid_status": r_c1_valid.status_code,
            "card0_blank_card1_valid_summary": extract_error_summary(h_c1_valid),
            "card0_blank_card1_bad_summary": extract_error_summary(h_c1_bad),
            "card0_valid_created_status": r_c0_ok.status_code,
            "inactive_supplier_summary": extract_error_summary(h_sup_off),
            "inactive_supplier_alert_count": h_sup_off.count("alert alert-danger"),
        },
    )

    # --- 3. TOTAL_FORMS=5, TOTAL_FORMS=0, and tampered management_form ---
    five_payload = {**base_mgmt(5), "product": str(p2.pk), "supplier": str(supplier.pk)}
    for i in range(5):
        five_payload.update(lot_row(i, f"L-FIVE-{i+1}", str(i + 2), "3.25", (today + timedelta(days=20 + i)).isoformat()))
    r_five = c_wh.post("/inventario/carga-inicial/", five_payload)
    p2.refresh_from_db()

    tamper_results = {}
    for label, mod_payload in [
        ("zero_total", {**base_mgmt(0), "product": str(p4.pk)}),
        ("missing_mgmt", {"product": str(p4.pk), **lot_row(0, "L-T1", "1", "1.00", f45.isoformat())}),
        ("alpha_total", {**base_mgmt(4), "lots-TOTAL_FORMS": "abc", "product": str(p4.pk), **lot_row(0, "L-T2", "1", "1.00", f45.isoformat())}),
        ("neg_total", {**base_mgmt(4), "lots-TOTAL_FORMS": "-1", "product": str(p4.pk), **lot_row(0, "L-T3", "1", "1.00", f45.isoformat())}),
        ("missing_initial", {"lots-TOTAL_FORMS": "1", "lots-MIN_NUM_FORMS": "1", "lots-MAX_NUM_FORMS": "1000", "product": str(p4.pk), **lot_row(0, "L-T4", "1", "1.00", f45.isoformat())}),
    ]:
        try:
            resp = c_wh.post("/inventario/carga-inicial/", mod_payload)
            body = html_lib.unescape(resp.content.decode("utf-8"))
            tamper_results[label] = {
                "status": resp.status_code,
                "exception": None,
                "summary": extract_error_summary(body),
                "has_alert": 'role="alert"' in body,
            }
        except Exception as exc:
            tamper_results[label] = {"status": "EXCEPTION", "exception": f"{type(exc).__name__}: {exc}"}

    record(
        "N3_five_lots_and_tampered_management_form",
        r_five.status_code == 302
        and Lot.objects.filter(product=p2).count() == 5
        and p2.physical_stock == 20
        and all(v["status"] == 200 and v["exception"] is None for v in tamper_results.values()),
        {
            "five_lots_status": r_five.status_code,
            "five_lots_count": Lot.objects.filter(product=p2).count(),
            "five_lots_stock": p2.physical_stock,
            "tamper_results": tamper_results,
        },
    )

    # --- 4. Expirations filter edges ---
    exp_checks = {}
    for q, val in [("missing", ""), ("zero", "0"), ("3651", "3651"), ("alpha", "abc"), ("neg", "-5"), ("ok_30", "30"), ("ok_3650", "3650")]:
        url = "/productos/vencimientos/" + (f"?dias={val}" if q != "missing" else "")
        rx = c_wh.get(url)
        body = html_lib.unescape(rx.content.decode("utf-8"))
        exp_checks[q] = {
            "status": rx.status_code,
            "has_error": 'role="alert"' in body or "alert-danger" in body or "entre 1 y 3650" in body.lower(),
            "rows": len(re.findall(r"<tbody>(.*?)</tbody>", body, re.S)[0].split("<tr")) - 1 if "<tbody>" in body else 0,
        }
    record(
        "N4_expirations_dias_edges",
        all(v["status"] == 200 for v in exp_checks.values())
        and exp_checks["zero"]["has_error"]
        and exp_checks["3651"]["has_error"]
        and exp_checks["neg"]["has_error"]
        and not exp_checks["alpha"]["has_error"]  # fallback default 30 when non-numeric? Let's observe!
        and exp_checks["ok_3650"]["rows"] >= 6,
        exp_checks,
    )

    # --- 5. Kardex pagination (>25 movements) and filter error edges ---
    load_p3 = confirm_initial_load(
        actor=wh,
        product=p3,
        lots=[LotInput("L-KDX-1", 50, Decimal("2.0000"), f90)],
        supplier=supplier,
    )
    lot_kdx = load_p3.lots.first()
    for idx in range(26):
        if idx % 2 == 0:
            register_stock_entry(
                actor=wh,
                product=p3,
                lots=[LotInput(f"L-REC-{idx:02d}", 2, Decimal("2.1000"), f90)],
                supplier=supplier,
            )
        else:
            register_physical_adjustment(
                actor=admin,
                lot=lot_kdx,
                delta=-1,
                reason=f"Conteo ajuste 05N #{idx}",
            )

    r_mov_p1 = c_wh.get(f"/inventario/productos/{p3.pk}/movimientos/")
    r_mov_p2 = c_wh.get(f"/inventario/productos/{p3.pk}/movimientos/?page=2")
    r_mov_p99 = c_wh.get(f"/inventario/productos/{p3.pk}/movimientos/?page=99")
    r_mov_p0 = c_wh.get(f"/inventario/productos/{p3.pk}/movimientos/?page=0")
    r_mov_only_desde = c_wh.get(f"/inventario/productos/{p3.pk}/movimientos/?desde=2026-11-01T00:00")
    r_mov_inverted = c_wh.get(f"/inventario/productos/{p3.pk}/movimientos/?desde=2026-11-20T00:00&hasta=2026-11-10T00:00")
    r_mov_bad_desde = c_wh.get(f"/inventario/productos/{p3.pk}/movimientos/?desde=bad")
    r_mov_dup_param = c_wh.get(f"/inventario/productos/{p3.pk}/movimientos/?tipo=ajuste&tipo=venta")
    r_mov_tipo_adj = c_wh.get(f"/inventario/productos/{p3.pk}/movimientos/?tipo=ajuste")

    def count_mov_rows(resp) -> int:
        html = html_lib.unescape(resp.content.decode("utf-8"))
        m = re.search(r'<table[^>]*movements-table[^>]*>.*?<tbody>(.*?)</tbody>', html, re.S)
        return m.group(1).count("<tr") if m else 0

    record(
        "N5_kardex_pagination_and_filters",
        r_mov_p1.status_code == 200
        and count_mov_rows(r_mov_p1) == 25
        and r_mov_p2.status_code == 200
        and count_mov_rows(r_mov_p2) == 2
        and r_mov_p99.status_code == 200
        and r_mov_p0.status_code == 200
        and r_mov_only_desde.status_code == 200
        and r_mov_inverted.status_code == 200
        and r_mov_bad_desde.status_code == 200
        and r_mov_dup_param.status_code == 200
        and r_mov_tipo_adj.status_code == 200
        and count_mov_rows(r_mov_tipo_adj) == 13,
        {
            "total_expected": 27,
            "page1_rows": count_mov_rows(r_mov_p1),
            "page2_rows": count_mov_rows(r_mov_p2),
            "page99_status_and_rows": [r_mov_p99.status_code, count_mov_rows(r_mov_p99)],
            "page0_status_has_alert": [r_mov_p0.status_code, 'role="alert"' in html_lib.unescape(r_mov_p0.content.decode("utf-8"))],
            "only_desde_has_msg": "Complete Desde y Hasta" in html_lib.unescape(r_mov_only_desde.content.decode("utf-8")),
            "inverted_has_msg": "posterior a Hasta" in html_lib.unescape(r_mov_inverted.content.decode("utf-8")),
            "bad_desde_has_msg": "AAAA-MM-DDTHH:MM" in html_lib.unescape(r_mov_bad_desde.content.decode("utf-8")),
            "dup_param_has_msg": "No repita el parámetro" in html_lib.unescape(r_mov_dup_param.content.decode("utf-8")),
            "tipo_ajuste_rows": count_mov_rows(r_mov_tipo_adj),
        },
    )

    # --- 6. ADMIN vs ALMACENERO role HTML surface check (decoded HTML entities) ---
    load_p1 = InitialInventoryLoad.objects.get(product=p1)
    h_created_wh = html_lib.unescape(c_wh.get(f"/inventario/cargas/{load_p1.pk}/").content.decode("utf-8"))
    h_created_admin = html_lib.unescape(c_admin.get(f"/inventario/cargas/{load_p1.pk}/").content.decode("utf-8"))
    h_stock_wh = html_lib.unescape(c_wh.get("/inventario/stock/").content.decode("utf-8"))
    h_stock_admin = html_lib.unescape(c_admin.get("/inventario/stock/").content.decode("utf-8"))

    record(
        "N6_role_surface_buttons_html",
        ("Cargar otro producto" in h_created_wh and "Cargar otro producto" not in h_created_admin)
        and ("Registrar entrada posterior" in h_created_wh and "Registrar entrada posterior" not in h_created_admin)
        and ("Registrar existencias iniciales" in h_stock_wh and "Registrar existencias iniciales" not in h_stock_admin)
        and ("+ Entrada de mercadería" in h_stock_wh and "+ Entrada de mercadería" not in h_stock_admin)
        and ("Registrar merma" in h_stock_wh and "Registrar merma" in h_stock_admin)
        and ("Ajuste físico" in h_stock_admin and "Ajuste físico" not in h_stock_wh),
        {
            "created_wh_has_cargar_otro": "Cargar otro producto" in h_created_wh,
            "created_admin_hides_cargar_otro": "Cargar otro producto" not in h_created_admin,
            "created_wh_has_entrada_post": "Registrar entrada posterior" in h_created_wh,
            "created_admin_hides_entrada_post": "Registrar entrada posterior" not in h_created_admin,
            "stock_wh_has_write_ctas": ("+ Registrar existencias iniciales" in h_stock_wh and "+ Entrada de mercadería" in h_stock_wh),
            "stock_admin_hides_wh_ctas_shows_adj": ("Ajuste físico" in h_stock_admin and "Registrar existencias iniciales" not in h_stock_admin),
            "stock_both_have_writeoff": ("Registrar merma" in h_stock_wh and "Registrar merma" in h_stock_admin),
        },
    )

finally:
    connections.close_all()
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    end_hashes = {k: sha256_or_none(ROOT / k) == v for k, v in start_hashes.items()}
    report["protected_unchanged"] = end_hashes
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    out_file = RESULTS / "evidencias" / f"05-N-probe-{STAMP}.json"
    out_file.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                "evidence": str(out_file.relative_to(ROOT)),
                "cases": [{"id": c["id"], "ok": c["ok"]} for c in report["cases"]],
                "all_protected_unchanged": all(end_hashes.values()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

if not report["cases"] or not all(c["ok"] for c in report["cases"]):
    raise SystemExit(1)
