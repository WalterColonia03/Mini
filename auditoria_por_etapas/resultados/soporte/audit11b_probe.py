"""Stage 11 isolated verification probe (SQLite :memory:, zero changes to r1_pmv.sqlite3)."""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sys
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "r1-pmv/manage.py").is_file())
PROJECT = ROOT / "r1-pmv"
OUT = Path(sys.argv[1]).resolve()
OUT.mkdir(parents=True, exist_ok=False)

os.environ.update(
    APP_ENV="test",
    DJANGO_DEBUG="false",
    DJANGO_SETTINGS_MODULE="config.settings",
    DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
    DJANGO_ALLOWED_HOSTS="testserver,localhost,127.0.0.1",
)
sys.path.insert(0, str(PROJECT))
os.chdir(PROJECT)

from config import env as project_env  # noqa: E402

project_env.load_dotenv = lambda path=None: None

from django.conf import settings  # noqa: E402

settings.DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}

import django  # noqa: E402

django.setup()

from django.core.exceptions import ValidationError  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.db import IntegrityError, connection, transaction  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import setup_test_environment  # noqa: E402
from django.urls import reverse  # noqa: E402
from django.utils import timezone  # noqa: E402

from cash.models import CashRegister, CashShift, CashShiftClose  # noqa: E402
from cash.services import close_cash_shift, open_cash_shift  # noqa: E402
from catalog.models import Category, Product  # noqa: E402
from identity.models import Account, Role  # noqa: E402
from inventory.models import Lot, StockWriteOff  # noqa: E402
from inventory.services import LotInput, confirm_initial_load, write_off_stock  # noqa: E402
from sales.models import Sale, SaleCounter, SaleDraft, SaleDraftLine, SaleLine, SaleLotAllocation  # noqa: E402
from sales.services import (  # noqa: E402
    DISCOUNTS_DISABLED,
    add_product_to_draft,
    checkout_sale,
    discard_active_draft,
    draft_signature,
    draft_totals,
)

PASSWORD = "Audit11B!ProbePassword"
LIMA = ZoneInfo("America/Lima")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_snapshot() -> dict:
    exts = {".py", ".html", ".css", ".js"}
    dirs = ("identity", "catalog", "inventory", "cash", "sales", "config", "templates", "app_platform", "tests")
    files = sorted(
        p for d in dirs for p in (PROJECT / d).rglob("*") if p.is_file() and p.suffix in exts
    )
    manifest = {p.relative_to(PROJECT).as_posix(): sha_bytes(p.read_bytes()) for p in files}
    return {
        "count": len(manifest),
        "sha256": sha_bytes(json.dumps(manifest, sort_keys=True).encode()),
        "files": manifest,
    }


def db_witness() -> dict:
    return {
        "sales": list(
            Sale.objects.order_by("id").values(
                "id", "correlative", "total_amount", "base_amount", "igv_amount",
                "discount_amount", "cash_received", "change_given", "draft_id",
            )
        ),
        "sale_lines": list(
            SaleLine.objects.order_by("id").values(
                "id", "sale_id", "position", "product_id", "quantity", "unit_price", "amount", "unit_cost"
            )
        ),
        "allocations": list(
            SaleLotAllocation.objects.order_by("id").values("id", "line_id", "lot_id", "quantity")
        ),
        "lots": list(
            Lot.objects.order_by("id").values("id", "number", "available_quantity", "expiration_date")
        ),
        "products": list(
            Product.objects.order_by("id").values("id", "sale_price", "average_cost", "is_active")
        ),
        "counters": list(SaleCounter.objects.order_by("id").values("id", "next_value")),
        "drafts": list(SaleDraft.objects.order_by("id").values("id", "status")),
        "closes": list(CashShiftClose.objects.order_by("id").values("id", "expected_amount", "counted_amount", "difference")),
    }


def main() -> None:
    setup_test_environment()
    call_command("migrate", verbosity=0, interactive=False)

    build_before = build_snapshot()
    plan08_hash = sha_bytes((ROOT / "08_Historias_de_Usuario.md").read_bytes())

    r_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    r_sel, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

    admin = Account.objects.create_user("admin11b@test.invalid", PASSWORD, display_name="Admin 11B", role=r_admin)
    wh = Account.objects.create_user("wh11b@test.invalid", PASSWORD, display_name="Almacenero 11B", role=r_wh)
    seller1 = Account.objects.create_user("seller1_11b@test.invalid", PASSWORD, display_name="Vendedora 11B", role=r_sel)
    seller2 = Account.objects.create_user("seller2_11b@test.invalid", PASSWORD, display_name="Vendedor 11B Dos", role=r_sel)
    reg = CashRegister.objects.create(code="CAJA-01")
    cat = Category.objects.create(name="Abarrotes 11B")
    today = timezone.localdate()

    def login_client(acc: Account) -> Client:
        c = Client()
        assert c.login(email=acc.email, password=PASSWORD)
        return c

    results: dict = {
        "executed_utc": datetime.now(ZoneInfo("UTC")).isoformat(),
        "database": ":memory:",
        "plan08_sha256": plan08_hash,
        "build_before": {"count": build_before["count"], "sha256": build_before["sha256"]},
        "checks": {},
    }

    # ── P01: Cantidad y precio + limites por operacion y acumulado ───────────
    p_min = Product.objects.create(category=cat, name="Caramelo Min", barcode="11B-MIN", sale_price=Decimal("0.01"))
    confirm_initial_load(actor=wh, product=p_min, lots=[LotInput("L-MIN", 5, Decimal("0.0050"), today + timedelta(days=30))])

    p_max = Product.objects.create(category=cat, name="Equipo Max", barcode="11B-MAX", sale_price=Decimal("9999999.99"))
    confirm_initial_load(actor=wh, product=p_max, lots=[LotInput("L-MAX", 5, Decimal("100.0000"), today + timedelta(days=30))])

    p_half = Product.objects.create(category=cat, name="Producto CincoM", barcode="11B-5M", sale_price=Decimal("5000000.00"))
    confirm_initial_load(actor=wh, product=p_half, lots=[LotInput("L-5M", 10, Decimal("100.0000"), today + timedelta(days=30))])

    shift = open_cash_shift(actor=seller1, opening_amount=Decimal("0.00"))
    sc1 = login_client(seller1)

    # Qty invalid inputs on draft
    bad_qty_cases = {}
    before_w = db_witness()
    for bad_q in ("0", "-1", "1.5", "abc", "1000000"):
        resp = sc1.post(reverse("sales-draft"), {"product_id": str(p_min.pk), "quantity": bad_q})
        bad_qty_cases[bad_q] = {"status": resp.status_code, "unchanged": db_witness() == before_w}
        assert bad_qty_cases[bad_q]["unchanged"]

    # DB constraint on SaleDraftLine.quantity <= 999999
    d_tmp = add_product_to_draft(actor=seller1, product_id=p_min.pk, quantity=1)
    line_tmp = d_tmp.lines.get()
    db_qty_rejected = False
    try:
        with transaction.atomic():
            SaleDraftLine.objects.filter(pk=line_tmp.pk).update(quantity=1_000_000)
    except IntegrityError:
        db_qty_rejected = True
    # Note: in SQLite the CheckConstraint enforces quantity <= 999999
    assert db_qty_rejected, "Expected IntegrityError for SaleDraftLine.quantity=1000000"
    discard_active_draft(actor=seller1)

    # Min sale 0.01
    add_product_to_draft(actor=seller1, product_id=p_min.pk, quantity=1)
    init = sc1.get(reverse("sales-checkout")).context["form"].initial
    r_min = sc1.post(
        reverse("sales-checkout"),
        {
            "cash_received": "0.01",
            "idempotency_key": str(init["idempotency_key"]),
            "expected_subtotal": str(init["expected_subtotal"]),
            "draft_signature": init["draft_signature"],
        },
    )
    assert r_min.status_code == 302
    sale_min = Sale.objects.get(correlative="V-00000001")
    assert (sale_min.total_amount, sale_min.base_amount, sale_min.igv_amount, sale_min.change_given) == (
        Decimal("0.01"), Decimal("0.01"), Decimal("0.00"), Decimal("0.00")
    )

    # Exact max single sale 9,999,999.99
    add_product_to_draft(actor=seller1, product_id=p_max.pk, quantity=1)
    init_max = sc1.get(reverse("sales-checkout")).context["form"].initial
    r_max = sc1.post(
        reverse("sales-checkout"),
        {
            "cash_received": "9999999.99",
            "idempotency_key": str(init_max["idempotency_key"]),
            "expected_subtotal": str(init_max["expected_subtotal"]),
            "draft_signature": init_max["draft_signature"],
        },
    )
    assert r_max.status_code == 302
    sale_max = Sale.objects.get(correlative="V-00000002")
    assert sale_max.total_amount == Decimal("9999999.99")

    # Over single sale cap: 2 * 5,000,000.00 = 10,000,000.00
    add_product_to_draft(actor=seller1, product_id=p_half.pk, quantity=2)
    init_over = sc1.get(reverse("sales-checkout")).context["form"].initial
    w_before_over = db_witness()
    r_over_cash = sc1.post(
        reverse("sales-checkout"),
        {
            "cash_received": "10000000.00",
            "idempotency_key": str(init_over["idempotency_key"]),
            "expected_subtotal": str(init_over["expected_subtotal"]),
            "draft_signature": init_over["draft_signature"],
        },
    )
    assert r_over_cash.status_code == 200 and db_witness() == w_before_over
    r_over_total = sc1.post(
        reverse("sales-checkout"),
        {
            "cash_received": "9999999.99",
            "idempotency_key": str(init_over["idempotency_key"]),
            "expected_subtotal": str(init_over["expected_subtotal"]),
            "draft_signature": init_over["draft_signature"],
        },
    )
    assert r_over_total.status_code == 200 and db_witness() == w_before_over
    over_errors = list(r_over_total.context["form"].non_field_errors())
    discard_active_draft(actor=seller1)
    close_cash_shift(actor=seller1, counted_amount=Decimal("10000000.00"))

    results["checks"]["P01_cantidad_y_precio"] = {
        "bad_qty_cases": bad_qty_cases,
        "db_qty_max_constraint": db_qty_rejected,
        "min_0_01_sale": {
            "total": str(sale_min.total_amount),
            "base": str(sale_min.base_amount),
            "igv": str(sale_min.igv_amount),
        },
        "max_9999999_99_ok": True,
        "over_10M_rejected": True,
        "over_total_errors": over_errors,
        "accumulated_10M_shift_close_ok": True,
    }

    # ── P02: Efectivo insuficiente / invalido / exacto / excedente ───────────
    p_20 = Product.objects.create(category=cat, name="Producto 20", barcode="11B-20", sale_price=Decimal("10.00"))
    confirm_initial_load(actor=wh, product=p_20, lots=[LotInput("L-20", 20, Decimal("4.0000"), today + timedelta(days=30))])

    shift2 = open_cash_shift(actor=seller1, opening_amount=Decimal("100.00"))
    add_product_to_draft(actor=seller1, product_id=p_20.pk, quantity=2)  # Total 20.00
    w_before_cash = db_witness()
    cash_bad_results = {}
    for bad_cash in ("", "0", "0.00", "-5.00", "abc", "20.001", "+20.00", "1e2", "١٠", "10000000.00", "19.99"):
        init_c = sc1.get(reverse("sales-checkout")).context["form"].initial
        resp = sc1.post(
            reverse("sales-checkout"),
            {
                "cash_received": bad_cash,
                "idempotency_key": str(init_c["idempotency_key"]),
                "expected_subtotal": str(init_c["expected_subtotal"]),
                "draft_signature": init_c["draft_signature"],
            },
        )
        form_resp = resp.context["form"]
        cash_bad_results[bad_cash] = {
            "status": resp.status_code,
            "field_errors": [str(e) for e in form_resp["cash_received"].errors],
            "non_field_errors": [str(e) for e in form_resp.non_field_errors()],
            "unchanged": db_witness() == w_before_cash,
        }
        assert resp.status_code == 200 and cash_bad_results[bad_cash]["unchanged"]

    # Check shortfall ("faltante") exact message on 19.99 vs 20.00
    short_msgs = cash_bad_results["19.99"]["non_field_errors"]
    mentions_shortfall_amount = any("0.01" in m or "0,01" in m or "faltante" in m.lower() for m in short_msgs)

    # Exact 20.00
    init_ex = sc1.get(reverse("sales-checkout")).context["form"].initial
    r_ex = sc1.post(
        reverse("sales-checkout"),
        {
            "cash_received": "20.00",
            "idempotency_key": str(init_ex["idempotency_key"]),
            "expected_subtotal": str(init_ex["expected_subtotal"]),
            "draft_signature": init_ex["draft_signature"],
        },
    )
    assert r_ex.status_code == 302
    s_ex = Sale.objects.get(idempotency_key=init_ex["idempotency_key"])
    assert (s_ex.total_amount, s_ex.cash_received, s_ex.change_given) == (
        Decimal("20.00"), Decimal("20.00"), Decimal("0.00")
    )

    # Excess 50.00 on 20.00
    add_product_to_draft(actor=seller1, product_id=p_20.pk, quantity=2)
    init_exc = sc1.get(reverse("sales-checkout")).context["form"].initial
    r_exc = sc1.post(
        reverse("sales-checkout"),
        {
            "cash_received": "50.00",
            "idempotency_key": str(init_exc["idempotency_key"]),
            "expected_subtotal": str(init_exc["expected_subtotal"]),
            "draft_signature": init_exc["draft_signature"],
        },
    )
    assert r_exc.status_code == 302
    s_exc = Sale.objects.get(idempotency_key=init_exc["idempotency_key"])
    assert (s_exc.total_amount, s_exc.cash_received, s_exc.change_given) == (
        Decimal("20.00"), Decimal("50.00"), Decimal("30.00")
    )
    close_s2 = close_cash_shift(actor=seller1, counted_amount=Decimal("140.00"))
    # opening 100 + 20 + 20 = 140 (NOT 100 + 20 + 50!)
    assert close_s2.expected_amount == Decimal("140.00") and close_s2.difference == Decimal("0.00")

    results["checks"]["P02_efectivo_y_faltante"] = {
        "invalid_cash_cases": cash_bad_results,
        "insufficient_19_99_messages": short_msgs,
        "mentions_shortfall_amount": mentions_shortfall_amount,
        "exact_cash_change": str(s_ex.change_given),
        "excess_50_change": str(s_exc.change_given),
        "shift_expected_after_excess_cash": str(close_s2.expected_amount),
    }

    # ── P03: Descuentos deshabilitados, limites y recuperacion historica ─────
    shift3 = open_cash_shift(actor=seller1, opening_amount=Decimal("50.00"))
    add_product_to_draft(actor=seller1, product_id=p_20.pk, quantity=2)  # subtotal 20.00
    get_co = sc1.get(reverse("sales-checkout"))
    co_html = get_co.content.decode("utf-8")
    has_visible_discount_input = ('name="discount_amount"' in co_html) and ('type="hidden" name="discount_amount"' not in co_html)
    w_before_disc = db_witness()
    disc_rejects = {}
    for bad_d in ("2.00", "0.01", "-1.00", "0.001", "abc", " 0.00 "):
        init_d = get_co.context["form"].initial
        resp = sc1.post(
            reverse("sales-checkout"),
            {
                "cash_received": "20.00",
                "discount_amount": bad_d,
                "idempotency_key": str(init_d["idempotency_key"]),
                "expected_subtotal": str(init_d["expected_subtotal"]),
                "draft_signature": init_d["draft_signature"],
            },
        )
        assert resp.status_code == 200
        assert resp.context["totals"].total == Decimal("20.00")
        assert resp.context["subtotal"] == Decimal("20.00")
        assert DISCOUNTS_DISABLED in resp.content.decode("utf-8")
        assert db_witness() == w_before_disc
        disc_rejects[bad_d] = {"status": resp.status_code, "message_present": True, "unchanged": True}

    # Multi-value discount_amount=['0.00', '2.00']
    init_dm = get_co.context["form"].initial
    resp_dm = sc1.post(
        reverse("sales-checkout"),
        {
            "cash_received": "20.00",
            "discount_amount": ["0.00", "2.00"],
            "idempotency_key": str(init_dm["idempotency_key"]),
            "expected_subtotal": str(init_dm["expected_subtotal"]),
            "draft_signature": init_dm["draft_signature"],
        },
    )
    assert resp_dm.status_code == 200 and DISCOUNTS_DISABLED in resp_dm.content.decode("utf-8")
    assert db_witness() == w_before_disc

    # Service direct reject with discount_amount > 0
    draft3 = SaleDraft.objects.get(seller=seller1, status=SaleDraft.Status.ACTIVE)
    try:
        checkout_sale(
            actor=seller1,
            draft_id=draft3.pk,
            cash_received=Decimal("20.00"),
            discount_amount=Decimal("2.00"),
            idempotency_key=uuid.uuid4(),
        )
        raise AssertionError("Expected ValidationError for service discount > 0")
    except ValidationError as exc:
        assert DISCOUNTS_DISABLED in exc.messages
    assert db_witness() == w_before_disc

    # Historical sale retry recovery (with discount 2.00 AND even after shift closed + another active draft)
    init_h = sc1.get(reverse("sales-checkout")).context["form"].initial
    r_h = sc1.post(
        reverse("sales-checkout"),
        {
            "cash_received": "20.00",
            "discount_amount": "0.00",
            "idempotency_key": str(init_h["idempotency_key"]),
            "expected_subtotal": str(init_h["expected_subtotal"]),
            "draft_signature": init_h["draft_signature"],
        },
    )
    assert r_h.status_code == 302
    s_hist = Sale.objects.get(idempotency_key=init_h["idempotency_key"])
    # Materialize pre-policy historical discount snapshot
    Sale.objects.filter(pk=s_hist.pk).update(
        discount_amount=Decimal("2.00"),
        total_amount=Decimal("18.00"),
        base_amount=Decimal("15.25"),
        igv_amount=Decimal("2.75"),
        change_given=Decimal("2.00"),
    )
    s_hist.refresh_from_db()

    # Retries while a new draft is active
    add_product_to_draft(actor=seller1, product_id=p_20.pk, quantity=1)
    retry_payload = {
        "cash_received": "20.00",
        "discount_amount": "2.00",
        "idempotency_key": str(init_h["idempotency_key"]),
        "expected_subtotal": str(init_h["expected_subtotal"]),
        "draft_signature": init_h["draft_signature"],
    }
    w_before_retry = db_witness()
    r_rec1 = sc1.post(reverse("sales-checkout"), retry_payload)
    assert r_rec1.status_code == 302 and f"/ventas/constancia/{s_hist.pk}/" in r_rec1["Location"]
    assert db_witness() == w_before_retry

    # Tampered discount on retry while new draft is active -> error, no mutation
    r_tamp_ret = sc1.post(reverse("sales-checkout"), dict(retry_payload, discount_amount="2.01"))
    assert r_tamp_ret.status_code == 200 and db_witness() == w_before_retry

    # Close shift after discarding active draft, then retry historical receipt
    discard_active_draft(actor=seller1)
    close_cash_shift(actor=seller1, counted_amount=Decimal("68.00"))
    w_closed = db_witness()
    r_rec_closed = sc1.post(reverse("sales-checkout"), retry_payload)
    assert r_rec_closed.status_code == 302 and f"/ventas/constancia/{s_hist.pk}/" in r_rec_closed["Location"]
    assert db_witness() == w_closed

    results["checks"]["P03_descuentos_y_recuperacion"] = {
        "has_visible_discount_input_in_checkout_get": has_visible_discount_input,
        "hidden_discount_input_present": 'name="discount_amount"' in co_html,
        "rejected_discount_cases": disc_rejects,
        "multi_value_rejected": True,
        "service_discount_rejected": True,
        "historical_discount_retry_with_new_draft_ok": True,
        "historical_discount_tampered_rejected": True,
        "historical_discount_retry_after_close_ok": True,
    }

    # ── P04: IGV HALF_UP ─────────────────────────────────────────────────────
    igv_cases = {}
    for total_str, exp_base, exp_igv in [
        ("0.01", "0.01", "0.00"),
        ("1.80", "1.53", "0.27"),
        ("10.65", "9.03", "1.62"),
        ("11.80", "10.00", "1.80"),
        ("14.20", "12.03", "2.17"),
        ("20.00", "16.95", "3.05"),
        ("25.00", "21.19", "3.81"),
    ]:
        amt = Decimal(total_str)
        fake_draft = type("D", (), {"lines": type("Ls", (), {"all": lambda self, a=amt: [type("L", (), {"amount": a})()]})()})()
        dt = draft_totals(fake_draft)
        b, i = dt.base, dt.igv
        assert dt.total == amt
        assert (b, i) == (Decimal(exp_base), Decimal(exp_igv)), f"{total_str}: {(b, i)}"
        assert b + i == amt
        igv_cases[total_str] = {"base": str(b), "igv": str(i)}
    results["checks"]["P04_igv_half_up"] = igv_cases

    # ── P05: FEFO 3 niveles + frontera vencimiento Lima + average_cost reset ─
    p_fefo = Product.objects.create(category=cat, name="Leche FEFO 11B", barcode="11B-FEFO", sale_price=Decimal("3.55"))
    t_now = timezone.now()
    load_f = confirm_initial_load(
        actor=wh,
        product=p_fefo,
        lots=[LotInput("L-SOON", 2, Decimal("2.0000"), today + timedelta(days=5))],
    )
    # Create explicit tie-breaker lots + expired lots directly in fixture to control exact received_at and UUIDs
    l_past = Lot.objects.create(
        product=p_fefo, initial_load=load_f, number="L-PAST", number_normalized="L-PAST",
        initial_quantity=5, available_quantity=5, unit_cost=Decimal("2.0000"), expiration_date=today - timedelta(days=1),
    )
    l_today = Lot.objects.create(
        product=p_fefo, initial_load=load_f, number="L-TODAY", number_normalized="L-TODAY",
        initial_quantity=5, available_quantity=5, unit_cost=Decimal("2.0000"), expiration_date=today,
    )
    l_tie_early = Lot.objects.create(
        product=p_fefo, initial_load=load_f, number="L-TIE-EARLY", number_normalized="L-TIE-EARLY",
        initial_quantity=2, available_quantity=2, unit_cost=Decimal("2.0000"), expiration_date=today + timedelta(days=20),
    )
    u_small = uuid.UUID("00000000-0000-4000-8000-000000000001")
    u_large = uuid.UUID("ffffffff-ffff-4fff-8fff-ffffffffffff")
    t_eq = t_now - timedelta(hours=2)
    l_tie_u_small = Lot.objects.create(
        id=u_small, product=p_fefo, initial_load=load_f, number="L-UUID-SMALL", number_normalized="L-UUID-SMALL",
        initial_quantity=2, available_quantity=2, unit_cost=Decimal("2.0000"), expiration_date=today + timedelta(days=20),
    )
    l_tie_u_large = Lot.objects.create(
        id=u_large, product=p_fefo, initial_load=load_f, number="L-UUID-LARGE", number_normalized="L-UUID-LARGE",
        initial_quantity=3, available_quantity=3, unit_cost=Decimal("2.0000"), expiration_date=today + timedelta(days=20),
    )
    # Set deterministic received_at timestamps bypassing trigger for fixture creation ONLY via update inside clean SQLite?
    # Note: inventory has guard trigger on received_at UPDATE, let's check! If trigger blocks received_at update, we'll know!
    trigger_blocked_received_at_update = False
    try:
        Lot.objects.filter(pk=l_tie_early.pk).update(received_at=t_now - timedelta(hours=3))
        Lot.objects.filter(pk__in=(u_small, u_large)).update(received_at=t_eq)
    except Exception:
        trigger_blocked_received_at_update = True

    shift4 = open_cash_shift(actor=seller1, opening_amount=Decimal("20.00"))
    add_product_to_draft(actor=seller1, product_id=p_fefo.pk, quantity=7)
    init_f = sc1.get(reverse("sales-checkout")).context["form"].initial
    r_fefo = sc1.post(
        reverse("sales-checkout"),
        {
            "cash_received": "30.00",
            "idempotency_key": str(init_f["idempotency_key"]),
            "expected_subtotal": str(init_f["expected_subtotal"]),
            "draft_signature": init_f["draft_signature"],
        },
    )
    assert r_fefo.status_code == 302
    s_fefo = Sale.objects.get(idempotency_key=init_f["idempotency_key"])
    line_f = s_fefo.lines.get()
    allocs = list(line_f.lot_allocations.select_related("lot").order_by("lot_snapshot_expiration_date", "lot_snapshot_received_at", "lot_id"))
    alloc_summary = [(a.lot_snapshot_number, a.quantity) for a in allocs]

    l_past.refresh_from_db()
    l_today.refresh_from_db()
    p_fefo.refresh_from_db()
    assert l_past.available_quantity == 5 and l_today.available_quantity == 5
    # With expired lots still having qty 10, selling remaining 2 sellable keeps average_cost = 2.0000
    add_product_to_draft(actor=seller1, product_id=p_fefo.pk, quantity=2)
    init_f2 = sc1.get(reverse("sales-checkout")).context["form"].initial
    sc1.post(
        reverse("sales-checkout"),
        {
            "cash_received": "10.00",
            "idempotency_key": str(init_f2["idempotency_key"]),
            "expected_subtotal": str(init_f2["expected_subtotal"]),
            "draft_signature": init_f2["draft_signature"],
        },
    )
    p_fefo.refresh_from_db()
    avg_with_expired_only = p_fefo.average_cost

    # Now write off expired lots to reach physical 0 -> wait: average_cost on full physical zero resets to 0.0000
    # Test clean product depletion via checkout to physical 0:
    p_zero = Product.objects.create(category=cat, name="Producto Cero", barcode="11B-ZERO", sale_price=Decimal("4.00"))
    confirm_initial_load(actor=wh, product=p_zero, lots=[LotInput("L-Z", 3, Decimal("2.3456"), today + timedelta(days=15))])
    add_product_to_draft(actor=seller1, product_id=p_zero.pk, quantity=3)
    init_z = sc1.get(reverse("sales-checkout")).context["form"].initial
    sc1.post(
        reverse("sales-checkout"),
        {
            "cash_received": "12.00",
            "idempotency_key": str(init_z["idempotency_key"]),
            "expected_subtotal": str(init_z["expected_subtotal"]),
            "draft_signature": init_z["draft_signature"],
        },
    )
    p_zero.refresh_from_db()
    s_zero = Sale.objects.get(idempotency_key=init_z["idempotency_key"])
    line_zero = s_zero.lines.get()
    assert p_zero.average_cost == Decimal("0.0000")
    assert line_zero.unit_cost == Decimal("2.3456")

    # Midnight expiration between draft and checkout
    p_mid = Product.objects.create(category=cat, name="Leche Medianoche", barcode="11B-MID", sale_price=Decimal("5.00"))
    confirm_initial_load(actor=wh, product=p_mid, lots=[LotInput("L-MID", 2, Decimal("2.0000"), today + timedelta(days=1))])
    d_mid = add_product_to_draft(actor=seller1, product_id=p_mid.pk, quantity=1)
    midnight_blocked = False
    with patch("sales.services.timezone.localdate", return_value=today + timedelta(days=1)):
        try:
            checkout_sale(actor=seller1, draft_id=d_mid.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4())
        except ValidationError as exc:
            midnight_blocked = True
            midnight_msg = exc.messages[0]
    assert midnight_blocked
    discard_active_draft(actor=seller1)

    results["checks"]["P05_fefo_vencimiento"] = {
        "trigger_blocked_received_at_update": trigger_blocked_received_at_update,
        "expired_past_today_untouched": True,
        "allocations_order": alloc_summary,
        "avg_cost_with_expired_only": str(avg_with_expired_only),
        "deplete_physical_zero_resets_product_avg": str(p_zero.average_cost),
        "deplete_keeps_line_unit_cost_4dec": str(line_zero.unit_cost),
        "midnight_expiry_rejected": midnight_blocked,
        "midnight_msg": midnight_msg,
    }

    # ── P06: Advertencia tributaria + sin costo en constancia + snapshots ────
    add_product_to_draft(actor=seller1, product_id=p_20.pk, quantity=1)
    get_co_html = sc1.get(reverse("sales-checkout")).content.decode("utf-8")
    expected_tax_warning = (
        "Esta venta genera una constancia interna. "
        "No emite una boleta ni factura electrónica autorizada por SUNAT."
    )
    tax_warning_before_confirm = expected_tax_warning in get_co_html
    receipt_html = sc1.get(reverse("sales-receipt", args=(s_fefo.pk,))).content.decode("utf-8")
    admin_c = login_client(admin)
    receipt_admin_html = admin_c.get(reverse("sales-receipt", args=(s_fefo.pk,))).content.decode("utf-8")
    discard_active_draft(actor=seller1)

    # Mutate masters and inspect receipt
    p_fefo.name = "Leche Renombrada 11B"
    p_fefo.sale_price = Decimal("99.00")
    p_fefo.save()
    seller1.display_name = "Nombre Cambiado 11B"
    seller1.save()
    reg.code = "CAJA-99"
    reg.save()
    receipt_after_rename = admin_c.get(reverse("sales-receipt", args=(s_fefo.pk,))).content.decode("utf-8")

    results["checks"]["P06_advertencia_y_snapshots"] = {
        "tax_warning_text": expected_tax_warning if tax_warning_before_confirm else "",
        "tax_warning_visible_before_confirm": tax_warning_before_confirm,
        "receipt_has_legal_legend": "CONTROL INTERNO — NO VÁLIDO COMO COMPROBANTE DE PAGO" in receipt_html,
        "receipt_hides_cost_seller_and_admin": ("2.0000" not in receipt_html) and ("2,0000" not in receipt_admin_html),
        "snapshots_preserved_after_rename": (
            "Leche FEFO 11B" in receipt_after_rename
            and "Vendedora 11B" in receipt_after_rename
            and "CAJA-01" in receipt_after_rename
            and "Leche Renombrada 11B" not in receipt_after_rename
        ),
    }
    assert tax_warning_before_confirm
    assert results["checks"]["P06_advertencia_y_snapshots"]["receipt_has_legal_legend"]
    assert results["checks"]["P06_advertencia_y_snapshots"]["receipt_hides_cost_seller_and_admin"]
    assert results["checks"]["P06_advertencia_y_snapshots"]["snapshots_preserved_after_rename"]

    # ── P07: Cambios entre pantallas y rollback post-escritura ───────────────
    p_p7 = Product.objects.create(category=cat, name="Producto P7", barcode="11B-P7", sale_price=Decimal("10.00"))
    confirm_initial_load(actor=wh, product=p_p7, lots=[LotInput("L-P7", 10, Decimal("3.0000"), today + timedelta(days=30))])
    add_product_to_draft(actor=seller1, product_id=p_p7.pk, quantity=2)
    init_p7 = sc1.get(reverse("sales-checkout")).context["form"].initial

    # Price drop while in checkout: GET must NOT mutate, POST updates draft & rejects sale
    p_p7.sale_price = Decimal("8.00")
    p_p7.save(update_fields=["sale_price"])
    w_before_get_p7 = db_witness()
    sc1.get(reverse("sales-checkout"))
    assert db_witness() == w_before_get_p7

    r_p7_post1 = sc1.post(
        reverse("sales-checkout"),
        {
            "cash_received": "20.00",
            "idempotency_key": str(init_p7["idempotency_key"]),
            "expected_subtotal": str(init_p7["expected_subtotal"]),
            "draft_signature": init_p7["draft_signature"],
        },
    )
    assert r_p7_post1.status_code == 200
    assert "cambió de S/ 10.00 a S/ 8.00" in r_p7_post1.content.decode("utf-8")
    assert SaleDraftLine.objects.get(product=p_p7).unit_price == Decimal("8.00")
    assert len(db_witness()["sales"]) == len(w_before_get_p7["sales"])

    # Post-write rollback after SaleLotAllocation + Lot.save (via reset_average_cost_if_empty)
    w_before_rb = db_witness()
    draft_rb = SaleDraft.objects.get(seller=seller1, status=SaleDraft.Status.ACTIVE)
    idem_rb = uuid.uuid4()
    rb_caught = False
    with patch("sales.services.reset_average_cost_if_empty", side_effect=RuntimeError("Injected post-write error after allocation & lot save")):
        try:
            checkout_sale(actor=seller1, draft_id=draft_rb.pk, cash_received=Decimal("20.00"), idempotency_key=idem_rb)
        except RuntimeError:
            rb_caught = True
    assert rb_caught and db_witness() == w_before_rb
    # Retry with same idempotency_key succeeds cleanly!
    s_rb_ok = checkout_sale(actor=seller1, draft_id=draft_rb.pk, cash_received=Decimal("20.00"), idempotency_key=idem_rb)
    assert s_rb_ok.total_amount == Decimal("16.00") and s_rb_ok.change_given == Decimal("4.00")

    results["checks"]["P07_cambios_y_reversion"] = {
        "price_decrease_get_no_muta": True,
        "price_decrease_post_requires_review": True,
        "post_write_allocation_rollback_exact": True,
        "retry_after_rollback_succeeds": True,
    }

    # ── P08: Autorizacion cruzada ────────────────────────────────────────────
    anon_c = Client()
    wh_c = login_client(wh)
    sc2 = login_client(seller2)
    assert anon_c.get(reverse("sales-checkout")).status_code == 302
    assert anon_c.post(reverse("sales-checkout"), {}).status_code == 302
    assert anon_c.get(reverse("sales-receipt", args=(s_fefo.pk,))).status_code == 302
    assert admin_c.get(reverse("sales-checkout")).status_code == 403
    assert admin_c.post(reverse("sales-checkout"), {}).status_code == 403
    assert wh_c.get(reverse("sales-checkout")).status_code == 403
    assert wh_c.post(reverse("sales-checkout"), {}).status_code == 403
    assert wh_c.get(reverse("sales-receipt", args=(s_fefo.pk,))).status_code == 403
    assert sc2.get(reverse("sales-receipt", args=(s_fefo.pk,))).status_code == 404

    results["checks"]["P08_autorizacion"] = {
        "anon_redirected_302": True,
        "admin_checkout_403": True,
        "warehouse_checkout_and_receipt_403": True,
        "other_seller_receipt_404": True,
    }

    build_after = build_snapshot()
    results["build_after"] = {"count": build_after["count"], "sha256": build_after["sha256"]}
    results["sources_stable"] = build_before == build_after
    if not results["sources_stable"]:
        results["changed_sources"] = [
            k for k in sorted(set(build_before["files"]) | set(build_after["files"]))
            if build_before["files"].get(k) != build_after["files"].get(k)
        ]

    (OUT / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "sources_stable": results["sources_stable"], "build": build_after["sha256"]}))


if __name__ == "__main__":
    main()
