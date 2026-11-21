"""Isolated live-server + Chrome Stage 07-B audit runner (empty DB + full scenario + mobile 390x844)."""

from __future__ import annotations

import hashlib
import http.client
import json
import os
import shutil
import socket
import subprocess
import sys
import time
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
R1_PMV = ROOT / "r1-pmv"
SUPPORT = Path(__file__).resolve().parent
EVID_DIR = ROOT / "auditoria_por_etapas" / "resultados" / "evidencias" / "07-B-20261114"
BROWSER_EVID = EVID_DIR / "browser"

sys.path.insert(0, str(SUPPORT))
sys.path.insert(0, str(R1_PMV))

import audit07_run


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def wait_server(port: int, proc: subprocess.Popen, log_path: Path, timeout_s: float = 25.0) -> None:
    deadline = time.monotonic() + timeout_s
    last_err = None
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"Server exited early ({proc.returncode}): log={log_path.read_text(encoding='utf-8', errors='replace')}")
        try:
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=1.5)
            conn.request("GET", "/", headers={"Host": f"127.0.0.1:{port}"})
            resp = conn.getresponse()
            resp.read()
            conn.close()
            if resp.status < 500:
                return
            last_err = f"HTTP {resp.status}"
        except Exception as exc:
            last_err = repr(exc)
            time.sleep(0.15)
    raise TimeoutError(f"Server did not answer on port {port} (last_err={last_err}): log={log_path.read_text(encoding='utf-8', errors='replace')}")


def wait_port_closed(port: int, timeout_s: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return True
        time.sleep(0.1)
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def seed_accounts_only() -> dict:
    from django.core.management import call_command
    from django.utils import timezone
    from cash.models import CashRegister
    from identity.models import Account, Role

    call_command("migrate", verbosity=0)
    CashRegister.objects.get_or_create(code="CAJA-01", defaults={"is_active": True})
    roles = {r.code: r for r in Role.objects.all()}
    for code, name in [
        (Role.Code.ADMIN, "Administrador"),
        (Role.Code.WAREHOUSE, "Almacenero"),
        (Role.Code.SELLER, "Vendedor"),
    ]:
        if code not in roles:
            roles[code] = Role.objects.create(code=code, name=name)

    accounts = {}
    for key, email, disp, rcode in [
        ("admin", "admin07b@audit.local", "Admin 07B", Role.Code.ADMIN),
        ("warehouse", "alm07b@audit.local", "Almacenero 07B", Role.Code.WAREHOUSE),
        ("seller", "vend07b@audit.local", "Vendedor 07B", Role.Code.SELLER),
    ]:
        pw = "Audit07B#Pass2026"
        Account.objects.create_user(email, pw, display_name=disp, role=roles[rcode])
        accounts[key] = {"email": email, "password": pw, "display_name": disp}
    return {
        "today_lima": str(timezone.localdate()),
        "accounts": accounts,
    }


def seed_full_stage07(info: dict) -> dict:
    from django.utils import timezone
    from cash.services import open_cash_shift
    from catalog.models import Category, Product
    from catalog.services import toggle_product_availability
    from identity.models import Account
    from inventory.models import Lot, StockWriteOff, Supplier
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        register_physical_adjustment,
        register_stock_entry,
        write_off_stock,
    )

    today = timezone.localdate()
    past_biz_date = today - timedelta(days=5)
    admin = Account.objects.get(email=info["accounts"]["admin"]["email"])
    wh = Account.objects.get(email=info["accounts"]["warehouse"]["email"])
    seller = Account.objects.get(email=info["accounts"]["seller"]["email"])

    cat_lacteos = Category.objects.create(name="Lácteos")
    cat_bebidas = Category.objects.create(name="Bebidas")
    cat_granos = Category.objects.create(name="Granos")
    sup = Supplier.objects.create(name="Distribuidora Andina", ruc="20456789012")

    p_mixto = Product.objects.create(
        name="Yogurt Vencimiento Mixto", category=cat_lacteos, barcode="7750070001011",
        unit="UND", sale_price=Decimal("8.50"), minimum_stock=8, is_active=True, controls_expiration=True,
    )
    confirm_initial_load(
        actor=wh, product=p_mixto, supplier=sup, business_date=past_biz_date,
        lots=[
            LotInput("YT-EXP", 7, Decimal("5.0000"), today - timedelta(days=2)),
            LotInput("YT-1D", 5, Decimal("5.0000"), today + timedelta(days=1)),
            LotInput("YT-30D", 3, Decimal("5.0000"), today + timedelta(days=30)),
        ],
    )

    p_q31 = Product.objects.create(
        name="Queso Fresco 31D", category=cat_lacteos, barcode="7750070001028",
        unit="UND", sale_price=Decimal("12.00"), minimum_stock=2, is_active=True, controls_expiration=True,
    )
    confirm_initial_load(
        actor=wh, product=p_q31, supplier=sup, business_date=today,
        lots=[LotInput("QF-31D", 4, Decimal("7.0000"), today + timedelta(days=31))],
    )

    p_inact_hoy = Product.objects.create(
        name="Producto E Vence Hoy", category=cat_lacteos, barcode="7750070001035",
        unit="UND", sale_price=Decimal("4.00"), minimum_stock=5, is_active=True, controls_expiration=True,
    )
    confirm_initial_load(
        actor=wh, product=p_inact_hoy, supplier=sup, business_date=past_biz_date,
        lots=[LotInput("LE-HOY", 3, Decimal("2.0000"), today)],
    )
    toggle_product_availability(actor=admin, product=p_inact_hoy, is_active=False)

    p_gaseosa_susp = Product.objects.create(
        name="Gaseosa Suspendida Cat", category=cat_bebidas, barcode="7750070001042",
        unit="UND", sale_price=Decimal("3.50"), minimum_stock=10, is_active=True, controls_expiration=True,
    )
    confirm_initial_load(
        actor=wh, product=p_gaseosa_susp, supplier=sup, business_date=today,
        lots=[LotInput("GAS-7D", 4, Decimal("2.0000"), today + timedelta(days=7))],
    )
    toggle_product_availability(actor=admin, product=p_gaseosa_susp, is_active=False)

    p_agua_cat = Product.objects.create(
        name="Agua Cat Activa", category=cat_bebidas, barcode="7750070001059",
        unit="UND", sale_price=Decimal("2.50"), minimum_stock=10, is_active=True, controls_expiration=True,
    )
    confirm_initial_load(
        actor=wh, product=p_agua_cat, supplier=sup, business_date=today,
        lots=[LotInput("AG-10D", 4, Decimal("1.0000"), today + timedelta(days=10))],
    )

    p_arroz = Product.objects.create(
        name="Arroz Ajustado Origen", category=cat_granos, barcode="7750070001066",
        unit="UND", sale_price=Decimal("4.80"), minimum_stock=10, is_active=True, controls_expiration=True,
    )
    confirm_initial_load(
        actor=wh, product=p_arroz, supplier=sup, business_date=past_biz_date,
        lots=[LotInput("AR-INIT", 2, Decimal("3.0000"), today + timedelta(days=15))],
    )
    lot_ar_init = Lot.objects.get(product=p_arroz, number_normalized="AR-INIT")
    write_off_stock(actor=wh, lot=lot_ar_init, quantity=2, reason=StockWriteOff.Reason.DAMAGE, notes="Agotar lote a cero")
    register_physical_adjustment(
        actor=admin, product=p_arroz, number="AR-ADJ-HOY",
        expiration_date=today, delta=2, unit_cost=Decimal("3.0000"),
        cost_source="Conteo físico audit07b", reason="Lote descubierto en conteo",
    )
    register_stock_entry(
        actor=wh, product=p_arroz, supplier=sup,
        lots=[LotInput("AR-REC-1D", 5, Decimal("3.2000"), today + timedelta(days=1))],
    )

    Product.objects.create(
        name="Sal Min Cero", category=cat_granos, barcode="7750070001073",
        unit="UND", sale_price=Decimal("1.50"), minimum_stock=0, is_active=True, controls_expiration=True,
    )

    open_cash_shift(actor=seller, opening_amount=Decimal("50.00"))
    lot_yt_exp = Lot.objects.get(number_normalized="YT-EXP")

    return {
        **info,
        "bebidas_cat_id": str(cat_bebidas.pk),
        "yt_exp_lot_id": str(lot_yt_exp.pk),
        "lot_ar_init_id": str(lot_ar_init.pk),
    }


def launch_and_run_phase(phase: str, cfg: dict, out_json: Path) -> dict:
    port = free_port()
    os.environ["AUDIT07_PORT"] = str(port)
    env = {**os.environ, "AUDIT07_PORT": str(port), "AUDIT07_DEFAULT_COOKIES": "1"}
    run_dir = Path(os.environ["AUDIT07_RUN_DIR"])
    log_path = run_dir / f"server_{phase}.log"
    with log_path.open("w", encoding="utf-8") as log_f:
        proc = subprocess.Popen(
            [sys.executable, str(SUPPORT / "audit07_run.py"), "serve"],
            cwd=str(R1_PMV),
            env=env,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            text=True,
        )
        try:
            wait_server(port, proc, log_path)
            cfg_file = run_dir / f"browser_{phase}.json"
            cfg_with_urls = {
                **cfg,
                "phase": phase,
                "baseUrl": f"http://127.0.0.1:{port}",
                "screenshotsDir": str(BROWSER_EVID),
                "resultPath": str(out_json),
            }
            cfg_file.write_text(json.dumps(cfg_with_urls, indent=2), encoding="utf-8")
            run = subprocess.run(
                ["node", str(SUPPORT / "audit07b_browser.cjs"), str(cfg_file)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            return {
                "returncode": run.returncode,
                "stdout": run.stdout,
                "stderr": run.stderr,
                "result": json.loads(out_json.read_text(encoding="utf-8")) if out_json.exists() else None,
            }
        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
            closed = wait_port_closed(port)
            if not closed:
                raise RuntimeError(f"Port {port} remained open after server shutdown!")


def main() -> int:
    BROWSER_EVID.mkdir(parents=True, exist_ok=True)
    before = audit07_run.protected_hashes()

    # Phase 1: Empty DB
    run_dir_empty, _, _ = audit07_run.make_run_dir("07b-browser-empty")
    os.environ["AUDIT07_RUN_DIR"] = str(run_dir_empty)
    os.environ["AUDIT07_OUT"] = str(EVID_DIR)
    os.environ["AUDIT07_DEFAULT_COOKIES"] = "1"
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit07_settings"
    import django
    django.setup()
    from django.db import connections

    cfg_empty = seed_accounts_only()
    connections.close_all()
    res_empty = launch_and_run_phase("empty", cfg_empty, EVID_DIR / "browser-07b-empty.json")

    # Phase 2: Full Stage 07 DB in fresh subprocess via helper script invocation
    run_dir_full, _, _ = audit07_run.make_run_dir("07b-browser-full")
    seed_proc = subprocess.run(
        [sys.executable, __file__, "--seed-full", str(run_dir_full)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    cfg_full = json.loads(seed_proc.stdout.strip().splitlines()[-1])
    os.environ["AUDIT07_RUN_DIR"] = str(run_dir_full)
    res_full = launch_and_run_phase("full", cfg_full, EVID_DIR / "browser-07b-full.json")

    after = audit07_run.protected_hashes()
    must_hold_keys = [
        k
        for k in before
        if (
            k.startswith("r1-pmv\\")
            or k.startswith("PLANIFICACION_SCRUM_R1PMV")
            or ("etapa07" in k.lower() and "07b-browser-" not in k.lower())
            or (
                "20261114" not in k
                and "20261115" not in k
                and "11b-" not in k.lower()
                and not k.startswith("datos\\temp")
            )
        )
    ]
    unchanged_core = all(before[k] == after.get(k) for k in must_hold_keys)
    concurrent_drifted = [k for k in before if before[k] != after.get(k)]
    summary = {
        "protected_core_unchanged": unchanged_core,
        "must_hold_count": len(must_hold_keys),
        "concurrent_external_db_changes": concurrent_drifted,
        "empty_returncode": res_empty["returncode"],
        "full_returncode": res_full["returncode"],
        "empty_checks": (res_empty.get("result") or {}).get("checks"),
        "full_checks": (res_full.get("result") or {}).get("checks"),
    }
    (EVID_DIR / "browser-07b-summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    if not unchanged_core or res_empty["returncode"] != 0 or res_full["returncode"] != 0:
        if res_empty["stderr"] or res_full["stderr"]:
            print("EMPTY STDERR:", res_empty["stderr"])
            print("FULL STDERR:", res_full["stderr"])
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--seed-full":
        run_dir = Path(sys.argv[2])
        os.environ["AUDIT07_RUN_DIR"] = str(run_dir)
        os.environ["AUDIT07_DEFAULT_COOKIES"] = "1"
        os.environ["DJANGO_SETTINGS_MODULE"] = "audit07_settings"
        import django
        django.setup()
        info = seed_accounts_only()
        full_cfg = seed_full_stage07(info)
        print(json.dumps(full_cfg))
        raise SystemExit(0)
    raise SystemExit(main())
