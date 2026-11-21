"""Stage 10-B isolated runner: full Django test suite + deep probe + live Chrome test server."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone as dt_tz
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parents[0]
ROOT = RESULTS.parents[1]
PMV = ROOT / "r1-pmv"
PYTHON = PMV / ".venv" / "Scripts" / "python.exe"
EV_DIR = RESULTS / "evidencias" / "10-B-20261114"
OPERATIONAL_DB = PMV / "r1_pmv.sqlite3"


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_isolated_run_dir() -> Path:
    stamp = datetime.now(dt_tz.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = RESULTS / "datos" / f"etapa10b-{stamp}-{secrets.token_hex(4)}"
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "marker.json").write_text(
        json.dumps({"run": run_dir.name, "stage": "10-B", "created_utc": stamp}),
        encoding="utf-8",
    )
    (run_dir / ".django-key").write_text("audit10b-" + secrets.token_hex(32), encoding="utf-8")
    return run_dir


def base_env(run_dir: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(
        {
            "AUDIT10B_RUN_DIR": str(run_dir),
            "DJANGO_SETTINGS_MODULE": "audit10b_settings",
            "PYTHONPATH": str(HERE) + os.pathsep + str(PMV),
            "PYTHONUTF8": "1",
        }
    )
    return env


def run_cmd(cmd: list[str], env: dict[str, str], cwd: Path = PMV) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, env=env, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace")


def cmd_all_tests() -> int:
    EV_DIR.mkdir(parents=True, exist_ok=True)
    db_before = file_sha256(OPERATIONAL_DB) if OPERATIONAL_DB.exists() else None
    run_dir = create_isolated_run_dir()
    env = base_env(run_dir)
    try:
        r_check = run_cmd([str(PYTHON), "manage.py", "check", "--settings=audit10b_settings"], env)
        r_makemig = run_cmd([str(PYTHON), "manage.py", "makemigrations", "--check", "--dry-run", "--settings=audit10b_settings"], env)
        r_migrate = run_cmd([str(PYTHON), "manage.py", "migrate", "--noinput", "--settings=audit10b_settings"], env)
        test_env = env.copy()
        test_env["AUDIT10B_DEFAULT_COOKIES"] = "1"
        r_test = run_cmd([str(PYTHON), "manage.py", "test", "--settings=audit10b_settings", "-v", "2"], test_env)
        (EV_DIR / "django-full-suite.txt").write_text(
            f"=== CMD: manage.py test --settings=audit10b_settings -v 2 (AUDIT10B_DEFAULT_COOKIES=1 for legacy tests expecting csrftoken) ===\nEXIT: {r_test.returncode}\n\n"
            f"--- STDOUT ---\n{r_test.stdout}\n\n--- STDERR ---\n{r_test.stderr}\n",
            encoding="utf-8",
        )
        r_test_10 = run_cmd([str(PYTHON), "manage.py", "test", "sales.test_audit10_draft", "--settings=audit10b_settings", "-v", "2"], test_env)
        (EV_DIR / "django-sales10-suite.txt").write_text(
            f"EXIT: {r_test_10.returncode}\n\n--- STDOUT ---\n{r_test_10.stdout}\n\n--- STDERR ---\n{r_test_10.stderr}\n",
            encoding="utf-8",
        )
        probe_out = EV_DIR / "probe-10b.json"
        r_probe = run_cmd([str(PYTHON), str(HERE / "audit10b_probe.py"), str(probe_out)], env, cwd=ROOT)
        db_after = file_sha256(OPERATIONAL_DB) if OPERATIONAL_DB.exists() else None

        # Extract exact Ran X tests summary lines from Django test stderr
        summary_full = [ln for ln in (r_test.stderr or "").splitlines() if ln.startswith("Ran ") or ln in ("OK", "FAILED")]
        summary_s10 = [ln for ln in (r_test_10.stderr or "").splitlines() if ln.startswith("Ran ") or ln in ("OK", "FAILED")]
        manifest = {
            "timestamp_utc": datetime.now(dt_tz.utc).isoformat(),
            "operational_db_sha256_before": db_before,
            "operational_db_sha256_after": db_after,
            "operational_db_untouched": db_before == db_after,
            "check_exit": r_check.returncode,
            "check_output": (r_check.stdout + r_check.stderr).strip(),
            "makemigrations_check_exit": r_makemig.returncode,
            "makemigrations_check_output": (r_makemig.stdout + r_makemig.stderr).strip(),
            "migrate_exit": r_migrate.returncode,
            "full_suite_exit": r_test.returncode,
            "full_suite_summary": summary_full,
            "sales10_suite_exit": r_test_10.returncode,
            "sales10_suite_summary": summary_s10,
            "probe_exit": r_probe.returncode,
            "probe_stderr": (r_probe.stderr or "").strip(),
        }
        (EV_DIR / "tests-manifiesto.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        if db_before != db_after:
            return 2
        return 0 if (r_check.returncode == 0 and r_makemig.returncode == 0 and r_test.returncode == 0 and r_probe.returncode == 0) else 1
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def seed_browser_fixture(run_dir: Path, creds: dict[str, str]) -> dict:
    sys.path.insert(0, str(PMV))
    sys.path.insert(0, str(HERE))
    os.environ["AUDIT10B_RUN_DIR"] = str(run_dir)
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit10b_settings"
    import django
    django.setup()
    from django.utils import timezone
    from cash.models import CashRegister
    from catalog.models import Product
    from catalog.services import create_category, register_canned_product
    from identity.models import Account, Role
    from inventory.models import Lot
    from inventory.services import LotInput, confirm_initial_load, create_supplier

    r_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    r_sell, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

    admin = Account.objects.create_user(email=creds["admin_email"], display_name="Admin 10B", role=r_admin, password=creds["password"])
    wh = Account.objects.create_user(email=creds["wh_email"], display_name="Almacenero 10B", role=r_wh, password=creds["password"])
    Account.objects.create_user(email=creds["seller_email"], display_name="Vendedor 10B", role=r_sell, password=creds["password"])
    Account.objects.create_user(email=creds["seller2_email"], display_name="Vendedor2 10B", role=r_sell, password=creds["password"])
    CashRegister.objects.create(code="CAJA-01", is_active=True)

    cat = create_category(actor=admin, name="Productos enlatados")
    cat2 = create_category(actor=admin, name="Bebidas 10B")
    sup = create_supplier(actor=admin, name="Distribuidora Demo 10B", ruc="20123456786", phone="999000111")
    today = timezone.localdate()

    p_tuna = register_canned_product(
        actor=admin, name="Atún Clásico 170g", barcode="7750001000013", category=cat, unit="UND",
        sale_price=Decimal("6.50"), minimum_stock=5, barcode_type=Product.BarcodeType.GTIN,
    )
    confirm_initial_load(
        actor=wh, product=p_tuna, supplier=sup, business_date=today,
        lots=[
            LotInput(number="LOT-EXP-01", quantity=4, unit_cost=Decimal("3.00"), expiration_date=today + timedelta(days=1)),
            LotInput(number="LOT-FEFO-1", quantity=5, unit_cost=Decimal("3.00"), expiration_date=today + timedelta(days=5)),
            LotInput(number="LOT-FEFO-2", quantity=10, unit_cost=Decimal("3.00"), expiration_date=today + timedelta(days=30)),
        ],
    )
    Lot.objects.filter(product=p_tuna, number="LOT-EXP-01").update(expiration_date=today - timedelta(days=1))

    p_sard = register_canned_product(
        actor=admin, name="Sardina Picante 200g", barcode="7750001000020", category=cat, unit="UND",
        sale_price=Decimal("10.00"), minimum_stock=3, barcode_type=Product.BarcodeType.GTIN,
    )
    confirm_initial_load(
        actor=wh, product=p_sard, supplier=sup, business_date=today,
        lots=[LotInput(number="LOT-MAN", quantity=3, unit_cost=Decimal("5.00"), expiration_date=today + timedelta(days=1))],
    )

    p_oil = register_canned_product(
        actor=admin, name="Aceite Dorado 1L", barcode="7750001000037", category=cat, unit="UND",
        sale_price=Decimal("12.30"), minimum_stock=2, barcode_type=Product.BarcodeType.GTIN,
    )
    confirm_initial_load(
        actor=wh, product=p_oil, supplier=sup, business_date=today,
        lots=[LotInput(number="LOT-ACE-1", quantity=8, unit_cost=Decimal("7.00"), expiration_date=today + timedelta(days=60))],
    )

    p_zero = register_canned_product(
        actor=admin, name="Conserva Sin Stock", barcode="7750001000044", category=cat, unit="UND",
        sale_price=Decimal("4.00"), minimum_stock=2, barcode_type=Product.BarcodeType.GTIN,
    )
    confirm_initial_load(
        actor=wh, product=p_zero, supplier=sup, business_date=today,
        lots=[LotInput(number="LOT-Z0", quantity=2, unit_cost=Decimal("2.00"), expiration_date=today + timedelta(days=1))],
    )
    # RN-03 boundary: expiration_date == today is NOT sellable in Lima ("igual o anterior").
    Lot.objects.filter(product=p_zero).update(expiration_date=today)

    long_name = ("Duraznos en Almíbar Premium Extra Seleccionados Lata Familiar 820g Minimarket 10B " * 2)[:160]
    long_barcode = "INT-" + "9" * 60
    p_long = register_canned_product(
        actor=admin, name=long_name, barcode=long_barcode, category=cat, unit="UND",
        sale_price=Decimal("99.90"), minimum_stock=1, barcode_type=Product.BarcodeType.INTERNAL,
    )
    confirm_initial_load(
        actor=wh, product=p_long, supplier=sup, business_date=today,
        lots=[LotInput(number="LOT-LONG", quantity=20, unit_cost=Decimal("40.00"), expiration_date=today + timedelta(days=45))],
    )

    p_cafe = register_canned_product(
        actor=admin, name="Café & Té 100g", barcode="775-001-10B", category=cat2, unit="UND",
        sale_price=Decimal("5.25"), minimum_stock=1, barcode_type=Product.BarcodeType.INTERNAL,
    )
    confirm_initial_load(
        actor=wh, product=p_cafe, supplier=sup, business_date=today,
        lots=[LotInput(number="LOT-CAFE", quantity=6, unit_cost=Decimal("2.50"), expiration_date=today + timedelta(days=20))],
    )

    return {
        "tuna_id": str(p_tuna.pk),
        "tuna_barcode": p_tuna.barcode,
        "sard_id": str(p_sard.pk),
        "sard_barcode": p_sard.barcode,
        "oil_id": str(p_oil.pk),
        "oil_barcode": p_oil.barcode,
        "zero_barcode": p_zero.barcode,
        "long_id": str(p_long.pk),
        "long_name": p_long.name,
        "long_barcode": p_long.barcode,
        "cafe_id": str(p_cafe.pk),
        "cafe_barcode": p_cafe.barcode,
        "cat_id": str(cat.pk),
        "cat2_id": str(cat2.pk),
    }


def cmd_browser() -> int:
    EV_DIR.mkdir(parents=True, exist_ok=True)
    browser_dir = EV_DIR / "browser"
    browser_dir.mkdir(parents=True, exist_ok=True)
    db_before = file_sha256(OPERATIONAL_DB) if OPERATIONAL_DB.exists() else None
    run_dir = create_isolated_run_dir()
    env = base_env(run_dir)
    creds = {
        "admin_email": "admin.10b@demo.invalid",
        "wh_email": "almacen.10b@demo.invalid",
        "seller_email": "vendedor.10b@demo.invalid",
        "seller2_email": "vendedor2.10b@demo.invalid",
        "password": f"Br10b!{secrets.token_hex(8)}",
    }
    server_proc = None
    try:
        r_mig = run_cmd([str(PYTHON), "manage.py", "migrate", "--noinput", "--settings=audit10b_settings"], env)
        if r_mig.returncode != 0:
            raise RuntimeError(f"Migrate failed: {r_mig.stderr}")

        # Seed isolated browser DB in a child python snippet using env json
        seed_script = (
            "import json, os, sys; sys.path.insert(0, r'" + str(HERE) + "'); "
            "from audit10b_run import seed_browser_fixture; "
            "from pathlib import Path; "
            "print(json.dumps(seed_browser_fixture(Path(os.environ['AUDIT10B_RUN_DIR']), json.loads(os.environ['AUDIT10B_SEED_CREDS']))))"
        )
        seed_env = env.copy()
        seed_env["AUDIT10B_SEED_CREDS"] = json.dumps(creds)
        r_seed = run_cmd([str(PYTHON), "-c", seed_script], seed_env, cwd=ROOT)
        if r_seed.returncode != 0:
            raise RuntimeError(f"Seed failed: {r_seed.stdout}\n{r_seed.stderr}")
        meta = json.loads(r_seed.stdout.strip().splitlines()[-1])

        port = free_port()
        base_url = f"http://127.0.0.1:{port}"
        srv_out = (run_dir / "server.out.log").open("wb")
        srv_err = (run_dir / "server.err.log").open("wb")
        server_proc = subprocess.Popen(
            [str(PYTHON), "manage.py", "runserver", f"127.0.0.1:{port}", "--noreload", "--insecure", "--settings=audit10b_settings"],
            env=env,
            cwd=str(PMV),
            stdout=srv_out,
            stderr=srv_err,
        )

        # Wait for HTTP readiness and verify HMAC proof
        nonce = secrets.token_hex(32)
        key = (run_dir / ".django-key").read_text(encoding="utf-8").strip().encode()
        expected_hmac = hmac.new(key, nonce.encode(), hashlib.sha256).hexdigest()
        ready = False
        for _ in range(40):
            if server_proc.poll() is not None:
                srv_err.flush()
                err_txt = (run_dir / "server.err.log").read_text(encoding="utf-8", errors="replace")
                raise RuntimeError(f"Server exited prematurely: {err_txt}")
            req = urllib.request.Request(base_url + "/", headers={"X-Audit10B-Challenge": nonce})
            try:
                with urllib.request.urlopen(req, timeout=2) as resp:
                    if resp.headers.get("X-Audit10B-Proof") == expected_hmac:
                        ready = True
                        break
            except Exception:
                time.sleep(0.25)
        if not ready:
            raise RuntimeError("Isolated Stage 10-B server failed HMAC proof readiness check.")

        node_env = os.environ.copy()
        node_env.update(
            {
                "AUDIT10B_BASE_URL": base_url,
                "AUDIT10B_EVIDENCE_DIR": str(browser_dir),
                "AUDIT10B_META": json.dumps(meta),
                "AUDIT10B_ADMIN_EMAIL": creds["admin_email"],
                "AUDIT10B_WH_EMAIL": creds["wh_email"],
                "AUDIT10B_SELLER_EMAIL": creds["seller_email"],
                "AUDIT10B_SELLER2_EMAIL": creds["seller2_email"],
                "AUDIT10B_PASS": creds["password"],
                "AUDIT10B_NONCE": nonce,
                "AUDIT10B_EXPECTED_HMAC": expected_hmac,
            }
        )
        r_node = subprocess.run(
            ["node", str(HERE / "audit10b_browser.cjs")],
            env=node_env,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        (browser_dir / "browser-stdout.txt").write_text(r_node.stdout or "", encoding="utf-8")
        (browser_dir / "browser-stderr.txt").write_text(r_node.stderr or "", encoding="utf-8")
        db_after = file_sha256(OPERATIONAL_DB) if OPERATIONAL_DB.exists() else None
        print(f"NODE_EXIT={r_node.returncode} DB_UNTOUCHED={db_before == db_after}")
        if r_node.stdout:
            print(r_node.stdout)
        if r_node.stderr:
            print("STDERR:", r_node.stderr)
        return r_node.returncode if db_before == db_after else 2
    finally:
        if server_proc is not None and server_proc.poll() is None:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_proc.kill()
        for fh_name in ("srv_out", "srv_err"):
            fh = locals().get(fh_name)
            if fh is not None:
                try:
                    fh.close()
                except Exception:
                    pass
        shutil.rmtree(run_dir, ignore_errors=True)


def cmd_probe() -> int:
    EV_DIR.mkdir(parents=True, exist_ok=True)
    db_before = file_sha256(OPERATIONAL_DB) if OPERATIONAL_DB.exists() else None
    run_dir = create_isolated_run_dir()
    env = base_env(run_dir)
    try:
        r_mig = run_cmd([str(PYTHON), "manage.py", "migrate", "--noinput", "--settings=audit10b_settings"], env)
        if r_mig.returncode != 0:
            raise RuntimeError(f"Migrate failed: {r_mig.stderr}")
        probe_out = EV_DIR / "probe-10b.json"
        r_probe = run_cmd([str(PYTHON), str(HERE / "audit10b_probe.py"), str(probe_out)], env, cwd=ROOT)
        db_after = file_sha256(OPERATIONAL_DB) if OPERATIONAL_DB.exists() else None
        print(f"PROBE_EXIT={r_probe.returncode} DB_UNTOUCHED={db_before == db_after}")
        if db_before != db_after:
            return 2
        return r_probe.returncode
    finally:
        shutil.rmtree(run_dir, ignore_errors=True)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all-tests"
    if mode == "all-tests":
        raise SystemExit(cmd_all_tests())
    elif mode == "browser":
        raise SystemExit(cmd_browser())
    elif mode == "probe":
        raise SystemExit(cmd_probe())
    else:
        raise SystemExit(f"Unknown mode: {mode}")
