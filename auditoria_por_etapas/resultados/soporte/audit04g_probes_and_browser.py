"""Deep Stage 04 probes (build f99a3999...):
- HTTP/service parity on supplier_toggle (302 on invalid vs duplicate params)
- Cache-Control, X-Request-ID & IdentityAuditEvent (02-E) across all supplier responses
- Unicode/whitespace/LIKE wildcards/Form-vs-Service divergence & multi-field ARIA/autofocus
- Query count (N+1) & payload scaling across 60 suppliers and downstream views
- Real Chrome: keyboard-only flow, Back+Reload after POST 302, 390x844 bounding-box audit, and @media print
Isolated under datos/etapa04-probes-* and evidencias/04-reval-20261114/probes-*.
"""
from __future__ import annotations

import contextlib
import hashlib
import hmac
import io
import json
import logging
import os
import re
import secrets
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
SUPPORT = Path(__file__).resolve().parent
PW_PATH = Path("C:/Users/walte/AppData/Local/Temp/audit14d-browser-6f523915")

if str(PW_PATH) not in sys.path:
    sys.path.insert(0, str(PW_PATH))

from playwright.sync_api import sync_playwright  # noqa: E402


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint_r1_pmv() -> dict:
    exts = {".py", ".html", ".css", ".js", ".svg"}
    h = hashlib.sha256()
    count = 0
    for p in sorted(APP.rglob("*")):
        if not p.is_file():
            continue
        if any(part in {".venv", "__pycache__", ".git"} for part in p.parts):
            continue
        if p.suffix.lower() not in exts:
            continue
        count += 1
        h.update(p.relative_to(APP).as_posix().encode("utf-8"))
        h.update(b"\x00")
        h.update(sha256_file(p).encode("ascii"))
        h.update(b"\n")
    return {"file_count": count, "sha256": h.hexdigest()}


def snapshot_core() -> dict[str, str]:
    targets = [
        APP / "r1_pmv.sqlite3",
        ROOT / "08_Historias_de_Usuario.md",
        ROOT / "07_Reglas_de_Negocio.md",
        ROOT / "09_Product_Backlog.md",
        ROOT / "03_Matriz_de_Trazabilidad_y_Pruebas.md",
    ]
    datos = RESULTS / "datos"
    if datos.exists():
        for db in sorted(datos.glob("etapa04-*/audit.sqlite3")):
            if not db.parent.name.startswith("etapa04-probes-"):
                targets.append(db)
    return {
        str(p.relative_to(ROOT)).replace("\\", "/"): sha256_file(p)
        for p in targets
        if p.exists()
    }


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def verify_proof(base_url: str, secret_key: str, run_name: str) -> dict:
    nonce = secrets.token_hex(32)
    req = urllib.request.Request(
        f"{base_url}/",
        headers={"X-Audit04-Challenge": nonce},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        proof = resp.headers.get("X-Audit04-Proof", "")
        srv_run = resp.headers.get("X-Audit04-Run", "")
    expected = hmac.new(secret_key.encode(), nonce.encode(), hashlib.sha256).hexdigest()
    return {"ok": hmac.compare_digest(proof, expected) and srv_run == run_name, "srv_run": srv_run}


class LogCapture(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records: list[dict] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append({"level": record.levelname, "name": record.name, "msg": record.getMessage()})


def http_req(
    base_url: str,
    method: str,
    path: str,
    cookie_header: str = "",
    csrf_token: str | None = None,
    form_data: list[tuple[str, str]] | None = None,
) -> dict:
    headers: dict[str, str] = {}
    if cookie_header:
        headers["Cookie"] = cookie_header
    data = None
    if method == "POST":
        headers["Referer"] = f"{base_url}/inventario/proveedores/"
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        if csrf_token is not None:
            headers["X-CSRFToken"] = csrf_token
        data = urllib.parse.urlencode(form_data or []).encode("utf-8")
    req = urllib.request.Request(f"{base_url}{path}", data=data, headers=headers, method=method)

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(req, timeout=10) as resp:
            return {
                "status": resp.status,
                "location": resp.headers.get("Location", ""),
                "cache_control": resp.headers.get("Cache-Control", ""),
                "x_request_id": resp.headers.get("X-Request-ID", ""),
                "body": resp.read().decode("utf-8", errors="replace"),
            }
    except urllib.error.HTTPError as err:
        return {
            "status": err.code,
            "location": err.headers.get("Location", ""),
            "cache_control": err.headers.get("Cache-Control", ""),
            "x_request_id": err.headers.get("X-Request-ID", ""),
            "body": err.read().decode("utf-8", errors="replace"),
        }


def run_part_a_server_probes(run_dir: Path) -> dict:
    sys.path.insert(0, str(APP))
    sys.path.insert(0, str(SUPPORT))
    os.environ["AUDIT04_RUN_DIR"] = str(run_dir)
    os.environ["AUDIT04_DEFAULT_COOKIES"] = "1"
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit04_settings"
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    import django

    django.setup()
    from django.core.exceptions import ValidationError
    from django.core.management import call_command
    from django.db import connection
    from django.test import Client
    from django.test.utils import CaptureQueriesContext
    from django.urls import reverse
    from django.utils import timezone as tz

    from catalog.models import Category, Product
    from identity.models import Account, IdentityAuditEvent, Role
    from inventory.forms import SupplierForm
    from inventory.models import InitialInventoryLoad, Lot, StockReceipt, Supplier
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        create_supplier,
        register_stock_entry,
        toggle_supplier_status,
    )

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    r_admin = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    r_wh = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    r_sel = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    creds = {
        "admin": ("admin@probes04.invalid", secrets.token_urlsafe(16) + "A1!", "Admin Probes", r_admin),
        "warehouse": ("wh@probes04.invalid", secrets.token_urlsafe(16) + "A1!", "Almacen Probes", r_wh),
        "seller": ("seller@probes04.invalid", secrets.token_urlsafe(16) + "A1!", "Vendedor Probes", r_sel),
    }
    accounts = {
        k: Account.objects.create_user(email, pw, display_name=name, role=role)
        for k, (email, pw, name, role) in creds.items()
    }

    out: dict = {"findings": [], "probes": {}}

    def rec_finding(fid: str, severity: str, detail: str, data=None):
        out["findings"].append({"id": fid, "severity": severity, "detail": detail, "data": data})

    # 1. Unicode, whitespace, Form-vs-Service & ARIA probes
    sup_base = create_supplier(actor=accounts["admin"], name="Lácteos Andinos EIRL", ruc="20123456789", phone="01 4445566")
    sup_hom = create_supplier(actor=accounts["admin"], name="Distribuidora Sol SAC", ruc="20987654321", phone="")

    c_ad = Client()
    c_ad.force_login(accounts["admin"])

    # Outer spaces in RUC via HTTP POST (CharField strip=True vs Chrome maxlength=11)
    r_ruc_outer_spaces_dup = c_ad.post(reverse("supplier-create"), {"name": "Dup Outer", "ruc": " 20123456789 ", "phone": ""})
    r_ruc_outer_spaces_new = c_ad.post(reverse("supplier-create"), {"name": "Nuevo Outer", "ruc": " 20111222334 ", "phone": ""})
    outer_created = Supplier.objects.filter(ruc="20111222334").exists()
    Supplier.objects.filter(ruc="20111222334").delete()

    # Fullwidth, internal space, superscript in RUC
    ruc_edge_results = {}
    for label, val in [
        ("internal_space", "20123 45678"),
        ("fullwidth_digits", "１２３４５６７８９０１"),
        ("superscript_digits", "²³⁴⁵⁶⁷⁸⁹⁰¹²"),
        ("arabic_indic", "٢٠١٢٣٤٥٦٧٨٩"),
    ]:
        f = SupplierForm(data={"name": "Proveedor Test", "ruc": val, "phone": ""})
        ruc_edge_results[label] = {"form_valid": f.is_valid(), "error": f.errors.get("ruc", [])}

    # Superscript name ("²³"), emoji name ("🏢📦"), tab/NBSP normalization
    f_super_name = SupplierForm(data={"name": "²³", "ruc": "20555666777", "phone": ""})
    f_emoji_name = SupplierForm(data={"name": "🏢📦", "ruc": "20555666778", "phone": ""})
    sup_ctrl_ws = create_supplier(actor=accounts["admin"], name="\tEmpresa\n\xa0SAC ", ruc="20555666779", phone="+51\xa0999\t111")
    ctrl_ws_vals = {"name": sup_ctrl_ws.name, "phone": sup_ctrl_ws.phone}
    sup_ctrl_ws.delete()

    # Phone Arabic digits vs no-digit symbols
    f_phone_arabic = SupplierForm(data={"name": "Tel Test", "ruc": "20555666780", "phone": "٩٩٩١١١٢٢٢"})
    f_phone_empty_syms = SupplierForm(data={"name": "Tel Test", "ruc": "20555666781", "phone": "() - +"})

    # Form vs Service pre-normalize max length divergence
    raw_165_name = "A" + (" " * 10) + ("B" * 154)
    f_long_norm = SupplierForm(data={"name": raw_165_name, "ruc": "20555666782", "phone": ""})
    svc_long_norm_ok = False
    try:
        s_ln = create_supplier(actor=accounts["admin"], name=raw_165_name, ruc="20555666782", phone="")
        svc_long_norm_ok = len(s_ln.name) == 156
        s_ln.delete()
    except ValidationError:
        svc_long_norm_ok = False

    raw_21_phone = ("9" * 10) + "  " + ("9" * 9)  # 21 raw -> 20 collapsed
    f_phone_norm = SupplierForm(data={"name": "Tel Len", "ruc": "20555666783", "phone": raw_21_phone})
    svc_phone_norm_ok = False
    try:
        s_pn = create_supplier(actor=accounts["admin"], name="Tel Len", ruc="20555666783", phone=raw_21_phone)
        svc_phone_norm_ok = len(s_pn.phone) == 20
        s_pn.delete()
    except ValidationError:
        svc_phone_norm_ok = False

    # Multi-field errors & ARIA + autofocus probes
    r_3_err = c_ad.post(reverse("supplier-create"), {"name": "---", "ruc": "123", "phone": "abc"})
    html_3_err = r_3_err.content.decode("utf-8")
    r_phone_only_err = c_ad.post(reverse("supplier-create"), {"name": "Empresa Valida", "ruc": "20888999000", "phone": "abc"})
    html_ph_err = r_phone_only_err.content.decode("utf-8")

    name_tag_3 = re.search(r'<input[^>]*id="id_name"[^>]*>', html_3_err).group(0)
    ruc_tag_3 = re.search(r'<input[^>]*id="id_ruc"[^>]*>', html_3_err).group(0)
    ph_tag_only = re.search(r'<input[^>]*id="id_phone"[^>]*>', html_ph_err).group(0)
    name_tag_ph = re.search(r'<input[^>]*id="id_name"[^>]*>', html_ph_err).group(0)

    out["probes"]["validation_and_a11y"] = {
        "outer_spaces_ruc_dup_status": r_ruc_outer_spaces_dup.status_code,
        "outer_spaces_ruc_dup_msg": "El RUC ya está registrado." in r_ruc_outer_spaces_dup.content.decode("utf-8"),
        "outer_spaces_ruc_http_post_accepted": r_ruc_outer_spaces_new.status_code == 302 and outer_created,
        "ruc_edge_results": ruc_edge_results,
        "superscript_name_23_form_valid": f_super_name.is_valid(),
        "emoji_name_form_valid": f_emoji_name.is_valid(),
        "control_ws_collapsed": ctrl_ws_vals,
        "arabic_phone_form_valid": f_phone_arabic.is_valid(),
        "symbol_phone_form_valid": f_phone_empty_syms.is_valid(),
        "name_form_rejects_raw165_norm156": not f_long_norm.is_valid(),
        "name_service_accepts_raw165_norm156": svc_long_norm_ok,
        "phone_form_rejects_raw21_norm20": not f_phone_norm.is_valid(),
        "phone_service_accepts_raw21_norm20": svc_phone_norm_ok,
        "multi3_err_shows_all_3": all(
            msg in html_3_err
            for msg in [
                "El nombre comercial debe contener letras o números.",
                "El RUC debe contener exactamente 11 dígitos numéricos.",
                "El teléfono debe incluir al menos un dígito",
            ]
        ),
        "multi3_autofocus_on_name_only": ("autofocus" in name_tag_3) and ("autofocus" not in ruc_tag_3) and ("autofocus" not in ph_tag_only),
        "phone_only_autofocus_moves_to_phone": ("autofocus" in ph_tag_only) and ("autofocus" not in name_tag_ph),
        "phone_error_input_has_aria_invalid": 'aria-invalid="true"' in ph_tag_only,
        "phone_error_input_describedby_has_error_id": "id_phone_error" in ph_tag_only,
        "ph_tag_html": ph_tag_only,
    }
    if not out["probes"]["validation_and_a11y"]["phone_error_input_has_aria_invalid"]:
        rec_finding(
            "OBS-04-FORM-NO-ARIA-INVALID-OR-ERROR-DESCRIBEDBY",
            "LOW",
            "supplier_form.html outputs role='alert' divs (#id_*_error) but invalid <input> elements lack aria-invalid='true' and do not include id_*_error in aria-describedby (unlike #supplier-search on supplier_list.html).",
            {"ph_tag_html": ph_tag_only},
        )
    if out["probes"]["validation_and_a11y"]["superscript_name_23_form_valid"]:
        rec_finding(
            "OBS-04-ALNUM-SUPERSCRIPT-NAME",
            "LOW",
            "Python str.isalnum() treats Unicode superscript digits ('²³') as alphanumeric, so name='²³' passes SupplierForm/Supplier.clean/create_supplier despite lacking ordinary letters/ASCII digits.",
        )

    # 2. Search wildcards (%, _, \) & whitespace-only & repeated ?q=
    search_probes = {}
    for lbl, url_qs in [
        ("percent", "?q=%25"),
        ("underscore", "?q=_"),
        ("backslash", "?q=%5C"),
        ("spaces_only", "?q=%20%20%20"),
        ("repeated_q", "?q=L%C3%A1cteos&q=Sol"),
        ("huge_10k", "?q=" + ("X" * 10000)),
    ]:
        r_s = c_ad.get(reverse("supplier-list") + url_qs)
        body = r_s.content.decode("utf-8")
        search_probes[lbl] = {
            "status": r_s.status_code,
            "has_sol": "Distribuidora Sol SAC" in body,
            "has_lacteos": "Lácteos Andinos EIRL" in body,
            "has_clear_btn": 'aria-label="Limpiar búsqueda"' in body,
        }
    out["probes"]["search_edge_cases"] = search_probes

    # 3. supplier_toggle HTTP edge modes (quizas -> 302!, empty -> 302!, conflicting duplicate params!)
    toggle_url = reverse("supplier-toggle", args=(sup_base.pk,))
    r_tog_quizas = c_ad.post(toggle_url, {"is_active": "quizas"})
    sup_base.refresh_from_db()
    r_tog_empty = c_ad.post(toggle_url, {"is_active": ""})
    sup_base.refresh_from_db()
    # Conflicting duplicate keys: QueryDict [("is_active", "false"), ("is_active", "true")] while active!
    # Django TestClient accepts list of values in dict {"is_active": ["false", "true"]}
    sup_base_active_before = sup_base.is_active
    r_tog_dup_false_true = c_ad.post(toggle_url, {"is_active": ["false", "true"]})
    sup_base.refresh_from_db()
    after_false_true = sup_base.is_active
    # Now send ["true", "false"]
    r_tog_dup_true_false = c_ad.post(toggle_url, {"is_active": ["true", "false"]})
    sup_base.refresh_from_db()
    after_true_false = sup_base.is_active
    # Padded uppercase "  TRUE  "
    r_tog_padded_true = c_ad.post(toggle_url, {"is_active": "  TRUE  "})
    sup_base.refresh_from_db()
    after_padded_true = sup_base.is_active
    # Unknown valid UUID & malformed UUID
    r_tog_404_uuid = c_ad.post(reverse("supplier-toggle", args=( "00000000-0000-0000-0000-000000000000", )), {"is_active": "false"})
    r_tog_404_bad = c_ad.post("/inventario/proveedores/no-es-uuid/estado/", {"is_active": "false"})
    r_tog_405_get = c_ad.get(toggle_url)

    out["probes"]["toggle_http_modes"] = {
        "quizas_status": r_tog_quizas.status_code,
        "quizas_location": r_tog_quizas.get("Location", ""),
        "empty_status": r_tog_empty.status_code,
        "dup_false_then_true_status": r_tog_dup_false_true.status_code,
        "dup_false_then_true_result_is_active": after_false_true,
        "dup_true_then_false_status": r_tog_dup_true_false.status_code,
        "dup_true_then_false_result_is_active": after_true_false,
        "padded_uppercase_true_restored": after_padded_true,
        "unknown_uuid_status": r_tog_404_uuid.status_code,
        "invalid_uuid_status": r_tog_404_bad.status_code,
        "get_method_status": r_tog_405_get.status_code,
    }
    if r_tog_dup_true_false.status_code == 302 and after_true_false is False:
        rec_finding(
            "OBS-04-TOGGLE-DUPLICATE-IS-ACTIVE-LAST-WINS",
            "LOW",
            "POST /inventario/proveedores/<uuid>/estado/ uses request.POST.get('is_active'), so duplicate conflicting params (is_active=true&is_active=false) silently obey the last value (302) instead of rejecting ambiguity like MovementFilterForm.",
        )

    # 4. Cache-Control & IdentityAuditEvent (02-E integration)
    log_cap = LogCapture()
    audit_logger = logging.getLogger("identity.audit")
    audit_logger.addHandler(log_cap)
    old_level = audit_logger.level
    audit_logger.setLevel(logging.INFO)
    try:
        db_events_before = IdentityAuditEvent.objects.count()
        c_anon = Client()
        c_wh = Client()
        c_wh.force_login(accounts["warehouse"])
        c_sel = Client()
        c_sel.force_login(accounts["seller"])
        c_csrf = Client(enforce_csrf_checks=True)
        c_csrf.force_login(accounts["admin"])

        header_matrix = {
            "anon_list_302": c_anon.get(reverse("supplier-list")),
            "admin_list_200": c_ad.get(reverse("supplier-list")),
            "admin_create_get_200": c_ad.get(reverse("supplier-create")),
            "admin_create_ok_302": c_ad.post(reverse("supplier-create"), {"name": "Hdr Test", "ruc": "20444333221", "phone": ""}),
            "admin_toggle_quizas_302": c_ad.post(toggle_url, {"is_active": "quizas"}),
            "admin_toggle_get_405": c_ad.get(toggle_url),
            "admin_toggle_404": c_ad.post(reverse("supplier-toggle", args=("00000000-0000-0000-0000-000000000000",)), {"is_active": "false"}),
            "seller_list_403": c_sel.get(reverse("supplier-list")),
            "wh_create_post_403": c_wh.post(reverse("supplier-create"), {"name": "X", "ruc": "20444333222"}),
            "csrf_fail_403": c_csrf.post(reverse("supplier-create"), {"name": "X", "ruc": "20444333223"}),
        }
        Supplier.objects.filter(ruc="20444333221").delete()
        db_events_after = IdentityAuditEvent.objects.count()
    finally:
        audit_logger.removeHandler(log_cap)
        audit_logger.setLevel(old_level)

    headers_summary = {
        k: {
            "status": resp.status_code,
            "cache_control": resp.headers.get("Cache-Control", ""),
            "x_request_id": bool(resp.headers.get("X-Request-ID")),
        }
        for k, resp in header_matrix.items()
    }
    missing_no_store = [
        k for k, info in headers_summary.items()
        if info["status"] in (403, 404, 405, 302) and "no-store" not in info["cache_control"].lower()
    ]
    out["probes"]["headers_and_identity_audit"] = {
        "headers": headers_summary,
        "responses_without_no_store": missing_no_store,
        "identity_audit_db_delta": db_events_after - db_events_before,
        "identity_audit_log_count": len(log_cap.records),
        "identity_audit_log_samples": log_cap.records[:10],
    }
    if missing_no_store:
        rec_finding(
            "OBS-04-HEADERS-NO-STORE-ERROR-REDIRECT",
            "LOW",
            f"Supplier routes apply @never_cache on 200 views, but 403/404/405/anonymous-302 responses lack Cache-Control: no-store: {missing_no_store}.",
            headers_summary,
        )

    # 5. Query Budget / N+1 check across 5 vs 60 suppliers & 12 lots/10 suppliers
    cat = Category.objects.create(name="Escala Audit04")
    p_scale = Product.objects.create(category=cat, name="Producto Escala", barcode="775040499001", sale_price=Decimal("5.50"))
    soon = tz.localdate() + timedelta(days=15)

    def measure_queries(path: str):
        with CaptureQueriesContext(connection) as ctx:
            resp = c_ad.get(path)
        return {"status": resp.status_code, "queries": len(ctx), "bytes": len(resp.content)}

    def measure_wh_queries(path: str):
        with CaptureQueriesContext(connection) as ctx:
            resp = c_wh.get(path)
        return {"status": resp.status_code, "queries": len(ctx), "bytes": len(resp.content)}

    # Seed initial load on p_scale with sup_base, then 10 lots with 10 new suppliers, plus 50 more suppliers
    load = confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_scale,
        lots=[LotInput("SC-INIT-1", 10, Decimal("2.0000"), soon)],
        supplier=sup_base,
    )
    q_small_list = measure_queries(reverse("supplier-list"))
    q_small_exp = measure_queries(reverse("product-expirations") + "?dias=3650")
    q_small_mov = measure_queries(reverse("product-movements", args=(p_scale.pk,)))

    extra_sups = []
    for i in range(58):
        s = create_supplier(actor=accounts["admin"], name=f"Proveedor Escala {i:03d}", ruc=f"209900{i:05d}", phone=f"999000{i:03d}")
        if i % 2 == 1:
            toggle_supplier_status(actor=accounts["admin"], supplier=s, is_active=False)
        extra_sups.append(s)
    for idx in range(10):
        register_stock_entry(
            actor=accounts["warehouse"],
            product=p_scale,
            lots=[LotInput(f"SC-ENT-{idx}", 5, Decimal("2.5000"), soon + timedelta(days=idx + 1))],
            supplier=extra_sups[idx * 2],
            idempotency_key=f"11111111-1111-4111-8111-{idx:012d}",
        )

    q_60_list = measure_queries(reverse("supplier-list"))
    q_60_load_created = measure_queries(reverse("inventory-load-created", args=(load.pk,)))
    q_60_exp = measure_queries(reverse("product-expirations") + "?dias=3650")
    q_60_mov = measure_queries(reverse("product-movements", args=(p_scale.pk,)))
    q_60_entry_form = measure_wh_queries(reverse("stock-entry"))

    out["probes"]["query_scaling_n_plus_1"] = {
        "small_2_suppliers": {"supplier_list": q_small_list, "expirations": q_small_exp, "movements": q_small_mov},
        "scaled_60_suppliers_11_lots": {
            "supplier_list": q_60_list,
            "initial_load_created": q_60_load_created,
            "expirations": q_60_exp,
            "movements": q_60_mov,
            "stock_entry_form": q_60_entry_form,
        },
        "no_n_plus_1_supplier_queries": (
            q_60_list["queries"] == q_small_list["queries"]
            and q_60_exp["queries"] <= q_small_exp["queries"] + 1
            and q_60_mov["queries"] == q_small_mov["queries"]
        ),
    }

    # Keep DB clean with just 3 known suppliers + 1 product for Chrome Part B!
    from inventory.models import InitialLoadLine, StockReceiptLine

    StockReceiptLine.objects.all().delete()
    InitialLoadLine.objects.all().delete()
    Lot.objects.all().delete()
    StockReceipt.objects.all().delete()
    InitialInventoryLoad.objects.all().delete()
    Product.objects.all().delete()
    Category.objects.all().delete()
    Supplier.objects.all().delete()

    # Recreate clean browser fixtures for Part B
    s1 = create_supplier(actor=accounts["admin"], name="Distribuidora Sol SAC", ruc="20123456789", phone="+51 (1) 555-1234")
    s2 = create_supplier(actor=accounts["admin"], name="Distribuidora Sol SAC", ruc="20987654321", phone="")
    toggle_supplier_status(actor=accounts["admin"], supplier=s2, is_active=False)
    s3 = create_supplier(actor=accounts["admin"], name="Lácteos Andinos EIRL", ruc="00123456789", phone="01 4445566")

    cat_b = Category.objects.create(name="Abarrotes Browser04g")
    p_b = Product.objects.create(category=cat_b, name="Aceite Chrome 1L", barcode="775040488001", sale_price=Decimal("8.90"))
    confirm_initial_load(actor=accounts["warehouse"], product=p_b, lots=[LotInput("BR-INIT-1", 10, Decimal("5.0000"), soon)], supplier=s1)
    rcpt_b = register_stock_entry(
        actor=accounts["warehouse"],
        product=p_b,
        lots=[LotInput("BR-ENT-1", 4, Decimal("5.2000"), soon + timedelta(days=10))],
        supplier=s1,
        idempotency_key="22222222-2222-4222-8222-000000000001",
    )
    out["browser_fixtures"] = {
        "admin": {"email": creds["admin"][0], "password": creds["admin"][1]},
        "s1_id": str(s1.pk),
        "s2_id": str(s2.pk),
        "receipt_id": str(rcpt_b.pk),
        "load_id": str(p_b.initial_load.pk),
    }
    return out


def run_part_b_chrome(run_dir: Path, ev_dir: Path, secret_key: str, run_name: str, fixtures: dict) -> dict:
    from inventory.models import Supplier

    shots_dir = ev_dir / "screenshots"
    shots_dir.mkdir(exist_ok=True)
    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env.pop("DJANGO_ALLOW_ASYNC_UNSAFE", None)
    env.update(
        {
            "AUDIT04_RUN_DIR": str(run_dir),
            "AUDIT04_DEFAULT_COOKIES": "0",
            "DJANGO_SETTINGS_MODULE": "audit04_settings",
            "PYTHONPATH": f"{APP}{os.pathsep}{SUPPORT}",
            "PYTHONUTF8": "1",
        }
    )
    server_log = open(ev_dir / "runserver.log", "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, str(APP / "manage.py"), "runserver", f"127.0.0.1:{port}", "--noreload", "--insecure"],
        cwd=str(APP),
        env=env,
        stdout=server_log,
        stderr=subprocess.STDOUT,
        text=True,
    )

    chrome_out: dict = {"checks": [], "console_errors": [], "page_errors": [], "server_500s": [], "layout_metrics": {}, "print_metrics": {}}

    def rec(cid: str, ok: bool, detail):
        chrome_out["checks"].append({"id": cid, "ok": ok, "detail": detail})

    try:
        proof = None
        for _ in range(50):
            try:
                proof = verify_proof(base_url, secret_key, run_name)
                if proof["ok"]:
                    break
            except Exception:
                time.sleep(0.25)
        if not proof or not proof["ok"]:
            raise RuntimeError(f"Live proof failed: {proof}")

        with sync_playwright() as pw:
            chrome_exe = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
            launch_kwargs = {"headless": True}
            if chrome_exe.exists():
                launch_kwargs["executable_path"] = str(chrome_exe)
            browser = pw.chromium.launch(**launch_kwargs)

            def attach(page):
                page.on("console", lambda m: chrome_out["console_errors"].append(m.text) if m.type == "error" else None)
                page.on("pageerror", lambda e: chrome_out["page_errors"].append(str(e)))
                page.on("response", lambda r: chrome_out["server_500s"].append({"url": r.url, "status": r.status}) if r.status >= 500 else None)

            # 1. Desktop 1366x768 Keyboard-only + Focus Shift + Back/Reload after POST 302
            ctx = browser.new_context(viewport={"width": 1366, "height": 768}, locale="es-PE")
            p = ctx.new_page()
            attach(p)
            p.goto(f"{base_url}/", wait_until="networkidle")
            p.locator('input[name="email"]').fill(fixtures["admin"]["email"])
            p.locator('input[name="password"]').fill(fixtures["admin"]["password"])
            with p.expect_navigation(wait_until="networkidle"):
                p.locator('input[name="password"]').press("Enter")

            # Navigate to Proveedores & Nuevo proveedor via keyboard Tab/Enter
            p.locator('#sidebar-navigation a[href="/inventario/proveedores/"]').focus()
            with p.expect_navigation(wait_until="networkidle"):
                p.keyboard.press("Enter")
            p.locator('a[href="/inventario/proveedores/nuevo/"]').focus()
            with p.expect_navigation(wait_until="networkidle"):
                p.keyboard.press("Enter")

            initial_focus = p.evaluate("() => document.activeElement && document.activeElement.id")
            # Type valid name, bad ruc, bad phone using keyboard/focus and press Enter
            p.keyboard.type("Teclado SAC")
            p.keyboard.press("Tab")
            p.keyboard.type("123")
            p.keyboard.press("Tab")
            p.keyboard.type("abc")
            p.locator('input[name="phone"]').press("Enter")
            p.wait_for_load_state("networkidle")

            focus_on_error = p.evaluate("() => document.activeElement && document.activeElement.id")
            preserved_name = p.locator('input[name="name"]').input_value()
            ruc_err_visible = p.locator("#id_ruc_error").inner_text().strip()
            phone_err_visible = p.locator("#id_phone_error").inner_text().strip()

            # Paste outer-space RUC probe
            p.locator('input[name="ruc"]').fill(" 20123456789 ")
            pasted_dom_val = p.locator('input[name="ruc"]').input_value()

            # Fix fields and submit via Enter
            p.locator('input[name="ruc"]').fill("20666555444")
            p.locator('input[name="phone"]').fill("")
            with p.expect_navigation(wait_until="networkidle"):
                p.locator('input[name="ruc"]').press("Enter")
            create_url_after = urllib.parse.urlparse(p.url).path
            flash_after_create = p.locator(".flash-stack").inner_text().strip()
            sup_kbd = Supplier.objects.get(ruc="20666555444")

            # Back after failed POST (no-store) -> valid POST 302 -> list triggers ERR_CACHE_MISS in Chrome
            back_after_failed_post_err = None
            try:
                p.go_back(wait_until="networkidle")
                back_from_list_url = urllib.parse.urlparse(p.url).path
            except Exception as exc:
                back_after_failed_post_err = str(exc).splitlines()[0]
                p.wait_for_timeout(300)
                back_from_list_url = p.url
            p.close()

            # Clean PRG Back + Reload probe on a fresh tab sharing session cookies
            p2 = ctx.new_page()
            attach(p2)
            p2.goto(f"{base_url}/inventario/proveedores/nuevo/", wait_until="networkidle")
            p2.locator('input[name="name"]').fill("Teclado PRG SAC")
            p2.locator('input[name="ruc"]').fill("20666555443")
            with p2.expect_navigation(wait_until="networkidle"):
                p2.locator('input[name="ruc"]').press("Enter")
            p2.go_back(wait_until="networkidle")
            prg_back_url = urllib.parse.urlparse(p2.url).path
            p2.reload(wait_until="networkidle")
            reload_after_back_status_ok = urllib.parse.urlparse(p2.url).path == "/inventario/proveedores/nuevo/"
            prg_count = Supplier.objects.filter(ruc="20666555443").count()

            # Go to list, toggle sup_kbd inactive, then Back + Reload -> confirm NO toggle back!
            p2.goto(f"{base_url}/inventario/proveedores/", wait_until="networkidle")
            with p2.expect_navigation(wait_until="networkidle"):
                p2.locator(f'form[action="/inventario/proveedores/{sup_kbd.pk}/estado/"] button[type="submit"]').click()
            sup_kbd.refresh_from_db()
            state_after_toggle = sup_kbd.is_active
            toggle_back_err = None
            try:
                p2.go_back(wait_until="networkidle")
                p2.reload(wait_until="networkidle")
            except Exception as exc:
                toggle_back_err = str(exc).splitlines()[0]
            sup_kbd.refresh_from_db()
            state_after_back_reload = sup_kbd.is_active

            rec(
                "desktop_keyboard_focus_paste_and_back_reload",
                initial_focus == "id_name"
                and focus_on_error == "id_ruc"
                and preserved_name == "Teclado SAC"
                and "11 dígitos" in ruc_err_visible
                and "al menos un dígito" in phone_err_visible
                and pasted_dom_val == " 2012345678"
                and create_url_after == "/inventario/proveedores/"
                and "Teclado SAC" in flash_after_create
                and prg_back_url == "/inventario/proveedores/nuevo/"
                and reload_after_back_status_ok
                and prg_count == 1
                and (not state_after_toggle)
                and (not state_after_back_reload),
                {
                    "initial_focus": initial_focus,
                    "focus_on_error": focus_on_error,
                    "preserved_name": preserved_name,
                    "pasted_dom_val": pasted_dom_val,
                    "create_url_after": create_url_after,
                    "flash_after_create": flash_after_create,
                    "back_from_list_url": back_from_list_url,
                    "back_after_failed_post_err": back_after_failed_post_err,
                    "prg_back_url": prg_back_url,
                    "prg_count": prg_count,
                    "toggle_back_err": toggle_back_err,
                    "state_after_toggle": state_after_toggle,
                    "state_after_back_reload": state_after_back_reload,
                },
            )

            # 2. @media print check on supplier_list and stock_receipt
            for pname, ppath in [
                ("supplier_list_print", "/inventario/proveedores/"),
                ("stock_receipt_print", f"/inventario/recepciones/{fixtures['receipt_id']}/"),
            ]:
                p2.goto(f"{base_url}{ppath}", wait_until="networkidle")
                p2.emulate_media(media="print")
                pmetrics = p2.evaluate("""() => {
                    const main = document.querySelector('#contenido');
                    const sidebar = document.querySelector('#sidebar-navigation');
                    const csMain = main ? getComputedStyle(main) : null;
                    const csSide = sidebar ? getComputedStyle(sidebar) : null;
                    return {
                        main_display: csMain ? csMain.display : null,
                        sidebar_display: csSide ? csSide.display : null,
                        text_len: main ? main.innerText.trim().length : 0,
                    };
                }""")
                p2.screenshot(path=str(shots_dir / f"{pname}.png"), full_page=True)
                p2.emulate_media(media="screen")
                chrome_out["print_metrics"][pname] = pmetrics

            rec(
                "media_print_visible_content",
                all(v["main_display"] != "none" and v["text_len"] > 50 for v in chrome_out["print_metrics"].values()),
                chrome_out["print_metrics"],
            )
            ctx.close()

            # 3. Mobile 390x844 Detailed Bounding-Box Audit (list, create errors, initial_load_created, stock_receipt)
            ctx_m = browser.new_context(viewport={"width": 390, "height": 844}, locale="es-PE")
            pm = ctx_m.new_page()
            attach(pm)
            pm.goto(f"{base_url}/", wait_until="networkidle")
            pm.locator('input[name="email"]').fill(fixtures["admin"]["email"])
            pm.locator('input[name="password"]').fill(fixtures["admin"]["password"])
            with pm.expect_navigation(wait_until="networkidle"):
                pm.locator('[data-testid="login-form"] button[type="submit"]').click()

            def measure_layout(label: str):
                dims = pm.evaluate("""() => {
                    const winW = window.innerWidth;
                    const docW = document.documentElement.scrollWidth;
                    const nav = document.querySelector('.sidebar-nav');
                    const navRect = nav ? nav.getBoundingClientRect() : null;
                    const navItems = Array.from(document.querySelectorAll('.sidebar-nav .nav-item'));
                    const clippedNavItems = navItems.filter(el => el.getBoundingClientRect().right > winW + 1).map(el => ({
                        text: el.innerText.trim(), right: Math.round(el.getBoundingClientRect().right)
                    }));
                    const mainClipped = Array.from(document.querySelectorAll('#contenido h2, #contenido a, #contenido button, #contenido input'))
                        .filter(el => el.getBoundingClientRect().width > 0 && el.getBoundingClientRect().right > winW + 1)
                        .map(el => ({ tag: el.tagName, text: (el.innerText || el.id || '').trim().slice(0, 40), right: Math.round(el.getBoundingClientRect().right) }));
                    const tr = document.querySelector('.table-responsive, .table-wrap');
                    return {
                        winW,
                        docW,
                        doc_overflow: docW > winW,
                        nav_scrollW: nav ? nav.scrollWidth : null,
                        nav_clientW: nav ? nav.clientWidth : null,
                        nav_right: navRect ? Math.round(navRect.right) : null,
                        clipped_nav_items_count: clippedNavItems.length,
                        clipped_nav_items: clippedNavItems.slice(0, 5),
                        clipped_main_elements: mainClipped,
                        table_scrollW: tr ? tr.scrollWidth : null,
                        table_clientW: tr ? tr.clientWidth : null,
                    };
                }""")
                chrome_out["layout_metrics"][label] = dims
                pm.screenshot(path=str(shots_dir / f"mobile_{label}.png"), full_page=True)

            pm.goto(f"{base_url}/inventario/proveedores/", wait_until="networkidle")
            measure_layout("supplier_list")

            pm.goto(f"{base_url}/inventario/proveedores/nuevo/", wait_until="networkidle")
            pm.locator('input[name="name"]').fill("---")
            pm.locator('input[name="ruc"]').fill("123")
            pm.locator('input[name="phone"]').fill("abc")
            pm.locator('[data-testid="supplier-form"] button[type="submit"]').click()
            pm.wait_for_load_state("networkidle")
            measure_layout("supplier_create_errors")

            pm.goto(f"{base_url}/inventario/cargas/{fixtures['load_id']}/", wait_until="networkidle")
            measure_layout("initial_load_created")

            pm.goto(f"{base_url}/inventario/recepciones/{fixtures['receipt_id']}/", wait_until="networkidle")
            measure_layout("stock_receipt")

            ctx_m.close()

            rec(
                "mobile_390x844_main_and_doc_no_overflow",
                all(
                    (not v["doc_overflow"]) and (len(v["clipped_main_elements"]) == 0)
                    for v in chrome_out["layout_metrics"].values()
                ),
                chrome_out["layout_metrics"],
            )

            browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        server_log.close()

    return chrome_out


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_name = f"etapa04-probes-{stamp}"
    run_dir = (RESULTS / "datos" / run_name).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    ev_dir = (RESULTS / "evidencias" / "04-reval-20261114" / f"probes-{stamp}").resolve()
    ev_dir.mkdir(parents=True, exist_ok=True)

    secret_key = secrets.token_urlsafe(48)
    (run_dir / ".django-key").write_text(secret_key, encoding="utf-8")
    (run_dir / "marker.json").write_text(json.dumps({"run": run_name, "created_utc": stamp}), encoding="utf-8")

    before_core = snapshot_core()
    build_before = fingerprint_r1_pmv()

    part_a = run_part_a_server_probes(run_dir)
    part_b = run_part_b_chrome(run_dir, ev_dir, secret_key, run_name, part_a.pop("browser_fixtures"))

    after_core = snapshot_core()
    build_after = fingerprint_r1_pmv()
    core_changed = [k for k in sorted(before_core) if before_core[k] != after_core.get(k)]

    report = {
        "stamp_utc": stamp,
        "build_before": build_before,
        "build_after": build_after,
        "build_unchanged": build_before == build_after,
        "protected_core_unchanged": len(core_changed) == 0,
        "protected_core_changed": core_changed,
        "part_a_server_and_orm": part_a,
        "part_b_chrome": part_b,
    }
    report_path = ev_dir / "probes-report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "report": str(report_path.relative_to(ROOT)).replace("\\", "/"),
                "build_sha256": build_after["sha256"],
                "build_unchanged": report["build_unchanged"],
                "protected_core_unchanged": report["protected_core_unchanged"],
                "findings": part_a["findings"],
                "chrome_checks": [(c["id"], c["ok"]) for c in part_b["checks"]],
                "console_errors": len(part_b["console_errors"]),
                "page_errors": len(part_b["page_errors"]),
                "server_500s": len(part_b["server_500s"]),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    ok = (
        report["build_unchanged"]
        and report["protected_core_unchanged"]
        and all(c["ok"] for c in part_b["checks"])
        and len(part_b["page_errors"]) == 0
        and len(part_b["server_500s"]) == 0
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
