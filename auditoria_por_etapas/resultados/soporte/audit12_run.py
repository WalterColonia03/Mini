"""Isolated Stage 12 runner (Django checks/tests, fixtures, snapshot, runserver, Chrome browser).
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
        os.environ["AUDIT12_DEFAULT_COOKIES"] = "1"
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit12_settings"
    import django

    django.setup()


def prepare_empty_migrated_db() -> None:
    from django.core.management import call_command

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)


def prepare_stage12_fixtures(run_dir: Path, out_dir: Path) -> dict:
    import uuid
    from decimal import ROUND_HALF_UP
    from zoneinfo import ZoneInfo

    from django.utils import timezone as tz

    def load_historical_discount(sale, discount: str) -> None:
        original_total = sale.total_amount
        sale.discount_amount = Decimal(discount)
        sale.total_amount = original_total - sale.discount_amount
        sale.base_amount = (sale.total_amount / Decimal("1.18")).quantize(Decimal("0.01"), ROUND_HALF_UP)
        sale.igv_amount = sale.total_amount - sale.base_amount
        sale.change_given = sale.cash_received - sale.total_amount
        sale.save(update_fields=("discount_amount", "total_amount", "base_amount", "igv_amount", "change_given"))

    from cash.models import CashRegister, CashShift, CashShiftClose
    from cash.services import close_cash_shift
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.services import LotInput, confirm_initial_load
    from sales.models import Sale, SaleCounter, SaleLine
    from sales.services import add_product_to_draft, checkout_sale

    admin_role, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    wh_role, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    seller_role, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

    creds = {}
    accounts = {}
    long_seller1_name = "CarmenElenaVendedoraDeMostradorConNombreExtensoParaProbarEnvoltura12"
    for key, email, display, role, is_active in [
        ("admin", "admin@audit12.invalid", "Admin Audit12", admin_role, True),
        ("warehouse", "warehouse@audit12.invalid", "Lucia Almacen12", wh_role, True),
        ("seller1", "seller1@audit12.invalid", long_seller1_name, seller_role, True),
        ("seller2", "seller2@audit12.invalid", "Mario Segundo Vendedor12", seller_role, True),
    ]:
        pw = secrets.token_urlsafe(18) + "A1!"
        creds[key] = {"email": email, "password": pw}
        accounts[key] = Account.objects.create_user(
            email, pw, display_name=display, role=role, is_active=is_active
        )

    (run_dir / ".credentials.json").write_text(json.dumps(creds), encoding="utf-8")

    cat_active = Category.objects.create(name="Abarrotes Stage 12", is_active=True)
    today = tz.localdate()
    d_plus30 = today + timedelta(days=30)
    d_yesterday = today - timedelta(days=1)

    p_tax = Product.objects.create(
        category=cat_active,
        name="Leche Evaporada Stage12 400g",
        barcode="775120000001",
        sale_price=Decimal("3.55"),
        minimum_stock=2,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_tax,
        lots=[LotInput("L12-TAX", 30, Decimal("1.7500"), d_plus30)],
    )

    p_std = Product.objects.create(
        category=cat_active,
        name="Arroz Superior Stage12 1kg",
        barcode="775120000002",
        sale_price=Decimal("10.00"),
        minimum_stock=2,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_std,
        lots=[LotInput("L12-STD", 25, Decimal("4.2500"), d_plus30)],
    )

    long_name = ("ProductoUltraExtensoSinEspaciosParaConstanciaHistorialEImpresion12" * 3)[:140]
    p_long = Product.objects.create(
        category=cat_active,
        name=long_name,
        barcode="775120000003" + "9" * 52,  # 64 chars max barcode
        sale_price=Decimal("12.00"),
        minimum_stock=1,
    )
    confirm_initial_load(
        actor=accounts["warehouse"],
        product=p_long,
        lots=[LotInput("L12-LONG", 15, Decimal("6.1250"), d_plus30)],
    )

    reg = CashRegister.objects.create(code="CAJA-01")
    SaleCounter.objects.get_or_create(id=1, defaults={"next_value": 1})

    # 1. Seller1 yesterday CLOSED shift with 1 sale (S1, shortage at close -5.00)
    t_yday_open = tz.now() - timedelta(days=1, hours=4)
    t_yday_sale = tz.now() - timedelta(days=1, hours=3)
    t_yday_close = tz.now() - timedelta(days=1, hours=1)
    shift1_closed = CashShift.objects.create(
        cash_register=reg, seller=accounts["seller1"], opening_amount=Decimal("100.00")
    )
    CashShift.objects.filter(pk=shift1_closed.pk).update(opened_at=t_yday_open)
    shift1_closed.refresh_from_db()

    d1 = add_product_to_draft(actor=accounts["seller1"], product_id=p_std.pk, quantity=2)  # 20.00
    s1_old = checkout_sale(
        actor=accounts["seller1"],
        draft_id=d1.pk,
        cash_received=Decimal("20.00"),
        idempotency_key=d1.pk,
    )
    Sale.objects.filter(pk=s1_old.pk).update(confirmed_at=t_yday_sale)
    s1_old.refresh_from_db()
    # Close with shortage (-5.00): expected 120.00, counted 115.00
    c1 = close_cash_shift(actor=accounts["seller1"], counted_amount=Decimal("115.00"))
    CashShiftClose.objects.filter(pk=c1.pk).update(closed_at=t_yday_close)
    c1.refresh_from_db()

    # 2. Seller2 today CLOSED shift with 1 sale (S2_V2, exact close)
    t_s2_open = tz.now() - timedelta(hours=3)
    t_s2_sale = tz.now() - timedelta(hours=2)
    t_s2_close = tz.now() - timedelta(hours=1)
    shift2_v2 = CashShift.objects.create(
        cash_register=reg, seller=accounts["seller2"], opening_amount=Decimal("50.00")
    )
    CashShift.objects.filter(pk=shift2_v2.pk).update(opened_at=t_s2_open)
    shift2_v2.refresh_from_db()

    d2 = add_product_to_draft(actor=accounts["seller2"], product_id=p_tax.pk, quantity=2)  # 7.10
    s2_v2 = checkout_sale(
        actor=accounts["seller2"],
        draft_id=d2.pk,
        cash_received=Decimal("10.00"),
        idempotency_key=d2.pk,
    )
    load_historical_discount(s2_v2, "0.10")  # net = 7.00
    Sale.objects.filter(pk=s2_v2.pk).update(confirmed_at=t_s2_sale)
    s2_v2.refresh_from_db()
    c2 = close_cash_shift(actor=accounts["seller2"], counted_amount=Decimal("57.00"))
    CashShiftClose.objects.filter(pk=c2.pk).update(closed_at=t_s2_close)
    c2.refresh_from_db()

    # 3. Seller1 today OPEN shift with 1 multi-item discounted sale (S3_OPEN)
    shift3_open = CashShift.objects.create(
        cash_register=reg, seller=accounts["seller1"], opening_amount=Decimal("80.00")
    )
    d3 = add_product_to_draft(actor=accounts["seller1"], product_id=p_long.pk, quantity=1)  # 12.00
    d3 = add_product_to_draft(actor=accounts["seller1"], product_id=p_tax.pk, quantity=2)   # + 7.10 = 19.10
    s3_open = checkout_sale(
        actor=accounts["seller1"],
        draft_id=d3.pk,
        cash_received=Decimal("25.00"),
        idempotency_key=d3.pk,
    )
    load_historical_discount(s3_open, "1.50")  # subtotal 19.10 - 1.50 = 17.60
    s3_open.refresh_from_db()
    # Prepare ONE more active draft for Seller1 so browser can immediately inspect /ventas/ and checkout retry!
    d4_active = add_product_to_draft(actor=accounts["seller1"], product_id=p_std.pk, quantity=1)  # 10.00

    # Mutate p_long & p_std catalog prices/names AFTER S1..S3 to verify snapshot immutability on existing receipts!
    # Keep p_std price at 10.00 for d4_active, mutate p_long name & price to test S3 snapshot!
    p_long.name = "CATALOGO RENOMBRADO POST VENTA"
    p_long.sale_price = Decimal("99.00")
    p_long.save(update_fields=["name", "sale_price"])

    # 4. Tied-timestamp 26 closed shifts & 26 confirmed sales pinned to 2026-11-10 for deterministic pagination
    lima = ZoneInfo("America/Lima")
    t_pag = datetime(2026, 11, 10, 12, 0, 0, tzinfo=lima)
    pag_shift_pks = []
    pag_shifts = []
    for idx in range(26):
        owner = accounts["seller1"] if idx % 2 == 0 else accounts["seller2"]
        sh = CashShift.objects.create(
            cash_register=reg,
            seller=owner,
            opening_amount=Decimal("10.00"),
            status=CashShift.Status.CLOSED,
        )
        CashShiftClose.objects.create(
            cash_shift=sh,
            closed_by=owner,
            counted_amount=Decimal("20.00"),
            expected_amount=Decimal("20.00"),
            difference=Decimal("0.00"),
        )
        pag_shifts.append(sh)
        pag_shift_pks.append(sh.pk)
    CashShift.objects.filter(pk__in=pag_shift_pks).update(opened_at=t_pag)
    CashShiftClose.objects.filter(cash_shift_id__in=pag_shift_pks).update(closed_at=t_pag)
    pagination_shifts_order = [str(pk) for pk in sorted(pag_shift_pks, reverse=True)]

    pag_sale_pks = []
    for idx in range(26):
        sh = pag_shifts[idx]
        s_pag = Sale.objects.create(
            cash_shift=sh,
            seller=sh.seller,
            seller_snapshot_name=sh.seller.display_name,
            cash_register_snapshot_code=reg.code,
            correlative=f"V-000100{idx + 1:02d}",
            idempotency_key=uuid.uuid4(),
            total_amount=Decimal("10.00"),
            base_amount=Decimal("8.47"),
            igv_amount=Decimal("1.53"),
            discount_amount=Decimal("0.00"),
            cash_received=Decimal("10.00"),
            change_given=Decimal("0.00"),
        )
        SaleLine.objects.create(
            sale=s_pag,
            position=1,
            product=p_std,
            product_snapshot_name=p_std.name,
            product_snapshot_barcode=p_std.barcode,
            quantity=1,
            unit_price=Decimal("10.00"),
            amount=Decimal("10.00"),
            unit_cost=Decimal("4.2500"),
        )
        pag_sale_pks.append(s_pag.pk)
    Sale.objects.filter(pk__in=pag_sale_pks).update(confirmed_at=t_pag)
    pagination_sales_correlatives = list(
        Sale.objects.filter(pk__in=pag_sale_pks)
        .order_by("-confirmed_at", "-correlative", "-id")
        .values_list("correlative", flat=True)
    )

    # 5. Reversed-UUID 3-line sale + legacy position=None sale pinned to 2026-11-09
    t_legacy = datetime(2026, 11, 9, 15, 0, 0, tzinfo=lima)
    shift_09 = CashShift.objects.create(
        cash_register=reg,
        seller=accounts["seller1"],
        opening_amount=Decimal("10.00"),
        status=CashShift.Status.CLOSED,
    )
    CashShiftClose.objects.create(
        cash_shift=shift_09,
        closed_by=accounts["seller1"],
        counted_amount=Decimal("49.10"),
        expected_amount=Decimal("49.10"),
        difference=Decimal("0.00"),
    )
    CashShift.objects.filter(pk=shift_09.pk).update(opened_at=t_legacy)
    CashShiftClose.objects.filter(cash_shift=shift_09).update(closed_at=t_legacy)

    s_rev_lines = Sale.objects.create(
        cash_shift=shift_09,
        seller=accounts["seller1"],
        seller_snapshot_name=accounts["seller1"].display_name,
        cash_register_snapshot_code=reg.code,
        correlative="V-00009901",
        idempotency_key=uuid.uuid4(),
        total_amount=Decimal("25.55"),
        base_amount=Decimal("21.65"),
        igv_amount=Decimal("3.90"),
        discount_amount=Decimal("0.00"),
        cash_received=Decimal("30.00"),
        change_given=Decimal("4.45"),
    )
    Sale.objects.filter(pk=s_rev_lines.pk).update(confirmed_at=t_legacy)
    SaleLine.objects.create(
        id=uuid.UUID("ffffffff-0000-0000-0000-000000000001"),
        sale=s_rev_lines,
        position=1,
        product=p_std,
        product_snapshot_name="LINEA_ORDEN_1_UUID_FFFF",
        product_snapshot_barcode=p_std.barcode,
        quantity=1,
        unit_price=Decimal("10.00"),
        amount=Decimal("10.00"),
        unit_cost=Decimal("4.2500"),
    )
    SaleLine.objects.create(
        id=uuid.UUID("88888888-0000-0000-0000-000000000002"),
        sale=s_rev_lines,
        position=2,
        product=p_tax,
        product_snapshot_name="LINEA_ORDEN_2_UUID_8888",
        product_snapshot_barcode=p_tax.barcode,
        quantity=1,
        unit_price=Decimal("3.55"),
        amount=Decimal("3.55"),
        unit_cost=Decimal("1.7500"),
    )
    SaleLine.objects.create(
        id=uuid.UUID("11111111-0000-0000-0000-000000000003"),
        sale=s_rev_lines,
        position=3,
        product=p_long,
        product_snapshot_name="LINEA_ORDEN_3_UUID_1111",
        product_snapshot_barcode=p_long.barcode,
        quantity=1,
        unit_price=Decimal("12.00"),
        amount=Decimal("12.00"),
        unit_cost=Decimal("6.1250"),
    )

    s_legacy_lines = Sale.objects.create(
        cash_shift=shift_09,
        seller=accounts["seller1"],
        seller_snapshot_name=accounts["seller1"].display_name,
        cash_register_snapshot_code=reg.code,
        correlative="V-00009902",
        idempotency_key=uuid.uuid4(),
        total_amount=Decimal("13.55"),
        base_amount=Decimal("11.48"),
        igv_amount=Decimal("2.07"),
        discount_amount=Decimal("0.00"),
        cash_received=Decimal("15.00"),
        change_given=Decimal("1.45"),
    )
    Sale.objects.filter(pk=s_legacy_lines.pk).update(confirmed_at=t_legacy)
    SaleLine.objects.create(
        id=uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001"),
        sale=s_legacy_lines,
        position=None,
        product=p_tax,
        product_snapshot_name="LEGACY_ALPHA",
        product_snapshot_barcode=p_tax.barcode,
        quantity=1,
        unit_price=Decimal("3.55"),
        amount=Decimal("3.55"),
    )
    SaleLine.objects.create(
        id=uuid.UUID("bbbbbbbb-0000-0000-0000-000000000002"),
        sale=s_legacy_lines,
        position=None,
        product=p_std,
        product_snapshot_name="LEGACY_BETA",
        product_snapshot_barcode=p_std.barcode,
        quantity=1,
        unit_price=Decimal("10.00"),
        amount=Decimal("10.00"),
    )

    fixture = {
        "dates": {
            "yesterday": d_yesterday.isoformat(),
            "today": today.isoformat(),
            "plus30": d_plus30.isoformat(),
            "pagination_date": "2026-11-10",
        },
        "shifts": {
            "seller1_closed": {"id": str(shift1_closed.pk), "expected": "120.00", "counted": "115.00", "sales_total": "20.00"},
            "seller2_closed": {"id": str(shift2_v2.pk), "expected": "57.00", "counted": "57.00", "sales_total": "7.00"},
            "seller1_open": {"id": str(shift3_open.pk), "opening": "80.00"},
        },
        "sales": {
            "s1_old": {"id": str(s1_old.pk), "correlative": s1_old.correlative, "total": str(s1_old.total_amount)},
            "s2_v2": {"id": str(s2_v2.pk), "correlative": s2_v2.correlative, "total": str(s2_v2.total_amount)},
            "s3_open": {
                "id": str(s3_open.pk),
                "correlative": s3_open.correlative,
                "subtotal": "19.10",
                "discount": "1.50",
                "total": str(s3_open.total_amount),
                "base": str(s3_open.base_amount),
                "igv": str(s3_open.igv_amount),
                "cash_received": str(s3_open.cash_received),
                "change_given": str(s3_open.change_given),
            },
            "s_rev_lines": {"id": str(s_rev_lines.pk), "correlative": s_rev_lines.correlative},
            "s_legacy_lines": {"id": str(s_legacy_lines.pk), "correlative": s_legacy_lines.correlative},
        },
        "accounts": {k: {"id": str(v.pk), "email": v.email, "display_name": v.display_name} for k, v in accounts.items()},
        "products": {
            "tax": {"id": str(p_tax.pk), "name": p_tax.name, "barcode": p_tax.barcode, "price": "3.55"},
            "std": {"id": str(p_std.pk), "name": p_std.name, "barcode": p_std.barcode, "price": "10.00"},
            "long": {"id": str(p_long.pk), "name": p_long.name, "barcode": p_long.barcode, "orig_price": "12.00", "mutated_price": "99.00"},
        },
        "active_draft": {"id": str(d4_active.pk)},
    }
    write(out_dir / "fixture.json", fixture)
    write(
        out_dir / "fixture-ids.json",
        {
            "shifts": {
                "s1_closed": str(shift1_closed.pk),
                "s2_closed": str(shift2_v2.pk),
                "s3_open": str(shift3_open.pk),
            },
            "sales": {
                "s1": str(s1_old.pk),
                "s2": str(s2_v2.pk),
                "s3": str(s3_open.pk),
                "s_rev_lines": str(s_rev_lines.pk),
                "s_legacy_lines": str(s_legacy_lines.pk),
            },
            "products": {
                "std": str(p_std.pk),
            },
            "pagination_date": "2026-11-10",
            "pagination_shifts_order": pagination_shifts_order,
            "pagination_sales_correlatives": pagination_sales_correlatives,
            "accounts": {k: str(v.pk) for k, v in accounts.items()},
        },
    )
    return fixture


def snapshot() -> dict:
    from cash.models import CashShift, CashShiftClose
    from catalog.models import Product
    from inventory.models import Lot
    from sales.models import Sale, SaleCounter, SaleDraft, SaleDraftLine, SaleLine

    return {
        "counter": list(SaleCounter.objects.values("id", "next_value")),
        "shifts": list(CashShift.objects.order_by("opened_at", "id").values("id", "status", "opening_amount", "seller_id")),
        "closes": list(CashShiftClose.objects.order_by("closed_at", "id").values("cash_shift_id", "expected_amount", "counted_amount", "difference")),
        "drafts": list(SaleDraft.objects.order_by("created_at", "id").values("id", "status", "seller_id", "cash_shift_id", "discarded_at")),
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
    run_dir = RESULTS / "datos" / f"etapa12-{tag}-{stamp}"
    out_dir = RESULTS / "evidencias" / f"12-{tag}-{stamp}"
    run_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    write(run_dir / "marker.json", {"run": run_dir.name, "created_utc": stamp})
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")
    return run_dir, out_dir, stamp


def protected_hashes() -> dict[str, str | None]:
    protected = [
        *APP.glob("*.sqlite3"),
        *(
            p
            for p in (RESULTS / "datos").rglob("*.sqlite3")
            if p.parent.name.startswith(("etapa00", "etapa01", "etapa02", "etapa03", "etapa04", "etapa05", "etapa06", "etapa07"))
            and "20261114" not in p.parent.name
            and "reval" not in p.parent.name
            and "07b" not in p.parent.name
        ),
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]
    return {str(p.relative_to(ROOT)): digest(p) if p.exists() else None for p in protected}


def run_checks() -> int:
    start_hashes = protected_hashes()
    run_dir, out_dir, stamp = make_run_dir("checks")
    os.environ.update(AUDIT12_RUN_DIR=str(run_dir), AUDIT12_OUT=str(out_dir), AUDIT12_DEFAULT_COOKIES="1")
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
        AUDIT12_RUN_DIR=str(run_dir),
        AUDIT12_OUT=str(out_dir),
        AUDIT12_DEFAULT_COOKIES="1",
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
        AUDIT12_RUN_DIR=str(run_dir),
        AUDIT12_OUT=str(out_dir),
        AUDIT12_PYTHON=sys.executable,
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
        prepare_stage12_fixtures(run_dir, out_dir)
        write(out_dir / "orm-initial.json", snapshot())

        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        os.environ["AUDIT12_PORT"] = str(port)
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
            ["node", str(SUPPORT / "audit12_browser.cjs")],
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
        raise SystemExit("Usage: audit12_run.py [checks|tests ...|browser|serve|snapshot]")
    action = sys.argv[1]
    if action == "serve":
        setup(default_cookies=False)
        from django.core.management import execute_from_command_line

        execute_from_command_line(
            ["manage.py", "runserver", f"127.0.0.1:{os.environ['AUDIT12_PORT']}", "--noreload", "--insecure"]
        )
        return 0
    if action == "snapshot":
        setup(default_cookies=False)
        print(json.dumps(snapshot(), ensure_ascii=False, default=str))
        return 0
    if action == "checks":
        return run_checks()
    if action == "tests":
        targets = sys.argv[2:] or ["sales", "cash"]
        return run_tests(targets)
    if action == "browser":
        return run_browser()
    raise SystemExit(f"Unknown action: {action}")


if __name__ == "__main__":
    raise SystemExit(main())

