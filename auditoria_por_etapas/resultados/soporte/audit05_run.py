"""Isolated Stage 05 runner (Django checks/tests, fixtures, snapshot, runserver, Chrome browser).
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
        os.environ["AUDIT05_DEFAULT_COOKIES"] = "1"
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit05_settings"
    import django

    django.setup()


def prepare_empty_migrated_db() -> None:
    from django.core.management import call_command

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)


def prepare_stage05_fixtures(run_dir: Path, out_dir: Path) -> dict:
    from django.utils import timezone as tz

    from cash.models import CashRegister
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.models import Lot
    from inventory.services import LotInput, confirm_initial_load, create_supplier, register_stock_entry

    admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    creds = {}
    accounts = {}
    for key, email, display, role in [
        ("admin", "admin@audit05.invalid", "Admin Audit05", admin_role),
        ("warehouse", "warehouse@audit05.invalid", "Lucia Almacen05", wh_role),
        ("warehouse2", "warehouse2@audit05.invalid", "Pedro Almacen05", wh_role),
        ("seller", "seller@audit05.invalid", "Vendedor Audit05", seller_role),
    ]:
        pw = secrets.token_urlsafe(18) + "A1!"
        creds[key] = {"email": email, "password": pw}
        accounts[key] = Account.objects.create_user(email, pw, display_name=display, role=role)

    (run_dir / ".credentials.json").write_text(json.dumps(creds), encoding="utf-8")

    cat_active = Category.objects.create(name="Lácteos y conservas Audit05", is_active=True)
    cat_drinks = Category.objects.create(name="Bebidas Audit05", is_active=True)
    cat_inactive = Category.objects.create(name="Categoría Suspendida Audit05", is_active=False)

    # 1. Eligible product 1 (multi-lot weighted cost & FEFO downstream sale)
    p_elig1 = Product.objects.create(
        category=cat_drinks,
        name="Jugo Natural Naranja 1L",
        barcode="775050500001",
        sale_price=Decimal("7.50"),
        minimum_stock=10,
    )
    # 2. Eligible product 2 (RN-06 stock == minimum == 10, extreme 64-char lot & 160-char supplier)
    p_elig2 = Product.objects.create(
        category=cat_active,
        name="Atún Clásico 170g",
        barcode="775050500002",
        sale_price=Decimal("5.80"),
        minimum_stock=10,
    )
    # 3. Pre-loaded product with both initial + subsequent lot by 2 warehouse workers
    p_sub = Product.objects.create(
        category=cat_active,
        name="Leche Evaporada Tarro",
        barcode="775050500003",
        sale_price=Decimal("4.60"),
        minimum_stock=25,
    )
    # 4. Pre-loaded product whose sole lot expires today (unsellable under RN-03, visible as Vencido)
    p_today_exp = Product.objects.create(
        category=cat_active,
        name="Yogurt Vence Hoy Audit05",
        barcode="775050500004",
        sale_price=Decimal("6.00"),
        minimum_stock=5,
    )
    # 5. Ineligible products (is_active=False, category.is_active=False)
    # Note: DB CheckConstraint product_requires_expiration enforces controls_expiration=True on all Product rows
    p_inactive = Product.objects.create(
        category=cat_active,
        name="Conserva Inactiva Audit05",
        barcode="775050500006",
        sale_price=Decimal("4.00"),
        is_active=False,
    )
    p_cat_off = Product.objects.create(
        category=cat_inactive,
        name="Producto Cat Suspendida Audit05",
        barcode="775050500007",
        sale_price=Decimal("4.20"),
    )

    sup_active = create_supplier(
        actor=accounts["admin"],
        name="Distribuidora Norte Audit05 SAC",
        ruc="20505050001",
        phone="01-5550001",
    )
    long_sup_name = (
        "Comercializadora Mayorista Continental de Alimentos y Bebidas del Peru "
        "Sociedad Anonima Cerrada Distribuida En Almacenes Lima Callao Norte Sur Centro Peru SAC Lima Este"
    )[:160]
    sup_long = create_supplier(
        actor=accounts["admin"],
        name=long_sup_name,
        ruc="20505050002",
        phone="01-5550002",
    )

    today = tz.localdate()
    tomorrow = today + timedelta(days=1)
    soon_15 = today + timedelta(days=15)
    future_45 = today + timedelta(days=45)
    future_90 = today + timedelta(days=90)

    load_sub = confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_sub,
        supplier=sup_active,
        lots=[LotInput("L-PRE-05", 10, Decimal("2.5000"), soon_15)],
    )
    register_stock_entry(
        actor=accounts["warehouse2"],
        product=p_sub,
        supplier=sup_active,
        lots=[LotInput("L-POST-05", 10, Decimal("3.5000"), future_45)],
    )

    load_today = confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_today_exp,
        lots=[LotInput("L-VENCE-HOY", 8, Decimal("2.0000"), tomorrow)],
    )
    # Simulate clock crossing midnight into expiration day for p_today_exp
    Lot.objects.filter(product=p_today_exp).update(expiration_date=today)

    CashRegister.objects.create(code="CAJA-01")

    fixture = {
        "today": today.isoformat(),
        "tomorrow": tomorrow.isoformat(),
        "soon_15": soon_15.isoformat(),
        "future_45": future_45.isoformat(),
        "future_90": future_90.isoformat(),
        "categories": {
            "active": {"id": str(cat_active.pk), "name": cat_active.name, "state_version": cat_active.state_version},
            "drinks": {"id": str(cat_drinks.pk), "name": cat_drinks.name, "state_version": cat_drinks.state_version},
            "inactive": {"id": str(cat_inactive.pk), "name": cat_inactive.name},
        },
        "products": {
            "elig1": {"id": str(p_elig1.pk), "name": p_elig1.name, "barcode": p_elig1.barcode},
            "elig2": {"id": str(p_elig2.pk), "name": p_elig2.name, "barcode": p_elig2.barcode},
            "sub": {
                "id": str(p_sub.pk),
                "name": p_sub.name,
                "barcode": p_sub.barcode,
                "load_id": str(load_sub.pk),
            },
            "today_exp": {
                "id": str(p_today_exp.pk),
                "name": p_today_exp.name,
                "barcode": p_today_exp.barcode,
                "load_id": str(load_today.pk),
            },
            "inactive": {"id": str(p_inactive.pk), "name": p_inactive.name},
            "cat_off": {"id": str(p_cat_off.pk), "name": p_cat_off.name},
        },
        "suppliers": {
            "active": {"id": str(sup_active.pk), "name": sup_active.name},
            "long": {"id": str(sup_long.pk), "name": sup_long.name},
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
            SaleLine.objects.order_by("pk").values("id", "sale_id", "product_id", "quantity", "unit_cost")
        ),
    }


def make_run_dir(tag: str) -> tuple[Path, Path, str]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)
    run_dir = RESULTS / "datos" / f"etapa05-{tag}-{stamp}"
    out_dir = RESULTS / "evidencias" / f"05-{tag}-{stamp}"
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
    os.environ.update(AUDIT05_RUN_DIR=str(run_dir), AUDIT05_OUT=str(out_dir), AUDIT05_DEFAULT_COOKIES="1")
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
        AUDIT05_RUN_DIR=str(run_dir),
        AUDIT05_OUT=str(out_dir),
        AUDIT05_DEFAULT_COOKIES="1",
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


def run_browser(script="audit05_browser.cjs", tag="browser") -> int:
    start_hashes = protected_hashes()
    source_paths = sorted(p for p in APP.rglob("*") if p.is_file()
        and p.suffix in {".py", ".html", ".css", ".js"}
        and not any(x in {".venv", ".git", "__pycache__"} for x in p.parts))
    source_paths += [SUPPORT / script, Path(__file__), SUPPORT / "audit05_settings.py"]
    source_hashes = {str(p.relative_to(ROOT)): digest(p) for p in source_paths}
    run_dir, out_dir, stamp = make_run_dir(tag)
    os.environ.update(
        AUDIT05_RUN_DIR=str(run_dir),
        AUDIT05_OUT=str(out_dir),
        AUDIT05_PYTHON=sys.executable,
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
        prepare_stage05_fixtures(run_dir, out_dir)
        write(out_dir / "orm-initial.json", snapshot())

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        os.environ["AUDIT05_PORT"] = str(port)
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
            ["node", str(SUPPORT / script)],
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
        write(out_dir / "source-manifest.json", {
            "before": source_hashes,
            "changed_during_run": [k for k, v in source_hashes.items()
                if not (ROOT / k).exists() or digest(ROOT / k) != v],
        })
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
        raise SystemExit("Usage: audit05_run.py [checks|tests ...|browser|serve|snapshot]")
    action = sys.argv[1]
    if action == "serve":
        setup(default_cookies=False)
        from django.core.management import execute_from_command_line

        execute_from_command_line(
            ["manage.py", "runserver", f"127.0.0.1:{os.environ['AUDIT05_PORT']}", "--noreload", "--insecure"]
        )
        return 0
    if action == "snapshot":
        setup(default_cookies=False)
        print(json.dumps(snapshot(), ensure_ascii=False, default=str))
        return 0
    if action == "checks":
        return run_checks()
    if action == "tests":
        targets = sys.argv[2:] or ["inventory.test_audit05_initial_load"]
        return run_tests(targets)
    if action == "browser":
        return run_browser()
    if action == "keyboard":
        return run_browser("audit05h_keyboard.cjs", "keyboard")
    if action == "narrow":
        return run_browser("audit05i_narrow.cjs", "narrow")
    raise SystemExit(f"Unknown action: {action}")


if __name__ == "__main__":
    raise SystemExit(main())
