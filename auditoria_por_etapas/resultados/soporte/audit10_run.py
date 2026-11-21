"""Isolated Stage 10 runner (Django checks/tests, fixtures, snapshot, runserver, Chrome browser).
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
        os.environ["AUDIT10_DEFAULT_COOKIES"] = "1"
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit10_settings"
    import django

    django.setup()


def prepare_empty_migrated_db() -> None:
    from django.core.management import call_command

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)


def prepare_stage10_fixtures(run_dir: Path, out_dir: Path) -> dict:
    from django.utils import timezone as tz

    from cash.models import CashRegister, CashShift
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.models import Lot
    from inventory.services import LotInput, confirm_initial_load

    admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    creds = {}
    accounts = {}
    for key, email, display, role in [
        ("admin", "admin@audit10.invalid", "Admin Audit10", admin_role),
        ("warehouse", "warehouse@audit10.invalid", "Lucia Almacen10", wh_role),
        ("seller", "seller@audit10.invalid", "Carmen Vendedora10", seller_role),
        ("seller2", "seller2@audit10.invalid", "Marco Vendedor10", seller_role),
    ]:
        pw = secrets.token_urlsafe(18) + "A1!"
        creds[key] = {"email": email, "password": pw}
        accounts[key] = Account.objects.create_user(email, pw, display_name=display, role=role)

    (run_dir / ".credentials.json").write_text(json.dumps(creds), encoding="utf-8")

    cat_active = Category.objects.create(name="Conservas A10", is_active=True)
    cat_toggle = Category.objects.create(name="Bebidas Toggle A10", is_active=True)
    cat_off = Category.objects.create(name="Suspendida A10", is_active=False)

    today = tz.localdate()
    d_minus1 = today - timedelta(days=1)
    d_plus5 = today + timedelta(days=5)
    d_plus20 = today + timedelta(days=20)
    d_plus40 = today + timedelta(days=40)

    # 1. p_gtin: Atun con GTIN 13, lotes mixtos (vencido -1d=4, vence hoy=5, vigentes 4+2=6) -> sellable = 6
    p_gtin = Product.objects.create(
        category=cat_active,
        name="Atún en Lata GTIN A10",
        barcode="0775000000014",
        barcode_type=Product.BarcodeType.GTIN,
        sale_price=Decimal("5.90"),
        minimum_stock=2,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_gtin,
        lots=[
            LotInput("A10-EXP-PAST", 4, Decimal("2.5000"), d_plus5),
            LotInput("A10-EXP-TODAY", 5, Decimal("2.5000"), d_plus5),
            LotInput("A10-VIG-1", 4, Decimal("2.5000"), d_plus5),
            LotInput("A10-VIG-2", 2, Decimal("2.5000"), d_plus20),
        ],
    )
    Lot.objects.filter(product=p_gtin, number_normalized="A10-EXP-PAST").update(expiration_date=d_minus1)
    Lot.objects.filter(product=p_gtin, number_normalized="A10-EXP-TODAY").update(expiration_date=today)

    # 2. p_amp: Café & Pan Especial A10 with INTERNAL leading zeros -> price S/ 10.00, sellable = 8
    p_amp = Product.objects.create(
        category=cat_toggle,
        name="Café & Pan Especial A10",
        barcode="00A10-99",
        barcode_type=Product.BarcodeType.INTERNAL,
        sale_price=Decimal("10.00"),
        minimum_stock=2,
    )
    load_amp = confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_amp,
        lots=[LotInput("A10-AMP", 8, Decimal("4.0000"), d_plus40)],
    )
    lot_amp = load_amp.lots.get()

    # 3. p_long: 160-char unbroken product name + 64-char unbroken barcode -> sellable = 5
    long_name = (
        "ProductoSuperLargoSinEspaciosParaVerificarEnvolturaDeTablaYPanelDeBorradorEnMostradorDelMinimarketLimaPeruA10"
        + "X" * 60
    )[:160]
    long_barcode = ("7" * 64)[:64]
    p_long = Product.objects.create(
        category=cat_active,
        name=long_name,
        barcode=long_barcode,
        barcode_type=Product.BarcodeType.INTERNAL,
        sale_price=Decimal("9.90"),
        minimum_stock=1,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_long,
        lots=[LotInput("A10-LONG", 5, Decimal("5.0000"), d_plus40)],
    )

    # 4. Excluded controls: only today-expired, zero stock, inactive product, suspended category
    p_today_only = Product.objects.create(
        category=cat_active,
        name="Leche Solo Hoy A10",
        barcode="775010100001",
        sale_price=Decimal("4.50"),
        minimum_stock=2,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_today_only,
        lots=[LotInput("A10-ONLY-TODAY", 7, Decimal("2.0000"), d_plus5)],
    )
    Lot.objects.filter(product=p_today_only).update(expiration_date=today)

    p_zero = Product.objects.create(
        category=cat_active,
        name="Arroz Cero Stock A10",
        barcode="775010100002",
        sale_price=Decimal("4.00"),
        minimum_stock=2,
    )

    p_inactive = Product.objects.create(
        category=cat_active,
        name="Fideos Inactivo A10",
        barcode="775010100003",
        sale_price=Decimal("3.00"),
        minimum_stock=2,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_inactive,
        lots=[LotInput("A10-INACT", 6, Decimal("1.5000"), d_plus20)],
    )
    p_inactive.is_active = False
    p_inactive.save(update_fields=["is_active"])

    p_catoff = Product.objects.create(
        category=cat_active,
        name="Jugo Categoria Suspendida A10",
        barcode="775010100004",
        sale_price=Decimal("3.50"),
        minimum_stock=2,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_catoff,
        lots=[LotInput("A10-COFF", 6, Decimal("1.5000"), d_plus20)],
    )
    p_catoff.category = cat_off
    p_catoff.save(update_fields=["category"])

    reg = CashRegister.objects.create(code="CAJA-01")
    shift = CashShift.objects.create(cash_register=reg, seller=accounts["seller"], opening_amount=Decimal("100.00"))

    fixture = {
        "cash_register_code": reg.code,
        "shift_id": str(shift.pk),
        "categories": {
            "active": {"id": str(cat_active.pk), "name": cat_active.name},
            "toggle": {"id": str(cat_toggle.pk), "name": cat_toggle.name},
            "off": {"id": str(cat_off.pk), "name": cat_off.name},
        },
        "products": {
            "gtin": {"id": str(p_gtin.pk), "name": p_gtin.name, "barcode": p_gtin.barcode},
            "amp": {"id": str(p_amp.pk), "name": p_amp.name, "barcode": p_amp.barcode, "lot_id": str(lot_amp.pk)},
            "long": {"id": str(p_long.pk), "name": p_long.name, "barcode": p_long.barcode},
            "today_only": {"id": str(p_today_only.pk), "name": p_today_only.name, "barcode": p_today_only.barcode},
            "zero": {"id": str(p_zero.pk), "name": p_zero.name, "barcode": p_zero.barcode},
            "inactive": {"id": str(p_inactive.pk), "name": p_inactive.name, "barcode": p_inactive.barcode},
            "catoff": {"id": str(p_catoff.pk), "name": p_catoff.name, "barcode": p_catoff.barcode},
        },
    }
    write(out_dir / "fixture.json", fixture)
    return fixture


def snapshot() -> dict:
    from cash.models import CashShift, CashShiftClose
    from catalog.models import Category, Product
    from inventory.models import Lot, StockWriteOff
    from sales.models import Sale, SaleDraft, SaleDraftLine

    return {
        "categories": list(Category.objects.order_by("name").values("id", "name", "is_active")),
        "products": list(
            Product.objects.order_by("barcode").values("id", "name", "barcode", "sale_price", "is_active", "category_id")
        ),
        "lots": list(
            Lot.objects.order_by("expiration_date", "received_at", "id").values(
                "id", "product_id", "number_normalized", "initial_quantity", "available_quantity", "expiration_date"
            )
        ),
        "shifts": list(CashShift.objects.order_by("opened_at").values("id", "seller_id", "opening_amount", "status")),
        "closes": list(CashShiftClose.objects.order_by("closed_at").values("id", "cash_shift_id", "counted_amount", "expected_amount")),
        "drafts": list(SaleDraft.objects.order_by("created_at").values("id", "cash_shift_id", "seller_id", "status", "discarded_at")),
        "draft_lines": list(SaleDraftLine.objects.order_by("created_at", "id").values("id", "draft_id", "product_id", "quantity", "unit_price")),
        "sales": list(Sale.objects.order_by("correlative").values("id", "correlative", "total_amount")),
        "writeoffs": list(StockWriteOff.objects.order_by("correlativo").values("id", "correlativo", "lot_id", "quantity")),
    }


def make_run_dir(tag: str) -> tuple[Path, Path, str]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)
    run_dir = RESULTS / "datos" / f"etapa10-{tag}-{stamp}"
    out_dir = RESULTS / "evidencias" / f"10-{tag}-{stamp}"
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
    os.environ.update(AUDIT10_RUN_DIR=str(run_dir), AUDIT10_OUT=str(out_dir), AUDIT10_DEFAULT_COOKIES="1")
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
    end_hashes = {k: (digest(ROOT / k) if (ROOT / k).exists() else None) == v for k, v in start_hashes.items()}
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
    os.environ.update(AUDIT10_RUN_DIR=str(run_dir), AUDIT10_OUT=str(out_dir), AUDIT10_DEFAULT_COOKIES="1")
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
    end_hashes = {k: (digest(ROOT / k) if (ROOT / k).exists() else None) == v for k, v in start_hashes.items()}
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
    return 0 if (exit_code == 0 and all(end_hashes.values())) else 1


def run_browser() -> int:
    start_hashes = protected_hashes()
    run_dir, out_dir, stamp = make_run_dir("browser")
    os.environ.update(AUDIT10_RUN_DIR=str(run_dir), AUDIT10_OUT=str(out_dir), AUDIT10_PYTHON=sys.executable)
    result = {"action": "browser", "run": run_dir.name, "started_utc": stamp, "evidence": str(out_dir.relative_to(ROOT))}
    server = None
    port = 0
    try:
        setup(default_cookies=False)
        prepare_empty_migrated_db()
        prepare_stage10_fixtures(run_dir, out_dir)
        write(out_dir / "orm-initial.json", snapshot())

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        os.environ["AUDIT10_PORT"] = str(port)
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
            ["node", str(SUPPORT / "audit10_browser.cjs")],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=240,
        )
        result.update(browser_exit=child.returncode, browser_output=child.stdout, browser_error=child.stderr)
        write(out_dir / "orm-final.json", snapshot())
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
    if result.get("browser_exit", 1) != 0 or not result.get("port_closed") or not all(result["protected_unchanged"].values()):
        return 1
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: audit10_run.py [checks|tests ...|browser|serve|snapshot]")
    action = sys.argv[1]
    if action == "serve":
        setup(default_cookies=False)
        from django.core.management import execute_from_command_line

        execute_from_command_line(
            ["manage.py", "runserver", f"127.0.0.1:{os.environ['AUDIT10_PORT']}", "--noreload", "--insecure"]
        )
        return 0
    if action == "snapshot":
        setup(default_cookies=False)
        print(json.dumps(snapshot(), ensure_ascii=False, default=str))
        return 0
    if action == "checks":
        return run_checks()
    if action == "tests":
        targets = sys.argv[2:] or ["sales.test_audit10_draft"]
        return run_tests(targets)
    if action == "browser":
        return run_browser()
    raise SystemExit(f"Unknown action: {action}")


if __name__ == "__main__":
    raise SystemExit(main())
