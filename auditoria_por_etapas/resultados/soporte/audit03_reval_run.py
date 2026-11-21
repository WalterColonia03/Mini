"""Stage 03 isolated revalidation runner against current build.

Creates fresh SQLite database + evidence folder, boots an isolated Django HTTP
server, invokes Chromium Playwright end-to-end checks across ADMIN, ALMACENERO,
VENDEDOR and anonymous/staff visitors, checks protected DB hashes before/after,
and exercises seed_pmv/seed_demo in a separate in-memory verification.
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
from uuid import uuid4

SUPPORT = Path(__file__).resolve().parent
RESULTS = SUPPORT.parent
ROOT = RESULTS.parent.parent
APP = ROOT / "r1-pmv"
sys.path[:0] = [str(APP), str(SUPPORT)]


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(65536):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def setup_django() -> None:
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit03_reval_settings"
    import django

    django.setup()


def seed_accounts() -> None:
    from identity.models import Account, Role

    run_dir = Path(os.environ["AUDIT03_REVAL_RUN_DIR"])
    roles = {}
    for code, name in [
        (Role.Code.ADMIN, "Administrador"),
        (Role.Code.WAREHOUSE, "Almacenero"),
        (Role.Code.SELLER, "Vendedor"),
    ]:
        roles[code], _ = Role.objects.get_or_create(code=code, defaults={"name": name})

    creds = {}
    specs = [
        ("admin", "admin1@reval03.invalid", Role.Code.ADMIN, "Admin Principal", True, False),
        ("admin2", "admin2@reval03.invalid", Role.Code.ADMIN, "Admin Segundo", True, False),
        ("warehouse", "almacen@reval03.invalid", Role.Code.WAREHOUSE, "Almacenero Uno", True, False),
        ("seller", "vendedor@reval03.invalid", Role.Code.SELLER, "Vendedor Uno", True, False),
        ("staff_noperm", "staff@reval03.invalid", Role.Code.ADMIN, "Staff Sin Permisos", True, True),
        ("inactive", "inactivo@reval03.invalid", Role.Code.ADMIN, "Admin Inactivo", False, False),
    ]
    for alias, email, role_code, display_name, is_active, is_staff in specs:
        pw = "Test03-" + secrets.token_urlsafe(12) + "A1"
        acc = Account.objects.create_user(
            email,
            pw,
            display_name=display_name,
            role=roles[role_code],
            is_active=is_active,
            is_staff=is_staff,
        )
        creds[alias] = {"id": str(acc.pk), "email": email, "password": pw, "role": role_code}

    # Cash register for VENDEDOR flow
    from cash.models import CashRegister
    from cash.services import open_cash_shift

    CashRegister.objects.create(code="CAJA-01", is_active=True)
    seller_acc = Account.objects.get(email="vendedor@reval03.invalid")
    open_cash_shift(actor=seller_acc, opening_amount=Decimal("100.00"))

    cred_path = run_dir / ".credentials.json"
    cred_path.write_text(json.dumps(creds, indent=2), encoding="utf-8")


def prepare_stock_and_history_cmd() -> dict:
    """Called via CLI mode after Chrome creates categories and initial products."""
    from django.utils import timezone as dj_tz
    from catalog.models import Category, Product
    from catalog.services import toggle_product_availability
    from identity.models import Account
    from inventory.models import InitialInventoryLoad, Lot, StockReceipt, StockWriteOff, PhysicalAdjustment
    from inventory.services import LotInput, confirm_initial_load, register_stock_entry
    from sales.services import add_product_to_draft, checkout_sale

    today = dj_tz.localdate()
    admin = Account.objects.get(email="admin1@reval03.invalid")
    warehouse = Account.objects.get(email="almacen@reval03.invalid")
    seller = Account.objects.get(email="vendedor@reval03.invalid")

    # 1. Leche base product for edit/deactivation/history tests
    lacteos = Category.objects.get(name_normalized="lácteos y derivados")
    abarrotes = Category.objects.create(name="Abarrotes", is_active=True)
    suspendida = Category.objects.create(name="Suspendida", is_active=False)

    leche = Product.objects.create(
        category=lacteos,
        name="Leche prueba",
        barcode="INT-LECHE-1",
        barcode_type=Product.BarcodeType.INTERNAL,
        sale_price=Decimal("10.00"),
        minimum_stock=10,
    )
    confirm_initial_load(
        actor=warehouse,
        product=leche,
        lots=[
            LotInput("L-A1", 10, Decimal("6.00"), today + timedelta(days=5)),
            LotInput("L-B1", 10, Decimal("6.50"), today + timedelta(days=20)),
        ],
    )
    draft1 = add_product_to_draft(actor=seller, product_id=leche.pk, quantity=2)
    sale1 = checkout_sale(
        actor=seller,
        draft_id=draft1.pk,
        cash_received=Decimal("25.00"),
        idempotency_key=uuid4(),
    )

    # 2. Additional stock scenarios for catalog alerts, expired vs valid, inactive cat, 0 stock
    # 2a. Valid stock = 5 + expired lot = 20 (seeded directly for yesterday/today) -> sellable=5 <= min=10
    atun = Product.objects.get(search_name="atún clásico 170 g")
    load_atun = confirm_initial_load(
        actor=warehouse,
        product=atun,
        lots=[LotInput("AT-VIG", 5, Decimal("4.00"), today + timedelta(days=15))],
    )
    Lot.objects.create(
        product=atun,
        initial_load=load_atun,
        responsible=warehouse,
        number="AT-VENC",
        initial_quantity=20,
        available_quantity=20,
        unit_cost=Decimal("4.00"),
        expiration_date=today - timedelta(days=1),
    )
    Lot.objects.create(
        product=atun,
        initial_load=load_atun,
        responsible=warehouse,
        number="AT-HOY",
        initial_quantity=3,
        available_quantity=3,
        unit_cost=Decimal("4.00"),
        expiration_date=today,
    )

    # 2b. Yogur stays with 0 stock (not sellable), active -> Sin stock vigente
    yogur = Product.objects.get(search_name="yogur natural 200 g")
    # Also create exact threshold boundary items: stock=11 min=10 (no alert), stock=0 min=0
    sobre = Product.objects.create(
        category=abarrotes,
        name="Sobre normal",
        barcode="INT-SOBRE",
        barcode_type=Product.BarcodeType.INTERNAL,
        sale_price=Decimal("3.00"),
        minimum_stock=10,
    )
    confirm_initial_load(
        actor=warehouse,
        product=sobre,
        lots=[LotInput("SB-1", 11, Decimal("1.50"), today + timedelta(days=30))],
    )

    inact_prod = Product.objects.create(
        category=abarrotes,
        name="Producto suspendido",
        barcode="INT-INACT",
        barcode_type=Product.BarcodeType.INTERNAL,
        sale_price=Decimal("4.00"),
        minimum_stock=10,
        is_active=True,
    )
    confirm_initial_load(
        actor=warehouse,
        product=inact_prod,
        lots=[LotInput("IN-1", 5, Decimal("2.00"), today + timedelta(days=25))],
    )
    toggle_product_availability(actor=admin, product=inact_prod, is_active=False)

    cat_off_prod = Product.objects.create(
        category=suspendida,
        name="Producto categoría suspendida",
        barcode="INT-CATOFF",
        barcode_type=Product.BarcodeType.INTERNAL,
        sale_price=Decimal("7.00"),
        minimum_stock=10,
        is_active=True,
    )
    confirm_initial_load(
        actor=warehouse,
        product=cat_off_prod,
        lots=[LotInput("CO-1", 6, Decimal("3.50"), today + timedelta(days=25))],
    ) if False else None
    # Note: confirm_initial_load blocks inactive category! Seed load while active or direct Lot for state fixture:
    load_co = InitialInventoryLoad.objects.create(
        product=cat_off_prod,
        responsible=warehouse,
        product_snapshot_name=cat_off_prod.name,
        product_snapshot_barcode=cat_off_prod.barcode,
        unit_snapshot="UND",
        responsible_snapshot_name=warehouse.display_name,
        average_cost_snapshot=Decimal("3.5000"),
    )
    Lot.objects.create(
        product=cat_off_prod,
        initial_load=load_co,
        responsible=warehouse,
        number="CO-1",
        initial_quantity=6,
        available_quantity=6,
        unit_cost=Decimal("3.50"),
        expiration_date=today + timedelta(days=25),
    )

    # Also test orphan SaleLine relink edge case in a separate probe product
    orphan_prod = Product.objects.create(
        category=abarrotes,
        name="Huerfano código",
        barcode="ORPHAN-OLD",
        barcode_type=Product.BarcodeType.INTERNAL,
        sale_price=Decimal("5.00"),
        minimum_stock=10,
    )
    from sales.models import SaleLine

    SaleLine.objects.create(
        sale=sale1,
        position=99,
        product=None,
        product_snapshot_name="Registro antiguo sin FK",
        product_snapshot_barcode="ORPHAN-OLD",
        quantity=1,
        unit_price=Decimal("5.00"),
        unit_cost=Decimal("2.0000"),
        amount=Decimal("5.00"),
    )

    # Put Leche prueba into seller's active draft (qty=1) for CP-HU-PROD-04-002 / deactivation checks
    draft2 = add_product_to_draft(actor=seller, product_id=leche.pk, quantity=1)

    return {
        "leche_id": str(leche.pk),
        "atun_id": str(atun.pk),
        "yogur_id": str(yogur.pk),
        "sobre_id": str(sobre.pk),
        "inact_prod_id": str(inact_prod.pk),
        "cat_off_prod_id": str(cat_off_prod.pk),
        "orphan_prod_id": str(orphan_prod.pk),
        "lacteos_id": str(lacteos.pk),
        "abarrotes_id": str(abarrotes.pk),
        "suspendida_id": str(suspendida.pk),
        "sale1_id": str(sale1.pk),
        "sale1_correlative": sale1.correlative,
        "draft2_id": str(draft2.pk),
    }


def snapshot_db() -> dict:
    from catalog.models import Category, Product, ProductBarcodeKey
    from inventory.models import InitialInventoryLoad, Lot, StockReceipt, StockWriteOff, PhysicalAdjustment
    from sales.models import Sale, SaleDraft, SaleDraftLine, SaleLine, SaleLotAllocation

    return {
        "categories": list(Category.objects.order_by("pk").values()),
        "products": list(Product.objects.order_by("pk").values()),
        "barcode_keys": list(ProductBarcodeKey.objects.order_by("reading_key").values()),
        "loads": list(InitialInventoryLoad.objects.order_by("pk").values()),
        "lots": list(Lot.objects.order_by("pk").values()),
        "receipts": list(StockReceipt.objects.order_by("pk").values()),
        "writeoffs": list(StockWriteOff.objects.order_by("pk").values()),
        "adjustments": list(PhysicalAdjustment.objects.order_by("pk").values()),
        "sales": list(Sale.objects.order_by("pk").values()),
        "sale_lines": list(SaleLine.objects.order_by("pk").values()),
        "allocations": list(SaleLotAllocation.objects.order_by("pk").values()),
        "drafts": list(SaleDraft.objects.order_by("pk").values()),
        "draft_lines": list(SaleDraftLine.objects.order_by("pk").values()),
    }


def check_cross_module_probes(leche_id: str, suspendida_id: str) -> dict:
    """Verify service-level inventory/sales/category deactivation & edge behaviors."""
    from django.core.exceptions import ValidationError
    from django.utils import timezone as dj_tz
    from catalog.barcodes import normalize_literal
    from catalog.forms import CategoryForm, ProductRegistrationForm
    from catalog.models import Category, Product
    from catalog.services import (
        create_category,
        register_canned_product,
        toggle_product_availability,
        update_product,
    )
    from identity.models import Account
    from inventory.models import Lot, StockWriteOff
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        register_physical_adjustment,
        register_stock_entry,
        write_off_stock,
    )
    from sales.models import SaleLine
    from sales.services import remove_draft_line, update_draft_line

    results = {}
    admin = Account.objects.get(email="admin1@reval03.invalid")
    warehouse = Account.objects.get(email="almacen@reval03.invalid")
    seller = Account.objects.get(email="vendedor@reval03.invalid")
    leche = Product.objects.get(pk=leche_id)
    suspendida = Category.objects.get(pk=suspendida_id)

    # 1. CategoryForm & create_category punctuation/whitespace check ("!!!")
    punctuation_ok = False
    try:
        cat_punct = create_category(actor=admin, name="!!!")
        punctuation_ok = True
        cat_punct.delete()
    except ValidationError as exc:
        results["category_punctuation_rejected"] = exc.message_dict
    results["category_punctuation_accepted"] = punctuation_ok

    # 2. CategoryForm whitespace & length checks
    results["form_ws_only_valid"] = CategoryForm(data={"name": " \t\u00a0 "}).is_valid()

    # 3. BARCODE_PATTERN allows internal whitespace (\t, \n, \xa0) before normalization?
    form_tab = ProductRegistrationForm(
        data={
            "name": "Probe tab",
            "barcode_type": "INTERNAL",
            "barcode": "AB\t12\xa0X",
            "category": str(leche.category_id),
            "unit": "UND",
            "sale_price": "5.00",
            "minimum_stock": "10",
        }
    )
    results["barcode_tab_form_valid"] = form_tab.is_valid()
    results["barcode_tab_cleaned"] = form_tab.cleaned_data.get("barcode") if form_tab.is_valid() else form_tab.errors

    # 4. Comma decimal in ProductRegistrationForm ("2,50") under es-PE
    form_comma = ProductRegistrationForm(
        data={
            "name": "Probe comma",
            "barcode_type": "INTERNAL",
            "barcode": "PRB-COMMA",
            "category": str(leche.category_id),
            "unit": "UND",
            "sale_price": "2,50",
            "minimum_stock": "10",
        }
    )
    results["price_comma_form_valid"] = form_comma.is_valid()
    results["price_comma_errors"] = dict(form_comma.errors) if not form_comma.is_valid() else str(form_comma.cleaned_data["sale_price"])

    # 5. Inventory operations on inactive product & inactive category
    # Temporarily create an inactive product with load + stock, test entry/writeoff/adjustment
    p_tmp = register_canned_product(
        actor=admin,
        name="Temp Cleanup Probe",
        barcode="TMP-CLN-1",
        category=leche.category,
        unit="UND",
        sale_price=Decimal("4.00"),
        minimum_stock=5,
        barcode_type="INTERNAL",
    )
    load_tmp = confirm_initial_load(
        actor=warehouse,
        product=p_tmp,
        lots=[LotInput("TMP-1", 5, Decimal("2.00"), dj_tz.localdate() + timedelta(days=30))],
    )
    lot_tmp = Lot.objects.get(initial_load=load_tmp)
    toggle_product_availability(actor=admin, product=p_tmp, is_active=False)

    entry_blocked = False
    try:
        register_stock_entry(
            actor=warehouse,
            product=p_tmp,
            lots=[LotInput("TMP-2", 2, Decimal("2.00"), dj_tz.localdate() + timedelta(days=40))],
        )
    except ValidationError as exc:
        entry_blocked = exc.messages[0]
    results["entry_on_inactive_product_blocked"] = entry_blocked

    wo = write_off_stock(
        actor=warehouse,
        lot=lot_tmp,
        quantity=1,
        reason=StockWriteOff.Reason.DAMAGE,
        notes="Prueba baja sobre producto inactivo",
    )
    adj = register_physical_adjustment(
        actor=admin,
        lot=lot_tmp,
        delta=-1,
        reason="Prueba ajuste sobre producto inactivo",
    )
    results["writeoff_on_inactive_allowed"] = str(wo.correlativo)
    results["adjustment_on_inactive_allowed"] = str(adj.pk)

    # 6. Check orphan SaleLine relinking on update_product
    orphan = Product.objects.get(barcode="ORPHAN-OLD")
    before_linked = SaleLine.objects.filter(product=orphan).count()
    update_product(
        actor=admin,
        product=orphan,
        name=orphan.name,
        barcode="ORPHAN-NEW",
        barcode_type=Product.BarcodeType.INTERNAL,
        category=orphan.category,
        sale_price=orphan.sale_price,
        minimum_stock=orphan.minimum_stock,
    )
    after_linked = SaleLine.objects.filter(product=orphan).count()
    results["orphan_saleline_relinked_count_before"] = before_linked
    results["orphan_saleline_relinked_count_after"] = after_linked

    # 7. Check editing product that ALREADY resides in inactive category (keeping inactive cat vs moving out)
    cat_off_prod = Product.objects.get(barcode="INT-CATOFF")
    keep_inactive_ok = False
    try:
        update_product(
            actor=admin,
            product=cat_off_prod,
            name="Producto categoría suspendida editado",
            barcode=cat_off_prod.barcode,
            barcode_type=cat_off_prod.barcode_type,
            category=suspendida,
            sale_price=Decimal("7.50"),
            minimum_stock=8,
        )
        keep_inactive_ok = True
    except ValidationError as exc:
        keep_inactive_ok = f"REJECTED: {exc.message_dict}"
    results["edit_product_already_in_inactive_category_keep"] = keep_inactive_ok

    switch_to_inactive_blocked = False
    try:
        update_product(
            actor=admin,
            product=orphan,
            name=orphan.name,
            barcode=orphan.barcode,
            barcode_type=orphan.barcode_type,
            category=suspendida,
            sale_price=orphan.sale_price,
            minimum_stock=orphan.minimum_stock,
        )
    except ValidationError as exc:
        switch_to_inactive_blocked = exc.message_dict
    results["switch_active_product_to_inactive_category_blocked"] = switch_to_inactive_blocked

    return results


def verify_seed_commands_in_temp() -> dict:
    """Run seed_pmv and seed_demo in a temporary sqlite test DB without touching operative files."""
    from django.core.management import call_command
    from django.db import connections
    import tempfile

    env_keys = ("SEED_ADMIN_PASSWORD", "SEED_SELLER_PASSWORD", "SEED_WAREHOUSE_PASSWORD")
    prev_env = {k: os.environ.get(k) for k in env_keys}
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_db = Path(tmpdir) / "seedprobe.sqlite3"
        old = dict(connections.databases["default"])
        connections.close_all()
        connections.databases["default"]["NAME"] = str(tmp_db)
        try:
            for k in env_keys:
                os.environ[k] = secrets.token_urlsafe(12)
            call_command("migrate", interactive=False, verbosity=0)
            out1, out2 = io.StringIO(), io.StringIO()
            call_command("seed_pmv", stdout=out1)
            call_command("seed_demo", stdout=out2)
            # Run again to verify idempotency
            out3 = io.StringIO()
            call_command("seed_demo", stdout=out3)
            from catalog.models import Category, Product

            cats = list(Category.objects.values_list("name", "is_active"))
            prods = list(Product.objects.order_by("name").values_list("name", "barcode", "barcode_type", "unit"))
        finally:
            connections.close_all()
            connections.databases["default"] = old
            for k, val in prev_env.items():
                if val is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = val
        return {
            "seed_pmv_out": out1.getvalue().strip(),
            "seed_demo_first": out2.getvalue().strip(),
            "seed_demo_second": out3.getvalue().strip(),
            "categories": cats,
            "products": prods,
        }


def run_all() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + secrets.token_hex(3)
    run_dir = (RESULTS / "datos" / f"03-REVAL-{stamp}").resolve()
    out_dir = (RESULTS / "evidencias" / f"03-REVAL-{stamp}").resolve()
    run_dir.mkdir(parents=True, exist_ok=False)
    out_dir.mkdir(parents=True, exist_ok=False)

    protected = [
        *(ROOT / "r1-pmv").glob("*.sqlite3"),
        *(RESULTS / "datos").rglob("*.sqlite3"),
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]
    hashes_before = {str(p.relative_to(ROOT)): digest(p) for p in protected if p.exists()}

    write_json(run_dir / "marker.json", {"run": run_dir.name, "created_utc": stamp})
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")

    os.environ["AUDIT03_REVAL_RUN_DIR"] = str(run_dir)
    os.environ["AUDIT03_REVAL_OUT_DIR"] = str(out_dir)

    setup_django()
    from django.core.management import call_command

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)
    seed_accounts()

    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    env = dict(os.environ)
    env["AUDIT03_REVAL_PORT"] = str(port)
    env["AUDIT03_REVAL_PYTHON"] = sys.executable

    server_log_path = out_dir / "server-stdout.txt"
    server_log_fh = server_log_path.open("w", encoding="utf-8", errors="replace")
    server_proc = subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "serve"],
        env=env,
        cwd=str(APP),
        stdout=server_log_fh,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    try:
        # Wait for HTTP listening (allow up to 45s on Windows cold subprocess import)
        deadline = time.time() + 45
        ready = False
        while time.time() < deadline:
            if server_proc.poll() is not None:
                server_log_fh.flush()
                raise RuntimeError("Django server exited prematurely: " + server_log_path.read_text(encoding="utf-8", errors="replace"))
            with socket.socket() as probe:
                if probe.connect_ex(("127.0.0.1", port)) == 0:
                    ready = True
                    break
            time.sleep(0.25)
        if not ready:
            raise RuntimeError("Timeout waiting for Django isolated server")

        browser_script = SUPPORT / "audit03_reval_browser.cjs"
        browser_res = subprocess.run(
            ["node", str(browser_script)],
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=240,
        )
        (out_dir / "browser-stdout.txt").write_text(browser_res.stdout + "\n---STDERR---\n" + browser_res.stderr, encoding="utf-8")
        if browser_res.returncode != 0:
            raise RuntimeError(f"Browser script failed ({browser_res.returncode}):\n{browser_res.stdout}\n{browser_res.stderr}")
    finally:
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server_proc.kill()
            server_proc.wait()
        server_log_fh.close()

    hashes_after = {str(p.relative_to(ROOT)): digest(p) for p in protected if p.exists()}
    unchanged = all(hashes_before.get(k) == v for k, v in hashes_after.items())
    seed_probe = verify_seed_commands_in_temp()
    summary = {
        "run_dir": str(run_dir.relative_to(ROOT)),
        "out_dir": str(out_dir.relative_to(ROOT)),
        "port": port,
        "protected_unchanged": unchanged,
        "protected_hashes_after": hashes_after,
        "seed_probe": seed_probe,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
    }
    write_json(out_dir / "summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if not unchanged:
        raise SystemExit(1)


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "run"
    if mode == "run":
        run_all()
        return

    setup_django()
    if mode == "serve":
        from django.core.management import execute_from_command_line

        execute_from_command_line(
            ["manage.py", "runserver", "127.0.0.1:" + os.environ["AUDIT03_REVAL_PORT"], "--noreload", "--insecure"]
        )
    elif mode == "snapshot":
        print(json.dumps(snapshot_db(), ensure_ascii=False, default=str))
    elif mode == "prepare-stock":
        print(json.dumps(prepare_stock_and_history_cmd(), ensure_ascii=False, default=str))
    elif mode == "probes":
        print(json.dumps(check_cross_module_probes(sys.argv[2], sys.argv[3]), ensure_ascii=False, default=str))
    else:
        raise SystemExit(f"Unknown mode: {mode}")


if __name__ == "__main__":
    main()
