"""Stage 08 pre-fix reproduction script (SQLite isolated + real PostgreSQL 18.4 concurrency).
Verifies exact current defects before any source edits in r1-pmv/.
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
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone as dt_timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
SUPPORT = Path(__file__).resolve().parent
BIN = Path("C:/Program Files/PostgreSQL/18/bin")


def pg_worker() -> int:
    pw = os.environ["AUDIT08_REPRO_PG_PW"]
    db = os.environ["AUDIT08_REPRO_PG_DB"]
    port = int(os.environ["AUDIT08_REPRO_PG_PORT"])
    out_file = Path(os.environ["AUDIT08_REPRO_PG_OUT"])

    sys.path.insert(0, str(APP))
    os.environ.update(
        APP_ENV="test",
        DJANGO_DEBUG="false",
        DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
        DJANGO_SETTINGS_MODULE="config.settings",
    )
    from config import env

    loader = env.load_dotenv
    env.load_dotenv = lambda path=None: None
    from django.conf import settings

    settings.DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db,
            "USER": "audit08r",
            "PASSWORD": pw,
            "HOST": "127.0.0.1",
            "PORT": port,
            "CONN_MAX_AGE": 0,
            "OPTIONS": {"options": "-c statement_timeout=15000 -c lock_timeout=10000"},
        }
    }
    settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
    env.load_dotenv = loader

    import django

    django.setup()

    from django.core.exceptions import ValidationError
    from django.core.management import call_command
    from django.db import close_old_connections, connections
    from django.test import Client
    from django.utils import timezone as tz
    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.models import Lot, StockWriteOff
    from inventory.services import LotInput, confirm_initial_load, write_off_stock

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    r_adm = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    r_wh = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    Role.objects.create(code=Role.Code.SELLER, name="Vendedor")
    user_pw = "Repro08#Pass123"
    pg_adm = Account.objects.create_user("pgadm@repro.invalid", user_pw, display_name="PG Adm", role=r_adm)
    pg_wh = Account.objects.create_user("pgwh@repro.invalid", user_pw, display_name="PG WH", role=r_wh)
    pg_cat = Category.objects.create(name="PG Repro Cat")
    future = tz.localdate() + timedelta(days=60)

    lots_distinct = []
    for i in range(8):
        pr = Product.objects.create(category=pg_cat, name=f"PG Corr {i}", barcode=f"7750888{i:05d}", sale_price=Decimal("4.00"))
        ld = confirm_initial_load(actor=pg_wh, product=pr, lots=[LotInput(f"PG-C-{i}", 10, Decimal("2.00"), future)])
        lots_distinct.append(ld.lots.get())

    bar_corr = threading.Barrier(8, timeout=10)

    def worker_corr(l_obj):
        close_old_connections()
        try:
            bar_corr.wait()
            wo = write_off_stock(actor=pg_wh, lot=l_obj, quantity=1, reason="VENCIMIENTO")
            return {"status": "ok", "correlativo": wo.correlativo}
        except ValidationError as exc:
            return {"status": "failed", "messages": exc.messages}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=8) as pool:
        corr_results = [f.result() for f in [pool.submit(worker_corr, l) for l in lots_distinct]]

    p_dbl = Product.objects.create(category=pg_cat, name="PG Dbl HTTP", barcode="775088899999", sale_price=Decimal("5.00"))
    lot_dbl = confirm_initial_load(actor=pg_wh, product=p_dbl, lots=[LotInput("PG-DBL-1", 20, Decimal("2.00"), future)]).lots.get()
    c_pg1 = Client(enforce_csrf_checks=True)
    c_pg1.force_login(pg_adm)
    csrf_pg = c_pg1.get(f"/inventario/bajas/nueva/?lote={lot_dbl.pk}").cookies["csrftoken"].value
    sess_cookie = c_pg1.cookies["sessionid"].value
    idem_uuid = str(uuid.uuid4())
    bar_http = threading.Barrier(2, timeout=10)

    def worker_http_dbl():
        close_old_connections()
        try:
            cl = Client(enforce_csrf_checks=True)
            cl.cookies["sessionid"] = sess_cookie
            cl.cookies["csrftoken"] = csrf_pg
            bar_http.wait()
            resp = cl.post(
                f"/inventario/bajas/nueva/?lote={lot_dbl.pk}",
                data={
                    "lot_id": str(lot_dbl.pk),
                    "quantity": "3",
                    "reason": "DAÑO",
                    "notes": "Concurrent dbl",
                    "idempotency_key": idem_uuid,
                    "csrfmiddlewaretoken": csrf_pg,
                },
            )
            return {"status": resp.status_code, "location": resp.get("Location")}
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1, f2 = pool.submit(worker_http_dbl), pool.submit(worker_http_dbl)
        dbl_http_results = [f1.result(), f2.result()]

    res = {
        "correlativo_8_threads_ok_count": sum(1 for r in corr_results if r["status"] == "ok"),
        "correlativo_8_threads_failed_count": sum(1 for r in corr_results if r["status"] == "failed"),
        "correlativo_8_threads_results": corr_results,
        "concurrent_same_session_writeoffs_created": StockWriteOff.objects.filter(lot=lot_dbl).count(),
        "concurrent_same_session_lot_remaining": Lot.objects.get(pk=lot_dbl.pk).available_quantity,
        "concurrent_http_results": dbl_http_results,
    }
    connections.close_all()
    out_file.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


def digest(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main() -> int:
    if "--pg-worker" in sys.argv:
        return pg_worker()

    stamp = datetime.now(dt_timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    protected = [
        *APP.glob("*.sqlite3"),
        *(RESULTS / "datos").rglob("*.sqlite3"),
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]
    start_hashes = {str(p.relative_to(ROOT)): digest(p) for p in protected}

    run_dir = RESULTS / "datos" / f"etapa08-repro-{stamp}-{secrets.token_hex(4)}"
    out_dir = RESULTS / "evidencias" / f"08-repro-{stamp}"
    run_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    (run_dir / "marker.json").write_text(json.dumps({"run": run_dir.name, "created_utc": stamp}), encoding="utf-8")
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")

    os.environ.update(
        AUDIT08_RUN_DIR=str(run_dir),
        AUDIT08_OUT=str(out_dir),
        AUDIT08_DEFAULT_COOKIES="1",
        DJANGO_SETTINGS_MODULE="audit08_settings",
    )
    sys.path.insert(0, str(APP))
    sys.path.insert(0, str(SUPPORT))

    import django

    django.setup()

    from django.contrib.auth.models import AnonymousUser
    from django.core.management import call_command
    from django.test import Client
    from django.urls import get_resolver
    from django.utils import timezone as tz

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    from cash.models import CashRegister, CashShift
    from catalog.models import Category, Product
    from catalog.services import update_product
    from identity.models import Account, Role
    from inventory.forms import PhysicalAdjustmentForm, StockWriteOffForm
    from inventory.models import Lot
    from inventory.services import LotInput, confirm_initial_load, register_physical_adjustment, write_off_stock
    from sales.services import add_product_to_draft, checkout_sale

    admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    pw = "Repro08#Pass123"
    admin = Account.objects.create_user("adm@repro08.invalid", pw, display_name="Admin Repro", role=admin_role)
    wh = Account.objects.create_user("wh@repro08.invalid", pw, display_name="WH Repro", role=wh_role)
    wh_stale = Account.objects.create_user("wh_stale@repro08.invalid", pw, display_name="WH Stale", role=wh_role)
    adm_stale = Account.objects.create_user("adm_stale@repro08.invalid", pw, display_name="ADM Stale", role=admin_role)
    seller = Account.objects.create_user("sel@repro08.invalid", pw, display_name="Seller Repro", role=seller_role)

    cat = Category.objects.create(name="Cat Repro 08")
    today = tz.localdate()
    future = today + timedelta(days=60)

    p1 = Product.objects.create(category=cat, name="Producto Repro 08", barcode="775080000001", sale_price=Decimal("8.00"))
    load1 = confirm_initial_load(actor=wh, product=p1, lots=[LotInput("L-REPRO-1", 50, Decimal("2.0000"), future)])
    lot1 = load1.lots.get()

    report = {"stamp_utc": stamp, "findings": {}, "planning_gaps": {}}

    c_adm = Client(enforce_csrf_checks=True)
    c_adm.force_login(admin)
    c_adm_noexc = Client(enforce_csrf_checks=True, raise_request_exception=False)
    c_adm_noexc.force_login(admin)

    tok_wo = c_adm.get(f"/inventario/bajas/nueva/?lote={lot1.pk}").cookies["csrftoken"].value
    r_wo_empty = c_adm.post(f"/inventario/bajas/nueva/?lote={lot1.pk}", data={}, HTTP_X_CSRFTOKEN=tok_wo)
    body_wo_empty = r_wo_empty.content.decode()

    tok_wo_noparam = c_adm_noexc.get(f"/inventario/bajas/nueva/?lote={lot1.pk}").cookies["csrftoken"].value
    r_wo_empty_noparam = c_adm_noexc.post("/inventario/bajas/nueva/", data={}, HTTP_X_CSRFTOKEN=tok_wo_noparam)

    tok_adj = c_adm.get(f"/inventario/ajustes/nuevo/?lote={lot1.pk}").cookies["csrftoken"].value
    r_adj_empty = c_adm.post(f"/inventario/ajustes/nuevo/?lote={lot1.pk}", data={}, HTTP_X_CSRFTOKEN=tok_adj)
    body_adj_empty = r_adj_empty.content.decode()
    r_adj_empty_noparam = c_adm_noexc.post("/inventario/ajustes/nuevo/", data={}, HTTP_X_CSRFTOKEN=tok_wo_noparam)

    report["findings"]["def08_01_empty_post_unbound"] = {
        "wo_with_lote_status": r_wo_empty.status_code,
        "wo_with_lote_has_error_ui": ("text-danger" in body_wo_empty or "alert-danger" in body_wo_empty),
        "wo_no_lote_status": r_wo_empty_noparam.status_code,
        "adj_with_lote_status": r_adj_empty.status_code,
        "adj_with_lote_has_error_ui": ("text-danger" in body_adj_empty or "alert-danger" in body_adj_empty),
        "adj_no_lote_status": r_adj_empty_noparam.status_code,
    }

    def capture_exc(fn):
        try:
            res = fn()
            return {"ok": True, "res": str(res)}
        except Exception as exc:
            return {"ok": False, "exc_type": type(exc).__name__, "message": str(exc)}

    Account.objects.filter(pk=wh_stale.pk).update(is_active=False)
    Account.objects.filter(pk=adm_stale.pk).update(is_active=False, role=seller_role)

    report["findings"]["def08_02_actor_and_lot_guards"] = {
        "wo_anonymous": capture_exc(lambda: write_off_stock(actor=AnonymousUser(), lot=lot1, quantity=1, reason="VENCIMIENTO")),
        "adj_anonymous": capture_exc(lambda: register_physical_adjustment(actor=AnonymousUser(), lot=lot1, delta=1, reason="Test")),
        "wo_stale_inactive_actor": capture_exc(lambda: write_off_stock(actor=wh_stale, lot=lot1, quantity=1, reason="VENCIMIENTO")),
        "adj_stale_demoted_inactive_actor": capture_exc(lambda: register_physical_adjustment(actor=adm_stale, lot=lot1, delta=1, reason="Stale")),
        "wo_missing_lot": capture_exc(lambda: write_off_stock(actor=wh, lot=Lot(id=uuid.uuid4(), product=p1), quantity=1, reason="VENCIMIENTO")),
        "adj_missing_lot": capture_exc(lambda: register_physical_adjustment(actor=admin, lot=Lot(id=uuid.uuid4(), product=p1), delta=1, reason="Missing")),
    }
    lot1.refresh_from_db()

    f_wo_arabic = StockWriteOffForm(data={"lot_id": str(lot1.pk), "quantity": "٥", "reason": "VENCIMIENTO", "notes": ""})
    f_adj_arabic = PhysicalAdjustmentForm(data={"lot_id": str(lot1.pk), "delta": "٥", "reason": "Conteo"})
    f_adj_plus = PhysicalAdjustmentForm(data={"lot_id": str(lot1.pk), "delta": "+10", "reason": "Conteo con +"})
    f_wo_bad = StockWriteOffForm(data={"lot_id": str(lot1.pk), "quantity": "", "reason": "BAD", "notes": ""})
    f_adj_bad = PhysicalAdjustmentForm(data={"lot_id": str(lot1.pk), "delta": "", "reason": "   "})

    report["findings"]["def08_03_validation_gaps"] = {
        "wo_bool_quantity_true": capture_exc(lambda: write_off_stock(actor=wh, lot=lot1, quantity=True, reason="VENCIMIENTO")),
        "adj_bool_delta_true": capture_exc(lambda: register_physical_adjustment(actor=admin, lot=lot1, delta=True, reason="Bool true")),
        "adj_reason_350_chars_in_service": capture_exc(lambda: register_physical_adjustment(actor=admin, lot=lot1, delta=1, reason="A" * 350)),
        "wo_nul_in_notes_service": capture_exc(lambda: write_off_stock(actor=wh, lot=lot1, quantity=1, reason="DAÑO", notes="abc\x00def")),
        "adj_nul_in_reason_service": capture_exc(lambda: register_physical_adjustment(actor=admin, lot=lot1, delta=1, reason="abc\x00def")),
        "form_wo_arabic_valid": f_wo_arabic.is_valid(),
        "form_wo_arabic_cleaned": f_wo_arabic.cleaned_data.get("quantity") if f_wo_arabic.is_valid() else None,
        "form_adj_arabic_valid": f_adj_arabic.is_valid(),
        "form_adj_arabic_cleaned": f_adj_arabic.cleaned_data.get("delta") if f_adj_arabic.is_valid() else None,
        "form_adj_plus10_valid": f_adj_plus.is_valid(),
        "form_wo_empty_errors": {k: list(v) for k, v in f_wo_bad.errors.items()},
        "form_adj_empty_errors": {k: list(v) for k, v in f_adj_bad.errors.items()},
    }
    lot1.refresh_from_db()

    reused_key = str(uuid.uuid4())
    qty_before = lot1.available_quantity
    tok_id = c_adm.get(f"/inventario/bajas/nueva/?lote={lot1.pk}").cookies["csrftoken"].value
    r_id1 = c_adm.post(
        f"/inventario/bajas/nueva/?lote={lot1.pk}",
        data={"lot_id": str(lot1.pk), "quantity": "1", "reason": "VENCIMIENTO", "notes": "", "idempotency_key": reused_key, "csrfmiddlewaretoken": tok_id},
    )
    tok_id2 = c_adm.get(f"/inventario/bajas/nueva/?lote={lot1.pk}").cookies["csrftoken"].value
    r_id2_tampered = c_adm.post(
        f"/inventario/bajas/nueva/?lote={lot1.pk}",
        data={"lot_id": str(lot1.pk), "quantity": "9", "reason": "DAÑO", "notes": "Otra cosa", "idempotency_key": reused_key, "csrfmiddlewaretoken": tok_id2},
        follow=True,
    )
    lot1.refresh_from_db()
    report["findings"]["def08_05_cross_payload_idempotency_reuse"] = {
        "first_status": r_id1.status_code,
        "second_tampered_final_status": r_id2_tampered.status_code,
        "second_tampered_body_has_ya_registrada": "ya fue registrada anteriormente" in r_id2_tampered.content.decode(),
        "lot_qty_before": qty_before,
        "lot_qty_after": lot1.available_quantity,
    }

    reg = CashRegister.objects.create(code="CAJA-REPRO08")
    CashShift.objects.create(cash_register=reg, seller=seller, opening_amount=Decimal("20.00"))
    p_orig = Product.objects.create(category=cat, name="Producto Original OldBC", barcode="775080000099", sale_price=Decimal("5.00"))
    confirm_initial_load(actor=wh, product=p_orig, lots=[LotInput("L-OLD-1", 5, Decimal("2.0000"), future)])
    draft = add_product_to_draft(actor=seller, product_id=p_orig.pk, quantity=1)
    sale_orig = checkout_sale(actor=seller, draft_id=draft.pk, cash_received=Decimal("10.00"), idempotency_key=uuid.uuid4())
    update_product(actor=admin, product=p_orig, name=p_orig.name, barcode="775080000199", sale_price=p_orig.sale_price, minimum_stock=p_orig.minimum_stock)
    p_new_reused = Product.objects.create(category=cat, name="Producto Nuevo ReusoBC", barcode="775080000099", sale_price=Decimal("6.00"))
    mov_new = c_adm.get(f"/inventario/productos/{p_new_reused.pk}/movimientos/")
    report["findings"]["def08_06_cross_product_saleline_leak"] = {
        "leaks_orig_sale_correlative": sale_orig.correlative in mov_new.content.decode(),
        "sale_correlative": sale_orig.correlative,
    }

    all_url_names = [u for u in get_resolver().reverse_dict.keys() if isinstance(u, str)]
    report["planning_gaps"] = {
        "writeoff_receipt_url_exists": any("constancia" in u or "receipt" in u for u in all_url_names if "writeoff" in u or "baja" in u),
        "writeoff_history_url_exists": any("baja" in u and "hist" in u for u in all_url_names),
        "adjustment_history_url_exists": any("ajust" in u and "hist" in u for u in all_url_names),
        "all_inventory_routes": sorted([u for u in all_url_names if u in ("stock-writeoff", "physical-adjustment", "product-movements", "stock-overview", "inventory-load", "stock-entry", "supplier-list", "supplier-create")]),
        "movements_has_running_balance": "saldo" in c_adm.get(f"/inventario/productos/{p1.pk}/movimientos/").content.decode().lower(),
        "movements_has_filters": "<form" in c_adm.get(f"/inventario/productos/{p1.pk}/movimientos/").content.decode().lower(),
    }

    pg_cluster = (Path(tempfile.gettempdir()) / ("audit08-repro-pg-" + secrets.token_hex(10))).resolve()
    pg_cluster.mkdir(exist_ok=False)
    pg_data = pg_cluster / "data"
    pg_pw = secrets.token_urlsafe(36)
    pg_pwfile = pg_cluster / "pw"
    pg_pwfile.write_text(pg_pw, encoding="utf-8")
    pg_db = "audit08_repro_" + secrets.token_hex(4)
    pg_out = out_dir / "repro_pg.json"
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        pg_port = s.getsockname()[1]

    def pg_cmd(exe: str, *args):
        subprocess.run([str(BIN / f"{exe}.exe"), *map(str, args)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW, timeout=40)

    pg_started = False
    try:
        pg_cmd("initdb", "-D", str(pg_data), "-U", "audit08r", "--pwfile", str(pg_pwfile), "--auth-host=scram-sha-256", "--auth-local=scram-sha-256", "--encoding=UTF8", "--locale=C")
        pg_pwfile.unlink()
        pg_cmd("pg_ctl", "-D", str(pg_data), "-l", str(pg_cluster / "pg.log"), "-o", f"-h 127.0.0.1 -p {pg_port} -c log_statement=none", "-w", "start")
        pg_started = True
        import psycopg
        from psycopg import sql

        with psycopg.connect(host="127.0.0.1", port=pg_port, user="audit08r", password=pg_pw, dbname="postgres", autocommit=True) as conn:
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(pg_db)))

        env_child = os.environ.copy()
        env_child.update(
            AUDIT08_REPRO_PG_PW=pg_pw,
            AUDIT08_REPRO_PG_DB=pg_db,
            AUDIT08_REPRO_PG_PORT=str(pg_port),
            AUDIT08_REPRO_PG_OUT=str(pg_out),
        )
        subprocess.run([sys.executable, __file__, "--pg-worker"], env=env_child, check=True, timeout=60)
        report["findings"]["def08_04_and_05_pg_concurrency"] = json.loads(pg_out.read_text(encoding="utf-8"))
    finally:
        if pg_started:
            pg_cmd("pg_ctl", "-D", str(pg_data), "-m", "fast", "-w", "stop")

    end_hashes = {str(p.relative_to(ROOT)): digest(p) for p in protected}
    report["protected_unchanged"] = all(start_hashes[k] == end_hashes[k] for k in start_hashes)
    (out_dir / "repro.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
