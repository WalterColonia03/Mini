"""Reproducción HTTP + PostgreSQL 18.4 de carreras SEC-15-CONC-02 (pre-corrección 02-F)."""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "r1-pmv/manage.py").is_file())
PROJECT = ROOT / "r1-pmv"
RESULTS = ROOT / "auditoria_por_etapas/resultados"
OUT = RESULTS / "evidencias/02-F-20261114/postgresql_repro"
OUT.mkdir(parents=True, exist_ok=True)
BIN = Path(r"C:\Program Files\PostgreSQL\18\bin")

CLUSTER = (Path(tempfile.gettempdir()) / f"audit02f-repro-{secrets.token_hex(6)}").resolve()
CLUSTER.mkdir(exist_ok=False)
DBDIR = CLUSTER / "data"
PW = secrets.token_urlsafe(36)
PWFILE = CLUSTER / "pw.txt"
PWFILE.write_text(PW, encoding="utf-8")
DBNAME = f"audit02f_repro_{secrets.token_hex(4)}"

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(("127.0.0.1", 0))
    PORT = s.getsockname()[1]


def pg(cmd: str, *args) -> None:
    with tempfile.TemporaryFile(mode="w+", encoding="utf-8", errors="replace") as capture:
        proc = subprocess.run(
            [str(BIN / f"{cmd}.exe"), *map(str, args)],
            stdout=capture,
            stderr=capture,
            timeout=60,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        capture.seek(0)
        msg = capture.read().replace(PW, "[REDACTED]")
    if proc.returncode != 0:
        raise RuntimeError(f"{cmd} failed: {msg[-800:]}")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def port_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex(("127.0.0.1", port)) == 0


def csrf_from(resp) -> str:
    assert resp.status_code == 200, f"Expected 200 for CSRF fetch, got {resp.status_code}"
    m = re.search(rb'name="csrfmiddlewaretoken"[^>]*value="([^"]+)"', resp.content)
    if m is None:
        m = re.search(rb'value="([^"]+)"[^>]*name="csrfmiddlewaretoken"', resp.content)
    if m is not None:
        return m.group(1).decode("ascii")
    cookie = resp.cookies.get("csrftoken")
    assert cookie is not None, "CSRF token not found in response body or cookie"
    return cookie.value


def main() -> None:
    prod_db = PROJECT / "r1_pmv.sqlite3"
    db_before = sha256_file(prod_db)
    evidence: dict = {
        "stage": "02-F-repro-pre-fix",
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "port": PORT,
        "cases": [],
    }
    started = False
    try:
        pg(
            "initdb",
            "-D",
            DBDIR,
            "-U",
            "audit02f",
            "--pwfile",
            PWFILE,
            "--auth-host=scram-sha-256",
            "--auth-local=scram-sha-256",
            "--encoding=UTF8",
            "--locale=C",
        )
        PWFILE.unlink()
        pg(
            "pg_ctl",
            "-D",
            DBDIR,
            "-l",
            CLUSTER / "postgres.log",
            "-o",
            f"-h 127.0.0.1 -p {PORT} -c log_statement=none -c log_min_error_statement=panic",
            "-w",
            "start",
        )
        started = True

        import psycopg
        from psycopg import sql

        with psycopg.connect(
            host="127.0.0.1",
            port=PORT,
            user="audit02f",
            password=PW,
            dbname="postgres",
            autocommit=True,
        ) as conn:
            evidence["postgres_version"] = conn.execute("SELECT version()").fetchone()[0]
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(DBNAME)))

        sys.path.insert(0, str(PROJECT))
        os.environ.update(
            APP_ENV="test",
            DJANGO_DEBUG="false",
            DJANGO_SECRET_KEY=secrets.token_urlsafe(48),
            DJANGO_SETTINGS_MODULE="config.settings",
        )
        from config import env as config_env

        config_env.load_dotenv = lambda path=None: None
        from django.conf import settings

        settings.ALLOWED_HOSTS = ["127.0.0.1", "localhost", "testserver"]
        settings.SECURE_SSL_REDIRECT = False
        settings.SESSION_COOKIE_SECURE = False
        settings.CSRF_COOKIE_SECURE = False
        settings.DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": DBNAME,
                "USER": "audit02f",
                "PASSWORD": PW,
                "HOST": "127.0.0.1",
                "PORT": PORT,
                "CONN_MAX_AGE": 0,
                "OPTIONS": {"options": "-c statement_timeout=20000 -c lock_timeout=12000"},
            }
        }
        import django

        django.setup()
        from django.contrib.sessions.models import Session
        from django.core.management import call_command
        from django.db import connections
        from django.test import Client
        from django.utils import timezone as dj_tz

        call_command("migrate", verbosity=0)

        from cash.models import CashRegister
        from cash.services import open_cash_shift
        from catalog.models import Category, Product
        from identity.models import Account, IdentityAuditEvent, Role
        from identity.services import (
            create_employee,
            create_server_session as real_create_server_session,
            deactivate_employee,
            update_employee,
        )
        from inventory.models import Lot
        from sales.models import Sale, SaleDraft
        from sales.services import (
            active_draft_for_actor as real_active_draft_for_actor,
            add_product_to_draft,
            checkout_sale,
            draft_signature,
        )

        admin_role, _ = Role.objects.get_or_create(
            code=Role.Code.ADMIN, defaults={"name": "Administrador"}
        )
        seller_role, _ = Role.objects.get_or_create(
            code=Role.Code.SELLER, defaults={"name": "Vendedor"}
        )
        Role.objects.get_or_create(
            code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"}
        )
        admin = Account.objects.create_user(
            "admin.repro@pg.test",
            "Admin1234",
            display_name="Admin Repro",
            role=admin_role,
        )

        def active_sessions_for(account_id) -> list[dict]:
            out = []
            sid = str(account_id)
            for s in Session.objects.all():
                data = s.get_decoded()
                if str(data.get("_auth_user_id")) == sid:
                    out.append({"session_key": s.session_key, "role_code": data.get("role_code")})
            return out

        def login_via_http(email: str, password: str) -> Client:
            c = Client(enforce_csrf_checks=True)
            g = c.get("/")
            p = c.post(
                "/",
                {"csrfmiddlewaretoken": csrf_from(g), "email": email, "password": password},
            )
            assert p.status_code == 302, f"Expected 302 login for {email}, got {p.status_code}"
            return c

        # ── CASE 1: HTTP POST /ingresar/ vs deactivate_employee ──
        cajero1 = create_employee(
            actor=admin,
            display_name="Cajero Race 1",
            email="cajero1.race@pg.test",
            password="Seller123",
            role=seller_role,
        )
        ready_c1 = threading.Event()
        deact_done_c1 = threading.Event()

        def paused_create_session_c1(req, acc):
            ready_c1.set()
            assert deact_done_c1.wait(timeout=10)
            return real_create_server_session(req, acc)

        cli1 = Client(enforce_csrf_checks=True)
        csrf1 = csrf_from(cli1.get("/"))

        def t_login_c1():
            try:
                with patch("identity.views.create_server_session", side_effect=paused_create_session_c1):
                    resp = cli1.post(
                        "/",
                        {"csrfmiddlewaretoken": csrf1, "email": "cajero1.race@pg.test", "password": "Seller123"},
                    )
                return {"status": resp.status_code, "location": resp.get("Location")}
            finally:
                connections.close_all()

        def t_deact_c1():
            try:
                assert ready_c1.wait(timeout=10)
                acc = Account.objects.select_related("role").get(pk=cajero1.pk)
                adm = Account.objects.select_related("role").get(pk=admin.pk)
                deactivate_employee(actor=adm, account=acc)
                deact_done_c1.set()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(t_login_c1)
            f2 = pool.submit(t_deact_c1)
            r1_login = f1.result(timeout=15)
            f2.result(timeout=15)

        cajero1.refresh_from_db()
        sessions_c1 = active_sessions_for(cajero1.pk)
        next_get = cli1.get("/inicio/")
        events_c1 = list(
            IdentityAuditEvent.objects.filter(target_id=str(cajero1.pk))
            .order_by("occurred_at")
            .values("action", "outcome", "metadata")
        )
        evidence["cases"].append(
            {
                "case": "race1_login_vs_deactivate",
                "login_post": r1_login,
                "is_active_after": cajero1.is_active,
                "sessions_created_for_inactive": len(sessions_c1),
                "reproduced_login_success_for_inactive": (
                    r1_login["status"] == 302
                    and not cajero1.is_active
                    and len(sessions_c1) > 0
                ),
                "subsequent_get_inicio_status": next_get.status_code,
                "events": events_c1,
            }
        )

        # ── CASE 2: HTTP POST /ingresar/ vs role change ──
        cajero2 = create_employee(
            actor=admin,
            display_name="Cajero Race 2",
            email="cajero2.race@pg.test",
            password="Seller123",
            role=seller_role,
        )
        ready_c2 = threading.Event()
        role_done_c2 = threading.Event()

        def paused_create_session_c2(req, acc):
            ready_c2.set()
            assert role_done_c2.wait(timeout=10)
            return real_create_server_session(req, acc)

        cli2 = Client(enforce_csrf_checks=True)
        csrf2 = csrf_from(cli2.get("/"))

        def t_login_c2():
            try:
                with patch("identity.views.create_server_session", side_effect=paused_create_session_c2):
                    resp = cli2.post(
                        "/",
                        {"csrfmiddlewaretoken": csrf2, "email": "cajero2.race@pg.test", "password": "Seller123"},
                    )
                return {"status": resp.status_code, "location": resp.get("Location")}
            finally:
                connections.close_all()

        def t_role_c2():
            try:
                assert ready_c2.wait(timeout=10)
                acc = Account.objects.select_related("role").get(pk=cajero2.pk)
                adm = Account.objects.select_related("role").get(pk=admin.pk)
                wh = Role.objects.get(code=Role.Code.WAREHOUSE)
                update_employee(
                    actor=adm,
                    account=acc,
                    display_name=acc.display_name,
                    email=acc.email,
                    role=wh,
                )
                role_done_c2.set()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(t_login_c2)
            f2 = pool.submit(t_role_c2)
            r2_login = f1.result(timeout=15)
            f2.result(timeout=15)

        cajero2.refresh_from_db()
        sessions_c2 = active_sessions_for(cajero2.pk)
        evidence["cases"].append(
            {
                "case": "race2_login_vs_role_change",
                "login_post": r2_login,
                "account_role_after": cajero2.role.code,
                "sessions_after": sessions_c2,
                "stale_session_role_reproduced": any(
                    s["role_code"] != cajero2.role.code for s in sessions_c2
                ),
            }
        )

        # ── CASE 3: HTTP POST /ingresar/ vs password reset ──
        cajero3 = create_employee(
            actor=admin,
            display_name="Cajero Race 3",
            email="cajero3.race@pg.test",
            password="OldPass123",
            role=seller_role,
        )
        ready_c3 = threading.Event()
        pwd_done_c3 = threading.Event()

        def paused_create_session_c3(req, acc):
            ready_c3.set()
            assert pwd_done_c3.wait(timeout=10)
            return real_create_server_session(req, acc)

        cli3 = Client(enforce_csrf_checks=True)
        csrf3 = csrf_from(cli3.get("/"))

        def t_login_c3():
            try:
                with patch("identity.views.create_server_session", side_effect=paused_create_session_c3):
                    resp = cli3.post(
                        "/",
                        {"csrfmiddlewaretoken": csrf3, "email": "cajero3.race@pg.test", "password": "OldPass123"},
                    )
                return {"status": resp.status_code, "location": resp.get("Location")}
            finally:
                connections.close_all()

        def t_pwd_c3():
            try:
                assert ready_c3.wait(timeout=10)
                acc = Account.objects.select_related("role").get(pk=cajero3.pk)
                adm = Account.objects.select_related("role").get(pk=admin.pk)
                update_employee(
                    actor=adm,
                    account=acc,
                    display_name=acc.display_name,
                    email=acc.email,
                    role=acc.role,
                    new_password="NewPass123",
                )
                pwd_done_c3.set()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(t_login_c3)
            f2 = pool.submit(t_pwd_c3)
            r3_login = f1.result(timeout=15)
            f2.result(timeout=15)

        sessions_c3 = active_sessions_for(cajero3.pk)
        get_inicio_c3 = cli3.get("/inicio/")
        evidence["cases"].append(
            {
                "case": "race3_login_vs_password_reset",
                "login_post": r3_login,
                "sessions_surviving_after_reset": len(sessions_c3),
                "stale_session_still_gets_200_inicio": get_inicio_c3.status_code == 200,
                "reproduced_defect": len(sessions_c3) > 0 and get_inicio_c3.status_code == 200,
            }
        )

        # ── Shared catalog & cash setup for logout races ──
        cat = Category.objects.create(name="Abarrotes Race", is_active=True)
        prod = Product.objects.create(
            category=cat,
            name="Arroz Race 1kg",
            barcode="7750001000015",
            sale_price=Decimal("4.50"),
            average_cost=Decimal("3.00"),
            is_active=True,
        )
        Lot.objects.create(
            product=prod,
            number="L-RACE-01",
            number_normalized="l-race-01",
            initial_quantity=50,
            available_quantity=50,
            unit_cost=Decimal("3.00"),
            expiration_date=dj_tz.localdate() + timedelta(days=90),
        )
        reg4 = CashRegister.objects.create(code="CAJA-RACE-4", name="Caja Race 4")
        reg5 = CashRegister.objects.create(code="CAJA-RACE-5", name="Caja Race 5")
        reg6 = CashRegister.objects.create(code="CAJA-RACE-6", name="Caja Race 6")

        # ── CASE 4: HTTP POST /salir/ (checked None) vs add_draft_line ──
        cajero4 = create_employee(
            actor=admin,
            display_name="Cajero Race 4",
            email="cajero4.race@pg.test",
            password="Seller123",
            role=seller_role,
        )
        open_cash_shift(actor=cajero4, cash_register=reg4, opening_amount=Decimal("20.00"))
        cli4 = login_via_http("cajero4.race@pg.test", "Seller123")
        csrf4 = csrf_from(cli4.get("/salir/"))
        checked_none_c4 = threading.Event()
        add_done_c4 = threading.Event()

        def paused_active_draft_c4(*, actor):
            res = real_active_draft_for_actor(actor=actor)
            if res is None:
                checked_none_c4.set()
                assert add_done_c4.wait(timeout=10)
            return res

        def t_logout_c4():
            try:
                with patch("sales.services.active_draft_for_actor", side_effect=paused_active_draft_c4):
                    resp = cli4.post("/salir/", {"csrfmiddlewaretoken": csrf4})
                return {"status": resp.status_code, "location": resp.get("Location")}
            finally:
                connections.close_all()

        def t_add_c4():
            try:
                assert checked_none_c4.wait(timeout=10)
                acc = Account.objects.select_related("role").get(pk=cajero4.pk)
                draft = add_product_to_draft(actor=acc, product_id=prod.pk, quantity=1)
                add_done_c4.set()
                return {"draft_id": str(draft.pk)}
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(t_logout_c4)
            f2 = pool.submit(t_add_c4)
            r4_out = f1.result(timeout=15)
            r4_add = f2.result(timeout=15)

        active_after_logout_c4 = SaleDraft.objects.filter(
            seller=cajero4, status=SaleDraft.Status.ACTIVE
        ).count()
        logout_events_c4 = list(
            IdentityAuditEvent.objects.filter(actor=cajero4, action="LOGOUT_SUCCESS").values("metadata")
        )
        evidence["cases"].append(
            {
                "case": "race4_logout_vs_add_draft_line",
                "logout_resp": r4_out,
                "add_resp": r4_add,
                "orphaned_active_drafts_after_logout": active_after_logout_c4,
                "reproduced_defect": active_after_logout_c4 > 0,
                "logout_metadata": logout_events_c4,
            }
        )

        # ── CASE 5: HTTP POST /salir/ (saw draft) vs checkout_sale ──
        cajero5 = create_employee(
            actor=admin,
            display_name="Cajero Race 5",
            email="cajero5.race@pg.test",
            password="Seller123",
            role=seller_role,
        )
        open_cash_shift(actor=cajero5, cash_register=reg5, opening_amount=Decimal("20.00"))
        draft5 = add_product_to_draft(actor=cajero5, product_id=prod.pk, quantity=1)
        sig5 = draft_signature(draft5.pk, list(draft5.lines.select_related("product").all()))
        cli5 = login_via_http("cajero5.race@pg.test", "Seller123")
        csrf5 = csrf_from(cli5.get("/salir/"))

        saw_draft_c5 = threading.Event()
        checkout_done_c5 = threading.Event()

        def paused_active_draft_c5(*, actor):
            res = real_active_draft_for_actor(actor=actor)
            saw_draft_c5.set()
            assert checkout_done_c5.wait(timeout=10)
            return res

        def t_logout_c5():
            try:
                with patch("sales.services.active_draft_for_actor", side_effect=paused_active_draft_c5):
                    resp = cli5.post("/salir/", {"csrfmiddlewaretoken": csrf5})
                return {"status": resp.status_code, "location": resp.get("Location")}
            finally:
                connections.close_all()

        def t_checkout_c5():
            try:
                assert saw_draft_c5.wait(timeout=10)
                acc = Account.objects.select_related("role").get(pk=cajero5.pk)
                sale = checkout_sale(
                    actor=acc,
                    draft_id=draft5.pk,
                    cash_received=Decimal("10.00"),
                    idempotency_key=uuid.uuid4(),
                    expected_subtotal=Decimal("4.50"),
                    expected_signature=sig5,
                )
                checkout_done_c5.set()
                return {"sale_id": str(sale.pk), "correlative": sale.correlative}
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(t_logout_c5)
            f2 = pool.submit(t_checkout_c5)
            r5_out = f1.result(timeout=15)
            r5_sale = f2.result(timeout=15)

        logout_events_c5 = list(
            IdentityAuditEvent.objects.filter(actor=cajero5, action="LOGOUT_SUCCESS").values("metadata")
        )
        evidence["cases"].append(
            {
                "case": "race5_logout_vs_checkout",
                "logout_resp": r5_out,
                "sale_resp": r5_sale,
                "sales_created": Sale.objects.filter(seller=cajero5).count(),
                "logout_metadata": logout_events_c5,
                "reproduced_misleading_discarded_audit": (
                    Sale.objects.filter(seller=cajero5).count() == 1
                    and bool(logout_events_c5)
                    and logout_events_c5[0]["metadata"].get("discarded_draft_id") == str(draft5.pk)
                ),
            }
        )

        # ── CASE 6: HTTP POST /salir/ (saw draft) vs deactivate_employee ──
        cajero6 = create_employee(
            actor=admin,
            display_name="Cajero Race 6",
            email="cajero6.race@pg.test",
            password="Seller123",
            role=seller_role,
        )
        open_cash_shift(actor=cajero6, cash_register=reg6, opening_amount=Decimal("20.00"))
        add_product_to_draft(actor=cajero6, product_id=prod.pk, quantity=1)
        cli6 = login_via_http("cajero6.race@pg.test", "Seller123")
        csrf6 = csrf_from(cli6.get("/salir/"))

        saw_draft_c6 = threading.Event()
        deact_done_c6 = threading.Event()

        def paused_active_draft_c6(*, actor):
            res = real_active_draft_for_actor(actor=actor)
            saw_draft_c6.set()
            assert deact_done_c6.wait(timeout=10)
            return res

        def t_logout_c6():
            try:
                with patch("sales.services.active_draft_for_actor", side_effect=paused_active_draft_c6):
                    resp = cli6.post("/salir/", {"csrfmiddlewaretoken": csrf6})
                return {"status": resp.status_code, "location": resp.get("Location")}
            finally:
                connections.close_all()

        def t_deact_c6():
            try:
                assert saw_draft_c6.wait(timeout=10)
                acc = Account.objects.select_related("role").get(pk=cajero6.pk)
                adm = Account.objects.select_related("role").get(pk=admin.pk)
                deactivate_employee(actor=adm, account=acc)
                deact_done_c6.set()
                return {"deactivated": True}
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(t_logout_c6)
            f2 = pool.submit(t_deact_c6)
            r6_out = f1.result(timeout=15)
            r6_deact = f2.result(timeout=15)

        evidence["cases"].append(
            {
                "case": "race6_logout_vs_deactivate",
                "logout_resp": r6_out,
                "deact_resp": r6_deact,
                "reproduced_403_on_logout": r6_out["status"] == 403,
            }
        )

    finally:
        if started:
            try:
                from django.db import connections

                connections.close_all()
            except Exception:
                pass
            pg("pg_ctl", "-D", DBDIR, "-m", "fast", "-w", "stop")
        shutil.rmtree(CLUSTER, ignore_errors=True)
        evidence["port_closed_after_stop"] = not port_open(PORT)
        evidence["prod_db_sha256_before"] = db_before
        evidence["prod_db_sha256_after"] = sha256_file(prod_db)
        evidence["prod_db_unchanged"] = db_before == evidence["prod_db_sha256_after"]
        evidence["finished_utc"] = datetime.now(timezone.utc).isoformat()
        (OUT / "resumen.json").write_text(
            json.dumps(evidence, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
        )
        print(json.dumps(evidence, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
