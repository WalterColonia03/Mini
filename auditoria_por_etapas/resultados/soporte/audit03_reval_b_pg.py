"""Isolated PostgreSQL 18.4 Sublote B concurrency revalidation for Stage 03 (catalog + cross-module)."""
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
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

SUPPORT = Path(__file__).resolve().parent
RESULTS = SUPPORT.parent
ROOT = RESULTS.parent.parent
sys.path.insert(0, str(SUPPORT))
from audit03l_concurrency import contest  # noqa: E402

BIN = Path("C:/Program Files/PostgreSQL/18/bin")
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)
CLUSTER = (Path(tempfile.gettempdir()) / ("audit03-reval-b-pg-" + secrets.token_hex(8))).resolve()
CLUSTER.mkdir(exist_ok=False)
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(36)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit03_reval_b_" + secrets.token_hex(4)

with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]

protected = [
    *(
        p for p in (RESULTS / "datos").rglob("*.sqlite3")
        if p.parent.name.startswith(("03-", "etapa03"))
    ),
    ROOT / "08_Historias_de_Usuario.md",
    *sorted((ROOT / "r1-pmv" / "catalog").rglob("*.py")),
]
external_watch = [
    *(ROOT / "r1-pmv").glob("*.sqlite3"),
    ROOT / "07_Reglas_de_Negocio.md",
    ROOT / "09_Product_Backlog.md",
    ROOT / "03_Matriz_de_Trazabilidad_y_Pruebas.md",
]
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
hashes_before = {str(p.relative_to(ROOT)): digest(p) for p in protected if p.exists()}
ext_before = {str(p.relative_to(ROOT)): digest(p) for p in external_watch if p.exists()}
report = {"started_utc": STAMP, "port": PORT, "cases": []}


def pg(cmd, *args):
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as fh:
        res = subprocess.run(
            [str(BIN / (cmd + ".exe")), *map(str, args)],
            stdout=fh,
            stderr=fh,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        fh.seek(0)
        diag = fh.read().replace(PW, "[REDACTED]")
    if res.returncode != 0:
        raise RuntimeError(f"{cmd} failed: {diag[-800:]}")


started = False
configured = False
try:
    pg("initdb", "-D", DBDIR, "-U", "audit03revalb", "--pwfile", PWFILE, "--auth-host=scram-sha-256", "--auth-local=scram-sha-256", "--encoding=UTF8", "--locale=C")
    PWFILE.unlink()
    pg("pg_ctl", "-D", DBDIR, "-l", CLUSTER / "pg.log", "-o", f"-h 127.0.0.1 -p {PORT} -c log_statement=none -c log_min_error_statement=panic", "-w", "start")
    started = True

    import psycopg
    from psycopg import sql

    with psycopg.connect(host="127.0.0.1", port=PORT, user="audit03revalb", password=PW, dbname="postgres", autocommit=True) as conn:
        report["pg_version"] = conn.execute("SELECT version()").fetchone()[0]
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
            "USER": "audit03revalb",
            "PASSWORD": PW,
            "HOST": "127.0.0.1",
            "PORT": PORT,
            "CONN_MAX_AGE": 0,
            "OPTIONS": {"options": "-c statement_timeout=20000 -c lock_timeout=12000"},
        }
    }
    env.load_dotenv = loader
    import django

    django.setup()
    configured = True

    from django.core.management import call_command
    from django.db import connections
    from django.utils import timezone as dj_tz
    from cash.models import CashRegister
    from cash.services import open_cash_shift
    from catalog.models import Category, Product
    from catalog.services import (
        create_category,
        product_edit_snapshot,
        register_canned_product,
        toggle_category_status,
        toggle_product_availability,
        update_product,
    )
    from identity.models import Account, Role
    from inventory.models import Lot
    from inventory.services import LotInput, confirm_initial_load, register_stock_entry
    from sales.models import Sale
    from sales.services import add_product_to_draft, checkout_sale

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    r_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    r_sel, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

    a1 = Account.objects.create_user("pgb_a1@audit.invalid", None, role=r_admin, display_name="PGB A1")
    a2 = Account.objects.create_user("pgb_a2@audit.invalid", None, role=r_admin, display_name="PGB A2")
    wh = Account.objects.create_user("pgb_wh@audit.invalid", None, role=r_wh, display_name="PGB WH")
    sel = Account.objects.create_user("pgb_sel@audit.invalid", None, role=r_sel, display_name="PGB SEL")
    CashRegister.objects.create(code="CAJA-01", is_active=True)
    open_cash_shift(actor=sel, opening_amount=Decimal("100.00"))
    today = dj_tz.localdate()

    # Case 1: toggle_category_status(False) vs checkout_sale
    cat1 = create_category(actor=a1, name="Lácteos PGB")
    p1 = register_canned_product(
        actor=a1, name="Leche PGB 1L", barcode="PGB-001", barcode_type="INTERNAL",
        category=cat1, unit="UND", sale_price=Decimal("5.00"), minimum_stock=5,
    )
    confirm_initial_load(actor=wh, product=p1, lots=[LotInput("L1", 10, Decimal("3.00"), today + timedelta(days=40))])
    draft1 = add_product_to_draft(actor=sel, product_id=p1.pk, quantity=2)
    r1 = contest(
        lambda: str(toggle_category_status(actor=a1, category=cat1, is_active=False, expected_version=0).state_version),
        lambda: str(checkout_sale(actor=sel, draft_id=draft1.pk, cash_received=Decimal("10.00"), idempotency_key=uuid4()).correlative),
    )
    cat1.refresh_from_db()
    lot1 = Lot.objects.get(product=p1, number="L1")
    ok1 = (
        r1["winner"]["status"] == "committed"
        and r1["contender"]["status"] == "rejected"
        and cat1.is_active is False
        and Sale.objects.count() == 0
        and lot1.available_quantity == 10
    )
    report["cases"].append({"id": "PG-REVAL-B-DEACT-CAT-VS-CHECKOUT", "ok": ok1, "race": r1})

    # Reactivate cat1 and test Case 2: toggle_product_availability(False) vs checkout_sale
    toggle_category_status(actor=a1, category=cat1, is_active=True, expected_version=cat1.state_version)
    r2 = contest(
        lambda: str(toggle_product_availability(actor=a1, product=p1, is_active=False).is_active),
        lambda: str(checkout_sale(actor=sel, draft_id=draft1.pk, cash_received=Decimal("10.00"), idempotency_key=uuid4()).correlative),
    )
    p1.refresh_from_db()
    lot1.refresh_from_db()
    ok2 = (
        r2["winner"]["status"] == "committed"
        and r2["contender"]["status"] == "rejected"
        and p1.is_active is False
        and Sale.objects.count() == 0
        and lot1.available_quantity == 10
    )
    report["cases"].append({"id": "PG-REVAL-B-DEACT-PROD-VS-CHECKOUT", "ok": ok2, "race": r2})

    # Reactivate p1 and test Case 3: toggle_category_status(False) vs register_stock_entry
    toggle_product_availability(actor=a1, product=p1, is_active=True)
    r3 = contest(
        lambda: str(toggle_category_status(actor=a1, category=cat1, is_active=False, expected_version=cat1.state_version).state_version),
        lambda: str(register_stock_entry(actor=wh, product=p1, lots=[LotInput("L2", 5, Decimal("3.20"), today + timedelta(days=50))], idempotency_key=uuid4()).correlative),
    )
    cat1.refresh_from_db()
    ok3 = (
        r3["winner"]["status"] == "committed"
        and r3["contender"]["status"] == "rejected"
        and cat1.is_active is False
        and not Lot.objects.filter(product=p1, number="L2").exists()
    )
    report["cases"].append({"id": "PG-REVAL-B-DEACT-CAT-VS-STOCK-ENTRY", "ok": ok3, "race": r3})

    # Case 4: toggle_category_status(cat2, False) vs update_product(p1, category=cat2) -> never move into deactivated category
    cat2 = create_category(actor=a1, name="Destino PGB")
    snap_p1 = product_edit_snapshot(p1)
    r4 = contest(
        lambda: str(toggle_category_status(actor=a1, category=cat2, is_active=False, expected_version=0).state_version),
        lambda: str(update_product(
            actor=a2, product=p1, name=p1.name, barcode=p1.barcode, barcode_type=p1.barcode_type,
            sale_price=p1.sale_price, minimum_stock=p1.minimum_stock, category=cat2, expected_snapshot=snap_p1,
        ).category_id),
    )
    p1.refresh_from_db()
    cat2.refresh_from_db()
    ok4 = (
        r4["winner"]["status"] == "committed"
        and r4["contender"]["status"] == "rejected"
        and cat2.is_active is False
        and p1.category_id == cat1.pk
    )
    report["cases"].append({"id": "PG-REVAL-B-DEACT-TARGET-CAT-VS-UPDATE-PROD", "ok": ok4, "race": r4})

    # Case 5: Two concurrent blind toggles (is_active=None, matching UI POST without state_version) -> both succeed and bounce state!
    # Re-enable cat1 & verify p1 starts True
    assert p1.is_active is True
    r5 = contest(
        lambda: str(toggle_product_availability(actor=a1, product=p1, is_active=None).is_active),
        lambda: str(toggle_product_availability(actor=a2, product=p1, is_active=None).is_active),
    )
    p1.refresh_from_db()
    # Both committed, winner made it False, contender flipped it BACK to True!
    ok5 = (
        r5["winner"]["status"] == "committed"
        and r5["winner"]["value"] == "False"
        and r5["contender"]["status"] == "committed"
        and r5["contender"]["value"] == "True"
        and p1.is_active is True
    )
    report["cases"].append({"id": "PG-REVAL-B-OMITTED-TOGGLE-LOST-INTENT", "ok": ok5, "race": r5})

except Exception as exc:
    report["error"] = {"type": type(exc).__name__, "message": str(exc).replace(PW, "[REDACTED]")[:800]}
finally:
    if configured:
        connections.close_all()
    if started:
        pg("pg_ctl", "-D", DBDIR, "-m", "fast", "-w", "stop")
    with socket.socket() as s:
        report["port_closed"] = s.connect_ex(("127.0.0.1", PORT)) != 0
    ext_after = {str(p.relative_to(ROOT)): digest(p) for p in external_watch if p.exists()}
    report["protected_unchanged"] = {k: (digest(ROOT / k) == v) for k, v in hashes_before.items()}
    report["external_before"] = ext_before
    report["external_after"] = ext_after
    report["external_changed_keys"] = [k for k in ext_after if ext_before.get(k) != ext_after[k]]
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    out = RESULTS / "evidencias" / f"03-REVAL-B-pg-{STAMP}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({
        "evidence": str(out.relative_to(ROOT)),
        "cases": [{"id": c["id"], "ok": c["ok"], "lock_observed": c["race"]["lock_observed"], "wait_event": c["race"]["wait_event"]} for c in report["cases"]],
        "error": report.get("error"),
        "port_closed": report["port_closed"],
        "protected_unchanged": all(report["protected_unchanged"].values()),
        "external_changed_keys": report["external_changed_keys"],
    }, ensure_ascii=False, indent=2))
if report.get("error") or len(report["cases"]) != 5 or not all(c["ok"] for c in report["cases"]) or not report["port_closed"] or not all(report["protected_unchanged"].values()):
    raise SystemExit(1)
