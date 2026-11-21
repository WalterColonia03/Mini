"""Pre-fix Stage 07 reproduction probes (SQLite + Chrome 1366x900 + ephemeral PostgreSQL 18.4).
Never loads operator .env and never mutates existing SQLite DBs.
"""
from __future__ import annotations

import contextlib
import hashlib
import inspect
import io
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
SUPPORT = Path(__file__).resolve().parent
PG_BIN = Path("C:/Program Files/PostgreSQL/18/bin")

STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
RUN_DIR = RESULTS / "datos" / f"etapa07-repro-{STAMP}"
OUT_DIR = RESULTS / "evidencias" / f"07-repro-{STAMP}"
RUN_DIR.mkdir(parents=True)
OUT_DIR.mkdir(parents=True)
(RUN_DIR / "marker.json").write_text(
    json.dumps({"run": RUN_DIR.name, "created_utc": STAMP}), encoding="utf-8"
)
(RUN_DIR / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")


def digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


protected = [
    *APP.glob("*.sqlite3"),
    *(RESULTS / "datos").rglob("*.sqlite3"),
    ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
]
start_hashes = {str(p.relative_to(ROOT)): digest(p) for p in protected}

os.environ.update(
    AUDIT07_RUN_DIR=str(RUN_DIR),
    AUDIT07_OUT=str(OUT_DIR),
    AUDIT07_DEFAULT_COOKIES="1",
    DJANGO_SETTINGS_MODULE="audit07_settings",
)
sys.path.insert(0, str(APP))
sys.path.insert(0, str(SUPPORT))

import django

django.setup()

from django.core.management import call_command
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext, setup_test_environment

setup_test_environment()
from django.urls import reverse
from django.utils import timezone as tz

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    call_command("migrate", interactive=False, verbosity=0)

import audit07_run
import catalog.views
import identity.views
import inventory.views
from cash.models import CashRegister, CashShift
from catalog.models import Category, Product, ProductBarcodeKey
from identity.models import Account, Role
from inventory.models import Lot
from inventory.services import LotInput, confirm_initial_load
from sales.models import Sale
from sales.services import add_product_to_draft, checkout_sale, sellable_stock_for_product
from sales.views import _search_products

fixture = audit07_run.prepare_stage07_fixtures(RUN_DIR, OUT_DIR)
creds = json.loads((RUN_DIR / ".credentials.json").read_text(encoding="utf-8"))

c_admin = Client(enforce_csrf_checks=True)
assert c_admin.login(username=creds["admin"]["email"], password=creds["admin"]["password"])
c_wh = Client(enforce_csrf_checks=True)
assert c_wh.login(username=creds["warehouse"]["email"], password=creds["warehouse"]["password"])
c_seller = Client(enforce_csrf_checks=True)
assert c_seller.login(username=creds["seller"]["email"], password=creds["seller"]["password"])
c_anon = Client()

findings: dict[str, object] = {
    "stamp_utc": STAMP,
    "protected_absent_at_start": [k for k, v in start_hashes.items() if v is None],
    "product_expirations_source": inspect.getsource(sys.modules["catalog.views"].product_expirations),
    "stock_overview_source": inspect.getsource(sys.modules["inventory.views"].stock_overview),
    "_admin_summary_source": inspect.getsource(sys.modules["identity.views"]._admin_summary),
    "product_expirations_template": (APP / "catalog/templates/catalog/product_expirations.html").read_text(encoding="utf-8"),
}

# 1. Dashboard (_admin_summary) vs stock_overview (OBS-05-RESUMEN-MINIMO + OBS-05-STOCK-CAT-INACTIVA)
with CaptureQueriesContext(connection) as q_dash:
    r_dash_admin = c_admin.get(reverse("dashboard"))
with CaptureQueriesContext(connection) as q_stock:
    r_stock_admin = c_admin.get(reverse("stock-overview"))
with CaptureQueriesContext(connection) as q_exp:
    r_exp_admin = c_admin.get(reverse("product-expirations"))

r_dash_wh = c_wh.get(reverse("dashboard"))
r_dash_seller = c_seller.get(reverse("dashboard"))

findings["parity_before_fix"] = {
    "admin_summary": r_dash_admin.context["summary"],
    "expected_summary_with_fixes": fixture["expected_summary"],
    "dashboard_counts_low_stock_with_lt_defect": r_dash_admin.context["summary"]["low_stock"] == 2,
    "stock_overview_low_stock_names": [p.name for p in r_stock_admin.context["low_stock"]],
    "stock_overview_includes_cat_off_defect": "Galletas Categoria Suspendida" in [p.name for p in r_stock_admin.context["low_stock"]],
    "stock_overview_expired_numbers": [l.number for l in r_stock_admin.context["expired_lots"]],
    "stock_overview_expiring_numbers": [l.number for l in r_stock_admin.context["expiring_lots"]],
    "stock_overview_lowercase_lot_shown_raw": "Lote mix-vence-hoy" in r_stock_admin.content.decode("utf-8"),
    "expirations_lot_numbers_default_30": [l.number_normalized for l in r_exp_admin.context["lots"]],
    "expirations_query_count": len(q_exp),
    "stock_overview_n_plus_1_query_count": len(q_stock),
    "dashboard_query_count": len(q_dash),
    "wh_sees_summary_without_sales": (
        r_dash_wh.context["summary"] is not None
        and "Ventas de hoy" not in r_dash_wh.content.decode("utf-8")
        and "Productos con stock bajo" in r_dash_wh.content.decode("utf-8")
    ),
    "seller_summary_is_none": r_dash_seller.context["summary"] is None,
}

# 2. ?dias= probes (including non-ASCII Arabic "٥" and "+7" and boundaries)
dias_probes = {}
for val in ["", "1", "7", "29", "30", "31", "3650", "0", "-5", "3651", "999999999", "abc", "7.5", "+7", "٥", "1\x00"]:
    resp = c_admin.get(reverse("product-expirations"), {"dias": val})
    dias_probes[repr(val)] = {
        "status": resp.status_code,
        "resolved_days": resp.context["days"],
        "lots_count": resp.context["lots"].count(),
        "has_d30": any(l.number_normalized == "D30-EXACT" for l in resp.context["lots"]),
        "has_d31": any(l.number_normalized == "D31-OUT" for l in resp.context["lots"]),
        "has_zero_qty": any(l.number_normalized == "MIX-ZERO-EXP" for l in resp.context["lots"]),
        "msgs": [str(m) for m in resp.context["messages"]],
    }
findings["dias_probes_before_fix"] = dias_probes

# 3. Chrome pre-fix layout probe for OBS-05-EXPIRATIONS-WRAP + stock_overview banner wrap
server = None
port = 0
chrome_repro = {}
try:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    os.environ["AUDIT07_PORT"] = str(port)
    # Run serve with default cookies=1 in env -> match cookie settings
    server = subprocess.Popen(
        [sys.executable, str(SUPPORT / "audit07_run.py"), "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(100):
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", port)) == 0:
                break
        time.sleep(0.1)

    js_probe = r"""
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const { chromium } = require(path.join(os.homedir(), ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core"));
(async () => {
  const creds = JSON.parse(fs.readFileSync(path.join(process.env.AUDIT07_RUN_DIR, ".credentials.json"), "utf8"));
  const base = "http://127.0.0.1:" + process.env.AUDIT07_PORT;
  const browser = await chromium.launch({ executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe", headless: true });
  const ctx = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(base);
  await page.locator("[name=email]").fill(creds.admin.email);
  await page.locator("[name=password]").fill(creds.admin.password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(base + "/inicio/");
  await page.goto(base + "/productos/vencimientos/");
  const expMetrics = await page.evaluate(() => {
    const wrap = document.querySelector(".table-responsive");
    const wr = wrap.getBoundingClientRect();
    const ths = Array.from(document.querySelectorAll("table th")).map(th => ({
      text: th.textContent.trim(),
      right: Math.round(th.getBoundingClientRect().right),
      clipped: th.getBoundingClientRect().right > wr.right + 1
    }));
    const rowsText = document.querySelector("table tbody").innerText;
    return {
      docScrollWidth: document.documentElement.scrollWidth,
      windowInnerWidth: window.innerWidth,
      tableWrapScrollWidth: wrap.scrollWidth,
      tableWrapClientWidth: wrap.clientWidth,
      overflowPx: wrap.scrollWidth - wrap.clientWidth,
      ths,
      hasDaysLeftShown: /Vence hoy|Venció|En \d+ día/.test(rowsText),
      hasDirectWriteoffLink: document.querySelectorAll('a[href*="/inventario/bajas/nueva/?lote="]').length > 0,
    };
  });
  await page.screenshot({ path: path.join(process.env.AUDIT07_OUT, "pre-fix-expirations.png"), fullPage: true });
  await page.goto(base + "/inventario/stock/");
  const stockMetrics = await page.evaluate(() => ({
    docScrollWidth: document.documentElement.scrollWidth,
    windowInnerWidth: window.innerWidth,
    docOverflow: document.documentElement.scrollWidth > window.innerWidth,
  }));
  await page.screenshot({ path: path.join(process.env.AUDIT07_OUT, "pre-fix-stock-overview.png"), fullPage: true });
  console.log(JSON.stringify({ expMetrics, stockMetrics }));
  await browser.close();
})();
"""
    proc = subprocess.run(["node", "-e", js_probe], capture_output=True, text=True, encoding="utf-8", timeout=90)
    chrome_repro = {"returncode": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr.strip()}
    if proc.returncode == 0 and proc.stdout.strip():
        chrome_repro["parsed"] = json.loads(proc.stdout.strip())
finally:
    if server is not None:
        server.terminate()
        server.wait(timeout=5)
findings["chrome_pre_fix"] = chrome_repro

# 4. UTC <-> Lima midnight boundary & POS multi-lot / multi-barcode check (SQLite)
p_mix = Product.objects.get(pk=fixture["products"]["exp_mix"]["id"])
ProductBarcodeKey.objects.create(product=p_mix, reading_key="0775070700001")
pos_search_mix = list(_search_products("Leche Mezcla"))
midnight_before = datetime(2026, 11, 12, 4, 59, 59, tzinfo=timezone.utc)  # 2026-11-11 23:59:59 Lima
midnight_after = datetime(2026, 11, 12, 5, 0, 0, tzinfo=timezone.utc)    # 2026-11-12 00:00:00 Lima
# Create a dedicated lot expiring on 2026-11-12 for midnight transition
p_mid = Product.objects.create(category=Category.objects.first(), name="Producto Medianoche Lima", barcode="775070700099", sale_price=Decimal("4.00"), minimum_stock=2)
with patch("django.utils.timezone.now", return_value=midnight_before):
    confirm_initial_load(actor=Account.objects.get(email=creds["warehouse"]["email"]), product=p_mid, lots=[LotInput("MID-12NOV", 5, Decimal("1.5000"), datetime(2026, 11, 12).date())])
with patch("django.utils.timezone.now", return_value=midnight_before):
    mid_before_res = {
        "localdate": str(tz.localdate()),
        "sellable_stock": p_mid.sellable_stock,
        "pos_sellable": sellable_stock_for_product(p_mid),
        "pos_found": _search_products("Medianoche Lima").exists(),
    }
with patch("django.utils.timezone.now", return_value=midnight_after):
    mid_after_res = {
        "localdate": str(tz.localdate()),
        "sellable_stock": p_mid.sellable_stock,
        "pos_sellable": sellable_stock_for_product(p_mid),
        "pos_found": _search_products("Medianoche Lima").exists(),
    }

findings["lima_midnight_and_pos_sqlite"] = {
    "p_mix_sellable_model": p_mix.sellable_stock,
    "p_mix_sellable_service": sellable_stock_for_product(p_mix),
    "p_mix_pos_search_qty_with_2_barcode_keys_and_4_lots": pos_search_mix[0].sellable_quantity if pos_search_mix else None,
    "p_all_expired_in_pos": _search_products("Conserva Solo Vencida").exists(),
    "p_cat_off_in_pos": _search_products("Galletas Categoria Suspendida").exists(),
    "p_inactive_in_pos": _search_products("Jugo Producto Deshabilitado").exists(),
    "midnight_before_045959Z": mid_before_res,
    "midnight_after_050000Z": mid_after_res,
}

# 5. HTTP role & method checks
findings["http_boundaries"] = {
    "anon_stock_status": c_anon.get(reverse("stock-overview")).status_code,
    "anon_expirations_status": c_anon.get(reverse("product-expirations")).status_code,
    "seller_stock_status": c_seller.get(reverse("stock-overview")).status_code,
    "seller_expirations_status": c_seller.get(reverse("product-expirations")).status_code,
    "admin_post_stock_405": c_admin.post(reverse("stock-overview")).status_code,
    "admin_post_expirations_405": c_admin.post(reverse("product-expirations")).status_code,
    "stock_cache_control": r_stock_admin.headers.get("Cache-Control", ""),
    "exp_cache_control": r_exp_admin.headers.get("Cache-Control", ""),
    "dash_cache_control": r_dash_admin.headers.get("Cache-Control", ""),
}

# 6. PostgreSQL 18.4 Sale.confirmed_at__date vs Lima midnight + lot_fefo_idx EXPLAIN check
pg_repro = {}
cluster = (Path(tempfile.gettempdir()) / ("audit07-repro-pg-" + secrets.token_hex(8))).resolve()
cluster.mkdir(exist_ok=False)
dbdir = cluster / "data"
pw_pg = secrets.token_urlsafe(32)
pwfile = cluster / "pw"
pwfile.write_text(pw_pg, encoding="utf-8")
with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    pg_port = s.getsockname()[1]

pg_started = False
try:
    subprocess.run(
        [str(PG_BIN / "initdb.exe"), "-D", str(dbdir), "-U", "audit07r", "--pwfile", str(pwfile), "--auth-host=scram-sha-256", "--auth-local=scram-sha-256", "--encoding=UTF8", "--locale=C"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
    )
    pwfile.unlink()
    subprocess.run(
        [str(PG_BIN / "pg_ctl.exe"), "-D", str(dbdir), "-l", str(cluster / "pg.log"), "-o", f"-h 127.0.0.1 -p {pg_port} -c log_statement=none", "-w", "start"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
    )
    pg_started = True
    import psycopg
    from psycopg import sql
    from django.conf import settings
    from django.db import connections

    with psycopg.connect(host="127.0.0.1", port=pg_port, user="audit07r", password=pw_pg, dbname="postgres", autocommit=True) as pconn:
        pconn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier("audit07_repro")))

    connections.close_all()
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "audit07_repro",
        "USER": "audit07r",
        "PASSWORD": pw_pg,
        "HOST": "127.0.0.1",
        "PORT": pg_port,
        "CONN_MAX_AGE": 0,
        "CONN_HEALTH_CHECKS": False,
        "ATOMIC_REQUESTS": False,
        "AUTOCOMMIT": True,
        "TIME_ZONE": "America/Lima",
        "OPTIONS": {"options": "-c statement_timeout=15000 -c lock_timeout=8000"},
    }
    del connections["default"]
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    r_adm = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    r_wh = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    r_sel = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
    u_adm = Account.objects.create_user("adm.pg7r@test.invalid", "StrongPass!123", display_name="Adm PG7", role=r_adm)
    u_wh = Account.objects.create_user("wh.pg7r@test.invalid", "StrongPass!123", display_name="Wh PG7", role=r_wh)
    u_sel = Account.objects.create_user("sel.pg7r@test.invalid", "StrongPass!123", display_name="Sel PG7", role=r_sel)
    cat_pg = Category.objects.create(name="PG07 Cat")
    p_pg = Product.objects.create(category=cat_pg, name="PG07 Prod", barcode="775077700001", sale_price=Decimal("10.00"), minimum_stock=5)
    confirm_initial_load(actor=u_wh, product=p_pg, lots=[LotInput("PG07-L1", 10, Decimal("2.00"), datetime(2026, 12, 15).date())])
    reg_pg = CashRegister.objects.create(code="CAJA-PG07R")
    CashShift.objects.create(cash_register=reg_pg, seller=u_sel, opening_amount=Decimal("50.00"))

    # Create two sales straddling UTC midnight (2026-11-12T04:30Z = Nov 11 23:30 Lima; 2026-11-12T05:30Z = Nov 12 00:30 Lima)
    d1 = add_product_to_draft(actor=u_sel, product_id=p_pg.pk, quantity=1)
    s1 = checkout_sale(actor=u_sel, draft_id=d1.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4())
    Sale.objects.filter(pk=s1.pk).update(confirmed_at=datetime(2026, 11, 12, 4, 30, tzinfo=timezone.utc))

    d2 = add_product_to_draft(actor=u_sel, product_id=p_pg.pk, quantity=2)
    s2 = checkout_sale(actor=u_sel, draft_id=d2.pk, cash_received=Decimal("20.00"), idempotency_key=uuid.uuid4())
    Sale.objects.filter(pk=s2.pk).update(confirmed_at=datetime(2026, 11, 12, 5, 30, tzinfo=timezone.utc))

    from identity.views import _admin_summary

    with patch("django.utils.timezone.now", return_value=datetime(2026, 11, 12, 4, 59, 59, tzinfo=timezone.utc)):
        pg_repro["summary_at_nov11_235959_lima"] = _admin_summary()
    with patch("django.utils.timezone.now", return_value=datetime(2026, 11, 12, 5, 0, 0, tzinfo=timezone.utc)):
        pg_repro["summary_at_nov12_000000_lima"] = _admin_summary()

    # NUL byte in ?dias= on PG
    pg_c = Client()
    pg_c.force_login(u_adm)
    r_nul_dias = pg_c.get(reverse("product-expirations"), {"dias": "7\x00"})
    pg_repro["nul_dias_status"] = r_nul_dias.status_code

    connections.close_all()
finally:
    if pg_started:
        subprocess.run(
            [str(PG_BIN / "pg_ctl.exe"), "-D", str(dbdir), "-m", "fast", "-w", "stop"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW
        )
    with socket.socket() as s:
        pg_repro["port_closed"] = s.connect_ex(("127.0.0.1", pg_port)) != 0

findings["postgresql_repro"] = pg_repro

end_hashes = {str(p.relative_to(ROOT)): digest(p) == start_hashes[str(p.relative_to(ROOT))] for p in protected}
findings["protected_unchanged"] = all(end_hashes.values())

repro_file = OUT_DIR / "repro.json"
repro_file.write_text(json.dumps(findings, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print(json.dumps({"repro": str(repro_file.relative_to(ROOT)), "parity_before_fix": findings["parity_before_fix"], "chrome_pre_fix": findings["chrome_pre_fix"].get("parsed"), "postgresql_repro": pg_repro, "protected_unchanged": findings["protected_unchanged"]}, ensure_ascii=False, indent=2, default=str))
