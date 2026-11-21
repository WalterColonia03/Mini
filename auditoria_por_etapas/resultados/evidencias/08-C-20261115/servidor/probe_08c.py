import hashlib
import json
import os
import re
import sys
import tempfile
import time
import uuid
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
R1 = ROOT / "r1-pmv"
sys.path.insert(0, str(R1))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

tmp_db_dir = Path(tempfile.mkdtemp(prefix="audit08c_probe_"))

import django
django.setup()

from django.conf import settings
settings.DATABASES["default"] = {
    "ENGINE": "django.db.backends.sqlite3",
    "NAME": str(tmp_db_dir / "probe08c.sqlite3"),
    "ATOMIC_REQUESTS": False,
    "AUTOCOMMIT": True,
    "CONN_MAX_AGE": 0,
    "OPTIONS": {"timeout": 20},
    "TIME_ZONE": None,
    "USER": "",
    "PASSWORD": "",
    "HOST": "",
    "PORT": "",
    "TEST": {"CHARSET": None, "COLLATION": None, "MIRROR": None, "NAME": None},
}
settings.ALLOWED_HOSTS = ["*"]

from django.core.management import call_command
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

call_command("migrate", verbosity=0)

from catalog.models import Category, Product
from cash.models import CashRegister, CashShift
from identity.models import Account, IdentityAuditEvent, Role
from inventory.models import InitialInventoryLoad, Lot, PhysicalAdjustment, StockWriteOff, Supplier
from inventory.services import confirm_initial_load, register_physical_adjustment, register_stock_entry, LotInput, write_off_stock
from sales.models import SaleDraft
from sales.services import add_product_to_draft, checkout_sale


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run():
    report = {
        "meta": {
            "stage": "08-C",
            "date": timezone.localtime().isoformat(),
            "r1_pmv_db_sha256": sha256_file(R1 / "r1_pmv.sqlite3"),
            "plan08_sha256": sha256_file(ROOT / "08_Historias_de_Usuario.md"),
            "inventory_file_count": len([p for p in (R1 / "inventory").rglob("*") if p.is_file() and "__pycache__" not in p.parts]),
            "app_css_sha256": sha256_file(R1 / "identity" / "static" / "identity" / "app.css"),
            "identity_audit_sha256": sha256_file(R1 / "identity" / "audit.py"),
        },
        "boundary_and_error_tests": {},
        "audit_event_behavior_on_403_404": {},
        "ui_surface_inventory": {},
        "kardex_volume_benchmark": {},
    }

    r_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    r_wh, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    r_sel, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

    u_admin = Account.objects.create_user(email="admin08c@local.test", password="Password123!", display_name="Admin 08C", role=r_admin, is_active=True)
    u_wh = Account.objects.create_user(email="alma08c@local.test", password="Password123!", display_name="Almacenero 08C", role=r_wh, is_active=True)
    u_sel = Account.objects.create_user(email="vend08c@local.test", password="Password123!", display_name="Vendedor 08C", role=r_sel, is_active=True)

    cat = Category.objects.create(name="Lacteos 08C")
    cat_inact = Category.objects.create(name="Inactiva 08C", is_active=True)
    prod = Product.objects.create(name="Leche UHT 08C", barcode="7750000000801", category=cat, unit=Product.Unit.UNIT, sale_price=Decimal("5.50"), minimum_stock=5, is_active=True)
    prod_q0 = Product.objects.create(name="Producto Q0 08C", barcode="7750000000802", category=cat, unit=Product.Unit.UNIT, sale_price=Decimal("3.00"), minimum_stock=2, is_active=True)
    prod_inact = Product.objects.create(name="Producto Inactivo 08C", barcode="7750000000803", category=cat_inact, unit=Product.Unit.UNIT, sale_price=Decimal("4.00"), minimum_stock=1, is_active=True)
    sup = Supplier.objects.create(name="Proveedor 08C SAC", ruc="20600000801", phone="999000801")

    today = timezone.localdate()
    load = confirm_initial_load(actor=u_wh, product=prod, lots=[LotInput(number="L-BASE-1", quantity=50, unit_cost=Decimal("2.5000"), expiration_date=today + timedelta(days=90))], supplier=sup)
    lot_base = load.lines.first().lot
    confirm_initial_load(actor=u_wh, product=prod_q0, lots=[LotInput(number="L-Q0-1", quantity=5, unit_cost=Decimal("1.5000"), expiration_date=today + timedelta(days=60))], supplier=sup)
    lot_q0 = prod_q0.lots.first()
    write_off_stock(actor=u_wh, lot=lot_q0, quantity=5, reason=StockWriteOff.Reason.THEFT, notes="Agotamiento inicial para Q=0")
    confirm_initial_load(actor=u_wh, product=prod_inact, lots=[LotInput(number="L-INACT-1", quantity=10, unit_cost=Decimal("2.0000"), expiration_date=today + timedelta(days=60))], supplier=sup)
    prod_inact.is_active = False
    prod_inact.save(update_fields=["is_active"])
    cat_inact.is_active = False
    cat_inact.save(update_fields=["is_active"])
    lot_inact = prod_inact.lots.first()

    # Create an expired lot via adjustment on prod_q0? Keep prod_q0 at Q=0 first, create expired lot via service on separate product
    prod_exp = Product.objects.create(name="Producto Vencido 08C", barcode="7750000000804", category=cat, unit=Product.Unit.UNIT, sale_price=Decimal("2.00"), minimum_stock=1, is_active=True)
    confirm_initial_load(actor=u_wh, product=prod_exp, lots=[LotInput(number="L-EXP-0", quantity=1, unit_cost=Decimal("1.0000"), expiration_date=today + timedelta(days=30))], supplier=sup)
    write_off_stock(actor=u_wh, lot=prod_exp.lots.first(), quantity=1, reason=StockWriteOff.Reason.THEFT, notes="Vaciar para lote vencido")
    adj_exp = register_physical_adjustment(
        actor=u_admin, product=prod_exp, delta=5, reason="Hallazgo lote vencido",
        number="L-VENCIDO", expiration_date=today, unit_cost=Decimal("1.0000"), cost_source="Doc prueba",
    )
    lot_exp = adj_exp.lot

    c_admin, c_wh, c_sel = Client(), Client(), Client()
    c_admin.force_login(u_admin)
    c_wh.force_login(u_wh)
    c_sel.force_login(u_sel)

    # 1. IdentityAuditEvent behavior on 403/404 for Stage 08
    ev_before = IdentityAuditEvent.objects.count()
    r403_wo = c_sel.get("/inventario/bajas/nueva/")
    r403_adj = c_sel.get("/inventario/ajustes/nuevo/")
    r403_mov = c_sel.get(f"/inventario/productos/{prod.pk}/movimientos/")
    r404_wo_list = c_admin.get("/inventario/bajas/")
    r404_adj_list = c_admin.get("/inventario/ajustes/")
    ev_after = IdentityAuditEvent.objects.count()
    report["audit_event_behavior_on_403_404"] = {
        "statuses": [r403_wo.status_code, r403_adj.status_code, r403_mov.status_code, r404_wo_list.status_code, r404_adj_list.status_code],
        "events_before": ev_before,
        "events_after": ev_after,
        "events_created": ev_after - ev_before,
        "types": list(IdentityAuditEvent.objects.values_list("action", "outcome")),
    }

    # 2. Boundary & error message tests (hidden fields, notes max length, query collisions, unicode, dates)
    b = {}

    # 2a. Missing / invalid hidden fields in StockWriteOffForm
    r_wo_missing_keys = c_wh.post(f"/inventario/bajas/nueva/?lote={lot_base.pk}", {
        "quantity": "1",
        "reason": StockWriteOff.Reason.THEFT,
        "notes": "Detalle valido",
    })
    html_missing = r_wo_missing_keys.content.decode()
    b["writeoff_missing_idempotency_key"] = {
        "status": r_wo_missing_keys.status_code,
        "has_english_this_field_required": "This field is required." in html_missing,
        "lot_qty_unchanged": Lot.objects.get(pk=lot_base.pk).available_quantity == 50,
    }

    r_wo_bad_uuid = c_wh.post(f"/inventario/bajas/nueva/?lote={lot_base.pk}", {
        "lot_id": str(lot_base.pk),
        "idempotency_key": "not-a-uuid",
        "quantity": "1",
        "reason": StockWriteOff.Reason.THEFT,
        "notes": "Detalle valido",
    })
    html_bad_uuid = r_wo_bad_uuid.content.decode()
    b["writeoff_bad_idempotency_uuid"] = {
        "status": r_wo_bad_uuid.status_code,
        "has_english_valid_uuid": "Enter a valid UUID." in html_bad_uuid,
        "exposes_raw_field_idempotency_key": "idempotency_key:" in html_bad_uuid,
    }

    # 2b. Missing / invalid hidden fields in PhysicalAdjustmentForm
    r_adj_bad_uuid = c_admin.post(f"/inventario/ajustes/nuevo/?lote={lot_base.pk}", {
        "lot_id": str(lot_base.pk),
        "idempotency_key": "not-a-uuid",
        "delta": "+1",
        "reason": "Conteo normal",
    })
    html_adj_bad = r_adj_bad_uuid.content.decode()
    b["adjustment_bad_idempotency_uuid"] = {
        "status": r_adj_bad_uuid.status_code,
        "has_english_valid_uuid": "Enter a valid UUID." in html_adj_bad,
        "exposes_raw_field_idempotency_key": "idempotency_key:" in html_adj_bad,
    }

    # 2c. GET + POST query collision ?lote=...&producto=...
    r_col_get = c_admin.get(f"/inventario/ajustes/nuevo/?lote={lot_base.pk}&producto={prod_q0.pk}")
    r_col_post = c_admin.post(f"/inventario/ajustes/nuevo/?lote={lot_base.pk}&producto={prod_q0.pk}", {
        "product_id": str(prod_q0.pk),
        "idempotency_key": str(uuid.uuid4()),
        "delta": "3",
        "reason": "Lote nuevo",
        "number": "L-COL-1",
        "expiration_date": (today + timedelta(days=60)).isoformat(),
        "unit_cost": "1.5000",
        "cost_source": "Factura test",
    })
    b["adjustment_query_lote_plus_producto_collision"] = {
        "get_status": r_col_get.status_code,
        "get_renders_new_lot_form": 'name="number"' in r_col_get.content.decode(),
        "get_warns_conflict": "Seleccione solo" in r_col_get.content.decode(),
        "post_status": r_col_post.status_code,
        "post_rejects_even_with_valid_new_lot_data": "Seleccione solo un lote existente o un producto para lote nuevo." in r_col_post.content.decode(),
        "lots_count_unchanged": Lot.objects.filter(product=prod_q0).count() == 1,
    }

    # 2d. WriteOff notes 5,000 chars accepted (no max_length) vs PhysicalAdjustment reason 301 chars rejected
    wo_big = c_wh.post(f"/inventario/bajas/nueva/?lote={lot_base.pk}", {
        "lot_id": str(lot_base.pk),
        "idempotency_key": str(uuid.uuid4()),
        "quantity": "1",
        "reason": StockWriteOff.Reason.THEFT,
        "notes": "X" * 5000,
    })
    lot_base.refresh_from_db()
    r_adj_301 = c_admin.post(f"/inventario/ajustes/nuevo/?lote={lot_base.pk}", {
        "lot_id": str(lot_base.pk),
        "idempotency_key": str(uuid.uuid4()),
        "delta": "+1",
        "reason": "R" * 301,
    })
    r_adj_space_305 = c_admin.post(f"/inventario/ajustes/nuevo/?lote={lot_base.pk}", {
        "lot_id": str(lot_base.pk),
        "idempotency_key": str(uuid.uuid4()),
        "delta": "+1",
        "reason": (" " * 10) + ("R" * 295),
    })
    b["text_length_boundaries"] = {
        "writeoff_5000_char_notes_redirect_302": wo_big.status_code,
        "writeoff_5000_char_saved_len": len(StockWriteOff.objects.order_by("-created_at").first().notes),
        "adjustment_301_reason_rejected_200": r_adj_301.status_code == 200 and lot_base.available_quantity == 49,
        "adjustment_10spaces_plus_295chars_accepted_302": r_adj_space_305.status_code,
    }
    lot_base.refresh_from_db()

    # 2e. MovementFilterForm edge cases: page=999999999, repeated params, inverted dates, valid same-minute filter
    r_mov_page_big = c_wh.get(f"/inventario/productos/{prod.pk}/movimientos/?page=999999999")
    r_mov_rep = c_wh.get(f"/inventario/productos/{prod.pk}/movimientos/?tipo=ajuste&tipo=merma")
    r_mov_2029_feb = c_wh.post(f"/inventario/ajustes/nuevo/?producto={prod_q0.pk}", {
        "product_id": str(prod_q0.pk),
        "idempotency_key": str(uuid.uuid4()),
        "delta": "2",
        "reason": "Fecha no bisiesto",
        "number": "L-2029",
        "expiration_date": "2029-02-29",
        "unit_cost": "1.5000",
        "cost_source": "Doc",
    })
    r_mov_max_exp = c_wh.post(f"/inventario/bajas/nueva/?lote={lot_base.pk}", {
        "lot_id": str(lot_base.pk),
        "idempotency_key": str(uuid.uuid4()),
        "quantity": "005",
        "reason": StockWriteOff.Reason.THEFT,
        "notes": "Ceros a la izquierda ASCII",
    })
    lot_base.refresh_from_db()
    b["numeric_date_and_kardex_filters"] = {
        "kardex_page_999999999_status": r_mov_page_big.status_code,
        "kardex_page_999999999_msg": "La página solicitada no existe" in r_mov_page_big.content.decode(),
        "kardex_repeated_tipo_msg": "No repita el parámetro tipo." in r_mov_rep.content.decode(),
        "non_leap_2029_02_29_rejected_200": r_mov_2029_feb.status_code == 200 and Lot.objects.filter(product=prod_q0).count() == 1,
        "writeoff_leading_zero_005_status": r_mov_max_exp.status_code,
        "lot_base_qty_after_005": lot_base.available_quantity,
    }

    # 2f. Cross-route tampering: ?lote= zero-stock lot in writeoff
    r_wo_q0_get = c_wh.get(f"/inventario/bajas/nueva/?lote={lot_q0.pk}")
    r_wo_q0_post = c_wh.post(f"/inventario/bajas/nueva/?lote={lot_q0.pk}", {
        "lot_id": str(lot_q0.pk),
        "idempotency_key": str(uuid.uuid4()),
        "quantity": "1",
        "reason": StockWriteOff.Reason.THEFT,
        "notes": "Intento sobre lote en cero",
    })
    b["zero_stock_lot_direct_url_writeoff"] = {
        "get_status": r_wo_q0_get.status_code,
        "post_status": r_wo_q0_post.status_code,
        "post_error_present": "La cantidad supera las existencias disponibles del lote." in r_wo_q0_post.content.decode(),
    }

    report["boundary_and_error_tests"] = b

    # 3. Literal UI surface inspection (titles, topbar <h1>, template <h2>, help/warning, nav)
    def parse_ui(resp):
        html = resp.content.decode()
        title_m = re.search(r"<title>(.*?)</title>", html, re.S)
        h1_m = re.search(r"<h1>(.*?)</h1>", html, re.S)
        h2_m = re.search(r"<h2[^>]*>(.*?)</h2>", html, re.S)
        nav_labels = re.findall(r'<a class="nav-item[^"]*" href="([^"]+)".*?<span>(.*?)</span>', html, re.S)
        return {
            "status": resp.status_code,
            "title": re.sub(r"\s+", " ", title_m.group(1)).strip() if title_m else None,
            "topbar_h1": re.sub(r"\s+", " ", h1_m.group(1)).strip() if h1_m else None,
            "content_h2": re.sub(r"\s+", " ", h2_m.group(1)).strip() if h2_m else None,
            "nav_links": [{"href": href, "label": re.sub(r"<[^>]+>", "", lbl).strip()} for href, lbl in nav_labels],
            "has_selector_inactivo_badge": "(Inactivo)" in html,
            "has_selector_vencido_badge": "(Vencido)" in html,
            "has_role_alert": 'role="alert"' in html,
            "has_writeoff_internal_disclaimer": "Constancia interna de merma. No es un comprobante de pago." in html,
            "has_adjustment_internal_disclaimer": "Registro interno de ajuste" in html or "Ajuste por conteo" in html,
        }

    latest_wo = StockWriteOff.objects.order_by("-created_at").first()
    latest_adj = PhysicalAdjustment.objects.order_by("-created_at").first()
    report["ui_surface_inventory"] = {
        "admin_writeoff_selector": parse_ui(c_admin.get("/inventario/bajas/nueva/")),
        "wh_writeoff_selector": parse_ui(c_wh.get("/inventario/bajas/nueva/")),
        "wh_writeoff_receipt": parse_ui(c_wh.get(f"/inventario/bajas/{latest_wo.pk}/")),
        "admin_adjustment_selector": parse_ui(c_admin.get("/inventario/ajustes/nuevo/")),
        "admin_adjustment_detail": parse_ui(c_admin.get(f"/inventario/ajustes/{latest_adj.pk}/")),
        "wh_adjustment_detail": parse_ui(c_wh.get(f"/inventario/ajustes/{latest_adj.pk}/")),
        "admin_kardex": parse_ui(c_admin.get(f"/inventario/productos/{prod.pk}/movimientos/")),
        "wh_kardex": parse_ui(c_wh.get(f"/inventario/productos/{prod.pk}/movimientos/")),
    }

    # 4. PT-KARDEX-01 Volume Benchmark: 2,011 events on 1 product (recepciones, ventas, mermas, ajustes)
    prod_vol = Product.objects.create(name="Producto Volumen 08C", barcode="7750000000899", category=cat, unit=Product.Unit.UNIT, sale_price=Decimal("10.00"), minimum_stock=5, is_active=True)
    confirm_initial_load(actor=u_wh, product=prod_vol, lots=[LotInput(number="VOL-0", quantity=2000, unit_cost=Decimal("4.0000"), expiration_date=today + timedelta(days=365))], supplier=sup)
    for idx in range(1, 11):
        register_stock_entry(actor=u_wh, product=prod_vol, lots=[LotInput(number=f"VOL-{idx}", quantity=500, unit_cost=Decimal("4.2000"), expiration_date=today + timedelta(days=365 + idx))], supplier=sup)

    reg = CashRegister.objects.create(name="CAJA-VOL-08C")
    shift = CashShift.objects.create(cash_register=reg, seller=u_sel, opening_amount=Decimal("100.00"), status=CashShift.Status.OPEN)

    for _ in range(1500):
        draft = add_product_to_draft(actor=u_sel, product_id=prod_vol.pk, quantity=1)
        checkout_sale(actor=u_sel, draft_id=draft.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4())

    target_lot = prod_vol.lots.filter(available_quantity__gt=350).first()
    for _ in range(300):
        write_off_stock(actor=u_wh, lot=target_lot, quantity=1, reason=StockWriteOff.Reason.THEFT, notes="Merma volumen", idempotency_key=uuid.uuid4())

    for j in range(200):
        register_physical_adjustment(actor=u_admin, lot=target_lot, delta=(1 if j % 2 == 0 else -1), reason=f"Ajuste volumen {j}", idempotency_key=uuid.uuid4())

    def measure_kardex(url: str):
        with CaptureQueriesContext(connection) as ctx:
            t0 = time.perf_counter()
            resp = c_admin.get(url)
            ms = (time.perf_counter() - t0) * 1000.0
        body = resp.content.decode()
        rows = len(re.findall(r'<tr data-event-id="', body))
        cnt_m = re.search(r'data-testid="filtered-count">(\d+)<', body)
        return {
            "url": url,
            "status": resp.status_code,
            "queries": len(ctx),
            "elapsed_ms": round(ms, 2),
            "html_bytes": len(resp.content),
            "rendered_rows": rows,
            "filtered_count": int(cnt_m.group(1)) if cnt_m else None,
        }

    report["kardex_volume_benchmark"] = {
        "sqlite_seeded_events_approx": 1 + 10 + 1500 + 300 + 200,
        "page_1": measure_kardex(f"/inventario/productos/{prod_vol.pk}/movimientos/"),
        "page_last_81": measure_kardex(f"/inventario/productos/{prod_vol.pk}/movimientos/?page=81"),
        "filter_ajuste": measure_kardex(f"/inventario/productos/{prod_vol.pk}/movimientos/?tipo=ajuste"),
        "filter_salidas": measure_kardex(f"/inventario/productos/{prod_vol.pk}/movimientos/?tipo=salidas"),
    }

    out = Path(__file__).with_name("probe_08c_resultado.json")
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "ok": True,
        "kardex_page_1": report["kardex_volume_benchmark"]["page_1"],
        "kardex_page_81": report["kardex_volume_benchmark"]["page_last_81"],
        "events_on_403_404": report["audit_event_behavior_on_403_404"]["events_created"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    run()
