"""Isolated Stage 08 runner (Django checks/tests, fixtures, snapshot, runserver, Chrome browser).
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
import uuid
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
        os.environ["AUDIT08_DEFAULT_COOKIES"] = "1"
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit08_settings"
    import django

    django.setup()


def prepare_empty_migrated_db() -> None:
    from django.core.management import call_command

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)


def prepare_stage08_fixtures(run_dir: Path, out_dir: Path) -> dict:
    from django.utils import timezone as tz

    from cash.models import CashRegister, CashShift
    from catalog.models import Category, Product
    from catalog.services import update_product
    from identity.models import Account, Role
    from inventory.models import Lot
    from inventory.services import LotInput, confirm_initial_load, create_supplier
    from sales.services import add_product_to_draft, checkout_sale

    admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    creds = {}
    accounts = {}
    for key, email, display, role in [
        ("admin", "admin@audit08.invalid", "Admin Audit08", admin_role),
        ("warehouse", "warehouse@audit08.invalid", "Lucia Almacen08", wh_role),
        ("seller", "seller@audit08.invalid", "Carmen Vendedora08", seller_role),
    ]:
        pw = secrets.token_urlsafe(18) + "A1!"
        creds[key] = {"email": email, "password": pw}
        accounts[key] = Account.objects.create_user(email, pw, display_name=display, role=role)

    (run_dir / ".credentials.json").write_text(json.dumps(creds), encoding="utf-8")

    cat_active = Category.objects.create(name="Abarrotes Audit08", is_active=True)
    sup_active = create_supplier(
        actor=accounts["admin"],
        name="Distribuidora Central 08 SAC",
        ruc="20808080011",
        phone="01-5550081",
    )

    today = tz.localdate()
    d_minus1 = today - timedelta(days=1)
    d_plus1 = today + timedelta(days=1)
    d_plus25 = today + timedelta(days=25)
    d_plus60 = today + timedelta(days=60)

    # 1. Producto mixto con dos lotes: uno vencido hoy (8u @ 2.00) y uno vigente (12u @ 4.00) -> avg_cost=4.0000 tras vencimiento / en merma
    p_mix = Product.objects.create(
        category=cat_active,
        name="Leche Evaporada Audit08 400g",
        barcode="775080800001",
        sale_price=Decimal("6.50"),
        minimum_stock=5,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_mix,
        supplier=sup_active,
        lots=[
            LotInput("LOT08-VENC", 8, Decimal("2.0000"), d_plus1),
            LotInput("LOT08-VIG", 12, Decimal("4.0000"), d_plus60),
        ],
    )
    Lot.objects.filter(product=p_mix, number_normalized="LOT08-VENC").update(expiration_date=today)
    lot_mix_exp = Lot.objects.get(product=p_mix, number_normalized="LOT08-VENC")
    lot_mix_vig = Lot.objects.get(product=p_mix, number_normalized="LOT08-VIG")

    # 2. Producto de texto largo sin espacios (140 chars producto, 64 chars lote) para probar layout/wrapping a 1366px
    long_name = ("ProductoUltraExtensoSinEspaciosParaValidarEnvolturaEnBajasAjustesYKardexAudit08" * 2)[:140]
    p_long = Product.objects.create(
        category=cat_active,
        name=long_name,
        barcode="775080800002",
        sale_price=Decimal("5.00"),
        minimum_stock=3,
    )
    lot_long_num = "L08" + ("W" * 61)
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_long,
        supplier=sup_active,
        lots=[LotInput(lot_long_num, 15, Decimal("2.5000"), d_plus25)],
    )
    lot_long = Lot.objects.get(product=p_long)

    # 3. Aislamiento de código de barras reutilizado en Kardex + venta real de VENDEDOR
    reg = CashRegister.objects.create(code="CAJA-08")
    CashShift.objects.create(cash_register=reg, seller=accounts["seller"], opening_amount=Decimal("100.00"))

    p_orig_bc = Product.objects.create(
        category=cat_active,
        name="Jugo Antiguo BC08",
        barcode="775080800099",
        sale_price=Decimal("7.00"),
        minimum_stock=2,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_orig_bc,
        supplier=sup_active,
        lots=[LotInput("BC-OLD-1", 10, Decimal("3.0000"), d_plus60)],
    )
    d_old = add_product_to_draft(actor=accounts["seller"], product_id=p_orig_bc.pk, quantity=2)
    sale_old = checkout_sale(
        actor=accounts["seller"], draft_id=d_old.pk, cash_received=Decimal("20.00"), idempotency_key=uuid.uuid4()
    )
    update_product(
        actor=accounts["admin"],
        product=p_orig_bc,
        name=p_orig_bc.name,
        barcode="775080800199",
        sale_price=p_orig_bc.sale_price,
        minimum_stock=p_orig_bc.minimum_stock,
    )
    p_reused_bc = Product.objects.create(
        category=cat_active,
        name="Snack Nuevo Reuso BC08",
        barcode="775080800099",
        sale_price=Decimal("4.50"),
        minimum_stock=2,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_reused_bc,
        supplier=sup_active,
        lots=[LotInput("BC-NEW-1", 6, Decimal("2.0000"), d_plus60)],
    )

    fixture = {
        "dates": {
            "minus1": d_minus1.isoformat(),
            "today": today.isoformat(),
            "plus1": d_plus1.isoformat(),
            "plus25": d_plus25.isoformat(),
            "plus60": d_plus60.isoformat(),
        },
        "products": {
            "mix": {"id": str(p_mix.pk), "name": p_mix.name},
            "long": {"id": str(p_long.pk), "name": p_long.name},
            "orig_bc": {"id": str(p_orig_bc.pk), "name": p_orig_bc.name, "sale_correlative": sale_old.correlative},
            "reused_bc": {"id": str(p_reused_bc.pk), "name": p_reused_bc.name},
        },
        "lots": {
            "mix_exp": {"id": str(lot_mix_exp.pk), "number": lot_mix_exp.number_normalized},
            "mix_vig": {"id": str(lot_mix_vig.pk), "number": lot_mix_vig.number_normalized},
            "long": {"id": str(lot_long.pk), "number": lot_long.number_normalized},
        },
    }
    write(out_dir / "fixture.json", fixture)
    return fixture


def snapshot() -> dict:
    from catalog.models import Product
    from inventory.models import Lot, PhysicalAdjustment, StockWriteOff
    from sales.models import Sale, SaleLine

    return {
        "products": list(
            Product.objects.order_by("barcode").values(
                "id", "name", "barcode", "is_active", "minimum_stock", "average_cost"
            )
        ),
        "lots": list(
            Lot.objects.order_by("expiration_date", "received_at", "id").values(
                "id",
                "product_id",
                "number_normalized",
                "initial_quantity",
                "available_quantity",
                "unit_cost",
                "expiration_date",
            )
        ),
        "writeoffs": list(
            StockWriteOff.objects.order_by("correlativo").values(
                "id", "correlativo", "lot_id", "quantity", "reason", "notes", "responsible__email"
            )
        ),
        "adjustments": list(
            PhysicalAdjustment.objects.order_by("created_at", "id").values(
                "id", "lot_id", "delta", "reason", "responsible__email"
            )
        ),
        "sales": list(
            Sale.objects.order_by("correlative").values("id", "correlative", "total_amount", "seller__email")
        ),
        "sale_lines": list(
            SaleLine.objects.order_by("sale__correlative", "id").values(
                "id", "sale__correlative", "product_id", "quantity", "unit_cost"
            )
        ),
    }


def make_run_dir(tag: str) -> tuple[Path, Path, str]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)
    run_dir = RESULTS / "datos" / f"etapa08-{tag}-{stamp}"
    out_dir = RESULTS / "evidencias" / f"08-{tag}-{stamp}"
    run_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    write(run_dir / "marker.json", {"run": run_dir.name, "created_utc": stamp})
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")
    return run_dir, out_dir, stamp


def protected_hashes() -> dict[str, str | None]:
    # Protect operative SQLite, XLSX, and settled pre-Stage-08 historical DBs
    # (excluding contemporary 23:38Z+ runs from sibling 04-C/05-H agents).
    import re

    settled = []
    for p in (RESULTS / "datos").glob("etapa0[0-7]*/*.sqlite3"):
        m = re.search(r"(2026\d{4}T\d{6})", p.parent.name)
        if m and m.group(1) >= "20261111T233500":
            continue
        settled.append(p)
    protected = [
        *APP.glob("*.sqlite3"),
        *settled,
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]
    return {str(p.relative_to(ROOT)): digest(p) if p.exists() else None for p in protected}


def run_checks() -> int:
    start_hashes = protected_hashes()
    run_dir, out_dir, stamp = make_run_dir("checks")
    os.environ.update(AUDIT08_RUN_DIR=str(run_dir), AUDIT08_OUT=str(out_dir), AUDIT08_DEFAULT_COOKIES="1")
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
        AUDIT08_RUN_DIR=str(run_dir),
        AUDIT08_OUT=str(out_dir),
        AUDIT08_DEFAULT_COOKIES="1",
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
        AUDIT08_RUN_DIR=str(run_dir),
        AUDIT08_OUT=str(out_dir),
        AUDIT08_PYTHON=sys.executable,
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
        prepare_stage08_fixtures(run_dir, out_dir)
        write(out_dir / "orm-initial.json", snapshot())

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        os.environ["AUDIT08_PORT"] = str(port)
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
            ["node", str(SUPPORT / "audit08_browser.cjs")],
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
        raise SystemExit("Usage: audit08_run.py [checks|tests ...|browser|serve|snapshot]")
    action = sys.argv[1]
    if action == "serve":
        setup(default_cookies=False)
        from django.core.management import execute_from_command_line

        execute_from_command_line(
            ["manage.py", "runserver", f"127.0.0.1:{os.environ['AUDIT08_PORT']}", "--noreload", "--insecure"]
        )
        return 0
    if action == "snapshot":
        setup(default_cookies=False)
        print(json.dumps(snapshot(), ensure_ascii=False, default=str))
        return 0
    if action == "checks":
        return run_checks()
    if action == "tests":
        targets = sys.argv[2:] or ["inventory.test_audit08_writeoffs_adjustments_movements"]
        return run_tests(targets)
    if action == "browser":
        return run_browser()
    raise SystemExit(f"Unknown action: {action}")


if __name__ == "__main__":
    raise SystemExit(main())
