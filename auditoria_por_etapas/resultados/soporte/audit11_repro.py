"""Pre-fix Stage 11 reproduction & behavior probes (isolated SQLite + Chrome + ephemeral PG 18.4).
Captures exact pre-edit defects and boundary behavior before applying any code fix.
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
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
SUPPORT = Path(__file__).resolve().parent
PG_BIN = Path("C:/Program Files/PostgreSQL/18/bin")

STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
RUN_DIR = RESULTS / "datos" / f"etapa11-repro-{STAMP}"
OUT_DIR = RESULTS / "evidencias" / f"11-repro-{STAMP}"
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
    AUDIT11_RUN_DIR=str(RUN_DIR),
    AUDIT11_OUT=str(OUT_DIR),
    AUDIT11_DEFAULT_COOKIES="1",
    DJANGO_SETTINGS_MODULE="audit11_settings",
)
sys.path.insert(0, str(APP))
sys.path.insert(0, str(SUPPORT))

import django

django.setup()

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.management import call_command
from django.test import Client
from django.test.utils import setup_test_environment

setup_test_environment()
from django.urls import reverse
from django.utils import timezone as tz

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    call_command("migrate", interactive=False, verbosity=0)

import audit11_run
from cash.models import CashRegister, CashShift
from cash.services import close_cash_shift
from catalog.models import Category, Product
from identity.models import Account, Role
from inventory.models import Lot
from sales.forms import CheckoutForm
from sales.models import Sale, SaleCounter, SaleDraft, SaleDraftLine, SaleLine
from sales.services import add_product_to_draft, checkout_sale, draft_totals

fixture = audit11_run.prepare_stage11_fixtures(RUN_DIR, OUT_DIR)
creds = json.loads((RUN_DIR / ".credentials.json").read_text(encoding="utf-8"))

seller = Account.objects.get(email=creds["seller"]["email"])
inactive_seller = Account.objects.get(email=creds["inactive_seller"]["email"])
admin = Account.objects.get(email=creds["admin"]["email"])
warehouse = Account.objects.get(email=creds["warehouse"]["email"])
p_fefo = Product.objects.get(pk=fixture["products"]["fefo"]["id"])
p_tax = Product.objects.get(pk=fixture["products"]["tax"]["id"])
p_price = Product.objects.get(pk=fixture["products"]["price"]["id"])
p_long = Product.objects.get(pk=fixture["products"]["long"]["id"])

findings: dict[str, object] = {
    "stamp_utc": STAMP,
    "protected_absent_at_start": [k for k, v in start_hashes.items() if v is None],
}

# ── Probe 1: Service-level defects before fix ────────────────────────────────
# 1a: Inactive seller direct call to add_product_to_draft & checkout_sale
# Note: prepare an active shift directly if testing inactive seller checkout, or add_product_to_draft.
reg = CashRegister.objects.get(code="CAJA-01")
shift_main = CashShift.objects.get(pk=fixture["shift"]["id"])
inact_reg = CashRegister.objects.create(code="CAJA-INACT-REPRO")
inact_shift = CashShift.objects.create(cash_register=inact_reg, seller=inactive_seller, opening_amount=Decimal("20.00"))
draft_inact = None
try:
    draft_inact = add_product_to_draft(actor=inactive_seller, product_id=p_tax.pk, quantity=1)
    sale_inact = checkout_sale(
        actor=inactive_seller,
        draft_id=draft_inact.pk,
        cash_received=Decimal("5.00"),
        idempotency_key=uuid.uuid4(),
    )
    findings["service_inactive_seller_defect_reproduced"] = {
        "bug_present": True,
        "sale_id": str(sale_inact.pk),
        "correlative": sale_inact.correlative,
    }
    SaleLine.objects.filter(sale=sale_inact).delete()
    sale_inact.delete()
    SaleDraftLine.objects.filter(draft=draft_inact).delete()
    draft_inact.delete()
    Lot.objects.filter(product=p_tax).update(available_quantity=20)
    SaleCounter.objects.filter(id=1).update(next_value=1)
except (PermissionDenied, ValidationError) as exc:
    findings["service_inactive_seller_defect_reproduced"] = {"bug_present": False, "error": str(exc)}
    SaleDraftLine.objects.filter(draft__seller=inactive_seller).delete()
    SaleDraft.objects.filter(seller=inactive_seller).delete()
finally:
    inact_shift.delete()
    inact_reg.delete()

# 1b: >2 decimals silently quantized (ROUND_HALF_EVEN) in direct checkout_sale call
draft_dec = add_product_to_draft(actor=seller, product_id=p_tax.pk, quantity=2)  # subtotal = 7.10
key_dec = uuid.uuid4()
try:
    sale_dec = checkout_sale(
        actor=seller,
        draft_id=draft_dec.pk,
        cash_received=Decimal("10.005"),
        discount_amount=Decimal("1.005"),
        idempotency_key=key_dec,
    )
    findings["service_3decimals_silent_quantize_defect"] = {
        "bug_present": True,
        "stored_discount": str(sale_dec.discount_amount),
        "stored_cash": str(sale_dec.cash_received),
        "stored_change": str(sale_dec.change_given),
        "stored_total": str(sale_dec.total_amount),
    }
    # Also test 1c: reusing SAME idempotency_key + SAME draft_id with DIFFERENT cash/discount!
    reused_diff = checkout_sale(
        actor=seller,
        draft_id=draft_dec.pk,
        cash_received=Decimal("50.00"),
        discount_amount=Decimal("2.00"),
        idempotency_key=key_dec,
    )
    findings["service_idem_diff_payload_defect"] = {
        "bug_present": reused_diff.pk == sale_dec.pk,
        "returned_sale_id": str(reused_diff.pk),
        "returned_cash_received": str(reused_diff.cash_received),
        "returned_discount_amount": str(reused_diff.discount_amount),
    }
    SaleLine.objects.filter(sale=sale_dec).delete()
    sale_dec.delete()
    SaleDraftLine.objects.filter(draft=draft_dec).delete()
    draft_dec.delete()
    Lot.objects.filter(product=p_tax).update(available_quantity=20)
    SaleCounter.objects.filter(id=1).update(next_value=1)
except ValidationError as exc:
    findings["service_3decimals_silent_quantize_defect"] = {"bug_present": False, "error": str(exc)}
    SaleDraftLine.objects.filter(draft=draft_dec).delete()
    draft_dec.delete()

# ── Probe 2: Form & HTTP View boundary probes ────────────────────────────────
c_seller = Client(enforce_csrf_checks=True)
assert c_seller.login(username=creds["seller"]["email"], password=creds["seller"]["password"])

draft_http = add_product_to_draft(actor=seller, product_id=p_price.pk, quantity=1)  # 10.00
get_co = c_seller.get(reverse("sales-checkout"))
init = get_co.context["form"].initial
csrf_tok = get_co.cookies["csrftoken"].value

form_probes = {}
for label, payload in [
    ("discount_equal_subtotal_100pct", {"cash_received": "10.00", "discount_amount": "10.00"}),
    ("discount_gt_subtotal", {"cash_received": "10.00", "discount_amount": "11.00"}),
    ("discount_negative", {"cash_received": "10.00", "discount_amount": "-1.00"}),
    ("discount_3decimals", {"cash_received": "10.00", "discount_amount": "1.005"}),
    ("discount_scientific", {"cash_received": "10.00", "discount_amount": "1e2"}),
    ("discount_nul", {"cash_received": "10.00", "discount_amount": "1\x00"}),
    ("discount_arabic", {"cash_received": "10.00", "discount_amount": "١.٠٠"}),
    ("cash_zero", {"cash_received": "0.00", "discount_amount": ""}),
    ("cash_3decimals", {"cash_received": "10.005", "discount_amount": ""}),
    ("cash_scientific", {"cash_received": "1e2", "discount_amount": ""}),
    ("cash_nul", {"cash_received": "10\x00", "discount_amount": ""}),
    ("cash_arabic", {"cash_received": "١٠.٠٠", "discount_amount": ""}),
    ("cash_insufficient_with_valid_discount", {"cash_received": "7.00", "discount_amount": "2.00"}),
]:
    p = {
        "csrfmiddlewaretoken": csrf_tok,
        "idempotency_key": str(uuid.uuid4()),
        "expected_subtotal": str(init["expected_subtotal"]),
        "draft_signature": init["draft_signature"],
        **payload,
    }
    resp = c_seller.post(reverse("sales-checkout"), p)
    form_ctx = resp.context.get("form") if resp.context else None
    form_probes[label] = {
        "status": resp.status_code,
        "location": resp.get("Location"),
        "sales_count": Sale.objects.count(),
        "form_errors": dict(form_ctx.errors) if form_ctx else None,
        "displayed_total": str(resp.context["totals"].total) if resp.context and "totals" in resp.context else None,
    }
    if resp.status_code == 302:
        SaleLine.objects.all().delete()
        Sale.objects.all().delete()
        SaleDraftLine.objects.all().delete()
        SaleDraft.objects.all().delete()
        Lot.objects.filter(product=p_price).update(available_quantity=10)
        SaleCounter.objects.filter(id=1).update(next_value=1)
        add_product_to_draft(actor=seller, product_id=p_price.pk, quantity=1)
        get_co = c_seller.get(reverse("sales-checkout"))
        init = get_co.context["form"].initial
        csrf_tok = get_co.cookies["csrftoken"].value
findings["http_form_probes"] = form_probes

# Probe 2b: draft discarded mid-POST in Checkout ValidationError branch (sales/views.py L222-253)
c_seller2 = Client(enforce_csrf_checks=True)
c_seller2.cookies = c_seller.cookies.copy()
orig_checkout_svc = sys.modules["sales.views"].checkout_sale

def _discard_during_checkout(**kwargs):
    draft_obj = SaleDraft.objects.get(pk=kwargs["draft_id"])
    SaleDraftLine.objects.filter(draft=draft_obj).delete()
    draft_obj.status = SaleDraft.Status.DISCARDED
    draft_obj.save(update_fields=["status"])
    return orig_checkout_svc(**kwargs)

get_co2 = c_seller.get(reverse("sales-checkout"))
init2 = get_co2.context["form"].initial
csrf_tok2 = get_co2.cookies["csrftoken"].value
with patch("sales.views.checkout_sale", side_effect=_discard_during_checkout):
    r_vanish = c_seller.post(
        reverse("sales-checkout"),
        {
            "csrfmiddlewaretoken": csrf_tok2,
            "cash_received": "20.00",
            "discount_amount": "",
            "idempotency_key": str(uuid.uuid4()),
            "expected_subtotal": str(init2["expected_subtotal"]),
            "draft_signature": init2["draft_signature"],
        },
    )
findings["view_vanished_draft_renders_empty_checkout_bug"] = {
    "status": r_vanish.status_code,
    "renders_empty_draft": r_vanish.status_code == 200 and r_vanish.context.get("draft") is None,
    "subtotal": str(r_vanish.context.get("subtotal")) if r_vanish.context else None,
}

# Clean up vanished draft
SaleDraftLine.objects.all().delete()
SaleDraft.objects.all().delete()

# ── Probe 3: Cache headers on sales/cash endpoints ───────────────────────────
add_product_to_draft(actor=seller, product_id=p_price.pk, quantity=1)
get_co3 = c_seller.get(reverse("sales-checkout"))
init3 = get_co3.context["form"].initial
csrf_tok3 = get_co3.cookies["csrftoken"].value
post_sale = c_seller.post(
    reverse("sales-checkout"),
    {
        "csrfmiddlewaretoken": csrf_tok3,
        "cash_received": "20.00",
        "discount_amount": "1.50",
        "idempotency_key": str(uuid.uuid4()),
        "expected_subtotal": str(init3["expected_subtotal"]),
        "draft_signature": init3["draft_signature"],
    },
)
sale_obj = Sale.objects.get()
c_admin = Client(enforce_csrf_checks=True)
assert c_admin.login(username=creds["admin"]["email"], password=creds["admin"]["password"])
findings["cache_control_before_fix"] = {
    "sales_checkout": get_co3.headers.get("Cache-Control", ""),
    "sales_receipt": c_seller.get(reverse("sales-receipt", args=(sale_obj.pk,))).headers.get("Cache-Control", ""),
    "sales_history": c_admin.get(reverse("sales-history")).headers.get("Cache-Control", ""),
    "sales_shift_history": c_seller.get(reverse("sales-shift-history")).headers.get("Cache-Control", ""),
    "cash_close": c_seller.get(reverse("cash-close")).headers.get("Cache-Control", ""),
}

# Cleanup sale before Chrome probe
SaleLine.objects.all().delete()
Sale.objects.all().delete()
SaleDraftLine.objects.all().delete()
SaleDraft.objects.all().delete()
Lot.objects.filter(product=p_price).update(available_quantity=10)
SaleCounter.objects.filter(id=1).update(next_value=1)

# ── Probe 4: Huge subtotal (>9,999,999.99) vs CheckoutForm cap ───────────────
p_huge = Product.objects.create(
    category=Category.objects.filter(is_active=True).first(),
    name="Producto Precio Max",
    barcode="775110000999",
    sale_price=Decimal("9999999.99"),
    minimum_stock=1,
)
from inventory.services import LotInput, confirm_initial_load
confirm_initial_load(
    actor=warehouse,
    product=p_huge,
    lots=[LotInput("HUGE-1", 5, Decimal("100.0000"), tz.localdate() + timedelta(days=20))],
)
draft_huge = add_product_to_draft(actor=seller, product_id=p_huge.pk, quantity=2)  # subtotal = 19,999,999.98
f_huge = CheckoutForm(
    data={
        "cash_received": "20000000.00",
        "discount_amount": "",
        "idempotency_key": str(uuid.uuid4()),
    }
)
findings["huge_subtotal_blocked_by_cash_max_value"] = {
    "subtotal": str(draft_totals(draft_huge).total),
    "form_valid": f_huge.is_valid(),
    "errors": dict(f_huge.errors),
}
SaleDraftLine.objects.filter(draft=draft_huge).delete()
draft_huge.delete()
p_huge.lots.all().delete()
p_huge.initial_load.delete()
p_huge.delete()

# ── Probe 5: Chrome pre-fix UI probe (double click, badInput, long wrap, notices)
draft_ui = add_product_to_draft(actor=seller, product_id=p_long.pk, quantity=1)
server = None
chrome_port = 0
chrome_repro = {}
try:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        chrome_port = sock.getsockname()[1]
    os.environ["AUDIT11_PORT"] = str(chrome_port)
    server = subprocess.Popen(
        [sys.executable, str(SUPPORT / "audit11_run.py"), "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(100):
        with socket.socket() as sock:
            if sock.connect_ex(("127.0.0.1", chrome_port)) == 0:
                break
        time.sleep(0.1)

    js_probe = r"""
const fs = require("node:fs");
const path = require("node:path");
const os = require("node:os");
const { chromium } = require(path.join(os.homedir(), ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright-core"));
(async () => {
  const creds = JSON.parse(fs.readFileSync(path.join(process.env.AUDIT11_RUN_DIR, ".credentials.json"), "utf8"));
  const base = "http://127.0.0.1:" + process.env.AUDIT11_PORT;
  const browser = await chromium.launch({ executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe", headless: true });
  const ctx = await browser.newContext({ locale: "es-PE", viewport: { width: 1366, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(base);
  await page.locator("[name=email]").fill(creds.seller.email);
  await page.locator("[name=password]").fill(creds.seller.password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL(base + "/inicio/");
  await page.goto(base + "/ventas/cobrar/");

  // Check overflow on long product name
  const layoutBefore = await page.evaluate(() => ({
    docScrollWidth: document.documentElement.scrollWidth,
    windowInnerWidth: window.innerWidth,
    docOverflow: document.documentElement.scrollWidth > window.innerWidth,
    hasSubtotalRow: document.querySelector(".sale-totals").innerText.includes("Subtotal"),
    hasTaxWarning: document.body.innerText.includes("No emite una boleta ni factura"),
  }));

  // Test badInput on discount_amount (typing "1e2" leaves discInput.value === "" in Chrome)
  await page.locator("#id_discount_amount").focus();
  await page.keyboard.type("1e2");
  const badInputState = await page.evaluate(() => {
    const el = document.getElementById("id_discount_amount");
    return {
      value: el.value,
      badInput: el.validity.badInput,
      totalText: document.getElementById("checkout-total").textContent,
    };
  });

  await page.locator("#id_discount_amount").fill("2.00");
  await page.locator("#id_cash_received").fill("20.00");
  await page.screenshot({ path: path.join(process.env.AUDIT11_OUT, "pre-fix-checkout.png"), fullPage: true });

  // Double-click Confirmar cobro rapidly and count POSTs sent
  let checkoutPosts = 0;
  page.on("request", (r) => { if (r.method() === "POST" && r.url().includes("/ventas/cobrar/")) checkoutPosts++; });
  await Promise.all([
    page.getByRole("button", { name: "Confirmar cobro", exact: true }).click(),
    page.getByRole("button", { name: "Confirmar cobro", exact: true }).click().catch(() => {}),
  ]);
  await page.waitForURL(/\/ventas\/constancia\//);
  const finalUrl = page.url();
  const receiptOverflow = await page.evaluate(() => ({
    url: location.pathname,
    docScrollWidth: document.documentElement.scrollWidth,
    windowInnerWidth: window.innerWidth,
    docOverflow: document.documentElement.scrollWidth > window.innerWidth,
    hasSunatPhraseRequiredByRN26: document.body.innerText.includes("CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO"),
  }));
  await page.screenshot({ path: path.join(process.env.AUDIT11_OUT, "pre-fix-receipt.png"), fullPage: true });

  console.log(JSON.stringify({ layoutBefore, badInputState, checkoutPosts, finalUrl, receiptOverflow }));
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

# ── Probe 6: PostgreSQL 18.4 pre-fix concurrent divergent idempotency key bug ──
pg_repro = {}
cluster = (Path(tempfile.gettempdir()) / ("audit11-repro-pg-" + secrets.token_hex(8))).resolve()
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
    for cmd_args in (
        [str(PG_BIN / "initdb.exe"), "-D", str(dbdir), "-U", "audit11", "--pwfile", str(pwfile),
         "--auth-host=scram-sha-256", "--auth-local=scram-sha-256", "--encoding=UTF8", "--locale=C"],
    ):
        subprocess.run(cmd_args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
    pwfile.unlink()
    subprocess.run(
        [str(PG_BIN / "pg_ctl.exe"), "-D", str(dbdir), "-l", str(cluster / "pg.log"),
         "-o", f"-h 127.0.0.1 -p {pg_port} -c log_statement=none -c log_min_error_statement=panic", "-w", "start"],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW,
    )
    pg_started = True
    import psycopg
    from psycopg import sql
    from django.db import close_old_connections, connections
    dbname = "repro11_" + secrets.token_hex(4)
    with psycopg.connect(host="127.0.0.1", port=pg_port, user="audit11", password=pw_pg, dbname="postgres", autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))
    connections.close_all()
    from django.conf import settings
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": dbname, "USER": "audit11", "PASSWORD": pw_pg, "HOST": "127.0.0.1", "PORT": pg_port,
        "CONN_MAX_AGE": 0, "CONN_HEALTH_CHECKS": False, "ATOMIC_REQUESTS": False, "AUTOCOMMIT": True,
        "TIME_ZONE": "America/Lima",
        "OPTIONS": {"options": "-c statement_timeout=15000 -c lock_timeout=10000"},
    }
    del connections["default"]
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    r_adm = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    r_wh = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    r_sel = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
    s_u = Account.objects.create_user("pg11@test.invalid", "PgPass123!", display_name="PG11 Seller", role=r_sel)
    w_u = Account.objects.create_user("pg11w@test.invalid", "PgPass123!", display_name="PG11 WH", role=r_wh)
    cat_pg = Category.objects.create(name="PG11 Cat")
    prod_pg = Product.objects.create(category=cat_pg, name="PG11 Prod", barcode="77511999", sale_price=Decimal("10.00"))
    from inventory.services import LotInput as PgLot, confirm_initial_load as pg_load
    pg_load(actor=w_u, product=prod_pg, lots=[PgLot("PGL-1", 10, Decimal("4.0000"), tz.localdate() + timedelta(days=10))])
    CashShift.objects.create(cash_register=CashRegister.objects.create(code="CAJA-01"), seller=s_u, opening_amount=Decimal("50.00"))
    d_pg = add_product_to_draft(actor=s_u, product_id=prod_pg.pk, quantity=1)
    k_pg = uuid.uuid4()

    # Check concurrent race on SAME key + SAME draft + DIFFERENT payload in PG
    evt_locked = threading.Event()
    evt_release = threading.Event()
    orig_create = Sale.objects.create

    def worker_a():
        close_old_connections()
        try:
            with patch.object(Sale.objects, "create", side_effect=lambda **kw: (evt_locked.set(), evt_release.wait(5), orig_create(**kw))[2]):
                res = checkout_sale(actor=s_u, draft_id=d_pg.pk, cash_received=Decimal("10.00"), idempotency_key=k_pg)
                return {"ok": True, "sale_id": str(res.pk), "cash": str(res.cash_received)}
        except Exception as e:
            return {"ok": False, "error": str(e)}
        finally:
            close_old_connections()

    def worker_b():
        close_old_connections()
        try:
            evt_locked.wait(5)
            res = checkout_sale(actor=s_u, draft_id=d_pg.pk, cash_received=Decimal("50.00"), discount_amount=Decimal("2.00"), idempotency_key=k_pg)
            return {"ok": True, "sale_id": str(res.pk), "cash": str(res.cash_received), "discount": str(res.discount_amount)}
        except Exception as e:
            return {"ok": False, "error": str(e)}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        fa = pool.submit(worker_a)
        fb = pool.submit(worker_b)
        time.sleep(0.4)
        evt_release.set()
        ra = fa.result(timeout=10)
        rb = fb.result(timeout=10)

    pg_repro["concurrent_same_key_diff_payload_before_fix"] = {
        "worker_a": ra,
        "worker_b": rb,
        "bug_present": bool(ra.get("ok") and rb.get("ok") and ra.get("sale_id") == rb.get("sale_id")),
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
    "inactive_seller_bug": findings["service_inactive_seller_defect_reproduced"],
    "3decimals_bug": findings["service_3decimals_silent_quantize_defect"],
    "idem_diff_payload_bug": findings.get("service_idem_diff_payload_defect"),
    "vanished_draft_bug": findings["view_vanished_draft_renders_empty_checkout_bug"],
    "cache_control": findings["cache_control_before_fix"],
    "huge_subtotal": findings["huge_subtotal_blocked_by_cash_max_value"],
    "chrome_pre_fix": findings["chrome_pre_fix"].get("parsed"),
    "pg_repro": findings["pg_repro"],
    "protected_unchanged": all(findings["protected_unchanged"].values()),
}, ensure_ascii=False, indent=2))
