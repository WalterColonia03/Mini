"""Stage 04 pre-fix defect reproduction against an isolated marked SQLite database.
Never loads operator .env and never modifies protected databases.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import sys
import traceback
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "auditoria_por_etapas" / "resultados"
APP = ROOT / "r1-pmv"
SUPPORT = Path(__file__).resolve().parent


def digest(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def main() -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = RESULTS / "datos" / f"etapa04-repro-{stamp}"
    out_dir = RESULTS / "evidencias" / f"04-repro-{stamp}"

    protected = [
        *APP.glob("*.sqlite3"),
        *(RESULTS / "datos").rglob("*.sqlite3"),
        ROOT / "PLANIFICACION_SCRUM_R1PMV.xlsx",
    ]
    hashes_before = {str(p.relative_to(ROOT)): digest(p) for p in protected}

    run_dir.mkdir(parents=False, exist_ok=False)
    out_dir.mkdir(parents=False, exist_ok=False)
    (run_dir / "marker.json").write_text(
        json.dumps({"run": run_dir.name, "created_utc": stamp}), encoding="utf-8"
    )
    (run_dir / ".django-key").write_text(secrets.token_urlsafe(48), encoding="utf-8")

    os.environ["APP_ENV"] = "test"
    os.environ["DATABASE_URL"] = "sqlite"
    os.environ["DJANGO_DEBUG"] = "false"
    os.environ["DJANGO_ALLOWED_HOSTS"] = "127.0.0.1,localhost,testserver"
    os.environ["DJANGO_SECRET_KEY"] = (run_dir / ".django-key").read_text(encoding="utf-8")
    os.environ["DJANGO_SETTINGS_MODULE"] = "config.settings"

    sys.path.insert(0, str(APP))
    from config import env as config_env

    loader = config_env.load_dotenv
    config_env.load_dotenv = lambda path=None: None
    try:
        from django.conf import settings
        settings.DATABASES["default"] = {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": run_dir / "audit.sqlite3",
        }
        import django
        django.setup()
    finally:
        config_env.load_dotenv = loader

    from django.contrib.auth.models import AnonymousUser
    from django.core.exceptions import PermissionDenied, ValidationError
    from django.core.management import call_command
    from django.test import Client
    from django.urls import reverse
    from django.utils import timezone as dj_tz

    from catalog.models import Category, Product
    from identity.models import Account, Role
    from identity.services import deactivate_employee, reactivate_employee
    from inventory.forms import InitialLoadProductForm, SupplierForm
    from inventory.models import Supplier
    from inventory.services import (
        LotInput,
        confirm_initial_load,
        create_supplier,
        register_stock_entry,
        toggle_supplier_status,
    )

    call_command("migrate", verbosity=0, interactive=False)

    admin_role, _ = Role.objects.get_or_create(code=Role.Code.ADMIN, defaults={"name": "Administrador"})
    wh_role, _ = Role.objects.get_or_create(code=Role.Code.WAREHOUSE, defaults={"name": "Almacenero"})
    Role.objects.get_or_create(code=Role.Code.SELLER, defaults={"name": "Vendedor"})

    pw = "Aa1!" + secrets.token_urlsafe(18)
    admin = Account.objects.create_user("admin04repro@audit04.invalid", pw, display_name="Admin Repro", role=admin_role)
    wh = Account.objects.create_user("wh04repro@audit04.invalid", pw, display_name="Almacenero Repro", role=wh_role)

    findings: dict[str, object] = {}

    # 1. Unicode digit RUC accepted in form & service + 12-digit message mismatch
    unicode_ruc = "٢٠١٢٣٤٥٦٧٨٩"
    f_uni = SupplierForm({"name": "Distribuidora Unicode", "ruc": unicode_ruc, "phone": "---"})
    findings["unicode_ruc_form_valid"] = f_uni.is_valid()
    sup_uni = create_supplier(actor=admin, name="  Distribuidora   Unicode  ", ruc=unicode_ruc, phone="abc<script>")
    findings["unicode_and_invalid_service_created"] = {
        "id": str(sup_uni.pk),
        "name": sup_uni.name,
        "ruc": sup_uni.ruc,
        "phone": sup_uni.phone,
    }

    f_12 = SupplierForm({"name": "Proveedor 12 dig", "ruc": "201234567890", "phone": ""})
    findings["ruc_12_digits_form_valid"] = f_12.is_valid()
    findings["ruc_12_digits_error"] = f_12.errors.get("ruc", [])

    # 2. Symbol-only name / NUL / length overflow in service & form
    f_sym = SupplierForm({"name": "---", "ruc": "20123456789", "phone": "((--))"})
    findings["symbol_only_name_and_phone_form_valid"] = f_sym.is_valid()

    # 3. Anonymous / stale deactivated ADMIN in create_supplier & toggle_supplier_status
    try:
        create_supplier(actor=AnonymousUser(), name="Anon", ruc="20123456788")
        findings["anon_create_result"] = "unexpected_success"
    except Exception as exc:
        findings["anon_create_error"] = f"{type(exc).__name__}: {exc}"

    stale_admin = Account.objects.select_related("role").get(pk=admin.pk)
    admin2 = Account.objects.create_user("admin04repro2@audit04.invalid", pw, display_name="Admin 2", role=admin_role)
    deactivate_employee(actor=admin2, account=Account.objects.get(pk=admin.pk))
    sup_stale = create_supplier(actor=stale_admin, name="Stale Admin Prov", ruc="20123456787")
    toggle_supplier_status(actor=stale_admin, supplier=sup_stale)
    findings["stale_deactivated_admin_succeeded"] = {
        "created_ruc": sup_stale.ruc,
        "toggled_is_active": sup_stale.is_active,
    }
    reactivate_employee(actor=admin2, account=Account.objects.get(pk=admin.pk))

    # 4. Blind double-tab toggle inversion
    client1 = Client()
    client2 = Client()
    client1.force_login(admin)
    client2.force_login(admin)
    target_sup = create_supplier(actor=admin, name="Proveedor Doble Tab", ruc="20555666777")
    toggle_url = reverse("supplier-toggle", args=(target_sup.pk,))
    r1 = client1.post(toggle_url)  # expects deactivate -> False
    r2 = client2.post(toggle_url)  # second stale tab clicking same "Desactivar" flips back to True!
    target_sup.refresh_from_db()
    findings["double_tab_toggle_inversion"] = {
        "after_first_post_status": r1.status_code,
        "after_second_post_status": r2.status_code,
        "final_is_active": target_sup.is_active,
    }

    # 5. Empty POST {} in supplier-create + GET ?q=%00 + label inside .input-group
    empty_post_resp = client1.post(reverse("supplier-create"), {})
    findings["empty_post_status_and_has_alert"] = {
        "status": empty_post_resp.status_code,
        "has_validation_error": "obligatorio" in empty_post_resp.content.decode("utf-8").lower(),
    }
    list_html = client1.get(reverse("supplier-list")).content.decode("utf-8")
    findings["label_inside_input_group"] = '<div class="input-group" style="max-width:400px;">\n    <label' in list_html or '<div class="input-group" style="max-width:400px;">\r\n    <label' in list_html
    try:
        nul_resp = client1.get(reverse("supplier-list"), {"q": "\x00"})
        findings["nul_search_status"] = nul_resp.status_code
    except Exception as exc:
        findings["nul_search_exception"] = f"{type(exc).__name__}: {exc}"

    # 6. Inactive supplier in InitialLoadProductForm + TemplateSyntaxError on initial_load_created
    cat = Category.objects.create(name="Abarrotes Repro")
    prod = Product.objects.create(category=cat, name="Leche Repro", barcode="775000400001", sale_price=Decimal("4.50"))
    future = dj_tz.localdate() + timedelta(days=60)
    sup_rec = create_supplier(actor=admin, name="Proveedor Recepcion", ruc="20444333221")
    sup_rec_inact = create_supplier(actor=admin, name="Proveedor Rechazado", ruc="20444333222")
    sup_rec_inact.is_active = False
    sup_rec_inact.save(update_fields=["is_active"])

    form_rec = InitialLoadProductForm({"product": str(prod.pk), "supplier": str(sup_rec_inact.pk)})
    findings["inactive_supplier_form_valid"] = form_rec.is_valid()
    findings["inactive_supplier_error"] = form_rec.errors.get("supplier", [])
    findings["inactive_supplier_html_keeps_identity"] = "Proveedor Rechazado" in str(form_rec["supplier"])

    load = confirm_initial_load(actor=wh, product=prod, lots=[LotInput("L-REPRO-1", 5, Decimal("2.00"), future)], supplier=sup_rec)
    register_stock_entry(actor=wh, product=prod, lots=[LotInput("L-REPRO-2", 5, Decimal("2.50"), future)], supplier=sup_rec)
    wh_client = Client()
    wh_client.force_login(wh)
    try:
        cert_resp = wh_client.get(reverse("inventory-load-created", args=(load.pk,)))
        findings["initial_load_created_status"] = cert_resp.status_code
    except Exception as exc:
        findings["initial_load_created_exception"] = f"{type(exc).__name__}: {exc}"

    hashes_after = {str(p.relative_to(ROOT)): digest(p) for p in protected}
    result = {
        "stamp_utc": stamp,
        "run": run_dir.name,
        "findings": findings,
        "protected_unchanged": {k: hashes_after[k] == hashes_before[k] for k in hashes_before},
        "protected_absent_at_start": [k for k, v in hashes_before.items() if v is None],
    }
    (out_dir / "repro.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    assert all(result["protected_unchanged"].values()), "Protected DB hash changed!"


if __name__ == "__main__":
    main()

