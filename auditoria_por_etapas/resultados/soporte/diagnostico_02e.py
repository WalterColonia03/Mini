"""Diagnostico aislado en memoria previo a correcciones acotadas de Etapa 02-E.

No abre ni modifica r1_pmv.sqlite3 ni ningun archivo de producto. Usa SQLite :memory:,
claves ficticias efimeras y Django Test Client para medir exactamente los defectos
H02E-01..04 sobre el codigo vigente al entrar a la subetapa 02-E.
"""

from __future__ import annotations

import json
import logging
import os
import secrets
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
APP_DIR = ROOT / "r1-pmv"
OUT_PATH = ROOT / "auditoria_por_etapas" / "resultados" / "evidencias" / "02-E-20261114" / "diagnostico-antes.json"

sys.path.insert(0, str(APP_DIR))
os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("DJANGO_SECRET_KEY", "diagnostico-02e-ephemeral-" + secrets.token_hex(16))

import django  # noqa: E402
from django.conf import settings  # noqa: E402

settings.DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
settings.ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]
django.setup()

from django.contrib.sessions.models import Session  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402
from django.utils import timezone  # noqa: E402

from catalog.models import Category, Product  # noqa: E402
from cash.models import CashRegister, CashShift  # noqa: E402
from identity.models import Account, LoginAttempt, Role  # noqa: E402
from identity.services import _login_identifier  # noqa: E402
from inventory.models import InitialInventoryLoad, Lot  # noqa: E402
from sales.models import SaleDraft, SaleDraftLine  # noqa: E402


class CaptureLogs(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[dict[str, str]] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(
            {
                "logger": record.name,
                "level": record.levelname,
                "message": record.getMessage(),
                "has_exc": str(bool(record.exc_info)),
            }
        )


def main() -> None:
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    call_command("migrate", verbosity=0, interactive=False)

    pwd_admin = "Adm!Diag02e#11"
    pwd_seller = "Ven!Diag02e#22"
    pwd_store = "Alm!Diag02e#33"

    r_admin, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    r_seller, _ = Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})
    r_store, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})

    admin = Account.objects.create_user(
        email="admin.diag02e@pruebas.invalid",
        display_name="Admin Diagnostico",
        role=r_admin,
        password=pwd_admin,
    )
    seller_no_shift = Account.objects.create_user(
        email="ven.sinturno@pruebas.invalid",
        display_name="Vendedor Sin Turno",
        role=r_seller,
        password=pwd_seller,
    )
    seller_with_shift = Account.objects.create_user(
        email="ven.conturno@pruebas.invalid",
        display_name="Vendedor Con Turno",
        role=r_seller,
        password=pwd_seller,
    )
    store = Account.objects.create_user(
        email="alm.diag02e@pruebas.invalid",
        display_name="Almacenero Diagnostico",
        role=r_store,
        password=pwd_store,
    )

    # Preparar lote y turno OPEN para seller_with_shift
    cat = Category(name="Abarrotes Diag", is_active=True)
    cat.full_clean()
    cat.save()
    prod = Product(
        category=cat,
        name="Arroz Diag 1kg",
        barcode="DIAG02E01",
        barcode_type=Product.BarcodeType.INTERNAL,
        sale_price=Decimal("4.50"),
        is_active=True,
    )
    prod.full_clean()
    prod.save()
    initial_load = InitialInventoryLoad.objects.create(product=prod, responsible=store)
    lot = Lot.objects.create(
        product=prod,
        initial_load=initial_load,
        responsible=store,
        is_initial=True,
        number="L-DIAG-01",
        initial_quantity=10,
        available_quantity=10,
        unit_cost=Decimal("3.0000"),
        expiration_date=date.today() + timedelta(days=30),
    )
    register = CashRegister.objects.first() or CashRegister.objects.create(code="CAJA-DIAG")
    shift = CashShift.objects.create(
        cash_register=register,
        seller=seller_with_shift,
        opening_amount=Decimal("50.00"),
        status=CashShift.Status.OPEN,
    )

    def login_client(email: str, password: str) -> Client:
        c = Client()
        resp = c.post(reverse("login"), {"email": email, "password": password})
        assert resp.status_code == 302, (email, resp.status_code)
        return c

    # H02E-01: mensajes de /salir/ segun rol, turno y borrador
    def norm_html(raw: str) -> str:
        return " ".join(raw.split())

    def extract_main_text(raw: str) -> str:
        import re
        m = re.search(r"<main[^>]*>(.*?)</main>", raw, flags=re.S | re.I)
        fragment = m.group(1) if m else raw
        return " ".join(re.sub(r"<[^>]+>", " ", fragment).split())

    c_no_shift = login_client(seller_no_shift.email, pwd_seller)
    html_no_shift = extract_main_text(c_no_shift.get(reverse("logout")).content.decode("utf-8"))

    c_admin = login_client(admin.email, pwd_admin)
    html_admin = extract_main_text(c_admin.get(reverse("logout")).content.decode("utf-8"))

    c_store = login_client(store.email, pwd_store)
    html_store = extract_main_text(c_store.get(reverse("logout")).content.decode("utf-8"))

    c_shift = login_client(seller_with_shift.email, pwd_seller)
    html_shift_no_draft = extract_main_text(c_shift.get(reverse("logout")).content.decode("utf-8"))

    draft = SaleDraft.objects.create(
        seller=seller_with_shift,
        cash_shift=shift,
        status=SaleDraft.Status.ACTIVE,
    )
    SaleDraftLine.objects.create(
        draft=draft,
        product=prod,
        quantity=1,
        unit_price=Decimal("4.50"),
    )
    html_shift_with_draft = extract_main_text(c_shift.get(reverse("logout")).content.decode("utf-8"))
    resp_logout_post = c_shift.post(reverse("logout"))
    draft.refresh_from_db()
    lot.refresh_from_db()
    shift.refresh_from_db()

    h02e_01 = {
        "seller_no_shift_text": html_no_shift,
        "seller_no_shift_claims_open_shift": "tu turno abierto seguirá ligado" in html_no_shift.lower(),
        "admin_text": html_admin,
        "admin_mentions_open_shift": "turno abierto" in html_admin.lower(),
        "storekeeper_text": html_store,
        "storekeeper_mentions_open_shift": "turno abierto" in html_store.lower(),
        "seller_with_shift_no_draft_text": html_shift_no_draft,
        "seller_with_shift_with_draft_text": html_shift_with_draft,
        "seller_with_shift_with_draft_mentions_discard": "se descartará" in html_shift_with_draft.lower(),
        "post_logout_status": resp_logout_post.status_code,
        "draft_status_after_logout": draft.status,
        "lot_qty_after_logout": lot.available_quantity,
        "shift_status_after_logout": shift.status,
    }

    # H02E-02: /empleados/ falta de pantalla de confirmacion de estado
    html_list = c_admin.get(reverse("employee-list")).content.decode("utf-8")
    resp_get_state = c_admin.get(reverse("employee-deactivate", args=[seller_no_shift.pk]))
    h02e_02 = {
        "list_posts_directly_to_estado": f'action="/empleados/{seller_no_shift.pk}/estado/"' in html_list,
        "get_estado_status": resp_get_state.status_code,
        "has_confirm_url_in_urls": any(
            getattr(p, "name", None) == "employee-state-confirm"
            for p in __import__("identity.urls").urls.urlpatterns
        ),
    }

    # H02E-03: bloqueo borrado en reactivar, cambio de correo, falta de sesiones revocadas al resetear clave, falta unlock_account
    anon = Client()
    for _ in range(5):
        anon.post(reverse("login"), {"email": seller_no_shift.email, "password": "Wrong!Pass01"})
    attempt_locked = LoginAttempt.objects.get(identifier=_login_identifier(seller_no_shift.email_normalized))
    locked_before_deactivate = bool(attempt_locked.locked_until and attempt_locked.locked_until > timezone.now())

    c_admin.post(reverse("employee-deactivate", args=[seller_no_shift.pk]), {"action": "desactivar"})
    c_admin.post(reverse("employee-deactivate", args=[seller_no_shift.pk]), {"action": "reactivar"})
    attempt_after_reactivate = LoginAttempt.objects.get(identifier=_login_identifier(seller_no_shift.email_normalized))

    # Bloqueo y cambio de correo sin cambio de clave
    for _ in range(5):
        anon.post(reverse("login"), {"email": store.email, "password": "Wrong!Pass02"})
    store_attempt_before = LoginAttempt.objects.get(identifier=_login_identifier(store.email_normalized))
    old_store_norm = store.email_normalized
    new_store_email = "alm.renombrado@pruebas.invalid"
    c_admin.post(
        reverse("employee-edit", args=[store.pk]),
        {
            "display_name": store.display_name,
            "email": new_store_email,
            "role": str(r_store.pk),
            "new_password": "",
        },
    )
    store_attempt_old_after = LoginAttempt.objects.get(identifier=_login_identifier(old_store_norm))
    store_attempt_new_after = LoginAttempt.objects.filter(
        identifier=_login_identifier(new_store_email)
    ).first()

    # Sesiones persistidas tras resetear clave de admin secundario o vendedor con turno
    c_v1 = login_client(seller_with_shift.email, pwd_seller)
    c_v2 = login_client(seller_with_shift.email, pwd_seller)
    sessions_before_pwd = [
        s.session_key
        for s in Session.objects.all()
        if s.get_decoded().get("_auth_user_id") == str(seller_with_shift.pk)
    ]
    c_admin.post(
        reverse("employee-edit", args=[seller_with_shift.pk]),
        {
            "display_name": seller_with_shift.display_name,
            "email": seller_with_shift.email,
            "role": str(r_seller.pk),
            "new_password": "Ven!Reset02e#99",
        },
    )
    sessions_after_pwd = [
        s.session_key
        for s in Session.objects.all()
        if s.get_decoded().get("_auth_user_id") == str(seller_with_shift.pk)
    ]
    resp_v1_after_pwd = c_v1.get(reverse("dashboard"))
    html_edit = c_admin.get(reverse("employee-edit", args=[seller_with_shift.pk])).content.decode("utf-8")

    h02e_03 = {
        "locked_before_deactivate": locked_before_deactivate,
        "reactivate_wiped_failures": attempt_after_reactivate.failures == 0 and attempt_after_reactivate.locked_until is None,
        "store_was_locked_before_email_rename": bool(
            store_attempt_before.locked_until and store_attempt_before.locked_until > timezone.now()
        ),
        "email_rename_wiped_old_lockout": (
            store_attempt_old_after.failures == 0 and store_attempt_old_after.locked_until is None
        ),
        "email_rename_new_attempt_exists": store_attempt_new_after is not None,
        "sessions_count_before_pwd_reset": len(sessions_before_pwd),
        "sessions_count_after_pwd_reset_still_persisted": len(sessions_after_pwd),
        "old_client_get_dashboard_status_after_pwd_reset": resp_v1_after_pwd.status_code,
        "edit_form_has_unlock_field": "unlock_account" in html_edit,
    }

    # H02E-04: auditoria tecnica y filtro de excepciones
    handler = CaptureLogs()
    root_logger = logging.getLogger()
    old_level = root_logger.level
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    try:
        c_tmp = login_client(admin.email, pwd_admin)
        c_tmp.post(reverse("logout"))
        c_store.get(reverse("employee-list"))
    finally:
        root_logger.removeHandler(handler)
        root_logger.setLevel(old_level)

    audit_records = [
        r for r in handler.records if "identity" in r["logger"] or "audit" in r["logger"]
    ]
    h02e_04 = {
        "captured_total_log_records": len(handler.records),
        "captured_identity_audit_records": len(audit_records),
        "sample_loggers": sorted({r["logger"] for r in handler.records}),
        "has_identity_audit_model": hasattr(__import__("identity.models").models, "IdentityAuditEvent"),
    }

    payload = {
        "scope": "02-E pre-fix baseline diagnostic (in-memory SQLite)",
        "h02e_01": h02e_01,
        "h02e_02": h02e_02,
        "h02e_03": h02e_03,
        "h02e_04": h02e_04,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
