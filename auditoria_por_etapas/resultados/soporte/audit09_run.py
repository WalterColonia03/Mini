"""Isolated Stage 09 runner (Django checks/tests, fixtures, snapshot, runserver, Chrome browser).
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
        os.environ["AUDIT09_DEFAULT_COOKIES"] = "1"
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit09_settings"
    import django

    django.setup()


def prepare_empty_migrated_db() -> None:
    from django.core.management import call_command

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)


def prepare_stage09_fixtures(run_dir: Path, out_dir: Path) -> dict:
    from django.utils import timezone as tz

    from cash.models import CashRegister
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.services import LotInput, confirm_initial_load, create_supplier

    admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    creds = {}
    accounts = {}
    for key, email, display, role in [
        ("admin", "admin@audit09.invalid", "Admin Audit09", admin_role),
        ("warehouse", "warehouse@audit09.invalid", "Almacen Audit09", wh_role),
        ("seller1", "seller1@audit09.invalid", "Ana Cajera09", seller_role),
        (
            "seller2",
            "seller2@audit09.invalid",
            "BetoVendedorConNombreExtensoParaVerificarEnvolturaDeHistorialYActasEnMinimarketLimaPeru09",
            seller_role,
        ),
    ]:
        pw = secrets.token_urlsafe(18) + "A1!"
        creds[key] = {"email": email, "password": pw, "display_name": display}
        accounts[key] = Account.objects.create_user(email, pw, display_name=display, role=role)

    (run_dir / ".credentials.json").write_text(json.dumps(creds), encoding="utf-8")

    # Seed the single register CAJA-01 without opening any shift initially
    reg = CashRegister.objects.create(code="CAJA-01")

    cat = Category.objects.create(name="Abarrotes Audit09", is_active=True)
    sup = create_supplier(
        actor=accounts["admin"],
        name="Proveedor Caja 09 SAC",
        ruc="20909090001",
        phone="01-5550091",
    )
    future = tz.localdate() + timedelta(days=90)

    p1 = Product.objects.create(
        category=cat,
        name="Arroz Extra 1kg Audit09",
        barcode="775090900001",
        sale_price=Decimal("5.50"),
        minimum_stock=2,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p1,
        supplier=sup,
        lots=[LotInput("LOT-ARROZ-09", 30, Decimal("3.2000"), future)],
    )

    p2 = Product.objects.create(
        category=cat,
        name="Aceite Vegetal 1L Audit09",
        barcode="775090900002",
        sale_price=Decimal("12.00"),
        minimum_stock=2,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p2,
        supplier=sup,
        lots=[LotInput("LOT-ACEITE-09", 20, Decimal("8.0000"), future)],
    )

    fixture = {
        "register": {"id": str(reg.pk), "code": reg.code},
        "products": {
            "p1": {"id": str(p1.pk), "name": p1.name, "barcode": p1.barcode, "sale_price": "5.50"},
            "p2": {"id": str(p2.pk), "name": p2.name, "barcode": p2.barcode, "sale_price": "12.00"},
        },
        "accounts": {
            k: {"id": str(v.pk), "display_name": v.display_name, "role": v.role.code}
            for k, v in accounts.items()
        },
    }
    write(out_dir / "fixture.json", fixture)
    return fixture


def snapshot() -> dict:
    from cash.models import CashRegister, CashShift, CashShiftClose
    from inventory.models import Lot
    from sales.models import Sale, SaleDraft

    return {
        "registers": list(CashRegister.objects.order_by("code").values("id", "code", "is_active")),
        "shifts": list(
            CashShift.objects.order_by("opened_at", "id").values(
                "id", "cash_register_id", "seller_id", "opening_amount", "status", "opened_at"
            )
        ),
        "closes": list(
            CashShiftClose.objects.order_by("closed_at", "id").values(
                "id",
                "cash_shift_id",
                "counted_amount",
                "expected_amount",
                "difference",
                "closed_by_id",
                "closed_at",
            )
        ),
        "drafts": list(
            SaleDraft.objects.order_by("created_at", "id").values("id", "cash_shift_id", "seller_id", "status")
        ),
        "sales": list(
            Sale.objects.order_by("correlative").values(
                "id",
                "correlative",
                "cash_shift_id",
                "seller_id",
                "total_amount",
                "discount_amount",
                "cash_received",
                "change_given",
            )
        ),
        "lots": list(Lot.objects.order_by("number_normalized").values("id", "number_normalized", "available_quantity")),
    }


def make_run_dir(tag: str) -> tuple[Path, Path, str]:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)
    run_dir = RESULTS / "datos" / f"etapa09-{tag}-{stamp}"
    out_dir = RESULTS / "evidencias" / f"09-{tag}-{stamp}"
    run_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    write(run_dir / "marker.json", {"run": run_dir.name, "created_utc": stamp})
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")
    return run_dir, out_dir, stamp


def protected_hashes() -> dict[str, str | None]:
    archived_prefixes = (
        "etapa00",
        "etapa01",
        "etapa02",
        "etapa03",
        "etapa04",
        "etapa05",
        "etapa06",
        "etapa07",
        "etapa09",
    )
    archived_dbs = sorted(
        p
        for p in (RESULTS / "datos").rglob("*.sqlite3")
        if p.parent.name.startswith(archived_prefixes)
    )
    protected = [
        *APP.glob("*.sqlite3"),
        *archived_dbs,
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]
    return {str(p.relative_to(ROOT)): digest(p) if p.exists() else None for p in protected}


def run_checks() -> int:
    start_hashes = protected_hashes()
    run_dir, out_dir, stamp = make_run_dir("checks")
    os.environ.update(AUDIT09_RUN_DIR=str(run_dir), AUDIT09_OUT=str(out_dir), AUDIT09_DEFAULT_COOKIES="1")
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
        AUDIT09_RUN_DIR=str(run_dir),
        AUDIT09_OUT=str(out_dir),
        AUDIT09_DEFAULT_COOKIES="1",
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
        AUDIT09_RUN_DIR=str(run_dir),
        AUDIT09_OUT=str(out_dir),
        AUDIT09_PYTHON=sys.executable,
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
        prepare_stage09_fixtures(run_dir, out_dir)
        write(out_dir / "orm-initial.json", snapshot())

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        os.environ["AUDIT09_PORT"] = str(port)
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
            ["node", str(SUPPORT / "audit09_browser.cjs")],
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
        raise SystemExit("Usage: audit09_run.py [checks|tests ...|browser|serve|snapshot]")
    action = sys.argv[1]
    if action == "serve":
        setup(default_cookies=False)
        from django.core.management import execute_from_command_line

        execute_from_command_line(
            ["manage.py", "runserver", f"127.0.0.1:{os.environ['AUDIT09_PORT']}", "--noreload", "--insecure"]
        )
        return 0
    if action == "snapshot":
        setup(default_cookies=False)
        print(json.dumps(snapshot(), ensure_ascii=False, default=str))
        return 0
    if action == "checks":
        return run_checks()
    if action == "tests":
        targets = sys.argv[2:] or ["cash"]
        return run_tests(targets)
    if action == "browser":
        return run_browser()
    raise SystemExit(f"Unknown action: {action}")


if __name__ == "__main__":
    raise SystemExit(main())
