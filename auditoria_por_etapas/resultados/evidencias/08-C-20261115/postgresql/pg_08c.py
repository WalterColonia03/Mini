"""08-C PostgreSQL 18.4: SIGKILL post-write, WAL crash recovery y PT-KARDEX-01."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / "r1-pmv" / "manage.py").exists())
R1 = ROOT / "r1-pmv"
BIN = Path("C:/Program Files/PostgreSQL/18/bin")
PY = Path(sys.executable)

STAMP = time.strftime("%Y-%m-%dT%H:%M:%S%z")
CLUSTER = (Path(tempfile.gettempdir()) / ("audit08c-pg-" + secrets.token_hex(8))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT08C_OWNED"
MARK.write_text(STAMP, encoding="utf-8")
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(32)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit08c_" + secrets.token_hex(4)
with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]


def pg(name: str, *args: object) -> str:
    assert MARK.read_text(encoding="utf-8") == STAMP
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as f:
        r = subprocess.run(
            [str(BIN / (name + ".exe")), *map(str, args)],
            stdout=f,
            stderr=f,
            timeout=90,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        f.seek(0)
        text = f.read().replace(PW, "[REDACTED]")
    if r.returncode:
        raise RuntimeError(f"{name}: {text[-1200:]}")
    return text


def run_child_sigkill(mode: str, actor_email: str, target_id: str, key_str: str) -> dict:
    flag = CLUSTER / f"{mode}.flag"
    child_code = f"""
import os, sys, time, uuid
from datetime import timedelta
from decimal import Decimal
sys.path.insert(0, {str(R1)!r})
os.environ.update(
    APP_ENV='test',
    DJANGO_DEBUG='false',
    DJANGO_SECRET_KEY='child-secret-08c',
    DJANGO_SETTINGS_MODULE='config.settings',
    DJANGO_ALLOWED_HOSTS='127.0.0.1,testserver',
    AUDIT08C_PG_NAME={DBNAME!r},
    AUDIT08C_PG_PORT={str(PORT)!r},
    AUDIT08C_PG_USER='audit08c',
    AUDIT08C_PG_PW={PW!r},
)
from config import env
env.load_dotenv = lambda path=None: None
from django.conf import settings
import django
settings.DATABASES = {{'default': {{
    'ENGINE': 'django.db.backends.postgresql',
    'NAME': os.environ['AUDIT08C_PG_NAME'],
    'USER': os.environ['AUDIT08C_PG_USER'],
    'PASSWORD': os.environ['AUDIT08C_PG_PW'],
    'HOST': '127.0.0.1',
    'PORT': int(os.environ['AUDIT08C_PG_PORT']),
    'CONN_MAX_AGE': 0,
}}}}
django.setup()
from django.utils import timezone
from identity.models import Account
from catalog.models import Product
from inventory.models import Lot, StockWriteOff, PhysicalAdjustment
from inventory.services import write_off_stock, register_physical_adjustment

actor = Account.objects.get(email={actor_email!r})
orig_lot_save = Lot.save
orig_prod_save = Product.save

if {mode!r} == 'writeoff_postwrite':
    def patched_lot_save(self, *args, **kwargs):
        res = orig_lot_save(self, *args, **kwargs)
        # StockWriteOff row and updated Lot row have both executed in the open tx!
        assert StockWriteOff.objects.filter(idempotency_key={key_str!r}).exists()
        open({str(flag)!r}, 'w').write('WROTE_IN_TX')
        time.sleep(30)
        return res
    Lot.save = patched_lot_save
    lot = Lot.objects.get(pk={target_id!r})
    write_off_stock(actor=actor, lot=lot, quantity=3, reason=StockWriteOff.Reason.THEFT, notes='SIGKILL probe', idempotency_key=uuid.UUID({key_str!r}))
elif {mode!r} == 'adjustment_newlot_postwrite':
    def patched_prod_save(self, *args, **kwargs):
        # PhysicalAdjustment and new Lot have both executed before final average_cost save commits!
        assert PhysicalAdjustment.objects.filter(idempotency_key={key_str!r}).exists()
        assert Lot.objects.filter(product_id={target_id!r}, number_normalized='L-SIGKILL-NEW').exists()
        open({str(flag)!r}, 'w').write('WROTE_IN_TX')
        time.sleep(30)
        return orig_prod_save(self, *args, **kwargs)
    Product.save = patched_prod_save
    prod = Product.objects.get(pk={target_id!r})
    register_physical_adjustment(
        actor=actor, product=prod, delta=4, reason='SIGKILL new lot Q0',
        number='L-SIGKILL-NEW', expiration_date=timezone.localdate() + timedelta(days=60),
        unit_cost=Decimal('3.2500'), cost_source='Factura SIGKILL', idempotency_key=uuid.UUID({key_str!r}),
    )
"""
    script = CLUSTER / f"child_{mode}.py"
    script.write_text(child_code, encoding="utf-8")
    proc = subprocess.Popen(
        [str(PY), str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    t0 = time.monotonic()
    while not flag.exists() and time.monotonic() - t0 < 25:
        if proc.poll() is not None:
            out, err = proc.communicate()
            raise RuntimeError(f"Child exited prematurely ({proc.returncode}): {err.decode(errors='replace')}")
        time.sleep(0.05)
    assert flag.exists(), "Child did not reach post-write barrier in time"

    import psycopg
    with psycopg.connect(host="127.0.0.1", port=PORT, user="audit08c", password=PW, dbname=DBNAME) as conn:
        rows = conn.execute(
            "SELECT a.pid, l.relation::regclass::text, l.mode "
            "FROM pg_stat_activity a JOIN pg_locks l ON l.pid = a.pid "
            "WHERE a.datname = %s AND a.pid <> pg_backend_pid() AND l.relation IS NOT NULL AND l.mode LIKE '%%Exclusive%%'",
            (DBNAME,),
        ).fetchall()
    proc.kill()
    rc = proc.wait(timeout=10)
    return {
        "flag_state": flag.read_text(encoding="utf-8"),
        "observed_pg_exclusive_locks_before_kill": [{"pid": r[0], "relation": r[1], "mode": r[2]} for r in rows],
        "os_kill_returncode": rc,
    }


started = False
report = {
    "stage": "08-C",
    "started": STAMP,
    "postgres_version": None,
    "port": PORT,
    "tests": {},
}
try:
    pg("initdb", "-D", DBDIR, "-U", "audit08c", "--pwfile", PWFILE, "--auth-host=scram-sha-256", "--auth-local=scram-sha-256", "--encoding=UTF8", "--locale=C")
    PWFILE.unlink()
    pg("pg_ctl", "-D", DBDIR, "-l", CLUSTER / "postgres.log", "-o", f"-h 127.0.0.1 -p {PORT}", "-w", "start")
    started = True

    import psycopg
    from psycopg import sql
    with psycopg.connect(host="127.0.0.1", port=PORT, user="audit08c", password=PW, dbname="postgres", autocommit=True) as c:
        report["postgres_version"] = c.execute("SELECT version()").fetchone()[0]
        c.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DBNAME)))

    sys.path.insert(0, str(R1))
    os.environ.update(APP_ENV="test", DJANGO_DEBUG="false", DJANGO_SECRET_KEY=secrets.token_urlsafe(32), DJANGO_SETTINGS_MODULE="config.settings", DJANGO_ALLOWED_HOSTS="127.0.0.1,testserver")
    from config import env
    env.load_dotenv = lambda path=None: None
    from django.conf import settings
    settings.DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DBNAME,
        "USER": "audit08c",
        "PASSWORD": PW,
        "HOST": "127.0.0.1",
        "PORT": PORT,
        "CONN_MAX_AGE": 0,
        "OPTIONS": {"options": "-c statement_timeout=30000 -c lock_timeout=15000"},
    }}
    import django
    django.setup()
    from django.core.management import call_command
    from django.db import connection, connections
    from django.test import Client
    from django.test.utils import CaptureQueriesContext
    from django.utils import timezone

    call_command("migrate", verbosity=0)

    from catalog.models import Category, Product
    from cash.models import CashRegister, CashShift
    from identity.models import Account, Role
    from inventory.models import Lot, PhysicalAdjustment, StockWriteOff, Supplier
    from inventory.services import LotInput, confirm_initial_load, register_physical_adjustment, register_stock_entry, write_off_stock
    from sales.services import add_product_to_draft, checkout_sale

    r_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    r_sel, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})
    u_admin = Account.objects.create_user(email="adm_pg@local.test", password="Password123!", display_name="Admin PG", role=r_admin, is_active=True)
    u_wh = Account.objects.create_user(email="wh_pg@local.test", password="Password123!", display_name="Almacenero PG", role=r_wh, is_active=True)
    u_sel = Account.objects.create_user(email="sel_pg@local.test", password="Password123!", display_name="Vendedor PG", role=r_sel, is_active=True)

    cat = Category.objects.create(name="PG Categoria 08C")
    sup = Supplier.objects.create(name="PG Proveedor 08C SAC", ruc="20600000899", phone="999000899")
    today = timezone.localdate()

    # Product for SIGKILL writeoff
    p1 = Product.objects.create(name="Prod SIGKILL WO", barcode="7750000008801", category=cat, unit=Product.Unit.UNIT, sale_price=Decimal("5.00"), minimum_stock=2, is_active=True)
    l1_load = confirm_initial_load(actor=u_wh, product=p1, lots=[LotInput(number="L-SK-1", quantity=20, unit_cost=Decimal("2.0000"), expiration_date=today + timedelta(days=90))], supplier=sup)
    lot1 = l1_load.lines.first().lot

    # Product for SIGKILL Q=0 new lot adjustment
    p2 = Product.objects.create(name="Prod SIGKILL Q0", barcode="7750000008802", category=cat, unit=Product.Unit.UNIT, sale_price=Decimal("7.00"), minimum_stock=2, is_active=True)
    confirm_initial_load(actor=u_wh, product=p2, lots=[LotInput(number="L-SK0", quantity=1, unit_cost=Decimal("2.0000"), expiration_date=today + timedelta(days=90))], supplier=sup)
    write_off_stock(actor=u_wh, lot=p2.lots.first(), quantity=1, reason=StockWriteOff.Reason.THEFT, notes="Vaciar Q0")
    baseline_wo_count = StockWriteOff.objects.count()  # 1

    # 1. SIGKILL post-write write_off_stock
    k_wo = uuid.uuid4()
    kill_wo_info = run_child_sigkill("writeoff_postwrite", "wh_pg@local.test", str(lot1.pk), str(k_wo))
    lot1.refresh_from_db()
    p1.refresh_from_db()
    rollback_clean = (
        StockWriteOff.objects.count() == baseline_wo_count
        and not StockWriteOff.objects.filter(idempotency_key=k_wo).exists()
        and lot1.available_quantity == 20
        and p1.average_cost == Decimal("2.0000")
    )
    recovered_wo = write_off_stock(actor=u_wh, lot=lot1, quantity=3, reason=StockWriteOff.Reason.THEFT, notes="SIGKILL probe", idempotency_key=k_wo)
    lot1.refresh_from_db()
    report["tests"]["PG08C_SIGKILL_01_writeoff"] = {
        **kill_wo_info,
        "rollback_clean": rollback_clean,
        "recovery_correlativo": recovered_wo.correlativo,
        "lot_qty_after_recovery": lot1.available_quantity,
    }

    # 2. SIGKILL post-write register_physical_adjustment (new lot Q=0)
    k_adj = uuid.uuid4()
    kill_adj_info = run_child_sigkill("adjustment_newlot_postwrite", "adm_pg@local.test", str(p2.pk), str(k_adj))
    p2.refresh_from_db()
    adj_rollback_clean = (
        PhysicalAdjustment.objects.count() == 0
        and not Lot.objects.filter(product=p2, number_normalized="L-SIGKILL-NEW").exists()
        and p2.average_cost == Decimal("0.0000")
    )
    recovered_adj = register_physical_adjustment(
        actor=u_admin, product=p2, delta=4, reason="SIGKILL new lot Q0",
        number="L-SIGKILL-NEW", expiration_date=today + timedelta(days=60),
        unit_cost=Decimal("3.2500"), cost_source="Factura SIGKILL", idempotency_key=k_adj,
    )
    p2.refresh_from_db()
    report["tests"]["PG08C_SIGKILL_02_adjustment_newlot"] = {
        **kill_adj_info,
        "rollback_clean": adj_rollback_clean,
        "recovery_adjustment_id": str(recovered_adj.pk),
        "p2_avg_cost_after_recovery": str(p2.average_cost),
        "p2_lots_count_after_recovery": Lot.objects.filter(product=p2).count(),
    }

    # 3. WAL immediate crash recovery (pg_ctl stop -m immediate)
    connections.close_all()
    pg("pg_ctl", "-D", DBDIR, "-m", "immediate", "-w", "stop")
    started = False
    pg("pg_ctl", "-D", DBDIR, "-l", CLUSTER / "postgres.log", "-o", f"-h 127.0.0.1 -p {PORT}", "-w", "start")
    started = True
    with psycopg.connect(host="127.0.0.1", port=PORT, user="audit08c", password=PW, dbname=DBNAME) as conn:
        table_count = conn.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema='public'").fetchone()[0]
    report["tests"]["PG08C_WAL_IMMEDIATE_03"] = {
        "public_tables": table_count,
        "writeoffs_persisted": StockWriteOff.objects.count(),
        "adjustments_persisted": PhysicalAdjustment.objects.count(),
        "recovered_wo_present": StockWriteOff.objects.filter(pk=recovered_wo.pk).exists(),
        "recovered_adj_present": PhysicalAdjustment.objects.filter(pk=recovered_adj.pk).exists(),
    }

    # 4. PT-KARDEX-01 real PG 18.4 volume test (2,011 events + concurrent read during active lock)
    p_vol = Product.objects.create(name="Prod Kardex Vol PG", barcode="7750000008899", category=cat, unit=Product.Unit.UNIT, sale_price=Decimal("10.00"), minimum_stock=5, is_active=True)
    confirm_initial_load(actor=u_wh, product=p_vol, lots=[LotInput(number="PGVOL-0", quantity=2000, unit_cost=Decimal("4.0000"), expiration_date=today + timedelta(days=365))], supplier=sup)
    for idx in range(1, 11):
        register_stock_entry(actor=u_wh, product=p_vol, lots=[LotInput(number=f"PGVOL-{idx}", quantity=500, unit_cost=Decimal("4.2000"), expiration_date=today + timedelta(days=365 + idx))], supplier=sup)
    reg = CashRegister.objects.create(name="CAJA-PG-08C")
    CashShift.objects.create(cash_register=reg, seller=u_sel, opening_amount=Decimal("100.00"), status=CashShift.Status.OPEN)
    for _ in range(1500):
        d = add_product_to_draft(actor=u_sel, product_id=p_vol.pk, quantity=1)
        checkout_sale(actor=u_sel, draft_id=d.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4())
    lot_v = p_vol.lots.filter(available_quantity__gt=350).first()
    for _ in range(300):
        write_off_stock(actor=u_wh, lot=lot_v, quantity=1, reason=StockWriteOff.Reason.THEFT, notes="PG merma vol", idempotency_key=uuid.uuid4())
    for j in range(200):
        register_physical_adjustment(actor=u_admin, lot=lot_v, delta=(1 if j % 2 == 0 else -1), reason=f"PG adj {j}", idempotency_key=uuid.uuid4())

    client = Client()
    client.force_login(u_admin)

    def bench_url(url: str) -> dict:
        with CaptureQueriesContext(connection) as ctx:
            t0 = time.perf_counter()
            r = client.get(url)
            ms = (time.perf_counter() - t0) * 1000.0
        body = r.content.decode()
        cnt = re.search(r'data-testid="filtered-count">(\d+)<', body)
        open_b = re.search(r'data-testid="opening-balance">([^<]+)<', body)
        close_b = re.search(r'data-testid="closing-balance">([^<]+)<', body)
        return {
            "url": url,
            "status": r.status_code,
            "queries": len(ctx),
            "elapsed_ms": round(ms, 2),
            "html_bytes": len(r.content),
            "filtered_count": int(cnt.group(1)) if cnt else None,
            "opening": open_b.group(1) if open_b else None,
            "closing": close_b.group(1) if close_b else None,
        }

    report["tests"]["PG08C_PT_KARDEX_01"] = {
        "page_1": bench_url(f"/inventario/productos/{p_vol.pk}/movimientos/"),
        "page_last_81": bench_url(f"/inventario/productos/{p_vol.pk}/movimientos/?page=81"),
        "filter_ajuste": bench_url(f"/inventario/productos/{p_vol.pk}/movimientos/?tipo=ajuste"),
    }

finally:
    try:
        from django.db import connections
        connections.close_all()
    except Exception:
        pass
    if started:
        try:
            pg("pg_ctl", "-D", DBDIR, "-m", "fast", "-w", "stop")
        except Exception:
            pass
    try:
        shutil.rmtree(CLUSTER, ignore_errors=True)
    except Exception:
        pass

out_file = HERE / "pg_08c_resultado.json"
out_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({
    "ok": True,
    "sigkill_wo_clean": report["tests"].get("PG08C_SIGKILL_01_writeoff", {}).get("rollback_clean"),
    "sigkill_adj_clean": report["tests"].get("PG08C_SIGKILL_02_adjustment_newlot", {}).get("rollback_clean"),
    "wal_tables": report["tests"].get("PG08C_WAL_IMMEDIATE_03", {}).get("public_tables"),
    "kardex_p1": report["tests"].get("PG08C_PT_KARDEX_01", {}).get("page_1"),
}, ensure_ascii=False))
