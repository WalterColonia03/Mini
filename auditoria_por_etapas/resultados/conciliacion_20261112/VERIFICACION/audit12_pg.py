"""Isolated Stage 12 PostgreSQL 18.4 verification:
- NUL (\x00) query parameter safety on /ventas/historial/ & /caja/turnos/
- Lima America/Lima day-boundary queries (23:59:59-05 vs 00:00:00-05)
- Subquery + Coalesce cash_shift_history constant 4-query count & N+1 sales_history invariance + EXPLAIN JSON
- Concurrent READ COMMITTED checkout + idempotent retry recovery
Never loads operator .env and never modifies existing SQLite files.
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
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[4]
APP = ROOT / "r1-pmv"
RESULTS = Path(__file__).resolve().parent / "pg12"
SUPPORT = Path(__file__).resolve().parent
PG_BIN = Path(r"C:\Program Files\PostgreSQL\18\bin")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_hashes() -> dict[str, str | None]:
    protected = [
        *APP.glob("*.sqlite3"),
        *(
            p
            for p in (RESULTS / "datos").rglob("*.sqlite3")
            if p.parent.name.startswith(("etapa00", "etapa01", "etapa02", "etapa03", "etapa04", "etapa05", "etapa06", "etapa07"))
        ),
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]
    return {str(p.relative_to(ROOT)): digest(p) if p.exists() else None for p in protected}


def run_cmd(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as f:
        res = subprocess.run(
            cmd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=f,
            stderr=subprocess.STDOUT,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        f.seek(0)
        out = f.read()
    return subprocess.CompletedProcess(cmd, res.returncode, stdout=out, stderr=out)


def main() -> int:
    start_hashes = protected_hashes()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)
    out_dir = RESULTS / "evidencias" / f"12-pg-{stamp}"
    run_dir = RESULTS / "datos" / f"etapa12-pg-{stamp}"
    out_dir.mkdir(parents=True)
    run_dir.mkdir(parents=True)
    (run_dir / "marker.json").write_text(json.dumps({"run": run_dir.name}), encoding="utf-8")
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")

    pg_root = (RESULTS / f"audit12-pg-{secrets.token_hex(8)}").resolve()
    assert pg_root.is_relative_to(RESULTS.resolve())
    pg_root.mkdir(exist_ok=False)
    pg_data = pg_root / "data"
    pg_pass = secrets.token_urlsafe(24)
    pw_file = pg_root / "pw.txt"
    pw_file.write_text(pg_pass, encoding="utf-8")
    db_name = f"audit12_pg_{secrets.token_hex(4)}"

    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        pg_port = s.getsockname()[1]

    report: dict = {"stamp_utc": stamp, "pg_port": pg_port, "db_name": db_name}
    pg_started = False

    try:
        init_res = run_cmd([
            str(PG_BIN / "initdb.exe"),
            "-D", str(pg_data),
            "-U", "audit12_pg",
            "--pwfile", str(pw_file),
            "--auth-host=scram-sha-256",
            "--auth-local=scram-sha-256",
            "-E", "UTF8",
            "--locale=C",
        ])
        if init_res.returncode != 0:
            raise RuntimeError(f"initdb failed: {init_res.stderr}")
        pw_file.unlink(missing_ok=True)

        start_res = run_cmd([
            str(PG_BIN / "pg_ctl.exe"),
            "-D", str(pg_data),
            "-l", str(pg_root / "postgres.log"),
            "-o", f"-h 127.0.0.1 -p {pg_port} -c log_statement=none",
            "-w",
            "start",
        ])
        if start_res.returncode != 0:
            raise RuntimeError(f"pg_ctl start failed: {start_res.stderr}\n{start_res.stdout}")
        pg_started = True

        pg_env = os.environ.copy()
        pg_env["PGPASSWORD"] = pg_pass
        createdb_res = run_cmd(
            [str(PG_BIN / "createdb.exe"), "-h", "127.0.0.1", "-p", str(pg_port), "-U", "audit12_pg", db_name],
            env=pg_env,
        )
        if createdb_res.returncode != 0:
            raise RuntimeError(f"createdb failed: {createdb_res.stderr}")

        # Configure isolated Django on PG 18.4 (blocking .env)
        os.environ.update(
            AUDIT12_RUN_DIR=str(run_dir),
            AUDIT12_OUT=str(out_dir),
            AUDIT12_DEFAULT_COOKIES="1",
            AUDIT12_PG_ENGINE="django.db.backends.postgresql",
            AUDIT12_PG_NAME=db_name,
            AUDIT12_PG_USER="audit12_pg",
            AUDIT12_PG_PASSWORD=pg_pass,
            AUDIT12_PG_HOST="127.0.0.1",
            AUDIT12_PG_PORT=str(pg_port),
            DJANGO_SETTINGS_MODULE="audit12_settings",
        )
        # Write a small PG settings overlay inside run_dir without touching audit12_settings.py
        pg_settings_mod = run_dir / "audit12_pg_settings.py"
        pg_settings_mod.write_text(
            "from audit12_settings import *\n"
            "import os\n"
            "DATABASES = {\n"
            "    'default': {\n"
            "        'ENGINE': 'django.db.backends.postgresql',\n"
            "        'NAME': os.environ['AUDIT12_PG_NAME'],\n"
            "        'USER': os.environ['AUDIT12_PG_USER'],\n"
            "        'PASSWORD': os.environ['AUDIT12_PG_PASSWORD'],\n"
            "        'HOST': os.environ['AUDIT12_PG_HOST'],\n"
            "        'PORT': os.environ['AUDIT12_PG_PORT'],\n"
            "    }\n"
            "}\n",
            encoding="utf-8",
        )
        os.environ["DJANGO_SETTINGS_MODULE"] = "audit12_pg_settings"
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(APP))
        sys.path.insert(0, str(SUPPORT))
        sys.path.insert(0, str(run_dir))
        import django
        django.setup()

        from django.core.management import call_command
        from django.db import close_old_connections, connection
        from django.test import Client
        from django.test.utils import CaptureQueriesContext, setup_test_environment
        from django.urls import reverse
        from django.utils import timezone as tz

        setup_test_environment()

        from cash.models import CashRegister, CashShift
        from cash.services import close_cash_shift, open_cash_shift
        from catalog.models import Category, Product
        from identity.models import Account, Role
        from inventory.services import LotInput, confirm_initial_load
        from sales.models import Sale, SaleCounter, SaleDraft
        from sales.services import add_product_to_draft, checkout_sale

        with contextlib.redirect_stdout(io.StringIO()):
            call_command("migrate", interactive=False, verbosity=0)

        with connection.cursor() as cur:
            cur.execute("SELECT version(), current_database()")
            report["pg_version"] = cur.fetchone()[0]

        admin_role, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
        seller_role, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})
        wh_role, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})

        pw = secrets.token_urlsafe(16) + "Pg1!"
        admin = Account.objects.create_user("adm@pg.invalid", pw, display_name="Admin PG12", role=admin_role)
        wh = Account.objects.create_user("wh@pg.invalid", pw, display_name="WH PG12", role=wh_role)
        s1 = Account.objects.create_user("s1@pg.invalid", pw, display_name="Seller 1 PG", role=seller_role)
        s2 = Account.objects.create_user("s2@pg.invalid", pw, display_name="Seller 2 PG", role=seller_role)
        reg = CashRegister.objects.create(code="CAJA-01")
        cat = Category.objects.create(name="Cat PG12")
        prod = Product.objects.create(category=cat, name="Producto PG12", barcode="7759990001", sale_price=Decimal("10.00"))
        confirm_initial_load(actor=wh, product=prod, lots=[LotInput("LPG-1", 50, Decimal("5.0000"), tz.localdate() + timedelta(days=30))])

        # Shift 1 & Sale 1 (Lima 2026-11-10 23:59:59) + Shift 2 & Sale 2 (2026-11-11 00:00:00)
        sh1 = open_cash_shift(actor=s1, opening_amount=Decimal("50.00"))
        d1 = add_product_to_draft(actor=s1, product_id=prod.pk, quantity=2)
        sale1 = checkout_sale(actor=s1, draft_id=d1.pk, cash_received=Decimal("20.00"), idempotency_key=uuid.uuid4())
        close_cash_shift(actor=s1, counted_amount=Decimal("70.00"))

        sh2 = open_cash_shift(actor=s2, opening_amount=Decimal("30.00"))
        d2 = add_product_to_draft(actor=s2, product_id=prod.pk, quantity=3)
        sale2 = checkout_sale(
            actor=s2, draft_id=d2.pk, cash_received=Decimal("30.00"),
            discount_amount=Decimal("5.00"), idempotency_key=uuid.uuid4(),
        )
        close_cash_shift(actor=s2, counted_amount=Decimal("55.00"))

        lima = ZoneInfo("America/Lima")
        Sale.objects.filter(pk=sale1.pk).update(confirmed_at=datetime(2026, 11, 10, 23, 59, 59, tzinfo=lima))
        Sale.objects.filter(pk=sale2.pk).update(confirmed_at=datetime(2026, 11, 11, 0, 0, 0, tzinfo=lima))
        CashShift.objects.filter(pk=sh1.pk).update(opened_at=datetime(2026, 11, 10, 23, 55, 0, tzinfo=lima))
        CashShift.objects.filter(pk=sh2.pk).update(opened_at=datetime(2026, 11, 11, 0, 0, 0, tzinfo=lima))

        # 1) NUL (\x00) safety on PG 18.4 across ALL filter parameters
        c_adm = Client()
        c_adm.force_login(admin)
        nul_cases = {}
        for name, url, params in [
            ("sales_corr_nul", reverse("sales-history"), {"correlativo": "V-\x00"}),
            ("sales_fecha_nul", reverse("sales-history"), {"fecha": "\x00"}),
            ("sales_desde_nul", reverse("sales-history"), {"fecha_desde": "2026-\x00"}),
            ("sales_vendedor_nul", reverse("sales-history"), {"vendedor": "\x00"}),
            ("sales_turno_nul", reverse("sales-history"), {"turno": "\x00"}),
            ("cash_desde_nul", reverse("cash-shift-history"), {"fecha_desde": "2026-\x00"}),
            ("cash_hasta_nul", reverse("cash-shift-history"), {"fecha_hasta": "\x00"}),
            ("cash_vendedor_nul", reverse("cash-shift-history"), {"vendedor": "\x00"}),
        ]:
            resp = c_adm.get(url, params)
            nul_cases[name] = {
                "status": resp.status_code,
                "has_error": "caracteres no válidos" in resp.content.decode("utf-8"),
            }
            assert resp.status_code == 200 and nul_cases[name]["has_error"], f"Failed NUL case {name}"
        report["nul_cases"] = nul_cases

        # 2) Lima boundary check on PG
        r10 = c_adm.get(reverse("sales-history"), {"fecha": "2026-11-10"})
        r11 = c_adm.get(reverse("sales-history"), {"fecha_desde": "2026-11-11", "fecha_hasta": "2026-11-11"})
        r_ch11 = c_adm.get(reverse("cash-shift-history"), {"fecha_desde": "2026-11-11", "fecha_hasta": "2026-11-11"})
        report["lima_boundary"] = {
            "sales_10": [s.correlative for s in r10.context["sales"]],
            "sales_11": [s.correlative for s in r11.context["sales"]],
            "shifts_11_collected": [str(sh.sales_collected) for sh in r_ch11.context["shifts"]],
        }
        assert report["lima_boundary"]["sales_10"] == [sale1.correlative]
        assert report["lima_boundary"]["sales_11"] == [sale2.correlative]
        assert report["lima_boundary"]["shifts_11_collected"] == ["25.00"]

        # 3) Query counts + N+1 invariance on PG 18.4 + EXPLAIN JSON
        with CaptureQueriesContext(connection) as q_ch1:
            r_ch_u1 = c_adm.get(reverse("cash-shift-history"))
        with CaptureQueriesContext(connection) as q_sh1:
            r_sh_u1 = c_adm.get(reverse("sales-history"))

        sh_open = open_cash_shift(actor=s1, opening_amount=Decimal("25.00"))
        for _ in range(15):
            d_ex = add_product_to_draft(actor=s1, product_id=prod.pk, quantity=1)
            checkout_sale(actor=s1, draft_id=d_ex.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4())

        with CaptureQueriesContext(connection) as q_ch2:
            r_ch_u2 = c_adm.get(reverse("cash-shift-history"))
        with CaptureQueriesContext(connection) as q_sh2:
            r_sh_u2 = c_adm.get(reverse("sales-history"))

        report["query_counts"] = {
            "cash_history_before": len(q_ch1),
            "cash_history_after_15_sales": len(q_ch2),
            "sales_history_before": len(q_sh1),
            "sales_history_after_15_sales": len(q_sh2),
        }
        assert len(q_ch1) == 4 and len(q_ch2) == 4, f"Expected 4 queries on cash history, got {len(q_ch1)} / {len(q_ch2)}"
        assert len(q_sh1) == len(q_sh2), f"N+1 detected in sales_history: {len(q_sh1)} vs {len(q_sh2)}"

        # Capture EXPLAIN (FORMAT JSON) of main list queries
        cash_list_sql = [q["sql"] for q in q_ch2 if '"cash_cashshift"' in q["sql"]][-1]
        sales_list_sql = [q["sql"] for q in q_sh2 if '"sales_sale"' in q["sql"] and "ORDER BY" in q["sql"]][-1]
        explain_cash = None
        explain_sales = None
        with connection.cursor() as cur:
            cur.execute("EXPLAIN (FORMAT JSON) " + cash_list_sql)
            explain_cash = cur.fetchone()[0]
            cur.execute("EXPLAIN (FORMAT JSON) " + sales_list_sql)
            explain_sales = cur.fetchone()[0]
        report["explain"] = {"cash_shift_history_list": explain_cash, "sales_history_list": explain_sales}

        # 4) Concurrent READ COMMITTED checkout + idempotent HTTP retry recovery
        d_conc = add_product_to_draft(actor=s1, product_id=prod.pk, quantity=1)
        c_s1 = Client()
        c_s1.force_login(s1)
        rev = c_s1.get(reverse("sales-checkout")).context["form"].initial
        idem_conc = rev["idempotency_key"]
        sig_conc = rev["draft_signature"]
        sub_conc = rev["expected_subtotal"]

        results_t = []
        barrier = threading.Barrier(2)

        def worker():
            close_old_connections()
            cl = Client()
            cl.force_login(s1)
            barrier.wait(timeout=5)
            resp = cl.post(
                reverse("sales-checkout"),
                {
                    "cash_received": "10.00",
                    "discount_amount": "",
                    "idempotency_key": str(idem_conc),
                    "expected_subtotal": str(sub_conc),
                    "draft_signature": sig_conc,
                },
            )
            results_t.append((resp.status_code, getattr(resp, "url", None)))
            close_old_connections()

        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        t1.start()
        t2.start()
        t1.join(timeout=15)
        t2.join(timeout=15)
        conc_sales = Sale.objects.filter(idempotency_key=idem_conc)
        assert conc_sales.count() == 1, f"Expected 1 concurrent sale, got {conc_sales.count()}"
        assert len(results_t) == 2 and not t1.is_alive() and not t2.is_alive(), "Both independent workers must finish"
        assert all(code == 302 for code, _ in results_t), f"Expected both threads to recover 302 receipt, got {results_t}"
        report["concurrent_checkout_retry"] = {"results": results_t, "sale_count_for_key": conc_sales.count()}

        close_old_connections()
        connection.close()
    finally:
        if pg_started:
            run_cmd([str(PG_BIN / "pg_ctl.exe"), "-D", str(pg_data), "-m", "fast", "stop"])
        # Clúster propio detenido conservado como evidencia; sin borrado recursivo.
        report["cluster_retained"] = str(pg_root.relative_to(ROOT))

    # Verify ephemeral PG port closed
    with socket.socket() as chk:
        port_closed = chk.connect_ex(("127.0.0.1", pg_port)) != 0
    end_hashes = {
        k: (digest(ROOT / k) if (ROOT / k).exists() else None) == v for k, v in start_hashes.items()
    }
    report["port_closed"] = port_closed
    report["protected_unchanged"] = all(end_hashes.values())
    (out_dir / "pg-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "evidence": str(out_dir.relative_to(ROOT)),
        "port_closed": port_closed,
        "protected_unchanged": report["protected_unchanged"],
        "query_counts": report.get("query_counts"),
        "concurrent_checkout_retry": report.get("concurrent_checkout_retry"),
    }, ensure_ascii=False, indent=2))
    return 0 if (port_closed and report["protected_unchanged"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
