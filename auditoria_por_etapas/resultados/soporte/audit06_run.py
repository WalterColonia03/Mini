"""Isolated Stage 06 runner (Django checks/tests, fixtures, snapshot, runserver, Chrome browser).
Never loads operator .env and never modifies existing SQLite databases.
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
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
SUPPORT = Path(__file__).resolve().parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def setup(default_cookies: bool = False) -> None:
    sys.path.insert(0, str(APP))
    sys.path.insert(0, str(SUPPORT))
    if default_cookies:
        os.environ["AUDIT06_DEFAULT_COOKIES"] = "1"
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit06_settings"
    import django

    django.setup()


def prepare_empty_migrated_db() -> None:
    from django.core.management import call_command

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)


def prepare_stage06_fixtures(run_dir: Path, out_dir: Path) -> dict:
    from django.utils import timezone as tz

    from cash.models import CashRegister
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.models import Lot
    from inventory.services import LotInput, confirm_initial_load, create_supplier

    admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    creds = {}
    accounts = {}
    for key, email, display, role in [
        ("admin", "admin@audit06.invalid", "Admin Audit06", admin_role),
        ("warehouse", "warehouse@audit06.invalid", "Lucia Almacen06", wh_role),
        ("warehouse2", "warehouse2@audit06.invalid", "Pedro Almacen06", wh_role),
        ("seller", "seller@audit06.invalid", "Vendedor Audit06", seller_role),
    ]:
        pw = secrets.token_urlsafe(18) + "A1!"
        creds[key] = {"email": email, "password": pw}
        accounts[key] = Account.objects.create_user(email, pw, display_name=display, role=role)

    (run_dir / ".credentials.json").write_text(json.dumps(creds), encoding="utf-8")

    cat_drinks = Category.objects.create(name="Bebidas Audit06", is_active=True)
    cat_food = Category.objects.create(name="Abarrotes Audit06", is_active=True)
    cat_inactive = Category.objects.create(name="Categoría Suspendida Audit06", is_active=False)

    # 1. p_entry1: Loaded product with 2 initial lots (avg 2.6000) for pre-entry POS sale + RN-28 + HALF_UP + FEFO
    p_entry1 = Product.objects.create(
        category=cat_drinks,
        name="Jugo Natural Naranja 1L",
        barcode="775060600001",
        sale_price=Decimal("7.50"),
        minimum_stock=5,
    )
    # 2. p_exhausted: Loaded product whose initial stock is exhausted (previous_quantity == 0)
    # Also used for dropped POST before/after commit + UI recovery + stock-overview link
    p_exhausted = Product.objects.create(
        category=cat_food,
        name="Arroz Extra Costeño 1kg",
        barcode="775060600002",
        sale_price=Decimal("4.80"),
        minimum_stock=8,
    )
    # 3. p_expired_only: Loaded product with sole lot expiring today (excluded from POS, still eligible in stock-entry)
    p_expired_only = Product.objects.create(
        category=cat_food,
        name="Yogurt Vence Hoy Audit06",
        barcode="775060600003",
        sale_price=Decimal("6.00"),
        minimum_stock=5,
    )
    # 4. Ineligible products for /inventario/entrada/
    p_no_load = Product.objects.create(
        category=cat_food,
        name="Fideos Sin Carga Audit06",
        barcode="775060600004",
        sale_price=Decimal("3.80"),
        minimum_stock=5,
    )
    p_inactive_loaded = Product.objects.create(
        category=cat_food,
        name="Conserva Inactiva Audit06",
        barcode="775060600005",
        sale_price=Decimal("4.20"),
    )
    p_catoff_loaded = Product.objects.create(
        category=cat_food,
        name="Producto Cat Suspendida Audit06",
        barcode="775060600006",
        sale_price=Decimal("4.40"),
    )

    sup_active = create_supplier(
        actor=accounts["admin"],
        name="Distribuidora Norte Audit06 SAC",
        ruc="20606060001",
        phone="01-5550001",
    )
    long_sup_name = (
        "Comercializadora Mayorista Continental de Alimentos y Bebidas del Peru "
        "Sociedad Anonima Cerrada Distribuida En Almacenes Lima Callao Norte Sur Centro Peru SAC"
    )[:160]
    sup_long = create_supplier(
        actor=accounts["admin"],
        name=long_sup_name,
        ruc="20606060002",
        phone="01-5550002",
    )
    sup_race = create_supplier(
        actor=accounts["admin"],
        name="Proveedor Carrera Estado Audit06 SAC",
        ruc="20606060003",
        phone="01-5550003",
    )

    today = tz.localdate()
    tomorrow = today + timedelta(days=1)
    soon_10 = today + timedelta(days=10)
    soon_20 = today + timedelta(days=20)
    future_45 = today + timedelta(days=45)
    future_60 = today + timedelta(days=60)
    future_90 = today + timedelta(days=90)

    load_entry1 = confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_entry1,
        supplier=sup_active,
        lots=[
            LotInput("L01-INI-LATE", 4, Decimal("2.0000"), future_90),
            LotInput("L02-INI-EARLY", 6, Decimal("3.0000"), soon_20),
        ],
    )
    load_exhausted = confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_exhausted,
        supplier=sup_active,
        lots=[LotInput("EXH-INI-01", 5, Decimal("2.0000"), future_45)],
    )
    Lot.objects.filter(product=p_exhausted).update(available_quantity=0)

    load_expired = confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_expired_only,
        lots=[LotInput("L-VENCE-HOY", 8, Decimal("2.0000"), tomorrow)],
    )
    Lot.objects.filter(product=p_expired_only).update(expiration_date=today)

    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_inactive_loaded,
        lots=[LotInput("INACT-INI-01", 4, Decimal("2.0000"), future_45)],
    )
    p_inactive_loaded.is_active = False
    p_inactive_loaded.save(update_fields=["is_active"])

    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_catoff_loaded,
        lots=[LotInput("CATOFF-INI-01", 4, Decimal("2.0000"), future_45)],
    )
    p_catoff_loaded.category = cat_inactive
    p_catoff_loaded.save(update_fields=["category"])

    CashRegister.objects.create(code="CAJA-01")

    fixture = {
        "today": today.isoformat(),
        "tomorrow": tomorrow.isoformat(),
        "soon_10": soon_10.isoformat(),
        "soon_20": soon_20.isoformat(),
        "future_45": future_45.isoformat(),
        "future_60": future_60.isoformat(),
        "future_90": future_90.isoformat(),
        "categories": {
            "drinks": {"id": str(cat_drinks.pk), "name": cat_drinks.name, "state_version": cat_drinks.state_version},
            "food": {"id": str(cat_food.pk), "name": cat_food.name, "state_version": cat_food.state_version},
            "inactive": {"id": str(cat_inactive.pk), "name": cat_inactive.name},
        },
        "products": {
            "entry1": {
                "id": str(p_entry1.pk),
                "name": p_entry1.name,
                "barcode": p_entry1.barcode,
                "load_id": str(load_entry1.pk),
            },
            "exhausted": {
                "id": str(p_exhausted.pk),
                "name": p_exhausted.name,
                "barcode": p_exhausted.barcode,
                "load_id": str(load_exhausted.pk),
            },
            "expired_only": {
                "id": str(p_expired_only.pk),
                "name": p_expired_only.name,
                "barcode": p_expired_only.barcode,
                "load_id": str(load_expired.pk),
            },
            "no_load": {"id": str(p_no_load.pk), "name": p_no_load.name},
            "inactive": {"id": str(p_inactive_loaded.pk), "name": p_inactive_loaded.name},
            "cat_off": {"id": str(p_catoff_loaded.pk), "name": p_catoff_loaded.name},
        },
        "suppliers": {
            "active": {"id": str(sup_active.pk), "name": sup_active.name, "ruc": sup_active.ruc},
            "long": {"id": str(sup_long.pk), "name": sup_long.name, "ruc": sup_long.ruc},
            "race": {"id": str(sup_race.pk), "name": sup_race.name, "ruc": sup_race.ruc},
        },
    }
    write(out_dir / "fixture.json", fixture)
    return fixture


def snapshot() -> dict:
    from cash.models import CashShift
    from catalog.models import Category, Product
    from inventory.models import InitialInventoryLoad, Lot, Supplier
    from sales.models import Sale, SaleLine

    return {
        "categories": list(Category.objects.order_by("name").values("id", "name", "is_active", "state_version")),
        "suppliers": list(Supplier.objects.order_by("name", "ruc").values("id", "name", "ruc", "is_active")),
        "loads": list(
            InitialInventoryLoad.objects.order_by("confirmed_at", "pk").values(
                "id", "product_id", "responsible_id", "confirmed_at"
            )
        ),
        "lots": list(
            Lot.objects.order_by("product_id", "number_normalized").values(
                "id",
                "product_id",
                "initial_load_id",
                "supplier_id",
                "responsible_id",
                "is_initial",
                "number",
                "number_normalized",
                "initial_quantity",
                "available_quantity",
                "unit_cost",
                "expiration_date",
                "received_at",
            )
        ),
        "products": list(
            Product.objects.order_by("barcode").values(
                "id", "name", "barcode", "category_id", "is_active", "minimum_stock", "average_cost"
            )
        ),
        "cash_shifts": list(CashShift.objects.order_by("opened_at").values("id", "status", "seller_id")),
        "sales": list(Sale.objects.order_by("correlative").values("id", "correlative", "total_amount", "seller_id")),
        "sale_lines": list(
            SaleLine.objects.order_by("pk").values(
                "id", "sale_id", "product_id", "quantity", "unit_price", "amount", "unit_cost"
            )
        ),
    }


def make_run_dir(tag: str) -> tuple[Path, Path, str]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)
    run_dir = RESULTS / "datos" / f"etapa06-{tag}-{stamp}"
    out_dir = RESULTS / "evidencias" / f"06-{tag}-{stamp}"
    run_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    write(run_dir / "marker.json", {"run": run_dir.name, "created_utc": stamp})
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")
    return run_dir, out_dir, stamp


def protected_hashes() -> dict[str, str | None]:
    protected = [
        *APP.glob("*.sqlite3"),
        *(RESULTS / "datos").rglob("*.sqlite3"),
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]
    return {str(p.relative_to(ROOT)): digest(p) if p.exists() else None for p in protected}


def run_checks() -> int:
    start_hashes = protected_hashes()
    run_dir, out_dir, stamp = make_run_dir("checks")
    os.environ.update(AUDIT06_RUN_DIR=str(run_dir), AUDIT06_OUT=str(out_dir), AUDIT06_DEFAULT_COOKIES="1")
    setup(default_cookies=True)
    from django.core.management import execute_from_command_line

    buf = io.StringIO()
    exit_code = 0
    old_cwd = Path.cwd()
    try:
        os.chdir(APP)
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            for argv in (["manage.py", "check"], ["manage.py", "makemigrations", "--check", "--dry-run"]):
                try:
                    execute_from_command_line(argv)
                except SystemExit as exc:
                    exit_code = max(exit_code, int(exc.code or 0))
    finally:
        os.chdir(old_cwd)
    out_text = buf.getvalue()
    (out_dir / "checks.txt").write_text(out_text, encoding="utf-8")
    end_hashes = {
        k: (digest(ROOT / k) if (ROOT / k).exists() else None) == v for k, v in start_hashes.items()
    }
    summary = {
        "stamp_utc": stamp,
        "exit_code": exit_code,
        "output": out_text,
        "protected_unchanged": all(end_hashes.values()),
    }
    write(out_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if (exit_code == 0 and all(end_hashes.values())) else 1


def run_tests(targets: list[str]) -> int:
    start_hashes = protected_hashes()
    run_dir, out_dir, stamp = make_run_dir("tests")
    os.environ.update(
        AUDIT06_RUN_DIR=str(run_dir),
        AUDIT06_OUT=str(out_dir),
        AUDIT06_DEFAULT_COOKIES="1",
    )
    setup(default_cookies=True)
    from django.core.management import execute_from_command_line

    buf = io.StringIO()
    argv = ["manage.py", "test", *targets, "-v", "2"]
    exit_code = 0
    started = time.monotonic()
    old_cwd = Path.cwd()
    try:
        os.chdir(APP)
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            try:
                execute_from_command_line(argv)
            except SystemExit as exc:
                exit_code = int(exc.code or 0)
    finally:
        os.chdir(old_cwd)
    duration = round(time.monotonic() - started, 3)
    output_text = buf.getvalue()
    (out_dir / "test_output.txt").write_text(output_text, encoding="utf-8")
    end_hashes = {
        k: (digest(ROOT / k) if (ROOT / k).exists() else None) == v for k, v in start_hashes.items()
    }
    summary = {
        "stamp_utc": stamp,
        "targets": targets,
        "exit_code": exit_code,
        "duration_s": duration,
        "evidence_txt": str((out_dir / "test_output.txt").relative_to(ROOT)),
        "protected_unchanged": end_hashes,
        "tail": output_text.splitlines()[-25:],
    }
    write(out_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if exit_code != 0 or not all(end_hashes.values()):
        return 1
    return 0


def run_browser() -> int:
    start_hashes = protected_hashes()
    run_dir, out_dir, stamp = make_run_dir("browser")
    os.environ.update(
        AUDIT06_RUN_DIR=str(run_dir),
        AUDIT06_OUT=str(out_dir),
        AUDIT06_PYTHON=sys.executable,
    )
    result = {
        "action": "browser",
        "run": run_dir.name,
        "started_utc": stamp,
        "evidence": str(out_dir.relative_to(ROOT)),
    }
    server = None
    port = 0
    try:
        setup(default_cookies=False)
        prepare_empty_migrated_db()
        prepare_stage06_fixtures(run_dir, out_dir)
        write(out_dir / "orm-initial.json", snapshot())

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        os.environ["AUDIT06_PORT"] = str(port)
        server = subprocess.Popen(
            [sys.executable, __file__, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(100):
            with socket.socket() as sock:
                if sock.connect_ex(("127.0.0.1", port)) == 0:
                    break
            if server.poll() is not None:
                raise RuntimeError("Django runserver terminated early")
            time.sleep(0.1)

        child = subprocess.run(
            ["node", str(SUPPORT / "audit06_browser.cjs")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=240,
        )
        result.update(
            browser_exit=child.returncode,
            browser_output=child.stdout,
            browser_error=child.stderr,
        )
        write(out_dir / "orm-final.json", snapshot())
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["error_message"] = str(exc)
        raise
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
            result["port_closed"] = False
            for _ in range(50):
                with socket.socket() as sock:
                    if sock.connect_ex(("127.0.0.1", port)) != 0:
                        result["port_closed"] = True
                        break
                time.sleep(0.1)
        result["protected_unchanged"] = {
            k: (digest(ROOT / k) if (ROOT / k).exists() else None) == v for k, v in start_hashes.items()
        }
        result["original_sha256"] = digest(APP / "r1_pmv.sqlite3")
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        write(out_dir / "result.json", result)
        print(
            json.dumps(
                {
                    "evidence": result["evidence"],
                    "browser_exit": result.get("browser_exit"),
                    "port_closed": result.get("port_closed"),
                    "protected_unchanged": all(result["protected_unchanged"].values()),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    if (
        result.get("browser_exit", 1) != 0
        or not result.get("port_closed")
        or not all(result["protected_unchanged"].values())
    ):
        return 1
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: audit06_run.py [checks|tests ...|browser|serve|snapshot]")
    action = sys.argv[1]
    if action == "serve":
        setup(default_cookies=False)
        from django.core.management import execute_from_command_line

        execute_from_command_line(
            ["manage.py", "runserver", f"127.0.0.1:{os.environ['AUDIT06_PORT']}", "--noreload", "--insecure"]
        )
        return 0
    if action == "snapshot":
        setup(default_cookies=False)
        print(json.dumps(snapshot(), ensure_ascii=False, default=str))
        return 0
    if action == "checks":
        return run_checks()
    if action == "tests":
        targets = sys.argv[2:] or ["inventory.test_audit06_stock_entry"]
        return run_tests(targets)
    if action == "browser":
        return run_browser()
    raise SystemExit(f"Unknown action: {action}")


if __name__ == "__main__":
    raise SystemExit(main())

