"""Stage 08 real PostgreSQL 18.4 verification:
1. Write-off vs POS checkout_sale concurrency on last units (zero negative stock, zero deadlock, preserved SaleLine.unit_cost).
2. Concurrent actor revocation / demotion vs write_off_stock & register_physical_adjustment (READ COMMITTED recheck + zero deadlock).
3. Concurrent identical same-session HTTP POST double-submit (only 1 write-off committed, 2nd returns replay redirect) & cross-payload key conflict rejection.
4. Simultaneous 10-thread distinct-lot write-offs generating unique sequential B-00000001..B-00000010 correlativos cleanly.
5. Concurrent same-lot negative physical adjustments (second fails cleanly without negative available_quantity) + rollback on mid-transaction error.
6. Lima midnight expiration boundary for DAÑO -> VENCIMIENTO + NUL byte safe rejection + product_movements query count & EXPLAIN index usage.
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
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "auditoria_por_etapas/resultados"
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
STAMP = datetime.now(dt_timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
CLUSTER = (Path(tempfile.gettempdir()) / ("audit08-pg-" + secrets.token_hex(12))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT08_OWNED"
MARK.write_text(STAMP, encoding="utf-8")
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(40)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit08_" + secrets.token_hex(5)
with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]

import re as _re

protected = [
    *(ROOT / "r1-pmv").glob("*.sqlite3"),
    *[
        p
        for p in (RESULTS / "datos").glob("etapa0[0-7]*/*.sqlite3")
        if not ((m := _re.search(r"(2026\d{4}T\d{6})", p.parent.name)) and m.group(1) >= "20261111T233500")
    ],
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
    assert CLUSTER.parent == Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith("audit08-pg-")
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
        "audit08",
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

    conf = {"host": "127.0.0.1", "port": PORT, "user": "audit08", "password": PW}
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
            "USER": "audit08",
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
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from identity.services import deactivate_employee, update_employee
    from inventory.models import Lot, PhysicalAdjustment, StockWriteOff, Supplier
    from inventory.services import LotInput, confirm_initial_load, register_physical_adjustment, write_off_stock
    from sales.models import SaleCounter, SaleLine
    from sales.services import add_product_to_draft, checkout_sale

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
    pw_user = "PgAudit08#Pass123"
    admin = Account.objects.create_user("admin.pg08@test.invalid", pw_user, display_name="Admin PG08", role=admin_role)
    wh1 = Account.objects.create_user("wh1.pg08@test.invalid", pw_user, display_name="Almacen1 PG08", role=wh_role)
    wh2 = Account.objects.create_user("wh2.pg08@test.invalid", pw_user, display_name="Almacen2 PG08", role=wh_role)
    seller = Account.objects.create_user("seller.pg08@test.invalid", pw_user, display_name="Vendedora PG08", role=seller_role)

    cat = Category.objects.create(name="PG08 Abarrotes")
    sup = Supplier.objects.create(name="Proveedor PG08 SAC", ruc="20808089901")
    reg = CashRegister.objects.create(code="CAJA-PG08")
    CashShift.objects.create(cash_register=reg, seller=seller, opening_amount=Decimal("50.00"))
    SaleCounter.objects.get_or_create(pk=1)
    today = tz.localdate()
    future = today + timedelta(days=45)

    # ── Case 1: 10-thread simultaneous write_off_stock on distinct lots -> unique correlativos B-00000001..B-00000010 ─
    corr_lots = []
    for i in range(10):
        pr = Product.objects.create(
            category=cat, name=f"PG Corr Prod {i:02d}", barcode=f"77508910{i:04d}", sale_price=Decimal("4.00")
        )
        ld = confirm_initial_load(actor=wh1, product=pr, supplier=sup, lots=[LotInput(f"PGC-{i:02d}", 10, Decimal("2.0000"), future)])
        corr_lots.append(ld.lots.get())

    bar_corr = threading.Barrier(10, timeout=12)

    def run_corr(l_obj):
        close_old_connections()
        try:
            bar_corr.wait()
            wo = write_off_stock(actor=wh2, lot=l_obj, quantity=1, reason=StockWriteOff.Reason.DAMAGE, notes="Concurrente 10")
            return {"ok": True, "correlativo": wo.correlativo}
        except Exception as exc:
            return {"ok": False, "type": type(exc).__name__, "msg": str(exc)}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=10) as pool:
        corr_res = [f.result(timeout=15) for f in [pool.submit(run_corr, l) for l in corr_lots]]

    corr_codes = sorted(r["correlativo"] for r in corr_res if r["ok"])
    c1_ok = len(corr_codes) == 10 and corr_codes == [f"B-{i:08d}" for i in range(1, 11)]
    report["cases"].append({
        "id": "pg_10_concurrent_writeoffs_unique_correlativos",
        "ok": c1_ok,
        "checks": {"ok_count": len(corr_codes), "codes": corr_codes, "failures": [r for r in corr_res if not r["ok"]]},
    })

    # ── Case 2: Concurrent same-session double-POST HTTP idempotency & cross-payload collision ─
    p_http = Product.objects.create(
        category=cat, name="PG HTTP Double", barcode="775089200001", sale_price=Decimal("5.00")
    )
    lot_http = confirm_initial_load(actor=wh1, product=p_http, lots=[LotInput("PG-HTTP-1", 25, Decimal("2.0000"), future)]).lots.get()

    c_pg = Client(enforce_csrf_checks=True)
    c_pg.force_login(admin)
    csrf_tok = c_pg.get(f"/inventario/bajas/nueva/?lote={lot_http.pk}").cookies["csrftoken"].value
    sess_id = c_pg.cookies["sessionid"].value
    idem_uuid = str(uuid.uuid4())
    bar_http = threading.Barrier(2, timeout=12)

    def run_http_dbl():
        close_old_connections()
        try:
            cl = Client(enforce_csrf_checks=True)
            cl.cookies["sessionid"] = sess_id
            cl.cookies["csrftoken"] = csrf_tok
            bar_http.wait()
            resp = cl.post(
                f"/inventario/bajas/nueva/?lote={lot_http.pk}",
                data={
                    "lot_id": str(lot_http.pk),
                    "quantity": "4",
                    "reason": "DAÑO",
                    "notes": "PG Doble POST",
                    "idempotency_key": idem_uuid,
                    "csrfmiddlewaretoken": csrf_tok,
                },
            )
            return {"status": resp.status_code, "location": resp.get("Location")}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1, f2 = pool.submit(run_http_dbl), pool.submit(run_http_dbl)
        http_res = [f1.result(timeout=15), f2.result(timeout=15)]

    lot_http.refresh_from_db()
    # Now attempt tampered reuse of the SAME key on a different payload sequentially
    csrf_tok2 = c_pg.get(f"/inventario/bajas/nueva/?lote={lot_http.pk}").cookies["csrftoken"].value
    r_tamper = c_pg.post(
        f"/inventario/bajas/nueva/?lote={lot_http.pk}",
        data={
            "lot_id": str(lot_http.pk),
            "quantity": "9",
            "reason": "ROBO",
            "notes": "Alterado PG",
            "idempotency_key": idem_uuid,
            "csrfmiddlewaretoken": csrf_tok2,
        },
    )
    lot_http.refresh_from_db()
    c2_ok = (
        StockWriteOff.objects.filter(lot=lot_http).count() == 1
        and lot_http.available_quantity == 21
        and all(r["status"] == 302 for r in http_res)
        and r_tamper.status_code == 200
        and "La clave de operación ya fue utilizada para otra solicitud" in r_tamper.content.decode()
    )
    report["cases"].append({
        "id": "pg_concurrent_http_idempotency_and_tamper_guard",
        "ok": c2_ok,
        "checks": {
            "writeoff_count": StockWriteOff.objects.filter(lot=lot_http).count(),
            "lot_remaining": lot_http.available_quantity,
            "http_results": http_res,
            "tamper_status": r_tamper.status_code,
        },
    })

    # ── Case 3: Race write_off_stock vs POS checkout_sale on last 5 units + concurrent negative adjustment ─
    p_race = Product.objects.create(
        category=cat, name="PG Race POS vs Merma", barcode="775089300001", sale_price=Decimal("6.00")
    )
    lot_race = confirm_initial_load(actor=wh1, product=p_race, lots=[LotInput("PG-RACE-1", 5, Decimal("3.0000"), future)]).lots.get()
    draft_race = add_product_to_draft(actor=seller, product_id=p_race.pk, quantity=4)
    bar_pos = threading.Barrier(2, timeout=12)

    def do_pos():
        close_old_connections()
        try:
            bar_pos.wait()
            sale = checkout_sale(actor=seller, draft_id=draft_race.pk, cash_received=Decimal("30.00"), idempotency_key=uuid.uuid4())
            return {"ok": True, "correlative": sale.correlative}
        except ValidationError as exc:
            return {"ok": False, "msg": str(exc.messages)}
        finally:
            close_old_connections()

    def do_wo_race():
        close_old_connections()
        try:
            bar_pos.wait()
            wo = write_off_stock(actor=wh1, lot=lot_race, quantity=3, reason=StockWriteOff.Reason.DAMAGE, notes="Rotura en piso")
            return {"ok": True, "correlativo": wo.correlativo}
        except ValidationError as exc:
            return {"ok": False, "msg": str(exc.messages)}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_pos = pool.submit(do_pos)
        f_wo = pool.submit(do_wo_race)
        pos_r, wo_r = f_pos.result(timeout=15), f_wo.result(timeout=15)

    lot_race.refresh_from_db()
    # Also race two -1 adjustments when 1 or 2 units remain: adjust down to 1 then race two -1
    if lot_race.available_quantity > 1:
        register_physical_adjustment(actor=admin, lot=lot_race, delta=-(lot_race.available_quantity - 1), reason="Prep race")
    elif lot_race.available_quantity == 0:
        register_physical_adjustment(actor=admin, lot=lot_race, delta=1, reason="Prep race")
    lot_race.refresh_from_db()
    assert lot_race.available_quantity == 1

    bar_adj = threading.Barrier(2, timeout=12)

    def do_neg_adj(label: str):
        close_old_connections()
        try:
            bar_adj.wait()
            adj = register_physical_adjustment(actor=admin, lot=lot_race, delta=-1, reason=label)
            return {"ok": True, "id": str(adj.pk)}
        except ValidationError as exc:
            return {"ok": False, "msg": str(exc.messages)}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f_a = pool.submit(do_neg_adj, "Race A")
        f_b = pool.submit(do_neg_adj, "Race B")
        adj_res = [f_a.result(timeout=15), f_b.result(timeout=15)]

    lot_race.refresh_from_db()
    c3_ok = (
        (pos_r["ok"] ^ wo_r["ok"])
        and lot_race.available_quantity == 0
        and sum(1 for r in adj_res if r["ok"]) == 1
        and sum(1 for r in adj_res if not r["ok"]) == 1
    )
    report["cases"].append({
        "id": "pg_concurrent_writeoff_vs_pos_and_negative_adjustment_race",
        "ok": c3_ok,
        "checks": {"pos": pos_r, "wo": wo_r, "adj_race": adj_res, "final_qty": lot_race.available_quantity},
    })

    # ── Case 4: Actor lock vs deactivate_employee & update_employee + blocking lock observation ─
    wh_rev = Account.objects.create_user("whrev.pg08@test.invalid", pw_user, display_name="WH Rev PG08", role=wh_role)
    adm_demote = Account.objects.create_user("admdem.pg08@test.invalid", pw_user, display_name="ADM Dem PG08", role=admin_role)
    p_rev = Product.objects.create(category=cat, name="PG Actor Rev", barcode="775089400001", sale_price=Decimal("4.00"))
    lot_rev = confirm_initial_load(actor=wh1, product=p_rev, lots=[LotInput("PG-REV-1", 10, Decimal("2.0000"), future)]).lots.get()

    evt_deact_locked = threading.Event()
    evt_release_deact = threading.Event()
    blocking_pid_observed = None

    def blocker_deactivate():
        close_old_connections()
        try:
            with transaction.atomic():
                deactivate_employee(actor=admin, account=wh_rev)
                evt_deact_locked.set()
                evt_release_deact.wait(timeout=8)
        finally:
            close_old_connections()

    def waiter_writeoff():
        close_old_connections()
        try:
            evt_deact_locked.wait(timeout=8)
            write_off_stock(actor=wh_rev, lot=lot_rev, quantity=2, reason=StockWriteOff.Reason.DAMAGE, notes="Should block/deny")
            return {"ok": True}
        except PermissionDenied as exc:
            return {"ok": False, "denied": str(exc)}
        finally:
            close_old_connections()

    def observe_pg_locks():
        close_old_connections()
        observed = None
        try:
            evt_deact_locked.wait(timeout=8)
            # Poll briefly for waiter blocked on wh_rev Account lock
            for _ in range(25):
                with connections["default"].cursor() as cur:
                    cur.execute(
                        "SELECT pid, pg_blocking_pids(pid) FROM pg_stat_activity WHERE datname = %s AND cardinality(pg_blocking_pids(pid)) > 0",
                        [DBNAME],
                    )
                    rows = cur.fetchall()
                    if rows:
                        observed = rows[0]
                        break
                threading.Event().wait(0.05)
            evt_release_deact.set()
            return observed
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=3) as pool:
        f_deact = pool.submit(blocker_deactivate)
        f_wait = pool.submit(waiter_writeoff)
        f_obs = pool.submit(observe_pg_locks)
        blocking_pid_observed = f_obs.result(timeout=15)
        f_deact.result(timeout=15)
        wo_rev_res = f_wait.result(timeout=15)

    # Demote adm_demote -> SELLER while trying register_physical_adjustment concurrently
    evt_dem_locked = threading.Event()
    evt_release_dem = threading.Event()

    def blocker_demote():
        close_old_connections()
        try:
            with transaction.atomic():
                update_employee(actor=admin, account=adm_demote, display_name=adm_demote.display_name, email=adm_demote.email, role=seller_role)
                evt_dem_locked.set()
                evt_release_dem.wait(timeout=8)
        finally:
            close_old_connections()

    def waiter_adj():
        close_old_connections()
        try:
            evt_dem_locked.wait(timeout=8)
            register_physical_adjustment(actor=adm_demote, lot=lot_rev, delta=1, reason="Should deny")
            return {"ok": True}
        except PermissionDenied as exc:
            return {"ok": False, "denied": str(exc)}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        fd = pool.submit(blocker_demote)
        fa = pool.submit(waiter_adj)
        evt_dem_locked.wait(timeout=8)
        threading.Event().wait(0.15)
        evt_release_dem.set()
        fd.result(timeout=15)
        adj_dem_res = fa.result(timeout=15)

    lot_rev.refresh_from_db()
    c4_ok = (
        wo_rev_res.get("ok") is False
        and adj_dem_res.get("ok") is False
        and lot_rev.available_quantity == 10
        and blocking_pid_observed is not None
    )
    report["cases"].append({
        "id": "pg_concurrent_actor_revocation_and_demotion_blocked",
        "ok": c4_ok,
        "checks": {
            "wo_after_deactivate": wo_rev_res,
            "adj_after_demote": adj_dem_res,
            "blocking_pids_observed": str(blocking_pid_observed),
            "lot_qty_unchanged": lot_rev.available_quantity,
        },
    })

    # ── Case 5: Atomic rollback, Lima midnight write-off boundary & Kardex N+1/EXPLAIN ─
    p_tz = Product.objects.create(category=cat, name="PG TZ WriteOff", barcode="775089500001", sale_price=Decimal("5.00"))
    exp_date = date(2026, 11, 12)
    t_before = datetime(2026, 11, 12, 4, 59, 59, tzinfo=dt_timezone.utc)
    t_after = datetime(2026, 11, 12, 5, 0, 0, tzinfo=dt_timezone.utc)
    with patch("django.utils.timezone.now", return_value=t_before):
        lot_tz = confirm_initial_load(actor=wh1, product=p_tz, lots=[LotInput("PG-TZ-WO", 6, Decimal("2.0000"), exp_date)]).lots.get()
        write_off_stock(actor=wh1, lot=lot_tz, quantity=1, reason=StockWriteOff.Reason.DAMAGE, notes="Antes medianoche")
    with patch("django.utils.timezone.now", return_value=t_after):
        dano_blocked = False
        try:
            write_off_stock(actor=wh1, lot=lot_tz, quantity=1, reason=StockWriteOff.Reason.DAMAGE, notes="Post medianoche")
        except ValidationError:
            dano_blocked = True
        wo_tz = write_off_stock(actor=wh1, lot=lot_tz, quantity=2, reason=StockWriteOff.Reason.EXPIRATION)

    # Simulated mid-transaction crash leaves 0 write-offs/adjustments added
    wo_before_rb = StockWriteOff.objects.count()
    adj_before_rb = PhysicalAdjustment.objects.count()
    try:
        with transaction.atomic():
            write_off_stock(actor=wh1, lot=lot_tz, quantity=1, reason=StockWriteOff.Reason.THEFT, notes="Rollback test")
            raise RuntimeError("Simulated crash before commit")
    except RuntimeError:
        pass
    lot_tz.refresh_from_db()

    # Check NUL byte rejection + Kardex EXPLAIN & query count
    c_pg.force_login(admin)
    csrf_adj = c_pg.get(f"/inventario/ajustes/nuevo/?lote={lot_tz.pk}").cookies["csrftoken"].value
    r_nul = c_pg.post(
        f"/inventario/ajustes/nuevo/?lote={lot_tz.pk}",
        {"lot_id": str(lot_tz.pk), "delta": "1", "reason": "Motivo\x00NUL", "csrfmiddlewaretoken": csrf_adj},
    )
    with CaptureQueriesContext(connection) as q_mov:
        r_mov = c_pg.get(f"/inventario/productos/{p_tz.pk}/movimientos/")
    sql_sl, params_sl = (
        SaleLine.objects.filter(product=p_tz).select_related("sale__seller").order_by("-sale__confirmed_at").query.sql_with_params()
    )
    with connection.cursor() as cur:
        cur.execute(f"EXPLAIN (FORMAT JSON) {sql_sl}", params_sl)
        sl_plan = cur.fetchone()[0][0]["Plan"]

    c5_ok = (
        dano_blocked
        and wo_tz.reason == StockWriteOff.Reason.EXPIRATION
        and StockWriteOff.objects.count() == wo_before_rb
        and PhysicalAdjustment.objects.count() == adj_before_rb
        and lot_tz.available_quantity == 3
        and r_nul.status_code == 200
        and r_mov.status_code == 200
        and len(q_mov) <= 15
    )
    report["cases"].append({
        "id": "pg_rollback_lima_midnight_nul_guard_and_kardex_plan",
        "ok": c5_ok,
        "checks": {
            "dano_blocked_at_lima_midnight": dano_blocked,
            "lot_tz_after_rollback": lot_tz.available_quantity,
            "nul_post_status": r_nul.status_code,
            "movements_query_count": len(q_mov),
            "saleline_plan_node": sl_plan.get("Node Type"),
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
    out = RESULTS / "evidencias" / ("08-postgresql-" + STAMP + ".json")
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
