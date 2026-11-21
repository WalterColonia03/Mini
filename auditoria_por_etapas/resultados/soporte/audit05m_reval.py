"""Stage 05-M supplemental verification against frozen 14-CIERRE build (SQLite isolated).

Covers behavior outside existing automated checks without altering r1-pmv/:
1. DEC-05-LOTE-ESPACIOS normalization/display preservation & LotInputForm max_length=64 raw-vs-collapsed divergence.
2. Reproducible defect in r1-pmv/inventory/views.py:165 (legacy_lots misclassifies adjustment_origin lots).
3. Cross-role matrix (ALMACENERO / ADMIN / VENDEDOR / anon) on canonical, alias, form, stock, and movements routes + no-store.
4. Boundary validation (qty 1 / 999999 / 1000000, cost 0.0001 / 0 / 5 decimals, Lima midnight boundary, deactivated supplier between GET & POST, controls_expiration=False).
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import secrets
import shutil
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(4)

TMP_DIR = Path(tempfile.gettempdir()).resolve() / f"audit05m-{STAMP}"
TMP_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = TMP_DIR / "audit05m.sqlite3"

protected = [
    *(APP).glob("*.sqlite3"),
    *(RESULTS / "datos").rglob("*.sqlite3"),
    ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
]


def state_hash(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


start_hashes = {str(p.relative_to(ROOT)): state_hash(p) for p in protected}
report: dict = {
    "started_utc": STAMP,
    "db_path": str(DB_PATH),
    "cases": [],
}

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

    from django.core.exceptions import ValidationError
    from django.core.management import call_command
    from django.db import IntegrityError, connections, transaction
    from django.test import Client
    from django.utils import timezone as tz
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.forms import LotInputForm
    from inventory.models import InitialInventoryLoad, InitialLoadLine, Lot
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        create_supplier,
        register_physical_adjustment,
        toggle_supplier_status,
    )

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    def record(case_id: str, ok: bool, details: dict) -> None:
        report["cases"].append({"id": case_id, "ok": bool(ok), "details": details})

    admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    pw = "Audit05M#Pass123"
    admin = Account.objects.create_user("admin05m@test.invalid", pw, display_name="Admin 05M", role=admin_role)
    wh = Account.objects.create_user("wh05m@test.invalid", pw, display_name="Almacenero 05M", role=wh_role)
    seller = Account.objects.create_user("seller05m@test.invalid", pw, display_name="Vendedor 05M", role=seller_role)

    cat = Category.objects.create(name="Categoria 05M")
    sup = create_supplier(actor=admin, name="Proveedor 05M SAC", ruc="20100070970")
    future = tz.localdate() + timedelta(days=45)
    future2 = tz.localdate() + timedelta(days=90)

    # ── T1: DEC-05-LOTE-ESPACIOS & form-vs-service max_length=64 raw vs normalized ──
    p_dec = Product.objects.create(category=cat, name="Producto DEC05", barcode="775050010001", sale_price=Decimal("8.00"))
    load_dec = confirm_initial_load(
        actor=wh,
        product=p_dec,
        supplier=sup,
        lots=[
            LotInput("  ab  12 ", 4, Decimal("2.0000"), future),
            LotInput("AB12", 6, Decimal("3.0000"), future2),
        ],
    )
    lots_dec = list(Lot.objects.filter(product=p_dec).order_by("number_normalized"))
    lines_dec = list(InitialLoadLine.objects.filter(load=load_dec).order_by("number"))
    raw67_norm63 = "AB" + (" " * 5) + ("X" * 60)  # raw length 67, normalized length 63 ("AB " + 60 X)
    form_raw67 = LotInputForm(
        data={
            "number": raw67_norm63,
            "quantity": "1",
            "unit_cost": "1.0000",
            "expiration_date": future.isoformat(),
        }
    )
    form_raw67_valid = form_raw67.is_valid()
    p_svc63 = Product.objects.create(category=cat, name="Producto SVC63", barcode="775050010002", sale_price=Decimal("8.00"))
    svc63_ok = False
    try:
        confirm_initial_load(
            actor=wh,
            product=p_svc63,
            lots=[LotInput(raw67_norm63, 1, Decimal("1.0000"), future)],
        )
        svc63_ok = True
    except ValidationError:
        svc63_ok = False

    record(
        "T1_dec05_normalization_and_max64_form_vs_service_divergence",
        len(lots_dec) == 2
        and [l.number for l in lots_dec] == ["AB 12", "AB12"]
        and [ln.number for ln in lines_dec] == ["AB 12", "AB12"]
        and not form_raw67_valid
        and svc63_ok,
        {
            "lot_numbers": [l.number for l in lots_dec],
            "lot_normalized": [l.number_normalized for l in lots_dec],
            "line_numbers": [ln.number for ln in lines_dec],
            "raw67_norm63_len_raw": len(raw67_norm63),
            "raw67_norm63_len_norm": len(Lot.normalize_number(raw67_norm63)),
            "form_accepts_raw67": form_raw67_valid,
            "form_errors": {k: list(v) for k, v in form_raw67.errors.items()},
            "service_accepts_raw67": svc63_ok,
        },
    )

    # ── T2: Repro of views.py:165 legacy_lots misclassification for adjustment_origin lots ──
    p_adj = Product.objects.create(category=cat, name="Producto Ajuste Constancia", barcode="775050010003", sale_price=Decimal("10.00"))
    load_adj = confirm_initial_load(
        actor=wh,
        product=p_adj,
        supplier=sup,
        lots=[LotInput("L-ORIG-ADJ", 5, Decimal("4.0000"), future)],
    )
    adj_result = register_physical_adjustment(
        actor=admin,
        product=p_adj,
        lot=None,
        delta=4,
        number="L-NEW-ADJ",
        expiration_date=future2,
        reason="Sobrante fisico encontrado en auditoria 05M",
    )
    c_wh = Client()
    c_wh.force_login(wh)
    resp_adj_const = c_wh.get(f"/inventario/cargas/{load_adj.pk}/")
    html_adj_const = resp_adj_const.content.decode("utf-8")
    resp_adj_mov = c_wh.get(f"/inventario/productos/{p_adj.pk}/movimientos/")
    html_adj_mov = resp_adj_mov.content.decode("utf-8")
    misclassified = (
        "Lotes vinculados sin fotografía original" in html_adj_const
        and "L-NEW-ADJ" in html_adj_const
        and adj_result.created_lot is not None
        and adj_result.created_lot.adjustment_origin_id == adj_result.pk
    )
    record(
        "T2_repro_views_py_165_adjustment_lot_misclassified_as_legacy",
        misclassified,
        {
            "status_constancia": resp_adj_const.status_code,
            "adjustment_lot_id": str(adj_result.created_lot.pk) if adj_result.created_lot else None,
            "has_adjustment_origin_id": bool(adj_result.created_lot and adj_result.created_lot.adjustment_origin_id),
            "renders_legacy_section": "Lotes vinculados sin fotografía original" in html_adj_const,
            "legacy_section_includes_adjustment_lot": "L-NEW-ADJ" in html_adj_const,
            "movements_status": resp_adj_mov.status_code,
            "movements_identifies_ajuste": "Ajuste" in html_adj_mov and "L-NEW-ADJ" in html_adj_mov,
        },
    )

    # ── T3: Cross-role HTTP matrix including canonical/alias constancia & no-store ──
    c_adm, c_sel, c_anon = Client(), Client(), Client()
    c_adm.force_login(admin)
    c_sel.force_login(seller)
    routes = [
        ("form", "/inventario/carga-inicial/", 200, 403, 403, 302),
        ("canonical", f"/inventario/cargas/{load_dec.pk}/", 200, 200, 403, 302),
        ("alias", f"/inventario/carga-inicial/{load_dec.pk}/creada/", 200, 200, 403, 302),
        ("stock", "/inventario/stock/", 200, 200, 403, 302),
        ("movements", f"/inventario/productos/{p_dec.pk}/movimientos/", 200, 200, 403, 302),
    ]
    role_matrix = {}
    matrix_ok = True
    for name, url, exp_w, exp_a, exp_s, exp_anon in routes:
        rw = c_wh.get(url)
        ra = c_adm.get(url)
        rs = c_sel.get(url)
        rx = c_anon.get(url)
        resps = [("wh", rw, exp_w), ("admin", ra, exp_a), ("seller", rs, exp_s), ("anon", rx, exp_anon)]
        statuses_ok = all(r.status_code == exp for _, r, exp in resps)
        ok_200_nostore = all("no-store" in r.headers.get("Cache-Control", "") for _, r, exp in resps if exp == 200)
        ok = statuses_ok and ok_200_nostore
        matrix_ok = matrix_ok and ok
        role_matrix[name] = {
            role_k: {"status": r.status_code, "cache_control": r.headers.get("Cache-Control", "")}
            for role_k, r, _ in resps
        }
    record("T3_role_matrix_and_alias_constancia_no_store", matrix_ok, role_matrix)

    # ── T4: Supplier deactivated between GET and POST, plus boundary checks & Lima midnight ──
    sup_temp = create_supplier(actor=admin, name="Proveedor Temporal 05M", ruc="20481000215")
    p_sup_stale = Product.objects.create(category=cat, name="Producto Stale Sup", barcode="775050010004", sale_price=Decimal("6.00"))
    toggle_supplier_status(actor=admin, supplier=sup_temp)  # deactivate after "GET"
    stale_payload = {
        "product": str(p_sup_stale.pk),
        "supplier": str(sup_temp.pk),
        "lots-TOTAL_FORMS": "1",
        "lots-INITIAL_FORMS": "0",
        "lots-MIN_NUM_FORMS": "1",
        "lots-MAX_NUM_FORMS": "1000",
        "lots-0-number": "L-STALE-SUP",
        "lots-0-quantity": "2",
        "lots-0-unit_cost": "1.5000",
        "lots-0-expiration_date": future.isoformat(),
    }
    stale_post = c_wh.post("/inventario/carga-inicial/", stale_payload)
    stale_body = stale_post.content.decode("utf-8")
    sentinel_post = c_wh.post(
        "/inventario/carga-inicial/",
        dict(stale_payload, supplier=f"__inactive__:{sup_temp.pk}"),
    )
    sentinel_body = sentinel_post.content.decode("utf-8")
    stale_ok = (
        stale_post.status_code == 200
        and sentinel_post.status_code == 200
        and InitialInventoryLoad.objects.filter(product=p_sup_stale).count() == 0
        and Lot.objects.filter(product=p_sup_stale).count() == 0
        and f"__inactive__:{sup_temp.pk}" in stale_body
        and "está inactivo. Seleccione un proveedor activo" in stale_body
        and "está inactivo. Seleccione un proveedor activo" in sentinel_body
    )
    record(
        "T4_deactivated_supplier_rejected_atomically_keeps_sentinel",
        stale_ok,
        {
            "status": stale_post.status_code,
            "sentinel_status": sentinel_post.status_code,
            "loads": InitialInventoryLoad.objects.filter(product=p_sup_stale).count(),
            "has_inactive_sentinel": f"__inactive__:{sup_temp.pk}" in stale_body,
            "has_inactive_msg": "está inactivo. Seleccione un proveedor activo" in stale_body,
            "sentinel_resubmit_rejected": "está inactivo. Seleccione un proveedor activo" in sentinel_body,
        },
    )

    # T5: Exact Lima midnight boundary & min/max qty/cost boundaries
    lima_tz = ZoneInfo("America/Lima")
    dt_2330_lima = datetime(2026, 11, 14, 23, 30, 0, tzinfo=lima_tz).astimezone(timezone.utc)
    p_bound = Product.objects.create(category=cat, name="Producto Limites 05M", barcode="775050010005", sale_price=Decimal("5.00"))
    with patch("django.utils.timezone.now", return_value=dt_2330_lima):
        from datetime import date

        today_lima_rejected = False
        try:
            confirm_initial_load(
                actor=wh,
                product=p_bound,
                lots=[LotInput("L-LIM-TODAY", 1, Decimal("0.0001"), date(2026, 11, 14))],
            )
        except ValidationError:
            today_lima_rejected = True

        tomorrow_lima_ok = False
        if InitialInventoryLoad.objects.filter(product=p_bound).count() == 0:
            load_bound = confirm_initial_load(
                actor=wh,
                product=p_bound,
                lots=[
                    LotInput("L-MIN", 1, Decimal("0.0001"), date(2026, 11, 15)),
                    LotInput("L-MAX", 999999, Decimal("9999999.9999"), date(2026, 11, 16)),
                ],
            )
            p_bound.refresh_from_db()
            tomorrow_lima_ok = (
                p_bound.physical_stock == 1000000
                and p_bound.average_cost == Decimal("9999989.9999")
                and load_bound.lots.count() == 2
            )

    p_over_cost = Product.objects.create(category=cat, name="Producto Costo Excedido 05M", barcode="775050010007", sale_price=Decimal("5.00"))
    over_cost_rejected = False
    try:
        confirm_initial_load(actor=wh, product=p_over_cost, lots=[LotInput("L-OVER", 1, Decimal("10000000.0000"), future)])
    except ValidationError:
        over_cost_rejected = True

    no_exp_db_rejected = False
    try:
        with transaction.atomic():
            Product.objects.create(
                category=cat,
                name="Producto Sin Vencimiento",
                barcode="775050010006",
                sale_price=Decimal("5.00"),
                controls_expiration=False,
            )
    except IntegrityError:
        no_exp_db_rejected = True

    non_und_db_rejected = False
    try:
        with transaction.atomic():
            Product.objects.create(
                category=cat,
                name="Producto Peso KG",
                barcode="775050010008",
                sale_price=Decimal("5.00"),
                unit="KG",
            )
    except IntegrityError:
        non_und_db_rejected = True

    record(
        "T5_boundaries_lima_midnight_min_cost_max_qty_no_expiration",
        today_lima_rejected and tomorrow_lima_ok and over_cost_rejected and no_exp_db_rejected and non_und_db_rejected,
        {
            "today_lima_rejected_at_2330": today_lima_rejected,
            "tomorrow_lima_and_extremes_ok": tomorrow_lima_ok,
            "over_cost_rejected": over_cost_rejected,
            "bound_stock": p_bound.physical_stock,
            "bound_avg_cost": str(p_bound.average_cost),
            "controls_expiration_false_db_check": no_exp_db_rejected,
            "non_und_db_check": non_und_db_rejected,
        },
    )

finally:
    connections.close_all()
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    report["protected_unchanged"] = {
        k: state_hash(ROOT / k) == v for k, v in start_hashes.items()
    }
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    out_file = RESULTS / "evidencias" / f"05-M-reval-{STAMP}.json"
    out_file.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                "evidence": str(out_file.relative_to(ROOT)),
                "cases": [{"id": c["id"], "ok": c["ok"]} for c in report["cases"]],
                "operational_unchanged": report["protected_unchanged"].get("r1-pmv\\r1_pmv.sqlite3"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )

if not report["cases"] or not all(c["ok"] for c in report["cases"]):
    raise SystemExit(1)
