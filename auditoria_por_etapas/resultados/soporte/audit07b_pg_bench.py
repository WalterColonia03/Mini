"""Stage 07-B real PostgreSQL 18.4 concurrency, Lima-midnight, and PT-SEARCH-01 / PROP-07-IDX-01 benchmark."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import secrets
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
R1 = ROOT / "r1-pmv"
EVID = ROOT / "auditoria_por_etapas" / "resultados" / "evidencias" / "07-B-20261114"
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
sys.path.insert(0, str(R1))


def sha256(p: Path) -> str | None:
    if not p.exists():
        return None
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


EVID.mkdir(parents=True, exist_ok=True)
STAMP = datetime.now(dt_timezone.utc).strftime("%Y%m%dT%H%M%SZ")
TMP = (Path(tempfile.gettempdir()) / f"audit07b-pg-{secrets.token_hex(8)}").resolve()
TMP.mkdir(exist_ok=False)
DBDIR = TMP / "pgdata"
PW = secrets.token_hex(16)
PORT = free_port()

protected = [R1 / "r1_pmv.sqlite3", ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx"]
for dbp in sorted((ROOT / "auditoria_por_etapas" / "resultados" / "datos").rglob("*.sqlite3")):
    protected.append(dbp)
before_hashes = {str(p.relative_to(ROOT)): sha256(p) for p in protected}

report: dict = {
    "stamp": STAMP,
    "engine": "postgresql",
    "port": PORT,
    "cases": {},
    "benchmarks": {},
}

started = False
try:
    pwfile = TMP / "pw.txt"
    pwfile.write_text(PW, encoding="utf-8")

    def pg(tool: str, *args):
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as f:
            res = subprocess.run(
                [str(BIN / f"{tool}.exe"), *map(str, args)],
                stdout=f,
                stderr=f,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            f.seek(0)
            out_txt = f.read().replace(PW, "[REDACTED]")
        if res.returncode != 0:
            raise RuntimeError(f"{tool} failed ({res.returncode}): {out_txt[-1000:]}")

    pg(
        "initdb",
        "-D", str(DBDIR),
        "-U", "audit07b",
        "--pwfile", str(pwfile),
        "--auth-host=scram-sha-256",
        "--auth-local=scram-sha-256",
        "--encoding=UTF8",
        "--locale=C",
    )
    pwfile.unlink()
    pg("pg_ctl", "-D", str(DBDIR), "-l", str(TMP / "pg.log"), "-o", f"-h 127.0.0.1 -p {PORT} -c log_statement=none", "-w", "start")
    started = True
    print("PG_STARTED", PORT, flush=True)

    import psycopg

    with psycopg.connect(host="127.0.0.1", port=PORT, user="audit07b", password=PW, dbname="postgres", autocommit=True) as c:
        report["pg_version"] = c.execute("SELECT version()").fetchone()[0]
        c.execute("CREATE DATABASE audit07b_pg ENCODING 'UTF8'")

    os.environ.update(
        APP_ENV="test",
        DJANGO_DEBUG="false",
        DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
        DJANGO_SETTINGS_MODULE="config.settings",
        DATABASE_URL=f"postgresql://audit07b:{PW}@127.0.0.1:{PORT}/audit07b_pg",
    )
    from config import env as config_env

    _orig_loader = config_env.load_dotenv
    config_env.load_dotenv = lambda path=None: None
    from django.conf import settings
    settings.DATABASES["default"] = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "audit07b_pg",
        "USER": "audit07b",
        "PASSWORD": PW,
        "HOST": "127.0.0.1",
        "PORT": PORT,
        "ATOMIC_REQUESTS": False,
        "CONN_MAX_AGE": 0,
        "OPTIONS": {"options": "-c statement_timeout=20000 -c lock_timeout=12000"},
        "TIME_ZONE": None,
        "AUTOCOMMIT": True,
        "TEST": {"CHARSET": None, "COLLATION": None, "MIGRATE": True, "MIRROR": None, "NAME": None},
    }
    settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
    config_env.load_dotenv = _orig_loader

    import django
    django.setup()
    print("DJANGO_READY", flush=True)
    from django.core.management import call_command
    from django.db import close_old_connections, connection, transaction
    from django.test import Client, override_settings
    from django.test.utils import CaptureQueriesContext, setup_test_environment
    from django.utils import timezone as tz

    setup_test_environment()
    call_command("migrate", verbosity=0)
    assert connection.vendor == "postgresql", connection.vendor
    print("PG_MIGRATED", flush=True)

    from cash.models import CashRegister
    from cash.services import open_cash_shift
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.models import InitialInventoryLoad, InitialLoadLine, Lot, Supplier
    from inventory.services import LotInput, confirm_initial_load
    from sales.services import add_product_to_draft, checkout_sale, sellable_stock_for_product
    import uuid

    CashRegister.objects.get_or_create(code="CAJA-01", defaults={"is_active": True})
    admin_role, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    wh_role, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    seller_role, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})
    pw_u = "PgAudit07b#Pass2026"
    admin = Account.objects.create_user("admin07b@pg.invalid", pw_u, display_name="Admin PG07B", role=admin_role)
    wh = Account.objects.create_user("wh07b@pg.invalid", pw_u, display_name="Wh PG07B", role=wh_role)
    seller = Account.objects.create_user("seller07b@pg.invalid", pw_u, display_name="Seller PG07B", role=seller_role)
    cat = Category.objects.create(name="Abarrotes PG")
    sup = Supplier.objects.create(name="Proveedor PG", ruc="20999888777")

    # ── Case A: Concurrent checkout_sale lock under PG READ COMMITTED ────────
    prod = Product.objects.create(
        name="Leche Concurrencia PG", category=cat, barcode="7759990000015",
        unit="UND", sale_price=Decimal("4.50"), minimum_stock=5, is_active=True, controls_expiration=True,
    )
    t_base = datetime(2026, 11, 12, 16, 0, tzinfo=dt_timezone.utc)
    with patch("django.utils.timezone.now", return_value=t_base):
        confirm_initial_load(
            actor=wh, product=prod, supplier=sup,
            lots=[
                LotInput("PG-EXP", 6, Decimal("2.0000"), date(2026, 11, 13)),
                LotInput("PG-VIG", 10, Decimal("2.0000"), date(2026, 12, 5)),
            ],
        )
    # Move time forward to Nov 14 Lima (PG-EXP expires, PG-VIG still valid -> physical=16, sellable=10)
    t_now = datetime(2026, 11, 14, 16, 0, tzinfo=dt_timezone.utc)
    open_cash_shift(actor=seller, opening_amount=Decimal("20.00"))
    draft = add_product_to_draft(actor=seller, product_id=prod.pk, quantity=6)  # drops sellable from 10 to 4 (<= min 5!)

    lock_acquired = threading.Event()
    release_lock = threading.Event()
    concurrent_reads: dict = {}

    def locker():
        close_old_connections()
        with transaction.atomic():
            Product.objects.select_for_update().get(pk=prod.pk)
            Lot.objects.filter(product=prod).select_for_update().count()
            lock_acquired.set()
            release_lock.wait(timeout=15)
            with patch("django.utils.timezone.now", return_value=t_now):
                sale = checkout_sale(
                    actor=seller,
                    draft_id=draft.pk,
                    cash_received=Decimal("30.00"),
                    idempotency_key=uuid.uuid4(),
                )
            concurrent_reads["sale_correlative"] = sale.correlative
        close_old_connections()

    def reader():
        close_old_connections()
        c_ad = Client()
        c_ad.force_login(admin)
        c_wh = Client()
        c_wh.force_login(wh)
        with patch("django.utils.timezone.now", return_value=t_now):
            t0 = time.perf_counter()
            r_stock = c_wh.get("/inventario/stock/")
            r_exp = c_wh.get("/productos/vencimientos/")
            r_dash = c_ad.get("/inicio/")
            dt_ms = (time.perf_counter() - t0) * 1000
            concurrent_reads["during_lock"] = {
                "stock_status": r_stock.status_code,
                "exp_status": r_exp.status_code,
                "dash_status": r_dash.status_code,
                "elapsed_ms": round(dt_ms, 2),
                "sellable_before_commit": sellable_stock_for_product(Product.objects.get(pk=prod.pk)),
            }
        close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_lock = pool.submit(locker)
        assert lock_acquired.wait(timeout=10)
        f_read = pool.submit(reader)
        f_read.result(timeout=10)
        release_lock.set()
        f_lock.result(timeout=10)

    c_ad = Client()
    c_ad.force_login(admin)
    c_wh = Client()
    c_wh.force_login(wh)
    with patch("django.utils.timezone.now", return_value=t_now):
        prod.refresh_from_db()
        concurrent_reads["after_commit"] = {
            "physical_stock": prod.physical_stock,
            "sellable_stock": prod.sellable_stock,
            "dash_summary": c_ad.get("/inicio/").context["summary"],
        }
    report["cases"]["concurrent_checkout_read_committed"] = {
        "ok": (
            concurrent_reads["during_lock"]["stock_status"] == 200
            and concurrent_reads["during_lock"]["sellable_before_commit"] == 10
            and concurrent_reads["after_commit"]["physical_stock"] == 10
            and concurrent_reads["after_commit"]["sellable_stock"] == 4
            and concurrent_reads["after_commit"]["dash_summary"]["low_stock"] == 1
            and concurrent_reads["after_commit"]["dash_summary"]["expired"] == 1
        ),
        "details": concurrent_reads,
    }
    print("CASE_A_OK:", report["cases"]["concurrent_checkout_read_committed"]["ok"], flush=True)

    # ── Case B: Synthetic volume PT-SEARCH-01 & PROP-07-IDX-01 (2,000 prod / 20,000 lots) ─
    t_bench_ref = date(2026, 11, 14)
    cats = [Category.objects.create(name=f"CatBench {i:02d}") for i in range(10)]
    products_to_create = []
    with transaction.atomic():
        for i in range(2000):
            p = Product(
                name=f"Producto Bench {i:04d}",
                category=cats[i % 10],
                barcode=f"7751000{i:06d}",
                unit="UND",
                sale_price=Decimal("5.00"),
                minimum_stock=5,
                is_active=(i % 20 != 0),
                controls_expiration=True,
            )
            p.search_name = Product.normalize_text(p.name) if hasattr(Product, "normalize_text") else p.name.lower()
            p.barcode_normalized = p.barcode
            p.save()
            products_to_create.append(p)

        loads = [InitialInventoryLoad(product=p, responsible=wh) for p in products_to_create]
        InitialInventoryLoad.objects.bulk_create(loads, batch_size=500)

        lots_bulk = []
        # 2,000 * 10 = 20,000 lots: 35% qty=0, 10% expired, 15% +1..+30d, 40% >+30d
        for idx_p, (p, ld) in enumerate(zip(products_to_create, loads)):
            for j in range(10):
                bucket = (idx_p + j) % 20
                if bucket < 7:
                    avail = 0
                    exp = t_bench_ref + timedelta(days=(bucket * 10) - 5)
                elif bucket < 9:
                    avail = 4
                    exp = t_bench_ref - timedelta(days=(bucket - 6))
                elif bucket < 12:
                    avail = 5
                    exp = t_bench_ref + timedelta(days=((bucket - 8) * 9))
                else:
                    avail = 8
                    exp = t_bench_ref + timedelta(days=40 + bucket * 5)
                lots_bulk.append(
                    Lot(
                        product=p,
                        initial_load=ld,
                        supplier=sup if (j % 3 != 0) else None,
                        responsible=wh,
                        is_initial=True,
                        number=f"LB-{idx_p:04d}-{j}",
                        number_normalized=f"LB-{idx_p:04d}-{j}",
                        initial_quantity=10,
                        available_quantity=avail,
                        unit_cost=Decimal("2.5000"),
                        expiration_date=exp,
                    )
                )
        Lot.objects.bulk_create(lots_bulk, batch_size=1000)

    with connection.cursor() as cur:
        cur.execute("VACUUM ANALYZE;")
    print("PG_BENCH_SEEDED lots=", Lot.objects.count(), flush=True)

    def run_bench_pass(label: str) -> dict:
        out: dict = {"endpoints": {}, "explains": {}}
        with patch("django.utils.timezone.now", return_value=datetime(2026, 11, 14, 16, 0, tzinfo=dt_timezone.utc)):
            for key, url, client_obj in [
                ("expirations_30", "/productos/vencimientos/?dias=30", c_wh),
                ("expirations_7", "/productos/vencimientos/?dias=7", c_wh),
                ("stock_overview", "/inventario/stock/", c_wh),
                ("dashboard_admin", "/inicio/", c_ad),
                ("product_list", "/productos/", c_ad),
            ]:
                times_ms = []
                last_len = 0
                query_counts = []
                captured_sqls = []
                for it in range(5):
                    t0 = time.perf_counter()
                    resp = client_obj.get(url)
                    elapsed = (time.perf_counter() - t0) * 1000
                    assert resp.status_code == 200, (url, resp.status_code)
                    times_ms.append(round(elapsed, 2))
                    last_len = len(resp.content)
                with override_settings(DEBUG=True):
                    connection.force_debug_cursor = True
                    try:
                        with CaptureQueriesContext(connection) as qctx:
                            resp_q = client_obj.get(url)
                        assert resp_q.status_code == 200
                        query_counts.append(len(qctx))
                        captured_sqls = [q["sql"] for q in qctx.captured_queries]
                    finally:
                        connection.force_debug_cursor = False
                out["endpoints"][key] = {
                    "min_ms": min(times_ms),
                    "median_ms": statistics.median(times_ms),
                    "max_ms": max(times_ms),
                    "times_ms": times_ms,
                    "response_bytes": last_len,
                    "query_count": query_counts[0],
                }
                # EXPLAIN ANALYZE relevant SELECTs touching inventory_lot or catalog_product
                explains = []
                for sql_stmt in captured_sqls:
                    low = sql_stmt.lower()
                    if "inventory_lot" in low and low.strip().startswith("select"):
                        with connection.cursor() as cur:
                            cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql_stmt}")
                            plan = cur.fetchone()[0][0]
                        explains.append({
                            "sql_preview": sql_stmt[:260],
                            "planning_time_ms": round(plan.get("Planning Time", 0.0), 3),
                            "execution_time_ms": round(plan.get("Execution Time", 0.0), 3),
                            "top_node": plan["Plan"].get("Node Type"),
                            "actual_rows": plan["Plan"].get("Actual Rows"),
                            "shared_hit_blocks": plan["Plan"].get("Shared Hit Blocks"),
                            "shared_read_blocks": plan["Plan"].get("Shared Read Blocks"),
                            "plan_tree_summary": _summarize_plan(plan["Plan"]),
                        })
                out["explains"][key] = explains
        return out

    def _summarize_plan(node: dict) -> list[dict]:
        items = [{
            "node": node.get("Node Type"),
            "rel": node.get("Relation Name"),
            "index": node.get("Index Name"),
            "actual_ms": round(node.get("Actual Total Time", 0.0), 3),
            "actual_rows": node.get("Actual Rows"),
            "removed_by_filter": node.get("Rows Removed by Filter"),
        }]
        for ch in node.get("Plans", []):
            items.extend(_summarize_plan(ch))
        return items

    report["benchmarks"]["lot_total_rows"] = Lot.objects.count()
    report["benchmarks"]["product_total_rows"] = Product.objects.count()
    report["benchmarks"]["baseline_no_partial_idx"] = run_bench_pass("baseline")

    with connection.cursor() as cur:
        cur.execute(
            "CREATE INDEX idx_lot_exp_avail_gt0 ON inventory_lot (expiration_date, received_at, id) WHERE available_quantity > 0;"
        )
        cur.execute("ANALYZE inventory_lot;")
        cur.execute("SELECT pg_relation_size('idx_lot_exp_avail_gt0'), pg_size_pretty(pg_relation_size('idx_lot_exp_avail_gt0')), pg_size_pretty(pg_total_relation_size('inventory_lot'));")
        idx_bytes, idx_pretty, tbl_pretty = cur.fetchone()
    report["benchmarks"]["experimental_partial_index"] = {
        "ddl": "CREATE INDEX idx_lot_exp_avail_gt0 ON inventory_lot (expiration_date, received_at, id) WHERE available_quantity > 0",
        "index_bytes": idx_bytes,
        "index_size_pretty": idx_pretty,
        "table_total_size_pretty": tbl_pretty,
    }
    report["benchmarks"]["with_partial_idx"] = run_bench_pass("with_partial_idx")

    connection.close()
finally:
    if started:
        with contextlib.suppress(Exception):
            pg("pg_ctl", "-D", str(DBDIR), "-m", "fast", "-w", "stop")
    with socket.socket() as s:
        report["port_closed"] = s.connect_ex(("127.0.0.1", PORT)) != 0
    shutil.rmtree(TMP, ignore_errors=True)

after_hashes = {str(p.relative_to(ROOT)): sha256(p) for p in protected}
must_hold_keys = [
    k
    for k in before_hashes
    if (
        k.startswith("r1-pmv\\")
        or k.startswith("PLANIFICACION_SCRUM_R1PMV")
        or ("etapa07" in k.lower())
        or ("20261114" not in k and "20261115" not in k and "11b-" not in k.lower() and not k.startswith("datos\\temp"))
    )
]
report["protected_core_unchanged"] = all(before_hashes[k] == after_hashes.get(k) for k in must_hold_keys)
report["protected_unchanged"] = report["protected_core_unchanged"]
report["concurrent_external_db_changes"] = [k for k in before_hashes if before_hashes[k] != after_hashes.get(k)]

out_path = EVID / f"pg-bench-07b-{STAMP}.json"
out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
print("WROTE:", out_path)
print("CONCURRENT_OK:", report["cases"].get("concurrent_checkout_read_committed", {}).get("ok"))
print("PORT_CLOSED:", report["port_closed"], "PROTECTED_UNCHANGED:", report["protected_unchanged"])
base_exp = report["benchmarks"].get("baseline_no_partial_idx", {}).get("endpoints", {}).get("expirations_30", {})
idx_exp = report["benchmarks"].get("with_partial_idx", {}).get("endpoints", {}).get("expirations_30", {})
print("EXP30_MEDIAN_MS baseline=", base_exp.get("median_ms"), "with_idx=", idx_exp.get("median_ms"))
