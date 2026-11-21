"""Stage 10-C isolated depth verification:
1) Build & planning snapshot check (read-only over r1-pmv and 08).
2) PT-SEARCH-01 scale benchmark (2,000 products / 20,000 lots) on isolated PostgreSQL 18.4 & SQLite.
3) Isolated clone migration & invariant check of r1-pmv/r1_pmv.sqlite3 (operational DB untouched).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import secrets
import shutil
import socket
import sqlite3
import statistics
import subprocess
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone as dt_tz
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parents[0]
ROOT = RESULTS.parents[1]
PMV = ROOT / "r1-pmv"
PYTHON = PMV / ".venv" / "Scripts" / "python.exe"
PG_BIN = Path("C:/Program Files/PostgreSQL/18/bin")
EV_DIR = RESULTS / "evidencias" / "10-C-20261114"
OPERATIONAL_DB = PMV / "r1_pmv.sqlite3"
PLAN08 = ROOT / "08_Historias_de_Usuario.md"
REGEN_SCRIPT = RESULTS / "fuente_unica_20261112" / "regenerar_vistas.py"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical_pmv_snapshot() -> dict:
    excluded_dirs = {".venv", "__pycache__", "staticfiles", ".git", ".pytest_cache"}
    excluded_files = {"r1_pmv.sqlite3", "r1_pmv.sqlite3-wal", "r1_pmv.sqlite3-shm", ".env"}
    entries: list[str] = []
    for p in sorted(PMV.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(PMV)
        if any(part in excluded_dirs for part in rel.parts):
            continue
        if rel.name in excluded_files or p.suffix == ".pyc":
            continue
        entries.append(f"{rel.as_posix()}:{file_sha256(p)}")
    digest = hashlib.sha256("\n".join(entries).encode("utf-8")).hexdigest()
    r_head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=str(PMV), capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    r_regen = subprocess.run(
        [str(PYTHON), str(REGEN_SCRIPT), "--check"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return {
        "timestamp_utc": datetime.now(dt_tz.utc).isoformat(),
        "git_head": (r_head.stdout or "").strip() if r_head.returncode == 0 else None,
        "manifest_file_count": len(entries),
        "manifest_sha256": digest,
        "plan08_sha256": file_sha256(PLAN08),
        "operational_db_sha256": file_sha256(OPERATIONAL_DB),
        "regenerar_vistas_exit": r_regen.returncode,
        "regenerar_vistas_output": (r_regen.stdout or "").strip(),
    }


def make_run_dir(tag: str) -> Path:
    stamp = datetime.now(dt_tz.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RESULTS / "datos" / f"etapa10c-{tag}-{stamp}-{secrets.token_hex(4)}"
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "marker.json").write_text(
        json.dumps({"run": run_dir.name, "stage": "10-C", "tag": tag, "created_utc": stamp}),
        encoding="utf-8",
    )
    (run_dir / ".django-key").write_text("audit10c-" + secrets.token_hex(32), encoding="utf-8")
    return run_dir


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_pg(pg_dir: Path, port: int, db_name: str) -> None:
    pgdata = pg_dir / "data"
    logfile = pg_dir / "pg.log"
    r_init = subprocess.run(
        [str(PG_BIN / "initdb.exe"), "-D", str(pgdata), "-U", "postgres", "-A", "trust", "-E", "UTF8", "--locale=C"],
        capture_output=True, text=True, encoding="cp1252", errors="replace",
    )
    if r_init.returncode != 0:
        raise RuntimeError("initdb failed: " + r_init.stdout + r_init.stderr)
    r_start = subprocess.run(
        [str(PG_BIN / "pg_ctl.exe"), "-D", str(pgdata), "-l", str(logfile), "-o", f"-p {port} -h 127.0.0.1", "-w", "start"],
        capture_output=True, text=True, encoding="cp1252", errors="replace", timeout=30,
    )
    if r_start.returncode != 0:
        raise RuntimeError("pg_ctl start failed: " + r_start.stdout + r_start.stderr)
    r_cdb = subprocess.run(
        [str(PG_BIN / "createdb.exe"), "-h", "127.0.0.1", "-p", str(port), "-U", "postgres", db_name],
        capture_output=True, text=True, encoding="cp1252", errors="replace", timeout=20,
    )
    if r_cdb.returncode != 0:
        raise RuntimeError("createdb failed: " + r_cdb.stdout + r_cdb.stderr)


def stop_pg(pg_dir: Path) -> None:
    pgdata = pg_dir / "data"
    if (pgdata / "postmaster.pid").exists():
        subprocess.run(
            [str(PG_BIN / "pg_ctl.exe"), "-D", str(pgdata), "stop", "-m", "immediate", "-w"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15,
        )


def make_ean13(prefix12: str) -> str:
    checksum = sum(int(d) * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(prefix12)))
    return prefix12 + str((10 - checksum % 10) % 10)


def percentile_nearest_rank(sorted_vals: list[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    rank = max(1, math.ceil((pct / 100.0) * len(sorted_vals)))
    return round(sorted_vals[min(rank - 1, len(sorted_vals) - 1)], 2)


def worker_scale_bench() -> dict:
    sys.path.insert(0, str(PMV))
    sys.path.insert(0, str(HERE))
    import django
    django.setup()

    from django.core.management import call_command
    from django.db import connection
    from django.test import Client
    from django.test.utils import CaptureQueriesContext
    from django.utils import timezone

    from catalog.barcodes import reading_keys
    from catalog.models import Category, Product, ProductBarcodeKey
    from cash.models import CashRegister, CashShift
    from identity.models import Account, Role
    from inventory.models import InitialInventoryLoad, Lot
    from sales.services import add_product_to_draft
    from sales.views import _search_products

    t_seed_start = time.perf_counter()
    call_command("migrate", verbosity=0, interactive=False)

    r_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    r_sell, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})
    pw = f"Scale10c!{secrets.token_hex(8)}"
    admin = Account.objects.create_user(email="admin.scale@demo.invalid", display_name="Admin Scale", role=r_admin, password=pw)
    wh = Account.objects.create_user(email="wh.scale@demo.invalid", display_name="Almacenero Scale", role=r_wh, password=pw)
    seller = Account.objects.create_user(email="seller.scale@demo.invalid", display_name="Vendedor Scale", role=r_sell, password=pw)
    reg = CashRegister.objects.create(code="CAJA-01", is_active=True)
    CashShift.objects.create(cash_register=reg, seller=seller, opening_amount=Decimal("100.00"))
    cat = Category.objects.create(name="Abarrotes y Conservas", is_active=True)

    today = timezone.localdate()
    exp_past = today - timedelta(days=5)
    exp_today = today
    future_dates = [today + timedelta(days=30 * k) for k in range(1, 6)]

    products: list[Product] = []
    barcode_1999 = make_ean13("775000001999")
    barcode_2000_expired = make_ean13("775000002000")
    for idx in range(1, 2001):
        code = make_ean13(f"7750000{idx:05d}")
        if idx == 1999:
            name = f"Atun Especial {idx}"
        elif idx == 2000:
            name = f"Conserva Vencida {idx}"
        elif 101 <= idx <= 150:
            name = f"Producto Escala MarcaDorada {idx:04d}"
        else:
            name = f"Producto Escala {idx:04d}"
        norm_name = Product.normalize_search_name(name)
        norm_code = Product.normalize_barcode(code)
        products.append(
            Product(
                id=uuid.uuid4(),
                category=cat,
                name=name,
                search_name=norm_name,
                barcode=code,
                barcode_type=Product.BarcodeType.GTIN,
                barcode_normalized=norm_code,
                unit=Product.Unit.UNIT,
                sale_price=Decimal("4.50") + Decimal(idx % 50) * Decimal("0.10"),
                minimum_stock=5,
                controls_expiration=True,
                average_cost=Decimal("2.5000"),
                is_active=True,
            )
        )
    Product.objects.bulk_create(products, batch_size=500)

    key_rows: list[ProductBarcodeKey] = []
    load_rows: list[InitialInventoryLoad] = []
    for p in products:
        for k in sorted(reading_keys(p.barcode, p.barcode_type)):
            key_rows.append(ProductBarcodeKey(product=p, reading_key=k))
        load_rows.append(InitialInventoryLoad(id=uuid.uuid4(), product=p, responsible=wh))
    ProductBarcodeKey.objects.bulk_create(key_rows, batch_size=1000)
    InitialInventoryLoad.objects.bulk_create(load_rows, batch_size=500)

    lot_rows: list[Lot] = []
    for idx, (p, load) in enumerate(zip(products, load_rows), start=1):
        if idx == 2000:
            # 10 lots all expired/today (non-sellable)
            specs = [(exp_past, 4, 4)] * 5 + [(exp_today, 4, 4)] * 5
        else:
            # 2 expired, 1 today, 2 depleted (avail=0), 5 future sellable (avail=4 => sellable=20)
            specs = [
                (exp_past, 3, 3),
                (exp_past, 3, 3),
                (exp_today, 2, 2),
                (future_dates[0], 5, 0),
                (future_dates[1], 5, 0),
                *[(d, 4, 4) for d in future_dates],
            ]
        for lno, (edate, init_q, avail_q) in enumerate(specs, start=1):
            num = f"L-{idx:04d}-{lno:02d}"
            lot_rows.append(
                Lot(
                    id=uuid.uuid4(),
                    product=p,
                    initial_load=load,
                    supplier=None,
                    responsible=wh,
                    is_initial=True,
                    number=num,
                    number_normalized=Lot.normalize_number(num),
                    initial_quantity=init_q,
                    available_quantity=avail_q,
                    unit_cost=Decimal("2.5000"),
                    expiration_date=edate,
                )
            )
    Lot.objects.bulk_create(lot_rows, batch_size=2000)

    # Active 5-line draft to match realistic POS reload load
    for line_idx in range(5):
        add_product_to_draft(actor=seller, product_id=products[line_idx].pk, quantity=1 + (line_idx % 3))

    if connection.vendor == "postgresql":
        with connection.cursor() as cur:
            cur.execute("ANALYZE;")

    seed_elapsed_s = round(time.perf_counter() - t_seed_start, 3)

    db_meta: dict = {
        "vendor": connection.vendor,
        "product_count": Product.objects.count(),
        "barcode_key_count": ProductBarcodeKey.objects.count(),
        "lot_count": Lot.objects.count(),
        "seed_elapsed_s": seed_elapsed_s,
    }
    if connection.vendor == "postgresql":
        with connection.cursor() as cur:
            cur.execute("SELECT version();")
            db_meta["pg_version"] = cur.fetchone()[0]
            cur.execute(
                """
                SELECT
                    pg_total_relation_size('catalog_product'),
                    pg_total_relation_size('catalog_productbarcodekey'),
                    pg_total_relation_size('inventory_lot')
                """
            )
            p_sz, k_sz, l_sz = cur.fetchone()
            db_meta["relation_sizes_bytes"] = {
                "catalog_product_total": p_sz,
                "catalog_productbarcodekey_total": k_sz,
                "inventory_lot_total": l_sz,
            }

    client = Client()
    client.force_login(seller)

    scenarios = [
        ("S1_barcode_exact", f"/ventas/?query={barcode_1999}", barcode_1999, 1, 25),
        ("S2_name_specific", "/ventas/?query=Atun%20Especial%201999", "Atun Especial 1999", 1, 25),
        ("S3_medium_50_matches", "/ventas/?query=MarcaDorada", "MarcaDorada", 50, 25),
        ("S4_broad_1999_matches", "/ventas/?query=Producto%20Escala", "Producto Escala", 1998, 5),
        ("S5_expired_only_code", f"/ventas/?query={barcode_2000_expired}", barcode_2000_expired, 0, 25),
        ("S6_no_match", "/ventas/?query=NOEXISTE99999", "NOEXISTE99999", 0, 25),
        ("S7_empty_draft_view", "/ventas/", None, None, 25),
    ]

    results = []
    for sid, url, raw_q, expected_min_rows, iters in scenarios:
        # Warmup once
        t_w0 = time.perf_counter()
        resp_w = client.get(url)
        warmup_ms = round((time.perf_counter() - t_w0) * 1000.0, 2)

        latencies_ms: list[float] = []
        last_bytes = len(resp_w.content)
        last_status = resp_w.status_code
        sql_count = None
        for idx_it in range(iters):
            if idx_it == 0:
                with CaptureQueriesContext(connection) as ctx:
                    t0 = time.perf_counter()
                    r = client.get(url)
                    elapsed_ms = (time.perf_counter() - t0) * 1000.0
                sql_count = len(ctx)
            else:
                t0 = time.perf_counter()
                r = client.get(url)
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(round(elapsed_ms, 2))
            last_bytes = len(r.content)
            last_status = r.status_code

        qs_count = _search_products(raw_q).count() if raw_q is not None else None
        pg_explain = None
        if connection.vendor == "postgresql" and raw_q is not None:
            qs = _search_products(raw_q)
            sql_stmt, params = qs.query.sql_with_params()
            with connection.cursor() as cur:
                cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {sql_stmt}", params)
                plan_doc = cur.fetchone()[0][0]
            pg_explain = {
                "execution_time_ms": round(float(plan_doc.get("Execution Time", 0.0)), 3),
                "planning_time_ms": round(float(plan_doc.get("Planning Time", 0.0)), 3),
                "top_node": plan_doc.get("Plan", {}).get("Node Type"),
                "actual_rows": plan_doc.get("Plan", {}).get("Actual Rows"),
                "plan_tree": plan_doc.get("Plan"),
            }

        sorted_l = sorted(latencies_ms)
        row_ok = True if qs_count is None else (
            qs_count == expected_min_rows if expected_min_rows in (0, 1, 50) else qs_count >= expected_min_rows
        )
        p95 = percentile_nearest_rank(sorted_l, 95)
        results.append(
            {
                "id": sid,
                "url": url,
                "iterations": iters,
                "http_status": last_status,
                "orm_result_count": qs_count,
                "row_count_ok": row_ok,
                "sql_query_count": sql_count,
                "response_bytes": last_bytes,
                "warmup_ms": warmup_ms,
                "min_ms": min(sorted_l),
                "median_ms": round(statistics.median(sorted_l), 2),
                "p95_ms": p95,
                "max_ms": max(sorted_l),
                "within_nfr05_2000ms_p95": p95 <= 2000.0,
                "pg_explain": pg_explain,
            }
        )

    return {"db_meta": db_meta, "scenarios": results}


def worker_clone_migration() -> dict:
    sys.path.insert(0, str(PMV))
    sys.path.insert(0, str(HERE))
    clone_path = Path(os.environ["AUDIT10C_RUN_DIR"]).resolve() / "r1_pmv_clone.sqlite3"
    if not clone_path.exists() or clone_path == OPERATIONAL_DB.resolve():
        raise RuntimeError(f"Unsafe clone db: {clone_path}")

    # Pre-migration raw SQLite inspection
    con = sqlite3.connect(str(clone_path))
    cur = con.cursor()
    pre_tables = {
        row[0]: cur.execute(f"SELECT COUNT(*) FROM \"{row[0]}\"").fetchone()[0]
        for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
        if row[0] in {
            "identity_account",
            "cash_cashshift",
            "cash_cashmovement",
            "sales_saledraft",
            "sales_saledraftline",
            "sales_sale",
            "sales_saleline",
            "catalog_product",
            "inventory_lot",
            "django_migrations",
        }
    }
    bad_draft_lines_qty = cur.execute(
        "SELECT COUNT(*) FROM sales_saledraftline WHERE quantity <= 0 OR quantity > 999999 OR unit_price <= 0"
    ).fetchone()[0]
    active_drafts_per_shift_dups = cur.execute(
        "SELECT cash_shift_id, COUNT(*) FROM sales_saledraft WHERE status='ACTIVE' GROUP BY cash_shift_id HAVING COUNT(*) > 1"
    ).fetchall()
    con.close()

    import io
    import django
    django.setup()
    from django.core.management import call_command

    def cap_cmd(*args, **kwargs) -> str:
        buf = io.StringIO()
        call_command(*args, stdout=buf, stderr=buf, **kwargs)
        return buf.getvalue()

    show_before = cap_cmd("showmigrations", "--list")
    pending_before = [ln.strip() for ln in show_before.splitlines() if "[ ]" in ln]
    migrate_plan = cap_cmd("migrate", "--plan")
    migrate_out = cap_cmd("migrate", interactive=False, verbosity=1)
    show_after = cap_cmd("showmigrations", "--list")
    pending_after = [ln.strip() for ln in show_after.splitlines() if "[ ]" in ln]
    check_out = cap_cmd("check")
    makemig_out = cap_cmd("makemigrations", check=True, dry_run=True)

    from catalog.models import Product
    from cash.models import CashShift
    from inventory.models import Lot
    from sales.models import Sale, SaleDraft, SaleDraftLine
    from sales.services import draft_totals
    from sales.views import _search_products

    post_counts = {
        "cash_shift": CashShift.objects.count(),
        "sale_draft": SaleDraft.objects.count(),
        "sale_draft_line": SaleDraftLine.objects.count(),
        "sale": Sale.objects.count(),
        "product": Product.objects.count(),
        "lot": Lot.objects.count(),
    }
    first_draft = SaleDraft.objects.filter(status=SaleDraft.Status.ACTIVE).first()
    totals_sample = None
    if first_draft is not None:
        t = draft_totals(first_draft)
        totals_sample = {"total": str(t.total), "base": str(t.base), "igv": str(t.igv)}
    search_sample_count = _search_products("a").count()

    return {
        "pre_tables": pre_tables,
        "pre_bad_draft_lines_qty_or_price": bad_draft_lines_qty,
        "pre_active_draft_shift_duplicates": len(active_drafts_per_shift_dups),
        "pending_migrations_before": pending_before,
        "migrate_plan_lines": [ln for ln in migrate_plan.splitlines() if ln.strip()],
        "migrate_output_lines": [ln for ln in migrate_out.splitlines() if ln.strip()],
        "pending_migrations_after": pending_after,
        "check_output": check_out.strip(),
        "makemigrations_check_output": makemig_out.strip(),
        "post_counts": post_counts,
        "sample_active_draft_totals": totals_sample,
        "sample_search_a_count": search_sample_count,
    }


def run_worker_subprocess(mode: str, run_dir: Path, extra_env: dict[str, str] | None = None) -> dict:
    env = os.environ.copy()
    env.update(
        {
            "AUDIT10C_WORKER": mode,
            "AUDIT10C_MODE": "clone" if mode == "clone" else ("pg" if mode == "pg" else "sqlite"),
            "AUDIT10C_RUN_DIR": str(run_dir),
            "DJANGO_SETTINGS_MODULE": "audit10c_settings",
            "PYTHONPATH": str(HERE) + os.pathsep + str(PMV),
            "PYTHONUTF8": "1",
        }
    )
    if extra_env:
        env.update(extra_env)
    r = subprocess.run(
        [str(PYTHON), str(Path(__file__).resolve())],
        env=env,
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    if r.returncode != 0:
        raise RuntimeError(f"Worker {mode} failed (exit={r.returncode}):\nSTDOUT:\n{r.stdout}\nSTDERR:\n{r.stderr}")
    lines = [ln for ln in (r.stdout or "").splitlines() if ln.strip()]
    return json.loads(lines[-1])


def main() -> int:
    worker_mode = os.environ.get("AUDIT10C_WORKER")
    if worker_mode in ("pg", "sqlite"):
        print(json.dumps(worker_scale_bench(), ensure_ascii=False))
        return 0
    if worker_mode == "clone":
        print(json.dumps(worker_clone_migration(), ensure_ascii=False))
        return 0

    EV_DIR.mkdir(parents=True, exist_ok=True)
    db_sha_before = file_sha256(OPERATIONAL_DB)

    snapshot = canonical_pmv_snapshot()
    (EV_DIR / "build-snapshot-10c.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    # 1) PostgreSQL 18.4 PT-SEARCH-01 (2,000 products / 20,000 lots)
    pg_run_dir = make_run_dir("pg")
    port = free_port()
    try:
        start_pg(pg_run_dir, port, "audit10c_pg")
        pg_res = run_worker_subprocess(
            "pg",
            pg_run_dir,
            {"AUDIT10C_PG_PORT": str(port), "AUDIT10C_PG_DB": "audit10c_pg"},
        )
        pg_doc = {
            "timestamp_utc": datetime.now(dt_tz.utc).isoformat(),
            "operational_db_sha256_before": db_sha_before,
            "operational_db_sha256_after": file_sha256(OPERATIONAL_DB),
            "operational_db_untouched": db_sha_before == file_sha256(OPERATIONAL_DB),
            **pg_res,
        }
        (EV_DIR / "pt-search-01-pg18.json").write_text(
            json.dumps(pg_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        stop_pg(pg_run_dir)
        shutil.rmtree(pg_run_dir, ignore_errors=True)

    # 2) SQLite PT-SEARCH-01 (2,000 products / 20,000 lots)
    sq_run_dir = make_run_dir("sqlite")
    try:
        sq_res = run_worker_subprocess("sqlite", sq_run_dir)
        sq_doc = {
            "timestamp_utc": datetime.now(dt_tz.utc).isoformat(),
            "operational_db_sha256_before": db_sha_before,
            "operational_db_sha256_after": file_sha256(OPERATIONAL_DB),
            "operational_db_untouched": db_sha_before == file_sha256(OPERATIONAL_DB),
            **sq_res,
        }
        (EV_DIR / "pt-search-01-sqlite.json").write_text(
            json.dumps(sq_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        shutil.rmtree(sq_run_dir, ignore_errors=True)

    # 3) Isolated clone migration rehearsal on r1_pmv.sqlite3 copy
    cl_run_dir = make_run_dir("clone")
    try:
        shutil.copy2(OPERATIONAL_DB, cl_run_dir / "r1_pmv_clone.sqlite3")
        cl_res = run_worker_subprocess("clone", cl_run_dir)
        db_sha_after = file_sha256(OPERATIONAL_DB)
        cl_doc = {
            "timestamp_utc": datetime.now(dt_tz.utc).isoformat(),
            "operational_db_sha256_before": db_sha_before,
            "operational_db_sha256_after": db_sha_after,
            "operational_db_untouched": db_sha_before == db_sha_after,
            **cl_res,
        }
        (EV_DIR / "clone-migration-check.json").write_text(
            json.dumps(cl_doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    finally:
        shutil.rmtree(cl_run_dir, ignore_errors=True)

    summary = {
        "operational_db_untouched": file_sha256(OPERATIONAL_DB) == db_sha_before,
        "operational_db_sha256": file_sha256(OPERATIONAL_DB),
        "plan08_sha256": snapshot["plan08_sha256"],
        "git_head": snapshot["git_head"],
        "manifest_sha256": snapshot["manifest_sha256"],
        "pg18_scenarios": [
            {k: s[k] for k in ("id", "orm_result_count", "sql_query_count", "response_bytes", "median_ms", "p95_ms", "max_ms", "within_nfr05_2000ms_p95")}
            for s in pg_doc["scenarios"]
        ],
        "sqlite_scenarios": [
            {k: s[k] for k in ("id", "orm_result_count", "sql_query_count", "response_bytes", "median_ms", "p95_ms", "max_ms", "within_nfr05_2000ms_p95")}
            for s in sq_doc["scenarios"]
        ],
        "clone_pending_before": cl_doc["pending_migrations_before"],
        "clone_pending_after": cl_doc["pending_migrations_after"],
        "clone_pre_bad_draft_lines": cl_doc["pre_bad_draft_lines_qty_or_price"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
