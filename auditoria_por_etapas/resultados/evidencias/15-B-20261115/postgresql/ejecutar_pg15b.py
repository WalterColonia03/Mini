"""Stage 15 (15-B) PostgreSQL 18.4 Concurrency, Correlatives & Deadlock Avoidance Suite.

Fills the concurrency gaps left between 15-A and the full Stage 15 mandate:
mermas, ajustes fisicos, mermas/ajustes vs checkout_sale, write-off/receipt/sale correlatives,
and cross-module anti-deadlock checks on an isolated ephemeral PostgreSQL 18.4 cluster.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import contextlib
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "r1-pmv/manage.py").exists())
HERE.mkdir(parents=True, exist_ok=True)
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
STAMP = datetime.now(dt_timezone.utc).isoformat()

CLUSTER = (Path(tempfile.gettempdir()) / ("audit15b-pg-" + secrets.token_hex(10))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT15B_OWNED"
MARK.write_text(STAMP, encoding="utf-8")
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(40)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit15b_" + secrets.token_hex(5)

with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_build() -> dict:
    names = (
        subprocess.check_output(
            ["git", "-C", str(ROOT / "r1-pmv"), "ls-files", "-co", "--exclude-standard", "-z"]
        )
        .decode()
        .split("\0")
    )
    files = {
        n: digest((ROOT / "r1-pmv" / n).read_bytes())
        for n in sorted(set(names))
        if n
        and not n.startswith("evidencias/")
        and Path(n).suffix in {".py", ".html", ".css", ".js", ".svg", ".ps1", ".sh"}
    }
    return {
        "count": len(files),
        "sha256": digest(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()),
    }


def own() -> None:
    assert CLUSTER.parent == Path(tempfile.gettempdir()).resolve()
    assert CLUSTER.name.startswith("audit15b-pg-")
    assert MARK.read_text(encoding="utf-8") == STAMP


def pg(name: str, *args, env_extra: dict | None = None) -> str:
    own()
    run_env = os.environ.copy()
    if env_extra:
        run_env.update(env_extra)
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as f:
        r = subprocess.run(
            [str(BIN / (name + ".exe")), *map(str, args)],
            stdout=f,
            stderr=f,
            env=run_env,
            timeout=90,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        f.seek(0)
        text = f.read().replace(PW, "[REDACTED]")
    if r.returncode:
        raise RuntimeError(f"{name} failed ({r.returncode}): {text[-1200:]}")
    return text


report: dict = {
    "started_utc": STAMP,
    "etapa": "ETAPA-15",
    "sublote": "15-B-PG",
    "pasada": 1,
    "cursor_entrada": "15-SEGURIDAD-CORRECCIONES-PENDIENTES",
    "cluster": str(CLUSTER),
    "database": DBNAME,
    "port": PORT,
    "plan08_sha256": digest((ROOT / "08_Historias_de_Usuario.md").read_bytes()),
    "head": subprocess.check_output(["git", "-C", str(ROOT / "r1-pmv"), "rev-parse", "HEAD"], text=True).strip(),
    "before_build": compute_build(),
    "cases": [],
}


def save_report(filename: str = "resultados-pg15b.json") -> None:
    (HERE / filename).write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8"
    )


def run_case(case_id: str, fn) -> None:
    t0 = time.monotonic()
    try:
        details = fn() or {}
        report["cases"].append(
            {"id": case_id, "ok": True, "seconds": round(time.monotonic() - t0, 3), **details}
        )
    except Exception as exc:
        report["cases"].append(
            {
                "id": case_id,
                "ok": False,
                "seconds": round(time.monotonic() - t0, 3),
                "error": type(exc).__name__,
                "detail": str(exc).replace(PW, "[REDACTED]"),
                "traceback": traceback.format_exc().replace(PW, "[REDACTED]"),
            }
        )
    save_report("resultados-pg15b-partial.json")
    print(f"[{case_id}] ok={report['cases'][-1]['ok']}", flush=True)


started = False
try:
    pg(
        "initdb",
        "-D",
        DBDIR,
        "-U",
        "audit15b",
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

    pg_conf = {"host": "127.0.0.1", "port": PORT, "user": "audit15b", "password": PW}
    with psycopg.connect(**pg_conf, dbname="postgres", autocommit=True) as conn:
        assert Path(conn.execute("SHOW data_directory").fetchone()[0]).resolve() == DBDIR
        report["postgres_version"] = conn.execute("SELECT version()").fetchone()[0]
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DBNAME)))

    sys.path.insert(0, str(ROOT / "r1-pmv"))
    os.environ.update(
        {
            "APP_ENV": "test",
            "DJANGO_DEBUG": "false",
            "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
            "DJANGO_SETTINGS_MODULE": "config.settings",
            "DJANGO_ALLOWED_HOSTS": "testserver,127.0.0.1,localhost",
        }
    )
    from config import env as config_env

    config_env.load_dotenv = lambda path=None: None
    from django.conf import settings

    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": DBNAME,
            "USER": "audit15b",
            "PASSWORD": PW,
            "HOST": "127.0.0.1",
            "PORT": PORT,
            "CONN_MAX_AGE": 0,
            "OPTIONS": {"options": "-c statement_timeout=30000 -c lock_timeout=15000"},
        }
    }
    import django

    django.setup()
    from django.core.management import call_command
    from django.db import close_old_connections, connection, connections, transaction
    from django.test.utils import setup_test_environment
    from django.utils import timezone as tz

    from cash.models import CashRegister, CashShift
    from cash.services import close_cash_shift, open_cash_shift
    from catalog.models import Category, Product
    from catalog.services import create_category, toggle_category_status, update_product
    from identity.models import Account, Role
    from identity.services import update_employee
    import inventory.services as inv_services
    from inventory.models import Lot, PhysicalAdjustment, StockReceipt, StockWriteOff
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        register_physical_adjustment,
        register_stock_entry,
        write_off_stock,
    )
    from sales.models import Sale, SaleCounter
    from sales.services import add_product_to_draft, checkout_sale

    with (HERE / "migrations-15b.txt").open("w", encoding="utf-8") as mlog, contextlib.redirect_stdout(
        mlog
    ), contextlib.redirect_stderr(mlog):
        call_command("migrate", interactive=False, verbosity=1)

    with connection.cursor() as cur:
        cur.execute(
            "SELECT current_database(), current_setting('data_directory'), current_setting('transaction_isolation')"
        )
        cur_db, cur_dir, cur_iso = cur.fetchone()
    assert cur_db == DBNAME and Path(cur_dir).resolve() == DBDIR
    report.update({"isolation": cur_iso, "migrated": True, "django": django.get_version()})
    setup_test_environment()

    PW_USER = "Audit15B!Pass9"
    roles = {
        code: Role.objects.update_or_create(code=code, defaults={"name": code})[0]
        for code in ("ADMIN", "ALMACENERO", "VENDEDOR")
    }

    def make_actor(code: str, label: str, password: str = PW_USER) -> Account:
        return Account.objects.create_user(
            email=f"{label.lower()}@audit15b.invalid",
            password=password,
            display_name=label,
            role=roles[code],
        )

    admin1 = make_actor("ADMIN", "Admin1PG15B")
    admin2 = make_actor("ADMIN", "Admin2PG15B")
    warehouse1 = make_actor("ALMACENERO", "Almacen1PG15B")
    warehouse2 = make_actor("ALMACENERO", "Almacen2PG15B")
    seller1 = make_actor("VENDEDOR", "Seller1PG15B")
    seller2 = make_actor("VENDEDOR", "Seller2PG15B")

    cat_main = create_category(actor=admin1, name="CatMainPG15B")
    cat_alt = create_category(actor=admin1, name="CatAltPG15B")
    reg1 = CashRegister.objects.get_or_create(code="CAJA-01")[0]
    reg2 = CashRegister.objects.get_or_create(code="CAJA-02")[0]
    future = tz.localdate() + timedelta(days=90)
    barcode_seq = [0]

    def make_product(label: str, qty: int = 10, cost: str = "3.0000", price: str = "10.00", cat: Category = cat_main):
        barcode_seq[0] += 1
        p = Product.objects.create(
            category=cat,
            name=label,
            barcode=f"775015B{barcode_seq[0]:06d}",
            sale_price=Decimal(price),
        )
        load = confirm_initial_load(
            actor=warehouse1,
            product=p,
            lots=[LotInput(f"LOT-{barcode_seq[0]:03d}", qty, Decimal(cost), future)],
        )
        return p, load.lots.get()

    def race_two(ops, lock_table: str):
        gate = threading.Barrier(2, timeout=15)
        locked = threading.Event()
        attempted = threading.Event()
        pids = {}
        waits = []

        def worker(i: int):
            close_old_connections()
            with connection.cursor() as cur:
                cur.execute("SELECT pg_backend_pid()")
                pids[i] = cur.fetchone()[0]
            first_hit = [False]

            def intercept(execute, query, params, many, context):
                match = ("FOR UPDATE" in query or "FOR NO KEY UPDATE" in query) and f'FROM "{lock_table}"' in query
                if i == 1 and match:
                    attempted.set()
                res = execute(query, params, many, context)
                if i == 0 and match and not first_hit[0]:
                    first_hit[0] = True
                    locked.set()
                    if not attempted.wait(12):
                        raise RuntimeError(f"Worker 1 did not reach lock query on {lock_table}")
                    deadline = time.monotonic() + 12
                    while time.monotonic() < deadline:
                        with connection.cursor() as cur:
                            cur.execute("SELECT pg_blocking_pids(%s)", [pids[1]])
                            blockers = cur.fetchone()[0]
                        if pids[0] in blockers:
                            waits.append({"blocked": pids[1], "blocker": pids[0], "table": lock_table})
                            break
                        time.sleep(0.02)
                    if not waits:
                        raise RuntimeError(f"No PG lock wait observed on {lock_table}")
                return res

            try:
                gate.wait()
                if i == 1 and not locked.wait(12):
                    raise RuntimeError(f"Worker 0 did not acquire lock on {lock_table}")
                with connection.execute_wrapper(intercept):
                    out = ops[i]()
                return {
                    "result": "success",
                    "value": str(getattr(out, "pk", out)),
                    "correlative": getattr(out, "correlative", getattr(out, "correlativo", None)),
                    "replayed": bool(getattr(out, "_replayed", False)),
                }
            except Exception as exc:
                return {"result": type(exc).__name__, "detail": str(exc), "pgcode": getattr(exc, "sqlstate", None)}
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futs = [pool.submit(worker, i) for i in range(2)]
            results = [f.result(timeout=40) for f in futs]
        assert len(set(pids.values())) == 2 and waits, {"pids": pids, "waits": waits, "results": results}
        return {"pids": pids, "lock_waits": waits, "results": results}

    # 1. Merma misma existencia (boundary 7 + 7 over 10)
    def case_01_merma_same_lot() -> dict:
        p, lot = make_product("MermaRaceProd", qty=10)
        r = race_two(
            [
                lambda: write_off_stock(
                    actor=warehouse1, lot=lot, quantity=7, reason=StockWriteOff.Reason.DAMAGE, notes="Rotura A"
                ),
                lambda: write_off_stock(
                    actor=warehouse2, lot=lot, quantity=7, reason=StockWriteOff.Reason.THEFT, notes="Faltante B"
                ),
            ],
            "catalog_product",
        )
        lot.refresh_from_db()
        assert lot.available_quantity == 3
        assert StockWriteOff.objects.filter(lot=lot).count() == 1
        statuses = sorted(item["result"] for item in r["results"])
        assert statuses == ["ValidationError", "success"], r
        return {**r, "remaining_qty": lot.available_quantity, "writeoffs": 1}

    run_case("PG15B-01-merma-mismo-lote-frontera", case_01_merma_same_lot)

    # 2. Merma idempotencia concurrente con misma clave
    def case_02_merma_idempotency() -> dict:
        p, lot = make_product("MermaIdempProd", qty=10)
        idem = str(uuid.uuid4())
        r = race_two(
            [
                lambda: write_off_stock(
                    actor=warehouse1, lot=lot, quantity=4, reason=StockWriteOff.Reason.DAMAGE, notes="Rotura X", idempotency_key=idem
                ),
                lambda: write_off_stock(
                    actor=warehouse1, lot=lot, quantity=4, reason=StockWriteOff.Reason.DAMAGE, notes="Rotura X", idempotency_key=idem
                ),
            ],
            "catalog_product",
        )
        lot.refresh_from_db()
        assert lot.available_quantity == 6
        assert StockWriteOff.objects.filter(lot=lot).count() == 1
        assert all(item["result"] == "success" for item in r["results"]), r
        assert r["results"][0]["value"] == r["results"][1]["value"], r
        assert any(item["replayed"] for item in r["results"]), r
        return {**r, "remaining_qty": lot.available_quantity, "writeoffs": 1}

    run_case("PG15B-02-merma-idempotencia-misma-clave", case_02_merma_idempotency)

    # 3. Merma vs checkout_sale FEFO concurrente en mismo producto/lote
    def case_03_merma_vs_checkout() -> dict:
        p, lot = make_product("MermaVsVentaProd", qty=10, price="10.00")
        shift = open_cash_shift(actor=seller1, opening_amount=Decimal("50.00"))
        try:
            draft = add_product_to_draft(actor=seller1, product_id=p.pk, quantity=7)
            k = uuid.uuid4()
            r = race_two(
                [
                    lambda: write_off_stock(
                        actor=warehouse1, lot=lot, quantity=7, reason=StockWriteOff.Reason.DAMAGE, notes="Rotura concurrente"
                    ),
                    lambda: checkout_sale(
                        actor=seller1, draft_id=draft.pk, cash_received=Decimal("80.00"), idempotency_key=k
                    ),
                ],
                "catalog_product",
            )
            lot.refresh_from_db()
            statuses = sorted(item["result"] for item in r["results"])
            assert statuses == ["ValidationError", "success"], r
            assert lot.available_quantity == 3
        finally:
            from sales.services import discard_active_draft

            discard_active_draft(actor=seller1)
            close_cash_shift(actor=seller1, counted_amount=Decimal("50.00") + sum(s.total_amount for s in Sale.objects.filter(cash_shift=shift)))
        return {**r, "remaining_qty": lot.available_quantity}

    run_case("PG15B-03-merma-vs-checkout-fefo", case_03_merma_vs_checkout)

    # 4. Colision correlativo B-XXXXXXXX en write_off_stock entre dos productos distintos (reintento SAVEPOINT)
    def case_04_writeoff_correlativo_collision() -> dict:
        p1, lot1 = make_product("CorrWriteOffA", qty=5)
        p2, lot2 = make_product("CorrWriteOffB", qty=5)
        orig_next = inv_services._next_writeoff_correlativo
        corr_gate = threading.Barrier(2, timeout=15)
        computed_corrs = []
        lock_list = threading.Lock()
        tx_blocker = {"blocked": False, "pids": []}

        def hooked_next() -> str:
            code = orig_next()
            with lock_list:
                computed_corrs.append(code)
                n_calls = len(computed_corrs)
            if n_calls <= 2:
                # Barrier guarantees both workers read identical correlative before either inserts.
                corr_gate.wait()
            return code

        results = [None, None]
        pids = {}
        try:
            inv_services._next_writeoff_correlativo = hooked_next
            ready_p0 = threading.Event()

            def w(idx: int, actor: Account, lot_obj: Lot):
                close_old_connections()
                with connection.cursor() as cur:
                    cur.execute("SELECT pg_backend_pid()")
                    pids[idx] = cur.fetchone()[0]
                ready_p0.set()

                def slow_insert_wrapper(execute, query, params, many, context):
                    if idx == 0 and 'INSERT INTO "inventory_stockwriteoff"' in query:
                        res = execute(query, params, many, context)
                        # Pause briefly inside transaction so worker 1 hits PostgreSQL unique-index transactionid wait
                        deadline = time.monotonic() + 2.0
                        while time.monotonic() < deadline and 1 in pids:
                            with connection.cursor() as cur:
                                cur.execute("SELECT pg_blocking_pids(%s)", [pids[1]])
                                blk = cur.fetchone()[0]
                            if pids[0] in blk:
                                tx_blocker["blocked"] = True
                                tx_blocker["pids"] = blk
                                break
                            time.sleep(0.02)
                        return res
                    return execute(query, params, many, context)

                try:
                    with connection.execute_wrapper(slow_insert_wrapper):
                        out = write_off_stock(
                            actor=actor,
                            lot=lot_obj,
                            quantity=1,
                            reason=StockWriteOff.Reason.DAMAGE,
                            notes=f"Corr {idx}",
                        )
                    results[idx] = {"result": "success", "correlativo": out.correlativo}
                except Exception as exc:
                    results[idx] = {"result": type(exc).__name__, "detail": str(exc)}
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=2) as pool:
                f0 = pool.submit(w, 0, warehouse1, lot1)
                f1 = pool.submit(w, 1, warehouse2, lot2)
                f0.result(timeout=30)
                f1.result(timeout=30)
        finally:
            inv_services._next_writeoff_correlativo = orig_next

        assert all(item and item["result"] == "success" for item in results), results
        corrs = sorted(item["correlativo"] for item in results)
        assert len(set(corrs)) == 2, results
        assert len(computed_corrs) >= 3, {"computed_corrs": computed_corrs, "results": results}
        lot1.refresh_from_db()
        lot2.refresh_from_db()
        assert lot1.available_quantity == 4 and lot2.available_quantity == 4
        return {
            "initial_colliding_computations": computed_corrs[:2],
            "all_computations": computed_corrs,
            "unique_index_wait_observed": tx_blocker["blocked"],
            "correlatives": corrs,
            "results": results,
        }

    run_case("PG15B-04-merma-correlativo-colision-savepoint", case_04_writeoff_correlativo_collision)

    # 5. Ajuste negativo mismo lote (boundary -7 and -7 on 10)
    def case_05_ajuste_negativo_mismo_lote() -> dict:
        p, lot = make_product("AjusteNegProd", qty=10)
        r = race_two(
            [
                lambda: register_physical_adjustment(actor=admin1, lot=lot, delta=-7, reason="Conteo fis A"),
                lambda: register_physical_adjustment(actor=admin2, lot=lot, delta=-7, reason="Conteo fis B"),
            ],
            "catalog_product",
        )
        lot.refresh_from_db()
        assert lot.available_quantity == 3
        assert PhysicalAdjustment.objects.filter(lot=lot).count() == 1
        statuses = sorted(item["result"] for item in r["results"])
        assert statuses == ["ValidationError", "success"], r
        return {**r, "remaining_qty": lot.available_quantity}

    run_case("PG15B-05-ajuste-negativo-mismo-lote", case_05_ajuste_negativo_mismo_lote)

    # 6. Ajuste positivo Q=0 creando lote nuevo con mismo numero concurrentemente
    def case_06_ajuste_nuevo_lote_mismo_numero() -> dict:
        p, lot = make_product("AjusteQ0Prod", qty=5)
        register_physical_adjustment(actor=admin1, lot=lot, delta=-5, reason="Llevar a cero para prueba Q0")
        p.refresh_from_db()
        assert p.average_cost == Decimal("0.0000")
        exp_new = future + timedelta(days=30)
        r = race_two(
            [
                lambda: register_physical_adjustment(
                    actor=admin1,
                    product=p,
                    number="aj-race-01",
                    expiration_date=exp_new,
                    delta=6,
                    unit_cost=Decimal("4.2500"),
                    cost_source="Boleta proveedor 001",
                    reason="Hallazgo Q0 A",
                ),
                lambda: register_physical_adjustment(
                    actor=admin2,
                    product=p,
                    number=" AJ-RACE-01 ",
                    expiration_date=exp_new,
                    delta=4,
                    unit_cost=Decimal("4.5000"),
                    cost_source="Boleta proveedor 002",
                    reason="Hallazgo Q0 B",
                ),
            ],
            "catalog_product",
        )
        p.refresh_from_db()
        new_lots = list(Lot.objects.filter(product=p, number_normalized="AJ-RACE-01"))
        assert len(new_lots) == 1
        statuses = sorted(item["result"] for item in r["results"])
        assert statuses == ["ValidationError", "success"], r
        return {**r, "new_lots_count": 1, "qty": new_lots[0].available_quantity, "avg_cost": str(p.average_cost)}

    run_case("PG15B-06-ajuste-positivo-q0-nuevo-lote", case_06_ajuste_nuevo_lote_mismo_numero)

    # 7. Ajuste idempotencia misma clave concurrente
    def case_07_ajuste_idempotencia() -> dict:
        p, lot = make_product("AjusteIdempProd", qty=10)
        idem = str(uuid.uuid4())
        r = race_two(
            [
                lambda: register_physical_adjustment(
                    actor=admin1, lot=lot, delta=4, reason="Reencuentro A", idempotency_key=idem
                ),
                lambda: register_physical_adjustment(
                    actor=admin1, lot=lot, delta=4, reason="Reencuentro A", idempotency_key=idem
                ),
            ],
            "catalog_product",
        )
        lot.refresh_from_db()
        assert lot.available_quantity == 14
        assert PhysicalAdjustment.objects.filter(lot=lot).count() == 1
        assert all(item["result"] == "success" for item in r["results"])
        assert r["results"][0]["value"] == r["results"][1]["value"]
        assert any(item["replayed"] for item in r["results"])
        return {**r, "final_qty": lot.available_quantity, "adjustments": 1}

    run_case("PG15B-07-ajuste-idempotencia-misma-clave", case_07_ajuste_idempotencia)

    # 8. Ajuste negativo vs checkout_sale concurrente
    def case_08_ajuste_vs_checkout() -> dict:
        p, lot = make_product("AjusteVsVentaProd", qty=10, price="10.00")
        shift = open_cash_shift(actor=seller1, opening_amount=Decimal("20.00"))
        try:
            draft = add_product_to_draft(actor=seller1, product_id=p.pk, quantity=7)
            k = uuid.uuid4()
            r = race_two(
                [
                    lambda: register_physical_adjustment(actor=admin1, lot=lot, delta=-7, reason="Conteo simultaneo"),
                    lambda: checkout_sale(
                        actor=seller1, draft_id=draft.pk, cash_received=Decimal("80.00"), idempotency_key=k
                    ),
                ],
                "catalog_product",
            )
            lot.refresh_from_db()
            statuses = sorted(item["result"] for item in r["results"])
            assert statuses == ["ValidationError", "success"], r
            assert lot.available_quantity == 3
        finally:
            from sales.services import discard_active_draft

            discard_active_draft(actor=seller1)
            close_cash_shift(actor=seller1, counted_amount=Decimal("20.00") + sum(s.total_amount for s in Sale.objects.filter(cash_shift=shift)))
        return {**r, "remaining_qty": lot.available_quantity}

    run_case("PG15B-08-ajuste-vs-checkout-fefo", case_08_ajuste_vs_checkout)

    # 9. Ajuste negativo vs merma concurrente
    def case_09_ajuste_vs_merma() -> dict:
        p, lot = make_product("AjusteVsMermaProd", qty=10)
        r = race_two(
            [
                lambda: register_physical_adjustment(actor=admin1, lot=lot, delta=-7, reason="Ajuste fis vs merma"),
                lambda: write_off_stock(
                    actor=warehouse1, lot=lot, quantity=7, reason=StockWriteOff.Reason.DAMAGE, notes="Merma vs ajuste"
                ),
            ],
            "catalog_product",
        )
        lot.refresh_from_db()
        statuses = sorted(item["result"] for item in r["results"])
        assert statuses == ["ValidationError", "success"], r
        assert lot.available_quantity == 3
        return {**r, "remaining_qty": lot.available_quantity}

    run_case("PG15B-09-ajuste-vs-merma", case_09_ajuste_vs_merma)

    # 10. Correlativos recepcion (StockReceiptCounter R-XXXXXXXX) en paralelo sobre dos productos
    def case_10_correlativos_recepcion() -> dict:
        p1, _ = make_product("RecCounterA", qty=2, cost="2.0000")
        p2, _ = make_product("RecCounterB", qty=2, cost="2.0000")
        r = race_two(
            [
                lambda: register_stock_entry(
                    actor=warehouse1,
                    product=p1,
                    lots=[LotInput("REC-A1", 5, Decimal("2.5000"), future + timedelta(days=10))],
                ),
                lambda: register_stock_entry(
                    actor=warehouse2,
                    product=p2,
                    lots=[LotInput("REC-B1", 5, Decimal("2.5000"), future + timedelta(days=10))],
                ),
            ],
            "inventory_stockreceiptcounter",
        )
        assert all(item["result"] == "success" for item in r["results"]), r
        corrs = sorted(item["correlative"] for item in r["results"])
        assert corrs == ["R-00000001", "R-00000002"], corrs
        assert StockReceipt.objects.count() == 2
        return {**r, "correlatives": corrs}

    run_case("PG15B-10-correlativos-recepcion-StockReceiptCounter", case_10_correlativos_recepcion)

    # 11. Correlativos venta (SaleCounter V-XXXXXXXX) paralelo + reintento idempotente sin salto
    def case_11_correlativos_venta() -> dict:
        p1, _ = make_product("SaleCounterA", qty=5, price="10.00")
        p2, _ = make_product("SaleCounterB", qty=5, price="10.00")
        sh1 = CashShift.objects.create(cash_register=reg1, seller=seller1, opening_amount=Decimal("10.00"))
        sh2 = CashShift.objects.create(cash_register=reg2, seller=seller2, opening_amount=Decimal("10.00"))
        try:
            d1 = add_product_to_draft(actor=seller1, product_id=p1.pk, quantity=1)
            d2 = add_product_to_draft(actor=seller2, product_id=p2.pk, quantity=1)
            k1 = uuid.uuid4()
            k2 = uuid.uuid4()
            r = race_two(
                [
                    lambda: checkout_sale(actor=seller1, draft_id=d1.pk, cash_received=Decimal("10.00"), idempotency_key=k1),
                    lambda: checkout_sale(actor=seller2, draft_id=d2.pk, cash_received=Decimal("10.00"), idempotency_key=k2),
                ],
                "sales_salecounter",
            )
            assert all(item["result"] == "success" for item in r["results"]), r
            corrs = [item["correlative"] for item in r["results"]]
            assert len(set(corrs)) == 2
            nums = sorted(int(c.split("-")[1]) for c in corrs)
            assert nums[1] == nums[0] + 1, corrs

            # Sub-check: concurrent idempotent retry on seller1 does NOT skip SaleCounter
            counter_before = SaleCounter.objects.get(id=1).next_value
            d_retry = add_product_to_draft(actor=seller1, product_id=p1.pk, quantity=1)
            k_retry = uuid.uuid4()
            r_retry = race_two(
                [
                    lambda: checkout_sale(
                        actor=seller1, draft_id=d_retry.pk, cash_received=Decimal("10.00"), idempotency_key=k_retry
                    ),
                    lambda: checkout_sale(
                        actor=seller1, draft_id=d_retry.pk, cash_received=Decimal("10.00"), idempotency_key=k_retry
                    ),
                ],
                "sales_saledraft",
            )
            counter_after = SaleCounter.objects.get(id=1).next_value
            assert all(item["result"] == "success" for item in r_retry["results"]), r_retry
            assert r_retry["results"][0]["value"] == r_retry["results"][1]["value"]
            assert counter_after == counter_before + 1, (counter_before, counter_after)
            return {
                "parallel_sellers_correlatives": sorted(corrs),
                "parallel_lock_waits": r["lock_waits"],
                "retry_same_key_results": r_retry["results"],
                "counter_before_retry": counter_before,
                "counter_after_retry": counter_after,
            }
        finally:
            sh1.status = CashShift.Status.CLOSED
            sh2.status = CashShift.Status.CLOSED
            sh1.save(update_fields=["status", "updated_at"])
            sh2.save(update_fields=["status", "updated_at"])

    run_case("PG15B-11-correlativos-venta-SaleCounter-y-reintento", case_11_correlativos_venta)

    # 12. Matriz anti-deadlock cruzado (0 DeadlockDetected 40P01)
    def case_12_anti_deadlock_matrix() -> dict:
        # 12a: toggle_category_status vs checkout_sale (with checkout holding Product before locking Category)
        cat_dead = create_category(actor=admin1, name="CatDeadlock15B")
        p_dead, _ = make_product("ProdDead15B", qty=5, price="10.00", cat=cat_dead)
        sh = open_cash_shift(actor=seller1, opening_amount=Decimal("10.00"))
        try:
            draft = add_product_to_draft(actor=seller1, product_id=p_dead.pk, quantity=1)
            k_dead = uuid.uuid4()
            holding_product = threading.Event()
            cat_updated = threading.Event()

            def run_checkout_holding_prod():
                close_old_connections()

                def wrap_cat(execute, query, params, many, context):
                    if 'FROM "catalog_product"' in query and ("FOR UPDATE" in query or "FOR NO KEY UPDATE" in query):
                        res = execute(query, params, many, context)
                        holding_product.set()
                        cat_updated.wait(10)
                        return res
                    return execute(query, params, many, context)

                try:
                    with connection.execute_wrapper(wrap_cat):
                        out = checkout_sale(
                            actor=seller1, draft_id=draft.pk, cash_received=Decimal("10.00"), idempotency_key=k_dead
                        )
                    return {"result": "success", "sale": str(out.pk)}
                except Exception as exc:
                    return {"result": type(exc).__name__, "detail": str(exc), "pgcode": getattr(exc, "sqlstate", None)}
                finally:
                    connections.close_all()

            def run_toggle_cat():
                close_old_connections()
                try:
                    holding_product.wait(10)
                    out = toggle_category_status(actor=admin1, category=cat_dead, is_active=False)
                    cat_updated.set()
                    return {"result": "success", "is_active": out.is_active}
                except Exception as exc:
                    cat_updated.set()
                    return {"result": type(exc).__name__, "detail": str(exc), "pgcode": getattr(exc, "sqlstate", None)}
                finally:
                    connections.close_all()

            with ThreadPoolExecutor(max_workers=2) as pool:
                f_chk = pool.submit(run_checkout_holding_prod)
                f_cat = pool.submit(run_toggle_cat)
                res_chk = f_chk.result(timeout=30)
                res_cat = f_cat.result(timeout=30)
            assert res_cat == {"result": "success", "is_active": False}, res_cat
            assert res_chk["result"] == "ValidationError" and res_chk.get("pgcode") != "40P01", res_chk
        finally:
            from sales.services import discard_active_draft

            discard_active_draft(actor=seller1)
            close_cash_shift(actor=seller1, counted_amount=Decimal("10.00") + sum(s.total_amount for s in Sale.objects.filter(cash_shift=sh)))

        # 12b: update_product(category=cat_alt) vs register_stock_entry on same Product (both lock Product -> Category)
        p_swap, _ = make_product("ProdSwap15B", qty=5, cost="3.0000", price="10.00")
        r_prod_cat = race_two(
            [
                lambda: update_product(
                    actor=admin1,
                    product=p_swap,
                    name=p_swap.name,
                    barcode=p_swap.barcode,
                    sale_price=Decimal("11.00"),
                    minimum_stock=p_swap.minimum_stock,
                    category=cat_alt,
                ),
                lambda: register_stock_entry(
                    actor=warehouse1,
                    product=p_swap,
                    lots=[LotInput("SWAP-01", 3, Decimal("3.5000"), future + timedelta(days=15))],
                ),
            ],
            "catalog_product",
        )
        assert all(item["result"] == "success" for item in r_prod_cat["results"]), r_prod_cat

        # 12c: Mutual update_employee(admin1 -> admin2) vs update_employee(admin2 -> admin1) serialized by Role('ADMIN')
        r_emp = race_two(
            [
                lambda: update_employee(
                    actor=admin1,
                    account=admin2,
                    display_name="Admin2RenamedB",
                    email=admin2.email,
                    role=roles["ADMIN"],
                ),
                lambda: update_employee(
                    actor=admin2,
                    account=admin1,
                    display_name="Admin1RenamedB",
                    email=admin1.email,
                    role=roles["ADMIN"],
                ),
            ],
            "identity_role",
        )
        assert all(item["result"] == "success" for item in r_emp["results"]), r_emp
        admin1.refresh_from_db()
        admin2.refresh_from_db()
        assert admin1.display_name == "Admin1RenamedB" and admin2.display_name == "Admin2RenamedB"
        return {
            "12a_category_toggle_vs_checkout": {"checkout": res_chk, "category_toggle": res_cat, "deadlocks": 0},
            "12b_update_product_vs_stock_entry": r_prod_cat,
            "12c_mutual_admin_update_employee": r_emp,
        }

    run_case("PG15B-12-matriz-anti-deadlock-cruzado", case_12_anti_deadlock_matrix)

except Exception as exc:
    report["fatal"] = {
        "type": type(exc).__name__,
        "detail": str(exc).replace(PW, "[REDACTED]"),
        "traceback": traceback.format_exc().replace(PW, "[REDACTED]"),
    }
finally:
    if started:
        try:
            if "connections" in globals():
                connections.close_all()
            pg("pg_ctl", "-D", DBDIR, "-m", "fast", "-w", "stop")
            with socket.socket() as s:
                s.settimeout(1)
                report["port_closed"] = s.connect_ex(("127.0.0.1", PORT)) != 0
            report["cluster_stopped"] = True
        except Exception as exc:
            report["stop_error"] = str(exc).replace(PW, "[REDACTED]")
    if PWFILE.exists():
        PWFILE.unlink()
    own()
    shutil.rmtree(CLUSTER, ignore_errors=True)
    report["cluster_deleted"] = not CLUSTER.exists()
    report["after_build"] = compute_build()
    report["source_stable"] = report["before_build"] == report["after_build"]
    report["passed"] = sum(1 for c in report["cases"] if c["ok"])
    report["total"] = len(report["cases"])
    report["ok"] = (
        not report.get("fatal")
        and report["passed"] == report["total"]
        and report["source_stable"]
        and report.get("cluster_stopped", False)
        and report.get("cluster_deleted", False)
        and report.get("port_closed", False)
    )
    report["finished_utc"] = datetime.now(dt_timezone.utc).isoformat()
    save_report("resultados-pg15b.json")
    partial_file = HERE / "resultados-pg15b-partial.json"
    if partial_file.exists():
        partial_file.unlink()
    print(
        json.dumps(
            {
                k: report[k]
                for k in ("ok", "passed", "total", "source_stable", "cluster_stopped", "cluster_deleted", "port_closed")
            },
            ensure_ascii=False,
        )
    )
sys.exit(0 if report["ok"] else 1)
