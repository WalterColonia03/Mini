"""Isolated PostgreSQL 18.4 concurrency revalidation for Stage 03 (catalog)."""
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

BIN = Path(os.environ.get("AUDIT03_PG_BIN", "C:/Program Files/PostgreSQL/18/bin"))
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)
CLUSTER = (Path(tempfile.gettempdir()) / ("audit03-reval-pg-" + secrets.token_hex(8))).resolve()
CLUSTER.mkdir(exist_ok=False)
MARK = CLUSTER / "AUDIT03_REVAL_PG"
MARK.write_text(STAMP, encoding="utf-8")
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(36)
PWFILE = CLUSTER / "password"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = "audit03_reval_" + secrets.token_hex(4)

with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]

protected = [
    *(ROOT / "r1-pmv").glob("*.sqlite3"),
    *(p for p in (RESULTS / "datos").rglob("*.sqlite3") if p.parent.name.startswith(("03-", "etapa00", "etapa01", "etapa02", "etapa03", "01-"))),
    ROOT / "08_Historias_de_Usuario.md",
    ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
]
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
hashes_before = {str(p.relative_to(ROOT)): digest(p) for p in protected}
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
    pg("initdb", "-D", DBDIR, "-U", "audit03reval", "--pwfile", PWFILE, "--auth-host=scram-sha-256", "--auth-local=scram-sha-256", "--encoding=UTF8", "--locale=C")
    PWFILE.unlink()
    pg("pg_ctl", "-D", DBDIR, "-l", CLUSTER / "pg.log", "-o", f"-h 127.0.0.1 -p {PORT} -c log_statement=none -c log_min_error_statement=panic", "-w", "start")
    started = True

    import psycopg
    from psycopg import sql

    with psycopg.connect(host="127.0.0.1", port=PORT, user="audit03reval", password=PW, dbname="postgres", autocommit=True) as conn:
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
            "USER": "audit03reval",
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
    from django.db import connection, connections
    from django.utils import timezone as dj_tz
    from cash.models import CashRegister
    from cash.services import open_cash_shift
    from catalog.models import Category, Product, ProductBarcodeKey
    from catalog.services import (
        create_category,
        product_edit_snapshot,
        register_canned_product,
        toggle_category_status,
        update_product,
    )
    from identity.models import Account, Role
    from inventory.services import LotInput, confirm_initial_load
    from sales.services import add_product_to_draft, checkout_sale

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    r_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    r_sel, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

    a1 = Account.objects.create_user("pg_a1@audit.invalid", None, role=r_admin, display_name="PG A1")
    a2 = Account.objects.create_user("pg_a2@audit.invalid", None, role=r_admin, display_name="PG A2")
    wh = Account.objects.create_user("pg_wh@audit.invalid", None, role=r_wh, display_name="PG WH")
    sel = Account.objects.create_user("pg_sel@audit.invalid", None, role=r_sel, display_name="PG SEL")
    CashRegister.objects.create(code="CAJA-01", is_active=True)

    # Case 1: Concurrent category create duplicate (normalized spaces/case)
    c1 = contest(
        lambda: str(create_category(actor=a1, name="  Lácteos   Frescos ").pk),
        lambda: str(create_category(actor=a2, name="lácteos frescos").pk),
    )
    ok1 = (
        c1["winner"]["status"] == "committed"
        and c1["contender"]["status"] == "rejected"
        and Category.objects.filter(name_normalized="lácteos frescos").count() == 1
    )
    report["cases"].append({"id": "PG-REVAL-CAT-DUP", "ok": ok1, "race": c1})

    # Case 2: Concurrent toggle_category_status from same version 0 -> stale rejected
    cat_lac = Category.objects.get(name_normalized="lácteos frescos")
    c2 = contest(
        lambda: str(toggle_category_status(actor=a1, category=cat_lac, is_active=False, expected_version=0).state_version),
        lambda: str(toggle_category_status(actor=a2, category=cat_lac, is_active=False, expected_version=0).state_version),
    )
    cat_lac.refresh_from_db()
    ok2 = (
        c2["winner"]["status"] == "committed"
        and c2["contender"]["status"] == "rejected"
        and cat_lac.state_version == 1
        and cat_lac.is_active is False
    )
    report["cases"].append({"id": "PG-REVAL-CAT-VERSION", "ok": ok2, "race": c2})
    toggle_category_status(actor=a1, category=cat_lac, is_active=True, expected_version=1)

    # Case 3: Concurrent duplicate normalized product name with distinct barcodes
    cat_other = create_category(actor=a1, name="Abarrotes PG")
    c3 = contest(
        lambda: str(register_canned_product(actor=a1, name="Atún   PG  170g", barcode="PG-N1", barcode_type="INTERNAL", category=cat_lac, unit="UND", sale_price=Decimal("5.00"), minimum_stock=5).pk),
        lambda: str(register_canned_product(actor=a2, name="ATÚN pg 170G", barcode="PG-N2", barcode_type="INTERNAL", category=cat_other, unit="UND", sale_price=Decimal("5.00"), minimum_stock=5).pk),
    )
    ok3 = (
        c3["winner"]["status"] == "committed"
        and c3["contender"]["status"] == "rejected"
        and Product.objects.filter(search_name="atún pg 170g").count() == 1
    )
    report["cases"].append({"id": "PG-REVAL-PROD-NAME-DUP", "ok": ok3, "race": c3})

    # Case 4: Concurrent GTIN UPC-12 vs EAN-13 padded race
    c4 = contest(
        lambda: str(register_canned_product(actor=a1, name="Aceite PG 1", barcode="012345678905", barcode_type="GTIN", category=cat_lac, unit="UND", sale_price=Decimal("8.00"), minimum_stock=5).pk),
        lambda: str(register_canned_product(actor=a2, name="Aceite PG 2", barcode="0012345678905", barcode_type="GTIN", category=cat_other, unit="UND", sale_price=Decimal("8.00"), minimum_stock=5).pk),
    )
    ok4 = (
        c4["winner"]["status"] == "committed"
        and c4["contender"]["status"] == "rejected"
        and Product.objects.filter(name__startswith="Aceite PG").count() == 1
    )
    report["cases"].append({"id": "PG-REVAL-GTIN-DUP", "ok": ok4, "race": c4})

    # Case 5: Concurrent product edit/price-or-deactivate vs checkout_sale (lock order Product->Category)
    open_cash_shift(actor=sel, opening_amount=Decimal("50.00"))
    prod = Product.objects.get(search_name="atún pg 170g")
    confirm_initial_load(actor=wh, product=prod, lots=[LotInput("PG-L1", 10, Decimal("3.00"), dj_tz.localdate() + timedelta(days=30))])
    draft = add_product_to_draft(actor=sel, product_id=prod.pk, quantity=2)
    c5 = contest(
        lambda: str(update_product(actor=a1, product=prod, name=prod.name, barcode=prod.barcode, barcode_type=prod.barcode_type, category=cat_other, sale_price=Decimal("9.90"), minimum_stock=5, expected_snapshot=product_edit_snapshot(prod)).sale_price),
        lambda: str(checkout_sale(actor=sel, draft_id=draft.pk, cash_received=Decimal("20.00"), idempotency_key=uuid4()).correlative),
    )
    ok5 = c5["winner"]["status"] == "committed" and c5["contender"]["status"] == "rejected"
    report["cases"].append({"id": "PG-REVAL-EDIT-VS-CHECKOUT", "ok": ok5, "race": c5})

except Exception as exc:
    report["error"] = {"type": type(exc).__name__, "message": str(exc).replace(PW, "[REDACTED]")[:800]}
finally:
    if configured:
        connections.close_all()
    if started:
        pg("pg_ctl", "-D", DBDIR, "-m", "fast", "-w", "stop")
    with socket.socket() as s:
        report["port_closed"] = s.connect_ex(("127.0.0.1", PORT)) != 0
    report["protected_unchanged"] = {k: (digest(ROOT / k) == v) for k, v in hashes_before.items()}
    report["finished_utc"] = datetime.now(timezone.utc).isoformat()
    out = RESULTS / "evidencias" / f"03-REVAL-pg-{STAMP}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"evidence": str(out.relative_to(ROOT)), "cases": [{"id": c["id"], "ok": c["ok"]} for c in report["cases"]], "error": report.get("error"), "port_closed": report["port_closed"], "protected_unchanged": all(report["protected_unchanged"].values())}, ensure_ascii=False))
if report.get("error") or len(report["cases"]) != 5 or not all(c["ok"] for c in report["cases"]) or not report["port_closed"] or not all(report["protected_unchanged"].values()):
    raise SystemExit(1)
