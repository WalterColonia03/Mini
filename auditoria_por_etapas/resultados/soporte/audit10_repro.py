"""Stage 10 baseline reproduction against UNMODIFIED code (SQLite, PostgreSQL 18.4, and Chrome).
Tests HU-VEN-01a/RN-22 absence, HU-VEN-04 gaps, search/form/view/service/layout defects,
without ever loading .env or altering protected SQLite databases.
"""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
SUPPORT = Path(__file__).resolve().parent
RESULTS = ROOT / "auditoria_por_etapas/resultados"
PG_BIN = Path("C:/Program Files/PostgreSQL/18/bin")
CHROME = Path("C:/Program Files/Google/Chrome/Application/chrome.exe")

STAMP = datetime.now(dt_timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)


def digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def protected_hashes() -> dict[str, str | None]:
    protected = [
        *APP.glob("*.sqlite3"),
        *(RESULTS / "datos").rglob("*.sqlite3"),
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]
    return {str(p.relative_to(ROOT)): digest(p) for p in protected}


def run_pg_repro() -> dict:
    cluster = (Path(tempfile.gettempdir()) / ("audit10-repro-pg-" + secrets.token_hex(10))).resolve()
    cluster.mkdir(exist_ok=False)
    mark = cluster / "AUDIT10_REPRO_OWNED"
    mark.write_text(STAMP, encoding="utf-8")
    dbdir = cluster / "data"
    pw = secrets.token_urlsafe(40)
    pwfile = cluster / "password"
    pwfile.write_text(pw, encoding="utf-8")
    dbname = "audit10_repro_" + secrets.token_hex(4)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    def pg(name: str, *args) -> None:
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as f:
            res = subprocess.run(
                [str(PG_BIN / (name + ".exe")), *map(str, args)],
                stdout=f,
                stderr=f,
                timeout=50,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            f.seek(0)
            diag = f.read().replace(pw, "[REDACTED]")
        if res.returncode:
            raise RuntimeError(f"{name} failed: {diag[-600:]}")

    pg_report: dict = {"cluster": str(cluster), "port": port, "findings": {}}
    started = False
    try:
        pg("initdb", "-D", dbdir, "-U", "audit10", "--pwfile", pwfile,
           "--auth-host=scram-sha-256", "--auth-local=scram-sha-256", "--encoding=UTF8", "--locale=C")
        pwfile.unlink()
        pg("pg_ctl", "-D", dbdir, "-l", cluster / "postgres.log",
           "-o", f"-h 127.0.0.1 -p {port} -c log_statement=none -c log_min_error_statement=panic",
           "-w", "start")
        started = True

        import psycopg
        from psycopg import sql

        with psycopg.connect(host="127.0.0.1", port=port, user="audit10", password=pw, dbname="postgres", autocommit=True) as conn:
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
            pg_report["version"] = conn.execute("SELECT version()").fetchone()[0]

        code = f"""
import contextlib, io, json, os, sys
from datetime import timedelta
from decimal import Decimal
sys.path.insert(0, {str(APP)!r})
os.environ.update(APP_ENV='test', DJANGO_DEBUG='false', DJANGO_SECRET_KEY='repro-pg-key', DJANGO_SETTINGS_MODULE='config.settings')
from config import env
env.load_dotenv = lambda path=None: None
from django.conf import settings
settings.DATABASES = {{'default': {{
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': {dbname!r},
    'USER': 'audit10',
    'PASSWORD': {pw!r},
    'HOST': '127.0.0.1',
    'PORT': {port},
    'CONN_MAX_AGE': 0,
    'OPTIONS': {{'options': '-c statement_timeout=15000 -c lock_timeout=8000'}},
}}}}
settings.ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'testserver']
import django
django.setup()
from django.core.management import call_command
from django.test import Client
from django.test.utils import setup_test_environment
from django.utils import timezone
setup_test_environment()
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    call_command('migrate', interactive=False, verbosity=0)

from cash.models import CashRegister, CashShift
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.services import LotInput, confirm_initial_load
from sales.services import _require_seller, add_product_to_draft

r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={{'name': 'Almacenero'}})
r_sel, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={{'name': 'Vendedor'}})
wh = Account.objects.create_user('wh.pg@test.invalid', 'PgRepro10#Pass', display_name='WH', role=r_wh)
sel = Account.objects.create_user('sel.pg@test.invalid', 'PgRepro10#Pass', display_name='Seller', role=r_sel)
reg = CashRegister.objects.create(code='CAJA-01')
CashShift.objects.create(cash_register=reg, seller=sel, opening_amount=Decimal('50.00'))
cat = Category.objects.create(name='Conservas')
prod = Product.objects.create(category=cat, name='Atún en lata 170g', barcode='775100000001', sale_price=Decimal('5.50'), minimum_stock=3)
confirm_initial_load(actor=wh, product=prod, lots=[LotInput('AT-01', 10, Decimal('3.00'), timezone.localdate() + timedelta(days=20))])

cl = Client()
cl.force_login(sel)
findings = {{}}

try:
    resp_nul = cl.get('/ventas/', {{'query': 'Atún\\x00'}})
    findings['pg_nul_query'] = {{'status': resp_nul.status_code, 'raised': None}}
except Exception as exc:
    findings['pg_nul_query'] = {{'status': 500, 'raised': type(exc).__name__, 'msg': str(exc)[:200]}}

resp_upper = cl.get('/ventas/', {{'query': 'ATÚN'}})
findings['pg_upper_accent'] = {{
    'status': resp_upper.status_code,
    'products_count': len(resp_upper.context['products']) if resp_upper.context else None,
    'empty_msg_present': 'No se encontraron productos con existencias vendibles.' in resp_upper.content.decode(),
}}

resp_spaces = cl.get('/ventas/', {{'query': 'Atún   en   lata'}})
findings['pg_multi_spaces'] = {{
    'status': resp_spaces.status_code,
    'products_count': len(resp_spaces.context['products']) if resp_spaces.context else None,
}}

print(json.dumps(findings, ensure_ascii=False))
"""
        sub = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
        )
        if sub.returncode != 0:
            pg_report["child_stderr"] = sub.stderr.replace(pw, "[REDACTED]")[-1000:]
            pg_report["child_returncode"] = sub.returncode
        else:
            pg_report["findings"] = json.loads(sub.stdout.strip().splitlines()[-1])
    finally:
        if started:
            pg("pg_ctl", "-D", dbdir, "-m", "fast", "-w", "stop")
        with socket.socket() as s:
            pg_report["port_closed"] = s.connect_ex(("127.0.0.1", port)) != 0
        shutil.rmtree(cluster, ignore_errors=True)
        pg_report["cluster_removed"] = not cluster.exists()
    return pg_report


def run_sqlite_and_browser_repro(run_dir: Path, out_dir: Path) -> dict:
    sys.path.insert(0, str(APP))
    sys.path.insert(0, str(SUPPORT))
    os.environ.update(
        AUDIT10_RUN_DIR=str(run_dir),
        AUDIT10_OUT=str(out_dir),
        AUDIT10_DEFAULT_COOKIES="0",
        DJANGO_SETTINGS_MODULE="audit10_settings",
    )
    import django
    django.setup()

    from django.conf import settings
    from django.core.exceptions import PermissionDenied, ValidationError
    from django.core.management import call_command
    from django.test import Client
    from django.test.utils import setup_test_environment
    from django.urls import get_resolver
    from django.utils import timezone

    setup_test_environment()
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    from cash.models import CashRegister, CashShift
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.services import LotInput, confirm_initial_load
    from sales.models import SaleDraft, SaleDraftLine
    from sales.services import add_product_to_draft, sellable_stock_for_product

    admin_role, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    wh_role, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    sel_role, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

    seller_pw = secrets.token_urlsafe(14) + "A1!"
    admin = Account.objects.create_user("admin.r10@test.invalid", seller_pw, display_name="Admin R10", role=admin_role)
    wh = Account.objects.create_user("wh.r10@test.invalid", seller_pw, display_name="Almacenero R10", role=wh_role)
    seller = Account.objects.create_user("seller.r10@test.invalid", seller_pw, display_name="Vendedor R10", role=sel_role)
    inactive_seller = Account.objects.create_user("inact.r10@test.invalid", seller_pw, display_name="Inactivo R10", role=sel_role)
    inactive_seller.is_active = False
    inactive_seller.save(update_fields=["is_active"])

    reg = CashRegister.objects.create(code="CAJA-01")
    cat = Category.objects.create(name="Abarrotes R10")
    cat_off = Category.objects.create(name="Suspendida R10", is_active=False)

    long_name = "AtúnEspecialDeLataConNombreLargoSinEspaciosParaProbarDesbordeEnTarjetaDeBorradorDeMostrador" * 1 + " " + ("X" * 70)
    long_name = long_name[:160]
    p_tuna = Product.objects.create(category=cat, name="Atún en lata 170g", barcode="775100000010", sale_price=Decimal("5.50"), minimum_stock=3)
    p_amp = Product.objects.create(category=cat, name="Cafe & Pan Especial", barcode="775100000020", sale_price=Decimal("7.00"), minimum_stock=2)
    p_long = Product.objects.create(category=cat, name=long_name, barcode="7" * 64, sale_price=Decimal("9.90"), minimum_stock=1)
    p_inactive = Product.objects.create(category=cat, name="Producto Inactivo R10", barcode="775100000030", sale_price=Decimal("4.00"), minimum_stock=1)
    p_catoff = Product.objects.create(category=cat, name="Producto Cat Off R10", barcode="775100000040", sale_price=Decimal("4.00"), minimum_stock=1)
    p_nostock = Product.objects.create(category=cat, name="Producto Cero Stock R10", barcode="775100000050", sale_price=Decimal("4.00"), minimum_stock=1)

    today = timezone.localdate()
    confirm_initial_load(actor=wh, product=p_tuna, lots=[LotInput("L-TUNA", 10, Decimal("3.00"), today + timedelta(days=20))])
    confirm_initial_load(actor=wh, product=p_amp, lots=[LotInput("L-AMP", 8, Decimal("4.00"), today + timedelta(days=20))])
    confirm_initial_load(actor=wh, product=p_long, lots=[LotInput("L-LONG", 5, Decimal("5.00"), today + timedelta(days=20))])
    confirm_initial_load(actor=wh, product=p_inactive, lots=[LotInput("L-INACT", 5, Decimal("2.00"), today + timedelta(days=20))])
    confirm_initial_load(actor=wh, product=p_catoff, lots=[LotInput("L-COFF", 5, Decimal("2.00"), today + timedelta(days=20))])
    p_inactive.is_active = False
    p_inactive.save(update_fields=["is_active"])
    p_catoff.category = cat_off
    p_catoff.save(update_fields=["category"])

    findings: dict = {}

    # 1. HU-VEN-01a / RN-22 inactivity screen lock audit
    resolver = get_resolver()
    all_url_names = [k for k in resolver.reverse_dict.keys() if isinstance(k, str)]
    lock_urls = [u for u in all_url_names if any(tok in u.lower() for tok in ("lock", "bloq", "idle", "inact"))]
    cl = Client()
    cl.force_login(seller)
    r_no_shift = cl.get("/ventas/", {"query": p_tuna.barcode})
    no_shift_html = r_no_shift.content.decode()
    findings["hu_ven_01a_screen_lock"] = {
        "session_cookie_age": settings.SESSION_COOKIE_AGE,
        "session_expire_at_browser_close": settings.SESSION_EXPIRE_AT_BROWSER_CLOSE,
        "session_save_every_request": settings.SESSION_SAVE_EVERY_REQUEST,
        "middleware": list(settings.MIDDLEWARE),
        "lock_related_url_names": lock_urls,
        "html_has_setTimeout_or_idle": any(t in no_shift_html.lower() for t in ("settimeout", "setinterval", "inactiv", "bloqueo de pantalla", "screenlock")),
    }

    # Check HU-VEN-04 gaps without open shift
    findings["hu_ven_04_no_shift"] = {
        "status": r_no_shift.status_code,
        "search_form_rendered": 'name="query"' in no_shift_html,
        "has_not_found_literal": "Producto no encontrado" in no_shift_html,
    }

    # 2. POST /ventas/ without open shift -> error rendered?
    r_post_noshift = cl.post("/ventas/", {"product_id": str(p_tuna.pk), "quantity": "1"})
    post_noshift_html = r_post_noshift.content.decode()
    findings["defect_post_noshift_hides_error"] = {
        "status": r_post_noshift.status_code,
        "form_errors": dict(r_post_noshift.context["add_form"].errors),
        "alert_error_in_html": "alert-error" in post_noshift_html,
        "error_text_in_html": "Necesitas un turno de caja abierto a tu nombre" in post_noshift_html,
    }

    # Open shift for seller now
    shift = CashShift.objects.create(cash_register=reg, seller=seller, opening_amount=Decimal("100.00"))

    # Simulate > 6 minutes after login with no activity -> still 200 unlocked
    future = timezone.now() + timedelta(minutes=6, seconds=1)
    with patch("django.utils.timezone.now", return_value=future):
        r_after_6m = cl.get("/ventas/")
        findings["hu_ven_01a_after_6min_status"] = r_after_6m.status_code
        findings["hu_ven_01a_still_shows_pos"] = 'name="query"' in r_after_6m.content.decode()

    # Check HU-VEN-04 quick lookup messages while shift open
    r_missing = cl.get("/ventas/", {"query": "9999999999999"})
    r_nostock = cl.get("/ventas/", {"query": p_nostock.barcode})
    findings["hu_ven_04_open_shift_missing"] = {
        "missing_has_producto_no_encontrado": "Producto no encontrado" in r_missing.content.decode(),
        "missing_actual_msg": "No se encontraron productos con existencias vendibles." in r_missing.content.decode(),
        "zero_stock_actual_msg": "No se encontraron productos con existencias vendibles." in r_nostock.content.decode(),
    }

    # 3. Over-160 query silently ignored
    r_over160 = cl.get("/ventas/", {"query": "A" * 161})
    over160_html = r_over160.content.decode()
    findings["defect_over160_silent_search"] = {
        "status": r_over160.status_code,
        "search_form_errors": dict(r_over160.context["search_form"].errors),
        "alert_error_in_html": "alert-error" in over160_html,
        "shows_blank_prompt": "Escribe un nombre o código de barras para buscar." in over160_html,
    }

    # 4. Empty POST /ventas/ `{}`
    r_empty_post = cl.post("/ventas/", {})
    findings["defect_empty_post_unbound"] = {
        "status": r_empty_post.status_code,
        "is_bound": r_empty_post.context["add_form"].is_bound,
        "errors": dict(r_empty_post.context["add_form"].errors),
    }

    # 5. Query with `&` redirect corruption on POST /ventas/
    r_amp_post = cl.post("/ventas/?query=Cafe%20%26%20Pan", {"product_id": str(p_amp.pk), "quantity": "1"})
    findings["defect_redirect_unescaped_query"] = {
        "status": r_amp_post.status_code,
        "location": r_amp_post["Location"] if r_amp_post.has_header("Location") else None,
        "draft_lines_after": SaleDraft.objects.get(cash_shift=shift, status=SaleDraft.Status.ACTIVE).lines.count(),
    }

    # Clean draft via discard
    cl.post("/ventas/descartar/")

    # 6. Arabic digits "٥" and "+2" in AddDraftLineForm
    r_arabic = cl.post("/ventas/", {"product_id": str(p_tuna.pk), "quantity": "٥"})
    active_after_arabic = SaleDraft.objects.filter(cash_shift=shift, status=SaleDraft.Status.ACTIVE).first()
    findings["defect_arabic_digits_accepted"] = {
        "status": r_arabic.status_code,
        "accepted_and_redirected": r_arabic.status_code == 302,
        "qty_persisted": active_after_arabic.lines.get(product=p_tuna).quantity if active_after_arabic else None,
    }
    cl.post("/ventas/descartar/")

    r_plus = cl.post("/ventas/", {"product_id": str(p_tuna.pk), "quantity": "+2"})
    active_after_plus = SaleDraft.objects.filter(cash_shift=shift, status=SaleDraft.Status.ACTIVE).first()
    findings["defect_plus_sign_accepted"] = {
        "status": r_plus.status_code,
        "qty_persisted": active_after_plus.lines.get(product=p_tuna).quantity if active_after_plus else None,
    }
    cl.post("/ventas/descartar/")

    # 7. Inactive seller calling add_product_to_draft directly
    shift_inact = None
    CashShift.objects.filter(pk=shift.pk).update(status=CashShift.Status.CLOSED)
    shift_inact = CashShift.objects.create(cash_register=reg, seller=inactive_seller, opening_amount=Decimal("10.00"))
    try:
        add_product_to_draft(actor=inactive_seller, product_id=p_tuna.pk, quantity=1)
        findings["defect_inactive_seller_allowed_in_service"] = True
    except PermissionDenied:
        findings["defect_inactive_seller_allowed_in_service"] = False
    SaleDraftLine.objects.filter(draft__cash_shift=shift_inact).delete()
    SaleDraft.objects.filter(cash_shift=shift_inact).delete()
    shift_inact.delete()
    CashShift.objects.filter(pk=shift.pk).update(status=CashShift.Status.OPEN)

    # 8. Test stale price, integer overflow, and sales_line_update warning race
    r_upd_big = cl.post(
        f"/ventas/lineas/{uuid.uuid4()}/",
        {"quantity": "99999999999999999999"},
    )
    add_product_to_draft(actor=seller, product_id=p_tuna.pk, quantity=2)
    draft_active = SaleDraft.objects.get(cash_shift=shift, status=SaleDraft.Status.ACTIVE)
    line_tuna = draft_active.lines.get(product=p_tuna)
    p_tuna.sale_price = Decimal("6.25")
    p_tuna.save(update_fields=["sale_price"])
    r_get_stale = cl.get("/ventas/")
    stale_html = r_get_stale.content.decode()
    findings["stale_price_on_get"] = {
        "draft_line_shows_old_5_50": "S/ 5.50 por unidad" in stale_html,
        "draft_line_shows_new_6_25": "S/ 6.25" in stale_html,
    }
    p_tuna.sale_price = Decimal("5.50")
    p_tuna.save(update_fields=["sale_price"])
    cl.post("/ventas/descartar/")

    # Restore seller draft with p_long and p_tuna to test Chrome layout in unmodified CSS!
    add_product_to_draft(actor=seller, product_id=p_long.pk, quantity=1)
    add_product_to_draft(actor=seller, product_id=p_tuna.pk, quantity=2)

    findings["lot_stock_unchanged_after_draft_ops"] = {
        "p_tuna_available": p_tuna.lots.get().available_quantity,
        "p_amp_available": p_amp.lots.get().available_quantity,
        "p_long_available": p_long.lots.get().available_quantity,
    }

    # Store credentials ONLY in file, never print to stdout
    cred_file = run_dir / ".credentials.json"
    cred_file.write_text(
        json.dumps({"seller": {"email": seller.email, "password": seller_pw}}),
        encoding="utf-8",
    )

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    serve_cmd = [
        sys.executable, "-c",
        (
            f"import os, sys; sys.path[:0]=[{str(APP)!r}, {str(SUPPORT)!r}]; "
            f"os.environ.update(AUDIT10_RUN_DIR={str(run_dir)!r}, AUDIT10_DEFAULT_COOKIES='0', DJANGO_SETTINGS_MODULE='audit10_settings'); "
            f"import django; django.setup(); from django.core.management import execute_from_command_line; "
            f"execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:{port}', '--noreload', '--insecure'])"
        ),
    ]
    server = subprocess.Popen(serve_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    chrome_report: dict = {}
    try:
        for _ in range(100):
            with socket.socket() as s:
                if s.connect_ex(("127.0.0.1", port)) == 0:
                    break
            import time
            time.sleep(0.1)

        node_script = r"""
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { chromium } = require(path.join(os.homedir(), ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core"));
(async () => {
  const creds = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
  const base = process.argv[3];
  const shotDir = process.argv[4];
  const browser = await chromium.launch({ executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe", headless: true });
  const results = {};
  for (const [label, vp] of [["1366x900", { width: 1366, height: 900 }], ["1366x768", { width: 1366, height: 768 }]]) {
    const ctx = await browser.newContext({ locale: "es-PE", viewport: vp });
    const page = await ctx.newPage();
    await page.goto(base);
    await page.locator("[name=email]").fill(creds.seller.email);
    await page.locator("[name=password]").fill(creds.seller.password);
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(base + "/inicio/");
    await page.goto(base + "/ventas/?query=At%C3%BAnEspecial");
    const m = await page.evaluate(() => {
      const docSW = document.documentElement.scrollWidth;
      const winW = window.innerWidth;
      const layout = document.querySelector(".sales-layout");
      const searchPanel = document.querySelector(".sales-search-panel");
      const draftPanel = document.querySelector(".sales-summary-panel");
      const wrap = document.querySelector(".table-wrap");
      const draftLines = Array.from(document.querySelectorAll(".draft-line"));
      return {
        docSW, winW,
        docOverflow: docSW > winW,
        layoutRight: layout ? Math.round(layout.getBoundingClientRect().right) : null,
        searchPanelW: searchPanel ? Math.round(searchPanel.getBoundingClientRect().width) : null,
        searchPanelSW: searchPanel ? searchPanel.scrollWidth : null,
        searchPanelCW: searchPanel ? searchPanel.clientWidth : null,
        draftPanelRight: draftPanel ? Math.round(draftPanel.getBoundingClientRect().right) : null,
        draftPanelSW: draftPanel ? draftPanel.scrollWidth : null,
        draftPanelCW: draftPanel ? draftPanel.clientWidth : null,
        wrapSW: wrap ? wrap.scrollWidth : null,
        wrapCW: wrap ? wrap.clientWidth : null,
        maxDraftLineSW: Math.max(0, ...draftLines.map(d => d.scrollWidth)),
        maxDraftLineCW: Math.max(0, ...draftLines.map(d => d.clientWidth)),
      };
    });
    results[label] = m;
    if (label === "1366x900") {
      await page.screenshot({ path: path.join(shotDir, "repro-1366x900.png"), fullPage: true });
    }
    await ctx.close();
  }
  await browser.close();
  console.log(JSON.stringify(results));
})();
"""
        ns_path = out_dir / "repro_chrome.cjs"
        ns_path.write_text(node_script, encoding="utf-8")
        res = subprocess.run(
            ["node", str(ns_path), str(cred_file), f"http://127.0.0.1:{port}", str(out_dir)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=120,
        )
        if res.returncode != 0:
            chrome_report = {"returncode": res.returncode, "stderr": res.stderr[-1000:]}
        else:
            chrome_report = json.loads(res.stdout.strip().splitlines()[-1])
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)
    findings["chrome_layout"] = chrome_report
    return findings


def main() -> int:
    start_hashes = protected_hashes()
    run_dir = RESULTS / "datos" / f"etapa10-repro-{STAMP}"
    out_dir = RESULTS / "evidencias" / f"10-repro-{STAMP}"
    run_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    (run_dir / "marker.json").write_text(json.dumps({"run": run_dir.name, "created_utc": STAMP}), encoding="utf-8")
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")

    report = {
        "stamp_utc": STAMP,
        "evidence": str(out_dir.relative_to(ROOT)),
        "pg_repro": run_pg_repro(),
        "sqlite_and_browser_repro": run_sqlite_and_browser_repro(run_dir, out_dir),
    }
    end_hashes = {k: digest(ROOT / k) == v for k, v in start_hashes.items()}
    report["protected_unchanged"] = all(end_hashes.values())
    (out_dir / "repro.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["protected_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
