"""Deepening checks for Stage 04 on the current build (2026-11-14):
- Phase sqlite (isolated audit04_settings):
  * /admin/ technical portal inspection (RN-29/DOC-01-06 roles + Supplier/Lot/StockReceipt registration)
  * Dashboard / & sidebar navigation per role after 16:33 identity/authorization.py updates
  * Inactive/demoted session enforcement on supplier routes
  * StockReceipt idempotency replay after supplier deactivation & divergent content rejection
  * Sentinel re-submission (__inactive__:<uuid>, unknown UUID, invalid string) + #initial-load-errors asymmetry
  * ORM bypass (.create without full_clean) & ProtectedError on supplier deletion
- Phase postgres (ephemeral PostgreSQL 18.4 owned cluster):
  * Full migrations & real pg_constraint / pg_indexes inspection on Supplier/Lot/StockReceipt/InitialInventoryLoad
  * Raw SQL insert bypassing format checks (confirming 0 SQL CHECK constraints on ruc/name/phone)
  * Raw SQL duplicate RUC IntegrityError & FK violation on referenced supplier delete
Preserves r1_pmv.sqlite3 and all previous Stage 04 artifacts untouched.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
SUPPORT = Path(__file__).resolve().parent
PG_BIN = Path("C:/Program Files/PostgreSQL/18/bin")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_r1_pmv_fingerprint() -> dict:
    exts = {".py", ".html", ".css", ".js", ".svg"}
    h = hashlib.sha256()
    count = 0
    for p in sorted(APP.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(APP).as_posix()
        if any(part in {".venv", "__pycache__", ".git"} for part in p.parts):
            continue
        if p.suffix.lower() not in exts:
            continue
        count += 1
        h.update(rel.encode("utf-8"))
        h.update(b"\x00")
        h.update(sha256_file(p).encode("ascii"))
        h.update(b"\n")
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    return {"git_head": head, "file_count": count, "sha256": h.hexdigest()}


def snapshot_protected(exclude_dir: Path | None = None) -> dict[str, str | None]:
    targets = [
        APP / "r1_pmv.sqlite3",
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
        ROOT / "08_Historias_de_Usuario.md",
    ]
    datos = RESULTS / "datos"
    if datos.exists():
        for db in sorted(datos.glob("etapa04-*/audit.sqlite3")):
            if exclude_dir is not None and db.parent.resolve() == exclude_dir.resolve():
                continue
            targets.append(db)
    return {
        str(p.relative_to(ROOT)).replace("\\", "/"): sha256_file(p) if p.exists() else None
        for p in targets
    }


def run_phase_sqlite(run_dir_str: str) -> dict:
    sys.path.insert(0, str(APP))
    sys.path.insert(0, str(SUPPORT))
    os.environ["AUDIT04_RUN_DIR"] = run_dir_str
    os.environ["DJANGO_SETTINGS_MODULE"] = "audit04_settings"
    import django

    django.setup()

    from django.contrib import admin
    from django.core.exceptions import ValidationError
    from django.core.management import call_command
    from django.db.models import ProtectedError
    from django.test import Client
    from django.utils import timezone as tz

    from catalog.models import Category, Product
    from identity.models import Account, Role
    from inventory.models import InitialInventoryLoad, Lot, StockReceipt, Supplier
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        create_supplier,
        register_stock_entry,
        toggle_supplier_status,
    )

    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        call_command("migrate", interactive=False, verbosity=0)

    admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
    wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
    seller_role = Role.objects.create(code=Role.Code.SELLER, name="Vendedor")

    creds = {}
    users = {}
    for key, email, display, role, staff, superuser in [
        ("admin", "admin@deep04.invalid", "Admin Deep04", admin_role, False, False),
        ("admin_rev", "adminrev@deep04.invalid", "Admin Revocable", admin_role, False, False),
        ("warehouse", "wh@deep04.invalid", "Almacenero Deep04", wh_role, False, False),
        ("seller", "seller@deep04.invalid", "Vendedor Deep04", seller_role, False, False),
        ("superuser", "techsuper@deep04.invalid", "Superuser Tech", admin_role, True, True),
    ]:
        pw = secrets.token_urlsafe(18) + "A1!"
        creds[key] = {"email": email, "password": pw}
        users[key] = Account.objects.create_user(
            email,
            pw,
            display_name=display,
            role=role,
            is_staff=staff,
            is_superuser=superuser,
        )

    cat = Category.objects.create(name="Bebidas Deep04")
    p_init = Product.objects.create(
        category=cat,
        name="Agua Mineral 625ml",
        barcode="775049900001",
        sale_price=Decimal("2.50"),
    )
    p_sub = Product.objects.create(
        category=cat,
        name="Gaseosa Cola 1.5L",
        barcode="775049900002",
        sale_price=Decimal("6.50"),
    )
    soon = tz.localdate() + timedelta(days=30)
    future = tz.localdate() + timedelta(days=90)
    base_load = confirm_initial_load(
        actor=users["warehouse"],
        product=p_sub,
        lots=[LotInput("L-BASE-DEEP", 10, Decimal("4.0000"), soon)],
    )

    def make_client(key: str | None = None) -> Client:
        c = Client(HTTP_HOST="127.0.0.1")
        if key is not None:
            ok = c.login(email=creds[key]["email"], password=creds[key]["password"])
            assert ok, f"Failed login for {key}"
        return c

    # (a) /admin/ technical portal inspection
    registry_info = {
        "supplier_registered": Supplier in admin.site._registry,
        "stockreceipt_registered": StockReceipt in admin.site._registry,
        "lot_registered": Lot in admin.site._registry,
        "initialload_registered": InitialInventoryLoad in admin.site._registry,
        "lot_admin_list_display": list(admin.site._registry[Lot].list_display) if Lot in admin.site._registry else None,
        "initialload_admin_list_display": list(admin.site._registry[InitialInventoryLoad].list_display)
        if InitialInventoryLoad in admin.site._registry
        else None,
    }
    admin_routes = [
        "/admin/",
        "/admin/login/",
        "/admin/inventory/",
        "/admin/inventory/supplier/",
        "/admin/inventory/lot/",
        "/admin/inventory/stockreceipt/",
        "/admin/inventory/initialinventoryload/",
        f"/admin/inventory/initialinventoryload/{base_load.pk}/change/",
    ]
    admin_access = {}
    for role_key in [None, "seller", "warehouse", "admin", "superuser"]:
        c = make_client(role_key)
        per_route = {}
        for route in admin_routes:
            resp = c.get(route)
            per_route[route] = {
                "status": resp.status_code,
                "location": resp.headers.get("Location", ""),
            }
        # Also test POST /admin/login/ with non-staff commercial ADMIN credentials
        if role_key == "admin":
            c.get("/admin/login/")
            post_login = c.post(
                "/admin/login/",
                {"username": creds["admin"]["email"], "password": creds["admin"]["password"], "next": "/admin/"},
            )
            per_route["POST_/admin/login/_commercial_admin"] = {
                "status": post_login.status_code,
                "rejected_non_staff": post_login.status_code == 200
                and ("staff" in post_login.content.decode("utf-8").lower() or "administración" in post_login.content.decode("utf-8").lower()),
            }
        admin_access[role_key or "anonymous"] = per_route

    c_su = make_client("superuser")
    lot_admin_html = c_su.get("/admin/inventory/lot/").content.decode("utf-8")
    load_change_html = c_su.get(f"/admin/inventory/initialinventoryload/{base_load.pk}/change/").content.decode("utf-8")
    admin_lot_has_supplier_col = ("Proveedor" in lot_admin_html) or ("supplier" in lot_admin_html.lower())
    admin_load_change_has_supplier = ("supplier" in load_change_html.lower()) or ("proveedor" in load_change_html.lower())

    # (b) Dashboard /inicio/ & sidebar navigation + 16:33 identity/authorization enforcement
    nav_checks = {}
    for role_key in ["admin", "warehouse", "seller"]:
        c = make_client(role_key)
        dash = c.get("/inicio/")
        html = dash.content.decode("utf-8")
        aside_match = re.search(r"<aside[^>]*>(.*?)</aside>", html, re.S)
        main_match = re.search(r'<main[^>]*id="contenido"[^>]*>(.*?)</main>', html, re.S)
        aside_hrefs = re.findall(r'href="([^"]+)"', aside_match.group(1)) if aside_match else []
        main_hrefs = re.findall(r'href="([^"]+)"', main_match.group(1)) if main_match else []
        hrefs = re.findall(r'href="([^"]+)"', html)
        nav_checks[role_key] = {
            "dashboard_status": dash.status_code,
            "sidebar_has_proveedores_link": "/inventario/proveedores/" in aside_hrefs,
            "sidebar_has_proveedores_nuevo_link": "/inventario/proveedores/nuevo/" in aside_hrefs,
            "dashboard_main_has_proveedores_card": "/inventario/proveedores/" in main_hrefs,
            "dashboard_main_has_proveedores_nuevo_card": "/inventario/proveedores/nuevo/" in main_hrefs,
            "sidebar_hrefs": aside_hrefs,
            "dashboard_main_hrefs": main_hrefs,
            "has_proveedores_link": "/inventario/proveedores/" in hrefs,
            "has_proveedores_nuevo_link": "/inventario/proveedores/nuevo/" in hrefs,
            "has_stock_link": "/inventario/stock/" in hrefs,
            "has_entrada_link": "/inventario/entrada/" in hrefs,
            "has_carga_inicial_link": "/inventario/carga-inicial/" in hrefs,
            "proveedores_link_count": hrefs.count("/inventario/proveedores/"),
        }

    # Check 403 exact text from 16:33 identity/authorization.py on Stage 04 routes
    c_seller = make_client("seller")
    r_sel_list = c_seller.get("/inventario/proveedores/")
    r_sel_new = c_seller.get("/inventario/proveedores/nuevo/")
    c_wh = make_client("warehouse")
    r_wh_new = c_wh.get("/inventario/proveedores/nuevo/")
    r_wh_post = c_wh.post("/inventario/proveedores/nuevo/", {"name": "Blocked SAC", "ruc": "20444555666", "phone": ""})

    s1 = create_supplier(actor=users["admin"], name="Proveedor Idempotente SAC", ruc="20111222333", phone="999111222")
    r_wh_toggle = c_wh.post(f"/inventario/proveedores/{s1.pk}/estado/")

    # Session revocation & role demotion with active cookies
    c_rev = make_client("admin_rev")
    assert c_rev.get("/inventario/proveedores/").status_code == 200
    Account.objects.filter(pk=users["admin_rev"].pk).update(is_active=False)
    r_rev_get = c_rev.get("/inventario/proveedores/")
    r_rev_post = c_rev.post("/inventario/proveedores/nuevo/", {"name": "Ghost Admin SAC", "ruc": "20777888999", "phone": ""})
    # Re-enable and demote to SELLER while keeping session authenticated via fresh login
    Account.objects.filter(pk=users["admin_rev"].pk).update(is_active=True)
    c_dem = make_client("admin_rev")
    assert c_dem.get("/inventario/proveedores/").status_code == 200
    Account.objects.filter(pk=users["admin_rev"].pk).update(role=seller_role)
    r_dem_post = c_dem.post("/inventario/proveedores/nuevo/", {"name": "Demoted SAC", "ruc": "20777888998", "phone": ""})

    sel_body = r_sel_list.content.decode("utf-8")
    wh_body = r_wh_post.content.decode("utf-8")
    dem_body = r_dem_post.content.decode("utf-8")
    auth_1633 = {
        "seller_list_status": r_sel_list.status_code,
        "seller_list_msg": "No tiene permiso para esta operación." in sel_body,
        "seller_list_body_preview": sel_body[:300],
        "seller_create_status": r_sel_new.status_code,
        "warehouse_create_get_status": r_wh_new.status_code,
        "warehouse_create_post_status": r_wh_post.status_code,
        "warehouse_create_post_msg": "No tiene permiso para esta operación." in wh_body,
        "warehouse_toggle_status": r_wh_toggle.status_code,
        "inactive_admin_get_status": r_rev_get.status_code,
        "inactive_admin_get_location": r_rev_get.headers.get("Location", ""),
        "inactive_admin_post_status": r_rev_post.status_code,
        "inactive_admin_post_location": r_rev_post.headers.get("Location", ""),
        "ghost_supplier_exists": Supplier.objects.filter(ruc="20777888999").exists(),
        "demoted_admin_post_status": r_dem_post.status_code,
        "demoted_admin_post_msg": "No tiene permiso para esta operación." in dem_body,
        "demoted_supplier_exists": Supplier.objects.filter(ruc="20777888998").exists(),
    }

    # (c) StockReceipt idempotent replay AFTER supplier deactivation + negative tampering + UI error summary asymmetry
    c_wh = make_client("warehouse")
    k1 = str(uuid.uuid4())
    entry_payload = {
        "idempotency_key": k1,
        "product": str(p_sub.pk),
        "supplier": str(s1.pk),
        "lots-TOTAL_FORMS": "1",
        "lots-INITIAL_FORMS": "0",
        "lots-MIN_NUM_FORMS": "1",
        "lots-MAX_NUM_FORMS": "1000",
        "lots-0-number": "L-REC-01",
        "lots-0-quantity": "10",
        "lots-0-unit_cost": "8.0000",
        "lots-0-expiration_date": future.isoformat(),
    }
    r_ent1 = c_wh.post("/inventario/entrada/", entry_payload)
    receipt_count_after_1 = StockReceipt.objects.count()
    first_receipt = StockReceipt.objects.get(idempotency_key=k1)

    # Admin deactivates S1
    toggle_supplier_status(actor=users["admin"], supplier=s1, is_active=False)
    s1.refresh_from_db()

    # Exact replay with same idempotency_key K1 after S1 is inactive
    r_replay_same = c_wh.post("/inventario/entrada/", entry_payload)
    receipt_count_after_replay = StockReceipt.objects.count()
    lot_count_after_replay = Lot.objects.filter(product=p_sub).count()

    # Divergent replay with same K1 (quantity changed 10 -> 12)
    div_payload = {**entry_payload, "lots-0-quantity": "12"}
    r_replay_div = c_wh.post("/inventario/entrada/", div_payload)
    div_html = r_replay_div.content.decode("utf-8")

    # New key K2 referencing inactive S1
    k2 = str(uuid.uuid4())
    inact_payload = {**entry_payload, "idempotency_key": k2, "lots-0-number": "L-REC-02"}
    r_inact = c_wh.post("/inventario/entrada/", inact_payload)
    inact_html = r_inact.content.decode("utf-8")

    # Resubmit __inactive__:<uuid> sentinel verbatim on stock-entry
    r_sentinel_resubmit = c_wh.post("/inventario/entrada/", {**inact_payload, "supplier": f"__inactive__:{s1.pk}"})
    sentinel_resubmit_html = r_sentinel_resubmit.content.decode("utf-8")

    # Tampered nonexistent UUID & non-UUID on stock-entry and initial-load
    missing_uuid = "00000000-0000-4000-8000-000000000099"
    r_missing_entry = c_wh.post("/inventario/entrada/", {**inact_payload, "supplier": missing_uuid})
    r_invalid_entry = c_wh.post("/inventario/entrada/", {**inact_payload, "supplier": "not-a-uuid"})
    r_missing_init = c_wh.post(
        "/inventario/carga-inicial/",
        {
            "product": str(p_init.pk),
            "supplier": missing_uuid,
            "lots-TOTAL_FORMS": "1",
            "lots-INITIAL_FORMS": "0",
            "lots-MIN_NUM_FORMS": "1",
            "lots-MAX_NUM_FORMS": "1000",
            "lots-0-number": "L-INIT-01",
            "lots-0-quantity": "5",
            "lots-0-unit_cost": "1.5000",
            "lots-0-expiration_date": future.isoformat(),
        },
    )
    init_err_html = r_missing_init.content.decode("utf-8")

    idempotency_and_tamper = {
        "first_entry_status": r_ent1.status_code,
        "first_entry_location": r_ent1.headers.get("Location", ""),
        "receipt_count_after_1": receipt_count_after_1,
        "replay_same_status": r_replay_same.status_code,
        "replay_same_location": r_replay_same.headers.get("Location", ""),
        "replay_redirects_to_same_receipt": r_replay_same.headers.get("Location", "") == f"/inventario/recepciones/{first_receipt.pk}/",
        "receipt_count_after_replay": receipt_count_after_replay,
        "lot_count_after_replay": lot_count_after_replay,
        "replay_divergent_status": r_replay_div.status_code,
        "replay_divergent_msg": "La clave de recepción ya fue utilizada con otro contenido o responsable." in div_html,
        "new_key_inactive_supplier_status": r_inact.status_code,
        "new_key_inactive_sentinel_rendered": f'value="__inactive__:{s1.pk}"' in inact_html,
        "sentinel_resubmit_status": r_sentinel_resubmit.status_code,
        "sentinel_resubmit_still_rejected_and_preserved": (
            r_sentinel_resubmit.status_code == 200
            and f'value="__inactive__:{s1.pk}"' in sentinel_resubmit_html
        ),
        "missing_uuid_entry_status": r_missing_entry.status_code,
        "missing_uuid_entry_sentinel": 'value="__unavailable__"' in r_missing_entry.content.decode("utf-8"),
        "invalid_str_entry_status": r_invalid_entry.status_code,
        "invalid_str_entry_sentinel": 'value="__invalid_supplier__"' in r_invalid_entry.content.decode("utf-8"),
        "missing_uuid_init_status": r_missing_init.status_code,
        "missing_uuid_init_sentinel": 'value="__unavailable__"' in init_err_html,
        "ui_error_summary_initial_load_has_top_box": 'id="initial-load-errors"' in init_err_html,
        "ui_error_summary_stock_entry_has_top_box": 'id="initial-load-errors"' in inact_html or 'role="alert"' in inact_html,
        "final_receipt_count": StockReceipt.objects.count(),
        "final_initial_load_count": InitialInventoryLoad.objects.count(),
    }

    # (d) ORM bypass & PROTECT behavior
    raw_bad = Supplier.objects.create(name="---", ruc="BAD1", phone="abc")
    raw_bad_ruc = Supplier.objects.create(name="Valid SAC", ruc="BAD2", phone="")
    raw_bad_phone = Supplier.objects.create(name="Valid SAC", ruc="20999888777", phone="abc")
    full_clean_fields: dict[str, list[str]] = {}
    for label, obj in [("bad_all", raw_bad), ("bad_ruc", raw_bad_ruc), ("bad_phone", raw_bad_phone)]:
        try:
            obj.full_clean(validate_unique=False)
            full_clean_fields[label] = []
        except ValidationError as exc:
            full_clean_fields[label] = sorted(exc.message_dict.keys())
        obj.delete()

    try:
        s1.delete()
        protected_blocked_delete = False
    except ProtectedError:
        protected_blocked_delete = True

    orm_checks = {
        "orm_create_without_full_clean_succeeded": True,
        "full_clean_rejected_fields": full_clean_fields,
        "protected_error_on_linked_supplier_delete": protected_blocked_delete,
        "s1_still_exists_after_delete_attempt": Supplier.objects.filter(pk=s1.pk).exists(),
    }

    return {
        "admin_registry": registry_info,
        "admin_access": admin_access,
        "admin_lot_has_supplier_col": admin_lot_has_supplier_col,
        "admin_load_change_has_supplier": admin_load_change_has_supplier,
        "nav_checks": nav_checks,
        "auth_1633": auth_1633,
        "idempotency_and_tamper": idempotency_and_tamper,
        "orm_checks": orm_checks,
    }


def run_phase_postgres() -> dict:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    cluster = (Path(tempfile.gettempdir()) / ("audit04f-pg-" + secrets.token_hex(10))).resolve()
    cluster.mkdir(exist_ok=False)
    mark = cluster / "AUDIT04F_OWNED"
    mark.write_text(stamp, encoding="utf-8")
    dbdir = cluster / "data"
    pw = secrets.token_urlsafe(32)
    pwfile = cluster / "pw"
    pwfile.write_text(pw, encoding="utf-8")
    dbname = "audit04f_" + secrets.token_hex(4)
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]

    def pg(name: str, *args):
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as f:
            res = subprocess.run(
                [str(PG_BIN / f"{name}.exe"), *map(str, args)],
                stdout=f,
                stderr=f,
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            f.seek(0)
            out = f.read().replace(pw, "[REDACTED]")
        if res.returncode:
            raise RuntimeError(f"{name} failed: {out[-800:]}")

    started = False
    configured = False
    pg_report: dict = {"port": port}
    try:
        pg(
            "initdb",
            "-D",
            dbdir,
            "-U",
            "audit04f",
            "--pwfile",
            pwfile,
            "--auth-host=scram-sha-256",
            "--auth-local=scram-sha-256",
            "--encoding=UTF8",
            "--locale=C",
        )
        pwfile.unlink()
        pg(
            "pg_ctl",
            "-D",
            dbdir,
            "-l",
            cluster / "postgres.log",
            "-o",
            f"-h 127.0.0.1 -p {port} -c log_statement=none -c log_min_error_statement=panic",
            "-w",
            "start",
        )
        started = True

        import psycopg
        from psycopg import sql

        conf = {"host": "127.0.0.1", "port": port, "user": "audit04f", "password": pw}
        with psycopg.connect(**conf, dbname="postgres", autocommit=True) as conn:
            pg_report["pg_version"] = conn.execute("SELECT version()").fetchone()[0]
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(dbname)))

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
                "NAME": dbname,
                "USER": "audit04f",
                "PASSWORD": pw,
                "HOST": "127.0.0.1",
                "PORT": port,
                "CONN_MAX_AGE": 0,
                "OPTIONS": {"options": "-c statement_timeout=20000 -c lock_timeout=12000"},
            }
        }
        settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
        env.load_dotenv = loader

        import django

        django.setup()
        configured = True

        from django.core.management import call_command
        from django.db import IntegrityError, connection, connections, transaction
        from django.utils import timezone as tz
        from catalog.models import Category, Product
        from identity.models import Account, Role
        from inventory.models import Supplier
        from inventory.services import LotInput, confirm_initial_load, create_supplier

        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            call_command("migrate", interactive=False, verbosity=0)

        with connection.cursor() as cur:
            cur.execute(
                """
                SELECT c.relname, con.conname, con.contype, pg_get_constraintdef(con.oid)
                FROM pg_constraint con
                JOIN pg_class c ON c.oid = con.conrelid
                WHERE c.relname IN ('inventory_supplier', 'inventory_lot', 'inventory_stockreceipt', 'inventory_initialinventoryload')
                ORDER BY c.relname, con.contype, con.conname
                """
            )
            constraints = [
                {"table": r[0], "name": r[1], "type": r[2], "definition": r[3]}
                for r in cur.fetchall()
            ]
            cur.execute(
                """
                SELECT tablename, indexname, indexdef
                FROM pg_indexes
                WHERE tablename IN ('inventory_supplier', 'inventory_lot', 'inventory_stockreceipt', 'inventory_initialinventoryload')
                ORDER BY tablename, indexname
                """
            )
            indexes = [{"table": r[0], "name": r[1], "def": r[2]} for r in cur.fetchall()]

        supplier_check_constraints = [c for c in constraints if c["table"] == "inventory_supplier" and c["type"] == "c"]

        # Prove SQL layer accepts bad format via direct INSERT (0 DB check constraints on ruc/name/phone)
        bad_id = str(uuid.uuid4())
        with connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO inventory_supplier (id, name, ruc, phone, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, true, NOW(), NOW())
                """,
                [bad_id, "---", "BAD-RUC", "abc"],
            )
            cur.execute("DELETE FROM inventory_supplier WHERE id = %s", [bad_id])

        # Prove duplicate RUC fails at SQL UNIQUE constraint and referenced supplier DELETE fails at FK constraint
        admin_role = Role.objects.create(code=Role.Code.ADMIN, name="Administrador")
        wh_role = Role.objects.create(code=Role.Code.WAREHOUSE, name="Almacenero")
        u_admin = Account.objects.create_user("pgad@deep04.invalid", secrets.token_urlsafe(16) + "A1!", display_name="PG Admin", role=admin_role)
        u_wh = Account.objects.create_user("pgwh@deep04.invalid", secrets.token_urlsafe(16) + "A1!", display_name="PG WH", role=wh_role)
        s_real = create_supplier(actor=u_admin, name="PG Real SAC", ruc="20555666777", phone="")
        cat = Category.objects.create(name="PG Cat")
        prod = Product.objects.create(category=cat, name="PG Prod", barcode="775049988801", sale_price=Decimal("3.00"))
        confirm_initial_load(
            actor=u_wh,
            product=prod,
            supplier=s_real,
            lots=[LotInput("L-PG-1", 3, Decimal("1.5000"), tz.localdate() + timedelta(days=20))],
        )

        dup_ruc_blocked_by_db = False
        try:
            with transaction.atomic():
                with connection.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO inventory_supplier (id, name, ruc, phone, is_active, created_at, updated_at)
                        VALUES (%s, %s, %s, '', true, NOW(), NOW())
                        """,
                        [str(uuid.uuid4()), "Dup SAC", "20555666777"],
                    )
        except IntegrityError:
            dup_ruc_blocked_by_db = True

        fk_blocked_raw_delete = False
        try:
            with transaction.atomic():
                with connection.cursor() as cur:
                    cur.execute("DELETE FROM inventory_supplier WHERE id = %s", [str(s_real.pk)])
        except IntegrityError:
            fk_blocked_raw_delete = True

        pg_report.update(
            {
                "constraints": constraints,
                "indexes": indexes,
                "supplier_sql_check_constraints_count": len(supplier_check_constraints),
                "raw_sql_bad_format_insert_accepted": True,
                "raw_sql_duplicate_ruc_blocked": dup_ruc_blocked_by_db,
                "raw_sql_fk_blocks_linked_supplier_delete": fk_blocked_raw_delete,
            }
        )
    finally:
        if configured:
            connections.close_all()
        if started:
            pg("pg_ctl", "-D", dbdir, "-m", "fast", "-w", "stop")
        with socket.socket() as s:
            pg_report["port_closed"] = s.connect_ex(("127.0.0.1", port)) != 0
        shutil.rmtree(cluster, ignore_errors=True)
        pg_report["cluster_cleaned"] = not cluster.exists()
    return pg_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=["all", "sqlite", "postgres"], default="all")
    parser.add_argument("--run-dir", default="")
    args = parser.parse_args()

    if args.phase == "sqlite":
        print(json.dumps(run_phase_sqlite(args.run_dir), ensure_ascii=False, default=str))
        return 0
    if args.phase == "postgres":
        print(json.dumps(run_phase_postgres(), ensure_ascii=False, default=str))
        return 0

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + secrets.token_hex(4)
    run_dir = RESULTS / "datos" / f"etapa04-deep-{stamp}"
    out_dir = RESULTS / "evidencias/04-reval-20261114" / f"deep-{stamp}"
    before = snapshot_protected(exclude_dir=run_dir)
    fp = current_r1_pmv_fingerprint()
    run_dir.mkdir(parents=True)
    out_dir.mkdir(parents=True)
    (run_dir / "marker.json").write_text(json.dumps({"run": run_dir.name, "created_utc": stamp}), encoding="utf-8")
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")

    res_sqlite = subprocess.run(
        [sys.executable, __file__, "--phase", "sqlite", "--run-dir", str(run_dir)],
        capture_output=True,
        text=True,
        check=True,
    )
    res_pg = subprocess.run(
        [sys.executable, __file__, "--phase", "postgres"],
        capture_output=True,
        text=True,
        check=True,
    )

    after = snapshot_protected(exclude_dir=run_dir)
    report = {
        "started_utc": stamp,
        "build": fp,
        "sqlite": json.loads(res_sqlite.stdout),
        "postgres": json.loads(res_pg.stdout),
        "protected_unchanged": before == after,
        "protected_before": before,
        "protected_after": after,
        "finished_utc": datetime.now(timezone.utc).isoformat(),
    }
    report_path = out_dir / "report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(
        json.dumps(
            {
                "evidence": str(report_path.relative_to(ROOT)).replace("\\", "/"),
                "build_sha256": fp["sha256"],
                "file_count": fp["file_count"],
                "protected_unchanged": report["protected_unchanged"],
                "pg_port_closed": report["postgres"]["port_closed"],
                "pg_cluster_cleaned": report["postgres"]["cluster_cleaned"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
