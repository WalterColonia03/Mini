"""Isolated Stage 08 technical verification probe (no mutation to repo or operational DB)."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import secrets
import shutil
import sys
import tempfile
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[5]
R1_PMV = ROOT / "r1-pmv"
BUILD_JSON = ROOT / "auditoria_por_etapas/resultados/evidencias/14-CIERRE-20261114/build-final.json"
OUT_JSON = Path(__file__).resolve().parent / "probe_etapa08_resultado.json"

assert (R1_PMV / "manage.py").exists(), f"Missing manage.py under {R1_PMV}"
assert BUILD_JSON.exists(), f"Missing {BUILD_JSON}"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_hashes_and_dead_helpers() -> dict:
    build_data = json.loads(BUILD_JSON.read_text(encoding="utf-8"))
    ref_files: dict[str, str] = build_data["fuentes"]
    stage08_rel_files = sorted(
        k
        for k in ref_files
        if k.startswith("inventory/")
        or k in {
            "catalog/templates/catalog/product_expirations.html",
            "identity/templates/identity/base.html",
            "sales/services.py",
        }
    )
    compared = {}
    all_inventory_match = True
    for rel in stage08_rel_files:
        cur_hash = sha256_file(R1_PMV / rel)
        matches = cur_hash == ref_files[rel]
        if not matches:
            all_inventory_match = False
        compared[rel] = {"matches_14_cierre": matches, "sha256": cur_hash}

    changed_since_14_cierre = []
    for rel, expected in ref_files.items():
        cur_path = R1_PMV / rel
        if not cur_path.exists():
            changed_since_14_cierre.append({"file": rel, "status": "missing"})
        else:
            cur_h = sha256_file(cur_path)
            if cur_h != expected:
                changed_since_14_cierre.append({"file": rel, "expected": expected, "actual": cur_h})

    # Scan for helper definitions & call sites across all Python files in r1-pmv
    helpers = [
        "_inventory_payload_signature",
        "_resolve_inventory_idempotency_key",
        "_load_locked_inventory_session",
        "_inventory_key_status",
        "_save_inventory_key",
    ]
    helper_refs: dict[str, list[str]] = {h: [] for h in helpers}
    for py_file in sorted(R1_PMV.rglob("*.py")):
        if ".venv" in py_file.parts:
            continue
        text = py_file.read_text(encoding="utf-8")
        for idx, line in enumerate(text.splitlines(), start=1):
            for h in helpers:
                if h in line:
                    helper_refs[h].append(f"{py_file.relative_to(R1_PMV).as_posix()}:{idx}:{line.strip()}")

    tracked_docs = [
        "08_Historias_de_Usuario.md",
        "07_Reglas_de_Negocio.md",
        "09_Product_Backlog.md",
        "03_Matriz_de_Trazabilidad_y_Pruebas.md",
        "02_Diseno_Tecnico_R1_PMV.md",
        "16_Task_Breakdown.md",
        "21_Alcance_Actual_y_Diferencias.md",
        "r1-pmv/r1_pmv.sqlite3",
    ]
    doc_hashes = {d: sha256_file(ROOT / d) for d in tracked_docs}

    return {
        "stage08_files_checked": len(stage08_rel_files),
        "all_stage08_files_match_14_cierre": all_inventory_match,
        "all_changed_files_since_14_cierre": changed_since_14_cierre,
        "dead_helper_references": helper_refs,
        "doc_and_protected_db_hashes": doc_hashes,
    }


def run_django_probes() -> dict:
    tmpdir = Path(tempfile.mkdtemp(prefix="audit08b_probe_"))
    db_path = tmpdir / "probe08b.sqlite3"
    try:
        sys.path.insert(0, str(R1_PMV))
        os.environ.update(
            APP_ENV="test",
            DJANGO_DEBUG="false",
            DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
            DJANGO_SETTINGS_MODULE="config.settings",
            DJANGO_ALLOWED_HOSTS="testserver,127.0.0.1,localhost",
        )
        from config import env as config_env

        config_env.load_dotenv = lambda path=None: None
        from django.conf import settings

        settings.DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": str(db_path),
            }
        }
        # Avoid modifying repo sessions or touching protected files
        import django

        django.setup()
        from django.core.exceptions import ValidationError
        from django.core.management import call_command
        from django.test import Client
        from django.utils import timezone as tz

        call_command("migrate", verbosity=0)

        from cash.models import CashRegister, CashShift
        from cash.services import open_cash_shift
        from catalog.models import Category, Product
        from identity.models import Account, Role
        from inventory.forms import (
            LotInputForm,
            MovementFilterForm,
            NewLotAdjustmentForm,
            PhysicalAdjustmentForm,
            StockWriteOffForm,
        )
        from inventory.ledger import build_ledger
        from inventory.models import InitialInventoryLoad, Lot, PhysicalAdjustment, StockWriteOff
        from inventory.services import (
            LotInput,
            confirm_initial_load,
            register_physical_adjustment,
            register_stock_entry,
            write_off_stock,
        )
        from sales.models import Sale, SaleLotAllocation
        from sales.services import add_product_to_draft, checkout_sale

        role_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
        role_alm, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
        role_ven, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

        admin = Account.objects.create_user(
            email="adm08b@example.invalid",
            password="Audit08b!Pass#91",
            role=role_admin,
            display_name="Admin 08B",
        )
        almacenero = Account.objects.create_user(
            email="alm08b@example.invalid",
            password="Audit08b!Pass#92",
            role=role_alm,
            display_name="Almacenero 08B",
        )
        vendedor = Account.objects.create_user(
            email="ven08b@example.invalid",
            password="Audit08b!Pass#93",
            role=role_ven,
            display_name="Vendedor 08B",
        )

        cat = Category.objects.create(name="Lacteos Audit08B")
        prod = Product.objects.create(
            category=cat,
            name="Leche UHT 1L",
            barcode="7750800000012",
            sale_price=Decimal("5.50"),
            minimum_stock=5,
        )
        today = tz.localdate()

        # Confirm initial load: 10 units @ S/ 3.0000
        init_load = confirm_initial_load(
            actor=almacenero,
            product=prod,
            lots=[LotInput(number="L-INIT-01", quantity=10, unit_cost=Decimal("3.0000"), expiration_date=today + timedelta(days=30))],
        )
        init_lot = Lot.objects.get(product=prod, number="L-INIT-01")

        # 1. Probe PhysicalAdjustmentForm vs LotInputForm unit_cost validation asymmetry
        form_probes = {}
        for sample_label, raw_cost in [("scientific_lower", "1e2"), ("scientific_upper", "1E2"), ("arabic_digits", "٢.٥"), ("five_decimals", "1.12345"), ("negative", "-1.00"), ("zero", "0"), ("over_max", "1000000.00")]:
            pa_form = PhysicalAdjustmentForm(
                data={
                    "lot_id": str(init_lot.pk),
                    "delta": "1",
                    "reason": "Conteo",
                    "unit_cost": raw_cost,
                    "idempotency_key": str(uuid.uuid4()),
                }
            )
            li_form = LotInputForm(
                data={
                    "number": "L-TEST-X",
                    "expiration_date": (today + timedelta(days=10)).isoformat(),
                    "quantity": "1",
                    "unit_cost": raw_cost,
                }
            )
            form_probes[sample_label] = {
                "raw_cost": raw_cost,
                "PhysicalAdjustmentForm_valid": pa_form.is_valid(),
                "PhysicalAdjustmentForm_errors": {k: [str(e) for e in v] for k, v in pa_form.errors.items()},
                "PhysicalAdjustmentForm_cleaned_unit_cost": str(pa_form.cleaned_data.get("unit_cost")) if pa_form.is_valid() else None,
                "LotInputForm_valid": li_form.is_valid(),
                "LotInputForm_errors": {k: [str(e) for e in v] for k, v in li_form.errors.items()},
            }

        # 2. Probe legacy average_cost == 0 on write_off_stock vs register_physical_adjustment
        cat_leg = Category.objects.create(name="Legado 08B")
        prod_leg = Product.objects.create(
            category=cat_leg,
            name="Conserva Legada",
            barcode="7750800000099",
            sale_price=Decimal("8.00"),
            minimum_stock=2,
            average_cost=Decimal("0.0000"),
        )
        load_leg = InitialInventoryLoad.objects.create(
            product=prod_leg,
            responsible=almacenero,
            product_snapshot_name=prod_leg.name,
            product_snapshot_barcode=prod_leg.barcode,
            unit_snapshot=prod_leg.unit,
            responsible_snapshot_name=almacenero.display_name,
            supplier_snapshot_name="",
        )
        lot_leg = Lot.objects.create(
            product=prod_leg,
            initial_load=load_leg,
            number="L-LEG-0",
            expiration_date=today + timedelta(days=20),
            initial_quantity=5,
            available_quantity=5,
            unit_cost=Decimal("3.0000"),
        )
        wo_zero = write_off_stock(
            actor=almacenero,
            lot=lot_leg,
            quantity=1,
            reason=StockWriteOff.Reason.DAMAGE,
            notes="Envase abollado",
            idempotency_key=uuid.uuid4(),
        )
        lot_leg.refresh_from_db()
        try:
            register_physical_adjustment(
                actor=admin,
                lot=lot_leg,
                delta=1,
                reason="Hallazgo en piso",
                idempotency_key=uuid.uuid4(),
            )
            adj_zero_positive_error = None
        except ValidationError as exc:
            adj_zero_positive_error = [str(m) for m in exc.messages]

        # 3. Probe simultaneous ?lote=<lot>&producto=<prod> GET & POST in HTTP view
        c_admin = Client()
        c_admin.force_login(admin)
        c_alm = Client()
        c_alm.force_login(almacenero)
        c_ven = Client()
        c_ven.force_login(vendedor)
        c_anon = Client()

        resp_both_params_get = c_admin.get(
            f"/inventario/ajustes/nuevo/?lote={init_lot.pk}&producto={prod.pk}"
        )
        both_html = resp_both_params_get.content.decode("utf-8")

        # 4. Probe POST with tampered lot_id vs NewLotAdjustmentForm on simultaneous request
        # Check DEC-05 spacing normalization in NewLotAdjustmentForm & register_physical_adjustment
        new_lot_adj = register_physical_adjustment(
            actor=admin,
            product=prod,
            number="  Lote  Espacio-1  ",
            expiration_date=today + timedelta(days=40),
            delta=5,
            reason="Ingreso por conteo",
            idempotency_key=uuid.uuid4(),
        )
        new_lot_adj.lot.refresh_from_db()

        # Check Q=0 documented cost + Q>0 preservation + expiration boundary + leap year
        leap_adj = register_physical_adjustment(
            actor=admin,
            product=prod,
            number="L-LEAP-28",
            expiration_date=date(2028, 2, 29),
            delta=2,
            reason="Lote bisiesto",
            idempotency_key=uuid.uuid4(),
        )

        # Check roles & HTTP methods across all Stage 08 routes + future 404 routes
        wo_test = write_off_stock(
            actor=almacenero,
            lot=init_lot,
            quantity=1,
            reason=StockWriteOff.Reason.THEFT,
            notes="Unidad faltante en conteo",
            idempotency_key=uuid.uuid4(),
        )
        route_checks = {}
        routes = [
            ("writeoff_form", "/inventario/bajas/nueva/"),
            ("writeoff_receipt", f"/inventario/bajas/{wo_test.pk}/"),
            ("adjustment_form", "/inventario/ajustes/nuevo/"),
            ("adjustment_detail", f"/inventario/ajustes/{new_lot_adj.pk}/"),
            ("movements", f"/inventario/productos/{prod.pk}/movimientos/"),
            ("stock_overview", "/inventario/stock/"),
            ("future_writeoffs_root", "/inventario/bajas/"),
            ("future_writeoffs_hist", "/inventario/bajas/historial/"),
            ("future_adjustments_root", "/inventario/ajustes/"),
            ("future_adjustments_hist", "/inventario/ajustes/historial/"),
        ]
        for label, url in routes:
            route_checks[label] = {
                "anon_get": c_anon.get(url).status_code,
                "admin_get": c_admin.get(url).status_code,
                "almacenero_get": c_alm.get(url).status_code,
                "vendedor_get": c_ven.get(url).status_code,
                "admin_put": c_admin.put(url).status_code,
                "admin_delete": c_admin.delete(url).status_code,
            }

        # Check VENDEDOR on /ventas/ does NOT see unit costs (check AFTER sale too below)
        pos_ven_html = c_ven.get("/ventas/").content.decode("utf-8")
        mov_ven_status = c_ven.get(f"/inventario/productos/{prod.pk}/movimientos/").status_code

        # Check Sales + CashShift interaction
        register = CashRegister.objects.create(code="CAJA-01")
        shift = open_cash_shift(actor=vendedor, opening_amount=Decimal("50.00"))
        # Record an expired physical adjustment lot (non-sellable)
        expired_adj = register_physical_adjustment(
            actor=admin,
            product=prod,
            number="L-VENC-08B",
            expiration_date=today,
            delta=3,
            reason="Hallazgo vencido no vendible",
            idempotency_key=uuid.uuid4(),
        )
        # Perform a write-off of 2 units on L-INIT-01 (leaving 10 - 1 - 2 = 7 on L-INIT-01)
        write_off_stock(
            actor=almacenero,
            lot=init_lot,
            quantity=2,
            reason=StockWriteOff.Reason.DAMAGE,
            notes="Botella rota",
            idempotency_key=uuid.uuid4(),
        )
        # Sell 10 units -> FEFO should pull 7 from L-INIT-01 and 3 from Lote Espacio-1, NEVER L-VENC-08B
        draft = add_product_to_draft(actor=vendedor, product_id=prod.pk, quantity=10)
        sale = checkout_sale(
            actor=vendedor,
            draft_id=draft.pk,
            cash_received=Decimal("60.00"),
            idempotency_key=uuid.uuid4(),
        )
        allocs = list(
            SaleLotAllocation.objects.filter(line__sale=sale)
            .select_related("lot")
            .order_by("id")
            .values_list("lot__number", "quantity")
        )
        prod.refresh_from_db()
        shift.refresh_from_db()

        # Check ADMIN / ALMACENERO on product_movements AFTER sale (verify sale unit cost + writeoff receipt link)
        mov_alm_html = c_alm.get(f"/inventario/productos/{prod.pk}/movimientos/").content.decode("utf-8")
        mov_adm_html = c_admin.get(f"/inventario/productos/{prod.pk}/movimientos/").content.decode("utf-8")
        wo_receipt_html = c_alm.get(f"/inventario/bajas/{wo_test.pk}/").content.decode("utf-8")

        # Check ledger closing balance = L-INIT(0) + LoteEspacio(2) + L-LEAP-28(2) + L-VENC-08B(3) = 7
        prod_for_ledger = Product.objects.prefetch_related(
            "lots__initial_line__load",
            "lots__receipt_line__receipt",
            "lots__adjustment_origin",
            "lots__responsible",
            "lots__supplier",
        ).get(pk=prod.pk)
        events, issues = build_ledger(prod_for_ledger)
        # Check DEC-08-KARDEX-COMPRAS filter boundary (minuto inclusivo + page validation + repeated tipo)
        mov_bad_page = c_admin.get(f"/inventario/productos/{prod.pk}/movimientos/?page=0")
        mov_repeat_type = c_admin.get(f"/inventario/productos/{prod.pk}/movimientos/?tipo=entrada&tipo=merma")
        mov_filter_salidas = c_admin.get(f"/inventario/productos/{prod.pk}/movimientos/?tipo=salidas")
        mov_filter_salidas_html = mov_filter_salidas.content.decode("utf-8")

        return {
            "form_unit_cost_probes": form_probes,
            "legacy_zero_cost_writeoff": {
                "writeoff_unit_cost": str(wo_zero.unit_cost),
                "remaining_lot_qty": lot_leg.available_quantity,
                "positive_adj_rejected_with": adj_zero_positive_error,
            },
            "simultaneous_lote_and_producto_get": {
                "status_code": resp_both_params_get.status_code,
                "selected_new_lot_heading_present": "Lote nuevo por ajuste:" in both_html,
                "adjustment_submit_button_present": "Confirmar ajuste" in both_html,
            },
            "new_lot_space_normalization": {
                "saved_number": new_lot_adj.lot.number,
                "normalized": new_lot_adj.lot.number_normalized,
                "adjustment_origin_id": str(new_lot_adj.lot.adjustment_origin_id),
            },
            "leap_year_2028_02_29_saved": leap_adj.lot.expiration_date.isoformat(),
            "route_permission_and_404_matrix": route_checks,
            "vendedor_and_role_cost_visibility": {
                "vendedor_movements_status": mov_ven_status,
                "vendedor_pos_sees_3_cost": "3.0000" in pos_ven_html or "3,0000" in pos_ven_html,
                "almacenero_mov_sees_sale_unit_cost": "Costo unitario de salida:" in mov_alm_html,
                "almacenero_mov_sees_3_0000": "3,0000" in mov_alm_html or "3.0000" in mov_alm_html,
                "admin_mov_sees_Costo_unitario": "Costo unitario de salida:" in mov_adm_html,
                "writeoff_receipt_sees_3_0000": "3,0000" in wo_receipt_html or "3.0000" in wo_receipt_html,
            },
            "sale_fefo_and_cash_shift_invariance": {
                "sale_total": str(sale.total_amount),
                "allocations": [(n, q) for n, q in allocs],
                "expired_lot_allocated": any(n == "L-VENC-08B" for n, _ in allocs),
                "product_physical_stock": sum(l.available_quantity for l in prod.lots.all()),
                "product_sellable_stock": sum(l.available_quantity for l in prod.lots.filter(expiration_date__gt=today)),
                "product_average_cost": str(prod.average_cost),
                "shift_opening_amount": str(shift.opening_amount),
                "shift_sales_count": shift.sales.count(),
                "ledger_closing_balance": events[-1]["balance"] if events else 0,
                "ledger_issues": issues,
                "ledger_row_count": len(events),
            },
            "ledger_query_param_checks": {
                "page_0_status": mov_bad_page.status_code,
                "page_0_has_error": "entero positivo" in mov_bad_page.content.decode("utf-8"),
                "repeated_tipo_status": mov_repeat_type.status_code,
                "repeated_tipo_has_error": "No repita el parámetro tipo." in mov_repeat_type.content.decode("utf-8"),
                "salidas_filter_status": mov_filter_salidas.status_code,
                "salidas_preserves_opening_closing": "Saldo de apertura (UND)" in mov_filter_salidas_html and "Saldo de cierre (UND)" in mov_filter_salidas_html,
            },
        }
    finally:
        from django.db import connections

        connections.close_all()
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    result = {
        "hashes_and_helpers": check_hashes_and_dead_helpers(),
        "django_probes": run_django_probes(),
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
