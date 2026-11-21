"""Pre-fix Stage 12 reproduction & behavior probes (isolated SQLite + Chrome 1366x900/1366x768/@media print + PG 18.4).
Captures exact pre-edit defects and empirical checkout-retry/receipt/history/print behavior before fixes.
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
import tempfile
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
SUPPORT = Path(__file__).resolve().parent
PG_BIN = Path("C:/Program Files/PostgreSQL/18/bin")

STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
RUN_DIR = RESULTS / "datos" / f"etapa12-repro-{STAMP}"
OUT_DIR = RESULTS / "evidencias" / f"12-repro-{STAMP}"
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
    AUDIT12_RUN_DIR=str(RUN_DIR),
    AUDIT12_OUT=str(OUT_DIR),
    AUDIT12_DEFAULT_COOKIES="1",
    DJANGO_SETTINGS_MODULE="audit12_settings",
)
sys.path.insert(0, str(APP))
sys.path.insert(0, str(SUPPORT))

import django

django.setup()

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import Client
from django.test.utils import setup_test_environment

setup_test_environment()
from django.urls import reverse
from django.utils import timezone as tz

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    call_command("migrate", interactive=False, verbosity=0)

import audit12_run
from cash.models import CashShift
from catalog.models import Product
from identity.models import Account
from inventory.models import Lot
from sales.models import Sale, SaleCounter, SaleDraft, SaleLine
from sales.services import add_product_to_draft, checkout_sale

fixture = audit12_run.prepare_stage12_fixtures(RUN_DIR, OUT_DIR)
creds = json.loads((RUN_DIR / ".credentials.json").read_text(encoding="utf-8"))

seller1 = Account.objects.get(email=creds["seller1"]["email"])
seller2 = Account.objects.get(email=creds["seller2"]["email"])
admin = Account.objects.get(email=creds["admin"]["email"])
warehouse = Account.objects.get(email=creds["warehouse"]["email"])
p_std = Product.objects.get(pk=fixture["products"]["std"]["id"])
p_tax = Product.objects.get(pk=fixture["products"]["tax"]["id"])
p_long = Product.objects.get(pk=fixture["products"]["long"]["id"])

findings: dict[str, object] = {
    "stamp_utc": STAMP,
    "protected_absent_at_start": [k for k, v in start_hashes.items() if v is None],
}

# ── Probe 1: Real effect of retrying POST /ventas/cobrar/ ────────────────────
c_s1 = Client(enforce_csrf_checks=True)
assert c_s1.login(username=creds["seller1"]["email"], password=creds["seller1"]["password"])

# Ensure p_std stock & initial sale state
lot_std_before = Lot.objects.get(product=p_std, number="L12-STD").available_quantity
counter_before = SaleCounter.objects.get(id=1).next_value
sales_count_before = Sale.objects.count()

co_get = c_s1.get(reverse("sales-checkout"))
init_retry = co_get.context["form"].initial
csrf_retry = co_get.cookies["csrftoken"].value
idem_retry = str(init_retry["idempotency_key"])
payload_retry = {
    "csrfmiddlewaretoken": csrf_retry,
    "cash_received": "15.00",
    "discount_amount": "0.00",
    "idempotency_key": idem_retry,
    "expected_subtotal": str(init_retry["expected_subtotal"]),
    "draft_signature": init_retry["draft_signature"],
}
first_post = c_s1.post(reverse("sales-checkout"), payload_retry)
confirmed_sale = Sale.objects.get(idempotency_key=idem_retry)
lot_after_confirm = Lot.objects.get(product=p_std, number="L12-STD").available_quantity
counter_after_confirm = SaleCounter.objects.get(id=1).next_value

# Probe 1a: Exact retry with NO new active draft (most realistic network drop / reload resubmit)
retry_no_draft = c_s1.post(reverse("sales-checkout"), payload_retry, follow=True)
msgs_no_draft = [str(m) for m in retry_no_draft.context.get("messages", [])] if retry_no_draft.context else []

# Probe 1b: Direct service call with SAME idempotency_key & draft_id but altered cash_received/discount_amount
diff_payload_rejected = False
diff_payload_returned = None
try:
    s_alt = checkout_sale(
        actor=seller1,
        draft_id=confirmed_sale.draft_id,
        cash_received=Decimal("99.00"),
        discount_amount=Decimal("5.00"),
        idempotency_key=confirmed_sale.idempotency_key,
    )
    diff_payload_returned = {
        "sale_id": str(s_alt.pk),
        "cash_received": str(s_alt.cash_received),
        "discount_amount": str(s_alt.discount_amount),
    }
except ValidationError as exc:
    diff_payload_rejected = True
    diff_payload_returned = {"error": str(exc)}

# Probe 1c: Seller1 starts a NEW draft (draft_2) and then delayed retry of draft_1's POST arrives!
d_new = add_product_to_draft(actor=seller1, product_id=p_tax.pk, quantity=1)
# Update csrf cookie on new session if needed (still valid in client)
retry_with_new_draft = c_s1.post(reverse("sales-checkout"), payload_retry)
form_err_new_draft = (
    dict(retry_with_new_draft.context["form"].errors)
    if retry_with_new_draft.context and "form" in retry_with_new_draft.context
    else None
)
# Cross-draft reuse with draft_2's signature and K1
co_get2 = c_s1.get(reverse("sales-checkout"))
init2 = co_get2.context["form"].initial
cross_draft_retry = c_s1.post(
    reverse("sales-checkout"),
    {
        "csrfmiddlewaretoken": co_get2.cookies["csrftoken"].value,
        "cash_received": "10.00",
        "discount_amount": "0.00",
        "idempotency_key": idem_retry,
        "expected_subtotal": str(init2["expected_subtotal"]),
        "draft_signature": init2["draft_signature"],
    },
)
cross_draft_errors = (
    dict(cross_draft_retry.context["form"].errors)
    if cross_draft_retry.context and "form" in cross_draft_retry.context
    else None
)

findings["checkout_retry_real_effect"] = {
    "before_sales_count": sales_count_before,
    "before_counter": counter_before,
    "before_std_lot": lot_std_before,
    "first_post_status": first_post.status_code,
    "first_post_location": first_post.get("Location"),
    "confirmed_sale_correlative": confirmed_sale.correlative,
    "confirmed_std_lot": lot_after_confirm,
    "confirmed_counter": counter_after_confirm,
    "retry_no_draft_redirect_chain": retry_no_draft.redirect_chain,
    "retry_no_draft_messages": msgs_no_draft,
    "retry_no_draft_recovers_receipt": any("/constancia/" in u for u, _ in retry_no_draft.redirect_chain),
    "lot_unchanged_after_retries": Lot.objects.get(product=p_std, number="L12-STD").available_quantity == lot_after_confirm,
    "counter_unchanged_after_retries": SaleCounter.objects.get(id=1).next_value == counter_after_confirm,
    "sales_count_unchanged_after_retries": Sale.objects.count() == sales_count_before + 1,
    "service_same_key_same_draft_diff_amounts_rejected": diff_payload_rejected,
    "service_same_key_same_draft_diff_amounts_result": diff_payload_returned,
    "retry_while_new_draft_active_status": retry_with_new_draft.status_code,
    "retry_while_new_draft_active_errors": form_err_new_draft,
    "cross_draft_same_key_status": cross_draft_retry.status_code,
    "cross_draft_same_key_errors": cross_draft_errors,
}

# Leave d_new discarded so Stage 12 repro fixtures stay tidy for next checks
c_s1.post(reverse("sales-draft-discard"), {"csrfmiddlewaretoken": co_get2.cookies["csrftoken"].value})

# ── Probe 2: Receipt content, SaleLine ordering, "Última constancia", cost exposure ──
s3_id = fixture["sales"]["s3_open"]["id"]
s3_obj = Sale.objects.prefetch_related("lines").get(pk=s3_id)
receipt_resp = c_s1.get(reverse("sales-receipt", args=(s3_id,)))
receipt_html = receipt_resp.content.decode("utf-8")
draft_resp = c_s1.get(reverse("sales-draft"))
draft_html = draft_resp.content.decode("utf-8")

# Compare SaleLine display order vs draft insertion order (S3 inserted p_long first, p_tax second)
sale_lines_rendered_names = [line.product_snapshot_name for line in s3_obj.lines.all()]
unit_costs_4dec = [f"{line.unit_cost:.4f}" for line in s3_obj.lines.all() if line.unit_cost is not None]

findings["receipt_and_pos_defects"] = {
    "has_literal_rn26_banner": "CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO" in receipt_html,
    "has_external_official_channel_notice": "canal autorizado" in receipt_html.lower(),
    "has_constancia_interna_text": "constancia interna" in receipt_html.lower(),
    "has_validez_tributaria_text": "validez tributaria" in receipt_html.lower(),
    "uses_undefined_text_right_class": 'class="text-right"' in receipt_html,
    "shows_pre_discount_subtotal": "Subtotal" in receipt_html and "19,10" in receipt_html,
    "shows_payment_method_efectivo": "Medio de pago" in receipt_html,
    "shows_discount_on_s3": "1,50" in receipt_html,
    "snapshot_price_12_preserved_not_99": ("12,00" in receipt_html) and ("99,00" not in receipt_html),
    "unit_costs_4dec_absent_from_html": all(uc not in receipt_html and uc.replace(".", ",") not in receipt_html for uc in unit_costs_4dec),
    "sale_lines_actual_uuids_order_names": sale_lines_rendered_names,
    "draft_insertion_expected_order_names": [p_long.name, p_tax.name],
    "sale_line_order_differs_from_insertion": sale_lines_rendered_names != [p_long.name, p_tax.name],
    "pos_draft_has_ultima_constancia_link": "Última constancia" in draft_html or reverse("sales-receipt", args=(confirmed_sale.pk,)) in draft_html,
}

# ── Probe 3: Permissions, Foreign IDs, Filters, Total cobrado, Cache-Control ──
c_s2 = Client(enforce_csrf_checks=True)
assert c_s2.login(username=creds["seller2"]["email"], password=creds["seller2"]["password"])
c_adm = Client(enforce_csrf_checks=True)
assert c_adm.login(username=creds["admin"]["email"], password=creds["admin"]["password"])
adm_csrf_page = c_adm.get(reverse("logout"))
adm_csrf = adm_csrf_page.cookies["csrftoken"].value
c_wh = Client(enforce_csrf_checks=True)
assert c_wh.login(username=creds["warehouse"]["email"], password=creds["warehouse"]["password"])
c_anon = Client()

s1_old_id = fixture["sales"]["s1_old"]["id"]
s2_v2_id = fixture["sales"]["s2_v2"]["id"]
sh1_closed_id = fixture["shifts"]["seller1_closed"]["id"]
sh2_v2_id = fixture["shifts"]["seller2_closed"]["id"]
sh3_open_id = fixture["shifts"]["seller1_open"]["id"]

sales_hist_adm = c_adm.get(reverse("sales-history"))
sales_hist_adm_filtered_v2 = c_adm.get(
    reverse("sales-history"),
    {"vendedor": fixture["accounts"]["seller2"]["id"], "turno": sh2_v2_id, "fecha_desde": fixture["dates"]["yesterday"], "fecha_hasta": fixture["dates"]["yesterday"]},
)
sales_hist_s1 = c_s1.get(reverse("sales-history"))
cash_hist_adm = c_adm.get(reverse("cash-shift-history"))
cash_hist_adm_filtered_v2 = c_adm.get(
    reverse("cash-shift-history"),
    {"vendedor": fixture["accounts"]["seller2"]["id"], "fecha_desde": fixture["dates"]["yesterday"], "fecha_hasta": fixture["dates"]["yesterday"]},
)
cash_closed_adm = c_adm.get(reverse("cash-shift-closed", args=(sh1_closed_id,)))
shift_hist_s1 = c_s1.get(reverse("sales-shift-history"))

findings["cache_control_before_fix"] = {
    "sales_receipt": receipt_resp.headers.get("Cache-Control", ""),
    "sales_shift_history": shift_hist_s1.headers.get("Cache-Control", ""),
    "sales_history": sales_hist_adm.headers.get("Cache-Control", ""),
    "cash_shift_history": cash_hist_adm.headers.get("Cache-Control", ""),
    "cash_shift_closed": cash_closed_adm.headers.get("Cache-Control", ""),
    "cash_shift_opened": c_s1.get(reverse("cash-shift-opened", args=(sh3_open_id,))).headers.get("Cache-Control", ""),
}

findings["history_and_permissions_repro"] = {
    "foreign_id_access": {
        "seller2_get_seller1_receipt": c_s2.get(reverse("sales-receipt", args=(s1_old_id,))).status_code,
        "seller1_get_seller2_receipt": c_s1.get(reverse("sales-receipt", args=(s2_v2_id,))).status_code,
        "seller2_get_seller1_closed_shift": c_s2.get(reverse("cash-shift-closed", args=(sh1_closed_id,))).status_code,
        "seller2_get_seller1_opened_shift": c_s2.get(reverse("cash-shift-opened", args=(sh3_open_id,))).status_code,
        "admin_get_seller1_receipt": c_adm.get(reverse("sales-receipt", args=(s1_old_id,))).status_code,
        "admin_get_seller1_closed_shift": c_adm.get(reverse("cash-shift-closed", args=(sh1_closed_id,))).status_code,
        "admin_get_seller1_opened_shift": c_adm.get(reverse("cash-shift-opened", args=(sh3_open_id,))).status_code,
        "admin_get_sales_shift_history": c_adm.get(reverse("sales-shift-history")).status_code,
        "admin_get_sales_draft": c_adm.get(reverse("sales-draft")).status_code,
        "warehouse_get_sales_receipt": c_wh.get(reverse("sales-receipt", args=(s1_old_id,))).status_code,
        "warehouse_get_sales_shift_history": c_wh.get(reverse("sales-shift-history")).status_code,
        "warehouse_get_sales_history": c_wh.get(reverse("sales-history")).status_code,
        "warehouse_get_cash_shift_history": c_wh.get(reverse("cash-shift-history")).status_code,
        "warehouse_get_cash_shift_closed": c_wh.get(reverse("cash-shift-closed", args=(sh1_closed_id,))).status_code,
        "anon_get_sales_receipt_loc": (r := c_anon.get(reverse("sales-receipt", args=(s1_old_id,)))).status_code,
        "anon_get_sales_receipt_next": r.get("Location"),
        "invalid_uuid_receipt": c_adm.get("/ventas/constancia/not-a-uuid/").status_code,
        "unknown_uuid_receipt": c_adm.get(reverse("sales-receipt", args=(uuid.uuid4(),))).status_code,
        "post_method_not_allowed_receipt": c_adm.post(reverse("sales-receipt", args=(s1_old_id,)), {"csrfmiddlewaretoken": adm_csrf}).status_code,
        "post_method_not_allowed_sales_history": c_adm.post(reverse("sales-history"), {"csrfmiddlewaretoken": adm_csrf}).status_code,
        "post_method_not_allowed_cash_history": c_adm.post(reverse("cash-shift-history"), {"csrfmiddlewaretoken": adm_csrf}).status_code,
    },
    "filters_and_columns": {
        "sales_history_has_fecha_desde_input": 'name="fecha_desde"' in sales_hist_adm.content.decode("utf-8"),
        "sales_history_has_fecha_hasta_input": 'name="fecha_hasta"' in sales_hist_adm.content.decode("utf-8"),
        "sales_history_has_vendedor_select": 'name="vendedor"' in sales_hist_adm.content.decode("utf-8"),
        "sales_history_has_turno_select": 'name="turno"' in sales_hist_adm.content.decode("utf-8"),
        "sales_history_filters_ignored_count": sales_hist_adm_filtered_v2.context["sales"].count(),
        "seller1_sales_history_excludes_seller2": fixture["sales"]["s2_v2"]["correlative"] not in sales_hist_s1.content.decode("utf-8"),
        "cash_history_has_total_cobrado_column": "Total cobrado" in cash_hist_adm.content.decode("utf-8"),
        "cash_history_has_fecha_desde_input": 'name="fecha_desde"' in cash_hist_adm.content.decode("utf-8"),
        "cash_history_has_vendedor_select": 'name="vendedor"' in cash_hist_adm.content.decode("utf-8"),
        "cash_history_filters_ignored_count": cash_hist_adm_filtered_v2.context["shifts"].count(),
        "cash_closed_has_total_cobrado": "Total cobrado" in cash_closed_adm.content.decode("utf-8"),
        "seller_sidebar_has_sales_history_link": 'href="/ventas/historial/"' in draft_html,
        "seller_sidebar_has_cash_history_link": 'href="/caja/turnos/"' in draft_html,
    },
}

# ── Probe 4: Chrome pre-fix UI / print / overflow / alignment probes ─────────
server = None
chrome_port = 0
chrome_repro = {}
try:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        chrome_port = sock.getsockname()[1]
    os.environ["AUDIT12_PORT"] = str(chrome_port)
    server = subprocess.Popen(
        [sys.executable, str(SUPPORT / "audit12_run.py"), "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(100):
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", chrome_port)) == 0:
                break
        time.sleep(0.1)

    js_probe = rf"""
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const {{ chromium }} = require(path.join(os.homedir(), ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core"));
(async () => {{
  const creds = JSON.parse(fs.readFileSync(path.join(process.env.AUDIT12_RUN_DIR, ".credentials.json"), "utf8"));
  const base = "http://127.0.0.1:" + process.env.AUDIT12_PORT;
  const s3Id = {json.dumps(s3_id)};
  const sh1Id = {json.dumps(sh1_closed_id)};
  const out = process.env.AUDIT12_OUT;
  const browser = await chromium.launch({{ executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe", headless: true }});

  // Seller 1 at 1366x900 and 1366x768 on receipt + media print
  const ctx = await browser.newContext({{ locale: "es-PE", viewport: {{ width: 1366, height: 900 }} }});
  const page = await ctx.newPage();
  await page.goto(base);
  await page.locator("[name=email]").fill(creds.seller1.email);
  await page.locator("[name=password]").fill(creds.seller1.password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(base + "/inicio/");

  await page.goto(base + "/ventas/constancia/" + s3Id + "/");
  const receipt900 = await page.evaluate(() => {{
    const card = document.getElementById("constancia-interna");
    const csCard = getComputedStyle(card);
    const thRight = document.querySelector("#constancia-interna th.text-right");
    const wrap = document.querySelector("#constancia-interna .table-wrap");
    return {{
      docScrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      docOverflow: document.documentElement.scrollWidth > window.innerWidth,
      wrapOverflowPx: wrap ? wrap.scrollWidth - wrap.clientWidth : 0,
      cardPaddingTop: csCard.paddingTop,
      cardPaddingLeft: csCard.paddingLeft,
      thTextRightAlign: thRight ? getComputedStyle(thRight).textAlign : null,
      hasLiteralPhrase: document.body.innerText.includes("CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO"),
    }};
  }});
  await page.screenshot({{ path: path.join(out, "pre-fix-receipt-1366x900.png"), fullPage: true }});

  await page.setViewportSize({{ width: 1366, height: 768 }});
  await page.emulateMedia({{ media: "print" }});
  const receiptPrint = await page.evaluate(() => ({{
    sidebarDisplay: getComputedStyle(document.querySelector(".app-sidebar")).display,
    noPrintDisplay: getComputedStyle(document.querySelector(".page-heading.no-print")).display,
    docScrollWidth: document.documentElement.scrollWidth,
    innerWidth: window.innerWidth,
    docOverflow: document.documentElement.scrollWidth > window.innerWidth,
  }}));
  await page.emulateMedia({{ media: "screen" }});

  // Admin at 1366x768 on sales history, cash history & cash closed acta
  const ctxAdm = await browser.newContext({{ locale: "es-PE", viewport: {{ width: 1366, height: 768 }} }});
  const pageAdm = await ctxAdm.newPage();
  await pageAdm.goto(base);
  await pageAdm.locator("[name=email]").fill(creds.admin.email);
  await pageAdm.locator("[name=password]").fill(creds.admin.password);
  await pageAdm.locator('button[type="submit"]').click();
  await pageAdm.waitForURL(base + "/inicio/");

  await pageAdm.goto(base + "/ventas/historial/");
  const salesHist768 = await pageAdm.evaluate(() => {{
    const wrap = document.querySelector(".table-responsive");
    return {{
      docScrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      docOverflow: document.documentElement.scrollWidth > window.innerWidth,
      wrapOverflowPx: wrap ? wrap.scrollWidth - wrap.clientWidth : 0,
    }};
  }});
  await pageAdm.screenshot({{ path: path.join(out, "pre-fix-sales-history-1366x768.png"), fullPage: true }});

  await pageAdm.goto(base + "/caja/turnos/");
  const cashHist768 = await pageAdm.evaluate(() => {{
    const wrap = document.querySelector(".table-responsive");
    return {{
      docScrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      docOverflow: document.documentElement.scrollWidth > window.innerWidth,
      wrapOverflowPx: wrap ? wrap.scrollWidth - wrap.clientWidth : 0,
    }};
  }});
  await pageAdm.screenshot({{ path: path.join(out, "pre-fix-cash-history-1366x768.png"), fullPage: true }});

  await pageAdm.goto(base + "/caja/turnos/" + sh1Id + "/cerrado/");
  const cashClosed768 = await pageAdm.evaluate(() => {{
    const panel = document.querySelectorAll("section.panel")[1];
    const cs = panel ? getComputedStyle(panel) : null;
    return {{
      secondPanelPaddingTop: cs ? cs.paddingTop : null,
      secondPanelPaddingLeft: cs ? cs.paddingLeft : null,
      hasTotalCobrado: document.body.innerText.includes("Total cobrado"),
    }};
  }});
  await pageAdm.screenshot({{ path: path.join(out, "pre-fix-cash-closed-1366x768.png"), fullPage: true }});

  console.log(JSON.stringify({{ receipt900, receiptPrint, salesHist768, cashHist768, cashClosed768 }}));
  await browser.close();
}})();
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

# ── Probe 5: PostgreSQL 18.4 pre-fix NUL filter 500 + Lima midnight date filter ──
pg_repro = {}
cluster = (Path(tempfile.gettempdir()) / ("audit12-repro-pg-" + secrets.token_hex(8))).resolve()
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
        [str(PG_BIN / "initdb.exe"), "-D", str(dbdir), "-U", "audit12", "--pwfile", str(pwfile),
         "--auth-host=scram-sha-256", "--auth-local=scram-sha-256", "--encoding=UTF8", "--locale=C"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    pwfile.unlink()
    subprocess.run(
        [str(PG_BIN / "pg_ctl.exe"), "-D", str(dbdir), "-l", str(cluster / "pg.log"),
         "-o", f"-h 127.0.0.1 -p {pg_port} -c log_statement=none -c log_min_error_statement=panic", "-w", "start"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    pg_started = True
    import psycopg
    from psycopg import sql
    from django.db import connections

    dbname = "repro12_" + secrets.token_hex(4)
    with psycopg.connect(host="127.0.0.1", port=pg_port, user="audit12", password=pw_pg, dbname="postgres", autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
    connections.close_all()
    from django.conf import settings
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": dbname, "USER": "audit12", "PASSWORD": pw_pg, "HOST": "127.0.0.1", "PORT": pg_port,
        "CONN_MAX_AGE": 0, "CONN_HEALTH_CHECKS": False, "ATOMIC_REQUESTS": False, "AUTOCOMMIT": True,
        "TIME_ZONE": "America/Lima",
        "OPTIONS": {"options": "-c statement_timeout=15000 -c lock_timeout=10000"},
    }
    del connections["default"]
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    from identity.models import Role
    from cash.models import CashRegister
    r_adm = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    r_sel = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
    adm_pg = Account.objects.create_user("pg12adm@test.invalid", "PgPass123!", display_name="PG12 Adm", role=r_adm)
    sel_pg = Account.objects.create_user("pg12sel@test.invalid", "PgPass123!", display_name="PG12 Sel", role=r_sel)
    reg_pg = CashRegister.objects.create(code="CAJA-01")
    sh_pg = CashShift.objects.create(cash_register=reg_pg, seller=sel_pg, opening_amount=Decimal("50.00"))
    s_before_mid = Sale.objects.create(
        cash_shift=sh_pg, seller=sel_pg, total_amount=Decimal("10.00"),
        base_amount=Decimal("8.47"), igv_amount=Decimal("1.53"),
        cash_received=Decimal("10.00"), change_given=Decimal("0.00"),
        correlative="V-00000001", idempotency_key=uuid.uuid4(),
    )
    # 2026-11-11T04:59:59Z == 2026-11-10 23:59:59 America/Lima
    Sale.objects.filter(pk=s_before_mid.pk).update(confirmed_at=datetime(2026, 11, 11, 4, 59, 59, tzinfo=timezone.utc))
    s_after_mid = Sale.objects.create(
        cash_shift=sh_pg, seller=sel_pg, total_amount=Decimal("15.00"),
        base_amount=Decimal("12.71"), igv_amount=Decimal("2.29"),
        cash_received=Decimal("20.00"), change_given=Decimal("5.00"),
        correlative="V-00000002", idempotency_key=uuid.uuid4(),
    )
    # 2026-11-11T05:00:00Z == 2026-11-11 00:00:00 America/Lima
    Sale.objects.filter(pk=s_after_mid.pk).update(confirmed_at=datetime(2026, 11, 11, 5, 0, 0, tzinfo=timezone.utc))

    c_pg = Client()
    c_pg.force_login(adm_pg)
    nul_error = None
    try:
        r_nul = c_pg.get(reverse("sales-history"), {"correlativo": "V-\x00"})
        nul_status = r_nul.status_code
    except Exception as exc:
        nul_status = 500
        nul_error = f"{type(exc).__name__}: {exc}"

    r_lima_10 = c_pg.get(reverse("sales-history"), {"fecha": "2026-11-10"})
    r_lima_11 = c_pg.get(reverse("sales-history"), {"fecha": "2026-11-11"})
    pg_repro["nul_correlativo_crash"] = {"status": nul_status, "error": nul_error}
    pg_repro["lima_midnight_filter"] = {
        "fecha_2026_11_10_correlatives": [s.correlative for s in r_lima_10.context["sales"]],
        "fecha_2026_11_11_correlatives": [s.correlative for s in r_lima_11.context["sales"]],
    }
finally:
    connections.close_all()
    if pg_started:
        subprocess.run([str(PG_BIN / "pg_ctl.exe"), "-D", str(dbdir), "-m", "fast", "-w", "stop"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    with socket.socket() as s:
        pg_repro["port_closed"] = s.connect_ex(("127.0.0.1", pg_port)) != 0

findings["pg_repro"] = pg_repro
findings["protected_unchanged"] = {
    k: (digest(ROOT / k) if (ROOT / k).exists() else None) == v for k, v in start_hashes.items()
}
(OUT_DIR / "repro.json").write_text(json.dumps(findings, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
print(json.dumps({
    "evidence": str((OUT_DIR / "repro.json").relative_to(ROOT)),
    "checkout_retry_real_effect": findings["checkout_retry_real_effect"],
    "receipt_and_pos_defects": findings["receipt_and_pos_defects"],
    "cache_control_before_fix": findings["cache_control_before_fix"],
    "history_and_permissions_repro": findings["history_and_permissions_repro"],
    "chrome_pre_fix": findings["chrome_pre_fix"].get("parsed"),
    "pg_repro": findings["pg_repro"],
    "protected_unchanged": all(findings["protected_unchanged"].values()),
}, ensure_ascii=False, indent=2))
