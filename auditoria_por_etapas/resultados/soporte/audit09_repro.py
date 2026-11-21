"""Stage 09 pre-fix reproduction script (isolated SQLite).
Verifies exact current defects, boundary inputs, permissions, and sales links BEFORE edits.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
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


def main() -> int:
    stamp = datetime.now(dt_timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    archived_prefixes = ("etapa00", "etapa01", "etapa02", "etapa03", "etapa04", "etapa05", "etapa06", "etapa07", "etapa09")
    protected = [
        *APP.glob("*.sqlite3"),
        *sorted(p for p in (RESULTS / "datos").rglob("*.sqlite3") if p.parent.name.startswith(archived_prefixes)),
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]
    start_hashes = {str(p.relative_to(ROOT)): digest(p) for p in protected}

    run_dir = RESULTS / "datos" / f"etapa09-repro-{stamp}-{secrets.token_hex(4)}"
    out_dir = RESULTS / "evidencias" / f"09-repro-{stamp}"
    run_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
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

    from django.contrib.auth.models import AnonymousUser
    from django.core.management import call_command
    from django.db import connection
    from django.test import Client
    from django.test.utils import CaptureQueriesContext
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
    from sales.models import SaleDraft
    from sales.services import (
        add_product_to_draft,
        checkout_sale,
        discard_active_draft,
        remove_draft_line,
    )

    r_adm = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    r_wh = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    r_sel = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    pw = "Repro09#Pass123"
    admin = Account.objects.create_user("adm@repro09.invalid", pw, display_name="Admin Repro09", role=r_adm)
    wh = Account.objects.create_user("wh@repro09.invalid", pw, display_name="Almacen Repro09", role=r_wh)
    seller1 = Account.objects.create_user("sel1@repro09.invalid", pw, display_name="Vendedor Uno 09", role=r_sel)
    seller2 = Account.objects.create_user("sel2@repro09.invalid", pw, display_name="Vendedor Dos 09", role=r_sel)
    seller_stale_inact = Account.objects.create_user("selin@repro09.invalid", pw, display_name="Seller Inact", role=r_sel)
    seller_stale_dem = Account.objects.create_user("seldem@repro09.invalid", pw, display_name="Seller Dem", role=r_sel)

    CashRegister.objects.create(code="CAJA-01")
    cat = Category.objects.create(name="Cat Repro 09")
    future = tz.localdate() + timedelta(days=60)
    prod = Product.objects.create(
        category=cat, name="Producto Repro 09", barcode="775090000001", sale_price=Decimal("5.00"), minimum_stock=1
    )
    confirm_initial_load(actor=wh, product=prod, lots=[LotInput("L-R09", 40, Decimal("2.00"), future)])

    report: dict = {"stamp_utc": stamp, "findings": {}, "planning_gaps": {}}

    # 1. Form boundary inputs
    samples = [
        "",
        "   ",
        "-0.01",
        "-0.00",
        "+10.00",
        "10,50",
        "10.50",
        "10.5",
        "0",
        "0.00",
        "١٠",
        "١٠.٥٠",
        "1e5",
        "1e-2",
        "1e-3",
        "NaN",
        "Infinity",
        "-Infinity",
        "1.001",
        "9999999.99",
        "10000000.00",
        "texto",
        "10\x00",
    ]
    form_checks = {}
    for s in samples:
        fo = CashOpeningForm(data={"opening_amount": s})
        fc = CashCloseForm(data={"counted_amount": s})
        form_checks[repr(s)] = {
            "open_valid": fo.is_valid(),
            "open_val": repr(fo.cleaned_data.get("opening_amount")) if fo.is_valid() else {k: list(v) for k, v in fo.errors.items()},
            "close_valid": fc.is_valid(),
            "close_val": repr(fc.cleaned_data.get("counted_amount")) if fc.is_valid() else {k: list(v) for k, v in fc.errors.items()},
        }
    report["findings"]["def09_form_inputs"] = form_checks

    # 2. Empty POST {} with valid CSRF token
    c_sel1 = Client(enforce_csrf_checks=True)
    c_sel1.force_login(seller1)
    tok_open = c_sel1.get("/caja/abrir/").cookies["csrftoken"].value
    r_open_empty = c_sel1.post("/caja/abrir/", data={}, HTTP_X_CSRFTOKEN=tok_open)
    body_open_empty = r_open_empty.content.decode()

    shift_tmp = open_cash_shift(actor=seller1, opening_amount=Decimal("20.00"))
    tok_close = c_sel1.get("/caja/cerrar/").cookies["csrftoken"].value
    r_close_empty = c_sel1.post("/caja/cerrar/", data={}, HTTP_X_CSRFTOKEN=tok_close)
    body_close_empty = r_close_empty.content.decode()
    report["findings"]["def09_01_empty_post_ignored"] = {
        "open_empty_status": r_open_empty.status_code,
        "open_empty_has_error": ("error-list" in body_open_empty or "alert-error" in body_open_empty or "field-error" in body_open_empty),
        "open_empty_shift_count": CashShift.objects.count(),
        "close_empty_status": r_close_empty.status_code,
        "close_empty_has_error": ("error-list" in body_close_empty or "alert-error" in body_close_empty or "field-error" in body_close_empty),
        "close_empty_shift_still_open": CashShift.objects.get(pk=shift_tmp.pk).status == CashShift.Status.OPEN,
    }
    close_cash_shift(actor=seller1, counted_amount=Decimal("20.00"))

    # 3. Direct service validation gaps (open & close)
    def close_any_open():
        for op in CashShift.objects.filter(status=CashShift.Status.OPEN):
            if not CashShiftClose.objects.filter(cash_shift=op).exists():
                CashShiftClose.objects.create(
                    cash_shift=op,
                    counted_amount=op.opening_amount,
                    expected_amount=op.opening_amount,
                    difference=Decimal("0.00"),
                    closed_by=op.seller,
                )
            op.status = CashShift.Status.CLOSED
            op.save(update_fields=["status"])

    Account.objects.filter(pk=seller_stale_inact.pk).update(is_active=False)
    Account.objects.filter(pk=seller_stale_dem.pk).update(role=r_wh)

    def test_open_case(fn):
        close_any_open()
        res = capture_exc(fn)
        open_now = CashShift.objects.filter(status=CashShift.Status.OPEN).first()
        res["opened_amount"] = repr(open_now.opening_amount) if open_now else None
        close_any_open()
        return res

    open_svc = {
        "negative": test_open_case(lambda: open_cash_shift(actor=seller1, opening_amount=Decimal("-0.01"))),
        "neg_zero": test_open_case(lambda: open_cash_shift(actor=seller1, opening_amount=Decimal("-0.00"))),
        "three_decimals": test_open_case(lambda: open_cash_shift(actor=seller1, opening_amount=Decimal("1.005"))),
        "nan": test_open_case(lambda: open_cash_shift(actor=seller1, opening_amount=Decimal("NaN"))),
        "infinity": test_open_case(lambda: open_cash_shift(actor=seller1, opening_amount=Decimal("Infinity"))),
        "over_max": test_open_case(lambda: open_cash_shift(actor=seller1, opening_amount=Decimal("10000000.00"))),
        "float": test_open_case(lambda: open_cash_shift(actor=seller1, opening_amount=10.0)),  # type: ignore[arg-type]
        "bool": test_open_case(lambda: open_cash_shift(actor=seller1, opening_amount=True)),  # type: ignore[arg-type]
        "str": test_open_case(lambda: open_cash_shift(actor=seller1, opening_amount="10.00")),  # type: ignore[arg-type]
        "anon": test_open_case(lambda: open_cash_shift(actor=AnonymousUser(), opening_amount=Decimal("10.00"))),
        "stale_inactive": test_open_case(lambda: open_cash_shift(actor=seller_stale_inact, opening_amount=Decimal("10.00"))),
        "stale_demoted": test_open_case(lambda: open_cash_shift(actor=seller_stale_dem, opening_amount=Decimal("10.00"))),
    }

    def test_close_case(fn):
        close_any_open()
        s = open_cash_shift(actor=seller1, opening_amount=Decimal("50.00"))
        res = capture_exc(fn)
        s.refresh_from_db()
        res["shift_status_after"] = s.status
        close_obj = CashShiftClose.objects.filter(cash_shift=s).first()
        res["saved_counted"] = repr(close_obj.counted_amount) if close_obj else None
        res["saved_diff"] = repr(close_obj.difference) if close_obj else None
        close_any_open()
        return res

    close_any_open()
    s_inact = open_cash_shift(actor=seller1, opening_amount=Decimal("50.00"))
    Account.objects.filter(pk=seller1.pk).update(is_active=False)
    res_close_stale_inact = capture_exc(lambda: close_cash_shift(actor=seller1, counted_amount=Decimal("50.00")))
    Account.objects.filter(pk=seller1.pk).update(is_active=True)
    seller1.refresh_from_db()
    s_inact.refresh_from_db()
    close_any_open()

    s_dem = open_cash_shift(actor=seller2, opening_amount=Decimal("50.00"))
    Account.objects.filter(pk=seller2.pk).update(role=r_wh)
    res_close_stale_dem = capture_exc(lambda: close_cash_shift(actor=seller2, counted_amount=Decimal("50.00")))
    Account.objects.filter(pk=seller2.pk).update(role=r_sel)
    seller2.refresh_from_db()
    s_dem.refresh_from_db()
    close_any_open()

    close_svc = {
        "negative": test_close_case(lambda: close_cash_shift(actor=seller1, counted_amount=Decimal("-10.00"))),
        "neg_zero": test_close_case(lambda: close_cash_shift(actor=seller1, counted_amount=Decimal("-0.00"))),
        "three_decimals": test_close_case(lambda: close_cash_shift(actor=seller1, counted_amount=Decimal("1.005"))),
        "nan": test_close_case(lambda: close_cash_shift(actor=seller1, counted_amount=Decimal("NaN"))),
        "infinity": test_close_case(lambda: close_cash_shift(actor=seller1, counted_amount=Decimal("Infinity"))),
        "over_max": test_close_case(lambda: close_cash_shift(actor=seller1, counted_amount=Decimal("10000000.00"))),
        "float": test_close_case(lambda: close_cash_shift(actor=seller1, counted_amount=50.0)),  # type: ignore[arg-type]
        "bool": test_close_case(lambda: close_cash_shift(actor=seller1, counted_amount=True)),  # type: ignore[arg-type]
        "str": test_close_case(lambda: close_cash_shift(actor=seller1, counted_amount="50.00")),  # type: ignore[arg-type]
        "stale_inactive_actor": {**res_close_stale_inact, "s_inact_status": s_inact.status},
        "stale_demoted_actor": {**res_close_stale_dem, "s_dem_status": s_dem.status},
    }
    report["findings"]["def09_02_service_validation"] = {"open": open_svc, "close": close_svc}

    # Helper for POST with valid session CSRF
    def post_with_csrf(client: Client, url: str, data: dict, get_url: str = "/salir/", follow: bool = False):
        if "csrftoken" not in client.cookies:
            client.get(get_url)
        tok = client.cookies["csrftoken"].value
        return client.post(url, {**data, "csrfmiddlewaretoken": tok}, follow=follow)

    # 4. cash_close view when NO open shift (hidden non_field_errors!)
    r_close_no_shift = post_with_csrf(c_sel1, "/caja/cerrar/", {"counted_amount": "50.00"})
    body_no_shift = r_close_no_shift.content.decode()
    report["findings"]["def09_03_close_no_shift_hidden_error"] = {
        "status": r_close_no_shift.status_code,
        "has_no_open_shift_msg": "No tienes un turno de caja abierto para cerrar." in body_no_shift,
        "has_alert_error": "alert-error" in body_no_shift,
    }

    # 5. cash_close with empty SaleDraft vs 1-line SaleDraft vs removed last line vs discarded
    s_draft = open_cash_shift(actor=seller1, opening_amount=Decimal("30.00"))
    empty_draft = SaleDraft.objects.create(cash_shift=s_draft, seller=seller1, status=SaleDraft.Status.ACTIVE)
    r_close_empty_draft_get = c_sel1.get("/caja/cerrar/")
    body_empty_draft = r_close_empty_draft_get.content.decode()
    r_close_empty_draft_post = post_with_csrf(c_sel1, "/caja/cerrar/", {"counted_amount": "30.00"})
    empty_draft.refresh_from_db()
    s_draft.refresh_from_db()

    # Open again, add line, check block, remove last line, check unblock; add line, discard, check unblock
    close_any_open()
    s_link = open_cash_shift(actor=seller1, opening_amount=Decimal("100.00"))
    d1 = add_product_to_draft(actor=seller1, product_id=prod.pk, quantity=2)
    r_close_with_line = post_with_csrf(c_sel1, "/caja/cerrar/", {"counted_amount": "100.00"})
    line1 = d1.lines.get()
    remove_draft_line(actor=seller1, line_id=line1.pk)
    d1.refresh_from_db()
    d2 = add_product_to_draft(actor=seller1, product_id=prod.pk, quantity=2)
    discard_active_draft(actor=seller1)
    d2.refresh_from_db()

    # Make discounted sale: 2 * 5.00 = 10.00, discount = 2.00 -> total = 8.00, cash_received = 20.00 -> change = 12.00
    d3 = add_product_to_draft(actor=seller1, product_id=prod.pk, quantity=2)
    sale1 = checkout_sale(
        actor=seller1,
        draft_id=d3.pk,
        cash_received=Decimal("20.00"),
        discount_amount=Decimal("2.00"),
        idempotency_key=uuid.uuid4(),
    )

    # Check logout preserves open shift
    r_logout_confirm = c_sel1.get("/salir/")
    tok_out = r_logout_confirm.cookies["csrftoken"].value
    r_logout_post = c_sel1.post("/salir/", {"csrfmiddlewaretoken": tok_out}, follow=False)
    s_link.refresh_from_db()

    # Check identity lock with open shift
    upd_role_blocked = capture_exc(
        lambda: update_employee(
            actor=admin,
            account=seller1,
            display_name=seller1.display_name,
            email=seller1.email,
            role=r_wh,
        )
    )
    deact_blocked = capture_exc(lambda: deactivate_employee(actor=admin, account=seller1))

    # Re-login seller1 and close with SHORTAGE (counted 105.00 vs expected 108.00 -> -3.00)
    c_sel1.force_login(seller1)
    tok_c = c_sel1.get("/caja/cerrar/").cookies["csrftoken"].value
    r_close_ok = c_sel1.post("/caja/cerrar/", {"counted_amount": "105.00", "csrfmiddlewaretoken": tok_c}, follow=False)
    r_close_retry = c_sel1.post("/caja/cerrar/", {"counted_amount": "105.00", "csrfmiddlewaretoken": tok_c}, follow=False)

    # 6. Opened detail view AFTER close + Closed acta CSS .status-error
    r_opened_after_close = c_sel1.get(f"/caja/turnos/{s_link.pk}/abierto/")
    r_closed_acta = c_sel1.get(f"/caja/turnos/{s_link.pk}/cerrado/")
    app_css = (APP / "identity/static/identity/app.css").read_text(encoding="utf-8")

    # 7. @never_cache headers across cash & sales read endpoints
    urls_to_check = [
        "/caja/abrir/",
        "/caja/cerrar/",
        f"/caja/turnos/{s_link.pk}/abierto/",
        f"/caja/turnos/{s_link.pk}/cerrado/",
        "/caja/turnos/",
        f"/ventas/recibo/{sale1.pk}/",
        "/ventas/historial/turno/",
        "/ventas/historial/",
    ]
    cache_headers = {}
    for u in urls_to_check:
        resp = c_sel1.get(u)
        cache_headers[u] = {
            "status": resp.status_code,
            "cache_control": resp.headers.get("Cache-Control", ""),
            "has_no_store": "no-store" in resp.headers.get("Cache-Control", "").lower(),
        }

    # 8. History view (N+1 queries, columns, filters, seller sidebar nav)
    c_adm = Client(enforce_csrf_checks=True)
    c_adm.force_login(admin)
    with CaptureQueriesContext(connection) as q_hist1:
        c_adm.get("/caja/turnos/")
    for _ in range(5):
        open_cash_shift(actor=seller2, opening_amount=Decimal("10.00"))
        close_cash_shift(actor=seller2, counted_amount=Decimal("10.00"))
    with CaptureQueriesContext(connection) as q_hist2:
        r_hist_adm2 = c_adm.get("/caja/turnos/")

    hist_html = r_hist_adm2.content.decode()
    sel_dash_html = c_sel1.get("/inicio/").content.decode()
    all_url_names = sorted(k for k in get_resolver().reverse_dict.keys() if isinstance(k, str))

    report["findings"]["def09_04_empty_draft_banner_mismatch"] = {
        "empty_draft_get_shows_warning": "Tienes una venta en preparación activa" in body_empty_draft,
        "empty_draft_post_status": r_close_empty_draft_post.status_code,
        "empty_draft_shift_status_after_post": s_draft.status,
    }
    report["findings"]["def09_05_opened_page_after_close"] = {
        "status": r_opened_after_close.status_code,
        "claims_abierta": "está abierta" in r_opened_after_close.content.decode(),
        "claims_Abierto": ">Abierto<" in r_opened_after_close.content.decode(),
        "has_preparar_venta_btn": "Ir a preparar venta" in r_opened_after_close.content.decode(),
    }
    report["findings"]["def09_06_missing_status_error_css"] = {
        "acta_has_status_error_class": "status-error" in r_closed_acta.content.decode(),
        "app_css_defines_status_error": ".status-error" in app_css,
    }
    report["findings"]["def09_07_cache_headers"] = cache_headers
    report["findings"]["sales_and_identity_link"] = {
        "with_line_blocks_close": "Hay una venta en preparación con productos" in r_close_with_line.content.decode(),
        "with_line_status": r_close_with_line.status_code,
        "remove_last_line_draft_status": d1.status,
        "discard_draft_status": d2.status,
        "sale_total": str(sale1.total_amount),
        "sale_discount": str(sale1.discount_amount),
        "sale_cash_received": str(sale1.cash_received),
        "close_expected_amount": str(CashShiftClose.objects.get(cash_shift=s_link).expected_amount),
        "close_difference": str(CashShiftClose.objects.get(cash_shift=s_link).difference),
        "close_redirect": r_close_ok.get("Location"),
        "retry_close_status": r_close_retry.status_code,
        "retry_close_shows_msg": "No tienes un turno de caja abierto para cerrar." in r_close_retry.content.decode(),
        "logout_keeps_shift_open": s_link.status == CashShift.Status.OPEN,
        "logout_confirm_mentions_open_shift": "turno abierto" in r_logout_confirm.content.decode().lower(),
        "logout_redirect": r_logout_post.get("Location"),
        "identity_role_change_blocked_open_shift": upd_role_blocked,
        "identity_deactivate_blocked_open_shift": deact_blocked,
    }
    report["findings"]["history_queries_and_ui"] = {
        "queries_with_few_shifts": len(q_hist1),
        "queries_with_plus5_shifts": len(q_hist2),
        "seller_sidebar_has_cash_history": "/caja/turnos/" in sel_dash_html,
        "history_has_back_to_dashboard": "Volver al inicio" in hist_html,
    }
    report["planning_gaps"] = {
        "history_has_total_cobrado_col": "Total cobrado" in hist_html,
        "history_has_filter_form": "<form" in hist_html.lower(),
        "close_view_shows_sales_total": False,
        "cash_url_names": [u for u in all_url_names if "cash" in u or "caja" in u],
    }

    end_hashes = {str(p.relative_to(ROOT)): digest(p) for p in protected}
    report["protected_unchanged"] = all(start_hashes[k] == end_hashes[k] for k in start_hashes)
    (out_dir / "repro.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
