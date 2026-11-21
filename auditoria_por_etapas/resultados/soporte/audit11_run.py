"""Isolated Stage 11 runner (Django checks/tests, fixtures, snapshot, runserver, Chrome browser).
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
from unittest.mock import patch

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
        os.environ["AUDIT11_DEFAULT_COOKIES"] = "1"
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit11_settings"
    import django

    django.setup()


def prepare_empty_migrated_db() -> None:
    from django.core.management import call_command

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)


def prepare_stage11_fixtures(run_dir: Path, out_dir: Path) -> dict:
    from django.utils import timezone as tz

    from cash.models import CashRegister, CashShift
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.models import Lot
    from inventory.services import LotInput, confirm_initial_load, create_supplier
    from sales.models import SaleCounter

    admin_role, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    wh_role, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    seller_role, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

    creds = {}
    accounts = {}
    for key, email, display, role, is_active in [
        ("admin", "admin@audit11.invalid", "Admin Audit11", admin_role, True),
        ("warehouse", "warehouse@audit11.invalid", "Lucia Almacen11", wh_role, True),
        ("seller", "seller@audit11.invalid", "Carmen Vendedora11", seller_role, True),
        ("seller2", "seller2@audit11.invalid", "Mario Vendedor11", seller_role, True),
        ("inactive_seller", "inactive.seller@audit11.invalid", "Inactivo Vendedor11", seller_role, False),
    ]:
        pw = secrets.token_urlsafe(18) + "A1!"
        creds[key] = {"email": email, "password": pw}
        accounts[key] = Account.objects.create_user(
            email, pw, display_name=display, role=role, is_active=is_active
        )

    (run_dir / ".credentials.json").write_text(json.dumps(creds), encoding="utf-8")

    cat_active = Category.objects.create(name="Conservas y Abarrotes 11", is_active=True)
    cat_off = Category.objects.create(name="Categoria Suspendida 11", is_active=False)
    supplier = create_supplier(
        actor=accounts["admin"],
        name="Distribuidora Lima Sur 11 SAC",
        ruc="20111111001",
        phone="01-5551101",
    )

    today = tz.localdate()
    d_minus2 = today - timedelta(days=2)
    d_plus1 = today + timedelta(days=1)
    d_plus5 = today + timedelta(days=5)
    d_plus20 = today + timedelta(days=20)
    d_plus25 = today + timedelta(days=25)
    d_plus30 = today + timedelta(days=30)

    # 1. p_fefo: expired (-2d, qty 5), expires today (qty 6), zero-qty (+1d, qty 0),
    # tie +5d: FEFO-TIE-B (t1, qty 2), FEFO-TIE-A (t2, qty 3), FEFO-FAR (+30d, t3, qty 10).
    # Total sellable = 15. Total physical = 26.
    p_fefo = Product.objects.create(
        category=cat_active,
        name="Atun FEFO MultiLote",
        barcode="775110000001",
        sale_price=Decimal("4.50"),
        minimum_stock=4,
    )
    t1 = tz.now() - timedelta(hours=3)
    t2 = tz.now() - timedelta(hours=2)
    t3 = tz.now() - timedelta(hours=1)
    with patch("django.utils.timezone.now", return_value=t1):
        load_fefo = confirm_initial_load(
            actor=accounts["warehouse"],
            product=p_fefo,
            supplier=supplier,
            lots=[
                LotInput("FEFO-VENC-PAST", 5, Decimal("2.0000"), d_plus1),
                LotInput("FEFO-VENC-HOY", 6, Decimal("2.1000"), d_plus1),
                LotInput("FEFO-ZERO-EXP", 4, Decimal("2.2000"), d_plus1),
                LotInput("FEFO-TIE-B", 2, Decimal("2.0000"), d_plus5),
            ],
        )
    with patch("django.utils.timezone.now", return_value=t2):
        Lot.objects.create(
            product=p_fefo,
            initial_load=load_fefo,
            supplier=supplier,
            responsible=accounts["warehouse"],
            is_initial=False,
            number="FEFO-TIE-A",
            initial_quantity=3,
            available_quantity=3,
            unit_cost=Decimal("3.0000"),
            expiration_date=d_plus5,
        )
    with patch("django.utils.timezone.now", return_value=t3):
        Lot.objects.create(
            product=p_fefo,
            initial_load=load_fefo,
            supplier=supplier,
            responsible=accounts["warehouse"],
            is_initial=False,
            number="FEFO-FAR",
            initial_quantity=10,
            available_quantity=10,
            unit_cost=Decimal("4.0000"),
            expiration_date=d_plus30,
        )
    Lot.objects.filter(product=p_fefo, number_normalized="FEFO-VENC-PAST").update(expiration_date=d_minus2)
    Lot.objects.filter(product=p_fefo, number_normalized="FEFO-VENC-HOY").update(expiration_date=today)
    Lot.objects.filter(product=p_fefo, number_normalized="FEFO-ZERO-EXP").update(available_quantity=0)

    # 2. p_tax: S/ 3.55 for exact centavo/IGV rounding + discount tests
    p_tax = Product.objects.create(
        category=cat_active,
        name="Conserva Centavos Exactos",
        barcode="775110000002",
        sale_price=Decimal("3.55"),
        minimum_stock=2,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_tax,
        supplier=supplier,
        lots=[LotInput("TAX-01", 20, Decimal("1.7500"), d_plus20)],
    )

    # 3. p_price: S/ 10.00 for inter-role price change / snapshot tests
    p_price = Product.objects.create(
        category=cat_active,
        name="Sardina Cambio Precio",
        barcode="775110000003",
        sale_price=Decimal("10.00"),
        minimum_stock=2,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_price,
        supplier=supplier,
        lots=[LotInput("PRC-01", 10, Decimal("4.0000"), d_plus20)],
    )

    # 4. p_long: 140-char unbroken product name for layout wrap verification
    long_name = ("ProductoUltraExtensoSinEspaciosParaCobroConstanciaHistorial11" * 3)[:140]
    p_long = Product.objects.create(
        category=cat_active,
        name=long_name,
        barcode="775110000004",
        sale_price=Decimal("12.00"),
        minimum_stock=2,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_long,
        supplier=supplier,
        lots=[LotInput("LNG-01", 8, Decimal("6.0000"), d_plus25)],
    )

    # 5. p_cat_off: active product whose category was later suspended (must block in POS and checkout)
    p_cat_off = Product.objects.create(
        category=cat_active,
        name="Atun Categoria Suspendida 11",
        barcode="775110000005",
        sale_price=Decimal("7.00"),
        minimum_stock=2,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_cat_off,
        supplier=supplier,
        lots=[LotInput("CATOFF-01", 5, Decimal("3.0000"), d_plus20)],
    )
    p_cat_off.category = cat_off
    p_cat_off.save(update_fields=["category"])

    reg = CashRegister.objects.create(code="CAJA-01")
    shift = CashShift.objects.create(
        cash_register=reg,
        seller=accounts["seller"],
        opening_amount=Decimal("100.00"),
    )
    SaleCounter.objects.get_or_create(id=1, defaults={"next_value": 1})

    fixture = {
        "dates": {
            "minus2": d_minus2.isoformat(),
            "today": today.isoformat(),
            "plus1": d_plus1.isoformat(),
            "plus5": d_plus5.isoformat(),
            "plus20": d_plus20.isoformat(),
            "plus25": d_plus25.isoformat(),
            "plus30": d_plus30.isoformat(),
        },
        "shift": {"id": str(shift.pk), "opening_amount": "100.00", "register": reg.code},
        "accounts": {k: {"id": str(v.pk), "email": v.email, "display_name": v.display_name} for k, v in accounts.items()},
        "products": {
            "fefo": {"id": str(p_fefo.pk), "name": p_fefo.name, "barcode": p_fefo.barcode, "price": "4.50"},
            "tax": {"id": str(p_tax.pk), "name": p_tax.name, "barcode": p_tax.barcode, "price": "3.55"},
            "price": {"id": str(p_price.pk), "name": p_price.name, "barcode": p_price.barcode, "price": "10.00"},
            "long": {"id": str(p_long.pk), "name": p_long.name, "barcode": p_long.barcode, "price": "12.00"},
            "cat_off": {"id": str(p_cat_off.pk), "name": p_cat_off.name, "barcode": p_cat_off.barcode, "price": "7.00"},
        },
    }
    write(out_dir / "fixture.json", fixture)
    return fixture


def snapshot() -> dict:
    from cash.models import CashShift, CashShiftClose
    from catalog.models import Product
    from inventory.models import Lot
    from sales.models import Sale, SaleCounter, SaleDraft, SaleDraftLine, SaleLine

    return {
        "counter": list(SaleCounter.objects.values("id", "next_value")),
        "shifts": list(CashShift.objects.order_by("opened_at").values("id", "status", "opening_amount", "seller_id")),
        "closes": list(CashShiftClose.objects.order_by("closed_at").values("cash_shift_id", "expected_amount", "counted_amount", "difference")),
        "drafts": list(SaleDraft.objects.order_by("created_at").values("id", "status", "seller_id", "cash_shift_id", "discarded_at")),
        "draft_lines": list(SaleDraftLine.objects.order_by("created_at", "id").values("id", "draft_id", "product_id", "quantity", "unit_price")),
        "sales": list(
            Sale.objects.order_by("correlative").values(
                "id",
                "correlative",
                "draft_id",
                "seller_id",
                "cash_shift_id",
                "total_amount",
                "discount_amount",
                "base_amount",
                "igv_amount",
                "cash_received",
                "change_given",
                "idempotency_key",
            )
        ),
        "sale_lines": list(
            SaleLine.objects.order_by("sale_id", "id").values(
                "id",
                "sale_id",
                "product_id",
                "product_snapshot_name",
                "product_snapshot_barcode",
                "quantity",
                "unit_price",
                "unit_cost",
                "amount",
            )
        ),
        "lots": list(
            Lot.objects.order_by("product_id", "expiration_date", "received_at", "id").values(
                "id",
                "product_id",
                "number",
                "number_normalized",
                "initial_quantity",
                "available_quantity",
                "expiration_date",
            )
        ),
        "products": list(
            Product.objects.order_by("barcode").values("id", "name", "barcode", "sale_price", "average_cost", "is_active")
        ),
    }


def make_run_dir(tag: str) -> tuple[Path, Path, str]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)
    run_dir = RESULTS / "datos" / f"etapa11-{tag}-{stamp}"
    out_dir = RESULTS / "evidencias" / f"11-{tag}-{stamp}"
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
    os.environ.update(AUDIT11_RUN_DIR=str(run_dir), AUDIT11_OUT=str(out_dir), AUDIT11_DEFAULT_COOKIES="1")
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
        AUDIT11_RUN_DIR=str(run_dir),
        AUDIT11_OUT=str(out_dir),
        AUDIT11_DEFAULT_COOKIES="1",
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
        AUDIT11_RUN_DIR=str(run_dir),
        AUDIT11_OUT=str(out_dir),
        AUDIT11_PYTHON=sys.executable,
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
        prepare_stage11_fixtures(run_dir, out_dir)
        write(out_dir / "orm-initial.json", snapshot())

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        os.environ["AUDIT11_PORT"] = str(port)
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
            ["node", str(SUPPORT / "audit11_browser.cjs")],
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
        raise SystemExit("Usage: audit11_run.py [checks|tests ...|browser|serve|snapshot]")
    action = sys.argv[1]
    if action == "serve":
        setup(default_cookies=False)
        from django.core.management import execute_from_command_line

        execute_from_command_line(
            ["manage.py", "runserver", f"127.0.0.1:{os.environ['AUDIT11_PORT']}", "--noreload", "--insecure"]
        )
        return 0
    if action == "snapshot":
        setup(default_cookies=False)
        print(json.dumps(snapshot(), ensure_ascii=False, default=str))
        return 0
    if action == "checks":
        return run_checks()
    if action == "tests":
        targets = sys.argv[2:] or ["sales"]
        return run_tests(targets)
    if action == "browser":
        return run_browser()
    raise SystemExit(f"Unknown action: {action}")


if __name__ == "__main__":
    raise SystemExit(main())

