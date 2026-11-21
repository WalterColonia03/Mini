"""Stage 07 real PostgreSQL 18.4 verification: timezone midnight boundaries,
deterministic ordering, READ COMMITTED concurrency under active writes/locks,
NUL-byte / non-ASCII query guards, N+1 constant query check, and EXPLAIN plan analysis.
Runs in an ephemeral owned cluster (AUDIT07_OWNED) and never alters existing SQLite DBs.
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
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "auditoria_por_etapas/resultados"
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
STAMP = datetime.now(dt_timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
CLUSTER = (Path(tempfile.gettempdir()) / ("audit07-pg-" + secrets.token_hex(12))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT07_OWNED"
MARK.write_text(STAMP, encoding="utf-8")
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(40)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit07_" + secrets.token_hex(5)
with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]

protected = [
    *(ROOT / "r1-pmv").glob("*.sqlite3"),
    *(RESULTS / "datos").rglob("*.sqlite3"),
    ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
]


def state_hash(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


hashes = {str(p.relative_to(ROOT)): state_hash(p) for p in protected}
report = {
    "started_utc": STAMP,
    "cluster": str(CLUSTER),
    "port": PORT,
    "cases": [],
    "protected_absent_at_start": [k for k, v in hashes.items() if v is None],
}


def own() -> None:
    assert CLUSTER.parent == Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith("audit07-pg-")
    assert MARK.read_text(encoding="utf-8") == STAMP


def pg(name: str, *args) -> None:
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as f:
        result = subprocess.run(
            [str(BIN / (name + ".exe")), *map(str, args)],
            stdout=f,
            stderr=f,
            timeout=50,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        f.seek(0)
        diagnostic = f.read().replace(PW, "[REDACTED]")
    if result.returncode:
        raise RuntimeError(name + " failed: " + diagnostic[-800:])


started = False
configured = False
try:
    own()
    pg(
        "initdb",
        "-D",
        DBDIR,
        "-U",
        "audit07",
        "--pwfile",
        PWFILE,
        "--auth-host=scram-sha-256",
        "--auth-local=scram-sha-256",
        "--encoding=UTF8",
        "--locale=C",
    )
    PWFILE.unlink()
    pg(
        "pg_ctl",
        "-D",
        DBDIR,
        "-l",
        CLUSTER / "postgres.log",
        "-o",
        f"-h 127.0.0.1 -p {PORT} -c log_statement=none -c log_min_error_statement=panic",
        "-w",
        "start",
    )
    started = True

    import psycopg
    from psycopg import sql

    conf = {"host": "127.0.0.1", "port": PORT, "user": "audit07", "password": PW}
    with psycopg.connect(**conf, dbname="postgres", autocommit=True) as conn:
        assert Path(conn.execute("SHOW data_directory").fetchone()[0]).resolve() == DBDIR
        report["version"] = conn.execute("SELECT version()").fetchone()[0]
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DBNAME)))

    sys.path.insert(0, str(ROOT / "r1-pmv"))
    os.environ.update(
        APP_ENV="test",
        DJANGO_DEBUG="false",
        DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
        DJANGO_SETTINGS_MODULE="config.settings",
    )
    from config import env

    loader = env.load_dotenv
    env.load_dotenv = lambda path=None: None
    from django.conf import settings

    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": DBNAME,
            "USER": "audit07",
            "PASSWORD": PW,
            "HOST": "127.0.0.1",
            "PORT": PORT,
            "CONN_MAX_AGE": 0,
            "OPTIONS": {"options": "-c statement_timeout=20000 -c lock_timeout=12000"},
        }
    }
    settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
    env.load_dotenv = loader

    import django

    django.setup()
    configured = True

    from django.core.management import call_command
    from django.db import close_old_connections, connection, connections, transaction
    from django.test import Client
    from django.test.utils import CaptureQueriesContext, setup_test_environment
    from django.utils import timezone as tz

    setup_test_environment()

    from cash.models import CashRegister, CashShift
    from catalog.models import Category, Product
    from catalog.services import toggle_category_status
    from identity.models import Account, Role
    from inventory.models import Lot, StockWriteOff, Supplier
    from inventory.services import LotInput, confirm_initial_load, write_off_stock
    from sales.models import Sale, SaleCounter
    from sales.services import add_product_to_draft, checkout_sale, sellable_stock_for_product
    from sales.views import _search_products

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    with connection.cursor() as cur:
        cur.execute("SELECT current_database(), current_setting('data_directory'), current_setting('transaction_isolation')")
        db, folder, iso = cur.fetchone()
        assert db == DBNAME and Path(folder).resolve() == DBDIR
    report.update(database=db, isolation=iso)

    admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
    pw_user = "PgAudit07#Pass123"
    admin = Account.objects.create_user("admin.pg07@test.invalid", pw_user, display_name="Admin PG07", role=admin_role)
    wh1 = Account.objects.create_user("wh1.pg07@test.invalid", pw_user, display_name="Almacen1 PG07", role=wh_role)
    wh2 = Account.objects.create_user("wh2.pg07@test.invalid", pw_user, display_name="Almacen2 PG07", role=wh_role)
    seller = Account.objects.create_user("seller.pg07@test.invalid", pw_user, display_name="Vendedora PG07", role=seller_role)

    cat_tz = Category.objects.create(name="PG07 Lacteos TZ")
    reg = CashRegister.objects.create(code="CAJA-PG07")
    shift = CashShift.objects.create(cash_register=reg, seller=seller, opening_amount=Decimal("50.00"))
    SaleCounter.objects.get_or_create(pk=1)

    # ── Case 1: PostgreSQL UTC vs America/Lima midnight boundary for lots AND sales ──
    p_tz = Product.objects.create(
        category=cat_tz, name="Leche Medianoche PG07", barcode="775070000101", sale_price=Decimal("6.00"), minimum_stock=3
    )
    t_before_lima_mid = datetime(2026, 11, 12, 4, 59, 59, tzinfo=dt_timezone.utc)  # 2026-11-11 23:59:59 Lima
    t_at_lima_mid = datetime(2026, 11, 12, 5, 0, 0, tzinfo=dt_timezone.utc)        # 2026-11-12 00:00:00 Lima
    with patch("django.utils.timezone.now", return_value=t_before_lima_mid):
        confirm_initial_load(actor=wh1, product=p_tz, lots=[LotInput("PG-TZ-12NOV", 5, Decimal("2.50"), date(2026, 11, 12))])
    import uuid as uuid_mod
    s1 = Sale.objects.create(
        correlative="V-00009001", cash_shift=shift, seller=seller,
        total_amount=Decimal("9.00"), base_amount=Decimal("7.63"), igv_amount=Decimal("1.37"),
        discount_amount=Decimal("1.00"), cash_received=Decimal("10.00"), change_given=Decimal("1.00"),
        idempotency_key=uuid_mod.uuid4(),
    )
    Sale.objects.filter(pk=s1.pk).update(confirmed_at=t_before_lima_mid)
    s2 = Sale.objects.create(
        correlative="V-00009002", cash_shift=shift, seller=seller,
        total_amount=Decimal("20.00"), base_amount=Decimal("16.95"), igv_amount=Decimal("3.05"),
        discount_amount=Decimal("0.00"), cash_received=Decimal("20.00"), change_given=Decimal("0.00"),
        idempotency_key=uuid_mod.uuid4(),
    )
    Sale.objects.filter(pk=s2.pk).update(confirmed_at=t_at_lima_mid)
    c_adm = Client()
    c_adm.force_login(admin)
    with patch("django.utils.timezone.now", return_value=t_before_lima_mid):
        sum_before = c_adm.get("/inicio/").context["summary"]
        exp_before = c_adm.get("/productos/vencimientos/?dias=1").content.decode()
        pos_before = sellable_stock_for_product(p_tz)
        pos_q_before = list(_search_products("Medianoche PG07"))
    with patch("django.utils.timezone.now", return_value=t_at_lima_mid):
        sum_after = c_adm.get("/inicio/").context["summary"]
        exp_after = c_adm.get("/productos/vencimientos/?dias=1").content.decode()
        pos_after = sellable_stock_for_product(p_tz)
        pos_q_after = list(_search_products("Medianoche PG07"))

    c1_ok = (
        str(sum_before["sales_total"]) == "9.00"
        and sum_before["expired"] == 0
        and sum_before["expiring"] == 1
        and sum_before["low_stock"] == 0
        and pos_before == 5
        and len(pos_q_before) == 1
        and "En 1 día" in exp_before
        and str(sum_after["sales_total"]) == "20.00"
        and sum_after["expired"] == 1
        and sum_after["expiring"] == 0
        and sum_after["low_stock"] == 1
        and pos_after == 0
        and len(pos_q_after) == 0
        and "Vence hoy" in exp_after
        and "Bloqueado para venta" in exp_after
    )
    report["cases"].append({
        "id": "pg_timezone_midnight_boundary_lots_and_sales",
        "ok": c1_ok,
        "checks": {
            "before": {"summary": {k: str(v) for k, v in sum_before.items()}, "pos_stock": pos_before},
            "after": {"summary": {k: str(v) for k, v in sum_after.items()}, "pos_stock": pos_after},
        },
    })

    # Clean PG-TZ lot zero so next cases run on clean current Lima baseline
    Lot.objects.filter(product=p_tz).update(available_quantity=0)

    # ── Case 2: Deterministic tie-break ordering and zero-qty filter on PG ──
    today = tz.localdate()
    p_ord = Product.objects.create(
        category=cat_tz, name="Orden PG07", barcode="775070000201", sale_price=Decimal("4.00"), minimum_stock=2
    )
    t1, t2 = tz.now() - timedelta(hours=3), tz.now() - timedelta(hours=1)
    with patch("django.utils.timezone.now", return_value=t1):
        l_init = confirm_initial_load(
            actor=wh1,
            product=p_ord,
            lots=[
                LotInput("PG-ZERO", 5, Decimal("1.50"), today + timedelta(days=1)),
                LotInput("PG-Z-EARLY", 3, Decimal("1.50"), today + timedelta(days=1)),
            ],
        )
    with patch("django.utils.timezone.now", return_value=t2):
        Lot.objects.create(
            product=p_ord, initial_load=l_init, responsible=wh2, is_initial=False,
            number="PG-A-LATE", initial_quantity=3, available_quantity=3,
            unit_cost=Decimal("1.50"), expiration_date=today + timedelta(days=1),
        )
    Lot.objects.filter(product=p_ord, number_normalized="PG-ZERO").update(available_quantity=0)

    exp_ord_resp = c_adm.get("/productos/vencimientos/")
    stock_ord_resp = c_adm.get("/inventario/stock/")
    exp_nums = [l.number_normalized for l in exp_ord_resp.context["lots"]]
    so_expiring_nums = [l.number_normalized for l in stock_ord_resp.context["expiring_lots"]]
    c2_ok = exp_nums == ["PG-Z-EARLY", "PG-A-LATE"] and so_expiring_nums == ["PG-Z-EARLY", "PG-A-LATE"]
    report["cases"].append({
        "id": "pg_deterministic_tie_order_and_zero_qty_filter",
        "ok": c2_ok,
        "checks": {"exp_nums": exp_nums, "so_expiring_nums": so_expiring_nums},
    })

    # ── Case 3: READ COMMITTED concurrent readers under open SELECT FOR UPDATE writeoff lock ──
    p_conc = Product.objects.create(
        category=cat_tz, name="Concurrencia PG07", barcode="775070000301", sale_price=Decimal("5.00"), minimum_stock=5
    )
    load_c = confirm_initial_load(
        actor=wh1, product=p_conc, lots=[LotInput("PG-CONC-VENC", 6, Decimal("2.00"), today + timedelta(days=2))]
    )
    lot_conc = load_c.lots.get()
    Lot.objects.filter(pk=lot_conc.pk).update(expiration_date=today - timedelta(days=1))
    lot_conc.refresh_from_db()

    ready_wo = threading.Event()
    release_wo = threading.Event()

    def writeoff_lock_holder():
        close_old_connections()
        try:
            with transaction.atomic():
                write_off_stock(
                    actor=wh1, lot=lot_conc, quantity=6, reason=StockWriteOff.Reason.EXPIRATION, notes="Retiro conc PG07"
                )
                ready_wo.set()
                release_wo.wait(timeout=8)
                return "committed"
        finally:
            close_old_connections()

    def concurrent_readers():
        close_old_connections()
        try:
            ready_wo.wait(timeout=8)
            cl = Client()
            cl.force_login(admin)
            r_dash = cl.get("/inicio/")
            r_stock = cl.get("/inventario/stock/")
            r_exp = cl.get("/productos/vencimientos/")
            return {
                "statuses": [r_dash.status_code, r_stock.status_code, r_exp.status_code],
                "expired_pre_commit": r_dash.context["summary"]["expired"],
                "has_lot_pre_commit": "PG-CONC-VENC" in r_exp.content.decode(),
            }
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_w = pool.submit(writeoff_lock_holder)
        f_r = pool.submit(concurrent_readers)
        during_lock = f_r.result(timeout=8)
        release_wo.set()
        wo_done = f_w.result(timeout=8)

    post_dash = c_adm.get("/inicio/").context["summary"]
    post_exp = c_adm.get("/productos/vencimientos/").content.decode()
    c3_ok = (
        wo_done == "committed"
        and during_lock["statuses"] == [200, 200, 200]
        and during_lock["expired_pre_commit"] == 1
        and during_lock["has_lot_pre_commit"] is True
        and post_dash["expired"] == 0
        and "PG-CONC-VENC" not in post_exp
    )
    report["cases"].append({
        "id": "pg_concurrent_read_committed_under_write_locks",
        "ok": c3_ok,
        "checks": {"during_lock": during_lock, "post_commit_expired": post_dash["expired"]},
    })

    # ── Case 4: NUL byte & non-ASCII/extreme query params rejected before SQL in PostgreSQL ──
    nul_dias = c_adm.get("/productos/vencimientos/", {"dias": "1\x00"})
    arabic_dias = c_adm.get("/productos/vencimientos/", {"dias": "٥"})
    plus_dias = c_adm.get("/productos/vencimientos/", {"dias": "+7"})
    over_dias = c_adm.get("/productos/vencimientos/", {"dias": "999999999"})
    nul_q = c_adm.get("/productos/", {"q": "leche\x00"})
    c4_ok = (
        all(r.status_code == 200 for r in (nul_dias, arabic_dias, plus_dias, over_dias, nul_q))
        and all(r.context["days"] == 30 for r in (nul_dias, arabic_dias, plus_dias, over_dias))
        and "número entero válido" in nul_dias.content.decode()
        and "número entero válido" in arabic_dias.content.decode()
        and "número entero válido" in plus_dias.content.decode()
        and "entre 1 y 3650" in over_dias.content.decode()
        and "carácter no válido" in nul_q.content.decode()
    )
    report["cases"].append({
        "id": "pg_nul_byte_and_extreme_params_safe",
        "ok": c4_ok,
        "checks": {
            "nul_dias_days": nul_dias.context["days"],
            "arabic_dias_days": arabic_dias.context["days"],
            "plus_dias_days": plus_dias.context["days"],
            "over_dias_days": over_dias.context["days"],
            "nul_q_status": nul_q.status_code,
        },
    })

    # ── Case 5: PostgreSQL N+1 invariance & EXPLAIN query plan observation ──
    with CaptureQueriesContext(connection) as q_small_stock:
        assert c_adm.get("/inventario/stock/").status_code == 200
    with CaptureQueriesContext(connection) as q_small_dash:
        assert c_adm.get("/inicio/").status_code == 200

    for idx in range(25):
        p_bulk = Product.objects.create(
            category=cat_tz, name=f"Bulk PG07 {idx:02d}", barcode=f"7750799{idx:05d}",
            sale_price=Decimal("3.00"), minimum_stock=5,
        )
        confirm_initial_load(
            actor=wh1, product=p_bulk, lots=[LotInput(f"BLK-{idx}", 4, Decimal("1.50"), today + timedelta(days=10 + idx))]
        )

    with CaptureQueriesContext(connection) as q_large_stock:
        assert c_adm.get("/inventario/stock/").status_code == 200
    with CaptureQueriesContext(connection) as q_large_dash:
        assert c_adm.get("/inicio/").status_code == 200

    qs_exp = Lot.objects.filter(available_quantity__gt=0, expiration_date__lte=today + timedelta(days=30)).select_related("product__category", "supplier").order_by("expiration_date", "product__name", "received_at", "id")
    sql_exp, params_exp = qs_exp.query.sql_with_params()
    with connection.cursor() as cur:
        cur.execute(f"EXPLAIN (FORMAT JSON) {sql_exp}", params_exp)
        explain_plan = cur.fetchone()[0][0]["Plan"]

    def collect_plan_nodes(node: dict) -> list[dict]:
        info = {"node_type": node.get("Node Type"), "relation": node.get("Relation Name"), "index": node.get("Index Name")}
        out_nodes = [info]
        for child in node.get("Plans", []):
            out_nodes.extend(collect_plan_nodes(child))
        return out_nodes

    c5_ok = len(q_small_stock) == len(q_large_stock) and len(q_small_dash) == len(q_large_dash)
    report["cases"].append({
        "id": "pg_n_plus_1_invariance_and_explain_plan",
        "ok": c5_ok,
        "checks": {
            "stock_queries_before": len(q_small_stock),
            "stock_queries_after_plus25": len(q_large_stock),
            "dash_queries_before": len(q_small_dash),
            "dash_queries_after_plus25": len(q_large_dash),
            "expirations_plan_nodes": collect_plan_nodes(explain_plan),
        },
    })

except Exception as exc:
    import traceback

    report["error"] = {
        "type": type(exc).__name__,
        "message": str(exc).replace(PW, "[REDACTED]")[:800],
        "traceback": traceback.format_exc().replace(PW, "[REDACTED]")[-1500:],
    }
finally:
    if configured:
        connections.close_all()
    if started:
        own()
        pg("pg_ctl", "-D", DBDIR, "-m", "fast", "-w", "stop")
    with socket.socket() as s:
        report["port_closed"] = s.connect_ex(("127.0.0.1", PORT)) != 0
    report["protected_unchanged"] = {str(p.relative_to(ROOT)): state_hash(p) == hashes[str(p.relative_to(ROOT))] for p in protected}
    report["finished_utc"] = datetime.now(dt_timezone.utc).isoformat()
    out = RESULTS / "evidencias" / ("07-postgresql-" + STAMP + ".json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                "evidence": str(out.relative_to(ROOT)),
                "cases": [{"id": c["id"], "ok": c["ok"]} for c in report["cases"]],
                "error": report.get("error"),
                "port_closed": report["port_closed"],
                "protected_unchanged": all(report["protected_unchanged"].values()),
            },
            ensure_ascii=False,
            default=str,
        )
    )

if (
    report.get("error")
    or len(report["cases"]) != 5
    or not all(x["ok"] for x in report["cases"])
    or not report["port_closed"]
    or not all(report["protected_unchanged"].values())
):
    raise SystemExit(1)
