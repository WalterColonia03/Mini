"""Stage 09 Revalidation Behavioral Probe (2026-11-14) in isolated SQLite.

Does not touch r1-pmv runtime code or operational/archived sqlite3 databases.
Tests forms, services, views, templates, sales/identity links, pagination,
tie-breaking, date limits, role isolation, DB constraints, and future-HU boundaries.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import re
import secrets
import sys
import uuid
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
SUPPORT = Path(__file__).resolve().parent


def digest(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def capture_exc(fn):
    try:
        res = fn()
        return {"ok": True, "result": str(res)}
    except BaseException as exc:  # noqa: BLE001
        return {
            "ok": False,
            "exc_type": type(exc).__name__,
            "message": str(exc),
        }


def safe_get(client, url: str):
    try:
        resp = client.get(url)
        return {
            "status": resp.status_code,
            "redirect": resp.headers.get("Location"),
            "cache_control": resp.headers.get("Cache-Control"),
            "body": resp.content.decode("utf-8", errors="replace"),
        }
    except BaseException as exc:  # noqa: BLE001
        return {
            "status": None,
            "exc_type": type(exc).__name__,
            "message": str(exc),
            "body": "",
        }


def safe_post(client, url: str, data: dict):
    try:
        resp = client.post(url, data=data)
        return {
            "status": resp.status_code,
            "redirect": resp.headers.get("Location"),
            "cache_control": resp.headers.get("Cache-Control"),
            "body": resp.content.decode("utf-8", errors="replace"),
        }
    except BaseException as exc:  # noqa: BLE001
        return {
            "status": None,
            "exc_type": type(exc).__name__,
            "message": str(exc),
            "body": "",
        }


def main() -> int:
    stamp = datetime.now(dt_timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    protected = [
        *APP.glob("*.sqlite3"),
        *sorted(
            p
            for p in (RESULTS / "datos").rglob("*.sqlite3")
            if p.parent.name.startswith("etapa09-") and not p.parent.name.startswith("etapa09-reval-")
        ),
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]
    start_hashes = {str(p.relative_to(ROOT)): digest(p) for p in protected}

    run_dir = RESULTS / "datos" / f"etapa09-reval-probe-{stamp}-{secrets.token_hex(4)}"
    out_dir = RESULTS / "evidencias" / "09-reval-20261114"
    run_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "marker.json").write_text(json.dumps({"run": run_dir.name, "created_utc": stamp}), encoding="utf-8")
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")

    os.environ.update(
        AUDIT09_RUN_DIR=str(run_dir),
        AUDIT09_OUT=str(out_dir),
        AUDIT09_DEFAULT_COOKIES="1",
        DJANGO_SETTINGS_MODULE="audit09_settings",
    )
    sys.path.insert(0, str(APP))
    sys.path.insert(0, str(SUPPORT))

    import django

    django.setup()

    from django.contrib import admin as django_admin
    from django.core.management import call_command
    from django.db import IntegrityError, connection, transaction
    from django.test import Client
    from django.urls import get_resolver
    from django.utils import timezone as tz

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    from cash.forms import CashCloseForm, CashOpeningForm
    from cash.models import CashRegister, CashShift, CashShiftClose
    from cash.services import close_cash_shift, open_cash_shift
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from identity.services import deactivate_employee, update_employee
    from inventory.services import LotInput, confirm_initial_load
    from sales.models import Sale, SaleDraft
    from sales.services import (
        add_product_to_draft,
        checkout_sale,
        discard_active_draft,
        remove_draft_line,
    )

    r_adm = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    r_wh = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    r_sel = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    pw = secrets.token_urlsafe(18) + "A1!"
    adm = Account.objects.create_user("adm@audit09.invalid", pw, display_name="Admin Probe", role=r_adm)
    wh = Account.objects.create_user("wh@audit09.invalid", pw, display_name="Almacen Probe", role=r_wh)
    s1 = Account.objects.create_user("s1@audit09.invalid", pw, display_name="Ana Vendedora", role=r_sel)
    s2 = Account.objects.create_user("s2@audit09.invalid", pw, display_name="Beto Vendedor", role=r_sel)
    s3 = Account.objects.create_user("s3@audit09.invalid", pw, display_name="Carla Sin Turnos", role=r_sel)

    cat = Category.objects.create(name="Abarrotes Probe", is_active=True)
    sup = __import__("inventory.services", fromlist=["create_supplier"]).create_supplier(
        actor=adm, name="Proveedor Probe SAC", ruc="20909090099", phone="01-5550099"
    )
    future = tz.localdate() + timedelta(days=90)
    prod = Product.objects.create(
        category=cat,
        name="Leche Evaporada Probe",
        barcode="775090999001",
        sale_price=Decimal("4.50"),
        minimum_stock=2,
    )
    confirm_initial_load(
        actor=wh,
        product=prod,
        supplier=sup,
        lots=[LotInput("LOT-PROBE-01", 50, Decimal("3.0000"), future)],
    )
    expensive = Product.objects.create(
        category=cat,
        name="Caja Mayorista Probe",
        barcode="775090999002",
        sale_price=Decimal("6000000.00"),
        minimum_stock=1,
    )
    confirm_initial_load(
        actor=wh,
        product=expensive,
        supplier=sup,
        lots=[LotInput("LOT-PROBE-BIG", 10, Decimal("5000000.0000"), future)],
    )

    findings: dict = {"stamp_utc": stamp}

    # ── 1. Missing / Inactive CashRegister CAJA-01 ───────────────────────────
    c_s1 = Client()
    c_s1.force_login(s1)
    r_missing_get = safe_get(c_s1, "/caja/abrir/")
    r_missing_post = safe_post(c_s1, "/caja/abrir/", {"opening_amount": "10.00"})
    reg = CashRegister.objects.create(code="CAJA-01", is_active=False)
    r_inactive_get = safe_get(c_s1, "/caja/abrir/")
    r_inactive_post = safe_post(c_s1, "/caja/abrir/", {"opening_amount": "10.00"})
    reg.is_active = True
    reg.save(update_fields=["is_active"])
    def extract_error_text(html_body: str) -> str:
        m = re.search(r'<div class="alert alert-error"[^>]*>(.*?)</div>', html_body, re.S)
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", m.group(1))).strip() if m else ""

    findings["register_edge_cases"] = {
        "missing_get_status": r_missing_get["status"],
        "missing_get_has_form": "cash-open-form" in r_missing_get["body"],
        "missing_post_status": r_missing_post["status"],
        "missing_post_has_error": "caja-01 no está disponible" in r_missing_post["body"].lower(),
        "missing_post_error_text": extract_error_text(r_missing_post["body"]),
        "inactive_get_status": r_inactive_get["status"],
        "inactive_get_has_form": "cash-open-form" in r_inactive_get["body"],
        "inactive_post_status": r_inactive_post["status"],
        "inactive_post_has_error": "caja-01 no está disponible" in r_inactive_post["body"].lower(),
        "inactive_post_error_text": extract_error_text(r_inactive_post["body"]),
        "shifts_after_rejects": CashShift.objects.count(),
    }

    # ── 2. Opening Form & Service Validation Matrix (DEC-11-TOPE-EFECTIVO-FORM)
    open_cases = [
        ("empty", ""),
        ("spaces", "   "),
        ("neg_001", "-0.01"),
        ("neg_zero", "-0.00"),
        ("plus_sign", "+10.00"),
        ("3_decimals", "10.001"),
        ("sci_notation", "1e2"),
        ("alpha", "abc"),
        ("non_ascii_digits", "١٠.٠٠"),
        ("over_op_max", "10000000.00"),
        ("zero", "0.00"),
        ("op_max", "9999999.99"),
    ]
    open_form_results = {}
    for label, raw in open_cases:
        form = CashOpeningForm(data={"opening_amount": raw})
        ok = form.is_valid()
        open_form_results[label] = {
            "valid": ok,
            "cleaned": str(form.cleaned_data["opening_amount"]) if ok else None,
            "errors": dict(form.errors),
        }
    open_svc_rejects = {}
    for label, val in [
        ("neg", Decimal("-0.01")),
        ("3_dec", Decimal("10.001")),
        ("over_max", Decimal("10000000.00")),
        ("float_type", 10.0),
    ]:
        open_svc_rejects[label] = capture_exc(lambda v=val: open_cash_shift(actor=s1, opening_amount=v))
    findings["open_validation"] = {
        "form": open_form_results,
        "service_rejections": open_svc_rejects,
        "shifts_count": CashShift.objects.count(),
    }

    # ── 3. Cumulative Close (> 9,999,999.99 up to 14,2 max) & Close Form Matrix
    big_shift = open_cash_shift(actor=s1, opening_amount=Decimal("9999999.99"))
    for _ in range(2):
        add_product_to_draft(actor=s1, product_id=expensive.pk, quantity=1)
        checkout_sale(
            actor=s1,
            draft_id=SaleDraft.objects.get(cash_shift=big_shift, status=SaleDraft.Status.ACTIVE).pk,
            cash_received=Decimal("6000000.00"),
            idempotency_key=uuid.uuid4(),
        )
    # expected = 9,999,999.99 + 12,000,000.00 = 21,999,999.99 (> 9,999,999.99!)
    close_cases = [
        ("empty", ""),
        ("neg_001", "-0.01"),
        ("neg_zero", "-0.00"),
        ("plus_sign", "+10.00"),
        ("3_decimals", "10.001"),
        ("sci_notation", "1e2"),
        ("non_ascii_digits", "١٠.٠٠"),
        ("10M_allowed_in_close", "10000000.00"),
        ("max_14_2", "999999999999.99"),
        ("over_14_2", "1000000000000.00"),
    ]
    close_form_results = {}
    for label, raw in close_cases:
        form = CashCloseForm(data={"counted_amount": raw})
        ok = form.is_valid()
        close_form_results[label] = {
            "valid": ok,
            "cleaned": str(form.cleaned_data["counted_amount"]) if ok else None,
            "errors": dict(form.errors),
        }
    big_close_res = capture_exc(lambda: close_cash_shift(actor=s1, counted_amount=Decimal("21999999.00")))
    big_shift.refresh_from_db()
    big_close_obj = CashShiftClose.objects.filter(cash_shift=big_shift).first()
    findings["cumulative_money_limit"] = {
        "close_form": close_form_results,
        "big_close_result": big_close_res,
        "expected": str(big_close_obj.expected_amount) if big_close_obj else None,
        "counted": str(big_close_obj.counted_amount) if big_close_obj else None,
        "difference": str(big_close_obj.difference) if big_close_obj else None,
    }

    # ── 4. DB Check Constraints Direct SQL Enforcement (cash_0001..0004) ──────
    db_constraint_tests = {}
    with connection.cursor() as cur:
        for label, sql, params in [
            (
                "neg_opening_amount",
                "INSERT INTO cash_cashshift (id, cash_register_id, seller_id, opening_amount, status, opened_at) VALUES (?, ?, ?, ?, ?, ?)",
                [str(uuid.uuid4()).replace("-", ""), str(reg.pk).replace("-", ""), str(s1.pk).replace("-", ""), "-1.00", "CLOSED", tz.now().isoformat()],
            ),
            (
                "invalid_status",
                "INSERT INTO cash_cashshift (id, cash_register_id, seller_id, opening_amount, status, opened_at) VALUES (?, ?, ?, ?, ?, ?)",
                [str(uuid.uuid4()).replace("-", ""), str(reg.pk).replace("-", ""), str(s1.pk).replace("-", ""), "0.00", "PAUSED", tz.now().isoformat()],
            ),
            (
                "inconsistent_difference",
                "INSERT INTO cash_cashshiftclose (id, cash_shift_id, closed_by_id, counted_amount, expected_amount, difference, closed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    str(uuid.uuid4()).replace("-", ""),
                    str(big_shift.pk).replace("-", ""),
                    str(s1.pk).replace("-", ""),
                    "100.00",
                    "100.00",
                    "5.00",
                    tz.now().isoformat(),
                ],
            ),
            (
                "neg_counted_close",
                "INSERT INTO cash_cashshiftclose (id, cash_shift_id, closed_by_id, counted_amount, expected_amount, difference, closed_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [
                    str(uuid.uuid4()).replace("-", ""),
                    str(big_shift.pk).replace("-", ""),
                    str(s1.pk).replace("-", ""),
                    "-1.00",
                    "0.00",
                    "-1.00",
                    tz.now().isoformat(),
                ],
            ),
        ]:
            def _ins(q=sql, p=params):
                with transaction.atomic():
                    cur.execute(q, p)
            res = capture_exc(_ins)
            db_constraint_tests[label] = (not res["ok"]) and (res["exc_type"] == "IntegrityError")
    findings["db_constraints_sqlite"] = db_constraint_tests

    # ── 5. Pagination (29 shifts), Boundary + Page-2 Tie-Breaking (-opened_at, -id), Filters
    tie_time = datetime(2026, 11, 10, 15, 0, 0, tzinfo=dt_timezone.utc)
    boundary_time = tz.now() - timedelta(days=1)
    b_uuid_low = uuid.UUID("11111111-1111-4000-8000-000000000001")
    b_uuid_high = uuid.UUID("eeeeeeee-eeee-4fff-bfff-ffffffffffff")
    tie_uuid_low = uuid.UUID("00000000-0000-4000-8000-000000000001")
    tie_uuid_high = uuid.UUID("ffffffff-ffff-4fff-bfff-ffffffffffff")

    # 24 newest shifts occupy ranks 1..24 on page 1 (1 big_shift + 23 new shifts)
    for i in range(23):
        actor = s1 if i % 2 == 0 else s2
        sh = open_cash_shift(actor=actor, opening_amount=Decimal("10.00") + i)
        close_cash_shift(actor=actor, counted_amount=Decimal("10.00") + i)

    # 2 shifts tied at boundary_time span position 25 (page 1) and position 26 (page 2)
    for uid, amt, sel in [(b_uuid_low, Decimal("333.33"), s1), (b_uuid_high, Decimal("444.44"), s2)]:
        sh_b = CashShift.objects.create(
            id=uid, cash_register=reg, seller=sel, opening_amount=amt, status=CashShift.Status.CLOSED
        )
        CashShiftClose.objects.create(
            cash_shift=sh_b, closed_by=sel, counted_amount=amt, expected_amount=amt, difference=Decimal("0.00")
        )
    CashShift.objects.filter(pk__in=[b_uuid_low, b_uuid_high]).update(opened_at=boundary_time)

    # 2 older shifts tied on 2026-11-10 appear on page 2 (and together in date filter)
    for uid, amt, sel in [(tie_uuid_low, Decimal("111.11"), s1), (tie_uuid_high, Decimal("222.22"), s2)]:
        sh_t = CashShift.objects.create(
            id=uid, cash_register=reg, seller=sel, opening_amount=amt, status=CashShift.Status.CLOSED
        )
        CashShiftClose.objects.create(
            cash_shift=sh_t, closed_by=sel, counted_amount=amt, expected_amount=amt, difference=Decimal("0.00")
        )
    CashShift.objects.filter(pk__in=[tie_uuid_low, tie_uuid_high]).update(opened_at=tie_time)

    c_adm = Client()
    c_adm.force_login(adm)
    hist_all = safe_get(c_adm, "/caja/turnos/")
    hist_page2 = safe_get(c_adm, "/caja/turnos/?page=2")
    p1_ids = re.findall(r"/caja/turnos/([0-9a-f-]+)/cerrado/", hist_all["body"])
    p2_ids = re.findall(r"/caja/turnos/([0-9a-f-]+)/cerrado/", hist_page2["body"])

    # Check -id tie-breaker both on page 2 (positions 27..28) and in filtered 2026-11-10 view
    hist_filtered_valid = safe_get(c_adm, "/caja/turnos/?fecha_desde=2026-11-10&fecha_hasta=2026-11-10")
    pos_high_p2 = hist_page2["body"].find("222.22") if "222.22" in hist_page2["body"] else hist_page2["body"].find("222,22")
    pos_low_p2 = hist_page2["body"].find("111.11") if "111.11" in hist_page2["body"] else hist_page2["body"].find("111,11")
    pos_high_flt = hist_filtered_valid["body"].find("222.22") if "222.22" in hist_filtered_valid["body"] else hist_filtered_valid["body"].find("222,22")
    pos_low_flt = hist_filtered_valid["body"].find("111.11") if "111.11" in hist_filtered_valid["body"] else hist_filtered_valid["body"].find("111,11")

    # Test extreme date 9999-12-31, repeated GET params, invalid filters, page edge cases, seller3 dropdown
    r_9999_hasta = safe_get(c_adm, "/caja/turnos/?fecha_hasta=9999-12-31")
    r_9999_desde = safe_get(c_adm, "/caja/turnos/?fecha_desde=9999-12-31")
    r_dup_param = safe_get(c_adm, "/caja/turnos/?fecha_desde=2026-11-10&fecha_desde=bad")
    r_dup_param_rev = safe_get(c_adm, "/caja/turnos/?fecha_desde=bad&fecha_desde=2026-11-10")
    r_inverted = safe_get(c_adm, "/caja/turnos/?fecha_desde=2026-11-12&fecha_hasta=2026-11-10")
    r_bad_uuid = safe_get(c_adm, "/caja/turnos/?vendedor=not-a-uuid")
    r_bad_page_nonascii = safe_get(c_adm, "/caja/turnos/?page=٢")
    r_bad_page_out = safe_get(c_adm, "/caja/turnos/?page=99")
    has_s3_unfiltered = "Carla Sin Turnos" in hist_all["body"]
    has_s3_filtered = "Carla Sin Turnos" in hist_filtered_valid["body"]

    # Seller 1 tries filtering by Seller 2 UUID & visiting Seller 2 closed detail
    r_s1_bypass = safe_get(c_s1, f"/caja/turnos/?vendedor={s2.pk}")
    r_s1_s2_closed = safe_get(c_s1, f"/caja/turnos/{tie_uuid_high}/cerrado/")
    r_adm_closed = safe_get(c_adm, f"/caja/turnos/{tie_uuid_high}/cerrado/")
    r_s1_home = safe_get(c_s1, "/inicio/")
    m_h1 = re.search(r"<h1[^>]*>(.*?)</h1>", r_adm_closed["body"], re.S)
    adm_closed_h1_text = re.sub(r"\s+", " ", m_h1.group(1)).strip() if m_h1 else ""
    m_nav = re.search(r'<nav[^>]*id="sidebar-navigation"[^>]*>(.*?)</nav>', r_s1_home["body"], re.S)
    s1_nav_html = m_nav.group(1) if m_nav else ""

    findings["history_and_filters"] = {
        "total_shifts_in_db": CashShift.objects.count(),
        "rendered_rows_page1_of_28": len(p1_ids),
        "rendered_rows_page2_of_28": len(p2_ids),
        "page1_and_page2_disjoint": len(set(p1_ids) & set(p2_ids)) == 0,
        "page1_plus_page2_union_equals_28": len(set(p1_ids) | set(p2_ids)) == 28,
        "boundary_high_on_p1_low_on_p2": (str(b_uuid_high) in p1_ids) and (str(b_uuid_low) in p2_ids),
        "has_pagination_nav": ("page=" in hist_all["body"]) or ("Página" in hist_all["body"]),
        "tie_222_before_111_page2": (pos_high_p2 != -1 and pos_low_p2 != -1 and pos_high_p2 < pos_low_p2),
        "tie_222_before_111_filtered": (pos_high_flt != -1 and pos_low_flt != -1 and pos_high_flt < pos_low_flt),
        "fecha_hasta_9999_12_31": {k: v for k, v in r_9999_hasta.items() if k != "body"},
        "fecha_desde_9999_12_31_status": r_9999_desde["status"],
        "dup_param_last_bad_status": r_dup_param["status"],
        "dup_param_last_bad_has_error": ("No repita el parámetro" in r_dup_param["body"]) and ("No se realizó la consulta" in r_dup_param["body"]),
        "dup_param_last_bad_rows": r_dup_param["body"].count("Ver acta"),
        "dup_param_first_bad_rows": r_dup_param_rev["body"].count("Ver acta"),
        "inverted_status": r_inverted["status"],
        "inverted_rows": r_inverted["body"].count("Ver acta"),
        "bad_uuid_status": r_bad_uuid["status"],
        "bad_uuid_rows": r_bad_uuid["body"].count("Ver acta"),
        "bad_page_nonascii_rows": r_bad_page_nonascii["body"].count("Ver acta"),
        "bad_page_out_rows": r_bad_page_out["body"].count("Ver acta"),
        "bad_page_out_has_warning": "No se realizó la consulta" in r_bad_page_out["body"],
        "seller3_zero_shifts_in_unfiltered_dropdown": has_s3_unfiltered,
        "seller3_zero_shifts_in_filtered_dropdown": has_s3_filtered,
        "s1_filter_s2_contains_beto": "Beto Vendedor" in r_s1_bypass["body"],
        "s1_other_closed_status": r_s1_s2_closed["status"],
        "adm_closed_status": r_adm_closed["status"],
        "adm_closed_h1_text": adm_closed_h1_text,
        "adm_closed_h1_cerrar_turno": adm_closed_h1_text == "Cerrar turno",
        "s1_sidebar_has_cash_history": 'href="/caja/turnos/"' in s1_nav_html,
        "s1_sidebar_has_sales_history": 'href="/ventas/historial/"' in s1_nav_html,
        "s1_sidebar_has_sales_shift": 'href="/ventas/historial/turno/"' in s1_nav_html,
    }

    # ── 6. Open-shift session, logout, employee edit/deactivate, and admin/urls
    open_sh = open_cash_shift(actor=s1, opening_amount=Decimal("25.00"))
    add_product_to_draft(actor=s1, product_id=prod.pk, quantity=2)
    r_logout_get = safe_get(c_s1, "/salir/")
    r_deact_open = capture_exc(lambda: deactivate_employee(actor=adm, account=s1))
    r_role_open = capture_exc(
        lambda: update_employee(
            actor=adm,
            account=s1,
            display_name=s1.display_name,
            email=s1.email,
            role=r_wh,
        )
    )
    # Logout discards draft, preserves open shift
    r_logout_post = safe_post(c_s1, "/salir/", {})
    open_sh.refresh_from_db()
    draft_after_logout = SaleDraft.objects.filter(cash_shift=open_sh, status=SaleDraft.Status.ACTIVE).exists()
    close_cash_shift(actor=s1, counted_amount=Decimal("25.00"))

    # Inspect registered admin models and URL patterns
    registered_models = [f"{m._meta.app_label}.{m.__name__}" for m in django_admin.site._registry]
    cash_urls = sorted(
        str(p.pattern) for p in get_resolver().url_patterns if str(p.pattern).startswith("caja")
    )
    from cash import urls as cash_urlconf
    cash_routes = [f"/caja/{p.pattern}" for p in cash_urlconf.urlpatterns]

    findings["links_and_surface"] = {
        "logout_warns_open_shift": "seguirá ligado" in r_logout_get["body"],
        "logout_warns_active_draft": "venta en preparación" in r_logout_get["body"],
        "logout_post_redirect": r_logout_post["redirect"],
        "open_shift_still_open_after_logout": open_sh.status == CashShift.Status.OPEN,
        "draft_discarded_after_logout": not draft_after_logout,
        "deactivate_blocked_while_open": (not r_deact_open["ok"]) and ("turno de caja abierto" in r_deact_open["message"]),
        "role_change_blocked_while_open": (not r_role_open["ok"]) and ("turno de caja abierto" in r_role_open["message"]),
        "cash_models_in_django_admin": [m for m in registered_models if m.startswith("cash.")],
        "cash_routes_defined": cash_routes,
    }

    end_hashes = {k: digest(ROOT / k) == v for k, v in start_hashes.items()}
    findings["protected_unchanged"] = all(end_hashes.values())

    report_path = out_dir / "probe-results.json"
    report_path.write_text(json.dumps(findings, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"probe_report": str(report_path.relative_to(ROOT)), "protected_unchanged": findings["protected_unchanged"]}, indent=2))
    return 0 if findings["protected_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
