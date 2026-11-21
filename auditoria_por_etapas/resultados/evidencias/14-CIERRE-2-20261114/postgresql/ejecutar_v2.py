"""14-CIERRE-2: 24 PostgreSQL 18.4 concurrency/persistence checks (19 base + PG14-16..20)."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "r1-pmv/manage.py").exists())
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / ("corrida-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S"))
OUT.mkdir(parents=True, exist_ok=False)
(OUT / "runner-ejecutado.py").write_bytes(Path(__file__).read_bytes())
(OUT / "08-ejecutado.md").write_bytes((ROOT / "08_Historias_de_Usuario.md").read_bytes())

BIN = Path("C:/Program Files/PostgreSQL/18/bin")
STAMP = datetime.now(timezone.utc).isoformat()
CLUSTER = (Path(tempfile.gettempdir()) / ("audit14c2-pg-" + secrets.token_hex(10))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT14C2_OWNED"
MARK.write_text(STAMP, encoding="utf-8")
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(40)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit14c2_" + secrets.token_hex(5)
with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build() -> dict:
    names = subprocess.check_output(
        ["git", "-C", str(ROOT / "r1-pmv"), "ls-files", "-co", "--exclude-standard", "-z"]
    ).decode().split("\0")
    files = {
        n: digest((ROOT / "r1-pmv" / n).read_bytes())
        for n in sorted(set(names))
        if n and not n.startswith("evidencias/") and Path(n).suffix in {".py", ".html", ".css", ".js", ".svg", ".ps1", ".sh"}
    }
    return dict(files=files, sha256=digest(json.dumps(files, sort_keys=True, separators=(",", ":")).encode()))


def save(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")


def own() -> None:
    assert CLUSTER.parent == Path(tempfile.gettempdir()).resolve() and CLUSTER.name.startswith("audit14c2-pg-")
    assert MARK.read_text(encoding="utf-8") == STAMP


def pg(name: str, *args) -> None:
    own()
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as f:
        r = subprocess.run(
            [str(BIN / (name + ".exe")), *map(str, args)],
            stdout=f,
            stderr=f,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        f.seek(0)
        text = f.read().replace(PW, "[REDACTED]")
    if r.returncode:
        raise RuntimeError(name + ": " + text[-1200:])


report: dict = dict(
    started_utc=STAMP,
    pasada=1,
    sublote="14-CIERRE-2-PG",
    cases=[],
    cluster=str(CLUSTER),
    database=DBNAME,
    port=PORT,
    plan08=digest((ROOT / "08_Historias_de_Usuario.md").read_bytes()),
    before=build(),
    runner_sha256=digest(Path(__file__).read_bytes()),
    python=sys.version,
    head=subprocess.check_output(["git", "-C", str(ROOT / "r1-pmv"), "rev-parse", "HEAD"], text=True).strip(),
)


def case(name: str, fn) -> None:
    start = time.monotonic()
    try:
        details = fn() or {}
        report["cases"].append(dict(id=name, ok=True, seconds=round(time.monotonic() - start, 3), **details))
    except Exception as e:
        report["cases"].append(
            dict(
                id=name,
                ok=False,
                seconds=round(time.monotonic() - start, 3),
                error=type(e).__name__,
                detail=str(e).replace(PW, "[REDACTED]"),
                traceback=traceback.format_exc().replace(PW, "[REDACTED]"),
            )
        )
    save(OUT / "results-partial.json", report)
    print(name, report["cases"][-1]["ok"], flush=True)


started = False
try:
    base_runner = ROOT / "auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/postgresql/ejecutar.py"
    base_out = OUT / "base-pg19"
    base_proc = subprocess.run(
        [sys.executable, "-X", "utf8", str(base_runner), str(base_out)],
        capture_output=True,
        text=True,
        timeout=240,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    (OUT / "base-pg19-stdout.txt").write_text(
        (base_proc.stdout or "") + "\n--- STDERR ---\n" + (base_proc.stderr or ""),
        encoding="utf-8",
    )
    base_results = json.loads((base_out / "results.json").read_text(encoding="utf-8"))
    report["base_pg19_summary"] = {
        "returncode": base_proc.returncode,
        "ok": base_results.get("ok"),
        "passed": base_results.get("passed"),
        "total": base_results.get("total"),
        "build_sha256": base_results.get("before", {}).get("sha256"),
        "source_stable": base_results.get("source_stable"),
    }
    assert base_proc.returncode == 0 and base_results.get("ok") is True and len(base_results.get("cases", [])) == 19, report["base_pg19_summary"]
    report["cases"].extend(base_results["cases"])
    save(OUT / "results-partial.json", report)

    pg("initdb", "-D", DBDIR, "-U", "audit14c2", "--pwfile", PWFILE, "--auth-host=scram-sha-256", "--auth-local=scram-sha-256", "--encoding=UTF8", "--locale=C")
    PWFILE.unlink()
    pg("pg_ctl", "-D", DBDIR, "-l", CLUSTER / "postgres.log", "-o", f"-h 127.0.0.1 -p {PORT} -c log_statement=none -c log_min_error_statement=panic", "-w", "start")
    started = True

    import psycopg
    from psycopg import sql

    conf = dict(host="127.0.0.1", port=PORT, user="audit14c2", password=PW)
    with psycopg.connect(**conf, dbname="postgres", autocommit=True) as c:
        assert Path(c.execute("SHOW data_directory").fetchone()[0]).resolve() == DBDIR
        report["postgres_version"] = c.execute("SELECT version()").fetchone()[0]
        c.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DBNAME)))

    sys.path.insert(0, str(ROOT / "r1-pmv"))
    os.environ.update(
        APP_ENV="test",
        DJANGO_DEBUG="false",
        DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
        DJANGO_SETTINGS_MODULE="config.settings",
        DJANGO_ALLOWED_HOSTS="testserver,127.0.0.1",
    )
    from config import env

    env.load_dotenv = lambda path=None: None
    from django.conf import settings

    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": DBNAME,
            "USER": "audit14c2",
            "PASSWORD": PW,
            "HOST": "127.0.0.1",
            "PORT": PORT,
            "CONN_MAX_AGE": 0,
            "OPTIONS": {"options": "-c statement_timeout=30000 -c lock_timeout=15000"},
        }
    }
    import django

    django.setup()
    from django.core.exceptions import ValidationError
    from django.core.management import call_command
    from django.db import close_old_connections, connection, connections
    from django.test.utils import setup_test_environment
    from django.utils import timezone as tz

    from cash.models import CashRegister, CashShift, CashShiftClose
    from cash.services import close_cash_shift, open_cash_shift
    from catalog.models import Category, Product
    from catalog.services import toggle_product_availability, update_product
    from identity.models import Account, Role
    from inventory.models import Lot
    from inventory.services import LotInput, confirm_initial_load, register_stock_entry
    from sales.models import Sale, SaleDraft, SaleDraftLine, SaleLine
    from sales.services import add_product_to_draft, checkout_sale, discard_active_draft

    with (OUT / "migrations-v2.txt").open("x", encoding="utf-8") as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        call_command("migrate", interactive=False, verbosity=1)

    with connection.cursor() as c:
        c.execute("SELECT current_database(), current_setting('data_directory'), current_setting('transaction_isolation')")
        db, folder, isolation = c.fetchone()
    assert db == DBNAME and Path(folder).resolve() == DBDIR
    report.update(isolation=isolation, migrated=True, django=django.get_version())
    setup_test_environment()

    roles = {code: Role.objects.create(code=code, name=code) for code in ("ADMIN", "ALMACENERO", "VENDEDOR")}

    def actor(code: str, label: str) -> Account:
        return Account.objects.create_user(
            email=label.lower() + "@audit14c2.invalid",
            password=None,
            display_name=label,
            role=roles[code],
        )

    admin = actor("ADMIN", "AdminPG2")
    warehouse = actor("ALMACENERO", "AlmacenPG2")
    seller = actor("VENDEDOR", "VentaPG2A")
    seller2 = actor("VENDEDOR", "VentaPG2B")
    cat_a = Category.objects.create(name="CatA_PG14C2", name_normalized="cata_pg14c2")
    cat_b = Category.objects.create(name="CatB_PG14C2", name_normalized="catb_pg14c2")
    register = CashRegister.objects.get_or_create(code="CAJA-01")[0]
    future = tz.localdate() + timedelta(days=90)

    def make_product(label: str, qty: int = 10, cost: str = "3", price: str = "10", category: Category | None = None):
        p = Product.objects.create(
            category=category or cat_a,
            name=label,
            barcode="INT-" + label,
            sale_price=Decimal(price),
            controls_expiration=True,
        )
        load = confirm_initial_load(actor=warehouse, product=p, lots=[LotInput("A", qty, Decimal(cost), future)])
        return p, load.lots.get()

    def race(ops, table: str = "catalog_product") -> dict:
        gate = threading.Barrier(2, timeout=12)
        locked = threading.Event()
        attempted = threading.Event()
        pids: dict[int, int] = {}
        waits: list[dict] = []

        def work(i: int) -> dict:
            close_old_connections()
            with connection.cursor() as c:
                c.execute("SELECT pg_backend_pid()")
                pids[i] = c.fetchone()[0]
            first_hit = [False]

            def intercept(execute, query, params, many, context):
                match = "FOR UPDATE" in query and f'FROM "{table}"' in query
                if i == 1 and match:
                    attempted.set()
                result = execute(query, params, many, context)
                if i == 0 and match and not first_hit[0]:
                    first_hit[0] = True
                    locked.set()
                    if not attempted.wait(12):
                        raise RuntimeError(f"Second connection did not reach contested lock on {table}")
                    end = time.monotonic() + 12
                    while time.monotonic() < end:
                        with connection.cursor() as c:
                            c.execute("SELECT pg_blocking_pids(%s)", [pids[1]])
                            observed = c.fetchone()[0]
                        if pids[0] in observed:
                            waits.append(dict(blocked=pids[1], blocker=pids[0]))
                            break
                        time.sleep(0.02)
                    if not waits:
                        raise RuntimeError(f"No real PG blocking observed on {table}")
                return result

            try:
                gate.wait()
                if i == 1 and not locked.wait(12):
                    raise RuntimeError(f"First lock not acquired on {table}")
                with connection.execute_wrapper(intercept):
                    result = ops[i]()
                return dict(result="success", pk=str(getattr(result, "pk", result)))
            except Exception as e:
                return dict(result=type(e).__name__, detail=str(e))
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(work, i) for i in range(2)]
            results = [f.result(timeout=40) for f in futures]
        assert len(set(pids.values())) == 2 and waits, dict(pids=pids, waits=waits, results=results)
        return dict(pids=pids, lock_waits=waits, results=results)

    def pg16_single_open_shift_concurrent():
        CashShift.objects.filter(status="OPEN").update(status="CLOSED")
        r = race(
            [
                lambda: open_cash_shift(actor=seller, opening_amount=Decimal("50.00")),
                lambda: open_cash_shift(actor=seller2, opening_amount=Decimal("60.00")),
            ],
            table="cash_cashregister",
        )
        assert [o["result"] for o in r["results"]] == ["success", "ValidationError"], r
        assert CashShift.objects.filter(status="OPEN").count() == 1
        return dict(**r, open_shifts=1)

    case("PG14-16-turno-unico-concurrente", pg16_single_open_shift_concurrent)

    def pg17_close_vs_checkout_concurrent():
        p, _ = make_product("CloseVsCheckoutPG14C2", qty=10, cost="3.0000", price="10.00")
        # Order A: close holds actor lock first -> blocks checkout -> checkout rejects cleanly
        CashShift.objects.filter(status="OPEN").update(status="CLOSED")
        sh1 = open_cash_shift(actor=seller, opening_amount=Decimal("100.00"))
        d1 = add_product_to_draft(actor=seller, product_id=p.pk, quantity=1)
        r_close_first = race(
            [
                lambda: close_cash_shift(actor=seller, counted_amount=Decimal("100.00")),
                lambda: checkout_sale(actor=seller, draft_id=d1.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4()),
            ],
            table="identity_account",
        )
        assert [o["result"] for o in r_close_first["results"]] == ["success", "ValidationError"], r_close_first
        c1 = CashShiftClose.objects.get(cash_shift=sh1)
        assert Sale.objects.filter(cash_shift=sh1).count() == 0 and c1.expected_amount == Decimal("100.00") and c1.difference == Decimal("0.00")

        # Order B: checkout holds actor lock first -> blocks close -> close sees committed sale (110.00)
        sh2 = open_cash_shift(actor=seller, opening_amount=Decimal("100.00"))
        d2 = add_product_to_draft(actor=seller, product_id=p.pk, quantity=1)
        r_sale_first = race(
            [
                lambda: checkout_sale(actor=seller, draft_id=d2.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4()),
                lambda: close_cash_shift(actor=seller, counted_amount=Decimal("110.00")),
            ],
            table="identity_account",
        )
        assert [o["result"] for o in r_sale_first["results"]] == ["success", "success"], r_sale_first
        c2 = CashShiftClose.objects.get(cash_shift=sh2)
        assert Sale.objects.filter(cash_shift=sh2).count() == 1 and c2.expected_amount == Decimal("110.00") and c2.difference == Decimal("0.00")
        return dict(close_first=r_close_first, sale_first=r_sale_first, remaining_stock=Lot.objects.get(product=p).available_quantity)

    case("PG14-17-cierre-y-cobro-concurrentes", pg17_close_vs_checkout_concurrent)

    def pg18_deactivate_product_vs_checkout():
        CashShift.objects.filter(status="OPEN").update(status="CLOSED")
        open_cash_shift(actor=seller, opening_amount=Decimal("50.00"))
        p, lot = make_product("DeactivateRacePG14C2", qty=10, cost="3.0000", price="10.00")
        draft = add_product_to_draft(actor=seller, product_id=p.pk, quantity=2)
        r = race(
            [
                lambda: toggle_product_availability(actor=admin, product=p, is_active=False),
                lambda: checkout_sale(actor=seller, draft_id=draft.pk, cash_received=Decimal("20.00"), idempotency_key=uuid.uuid4()),
            ],
            table="catalog_product",
        )
        assert [o["result"] for o in r["results"]] == ["success", "ValidationError"], r
        p.refresh_from_db()
        lot.refresh_from_db()
        assert not p.is_active and Sale.objects.filter(draft=draft).count() == 0 and lot.available_quantity == 10
        discard_active_draft(actor=seller)
        return dict(**r, active=p.is_active, stock=lot.available_quantity)

    case("PG14-18-borrador-producto-desactivado-concurrente", pg18_deactivate_product_vs_checkout)

    def pg19_reprice_reclassify_vs_checkout():
        CashShift.objects.filter(status="OPEN").update(status="CLOSED")
        sh = open_cash_shift(actor=seller, opening_amount=Decimal("50.00"))
        p, lot = make_product("RepriceCatPG14C2", qty=10, cost="3.0000", price="10.00", category=cat_a)
        draft = add_product_to_draft(actor=seller, product_id=p.pk, quantity=2)
        r = race(
            [
                lambda: update_product(
                    actor=admin,
                    product=p,
                    name=p.name,
                    barcode=p.barcode,
                    sale_price=Decimal("12.00"),
                    minimum_stock=p.minimum_stock,
                    category=cat_b,
                ),
                lambda: checkout_sale(
                    actor=seller,
                    draft_id=draft.pk,
                    cash_received=Decimal("20.00"),
                    idempotency_key=uuid.uuid4(),
                    expected_subtotal=Decimal("20.00"),
                ),
            ],
            table="catalog_product",
        )
        assert [o["result"] for o in r["results"]] == ["success", "ValidationError"], r
        p.refresh_from_db()
        assert p.sale_price == Decimal("12.00") and p.category_id == cat_b.pk
        assert Sale.objects.filter(draft=draft).count() == 0

        # Explicit DEC-12 review: if line still has old price, next checkout call refreshes it and requires review
        line = SaleDraftLine.objects.get(draft=draft)
        if line.unit_price != Decimal("12.00"):
            try:
                checkout_sale(
                    actor=seller,
                    draft_id=draft.pk,
                    cash_received=Decimal("24.00"),
                    idempotency_key=uuid.uuid4(),
                    expected_subtotal=Decimal("20.00"),
                )
            except ValidationError:
                pass
            else:
                raise AssertionError("Expected price review ValidationError before confirmation")
        sale = checkout_sale(
            actor=seller,
            draft_id=draft.pk,
            cash_received=Decimal("24.00"),
            idempotency_key=uuid.uuid4(),
            expected_subtotal=Decimal("24.00"),
        )
        assert sale.total_amount == Decimal("24.00") and CashShift.objects.filter(pk=sh.pk, status="OPEN").exists()
        lot.refresh_from_db()
        assert lot.available_quantity == 8
        return dict(**r, reviewed_sale_total=str(sale.total_amount), new_category=str(p.category.name), remaining_stock=lot.available_quantity)

    case("PG14-19-cambio-precio-categoria-con-borrador", pg19_reprice_reclassify_vs_checkout)

    def pg20_cost_race_entry_vs_checkout():
        CashShift.objects.filter(status="OPEN").update(status="CLOSED")
        open_cash_shift(actor=seller, opening_amount=Decimal("50.00"))
        p_cost = Product.objects.create(
            category=cat_a,
            name="FCostoPG14C2",
            barcode="INT-FCOSTO-PG14C2",
            sale_price=Decimal("10.00"),
            minimum_stock=2,
            controls_expiration=True,
        )
        confirm_initial_load(
            actor=warehouse,
            product=p_cost,
            lots=[
                LotInput("EXP8", 8, Decimal("3.0000"), future),
                LotInput("VAL10", 10, Decimal("3.0000"), future),
            ],
        )
        Lot.objects.filter(product=p_cost, number_normalized="EXP8").update(expiration_date=tz.localdate() - timedelta(days=1))
        draft = add_product_to_draft(actor=seller, product_id=p_cost.pk, quantity=2)
        r = race(
            [
                lambda: register_stock_entry(
                    actor=warehouse,
                    product=p_cost,
                    lots=[LotInput("C2", 10, Decimal("6.0000"), future)],
                    idempotency_key=uuid.uuid4(),
                ),
                lambda: checkout_sale(
                    actor=seller,
                    draft_id=draft.pk,
                    cash_received=Decimal("20.00"),
                    idempotency_key=uuid.uuid4(),
                ),
            ],
            table="catalog_product",
        )
        assert [o["result"] for o in r["results"]] == ["success", "success"], r
        p_cost.refresh_from_db()
        sale_line = SaleLine.objects.get(sale_id=r["results"][1]["pk"])
        expected_avg = Decimal("4.0714")
        assert sale_line.unit_cost == expected_avg, (sale_line.unit_cost, expected_avg)
        assert p_cost.average_cost == expected_avg and p_cost.physical_stock == 26
        assert Lot.objects.get(product=p_cost, number_normalized="VAL10").available_quantity == 8
        assert Lot.objects.get(product=p_cost, number_normalized="C2").available_quantity == 10
        return dict(
            **r,
            sale_unit_cost=str(sale_line.unit_cost),
            final_average_cost=str(p_cost.average_cost),
            physical_stock=p_cost.physical_stock,
        )

    case("PG14-20-costo-promedio-carrera-entrada-salida", pg20_cost_race_entry_vs_checkout)

except Exception as e:
    report["fatal"] = dict(
        type=type(e).__name__,
        detail=str(e).replace(PW, "[REDACTED]"),
        traceback=traceback.format_exc().replace(PW, "[REDACTED]"),
    )
finally:
    if started:
        try:
            if "connections" in globals():
                connections.close_all()
            pg("pg_ctl", "-D", DBDIR, "-m", "fast", "-w", "stop")
            report["cluster_stopped"] = True
        except Exception as e:
            report["stop_error"] = str(e).replace(PW, "[REDACTED]")
    if PWFILE.exists():
        PWFILE.unlink()
    report.update(after=build(), finished_utc=datetime.now(timezone.utc).isoformat())
    report["source_stable"] = report["before"] == report["after"]
    report["passed"] = sum(c["ok"] for c in report["cases"])
    report["total"] = len(report["cases"])
    report["ok"] = (
        not report.get("fatal")
        and report["passed"] == 24
        and report["total"] == 24
        and report["source_stable"]
        and report.get("cluster_stopped", False)
    )
    save(OUT / "results.json", report)
    print(json.dumps({k: report[k] for k in ("ok", "passed", "total", "source_stable")}, ensure_ascii=False))
sys.exit(0 if report["ok"] else 1)

