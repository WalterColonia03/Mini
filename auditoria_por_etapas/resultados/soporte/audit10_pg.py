"""Stage 10 real PostgreSQL 18.4 verification: Lima timezone midnight boundary for sellable stock/drafts,
--locale=C Unicode/whitespace/NUL/& search parity, concurrent add stock bounds (no oversell),
concurrent update vs discard and close_cash_shift (RN-30), Account row lock with pg_blocking_pids,
concurrent catalog price/category toggles vs draft edits (zero deadlocks), N+1 query invariance,
and EXPLAIN (FORMAT JSON) plan analysis on _search_products.
Runs in an ephemeral owned cluster (AUDIT10_OWNED) and never alters existing SQLite DBs.
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
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "auditoria_por_etapas/resultados"
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
STAMP = datetime.now(dt_timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
CLUSTER = (Path(tempfile.gettempdir()) / ("audit10-pg-" + secrets.token_hex(12))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT10_OWNED"
MARK.write_text(STAMP, encoding="utf-8")
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(40)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit10_" + secrets.token_hex(5)
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
    assert CLUSTER.parent == Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith("audit10-pg-")
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


def collect_plan_nodes(node: dict) -> list[dict]:
    info = {
        "node_type": node.get("Node Type"),
        "relation": node.get("Relation Name"),
        "index": node.get("Index Name"),
    }
    out_nodes = [info]
    for child in node.get("Plans", []):
        out_nodes.extend(collect_plan_nodes(child))
    return out_nodes


started = False
configured = False
try:
    own()
    pg(
        "initdb",
        "-D",
        DBDIR,
        "-U",
        "audit10",
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

    conf = {"host": "127.0.0.1", "port": PORT, "user": "audit10", "password": PW}
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
            "USER": "audit10",
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

    from django.core.exceptions import PermissionDenied, ValidationError
    from django.core.management import call_command
    from django.db import close_old_connections, connection, connections, transaction
    from django.test import Client
    from django.test.utils import CaptureQueriesContext, setup_test_environment
    from django.utils import timezone as tz

    setup_test_environment()

    from cash.models import CashRegister, CashShift
    from cash.services import close_cash_shift, open_cash_shift
    from catalog.models import Category, Product
    from catalog.services import toggle_category_status, update_product
    from identity.models import Account, Role
    from inventory.models import Lot
    from inventory.services import LotInput, confirm_initial_load
    from sales.models import SaleDraft, SaleDraftLine
    from sales.services import (
        add_product_to_draft,
        discard_active_draft,
        sellable_stock_for_product,
        update_draft_line,
    )
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
    pw_user = "PgAudit10#Pass123"
    admin = Account.objects.create_user("admin.pg10@test.invalid", pw_user, display_name="Admin PG10", role=admin_role)
    wh = Account.objects.create_user("wh.pg10@test.invalid", pw_user, display_name="Almacen PG10", role=wh_role)
    seller = Account.objects.create_user("seller.pg10@test.invalid", pw_user, display_name="Vendedor PG10", role=seller_role)
    seller2 = Account.objects.create_user("seller2.pg10@test.invalid", pw_user, display_name="Vendedor2 PG10", role=seller_role)

    cat_active = Category.objects.create(name="Conservas PG10")
    cat_toggle = Category.objects.create(name="Bebidas Toggle PG10")
    CashRegister.objects.create(code="CAJA-01")

    # ── Case 1: Lima midnight boundary for sellable stock, _search_products, add/update draft ──
    shift_tz = open_cash_shift(actor=seller, opening_amount=Decimal("40.00"))
    p_tz = Product.objects.create(
        category=cat_active, name="Leche Medianoche PG10", barcode="775100000010", sale_price=Decimal("6.00"), minimum_stock=2
    )
    t_before_mid = datetime(2026, 11, 12, 4, 59, 59, tzinfo=dt_timezone.utc)  # 2026-11-11 23:59:59 Lima
    t_at_mid = datetime(2026, 11, 12, 5, 0, 0, tzinfo=dt_timezone.utc)        # 2026-11-12 00:00:00 Lima
    with patch("django.utils.timezone.now", return_value=t_before_mid):
        confirm_initial_load(actor=wh, product=p_tz, lots=[LotInput("PG10-MID", 5, Decimal("2.50"), date(2026, 11, 12))])
        s_before = sellable_stock_for_product(p_tz)
        q_before = list(_search_products("Medianoche PG10"))
        draft_tz = add_product_to_draft(actor=seller, product_id=p_tz.pk, quantity=2)
        line_tz = draft_tz.lines.get()
    with patch("django.utils.timezone.now", return_value=t_at_mid):
        s_after = sellable_stock_for_product(p_tz)
        q_after = list(_search_products("Medianoche PG10"))
        add_expired_err = None
        upd_expired_err = None
        try:
            add_product_to_draft(actor=seller, product_id=p_tz.pk, quantity=1)
        except ValidationError as err:
            add_expired_err = err.messages[0]
        try:
            update_draft_line(actor=seller, line_id=line_tz.pk, quantity=3)
        except ValidationError as err:
            upd_expired_err = err.messages[0]
        discard_active_draft(actor=seller)

    lot_tz_qty = Lot.objects.get(product=p_tz).available_quantity
    Lot.objects.filter(product=p_tz).update(available_quantity=0)
    c1_ok = (
        s_before == 5
        and len(q_before) == 1
        and q_before[0].sellable_quantity == 5
        and s_after == 0
        and len(q_after) == 0
        and add_expired_err is not None
        and upd_expired_err is not None
        and lot_tz_qty == 5
    )
    report["cases"].append({
        "id": "pg_timezone_lima_midnight_draft_boundary",
        "ok": c1_ok,
        "checks": {
            "before_stock": s_before,
            "after_stock": s_after,
            "add_expired_err": add_expired_err,
            "upd_expired_err": upd_expired_err,
            "lot_untouched": lot_tz_qty,
        },
    })

    # ── Case 2: --locale=C Unicode accent/whitespace, multi-GTIN, leading zero internal, NUL, and & redirect ──
    today = tz.localdate()
    p_gtin = Product.objects.create(
        category=cat_active, name="Atún en Lata PG10", barcode="0775000000014",
        barcode_type=Product.BarcodeType.GTIN, sale_price=Decimal("5.90"), minimum_stock=2,
    )
    l_gtin = confirm_initial_load(
        actor=wh, product=p_gtin,
        lots=[
            LotInput("PG10-VIG1", 4, Decimal("2.00"), today + timedelta(days=5)),
            LotInput("PG10-VIG2", 2, Decimal("2.00"), today + timedelta(days=20)),
            LotInput("PG10-EXP", 5, Decimal("2.00"), today + timedelta(days=5)),
        ],
    )
    Lot.objects.filter(product=p_gtin, number_normalized="PG10-EXP").update(expiration_date=today)

    p_amp = Product.objects.create(
        category=cat_toggle, name="Café & Pan PG10", barcode="00PG10-INT",
        barcode_type=Product.BarcodeType.INTERNAL, sale_price=Decimal("10.00"), minimum_stock=2,
    )
    confirm_initial_load(
        actor=wh, product=p_amp,
        lots=[LotInput("PG10-AMP", 8, Decimal("4.00"), today + timedelta(days=25))],
    )

    c_seller = Client()
    c_seller.force_login(seller)
    r_accent = c_seller.get("/ventas/", {"query": "  ATÚN   EN   LATA  "})
    r_upc12 = c_seller.get("/ventas/", {"query": "775000000014"})
    r_gtin14 = c_seller.get("/ventas/", {"query": "00775000000014"})
    r_int_ok = c_seller.get("/ventas/", {"query": "00PG10-INT"})
    r_int_no = c_seller.get("/ventas/", {"query": "PG10-INT"})
    r_nul = c_seller.get("/ventas/", {"query": "atun\x00"})
    r_over = c_seller.get("/ventas/", {"query": "X" * 161})
    r_amp_post = c_seller.post("/ventas/?query=Caf%C3%A9%20%26%20Pan", {"product_id": str(p_amp.pk), "quantity": "1"})

    p_accent = list(r_accent.context["products"])
    p_u12 = list(r_upc12.context["products"])
    p_g14 = list(r_gtin14.context["products"])
    c2_ok = (
        len(p_accent) == 1 and p_accent[0].sellable_quantity == 6
        and len(p_u12) == 1 and p_u12[0].sellable_quantity == 6
        and len(p_g14) == 1 and p_g14[0].sellable_quantity == 6
        and len(list(r_int_ok.context["products"])) == 1
        and len(list(r_int_no.context["products"])) == 0
        and r_nul.status_code == 200 and r_nul.context["search_form"].errors
        and r_over.status_code == 200 and r_over.context["search_form"].errors
        and r_amp_post.status_code == 302 and r_amp_post["Location"] == "/ventas/?query=Caf%C3%A9+%26+Pan"
    )
    discard_active_draft(actor=seller)
    report["cases"].append({
        "id": "pg_locale_c_unicode_gtin_nul_and_amp_search",
        "ok": c2_ok,
        "checks": {
            "accent_qty": p_accent[0].sellable_quantity if p_accent else None,
            "nul_status": r_nul.status_code,
            "amp_redirect": r_amp_post.get("Location"),
        },
    })

    # ── Case 3: Concurrent two-thread add_product_to_draft racing on stock bound (4 + 4 vs 6) ──
    add_barrier = threading.Barrier(2)

    def try_add_4():
        close_old_connections()
        try:
            add_barrier.wait(timeout=8)
            add_product_to_draft(actor=seller, product_id=p_gtin.pk, quantity=4)
            return "ok"
        except Exception as exc:
            return type(exc).__name__
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(try_add_4)
        f2 = pool.submit(try_add_4)
        res_add = sorted([f1.result(timeout=12), f2.result(timeout=12)])

    active_drafts_c3 = SaleDraft.objects.filter(cash_shift=shift_tz, status=SaleDraft.Status.ACTIVE)
    line_qty_c3 = active_drafts_c3.get().lines.get().quantity if active_drafts_c3.count() == 1 else -1
    lots_gtin_after = list(Lot.objects.filter(product=p_gtin).order_by("id").values_list("available_quantity", flat=True))
    c3_ok = res_add == ["ValidationError", "ok"] and active_drafts_c3.count() == 1 and line_qty_c3 == 4 and sum(lots_gtin_after) == 11
    report["cases"].append({
        "id": "pg_concurrent_add_stock_cap_no_oversell",
        "ok": c3_ok,
        "checks": {"outcomes": res_add, "drafts": active_drafts_c3.count(), "line_qty": line_qty_c3},
    })

    # ── Case 4: Concurrent update_draft_line vs discard_active_draft AND add vs close_cash_shift (RN-30) ──
    line_c4 = active_drafts_c3.get().lines.get()
    b_upd_disc = threading.Barrier(2)

    def worker_upd():
        close_old_connections()
        try:
            b_upd_disc.wait(timeout=8)
            update_draft_line(actor=seller, line_id=line_c4.pk, quantity=5)
            return "updated"
        except Exception as exc:
            return type(exc).__name__
        finally:
            close_old_connections()

    def worker_disc():
        close_old_connections()
        try:
            b_upd_disc.wait(timeout=8)
            return "discarded" if discard_active_draft(actor=seller) else "noop"
        except Exception as exc:
            return type(exc).__name__
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        fu = pool.submit(worker_upd)
        fd = pool.submit(worker_disc)
        r_upd, r_disc = fu.result(timeout=12), fd.result(timeout=12)

    if SaleDraft.objects.filter(cash_shift=shift_tz, status=SaleDraft.Status.ACTIVE).exists():
        discard_active_draft(actor=seller)  # only possible? Actually discard MUST either win or serialize after update and discard!
    lines_remaining_4a = SaleDraftLine.objects.filter(draft__cash_shift=shift_tz).count()
    c4a_ok = r_disc == "discarded" and r_upd in ("updated", "ValidationError") and lines_remaining_4a == 0

    # Subcase 4b: add vs close_cash_shift on shift_tz (RN-30)
    b_add_close = threading.Barrier(2)

    def worker_add():
        close_old_connections()
        try:
            b_add_close.wait(timeout=8)
            add_product_to_draft(actor=seller, product_id=p_gtin.pk, quantity=1)
            return "added"
        except Exception as exc:
            return type(exc).__name__
        finally:
            close_old_connections()

    def worker_close():
        close_old_connections()
        try:
            b_add_close.wait(timeout=8)
            close_cash_shift(actor=seller, counted_amount=Decimal("40.00"))
            return "closed"
        except Exception as exc:
            return type(exc).__name__
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        fa = pool.submit(worker_add)
        fc = pool.submit(worker_close)
        r_add4b, r_close4b = fa.result(timeout=12), fc.result(timeout=12)

    shift_tz.refresh_from_db()
    has_active_4b = SaleDraft.objects.filter(cash_shift=shift_tz, status=SaleDraft.Status.ACTIVE).exists()
    c4b_ok = (
        (r_add4b == "added" and r_close4b == "ValidationError" and shift_tz.status == CashShift.Status.OPEN and has_active_4b)
        or (r_close4b == "closed" and r_add4b == "ValidationError" and shift_tz.status == CashShift.Status.CLOSED and not has_active_4b)
    )
    if shift_tz.status == CashShift.Status.OPEN:
        discard_active_draft(actor=seller)
        close_cash_shift(actor=seller, counted_amount=Decimal("40.00"))
    report["cases"].append({
        "id": "pg_concurrent_update_vs_discard_and_rn30_close",
        "ok": c4a_ok and c4b_ok,
        "checks": {
            "upd_vs_disc": [r_upd, r_disc, lines_remaining_4a],
            "add_vs_close": [r_add4b, r_close4b, shift_tz.status, has_active_4b],
        },
    })

    # ── Case 5: Account row lock (pg_blocking_pids) & seller deactivation race ──
    shift_s2 = open_cash_shift(actor=seller2, opening_amount=Decimal("25.00"))
    holder_ready = threading.Event()
    holder_release = threading.Event()
    holder_pid_box: list[int] = []

    def deactivate_holder():
        close_old_connections()
        try:
            with transaction.atomic():
                with connection.cursor() as cur:
                    cur.execute("SELECT pg_backend_pid()")
                    holder_pid_box.append(cur.fetchone()[0])
                locked = Account.objects.select_for_update().get(pk=seller2.pk)
                holder_ready.set()
                holder_release.wait(timeout=8)
                locked.is_active = False
                locked.save(update_fields=["is_active"])
                return "deactivated"
        finally:
            close_old_connections()

    def blocked_add():
        close_old_connections()
        try:
            holder_ready.wait(timeout=8)
            add_product_to_draft(actor=seller2, product_id=p_gtin.pk, quantity=1)
            return "unexpected_ok"
        except Exception as exc:
            return type(exc).__name__
        finally:
            close_old_connections()

    blocking_observed = False
    blocking_details = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        fh = pool.submit(deactivate_holder)
        assert holder_ready.wait(timeout=8)
        fa2 = pool.submit(blocked_add)
        h_pid = holder_pid_box[0]
        with psycopg.connect(**conf, dbname=DBNAME, autocommit=True) as mon:
            for _ in range(30):
                rows = mon.execute(
                    """
                    SELECT pid, wait_event_type, wait_event, pg_blocking_pids(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s AND %s = ANY(pg_blocking_pids(pid))
                    """,
                    (DBNAME, h_pid),
                ).fetchall()
                if rows:
                    blocking_observed = True
                    blocking_details = [[r[0], r[1], r[2], list(r[3])] for r in rows]
                    break
                time.sleep(0.025)
        holder_release.set()
        h_res = fh.result(timeout=10)
        a2_res = fa2.result(timeout=10)

    c5_ok = (
        h_res == "deactivated"
        and blocking_observed
        and a2_res == "PermissionDenied"
        and not SaleDraft.objects.filter(cash_shift=shift_s2).exists()
    )
    report["cases"].append({
        "id": "pg_actor_lock_and_deactivation_blocking_pids",
        "ok": c5_ok,
        "checks": {
            "holder": h_res,
            "blocked_outcome": a2_res,
            "blocking_observed": blocking_observed,
            "blocking_details": blocking_details,
        },
    })

    # ── Case 6: Concurrent catalog price edit & category toggle vs draft edits (zero deadlocks) ──
    seller2.is_active = True
    seller2.save(update_fields=["is_active"])
    close_cash_shift(actor=seller2, counted_amount=Decimal("25.00"))
    shift_tz = open_cash_shift(actor=seller, opening_amount=Decimal("40.00"))
    draft_c6 = add_product_to_draft(actor=seller, product_id=p_amp.pk, quantity=1)
    line_c6 = draft_c6.lines.get()
    b_cat_draft = threading.Barrier(2)

    def admin_edit_amp():
        close_old_connections()
        try:
            b_cat_draft.wait(timeout=8)
            update_product(
                actor=admin, product=p_amp, name=p_amp.name, barcode=p_amp.barcode,
                sale_price=Decimal("13.50"), minimum_stock=p_amp.minimum_stock, category=p_amp.category,
            )
            toggle_category_status(actor=admin, category=cat_toggle, is_active=False)
            return "catalog_done"
        except Exception as exc:
            return f"{type(exc).__name__}:{exc}"
        finally:
            close_old_connections()

    def seller_edit_amp():
        close_old_connections()
        try:
            b_cat_draft.wait(timeout=8)
            update_draft_line(actor=seller, line_id=line_c6.pk, quantity=3)
            return "draft_updated"
        except ValidationError:
            return "ValidationError"
        except Exception as exc:
            return f"{type(exc).__name__}:{exc}"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_cat = pool.submit(admin_edit_amp)
        f_drf = pool.submit(seller_edit_amp)
        r_cat, r_drf = f_cat.result(timeout=12), f_drf.result(timeout=12)

    toggle_category_status(actor=admin, category=cat_toggle, is_active=True)
    discard_active_draft(actor=seller)
    c6_ok = r_cat == "catalog_done" and r_drf in ("draft_updated", "ValidationError")
    report["cases"].append({
        "id": "pg_concurrent_catalog_price_category_vs_draft_no_deadlock",
        "ok": c6_ok,
        "checks": {"catalog": r_cat, "draft": r_drf},
    })

    # ── Case 7: N+1 query invariance & EXPLAIN (FORMAT JSON) on _search_products ──
    with CaptureQueriesContext(connection) as q_before:
        assert c_seller.get("/ventas/", {"query": "Atún"}).status_code == 200

    for idx in range(25):
        p_bulk = Product.objects.create(
            category=cat_active, name=f"Conserva Bulk PG10 {idx:02d}", barcode=f"7751099{idx:05d}",
            sale_price=Decimal("4.20"), minimum_stock=2,
        )
        confirm_initial_load(
            actor=wh, product=p_bulk,
            lots=[
                LotInput(f"B10-A-{idx}", 3, Decimal("2.00"), today + timedelta(days=5 + idx)),
                LotInput(f"B10-B-{idx}", 4, Decimal("2.00"), today + timedelta(days=15 + idx)),
            ],
        )

    with CaptureQueriesContext(connection) as q_after:
        r_bulk = c_seller.get("/ventas/", {"query": "Conserva Bulk PG10"})
        assert r_bulk.status_code == 200
        assert len(list(r_bulk.context["products"])) == 25

    qs_search = _search_products("Conserva Bulk PG10")
    sql_s, params_s = qs_search.query.sql_with_params()
    with connection.cursor() as cur:
        cur.execute(f"EXPLAIN (FORMAT JSON) {sql_s}", params_s)
        explain_search = cur.fetchone()[0][0]["Plan"]

    c7_ok = len(q_before) == len(q_after)
    report["cases"].append({
        "id": "pg_n_plus_1_invariance_and_explain_search",
        "ok": c7_ok,
        "checks": {
            "queries_before": len(q_before),
            "queries_after_plus25_50lots": len(q_after),
            "search_plan_nodes": collect_plan_nodes(explain_search),
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
    if started and report["port_closed"]:
        shutil.rmtree(CLUSTER, ignore_errors=True)
    report["cluster_removed"] = not CLUSTER.exists()
    report["protected_unchanged"] = {str(p.relative_to(ROOT)): state_hash(p) == hashes[str(p.relative_to(ROOT))] for p in protected}
    own_prefixes = (
        "r1-pmv\\",
        "r1-pmv/",
        "PLANIFICACION_SCRUM_R1PMV.xlsx",
        "auditoria_por_etapas\\resultados\\datos\\etapa00",
        "auditoria_por_etapas\\resultados\\datos\\etapa01",
        "auditoria_por_etapas\\resultados\\datos\\etapa02",
        "auditoria_por_etapas\\resultados\\datos\\etapa03",
        "auditoria_por_etapas\\resultados\\datos\\etapa04",
        "auditoria_por_etapas\\resultados\\datos\\etapa05",
        "auditoria_por_etapas\\resultados\\datos\\etapa06",
        "auditoria_por_etapas\\resultados\\datos\\etapa07",
        "auditoria_por_etapas\\resultados\\datos\\etapa10",
    )
    report["own_and_operational_unchanged"] = all(
        ok for k, ok in report["protected_unchanged"].items() if k.startswith(own_prefixes)
    )
    report["finished_utc"] = datetime.now(dt_timezone.utc).isoformat()
    out = RESULTS / "evidencias" / ("10-postgresql-" + STAMP + ".json")
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                "evidence": str(out.relative_to(ROOT)),
                "cases": [{"id": c["id"], "ok": c["ok"]} for c in report["cases"]],
                "error": report.get("error"),
                "port_closed": report["port_closed"],
                "cluster_removed": report["cluster_removed"],
                "own_and_operational_unchanged": report["own_and_operational_unchanged"],
                "protected_unchanged": all(report["protected_unchanged"].values()),
            },
            ensure_ascii=False,
            default=str,
        )
    )

if (
    report.get("error")
    or len(report["cases"]) != 7
    or not all(x["ok"] for x in report["cases"])
    or not report["port_closed"]
    or not report["own_and_operational_unchanged"]
):
    raise SystemExit(1)
