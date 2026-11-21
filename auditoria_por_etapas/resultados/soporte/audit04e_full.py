"""Isolated Stage 04 full browser + HTTP verification on the current build (2026-11-14).

Reads/writes ONLY a dedicated marker-verified directory under resultados/datos/etapa04-reval-*
and writes evidence JSON + screenshots under resultados/evidencias/04-reval-20261114/.
Never touches r1_pmv.sqlite3 or prior audit SQLite files.
"""
from __future__ import annotations

import contextlib
import hashlib
import hmac
import io
import json
import os
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


def protected_hashes() -> dict[str, str]:
    targets = [APP / "r1_pmv.sqlite3", ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx"]
    datos = RESULTS / "datos"
    if datos.exists():
        for db in sorted(datos.glob("*/audit.sqlite3")):
            if not db.parent.name.startswith("etapa04-reval-"):
                targets.append(db)
    return {
        str(p.relative_to(ROOT)).replace("\\", "/"): sha256_file(p)
        for p in targets
        if p.exists()
    }


def compare_protected(before_hashes: dict[str, str], after_hashes: dict[str, str]) -> dict:
    changed = [
        {"path": k, "before": before_hashes[k], "after": after_hashes[k]}
        for k in sorted(before_hashes)
        if k in after_hashes and before_hashes[k] != after_hashes[k]
    ]
    deleted = [k for k in sorted(before_hashes) if k not in after_hashes]
    new_concurrent = [k for k in sorted(after_hashes) if k not in before_hashes]
    core_ok = (before_hashes.get("r1-pmv/r1_pmv.sqlite3") == after_hashes.get("r1-pmv/r1_pmv.sqlite3")) and not changed and not deleted
    return {
        "protected_unchanged": core_ok and len(before_hashes) > 0,
        "changed": changed,
        "deleted": deleted,
        "new_concurrent_external_dbs": new_concurrent,
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
        cache_ctrl = resp.headers.get("Cache-Control", "")
    expected = hmac.new(secret_key.encode(), nonce.encode(), hashlib.sha256).hexdigest()
    return {
        "ok": hmac.compare_digest(proof, expected) and srv_run == run_name,
        "srv_run": srv_run,
        "cache_control_login": cache_ctrl,
    }


def setup_isolated_db(run_dir: Path) -> dict:
    sys.path.insert(0, str(APP))
    sys.path.insert(0, str(SUPPORT))
    os.environ["AUDIT04_RUN_DIR"] = str(run_dir)
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit04_settings"
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
    import django

    django.setup()
    from django.core.management import call_command
    from django.utils import timezone as tz
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.services import LotInput, confirm_initial_load

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    creds = {}
    accounts = {}
    for key, email, display, role in [
        ("admin", "admin@audit04e.invalid", "Admin Principal", admin_role),
        ("admin_b", "adminb@audit04e.invalid", "Admin Revisor", admin_role),
        ("admin_rev", "revoked@audit04e.invalid", "Admin Revocable", admin_role),
        ("warehouse", "almacen@audit04e.invalid", "Almacenero Turno", wh_role),
        ("seller", "vendedor@audit04e.invalid", "Vendedor Caja", seller_role),
    ]:
        pw = secrets.token_urlsafe(18) + "A1!"
        creds[key] = {"email": email, "password": pw, "display_name": display}
        accounts[key] = Account.objects.create_user(email, pw, display_name=display, role=role)

    cat = Category.objects.create(name="Abarrotes Audit04e")
    p_init_opt = Product.objects.create(
        category=cat, name="Arroz Costeño 750g", barcode="775040410001", sale_price=Decimal("4.80")
    )
    p_init_hom = Product.objects.create(
        category=cat, name="Leche Evaporada 400g", barcode="775040410002", sale_price=Decimal("4.20")
    )
    p_sub = Product.objects.create(
        category=cat, name="Aceite Vegetal 1L", barcode="775040410003", sale_price=Decimal("9.80")
    )
    soon = tz.localdate() + timedelta(days=15)
    later = tz.localdate() + timedelta(days=45)
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_sub,
        lots=[LotInput("L-BASE-01", 5, Decimal("6.0000"), soon)],
    )
    return {
        "creds": creds,
        "products": {
            "p_init_opt": {"id": str(p_init_opt.pk), "name": p_init_opt.name},
            "p_init_hom": {"id": str(p_init_hom.pk), "name": p_init_hom.name},
            "p_sub": {"id": str(p_sub.pk), "name": p_sub.name},
        },
        "soon": soon.isoformat(),
        "later": later.isoformat(),
    }


def login_page(page, base_url: str, cred: dict) -> None:
    page.goto(f"{base_url}/", wait_until="networkidle")
    page.locator('input[name="email"]').fill(cred["email"])
    page.locator('input[name="password"]').fill(cred["password"])
    with page.expect_navigation(wait_until="networkidle"):
        page.locator('[data-testid="login-form"] button[type="submit"]').click()


def fill_first_lot(page, number: str, qty: str, cost: str, exp_iso: str) -> None:
    card = page.locator(".lot-card").first
    card.locator('input[name$="-number"]').fill(number)
    card.locator('input[name$="-quantity"]').fill(qty)
    card.locator('input[name$="-unit_cost"]').fill(cost)
    card.locator('input[name$="-expiration_date"]').fill(exp_iso)


def post_raw_form(base_url: str, cookie_header: str, csrf_token: str | None, path: str, form_data: list[tuple[str, str]]) -> dict:
    body = urllib.parse.urlencode(form_data).encode("utf-8")
    headers = {
        "Cookie": cookie_header,
        "Referer": f"{base_url}/inventario/proveedores/",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    if csrf_token is not None:
        headers["X-CSRFToken"] = csrf_token
    req = urllib.request.Request(f"{base_url}{path}", data=body, headers=headers, method="POST")

    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    opener = urllib.request.build_opener(NoRedirect())
    try:
        with opener.open(req, timeout=10) as resp:
            return {"status": resp.status, "location": resp.headers.get("Location", ""), "body": resp.read().decode("utf-8", errors="replace")}
    except urllib.error.HTTPError as err:
        return {"status": err.code, "location": err.headers.get("Location", ""), "body": err.read().decode("utf-8", errors="replace")}


def get_raw(base_url: str, cookie_header: str | None, path: str) -> dict:
    headers = {}
    if cookie_header:
        headers["Cookie"] = cookie_header
    req = urllib.request.Request(f"{base_url}{path}", headers=headers, method="GET")

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
                "body": resp.read().decode("utf-8", errors="replace"),
            }
    except urllib.error.HTTPError as err:
        return {
            "status": err.code,
            "location": err.headers.get("Location", ""),
            "cache_control": err.headers.get("Cache-Control", ""),
            "body": err.read().decode("utf-8", errors="replace"),
        }


def context_cookie_header(context) -> tuple[str, str]:
    cookies = context.cookies()
    pairs = [f"{c['name']}={c['value']}" for c in cookies]
    csrf = next((c["value"] for c in cookies if c["name"] == "audit04_csrftoken"), "")
    return "; ".join(pairs), csrf


def snapshot_db(base_info: dict) -> dict:
    from inventory.models import InitialInventoryLoad, Lot, StockReceipt, Supplier
    from identity.models import Account
    from django.contrib.sessions.models import Session

    return {
        "suppliers": [
            {
                "id": str(s.pk),
                "name": s.name,
                "ruc": s.ruc,
                "phone": s.phone,
                "is_active": s.is_active,
            }
            for s in Supplier.objects.order_by("name", "ruc")
        ],
        "loads": [
            {
                "id": str(l.pk),
                "product": l.product.name,
                "lot_supplier_ids": [
                    str(sid) if sid else None
                    for sid in l.lots.order_by("number").values_list("supplier_id", flat=True)
                ],
                "supplier_snapshot_name": l.supplier_snapshot_name,
                "supplier_snapshot_ruc": l.supplier_snapshot_ruc,
            }
            for l in InitialInventoryLoad.objects.select_related("product").order_by("confirmed_at")
        ],
        "receipts": [
            {
                "correlative": r.correlative,
                "product": r.product.name,
                "supplier_id": str(r.supplier_id) if r.supplier_id else None,
                "supplier_snapshot_name": r.supplier_snapshot_name,
                "supplier_snapshot_ruc": r.supplier_snapshot_ruc,
            }
            for r in StockReceipt.objects.select_related("product").order_by("correlative")
        ],
        "lots_count": Lot.objects.count(),
        "session_count": Session.objects.count(),
        "revoked_active": Account.objects.get(email=base_info["creds"]["admin_rev"]["email"]).is_active,
    }


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_name = f"etapa04-reval-{stamp}"
    run_dir = (RESULTS / "datos" / run_name).resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    ev_dir = (RESULTS / "evidencias" / "04-reval-20261114" / f"browser-{stamp}").resolve()
    ev_dir.mkdir(parents=True, exist_ok=True)
    shots_dir = ev_dir / "screenshots"
    shots_dir.mkdir(exist_ok=True)

    secret_key = secrets.token_urlsafe(48)
    (run_dir / ".django-key").write_text(secret_key, encoding="utf-8")
    (run_dir / "marker.json").write_text(json.dumps({"run": run_name, "created_utc": stamp}), encoding="utf-8")

    before_hashes = protected_hashes()
    setup_info = setup_isolated_db(run_dir)
    from catalog.models import Product
    from identity.models import Account
    from identity.services import deactivate_employee
    from inventory.models import InitialInventoryLoad, Lot, StockReceipt, Supplier

    port = free_port()
    base_url = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env.pop("DJANGO_ALLOW_ASYNC_UNSAFE", None)
    env.update(
        {
            "AUDIT04_RUN_DIR": str(run_dir),
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

    report = {
        "stamp_utc": stamp,
        "run_dir": str(run_dir.relative_to(ROOT)).replace("\\", "/"),
        "base_url": base_url,
        "checks": [],
        "observations": [],
        "defects_reproduced": [],
        "console_errors": [],
        "page_errors": [],
        "server_500s": [],
    }

    def rec(check_id: str, ok: bool, detail):
        report["checks"].append({"id": check_id, "ok": ok, "detail": detail})

    try:
        # Wait for runserver
        proof_result = None
        for _ in range(50):
            try:
                proof_result = verify_proof(base_url, secret_key, run_name)
                if proof_result["ok"]:
                    break
            except Exception:
                time.sleep(0.25)
        if not proof_result or not proof_result["ok"]:
            raise RuntimeError(f"Live server proof failed: {proof_result}")
        rec("isolation_hmac_proof", True, proof_result)

        with sync_playwright() as pw:
            chrome_exe = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")
            launch_kwargs = {"headless": True}
            if chrome_exe.exists():
                launch_kwargs["executable_path"] = str(chrome_exe)
            browser = pw.chromium.launch(**launch_kwargs)

            def new_ctx(viewport=(1366, 900)):
                ctx = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]})
                page = ctx.new_page()
                page.on("console", lambda msg: report["console_errors"].append({"url": page.url, "text": msg.text}) if msg.type == "error" else None)
                page.on("pageerror", lambda err: report["page_errors"].append({"url": page.url, "err": str(err)}))
                page.on("response", lambda resp: report["server_500s"].append({"url": resp.url, "status": resp.status}) if resp.status >= 500 else None)
                return ctx, page

            # 1. Anonymous redirects + Cache-Control
            anon_list = get_raw(base_url, None, "/inventario/proveedores/")
            anon_new = get_raw(base_url, None, "/inventario/proveedores/nuevo/")
            anon_post = post_raw_form(base_url, "", None, "/inventario/proveedores/nuevo/", [("name", "X"), ("ruc", "20111111111")])
            rec(
                "anon_redirects",
                anon_list["status"] == 302 and anon_new["status"] == 302 and anon_post["status"] in (302, 403),
                {
                    "list": {k: anon_list[k] for k in ("status", "location")},
                    "new": {k: anon_new[k] for k in ("status", "location")},
                    "post_no_csrf": {k: anon_post[k] for k in ("status", "location")},
                },
            )

            # 2. Empty state in browser (ALMACENERO + ADMIN)
            ctx_wh, p_wh = new_ctx()
            login_page(p_wh, base_url, setup_info["creds"]["warehouse"])
            wh_nav = [a.inner_text().strip() for a in p_wh.locator("#sidebar-navigation .nav-item").all()]
            p_wh.locator('#sidebar-navigation a[href="/inventario/proveedores/"]').click()
            p_wh.wait_for_load_state("networkidle")
            wh_empty_text = p_wh.locator("#contenido").inner_text()
            wh_has_new_btn = p_wh.locator('a[href="/inventario/proveedores/nuevo/"]').count()
            wh_has_toggle_btn = p_wh.locator('form[action$="/estado/"]').count()
            p_wh.screenshot(path=str(shots_dir / "01_warehouse_empty_list.png"), full_page=True)
            rec(
                "warehouse_readonly_empty_list",
                any("Proveedores" in item for item in wh_nav)
                and ("No hay proveedores registrados." in wh_empty_text)
                and wh_has_new_btn == 0
                and wh_has_toggle_btn == 0,
                {"nav": wh_nav, "new_btn": wh_has_new_btn, "toggle_forms": wh_has_toggle_btn},
            )

            # ALMACENERO denied routes
            wh_cookie, wh_csrf = context_cookie_header(ctx_wh)
            wh_get_new = get_raw(base_url, wh_cookie, "/inventario/proveedores/nuevo/")
            wh_post_new = post_raw_form(
                base_url,
                wh_cookie,
                wh_csrf,
                "/inventario/proveedores/nuevo/",
                [("csrfmiddlewaretoken", wh_csrf), ("name", "X"), ("ruc", "20111111111")],
            )
            rec(
                "warehouse_create_denied_403",
                wh_get_new["status"] == 403 and wh_post_new["status"] == 403 and Supplier.objects.count() == 0,
                {"get_status": wh_get_new["status"], "post_status": wh_post_new["status"]},
            )

            # 3. VENDEDOR completely denied + absent from sidebar/dashboard
            ctx_sel, p_sel = new_ctx()
            login_page(p_sel, base_url, setup_info["creds"]["seller"])
            sel_nav = [a.inner_text().strip() for a in p_sel.locator("#sidebar-navigation .nav-item").all()]
            sel_cookie, sel_csrf = context_cookie_header(ctx_sel)
            sel_get_list = get_raw(base_url, sel_cookie, "/inventario/proveedores/")
            sel_get_new = get_raw(base_url, sel_cookie, "/inventario/proveedores/nuevo/")
            rec(
                "seller_no_nav_and_403",
                ("Proveedores" not in sel_nav) and sel_get_list["status"] == 403 and sel_get_new["status"] == 403,
                {"nav": sel_nav, "get_list": sel_get_list["status"], "get_new": sel_get_new["status"]},
            )
            ctx_sel.close()

            # 4. ADMIN flows + validations + CSRF + form/service whitespace probe
            ctx_ad, p_ad = new_ctx()
            login_page(p_ad, base_url, setup_info["creds"]["admin"])
            ad_nav = [a.inner_text().strip() for a in p_ad.locator("#sidebar-navigation .nav-item").all()]
            p_ad.locator('#sidebar-navigation a[href="/inventario/proveedores/"]').click()
            p_ad.wait_for_load_state("networkidle")
            ad_headers = [th.inner_text().strip() for th in p_ad.locator("table thead th").all()]
            ad_empty_text = p_ad.locator("#contenido").inner_text()
            cache_list = get_raw(base_url, context_cookie_header(ctx_ad)[0], "/inventario/proveedores/")["cache_control"]

            # Navigate to create
            p_ad.locator('a[href="/inventario/proveedores/nuevo/"]').click()
            p_ad.wait_for_load_state("networkidle")
            ad_create_text = p_ad.locator("#contenido").inner_text()
            report["ui_literals"] = {"supplier_create_text": ad_create_text, "admin_list_headers": ad_headers, "admin_empty_text": ad_empty_text, "wh_empty_text": wh_empty_text}
            focus_initial = p_ad.evaluate("() => document.activeElement && document.activeElement.id")
            sunat_disclaimer_ok = ("formato" in ad_create_text.lower()) and ("sunat" in ad_create_text.lower()) and ("validado sunat" not in ad_create_text.lower())

            # Empty submit
            p_ad.locator('[data-testid="supplier-form"] button[type="submit"]').click()
            p_ad.wait_for_load_state("networkidle")
            err_empty_text = p_ad.locator("#contenido").inner_text()
            focus_after_empty = p_ad.evaluate("() => document.activeElement && document.activeElement.id")

            # Browser validation variants (no browser maxlength truncation) + inspect HTML maxlength attrs
            maxlens = p_ad.evaluate("""() => ({
                name: document.querySelector('input[name="name"]')?.getAttribute('maxlength'),
                ruc: document.querySelector('input[name="ruc"]')?.getAttribute('maxlength'),
                phone: document.querySelector('input[name="phone"]')?.getAttribute('maxlength'),
            })""")
            ui_variants = [
                ("unicode_ruc", "Proveedor Uno", "٢٠١٢٣٤٥٦٧٨٩", "999111222"),
                ("ruc_10_digits", "Proveedor Uno", "2012345678", ""),
                ("ruc_letters", "Proveedor Uno", "2012345678A", ""),
                ("symbols_name", "---", "20123456789", ""),
                ("letters_phone", "Proveedor Uno", "20123456789", "abc"),
                ("symbols_phone", "Proveedor Uno", "20123456789", "+--()"),
            ]
            variant_results = {}
            for vname, nm, ruc, ph in ui_variants:
                p_ad.locator('input[name="name"]').fill(nm)
                p_ad.locator('input[name="ruc"]').fill(ruc)
                p_ad.locator('input[name="phone"]').fill(ph)
                p_ad.locator('[data-testid="supplier-form"] button[type="submit"]').click()
                p_ad.wait_for_load_state("networkidle")
                errs = [e.inner_text().strip() for e in p_ad.locator(".errorlist, .invalid-feedback, .error-list, .alert-danger, .alert-error, .text-danger").all()]
                focus_id = p_ad.evaluate("() => document.activeElement && document.activeElement.id")
                variant_results[vname] = {"url": p_ad.url, "errors": errs, "focus": focus_id, "count": Supplier.objects.count()}

            # Direct authenticated HTTP POST variants (bypasses browser maxlength to test server validation)
            ad_cookie, ad_csrf = context_cookie_header(ctx_ad)
            http_variants = [
                ("ruc_12_digits_http", "Proveedor Uno", "201234567890", ""),
                ("name_161_http", "A" * 161, "20123456789", ""),
                ("phone_21_http", "Proveedor Uno", "20123456789", "1" * 21),
                ("name_collapsed_156_raw_165_http", "A" + (" " * 10) + ("B" * 154), "20123456789", ""),
                ("phone_collapsed_13_raw_22_http", "Proveedor Uno", "20123456789", "1" + (" " * 10) + ("2" * 11)),
                ("nul_name_http", "Prov\x00Nul", "20123456789", ""),
            ]
            http_variant_results = {}
            for vname, nm, ruc, ph in http_variants:
                res = post_raw_form(
                    base_url, ad_cookie, ad_csrf, "/inventario/proveedores/nuevo/",
                    [("csrfmiddlewaretoken", ad_csrf), ("name", nm), ("ruc", ruc), ("phone", ph)],
                )
                http_variant_results[vname] = {"status": res["status"], "count": Supplier.objects.count()}
            bad_csrf_create = post_raw_form(
                base_url, ad_cookie, "invalid_token", "/inventario/proveedores/nuevo/",
                [("csrfmiddlewaretoken", "invalid_token"), ("name", "Prov Bad Csrf"), ("ruc", "20123456789"), ("phone", "")],
            )
            rec(
                "create_validations_and_csrf",
                Supplier.objects.count() == 0
                and bad_csrf_create["status"] == 403
                and sunat_disclaimer_ok
                and focus_initial == "id_name"
                and focus_after_empty == "id_name"
                and all(v["count"] == 0 and len(v["errors"]) >= 1 for v in variant_results.values())
                and all(v["status"] == 200 and v["count"] == 0 for v in http_variant_results.values()),
                {
                    "maxlengths": maxlens,
                    "focus_initial": focus_initial,
                    "focus_after_empty": focus_after_empty,
                    "sunat_disclaimer_ok": sunat_disclaimer_ok,
                    "cache_list": cache_list,
                    "bad_csrf_status": bad_csrf_create["status"],
                    "variant_results": variant_results,
                    "http_variant_results": http_variant_results,
                },
            )
            if http_variant_results["name_collapsed_156_raw_165_http"]["status"] == 200 or http_variant_results["phone_collapsed_13_raw_22_http"]["status"] == 200:
                report["observations"].append({
                    "id": "OBS-04-FORM-MAXLEN-PRE-NORMALIZE",
                    "detail": "SupplierForm rejects inputs whose raw length exceeds 160/20 due to internal spaces even when normalized length is <= 160/20; create_supplier() service accepts normalized length. Also browser HTML maxlength=11/160/20 silently truncates pasted oversizes instead of warning.",
                    "maxlengths": maxlens,
                    "http_variant_results": http_variant_results,
                })

            # Probe pasting RUC with leading/trailing spaces into maxlength=11 browser input
            p_ad.locator('input[name="name"]').fill("Proveedor Espacio")
            p_ad.locator('input[name="ruc"]').fill(" 20123456789 ")
            truncated_ruc_val = p_ad.locator('input[name="ruc"]').input_value()
            if truncated_ruc_val != "20123456789":
                report["observations"].append({
                    "id": "OBS-04-RUC-PASTE-MAXLENGTH-TRUNCATION",
                    "detail": "HTML maxlength=11 on input[name='ruc'] silently truncates pasted ' 20123456789 ' (leading space) to '" + truncated_ruc_val + "' before submit, causing false 10-digit failure (or cutting last digit).",
                    "pasted_value": " 20123456789 ",
                    "dom_input_value": truncated_ruc_val,
                })

            # Create Supplier S1 with clean 11-digit RUC + extra spaces in name & phone
            p_ad.locator('input[name="name"]').fill("  Distribuidora   Sol   SAC  ")
            p_ad.locator('input[name="ruc"]').fill("20123456789")
            p_ad.locator('input[name="phone"]').fill(" +51  (1)  555-1234 ")
            p_ad.screenshot(path=str(shots_dir / "02_create_valid_form.png"), full_page=True)
            with p_ad.expect_navigation(wait_until="networkidle"):
                p_ad.locator('[data-testid="supplier-form"] button[type="submit"]').click()
            s1 = Supplier.objects.get(ruc="20123456789")

            # Create S2 (homonym "Distribuidora Sol SAC", RUC 20987654321, no phone)
            p_ad.goto(f"{base_url}/inventario/proveedores/nuevo/", wait_until="networkidle")
            p_ad.locator('input[name="name"]').fill("Distribuidora Sol SAC")
            p_ad.locator('input[name="ruc"]').fill("20987654321")
            p_ad.locator('input[name="phone"]').fill("")
            with p_ad.expect_navigation(wait_until="networkidle"):
                p_ad.locator('[data-testid="supplier-form"] button[type="submit"]').click()
            s2 = Supplier.objects.get(ruc="20987654321")

            # Create S3 (leading-zero RUC "00123456789", accented name)
            p_ad.goto(f"{base_url}/inventario/proveedores/nuevo/", wait_until="networkidle")
            p_ad.locator('input[name="name"]').fill("Lácteos Andinos EIRL")
            p_ad.locator('input[name="ruc"]').fill("00123456789")
            p_ad.locator('input[name="phone"]').fill("01 4445566")
            with p_ad.expect_navigation(wait_until="networkidle"):
                p_ad.locator('[data-testid="supplier-form"] button[type="submit"]').click()
            s3 = Supplier.objects.get(ruc="00123456789")

            # Duplicate RUC via browser + double submit probe via direct concurrent/sequential POST
            p_ad.goto(f"{base_url}/inventario/proveedores/nuevo/", wait_until="networkidle")
            p_ad.locator('input[name="name"]').fill("Otro Nombre")
            p_ad.locator('input[name="ruc"]').fill("20123456789")
            p_ad.locator('[data-testid="supplier-form"] button[type="submit"]').click()
            p_ad.wait_for_load_state("networkidle")
            dup_ruc_text = p_ad.locator("#contenido").inner_text()
            rec(
                "create_homonyms_leading_zero_and_dup",
                s1.name == "Distribuidora Sol SAC"
                and s1.phone == "+51 (1) 555-1234"
                and s2.name == "Distribuidora Sol SAC"
                and s2.phone == ""
                and s3.ruc == "00123456789"
                and "El RUC ya está registrado." in dup_ruc_text
                and Supplier.objects.count() == 3,
                {"s1": [s1.name, s1.ruc, s1.phone], "s2": [s2.name, s2.ruc, s2.phone], "s3": [s3.name, s3.ruc]},
            )

            # 5. List & Search (name, collapsed spaces, RUC, homonyms, empty, NUL, accent probe, long query)
            p_ad.goto(f"{base_url}/inventario/proveedores/", wait_until="networkidle")
            p_ad.screenshot(path=str(shots_dir / "03_admin_list_3_suppliers.png"), full_page=True)
            rows_all = [r.inner_text().strip() for r in p_ad.locator("table tbody tr").all()]

            # Search collapsed spaces
            p_ad.locator("#supplier-search").fill("Distribuidora   Sol")
            p_ad.locator('#contenido form button[type="submit"]').first.click()
            p_ad.wait_for_load_state("networkidle")
            rows_hom = [r.inner_text().strip() for r in p_ad.locator("table tbody tr").all()]

            # Search partial RUC
            p_ad.locator("#supplier-search").fill("20987654")
            p_ad.locator('#contenido form button[type="submit"]').first.click()
            p_ad.wait_for_load_state("networkidle")
            rows_ruc = [r.inner_text().strip() for r in p_ad.locator("table tbody tr").all()]

            # Search clear button
            p_ad.locator('a[aria-label="Limpiar búsqueda"]').click()
            p_ad.wait_for_load_state("networkidle")
            rows_cleared = p_ad.locator("table tbody tr").count()

            # Accent probe "Lacteos" vs "Lácteos Andinos EIRL"
            p_ad.locator("#supplier-search").fill("Lacteos")
            p_ad.locator('#contenido form button[type="submit"]').first.click()
            p_ad.wait_for_load_state("networkidle")
            rows_accent_probe = p_ad.locator("table tbody tr").count()

            # NUL search
            p_ad.goto(f"{base_url}/inventario/proveedores/?q=%00", wait_until="networkidle")
            nul_err_el = p_ad.locator("#supplier-search-error")
            nul_aria_inv = p_ad.locator("#supplier-search").get_attribute("aria-invalid")
            nul_rows = p_ad.locator("table tbody tr").count()
            nul_text = nul_err_el.inner_text().strip() if nul_err_el.count() else ""
            p_ad.screenshot(path=str(shots_dir / "04_search_nul_error.png"), full_page=True)

            # Long query 500 chars
            long_q = get_raw(base_url, ad_cookie, "/inventario/proveedores/?q=" + ("X" * 500))
            rec(
                "search_and_nul_guard",
                len(rows_all) == 3
                and len(rows_hom) == 2
                and len(rows_ruc) == 1
                and rows_cleared == 3
                and nul_rows == 0
                and nul_aria_inv == "true"
                and "La búsqueda contiene caracteres no válidos." in nul_text
                and long_q["status"] == 200,
                {
                    "rows_all": len(rows_all),
                    "rows_hom": len(rows_hom),
                    "rows_ruc": len(rows_ruc),
                    "rows_accent_probe_unaccented": rows_accent_probe,
                    "nul_text": nul_text,
                    "long_q_status": long_q["status"],
                },
            )

            # 6. Toggle state + Two-tab stale idempotency + OMITTED is_active BUG check + HU-PROV-03 404
            p_ad.goto(f"{base_url}/inventario/proveedores/", wait_until="networkidle")
            # Inspect rendered toggle form HTML for s2
            s2_form = p_ad.locator(f'form[action="/inventario/proveedores/{s2.pk}/estado/"]')
            s2_hidden_val = s2_form.locator('input[name="is_active"]').get_attribute("value")
            report["ui_literals"]["admin_list_text_with_rows"] = p_ad.locator("#contenido").inner_text()
            report["ui_literals"]["toggle_form_html"] = s2_form.evaluate("el => el.outerHTML")
            has_confirm_page = False  # direct submit on list

            # Double-POST supplier-create replay check (non-idempotent create protected by RUC unique)
            ad_cookie_dbl, ad_csrf_dbl = context_cookie_header(ctx_ad)
            dbl_1 = post_raw_form(
                base_url, ad_cookie_dbl, ad_csrf_dbl, "/inventario/proveedores/nuevo/",
                [("csrfmiddlewaretoken", ad_csrf_dbl), ("name", "Doble Clic SAC"), ("ruc", "20777777771"), ("phone", "")],
            )
            dbl_2 = post_raw_form(
                base_url, ad_cookie_dbl, ad_csrf_dbl, "/inventario/proveedores/nuevo/",
                [("csrfmiddlewaretoken", ad_csrf_dbl), ("name", "Doble Clic SAC"), ("ruc", "20777777771"), ("phone", "")],
            )
            dbl_count = Supplier.objects.filter(ruc="20777777771").count()
            # Clean up extra supplier before continuing row assertions (or note 4 suppliers!)
            Supplier.objects.filter(ruc="20777777771").delete()
            report["double_submit_create"] = {
                "first_status": dbl_1["status"],
                "second_status": dbl_2["status"],
                "second_has_dup_error": "El RUC ya está registrado." in dbl_2["body"],
                "db_count_before_cleanup": dbl_count,
            }

            # Open second tab as Admin BEFORE toggling s2
            p_ad_tab2 = ctx_ad.new_page()
            p_ad_tab2.goto(f"{base_url}/inventario/proveedores/", wait_until="networkidle")

            # Tab 1 deactivates s2
            with p_ad.expect_navigation(wait_until="networkidle"):
                s2_form.locator('button[type="submit"]').click()
            s2.refresh_from_db()
            tab1_flash = p_ad.locator(".flash-stack").inner_text().strip()

            # Tab 2 (stale) clicks Desactivar on s2 (posts is_active=false again)
            with p_ad_tab2.expect_navigation(wait_until="networkidle"):
                p_ad_tab2.locator(f'form[action="/inventario/proveedores/{s2.pk}/estado/"] button[type="submit"]').click()
            s2.refresh_from_db()
            tab2_flash = p_ad_tab2.locator(".flash-stack").inner_text().strip()
            p_ad_tab2.close()

            # Duplicate RUC against INACTIVE s2
            p_ad.goto(f"{base_url}/inventario/proveedores/nuevo/", wait_until="networkidle")
            p_ad.locator('input[name="name"]').fill("Reuso RUC Inactivo")
            p_ad.locator('input[name="ruc"]').fill("20987654321")
            p_ad.locator('[data-testid="supplier-form"] button[type="submit"]').click()
            p_ad.wait_for_load_state("networkidle")
            dup_inactive_err = p_ad.locator("#contenido").inner_text()

            # Refresh cookies after nav
            ad_cookie, ad_csrf = context_cookie_header(ctx_ad)
            # Invalid is_active value "quizas" -> should reject cleanly
            toggle_invalid = post_raw_form(
                base_url, ad_cookie, ad_csrf, f"/inventario/proveedores/{s2.pk}/estado/",
                [("csrfmiddlewaretoken", ad_csrf), ("is_active", "quizas")],
            )
            s2.refresh_from_db()
            s2_after_invalid = s2.is_active

            # OMITTED is_active value -> test against DEC-04-RUC-VALIDACION/C-02!
            s2_before_omitted = s2.is_active
            toggle_omitted = post_raw_form(
                base_url, ad_cookie, ad_csrf, f"/inventario/proveedores/{s2.pk}/estado/",
                [("csrfmiddlewaretoken", ad_csrf)],
            )
            s2.refresh_from_db()
            s2_after_omitted = s2.is_active
            if s2_after_omitted != s2_before_omitted:
                report["defects_reproduced"].append({
                    "id": "DEF-04-DEC04-C02-OMIT-TARGET",
                    "severity": "HIGH",
                    "contract": "DEC-04-RUC-VALIDACION/C-02 & CP-HU-PROV-04-001",
                    "detail": f"POST /inventario/proveedores/{s2.pk}/estado/ omitting 'is_active' returned HTTP {toggle_omitted['status']} and MUTATED is_active from {s2_before_omitted} to {s2_after_omitted}.",
                })
                # Restore s2 back to False explicitly for downstream inactive tests
                post_raw_form(
                    base_url, ad_cookie, ad_csrf, f"/inventario/proveedores/{s2.pk}/estado/",
                    [("csrfmiddlewaretoken", ad_csrf), ("is_active", "false")],
                )
                s2.refresh_from_db()

            # Warehouse 403 on toggle + HU-PROV-03 edit routes 404
            wh_cookie, wh_csrf = context_cookie_header(ctx_wh)
            wh_toggle = post_raw_form(
                base_url, wh_cookie, wh_csrf, f"/inventario/proveedores/{s2.pk}/estado/",
                [("csrfmiddlewaretoken", wh_csrf), ("is_active", "true")],
            )
            edit_404_1 = get_raw(base_url, ad_cookie, f"/inventario/proveedores/{s2.pk}/editar/")["status"]
            edit_404_2 = get_raw(base_url, ad_cookie, f"/inventario/proveedores/{s2.pk}/")["status"]
            toggle_get_405 = get_raw(base_url, ad_cookie, f"/inventario/proveedores/{s2.pk}/estado/")["status"]

            rec(
                "toggle_idempotent_invalid_and_perms",
                s2_hidden_val == "false"
                and (not s2.is_active)
                and "ya se encontraba inactivo" in tab2_flash
                and "El RUC ya está registrado." in dup_inactive_err
                and (not s2_after_invalid)
                and toggle_invalid["status"] == 302
                and wh_toggle["status"] == 403
                and edit_404_1 == 404
                and edit_404_2 == 404
                and toggle_get_405 == 405,
                {
                    "tab1_flash": tab1_flash,
                    "tab2_flash": tab2_flash,
                    "s2_before_omitted": s2_before_omitted,
                    "s2_after_omitted": s2_after_omitted,
                    "toggle_omitted_http": toggle_omitted["status"],
                    "wh_toggle_status": wh_toggle["status"],
                    "edit_404": [edit_404_1, edit_404_2],
                    "toggle_get_405": toggle_get_405,
                    "has_confirmation_step": has_confirm_page,
                },
            )

            # 7. Cross-module: ALMACENERO dropdowns, stale deactivation in BOTH initial_load & stock_entry, sentinel preservation
            # First activate s2 explicitly so ALMACENERO can open forms and select s2!
            p_ad.goto(f"{base_url}/inventario/proveedores/", wait_until="networkidle")
            with p_ad.expect_navigation(wait_until="networkidle"):
                p_ad.locator(f'form[action="/inventario/proveedores/{s2.pk}/estado/"] button[type="submit"]').click()
            s2.refresh_from_db()

            # ALMACENERO opens initial_load and stock_entry, verifies active homonyms distinct in select, selects s2
            p_wh.goto(f"{base_url}/inventario/carga-inicial/", wait_until="networkidle")
            init_options = [o.inner_text().strip() for o in p_wh.locator('select[name="supplier"] option').all()]
            p_wh.locator('select[name="product"]').select_option(setup_info["products"]["p_init_opt"]["id"])
            p_wh.locator('select[name="supplier"]').select_option(str(s2.pk))
            fill_first_lot(p_wh, "LI-STALE-1", "5", "2.50", setup_info["soon"])

            p_wh_entry = ctx_wh.new_page()
            p_wh_entry.goto(f"{base_url}/inventario/entrada/", wait_until="networkidle")
            entry_options = [o.inner_text().strip() for o in p_wh_entry.locator('select[name="supplier"] option').all()]
            p_wh_entry.locator('select[name="product"]').select_option(setup_info["products"]["p_sub"]["id"])
            p_wh_entry.locator('select[name="supplier"]').select_option(str(s2.pk))
            fill_first_lot(p_wh_entry, "LE-STALE-1", "4", "6.20", setup_info["later"])

            # Concurrent ADMIN deactivates s2
            p_ad.goto(f"{base_url}/inventario/proveedores/", wait_until="networkidle")
            with p_ad.expect_navigation(wait_until="networkidle"):
                p_ad.locator(f'form[action="/inventario/proveedores/{s2.pk}/estado/"] button[type="submit"]').click()
            s2.refresh_from_db()

            # ALMACENERO submits stale initial_load -> MUST reject with sentinel, 0 loads created for p_init_opt
            p_wh.locator('[data-testid="inventory-load-form"] button[type="submit"]').click()
            p_wh.wait_for_load_state("networkidle")
            init_err_text = p_wh.locator("#contenido").inner_text()
            init_sentinel_val = p_wh.locator('select[name="supplier"]').input_value()
            p_wh.screenshot(path=str(shots_dir / "05_initial_load_stale_supplier_sentinel.png"), full_page=True)
            # Blind 2nd submit without changing supplier -> STILL rejected!
            p_wh.locator('[data-testid="inventory-load-form"] button[type="submit"]').click()
            p_wh.wait_for_load_state("networkidle")
            init_blind_err_text = p_wh.locator("#contenido").inner_text()
            init_still_no_load = not InitialInventoryLoad.objects.filter(product_id=setup_info["products"]["p_init_opt"]["id"]).exists()

            # ALMACENERO submits stale stock_entry -> MUST reject with sentinel, 0 receipts created
            p_wh_entry.locator('[data-testid="stock-entry-form"] button[type="submit"]').click()
            p_wh_entry.wait_for_load_state("networkidle")
            entry_err_text = p_wh_entry.locator("#contenido").inner_text()
            entry_sentinel_val = p_wh_entry.locator('select[name="supplier"]').input_value()
            # Blind 2nd submit -> STILL rejected!
            p_wh_entry.locator('[data-testid="stock-entry-form"] button[type="submit"]').click()
            p_wh_entry.wait_for_load_state("networkidle")
            entry_blind_err_text = p_wh_entry.locator("#contenido").inner_text()
            entry_still_no_receipt = StockReceipt.objects.count() == 0

            # Recover p_init_opt with "Sin proveedor asignado" ("")
            p_wh.locator('select[name="supplier"]').select_option("")
            with p_wh.expect_navigation(wait_until="networkidle"):
                p_wh.locator('[data-testid="inventory-load-form"] button[type="submit"]').click()
            load_none_url = p_wh.url
            load_none_text = p_wh.locator("#contenido").inner_text()

            # Recover p_sub stock_entry with active S1 (20123456789) -> redirects to /inventario/recepciones/<uuid>/
            p_wh_entry.locator('select[name="supplier"]').select_option(str(s1.pk))
            with p_wh_entry.expect_navigation(wait_until="networkidle"):
                p_wh_entry.locator('[data-testid="stock-entry-form"] button[type="submit"]').click()
            rcpt_s1_url = p_wh_entry.url
            rcpt_s1_text = p_wh_entry.locator("#contenido").inner_text()
            p_wh_entry.screenshot(path=str(shots_dir / "06_stock_receipt_s1.png"), full_page=True)
            p_wh_entry.close()

            rec(
                "stale_inactive_rejected_and_sentinel_preserved",
                init_still_no_load
                and entry_still_no_receipt
                and init_sentinel_val == f"__inactive__:{s2.pk}"
                and entry_sentinel_val == f"__inactive__:{s2.pk}"
                and ("está inactivo" in init_err_text)
                and ("está inactivo" in init_blind_err_text)
                and ("está inactivo" in entry_err_text)
                and ("está inactivo" in entry_blind_err_text)
                and ("Sin proveedor asignado" in load_none_text)
                and ("/inventario/recepciones/" in rcpt_s1_url)
                and ("Distribuidora Sol SAC" in rcpt_s1_text and "20123456789" in rcpt_s1_text),
                {
                    "init_options": init_options,
                    "entry_options": entry_options,
                    "init_sentinel": init_sentinel_val,
                    "entry_sentinel": entry_sentinel_val,
                    "load_none_url": load_none_url,
                    "rcpt_s1_url": rcpt_s1_url,
                },
            )

            # 8. Homonym & Inactive Historical Visibility Audit across:
            #    initial_load_created, stock_receipt, product_movements (Kardex), product_expirations
            # Temporarily activate s2, create initial load on p_init_hom with S1 AND stock entry on p_init_hom with S2, then deactivate s2!
            p_ad.goto(f"{base_url}/inventario/proveedores/", wait_until="networkidle")
            with p_ad.expect_navigation(wait_until="networkidle"):
                p_ad.locator(f'form[action="/inventario/proveedores/{s2.pk}/estado/"] button[type="submit"]').click()

            p_wh.goto(f"{base_url}/inventario/carga-inicial/", wait_until="networkidle")
            p_wh.locator('select[name="product"]').select_option(setup_info["products"]["p_init_hom"]["id"])
            p_wh.locator('select[name="supplier"]').select_option(str(s1.pk))
            fill_first_lot(p_wh, "HOM-L1", "8", "3.00", setup_info["soon"])
            with p_wh.expect_navigation(wait_until="networkidle"):
                p_wh.locator('[data-testid="inventory-load-form"] button[type="submit"]').click()
            hom_load_url = p_wh.url
            hom_load_text = p_wh.locator("#contenido").inner_text()

            p_wh.goto(f"{base_url}/inventario/entrada/", wait_until="networkidle")
            p_wh.locator('select[name="product"]').select_option(setup_info["products"]["p_init_hom"]["id"])
            p_wh.locator('select[name="supplier"]').select_option(str(s2.pk))
            fill_first_lot(p_wh, "HOM-L2", "6", "3.50", setup_info["later"])
            with p_wh.expect_navigation(wait_until="networkidle"):
                p_wh.locator('[data-testid="stock-entry-form"] button[type="submit"]').click()
            hom_rcpt_s2_url = p_wh.url

            # Deactivate s2 again (now S2 is INACTIVE and historical!)
            p_ad.goto(f"{base_url}/inventario/proveedores/", wait_until="networkidle")
            with p_ad.expect_navigation(wait_until="networkidle"):
                p_ad.locator(f'form[action="/inventario/proveedores/{s2.pk}/estado/"] button[type="submit"]').click()
            s2.refresh_from_db()

            # Check initial_load_created, stock_receipt (inactive S2), Kardex product_movements, product_expirations as ADMIN
            p_ad.goto(hom_load_url, wait_until="networkidle")
            ad_hom_load_text = p_ad.locator("#contenido").inner_text()
            p_ad.screenshot(path=str(shots_dir / "07_initial_load_homonym_s1.png"), full_page=True)

            p_ad.goto(hom_rcpt_s2_url, wait_until="networkidle")
            ad_hom_rcpt_s2_text = p_ad.locator("#contenido").inner_text()
            p_ad.screenshot(path=str(shots_dir / "08_stock_receipt_inactive_homonym_s2.png"), full_page=True)

            p_ad.goto(f"{base_url}/inventario/productos/{setup_info['products']['p_init_hom']['id']}/movimientos/", wait_until="networkidle")
            ad_kardex_text = p_ad.locator("#contenido").inner_text()
            ad_kardex_rows = [r.inner_text().strip() for r in p_ad.locator("table tbody tr").all()]
            p_ad.screenshot(path=str(shots_dir / "09_kardex_homonyms_missing_ruc.png"), full_page=True)

            # Also verify ALMACENERO cross-role visibility (list with Inactivo, receipt with inactive S2, Kardex, Expirations)
            p_wh.goto(f"{base_url}/inventario/proveedores/", wait_until="networkidle")
            wh_populated_text = p_wh.locator("#contenido").inner_text()
            wh_populated_headers = [th.inner_text().strip() for th in p_wh.locator("table thead th").all()]
            report["ui_literals"]["warehouse_populated_headers"] = wh_populated_headers
            report["ui_literals"]["warehouse_populated_text"] = wh_populated_text
            p_wh.screenshot(path=str(shots_dir / "12_warehouse_list_with_homonyms_inactive.png"), full_page=True)
            p_wh.goto(hom_rcpt_s2_url, wait_until="networkidle")
            wh_rcpt_s2_ok = ("Distribuidora Sol SAC" in p_wh.locator("#contenido").inner_text()) and ("20987654321" in p_wh.locator("#contenido").inner_text())
            report["ui_literals"]["wh_rcpt_s2_visible"] = wh_rcpt_s2_ok

            p_ad.goto(f"{base_url}/productos/vencimientos/?dias=3650", wait_until="networkidle")
            ad_exp_text = p_ad.locator("#contenido").inner_text()
            ad_exp_rows = [r.inner_text().strip() for r in p_ad.locator("table tbody tr").all()]
            p_ad.screenshot(path=str(shots_dir / "10_expirations_homonyms_missing_ruc.png"), full_page=True)

            kardex_distinguishes_ruc = ("20123456789" in ad_kardex_text) and ("20987654321" in ad_kardex_text)
            exp_distinguishes_ruc = ("20123456789" in ad_exp_text) and ("20987654321" in ad_exp_text)
            if not kardex_distinguishes_ruc or not exp_distinguishes_ruc:
                report["defects_reproduced"].append({
                    "id": "DEF-04-DEC04-C01-HOMONYMS-NO-RUC-CROSSMODULE",
                    "severity": "MEDIUM",
                    "contract": "DEC-04-RUC-VALIDACION/C-01",
                    "detail": "Homonymous suppliers ('Distribuidora Sol SAC', RUC 20123456789 vs 20987654321) are NOT distinguished by RUC in Kardex (/inventario/productos/<id>/movimientos/) or Expirations (/productos/vencimientos/).",
                    "kardex_has_rucs": kardex_distinguishes_ruc,
                    "expirations_has_rucs": exp_distinguishes_ruc,
                })

            rec(
                "downstream_historical_visibility_and_homonyms",
                ("Distribuidora Sol SAC" in ad_hom_load_text and "20123456789" in ad_hom_load_text)
                and ("Distribuidora Sol SAC" in ad_hom_rcpt_s2_text and "20987654321" in ad_hom_rcpt_s2_text),
                {
                    "hom_load_has_s1_ruc": "20123456789" in ad_hom_load_text,
                    "hom_rcpt_s2_has_s2_ruc": "20987654321" in ad_hom_rcpt_s2_text,
                    "kardex_has_rucs": kardex_distinguishes_ruc,
                    "expirations_has_rucs": exp_distinguishes_ruc,
                    "kardex_rows": ad_kardex_rows,
                    "exp_rows": ad_exp_rows,
                },
            )

            # 9. Mobile 390x844 layout & scrollWidth checks
            ctx_mob, p_mob = new_ctx((390, 844))
            login_page(p_mob, base_url, setup_info["creds"]["admin"])
            mob_results = {}
            for name, url_path in [
                ("supplier_list", "/inventario/proveedores/"),
                ("supplier_create", "/inventario/proveedores/nuevo/"),
                ("stock_receipt", urllib.parse.urlparse(hom_rcpt_s2_url).path),
            ]:
                p_mob.goto(f"{base_url}{url_path}", wait_until="networkidle")
                dims = p_mob.evaluate("() => ({ docW: document.documentElement.scrollWidth, winW: window.innerWidth })")
                mob_results[name] = {**dims, "no_horizontal_overflow": dims["docW"] <= dims["winW"]}
                p_mob.screenshot(path=str(shots_dir / f"11_mobile_{name}.png"), full_page=True)
            ctx_mob.close()
            rec(
                "mobile_390x844_viewport",
                all(v["no_horizontal_overflow"] for v in mob_results.values()),
                mob_results,
            )

            # 10. Logout + Back button protection
            p_ad.goto(f"{base_url}/inventario/proveedores/", wait_until="networkidle")
            with p_ad.expect_navigation(wait_until="networkidle"):
                p_ad.locator(".sidebar-logout").click()
            with p_ad.expect_navigation(wait_until="networkidle"):
                p_ad.locator('#contenido form button[type="submit"]').click()
            post_logout_url = p_ad.url
            p_ad.go_back(wait_until="networkidle")
            back_url = p_ad.url
            # Try reloading after logout
            p_ad.reload(wait_until="networkidle")
            reload_url = p_ad.url
            rec(
                "logout_and_back_button",
                urllib.parse.urlparse(post_logout_url).path == "/"
                and "/inventario/proveedores/" not in urllib.parse.urlparse(reload_url).path
                and urllib.parse.urlparse(reload_url).path == "/",
                {"post_logout": post_logout_url, "after_back": back_url, "after_reload": reload_url},
            )
            ctx_ad.close()
            ctx_wh.close()

            # 11. Revoked ADMIN session in live browser (04-D check on current build)
            ctx_rev, p_rev = new_ctx()
            login_page(p_rev, base_url, setup_info["creds"]["admin_rev"])
            p_rev.goto(f"{base_url}/inventario/proveedores/nuevo/", wait_until="networkidle")
            # Revoke admin_rev via service
            operator = Account.objects.get(email=setup_info["creds"]["admin_b"]["email"])
            target = Account.objects.get(email=setup_info["creds"]["admin_rev"]["email"])
            deactivate_employee(actor=operator, account=target)
            suppliers_before_rev_post = Supplier.objects.count()
            p_rev.locator('input[name="name"]').fill("Proveedor Bloqueado")
            p_rev.locator('input[name="ruc"]').fill("20555555551")
            p_rev.locator('[data-testid="supplier-form"] button[type="submit"]').click()
            p_rev.wait_for_load_state("networkidle")
            rev_final_url = p_rev.url
            suppliers_after_rev_post = Supplier.objects.count()
            ctx_rev.close()
            rec(
                "revoked_admin_browser_session_blocked",
                suppliers_after_rev_post == suppliers_before_rev_post and urllib.parse.urlparse(rev_final_url).path == "/",
                {"final_url": rev_final_url, "suppliers_before": suppliers_before_rev_post, "suppliers_after": suppliers_after_rev_post},
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

    after_hashes = protected_hashes()
    prot_check = compare_protected(before_hashes, after_hashes)
    report["protected_unchanged"] = prot_check["protected_unchanged"]
    report["protected_detail"] = prot_check
    report["db_snapshot"] = snapshot_db(setup_info)
    report["summary"] = {
        "total_checks": len(report["checks"]),
        "passed_checks": sum(1 for c in report["checks"] if c["ok"]),
        "failed_checks": [c["id"] for c in report["checks"] if not c["ok"]],
        "defects_reproduced_count": len(report["defects_reproduced"]),
        "console_errors": len(report["console_errors"]),
        "page_errors": len(report["page_errors"]),
        "server_500s": len(report["server_500s"]),
    }
    (ev_dir / "browser-checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"evidence": str(ev_dir.relative_to(ROOT)).replace("\\", "/"), **report["summary"], "protected_unchanged": report["protected_unchanged"], "defects_reproduced": report["defects_reproduced"], "observations": report["observations"]}, ensure_ascii=False, indent=2))
    return 0 if report["protected_unchanged"] and not report["summary"]["failed_checks"] and report["summary"]["server_500s"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
