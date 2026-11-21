"""Isolated Stage 07 runner (Django checks/tests, fixtures, snapshot, runserver, Chrome browser).
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
        os.environ["AUDIT07_DEFAULT_COOKIES"] = "1"
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit07_settings"
    import django

    django.setup()


def prepare_empty_migrated_db() -> None:
    from django.core.management import call_command

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)


def prepare_stage07_fixtures(run_dir: Path, out_dir: Path) -> dict:
    from django.utils import timezone as tz

    from cash.models import CashRegister, CashShift
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.models import InitialInventoryLoad, Lot
    from inventory.services import LotInput, confirm_initial_load, create_supplier
    from sales.services import add_product_to_draft, checkout_sale

    admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    creds = {}
    accounts = {}
    for key, email, display, role in [
        ("admin", "admin@audit07.invalid", "Admin Audit07", admin_role),
        ("warehouse", "warehouse@audit07.invalid", "Lucia Almacen07", wh_role),
        ("warehouse2", "warehouse2@audit07.invalid", "Pedro Almacen07", wh_role),
        ("seller", "seller@audit07.invalid", "Carmen Vendedora07", seller_role),
    ]:
        pw = secrets.token_urlsafe(18) + "A1!"
        creds[key] = {"email": email, "password": pw}
        accounts[key] = Account.objects.create_user(email, pw, display_name=display, role=role)

    (run_dir / ".credentials.json").write_text(json.dumps(creds), encoding="utf-8")

    cat_active = Category.objects.create(name="Cat Activa 07", is_active=True)
    cat_long = Category.objects.create(
        name="CategoriaExtensaParaProbarEnvolturaVisualEnConsultasYAlertasDelMinimarketLimaPeruSAC07"[:100],
        is_active=True,
    )
    cat_off = Category.objects.create(name="Cat Suspendida 07", is_active=False)

    sup_active = create_supplier(
        actor=accounts["admin"],
        name="Distribuidora Norte 07 SAC",
        ruc="20707070001",
        phone="01-5550071",
    )
    long_sup_name = (
        "ComercializadoraMayoristaContinentalDeAlimentosYBebidasDelPeru"
        "SociedadAnonimaCerradaDistribuidaEnAlmacenesLimaCallaoNorteSurCentroPeruSAC07"
    )[:160]
    sup_long = create_supplier(
        actor=accounts["admin"],
        name=long_sup_name,
        ruc="20707070002",
        phone="01-5550072",
    )

    today = tz.localdate()
    d_minus2 = today - timedelta(days=2)
    d_minus1 = today - timedelta(days=1)
    d_plus1 = today + timedelta(days=1)
    d_plus3 = today + timedelta(days=3)
    d_plus4 = today + timedelta(days=4)
    d_plus5 = today + timedelta(days=5)
    d_plus7 = today + timedelta(days=7)
    d_plus30 = today + timedelta(days=30)
    d_plus31 = today + timedelta(days=31)
    d_plus60 = today + timedelta(days=60)

    # 1. p_exp_mix: physical=17, sellable=10 == minimum_stock=10 (RN-06), ties on +1d, zero-qty lot, past/today/upcoming
    p_exp_mix = Product.objects.create(
        category=cat_active,
        name="Leche Mezcla Vencimientos 1L",
        barcode="775070700001",
        sale_price=Decimal("6.50"),
        minimum_stock=10,
    )
    t1 = tz.now() - timedelta(hours=3)
    t2 = tz.now() - timedelta(hours=1)
    with patch("django.utils.timezone.now", return_value=t1):
        load_mix = confirm_initial_load(
            actor=accounts["warehouse"],
            product=p_exp_mix,
            supplier=sup_active,
            lots=[
                LotInput("MIX-VENC-PAST", 3, Decimal("2.0000"), d_plus1),
                LotInput("mix-vence-hoy", 4, Decimal("2.2000"), d_plus1),
                LotInput("MIX-ZERO-EXP", 5, Decimal("2.4000"), d_plus1),
                LotInput("MIX-TIE-Z-FIRST", 2, Decimal("2.5000"), d_plus1),
                LotInput("MIX-DAY07", 6, Decimal("2.6000"), d_plus7),
            ],
        )
    with patch("django.utils.timezone.now", return_value=t2):
        Lot.objects.create(
            product=p_exp_mix,
            initial_load=load_mix,
            supplier=sup_active,
            responsible=accounts["warehouse2"],
            is_initial=False,
            number="MIX-TIE-A-SECOND",
            initial_quantity=2,
            available_quantity=2,
            unit_cost=Decimal("2.7000"),
            expiration_date=d_plus1,
        )
    Lot.objects.filter(product=p_exp_mix, number_normalized="MIX-VENC-PAST").update(expiration_date=d_minus2)
    Lot.objects.filter(product=p_exp_mix, number_normalized="MIX-VENCE-HOY").update(expiration_date=d_minus1)
    # Set exact today in Lima for MIX-VENCE-HOY
    Lot.objects.filter(product=p_exp_mix, number_normalized="MIX-VENCE-HOY").update(expiration_date=today)
    Lot.objects.filter(product=p_exp_mix, number_normalized="MIX-ZERO-EXP").update(available_quantity=0)

    # 2. p_exp_edge30: +30d (included in default) and +31d (excluded from 30d); sellable=9 > min=3
    p_exp_edge30 = Product.objects.create(
        category=cat_active,
        name="Yogurt Limite 30 Dias",
        barcode="775070700002",
        sale_price=Decimal("5.00"),
        minimum_stock=3,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_exp_edge30,
        supplier=sup_active,
        lots=[
            LotInput("D30-EXACT", 4, Decimal("2.0000"), d_plus30),
            LotInput("D31-OUT", 5, Decimal("2.1000"), d_plus31),
        ],
    )

    # 3. p_all_expired: only today-expired lot (physical=8, sellable=0, Sin stock vendible, blocked in POS)
    p_all_expired = Product.objects.create(
        category=cat_active,
        name="Conserva Solo Vencida 400g",
        barcode="775070700003",
        sale_price=Decimal("7.00"),
        minimum_stock=5,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_all_expired,
        lots=[LotInput("ONLY-VENC-HOY", 8, Decimal("3.0000"), d_plus1)],
    )
    Lot.objects.filter(product=p_all_expired).update(expiration_date=today)

    # 4. p_long_wrap: 140-char unbroken product name + 100-char cat + 64-char unbroken lot + 160-char unbroken supplier
    long_prod_name = ("ProductoUltraExtensoSinEspaciosParaValidarAjusteDeLineaEnTablaStockYVencimientos07" * 2)[:140]
    p_long_wrap = Product.objects.create(
        category=cat_long,
        name=long_prod_name,
        barcode="775070700004",
        sale_price=Decimal("4.00"),
        minimum_stock=2,
    )
    lot64 = "L" + ("X" * 63)
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_long_wrap,
        supplier=sup_long,
        lots=[LotInput(lot64, 3, Decimal("2.0000"), d_plus5)],
    )

    # 5. p_min_zero_empty: minimum_stock == 0 and zero stock (must count as low_stock / Sin stock vendible)
    p_min_zero_empty = Product.objects.create(
        category=cat_active,
        name="Avena Sin Minimo Cero Stock",
        barcode="775070700005",
        sale_price=Decimal("3.50"),
        minimum_stock=0,
    )

    # 6. p_min_zero_ok: minimum_stock == 0 and valid stock at +60d (OK, not low_stock, not in 30d alerts)
    p_min_zero_ok = Product.objects.create(
        category=cat_active,
        name="Sal Sin Minimo Con Stock",
        barcode="775070700006",
        sale_price=Decimal("2.00"),
        minimum_stock=0,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_min_zero_ok,
        lots=[LotInput("SAL-OK", 7, Decimal("1.0000"), d_plus60)],
    )

    # 7. p_inactive_prod: inactive product with both expired (-1d) and upcoming (+4d) lots
    p_inactive_prod = Product.objects.create(
        category=cat_active,
        name="Jugo Producto Deshabilitado",
        barcode="775070700007",
        sale_price=Decimal("9.00"),
        minimum_stock=10,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_inactive_prod,
        lots=[
            LotInput("INACT-VENC", 3, Decimal("3.0000"), d_plus1),
            LotInput("INACT-PROX", 2, Decimal("3.0000"), d_plus4),
        ],
    )
    Lot.objects.filter(product=p_inactive_prod, number_normalized="INACT-VENC").update(expiration_date=d_minus1)
    p_inactive_prod.is_active = False
    p_inactive_prod.save(update_fields=["is_active"])

    # 8. p_cat_off: active product inside inactive category (sellable=2 <= min=10; OBS-05-STOCK-CAT-INACTIVA)
    p_cat_off = Product.objects.create(
        category=cat_active,
        name="Galletas Categoria Suspendida",
        barcode="775070700008",
        sale_price=Decimal("4.50"),
        minimum_stock=10,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_cat_off,
        lots=[LotInput("CATOFF-PROX", 2, Decimal("2.0000"), d_plus3)],
    )
    p_cat_off.category = cat_off
    p_cat_off.save(update_fields=["category"])

    # Open CashShift + 1 confirmed sale today on p_min_zero_ok (2 x 2.00, no discount -> remaining sellable 5 > min 0)
    reg = CashRegister.objects.create(code="CAJA-01")
    CashShift.objects.create(cash_register=reg, seller=accounts["seller"], opening_amount=Decimal("100.00"))
    draft = add_product_to_draft(actor=accounts["seller"], product_id=p_min_zero_ok.pk, quantity=2)
    checkout_sale(
        actor=accounts["seller"],
        draft_id=draft.pk,
        cash_received=Decimal("10.00"),
        discount_amount=Decimal("0.50"),
        idempotency_key=uuid.uuid4(),
    )

    fixture = {
        "dates": {
            "minus2": d_minus2.isoformat(),
            "minus1": d_minus1.isoformat(),
            "today": today.isoformat(),
            "plus1": d_plus1.isoformat(),
            "plus3": d_plus3.isoformat(),
            "plus4": d_plus4.isoformat(),
            "plus5": d_plus5.isoformat(),
            "plus7": d_plus7.isoformat(),
            "plus30": d_plus30.isoformat(),
            "plus31": d_plus31.isoformat(),
            "plus60": d_plus60.isoformat(),
        },
        "expected_summary": {
            "sales_count": 1,
            "sales_total": "3.50",
            "discount_total": "0.50",
            "open_shifts": 1,
            "low_stock": 3,
            "expiring": 7,
            "expired": 4,
        },
        "lot64": lot64,
        "products": {
            "exp_mix": {"id": str(p_exp_mix.pk), "name": p_exp_mix.name},
            "exp_edge30": {"id": str(p_exp_edge30.pk), "name": p_exp_edge30.name},
            "all_expired": {"id": str(p_all_expired.pk), "name": p_all_expired.name},
            "long_wrap": {"id": str(p_long_wrap.pk), "name": p_long_wrap.name},
            "min_zero_empty": {"id": str(p_min_zero_empty.pk), "name": p_min_zero_empty.name},
            "min_zero_ok": {"id": str(p_min_zero_ok.pk), "name": p_min_zero_ok.name},
            "inactive_prod": {"id": str(p_inactive_prod.pk), "name": p_inactive_prod.name},
            "cat_off": {"id": str(p_cat_off.pk), "name": p_cat_off.name},
        },
    }
    write(out_dir / "fixture.json", fixture)
    return fixture


def snapshot() -> dict:
    from catalog.models import Category, Product
    from inventory.models import Lot, StockWriteOff
    from sales.models import Sale

    return {
        "categories": list(Category.objects.order_by("name").values("id", "name", "is_active")),
        "products": list(
            Product.objects.order_by("barcode").values(
                "id", "name", "barcode", "category_id", "is_active", "minimum_stock", "average_cost"
            )
        ),
        "lots": list(
            Lot.objects.order_by("expiration_date", "received_at", "id").values(
                "id",
                "product_id",
                "number",
                "number_normalized",
                "initial_quantity",
                "available_quantity",
                "expiration_date",
                "received_at",
            )
        ),
        "sales": list(Sale.objects.order_by("correlative").values("id", "correlative", "total_amount", "discount_amount")),
        "writeoffs": list(StockWriteOff.objects.order_by("correlativo").values("id", "correlativo", "lot_id", "quantity")),
    }


def make_run_dir(tag: str) -> tuple[Path, Path, str]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)
    run_dir = RESULTS / "datos" / f"etapa07-{tag}-{stamp}"
    out_dir = RESULTS / "evidencias" / f"07-{tag}-{stamp}"
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
    os.environ.update(AUDIT07_RUN_DIR=str(run_dir), AUDIT07_OUT=str(out_dir), AUDIT07_DEFAULT_COOKIES="1")
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
        AUDIT07_RUN_DIR=str(run_dir),
        AUDIT07_OUT=str(out_dir),
        AUDIT07_DEFAULT_COOKIES="1",
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
        AUDIT07_RUN_DIR=str(run_dir),
        AUDIT07_OUT=str(out_dir),
        AUDIT07_PYTHON=sys.executable,
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
        prepare_stage07_fixtures(run_dir, out_dir)
        write(out_dir / "orm-initial.json", snapshot())

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        os.environ["AUDIT07_PORT"] = str(port)
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
            ["node", str(SUPPORT / "audit07_browser.cjs")],
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
        raise SystemExit("Usage: audit07_run.py [checks|tests ...|browser|serve|snapshot]")
    action = sys.argv[1]
    if action == "serve":
        setup(default_cookies=False)
        from django.core.management import execute_from_command_line

        execute_from_command_line(
            ["manage.py", "runserver", f"127.0.0.1:{os.environ['AUDIT07_PORT']}", "--noreload", "--insecure"]
        )
        return 0
    if action == "snapshot":
        setup(default_cookies=False)
        print(json.dumps(snapshot(), ensure_ascii=False, default=str))
        return 0
    if action == "checks":
        return run_checks()
    if action == "tests":
        targets = sys.argv[2:] or ["inventory.test_audit07_stock_expirations"]
        return run_tests(targets)
    if action == "browser":
        return run_browser()
    raise SystemExit(f"Unknown action: {action}")


if __name__ == "__main__":
    raise SystemExit(main())

