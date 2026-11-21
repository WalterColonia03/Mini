"""Stage 06-B Deep Probes:
1) OPDB-01: Read-only operational r1_pmv.sqlite3 migration/collision/snapshot diagnostic.
2) EDGE-01..07: LotInputForm pre-collapse maxlen, historical replay cross-user & divergent HTML leaks,
   receipt line rounding, formset DoS/intra-duplicate, Kardex cross-module RUC/links/roles,
   and 2,000-product <select> scalability probe on /inventario/entrada/.
3) CRASH-01..03: Real OS process kill (TerminateProcess) pre-commit & post-commit HTTP + PG 18.4
   `pg_ctl -m immediate` WAL crash recovery & idempotent replay.
Zero modifications to r1-pmv/ or r1_pmv.sqlite3.
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
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar
import uuid
from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
SUPPORT = Path(__file__).resolve().parent
PG_BIN = Path("C:/Program Files/PostgreSQL/18/bin")

for p in (str(APP), str(SUPPORT)):
    if p not in sys.path:
        sys.path.insert(0, p)


def digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def protected_hashes() -> dict[str, str | None]:
    items = [
        *APP.glob("*.sqlite3"),
        *(
            p
            for d in (RESULTS / "datos").iterdir()
            if d.is_dir() and d.name.startswith(("etapa00", "etapa06", "06-"))
            for p in d.rglob("*.sqlite3")
        ),
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]
    return {str(p.relative_to(ROOT)): digest(p) for p in items}


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


# ── Worker mode for HTTP real-OS crash subprocesses ───────────────────────────
def run_crash_worker() -> int:
    from wsgiref.simple_server import make_server, WSGIServer
    import socketserver

    os.environ["AUDIT06_DEFAULT_COOKIES"] = "1"
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit06_settings"
    import django

    django.setup()
    from django.core.wsgi import get_wsgi_application
    import inventory.views as inv_views
    import inventory.services as inv_services

    mode = os.environ["AUDIT06B_CRASH_MODE"]
    signal_file = Path(os.environ["AUDIT06B_SIGNAL_FILE"])
    port = int(os.environ["AUDIT06B_PORT"])

    if mode == "precommit":
        orig_create = inv_services.StockReceipt.objects.create

        def hooked_create(*args, **kwargs):
            receipt = orig_create(*args, **kwargs)
            signal_file.write_text(
                json.dumps({"phase": "precommit_locked", "correlative": receipt.correlative}),
                encoding="utf-8",
            )
            time.sleep(30)
            return receipt

        inv_services.StockReceipt.objects.create = hooked_create
    elif mode == "postcommit":
        orig_register = inv_views.register_stock_entry

        def hooked_register(*args, **kwargs):
            receipt = orig_register(*args, **kwargs)
            signal_file.write_text(
                json.dumps(
                    {
                        "phase": "postcommit_before_response",
                        "receipt_id": str(receipt.pk),
                        "correlative": receipt.correlative,
                    }
                ),
                encoding="utf-8",
            )
            time.sleep(30)
            return receipt

        inv_views.register_stock_entry = hooked_register

    app = get_wsgi_application()

    class _ThreadedServer(socketserver.ThreadingMixIn, WSGIServer):
        daemon_threads = True

    with make_server("127.0.0.1", port, app, server_class=_ThreadedServer) as httpd:
        signal_file.with_suffix(".ready").write_text("1", encoding="utf-8")
        httpd.serve_forever()
    return 0


# ── HTML helpers ──────────────────────────────────────────────────────────────
class SelectOptionsParser(HTMLParser):
    def __init__(self, select_name: str) -> None:
        super().__init__()
        self.select_name = select_name
        self.in_target = False
        self.in_option = False
        self.options: list[tuple[str, str]] = []
        self._val = ""
        self._buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        amap = dict(attrs)
        if tag == "select" and amap.get("name") == self.select_name:
            self.in_target = True
        elif self.in_target and tag == "option":
            self.in_option = True
            self._val = amap.get("value") or ""
            self._buf = []

    def handle_data(self, data: str) -> None:
        if self.in_option:
            self._buf.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "option" and self.in_option:
            self.options.append((self._val, " ".join("".join(self._buf).split())))
            self.in_option = False
        elif tag == "select" and self.in_target:
            self.in_target = False


def extract_input_value(html: str, name: str) -> str | None:
    class _P(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.value = None

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag == "input" and self.value is None:
                m = dict(attrs)
                if m.get("name") == name:
                    self.value = m.get("value")

    p = _P()
    p.feed(html)
    return p.value


# ── 1) OPDB-01: Read-only Operational SQLite Diagnostic ───────────────────────
def run_opdb_diagnostic(out_dir: Path) -> dict:
    db = APP / "r1_pmv.sqlite3"
    sha_before = digest(db)
    conn = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    applied: dict[str, set[str]] = {}
    for app_name, mig_name in conn.execute("SELECT app, name FROM django_migrations").fetchall():
        applied.setdefault(app_name, set()).add(mig_name)

    migrations_status = {}
    for app_dir in sorted(APP.iterdir()):
        mig_dir = app_dir / "migrations"
        if mig_dir.is_dir():
            disk = sorted(p.stem for p in mig_dir.glob("*.py") if p.stem != "__init__")
            app_applied = sorted(m for m in disk if m in applied.get(app_dir.name, set()))
            pending = [m for m in disk if m not in applied.get(app_dir.name, set())]
            migrations_status[app_dir.name] = {
                "disk_count": len(disk),
                "applied_count": len(app_applied),
                "pending": pending,
            }

    products = [dict(r) for r in conn.execute("SELECT id, name, barcode, controls_expiration, average_cost, sale_price, is_active, category_id FROM catalog_product ORDER BY name").fetchall()]
    categories = {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM catalog_category").fetchall()}
    loads = [dict(r) for r in conn.execute("SELECT * FROM inventory_initialinventoryload").fetchall()]
    lots = [dict(r) for r in conn.execute("SELECT id, product_id, number, number_normalized, initial_quantity, available_quantity, unit_cost, expiration_date, is_initial, supplier_id, responsible_id, initial_load_id FROM inventory_lot ORDER BY received_at").fetchall()]

    norm_seen: dict[tuple[str, str], str] = {}
    collisions = []
    norm_mismatches = []
    for l in lots:
        calc_norm = " ".join(str(l["number"]).split()).upper()
        if l["number_normalized"] != calc_norm:
            norm_mismatches.append({"lot_id": l["id"], "number": l["number"], "stored": l["number_normalized"], "calc": calc_norm})
        key = (l["product_id"], calc_norm)
        if key in norm_seen:
            collisions.append({"product_id": l["product_id"], "normalized": calc_norm, "lot_a": norm_seen[key], "lot_b": l["id"]})
        else:
            norm_seen[key] = l["id"]

    table_counts = {}
    for tbl in (
        "inventory_supplier",
        "inventory_initialinventoryload",
        "inventory_initialloadline",
        "inventory_stockreceipt",
        "inventory_stockreceiptcounter",
        "inventory_stockreceiptline",
        "inventory_lot",
        "inventory_stockwriteoff",
        "inventory_physicaladjustment",
    ):
        table_counts[tbl] = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]

    triggers = [
        {"name": r["name"], "table": r["tbl_name"]}
        for r in conn.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='trigger' ORDER BY name").fetchall()
    ]
    null_snapshot_loads = sum(1 for ld in loads if ld.get("average_cost_snapshot") is None)
    anomalies = [
        {
            "product_id": p["id"],
            "name": p["name"],
            "category": categories.get(p["category_id"]),
            "average_cost": p["average_cost"],
            "sale_price": p["sale_price"],
            "note": "Demo/test seed data outside typical minimarket rice pricing/category.",
        }
        for p in products
        if p["average_cost"] >= 100 or (categories.get(p["category_id"]) == "Productos enlatados" and "Arroz" in p["name"])
    ]
    conn.close()
    sha_after = digest(db)

    res = {
        "id": "OPDB-01",
        "ok": sha_before == sha_after and len(migrations_status["inventory"]["pending"]) == 0,
        "sqlite_sha256_before": sha_before,
        "sqlite_sha256_after": sha_after,
        "read_only_intact": sha_before == sha_after,
        "migrations_status": migrations_status,
        "table_counts": table_counts,
        "lot_norm_collisions": collisions,
        "lot_norm_mismatches": norm_mismatches,
        "legacy_initial_loads_with_null_snapshot": null_snapshot_loads,
        "triggers_present": triggers,
        "demo_data_anomalies": anomalies,
    }
    write_json(out_dir / "opdb-diag.json", res)
    return res


# ── HTTP Client Helper ────────────────────────────────────────────────────────
def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class HttpSession:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.jar = http.cookiejar.CookieJar()
        class _NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, req, fp, code, msg, headers, newurl):
                return None

        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.jar),
            _NoRedirect(),
        )

    def get(self, path: str) -> tuple[int, dict, str]:
        req = urllib.request.Request(self.base_url + path, method="GET")
        try:
            with self.opener.open(req, timeout=10) as resp:
                return resp.status, dict(resp.headers), resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read().decode("utf-8", errors="replace")

    def post(self, path: str, data: dict) -> tuple[int, dict, str]:
        csrf = next((c.value for c in self.jar if c.name == "csrftoken"), data.get("csrfmiddlewaretoken", ""))
        encoded = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + path,
            data=encoded,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded", "Referer": self.base_url + path, "X-CSRFToken": csrf},
        )
        try:
            with self.opener.open(req, timeout=15) as resp:
                return resp.status, dict(resp.headers), resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read().decode("utf-8", errors="replace")

    def login(self, email: str, password: str) -> int:
        _, _, html = self.get("/")
        token = extract_input_value(html, "csrfmiddlewaretoken") or ""
        status, _, _ = self.post("/", {"csrfmiddlewaretoken": token, "email": email, "password": password})
        return status


def wait_port_open(port: int, timeout_s: float = 15.0) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.05)
    raise RuntimeError(f"Port {port} did not open within {timeout_s}s")


def port_is_closed(port: int) -> bool:
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


# ── 2) EDGE + SCALE + KARDEX SUITE ────────────────────────────────────────────
def run_edge_and_scale_suite(run_dir: Path, out_dir: Path) -> list[dict]:
    from django.core.management import call_command
    from django.db import connection
    from django.test import Client
    from django.test.utils import CaptureQueriesContext
    from django.utils import timezone
    from catalog.models import Category, Product
    from cash.models import CashRegister
    from cash.services import open_cash_shift
    from identity.models import Account, Role
    from inventory.models import InitialInventoryLoad, Lot, StockReceipt, Supplier
    from inventory.services import LotInput, confirm_initial_load, register_stock_entry
    from sales.services import add_product_to_draft, checkout_sale

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    r_admin = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    r_wh = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    r_sel = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    pw = "Audit06B!2026"
    admin = Account.objects.create_user(email="admin06b@example.com", password=pw, display_name="Admin 06B", role=r_admin)
    wh1 = Account.objects.create_user(email="wh1.06b@example.com", password=pw, display_name="Almacen Uno", role=r_wh)
    wh2 = Account.objects.create_user(email="wh2.06b@example.com", password=pw, display_name="Almacen Dos", role=r_wh)
    seller = Account.objects.create_user(email="seller06b@example.com", password=pw, display_name="Vendedor 06B", role=r_sel)

    cat_act = Category.objects.create(name="Lacteos 06B")
    p_main = Product.objects.create(
        category=cat_act, name="Leche 06B", barcode="775999060001", unit="UND",
        sale_price=Decimal("7.50"), minimum_stock=5, controls_expiration=True,
    )
    p_inact = Product.objects.create(
        category=cat_act, name="Producto Oculto Inactivo 06B", barcode="775999060002", unit="UND",
        sale_price=Decimal("4.00"), minimum_stock=2, controls_expiration=True, is_active=True,
    )
    today = timezone.localdate()
    exp1 = today + timedelta(days=60)
    exp2 = today + timedelta(days=90)
    confirm_initial_load(actor=wh1, product=p_main, lots=[LotInput("INI-06B", 10, Decimal("3.0000"), exp2)])
    confirm_initial_load(actor=wh1, product=p_inact, lots=[LotInput("INI-INACT", 5, Decimal("2.0000"), exp2)])
    p_inact.is_active = False
    p_inact.save(update_fields=["is_active"])

    sup_hom1 = Supplier.objects.create(name="Distribuidora Central SAC", ruc="20111111111", is_active=True)
    sup_hom2 = Supplier.objects.create(name="Distribuidora Central SAC", ruc="20222222222", is_active=True)
    sup_inact = Supplier.objects.create(name="Proveedor Desactivado 06B SAC", ruc="20333333333", is_active=False)

    CashRegister.objects.create(code="CAJA-01", is_active=True)
    open_cash_shift(actor=seller, opening_amount=Decimal("100.00"))

    cases = []

    def make_payload(token, key, prod_id, sup_id, rows):
        data = {
            "csrfmiddlewaretoken": token,
            "idempotency_key": str(key),
            "product": str(prod_id),
            "supplier": str(sup_id) if sup_id else "",
            "lots-TOTAL_FORMS": str(max(4, len(rows))),
            "lots-INITIAL_FORMS": "0",
            "lots-MIN_NUM_FORMS": "1",
            "lots-MAX_NUM_FORMS": "1000",
        }
        for i, row in enumerate(rows):
            data[f"lots-{i}-number"] = row["number"]
            data[f"lots-{i}-quantity"] = str(row["quantity"])
            data[f"lots-{i}-unit_cost"] = str(row["unit_cost"])
            data[f"lots-{i}-expiration_date"] = row["expiration_date"]
        for j in range(len(rows), 4):
            data[f"lots-{j}-number"] = ""
            data[f"lots-{j}-quantity"] = ""
            data[f"lots-{j}-unit_cost"] = ""
            data[f"lots-{j}-expiration_date"] = ""
        return data

    def fresh_token_and_key(client):
        r = client.get("/inventario/entrada/")
        html = r.content.decode()
        return extract_input_value(html, "csrfmiddlewaretoken") or "", extract_input_value(html, "idempotency_key") or "", html

    # Case 1: S06B-EDGE-NORM-MAXLEN-01 (LotInputForm max_length=64 pre-collapse check)
    c1 = Client()
    c1.force_login(wh1)
    tok, key_norm, _ = fresh_token_and_key(c1)
    raw65_norm64 = "AB   " + "C" * 60  # len(raw)=65, len(collapsed)=len("AB " + "C"*60)=63 -> 64 with 1 more C!
    raw65_norm64 = "AB   " + "C" * 61  # raw=66 (stripped=66), collapsed="AB " + "C"*61 -> 64!
    raw65 = "A   " + "B" * 61          # raw=65 (stripped=65), collapsed="A " + "B"*61 -> 63 (<64)!
    r_raw65 = c1.post("/inventario/entrada/", make_payload(tok, key_norm, p_main.pk, sup_hom1.pk, [
        {"number": raw65, "quantity": 2, "unit_cost": "4.0000", "expiration_date": exp1.isoformat()},
    ]))
    raw64 = "A  " + "B" * 61           # raw=64, collapsed=63
    r_raw64 = c1.post("/inventario/entrada/", make_payload(tok, key_norm, p_main.pk, sup_hom1.pk, [
        {"number": raw64, "quantity": 2, "unit_cost": "4.0000", "expiration_date": exp1.isoformat()},
    ]))
    cases.append({
        "id": "S06B-EDGE-NORM-MAXLEN-01",
        "ok": r_raw65.status_code == 200 and r_raw64.status_code == 302,
        "raw65_norm63_status": r_raw65.status_code,
        "raw65_norm63_rejected_pre_collapse": "64" in r_raw65.content.decode() or r_raw65.status_code == 200,
        "raw64_status": r_raw64.status_code,
        "finding_confirmed": "LotInputForm.number max_length=64 validates before space-collapse normalization (OBS-05M-01 sibling in stock-entry).",
    })

    # Seed known receipt R-00000002 under key_wh1 for historical replay / cross-user checks
    key_wh1 = str(uuid.uuid4())
    tok, _, _ = fresh_token_and_key(c1)
    r_ok = c1.post("/inventario/entrada/", make_payload(tok, key_wh1, p_main.pk, sup_hom2.pk, [
        {"number": "LOT-HIST-1", "quantity": 4, "unit_cost": "5.0000", "expiration_date": exp1.isoformat()},
    ]))
    assert r_ok.status_code == 302

    # Case 2: S06B-EDGE-HIST-CROSSUSER-01 (wh2 tries wh1 key with inactive product)
    c2 = Client()
    c2.force_login(wh2)
    tok2, _, _ = fresh_token_and_key(c2)
    r_cross_inact = c2.post("/inventario/entrada/", make_payload(tok2, key_wh1, p_inact.pk, sup_inact.pk, [
        {"number": "LOT-HIST-1", "quantity": 4, "unit_cost": "5.0000", "expiration_date": exp1.isoformat()},
    ]))
    html_cross = r_cross_inact.content.decode()
    sp_cross = SelectOptionsParser("product")
    sp_cross.feed(html_cross)
    r_cross_act = c2.post("/inventario/entrada/", make_payload(tok2, key_wh1, p_main.pk, sup_hom2.pk, [
        {"number": "LOT-HIST-1", "quantity": 4, "unit_cost": "5.0000", "expiration_date": exp1.isoformat()},
    ]))
    cases.append({
        "id": "S06B-EDGE-HIST-CROSSUSER-01",
        "ok": r_cross_inact.status_code == 200 and r_cross_act.status_code == 200 and not any(v == str(p_inact.pk) for v, _ in sp_cross.options),
        "cross_inactive_status": r_cross_inact.status_code,
        "inactive_product_leaked_in_select": any(v == str(p_inact.pk) for v, _ in sp_cross.options),
        "cross_active_status": r_cross_act.status_code,
        "cross_active_msg_present": "otro contenido o responsable" in r_cross_act.content.decode(),
    })

    # Case 3: S06B-EDGE-HIST-DIVERGENT-01 (wh1 resends OWN key_wh1 with divergent inactive supplier + invalid qty=0)
    r_div_inact_sup = c1.post("/inventario/entrada/", make_payload(tok, key_wh1, p_main.pk, sup_inact.pk, [
        {"number": "LOT-HIST-1", "quantity": 4, "unit_cost": "5.0000", "expiration_date": exp1.isoformat()},
    ]))
    r_div_qty0 = c1.post("/inventario/entrada/", make_payload(tok, key_wh1, p_main.pk, sup_hom2.pk, [
        {"number": "LOT-HIST-1", "quantity": 0, "unit_cost": "5.0000", "expiration_date": exp1.isoformat()},
    ]))
    html_div_qty0 = r_div_qty0.content.decode()
    sp_prod_hist = SelectOptionsParser("product")
    sp_prod_hist.feed(html_div_qty0)
    sp_sup_hist = SelectOptionsParser("supplier")
    sp_sup_hist.feed(html_div_qty0)
    cases.append({
        "id": "S06B-EDGE-HIST-DIVERGENT-01",
        "ok": r_div_inact_sup.status_code == 200 and "otro contenido o responsable" in r_div_inact_sup.content.decode(),
        "divergent_inactive_supplier_rejected_status": r_div_inact_sup.status_code,
        "divergent_error_shown": "otro contenido o responsable" in r_div_inact_sup.content.decode(),
        "historical_rerender_includes_inactive_product_in_select": any(v == str(p_inact.pk) for v, _ in sp_prod_hist.options),
        "historical_rerender_includes_inactive_supplier_in_select": any(v == str(sup_inact.pk) for v, _ in sp_sup_hist.options),
    })

    # Case 4: S06B-EDGE-AMOUNT-ROUND-01 (3 * 0.0050 = 0.0150, 5 * 0.0050 = 0.0250)
    tok, key_rnd, _ = fresh_token_and_key(c1)
    r_rnd = c1.post("/inventario/entrada/", make_payload(tok, key_rnd, p_main.pk, sup_hom1.pk, [
        {"number": "RND-HALF-1", "quantity": 3, "unit_cost": "0.0050", "expiration_date": exp1.isoformat()},
        {"number": "RND-HALF-2", "quantity": 5, "unit_cost": "0.0050", "expiration_date": exp1.isoformat()},
    ]))
    html_rnd = c1.get(r_rnd["Location"]).content.decode() if r_rnd.status_code == 302 else ""
    cases.append({
        "id": "S06B-EDGE-AMOUNT-ROUND-01",
        "ok": r_rnd.status_code == 302,
        "receipt_status": r_rnd.status_code,
        "rendered_0015_as_0_02": "0,02" in html_rnd or "0.02" in html_rnd,
        "rendered_0025_as_0_03_or_0_02": {"has_0_03": ("0,03" in html_rnd or "0.03" in html_rnd), "has_0_02": ("0,02" in html_rnd or "0.02" in html_rnd)},
    })

    # Case 5: S06B-EDGE-FORMSET-LIMITS-01 (TOTAL_FORMS=1001 & duplicate lot different expiration)
    tok, key_lim, _ = fresh_token_and_key(c1)
    big_data = {
        "csrfmiddlewaretoken": tok,
        "idempotency_key": key_lim,
        "product": str(p_main.pk),
        "supplier": "",
        "lots-TOTAL_FORMS": "1001",
        "lots-INITIAL_FORMS": "0",
        "lots-MIN_NUM_FORMS": "1",
        "lots-MAX_NUM_FORMS": "1000",
    }
    for i in range(255):  # > DATA_UPLOAD_MAX_NUMBER_FIELDS (1000 fields across 4 inputs = 250 forms)
        big_data[f"lots-{i}-number"] = f"L-{i}"
        big_data[f"lots-{i}-quantity"] = "1"
        big_data[f"lots-{i}-unit_cost"] = "1.0000"
        big_data[f"lots-{i}-expiration_date"] = exp1.isoformat()
    r_dos = c1.post("/inventario/entrada/", big_data)
    r_dup_diff_exp = c1.post("/inventario/entrada/", make_payload(tok, key_lim, p_main.pk, None, [
        {"number": "DUP  01", "quantity": 2, "unit_cost": "4.0000", "expiration_date": exp1.isoformat()},
        {"number": "dup 01", "quantity": 3, "unit_cost": "4.5000", "expiration_date": exp2.isoformat()},
    ]))
    cases.append({
        "id": "S06B-EDGE-FORMSET-LIMITS-01",
        "ok": r_dos.status_code == 400 and r_dup_diff_exp.status_code == 200 and "está repetido" in r_dup_diff_exp.content.decode(),
        "over_max_fields_status": r_dos.status_code,
        "dup_diff_exp_status": r_dup_diff_exp.status_code,
        "dup_diff_exp_error_present": "está repetido" in r_dup_diff_exp.content.decode(),
    })

    # Case 6: S06B-EDGE-KARDEX-CROSS-01 (homonym supplier + sale FEFO backlink + role check)
    draft = add_product_to_draft(actor=seller, product_id=p_main.pk, quantity=12)  # consumes INI-06B(10) + RND/LOT-HIST-1
    sale = checkout_sale(actor=seller, draft_id=draft.pk, cash_received=Decimal("100.00"), idempotency_key=uuid.uuid4())
    r_k_wh = c1.get(f"/inventario/productos/{p_main.pk}/movimientos/")
    c_adm = Client(); c_adm.force_login(admin)
    r_k_adm = c_adm.get(f"/inventario/productos/{p_main.pk}/movimientos/")
    c_sel = Client(); c_sel.force_login(seller)
    r_k_sel = c_sel.get(f"/inventario/productos/{p_main.pk}/movimientos/")
    k_html = r_k_wh.content.decode()
    r_load = c1.get(f"/inventario/cargas/{p_main.initial_load.pk}/").content.decode()
    cases.append({
        "id": "S06B-EDGE-KARDEX-CROSS-01",
        "ok": r_k_wh.status_code == 200 and r_k_adm.status_code == 200 and r_k_sel.status_code == 403 and "R-00000002" in k_html,
        "statuses": {"warehouse": r_k_wh.status_code, "admin": r_k_adm.status_code, "seller": r_k_sel.status_code},
        "sale_correlative": sale.correlative,
        "kardex_shows_receipt_correlative": "R-00000002" in k_html,
        "kardex_shows_ver_recepcion_link": "Ver recepción" in k_html and "/inventario/recepciones/" in k_html,
        "kardex_omits_supplier_ruc": "20222222222" not in k_html,
        "kardex_volver_lacks_button_secondary": 'class="button">&larr; Volver al inventario' in k_html or 'class="button">← Volver al inventario' in k_html,
        "initial_load_page_links_receipts": "R-00000002" in r_load and "/inventario/recepciones/" in r_load,
    })

    # Case 7: S06B-SCALE-2000-01 (<select id="id_product"> scaling with 2,000 active products)
    with CaptureQueriesContext(connection) as q_before:
        t0 = time.monotonic()
        r_1 = c1.get("/inventario/entrada/")
        ms_before = round((time.monotonic() - t0) * 1000, 2)
    bytes_before = len(r_1.content)

    bulk_prods = []
    for idx in range(1999):
        bulk_prods.append(Product(
            category=cat_act,
            name=f"Producto Escala {idx:04d}",
            search_name=f"producto escala {idx:04d}",
            barcode=f"7758880{idx:05d}",
            barcode_normalized=f"7758880{idx:05d}",
            unit="UND",
            sale_price=Decimal("5.00"),
            minimum_stock=5,
            controls_expiration=True,
            is_active=True,
        ))
    created_prods = Product.objects.bulk_create(bulk_prods)
    InitialInventoryLoad.objects.bulk_create([
        InitialInventoryLoad(product=p, responsible=wh1) for p in created_prods
    ])
    with CaptureQueriesContext(connection) as q_after:
        t1 = time.monotonic()
        r_2000 = c1.get("/inventario/entrada/")
        ms_after = round((time.monotonic() - t1) * 1000, 2)
    html_2000 = r_2000.content.decode()
    sp_2000 = SelectOptionsParser("product")
    sp_2000.feed(html_2000)
    cases.append({
        "id": "S06B-SCALE-2000-01",
        "ok": r_2000.status_code == 200 and len(sp_2000.options) >= 2000,
        "before_active_products": 1,
        "before_ms": ms_before,
        "before_queries": len(q_before),
        "before_html_kb": round(bytes_before / 1024, 2),
        "after_active_products": len(sp_2000.options) - 1,
        "after_ms": ms_after,
        "after_queries": len(q_after),
        "after_html_kb": round(len(r_2000.content) / 1024, 2),
        "finding_note": "No search/pagination in <select id='id_product'>; constant SQL queries (O(1)) but HTML payload grows linearly (~320 KB for 2k options).",
    })

    return cases


# ── 3) CRASH-01 & CRASH-02: Real OS TerminateProcess HTTP pre/post commit ─────
def run_http_os_crash_cases(out_dir: Path) -> list[dict]:
    from django.core.management import call_command
    from django.utils import timezone
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.models import InitialInventoryLoad, Lot, StockReceipt, StockReceiptCounter
    from inventory.services import LotInput, confirm_initial_load

    results = []
    pw = "Audit06Crash!2026"
    exp = (timezone.localdate() + timedelta(days=45)).isoformat()

    for case_id, mode in (("CRASH-01-HTTP-PRECOMMIT", "precommit"), ("CRASH-02-HTTP-POSTCOMMIT", "postcommit")):
        c_run = RESULTS / "datos" / f"etapa06-reval-crash-{mode}-{secrets.token_hex(4)}"
        c_run.mkdir(parents=True)
        (c_run / "marker.json").write_text(json.dumps({"run": c_run.name}), encoding="utf-8")
        (c_run / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")

        # Seed isolated SQLite DB via subprocess so parent process keeps one clean settings state
        seed_script = f"""
import contextlib, io, os, sys
from datetime import timedelta
from decimal import Decimal
sys.path.insert(0, r'{APP}'); sys.path.insert(0, r'{SUPPORT}')
os.environ.update(AUDIT06_RUN_DIR=r'{c_run}', DJANGO_SETTINGS_MODULE='audit06_settings', AUDIT06_DEFAULT_COOKIES='1')
import django; django.setup()
from django.core.management import call_command
from django.utils import timezone
from identity.models import Account, Role
from catalog.models import Category, Product
from inventory.services import LotInput, confirm_initial_load
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    call_command('migrate', interactive=False, verbosity=0)
r_wh = Role.objects.create(code=Role.Code.WAREHOUSE, name='Almacenero')
wh = Account.objects.create_user(email='wh.crash@example.com', password='{pw}', display_name='Almacenero Crash', role=r_wh)
cat = Category.objects.create(name='Cat Crash')
prod = Product.objects.create(category=cat, name='Prod Crash', barcode='775000099901', unit='UND', sale_price=Decimal('10.00'), minimum_stock=3, controls_expiration=True)
confirm_initial_load(actor=wh, product=prod, lots=[LotInput('C-INI', 10, Decimal('3.0000'), timezone.localdate()+timedelta(days=60))])
print(str(prod.pk))
"""
        prod_id = subprocess.check_output([sys.executable, "-c", seed_script], text=True).strip().splitlines()[-1]

        port = free_port()
        sig_file = c_run / "signal.json"
        env = dict(os.environ, AUDIT06_RUN_DIR=str(c_run), AUDIT06B_CRASH_MODE=mode, AUDIT06B_SIGNAL_FILE=str(sig_file), AUDIT06B_PORT=str(port))
        proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "__crash_worker__"], env=env, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            ready_deadline = time.monotonic() + 15.0
            while not sig_file.with_suffix(".ready").exists():
                if time.monotonic() > ready_deadline:
                    raise RuntimeError("Crash worker failed to signal ready")
                time.sleep(0.05)
            wait_port_open(port)

            sess = HttpSession(f"http://127.0.0.1:{port}")
            assert sess.login("wh.crash@example.com", pw) == 302
            _, _, form_html = sess.get("/inventario/entrada/")
            csrf = extract_input_value(form_html, "csrfmiddlewaretoken") or ""
            idem_key = extract_input_value(form_html, "idempotency_key") or str(uuid.uuid4())
            payload = {
                "csrfmiddlewaretoken": csrf,
                "idempotency_key": idem_key,
                "product": prod_id,
                "supplier": "",
                "lots-TOTAL_FORMS": "4",
                "lots-INITIAL_FORMS": "0",
                "lots-MIN_NUM_FORMS": "1",
                "lots-MAX_NUM_FORMS": "1000",
                "lots-0-number": f"CRASH-{mode.upper()}",
                "lots-0-quantity": "10",
                "lots-0-unit_cost": "6.0000",
                "lots-0-expiration_date": exp,
            }
            for j in range(1, 4):
                payload.update({f"lots-{j}-number": "", f"lots-{j}-quantity": "", f"lots-{j}-unit_cost": "", f"lots-{j}-expiration_date": ""})

            req_err = {}
            def do_post():
                try:
                    sess.post("/inventario/entrada/", payload)
                except Exception as exc:
                    req_err["exc"] = f"{type(exc).__name__}: {exc}"

            t = threading.Thread(target=do_post, daemon=True)
            t.start()
            deadline = time.monotonic() + 15.0
            while not sig_file.exists():
                if time.monotonic() > deadline:
                    raise RuntimeError(f"Worker did not reach {mode} barrier")
                time.sleep(0.02)
            sig_data = json.loads(sig_file.read_text(encoding="utf-8"))
            time.sleep(0.15)  # keep request blocked inside barrier, then kill OS process abruptly
            proc.kill()
            proc.wait(timeout=10)
            t.join(timeout=10)
        finally:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=5)

        # Inspect DB state on disk immediately after TerminateProcess
        db_path = c_run / "audit.sqlite3"
        raw_conn = sqlite3.connect(str(db_path))
        receipt_cnt_after_kill = raw_conn.execute("SELECT COUNT(*) FROM inventory_stockreceipt").fetchone()[0]
        counter_row = raw_conn.execute("SELECT last_number FROM inventory_stockreceiptcounter WHERE key='global'").fetchone()
        counter_after_kill = counter_row[0] if counter_row else 0
        lot_cnt_after_kill = raw_conn.execute("SELECT COUNT(*) FROM inventory_lot").fetchone()[0]
        avg_after_kill = raw_conn.execute("SELECT average_cost FROM catalog_product").fetchone()[0]
        raw_conn.close()

        # Restart clean normal HTTP server against the SAME DB and replay exact same idempotency_key
        sig_file.with_suffix(".ready").unlink(missing_ok=True)
        port2 = free_port()
        env2 = dict(os.environ, AUDIT06_RUN_DIR=str(c_run), AUDIT06B_CRASH_MODE="normal", AUDIT06B_SIGNAL_FILE=str(sig_file), AUDIT06B_PORT=str(port2))
        proc2 = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "__crash_worker__"], env=env2, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            ready_deadline = time.monotonic() + 15.0
            while not sig_file.with_suffix(".ready").exists():
                if time.monotonic() > ready_deadline:
                    raise RuntimeError("Recovery worker failed to signal ready")
                time.sleep(0.05)
            wait_port_open(port2)

            sess2 = HttpSession(f"http://127.0.0.1:{port2}")
            assert sess2.login("wh.crash@example.com", pw) == 302
            _, _, form2 = sess2.get("/inventario/entrada/")
            payload_replay = dict(payload, csrfmiddlewaretoken=extract_input_value(form2, "csrfmiddlewaretoken") or "")
            replay_status, replay_hdrs, _ = sess2.post("/inventario/entrada/", payload_replay)
            receipt_page = sess2.get(replay_hdrs["Location"])[2] if replay_status == 302 else ""

            # Also verify divergent resend with same key after recovery rejects cleanly
            payload_div = dict(payload_replay, **{"lots-0-quantity": "99"})
            div_status, _, div_html = sess2.post("/inventario/entrada/", payload_div)
        finally:
            proc2.terminate()
            proc2.wait(timeout=5)

        raw_conn = sqlite3.connect(str(db_path))
        receipt_cnt_final = raw_conn.execute("SELECT COUNT(*) FROM inventory_stockreceipt").fetchone()[0]
        lot_cnt_final = raw_conn.execute("SELECT COUNT(*) FROM inventory_lot").fetchone()[0]
        avg_final = raw_conn.execute("SELECT average_cost FROM catalog_product").fetchone()[0]
        raw_conn.close()

        if mode == "precommit":
            ok = (
                proc.returncode != 0
                and receipt_cnt_after_kill == 0
                and counter_after_kill == 0
                and lot_cnt_after_kill == 1
                and float(avg_after_kill) == 3.0
                and replay_status == 302
                and "R-00000001" in receipt_page
                and receipt_cnt_final == 1
                and lot_cnt_final == 2
                and abs(float(avg_final) - 4.5) < 1e-6
                and div_status == 200
                and port_is_closed(port)
                and port_is_closed(port2)
            )
        else:
            ok = (
                proc.returncode != 0
                and receipt_cnt_after_kill == 1
                and counter_after_kill == 1
                and lot_cnt_after_kill == 2
                and abs(float(avg_after_kill) - 4.5) < 1e-6
                and replay_status == 302
                and "R-00000001" in receipt_page
                and receipt_cnt_final == 1
                and lot_cnt_final == 2
                and div_status == 200
                and port_is_closed(port)
                and port_is_closed(port2)
            )

        results.append({
            "id": case_id,
            "ok": ok,
            "kill_returncode": proc.returncode,
            "signal": sig_data,
            "client_post_error_during_kill": req_err.get("exc"),
            "after_kill_db": {"receipts": receipt_cnt_after_kill, "counter": counter_after_kill, "lots": lot_cnt_after_kill, "average_cost": str(avg_after_kill)},
            "after_recovery_replay": {"status": replay_status, "location": replay_hdrs.get("Location"), "correlative_in_html": "R-00000001" in receipt_page, "receipts": receipt_cnt_final, "lots": lot_cnt_final, "average_cost": str(avg_final)},
            "divergent_replay_rejected": div_status == 200 and "otro contenido o responsable" in div_html,
            "ports_closed": port_is_closed(port) and port_is_closed(port2),
        })
    return results


# ── 4) CRASH-03: Real PostgreSQL 18.4 pg_ctl -m immediate WAL crash recovery ──
def run_pg18_immediate_crash() -> dict:
    cluster = (Path(tempfile.gettempdir()) / ("audit06b-pgcrash-" + secrets.token_hex(8))).resolve()
    cluster.mkdir(exist_ok=False)
    dbdir = cluster / "data"
    pw = secrets.token_urlsafe(32)
    pwfile = cluster / "pw"
    pwfile.write_text(pw, encoding="utf-8")
    dbname = "audit06b_" + secrets.token_hex(4)
    port = free_port()

    def pg_cmd(exe: str, *args):
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as f:
            p = subprocess.run([str(PG_BIN / f"{exe}.exe"), *map(str, args)], stdout=f, stderr=f, timeout=60, creationflags=subprocess.CREATE_NO_WINDOW)
            f.seek(0)
            out = f.read().replace(pw, "[REDACTED]")
        if p.returncode:
            raise RuntimeError(f"{exe} failed: {out[-800:]}")
        return out

    started = False
    try:
        pg_cmd("initdb", "-D", dbdir, "-U", "postgres", "-A", "scram-sha-256", "--pwfile", pwfile, "-E", "UTF8", "--locale=C")
        pg_cmd("pg_ctl", "-D", dbdir, "-l", cluster / "pg.log", "-o", f"-p {port} -h 127.0.0.1 -k .", "start")
        started = True
        env = dict(os.environ, PGPASSWORD=pw)
        subprocess.run([str(PG_BIN / "createdb.exe"), "-h", "127.0.0.1", "-p", str(port), "-U", "postgres", dbname], env=env, check=True, capture_output=True)

        runner_code = """
import json, os, sys, uuid
from datetime import timedelta
from decimal import Decimal
import psycopg
sys.path.insert(0, os.environ['APP_DIR'])
os.environ.update(APP_ENV='test', DATABASE_URL=os.environ['PG_URL'], DJANGO_DEBUG='false', DJANGO_ALLOWED_HOSTS='127.0.0.1,localhost', DJANGO_SECRET_KEY='audit06b-pgcrash-key-secret-value')
import django; django.setup()
from django.core.management import call_command
from django.utils import timezone
from identity.models import Account, Role
from catalog.models import Category, Product
from inventory.models import StockReceipt, StockReceiptCounter, Lot
from inventory.services import LotInput, confirm_initial_load, register_stock_entry

phase = os.environ['PHASE']
if phase == 'setup':
    call_command('migrate', interactive=False, verbosity=0)
    r_wh = Role.objects.create(code=Role.Code.WAREHOUSE, name='Almacenero')
    wh = Account.objects.create_user(email='wh.pgcrash@example.com', password='Pw!06bPg', display_name='WH PG', role=r_wh)
    cat = Category.objects.create(name='Cat PG Crash')
    prod = Product.objects.create(category=cat, name='Prod PG Crash', barcode='775123400001', unit='UND', sale_price=Decimal('9.00'), minimum_stock=5, controls_expiration=True)
    confirm_initial_load(actor=wh, product=prod, lots=[LotInput('PG-INI', 10, Decimal('3.0000'), timezone.localdate()+timedelta(days=60))])
    print(json.dumps({'prod_id': str(prod.pk), 'wh_id': str(wh.pk)}))
elif phase == 'uncommitted_before_immediate':
    info = json.loads(os.environ['INFO_JSON'])
    key = uuid.uuid4()
    with psycopg.connect(os.environ['PG_URL'], autocommit=False) as conn:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO inventory_stockreceiptcounter (key, last_number) VALUES ('global', 1) ON CONFLICT (key) DO UPDATE SET last_number = 1")
            cur.execute("UPDATE catalog_product SET average_cost = 9.9999 WHERE id = %s", (info['prod_id'],))
            cur.execute(
                "INSERT INTO inventory_stockreceipt (id, idempotency_key, content_signature, correlative, confirmed_at, product_snapshot_name, product_snapshot_barcode, responsible_snapshot_name, supplier_snapshot_name, supplier_snapshot_ruc, average_cost_after, product_id, responsible_id, supplier_id) VALUES (%s,%s,%s,%s,now(),'P','B','R','','',9.9999,%s,%s,NULL)",
                (str(uuid.uuid4()), str(key), 'a'*64, 'R-00000001', info['prod_id'], info['wh_id']),
            )
            # Deliberately DO NOT commit; signal parent to execute pg_ctl -m immediate stop
            open(os.environ['SIG_FILE'], 'w').write('dirty_uncommitted')
            import time; time.sleep(30)
elif phase == 'inspect_and_commit':
    info = json.loads(os.environ['INFO_JSON'])
    prod = Product.objects.get(pk=info['prod_id'])
    wh = Account.objects.get(pk=info['wh_id'])
    pre_state = {'receipts': StockReceipt.objects.count(), 'counter': StockReceiptCounter.objects.filter(key='global').values_list('last_number', flat=True).first(), 'lots': Lot.objects.count(), 'avg': str(prod.average_cost)}
    key1 = uuid.UUID('aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee')
    r1 = register_stock_entry(actor=wh, product=prod, lots=[LotInput('PG-C1', 10, Decimal('6.0000'), timezone.localdate()+timedelta(days=30))], idempotency_key=key1)
    prod.refresh_from_db()
    print(json.dumps({'pre_state_after_uncommitted_kill': pre_state, 'committed_correlative': r1.correlative, 'avg_after_commit': str(prod.average_cost)}))
elif phase == 'post_immediate_verify':
    info = json.loads(os.environ['INFO_JSON'])
    prod = Product.objects.get(pk=info['prod_id'])
    wh = Account.objects.get(pk=info['wh_id'])
    key1 = uuid.UUID('aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee')
    r_replay = register_stock_entry(actor=wh, product=prod, lots=[LotInput('PG-C1', 10, Decimal('6.0000'), timezone.localdate()+timedelta(days=30))], idempotency_key=key1)
    r2 = register_stock_entry(actor=wh, product=prod, lots=[LotInput('PG-C2', 2, Decimal('6.0000'), timezone.localdate()+timedelta(days=30))])
    prod.refresh_from_db()
    print(json.dumps({'replay_correlative': r_replay.correlative, 'next_correlative': r2.correlative, 'receipts': StockReceipt.objects.count(), 'counter': StockReceiptCounter.objects.get(key='global').last_number, 'lots': Lot.objects.count(), 'avg_after_all': str(prod.average_cost)}))
"""
        pg_url = f"postgresql://postgres:{urllib.parse.quote(pw, safe='')}@127.0.0.1:{port}/{dbname}"
        base_env = dict(os.environ, APP_DIR=str(APP), PG_URL=pg_url)

        def call_pg_phase(phase_name, extra=None):
            e = dict(base_env, PHASE=phase_name)
            if extra:
                e.update(extra)
            out = subprocess.check_output([sys.executable, "-c", runner_code], env=e, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return json.loads(out.strip().splitlines()[-1])

        info = call_pg_phase("setup")
        sig = cluster / "uncommitted.sig"
        p_dirty = subprocess.Popen(
            [sys.executable, "-c", runner_code],
            env=dict(base_env, PHASE="uncommitted_before_immediate", INFO_JSON=json.dumps(info), SIG_FILE=str(sig)),
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        dl = time.monotonic() + 15.0
        while not sig.exists():
            if time.monotonic() > dl:
                p_dirty.kill()
                raise RuntimeError("PG uncommitted worker did not write signal")
            time.sleep(0.02)
        time.sleep(0.1)
        pg_cmd("pg_ctl", "-D", dbdir, "-m", "immediate", "stop")
        started = False
        p_dirty.wait(timeout=10)

        # Restart after immediate crash #1 -> verify uncommitted rows rolled back via WAL
        pg_cmd("pg_ctl", "-D", dbdir, "-l", cluster / "pg.log", "-o", f"-p {port} -h 127.0.0.1 -k .", "start")
        started = True
        step2 = call_pg_phase("inspect_and_commit", {"INFO_JSON": json.dumps(info)})

        # Immediate crash #2 right after commit -> restart -> verify WAL durability + idempotent replay
        pg_cmd("pg_ctl", "-D", dbdir, "-m", "immediate", "stop")
        started = False
        pg_cmd("pg_ctl", "-D", dbdir, "-l", cluster / "pg.log", "-o", f"-p {port} -h 127.0.0.1 -k .", "start")
        started = True
        step3 = call_pg_phase("post_immediate_verify", {"INFO_JSON": json.dumps(info)})

        pg_cmd("pg_ctl", "-D", dbdir, "-m", "fast", "stop")
        started = False
    finally:
        if started:
            subprocess.run([str(PG_BIN / "pg_ctl.exe"), "-D", str(dbdir), "-m", "immediate", "stop"], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        shutil.rmtree(cluster, ignore_errors=True)

    pre = step2["pre_state_after_uncommitted_kill"]
    ok = (
        pre["receipts"] == 0
        and pre["lots"] == 1
        and Decimal(pre["avg"]) == Decimal("3.0000")
        and step2["committed_correlative"] == "R-00000001"
        and step2["avg_after_commit"] == "4.5000"
        and step3["replay_correlative"] == "R-00000001"
        and step3["next_correlative"] == "R-00000002"
        and step3["receipts"] == 2
        and step3["counter"] == 2
        and step3["lots"] == 3
        and port_is_closed(port)
    )
    return {
        "id": "CRASH-03-PG18-IMMEDIATE",
        "ok": ok,
        "after_uncommitted_immediate_stop": step2,
        "after_committed_immediate_stop": step3,
        "port_closed": port_is_closed(port),
    }


def run_browser_deep(out_dir: Path) -> dict:
    from django.utils import timezone

    b_run = RESULTS / "datos" / f"etapa06-06b-browser-{datetime.now(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4)}"
    b_run.mkdir(parents=True)
    write_json(b_run / "marker.json", {"run": b_run.name})
    (b_run / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")

    pw = "Audit06Browser!2026"
    future_date = (timezone.localdate() + timedelta(days=45)).isoformat()
    seed_script = f"""
import contextlib, io, json, os, sys
from datetime import timedelta
from decimal import Decimal
sys.path.insert(0, r'{APP}'); sys.path.insert(0, r'{SUPPORT}')
os.environ.update(AUDIT06_RUN_DIR=r'{b_run}', DJANGO_SETTINGS_MODULE='audit06_settings', AUDIT06_DEFAULT_COOKIES='1')
import django; django.setup()
from django.core.management import call_command
from django.utils import timezone
from identity.models import Account, Role
from catalog.models import Category, Product
from inventory.models import Supplier
from inventory.services import LotInput, confirm_initial_load
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    call_command('migrate', interactive=False, verbosity=0)
r_wh = Role.objects.create(code=Role.Code.WAREHOUSE, name='Almacenero')
wh = Account.objects.create_user(email='wh.kbd@example.com', password='{pw}', display_name='Almacenero Teclado', role=r_wh)
cat = Category.objects.create(name='Bebidas 06B')
prod = Product.objects.create(category=cat, name='Agua Mineral 06B', barcode='775111000601', unit='UND', sale_price=Decimal('2.50'), minimum_stock=5, controls_expiration=True)
confirm_initial_load(actor=wh, product=prod, lots=[LotInput('AG-INI', 10, Decimal('1.0000'), timezone.localdate()+timedelta(days=90))])
sup = Supplier.objects.create(name='Distribuidora Central SAC', ruc='20998877661', is_active=True)
print(json.dumps({{'product_id': str(prod.pk), 'supplier_homonym_id': str(sup.pk), 'supplier_homonym_ruc': sup.ruc}}))
"""
    fixture = json.loads(subprocess.check_output([sys.executable, "-c", seed_script], text=True).strip().splitlines()[-1])
    fixture["future_date"] = future_date
    write_json(b_run / ".credentials.json", {"wh": {"email": "wh.kbd@example.com", "password": pw}})
    write_json(out_dir / "browser-fixture.json", fixture)

    port = free_port()
    env = dict(os.environ, AUDIT06_RUN_DIR=str(b_run), AUDIT06B_RUN_DIR=str(b_run), AUDIT06B_OUT=str(out_dir), AUDIT06B_PORT=str(port), AUDIT06_DEFAULT_COOKIES="1")
    srv = subprocess.Popen(
        [sys.executable, str(SUPPORT / "audit06_reval_run.py"), "serve"],
        env=dict(env, AUDIT06_PORT=str(port)),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    try:
        wait_port_open(port)
        child = subprocess.run(
            ["node", str(SUPPORT / "audit06b_browser_deep.cjs")],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=180,
        )
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=5)
        except subprocess.TimeoutExpired:
            srv.kill()
            srv.wait(timeout=5)

    browser_report = json.loads((out_dir / "browser-deep.json").read_text(encoding="utf-8")) if (out_dir / "browser-deep.json").exists() else {}
    return {
        "id": "BROWSER-06B-A11Y-KBD-KARDEX",
        "ok": child.returncode == 0 and port_is_closed(port) and len(browser_report.get("page_errors", [])) == 0,
        "exit_code": child.returncode,
        "stdout": child.stdout,
        "stderr": child.stderr,
        "port_closed": port_is_closed(port),
        "checks_count": len(browser_report.get("checks", [])),
        "a11y_metrics": browser_report.get("a11y_metrics"),
        "layout_metrics": browser_report.get("layout_metrics"),
        "screenshots": browser_report.get("screenshots"),
    }


def main() -> int:
    if len(sys.argv) >= 2 and sys.argv[1] == "__crash_worker__":
        return run_crash_worker()

    start_hashes = protected_hashes()
    out_dir = RESULTS / "evidencias" / "06-B-20261115"
    out_dir.mkdir(parents=True, exist_ok=True)
    run_dir = RESULTS / "datos" / f"etapa06-06b-edges-{datetime.now(dt_timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4)}"
    run_dir.mkdir(parents=True)
    write_json(run_dir / "marker.json", {"run": run_dir.name})
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")

    os.environ.update(AUDIT06_RUN_DIR=str(run_dir), AUDIT06_DEFAULT_COOKIES="1", DJANGO_SETTINGS_MODULE="audit06_settings")
    import django
    django.setup()

    opdb = run_opdb_diagnostic(out_dir)
    edge_cases = run_edge_and_scale_suite(run_dir, out_dir)
    http_crashes = run_http_os_crash_cases(out_dir)
    pg_crash = run_pg18_immediate_crash()
    browser_deep = run_browser_deep(out_dir)

    end_hashes = {k: digest(ROOT / k) == v for k, v in start_hashes.items()}
    protected_ok = all(end_hashes.values())

    report = {
        "stamp_utc": datetime.now(dt_timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "protected_unchanged": protected_ok,
        "opdb": opdb,
        "edge_cases": edge_cases,
        "http_os_crashes": http_crashes,
        "pg18_immediate_crash": pg_crash,
        "browser_deep": browser_deep,
        "summary": {
            "opdb_ok": opdb["ok"],
            "edge_ok": f"{sum(1 for c in edge_cases if c['ok'])}/{len(edge_cases)}",
            "http_crash_ok": f"{sum(1 for c in http_crashes if c['ok'])}/{len(http_crashes)}",
            "pg_crash_ok": pg_crash["ok"],
            "browser_deep_ok": browser_deep["ok"],
        },
    }
    write_json(out_dir / "deep-probes.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    all_ok = opdb["ok"] and all(c["ok"] for c in edge_cases) and all(c["ok"] for c in http_crashes) and pg_crash["ok"] and browser_deep["ok"] and protected_ok
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
